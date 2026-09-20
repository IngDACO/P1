# -*- coding: utf-8 -*-
"""Un proyecto CON survey, construido, para los guardianes de informes.

⚠️ Existe porque v456 vació la demo y tres guardianes —los dos informes y el smoke de
`report`— pasaron a salir SIN DATOS: sus afirmaciones llevaban versiones sin
comprobarse. El caso se construye una sola vez y aquí, no copiado en los tres (la
lección de los cinco `_num` divergentes de v323).

⚠️ Y no son números al azar: la geometría es COHERENTE con lo que documenta CLAUDE.md,
porque el cálculo la rechaza si no lo es —lo comprobé a base de que `recalcular`
devolviera `None`—:
  · `BS = SF1 + BKS + 2·RAIL + SF2` (si no cuadra, el encaje del plomado miente);
  · `FS − TSW ≤ BC_CALC`, o no hay hueco por detrás y todo paso se descarta;
  · y **los pisos tienen que DIFERIR entre sí**: `apply_offsets` normaliza contra la
    ÚLTIMA fila, así que con todos iguales `MAX_OFF_RL` sale ≤ 0, el barrido del
    optimizador queda VACÍO y no hay solución que informar. Un survey con todos los
    pisos idénticos no ejercita nada.
"""
import json

SF1 = SF2 = 51.0
BKS = 1100.0
RAIL = 62.0
BS = SF1 + BKS + 2 * RAIL + SF2          # 1326.0

PARAMS = {
    # los 17 del plano
    "TKSW": 965.0, "BKS": BKS, "TKA": 25.0, "TKS": 30.0, "TSW": 70.0, "BGS": 100.0,
    "BKF1": 170.0, "BKF2": 170.0, "BS": BS, "BT": 900.0, "BK": 1000.0, "TK": 1400.0,
    "TS": 1750.0, "SF1": SF1, "SF2": SF2, "SG": 300.0, "TG": 80.0,
    # los del usuario
    "BSR": BS + 4, "FS": 120.0, "FRAME": 40.0, "RAIL": RAIL, "OFFSET_CABIN": 0.0,
    "OFFSET_SIDE": "L", "LengthTemplate": 0.0,
    # configuración
    "OMEGA_SIDE": "R", "WALL_LIMITING": False, "WALL_STOP": 0, "WALL_SIDE": "R",
    "NS": 3,
}

MATRIZ = [
    {"Floor": 0, "WR": 62.0, "FR": 812.0, "OR": 92.0, "WL": 78.0, "FL": 818.0, "OL": 86.0},
    {"Floor": 1, "WR": 68.0, "FR": 816.0, "OR": 89.0, "WL": 74.0, "FL": 820.0, "OL": 88.0},
    {"Floor": 2, "WR": 70.0, "FR": 818.0, "OR": 88.0, "WL": 72.0, "FL": 822.0, "OL": 90.0},
]


def proyecto() -> dict:
    """La fila de proyecto tal y como la devolvería `list_projects`."""
    return {
        "ID": "PRJ-FIX", "Group": "cliente1", "Name": "Obra de prueba (fixture)",
        "Nombre": "Obra de prueba (fixture)", "Client": "Cliente de prueba",
        "Cliente": "Cliente de prueba", "Status": "En progreso", "NS": 3,
        "ParamsJSON": json.dumps(PARAMS), "MatrizJSON": json.dumps(MATRIZ),
        "InterpJSON": "", "Ingeniero": "campo1", "Location": "Sydney NSW",
    }


def valido() -> bool:
    """⚠️ El propio fixture se comprueba: si el cálculo no lo digiere, no vale de nada.

    Sin esto, un fixture mal construido dejaría a los tres guardianes en verde sin
    haber generado ningún informe — el «OK en vacío» que el mecanismo de SIN DATOS
    existía justamente para no fingir (trampa nº1).
    """
    from core import survey_calc
    r = survey_calc.recalcular(PARAMS, MATRIZ)
    return bool(r) and bool(r.get("best"))
