# -*- coding: utf-8 -*-
"""v682 · Ciclo 4 → mejoras 2/3: archivos y herramientas (visto ejercitando el ciclo 4 en PRJ-0045, 16/11/2026).

- H14 · Rieles, Caso 2: «CutRF Lift 2 = −290 mm» salía sin una palabra y así se guardaba (CAL-0019).
- H8/H9 · el Survey archivaba «drawing.pdf», «survey_matrix.csv» y «client_report.pdf»: el plano otra vez y, al
  guardar de nuevo, DOS de cada sin forma de saber cuál vale. Y sustituía el Survey de la obra sin decirlo.
- H7 · «Riel: T75-3/B» y «RAIL (altura): 62» en «Drawing read». H10 · «Clear everything» no decía nada.
- La Plomada pedía otra vez la plantilla y el BSR que el Survey ya guardó (600 y 1840).
- Buffers «check» en minúscula; Tools → Home «Last used · nombre» sin el ID.
"""
import ast
import io
import os
import sys

RAIZ = r"C:\Users\diego\P1\survey_app"
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Admin2", "rol": "administrator", "grupo": "cliente1"}
from streamlit.testing.v1 import AppTest                         # noqa: E402
import pandas as pd                                               # noqa: E402

FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:600]))
    if not cond:
        FALLOS.append(nombre)


def sec(t):
    print("\n" + t)


def fuente(rel):
    return io.open(os.path.join(RAIZ, rel), encoding="utf-8").read()


def _todo(a):
    return " | ".join(str(x.value) for k in ("markdown", "caption", "info", "warning", "error", "success")
                      for x in getattr(a, k, []))


# ══════════════════════════════════════════════════════════════════════════════
sec("1. Rieles, Caso 2: un negativo se dice (H14)")
G = r'''
import streamlit as st
import importlib
st.session_state.setdefault("auth", {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"})
from core import plan_ui, flash, incrustar, toolruns, projects as P
plan_ui = importlib.reload(plan_ui)
from core import rail_cut_ui
incrustar.dibujo = lambda html, *a, **k: None
incrustar.script = lambda html, *a, **k: None
_PRJ = {"ID": "PRJ-1", "Name": "Lift A", "Type": "Installation", "Status": "In progress", "Group": "cliente1"}
plan_ui.selector_proyecto = lambda key, ayuda="": (_PRJ, {"lfkk": 1150, "lfgk": 980})
P.list_projects = lambda *a, **k: [_PRJ]
toolruns.is_configured = lambda: True
def _reg(**k):
    st.session_state.setdefault("_REG", []).append(k)
    return {"ok": True, "id": "CAL-9", "drive_id": "x"}
toolruns.registrar = _reg
if not hasattr(rail_cut_ui, "_tool_pdf_real"):
    rail_cut_ui._tool_pdf_real = rail_cut_ui.tool_pdf
def _tp(*a, **k):
    st.session_state["_NOTAS"] = list(k.get("notas") or [])
    return rail_cut_ui._tool_pdf_real(*a, **k)
rail_cut_ui.tool_pdf = _tp
flash.mostrar()
rail_cut_ui.render_rail_cut_tab()
'''


def _btn(a, k):
    return next((b for b in a.button if b.key == k), None)


def caso2(rf2):
    a = AppTest.from_string(G, default_timeout=300)
    a.run()
    a.radio(key="rc_caso").set_value("Case 2 — last installed (the top one)").run()
    a.number_input(key="rc_n").set_value(2).run()
    a.session_state["rc_in_df"] = pd.DataFrame({"Riel": ["RZ", "RO", "RF", "RB"],
                                                "Elevador 1": [300.0, 310.0, 280.0, 290.0],
                                                "Elevador 2": [305.0, 300.0, rf2, 295.0]})
    a.run()
    _btn(a, "rc_calc2").click()
    a.run()
    return a


