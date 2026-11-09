# -*- coding: utf-8 -*-
"""v644 · EL MANAGEMENT ASSISTANT ACTÚA, CON TARJETA (niveles 2 y 3 de la oficina, 03/11/2026).

Decisión del usuario: la oficina prepara cinco acciones que solo pasan con **Confirm** —aprobar o rechazar una
ausencia, aprobar o revertir una corrección de fichaje, cerrar un aviso, asignar a alguien a una obra y mandar un
aviso a la cuadrilla—, apunta y marca en To-do sola, y recuerda la conversación como el campo. Nunca, ni confirmado:
facturar, cobros, nóminas, Xero, borrar, usuarios, roles o tarifas, ni avance. El propietario, con su recorrido.

Lo que protege, SIN la API ni la hoja (todo lo que escribe o avisa, sustituido y apuntado en `ESC`):
  (a) ⚠️ cada rol, lo suyo: al ofrecer, al ejecutar y AL CONFIRMAR;
  (b) ⚠️ preparar no escribe ni avisa, y los IDs del modelo solo abren lo que espera en SU grupo;
  (c) cada tarjeta enseña lo que su pantalla enseña antes de decidir (saldo, obras, nómina, certificados…);
  (d) ⚠️ confirmar vuelve a mirar (otro pudo decidir antes) y hace lo MISMO que la pantalla, con su función;
  (e) ⚠️ lo que nunca hace no existe, ni como herramienta ni como llamada;
  (f) la oficina recuerda, cada uno lo suyo; el propietario no; la foto, solo el campo.
"""
import ast
import datetime as dt
import json
import os
import sys
import types

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"}

from streamlit.testing.v1 import AppTest                          # noqa: E402

import core                                                        # noqa: E402
from core import admin_digest as AD, alerts as AL, auth, ausencias as AU, ausencias_ui as AUI, chat_agent as CA   # noqa: E402
from core import chat_memoria as CM, chat_tools as CT, chat_ui as CU, clock, correcciones as CO, correcciones_ui as CUI  # noqa: E402
from core import credentials as CR, notify, projects as P, projects_ui as PU, roster as R, tareas as TA, timeclock as TC  # noqa: E402
from core import daily_log as DL                                  # noqa: E402

n_ok, fallos = 0, []


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("   ok   %s" % q)
    else:
        fallos.append(q)
        print("   FALLO %s%s" % (q, ("  -> " + str(det)) if det != "" else ""))


def sec(x):
    print("\n" + x)
    print("-" * 70)


def leer(rel):
    with open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def funcion(fuente, nombre):
    arbol = ast.parse(fuente)
    return next((ast.get_source_segment(fuente, n) for n in ast.walk(arbol)
                 if isinstance(n, ast.FunctionDef) and n.name == nombre), "")


HOY = dt.date(2026, 11, 3)
clock.today = lambda *a: HOY
clock.now = lambda *a: dt.datetime(2026, 11, 3, 7, 30)

# ── Todo lo que escribe o avisa, sustituido: aquí se apunta, y nada sale ─────────────
ESC = []


def apunta(nombre, res):
    def f(*a, **k):
        ESC.append((nombre, a, k))
        return res() if callable(res) else res
    return f


_mem = {}
CM.cargar = lambda u, g: list(_mem.get((u, g), []))
CM.guardar = apunta("CM.guardar", True)
CM.borrar = apunta("CM.borrar", True)
TA.crear = apunta("TA.crear", (True, "TSK-9"))
TA.marcar = apunta("TA.marcar", (True, "ok"))
AU.resolver = apunta("AU.resolver", (True, "Absence approved."))
AU.aplicar_al_roster = apunta("roster", (True, 2))
AUI._avisar_persona = apunta("aus_avisar", None)
CO.aprobar = apunta("CO.aprobar", (True, "Correction approved."))
CO.revertir = apunta("CO.revertir", (True, "Correction reverted: the original time is back."))
CO.ajustar = apunta("CO.ajustar", (True, "Time set."))
CO.cerrar_sustituida = apunta("CO.cerrar_sustituida", (True, "Closed."))
CUI._avisar_persona = apunta("cor_avisar", None)
AL.resolve_alert = apunta("AL.resolve_alert", (True, "Alert resolved."))
AL.notify_change = apunta("AL.notify_change", (True, "ALR-0009"))
AL.report_problem = apunta("AL.report_problem", (True, "ALR-X"))
AL.create_alert = apunta("AL.create_alert", (True, "ALR-X"))
# Lo del campo también: una rotura del rol podría llevar una tarjeta de la oficina hasta aquí
DL.crear = apunta("DL.crear", (True, "DL-9"))
AU.solicitar = apunta("AU.solicitar", (True, "AUS-9"))
AUI.registrar = apunta("AUI.registrar", (True, "AUS-9", ""))
P.add_field_user = apunta("P.add_field_user", (True, True))
P.update_project = apunta("P.update_project", (True, "ok"))
notify.notify_assignment = apunta("notify_assignment", {"email": True, "telegram": False})
notify.notify_user = apunta("notify_user", {"email": False, "telegram": False})
_canal = {"hay": True}
notify.any_channel_configured = lambda: _canal["hay"]
_autopoblar_real = R.autopoblar_proyecto
R.autopoblar_proyecto = apunta("autopoblar", {"llenadas": 4, "ocupadas": 1, "actualizadas": 0, "nuevas": 0, "semanas": 1})

# ── Los datos ─────────────────────────────────────────────────────────────────────
O1 = {"ID": "PRJ-1", "Name": "Bondi", "Group": "cliente1", "Status": "In progress", "FieldAssigned": "campo000",
      "StartDate": "2026-11-02", "EndDateEst": "2026-11-20", "RequiredCerts": "EWP;White Card", "Location": "x"}
O2 = {"ID": "PRJ-2", "Name": "Vacía", "Group": "cliente1", "Status": "Planned", "FieldAssigned": "", "StartDate": "", "EndDateEst": ""}
O3 = {"ID": "PRJ-3", "Name": "Otra obra", "Group": "cliente1", "Status": "In progress", "FieldAssigned": "helper", "EndDateEst": "2026-12-01"}
O4 = {"ID": "PRJ-4", "Name": "Vencida", "Group": "cliente1", "Status": "In progress", "FieldAssigned": "", "StartDate": "2026-09-14",
      "EndDateEst": "2026-10-29"}
AJENA = {"ID": "PRJ-9", "Name": "De otra", "Group": "otro", "Status": "In progress", "FieldAssigned": "ajeno"}
P.list_projects = lambda grupo=None, agrupacion_id=None, incluir_archivados=False, incluir_internos=False: (
    {"cliente1": [O1, O2, O3, O4], "otro": [AJENA]}.get(grupo, []))
