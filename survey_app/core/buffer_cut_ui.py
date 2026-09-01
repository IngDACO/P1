"""
UI de la pestaña de corte de buffers.

⚠️ v129: los resultados se calculaban y dibujaban DENTRO de `if st.button(...)`,
así que desaparecían con cualquier interacción posterior — el mismo bug
estructural que se corrigió en el Survey en v110, y que además hacía imposible
añadir un botón de "guardar en el proyecto" (al pulsarlo se perdía todo).
Ahora el botón solo CALCULA y guarda en session_state; el render vive fuera.
"""
import streamlit as st

from core.i18n import t, d
import streamlit.components.v1 as components
import pandas as pd

from core.buffer_cut import compute_buffer_cut, buffer_cut_svg
from extractors.schindler import extract_hkp
from core import plan_store
from core import plan_ui
from core.tool_pdf import tool_pdf
from core.tool_save_ui import render_guardar
from core import tool_save_ui
from core import tabla

_K = "bc_res"


def _kpi(label, value, color=None):
    col = f"color:{color};" if color else ""
    return ('<div style="background:#fff;border:1px solid #e6e9ef;border-radius:12px;'
            'padding:10px 14px;flex:1;min-width:96px;">'
            f'<div style="font-size:12px;color:#6b7280;">{label}</div>'
            f'<div style="font-size:21px;font-weight:700;{col}">{value}</div></div>')


def _kpi_row(cards):
    return ('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px">'
            + "".join(cards) + "</div>")


