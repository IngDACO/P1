# -*- coding: utf-8 -*-
"""v490 · Parte de horas y ausencias pagadas → Xero Payroll AU (fase 2.3-B).

Lo que falla EN SILENCIO y hay que proteger:
  (a) las fechas: Xero RECHAZA un parte cuyo periodo no es exactamente uno del calendario
      del empleado, y un `/Date()/` con el día corrido manda las horas a otro día;
  (b) `NumberOfUnits` es UNA entrada por día y EN ORDEN: un orden cruzado paga días
      equivocados sin error;
  (c) las ausencias van como PERMISOS (LeaveApplications), no como líneas del parte;
  (d) no duplicar: un parte existente en borrador se ACTUALIZA, uno aprobado no se toca,
      y si no se puede comprobar NO se crea; un permiso que ya está no se reenvía;
  (e) el emparejado solo propone parejas ÚNICAS (adivinar paga las horas de otro);
  (f) el ritmo: no pasar de 60 llamadas/min a una organización.
Todo EJECUTANDO con Xero sustituido: nunca sale nada a Internet.
"""
import ast
import datetime as dt
import io
import json
import os
import sys
import time

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
G = "cliente1"
st.session_state["auth"] = {"usuario": "admin", "nombre": "admin",
                            "rol": "administrator", "grupo": G}

fallos = []
n_ok = 0


def ok(que):
    global n_ok
    n_ok += 1
    print(f"  ok   {que}")


def fallo(que, detalle=""):
    fallos.append(que)
    print(f"  *** FALLO  {que}" + (f"  -> {detalle}" if detalle else ""))


def ck(que, real, esperado):
    if real == esperado:
        ok(que)
    else:
        fallo(que, f"{real!r} != {esperado!r}")


def _fuente(f):
    return io.open(os.path.join(RAIZ, f), encoding="utf-8").read()


from core import contable                                        # noqa: E402
from core import xero as X                                       # noqa: E402
from core import xero_nomina as XN                               # noqa: E402

D = dt.date

# ═════ 1 · fechas de Xero ═══════════════════════════════════════════════════
print("\n[1] fechas en el formato de Xero")
ck("a_ms: medianoche UTC del día", XN.a_ms(D(2019, 11, 8)), "/Date(1573171200000+0000)/")
ck("de_ms lee el ejemplo OFICIAL de la especificación",
   XN.de_ms("/Date(1573171200000+0000)/"), D(2019, 11, 8))
ck("ida y vuelta sin correr el día (incluido fin de año y bisiesto)",
   [XN.de_ms(XN.a_ms(x)) for x in (D(2026, 12, 31), D(2028, 2, 29), D(2026, 1, 1))],
   [D(2026, 12, 31), D(2028, 2, 29), D(2026, 1, 1)])
ck("de_ms acepta también YYYY-MM-DD", XN.de_ms("2026-09-14"), D(2026, 9, 14))
ck("basura → None", XN.de_ms("no"), None)

# ═════ 2 · periodos del calendario ══════════════════════════════════════════
print("\n[2] periodos de cada tipo de calendario")


def cal(tipo, inicio):
    return {"PayrollCalendarID": "C", "Name": "x", "CalendarType": tipo,
            "StartDate": XN.a_ms(inicio)}


def rangos(tipo, inicio):
    return [(p["inicio"], p["fin"], p["proximo"]) for p in XN.periodos(cal(tipo, inicio))]


ck("WEEKLY: el próximo y 3 anteriores, del más reciente al más viejo",
   rangos("WEEKLY", D(2026, 9, 14)),
   [(D(2026, 9, 14), D(2026, 9, 20), True), (D(2026, 9, 7), D(2026, 9, 13), False),
    (D(2026, 8, 31), D(2026, 9, 6), False), (D(2026, 8, 24), D(2026, 8, 30), False)])
ck("FORTNIGHTLY", rangos("FORTNIGHTLY", D(2026, 9, 14))[:2],
   [(D(2026, 9, 14), D(2026, 9, 27), True), (D(2026, 8, 31), D(2026, 9, 13), False)])
ck("FOURWEEKLY", rangos("FOURWEEKLY", D(2026, 9, 14))[1],
   (D(2026, 8, 17), D(2026, 9, 13), False))
