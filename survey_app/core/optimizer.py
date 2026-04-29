import numpy as np
import copy

def optimize(survey_adjusted: list, limits: dict, params: dict) -> dict:
    """
    Busca la combinación óptima de desplazamientos RL y FB.
    Retorna la mejor combinación y la matriz resultante.
    """
    cols    = ["WR", "FR", "OR", "WL", "FL", "OL"]
    lim_map = {
        "WR": limits["LIMIT_WR"], "FR": limits["LIMIT_FR"],
        "OR": limits["LIMIT_OR"], "WL": limits["LIMIT_WL"],
        "FL": limits["LIMIT_FL"], "OL": limits["LIMIT_OL"],
    }

    max_rl = limits["MAX_OFF_RL"]
    max_fb = limits["MAX_OFF_FB"]

    rl_steps = np.arange(-max_rl, max_rl + 0.5, 0.5)
    fb_steps = np.arange(-max_fb, max_fb + 0.5, 0.5)

    limit_r = limits["LIMIT_R"]
    limit_l = limits["LIMIT_L"]

    wall    = params.get("WALL_LIMITING", False)
    wall_stop = params.get("WALL_STOP", None)
    wall_side = params.get("WALL_SIDE", None)
    tsw     = params["TSW"]
    fs      = params.get("FS", None)

    best = None

    for rl in rl_steps:
        # Validar rango RL
        if rl < 0 and abs(rl) > limit_r:
            continue
        if rl > 0 and abs(rl) > limit_l:
            continue

        for fb in fb_steps:
            # Aplicar desplazamientos a copia de la matriz
            modified = []
            for row in survey_adjusted:
                modified.append({
                    "WR": row["WR"] + rl,
                    "FR": row["FR"] + fb,
                    "OR": row["OR"] + rl,
                    "WL": row["WL"] - rl,
                    "FL": row["FL"] + fb,
                    "OL": row["OL"] - rl,
                })

            # Contar valores fuera de límite
            total_off = 0
            for col in cols:
                lim = lim_map[col]
                total_off += sum(1 for row in modified if row[col] < lim)

            # Validar pared limitante
            if wall and fs is not None and tsw < fs:
                stop_idx = wall_stop - 1  # convertir a índice 0-based
                if 0 <= stop_idx < len(modified):
                    stop_row = modified[stop_idx]
                    if wall_side == "R" and stop_row["OR"] < lim_map["OR"]:
                        continue
                    if wall_side == "L" and stop_row["OL"] < lim_map["OL"]:
                        continue

            # Guardar si es mejor
            if best is None or total_off < best["total_off"]:
                best = {
                    "rl": rl,
                    "fb": fb,
                    "total_off": total_off,
                    "matrix": modified,
                }

    return best
