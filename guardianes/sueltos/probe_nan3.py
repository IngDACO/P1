# -*- coding: utf-8 -*-
"""Que se pone en una celda que debe salir VACIA en una columna con formato de dinero.

Las tablas afectadas (`payroll_ui` Rate/h, `inventory_ui` Costo) declaran
`NumberColumn(format="$%,.2f")`, asi que la respuesta de la sonda 2 (cadena vacia) hay
que probarla CON ese formato, no sin el. Una tabla por candidato, una sola columna de
datos, para poder atribuir sin sumar agregados.
"""
import sys

sys.path.insert(0, "C:/Users/diego/P1/survey_app")

import pandas as pd
import streamlit as st

from core import tabla

st.write("SONDA NAN 3")


def prueba(etq, vacio, cfg, styler=False):
    col = "D" + etq
    df = pd.DataFrame([{"Nombre": "Ana", col: 12.5}, {"Nombre": "Beto", col: vacio}])
    st.write(f"{etq} · dtype={df[col].dtype}")
    dato = df.style.format({col: "{:.2f}"}, na_rep="") if styler else df
    st.dataframe(dato, hide_index=True, width="stretch",
                 column_config=tabla.cfg(None, cfg) if cfg else tabla.cfg())


M = st.column_config.NumberColumn
# I = cadena vacia CON formato de dinero (la respuesta de la sonda 2, en su sitio real)
prueba("_I", "", {"D_I": M("D_I", format="$%,.2f")})
# J = cadena vacia con NumberColumn sin formato
prueba("_J", "", {"D_J": M("D_J")})
# K = NaN con TextColumn
prueba("_K", float("nan"), {"D_K": st.column_config.TextColumn("D_K")})
# L = ya formateado en Python, texto puro
prueba("_L", "", None)
# N = NaN + Styler con na_rep="" (la via canonica de pandas)
prueba("_N", float("nan"), None, styler=True)
