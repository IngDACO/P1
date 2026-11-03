# -*- coding: utf-8 -*-
"""Lo que los asistentes pueden consultar y hacer (Field v639-v642, Management desde v643).

Hasta aquí no sabía quién le preguntaba: recibía la guía, los manuales y el cálculo abierto, y
«¿qué me falta hoy?» no tenía respuesta. Ahora puede mirar los datos de ESA persona antes de
contestar. Decisión del usuario (02/11/2026), tres niveles:

  1. VER (`LECTURA`): sus datos, y nada más.
  2. PREPARAR Y CONFIRMAR (`PREPARAR`): el parte, el aviso a la oficina y las ausencias. Se valida, se
     deja una tarjeta en la sesión y NO se escribe nada: lo hace `confirmar`, al tocar Confirm (`chat_ui`).
  3. ACTUAR SOLO (`DIRECTAS`): apuntar y marcar en To-do, y nada más: es reversible y no avisa a nadie.

⚠️ Fichar, firmar, enviar el Pre-Start o el checklist y acreditar avance NO están, ni confirmados: son
actos personales de quien los hace, y la app no acredita sola (decisión del usuario).

## Cada herramienta, con su rol (`_POR_ROL`)

Las mismas reglas para la oficina (v643), con lo suyo: la cartera, el equipo, las bandejas y el dinero
de SU grupo. ⚠️ El rol se comprueba en `ejecutar`, no solo al ofrecerlas: que el modelo pida una
herramienta de otro rol no la abre. El propietario, ninguna: ve varias empresas a la vez, y va con su
recorrido (decisión del usuario).

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
MAX_LISTA = 15            # de cada lista de la oficina: lo que cabe en una respuesta
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
    """Las obras de la persona, internas incluidas: las mismas que su pantalla de Pre-Start. Para la
    oficina, las de su grupo: `list_projects` no sale de él."""
    from core import projects as P
    if ctx.get("rol") == "administrator":
        return P.list_projects(grupo=ctx["grupo"], incluir_internos=True)
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
    # La oficina pregunta por la obra, no por su propia firma
    if ctx.get("rol") == "administrator":
        _vivo = FC.activo(prj, clock.today(g))
        return {"pre_start": "done" if PS.hecho_hoy(pid, g) else "missing",
                "false_car_check": ("not_required" if not _vivo else "done" if FC.hecho_hoy(pid, g) else "missing")}
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
    _oficina = ctx.get("rol") == "administrator"
    _docs = {}
    for d in P.list_documents(pid) or []:
        if _oficina or str(d.get("Type", "")) in _CAMPO_VER:
            _docs.setdefault(str(d.get("Type", "")), []).append(str(d.get("Name", "")))
    _extra = {}
    if _oficina:
        from core import admin_digest as AD
        _nom = AD.nombres_usuarios()
        _extra = {"client": prj.get("Client", ""), "assigned": _asignados(prj, _nom),
                  "hours_worked": round(_num(P.project_hours_bulk(ctx["grupo"]).get(pid)), 1),
                  "days_late": round(_num(AD._base(ctx["grupo"])["delays"].get(pid)))}
    return {**_extra, "project_id": pid, "name": prj.get("Name", ""), "location": prj.get("Location", ""),
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


# ═════════════════════════════════════════════════════════════════
# La oficina (v643): su grupo, y lo que ya ve en sus pantallas
# ═════════════════════════════════════════════════════════════════
def _asignados(prj, nom) -> list:
    return [nom.get(x.strip(), x.strip()) for x in str(prj.get("FieldAssigned", "")).split(";") if x.strip()]


def _cartera(entrada, ctx) -> dict:
    from core import admin_digest as AD
    b = AD._base(ctx["grupo"])
    nom = AD.nombres_usuarios()
    filas = b["proys"] if entrada.get("include_finished") else b["activos"]
    jobs = [
        {"project_id": str(p.get("ID", "")), "name": p.get("Name", ""), "client": p.get("Client", ""),
         "status": p.get("Status", ""), "progress_pct": round(_num(p.get("Progress")), 1),
         "estimated_finish": dmy(p.get("EndDateEst", "")), "assigned": _asignados(p, nom),
         "hours_worked": round(_num(b["horas"].get(str(p.get("ID", "")))), 1),
         "days_late": round(_num(b["delays"].get(str(p.get("ID", ""))))),
         "open_alerts": int(_num(b["alarmas"].get(str(p.get("ID", "")))))} for p in filas]
    # ⚠️ El recuento va hecho: el modelo contó 4 atrasadas con 5 delante (examen real)
    return {"count": len(jobs), "late_jobs": sum(1 for j in jobs if j["days_late"] > 0), "jobs": jobs}


def _equipo(entrada, ctx) -> dict:
    from core import admin_digest as AD, auth, ausencias as AU, credentials as CR, roster as R, timeclock as TC
    g = ctx["grupo"]
    hoy = clock.today(g)
    dia = _parse_date(entrada.get("date")) if entrada.get("date") else hoy
    if not dia:
        raise _Negado("The date has to be YYYY-MM-DD.")
    nom = AD.nombres_usuarios()
    fichados = {}
    # Quién está fichado solo tiene sentido hoy: de otro día se responde con lo planificado
    if dia == hoy:
        for s in TC.open_now(g):
            u = s.get("usuario") or s.get("nombre")
            e = fichados.setdefault(u, {"who": nom.get(u, s.get("nombre") or u), "job": "", "project_id": "", "since": ""})
            _ci = str(s.get("clock_in", ""))
            if s.get("tipo") == TC.TIPO_PROYECTO:
                e.update(job=s.get("proyecto", ""), project_id=s.get("proyecto_id", ""), since=_ci[11:16])
            elif not e["since"]:
                e["since"] = _ci[11:16]
            if _ci[:10] != hoy.isoformat():
                e["left_open_from_a_previous_day"] = True
    planificado = []
    for u in auth.list_users(g):
        if str(u.get("Role", "")).lower() != "field":
            continue
        _us = str(u.get("User", ""))
        for a in R.asignaciones_dia(g, _us, dia) or []:
            planificado.append({"who": nom.get(_us, _us), "what": a.get("etiqueta", ""),
                                "project_id": a.get("proyecto_id", ""), "note": a.get("nota", "")})
    return {"date": dmy(dia), "clocked_in_now": list(fichados.values()), "planned": planificado,
            "absent": [{"who": nom.get(str(r.get("User", "")), r.get("Name", "")), "type": AU.nombre_tipo(str(r.get("Type", ""))),
                        "from": dmy(r.get("From", "")), "to": dmy(r.get("To", "")), "status": r.get("Status", "")}
                       for r in AU.ausentes_en(g, dia)],
            "credentials_expiring": [{"who": nom.get(str(c.get("usuario", "")), c.get("usuario", "")), "credential": c.get("tipo", ""),
                                      "expires": dmy(c.get("vencimiento", "")), "days_left": c.get("dias")}
                                     for c in CR.expiring(g)[:MAX_LISTA]]}


def _bandejas(entrada, ctx) -> dict:
    from core import admin_digest as AD, alerts as AL, ausencias as AU, correcciones as CO, falsecar as FC
    g = ctx["grupo"]
    nom = AD.nombres_usuarios()
    _quien = lambda r: nom.get(str(r.get("User", "")), r.get("Name", ""))        # noqa: E731
    _dias = FC.dias_sin_registro(g)
    _als = [r for r in AL._alarmas_visibles() if str(r.get("Group", "")) == str(g) and str(r.get("Status", "")) == "abierta"]
    _obras = {str(o.get("ID", "")): o.get("Name", "") for o in _mis_obras(ctx)}
    return {
        "absences_to_approve": [{"id": r.get("ID", ""), "who": _quien(r), "type": AU.nombre_tipo(str(r.get("Type", ""))),
                                 "from": dmy(r.get("From", "")), "to": dmy(r.get("To", "")), "days": r.get("Days", ""),
                                 "reason": _corto(r.get("Reason", ""))} for r in AU.pendientes(g)[:MAX_LISTA]],
        "time_fixes_to_review": [{"id": r.get("ID", ""), "who": _quien(r), "job": r.get("Project", ""), "field": r.get("Field", ""),
                                  "was": r.get("OldValue", ""), "now": r.get("NewValue", ""), "reason": _corto(r.get("Reason", "")),
                                  "already_on_payslip": r.get("PayslipCovers", "")} for r in CO.pendientes(g)[:MAX_LISTA]],
        "sick_days_over_balance": [{"id": x["id"], "who": x["nombre"], "days": len(x["dias"])} for x in AU.excesos_por_decidir(g)[:MAX_LISTA]],
        "open_alerts": [{"id": r.get("ID", ""), "job": _obras.get(str(r.get("ProjectID", "")), r.get("ProjectID", "")),
                         "project_id": r.get("ProjectID", ""), "message": _corto(r.get("Message", "")),
                         "from": nom.get(str(r.get("CreatedBy", "")), r.get("CreatedBy", "")), "date": dmy(r.get("Date", ""))}
                        for r in _als[:MAX_LISTA]],
        "days_worked_without_records": {"count": len(_dias), "latest": [
            {"date": dmy(x["fecha"]), "job": x["nombre"], "project_id": x["pid"], "missing": x["falta"]} for x in _dias[:MAX_LISTA]]}}


def _dinero(entrada, ctx) -> dict:
    from core import expenses as E, finance as F, invoices as INV
    g = ctx["grupo"]
    if entrada.get("project_id"):
        prj = _obra(entrada, ctx)
        pid = str(prj.get("ID", ""))
        c, r = E.project_cost(pid, g), F.project_revenue(pid, g, prj)
        return {"project_id": pid, "name": prj.get("Name", ""), "budget": c["presupuesto"], "spent": c["total"], "materials": c["compras"],
                "labour": c["mano_obra"], "committed_orders": c["comprometido"], "pct_of_budget": c["pct"], "over_budget": c["over"],
                "will_go_over_with_orders": c["over_comp"], "estimated_revenue": r.get("ingreso"), "estimated_profit": r.get("ganancia"),
                "pending_to_invoice": round(_num(INV.pendiente_de_facturar(pid, g, prj)), 2)}
    hoy = clock.today(g)
    d0 = _parse_date(entrada.get("from")) if entrada.get("from") else hoy.replace(day=1)
    d1 = _parse_date(entrada.get("to")) if entrada.get("to") else hoy
    if not d0 or not d1 or d1 < d0:
        raise _Negado("The period needs valid YYYY-MM-DD dates, with «to» on or after «from».")
    p = F.pnl(g, d0, d1)
    rent = F.group_profitability(g)
    _filas = sorted(rent["rows"], key=lambda x: _num(x.get("ganancia")))
    _nombres = {str(o.get("ID", "")): o.get("Name", "") for o in _mis_obras(ctx)}
    _por = sorted(((k, _num(v)) for k, v in INV.pendiente_por_proyecto(g).items() if _num(v) > 0), key=lambda x: -x[1])
    _abiertas = [f for f in INV.list_facturas(g) if INV.estado_cobro(f) not in ("cobrada", "anulada")]
    return {"period": {"from": dmy(d0), "to": dmy(d1)},
            # ⚠️ Dijo «no hubo horas en octubre» con 180 h en esa obra: un P&L a 0 no es que no se trabajara
            "profit_and_loss_counts": "Only invoices issued, payslips already generated and purchases, by date. Hours worked with no "
                                      "payslip yet are NOT in it: a 0 here does not mean nobody worked. Labour from hours is in the job costs.",
            "profit_and_loss": {"invoiced": p["facturado"], "collected": p["cobrado"], "to_collect": p["por_cobrar"], "overdue": p["vencido"],
                                "payroll_cost": p["costo_nomina"], "purchases": p["compras"], "total_cost": p["costo_total"],
                                "profit": p["ganancia"], "payroll_to_pay": p["por_pagar"]},
            "all_time_estimate": rent["totales"],
            "jobs_by_estimated_profit_lowest_first": [{"project_id": x.get("id"), "name": x.get("nombre"), "cost": x.get("costo"),
                                                       "estimated_revenue": x.get("ingreso"), "estimated_profit": x.get("ganancia"),
                                                       "margin_pct": x.get("margen_ing")} for x in _filas[:MAX_LISTA]],
            "over_budget": E.over_budget(g),
            "pending_to_invoice": [{"project_id": k, "name": _nombres.get(k, k), "amount": round(v, 2)} for k, v in _por[:MAX_LISTA]],
            "open_invoices": [{"number": f.get("Number", ""), "client": f.get("ClientName", ""), "total": f.get("Total", ""),
                               "collected": f.get("Collected", ""), "due": dmy(f.get("ExpiryDate", "")), "status": INV.estado_cobro(f)}
                              for f in _abiertas[:MAX_LISTA]]}


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
                    "asks you to add a task to a job. Not for things they only want you to remember."},
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
_DETALLE = next(h for h in LECTURA if h["name"] == "get_job_details")
LECTURA_OFICINA = [
    {"name": "get_portfolio", "fn": _cartera,
     "input_schema": {"type": "object", "additionalProperties": False,
                      "properties": {"include_finished": {"type": "boolean", "description": "Also finished and cancelled jobs."}}},
     "description": "All the company's jobs: status, progress, finish date, who is assigned, hours, days late and open alerts. "
                    "Call it first for anything about the jobs as a whole: which is furthest behind, who is on what, how many are running."},
    _DETALLE,
    {"name": "get_team", "fn": _equipo,
     "input_schema": {"type": "object", "additionalProperties": False,
                      "properties": {"date": {"type": "string", "description": "YYYY-MM-DD. Defaults to today."}}},
     "description": "The team on a day: who is clocked in now and where (today only), who is planned on what, who is absent, and "
                    "credentials expiring. Call it for anything about people: who is working, who is off, who is free."},
    {"name": "get_inbox", "fn": _bandejas, "input_schema": _SIN_ENTRADA,
     "description": "What is waiting for the office: absences to approve, time fixes to review, sick days over balance to decide, open "
                    "alerts, and days worked with no Pre-Start or false car check. Call it for anything about what is pending."},
    {"name": "get_money", "fn": _dinero,
     "input_schema": {"type": "object", "additionalProperties": False,
                      "properties": {"project_id": {"type": "string", "description": "One job, like PRJ-0027. Without it, the whole company."},
                                     "from": {"type": "string", "description": "YYYY-MM-DD. Defaults to the 1st of this month."},
                                     "to": {"type": "string", "description": "YYYY-MM-DD. Defaults to today."}}},
     "description": "The money. For one job: budget, spent, materials, labour, estimated profit and pending to invoice. For the company: "
                    "profit and loss for a period, jobs by profit, over budget, pending to invoice and open invoices. Call it for anything "
                    "about costs, budget, invoices or margin."},
]
_POR_ROL = {"field": TODAS, "administrator": LECTURA_OFICINA}


def definiciones(rol, usuario="") -> list:
    """Las herramientas de ese rol, sin nada interno. Sin persona identificada, ninguna; el propietario
    tampoco: va con su recorrido."""
    if not str(usuario or "").strip():
        return []
    return [{k: v for k, v in h.items() if k != "fn"} for h in _POR_ROL.get(rol, [])]


def ejecutar(nombre, entrada, ctx) -> tuple:
    """`(texto, es_error)`. ⚠️ `ctx` viene de la sesión; lo que dice el modelo solo es `entrada`. Un
    fallo vuelve al modelo como texto: mejor «no pude mirarlo» que una respuesta inventada."""
    # ⚠️ Las de SU rol: ofrecerlas no basta, un modelo puede pedir una que no se le ofreció
    _suyas = _POR_ROL.get((ctx or {}).get("rol", ""), [])
    h = next((x for x in _suyas if x["name"] == str(nombre)), None)
    if h is None:
        return f"Unknown tool: {nombre}. Available: {', '.join(x['name'] for x in _suyas)}.", True
    if not str((ctx or {}).get("usuario", "")).strip() or not str((ctx or {}).get("grupo", "")).strip():
        return "This person could not be identified.", True
    try:
        return json.dumps(h["fn"](entrada or {}, ctx), ensure_ascii=False, default=str), False
    except _Negado as e:
        return str(e), True
    except Exception as e:
        logger.warning("chat_tools.%s: %r", nombre, e)
        return "That could not be read right now. Say so; do not guess.", True
