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
BORDE = "#e3e8ef"
FONDO_SUAVE = "#f4f7fb"

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
.cpx-sec {{
  display: flex; align-items: baseline; gap: 9px;
  margin: 14px 0 6px; padding-bottom: 5px; border-bottom: 1px solid {BORDE};
}}
.cpx-sec .t {{ font-size: 1.02rem; font-weight: 700; color: {AZUL_OSC}; }}
.cpx-sec .s {{ font-size: .8rem; color: {GRIS_TXT}; }}
</style>
"""


def inject():
    """Inyecta el CSS del sistema de diseño. Idempotente por sesión."""
    if st.session_state.get("_cpx_theme"):
        return
    st.session_state["_cpx_theme"] = True
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
