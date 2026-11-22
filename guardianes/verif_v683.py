# -*- coding: utf-8 -*-
"""v683 · Ciclo 4 → mejoras 3/3: el asistente y lo visto en el campo.

- H15 · el Management assistant no veía lo que dieron el Survey ni las herramientas de una obra: «I can't give you the
  numbers. The job data only lists the saved files» (ni el corte de riel de −290 mm). Nueva consulta de SOLO lectura,
  `get_calculations`, solo para la oficina.
- F1 · «My route» del campo en sábado o domingo abría en ese día («Nothing is planned for you on Sat 21/11»): el lunes,
  como la ruta de la oficina, si ese día no tiene obras. F2 · en su día de vacaciones decía «Nothing is planned» sin decir
  que está de vacaciones.
"""
import io
import json
import os
import sys

RAIZ = r"C:\Users\diego\P1\survey_app"
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:700]))
    if not cond:
        FALLOS.append(nombre)


def sec(t):
    print("\n" + t)


import streamlit as st                                                  # noqa: E402
from core import chat_tools as CT, projects as P, toolruns as TR         # noqa: E402

# ══════════════════════════════════════════════════════════════════════════════
sec("1. get_calculations: lo que dieron el Survey y las herramientas (H15)")
chk("está entre las consultas de la OFICINA", "get_calculations" in [h["name"] for h in CT.LECTURA_OFICINA])
chk("…y NO entre las del campo", "get_calculations" not in [h["name"] for h in CT._POR_ROL["field"]])
COLS = ["WR", "FR", "OR", "WL", "FL", "OL"]
M = [(99, 879, 402, 106, 874, 386), (98, 877, 405, 106, 867, 382), (103, 864, 390, 109, 854, 403),
     (110, 869, 419, 108, 879, 405), (105, 859, 392, 101, 861, 402), (109, 872, 385, 90, 867, 383),
     (103, 871, 396, 111, 855, 387), (102, 844, 403, 83, 865, 409), (93, 880, 379, 101, 853, 393),
     (96, 873, 380, 113, 869, 401), (115, 842, 385, 103, 857, 385), (111, 845, 400, 101, 851, 392)]
PAR = {"TKSW": 1000, "BKS": 1600, "TKA": 100, "TKS": 35, "TSW": 100, "BGS": 850, "BKF1": 420, "BKF2": 430,
       "BS": 1854, "BT": 800, "BK": 1050, "TK": 1350, "TS": 1760, "SF1": 60, "SF2": 70, "SG": 320, "TG": 70,
       "BSR": 1840, "RAIL": 62, "OFFSET_CABIN": 0, "FRAME": 30, "OMEGA_SIDE": "R", "OFFSET_SIDE": "R", "FS": 140,
       "WALL_LIMITING": True, "WALL_STOP": 4, "WALL_SIDE": "R", "CTRL_IN_FRAME": False, "CTRL_SIDE": None, "NS": 12,
       "LengthTemplate": 600}
