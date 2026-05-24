"""
Cálculos geométricos del survey:
  - calculate_limits(): límites laterales, frontales, Omega/Z, restricción FB atrás
  - apply_offsets(): ajusta la matriz survey con los offsets calculados
  - analyze_matrix(): cuenta violaciones, MIN/MAX/DIF por columna
  - validate_inputs(): validación previa de parámetros (opcional)
"""


def validate_inputs(p: dict) -> list:
    """
    Devuelve una lista de strings con problemas encontrados en los parámetros.
    Lista vacía = todo bien.  El llamador decide si avisar o detener.
    """
    issues = []
    required_positive = ["BKS", "TKSW", "TS", "TK", "SF1", "SF2", "RAIL"]
    for k in required_positive:
        v = p.get(k)
        if v is None or float(v) <= 0:
            issues.append(f"{k} debe ser > 0 (actual: {v})")
    # BSR debería estar definido (puede igualar BS)
    if p.get("BSR") is None or float(p.get("BSR", 0)) <= 0:
        issues.append("BSR debe estar definido y > 0")
    # FS debería ser ≥ TSW para que tenga sentido la lógica de pared
    fs, tsw = p.get("FS"), p.get("TSW")
    if fs is not None and tsw is not None and float(fs) < float(tsw):
        issues.append(f"FS ({fs}) < TSW ({tsw}): no hay espacio frontal de seguridad")
    return issues


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
    # Máximo desplazamiento FB hacia atrás permitido.
    # Si DIF_TSW_FS > BC_CALC, la cabina ya consumió todo el espacio trasero
    # disponible (FS está más adelante de lo que cabe), → no se puede mover más atrás.
    if dif_tsw_fs > c["BC_CALC"] or c["BC_CALC"] <= 0:
        c["FB_MAX_BACK"] = 0.0
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
    WR → Offset_WR (suma)         OR → Offset_OR  (resta)
    FR → Offset_FR (suma)         FL → Offset_FL  (suma)
    WL → Offset_WL (suma)         OL → Offset_OL  (resta)
    """
    return [{
        "WR": row["WR"] + offsets["Offset_WR"],
        "FR": row["FR"] + offsets["Offset_FR"],
        "OR": row["OR"] - offsets["Offset_OR"],
        "WL": row["WL"] + offsets["Offset_WL"],
        "FL": row["FL"] + offsets["Offset_FL"],
        "OL": row["OL"] - offsets["Offset_OL"],
    } for row in survey]


def analyze_matrix(survey: list, limits: dict, wall_limiting: bool = True) -> dict:
    """
    Analiza la matriz ajustada contra los límites.
    Retorna off-counts, mínimos, máximos y diferencias por columna.

    Convención de signos:
      WR, FR, WL, FL → DIF = LIMIT − MIN  (positivo = bajo límite = requiere corrección)
      OR, OL         → DIF = MAX − LIMIT  (positivo = supera límite = requiere corte)

    MAX_OFF_RL define el rango de barrido del optimizador. Incluye:
      - DIF_WR y DIF_WL siempre
      - DIF_OR y DIF_OL solo cuando wall_limiting=True (porque solo en Caso 1
        cuentan como violación; en Caso 2 son informativos)
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
            # OR/OL: fuera de límite = v > lim (supera límite → requiere corte)
            # DIF = MAX − LIMIT: positivo = el máximo supera el límite
            result[f"{col}_OFF_COUNT"] = sum(1 for v in values if v > lim)
            result[f"DIF_{col}"]       = max_val - lim
        else:
            # WR, FR, WL, FL: fuera de límite = v < lim (bajo el mínimo requerido)
            # DIF = LIMIT − MIN: positivo = el peor valor está bajo el límite
            result[f"{col}_OFF_COUNT"] = sum(1 for v in values if v < lim)
            result[f"DIF_{col}"]       = lim - min_val

    # ── MAX_OFF_RL: rango del barrido lateral ────────────────────
    # En Caso 1 (wall_limiting=True): OR/OL cuentan como OFF → DIF_OR/OL aportan
    # En Caso 2 (wall_limiting=False): OR/OL no cuentan → solo WR/WL definen el rango
    base_rl = [result["DIF_WR"], result["DIF_WL"]]
    if wall_limiting:
        base_rl += [max(0.0, result["DIF_OR"]), max(0.0, result["DIF_OL"])]
    result["MAX_OFF_RL"] = max(base_rl)
    result["MAX_OFF_FB"] = max(result["DIF_FR"], result["DIF_FL"])

    return result
