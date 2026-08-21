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
from core.num import col_letter as _col_letter

logger = logging.getLogger(__name__)

CLIENTES_SHEET = "Clientes"
CLIENTES_HEADERS = [
    "ID", "Grupo", "Nombre", "Contacto", "Telefono", "Email",
    "Direccion", "Notas", "Activo", "CreadoPor", "Creado",
]
_CCOL = {h: i + 1 for i, h in enumerate(CLIENTES_HEADERS)}



def _libro_de(_hoja) -> str:
    """El id del libro que le toca a esta hoja AHORA (v378).

    Va como primer argumento del lector cacheado para que la clave distinga
    inquilinos. No se usa dentro: `hojas.registros` resuelve el libro por su
    cuenta; aquí solo hace falta que el VALOR entre en la clave.
    """
    try:
        from core import timeclock
        return timeclock.sheet_id_para(_hoja)
    except Exception:
        return ""

def is_configured() -> bool:
    return timeclock._secrets_present()


def _norm(s) -> str:
    """Nombre normalizado para casar cliente↔proyecto (sin may/min ni espacios dobles)."""
    return " ".join(str(s or "").strip().lower().split())


# ── Worksheet + lecturas cacheadas ───────────────────────────────
def _ws():
    if not timeclock._secrets_present():
        return None, "Google Sheets no está configurado."
    try:
        return timeclock.get_sheet(CLIENTES_SHEET, tuple(CLIENTES_HEADERS)), None
    except Exception as e:
        logger.warning("clientes: no se pudo abrir la hoja: %s", e)
        return None, f"No se pudo abrir la hoja {CLIENTES_SHEET}: {e}"


@st.cache_data(ttl=120, show_spinner=False)
def _records_cached(libro: str):
    """Registros de CLIENTES_SHEET (por lote, v339)."""
    from core import hojas          # perezoso: evita el ciclo con timeclock
    return hojas.registros(CLIENTES_SHEET, CLIENTES_HEADERS) or []




def _records():
    """Envoltorio: resuelve el libro y delega en la versión cacheada (v378).

    ⚠️ El id del libro va en la CLAVE de caché. Sin él, `st.cache_data` —que se
    comparte por PROCESO— servía al segundo cliente lo que dejó memoizado el
    primero: una fuga de datos entre inquilinos, no un problema de rendimiento.
    """
    return _records_cached(_libro_de(CLIENTES_SHEET))
def _invalidate():
    # ⚠️ v339: además de la caché propia hay que tirar el LOTE compartido
    # (`hojas._lote`). Si no, tras escribir, el dato seguiría saliendo del lote
    # cacheado hasta 120 s y parecería que no se guardó.
    from core import hojas
    hojas.invalidar()
    try:
        _records_cached.clear()
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
def _ids_frescos(col: str = "ID") -> list:
    """Los IDs LEÍDOS DE LA HOJA, saltándose la caché (ver `invoices._ids_frescos`).

    ⚠️ v323: `_next_id` leía de `_records()` (cacheado 120 s desde v290) y podía
    devolver un ID **ya usado**. El ID es la identidad: dos clientes con el mismo
    CLI-#### se pisan y los proyectos enlazados apuntan al equivocado.
    """
    w, err = _ws()
    if err or w is None:
        return []
    try:
        vals = w.get_all_values()
    except Exception as e:
        logger.warning("clientes: lectura fresca de IDs falló: %s", e)
        return []
    if not vals:
        return []
    try:
        i = vals[0].index(col)
    except ValueError:
        return []
    return [f[i] for f in vals[1:] if len(f) > i]


def _next_id() -> str:
    """CLI-#### incremental (máximo existente + 1). Lee FRESCO: es escritura."""
    mx = 0
    for cid in _ids_frescos():
        cid = str(cid)
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


# ── Enlace cliente↔proyecto (ID-primero, nombre-de-respaldo) ─────
def es_del_cliente(proyecto: dict, cid: str, nombre_norm: str) -> bool:
    """¿El proyecto pertenece a este cliente?

    Regla única (como `timeclock.es_del_proyecto`, v145): si el proyecto tiene
    `ClienteID`, manda ese; si no, cae al `Cliente` (texto) normalizado. Así un
    proyecto vinculado por ID sigue casando aunque le renombren el texto, y los
    proyectos viejos (sin ID) siguen casando por nombre.
    """
    pid_cli = str(proyecto.get("ClienteID", "")).strip()
    if pid_cli:
        return bool(cid) and pid_cli == str(cid)
    return _norm(proyecto.get("Cliente")) == nombre_norm


def client_key(proyecto: dict, fichas_by_id: dict):
    """(clave_normalizada, display) del cliente de un proyecto.

    Si el `ClienteID` resuelve a una ficha, se agrupa bajo el NOMBRE de la ficha
    (aunque el texto `Cliente` difiera); si no, bajo el texto `Cliente`.
    """
    pid_cli = str(proyecto.get("ClienteID", "")).strip()
    f = fichas_by_id.get(pid_cli) if pid_cli else None
    nom = (f.get("Nombre") if f else str(proyecto.get("Cliente", "")).strip())
    return _norm(nom), nom
