# -*- coding: utf-8 -*-
"""El parte de horas y las ausencias pagadas, a Xero Payroll AU (v490, fase 2.3-B).

Decisiones del usuario: **horas y permisos** (las ausencias pagadas que COPEX ya aprueba
van también), el parte llega en **borrador**, cada usuario se **empareja solo y se
confirma** una vez, y un parte que ya existe se **actualiza solo si sigue en borrador**.

## Lo que la especificación de Xero obligó a cambiar respecto al parte de v484
1. ⚠️ **Las ausencias NO van en el parte.** Una línea de parte solo admite un
   *EarningsRate*; vacaciones y bajas son *LeaveTypes* y se registran como
   *LeaveApplications* (que, creadas por la API, quedan PROGRAMADAS: aprobadas para
   pagarse). El CSV de v484 las ponía como líneas; aquí se separan.
2. ⚠️ **El periodo no es libre**: las fechas del parte tienen que coincidir EXACTAMENTE con
   un periodo del calendario de nómina del empleado, o Xero lo rechaza. Por eso el
   periodo sale del calendario de Xero, no de dos fechas elegidas a mano.
3. ⚠️ **Un empleado de Xero AU no tiene número**: solo nombre y email. El emparejado se
   guarda por empresa y por ORGANIZACIÓN (si se reconecta a otra, no vale).

## Una definición de «qué se paga»
Las horas salen de `contable.partes` — la misma función del CSV, que a su vez usa la
jornada fichada y `ausencias.horas_pagadas_dia` (el criterio de v432). Si Xero recibiera
otra cuenta, la nómina de Xero y la de COPEX pagarían distinto sin que nada lo delatara.

La hora ordinaria usa el `OrdinaryEarningsRateID` de CADA empleado en Xero, no un nombre:
casar por nombre es frágil y cada persona puede tener su propio tipo ordinario.
"""
import calendar as _cal
import datetime as _dt
import logging

from core import contable
from core import xero as X
from core.i18n import t
from core.num import num as _num, parse_date as _parse_date

logger = logging.getLogger(__name__)

BORRADOR = "DRAFT"
_DIAS_TIPO = {"WEEKLY": 7, "FORTNIGHTLY": 14, "FOURWEEKLY": 28}
_PERIODOS_ATRAS = 3


# ─────────────────────────────────────────────────────────────────────────────
# Fechas en el formato de Xero
# ─────────────────────────────────────────────────────────────────────────────
def a_ms(d) -> str:
    """date → `/Date(ms+0000)/`, el formato de fecha que usa Payroll AU (medianoche UTC)."""
    d = _parse_date(d) if not isinstance(d, _dt.date) else d
    base = _dt.datetime(d.year, d.month, d.day, tzinfo=_dt.timezone.utc)
    return f"/Date({int(base.timestamp() * 1000)}+0000)/"


def de_ms(valor):
    """`/Date(ms+0000)/` o `YYYY-MM-DD` → date (o None).

    ⚠️ Delega en `xero.de_fecha`: al traer el cobrado de una factura (v495) hacía falta
    el mismo parser, y dos copias de la misma fecha divergen (v323).
    """
    return X.de_fecha(valor)


# ─────────────────────────────────────────────────────────────────────────────
# Periodos de un calendario de nómina (función PURA)
# ─────────────────────────────────────────────────────────────────────────────
def _suma_meses(d: _dt.date, meses: int) -> _dt.date:
    m = d.month - 1 + meses
    anio, mes = d.year + m // 12, m % 12 + 1
    return _dt.date(anio, mes, min(d.day, _cal.monthrange(anio, mes)[1]))


def _fin_de_mes(d: _dt.date) -> _dt.date:
    return _dt.date(d.year, d.month, _cal.monthrange(d.year, d.month)[1])


