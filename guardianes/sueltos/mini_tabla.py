# -*- coding: utf-8 -*-
"""¿Un `Column(label)` puede REACTIVAR una columna que `disabled=[…]` bloqueó?

Es el único riesgo del arreglo de v450 que no se había medido: `_miembros_editor` y
la tabla de avance del campo bloquean columnas por nombre, y si la configuración las
volviera editables se podría escribir donde no se debe — un fallo silencioso.
"""
import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")

FILAS = [{"Proyecto": "Meriton Zetland", "Peso": 1.0, "Avance %": 46},
         {"Proyecto": "Stockland", "Peso": 2.0, "Avance %": 100}]

st.markdown("### disabled=['Proyecto'] + Column('Project')")
_ed = st.data_editor(
    pd.DataFrame(FILAS), hide_index=True, width="stretch", num_rows="fixed",
    key="ed1", disabled=["Proyecto", "Avance %"],
    column_config={"Proyecto": st.column_config.Column("Project"),
                   "Peso": st.column_config.Column("Weight"),
                   "Avance %": st.column_config.Column("Progress %")})
st.text("columnas: " + " | ".join(str(c) for c in _ed.columns))
