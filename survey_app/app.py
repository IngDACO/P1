import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from extractors.schindler import extract_from_pdf, PARAMS as PDF_PARAMS, PARAM_DESCRIPTIONS
from core.calculations import calculate_limits, apply_offsets, analyze_matrix
from core.optimizer import optimize
from core.bs_logic import find_bs_step
from core.report import generate_report
from core.excel_io import export_survey_excel, import_survey_excel

st.set_page_config(page_title="Survey Analyzer", layout="wide", page_icon="📐")

SURVEY_COLS = ["WR", "FR", "OR", "WL", "FL", "OL"]
USER_ONLY   = {
    "BSR":   "Ancho real del hueco medido en obra (mm)",
    "BC":    "Distancia buffer a cabina (mm)",
    "FS":    "Distancia frontal de seguridad (mm)",
    "FRAME": "Marco de puerta de entrada (mm)",
    "RAIL":  "Ancho de la cabeza del riel (mm)",
}

# ══════════════════════════════════════════════════════
# SESSION STATE — inicializar UNA sola vez
# ══════════════════════════════════════════════════════
def _init_state():
    defaults = {
        "pdf_extracted":  {},
        "last_pdf_name":  None,
        "pdf_vals":       {p: 0.0 for p in PDF_PARAMS},
        "user_vals":      {p: 0.0 for p in USER_ONLY},
        "ns":             6,
        "survey_df":      pd.DataFrame({c: [0.0]*6 for c in SURVEY_COLS}),
        "calc_results":   None,
        "excel_loaded":   False,   # flag para forzar update del editor
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ══════════════════════════════════════════════════════
# SIDEBAR — valores extraídos del PDF
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📋 Valores extraídos del PDF")
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
            desc = PARAM_DESCRIPTIONS.get(k,"")
            if desc:
                st.caption(desc)
    else:
        st.info("Carga un PDF para ver los valores aquí.")
    st.markdown("---")
    st.caption("🔴 Rojo oscuro = mínimo fuera de límite")
    st.caption("🔴 Rojo claro  = fuera de límite")

# ══════════════════════════════════════════════════════
# TÍTULO
# ══════════════════════════════════════════════════════
st.title("📐 Elevator Survey Analyzer")

# ══════════════════════════════════════════════════════
# PASO 1 — CARGAR PDF
# ══════════════════════════════════════════════════════
st.header("1. Cargar planos")
col_brand, col_pdf = st.columns([1, 3])
brand    = col_brand.selectbox("Marca", ["Schindler"])
pdf_file = col_pdf.file_uploader("PDF de planos", type=["pdf"])

if pdf_file is not None and pdf_file.name != st.session_state.last_pdf_name:
    with st.spinner("⏳ Extrayendo datos del PDF..."):
        extracted = extract_from_pdf(pdf_file)
    st.session_state.pdf_extracted = extracted
    st.session_state.last_pdf_name = pdf_file.name

    # ── CRÍTICO: poblar pdf_vals con los valores encontrados ──
    for p in PDF_PARAMS:
        if extracted.get(p) is not None:
            st.session_state.pdf_vals[p] = float(extracted[p])

    found   = sum(1 for v in extracted.values() if v is not None)
    missing = [k for k,v in extracted.items() if v is None]
    st.success(f"✅ {found}/{len(extracted)} parámetros encontrados.")
    if missing:
        st.warning(f"⚠️ Ingresar manualmente: **{', '.join(missing)}**")

elif pdf_file and pdf_file.name == st.session_state.last_pdf_name:
    st.info(f"📄 Datos de: **{pdf_file.name}** — ver sidebar.")

# ══════════════════════════════════════════════════════
# PASO 2 — PARÁMETROS
# ══════════════════════════════════════════════════════
st.header("2. Parámetros del proyecto")

# Callbacks para guardar cambios en session_state sin rerenderizar
def _update_pdf_val(key):
    st.session_state.pdf_vals[key] = st.session_state[f"inp_{key}"]

def _update_user_val(key):
    st.session_state.user_vals[key] = st.session_state[f"inp_{key}"]

with st.expander("📄 Parámetros del PDF (editables)", expanded=True):
    for i in range(0, len(PDF_PARAMS), 4):
        row_params = PDF_PARAMS[i:i+4]
        cols = st.columns(4)
        for j, p in enumerate(row_params):
            cols[j].number_input(
                label    = p,
                value    = float(st.session_state.pdf_vals.get(p, 0.0)),
                step     = 0.5,
                help     = PARAM_DESCRIPTIONS.get(p, ""),
                key      = f"inp_{p}",
                on_change= _update_pdf_val,
                args     = (p,)
            )

with st.expander("✏️ Parámetros del usuario", expanded=True):
    cols = st.columns(len(USER_ONLY))
    for j, (p, desc) in enumerate(USER_ONLY.items()):
        cols[j].number_input(
            label    = p,
            value    = float(st.session_state.user_vals.get(p, 0.0)),
            step     = 0.5,
            help     = desc,
            key      = f"inp_{p}",
            on_change= _update_user_val,
            args     = (p,)
        )

st.subheader("Configuración")
c1, c2 = st.columns(2)
omega_side = c1.radio("Lado del Omega", ["R","L"], horizontal=True)
wall_yn    = c2.radio("¿Hay pared limitante?", ["N","Y"], horizontal=True)

wall_stop, wall_side = None, None
if wall_yn == "Y":
    wc1, wc2  = st.columns(2)
    wall_stop = wc1.number_input("Parada limitante", min_value=1, step=1, value=1)
    wall_side = wc2.radio("Lado de la pared", ["R","L"], horizontal=True)

# ══════════════════════════════════════════════════════
# PASO 3 — MATRIZ SURVEY
# ══════════════════════════════════════════════════════
st.header("3. Matriz SURVEY")

sc1, sc2, sc3 = st.columns([1, 2, 2])

# Número de paradas
ns = sc1.number_input(
    "Número de paradas (NS)", min_value=2, max_value=50,
    value=st.session_state.ns, step=1, key="ns_input"
)

# Si NS cambió, ajustar tamaño del dataframe
if int(ns) != len(st.session_state.survey_df):
    old_df = st.session_state.survey_df
    new_df = pd.DataFrame({c: [0.0]*int(ns) for c in SURVEY_COLS})
    # Preservar filas existentes
    rows_to_keep = min(len(old_df), int(ns))
    new_df.iloc[:rows_to_keep] = old_df.iloc[:rows_to_keep].values
    st.session_state.survey_df = new_df
    st.session_state.ns = int(ns)
    st.rerun()

# Cargar desde Excel
uploaded_excel = sc2.file_uploader("📂 Cargar matriz (.xlsx)", type=["xlsx"], key="excel_uploader")
if uploaded_excel is not None:
    try:
        imported = import_survey_excel(uploaded_excel)
        # Ajustar NS si el Excel tiene diferente cantidad de filas
        st.session_state.survey_df = imported
        st.session_state.ns = len(imported)
        st.session_state.excel_loaded = True
        st.rerun()   # forzar rerender del data_editor con los nuevos datos
    except Exception as e:
        sc2.error(f"Error al leer Excel: {e}")

if st.session_state.excel_loaded:
    sc2.success("✅ Matriz cargada desde Excel.")
    st.session_state.excel_loaded = False

# ── Data editor vinculado al session_state ──
st.caption("Ingresa o edita las medidas en campo (mm).")

edited_df = st.data_editor(
    st.session_state.survey_df.copy(),
    use_container_width=True,
    num_rows="fixed",
    key="survey_editor"
)

# Guardar cambios del editor en session_state inmediatamente
st.session_state.survey_df = edited_df

# Botón guardar Excel
all_params_for_info = {**st.session_state.pdf_vals, **st.session_state.user_vals}
excel_bytes = export_survey_excel(edited_df, all_params_for_info)
sc3.download_button(
    label     = "💾 Guardar matriz (.xlsx)",
    data      = excel_bytes,
    file_name = "survey_matrix.xlsx",
    mime      = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)

# ══════════════════════════════════════════════════════
# PASO 4 — CALCULAR
# ══════════════════════════════════════════════════════
st.header("4. Cálculo y Optimización")

if st.button("🚀 Calcular", type="primary", use_container_width=True):

    # Tomar valores directamente del session_state (ya actualizados)
    all_params = {**st.session_state.pdf_vals, **st.session_state.user_vals}
    all_params["OMEGA_SIDE"]    = omega_side
    all_params["WALL_LIMITING"] = (wall_yn == "Y")
    all_params["WALL_STOP"]     = wall_stop
    all_params["WALL_SIDE"]     = wall_side

    # Totales = última fila
    last = st.session_state.survey_df.iloc[-1]
    for col in SURVEY_COLS:
        all_params[f"{col[0]}{col[1]}T"] = last[col]

    try:
        limits = calculate_limits(all_params)
    except Exception as e:
        st.error(f"Error en cálculo de límites: {e}")
        st.stop()

    all_params.update(limits)

    with st.expander("📊 Parámetros calculados", expanded=False):
        st.dataframe(
            pd.DataFrame([{"Parámetro":k,"Valor":round(v,3)} for k,v in limits.items()]),
            use_container_width=True, hide_index=True
        )

    # Matriz ajustada
    survey_adj    = apply_offsets(st.session_state.survey_df.to_dict("records"), limits)
    survey_adj_df = pd.DataFrame(survey_adj)
    analysis      = analyze_matrix(survey_adj, limits)
    all_params.update(analysis)
    limits.update(analysis)

    lim_map  = {c: limits[f"LIMIT_{c}"] for c in SURVEY_COLS}
    min_vals = {f"MIN_{c}": analysis[f"MIN_{c}"] for c in SURVEY_COLS}

    def highlight(df, lm, mv):
        styles = pd.DataFrame("", index=df.index, columns=df.columns)
        for col in df.columns:
            lim     = lm.get(col, 9999)
            min_val = mv.get(f"MIN_{col}")
            for idx in df.index:
                v = df.at[idx, col]
                if min_val is not None and abs(v - min_val) < 0.001 and v < lim:
                    styles.at[idx,col] = "background-color:#c0392b;color:white;font-weight:bold"
                elif v < lim:
                    styles.at[idx,col] = "background-color:#f1948a"
        return styles

    st.subheader("Matriz SURVEY ajustada")
    st.dataframe(
        survey_adj_df.style.apply(lambda df: highlight(df, lim_map, min_vals), axis=None),
        use_container_width=True
    )

    st.subheader("Resumen por columna")
    summary = []
    for col in SURVEY_COLS:
        summary.append({
            "Columna":        col,
            "Límite (mm)":    round(lim_map[col], 2),
            "Fuera límite":   analysis[f"{col}_OFF_COUNT"],
            "Mínimo (mm)":    round(analysis[f"MIN_{col}"], 2),
            "Diferencia(mm)": round(analysis[f"DIF_{col}"], 2),
        })
    st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)
    st.info(
        f"**MAX OFF RL:** {analysis['MAX_OFF_RL']:.2f} mm  |  "
        f"**MAX OFF FB:** {analysis['MAX_OFF_FB']:.2f} mm"
    )

    # Optimización
    st.subheader("🔍 Optimización")
    with st.spinner("Buscando combinación óptima..."):
        best = optimize(survey_adj, limits, all_params)

    if best:
        st.success(
            f"✅ **RL = {best['rl']} mm**  |  **FB = {best['fb']} mm**  |  "
            f"Fuera de límite: **{best['total_off']}**"
        )
        best_df  = pd.DataFrame(best["matrix"])
        best_min = {f"MIN_{c}": min(best_df[c]) for c in SURVEY_COLS}
        st.markdown("**Matriz solución:**")
        st.dataframe(
            best_df.style.apply(lambda df: highlight(df, lim_map, best_min), axis=None),
            use_container_width=True
        )
        final_sum = []
        for col in SURVEY_COLS:
            col_vals = [r[col] for r in best["matrix"]]
            final_sum.append({
                "Columna":       col,
                "Límite (mm)":   round(lim_map[col], 2),
                "Fuera límite":  sum(1 for v in col_vals if v < lim_map[col]),
                "Mínimo (mm)":   round(min(col_vals), 2),
                "Dif vs Límite": round(lim_map[col] - min(col_vals), 2),
            })
        st.dataframe(pd.DataFrame(final_sum), use_container_width=True, hide_index=True)
    else:
        st.error("No se encontró combinación válida.")
        best = None

    # BSR vs BS
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

    # Guardar resultados para el reporte
    st.session_state.calc_results = {
        "all_params":  all_params,
        "limits":      limits,
        "survey_orig": st.session_state.survey_df.copy(),
        "survey_adj":  survey_adj_df,
        "lim_map":     lim_map,
        "analysis":    analysis,
        "best":        best,
        "bs_result":   bs_result,
    }
    st.success("✅ Cálculo completado.")

# ══════════════════════════════════════════════════════
# PASO 5 — REPORTE PDF
# ══════════════════════════════════════════════════════
st.header("5. Reporte")

if st.session_state.calc_results:
    r = st.session_state.calc_results
    if st.button("📄 Generar reporte PDF", use_container_width=True):
        with st.spinner("Generando reporte..."):
            pdf_bytes = generate_report(
                project_params  = r["all_params"],
                calculated      = r["limits"],
                survey_original = r["survey_orig"],
                survey_adjusted = r["survey_adj"],
                lim_map         = r["lim_map"],
                analysis        = r["analysis"],
                best            = r["best"],
                bs_result       = r["bs_result"],
                survey_cols     = SURVEY_COLS,
            )
        st.download_button(
            label     = "⬇️ Descargar reporte PDF",
            data      = pdf_bytes,
            file_name = "survey_report.pdf",
            mime      = "application/pdf",
            use_container_width=True
        )
else:
    st.info("Realiza el cálculo primero para poder generar el reporte.")
