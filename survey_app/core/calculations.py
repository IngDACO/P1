def calculate_limits(p: dict) -> dict:
    """
    Calcula todos los límites y valores derivados.
    p = diccionario con todos los parámetros del proyecto.
    """
    c = {}

    c["LIMIT_WR"] = p["SF2"] + (p["RAIL"] / 2)
    c["LIMIT_FR"] = p["TKSW"] - 150
    c["LIMIT_OR"] = (p["BT"] / 2) + p["FRAME"]
    c["LIMIT_WL"] = p["SF1"] + (p["RAIL"] / 2)
    c["LIMIT_FL"] = p["TKSW"] - 150
    c["LIMIT_OL"] = (p["BT"] / 2) + p["FRAME"]

    limit_ob_raw = (p["SG"] - (p["TG"] / 2)) * 0.3
    limit_zb_raw = p["SF2"] * 0.3

    # Asignar según lado del omega
    if p["OMEGA_SIDE"] == "R":
        c["LIMIT_OB"] = c["LIMIT_OR"]   # lado R
        c["LIMIT_ZB"] = c["LIMIT_OL"]   # lado L
        c["LIMIT_R"]  = limit_ob_raw
        c["LIMIT_L"]  = limit_zb_raw
    else:
        c["LIMIT_OB"] = c["LIMIT_OL"]   # lado L
        c["LIMIT_ZB"] = c["LIMIT_OR"]   # lado R
        c["LIMIT_R"]  = limit_zb_raw
        c["LIMIT_L"]  = limit_ob_raw

    # Offsets
    c["Offset_FR"] = c["LIMIT_FR"] - p["FRT"]
    c["Offset_FL"] = c["LIMIT_FL"] - p["FLT"]
    c["Offset_WR"] = c["LIMIT_WR"] - p["WRT"] + ((p["BSR"] - p["BS"]) / 2)
    c["Offset_WL"] = c["LIMIT_WL"] - p["WLT"] + ((p["BSR"] - p["BS"]) / 2)

    # Dimensiones de cabina
    c["CS"]   = p["TK"] + p["TKA"]
    c["TL"]   = c["CS"] + p["TKS"] + p["TSW"]
    c["TLBC"] = c["TL"] + p["BC"]

    return c


def apply_offsets(survey: list, offsets: dict) -> list:
    """
    Ajusta la matriz SURVEY aplicando los offsets.
    survey: lista de dicts con keys WR, FR, OR, WL, FL, OL
    """
    adjusted = []
    for row in survey:
        adjusted.append({
            "WR": row["WR"] + offsets["Offset_WR"],
            "FR": row["FR"] + offsets["Offset_FR"],
            "OR": row["OR"],
            "WL": row["WL"] + offsets["Offset_WL"],
            "FL": row["FL"] + offsets["Offset_FL"],
            "OL": row["OL"],
        })
    return adjusted


def analyze_matrix(survey: list, limits: dict) -> dict:
    """
    Analiza la matriz ajustada contra los límites.
    Retorna off-counts, mínimos y diferencias.
    """
    cols   = ["WR", "FR", "OR", "WL", "FL", "OL"]
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
        values   = [row[col] for row in survey]
        lim      = lim_map[col]
        off_vals = [v for v in values if v < lim]
        min_val  = min(values)
        result[f"{col}_OFF_COUNT"] = len(off_vals)
        result[f"MIN_{col}"]       = min_val
        result[f"DIF_{col}"]       = lim - min_val

    result["MAX_OFF_RL"] = max(
        result["DIF_WR"], result["DIF_OR"],
        result["DIF_WL"], result["DIF_OL"]
    )
    result["MAX_OFF_FB"] = max(result["DIF_FR"], result["DIF_FL"])

    return result
