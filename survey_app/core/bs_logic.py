def find_bs_step(bsr: float, bs: float, limit_zb: float, limit_ob: float) -> dict:
    """
    Lógica BSR vs BS:
    Encuentra el paso en el que DIF_BS llega a 0.
    """
    if bsr >= bs:
        return {"needed": False}

    dif_bs = bs - bsr
    original_dif = dif_bs

    # Rango 1: [0, LIMIT_ZB]
    step = 0.0
    val = 0.0
    while val <= limit_zb:
        dif_bs -= val
        if dif_bs <= 0:
            return {
                "needed": True,
                "step": val,
                "range": f"[0, {limit_zb}]",
                "range_name": "ZB",
                "dif_original": original_dif
            }
        val += 0.5

    # Rango 2: [LIMIT_ZB, LIMIT_ZB + LIMIT_OB]
    dif_bs = original_dif  # reiniciar
    val = limit_zb
    while val <= limit_zb + limit_ob:
        dif_bs -= val
        if dif_bs <= 0:
            return {
                "needed": True,
                "step": val,
                "range": f"[{limit_zb}, {limit_zb + limit_ob}]",
                "range_name": "OB",
                "dif_original": original_dif
            }
        val += 0.5

    # Rango 3: [LIMIT_ZB + LIMIT_OB, 1000]
    dif_bs = original_dif
    val = limit_zb + limit_ob
    while val <= 1000:
        dif_bs -= val
        if dif_bs <= 0:
            return {
                "needed": True,
                "step": val,
                "range": f"[{limit_zb + limit_ob}, 1000]",
                "range_name": "Extended",
                "dif_original": original_dif
            }
        val += 0.5

    return {
        "needed": True,
        "step": None,
        "range": "Not found in any range",
        "dif_original": original_dif
    }
