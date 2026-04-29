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

# ══════════════════════════════════════════════════════
# SESSION STATE — inicializar
# ══════════════════════════════════════════════════════
if "pdf_extracted"  not in st.session_state: st.session_state.pdf_extracted  = {}
if "last_pdf_name"  not in st.session_state: st.session_state.last_pdf_name  = None
if "survey_df"      not in st.session_state: st.session_state.survey_df      = None
if "calc_results"   not in st.session_state: st.session_state.calc_results   = None

SURVEY_COLS  = ["WR", "FR", "OR", "WL", "FL", "OL"]
USER_ONLY    = {
    "BSR":   "Ancho real del hueco medido en obra (mm)",
    "BC":    "Distancia buffer a cabina (mm)",
    "FS":    "Distancia frontal de seguridad (mm)",
    "FRAME": "Marco de puerta de entrada (mm)",
    "RAIL":  "Ancho de la cabeza del riel (mm)",
}

# ══════════════════════════════════════════════════════
# SIDEBAR — valores extraídos del PDF
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📋 Valores del PDF")
    if st.session_state.pdf_extracted:
        found   = {k:v for k,v in st.session_state.pdf_extracted.items() if v is not None}
        missing = [k for k,v in st.session_state.pdf_extracted.items() if v is None]

        st.markdown(f"**Archivo:** `{st.session_state.last_pdf_name}`")
        st.markdown(f"✅ Encontrados: **{len(found)}** / {len(st.session_state.pdf_extracted)}")
        if missing:
            st.markdown(f"⚠️ Faltantes: `{'`, `'.join(missing)}`")
        st.markdown("---")

        for k, v in sorted(found.items()):
            desc = PARAM_DESCRIPTIONS.get(k, "")
            st.markdown(f"**{k}** = `{v:.0f}` mm")
            if desc:
                st.caption(desc)
    else:
        st.info("Carga un PDF de planos para ver los valores extraídos aquí.")

    st.markdown("---")
    st.markdown("## ℹ️ Ayuda")
    st.caption("🔴 Rojo oscuro = valor mínimo fuera de límite")
    st.caption("🔴 Rojo claro  = valor fuera de límite")
    st.caption("Los offsets se calculan automáticamente al presionar **Calcular**.")

# ══════════════════════════════════════════════════════
# MAIN — título
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
    found   = sum(1 for v in extracted.values() if v is not None)
    missing = [k for k,v in extracted.items() if v is None]
    st.success(f"✅ {found}/{len(extracted)} parámetros encontrados. "
               f"{'Revisa el sidebar para ver los valores.' if found else ''}")
    if missing:
        st.warning(f"⚠️ No encontrados (ingrésalos abajo): **{', '.join(missing)}**")
elif pdf_file and pdf_file.name == st.session_state.last_pdf_name:
    st.info(f"📄 Datos ya extraídos de: **{pdf_file.name}** — revisa el sidebar.")

# ══════════════════════════════════════════════════════
# PASO 2 — PARÁMETROS
# ══════════════════════════════════════════════════════
st.header("2. Parámetros del proyecto")

with st.expander("📄 Parámetros del PDF (editar si es necesario)", expanded=True):
    pdf_vals = {}
    for i in range(0, len(PDF_PARAMS), 4):
        row_params = PDF_PARAMS[i:i+4]
        cols = st.columns(4)
        for j, p in enumerate(row_params):
            default = float(st.session_state.pdf_extracted.get(p) or 0.0)
            pdf_vals[p] = cols[j].number_input(
                p, value=default, step=0.5,
                help=PARAM_DESCRIPTIONS.get(p,""), key=f"pdf_{p}"
            )

with st.expander("✏️ Parámetros del usuario", expanded=True):
    user_vals = {}
    cols = st.columns(len(USER_ONLY))
    for j, (p, desc) in enumerate(USER_ONLY.items()):
        user_vals[p] = cols[j].number_input(p, value=0.0, step=0.5,
                                             help=desc, key=f"usr_{p}")

st.subheader("Configuración")
c1, c2 = st.columns(2)
omega_side = c1.radio("Lado del Omega (bracket estructural)", ["R","L"], horizontal=True)
wall_yn    = c2.radio("¿Hay pared limitante?", ["N","Y"], horizontal=True)

wall_stop, wall_side = None, None
if wall_yn == "Y":
    wc1, wc2 = st.columns(2)
    wall_stop = wc1.number_input("Parada limitante (número)", min_value=1, step=1, value=1)
    wall_side = wc2.radio("Lado de la pared", ["R","L"], horizontal=True)

# ══════════════════════════════════════════════════════
# PASO 3 — MATRIZ SURVEY
# ══════════════════════════════════════════════════════
st.header("3. Matriz SURVEY")

sc1, sc2, sc3 = st.columns([1,2,2])
ns = sc1.number_input("Número de paradas (NS)", min_value=2, max_value=50, value=6, step=1)

# Cargar desde Excel
uploaded_excel = sc2.file_uploader("📂 Cargar matriz guardada (.xlsx)", type=["xlsx"])
if uploaded_excel:
    try:
        imported = import_survey_excel(uploaded_excel)
        st.session_state.survey_df = imported
        sc2.success("✅ Matriz cargada correctamente.")
    except Exception as e:
        sc2.error(f"Error al leer Excel: {e}")

