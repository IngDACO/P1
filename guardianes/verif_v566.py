# -*- coding: utf-8 -*-
"""v566 · FINANCE → SUMMARY, PROBADA ACCIÓN POR ACCIÓN (decisión del usuario: «Dale con todo»).

  1. ⚠️ Lo PENDIENTE es un saldo a HOY (por cobrar, vencido, por pagar, sin tarifa,
     cargado sin jornada), no lo emitido en el periodo.
  2. ⚠️ Un periodo sin movimiento ya no deja la pantalla en blanco (+ «See All»).
  3. El periodo se recuerda (`persist_state`).
  4. Se compara con el MISMO tramo del periodo anterior, con el año en las fechas.
  5. «Charged with no workday» (decía «Hours with no payslip» y medía otra cosa) → Hours.
  6. «No margin»: «would be invoiced at cost» (decía «Invoiced at cost» de obras sin facturar).
  7. ⚠️ Negativos «-$128» (salía «$-128»), en `theme.dinero` para toda la app.
  8. Tarjetas ACTIVAS: Income → Invoices, What you pay → Breakdown, Profit → By project.
  9. ⚠️ Detalles ACTIVOS: cada obra sin facturar abre SU factura; cada persona sin tarifa,
     su ficha; cada obra sin margen o sobre presupuesto, sus Costs.
 10. By project: obra fijada, resultado y margen delante, cabeceras con etiqueta, fila → obra.
 11. «→ Go to Invoices» (decía «→ Ir a Facturas»), «Over budget», «1 person», «3 jobs».
 12. «vs previous» (decía «vs. periodo anterior»).   13-14. Textos con `t()`.
 15-17. Etiqueta arriba y cifra abajo; 2 por fila bajo 760 px (`@container`).
 19. De paso: las descripciones de Tools con `t()`.

AppTest con las fuentes de datos sustituidas: ninguna hoja se toca.
"""
import ast
import datetime as dt
import io
import os
import re
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
fallos, n_ok = [], 0


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("  ok   " + q)
    else:
        fallos.append(q)
        print("  FALLO " + q + (("  -> " + str(det)) if det != "" else ""))


def _textos(at):
    _t = []
    for coll in (at.markdown, at.caption, at.info, at.warning, at.success, at.error):
        _t += [str(x.value) for x in coll]
    _t += [str(b.label) for b in at.button]
    return " ¦ ".join(_t)


# ══════════════════════════════════════════════════════════════════════════════
print("0. El motor: el tramo comparable y el signo de los negativos")
from core import finance as F, theme as T                                    # noqa: E402
_D = dt.date
chk("⚠️ «This year» se compara con el mismo tramo del año pasado",
    F.periodo_comparable(_D(2026, 1, 1), _D(2026, 10, 13), "anio") == (_D(2025, 1, 1), _D(2025, 10, 13)))
chk("«This month» con los mismos días del mes anterior",
    F.periodo_comparable(_D(2026, 10, 1), _D(2026, 10, 13), "mes") == (_D(2026, 9, 1), _D(2026, 9, 13)))
chk("…y un día que no existe se ajusta (31/03 → 28/02)",
    F.periodo_comparable(_D(2026, 3, 1), _D(2026, 3, 31), "mes") == (_D(2026, 2, 1), _D(2026, 2, 28)))
chk("«Quarter» con el mismo tramo del trimestre anterior",
    F.periodo_comparable(_D(2026, 1, 1), _D(2026, 2, 10), "trimestre") == (_D(2025, 10, 1), _D(2025, 11, 10)))
chk("sin modo, lo de siempre (desplazar la duración)",
    F.periodo_comparable(_D(2026, 8, 1), _D(2026, 8, 16)) == F.periodo_anterior(_D(2026, 8, 1), _D(2026, 8, 16)))
chk("⚠️ negativo con el signo DELANTE («-\\$128»)", T.dinero(-128, 0) == "-\\$128", T.dinero(-128, 0))
chk("…y en HTML («-$128», sin barra)", T.dinero_html(-128, 0) == "-$128", T.dinero_html(-128, 0))
chk("…positivos sin cambio", T.dinero(1234.5) == "\\$1,234.50")

from streamlit.testing.v1 import AppTest                                    # noqa: E402