def periodo_de(tipo: str, inicio: _dt.date):
    """(inicio, fin) del periodo que EMPIEZA en `inicio`, o None si el tipo no se admite."""
    tipo = str(tipo or "").upper()
    if tipo in _DIAS_TIPO:
        return inicio, inicio + _dt.timedelta(days=_DIAS_TIPO[tipo] - 1)
    if tipo == "MONTHLY":
        return inicio, _suma_meses(inicio, 1) - _dt.timedelta(days=1)
    if tipo == "QUARTERLY":
        return inicio, _suma_meses(inicio, 3) - _dt.timedelta(days=1)
    if tipo == "TWICEMONTHLY":
        if inicio.day == 1:
            return inicio, _dt.date(inicio.year, inicio.month, 15)
        if inicio.day == 16:
            return inicio, _fin_de_mes(inicio)
    return None


def _anterior(tipo: str, inicio: _dt.date):
    tipo = str(tipo or "").upper()
    if tipo in _DIAS_TIPO:
        return inicio - _dt.timedelta(days=_DIAS_TIPO[tipo])
    if tipo == "MONTHLY":
        return _suma_meses(inicio, -1)
    if tipo == "QUARTERLY":
        return _suma_meses(inicio, -3)
    if tipo == "TWICEMONTHLY":
        if inicio.day == 16:
            return _dt.date(inicio.year, inicio.month, 1)
        previo = inicio - _dt.timedelta(days=1)
        return _dt.date(previo.year, previo.month, 16)
    return None


def periodos(calendario: dict, atras: int = _PERIODOS_ATRAS) -> list:
    """Los periodos que se ofrecen de un calendario: el PRÓXIMO y los `atras` anteriores.

    `[{inicio, fin, proximo}]`, del más reciente al más viejo. `StartDate` de Xero es el
    inicio del periodo que viene; los anteriores se cuentan hacia atrás desde ahí.
    ⚠️ Un tipo que no se sabe calcular devuelve [] (se dice en pantalla), en vez de
    inventar fechas que Xero va a rechazar.
    """
    inicio = de_ms(calendario.get("StartDate"))
    tipo = calendario.get("CalendarType")
    if not inicio or periodo_de(tipo, inicio) is None:
        return []
    out, actual = [], inicio
    for k in range(atras + 1):
        rango = periodo_de(tipo, actual)
        if rango is None:
            break
        out.append({"inicio": rango[0], "fin": rango[1], "proximo": k == 0})
        actual = _anterior(tipo, actual)
        if actual is None:
            break
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Emparejado de personas (función PURA + guardado)
# ─────────────────────────────────────────────────────────────────────────────
def _cf(s) -> str:
    return " ".join(str(s or "").split()).casefold()


def nombre_empleado(e: dict) -> str:
    return " ".join(x for x in (str(e.get("FirstName", "")).strip(),
                                str(e.get("LastName", "")).strip()) if x)


