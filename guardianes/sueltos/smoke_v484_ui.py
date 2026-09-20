# -*- coding: utf-8 -*-
"""EJECUTA la pantalla del parte. Importar no ejecuta (v378), y estos fallos
—un nombre sin importar, una función del kit que DEVUELVE en vez de pintar— no los
ven ni `compileall` ni el import (v423/v424/v425).
"""
import datetime as dt
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd                                               # noqa: E402
import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "admin", "nombre": "admin",
                            "rol": "administrator", "grupo": "cliente1"}

from core import contable, contable_ui, theme as T                 # noqa: E402

G = "cliente1"
pintado = {"kpi": 0, "dataframe": 0, "download": 0, "warning": 0, "caption": 0,
           "section": 0, "expander": 0, "editor": 0}
fallos = []


class _Col:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def __getattr__(self, n):
        return _finge(n)


def _finge(nombre):
    def _f(*a, **kw):
        if nombre == "date_input":
            return kw.get("value") or dt.date.today()
        if nombre == "data_editor":
            pintado["editor"] += 1
            return a[0] if a and isinstance(a[0], pd.DataFrame) else pd.DataFrame()
        if nombre == "download_button":
            pintado["download"] += 1
            return False
        if nombre in ("dataframe", "warning", "caption", "expander", "radio",
                      "button", "checkbox", "text_input", "markdown", "code",
                      "columns", "error"):
            if nombre in pintado:
                pintado[nombre] += 1
            if nombre == "columns":
                n = a[0] if a else 2
                return [_Col() for _ in range(n if isinstance(n, int) else len(n))]
            if nombre == "expander":
                return _Col()
            if nombre == "radio":
                return (a[1][0] if len(a) > 1 and a[1] else None)
            if nombre == "checkbox":
                return kw.get("value", False)
            if nombre == "text_input":
                return kw.get("value", "")
            if nombre == "button":
                return False
            return None
        return None
    return _f


_guardado = {}
for n in ("date_input", "data_editor", "download_button", "dataframe", "warning",
          "caption", "expander", "radio", "button", "checkbox", "text_input",
          "markdown", "code", "columns", "error"):
    _guardado[n] = getattr(st, n)
    setattr(st, n, _finge(n))
_sec = T.section
T.section = lambda *a, **kw: pintado.__setitem__("section", pintado["section"] + 1)
_kpi = T.kpi_row


def _kpi_espia(items):
    pintado["kpi"] += 1
    # ⚠️ kpi_row PINTA (no devuelve, que es el fallo de v424): se comprueba que las
    # tarjetas llegan con sus tres partes y que ninguna trae None por valor.
    for it in items:
        if it[1] is None:
            fallos.append("una tarjeta KPI con valor None")
    return _kpi(items)


T.kpi_row = _kpi_espia

try:
    print("=" * 72)
    print("[1] _partes_section EJECUTADA con los datos reales del grupo")
    contable_ui._partes_section(G)
    print("   pintado:", pintado)
    for k in ("kpi", "download", "caption", "expander"):
        if not pintado[k]:
            fallos.append(f"no se pinto {k}")
    if not pintado["editor"]:
        fallos.append("el editor de earnings rates no se pinto")

    print()
    print("[2] la pantalla ENTERA, que es donde se vería un nombre sin importar")
    antes = dict(pintado)
    contable_ui.render_contable(G)
    print("   pintado:", {k: pintado[k] - antes[k] for k in pintado})
    if pintado["section"] - antes["section"] < 1:
        fallos.append("render_contable no pinto la seccion del parte")
    if pintado["download"] - antes["download"] < 3:
        fallos.append("faltan botones de descarga (facturas + gastos + parte)")
except Exception as e:
    import traceback
    traceback.print_exc()
    fallos.append(f"{type(e).__name__}: {e}")
finally:
    for n, f in _guardado.items():
        setattr(st, n, f)
    T.section, T.kpi_row = _sec, _kpi

print("=" * 72)
print("TODO OK" if not fallos else f"{len(fallos)} FALLOS: {fallos}")
sys.exit(1 if fallos else 0)
