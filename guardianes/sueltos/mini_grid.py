"""Mini-app para VERIFICAR la rejilla + zebra + columna de HOY del Panel.

⚠️ Replica la estructura de `roster_ui._tablero_editable`. Lo que se mide es el MECANISMO
CSS, no los datos. Motivo de medir en vez de escribir y desplegar: v304, v332 y v283 —
un selector que no casa NO da error, la app se ve «casi bien» y nadie lo nota.

Medido antes en producción y aprovechado aquí:
  · los hijos de una fila son TODOS `stColumn` → `nth-child(N)` es fiable para «hoy».
  · los hijos del grid son `stLayoutWrapper` → NO se usa `nth-child` sobre ellos para la
    zebra (wrapper reciente, se rompe en silencio si Streamlit mete otro nivel, v327):
    la zebra va por contenedor-por-fila con su propia key, que es el patrón que el
    módulo ya usa para el color de cada celda.
"""
import streamlit as st

st.set_page_config(layout="wide")

DIAS = ["lun", "mar", "mie", "jue", "vie", "sab"]
LABEL = {"lun": "Lun", "mar": "Mar", "mie": "Mié", "jue": "Jue", "vie": "Vie", "sab": "Sáb"}
STAFF = ["Diego Moreno", "Ana Ruiz", "Beto Sánchez", "Mei Chen", "Carlos Pérez",
         "Luis Ortega", "Sara Ibáñez", "Tom Willis"]
COLOR = {0: "#2e6da4", 1: "#0f766e", 3: "#b45309", 5: "#6d28d9"}
CELDAS = {
    (0, 0): "Meriton A", (0, 1): "Meriton A", (0, 2): "Meriton A +1",
    (1, 0): "RNSH L4", (1, 3): "OFF",
    (2, 1): "Stockland", (2, 2): "Stockland", (2, 4): "Chullora",
    (3, 0): "Meriton B", (3, 1): "Meriton B", (3, 2): "Meriton B", (3, 4): "TAFE",
    (4, 2): "RNSH L5",
    (5, 0): "Zetland C", (5, 1): "Zetland C", (5, 3): "Zetland C",
    (6, 4): "OFF",
    (7, 2): "Chullora", (7, 3): "Chullora",
}

HOY_IDX = st.selectbox("Día de HOY (índice; -1 = fuera de la semana)",
                       [-1, 0, 1, 2, 3, 4, 5], index=3, key="hoy")
ZEBRA = st.checkbox("Franjas alternas", value=True, key="zebra")
HOY_ON = st.checkbox("Resaltar la columna de hoy", value=True, key="hoyon")

# ── CSS de densidad que ya tiene la app (v287) ───────────────────────────────
st.markdown("""
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
[class*="st-key-pnm_"] button p {
  font-size:13px !important; font-weight: 700 !important;
  text-align: left !important; width: 100%; color: #1e4e79;
}
</style>""", unsafe_allow_html=True)

# ── Rejilla (v410, ya desplegada) ────────────────────────────────────────────
st.markdown("""
<style>
.st-key-rosgrid [data-testid="stHorizontalBlock"],
.st-key-roshead [data-testid="stHorizontalBlock"] {
  padding: 3px 0 !important; margin: 0 !important; gap: 0 !important;
}
.st-key-rosgrid [data-testid="stHorizontalBlock"] {
  border-bottom: 1px solid #e6eaf0 !important;
}
.st-key-roshead [data-testid="stHorizontalBlock"] {
  border-bottom: 2px solid #cfd8e3 !important; padding-bottom: 4px !important;
}
.st-key-rosgrid [data-testid="stColumn"],
.st-key-roshead [data-testid="stColumn"] {
  border-right: 1px solid #dfe5ec; padding: 0 4px !important;
}
.st-key-rosgrid [data-testid="stColumn"]:last-child,
.st-key-roshead [data-testid="stColumn"]:last-child { border-right: none; }
.st-key-rosgrid [class*="st-key-roscel_"] [data-testid="stHorizontalBlock"],
.st-key-rosgrid [class*="st-key-roscel_"] [data-testid="stColumn"] {
  border: none !important; padding: revert !important; gap: revert !important;
}
</style>""", unsafe_allow_html=True)

css = []