def propuesta_detallada(usuarios: list, empleados: list) -> dict:
    """{usuario: {"id", "por", "motivo"}} — la pareja propuesta y POR QUÉ (v497).

    `por` = "email" | "nombre" cuando hay pareja. Si no la hay, `motivo` dice cuál de
    los cinco casos es, para que el administrador sepa qué arreglar en vez de mirar un
    «— not in Xero —» mudo: el dato que falta suele estar en COPEX (un correo), no en Xero.

    ⚠️ Solo parejas ÚNICAS: si dos empleados de Xero comparten email o nombre (o dos
    usuarios de COPEX apuntan al mismo), no se propone nada. Adivinar ahí pagaría las
    horas de una persona a otra; es mejor que el administrador lo elija.
    """
    por_email, por_nombre = {}, {}
    for e in empleados:
        if _cf(e.get("Email")):
            por_email.setdefault(_cf(e.get("Email")), []).append(e["EmployeeID"])
        por_nombre.setdefault(_cf(nombre_empleado(e)), []).append(e["EmployeeID"])
    out = {}
    for u in usuarios:
        login = str(u.get("User", ""))
        email, nombre = _cf(u.get("Email")), _cf(u.get("Name"))
        cand = por_email.get(email) if email else None
        if cand and len(cand) == 1:
            out[login] = {"id": cand[0], "por": "email", "motivo": ""}
            continue
        ambiguo_email = bool(cand and len(cand) > 1)
        cand2 = por_nombre.get(nombre) if nombre else None
        if cand2 and len(cand2) == 1:
            out[login] = {"id": cand2[0], "por": "nombre", "motivo": ""}
            continue
        if ambiguo_email:
            motivo = "email_repetido"          # dos empleados de Xero con ese correo
        elif cand2 and len(cand2) > 1:
            motivo = "nombre_repetido"         # dos empleados de Xero se llaman igual
        elif not email:
            motivo = "sin_email"               # en COPEX no tiene correo: es lo que falta
        else:
            motivo = "no_esta"                 # su correo y su nombre no están en Xero
        out[login] = {"id": "", "por": "", "motivo": motivo}
    # ⚠️ Dos personas de COPEX que caen en el MISMO empleado: ninguna se propone.
    ids = [v["id"] for v in out.values() if v["id"]]
    repetidos = {i for i in ids if ids.count(i) > 1}
    for v in out.values():
        if v["id"] in repetidos:
            v.update({"id": "", "por": "", "motivo": "mismo_empleado"})
    return out


def propuesta(usuarios: list, empleados: list) -> dict:
    """{usuario: EmployeeID} que se PROPONE. DELEGA en `propuesta_detallada` (v497):
    una sola definición de cómo se empareja (v323)."""
    return {k: v["id"] for k, v in propuesta_detallada(usuarios, empleados).items() if v["id"]}


def emparejado(grupo: str, tenant_id: str) -> dict:
    """{usuario: EmployeeID} CONFIRMADO para esta organización. Vacío si se reconectó a otra."""
    guardado = contable.mapa(grupo).get("xero_empleados") or {}
    if not isinstance(guardado, dict) or guardado.get("tenant") != tenant_id:
        return {}
    return {str(k): str(v) for k, v in (guardado.get("map") or {}).items() if v}


def guardar_emparejado(grupo: str, tenant_id: str, mapa_nuevo: dict) -> tuple:
    # ⚠️ Solo esta clave (v492): antes se escribía `mapa()` entero y se congelaban en
    # el grupo todos los valores contables de fábrica.
    return contable.guardar_claves(grupo, {"xero_empleados": {
        "tenant": tenant_id,
        "map": {str(k): str(v) for k, v in (mapa_nuevo or {}).items() if v}}})


# ─────────────────────────────────────────────────────────────────────────────
# Lo que se manda (funciones PURAS)
# ─────────────────────────────────────────────────────────────────────────────
def dias_del_periodo(inicio: _dt.date, fin: _dt.date) -> list:
    return [inicio + _dt.timedelta(days=i) for i in range((fin - inicio).days + 1)]


def parte_de(empleado_id: str, rate_id: str, inicio, fin, horas_por_dia: dict) -> dict:
    """El parte tal como lo pide `POST /Timesheets`. `NumberOfUnits` = UNA entrada por
    día del periodo y EN ORDEN — por eso v484 hizo el CSV ancho."""
    unidades = [round(_num((horas_por_dia or {}).get(d)), 2) for d in dias_del_periodo(inicio, fin)]
    return {"EmployeeID": empleado_id, "StartDate": a_ms(inicio), "EndDate": a_ms(fin),
            "Status": BORRADOR,
            "TimesheetLines": [{"EarningsRateID": rate_id, "NumberOfUnits": unidades}]}


def tramos(horas_por_dia: dict) -> list:
    """Días con horas agrupados en tramos de días SEGUIDOS: [(desde, hasta, horas)].

    Cada tramo es un permiso. ⚠️ Un día sin horas corta el tramo: si se mandara un
    permiso de viernes a lunes, Xero contaría el fin de semana.
    """
    dias = sorted(d for d, h in (horas_por_dia or {}).items() if _num(h) > 0)
    out = []
    for d in dias:
        if out and d == out[-1][1] + _dt.timedelta(days=1):
            out[-1] = (out[-1][0], d, round(out[-1][2] + _num(horas_por_dia[d]), 2))
        else:
            out.append((d, d, round(_num(horas_por_dia[d]), 2)))
    return out


