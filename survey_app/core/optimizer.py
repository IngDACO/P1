"""
Optimizador de posición del elevador.
Retorna TODAS las combinaciones óptimas (mismo mínimo de valores fuera de límite)
y un log detallado de cada paso evaluado.
"""
import numpy as np


def optimize(survey_adjusted: list, limits: dict, params: dict) -> dict:
    # Parámetros de pared — se leen primero para definir columnas activas
    wall      = params.get("WALL_LIMITING", False)
    wall_stop = params.get("WALL_STOP", None)
    wall_side = params.get("WALL_SIDE", None)
    tsw       = params.get("TSW", 0)
    fs        = params.get("FS", None)

    # Columnas y límites activos: OR/OL solo cuando hay pared limitante
    if wall:
        cols    = ["WR", "FR", "OR", "WL", "FL", "OL"]
        lim_map = {
            "WR": limits["LIMIT_WR"], "FR": limits["LIMIT_FR"],
            "OR": limits["LIMIT_OR"], "WL": limits["LIMIT_WL"],
            "FL": limits["LIMIT_FL"], "OL": limits["LIMIT_OL"],
        }
    else:
        cols    = ["WR", "FR", "WL", "FL"]
        lim_map = {
            "WR": limits["LIMIT_WR"], "FR": limits["LIMIT_FR"],
            "WL": limits["LIMIT_WL"], "FL": limits["LIMIT_FL"],
        }

    # lim_map completo para chequeos de pared (OR/OL siempre disponibles)
    full_lim_map = {
        "WR": limits["LIMIT_WR"], "FR": limits["LIMIT_FR"],
        "OR": limits["LIMIT_OR"], "WL": limits["LIMIT_WL"],
        "FL": limits["LIMIT_FL"], "OL": limits["LIMIT_OL"],
    }

    max_rl   = limits["MAX_OFF_RL"]
    max_fb   = limits["MAX_OFF_FB"]
    rl_steps = np.arange(-max_rl, max_rl + 0.5, 0.5)
    fb_steps = np.arange(-max_fb, max_fb + 0.5, 0.5)

    # ── Restricción FB hacia atrás ───────────────────────────────────
    fb_max_back = limits.get("FB_MAX_BACK", float("inf"))

    # ── Controlador en el frame ──────────────────────────────────────
    ctrl_in_frame = params.get("CTRL_IN_FRAME", False)
    ctrl_side     = params.get("CTRL_SIDE", None)
    last_row_idx  = len(survey_adjusted) - 1
    full_lim_or   = limits.get("LIMIT_OR", 0)
    full_lim_ol   = limits.get("LIMIT_OL", 0)

    limit_r = limits.get("LIMIT_R", max_rl)
    limit_l = limits.get("LIMIT_L", max_rl)

    best_total_off = None
    best_solutions = []
    step_log       = []

    # ── Helper: aplica desplazamientos (rl_, fb_) a survey_adjusted ──
    def _apply(rl_, fb_):
        return [{
            "WR": row["WR"] + rl_,
            "FR": row["FR"] + fb_,
            "OR": row["OR"] - rl_,   # rl>0 → resta OR  / rl<0 → suma OR
            "WL": row["WL"] - rl_,
            "FL": row["FL"] + fb_,
            "OL": row["OL"] + rl_,   # rl>0 → suma OL  / rl<0 → resta OL
        } for row in survey_adjusted]

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

        # Dirección hacia la pared (se evalúa por cada rl, fuera del loop fb)
        toward_wall = (
            wall and wall_stop is not None and wall_side is not None and
            ((wall_side == "R" and rl < 0) or (wall_side == "L" and rl > 0))
        )

        for fb in fb_steps:
            # Validar límite FB hacia atrás
            if fb > fb_max_back:
                step_log.append({
                    "rl": float(rl), "fb": float(fb), "status": "SKIP",
                    "reason": f"FB={fb:.1f} > FB_MAX_BACK={fb_max_back:.1f}",
                    "total_off": None, "off_by_col": {}, "min_by_col": {},
                })
                continue

            # ── Paso 1: desplazamientos iniciales ────────────────────
            modified   = _apply(rl, fb)
            fb_applied = fb

            # ── Paso 2: FB extra si RL va hacia la pared ─────────────
            # Condiciones:
            #   a) RL apunta hacia el lado de la pared
            #   b) OR/OL en el nivel crítico (WALL_STOP) supera el límite (fuera de límite)
            #   c) FS > TSW  →  hay espacio extra disponible hacia atrás
            # → fb_applied = min(fb + (FS − TSW), FB_MAX_BACK)
            if toward_wall:
                stop_idx  = int(wall_stop) - 1
                check_col = "OR" if wall_side == "R" else "OL"
                if 0 <= stop_idx < len(modified):
                    if modified[stop_idx][check_col] > full_lim_map[check_col]:
                        # OR/OL supera límite → intentar FB extra para esquivar la pared
                        if fs is not None and fs > tsw:
                            extra      = fs - tsw
                            fb_applied = min(fb + extra, fb_max_back)
                            modified   = _apply(rl, fb_applied)

            # ── Paso 3: contar valores fuera de límite ────────────────
            # WR/WL/FR/FL: fuera de límite = v < lim  (clearance insuficiente)
            # OR/OL:        fuera de límite = v > lim  (dimensión supera máximo → requiere corte)
            off_by_col = {}
            min_by_col = {}
            total_off  = 0
            for col in cols:
                lim      = lim_map[col]
                col_vals = [r[col] for r in modified]
                off      = 0
                for row_idx, v in enumerate(col_vals):
                    eff_lim = lim
                    if ctrl_in_frame and row_idx == last_row_idx:
                        if col == "OR" and ctrl_side == "R":
                            eff_lim = lim - 70
                        elif col == "OL" and ctrl_side == "L":
                            eff_lim = lim - 70
                    if col in ("OR", "OL"):
                        if v > eff_lim:
                            off += 1
                    else:
                        if v < eff_lim:
                            off += 1
                off_by_col[col] = off
                total_off      += off
                min_by_col[col] = round(min(col_vals), 2)

            # Caso 2: controlador activo sobre OR/OL (no están en cols)
            if ctrl_in_frame and ctrl_side in ("R", "L"):
                ctrl_col = "OR" if ctrl_side == "R" else "OL"
                if ctrl_col not in cols:
                    ctrl_base_lim = (full_lim_or if ctrl_side == "R" else full_lim_ol) - 70
                    last_v        = modified[last_row_idx][ctrl_col]
                    if last_v > ctrl_base_lim:   # OR/OL: fuera de límite = v > lim
                        off_by_col[ctrl_col] = off_by_col.get(ctrl_col, 0) + 1
                        total_off += 1

            # ── Paso 4: chequeo duro de pared ─────────────────────────
            # Se evalúa sobre el modified final (post-FB extra si aplica).
            # Solo aplica cuando RL va hacia la pared (toward_wall).
            # Si OR/OL en la parada crítica sigue superando el límite → SKIP.
            wall_fail   = False
            wall_reason = ""
            if toward_wall:
                stop_idx = int(wall_stop) - 1
                if 0 <= stop_idx < len(modified):
                    stop_row = modified[stop_idx]
                    if wall_side == "R" and stop_row["OR"] > full_lim_map["OR"]:
                        wall_fail   = True
                        wall_reason = (f"Pared: OR parada {wall_stop}="
                                       f"{stop_row['OR']:.1f} > LIMIT OR={full_lim_map['OR']:.1f}")
                    if wall_side == "L" and stop_row["OL"] > full_lim_map["OL"]:
                        wall_fail   = True
                        wall_reason = (f"Pared: OL parada {wall_stop}="
                                       f"{stop_row['OL']:.1f} > LIMIT OL={full_lim_map['OL']:.1f}")

            log_entry = {
                "rl":          float(rl),
                "fb":          float(fb),
                "fb_applied":  float(fb_applied),   # FB efectivo (puede incluir extra FS-TSW)
                "total_off":   total_off,
                "off_by_col":  off_by_col.copy(),
                "min_by_col":  min_by_col.copy(),
                "wall_fail":   wall_fail,
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
                "fb_applied": float(fb_applied),
                "total_off":  total_off,
                "matrix":     modified,
                "off_by_col": off_by_col.copy(),
                "min_by_col": min_by_col.copy(),
            }

            if best_total_off is None or total_off < best_total_off:
                best_total_off = total_off
                best_solutions = [solution]
            elif total_off == best_total_off:
                best_solutions.append(solution)

    # Desempate: menor desplazamiento total
    if best_solutions:
        best_selected = min(best_solutions, key=lambda s: abs(s["rl"]) + abs(s["fb_applied"]))
    else:
        best_selected = None

    return {
        "best":           best_selected,
        "all_solutions":  best_solutions,
        "step_log":       step_log,
        "best_total_off": best_total_off,
    }
