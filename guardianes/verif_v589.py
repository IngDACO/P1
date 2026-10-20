"""v589 · TOOLS → SURVEY, PROBADA (decisión del usuario: «Dale con todo»).

  1-4. ⚠️ Español en pantalla con el inglés de base: los avisos de parámetros («BKS debe ser
       > 0 (actual: 0.0)», visto en producción) y su «8 warning(s)», los motivos del registro del
       optimizador («Apertura tapada», «Pared: OR parada»), el diagrama de plomada («componentes»,
       «dif … revisar», «sobra», «lado Z», «lado Omega» — también en el PDF del CLIENTE), las
       cabeceras de la plomada y del cronograma, y las del PDF técnico («Medida», «Distancia»).
  5-6. Los campos medidos de 3 en 3 (en una fila de seis, tres rótulos partían y descuadraban);
       «Stops (NS)» y la casilla del Excel, cortos (partía / se cortaba con «…»).
  7.   El selector de obra de las herramientas, solo instalaciones abiertas.
  8.   El aviso «sin plano»: mandaba a un menú que ya no existe → la obra · Files, con botón.
  9.   El enlace al mapa con UN icono (salían 📍 y el de Material).
  10.  Resultados sin cálculo: un aviso y un botón (eran cuatro cabeceras vacías).

Todo EJECUTANDO: el cálculo completo con AppTest (la IA y el correo sustituidos: no se gasta
ni se manda nada) y el PDF técnico leído con pypdf.
"""
import io
import json
import os
import re
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Admin2", "rol": "administrator", "grupo": "cliente1"}
from streamlit.testing.v1 import AppTest                         # noqa: E402

fallos, n_ok = [], 0
ES = re.compile(r"\b(debe|actual|apertura|tapada|pared|parada|componentes|dif|revisar|sobra|lado|"
                r"Línea|inicial|Desplazada|Medida|Distancia|Duración|Peso)\b", re.I)


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("   ok   " + q)
    else:
        fallos.append(q)
        print("   FALLO " + q + (("  -> " + str(det)) if det != "" else ""))


print("1. ⚠️ Los avisos de parámetros, en el idioma base (motor, EJECUTADO)")
from core.calculations import validate_inputs                    # noqa: E402
_v = validate_inputs({"BKS": 0, "TKSW": 1, "TS": 1, "TK": 1, "SF1": 1, "SF2": 1, "RAIL": 1,
                      "BSR": 0, "FS": 50, "TSW": 100})
chk("tres avisos, ninguno en español (salía «BKS debe ser > 0 (actual: 0.0)»)",
    len(_v) == 3 and not any(ES.search(x) for x in _v) and _v[0] == "BKS must be greater than 0 (now 0).", _v)

