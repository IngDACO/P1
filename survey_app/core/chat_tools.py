# -*- coding: utf-8 -*-
"""Lo que el Field assistant puede CONSULTAR (v639): el primer nivel de autonomía.

Hasta aquí no sabía quién le preguntaba: recibía la guía, los manuales y el cálculo abierto, y
«¿qué me falta hoy?» no tenía respuesta. Ahora puede mirar los datos de ESA persona antes de
contestar. Decisión del usuario (02/11/2026): tres niveles —ver, preparar y confirmar, actuar solo en
lo reversible— y se empieza por ver.

## ⚠️ La identidad no la dice el modelo

Ninguna herramienta recibe un usuario: sale de `ctx`, que la app arma con la SESIÓN. El modelo solo
elige QUÉ mirar y `project_id`, que se comprueba contra las obras de la persona (`_obra`). Así, ni un
error del modelo ni un texto escrito en una tarea pueden enseñar los datos de otro.

## ⚠️ Lo que devuelven son DATOS

Tareas, partes y avisos los escribe otra gente: el texto llega aquí tal cual y la persona del
asistente dice que nunca es una instrucción (`chat_agent._PERSONA`).

## Solo lectura

Ninguna función de este módulo escribe, y lo que el campo no ve en su pantalla no sale de aquí: las
nóminas no están, y los documentos pasan por el mismo filtro que Files (`_CAMPO_VER`).
"""
import json
import logging

from core import clock
from core.num import dmy, num as _num

logger = logging.getLogger(__name__)

MAX_PARTES = 3            # los últimos partes de la obra: para saber por dónde va, no el archivo
MAX_CARACTERES = 400      # de cada texto largo (un parte, las instrucciones)
MAX_SOLICITUDES = 8       # las últimas ausencias
# `credentials.estado` devuelve el dato en español, que es con lo que se compara en la app
_ESTADO_CRED = {"incompleta": "incomplete", "vigente": "valid", "por_vencer": "expiring_soon", "vencido": "expired"}


class _Negado(Exception):
    """Lo que se pidió no se puede: el mensaje vuelve al modelo con `is_error`."""


def _corto(texto, n=MAX_CARACTERES) -> str:
    _t = " ".join(str(texto or "").split())
    return _t if len(_t) <= n else _t[:n].rstrip() + "…"


def _mis_obras(ctx) -> list:
    """Las obras de la persona, internas incluidas: las mismas que su pantalla de Pre-Start."""
    from core import projects as P
    return P.list_projects_for_field(ctx["usuario"], grupo=ctx["grupo"], incluir_internos=True)


def _obra(entrada, ctx) -> dict:
    """La obra pedida, si es de esta persona. ⚠️ Es el único sitio por donde entra un ID del modelo."""
    pid = str((entrada or {}).get("project_id", "")).strip()
    obras = _mis_obras(ctx)
    p = next((o for o in obras if str(o.get("ID", "")).strip() == pid), None)
    if p is None:
        raise _Negado("That is not one of this person's jobs. Their jobs: "
                      + (", ".join(f"{o.get('ID')} ({o.get('Name')})" for o in obras) or "none"))
    return p


# ═════════════════════════════════════════════════════════════════
# Las consultas
# ═════════════════════════════════════════════════════════════════
def _estado_del_dia(prj, pid, ctx) -> dict:
    """Lo que esa obra le pide HOY a esta persona: Pre-Start y checklist del false car."""
    from core import falsecar as FC, prestart as PS
    g, u, n = ctx["grupo"], ctx["usuario"], ctx["nombre"]
    if not PS.hecho_hoy(pid, g):
        ps = "missing"
    else:
        ps = "needs_your_signature" if PS.pendiente_de_firma(pid, g, n, usuario=u) else "done"
    _toca = FC.pendiente_hoy(prj, g, n, u)
    if _toca:
        fc = "missing" if _toca == FC.HACER else "needs_your_signature"
    else:
        fc = "done" if FC.activo(prj, clock.today(g)) else "not_required"
    return {"pre_start": ps, "false_car_check": fc}