P.list_projects_for_field = lambda u, grupo=None, incluir_internos=False: [O1] if u == "campo000" else []
USERS = [{"User": "campo000", "Name": "Field Test", "Role": "field", "Group": "cliente1", "Email": "f@x.com"},
         {"User": "helper", "Name": "Helper One", "Role": "field", "Group": "cliente1", "Email": ""},
         {"User": "mei1", "Name": "Mei Chen", "Role": "field", "Group": "cliente1", "Email": "m@x.com"},
         {"User": "mei2", "Name": "Mei Chen", "Role": "field", "Group": "cliente1", "Email": "n@x.com"},
         {"User": "Admin2", "Name": "Bobo", "Role": "administrator", "Group": "cliente1", "Email": "b@x.com"},
         {"User": "ajeno", "Name": "Ajeno", "Role": "field", "Group": "otro", "Email": "a@x.com"}]
auth.list_users = lambda g=None: [u for u in USERS if g is None or u["Group"].lower() == str(g).lower()]
auth.get_user = lambda u: next((x for x in USERS if x["User"] == u), {})
AD.nombres_usuarios = lambda: {u["User"]: u["Name"] for u in USERS}
notify.contacto_campo_ok = lambda info: bool(str((info or {}).get("Email", "")).strip())
CR.list_for = lambda u: [{"Type": "Forklift", "ExpiryDate": "2026-11-10"}] if u == "helper" else []
CR.status = lambda v: "por_vencer"
CR.status_label = lambda v: "expires 10/11/2026"
CR.compliance = lambda u, req: {"cumple": False, "por_tipo": {"EWP": "vencido", "White Card": "vigente"}}

AUS = [{"ID": "AUS-1", "Group": "cliente1", "User": "helper", "Name": "Helper One", "Type": "vacaciones", "From": "2026-11-10",
        "To": "2026-11-12", "Days": "3", "Reason": "Family", "Status": AU.PENDIENTE},
       {"ID": "AUS-2", "Group": "cliente1", "User": "campo000", "Name": "Field Test", "Type": "libre", "From": "2026-11-05",
        "To": "2026-11-05", "Days": "1", "Reason": "", "Status": AU.APROBADA},
       {"ID": "AUS-8", "Group": "otro", "User": "ajeno", "Name": "Ajeno", "Type": "libre", "From": "2026-11-05",
        "To": "2026-11-05", "Days": "1", "Reason": "", "Status": AU.PENDIENTE}]
AU.list_group = lambda g, estado=None, usuario=None: [r for r in AUS if r["Group"] == g and (estado is None or r["Status"] == estado)
                                                      and (usuario is None or r["User"] == usuario)]
AU.pendientes = lambda g: AU.list_group(g, estado=AU.PENDIENTE)
_saldo = {"restantes": 2.0}
AU.saldo = lambda g, u, tipo, ref=None: {"ilimitado": False, "restantes": _saldo["restantes"], "asignados": 20.0, "disponibles": 2.0,
                                          "usados": 18.0, "pendientes": 0.0}
AU.choques = lambda g, u, d0, d1: [{"etiqueta": "Bondi", "fecha": "2026-11-10", "proyecto_id": "PRJ-1"},
                                   {"etiqueta": "Bondi", "fecha": "2026-11-11", "proyecto_id": "PRJ-1"}]

COR = [{"ID": "COR-1", "Group": "cliente1", "User": "campo000", "Name": "Field Test", "Type": TC.TIPO_GENERAL, "Project": "",
        "Field": CO.CAMPO_IN, "OldValue": "2026-11-02 07:00:00", "NewValue": "2026-11-02 06:30:00", "Reason": "forgot",
        "Status": CO.PENDIENTE, "Created": "2026-11-02 08:00:00", "PayslipCovers": "NOM-3"},
       {"ID": "COR-2", "Group": "cliente1", "User": "campo000", "Name": "Field Test", "Type": TC.TIPO_GENERAL, "Project": "",
        "Field": CO.CAMPO_OUT, "OldValue": "", "NewValue": "2026-11-02 17:00:00", "Reason": "left open",
        "Status": CO.PENDIENTE, "Created": "2026-11-02 18:00:00", "PayslipCovers": ""},
       {"ID": "COR-3", "Group": "cliente1", "User": "helper", "Name": "Helper One", "Type": TC.TIPO_GENERAL, "Project": "",
        "Field": CO.CAMPO_IN, "OldValue": "2026-11-01 08:00:00", "NewValue": "2026-11-01 07:30:00", "Reason": "a",
        "Status": CO.PENDIENTE, "Created": "2026-11-01 09:00:00", "PayslipCovers": ""},
       {"ID": "COR-4", "Group": "cliente1", "User": "helper", "Name": "Helper One", "Type": TC.TIPO_GENERAL, "Project": "",
        "Field": CO.CAMPO_IN, "OldValue": "2026-11-01 07:30:00", "NewValue": "2026-11-01 08:00:00", "Reason": "b",
        "Status": CO.PENDIENTE, "Created": "2026-11-01 10:00:00", "PayslipCovers": ""},
       {"ID": "COR-9", "Group": "otro", "User": "ajeno", "Name": "Ajeno", "Type": TC.TIPO_GENERAL, "Project": "",
        "Field": CO.CAMPO_IN, "OldValue": "2026-11-01 08:00:00", "NewValue": "2026-11-01 07:00:00", "Reason": "",
        "Status": CO.PENDIENTE, "Created": "2026-11-01 09:00:00", "PayslipCovers": ""}]
CO.list_group = lambda g, estado=None, usuario=None: [r for r in COR if r["Group"].lower() == str(g).lower()
                                                      and (estado is None or r["Status"] == estado)]
CO.pendientes = lambda g: CO.list_group(g, estado=CO.PENDIENTE)

ALS = [{"ID": "ALR-1", "Group": "cliente1", "Status": "abierta", "ProjectID": "PRJ-1", "Message": "Door jammed", "CreatedBy": "helper",
        "Date": "2026-11-02 08:05", "Type": "problema"},
       {"ID": "ALR-2", "Group": "cliente1", "Status": "resuelta", "ProjectID": "PRJ-1", "Message": "Vieja", "CreatedBy": "x", "Date": "2026-10-01"},
       {"ID": "ALR-3", "Group": "otro", "Status": "abierta", "ProjectID": "PRJ-9", "Message": "De otra", "CreatedBy": "x", "Date": "2026-11-01"}]
AL._alarmas_visibles = lambda: list(ALS)
# v646 · la bandeja mira también los partes que esperan a la oficina (verif_v646): sin leer la hoja
from core import daily_log_ui as _DLU                             # noqa: E402
_DLU.partes_para_la_oficina = lambda g: []


def octx(**k):
    return {"usuario": "Admin2", "nombre": "Bobo", "grupo": "cliente1", "rol": "administrator", "acciones": [], **k}


def cctx(**k):
    return {"usuario": "campo000", "nombre": "Field Test", "grupo": "cliente1", "rol": "field", "acciones": [], **k}


def ej(nombre, entrada, ctx=None):
    c = ctx if ctx is not None else octx()
    txt, mal = CT.ejecutar(nombre, entrada, c)
    return (json.loads(txt) if not mal else txt), mal, c