ck("MONTHLY: fin de mes real (febrero y marzo)", rangos("MONTHLY", D(2026, 3, 1))[:2],
   [(D(2026, 3, 1), D(2026, 3, 31), True), (D(2026, 2, 1), D(2026, 2, 28), False)])
ck("TWICEMONTHLY: 16→fin de mes, 1→15, y el anterior cruza de mes",
   rangos("TWICEMONTHLY", D(2026, 9, 16))[:3],
   [(D(2026, 9, 16), D(2026, 9, 30), True), (D(2026, 9, 1), D(2026, 9, 15), False),
    (D(2026, 8, 16), D(2026, 8, 31), False)])
ck("QUARTERLY", rangos("QUARTERLY", D(2026, 7, 1))[:2],
   [(D(2026, 7, 1), D(2026, 9, 30), True), (D(2026, 4, 1), D(2026, 6, 30), False)])
ck("un tipo que no se sabe calcular NO inventa fechas", rangos("RARO", D(2026, 9, 1)), [])
ck("TWICEMONTHLY que no empieza en 1 o 16: tampoco", rangos("TWICEMONTHLY", D(2026, 9, 5)), [])

# ═════ 3 · emparejado ════════════════════════════════════════════════════════
print("\n[3] emparejado de personas")
EMP = [
    {"EmployeeID": "E1", "FirstName": "Ana", "LastName": "Ruiz", "Email": "ana@x.com"},
    {"EmployeeID": "E2", "FirstName": "Luis", "LastName": "Paz", "Email": ""},
    {"EmployeeID": "E3", "FirstName": "Mei", "LastName": "Chen", "Email": "mei@x.com"},
    {"EmployeeID": "E4", "FirstName": "Mei", "LastName": "Chen", "Email": "mei2@x.com"},
    {"EmployeeID": "E5", "FirstName": "Doble", "LastName": "", "Email": "doble@x.com"},
    {"EmployeeID": "E6", "FirstName": "Otra", "LastName": "", "Email": "doble@x.com"},
]
USU = [
    {"User": "ana", "Name": "Ana  RUIZ", "Email": "otra@x.com"},        # nombre, con espacios
    {"User": "luis", "Name": "Luis Paz", "Email": ""},                    # nombre
    {"User": "mei", "Name": "Mei Chen", "Email": ""},                      # homónimo: nada
    {"User": "mei2", "Name": "Mei Chen", "Email": "MEI2@x.com"},          # email gana
    {"User": "doble", "Name": "", "Email": "doble@x.com"},               # email repetido: nada
    {"User": "sinnombre", "Name": "", "Email": ""},                      # nada
]
prop = XN.propuesta(USU, EMP)
ck("por email (sin mayúsculas) y, si no, por nombre (sin espacios dobles)",
   (prop.get("mei2"), prop.get("ana"), prop.get("luis")), ("E4", "E1", "E2"))
ck("homónimos, email repetido o sin datos: NO se propone",
   [k for k in ("mei", "doble", "sinnombre") if k in prop], [])
ck("dos usuarios hacia el MISMO empleado: ninguno se propone",
   XN.propuesta([{"User": "a", "Name": "Luis Paz"}, {"User": "b", "Name": "luis paz"}], EMP), {})
_orig_mapa = contable.mapa
contable.mapa = lambda g: {"xero_empleados": {"tenant": "T1", "map": {"ana": "E1", "x": ""}}}
ck("el emparejado vale solo para SU organización", (XN.emparejado(G, "T1"), XN.emparejado(G, "T2")),
   ({"ana": "E1"}, {}))
contable.mapa = _orig_mapa

# ═════ 4 · construir parte y permisos ═══════════════════════════════════════
print("\n[4] el parte y los permisos")
ini, fin = D(2026, 9, 14), D(2026, 9, 20)
p = XN.parte_de("E1", "R1", ini, fin, {D(2026, 9, 14): 8, D(2026, 9, 16): 7.456, D(2026, 9, 20): 2})
ck("una entrada por día del periodo, EN ORDEN y con 0 donde no hay horas",
   p["TimesheetLines"][0]["NumberOfUnits"], [8.0, 0.0, 7.46, 0.0, 0.0, 0.0, 2.0])
