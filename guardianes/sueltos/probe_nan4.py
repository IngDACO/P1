# -*- coding: utf-8 -*-
"""La cadena vacia CON un `Column(...)` genérico, que es el caso real.

`tabla.CABECERAS` incluye «Costo» y «Horas», asi que esas columnas SI reciben un
`Column(etiqueta)` de `cfg()`. La sonda 3 probo la cadena vacia en columnas SIN config
ninguna, que no es donde va a vivir. Y se prueba `alignment`, que existe en 1.57.
"""
import sys

sys.path.insert(0, "C:/Users/diego/P1/survey_app")

import pandas as pd
import streamlit as st

from core import tabla

st.write("SONDA NAN 4")
C = st.column_config.Column


def prueba(etq, lleno, vacio, cfg):
    col = "Costo"                      # ESTA en CABECERAS -> cfg() le pone Column()
    df = pd.DataFrame([{"Nombre": "Ana", col: lleno}, {"Nombre": "Beto", col: vacio}])
    st.write(f"{etq} · dtype={df[col].dtype}")
    st.dataframe(df, hide_index=True, width="stretch",
                 column_config=tabla.cfg(None, cfg))


# O = cadena vacia con el Column() genérico que cfg() ya pone (el caso real)
prueba("_O", 12.5, "", None)
# P = igual, pero alineado a la derecha
prueba("_P", 12.5, "", {"Costo": C("Cost P", alignment="right")})
# Q = importe ya formateado en Python + vacia, alineado a la derecha (la propuesta)
prueba("_Q", "$12.50", "", {"Costo": C("Cost Q", alignment="right")})
# R = CONTROL: NaN con el Column() genérico -> debe seguir pintando «None»
prueba("_R", 12.5, float("nan"), None)
