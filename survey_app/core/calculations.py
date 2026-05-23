def calculate_limits(p: dict) -> dict:
    """
    Calcula todos los límites y valores derivados.
    p = diccionario con todos los parámetros del proyecto.
    """
    c = {}

    c["LIMIT_WR"] = p["SF2"] + (p["RAIL"] / 2)
    c["LIMIT_FR"] = p["TKSW"] - 150
    c["LIMIT_WL"] = p["SF1"] + (p["RAIL"] / 2)
    c["LIMIT_FL"] = p["TKSW"] - 150

    # ── LIMIT OR / LIMIT OL — basados en geometría de cabina ────────
    # Base común = (BKS/2) + (RAIL/2) - (BT/2) - FRAME
    # Lado offset L → LIMIT OR = base + OFFSET_CABIN  /  LIMIT OL = base - OFFSET_CABIN
    # Lado offset R → LIMIT OR = base - OFFSET_CABIN  /  LIMIT OL = base + OFFSET_CABIN
    _base_or_ol = (p["BKS"] / 2) + (p["RAIL"] / 2) - (p["BT"] / 2) - p["FRAME"]
    if p.get("OFFSET_SIDE", "R") == "L":
        c["LIMIT_OR"] = _base_or_ol + p["OFFSET_CABIN"]
        c["LIMIT_OL"] = _base_or_ol - p["OFFSET_CABIN"]
    else:  # R
        c["LIMIT_OR"] = _base_or_ol - p["OFFSET_CABIN"]
        c["LIMIT_OL"] = _base_or_ol + p["OFFSET_CABIN"]

    # ── LIMIT OB y LIMIT ZB ──────────────────────────────────────
    # OB está del lado del Omega.
    # Z siempre está del lado OPUESTO al Omega.
    # LIMIT ZB depende del lado donde está el Z:
    #   Z del lado R (Omega=L) → LIMIT ZB = SF2 × 0.3
    #   Z del lado L (Omega=R) → LIMIT ZB = SF1 × 0.3
    limit_ob_raw = (p["SG"] - (p["TG"] / 2)) * 0.3

    if p["OMEGA_SIDE"] == "R":
        # Omega en R  →  Z en L  →  LIMIT ZB usa SF1
        limit_zb_raw     = p["SF1"] * 0.3
        c["LIMIT_OB"]    = c["LIMIT_OR"]   # Omega lado R
        c["LIMIT_ZB"]    = c["LIMIT_OL"]   # Z lado L
        c["LIMIT_R"]     = limit_ob_raw
        c["LIMIT_L"]     = limit_zb_raw
        c["Z_SIDE"]      = "L"
    else:
        # Omega en L  →  Z en R  →  LIMIT ZB usa SF2
        limit_zb_raw     = p["SF2"] * 0.3
        c["LIMIT_OB"]    = c["LIMIT_OL"]   # Omega lado L
        c["LIMIT_ZB"]    = c["LIMIT_OR"]   # Z lado R
        c["LIMIT_R"]     = limit_zb_raw
        c["LIMIT_L"]     = limit_ob_raw
        c["Z_SIDE"]      = "R"

    c["LIMIT_OB_RAW"] = limit_ob_raw
    c["LIMIT_ZB_RAW"] = limit_zb_raw

    # ── Offsets ──────────────────────────────────────────────────
    c["Offset_FR"] = c["LIMIT_FR"] - p["FRT"]
    c["Offset_FL"] = c["LIMIT_FL"] - p["FLT"]
    c["Offset_WR"] = c["LIMIT_WR"] - p["WRT"] + ((p["BSR"] - p["BS"]) / 2)
    c["Offset_WL"] = c["LIMIT_WL"] - p["WLT"] + ((p["BSR"] - p["BS"]) / 2)
    # OR y OL reciben el mismo offset lateral que WR y WL
    c["Offset_OR"] = c["Offset_WR"]
    c["Offset_OL"] = c["Offset_WL"]

    # ── Restricción FB hacia atrás ────────────────────────────────
    # BC_CALC = espacio libre detrás de la cabina (fondo del hueco)
    #   TS      = profundidad total del hueco
    #   TKSW    = pared frontal → eje de rieles
    #   TK/2    = eje de rieles → fondo de cabina
    #   25      = holgura mínima de seguridad
    c["BC_CALC"]    = p["TS"] - p["TKSW"] - (p["TK"] / 2) - 25
    # DIF_TSW_FS: cuánto supera FS al valor de plano TSW
    dif_tsw_fs      = p.get("FS", 0.0) - p.get("TSW", 0.0)
    c["DIF_TSW_FS"] = dif_tsw_fs
    # Máximo desplazamiento FB hacia atrás permitido
    if dif_tsw_fs > c["BC_CALC"] or c["BC_CALC"] <= 0:
        c["FB_MAX_BACK"] = 0.0   # no se puede desplazar hacia atrás
    else:
        c["FB_MAX_BACK"] = float(c["BC_CALC"])

    # ── Dimensiones de cabina ────────────────────────────────────
    c["CS"]   = p["TK"] + p["TKA"]
    c["TL"]   = c["CS"] + p["TKS"] + p["TSW"]
    c["TLBC"] = c["TL"] + c["BC_CALC"]

    return c