print("\n2. Los motivos del optimizador")
import ast                                                       # noqa: E402
OP = io.open(os.path.join(RAIZ, "core", "optimizer.py"), encoding="utf-8").read()
# ⚠️ Las CADENAS del código (AST), no el texto: la 1ª vuelta cazó «Apertura tapada» en MI
# comentario (trampa 2: buscar no es usar).
_cad = [n.value for n in ast.walk(ast.parse(OP)) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
chk("⚠️ sin «Apertura tapada» ni «Pared: … parada» en ninguna cadena del optimizador",
    not [c for c in _cad if "Apertura" in c or "Pared:" in c or "parada" in c]
    and "Opening covered: |RL|={rl} > FRAME={f}" in _cad
    and sum(c.startswith("Wall: O") for c in _cad) == 2, [c for c in _cad if "Apertura" in c or "Pared" in c])

print("\n3. ⚠️ El diagrama de plomada (EJECUTADO)")
from core.plumb import compute_plumb, plumb_svg                 # noqa: E402
_r = compute_plumb({"BKS": 1600, "RAIL": 62, "TKSW": 965, "LengthTemplate": 300, "SF1": 51, "SF2": 51,
                    "BSR": 1985, "BS": 1998, "SG": 300, "TG": 60, "OMEGA_SIDE": "R"})
_tx = re.findall(r">([^<>]{3,})<", plumb_svg(_r))
# ⚠️ v597 · Al día con su razón (v385): lo medido y lo derivado lleva UN decimal en toda la
# plomada («13.0», «0.0»; antes «13», «0», que no casaba con las cifras ni la tabla); las cotas
# del plano del recuadro de BS siguen enteras («1826», «172»). El principio —en inglés— no cambia.
chk("el recuadro BS y el de BSR < BS, en inglés: components · diff · to absorb · Z side · Omega side",
    {"components 1826", "diff 172 mm — check", "to absorb: 13.0 mm", "Z side (L): 13.0",
     "Omega side: 0.0"} <= set(_tx), _tx)
chk("…y ningún texto del dibujo en español", not [x for x in _tx if ES.search(x)], [x for x in _tx if ES.search(x)])

print("\n4. El cálculo COMPLETO (AppTest, la IA y el correo sustituidos)")
G = r'''
import streamlit as st
import pandas as pd
st.session_state.setdefault("auth", {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"})
from core import survey_ui as SU, flash
_LOG = st.session_state.setdefault("_LOG", [])
_INT = {k: "x" for k in ("parametros", "estado_inicial", "desplazamientos", "solucion_optima",
                         "evasion_pared", "bsr_vs_bs", "consideraciones")}
_INT["_ok"] = True
_INTU = {k: "x" for k in ("resumen", "desplazamientos", "cortes", "implementacion", "verificacion")}
_INTU["_ok"] = True
SU.generate_interpretation = lambda *a, **k: dict(_INT)
SU.generate_user_interpretation = lambda *a, **k: dict(_INTU)
def _correo(*a, **k):
    st.session_state["_PDF_ADMIN"] = k.get("admin_report")
SU.send_usage_notification = _correo
SU.plan_ui.selector_proyecto = lambda key, ayuda="": (None, {})
SU.projects_data.list_projects = lambda *a, **k: []
SU.init_state()                       # lo que hace `app.py` antes de pintar el Survey
if "_INI" not in st.session_state and st.session_state.get("_CON_DATOS"):
    st.session_state["_INI"] = 1
    P = {"BKS": 1600, "RAIL": 62, "TKSW": 965, "SF1": 51, "SF2": 51, "BS": 1998, "BSR": 1985,
         "BT": 900, "FRAME": 30, "TS": 1750, "TK": 1400, "TKA": 100, "TKS": 30, "TSW": 100,
         "FS": 120, "OFFSET_CABIN": 0, "SG": 300, "TG": 60, "LengthTemplate": 300,
         "BGS": 900, "BK": 1100, "BKF1": 450, "BKF2": 450}
    for k, v in P.items():
        st.session_state["inp_" + k] = float(v)
    st.session_state["ns"] = 6
    st.session_state["survey_df"] = pd.DataFrame({
        "WR": [95, 88, 76, 92, 85, 80], "FR": [830, 822, 810, 818, 826, 815],
        "OR": [280, 296, 310, 288, 302, 295], "WL": [90, 84, 98, 79, 88, 86],
        "FL": [828, 820, 812, 824, 819, 816], "OL": [285, 292, 300, 305, 290, 298]}).astype(float)
flash.mostrar()
SU.render_survey_tab("administrator", "cliente1")
'''


def _txt(a):
    return " | ".join(str(x.value) for k in ("markdown", "caption", "info", "warning", "error", "success",
                                              "header") for x in getattr(a, k, []))


at = AppTest.from_string(G, default_timeout=600).run()
chk("sin datos: sin excepción", not at.exception, [e.value for e in at.exception][:1])
_ex = [str(e.label) for e in list(at.expander) + list(at.status)]
chk("⚠️ «8 warnings in the parameters», con su plural (decía «8 warning(s)»)",
    any("8 warnings in the parameters" in x for x in _ex), [x for x in _ex if "warning" in x])
chk("…y los avisos de dentro, en inglés",
    "BKS must be greater than 0" in _txt(at) and "debe ser" not in _txt(at))
_ni = {str(x.label): x for x in at.number_input}
chk("«Stops (NS)» (no «Number of stops (NS)», que partía)", "Stops (NS)" in _ni and "Number of stops (NS)" not in _ni)
chk("la casilla del Excel, corta («Also load its parameters»)",
    any(str(c.label) == "Also load its parameters" for c in at.checkbox))
SU_SRC = io.open(os.path.join(RAIZ, "core", "survey_ui.py"), encoding="utf-8").read()
chk("⚠️ los campos medidos de 3 en 3 (estático: AppTest no mide)",
    "cols = st.columns(3)\n            for j, (p, desc) in enumerate(USER_ONLY.items()):\n                cols[j % 3].number_input(" in SU_SRC)
at.radio(key="survey_fase").set_value("📊 Resultados e informes")
at.run()
_h = [str(x.value) for x in at.header]
chk("⚠️ resultados SIN cálculo: un aviso y un botón, sin las otras tres cabeceras vacías",
    any("Go to Survey data" in str(b.label) for b in at.button) and not [x for x in _h if "Schedule" in x
                                                                          or "Client report" in x
                                                                          or "Save to the project" in x], _h)
next(b for b in at.button if b.key == "btn_sv_ir_datos").click()
at.run()
chk("…y el botón vuelve a los datos", at.session_state["survey_fase"] == "📝 Survey data")

at = AppTest.from_string(G, default_timeout=600)
at.session_state["_CON_DATOS"] = True
at.run()
next(b for b in at.button if b.key == "btn_calc_datos").click()
at.run()
chk("con datos: calcula sin excepción", not at.exception, [e.value for e in at.exception][:1])


def _etq(d):
    try:
        return {k: (v or {}).get("label") for k, v in json.loads(d.proto.columns).items()}
    except Exception:
        return {}


_cols = {}
for d in list(at.dataframe):
    _cols.update({k: v for k, v in _etq(d).items() if v})
chk("⚠️ la tabla de plomada pinta Line · X start · X end · Shifted (las claves siguen siendo las suyas)",
    _cols.get("Línea") == "Line" and _cols.get("X inicial (mm)") == "X start (mm)"
    and _cols.get("X final (mm)") == "X end (mm)" and _cols.get("Desplazada") == "Shifted", _cols)
chk("…sus comprobaciones, Measurement · Distance (mm)",
    _cols.get("Medida") == "Measurement" and _cols.get("Distancia (mm)") == "Distance (mm)")
chk("…y el cronograma, Duration (d) · Weight (%)",
    _cols.get("Duración (d)") == "Duration (d)" and _cols.get("Peso (%)") == "Weight (%)", _cols)
_pdf = at.session_state["_PDF_ADMIN"] if "_PDF_ADMIN" in at.session_state else None
if _pdf:
    from pypdf import PdfReader
    _tp = " ".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(_pdf)).pages)
    chk("⚠️ el PDF TÉCNICO: «Measurement» / «Distance (mm)» (salían «Medida» / «Distancia (mm)»)",
        "Measurement" in _tp and "Distance (mm)" in _tp and "Medida" not in _tp and "Distancia" not in _tp)