def _mi_dia(entrada, ctx) -> dict:
    from core import credentials as CR, projects as P, roster as R, timeclock as TC
    g, u, n = ctx["grupo"], ctx["usuario"], ctx["nombre"]
    hoy = clock.today(g)
    ses = TC.open_sessions(n, g, u)
    jornada, fichada = ses.get(TC.TIPO_GENERAL), ses.get(TC.TIPO_PROYECTO)
    obras = {str(o.get("ID", "")): o for o in _mis_obras(ctx)}
    asig = []
    try:
        asig = R.asignaciones_dia(g, u, hoy) or []
    except Exception as e:
        logger.warning("chat_tools: no se pudo leer el tablero: %s", e)
    ids = []
    if fichada and fichada.get("proyecto_id"):
        ids.append(str(fichada["proyecto_id"]))
    ids += [str(a.get("proyecto_id")) for a in asig if a.get("proyecto_id")]
    pendientes = []
    for pid in dict.fromkeys(ids):
        # La de su fichaje o su tablero es suya aunque ya no esté en su lista de asignadas.
        prj = obras.get(pid) or P.get_project(pid) or {}
        pendientes.append({"project_id": pid, "job": prj.get("Name", ""), **_estado_del_dia(prj, pid, ctx)})
    _vence = []
    for c in CR.list_for(u) or []:
        _d = CR.dias_para(c.get("ExpiryDate", ""))
        if _d is not None and _d <= 30:
            _vence.append({"credential": c.get("Type", ""), "expires": dmy(c.get("ExpiryDate", "")), "days_left": _d})
    return {"today": dmy(hoy), "weekday": hoy.strftime("%A"), "time": clock.now(g).strftime("%H:%M"),
            "person": n,
            "clocked_in": {"workday": bool(jornada),
                           "job": (fichada or {}).get("proyecto", ""),
                           "project_id": (fichada or {}).get("proyecto_id", ""),
                           "since": str((fichada or jornada or {}).get("clock_in", ""))[11:16]},
            "entry_left_open_from_a_previous_day": bool(TC.olvidos(ses)),
            "planned_today": [{"what": a.get("etiqueta", ""), "project_id": a.get("proyecto_id", ""),
                               "note": a.get("nota", "")} for a in asig],
            "jobs_today": pendientes, "credentials_expiring_soon": _vence}


def _mis_trabajos(entrada, ctx) -> dict:
    return {"jobs": [{"project_id": o.get("ID", ""), "name": o.get("Name", ""), "location": o.get("Location", ""),
                      "type": o.get("Type", ""), "status": o.get("Status", ""),
                      "progress_pct": round(_num(o.get("Progress")), 1), "start": dmy(o.get("StartDate", "")),
                      "estimated_finish": dmy(o.get("EndDateEst", "")),
                      "instructions": _corto(o.get("Instructions", ""))} for o in _mis_obras(ctx)]}


def _detalle_obra(entrada, ctx) -> dict:
    from core import alerts as AL, daily_log as DL, projects as P, stage_progress as SP, tareas as TA
    from core.projects_ui import _CAMPO_VER
    prj = _obra(entrada, ctx)
    pid = str(prj.get("ID", ""))
    etapas, siguiente = [], None
    for e in SP.detalle(pid, prj):
        _acts = e.get("actividades") or []
        _pct = SP.avance_de(_acts)
        etapas.append({"stage": e.get("nombre", ""), "done_pct": _pct})
        if siguiente is None and _pct < 100:
            siguiente = {"stage": e.get("nombre", ""),
                         "activities_left": [a.get("nombre", "") for a in _acts if _num(a.get("pct")) < 100]}
    _docs = {}
    for d in P.list_documents(pid) or []:
        if str(d.get("Type", "")) in _CAMPO_VER:
            _docs.setdefault(str(d.get("Type", "")), []).append(str(d.get("Name", "")))
    return {"project_id": pid, "name": prj.get("Name", ""), "location": prj.get("Location", ""),
            "status": prj.get("Status", ""), "progress_pct": round(_num(prj.get("Progress")), 1),
            "estimated_finish": dmy(prj.get("EndDateEst", "")), "instructions": _corto(prj.get("Instructions", "")),
            "today": _estado_del_dia(prj, pid, ctx),
            "stages": etapas, "next_up": siguiente,
            "todo_open": [{"task_id": r.get("ID", ""), "text": _corto(r.get("Text", ""))} for r in TA.pendientes(pid)],
            "open_alerts": [_corto(r.get("Message", "")) for r in AL.list_alerts(pid, "abierta")],
            "documents": _docs,
            "latest_daily_logs": [{"date": dmy(r.get("Date", "")), "by": r.get("Author", ""), "text": _corto(r.get("Text", ""))}
                                  for r in DL.partes(pid)[:MAX_PARTES]]}


