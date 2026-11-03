# -*- coding: utf-8 -*-
"""La memoria de conversación del Field assistant (v641).

Hasta aquí, cerrar la sesión borraba la conversación. Ahora se guarda por persona, para retomarla.

## Una fila por persona, no una por mensaje

Hoja `ChatMemory`, en el libro del cliente, con los últimos mensajes en JSON. Con una fila por mensaje
la hoja crecería sin fin, y el lote de lecturas la trae entera en cada recarga: esa es la cuota que
comparte toda la app (`constraint_cuota_sheets`). Así, una persona ocupa siempre una fila.

## ⚠️ Lo que se guarda es lo que se dijo, no lo que es verdad

Lo que el asistente contestó hace tres días puede estar viejo: por eso solo se conservan `MAX_DIAS`, y
su persona dice que los datos de hoy se vuelven a mirar. Las fotos no se guardan nunca: se quedan en la
pregunta que las llevó (`chat_ui`). Y las tarjetas sin confirmar tampoco: viven en la sesión.

`borrar` lo pide la propia persona con «Clear the conversation».
"""
import datetime as _dt
import json
import logging

import streamlit as st

from core import clock, columnas, timeclock
from core.num import col_letter

logger = logging.getLogger(__name__)

SHEET = "ChatMemory"
# ⚠️ Regla v363: columnas NUEVAS siempre al FINAL.
HEADERS = ["User", "Group", "Messages", "Updated"]
_COL = {h: i + 1 for i, h in enumerate(HEADERS)}

MAX_MENSAJES = 20         # los que el asistente recibe como historial (`chat_agent.MAX_HISTORY`)
MAX_DIAS = 14             # lo más viejo que merece la pena recordar
MAX_JSON = 40000          # una celda de Sheets admite 50000 caracteres


def _libro_de(_hoja) -> str:
    """El id del libro que le toca a esta hoja AHORA (v378): va en la CLAVE de caché."""
    try:
        return timeclock.sheet_id_para(_hoja)
    except Exception:
        return ""


def _ws():
    """⚠️ `get_sheet` CREA la hoja si falta: solo lo usan las escrituras."""
    if not timeclock._secrets_present():
        return None
    try:
        return timeclock.get_sheet(SHEET, tuple(HEADERS))
    except Exception as e:
        logger.warning("chat_memoria: no se pudo abrir %s: %s", SHEET, e)
        return None


@st.cache_data(ttl=120, show_spinner=False)
def _records_cached(libro: str) -> list:
    """⚠️ SIN cabeceras, y por eso va en `hojas.HOJAS_LECTURA` (v461/v507/v514/v610)."""
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
        logger.warning("chat_memoria._invalidate: %s", e)


def _fila_de(recs, usuario, grupo):
    """`(número de fila, registro)` de esa persona, o `(None, None)`. Por usuario Y grupo."""
    for i, r in enumerate(recs or []):
        if str(r.get("User", "")).strip() == str(usuario).strip() and str(r.get("Group", "")).strip() == str(grupo).strip():
            return i + 2, r
    return None, None


def recortar(mensajes, hoy) -> list:
    """Lo que merece quedarse. ⚠️ Siempre empezando por una pregunta: la API rechaza una conversación
    que empieza por el asistente, y al cortar por el principio puede quedar así."""
    _lim = (hoy - _dt.timedelta(days=MAX_DIAS)).isoformat()
    out = [{"role": m["role"], "content": str(m["content"]), "at": str(m.get("at") or hoy.isoformat()),
            # v645 · lo que escribió la app al tocar una tarjeta lo sigue siendo mañana (`chat_agent._para_el_modelo`)
            **({"app": str(m["app"]), "card": str(m.get("card") or "")} if m.get("app") else {})}
           for m in (mensajes or [])
           if isinstance(m, dict) and m.get("role") in ("user", "assistant") and str(m.get("content") or "").strip()]
    out = [m for m in out if m["at"] >= _lim][-MAX_MENSAJES:]
    while out and (out[0]["role"] != "user" or len(json.dumps(out, ensure_ascii=False)) > MAX_JSON):
        out = out[1:]
    return out


def cargar(usuario, grupo) -> list:
    """La conversación guardada, o []. Nunca lanza: sin memoria el asistente sigue funcionando."""
    try:
        _f, r = _fila_de(_records(), usuario, grupo)
        if r is None:
            return []
        return recortar(json.loads(r.get("Messages") or "[]"), clock.today(grupo))
    except Exception as e:
        logger.warning("chat_memoria.cargar(%s): %s", usuario, e)
        return []


def guardar(usuario, grupo, mensajes) -> bool:
    """Guarda la conversación. ⚠️ Lee FRESCO para decidir la fila (v323), y un fallo no se le enseña a
    nadie: perder la memoria no puede estropear la respuesta que ya se dio."""
    if not str(usuario or "").strip() or not str(grupo or "").strip():
        return False
    w = _ws()
    if w is None:
        return False
    try:
        txt = json.dumps(recortar(mensajes, clock.today(grupo)), ensure_ascii=False)
        _ahora = clock.now(grupo).strftime("%Y-%m-%d %H:%M")
        f, _r = _fila_de(columnas.canonizar(w.get_all_records(numericise_ignore=["all"])), usuario, grupo)
        if f is None:
            w.append_row([str(usuario), str(grupo), txt, _ahora], value_input_option="RAW")
        else:
            _c = col_letter(_COL["Messages"])
            _u = col_letter(_COL["Updated"])
            w.batch_update([{"range": f"{_c}{f}:{_u}{f}", "values": [[txt, _ahora]]}], value_input_option="RAW")
    except Exception as e:
        logger.warning("chat_memoria.guardar(%s): %s", usuario, e)
        return False
    _invalidate()
    return True


def borrar(usuario, grupo) -> bool:
    """«Clear the conversation»: se va de verdad, no se oculta: es de la persona que lo pide."""
    w = _ws()
    if w is None:
        return False
    try:
        f, _r = _fila_de(columnas.canonizar(w.get_all_records(numericise_ignore=["all"])), usuario, grupo)
        if f is not None:
            w.delete_rows(f)
            _invalidate()
    except Exception as e:
        logger.warning("chat_memoria.borrar(%s): %s", usuario, e)
        return False
    return True