def permiso_de(empleado_id: str, tipo_id: str, titulo: str, desde, hasta, horas,
               inicio_periodo, fin_periodo) -> dict:
    """El permiso tal como lo pide `POST /LeaveApplications`, con las HORAS explícitas.

    ⚠️ Sin `LeavePeriods`, Xero calcula las unidades con la jornada tipo del empleado, y
    COPEX ya recortó lo que se paga (un día con ausencia y fichaje paga solo lo que
    falta, v432). Mandar las horas evita que Xero pague otra cuenta.
    """
    return {"EmployeeID": empleado_id, "LeaveTypeID": tipo_id, "Title": titulo[:50],
            "StartDate": a_ms(desde), "EndDate": a_ms(hasta),
            "LeavePeriods": [{"PayPeriodStartDate": a_ms(inicio_periodo),
                              "PayPeriodEndDate": a_ms(fin_periodo),
                              "NumberOfUnits": round(_num(horas), 2)}]}


# ─────────────────────────────────────────────────────────────────────────────
# Leer de Xero
# ─────────────────────────────────────────────────────────────────────────────
def _msg(js, status) -> str:
    return "; ".join(X.mensajes_error(js)) or f"HTTP {status}"


def datos(grupo: str) -> dict:
    """{empleados, calendarios, tipos_permiso, error} de la organización conectada.

    ⚠️ Sin Payroll AU (otra región, o una organización sin nómina) Xero responde con
    error: se devuelve legible en vez de reventar la pantalla.
    """
    out = {"empleados": [], "calendarios": [], "tipos_permiso": {}, "error": ""}
    empleados, pagina = [], 1
    while pagina <= 20:
        st_, js, _h = X._api(grupo, "GET", "/Employees", base=X.PAYROLL_URL,
                             params={"page": pagina})
        if st_ != 200:
            out["error"] = t("Xero Payroll could not be read ({e}). The organisation needs "
                             "Payroll AU set up.", e=_msg(js, st_))
            return out
        lote = (js or {}).get("Employees") or []
        empleados += lote
        if len(lote) < 100:
            break
        pagina += 1
    out["empleados"] = [e for e in empleados
                        if str(e.get("Status", "ACTIVE")).upper() == "ACTIVE"]
    st_, js, _h = X._api(grupo, "GET", "/PayrollCalendars", base=X.PAYROLL_URL)
    if st_ != 200:
        out["error"] = t("The pay calendars could not be read in Xero ({e}).", e=_msg(js, st_))
        return out
    out["calendarios"] = (js or {}).get("PayrollCalendars") or []
    st_, js, _h = X._api(grupo, "GET", "/PayItems", base=X.PAYROLL_URL)
    if st_ != 200:
        out["error"] = t("The leave types could not be read in Xero ({e}).", e=_msg(js, st_))
        return out
    items = (js or {}).get("PayItems") or {}
    if isinstance(items, list):
        items = items[0] if items else {}
    out["tipos_permiso"] = {_cf(lt.get("Name")): lt for lt in items.get("LeaveTypes") or []}
    return out


def _todas_las_paginas(grupo, ruta, clave, empleado_id) -> tuple:
    """([objetos], error) de un empleado, recorriendo TODAS las páginas (100 por página).

    ⚠️ Mirar solo la primera página no vería el parte del periodo en alguien con más de
    100 partes históricos (dos años semanales), y se crearía otro encima.
    """
    out, pagina = [], 1
    while pagina <= 50:
        st_, js, _h = X._api(grupo, "GET", ruta, base=X.PAYROLL_URL,
                             params={"where": f'EmployeeID==Guid("{empleado_id}")',
                                     "page": pagina})
        if st_ != 200:
            return None, _msg(js, st_)
        lote = (js or {}).get(clave) or []
        out += lote
        if len(lote) < 100:
            return out, ""
        pagina += 1
    return None, t("too many pages")