ck("empleado, tipo ordinario, fechas del periodo y BORRADOR",
   (p["EmployeeID"], p["TimesheetLines"][0]["EarningsRateID"], XN.de_ms(p["StartDate"]),
    XN.de_ms(p["EndDate"]), p["Status"]), ("E1", "R1", ini, fin, "DRAFT"))
ck("tramos de días SEGUIDOS; un hueco corta; un 0 no cuenta",
   XN.tramos({D(2026, 9, 14): 8, D(2026, 9, 15): 8, D(2026, 9, 17): 4, D(2026, 9, 18): 0}),
   [(D(2026, 9, 14), D(2026, 9, 15), 16.0), (D(2026, 9, 17), D(2026, 9, 17), 4.0)])
pm = XN.permiso_de("E1", "L1", "COPEX · " + "x" * 80, D(2026, 9, 14), D(2026, 9, 15), 16, ini, fin)
ck("permiso con las HORAS explícitas en el periodo de pago, y título acotado a 50",
   (pm["LeavePeriods"], len(pm["Title"]), XN.de_ms(pm["StartDate"]), XN.de_ms(pm["EndDate"])),
   ([{"PayPeriodStartDate": XN.a_ms(ini), "PayPeriodEndDate": XN.a_ms(fin),
      "NumberOfUnits": 16.0}], 50, D(2026, 9, 14), D(2026, 9, 15)))

# ═════ 5 · enviar, con Xero sustituido ══════════════════════════════════════
print("\n[5] enviar (todas las ramas)")
EMPLEADOS = [
    {"EmployeeID": "EA", "FirstName": "Ana", "LastName": "Ruiz", "Status": "ACTIVE",
     "PayrollCalendarID": "C1", "OrdinaryEarningsRateID": "R-ORD"},
    {"EmployeeID": "EB", "FirstName": "Beto", "LastName": "Sol", "Status": "ACTIVE",
     "PayrollCalendarID": "C2", "OrdinaryEarningsRateID": "R-ORD"},
    {"EmployeeID": "EX", "FirstName": "Baja", "LastName": "", "Status": "TERMINATED",
     "PayrollCalendarID": "C1", "OrdinaryEarningsRateID": "R-ORD"},
]
CALS = [{"PayrollCalendarID": "C1", "Name": "Weekly", "CalendarType": "WEEKLY",
         "StartDate": XN.a_ms(ini)},
        {"PayrollCalendarID": "C2", "Name": "Fortnightly", "CalendarType": "FORTNIGHTLY",
         "StartDate": XN.a_ms(ini)}]
TIPOS = [{"LeaveTypeID": "LT-AL", "Name": "Annual Leave"},
         {"LeaveTypeID": "LT-PC", "Name": "Personal/Carer's Leave"}]
FILAS = [
    {"usuario": "ana", "nombre": "Ana Ruiz", "concepto": contable.ORDINARIAS,
     "horas": {D(2026, 9, 14): 8.0, D(2026, 9, 15): 7.5}, "total": 15.5},
    {"usuario": "ana", "nombre": "Ana Ruiz", "concepto": "vacaciones",
     "horas": {D(2026, 9, 16): 8.0, D(2026, 9, 17): 8.0, D(2026, 9, 19): 4.0}, "total": 20.0},
    {"usuario": "ana", "nombre": "Ana Ruiz", "concepto": "enfermedad",
     "horas": {D(2026, 9, 18): 3.0}, "total": 3.0},
    {"usuario": "beto", "nombre": "Beto Sol", "concepto": contable.ORDINARIAS,
     "horas": {D(2026, 9, 14): 8.0}, "total": 8.0},
    {"usuario": "carla", "nombre": "Carla", "concepto": contable.ORDINARIAS,
     "horas": {D(2026, 9, 14): 8.0}, "total": 8.0},
    {"usuario": "dani", "nombre": "Dani", "concepto": contable.ORDINARIAS,
     "horas": {D(2026, 9, 14): 8.0}, "total": 8.0},
]
CFG = {"xero_empleados": {"tenant": "T1", "map": {"ana": "EA", "beto": "EB", "dani": "EX"}},
       "conceptos": {"ordinarias": "Ordinary Hours", "vacaciones": "Annual Leave",
                     "enfermedad": "Personal/Carer's Leave"}}

LLAMADAS = []
ESCENA = {}


