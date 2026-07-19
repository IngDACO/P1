"""
UI de la pestaña de corte de buffers.
"""
import streamlit as st
import pandas as pd

from core.buffer_cut import compute_buffer_cut
from extractors.schindler import extract_hkp
from core import plan_store


def render_buffer_cut_tab():
    st.markdown("### 🛡 Corte de buffers")
    st.caption("Calcula cuánto cortar cada buffer. Carga el PDF para leer **HKP** "
               "(o ingrésalo manualmente) e indica el **HKPR** real de cada buffer.")

    # ── 1. PDF → HKP ────────────────────────────────────────
    st.markdown("**1. Parámetro del plano (HKP)**")
    pdf = plan_store.selector("PDF de planos (para HKP)", "bc_pdf")
    if pdf is not None and pdf.name != st.session_state.get("bc_pdf_name"):
        with st.spinner("Leyendo HKP del PDF..."):
            ex = extract_hkp(pdf)
        st.session_state["bc_pdf_name"] = pdf.name
        if ex.get("HKP") is not None:
            st.session_state["bc_hkp"] = float(ex["HKP"])
            st.success(f"HKP encontrado en el PDF: {ex['HKP']:.0f} mm. Verifica abajo.")
        else:
            st.warning("No se encontró HKP en el PDF. Ingrésalo manualmente.")

    hkp = st.number_input("HKP (mm) — sticker de cabina ↔ buffer sirviendo el 1er nivel",
                          value=float(st.session_state.get("bc_hkp", 0.0)),
                          step=0.5, key="bc_hkp")

    # ── 2. Nº de buffers ────────────────────────────────────
    st.markdown("**2. Buffers**")
    n = int(st.number_input("¿Cuántos buffers hay?", min_value=1, max_value=12, step=1,
                            value=int(st.session_state.get("bc_n", 1)), key="bc_n"))

    # ── 3. HKPR real de cada buffer ─────────────────────────
    st.markdown("**3. HKPR real de cada buffer (mm)**")
    base = st.session_state.get("bc_df")
    if base is None or len(base) != n:
        base = pd.DataFrame({"Buffer": [f"Buffer {i+1}" for i in range(n)],
                             "HKPR (mm)": [0.0] * n})
    edit = st.data_editor(base, use_container_width=True, hide_index=True,
                          num_rows="fixed", disabled=["Buffer"], key="bc_editor")
    st.session_state["bc_df"] = edit

    # ── 4. Calcular ─────────────────────────────────────────
    if st.button("🛡 Calcular cortes", type="primary", use_container_width=True, key="bc_calc"):
        hkpr_list = [float(x) for x in edit["HKPR (mm)"].tolist()]
        res = compute_buffer_cut(hkp, hkpr_list)
        st.success(f"HKP = {res['HKP']:.0f} mm   ·   CutBuffer = HKP − HKPR")
        rows = [{
            "Buffer":        f"Buffer {b['n']}",
            "HKPR (mm)":     round(b["HKPR"], 1),
            "Corte (mm)":    b["CutBuffer"],
            "":              "⚠️ revisar" if b["warn"] else "",
        } for b in res["buffers"]]
        st.subheader("Resultado — cortes (mm)")
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        if any(b["warn"] for b in res["buffers"]):
            st.warning("⚠️ Un corte negativo significa que el HKPR real supera al HKP del plano: "
                       "no hay nada que cortar en ese buffer, revísalo en obra.")
