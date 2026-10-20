"""v593 · TOOLS → RAILS, PROBADA (decisión del usuario: «Ok dale»).

Visto en producción (20/10/2026, Bondi L1, 2 ascensores, A = 2×2500 + 3×5000):
  1. ⚠️ Resultados VIEJOS: las cifras y el PDF con LFKK/LFGK de AHORA junto a cortes del cálculo
     → aviso, ni descargar ni guardar, y cifras/PDF con los del cálculo.
  2. ⚠️ Sin validación: con todo en 0 calculaba («A 0 mm», cortes = los LF) y ofrecía PDF y
     guardar → se dice qué falta y no se calcula.
  3. ⚠️ Cambiar el nº de ascensores BORRABA lo tecleado (Rails y la tabla de BSR de la plomada).
  4. ⚠️ El Caso 2 decidía por el TEXTO de la opción (`startswith("Above")`) → constantes.
  5. Español en lo guardado («Caso 1 · E1:», «(encima)», «lift(s)», «corte_rieles_*.pdf»).
  6. El diagrama: «Elev.»/«Elevator» → «Lift»; el nombre medido; la cifra fuera de la banda fina.
  7. El signo de los cortes junto a la tabla; el aviso del plano FIJO; cifras ACTIVAS.
"""
import ast
import io
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
import pandas as pd                                               # noqa: E402

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
from core import rail_cut_ui, tool_save_ui
_SVG = st.session_state.setdefault("_SVG", [])
incrustar.dibujo = lambda html, *a, **k: _SVG.append(html)
_LL = st.session_state.setdefault("_LL", [])
incrustar.script = lambda html, *a, **k: _LL.append(html)
_PRJ = {"ID": "PRJ-1", "Name": "Lift A", "Type": "Installation", "Status": "In progress", "Group": "cliente1"}
plan_ui.selector_proyecto = lambda key, ayuda="": (_PRJ, st.session_state.get("_PLANO", {}))
P.list_projects = lambda *a, **k: [_PRJ]
toolruns.is_configured = lambda: True
def _reg(**k):
    st.session_state.setdefault("_REG", []).append(k)
    return {"ok": True, "id": "CAL-9", "drive_id": "x"}