a = caso2(1500.0)                     # LFGK 980 − 1500 = −520
chk("sin excepción", not a.exception, [e.value for e in a.exception][:1])
_w = " | ".join(str(x.value) for x in a.warning)
chk("⚠️ el negativo se dice, con su ascensor y su riel: «lift 2 RF -520.0 mm»",
    "falls SHORT by that much: there is nothing to cut off it" in _w and "lift 2 RF -520.0 mm" in _w, _w[:400])
_nt = a.session_state["_NOTAS"] if "_NOTAS" in a.session_state else []
chk("…también en el PDF (su nota)", any("falls short by that much" in n for n in _nt), _nt)
_btn(a, "save_rc2").click()
a.run()
_reg = a.session_state["_REG"] if "_REG" in a.session_state else []
chk("…y en lo guardado: «Case 2 (above the FFL) · 2 lifts · CHECK: negative cut on lift 2 RF»",
    _reg and _reg[-1].get("resumen") == "Case 2 (above the FFL) · 2 lifts · CHECK: negative cut on lift 2 RF",
    _reg[-1].get("resumen") if _reg else None)
a = caso2(285.0)                      # sin negativos: nada
chk("sin negativos, ni aviso ni marca (el control)", "falls SHORT" not in " | ".join(str(x.value) for x in a.warning)
    and not any("falls short" in n for n in (a.session_state["_NOTAS"] if "_NOTAS" in a.session_state else [])))

