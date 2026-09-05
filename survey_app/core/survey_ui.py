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

import logging

from core.i18n import t
import streamlit as st

from core import flash
import streamlit.components.v1 as components
import pandas as pd
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
from core                 import toolruns
from core                 import plan_ui
from core                 import plan_store
from core.auth import can_reports
from core import clock
from core import tabla

logger = logging.getLogger(__name__)

# Opción neutra: sin ella el selectbox devuelve el primer proyecto y se
# escribiría sobre un elevador que nadie eligió.
_VACIO = "— choose the project —"

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

# ⚠️ SIN `t()`: es una constante de MODULO, evaluada al IMPORTAR — ahi todavia no
# hay idioma elegido y la etiqueta quedaria congelada. El texto va en BASE (ingles)
# y la traduccion se hace al PINTAR (ver `_GRUPOS_PARAM` mas abajo, `t(_titulo)`).
# Las CLAVES de agrupacion son las listas de parametros; el titulo es solo etiqueta.
_GRUPOS_PARAM = [
    (":material/crop_free: Shaft",            ["BS", "TS"]),
    (":material/elevator: Car",               ["BK", "TK", "BKS"]),
    (":material/door_front: Door / sill",     ["BT", "TKA", "TKS", "TSW"]),
    (":material/place: Front",                ["TKSW", "BKF1", "BKF2"]),
    (":material/swap_horiz: Sides",           ["SF1", "SF2"]),
    (":material/balance: Counterweight",      ["BGS", "SG", "TG"]),
]

