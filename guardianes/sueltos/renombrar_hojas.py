# -*- coding: utf-8 -*-
"""Renombra las pestañas de los DOS libros al ingles.

  python renombrar_hojas.py seco       -> dice que haria, sin tocar nada
  python renombrar_hojas.py aplicar    -> renombra y verifica leyendo

⚠️ ORDEN OBLIGATORIO: primero se despliega el codigo con el respaldo (v465) y
DESPUES se renombra. Al reves, la app que esta corriendo pide el nombre viejo, no
lo encuentra y **crea una pestaña vacia** donde se pone a escribir — sin ningun
error y con los datos intactos al lado.
"""
import os
import sys

os.chdir(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, os.getcwd())
import streamlit as st
st.session_state["auth"] = {"usuario": "dacox", "rol": "propietario", "grupo": "cliente1"}

import gspread
from google.oauth2.service_account import Credentials
from core import timeclock, auth

MODO = sys.argv[1] if len(sys.argv) > 1 else "seco"
ALCANCE = ["https://www.googleapis.com/auth/spreadsheets"] if MODO == "aplicar" \
    else ["https://www.googleapis.com/auth/spreadsheets.readonly"]
gc = gspread.authorize(Credentials.from_service_account_info(
    dict(st.secrets["gcp_service_account"]), scopes=ALCANCE))

# viejo -> nuevo, derivado del mapa que usa la app (no una copia mia: si divergen,
# el codigo buscaria un nombre que el libro no tiene)
NUEVO = {v: k for k, v in timeclock.LEGADO.items()}
CANON = {}
for p in ("projects", "catalogo", "inventory", "invoices", "payroll", "quotes",
          "orders", "auditoria", "ausencias", "correcciones", "clientes",
          "credentials", "expenses", "alerts", "auth", "rails", "roster",
          "toolruns", "manuals"):
    try:
        m = __import__("core." + p, fromlist=["x"])
    except Exception:
        continue
    for n in dir(m):
        v = getattr(m, n, None)
        if n.endswith("SHEET") and isinstance(v, str):
            CANON[v.lower()] = v          # la capitalizacion EXACTA que usa el codigo

libros = {"MAESTRO": st.secrets["TIMECLOCK_SHEET_ID"]}
sid = auth.group_sheet_id("cliente1")
if sid and sid != libros["MAESTRO"]:
    libros["DEMO (cliente1)"] = sid

total = 0
for nombre, s_id in libros.items():
    sh = gc.open_by_key(s_id)
    titulos = {w.title for w in sh.worksheets()}
    print("── %s" % nombre)
    for w in sh.worksheets():
        if w.title not in NUEVO:
            continue                      # Sheet1, Login, Roster, PreStarts…
        destino = CANON.get(NUEVO[w.title], NUEVO[w.title])
        if destino in titulos:
            # ⚠️ No se renombra encima de una que ya existe: seria un choque de
            # titulos y ademas significaria que hay DOS hojas con los mismos datos.
            print("   ⚠️ %-22s ya existe %r: NO se toca, hay que mirarlo" % (w.title, destino))
            continue
        if MODO == "aplicar":
            w.update_title(destino)
            print("   %-22s -> %s" % (w.title, destino))
        else:
            print("   %-22s -> %s   (en seco)" % (w.title, destino))
        total += 1
    print("")

print("pestañas %s: %d" % ("renombradas" if MODO == "aplicar" else "que se renombrarian", total))

if MODO == "aplicar":
    print("\n== VERIFICACION (leyendo de vuelta) ==")
    for nombre, s_id in libros.items():
        t = sorted(w.title for w in gc.open_by_key(s_id).worksheets())
        quedan = [x for x in t if x in NUEVO]
        print("   %-16s %d pestañas · con nombre viejo: %s"
              % (nombre, len(t), quedan or "NINGUNA"))
