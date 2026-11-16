"""
Recálculo determinista del survey a partir de datos guardados.

Permite regenerar la solución de un proyecto SIN pasar por la pestaña Survey:
el proyecto guarda `ParamsJSON` (que ya incluye toda la configuración —
OMEGA_SIDE, WALL_LIMITING, WALL_STOP/SIDE, CTRL_*, NS) y `MatrizJSON`, pero
NO la solución, que es derivada.

⚠️ Replica la secuencia de `survey_ui._do_calculo`, pero SOLO su parte
determinista: sin IA, sin correo, sin cronograma y sin nada de Streamlit.
La lógica de verdad sigue viviendo en calculations/optimizer/plumb — aquí solo
se encadenan las llamadas, así que no hay reglas duplicadas que puedan divergir.
"""
import pandas as pd

from core.calculations import calculate_limits, apply_offsets, analyze_matrix
from core.optimizer import optimize
from core.plumb import compute_plumb

SURVEY_COLS = ["WR", "FR", "OR", "WL", "FL", "OL"]


def _si(v) -> bool:
    return v if isinstance(v, bool) else str(v).strip().lower() in ("true", "1", "yes", "y", "sí", "si")


def cfg_de_params(cfg: dict) -> dict:
    """La configuración guardada de un Survey (ParamsJSON de la obra, o la hoja del Excel) → las claves de sus controles.

    ⚠️ v681 · UNA definición (H13 del ciclo 4): «Load this project into the Survey» cargaba medidas, NS y matriz pero NO
    esto, y el muro limitante volvía a «N» (con omega, lado del desplazamiento y controlador por defecto): quien pulsaba
    Calculate, como pedía el aviso, regeneraba los informes con OTRO caso y otra solución. La importación del Excel ya lo
    hacía, con su propia copia de estas líneas."""
    cfg = cfg or {}
    out = {}
    if cfg.get("OMEGA_SIDE") in ("R", "L"):
        out["cfg_omega_side"] = cfg["OMEGA_SIDE"]
    if cfg.get("OFFSET_SIDE") in ("R", "L"):
        out["cfg_offset_side"] = cfg["OFFSET_SIDE"]
    if cfg.get("WALL_LIMITING") is not None:
        out["cfg_wall_yn"] = "Y" if _si(cfg["WALL_LIMITING"]) else "N"
    if cfg.get("WALL_STOP") not in (None, ""):
        try:
            out["cfg_wall_stop"] = int(float(cfg["WALL_STOP"]))
        except (TypeError, ValueError):
            pass
    if cfg.get("WALL_SIDE") in ("R", "L"):
        out["cfg_wall_side"] = cfg["WALL_SIDE"]
    if cfg.get("CTRL_IN_FRAME") is not None:
        out["cfg_ctrl_yn"] = "Y" if _si(cfg["CTRL_IN_FRAME"]) else "N"
    if cfg.get("CTRL_SIDE") in ("R", "L"):
        out["cfg_ctrl_side"] = cfg["CTRL_SIDE"]
    return out


def recalcular(params: dict, matriz) -> dict | None:
    """params = ParamsJSON del proyecto; matriz = MatrizJSON (lista de dicts).

    Devuelve {all_params, limits, lim_map, best, plumb} o None si no se puede.
    """
    if not params or not matriz:
        return None
    try:
        df = pd.DataFrame(matriz)
        if df.empty:
            return None
        ap = dict(params)

        # Totales = ultima fila de la matriz (WRT, FRT, ORT, WLT, FLT, OLT)
        last = df.iloc[-1]
        for col in SURVEY_COLS:
            ap[f"{col[0]}{col[1]}T"] = float(last[col])

        limits = calculate_limits(ap)
        ap.update(limits)

        survey_adj = apply_offsets(df.to_dict("records"), limits)
        analysis = analyze_matrix(survey_adj, limits,
                                  wall_limiting=bool(ap.get("WALL_LIMITING")))
        ap.update(analysis)
        limits.update(analysis)
        lim_map = {c: limits[f"LIMIT_{c}"] for c in SURVEY_COLS}

        best = (optimize(survey_adj, limits, ap) or {}).get("best")
        if not best:
            return None

        plumb = None
        try:
            plumb = compute_plumb(
                {"BKS": ap["BKS"], "RAIL": ap["RAIL"], "TKSW": ap["TKSW"],
                 "LengthTemplate": ap.get("LengthTemplate", 0.0),
                 "SF1": ap["SF1"], "SF2": ap["SF2"],
                 "BSR": ap["BSR"], "BS": ap["BS"]},
                survey_disp={"rl": best["rl"],
                             "fb": best.get("fb_applied", best.get("fb", 0))})
        except Exception:
            plumb = None

        return {"all_params": ap, "limits": limits, "lim_map": lim_map,
                "best": best, "plumb": plumb}
    except Exception:
        return None
