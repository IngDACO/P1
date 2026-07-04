"""
UI de la pestaña de líneas de plomada (Streamlit).
Herramienta independiente del survey.
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

from core.plumb import compute_plumb, plumb_table, plumb_svg


def render_plumb_tab():
    st.markdown("### 🔩 Cálculo de líneas de plomada")
    st.caption("Herramienta independiente. Ingresa las medidas y obtén la tabla de "
               "posiciones de las plomadas y el diagrama de la plantilla.")

    # ── Entradas principales ────────────────────────────────
    st.markdown("**Entradas principales**")
    c1, c2, c3, c4 = st.columns(4)
    bks  = c1.number_input("BKS (mm)",            value=1200.0, step=0.5, key="plb_bks")
    rail = c2.number_input("RAIL (mm)",           value=12.0,   step=0.5, key="plb_rail")
    tksw = c3.number_input("TKSW (mm)",           value=1315.0, step=0.5, key="plb_tksw")
    lt   = c4.number_input("LengthTemplate (mm)", value=800.0,  step=0.5, key="plb_lt")

    # ── Entradas para líneas verticales ─────────────────────
    st.markdown("**Entradas para líneas de referencia**")
    d1, d2, d3, d4 = st.columns(4)
    sf1 = d1.number_input("SF1 (mm)", value=51.0,   step=0.5, key="plb_sf1")
    sf2 = d2.number_input("SF2 (mm)", value=260.0,  step=0.5, key="plb_sf2")
    bsr = d3.number_input("BSR (mm)", value=1586.0, step=0.5, key="plb_bsr")
    bs  = d4.number_input("BS (mm)",  value=1597.0, step=0.5, key="plb_bs")

    # ── Entradas condicionales (BSR < BS) ───────────────────
    needs = bsr < bs
    if needs:
        st.info("BSR < BS → se aplica desplazamiento. Ingresa SG, TG y el lado del Omega.")
        e1, e2, e3 = st.columns(3)
        sg    = e1.number_input("SG (mm)", value=400.0, step=0.5, key="plb_sg")
        tg    = e2.number_input("TG (mm)", value=100.0, step=0.5, key="plb_tg")
        omega = e3.radio("Lado del Omega", ["R", "L"], horizontal=True, key="plb_omega")
    else:
        sg, tg, omega = 0.0, 0.0, "R"

    # ── Cálculo ─────────────────────────────────────────────
    if st.button("🔩 Calcular plomadas", type="primary", use_container_width=True, key="plb_calc"):
        inp = {
            "BKS": bks, "RAIL": rail, "TKSW": tksw, "LengthTemplate": lt,
            "SF1": sf1, "SF2": sf2, "BSR": bsr, "BS": bs,
            "SG": sg, "TG": tg, "OMEGA_SIDE": omega,
        }
        res = compute_plumb(inp)

        m1, m2, m3 = st.columns(3)
        m1.metric("DBP",  f"{res['dbp']:.1f} mm")
        m2.metric("DBPW", f"{res['dbpw']:.1f} mm")
        m3.metric("RW",   f"{res['rw']:.1f} mm")
        st.caption(f"Distancias diagonales de plantilla:  P→C1 = **{res['d1']:.2f} mm**  |  "
                   f"P→C2 = **{res['d2']:.2f} mm**")

        disp = res["displacement"]
        if disp:
            warn = "  ⚠️ FUERA DE RANGO (> 1000)" if disp["fuera_rango"] else ""
            st.info(
                f"**Desplazamiento (BSR < BS):**  Z = {disp['linea_z']} (lado {disp['z_side']}), "
                f"Omega = {disp['linea_omega']}  |  LIMIT_ZB = {disp['limit_zb']:.1f}, "
                f"LIMIT_OB = {disp['limit_ob']:.1f}  |  DIF_BS = {disp['dif_bs']:.1f}  |  "
                f"paso = {disp['paso']:.1f} ({disp['rango']})  |  "
                f"desp_Z = {disp['desp_z']:.1f}, desp_Omega = {disp['desp_omega']:.1f}{warn}"
            )
        else:
            st.success("BSR ≥ BS → sin desplazamiento (V4/V6 en posición inicial).")

        st.subheader("📋 Tabla de posiciones")
        st.dataframe(pd.DataFrame(plumb_table(res)), use_container_width=True, hide_index=True)

        st.subheader("📐 Diagrama de la plantilla")
        components.html(
            '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
            + plumb_svg(res) + '</body></html>',
            height=460, scrolling=False,
        )