def preparar(nombre, entrada, ctx=None):
    """Prepara y devuelve `(resultado, error, tarjeta)`; ⚠️ comprueba de paso que no se escribió ni avisó nada."""
    ESC.clear()
    x, m, c = ej(nombre, entrada, ctx)
    _prep["n"] += 1
    _prep["esc"] += len(ESC)
    if ESC:
        chk("⚠️ preparar no escribe ni avisa: " + nombre, False, ESC)
    return x, m, (c["acciones"][-1] if c["acciones"] else None)


_prep = {"n": 0, "esc": 0}
NUEVAS = ["prepare_absence_decision", "prepare_time_fix_decision", "prepare_close_alert", "prepare_assignment", "prepare_crew_notice"]

# ═════════════════════════════════════════════════════════════════
sec("1. ⚠️ Cada rol, lo suyo")
_n = [h["name"] for h in CT.definiciones("administrator", "Admin2")]
chk("la oficina: las cinco consultas, To-do y las cinco con tarjeta, en ese orden",
    _n == ["get_portfolio", "get_job_details", "get_team", "get_inbox", "get_money", "add_todo", "mark_todo"] + NUEVAS, _n)
_d = CT.definiciones("administrator", "Admin2")
chk("a la API no le llega la función", all(set(h) == {"name", "description", "input_schema"} for h in _d) and bool(json.dumps(_d)))
chk("cada una dice cuándo usarla", all("Call it" in h["description"] for h in _d))
chk("⚠️ cada una que cambia algo dice si espera o no", all(("no confirmation" in h["description"]) or ("card" in h["description"] and "nothing yet" in h["description"])
                                                         for h in _d[5:]), [h["name"] for h in _d[5:]])
chk("⚠️ ninguna recibe quién la pide ni de qué empresa", all(not ({"usuario", "user", "grupo", "group", "rol", "role", "author"} & set(h["input_schema"].get("properties", {}))) for h in _d))
_c = [h["name"] for h in CT.definiciones("field", "campo000")]
chk("⚠️ el campo no recibe ninguna de la oficina", not (set(NUEVAS) & set(_c)), _c)
for nom in NUEVAS:
    x, m, c = ej(nom, {"project_id": "PRJ-1"}, cctx())
    if not (m and "Unknown tool" in x):
        chk("⚠️ ni la abre aunque el modelo la pida", False, (nom, x))
        break
else:
    chk("⚠️ ni la abre aunque el modelo la pida", True)
x, m, c = ej("prepare_absence", {"type": "day_off", "from": "2026-11-10"})
chk("⚠️ la oficina no pide ausencias como si fuera del campo", m and "Unknown tool" in x, x)
chk("⚠️ el propietario, ninguna: va con su recorrido", CT.definiciones("owner", "own") == [])
x, m, c = ej("prepare_close_alert", {"alert_id": "ALR-1"}, octx(rol="owner"))
chk("⚠️ ...ni las ejecuta", m and "Unknown tool" in x, x)
x, m, c = ej("prepare_close_alert", {"alert_id": "ALR-1"}, octx(usuario=""))
chk("sin identidad, nada", m and not c["acciones"], x)

sec("2. Nivel 3: To-do, directo y con la sesión")
ESC.clear()
x, m, c = ej("add_todo", {"project_id": "PRJ-2", "text": "Order rails", "user": "otro"})
chk("apunta en cualquier obra de su empresa, con la sesión como autor", not m and ESC == [("TA.crear", ("PRJ-2", "cliente1", "Order rails", "Admin2"), {})], ESC)
ESC.clear()
x, m, c = ej("add_todo", {"project_id": "PRJ-9", "text": "x"})
chk("⚠️ en una de otra empresa, no", m and ESC == [], (x, ESC))
ESC.clear()
x, m, c = ej("mark_todo", {"project_id": "PRJ-3", "task_id": "TSK-4"})
chk("marca, con la sesión", not m and ESC == [("TA.marcar", ("TSK-4", "PRJ-3", True, "Admin2"), {})], ESC)
_ct = octx()
for i in range(CT.MAX_DIRECTAS + 1):
    x, m, c = ej("add_todo", {"project_id": "PRJ-1", "text": "t%d" % i}, _ct)
chk("⚠️ con tope por pregunta", m and "enough changes" in x, x)

sec("3. ⚠️ Ausencias: lo que espera en SU grupo, con lo que enseña la pantalla")
x, m, a = preparar("prepare_absence_decision", {"absence_id": "AUS-1", "decision": "approve", "note": "Enjoy"})
chk("prepara, y no está hecha", not m and x["status"] == "NOT DONE YET" and "Do not say it is done" in x["next"], x)
chk("la tarjeta: aprobar, qué y quién", a["tipo"] == "ausencia_decidir" and a["titulo"] == "Approve · Annual leave · Helper One", a["titulo"])
chk("las fechas, los días y el motivo", "10/11/2026 to 12/11/2026 · 3 day(s)" in a["detalle"] and "Reason: Family" in a["detalle"], a["detalle"])
chk("⚠️ el saldo que QUEDA, y si se pasa", "Balance after this: -1 of 20 days." in a["detalle"] and "⚠️ This goes over their balance." in a["detalle"], a["detalle"])
chk("⚠️ las obras que pierde, una vez cada una", "Already planned on those days: Bondi. Those days are freed on the board." in a["detalle"], a["detalle"])
chk("la nota, y que se le avisa", "Note for them: Enjoy" in a["detalle"] and a["detalle"].endswith("Helper One is told."), a["detalle"])
chk("⚠️ el modelo también ve las advertencias", x.get("warnings_on_the_card") == ["This goes over their balance.", "Already planned on those days: Bondi. Those days are freed on the board."], x)
chk("lo que se hará: solo ID, decisión y nota", a["datos"] == {"absence_id": "AUS-1", "approve": True, "note": "Enjoy"}, a["datos"])
_saldo["restantes"] = 10.0
x, m, a = preparar("prepare_absence_decision", {"absence_id": "AUS-1", "decision": "reject"})
_saldo["restantes"] = 2.0
chk("rechazar: sin saldo ni tablero, que no cambian", a["titulo"].startswith("Reject ·") and "Balance" not in a["detalle"] and "board" not in a["detalle"] and "warnings_on_the_card" not in x, a["detalle"])
x, m, a = preparar("prepare_absence_decision", {"absence_id": "AUS-2", "decision": "approve"})
chk("⚠️ una ya decidida no se abre, y dice cuáles esperan", m and a is None and "not one of the absences waiting" in x and "AUS-1 (Helper One)" in x, x)
x, m, a = preparar("prepare_absence_decision", {"absence_id": "AUS-8", "decision": "approve"})
chk("⚠️ la de otra empresa tampoco, ni se nombra", m and "AUS-8" not in x.split("Waiting:")[1] and "Ajeno" not in x, x)
x, m, a = preparar("prepare_absence_decision", {"absence_id": "AUS-1", "decision": "maybe"})
chk("una decisión que no es ninguna", m and "approve or reject" in x, x)
x, m, a = preparar("prepare_absence_decision", {"absence_id": "AUS-1", "decision": "approve", "note": "x" * (CT.MAX_NOTA + 1)})
chk("una nota larguísima, no", m and "too long" in x, x)

