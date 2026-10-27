# -*- coding: utf-8 -*-
"""La lista de pendientes de una obra (v615): el campo apunta tareas y las marca como hechas.

Decisión del usuario (28/10/2026): «una herramienta que le permite al usuario de campo crear una
lista de tareas pendientes en el proyecto. Es una sencilla lista de check en donde puede ir
agregando tareas y también ir marcando como hechas algunas de estas». Y, preguntado:
  1. UNA lista por obra, compartida por toda la cuadrilla (cada tarea dice quién la apuntó);
  2. la marca y desmarca cualquiera de la obra; la BORRA solo quien la escribió (o la oficina);
  3. la oficina también añade (le sirve para dejarle encargos a la cuadrilla);
  4. nada más por ahora: ni fechas, ni asignar a alguien, ni prioridad.

## ⚠️ No acredita nada
Es una lista, no el avance: marcar una tarea no toca ninguna actividad ni el % de la obra. El
avance sigue siendo lo que el campo marca en «Progress» (v514) o confirma de su parte (v523).

## ⚠️ Borrar OCULTA, no elimina
`Active=NO` con quién y cuándo: una tarea que alguien apuntó no desaparece del libro porque otro
la quite de la vista. Solo `borrar_de_obra` (al borrar la OBRA, como los partes) quita filas.
"""
import logging
import re

import streamlit as st

from core import clock, columnas, timeclock
from core.i18n import t
from core.num import num as _num

logger = logging.getLogger(__name__)

SHEET = "Tasks"
# ⚠️ Regla v363: columnas NUEVAS siempre al FINAL.
HEADERS = ["ID", "Group", "ProjectID", "Text", "CreatedBy", "Created",
           "Done", "DoneBy", "DoneAt", "Active", "DeletedBy", "DeletedAt"]
_COL = {h: i + 1 for i, h in enumerate(HEADERS)}
HECHA = "YES"
MAX_TEXTO = 200        # una tarea es una línea («Pick up the landing door keys»), no un parte


def _libro_de(_hoja) -> str:
    """El id del libro que le toca a esta hoja AHORA (v378): va en la CLAVE de caché."""
    try:
        return timeclock.sheet_id_para(_hoja)
    except Exception:
        return ""


def is_configured() -> bool:
    return timeclock._secrets_present()


def _ws():
    """⚠️ `get_sheet` CREA la hoja si falta: solo lo usan las escrituras."""
    if not timeclock._secrets_present():
        return None
    try:
        return timeclock.get_sheet(SHEET, tuple(HEADERS))
    except Exception as e:
        logger.warning("tareas: no se pudo abrir %s: %s", SHEET, e)
        return None


@st.cache_data(ttl=120, show_spinner=False)
def _records_cached(libro: str) -> list:
    """⚠️ SIN cabeceras: con ellas cae a `get_sheet`, que CREA la hoja — un lector que
    escribe (regla v145). La crea la primera tarea que se apunte. Y por eso la hoja va en
    `hojas.HOJAS_LECTURA`: fuera del lote se leería VACÍA para siempre (v461/v507/v514/v610)."""
    from core import hojas
    return hojas.registros(SHEET) or []


def _records():
    return _records_cached(_libro_de(SHEET))


def _invalidate():
    from core import hojas
    hojas.invalidar(SHEET)
    try:
        _records_cached.clear()
    except Exception as e:
        logger.warning("tareas._invalidate: %s", e)


def normaliza(s) -> str:
    """Para comparar dos tareas: sin mayúsculas ni espacios de más."""
    return re.sub(r"\s+", " ", str(s or "")).strip().lower()


def hecha(r) -> bool:
    return str((r or {}).get("Done", "")).strip().upper() == HECHA


def _activa(r) -> bool:
    return str((r or {}).get("Active", "")).strip().upper() != "NO"


# ═════════════════════════════════════════════════════════════════
# Lecturas
# ═════════════════════════════════════════════════════════════════
def de_obra(pid) -> list:
    """Las tareas VIVAS de una obra (las borradas no), sin ordenar."""
    return [r for r in _records()
            if str(r.get("ProjectID", "")) == str(pid) and _activa(r)
            and str(r.get("Text", "")).strip()]


