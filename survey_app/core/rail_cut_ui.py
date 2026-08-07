"""
UI de la pestaña de corte de rieles.
"""
import streamlit as st
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
    cols = {f"Elevador {i+1}": [round(per_elev_values[i][lab], 1) for lab in labels]
            for i in range(n)}
    return pd.DataFrame(cols, index=labels)


def _kpi(label, value, color=None):
    col = f"color:{color};" if color else ""
    return ('<div style="background:#fff;border:1px solid #e6e9ef;border-radius:12px;'
            'padding:10px 14px;flex:1;min-width:96px;">'
            f'<div style="font-size:12px;color:#6b7280;">{label}</div>'
            f'<div style="font-size:20px;font-weight:700;{col}">{value}</div></div>')


def _kpi_row(cards):
    return ('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px">'
            + "".join(cards) + "</div>")


def render_rail_cut_tab():
    st.markdown("### :material/content_cut: Corte de rieles")
    st.caption("Calcula el corte de los rieles de cada elevador del shaft. "
               "LFKK y LFGK salen del plano del proyecto; si falta, se ingresan a mano.")

    # ── 1. PDF → LFKK / LFGK ────────────────────────────────
    # ── Proyecto: de aquí salen los datos del plano ya leídos ──
    # El admin elige el proyecto; al campo le sale del clock-in. Si el proyecto
    # tiene su plano cargado, los valores se rellenan solos y NO hace falta
    # volver a subir el PDF (antes cada herramienta lo reparseaba, 30-70 s).
    # Reabrir un calculo guardado: escribe claves de widget, asi que
    # va ANTES de instanciar ninguno (regla v111).
    _reab = tool_save_ui.aplicar_restauracion("rieles")
    if _reab:
        st.info(f":material/replay: Reabierto el cálculo **{_reab}**. Ajusta lo que necesites y vuelve a calcular.")

    _prj, _plano = plan_ui.selector_proyecto("rc")
    _pr = str((_prj or {}).get("Nombre", "") or "")     # v180: al diagrama y al PDF
    if _plano:
        _n = plan_ui.aplicar(_plano, {"lfkk": "rc_lfkk", "lfgk": "rc_lfgk"})
        if _n:
            st.caption("✅ LFKK y LFGK tomado(s) del plano del proyecto.")

    st.markdown("**1. Parámetros del plano (LFKK, LFGK)**")
    # Plan B, plegado: desde v137 el plano vive en el PROYECTO y sus valores
    # se rellenan arriba. Esto sigue haciendo falta para un proyecto creado
    # sin plano, o para calcular sin proyecto asignado.
    with st.expander("¿El proyecto no tiene plano? Cárgalo aquí", icon=":material/description:"):
        st.caption("Se leerá LFKK y LFGK de este PDF. Lo normal es que ya vengan del plano del proyecto.")
        pdf = plan_store.selector("PDF de planos (para LFKK / LFGK)", "rc_pdf")
        if pdf is not None and pdf.name != st.session_state.get("rc_pdf_name"):
            with st.spinner("Leyendo LFKK / LFGK del PDF..."):
                lf = extract_lf(pdf)
            st.session_state["rc_pdf_name"] = pdf.name
            if lf.get("LFKK") is not None:
                st.session_state["rc_lfkk"] = float(lf["LFKK"])
            if lf.get("LFGK") is not None:
                st.session_state["rc_lfgk"] = float(lf["LFGK"])
            found = [k for k in ("LFKK", "LFGK") if lf.get(k) is not None]
            st.success(f"Encontrados en el PDF: {', '.join(found) if found else 'ninguno'}. "
                       "Verifica o completa abajo.")

    c1, c2 = st.columns(2)
    lfkk = c1.number_input("LFKK (mm)", value=float(st.session_state.get("rc_lfkk", 0.0)),
                           step=0.5, key="rc_lfkk")
    lfgk = c2.number_input("LFGK (mm)", value=float(st.session_state.get("rc_lfgk", 0.0)),
                           step=0.5, key="rc_lfgk")

    # ── 2. Nº de elevadores ─────────────────────────────────
    st.markdown("**2. Elevadores en el shaft**")
    n = int(st.number_input("¿Cuántos elevadores hay en el shaft?", min_value=1, max_value=12,
                            step=1, value=int(st.session_state.get("rc_n", 1)), key="rc_n"))

    # ── 3. Caso ─────────────────────────────────────────────
    st.markdown("**3. Caso de corte**")
    caso = st.radio(
        "¿Qué riel se corta?",
        ["Caso 1 — primero instalado (el de abajo)",
         "Caso 2 — último instalado (el de arriba)"],
        key="rc_caso",
    )

    st.markdown("---")

    # ════════════════════════════════════════════════════════
    # CASO 1
    # ════════════════════════════════════════════════════════
    if caso.startswith("Caso 1"):
        st.markdown("**Caso 1 — datos**")
        d1, d2 = st.columns(2)
        n2500 = int(d1.number_input("Nº de rieles de 2500 mm", min_value=0, step=1,
                                    value=int(st.session_state.get("rc_n2500", 0)), key="rc_n2500"))
        n5000 = int(d2.number_input("Nº de rieles de 5000 mm", min_value=0, step=1,
                                    value=int(st.session_state.get("rc_n5000", 0)), key="rc_n5000"))
        A = n2500 * 2500 + n5000 * 5000
        st.caption(f"A = {n2500}×2500 + {n5000}×5000 = **{A:.0f} mm**")

        st.markdown("**L de cada elevador** (FFL del piso más alto → fondo del shaft):")
        base = st.session_state.get("rc_L_df")
        if base is None or len(base) != n:
            base = pd.DataFrame({"Elevador": [f"Elevador {i+1}" for i in range(n)],
                                 "L (mm)": [0.0] * n})
        L_edit = st.data_editor(base, use_container_width=True, hide_index=True,
                                num_rows="fixed", disabled=["Elevador"], key="rc_L_editor")
        st.session_state["rc_L_df"] = L_edit

        # El boton SOLO computa: antes todo el resultado colgaba de aqui y se
        # perdia con cualquier interaccion (bug estructural de v110).
        if st.button(":material/content_cut: Calcular cortes (Caso 1)", type="primary",
                     use_container_width=True, key="rc_calc1"):
            L_list = [float(x) for x in L_edit["L (mm)"].tolist()]
            st.session_state["rc_res"] = {
                "caso": 1, "res": compute_case1(lfkk, lfgk, n2500, n5000, L_list),
                "n2500": int(n2500), "n5000": int(n5000), "n": int(n)}

        _e = st.session_state.get("rc_res")
        if _e and _e.get("caso") == 1:
            res = _e["res"]
            st.markdown(_kpi_row([
                _kpi("A (pila instalada)", f"{res['A']:.0f} mm"),
                _kpi("LFKK", f"{lfkk:.0f}"), _kpi("LFGK", f"{lfgk:.0f}"),
                _kpi("Elevadores", str(_e["n"]))]), unsafe_allow_html=True)
            mat = _result_matrix(["CutRC", "CutRCW"], res["elevadores"], _e["n"])
            st.subheader("Resultado — cortes (mm)")
            st.dataframe(mat, use_container_width=True)
            with st.expander("Detalle (RC, RCW)"):
                det = _result_matrix(["RC", "RCW"], res["elevadores"], _e["n"])
                st.dataframe(det, use_container_width=True)

            svg = rail_cut_svg(res, caso=1, n2500=_e["n2500"], n5000=_e["n5000"], proyecto=_pr)
            st.subheader(":material/architecture: Diagrama de cortes")
            components.html(
                '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
                + svg + '</body></html>', height=390, scrolling=False)

            _filas = [{"Elevador": i + 1, "L (mm)": round(x["L"], 1),
                       "RC (mm)": round(x["RC"], 1), "CutRC (mm)": round(x["CutRC"], 1),
                       "RCW (mm)": round(x["RCW"], 1), "CutRCW (mm)": round(x["CutRCW"], 1)}
                      for i, x in enumerate(res["elevadores"])]
            _pdf = tool_pdf(
                "Corte de rieles — Caso 1",
                meta={"Proyecto": _pr or "—",
                      "A (pila instalada)": f"{res['A']:.0f} mm",
                      "Composición": f"{_e['n2500']}×2500 + {_e['n5000']}×5000",
                      "LFKK / LFGK": f"{lfkk:.0f} / {lfgk:.0f} mm"},
                svgs=[svg], tablas=[("Cortes por elevador", _filas)],
                notas=["Caso 1: el riel a cortar es el primero instalado (abajo). "
                       "CutRC = RC − A, CutRCW = RCW − A."])
            render_guardar(herramienta="rieles", titulo_pdf="corte de rieles",
                           pdf_bytes=_pdf,
                           resumen=("Caso 1 · A " + f"{res['A']:.0f} · "
                                    + ", ".join(f"E{i+1}: {x['CutRC']:.0f}/{x['CutRCW']:.0f}"
                                                for i, x in enumerate(res["elevadores"]))),
                           datos=res, nombre_archivo="corte_rieles_caso1.pdf", key="rc1")

    # ════════════════════════════════════════════════════════
    # CASO 2
    # ════════════════════════════════════════════════════════
    else:
        st.markdown("**Caso 2 — sub-caso**")
        sub = st.radio(
            "El penúltimo riel está…",
            ["Por encima del FFL (resta)", "Por debajo del FFL (suma)"],
            key="rc_sub",
        )
        subcaso = "encima" if sub.startswith("Por encima") else "debajo"

        st.markdown("**Matriz de entrada** (llena RZ, RO, RF, RB de cada elevador):")
        rieles = ["RZ", "RO", "RF", "RB"]
        base = st.session_state.get("rc_in_df")
        cols_expected = ["Riel"] + [f"Elevador {i+1}" for i in range(n)]
        if base is None or list(base.columns) != cols_expected:
            base = pd.DataFrame({"Riel": rieles,
                                 **{f"Elevador {i+1}": [0.0] * 4 for i in range(n)}})
        in_edit = st.data_editor(base, use_container_width=True, hide_index=True,
                                 num_rows="fixed", disabled=["Riel"], key="rc_in_editor")
        st.session_state["rc_in_df"] = in_edit

        if st.button(":material/content_cut: Calcular cortes (Caso 2)", type="primary",
                     use_container_width=True, key="rc_calc2"):
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
                _kpi("Fórmula", signo), _kpi("LFKK", f"{lfkk:.0f}"),
                _kpi("LFGK", f"{lfgk:.0f}"), _kpi("Elevadores", str(_e["n"]))]),
                unsafe_allow_html=True)
            st.caption(f"Sub-caso: {_e['sub']}")
            mat = _result_matrix(["CutRZ", "CutRO", "CutRF", "CutRB"], res, _e["n"])
            st.subheader("Resultado — cortes (mm)")
            st.dataframe(mat, use_container_width=True)

            svg = rail_cut_svg({"elevadores": res}, caso=2, proyecto=_pr)
            st.subheader(":material/architecture: Diagrama de cortes")
            components.html(
                '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
                + svg + '</body></html>', height=330, scrolling=False)

            _filas = [{"Elevador": i + 1,
                       **{k: round(float(x.get(k) or 0), 1)
                          for k in ("CutRZ", "CutRO", "CutRF", "CutRB")}}
                      for i, x in enumerate(res)]
            _pdf = tool_pdf(
                "Corte de rieles — Caso 2",
                meta={"Proyecto": _pr or "—", "Sub-caso": _e["sub"], "Fórmula": signo,
                      "LFKK / LFGK": f"{lfkk:.0f} / {lfgk:.0f} mm"},
                svgs=[svg], tablas=[("Cortes por elevador", _filas)],
                notas=["Caso 2: el riel a cortar es el último instalado (arriba)."])
            render_guardar(herramienta="rieles", titulo_pdf="corte de rieles",
                           pdf_bytes=_pdf,
                           resumen=f"Caso 2 ({_e['subcaso']}) · {len(res)} elevador(es)",
                           datos={"subcaso": _e["subcaso"], "elevadores": res},
                           nombre_archivo="corte_rieles_caso2.pdf", key="rc2")
