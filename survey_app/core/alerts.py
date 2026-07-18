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
from datetime import datetime

import streamlit as st

from core import timeclock
from core import notify
from core import auth

logger = logging.getLogger(__name__)

ALERTS_SHEET   = "Alarmas"
ALERTS_HEADERS = ["ID", "ProyectoID", "Grupo", "Origen", "Tipo", "Mensaje",
                  "CreadoPor", "Fecha", "Estado", "ResueltoPor", "FechaResuelta"]
_COL = {h: i + 1 for i, h in enumerate(ALERTS_HEADERS)}


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


@st.cache_data(ttl=30, show_spinner=False)
def _records():
    w, err = _ws()
    if err or w is None:
        return []
    try:
        return w.get_all_records(numericise_ignore=["all"])
    except Exception as e:
        logger.warning("alerts: lectura falló: %s", e)
        return []


def _invalidate():
    try:
        _records.clear()
    except Exception:
        pass


def _col_letter(n):
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


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
                  datetime.now().strftime("%Y-%m-%d %H:%M"), "abierta", "", ""],
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
                 "values": [[datetime.now().strftime("%Y-%m-%d %H:%M")]]},
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
            f"🔴 Alarma en proyecto {project_name or pid}",
            [f"<b>Problema reportado</b> por {creado_por}:", mensaje,
             f"Proyecto: {project_name or pid}."])
    return True, aid


def notify_change(pid, grupo, mensaje, creado_por, assigned_users, project_name="") -> tuple:
    """El admin cambió algo → aviso al campo asignado (in-app + Telegram)."""
    ok, aid = create_alert(pid, grupo, "admin", "cambio", mensaje, creado_por)
    if assigned_users:
        _notify(assigned_users,
                f"🔵 Actualización en {project_name or pid}",
                [f"El administrador actualizó el proyecto <b>{project_name or pid}</b>:", mensaje])
    return ok, aid
