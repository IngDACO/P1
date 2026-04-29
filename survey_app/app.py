import streamlit as st
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from extractors.schindler import extract_from_pdf
from core.calculations import calculate_limits, apply_offsets, analyze_matrix
from core.optimizer import optimize
from core.bs_logic import find_bs_step

st.set_page_config(page_title="Survey Analyzer", layout="wide")
st.title("📐 Elevator Survey Analyzer")

# ─────────────────────────────────────────────
# PASO 1 — CARGAR PDF Y EXTRAER DATOS
# ─────────────────────────────────────────────
st.header("1. Datos del Proyecto")

brand = st.selectbox("Marca del elevador", ["Schindler"])  # futuro: Otis, Kone...
pdf_file = st.file_uploader("Cargar PDF de planos", type=["pdf"])

pdf_params = {}
if pdf_file:
    with st.spinner("Extrayendo datos del PDF..."):
        pdf_params = extract_from_pdf(pdf_file)
    found   = {k: v for k, v in pdf_params.items() if v is not None}
    missing = [k for k, v in pdf_params.items() if v is None]
    st.success(f"✅ Se encontraron {len(found)} parámetros en el PDF.")
    if missing:
        st.warning(f"⚠️ No se encontraron: {', '.join(missing)}. Por favor ingresarlos abajo.")

# ─────────────────────────────────────────────
# PASO 2 — FORMULARIO DE PARÁMETROS
# ─────────────────────────────────────────────
st.subheader("Parámetros del proyecto")

PDF_PARAMS = ["BS","BT","BK","BKS","TK","TKA","TKS","TSW","TKSW","TS","SF1","SF2","SG","TG","BGS","BKF1","BKF2"]
USER_PARAMS = ["BSR","BC","FS","FRAME","RAIL"]

def get_val(key):
    return pdf_params.get(key) or 0.0

with st.expander("📋 Parámetros extraídos del PDF (editar si es necesario)", expanded=True):
    cols_per_row = 4
    pdf_values = {}
    param_list = PDF_PARAMS
    for i in range(0, len(param_list), cols_per_row):
        row_params = param_list[i:i+cols_per_row]
        cols = st.columns(cols_per_row)
        for j, p in enumerate(row_params):
            default = get_val(p)
            pdf_values[p] = cols[j].number_input(
                p, value=float(default), step=0.5, key=f"pdf_{p}"
            )

with st.expander("✏️ Parámetros ingresados por el usuario", expanded=True):
    cols = st.columns(len(USER_PARAMS))
    user_values = {}
    for j, p in enumerate(USER_PARAMS):
        user_values[p] = cols[j].number_input(p, value=0.0, step=0.5, key=f"user_{p}")

# Lado del omega
st.subheader("Configuración")
col1, col2 = st.columns(2)
omega_side = col1.radio("¿Dónde está el Omega?", ["R", "L"], horizontal=True)
wall_yn    = col2.radio("¿Hay pared limitante?", ["N", "Y"], horizontal=True)

wall_stop = None
wall_side = None
if wall_yn == "Y":
    wc1, wc2 = st.columns(2)
    wall_stop = wc1.number_input("Parada de la pared limitante", min_value=1, step=1, value=1)
    wall_side = wc2.radio("Lado de la pared limitante", ["R", "L"], horizontal=True)

# ─────────────────────────────────────────────
# PASO 3 — MATRIZ SURVEY
# ─────────────────────────────────────────────
st.header("2. Matriz SURVEY")
ns = st.number_input("Número de paradas (NS)", min_value=2, max_value=50, value=6, step=1)

survey_cols = ["WR", "FR", "OR", "WL", "FL", "OL"]
default_data = {col: [0.0] * int(ns) for col in survey_cols}
survey_df = pd.DataFrame(default_data)

st.markdown("Ingresa las medidas tomadas en campo (mm):")
edited_df = st.data_editor(
    survey_df,
    use_container_width=True,
    num_rows="fixed",
    key="survey_editor"
)

# ─────────────────────────────────────────────
# PASO 4 — CALCULAR
# ─────────────────────────────────────────────
st.header("3. Cálculo y Optimización")