RUNS = [  # del más reciente al más antiguo, como `toolruns.list_for`
    {"Tool": "belting", "Date": "2026-11-16 12:59", "Summary": "Lift 1: DSTS 13.5, Lift 2: DSTS -26.5",
     "DataJSON": json.dumps({"entradas": {}, "resultados": {"hgp": 90.0, "hq": 16500.0, "results": [
         {"elevador": 1, "hgpr": 120.0, "dsts": 13.5}, {"elevador": 2, "hgpr": 80.0, "dsts": -26.5}]}})},
    {"Tool": "buffers", "Date": "2026-11-16 12:58", "Summary": "HKP 160 · Buffer 3: -10.0",
     "DataJSON": json.dumps({"entradas": {}, "resultados": {"HKP": 160.0, "buffers": [
         {"n": 3, "HKPR": 170.0, "CutBuffer": -10.0, "warn": True}]}})},
    {"Tool": "rieles", "Date": "2026-11-16 12:57", "Summary": "Case 2 (above the FFL) · 2 lifts",
     "DataJSON": json.dumps({"entradas": {}, "resultados": {"subcaso": "encima", "elevadores": [
         {"CutRZ": 950.0, "CutRO": 940.0, "CutRF": 790.0, "CutRB": 800.0},
         {"CutRZ": 1000.0, "CutRO": 990.0, "CutRF": -290.0, "CutRB": 830.0}]}})},
    {"Tool": "rieles", "Date": "2026-11-10 09:00", "Summary": "VIEJO", "DataJSON": "{}"},
    {"Tool": "plomada", "Date": "2026-11-16 12:56", "Summary": "Template DBP 1662.0",
     "DataJSON": json.dumps({"entradas": {}, "resultados": {"plantilla": {"dbp": 1662.0, "d1": 1025.0},
                                                            "elevadores": [{"Lift": 1, "di (left wall→plumb)": 77.0}]}})},
    {"Tool": "survey", "Date": "2026-11-16 12:54", "Summary": "RL -25.0 · FB +16.0", "DataJSON": "{}"},
]
_obra_r, _full_r, _list_r = CT._obra, P.get_project_full, TR.list_for
try:
    CT._obra = lambda e, c: {"ID": "PRJ-0045", "Name": "C4 — Obra"}
    P.get_project_full = lambda pid: {"params": dict(PAR), "matriz": [dict(zip(COLS, map(float, r))) for r in M]}
    TR.list_for = lambda pid: list(RUNS)
    _ctx = {"rol": "administrator", "usuario": "Admin2", "grupo": "cliente1"}
    _txt, _err = CT.ejecutar("get_calculations", {"project_id": "PRJ-0045"}, _ctx)
    out = json.loads(_txt) if not _err else {}
    _txt_c, _err_c = CT.ejecutar("get_calculations", {"project_id": "PRJ-0045"}, dict(_ctx, rol="field"))
    P.get_project_full = lambda pid: {}
    TR.list_for = lambda pid: []
    vacio = json.loads(CT.ejecutar("get_calculations", {"project_id": "PRJ-0045"}, _ctx)[0])
finally:
    CT._obra, P.get_project_full, TR.list_for = _obra_r, _full_r, _list_r
chk("sin error", not _err, _txt[:300])
s = out.get("survey") or {}
chk("el Survey recalculado: «25.0 mm to the RIGHT» y «16.0 mm towards the REAR»",
    s.get("lateral_shift") == "25.0 mm to the RIGHT" and s.get("front_back_shift") == "16.0 mm towards the REAR", s)
chk("…con el muro: piso 4, no se corta, esquivado (13.0 mm de empuje extra: la solución única de v682)",
    (s.get("limiting_wall") or {}).get("cut") is False and s["limiting_wall"]["stop"] == 4
    and s["limiting_wall"]["cleared_by_extra_push_towards_rear_mm"] == 13.0, s.get("limiting_wall"))
chk("…los cortes de apertura SIN el muro (11 pisos, ninguno a la derecha del 4)",
    len(s.get("opening_cuts") or []) == 11 and not any(c["floor"] == 4 and c.get("cut_right_side_of_opening_mm")
                                                        for c in s.get("opening_cuts") or []), s.get("opening_cuts"))
chk("…y la plomada: di + DBP + dd = BSR 1840.0", (s.get("plumb_lines") or {}).get("check") == "di + DBP + dd = BSR 1840.0"
    and s["plumb_lines"]["between_plumbs_dbp_mm"] == 1662.0, s.get("plumb_lines"))
chk("…con la fecha en que se guardó (16/11/2026)", s.get("saved_on") == "16/11/2026", s.get("saved_on"))
h = out.get("site_tools") or {}
chk("⚠️ Rieles: el ÚLTIMO cálculo, con el negativo señalado (lift 2 RF −290)",
    (h.get("Rail cutting") or {}).get("negative_values") == [{"lift": 2, "rail": "RF", "mm": -290.0}]
    and h["Rail cutting"]["summary"] != "VIEJO", h.get("Rail cutting"))
chk("Buffers, Belting y la Plomada, con sus valores", (h.get("Buffer cutting") or {}).get("per_buffer", [{}])[0].get("CutBuffer") == -10.0
    and (h.get("Belting") or {}).get("per_lift", [{}])[1].get("dsts") == -26.5
    and (h.get("Plumb lines") or {}).get("template", {}).get("dbp") == 1662.0, h)
chk("el Survey no sale como herramienta (va arriba, recalculado)", "Lift survey" not in h, list(h))
chk("cómo leerlo: el muro no se corta, y qué es un negativo en cada herramienta",
    "NEVER cut" in out.get("how_to_read", "") and "falls short" in out.get("how_to_read", "")
    and "HKPR is greater" in out.get("how_to_read", ""), out.get("how_to_read"))