sec("4. ⚠️ Correcciones de fichaje: las que se pueden revisar, como en Time fixes")
x, m, a = preparar("prepare_time_fix_decision", {"time_fix_id": "COR-1", "decision": "revert", "note": "Check with me"})
chk("revertir: la tarjeta", not m and a["tipo"] == "fichaje_decidir" and a["titulo"] == "Revert time fix · Field Test · Mon 02/11/2026", a["titulo"])
# ⚠️ v663 · CADUCADO a propósito: el cambio se dice en horas TRABAJADAS (una entrada que se adelanta
# media hora SUMA media hora; salía «−0.50 h»)
chk("qué fichaje y las dos horas, con cuánto cambió", "clock in · Mon 02/11/2026 · workday" in a["detalle"] and "Was 07:00 → now 06:30 · +0.50 h worked" in a["detalle"], a["detalle"])
chk("⚠️ si ese día ya se pagó, en qué nómina", "That day was already paid in NOM-3" in a["detalle"] and x["warnings_on_the_card"], a["detalle"])
chk("⚠️ y lo que pasa: vuelve la hora y se le avisa", "The time goes back to 07:00 and Field Test is told." in a["detalle"], a["detalle"])
chk("lo que se hará", a["datos"] == {"time_fix_id": "COR-1", "action": "revertir", "note": "Check with me"}, a["datos"])
x, m, a = preparar("prepare_time_fix_decision", {"time_fix_id": "COR-1", "decision": "approve"})
chk("aprobar: no cambia nada y no se avisa", a["titulo"].startswith("Approve time fix") and "Nobody is told." in a["detalle"] and a["datos"]["action"] == "aprobar", a["detalle"])
x, m, a = preparar("prepare_time_fix_decision", {"time_fix_id": "COR-2", "decision": "revert"})
chk("⚠️ el cierre de una entrada olvidada no se revierte: la reabriría", m and a is None and "no earlier time" in x and "Planning → Time fixes" in x, x)
x, m, a = preparar("prepare_time_fix_decision", {"time_fix_id": "COR-2", "decision": "approve"})
chk("...pero se puede aprobar, y dice que estaba abierta", not m and "Was (open) → now 17:00" in a["detalle"], a and a["detalle"])
x, m, a = preparar("prepare_time_fix_decision", {"time_fix_id": "COR-3", "decision": "approve"})
chk("⚠️ una sustituida por otra posterior no se decide: se revisa aquella", m and "Superseded by COR-4" in x, x)
x, m, a = preparar("prepare_time_fix_decision", {"time_fix_id": "COR-9", "decision": "approve"})
chk("⚠️ la de otra empresa no se abre", m and "not one of the time fixes" in x and "COR-9" not in x.split("Waiting:")[1], x)
x, m, a = preparar("prepare_time_fix_decision", {"time_fix_id": "COR-1", "decision": "reject"})
chk("«reject» no es una de las dos: revertir es como se rechaza", m and "approve or revert" in x, x)
x, m, c = ej("get_inbox", {})
_tf = {r["id"]: r for r in x["time_fixes_to_review"]}
chk("⚠️ la bandeja ya dice cuál está sustituida", _tf["COR-3"]["superseded_by"] == "COR-4" and _tf["COR-1"]["superseded_by"] == "", _tf)

sec("5. Cerrar un aviso: solo los abiertos de SU grupo")
x, m, a = preparar("prepare_close_alert", {"alert_id": "ALR-1"})
chk("la tarjeta: qué obra, quién, cuándo y qué", not m and a["titulo"] == "Close alert · Bondi" and "02/11/2026 · Helper One" in a["detalle"] and "Door jammed" in a["detalle"], a)
# ⚠️ v665 · CADUCADO a propósito: la tarjeta lleva también la nota (vacía en una alarma que no es de seguridad)
chk("lo que se hará", a["datos"] == {"alert_id": "ALR-1", "note": ""}, a["datos"])
x, m, a = preparar("prepare_close_alert", {"alert_id": "ALR-2"})
chk("⚠️ uno ya resuelto, no", m and "not one of this company's open alerts" in x, x)
x, m, a = preparar("prepare_close_alert", {"alert_id": "ALR-3"})
chk("⚠️ uno de otra empresa, no, ni se nombra", m and "ALR-3" not in x.split("Open:")[1], x)

sec("6. Asignar: la persona por su nombre, con los avisos de la pantalla")
x, m, a = preparar("prepare_assignment", {"project_id": "PRJ-1", "person": "helper one"})
chk("encuentra a la persona por su nombre", not m and a["tipo"] == "asignar" and a["datos"] == {"project_id": "PRJ-1", "user": "helper"}, (x, a))
chk("la tarjeta: quién y a qué obra", a["titulo"] == "Assign · Helper One → Bondi", a["titulo"])
_dt = a["detalle"]
chk("⚠️ sus ausencias en esas fechas", "⚠️ Not available: Helper One: Annual leave from 10/11/2026 to 12/11/2026 (not approved yet)" in _dt, _dt)
chk("⚠️ los certificados que la obra exige", "⚠️ Missing the certificates this job requires: Helper One: EWP" in _dt, _dt)
chk("las otras credenciales", "⚠️ Other credentials to check: Helper One — Forklift" in _dt, _dt)
chk("⚠️ si ya está en otra obra, sin iconos ni negritas", "⚠️ Already on another job: Helper One → Otra obra (until 01/12/2026)" in _dt and ":material/" not in _dt and "**" not in _dt, _dt)
chk("⚠️ si no le llegará el aviso", "⚠️ Missing contact details" in _dt, _dt)
# ⚠️ v644 · DESDE HOY (03/11), no desde que empezó la obra (02/11): lo pasado no se planifica
chk("y lo que pasa al confirmar: el tablero, desde hoy hasta el fin de la obra", "They get the job details and the inductions" in _dt
    and "from 03/11/2026 to 20/11/2026" in _dt, _dt)
chk("⚠️ el modelo ve las mismas advertencias", len(x["warnings_on_the_card"]) == 5, x.get("warnings_on_the_card"))
x, m, a = preparar("prepare_assignment", {"project_id": "PRJ-2", "person": "Field Test"})
# Sin fechas de obra, la pantalla avisa de las ausencias que aún no han terminado (el día libre de Field Test) y de
# sus otras obras
chk("sin fechas en la obra: lo dice, y avisa de lo que aún no ha pasado", not m and "no start or end date" in a["detalle"]
    and x["warnings_on_the_card"] == ["Not available: Field Test: Day off from 05/11/2026 to 05/11/2026",
                                      "Already on another job: Field Test → Bondi (until 20/11/2026)"], (x, a and a["detalle"]))
