"""
UI de la pestaña de corte de rieles.
"""
import streamlit as st

from core.i18n import t, d
import pandas as pd

from core.rail_cut import (extract_lf, compute_case1, compute_case2,
                           rail_cut_svg)
from core.tool_pdf import tool_pdf
from core.tool_save_ui import render_guardar
from core import tool_save_ui
from core import plan_store
from core import plan_ui
from core import estado_vivo
from core import tabla
from core import incrustar
from core import clock
from core import theme as T
from core.num import nombre_archivo as _archivo


def _result_matrix(labels, per_elev_values, n):
    """DataFrame: filas = labels, columnas = Elevador 1..n."""
    cols = {f"{d('Lift')} {i+1}": [round(per_elev_values[i][lab], 1) for lab in labels]
            for i in range(n)}
    return pd.DataFrame(cols, index=labels)


def _firma(*vals) -> tuple:
    """v593 · Las ENTRADAS de un cálculo, para saber si lo de pantalla sigue valiendo."""
    out = []
    for v in vals:
        if isinstance(v, (list, tuple)):
            out.append(tuple(round(float(x or 0), 3) for x in v))
        elif isinstance(v, (int, float)):
            out.append(round(float(v), 3))
        else:
            out.append(str(v))
    return tuple(out)


def _cifras(items, pre):
    """v593 · Las cifras del resultado, ACTIVAS (eran HTML): cada una lleva al diagrama."""
    st.markdown(T.por_fila(f"cpx_{pre}_kpis", len(items)), unsafe_allow_html=True)
    with st.container(key=f"cpx_{pre}_kpis"):
        for _col, (_s, _l, _v) in zip(st.columns(len(items)), items):
            if _col.button(f"{_l}\n\n{_v}", key=f"cpxkpi_{pre}_{_s}", width="stretch",
                           help=t("See it on the diagram")):
                st.session_state["_bajar_cpx_rc_dibujo"] = True
                st.rerun()


def _titulo_diagrama():
    """v593 · El destino de las cifras: el bloque envuelve el TÍTULO del diagrama."""
    from core import projects_ui as _PU
    with st.container(key="cpx_rc_dibujo"):
        _PU._bajar_a("cpx_rc_dibujo", "_bajar_cpx_rc_dibujo", bloque="start")
        st.subheader(t(":material/architecture: Cutting diagram"))


