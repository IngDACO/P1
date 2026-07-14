"""
UI de la pestaña de Belting (herramienta independiente).
Del plano: HQ (autocompletado). Del usuario: HGP y HGPR por elevador.
DSTS = HGPR − HGP − HQ/1000 (mm), por elevador.
"""
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from core.belting import compute_belting, belting_svg


def render_belting_tab():
    st.markdown("### 🎗 Belting — posición de la cabina para instalar los belts")
    st.caption("Calcula **DSTS** = cuánto bajar la cabina bajo el FFL del piso más alto para instalar "
               "los belts respetando el recorrido de diseño.  DSTS = HGPR − HGP − HQ/1000 (mm), por elevador.")

    for k in ("belt_hgp", "belt_hq"):
        st.session_state.setdefault(k, 0.0)
    st.session_state.setdefault("belt_ns", 1)

    # ── PDF: autocompleta HQ ────────────────────────────────
    pdf = st.file_uploader("📄 PDF de planos (autocompleta HQ)", type=["pdf"], key="belt_pdf")
    if pdf is not None and pdf.name != st.session_state.get("belt_pdf_name"):
        from extractors.schindler import extract_belting
        with st.spinner("Leyendo el plano..."):
            ex = extract_belting(pdf)
        st.session_state["belt_pdf_name"] = pdf.name
        if ex.get("HQ") is not None:
            st.session_state["belt_hq"] = float(ex["HQ"])
            st.success(f"✅ HQ (travel height) = **{ex['HQ']:.0f} mm** del plano. "
                       "Ingresa HGP y los HGPR de cada elevador.")
        else:
            st.warning("No se encontró HQ en el plano. Ingrésalo a mano.")
        st.rerun()
    elif pdf is not None:
        st.caption(f"📄 Plano cargado: **{pdf.name}**")

    # ── Datos del plano ─────────────────────────────────────
    st.markdown("**Datos**  ·  📄 = del plano · ✏️ = manual")
    c1, c2 = st.columns(2)
    hq  = c1.number_input("📄 HQ — travel height (mm)", step=1.0, key="belt_hq")
    hgp = c2.number_input("✏️ HGP — striker↔buffer de diseño (mm)", step=0.5, key="belt_hgp")

    ne = st.number_input("Número de elevadores", min_value=1, max_value=12, step=1, key="belt_ns")

    st.markdown("**✏️ HGPR — distancia REAL striker↔buffer del contrapeso, por elevador (mm)**")
    hgpr_list = []
    cols = st.columns(min(int(ne), 4))
    for i in range(int(ne)):
        v = cols[i % len(cols)].number_input(f"HGPR elevador {i+1}", step=0.5, key=f"belt_hgpr_{i}")
        hgpr_list.append(v)

    # ── Cálculo ─────────────────────────────────────────────
    if st.button("🎗 Calcular belting", type="primary", use_container_width=True, key="belt_calc"):
        results = compute_belting(hgp, hq, hgpr_list)
        st.subheader("📋 Resultados (DSTS por elevador)")
        st.dataframe(pd.DataFrame([{
            "Elevador":  r["elevador"],
            "HGPR (mm)": r["hgpr"],
            "DSTS (mm)": r["dsts"],
            "Posición":  f"{abs(r['dsts']):.0f} mm {'por debajo' if r['dsts'] >= 0 else 'por encima'} del FFL top",
        } for r in results]), use_container_width=True, hide_index=True)
        st.caption(f"DSTS = HGPR − HGP({hgp:.0f}) − HQ({hq:.0f})/1000  "
                   f"= HGPR − {hgp + hq / 1000.0:.1f} mm")

        st.subheader("📐 Diagrama")
        components.html(
            '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
            + belting_svg(results) + '</body></html>',
            height=330, scrolling=False,
        )