def pendientes(pid) -> list:
    """Las pendientes, la ÚLTIMA apuntada primero: queda justo debajo de la caja donde se
    escribió, y quien la acaba de añadir la ve sin bajar (con una lista larga, al final no)."""
    return sorted([r for r in de_obra(pid) if not hecha(r)],
                  key=lambda r: (str(r.get("Created", "")), str(r.get("ID", ""))), reverse=True)


def hechas(pid) -> list:
    """Las hechas, la ÚLTIMA marcada primero."""
    return sorted([r for r in de_obra(pid) if hecha(r)],
                  key=lambda r: (str(r.get("DoneAt", "")), str(r.get("ID", ""))), reverse=True)


# ═════════════════════════════════════════════════════════════════
# Escrituras — ⚠️ todas leen FRESCO para decidir dónde escribir (v323)
# ═════════════════════════════════════════════════════════════════
def _next_id(recs) -> str:
    n = 0
    for r in recs:
        _v = str(r.get("ID", ""))
        if _v.startswith("TSK-"):
            n = max(n, int(_num(_v[4:]) or 0))
    from core import hojas
    try:
        return hojas.siguiente_id_libre("TSK-", n, propia=SHEET)
    except Exception as e:                       # nunca impedir dar de alta
        logger.warning("tareas._next_id: %s", e)
        return "TSK-%04d" % (n + 1)


def _frescos(w) -> list:
    return columnas.canonizar(w.get_all_records(numericise_ignore=["all"]))


def crear(pid, grupo, texto, autor) -> tuple:
    """Apunta una tarea. `(ok, id_o_mensaje)`.

    ⚠️ Una tarea igual que otra PENDIENTE de la misma obra no se repite: dos personas apuntando
    lo mismo, o un doble toque en el móvil, la duplicarían (lo que pasó con el alta de Inventory
    en v599). Si ya está hecha, sí se puede volver a apuntar: es otra vez trabajo."""
    _txt = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not _txt:
        return False, t("Write the task first.")
    if len(_txt) > MAX_TEXTO:
        return False, t("That is too long for a task ({n} of {max} characters). Keep it to one line.",
                        n=len(_txt), max=MAX_TEXTO)
    if not str(pid or "").strip():
        return False, t("The task has to belong to a job.")
    w = _ws()
    if w is None:
        return False, timeclock.motivo_sin_hoja()
    try:
        recs = _frescos(w)
        if any(str(r.get("ProjectID", "")) == str(pid) and _activa(r) and not hecha(r)
               and normaliza(r.get("Text")) == normaliza(_txt) for r in recs):
            return False, t("That task is already on the list.")
        tid = _next_id(recs)
        _ahora = clock.now(grupo).strftime("%Y-%m-%d %H:%M:%S")
        # ⚠️ La fila ENTERA, posicional (v363): lo de «hecha» y «borrada» nace vacío.
        w.append_row([tid, str(grupo or ""), str(pid), _txt, str(autor or ""), _ahora,
                      "", "", "", "", "", ""], value_input_option="RAW")
    except Exception as e:
        logger.warning("tareas.crear(%s): %s", pid, e)
        return False, timeclock.motivo_sin_hoja()
    _invalidate()
    return True, tid


def _fila(recs, tid, pid):
    for i, r in enumerate(recs):
        if str(r.get("ID", "")) == str(tid) and str(r.get("ProjectID", "")) == str(pid):
            return i + 2, r
    return None, None


