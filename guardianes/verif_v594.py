"""v594 · TOOLS → BUFFERS, PROBADA (decisión del usuario: «Ok dale»; «no dejes nada pendiente»).

Visto en producción (20/10/2026, Bondi L1, HKP 520 del plano):
  1. ⚠️ Tres buffers SIN MEDIR (HKPR 0) → «Cut 520 mm · OK» en los tres, «To check 0» y el PDF:
     la orden de cortar el HKP entero sin haber medido → sin medir no se calcula.
  2. ⚠️ Resultados viejos sin aviso → aviso, ni descargar ni guardar.
  3. ⚠️ Cambiar el nº de buffers BORRABA los HKPR → se conservan.
  4. El aviso del plano de UNA pasada → fijo; «corte_buffers.pdf», «B1:» → inglés con obra y
     fecha; el nombre sin medir en el diagrama; cifras pasivas → activas.
  Y lo que quedaba (v593): la plomada calculaba con un BSR en 0 → se dice qué falta.
"""
import io
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
from core import buffer_cut_ui, tool_save_ui
_SVG = st.session_state.setdefault("_SVG", [])
_LL = st.session_state.setdefault("_LL", [])
incrustar.dibujo = lambda html, *a, **k: _SVG.append(html)
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
buffer_cut_ui.render_buffer_cut_tab()
'''


def _btn(a, k):
    return next((b for b in a.button if b.key == k), None)


print("1. ⚠️ Sin medir NO se calcula (el caso de producción: tres buffers en 0)")
at = AppTest.from_string(G, default_timeout=300)
at.session_state["_PLANO"] = {"hkp": 520}
at.run()
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
_c = " | ".join(str(c.value) for c in at.caption)
chk("el aviso del plano, FIJO («HKP comes from the project's drawing data.»)",
    "HKP comes from the project's drawing data." in _c)
at.number_input(key="bc_n").set_value(3).run()
chk("…y sigue tras cambiar el nº de buffers (en producción se iba)",
    "HKP comes from the project's drawing data." in " | ".join(str(c.value) for c in at.caption))
_btn(at, "bc_calc").click()
at.run()
_w = " ".join(str(x.value) for x in at.warning)
chk("⚠️ tres HKPR en 0: NO calcula y dice cuáles (salía «Cut 520 mm · OK» en los tres)",
    "Fill in before calculating" in _w and "the HKPR measured on buffer 1, 2, 3" in _w
    and "bc_res" not in at.session_state and not list(at.get("download_button")), _w[:200])

print("\n2. Medidos: el cálculo, las cifras y los avisos")
at.session_state["bc_df"] = pd.DataFrame({"Buffer": ["Buffer 1", "Buffer 2", "Buffer 3"],
                                          "HKPR (mm)": [500.0, 530.0, 515.0]})
at.run()
# (la 1ª tanda de romper_v594 dejó escapar «sin HKP vuelve a calcular»: el guion tenía siempre
# HKP 520. Y con plano en la obra, un HKP en 0 lo vuelve a rellenar `plan_ui.aplicar` —bien
# hecho—: el caso real es SIN plano, en su propia sesión.)
at0 = AppTest.from_string(G, default_timeout=300)
at0.session_state["_PLANO"] = {}
at0.session_state["bc_df"] = pd.DataFrame({"Buffer": ["Buffer 1"], "HKPR (mm)": [500.0]})
at0.run()
_btn(at0, "bc_calc").click()
at0.run()
_w = " ".join(str(x.value) for x in at0.warning)
chk("⚠️ sin plano y sin HKP (el buffer medido) tampoco calcula",
    "HKP (from the drawing, or by hand)" in _w and "bc_res" not in at0.session_state, _w[:200])
_btn(at, "bc_calc").click()
at.run()
_r = at.session_state["bc_res"] if "bc_res" in at.session_state else {}
chk("Cut = HKP − HKPR: 20 · −10 (a revisar) · 5",
    [b["CutBuffer"] for b in _r.get("buffers", [])] == [20.0, -10.0, 5.0]
    and [b["warn"] for b in _r.get("buffers", [])] == [False, True, False], _r.get("buffers"))
_k = sorted(b.key for b in at.button if str(b.key or "").startswith("cpxkpi_bc_"))
chk("las cifras son BOTONES (eran HTML)", _k == ["cpxkpi_bc_hkp", "cpxkpi_bc_n", "cpxkpi_bc_rev"], _k)
chk("…«To check 1»", "1" in str(_btn(at, "cpxkpi_bc_rev").label))
_LL0 = len(at.session_state["_LL"])
_btn(at, "cpxkpi_bc_rev").click()
at.run()
chk("«To check» lleva a la TABLA", any(".st-key-cpx_bc_tabla" in s for s in at.session_state["_LL"][_LL0:]))
_LL0 = len(at.session_state["_LL"])
_btn(at, "cpxkpi_bc_hkp").click()
at.run()
chk("…y HKP, al diagrama", any(".st-key-cpx_bc_dibujo" in s for s in at.session_state["_LL"][_LL0:]))

print("\n3. ⚠️ Resultados viejos")
at.number_input(key="bc_hkp").set_value(525.0).run()
chk("cambiar HKP lo DICE", "You changed data since the last calculation" in " ".join(
    str(x.value) for x in at.warning))
chk("…y ni descarga ni guardar", not list(at.get("download_button")) and _btn(at, "save_bc") is None)
at.number_input(key="bc_hkp").set_value(520.0).run()
chk("de vuelta a lo calculado, vuelve todo", _btn(at, "save_bc") is not None)

print("\n4. Guardar: en inglés y con nombre de archivo")
_btn(at, "save_bc").click()
at.run()
_reg = at.session_state["_REG"] if "_REG" in at.session_state else []
chk("⚠️ el resumen «HKP 520 · Buffer 1: 20.0, Buffer 2: -10.0, Buffer 3: 5.0» (decía «B1: 20.0»)",
    bool(_reg) and _reg[-1].get("resumen") == "HKP 520 · Buffer 1: 20.0, Buffer 2: -10.0, Buffer 3: 5.0",
    _reg[-1].get("resumen") if _reg else "")
chk("…el PDF «Buffer_cutting_Lift_A_<fecha>.pdf» (era «corte_buffers.pdf»)",
    bool(_reg) and str(_reg[-1].get("filename", "")).startswith("Buffer_cutting_Lift_A_"),
    _reg[-1].get("filename") if _reg else "")
chk("…y lo guardado sin la huella interna del cálculo",
    bool(_reg) and "firma" not in (_reg[-1].get("datos") or {}).get("resultados", {}))

print("\n5. ⚠️ Cambiar el nº de buffers CONSERVA lo medido")
at.number_input(key="bc_n").set_value(4).run()
chk("de 3 a 4: 500, 530, 515, 0 (antes todo a 0)",
    [float(x) for x in at.session_state["bc_df"]["HKPR (mm)"]] == [500.0, 530.0, 515.0, 0.0],
    list(at.session_state["bc_df"]["HKPR (mm)"]))

print("\n6. El diagrama: el nombre medido y escapado")
from core.buffer_cut import buffer_cut_svg, compute_buffer_cut    # noqa: E402
from core import texto_svg as TS                                   # noqa: E402
_LARGO = ("Smith & Sons — Westfield Bondi Junction Shopping Centre — Car Park Goods Lift 14 "
          "East Tower Level B4")
_s = buffer_cut_svg(compute_buffer_cut(520, [500, 530]), proyecto=_LARGO)
_t = [x.text or "" for x in ET.fromstring(_s).iter("{http://www.w3.org/2000/svg}text")]
_nom = [x for x in _t if x.startswith("Smith")]
_vw = float(re.search(r'viewBox="0 0 (\d+)', _s).group(1))
chk("cortado con «…», escapado (el SVG es válido) y sin pisar el título",
    bool(_nom) and _nom[0].endswith("…")
    and TS.ancho(_nom[0], 9, True) <= _vw - 36 - TS.ancho("BUFFER CUTTING", 11, True) - 16, _nom)

print("\n7. ⚠️ La plomada: sin datos no calcula (con un BSR en 0 calculaba igual)")
GP = r'''
import streamlit as st
import pandas as pd
st.session_state.setdefault("auth", {"usuario": "Admin2", "rol": "administrator", "grupo": "cliente1"})
from core import plan_ui, plumb_ui
plan_ui.selector_proyecto = lambda key, ayuda="": (None, {})
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    for k, v in {"plb_bks": 1772, "plb_rail": 62, "plb_tksw": 965, "plb_lt": 300, "plb_sf1": 51,
                 "plb_sf2": 51, "plb_bs": 1998, "plb_sg": 300, "plb_tg": 60}.items():
        st.session_state[k] = float(v)
    st.session_state["plb_n"] = 2
    st.session_state["plb_bsr_df"] = pd.DataFrame({"Elevador": ["Lift 1", "Lift 2"],
                                                   "BSR (mm)": [1985.0, 0.0]})
plumb_ui.render_plumb_tab()
'''
ap = AppTest.from_string(GP, default_timeout=120).run()
_btn(ap, "plb_calc").click()
ap.run()
_w = " ".join(str(x.value) for x in ap.warning)
chk("un BSR en 0: NO calcula y dice cuál («the BSR measured on lift 2»)",
    "Fill in before calculating" in _w and "the BSR measured on lift 2" in _w
    and "plb_res_multi" not in ap.session_state, _w[:200])
ap.number_input(key="plb_lt").set_value(0.0).run()
_btn(ap, "plb_calc").click()
ap.run()
chk("…y sin LengthTemplate también lo dice",
    "LengthTemplate" in " ".join(str(x.value) for x in ap.warning))
ap.number_input(key="plb_lt").set_value(300.0).run()
ap.session_state["plb_bsr_df"] = pd.DataFrame({"Elevador": ["Lift 1", "Lift 2"],
                                               "BSR (mm)": [1985.0, 2010.0]})
ap.run()
_btn(ap, "plb_calc").click()
ap.run()
chk("con todo medido, calcula", "plb_res_multi" in ap.session_state and not ap.exception)

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
sys.exit(1 if fallos else 0)