if st.button("🚀 Calcular", type="primary", use_container_width=True):

    # Armar diccionario de parámetros completo
    all_params = {**pdf_values, **user_values}
    all_params["OMEGA_SIDE"] = omega_side
    all_params["WALL_LIMITING"] = (wall_yn == "Y")
    all_params["WALL_STOP"] = wall_stop
    all_params["WALL_SIDE"] = wall_side

    # Totales de la última fila
    last = edited_df.iloc[-1]
    all_params["WRT"] = last["WR"]
    all_params["FRT"] = last["FR"]
    all_params["ORT"] = last["OR"]
    all_params["WLT"] = last["WL"]
    all_params["FLT"] = last["FL"]
    all_params["OLT"] = last["OL"]

    # Calcular límites y offsets
    limits_and_derived = calculate_limits(all_params)
    all_params.update(limits_and_derived)

    # Mostrar parámetros calculados
    with st.expander("📊 Parámetros calculados", expanded=False):
        calc_df = pd.DataFrame([
            {"Parámetro": k, "Valor": round(v, 3)}
            for k, v in limits_and_derived.items()
        ])
        st.dataframe(calc_df, use_container_width=True, hide_index=True)

    # Aplicar offsets a la matriz
    survey_list = edited_df.to_dict(orient="records")
    survey_adj  = apply_offsets(survey_list, limits_and_derived)
    survey_adj_df = pd.DataFrame(survey_adj)

    # Analizar matriz ajustada
    analysis = analyze_matrix(survey_adj, limits_and_derived)
    all_params.update(analysis)
    limits_and_derived.update(analysis)

    st.subheader("Matriz SURVEY Ajustada")
    lim_map = {
        "WR": limits_and_derived["LIMIT_WR"],
        "FR": limits_and_derived["LIMIT_FR"],
        "OR": limits_and_derived["LIMIT_OR"],
        "WL": limits_and_derived["LIMIT_WL"],
        "FL": limits_and_derived["LIMIT_FL"],
        "OL": limits_and_derived["LIMIT_OL"],
    }

    def highlight_matrix(df, lim_map, min_vals):
        styles = pd.DataFrame("", index=df.index, columns=df.columns)
        for col in df.columns:
            lim     = lim_map[col]
            min_val = min_vals[f"MIN_{col}"]
            for idx in df.index:
                val = df.at[idx, col]
                if val == min_val and val < lim:
                    styles.at[idx, col] = "background-color: #ff4444; color: white; font-weight: bold"
                elif val < lim:
                    styles.at[idx, col] = "background-color: #ffcccc"
        return styles

    min_vals = {f"MIN_{c}": analysis[f"MIN_{c}"] for c in survey_cols}
    styled = survey_adj_df.style.apply(
        lambda df: highlight_matrix(df, lim_map, min_vals), axis=None
    )
    st.dataframe(styled, use_container_width=True)

    # Resumen de off-limits
    st.subheader("Resumen de valores fuera de límite")
    summary_data = []
    for col in survey_cols:
        summary_data.append({
            "Columna": col,
            "Límite": round(lim_map[col], 2),
            "Fuera de límite": analysis[f"{col}_OFF_COUNT"],
            "Mínimo": round(analysis[f"MIN_{col}"], 2),
            "Diferencia": round(analysis[f"DIF_{col}"], 2),
        })
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)

    st.info(f"**MAX OFF RL:** {round(analysis['MAX_OFF_RL'], 2)} mm  |  **MAX OFF FB:** {round(analysis['MAX_OFF_FB'], 2)} mm")

    # ── Optimización ──
    st.subheader("🔍 Optimización")
    with st.spinner("Buscando combinación óptima..."):
        best = optimize(survey_adj, limits_and_derived, all_params)

    if best:
        st.success(f"✅ Mejor combinación: RL = {best['rl']} mm | FB = {best['fb']} mm | Valores fuera de límite: {best['total_off']}")

        best_df = pd.DataFrame(best["matrix"])
        styled_best = best_df.style.apply(
            lambda df: highlight_matrix(df, lim_map, {
                f"MIN_{c}": min(best_df[c]) for c in survey_cols
            }), axis=None
        )
        st.markdown("**Matriz solución:**")
        st.dataframe(styled_best, use_container_width=True)

        # Resumen final
        final_summary = []
        for col in survey_cols:
            col_vals = [r[col] for r in best["matrix"]]
            min_v    = min(col_vals)
            off_c    = sum(1 for v in col_vals if v < lim_map[col])
            final_summary.append({
                "Columna": col,
                "Límite": round(lim_map[col], 2),
                "Fuera de límite": off_c,
                "Mínimo": round(min_v, 2),
                "Diferencia vs Límite": round(lim_map[col] - min_v, 2),
            })
        st.dataframe(pd.DataFrame(final_summary), use_container_width=True, hide_index=True)
    else:
        st.error("No se encontró combinación válida.")

    # ── Lógica BSR vs BS ──
    st.subheader("📏 Análisis BSR vs BS")
    bs_result = find_bs_step(
        all_params["BSR"], all_params["BS"],
        limits_and_derived["LIMIT_ZB"], limits_and_derived["LIMIT_OB"]
    )
    if not bs_result["needed"]:
        st.success("BSR ≥ BS: No se requiere ajuste.")
    elif bs_result["step"] is None:
        st.error(f"No se encontró paso en ningún rango. DIF BS = {bs_result['dif_original']} mm")
    else:
        st.success(
            f"✅ Paso encontrado: **{bs_result['step']} mm**  |  "
            f"Rango: **{bs_result['range']}**  |  "
            f"Zona: **{bs_result['range_name']}**"
        )

