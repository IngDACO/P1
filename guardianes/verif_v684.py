# -*- coding: utf-8 -*-
"""v684 · Lo visto verificando v683 en producción (el Management assistant con `get_calculations`, PRJ-0045):

- dijo «The stop 4 wall is out of its limit even after the 13 mm rear push. Check that wall on site.»: el hecho
  `within_its_limit: false` significaba «sin el empuje estaría fuera» y lo leyó como «sigue fuera». Ese hecho lo lee
  también el modelo del informe del CLIENTE. Ahora va en palabras (`how_it_is_handled`) y con `needs_attention: false`.
- vio «dos Rail_cutting_case2 repetidos»: lo archivado por las herramientas llevaba la fecha sin la hora.
"""
import io
import os
import re
import sys

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:600]))
    if not cond:
        FALLOS.append(nombre)


def sec(t):
    print("\n" + t)


import pandas as pd                                                                   # noqa: E402
from core.calculations import calculate_limits, apply_offsets, analyze_matrix         # noqa: E402
from core.optimizer import optimize                                                   # noqa: E402
from core import interpretation as I, chat_tools as CT                                # noqa: E402

COLS = ["WR", "FR", "OR", "WL", "FL", "OL"]
# la matriz de PRUEBA del ciclo 4 (PRJ-0045, sintética): el nivel 4 choca con el muro
M = [(99, 879, 402, 106, 874, 386), (98, 877, 405, 106, 867, 382), (103, 864, 390, 109, 854, 403),
     (110, 869, 419, 108, 879, 405), (105, 859, 392, 101, 861, 402), (109, 872, 385, 90, 867, 383),
     (103, 871, 396, 111, 855, 387), (102, 844, 403, 83, 865, 409), (93, 880, 379, 101, 853, 393),
     (96, 873, 380, 113, 869, 401), (115, 842, 385, 103, 857, 385), (111, 845, 400, 101, 851, 392)]


def hechos(fs):
    p = {"TKSW": 1000, "BKS": 1600, "TKA": 100, "TKS": 35, "TSW": 100, "BGS": 850, "BKF1": 420, "BKF2": 430,
         "BS": 1854, "BT": 800, "BK": 1050, "TK": 1350, "TS": 1760, "SF1": 60, "SF2": 70, "SG": 320, "TG": 70,
         "BSR": 1840, "RAIL": 62, "OFFSET_CABIN": 0, "FRAME": 30, "OMEGA_SIDE": "R", "OFFSET_SIDE": "R", "FS": fs,
         "WALL_LIMITING": True, "WALL_STOP": 4, "WALL_SIDE": "R", "CTRL_IN_FRAME": False, "CTRL_SIDE": None, "NS": 12}
    df = pd.DataFrame([dict(zip(COLS, map(float, r))) for r in M])
    for c in COLS:
        p["%sT" % c] = float(df.iloc[-1][c])
    lim = calculate_limits(p)
    p.update(lim)
    adj = apply_offsets(df.to_dict("records"), lim)
    lim.update(analyze_matrix(adj, lim, wall_limiting=True))
    opt = optimize(adj, lim, p)
    return I.hechos({"limits": lim, "analysis": lim, "optimizer_result": opt}, p)["solution"]["limiting_wall"]


sec("1. El muro, en palabras y sin «within_its_limit»")
w140, w120 = hechos(140), hechos(120)
chk("FS 140: «cleared by the 16.0 mm shift towards the REAR (it includes 13.0 mm of extra push for the wall)»",
    w140.get("how_it_is_handled") == "cleared by the 16.0 mm shift towards the REAR (it includes 13.0 mm of extra "
    "push for the wall)", w140)
chk("FS 120: «already clear: at that floor the car is far enough towards the REAR»",
    w120.get("how_it_is_handled") == "already clear: at that floor the car is far enough towards the REAR", w120)
chk("⚠️ needs_attention false y ya NO va «within_its_limit» (lo leyó como «sigue fuera»)",
    w140.get("needs_attention") is False and w120.get("needs_attention") is False
    and "within_its_limit" not in w140 and "within_its_limit" not in w120, (w140, w120))
