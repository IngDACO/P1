# -*- coding: utf-8 -*-
"""Quita los datos de prueba de v495 de `cliente1`. Doble guarda: ID Y marca."""
import sys
import tomllib

import gspread
from google.oauth2.service_account import Credentials

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sec = tomllib.load(open("C:/Users/diego/P1/survey_app/.streamlit/secrets.toml", "rb"))
gc = gspread.authorize(Credentials.from_service_account_info(
    dict(sec["gcp_service_account"]), scopes=["https://www.googleapis.com/auth/spreadsheets"]))
D = gc.open_by_key("1WHGCrZndwdmqrR3RehLh7jocOIVkRvjAbigifvfSe1Y")
SIMULAR = "--real" not in sys.argv

plan = []
wf = D.worksheet("Invoices")
vf = wf.get_all_values()
hf = vf[0]
filas = [i for i, r in enumerate(vf[1:], start=2)
         if dict(zip(hf, r)).get("ID") == "FAC-0001"
         and dict(zip(hf, r)).get("Note", "").startswith("ZZ PRUEBA v495")
         and dict(zip(hf, r)).get("Number") == "V495-0001"]
assert len(filas) == 1, filas
plan.append(("Invoices", filas[0], vf[filas[0] - 1]))

wc = D.worksheet("Clients")
vc = wc.get_all_values()
hc = vc[0]
filc = [i for i, r in enumerate(vc[1:], start=2)
        if dict(zip(hc, r)).get("ID") == "CLI-0001"
        and dict(zip(hc, r)).get("Name", "").startswith("ZZ PRUEBA v495")]
assert len(filc) == 1, filc
plan.append(("Clients", filc[0], vc[filc[0] - 1]))

for hoja, fila, datos in plan:
    print("PLAN borrar", hoja, "fila", fila, "->", [x for x in datos if x][:6])
if SIMULAR:
    print("simulación: nada borrado")
    sys.exit(0)
wf.delete_rows(filas[0])
wc.delete_rows(filc[0])
print("borrado")
print("Invoices:", len(wf.get_all_values()) - 1, "filas · Clients:", len(wc.get_all_values()) - 1, "filas")