toolruns.registrar = _reg
flash.mostrar()
rail_cut_ui.render_rail_cut_tab()
'''


def _btn(a, k):
    return next((b for b in a.button if b.key == k), None)


def _todo(a):
    return " | ".join(str(x.value) for k in ("markdown", "caption", "info", "warning", "error",
                                              "success") for x in getattr(a, k, []))


print("1. Caso 1: el aviso del plano, la validación y el cálculo")
at = AppTest.from_string(G, default_timeout=300)
at.session_state["_PLANO"] = {"lfkk": 1150, "lfgk": 980}
at.run()
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
_c = " | ".join(str(c.value) for c in at.caption)
chk("el aviso del plano, FIJO (salía «taken from the project drawing» una pasada)",
    "LFKK and LFGK come from the project's drawing data." in _c)
at.number_input(key="rc_n").set_value(2).run()
chk("…y sigue tras tocar otro campo",
    "LFKK and LFGK come from the project's drawing data." in " | ".join(str(c.value) for c in at.caption))
_btn(at, "rc_calc1").click()
at.run()
_w = " ".join(str(x.value) for x in at.warning)
chk("⚠️ con A = 0 y L = 0 NO calcula y dice qué falta (antes «A 0 mm» y PDF)",
    "Fill in before calculating" in _w and "A = 0" in _w and "L for lift 1, 2" in _w
    and "rc_res" not in at.session_state and not list(at.get("download_button")), _w[:300])
at.number_input(key="rc_n2500").set_value(2).run()
at.number_input(key="rc_n5000").set_value(3).run()
at.session_state["rc_L_df"] = pd.DataFrame({"Elevador": ["Lift 1", "Lift 2"],
                                            "L (mm)": [19500.0, 18200.0]})
at.run()
_btn(at, "rc_calc1").click()
at.run()
_r = (at.session_state["rc_res"] if "rc_res" in at.session_state else {}).get("res") or {}
_cuts = [(round(x["CutRC"]), round(x["CutRCW"])) for x in _r.get("elevadores", [])]
chk("calcula los cortes de producción: CutRC +650/−650, CutRCW +480/−820",
    _cuts == [(650, 480), (-650, -820)], _cuts)
chk("el SIGNO, dicho junto a la tabla", "**Negative = trim**" in _todo(at)
    and "**positive = it falls short**" in _todo(at))
_k = sorted(b.key for b in at.button if str(b.key or "").startswith("cpxkpi_rc_"))
chk("las cifras son BOTONES (eran HTML)", _k == ["cpxkpi_rc_a", "cpxkpi_rc_lfgk", "cpxkpi_rc_lfkk",
                                                 "cpxkpi_rc_n"], _k)
_LL0 = len(at.session_state["_LL"])
_btn(at, "cpxkpi_rc_a").click()
at.run()
chk("…y tocar una lleva al diagrama (arriba del todo)",
    any(".st-key-cpx_rc_dibujo" in s and "block:'start'" in s for s in at.session_state["_LL"][_LL0:]))

print("\n2. ⚠️ Resultados viejos: aviso, cifras del cálculo y ni descargar ni guardar")
at.number_input(key="rc_lfkk").set_value(1200.0).run()
chk("cambiar LFKK lo DICE", "You changed data since the last calculation" in " ".join(
    str(x.value) for x in at.warning))
chk("⚠️ …y la cifra sigue diciendo el LFKK DEL CÁLCULO (1150), no el de ahora (1200)",
    "1150" in str(_btn(at, "cpxkpi_rc_lfkk").label) and "1200" not in str(_btn(at, "cpxkpi_rc_lfkk").label),
    str(_btn(at, "cpxkpi_rc_lfkk").label))
chk("…ni descarga ni guardar", not list(at.get("download_button")) and _btn(at, "save_rc1") is None)
at.number_input(key="rc_lfkk").set_value(1150.0).run()
chk("de vuelta a lo calculado, vuelve todo", _btn(at, "save_rc1") is not None)

print("\n3. Guardar: en inglés, con plural y nombre de archivo")
_btn(at, "save_rc1").click()
at.run()
_reg = at.session_state["_REG"] if "_REG" in at.session_state else []
# ⚠️ v597 · Al día con su razón (v385): los cortes del resumen llevan el decimal de la tabla (a
# entero, un 650.5 se guardaba «650» con «650.5» en pantalla). El principio —inglés— no cambia.
chk("⚠️ el resumen en inglés («Case 1 · A 20000 · Lift 1: 650.0/480.0, Lift 2: -650.0/-820.0»; decía «Caso 1 · E1:»)",
    bool(_reg) and _reg[-1].get("resumen") == "Case 1 · A 20000 · Lift 1: 650.0/480.0, Lift 2: -650.0/-820.0",
    _reg[-1].get("resumen") if _reg else "")
chk("…y el PDF «Rail_cutting_case1_Lift_A_<fecha>.pdf» (era «corte_rieles_caso1.pdf»)",
    bool(_reg) and str(_reg[-1].get("filename", "")).startswith("Rail_cutting_case1_Lift_A_"),
    _reg[-1].get("filename") if _reg else "")

print("\n4. ⚠️ Cambiar el nº de ascensores CONSERVA lo tecleado")
at.number_input(key="rc_n").set_value(3).run()
_df = at.session_state["rc_L_df"]
chk("Caso 1: de 2 a 3 ascensores, L = 19500, 18200, 0 (antes todo a 0)",
    [float(x) for x in _df["L (mm)"]] == [19500.0, 18200.0, 0.0], list(_df["L (mm)"]))

print("\n5. Caso 2: constantes, validación, cálculo y resumen")
at.radio(key="rc_caso").set_value("Case 2 — last installed (the top one)").run()
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
at.session_state["rc_in_df"] = pd.DataFrame({"Riel": ["RZ", "RO", "RF", "RB"],
                                             "Elevador 1": [300.0, 310.0, 280.0, 290.0],
                                             "Elevador 2": [305.0, 300.0, 285.0, 295.0],
                                             "Elevador 3": [0.0, 0.0, 0.0, 0.0]})
at.run()
_btn(at, "rc_calc2").click()
at.run()
_w = " ".join(str(x.value) for x in at.warning)
chk("⚠️ un ascensor con RZ/RO/RF/RB en 0 NO se calcula (daba los LF a pelo)",
    "RZ, RO, RF and RB for lift 3" in _w and (at.session_state["rc_res"] if "rc_res" in at.session_state else None) is None,
    _w[:200])
at.number_input(key="rc_n").set_value(2).run()
chk("…y de 3 a 2 ascensores se quedan las columnas que había",
    list(at.session_state["rc_in_df"]["Elevador 1"]) == [300.0, 310.0, 280.0, 290.0])
_btn(at, "rc_calc2").click()
at.run()
_r2 = (at.session_state["rc_res"] if "rc_res" in at.session_state else {}) or {}
chk("Above the FFL: CutR = LF − R (850 · 840 · 700 · 690)",
    [round(_r2["res"][0][k]) for k in ("CutRZ", "CutRO", "CutRF", "CutRB")] == [850, 840, 700, 690]
    if _r2 else False)
at.radio(key="rc_sub").set_value("Below the FFL (add)").run()
chk("cambiar el sub-caso deja el resultado VIEJO y lo dice",
    "You changed data since the last calculation" in " ".join(str(x.value) for x in at.warning))
_btn(at, "rc_calc2").click()
at.run()
_r2 = at.session_state["rc_res"]
chk("Below the FFL: CutR = LF + R (1450 · 1460 · 1260 · 1270)",
    [round(_r2["res"][0][k]) for k in ("CutRZ", "CutRO", "CutRF", "CutRB")] == [1450, 1460, 1260, 1270])
_btn(at, "save_rc2").click()
at.run()
_reg = at.session_state["_REG"]
chk("⚠️ el resumen «Case 2 (below the FFL) · 2 lifts» (decía «(debajo) · 2 lift(s)»)",
    _reg[-1].get("resumen") == "Case 2 (below the FFL) · 2 lifts", _reg[-1].get("resumen"))

print("\n6. El diagrama")
from core.rail_cut import rail_cut_svg, compute_case1, compute_case2   # noqa: E402
import xml.etree.ElementTree as ET                                     # noqa: E402
# (la 1ª vuelta usó un nombre que CABÍA —530 px de dibujo con 2 ascensores—: el código hacía
# lo correcto y la sonda no obligaba a cortar. Ahora uno que no cabe, y se mide el resultado.)
_LARGO = ("Smith & Sons — Westfield Bondi Junction Shopping Centre — Car Park Goods Lift 14 "
          "East Tower Level B4 Loading Dock")
_s1 = rail_cut_svg(compute_case1(1150, 980, 2, 3, [19500, 18200]), caso=1, n2500=2, n5000=3,
                   proyecto=_LARGO)
_s2 = rail_cut_svg({"elevadores": compute_case2(1150, 980, [{"RZ": 300, "RO": 310, "RF": 280, "RB": 290}],
                                                "encima")}, caso=2, proyecto="Lift A")
_t1 = [x.text or "" for x in ET.fromstring(_s1).iter("{http://www.w3.org/2000/svg}text")]
_t2 = [x.text or "" for x in ET.fromstring(_s2).iter("{http://www.w3.org/2000/svg}text")]
chk("⚠️ «Lift 1» / «Lift 2» (decía «Elev.» y «Elevator»)",
    "Lift 1" in _t1 and "Lift 2" in _t1 and "Lift 1" in _t2
    and not [x for x in _t1 + _t2 if "Elev" in x])
_nom = [x for x in _t1 if x.startswith("Smith")]
from core import texto_svg as TS                                        # noqa: E402
_vw = float(re.search(r'viewBox="0 0 (\d+)', _s1).group(1))
_libre = _vw - 36 - TS.ancho("RAIL CUTTING", 11, True) - 16
chk("el nombre MEDIDO: cortado con «…», escapado y sin pisar el título",
    bool(_nom) and _nom[0].endswith("…") and "&" in _nom[0]
    and TS.ancho(_nom[0], 9, True) <= _libre, (_nom, _libre))
_rt = ET.fromstring(_s1)
_bandas = [float(r.get("y")) for r in _rt.iter("{http://www.w3.org/2000/svg}rect")
           if r.get("fill") in ("#fcebeb", "#e8f5e9") and float(r.get("height", 0)) < 12
           and float(r.get("width", 0)) == 36]
# (v597 · la cifra lleva ahora un decimal: «650.0»)
_cif = [float(x.get("y")) for x in _rt.iter("{http://www.w3.org/2000/svg}text") if (x.text or "") == "650.0"]
chk("la cifra de una banda fina va ENCIMA (se montaba sobre el suelo)",
    bool(_bandas) and bool(_cif) and min(_cif) < min(_bandas), (_bandas, _cif))

print("\n7. ⚠️ La plomada también conserva los BSR")
GP = r'''
import streamlit as st
import pandas as pd
st.session_state.setdefault("auth", {"usuario": "Admin2", "rol": "administrator", "grupo": "cliente1"})
from core import plan_ui, plumb_ui
plan_ui.selector_proyecto = lambda key, ayuda="": (None, {})
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    st.session_state["plb_n"] = 3
    st.session_state["plb_bsr_df"] = pd.DataFrame({"Elevador": ["Lift 1", "Lift 2", "Lift 3"],
                                                   "BSR (mm)": [1985.0, 2010.0, 1900.0]})
