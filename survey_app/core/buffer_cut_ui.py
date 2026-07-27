"""
UI de la pestaña de corte de buffers.

⚠️ v129: los resultados se calculaban y dibujaban DENTRO de `if st.button(...)`,
así que desaparecían con cualquier interacción posterior — el mismo bug
estructural que se corrigió en el Survey en v110, y que además hacía imposible
añadir un botón de "guardar en el proyecto" (al pulsarlo se perdía todo).
Ahora el botón solo CALCULA y guarda en session_state; el render vive fuera.
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

from core.buffer_cut import compute_buffer_cut, buffer_cut_svg
from extractors.schindler import extract_hkp
from core import plan_store
from core import plan_ui
from core.tool_pdf import tool_pdf
from core.tool_save_ui import render_guardar
from core import tool_save_ui

_K = "bc_res"


def _kpi(label, value, color=None):
    col = f"color:{color};" if color else ""
    return ('<div style="background:#fff;border:1px solid #e6e9ef;border-radius:12px;'
            'padding:10px 14px;flex:1;min-width:96px;">'
            f'<div style="font-size:12px;color:#6b7280;">{label}</div>'
            f'<div style="font-size:20px;font-weight:700;{col}">{value}</div></div>')


def _kpi_row(cards):
    return ('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px">'
            + "".join(cards) + "</div>")


def render_buffer_cut_tab():
    st.markdown("### 🛡 Corte de buffers")
    st.caption("Calcula cuánto cortar cada buffer. **HKP** sale del plano del proyecto; "
               "tú indicas el **HKPR** real medido en cada buffer.")

    # ── Proyecto: de aquí salen los datos del plano ya leídos ──
    # El admin elige el proyecto; al campo le sale del clock-in. Si el proyecto
    # tiene su plano cargado, los valores se rellenan solos y NO hace falta
    # volver a subir el PDF (antes cada herramienta lo reparseaba, 30-70 s).
    # Reabrir un calculo guardado: escribe claves de widget, asi que
    # va ANTES de instanciar ninguno (regla v111).
    _reab = tool_save_ui.aplicar_restauracion("buffers")
    if _reab:
        st.info(f"↩️ Reabierto el cálculo **{_reab}**. Ajusta lo que necesites y vuelve a calcular.")

    _prj, _plano = plan_ui.selector_proyecto("bc")
    _pr = str((_prj or {}).get("Nombre", "") or "")     # v181: al diagrama y al PDF
    if _plano:
        _n = plan_ui.aplicar(_plano, {"hkp": "bc_hkp"})
        if _n:
            st.caption("✅ HKP tomado(s) del plano del proyecto.")

    # ── 1. PDF → HKP ────────────────────────────────────────
    st.markdown("**1. Parámetro del plano (HKP)**")
    # Plan B, plegado: desde v137 el plano vive en el PROYECTO y sus valores
    # se rellenan arriba. Esto sigue haciendo falta para un proyecto creado
    # sin plano, o para calcular sin proyecto asignado.
    with st.expander("📄 ¿El proyecto no tiene plano? Cárgalo aquí"):
        st.caption("Se leerá HKP de este PDF. Lo normal es que ya vengan del plano del proyecto.")
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

    # ── 4. Calcular (solo computa; el render va fuera) ──────
    if st.button("🛡 Calcular cortes", type="primary", use_container_width=True,
                 key="bc_calc"):
        hkpr_list = [float(x) for x in edit["HKPR (mm)"].tolist()]
        st.session_state[_K] = compute_buffer_cut(hkp, hkpr_list)

    res = st.session_state.get(_K)
    if not res:
        return

    # ── 5. Resultado (persistente entre reruns) ─────────────
    _n_warn = sum(1 for b in res["buffers"] if b["warn"])
    st.markdown(_kpi_row([
        _kpi("HKP (plano)", f"{res['HKP']:.0f} mm"),
        _kpi("Buffers", str(len(res["buffers"]))),
        _kpi("A revisar", str(_n_warn), "#c0392b" if _n_warn else None)]),
        unsafe_allow_html=True)
    st.caption("Corte = HKP − HKPR (por buffer).")
    filas = [{
        "Buffer":     f"Buffer {b['n']}",
        "HKPR (mm)":  round(b["HKPR"], 1),
        "Corte (mm)": b["CutBuffer"],
        "Estado":     "⚠️ revisar" if b["warn"] else "OK",
    } for b in res["buffers"]]
    st.subheader("Resultado — cortes (mm)")
    st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

    svg = buffer_cut_svg(res, proyecto=_pr)
    st.subheader("📐 Diagrama de cortes")
    components.html(
        '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
        + svg + '</body></html>', height=330, scrolling=False)

    if any(b["warn"] for b in res["buffers"]):
        st.warning("⚠️ Un corte negativo significa que el HKPR real supera al HKP del plano: "
                   "no hay nada que cortar en ese buffer, revísalo en obra.")

    # ── 6. PDF + guardar contra el proyecto ─────────────────
    _cortes = ", ".join(f"B{b['n']}: {b['CutBuffer']}" for b in res["buffers"])
    pdf_bytes = tool_pdf(
        "Corte de buffers",
        meta={"Proyecto": _pr or "—", "HKP del plano": f"{res['HKP']:.0f} mm",
              "Buffers": str(len(res["buffers"]))},
        svgs=[svg],
        tablas=[("Cortes por buffer", filas)],
        notas=["Corte = HKP − HKPR. Un valor negativo indica que el buffer real "
               "supera al del plano: no hay nada que cortar, revisar en obra."])
    render_guardar(herramienta="buffers", titulo_pdf="corte de buffers",
                   pdf_bytes=pdf_bytes, resumen=f"HKP {res['HKP']:.0f} · {_cortes}",
                   datos=res, nombre_archivo="corte_buffers.pdf", key="bc")
