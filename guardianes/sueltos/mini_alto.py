"""Mini-app para acotar la ALTURA de la fila del Panel sin perder información.

Medido en producción a 1440 (el ancho donde vive el admin, no el del panel — el error de
v335 ya me costó dos decisiones hoy):
    filas de 36 a 116 px · tablero 546 px
    la peor fila = botón de 53 px (2 líneas) + NOTA de 61 px
o sea que **la nota ocupa más que la propia celda**. Ese es el objetivo principal.

Se comparan las tres variantes en la misma pantalla para poder medirlas de una pasada.
"""
import streamlit as st

st.set_page_config(layout="wide")

DIAS = ["lun", "mar", "mie", "jue", "vie", "sab"]
LABEL = {"lun": "Lun", "mar": "Mar", "mie": "Mié", "jue": "Jue", "vie": "Vie", "sab": "Sáb"}
# Caso REAL de producción (fila `lksdfkldsf`) + un caso peor a propósito.
FILAS = [
    {"nom": "lksdfkldsf",
     "celdas": {0: ("prueba2", ""),
                1: ("prueba2 7:00–11:00 · prueba 3 11:30–15:30", "cambia de obra a media mañana"),
                2: ("prueba2", ""), 3: ("prueba2", ""), 4: ("prueba2", "")}},
    {"nom": "Caso peor",
     "celdas": {0: ("Meriton Zetland — Torre A 6:30–14:00 · RNSH Lift 4 14:30–18:00",
                    "lleva la furgoneta grande y pasa por el almacén a por los rieles antes"),
                3: ("OFF", "")}},
    {"nom": "Anjali Patel", "celdas": {2: ("prueba2", "nota corta")}},
]

MODO = st.radio("Altura", ["como hoy", "acotada"], horizontal=True, key="modo")

BASE = """
<style>
[class*="st-key-roscel_"] button {
  padding: 4px 7px !important; min-height: 0 !important; border-radius: 7px !important;
  line-height: 1.2 !important;
}
[class*="st-key-roscel_"] button p {
  font-size:12px !important; font-weight: 600 !important;
  text-align: left !important; width: 100%; white-space: normal !important;
}
[class*="st-key-pnm_"] button {
  padding: 4px 8px !important; min-height: 0 !important;
  background: transparent !important; border: none !important;
  border-left: 3px solid #2e6da4 !important; border-radius: 0 !important;
}
[class*="st-key-pnm_"] button p { font-size:13px !important; font-weight:700 !important;
  text-align:left !important; width:100%; color:#1e4e79; }
.st-key-rosgrid [data-testid="stHorizontalBlock"] {
  border-bottom: 1px solid #e6eaf0 !important; padding: 3px 0 !important;
  margin: 0 !important; gap: 0 !important;
}
.st-key-rosgrid [data-testid="stColumn"] {
  border-right: 1px solid #dfe5ec; padding: 0 4px !important;
}
</style>"""
st.markdown(BASE, unsafe_allow_html=True)

# ── La acotación: el label del botón a 2 líneas como mucho ───────────────────
# ⚠️ `-webkit-line-clamp` necesita las TRES: display:-webkit-box, box-orient y overflow.
# Con una sola no recorta y no da ningún error — se ve «casi bien» (v304/v332).
ACOTAR = """
<style>
[class*="st-key-roscel_"] button p {
  display: -webkit-box !important;
  -webkit-line-clamp: 2 !important;
  -webkit-box-orient: vertical !important;
  overflow: hidden !important;
  /* ⚠️ Respaldo: el `<p>` vive dentro de un contenedor flex, así que el navegador
     BLOCKIFICA el `display:-webkit-box` a `flow-root` (medido: la única regla que
     toca `display` es esta, y el computed sale `flow-root`). El clamp sigue
     recortando en Chrome, pero no quiero que la altura del tablero dependa de un
     comportamiento que no controlo: 2 líneas × 1.2 de interlineado × 12px = 28.8px
     lo garantiza en cualquier navegador. */
  max-height: 29px !important;
}
</style>"""
if MODO == "acotada":
    st.markdown(ACOTAR, unsafe_allow_html=True)

anchos = [1.4] + [1] * len(DIAS)
_CAB = "font-size:13px;font-weight:600;color:#5b6472;text-align:center;margin-bottom:6px"

_head = st.container(key="roshead")
h = _head.columns(anchos)
h[0].markdown(f"<div style='{_CAB}'>Persona</div>", unsafe_allow_html=True)
for i, d in enumerate(DIAS):
    h[i + 1].markdown(f"<div style='{_CAB}'>{LABEL[d]} 2{4+i}/08</div>",
                      unsafe_allow_html=True)

_grid = st.container(key="rosgrid")
for pi, f in enumerate(FILAS):
    _row = _grid.container(key=f"rosrow_{pi}")
    cols = _row.columns(anchos)
    cols[0].button(f["nom"], key=f"pnm_{pi}", width="stretch")
    for di in range(len(DIAS)):
        idx = pi * len(DIAS) + di
        et, nota = f["celdas"].get(di, ("", ""))
        col = cols[di + 1]
        with col.popover(et or "＋", key=f"roscel_{idx}", width="stretch"):
            st.caption("editor")
            # Botón con texto LARGO, como los reales del editor («Ver el día»,
            # «→ Meriton Zetland — Torre A»): si el tope de altura le llegara,
            # le cortaría el texto.
            st.button("→ Meriton Zetland — Torre A (abrir el proyecto)",
                      key=f"largo_{idx}", width="stretch")
        if nota:
            if MODO == "acotada":
                # ⚠️ Una línea + elipsis + el texto COMPLETO en el `title` nativo: se
                # acota lo que ocupa, no lo que se puede saber. Y se escapan las
                # comillas además del HTML — `_esc` del módulo NO las escapa, y una
                # comilla en la nota rompería el atributo.
                _t = nota.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                _a = _t.replace('"', "&quot;")
                # HASTA 2 lineas: la nota corta sigue ocupando una, solo la larga
                # paga el alto. `-webkit-line-clamp` pone «...» al final de la 2a.
                # ⚠️ `max-height` de respaldo (2 x 1.3 x 11px = 28.6), por si el
                # navegador blockifica el display dentro de un flex (leccion v412).
                col.markdown(
                    f'<div title="{_a}" style="font-size:11px;color:#6b7280;'
                    f'line-height:1.3;overflow:hidden;padding:0 2px;'
                    f'display:-webkit-box;-webkit-line-clamp:2;'
                    f'-webkit-box-orient:vertical;max-height:29px">{_t}</div>',
                    unsafe_allow_html=True)
            else:
                col.caption(nota)
