"""
Seccion 📐 Survey de elevador — UI completa.

Extraido de app.py en v125. Era el UNICO modulo grande que vivia dentro de
app.py (~1290 de sus ~1650 lineas), a diferencia de plumb_ui / prestart_ui /
timeclock_ui / projects_ui / auth_ui. Esa concentracion causo v118 y v120: un
error de indentacion dentro de un archivo enorme con dos fases anidadas, que
compilaba perfecto y rompia en produccion.

`render_survey_tab(_ROL, _GRUPO)` recibe rol y grupo del login. Los parametros
conservan esos nombres a proposito: el cuerpo movido los usa tal cual, asi la
extraccion no tuvo que renombrar nada.
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import date
from extractors.schindler import extract_from_pdf, PARAMS as PDF_PARAMS, PARAM_DESCRIPTIONS
from core.calculations import calculate_limits, apply_offsets, analyze_matrix, validate_inputs
from core.optimizer    import optimize
from core.bs_logic     import find_bs_step
from core.report       import generate_report
from core.excel_io     import export_survey_excel, import_survey_excel
from core.highlighting import cell_state, ctrl_applies_to_cell, streamlit_style, OR_OL_COLS
from core.interpretation  import generate_interpretation, generate_user_interpretation
from core.email_notify    import send_usage_notification
from core.user_report     import generate_user_report
from core.diagrams        import (render_floor_plans_html, floors_with_issues,
                                  floor_plans_pdf, shaft_iso_svg)
from core.schedule        import build_schedule, detect_flags, schedule_svg
from core.plumb           import (compute_plumb, plumb_svg, plumb_table, plumb_checks,
                                  plumb_iso_svg, plumb_detail_svg, plumb_card_svg)
from core                 import projects as projects_data
from core                 import drive_store
from core                 import notify
from core.field_pack      import field_pack_pdf
from core.auth            import get_user as auth_get_user
from core                 import credentials
from core                 import plan_store
from core.auth import can_reports

SURVEY_COLS = ["WR", "FR", "OR", "WL", "FL", "OL"]

def _cfg_from_state():
    """Configuración del survey leída de session_state (no de variables locales).

    Necesario porque el Survey se divide en fases: cuando estás en 'Resultados' los
    widgets del paso 2 NO se instancian, así que las variables locales no existirían.
    Los valores sí persisten en session_state, que es la fuente de verdad."""
    _wl = st.session_state.get("cfg_wall_yn", "N") == "Y"
    _ci = st.session_state.get("cfg_ctrl_yn", "N") == "Y"
    return {
        "omega_side":    st.session_state.get("cfg_omega_side", "R"),
        "offset_side":   st.session_state.get("cfg_offset_side", "R"),
        "wall_limiting": _wl,
        "wall_stop":     int(st.session_state.get("cfg_wall_stop", 1)) if _wl else None,
        "wall_side":     st.session_state.get("cfg_wall_side", "R") if _wl else None,
        "ctrl_in_frame": _ci,
        "ctrl_side":     st.session_state.get("cfg_ctrl_side", "R") if _ci else None,
        "ns":            int(st.session_state.get("ns", 2)),
    }

_GRUPOS_PARAM = [
    ("🏗 Hueco",           ["BS", "TS"]),
    ("🛗 Cabina",          ["BK", "TK", "BKS"]),
    ("🚪 Puerta / umbral", ["BT", "TKA", "TKS", "TSW"]),
    ("📍 Frontal",         ["TKSW", "BKF1", "BKF2"]),
    ("↔️ Laterales",       ["SF1", "SF2"]),
    ("⚖️ Contrapeso",      ["BGS", "SG", "TG"]),
]

USER_ONLY = {
    "BSR":            "Ancho real del hueco medido en obra (mm)",
    "FS":             "Distancia frontal de seguridad (mm)",
    "FRAME":          "Marco de puerta de entrada (mm)",
    "RAIL":           "Ancho de la cabeza del riel (mm)",
    "OFFSET_CABIN":   "Offset de cabina (mm)",
    "LengthTemplate": "Longitud del template de plomada (mm) — para el esquema de plomado",
}

def init_state():
    if "initialized" in st.session_state:
        return
    # PDF params
    for p in PDF_PARAMS:
        st.session_state[f"inp_{p}"] = 0.0
    # User params
    for p in USER_ONLY:
        st.session_state[f"inp_{p}"] = 0.0
    # Config defaults (con keys para que radios lean de session_state)
    st.session_state["cfg_omega_side"]   = "R"
    st.session_state["cfg_wall_yn"]      = "N"
    st.session_state["cfg_offset_side"]  = "R"
    st.session_state["cfg_wall_stop"]    = 1
    st.session_state["cfg_wall_side"]    = "R"
    st.session_state["cfg_ctrl_yn"]      = "N"
    st.session_state["cfg_ctrl_side"]    = "R"
    # Otros
    st.session_state["pdf_extracted"]  = {}
    st.session_state["last_pdf_name"]  = None
    st.session_state["pdf_bytes"]      = None
    st.session_state["ns"]             = 2   # mínimo neutro; el NS real sale del plano (NUMBER OF STOPS)
    st.session_state["survey_df"]      = pd.DataFrame({c: [0.0]*2 for c in SURVEY_COLS})
    st.session_state["survey_original_input"] = None   # snapshot al momento del cálculo
    st.session_state["calc_results"]   = None
    st.session_state["chat_history"]   = []
    st.session_state["proyecto"]       = ""
    st.session_state["cliente"]        = ""
    st.session_state["ubicacion"]      = ""
    st.session_state["ingeniero"]      = ""
    st.session_state["initialized"]    = True

def render_survey_tab(_ROL, _GRUPO):
    for _k in [k for k in list(st.session_state.keys())
               if k.startswith("inp_") or k.startswith("cfg_")
               or k in ("ns", "proyecto", "cliente", "ubicacion", "ingeniero")]:
        st.session_state[_k] = st.session_state[_k]

    # ── Empezar de cero (se procesa ANTES de crear los widgets) ──
    if st.session_state.pop("_reset_survey", False):
        # Los inp_*/cfg_* sí se borran (los widgets los recrean con su valor por defecto).
        for _k in [k for k in list(st.session_state.keys())
                   if k.startswith("inp_") or k.startswith("cfg_")]:
            st.session_state.pop(_k, None)
        # ⚠️ El RESTO se REINICIA a su valor por defecto, NO se borra: hay lecturas por
        # atributo (st.session_state.last_pdf_name…) que lanzan AttributeError si falta la clave.
        st.session_state["pdf_extracted"] = {}
        st.session_state["last_pdf_name"] = None
        st.session_state["pdf_bytes"]     = None
        st.session_state["ns"]            = 2
        st.session_state["survey_df"]     = pd.DataFrame({c: [0.0] * 2 for c in SURVEY_COLS})
        st.session_state["calc_results"]  = None
        for _k in ("proyecto", "cliente", "ubicacion", "ingeniero"):
            st.session_state[_k] = ""
        for _k in ("last_excel_id", "_calc_sig", "ns_msg", "rail_ref_msg", "sched_rows",
                   "sched_start", "_rebuilt_from", "_diag_pdf", "sol_activa", "diag_pisos"):
            st.session_state.pop(_k, None)

    # ── Duplicar para el siguiente elevador (conserva parámetros, limpia la matriz) ──
    if st.session_state.pop("_dup_survey", False):
        _nsd = int(st.session_state.get("ns", 2))
        st.session_state["survey_df"]    = pd.DataFrame({c: [0.0] * _nsd for c in SURVEY_COLS})
        st.session_state["calc_results"] = None
        for _k in ("_calc_sig", "sched_rows", "sched_start", "_diag_pdf", "_rebuilt_from"):
            st.session_state.pop(_k, None)
        st.session_state["_dup_msg"] = True
        st.session_state["_fase_pending"] = "📝 Datos del survey"

    _pend = st.session_state.pop("_import_pending", None)
    if _pend:
        if _pend.get("df") is not None:
            st.session_state["survey_df"] = _pend["df"]
        if _pend.get("ns"):
            st.session_state["ns"] = int(_pend["ns"])
        for _k, _v in (_pend.get("params") or {}).items():
            st.session_state[f"inp_{_k}"] = float(_v)
        for _k, _v in (_pend.get("cfg") or {}).items():
            st.session_state[_k] = _v
        st.success("✅ Matriz, parámetros y configuración cargados desde el Excel."
                   if _pend.get("todo") else
                   "✅ Matriz cargada desde el Excel (los parámetros del plano se conservan).")

    if st.session_state.pop("_dup_msg", False):
        st.success("📑 Survey duplicado: se conservaron parámetros y configuración. "
                   "Ingresa la matriz del siguiente elevador y calcula.")

    # Aviso cuando se llega desde "Reconstruir proyecto" (Mi grupo → detalle)
    if st.session_state.get("_rebuilt_from"):
        st.info(f"📥 Cargaste el proyecto **{st.session_state['_rebuilt_from']}**. "
                "Pulsa **🚀 Calcular** para regenerar diagramas e informes.")

    # ── Identificación del proyecto ───────────────────────
    _id1, _id2 = st.columns(2)
    _id1.text_input("🏗 Proyecto", key="proyecto", placeholder="Ej: Torre Central")
    _id2.text_input("🏢 Cliente", key="cliente", placeholder="Empresa / constructora")
    _id3, _id4 = st.columns(2)
    _id3.text_input("📍 Ubicación de la obra", key="ubicacion",
                    placeholder="Dirección — aparece en el informe")
    _id4.text_input("👷 Ingeniero responsable", key="ingeniero",
                    placeholder="Quien realiza el survey")
    if st.session_state.get("ubicacion", "").strip():
        from core import maps as _maps
        _id3.caption(_maps.maps_link_md(st.session_state["ubicacion"], "ver en Maps"))

    with st.expander("🧹 Empezar un survey nuevo"):
        st.caption("Borra parámetros, matriz, configuración y resultados de esta sesión. "
                   "No afecta a los proyectos ya guardados.")
        if st.button("🧹 Limpiar todo y empezar de cero", key="btn_reset_survey"):
            st.session_state["_reset_survey"] = True
            st.rerun()

    # ══════════════════════════════════════════════════════

    # ══════════════════════════════════════════════════════
    # FASES DEL SURVEY: 📝 Datos (pasos 1-3) · 📊 Resultados (4-7)
    # ══════════════════════════════════════════════════════
    # El cambio de fase se aplica ANTES de crear el radio (no se puede escribir la
    # clave de un widget ya instanciado).
    _fp = st.session_state.pop("_fase_pending", None)
    if _fp:
        st.session_state["survey_fase"] = _fp
    _FASE_DATOS, _FASE_RES = "📝 Datos del survey", "📊 Resultados e informes"
    _fase = st.radio("Fase", [_FASE_DATOS, _FASE_RES], horizontal=True,
                     key="survey_fase", label_visibility="collapsed")
    st.markdown("---")

    # Helper: highlight para DataFrames de Streamlit
    # ══════════════════════════════════════════════════════
    def make_highlighter(lim_map, min_vals, max_vals, cut_cols, ctrl_in_frame_, ctrl_side_):
        """Devuelve una función que aplica CSS de highlight a un DataFrame."""
        def _highlight(df):
            styles = pd.DataFrame("", index=df.index, columns=df.columns)
            total_rows = len(df)
            for ri_off, idx in enumerate(df.index):
                for col in df.columns:
                    if col not in lim_map:
                        continue
                    val = df.at[idx, col]
                    state = cell_state(
                        value       = val,
                        col         = col,
                        lim         = lim_map[col],
                        min_val     = min_vals.get(f"MIN_{col}"),
                        max_val     = max_vals.get(f"MAX_{col}"),
                        in_cut_cols = col in cut_cols,
                        ctrl_applies= ctrl_applies_to_cell(ri_off, total_rows, col, ctrl_in_frame_, ctrl_side_),
                    )
                    styles.at[idx, col] = streamlit_style(state)
            return styles
        return _highlight

    # ══════════════════════════════════════════════════════
    def _survey_signature():
        """Huella de las entradas (parámetros + configuración + matriz).
        Si cambia respecto al último cálculo, los resultados en pantalla están obsoletos."""
        _c = _cfg_from_state()
        import hashlib, json as _json
        base = {
            "params": {p: st.session_state.get(f"inp_{p}", 0.0)
                       for p in list(PDF_PARAMS) + list(USER_ONLY.keys())},
            "cfg": [_c["omega_side"], _c["offset_side"], _c["wall_limiting"], _c["wall_stop"], _c["wall_side"],
                    _c["ctrl_in_frame"], _c["ctrl_side"], _c["ns"]],
            "matriz": st.session_state.survey_df.to_dict("records"),
        }
        return hashlib.md5(_json.dumps(base, sort_keys=True, default=str).encode()).hexdigest()

    def _leyenda_matriz():
        """Clave de color de las tablas.

        Se quito del sidebar en v93 y nunca se repuso: desde entonces las celdas
        salian coloreadas sin que nada explicara que significan. Usa las MISMAS
        palabras que los planos ("fuera de limite") para que tabla y dibujo se
        lean como un solo lenguaje.
        """
        st.markdown(
            '<div style="display:flex;flex-wrap:wrap;gap:14px;align-items:center;'
            'font-size:0.78rem;color:#5f6b7a;margin:-6px 0 10px 2px">'
            '<span><span style="display:inline-block;width:11px;height:11px;'
            'background:#c0392b;border-radius:2px;vertical-align:-1px"></span> '
            'fuera de límite — el valor más crítico de su columna</span>'
            '<span><span style="display:inline-block;width:11px;height:11px;'
            'background:#f1948a;border-radius:2px;vertical-align:-1px"></span> '
            'fuera de límite</span>'
            '<span><span style="display:inline-block;width:11px;height:11px;'
            'background:#e67e22;border-radius:2px;vertical-align:-1px"></span> '
            'requiere corte (OR/OL)</span>'
            '<span style="opacity:.85">WR·WL·FR·FL incumplen por <b>debajo</b> '
            'del límite; OR·OL por <b>encima</b>.</span>'
            '</div>', unsafe_allow_html=True)

    def _render_survey_results(r):
        """Dibuja TODOS los resultados del cálculo leyendo de `calc_results`.

        Vive FUERA del botón a propósito: antes todo esto se dibujaba dentro del
        `if st.button("Calcular")`, así que cualquier interacción posterior (cambiar
        un dato, descargar un informe, abrir un desplegable) borraba los resultados
        y obligaba a recalcular. Ahora persisten entre reruns.
        """
        all_params = r["all_params"]
        limits     = r["limits"]
        analysis   = r["analysis"]
        lim_map    = r["lim_map"]
        opt_result = r.get("optimizer_result") or {}
        bs_result  = r.get("bs_result") or {}
        plumb_res  = r.get("plumb")
        interpretation = r.get("interpretation") or {}

        survey_adj_df = r["survey_adj"]
        survey_adj    = survey_adj_df.to_dict("records")
        wall_limiting_ = bool(all_params.get("WALL_LIMITING"))
        ctrl_in_frame_ = bool(all_params.get("CTRL_IN_FRAME"))
        ctrl_side_     = all_params.get("CTRL_SIDE")
        cut_cols       = ["OR", "OL"] if not wall_limiting_ else []
        min_vals = {f"MIN_{c}": analysis[f"MIN_{c}"] for c in SURVEY_COLS}
        max_vals = {f"MAX_{c}": analysis.get(f"MAX_{c}", analysis[f"MIN_{c}"]) for c in SURVEY_COLS}
        highlight = make_highlighter(lim_map, min_vals, max_vals, cut_cols,
                                     ctrl_in_frame_, ctrl_side_)

        # ── Resumen ejecutivo: lo importante de un vistazo ──
        _b = opt_result.get("best")
        if _b:
            _off = int(_b.get("total_off", 0))
            e1, e2, e3, e4 = st.columns(4)
            e1.metric("Lateral (RL)",  f"{_b['rl']:+.1f} mm")
            e2.metric("Frontal (FB)",  f"{_b.get('fb_applied', _b['fb']):+.1f} mm")
            e3.metric("Fuera de límite", _off)
            e4.metric("Soluciones óptimas", len(opt_result.get("all_solutions", [])))
            if _off == 0:
                st.success("✅ Solución encontrada **sin valores fuera de límite**.")
            else:
                _cols_off = [c for c in SURVEY_COLS if (_b.get("off_by_col") or {}).get(c, 0)]
                st.warning(f"⚠️ La solución activa deja **{_off} valor(es) fuera de límite**"
                           + (f" en: **{', '.join(_cols_off)}**." if _cols_off else "."))
        else:
            st.error("❌ No se encontró ninguna combinación válida con estos parámetros.")

        with st.expander("📊 Parámetros calculados", expanded=False):
            st.dataframe(
                pd.DataFrame([
                    {"Parámetro": k, "Valor": round(v, 3) if isinstance(v, (int, float)) else v}
                    for k, v in limits.items()
                ]),
                use_container_width=True, hide_index=True
            )

        st.subheader("Matriz SURVEY ajustada")
        st.dataframe(survey_adj_df.style.apply(highlight, axis=None),
                     use_container_width=True)
        _leyenda_matriz()

        st.subheader("Resumen por columna — Estado inicial")
        summary = []
        for col in SURVEY_COLS:
            lim_c = lim_map[col]
            viols = []
            for i, row in enumerate(survey_adj):
                v  = row[col]
                el = lim_c
                if ctrl_applies_to_cell(i, len(survey_adj), col, ctrl_in_frame_, ctrl_side_):
                    el -= 70
                if col in OR_OL_COLS:
                    if v > el: viols.append(str(i + 1))
                else:
                    if v < el: viols.append(str(i + 1))
            ext = round(analysis.get(f"MAX_{col}", analysis[f"MIN_{col}"]), 2) \
                  if col in OR_OL_COLS else round(analysis[f"MIN_{col}"], 2)
            summary.append({
                "Columna":             col,
                "Límite (mm)":         round(lim_c, 2),
                "Fuera límite":        analysis[f"{col}_OFF_COUNT"],
                "Niveles incumplidos": ", ".join(viols) if viols else "—",
                "Min / Max (mm)":      ext,
                "Diferencia (mm)":     round(analysis[f"DIF_{col}"], 2),
            })
        st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)

        st.info(
            f"**MAX OFF RL:** {analysis['MAX_OFF_RL']:.2f} mm  |  "
            f"**MAX OFF FB:** {analysis['MAX_OFF_FB']:.2f} mm  |  "
            f"**BC_CALC:** {limits.get('BC_CALC', 0):.2f} mm  |  "
            f"**DIF TSW-FS:** {limits.get('DIF_TSW_FS', 0):.2f} mm  |  "
            f"**FB máx. hacia atrás:** {limits.get('FB_MAX_BACK', 0):.2f} mm"
        )

        # ── Optimización ──────────────────────────────────────
        st.subheader("🔍 Optimización")
        best          = opt_result.get("best")
        all_solutions = opt_result.get("all_solutions", [])
        step_log      = opt_result.get("step_log", [])

        if best:
            st.success(
                f"✅ Se encontraron **{len(all_solutions)} solución(es) óptima(s)** con "
                f"**{best['total_off']} valor(es) fuera de límite**"
            )
            best_pair = (best["rl"], best["fb"])
            sorted_solutions = sorted(
                all_solutions,
                key=lambda s: (
                    0 if (s["rl"], s["fb"]) == best_pair else 1,
                    abs(s["rl"]) + abs(s.get("fb_applied", s["fb"]))
                )
            )

            # ── Solución ACTIVA: el optimizador propone, pero decide el ingeniero ──
            _idx_act = next((k for k, s in enumerate(sorted_solutions)
                             if (s["rl"], s["fb"]) == best_pair), 0)
            if len(sorted_solutions) > 1:
                # ⚠️ .1f obligatorio: el optimizador barre en pasos de 0.5 mm, así que
                # RL/FB pueden ser x.5. Con .0f, RL −6.0 y RL −6.5 daban la MISMA
                # etiqueta y las soluciones no se podían distinguir en el desplegable.
                _lbl = [f"RL {s['rl']:+.1f} · FB {s.get('fb_applied', s['fb']):+.1f} · "
                        f"{s['total_off']} fuera" for s in sorted_solutions]
                _sel = st.selectbox(
                    "🎯 Solución activa — se usa en diagramas, plomado e informes",
                    range(len(_lbl)), index=_idx_act, format_func=lambda k: _lbl[k],
                    key="sol_activa",
                )
                if _sel != _idx_act:
                    _nueva = sorted_solutions[_sel]
                    r["optimizer_result"]["best"] = _nueva
                    try:   # el plomado depende del desplazamiento → recalcular
                        r["plumb"] = compute_plumb(
                            {"BKS": all_params["BKS"],  "RAIL": all_params["RAIL"],
                             "TKSW": all_params["TKSW"],
                             "LengthTemplate": all_params.get("LengthTemplate", 0.0),
                             "SF1": all_params["SF1"], "SF2": all_params["SF2"],
                             "BSR": all_params["BSR"], "BS": all_params["BS"]},
                            survey_disp={"rl": _nueva["rl"], "fb": _nueva["fb_applied"]})
                    except Exception:
                        r["plumb"] = None
                    st.rerun()

                with st.expander("⚖️ Comparar soluciones lado a lado", expanded=False):
                    _comp = []
                    for k, s in enumerate(sorted_solutions):
                        _obc = s.get("off_by_col", {}) or {}
                        _comp.append({
                            "": "🎯" if k == _idx_act else "",
                            "#": k + 1, "RL": s["rl"], "FB": s["fb"],
                            "FB aplic.": s.get("fb_applied", s["fb"]),
                            "Fuera": s["total_off"],
                            **{c: _obc.get(c, 0) for c in SURVEY_COLS},
                        })
                    st.dataframe(pd.DataFrame(_comp), hide_index=True, use_container_width=True)
            for idx_sol, sol in enumerate(sorted_solutions):
                is_best   = (sol["rl"], sol["fb"]) == best_pair
                fb_ap     = sol.get("fb_applied", sol["fb"])
                fb_suffix = f"  |  FB aplic. = {fb_ap:.1f} mm" if abs(fb_ap - sol["fb"]) > 0.01 else ""
                sol_label = f"{'⭐ ' if is_best else ''}Solución {idx_sol+1} — RL = {sol['rl']:+.1f} mm  |  FB = {sol['fb']:+.1f} mm{fb_suffix}"
                with st.expander(sol_label, expanded=(idx_sol == 0)):
                    sol_df  = pd.DataFrame(sol["matrix"])
                    sol_min = {f"MIN_{c}": min(sol_df[c]) for c in SURVEY_COLS}
                    sol_max = {f"MAX_{c}": max(sol_df[c]) for c in SURVEY_COLS}
                    if not wall_limiting_:
                        lor_v        = lim_map["OR"]
                        lol_v        = lim_map["OL"]
                        last_sol_idx = len(sol_df) - 1
                        cut_or_vals, cut_ol_vals = [], []
                        for i, (or_v, ol_v) in enumerate(zip(sol_df["OR"], sol_df["OL"])):
                            or_lim = lor_v - 70 if (ctrl_in_frame_ and ctrl_side_ == "R" and i == last_sol_idx) else lor_v
                            ol_lim = lol_v - 70 if (ctrl_in_frame_ and ctrl_side_ == "L" and i == last_sol_idx) else lol_v
                            cut_or_vals.append(round(or_v - or_lim, 1) if or_v - or_lim > 0 else "")
                            cut_ol_vals.append(round(ol_v - ol_lim, 1) if ol_v - ol_lim > 0 else "")
                        sol_df.insert(3, "CUT OR", cut_or_vals)
                        sol_df.insert(7, "CUT OL", cut_ol_vals)
                    sol_highlighter = make_highlighter(lim_map, sol_min, sol_max, cut_cols,
                                                       ctrl_in_frame_, ctrl_side_)
                    st.dataframe(sol_df.style.apply(sol_highlighter, axis=None),
                                 use_container_width=True)
                    _leyenda_matriz()
                    if not wall_limiting_:
                        st.caption("CUT OR / CUT OL: valor a cortar si OR/OL supera el límite (OR/OL − LIMIT). Positivo = requiere corte. Blanco = dentro del límite.")
                    sol_sum = []
                    for col in SURVEY_COLS:
                        col_vals = [x[col] for x in sol["matrix"]]
                        lim_c = lim_map[col]
                        if col in OR_OL_COLS:
                            ext_c = max(col_vals); dif_c = ext_c - lim_c
                            off_c = sum(1 for v in col_vals if v > lim_c)
                            lbl   = "Máximo (mm)"
                            viols_s = [str(i+1) for i, v in enumerate(col_vals) if v > lim_c]
                        else:
                            ext_c = min(col_vals); dif_c = lim_c - ext_c
                            off_c = sum(1 for v in col_vals if v < lim_c)
                            lbl   = "Mínimo (mm)"
                            viols_s = [str(i+1) for i, v in enumerate(col_vals) if v < lim_c]
                        sol_sum.append({
                            "Columna":       col,
                            "Límite (mm)":   round(lim_c, 2),
                            "Fuera límite":  off_c,
                            "Niveles":       ", ".join(viols_s) if viols_s else "—",
                            lbl:             round(ext_c, 2),
                            "Dif vs Límite": round(dif_c, 2),
                        })
                    st.dataframe(pd.DataFrame(sol_sum), use_container_width=True, hide_index=True)

            # El log expone la traza del optimizador (pasos, descartes y por que).
            # Es logica propietaria: misma regla que ya aplica el agente IA y que
            # excluye el informe del cliente. Solo el propietario lo ve.
            if _ROL == "propietario":
                with st.expander(f"📋 Log del optimizador ({len(step_log)} pasos evaluados)", expanded=False):
                    valid_steps  = [s for s in step_log if s.get("status") == "VALID"]
                    skip_steps   = [s for s in step_log if s.get("status") == "SKIP"]
                    skip_phys    = [s for s in skip_steps if s.get("skip_type", "").startswith("physical")]
                    skip_wall    = [s for s in skip_steps if s.get("skip_type") == "wall"]
                    skip_frame   = [s for s in skip_steps if s.get("skip_type") == "frame_opening"]
                    st.caption(
                        f"Válidos: {len(valid_steps)}  |  "
                        f"Omitidos por límite físico (RL/FB): {len(skip_phys)}  |  "
                        f"Omitidos por pared: {len(skip_wall)}  |  "
                        f"Omitidos por apertura tapada: {len(skip_frame)}"
                    )
                    if valid_steps:
                        opt_pairs = {(s["rl"], s["fb"]) for s in all_solutions}
                        best_p    = (best["rl"], best["fb"])
                        log_rows  = []
                        for s in valid_steps:
                            obc  = s.get("off_by_col", {})
                            pair = (s["rl"], s["fb"])
                            if pair == best_p:        estado = "⭐ SELECCIONADA"
                            elif pair in opt_pairs:   estado = "✅ ÓPTIMA"
                            else:                     estado = ""
                            log_rows.append({
                                "RL": s["rl"], "FB": s["fb"],
                                "FB aplic.": s.get("fb_applied", s["fb"]),
                                "Total OFF": s["total_off"],
                                "WR": obc.get("WR", 0), "FR": obc.get("FR", 0),
                                "OR": obc.get("OR", 0), "WL": obc.get("WL", 0),
                                "FL": obc.get("FL", 0), "OL": obc.get("OL", 0),
                                "Estado": estado,
                            })
                        log_rows = (
                            [x for x in log_rows if x["Estado"] == "⭐ SELECCIONADA"] +
                            [x for x in log_rows if x["Estado"] == "✅ ÓPTIMA"] +
                            [x for x in log_rows if x["Estado"] == ""]
                        )
                        df_log = pd.DataFrame(log_rows)
                        def _hl(row):
                            if row["Estado"] == "⭐ SELECCIONADA":
                                return ["background-color:#7b5c00;color:white;font-weight:bold"] * len(row)
                            if row["Estado"] == "✅ ÓPTIMA":
                                return ["background-color:#1a3a2a;color:#a8e6cf"] * len(row)
                            return [""] * len(row)
                        st.dataframe(df_log.style.apply(_hl, axis=1),
                                     use_container_width=True, hide_index=True)
        else:
            st.error("No se encontró combinación válida.")

        # ── Diagrama físico — planta por piso ─────────────────
        st.subheader("📐 Diagrama de posicionamiento — planta por piso")
        st.caption("Vista superior de cómo encaja la cabina en el shaft en cada piso "
                   "(matriz de la solución seleccionada). Verde = dentro de límite, "
                   "naranja = al límite, rojo = fuera.")
        if best and best.get("matrix"):
            n_floors = len(best["matrix"])
            _prob = floors_with_issues(best, lim_map)

            with st.expander("🧊 Vista isométrica del hueco", expanded=False):
                components.html(
                    shaft_iso_svg(all_params, limits, best, n_floors, lim_map,
                                  proyecto=str(st.session_state.get("proyecto", ""))),
                    height=730, scrolling=False,
                )

            _modo = st.radio(
                "Pisos a mostrar",
                ["Con incidencias", "Todos", "Elegir"],
                horizontal=True, key="diag_modo", label_visibility="collapsed",
            )
            if _modo == "Con incidencias":
                _floors = _prob or list(range(n_floors))
                st.caption(f"Mostrando {len(_floors)} de {n_floors} pisos"
                           + ("" if _prob else " (ninguno tiene incidencias: se muestran todos)"))
            elif _modo == "Todos":
                _floors = list(range(n_floors))
            else:
                _floors = st.multiselect(
                    "Pisos", list(range(n_floors)),
                    default=_prob[:1] or [0], key="diag_pisos",
                    format_func=lambda i: f"Piso {i + 1}",
                )
            if _floors:
                components.html(
                    render_floor_plans_html(all_params, limits, best, lim_map,
                                            ctrl_in_frame_, ctrl_side_, floors=_floors),
                    height=min(500 * len(_floors) + 20, 8000),
                    scrolling=True,
                )
                # Exportar los diagramas sueltos (para mandar a obra sin el informe)
                if st.button("📄 Preparar PDF de estos diagramas", key="btn_diag_pdf"):
                    with st.spinner("Generando PDF de diagramas..."):
                        st.session_state["_diag_pdf"] = floor_plans_pdf(
                            all_params, limits, best, lim_map, ctrl_in_frame_, ctrl_side_,
                            floors=_floors,
                            titulo=f"Diagramas de posicionamiento — "
                                   f"{all_params.get('PROYECTO') or 'Survey'}")
                if st.session_state.get("_diag_pdf"):
                    st.download_button("⬇️ Descargar diagramas (PDF)",
                                       data=st.session_state["_diag_pdf"],
                                       file_name="diagramas_posicionamiento.pdf",
                                       mime="application/pdf", key="dl_diag_pdf")

        # ── BSR vs BS ─────────────────────────────────────────
        st.subheader("📏 Análisis BSR vs BS")
        if not bs_result.get("needed"):
            st.success("BSR ≥ BS — No se requiere ajuste de shaft.")
        elif bs_result.get("step") is None:
            st.error(f"No se encontró paso. DIF BS = {bs_result.get('dif_original')} mm")
        else:
            st.success(
                f"✅ Paso: **{bs_result['step']} mm**  |  "
                f"Rango: **{bs_result['range']}**  |  Zona: **{bs_result['range_name']}**"
            )

        # ── Plomado definitivo (con el desplazamiento del survey) ──
        st.subheader("🔩 Plomado definitivo (según el survey)")
        st.caption("Esquema de plomado con los desplazamientos que determinó el survey. "
                   "El conjunto (plomos + paredes teóricas + template) se mueve; las paredes "
                   "reales quedan fijas (eje cero = pared real izquierda).")
        if plumb_res and best:
            st.info(
                f"Desplazamiento aplicado:  lateral (rl) = **{best['rl']:.1f} mm**  ·  "
                f"frontal (fb) = **{best['fb_applied']:.1f} mm**."
            )
            pm1, pm2, pm3 = st.columns(3)
            pm1.metric("DBP",  f"{plumb_res['dbp']:.1f} mm")
            pm2.metric("DBPW", f"{plumb_res['dbpw']:.1f} mm")
            pm3.metric("RW",   f"{plumb_res['rw']:.1f} mm")
            st.dataframe(pd.DataFrame(plumb_table(plumb_res)),
                         use_container_width=True, hide_index=True)
            _pr_ = str(st.session_state.get("proyecto", ""))
            _bs = plumb_res.get("bs_check") or {}
            if _bs and not _bs.get("ok", True):
                st.error(
                    f"⚠️ **BS incoherente:** el plano dice **{_bs['bs_plano']:.0f}** pero "
                    f"SF1+BKS+2·RAIL+SF2 = **{_bs['bs_componentes']:.0f}** "
                    f"(dif {_bs['dif']:+.0f} mm). El encaje usa (BSR−BS)/2, así que con este "
                    f"desajuste los plomos quedan mal ubicados. Revisa BS, SF1, SF2, BKS o RAIL."
                )
            components.html(
                '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
                + plumb_svg(plumb_res, proyecto=_pr_) + '</body></html>',
                height=500, scrolling=False,
            )
            _v3d, _vfi = st.columns(2)
            with _v3d.expander("🧊 Vistas 3D del replanteo", expanded=False):
                components.html(
                    '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
                    + plumb_iso_svg(plumb_res, proyecto=_pr_) + '</body></html>',
                    height=650, scrolling=False,
                )
                components.html(
                    '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
                    + plumb_detail_svg(plumb_res, proyecto=_pr_) + '</body></html>',
                    height=500, scrolling=False,
                )
            with _vfi.expander("📋 Ficha de replanteo (para obra)", expanded=False):
                st.caption("Los números a medir con cinta. Imprímela o ábrela en el móvil.")
                components.html(
                    '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
                    + plumb_card_svg(plumb_res, proyecto=_pr_) + '</body></html>',
                    height=430, scrolling=False,
                )
            st.markdown("**📏 Verificación en campo — distancias plomo ↔ pared real**")
            st.dataframe(pd.DataFrame(plumb_checks(plumb_res)),
                         use_container_width=True, hide_index=True)
            if float(all_params.get("LengthTemplate", 0.0)) <= 0:
                st.info("💡 Ingresa **LengthTemplate** en los parámetros para ver el "
                        "template completo (punto P, cortes C1/C2 y diagonales).")
        else:
            st.caption("Se mostrará cuando el survey encuentre una solución válida.")

        # ── Paquete de obra: todo lo que necesita quien va a terreno ──
        # Las piezas ya existian sueltas tras v119-v123; aqui van en UN PDF.
        # Vive DENTRO de _render_survey_results porque usa sus locales
        # (best, lim_map, ctrl_in_frame_) y solo tiene sentido con calculo hecho.
        with st.expander("🧰 Paquete de obra (PDF para terreno)", expanded=False):
            st.caption("Isométrica del hueco + plantas a escala + replanteo de plomadas "
                       "con la ficha de medidas. Sin interpretaciones ni log: solo lo "
                       "que se usa para montar.")
            _pk1, _pk2 = st.columns([2, 1])
            _solo = _pk1.checkbox("Solo los pisos con incidencias", value=False,
                                  key="pack_solo_inc")
            if _pk2.button("Preparar paquete", use_container_width=True, key="btn_pack"):
                with st.spinner("Generando paquete de obra..."):
                    st.session_state["_pack_pdf"] = field_pack_pdf(
                        all_params, limits, best, lim_map,
                        plumb=r.get("plumb"),
                        ctrl_in_frame=ctrl_in_frame_, ctrl_side=ctrl_side_,
                        meta={"proyecto": st.session_state.get("proyecto", ""),
                              "cliente": st.session_state.get("cliente", ""),
                              "ubicacion": st.session_state.get("ubicacion", "")},
                        solo_incidencias=_solo)
            _pk = st.session_state.get("_pack_pdf")
            if _pk:
                st.download_button("⬇️ Descargar paquete de obra (PDF)", data=_pk,
                                   file_name="paquete_obra.pdf", mime="application/pdf",
                                   use_container_width=True, key="dl_pack")
            elif "_pack_pdf" in st.session_state:
                st.warning("No se pudo generar el paquete de obra.")

        # ── Estado de las interpretaciones IA ─────────────────
        if not interpretation.get("_ok"):
            st.error(
                f"⚠️ **No se pudo generar la interpretación técnica:** {interpretation.get('_error')}\n\n"
                "Los informes **requieren** la interpretación IA. Verifica que "
                "`ANTHROPIC_API_KEY` esté configurada en los **Secrets de Streamlit Cloud**."
            )

    def _do_calculo():

        # Snapshot del survey ANTES de hacer cualquier ajuste
        _c = _cfg_from_state()
        survey_original_input = st.session_state.survey_df.copy()

        # Build de parámetros
        all_params = {p: st.session_state.get(f"inp_{p}", 0.0) for p in list(PDF_PARAMS) + list(USER_ONLY.keys())}
        all_params["OMEGA_SIDE"]    = _c["omega_side"]
        all_params["WALL_LIMITING"] = _c["wall_limiting"]
        all_params["WALL_STOP"]     = _c["wall_stop"]
        all_params["WALL_SIDE"]     = _c["wall_side"]
        all_params["OFFSET_SIDE"]   = _c["offset_side"]
        all_params["CTRL_IN_FRAME"] = _c["ctrl_in_frame"]
        all_params["CTRL_SIDE"]     = _c["ctrl_side"]
        all_params["NS"]            = _c["ns"]
        all_params["PROYECTO"]      = st.session_state.get("proyecto", "")
        all_params["INGENIERO"]     = st.session_state.get("ingeniero", "")
        all_params["CLIENTE"]       = st.session_state.get("cliente", "")
        all_params["UBICACION"]     = st.session_state.get("ubicacion", "")

        # Totales = última fila de la matriz
        last = survey_original_input.iloc[-1]
        for col in SURVEY_COLS:
            all_params[f"{col[0]}{col[1]}T"] = float(last[col])

        # ── Validación de inputs ─────────────────────────────
        issues = validate_inputs(all_params)
        if issues:
            st.error("⚠️ Problemas en los parámetros — revisar antes de calcular:")
            for issue in issues:
                st.error(f"  • {issue}")
            st.stop()

        try:
            limits = calculate_limits(all_params)
        except Exception as e:
            st.error(f"Error en cálculo: {e}")
            st.stop()

        all_params.update(limits)

        # Matriz ajustada + análisis
        survey_adj    = apply_offsets(survey_original_input.to_dict("records"), limits)
        survey_adj_df = pd.DataFrame(survey_adj)
        analysis      = analyze_matrix(survey_adj, limits, wall_limiting=_c["wall_limiting"])
        all_params.update(analysis)
        limits.update(analysis)
        lim_map = {c: limits[f"LIMIT_{c}"] for c in SURVEY_COLS}

        # ── Optimización ──────────────────────────────────────
        with st.spinner("🔍 Buscando combinación óptima..."):
            opt_result = optimize(survey_adj, limits, all_params)
        best_sol = opt_result.get("best")
        if not best_sol:
            opt_result = {"best": None, "all_solutions": [],
                          "step_log": opt_result.get("step_log", [])}

        # ── BSR vs BS ─────────────────────────────────────────
        bs_result = find_bs_step(
            all_params["BSR"], all_params["BS"],
            limits["LIMIT_ZB"], limits["LIMIT_OB"]
        )

        # ── Plomado definitivo (con el desplazamiento del survey) ──
        plumb_res = None
        if best_sol is not None:
            try:
                _plumb_inp = {
                    "BKS":  all_params["BKS"],  "RAIL": all_params["RAIL"],
                    "TKSW": all_params["TKSW"], "LengthTemplate": all_params.get("LengthTemplate", 0.0),
                    "SF1":  all_params["SF1"],  "SF2":  all_params["SF2"],
                    "BSR":  all_params["BSR"],  "BS":   all_params["BS"],
                }
                _sdisp    = {"rl": best_sol["rl"], "fb": best_sol["fb_applied"]}
                plumb_res = compute_plumb(_plumb_inp, survey_disp=_sdisp)
            except Exception as e:
                plumb_res = None
                st.warning(f"No se pudo generar el plomado definitivo: {e}")

        # ── Interpretaciones IA (admin + usuario) ─────────────
        _calc_for_ia = {
            "limits":           limits,
            "analysis":         analysis,
            "optimizer_result": opt_result,
            "bs_result":        bs_result,
        }
        with st.spinner("🤖 Generando interpretación técnica con IA..."):
            interpretation = generate_interpretation(_calc_for_ia, all_params)
        with st.spinner("🤖 Generando interpretación del informe de cliente..."):
            interpretation_user = generate_user_interpretation(_calc_for_ia, all_params)

        # ── Persistir para el render y los reportes ───────────
        st.session_state.calc_results = {
            "all_params":          all_params,
            "limits":              limits,
            "survey_orig":         survey_original_input,
            "survey_adj":          survey_adj_df,
            "lim_map":             lim_map,
            "analysis":            analysis,
            "optimizer_result":    opt_result,
            "bs_result":           bs_result,
            "interpretation":      interpretation,
            "interpretation_user": interpretation_user,
            "plumb":               plumb_res,
        }
        st.session_state["_calc_sig"] = _survey_signature()
        st.session_state.pop("_rebuilt_from", None)
        # El nº de soluciones y los diagramas cambian: descartar lo derivado del cálculo previo
        st.session_state.pop("sol_activa", None)
        st.session_state.pop("_diag_pdf", None)
        st.session_state.pop("diag_pisos", None)

        # ── Cronograma automático según el proyecto ───────────
        _flags = detect_flags(st.session_state.calc_results)
        _auto  = build_schedule(_c["ns"], date.today(), _flags)
        st.session_state.calc_results["schedule"] = _auto
        st.session_state["sched_rows"] = [
            {"Actividad": a["nombre"], "Duración (d)": int(a["duracion"]), "Peso (%)": a["peso"]}
            for a in _auto["activities"]
        ]
        st.session_state["sched_start"] = date.today()

        # ── Informe ADMIN (completo) → correo interno ─────────
        admin_pdf = None
        if interpretation.get("_ok"):
            try:
                with st.spinner("📄 Preparando informe interno de administración..."):
                    admin_pdf = generate_report(
                        project_params   = all_params,
                        calculated       = limits,
                        survey_original  = survey_original_input,
                        survey_adjusted  = survey_adj_df,
                        lim_map          = lim_map,
                        analysis         = analysis,
                        optimizer_result = opt_result,
                        bs_result        = bs_result,
                        survey_cols      = SURVEY_COLS,
                        interpretation   = interpretation,
                        schedule         = _auto,
                        plumb            = plumb_res,
                    )
            except Exception as e:
                st.warning(f"No se pudo generar el informe admin para el correo: {e}")

        # ── Notificación por correo (con informe admin adjunto) ─
        send_usage_notification(
            proyecto        = st.session_state.get("proyecto", ""),
            ingeniero       = st.session_state.get("ingeniero", ""),
            all_params      = all_params,
            analysis        = analysis,
            opt_result      = opt_result,
            bs_result       = bs_result,
            survey_df       = survey_original_input,
            pdf_bytes       = st.session_state.get("pdf_bytes"),
            pdf_name        = st.session_state.get("last_pdf_name"),
            admin_report    = admin_pdf,
        )
        if admin_pdf:
            st.info("📧 Informe interno de administración enviado por correo.")
        if interpretation.get("_ok"):
            st.success("🤖 Interpretaciones generadas correctamente.")
        st.success("✅ Cálculo e interpretación completados.")

    if _fase == _FASE_DATOS:
        # PASO 1 — CARGAR PDF
        # ══════════════════════════════════════════════════════
        st.header("📄 Plano del elevador")
        col_brand, col_pdf = st.columns([1, 3])
        col_brand.selectbox("Marca", ["Schindler"], key="brand")   # placeholder p/ futura expansión
        pdf_file = col_pdf.file_uploader("PDF de planos", type=["pdf"])

        if pdf_file is not None and pdf_file.name != st.session_state.get("last_pdf_name"):
            with st.spinner("⏳ Extrayendo datos del PDF..."):
                extracted = extract_from_pdf(pdf_file)
            st.session_state.pdf_extracted = extracted
            st.session_state.last_pdf_name = pdf_file.name
            st.session_state.pdf_bytes     = pdf_file.getvalue()   # guardar para adjuntar en correo
            # Plano de la sesion: lo heredan Plomadas, Cortes y Belting,
            # que hasta v127 pedian cada una su propio PDF.
            plan_store.guardar(pdf_file.name, st.session_state.pdf_bytes)
            for p in PDF_PARAMS:
                if extracted.get(p) is not None:
                    st.session_state[f"inp_{p}"] = float(extracted[p])
            # ── Riel de cabina: leer referencia del plano → autocompletar RAIL del catálogo ──
            st.session_state["rail_ref_msg"] = ""
            try:
                from extractors.schindler import extract_car_guide_rail
                from core import rails
                _code = extract_car_guide_rail(pdf_file)
                if _code:
                    _info = rails.get_rail(_code) if rails.is_configured() else None
                    if _info and _info.get("altura"):
                        st.session_state["inp_RAIL"] = float(_info["altura"])
                        st.session_state["rail_ref_msg"] = (
                            f"✅ Riel de cabina **{_code}** → RAIL = **{_info['altura']} mm** "
                            "(altura del diente desde la espalda, del catálogo).")
                    else:
                        st.session_state["rail_ref_msg"] = (
                            f"⚠️ Riel **{_code}** detectado pero **no está en el catálogo de Rieles**. "
                            "Ingresa RAIL a mano o agrégalo al catálogo.")
                else:
                    st.session_state["rail_ref_msg"] = (
                        "ℹ️ No se detectó el código del riel de cabina; ingresa RAIL a mano.")
            except Exception:
                pass
            # ── Número de paradas: NUMBER OF STOPS del plano → NS ──
            st.session_state["ns_msg"] = ""
            try:
                from extractors.schindler import extract_number_of_stops
                _ns = extract_number_of_stops(pdf_file)
                if _ns and 2 <= _ns <= 50:
                    st.session_state["ns"] = int(_ns)
                    st.session_state["ns_msg"] = f"✅ NUMBER OF STOPS del plano → NS = **{_ns}**."
                else:
                    st.session_state["ns_msg"] = ("ℹ️ No se detectó NUMBER OF STOPS en el plano; "
                                                  "ingresa NS a mano.")
            except Exception:
                pass
            found   = sum(1 for v in extracted.values() if v is not None)
            missing = [k for k,v in extracted.items() if v is None]
            st.success(f"✅ {found}/{len(extracted)} parámetros encontrados.")
            if missing:
                st.warning(f"⚠️ Ingresar manualmente: **{', '.join(missing)}**")
            st.rerun()
        elif pdf_file and pdf_file.name == st.session_state.get("last_pdf_name"):
            st.info(f"📄 Datos de: **{pdf_file.name}** — ver sidebar.")

        if st.session_state.get("rail_ref_msg"):
            _m = st.session_state["rail_ref_msg"]
            (st.success if _m.startswith("✅") else
             st.warning if _m.startswith("⚠️") else st.info)(_m)

        # ══════════════════════════════════════════════════════
        # PASO 2 — PARÁMETROS
        # ══════════════════════════════════════════════════════
        st.header("⚙️ Parámetros")

        # Marca por campo: ✅ leído del plano · ✏️ a completar a mano.
        # (Recupera la señal que se perdió al quitar el panel del sidebar en v93.)
        _ext = st.session_state.get("pdf_extracted") or {}

        def _mark(p):
            if not _ext or p not in _ext:
                return ""
            return "✅ " if _ext.get(p) is not None else "✏️ "

        if _ext:
            _found = [p for p, v in _ext.items() if v is not None]
            _miss  = [p for p, v in _ext.items() if v is None]
            _r1, _r2 = st.columns([1, 2])
            _r1.metric("Leídos del plano", f"{len(_found)}/{len(_ext)}")
            if _miss:
                _r2.warning("✏️ Completa a mano: **" + "**, **".join(_miss) + "**")
            else:
                _r2.success("✅ El plano aportó todos los parámetros.")

        with st.expander("📄 Parámetros del plano (editables)", expanded=True):
            _pendientes = list(PDF_PARAMS)
            for _titulo, _lista in _GRUPOS_PARAM:
                _ps = [p for p in _lista if p in _pendientes]
                if not _ps:
                    continue
                st.markdown(f"**{_titulo}**")
                _cols = st.columns(4)
                for j, p in enumerate(_ps):
                    _cols[j % 4].number_input(
                        label = f"{_mark(p)}{p} (mm)",
                        step  = 0.5,
                        help  = PARAM_DESCRIPTIONS.get(p, ""),
                        key   = f"inp_{p}",
                    )
                    _pendientes.remove(p)
            if _pendientes:      # cualquier parámetro nuevo que no esté agrupado
                st.markdown("**Otros**")
                _cols = st.columns(4)
                for j, p in enumerate(_pendientes):
                    _cols[j % 4].number_input(
                        label = f"{_mark(p)}{p} (mm)", step = 0.5,
                        help  = PARAM_DESCRIPTIONS.get(p, ""), key = f"inp_{p}",
                    )

        with st.expander("✏️ Parámetros medidos en obra", expanded=True):
            cols = st.columns(len(USER_ONLY))
            for j, (p, desc) in enumerate(USER_ONLY.items()):
                cols[j].number_input(
                    label = f"{p} (mm)",
                    step  = 0.5,
                    help  = desc,
                    key   = f"inp_{p}",
                )

        st.markdown("**⚙️ Configuración**")
        c1, c2, c3 = st.columns(3)
        c1.radio("Lado del Omega",        ["R", "L"], horizontal=True, key="cfg_omega_side")
        c2.radio("¿Hay pared limitante?", ["N", "Y"], horizontal=True, key="cfg_wall_yn")
        c3.radio("Lado offset cabina",    ["R", "L"], horizontal=True, key="cfg_offset_side")

        wall_limiting = (st.session_state.cfg_wall_yn == "Y")
        if wall_limiting:
            wc1, wc2 = st.columns(2)
            wc1.number_input("Parada limitante", min_value=1, step=1, key="cfg_wall_stop")
            wc2.radio("Lado de la pared",        ["R", "L"], horizontal=True, key="cfg_wall_side")

        cc1, cc2 = st.columns(2)
        cc1.radio("¿Controlador hace parte del frame?", ["N", "Y"], horizontal=True, key="cfg_ctrl_yn")
        ctrl_in_frame = (st.session_state.cfg_ctrl_yn == "Y")
        if ctrl_in_frame:
            cc2.radio("Lado del controlador", ["R", "L"], horizontal=True, key="cfg_ctrl_side")

        # Lectura final de configuración para resto del flujo
        omega_side  = st.session_state.cfg_omega_side
        offset_side = st.session_state.cfg_offset_side
        wall_stop   = st.session_state.cfg_wall_stop if wall_limiting else None
        wall_side   = st.session_state.cfg_wall_side if wall_limiting else None
        ctrl_side   = st.session_state.cfg_ctrl_side if ctrl_in_frame else None

        # ══════════════════════════════════════════════════════
        # PASO 3 — MATRIZ SURVEY
        # ══════════════════════════════════════════════════════
        st.header("📊 Matriz del survey")

        sc1, sc2, sc3 = st.columns([1, 2, 2])

        sc1.number_input("Número de paradas (NS)", min_value=2, max_value=50, step=1, key="ns")
        if st.session_state.get("ns_msg"):
            sc1.caption(st.session_state["ns_msg"])

        # Ajustar tamaño si NS cambió
        current_ns = len(st.session_state.survey_df)
        if int(st.session_state.ns) != current_ns:
            old_df    = st.session_state.survey_df.copy()
            new_ns    = int(st.session_state.ns)
            new_df    = pd.DataFrame({c: [0.0]*new_ns for c in SURVEY_COLS})
            rows_keep = min(len(old_df), new_ns)
            new_df.iloc[:rows_keep] = old_df.iloc[:rows_keep].values
            st.session_state.survey_df = new_df
            st.rerun()

        # Cargar Excel
        uploaded_excel = sc2.file_uploader("📂 Cargar matriz (.xlsx)", type=["xlsx"], key="excel_uploader")
        # Por defecto solo se importa la MATRIZ: si ya cargaste el plano, los parámetros del
        # PDF mandan y no deben ser pisados por los que venían guardados en el Excel.
        _imp_todo = sc2.checkbox("Restaurar también parámetros y configuración del Excel",
                                 value=False, key="excel_imp_todo",
                                 help="Desmarcado: solo se importa la matriz de medidas.")
        if st.session_state.get("last_excel_id") and sc2.button("🔄 Volver a importar el Excel",
                                                                key="btn_reimport_xls"):
            st.session_state.pop("last_excel_id", None)
            st.rerun()
        # ⚠️ GUARDA obligatoria: el file_uploader conserva el archivo entre reruns, así que
        # sin esta condición el import se repetiría en CADA rerun y pisaría los valores del
        # PDF o los que escriba el usuario. Mismo patrón que la carga de PDF.
        _xls_id = f"{uploaded_excel.name}:{uploaded_excel.size}" if uploaded_excel is not None else None
        if uploaded_excel is not None and _xls_id != st.session_state.get("last_excel_id"):
            try:
                imported = import_survey_excel(uploaded_excel)
                # Nada se modifica hasta tener TODO parseado; se aplica en el próximo rerun.
                _params = {k: float(v) for k, v in (imported.get("info") or {}).items()
                           if k in PDF_PARAMS or k in USER_ONLY}
                cfg = imported.get("config", {})
                _cfg = {}
                if cfg.get("OMEGA_SIDE")  in ("R", "L"): _cfg["cfg_omega_side"]  = cfg["OMEGA_SIDE"]
                if cfg.get("OFFSET_SIDE") in ("R", "L"): _cfg["cfg_offset_side"] = cfg["OFFSET_SIDE"]
                if "WALL_LIMITING" in cfg:
                    _cfg["cfg_wall_yn"] = "Y" if cfg["WALL_LIMITING"] else "N"
                if cfg.get("WALL_STOP") is not None:     _cfg["cfg_wall_stop"] = int(cfg["WALL_STOP"])
                if cfg.get("WALL_SIDE") in ("R", "L"):   _cfg["cfg_wall_side"] = cfg["WALL_SIDE"]
                if "CTRL_IN_FRAME" in cfg:
                    _cfg["cfg_ctrl_yn"] = "Y" if cfg["CTRL_IN_FRAME"] else "N"
                if cfg.get("CTRL_SIDE") in ("R", "L"):   _cfg["cfg_ctrl_side"] = cfg["CTRL_SIDE"]

                st.session_state["_import_pending"] = {
                    "ns": len(imported["df"]),
                    "params": _params if _imp_todo else {},
                    "cfg":    _cfg    if _imp_todo else {},
                    "df": imported["df"].copy(),
                    "todo": bool(_imp_todo),
                }
                st.session_state["last_excel_id"] = _xls_id
                st.rerun()
            except Exception as e:
                st.session_state["last_excel_id"] = _xls_id   # no reintentar en bucle
                sc2.error(f"Error al importar Excel: {e}")

        st.caption("Ingresa o edita las medidas en campo (mm).")
        edited_df = st.data_editor(
            st.session_state.survey_df,
            use_container_width=True,
            num_rows="fixed",
            key="survey_editor"
        )
        st.session_state.survey_df = edited_df.copy()

        # Exportar Excel
        info_dict   = {p: st.session_state.get(f"inp_{p}", 0.0) for p in list(PDF_PARAMS) + list(USER_ONLY.keys())}
        config_dict = {
            "OMEGA_SIDE":    omega_side,
            "WALL_LIMITING": wall_limiting,
            "WALL_STOP":     wall_stop,
            "WALL_SIDE":     wall_side,
            "OFFSET_SIDE":   offset_side,
            "CTRL_IN_FRAME": ctrl_in_frame,
            "CTRL_SIDE":     ctrl_side,
            "NS":            int(st.session_state.ns),
        }
        excel_bytes = export_survey_excel(edited_df, info_dict, config_dict)
        sc3.download_button(
            label     = "💾 Guardar matriz (.xlsx)",
            data      = excel_bytes,
            file_name = "survey_matrix.xlsx",
            mime      = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        # ══════════════════════════════════════════════════════

        st.markdown("---")

        # ── ¿Listo para calcular? Estado de cada entrada ──
        _ex   = st.session_state.get("pdf_extracted") or {}
        _falt = [p for p, v in _ex.items() if v is None] if _ex else []
        _nsv  = int(st.session_state.get("ns", 2))
        _chips = [
            ("✅ Plano cargado" if _ex else "⚪ Sin plano (parámetros a mano)"),
            ("✅ Parámetros completos" if (_ex and not _falt)
             else (f"⚠️ {len(_falt)} parámetro(s) sin leer" if _falt else "✏️ Parámetros manuales")),
            f"✅ Matriz: {_nsv} niveles",
        ]
        st.markdown("  ".join(f"`{c}`" for c in _chips))

        # Validación temprana: avisar ANTES de pulsar Calcular
        try:
            _c0  = _cfg_from_state()
            _ap0 = {p: st.session_state.get(f"inp_{p}", 0.0)
                    for p in list(PDF_PARAMS) + list(USER_ONLY.keys())}
            _ap0.update({"OMEGA_SIDE": _c0["omega_side"], "WALL_LIMITING": _c0["wall_limiting"],
                         "WALL_STOP": _c0["wall_stop"], "WALL_SIDE": _c0["wall_side"],
                         "OFFSET_SIDE": _c0["offset_side"], "CTRL_IN_FRAME": _c0["ctrl_in_frame"],
                         "CTRL_SIDE": _c0["ctrl_side"], "NS": _c0["ns"]})
            _last0 = st.session_state.survey_df.iloc[-1]
            for _col in SURVEY_COLS:
                _ap0[f"{_col[0]}{_col[1]}T"] = float(_last0[_col])
            _iss0 = validate_inputs(_ap0)
        except Exception:
            _iss0 = []
        if _iss0:
            with st.expander(f"⚠️ {len(_iss0)} aviso(s) en los parámetros", expanded=False):
                for _x in _iss0:
                    st.warning(_x)

        if st.button("🚀 Calcular y ver resultados", type="primary",
                     use_container_width=True, key="btn_calc_datos"):
            _do_calculo()
            st.session_state["_fase_pending"] = _FASE_RES
            st.rerun()

        with st.expander("📑 Duplicar para el siguiente elevador"):
            st.caption("Conserva parámetros y configuración de este survey y limpia la matriz "
                       "y los resultados. Útil cuando hay varios elevadores en el mismo hueco.")
            if st.button("📑 Duplicar survey", key="btn_dup_survey"):
                st.session_state["_dup_survey"] = True
                st.rerun()


    else:

        st.header("✅ Resultados")
        if not st.session_state.calc_results:
            st.info("Aún no hay cálculo. Ve a **📝 Datos del survey**, completa la "
                    "información y pulsa **🚀 Calcular y ver resultados**.")
        else:
            if st.session_state.get("_calc_sig") and st.session_state["_calc_sig"] != _survey_signature():
                st.warning("⚠️ Cambiaste datos desde el último cálculo. Lo de abajo corresponde "
                           "al cálculo anterior — recalcula para actualizarlo.")
            if st.button("🔄 Recalcular con los datos actuales", use_container_width=True,
                         key="btn_recalc"):
                _do_calculo()
                st.rerun()
            _render_survey_results(st.session_state.calc_results)

        # PASO 5 — GESTIÓN DE PROYECTO (cronograma + curva S)
        # ══════════════════════════════════════════════════════
        st.header("📅 Cronograma")
        if st.session_state.calc_results:
            st.caption("Cronograma y curva S generados automáticamente según el proyecto "
                       "(escalados por NS y por los hallazgos del análisis). Ajusta duraciones "
                       "y pesos si lo necesitas — la curva S se recalcula sola.")

            if "sched_start" not in st.session_state:
                st.session_state["sched_start"] = date.today()

            gc1, gc2 = st.columns([1, 2])
            start = gc1.date_input("Fecha de inicio del proyecto", key="sched_start")

            # Editor de actividades (nombre bloqueado; duración y peso editables)
            sched_rows = st.session_state.get("sched_rows", [])
            if sched_rows:
                edited = st.data_editor(
                    pd.DataFrame(sched_rows),
                    use_container_width=True, hide_index=True, num_rows="fixed",
                    disabled=["Actividad"], key="sched_editor",
                )
                st.session_state["sched_rows"] = edited.to_dict("records")

                custom = [{"nombre": r["Actividad"],
                           "duracion": r.get("Duración (d)", 1),
                           "peso":     r.get("Peso (%)", 1)}
                          for r in st.session_state["sched_rows"]]
                sched = build_schedule(int(st.session_state.ns), start, {}, custom_rows=custom)
                st.session_state.calc_results["schedule"] = sched

                m1, m2, m3 = st.columns(3)
                m1.metric("Duración total", f"{sched['total_dias']} días")
                m2.metric("Inicio",       sched["start_date"].strftime("%d/%m/%Y"))
                m3.metric("Fin estimado", sched["fecha_fin"].strftime("%d/%m/%Y"))

                components.html(
                    '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
                    + schedule_svg(sched) + '</body></html>',
                    height=140 + len(sched["activities"]) * 22 + 200,
                    scrolling=False,
                )
        else:
            st.info("Realiza el cálculo primero para generar el cronograma.")

        # ══════════════════════════════════════════════════════
        # PASO 6 — INFORME DEL CLIENTE  (solo propietario / administrador)
        # ══════════════════════════════════════════════════════
        if not can_reports(_ROL):
            st.header("📄 Informe del cliente")
            st.caption("🔒 La descarga de informes está disponible para administración "
                       "(propietario / administrador).")
        else:
            st.header("📄 Informe del cliente")
            st.caption("Informe profesional para entregar al cliente (solución final, diagramas e "
                       "instrucciones de implementación). El informe técnico interno se envía "
                       "automáticamente por correo a administración.")

            if st.session_state.calc_results:
                r          = st.session_state.calc_results
                interp     = r.get("interpretation") or {}
                interp_usr = r.get("interpretation_user") or {}
                if not interp_usr.get("_ok"):
                    st.error(
                        "🚫 **No se puede generar el informe sin la interpretación IA.**\n\n"
                        f"Motivo: {interp_usr.get('_error', interp.get('_error', 'no disponible'))}.\n\n"
                        "Configura `ANTHROPIC_API_KEY` en los Secrets de Streamlit Cloud y vuelve a calcular."
                    )
                elif st.button("📄 Generar informe del cliente", use_container_width=True):
                    with st.spinner("Generando informe del cliente..."):
                        user_pdf = generate_user_report(
                            project_params      = r["all_params"],
                            calculated          = r["limits"],
                            optimizer_result    = r["optimizer_result"],
                            lim_map             = r["lim_map"],
                            survey_cols         = SURVEY_COLS,
                            interpretation_user = r.get("interpretation_user"),
                            schedule            = r.get("schedule"),
                            plumb               = r.get("plumb"),
                        )
                    proj = (r["all_params"].get("PROYECTO") or "cliente").replace(" ", "_")
                    st.download_button(
                        label     = "⬇️ Descargar informe del cliente",
                        data      = user_pdf,
                        file_name = f"informe_{proj}.pdf",
                        mime      = "application/pdf",
                        use_container_width=True
                    )
            else:
                st.info("Realiza el cálculo primero para poder generar el informe.")

        # ══════════════════════════════════════════════════════
        # PASO 7 — GUARDAR COMO PROYECTO  (solo administrador / propietario)
        # ══════════════════════════════════════════════════════
        if _ROL in ("administrador", "propietario"):
            st.header("💾 Guardar como proyecto")
            if not st.session_state.get("calc_results"):
                st.info("Calcula primero: el proyecto se inicia con este survey.")
            elif not projects_data.is_configured():
                st.caption("🔒 Requiere Google Sheets configurado para guardar proyectos.")
            elif not _GRUPO:
                st.caption("🔒 Tu cuenta no tiene grupo asignado; no se pueden crear proyectos.")
            else:
                r  = st.session_state.calc_results
                ap = r["all_params"]
                _campos = []
                try:
                    from core.auth import list_users
                    _campos = [u["Usuario"] for u in list_users(_GRUPO)
                               if str(u.get("Rol", "")) == "campo"]
                except Exception:
                    pass
                # ── Asignacion de campo FUERA del form ──────────────
                # Va fuera a proposito: dentro de un st.form los widgets no
                # actualizan session_state hasta el submit, y el aviso de
                # credenciales/contacto solo sirve ANTES de guardar.
                pj_asg = st.multiselect("👷 Usuarios de campo asignados", _campos,
                                        key="pj_asg_sel")
                if pj_asg:
                    _sin_contacto, _cred_mal = [], []
                    for _u in pj_asg:
                        try:
                            _info = auth_get_user(_u) or {}
                            if not (str(_info.get("Email", "")).strip()
                                    and str(_info.get("TelegramChatID", "")).strip()):
                                _sin_contacto.append(_u)
                        except Exception:
                            pass
                        try:
                            for _c in credentials.list_for(_u):
                                _e = credentials.status(_c.get("Vencimiento"))
                                if _e in ("vencido", "por_vencer"):
                                    _cred_mal.append(
                                        f"{_u} — {_c.get('Tipo','credencial')}: "
                                        f"{credentials.status_label(_c.get('Vencimiento'))}"
                                        + (f" ({_c.get('Vencimiento')})"
                                           if _c.get("Vencimiento") else ""))
                        except Exception:
                            pass
                    if _cred_mal:
                        st.warning("🎫 **Credenciales a revisar antes de mandarlos a obra:**\n\n"
                                   + "\n".join(f"- {x}" for x in _cred_mal)
                                   + "\n\nPuedes guardar igualmente; el aviso es informativo.")
                    if _sin_contacto:
                        st.warning(
                            "📵 **Sin contacto completo (email + Telegram):** "
                            + ", ".join(_sin_contacto)
                            + ". No recibirán la asignación ni las inducciones, y sin "
                              "contacto no pueden usar la app. Complétalo en "
                              "🛠 Mi grupo → Usuarios.")

                with st.form("save_project"):
                    st.caption("Se guarda el survey completo (parámetros, matriz, interpretaciones "
                               "y cronograma). El avance lo alimentará el equipo de campo.")
                    pc1, pc2 = st.columns(2)
                    pj_nom = pc1.text_input("Nombre del proyecto", value=ap.get("PROYECTO", ""))
                    pj_cli = pc2.text_input("Cliente", value=st.session_state.get("cliente", ""))
                    pj_ubi = pc1.text_input("Ubicación", value=st.session_state.get("ubicacion", ""))
                    pj_mod = pc2.text_input("Modelo de elevador")
                    pj_ing = pc1.text_input("Ingeniero", value=ap.get("INGENIERO", ""))
                    pj_instr = st.text_area("📌 Instrucciones particulares del proyecto",
                                            placeholder="Indicaciones específicas para el equipo…")
                    pj_ind = st.text_area("📝 Inducciones (un link por línea)",
                                          placeholder="https://...\nhttps://...",
                                          help="Se enviarán por Telegram/email a los usuarios de campo "
                                               "asignados para que las diligencien.")
                    pj_pres = st.number_input("💰 Presupuesto del proyecto (0 = sin presupuesto)",
                                              min_value=0.0, step=100.0,
                                              help="Se compara contra compras + mano de obra.")
                    pj_dup_ok = st.checkbox(
                        "Crear aunque ya exista un proyecto con ese nombre",
                        value=False, key="pj_dup_ok",
                        help="Marca esto solo si de verdad es un elevador distinto.")
                    if st.form_submit_button("💾 Guardar como proyecto", use_container_width=True):
                        # Un proyecto = un elevador. Sin este control es facil crear
                        # el mismo dos veces (el survey se repite por elevador) y las
                        # horas/gastos quedan repartidos entre duplicados.
                        _dups = []
                        try:
                            _norm = lambda x: " ".join(str(x or "").lower().split())
                            for _p in projects_data.list_projects(_GRUPO):
                                if _norm(_p.get("Nombre")) == _norm(pj_nom):
                                    _dups.append(f"{_p.get('ID')} · {_p.get('Nombre')}"
                                                 + (f" ({_p.get('Cliente')})"
                                                    if _p.get("Cliente") else ""))
                        except Exception:
                            pass
                        if not pj_nom.strip():
                            st.error("El nombre del proyecto es obligatorio.")
                        elif _dups and not pj_dup_ok:
                            st.warning(
                                "⚠️ Ya existe un proyecto con ese nombre en tu grupo:\n\n"
                                + "\n".join(f"- {d}" for d in _dups)
                                + "\n\nSi es otro elevador, marca la casilla de arriba "
                                  "y vuelve a guardar. Si es el mismo, ábrelo en "
                                  "🛠 Mi grupo en vez de duplicarlo."
                            )
                        else:
                            sched = r.get("schedule") or {}
                            _sd = sched.get("start_date"); _ff = sched.get("fecha_fin")
                            matriz = (r["survey_orig"].to_dict("records")
                                      if hasattr(r.get("survey_orig"), "to_dict") else [])
                            ok, res = projects_data.create_project(
                                grupo=_GRUPO, nombre=pj_nom.strip(), cliente=pj_cli,
                                ubicacion=pj_ubi, modelo=pj_mod, ns=int(ap.get("NS", 0) or 0),
                                ingeniero=pj_ing, campo_asignados=pj_asg,
                                fecha_inicio=(_sd.strftime("%Y-%m-%d") if _sd else ""),
                                fecha_fin_est=(_ff.strftime("%Y-%m-%d") if _ff else ""),
                                params=ap, matriz=matriz,
                                interp={"admin": r.get("interpretation"),
                                        "user":  r.get("interpretation_user")},
                                activities=sched.get("activities", []),
                                creado_por=st.session_state.auth.get("usuario", ""),
                                instrucciones=pj_instr, induccion_links=pj_ind,
                                presupuesto=pj_pres,
                            )
                            if ok:
                                st.session_state["_prj_creado"] = {
                                    "id": res, "nombre": pj_nom.strip()}
                                st.success(f"✅ Proyecto **{res}** guardado.")
                                # ── Avisar a los usuarios de campo asignados ──
                                if pj_asg and not notify.any_channel_configured():
                                    st.caption("📨 Sin canales de aviso configurados "
                                               "(Gmail / Telegram): no se envió nada.")
                                if pj_asg and notify.any_channel_configured():
                                    _pinfo = {"Nombre": pj_nom.strip(), "Cliente": pj_cli,
                                              "Ubicacion": pj_ubi,
                                              "FechaInicio": (_sd.strftime("%Y-%m-%d") if _sd else ""),
                                              "FechaFinEst": (_ff.strftime("%Y-%m-%d") if _ff else ""),
                                              "InduccionLinks": pj_ind}
                                    _nn = 0
                                    for un in pj_asg:
                                        try:
                                            rr = notify.notify_assignment(un, _pinfo)
                                            if rr.get("email") or rr.get("telegram"):
                                                _nn += 1
                                        except Exception:
                                            pass
                                    if _nn == len(pj_asg):
                                        st.caption(f"📨 {_nn} usuario(s) de campo notificado(s).")
                                    elif _nn:
                                        st.warning(f"📨 Notificados {_nn} de {len(pj_asg)}. "
                                                   "Al resto le falta email o Telegram.")
                                    else:
                                        st.warning("📵 No se pudo notificar a ningún usuario "
                                                   "asignado: revisa su email y Telegram en "
                                                   "🛠 Mi grupo → Usuarios.")
                                # ── Auto-archivo en Drive: plano + matriz + informe cliente ──
                                if drive_store.is_configured():
                                    if not drive_store.is_available():
                                        st.caption("📎 Documentos no archivados: Google Drive no está "
                                                   "conectado (revisa las credenciales OAuth en Secrets).")
                                    else:
                                        _usr = st.session_state.auth.get("usuario", "")
                                        _fallos = []
                                        with st.spinner("Archivando documentos en Drive..."):
                                            try:
                                                pb = st.session_state.get("pdf_bytes")
                                                if pb:
                                                    fid = drive_store.upload(res, "plano.pdf", pb, "application/pdf")
                                                    projects_data.add_document(res, "plano.pdf", "plano", fid, _usr)
                                            except Exception:
                                                _fallos.append("plano")
                                            try:
                                                csv = r["survey_orig"].to_csv(index=False).encode("utf-8")
                                                fid = drive_store.upload(res, "matriz_survey.csv", csv, "text/csv")
                                                projects_data.add_document(res, "matriz_survey.csv",
                                                                           "matriz_survey", fid, _usr)
                                            except Exception:
                                                _fallos.append("matriz")
                                            try:
                                                if (r.get("interpretation_user") or {}).get("_ok"):
                                                    pdfb = generate_user_report(
                                                        project_params=r["all_params"], calculated=r["limits"],
                                                        optimizer_result=r["optimizer_result"], lim_map=r["lim_map"],
                                                        survey_cols=SURVEY_COLS,
                                                        interpretation_user=r.get("interpretation_user"),
                                                        schedule=r.get("schedule"), plumb=r.get("plumb"))
                                                    fid = drive_store.upload(res, "informe_cliente.pdf",
                                                                             pdfb, "application/pdf")
                                                    projects_data.add_document(res, "informe_cliente.pdf",
                                                                               "informe_cliente", fid, _usr)
                                            except Exception:
                                                _fallos.append("informe cliente")
                                        if _fallos:
                                            st.caption("📎 Documentos base archivados, salvo: "
                                                       + ", ".join(_fallos) + ".")
                                        else:
                                            st.caption("📎 Documentos base archivados en Drive.")
                            else:
                                st.error(f"No se pudo guardar: {res}")

                # ── Cerrar el ciclo: llevar al proyecto recien creado ──
                # Antes esto terminaba en un texto muerto ("Gestionalo en Mi grupo").
                _pc = st.session_state.get("_prj_creado")
                if _pc:
                    _c1, _c2 = st.columns([3, 1])
                    _c1.info(f"Proyecto **{_pc['id']} · {_pc['nombre']}** listo. "
                             "Puedes abrirlo para asignar campo, actividades y gastos.")
                    if _c2.button("Abrir proyecto ➜", use_container_width=True,
                                  key="ir_al_proyecto"):
                        st.session_state["_prjsel_pending"] = _pc["id"]
                        st.session_state["_nav_pending"] = (
                            "👑 Administración" if _ROL == "propietario" else "🛠 Mi grupo")
                        if _ROL == "propietario":
                            st.session_state["owner_sec"] = "📁 Proyectos"
                        st.session_state.pop("_prj_creado", None)
                        st.rerun()
