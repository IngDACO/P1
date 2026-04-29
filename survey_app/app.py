import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from extractors.schindler import extract_from_pdf, PARAMS as PDF_PARAMS, PARAM_DESCRIPTIONS
from core.calculations import calculate_limits, apply_offsets, analyze_matrix
from core.optimizer import optimize
from core.bs_logic import find_bs_step

st.set_page_config(page_title="Survey Analyzer", layout="wide")
st.title("📐 Elevator Survey Analyzer")

# ══════════════════════════════════════════════
# INICIALIZAR session_state
# ══════════════════════════════════════════════
if "pdf_extracted" not in st.session_state:
    st.session_state.pdf_extracted = {}   # valores extraídos del PDF
if "last_pdf_name" not in st.session_state:
    st.session_state.last_pdf_name = None

# Parámetros que siempre ingresa el usuario (no están en el PDF)
USER_ONLY_PARAMS = {
    "BSR":   "Ancho real del hueco medido en obra",
    "BC":    "Distancia buffer a cabina",
    "FS":    "Distancia frontal de seguridad",
    "FRAME": "Marco de puerta de entrada",
    "RAIL":  "Ancho del riel (cabeza)",
}

# ══════════════════════════════════════════════
# PASO 1 — CARGAR PDF
# ══════════════════════════════════════════════
st.header("1. Cargar planos")
brand    = st.selectbox("Marca del elevador", ["Schindler"])
pdf_file = st.file_uploader("Cargar PDF de planos", type=["pdf"])

if pdf_file is not None:
    # Solo extraer si es un PDF nuevo
    if pdf_file.name != st.session_state.last_pdf_name:
        with st.spinner("⏳ Extrayendo datos del PDF..."):
            extracted = extract_from_pdf(pdf_file)
        st.session_state.pdf_extracted  = extracted
        st.session_state.last_pdf_name  = pdf_file.name

        found   = sum(1 for v in extracted.values() if v is not None)
        missing = [k for k, v in extracted.items() if v is None]
        st.success(f"✅ {found}/{len(extracted)} parámetros encontrados en el PDF.")
        if missing:
            st.warning(f"⚠️ No encontrados: {', '.join(missing)} — ingrésalos manualmente abajo.")
    else:
        st.info(f"📄 Usando datos ya extraídos de: **{pdf_file.name}**")

# ══════════════════════════════════════════════
# PASO 2 — PARÁMETROS DEL PROYECTO
# ══════════════════════════════════════════════
st.header("2. Parámetros del proyecto")

# ── Parámetros del PDF (editables) ──
st.subheader("Extraídos del PDF")
st.caption("Revisa y corrige si algún valor no es correcto.")

pdf_vals = {}
cols_per_row = 4
param_list   = list(PDF_PARAMS)

for i in range(0, len(param_list), cols_per_row):
    row_params = param_list[i:i + cols_per_row]
    cols = st.columns(cols_per_row)
    for j, p in enumerate(row_params):
        default = st.session_state.pdf_extracted.get(p) or 0.0
        label   = f"{p}"
        help_txt = PARAM_DESCRIPTIONS.get(p, "")
        pdf_vals[p] = cols[j].number_input(
            label, value=float(default), step=0.5,
            help=help_txt, key=f"pdf_{p}"
        )

# ── Parámetros del usuario ──
st.subheader("Ingresados por el usuario")
user_vals = {}
cols = st.columns(len(USER_ONLY_PARAMS))
for j, (p, desc) in enumerate(USER_ONLY_PARAMS.items()):
    user_vals[p] = cols[j].number_input(p, value=0.0, step=0.5, help=desc, key=f"usr_{p}")

# ── Configuración ──
st.subheader("Configuración")
c1, c2 = st.columns(2)
omega_side = c1.radio("¿Dónde está el Omega (bracket estructural)?", ["R", "L"], horizontal=True)
wall_yn    = c2.radio("¿Hay pared limitante?", ["N", "Y"], horizontal=True)

wall_stop, wall_side = None, None
if wall_yn == "Y":
    wc1, wc2   = st.columns(2)
    wall_stop  = wc1.number_input("Número de parada", min_value=1, step=1, value=1)
    wall_side  = wc2.radio("Lado", ["R", "L"], horizontal=True)

# ══════════════════════════════════════════════
# PASO 3 — MATRIZ SURVEY
# ══════════════════════════════════════════════
st.header("3. Matriz SURVEY")
st.caption("Medidas tomadas en campo (mm). Ingresa el número de paradas y completa la tabla.")

ns = st.number_input("Número de paradas (NS)", min_value=2, max_value=50, value=6, step=1)

survey_cols  = ["WR", "FR", "OR", "WL", "FL", "OL"]
default_data = {col: [0.0] * int(ns) for col in survey_cols}
edited_df    = st.data_editor(
    pd.DataFrame(default_data),
    use_container_width=True,
    num_rows="fixed",
    key="survey_editor"
)

# ══════════════════════════════════════════════
# PASO 4 — CALCULAR
# ══════════════════════════════════════════════
st.header("4. Cálculo y Optimización")

