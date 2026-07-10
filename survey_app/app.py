"""
Survey Analyzer — UI Streamlit.
Solo presentación: toda la lógica de cálculo vive en core/.
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import sys, os
from datetime import date
sys.path.insert(0, os.path.dirname(__file__))

from extractors.schindler import extract_from_pdf, PARAMS as PDF_PARAMS, PARAM_DESCRIPTIONS
from core.calculations import calculate_limits, apply_offsets, analyze_matrix, validate_inputs
from core.optimizer    import optimize
from core.bs_logic     import find_bs_step
from core.report       import generate_report
from core.excel_io     import export_survey_excel, import_survey_excel
from core.highlighting import cell_state, ctrl_applies_to_cell, streamlit_style, OR_OL_COLS
from core.chat_agent      import get_chat_response
from core.interpretation  import generate_interpretation, generate_user_interpretation
from core.email_notify    import send_usage_notification
from core.user_report     import generate_user_report
from core.diagrams        import render_floor_plans_html
from core.schedule        import build_schedule, detect_flags, schedule_svg
from core.plumb           import compute_plumb, plumb_svg, plumb_table, plumb_checks
from core                 import projects as projects_data

try:
    # utf-8-sig elimina el BOM que agrega PowerShell al escribir VERSION
    APP_VERSION = open(os.path.join(os.path.dirname(__file__), "VERSION"),
                       encoding="utf-8-sig").read().strip()
except Exception:
    APP_VERSION = "v?"

# Favicon = ícono COPEX (lado servidor, reemplaza el ícono de Streamlit)
try:
    from PIL import Image
    _PAGE_ICON = Image.open(os.path.join(os.path.dirname(__file__), "static", "icon-192.png"))
except Exception:
    _PAGE_ICON = "📐"

st.set_page_config(page_title=f"COPEX Survey Analyzer {APP_VERSION}",
                   layout="wide", page_icon=_PAGE_ICON)

# ══════════════════════════════════════════════════════
# OPTIMIZACIÓN MÓVIL (CSS responsive)
# ══════════════════════════════════════════════════════
st.markdown("""
<style>
/* En móvil: apilar columnas verticalmente (Streamlit no lo hace solo) */
@media (max-width: 640px) {
  div[data-testid="stHorizontalBlock"] {
    flex-wrap: wrap !important;
    gap: 0.35rem !important;
  }
  div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    min-width: 100% !important;
    flex: 1 1 100% !important;
  }
  /* Menos padding en pantalla pequeña → más espacio útil */
  .block-container {
    padding-top: 1rem !important;
    padding-left: 0.7rem !important;
    padding-right: 0.7rem !important;
  }
  /* Pestañas más compactas y con scroll horizontal si no caben */
  div[data-testid="stTabs"] button[data-baseweb="tab"] {
    padding: 0 10px !important;
    font-size: 0.85rem !important;
  }
  h1 { font-size: 1.4rem !important; }
  h2 { font-size: 1.2rem !important; }
  h3 { font-size: 1.05rem !important; }
  /* Botones más altos = más fáciles de tocar */
  div[data-testid="stButton"] button { min-height: 44px; }
}
/* Inputs con altura táctil cómoda en cualquier pantalla */
div[data-testid="stNumberInput"] input,
div[data-testid="stTextInput"] input { min-height: 40px; }
</style>
""", unsafe_allow_html=True)

# ── PWA: manifest + íconos + meta-tags (instalable con ícono COPEX) ──
components.html("""
<script>
try {
  var d = window.parent.document, h = d.head;
  var base = window.parent.location.origin + '/app/static/';
  function add(tag, attrs){ var e=d.createElement(tag); for(var k in attrs) e.setAttribute(k, attrs[k]); h.appendChild(e); }
  if(!d.querySelector('link[rel="manifest"]')){
    add('link', {rel:'manifest', href: base + 'manifest.webmanifest'});
    add('link', {rel:'apple-touch-icon', href: base + 'icon-192.png'});
    add('link', {rel:'icon', type:'image/png', sizes:'512x512', href: base + 'icon-512.png'});
    add('meta', {name:'apple-mobile-web-app-capable', content:'yes'});
    add('meta', {name:'mobile-web-app-capable', content:'yes'});
    add('meta', {name:'apple-mobile-web-app-status-bar-style', content:'black-translucent'});
    add('meta', {name:'apple-mobile-web-app-title', content:'COPEX'});
    add('meta', {name:'theme-color', content:'#1a3a5c'});
  }
} catch(e) {}
</script>
""", height=0)

SURVEY_COLS = ["WR", "FR", "OR", "WL", "FL", "OL"]
USER_ONLY = {
    "BSR":            "Ancho real del hueco medido en obra (mm)",
    "FS":             "Distancia frontal de seguridad (mm)",
    "FRAME":          "Marco de puerta de entrada (mm)",
    "RAIL":           "Ancho de la cabeza del riel (mm)",
    "OFFSET_CABIN":   "Offset de cabina (mm)",
    "LengthTemplate": "Longitud del template de plomada (mm) — para el esquema de plomado",
}

# ══════════════════════════════════════════════════════
# INICIALIZACIÓN DE STATE
# ══════════════════════════════════════════════════════
def _init_state():
    if "initialized" in st.session_state:
        return
    # PDF params
    for p in PDF_PARAMS:
        st.session_state[f"inp_{p}"] = 0.0
    # User params
    for p in USER_ONLY:
        st.session_state[f"inp_{p}"] = 0.0
    # Config defaults (con keys para que radios lean de session_state)
    st.session_state["cfg_omega_side"]   = "R"
    st.session_state["cfg_wall_yn"]      = "N"
    st.session_state["cfg_offset_side"]  = "R"
    st.session_state["cfg_wall_stop"]    = 1
    st.session_state["cfg_wall_side"]    = "R"
    st.session_state["cfg_ctrl_yn"]      = "N"
    st.session_state["cfg_ctrl_side"]    = "R"
    # Otros
    st.session_state["pdf_extracted"]  = {}
    st.session_state["last_pdf_name"]  = None
    st.session_state["pdf_bytes"]      = None
    st.session_state["ns"]             = 6
    st.session_state["survey_df"]      = pd.DataFrame({c: [0.0]*6 for c in SURVEY_COLS})
    st.session_state["survey_original_input"] = None   # snapshot al momento del cálculo
    st.session_state["calc_results"]   = None
    st.session_state["chat_history"]   = []
    st.session_state["proyecto"]       = ""
    st.session_state["ingeniero"]      = ""
    st.session_state["initialized"]    = True

_init_state()

# ══════════════════════════════════════════════════════
# LOGIN — barrera de acceso
# ══════════════════════════════════════════════════════
from core.auth_ui import render_login, render_user_bar, render_owner_panel, render_group_panel
from core.auth import can_reports

if not render_login():
    st.stop()

_ROL   = st.session_state.auth["rol"]
_GRUPO = st.session_state.auth.get("grupo", "")

# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════
with st.sidebar:
    # ── Cabecera COPEX ─────────────────────────────────
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1a3a5c,#2e6da4);
                padding:14px 16px;border-radius:8px;margin-bottom:12px;">
        <div style="color:white;font-size:1.7rem;font-weight:900;
                    letter-spacing:0.18em;font-family:'Segoe UI',sans-serif;
                    line-height:1.1;">COPEX</div>
        <div style="color:#b0c8e8;font-size:0.72rem;margin-top:2px;">
            Elevator Survey Analyzer &nbsp;·&nbsp; {APP_VERSION}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Usuario logueado ────────────────────────────────
    render_user_bar()
    st.markdown("---")

    # ── Valores extraídos del PDF ───────────────────────
    st.markdown("#### 📋 Valores del PDF")
    if st.session_state.pdf_extracted:
        found   = {k:v for k,v in st.session_state.pdf_extracted.items() if v is not None}
        missing = [k for k,v in st.session_state.pdf_extracted.items() if v is None]
        st.markdown(f"**Archivo:** `{st.session_state.last_pdf_name}`")
        st.markdown(f"✅ Encontrados: **{len(found)}** / {len(st.session_state.pdf_extracted)}")
        if missing:
            st.warning(f"Faltantes: `{'`, `'.join(missing)}`")
        st.markdown("---")
        for k, v in sorted(found.items()):
            st.markdown(f"**{k}** = `{v:.0f}` mm")
            desc = PARAM_DESCRIPTIONS.get(k, "")
            if desc:
                st.caption(desc)
    else:
        st.info("Carga un PDF para ver los valores aquí.")

    # ── Leyenda ────────────────────────────────────────
    st.markdown("---")
    st.caption("🔴 Rojo oscuro = peor valor fuera de límite")
    st.caption("🔴 Rojo claro  = fuera de límite")
    st.caption("🟠 Naranja     = OR/OL requiere corte (Caso 2)")

    # ══════════════════════════════════════════════════
    # ASISTENTE IA — desplegable en sidebar
    # ══════════════════════════════════════════════════
    st.markdown("---")
    with st.expander("🤖 Asistente Técnico COPEX", expanded=False):
        ctx_label = "🔗 Con contexto del cálculo actual." if st.session_state.calc_results else "Sin cálculo activo."
        st.caption(f"Experto en instalación de elevadores Schindler. {ctx_label}")

        # Historial
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"],
                                 avatar="🧑‍🔧" if msg["role"] == "user" else "🤖"):
                st.markdown(msg["content"])

        # Input
        if prompt := st.chat_input("Escribe tu pregunta…", key="sidebar_chat_input"):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="🧑‍🔧"):
                st.markdown(prompt)
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Consultando…"):
                    _r = st.session_state.calc_results
                    _response = get_chat_response(
                        user_message = prompt,
                        history      = st.session_state.chat_history[:-1],
                        calc_results = _r,
                        all_params   = _r["all_params"] if _r else None,
                    )
                st.markdown(_response)
            st.session_state.chat_history.append({"role": "assistant", "content": _response})

        # Limpiar
        if st.session_state.chat_history:
            if st.button("🗑 Limpiar conversación", use_container_width=True, key="clear_chat_sb"):
                st.session_state.chat_history = []
                st.rerun()

# ══════════════════════════════════════════════════════
# CABECERA PRINCIPAL
# ══════════════════════════════════════════════════════
st.markdown(f"""
<div style="background:linear-gradient(135deg,#1a3a5c 0%,#2e6da4 100%);
            padding:clamp(14px,4vw,22px) clamp(16px,5vw,32px);border-radius:12px;
            margin-bottom:20px;display:flex;justify-content:space-between;
            align-items:center;gap:12px;flex-wrap:wrap;">
    <div style="min-width:0;">
        <div style="color:white;font-size:clamp(1.6rem,7vw,2.4rem);font-weight:900;
                    letter-spacing:0.18em;font-family:'Segoe UI',sans-serif;
                    line-height:1.0;">COPEX</div>
        <div style="color:#b0c8e8;font-size:clamp(0.8rem,3vw,1rem);margin-top:4px;font-weight:400;">
            Elevator Survey Analyzer
        </div>
    </div>
    <div style="text-align:right;">
        <div style="color:#b0c8e8;font-size:0.75rem;">Versión</div>
        <div style="color:white;font-size:clamp(1.1rem,4vw,1.4rem);font-weight:700;
                    font-family:'Courier New',monospace;">{APP_VERSION}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Navegación con selector (NO st.tabs → evita el bug de mezcla de contenido).