CAB = r'''
import datetime as dt
import streamlit as st
from core import projects_ui as PU, projects as P, finance as F, clock, auth
from core import expenses as E
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G",
                                     "nombre": "Jefa"})
clock.today = lambda *a, **k: dt.date(2026, 10, 13)
st.session_state.setdefault("_LL", [])
_VACIO = {"facturado": 0.0, "cobrado": 0.0, "por_cobrar": 0.0, "vencido": 0.0, "costo_nomina": 0.0,
          "compras": 0.0, "costo_total": 0.0, "ganancia": 0.0, "por_pagar": 0.0, "pagado": 0.0,
          "por_cliente": []}
_TODO = dict(_VACIO, facturado=1500.0, cobrado=1000.0, por_cobrar=500.0, vencido=200.0,
             compras=128.0, costo_total=1628.0, ganancia=-128.0, por_pagar=300.0,
             por_cliente=[("Cliente A", 1500.0)])
_ANIO = dict(_TODO)
_PREV = dict(_VACIO, facturado=1000.0, costo_total=1000.0, ganancia=0.0)
def _pnl(grupo, desde=None, hasta=None):
    st.session_state["_LL"].append(("pnl", desde, hasta))
    if desde is None:
        return dict(_TODO)
    if desde == dt.date(2026, 1, 1):
        return dict(_ANIO)
    if desde.year == 2025:
        return dict(_PREV)
    return dict(_VACIO)                     # octubre: sin movimiento
F.pnl = _pnl
_CC = {"cargado": 141.6, "cobrado_no_pagado": 0.0, "pagado_no_cargado": 4.05, "base_teorica": 145.65,
       "base_nomina": 0.0, "ausencias": 0.0, "aportes": 0.0, "costo_real": 0.0, "sin_explicar": 145.65,
       "interno": 0.0, "de_baja": []}
def _conc(grupo, desde=None, hasta=None):
    if desde is None:                       # el histórico: ana trabajó en septiembre sin tarifa
        return dict(_CC, sin_tarifa=["Ana Campo"], sin_tarifa_claves={"Ana Campo": "campo1"})
    return dict(_CC, sin_tarifa=[], sin_tarifa_claves={})
F.conciliacion_mo = _conc
F.sin_facturar_ids = lambda g: [("PRJ-1", "88 walker", 134.0), ("PRJ-2", "Movil", 133.0)]
F.group_profitability = lambda g: {"rows": [{"id": "PRJ-1", "nombre": "88 walker", "margen": 0},
                                            {"id": "PRJ-3", "nombre": "Con margen", "margen": 20}]}
E.over_budget = lambda g: []
F.resultado_por_proyecto = lambda g: [{"id": "PRJ-1", "nombre": "88 walker", "facturado": 0.0,
                                       "mo": 134.0, "compras": 0.0, "costo": 134.0,
                                       "resultado": -134.0, "margen": None}]
P.get_project = lambda pid: {"ID": pid, "Name": "88 walker", "Client": "", "Group": "G"}
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    for _k, _v in (st.session_state.get("_PRE") or {}).items():
        st.session_state[_k] = _v
PU.render_pnl("G")
'''

# ══════════════════════════════════════════════════════════════════════════════
print("\n1-2. ⚠️ Un mes sin movimiento: lo pendiente SIGUE, con saldos a hoy")
at = AppTest.from_string(CAB, default_timeout=90)
at.run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_kb = {b.key: b.label for b in at.button}
chk("⚠️ sin movimiento en octubre, la rejilla de pendientes SIGUE (antes, pantalla vacía)",
    all(f"pnlind_{s}" in _kb for s in ("venc", "cobrar", "sinfac", "pagar", "sinnom", "sintar", "sinmar", "over")),
    sorted(_kb))
chk("⚠️ «To collect» es el saldo a HOY ($500), no lo emitido en octubre ($0)",
    _kb.get("pnlind_cobrar", "").endswith("\\$500"), _kb.get("pnlind_cobrar"))
chk("…igual «Overdue» ($200) y «To pay» ($300)",
    _kb.get("pnlind_venc", "").endswith("\\$200") and _kb.get("pnlind_pagar", "").endswith("\\$300"))
chk("⚠️ «No rate» cuenta a quien trabajó ANTES del mes (saldo a hoy)",
    _kb.get("pnlind_sintar", "").endswith("1 person"), _kb.get("pnlind_sintar"))