def render_buffer_cut_tab():
    st.markdown(t("### :material/shield: Buffer cutting"))
    st.caption(t("Works out how much to cut off each buffer. **HKP** comes from the project drawing; you enter the actual **HKPR** measured on each buffer."))

    # ── Proyecto: de aquí salen los datos del plano ya leídos ──
    # El admin elige el proyecto; al campo le sale del clock-in. Si el proyecto
    # tiene su plano cargado, los valores se rellenan solos y NO hace falta
    # volver a subir el PDF (antes cada herramienta lo reparseaba, 30-70 s).
    # Reabrir un calculo guardado: escribe claves de widget, asi que
    # va ANTES de instanciar ninguno (regla v111).
    _reab = tool_save_ui.aplicar_restauracion("buffers")
    if _reab:
        st.info(f":material/replay: Reopened calculation **{_reab}**. Adjust whatever you need and calculate again.")

    _prj, _plano = plan_ui.selector_proyecto("bc")
    _pr = str((_prj or {}).get("Nombre", "") or "")     # v181: al diagrama y al PDF
    if _plano:
        _n = plan_ui.aplicar(_plano, {"hkp": "bc_hkp"})
        if _n:
            st.caption(t(":green[:material/check_circle:] HKP taken from the project drawing."))

    # ── 1. PDF → HKP ────────────────────────────────────────
    st.markdown(t("**1. Drawing parameter (HKP)**"))
    # Plan B, plegado: desde v137 el plano vive en el PROYECTO y sus valores
    # se rellenan arriba. Esto sigue haciendo falta para un proyecto creado
    # sin plano, o para calcular sin proyecto asignado.
    with st.expander(t("Does the project have no drawing? Upload it here"), icon=":material/description:"):
        st.caption(t("HKP will be read from this PDF. Normally it already comes from the project drawing."))
        pdf = plan_store.selector("Drawing PDF (for HKP)", "bc_pdf")
        if pdf is not None and pdf.name != st.session_state.get("bc_pdf_name"):
            with st.spinner("Reading HKP from the PDF..."):
                ex = extract_hkp(pdf)
            st.session_state["bc_pdf_name"] = pdf.name
            if ex.get("HKP") is not None:
                st.session_state["bc_hkp"] = float(ex["HKP"])
                st.success(f"HKP found in the PDF: {ex['HKP']:.0f} mm. Check below.")
            else:
                st.warning(t("HKP was not found in the PDF. Enter it by hand."))

    hkp = st.number_input(t("HKP (mm) — car sticker ↔ buffer serving the 1st level"),
                          value=float(st.session_state.get("bc_hkp", 0.0)),
                          step=0.5, key="bc_hkp")

    # ── 2. Nº de buffers ────────────────────────────────────
    st.markdown(t("**2. Buffers**"))
    n = int(st.number_input(t("How many buffers are there?"), min_value=1, max_value=12, step=1,
                            value=int(st.session_state.get("bc_n", 1)), key="bc_n"))

    # ── 3. HKPR real de cada buffer ─────────────────────────
    st.markdown(t("**3. Actual HKPR of each buffer (mm)**"))
    base = st.session_state.get("bc_df")
    if base is None or len(base) != n:
        base = pd.DataFrame({"Buffer": [f"Buffer {i+1}" for i in range(n)],
                             "HKPR (mm)": [0.0] * n})
    edit = st.data_editor(base, width="stretch", hide_index=True,
                          num_rows="fixed", disabled=["Buffer"], key="bc_editor", column_config=tabla.cfg())
    st.session_state["bc_df"] = edit

    # ── 4. Calcular (solo computa; el render va fuera) ──────
    if st.button(t(":material/shield: Calculate cuts"), type="primary", width="stretch",
                 key="bc_calc"):
        hkpr_list = [float(x) for x in edit["HKPR (mm)"].tolist()]
        st.session_state[_K] = compute_buffer_cut(hkp, hkpr_list)

    res = st.session_state.get(_K)
    if not res:
        return

    # ── 5. Resultado (persistente entre reruns) ─────────────
    _n_warn = sum(1 for b in res["buffers"] if b["warn"])
    st.markdown(_kpi_row([
        _kpi(t("HKP (drawing)"), f"{res['HKP']:.0f} mm"),
        _kpi(t("Buffers"), str(len(res["buffers"]))),
        _kpi(t("To check"), str(_n_warn), "#c0392b" if _n_warn else None)]),
        unsafe_allow_html=True)
    st.caption(t("Cut = HKP − HKPR (per buffer)."))
    filas = [{
        "Buffer":     f"Buffer {b['n']}",
        "HKPR (mm)":  round(b["HKPR"], 1),
        d("Cut (mm)"): b["CutBuffer"],
        d("Status"):   d("check") if b["warn"] else "OK",
    } for b in res["buffers"]]
    st.subheader(t("Result — cuts (mm)"))
    st.dataframe(pd.DataFrame(filas), width="stretch", hide_index=True, column_config=tabla.cfg())

    svg = buffer_cut_svg(res, proyecto=_pr)
    st.subheader(t(":material/architecture: Cutting diagram"))
    components.html(
        '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
        + svg + '</body></html>', height=330, scrolling=False)

    if any(b["warn"] for b in res["buffers"]):
        st.warning(t(":material/warning: A negative cut means the actual HKPR is greater than the HKP on the drawing: there is nothing to cut off that buffer, check it on site."))

    # ── 6. PDF + guardar contra el proyecto ─────────────────
    _cortes = ", ".join(f"B{b['n']}: {b['CutBuffer']}" for b in res["buffers"])
    pdf_bytes = tool_pdf(
        d("Buffer cutting"),
        meta={d("Project"): _pr or "—", d("HKP from the drawing"): f"{res['HKP']:.0f} mm",
              "Buffers": str(len(res["buffers"]))},
        svgs=[svg],
        tablas=[(d("Cuts per buffer"), filas)],
        notas=["Cut = HKP − HKPR. A negative value means the actual buffer is longer than the drawing says: there is nothing to cut, check on site."])
    render_guardar(herramienta="buffers", titulo_pdf=d("buffer cutting"),
                   pdf_bytes=pdf_bytes, resumen=f"HKP {res['HKP']:.0f} · {_cortes}",
                   datos=res, nombre_archivo="corte_buffers.pdf", key="bc")