# Solo se renderiza la sección seleccionada; no hay paneles ocultos que se filtren.
_L_SURVEY = "📐 Survey de elevador"
_L_PLUMB  = "🔩 Líneas de plomada"
_L_RAIL   = "✂️ Corte de rieles"
_L_CLOCK  = "⏱ Fichaje"
_L_OWNER  = "👑 Administración"
_L_GRUPO  = "🛠 Mi grupo"
_L_FIELDPROJ = "📋 Mis proyectos"

_nav = [_L_SURVEY, _L_PLUMB, _L_RAIL, _L_CLOCK]
if _ROL == "campo":
    _nav.append(_L_FIELDPROJ)
if _ROL == "propietario":
    _nav.append(_L_OWNER)
elif _ROL == "administrador":
    _nav.append(_L_GRUPO)

_seccion = st.radio("Navegación", _nav, horizontal=True,
                    key="main_nav", label_visibility="collapsed")
st.markdown("---")

if _seccion == _L_SURVEY:

    # ── Identificación del proyecto ───────────────────────
    _id1, _id2 = st.columns(2)
    _id1.text_input("🏗 Nombre del proyecto / Cliente", key="proyecto",
                    placeholder="Ej: Edificio Centro, Cliente ABC…")
    _id2.text_input("👷 Ingeniero responsable", key="ingeniero",
                    placeholder="Nombre del técnico que realiza el survey")

    # ══════════════════════════════════════════════════════
    # PASO 1 — CARGAR PDF
    # ══════════════════════════════════════════════════════
    st.header("1. Cargar planos")
    col_brand, col_pdf = st.columns([1, 3])
    col_brand.selectbox("Marca", ["Schindler"], key="brand")   # placeholder p/ futura expansión
    pdf_file = col_pdf.file_uploader("PDF de planos", type=["pdf"])

    if pdf_file is not None and pdf_file.name != st.session_state.last_pdf_name:
        with st.spinner("⏳ Extrayendo datos del PDF..."):
            extracted = extract_from_pdf(pdf_file)
        st.session_state.pdf_extracted = extracted
        st.session_state.last_pdf_name = pdf_file.name
        st.session_state.pdf_bytes     = pdf_file.getvalue()   # guardar para adjuntar en correo
        for p in PDF_PARAMS:
            if extracted.get(p) is not None:
                st.session_state[f"inp_{p}"] = float(extracted[p])
        found   = sum(1 for v in extracted.values() if v is not None)
        missing = [k for k,v in extracted.items() if v is None]
        st.success(f"✅ {found}/{len(extracted)} parámetros encontrados.")
        if missing:
            st.warning(f"⚠️ Ingresar manualmente: **{', '.join(missing)}**")
        st.rerun()
    elif pdf_file and pdf_file.name == st.session_state.last_pdf_name:
        st.info(f"📄 Datos de: **{pdf_file.name}** — ver sidebar.")

    # ══════════════════════════════════════════════════════
    # PASO 2 — PARÁMETROS
    # ══════════════════════════════════════════════════════
    st.header("2. Parámetros del proyecto")

    with st.expander("📄 Parámetros del PDF (editables)", expanded=True):
        for i in range(0, len(PDF_PARAMS), 4):
            cols = st.columns(4)
            for j, p in enumerate(PDF_PARAMS[i:i+4]):
                cols[j].number_input(
                    label = f"{p} (mm)",
                    step  = 0.5,
                    help  = PARAM_DESCRIPTIONS.get(p, ""),
                    key   = f"inp_{p}",
                )

    with st.expander("✏️ Parámetros del usuario", expanded=True):
        cols = st.columns(len(USER_ONLY))
        for j, (p, desc) in enumerate(USER_ONLY.items()):
            cols[j].number_input(
                label = f"{p} (mm)",
                step  = 0.5,
                help  = desc,
                key   = f"inp_{p}",
            )

    st.subheader("Configuración")
    c1, c2, c3 = st.columns(3)
    c1.radio("Lado del Omega",        ["R", "L"], horizontal=True, key="cfg_omega_side")
    c2.radio("¿Hay pared limitante?", ["N", "Y"], horizontal=True, key="cfg_wall_yn")
    c3.radio("Lado offset cabina",    ["R", "L"], horizontal=True, key="cfg_offset_side")

    wall_limiting = (st.session_state.cfg_wall_yn == "Y")
    if wall_limiting:
        wc1, wc2 = st.columns(2)
        wc1.number_input("Parada limitante", min_value=1, step=1, key="cfg_wall_stop")
        wc2.radio("Lado de la pared",        ["R", "L"], horizontal=True, key="cfg_wall_side")

    cc1, cc2 = st.columns(2)
    cc1.radio("¿Controlador hace parte del frame?", ["N", "Y"], horizontal=True, key="cfg_ctrl_yn")
    ctrl_in_frame = (st.session_state.cfg_ctrl_yn == "Y")
    if ctrl_in_frame:
        cc2.radio("Lado del controlador", ["R", "L"], horizontal=True, key="cfg_ctrl_side")

    # Lectura final de configuración para resto del flujo
    omega_side  = st.session_state.cfg_omega_side
    offset_side = st.session_state.cfg_offset_side
    wall_stop   = st.session_state.cfg_wall_stop if wall_limiting else None
    wall_side   = st.session_state.cfg_wall_side if wall_limiting else None
    ctrl_side   = st.session_state.cfg_ctrl_side if ctrl_in_frame else None

    # ══════════════════════════════════════════════════════
    # PASO 3 — MATRIZ SURVEY
    # ══════════════════════════════════════════════════════
    st.header("3. Matriz SURVEY")

    sc1, sc2, sc3 = st.columns([1, 2, 2])

    sc1.number_input("Número de paradas (NS)", min_value=2, max_value=50, step=1, key="ns")

    # Ajustar tamaño si NS cambió
    current_ns = len(st.session_state.survey_df)
    if int(st.session_state.ns) != current_ns:
        old_df    = st.session_state.survey_df.copy()
        new_ns    = int(st.session_state.ns)
        new_df    = pd.DataFrame({c: [0.0]*new_ns for c in SURVEY_COLS})
        rows_keep = min(len(old_df), new_ns)
        new_df.iloc[:rows_keep] = old_df.iloc[:rows_keep].values
        st.session_state.survey_df = new_df
        st.rerun()

    # Cargar Excel
    uploaded_excel = sc2.file_uploader("📂 Cargar matriz (.xlsx)", type=["xlsx"], key="excel_uploader")
    if uploaded_excel is not None:
        try:
            imported = import_survey_excel(uploaded_excel)
            st.session_state.survey_df = imported["df"].copy()
            st.session_state["ns"]     = len(imported["df"])
            # Restaurar parámetros numéricos
            for k, v in imported.get("info", {}).items():
                if k in PDF_PARAMS or k in USER_ONLY:
                    st.session_state[f"inp_{k}"] = float(v)
            # Restaurar configuración
            cfg = imported.get("config", {})
            if cfg.get("OMEGA_SIDE")   in ("R", "L"): st.session_state.cfg_omega_side  = cfg["OMEGA_SIDE"]
            if cfg.get("OFFSET_SIDE")  in ("R", "L"): st.session_state.cfg_offset_side = cfg["OFFSET_SIDE"]
            if "WALL_LIMITING" in cfg:
                st.session_state.cfg_wall_yn = "Y" if cfg["WALL_LIMITING"] else "N"
            if cfg.get("WALL_STOP") is not None:      st.session_state.cfg_wall_stop = int(cfg["WALL_STOP"])
            if cfg.get("WALL_SIDE") in ("R", "L"):    st.session_state.cfg_wall_side = cfg["WALL_SIDE"]
            if "CTRL_IN_FRAME" in cfg:
                st.session_state.cfg_ctrl_yn = "Y" if cfg["CTRL_IN_FRAME"] else "N"
            if cfg.get("CTRL_SIDE") in ("R", "L"):    st.session_state.cfg_ctrl_side = cfg["CTRL_SIDE"]
            sc2.success("✅ Matriz y configuración cargadas.")
            st.rerun()
        except Exception as e:
            sc2.error(f"Error al importar Excel: {e}")

    st.caption("Ingresa o edita las medidas en campo (mm).")
    edited_df = st.data_editor(
        st.session_state.survey_df,
        use_container_width=True,
        num_rows="fixed",
        key="survey_editor"
    )
    st.session_state.survey_df = edited_df.copy()

    # Exportar Excel
    info_dict   = {p: st.session_state.get(f"inp_{p}", 0.0) for p in list(PDF_PARAMS) + list(USER_ONLY.keys())}
    config_dict = {
        "OMEGA_SIDE":    omega_side,
        "WALL_LIMITING": wall_limiting,
        "WALL_STOP":     wall_stop,
        "WALL_SIDE":     wall_side,
        "OFFSET_SIDE":   offset_side,
        "CTRL_IN_FRAME": ctrl_in_frame,
        "CTRL_SIDE":     ctrl_side,
        "NS":            int(st.session_state.ns),
    }
    excel_bytes = export_survey_excel(edited_df, info_dict, config_dict)
    sc3.download_button(
        label     = "💾 Guardar matriz (.xlsx)",
        data      = excel_bytes,
        file_name = "survey_matrix.xlsx",
        mime      = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    # ══════════════════════════════════════════════════════
    # Helper: highlight para DataFrames de Streamlit
    # ══════════════════════════════════════════════════════
    def make_highlighter(lim_map, min_vals, max_vals, cut_cols, ctrl_in_frame_, ctrl_side_):
        """Devuelve una función que aplica CSS de highlight a un DataFrame."""
        def _highlight(df):
            styles = pd.DataFrame("", index=df.index, columns=df.columns)
            total_rows = len(df)
            for ri_off, idx in enumerate(df.index):
                for col in df.columns:
                    if col not in lim_map:
                        continue
                    val = df.at[idx, col]
                    state = cell_state(
                        value       = val,
                        col         = col,
                        lim         = lim_map[col],
                        min_val     = min_vals.get(f"MIN_{col}"),
                        max_val     = max_vals.get(f"MAX_{col}"),
                        in_cut_cols = col in cut_cols,
                        ctrl_applies= ctrl_applies_to_cell(ri_off, total_rows, col, ctrl_in_frame_, ctrl_side_),
                    )
                    styles.at[idx, col] = streamlit_style(state)
            return styles
        return _highlight

    # ══════════════════════════════════════════════════════
    # PASO 4 — CALCULAR
    # ══════════════════════════════════════════════════════
    st.header("4. Cálculo y Optimización")

    if st.button("🚀 Calcular", type="primary", use_container_width=True):

        # Snapshot del survey ANTES de hacer cualquier ajuste
        survey_original_input = st.session_state.survey_df.copy()

        # Build de parámetros
        all_params = {p: st.session_state.get(f"inp_{p}", 0.0) for p in list(PDF_PARAMS) + list(USER_ONLY.keys())}
        all_params["OMEGA_SIDE"]    = omega_side
        all_params["WALL_LIMITING"] = wall_limiting
        all_params["WALL_STOP"]     = wall_stop
        all_params["WALL_SIDE"]     = wall_side
        all_params["OFFSET_SIDE"]   = offset_side
        all_params["CTRL_IN_FRAME"] = ctrl_in_frame
        all_params["CTRL_SIDE"]     = ctrl_side
        all_params["NS"]            = int(st.session_state.ns)
        all_params["PROYECTO"]      = st.session_state.get("proyecto", "")
        all_params["INGENIERO"]     = st.session_state.get("ingeniero", "")

        # Totales = última fila de la matriz
        last = survey_original_input.iloc[-1]
        for col in SURVEY_COLS:
            all_params[f"{col[0]}{col[1]}T"] = float(last[col])

        # ── Validación de inputs ─────────────────────────────
        issues = validate_inputs(all_params)
        if issues:
            st.error("⚠️ Problemas en los parámetros — revisar antes de calcular:")
            for issue in issues:
                st.error(f"  • {issue}")
            st.stop()

        try:
            limits = calculate_limits(all_params)
        except Exception as e:
            st.error(f"Error en cálculo: {e}")
            st.stop()

        all_params.update(limits)

        with st.expander("📊 Parámetros calculados", expanded=False):
            st.dataframe(
                pd.DataFrame([
                    {"Parámetro": k, "Valor": round(v, 3) if isinstance(v, (int, float)) else v}
                    for k, v in limits.items()
                ]),
                use_container_width=True, hide_index=True
            )

        # Matriz ajustada
        survey_adj    = apply_offsets(survey_original_input.to_dict("records"), limits)
        survey_adj_df = pd.DataFrame(survey_adj)
        analysis      = analyze_matrix(survey_adj, limits, wall_limiting=wall_limiting)
        all_params.update(analysis)
        limits.update(analysis)

        lim_map  = {c: limits[f"LIMIT_{c}"] for c in SURVEY_COLS}
        min_vals = {f"MIN_{c}": analysis[f"MIN_{c}"] for c in SURVEY_COLS}
        max_vals = {f"MAX_{c}": analysis.get(f"MAX_{c}", analysis[f"MIN_{c}"]) for c in SURVEY_COLS}

        # En Caso 2 OR/OL no son OFF: se muestran en naranja (CUT)
        cut_cols = ["OR", "OL"] if not wall_limiting else []

        highlight = make_highlighter(lim_map, min_vals, max_vals, cut_cols, ctrl_in_frame, ctrl_side)

        st.subheader("Matriz SURVEY ajustada")
        st.dataframe(survey_adj_df.style.apply(highlight, axis=None),
                     use_container_width=True)

        st.subheader("Resumen por columna — Estado inicial")
        last_adj = len(survey_adj) - 1
        summary  = []
        for col in SURVEY_COLS:
            lim_c = lim_map[col]
            viols = []
            for i, row in enumerate(survey_adj):
                v  = row[col]
                el = lim_c
                if ctrl_applies_to_cell(i, len(survey_adj), col, ctrl_in_frame, ctrl_side):
                    el -= 70
                if col in OR_OL_COLS:
                    if v > el: viols.append(str(i + 1))
                else:
                    if v < el: viols.append(str(i + 1))
            ext = round(analysis.get(f"MAX_{col}", analysis[f"MIN_{col}"]), 2) \
                  if col in OR_OL_COLS else round(analysis[f"MIN_{col}"], 2)
            summary.append({
                "Columna":             col,
                "Límite (mm)":         round(lim_c, 2),
                "Fuera límite":        analysis[f"{col}_OFF_COUNT"],
                "Niveles incumplidos": ", ".join(viols) if viols else "—",
                "Min / Max (mm)":      ext,
                "Diferencia (mm)":     round(analysis[f"DIF_{col}"], 2),
            })
        st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)

        st.info(
            f"**MAX OFF RL:** {analysis['MAX_OFF_RL']:.2f} mm  |  "
            f"**MAX OFF FB:** {analysis['MAX_OFF_FB']:.2f} mm  |  "
            f"**BC_CALC:** {limits.get('BC_CALC', 0):.2f} mm  |  "
            f"**DIF TSW-FS:** {limits.get('DIF_TSW_FS', 0):.2f} mm  |  "
            f"**FB máx. hacia atrás:** {limits.get('FB_MAX_BACK', 0):.2f} mm"
        )

        # ── Optimización ──────────────────────────────────────
        st.subheader("🔍 Optimización")
        with st.spinner("Buscando combinación óptima..."):
            opt_result = optimize(survey_adj, limits, all_params)

        best          = opt_result.get("best")
        all_solutions = opt_result.get("all_solutions", [])
        step_log      = opt_result.get("step_log", [])

        if best:
            n_sol = len(all_solutions)
            st.success(
                f"✅ Se encontraron **{n_sol} solución(es) óptima(s)** con "
                f"**{best['total_off']} valor(es) fuera de límite**"
            )

            # Ordenar usando el mismo criterio que el optimizer (fb_applied)
            best_pair = (best["rl"], best["fb"])
            sorted_solutions = sorted(
                all_solutions,
                key=lambda s: (
                    0 if (s["rl"], s["fb"]) == best_pair else 1,
                    abs(s["rl"]) + abs(s.get("fb_applied", s["fb"]))
                )
            )
            for idx_sol, sol in enumerate(sorted_solutions):
                is_best   = (sol["rl"], sol["fb"]) == best_pair
                fb_ap     = sol.get("fb_applied", sol["fb"])
                fb_suffix = f"  |  FB aplic. = {fb_ap:.1f} mm" if abs(fb_ap - sol["fb"]) > 0.01 else ""
                sol_label = f"{'⭐ ' if is_best else ''}Solución {idx_sol+1} — RL = {sol['rl']} mm  |  FB = {sol['fb']} mm{fb_suffix}"
                with st.expander(sol_label, expanded=(idx_sol == 0)):
                    sol_df  = pd.DataFrame(sol["matrix"])
                    sol_min = {f"MIN_{c}": min(sol_df[c]) for c in SURVEY_COLS}
                    sol_max = {f"MAX_{c}": max(sol_df[c]) for c in SURVEY_COLS}
                    if not wall_limiting:
                        lor_v        = lim_map["OR"]
                        lol_v        = lim_map["OL"]
                        last_sol_idx = len(sol_df) - 1
                        cut_or_vals, cut_ol_vals = [], []
                        for i, (or_v, ol_v) in enumerate(zip(sol_df["OR"], sol_df["OL"])):
                            or_lim = lor_v - 70 if (ctrl_in_frame and ctrl_side == "R" and i == last_sol_idx) else lor_v
                            ol_lim = lol_v - 70 if (ctrl_in_frame and ctrl_side == "L" and i == last_sol_idx) else lol_v
                            cut_or_vals.append(round(or_v - or_lim, 1) if or_v - or_lim > 0 else "")
                            cut_ol_vals.append(round(ol_v - ol_lim, 1) if ol_v - ol_lim > 0 else "")
                        sol_df.insert(3, "CUT OR", cut_or_vals)
                        sol_df.insert(7, "CUT OL", cut_ol_vals)
                    sol_highlighter = make_highlighter(lim_map, sol_min, sol_max, cut_cols, ctrl_in_frame, ctrl_side)
                    st.dataframe(sol_df.style.apply(sol_highlighter, axis=None),
                                 use_container_width=True)
                    if not wall_limiting:
                        st.caption("CUT OR / CUT OL: valor a cortar si OR/OL supera el límite (OR/OL − LIMIT). Positivo = requiere corte. Blanco = dentro del límite.")
                    sol_sum = []
                    for col in SURVEY_COLS:
                        col_vals = [r[col] for r in sol["matrix"]]
                        lim_c = lim_map[col]
                        if col in OR_OL_COLS:
                            ext_c = max(col_vals); dif_c = ext_c - lim_c
                            off_c = sum(1 for v in col_vals if v > lim_c)
                            lbl   = "Máximo (mm)"
                            viols_s = [str(i+1) for i,v in enumerate(col_vals) if v > lim_c]
                        else:
                            ext_c = min(col_vals); dif_c = lim_c - ext_c
                            off_c = sum(1 for v in col_vals if v < lim_c)
                            lbl   = "Mínimo (mm)"
                            viols_s = [str(i+1) for i,v in enumerate(col_vals) if v < lim_c]
                        sol_sum.append({
                            "Columna":       col,
                            "Límite (mm)":   round(lim_c, 2),
                            "Fuera límite":  off_c,
                            "Niveles":       ", ".join(viols_s) if viols_s else "—",
                            lbl:             round(ext_c, 2),
                            "Dif vs Límite": round(dif_c, 2),
                        })
                    st.dataframe(pd.DataFrame(sol_sum), use_container_width=True, hide_index=True)

            # Log del optimizador
            with st.expander(f"📋 Log del optimizador ({len(step_log)} pasos evaluados)", expanded=False):
                valid_steps  = [s for s in step_log if s.get("status") == "VALID"]
                skip_steps   = [s for s in step_log if s.get("status") == "SKIP"]
                skip_phys    = [s for s in skip_steps if s.get("skip_type", "").startswith("physical")]
                skip_wall    = [s for s in skip_steps if s.get("skip_type") == "wall"]
                skip_frame   = [s for s in skip_steps if s.get("skip_type") == "frame_opening"]
                st.caption(
                    f"Válidos: {len(valid_steps)}  |  "
                    f"Omitidos por límite físico (RL/FB): {len(skip_phys)}  |  "
                    f"Omitidos por pared: {len(skip_wall)}  |  "
                    f"Omitidos por apertura tapada: {len(skip_frame)}"
                )
                if valid_steps:
                    opt_pairs = {(s["rl"], s["fb"]) for s in all_solutions}
                    best_p    = (best["rl"], best["fb"])
                    log_rows  = []
                    for s in valid_steps:
                        obc  = s.get("off_by_col", {})
                        pair = (s["rl"], s["fb"])
                        if pair == best_p:        estado = "⭐ SELECCIONADA"
                        elif pair in opt_pairs:   estado = "✅ ÓPTIMA"
                        else:                     estado = ""
                        log_rows.append({
                            "RL": s["rl"], "FB": s["fb"],
                            "FB aplic.": s.get("fb_applied", s["fb"]),
                            "Total OFF": s["total_off"],
                            "WR": obc.get("WR",0), "FR": obc.get("FR",0),
                            "OR": obc.get("OR",0), "WL": obc.get("WL",0),
                            "FL": obc.get("FL",0), "OL": obc.get("OL",0),
                            "Estado": estado,
                        })
                    # Ordenar: seleccionada → óptimas → resto
                    log_rows = (
                        [r for r in log_rows if r["Estado"] == "⭐ SELECCIONADA"] +
                        [r for r in log_rows if r["Estado"] == "✅ ÓPTIMA"] +
                        [r for r in log_rows if r["Estado"] == ""]
                    )
                    df_log = pd.DataFrame(log_rows)
                    def _hl(row):
                        if row["Estado"] == "⭐ SELECCIONADA":
                            return ["background-color:#7b5c00;color:white;font-weight:bold"] * len(row)
                        if row["Estado"] == "✅ ÓPTIMA":
                            return ["background-color:#1a3a2a;color:#a8e6cf"] * len(row)
                        return [""] * len(row)
                    st.dataframe(df_log.style.apply(_hl, axis=1),
                                 use_container_width=True, hide_index=True)
        else:
            st.error("No se encontró combinación válida.")
            opt_result = {"best": None, "all_solutions": [], "step_log": step_log}

        # ── Diagrama físico — planta por piso ─────────────────
        st.subheader("📐 Diagrama de posicionamiento — planta por piso")
        st.caption("Vista superior de cómo encaja la cabina en el shaft en cada piso "
                   "(matriz de la solución seleccionada). Verde = dentro de límite, "
                   "naranja = al límite, rojo = fuera.")
        best_sol = opt_result.get("best") if opt_result else None
        if best_sol and best_sol.get("matrix"):
            n_floors = len(best_sol["matrix"])
            components.html(
                render_floor_plans_html(all_params, limits, best_sol, lim_map,
                                        ctrl_in_frame, ctrl_side),
                height=min(398 * n_floors + 20, 8000),
                scrolling=True,
            )

        # ── BSR vs BS ─────────────────────────────────────────
        st.subheader("📏 Análisis BSR vs BS")
        bs_result = find_bs_step(
            all_params["BSR"], all_params["BS"],
            limits["LIMIT_ZB"], limits["LIMIT_OB"]
        )
        if not bs_result.get("needed"):
            st.success("BSR ≥ BS — No se requiere ajuste de shaft.")
        elif bs_result.get("step") is None:
            st.error(f"No se encontró paso. DIF BS = {bs_result.get('dif_original')} mm")
        else:
            st.success(
                f"✅ Paso: **{bs_result['step']} mm**  |  "
                f"Rango: **{bs_result['range']}**  |  Zona: **{bs_result['range_name']}**"
            )

        # ── Plomado definitivo (con el desplazamiento del survey) ──
        st.subheader("🔩 Plomado definitivo (según el survey)")
        st.caption("Esquema de plomado con los desplazamientos que determinó el survey. "
                   "El conjunto (plomos + paredes teóricas + template) se mueve; las paredes "
                   "reales quedan fijas (eje cero = pared real izquierda).")
        plumb_res = None
        if best_sol is not None:
            try:
                _plumb_inp = {
                    "BKS":  all_params["BKS"],  "RAIL": all_params["RAIL"],
                    "TKSW": all_params["TKSW"], "LengthTemplate": all_params.get("LengthTemplate", 0.0),
                    "SF1":  all_params["SF1"],  "SF2":  all_params["SF2"],
                    "BSR":  all_params["BSR"],  "BS":   all_params["BS"],
                }
                _sdisp    = {"rl": best_sol["rl"], "fb": best_sol["fb_applied"]}
                plumb_res = compute_plumb(_plumb_inp, survey_disp=_sdisp)
                st.info(
                    f"Desplazamiento aplicado:  lateral (rl) = **{best_sol['rl']:.1f} mm**  ·  "
                    f"frontal (fb) = **{best_sol['fb_applied']:.1f} mm**."
                )
                pm1, pm2, pm3 = st.columns(3)
                pm1.metric("DBP",  f"{plumb_res['dbp']:.1f} mm")
                pm2.metric("DBPW", f"{plumb_res['dbpw']:.1f} mm")
                pm3.metric("RW",   f"{plumb_res['rw']:.1f} mm")
                st.dataframe(pd.DataFrame(plumb_table(plumb_res)),
                             use_container_width=True, hide_index=True)
                components.html(
                    '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
                    + plumb_svg(plumb_res) + '</body></html>',
                    height=460, scrolling=False,
                )
                st.markdown("**📏 Verificación en campo — distancias plomo ↔ pared real**")
                st.dataframe(pd.DataFrame(plumb_checks(plumb_res)),
                             use_container_width=True, hide_index=True)
                if float(all_params.get("LengthTemplate", 0.0)) <= 0:
                    st.info("💡 Ingresa **LengthTemplate** en los parámetros para ver el "
                            "template completo (punto P, cortes C1/C2 y diagonales).")
            except Exception as e:
                plumb_res = None
                st.warning(f"No se pudo generar el plomado definitivo: {e}")
        else:
            st.caption("Se mostrará cuando el survey encuentre una solución válida.")

        # ── Interpretaciones IA (admin + usuario) ─────────────
        _calc_for_ia = {
            "limits":           limits,
            "analysis":         analysis,
            "optimizer_result": opt_result,
            "bs_result":        bs_result,
        }
        with st.spinner("🤖 Generando interpretación técnica con IA..."):
            interpretation = generate_interpretation(_calc_for_ia, all_params)
        with st.spinner("🤖 Generando interpretación del informe de cliente..."):
            interpretation_user = generate_user_interpretation(_calc_for_ia, all_params)

        if interpretation.get("_ok"):
            st.success("🤖 Interpretaciones generadas correctamente.")
        else:
            st.error(
                f"⚠️ **No se pudo generar la interpretación técnica:** {interpretation.get('_error')}\n\n"
                "Los informes **requieren** la interpretación IA. Verifica que "
                "`ANTHROPIC_API_KEY` esté configurada en los **Secrets de Streamlit Cloud**."
            )

        # ── Persistir para los reportes ───────────────────────
        st.session_state.calc_results = {
            "all_params":          all_params,
            "limits":              limits,
            "survey_orig":         survey_original_input,
            "survey_adj":          survey_adj_df,
            "lim_map":             lim_map,
            "analysis":            analysis,
            "optimizer_result":    opt_result,
            "bs_result":           bs_result,
            "interpretation":      interpretation,
            "interpretation_user": interpretation_user,
            "plumb":               plumb_res,
        }

        # ── Cronograma automático según el proyecto ───────────
        _flags = detect_flags(st.session_state.calc_results)
        _auto  = build_schedule(int(st.session_state.ns), date.today(), _flags)
        st.session_state.calc_results["schedule"] = _auto
        st.session_state["sched_rows"] = [
            {"Actividad": a["nombre"], "Duración (d)": int(a["duracion"]), "Peso (%)": a["peso"]}
            for a in _auto["activities"]
        ]
        st.session_state["sched_start"] = date.today()

        # ── Informe ADMIN (completo) → correo interno ─────────
        admin_pdf = None
        if interpretation.get("_ok"):
            try:
                with st.spinner("📄 Preparando informe interno de administración..."):
                    admin_pdf = generate_report(
                        project_params   = all_params,
                        calculated       = limits,
                        survey_original  = survey_original_input,
                        survey_adjusted  = survey_adj_df,
                        lim_map          = lim_map,
                        analysis         = analysis,
                        optimizer_result = opt_result,
                        bs_result        = bs_result,
                        survey_cols      = SURVEY_COLS,
                        interpretation   = interpretation,
                        schedule         = _auto,
                        plumb            = plumb_res,
                    )
            except Exception as e:
                st.warning(f"No se pudo generar el informe admin para el correo: {e}")

        # ── Notificación por correo (con informe admin adjunto) ─
        send_usage_notification(
            proyecto        = st.session_state.get("proyecto", ""),
            ingeniero       = st.session_state.get("ingeniero", ""),
            all_params      = all_params,
            analysis        = analysis,
            opt_result      = opt_result,
            bs_result       = bs_result,
            survey_df       = survey_original_input,
            pdf_bytes       = st.session_state.get("pdf_bytes"),
            pdf_name        = st.session_state.get("last_pdf_name"),
            admin_report    = admin_pdf,
        )
        if admin_pdf:
            st.info("📧 Informe interno de administración enviado por correo.")

        st.success("✅ Cálculo e interpretación completados.")

    # ══════════════════════════════════════════════════════
    # PASO 5 — GESTIÓN DE PROYECTO (cronograma + curva S)
    # ══════════════════════════════════════════════════════
    st.header("5. Gestión de proyecto")
    if st.session_state.calc_results:
        st.caption("Cronograma y curva S generados automáticamente según el proyecto "
                   "(escalados por NS y por los hallazgos del análisis). Ajusta duraciones "
                   "y pesos si lo necesitas — la curva S se recalcula sola.")

        if "sched_start" not in st.session_state:
            st.session_state["sched_start"] = date.today()

        gc1, gc2 = st.columns([1, 2])
        start = gc1.date_input("Fecha de inicio del proyecto", key="sched_start")

        # Editor de actividades (nombre bloqueado; duración y peso editables)
        sched_rows = st.session_state.get("sched_rows", [])
        if sched_rows:
            edited = st.data_editor(
                pd.DataFrame(sched_rows),
                use_container_width=True, hide_index=True, num_rows="fixed",
                disabled=["Actividad"], key="sched_editor",
            )
            st.session_state["sched_rows"] = edited.to_dict("records")

            custom = [{"nombre": r["Actividad"],
                       "duracion": r.get("Duración (d)", 1),
                       "peso":     r.get("Peso (%)", 1)}
                      for r in st.session_state["sched_rows"]]
            sched = build_schedule(int(st.session_state.ns), start, {}, custom_rows=custom)
            st.session_state.calc_results["schedule"] = sched

            m1, m2, m3 = st.columns(3)
            m1.metric("Duración total", f"{sched['total_dias']} días")
            m2.metric("Inicio",       sched["start_date"].strftime("%d/%m/%Y"))
            m3.metric("Fin estimado", sched["fecha_fin"].strftime("%d/%m/%Y"))

            components.html(
                '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
                + schedule_svg(sched) + '</body></html>',
                height=140 + len(sched["activities"]) * 22 + 200,
                scrolling=False,
            )
    else:
        st.info("Realiza el cálculo primero para generar el cronograma.")

    # ══════════════════════════════════════════════════════
    # PASO 6 — INFORME DEL CLIENTE  (solo propietario / administrador)
    # ══════════════════════════════════════════════════════
    if not can_reports(_ROL):
        st.header("6. Informe del cliente")
        st.caption("🔒 La descarga de informes está disponible para administración "
                   "(propietario / administrador).")
    else:
        st.header("6. Informe del cliente")
        st.caption("Informe profesional para entregar al cliente (solución final, diagramas e "
                   "instrucciones de implementación). El informe técnico interno se envía "
                   "automáticamente por correo a administración.")

        if st.session_state.calc_results:
            r          = st.session_state.calc_results
            interp     = r.get("interpretation") or {}
            interp_usr = r.get("interpretation_user") or {}
            if not interp_usr.get("_ok"):
                st.error(
                    "🚫 **No se puede generar el informe sin la interpretación IA.**\n\n"
                    f"Motivo: {interp_usr.get('_error', interp.get('_error', 'no disponible'))}.\n\n"
                    "Configura `ANTHROPIC_API_KEY` en los Secrets de Streamlit Cloud y vuelve a calcular."
                )
            elif st.button("📄 Generar informe del cliente", use_container_width=True):
                with st.spinner("Generando informe del cliente..."):
                    user_pdf = generate_user_report(
                        project_params      = r["all_params"],
                        calculated          = r["limits"],
                        optimizer_result    = r["optimizer_result"],
                        lim_map             = r["lim_map"],
                        survey_cols         = SURVEY_COLS,
                        interpretation_user = r.get("interpretation_user"),
                        schedule            = r.get("schedule"),
                        plumb               = r.get("plumb"),
                    )
                proj = (r["all_params"].get("PROYECTO") or "cliente").replace(" ", "_")
                st.download_button(
                    label     = "⬇️ Descargar informe del cliente",
                    data      = user_pdf,
                    file_name = f"informe_{proj}.pdf",
                    mime      = "application/pdf",
                    use_container_width=True
                )
        else:
            st.info("Realiza el cálculo primero para poder generar el informe.")

    # ══════════════════════════════════════════════════════
    # PASO 7 — GUARDAR COMO PROYECTO  (solo administrador / propietario)
    # ══════════════════════════════════════════════════════
    if _ROL in ("administrador", "propietario"):
        st.header("7. Guardar como proyecto")
        if not st.session_state.get("calc_results"):
            st.info("Calcula primero: el proyecto se inicia con este survey.")
        elif not projects_data.is_configured():
            st.caption("🔒 Requiere Google Sheets configurado para guardar proyectos.")
        elif not _GRUPO:
            st.caption("🔒 Tu cuenta no tiene grupo asignado; no se pueden crear proyectos.")
        else:
            r  = st.session_state.calc_results
            ap = r["all_params"]
            _campos = []
            try:
                from core.auth import list_users
                _campos = [u["Usuario"] for u in list_users(_GRUPO)
                           if str(u.get("Rol", "")) == "campo"]
            except Exception:
                pass
            with st.form("save_project"):
                st.caption("Se guarda el survey completo (parámetros, matriz, interpretaciones "
                           "y cronograma). El avance lo alimentará el equipo de campo.")
                pc1, pc2 = st.columns(2)
                pj_nom = pc1.text_input("Nombre del proyecto", value=ap.get("PROYECTO", ""))
                pj_cli = pc2.text_input("Cliente")
                pj_ubi = pc1.text_input("Ubicación")
                pj_mod = pc2.text_input("Modelo de elevador")
                pj_ing = pc1.text_input("Ingeniero", value=ap.get("INGENIERO", ""))
                pj_asg = st.multiselect("Usuarios de campo asignados", _campos)
                if st.form_submit_button("💾 Guardar como proyecto", use_container_width=True):
                    if not pj_nom.strip():
                        st.error("El nombre del proyecto es obligatorio.")
                    else:
                        sched = r.get("schedule") or {}
                        _sd = sched.get("start_date"); _ff = sched.get("fecha_fin")
                        matriz = (r["survey_orig"].to_dict("records")
                                  if hasattr(r.get("survey_orig"), "to_dict") else [])
                        ok, res = projects_data.create_project(
                            grupo=_GRUPO, nombre=pj_nom.strip(), cliente=pj_cli,
                            ubicacion=pj_ubi, modelo=pj_mod, ns=int(ap.get("NS", 0) or 0),
                            ingeniero=pj_ing, campo_asignados=pj_asg,
                            fecha_inicio=(_sd.strftime("%Y-%m-%d") if _sd else ""),
                            fecha_fin_est=(_ff.strftime("%Y-%m-%d") if _ff else ""),
                            params=ap, matriz=matriz,
                            interp={"admin": r.get("interpretation"),
                                    "user":  r.get("interpretation_user")},
                            activities=sched.get("activities", []),
                            creado_por=st.session_state.auth.get("usuario", ""),
                        )
                        if ok:
                            st.success(f"✅ Proyecto **{res}** guardado. "
                                       "Gestiónalo en 🛠 Mi grupo → Proyectos.")
                        else:
                            st.error(f"No se pudo guardar: {res}")


elif _seccion == _L_PLUMB:
    from core.plumb_ui import render_plumb_tab
    render_plumb_tab()

elif _seccion == _L_RAIL:
    from core.rail_cut_ui import render_rail_cut_tab
    render_rail_cut_tab()

elif _seccion == _L_CLOCK:
    from core.timeclock_ui import render_timeclock_tab
    render_timeclock_tab()

elif _seccion == _L_FIELDPROJ:
    from core.projects_ui import render_field_projects
    render_field_projects(st.session_state.auth.get("usuario", ""), _GRUPO)

elif _seccion == _L_OWNER:
    render_owner_panel()

elif _seccion == _L_GRUPO:
    render_group_panel(_GRUPO)
