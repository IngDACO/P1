"""v587 · LAS OBRAS CON DESMONTAJE NO SE PODÍAN CREAR (decisión del usuario: «Ok dale resuelve
los fallos»). Lo destapó poblar la app de material de prueba por todos los caminos de alta.

  1. ⚠️ «New project»: al contestar tracción/hidráulico la pregunta dejaba de pintarse,
     Streamlit borraba su valor y «Create project» decía «Answer this first» SIEMPRE.
     Ninguna obra Ripout ni Ripout + Installation se podía crear → la pregunta se pinta
     siempre que el tipo la necesita, con su respuesta.
  2. ⚠️ Desde una cotización («Turn it into a project»): no preguntaba tracción/hidráulico
     (el desmontaje nacía SIN la demolición en el plan), dejaba NS 0 (una instalación
     nacía SIN plan, y la ayuda decía «no activities» cuando nacía con una) y a un
     Delivery/Other no le pedía fecha de fin (PRJ-0033 nació sin ella) → las reglas del
     alta normal, en la pantalla Y en el motor.

Todo EJECUTANDO con AppTest y el motor con la hoja sustituida: no se escribe nada.
"""
import datetime as dt
import json
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Admin2", "rol": "administrator", "grupo": "cliente1"}
from streamlit.testing.v1 import AppTest                         # noqa: E402

fallos, n_ok = [], 0
TRAC = "Rip out mechanical components - traction"
HIDR = "Rip out mechanical components - hydraulic"


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("   ok   " + q)
    else:
        fallos.append(q)
        print("   FALLO " + q + (("  -> " + str(det)) if det != "" else ""))


def _w(at, kind, key):
    return next((x for x in getattr(at, kind) if x.key == key), None)


print("1. ⚠️ La respuesta tracción/hidráulico SE QUEDA (antes se borraba en la pasada siguiente)")
G1 = r'''
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "Admin2", "rol": "administrator", "grupo": "cliente1"})
from core import projects_ui as PU
st.session_state["_PEND"] = len(PU._pregunta_etapas(st.session_state.get("_T", "Ripout + Installation"), "adm"))
st.session_state["_COND"] = PU._cond_elegidas("adm")
'''
at = AppTest.from_string(G1).run()
r = _w(at, "radio", "np_demol_adm")
chk("sin contestar: la pregunta está y queda 1 pendiente", r is not None and at.session_state["_PEND"] == 1)
r.set_value(TRAC)
at.run()
chk("contestada: la pregunta SIGUE en pantalla con su respuesta (antes desaparecía)",
    _w(at, "radio", "np_demol_adm") is not None and _w(at, "radio", "np_demol_adm").value == TRAC)
at.run()
at.run()
chk("⚠️ …y dos pasadas después la respuesta sigue (antes volvía vacía)",
    at.session_state["_COND"] == (TRAC,) and at.session_state["_PEND"] == 0, at.session_state["_COND"])
at = AppTest.from_string(G1)
at.session_state["_T"] = "Installation"
at.run()
chk("una instalación no pregunta nada", _w(at, "radio", "np_demol_adm") is None and at.session_state["_PEND"] == 0)

print("\n2. ⚠️ «New project» crea un Ripout + Installation de principio a fin (AppTest, sin hoja)")
G2 = r'''
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "Admin2", "rol": "administrator", "grupo": "cliente1"})
from core import projects_ui as PU, projects as P, clientes as C, notify, flash
_LOG = st.session_state.setdefault("_LOG", [])
P.create_project = lambda *a, **k: (_LOG.append(k) or (True, "PRJ-9999"))
P.list_projects = lambda *a, **k: []
C.list_clientes = lambda *a, **k: []
notify.notify_assignment = lambda *a, **k: {}
PU._field_users = lambda g: []
flash.mostrar()
PU._nuevo_proyecto_form("cliente1", key="adm")
'''


