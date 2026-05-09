"""
Optimizador de posición del elevador.
Retorna TODAS las combinaciones óptimas (mismo mínimo de valores fuera de límite)
y un log detallado de cada paso evaluado.
"""
import numpy as np


def optimize(survey_adjusted: list, limits: dict, params: dict) -> dict:
    cols    = ["WR", "FR", "OR", "WL", "FL", "OL"]
    lim_map = {
        "WR": limits["LIMIT_WR"], "FR": limits["LIMIT_FR"],
        "OR": limits["LIMIT_OR"], "WL": limits["LIMIT_WL"],
        "FL": limits["LIMIT_FL"], "OL": limits["LIMIT_OL"],
    }

    max_rl  = limits["MAX_OFF_RL"]
    max_fb  = limits["MAX_OFF_FB"]
    rl_steps = np.arange(-max_rl, max_rl + 0.5, 0.5)
    fb_steps = np.arange(-max_fb, max_fb + 0.5, 0.5)

    limit_r = limits.get("LIMIT_R", max_rl)
    limit_l = limits.get("LIMIT_L", max_rl)

    wall      = params.get("WALL_LIMITING", False)
    wall_stop = params.get("WALL_STOP", None)
    wall_side = params.get("WALL_SIDE", None)
    tsw       = params.get("TSW", 0)
    fs        = params.get("FS", None)

    best_total_off = None   # mínimo encontrado hasta ahora
    best_solutions = []     # TODAS las soluciones con ese mínimo
    step_log       = []

    for rl in rl_steps:
        # Validar rango RL
        if rl < 0 and abs(rl) > limit_r:
            step_log.append({
                "rl": float(rl), "fb": None, "status": "SKIP",
                "reason": f"|RL|={abs(rl):.1f} > LIMIT R={limit_r:.1f}",
                "total_off": None, "off_by_col": {}, "min_by_col": {},
            })
            continue
        if rl > 0 and abs(rl) > limit_l:
            step_log.append({
                "rl": float(rl), "fb": None, "status": "SKIP",
                "reason": f"|RL|={abs(rl):.1f} > LIMIT L={limit_l:.1f}",
                "total_off": None, "off_by_col": {}, "min_by_col": {},
            })
            continue

        for fb in fb_steps:
            # Aplicar desplazamientos
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
            off_by_col = {}
            min_by_col = {}
            total_off  = 0
            for col in cols:
                lim          = lim_map[col]
                col_vals     = [r[col] for r in modified]
                off          = sum(1 for v in col_vals if v < lim)
                off_by_col[col] = off
                total_off      += off
                min_by_col[col] = round(min(col_vals), 2)

            # Validar pared limitante
            wall_fail   = False
            wall_reason = ""
            if wall and fs is not None and tsw < fs:
                stop_idx = int(wall_stop) - 1
                if 0 <= stop_idx < len(modified):
                    stop_row = modified[stop_idx]
                    if wall_side == "R" and stop_row["OR"] < lim_map["OR"]:
                        wall_fail   = True
                        wall_reason = (f"Pared: OR parada {wall_stop}="
                                       f"{stop_row['OR']:.1f} < LIMIT OR={lim_map['OR']:.1f}")
                    if wall_side == "L" and stop_row["OL"] < lim_map["OL"]:
                        wall_fail   = True
                        wall_reason = (f"Pared: OL parada {wall_stop}="
                                       f"{stop_row['OL']:.1f} < LIMIT OL={lim_map['OL']:.1f}")

            log_entry = {
                "rl":         float(rl),
                "fb":         float(fb),
                "total_off":  total_off,
                "off_by_col": off_by_col.copy(),
                "min_by_col": min_by_col.copy(),
                "wall_fail":  wall_fail,
                "wall_reason": wall_reason,
            }

            if wall_fail:
                log_entry["status"] = "SKIP"
                log_entry["reason"] = wall_reason
                step_log.append(log_entry)
                continue

            log_entry["status"] = "VALID"
            log_entry["reason"] = ""
            step_log.append(log_entry)

            solution = {
                "rl":         float(rl),
                "fb":         float(fb),
                "total_off":  total_off,
                "matrix":     modified,
                "off_by_col": off_by_col.copy(),
                "min_by_col": min_by_col.copy(),
            }

            # ── Guardar todas las soluciones óptimas ──
            if best_total_off is None or total_off < best_total_off:
                # Nuevo mínimo: reiniciar lista de soluciones
                best_total_off = total_off
                best_solutions = [solution]
            elif total_off == best_total_off:
                # Mismo mínimo: agregar a la lista
                best_solutions.append(solution)

    return {
        "best":           best_solutions[0] if best_solutions else None,
        "all_solutions":  best_solutions,
        "step_log":       step_log,
        "best_total_off": best_total_off,
    }
