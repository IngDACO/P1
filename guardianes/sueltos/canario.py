# -*- coding: utf-8 -*-
"""Canario: renombra UNA hoja intrascendente y mira si la app la recrea.

Si el proceso del Cloud sigue con el codigo viejo, pedira `InvCategorias`, no lo
encontrara y CREARA una pestaña vacia — que es justo el desastre silencioso que
hay que descartar antes de renombrar las 44. Se elige `InvCategorias` porque en
la demo tiene 0 filas de datos: si se recrea, no se pierde nada.
"""
import os, sys
os.chdir(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, os.getcwd())
import streamlit as st
st.session_state["auth"] = {"usuario": "dacox", "rol": "propietario", "grupo": "cliente1"}
import gspread
from google.oauth2.service_account import Credentials
from core import auth

MODO = sys.argv[1]
gc = gspread.authorize(Credentials.from_service_account_info(
    dict(st.secrets["gcp_service_account"]),
    scopes=["https://www.googleapis.com/auth/spreadsheets"]))
sh = gc.open_by_key(auth.group_sheet_id("cliente1"))
tit = {w.title: w for w in sh.worksheets()}

if MODO == "renombrar":
    if "InvCategorias" in tit:
        tit["InvCategorias"].update_title("AssetCategories")
        print("renombrada: InvCategorias -> AssetCategories")
    else:
        print("ya estaba renombrada")
elif MODO == "mirar":
    t = sorted(tit)
    print("AssetCategories presente :", "AssetCategories" in t)
    print("InvCategorias RECREADA   :", "InvCategorias" in t,
          "  <- si es True, el Cloud sigue con el codigo VIEJO")
    print("total pestañas           :", len(t))
elif MODO == "revertir":
    if "AssetCategories" in tit:
        tit["AssetCategories"].update_title("InvCategorias")
        print("revertida")
