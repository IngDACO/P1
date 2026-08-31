"""
UI de la pestaña de líneas de plomada (Streamlit).
Herramienta independiente del survey.
"""
import streamlit as st

from core.i18n import t, d
import streamlit.components.v1 as components
import pandas as pd

from core.plumb import compute_plumb, plumb_table, plumb_svg, plumb_iso_svg, plumb_detail_svg, plumb_card_svg
from core import plan_store
from core import plan_ui
from core.tool_pdf import tool_pdf
from core.tool_save_ui import render_guardar
from core import tool_save_ui


def _kpi(label, value, color=None):
    col = f"color:{color};" if color else ""
    return ('<div style="background:#fff;border:1px solid #e6e9ef;border-radius:12px;'
            'padding:10px 14px;flex:1;min-width:92px;">'
            f'<div style="font-size:12px;color:#6b7280;">{label}</div>'
            f'<div style="font-size:21px;font-weight:700;{col}">{value}</div></div>')


def _encaje_txt(disp) -> str:
    """Resumen accionable del encaje de un elevador (para la tabla)."""
    if not disp:
        return "no shift (BSR = BS)"
    if disp.get("centrado"):
        return f"centrado · holgura {disp.get('holgura_lado', 0):.0f} mm/lado"
    if disp.get("fuera_rango"):
        return (f":orange[:material/warning:] DOES NOT FIT · Omega {disp.get('omega_sacrificio', 0):.0f} > "
                f"limit {disp.get('limit_ob', 0):.0f}")
    return f"move {abs(disp.get('desp_conjunto', 0)):.0f} mm towards the {disp.get('z_side', '')} side"


