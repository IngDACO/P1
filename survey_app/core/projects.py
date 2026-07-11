"""
Gestión de proyectos (un proyecto = un elevador) con persistencia en Google Sheets.

Modelo (ver CLAUDE.md):
  - Proyecto = 1 elevador. Se inicia con el survey (params + matriz + interpretaciones)
    y su cronograma. El avance = Σ(peso_actividad × avance) / Σ(peso).
  - Actividades = filas del cronograma; el usuario de campo actualiza su Avance%.
  - Agrupaciones = varios proyectos con peso; avance = Σ(peso_proy × avance_proy)/Σ(peso).
  - Horas: se suman del fichaje (hoja del timeclock) por nombre de proyecto.

Reusa la conexión del fichaje (core.timeclock._get_worksheet) y la misma hoja de cálculo.
Escrituras RAW + lecturas con numericise_ignore=['all'] (conserva textos/JSON/ceros).
"""
import json
import logging
from datetime import datetime, date

import streamlit as st

from core import timeclock

logger = logging.getLogger(__name__)

PROJECTS_SHEET   = "Proyectos"
ACTIVITIES_SHEET = "Actividades"
GROUPINGS_SHEET  = "Agrupaciones"

PROJECTS_HEADERS = [
    "ID", "Grupo", "Nombre", "Cliente", "Ubicacion", "Modelo", "NS",
    "Estado", "EstadoManual", "FechaInicio", "FechaFinEst", "Ingeniero",
    "CampoAsignados", "Avance", "AgrupacionID", "PesoEnAgrupacion",
    "ParamsJSON", "MatrizJSON", "InterpJSON", "CreadoPor", "Creado",
]
ACTIVITIES_HEADERS = [
    "ProyectoID", "Orden", "Nombre", "DuracionDias", "Peso", "Avance",
    "FechaInicioReal", "FechaFinReal", "Nota",
]
GROUPINGS_HEADERS = ["ID", "Grupo", "Nombre", "Descripcion"]

_PCOL = {h: i + 1 for i, h in enumerate(PROJECTS_HEADERS)}
_ACOL = {h: i + 1 for i, h in enumerate(ACTIVITIES_HEADERS)}

ESTADOS_MANUAL = ["", "En pausa", "Cancelado"]
FMT_DATE = "%Y-%m-%d"


def is_configured() -> bool:
    return timeclock._secrets_present()


# ── Worksheets (crea la pestaña si no existe) ────────────────────
def _get_ws(title, headers):
    ws, err = timeclock._get_worksheet()
    if err:
        return None, err
    try:
        ss = ws.spreadsheet
        try:
            w = ss.worksheet(title)
        except Exception:
            w = ss.add_worksheet(title=title, rows=500, cols=len(headers))
            w.append_row(headers)
        if not w.row_values(1):
            w.append_row(headers)
        return w, None
    except Exception as e:
        logger.warning("projects: no se pudo abrir la hoja %s: %s", title, e)
        return None, f"No se pudo abrir la hoja {title}: {e}"


def _projects_ws():   return _get_ws(PROJECTS_SHEET,   PROJECTS_HEADERS)
def _activities_ws(): return _get_ws(ACTIVITIES_SHEET, ACTIVITIES_HEADERS)
def _groupings_ws():  return _get_ws(GROUPINGS_SHEET,  GROUPINGS_HEADERS)


# ── Lecturas CACHEADAS (evitan golpear la API en cada rerun) ─────
# Google Sheets limita ~60 lecturas/min. Sin caché, cada slider/rerun re-leía
# las hojas y disparaba APIError (429). Se cachea 20s y se invalida al escribir.
_HEADERS_BY_TITLE = {
    PROJECTS_SHEET:   PROJECTS_HEADERS,
    ACTIVITIES_SHEET: ACTIVITIES_HEADERS,
    GROUPINGS_SHEET:  GROUPINGS_HEADERS,
}


@st.cache_data(ttl=20, show_spinner=False)
def _records(title):
    """Registros de una hoja (cacheados). Solo lecturas de DISPLAY."""
    w, err = _get_ws(title, _HEADERS_BY_TITLE.get(title, []))
    if err or w is None:
        return []
    try:
        return w.get_all_records(numericise_ignore=["all"])
    except Exception as e:
        logger.warning("projects: lectura de %s falló: %s", title, e)
        return []