else:
    chk("se generó el PDF técnico (el del correo)", False)

print("\n7-8. El selector de obra de las herramientas (plan_ui)")
from core import plan_ui as PL                                   # noqa: E402
chk("una instalación abierta sí; también tras desmontaje; y una obra sin tipo (vieja)",
    PL.es_de_herramientas({"Type": "Installation", "Status": "In progress"})
    and PL.es_de_herramientas({"Type": "Ripout + Installation", "Status": "Planned"})
    and PL.es_de_herramientas({"Type": "", "Status": "Planned"}))
chk("⚠️ Delivery, Other, un desmontaje solo, una completada y una cancelada, no",
    not any(PL.es_de_herramientas(p) for p in (
        {"Type": "Delivery", "Status": "Planned"}, {"Type": "Other", "Status": "On hold"},
        {"Type": "Ripout", "Status": "In progress"}, {"Type": "Installation", "Status": "Completed"},
        {"Type": "Installation", "Status": "Cancelled"})))
G2 = r'''
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "Admin2", "rol": st.session_state.get("_ROL", "administrator"),
                                     "grupo": "cliente1"})
import importlib
from core import plan_ui as PL, projects as P, plan_data
# ⚠️ el guion de la sección 4 dejó `selector_proyecto` SUSTITUIDO (mismo proceso, v574)
PL = importlib.reload(PL)
P.is_configured = lambda: True
P.list_projects = lambda *a, **k: [
    {"ID": "PRJ-1", "Name": "Lift A", "Type": "Installation", "Status": "In progress"},
    {"ID": "PRJ-2", "Name": "Truck", "Type": "Delivery", "Status": "Planned"},
    {"ID": "PRJ-3", "Name": "Old", "Type": "Installation", "Status": "Completed"}]
plan_data.del_proyecto = lambda pid: {}
PL.timeclock.open_sessions = lambda *a, **k: {PL.timeclock.TIPO_PROYECTO: {"proyecto": "Lift A"}}
prj, datos = PL.selector_proyecto("sv")
st.session_state["_SEL"] = (prj or {}).get("ID")
'''
at = AppTest.from_string(G2, default_timeout=60).run()
_op = list(at.selectbox(key="pl_prj_sv").options)
chk("⚠️ el selector solo ofrece la instalación abierta", _op == [PL.SIN_PROYECTO, "Lift A (PRJ-1)"], _op)
at = AppTest.from_string(G2, default_timeout=60)
at.session_state["pl_prj_sv"] = "Old (PRJ-3)"
at.run()
chk("…pero la que ya estaba elegida se queda (no desaparece de golpe)",
    "Old (PRJ-3)" in at.selectbox(key="pl_prj_sv").options and not at.exception)