USER_ONLY = {
    "BSR":            "Actual shaft width measured on site (mm)",
    "FS":             "Front safety distance (mm)",
    "FRAME":          "Entrance door frame (mm)",
    "RAIL":           "Rail head width (mm)",
    "OFFSET_CABIN":   "Car offset (mm)",
    "LengthTemplate": "Plumb template length (mm) — for the plumb layout",
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
        st.session_state["_fase_pending"] = "📝 Survey data"

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
        st.success(t(":material/check_circle: Matrix, parameters and settings loaded from the Excel file.")
                   if _pend.get("todo") else
                   t(":green[:material/check_circle:] Matrix loaded from the Excel file (the drawing's parameters are kept)."))

    if st.session_state.pop("_dup_msg", False):
        st.success(t(":material/summarize: Survey duplicated: parameters and configuration were kept. Enter the matrix for the next lift and calculate."))

    # Aviso cuando se llega desde "Reconstruir proyecto" (Mi grupo → detalle)
    if st.session_state.get("_rebuilt_from"):
        st.info(f":material/download: You loaded project **{st.session_state['_rebuilt_from']}**. "
                "Press **:material/play_arrow: Calculate** to regenerate diagrams and reports.")

    # ── Identificación del proyecto ───────────────────────
    # NO se teclea: el survey alimenta un proyecto que YA existe (v135) y ese
    # proyecto trae proyecto/cliente/ubicación/ingeniero. Se toman de él al
    # elegirlo (en el selector del plano, más abajo) y se usan en el informe.
    # En modo «sin proyecto» el informe va sin ellos.
    with st.expander(t(":material/cleaning_services: Start a new survey")):
        st.caption(t("Clears the parameters, matrix, configuration and results of this session. It does not affect projects already saved."))
        if st.button(t(":material/cleaning_services: Clear everything and start over"), key="btn_reset_survey"):
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
    _FASE_DATOS, _FASE_RES = "📝 Survey data", "📊 Resultados e informes"
    _fase = st.radio(t("Phase"), [_FASE_DATOS, _FASE_RES], horizontal=True,
                     format_func=lambda o: {_FASE_DATOS: t(":material/edit: Survey data"),
                                            _FASE_RES: t(":material/insights: Results and reports")}.get(o, o),
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
            '<div style="display:flex;flex-wrap:wrap;gap:14px;align-items:center;font-size:12px;color:#5f6b7a;margin:-6px 0 10px 2px"><span><span style="display:inline-block;width:11px;height:11px;background:#c0392b;border-radius:2px;vertical-align:-1px"></span> out of limit — the most critical value in its column</span><span><span style="display:inline-block;width:11px;height:11px;background:#f1948a;border-radius:2px;vertical-align:-1px"></span> out of limit</span><span><span style="display:inline-block;width:11px;height:11px;background:#e67e22;border-radius:2px;vertical-align:-1px"></span> needs cutting (OR/OL)</span><span style="opacity:.85">WR·WL·FR·FL fail <b>below</b> the limit; OR·OL fail <b>above</b> it.</span></div>', unsafe_allow_html=True)

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
            e1.metric(t("Lateral (RL)"),  f"{_b['rl']:+.1f} mm")
            e2.metric(t("Front (FB)"),  f"{_b.get('fb_applied', _b['fb']):+.1f} mm")
            e3.metric(t("Out of limit"), _off)
            e4.metric(t("Optimal solutions"), len(opt_result.get("all_solutions", [])))
            if _off == 0:
                st.success(t(":material/check_circle: Solution found **with no values out of limit**."))
            else:
                _cols_off = [c for c in SURVEY_COLS if (_b.get("off_by_col") or {}).get(c, 0)]
                st.warning(f":material/warning: The active solution leaves **{_off} value(s) out of limit**"
                           + (f" in: **{', '.join(_cols_off)}**." if _cols_off else "."))
        else:
            st.error(t(":material/cancel: No valid combination was found with these parameters."))

        with st.expander(t("Calculated parameters"), icon=":material/calculate:", expanded=False):
            st.dataframe(
                pd.DataFrame([
                    {"Parameter": k, "Valor": round(v, 3) if isinstance(v, (int, float)) else v}
                    for k, v in limits.items()
                ]),
                width="stretch", hide_index=True
            , column_config=tabla.cfg())

        st.subheader(t("Adjusted SURVEY matrix"))
        st.dataframe(survey_adj_df.style.apply(highlight, axis=None),
                     width="stretch", column_config=tabla.cfg())
        _leyenda_matriz()

        st.subheader(t("Column summary — initial state"))
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
                "Limit (mm)":         round(lim_c, 2),
                "Out of limit":        analysis[f"{col}_OFF_COUNT"],
                "Niveles incumplidos": ", ".join(viols) if viols else "—",
                "Min / Max (mm)":      ext,
                "Diferencia (mm)":     round(analysis[f"DIF_{col}"], 2),
            })
        st.dataframe(pd.DataFrame(summary), width="stretch", hide_index=True, column_config=tabla.cfg())

        st.info(
            f"**MAX OFF RL:** {analysis['MAX_OFF_RL']:.2f} mm  |  "
            f"**MAX OFF FB:** {analysis['MAX_OFF_FB']:.2f} mm  |  "
            f"**BC_CALC:** {limits.get('BC_CALC', 0):.2f} mm  |  "
            f"**DIF TSW-FS:** {limits.get('DIF_TSW_FS', 0):.2f} mm  |  "
            f"**FB max. backwards:** {limits.get('FB_MAX_BACK', 0):.2f} mm"
        )

        # ── Optimización ──────────────────────────────────────
        st.subheader(t(":material/search: Optimisation"))
        best          = opt_result.get("best")
        all_solutions = opt_result.get("all_solutions", [])
        step_log      = opt_result.get("step_log", [])

        if best:
            st.success(
                f":green[:material/check_circle:] Found **{len(all_solutions)} optimal solution(s)** with "
                f"**{best['total_off']} value(s) out of limit**"
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
                    t(":material/star: Active solution — used in diagrams, plumb setting and reports"),
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

                with st.expander(t("Compare solutions side by side"), icon=":material/compare:", expanded=False):
                    _comp = []
                    for k, s in enumerate(sorted_solutions):
                        _obc = s.get("off_by_col", {}) or {}
                        _comp.append({
                            "": "activa" if k == _idx_act else "",
                            "#": k + 1, "RL": s["rl"], "FB": s["fb"],
                            "FB aplic.": s.get("fb_applied", s["fb"]),
                            "Fuera": s["total_off"],
                            **{c: _obc.get(c, 0) for c in SURVEY_COLS},
                        })
                    st.dataframe(pd.DataFrame(_comp), hide_index=True, width="stretch", column_config=tabla.cfg())
            for idx_sol, sol in enumerate(sorted_solutions):
                is_best   = (sol["rl"], sol["fb"]) == best_pair
                fb_ap     = sol.get("fb_applied", sol["fb"])
                fb_suffix = f"  |  FB aplic. = {fb_ap:.1f} mm" if abs(fb_ap - sol["fb"]) > 0.01 else ""
                sol_label = f"{':material/star: ' if is_best else ''}{t('Solution')} {idx_sol+1} — RL = {sol['rl']:+.1f} mm  |  FB = {sol['fb']:+.1f} mm{fb_suffix}"
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
                                 width="stretch", column_config=tabla.cfg())
                    _leyenda_matriz()
                    if not wall_limiting_:
                        st.caption(t("CUT OR / CUT OL: how much to cut if OR/OL exceeds the limit (OR/OL − LIMIT). Positive = a cut is needed. Blank = within the limit."))
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
                            "Limit (mm)":   round(lim_c, 2),
                            "Out of limit":  off_c,
                            "Niveles":       ", ".join(viols_s) if viols_s else "—",
                            lbl:             round(ext_c, 2),
                            "Diff vs Limit": round(dif_c, 2),
                        })
                    st.dataframe(pd.DataFrame(sol_sum), width="stretch", hide_index=True, column_config=tabla.cfg())

            # El log expone la traza del optimizador (pasos, descartes y por que).
            # Es logica propietaria: misma regla que ya aplica el agente IA y que
            # excluye el informe del cliente. Solo el propietario lo ve.
            if _ROL == "propietario":
                with st.expander(f"Optimiser log ({len(step_log)} steps evaluated)", icon=":material/list_alt:", expanded=False):
                    valid_steps  = [s for s in step_log if s.get("status") == "VALID"]
                    skip_steps   = [s for s in step_log if s.get("status") == "SKIP"]
                    skip_phys    = [s for s in skip_steps if s.get("skip_type", "").startswith("physical")]
                    skip_wall    = [s for s in skip_steps if s.get("skip_type") == "wall"]
                    skip_frame   = [s for s in skip_steps if s.get("skip_type") == "frame_opening"]
                    st.caption(
                        f"Valid: {len(valid_steps)}  |  "
                        f"Skipped for physical limit (RL/FB): {len(skip_phys)}  |  "
                        f"Skipped for the wall: {len(skip_wall)}  |  "
                        f"Skipped for a blocked opening: {len(skip_frame)}"
                    )
                    if valid_steps:
                        opt_pairs = {(s["rl"], s["fb"]) for s in all_solutions}
                        best_p    = (best["rl"], best["fb"])
                        log_rows  = []
                        for s in valid_steps:
                            obc  = s.get("off_by_col", {})
                            pair = (s["rl"], s["fb"])
                            if pair == best_p:        estado = "SELECTED"
                            elif pair in opt_pairs:   estado = "OPTIMAL"
                            else:                     estado = ""
                            log_rows.append({
                                "RL": s["rl"], "FB": s["fb"],
                                "FB aplic.": s.get("fb_applied", s["fb"]),
                                "Total OFF": s["total_off"],
                                "WR": obc.get("WR", 0), "FR": obc.get("FR", 0),
                                "OR": obc.get("OR", 0), "WL": obc.get("WL", 0),
                                "FL": obc.get("FL", 0), "OL": obc.get("OL", 0),
                                "Status": estado,
                            })
                        log_rows = (
                            [x for x in log_rows if x["Status"] == "SELECTED"] +
                            [x for x in log_rows if x["Status"] == "OPTIMAL"] +
                            [x for x in log_rows if x["Status"] == ""]
                        )
                        df_log = pd.DataFrame(log_rows)
                        def _hl(row):
                            if row["Status"] == "SELECTED":
                                return ["background-color:#7b5c00;color:white;font-weight:bold"] * len(row)
                            if row["Status"] == "OPTIMAL":
                                return ["background-color:#1a3a2a;color:#a8e6cf"] * len(row)
                            return [""] * len(row)
                        st.dataframe(df_log.style.apply(_hl, axis=1),
                                     width="stretch", hide_index=True, column_config=tabla.cfg())
        else:
            st.error(t("No valid combination was found."))

        # ── Diagrama físico — planta por piso ─────────────────
        st.subheader(t(":material/architecture: Positioning diagram — plan view per floor"))
        st.caption(t("Top view of how the car fits in the shaft on each floor (matrix of the selected solution). Green = within limit, orange = at the limit, red = out."))
        if best and best.get("matrix"):
            n_floors = len(best["matrix"])
            _prob = floors_with_issues(best, lim_map)

            with st.expander(t("Isometric view of the shaft"), icon=":material/view_in_ar:", expanded=False):
                components.html(
                    shaft_iso_svg(all_params, limits, best, n_floors, lim_map,
                                  proyecto=str(st.session_state.get("proyecto", ""))),
                    height=730, scrolling=False,
                )

            # ⚠️ Se comparan abajo → se traduce el display, no la opción.
            _MODO = {"With issues": "With issues", "Todos": "All", "Elegir": "Choose"}
            _modo = st.radio(
                t("Floors to show"),
                list(_MODO), format_func=lambda o: t(_MODO[o]),
                horizontal=True, key="diag_modo", label_visibility="collapsed",
            )
            if _modo == "With issues":
                _floors = _prob or list(range(n_floors))
                st.caption(f"Showing {len(_floors)} of {n_floors} floors"
                           + ("" if _prob else " (none has any issue: all are shown)"))
            elif _modo == "Todos":
                _floors = list(range(n_floors))
            else:
                _floors = st.multiselect(
                    t("Floors"), list(range(n_floors)),
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
                if st.button(t(":material/picture_as_pdf: Prepare a PDF of these diagrams"), key="btn_diag_pdf"):
                    with st.spinner("Generating the diagrams PDF..."):
                        st.session_state["_diag_pdf"] = floor_plans_pdf(
                            all_params, limits, best, lim_map, ctrl_in_frame_, ctrl_side_,
                            floors=_floors,
                            titulo=f"Positioning diagrams — "
                                   f"{all_params.get('PROYECTO') or 'Survey'}")
                if st.session_state.get("_diag_pdf"):
                    st.download_button(t(":material/download: Download diagrams (PDF)"),
                                       data=st.session_state["_diag_pdf"],
                                       file_name="positioning_diagrams.pdf",
                                       mime="application/pdf", key="dl_diag_pdf")

        # ── BSR vs BS ─────────────────────────────────────────
        st.subheader(t(":material/straighten: BSR vs BS analysis"))
        if not bs_result.get("needed"):
            st.success(t("BSR ≥ BS — no shaft adjustment is needed."))
        elif bs_result.get("step") is None:
            st.error(f"No step was found. DIF BS = {bs_result.get('dif_original')} mm")
        else:
            st.success(
                f":green[:material/check_circle:] Step: **{bs_result['step']} mm**  |  "
                f"Range: **{bs_result['range']}**  |  Zone: **{bs_result['range_name']}**"
            )

        # ── Plomado definitivo (con el desplazamiento del survey) ──
        st.subheader(t(":material/straighten: Final plumb setting (from the survey)"))
        st.caption(t("Plumb layout with the shifts the survey worked out. The assembly (plumb points + theoretical walls + template) moves; the real walls stay fixed (zero axis = real left wall)."))
        if plumb_res and best:
            st.info(
                f"Shift applied:  lateral (rl) = **{best['rl']:.1f} mm**  ·  "
                f"front (fb) = **{best['fb_applied']:.1f} mm**."
            )
            pm1, pm2, pm3 = st.columns(3)
            pm1.metric(t("DBP"),  f"{plumb_res['dbp']:.1f} mm")
            pm2.metric(t("DBPW"), f"{plumb_res['dbpw']:.1f} mm")
            pm3.metric("RW",   f"{plumb_res['rw']:.1f} mm")
            st.dataframe(pd.DataFrame(plumb_table(plumb_res)),
                         width="stretch", hide_index=True, column_config=tabla.cfg())
            _pr_ = str(st.session_state.get("proyecto", ""))
            _bs = plumb_res.get("bs_check") or {}
            if _bs and not _bs.get("ok", True):
                st.error(
                    f":orange[:material/warning:] **BS does not add up:** the drawing says **{_bs['bs_plano']:.0f}** but "
                    f"SF1+BKS+2·RAIL+SF2 = **{_bs['bs_componentes']:.0f}** "
                    f"(diff {_bs['dif']:+.0f} mm). The fit uses (BSR−BS)/2, so with this "
                    f"mismatch the plumb points end up in the wrong place. Check BS, SF1, SF2, BKS or RAIL."
                )
            components.html(
                '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
                + plumb_svg(plumb_res, proyecto=_pr_) + '</body></html>',
                height=500, scrolling=False,
            )
            _v3d, _vfi = st.columns(2)
            with _v3d.expander(t("3D views of the setting out"), icon=":material/view_in_ar:", expanded=False):
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
            with _vfi.expander(t("Setting-out card (for site)"), icon=":material/assignment:", expanded=False):
                st.caption(t("The numbers to measure with a tape. Print it or open it on your phone."))
                components.html(
                    '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
                    + plumb_card_svg(plumb_res, proyecto=_pr_) + '</body></html>',
                    height=430, scrolling=False,
                )
            st.markdown(t("**:material/straighten: On-site check — plumb ↔ real wall distances**"))
            st.dataframe(pd.DataFrame(plumb_checks(plumb_res)),
                         width="stretch", hide_index=True, column_config=tabla.cfg())
            if float(all_params.get("LengthTemplate", 0.0)) <= 0:
                st.info(t(":material/lightbulb: Enter **LengthTemplate** in the parameters to see the full template (point P, cuts C1/C2 and diagonals)."))
        else:
            st.caption(t("It will be shown once the survey finds a valid solution."))

        # ── Estado de las interpretaciones IA ─────────────────
        if not interpretation.get("_ok"):
            st.error(
                f":orange[:material/warning:] **The technical interpretation could not be generated:** {interpretation.get('_error')}\n\n"
                "The reports **require** the AI interpretation. Check that "
                "`ANTHROPIC_API_KEY` is configured in the **Streamlit Cloud Secrets**."
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
            st.error(t(":material/warning: Problems in the parameters — check before calculating:"))
            for issue in issues:
                st.error(f"  • {issue}")
            st.stop()

        try:
            limits = calculate_limits(all_params)
        except Exception as e:
            st.error(f"Error in the calculation: {e}")
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
        with st.spinner(":material/search: Searching for the optimal combination..."):
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
                st.warning(f"The final plumb setting could not be generated: {e}")

        # ── Interpretaciones IA (admin + usuario) ─────────────
        _calc_for_ia = {
            "limits":           limits,
            "analysis":         analysis,
            "optimizer_result": opt_result,
            "bs_result":        bs_result,
        }
        with st.spinner(":material/smart_toy: Generating the technical interpretation with AI..."):
            interpretation = generate_interpretation(_calc_for_ia, all_params)
        with st.spinner(":material/smart_toy: Generating the client report's interpretation..."):
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
        _auto  = build_schedule(_c["ns"], clock.today(), _flags)
        st.session_state.calc_results["schedule"] = _auto
        st.session_state["sched_rows"] = [
            {"Actividad": a["nombre"], "Duración (d)": int(a["duracion"]), "Peso (%)": a["peso"]}
            for a in _auto["activities"]
        ]
        st.session_state["sched_start"] = clock.today()

        # ── Informe ADMIN (completo) → correo interno ─────────
        admin_pdf = None
        if interpretation.get("_ok"):
            try:
                with st.spinner(":material/description: Preparing the internal admin report..."):
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
                st.warning(f"The admin report for the email could not be generated: {e}")

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
            st.info(t(":material/mail: Internal management report sent by email."))
        if interpretation.get("_ok"):
            st.success(t(":material/smart_toy: Interpretations generated successfully."))
        st.success(t(":material/check_circle: Calculation and interpretation completed."))

    if _fase == _FASE_DATOS:
        # PASO 1 — CARGAR PDF
        # ══════════════════════════════════════════════════════
        st.header(t(":material/description: Lift drawing"))

        # ── Proyecto: sus datos del plano, ya leídos ─────────
        # Desde v137 el plano se lee UNA vez al crear el proyecto. Aquí solo se
        # vuelcan sus valores: el técnico no tiene que volver a subir el PDF ni
        # esperar la extracción (que cuesta ~80 s).
        _prj_sv, _plano_sv = plan_ui.selector_proyecto("sv")
        # Identidad del informe TOMADA del proyecto elegido (ya no se teclea).
        # Seguro escribir estas claves: dejaron de ser widgets al quitar los
        # text_input de arriba (habría sido el error de v111 si aún lo fueran).
        if _prj_sv:
            st.session_state["proyecto"]  = str(_prj_sv.get("Name", ""))
            st.session_state["cliente"]   = str(_prj_sv.get("Client", ""))
            st.session_state["ubicacion"] = str(_prj_sv.get("Location", ""))
            # ⚠️ El NOMBRE, no los login. La columna guarda «campo1;mchen» (v459) y
            # esta clave es la que pintan el informe del CLIENTE y el correo: sin
            # resolver, el documento que se le manda al cliente diría «campo1;mchen».
            _ing_sv = projects_data.head_installers_label(
                _prj_sv, str(_prj_sv.get("Group", _GRUPO)))
            st.session_state["ingeniero"] = _ing_sv
            _rep = " · ".join(x for x in (str(_prj_sv.get("Client", "")),
                                          str(_prj_sv.get("Location", "")),
                                          _ing_sv) if x)
            st.caption(":material/info: The report will use this project's details"
                       + (f": {_rep}." if _rep else "."))
            if str(_prj_sv.get("Location", "")).strip():
                from core import maps as _maps
                st.caption(_maps.maps_link_md(_prj_sv.get("Location"), ":material/place: see on Maps"))
        else:
            # Sin proyecto: cálculo suelto, el informe va sin identidad.
            for _kid in ("proyecto", "cliente", "ubicacion", "ingeniero"):
                st.session_state[_kid] = ""
        if _plano_sv:
            _mapa_sv = {f"params.{_p}": f"inp_{_p}" for _p in PDF_PARAMS}
            _mapa_sv["ns"] = "ns"
            _mapa_sv["rail_altura"] = "inp_RAIL"   # altura del diente, del catálogo
            _n_sv = plan_ui.aplicar(_plano_sv, _mapa_sv)
            if _n_sv:
                st.caption(f":green[:material/check_circle:] {_n_sv} value(s) taken from the project drawing. "
                           "Check them and fill in the ones measured on site.")
            if _plano_sv.get("rail"):
                st.caption(f":material/train: Rail from the drawing: **{_plano_sv['rail']}** "
                           "— adjust RAIL if the catalogue does not have it.")

        col_brand, col_pdf = st.columns([1, 3])
        col_brand.selectbox(t("Brand"), ["Schindler"], key="brand")   # placeholder p/ futura expansión
        pdf_file = col_pdf.file_uploader(t("Drawings PDF"), type=["pdf"])

        if pdf_file is not None and pdf_file.name != st.session_state.get("last_pdf_name"):
            with st.spinner(":material/hourglass_empty: Extracting data from the PDF..."):
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
                            f":green[:material/check_circle:] Car guide rail **{_code}** → RAIL = **{_info['altura']} mm** "
                            "(tooth height from the back, from the catalogue).")
                    else:
                        st.session_state["rail_ref_msg"] = (
                            f":orange[:material/warning:] Rail **{_code}** was detected but **it is not in the Rails catalogue**. "
                            "Enter RAIL by hand or add it to the catalogue.")
                else:
                    st.session_state["rail_ref_msg"] = (
                        ":blue[:material/info:] The car guide rail code was not detected; enter RAIL by hand.")
            except Exception:
                pass
            # ── Número de paradas: NUMBER OF STOPS del plano → NS ──
            st.session_state["ns_msg"] = ""
            try:
                from extractors.schindler import extract_number_of_stops
                _ns = extract_number_of_stops(pdf_file)
                if _ns and 2 <= _ns <= 50:
                    st.session_state["ns"] = int(_ns)
                    st.session_state["ns_msg"] = f":green[:material/check_circle:] NUMBER OF STOPS from the drawing → NS = **{_ns}**."
                else:
                    st.session_state["ns_msg"] = (":blue[:material/info:] NUMBER OF STOPS was not detected on the drawing; enter NS by hand.")
            except Exception:
                pass
            found   = sum(1 for v in extracted.values() if v is not None)
            missing = [k for k,v in extracted.items() if v is None]
            flash.exito(f":material/check_circle: {found}/{len(extracted)} parameters found.")
            if missing:
                st.warning(f":material/warning: Enter by hand: **{', '.join(missing)}**")
            st.rerun()
        elif pdf_file and pdf_file.name == st.session_state.get("last_pdf_name"):
            st.info(f":material/description: Data from: **{pdf_file.name}** — see the sidebar.")

        if st.session_state.get("rail_ref_msg"):
            _m = st.session_state["rail_ref_msg"]
            (st.success if _m.startswith(":material/check_circle:") else
             st.warning if _m.startswith(":material/warning:") else st.info)(_m)

        # ══════════════════════════════════════════════════════
        # PASO 2 — PARÁMETROS
        # ══════════════════════════════════════════════════════
        st.header(t(":material/tune: Parameters"))

        # Marca por campo: ✅ leído del plano · ✏️ a completar a mano.
        # (Recupera la señal que se perdió al quitar el panel del sidebar en v93.)
        _ext = st.session_state.get("pdf_extracted") or {}

        def _mark(p):
            if not _ext or p not in _ext:
                return ""
            return ":green[:material/check_circle:] " if _ext.get(p) is not None else "✏️ "

        if _ext:
            _found = [p for p, v in _ext.items() if v is not None]
            _miss  = [p for p, v in _ext.items() if v is None]
            _r1, _r2 = st.columns([1, 2])
            _r1.metric(t("Read from the drawing"), f"{len(_found)}/{len(_ext)}")
            if _miss:
                _r2.warning(":material/edit: Fill in by hand: **" + "**, **".join(_miss) + "**")
            else:
                _r2.success(t(":green[:material/check_circle:] The drawing supplied every parameter."))

        with st.expander(t("Drawing parameters (editable)"), icon=":material/description:", expanded=True):
            _pendientes = list(PDF_PARAMS)
            for _titulo, _lista in _GRUPOS_PARAM:
                _ps = [p for p in _lista if p in _pendientes]
                if not _ps:
                    continue
                st.markdown(f"**{t(_titulo)}**")
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
                st.markdown(t("**Others**"))
                _cols = st.columns(4)
                for j, p in enumerate(_pendientes):
                    _cols[j % 4].number_input(
                        label = f"{_mark(p)}{p} (mm)", step = 0.5,
                        help  = PARAM_DESCRIPTIONS.get(p, ""), key = f"inp_{p}",
                    )

        with st.expander(t("Parameters measured on site"), icon=":material/straighten:", expanded=True):
            cols = st.columns(len(USER_ONLY))
            for j, (p, desc) in enumerate(USER_ONLY.items()):
                cols[j].number_input(
                    label = f"{p} (mm)",
                    step  = 0.5,
                    help  = desc,
                    key   = f"inp_{p}",
                )

        st.markdown(t("**:material/tune: Configuration**"))
        c1, c2, c3 = st.columns(3)
        c1.radio(t("Omega side"),        ["R", "L"], horizontal=True, key="cfg_omega_side")
        c2.radio(t("Is there a limiting wall?"), ["N", "Y"], horizontal=True, key="cfg_wall_yn")
        c3.radio(t("Car offset side"),    ["R", "L"], horizontal=True, key="cfg_offset_side")

        wall_limiting = (st.session_state.cfg_wall_yn == "Y")
        if wall_limiting:
            wc1, wc2 = st.columns(2)
            wc1.number_input(t("Limiting stop"), min_value=1, step=1, key="cfg_wall_stop")
            wc2.radio(t("Wall side"),        ["R", "L"], horizontal=True, key="cfg_wall_side")

        cc1, cc2 = st.columns(2)
        cc1.radio(t("Is the controller part of the frame?"), ["N", "Y"], horizontal=True, key="cfg_ctrl_yn")
        ctrl_in_frame = (st.session_state.cfg_ctrl_yn == "Y")
        if ctrl_in_frame:
            cc2.radio(t("Controller side"), ["R", "L"], horizontal=True, key="cfg_ctrl_side")

        # Lectura final de configuración para resto del flujo
        omega_side  = st.session_state.cfg_omega_side
        offset_side = st.session_state.cfg_offset_side
        wall_stop   = st.session_state.cfg_wall_stop if wall_limiting else None
        wall_side   = st.session_state.cfg_wall_side if wall_limiting else None
        ctrl_side   = st.session_state.cfg_ctrl_side if ctrl_in_frame else None

        # ══════════════════════════════════════════════════════
        # PASO 3 — MATRIZ SURVEY
        # ══════════════════════════════════════════════════════
        st.header(t(":material/grid_on: Survey matrix"))

        sc1, sc2, sc3 = st.columns([1, 2, 2])

        sc1.number_input(t("Number of stops (NS)"), min_value=2, max_value=50, step=1, key="ns")
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
        uploaded_excel = sc2.file_uploader(t(":material/folder_open: Load matrix (.xlsx)"), type=["xlsx"], key="excel_uploader")
        # Por defecto solo se importa la MATRIZ: si ya cargaste el plano, los parámetros del
        # PDF mandan y no deben ser pisados por los que venían guardados en el Excel.
        _imp_todo = sc2.checkbox(t("Also restore parameters and configuration from the Excel file"),
                                 value=False, key="excel_imp_todo",
                                 help=t("Unticked: only the measurement matrix is imported."))
        if st.session_state.get("last_excel_id") and sc2.button(t(":material/refresh: Import the Excel again"),
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
                sc2.error(f"Error importing the Excel file: {e}")

        st.caption(t("Enter or edit the measurements taken on site (mm)."))
        edited_df = st.data_editor(
            st.session_state.survey_df,
            width="stretch",
            num_rows="fixed",
            key="survey_editor"
        , column_config=tabla.cfg())
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
            label     = t(":material/download: Save matrix (.xlsx)"),
            data      = excel_bytes,
            file_name = "survey_matrix.xlsx",
            mime      = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch"
        )

        # ══════════════════════════════════════════════════════

        st.markdown("---")

        # ── ¿Listo para calcular? Estado de cada entrada ──
        _ex   = st.session_state.get("pdf_extracted") or {}
        _falt = [p for p, v in _ex.items() if v is None] if _ex else []
        _nsv  = int(st.session_state.get("ns", 2))
        _chips = [
            (":green[:material/check_circle:] Drawing loaded" if _ex else ":gray[:material/radio_button_unchecked:] No drawing (parameters by hand)"),
            (":green[:material/check_circle:] Parameters complete" if (_ex and not _falt)
             else (f":orange[:material/warning:] {len(_falt)} parameter(s) not read" if _falt else ":material/edit: Manual parameters")),
            f":green[:material/check_circle:] Matriz: {_nsv} niveles",
        ]
        st.markdown("  ·  ".join(_chips))

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
            with st.expander(f":material/warning: {len(_iss0)} warning(s) in the parameters", expanded=False):
                for _x in _iss0:
                    st.warning(_x)

        if st.button(t(":material/play_arrow: Calculate and see the results"), type="primary",
                     width="stretch", key="btn_calc_datos"):
            _do_calculo()
            st.session_state["_fase_pending"] = _FASE_RES
            st.rerun()

        with st.expander(t(":material/summarize: Duplicate for the next lift")):
            st.caption(t("Keeps this survey's parameters and configuration and clears the matrix and the results. Useful when there are several lifts in the same shaft."))
            if st.button(t(":material/summarize: Duplicate survey"), key="btn_dup_survey"):
                st.session_state["_dup_survey"] = True
                st.rerun()


    else:

        st.header(t(":material/insights: Results"))
        if not st.session_state.calc_results:
            st.info(t("No calculation yet. Go to **:material/edit: Survey data**, fill in the information and press **:material/play_arrow: Calculate and see the results**."))
        else:
            if st.session_state.get("_calc_sig") and st.session_state["_calc_sig"] != _survey_signature():
                st.warning(t(":material/warning: You changed data since the last calculation. What is below belongs to the previous one — recalculate to update it."))
            if st.button(t(":material/sync: Recalculate with the current data"), width="stretch",
                         key="btn_recalc"):
                _do_calculo()
                st.rerun()
            _render_survey_results(st.session_state.calc_results)

        # PASO 5 — GESTIÓN DE PROYECTO (cronograma + curva S)
        # ══════════════════════════════════════════════════════
        st.header(t(":material/calendar_month: Schedule"))
        if st.session_state.calc_results:
            st.caption(t("Schedule and S-curve generated automatically for the project (scaled by NS and by what the analysis found). Adjust durations and weights if you need to — the S-curve recalculates itself."))

            if "sched_start" not in st.session_state:
                st.session_state["sched_start"] = clock.today()

            gc1, gc2 = st.columns([1, 2])
            start = gc1.date_input(t("Project start date"), key="sched_start")

            # Editor de actividades (nombre bloqueado; duración y peso editables)
            sched_rows = st.session_state.get("sched_rows", [])
            if sched_rows:
                edited = st.data_editor(
                    pd.DataFrame(sched_rows),
                    width="stretch", hide_index=True, num_rows="fixed",
                    disabled=["Actividad"], key="sched_editor",
                column_config=tabla.cfg())
                st.session_state["sched_rows"] = edited.to_dict("records")

                custom = [{"nombre": r["Actividad"],
                           "duracion": r.get("Duración (d)", 1),
                           "peso":     r.get("Peso (%)", 1)}
                          for r in st.session_state["sched_rows"]]
                sched = build_schedule(int(st.session_state.ns), start, {}, custom_rows=custom)
                st.session_state.calc_results["schedule"] = sched

                m1, m2, m3 = st.columns(3)
                m1.metric(t("Total duration"), f"{sched['total_dias']} days")
                m2.metric(t("Start"),       sched["start_date"].strftime("%d/%m/%Y"))
                m3.metric(t("Estimated finish"), sched["fecha_fin"].strftime("%d/%m/%Y"))

                components.html(
                    '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
                    + schedule_svg(sched, animar=True)      # v336: pantalla
                    + '</body></html>',
                    height=140 + len(sched["activities"]) * 22 + 200,
                    scrolling=False,
                )
        else:
            st.info(t("Do the calculation first to generate the schedule."))

        # ══════════════════════════════════════════════════════
        # PASO 6 — INFORME DEL CLIENTE  (solo propietario / administrador)
        # ══════════════════════════════════════════════════════
        if not can_reports(_ROL):
            st.header(t(":material/description: Client report"))
            st.caption(t(":material/lock: Report downloads are available to management (owner / administrator)."))
        else:
            st.header(t(":material/description: Client report"))
            st.caption(t("A professional report to hand to the client (final solution, diagrams and implementation instructions). The internal technical report is emailed to management automatically."))

            if st.session_state.calc_results:
                r          = st.session_state.calc_results
                interp     = r.get("interpretation") or {}
                interp_usr = r.get("interpretation_user") or {}
                if not interp_usr.get("_ok"):
                    st.error(
                        ":red[:material/block:] **The report cannot be generated without the AI interpretation.**\n\n"
                        f"Reason: {interp_usr.get('_error', interp.get('_error', 'not available'))}.\n\n"
                        "Configure `ANTHROPIC_API_KEY` in the Streamlit Cloud Secrets and calculate again."
                    )
                elif st.button(t(":material/description: Generate the client report"), width="stretch"):
                    with st.spinner("Generating the client report..."):
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
                        label     = t(":material/download: Download the client report"),
                        data      = user_pdf,
                        file_name = f"informe_{proj}.pdf",
                        mime      = "application/pdf",
                        width="stretch"
                    )
            else:
                st.info(t("Do the calculation first so the report can be generated."))

        # ══════════════════════════════════════════════════════
        # PASO 7 — GUARDAR COMO PROYECTO  (solo administrador / propietario)
        # ══════════════════════════════════════════════════════
        # ══════════════════════════════════════════════════════
        # GUARDAR EN EL PROYECTO  (v135: el survey ya NO crea proyectos)
        # ══════════════════════════════════════════════════════
        # El survey pasa a ser una herramienta que ALIMENTA un proyecto, igual
        # que Plomadas, Cortes o Belting. El proyecto se crea aparte, en
        # 🛠 Mi grupo → ➕ Nuevo proyecto. Motivo: la obra existe antes que el
        # survey, y atar la creación al survey obligaba a tenerlo hecho para
        # poder dar de alta el proyecto.
        if _ROL in ("administrador", "propietario"):
            st.header(t(":material/save: Save to the project"))
            if not st.session_state.get("calc_results"):
                st.info(t("Calculate first so the survey can be saved to a project."))
            elif not projects_data.is_configured():
                st.caption(t(":material/lock: This needs Google Sheets configured."))
            else:
                r  = st.session_state.calc_results
                ap = r["all_params"]
                _proys = (projects_data.list_projects() if _ROL == "propietario"
                          else projects_data.list_projects(_GRUPO))
                if not _proys:
                    st.info(t("There are no projects yet. Create one in {x} and come back here "
                              "to attach this survey to it.")
                            .replace("{x}", t("**👑 Administration → :material/folder: Projects**")
                                     if _ROL == "propietario" else
                                     t("**:material/build: My company → :material/bar_chart: "
                                       "Projects → :material/add: New project**")))
                else:
                    st.caption(t("The parameters, the matrix and the interpretations are attached to the project, and the drawing, the matrix and the client report are filed. The project's schedule and progress are NOT touched."))
                    _idmap = {f"{p.get('Name')} ({p.get('ID')})": p for p in _proys}
                    _sel = st.selectbox(t("Target project"),
                                        [_VACIO] + list(_idmap.keys()),
                                        key="sv_prj_sel")
                    if not _sel or _sel == _VACIO:
                        st.caption(t("Choose which project to attach this survey to."))
                        _prj = None
                    else:
                        _prj = _idmap[_sel]

                    # NS del plano vs NS del proyecto: avisar, nunca pisar en silencio
                    # (protegido: _prj es None mientras no se elija destino)
                    try:
                        assert _prj is not None
                        _ns_prj = int(float(_prj.get("NS") or 0))
                        _ns_sv  = int(float(ap.get("NS") or 0))
                        if _ns_prj and _ns_sv and _ns_prj != _ns_sv:
                            st.warning(f":material/warning: The project has **NS = {_ns_prj}** and this survey has "
                                       f"**NS = {_ns_sv}**. Check which one is right: the "
                                       "project schedule was worked out with its own.")
                    except Exception:
                        pass

                    if st.button(t(":material/save: Save the survey to this project"),
                                 width="stretch", key="sv_save_prj",
                                 disabled=(_prj is None)):
                        _pid = str(_prj.get("ID", ""))
                        _usr = st.session_state.get("auth", {}).get("usuario", "")
                        _matriz = (r["survey_orig"].to_dict("records")
                                   if hasattr(r.get("survey_orig"), "to_dict") else [])
                        ok, msg = projects_data.attach_survey(
                            _pid, params=ap, matriz=_matriz,
                            interp={"admin": r.get("interpretation"),
                                    "user":  r.get("interpretation_user")})
                        if not ok:
                            st.error(f"It could not be saved: {msg}")
                        else:
                            _best = (r.get("optimizer_result") or {}).get("best") or {}
                            st.session_state["_prj_creado"] = {
                                "id": _pid, "nombre": str(_prj.get("Name", ""))}

                            # Registro en el historial de cálculos del proyecto
                            try:
                                toolruns.registrar(
                                    pid=_pid, grupo=str(_prj.get("Group", _GRUPO)),
                                    herramienta="survey",
                                    resumen=(f"RL {_best.get('rl', 0):+.1f} · "
                                             f"FB {_best.get('fb_applied', _best.get('fb', 0)):+.1f} · "
                                             f"{_best.get('total_off', 0)} out of limit"),
                                    datos={"rl": _best.get("rl"), "fb": _best.get("fb"),
                                           "total_off": _best.get("total_off"),
                                           "ns": ap.get("NS")},
                                    usuario=_usr)
                            except Exception as e:
                                # El survey YA quedó guardado en el proyecto; esto solo
                                # alimenta el historial de cálculos (v131). No se avisa
                                # en pantalla para no ensuciar el éxito, pero deja rastro.
                                logger.warning(
                                    "survey_ui: el cálculo no entró al historial "
                                    "del proyecto %s: %s", _pid, e)

                            # Documentos base en Drive (best-effort)
                            if drive_store.is_configured() and drive_store.is_available():
                                _fallos = []
                                with st.spinner("Filing documents in Drive..."):
                                    try:
                                        pb = st.session_state.get("pdf_bytes")
                                        if pb:
                                            fid = drive_store.upload(_pid, "plano.pdf", pb,
                                                                     "application/pdf")
                                            projects_data.add_document(_pid, "plano.pdf",
                                                                       "plano", fid, _usr)
                                    except Exception:
                                        _fallos.append("plano")
                                    try:
                                        csv = r["survey_orig"].to_csv(index=False).encode("utf-8")
                                        fid = drive_store.upload(_pid, "matriz_survey.csv", csv,
                                                                 "text/csv")
                                        projects_data.add_document(_pid, "matriz_survey.csv",
                                                                   "matriz_survey", fid, _usr)
                                    except Exception:
                                        _fallos.append("matriz")
                                    try:
                                        if (r.get("interpretation_user") or {}).get("_ok"):
                                            pdfb = generate_user_report(
                                                project_params=r["all_params"],
                                                calculated=r["limits"],
                                                optimizer_result=r["optimizer_result"],
                                                lim_map=r["lim_map"],
                                                survey_cols=SURVEY_COLS,
                                                interpretation_user=r.get("interpretation_user"),
                                                schedule=r.get("schedule"), plumb=r.get("plumb"))
                                            fid = drive_store.upload(_pid, "informe_cliente.pdf",
                                                                     pdfb, "application/pdf")
                                            projects_data.add_document(_pid, "informe_cliente.pdf",
                                                                       "informe_cliente", fid, _usr)
                                    except Exception:
                                        _fallos.append("client report")
                                if _fallos:
                                    st.caption(":material/attach_file: " + t("Documents filed, except") + ": "
                                               + ", ".join(_fallos) + ".")
                                else:
                                    st.caption(t(":material/attach_file: Documents filed in Drive."))
                            elif drive_store.is_configured():
                                st.caption(t(":material/attach_file: Documents not filed: Drive is not connected."))

                            st.success(f":material/check_circle: Survey saved to **{_prj.get('Name')}**.")

                # ── Cerrar el ciclo: llevar al proyecto ──
                _pc = st.session_state.get("_prj_creado")
                if _pc:
                    _c1, _c2 = st.columns([3, 1])
                    _c1.info(f"Project **{_pc['id']} · {_pc['nombre']}** updated with "
                             "this survey.")
                    if _c2.button(t("Open project ➜"), width="stretch",
                                  key="ir_al_proyecto"):
                        st.session_state["_prjsel_pending"] = _pc["id"]
                        # v299: la nav vieja (`_nav_pending` + el radio `main_nav`) se
                        # borró; el salto va por el mecanismo de la shell. Cada rol
                        # tiene su sección de proyectos: el propietario dentro de
                        # Administración, el administrador en la suya.
                        st.session_state["_admin_nav_pending"] = (
                            ("administracion", "📁 Proyectos") if _ROL == "propietario"
                            else ("proyectos", "📊 Proyectos"))
                        st.session_state.pop("_prj_creado", None)
                        st.rerun()