def render_plumb_tab():
    st.markdown(t("### :material/straighten: Plumb line calculation"))
    st.caption(t("One **template** for the shaft; the **BSR is measured per lift**. The values from the drawing fill themselves in; RAIL comes from the catalogue."))

    # ── Inicializar en 0 (BSR ya NO es global: se mide por elevador) ──
    _keys = ["plb_bks", "plb_rail", "plb_tksw", "plb_lt", "plb_sf1", "plb_sf2",
             "plb_bs", "plb_sg", "plb_tg"]
    for _k in _keys:
        st.session_state.setdefault(_k, 0.0)

    # Reabrir un calculo guardado: escribe claves de widget, va ANTES de crearlos (v111).
    _reab = tool_save_ui.aplicar_restauracion("plomada")
    if _reab:
        st.info(f":material/replay: Reopened calculation **{_reab}**. Adjust whatever you need and calculate again.")

    # ── Proyecto: el plano ya leído ──
    _prj, _plano = plan_ui.selector_proyecto("plb")
    _pr_base = str((_prj or {}).get("Nombre", "") or "")     # v179: el proyecto SÍ se conoce
    if _plano:
        _n = plan_ui.aplicar(_plano, {
            "params.BKS": "plb_bks", "params.TKSW": "plb_tksw",
            "params.SF1": "plb_sf1", "params.SF2": "plb_sf2",
            "params.BS": "plb_bs", "params.SG": "plb_sg", "params.TG": "plb_tg",
            "rail_altura": "plb_rail"})   # RAIL = altura del diente, del catálogo
        if _n:
            st.caption(f":green[:material/check_circle:] {_n} value(s) taken from the project drawing.")

    with st.expander(t("Does the project have no drawing? Upload it here"), icon=":material/description:"):
        st.caption(t("BKS, TKSW, SF1, SF2, BS, SG and TG will be read from this PDF."))
        pdf = plan_store.selector(":material/description: Drawing PDF (fills in from the drawing)", "plb_pdf")
        if pdf is not None and pdf.name != st.session_state.get("plb_pdf_name"):
            from extractors.schindler import extract_from_pdf
            with st.spinner("Reading the drawing..."):
                ex = extract_from_pdf(pdf)
            st.session_state["plb_pdf_name"] = pdf.name
            mapping = {"BKS": "plb_bks", "TKSW": "plb_tksw", "SF1": "plb_sf1", "SF2": "plb_sf2",
                       "BS": "plb_bs", "SG": "plb_sg", "TG": "plb_tg"}
            found = []
            for src, key in mapping.items():
                if ex.get(src) is not None:
                    st.session_state[key] = float(ex[src]); found.append(src)
            if found:
                st.success(f":material/check_circle: From the drawing: **{', '.join(found)}**. Fill in LengthTemplate; "
                           "RAIL comes from the rail code; the BSR is measured per lift.")
            else:
                st.warning(t("No values were found in the drawing. Enter them by hand."))
            st.rerun()
        elif pdf is not None:
            st.caption(f":material/description: Drawing loaded: **{pdf.name}**")

    # ── Entradas COMPARTIDAS del shaft (la plantilla es una sola) ──
    st.markdown(t("**Shaft template (shared)**  ·  :material/description: = from the drawing · ✏️ = by hand"))
    c1, c2, c3, c4 = st.columns(4)
    bks  = c1.number_input(t(":material/description: BKS (mm)"),            step=0.5, key="plb_bks")
    rail = c2.number_input(t(":material/description: RAIL (mm)"),           step=0.5, key="plb_rail")
    tksw = c3.number_input(t(":material/description: TKSW (mm)"),           step=0.5, key="plb_tksw")
    lt   = c4.number_input(t(":material/edit: LengthTemplate (mm)"), step=0.5, key="plb_lt")
    g1, g2, g3, _g4 = st.columns(4)
    sf1 = g1.number_input(t(":material/description: SF1 (mm)"), step=0.5, key="plb_sf1")
    sf2 = g2.number_input(t(":material/description: SF2 (mm)"), step=0.5, key="plb_sf2")
    bs  = g3.number_input(t(":material/description: BS (mm)"),  step=0.5, key="plb_bs")

    with st.expander(t("Fit data (SG, TG, Omega side) — used when a BSR < BS")):
        e1, e2, e3 = st.columns(3)
        sg    = e1.number_input(t(":material/description: SG (mm)"), step=0.5, key="plb_sg")
        tg    = e2.number_input(t(":material/description: TG (mm)"), step=0.5, key="plb_tg")
        omega = e3.radio(t(":material/edit: Omega side"), ["R", "L"], horizontal=True, key="plb_omega")

    # ── BSR por elevador (lo que varía entre huecos) ──
    st.markdown(t("**BSR measured on each lift (mm)**"))
    n = int(st.number_input(t("How many lifts are there in the shaft?"), min_value=1, max_value=12,
                            step=1, value=int(st.session_state.get("plb_n", 1)), key="plb_n"))
    base = st.session_state.get("plb_bsr_df")
    if base is None or len(base) != n:
        base = pd.DataFrame({"Elevador": [f"Elevador {i+1}" for i in range(n)],
                             "BSR (mm)": [0.0] * n})
    bsr_edit = st.data_editor(base, width="stretch", hide_index=True,
                              num_rows="fixed", disabled=["Elevador"], key="plb_bsr_editor")
    st.session_state["plb_bsr_df"] = bsr_edit

    if st.button(t(":material/straighten: Calculate plumb lines"), type="primary", width="stretch", key="plb_calc"):
        bsr_list = [float(x or 0) for x in bsr_edit["BSR (mm)"].tolist()]
        st.session_state["plb_res_multi"] = {"n": n, "results": [compute_plumb({
            "BKS": bks, "RAIL": rail, "TKSW": tksw, "LengthTemplate": lt,
            "SF1": sf1, "SF2": sf2, "BSR": b, "BS": bs,
            "SG": sg, "TG": tg, "OMEGA_SIDE": omega,
        }) for b in bsr_list]}

    data = st.session_state.get("plb_res_multi")
    if not data:
        return
    results, n = data["results"], data["n"]
    r0 = results[0]                       # la plantilla es la misma para todos

    # ── La plantilla (compartida, UNA vez) ──
    st.markdown(t("#### :material/architecture: The template (the same for every lift)"))
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px">'
                + "".join([_kpi(t("DBP"), f"{r0['dbp']:.1f}"), _kpi(t("DBPW"), f"{r0['dbpw']:.1f}"),
                           _kpi("RW", f"{r0['rw']:.1f}"), _kpi("d1", f"{r0['d1']:.2f}"),
                           _kpi("d2", f"{r0['d2']:.2f}")]) + "</div>",
                unsafe_allow_html=True)
    st.caption(t("DBP = spacing between the plumb points · d1/d2 = template→plumb diagonals (measured with a tape)."))

    _bs = r0.get("bs_check") or {}
    if _bs and not _bs.get("ok", True):
        st.error(f":material/warning: **BS does not add up:** the drawing says **{_bs['bs_plano']:.0f}** but "
                 f"SF1+BKS+2·RAIL+SF2 = **{_bs['bs_componentes']:.0f}** (diff {_bs['dif']:+.0f} mm). "
                 "With this mismatch the plumb points end up in the wrong place. Check BS, SF1, SF2, BKS or RAIL.")

    # ── Tabla por elevador ──
    st.markdown(t("#### :material/elevator: Per lift — fit and check"))
    _rows = []
    for i, r in enumerate(results):
        v = r.get("verif") or {}
        cierre = (r.get("cierre") or {}).get("suma", 0.0)
        _rows.append({
            d("Lift"): i + 1,
            "BSR (mm)": round(r.get("bsr", 0), 1),
            d("Fit"): _encaje_txt(r.get("displacement")),
            d("di (left wall→plumb)"): round(v.get("plomo_izq_pared_izq", 0), 1),
            d("dd (plumb→right wall)"): round(v.get("plomo_der_pared_der", 0), 1),
            "di+DBP+dd": round(cierre, 1),
        })
    st.dataframe(pd.DataFrame(_rows), width="stretch", hide_index=True)
    st.caption(t("On-site check: **di + DBP + dd = BSR**. If it does not add up, there is a measurement error."))

    # ── Diagramas de un elevador ──
    st.markdown(t("#### :material/architecture: Diagrams for one lift"))
    sel = st.selectbox(t("View the setting out for lift"), list(range(1, n + 1)),
                       format_func=lambda i: f"{t('Lift')} {i}", key="plb_sel_e")
    r = results[sel - 1]
    _pr = (f"{_pr_base} · {d('Lift')} {sel}" if _pr_base else f"{d('Lift')} {sel}")

    disp = r.get("displacement")
    if disp and disp.get("centrado"):
        st.success(f"Lift {sel}: BSR > BS → the assembly is **centred** "
                   f"(clearance {disp['holgura_lado']:.1f} mm/side).")
    elif disp:
        if disp.get("fuera_rango"):
            st.error(f":material/warning: Lift {sel}: DOES NOT FIT — it would need {disp['omega_sacrificio']:.1f} mm "
                     f"off the Omega, but the limit is {disp['limit_ob']:.1f} mm.")
        st.info(f"Lift {sel}: BSR < BS → **move the assembly {abs(disp['desp_conjunto']):.1f} mm "
                f"towards the {disp['z_side']}** side (Omega {disp['omega_side']} on the other side).")
        with st.expander(t("Fit detail (internal thresholds)")):
            st.caption(f"DIF = {disp['dif_bs']:.1f} · LIMIT_ZB = {disp['limit_zb']:.1f} · "
                       f"LIMIT_OB = {disp['limit_ob']:.1f} · Z give-up = {disp['z_sacrificio']:.1f} · "
                       f"Omega give-up = {disp['omega_sacrificio']:.1f}")
    else:
        st.success(f"Lift {sel}: BSR = BS → no shift.")

    components.html('<!DOCTYPE html><html><body style="margin:0;background:transparent">'
                    + plumb_svg(r, proyecto=_pr) + '</body></html>', height=500, scrolling=False)
    _v3d, _vfi = st.columns(2)
    with _v3d.expander(t("3D views of the setting out"), icon=":material/view_in_ar:", expanded=False):
        components.html('<!DOCTYPE html><html><body style="margin:0;background:transparent">'
                        + plumb_iso_svg(r, proyecto=_pr) + '</body></html>', height=650, scrolling=False)
        components.html('<!DOCTYPE html><html><body style="margin:0;background:transparent">'
                        + plumb_detail_svg(r, proyecto=_pr) + '</body></html>', height=500, scrolling=False)
    with _vfi.expander(t("Setting-out card (for site)"), icon=":material/assignment:", expanded=False):
        st.caption(t("The numbers to measure with a tape. Print it or open it on your phone."))
        components.html('<!DOCTYPE html><html><body style="margin:0;background:transparent">'
                        + plumb_card_svg(r, proyecto=_pr) + '</body></html>', height=430, scrolling=False)

    # ── PDF (con el nombre del proyecto) + guardar contra el proyecto ──
    _svgs = []
    for i, rr in enumerate(results):
        _lbl = (f"{_pr_base} · Lift {i+1}" if _pr_base else f"Lift {i+1}")
        _svgs.append(plumb_svg(rr, proyecto=_lbl))
        _svgs.append((plumb_card_svg(rr, proyecto=_lbl), 0.60))
    pdf_bytes = tool_pdf(
        d("Plumb setting-out"),
        meta={d("Project"): _pr_base or "—", d("Lifts"): str(n),
              "DBP": f"{r0['dbp']:.1f} mm", "DBPW": f"{r0['dbpw']:.1f} mm",
              "RW": f"{r0['rw']:.1f} mm", "d1 / d2": f"{r0['d1']:.1f} / {r0['d2']:.1f} mm"},
        svgs=_svgs,
        tablas=[("Per lift — fit and check", _rows),
                ("Template — line positions", plumb_table(r0))],
        notas=["The template (DBP, d1, d2) is the same for the whole shaft; the BSR is measured per lift and sets its fit and its check.",
               "Site check: di + DBP + dd = BSR."])
    render_guardar(herramienta="plomada", titulo_pdf=d("plumb setting-out"),
                   pdf_bytes=pdf_bytes,
                   resumen=(f"Template DBP {r0['dbp']:.1f} · d1 {r0['d1']:.1f}/d2 {r0['d2']:.1f} · "
                            f"{n} lift(s)"),
                   datos={"n": n,
                          "plantilla": {k: r0.get(k) for k in ("dbp", "dbpw", "rw", "d1", "d2")},
                          "elevadores": _rows},
                   nombre_archivo="replanteo_plomadas.pdf", key="plb")