_d = I.hechos({"limits": {"LIMIT_OR": 401.0, "LIMIT_OL": 401.0},
               "optimizer_result": {"best": {"rl": 0.0, "fb": 0.0, "fb_applied": 0.0, "total_off": 0, "off_by_col": {},
                                             "matrix": [{c: 100.0 for c in COLS}] * 4, "wall_evaded": False,
                                             "fb_extra_applied": False}}},
              {"WALL_LIMITING": True, "WALL_STOP": 2, "WALL_SIDE": "L", "NS": 4})["solution"]["limiting_wall"]
chk("dentro de su límite: «within its limit with these shifts»", _d.get("how_it_is_handled") == "within its limit with "
    "these shifts" and _d.get("needs_attention") is False, _d)
from core import projects as P, toolruns as TR                                       # noqa: E402
_o, _f, _l = CT._obra, P.get_project_full, TR.list_for
try:
    CT._obra = lambda e, c: {"ID": "PRJ-1", "Name": "Obra"}
    P.get_project_full = lambda pid: {}
    TR.list_for = lambda pid: []
    _how = CT._calculos({"project_id": "PRJ-1"}, {"rol": "administrator", "usuario": "u", "grupo": "g"})["how_to_read"]
finally:
    CT._obra, P.get_project_full, TR.list_for = _o, _f, _l
chk("cómo leerlo (get_calculations): needs_attention false = nada que comprobar; los buffers no son ascensores",
    "needs_attention false = nothing to check about the wall" in _how
    and "lists buffers (a pit can have more than one per lift), not lifts" in _how, _how)
chk("…y la consulta lo devuelve (está en LECTURA_OFICINA)", "get_calculations" in [h["name"] for h in CT.LECTURA_OFICINA])

sec("2. Lo archivado por las herramientas lleva la hora")
from streamlit.testing.v1 import AppTest                                              # noqa: E402
GS = r'''
import streamlit as st
from core import tool_save_ui as TS, toolruns
st.session_state.setdefault("auth", {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"})
toolruns.is_configured = lambda: True
_P = {"ID": "PRJ-1", "Name": "Lift A", "Type": "Installation", "Status": "In progress", "Group": "cliente1"}
if not hasattr(TS, "_proyectos_de_real"):
    TS._proyectos_de_real = TS._proyectos_de
TS._proyectos_de = lambda *a, **k: [_P]
def _reg(**k):
    st.session_state.setdefault("_REG", []).append(k)
    return {"ok": True, "id": "CAL-9", "drive_id": "x"}
toolruns.registrar = _reg
TS.render_guardar(herramienta="buffers", titulo_pdf="buffer cutting", pdf_bytes=b"%PDF-1.4 x", resumen="HKP 160",
                  datos={"HKP": 160.0}, nombre_archivo="Buffer_cutting_Lift_A_2026-11-16.pdf", key="bc", obra_id="PRJ-1")
'''
a = AppTest.from_string(GS, default_timeout=60)
a.run()
chk("sin excepción", not a.exception, [e.value for e in a.exception][:1])
_b = next((b for b in a.button if b.key == "save_bc"), None)
chk("se localiza «Save to the project»", _b is not None, [b.key for b in a.button])
if _b is not None:
    _b.click()
    a.run()
_r = a.session_state["_REG"] if "_REG" in a.session_state else []
_fn = _r[-1].get("filename", "") if _r else ""
chk("⚠️ archivado como «Buffer_cutting_Lift_A_2026-11-16_HHMM.pdf» (con la hora)",
    bool(re.fullmatch(r"Buffer_cutting_Lift_A_2026-11-16_\d{4}\.pdf", _fn)), _fn)
chk("…y la descarga sigue con su nombre de siempre", 'file_name=nombre_archivo, mime="application/pdf"' in
    io.open(os.path.join(RAIZ, "core", "tool_save_ui.py"), encoding="utf-8").read())

print()
print(f"=== {('TODO OK' if not FALLOS else str(len(FALLOS)) + ' FALLO(S)')} ===")
sys.exit(1 if FALLOS else 0)
