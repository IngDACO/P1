# -*- coding: utf-8 -*-
"""Batería de roturas de v688. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v688"
TOPE_S = 300
SU, PU = "core/survey_ui.py", "core/projects_ui.py"

ROTURAS = [
    ("⚠️ el Survey del campo vuelve a «Survey_<fecha>_<cuenta>.json»", SU,
     [("filename=f\"Field_survey_{nombre_archivo(prj.get('Name'), 'project')}_{_cuando}.json\", mime=\"application/json\")",
       "filename=f\"Survey_{_cuando}_{usuario}.json\", mime=\"application/json\")")]),
    ("⚠️ cargarlo no apunta que es del campo", PU,
     [("        st.session_state[\"_rebuilt_campo\"] = {", "        _no_v688 = {")]),
    ("la cuenta en vez del nombre", PU,
     [("            \"quien\": (_nombres_de([str(run.get(\"User\", \"\"))], str(_prj.get(\"Group\", \"\"))) or [\"\"])[0],",
       "            \"quien\": str(run.get(\"User\", \"\")),")]),
    ("la fecha sin formato (ISO)", PU,
     [("            \"cuando\": _dmy(_fh) + (\" \" + _fh[11:16] if len(_fh) >= 16 else \"\")}",
       "            \"cuando\": _fh}")]),
    ("⚠️ «Load this project» no lo quita (se arrastra)", PU,
     [("    st.session_state.pop(\"_rebuilt_campo\", None)        # v688 · lo de la obra; el del campo lo pone `_decidir_survey`",
       "    pass")]),
    ("⚠️ el Survey no lo dice", SU, [("    if _campo_sv:", "    if False:")]),
    ("calcular no lo olvida", SU,
     [("        st.session_state.pop(\"_rebuilt_campo\", None)\n", "        pass\n")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", PU,
           [("        # como al cargar el de la obra). El login se muestra con su nombre (`_nombres_de`, v544).",
             "        # (control) como al cargar el de la obra). El login se muestra con su nombre (`_nombres_de`, v544).")])


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
