# -*- coding: utf-8 -*-
"""Lo que el Field assistant puede consultar y hacer (v639-v640).

Hasta aquí no sabía quién le preguntaba: recibía la guía, los manuales y el cálculo abierto, y
«¿qué me falta hoy?» no tenía respuesta. Ahora puede mirar los datos de ESA persona antes de
contestar. Decisión del usuario (02/11/2026), tres niveles:

  1. VER (`LECTURA`): sus datos, y nada más.
  2. PREPARAR Y CONFIRMAR (`PREPARAR`): el parte, el aviso a la oficina y las ausencias. Se valida, se
     deja una tarjeta en la sesión y NO se escribe nada: lo hace `confirmar`, al tocar Confirm (`chat_ui`).
  3. ACTUAR SOLO (`DIRECTAS`): apuntar y marcar en To-do, y nada más: es reversible y no avisa a nadie.

⚠️ Fichar, firmar, enviar el Pre-Start o el checklist y acreditar avance NO están, ni confirmados: son
actos personales de quien los hace, y la app no acredita sola (decisión del usuario).

## ⚠️ La identidad no la dice el modelo

Ninguna herramienta recibe un usuario: sale de `ctx`, que la app arma con la SESIÓN. El modelo solo
elige QUÉ mirar y `project_id`, que se comprueba contra las obras de la persona (`_obra`). Así, ni un
error del modelo ni un texto escrito en una tarea pueden enseñar los datos de otro.

## ⚠️ Lo que devuelven son DATOS

Tareas, partes y avisos los escribe otra gente: el texto llega aquí tal cual y la persona del
asistente dice que nunca es una instrucción (`chat_agent._PERSONA`).

Por eso una herramienta que cambia algo solo se usa si la persona lo pidió en la conversación.

## Lo que no se ve

Lo que el campo no ve en su pantalla no sale de aquí: las nóminas no están, y los documentos pasan
por el mismo filtro que Files (`_CAMPO_VER`).
"""
import json
import logging
import uuid

from core import clock
from core.i18n import t
from core.num import dmy, num as _num, parse_date as _parse_date

logger = logging.getLogger(__name__)

MAX_PARTES = 3            # los últimos partes de la obra: para saber por dónde va, no el archivo
MAX_CARACTERES = 400      # de cada texto largo (un parte, las instrucciones)
MAX_SOLICITUDES = 8       # las últimas ausencias
# `credentials.estado` devuelve el dato en español, que es con lo que se compara en la app
MAX_DIRECTAS = 5          # apuntar o marcar, por pregunta: un error del modelo no vacía la lista
MAX_TARJETAS = 3          # esperando un toque a la vez
MAX_AVISO = 1000          # lo mismo que manda la pantalla del parte a la oficina
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


# ═════════════════════════════════════════════════════════════════
# Nivel 3 — lo que hace solo: reversible y sin avisar a nadie
# ═════════════════════════════════════════════════════════════════
def _una_directa(ctx) -> None:
    ctx["_directas"] = ctx.get("_directas", 0) + 1
    if ctx["_directas"] > MAX_DIRECTAS:
        raise _Negado("That is enough changes for one go. Tell the person what is left and stop.")


def _apuntar_tarea(entrada, ctx) -> dict:
    from core import tareas as TA
    prj = _obra(entrada, ctx)
    _una_directa(ctx)
    ok, r = TA.crear(str(prj.get("ID", "")), ctx["grupo"], entrada.get("text"), ctx["usuario"])
    if not ok:
        raise _Negado(str(r))
    return {"done": True, "task_id": r, "job": prj.get("Name", "")}


def _marcar_tarea(entrada, ctx) -> dict:
    from core import tareas as TA
    prj = _obra(entrada, ctx)
    _una_directa(ctx)
    ok, r = TA.marcar(str(entrada.get("task_id", "")).strip(), str(prj.get("ID", "")),
                      bool(entrada.get("done", True)), ctx["usuario"])
    if not ok:
        raise _Negado(str(r))
    return {"done": True, "job": prj.get("Name", "")}


# ═════════════════════════════════════════════════════════════════
# Nivel 2 — lo que prepara: valida y deja una tarjeta, SIN escribir
# ═════════════════════════════════════════════════════════════════
def _tarjeta(ctx, tipo, titulo, detalle, datos) -> dict:
    lista = ctx.get("acciones")
    if lista is None:
        raise _Negado("Nothing can be prepared here.")
    if any(a.get("tipo") == tipo and a.get("datos") == datos for a in lista):
        return {"prepared": True, "status": "NOT DONE YET", "next": "That card is already waiting for them."}
    if len(lista) >= MAX_TARJETAS:
        raise _Negado("Several cards are already waiting. Ask the person to confirm or cancel them first.")
    lista.append({"id": uuid.uuid4().hex[:8], "tipo": tipo, "titulo": titulo, "detalle": detalle, "datos": datos})
    return {"prepared": True, "status": "NOT DONE YET",
            "next": "They now see a card with Confirm and Cancel, and nothing happens until they press Confirm. "
                    "Tell them that in one line. Do not say it is done."}