def _mis_ausencias(entrada, ctx) -> dict:
    from core import ausencias as AU
    g, u = ctx["grupo"], ctx["usuario"]
    saldos = {}
    for tipo in AU.TIPOS:
        s = AU.saldo(g, u, tipo)
        saldos[AU.nombre_tipo(tipo)] = ({"no_limit": True, "days_used": s["usados"]} if s["ilimitado"] else
                                        {"days_available": max(s["disponibles"], 0), "days_used": s["usados"],
                                         "days_waiting_approval": s["pendientes"]})
    _pedidas = sorted(AU.list_group(g, usuario=u) or [], key=lambda r: str(r.get("From", "")), reverse=True)
    return {"balance": saldos,
            "requests": [{"type": AU.nombre_tipo(str(r.get("Type", ""))), "from": dmy(r.get("From", "")),
                          "to": dmy(r.get("To", "")), "days": r.get("Days", ""), "status": r.get("Status", "")}
                         for r in _pedidas[:MAX_SOLICITUDES]]}


def _mis_credenciales(entrada, ctx) -> dict:
    from core import credentials as CR
    return {"credentials": [{"type": c.get("Type", ""),
                             "expires": dmy(c.get("ExpiryDate")) if str(c.get("ExpiryDate") or "").strip() else "no expiry",
                             "status": _ESTADO_CRED.get(CR.estado(c), CR.estado(c)),
                             "days_left": CR.dias_para(c.get("ExpiryDate", ""))}
                            for c in CR.list_for(ctx["usuario"]) or []]}


_SIN_ENTRADA = {"type": "object", "properties": {}, "additionalProperties": False}
_POR_OBRA = {"type": "object", "additionalProperties": False, "required": ["project_id"],
             "properties": {"project_id": {"type": "string", "description": "The job ID, like PRJ-0027."}}}

LECTURA = [
    {"name": "get_my_day", "input_schema": _SIN_ENTRADA, "fn": _mi_dia,
     "description": "What this person has today: date and time, whether they are clocked in and where, what is planned "
                    "for them, and for each of today's jobs whether the Pre-Start and the false car check are done or "
                    "need their signature, plus credentials expiring soon. Call it first for anything about today, "
                    "such as «what do I have to do?», «what's missing?» or «where am I working?»."},
    {"name": "get_my_jobs", "input_schema": _SIN_ENTRADA, "fn": _mis_trabajos,
     "description": "The jobs this person is assigned to, with ID, location, status, progress and instructions. Call it "
                    "when they ask about their jobs or name one, to find its project_id."},
    {"name": "get_job_details", "input_schema": _POR_OBRA, "fn": _detalle_obra,
     "description": "One of their jobs in detail: stages and what is left in the next one, open To-do tasks, open "
                    "alerts, documents they can see and the latest daily logs. Call it for anything about how a job "
                    "is going or what comes next on it."},
    {"name": "get_my_absences", "input_schema": _SIN_ENTRADA, "fn": _mis_ausencias,
     "description": "Their leave balance by type and their latest requests with status. Call it for anything about "
                    "days left, annual leave, sick leave or a request they made."},
    {"name": "get_my_credentials", "input_schema": _SIN_ENTRADA, "fn": _mis_credenciales,
     "description": "Their credentials and tickets with expiry date and status. Call it for anything about their "
                    "cards, tickets or licences."},
]
_POR_NOMBRE = {h["name"]: h for h in LECTURA}


def definiciones(rol, usuario="") -> list:
    """Las herramientas de ese rol, sin nada interno. Sin persona identificada, ninguna; y por ahora
    solo el campo: la oficina es el siguiente agente del recorrido."""
    if rol != "field" or not str(usuario or "").strip():
        return []
    return [{k: v for k, v in h.items() if k != "fn"} for h in LECTURA]


def ejecutar(nombre, entrada, ctx) -> tuple:
    """`(texto, es_error)`. ⚠️ `ctx` viene de la sesión; lo que dice el modelo solo es `entrada`. Un
    fallo vuelve al modelo como texto: mejor «no pude mirarlo» que una respuesta inventada."""
    h = _POR_NOMBRE.get(str(nombre))
    if h is None:
        return f"Unknown tool: {nombre}. Available: {', '.join(_POR_NOMBRE)}.", True
    if not str((ctx or {}).get("usuario", "")).strip() or not str((ctx or {}).get("grupo", "")).strip():
        return "This person could not be identified.", True
    try:
        return json.dumps(h["fn"](entrada or {}, ctx), ensure_ascii=False, default=str), False
    except _Negado as e:
        return str(e), True
    except Exception as e:
        logger.warning("chat_tools.%s: %r", nombre, e)
        return "That could not be read right now. Say so; do not guess.", True
