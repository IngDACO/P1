# -*- coding: utf-8 -*-
"""Borra SOLO lo que sembro crear_v486prod.py en el libro de cliente1.

Doble guarda: el ID tiene que estar en creado_v486prod.json Y la fila tiene que llevar
la marca «ZZ PRUEBA» en alguna celda. Si una fila casa por ID pero no lleva la marca,
NO se toca y se avisa: seria de otra persona.
Se borra de abajo a arriba para que los indices no se desplacen.
"""
import io
import json
import os
import tomllib

import gspread
from google.oauth2.service_account import Credentials

AQUI = os.path.dirname(os.path.abspath(__file__))
SEC = "C:/Users/diego/P1/survey_app/.streamlit/secrets.toml"

with open(SEC, "rb") as f:
    sec = tomllib.load(f)
cred = Credentials.from_service_account_info(
    dict(sec["gcp_service_account"]),
    scopes=["https://www.googleapis.com/auth/spreadsheets"])
gc = gspread.authorize(cred)

maestro = gc.open_by_key(str(sec["TIMECLOCK_SHEET_ID"]))
grupos = maestro.worksheet("Groups").get_all_values()
cab = grupos[0]
fila = next(r for r in grupos[1:] if r[cab.index("Group")] == "cliente1")
libro = gc.open_by_key(fila[cab.index("SheetID")])

with io.open(os.path.join(AQUI, "creado_v486prod.json"), encoding="utf-8") as f:
    creado = json.load(f)

for hoja, ids in creado.items():
    if not ids:
        continue
    w = libro.worksheet(hoja)
    vals = w.get_all_values()
    borrar, ajenas = [], []
    for i, r in enumerate(vals[1:], start=2):
        if r and r[0] in ids:
            if any("ZZ PRUEBA" in c or "zzprueba" in c for c in r):
                borrar.append(i)
            else:
                ajenas.append((i, r[0]))
    for i in sorted(borrar, reverse=True):
        w.delete_rows(i)
    print("%-15s borradas %d (filas %s)%s" % (
        hoja, len(borrar), sorted(borrar),
        ("  !! NO tocadas por no llevar la marca: %s" % ajenas) if ajenas else ""))
