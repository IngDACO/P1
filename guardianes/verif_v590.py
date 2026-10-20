"""v590 · LO VISTO VERIFICANDO v589 EN PRODUCCIÓN (decisión del usuario: «Si dale con todo»).

  1-3. ⚠️ El aviso ANTES de borrar una obra (`projects.datos_asociados`) pedía «Gastos»,
       «Calculos» y «Alarmas» —los nombres de antes del renombrado—: contaba SIEMPRE 0 y, al no
       encontrarlas, la LECTURA las creaba vacías (las tres del libro de cliente1). Medido en
       PRJ-0026: «0 cálculos» con CAL-0001 en ToolRuns. verif_v381 no lo veía: su sustituto
       contestaba a «Gastos». → nombres de hoy, una lectura no crea pestañas, y ningún nombre
       viejo de pestaña en el código de la app.
  4.   Los avisos tras CALCULAR no se veían nunca (antes de un `st.rerun()`) → `flash`, y el del
       correo dice lo que PASÓ.
  5.   ⚠️ «Save to the project»: sin elegir y con obras cerradas → la del cálculo, elegida, y solo
       instalaciones abiertas; sin ninguna, un botón (no «My company»).
  6.   Cifras de resultados ACTIVAS (eran `st.metric`); plurales; «activa», «FB aplic.».
  7.   «EJES» → «AXIS OFFSET»; el nombre de la obra en los SVG MEDIDO y ESCAPADO (`[:24]`
       dejaba «Bondi Junction Tower — L», y «Smith & Sons» rompía el SVG).
  8.   El chip «No drawing» con el plano de la obra; el mensaje del riel con su color; «0» no
       «0.0»; archivos y Excel en inglés; plurales del PDF del CLIENTE.
"""
import ast
import io
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Admin2", "rol": "administrator", "grupo": "cliente1"}
from streamlit.testing.v1 import AppTest                         # noqa: E402

fallos, n_ok = [], 0


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("   ok   " + q)
    else:
        fallos.append(q)
        print("   FALLO " + q + (("  -> " + str(det)) if det != "" else ""))


def fuente(rel):
    return io.open(os.path.join(RAIZ, *rel.split("/")), encoding="utf-8").read()


def cadenas(src):
    """Las cadenas del CÓDIGO (AST), sin docstrings (trampa 2: buscar no es usar)."""
    arbol = ast.parse(src)
    docs = set()
    for n in ast.walk(arbol):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body \
                and isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant):
            docs.add(id(n.body[0].value))
    return [n.value for n in ast.walk(arbol)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs]


# ══════════════════════════════════════════════════════════════════════════
print("1. ⚠️ El recuento ANTES de borrar una obra cuenta lo que hay (caso construido)")
from core import projects as P                                   # noqa: E402
_FILAS = {
    "Projects": [{"ID": "PRJ-Z", "Group": "cliente1", "Name": "Obra Z"}],
    "Expenses": [{"ProjectID": "PRJ-Z"}, {"ProjectID": "PRJ-Z"}, {"ProjectID": "OTRA"}],
    "ToolRuns": [{"ProjectID": "PRJ-Z"}],
    "PreStarts": [{"ProjectID": "OTRA"}],
    "Alerts": [{"ProjectID": "PRJ-Z"}],
}
_PEDIDAS = []
_orig = (P._records, P._fichaje_records, P.get_project, P.list_documents, P.list_activities)


def _rec(t=None):
    _PEDIDAS.append(t)
    return _FILAS.get(t, [])     # ⚠️ SOLO los nombres de hoy: el viejo («Gastos»…) no da nada


P._records = _rec
P._fichaje_records = lambda: []
P.get_project = lambda pid: _FILAS["Projects"][0] if pid == "PRJ-Z" else None
P.list_documents = lambda pid: [1, 2]
P.list_activities = lambda pid: [1, 2, 3]
try:
    _aso = P.datos_asociados("PRJ-Z")
finally:
    P._records, P._fichaje_records, P.get_project, P.list_documents, P.list_activities = _orig
chk("⚠️ cuenta los gastos, el CÁLCULO y la alarma (salían 0: se pedían «Gastos/Calculos/Alarmas»)",
    _aso.get("Expenses") == 2 and _aso.get("Calculations") == 1 and _aso.get("Alerts") == 1
    and _aso.get("Pre-Starts") == 0 and _aso.get("Documents") == 2 and _aso.get("Activities") == 3, _aso)
