# -*- coding: utf-8 -*-
"""v492 contra la hoja REAL: guardar por claves no congela lo de fábrica. Deja todo como estaba."""
import json
import os
import sys
import tomllib

import gspread
from google.oauth2.service_account import Credentials

os.chdir("C:/Users/diego/P1/survey_app")
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import streamlit as st  # noqa: E402

G = "cliente1"
st.session_state["auth"] = {"usuario": "Admin2", "rol": "administrator", "nombre": "Bobo", "grupo": G}
from core import auth, contable, xero_nomina as XN  # noqa: E402

sec = tomllib.load(open(".streamlit/secrets.toml", "rb"))
_ro = gspread.authorize(Credentials.from_service_account_info(
    dict(sec["gcp_service_account"]),
    scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]))


def crudo():
    """Lectura en SOLO LECTURA con gspread crudo, sin pasar por los helpers de la app."""
    v = _ro.open_by_key(sec["TIMECLOCK_SHEET_ID"]).worksheet("Groups").get_all_values()
    h = v[0]
    r = next(x for x in v[1:] if x and x[0] == G)
    r = r + [""] * (len(h) - len(r))
    return r[h.index("AccountingJSON")]


fallos = []


def ck(que, real, esp):
    print(("  ok   " if real == esp else "  *** FALLO  ") + que + ("" if real == esp else f"  -> {real!r} != {esp!r}"))
    if real != esp:
        fallos.append(que)


antes = crudo()
print("antes:", repr(antes))
assert antes == "", "la prueba asume AccountingJSON vacío (así estaba tras limpiar v491)"
try:
    ok, msg = XN.guardar_emparejado(G, "TENANT-PRUEBA-v492", {"ZZ PRUEBA v492": "EMP-X"})
    ck("guardar_emparejado devuelve ok", ok, True)
    g1 = json.loads(crudo() or "{}")
    ck("en la HOJA solo queda xero_empleados (nada de fábrica congelado)", sorted(g1), ["xero_empleados"])
    ok, msg = contable.guardar_claves(G, {"xero_estado": "DRAFT"})
    g2 = json.loads(crudo() or "{}")
    ck("guardar otra clave CONSERVA el emparejado", (sorted(g2), g2.get("xero_empleados", {}).get("map")),
       (["xero_empleados", "xero_estado"], {"ZZ PRUEBA v492": "EMP-X"}))
    auth._invalidate_groups()
    m = contable.mapa(G)
    ck("mapa() sigue viendo lo de fábrica debajo", m.get("cuentas", {}).get("xero", {}).get(contable.VENTAS), "200")
finally:
    ok, msg = auth.set_group_setting(G, "AccountingJSON", "")
    print("restaurado:", ok, msg)
despues = crudo()
ck("AccountingJSON vuelve a estar EXACTAMENTE como antes", despues, antes)
print("\nTODO OK" if not fallos else f"\nHAY FALLOS: {fallos}")
sys.exit(1 if fallos else 0)
