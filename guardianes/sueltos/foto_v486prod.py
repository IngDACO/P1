# -*- coding: utf-8 -*-
"""Foto en SOLO LECTURA del libro de cliente1 (gspread crudo, scope readonly).

Nunca por los helpers de la app: migran cabeceras al acceder, o sea que ESCRIBEN (v145).
Uso: python foto_v486prod.py antes|despues
"""
import io
import json
import os
import sys
import tomllib

import gspread
from google.oauth2.service_account import Credentials

AQUI = os.path.dirname(os.path.abspath(__file__))
SEC = "C:/Users/diego/P1/survey_app/.streamlit/secrets.toml"
HOJAS = ["Catalogue", "Payroll", "Assets", "AssetMovements", "Auditoria"]

with open(SEC, "rb") as f:
    sec = tomllib.load(f)
cred = Credentials.from_service_account_info(
    dict(sec["gcp_service_account"]),
    scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
gc = gspread.authorize(cred)

maestro = gc.open_by_key(str(sec["TIMECLOCK_SHEET_ID"]))
grupos = maestro.worksheet("Groups").get_all_values()
cab = grupos[0]
fila = next(r for r in grupos[1:] if r[cab.index("Group")] == "cliente1")
libro_id = fila[cab.index("SheetID")] if "SheetID" in cab else ""
libro = gc.open_by_key(libro_id) if libro_id else maestro
titulos = [w.title for w in libro.worksheets()]

foto = {"libro_propio": bool(libro_id), "hojas": {}}
for h in HOJAS:
    if h not in titulos:
        foto["hojas"][h] = None
        continue
    vals = libro.worksheet(h).get_all_values()
    ids = [r[0] for r in vals[1:] if r and r[0]]
    foto["hojas"][h] = {"cabecera": vals[0] if vals else [], "filas": len(vals) - 1 if vals else 0,
                        "ids": ids}

modo = sys.argv[1] if len(sys.argv) > 1 else "antes"
with io.open(os.path.join(AQUI, "foto_v486prod_%s.json" % modo), "w", encoding="utf-8") as f:
    json.dump(foto, f, ensure_ascii=False, indent=1)
print("libro propio de cliente1:", foto["libro_propio"])
for h, d in foto["hojas"].items():
    print("  %-15s %s" % (h, "NO EXISTE" if d is None else "%d filas · ids %s" % (d["filas"], d["ids"][-5:])))
