# -*- coding: utf-8 -*-
"""Renombra la FILA 1 (cabeceras) de las hojas de los dos libros, al ingles.

  python renombrar_columnas_hoja.py seco
  python renombrar_columnas_hoja.py aplicar

⚠️ ORDEN OBLIGATORIO: primero el proceso del Cloud tiene que estar corriendo v468.
Con el codigo viejo, cada `.get("Estado")` devolveria "" **y** la migracion de
cabecera de `get_sheet` intentaria reescribir la fila 1 para "restaurar" las columnas
que cree que faltan — eso si es daño, no solo pantallas vacias.

⚠️ Solo se toca la FILA 1. Las posiciones no se mueven, asi que las escrituras
posicionales siguen cayendo donde deben con el libro en cualquiera de los dos estados.
"""
import os
import sys

os.chdir(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, os.getcwd())
import streamlit as st
st.session_state["auth"] = {"usuario": "dacox", "rol": "propietario", "grupo": "cliente1"}

import gspread
from google.oauth2.service_account import Credentials
from core import auth
from core.columnas import LEGADO

MODO = sys.argv[1] if len(sys.argv) > 1 else "seco"
ALCANCE = ["https://www.googleapis.com/auth/spreadsheets"] if MODO == "aplicar" \
    else ["https://www.googleapis.com/auth/spreadsheets.readonly"]
gc = gspread.authorize(Credentials.from_service_account_info(
    dict(st.secrets["gcp_service_account"]), scopes=ALCANCE))

libros = {"MAESTRO": st.secrets["TIMECLOCK_SHEET_ID"]}
sid = auth.group_sheet_id("cliente1")
if sid and sid != libros["MAESTRO"]:
    libros["DEMO (cliente1)"] = sid

tot_celdas = 0
for nombre, s_id in libros.items():
    sh = gc.open_by_key(s_id)
    print("── %s" % nombre)
    for w in sh.worksheets():
        try:
            cab = w.row_values(1)
        except Exception as e:
            print("   %-20s no se pudo leer: %s" % (w.title, e)); continue
        if not cab:
            continue
        nueva = [LEGADO.get(c, c) for c in cab]
        if nueva == cab:
            continue
        cambian = sum(1 for a, b in zip(cab, nueva) if a != b)
        if MODO == "aplicar":
            # ⚠️ UNA escritura por hoja (rango A1:<ultima>1). Celda a celda serian
            # cientos de llamadas contra el techo de 60/min (regla v80).
            w.update([nueva], "A1:%s1" % gspread.utils.rowcol_to_a1(1, len(nueva))[:-1])
            print("   %-20s %d cabeceras renombradas" % (w.title, cambian))
        else:
            muestra = ", ".join("%s→%s" % (a, b) for a, b in zip(cab, nueva) if a != b)
            print("   %-20s %d: %s" % (w.title, cambian, muestra[:80]))
        tot_celdas += cambian
    print("")

print("celdas de cabecera %s: %d"
      % ("renombradas" if MODO == "aplicar" else "que se renombrarian", tot_celdas))

if MODO == "aplicar":
    print("\n== VERIFICACION (leyendo de vuelta) ==")
    for nombre, s_id in libros.items():
        quedan = []
        for w in gc.open_by_key(s_id).worksheets():
            try:
                quedan += [c for c in w.row_values(1) if c in LEGADO]
            except Exception:
                pass
        print("   %-16s cabeceras con nombre viejo: %s" % (nombre, sorted(set(quedan)) or "NINGUNA"))