if st.button("🚀 Calcular", type="primary", use_container_width=True):

    # Armar diccionario completo de parámetros
    all_params = {**pdf_vals, **user_vals}
    all_params["OMEGA_SIDE"]    = omega_side
    all_params["WALL_LIMITING"] = (wall_yn == "Y")
    all_params["WALL_STOP"]     = wall_stop
    all_params["WALL_SIDE"]     = wall_side

    # Totales = última fila de la matriz
    last = edited_df.iloc[-1]
    for col in survey_cols:
        all_params[f"{col[0]}{col[1]}T"] = last[col]   # WRT, FRT, ORT, WLT, FLT, OLT

    # ── Cálculo de límites y derivados ──
    try:
        limits = calculate_limits(all_params)
    except Exception as e:
        st.error(f"Error en cálculo de límites: {e}")
        st.stop()

    all_params.update(limits)

    with st.expander("📊 Parámetros calculados", expanded=False):
        calc_df = pd.DataFrame([{"Parámetro": k, "Valor": round(v, 3)} for k, v in limits.items()])
        st.dataframe(calc_df, use_container_width=True, hide_index=True)

    # ── Aplicar offsets a la matriz ──
    survey_list = edited_df.to_dict(orient="records")
    survey_adj  = apply_offsets(survey_list, limits)
    survey_adj_df = pd.DataFrame(survey_adj)

    # ── Analizar matriz ajustada ──
    analysis = analyze_matrix(survey_adj, limits)
    all_params.update(analysis)
    limits.update(analysis)

    lim_map = {
        "WR": limits["LIMIT_WR"], "FR": limits["LIMIT_FR"],
        "OR": limits["LIMIT_OR"], "WL": limits["LIMIT_WL"],
        "FL": limits["LIMIT_FL"], "OL": limits["LIMIT_OL"],
    }

    def highlight_matrix(df, lim_map, min_vals):
        styles = pd.DataFrame("", index=df.index, columns=df.columns)
        for col in df.columns:
            lim     = lim_map[col]
            min_val = min_vals.get(f"MIN_{col}", None)
            for idx in df.index:
                val = df.at[idx, col]
                if min_val is not None and val == min_val and val < lim:
                    styles.at[idx, col] = "background-color:#c0392b;color:white;font-weight:bold"
                elif val < lim:
                    styles.at[idx, col] = "background-color:#f1948a"
        return styles

    min_vals = {f"MIN_{c}": analysis[f"MIN_{c}"] for c in survey_cols}

    st.subheader("Matriz SURVEY ajustada")
    st.dataframe(
        survey_adj_df.style.apply(
            lambda df: highlight_matrix(df, lim_map, min_vals), axis=None
        ),
        use_container_width=True
    )

    # ── Resumen ──
    st.subheader("Resumen columna por columna")
    summary = []
    for col in survey_cols:
        summary.append({
            "Columna":          col,
            "Límite (mm)":      round(lim_map[col], 2),
            "Fuera de límite":  analysis[f"{col}_OFF_COUNT"],
            "Mínimo (mm)":      round(analysis[f"MIN_{col}"], 2),
            "Diferencia (mm)":  round(analysis[f"DIF_{col}"], 2),
        })
    st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)
    st.info(f"**MAX OFF RL:** {round(analysis['MAX_OFF_RL'],2)} mm  |  **MAX OFF FB:** {round(analysis['MAX_OFF_FB'],2)} mm")

    # ── Optimización ──
    st.subheader("🔍 Optimización")
    with st.spinner("Buscando combinación óptima de desplazamientos..."):
        best = optimize(survey_adj, limits, all_params)

    if best:
        st.success(
            f"✅ Mejor combinación encontrada:  "
            f"**RL = {best['rl']} mm**  |  **FB = {best['fb']} mm**  |  "
            f"Valores fuera de límite: **{best['total_off']}**"
        )
        best_df  = pd.DataFrame(best["matrix"])
        best_min = {f"MIN_{c}": min(best_df[c]) for c in survey_cols}
        st.markdown("**Matriz solución:**")
        st.dataframe(
            best_df.style.apply(
                lambda df: highlight_matrix(df, lim_map, best_min), axis=None
            ),
            use_container_width=True
        )

        final_summary = []
        for col in survey_cols:
            col_vals = [r[col] for r in best["matrix"]]
            final_summary.append({
                "Columna":         col,
                "Límite (mm)":     round(lim_map[col], 2),
                "Fuera de límite": sum(1 for v in col_vals if v < lim_map[col]),
                "Mínimo (mm)":     round(min(col_vals), 2),
                "Dif vs Límite":   round(lim_map[col] - min(col_vals), 2),
            })
        st.dataframe(pd.DataFrame(final_summary), use_container_width=True, hide_index=True)
    else:
        st.error("No se encontró combinación válida con los criterios dados.")

    # ── BSR vs BS ──
    st.subheader("📏 Análisis BSR vs BS")
    bs_result = find_bs_step(
        all_params["BSR"], all_params["BS"],
        limits["LIMIT_ZB"], limits["LIMIT_OB"]
    )
    if not bs_result["needed"]:
        st.success("BSR ≥ BS — No se requiere ajuste de shaft.")
    elif bs_result["step"] is None:
        st.error(f"No se encontró paso en ningún rango. DIF BS = {bs_result['dif_original']} mm")
    else:
        st.success(
            f"✅ Paso encontrado: **{bs_result['step']} mm**  |  "
            f"Rango: **{bs_result['range']}**  |  Zona: **{bs_result['range_name']}**"
        )

