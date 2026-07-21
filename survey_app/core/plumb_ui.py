"""
UI de la pestaña de líneas de plomada (Streamlit).
Herramienta independiente del survey.
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

from core.plumb import (compute_plumb, plumb_table, plumb_svg, plumb_checks,
                        plumb_iso_svg, plumb_detail_svg, plumb_card_svg)
from core import plan_store
from core import plan_ui
from core.tool_pdf import tool_pdf
from core.tool_save_ui import render_guardar


def render_plumb_tab():
    st.markdown("### 🔩 Cálculo de líneas de plomada")
    st.caption("Carga el PDF del plano para autocompletar los valores que se pueden leer, "
               "o ingresa todo a mano.")

    # ── Inicializar en 0 (sin valores residuales de ejemplo) ─
    _keys = ["plb_bks", "plb_rail", "plb_tksw", "plb_lt", "plb_sf1", "plb_sf2",
             "plb_bsr", "plb_bs", "plb_sg", "plb_tg"]
    for _k in _keys:
        st.session_state.setdefault(_k, 0.0)

    # ── Carga de PDF → autocompleta lo que trae el plano ────
    # ── Proyecto: el plano ya leído ──────────────────────
    # El admin elige el proyecto; al campo le sale del clock-in. Si el proyecto
    # tiene su plano cargado, estos valores se rellenan sin abrir el PDF.
    _prj, _plano = plan_ui.selector_proyecto("plb")
    if _plano:
        _n = plan_ui.aplicar(_plano, {
            "params.BKS": "plb_bks", "params.TKSW": "plb_tksw",
            "params.SF1": "plb_sf1", "params.SF2": "plb_sf2",
            "params.BS": "plb_bs", "params.SG": "plb_sg", "params.TG": "plb_tg"})
        if _n:
            st.caption(f"✅ {_n} valor(es) tomados del plano del proyecto.")

    pdf = plan_store.selector("📄 PDF de planos (autocompleta del plano)", "plb_pdf")
    if pdf is not None and pdf.name != st.session_state.get("plb_pdf_name"):
        from extractors.schindler import extract_from_pdf
        with st.spinner("Leyendo el plano..."):
            ex = extract_from_pdf(pdf)
        st.session_state["plb_pdf_name"] = pdf.name
        mapping = {"BKS": "plb_bks", "TKSW": "plb_tksw", "SF1": "plb_sf1", "SF2": "plb_sf2",
                   "BS": "plb_bs", "SG": "plb_sg", "TG": "plb_tg"}
        found = []
        for src, key in mapping.items():
            if ex.get(src) is not None:
                st.session_state[key] = float(ex[src]); found.append(src)
        if found:
            st.success(f"✅ Del plano: **{', '.join(found)}**. "
                       "Completa RAIL, LengthTemplate y BSR (no vienen en el plano).")
        else:
            st.warning("No se encontraron valores en el plano. Ingrésalos manualmente.")
        st.rerun()
    elif pdf is not None:
        st.caption(f"📄 Plano cargado: **{pdf.name}**")

    # ── Entradas principales ────────────────────────────────
    st.markdown("**Entradas principales**  ·  📄 = del plano · ✏️ = manual")
    c1, c2, c3, c4 = st.columns(4)
    bks  = c1.number_input("📄 BKS (mm)",            step=0.5, key="plb_bks")
    rail = c2.number_input("✏️ RAIL (mm)",           step=0.5, key="plb_rail")
    tksw = c3.number_input("📄 TKSW (mm)",           step=0.5, key="plb_tksw")
    lt   = c4.number_input("✏️ LengthTemplate (mm)", step=0.5, key="plb_lt")

    # ── Entradas para líneas verticales ─────────────────────
    st.markdown("**Entradas para líneas de referencia**")
    d1, d2, d3, d4 = st.columns(4)
    sf1 = d1.number_input("📄 SF1 (mm)", step=0.5, key="plb_sf1")
    sf2 = d2.number_input("📄 SF2 (mm)", step=0.5, key="plb_sf2")
    bsr = d3.number_input("✏️ BSR (mm)", step=0.5, key="plb_bsr")
    bs  = d4.number_input("📄 BS (mm)",  step=0.5, key="plb_bs")

    # ── Entradas condicionales (BSR < BS) ───────────────────
    needs = bsr < bs
    if needs:
        st.info("BSR < BS → se aplica desplazamiento. Ingresa SG, TG y el lado del Omega.")
        e1, e2, e3 = st.columns(3)
        sg    = e1.number_input("📄 SG (mm)", step=0.5, key="plb_sg")
        tg    = e2.number_input("📄 TG (mm)", step=0.5, key="plb_tg")
        omega = e3.radio("✏️ Lado del Omega", ["R", "L"], horizontal=True, key="plb_omega")
    else:
        sg, tg, omega = 0.0, 0.0, "R"

    # ── Cálculo ─────────────────────────────────────────────
    # ⚠️ El boton SOLO computa. Antes colgaban ~80 lineas de aqui (incluidos los
    # 4 graficos CAD de v123), asi que todo el resultado se borraba con cualquier
    # interaccion — el bug estructural de v110 — y hacia imposible un boton de
    # "guardar en el proyecto": al pulsarlo se perdia el propio resultado.
    if st.button("🔩 Calcular plomadas", type="primary", use_container_width=True, key="plb_calc"):
        st.session_state["plb_res"] = compute_plumb({
            "BKS": bks, "RAIL": rail, "TKSW": tksw, "LengthTemplate": lt,
            "SF1": sf1, "SF2": sf2, "BSR": bsr, "BS": bs,
            "SG": sg, "TG": tg, "OMEGA_SIDE": omega,
        })

    res = st.session_state.get("plb_res")
    if not res:
        return

    m1, m2, m3 = st.columns(3)
    m1.metric("DBP",  f"{res['dbp']:.1f} mm")
    m2.metric("DBPW", f"{res['dbpw']:.1f} mm")
    m3.metric("RW",   f"{res['rw']:.1f} mm")
    st.caption(f"Distancias diagonales de plantilla:  P→C1 = **{res['d1']:.2f} mm**  |  "
               f"P→C2 = **{res['d2']:.2f} mm**")

    disp = res["displacement"]
    if disp and disp.get("centrado"):
        st.success(
            f"BSR > BS → el conjunto se **centra** dentro del shaft real "
            f"(holgura {disp['holgura_lado']:.1f} mm a cada lado). Paredes reales fijas."
        )
    elif disp:
        if disp["fuera_rango"]:
            st.error(
                f"⚠️ NO CABE: hay que sacrificar {disp['omega_sacrificio']:.1f} mm del lado Omega, "
                f"pero LIMIT_OB = {disp['limit_ob']:.1f} mm."
            )
        st.info(
            f"**Encaje (BSR < BS):**  el conjunto se acerca al lado **Z ({disp['z_side']})**, "
            f"Omega ({disp['omega_side']}) del otro lado.  |  "
            f"DIF = {disp['dif_bs']:.1f} mm  |  "
            f"LIMIT_ZB = {disp['limit_zb']:.1f}, LIMIT_OB = {disp['limit_ob']:.1f}  |  "
            f"sacrificio Z = {disp['z_sacrificio']:.1f}, sacrificio Omega = {disp['omega_sacrificio']:.1f}  |  "
            f"desplazamiento del conjunto = {disp['desp_conjunto']:.1f} mm"
        )
    else:
        st.success("BSR = BS → el conjunto queda en su posición inicial (sin desplazar).")

    st.subheader("📋 Tabla de posiciones")
    st.dataframe(pd.DataFrame(plumb_table(res)), use_container_width=True, hide_index=True)

    st.subheader("📐 Diagrama de la plantilla")
    _pr_ = ""
    _bs = res.get("bs_check") or {}
    if _bs and not _bs.get("ok", True):
        st.error(
            f"⚠️ **BS incoherente:** el plano dice **{_bs['bs_plano']:.0f}** pero "
            f"SF1+BKS+2·RAIL+SF2 = **{_bs['bs_componentes']:.0f}** "
            f"(dif {_bs['dif']:+.0f} mm). El encaje usa (BSR−BS)/2, así que con este "
            f"desajuste los plomos quedan mal ubicados. Revisa BS, SF1, SF2, BKS o RAIL."
        )
    components.html(
        '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
        + plumb_svg(res, proyecto=_pr_) + '</body></html>',
        height=500, scrolling=False,
    )
    _v3d, _vfi = st.columns(2)
    with _v3d.expander("🧊 Vistas 3D del replanteo", expanded=False):
        components.html(
            '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
            + plumb_iso_svg(res, proyecto=_pr_) + '</body></html>',
            height=650, scrolling=False,
        )
        components.html(
            '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
            + plumb_detail_svg(res, proyecto=_pr_) + '</body></html>',
            height=500, scrolling=False,
        )
    with _vfi.expander("📋 Ficha de replanteo (para obra)", expanded=False):
        st.caption("Los números a medir con cinta. Imprímela o ábrela en el móvil.")
        components.html(
            '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
            + plumb_card_svg(res, proyecto=_pr_) + '</body></html>',
            height=430, scrolling=False,
        )

    st.subheader("📏 Verificación en campo — distancias plomo ↔ pared real")
    st.caption("Mide en obra desde cada pared real hasta el plomo correspondiente.")
    st.dataframe(pd.DataFrame(plumb_checks(res)),
                 use_container_width=True, hide_index=True)

    # ── PDF + guardar contra el proyecto ────────────────────
    _cierre = res.get("cierre") or {}
    pdf_bytes = tool_pdf(
        "Replanteo de plomadas",
        meta={"DBP": f"{res['dbp']:.1f} mm", "DBPW": f"{res['dbpw']:.1f} mm",
              "RW": f"{res['rw']:.1f} mm",
              "d1 / d2": f"{res['d1']:.1f} / {res['d2']:.1f} mm"},
        svgs=[plumb_svg(res), (plumb_iso_svg(res), 0.50),
              (plumb_card_svg(res), 0.62)],
        tablas=[("Posiciones de las líneas", plumb_table(res)),
                ("Verificación en campo", plumb_checks(res))],
        notas=["Comprobación de obra: di + DBP + dd debe dar BSR "
               f"({_cierre.get('suma', 0):.1f}). Si no cierra, hay error de medida."])
    render_guardar(herramienta="plomada", titulo_pdf="replanteo de plomadas",
                   pdf_bytes=pdf_bytes,
                   resumen=(f"DBP {res['dbp']:.1f} · DBPW {res['dbpw']:.1f} · "
                            f"d1 {res['d1']:.1f} · d2 {res['d2']:.1f}"),
                   datos={k: res.get(k) for k in
                          ("dbp", "dbpw", "rw", "d1", "d2", "verif", "cierre",
                           "bs_check", "displacement")},
                   nombre_archivo="replanteo_plomadas.pdf", key="plb")
