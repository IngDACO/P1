"""
UI de la pestaña de corte de rieles.
"""
import streamlit as st
import pandas as pd

from core.rail_cut import extract_lf, compute_case1, compute_case2


def _result_matrix(labels, per_elev_values, n):
    """DataFrame: filas = labels, columnas = Elevador 1..n."""
    cols = {f"Elevador {i+1}": [round(per_elev_values[i][lab], 1) for lab in labels]
            for i in range(n)}
    return pd.DataFrame(cols, index=labels)


def render_rail_cut_tab():
    st.markdown("### ✂️ Corte de rieles")
    st.caption("Calcula el corte de los rieles de cada elevador del shaft. "
               "Carga el PDF para leer LFKK y LFGK (o ingrésalos manualmente).")

    # ── 1. PDF → LFKK / LFGK ────────────────────────────────
    st.markdown("**1. Parámetros del plano (LFKK, LFGK)**")
    pdf = st.file_uploader("PDF de planos (para LFKK / LFGK)", type=["pdf"], key="rc_pdf")
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

        if st.button("✂️ Calcular cortes (Caso 1)", type="primary", use_container_width=True, key="rc_calc1"):
            L_list = [float(x) for x in L_edit["L (mm)"].tolist()]
            res = compute_case1(lfkk, lfgk, n2500, n5000, L_list)
            st.success(f"A = {res['A']:.0f} mm")
            mat = _result_matrix(["CutRC", "CutRCW"], res["elevadores"], n)
            st.subheader("Resultado — cortes (mm)")
            st.dataframe(mat, use_container_width=True)
            with st.expander("Detalle (RC, RCW)"):
                det = _result_matrix(["RC", "RCW"], res["elevadores"], n)
                st.dataframe(det, use_container_width=True)

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

        if st.button("✂️ Calcular cortes (Caso 2)", type="primary", use_container_width=True, key="rc_calc2"):
            rows = []
            for i in range(n):
                col = in_edit[f"Elevador {i+1}"].tolist()
                rows.append({"RZ": col[0], "RO": col[1], "RF": col[2], "RB": col[3]})
            res = compute_case2(lfkk, lfgk, rows, subcaso)
            signo = "LFKK/LFGK − R" if subcaso == "encima" else "LFKK/LFGK + R"
            st.success(f"Sub-caso: {sub}  →  {signo}")
            mat = _result_matrix(["CutRZ", "CutRO", "CutRF", "CutRB"], res, n)
            st.subheader("Resultado — cortes (mm)")
            st.dataframe(mat, use_container_width=True)