chk("⚠️ el campo no la puede pedir aunque la nombre el modelo", _err_c and "Unknown tool" in _txt_c, _txt_c[:120])
chk("una obra sin nada guardado: survey null y sin herramientas", vacio.get("survey") is None and vacio.get("site_tools") == {},
    vacio)
_ca = io.open(os.path.join(RAIZ, "core", "chat_agent.py"), encoding="utf-8").read()
# v692 · la línea dice ahora también «las cotizaciones, el inventario» (H20 del ciclo 5); lo del Survey sigue
chk("la guía de la oficina lo sabe", "y lo que dieron el Survey y las herramientas técnicas de una obra" in _ca)

# ══════════════════════════════════════════════════════════════════════════════
sec("2. «My route» en fin de semana (F1) y en un día de ausencia (F2)")
from streamlit.testing.v1 import AppTest                                # noqa: E402
GR = r'''
import datetime as dt
import streamlit as st
from core import clock as CK, route_ui as RT, roster as R
if not hasattr(CK, "_today_real"):
    CK._today_real = CK.today
if not hasattr(RT, "_obras_real"):
    RT._obras_real = RT.obras_de_mi_dia
if not hasattr(R, "_asig_real"):
    R._asig_real = R.asignaciones_dia
CK.today = lambda *a, **k: dt.date(*st.session_state["_HOY"])
_OB = st.session_state.get("_OBRAS", {})
RT.obras_de_mi_dia = lambda u, g, f: list(_OB.get(f.isoformat(), []))
R.asignaciones_dia = lambda g, u, f: list(st.session_state.get("_ASIG", {}).get(f.isoformat(), []))
try:
    RT.render_mi_ruta("campo000", "cliente1")
finally:
    CK.today, RT.obras_de_mi_dia, R.asignaciones_dia = CK._today_real, RT._obras_real, R._asig_real
'''
_SITIO = [{"ID": "PRJ-1", "Name": "Darling Park", "Group": "cliente1"}]


def ruta(hoy, obras=None, asig=None):
    a = AppTest.from_string(GR, default_timeout=60)
    a.session_state["_HOY"] = hoy
    a.session_state["_OBRAS"] = obras or {}
    a.session_state["_ASIG"] = asig or {}
    a.run()
    return a


def _dia(a):
    return next((d.value for d in a.date_input if d.key == "miruta_dia"), None)


def _txt(a):
    return " | ".join(str(x.value) for k in ("info", "caption", "markdown") for x in getattr(a, k, []))


import datetime as dt                                                   # noqa: E402
a = ruta((2026, 11, 21), {"2026-11-23": _SITIO})
chk("sin excepción", not a.exception, [e.value for e in a.exception][:1])
chk("⚠️ F1: el sábado sin obras abre en el LUNES 23/11", _dia(a) == dt.date(2026, 11, 23), _dia(a))
a = ruta((2026, 11, 22), {"2026-11-23": _SITIO})
chk("…el domingo también", _dia(a) == dt.date(2026, 11, 23), _dia(a))
a = ruta((2026, 11, 21), {"2026-11-21": _SITIO, "2026-11-23": _SITIO})
chk("…pero un sábado CON obra en su tablero se queda en el sábado", _dia(a) == dt.date(2026, 11, 21), _dia(a))
a = ruta((2026, 11, 18), {"2026-11-23": _SITIO})
chk("…y entre semana, hoy (aunque no tenga nada)", _dia(a) == dt.date(2026, 11, 18), _dia(a))
a = ruta((2026, 11, 20), {}, {"2026-11-20": [{"asig": "LEAVE", "nota": "Annual leave · AUS-0007", "proyecto_id": "",
                                              "etiqueta": "Leave", "color": "", "es_estado": True}]})
chk("⚠️ F2: en su día de vacaciones: «You are off on Fri 20/11/2026: Annual leave · AUS-0007.»",
    "You are off on Fri 20/11/2026: Annual leave · AUS-0007." in _txt(a), _txt(a)[:300])
a = ruta((2026, 11, 18), {}, {})
chk("…y un día sin nada, «Nothing is planned for you»", "Nothing is planned for you on Wed 18/11/2026" in _txt(a), _txt(a)[:300])

print()
print(f"=== {('TODO OK' if not FALLOS else str(len(FALLOS)) + ' FALLO(S)')} ===")
sys.exit(1 if FALLOS else 0)