def api_falsa(grupo, metodo, ruta, *, params=None, cuerpo=None, cabeceras=None, base=X.API_URL):
    LLAMADAS.append((metodo, ruta, params, cuerpo, base))
    if base != X.PAYROLL_URL:
        return 599, {"Message": "base equivocada"}, {}
    clave = (metodo, ruta.split("/")[1] if ruta.count("/") >= 1 else ruta)
    fn = ESCENA.get((metodo, ruta)) or ESCENA.get(clave)
    if fn:
        return fn(params, cuerpo)
    return 599, {"Message": f"sin simular {metodo} {ruta}"}, {}


def escena_base():
    ESCENA.clear()
    ESCENA[("GET", "/Employees")] = lambda pa, cu: (200, {"Employees": EMPLEADOS}, {})
    ESCENA[("GET", "/PayrollCalendars")] = lambda pa, cu: (200, {"PayrollCalendars": CALS}, {})
    ESCENA[("GET", "/PayItems")] = lambda pa, cu: (200, {"PayItems": {"LeaveTypes": TIPOS}}, {})
    ESCENA[("GET", "/Timesheets")] = lambda pa, cu: (200, {"Timesheets": [
        {"TimesheetID": "TS-VIEJO", "EmployeeID": "EA", "StartDate": XN.a_ms(D(2026, 9, 7)),
         "Status": "APPROVED"}]}, {})
    ESCENA[("POST", "/Timesheets")] = lambda pa, cu: (200, {"Timesheets": [dict(cu[0], TimesheetID="TS-NUEVO")]}, {})
    ESCENA[("GET", "/LeaveApplications")] = lambda pa, cu: (200, {"LeaveApplications": [
        {"LeaveTypeID": "LT-AL", "StartDate": XN.a_ms(D(2026, 9, 19)),
         "EndDate": XN.a_ms(D(2026, 9, 19))}]}, {})
    ESCENA[("POST", "/LeaveApplications")] = lambda pa, cu: (200, {"LeaveApplications": [dict(cu[0], LeaveApplicationID="LA")]}, {})


