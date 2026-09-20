# -*- coding: utf-8 -*-
"""Una tabla por candidato, UNA sola columna de datos cada una.

Asi cualquier «None» pintado pertenece sin ambiguedad al candidato de esa tabla: no
hay otra columna a la que atribuirlo. Es la leccion de la pasada anterior, donde
sume el agregado y se lo asigne a la columna que esperaba.

Cada tabla: fila con valor (7.25) + fila SIN valor (el candidato). Igual que el parte,
donde casi todos los dias estan vacios y alguno tiene horas.
"""
import sys

sys.path.insert(0, "C:/Users/diego/P1/survey_app")

import pandas as pd
import streamlit as st

from core import tabla

st.write("SONDA NAN 2")

NADA = object()


def prueba(etq, vacio, cfg_extra=None, dtype=None):
    col = "D" + etq          # cabecera corta y unica: D_A, D_B...
    filas = [{"Nombre": "Ana", col: 7.25}, {"Nombre": "Beto", col: vacio}]
    df = pd.DataFrame(filas)
    if dtype:
        df[col] = df[col].astype(dtype)
    st.write(f"{etq} · dtype={df[col].dtype}")
    st.dataframe(df, hide_index=True, width="stretch",
                 column_config=tabla.cfg(extra=cfg_extra))


# A = lo que hace v485 hoy
prueba("_A", float("nan"))
# B = NaN pero declarando la columna como numerica
prueba("_B", float("nan"), {"D_B": st.column_config.NumberColumn("D_B")})
# C = cadena vacia (lo que ya hace el CSV) -> la columna pasa a object
prueba("_C", "")
# D = None con columna numerica declarada
prueba("_D", None, {"D_D": st.column_config.NumberColumn("D_D")})
# E = nulo de pandas con dtype nullable
prueba("_E", pd.NA, None, "Float64")


# ── CONTROLES: ¿es NaN, o es `tabla.cfg()`? Sin control esto no discrimina nada.
def crudo(etq, vacio, cfg):
    col = "D" + etq
    df = pd.DataFrame([{"Nombre": "Ana", col: 7.25}, {"Nombre": "Beto", col: vacio}])
    st.write(f"{etq} · dtype={df[col].dtype} · cfg={cfg!r}")
    if cfg is NADA:
        st.dataframe(df, hide_index=True, width="stretch")
    else:
        st.dataframe(df, hide_index=True, width="stretch", column_config=cfg)


# F = NaN y NINGUN column_config (el control que discrimina)
crudo("_F", float("nan"), NADA)
# G = NaN con column_config vacio
crudo("_G", float("nan"), {})
# H = NaN con formato numerico explicito
crudo("_H", float("nan"), {"D_H": st.column_config.NumberColumn("D_H", format="%.2f")})