x, m, a = preparar("prepare_assignment", {"project_id": "PRJ-4", "person": "Mei Chen (mei1)"})
chk("⚠️ una obra que ya debía haber acabado: no promete tablero, y dónde hacerlo a mano", not m
    and "end date (29/10/2026) has passed: nothing is planned on the board" in a["detalle"] and "Planning → Panel" in a["detalle"], a and a["detalle"])
x, m, a = preparar("prepare_assignment", {"project_id": "PRJ-1", "person": "Mei Chen"})
chk("⚠️ dos que se llaman igual: pregunta cuál, con su login", m and "More than one person" in x and "Mei Chen (mei1)" in x and "Mei Chen (mei2)" in x, x)
x, m, a = preparar("prepare_assignment", {"project_id": "PRJ-1", "person": "Mei Chen (mei2)"})
chk("...y con el que dice la app, la encuentra", not m and a["datos"]["user"] == "mei2", x)
x, m, a = preparar("prepare_assignment", {"project_id": "PRJ-1", "person": "Field Test"})
chk("quien ya está, no", m and "already assigned" in x, x)
x, m, a = preparar("prepare_assignment", {"project_id": "PRJ-1", "person": "Bobo"})
chk("⚠️ solo gente de campo", m and "nobody in the field staff" in x, x)
x, m, a = preparar("prepare_assignment", {"project_id": "PRJ-1", "person": "Ajeno"})
chk("⚠️ ni de otra empresa, ni se nombra", m and "Ajeno" not in x, x)
x, m, a = preparar("prepare_assignment", {"project_id": "PRJ-9", "person": "Helper One"})
chk("⚠️ ni a una obra de otra empresa", m and "not one of" in x, x)

# get_team, sin leer nada: lo que mira es solo quién es de campo
R.asignaciones_dia = lambda g, u, d=None: []
TC.open_now = lambda g: []
AU.ausentes_en = lambda g, d=None: []
CR.expiring = lambda g, days=30: []
x, m, c = ej("get_team", {})
chk("⚠️ get_team trae toda la gente de campo por su nombre: sin ella no supo quién era «installer» (examen real)",
    x["field_staff"] == ["Field Test", "Helper One", "Mei Chen (mei1)", "Mei Chen (mei2)"], x.get("field_staff"))
chk("⚠️ la herramienta de asignar le dice que la llame con sus palabras", "with the person as they said it" in
    next(h["description"] for h in _d if h["name"] == "prepare_assignment"))

sec("7. Aviso a la cuadrilla")
x, m, a = preparar("prepare_crew_notice", {"project_id": "PRJ-3", "message": "Saturday is cancelled"})
chk("la tarjeta: el texto y a quién va", not m and a["titulo"] == "Notice to the crew · Otra obra" and a["detalle"].startswith("Saturday is cancelled") and "To: Helper One." in a["detalle"], a)
chk("lo que se hará: obra y texto, no la gente", a["datos"] == {"project_id": "PRJ-3", "message": "Saturday is cancelled"}, a["datos"])
x, m, a = preparar("prepare_crew_notice", {"project_id": "PRJ-2", "message": "x"})
chk("⚠️ sin nadie asignado no hay a quién", m and "Nobody is assigned" in x, x)
x, m, a = preparar("prepare_crew_notice", {"project_id": "PRJ-3", "message": "  "})
chk("vacío, no", m and "empty" in x, x)
x, m, a = preparar("prepare_crew_notice", {"project_id": "PRJ-3", "message": "x" * (CT.MAX_AVISO + 1)})
chk("larguísimo, no", m and "too long" in x, x)
_ct = octx()
for i in range(CT.MAX_TARJETAS + 1):
    x, m, c = ej("prepare_crew_notice", {"project_id": "PRJ-3", "message": "m%d" % i}, _ct)
chk("⚠️ con tope de tarjetas esperando", m and "Several cards" in x and len(_ct["acciones"]) == CT.MAX_TARJETAS, x)
x, m, c = ej("prepare_crew_notice", {"project_id": "PRJ-3", "message": "m0"}, octx(acciones=[dict(_ct["acciones"][0])]))
chk("la misma dos veces es la misma tarjeta", not m and "already waiting" in x["next"] and len(c["acciones"]) == 1, x)

sec("8. ⚠️ Confirmar: vuelve a mirar, con la sesión, y hace lo de la pantalla")


def carta(nombre, entrada):
    x, m, a = preparar(nombre, entrada)
    assert not m, x
    return a


ESC.clear()
ok, msg = CT.confirmar(carta("prepare_absence_decision", {"absence_id": "AUS-1", "decision": "approve", "note": "Enjoy"}), octx())
chk("⚠️ aprobar: decisión, tablero y aviso, en ese orden", ok and [e[0] for e in ESC] == ["AU.resolver", "roster", "aus_avisar"], ESC)
chk("⚠️ con quien está en la sesión", ESC[0][1] == ("AUS-1", True, "Admin2", "Enjoy"), ESC[0])
chk("y lo dice, con el tablero", "Absence approved." in msg and "2 day(s) marked in the planner." in msg, msg)
ESC.clear()
ok, msg = CT.confirmar(carta("prepare_absence_decision", {"absence_id": "AUS-1", "decision": "reject"}), octx())
chk("rechazar: decisión y aviso, sin tablero", ok and [e[0] for e in ESC] == ["AU.resolver", "aus_avisar"] and ESC[0][1][1] is False, ESC)
_a = carta("prepare_absence_decision", {"absence_id": "AUS-1", "decision": "approve"})
AUS[0]["Status"] = AU.APROBADA                     # otro la decidió mientras la tarjeta esperaba
ESC.clear()
ok, msg = CT.confirmar(_a, octx())
AUS[0]["Status"] = AU.PENDIENTE
chk("⚠️ ya decidida por otro: no se toca, y lo dice", not ok and ESC == [] and "not one of the absences waiting" in msg, (msg, ESC))
ESC.clear()
ok, msg = CT.confirmar(_a, octx(grupo="otro"))
chk("⚠️ con la sesión de otra empresa, no", not ok and ESC == [], (msg, ESC))
ok, msg = CT.confirmar(_a, cctx())
chk("⚠️ el campo no confirma lo de la oficina", not ok and ESC == [] and "not recognised" in msg, msg)
ok, msg = CT.confirmar({"tipo": "parte", "datos": {"project_id": "PRJ-1", "text": "x"}}, octx())
chk("⚠️ ni la oficina lo del campo", not ok and ESC == [] and "not recognised" in msg, msg)
ok, msg = CT.confirmar(_a, octx(usuario=""))
chk("sin identidad, nada", not ok and ESC == [], msg)