_orig = (X._api, X._token, contable.partes, contable.mapa)
X._api = api_falsa
X._token = lambda g, forzar=False: (True, {"access": "a", "tenant_id": "T1", "short_code": ""})
contable.partes = lambda g, a, b: {"filas": [dict(f) for f in FILAS], "avisos": ["aviso del parte"]}
contable.mapa = lambda g: json.loads(json.dumps(CFG))
try:
    escena_base()
    LLAMADAS.clear()
    res = XN.enviar(G, "C1", ini, fin)
    ck("todas las llamadas van a la API de NÓMINA", {c[4] for c in LLAMADAS}, {X.PAYROLL_URL})
    ck("Ana: parte CREADO con sus 15,5 h", res["partes_creados"], [("Ana Ruiz", 15.5)])
    _post_ts = [c for c in LLAMADAS if c[0] == "POST" and c[1] == "/Timesheets"]
    ck("un solo POST de parte, con lista de UN parte", (len(_post_ts), len(_post_ts[0][3])), (1, 1))
    _ts = _post_ts[0][3][0]
    ck("…con el tipo ORDINARIO del empleado y las horas día a día en orden",
       (_ts["TimesheetLines"][0]["EarningsRateID"], _ts["TimesheetLines"][0]["NumberOfUnits"],
        _ts["Status"]), ("R-ORD", [8.0, 7.5, 0.0, 0.0, 0.0, 0.0, 0.0], "DRAFT"))
    _omit = dict(res["omitidos"])
    ck("Beto está en OTRO calendario: no se manda", "Beto Sol" in _omit, True)
    ck("Carla no está emparejada: no se manda", "Carla" in _omit, True)
    ck("Dani apunta a un empleado dado de baja: no se manda", "Dani" in _omit, True)
    _perm = [c[3][0] for c in LLAMADAS if c[0] == "POST" and c[1] == "/LeaveApplications"]
    ck("permisos: vacaciones 16–17 (16 h) y baja 18 (3 h); el 19 YA estaba en Xero",
       sorted((p_["LeaveTypeID"], XN.de_ms(p_["StartDate"]), XN.de_ms(p_["EndDate"]),
               p_["LeavePeriods"][0]["NumberOfUnits"]) for p_ in _perm),
       [("LT-AL", D(2026, 9, 16), D(2026, 9, 17), 16.0), ("LT-PC", D(2026, 9, 18), D(2026, 9, 18), 3.0)])
    ck("…y el del 19 se cuenta como omitido, no como enviado",
       (len(res["permisos_creados"]), any("19/09" in m for n, m in res["omitidos"])), (2, True))
    ck("los avisos del parte NO se repiten tras enviar", res["avisos"], [])
    ck("la búsqueda de partes filtra por EMPLEADO",
       [c[2]["where"] for c in LLAMADAS if c[1] == "/Timesheets" and c[0] == "GET"],
       ['EmployeeID==Guid("EA")'])

    # borrador existente → se ACTUALIZA
    escena_base()
    ESCENA[("GET", "/Timesheets")] = lambda pa, cu: (200, {"Timesheets": [
        {"TimesheetID": "TS-BORR", "StartDate": XN.a_ms(ini), "Status": "DRAFT"}]}, {})
    ESCENA[("POST", "/Timesheets/TS-BORR")] = lambda pa, cu: (200, {"Timesheets": [cu[0]]}, {})
    LLAMADAS.clear()
    res = XN.enviar(G, "C1", ini, fin)
    _upd = [c for c in LLAMADAS if c[0] == "POST" and c[1].startswith("/Timesheets")]
    ck("un parte en BORRADOR se actualiza (POST a su ID, con su TimesheetID)",
       ([c[1] for c in _upd], _upd[0][3][0].get("TimesheetID"), res["partes_actualizados"]),
       (["/Timesheets/TS-BORR"], "TS-BORR", [("Ana Ruiz", 15.5)]))

    # aprobado → no se toca
    escena_base()
    ESCENA[("GET", "/Timesheets")] = lambda pa, cu: (200, {"Timesheets": [
        {"TimesheetID": "TS-OK", "StartDate": XN.a_ms(ini), "Status": "APPROVED"}]}, {})
    LLAMADAS.clear()
    res = XN.enviar(G, "C1", ini, fin)
    ck("un parte ya APROBADO no se toca y se dice",
       ([c for c in LLAMADAS if c[0] == "POST" and "Timesheets" in c[1]], res["partes_creados"],
        any("approved" in m for n, m in res["omitidos"])), ([], [], True))

    # no se puede comprobar → no se crea
    escena_base()
    ESCENA[("GET", "/Timesheets")] = lambda pa, cu: (500, {"Message": "caído"}, {})
    LLAMADAS.clear()
    res = XN.enviar(G, "C1", ini, fin)
    ck("sin poder comprobar los partes NO se crea ninguno (duplicado a ciegas)",
       ([c for c in LLAMADAS if c[0] == "POST" and "Timesheets" in c[1]], bool(res["errores"])),
       ([], True))

    # paginación: el del periodo está en la página 2
    escena_base()

    def _paginas(pa, cu):
        if pa.get("page") == 1:
            return 200, {"Timesheets": [{"TimesheetID": f"V{i}", "StartDate": XN.a_ms(D(2020, 1, 1)),
                                         "Status": "APPROVED"} for i in range(100)]}, {}
        return 200, {"Timesheets": [{"TimesheetID": "TS-P2", "StartDate": XN.a_ms(ini),
                                     "Status": "DRAFT"}]}, {}
    ESCENA[("GET", "/Timesheets")] = _paginas
    ESCENA[("POST", "/Timesheets/TS-P2")] = lambda pa, cu: (200, {"Timesheets": [cu[0]]}, {})
    LLAMADAS.clear()
    res = XN.enviar(G, "C1", ini, fin)
    ck("con más de 100 partes, el del periodo en la página 2 se ENCUENTRA (se actualiza, no se duplica)",
       (res["partes_actualizados"], res["partes_creados"]), ([("Ana Ruiz", 15.5)], []))

    # fechas que no son un periodo
    escena_base()
    LLAMADAS.clear()
    res = XN.enviar(G, "C1", D(2026, 9, 15), D(2026, 9, 21))
    ck("fechas que NO son un periodo del calendario: error y ni una llamada a partes/permisos",
       (bool(res["errores"]), [c for c in LLAMADAS if c[1] in ("/Timesheets", "/LeaveApplications")]),
       (True, []))

    # errores de validación dentro de la respuesta
    escena_base()
    ESCENA[("POST", "/Timesheets")] = lambda pa, cu: (400, {"Timesheets": [dict(cu[0], ValidationErrors=[
        {"Message": "The timesheet period does not match the payroll calendar"}])]}, {})
    res = XN.enviar(G, "C1", ini, fin)
    ck("el error de validación de Xero llega TAL CUAL",
       [m for n, ms in res["errores"] for m in ms if "payroll calendar" in m] != [], True)

    # tipo de permiso que no existe
    escena_base()
    ESCENA[("GET", "/PayItems")] = lambda pa, cu: (200, {"PayItems": {"LeaveTypes": [TIPOS[0]]}}, {})
    res = XN.enviar(G, "C1", ini, fin)
    ck("un tipo de permiso sin nombre en Xero: error legible, los demás siguen",
       (any("Personal/Carer's Leave" in m for n, ms in res["errores"] for m in ms),
        len(res["permisos_creados"])), (True, 1))
