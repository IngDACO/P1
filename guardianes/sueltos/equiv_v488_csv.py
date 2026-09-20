# -*- coding: utf-8 -*-
"""v488: el CSV de ventas tiene que salir IDENTICO byte a byte tras extraer
`documento_venta` (la definicion unica que ahora comparten CSV y API de Xero).

Se carga la version ANTERIOR sacada del commit y se ejecutan las dos sobre las
MISMAS facturas construidas (casos limite) con las fuentes sustituidas.
"""
import importlib.util
import json
import os
import sys

RAIZ = "C:/Users/diego/P1/survey_app"
AQUI = os.path.dirname(os.path.abspath(__file__))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)

import streamlit as st  # noqa: E402

st.session_state["auth"] = {"usuario": "zz", "rol": "administrator", "grupo": "cliente1"}

from core import contable as NEW  # noqa: E402

spec = importlib.util.spec_from_file_location("core.contable_old",
                                              os.path.join(AQUI, "_v488_old_contable.py"))
OLD = importlib.util.module_from_spec(spec)
spec.loader.exec_module(OLD)

L = lambda xs: json.dumps(xs)  # noqa: E731
FACTURAS = [
    {"ID": "FAC-0001", "Group": "g", "ClientID": "CLI-1", "ClientName": "Acme Pty",
     "Number": "0003", "Date": "2026-09-01", "ExpiryDate": "2026-09-15",
     "LinesJSON": L([{"concepto": "A", "importe": 33.33, "proyecto_id": "PRJ-1"},
                     {"concepto": "B", "importe": 33.33, "proyecto_id": "PRJ-2"},
                     {"concepto": "", "importe": 33.34, "proyecto_id": ""}]),
     "TaxPct": "10", "Tax": "10.00", "Status": "emitida"},
    {"ID": "FAC-0002", "Group": "g", "ClientID": "", "ClientName": "",
     "Number": "0001", "Date": "01/09/2026", "ExpiryDate": "",
     "LinesJSON": L([{"concepto": "Sin cliente ni vence", "importe": "1,234.56",
                      "proyecto_id": "PRJ-LARGO"}]),
     "TaxPct": "0", "Tax": "0", "Status": "emitida"},
    {"ID": "FAC-0003", "Group": "g", "ClientID": "CLI-2", "ClientName": "Anulada",
     "Number": "0002", "Date": "2026-09-02", "ExpiryDate": "2026-09-03",
     "LinesJSON": L([{"concepto": "x", "importe": 5}]), "TaxPct": "10", "Tax": "0.5",
     "Status": "anulada"},
    {"ID": "FAC-0004", "Group": "g", "ClientID": "CLI-2", "ClientName": "",
     "Number": "0004", "Date": "2026-09-03", "ExpiryDate": "2026-09-30",
     "LinesJSON": "[]", "TaxPct": "10", "Tax": "0", "Status": "emitida"},
    {"ID": "FAC-0005", "Group": "g", "ClientID": "CLI-2", "ClientName": "",
     "Number": "0005", "Date": "2026-09-04", "ExpiryDate": "fecha rara",
     "LinesJSON": L([{"concepto": "Z" * 300, "importe": 100, "proyecto_id": "PRJ-1"},
                     {"concepto": "neg", "importe": -20, "proyecto_id": "PRJ-2"}]),
     "TaxPct": "10", "Tax": "8.00", "Status": "Emitida"},
    {"ID": "FAC-0006", "Group": "g", "ClientID": "CLI-1", "ClientName": "Acme Pty",
     "Number": "0006", "Date": "2026-10-04", "ExpiryDate": "2026-10-18",
     "LinesJSON": L([{"concepto": "fuera de rango", "importe": 50}]),
     "TaxPct": "10", "Tax": "5", "Status": "void"},
]
CLIENTES = [{"ID": "CLI-1", "Name": "Acme Pty", "Email": "a@example.com", "Address": "1 St"},
            {"ID": "CLI-2", "Name": "Beta, \"Ltd\"", "Email": "", "Address": "2\nSt"}]
ETQ = {"PRJ-1": "Torre Norte", "PRJ-2": "Torre Norte (PRJ-2)",
       "PRJ-LARGO": "X" * 60}


def parche(mod, seguimiento=True, abn="", cuentas=None):
    mod.invoices.list_facturas = lambda grupo=None, cliente_id=None: list(FACTURAS)
    mod.clientes.list_clientes = lambda grupo, incluir_inactivos=False: list(CLIENTES)
    cfgjson = json.dumps({"seguimiento": seguimiento,
                          **({"cuentas": cuentas} if cuentas else {})})
    txt = {"AccountingJSON": cfgjson, "ABN": abn, "LegalName": "", "PaymentTermsDays": ""}
    mod.auth.group_text_setting = lambda g, field, default="": txt.get(field, default) or default
    mod._etiquetas = lambda g: dict(ETQ)


import datetime as _dt  # noqa: E402

fallos = 0
casos = 0
for perfil in ("xero", "myob"):
    for seg in (True, False):
        for abn in ("", "12 345 678 901"):
            for rango in ((None, None), (_dt.date(2026, 9, 1), _dt.date(2026, 9, 30))):
                for cuentas in (None, {"xero": {"_ventas": ""}, "myob": {"_ventas": "4-9999"}}):
                    parche(OLD, seg, abn, cuentas)
                    parche(NEW, seg, abn, cuentas)
                    a = OLD.csv_ventas("g", perfil, *rango)
                    b = NEW.csv_ventas("g", perfil, *rango)
                    casos += 1
                    if a != b:
                        fallos += 1
                        print("DIFERENTE", perfil, seg, abn, rango, cuentas)
                        for k in a:
                            if a[k] != b[k]:
                                print("  clave", k, repr(a[k])[:300], "||", repr(b[k])[:300])
parche(NEW)
muestra = NEW.csv_ventas("g", "xero")
print("casos", casos, "diferencias", fallos)
print("filas de muestra:", muestra["filas"], "documentos:", muestra["documentos"])
assert muestra["filas"] >= 5 and muestra["documentos"] == 3, "el caso no ejercita nada"
print("OK identico" if fallos == 0 else "*** DIFIERE ***")
sys.exit(1 if fallos else 0)
