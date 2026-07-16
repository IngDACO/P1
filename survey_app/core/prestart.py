"""
Pre-Start diario (Daily Pre-Start) — registro de la charla de seguridad antes de
empezar en obra, por proyecto. Basado en el formato de CI Liftworx.

Flujo al enviar: genera el PDF (marca = nombre del grupo) → lo archiva en la carpeta
del proyecto en Drive + lo registra como documento → guarda una fila en la hoja
`PreStarts` → si hay Near Miss/Hazard, abre una alarma del proyecto.

Nombre de archivo: `ddmmyyyy AB CD EF.pdf` (fecha + iniciales de los asistentes).
"""
import json
import logging
from datetime import datetime

import streamlit as st

from core import timeclock

logger = logging.getLogger(__name__)

SHEET   = "PreStarts"
HEADERS = ["ID", "ProyectoID", "Grupo", "Fecha", "Hora", "Location", "Facilitador",
           "ActividadesNotas", "NearMiss", "NearMissDesc", "S1JSON", "S3JSON",
           "NotasGenerales", "Asistentes", "Archivo", "DriveID", "CreadoPor", "Creado"]

# Sección 1 — YES/NO
CHECKS_S1 = [
    ("permisos",        "Permisos obtenidos y revisados por cambios desde su emisión"),
    ("toolbox",         "Notas del toolbox del builder revisadas y discutidas"),
    ("subcontratistas", "Coordinación con subcontratistas y otros oficios en obra"),
    ("preop",           "Chequeos/inspecciones pre-operacionales diarios hechos o asignados"),
]
# Sección 3 — Shaft Protection: NO/YES/N/A
CHECKS_S3 = [
    ("cages",        "Landing cages íntegras (fijas, seguras, sin huecos inaceptables)"),
    ("landings",     "Landings libres de escombros y herramientas que puedan caer al hueco"),
    ("penetrations", "Penetraciones del hueco adecuadamente cubiertas"),
]
OPTS_YN  = ["YES", "NO"]
OPTS_YNA = ["YES", "NO", "N/A"]


def is_configured() -> bool:
    return timeclock._secrets_present()


def _ws():
    if not timeclock._secrets_present():
        return None
    try:
        return timeclock.get_sheet(SHEET, tuple(HEADERS))
    except Exception as e:
        logger.warning("prestart: no se pudo abrir la hoja: %s", e)
        return None


@st.cache_data(ttl=30, show_spinner=False)
def _records() -> list:
    w = _ws()
    if w is None:
        return []
    try:
        return w.get_all_records(numericise_ignore=["all"])
    except Exception:
        return []


def _invalidate():
    try:
        _records.clear()
    except Exception:
        pass


def list_prestarts(pid) -> list:
    """Pre-starts de un proyecto, más recientes primero."""
    out = [r for r in _records() if str(r.get("ProyectoID", "")) == str(pid)]
    return list(reversed(out))


def _next_id(recs) -> str:
    mx = 0
    for r in recs:
        i = str(r.get("ID", ""))
        if i.startswith("PS-"):
            try:
                mx = max(mx, int(i.split("-")[1]))
            except Exception:
                pass
    return f"PS-{mx + 1:04d}"


def filename_for(data) -> str:
    """`ddmmyyyy AB CD EF.pdf` — fecha + iniciales de los asistentes."""
    f = data.get("fecha")
    ddmmyyyy = f.strftime("%d%m%Y") if hasattr(f, "strftime") else datetime.now().strftime("%d%m%Y")
    inis = [str(a.get("initial", "")).strip().upper() for a in data.get("attendees", [])
            if str(a.get("initial", "")).strip()]
    tail = (" " + " ".join(inis)) if inis else ""
    return f"{ddmmyyyy}{tail}.pdf"


def submit(data: dict) -> dict:
    """Genera el PDF, lo archiva en Drive + hoja y crea alarma si hay near miss.
    Devuelve {ok, id, pdf, filename, drive_id, alarma, error}."""
    res = {"ok": False, "id": "", "pdf": None, "filename": "", "drive_id": "",
           "alarma": False, "error": ""}

    # 1) PDF
    try:
        from core import prestart_pdf
        pdf = prestart_pdf.generate_prestart_pdf(data)
    except Exception as e:
        res["error"] = f"No se pudo generar el PDF: {e}"
        return res
    fname = filename_for(data)
    res["pdf"] = pdf
    res["filename"] = fname

    pid   = str(data.get("proyecto_id", ""))
    grupo = str(data.get("grupo", ""))
    creado_por = str(data.get("creado_por", ""))

    # 2) Archivar en Drive + documento del proyecto (best-effort)
    drive_id = ""
    try:
        from core import drive_store
        from core import projects
        if pid and drive_store.is_available():
            drive_id = drive_store.upload(pid, fname, pdf, "application/pdf")
            projects.add_document(pid, fname, "prestart", drive_id, creado_por)
    except Exception as e:
        logger.warning("prestart: archivado en Drive falló: %s", e)
    res["drive_id"] = drive_id

    # 3) Registro en la hoja
    w = _ws()
    if w is None:
        res["error"] = "No se pudo abrir la hoja de pre-starts."
        return res
    try:
        f = data.get("fecha")
        fecha_s = f.strftime("%Y-%m-%d") if hasattr(f, "strftime") else str(f)
        aid = _next_id(w.get_all_records(numericise_ignore=["all"]))
        w.append_row([
            aid, pid, grupo, fecha_s, str(data.get("hora", "")),
            str(data.get("location", "")), str(data.get("facilitador", "")),
            str(data.get("activities_notes", "")),
            str(data.get("near_miss", "NO")), str(data.get("near_miss_desc", "")),
            json.dumps(data.get("s1", {}), ensure_ascii=False),
            json.dumps(data.get("s3", {}), ensure_ascii=False),
            str(data.get("general_notes", "")),
            json.dumps(data.get("attendees", []), ensure_ascii=False),
            fname, drive_id, creado_por, datetime.now().strftime("%Y-%m-%d %H:%M"),
        ], value_input_option="RAW")
    except Exception as e:
        res["error"] = f"No se pudo registrar el pre-start: {e}"
        return res
    _invalidate()
    res["ok"] = True
    res["id"] = aid

    # 4) Alarma si hay near miss / hazard
    if str(data.get("near_miss", "")).upper() == "YES":
        try:
            from core import alerts
            msg = "Near Miss/Hazard reportado en el Pre-Start"
            if data.get("near_miss_desc"):
                msg += f": {data['near_miss_desc']}"
            ok, _ = alerts.report_problem(pid, grupo, msg, creado_por,
                                          data.get("proyecto_nombre", ""))
            res["alarma"] = bool(ok)
        except Exception as e:
            logger.warning("prestart: no se pudo crear la alarma: %s", e)

    return res