finally:
    X._api, X._token, contable.partes, contable.mapa = _orig

# ═════ 6 · ritmo y 429 en xero._api ════════════════════════════════════════
print("\n[6] ritmo de llamadas y 429")
X._LLAMADAS.clear()
ahora = 1_000_000.0
esperas = [X._espera_cupo("TA", ahora=ahora + i * 0.1) for i in range(X._CUPO_MIN)]
ck("las primeras 55 llamadas en 60 s no esperan", max(esperas), 0.0)
ck("la 56 espera a que se libere el minuto", X._espera_cupo("TA", ahora=ahora + 6) > 50, True)
ck("otra organización no comparte el cupo", X._espera_cupo("TB", ahora=ahora + 6), 0.0)
ck("pasado el minuto se vuelve a llamar sin esperar",
   X._espera_cupo("TC", ahora=ahora) == 0.0 and X._espera_cupo("TA", ahora=ahora + 200) == 0.0, True)


class R:
    def __init__(self, s, h=None):
        self.status_code, self.headers = s, h or {}

    def json(self):
        return {}


_seq = []
_orig_http, _orig_tok, _orig_sleep = X._http, X._token, time.sleep
X._token = lambda g, forzar=False: (True, {"access": "a", "tenant_id": "T-429", "short_code": ""})
_dormido = []
time.sleep = lambda s: _dormido.append(s)
try:
    X._http = lambda m, u, **kw: (_seq.append(1) or (R(429, {"Retry-After": "2"}) if len(_seq) == 1 else R(200)))
    st_, js, h = X._api(G, "GET", "/x")
    ck("un 429 con espera CORTA se reintenta una vez", (st_, len(_seq), _dormido), (200, 2, [2.0]))
    _seq.clear()
    _dormido.clear()
    X._http = lambda m, u, **kw: (_seq.append(1) or R(429, {"Retry-After": "40"}))
    st_, js, h = X._api(G, "GET", "/x")
    ck("…con espera LARGA se devuelve sin colgar la pantalla", (st_, len(_seq), _dormido), (429, 1, []))
    _seq.clear()
    X._http = lambda m, u, **kw: (_seq.append(u) or R(200))
    X._api(G, "GET", "/Employees", base=X.PAYROLL_URL)
    ck("`base` elige la API de nómina", _seq[-1], "https://api.xero.com/payroll.xro/1.0/Employees")
finally:
    X._http, X._token, time.sleep = _orig_http, _orig_tok, _orig_sleep

ck("los errores de validación de Payroll AU se extraen de CADA objeto",
   X.mensajes_error({"Message": "A validation exception occurred",
                     "Timesheets": [{"ValidationErrors": [{"Message": "Periodo no válido"}]}]}),
   ["Periodo no válido"])

# ═════ 7 · pantalla y enganches ═════════════════════════════════════════════
print("\n[7] pantalla y enganches")
from core import xero_ui as XU                                  # noqa: E402
from core import auth                                            # noqa: E402

_arb_cu = ast.parse(_fuente("core/contable_ui.py"))
_ps = next(n for n in ast.walk(_arb_cu) if isinstance(n, ast.FunctionDef) and n.name == "_partes_section")
ck("el parte de la pantalla Contable llama al envío a Xero Payroll",
   any(isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "render_partes_xero"
       for n in ast.walk(_ps)), True)
