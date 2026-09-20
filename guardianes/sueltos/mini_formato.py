"""Mini-app: ¿qué PINTA de verdad `NumberColumn(format=...)`?

El DOM no puede responderlo — glide-data-grid pinta en canvas y el nodo accesible
lleva el valor CRUDO (medido en producción: la celda dice `27882.67`). Así que
aquí se dibujan los candidatos y el veredicto se lee interceptando `fillText`.

Los importes son los REALES de la cartera de `cliente1`, para que el veredicto
sea sobre las cifras que el usuario ve, no sobre un 1234.56 de manual.
"""
import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")

VALORES = [0.0, 368.83, 980.0, 2960.0, 3305.76, 27882.67]

# candidato -> lo que ESPERO que pinte (se compara con lo pintado de verdad)
CANDIDATOS = {
    "$%d":    "actual en 20 columnas (TRUNCA)",
    "$%,d":   "el mismo, con coma  -> ¿trunca igual?",
    "$%.2f":  "actual en las de céntimos",
    "$%,.2f": "el mismo, con coma",
}

df = pd.DataFrame({"Valor": VALORES})
for i, f in enumerate(CANDIDATOS):
    df[f"c{i}"] = VALORES

st.dataframe(
    df, hide_index=True, use_container_width=True, key="tabla",
    column_config={
        f"c{i}": st.column_config.NumberColumn(f"c{i}", format=f)
        for i, f in enumerate(CANDIDATOS)
    })

st.caption(" · ".join(f"c{i} = {f!r}" for i, f in enumerate(CANDIDATOS)))

# ⚠️ Varias columnas de dinero son EDITABLES (Cotizaciones, Nóminas, Ganancia/h).
# Que el separador no rompa lo que se TECLEA hay que verlo, no suponerlo.
st.divider()
ed = st.data_editor(
    pd.DataFrame({"Importe": [1500.0, 27882.67]}), key="ed", hide_index=True,
    column_config={"Importe": st.column_config.NumberColumn(
        "Importe", format="$%,.2f", min_value=0.0)})
st.write("DEVUELTO:", [float(v) for v in ed["Importe"]])

