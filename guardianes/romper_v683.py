# -*- coding: utf-8 -*-
"""Batería de roturas de v683. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v683"
TOPE_S = 600
CT, CA, RT = "core/chat_tools.py", "core/chat_agent.py", "core/route_ui.py"

ROTURAS = [
    ("⚠️ la oficina no tiene get_calculations", CT,
     [("    {\"name\": \"get_calculations\", \"fn\": _calculos, \"input_schema\": _POR_OBRA,",
       "    {\"name\": \"get_calculations_x\", \"fn\": _calculos, \"input_schema\": _POR_OBRA,")]),
    ("⚠️ Rieles: el negativo no se señala", CT,
     [("for c in (\"CutRZ\", \"CutRO\", \"CutRF\", \"CutRB\", \"CutRC\", \"CutRCW\") if _num(x.get(c)) < 0]",
       "for c in (\"CutRZ\", \"CutRO\", \"CutRF\", \"CutRB\", \"CutRC\", \"CutRCW\") if _num(x.get(c)) < -1e9]")]),
    ("un cálculo VIEJO pisa el último", CT, [("        if k == \"survey\" or k in herr:", "        if k == \"survey\":")]),
    ("el Survey sin sus parámetros (el muro como corte)", CT,
     [("            f = I.hechos({\"limits\": lim, \"analysis\": lim, \"optimizer_result\": {\"best\": b}}, rc[\"all_params\"])",
       "            f = I.hechos({\"limits\": lim, \"analysis\": lim, \"optimizer_result\": {\"best\": b}}, {})")]),
    ("sin la fecha del Survey", CT, [("                \"saved_on\": dmy(str(_sv.get(\"Date\", \"\"))[:10]) if _sv else \"\",",
                                      "                \"saved_on\": \"\",")]),
    ("cómo leerlo, sin el muro", CT, [(" (a limiting wall is NEVER cut)", "")]),
    ("la guía de la oficina no lo sabe", CA,
     [("tiene pendiente de decidir, el dinero y lo que dieron el Survey y las herramientas técnicas de una obra. Ya ",
       "tiene pendiente de decidir y el dinero. Ya ")]),
    ("⚠️ F1: el fin de semana vuelve a abrir en ese día", RT,
     [("            if not obras_de_mi_dia(usuario, grupo, _hoy):\n                _ini = _R.semana_de_trabajo(_hoy)",
       "            if False:\n                _ini = _R.semana_de_trabajo(_hoy)")]),
    ("F1: salta al lunes aunque el sábado tenga obra", RT,
     [("            if not obras_de_mi_dia(usuario, grupo, _hoy):\n", "            if True:\n")]),
    ("⚠️ F2: el día de vacaciones vuelve a «Nothing is planned»", RT, [("            if _fuera:\n", "            if False:\n")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", RT,
           [("    # no tiene obras en su tablero, el lunes.", "    # (control) no tiene obras en su tablero, el lunes.")])


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