def _aviso_viejo():
    st.warning(t(":material/warning: You changed data since the last calculation. What is below "
                 "belongs to the previous one — press **Calculate cuts** to update it."))


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
        st.info(t(":material/replay: Reopened calculation **{x}**. Adjust whatever you need and "
                  "calculate again.", x=_reab))

    _prj, _plano = plan_ui.selector_proyecto("rc")
    _pr = str((_prj or {}).get("Name", "") or "")     # v180: al diagrama y al PDF
    if _plano:
        plan_ui.aplicar(_plano, {"lfkk": "rc_lfkk", "lfgk": "rc_lfgk"})
        # ⚠️ v593 · FIJO (como v591/v592): salía solo en la pasada que rellenaba y se iba al
        # tocar cualquier otro campo (visto en producción).
        if _plano.get("lfkk") or _plano.get("lfgk"):
            st.caption(t(":green[:material/check_circle:] LFKK and LFGK come from the project's "
                         "drawing data."))

    st.markdown(t("**1. Drawing parameters (LFKK, LFGK)**"))
    # Plan B, plegado: desde v137 el plano vive en el PROYECTO y sus valores
    # se rellenan arriba. Esto sigue haciendo falta para un proyecto creado
    # sin plano, o para calcular sin proyecto asignado.
    with st.expander(t("Does the project have no drawing? Upload it here"), icon=":material/description:", key="exp_rail_plano"):
        st.caption(t("LFKK and LFGK will be read from this PDF. Normally they already come from the project drawing."))
        pdf = plan_store.selector(t("Drawing PDF (for LFKK / LFGK)"), "rc_pdf")   # v595 · por `t()`
        if pdf is not None and pdf.name != st.session_state.get("rc_pdf_name"):
            with st.spinner(t("Reading LFKK / LFGK from the PDF...")):
                lf = extract_lf(pdf)
            st.session_state["rc_pdf_name"] = pdf.name
            if lf.get("LFKK") is not None:
                st.session_state["rc_lfkk"] = float(lf["LFKK"])
            if lf.get("LFGK") is not None:
                st.session_state["rc_lfgk"] = float(lf["LFGK"])
            found = [k for k in ("LFKK", "LFGK") if lf.get(k) is not None]
            st.success(t("Found in the PDF: {x}. Check or complete below.",
                         x=", ".join(found) if found else t("none")))

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
    caso = st.radio(t("Which rail is cut?"), [_C1, _C2], key="rc_caso", format_func=t)

    st.markdown("---")
    _hoy = clock.today().strftime("%Y-%m-%d")

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
            # ⚠️ v593 · Cambiar el nº de ascensores CONSERVA lo tecleado (antes la tabla nacía
            # entera en 0) y estrena la tabla editable (v542: si no, Streamlit reaplica lo
            # tecleado en la tabla anterior sobre la nueva forma).
            _prev = [float(x or 0) for x in (list(base["L (mm)"]) if base is not None else [])]
            # v534 · El rótulo de cada fila salía en español («Elevador 1») en una pantalla
            # en inglés. Es solo lo que se LEE: la columna sigue llamándose igual.
            base = pd.DataFrame({"Elevador": [t("Lift {n}", n=i + 1) for i in range(n)],
                                 "L (mm)": (_prev + [0.0] * n)[:n]})
            if _prev:
                estado_vivo.tabla_nueva("rc")
        L_edit = st.data_editor(base, width="stretch", hide_index=True,
                                num_rows="fixed", disabled=["Elevador"],
                                # v540 · Clave con generación: al cambiar de obra, tabla nueva.
                                key=estado_vivo.clave_tabla("rc", "rc_L_editor"),
                                column_config=tabla.cfg())
        st.session_state["rc_L_df"] = L_edit
        L_list = [float(x or 0) for x in L_edit["L (mm)"].tolist()]
        _ahora = _firma(1, lfkk, lfgk, n, n2500, n5000, L_list)

        # El boton SOLO computa: antes todo el resultado colgaba de aqui y se
        # perdia con cualquier interaccion (bug estructural de v110).
        if st.button(t(":material/content_cut: Calculate cuts (Case 1)"), type="primary",
                     width="stretch", key="rc_calc1"):
            # ⚠️ v593 · Sin datos no se calcula: con todo en 0 daba «A 0 mm» y unos cortes sin
            # sentido, y ofrecía el PDF y guardarlo (visto en producción).
            _faltan = []
            if lfkk <= 0 or lfgk <= 0:
                _faltan.append(t("LFKK and LFGK (from the drawing, or by hand)"))
            if A <= 0:
                _faltan.append(t("how many 2500 and 5000 mm rails are installed (A = 0)"))
            _sin_l = [str(i + 1) for i, x in enumerate(L_list) if x <= 0]
            if _sin_l:
                _faltan.append(t("L for lift {x}", x=", ".join(_sin_l)))
            if _faltan:
                st.session_state.pop("rc_res", None)
                st.warning(t(":material/edit: Fill in before calculating: {x}.", x="; ".join(_faltan)))
            else:
                st.session_state["rc_res"] = {
                    "caso": 1, "res": compute_case1(lfkk, lfgk, n2500, n5000, L_list),
                    "n2500": int(n2500), "n5000": int(n5000), "n": int(n),
                    "lfkk": float(lfkk), "lfgk": float(lfgk), "firma": _ahora}

        _e = st.session_state.get("rc_res")
        if _e and _e.get("caso") == 1:
            res = _e["res"]
            # ⚠️ v593 · Lo de abajo es del ÚLTIMO cálculo: si un dato cambió, se dice — y no se
            # descarga ni se guarda. Y sus cifras y el PDF llevan LFKK/LFGK DEL CÁLCULO (antes
            # los de ahora: «LFKK 1150» junto a unos cortes hechos con 0, visto en producción).
            _vig = _e.get("firma") == _ahora
            if not _vig:
                _aviso_viejo()
            _lk, _lg = _e.get("lfkk", lfkk), _e.get("lfgk", lfgk)
            _cifras([("a", t("A (stack installed)"), f"{res['A']:.0f} mm"),
                     ("lfkk", t("LFKK"), f"{_lk:.0f}"), ("lfgk", t("LFGK"), f"{_lg:.0f}"),
                     ("n", t("Lifts"), str(_e["n"]))], "rc")
            mat = _result_matrix(["CutRC", "CutRCW"], res["elevadores"], _e["n"])
            st.subheader(t("Result — cuts (mm)"))
            st.dataframe(mat, width="stretch", column_config=tabla.cfg())
            # v593 · el signo, dicho junto a la tabla (solo lo decía la leyenda del diagrama)
            st.caption(t("The cut goes on the 1st rail (the bottom one, first installed). "
                         "**Negative = trim** that much off it · **positive = it falls short**: "
                         "add that much. Same signed value as the diagram."))
            with st.expander(t("Detail (RC, RCW)")):
                det = _result_matrix(["RC", "RCW"], res["elevadores"], _e["n"])
                st.dataframe(det, width="stretch", column_config=tabla.cfg())

            svg = rail_cut_svg(res, caso=1, n2500=_e["n2500"], n5000=_e["n5000"], proyecto=_pr)
            _titulo_diagrama()
            incrustar.dibujo('<!DOCTYPE html><html><body style="margin:0;background:transparent">'
                + svg + '</body></html>', 390)

            _filas = [{d("Lift"): i + 1, "L (mm)": round(x["L"], 1),
                       "RC (mm)": round(x["RC"], 1), "CutRC (mm)": round(x["CutRC"], 1),
                       "RCW (mm)": round(x["RCW"], 1), "CutRCW (mm)": round(x["CutRCW"], 1)}
                      for i, x in enumerate(res["elevadores"])]
            _pdf = tool_pdf(
                d("Rail cutting — Case 1"),
                meta={d("Project"): _pr or "—",
                      d("A (installed stack)"): f"{res['A']:.0f} mm",
                      d("Make-up"): f"{_e['n2500']}×2500 + {_e['n5000']}×5000",
                      "LFKK / LFGK": f"{_lk:.0f} / {_lg:.0f} mm"},
                svgs=[svg], tablas=[(d("Cuts per lift"), _filas)],
                notas=[d("Case 1: the rail to cut is the first one installed (at the bottom). "
                         "CutRC = RC − A, CutRCW = RCW − A."),
                       d("Negative = trim that much off the 1st rail; positive = it falls short: "
                         "add that much.")])
            render_guardar(herramienta="rieles", titulo_pdf=d("rail cutting"),
                           pdf_bytes=_pdf,
                           # v593 · en inglés (decía «Caso 1 · … E1: …»)
                           resumen=d("Case 1 · A {a} · {x}", a=f"{res['A']:.0f}", x=", ".join(
                               d("Lift {i}: {c}/{w}", i=i + 1, c=f"{x['CutRC']:.0f}",
                                 w=f"{x['CutRCW']:.0f}") for i, x in enumerate(res["elevadores"]))),
                           datos=res,
                           nombre_archivo=f"Rail_cutting_case1_{_archivo(_pr, 'shaft')}_{_hoy}.pdf",
                           key="rc1", obra_id=str((_prj or {}).get("ID", "")),   # v592
                           vigente=_vig)                                         # v593

    # ════════════════════════════════════════════════════════
    # CASO 2
    # ════════════════════════════════════════════════════════
    else:
        st.markdown(t("**Case 2 — sub-case**"))
        # ⚠️ v593 · Constantes, como el caso (ver arriba): la rama se decidía con
        # `sub.startswith("Above")` sobre el TEXTO — la trampa que dejó muerto el Caso 1 en v441.
        _S1 = "Above the FFL (subtract)"
        _S2 = "Below the FFL (add)"
        sub = st.radio(t("The second-to-last rail is…"), [_S1, _S2], key="rc_sub", format_func=t)
        subcaso = "encima" if sub == _S1 else "debajo"      # código del motor (`compute_case2`)

        st.markdown(t("**Input matrix** (fill in RZ, RO, RF, RB for each lift):"))
        st.caption(t("RZ, RO = car rails · RF, RB = counterweight rails · in mm, measured on site."))
        rieles = ["RZ", "RO", "RF", "RB"]
        base = st.session_state.get("rc_in_df")
        cols_expected = ["Riel"] + [f"Elevador {i+1}" for i in range(n)]
        if base is None or list(base.columns) != cols_expected:
            # ⚠️ v593 · Las columnas que ya había CONSERVAN lo tecleado (antes, todo a 0).
            _prev = ({c: list(base[c]) for c in base.columns if c != "Riel"}
                     if base is not None else {})
            base = pd.DataFrame({"Riel": rieles,
                                 **{f"Elevador {i+1}": [0.0] * 4 for i in range(n)}})
            for _c, _v in _prev.items():
                if _c in base.columns:
                    base[_c] = [float(x or 0) for x in _v]
            if _prev:
                estado_vivo.tabla_nueva("rc")
        # v534 · «Elevador N» es la CLAVE de la columna (se lee de vuelta al calcular y
        # vive en la sesión): se le cambia la etiqueta, no el nombre (v450).
        in_edit = st.data_editor(base, width="stretch", hide_index=True,
                                 num_rows="fixed", disabled=["Riel"],
                                 key=estado_vivo.clave_tabla("rc", "rc_in_editor"),
                                 column_config=tabla.cfg(extra={
                                     f"Elevador {i+1}": st.column_config.Column(t("Lift {n}", n=i + 1))
                                     for i in range(n)}))
        st.session_state["rc_in_df"] = in_edit
        rows = []
        for i in range(n):
            col = in_edit[f"Elevador {i+1}"].tolist()
            rows.append({"RZ": col[0], "RO": col[1], "RF": col[2], "RB": col[3]})
        _ahora = _firma(2, lfkk, lfgk, n, subcaso,
                        [float(r[k] or 0) for r in rows for k in ("RZ", "RO", "RF", "RB")])

        if st.button(t(":material/content_cut: Calculate cuts (Case 2)"), type="primary",
                     width="stretch", key="rc_calc2"):
            # ⚠️ v593 · Sin datos no se calcula (todo en 0 daba los LF a pelo, 1150 y 980).
            _faltan = []
            if lfkk <= 0 or lfgk <= 0:
                _faltan.append(t("LFKK and LFGK (from the drawing, or by hand)"))
            _vacios = [str(i + 1) for i, r in enumerate(rows)
                       if not any(float(r[k] or 0) for k in ("RZ", "RO", "RF", "RB"))]
            if _vacios:
                _faltan.append(t("RZ, RO, RF and RB for lift {x}", x=", ".join(_vacios)))
            if _faltan:
                st.session_state.pop("rc_res", None)
                st.warning(t(":material/edit: Fill in before calculating: {x}.", x="; ".join(_faltan)))
            else:
                st.session_state["rc_res"] = {
                    "caso": 2, "res": compute_case2(lfkk, lfgk, rows, subcaso),
                    "subcaso": subcaso, "sub": sub, "n": int(n),
                    "lfkk": float(lfkk), "lfgk": float(lfgk), "firma": _ahora}

        _e = st.session_state.get("rc_res")
        if _e and _e.get("caso") == 2:
            res = _e["res"]
            _vig = _e.get("firma") == _ahora
            if not _vig:
                _aviso_viejo()
            _lk, _lg = _e.get("lfkk", lfkk), _e.get("lfgk", lfgk)
            signo = "LFKK/LFGK − R" if _e["subcaso"] == "encima" else "LFKK/LFGK + R"
            _cifras([("f", t("Formula"), signo), ("lfkk", t("LFKK"), f"{_lk:.0f}"),
                     ("lfgk", t("LFGK"), f"{_lg:.0f}"), ("n", t("Lifts"), str(_e["n"]))], "rc2")
            _sub_txt = t(_S1) if _e["subcaso"] == "encima" else t(_S2)
            st.caption(t("Sub-case: {x}", x=_sub_txt))
            mat = _result_matrix(["CutRZ", "CutRO", "CutRF", "CutRB"], res, _e["n"])
            st.subheader(t("Result — cuts (mm)"))
            st.dataframe(mat, width="stretch", column_config=tabla.cfg())
            st.caption(t("The cut (mm) goes on the TOP rail of each line: car RZ, RO · "
                         "counterweight RF, RB."))

            svg = rail_cut_svg({"elevadores": res}, caso=2, proyecto=_pr)
            _titulo_diagrama()
            incrustar.dibujo('<!DOCTYPE html><html><body style="margin:0;background:transparent">'
                + svg + '</body></html>', 330)

            _filas = [{d("Lift"): i + 1,
                       **{k: round(float(x.get(k) or 0), 1)
                          for k in ("CutRZ", "CutRO", "CutRF", "CutRB")}}
                      for i, x in enumerate(res)]
            _sub_doc = d("above the FFL") if _e["subcaso"] == "encima" else d("below the FFL")
            _pdf = tool_pdf(
                d("Rail cutting — Case 2"),
                meta={d("Project"): _pr or "—", d("Sub-case"): _sub_doc, d("Formula"): signo,
                      "LFKK / LFGK": f"{_lk:.0f} / {_lg:.0f} mm"},
                svgs=[svg], tablas=[(d("Cuts per lift"), _filas)],
                notas=[d("Case 2: the rail to cut is the last one installed (at the top).")])
            render_guardar(herramienta="rieles", titulo_pdf=d("rail cutting"),
                           pdf_bytes=_pdf,
                           # v593 · en inglés y con su plural (decía «(encima) · 2 lift(s)»)
                           resumen=(d("Case 2 ({s}) · {n} lift", s=_sub_doc, n=len(res)) if len(res) == 1
                                    else d("Case 2 ({s}) · {n} lifts", s=_sub_doc, n=len(res))),
                           datos={"subcaso": _e["subcaso"], "elevadores": res},
                           nombre_archivo=f"Rail_cutting_case2_{_archivo(_pr, 'shaft')}_{_hoy}.pdf",
                           key="rc2", obra_id=str((_prj or {}).get("ID", "")),   # v592
                           vigente=_vig)                                         # v593
