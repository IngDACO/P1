"""¿`st.dataframe` (glide) dibuja «…» cuando el texto no cabe, o corta en seco?

De esto depende la decisión sobre la columna `Proyecto` de la cartera: hoy el nombre más
largo deja **8 px** de margen. Si glide pone elipsis, un nombre más largo se vería
cortado PERO SE NOTARÍA. Si corta en seco, el usuario lee un nombre a medias sin saberlo
— y ahí sí hay que garantizar el ancho.

⚠️ En v408 concluí «recorta por clip, sin elipsis» a partir de que el hook de `fillText`
recibía el texto ENTERO. Eso prueba lo que se le PASA a fillText, no lo que se ve: glide
podría estar recortando la cadena antes en otra ruta, o el canvas recortando por clip.
Aquí se mide lo que de verdad se pinta.
"""
import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")

LARGO = "Stockland Wetherill Park — Instalación y puesta en marcha fase 2"
FILAS = [
    {"Proyecto": LARGO, "Sin facturar": 27882.67},
    {"Proyecto": "Meriton Zetland — Torre A", "Sin facturar": 5200.0},
]

st.markdown("### columna ESTRECHA (120 px): ¿aparece «…»?")
st.dataframe(pd.DataFrame(FILAS), hide_index=True, width=600, key="t1",
             column_config={
                 "Proyecto": st.column_config.TextColumn("Proyecto", width=120),
                 "Sin facturar": st.column_config.NumberColumn(format="$%,.0f", width=104),
             })

st.markdown("### columna como en la app (248 px)")
st.dataframe(pd.DataFrame(FILAS), hide_index=True, width=600, key="t2",
             column_config={
                 "Proyecto": st.column_config.TextColumn("Proyecto", width=248),
                 "Sin facturar": st.column_config.NumberColumn(format="$%,.0f", width=104),
             })
