# -*- coding: utf-8 -*-
"""¿Qué está pendiente DE VERDAD? Auditado contra la hoja, no contra el documento.

⚠️ SOLO LECTURA con gspread crudo y scope `spreadsheets.readonly`: los helpers de la app
MIGRAN la cabecera al acceder, así que una «lectura» por ahí escribe (regla v145).
"""
import json
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gspread                                                    # noqa: E402
import streamlit as st                                            # noqa: E402
from google.oauth2.service_account import Credentials             # noqa: E402

cred = Credentials.from_service_account_info(
    dict(st.secrets["gcp_service_account"]),
    scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
gc = gspread.authorize(cred)
MAESTRO = st.secrets["TIMECLOCK_SHEET_ID"]
libro = gc.open_by_key(MAESTRO)
hojas = {w.title: w for w in libro.worksheets()}
print("MAESTRO: %d pestañas" % len(hojas))

# el libro de la DEMO (cliente1) vive aparte desde v377
grp = hojas["Groups"].get_all_values()
cab = grp[0]
def col(n):
    return cab.index(n) if n in cab else -1

print("\n── GRUPOS ──")
for fila in grp[1:]:
    g = fila[0] if fila else ""
    if not g:
        continue
    sid = fila[col("SheetID")] if col("SheetID") >= 0 and len(fila) > col("SheetID") else ""
    abn = fila[col("ABN")] if col("ABN") >= 0 and len(fila) > col("ABN") else ""
    legal = fila[col("LegalName")] if col("LegalName") >= 0 and len(fila) > col("LegalName") else ""
    acc = fila[col("AccountingJSON")] if col("AccountingJSON") >= 0 and len(fila) > col("AccountingJSON") else ""
    try:
        emp = json.loads(acc or "{}").get("xero_empleados", {})
    except Exception:
        emp = {}
    print("  %-12s libro propio: %-5s  ABN: %-14s  LegalName: %-22s  empleados Xero emparejados: %d"
          % (g, bool(sid), abn or "(vacío)", legal or "(vacío)", len(emp.get("map", emp) or {})))

print("\n── CREDENCIALES (el pendiente de v498) ──")
if "Credentials" in hojas:
    filas = hojas["Credentials"].get_all_values()
    print("  filas: %d" % max(0, len(filas) - 1))
    for f in filas[1:6]:
        print("    %s" % " · ".join(f[:6]))
else:
    print("  la pestaña no existe")

# ── el libro del cliente ──
sid = ""
for fila in grp[1:]:
    if fila and fila[0] == "cliente1" and col("SheetID") >= 0 and len(fila) > col("SheetID"):
        sid = fila[col("SheetID")]
if sid:
    lib2 = gc.open_by_key(sid)
    h2 = {w.title: w for w in lib2.worksheets()}
    print("\n── LIBRO DE cliente1: %d pestañas ──" % len(h2))
    for nombre in ("Projects", "Activities"):
        if nombre not in h2:
            print("  %s: NO existe" % nombre)
            continue
        vals = h2[nombre].get_all_values()
        c = vals[0] if vals else []
        print("  %-11s %3d filas · %d columnas" % (nombre, max(0, len(vals) - 1), len(c)))
        if nombre == "Activities":
            hay = "Predecessors" in c
            print("     columna «Predecessors» en la hoja: %s" % ("SÍ" if hay else
                  "NO — la crea la app al abrir un proyecto (migración de cabecera)"))
            if hay:
                i = c.index("Predecessors")
                con = [f for f in vals[1:] if len(f) > i and str(f[i]).strip()]
                print("     actividades con dependencia declarada: %d de %d"
                      % (len(con), max(0, len(vals) - 1)))
    if "Invoices" in h2:
        v = h2["Invoices"].get_all_values()
        print("  %-11s %3d filas" % ("Invoices", max(0, len(v) - 1)))
