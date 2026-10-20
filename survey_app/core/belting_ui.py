"""
UI de la pestaña de Belting (herramienta independiente).
Del plano del proyecto: HQ y HGP (v137). Del usuario: HGPR por elevador.
DSTS = HGPR − HGP − HQ/1000 (mm), por elevador.

v129/v130: los resultados vivían dentro de `if st.button(...)` y se perdían con
cualquier interacción (bug de v110). Ahora el botón solo calcula; el render,
el PDF y el guardado contra el proyecto van fuera.
"""
import pandas as pd

from core.i18n import t, d
import streamlit as st

from core.belting import compute_belting, belting_svg
from core import plan_store
from core import plan_ui
from core.tool_pdf import tool_pdf
from core.tool_save_ui import render_guardar
from core import tool_save_ui
from core import tabla
from core import incrustar
from core import flash
from core import clock
from core import theme as T
from core.num import nombre_archivo as _archivo

_K = "belt_res"


def _firma(hq, hgp, hgpr_list) -> tuple:
    """v595 · Las ENTRADAS de un cálculo, para saber si lo de pantalla sigue valiendo."""
    return (round(float(hq or 0), 3), round(float(hgp or 0), 3),
            tuple(round(float(x or 0), 3) for x in hgpr_list))


def _posicion(dsts) -> str:
    """v595 · «21.0 mm below the top FFL» (decía «21 mm below from the top FFL»: a entero —el
    DSTS lleva un decimal— y mal dicho)."""
    v = float(dsts)
    if abs(v) < 0.05:
        return d("at the top FFL")
    return (d("{x} mm below the top FFL", x=f"{abs(v):.1f}") if v > 0
            else d("{x} mm above the top FFL", x=f"{abs(v):.1f}"))


