"""
Optimizador de posición del bloque cabina (rieles + frame).

Retorna TODAS las combinaciones óptimas (mismo mínimo de valores fuera de límite)
y un log detallado de cada paso evaluado.

Flujo en cada paso (rl, fb):
  Paso 1: aplicar desplazamientos iniciales (rl, fb) a la matriz
  Paso 2: si OR/OL en WALL_STOP (del lado del muro) > LIMIT Y FS > TSW, vaya RL hacia donde vaya (v681)
          → aplicar FB extra = FS − TSW (cabina evade el muro físicamente)
          → fb_extra_applied = True
  Paso 2b: si fb_extra_applied Y RL va hacia la pared Y |RL| > FRAME → SKIP
           (apertura de cabina quedaría tapada por la pared limitante)
  Paso 3: contar violaciones (excluye OR/OL del nivel evadido)
  Paso 4: SKIP duro si OR/OL en WALL_STOP > LIMIT y NO se pudo evadir, vaya RL hacia donde vaya (v681)

⚠️ v681 · H3 del ciclo 4, decidido por el usuario: «un muro limitante es aquel que no puede ser cortado… lo único que se
puede hacer es empujar el elevador hacia atrás hasta que esquive el límite físico de esa pared; todos los demás niveles
sí pueden ser cortados» y, cuando el muro YA está fuera en su nivel y la solución se aleja de él sin bastar, «se debe
empujar hacia atrás» (opción a: ninguna solución deja el muro por encima de su límite; para librarlo vale alejarse lo
suficiente o empujar si cabe; si no, se descarta; entre las válidas, la de menos cortes). Hasta v680 los pasos 2 y 4
solo actuaban yendo HACIA el muro: con FS 120 la solución se alejó 18 mm, el muro (436 → 418, límite 401) quedó fuera
sin empujar ni descartar, y el informe pedía cortarlo.
"""
import numpy as np

from core.i18n import t


