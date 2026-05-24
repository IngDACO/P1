"""
Lógica compartida de resaltado de celdas (highlight) para tablas de survey.

Se usa tanto en la app Streamlit como en el reporte PDF (ReportLab).
La lógica de DECIDIR el highlight vive aquí; cada renderizador traduce
el código de highlight a su formato propio (CSS para Streamlit,
TableStyle para ReportLab).

Convención:
  - WR/WL/FR/FL: fuera de límite = v < LIMIT (clearance insuficiente)
  - OR/OL:       fuera de límite = v > LIMIT (apertura requiere corte)

Códigos de highlight:
  None      → sin resaltado (dentro del límite)
  "extreme" → el valor más crítico (MIN para WR/WL/FR/FL, MAX para OR/OL)
  "out"     → fuera de límite pero no es el más crítico
  "cut"     → OR/OL en Caso 2 (no cuenta como OFF, requiere corte físico)
"""
from typing import Optional

SURVEY_COLS = ["WR", "FR", "OR", "WL", "FL", "OL"]
OR_OL_COLS  = ("OR", "OL")
EPS         = 1e-3   # tolerancia para comparar floats


def cell_state(
    value, col: str, lim: float,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    in_cut_cols: bool = False,
    ctrl_applies: bool = False,
) -> Optional[str]:
    """
    Decide el estado de resaltado de una celda.

    Parameters
    ----------
    value         : valor en la celda
    col           : nombre de la columna (WR/WL/FR/FL/OR/OL)
    lim           : límite base de la columna (sin ajuste por controlador)
    min_val       : valor mínimo de la columna (para resaltar el peor en WR/WL/FR/FL)
    max_val       : valor máximo de la columna (para resaltar el peor en OR/OL)
    in_cut_cols   : True si la columna está en cut_cols (Caso 2: OR/OL no cuentan)
    ctrl_applies  : True si el controlador en frame aplica a esta celda (último nivel)

    Returns
    -------
    "extreme" | "out" | "cut" | None
    """
    if not isinstance(value, (int, float)):
        return None

    eff_lim = lim - 70 if ctrl_applies else lim

    if col in OR_OL_COLS:
        # OR/OL: fuera de límite = v > LIMIT
        if value > eff_lim:
            if max_val is not None and abs(value - max_val) < EPS:
                return "extreme"
            return "cut" if in_cut_cols else "out"
        return None
    else:
        # WR/WL/FR/FL: fuera de límite = v < LIMIT
        if value < eff_lim:
            if min_val is not None and abs(value - min_val) < EPS:
                return "extreme"
            return "out"
        return None


def ctrl_applies_to_cell(
    row_idx: int, total_rows: int, col: str,
    ctrl_in_frame: bool, ctrl_side: Optional[str],
) -> bool:
    """
    Determina si la regla del controlador en frame (LIMIT − 70 mm)
    aplica a una celda específica.

    Solo aplica en el último nivel, sobre OR (si ctrl_side="R") o OL (si "L").
    """
    if not ctrl_in_frame:
        return False
    if row_idx != total_rows - 1:
        return False
    if col == "OR" and ctrl_side == "R":
        return True
    if col == "OL" and ctrl_side == "L":
        return True
    return False


# ── Renderizado para Streamlit ────────────────────────────────────
_STREAMLIT_CSS = {
    "extreme": "background-color:#c0392b;color:white;font-weight:bold",
    "out":     "background-color:#f1948a",
    "cut":     "background-color:#e67e22;color:white;font-weight:bold",
}


def streamlit_style(state: Optional[str]) -> str:
    """Devuelve el string CSS para Streamlit dado un estado de celda."""
    return _STREAMLIT_CSS.get(state, "") if state else ""


# ── Renderizado para ReportLab ────────────────────────────────────
# Cada estado devuelve una lista de comandos TableStyle aplicables
# en (col, row), (col, row).  El llamador inserta col,row en los comandos.
def reportlab_commands(state: Optional[str], colors_mod):
    """
    Devuelve una lista de tuplas (estilo_atributo, color_o_valor) para
    aplicar al celda. El llamador debe envolverlas con las coords (ci, ri).

    Parameters
    ----------
    state      : código devuelto por cell_state()
    colors_mod : el módulo reportlab.lib.colors (para crear HexColor)

    Returns
    -------
    list de tuplas ('BACKGROUND', color), ('TEXTCOLOR', color), ('FONTNAME', name)
    """
    if not state:
        return []
    if state == "extreme":
        return [
            ("BACKGROUND", colors_mod.HexColor("#c0392b")),
            ("TEXTCOLOR",  colors_mod.white),
            ("FONTNAME",   "Helvetica-Bold"),
        ]
    if state == "cut":
        return [
            ("BACKGROUND", colors_mod.HexColor("#e67e22")),
            ("TEXTCOLOR",  colors_mod.white),
            ("FONTNAME",   "Helvetica-Bold"),
        ]
    if state == "out":
        return [("BACKGROUND", colors_mod.HexColor("#f1948a"))]
    return []