def _alta(tipo, demol, ns=6):
    a = AppTest.from_string(G2, default_timeout=120).run()
    _w(a, "selectbox", "np_tipo_adm").set_value(tipo)
    a.run()
    if demol:
        _w(a, "radio", "np_demol_adm").set_value(demol)
        a.run()
    _w(a, "number_input", "np_ns_adm").set_value(ns)
    a.run()
    _w(a, "text_input", "np_nom_adm").set_value("ZZ alta v587")
    next(b for b in a.button if "Create project" in str(b.label)).click()
    a.run()
    return a


at = _alta("Ripout + Installation", TRAC)
_k = at.session_state["_LOG"][0] if at.session_state["_LOG"] else {}
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("⚠️ se CREA (antes: «Answer this first» siempre)", bool(_k) and not [e for e in at.error],
    [e.value for e in at.error])
chk("…con la demolición de TRACCIÓN en el plan sellado",
    _k and json.loads(_k.get("stage_plan") or "{}").get("condicionales") == [TRAC], _k.get("stage_plan"))
at = _alta("Ripout", HIDR, ns=4)
_k = at.session_state["_LOG"][0] if at.session_state["_LOG"] else {}
chk("un Ripout hidráulico también se crea, con lo suyo",
    _k and json.loads(_k.get("stage_plan") or "{}").get("condicionales") == [HIDR], _k.get("stage_plan"))
at = _alta("Ripout + Installation", None)
chk("sin contestar, sigue sin crearse (la regla de v512 se queda)",
    not at.session_state["_LOG"] and any("Answer this first" in e.value for e in at.error))

print("\n3. ⚠️ «Turn it into a project» (cotización aceptada): las reglas del alta normal (AppTest)")
G3 = r'''
import datetime as dt
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "Admin2", "rol": "administrator", "grupo": "cliente1"})
from core import quotes_ui as QU, quotes as Q, flash
_LOG = st.session_state.setdefault("_LOG", [])
Q.aceptar_y_crear_proyecto = lambda cid, **k: (_LOG.append(k) or (True, "PRJ-9998"))
flash.mostrar()
QU._crear_proyecto("cliente1", {"ID": "COT-9", "ClientName": "ZZ", "Number": "0009"},
                   {"costo": 100.0, "subtotal": 150.0})
'''


def _nums(a):
    return [x for x in a.number_input if "Stops" in str(x.label)]


def _fins(a):
    return [x for x in a.date_input if "finish" in str(x.label)]


def _crear(a):
    next(b for b in a.button if "Create the project" in str(b.label)).click()
    a.run()


at = AppTest.from_string(G3, default_timeout=120).run()
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("Installation: NS obligatorio (≥ 2) y sin fecha de fin",
    _nums(at) and _nums(at)[0].min == 2 and _nums(at)[0].value == 2 and not _fins(at),
    [(x.label, x.min, x.value) for x in _nums(at)])
_w(at, "selectbox", "cot_prj_tipo_COT-9").set_value("Ripout + Installation")
at.run()
chk("⚠️ Ripout + Installation: PREGUNTA tracción o hidráulico (antes no)", _w(at, "radio", "np_demol_cot_COT-9") is not None)
_crear(at)
chk("…sin contestar NO crea y lo dice", not at.session_state["_LOG"]
    and any("Answer this first" in e.value for e in at.error), [e.value for e in at.error])
_w(at, "radio", "np_demol_cot_COT-9").set_value(TRAC)
at.run()
_nums(at)[0].set_value(10)
_crear(at)
_k = at.session_state["_LOG"][0] if at.session_state["_LOG"] else {}
chk("⚠️ contestado: crea con la demolición, el tipo y el NS", _k.get("condicionales") == (TRAC,)
    and _k.get("tipo") == "Ripout + Installation" and _k.get("ns") == 10, _k)