def render_belting_tab():
    st.markdown(t("### :material/swap_vert: Belting — car position for installing the belts"))
    st.caption(t("Works out **DSTS** = how far to lower the car below the FFL of the top floor to install the belts while respecting the design travel.  DSTS = HGPR − HGP − HQ/1000 (mm), per lift."))

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
        st.info(t(":material/replay: Reopened calculation **{x}**. Adjust whatever you need and "
                  "calculate again.", x=_reab))

    _prj, _plano = plan_ui.selector_proyecto("belt")
    _pr = str((_prj or {}).get("Name", "") or "")     # v183: al diagrama y al PDF
    if _plano:
        plan_ui.aplicar(_plano, {"hq": "belt_hq", "hgp": "belt_hgp"})
        # ⚠️ v595 · FIJO (como v591-v594): salía solo en la pasada que rellenaba y se iba al
        # tocar otro campo (visto en producción).
        if _plano.get("hq") or _plano.get("hgp"):
            st.caption(t(":green[:material/check_circle:] HQ and HGP come from the project's "
                         "drawing data."))

    # ── PDF: autocompleta HQ ────────────────────────────────
    # Plan B, plegado: desde v137 el plano vive en el PROYECTO y sus valores
    # se rellenan arriba. Esto sigue haciendo falta para un proyecto creado
    # sin plano, o para calcular sin proyecto asignado.
    with st.expander(t("Does the project have no drawing? Upload it here"), icon=":material/description:", key="exp_blt_plano"):
        st.caption(t("HQ and HGP will be read from this PDF. Normally they already come from the project drawing."))
        # v595 · por `t()` (en las cuatro herramientas iba sin traducir) y «HQ and HGP»: lee las dos
        pdf = plan_store.selector(t(":material/description: Drawing PDF (fills in HQ and HGP)"),
                                  "belt_pdf")
        if pdf is not None and pdf.name != st.session_state.get("belt_pdf_name"):
            from extractors.schindler import extract_belting
            with st.spinner(t("Reading the drawing...")):
                ex = extract_belting(pdf)
            st.session_state["belt_pdf_name"] = pdf.name
            _found = []
            if ex.get("HQ") is not None:
                st.session_state["belt_hq"] = float(ex["HQ"]);  _found.append(f"HQ={ex['HQ']:.0f}")
            if ex.get("HGP") is not None:
                st.session_state["belt_hgp"] = float(ex["HGP"]); _found.append(f"HGP={ex['HGP']:.0f}")
            # ⚠️ v595 · Por `flash`: iban con `st.success`/`st.warning` justo antes del
            # `st.rerun()` y no los veía nadie (como la plomada hasta v592).
            if _found:
                flash.exito(t(":material/check_circle: From the drawing: **{x} mm**. Enter the actual "
                              "HGPR for each lift.", x=", ".join(_found)))
            else:
                flash.aviso(t("HQ/HGP were not found in the drawing. Enter them by hand."))
            st.rerun()
        elif pdf is not None:
            st.caption(t(":material/description: Drawing loaded: **{x}**", x=pdf.name))

    # ── Datos del plano ─────────────────────────────────────
    # v595 · el mismo icono que llevan los campos (decía «✏️ = by hand» con otro lápiz)
    st.markdown(t("**Data**  ·  :material/description: = from the drawing · :material/edit: = by hand"))
    c1, c2 = st.columns(2)
    hq  = c1.number_input(t(":material/description: HQ — travel height (mm)"), step=1.0, key="belt_hq")
    hgp = c2.number_input(t(":material/description: HGP — design striker↔buffer (mm)"), step=0.5, key="belt_hgp")

    ne = st.number_input(t("Number of lifts"), min_value=1, max_value=12, step=1, key="belt_ns")

    st.markdown(t("**:material/edit: HGPR — ACTUAL striker↔buffer distance on the counterweight, per lift (mm)**"))
    hgpr_list = []
    cols = st.columns(min(int(ne), 4))
    for i in range(int(ne)):
        v = cols[i % len(cols)].number_input(t("HGPR · Lift {n}", n=i + 1), step=0.5,
                                             key=f"belt_hgpr_{i}")
        hgpr_list.append(v)
    _ahora = _firma(hq, hgp, hgpr_list)

    # ── Cálculo (solo computa; el render va fuera) ──────────
    if st.button(t(":material/swap_vert: Calculate belting"), type="primary", width="stretch",
                 key="belt_calc"):
        # ⚠️ v595 · Sin medir no se calcula: un ascensor con HGPR 0 salía «DSTS −99 mm · above
        # FFL» —la orden de dejar la cabina 99 mm sobre el último piso sin haber medido—.
        _faltan = [x for x, val in (("HQ", hq), ("HGP", hgp)) if float(val or 0) <= 0]
        _sin = [str(i + 1) for i, x in enumerate(hgpr_list) if float(x or 0) <= 0]
        if _sin:
            _faltan.append(t("the HGPR measured on lift {x}", x=", ".join(_sin)))
        if _faltan:
            st.session_state.pop(_K, None)
            st.warning(t(":material/edit: Fill in before calculating: {x}.", x=", ".join(_faltan)))
        else:
            st.session_state[_K] = {"results": compute_belting(hgp, hq, hgpr_list),
                                    "hgp": hgp, "hq": hq, "firma": _ahora}

    est = st.session_state.get(_K)
    if not est:
        return
    results, _hgp, _hq = est["results"], est["hgp"], est["hq"]
    # ⚠️ v595 · Lo de abajo es del ÚLTIMO cálculo: si un dato cambió, se dice — y no se descarga
    # ni se guarda (visto en producción: HGPR 130 en pantalla y el dibujo con el de 120).
    _vig = est.get("firma") == _ahora
    if not _vig:
        st.warning(t(":material/warning: You changed data since the last calculation. What is "
                     "below belongs to the previous one — press **Calculate belting** to update it."))

    # ── Resultado (persistente entre reruns) ────────────────
    # v595 · ACTIVAS (eran HTML): cada cifra lleva al diagrama.
    _K3 = [("hq", t("HQ (travel)"), f"{_hq:.0f} mm"), ("hgp", t("HGP (design)"), f"{_hgp:.0f} mm"),
           ("n", t("Lifts"), str(len(results)))]
    st.markdown(T.por_fila("cpx_belt_kpis", 3), unsafe_allow_html=True)
    with st.container(key="cpx_belt_kpis"):
        for _col, (_s, _l, _v) in zip(st.columns(len(_K3)), _K3):
            if _col.button(f"{_l}\n\n{_v}", key=f"cpxkpi_belt_{_s}", width="stretch",
                           help=t("See it on the diagram")):
                st.session_state["_bajar_cpx_belt_dibujo"] = True
                st.rerun()
    filas = [{
        d("Lift"):   r["elevador"],
        "HGPR (mm)": round(float(r["hgpr"]), 1),      # v597 · al décimo, como el DSTS
        "DSTS (mm)": r["dsts"],
        d("Position"): _posicion(r["dsts"]),
    } for r in results]
    st.subheader(t(":material/table_rows: Results (DSTS per lift)"))
    # v596 · el DSTS con UN decimal, como la posición, el resumen y el PDF (salía «21» aquí y
    # «21.0» al lado). v597 · y el HGPR igual («120» y «70.5» en la misma columna, visto en
    # producción): `tabla.mm1`, con su etiqueta (regla de v579)
    st.dataframe(pd.DataFrame(filas), width="stretch", hide_index=True,
                 column_config=tabla.cfg(extra={"HGPR (mm)": tabla.mm1(t("HGPR (mm)")),
                                                "DSTS (mm)": tabla.mm1(t("DSTS (mm)"))}))
    _formula = d("DSTS = HGPR − HGP({a}) − HQ({b})/1000 = HGPR − {c} mm", a=f"{_hgp:.0f}",
                 b=f"{_hq:.0f}", c=f"{_hgp + _hq / 1000.0:.1f}")
    st.caption(_formula)

    svg = belting_svg(results, proyecto=_pr)
    from core import projects_ui as _PU
    with st.container(key="cpx_belt_dibujo"):        # v595 · destino de las cifras
        _PU._bajar_a("cpx_belt_dibujo", "_bajar_cpx_belt_dibujo", bloque="start")
        st.subheader(t(":material/architecture: Diagram"))
    incrustar.dibujo('<!DOCTYPE html><html><body style="margin:0;background:transparent">'
        + svg + '</body></html>', 330)

    # ── PDF + guardar contra el proyecto ────────────────────
    # v595 · «Lift 1: DSTS 21.0» (decía «E1: DSTS 21.0»)
    _resumen = ", ".join(d("Lift {i}: DSTS {x}", i=r["elevador"], x=f"{float(r['dsts']):.1f}")
                         for r in results)
    pdf_bytes = tool_pdf(
        d("Belting — car position"),
        meta={d("Project"): _pr or "—", d("HQ (travel)"): f"{_hq:.0f} mm",
              d("HGP (design)"): f"{_hgp:.0f} mm", d("Lifts"): str(len(results))},
        svgs=[svg],
        tablas=[(d("DSTS per lift"), filas)],
        notas=[_formula,
               d("DSTS > 0 = lower the car by that distance below the FFL of the top floor.")])
    render_guardar(herramienta="belting", titulo_pdf=d("belting"),
                   pdf_bytes=pdf_bytes, resumen=_resumen,
                   datos={"hgp": _hgp, "hq": _hq, "results": results},
                   # v595 · con la obra y la fecha (era «belting.pdf»)
                   nombre_archivo=f"Belting_{_archivo(_pr, 'shaft')}_"
                                  f"{clock.today().strftime('%Y-%m-%d')}.pdf",
                   key="belt", obra_id=str((_prj or {}).get("ID", "")),   # v592
                   vigente=_vig)                                           # v595
