# -*- coding: utf-8 -*-
"""v567 · LO VISTO VERIFICANDO v566 EN PRODUCCIÓN (decisión del usuario: «Dale»).

  1. Las tarjetas-botón `cpxkpi_` con texto corto salían CENTRADAS (un `<span>` flex
     encoge al texto: 43 px en 146) → a todo el ancho y a la izquierda (CSS medido en vivo).
  2. La herramienta abierta desde una tarjeta se pintaba FUERA de la vista (y=1168 con 698
     de alto) → la vista baja a ella UNA vez (patrón de v553).
  3. El margen de una obra sin facturar salía «None» → «—» (texto a la derecha; `None` y
     `NaN` se pintan los dos «None», medido en una mini-app 1.64).
  4. Una fila de By project solo se abría con su casilla → `single-cell`: un toque en
     cualquier celda (medido: `cells=[(0, col)]`).

AppTest con las fuentes de datos sustituidas: ninguna hoja se toca.
"""
import ast
import io
import os
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


print("1. Las tarjetas-botón, a la izquierda (CSS del kit)")
from core import theme as T                                                  # noqa: E402
_css = T.CSS if hasattr(T, "CSS") else ""
if not _css:
    _css = io.open(os.path.join(RAIZ, "core", "theme.py"), encoding="utf-8").read()
# ⚠️ Sin NINGÚN espacio en blanco (también los saltos de línea: la regla va en varias
# líneas y la 1ª versión de la sonda solo quitaba los espacios — rojo con el CSS bien).
import re                                                                    # noqa: E402
_c = re.sub(r"\s+", "", _css).replace("{{", "{").replace("}}", "}")
chk("⚠️ el envoltorio del botón a todo el ancho y a la izquierda",
    '[class*="st-key-cpxkpi_"]button>div{width:100%;justify-content:flex-start!important;}' in _c, "")
chk("⚠️ …y el `<span>` flex que encogía, estirado",
    '[class*="st-key-cpxkpi_"]button>div>span{flex:11auto;width:100%;justify-content:flex-start!important;}' in _c, "")

from streamlit.testing.v1 import AppTest                                    # noqa: E402

CAB = r'''
import datetime as dt
import streamlit as st
from core import projects_ui as PU, projects as P, finance as F, clock, incrustar
from core import expenses as E
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G",
                                     "nombre": "Jefa"})
clock.today = lambda *a, **k: dt.date(2026, 10, 13)
st.session_state.setdefault("_LL", [])
incrustar.script = lambda h, *a, **k: st.session_state["_LL"].append(("script", h))
_TODO = {"facturado": 1500.0, "cobrado": 1000.0, "por_cobrar": 500.0, "vencido": 0.0,
         "costo_nomina": 0.0, "compras": 128.0, "costo_total": 128.0, "ganancia": 1372.0,
         "por_pagar": 0.0, "pagado": 0.0, "por_cliente": [("Cliente A", 1500.0)]}
F.pnl = lambda grupo, desde=None, hasta=None: dict(_TODO)
F.conciliacion_mo = lambda grupo, desde=None, hasta=None: {
    "cargado": 0.0, "cobrado_no_pagado": 0.0, "pagado_no_cargado": 0.0, "base_teorica": 0.0,
    "base_nomina": 0.0, "ausencias": 0.0, "aportes": 0.0, "costo_real": 0.0, "sin_explicar": 0.0,
    "interno": 0.0, "de_baja": [], "sin_tarifa": [], "sin_tarifa_claves": {}}
F.sin_facturar_ids = lambda g: []
F.group_profitability = lambda g: {"rows": []}
E.over_budget = lambda g: []
F.resultado_por_proyecto = lambda g: [
    {"id": "PRJ-1", "nombre": "Sin facturar", "facturado": 0.0, "mo": 134.0, "compras": 0.0,
     "costo": 134.0, "resultado": -134.0, "margen": None},
    {"id": "PRJ-2", "nombre": "Facturada", "facturado": 500.0, "mo": 100.0, "compras": 0.0,
     "costo": 100.0, "resultado": 400.0, "margen": 80.0}]
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    for _k, _v in (st.session_state.get("_PRE") or {}).items():
        st.session_state[_k] = _v
PU.render_pnl("G")
'''

