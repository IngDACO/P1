# -*- coding: utf-8 -*-
"""Batería de roturas de v706. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v706"
TOPE_S = 180
PU, SP = "core/projects_ui.py", "core/stage_progress_ui.py"

ROTURAS = [
    ("V4: al reanudar ya no se mira el tablero", PU,
     [("        _con = [x for x in _dest if _dias.get(x)]", "        _con = []")]),
    ("V4: a todos «stay as they were», haya días o no", PU,
     [("        _con = [x for x in _dest if _dias.get(x)]", "        _con = list(_dest)")]),
    ("V4: quien sigue en el tablero recibe los dos avisos", PU,
     [("        _envios = [(_txt, [x for x in _dest if x not in _con]),", "        _envios = [(_txt, list(_dest)),")]),
    ("V4: se mira el tablero también al guardar sin reanudar", PU,
     [("    _envios = [(_txt, _dest)]\n    if _reanuda:", "    _envios = [(_txt, _dest)]\n    if True:")]),
    ("V5: vuelve «1 unsaved ticks» en la lista", SP,
     [("if len(_pend) == 1 else", "if False else")]),
    ("V5: vuelve «1 unsaved ticks in «Progress»»", PU,
     [("                   if _npend == 1 else", "                   if False else")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", PU,
           [("    # ⚠️ v706 · V4 del ciclo 7 (lo de V1, del lado del CAMPO)",
             "    # ⚠️ v706 · V4 del ciclo 7 (lo de V1, del lado del CAMPO) · control")])


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
