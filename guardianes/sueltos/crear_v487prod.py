# -*- coding: utf-8 -*-
"""Siembra en cliente1 lo que ejercita v487 en PRODUCCION.

  A: categoria que NO esta en la lista («ZZ Categoria borrada») y estado disponible.
  B: estado «in use».
Con el inventario vacio, las KPIs tienen que dar Available=1 · In use=1 (antes: 0 · 0).
Y al pulsar «Save changes» en A sin tocar nada, la categoria tiene que SEGUIR igual.
"""
import io
import json
import os
import sys

os.chdir("C:/Users/diego/P1/survey_app")
sys.path.insert(0, ".")
import streamlit as st  # noqa: E402

GRUPO = "cliente1"
st.session_state["auth"] = {"usuario": "zzprueba", "rol": "administrator",
                            "nombre": "ZZ Prueba", "grupo": GRUPO}
from core import inventory as INV  # noqa: E402

AQUI = r"C:\Users\diego\AppData\Local\Temp\claude\C--Users-diego\1734b676-4bc1-41b7-b6b7-689294f44640\scratchpad"
creado = {"Assets": [], "AssetMovements": []}

ok, a = INV.create_activo(GRUPO, "ZZ PRUEBA v487 A", categoria="ZZ Categoria borrada",
                         marca="Hilti", valor_compra=900, vida_util=5,
                         fecha_compra="2025-03-01", creado_por="zzprueba")
print("A:", ok, a)
creado["Assets"].append(a)
ok, b = INV.create_activo(GRUPO, "ZZ PRUEBA v487 B", categoria="Tool",
                         valor_compra=500, vida_util=5, fecha_compra="2025-03-01",
                         creado_por="zzprueba")
print("B:", ok, b)
creado["Assets"].append(b)
print("B -> in use:", INV.update_activo(b, {"Status": INV.EN_USO}))
INV._invalidate()
print("resumen local:", INV.resumen(GRUPO)["por_estado"])
with io.open(os.path.join(AQUI, "creado_v487prod.json"), "w", encoding="utf-8") as f:
    json.dump(creado, f, indent=1)
print("CREADO:", creado)
