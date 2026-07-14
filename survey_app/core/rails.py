"""
Catálogo de rieles (referencia → medidas) en Google Sheets, hoja 'Rieles'.

Al cargar un plano, se lee la referencia del CAR GUIDE RAIL (ej. 'T75-3/B') y se
busca aquí para autocompletar el campo RAIL del survey.

Columnas:
  Referencia   ej. T75-3/B
  AnchoDiente  ancho del diente del riel (mm)  → este es el valor RAIL
  AlturaDiente altura del diente desde la espalda del riel (mm)
"""
import logging

import streamlit as st

from core import timeclock

logger = logging.getLogger(__name__)

RIELES_SHEET   = "Rieles"
RIELES_HEADERS = ["Referencia", "AnchoDiente", "AlturaDiente"]


def is_configured() -> bool:
    return timeclock._secrets_present()


def _ws():
    ws, err = timeclock._get_worksheet()
    if err:
        return None, err
    try:
        ss = ws.spreadsheet
        try:
            w = ss.worksheet(RIELES_SHEET)
        except Exception:
            w = ss.add_worksheet(title=RIELES_SHEET, rows=200, cols=len(RIELES_HEADERS))
            w.append_row(RIELES_HEADERS)
        if not w.row_values(1):
            w.append_row(RIELES_HEADERS)
        return w, None
    except Exception as e:
        logger.warning("rails: no se pudo abrir la hoja %s: %s", RIELES_SHEET, e)
        return None, f"No se pudo abrir la hoja {RIELES_SHEET}: {e}"


@st.cache_data(ttl=120, show_spinner=False)
def _records():
    w, err = _ws()
    if err or w is None:
        return []
    try:
        return w.get_all_records(numericise_ignore=["all"])
    except Exception as e:
        logger.warning("rails: lectura falló: %s", e)
        return []


def _norm(ref) -> str:
    return str(ref).strip().upper().replace(" ", "")


def _f(v):
    try:
        return float(str(v).replace(",", "."))
    except Exception:
        return None


def list_rieles() -> list:
    return _records()


def get_rail(referencia) -> dict:
    """Devuelve {'referencia','ancho','altura'} de la referencia, o None si no está."""
    if not referencia:
        return None
    key = _norm(referencia)
    for r in _records():
        if _norm(r.get("Referencia", "")) == key:
            return {"referencia": str(r.get("Referencia", "")),
                    "ancho":  _f(r.get("AnchoDiente")),
                    "altura": _f(r.get("AlturaDiente"))}
    return None


def add_riel(referencia, ancho, altura) -> tuple:
    w, err = _ws()
    if err:
        return False, err
    referencia = str(referencia).strip()
    if not referencia:
        return False, "La referencia es obligatoria."
    if get_rail(referencia):
        return False, f"La referencia '{referencia}' ya existe."
    w.append_row([referencia, str(ancho), str(altura)], value_input_option="RAW")
    _records.clear()
    return True, f"Riel '{referencia}' agregado."


def update_riel(referencia, ancho=None, altura=None) -> tuple:
    w, err = _ws()
    if err:
        return False, err
    recs = w.get_all_records(numericise_ignore=["all"])
    for i, r in enumerate(recs):
        if _norm(r.get("Referencia", "")) == _norm(referencia):
            row = i + 2
            if ancho is not None:
                w.update_cell(row, 2, str(ancho))
            if altura is not None:
                w.update_cell(row, 3, str(altura))
            _records.clear()
            return True, "Riel actualizado."
    return False, "Referencia no encontrada."


def delete_riel(referencia) -> tuple:
    w, err = _ws()
    if err:
        return False, err
    recs = w.get_all_records(numericise_ignore=["all"])
    for i, r in enumerate(recs):
        if _norm(r.get("Referencia", "")) == _norm(referencia):
            w.delete_rows(i + 2)
            _records.clear()
            return True, "Riel eliminado."
    return False, "Referencia no encontrada."