ESC.clear()
ok, msg = CT.confirmar(carta("prepare_time_fix_decision", {"time_fix_id": "COR-1", "decision": "revert", "note": "n"}), octx())
chk("⚠️ revertir: la hora vuelve y se le avisa", ok and [e[0] for e in ESC] == ["CO.revertir", "cor_avisar"] and ESC[0][1] == ("COR-1", "Admin2", "n"), ESC)
ESC.clear()
ok, msg = CT.confirmar(carta("prepare_time_fix_decision", {"time_fix_id": "COR-1", "decision": "approve"}), octx())
chk("aprobar: solo se confirma, sin aviso", ok and [e[0] for e in ESC] == ["CO.aprobar"], ESC)
_q = carta("prepare_time_fix_decision", {"time_fix_id": "COR-1", "decision": "approve"})
_q["datos"]["action"] = "sustituida"            # cerrar como sustituida no es una de las cinco
ESC.clear()
ok, msg = CT.confirmar(_q, octx())
chk("⚠️ una tarjeta tocada no hace otra cosa", not ok and ESC == [], (msg, ESC))

ESC.clear()
ok, msg = CT.confirmar(carta("prepare_close_alert", {"alert_id": "ALR-1"}), octx())
# ⚠️ v665 · CADUCADO a propósito: Confirm pasa también la nota (vacía en una alarma que no es de seguridad)
chk("cerrar: como oficina, con la sesión", ok and ESC == [("AL.resolve_alert", ("ALR-1", "Admin2"), {"gestor": True, "nota": ""})], ESC)
_q = carta("prepare_close_alert", {"alert_id": "ALR-1"})
ALS[0]["Status"] = "resuelta"
ESC.clear()
ok, msg = CT.confirmar(_q, octx())
ALS[0]["Status"] = "abierta"
chk("⚠️ ya cerrado: nada", not ok and ESC == [], (msg, ESC))

ESC.clear()
ok, msg = CT.confirmar(carta("prepare_assignment", {"project_id": "PRJ-1", "person": "Helper One"}), octx())
chk("⚠️ asignar: lo que hace Save changes, en orden", ok and [e[0] for e in ESC] == ["P.add_field_user", "notify_assignment", "autopoblar"], ESC)
chk("con la persona, y el tablero desde HOY hasta el fin", ESC[0][1] == ("PRJ-1", "helper") and ESC[2][1] == ("cliente1", "PRJ-1", ["helper"], "2026-11-03", "2026-11-20"), ESC)
chk("y lo dice todo", "Helper One assigned to Bondi." in msg and "They were told." in msg and "4 day(s) assigned" in msg and "1 day(s) already taken" in msg, msg)
_q = carta("prepare_assignment", {"project_id": "PRJ-1", "person": "Helper One"})
O1["FieldAssigned"] = "campo000;helper"
ESC.clear()
ok, msg = CT.confirmar(_q, octx())
O1["FieldAssigned"] = "campo000"
chk("⚠️ si alguien la asignó mientras tanto, no la repite", not ok and ESC == [] and "already assigned" in msg, (msg, ESC))
ESC.clear()
ok, msg = CT.confirmar(carta("prepare_assignment", {"project_id": "PRJ-4", "person": "Mei Chen (mei1)"}), octx())
chk("⚠️ en una obra vencida asigna y avisa, sin tocar el tablero, y lo dice", ok and [e[0] for e in ESC] == ["P.add_field_user", "notify_assignment"]
    and "end date has passed" in msg, (msg, ESC))
_canal["hay"] = False
ESC.clear()
ok, msg = CT.confirmar(carta("prepare_assignment", {"project_id": "PRJ-2", "person": "Field Test"}), octx())
_canal["hay"] = True
chk("sin canales ni fechas: asigna, y lo dice sin inventar", ok and [e[0] for e in ESC] == ["P.add_field_user"] and "nobody was told" in msg and "Planner" not in msg, (msg, ESC))

ESC.clear()
_q = carta("prepare_crew_notice", {"project_id": "PRJ-3", "message": "Saturday is cancelled"})
O3["FieldAssigned"] = "helper;mei1"
ESC.clear()
ok, msg = CT.confirmar(_q, octx())
chk("⚠️ el aviso va a la cuadrilla de AHORA, con la sesión", ok and ESC == [("AL.notify_change", ("PRJ-3", "cliente1", "Saturday is cancelled", "Admin2", ["helper", "mei1"], "Otra obra"), {})], ESC)
chk("y lo dice", "Sent to 2 person(s) on Otra obra" in msg and "ALR-0009" in msg, msg)
O3["FieldAssigned"] = ""
ESC.clear()
ok, msg = CT.confirmar(_q, octx())
O3["FieldAssigned"] = "helper"
chk("⚠️ si ya no queda nadie, no manda", not ok and ESC == [], (msg, ESC))

sec("9. Las pantallas y el asistente, con la MISMA función")
ESC.clear()
ok, msg = AUI.decidir("cliente1", "AUS-8", True, "Admin2")
chk("⚠️ `decidir` no toca la de otra empresa", not ok and ESC == [], (msg, ESC))
_s = leer("core/ausencias_ui.py")
chk("⚠️ la bandeja de Absences decide con `decidir`", "decidir(grupo, aid, aprobar, quien" in funcion(_s, "_ejecutar") and "AU.resolver" not in funcion(_s, "_ejecutar"))
_s = leer("core/correcciones_ui.py")
chk("⚠️ la de Time fixes, con `hacer`", "hacer(acc, grupo, quien)" in funcion(_s, "_ejecutar") and "C.aprobar" not in funcion(_s, "_ejecutar"))
ESC.clear()
ok, msg = CUI.hacer({"cid": "COR-3", "accion": "aprobar"}, "cliente1", "Admin2")
chk("⚠️ `hacer` tampoco aprueba una sustituida (ni desde la pantalla)", not ok and ESC == [] and "Superseded" in msg, msg)
ok, msg = CUI.hacer({"cid": "COR-2", "accion": "revertir"}, "cliente1", "Admin2")
chk("⚠️ ni reabre una entrada olvidada", not ok and ESC == [], msg)
ok, msg = CUI.hacer({"cid": "COR-3", "accion": "sustituida", "por": "COR-4"}, "cliente1", "Admin2")
chk("cerrarla como sustituida sigue funcionando", ok and ESC[-1][0] == "CO.cerrar_sustituida", ESC)
ESC.clear()
ok, msg = CUI.hacer({"cid": "COR-1", "accion": "ajustar", "hora": "06:45"}, "cliente1", "Admin2")
chk("fijar la hora sigue funcionando, y avisa", ok and [e[0] for e in ESC] == ["CO.ajustar", "cor_avisar"], ESC)
ok, msg = CUI.hacer({"cid": "COR-1", "accion": "ajustar", "hora": "mediodía"}, "cliente1", "Admin2")
chk("una hora ilegible, dicho", not ok and "could not be read" in msg, msg)
ok, msg = CUI.hacer({"cid": "COR-1", "accion": "otra"}, "cliente1", "Admin2")
chk("una acción desconocida: nada, y sin mensaje", (ok, msg) == (False, ""))
_av = PU.avisos_asignacion(["helper"], "cliente1", exclude_pid="PRJ-1", certs_req=["EWP", "White Card"], fechas=("2026-11-02", "2026-11-20"))
chk("`avisos_asignacion` devuelve las seis listas", set(_av) == {"fuera", "ocupados", "no_cumplen", "cert_pv", "cred_mal", "sin_contacto"} and all(_av.values()) is False and _av["fuera"] and _av["no_cumplen"], _av)
_pint = []
_st0 = PU.st
PU.st = types.SimpleNamespace(warning=_pint.append, info=_pint.append, error=_pint.append)
PU._avisar_asignados(["helper"], "cliente1", exclude_pid="PRJ-1", certs_req=["EWP", "White Card"], fechas=("2026-11-02", "2026-11-20"))
PU.st = _st0
_todo = "\n".join(_pint)
chk("⚠️ y la pantalla pinta exactamente esos", all(x in _todo for k in ("fuera", "ocupados", "no_cumplen", "cred_mal") for x in _av[k]) and "Helper One" in _todo, _pint)