chk("sin cifras del periodo, ni tarjetas a 0", not [k for k in _kb if str(k).startswith("cpxkpi_pnl_")])
chk("el aviso del periodo vacío y el botón «See All»", "pnl_ver_todo" in _kb
    and any("no invoices or costs" in i.value for i in at.info))
[b for b in at.button if b.key == "pnl_ver_todo"][0].click()
at.run()
chk("⚠️ «See All» cambia el periodo a «All»", at.session_state["cpxseg_pnl_per"] == "Todo"
    and [k for k in (b.key for b in at.button) if str(k).startswith("cpxkpi_pnl_")],
    at.session_state["cpxseg_pnl_per"])

PUS = io.open(os.path.join(RAIZ, "core", "projects_ui.py"), encoding="utf-8").read()
_t = ast.parse(PUS)


def _fn(nombre):
    return next(n for n in ast.walk(_t) if isinstance(n, ast.FunctionDef) and n.name == nombre)


_rp = _fn("render_pnl")
_rad = [n for n in ast.walk(_rp) if isinstance(n, ast.Call) and ast.unparse(n.func) == "st.radio"]
chk("⚠️ el periodo se RECUERDA (`persist_state='session'`)",
    len(_rad) == 1 and any(k.arg == "persist_state" and ast.unparse(k.value) == "'session'"
                           for k in _rad[0].keywords))

# ══════════════════════════════════════════════════════════════════════════════
print("\n4-8. «This year»: el tramo comparable y las tarjetas ACTIVAS")
at = AppTest.from_string(CAB, default_timeout=90)
at.session_state["_PRE"] = {"cpxseg_pnl_per": "Este año"}
at.run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("⚠️ compara con 01/01/2025 → 13/10/2025 (no «21/03–31/12» sin año)",
    ("pnl", _D(2025, 1, 1), _D(2025, 10, 13)) in at.session_state["_LL"]
    and any("compared with 01/01/2025 → 13/10/2025" in c.value for c in at.caption),
    [c.value for c in at.caption][:3])
_kb = {b.key: b.label for b in at.button}
chk("⚠️ 3 tarjetas-BOTÓN (Income, What you pay, Profit)",
    [k for k in _kb if str(k).startswith("cpxkpi_pnl_")] == ["cpxkpi_pnl_ing", "cpxkpi_pnl_cos", "cpxkpi_pnl_gan"],
    [k for k in _kb if str(k).startswith("cpxkpi_pnl_")])
chk("…con la comparación en inglés («▲ 50% vs previous»)",
    _kb.get("cpxkpi_pnl_ing", "").endswith("▲ 50% vs previous"), _kb.get("cpxkpi_pnl_ing"))
chk("⚠️ Profit negativo: «-\\$128» (no «$-128»)", "\n\n-\\$128\n\n" in _kb.get("cpxkpi_pnl_gan", ""),
    _kb.get("cpxkpi_pnl_gan"))
chk("el pie: clientes y margen", any("1 client(s) invoiced" in c.value and "margin -9%" in c.value
                                     for c in at.caption), [c.value for c in at.caption][:3])
for _k, _esp, _q in (("cpxkpi_pnl_cos", ("_pnl_tool", "comp"), "«What you pay» abre el desglose"),
                     ("cpxkpi_pnl_gan", ("_pnl_tool", "prj"), "«Profit» abre el resultado por obra")):
    at = AppTest.from_string(CAB, default_timeout=90)
    at.session_state["_PRE"] = {"cpxseg_pnl_per": "Este año"}
    at.run()
    [b for b in at.button if b.key == _k][0].click()
    at.run()
    chk("⚠️ " + _q, at.session_state[_esp[0]] == _esp[1], at.session_state[_esp[0]])
at = AppTest.from_string(CAB, default_timeout=90)
at.session_state["_PRE"] = {"cpxseg_pnl_per": "Este año"}
at.run()
[b for b in at.button if b.key == "cpxkpi_pnl_ing"][0].click()
at.run()
chk("⚠️ «Income» lleva a Invoices", at.session_state["_admin_nav_pending"] == ("finanzas", "🧾 Facturas"))

# ══════════════════════════════════════════════════════════════════════════════
print("\n5-6, 9, 11, 15. Los pendientes: nombres, dos líneas y detalles ACTIVOS")
at = AppTest.from_string(CAB, default_timeout=90)
at.session_state["_PRE"] = {"cpxseg_pnl_per": "Todo"}
at.run()
_kb = {b.key: b.label for b in at.button}
chk("⚠️ etiqueta ARRIBA y cifra DEBAJO («Not invoiced\\n\\n$267»)",
    _kb.get("pnlind_sinfac", "").endswith("Not invoiced\n\n\\$267"), _kb.get("pnlind_sinfac"))