def marcar(tid, pid, hecho, quien) -> tuple:
    """Marca (o desmarca) una tarea. `(ok, mensaje)`. Cualquiera de la obra (decisión del
    usuario): la pantalla solo se la enseña a quien está en ella.
    ⚠️ Si ya está como se pide (dos personas, o un doble toque), no escribe nada y dice que sí:
    lo que se quería ya es verdad."""
    w = _ws()
    if w is None:
        return False, timeclock.motivo_sin_hoja()
    try:
        recs = _frescos(w)
    except Exception as e:
        logger.warning("tareas.marcar(%s): %s", tid, e)
        return False, timeclock.motivo_sin_hoja()
    fila, r = _fila(recs, tid, pid)
    if fila is None or not _activa(r):
        return False, t("That task is no longer on the list.")
    if hecha(r) == bool(hecho):
        return True, ""
    from core.num import col_letter
    _ahora = clock.now(r.get("Group")).strftime("%Y-%m-%d %H:%M:%S") if hecho else ""
    try:
        w.batch_update([
            {"range": "%s%d" % (col_letter(_COL["Done"]), fila), "values": [[HECHA if hecho else ""]]},
            {"range": "%s%d" % (col_letter(_COL["DoneBy"]), fila), "values": [[str(quien) if hecho else ""]]},
            {"range": "%s%d" % (col_letter(_COL["DoneAt"]), fila), "values": [[_ahora]]},
        ], value_input_option="RAW")
    except Exception as e:
        logger.warning("tareas.marcar(%s): %s", tid, e)
        return False, timeclock.motivo_sin_hoja()
    _invalidate()
    return True, ""


def puede_borrar(r, quien, gestor) -> bool:
    """Quien la escribió, o la oficina (admin/propietario) — decisión del usuario."""
    return bool(gestor) or str((r or {}).get("CreatedBy", "")) == str(quien)


def borrar(tid, pid, quien, gestor) -> tuple:
    """La quita de la lista (`Active=NO`, con quién y cuándo: no se elimina la fila).
    ⚠️ Los permisos se miran AQUÍ otra vez, sobre la fila fresca: la pantalla solo ofrece
    las que cada uno puede quitar, pero quien decide es esto."""
    w = _ws()
    if w is None:
        return False, timeclock.motivo_sin_hoja()
    try:
        recs = _frescos(w)
    except Exception as e:
        logger.warning("tareas.borrar(%s): %s", tid, e)
        return False, timeclock.motivo_sin_hoja()
    fila, r = _fila(recs, tid, pid)
    if fila is None or not _activa(r):
        return False, t("That task is no longer on the list.")
    if not puede_borrar(r, quien, gestor):
        return False, t("Only the person who wrote it (or the office) can delete it.")
    from core.num import col_letter
    _ahora = clock.now(r.get("Group")).strftime("%Y-%m-%d %H:%M:%S")
    try:
        w.batch_update([
            {"range": "%s%d" % (col_letter(_COL["Active"]), fila), "values": [["NO"]]},
            {"range": "%s%d" % (col_letter(_COL["DeletedBy"]), fila), "values": [[str(quien)]]},
            {"range": "%s%d" % (col_letter(_COL["DeletedAt"]), fila), "values": [[_ahora]]},
        ], value_input_option="RAW")
    except Exception as e:
        logger.warning("tareas.borrar(%s): %s", tid, e)
        return False, timeclock.motivo_sin_hoja()
    _invalidate()
    return True, t("Task deleted.")


def borrar_de_obra(pid) -> int:
    """Todas las tareas de una obra, de una vez (al borrar la OBRA, `projects.delete_project`).
    Devuelve cuántas se fueron. ⚠️ Como los partes (v516) y los créditos (v514): viven en OTRA
    hoja, y sin esto quedarían apuntando a una obra que ya no existe — y se pegarían a una obra
    nueva si algún día se reutilizara el ID."""
    w = _ws()
    if w is None:
        return 0
    try:
        recs = _frescos(w)
    except Exception as e:
        logger.warning("tareas.borrar_de_obra(%s): %s", pid, e)
        return 0
    # ⚠️ De abajo arriba: borrar por índice desplaza todo lo que va debajo.
    filas = [i + 2 for i, r in enumerate(recs) if str(r.get("ProjectID", "")) == str(pid)]
    n = 0
    for fila in sorted(filas, reverse=True):
        try:
            w.delete_rows(fila)
            n += 1
        except Exception as e:
            logger.warning("tareas.borrar_de_obra(%s): %s", pid, e)
            break
    if n:
        _invalidate()
    return n