@st.cache_data(ttl=20, show_spinner=False)
def _fichaje_records():
    """Registros del fichaje (cacheados) para sumar horas."""
    ws, err = timeclock._get_worksheet()
    if err or ws is None:
        return []
    try:
        return ws.get_all_records(numericise_ignore=["all"])
    except Exception as e:
        logger.warning("projects: lectura de fichaje falló: %s", e)
        return []


def _invalidate():
    """Limpia el caché de lecturas tras una escritura, para reflejar el cambio."""
    for fn in (_records, _fichaje_records):
        try:
            fn.clear()
        except Exception:
            pass


# ── Helpers de dominio ───────────────────────────────────────────
def _num(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default


def compute_avance(activities: list) -> float:
    """% del proyecto = Σ(peso × avance) / Σ(peso).  activities: list de dicts."""
    tot_peso = sum(_num(a.get("Peso")) for a in activities)
    if tot_peso <= 0:
        return 0.0
    acc = sum(_num(a.get("Peso")) * _num(a.get("Avance")) for a in activities)
    return round(acc / tot_peso, 1)


def derive_estado(avance: float, estado_manual: str = "") -> str:
    """Estado automático por avance, salvo override manual (En pausa / Cancelado)."""
    if estado_manual in ("En pausa", "Cancelado"):
        return estado_manual
    if avance <= 0:
        return "Planificado"
    if avance >= 100:
        return "Completado"
    return "En progreso"


def _next_project_id(pws) -> str:
    """PRJ-#### incremental (máximo existente + 1)."""
    mx = 0
    for r in pws.get_all_records(numericise_ignore=["all"]):
        pid = str(r.get("ID", ""))
        if pid.startswith("PRJ-"):
            try:
                mx = max(mx, int(pid.split("-")[1]))
            except Exception:
                pass
    return f"PRJ-{mx + 1:04d}"


def _find_row(ws, header, value):
    """Nº de fila (1-based, incluye cabecera) del primer registro con header==value."""
    records = ws.get_all_records(numericise_ignore=["all"])
    for i, r in enumerate(records):
        if str(r.get(header, "")) == str(value):
            return i + 2  # +1 cabecera, +1 base-1
    return None


# ── Agrupaciones ─────────────────────────────────────────────────
def list_groupings(grupo: str = None) -> list:
    out = []
    for r in _records(GROUPINGS_SHEET):
        if grupo is not None and str(r.get("Grupo", "")) != str(grupo):
            continue
        out.append(r)
    return out


def create_grouping(grupo: str, nombre: str, descripcion: str = "") -> tuple:
    gws, err = _groupings_ws()
    if err:
        return False, err
    existing = gws.get_all_records(numericise_ignore=["all"])
    mx = 0
    for r in existing:
        gid = str(r.get("ID", ""))
        if gid.startswith("AGR-"):
            try:
                mx = max(mx, int(gid.split("-")[1]))
            except Exception:
                pass
        if str(r.get("Grupo", "")) == str(grupo) and str(r.get("Nombre", "")) == nombre:
            return False, "Ya existe una agrupación con ese nombre en el grupo."
    gid = f"AGR-{mx + 1:04d}"
    gws.append_row([gid, grupo, nombre, descripcion], value_input_option="RAW")
    _invalidate()
    return True, gid


def delete_grouping(gid: str) -> tuple:
    gws, err = _groupings_ws()
    if err:
        return False, err
    row = _find_row(gws, "ID", gid)
    if row is None:
        return False, "Agrupación no encontrada."
    gws.delete_rows(row)
    _invalidate()
    return True, "Agrupación eliminada."


# ── Proyectos ────────────────────────────────────────────────────
def create_project(grupo, nombre, cliente="", ubicacion="", modelo="", ns=0,
                   ingeniero="", campo_asignados=None, fecha_inicio="", fecha_fin_est="",
                   params=None, matriz=None, interp=None, activities=None,
                   creado_por="", agrupacion_id="", peso_agrupacion=0) -> tuple:
    """Crea un proyecto (fila en Proyectos + filas en Actividades). Devuelve (ok, id|error)."""
    pws, err = _projects_ws()
    if err:
        return False, err
    aws, err2 = _activities_ws()
    if err2:
        return False, err2

    pid = _next_project_id(pws)
    campo = ";".join(campo_asignados or [])
    avance = compute_avance(activities or [])
    estado = derive_estado(avance, "")

    row = [
        pid, grupo, nombre, cliente, ubicacion, modelo, str(ns),
        estado, "", fecha_inicio, fecha_fin_est, ingeniero,
        campo, str(avance), agrupacion_id, str(peso_agrupacion),
        json.dumps(params or {}, ensure_ascii=False, default=str),
        json.dumps(matriz or [], ensure_ascii=False, default=str),
        json.dumps(interp or {}, ensure_ascii=False, default=str),
        creado_por, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    ]
    pws.append_row(row, value_input_option="RAW")

    # Actividades del cronograma (batch: 1 sola llamada a la API)
    act_rows = [[
        pid, str(i + 1), a.get("nombre", a.get("Nombre", f"Actividad {i+1}")),
        str(a.get("duracion", a.get("DuracionDias", 0))),
        str(a.get("peso", a.get("Peso", 0))),
        "0", "", "", "",
    ] for i, a in enumerate(activities or [])]
    if act_rows:
        aws.append_rows(act_rows, value_input_option="RAW")
    _invalidate()
    return True, pid


def list_projects(grupo: str = None, agrupacion_id: str = None) -> list:
    out = []
    for r in _records(PROJECTS_SHEET):
        if grupo is not None and str(r.get("Grupo", "")) != str(grupo):
            continue
        if agrupacion_id is not None and str(r.get("AgrupacionID", "")) != str(agrupacion_id):
            continue
        out.append(r)
    return out


def list_projects_for_field(usuario: str, grupo: str = None) -> list:
    """Proyectos donde el usuario de campo está asignado (CampoAsignados)."""
    out = []
    for r in list_projects(grupo=grupo):
        asignados = [x.strip() for x in str(r.get("CampoAsignados", "")).split(";") if x.strip()]
        if usuario in asignados:
            out.append(r)
    return out


def get_project(pid: str) -> dict:
    for r in _records(PROJECTS_SHEET):
        if str(r.get("ID", "")) == str(pid):
            return r
    return {}


def get_project_full(pid: str) -> dict:
    """Proyecto + JSONs deserializados (params, matriz, interp) + actividades."""
    r = get_project(pid)
    if not r:
        return {}
    def _load(key):
        try:
            return json.loads(r.get(key) or ("[]" if "Matriz" in key else "{}"))
        except Exception as e:
            logger.warning("projects: JSON inválido en %s de %s: %s", key, pid, e)
            return {} if "Matriz" not in key else []
    r["params"]     = _load("ParamsJSON")
    r["matriz"]     = _load("MatrizJSON")
    r["interp"]     = _load("InterpJSON")
    r["activities"] = list_activities(pid)
    return r


def update_project(pid: str, fields: dict) -> tuple:
    """Actualiza columnas sueltas del proyecto (fields = {Header: valor})."""
    pws, err = _projects_ws()
    if err:
        return False, err
    row = _find_row(pws, "ID", pid)
    if row is None:
        return False, "Proyecto no encontrado."
    for k, v in fields.items():
        if k in _PCOL:
            pws.update_cell(row, _PCOL[k], str(v))
    _invalidate()
    return True, "Proyecto actualizado."


def set_estado_manual(pid: str, estado_manual: str) -> tuple:
    if estado_manual not in ESTADOS_MANUAL:
        return False, "Estado manual inválido."
    prj = get_project(pid)
    if not prj:
        return False, "Proyecto no encontrado."
    avance = _num(prj.get("Avance"))
    return update_project(pid, {
        "EstadoManual": estado_manual,
        "Estado":       derive_estado(avance, estado_manual),
    })


def delete_project(pid: str) -> tuple:
    pws, err = _projects_ws()
    if err:
        return False, err
    row = _find_row(pws, "ID", pid)
    if row is None:
        return False, "Proyecto no encontrado."
    pws.delete_rows(row)
    # borrar sus actividades
    aws, err2 = _activities_ws()
    if not err2:
        recs = aws.get_all_records(numericise_ignore=["all"])
        for i in range(len(recs) - 1, -1, -1):
            if str(recs[i].get("ProyectoID", "")) == str(pid):
                aws.delete_rows(i + 2)
    _invalidate()
    return True, "Proyecto eliminado."


# ── Actividades ──────────────────────────────────────────────────
def list_activities(pid: str) -> list:
    out = [r for r in _records(ACTIVITIES_SHEET)
           if str(r.get("ProyectoID", "")) == str(pid)]
    out.sort(key=lambda r: _num(r.get("Orden")))
    return out


def update_activity_progress(pid: str, orden, avance, fecha_inicio="", fecha_fin="",
                             nota=None) -> tuple:
    """El usuario de campo actualiza el Avance% (0-100) de una actividad.
    Recalcula el avance y el estado del proyecto."""
    aws, err = _activities_ws()
    if err:
        return False, err
    avance = max(0.0, min(100.0, _num(avance)))
    recs = aws.get_all_records(numericise_ignore=["all"])
    target = None
    for i, r in enumerate(recs):
        if str(r.get("ProyectoID", "")) == str(pid) and str(r.get("Orden", "")) == str(orden):
            target = i + 2
            break
    if target is None:
        return False, "Actividad no encontrada."
    aws.update_cell(target, _ACOL["Avance"], str(avance))
    if fecha_inicio:
        aws.update_cell(target, _ACOL["FechaInicioReal"], fecha_inicio)
    if fecha_fin:
        aws.update_cell(target, _ACOL["FechaFinReal"], fecha_fin)
    if nota is not None:
        aws.update_cell(target, _ACOL["Nota"], nota)

    # Recalcular el avance del proyecto EN MEMORIA (recs ya leídas, sin re-leer)
    proj_acts = []
    for r in recs:
        if str(r.get("ProyectoID", "")) != str(pid):
            continue
        rr = dict(r)
        if str(rr.get("Orden", "")) == str(orden):
            rr["Avance"] = avance
        proj_acts.append(rr)
    nuevo  = compute_avance(proj_acts)
    prj    = get_project(pid)                       # cacheado
    manual = str(prj.get("EstadoManual", "")) if prj else ""
    update_project(pid, {"Avance": nuevo, "Estado": derive_estado(nuevo, manual)})
    # update_project ya invalida el caché de lecturas
    return True, f"Avance actualizado. Proyecto: {nuevo}%"


# ── Horas trabajadas (desde el fichaje) ──────────────────────────
def project_hours(proyecto_nombre: str, grupo: str = None) -> float:
    """Suma de horas del fichaje asociadas al proyecto (por nombre, opcionalmente grupo)."""
    total = 0.0
    for r in _fichaje_records():
        if str(r.get("Proyecto", "")) != str(proyecto_nombre):
            continue
        if grupo is not None and str(r.get("Grupo", "")) != str(grupo):
            continue
        total += _num(r.get("Horas"))
    return round(total, 2)


def project_hours_bulk(grupo: str = None) -> dict:
    """{nombre_proyecto: horas} (fichaje cacheado, 1 lectura para la lista)."""
    out = {}
    for r in _fichaje_records():
        if grupo is not None and str(r.get("Grupo", "")) != str(grupo):
            continue
        nom = str(r.get("Proyecto", ""))
        if not nom:
            continue
        out[nom] = out.get(nom, 0.0) + _num(r.get("Horas"))
    return {k: round(v, 2) for k, v in out.items()}


# ── Avance de una agrupación ─────────────────────────────────────
def grouping_progress(gid: str) -> dict:
    """Avance ponderado de una agrupación: Σ(peso_proy × avance_proy)/Σ(peso)."""
    proys = list_projects(agrupacion_id=gid)
    tot_peso = sum(_num(p.get("PesoEnAgrupacion")) for p in proys)
    if tot_peso <= 0:
        avance = 0.0
    else:
        avance = round(sum(_num(p.get("PesoEnAgrupacion")) * _num(p.get("Avance"))
                           for p in proys) / tot_peso, 1)
    return {"avance": avance, "n_proyectos": len(proys), "peso_total": tot_peso}


# ── Cronograma planificado + curva S real ────────────────────────
def project_schedule(pid: str):
    """Reconstruye el cronograma PLANIFICADO (de las actividades guardadas) y calcula
    la curva S REAL (del avance de cada actividad). Devuelve {sched, real, today_day} o None."""
    from core.schedule import build_schedule, real_scurve, schedule_projection
    prj  = get_project(pid)
    acts = list_activities(pid)
    if not prj or not acts:
        return None
    try:
        y, m, d = str(prj.get("FechaInicio", "")).split("-")
        start = date(int(y), int(m), int(d))
    except Exception:
        start = date.today()
    custom = [{"nombre":   a.get("Nombre", ""),
               "duracion": _num(a.get("DuracionDias")) or 1.0,
               "peso":     _num(a.get("Peso"))} for a in acts]
    sched     = build_schedule(1, start, {}, custom_rows=custom)
    avances   = [_num(a.get("Avance")) for a in acts]
    today_day = (date.today() - start).days
    real      = real_scurve(sched, avances, upto_day=today_day)   # se corta en HOY
    proj      = schedule_projection(sched, avances, today_day)
    return {"sched": sched, "real": real, "today_day": today_day,
            "avances": avances, "proj": proj}