sec("9b. ⚠️ El tablero, desde HOY (también al guardar en Projects → Data)")


class _HojaTablero:
    def __init__(self):
        self.escr = []

    def get_all_values(self):
        return [["ID", "Group", "Week", "User", "Data"]]

    def batch_update(self, u, **k):
        self.escr.append(("upd", u))

    def append_rows(self, filas, **k):
        self.escr.append(("add", filas))


_h = _HojaTablero()
_ws0, _inv0 = R._ws_roster, R._invalidate
R._ws_roster, R._invalidate = (lambda: _h), (lambda: None)
from core import hojas as _HJ                                      # noqa: E402
_ids0 = _HJ.siguientes_ids_libres
_HJ.siguientes_ids_libres = lambda p, n, k, propia=None: ["ROS-%04d" % (n + i + 1) for i in range(k)]
_res = _autopoblar_real("cliente1", "PRJ-1", ["helper"], "2026-10-26", "2026-11-06")
_filas = [f for e in _h.escr if e[0] == "add" for f in e[1]]
chk("⚠️ una obra empezada: solo de hoy (mar 03/11) en adelante, ni su semana pasada ni el lunes", _res["llenadas"] == 4
    and [f[2] for f in _filas] == ["2026-11-02"] and set(json.loads(_filas[0][4])) == {"mar", "mie", "jue", "vie"}, (_res, _filas))
_h.escr.clear()
_res = _autopoblar_real("cliente1", "PRJ-1", ["helper"], "2026-09-14", "2026-10-29")
chk("⚠️ una obra que ya debía haber acabado: nada, y lo dice", _res.get("pasado") is True and _res["llenadas"] == 0 and _h.escr == [], (_res, _h.escr))
_h.escr.clear()
_res = _autopoblar_real("cliente1", "PRJ-1", ["helper"], "2026-11-09", "2026-11-13")
chk("una que empieza más adelante, desde su inicio", _res["llenadas"] == 5 and "pasado" not in _res, _res)
R._ws_roster, R._invalidate, _HJ.siguientes_ids_libres = _ws0, _inv0, _ids0
chk("la pantalla también lo dice al guardar", 'r.get("pasado")' in funcion(leer("core/projects_ui.py"), "_autoagenda")
    and "end date has already passed" in funcion(leer("core/projects_ui.py"), "_autoagenda"))

sec("10. ⚠️ Lo que nunca hace, ni confirmado")
_mal_nombre = ("invoice", "payment", "collect", "payroll", "payslip", "xero", "delete", "remove", "rate", "role", "user", "progress", "credit", "stage")
chk("⚠️ ninguna herramienta lo es", not [n for n in _n if any(x in n for x in _mal_nombre)], _n)
_src = leer("core/chat_tools.py")
_arb = ast.parse(_src)
_of = {"_preparar_decision_ausencia", "_preparar_decision_fichaje", "_preparar_cierre_aviso", "_preparar_asignacion", "_preparar_aviso_cuadrilla",
       "_confirmar_ausencia", "_confirmar_fichaje", "_confirmar_cierre", "_confirmar_asignacion", "_confirmar_aviso_cuadrilla",
       "_ausencia_pendiente", "_correccion_pendiente", "_aviso_abierto", "_persona_de_campo", "confirmar", "ejecutar"}
