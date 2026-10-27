# -*- coding: utf-8 -*-
"""Bateria de roturas de v613 (el Telegram, por ahora no obligatorio para entrar; UNA regla de
contacto de campo). ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455). Con TOPE
de tiempo (v522). Cada rotura es una LISTA de cambios (v526); el 4º campo, el guardián que la caza.

⚠️ Anclas en LÍNEA y literales: check_anclas_roturas no lee variables (v570).
`--anclas` solo comprueba que cada ancla casa UNA vez; un argumento suelto filtra roturas.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v613"
NT = "core/notify.py"
APPF = "app.py"
AD = "core/admin_digest.py"
AU = "core/auth_ui.py"
PU = "core/projects_ui.py"
TOPE_S = 600


def corre(g=G):
    """True = verde, False = rojo, None = COLGADO (supero el tope)."""
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                           cwd=RAIZ, capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


ROTURAS = [
    # ── la regla ──
    ("⚠️ el Telegram vuelve a ser obligatorio sin decirlo nadie", NT,
     [('TELEGRAM_OBLIGATORIO_CAMPO = False\n', 'TELEGRAM_OBLIGATORIO_CAMPO = True\n')]),
    ("⚠️ se exige aunque el bot no exista (el callejón sin salida de v368)", NT,
     [('    return bool(TELEGRAM_OBLIGATORIO_CAMPO and telegram_configured() and bot_username())\n',
       '    return bool(TELEGRAM_OBLIGATORIO_CAMPO)\n')]),
    ("la regla ignora la política (se exige siempre que haya bot)", NT,
     [('    return bool(TELEGRAM_OBLIGATORIO_CAMPO and telegram_configured() and bot_username())\n',
       '    return bool(telegram_configured() and bot_username())\n')]),
    ("⚠️ el email deja de ser obligatorio", NT,
     [('    if not str(u.get("Email", "")).strip():\n        return False\n', '')]),
    # ── la puerta de app.py ──
    ("⚠️ la puerta exige el Telegram siempre", APPF,
     [('    _falta_tg   = _exige_tg and not _has_tg        # sin bot o sin la política, no se exige\n',
       '    _falta_tg   = not _has_tg\n')], "verif_v368"),
    ("⚠️ la puerta decide por su cuenta (solo el bot, sin la política)", APPF,
     [('        _exige_tg = notify.exige_telegram_campo()\n',
       '        _exige_tg = bool(notify.telegram_configured() and notify.bot_username())\n')]),
    ("la puerta deja entrar sin email", APPF,
     [('    _falta_mail = not _has_mail\n', '    _falta_mail = False\n')], "verif_v368"),
    # ── los demás sitios, con la regla copiada a mano ──
    ("el resumen del admin vuelve a pedir «email Y Telegram» (la cifra del Home)", AD,
     [('        if not _nt.contacto_campo_ok(u):\n',
       '        if not (str(u.get("Email", "")).strip() and str(u.get("TelegramChatID", "")).strip()):\n')]),
    ("la tabla del propietario vuelve a pedir los dos", AU,
     [('                     else (t("yes") if _nt.contacto_campo_ok(u) else t("missing")))\n',
       '                     else (t("yes") if (str(u.get("Email", "")).strip() and '
       'str(u.get("TelegramChatID", "")).strip()) else t("missing")))\n')]),
    ("la fila de salud del equipo vuelve a pedir los dos", AU,
     [('        return _nt.contacto_campo_ok(u)           # v613 · la regla de la puerta\n',
       '        return bool(str(u.get("Email", "")).strip() and str(u.get("TelegramChatID", "")).strip())\n')]),
    ("⚠️ el aviso al asignar vuelve a pedir los dos («no recibirán la asignación»)", PU,
     [('            if not notify.contacto_campo_ok(info):\n',
       '            if not (str(info.get("Email", "")).strip() and str(info.get("TelegramChatID", "")).strip()):\n')]),
    ("el aviso al asignar dice «(email + Telegram)» aunque solo falte el email", PU,
     [('                    if notify.exige_telegram_campo() else\n', '                    if True else\n')]),
    # ── la ficha de contacto ──
    ("la ficha no dice que por ahora es opcional", AU,
     [('        if not notify.exige_telegram_campo():\n            # v613', '        if False:\n            # v613')]),
    ("la ficha dice «opcional» aunque se exija", AU,
     [('        if not notify.exige_telegram_campo():\n            # v613', '        if True:\n            # v613')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           NT, [('TELEGRAM_OBLIGATORIO_CAMPO = False\n', 'TELEGRAM_OBLIGATORIO_CAMPO = False   # (control)\n')])


def aplica(rel, cambios):
    """Aplica TODOS los cambios o ninguno. Devuelve (ok, bak, p, detalle)."""
    p = os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep)))
    bak = io.open(p, encoding="utf-8", newline="").read()
    txt = bak
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    _filtro = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--anclas" in sys.argv:
        _m = 0
        for r in ROTURAS + [CONTROL]:
            desc, rel, cambios = r[:3]
            txt = io.open(os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep))),
                          encoding="utf-8", newline="").read()
            for viejo, _ in cambios:
                if txt.count(viejo) != 1:
                    _m += 1
                    print("  x%d  %s  <- %s" % (txt.count(viejo), desc, viejo[:60]))
        print("anclas: %d mal de %d roturas" % (_m, len(ROTURAS) + 1))
        sys.exit(1 if _m else 0)

    _rot = [r for r in ROTURAS if not _filtro or any(f in r[0] for f in _filtro)]
    print("0. Verde de base")
    for _g in sorted({r[3] if len(r) > 3 else G for r in _rot} | {G}):
        _base = corre(_g)
        if not _base:
            print("   ⚠️ %s YA esta %s: la tanda saldria «cazada» sin probar nada"
                  % (_g, "COLGADO" if _base is None else "rojo"))
            sys.exit(1)
        print("   %s verde" % _g)

    print("")
    print("1. Roturas (cada una debe ponerse ROJA)")
    cazadas = total = 0
    saltadas, colgadas = [], []
    for r in _rot:
        desc, rel, cambios = r[:3]
        _g = r[3] if len(r) > 3 else G
        _ok, bak, p, det = aplica(rel, cambios)
        if _ok is None:
            print("  ??      ancla %s en %s -> %s" % (det, rel, desc))
            saltadas.append(desc)
            continue
        total += 1
        try:
            verde = corre(_g)
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE
        if verde is None:
            colgadas.append(desc)
            print("  COLGADA  %s" % desc)
            continue
        cazadas += (not verde)
        print("  %s %s%s" % ("CAZADA  " if not verde else "ESCAPADA", desc,
                             "" if _g == G else "  [%s]" % _g), flush=True)

    print("")
    print("2. Control (debe seguir VERDE)")
    _d, _r, _c = CONTROL
    _ok, bak, p, det = aplica(_r, _c)
    control_ok = False
    if _ok is None:
        print("  ??      ancla del control %s" % det)
    else:
        try:
            control_ok = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)
        print("  %s %s" % ("ok     " if control_ok else "MAL    ", _d))

    print("")
    print("=== %d de %d roturas cazadas ===" % (cazadas, total))
    if saltadas:
        print("⚠️ %d rotura(s) NO se pudieron aplicar: la bateria no las ha probado"
              % len(saltadas))
    if colgadas:
        print("⚠️ %d rotura(s) COLGARON el guardian (tope %d s): no son detecciones"
              % (len(colgadas), TOPE_S))
    sys.exit(0 if cazadas == total and not saltadas and not colgadas and control_ok else 1)
