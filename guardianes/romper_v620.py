# -*- coding: utf-8 -*-
"""Batería de roturas de v620. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v620"
TOPE_S = 180
AUI = "core/auth_ui.py"

ROTURAS = [
    ("⚠️ la restauración deja de olvidar la página anterior", AUI,
     [("                _olvidar_pagina_anterior()\n", "")]),
    ("se tira también lo del gestor de cookies", AUI,
     [('        if not str(k).startswith(("_", "login_", "copex_")):\n',
       '        if not str(k).startswith(("_", "login_")):\n')]),
    ("no se tira nada", AUI,
     [("            del st.session_state[k]\n", "            pass\n")]),
    ("⚠️ se olvida antes de saber si la cookie vale", AUI,
     [("        if _u and _t:\n            try:\n                _a = auth.validate_session(_u, _t)\n",
       "        if _u and _t:\n            _olvidar_pagina_anterior()\n            try:\n"
       "                _a = auth.validate_session(_u, _t)\n")]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", AUI,
           [('    """v620 · Al restaurar desde la cookie la sesión es NUEVA,', '    """(control) v620 · Al restaurar desde la cookie la sesión es NUEVA,')])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


def aplica(rel, cambios):
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    bak = io.open(p, encoding="utf-8", newline="").read()
    txt = bak.replace("\r\n", "\n")
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    if corre() is not True:
        print("⚠️ el guardian YA esta rojo: la tanda saldria «cazada» sin probar nada")
        sys.exit(1)
    print("0. Verde de base: ok")
    cazadas, malas = 0, []
    for desc, rel, cambios in ROTURAS:
        ok, bak, p, msg = aplica(rel, cambios)
        if ok is None:
            print("  ?? ancla %s: %s" % (desc, msg))
            malas.append(desc)
            continue
        try:
            r = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)
        if r is False:
            cazadas += 1
            print("  ok    cazada: %s" % desc)
        else:
            print("  ESCAPA %s (%s)" % (desc, "COLGADA" if r is None else "verde"))
            malas.append(desc)
    desc, rel, cambios = CONTROL
    ok, bak, p, msg = aplica(rel, cambios)
    try:
        r = corre() if ok else None
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok   " if r is True else "ESCAPA", desc))
    if r is not True:
        malas.append(desc)
    if corre() is not True:
        print("⚠️ el guardian NO vuelve a verde tras restaurar")
        malas.append("restaurar")
    print("=== %d de %d roturas cazadas ===" % (cazadas, len(ROTURAS)))
    sys.exit(1 if malas else 0)