chk("…pidiendo las pestañas por su nombre de HOY (ninguna vieja)",
    {"Expenses", "ToolRuns", "PreStarts", "Alerts"} <= set(_PEDIDAS)
    and not {"Gastos", "Calculos", "Alarmas"} & set(_PEDIDAS), _PEDIDAS)
_PU_SRC = fuente("core/projects_ui.py")
_tramo = _PU_SRC.split("_aso = P.datos_asociados(pid)")[1][:1800] if "_aso = P.datos_asociados(pid)" in _PU_SRC else ""
chk("…y la pantalla pinta cada clave con su nombre y su plural (no «documentos», «gastos»)",
    bool(_tramo) and "_ETQ_ASO" in _tramo and "k.lower()" not in _tramo
    and 't("It will be left with no project:")' in _tramo, _tramo[:300])

print("\n2. ⚠️ Una LECTURA no crea pestañas (motor de verdad, sondas validadas)")
from core import hojas, timeclock                                # noqa: E402
_crea, _o2 = [], (hojas._lote, timeclock.get_sheet)
hojas._lote = lambda sid: {}                                      # el libro NO tiene la pestaña
timeclock.get_sheet = lambda titulo, cab=(), grupo=None: (_crea.append(titulo), (_ for _ in ()).throw(RuntimeError("x")))[1]
try:
    r_none = hojas.registros("ToolRuns", None)
    _antes = len(_crea)
    hojas.registros("ToolRuns", [])                               # CONTROL: con [] SÍ la crea
    _control = len(_crea) > _antes
finally:
    hojas._lote, timeclock.get_sheet = _o2
chk("CONTROL: la sonda ve la creación cuando la hay (con cabecera `[]`)", _control, _crea)
# (la 1ª vuelta contó «Groups»: `sheet_id_para` lee esa pestaña GLOBAL para saber el libro y el
# sustituto la apuntaba como creada — la sonda, no el código. Se mira la pestaña pedida.)
chk("…y con `None` no se crea nada", r_none is None and "ToolRuns" not in _crea[:_antes], (r_none, _crea))
_cab = []
_o3 = hojas.registros
hojas.registros = lambda titulo, cabeceras=None, grupo=None: (_cab.append((titulo, cabeceras)), [])[1]
try:
    P._records_cached.clear()
    P._records_cached("libro-x", "ToolRuns")
    P._records_cached("libro-x", P.PROJECTS_SHEET)
finally:
    hojas.registros = _o3
    P._records_cached.clear()
chk("⚠️ `projects._records` pide sin cabecera (`None`) lo que no conoce, y con la suya lo que sí",
    ("ToolRuns", None) in _cab and any(t == P.PROJECTS_SHEET and c for t, c in _cab), _cab)

print("\n3. Ningún nombre VIEJO de pestaña en el código de la app (barrido)")
_LEG = next(ast.literal_eval(n.value) for n in ast.parse(fuente("core/timeclock.py")).body
            if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "LEGADO")
_VIEJOS = set(_LEG.values())                     # con su mayúscula: así se pide una pestaña
_hall = []
for _dp, _dn, _fs in os.walk(RAIZ):
    if any(x in _dp for x in (".git", "__pycache__", ".streamlit")):
        continue
    for _f in _fs:
        if _f.endswith(".py"):
            _rel = os.path.relpath(os.path.join(_dp, _f), RAIZ).replace(os.sep, "/")
            _s = io.open(os.path.join(_dp, _f), encoding="utf-8").read()
            _arb = ast.parse(_s)
            _fuera = set()
            for n in ast.walk(_arb):
                if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "LEGADO":
                    _fuera |= {id(x) for x in ast.walk(n.value)}
            _cs = cadenas(_s)
            for n in ast.walk(_arb):
                if (isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value in _VIEJOS
                        and id(n) not in _fuera and n.value in _cs):
                    _hall.append("%s:%d %r" % (_rel, n.lineno, n.value))
