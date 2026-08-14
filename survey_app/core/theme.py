"""
Sistema de diseño COPEX (v283) — la capa de estilo compartida por toda la app.

Por qué existe: la app es un PRODUCTO que se vende, así que lo que decide la
primera impresión es la **coherencia** (misma tarjeta, mismo chip, mismos colores
en todas las pantallas), no una pantalla suelta bonita.

Dos capas, a propósito:
1. **Tema oficial** (`.streamlit/config.toml [theme]`) = color de marca, fondos y
   tipografía. Es API soportada de Streamlit → estable entre versiones.
2. **Este módulo** = lo que el tema NO cubre: densidad, tarjetas KPI, chips,
   cabeceras de sección. El CSS a medida es más frágil, así que se mantiene
   ACOTADO y en UN solo sitio (si una versión de Streamlit lo rompe, se arregla
   aquí y no en 20 pantallas).

Uso: `theme.inject()` una vez por página (idempotente por sesión) y luego los
helpers `kpi_row`, `chip`, `section`.
"""
import streamlit as st

# ── Paleta COPEX (los colores que la app YA usa en diagramas y estados) ──
AZUL = "#2e6da4"        # marca / primario
AZUL_OSC = "#1e4e79"    # activo / titulares
ROJO = "#c0392b"        # fuera de límite, retraso, alarma
VERDE = "#1e8449"       # correcto, adelanto
AMBAR = "#e67e22"       # al límite, por vencer
GRIS_TXT = "#5b6472"    # texto secundario
GRIS_SUAVE = "#9aa7b8"  # texto terciario (porcentajes, pies)
TXT = "#1f2937"         # texto principal
PISTA = "#eef1f5"       # fondo de barra/pista
BORDE = "#e3e8ef"
FONDO_SUAVE = "#f4f7fb"

# Paleta CATEGÓRICA (torta de rubros, series): arranca en el azul de marca y
# alterna tonos distinguibles. Única fuente — no redefinir paletas por módulo.
PALETA = ["#2e6da4", "#BA7517", "#1e8449", "#8e44ad", "#c0392b", "#16a085",
          "#e67e22", "#2980b9", "#d4537e", "#7f8c8d", "#f1c40f", "#34495e"]

