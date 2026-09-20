"""Mini-app para MEDIR los anchos de la tabla de `Proyectos · Lista` antes de tocar la app.

⚠️ Se replica el ancho REAL del contenedor medido en producción (`width=1066`, con 1054
visibles). Si midiera en un contenedor más ancho, la tabla cabría siempre y el OK sería
falso — la trampa nº1 del CLAUDE.md.

Los datos son sintéticos A PROPÓSITO pero con los textos MÁS LARGOS del caso real: lo que
se mide aquí es geometría de columnas, y glide dimensiona por contenido + cabecera, así que
lo que decide es el peor caso, no las cifras.
"""
import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")

ANCHO = 1066  # medido en producción: la caja de la tabla en el detalle del admin

FILAS = [
    {"ID": "PRJ-0011", "Proyecto": "Stockland Wetherill Park — Instalación",
     "Sin facturar": 27882.67, "Tipo": "Instalación", "Estado": "En progreso",
     "Avance": 100, "Cliente": "Meriton Property Group", "Inicio": "26/08/26",
     "Fin": "26/08/26", "Ppto": "100% over", "Usuarios": 12,
     "Situación": "12 d adelanto", "Alertas": "12"},
    {"ID": "PRJ-0014", "Proyecto": "Bespoke — Delivery Chullora",
     "Sin facturar": 5200.0, "Tipo": "Delivery", "Estado": "Planificado",
     "Avance": 0, "Cliente": "Bespoke Lifts", "Inicio": "01/09/26",
     "Fin": "15/09/26", "Ppto": "—", "Usuarios": 2,
     "Situación": "6 d retraso", "Alertas": ""},
]

# ── Propuesta A: anchos en px + cabeceras cortas + identidad fijada ────────────
CFG = {
    "ID":            st.column_config.TextColumn("ID", width=78, pinned=True),
    "Proyecto":      st.column_config.TextColumn("Proyecto", width=190, pinned=True),
    "Sin facturar":  st.column_config.NumberColumn("Sin facturar", format="$%,.0f", width=100),
    "Tipo":          st.column_config.TextColumn("Tipo", width=84),
    "Estado":        st.column_config.TextColumn("Estado", width=88),
    "Avance":        st.column_config.ProgressColumn("Avance", min_value=0, max_value=100,
                                                     format="%d%%", width=76),
    "Cliente":       st.column_config.TextColumn("Cliente", width=96),
    "Inicio":        st.column_config.TextColumn("Inicio", width=68),
    "Fin":           st.column_config.TextColumn("Fin", width=64),
    "Ppto":          st.column_config.TextColumn("Ppto", width=70),
    "Usuarios":      st.column_config.NumberColumn("Equipo", width=64),
    "Situación":     st.column_config.TextColumn("Ritmo", width=88),
    "Alertas":       st.column_config.TextColumn("Avisos", width=66),
}

# ── Propuesta A': lo mismo, SIN la columna `Tipo` (ya está como filtro encima de
# la tabla desde v306) y con los anchos apretados un punto más. La medición de A
# dijo 1164 px de contenido para 1054 visibles: 13 columnas no caben, por mucho
# que se recorten. Quitar `Tipo` es lo único que no pierde nada.
CFG2 = {
    "ID":            st.column_config.TextColumn("ID", width=74, pinned=True),
    "Proyecto":      st.column_config.TextColumn("Proyecto", width=180, pinned=True),
    "Sin facturar":  st.column_config.NumberColumn("Sin facturar", format="$%,.0f", width=98),
    "Estado":        st.column_config.TextColumn("Estado", width=84),
    "Avance":        st.column_config.ProgressColumn("Avance", min_value=0, max_value=100,
                                                     format="%d%%", width=74),
    "Cliente":       st.column_config.TextColumn("Cliente", width=94),
    "Inicio":        st.column_config.TextColumn("Inicio", width=64),
    "Fin":           st.column_config.TextColumn("Fin", width=60),
    "Ppto":          st.column_config.TextColumn("Ppto", width=66),
    "Usuarios":      st.column_config.NumberColumn("Equipo", width=62),
    "Situación":     st.column_config.TextColumn("Ritmo", width=84),
    "Alertas":       st.column_config.TextColumn("Avisos", width=64),
}

# ── Propuesta FINAL: no se encoge, se PRIORIZA (la cura de v398) ──────────────
# Medido: con 12-13 columnas y nombres de obra reales, NO hay reparto de anchos que
# quepa en 1054 px sin CORTAR texto (glide recorta por clip, sin elipsis: 9 textos
# quedaban cortados, el nombre de obra y el cliente por 60 px). Así que se deja el
# scroll horizontal y se cambia lo que se ve PRIMERO:
#   · `ID` y `Proyecto` van `pinned` → la identidad no se escapa al desplazarse.
#   · las tres de atención (Sin facturar · Ritmo · Avisos) suben junto al nombre.
#   · el contexto (Cliente, Tipo, fechas, Ppto) queda a la derecha, para quien lo busque.
_W = int(st.query_params.get("w", "248"))
ORDEN = ["ID", "Proyecto", "Sin facturar", "Avance", "Situación", "Alertas",
         "Estado", "Usuarios", "Cliente", "Tipo", "Inicio", "Fin", "Ppto"]
CFG3 = {
    "ID":           st.column_config.TextColumn("ID", width=76, pinned=True),
    "Proyecto":     st.column_config.TextColumn("Proyecto", width=_W, pinned=True),
    "Sin facturar": st.column_config.NumberColumn("Sin facturar", format="$%,.0f", width=104),
    "Avance":       st.column_config.ProgressColumn("Avance", min_value=0, max_value=100,
                                                    format="%d%%", width=78),
    "Situación":    st.column_config.TextColumn("Ritmo", width=100),
    "Alertas":      st.column_config.TextColumn("Avisos", width=70),
    "Estado":       st.column_config.TextColumn("Estado", width=92),
    "Usuarios":     st.column_config.NumberColumn("Equipo", width=70),
}

st.markdown("### propuesta A (13 columnas, solo anchos)")
st.dataframe(pd.DataFrame(FILAS), hide_index=True, width=ANCHO,
             on_select="rerun", selection_mode="single-row", key="prop",
             column_config=CFG)

st.markdown("### propuesta A' (sin `Tipo`) — cabe pero CORTA texto")
st.dataframe(pd.DataFrame(FILAS).drop(columns=["Tipo"]), hide_index=True, width=ANCHO,
             on_select="rerun", selection_mode="single-row", key="prop2",
             column_config=CFG2)

st.markdown("### propuesta FINAL (prioridad + pinned)")
st.dataframe(pd.DataFrame(FILAS)[ORDEN], hide_index=True, width=ANCHO,
             on_select="rerun", selection_mode="single-row", key="prop3",
             column_config=CFG3)

st.markdown("### actual (sin anchos, como está hoy)")
st.dataframe(pd.DataFrame(FILAS), hide_index=True, width=ANCHO,
             on_select="rerun", selection_mode="single-row", key="hoy",
             column_config={
                 "Avance": st.column_config.ProgressColumn("Avance", min_value=0,
                                                           max_value=100, format="%d%%"),
                 "Sin facturar": st.column_config.NumberColumn("Sin facturar",
                                                               format="$%,.0f"),
             })
