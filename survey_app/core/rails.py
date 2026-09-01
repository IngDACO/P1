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

from core.i18n import t
logger = logging.getLogger(__name__)

RIELES_SHEET   = "Rieles"
RIELES_HEADERS = ["Referencia", "AnchoDiente", "AlturaDiente"]


def is_configured() -> bool:
    return timeclock._secrets_present()


def _ws():
    """La hoja `Rieles` — ⚠️ del libro MAESTRO, no del libro del grupo.

    v404 · FALLO REAL: el catálogo de rieles es GLOBAL (v359 lo puso junto a `Login`,
    `Grupos` y `Manuales`, en el maestro). Pero esto se abría con
    `timeclock._get_worksheet()`, que devuelve el libro **del grupo de la sesión**, así
    que desde que hay un libro por cliente se **ESCRIBÍA en el libro del cliente y se
    LEÍA del maestro** — porque el lector va por `hojas.registros`, que resuelve con
    `sheet_id_para`. Medido en la demo: 2 rieles en el maestro, 0 en el libro donde
    escribía. Efecto: un riel nuevo no se encontraba NUNCA, así que al cargar un plano
    **RAIL se quedaba en 0** (el síntoma que v157 dio por cerrado), y editar o borrar
    un riel del catálogo real respondía «Referencia no encontrada».

    `get_sheet` resuelve el libro con el MISMO `sheet_id_para` que usa el lector, así
    que escritura y lectura vuelven a caer en el mismo sitio. Además crea la hoja y
    migra la cabecera, que es lo que hacía a mano el bloque anterior.
    """
    if not timeclock._secrets_present():
        return None, t("The rail catalogue is not connected: credentials "
                       "(gcp_service_account) or TIMECLOCK_SHEET_ID are missing "
                       "from Secrets.")
    try:
        return timeclock.get_sheet(RIELES_SHEET, tuple(RIELES_HEADERS)), None
    except Exception as e:
        logger.warning("rails: no se pudo abrir la hoja %s: %s", RIELES_SHEET, e)
        return None, f"{t('Could not open sheet')} {RIELES_SHEET}: {e}"


def _invalidate():
    """⚠️ Las DOS cachés, no solo la del módulo.

    `_records` lee por `hojas.registros`, o sea del LOTE de v339, que tiene su propia
    caché. Limpiar solo `_records` lo repuebla con el lote viejo y el riel recién
    creado no aparece hasta 120 s después — el «lo guardé y no sale» que v339 dejó
    documentado y que v344 encontró vivo en `projects`.
    """
    try:
        from core import hojas
        hojas.invalidar()
    except Exception:
        pass
    try:
        _records.clear()
    except Exception:
        pass


@st.cache_data(ttl=120, show_spinner=False)
def _records():
    """Registros de SHEET (por lote, v339)."""
    from core import hojas          # perezoso: evita el ciclo con timeclock
    return hojas.registros(RIELES_SHEET, RIELES_HEADERS) or []


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
        return False, t("The reference is required.")
    if get_rail(referencia):
        return False, f"{t('Reference')} '{referencia}' {t('already exists.')}"
    w.append_row([referencia, str(ancho), str(altura)], value_input_option="RAW")
    _invalidate()
    return True, f"{t('Rail')} '{referencia}' {t('added.')}"


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
            _invalidate()
            return True, t("Rail updated.")
    return False, t("Reference not found.")


def delete_riel(referencia) -> tuple:
    w, err = _ws()
    if err:
        return False, err
    recs = w.get_all_records(numericise_ignore=["all"])
    for i, r in enumerate(recs):
        if _norm(r.get("Referencia", "")) == _norm(referencia):
            w.delete_rows(i + 2)
            _invalidate()
            return True, t("Rail deleted.")
    return False, t("Reference not found.")