_CSS = f"""
<style>
/* ── Densidad: la app maneja mucha información; menos aire = más profesional ── */
div.block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1400px; }}
div[data-testid="stVerticalBlock"] {{ gap: 0.6rem; }}
h1 {{ font-size: 1.7rem !important; font-weight: 700; letter-spacing: -.4px; }}
h2 {{ font-size: 1.32rem !important; font-weight: 700; letter-spacing: -.3px; }}
h3 {{ font-size: 1.12rem !important; font-weight: 650; }}
h4 {{ font-size: 1rem !important; font-weight: 650; color: {AZUL_OSC}; }}

/* ── Métricas nativas como TARJETA (no números flotando) ── */
div[data-testid="stMetric"] {{
  background: #fff; border: 1px solid {BORDE}; border-radius: 12px;
  padding: 12px 14px; box-shadow: 0 1px 2px rgba(16,24,40,.04);
}}
div[data-testid="stMetricLabel"] p {{
  font-size: .74rem !important; font-weight: 600; letter-spacing: .3px;
  text-transform: uppercase; color: {GRIS_TXT};
}}
div[data-testid="stMetricValue"] {{ font-size: 1.6rem; font-weight: 700; color: {AZUL_OSC}; }}

/* ── Contenedores con borde: tarjetas de verdad ── */
div[data-testid="stVerticalBlockBorderWrapper"] {{
  border-radius: 12px; border-color: {BORDE};
  box-shadow: 0 1px 2px rgba(16,24,40,.04);
}}

/* ── Botones: menos "botón de formulario", más control de producto ── */
div[data-testid="stButton"] > button,
div[data-testid="stFormSubmitButton"] > button,
div[data-testid="stDownloadButton"] > button {{
  border-radius: 9px; font-weight: 600; border-color: {BORDE};
  transition: border-color .12s ease, background .12s ease;
}}
div[data-testid="stButton"] > button:hover {{ border-color: {AZUL}; color: {AZUL}; }}

/* ── Expander: cabecera legible, sin caja pesada ── */
div[data-testid="stExpander"] details {{ border-radius: 10px; border-color: {BORDE}; }}
div[data-testid="stExpander"] summary p {{ font-weight: 600; }}

/* ── Tabs de datos / tablas: encabezado sobrio ── */
div[data-testid="stDataFrame"] {{ border-radius: 10px; }}

/* ── Sidebar: superficie de marca ── */
section[data-testid="stSidebar"] {{ border-right: 1px solid {BORDE}; }}

/* ── Cabecera de Streamlit transparente (evita la franja oscura arriba) ── */
header[data-testid="stHeader"] {{ background: transparent; }}

/* ── Piezas del kit (kpi_row / chip / section) ── */
.cpx-kpis {{ display: flex; gap: 10px; flex-wrap: wrap; margin: 2px 0 12px; }}
.cpx-kpi {{
  flex: 1 1 150px; background: #fff; border: 1px solid {BORDE};
  border-left: 3px solid var(--cpx-accent, {AZUL}); border-radius: 12px;
  padding: 10px 13px; box-shadow: 0 1px 2px rgba(16,24,40,.04);
}}
.cpx-kpi .lbl {{
  font-size: .72rem; font-weight: 600; letter-spacing: .3px;
  text-transform: uppercase; color: {GRIS_TXT}; margin-bottom: 2px;
}}
.cpx-kpi .val {{ font-size: 1.5rem; font-weight: 700; color: {AZUL_OSC}; line-height: 1.15; }}
.cpx-kpi .sub {{ font-size: .76rem; color: {GRIS_TXT}; margin-top: 1px; }}
.cpx-chip {{
  display: inline-block; padding: 2px 9px; border-radius: 999px;
  font-size: .76rem; font-weight: 600; line-height: 1.5;
}}

/* ── KPI CLICKEABLE: un botón con key `cpxkpi_*` se ve como tarjeta KPI ──
   (el principio del usuario: nada pasivo — la métrica lleva a su sección).
   Usa la clase `st-key-<key>` que Streamlit pone en el contenedor del widget. */
[class*="st-key-cpxkpi_"] button {{
  background: #fff !important; border: 1px solid {BORDE} !important;
  border-left: 3px solid {AZUL} !important; border-radius: 12px !important;
  padding: 12px 14px !important; min-height: 64px;
  box-shadow: 0 1px 2px rgba(16,24,40,.04);
  justify-content: flex-start !important;
}}
[class*="st-key-cpxkpi_"] button:hover {{
  border-color: {AZUL} !important; box-shadow: 0 2px 8px rgba(46,109,164,.13);
}}
[class*="st-key-cpxkpi_"] button p {{
  text-align: left !important; width: 100%;
  font-size: 1.02rem !important; font-weight: 700 !important; color: {AZUL_OSC};
}}
/* Tarjeta KPI de TRES líneas (v303): el label del botón va como
   `etiqueta\n\nvalor\n\ncontexto` y Streamlit lo renderiza como TRES <p>.
   ⚠️ VERIFICADO EN VIVO antes de escribir esto (mini-app + medición del DOM):
   `\n\n` da <p> separados; `  \n` da UN <p> con <br> dentro (no sirve, no se
   pueden estilar por separado) y `\n` simple también colapsa en uno.
   Espeja `.cpx-kpi .lbl/.val/.sub` de arriba para que la tarjeta clickeable y la
   pasiva se vean IGUAL. Los `:not(...)` dejan intacta la tarjeta de una sola
   línea: sin ellos, un botón KPI de un solo <p> se encogería a .72rem. */
[class*="st-key-cpxkpi_"] button p:first-child:not(:last-child) {{
  font-size: .72rem !important; font-weight: 600 !important; letter-spacing: .3px;
  text-transform: uppercase; color: {GRIS_TXT} !important; margin-bottom: 1px !important;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
[class*="st-key-cpxkpi_"] button p:nth-child(2):not(:last-child) {{
  font-size: 1.5rem !important; font-weight: 700 !important; color: {AZUL_OSC} !important;
  line-height: 1.15 !important; margin: 0 !important;
}}
/* ⚠️ `nowrap` + elipsis NO es cosmético: es lo que garantiza que las 3 tarjetas de
   una fila midan LO MISMO. Sin él, un pie de 94 px en los 93 px útiles que hay
   dentro de la columna del mapa salta a 2 líneas y esa tarjeta crece 20 px — pasó,
   medido. Con esto, un texto que no quepa se recorta con "…" en vez de descuadrar
   la fila. Aun así los pies se escriben cortos (ver `render_kpis`). */
[class*="st-key-cpxkpi_"] button p:last-child:not(:first-child) {{
  font-size: .76rem !important; font-weight: 500 !important; color: {GRIS_TXT} !important;
  margin-top: 1px !important;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
/* ── TOGGLE SEGMENTADO: un `st.radio(horizontal=True)` con key `cpxseg_*` se ve
   como un control segmentado, no como dos bolitas sueltas (v292).
   ⚠️ Verificado EN VIVO antes de escribirlo (mini-app + medición del DOM):
   la bolita queda `display:none`, el elegido sale `rgb(232,238,246)` y el otro
   transparente. El bloque va dentro de `@supports selector(:has())` A PROPÓSITO:
   sin `:has()` no se podría resaltar el elegido y, con la bolita oculta, no
   habría NINGUNA marca de cuál está activo — así degrada al radio de siempre. */
[class*="st-key-cpxseg_"] div[role="radiogroup"] {{
  gap: 0 !important; display: inline-flex !important; background: #fff;
  border: 1px solid {BORDE}; border-radius: 9px; overflow: hidden;
}}
[class*="st-key-cpxseg_"] div[role="radiogroup"] > label {{
  margin: 0 !important; padding: 6px 14px !important; border-radius: 0 !important;
  border-right: 1px solid {BORDE};
}}
[class*="st-key-cpxseg_"] div[role="radiogroup"] > label:last-child {{ border-right: none; }}
[class*="st-key-cpxseg_"] div[role="radiogroup"] > label:hover {{ background: {FONDO_SUAVE}; }}
@supports selector(label:has(input:checked)) {{
  [class*="st-key-cpxseg_"] div[role="radiogroup"] > label > div:first-child {{
    display: none !important;
  }}
  [class*="st-key-cpxseg_"] div[role="radiogroup"] > label:has(input:checked) {{
    background: #e8eef6 !important;
  }}
  [class*="st-key-cpxseg_"] div[role="radiogroup"] > label:has(input:checked) p {{
    color: {AZUL_OSC} !important; font-weight: 700 !important;
  }}
}}

.cpx-sec {{
  display: flex; align-items: baseline; gap: 9px;
  margin: 14px 0 6px; padding-bottom: 5px; border-bottom: 1px solid {BORDE};
}}
.cpx-sec .t {{ font-size: 1.02rem; font-weight: 700; color: {AZUL_OSC}; }}
.cpx-sec .s {{ font-size: .8rem; color: {GRIS_TXT}; }}
</style>
"""


