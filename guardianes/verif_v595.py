"""v595 · TOOLS → BELTING, PROBADA (decisión del usuario: «Dale con todo»). Con esto, Tools entera.

Visto en producción (20/10/2026, Bondi L1, HQ 14045 y HGP 85 del plano):
  1. ⚠️ Un ascensor SIN MEDIR (HGPR 0) → «DSTS -99 mm · above FFL» y el PDF: la orden de dejar la
     cabina 99 mm por ENCIMA del último piso sin haber medido → sin medir no se calcula.
  2. ⚠️ Resultados viejos: HGPR 130 en pantalla y el dibujo con el de 120, con descarga →
     aviso, ni descargar ni guardar.
  3. El aviso del plano de UNA pasada → fijo; los avisos del PDF antes de un `st.rerun()` → `flash`.
  4. «21 mm below from the top FFL» → «21.0 mm below the top FFL»; «Elevator» → «Lift» en el
     diagrama y el nombre medido; «HGPR lift 1» → «HGPR · Lift 1» por `t()`; la leyenda con el
     icono de los campos; «E1: DSTS 21.0» y «belting.pdf» → «Lift 1: DSTS 21.0» y
     «Belting_<obra>_<fecha>.pdf»; el PDF por `d()`; cifras pasivas → activas.
  Y de paso (las cuatro herramientas): la etiqueta del selector de plano por `t()`.
"""
import ast
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
    return io.open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8").read()


G = r'''
import streamlit as st
import importlib
st.session_state.setdefault("auth", {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"})
from core import plan_ui, plan_store, flash, incrustar, toolruns, projects as P
plan_ui = importlib.reload(plan_ui)
from core import belting_ui, tool_save_ui
import extractors.schindler as XS
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
class _Pdf:
    def __init__(self, n):
        self.name = n
plan_store.selector = lambda label, key, ayuda="": (_Pdf(st.session_state["_PDF"])
                                                    if st.session_state.get("_PDF") else None)
XS.extract_belting = lambda f: st.session_state.get("_EX", {})
_real_pdf = belting_ui.tool_pdf
def _pdf(titulo, **k):
    st.session_state["_PDFT"] = (titulo, k)
    return b"%PDF-1.4 prueba"
belting_ui.tool_pdf = _pdf
flash.mostrar()
belting_ui.render_belting_tab()
'''


def _btn(a, k):
    return next((b for b in a.button if b.key == k), None)


def _caps(a):
    return " | ".join(str(c.value) for c in a.caption)


def _ss(a, k, defecto=None):
    return a.session_state[k] if k in a.session_state else defecto


print("1. ⚠️ Sin medir NO se calcula (el caso de producción: HGPR en 0)")
at = AppTest.from_string(G, default_timeout=300)
at.session_state["_PLANO"] = {"hq": 14000, "hgp": 85}
at.run()
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("el aviso del plano, FIJO («HQ and HGP come from the project's drawing data.»)",
    "HQ and HGP come from the project's drawing data." in _caps(at))
at.number_input(key="belt_ns").set_value(2).run()
chk("…y sigue tras cambiar el nº de ascensores (en producción se iba)",
    "HQ and HGP come from the project's drawing data." in _caps(at))
_lab = [w.label for w in at.number_input if str(w.key or "").startswith("belt_hgpr_")]
chk("las casillas «HGPR · Lift 1» / «HGPR · Lift 2» (decían «HGPR lift 1»)",
    _lab == ["HGPR · Lift 1", "HGPR · Lift 2"], _lab)
_btn(at, "belt_calc").click()
at.run()
_w = " ".join(str(x.value) for x in at.warning)
chk("⚠️ dos HGPR en 0: NO calcula y dice cuáles (salía «DSTS -99 mm · above FFL»)",
    "Fill in before calculating" in _w and "the HGPR measured on lift 1, 2" in _w
    and "belt_res" not in at.session_state and not list(at.get("download_button")), _w[:200])
at.number_input(key="belt_hgpr_0").set_value(120.0).run()
_btn(at, "belt_calc").click()
at.run()
_w = " ".join(str(x.value) for x in at.warning)
chk("…con uno medido, dice el que falta («lift 2») y sigue sin calcular",
    "the HGPR measured on lift 2" in _w and "lift 1, 2" not in _w
    and "belt_res" not in at.session_state, _w[:200])
# sin plano y sin HQ/HGP (con plano, `plan_ui.aplicar` los rellena — bien hecho)
at0 = AppTest.from_string(G, default_timeout=300)
at0.session_state["_PLANO"] = {}
at0.run()
at0.number_input(key="belt_hgpr_0").set_value(120.0).run()
_btn(at0, "belt_calc").click()
at0.run()
_w = " ".join(str(x.value) for x in at0.warning)
chk("⚠️ sin plano, sin HQ ni HGP (el HGPR medido) tampoco calcula",
    "Fill in before calculating: HQ, HGP." in _w and "belt_res" not in at0.session_state, _w[:200])
chk("…y sin plano no dice que vienen del plano",
    "come from the project's drawing data" not in _caps(at0))

