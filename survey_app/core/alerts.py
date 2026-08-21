"""
Alarmas / avisos por proyecto (hoja 'Alarmas' en Google Sheets) + Telegram/email.

Dos flujos:
  - problema (campo → admin): el campo reporta un inconveniente. Llega a los admins del
    grupo + propietarios. El admin la resuelve → se apaga.
  - cambio  (admin → campo): al guardar cambios en el proyecto, se avisa al campo asignado.
    El campo la marca como vista → se apaga.

Estado: abierta | resuelta.
"""
import logging

import streamlit as st

from core import timeclock
from core import notify
from core import auth
from core import clock
from core.num import col_letter as _col_letter

logger = logging.getLogger(__name__)

ALERTS_SHEET   = "Alarmas"
ALERTS_HEADERS = ["ID", "ProyectoID", "Grupo", "Origen", "Tipo", "Mensaje",
                  "CreadoPor", "Fecha", "Estado", "ResueltoPor", "FechaResuelta"]
_COL = {h: i + 1 for i, h in enumerate(ALERTS_HEADERS)}



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


def _ws():
    if not timeclock._secrets_present():
        return None, "Google Sheets no está configurado."
    try:
        return timeclock.get_sheet(ALERTS_SHEET, tuple(ALERTS_HEADERS)), None
    except Exception as e:
        logger.warning("alerts: no se pudo abrir la hoja: %s", e)
        return None, f"No se pudo abrir la hoja {ALERTS_SHEET}: {e}"


@st.cache_data(ttl=120, show_spinner=False)
def _records_cached(libro: str):
    """Registros de "Alarmas" (por lote, v339)."""
    from core import hojas          # perezoso: evita el ciclo con timeclock
    return hojas.registros("Alarmas", ALERTS_HEADERS) or []




def _records():
    """Envoltorio: resuelve el libro y delega en la versión cacheada (v378).

    ⚠️ El id del libro va en la CLAVE de caché. Sin él, `st.cache_data` —que se
    comparte por PROCESO— servía al segundo cliente lo que dejó memoizado el
    primero: una fuga de datos entre inquilinos, no un problema de rendimiento.
    """
    return _records_cached(_libro_de("Alarmas"))
def _invalidate():
    # ⚠️ v339: además de la caché propia hay que tirar el LOTE compartido
    # (`hojas._lote`). Si no, tras escribir el dato seguiría saliendo del lote
    # cacheado hasta 120 s y parecería que no se guardó.
    from core import hojas
    hojas.invalidar()
    try:
        _records_cached.clear()
    except Exception:
        pass


# ── Lecturas ─────────────────────────────────────────────────────
def list_alerts(pid, estado=None) -> list:
    out = [r for r in _records() if str(r.get("ProyectoID", "")) == str(pid)]
    if estado:
        out = [r for r in out if str(r.get("Estado", "")) == estado]
    return out


def open_counts_all() -> dict:
    """{ProyectoID: nº alarmas abiertas} de todos los proyectos (1 lectura, para badges)."""
    d = {}
    for r in _records():
        if str(r.get("Estado", "")) == "abierta":
            k = str(r.get("ProyectoID", ""))
            d[k] = d.get(k, 0) + 1
    return d


# ── Escrituras ───────────────────────────────────────────────────
def _next_id(recs) -> str:
    mx = 0
    for r in recs:
        i = str(r.get("ID", ""))
        if i.startswith("ALR-"):
            try:
                mx = max(mx, int(i.split("-")[1]))
            except Exception:
                pass
    return f"ALR-{mx + 1:04d}"


def create_alert(pid, grupo, origen, tipo, mensaje, creado_por) -> tuple:
    w, err = _ws()
    if err:
        return False, err
    aid = _next_id(w.get_all_records(numericise_ignore=["all"]))
    w.append_row([aid, str(pid), str(grupo), origen, tipo, str(mensaje), str(creado_por),
                  clock.now().strftime("%Y-%m-%d %H:%M"), "abierta", "", ""],
                 value_input_option="RAW")
    _invalidate()
    return True, aid


def resolve_alert(alert_id, resuelto_por) -> tuple:
    w, err = _ws()
    if err:
        return False, err
    recs = w.get_all_records(numericise_ignore=["all"])
    for i, r in enumerate(recs):
        if str(r.get("ID", "")) == str(alert_id):
            row = i + 2
            w.batch_update([
                {"range": f"{_col_letter(_COL['Estado'])}{row}", "values": [["resuelta"]]},
                {"range": f"{_col_letter(_COL['ResueltoPor'])}{row}", "values": [[str(resuelto_por)]]},
                {"range": f"{_col_letter(_COL['FechaResuelta'])}{row}",
                 "values": [[clock.now().strftime("%Y-%m-%d %H:%M")]]},
            ], value_input_option="RAW")
            _invalidate()
            return True, "Alarma resuelta."
    return False, "Alarma no encontrada."


# ── Destinatarios ────────────────────────────────────────────────
def _admins_and_owners(grupo) -> list:
    users = auth.list_users()
    out = [u["Usuario"] for u in users
           if str(u.get("Rol", "")).lower() == "administrador" and str(u.get("Grupo", "")) == str(grupo)]
    out += [u["Usuario"] for u in users if str(u.get("Rol", "")).lower() == "propietario"]
    return list(dict.fromkeys(out))


def _notify(usuarios, subject, lines):
    for u in usuarios:
        try:
            notify.notify_user(u, subject, lines)
        except Exception as e:
            logger.warning("alerts notify %s: %s", u, e)


# ── Alto nivel ───────────────────────────────────────────────────
def report_problem(pid, grupo, mensaje, creado_por, project_name="") -> tuple:
    """El campo reporta un problema → alarma abierta + aviso a admins/propietarios."""
    ok, aid = create_alert(pid, grupo, "campo", "problema", mensaje, creado_por)
    if not ok:
        return False, aid
    _notify(_admins_and_owners(grupo),
            f"Alarma en proyecto {project_name or pid}",
            [f"<b>Problema reportado</b> por {creado_por}:", mensaje,
             f"Proyecto: {project_name or pid}."])
    return True, aid


def notify_change(pid, grupo, mensaje, creado_por, assigned_users, project_name="") -> tuple:
    """El admin cambió algo → aviso al campo asignado (in-app + Telegram)."""
    ok, aid = create_alert(pid, grupo, "admin", "cambio", mensaje, creado_por)
    if assigned_users:
        _notify(assigned_users,
                f"Actualización en {project_name or pid}",
                [f"El administrador actualizó el proyecto <b>{project_name or pid}</b>:", mensaje])
    return ok, aid