def _preparar_parte(entrada, ctx) -> dict:
    from core import daily_log as DL
    prj = _obra(entrada, ctx)
    txt = str(entrada.get("text") or "").strip()
    if not txt:
        raise _Negado("The daily log is empty: ask them what they did.")
    if len(txt) > DL.MAX_TEXTO:
        raise _Negado(f"That is too long for a daily log (limit {DL.MAX_TEXTO} characters): shorten it.")
    hoy = clock.today(ctx["grupo"])
    dia = _parse_date(entrada.get("date")) if entrada.get("date") else hoy
    if not dia or dia > hoy:
        raise _Negado("The date has to be today or an earlier day, as YYYY-MM-DD.")
    return _tarjeta(ctx, "parte", t("Daily log · {o} · {d}", o=prj.get("Name", ""), d=dmy(dia)), txt,
                    {"project_id": str(prj.get("ID", "")), "text": txt, "date": dia.isoformat()})


def _preparar_aviso(entrada, ctx) -> dict:
    prj = _obra(entrada, ctx)
    txt = str(entrada.get("message") or "").strip()
    if not txt:
        raise _Negado("The alert is empty: ask them what the problem is.")
    if len(txt) > MAX_AVISO:
        raise _Negado(f"That is too long for an alert (limit {MAX_AVISO} characters): shorten it.")
    return _tarjeta(ctx, "aviso", t("Alert to the office · {o}", o=prj.get("Name", "")), txt,
                    {"project_id": str(prj.get("ID", "")), "message": txt})


def _preparar_ausencia(entrada, ctx) -> dict:
    from core import ausencias as AU
    tipo = {"annual_leave": AU.VACACIONES, "day_off": AU.LIBRE, "sick_leave": AU.ENFERMEDAD}.get(str(entrada.get("type")))
    if tipo is None:
        raise _Negado("The type has to be annual_leave, day_off or sick_leave.")
    d0, d1 = _parse_date(entrada.get("from")), _parse_date(entrada.get("to") or entrada.get("from"))
    if not d0 or not d1:
        raise _Negado("The dates have to be YYYY-MM-DD: ask them if they are not clear.")
    findes = bool(entrada.get("include_weekends", False))
    _err = AU.problema_solicitud(ctx["grupo"], ctx["usuario"], tipo, d0, d1, findes)
    if _err:
        raise _Negado(str(_err))
    _n = len(AU.dias_del_rango(d0, d1, findes))
    motivo = str(entrada.get("reason") or "").strip()
    _ex = AU.exceso(ctx["grupo"], ctx["usuario"], tipo, _n)
    _lineas = [t("{a} to {b} · {n} day(s)", a=dmy(d0), b=dmy(d1), n=_n)]
    if motivo:
        _lineas.append(motivo)
    if _ex:
        _lineas.append(t("{n} day(s) over your balance: the office decides how they are paid.", n=_ex))
    return _tarjeta(ctx, "ausencia", AU.nombre_tipo(tipo), "\n".join(_lineas),
                    {"tipo": tipo, "from": d0.isoformat(), "to": d1.isoformat(), "reason": motivo, "weekends": findes})