def inject():
    """Inyecta el CSS del sistema de diseño.

    ⚠️ SE EMITE EN CADA RUN, a propósito. Streamlit **reconstruye el DOM en cada
    rerun**: un elemento que no se vuelve a emitir DESAPARECE. La v283 lo guardaba
    con un flag en `session_state` ("idempotente por sesión") y el resultado fue que
    el estilo solo existía en el primer run — las tarjetas KPI salían como texto
    plano en cuanto había cualquier interacción. Evidencia: el CSS de densidad del
    tablero (emitido sin guarda) sí se aplicaba. **No volver a poner una guarda aquí.**
    """
    st.markdown(_CSS, unsafe_allow_html=True)


def _esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def kpi_row(items):
    """Fila de tarjetas KPI. `items` = [(label, valor)] o [(label, valor, sub)] o
    [(label, valor, sub, color_acento)]. Una sola fila responsive."""
    if not items:
        return
    out = []
    for it in items:
        lbl, val = it[0], it[1]
        sub = it[2] if len(it) > 2 else ""
        acc = it[3] if len(it) > 3 else AZUL
        out.append(
            f'<div class="cpx-kpi" style="--cpx-accent:{acc}">'
            f'<div class="lbl">{_esc(lbl)}</div>'
            f'<div class="val">{_esc(val)}</div>'
            + (f'<div class="sub">{_esc(sub)}</div>' if sub else "")
            + "</div>")
    st.markdown('<div class="cpx-kpis">' + "".join(out) + "</div>",
                unsafe_allow_html=True)


def chip(texto, color=AZUL) -> str:
    """Chip/píldora coloreada (devuelve HTML para componer en un markdown)."""
    return (f'<span class="cpx-chip" style="background:{color}1a;color:{color};">'
            f'{_esc(texto)}</span>')


def section(titulo, sub=""):
    """Cabecera de sección con línea — separa bloques sin gritar."""
    st.markdown(
        f'<div class="cpx-sec"><span class="t">{_esc(titulo)}</span>'
        + (f'<span class="s">{_esc(sub)}</span>' if sub else "")
        + "</div>", unsafe_allow_html=True)