chk("«Over budget» y «0 jobs» (no «Sobre ppto.»)", _kb.get("pnlind_over", "").endswith("Over budget\n\n0 jobs"),
    _kb.get("pnlind_over"))
chk("«No margin · 1 job» en singular", _kb.get("pnlind_sinmar", "").endswith("No margin\n\n1 job"),
    _kb.get("pnlind_sinmar"))
chk("⚠️ «Charged with no workday» (no «Hours with no payslip»)",
    "Charged with no workday" in _kb.get("pnlind_sinnom", "") and "payslip" not in _kb.get("pnlind_sinnom", ""))
chk("…y va a Hours, donde se ven", "\"⏱ Horas\", _det_sinnom" in PUS.replace("'", '"'))


def _abre(slug):
    a = AppTest.from_string(CAB, default_timeout=90)
    a.session_state["_PRE"] = {"cpxseg_pnl_per": "Todo"}
    a.run()
    [b for b in a.button if b.key == f"pnlind_{slug}"][0].click()
    a.run()
    return a


at = _abre("sinfac")
_kb = {b.key: b.label for b in at.button}
chk("⚠️ «Not invoiced»: un botón por obra", "pnlfac_PRJ-1" in _kb and "pnlfac_PRJ-2" in _kb, sorted(_kb))
chk("«→ Go to … Invoices» (no «→ Ir a Facturas»)",
    "Go to" in _kb.get("pnlgo_sinfac", "") and "Invoices" in _kb.get("pnlgo_sinfac", "")
    and "Ir a" not in _kb.get("pnlgo_sinfac", ""), _kb.get("pnlgo_sinfac"))
[b for b in at.button if b.key == "pnlfac_PRJ-1"][0].click()
at.run()
chk("⚠️ …tocar una obra prepara SU factura (`_ir_a_facturar`)",
    at.session_state["_fac_prj_pending"] == "PRJ-1"
    and at.session_state["_admin_nav_pending"] == ("finanzas", "🧾 Facturas"))
at = _abre("sintar")
_kb = {b.key: b.label for b in at.button}
chk("⚠️ «No rate»: la persona es un botón", "pnlrate_0" in _kb and "Ana Campo" in _kb.get("pnlrate_0", ""))
[b for b in at.button if b.key == "pnlrate_0"][0].click()
at.run()
chk("…que abre SU ficha en Users", at.session_state["gp_fichasel"] == "Ana Campo (campo1)"
    and at.session_state["_admin_nav_pending"] == ("planificacion", "👷 Usuarios"))
at = _abre("sinmar")
chk("«No margin»: «would be invoiced at cost» (no «Invoiced at cost»)",
    any("would be invoiced at cost" in c.value for c in at.caption)
    and not any(c.value.startswith("Invoiced at cost") for c in at.caption))
[b for b in at.button if b.key == "pnlmar_PRJ-1"][0].click()
at.run()
chk("⚠️ …la obra abre su ficha en Costs", at.session_state["_prjsel_pending"] == "PRJ-1"
    and at.session_state["_prj_sec_pending"] == "💰 Costos"
    and at.session_state["_admin_nav_pending"] == ("proyectos", "📊 Proyectos"))

# ══════════════════════════════════════════════════════════════════════════════
print("\n10. By project")
at = AppTest.from_string(CAB, default_timeout=90)
at.session_state["_PRE"] = {"cpxseg_pnl_per": "Todo", "_pnl_tool": "prj"}
at.run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_df = at.dataframe[0] if at.dataframe else None
chk("se pinta la tabla", _df is not None)
if _df is not None:
    chk("⚠️ el resultado y el margen DELANTE", list(_df.value.columns)[:3] == ["Proyecto", "Resultado", "Margen %"],
        list(_df.value.columns))
    _cfg = _df.proto.columns.replace(" ", "")
    chk("⚠️ cabeceras con etiqueta («Invoiced», «Result»; salían «Facturado»…)",
        '"Facturado":{"label":"Invoiced"' in _cfg and '"Resultado":{"label":"Result"' in _cfg, _cfg[:300])
    chk("la obra FIJADA", re.search(r'"Proyecto":\{[^}]*"pinned":true', _cfg) is not None, _cfg[:200])
    chk("⚠️ dinero con el signo delante (formato «dollar», no «$%,.0f»)",
        _cfg.count('"format":"dollar"') == 4, _cfg[:400])
