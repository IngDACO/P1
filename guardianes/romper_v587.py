# -*- coding: utf-8 -*-
"""Bateria de roturas de v587 (las obras con desmontaje no se podían crear). ⚠️ Verde de BASE
primero (v459) y NO en paralelo con la suite (v455). Anclas en LÍNEA y literales (v570).
`--anclas` solo comprueba que cada ancla casa UNA vez.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v587"
PU = "core/projects_ui.py"
QE = "core/quotes.py"
QU = "core/quotes_ui.py"
TOPE_S = 400

ROTURAS = [
    ("⚠️ «New project» vuelve a pintar solo las preguntas PENDIENTES (la respuesta se borra)", PU,
     [("    for g in _S.falta_por_decidir(tipo, ()):\n",
       "    for g in _S.falta_por_decidir(tipo, _cond_elegidas(key)):\n")]),
    ("⚠️ el motor vuelve a crear una instalación con NS 0 (sin plan)", QE,
     [("        if _num(ns) < 2:\n", "        if False:\n")]),
    ("⚠️ el motor vuelve a crear un desmontaje sin tracción/hidráulico", QE,
     [("        if _faltan:\n", "        if False:\n")]),
    ("una Delivery desde cotización vuelve a nacer sin fecha de fin", QE,
     [("        fin = _ff.isoformat()\n", "")]),
    ("el motor acepta un fin ANTES del inicio", QE,
     [("    elif fecha_fin is not None and fecha_fin < ini:\n", "    elif False:\n")]),
    ("⚠️ la pantalla de la cotización deja de pasar la respuesta al motor", QU,
     [("                condicionales=_PU._cond_elegidas(_kalta), fecha_fin=fin)\n",
       "                fecha_fin=fin)\n")]),
    ("la pantalla de la cotización crea sin la respuesta", QU,
     [("            if _pend:\n", "            if False:\n")]),
    ("vuelve el NS 0 en la pantalla de la cotización", QU,
     [("min_value=2, max_value=50, step=1, value=2,", "min_value=0, max_value=50, step=1, value=0,")]),
    ("una Delivery desde cotización vuelve a pedir NS y no la fecha de fin", QU,
     [("        if _con_plan:\n", "        if True:\n")]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", QU,
           [("def _crear_proyecto(grupo, c, _tot):\n", "def _crear_proyecto(grupo, c, _tot):   # (control)\n")])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


def aplica(rel, cambios):
    p = os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep)))
    bak = io.open(p, encoding="utf-8").read()
    txt = bak
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    if "--anclas" in sys.argv:
        _m = 0
        for desc, rel, cambios in ROTURAS + [CONTROL]:
            txt = io.open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8").read()
            for viejo, _ in cambios:
                if txt.count(viejo) != 1:
                    _m += 1
                    print("  x%d  %s" % (txt.count(viejo), desc))
        print("anclas: %d mal de %d roturas" % (_m, len(ROTURAS) + 1))
        sys.exit(1 if _m else 0)
    if not corre():
        print("⚠️ %s YA esta rojo: la tanda no probaria nada" % G)
        sys.exit(1)
    print("0. %s verde de base" % G)
    cazadas = total = 0
    for desc, rel, cambios in ROTURAS:
        _ok, bak, p, det = aplica(rel, cambios)
        if _ok is None:
            print("  ??      ancla %s -> %s" % (det, desc))
            continue
        total += 1
        try:
            verde = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE
        cazadas += (verde is False)
        print("  %s %s" % ("CAZADA  " if verde is False else "ESCAPADA", desc), flush=True)
    _ok, bak, p, det = aplica(*CONTROL[1:])
    try:
        control_ok = corre() is True
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok     " if control_ok else "MAL    ", CONTROL[0]))
    print("\n=== %d de %d roturas cazadas ===" % (cazadas, len(ROTURAS)))
    sys.exit(0 if cazadas == total == len(ROTURAS) and control_ok else 1)