print("\n2. Medidos: el cálculo, la posición y las cifras")
at.number_input(key="belt_hgpr_1").set_value(70.0).run()
_btn(at, "belt_calc").click()
at.run()
_r = _ss(at, "belt_res", {})
chk("DSTS = HGPR − HGP − HQ/1000: 120 → 21.0 · 70 → -29.0",
    [x["dsts"] for x in _r.get("results", [])] == [21.0, -29.0], _r.get("results"))
_df = at.dataframe[0].value if list(at.dataframe) else None
_pos = list(_df["Position"]) if _df is not None and "Position" in _df else []
chk("⚠️ «21.0 mm below the top FFL» y «29.0 mm above the top FFL» (decía «21 mm below from the top FFL»)",
    _pos == ["21.0 mm below the top FFL", "29.0 mm above the top FFL"], _pos)
from core import belting_ui as BU                                  # noqa: E402
chk("…y en el FFL justo, «at the top FFL»", BU._posicion(0.0) == "at the top FFL", BU._posicion(0.0))
_k = sorted(b.key for b in at.button if str(b.key or "").startswith("cpxkpi_belt_"))
chk("las cifras son BOTONES (eran HTML)", _k == ["cpxkpi_belt_hgp", "cpxkpi_belt_hq", "cpxkpi_belt_n"], _k)
chk("…«HQ (travel)» con «14000 mm» y «Lifts» con «2»",
    "14000 mm" in str(_btn(at, "cpxkpi_belt_hq").label) and "2" in str(_btn(at, "cpxkpi_belt_n").label))
_LL0 = len(_ss(at, "_LL", []))
_btn(at, "cpxkpi_belt_hq").click()
at.run()
chk("una cifra lleva al DIAGRAMA", any(".st-key-cpx_belt_dibujo" in s for s in _ss(at, "_LL", [])[_LL0:]))
_LL0 = len(_ss(at, "_LL", []))
at.run()
chk("…una vez (otra pasada no vuelve a bajar)",
    not any(".st-key-cpx_belt_dibujo" in s for s in _ss(at, "_LL", [])[_LL0:]))

print("\n3. ⚠️ Resultados viejos")
at.number_input(key="belt_hgpr_0").set_value(130.0).run()
chk("cambiar un HGPR lo DICE (en producción, 130 en pantalla y el dibujo con el de 120)",
    "You changed data since the last calculation" in " ".join(str(x.value) for x in at.warning))
chk("…y ni descarga ni guardar", not list(at.get("download_button")) and _btn(at, "save_belt") is None)
at.number_input(key="belt_hgpr_0").set_value(120.0).run()
chk("de vuelta a lo calculado, vuelve todo",
    _btn(at, "save_belt") is not None and bool(list(at.get("download_button"))))

print("\n4. Guardar y el PDF: en inglés, por `d()` y con nombre de archivo")
_btn(at, "save_belt").click()
at.run()
_reg = _ss(at, "_REG", [])
chk("⚠️ el resumen «Lift 1: DSTS 21.0, Lift 2: DSTS -29.0» (decía «E1: DSTS 21.0»)",
    bool(_reg) and _reg[-1].get("resumen") == "Lift 1: DSTS 21.0, Lift 2: DSTS -29.0",
    _reg[-1].get("resumen") if _reg else "")
chk("…el PDF «Belting_Lift_A_<fecha>.pdf» (era «belting.pdf»)",
    bool(_reg) and re.fullmatch(r"Belting_Lift_A_\d{4}-\d{2}-\d{2}\.pdf",
                                str(_reg[-1].get("filename", ""))) is not None,
    _reg[-1].get("filename") if _reg else "")
chk("…y lo guardado sin la huella interna del cálculo",
    bool(_reg) and "firma" not in (_reg[-1].get("datos") or {}).get("resultados", {}))
_pt = _ss(at, "_PDFT", ("", {}))
chk("el PDF: título, cifras y notas en inglés",
    _pt[0] == "Belting — car position" and "HQ (travel)" in (_pt[1].get("meta") or {})
    and any("DSTS > 0 = lower the car" in n for n in (_pt[1].get("notas") or [])), _pt)