plumb_ui.render_plumb_tab()
'''
ap = AppTest.from_string(GP, default_timeout=120).run()
ap.number_input(key="plb_n").set_value(4).run()
chk("de 3 a 4 ascensores, BSR = 1985, 2010, 1900, 0 (antes todo a 0)",
    [float(x) for x in ap.session_state["plb_bsr_df"]["BSR (mm)"]] == [1985.0, 2010.0, 1900.0, 0.0],
    list(ap.session_state["plb_bsr_df"]["BSR (mm)"]))

print("\n8. Estático")
_cads = [n.value for n in ast.walk(ast.parse(io.open(os.path.join(RAIZ, "core", "rail_cut_ui.py"),
                                                     encoding="utf-8").read()))
         if isinstance(n, ast.Constant) and isinstance(n.value, str)]
_src = io.open(os.path.join(RAIZ, "core", "rail_cut_ui.py"), encoding="utf-8").read()
# (por el AST: la 1ª vuelta casó «startswith("Above")» en MI comentario — trampa 2)
_sw = [ast.unparse(n) for n in ast.walk(ast.parse(_src)) if isinstance(n, ast.Call)
       and getattr(n.func, "attr", "") == "startswith"]
chk("⚠️ el Caso 2 decide por constantes (ningún `startswith` sobre el texto, la trampa de v441)",
    "sub == _S1" in _src and not _sw, _sw)
chk("nada de «Caso», «E1», «corte_rieles» en las cadenas",
    not [c for c in _cads if c.startswith(("Caso ", "corte_rieles")) or re.search(r"\bE\{i", c)])

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
sys.exit(1 if fallos else 0)