def apply_offsets(survey: list, offsets: dict) -> list:
    """
    Ajusta la matriz SURVEY aplicando los offsets.
    WR → Offset_WR
    FR → Offset_FR
    OR → Offset_OR  (= Offset_WR)
    WL → Offset_WL
    FL → Offset_FL
    OL → Offset_OL  (= Offset_WL)
    """
    adjusted = []
    for row in survey:
        adjusted.append({
            "WR": row["WR"] + offsets["Offset_WR"],
            "FR": row["FR"] + offsets["Offset_FR"],
            "OR": row["OR"] - offsets["Offset_OR"],
            "WL": row["WL"] + offsets["Offset_WL"],
            "FL": row["FL"] + offsets["Offset_FL"],
            "OL": row["OL"] - offsets["Offset_OL"],
        })
    return adjusted


def analyze_matrix(survey: list, limits: dict, wall_limiting: bool = True) -> dict:
    """
    Analiza la matriz ajustada contra los límites.
    Retorna off-counts, mínimos y diferencias.

    Convención de signos:
      WR, FR, WL, FL → DIF = LIMIT − MIN  (positivo = bajo límite = requiere corrección)
      OR, OL         → DIF = MIN − LIMIT  (positivo = supera límite = requiere corte;
                                            negativo = bajo límite = sin violación)
    MAX_OFF_RL = max(DIF_WR, DIF_WL) en ambos casos.
      OR/OL no aportan: en Caso 1 su DIF es negativo y la restricción se
      maneja como SKIP duro en el optimizador; en Caso 2 ya estaban excluidos.
    """
    cols    = ["WR", "FR", "OR", "WL", "FL", "OL"]
    lim_map = {
        "WR": limits["LIMIT_WR"],
        "FR": limits["LIMIT_FR"],
        "OR": limits["LIMIT_OR"],
        "WL": limits["LIMIT_WL"],
        "FL": limits["LIMIT_FL"],
        "OL": limits["LIMIT_OL"],
    }

    result = {}
    for col in cols:
        values  = [row[col] for row in survey]
        lim     = lim_map[col]
        min_val = min(values)
        max_val = max(values)
        result[f"MIN_{col}"] = min_val
        result[f"MAX_{col}"] = max_val
        if col in ("OR", "OL"):
            # OR/OL: fuera de límite = v > lim (supera el límite → requiere corte)
            # DIF = MAX − LIMIT: positivo = el máximo supera el límite (cut needed)
            #                    negativo = el máximo está bajo el límite (sin violación)
            result[f"{col}_OFF_COUNT"] = sum(1 for v in values if v > lim)
            result[f"DIF_{col}"]       = max_val - lim
        else:
            # WR, FR, WL, FL: fuera de límite = v < lim (bajo el mínimo requerido)
            # DIF = LIMIT − MIN: positivo = el peor valor está bajo el límite
            result[f"{col}_OFF_COUNT"] = sum(1 for v in values if v < lim)
            result[f"DIF_{col}"]       = lim - min_val

    result["MAX_OFF_RL"] = max(
        result["DIF_WR"],
        result["DIF_WL"],
        max(0.0, result["DIF_OR"]),   # OR sobre límite → necesita rl > 0
        max(0.0, result["DIF_OL"]),   # OL sobre límite → necesita rl < 0
    )
    result["MAX_OFF_FB"] = max(result["DIF_FR"], result["DIF_FL"])

    return result
