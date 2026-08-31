"""
UI de la pestaña de corte de rieles.
"""
import streamlit as st

from core.i18n import t, d
import pandas as pd

from core.rail_cut import (extract_lf, compute_case1, compute_case2,
                           rail_cut_svg)
import streamlit.components.v1 as components
from core.tool_pdf import tool_pdf
from core.tool_save_ui import render_guardar
from core import tool_save_ui
from core import plan_store
from core import plan_ui


def _result_matrix(labels, per_elev_values, n):
    """DataFrame: filas = labels, columnas = Elevador 1..n."""
    cols = {f"{d('Lift')} {i+1}": [round(per_elev_values[i][lab], 1) for lab in labels]
            for i in range(n)}
    return pd.DataFrame(cols, index=labels)


def _kpi(label, value, color=None):
    col = f"color:{color};" if color else ""
    return ('<div style="background:#fff;border:1px solid #e6e9ef;border-radius:12px;'
            'padding:10px 14px;flex:1;min-width:96px;">'
            f'<div style="font-size:12px;color:#6b7280;">{label}</div>'
            f'<div style="font-size:21px;font-weight:700;{col}">{value}</div></div>')


def _kpi_row(cards):
    return ('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px">'
            + "".join(cards) + "</div>")


def render_rail_cut_tab():
    st.markdown(t("### :material/content_cut: Rail cutting"))
    st.caption(t("Works out the rail cut for each lift in the shaft. LFKK and LFGK come from the project drawing; if it is missing, they are entered by hand."))

    # ── 1. PDF → LFKK / LFGK ────────────────────────────────
    # ── Proyecto: de aquí salen los datos del plano ya leídos ──
    # El admin elige el proyecto; al campo le sale del clock-in. Si el proyecto
    # tiene su plano cargado, los valores se rellenan solos y NO hace falta
    # volver a subir el PDF (antes cada herramienta lo reparseaba, 30-70 s).
    # Reabrir un calculo guardado: escribe claves de widget, asi que
    # va ANTES de instanciar ninguno (regla v111).
    _reab = tool_save_ui.aplicar_restauracion("rieles")
    if _reab:
        st.info(f":material/replay: Reopened calculation **{_reab}**. Adjust whatever you need and calculate again.")

    _prj, _plano = plan_ui.selector_proyecto("rc")
    _pr = str((_prj or {}).get("Nombre", "") or "")     # v180: al diagrama y al PDF
    if _plano:
        _n = plan_ui.aplicar(_plano, {"lfkk": "rc_lfkk", "lfgk": "rc_lfgk"})
        if _n:
            st.caption(t(":green[:material/check_circle:] LFKK and LFGK taken from the project drawing."))

    st.markdown(t("**1. Drawing parameters (LFKK, LFGK)**"))
    # Plan B, plegado: desde v137 el plano vive en el PROYECTO y sus valores
    # se rellenan arriba. Esto sigue haciendo falta para un proyecto creado
    # sin plano, o para calcular sin proyecto asignado.
    with st.expander(t("Does the project have no drawing? Upload it here"), icon=":material/description:"):
        st.caption(t("LFKK and LFGK will be read from this PDF. Normally they already come from the project drawing."))
        pdf = plan_store.selector("Drawing PDF (for LFKK / LFGK)", "rc_pdf")
        if pdf is not None and pdf.name != st.session_state.get("rc_pdf_name"):
            with st.spinner("Reading LFKK / LFGK from the PDF..."):
                lf = extract_lf(pdf)
            st.session_state["rc_pdf_name"] = pdf.name
            if lf.get("LFKK") is not None:
                st.session_state["rc_lfkk"] = float(lf["LFKK"])
            if lf.get("LFGK") is not None:
                st.session_state["rc_lfgk"] = float(lf["LFGK"])
            found = [k for k in ("LFKK", "LFGK") if lf.get(k) is not None]
            st.success(f"Found in the PDF: {', '.join(found) if found else 'none'}. "
                       "Check or complete below.")

    c1, c2 = st.columns(2)
    lfkk = c1.number_input(t("LFKK (mm)"), value=float(st.session_state.get("rc_lfkk", 0.0)),
                           step=0.5, key="rc_lfkk")
    lfgk = c2.number_input(t("LFGK (mm)"), value=float(st.session_state.get("rc_lfgk", 0.0)),
                           step=0.5, key="rc_lfgk")

    # ── 2. Nº de elevadores ─────────────────────────────────
    st.markdown(t("**2. Lifts in the shaft**"))
    n = int(st.number_input(t("How many lifts are there in the shaft?"), min_value=1, max_value=12,
                            step=1, value=int(st.session_state.get("rc_n", 1)), key="rc_n"))

    # ── 3. Caso ─────────────────────────────────────────────
    st.markdown(t("**3. Cutting case**"))
    # ⚠️ La opción se guarda en una CONSTANTE y la rama compara contra ella. Antes el
    # texto estaba escrito dos veces —en el radio y en el `startswith`— y al traducir
    # solo el del radio (v441) la rama del Caso 1 quedó MUERTA: la herramienta caía
    # siempre al Caso 2, sin dar ningún error. Con la constante no pueden divergir.
    _C1 = "Case 1 — first installed (the bottom one)"
    _C2 = "Case 2 — last installed (the top one)"
    caso = st.radio(t("Which rail is cut?"), [_C1, _C2], key="rc_caso")

    st.markdown("---")

    # ════════════════════════════════════════════════════════
    # CASO 1
    # ════════════════════════════════════════════════════════
    if caso == _C1:
        st.markdown(t("**Case 1 — data**"))
        d1, d2 = st.columns(2)
        n2500 = int(d1.number_input(t("No. of 2500 mm rails"), min_value=0, step=1,
                                    value=int(st.session_state.get("rc_n2500", 0)), key="rc_n2500"))
        n5000 = int(d2.number_input(t("No. of 5000 mm rails"), min_value=0, step=1,
                                    value=int(st.session_state.get("rc_n5000", 0)), key="rc_n5000"))
        A = n2500 * 2500 + n5000 * 5000
        st.caption(f"A = {n2500}×2500 + {n5000}×5000 = **{A:.0f} mm**")

        st.markdown(t("**L for each lift** (FFL of the top floor → bottom of the shaft):"))
        base = st.session_state.get("rc_L_df")
        if base is None or len(base) != n:
            base = pd.DataFrame({"Elevador": [f"Elevador {i+1}" for i in range(n)],
                                 "L (mm)": [0.0] * n})
        L_edit = st.data_editor(base, width="stretch", hide_index=True,
                                num_rows="fixed", disabled=["Elevador"], key="rc_L_editor")
        st.session_state["rc_L_df"] = L_edit

        # El boton SOLO computa: antes todo el resultado colgaba de aqui y se
        # perdia con cualquier interaccion (bug estructural de v110).
        if st.button(t(":material/content_cut: Calculate cuts (Case 1)"), type="primary",
                     width="stretch", key="rc_calc1"):
            L_list = [float(x) for x in L_edit["L (mm)"].tolist()]
            st.session_state["rc_res"] = {
                "caso": 1, "res": compute_case1(lfkk, lfgk, n2500, n5000, L_list),
                "n2500": int(n2500), "n5000": int(n5000), "n": int(n)}

        _e = st.session_state.get("rc_res")
        if _e and _e.get("caso") == 1:
            res = _e["res"]
            st.markdown(_kpi_row([
                _kpi(t("A (stack installed)"), f"{res['A']:.0f} mm"),
                _kpi(t("LFKK"), f"{lfkk:.0f}"), _kpi(t("LFGK"), f"{lfgk:.0f}"),
                _kpi(t("Lifts"), str(_e["n"]))]), unsafe_allow_html=True)
            mat = _result_matrix(["CutRC", "CutRCW"], res["elevadores"], _e["n"])
            st.subheader(t("Result — cuts (mm)"))
            st.dataframe(mat, width="stretch")
            with st.expander(t("Detail (RC, RCW)")):
                det = _result_matrix(["RC", "RCW"], res["elevadores"], _e["n"])
                st.dataframe(det, width="stretch")

            svg = rail_cut_svg(res, caso=1, n2500=_e["n2500"], n5000=_e["n5000"], proyecto=_pr)
            st.subheader(t(":material/architecture: Cutting diagram"))
            components.html(
                '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
                + svg + '</body></html>', height=390, scrolling=False)

            _filas = [{d("Lift"): i + 1, "L (mm)": round(x["L"], 1),
                       "RC (mm)": round(x["RC"], 1), "CutRC (mm)": round(x["CutRC"], 1),
                       "RCW (mm)": round(x["RCW"], 1), "CutRCW (mm)": round(x["CutRCW"], 1)}
                      for i, x in enumerate(res["elevadores"])]
            _pdf = tool_pdf(
                d("Rail cutting — Case 1"),
                meta={d("Project"): _pr or "—",
                      d("A (installed stack)"): f"{res['A']:.0f} mm",
                      d("Make-up"): f"{_e['n2500']}×2500 + {_e['n5000']}×5000",
                      "LFKK / LFGK": f"{lfkk:.0f} / {lfgk:.0f} mm"},
                svgs=[svg], tablas=[(d("Cuts per lift"), _filas)],
                notas=["Case 1: the rail to cut is the first one installed (at the bottom). CutRC = RC − A, CutRCW = RCW − A."])
            render_guardar(herramienta="rieles", titulo_pdf=d("rail cutting"),
                           pdf_bytes=_pdf,
                           resumen=("Caso 1 · A " + f"{res['A']:.0f} · "
                                    + ", ".join(f"E{i+1}: {x['CutRC']:.0f}/{x['CutRCW']:.0f}"
                                                for i, x in enumerate(res["elevadores"]))),
                           datos=res, nombre_archivo="corte_rieles_caso1.pdf", key="rc1")

    # ════════════════════════════════════════════════════════
    # CASO 2
    # ════════════════════════════════════════════════════════
    else:
        st.markdown(t("**Case 2 — sub-case**"))
        sub = st.radio(
            t("The second-to-last rail is…"),
            ["Above the FFL (subtract)", "Below the FFL (add)"],
            key="rc_sub",
        )
        subcaso = "encima" if sub.startswith("Above") else "debajo"

        st.markdown(t("**Input matrix** (fill in RZ, RO, RF, RB for each lift):"))
        rieles = ["RZ", "RO", "RF", "RB"]
        base = st.session_state.get("rc_in_df")
        cols_expected = ["Riel"] + [f"Elevador {i+1}" for i in range(n)]
        if base is None or list(base.columns) != cols_expected:
            base = pd.DataFrame({"Riel": rieles,
                                 **{f"Elevador {i+1}": [0.0] * 4 for i in range(n)}})
        in_edit = st.data_editor(base, width="stretch", hide_index=True,
                                 num_rows="fixed", disabled=["Riel"], key="rc_in_editor")
        st.session_state["rc_in_df"] = in_edit

        if st.button(t(":material/content_cut: Calculate cuts (Case 2)"), type="primary",
                     width="stretch", key="rc_calc2"):
            rows = []
            for i in range(n):
                col = in_edit[f"Elevador {i+1}"].tolist()
                rows.append({"RZ": col[0], "RO": col[1], "RF": col[2], "RB": col[3]})
            st.session_state["rc_res"] = {
                "caso": 2, "res": compute_case2(lfkk, lfgk, rows, subcaso),
                "subcaso": subcaso, "sub": sub, "n": int(n)}

        _e = st.session_state.get("rc_res")
        if _e and _e.get("caso") == 2:
            res = _e["res"]
            signo = "LFKK/LFGK − R" if _e["subcaso"] == "encima" else "LFKK/LFGK + R"
            st.markdown(_kpi_row([
                _kpi(t("Formula"), signo), _kpi(t("LFKK"), f"{lfkk:.0f}"),
                _kpi(t("LFGK"), f"{lfgk:.0f}"), _kpi(t("Lifts"), str(_e["n"]))]),
                unsafe_allow_html=True)
            st.caption(f"Sub-case: {_e['sub']}")
            mat = _result_matrix(["CutRZ", "CutRO", "CutRF", "CutRB"], res, _e["n"])
            st.subheader(t("Result — cuts (mm)"))
            st.dataframe(mat, width="stretch")

            svg = rail_cut_svg({"elevadores": res}, caso=2, proyecto=_pr)
            st.subheader(t(":material/architecture: Cutting diagram"))
            components.html(
                '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
                + svg + '</body></html>', height=330, scrolling=False)

            _filas = [{d("Lift"): i + 1,
                       **{k: round(float(x.get(k) or 0), 1)
                          for k in ("CutRZ", "CutRO", "CutRF", "CutRB")}}
                      for i, x in enumerate(res)]
            _pdf = tool_pdf(
                d("Rail cutting — Case 2"),
                meta={d("Project"): _pr or "—", d("Sub-case"): _e["sub"], d("Formula"): signo,
                      "LFKK / LFGK": f"{lfkk:.0f} / {lfgk:.0f} mm"},
                svgs=[svg], tablas=[(d("Cuts per lift"), _filas)],
                notas=["Case 2: the rail to cut is the last one installed (at the top)."])
            render_guardar(herramienta="rieles", titulo_pdf=d("rail cutting"),
                           pdf_bytes=_pdf,
                           resumen=f"Case 2 ({_e['subcaso']}) · {len(res)} lift(s)",
                           datos={"subcaso": _e["subcaso"], "elevadores": res},
                           nombre_archivo="corte_rieles_caso2.pdf", key="rc2")
