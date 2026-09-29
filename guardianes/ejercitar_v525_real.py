# -*- coding: utf-8 -*-
"""v525 contra la HOJA REAL (método v344): foto → ejercitar → verificar LEYENDO →
restaurar → segunda foto.

⚠️ Lo que esto prueba y los tests de mesa NO: que en la hoja de verdad `WorkDate` nazca al
FINAL de StageProgress (leído por un SEGUNDO camino, gspread de solo lectura), y que las
fechas REALES de la etapa que quedan en `Activities` —las que dibujan la curva S real—
sean las del TRABAJO: un parte de hace días, confirmado hoy, fecha la etapa en su día.
Datos de prueba («ZZ PRUEBA v525»), creados aquí y borrados pase lo que pase.
"""
import os
import sys
import time
from datetime import date, timedelta

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "dacox", "nombre": "dacox",
                            "rol": "administrator", "grupo": "cliente1"}

fallos, n_ok = [], 0


def ok(q, det=""):
    global n_ok
    n_ok += 1
    print("  ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("  FALLO %s%s" % (q, ("  -> " + str(det)) if det else ""))


def chk(q, cond, det=""):
    (ok if cond else fallo)(q, det)


def sec(x):
    print("\n%s" % x)


def respira(s=6):
    time.sleep(s)          # ⚠️ techo de 60 lecturas/min con UNA cuenta de servicio


import gspread                                                    # noqa: E402
from google.oauth2.service_account import Credentials             # noqa: E402

from core import clock                                            # noqa: E402
from core import daily_log as DL                                  # noqa: E402
from core import hojas as H                                       # noqa: E402
from core import projects as P                                    # noqa: E402
from core import schedule as SC                                   # noqa: E402
from core import stage_progress as SP                             # noqa: E402

GRUPO, YO, NS = "cliente1", "dacox", 6
MARCA = "ZZ PRUEBA v525"
CREADOS = []


def _ro():
    c = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    gc = gspread.authorize(c)
    lib = gc.open_by_key(st.secrets["TIMECLOCK_SHEET_ID"])
    grp = lib.worksheet("Groups").get_all_values()
    sid = [f[grp[0].index("SheetID")] for f in grp[1:] if f and f[0] == GRUPO][0]
    return gc.open_by_key(sid)


def crudo(libro, hoja):
    try:
        return libro.worksheet(hoja).get_all_values()
    except gspread.exceptions.WorksheetNotFound:
        return []


def foto():
    for h in ("Projects", "Activities", SP.SHEET, DL.SHEET):
        H.invalidar(h)
    respira(2)
    return {"Projects": len(P.list_projects(GRUPO) or []),
            "Activities": len(H.registros("Activities") or []),
            "StageProgress": len(H.registros(SP.SHEET) or []),
            "DailyLogs": len(H.registros(DL.SHEET) or [])}


def limpia():
    for pid in list(CREADOS):
        for intento in range(3):
            try:
                P.delete_project(pid)
                CREADOS.remove(pid)
                break
            except Exception as e:
                print("   (limpieza %s, intento %d: %s)" % (pid, intento + 1, e))
                time.sleep(8)


def fila_act(pid, orden):
    P._invalidate()
    respira(3)
    return next((a for a in (P.list_activities(pid) or [])
                 if int(float(a.get("Order") or 0)) == orden), {})


RO = _ro()
_cab0 = (crudo(RO, SP.SHEET) or [[]])[0]
print("CABECERA StageProgress ANTES · %d columnas" % len(_cab0))
ANTES = foto()
print("ANTES · %s" % " · ".join("%s %d" % kv for kv in ANTES.items()))
HOY = clock.today(GRUPO)
D5, D3 = (HOY - timedelta(days=5)).isoformat(), (HOY - timedelta(days=3)).isoformat()
print("hoy en %s: %s · partes del %s y del %s" % (GRUPO, HOY, D5, D3))

try:
    sec("1. Una obra de prueba con plan sellado")
    _f = SC.filas_de_etapas("Installation", NS, (), None)
    _s = SC.build_schedule(NS, date(2026, 10, 1), {}, custom_rows=_f)
    _ok, PID = P.create_project(
        GRUPO, MARCA, ns=NS, tipo="Installation", fecha_inicio="2026-10-01",
        fecha_fin_est=_s["fecha_fin"].strftime("%Y-%m-%d"), activities=_s["activities"],
        creado_por=YO, stage_plan=P.plan_nuevo("Installation", (), None))
    chk("obra creada", _ok, PID)
    if not _ok:
        raise SystemExit("sin obra no hay nada que ejercitar")
    CREADOS.append(PID)
    respira()
    P._invalidate()
    PRJ = P.get_project(PID) or {}
    PLAN = SP.plan_de_obra(PRJ)
    O7 = next(i for i, e in enumerate(PLAN, start=1)
              if "Install headers" in [a["nombre"] for a in e["actividades"]])
    OC = min(range(1, len(PLAN) + 1), key=lambda i: len(PLAN[i - 1]["actividades"]))
    ACTS_C = [a["nombre"] for a in PLAN[OC - 1]["actividades"]]

    sec("2. ⚠️ Un parte de hace TRES días, confirmado hoy")
    respira()
    _ok, LID = DL.crear(PID, GRUPO, "Installed header", YO, dia=D3)
    chk("parte guardado con su día (%s)" % D3, _ok, LID)
    respira()
    _ok, _m = SP.acreditar(PID, GRUPO, PRJ, [{"etapa": O7, "actividad": "Install headers",
                                             "pct": 100, "nota": LID}],
                           quien=YO, origen=SP.PARTE, fecha=D3)
    chk("se acredita", _ok, _m)
    _a7 = fila_act(PID, O7)
    chk("⚠️ la etapa EMPIEZA el día del parte (%s), no hoy (%s)" % (D3, HOY),
        _a7.get("ActualStartDate") == D3, _a7.get("ActualStartDate"))
    respira()
    _v = crudo(RO, SP.SHEET)
    _cab = _v[0] if _v else []
    print("   CABECERA StageProgress DESPUÉS · %d columnas" % len(_cab))
    chk("en la hoja REAL `WorkDate` nace AL FINAL (%s)" % (len(_cab) and _cab[-1]),
        _cab[:len(SP.HEADERS)] == SP.HEADERS, _cab)
    _iw = SP.HEADERS.index("WorkDate")
    _mias = [f for f in _v[1:] if len(f) > 2 and f[2] == PID]
    chk("por el SEGUNDO camino: el crédito guarda el día del TRABAJO",
        [f[_iw] if len(f) > _iw else "" for f in _mias] == [D3], _mias)

    sec("3. Un crédito a mano hoy NO atrasa ese inicio")
    respira()
    _ok, _m = SP.acreditar(PID, GRUPO, PRJ, [{"etapa": O7, "actividad": "Install sills",
                                             "pct": 100, "nota": ""}], quien=YO)
    chk("se acredita a mano", _ok, _m)
    _a7 = fila_act(PID, O7)
    chk("el inicio sigue en %s" % D3, _a7.get("ActualStartDate") == D3,
        _a7.get("ActualStartDate"))

    sec("4. ⚠️ Una etapa completada con partes: termina el ÚLTIMO día de trabajo")
    respira()
    _ok, _m = SP.acreditar(PID, GRUPO, PRJ, [{"etapa": OC, "actividad": a, "pct": 100,
                                             "nota": "LOG-A"} for a in ACTS_C[:-1]],
                           quien=YO, origen=SP.PARTE, fecha=D5)
    chk("todas menos una, con un parte de hace 5 días", _ok, _m)
    respira()
    _ok, _m = SP.acreditar(PID, GRUPO, PRJ, [{"etapa": OC, "actividad": ACTS_C[-1],
                                             "pct": 100, "nota": "LOG-B"}],
                           quien=YO, origen=SP.PARTE, fecha=D3)
    chk("y la última con el de hace 3", _ok, _m)
    _ac = fila_act(PID, OC)
    chk("⚠️ la etapa va del %s al %s, releída de Activities" % (D5, D3),
        _ac.get("ActualStartDate") == D5 and _ac.get("ActualEndDate") == D3
        and float(_ac.get("Progress") or 0) >= 100,
        (_ac.get("ActualStartDate"), _ac.get("ActualEndDate"), _ac.get("Progress")))

    sec("5. Borrar la obra se lo lleva todo")
    _okd, _m = P.delete_project(PID)
    chk("se borra %s" % PID, _okd, _m)
    if _okd and PID in CREADOS:
        CREADOS.remove(PID)
    respira()
    for h in (SP.SHEET, DL.SHEET):
        H.invalidar(h)
    respira(3)
    chk("...ni parte ni crédito huérfano",
        not [r for r in (H.registros(SP.SHEET) or []) if str(r.get("ProjectID")) == PID]
        and not [r for r in (H.registros(DL.SHEET) or []) if str(r.get("ProjectID")) == PID])
finally:
    limpia()

respira(4)
DESPUES = foto()
print("")
print("DESPUES · %s" % " · ".join("%s %d" % kv for kv in DESPUES.items()))
chk("⚠️ la hoja quedó EXACTAMENTE como estaba (en filas)", DESPUES == ANTES,
    "antes=%s despues=%s" % (ANTES, DESPUES))

print("")
if fallos:
    print("FALLOS: %d de %d" % (len(fallos), n_ok + len(fallos)))
    sys.exit(1)
print("v525 HOJA REAL — TODO OK (%d comprobaciones)" % n_ok)