chk("el acumulado «-\\$134»", any("Cumulative result across jobs: **-\\$134**" in m.value for m in at.markdown))
_pp = _fn("_pnl_por_proyecto")
_dfc = [n for n in ast.walk(_pp) if isinstance(n, ast.Call) and ast.unparse(n.func) == "st.dataframe"][0]
_kw = {k.arg: ast.unparse(k.value) for k in _dfc.keywords}
chk("⚠️ tocar una fila abre la obra (`on_select` + clave con generación)",
    _kw.get("on_select") == "'rerun'" and _kw.get("selection_mode") == "'single-row'"
    and "_gen" in _kw.get("key", ""), _kw)

# ══════════════════════════════════════════════════════════════════════════════
print("\n12. La tarjeta KPI compara en inglés")
from core import projects_ui as PU                                          # noqa: E402
_h = PU._kpi_card("X", "1", var={"dif": 5, "pct": 10.0, "mejor": True})
chk("«▲ 10% vs previous» (decía «vs. periodo anterior»)", "▲ 10% vs previous" in _h and "periodo" not in _h, _h)

print("\n13-14, 19. Textos con `t()`")
_lit = []
for fn in ("render_pnl", "_pnl_kpis", "_pnl_conciliacion", "_pnl_por_proyecto"):
    _f = _fn(fn)
    for n in ast.walk(_f):
        if (isinstance(n, ast.Call) and not ast.unparse(n.func).startswith("logger")
                and ast.unparse(n.func).split(".")[-1] in (
                    "caption", "warning", "info", "error", "success", "markdown", "button")):
            for a in n.args[:1]:
                if (isinstance(a, ast.Constant) and isinstance(a.value, str)
                        and re.search(r"[A-Za-z]{4}", re.sub(r":material/\w+:", "", a.value))
                        and not a.value.lstrip().startswith("<")):
                    _lit.append("%s:%d %s" % (fn, n.lineno, ast.unparse(a)[:60]))
                elif isinstance(a, ast.JoinedStr):
                    _txt = "".join(v.value for v in a.values if isinstance(v, ast.Constant))
                    if re.search(r"[A-Za-z]{4,}\s+[A-Za-z]{2,}", _txt):
                        _lit.append("%s:%d %s" % (fn, n.lineno, ast.unparse(a)[:60]))
        # las etiquetas que van por una TUPLA (conciliación) o por variable (trampa 30)
        if isinstance(n, ast.Tuple) and n.elts and isinstance(n.elts[0], ast.Constant) \
                and isinstance(n.elts[0].value, str) and re.search(r"[a-z]{4,} [a-z]{2,} [a-z]{2,}", n.elts[0].value):
            _lit.append("%s:%d tupla %s" % (fn, n.lineno, n.elts[0].value[:50]))
chk("⚠️ el Resumen sin frases sueltas (ni en tuplas)", not _lit, _lit)
chk("sin «Ir a», «Sobre ppto.» ni «pers.»", not re.search(r'Ir a |Sobre ppto|pers\.', ast.unparse(_rp)))
HUS = io.open(os.path.join(RAIZ, "core", "home_ui.py"), encoding="utf-8").read()
chk("de paso: las descripciones de Tools con `t()`", "st.caption(t(_desc.get(_id, '')))" in
    ast.unparse(next(n for n in ast.walk(ast.parse(HUS)) if isinstance(n, ast.FunctionDef)
                     and n.name == "_hub_herramientas")))

print("\n15-17. Dos por fila bajo 760 px (medido en producción)")
_css = ast.unparse(_rp)
chk("los dos bloques con clave y `container-type`",
    ".st-key-cpx_pnl_ind,.st-key-cpx_pnl_tools{container-type:inline-size}" in _css)
chk("⚠️ la regla `@container (max-width:760px)` con columnas al 50 %",
    "@container (max-width:760px)" in _css and "calc(50% - 0.5rem)" in _css)
chk("la cifra nunca se parte (`nowrap`)", "font-weight:700!important;white-space:nowrap!important" in _css)

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("TODO OK")