def _partes_existentes(grupo, empleado_id, inicio) -> tuple:
    """(parte de ese empleado que empieza en `inicio` | None, error)."""
    todos, err = _todas_las_paginas(grupo, "/Timesheets", "Timesheets", empleado_id)
    if err:
        return None, err
    return next((ts for ts in todos if de_ms(ts.get("StartDate")) == inicio), None), ""


def _permisos_existentes(grupo, empleado_id) -> tuple:
    return _todas_las_paginas(grupo, "/LeaveApplications", "LeaveApplications", empleado_id)


# ─────────────────────────────────────────────────────────────────────────────
# Mandar
# ─────────────────────────────────────────────────────────────────────────────
def enviar(grupo: str, calendario_id: str, inicio, fin) -> dict:
    """Manda el parte y los permisos del periodo. Nunca lanza.

    {partes_creados, partes_actualizados, permisos_creados, omitidos, errores, avisos}
    donde cada lista lleva (nombre, detalle).
    """
    res = {"partes_creados": [], "partes_actualizados": [], "permisos_creados": [],
           "omitidos": [], "errores": [], "avisos": []}
    inicio, fin = _parse_date(inicio), _parse_date(fin)
    ok, tok = X._token(grupo)
    if not ok:
        res["errores"].append(("—", [tok]))
        return res
    d = datos(grupo)
    if d["error"]:
        res["errores"].append(("—", [d["error"]]))
        return res
    cal = next((c for c in d["calendarios"] if c.get("PayrollCalendarID") == calendario_id), None)
    if cal is None:
        res["errores"].append(("—", [t("That pay calendar no longer exists in Xero.")]))
        return res
    # ⚠️ Xero rechaza un parte cuyas fechas no son un periodo de ESE calendario.
    if not any(p["inicio"] == inicio and p["fin"] == fin for p in periodos(cal)):
        res["errores"].append(("—", [t("Those dates are not a pay period of «{c}».",
                                       c=cal.get("Name", ""))]))
        return res

    emp_por_id = {e["EmployeeID"]: e for e in d["empleados"]}
    pareja = emparejado(grupo, tok["tenant_id"])
    cfg = contable.mapa(grupo)
    nombres_permiso = cfg.get("conceptos", {})
    # ⚠️ Los avisos de `partes` (homónimos, recortes…) ya salen en la pantalla del parte:
    # repetirlos aquí duplicaría cada aviso tras el envío.
    p = contable.partes(grupo, inicio, fin)

    por_usuario = {}
    for f in p.get("filas") or []:
        u = por_usuario.setdefault(f["usuario"], {"nombre": f["nombre"], "conceptos": {}})
        u["conceptos"][f["concepto"]] = f["horas"]

    for login, info in sorted(por_usuario.items(), key=lambda kv: kv[1]["nombre"].casefold()):
        nombre = info["nombre"]
        eid = pareja.get(login)
        emp = emp_por_id.get(eid) if eid else None
        if not eid:
            res["omitidos"].append((nombre, t("not matched to a Xero employee")))
            continue
        if emp is None:
            res["omitidos"].append((nombre, t("the matched Xero employee is not active")))
            continue
        if emp.get("PayrollCalendarID") != calendario_id:
            res["omitidos"].append((nombre, t("is on another pay calendar in Xero")))
            continue

        # ── horas ordinarias → parte ──
        ordinarias = info["conceptos"].get(contable.ORDINARIAS) or {}
        if sum(_num(h) for h in ordinarias.values()) > 0:
            rate = emp.get("OrdinaryEarningsRateID")
            if not rate:
                res["errores"].append((nombre, [t("this employee has no ordinary earnings "
                                                  "rate in Xero")]))
            else:
                cuerpo = parte_de(eid, rate, inicio, fin, ordinarias)
                horas = round(sum(cuerpo["TimesheetLines"][0]["NumberOfUnits"]), 2)
                existe, err = _partes_existentes(grupo, eid, inicio)
                if err:
                    # ⚠️ Sin poder comprobar si ya hay parte NO se crea otro (duplicado).
                    res["errores"].append((nombre, [t("the existing timesheets could not be "
                                                      "checked ({e}); nothing was sent", e=err)]))
                elif existe is not None and str(existe.get("Status", "")).upper() != BORRADOR:
                    res["omitidos"].append((nombre, t("its timesheet for this period is already "
                                                      "{s} in Xero; it was not changed",
                                                      s=str(existe.get("Status", "")).lower())))
                else:
                    if existe is not None:
                        cuerpo["TimesheetID"] = existe.get("TimesheetID")
                        ruta = f"/Timesheets/{existe.get('TimesheetID')}"
                    else:
                        ruta = "/Timesheets"
                    st_, js, _h = X._api(grupo, "POST", ruta, base=X.PAYROLL_URL, cuerpo=[cuerpo])
                    devueltos = (js or {}).get("Timesheets") if isinstance(js, dict) else None
                    errs = [str(v.get("Message")) for ts in (devueltos or [])
                            for v in ts.get("ValidationErrors") or [] if v.get("Message")]
                    if st_ == 200 and devueltos and not errs:
                        (res["partes_actualizados"] if existe is not None
                         else res["partes_creados"]).append((nombre, horas))
                    else:
                        res["errores"].append((nombre, errs or [_msg(js, st_)]))

        # ── ausencias pagadas → permisos ──
        conceptos_permiso = [c for c in info["conceptos"] if c != contable.ORDINARIAS]
        if not conceptos_permiso:
            continue
        previos, err = _permisos_existentes(grupo, eid)
        if err:
            res["errores"].append((nombre, [t("the existing leave could not be checked ({e}); "
                                              "no leave was sent", e=err)]))
            continue
        for concepto in conceptos_permiso:
            nombre_tipo = str(nombres_permiso.get(concepto, concepto))
            tipo = d["tipos_permiso"].get(_cf(nombre_tipo))
            if not tipo:
                res["errores"].append((nombre, [t("Xero has no leave type «{l}» (rename it in "
                                                  "«Payroll names» below)", l=nombre_tipo)]))
                continue
            for desde, hasta, horas in tramos(info["conceptos"][concepto]):
                ya = any(a.get("LeaveTypeID") == tipo.get("LeaveTypeID")
                         and de_ms(a.get("StartDate")) and de_ms(a.get("EndDate"))
                         and de_ms(a.get("StartDate")) <= hasta
                         and desde <= de_ms(a.get("EndDate"))
                         for a in previos)
                if ya:
                    res["omitidos"].append((nombre, t("{l} {a}–{b} was already in Xero",
                                                      l=nombre_tipo, a=desde.strftime("%d/%m"),
                                                      b=hasta.strftime("%d/%m"))))
                    continue
                cuerpo = permiso_de(eid, tipo.get("LeaveTypeID"), f"COPEX · {nombre_tipo}",
                                    desde, hasta, horas, inicio, fin)
                st_, js, _h = X._api(grupo, "POST", "/LeaveApplications", base=X.PAYROLL_URL,
                                     cuerpo=[cuerpo])
                devueltos = (js or {}).get("LeaveApplications") if isinstance(js, dict) else None
                errs = [str(v.get("Message")) for a in (devueltos or [])
                        for v in a.get("ValidationErrors") or [] if v.get("Message")]
                if st_ == 200 and devueltos and not errs:
                    res["permisos_creados"].append((nombre, f"{nombre_tipo} {horas:g} h"))
                else:
                    res["errores"].append((nombre, errs or [_msg(js, st_)]))
    return res

