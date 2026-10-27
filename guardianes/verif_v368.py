"""GUARDIÁN v368 — el bloqueo de contacto no puede ser un callejón sin salida.

El fallo real: se exigía email **y** Telegram a todo usuario de campo, aunque el bot no
estuviera en Secrets. Y entonces no había salida por ningún lado —la pantalla no podía
mostrar el link de Start (condicionado a `telegram_configured()`) y el admin no tenía
botón para vincular—, así que 7 de los 8 usuarios de campo del grupo estaban encerrados.

⚠️ La condición se lee del CÓDIGO REAL de `app.py` por AST y se evalúa, en vez de
copiarla al test: replicar un `if` a mano es lo que produjo el OK en falso de v324.
"""
import ast
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
APP = pathlib.Path(r"C:\Users\diego\P1\survey_app\app.py")
src = APP.read_text(encoding="utf-8")
arbol = ast.parse(src)

# ── se localizan las asignaciones reales de _falta_mail / _falta_tg y la guarda
exprs = {}
for n in ast.walk(arbol):
    if isinstance(n, ast.Assign) and len(n.targets) == 1:
        nom = getattr(n.targets[0], "id", "")
        if nom in ("_falta_mail", "_falta_tg"):
            exprs[nom] = ast.unparse(n.value)

print("== condiciones tal y como están escritas en app.py ==")
for k, v in exprs.items():
    print(f"   {k} = {v}")
assert "_falta_mail" in exprs and "_falta_tg" in exprs, "no encuentro las condiciones en app.py"

# ⚠️ v613 · AL DÍA CON SU RAZÓN: la puerta ya no calcula `_tg_hay` ella misma. Pide
# `notify.exige_telegram_campo()` (→ `_exige_tg`), que es la POLÍTICA (v613: por ahora el
# Telegram NO se exige, decisión del usuario) Y que el bot exista (lo de v368). La afirmación
# de v368 sigue entera: se comprueba en la regla REAL de `notify`, por AST y ejecutándola.
assert "_exige_tg" in exprs["_falta_tg"], \
    "‼️ _falta_tg ya no sale de la regla de notify → la puerta y los paneles se separan"
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import inspect                                                   # noqa: E402
from core import notify as N                                     # noqa: E402
_src_n = inspect.getsource(N.exige_telegram_campo)
assert "telegram_configured()" in _src_n and "bot_username()" in _src_n, \
    "‼️ la exigencia de Telegram ya no depende de si el canal existe → vuelve el callejón sin salida"
print("   ✓ la exigencia de Telegram depende de que el bot exista (y de la política, v613)")
_ORIG_N = (N.TELEGRAM_OBLIGATORIO_CAMPO, N.telegram_configured, N.bot_username)


def evaluar(tg_hay, has_mail, has_tg, politica=True):
    """Evalúa las expresiones REALES del fichero con este escenario, con la regla REAL de
    `notify` (la política y el bot, sustituidos)."""
    N.TELEGRAM_OBLIGATORIO_CAMPO = politica
    N.telegram_configured = lambda: tg_hay
    N.bot_username = lambda: "bot" if tg_hay else ""
    ent = {"_exige_tg": N.exige_telegram_campo(), "_has_mail": has_mail, "_has_tg": has_tg}
    fm = eval(exprs["_falta_mail"], {}, ent)
    ft = eval(exprs["_falta_tg"], {}, ent)
    # v613 · la puerta y `contacto_campo_ok` (Home, resumen, paneles) son la MISMA regla
    _u = {"Email": "a@b.co" if has_mail else "", "TelegramChatID": "1" if has_tg else ""}
    assert (not fm and not ft) == N.contacto_campo_ok(_u), \
        "‼️ la puerta y contacto_campo_ok no coinciden en %r" % ((politica, tg_hay, has_mail, has_tg),)
    return (not fm and not ft), fm, ft


print("\n== los 8 escenarios (con la política de exigir Telegram, la de v368) ==")
print(f"   {'bot?':<6}{'email?':<8}{'tg?':<6}{'ENTRA':<8} qué debe pasar")
casos = [
    # (bot, mail, tg, entra_esperado, nota)
    (False, True,  False, True,  "SIN bot y con email → entra (antes: ENCERRADO)"),
    (False, True,  True,  True,  "sin bot pero con tg guardado → entra"),
    (False, False, False, False, "sin email → bloqueado, y lo pone el admin"),
    (False, False, True,  False, "sin email → bloqueado aunque tenga tg"),
    (True,  True,  True,  True,  "con bot y todo puesto → entra"),
    (True,  True,  False, False, "con bot y sin tg → bloqueado, PERO con link de Start"),
    (True,  False, True,  False, "con bot y sin email → bloqueado"),
    (True,  False, False, False, "con bot y sin nada → bloqueado"),
]
ok = True
for bot, mail, tg, esperado, nota in casos:
    entra, fm, ft = evaluar(bot, mail, tg)
    bien = entra == esperado
    ok &= bien
    print(f"   {str(bot):<6}{str(mail):<8}{str(tg):<6}{str(entra):<8} "
          f"{'✓' if bien else '✗'} {nota}")

# ── la salida SIEMPRE existe cuando se bloquea ────────────────────
# ⚠️ Es el corazón del arreglo: si se bloquea por Telegram, tiene que ser porque el bot
#    existe — y entonces la pantalla PUEDE mostrar el link. Sin bot no se bloquea por
#    Telegram nunca, así que no puede haber pendiente sin salida.
# v613 · y SIN la política (la de ahora): el Telegram no bloquea nunca; el email, sí
print("\n== sin exigir Telegram (v613, la decisión vigente) ==")
for bot in (False, True):
    for mail in (False, True):
        for tg in (False, True):
            entra, fm, ft = evaluar(bot, mail, tg, politica=False)
            bien = (entra == mail) and not ft
            ok &= bien
            print(f"   bot={str(bot):<6}email={str(mail):<6}tg={str(tg):<6}entra={str(entra):<6}"
                  f"{'✓' if bien else '✗'}")

print("\n== ¿algún bloqueo sin salida? (las dos políticas) ==")
sin_salida = []
for politica in (True, False):
    for bot in (False, True):
        for mail in (False, True):
            for tg in (False, True):
                entra, fm, ft = evaluar(bot, mail, tg, politica)
                if entra:
                    continue
                # bloqueado: ¿lo puede resolver alguien?
                #   falta email → lo pone el admin (siempre posible)
                #   falta tg    → solo se exige si hay bot, y entonces hay link
                if ft and not bot:
                    sin_salida.append((politica, bot, mail, tg))
print("   ", sin_salida or "ninguno: todo bloqueo tiene quien lo resuelva")
ok &= not sin_salida
N.TELEGRAM_OBLIGATORIO_CAMPO, N.telegram_configured, N.bot_username = _ORIG_N

print("\n" + ("✅ v368 OK: no se exige un canal que no existe, y todo bloqueo tiene salida"
              if ok else "⚠️ REVISAR"))
sys.exit(0 if ok else 1)