at = AppTest.from_string(G2, default_timeout=60).run()
at.selectbox(key="pl_prj_sv").set_value("Lift A (PRJ-1)")
at.run()
_w = " ".join(str(w.value) for w in at.warning)
chk("⚠️ sin plano: dice la obra · Files (no «My company»)", "Files" in _w and "My company" not in _w, _w)
_b = next((b for b in at.button if b.key == "pl_ir_archivos_PRJ-1"), None)
chk("…con botón al administrador", _b is not None)
if _b is not None:
    _b.click()
    at.run()
    chk("…que abre la obra en Files", at.session_state["_prj_sec_pending"] == "📎 Archivos"
        and at.session_state["_prjsel_pending"] == "PRJ-1"
        and tuple(at.session_state["_admin_nav_pending"]) == ("proyectos", "📊 Proyectos"))
at = AppTest.from_string(G2, default_timeout=60)
at.session_state["_ROL"] = "field"
at.run()
_w = " ".join(str(w.value) for w in at.warning)
chk("al campo: «Ask the office», sin botón", "Ask the office" in _w and not any(
    str(b.key or "").startswith("pl_ir_archivos_") for b in at.button), _w)

print("\n9. El enlace al mapa: un icono")
from core import maps                                            # noqa: E402
chk("`maps_link_md` sin «📍»", "📍" not in maps.maps_link_md("500 Oxford St", "x") and
    maps.maps_link_md("500 Oxford St", "x").startswith("[x]("))
_sin = []
for f in sorted(os.listdir(os.path.join(RAIZ, "core"))):
    if f.endswith(".py") and f != "maps.py":
        for n, l in enumerate(io.open(os.path.join(RAIZ, "core", f), encoding="utf-8"), 1):
            if "maps_link_md(" in l and ":material/place:" not in l:
                _sin.append("%s:%d" % (f, n))
chk("⚠️ cada sitio que pinta el enlace le pone SU icono (uno)", not _sin, _sin)

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
sys.exit(1 if fallos else 0)