def optimize(survey_adjusted: list, limits: dict, params: dict) -> dict:
    # ── Parámetros de pared ────────────────────────────────────
    wall      = params.get("WALL_LIMITING", False)
    wall_stop = params.get("WALL_STOP", None)
    wall_side = params.get("WALL_SIDE", None)
    tsw       = params.get("TSW", 0)
    fs        = params.get("FS", None)
    frame     = float(params.get("FRAME", 0))

    # ── Columnas activas según caso ────────────────────────────
    # Caso 1 (wall): OR/OL cuentan como OFF completo
    # Caso 2:        OR/OL no cuentan (se manejan como CUT en la UI/reporte)
    full_lim_map = {
        "WR": limits["LIMIT_WR"], "FR": limits["LIMIT_FR"],
        "OR": limits["LIMIT_OR"], "WL": limits["LIMIT_WL"],
        "FL": limits["LIMIT_FL"], "OL": limits["LIMIT_OL"],
    }
    if wall:
        cols    = ["WR", "FR", "OR", "WL", "FL", "OL"]
        lim_map = dict(full_lim_map)
    else:
        cols    = ["WR", "FR", "WL", "FL"]
        lim_map = {k: full_lim_map[k] for k in cols}

    # ── Rango del barrido ──────────────────────────────────────
    max_rl   = limits["MAX_OFF_RL"]
    max_fb   = limits["MAX_OFF_FB"]
    rl_steps = np.arange(-max_rl, max_rl + 0.5, 0.5)
    fb_steps = np.arange(-max_fb, max_fb + 0.5, 0.5)

    fb_max_back = limits.get("FB_MAX_BACK", float("inf"))

    # ── Controlador en el frame (reduce LIMIT_OR/OL −70 mm en último nivel) ──
    ctrl_in_frame = params.get("CTRL_IN_FRAME", False)
    ctrl_side     = params.get("CTRL_SIDE", None)
    last_row_idx  = len(survey_adjusted) - 1

    # ── Restricciones laterales físicas ────────────────────────
    limit_r = limits.get("LIMIT_R", max_rl)
    limit_l = limits.get("LIMIT_L", max_rl)

    # ── Constantes de muro (no dependen de rl ni fb) ───────────
    wall_active    = bool(wall and wall_stop is not None and wall_side in ("R", "L"))
    wall_stop_idx  = int(wall_stop) - 1 if wall_active else -1
    wall_check_col = ("OR" if wall_side == "R" else "OL") if wall_active else None
    wall_lim_val   = full_lim_map.get(wall_check_col) if wall_check_col else None

    best_total_off = None
    best_solutions = []
    step_log       = []

    # ── Helper: aplicar desplazamientos a survey_adjusted ────
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
        # ── Validar rango RL contra LIMIT_R / LIMIT_L (físico) ──
        if rl < 0 and abs(rl) > limit_r:
            step_log.append({
                "rl": float(rl), "fb": None, "status": "SKIP",
                "reason": f"|RL|={abs(rl):.1f} > LIMIT R={limit_r:.1f}",
                "skip_type": "physical_rl",
                "total_off": None, "off_by_col": {}, "min_by_col": {}, "max_by_col": {},
            })
            continue
        if rl > 0 and abs(rl) > limit_l:
            step_log.append({
                "rl": float(rl), "fb": None, "status": "SKIP",
                "reason": f"|RL|={abs(rl):.1f} > LIMIT L={limit_l:.1f}",
                "skip_type": "physical_rl",
                "total_off": None, "off_by_col": {}, "min_by_col": {}, "max_by_col": {},
            })
            continue

        # ── Dirección hacia la pared (evalúa una vez por rl) ──
        toward_wall = (
            wall_active and
            ((wall_side == "R" and rl < 0) or (wall_side == "L" and rl > 0))
        )

        for fb in fb_steps:
            # ── Validar FB hacia atrás ──────────────────────────
            if fb > fb_max_back:
                step_log.append({
                    "rl": float(rl), "fb": float(fb), "status": "SKIP",
                    "reason": f"FB={fb:.1f} > FB_MAX_BACK={fb_max_back:.1f}",
                    "skip_type": "physical_fb",
                    "total_off": None, "off_by_col": {}, "min_by_col": {}, "max_by_col": {},
                })
                continue

            # ── Paso 1: desplazamientos iniciales ────────────────
            modified         = _apply(rl, fb)
            fb_applied       = float(fb)
            fb_extra_applied = False

            # ── Paso 2: FB extra si va hacia la pared ────────────
            # Condición: RL implica colisión (OR/OL en WALL_STOP > LIMIT) y FS > TSW.
            # El extra exacto depende de cuánto FR/FL del piso limitante ya supera
            # su propio límite gracias al fb actual del loop:
            #   excess       = FR/FL_piso_limitante − LIMIT_FR/FL   (puede ser negativo)
            #   extra_needed = max(0, FS−TSW − excess)
            # Casos:
            #   1) Piso limitante es el más crítico en FR/FL (excess ≈ 0) → extra completo
            #   2) Otro piso más crítico ya empujó fb; wall_stop lleva ventaja → extra reducido
            #   3) Sin violación FR/FL (fb=0); wall_stop ya está sobre límite → extra reducido
            # Tras la evasión, el nivel WALL_STOP queda fuera del conteo OR/OL.
            # ⚠️ v681 · Vaya RL hacia donde vaya (ver el docstring): el muro no se corta nunca. Y «esquivado» (`wall_evaded`)
            # es un hecho aparte del empuje (`fb_extra_applied`):
            #   - con extra_needed = 0 (el piso del muro ya está FS−TSW o más por detrás de su límite frontal, el caso 3 de
            #     arriba) el muro YA está esquivado sin empujar. Hasta v680 eso no se marcaba y, yendo hacia el muro, se
            #     descartaba como choque; con los datos de PRJ-0045 (FS 120) la regla nueva se quedaba SIN solución.
            #   - si el empuje entero no cabe detrás (FB_MAX_BACK), NO está esquivado: hasta v680 se empujaba lo que cupiera
            #     y se daba por esquivado. El muro no se corta, así que esa solución no vale.
            wall_evaded = False
            if wall_active and 0 <= wall_stop_idx < len(modified):
                if modified[wall_stop_idx][wall_check_col] > wall_lim_val:
                    if fs is not None and fs > tsw:
                        # Columna frontal del lado de la pared (FR si R, FL si L)
                        fb_col     = "FR" if wall_side == "R" else "FL"
                        fb_lim_val = full_lim_map[fb_col]

                        # Valor FR/FL en el piso limitante con el (rl, fb) actual
                        fr_at_wall = modified[wall_stop_idx][fb_col]

                        # Cuánto ya supera el límite frontal en ese piso
                        excess = fr_at_wall - fb_lim_val

                        # Push extra necesario para completar la evasión
                        extra_needed = max(0.0, (fs - tsw) - excess)
                        objetivo     = fb + extra_needed

                        if objetivo <= fb_max_back + 1e-3:
                            wall_evaded = True
                            if objetivo > fb_applied + 1e-3:
                                fb_applied       = float(objetivo)
                                modified         = _apply(rl, fb_applied)
                                fb_extra_applied = True

            # ── Paso 2b: restricción apertura de cabina ──────────
            # Si la cabina evadió la pared (empujando, o ya por detrás de ella: v681) y el RL hacia la pared
            # supera FRAME, la apertura de la cabina queda tapada → SKIP.
            if wall_evaded and toward_wall and frame > 0 and abs(rl) > frame:
                step_log.append({
                    "rl":               float(rl),
                    "fb":               float(fb),
                    "fb_applied":       float(fb_applied),
                    "fb_extra_applied": fb_extra_applied,
                    "wall_evaded":      True,
                    "status":           "SKIP",
                    # v589 · en el idioma base (decía «Apertura tapada»)
                    "reason":           t("Opening covered: |RL|={rl} > FRAME={f}",
                                          rl="%.1f" % abs(rl), f="%.1f" % frame),
                    "skip_type":        "frame_opening",
                    "total_off":        None,
                    "off_by_col":       {},
                    "min_by_col":       {},
                    "max_by_col":       {},
                    "wall_fail":        False,
                    "wall_reason":      "",
                })
                continue

            # ── Paso 3: contar valores fuera de límite ────────────
            off_by_col = {}
            min_by_col = {}
            max_by_col = {}
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
                    # Nivel de pared evadido (con FB extra o ya por detrás, v681) → no contar
                    if wall_evaded and row_idx == wall_stop_idx and col == wall_check_col:
                        continue
                    if col in ("OR", "OL"):
                        if v > eff_lim:
                            off += 1
                    else:
                        if v < eff_lim:
                            off += 1
                off_by_col[col] = off
                total_off      += off
                min_by_col[col] = round(min(col_vals), 2)
                max_by_col[col] = round(max(col_vals), 2)

            # ── Caso 2: controlador activo sobre OR/OL (no están en cols) ──
            if ctrl_in_frame and ctrl_side in ("R", "L"):
                ctrl_col = "OR" if ctrl_side == "R" else "OL"
                if ctrl_col not in cols:
                    ctrl_base_lim = full_lim_map[ctrl_col] - 70
                    last_v        = modified[last_row_idx][ctrl_col]
                    if last_v > ctrl_base_lim:
                        off_by_col[ctrl_col] = off_by_col.get(ctrl_col, 0) + 1
                        total_off += 1

            # ── Paso 4: chequeo duro de pared ────────────────────
            # SKIP si OR/OL > LIMIT en la parada del muro y NO se pudo evadir: alejándose tampoco vale dejarlo fuera
            # (v681: hasta entonces solo yendo HACIA la pared, y el informe pedía cortar el muro).
            wall_fail   = False
            wall_reason = ""
            if wall_active and not wall_evaded and 0 <= wall_stop_idx < len(modified):
                stop_row = modified[wall_stop_idx]
                if wall_side == "R" and stop_row["OR"] > full_lim_map["OR"]:
                    wall_fail   = True
                    wall_reason = t("Wall: OR at stop {s} = {v} > LIMIT OR = {l}", s=wall_stop,
                                    v="%.1f" % stop_row["OR"], l="%.1f" % full_lim_map["OR"])
                if wall_side == "L" and stop_row["OL"] > full_lim_map["OL"]:
                    wall_fail   = True
                    wall_reason = t("Wall: OL at stop {s} = {v} > LIMIT OL = {l}", s=wall_stop,
                                    v="%.1f" % stop_row["OL"], l="%.1f" % full_lim_map["OL"])

            log_entry = {
                "rl":               float(rl),
                "fb":               float(fb),
                "fb_applied":       float(fb_applied),
                "fb_extra_applied": fb_extra_applied,
                "wall_evaded":      wall_evaded,
                "total_off":        total_off,
                "off_by_col":       off_by_col.copy(),
                "min_by_col":       min_by_col.copy(),
                "max_by_col":       max_by_col.copy(),
                "wall_fail":        wall_fail,
                "wall_reason":      wall_reason,
            }

            if wall_fail:
                log_entry["status"]    = "SKIP"
                log_entry["reason"]    = wall_reason
                log_entry["skip_type"] = "wall"
                step_log.append(log_entry)
                continue

            log_entry["status"]    = "VALID"
            log_entry["reason"]    = ""
            log_entry["skip_type"] = None
            step_log.append(log_entry)

            solution = {
                "rl":               float(rl),
                "fb":               float(fb),
                "fb_applied":       float(fb_applied),
                "fb_extra_applied": fb_extra_applied,
                "wall_evaded":      wall_evaded,
                "total_off":        total_off,
                "matrix":           modified,
                "off_by_col":       off_by_col.copy(),
                "min_by_col":       min_by_col.copy(),
                "max_by_col":       max_by_col.copy(),
            }

            if best_total_off is None or total_off < best_total_off:
                best_total_off = total_off
                best_solutions = [solution]
            elif total_off == best_total_off:
                best_solutions.append(solution)

    # ── Equivalentes: misma posición (rl, fb APLICADO) = la misma matriz ──
    # ⚠️ v682 · Visto verificando v681 en producción: con el empuje extra del muro, varios fb del barrido acaban en el
    # MISMO fb aplicado, y PRJ-0045 (FS 140) daba «143 optimal solutions» que eran 11 posiciones repetidas 13 veces. El
    # selector de la solución activa tenía etiquetas idénticas y saltaba de una a otra, y la parte «extra» del empuje
    # (19 o 13 mm) cambiaba sin que la cabina se moviera. Se queda UNA por posición: la de mayor fb del barrido (el
    # empuje extra mínimo que hace falta), en el orden de siempre.
    _una = {}
    for s in best_solutions:
        k = (round(s["rl"], 3), round(s["fb_applied"], 3))
        if k not in _una or s["fb"] > _una[k]["fb"]:
            _una[k] = s
    best_solutions = [s for s in best_solutions if _una[(round(s["rl"], 3), round(s["fb_applied"], 3))] is s]

    # ── Desempate: menor desplazamiento total |rl| + |fb_applied| ──
    if best_solutions:
        best_selected = min(
            best_solutions,
            key=lambda s: abs(s["rl"]) + abs(s["fb_applied"])
        )
    else:
        best_selected = None

    return {
        "best":           best_selected,
        "all_solutions":  best_solutions,
        "step_log":       step_log,
        "best_total_off": best_total_off,
    }
