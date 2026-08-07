"""
UI de la pestaña de Belting (herramienta independiente).
Del plano del proyecto: HQ y HGP (v137). Del usuario: HGPR por elevador.
DSTS = HGPR − HGP − HQ/1000 (mm), por elevador.

v129/v130: los resultados vivían dentro de `if st.button(...)` y se perdían con
cualquier interacción (bug de v110). Ahora el botón solo calcula; el render,
el PDF y el guardado contra el proyecto van fuera.
"""
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from core.belting import compute_belting, belting_svg
from core import plan_store
from core import plan_ui
from core.tool_pdf import tool_pdf
from core.tool_save_ui import render_guardar
from core import tool_save_ui

_K = "belt_res"


def _kpi(label, value, color=None):
    col = f"color:{color};" if color else ""
    return ('<div style="background:#fff;border:1px solid #e6e9ef;border-radius:12px;'
            'padding:10px 14px;flex:1;min-width:96px;">'
            f'<div style="font-size:12px;color:#6b7280;">{label}</div>'
            f'<div style="font-size:20px;font-weight:700;{col}">{value}</div></div>')


def _kpi_row(cards):
    return ('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px">'
            + "".join(cards) + "</div>")


def render_belting_tab():
    st.markdown("### :material/swap_vert: Belting — posición de la cabina para instalar los belts")
    st.caption("Calcula **DSTS** = cuánto bajar la cabina bajo el FFL del piso más alto para instalar "
               "los belts respetando el recorrido de diseño.  DSTS = HGPR − HGP − HQ/1000 (mm), por elevador.")

    for k in ("belt_hgp", "belt_hq"):
        st.session_state.setdefault(k, 0.0)
    st.session_state.setdefault("belt_ns", 1)

    # ── Proyecto: de aquí salen los datos del plano ya leídos ──
    # El admin elige el proyecto; al campo le sale del clock-in. Si el proyecto
    # tiene su plano cargado, los valores se rellenan solos y NO hace falta
    # volver a subir el PDF (antes cada herramienta lo reparseaba, 30-70 s).
    # Reabrir un calculo guardado: escribe claves de widget, asi que
    # va ANTES de instanciar ninguno (regla v111).
    _reab = tool_save_ui.aplicar_restauracion("belting")
    if _reab:
        st.info(f"↩️ Reabierto el cálculo **{_reab}**. Ajusta lo que necesites y vuelve a calcular.")

    _prj, _plano = plan_ui.selector_proyecto("belt")
    _pr = str((_prj or {}).get("Nombre", "") or "")     # v183: al diagrama y al PDF
    if _plano:
        _n = plan_ui.aplicar(_plano, {"hq": "belt_hq", "hgp": "belt_hgp"})
        if _n:
            st.caption("✅ HQ y HGP tomado(s) del plano del proyecto.")

    # ── PDF: autocompleta HQ ────────────────────────────────
    # Plan B, plegado: desde v137 el plano vive en el PROYECTO y sus valores
    # se rellenan arriba. Esto sigue haciendo falta para un proyecto creado
    # sin plano, o para calcular sin proyecto asignado.
    with st.expander("📄 ¿El proyecto no tiene plano? Cárgalo aquí"):
        st.caption("Se leerá HQ y HGP de este PDF. Lo normal es que ya vengan del plano del proyecto.")
        pdf = plan_store.selector("📄 PDF de planos (autocompleta HQ)", "belt_pdf")
        if pdf is not None and pdf.name != st.session_state.get("belt_pdf_name"):
            from extractors.schindler import extract_belting
            with st.spinner("Leyendo el plano..."):
                ex = extract_belting(pdf)
            st.session_state["belt_pdf_name"] = pdf.name
            _found = []
            if ex.get("HQ") is not None:
                st.session_state["belt_hq"] = float(ex["HQ"]);  _found.append(f"HQ={ex['HQ']:.0f}")
            if ex.get("HGP") is not None:
                st.session_state["belt_hgp"] = float(ex["HGP"]); _found.append(f"HGP={ex['HGP']:.0f}")
            if _found:
                st.success(f"✅ Del plano: **{', '.join(_found)} mm**. "
                           "Ingresa los HGPR reales de cada elevador.")
            else:
                st.warning("No se encontraron HQ/HGP en el plano. Ingrésalos a mano.")
            st.rerun()
        elif pdf is not None:
            st.caption(f"📄 Plano cargado: **{pdf.name}**")

    # ── Datos del plano ─────────────────────────────────────
    st.markdown("**Datos**  ·  📄 = del plano · ✏️ = manual")
    c1, c2 = st.columns(2)
    hq  = c1.number_input("📄 HQ — travel height (mm)", step=1.0, key="belt_hq")
    hgp = c2.number_input("📄 HGP — striker↔buffer de diseño (mm)", step=0.5, key="belt_hgp")

    ne = st.number_input("Número de elevadores", min_value=1, max_value=12, step=1, key="belt_ns")

    st.markdown("**✏️ HGPR — distancia REAL striker↔buffer del contrapeso, por elevador (mm)**")
    hgpr_list = []
    cols = st.columns(min(int(ne), 4))
    for i in range(int(ne)):
        v = cols[i % len(cols)].number_input(f"HGPR elevador {i+1}", step=0.5, key=f"belt_hgpr_{i}")
        hgpr_list.append(v)

    # ── Cálculo (solo computa; el render va fuera) ──────────
    if st.button(":material/swap_vert: Calcular belting", type="primary", use_container_width=True,
                 key="belt_calc"):
        st.session_state[_K] = {"results": compute_belting(hgp, hq, hgpr_list),
                                "hgp": hgp, "hq": hq}

    est = st.session_state.get(_K)
    if not est:
        return
    results, _hgp, _hq = est["results"], est["hgp"], est["hq"]

    # ── Resultado (persistente entre reruns) ────────────────
    st.markdown(_kpi_row([
        _kpi("HQ (travel)", f"{_hq:.0f} mm"),
        _kpi("HGP (diseño)", f"{_hgp:.0f} mm"),
        _kpi("Elevadores", str(len(results)))]),
        unsafe_allow_html=True)
    filas = [{
        "Elevador":  r["elevador"],
        "HGPR (mm)": r["hgpr"],
        "DSTS (mm)": r["dsts"],
        "Posición":  f"{abs(r['dsts']):.0f} mm "
                     f"{'por debajo' if r['dsts'] >= 0 else 'por encima'} del FFL top",
    } for r in results]
    st.subheader(":material/table_rows: Resultados (DSTS por elevador)")
    st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)
    _formula = (f"DSTS = HGPR − HGP({_hgp:.0f}) − HQ({_hq:.0f})/1000 "
                f"= HGPR − {_hgp + _hq / 1000.0:.1f} mm")
    st.caption(_formula)

    svg = belting_svg(results, proyecto=_pr)
    st.subheader(":material/architecture: Diagrama")
    components.html(
        '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
        + svg + '</body></html>', height=330, scrolling=False)

    # ── PDF + guardar contra el proyecto ────────────────────
    _resumen = ", ".join(f"E{r['elevador']}: DSTS {r['dsts']}" for r in results)
    pdf_bytes = tool_pdf(
        "Belting — posición de la cabina",
        meta={"Proyecto": _pr or "—", "HQ (travel)": f"{_hq:.0f} mm",
              "HGP (diseño)": f"{_hgp:.0f} mm", "Elevadores": str(len(results))},
        svgs=[svg],
        tablas=[("DSTS por elevador", filas)],
        notas=[_formula,
               "DSTS > 0 = bajar la cabina esa distancia bajo el FFL del piso más alto."])
    render_guardar(herramienta="belting", titulo_pdf="belting",
                   pdf_bytes=pdf_bytes, resumen=_resumen,
                   datos={"hgp": _hgp, "hq": _hq, "results": results},
                   nombre_archivo="belting.pdf", key="belt")