# ══════════════════════════════════════════════════════════════════════════════
sec("2. Los ficheros del Survey en la obra (H8/H9), el aviso al sustituir y vaciar")
_su = fuente("core/survey_ui.py")
_cad = {n.value for n in ast.walk(ast.parse(_su)) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
chk("⚠️ ni «drawing.pdf», ni «survey_matrix.csv», ni «client_report.pdf» como nombre",
    not {"drawing.pdf", "survey_matrix.csv", "client_report.pdf"} & _cad, {"drawing.pdf", "survey_matrix.csv", "client_report.pdf"} & _cad)
chk("con la obra y la fecha: Drawing_<obra>.pdf, Survey_matrix_<obra>_<fecha>.csv, Client_report_<obra>_<fecha>.pdf",
    'f"Drawing_{_nom_f}.pdf"' in _su and 'f"Survey_matrix_{_nom_f}_{_marca_f}.csv"' in _su
    and 'f"Client_report_{_nom_f}_{_marca_f}.pdf"' in _su and '_marca_f = clock.now().strftime("%Y-%m-%d_%H%M")' in _su)
chk("el plano, solo si la obra no tiene ya uno", "if pb and not _ya_plano:" in _su
    and '_ya_plano = any(str(_dd.get("Type", "")) == "plano"' in _su)
chk("la oficina sabe ANTES que guardar sustituye el Survey de la obra",
    "already has a saved survey: saving this one replaces it" in _su
    and "if not _es_campo and _prj is not None and projects_data.tiene_survey(_prj):" in _su)
_cl = _su.split('key="btn_reset_survey"')[1][:500]
chk("«Clear everything» dice que ha vaciado", "flash.info(" in _cl and "Survey cleared" in _cl, _cl[:300])

# ══════════════════════════════════════════════════════════════════════════════
sec("3. «Drawing read» en inglés (H7)")
from core import plan_data as PD                                  # noqa: E402
_tab = PD.por_herramienta({"params": {"BS": 1}, "n_total": 17, "ns": 12, "rail": "T75-3/B", "rail_altura": 62.0})
_lbl = [l for g in _tab for l, _v in g["items"]]
chk("«Car guide rail» y «RAIL (tooth height)»", "Car guide rail" in _lbl and "RAIL (tooth height)" in _lbl, _lbl)
chk("…sin «Riel» ni «altura»", not [x for x in _lbl if "Riel" in x or "altura" in x], _lbl)

# ══════════════════════════════════════════════════════════════════════════════
sec("4. La Plomada, con lo que el Survey de la obra ya midió")
GP = r'''
import json
import streamlit as st
import importlib
st.session_state.setdefault("auth", {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"})
from core import plan_ui, incrustar
plan_ui = importlib.reload(plan_ui)
from core import plumb_ui
incrustar.dibujo = lambda html, *a, **k: None
incrustar.script = lambda html, *a, **k: None
_P = st.session_state.get("_PAR")
_PRJ = {"ID": "PRJ-1", "Name": "Lift A", "Type": "Installation", "Status": "In progress", "Group": "cliente1",
        "ParamsJSON": json.dumps(_P) if _P is not None else ""}
plan_ui.selector_proyecto = lambda key, ayuda="": (_PRJ, {"params": {"BKS": 1600.0}})
_lt = st.session_state.pop("_LT0", None)
if _lt is not None:
    st.session_state["plb_lt"] = _lt
plumb_ui.render_plumb_tab()
'''


def plomada(par, lt0=None):
    a = AppTest.from_string(GP, default_timeout=120)
    a.session_state["_PAR"] = par
    if lt0 is not None:
        a.session_state["_LT0"] = lt0
    a.run()
    return a


a = plomada({"LengthTemplate": 600, "BSR": 1840})
chk("sin excepción", not a.exception, [e.value for e in a.exception][:1])
chk("⚠️ LengthTemplate 600 y el BSR del ascensor 1, 1840, del Survey de la obra",
    float(a.session_state["plb_lt"]) == 600.0 and float(a.session_state["plb_bsr_df"]["BSR (mm)"].iloc[0]) == 1840.0,
    (a.session_state["plb_lt"], list(a.session_state["plb_bsr_df"]["BSR (mm)"])))
chk("…y lo dice", "From the project's survey (when empty): LengthTemplate 600 mm · BSR of lift 1 1840 mm." in _todo(a), _todo(a)[:300])
a = plomada({"LengthTemplate": 600, "BSR": 1840}, lt0=450.0)
chk("lo tecleado se respeta: con 450 puesto, se queda 450", float(a.session_state["plb_lt"]) == 450.0,
    a.session_state["plb_lt"])
a = plomada(None)
chk("una obra sin Survey: nada", float(a.session_state["plb_lt"]) == 0.0 and "From the project's survey" not in _todo(a))

# ══════════════════════════════════════════════════════════════════════════════
sec("5. Buffers «Check» y «Last used» con el ID")
_bc = fuente("core/buffer_cut_ui.py")
chk("Buffers: «Check», con mayúscula", 'd("Check") if b["warn"] else "OK"' in _bc and 'd("check")' not in _bc)
from core import home_ui as H, toolruns as TR, projects as P                     # noqa: E402
_ult_real, _gp_real, _rol_real = TR.ultimos_por_herramienta, P.get_project, H._rol
try:
    TR.ultimos_por_herramienta = lambda g, pids=None: {"plomada": {"ProjectID": "PRJ-1", "Date": "2026-11-16 12:00"}}
    P.get_project = lambda pid: {"Name": "Lift A"} if pid == "PRJ-1" else None
    H._rol = lambda: "administrator"
    _u = H._ultimos_usos("cliente1", ["🔩 Plomada"])
finally:
    TR.ultimos_por_herramienta, P.get_project, H._rol = _ult_real, _gp_real, _rol_real
chk("⚠️ «Last used 16/11/2026 · Lift A (PRJ-1)»", _u.get("🔩 Plomada") == "Last used 16/11/2026 · Lift A (PRJ-1)", _u)

# ══════════════════════════════════════════════════════════════════════════════
sec("6. Visto verificando v681: soluciones equivalentes, la nota del muro y las tablas de resultados")
from core.calculations import calculate_limits, apply_offsets, analyze_matrix       # noqa: E402
from core.optimizer import optimize                                                 # noqa: E402
from core import interpretation as I                                               # noqa: E402
COLS = ["WR", "FR", "OR", "WL", "FL", "OL"]
# la matriz de PRUEBA del ciclo 4 (PRJ-0045, sintética): el nivel 4 choca con el muro
M = [(99, 879, 402, 106, 874, 386), (98, 877, 405, 106, 867, 382), (103, 864, 390, 109, 854, 403),
     (110, 869, 419, 108, 879, 405), (105, 859, 392, 101, 861, 402), (109, 872, 385, 90, 867, 383),
     (103, 871, 396, 111, 855, 387), (102, 844, 403, 83, 865, 409), (93, 880, 379, 101, 853, 393),
     (96, 873, 380, 113, 869, 401), (115, 842, 385, 103, 857, 385), (111, 845, 400, 101, 851, 392)]


def base(**kw):
    p = {"TKSW": 1000, "BKS": 1600, "TKA": 100, "TKS": 35, "TSW": 100, "BGS": 850, "BKF1": 420, "BKF2": 430,
         "BS": 1854, "BT": 800, "BK": 1050, "TK": 1350, "TS": 1760, "SF1": 60, "SF2": 70, "SG": 320, "TG": 70,
         "BSR": 1840, "RAIL": 62, "OFFSET_CABIN": 0, "FRAME": 30, "OMEGA_SIDE": "R", "OFFSET_SIDE": "R", "FS": 140,
         "WALL_LIMITING": True, "WALL_STOP": 4, "WALL_SIDE": "R", "CTRL_IN_FRAME": False, "CTRL_SIDE": None, "NS": 12}
    p.update(kw)
    return p


def corre(p):
    df = pd.DataFrame([dict(zip(COLS, map(float, r))) for r in M])
    for c in COLS:
        p["%sT" % c] = float(df.iloc[-1][c])
    lim = calculate_limits(p)
    p.update(lim)
    adj = apply_offsets(df.to_dict("records"), lim)
    lim.update(analyze_matrix(adj, lim, wall_limiting=bool(p.get("WALL_LIMITING"))))
    opt = optimize(adj, lim, p)
    return {"p": p, "opt": opt, "best": opt["best"]}


_R = corre(base(FS=140))
_sols = _R["opt"]["all_solutions"]
_pos = {(s["rl"], s["fb_applied"]) for s in _sols}
chk("⚠️ FS 140: una solución por POSICIÓN (11, no 143 con 13 repetidas)", len(_sols) == len(_pos) == 11, (len(_sols), len(_pos)))
chk("…de las equivalentes, la de mayor fb del barrido (empuje extra mínimo: 13.0)", _R["best"]["fb"] == 3.0
    and I.empuje_extra(_R["best"]) == 13.0 and _R["best"]["fb_applied"] == 16.0, (_R["best"]["fb"], _R["best"]["fb_applied"]))
chk("sin muro, nada se agrupa que no sea igual (cada posición, una vez)",
    len({(s["rl"], s["fb_applied"]) for s in corre(base(WALL_LIMITING=False))["opt"]["all_solutions"]})
    == len(corre(base(WALL_LIMITING=False))["opt"]["all_solutions"]))
chk("la nota del muro dice el desplazamiento APLICADO (16.0), no la parte extra",
    I.texto_muro(I.muro_de(_R["p"]), _R["best"]) == "Floor 4, right side: limiting wall. It is not cut: the 16.0 mm shift "
    "towards the rear clears it.", I.texto_muro(I.muro_de(_R["p"]), _R["best"]))
from core import survey_ui as SUI                                                 # noqa: E402
_pp = SUI._por_paradas(pd.DataFrame({"WR": [1.0, 2.0, 3.0]}))
chk("las tablas de resultados, numeradas 1…NS (`_por_paradas`)", list(_pp.index) == [1, 2, 3], list(_pp.index))
_su2 = io.open(os.path.join(RAIZ, "core", "survey_ui.py"), encoding="utf-8").read()
chk("…la matriz ajustada y las soluciones se pintan con ella", "st.dataframe(_por_paradas(survey_adj_df).style" in _su2
    and "st.dataframe(_por_paradas(sol_df).style" in _su2)

print()
print(f"=== {('TODO OK' if not FALLOS else str(len(FALLOS)) + ' FALLO(S)')} ===")
sys.exit(1 if FALLOS else 0)