# Inicializar o usar guardada
if st.session_state.survey_df is None or len(st.session_state.survey_df) != int(ns):
    st.session_state.survey_df = pd.DataFrame({c: [0.0]*int(ns) for c in SURVEY_COLS})

st.caption("Ingresa o edita las medidas en campo (mm). Los cambios se guardan en sesión.")
edited_df = st.data_editor(
    st.session_state.survey_df,
    use_container_width=True,
    num_rows="fixed",
    key="survey_editor"
)
st.session_state.survey_df = edited_df

# Guardar Excel
all_params_for_info = {**pdf_vals, **user_vals}
excel_bytes = export_survey_excel(edited_df, all_params_for_info)
sc3.download_button(
    label="💾 Guardar matriz como Excel",
    data=excel_bytes,
    file_name="survey_matrix.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# ══════════════════════════════════════════════════════
# PASO 4 — CALCULAR
# ══════════════════════════════════════════════════════
st.header("4. Cálculo y Optimización")

if st.button("🚀 Calcular", type="primary", use_container_width=True):

    all_params = {**pdf_vals, **user_vals}
    all_params["OMEGA_SIDE"]    = omega_side
    all_params["WALL_LIMITING"] = (wall_yn == "Y")
    all_params["WALL_STOP"]     = wall_stop
    all_params["WALL_SIDE"]     = wall_side

    last = edited_df.iloc[-1]
    for col in SURVEY_COLS:
        all_params[f"{col[0]}{col[1]}T"] = last[col]

    # ── Límites ──
    try:
        limits = calculate_limits(all_params)
    except Exception as e:
        st.error(f"Error en cálculo: {e}")
        st.stop()
    all_params.update(limits)

    with st.expander("📊 Parámetros calculados", expanded=False):
        calc_df = pd.DataFrame([{"Parámetro":k,"Valor":round(v,3)} for k,v in limits.items()])
        st.dataframe(calc_df, use_container_width=True, hide_index=True)

    # ── Matriz ajustada ──
    survey_adj    = apply_offsets(edited_df.to_dict("records"), limits)
    survey_adj_df = pd.DataFrame(survey_adj)
    analysis      = analyze_matrix(survey_adj, limits)
    all_params.update(analysis)
    limits.update(analysis)

    lim_map  = {c: limits[f"LIMIT_{c}"] for c in SURVEY_COLS}
    min_vals = {f"MIN_{c}": analysis[f"MIN_{c}"] for c in SURVEY_COLS}

    def highlight(df, lim_map, min_vals):
        styles = pd.DataFrame("", index=df.index, columns=df.columns)
        for col in df.columns:
            lim     = lim_map.get(col, 9999)
            min_val = min_vals.get(f"MIN_{col}")
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
    st.info(f"**MAX OFF RL:** {analysis['MAX_OFF_RL']:.2f} mm  |  **MAX OFF FB:** {analysis['MAX_OFF_FB']:.2f} mm")

    # ── Optimización ──
    st.subheader("🔍 Optimización")
    with st.spinner("Buscando combinación óptima..."):
        best = optimize(survey_adj, limits, all_params)

    if best:
        st.success(
            f"✅ Mejor combinación:  **RL = {best['rl']} mm**  |  "
            f"**FB = {best['fb']} mm**  |  Fuera de límite: **{best['total_off']}**"
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
                "Columna":        col,
                "Límite (mm)":    round(lim_map[col], 2),
                "Fuera límite":   sum(1 for v in col_vals if v < lim_map[col]),
                "Mínimo (mm)":    round(min(col_vals), 2),
                "Dif vs Límite":  round(lim_map[col] - min(col_vals), 2),
            })
        st.dataframe(pd.DataFrame(final_sum), use_container_width=True, hide_index=True)
    else:
        st.error("No se encontró combinación válida.")
        best = None

    # ── BSR vs BS ──
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

    # ── Guardar resultados en session para reporte ──
    st.session_state.calc_results = {
        "all_params":    all_params,
        "limits":        limits,
        "survey_orig":   edited_df,
        "survey_adj":    survey_adj_df,
        "lim_map":       lim_map,
        "analysis":      analysis,
        "best":          best,
        "bs_result":     bs_result,
    }
    st.success("✅ Cálculo completado. Puedes descargar el reporte abajo.")

# ══════════════════════════════════════════════════════
# PASO 5 — REPORTE PDF
# ══════════════════════════════════════════════════════
st.header("5. Reporte")

if st.session_state.calc_results:
    r = st.session_state.calc_results
    if st.button("📄 Generar reporte PDF", use_container_width=True):
        with st.spinner("Generando reporte..."):
            pdf_bytes = generate_report(
                project_params = r["all_params"],
                calculated     = r["limits"],
                survey_original= r["survey_orig"],
                survey_adjusted= r["survey_adj"],
                lim_map        = r["lim_map"],
                analysis       = r["analysis"],
                best           = r["best"],
                bs_result      = r["bs_result"],
                survey_cols    = SURVEY_COLS,
            )
        st.download_button(
            label="⬇️ Descargar reporte PDF",
            data=pdf_bytes,
            file_name="survey_report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        st.success("✅ Reporte generado. Haz clic en el botón para descargarlo.")
else:
    st.info("Primero realiza el cálculo para poder generar el reporte.")
