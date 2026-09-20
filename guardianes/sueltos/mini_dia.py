"""¿Cabe la barra del Panel en una fila a media pantalla? (v394)

⚠️ Es una RÉPLICA de la barra, no la función real: `render_planificacion` necesita
sesión y Sheets. Lo que se mide aquí es el MECANISMO —gap, pesos, padding del
segmentado y el rango corto— con las mismas piezas y el CSS del kit, y el bloque
forzado a los 406 px que mide la fila en producción a 780 de ventana.
"""
import sys
from datetime import date

sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st

st.session_state.setdefault("auth", {"usuario": "dmoreno", "grupo": "cliente1",
                                     "rol": "administrador"})

from core import roster as R       # noqa: E402
from core import theme             # noqa: E402

theme.inject()

# el bloque, al ancho REAL medido en producción
st.markdown("""
<style>
section[data-testid="stMain"] div.block-container { max-width: 438px !important; }
[class*="st-key-cpxseg_vista"] div[role="radiogroup"] > label { padding: 6px 8px !important; }
</style>""", unsafe_allow_html=True)

LUN = date(2026, 8, 17)
st.caption("réplica de la barra — 406 px útiles")

b1, b2, b3, b4 = st.columns([0.6, 2.3, 0.6, 8.5], gap="xxsmall")
b1.button("◀", key="p", use_container_width=True)
b2.markdown(f"<div style='text-align:center;font-weight:700;font-size:14px;"
            f"padding-top:9px;white-space:nowrap'>"
            f"{R.rango_label(LUN, corto=True)}</div>", unsafe_allow_html=True)
b3.button("▶", key="n", use_container_width=True)
b4.radio("vista", ["📋 Tablero", "🕐 Día", "👀 Disponibilidad"], horizontal=True,
         key="cpxseg_vista", label_visibility="collapsed",
         format_func=lambda o: {
             "📋 Tablero": ":material/calendar_view_week: Semana",
             "🕐 Día": ":material/schedule: Día",
             "👀 Disponibilidad": ":material/event_available: Libres"}.get(o, o))

st.divider()
st.caption("Comparación: la MISMA barra como estaba en v392")
c1, c2, c3, c4 = st.columns([0.7, 2, 0.7, 8.6])
c1.button("◀", key="p2", use_container_width=True)
c2.markdown(f"<div style='text-align:center;font-weight:700;font-size:16px;"
            f"padding-top:6px'>{R.rango_label(LUN)}</div>", unsafe_allow_html=True)
c3.button("▶", key="n2", use_container_width=True)
c4.radio("vista2", ["📋 Tablero", "🕐 Día", "👀 Disponibilidad"], horizontal=True,
         key="cpxseg_vieja", label_visibility="collapsed",
         format_func=lambda o: {
             "📋 Tablero": ":material/calendar_view_week: Semana",
             "🕐 Día": ":material/schedule: Día",
             "👀 Disponibilidad": ":material/event_available: Libres"}.get(o, o))
