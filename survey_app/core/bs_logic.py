"""
Lógica BSR vs BS — encuentra el paso (step) en el que la suma triangular
de incrementos (paso 0.5 mm) supera la diferencia BS − BSR.

Tres rangos consecutivos:
  Rango 1 — ZB:       val ∈ [0,                 LIMIT_ZB]
  Rango 2 — OB:       val ∈ [LIMIT_ZB,          LIMIT_ZB + LIMIT_OB]
  Rango 3 — Extended: val ∈ [LIMIT_ZB + LIMIT_OB, 1000]
"""
from typing import Optional

STEP_SIZE  = 0.5
RANGE3_MAX = 1000.0


def _scan_range(dif_bs_initial: float, start: float, end: float,
                range_name: str, range_label: str,
                original_dif: float) -> Optional[dict]:
    """
    Barre desde `start` hasta `end` (paso STEP_SIZE).
    Resta cada `val` al `dif_bs` acumulado.  Cuando dif_bs ≤ 0,
    devuelve el dict con el step encontrado.  Si no encuentra, retorna None.
    """
    dif_bs = dif_bs_initial
    val    = start
    while val <= end:
        dif_bs -= val
        if dif_bs <= 0:
            return {
                "needed":       True,
                "step":         val,
                "range":        range_label,
                "range_name":   range_name,
                "dif_original": original_dif,
            }
        val += STEP_SIZE
    return None


def find_bs_step(bsr: float, bs: float, limit_zb: float, limit_ob: float) -> dict:
    """
    Si BSR ≥ BS no hay ajuste.
    Si BSR < BS busca el step en los 3 rangos consecutivos.
    """
    if bsr >= bs:
        return {"needed": False}

    dif_bs = bs - bsr

    # Rangos consecutivos
    ranges = [
        (0.0,                 limit_zb,                 "ZB",       f"[0, {limit_zb}]"),
        (limit_zb,            limit_zb + limit_ob,      "OB",       f"[{limit_zb}, {limit_zb + limit_ob}]"),
        (limit_zb + limit_ob, RANGE3_MAX,               "Extended", f"[{limit_zb + limit_ob}, {RANGE3_MAX:.0f}]"),
    ]
    for start, end, name, label in ranges:
        result = _scan_range(dif_bs, start, end, name, label, dif_bs)
        if result is not None:
            return result

    return {
        "needed":       True,
        "step":         None,
        "range":        "Not found in any range",
        "dif_original": dif_bs,
    }
