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

# ⚠️ lo que hace este chequeo REAL: comprobar que la exigencia de Telegram está
# condicionada a que el canal exista. Si alguien la vuelve incondicional, salta.
assert "_tg_hay" in exprs["_falta_tg"], \
    "‼️ _falta_tg ya no depende de si el canal existe → vuelve el callejón sin salida"
print("   ✓ la exigencia de Telegram depende de que el bot exista")


def evaluar(tg_hay, has_mail, has_tg):
    """Evalúa las expresiones REALES del fichero con este escenario."""
    ent = {"_tg_hay": tg_hay, "_has_mail": has_mail, "_has_tg": has_tg}
    fm = eval(exprs["_falta_mail"], {}, ent)
    ft = eval(exprs["_falta_tg"], {}, ent)
    return (not fm and not ft), fm, ft


print("\n== los 8 escenarios ==")
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
print("\n== ¿algún bloqueo sin salida? ==")
sin_salida = []
for bot in (False, True):
    for mail in (False, True):
        for tg in (False, True):
            entra, fm, ft = evaluar(bot, mail, tg)
            if entra:
                continue
            # bloqueado: ¿lo puede resolver alguien?
            #   falta email → lo pone el admin (siempre posible)
            #   falta tg    → solo se exige si hay bot, y entonces hay link
            if ft and not bot:
                sin_salida.append((bot, mail, tg))
print("   ", sin_salida or "ninguno: todo bloqueo tiene quien lo resuelva")
ok &= not sin_salida

print("\n" + ("✅ v368 OK: no se exige un canal que no existe, y todo bloqueo tiene salida"
              if ok else "⚠️ REVISAR"))
sys.exit(0 if ok else 1)