chk("⚠️ ni «Gastos», ni «Calculos», ni «Alarmas»… fuera de `timeclock.LEGADO`", not _hall, _hall)
chk("CONTROL: el barrido ve los nombres viejos donde SÍ están (dentro de LEGADO)",
    {"Gastos", "Calculos", "Alarmas"} <= _VIEJOS)

# ══════════════════════════════════════════════════════════════════════════
print("\n4-6. El Survey ENTERO con AppTest (la IA y el correo sustituidos)")
G = r'''
import streamlit as st
import pandas as pd
import importlib
st.session_state.setdefault("auth", {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"})
from core import survey_ui as SU, flash, incrustar, plan_ui
plan_ui = importlib.reload(plan_ui)
SU.plan_ui = plan_ui
_LL = st.session_state.setdefault("_LL", [])
incrustar.script = lambda html, *a, **k: _LL.append(html)
_INT = {k: "x" for k in ("parametros", "estado_inicial", "desplazamientos", "solucion_optima",
                         "evasion_pared", "bsr_vs_bs", "consideraciones")}
_INT["_ok"] = True
_INTU = {k: "x" for k in ("resumen", "desplazamientos", "cortes", "implementacion", "verificacion")}
_INTU["_ok"] = True
SU.generate_interpretation = lambda *a, **k: dict(_INT)
SU.generate_user_interpretation = lambda *a, **k: dict(_INTU)
def _correo(*a, **k):
    st.session_state["_PDF_ADMIN"] = k.get("admin_report")
    return st.session_state.get("_ENVIA", True)
SU.send_usage_notification = _correo
_PRJ = {"ID": "PRJ-1", "Name": "Lift A", "Type": "Installation", "Status": "In progress",
        "Group": "cliente1", "NS": 6}
_PLANO = st.session_state.get("_PLANO", {})
SU.plan_ui.selector_proyecto = lambda key, ayuda="": ((_PRJ, _PLANO) if st.session_state.get("_OBRA") else (None, {}))
SU.projects_data.head_installers_label = lambda *a, **k: "CI"
SU.projects_data.is_configured = lambda: True
SU.projects_data.list_projects = lambda *a, **k: st.session_state.get("_LISTA", [])
SU.init_state()
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
_LISTA = [{"ID": "PRJ-1", "Name": "Lift A", "Type": "Installation", "Status": "In progress", "NS": 6},
          {"ID": "PRJ-9", "Name": "Lift A", "Type": "Installation", "Status": "Cancelled", "NS": 4},
          {"ID": "PRJ-8", "Name": "Truck", "Type": "Delivery", "Status": "Planned"},
          {"ID": "PRJ-7", "Name": "Lift B", "Type": "Ripout + Installation", "Status": "Planned"}]


def _todo(a):
    return " | ".join(str(x.value) for k in ("markdown", "caption", "info", "warning", "error",
                                              "success", "header", "subheader") for x in getattr(a, k, []))


at = AppTest.from_string(G, default_timeout=600)
at.session_state["_CON_DATOS"] = True
at.session_state["_OBRA"] = True
at.session_state["_PLANO"] = {"params": {}, "faltan": [], "n_params": 17, "n_total": 17}
at.session_state["_LISTA"] = _LISTA
at.run()
chk("con obra y plano de la obra: sin excepción", not at.exception, [e.value for e in at.exception][:1])
_md = " ".join(str(m.value) for m in at.markdown)
chk("⚠️ el chip dice «Drawing from the project» y «Parameters complete» (decía «No drawing»)",
    "Drawing from the project" in _md and "Parameters complete" in _md and "No drawing" not in _md, _md[-400:])
next(b for b in at.button if b.key == "btn_calc_datos").click()
at.run()
chk("calcula sin excepción", not at.exception, [e.value for e in at.exception][:1])
_ok = " ".join(str(x.value) for x in at.success)
_inf = " ".join(str(x.value) for x in at.info)
chk("⚠️ tras calcular SE VEN los avisos (`flash`): «Calculation and interpretation completed.»",
    "Calculation and interpretation completed." in _ok, _ok[:300])
chk("…y el del correo, porque SE ENVIÓ («sent by email»)", "sent by email" in _inf, _inf[:300])
_t = _todo(at)
chk("⚠️ plurales: «optimal solutions» y «values out of limit», ningún «(s)»",
    "optimal solutions**" in _t and "(s)" not in _t, [x for x in re.findall(r"[^|]{0,40}\(s\)[^|]{0,20}", _t)][:4])
_k = {b.key: str(b.label) for b in at.button if str(b.key or "").startswith("cpxkpi_sv_")}
chk("⚠️ las cuatro cifras son BOTONES (eran `st.metric`)",
    set(_k) == {"cpxkpi_sv_rl", "cpxkpi_sv_fb", "cpxkpi_sv_off", "cpxkpi_sv_sol"}
    and "mm" in _k.get("cpxkpi_sv_rl", "") and not [m for m in at.metric if str(m.label) == "Out of limit"], _k)
_df_comp = [d.value for d in at.dataframe if "" in list(getattr(d.value, "columns", []))]
chk("«active» en la comparación de soluciones (decía «activa»)",
    bool(_df_comp) and "active" in list(_df_comp[0][""]) and "activa" not in list(_df_comp[0][""]),
    [list(d[""]) for d in _df_comp][:1])
_exp = [str(e.label) for e in list(at.expander) + list(at.status)]
chk("ningún título con «FB aplic.»", not [x for x in _exp if "aplic" in x], [x for x in _exp if "aplic" in x])
# ── la cifra «Out of limit» lleva a los pisos con problemas ──
_LL0 = len(at.session_state["_LL"])
at.session_state["diag_modo"] = "Todos"
next(b for b in at.button if b.key == "cpxkpi_sv_off").click()
at.run()
_scr = at.session_state["_LL"][_LL0:]
chk("⚠️ tocar «Out of limit» pone los pisos «With issues» y BAJA al plano por piso (arriba del todo)",
    at.session_state["diag_modo"] == "With issues"
    and any(".st-key-cpx_sv_planta" in s and "block:'start'" in s for s in _scr), _scr[-1:][:1])
_LL0 = len(at.session_state["_LL"])
next(b for b in at.button if b.key == "cpxkpi_sv_rl").click()
at.run()
chk("…RL/FB, a la plomada", any(".st-key-cpx_sv_plomo" in s for s in at.session_state["_LL"][_LL0:]))
_LL0 = len(at.session_state["_LL"])
next(b for b in at.button if b.key == "cpxkpi_sv_sol").click()
at.run()
chk("…y «Optimal solutions», a la optimización",
    any(".st-key-cpx_sv_opt" in s for s in at.session_state["_LL"][_LL0:]))
_LL0 = len(at.session_state["_LL"])
at.run()
chk("…UNA vez: la pasada siguiente no vuelve a bajar", not [s for s in at.session_state["_LL"][_LL0:]
                                                         if ".st-key-cpx_sv_" in s])
# ── «Save to the project» ──
_sel = at.selectbox(key="sv_prj_sel")
chk("⚠️ el destino viene ELEGIDO con la obra del cálculo (antes, «— choose the project —»)",
    _sel.value == "Lift A (PRJ-1)", _sel.value)
chk("⚠️ …y solo ofrece instalaciones abiertas (fuera la CANCELADA homónima y la entrega)",
    list(_sel.options) == ["— choose the project —", "Lift A (PRJ-1)", "Lift B (PRJ-7)"], list(_sel.options))
_sel.set_value("Lift B (PRJ-7)")
at.run()
chk("…y si quien guarda elige otra, se respeta", at.selectbox(key="sv_prj_sel").value == "Lift B (PRJ-7)")
# los datos para las secciones 7-8 (el cálculo de verdad)
_CR = at.session_state["calc_results"]
_PDF_ADMIN = at.session_state["_PDF_ADMIN"] if "_PDF_ADMIN" in at.session_state else None

# sin obras abiertas: un botón, no una ruta
at2 = AppTest.from_string(G, default_timeout=600)
at2.session_state["_CON_DATOS"] = True
at2.session_state["_ENVIA"] = False
at2.session_state["_LISTA"] = [{"ID": "PRJ-9", "Name": "Old", "Type": "Installation", "Status": "Cancelled"}]
at2.run()
next(b for b in at2.button if b.key == "btn_calc_datos").click()
at2.run()
_w = " ".join(str(x.value) for x in at2.warning)
chk("⚠️ si el correo NO sale, lo dice (antes «sent by email» con tener el PDF)",
    "was not sent" in _w and "sent by email" not in " ".join(str(x.value) for x in at2.info), _w[:300])
_t2 = _todo(at2)
chk("⚠️ sin obras abiertas: lo dice, sin «My company» (que no existe)",
    "no open installation projects" in _t2 and "My company" not in _t2, _t2[-300:])
_bp = next((b for b in at2.button if b.key == "sv_ir_proyectos"), None)
chk("…con un botón a Projects", _bp is not None)
if _bp is not None:
    _bp.click()
    at2.run()
    chk("…que lleva a Projects", tuple(at2.session_state["_admin_nav_pending"]) == ("proyectos", "📊 Proyectos"))

# el mensaje del riel, con SU color
at3 = AppTest.from_string(G, default_timeout=600)
at3.session_state["rail_ref_msg"] = (":orange[:material/warning:] Rail **T9** was detected but **it is "
                                     "not in the Rails catalogue**. Enter RAIL by hand or add it to the catalogue.")
at3.run()
chk("⚠️ el riel que NO está en el catálogo sale como AVISO (salía como `info`, en azul)",
    any("T9" in str(x.value) for x in at3.warning) and not any("T9" in str(x.value) for x in at3.info))

# ══════════════════════════════════════════════════════════════════════════
print("\n7. Los diagramas: «AXIS OFFSET» y el nombre medido y escapado")
from core import diagrams as DG, plumb as PB, texto_svg as TS   # noqa: E402
_ap, _lim, _best = _CR["all_params"], _CR["limits"], _CR["optimizer_result"]["best"]
_lm = _CR["lim_map"]
_plantas = "".join(DG.floor_plan_svg(_ap, _lim, row, i, _lm, rl=_best["rl"], fb=_best["fb"],
                                     n_floors=len(_best["matrix"]), proyecto="Bondi Junction Tower — Lift 1")
                   for i, row in enumerate(_best["matrix"]))
chk("⚠️ el plano por piso ya no dice «EJES» (y SÍ «AXIS OFFSET», la sonda lo ve)",
    "EJES" not in _plantas and "AXIS OFFSET" in _plantas)
chk("⚠️ el nombre ENTERO en el cajetín (salía «Bondi Junction Tower — L»)",
    "Bondi Junction Tower — Lift 1<" in _plantas)
_raro = "Smith & Sons <Tower> — Lift 1"
_svgs = [DG.floor_plan_svg(_ap, _lim, _best["matrix"][0], 0, _lm, proyecto=_raro),
         DG.shaft_iso_svg(_ap, _lim, _best, len(_best["matrix"]), _lm, proyecto=_raro),
         PB.plumb_svg(_CR["plumb"], proyecto=_raro), PB.plumb_iso_svg(_CR["plumb"], proyecto=_raro),
         PB.plumb_detail_svg(_CR["plumb"], proyecto=_raro), PB.plumb_card_svg(_CR["plumb"], proyecto=_raro)]
_malos = []
for _i, _s in enumerate(_svgs):
    try:
        ET.fromstring(_s)
    except ET.ParseError as e:
        _malos.append((_i, str(e)))
chk("⚠️ una obra «Smith & Sons <Tower>» deja los SEIS SVG válidos (el «&» los rompía)",
    not _malos and all("Smith &amp; Sons" in s for s in _svgs), _malos)
_largo = "Westfield Bondi Junction Shopping Centre — Car Park Goods Lift Number 14 East"
_c = TS.cabe(_largo, 140, 7.5)
chk("un nombre que NO cabe se corta con «…» y cabe (medido con Helvetica)",
    _c.endswith("…") and TS.ancho(_c, 7.5) <= 140 and len(_c) > 20, (_c, TS.ancho(_c, 7.5)))
chk("…y uno que cabe, entero", TS.cabe("Bondi Junction Tower — Lift 1", 140, 7.5) == "Bondi Junction Tower — Lift 1")

print("\n8. Los informes, los archivos y el resto")
if _PDF_ADMIN:
    from pypdf import PdfReader
    _tp = " ".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(_PDF_ADMIN)).pages)
    chk("⚠️ el PDF TÉCNICO sin «value(s)»", "value(s)" not in _tp and "out of limit" in _tp)
else:
    chk("se generó el PDF técnico", False)
from core.user_report import generate_user_report                # noqa: E402
from pypdf import PdfReader                                      # noqa: E402
_bu = dict(_best, total_off=3)
_pdfu = generate_user_report(_ap, _lim, dict(_CR["optimizer_result"], best=_bu), _lm,
                             ["WR", "FR", "OR", "WL", "FL", "OL"], _CR["interpretation_user"],
                             schedule=_CR.get("schedule"), plumb=_CR.get("plumb"))
_tu = " ".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(_pdfu)).pages)
chk("⚠️ el PDF del CLIENTE con su plural («3 values out of limit», ningún «(s)»)",
    "value(s)" not in _tu and "3 values" in _tu.replace("\n", " "), re.findall(r".{20}value.{20}", _tu)[:3])
from core.calculations import validate_inputs                    # noqa: E402
_v = validate_inputs({"BKS": 0.0, "TKSW": 1, "TS": 1, "TK": 1, "SF1": 1, "SF2": 1, "RAIL": 1,
                      "BSR": 1, "FS": 50.0, "TSW": 100.0})
chk("«(now 0)» y «FS (50) … TSW (100)», no «0.0» / «50.0»",
    "BKS must be greater than 0 (now 0)." in _v and any("FS (50) is smaller than TSW (100)" in x for x in _v), _v)
from core.excel_io import export_survey_excel, import_survey_excel   # noqa: E402
import openpyxl                                                       # noqa: E402
import pandas as pd                                                   # noqa: E402
_x = export_survey_excel(pd.DataFrame({c: [1.0, 2.0] for c in ["WR", "FR", "OR", "WL", "FL", "OL"]}),
                         {"BS": 1998.0}, {"NS": 2})
_wb = openpyxl.load_workbook(io.BytesIO(_x))
chk("el Excel: «Stop», «Parameter», «Value» (eran «Parada», «Parámetro», «Valor»)",
    _wb["SURVEY"]["A2"].value == "Stop" and _wb["INFO"]["A2"].value == "Parameter"
    and _wb["INFO"]["B2"].value == "Value")
_wb["SURVEY"]["A2"].value = "Parada"                                  # un Excel VIEJO
_b = io.BytesIO()
_wb.save(_b)
_b.seek(0)
_imp = import_survey_excel(_b)
chk("…y un Excel viejo con «Parada» se sigue importando", list(_imp["df"]["WR"]) == [1.0, 2.0])
_cad = cadenas(fuente("core/survey_ui.py")) + cadenas(fuente("core/email_notify.py")) \
    + cadenas(fuente("core/projects_ui.py"))
_es = [c for c in _cad if c in ("plano.pdf", "matriz_survey.csv", "informe_cliente.pdf", "Nivel")
       or c.startswith("informe_") and c.endswith((".pdf", "_"))]
chk("⚠️ ningún archivo con nombre en español (plano.pdf, matriz_survey.csv, informe_…)", not _es, _es)
from core.num import nombre_archivo                                   # noqa: E402
chk("el nombre del PDF del cliente, sin la raya larga", nombre_archivo("Bondi Junction Tower — Lift 1")
    == "Bondi_Junction_Tower_Lift_1" and nombre_archivo("") == "survey")
_SU = fuente("core/survey_ui.py")
_dc = next(n for n in ast.walk(ast.parse(_SU)) if isinstance(n, ast.FunctionDef) and n.name == "_do_calculo")
_pierde = [ast.unparse(n.func) for n in ast.walk(_dc) if isinstance(n, ast.Call)
           and ast.unparse(n.func) in ("st.success", "st.info", "st.warning")]
chk("⚠️ en el cálculo ningún `st.success/info/warning` (los relanza un `st.rerun()`: van por `flash`)",
    not _pierde, _pierde)
# ⚠️ por las CADENAS del código: la 1ª vuelta casó con MI comentario (trampa 2)
_csu = cadenas(_SU)
chk("fuera el «— see the sidebar» (ese panel se quitó en v93) y el «Enter by hand» perdido",
    not [c for c in _csu if "see the sidebar" in c or "Enter by hand" in c])
chk("la franja de después de guardar ya no REPITE «updated with the survey»",
    not [c for c in _csu if "updated with the survey" in c]
    and any("keeps the one you saved" in c for c in _csu))

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
sys.exit(1 if fallos else 0)