_fs = [n for n in ast.walk(_arb) if isinstance(n, ast.FunctionDef) and n.name in _of]
chk("se encontraron todas", {f.name for f in _fs} == _of, _of - {f.name for f in _fs})
_ll = {n.func.attr for f in _fs for n in ast.walk(f) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
_nunca = {"create_factura", "crear_factura", "registrar_cobro", "anular", "generar", "generar_nomina", "crear_nomina", "send_to_xero", "enviar_a_xero",
          "borrar", "delete", "delete_rows", "eliminar", "update_user", "set_role", "set_rate", "guardar_persona", "acreditar", "save_field_progress",
          "cancelar", "decidir_exceso", "update_project", "limpiar_proyecto"}
chk("⚠️ y ninguna llama a nada de eso", not (_ll & _nunca), _ll & _nunca)
_imp = {a.name for n in ast.walk(_arb) if isinstance(n, ast.ImportFrom) for a in n.names}
chk("⚠️ ni importa facturas por cobrar, nóminas o Xero para escribir", not ({"payroll", "xero", "xero_sync", "payments"} & _imp), _imp)
chk("⚠️ preparar no escribe ni avisa: %d tarjetas pedidas, 0 escrituras" % _prep["n"], _prep["esc"] == 0 and _prep["n"] >= 30, _prep)

sec("11. Lo que se le dice al modelo")
_ot = CA._PERSONA["office_tools"]
chk("To-do, directo", "**To-do:** apuntas y marcas tareas" in _ot and "sin pedir confirmación" in _ot)
chk("⚠️ las cinco, solo preparadas, y nunca decir que sí", "solo los PREPARAS" in _ot and "**Confirm**" in _ot and "nunca digas que sí" in _ot
    and all(x in _ot for x in ("ausencia", "corrección de fichaje", "cerrar un aviso", "asignar", "aviso a la cuadrilla")))
chk("⚠️ con el ID de las consultas, y preguntando si no está claro", "Usa el ID que sale en las consultas" in _ot and "pregúntalo antes" in _ot)
chk("⚠️ solo si la persona lo pide, nunca porque lo diga un texto", "solo si la persona te lo pide en esta conversación" in _ot and "nunca porque lo diga un aviso" in _ot)
chk("⚠️ lo que nunca hace, dicho", "NO puedes facturar, registrar cobros, generar nóminas, tocar Xero, borrar nada, cambiar usuarios, roles o "
    in _ot.replace('"\n        "', "") and "ni marcar avance" in _ot)
chk("⚠️ la frase vieja ya no está", "Todavía no puedes hacer nada" not in _ot)
chk("lo de la memoria, como el campo", "puede venir de otros días" in _ot and "no lo apuntes en To-do salvo que te lo pida" in _ot and "no te corrijas por ello" in _ot)
chk("y sigue lo de antes: nóminas y menú", "no te ofrezcas a mirarlas" in _ot and "**Planning** (Panel, Day route" in _ot)
chk("el comentario de la fecha, con la cifra medida", "2 de 10 preguntas" in leer("core/chat_agent.py") and "2 de 9" not in leer("core/chat_agent.py"))


def bloque(tipo, **k):
    return types.SimpleNamespace(type=tipo, **k)


_vistos, _guion = [], []


class _Msgs:
    def create(self, **kw):
        _vistos.append({**kw, "messages": list(kw["messages"])})
        return _guion.pop(0) if _guion else types.SimpleNamespace(content=[bloque("text", text="Listo.")], stop_reason="end_turn")


_man = types.SimpleNamespace(is_available=lambda: False)
# ⚠️ v655 · `**_kw`: el cliente de verdad lleva ahora timeout y max_retries (antes, solo la clave)
CA.anthropic = types.SimpleNamespace(Anthropic=lambda api_key=None, **_kw: types.SimpleNamespace(beta=types.SimpleNamespace(messages=_Msgs())),
                                     AuthenticationError=type("A", (Exception,), {}), RateLimitError=type("R", (Exception,), {}))
CA.st = types.SimpleNamespace(secrets={"ANTHROPIC_API_KEY": "x"})
sys.modules["core.manuals"] = _man
core.manuals = _man
_guion += [types.SimpleNamespace(content=[bloque("tool_use", id="t1", name="prepare_absence_decision", input={"absence_id": "AUS-1", "decision": "approve"}),
                                          bloque("tool_use", id="t2", name="add_todo", input={"project_id": "PRJ-1", "text": "Call the client"})],
                                 stop_reason="tool_use")]
_tarj = []
ESC.clear()
_r = CA.get_chat_response("approve Helper's leave and note to call the client", [], None, None, rol="administrator", grupo="cliente1",
                          usuario="Admin2", nombre="Bobo", acciones=_tarj)
_res = {b["tool_use_id"]: b for b in _vistos[1]["messages"][-1]["content"] if b.get("type") == "tool_result"}
chk("en el bucle real: una tarjeta y una tarea", len(_tarj) == 1 and _tarj[0]["tipo"] == "ausencia_decidir" and [e[0] for e in ESC] == ["TA.crear"], (_tarj, ESC))
chk("⚠️ y el modelo lee que la ausencia NO está hecha, con lo que advierte", "NOT DONE YET" in _res["t1"]["content"] and "warnings_on_the_card" in _res["t1"]["content"], _res)
chk("la tarea, con la sesión", ESC[0][1][3] == "Admin2", ESC)
_s = "".join(b["text"] for b in _vistos[0]["system"])
chk("⚠️ las doce le llegan, y la persona nueva", [h["name"] for h in _vistos[0]["tools"]] == _n and "solo los PREPARAS" in _s)

sec("12. La memoria de la oficina, y la foto solo del campo")
chk("⚠️ recuerdan el campo y la oficina; el propietario no", CU._CON_MEMORIA == ("field", "administrator"))
_ses = st.session_state


def sesion(rol, usuario, hist=None):
    for k in ("_chat_recordada", "chat_history", "_chat_acciones", "_chat_pet"):
        _ses.pop(k, None)
    _ses["auth"] = {"usuario": usuario, "nombre": usuario, "rol": rol, "grupo": "cliente1"}
    if hist is not None:
        _ses["chat_history"] = hist


_mem[("Admin2", "cliente1")] = [{"role": "user", "content": "de ayer"}]
_mem[("campo000", "cliente1")] = [{"role": "user", "content": "del campo"}]
sesion("administrator", "Admin2", [])
CU.recordar()
chk("⚠️ al abrir, la oficina recupera SU conversación", [m["content"] for m in _ses["chat_history"]] == ["de ayer"], _ses.get("chat_history"))
ESC.clear()
_ses["chat_history"].append({"role": "assistant", "content": "vale"})
CU.memorizar()
chk("y la guarda como suya", ESC and ESC[-1][0] == "CM.guardar" and ESC[-1][1][:2] == ("Admin2", "cliente1"), ESC)
ESC.clear()
CU.olvidar()
chk("⚠️ limpiar borra la suya, no la de otro", ESC == [("CM.borrar", ("Admin2", "cliente1"), {})], ESC)
_mem[("own", "cliente1")] = [{"role": "user", "content": "del propietario"}]   # aunque la hubiera
sesion("owner", "own", [])
ESC.clear()
CU.recordar()
CU.memorizar()
CU.olvidar()
chk("⚠️ el propietario: ni recuerda ni guarda", _ses["chat_history"] == [] and ESC == [], ESC)
chk("⚠️ la foto, todavía solo el campo", CU.opciones_foto("administrator") == {} and CU.opciones_foto("owner") == {} and CU.opciones_foto("field"))
_a = leer("app.py")
chk("la oficina sabe que se guarda, sin prometer fotos", 'elif _ROL == "administrator":\n            st.caption(t("Your conversation is kept for 14 days."))' in _a)

sec("13. ⚠️ Confirm, con clics: la tarjeta de la oficina hace lo de la pantalla")
GUION = r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
from core import chat_ui as U
st.session_state["auth"] = {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"}
if not st.session_state.get("_ya"):
    st.session_state["_ya"] = True
    st.session_state["_chat_acciones"] = list(st.session_state["_cartas"])
U.atender()
for m in st.session_state.get("chat_history", []):
    st.write(m["content"])
U.tarjetas()
'''
_carta = carta("prepare_absence_decision", {"absence_id": "AUS-1", "decision": "approve"})
at = AppTest.from_string(GUION, default_timeout=60)
at.session_state["_cartas"] = [_carta]
at.run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_ok = next((b for b in at.button if b.key == "chat_ok_" + _carta["id"]), None)
chk("la tarjeta, con Confirm", _ok is not None and any("Balance after this" in m.value for m in at.markdown), [m.value for m in at.markdown])
ESC.clear()
_ok.click().run()
chk("⚠️ Confirm decide con la función de la bandeja y la sesión", [e[0] for e in ESC][:3] == ["AU.resolver", "roster", "aus_avisar"] and ESC[0][1][2] == "Admin2", ESC)
chk("se va la tarjeta y queda dicho", at.session_state["_chat_acciones"] == [] and at.session_state["chat_history"][-1]["content"].startswith("✅ Absence approved."), at.session_state["chat_history"])
chk("⚠️ y queda en SU memoria", any(e[0] == "CM.guardar" and e[1][0] == "Admin2" for e in ESC), ESC)

print("\n=== verif_v644: %d OK, %d FALLOS ===" % (n_ok, len(fallos)))
for f in fallos:
    print("   -", f)
sys.exit(1 if fallos else 0)