print("\n2. ⚠️ La herramienta abierta desde una TARJETA: la vista baja a ella UNA vez")
at = AppTest.from_string(CAB, default_timeout=90)
at.session_state["_PRE"] = {"cpxseg_pnl_per": "Todo"}
at.run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
[b for b in at.button if b.key == "cpxkpi_pnl_gan"][0].click()
at.run()
_scr = [x for x in at.session_state["_LL"] if x[0] == "script"]
chk("⚠️ tocar «Profit» abre la herramienta Y lleva la vista a ella (un script)",
    at.session_state["_pnl_tool"] == "prj" and len(_scr) == 1, (at.session_state["_pnl_tool"], len(_scr)))
chk("…que busca el recuadro de la herramienta y espera a que la pasada termine",
    _scr and ".st-key-cpx_pnl_panel" in _scr[0][1] and "data-test-script-state" in _scr[0][1]
    and "block:'nearest'" in _scr[0][1] and "window.parent" in _scr[0][1])
_PUS0 = io.open(os.path.join(RAIZ, "core", "projects_ui.py"), encoding="utf-8").read()
_rp = next(n for n in ast.walk(ast.parse(_PUS0)) if isinstance(n, ast.FunctionDef) and n.name == "render_pnl")
chk("⚠️ …y el recuadro de la herramienta LLEVA esa clave (si no, el script no encuentra nada)",
    any(isinstance(n, ast.Call) and ast.unparse(n.func) == "st.container"
        and any(k.arg == "key" and ast.unparse(k.value) == "'cpx_pnl_panel'" for k in n.keywords)
        for n in ast.walk(_rp)))
at.run()
chk("⚠️ UNA sola vez: otra pasada no vuelve a mover la vista",
    len([x for x in at.session_state["_LL"] if x[0] == "script"]) == 1)
at = AppTest.from_string(CAB, default_timeout=90)
at.session_state["_PRE"] = {"cpxseg_pnl_per": "Todo"}
at.run()
[b for b in at.button if b.key == "pnltool_conc"][0].click()
at.run()
chk("desde la fila de herramientas (ya está debajo) no hace falta: sin script",
    at.session_state["_pnl_tool"] == "conc" and not [x for x in at.session_state["_LL"] if x[0] == "script"])

print("\n3-4. By project: «—» en vez de «None», y una celda abre la obra")
at = AppTest.from_string(CAB, default_timeout=90)
at.session_state["_PRE"] = {"cpxseg_pnl_per": "Todo", "_pnl_tool": "prj"}
at.run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_df = at.dataframe[0] if at.dataframe else None
if _df is not None:
    chk("⚠️ el margen de una obra SIN facturar es «—» (no «None»)",
        list(_df.value["Margen %"]) == ["—", "80.0%"], list(_df.value["Margen %"]))
    _cfg = _df.proto.columns.replace(" ", "")
    chk("…como texto alineado a la DERECHA (se lee como una cifra)",
        '"Margen%":{"label":"Margin%"' in _cfg and '"alignment":"right"' in _cfg, _cfg[:400])
else:
    chk("se pinta la tabla", False)
PUS = io.open(os.path.join(RAIZ, "core", "projects_ui.py"), encoding="utf-8").read()
_pp = next(n for n in ast.walk(ast.parse(PUS)) if isinstance(n, ast.FunctionDef) and n.name == "_pnl_por_proyecto")
_dfc = [n for n in ast.walk(_pp) if isinstance(n, ast.Call) and ast.unparse(n.func) == "st.dataframe"][0]
_kw = {k.arg: ast.unparse(k.value) for k in _dfc.keywords}
chk("⚠️ `single-cell`: un toque en la celda elige (con «single-row» hacía falta la casilla)",
    _kw.get("selection_mode") == "'single-cell'", _kw.get("selection_mode"))
at = AppTest.from_string(CAB, default_timeout=90)
at.session_state["_PRE"] = {"cpxseg_pnl_per": "Todo", "_pnl_tool": "prj",
                            "pnl_prj_tbl_0": {"selection": {"rows": [], "columns": [],
                                                            "cells": [(1, "Resultado")]}}}
at.run()
chk("⚠️ una CELDA de la 2ª fila abre ESA obra en Costs",
    at.session_state["_prjsel_pending"] == "PRJ-2" if "_prjsel_pending" in at.session_state else False,
    at.session_state["_prjsel_pending"] if "_prjsel_pending" in at.session_state else "—")
chk("…con otra generación de clave (al volver no salta sola)",
    at.session_state["_pnl_prj_gen"] == 1 if "_pnl_prj_gen" in at.session_state else False)
chk("…y el pie dice lo que pasa («Tap a job to open it»)",
    any("Tap a job to open it in its Costs." in c.value for c in at.caption)
    or "Tap a job to open it in its Costs." in PUS)

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("TODO OK")