# Por `d()`: ningún literal de la llamada a `tool_pdf` (ni `titulo_pdf`) fuera de `d()`
_arb = ast.parse(fuente("core/belting_ui.py"))
_cads = [n.value for n in ast.walk(_arb) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def _sueltos(nodo):
    """Literales de `nodo` que NO están dentro de un `d(...)` ni son trozos de un f-string."""
    cubiertos = set()
    for n in ast.walk(nodo):
        if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "d" or isinstance(n, ast.JoinedStr):
            cubiertos |= {id(x) for x in ast.walk(n)}
    return [n.value for n in ast.walk(nodo) if isinstance(n, ast.Constant)
            and isinstance(n.value, str) and id(n) not in cubiertos and n.value not in ("—",)]


_tp = [c for c in ast.walk(_arb) if isinstance(c, ast.Call) and getattr(c.func, "id", "") == "tool_pdf"]
_rg = [c for c in ast.walk(_arb) if isinstance(c, ast.Call) and getattr(c.func, "id", "") == "render_guardar"]
_tit = [k.value for c in _rg for k in c.keywords if k.arg == "titulo_pdf"]
chk("el PDF entero por `d()` (título, cifras y notas iban sueltos)",
    len(_tp) == 1 and not _sueltos(_tp[0]), [_sueltos(c) for c in _tp])
chk("…y el nombre del PDF del botón (`titulo_pdf=d(\"belting\")`)",
    len(_tit) == 1 and isinstance(_tit[0], ast.Call) and getattr(_tit[0].func, "id", "") == "d")
_inf = [c for c in ast.walk(_arb) if isinstance(c, ast.Call) and getattr(c.func, "attr", "") == "info"]
chk("el aviso de reabrir, por `t()` (era un f-string)",
    len(_inf) == 1 and isinstance(_inf[0].args[0], ast.Call)
    and getattr(_inf[0].args[0].func, "id", "") == "t")
# (por las CADENAS del código — trampa 2: un comentario mío no puede pasar por el código)
chk("la leyenda con el icono de los campos (decía «✏️ = by hand»)",
    any(":material/edit: = by hand" in c for c in _cads) and not any("✏️" in c for c in _cads))

print("\n5. Los avisos del PDF del plano se VEN (iban antes de un `st.rerun()`)")
ap = AppTest.from_string(G, default_timeout=300)
ap.session_state["_PLANO"] = {}
ap.session_state["_PDF"] = "plano_bondi.pdf"
ap.session_state["_EX"] = {"HQ": 14045, "HGP": 85}
ap.run()
_s = " ".join(str(x.value) for x in ap.success)
chk("con HQ y HGP en el plano: «From the drawing: **HQ=14045, HGP=85 mm**…» A LA VISTA",
    "From the drawing: **HQ=14045, HGP=85 mm**" in _s and not ap.exception, _s[:200])
chk("…y los campos rellenos (14045 / 85)",
    ap.number_input(key="belt_hq").value == 14045.0 and ap.number_input(key="belt_hgp").value == 85.0)
ap2 = AppTest.from_string(G, default_timeout=300)
ap2.session_state["_PLANO"] = {}
ap2.session_state["_PDF"] = "plano_sin_datos.pdf"
ap2.session_state["_EX"] = {}
ap2.run()
_w = " ".join(str(x.value) for x in ap2.warning)
chk("sin datos en el plano: «HQ/HGP were not found in the drawing…» A LA VISTA",
    "HQ/HGP were not found in the drawing" in _w and not ap2.exception, _w[:200])

print("\n6. El diagrama: «Lift», el nombre medido y escapado")
from core.belting import belting_svg, compute_belting              # noqa: E402
from core import texto_svg as TS                                   # noqa: E402
_LARGO = ("Smith & Sons — Westfield Bondi Junction Shopping Centre — Car Park Goods Lift 14 "
          "East Tower Level B4 and the long service corridor")
_s = belting_svg(compute_belting(85, 14000, [120.0, 70.0]), proyecto=_LARGO)
try:
    _t = [x.text or "" for x in ET.fromstring(_s).iter("{http://www.w3.org/2000/svg}text")]
except ET.ParseError as e:
    _t = ["<SVG inválido: %s>" % e]
chk("⚠️ «Lift 1» / «Lift 2» (decía «Elevator 1/2»)",
    "Lift 1" in _t and "Lift 2" in _t and not any("Elevator" in x for x in _t), _t)
_nom = [x for x in _t if x.startswith("Smith")]
_vw = float(re.search(r'viewBox="0 0 (\d+)', _s).group(1))
chk("el nombre cortado con «…», escapado (el SVG es válido) y dentro del dibujo",
    bool(_nom) and _nom[0].endswith("…") and TS.ancho(_nom[0], 9, True) <= _vw - 36, _nom)
_c = belting_svg(compute_belting(85, 14000, [120.0]), proyecto="Bondi Junction Tower — Lift 1")
_tc = [x.text or "" for x in ET.fromstring(_c).iter("{http://www.w3.org/2000/svg}text")]
chk("…y uno que cabe, entero", "Bondi Junction Tower — Lift 1" in _tc, _tc)

print("\n7. De paso: la etiqueta del selector de plano por `t()` en las CUATRO herramientas")
_mal = []
for _f in ("plumb_ui", "rail_cut_ui", "buffer_cut_ui", "belting_ui"):
    _n = [c for c in ast.walk(ast.parse(fuente("core/%s.py" % _f))) if isinstance(c, ast.Call)
          and getattr(c.func, "attr", "") == "selector" and getattr(c.func.value, "id", "") == "plan_store"]
    if len(_n) != 1 or not (isinstance(_n[0].args[0], ast.Call) and getattr(_n[0].args[0].func, "id", "") == "t"):
        _mal.append(_f)
chk("las cuatro con `t(...)` (iban sin traducir)", not _mal, _mal)

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
sys.exit(1 if fallos else 0)
