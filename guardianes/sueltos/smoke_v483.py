# -*- coding: utf-8 -*-
"""Ejercita v483 contra la hoja REAL: importar no ejecuta (v378).

⚠️ Se lanza con cwd=survey_app o Streamlit no encuentra los secrets y salen rojos que
no existen (trampa nº19).
"""
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)                      # los secrets se buscan desde el CWD (trampa n19)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "admin", "nombre": "admin",
                            "rol": "administrator", "grupo": "cliente1"}

from core import contable, invoices, expenses, auth              # noqa: E402

G = "cliente1"
print("=" * 70)

# ── 1 · reparto del impuesto: la suma tiene que CUADRAR ─────────────────────
casos = [
    ([100.0, 200.0, 700.0], 100.0),
    ([0.333, 0.333, 0.334], 0.10),
    ([1000.0], 100.0),
    ([0.0, 0.0], 0.0),
    ([33.33] * 30, 99.99),
]
for imp, tot in casos:
    partes = contable.reparte_impuesto(imp, tot)
    suma = round(sum(partes), 2)
    print(f"  reparte {len(imp):>2} lineas · total {tot:>7.2f} -> suma {suma:>7.2f}"
          f"  {'OK' if suma == round(tot, 2) else '*** NO CUADRA ***'}")

# ── 2 · identidad y mapa contra la hoja real ────────────────────────────────
print("-" * 70)
ident = contable.identidad(G)
print("  identidad:", ident)
cfg = contable.mapa(G)
print("  moneda:", cfg["moneda"], "· gastos con impuesto:", cfg["gastos_incluyen_impuesto"])
print("  cuentas xero:", cfg["cuentas"]["xero"])
print("  cuentas myob:", cfg["cuentas"]["myob"])
print("  perfiles:", contable.perfiles())

# ── 3 · lo que hay en el libro ──────────────────────────────────────────────
print("-" * 70)
facs = invoices.list_facturas(G)
gastos = expenses.list_group(G)
print(f"  facturas: {len(facs)} · gastos del grupo: {len(gastos)}")

# ── 4 · los CSV de verdad, en los dos perfiles ──────────────────────────────
for perfil in ("xero", "myob"):
    print("-" * 70)
    for nombre, fn in (("VENTAS", contable.csv_ventas), ("COMPRAS", contable.csv_compras)):
        r = fn(G, perfil, None, None)
        print(f"  [{perfil}] {nombre}: {r['documentos']} doc · {r['filas']} filas")
        for a in r["avisos"]:
            print("      aviso:", a)
        for ln in r["csv"].splitlines()[:3]:
            print("      |", ln[:150])

# ── 5 · perfil inexistente no revienta ──────────────────────────────────────
print("-" * 70)
r = contable.csv_ventas(G, "sap", None, None)
print("  perfil desconocido ->", r["avisos"], "· filas", r["filas"])

print("=" * 70)
print("smoke terminado sin excepciones")