at = AppTest.from_string(G3, default_timeout=120).run()
_w(at, "selectbox", "cot_prj_tipo_COT-9").set_value("Delivery")
at.run()
chk("Delivery: SIN NS y CON fecha de fin (antes nacía sin ella)", not _nums(at) and _fins(at))
_fins(at)[0].set_value(dt.date.today() + dt.timedelta(days=3))
at.run()
_crear(at)
_k = at.session_state["_LOG"][0] if at.session_state["_LOG"] else {}
chk("…y la pasa al motor", _k.get("fecha_fin") == dt.date.today() + dt.timedelta(days=3)
    and _k.get("ns") == 0, _k)

print("\n4. ⚠️ El motor `aceptar_y_crear_proyecto` (la hoja sustituida)")
import importlib                                                 # noqa: E402
from core import quotes as Q, projects as P                      # noqa: E402
# ⚠️ El guion de la sección 3 dejó `aceptar_y_crear_proyecto` SUSTITUIDO (AppTest corre en
# este mismo proceso, la lección de v574): sin recargar, se probaba el doble.
Q = importlib.reload(Q)
_o = {n: getattr(Q, n) for n in ("get_cotizacion", "lineas_de", "totales", "_ws", "_fila")}
_cp = P.create_project
_L = []
try:
    Q.get_cotizacion = lambda cid: {"ID": cid, "Group": "cliente1", "ClientName": "ZZ", "ClientID": "",
                                    "Number": "0009", "TaxPct": "10"}
    Q.lineas_de = lambda c: [{"x": 1}]
    Q.totales = lambda l, imp=0: {"costo": 100.0, "subtotal": 150.0}
    Q._ws = lambda: None
    Q._fila = lambda w, cid: (None, None)
    P.create_project = lambda *a, **k: (_L.append(k) or (True, "PRJ-9997"))
    I = dt.date(2026, 10, 26)
    r = Q.aceptar_y_crear_proyecto("COT-9", tipo="Installation", fecha_inicio=I, ns=0)
    chk("⚠️ Installation con NS 0 → NO crea (antes nacía sin plan)", r[0] is False and "stops" in r[1] and not _L, r)
    r = Q.aceptar_y_crear_proyecto("COT-9", tipo="Ripout + Installation", fecha_inicio=I, ns=6)
    chk("⚠️ desmontaje sin tracción/hidráulico → NO crea", r[0] is False and "Answer this first" in r[1] and not _L, r)
    Q.aceptar_y_crear_proyecto("COT-9", tipo="Ripout + Installation", fecha_inicio=I, ns=6,
                               condicionales=(TRAC,))
    _k = _L[-1] if _L else {}
    chk("…con la respuesta crea, con plan sellado y cronograma",
        _k and json.loads(_k["stage_plan"]).get("condicionales") == [TRAC] and len(_k["activities"]) > 1, _k.get("stage_plan"))
    Q.aceptar_y_crear_proyecto("COT-9", tipo="Delivery", fecha_inicio=I, fecha_fin=I + dt.timedelta(days=2))
    _k = _L[-1]
    chk("⚠️ Delivery con su fecha de fin y la duración que cubre (3 días)",
        _k["fecha_fin_est"] == "2026-10-28" and _k["activities"][0]["duracion"] == 3 and not _k["stage_plan"], _k)
    _n = len(_L)
    r = Q.aceptar_y_crear_proyecto("COT-9", tipo="Delivery", fecha_inicio=I, fecha_fin=I - dt.timedelta(days=1))
    chk("…fin antes del inicio → NO crea", r[0] is False and len(_L) == _n, r)
    Q.aceptar_y_crear_proyecto("COT-9", tipo="Other", fecha_inicio=I)
    chk("sin fecha de fin (otra pantalla que no la pase): el mismo día, nunca vacía",
        _L[-1]["fecha_fin_est"] == "2026-10-26", _L[-1]["fecha_fin_est"])
finally:
    for n, f in _o.items():
        setattr(Q, n, f)
    P.create_project = _cp

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
sys.exit(1 if fallos else 0)