def confirmar(accion, ctx) -> tuple:
    """Hace lo que la tarjeta dice: `(ok, mensaje)`. Solo lo llama el toque de Confirm (`chat_ui`).
    ⚠️ Con la identidad de la SESIÓN, y la obra se vuelve a comprobar: la cuadrilla pudo cambiar."""
    d = (accion or {}).get("datos") or {}
    g, u, n = ctx.get("grupo", ""), ctx.get("usuario", ""), ctx.get("nombre", "")
    if not str(u).strip() or not str(g).strip():
        return False, t("This person could not be identified.")
    tipo = (accion or {}).get("tipo")
    try:
        if tipo == "parte":
            from core import daily_log as DL
            prj = _obra(d, ctx)
            ok, r = DL.crear(str(prj.get("ID", "")), g, d.get("text"), u, dia=d.get("date"))
            return (True, t("Daily log saved. Open it in **Daily log** to confirm what it proposes.")) if ok else (False, str(r))
        if tipo == "aviso":
            from core import alerts
            prj = _obra(d, ctx)
            ok, r = alerts.report_problem(str(prj.get("ID", "")), g, d.get("message"), u, str(prj.get("Name", "")))
            return (True, t("Sent to the office ({a}).", a=r)) if ok else (False, str(r))
        if tipo == "ausencia":
            from core import ausencias as AU, ausencias_ui as AUI
            ok, r, aviso = AUI.registrar(g, u, n, d.get("tipo"), d.get("from"), d.get("to"), d.get("reason", ""), bool(d.get("weekends")))
            if not ok:
                return False, str(r)
            _m = (t("{x} recorded ({i}).", x=AU.nombre_tipo(d.get("tipo")), i=r) if not AU.TIPOS[d.get("tipo")]["aprobacion"]
                  else t("Request sent ({i}). We will let you know when it is resolved.", i=r))
            return True, _m + (" " + aviso if aviso else "")
    except _Negado as e:
        return False, str(e)
    except Exception as e:
        logger.warning("chat_tools.confirmar(%s): %r", tipo, e)
        return False, t("That could not be saved. Try again in a minute.")
    return False, t("This action is not recognised.")


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
_ID_OBRA = {"type": "string", "description": "The job ID, like PRJ-0027."}
DIRECTAS = [
    {"name": "add_todo", "fn": _apuntar_tarea,
     "input_schema": {"type": "object", "additionalProperties": False, "required": ["project_id", "text"],
                      "properties": {"project_id": _ID_OBRA, "text": {"type": "string", "description": "One line."}}},
     "description": "Add a task to a job's To-do list, straight away and with no confirmation. Call it when the person "
                    "asks you to note, add or remember something for a job."},
    {"name": "mark_todo", "fn": _marcar_tarea,
     "input_schema": {"type": "object", "additionalProperties": False, "required": ["project_id", "task_id"],
                      "properties": {"project_id": _ID_OBRA,
                                     "task_id": {"type": "string", "description": "Like TSK-0012, from get_job_details."},
                                     "done": {"type": "boolean", "description": "False to reopen it. Defaults to true."}}},
     "description": "Mark a To-do task as done, or reopen it, straight away and with no confirmation. Call it when the "
                    "person says a task is done or asks to reopen it."},
]
PREPARAR = [
    {"name": "prepare_daily_log", "fn": _preparar_parte,
     "input_schema": {"type": "object", "additionalProperties": False, "required": ["project_id", "text"],
                      "properties": {"project_id": _ID_OBRA, "text": {"type": "string", "description": "What they said they did, in their own words."},
                                     "date": {"type": "string", "description": "YYYY-MM-DD, only if it is not for today."}}},
     "description": "Prepare the person's daily log for a job. It shows them a card to confirm and saves nothing yet. Call "
                    "it when they tell you what they did and ask you to write it up. Add nothing they did not say."},
    {"name": "prepare_office_alert", "fn": _preparar_aviso,
     "input_schema": {"type": "object", "additionalProperties": False, "required": ["project_id", "message"],
                      "properties": {"project_id": _ID_OBRA, "message": {"type": "string", "description": "The problem, clear and short."}}},
     "description": "Prepare an alert to the office about a problem on a job. It shows them a card to confirm and sends "
                    "nothing yet. Call it when they ask you to tell the office about a problem."},
    {"name": "prepare_absence", "fn": _preparar_ausencia,
     "input_schema": {"type": "object", "additionalProperties": False, "required": ["type", "from"],
                      "properties": {"type": {"type": "string", "enum": ["annual_leave", "day_off", "sick_leave"]},
                                     "from": {"type": "string", "description": "YYYY-MM-DD."},
                                     "to": {"type": "string", "description": "YYYY-MM-DD. Defaults to the same day."},
                                     "reason": {"type": "string"},
                                     "include_weekends": {"type": "boolean", "description": "Only if those days are worked."}}},
     "description": "Prepare a day off, annual leave or sick leave. It checks the dates and the balance and shows them a "
                    "card to confirm, and records nothing yet. Call it when they ask for time off or say they are sick."},
]
TODAS = LECTURA + DIRECTAS + PREPARAR
_POR_NOMBRE = {h["name"]: h for h in TODAS}


def definiciones(rol, usuario="") -> list:
    """Las herramientas de ese rol, sin nada interno. Sin persona identificada, ninguna; y por ahora
    solo el campo: la oficina es el siguiente agente del recorrido."""
    if rol != "field" or not str(usuario or "").strip():
        return []
    return [{k: v for k, v in h.items() if k != "fn"} for h in TODAS]


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
