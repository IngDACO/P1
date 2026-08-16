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
GRIS_TXT = "#5b6472"    # texto secundario · 5.98:1 sobre blanco
# ⚠️ v326: era #9aa7b8, que da **2.27:1** sobre el fondo suave — la MITAD del
# mínimo WCAG AA (4.5:1). Se usa en los indicadores en reposo, que es el estado
# que más se ve, y esta app se abre EN OBRA con sol. #667080 mantiene la jerarquía
# de tres niveles (principal → secundario → terciario) y pasa en los tres fondos:
# blanco 5.01 · #f4f7fb 4.66 · #f7fafd 4.78. Medido, no estimado.
GRIS_SUAVE = "#667080"  # texto terciario (porcentajes, pies)
AMBAR_TXT = "#8a5600"   # ámbar cuando es TEXTO · 5.65:1 sobre #fff4e0 (era #c77700, 3.18)
TXT = "#1f2937"         # texto principal
PISTA = "#eef1f5"       # fondo de barra/pista
BORDE = "#e3e8ef"
FONDO_SUAVE = "#f4f7fb"


# ── Un color de ACENTO no siempre sirve como color de TEXTO ──────────────
# ⚠️ v328: `_kpi_card(label, valor, color)` tiñe con el mismo color el borde de
# acento Y el valor. Pasarle AMBAR (#e67e22) daba un importe a **2.85:1** sobre
# blanco — el KPI «Por facturar» de Rentabilidad. El acento vivo está bien en un
# borde de 3 px (no es texto); como texto hay que oscurecerlo.
# Se resuelve AQUÍ y no en cada llamada: hay ~20 tarjetas repartidas por la app y
# la siguiente que alguien escriba tiene que salir accesible sin acordarse.
_TEXTO_SEGURO = {AMBAR: AMBAR_TXT}


def texto_seguro(color: str) -> str:
    """El equivalente legible de un color de acento, para usarlo como TEXTO."""
    return _TEXTO_SEGURO.get(color, color) if color else color


# Paleta CATEGÓRICA (torta de rubros, series): arranca en el azul de marca y
# alterna tonos distinguibles. Única fuente — no redefinir paletas por módulo.
PALETA = ["#2e6da4", "#BA7517", "#1e8449", "#8e44ad", "#c0392b", "#16a085",
          "#e67e22", "#2980b9", "#d4537e", "#7f8c8d", "#f1c40f", "#34495e"]

