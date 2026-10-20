"""v597 · UN DECIMAL EN LAS CUATRO HERRAMIENTAS (decisión del usuario: «Si dale», tras «No hay nada
pendiente??»).

Visto auditando v596 (21/10/2026):
  1. ⚠️ Rails: el resumen GUARDADO redondeaba a entero — con L 19500.5 la tabla daba 650.5 y lo
     guardado «650» (redondeo al par): la instrucción guardada y la de la pantalla, distintas.
  2. El fallo de v596 en las demás columnas: Belting HGPR «120»/«70.5» (producción), Buffers
     «20»/«7.5» con «Buffer 1: 20.0» guardado (producción, CAL-0007), Rails y los dibujos de la
     plomada sin el «.0» → `tabla.mm1` y un decimal en tabla, diagrama, resumen y PDF; las cotas
     del plano (HQ, HGP, HKP, LFKK, LFGK, A, el chequeo de BS) enteras.
  3. Rails: «Found in the PDF: none.» en VERDE (producción) → aviso; y si falta una, cuál.
  Y visto al hacerlo: ⚠️ el PDF de la plomada imprimía «Línea · X inicial (mm) · X final (mm) ·
  Desplazada» (las CLAVES de `plumb_table`, que son dato) → `plumb_table_doc`. Y con 5 buffers la
  cifra del último pisaba «HKP design 520» (verif_v533) → el dibujo reserva el ancho del rótulo.
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
import pandas as pd                                               # noqa: E402

fallos, n_ok = [], 0
SVGNS = "{http://www.w3.org/2000/svg}"


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


def _btn(a, k):
    return next((b for b in a.button if b.key == k), None)


def _ss(a, k, defecto=None):
    return a.session_state[k] if k in a.session_state else defecto


def _cols(a):
    """La configuración de columnas de cada tabla pintada (lo que viaja al navegador)."""
    return [json.loads(x.proto.columns or "{}") for x in a.dataframe]


def _mm1(cfg, clave, etiqueta):
    c = cfg.get(clave) or {}
    tc = c.get("type_config") or {}
    return c.get("label") == etiqueta and tc.get("type") == "number" and tc.get("format") == "%.1f"


def _textos(svg):
    i = svg.find("<svg")
    if i < 0:
        return []
    try:
        return [x.text or "" for x in ET.fromstring(svg[i:svg.rfind("</svg>") + 6]).iter(SVGNS + "text")]
    except ET.ParseError as e:
        return ["<SVG inválido: %s>" % e]


CAB = r'''
import streamlit as st
import importlib
st.session_state.setdefault("auth", {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"})
from core import plan_ui, plan_store, flash, incrustar, toolruns, projects as P
plan_ui = importlib.reload(plan_ui)
from core import rail_cut_ui, buffer_cut_ui, belting_ui, tool_save_ui
_SVG = st.session_state.setdefault("_SVG", [])
incrustar.dibujo = lambda html, *a, **k: _SVG.append(html)
incrustar.script = lambda html, *a, **k: None
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
rail_cut_ui.extract_lf = lambda f: st.session_state.get("_EX", {})
def _pdf(titulo, **k):
    st.session_state.setdefault("_PDFT", []).append((titulo, k))
    return b"%PDF-1.4 prueba"
for _m in (rail_cut_ui, buffer_cut_ui, belting_ui):
    _m.tool_pdf = _pdf
flash.mostrar()
'''
GR = CAB + "rail_cut_ui.render_rail_cut_tab()\n"
GB = CAB + "buffer_cut_ui.render_buffer_cut_tab()\n"
GT = CAB + "belting_ui.render_belting_tab()\n"

print("1. ⚠️ Rails, Caso 1 con un decimal en la medida (el caso del resumen distinto de la tabla)")
at = AppTest.from_string(GR, default_timeout=300)
at.session_state["_PLANO"] = {"lfkk": 1150, "lfgk": 980}
at.run()
at.number_input(key="rc_n").set_value(2).run()
at.number_input(key="rc_n2500").set_value(2).run()
at.number_input(key="rc_n5000").set_value(3).run()
at.session_state["rc_L_df"] = pd.DataFrame({"Elevador": ["Lift 1", "Lift 2"], "L (mm)": [19500.5, 18200.0]})
at.run()
_btn(at, "rc_calc1").click()
at.run()
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
_res = (_ss(at, "rc_res", {}) or {}).get("res", {})
chk("(el caso: CutRC 650.5 y -650, CutRCW 480.5 y -820)",
    [round(e["CutRC"], 1) for e in _res.get("elevadores", [])] == [650.5, -650.0], _res)
_cc = [c for c in _cols(at) if "Lift 1" in c and "Lift 2" in c]
chk("⚠️ las tablas de cortes («Result» y «Detail») con UN decimal y su etiqueta",
    len(_cc) >= 2 and all(_mm1(c, "Lift 1", "Lift 1") and _mm1(c, "Lift 2", "Lift 2") for c in _cc), _cc)
_t = _textos((_ss(at, "_SVG", [""]) or [""])[-1])
chk("el diagrama: «650.5», «-650.0», «L 19500.5» y «L 18200.0» (decía «-650» y «L 18200»)",
    {"650.5", "-650.0", "L 19500.5", "L 18200.0"} <= set(_t), _t)
chk("…y A, la pila instalada (cota entera), sigue «A 20000»", "A 20000" in _t, _t)
_btn(at, "save_rc1").click()
at.run()
_reg = _ss(at, "_REG", [])
chk("⚠️ el resumen guardado con el decimal de la tabla («650.5/480.5», antes «650/480»)",
    bool(_reg) and _reg[-1].get("resumen") == "Case 1 · A 20000 · Lift 1: 650.5/480.5, Lift 2: -650.0/-820.0",
    _reg[-1].get("resumen") if _reg else "")

print("\n2. Rails, Caso 2")
at.radio(key="rc_caso").set_value("Case 2 — last installed (the top one)").run()
at.session_state["rc_in_df"] = pd.DataFrame({"Riel": ["RZ", "RO", "RF", "RB"],
                                             "Elevador 1": [100.0, 120.5, 90.0, 95.0],
                                             "Elevador 2": [110.0, 100.0, 80.0, 85.0]})
at.run()
_btn(at, "rc_calc2").click()
at.run()
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
_cc = [c for c in _cols(at) if "Lift 1" in c and "Lift 2" in c]
chk("la tabla de cortes del Caso 2 con UN decimal", bool(_cc) and _mm1(_cc[-1], "Lift 1", "Lift 1"), _cc)
_t = _textos((_ss(at, "_SVG", [""]) or [""])[-1])
chk("…y su diagrama («1050.0», «1029.5»: LFKK − R con el subcaso de arriba)",
    {"1050.0", "1029.5"} <= set(_t), [x for x in _t if re.fullmatch(r"-?\d+(\.\d+)?", x)])

print("\n3. ⚠️ Rails: lo que NO se encuentra en el PDF es un AVISO (salía en verde)")
for ex, quiere_aviso, texto in (({}, True, "LFKK and LFGK were not found in the drawing"),
                                ({"LFKK": 1150.0}, True, "LFGK was not found: enter it by hand"),
                                ({"LFKK": 1150.0, "LFGK": 980.0}, False,
                                 "From the drawing: **LFKK=1150, LFGK=980 mm**")):
    ap = AppTest.from_string(GR, default_timeout=300)
    ap.session_state["_PLANO"] = {}
    ap.session_state["_PDF"] = "plano.pdf"
    ap.session_state["_EX"] = ex
    ap.run()
    _w = " ".join(str(x.value) for x in ap.warning)
    _s = " ".join(str(x.value) for x in ap.success)
    if quiere_aviso:
        chk("%s → AVISO amarillo («%s…»), nada en verde" % (sorted(ex) or "nada", texto[:30]),
            texto in _w and "Found in the PDF" not in _s and not _s, (_w[:160], _s[:160]))
    else:
        chk("las dos → éxito con sus valores («%s»)" % texto, texto in _s and not ap.exception, _s[:160])

print("\n4. Buffers: tabla, diagrama y resumen con UN decimal")
ab = AppTest.from_string(GB, default_timeout=300)
ab.session_state["_PLANO"] = {"hkp": 520}
ab.run()
ab.number_input(key="bc_n").set_value(2).run()
ab.session_state["bc_df"] = pd.DataFrame({"Buffer": ["Buffer 1", "Buffer 2"], "HKPR (mm)": [500.0, 512.5]})
ab.run()
_btn(ab, "bc_calc").click()
ab.run()
chk("sin excepción", not ab.exception, [e.value for e in ab.exception][:1])
_cc = [c for c in _cols(ab) if "Cut (mm)" in c]
chk("⚠️ «HKPR (mm)» y «Cut (mm)» con UN decimal y su etiqueta (salía «20» y «7.5»)",
    bool(_cc) and _mm1(_cc[-1], "HKPR (mm)", "HKPR (mm)") and _mm1(_cc[-1], "Cut (mm)", "Cut (mm)"), _cc)
_t = _textos((_ss(ab, "_SVG", [""]) or [""])[-1])
chk("el diagrama: «cut 20.0», «cut 7.5», «HKPR 500.0» (decía «cut 20», «HKPR 500»)",
    {"cut 20.0", "cut 7.5", "HKPR 500.0", "HKPR 512.5"} <= set(_t), _t)
chk("…y HKP, cota del plano, entera («HKP design 520»)", "HKP design 520" in _t, _t)
_btn(ab, "save_bc").click()
ab.run()
_reg = _ss(ab, "_REG", [])
chk("…el resumen, igual que la tabla («Buffer 1: 20.0, Buffer 2: 7.5»)",
    bool(_reg) and _reg[-1].get("resumen") == "HKP 520 · Buffer 1: 20.0, Buffer 2: 7.5",
    _reg[-1].get("resumen") if _reg else "")

print("\n5. ⚠️ Buffers con 5: el rótulo «HKP design» no lo pisa ningún buffer")
from core.buffer_cut import buffer_cut_svg, compute_buffer_cut     # noqa: E402
from core import texto_svg as TS                                   # noqa: E402
_ok5 = []
for n in range(1, 7):
    _s = buffer_cut_svg(compute_buffer_cut(120, [110.0 + i * 0.5 for i in range(n)]))
    _r = ET.fromstring(_s)
    _vw = float(re.search(r'viewBox="0 0 (\d+)', _s).group(1))
    _lab = [x for x in _r.iter(SVGNS + "text") if (x.text or "").startswith("HKP design")]
    _cuerpos = [float(x.get("x")) + float(x.get("width")) for x in _r.iter(SVGNS + "rect")
                if x.get("height") == "58"]
    if _lab and _cuerpos:
        _ini = float(_lab[0].get("x")) - TS.ancho(_lab[0].text, 8.5, True)
        _ok5.append((n, _ini > max(_cuerpos), round(_ini - max(_cuerpos), 1)))
chk("de 1 a 6 buffers, el rótulo empieza DESPUÉS del último buffer (con 5, la cifra lo pisaba)",
    len(_ok5) == 6 and all(x[1] for x in _ok5), _ok5)

print("\n6. Belting: el HGPR con UN decimal (salía «120» y «70.5» en la misma columna)")
ag = AppTest.from_string(GT, default_timeout=300)
ag.session_state["_PLANO"] = {"hq": 14000, "hgp": 85}
ag.run()
ag.number_input(key="belt_ns").set_value(2).run()
ag.number_input(key="belt_hgpr_0").set_value(120.0).run()
ag.number_input(key="belt_hgpr_1").set_value(70.5).run()
_btn(ag, "belt_calc").click()
ag.run()
chk("sin excepción", not ag.exception, [e.value for e in ag.exception][:1])
_cc = [c for c in _cols(ag) if "HGPR (mm)" in c]
chk("«HGPR (mm)» y «DSTS (mm)» con UN decimal y su etiqueta",
    bool(_cc) and _mm1(_cc[-1], "HGPR (mm)", "HGPR (mm)") and _mm1(_cc[-1], "DSTS (mm)", "DSTS (mm)"), _cc)
_t = _textos((_ss(ag, "_SVG", [""]) or [""])[-1])
chk("el diagrama: «HGPR 120.0» y «HGPR 70.5» (decía «HGPR 120»)",
    any(x.endswith("HGPR 120.0") for x in _t) and any(x.endswith("HGPR 70.5") for x in _t), _t)
_pt = (_ss(ag, "_PDFT", []) or [("", {})])[-1]
_fil = (_pt[1].get("tablas") or [("", [])])[0][1]
chk("…y la tabla del PDF («120.0», «70.5»)", [str(f.get("HGPR (mm)")) for f in _fil] == ["120.0", "70.5"], _fil)
# Un HGPR con dos decimales: el PDF imprime `str()` del valor, así que sin redondear saldría
# «120.25» con «120.2» en la tabla (trampa 1: con 120 y 70.5 eso no se ve)
ag.number_input(key="belt_hgpr_0").set_value(120.25).run()
_btn(ag, "belt_calc").click()
ag.run()
_pt = (_ss(ag, "_PDFT", []) or [("", {})])[-1]
_fil = (_pt[1].get("tablas") or [("", [])])[0][1]
_v = list(ag.dataframe[-1].value["HGPR (mm)"]) if list(ag.dataframe) else []
chk("…con dos decimales tecleados, el PDF dice lo mismo que la tabla (al décimo)",
    bool(_fil) and str(_fil[0].get("HGPR (mm)")) == str(_v[0]) and len(str(_v[0]).split(".")[-1]) == 1,
    (_fil[:1], _v))

print("\n7. Plumb: los dibujos con UN decimal y ⚠️ el PDF con cabeceras en inglés")
from core import plumb as PL                                       # noqa: E402
from core.tool_pdf import tool_pdf                                 # noqa: E402
from pypdf import PdfReader                                        # noqa: E402
_r = PL.compute_plumb({"BKS": 1600, "RAIL": 62, "TKSW": 965, "LengthTemplate": 300, "SF1": 51, "SF2": 51,
                       "BSR": 1985, "BS": 1998, "SG": 300, "TG": 60, "OMEGA_SIDE": "R"})
_tx = re.findall(r">([^<>]{2,})<", PL.plumb_svg(_r))
chk("el dibujo: «DBP 1662.0», «LT 300.0» y la comprobación «69.0 + 1662.0 + 82.0» (decía «DBP 1662»)",
    {"DBP 1662.0", "LT 300.0", "69.0 + 1662.0 + 82.0"} <= set(_tx), _tx)
chk("…y el chequeo de BS, cotas del PLANO, entero («components 1826», «diff 172 mm — check»)",
    {"components 1826", "diff 172 mm — check"} <= set(_tx), _tx)
_card = re.findall(r">([^<>]+)<", PL.plumb_card_svg(_r))
# (trampa 1: que la tarjeta TENGA medidas — si no, «ninguna sin decimal» pasa en vacío)
chk("la tarjeta de obra, igual (tiene medidas, y ninguna sin su decimal)",
    sum(1 for x in _card if re.fullmatch(r"-?\d+\.\d", x.strip())) >= 3
    and not [x for x in _card if re.fullmatch(r"-?\d{2,}", x.strip())],
    [x for x in _card if re.search(r"\d", x)])
# Con BSR 1985.25 las posiciones crudas llevan DOS decimales en las DOS columnas (si no, un
# `round(…, 2)` pasaría igual — trampa 1). ⚠️ La 1ª tanda de romper_v597 dejó escapar «X final
# a dos decimales» con razón: con BSR 1985.5 solo «X inicial» tenía .75 (las finales, .5).
_r2 = PL.compute_plumb({"BKS": 1600, "RAIL": 62, "TKSW": 965, "LengthTemplate": 300, "SF1": 51,
                        "SF2": 51, "BSR": 1985.25, "BS": 1998, "SG": 300, "TG": 60, "OMEGA_SIDE": "R"})
_dos = {c: any(round(v[c], 1) != round(v[c], 2) for v in _r2["lines"].values()) for c in ("x0", "x")}
_fil = PL.plumb_table(_r2)
chk("`plumb_table` a UN decimal (iba a dos) y con sus claves de siempre (dato, las leen los informes)",
    _dos == {"x0": True, "x": True}
    and all(round(f[k], 1) == f[k] for f in _fil for k in ("X inicial (mm)", "X final (mm)"))
    and set(_fil[0]) == {"Línea", "X inicial (mm)", "X final (mm)", "Desplazada"}, (_dos, _fil[:2]))
_doc = PL.plumb_table_doc(_r)
chk("`plumb_table_doc`: las cabeceras del documento («Line · X start (mm) · X end (mm) · Shifted»)",
    bool(_doc) and list(_doc[0]) == ["Line", "X start (mm)", "X end (mm)", "Shifted"], _doc[:1])
_txt = "\n".join(p.extract_text() for p in PdfReader(io.BytesIO(
    tool_pdf("Plumb setting-out", meta={"Project": "x"}, tablas=[("Template — line positions", _doc)]))).pages)
chk("⚠️ en el PDF de verdad: «Line», «X start (mm)»… y ni rastro de «Línea» / «X inicial» / «Desplazada»",
    all(w in _txt for w in ("Line", "X start (mm)", "X end (mm)", "Shifted"))
    and not any(w in _txt for w in ("Línea", "X inicial", "X final", "Desplazada")), _txt[:300])
_arb = ast.parse(fuente("core/plumb_ui.py"))
_tp = [c for c in ast.walk(_arb) if isinstance(c, ast.Call) and getattr(c.func, "id", "") == "tool_pdf"]
_usa = {getattr(n.func, "id", "") for c in _tp for n in ast.walk(c) if isinstance(n, ast.Call)}
chk("…y el PDF de la herramienta usa `plumb_table_doc` (no `plumb_table`)",
    len(_tp) == 1 and "plumb_table_doc" in _usa and "plumb_table" not in _usa, _usa)

print("\n8. El Survey: sus tablas de plomada con UN decimal, como sus dibujos")
_arb = ast.parse(fuente("core/survey_ui.py"))
_df = {}
for c in ast.walk(_arb):
    if isinstance(c, ast.Call) and getattr(c.func, "attr", "") == "dataframe" and c.args:
        _f = {getattr(n.func, "id", "") for n in ast.walk(c.args[0]) if isinstance(n, ast.Call)}
        for nom in ("plumb_table", "plumb_checks"):
            if nom in _f:
                _cc = [k for k in c.keywords if k.arg == "column_config"]
                _df[nom] = {kk.value: getattr(vv.func, "attr", "")
                            for x in _cc for n in ast.walk(x.value) if isinstance(n, ast.Dict)
                            for kk, vv in zip(n.keys, n.values)
                            if isinstance(kk, ast.Constant) and isinstance(vv, ast.Call)}
chk("«X inicial (mm)» y «X final (mm)» con `tabla.mm1`; «Distancia (mm)» también",
    _df.get("plumb_table", {}).get("X inicial (mm)") == "mm1"
    and _df.get("plumb_table", {}).get("X final (mm)") == "mm1"
    and _df.get("plumb_checks", {}).get("Distancia (mm)") == "mm1", _df)

print("\n9. El helper y la documentación")
from core import tabla                                             # noqa: E402
_m = tabla.mm1("HKPR (mm)")
chk("`tabla.mm1`: número, «%.1f» y CON etiqueta (la regla de v579)",
    _m.get("label") == "HKPR (mm)" and (_m.get("type_config") or {}).get("format") == "%.1f"
    and (_m.get("type_config") or {}).get("type") == "number", _m)
_cl = io.open(os.path.join(RAIZ, "..", "CLAUDE.md"), encoding="utf-8").read()
chk("CLAUDE.md ya no dice que el buscador está «aún sin backend» (busca desde v330)",
    "aún sin backend" not in _cl and "busca de verdad desde v330" in _cl)

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
sys.exit(1 if fallos else 0)
