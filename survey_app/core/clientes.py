"""Gestión de clientes (CRM básico) — hoja `Clientes`, multi-tenant por grupo.

Hasta ahora un cliente era solo el texto libre `Cliente` de cada proyecto: no
había dónde guardar persona de contacto, teléfono, email, dirección ni notas.
Este módulo añade la ENTIDAD cliente (con esa info) sin migrar nada: el enlace
cliente↔proyectos se resuelve **por nombre normalizado** (el `Cliente` del
proyecto). Más adelante se puede añadir un `ClienteID` al proyecto para robustez.

Sigue los mismos patrones que `projects.py`: handle de hoja cacheado vía
`timeclock.get_sheet` (crea/migra la cabecera una vez), lecturas cacheadas 30 s
con invalidación al escribir, y escrituras en batch.
"""
import logging

import streamlit as st

from core import clock, timeclock

logger = logging.getLogger(__name__)

CLIENTES_SHEET = "Clientes"
CLIENTES_HEADERS = [
    "ID", "Grupo", "Nombre", "Contacto", "Telefono", "Email",
    "Direccion", "Notas", "Activo", "CreadoPor", "Creado",
]
_CCOL = {h: i + 1 for i, h in enumerate(CLIENTES_HEADERS)}


def is_configured() -> bool:
    return timeclock._secrets_present()


def _norm(s) -> str:
    """Nombre normalizado para casar cliente↔proyecto (sin may/min ni espacios dobles)."""
    return " ".join(str(s or "").strip().lower().split())


def _num(v, default=0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _col_letter(n: int) -> str:
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


# ── Worksheet + lecturas cacheadas ───────────────────────────────
def _ws():
    if not timeclock._secrets_present():
        return None, "Google Sheets no está configurado."
    try:
        return timeclock.get_sheet(CLIENTES_SHEET, tuple(CLIENTES_HEADERS)), None
    except Exception as e:
        logger.warning("clientes: no se pudo abrir la hoja: %s", e)
        return None, f"No se pudo abrir la hoja {CLIENTES_SHEET}: {e}"


@st.cache_data(ttl=30, show_spinner=False)
def _records():
    w, err = _ws()
    if err or w is None:
        return []
    try:
        return w.get_all_records(numericise_ignore=["all"])
    except Exception as e:
        logger.warning("clientes: lectura falló: %s", e)
        return []


def _invalidate():
    try:
        _records.clear()
    except Exception:
        pass


# ── Lecturas de dominio ──────────────────────────────────────────
def list_clientes(grupo: str = None, incluir_inactivos: bool = False) -> list:
    """Fichas de cliente del grupo (las que tienen fila en la hoja)."""
    out = []
    for r in _records():
        if grupo is not None and str(r.get("Grupo", "")) != str(grupo):
            continue
        if not incluir_inactivos and str(r.get("Activo", "SI")).upper() in ("NO", "FALSE", "0"):
            continue
        out.append(r)
    return out


def get_cliente(cid: str) -> dict:
    for r in _records():
        if str(r.get("ID", "")) == str(cid):
            return r
    return {}


# ── Escrituras ───────────────────────────────────────────────────
def _next_id() -> str:
    """CLI-#### incremental (máximo existente + 1)."""
    mx = 0
    for r in _records():
        cid = str(r.get("ID", ""))
        if cid.startswith("CLI-"):
            try:
                mx = max(mx, int(cid.split("-")[1]))
            except Exception:
                pass
    return f"CLI-{mx + 1:04d}"


def create_cliente(grupo, nombre, contacto="", telefono="", email="",
                   direccion="", notas="", creado_por="") -> tuple:
    """Crea una ficha de cliente. Devuelve (ok, id|error)."""
    w, err = _ws()
    if err:
        return False, err
    nombre = str(nombre or "").strip()
    if not nombre:
        return False, "El nombre del cliente es obligatorio."
    for r in _records():
        if str(r.get("Grupo", "")) == str(grupo) and _norm(r.get("Nombre")) == _norm(nombre):
            return False, "Ya existe una ficha de cliente con ese nombre en el grupo."
    cid = _next_id()
    row = [cid, grupo, nombre, str(contacto or ""), str(telefono or ""),
           str(email or ""), str(direccion or ""), str(notas or ""),
           "SI", str(creado_por or ""), clock.now().strftime("%Y-%m-%d %H:%M:%S")]
    w.append_row(row, value_input_option="RAW")
    _invalidate()
    return True, cid


def update_cliente(cid: str, fields: dict) -> tuple:
    """Actualiza columnas sueltas de la ficha (fields = {Header: valor}), 1 batch."""
    w, err = _ws()
    if err:
        return False, err
    row = None
    try:
        recs = w.get_all_records(numericise_ignore=["all"])   # fresco al escribir
    except Exception as e:
        return False, str(e)
    for i, r in enumerate(recs):
        if str(r.get("ID", "")) == str(cid):
            row = i + 2  # +1 cabecera, +1 base-1
            break
    if row is None:
        return False, "Cliente no encontrado."
    batch = [{"range": f"{_col_letter(_CCOL[k])}{row}", "values": [[str(v)]]}
             for k, v in fields.items() if k in _CCOL]
    if batch:
        try:
            w.batch_update(batch, value_input_option="RAW")
        except Exception as e:
            return False, str(e)
    _invalidate()
    return True, "Cliente actualizado."


def set_activo(cid: str, activo: bool) -> tuple:
    return update_cliente(cid, {"Activo": "SI" if activo else "NO"})