_CSS = f"""
<style>
/* ── Densidad: la app maneja mucha información; menos aire = más profesional ── */
/* ⚠️ v326: el lateral NUNCA se había fijado, así que heredaba los 5rem (80 px por
   lado) de fábrica de Streamlit: **160 px regalados** en cada pantalla, el 14 % del
   ancho útil. Se notaba en HOME, donde las 3 columnas caían a 345/248/248 px sobre
   una pantalla de 1440. A 2rem se recuperan 96 px para TODAS las pantallas. */
div.block-container {{
  padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1400px;
  padding-left: 2rem; padding-right: 2rem;
}}
@media (max-width: 640px) {{
  div.block-container {{ padding-left: 1rem; padding-right: 1rem; }}
}}
[data-testid="stVerticalBlock"] {{ gap: 0.6rem; }}
h1 {{ font-size: 1.7rem !important; font-weight: 700; letter-spacing: -.4px; }}
h2 {{ font-size: 1.32rem !important; font-weight: 700; letter-spacing: -.3px; }}
h3 {{ font-size: 1.12rem !important; font-weight: 650; }}
h4 {{ font-size: 1rem !important; font-weight: 650; color: {AZUL_OSC}; }}

/* ── Métricas nativas como TARJETA (no números flotando) ── */
[data-testid="stMetric"] {{
  background: #fff; border: 1px solid {BORDE}; border-radius: 12px;
  padding: 12px 14px; box-shadow: 0 1px 2px rgba(16,24,40,.04);
}}
[data-testid="stMetricLabel"] p {{
  font-size: .74rem !important; font-weight: 600; letter-spacing: .3px;
  text-transform: uppercase; color: {GRIS_TXT};
}}
[data-testid="stMetricValue"] {{ font-size: 1.6rem; font-weight: 700; color: {AZUL_OSC}; }}

/* ── Contenedores con borde: tarjetas de verdad ── */
[data-testid="stVerticalBlockBorderWrapper"] {{
  border-radius: 12px; border-color: {BORDE};
  box-shadow: 0 1px 2px rgba(16,24,40,.04);
}}

/* ── Botones: menos "botón de formulario", más control de producto ──
   ⚠️ v326: estos selectores usaban el combinador HIJO (`>`). Cuando un botón lleva
   `help=`, Streamlit lo envuelve en `stTooltipHoverTarget`, así que deja de ser hijo
   directo y **el estilo del kit no le llegaba**. Medido en producción: 10 de 25
   botones visibles (**40 %**) se quedaban sin radio, sin peso, sin hover y sin el
   acuse de recibo — incluidos el ← de la barra y todos los indicadores. Descendiente,
   no hijo. */
[data-testid="stButton"] button,
[data-testid="stFormSubmitButton"] button,
[data-testid="stDownloadButton"] button {{
  border-radius: 9px; font-weight: 600; border-color: {BORDE};
  min-height: 38px;            /* v326: eran 32 px — corto para ratón, imposible con el dedo */
  transition: border-color .14s ease, background .14s ease,
              transform .09s ease-out, box-shadow .14s ease;
}}
[data-testid="stButton"] button:hover {{
  border-color: {AZUL}; color: {AZUL};
  box-shadow: 0 2px 8px -2px rgba(46,109,164,.28);
}}

/* ── ACUSE DE RECIBO (v326) ──────────────────────────────────────────────
   El fallo de sensación más caro de la app: una navegación tarda hasta 2,9 s y
   NADA respondía al clic — se pulsaba y no pasaba absolutamente nada, así que el
   usuario vuelve a pulsar y entonces sí parece rota. Esto NO acelera el rerun:
   confirma que se recibió, que es lo que separa "no funcionó" de "está
   trabajando". Ocurre en el navegador, antes de que el servidor conteste. */
[data-testid="stButton"] button:active,
[data-testid="stFormSubmitButton"] button:active,
[data-testid="stDownloadButton"] button:active {{
  transform: scale(.985); opacity: .72; transition: transform .09s ease-out;
}}

/* ── ESTADO DE CARGA (v332) ──────────────────────────────────────────────
   ⚠️ La regla de v326 apuntaba a `[data-testid="stMain"]` y **stMain es un
   `<section>`**, así que NO casaba con nada: el atenuado nunca llegó a verse. Mismo
   error que el combinador `>` de v327 — un selector supuesto en vez de medido. Sin
   nombre de etiqueta, que además es más robusto si Streamlit lo cambia.

   Dos señales, porque resuelven cosas distintas: la BARRA dice «te he oído y estoy
   trabajando» (aparece al instante, en el navegador) y el ATENUADO dice «lo que ves
   ya no es lo definitivo». Sin ellas, hasta 2,9 s de pantalla idéntica y quieta. */
[data-testid="stMain"] {{ transition: opacity .2s ease; }}
body:has([data-testid="stStatusWidget"]) [data-testid="stMain"] {{ opacity: .55; }}

body::before {{
  content: ""; position: fixed; inset: 0 0 auto 0; height: 3px; z-index: 9999;
  pointer-events: none; opacity: 0; transition: opacity .15s ease;
  background: linear-gradient(90deg, transparent, {AZUL} 45%, {AZUL_OSC} 55%, transparent);
  background-size: 42% 100%; background-repeat: no-repeat;
}}
body:has([data-testid="stStatusWidget"])::before {{
  opacity: 1; animation: cpx-cargando 1.05s ease-in-out infinite;
}}
@keyframes cpx-cargando {{
  from {{ background-position: -42% 0; }}
  to   {{ background-position: 142% 0; }}
}}

/* ⚠️ Respeta a quien pide menos movimiento (y a quien se marea con él). */
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{
    animation-duration: .001ms !important; transition-duration: .001ms !important;
  }}
}}

/* ── Expander: cabecera legible, sin caja pesada ── */
[data-testid="stExpander"] details {{ border-radius: 10px; border-color: {BORDE}; }}
[data-testid="stExpander"] summary p {{ font-weight: 600; }}

/* ── Tabs de datos / tablas: encabezado sobrio ── */
[data-testid="stDataFrame"] {{ border-radius: 10px; }}

/* ── Sidebar: superficie de marca ── */
[data-testid="stSidebar"] {{ border-right: 1px solid {BORDE}; }}

/* ── Cabecera de Streamlit transparente (evita la franja oscura arriba) ── */
[data-testid="stHeader"] {{ background: transparent; }}

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
    """Escapa texto para meterlo en HTML.

    ⚠️ v312: además DESHACE el escape de markdown `\\$`. `dinero()` devuelve `\\$1.234`
    porque en markdown dos `$` sueltos se interpretan como LaTeX — pero en HTML la
    barra no es un escape, es un carácter, y salía en pantalla: la tarjeta de Gastos
    mostraba literalmente `\\$3,145`. Como TODAS las piezas HTML del kit pasan por aquí
    (`kpi_row`, `_kpi_card`, `chip`…), esto lo arregla en el único sitio donde importa
    y hace imposible volver a cometer el error pasando el importe equivocado.
    """
    return (str(s).replace("\\$", "$")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def dinero(valor, dec: int = 2, simbolo: str = "$") -> str:
    """Importe formateado y **seguro para `st.markdown` / `st.metric`** (v309).

    ⚠️ Streamlit trata lo que hay entre dos `$` de una misma cadena como **LaTeX**.
    Medido en vivo con las cadenas reales de la app:
      - `"Subtotal **$3,145.20** · Impuesto **$314.52**"` → se renderiza como una
        FÓRMULA ilegible (el DOM trae KaTeX de verdad).
      - `"**$0.00** · pagado $1,287"` → los `$` **desaparecen** y los `**` salen
        literales, que es lo que se veía en el P&L.
      - `st.metric("Cobrado", "$3,145 de $3,145")` → muestra `3,145 de 3,145`,
        sin símbolo de moneda.
    Con `\\$` los cuatro casos salen bien, y **con una sola cifra el escape es
    inofensivo** (verificado), así que se escapa SIEMPRE en vez de contar dólares.

    Por eso el formato de importes vive en UN sitio: cada vez que alguien escriba
    `f"${x:,.2f}"` a mano el fallo vuelve, y vuelve en las pantallas de dinero.
    """
    try:
        v = float(valor or 0)
    except (TypeError, ValueError):
        v = 0.0
    return f"\\{simbolo}{v:,.{dec}f}"


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
