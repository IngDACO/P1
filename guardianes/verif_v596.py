"""v596 · LO VISTO VERIFICANDO v595 (decisión del usuario: «dale»).

En producción (20/10/2026, Bondi L1, HGPR 120 y 70): el mismo DSTS salía «21» en la tabla y en el
diagrama y «21.0» en la posición, el resumen guardado y el PDF; y con un -28.5 la misma columna
mezclaba «21» y «-28.5». → UN decimal en todas partes.
"""
import json
import os
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


G = r'''
import streamlit as st
import importlib
st.session_state.setdefault("auth", {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"})
from core import plan_ui, flash, incrustar, toolruns, projects as P
plan_ui = importlib.reload(plan_ui)
from core import belting_ui
_SVG = st.session_state.setdefault("_SVG", [])
incrustar.dibujo = lambda html, *a, **k: _SVG.append(html)
incrustar.script = lambda html, *a, **k: None
_PRJ = {"ID": "PRJ-1", "Name": "Lift A", "Type": "Installation", "Status": "In progress", "Group": "cliente1"}
plan_ui.selector_proyecto = lambda key, ayuda="": (_PRJ, {"hq": 14000, "hgp": 85})
P.list_projects = lambda *a, **k: [_PRJ]
toolruns.is_configured = lambda: True
def _reg(**k):
    st.session_state.setdefault("_REG", []).append(k)
    return {"ok": True, "id": "CAL-9", "drive_id": "x"}
toolruns.registrar = _reg
def _pdf(titulo, **k):
    st.session_state["_PDFT"] = (titulo, k)
    return b"%PDF-1.4 prueba"
belting_ui.tool_pdf = _pdf
flash.mostrar()
belting_ui.render_belting_tab()
'''

print("1. El DSTS con UN decimal en la tabla, el diagrama, la posición, el resumen y el PDF")
at = AppTest.from_string(G, default_timeout=300)
at.run()
at.number_input(key="belt_ns").set_value(2).run()
at.number_input(key="belt_hgpr_0").set_value(120.0).run()
at.number_input(key="belt_hgpr_1").set_value(70.5).run()
next(b for b in at.button if b.key == "belt_calc").click()
at.run()
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
_r = at.session_state["belt_res"] if "belt_res" in at.session_state else {}
chk("(el caso: DSTS 21.0 y -28.5 — uno entero y otro no, la mezcla de producción)",
    [x["dsts"] for x in _r.get("results", [])] == [21.0, -28.5], _r.get("results"))
_cols = json.loads(at.dataframe[0].proto.columns) if list(at.dataframe) else {}
_tc = (_cols.get("DSTS (mm)") or {}).get("type_config") or {}
chk("⚠️ la columna «DSTS (mm)» con formato «%.1f» (salía «21» junto a «21.0»)",
    _tc.get("type") == "number" and _tc.get("format") == "%.1f", _cols.get("DSTS (mm)"))
# (la 1ª suite dio un rojo de VERDAD en verif_v579: el formato iba SIN etiqueta, y la regla de
# v579 exige que ninguna columna configurada quede sin etiqueta ni traducción)
chk("…con su ETIQUETA «DSTS (mm)» (la regla de v579)",
    (_cols.get("DSTS (mm)") or {}).get("label") == "DSTS (mm)", _cols.get("DSTS (mm)"))
_svg = (at.session_state["_SVG"] if "_SVG" in at.session_state else [""])[-1]
_ini = _svg.find("<svg")
_t = [x.text or "" for x in ET.fromstring(_svg[_ini:_svg.rfind("</svg>") + 6]).iter(
    "{http://www.w3.org/2000/svg}text")] if _ini >= 0 else []
chk("⚠️ el diagrama: «DSTS 21.0 mm» y «DSTS -28.5 mm» (decía «DSTS 21 mm»)",
    "DSTS 21.0 mm" in _t and "DSTS -28.5 mm" in _t, [x for x in _t if x.startswith("DSTS")])
_df = at.dataframe[0].value
chk("…la posición, igual («21.0 mm below…», «28.5 mm above…»)",
    list(_df["Position"]) == ["21.0 mm below the top FFL", "28.5 mm above the top FFL"], list(_df["Position"]))
next(b for b in at.button if b.key == "save_belt").click()
at.run()
_reg = at.session_state["_REG"] if "_REG" in at.session_state else []
chk("…el resumen guardado («Lift 1: DSTS 21.0, Lift 2: DSTS -28.5»)",
    bool(_reg) and _reg[-1].get("resumen") == "Lift 1: DSTS 21.0, Lift 2: DSTS -28.5",
    _reg[-1].get("resumen") if _reg else "")
_pt = at.session_state["_PDFT"] if "_PDFT" in at.session_state else ("", {})
_filas = ((_pt[1].get("tablas") or [("", [])])[0][1])
chk("…y la tabla del PDF (las celdas salen por `str()`: 21.0 y -28.5)",
    [str(f.get("DSTS (mm)")) for f in _filas] == ["21.0", "-28.5"], _filas)

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
sys.exit(1 if fallos else 0)
