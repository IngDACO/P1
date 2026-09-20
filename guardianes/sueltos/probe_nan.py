# -*- coding: utf-8 -*-
"""Que pinta Streamlit en una celda NaN? La pregunta que decide si v485 arreglo algo.

Tres columnas a la vez, para no creerle a una sola lectura (trampa n12):
  NANCOL  -> float("nan") en toda la columna  = el arreglo de v485
  NONECOL -> None en toda la columna          = el fallo (control POSITIVO)
  OKCOL   -> numeros de verdad                = control de que la sonda ve algo

Se pinta con `tabla.cfg()`, igual que la pantalla del parte.
"""
import sys

sys.path.insert(0, "C:/Users/diego/P1/survey_app")

import pandas as pd
import streamlit as st

from core import tabla

st.write("SONDA NAN v485")

filas = [
    {"Nombre": "Ana", "NANCOL": float("nan"), "NONECOL": None, "OKCOL": 7.25},
    {"Nombre": "Beto", "NANCOL": float("nan"), "NONECOL": None, "OKCOL": 3.5},
]
df = pd.DataFrame(filas)
st.write({c: str(df[c].dtype) for c in df.columns})
st.dataframe(df, hide_index=True, width="stretch", column_config=tabla.cfg())
