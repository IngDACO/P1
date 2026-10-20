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
import pandas as pd

from core.buffer_cut import compute_buffer_cut, buffer_cut_svg
from extractors.schindler import extract_hkp
from core import plan_store
from core import plan_ui
from core import estado_vivo
from core.tool_pdf import tool_pdf
from core.tool_save_ui import render_guardar
from core import tool_save_ui
from core import tabla
from core import incrustar
from core import clock
from core import theme as T
from core.num import nombre_archivo as _archivo

_K = "bc_res"


def _firma(hkp, n, hkpr_list) -> tuple:
    """v594 · Las ENTRADAS de un cálculo, para saber si lo de pantalla sigue valiendo."""
    return (round(float(hkp or 0), 3), int(n), tuple(round(float(x or 0), 3) for x in hkpr_list))


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
        st.info(t(":material/replay: Reopened calculation **{x}**. Adjust whatever you need and "
                  "calculate again.", x=_reab))

    _prj, _plano = plan_ui.selector_proyecto("bc")
    _pr = str((_prj or {}).get("Name", "") or "")     # v181: al diagrama y al PDF
    if _plano:
        plan_ui.aplicar(_plano, {"hkp": "bc_hkp"})
        # ⚠️ v594 · FIJO (como v591-v593): salía solo en la pasada que rellenaba (visto en
        # producción: se iba al cambiar el nº de buffers).
        if _plano.get("hkp"):
            st.caption(t(":green[:material/check_circle:] HKP comes from the project's drawing data."))

    # ── 1. PDF → HKP ────────────────────────────────────────
    st.markdown(t("**1. Drawing parameter (HKP)**"))
    # Plan B, plegado: desde v137 el plano vive en el PROYECTO y sus valores
    # se rellenan arriba. Esto sigue haciendo falta para un proyecto creado
    # sin plano, o para calcular sin proyecto asignado.
    with st.expander(t("Does the project have no drawing? Upload it here"), icon=":material/description:", key="exp_buf_plano"):
        st.caption(t("HKP will be read from this PDF. Normally it already comes from the project drawing."))
        pdf = plan_store.selector(t("Drawing PDF (for HKP)"), "bc_pdf")   # v595 · por `t()`
        if pdf is not None and pdf.name != st.session_state.get("bc_pdf_name"):
            with st.spinner(t("Reading HKP from the PDF...")):
                ex = extract_hkp(pdf)
            st.session_state["bc_pdf_name"] = pdf.name
            if ex.get("HKP") is not None:
                st.session_state["bc_hkp"] = float(ex["HKP"])
                st.success(t("HKP found in the PDF: {x} mm. Check below.", x=f"{ex['HKP']:.0f}"))
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
        # ⚠️ v594 · Cambiar el nº de buffers CONSERVA lo medido (antes nacía todo en 0) y
        # estrena la tabla editable (v542).
        _prev = [float(x or 0) for x in (list(base["HKPR (mm)"]) if base is not None else [])]
        base = pd.DataFrame({"Buffer": [t("Buffer {n}", n=i + 1) for i in range(n)],
                             "HKPR (mm)": (_prev + [0.0] * n)[:n]})
        if _prev:
            estado_vivo.tabla_nueva("bc")
    edit = st.data_editor(base, width="stretch", hide_index=True,
                          num_rows="fixed", disabled=["Buffer"],
                          # v540 · Clave con generación: al cambiar de obra, tabla nueva.
                          key=estado_vivo.clave_tabla("bc", "bc_editor"), column_config=tabla.cfg())
    st.session_state["bc_df"] = edit
    hkpr_list = [float(x or 0) for x in edit["HKPR (mm)"].tolist()]
    _ahora = _firma(hkp, n, hkpr_list)

    # ── 4. Calcular (solo computa; el render va fuera) ──────
    if st.button(t(":material/shield: Calculate cuts"), type="primary", width="stretch",
                 key="bc_calc"):
        # ⚠️ v594 · Sin medir no se calcula: un buffer con HKPR 0 salía «Cut 520 mm · OK» —la
        # orden de cortar el HKP entero sin haber medido nada (visto en producción, tres así).
        _faltan = []
        if hkp <= 0:
            _faltan.append(t("HKP (from the drawing, or by hand)"))
        _sin = [str(i + 1) for i, x in enumerate(hkpr_list) if x <= 0]
        if _sin:
            _faltan.append(t("the HKPR measured on buffer {x}", x=", ".join(_sin)))
        if _faltan:
            st.session_state.pop(_K, None)
            st.warning(t(":material/edit: Fill in before calculating: {x}.", x="; ".join(_faltan)))
        else:
            st.session_state[_K] = dict(compute_buffer_cut(hkp, hkpr_list), firma=_ahora)

    res = st.session_state.get(_K)
    if not res:
        return

    # ── 5. Resultado (persistente entre reruns) ─────────────
    # ⚠️ v594 · Lo de abajo es del ÚLTIMO cálculo: si un dato cambió, se dice — y no se
    # descarga ni se guarda (se mezclarían las entradas nuevas con los resultados viejos).
    _vig = res.get("firma") == _ahora
    if not _vig:
        st.warning(t(":material/warning: You changed data since the last calculation. What is "
                     "below belongs to the previous one — press **Calculate cuts** to update it."))
    _n_warn = sum(1 for b in res["buffers"] if b["warn"])
    # v594 · ACTIVAS (eran HTML): HKP lleva al diagrama; los buffers y «To check», a la tabla.
    _K3 = [("hkp", t("HKP (drawing)"), f"{res['HKP']:.0f} mm", "cpx_bc_dibujo"),
           ("n", t("Buffers"), str(len(res["buffers"])), "cpx_bc_tabla"),
           ("rev", t("To check"), str(_n_warn), "cpx_bc_tabla")]
    st.markdown(T.por_fila("cpx_bc_kpis", 3)
                + ("<style>.st-key-cpxkpi_bc_rev button{border-left-color:#c0392b!important}</style>"
                   if _n_warn else ""), unsafe_allow_html=True)
    with st.container(key="cpx_bc_kpis"):
        for _col, (_s, _l, _v, _dest) in zip(st.columns(len(_K3)), _K3):
            if _col.button(f"{_l}\n\n{_v}", key=f"cpxkpi_bc_{_s}", width="stretch",
                           help=t("Go to it")):
                st.session_state["_bajar_" + _dest] = True
                st.rerun()
    st.caption(t("Cut = HKP − HKPR (per buffer)."))
    filas = [{
        "Buffer":     d("Buffer {n}", n=b["n"]),
        "HKPR (mm)":  round(b["HKPR"], 1),
        d("Cut (mm)"): b["CutBuffer"],
        d("Status"):   d("check") if b["warn"] else "OK",
    } for b in res["buffers"]]
    # v594 · los destinos de las cifras: cada bloque envuelve su TÍTULO (claves literales,
    # para que verif_v585 lo compruebe)
    from core import projects_ui as _PU
    with st.container(key="cpx_bc_tabla"):
        _PU._bajar_a("cpx_bc_tabla", "_bajar_cpx_bc_tabla", bloque="start")
        st.subheader(t("Result — cuts (mm)"))
    # v597 · UN decimal, como el resumen y el PDF (salía «20» y «7.5» en la misma columna y
    # «Buffer 1: 20.0» en lo guardado, visto en producción)
    st.dataframe(pd.DataFrame(filas), width="stretch", hide_index=True,
                 column_config=tabla.cfg(extra={"HKPR (mm)": tabla.mm1(t("HKPR (mm)")),
                                                d("Cut (mm)"): tabla.mm1(t("Cut (mm)"))}))

    svg = buffer_cut_svg(res, proyecto=_pr)
    with st.container(key="cpx_bc_dibujo"):
        _PU._bajar_a("cpx_bc_dibujo", "_bajar_cpx_bc_dibujo", bloque="start")
        st.subheader(t(":material/architecture: Cutting diagram"))
    incrustar.dibujo('<!DOCTYPE html><html><body style="margin:0;background:transparent">'
        + svg + '</body></html>', 330)

    if any(b["warn"] for b in res["buffers"]):
        st.warning(t(":material/warning: A negative cut means the actual HKPR is greater than the HKP on the drawing: there is nothing to cut off that buffer, check it on site."))

    # ── 6. PDF + guardar contra el proyecto ─────────────────
    pdf_bytes = tool_pdf(
        d("Buffer cutting"),
        meta={d("Project"): _pr or "—", d("HKP from the drawing"): f"{res['HKP']:.0f} mm",
              "Buffers": str(len(res["buffers"]))},
        svgs=[svg],
        tablas=[(d("Cuts per buffer"), filas)],
        notas=[d("Cut = HKP − HKPR. A negative value means the actual buffer is longer than the "
                 "drawing says: there is nothing to cut, check on site.")])
    render_guardar(herramienta="buffers", titulo_pdf=d("buffer cutting"),
                   pdf_bytes=pdf_bytes,
                   # v594 · «Buffer 1: 20.0» (decía «B1: 20.0»)
                   resumen=d("HKP {h} · {x}", h=f"{res['HKP']:.0f}", x=", ".join(
                       d("Buffer {i}: {c}", i=b["n"], c=f"{b['CutBuffer']:.1f}")
                       for b in res["buffers"])),
                   datos={k: v for k, v in res.items() if k != "firma"},
                   # v594 · con la obra y la fecha (era «corte_buffers.pdf»)
                   nombre_archivo=f"Buffer_cutting_{_archivo(_pr, 'shaft')}_"
                                  f"{clock.today().strftime('%Y-%m-%d')}.pdf",
                   key="bc", obra_id=str((_prj or {}).get("ID", "")),   # v592
                   vigente=_vig)                                         # v594