# ⚠️ Por AST: el literal viejo sigue en un COMENTARIO que explica el cambio, y buscarlo
# como texto daba un rojo que no existía (trampa nº2).
_titulos = [ast.literal_eval(n.args[0].args[0]) for n in ast.walk(_ps)
            if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "expander"
            and n.args and isinstance(n.args[0], ast.Call) and n.args[0].args
            and isinstance(n.args[0].args[0], ast.Constant)]
ck("el desplegable de nombres se titula «Payroll names» (hay tipos de permiso, no solo de ganancia)",
   _titulos, ["Payroll names"])
ck("los usuarios activos usan los valores de `auth`, no una copia (v323)",
   "auth._ACTIVE_OK" in _fuente("core/xero_ui.py") and "_ACTIVOS" not in _fuente("core/xero_ui.py"), True)

PINT = {"selectbox": [], "button": [], "df": [], "caption": [], "warning": []}
_g = {}


class _Ctx:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _espia(n, fn):
    _g[n] = getattr(st, n)
    setattr(st, n, fn)


_espia("markdown", lambda *a, **kw: None)
_espia("caption", lambda txt, **kw: PINT["caption"].append(txt))
_espia("warning", lambda txt, **kw: PINT["warning"].append(txt))
_espia("info", lambda *a, **kw: None)
_espia("expander", lambda *a, **kw: _Ctx())
_espia("spinner", lambda *a, **kw: _Ctx())
_espia("button", lambda label, **kw: PINT["button"].append((label, kw.get("disabled"))) or False)
_espia("selectbox", lambda label, opciones, **kw: PINT["selectbox"].append((kw.get("key"), list(opciones), kw.get("index", 0))) or opciones[kw.get("index", 0) or 0])
_espia("dataframe", lambda df, **kw: PINT["df"].append(df))
_oc = (X.configuracion, X.estado, XN.datos, auth.list_users, contable.partes, contable.mapa)
try:
    X.configuracion = lambda: {"ok": True}
    X.estado = lambda g: {"conectada": False, "tenant_id": ""}
    XU.render_partes_xero(G)
    ck("sin conexión: dice que conecte y no llama a Xero",
       any("Connect Xero" in c for c in PINT["caption"]), True)
    X.estado = lambda g: {"conectada": True, "tenant_id": "T1"}
    XN.datos = lambda g: {"empleados": EMPLEADOS[:2], "calendarios": CALS, "tipos_permiso": {}, "error": ""}
    auth.list_users = lambda g=None: [
        {"User": "ana", "Name": "Ana Ruiz", "Email": "", "Active": "SI"},
        {"User": "beto", "Name": "Beto Sol", "Email": "", "Active": "YES"},
        {"User": "ido", "Name": "Se fue", "Email": "", "Active": "NO"}]
    contable.partes = lambda g, a, b: {"filas": [dict(f) for f in FILAS], "avisos": []}
    contable.mapa = lambda g: json.loads(json.dumps(CFG))
    st.session_state.pop(f"_xero_nomina_{G}", None)
    XU.render_partes_xero(G)
    _keys = [k for k, o, i in PINT["selectbox"] if str(k).startswith("xn_emp_")]
    ck("un selector por usuario ACTIVO (el inactivo no sale)", _keys, ["xn_emp_ana", "xn_emp_beto"])
    _per = [o for k, o, i in PINT["selectbox"] if k == "xn_periodo"]
    ck("el periodo se elige de los calendarios de Xero (4 + 4 periodos)",
       len(_per[0]) if _per else 0, 8)
    ck("hay tabla de lo que se va a mandar", len(PINT["df"]), 1)
    _df = PINT["df"][0]
    ck("…con la celda de horas SIN nulos (v486)", _df["Horas"].isna().sum() if "Horas" in _df else -1, 0)
    _btn = [b for b in PINT["button"] if "Xero Payroll" in b[0]]
    ck("el botón de enviar cuenta solo a quien se va a mandar (Ana)",
       bool(_btn) and "1" in _btn[0][0] and _btn[0][1] is False, True)
finally:
    for n, f in _g.items():
        setattr(st, n, f)
    (X.configuracion, X.estado, XN.datos, auth.list_users, contable.partes, contable.mapa) = _oc

print("\n" + "=" * 74)
print(f"{n_ok} comprobaciones OK · {len(fallos)} fallos")
if fallos:
    for f in fallos:
        print("   -", f)
sys.exit(1 if fallos else 0)