# ── ZEBRA: fondo por fila impar ──────────────────────────────────────────────
if ZEBRA:
    for pi in range(len(STAFF)):
        if pi % 2 == 1:
            css.append(f".st-key-rosrow_{pi}{{background:#f6f8fa;}}")

# ── HOY: la columna del día, en todas las filas y en la cabecera ─────────────
# ⚠️ `nth-child(N+2)`: la 1ª columna es «Persona», así que el día `di` es la `di+2`.
if HOY_ON and HOY_IDX >= 0:
    n = HOY_IDX + 2
    css.append(
        f".st-key-rosgrid [data-testid='stHorizontalBlock']>[data-testid='stColumn']:nth-child({n}),"
        f".st-key-roshead [data-testid='stHorizontalBlock']>[data-testid='stColumn']:nth-child({n})"
        f"{{background:rgba(46,109,164,.10);}}")
    css.append(
        f".st-key-roshead [data-testid='stHorizontalBlock']>[data-testid='stColumn']:nth-child({n})"
        f"{{box-shadow: inset 0 -3px 0 0 #2e6da4;}}")

# ── Color por celda (igual que la app) ───────────────────────────────────────
for pi in range(len(STAFF)):
    for di in range(len(DIAS)):
        idx = pi * len(DIAS) + di
        key = f"roscel_20260824_{idx}"
        if (pi, di) in CELDAS:
            bg = COLOR.get(pi) or "#475569"
            css.append(f".st-key-{key} button{{background:{bg}!important;"
                       f"color:#fff!important;border-color:{bg}!important;}}")
        else:
            # ⚠️ La celda vacía se hace TRANSPARENTE: con un fondo propio (#f8fafc)
            # taparía la zebra y la franja de hoy, que es justo lo que se quiere ver.
            css.append(f".st-key-{key} button{{background:transparent!important;"
                       f"color:#b6c0cd!important;border:1px dashed #e2e8f0!important;}}"
                       f".st-key-{key} button [data-testid='stIconMaterial']"
                       f"{{display:none!important;}}")
st.markdown("<style>" + "".join(css) + "</style>", unsafe_allow_html=True)

anchos = [1.4] + [1] * len(DIAS)
_CAB = "font-size:13px;font-weight:600;color:#5b6472;text-align:center;margin-bottom:6px"
_CAB_HOY = "font-size:13px;font-weight:700;color:#1e4e79;text-align:center;margin-bottom:6px"

_head = st.container(key="roshead")
h = _head.columns(anchos)
h[0].markdown(f"<div style='{_CAB}'>Persona</div>", unsafe_allow_html=True)
for i, d in enumerate(DIAS):
    _es_hoy = HOY_ON and i == HOY_IDX
    _s = _CAB_HOY if _es_hoy else _CAB
    # ⚠️ «hoy» va en una SEGUNDA LÍNEA, no pegado a la fecha. Medido en producción: a
    # 1440 la columna da 136 px útiles y «Mié 26/08 · hoy» mide 85 (cabe), pero con la
    # ventana estrecha la columna baja a 55 px y ahí ni la fecha sola (53) va holgada:
    # en la misma línea se cortaría, y el corte de un texto en HTML sí deja elipsis o
    # desborda, pero de cualquier modo dejaría de informar (v335).
    _extra = ("<div style='font-size:11px;font-weight:700;color:#2e6da4;"
              "line-height:1.1'>hoy</div>") if _es_hoy else ""
    h[i + 1].markdown(f"<div style='{_s}'>{LABEL[d]} 2{4+i}/08{_extra}</div>",
                      unsafe_allow_html=True)

_grid = st.container(key="rosgrid")
for pi, nom in enumerate(STAFF):
    _row = _grid.container(key=f"rosrow_{pi}")
    cols = _row.columns(anchos)
    cols[0].button(nom, key=f"pnm_20260824_{pi}", width="stretch")
    for di, d in enumerate(DIAS):
        idx = pi * len(DIAS) + di
        et = CELDAS.get((pi, di), "")
        with cols[di + 1].popover(et or "＋", key=f"roscel_20260824_{idx}",
                                  width="stretch"):
            st.caption(f"**{nom}** · {LABEL[d]}")
            c1, c2 = st.columns(2)
            c1.text_input("Desde", "07:00", key=f"ini_{idx}")
            c2.text_input("Hasta", "15:30", key=f"fin_{idx}")
