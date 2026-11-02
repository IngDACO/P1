# -*- coding: utf-8 -*-
"""v640 · EL FIELD ASSISTANT PREPARA Y HACE (niveles 2 y 3 de autonomía, 02/11/2026).

Decisión del usuario: el parte, el aviso a la oficina y las ausencias los prepara y la persona confirma;
apuntar y marcar en To-do lo hace solo, porque es reversible y no avisa a nadie. Fichar, firmar, enviar el
Pre-Start o el checklist y acreditar avance NO, ni confirmados.

Lo que protege, SIN la API ni la hoja (escrituras y avisos sustituidos, y CONTADOS):
  (a) lo que no debe hacer ni existe como herramienta;
  (b) ⚠️ PREPARAR NO ESCRIBE: ni hoja ni avisos, hasta el toque de Confirm;
  (c) los errores salen antes de la tarjeta, con las reglas de siempre;
  (d) confirmar hace lo de la tarjeta, con la identidad de la sesión y la obra comprobada otra vez;
  (e) ⚠️ un doble toque no manda dos veces; cancelar no hace nada; un fallo deja la tarjeta para reintentar;
  (f) lo directo tiene tope, no sale de sus obras y no avisa;
  (g) la ausencia hace lo mismo por la pantalla que por el asistente (`registrar`).
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
st.session_state["auth"] = {"usuario": "campo000", "nombre": "Field Test", "rol": "field", "grupo": "cliente1"}

from streamlit.testing.v1 import AppTest                          # noqa: E402

import core                                                        # noqa: E402
from core import alerts as AL, ausencias as AU, ausencias_ui as AUI, chat_agent as CA, chat_tools as CT   # noqa: E402
from core import clock, daily_log as DL, projects as P, tareas as TA   # noqa: E402

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
OBRA = {"ID": "PRJ-1", "Name": "Bondi Tower", "Group": "cliente1"}
_quien = {"campo000": [OBRA]}
P.list_projects_for_field = lambda u, grupo=None, incluir_internos=False: list(_quien.get(u, []))
ESC = []                 # todo lo que escribe o avisa pasa por aquí


def apunta(nombre, res):
    def f(*a, **k):
        ESC.append((nombre, a, k))
        return res() if callable(res) else res
    return f


TA.crear = apunta("TA.crear", (True, "TSK-9"))
TA.marcar = apunta("TA.marcar", (True, "ok"))
DL.crear = apunta("DL.crear", (True, "DL-9"))
AL.report_problem = apunta("alerta", (True, "AL-9"))
AU.solicitar = apunta("AU.solicitar", (True, "AUS-9"))
AU.aplicar_al_roster = apunta("roster", (True, 1))
AUI._avisar_admins = apunta("avisar_admins", None)
AU.get = lambda aid: {"ID": aid}
_aus = {"problema": "", "exceso": 0}
AU.problema_solicitud = lambda *a, **k: _aus["problema"]
AU.exceso = lambda g, u, tipo, n: _aus["exceso"]
AU.dias_del_rango = lambda d, h, f=False: ["x"] * 2


def nctx(**k):
    return {"usuario": "campo000", "nombre": "Field Test", "grupo": "cliente1", "rol": "field", "acciones": [], **k}


def ej(nombre, entrada, ctx=None):
    c = ctx if ctx is not None else nctx()
    txt, mal = CT.ejecutar(nombre, entrada, c)
    return (json.loads(txt) if not mal else txt), mal, c


# ═════════════════════════════════════════════════════════════════
sec("1. ⚠️ Lo que no debe hacer ni existe")
_nom = [h["name"] for h in CT.definiciones("field", "campo000")]
chk("lo pedido: dos directas y tres que se preparan", _nom[5:] == ["add_todo", "mark_todo", "prepare_daily_log", "prepare_office_alert", "prepare_absence"], _nom)
_mal = ("clock", "sign", "firm", "submit", "credit", "progress", "prestart", "pre_start", "false_car", "delete", "cancel")
chk("⚠️ fichar, firmar, enviar o acreditar no existen como herramienta", not [n for n in _nom if any(x in n.lower() for x in _mal)], _nom)
_s = leer("core/chat_tools.py")
_ll = {n.func.attr for n in ast.walk(ast.parse(_s)) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
chk("⚠️ y el módulo no llama a nada de eso", not (_ll & {"clock_in", "clock_out", "fichar_proyecto", "cerrar_jornada", "firmar", "submit", "acreditar", "save_field_progress", "borrar", "cancelar"}), _ll)
chk("sigue sin nóminas", "payroll" not in _s)
chk("⚠️ cada una dice si guarda o no", all(("no confirmation" in h["description"]) or ("card to confirm" in h["description"]) for h in CT.definiciones("field", "x")[5:]), [h["name"] for h in CT.definiciones("field", "x")[5:]])

sec("2. Nivel 3: To-do, directo")
ESC.clear()
x, m, c = ej("add_todo", {"project_id": "PRJ-1", "text": "Pick up keys"})
chk("apunta de verdad, con la sesión como autor", not m and x["done"] and ESC == [("TA.crear", ("PRJ-1", "cliente1", "Pick up keys", "campo000"), {})], ESC)
ESC.clear()
x, m, c = ej("add_todo", {"project_id": "PRJ-2", "text": "x"})
chk("⚠️ en una obra ajena no apunta", m and ESC == [], (x, ESC))
ESC.clear()
ej("add_todo", {"project_id": "PRJ-1", "text": "x", "usuario": "otro", "autor": "otro"})
chk("⚠️ el autor no lo dice el modelo", ESC[0][1][3] == "campo000", ESC)
ESC.clear()
x, m, c = ej("mark_todo", {"project_id": "PRJ-1", "task_id": " TSK-3 "})
chk("marca, y hecha por defecto", not m and ESC == [("TA.marcar", ("TSK-3", "PRJ-1", True, "campo000"), {})], ESC)
ESC.clear()
ej("mark_todo", {"project_id": "PRJ-1", "task_id": "TSK-3", "done": False})
chk("también la reabre", ESC[0][1][2] is False, ESC)
ESC.clear()
ej("mark_todo", {"project_id": "PRJ-2", "task_id": "TSK-3"})
chk("⚠️ no marca en una obra ajena", ESC == [], ESC)
_tc = TA.crear
TA.crear = lambda *a: (False, "That task is already on the list.")
x, m, c = ej("add_todo", {"project_id": "PRJ-1", "text": "x"})
TA.crear = _tc
chk("lo que dice el motor vuelve como error", m and "already on the list" in x, x)
ESC.clear()
c = nctx()
_r = [CT.ejecutar("add_todo", {"project_id": "PRJ-1", "text": str(i)}, c) for i in range(CT.MAX_DIRECTAS + 2)]
chk("⚠️ tope por pregunta: un error no vacía ni llena la lista", len(ESC) == CT.MAX_DIRECTAS and _r[-1][1] is True and "stop" in _r[-1][0], (len(ESC), _r[-1]))
chk("el tope es por pregunta: otra empieza de cero", CT.ejecutar("add_todo", {"project_id": "PRJ-1", "text": "z"}, nctx())[1] is False)

sec("3. ⚠️ Nivel 2: preparar NO escribe")
ESC.clear()
x, m, c = ej("prepare_daily_log", {"project_id": "PRJ-1", "text": "Finished the bedplates"})
chk("⚠️ el parte no se guarda", ESC == [] and not m and x["status"] == "NOT DONE YET", (ESC, x))
_a = c["acciones"][0]
chk("deja la tarjeta, con la obra y el día", _a["tipo"] == "parte" and "Bondi Tower" in _a["titulo"] and "03/11/2026" in _a["titulo"] and _a["detalle"] == "Finished the bedplates", _a)
chk("⚠️ al modelo le dice que NO está hecho", "Do not say it is done" in x["next"], x)
x, m, c = ej("prepare_office_alert", {"project_id": "PRJ-1", "message": "Door jammed"})
chk("⚠️ el aviso no se manda", ESC == [] and c["acciones"][0]["tipo"] == "aviso" and c["acciones"][0]["detalle"] == "Door jammed", ESC)
x, m, c = ej("prepare_absence", {"type": "sick_leave", "from": "2026-11-03"})
chk("⚠️ la ausencia no se registra ni avisa", ESC == [] and c["acciones"][0]["tipo"] == "ausencia", ESC)
_d = c["acciones"][0]["datos"]
chk("un día, y con su tipo real", _d["tipo"] == AU.ENFERMEDAD and _d["from"] == _d["to"] == "2026-11-03", _d)
chk("el título, con su nombre visible", c["acciones"][0]["titulo"] == "Sick leave", c["acciones"][0])
for tipo, real in (("annual_leave", AU.VACACIONES), ("day_off", AU.LIBRE)):
    x, m, c = ej("prepare_absence", {"type": tipo, "from": "2026-11-10", "to": "2026-11-11", "reason": "Family"})
    if c["acciones"][0]["datos"]["tipo"] != real or "Family" not in c["acciones"][0]["detalle"]:
        chk("cada tipo con el suyo", False, c["acciones"])
        break
else:
    chk("cada tipo con el suyo, y el motivo en la tarjeta", True)
_aus["exceso"] = 3
x, m, c = ej("prepare_absence", {"type": "sick_leave", "from": "2026-11-03"})
_aus["exceso"] = 0
chk("⚠️ si pasa del saldo, la tarjeta lo dice antes de confirmar", "3 day(s) over your balance" in c["acciones"][0]["detalle"], c["acciones"])
chk("sigue sin escribir nada", ESC == [], ESC)

sec("4. Los errores salen ANTES de la tarjeta")
for q, nom, ent, frag in (("parte vacío", "prepare_daily_log", {"project_id": "PRJ-1", "text": "  "}, "empty"),
                          ("parte larguísimo", "prepare_daily_log", {"project_id": "PRJ-1", "text": "x" * (DL.MAX_TEXTO + 1)}, "too long"),
                          ("⚠️ parte del futuro", "prepare_daily_log", {"project_id": "PRJ-1", "text": "x", "date": "2026-11-04"}, "today or an earlier"),
                          ("fecha ilegible", "prepare_daily_log", {"project_id": "PRJ-1", "text": "x", "date": "ayer"}, "YYYY-MM-DD"),
                          ("⚠️ parte en obra ajena", "prepare_daily_log", {"project_id": "PRJ-2", "text": "x"}, "not one of"),
                          ("aviso vacío", "prepare_office_alert", {"project_id": "PRJ-1", "message": ""}, "empty"),
                          ("aviso larguísimo", "prepare_office_alert", {"project_id": "PRJ-1", "message": "x" * (CT.MAX_AVISO + 1)}, "too long"),
                          ("⚠️ aviso de obra ajena", "prepare_office_alert", {"project_id": "PRJ-2", "message": "x"}, "not one of"),
                          ("tipo inventado", "prepare_absence", {"type": "holiday", "from": "2026-11-10"}, "annual_leave"),
                          ("fechas ilegibles", "prepare_absence", {"type": "day_off", "from": "mañana"}, "YYYY-MM-DD")):
    x, m, c = ej(nom, ent)
    chk(q, m and frag in x and c["acciones"] == [], (x, c["acciones"]))
_aus["problema"] = "You are asking for 5 and you have 2 available."
x, m, c = ej("prepare_absence", {"type": "annual_leave", "from": "2026-11-10"})
_aus["problema"] = ""
chk("⚠️ las reglas de ausencias son las de siempre, y sin tarjeta", m and "you have 2 available" in x and c["acciones"] == [], x)
x, m, c = ej("prepare_daily_log", {"project_id": "PRJ-1", "text": "ayer", "date": "2026-11-02"})
chk("un parte de otro día, con ese día", c["acciones"][0]["datos"]["date"] == "2026-11-02" and "02/11/2026" in c["acciones"][0]["titulo"], c["acciones"])
c = nctx()
ej("prepare_office_alert", {"project_id": "PRJ-1", "message": "igual"}, c)
x, m, c = ej("prepare_office_alert", {"project_id": "PRJ-1", "message": "igual"}, c)
chk("⚠️ la misma dos veces es una tarjeta", len(c["acciones"]) == 1 and not m, c["acciones"])
c = nctx()
for i in range(CT.MAX_TARJETAS + 1):
    x, m, c = ej("prepare_office_alert", {"project_id": "PRJ-1", "message": "m%d" % i}, c)
chk("⚠️ tope de tarjetas esperando", len(c["acciones"]) == CT.MAX_TARJETAS and m and "confirm or cancel" in x, (len(c["acciones"]), x))
c = nctx()
c["acciones"] = None
x, m, c = ej("prepare_office_alert", {"project_id": "PRJ-1", "message": "m"}, c)
chk("sin dónde dejar la tarjeta, no finge haberla dejado", m and "Nothing can be prepared" in x, x)

sec("5. Confirmar")
CTX = nctx()


def carta(nombre, ent):
    c = nctx()
    ej(nombre, ent, c)
    return c["acciones"][0]


ESC.clear()
ok, msg = CT.confirmar(carta("prepare_daily_log", {"project_id": "PRJ-1", "text": "Bedplates", "date": "2026-11-02"}), CTX)
chk("⚠️ guarda el parte, con la sesión y su día", ok and ESC == [("DL.crear", ("PRJ-1", "cliente1", "Bedplates", "campo000"), {"dia": "2026-11-02"})], ESC)
chk("⚠️ y recuerda que acreditar lo hace la persona, en Daily log", "Daily log" in msg, msg)
ESC.clear()
ok, msg = CT.confirmar(carta("prepare_office_alert", {"project_id": "PRJ-1", "message": "Door jammed"}), CTX)
chk("⚠️ manda el aviso, con su obra y su nombre", ok and ESC == [("alerta", ("PRJ-1", "cliente1", "Door jammed", "campo000", "Bondi Tower"), {})] and "AL-9" in msg, (ESC, msg))
ESC.clear()
ok, msg = CT.confirmar(carta("prepare_absence", {"type": "sick_leave", "from": "2026-11-03", "to": "2026-11-04", "reason": "flu"}), CTX)
chk("⚠️ la baja: guarda, tablero y oficina, en orden", [e[0] for e in ESC] == ["AU.solicitar", "roster", "avisar_admins"], [e[0] for e in ESC])
chk("con la sesión, las fechas y el motivo", ESC[0][1][:7] == ("cliente1", "campo000", "Field Test", AU.ENFERMEDAD, "2026-11-03", "2026-11-04", "flu"), ESC[0])
chk("dice que está registrada", "recorded (AUS-9)" in msg, msg)
ESC.clear()
ok, msg = CT.confirmar(carta("prepare_absence", {"type": "annual_leave", "from": "2026-11-10"}), CTX)
chk("⚠️ las vacaciones no tocan el tablero hasta aprobarse", [e[0] for e in ESC] == ["AU.solicitar", "avisar_admins"] and "Request sent" in msg, ([e[0] for e in ESC], msg))
_q = carta("prepare_office_alert", {"project_id": "PRJ-1", "message": "x"})
_qp = carta("prepare_daily_log", {"project_id": "PRJ-1", "text": "x"})
_quien["campo000"] = []
ESC.clear()
ok, msg = CT.confirmar(_q, CTX)
ok2, msg2 = CT.confirmar(_qp, CTX)
_quien["campo000"] = [OBRA]
chk("⚠️ si ya no está en la obra, no se manda", not ok and ESC == [] and "not one of" in msg, (ok, msg, ESC))
chk("⚠️ ...ni se guarda el parte", not ok2 and ESC == [] and "not one of" in msg2, (ok2, msg2, ESC))
# ⚠️ Con una AUSENCIA, que no pasa por `_obra`: con un aviso lo paraba la obra y el control no se probaba
_qa = carta("prepare_absence", {"type": "day_off", "from": "2026-11-10"})
ESC.clear()
ok, msg = CT.confirmar(_qa, {**CTX, "usuario": ""})
chk("⚠️ sin identidad, nada", not ok and ESC == [] and "identified" in msg, (msg, ESC))
ok, msg = CT.confirmar(_qa, {**CTX, "grupo": ""})
chk("⚠️ sin grupo, tampoco", not ok and ESC == [], (msg, ESC))
ok, msg = CT.confirmar({"tipo": "borrar_todo", "datos": {}}, CTX)
chk("una tarjeta rara no hace nada", not ok and ESC == [], msg)
_rp = AL.report_problem
AL.report_problem = lambda *a: (_ for _ in ()).throw(RuntimeError("secreto 503"))
ok, msg = CT.confirmar(_q, CTX)
AL.report_problem = _rp
chk("⚠️ un fallo se dice, sin el error interno", not ok and "secreto" not in msg and "Try again" in msg, msg)
_sl = AU.solicitar
AU.solicitar = lambda *a, **k: (False, "There is already an absence overlapping those dates")
ESC.clear()
ok, msg = CT.confirmar(carta("prepare_absence", {"type": "day_off", "from": "2026-11-10"}), CTX)
AU.solicitar = _sl
chk("⚠️ si el motor lo rechaza al confirmar, ni tablero ni aviso", not ok and "overlapping" in msg and ESC == [], (msg, ESC))

sec("6. `registrar`: una sola definición")
_u = leer("core/ausencias_ui.py")
_p = funcion(_u, "_pedir")
chk("⚠️ la pantalla usa `registrar`", "registrar(grupo, usuario, nombre, tipo, desde, hasta, motivo, findes)" in _p, _p[-500:])
chk("⚠️ y ya no repite los pasos", "AU.solicitar" not in _p and "_avisar_admins" not in _p and "aplicar_al_roster" not in _p)
_rr = AU.aplicar_al_roster
AU.aplicar_al_roster = lambda a: (False, "sin tablero")
ESC.clear()
ok, r, aviso = AUI.registrar("g", "u", "n", AU.ENFERMEDAD, "2026-11-03", "2026-11-03")
AU.aplicar_al_roster = _rr
chk("⚠️ sin tablero: registrada, avisa a la oficina, y lo dice", ok and "planner could not be updated" in aviso and [e[0] for e in ESC] == ["AU.solicitar", "avisar_admins"], (aviso, ESC))
_a0 = leer("core/ausencias.py")
_ps = funcion(_a0, "problema_solicitud")
chk("⚠️ validar no escribe", "_ws()" not in _ps and "append_row" not in _ps, _ps[:100])
chk("⚠️ `solicitar` valida con la misma", "_err = problema_solicitud(grupo, usuario, tipo, desde, hasta, incluir_findes)" in funcion(_a0, "solicitar"))
chk("sin copias de la regla", _a0.count("You are asking for {n}") == 1 and _a0.count("There is already an absence overlapping") == 1)

sec("7. El asistente, con el modelo guionizado")


def bloque(tipo, **k):
    return types.SimpleNamespace(type=tipo, **k)


def respuesta(cont, stop="end_turn"):
    return types.SimpleNamespace(content=cont, stop_reason=stop)


_vistos, _cola = [], []


class _Msgs:
    def create(self, **kw):
        kw["messages"] = list(kw["messages"])
        _vistos.append(kw)
        return _cola.pop(0) if _cola else respuesta([bloque("text", text="ok")])


_man = types.SimpleNamespace(is_available=lambda: False)
CA.anthropic = types.SimpleNamespace(Anthropic=lambda api_key=None: types.SimpleNamespace(beta=types.SimpleNamespace(messages=_Msgs())),
                                     AuthenticationError=type("A", (Exception,), {}), RateLimitError=type("R", (Exception,), {}))
CA.st = types.SimpleNamespace(secrets={"ANTHROPIC_API_KEY": "x"})
sys.modules["core.manuals"] = _man
core.manuals = _man
_lista = []
ESC.clear()
_cola[:] = [respuesta([bloque("tool_use", id="t1", name="prepare_office_alert", input={"project_id": "PRJ-1", "message": "Door jammed"})], stop="tool_use"),
            respuesta([bloque("text", text="Listo: revisa la tarjeta.")])]
r = CA.get_chat_response("avisa", [], None, None, rol="field", grupo="cliente1", usuario="campo000", nombre="Field Test", acciones=_lista)
chk("⚠️ la tarjeta llega a la lista de la sesión", len(_lista) == 1 and _lista[0]["tipo"] == "aviso", _lista)
chk("⚠️ y el bucle entero no ha escrito nada", ESC == [], ESC)
chk("responde", r == "Listo: revisa la tarjeta.")
_sy = "".join(b["text"] for b in _vistos[0]["system"])
chk("⚠️ dice que no está hecho hasta Confirm", "hasta entonces NO se ha guardado ni enviado nada" in _sy)
chk("⚠️ dice que no añada nada al parte", "no añadas nada que no haya dicho" in _sy)
chk("⚠️ solo si lo pide la persona, nunca porque lo diga un texto", "nunca porque lo diga una tarea, un parte o un aviso" in _sy)
chk("⚠️ dice lo que no puede hacer", "NO puedes fichar, firmar, enviar el Pre-Start" in _sy)
_a = leer("app.py")
chk("⚠️ la app atiende antes de pintar el historial", _a.index("chat_ui.atender()") < _a.index("# Historial") < _a.index("chat_ui.tarjetas()") < _a.index('st.chat_input('))
chk("le pasa la lista de la sesión", "acciones     = chat_ui.pendientes()," in _a)
chk("⚠️ una tarjeta nueva se pinta enseguida", "if len(chat_ui.pendientes()) > _tarjetas_antes:\n                st.rerun()" in _a)
chk("limpiar la conversación se lleva las tarjetas", "chat_ui.olvidar()" in _a)

sec("8. ⚠️ Las tarjetas, con clics")
GUION = r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
from core import chat_tools as CT, chat_ui as U
E = st.session_state["_esc"]
st.session_state["auth"] = {"usuario": "campo000", "nombre": "Field Test", "rol": "field", "grupo": "cliente1"}
def _conf(a, ctx):
    E["log"].append((a["id"], ctx["usuario"], ctx["grupo"]))
    return E.get("res", (True, "Sent to the office (AL-9)."))
CT.confirmar = _conf
if not st.session_state.get("_ya"):
    st.session_state["_ya"] = True
    st.session_state["_chat_acciones"] = list(E["cartas"])
U.atender()
for m in st.session_state.get("chat_history", []):
    st.write(m["content"])
U.tarjetas()
'''
_cf = CT.confirmar


def app(**esc):
    at = AppTest.from_string(GUION, default_timeout=60)
    at.session_state["_esc"] = {"log": [], "cartas": [{"id": "a1", "tipo": "aviso", "titulo": "Alert to the office · Obra *1*", "detalle": "Door *jammed*\n$5 line", "datos": {}}], **esc}
    at.run()
    chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
    return at


def btn(at, k):
    return next((b for b in at.button if b.key == k), None)


at = app()
chk("la tarjeta, con sus dos botones", btn(at, "chat_ok_a1") is not None and btn(at, "chat_no_a1") is not None)
chk("⚠️ dice lo que va a pasar y que no ha pasado", any("Door" in m.value for m in at.markdown) and any("Nothing happens until you confirm" in c.value for c in at.caption))
chk("⚠️ el texto ajeno, literal", any("\\*jammed\\*" in m.value and "\\$5" in m.value for m in at.markdown), [m.value for m in at.markdown])
chk("todavía nada", at.session_state["_esc"]["log"] == [])
btn(at, "chat_ok_a1").click().run()
chk("⚠️ Confirm ejecuta una vez, con la sesión", at.session_state["_esc"]["log"] == [("a1", "campo000", "cliente1")], at.session_state["_esc"]["log"])
chk("⚠️ la tarjeta se va", btn(at, "chat_ok_a1") is None and at.session_state["_chat_acciones"] == [])
chk("y queda en la conversación", at.session_state["chat_history"][-1]["content"].startswith("✅ Sent to the office"), at.session_state["chat_history"])
at.session_state["_chat_pet"] = {"id": "a1", "si": True}
at.run()
chk("⚠️ un doble toque no manda dos veces", len(at.session_state["_esc"]["log"]) == 1 and "_chat_pet" not in at.session_state, at.session_state["_esc"]["log"])
at = app()
btn(at, "chat_no_a1").click().run()
chk("⚠️ Cancel no hace nada", at.session_state["_esc"]["log"] == [] and at.session_state["_chat_acciones"] == [])
chk("y lo dice", "Nothing was sent" in at.session_state["chat_history"][-1]["content"], at.session_state["chat_history"])
at = app(res=(False, "The sheet is busy."))
btn(at, "chat_ok_a1").click().run()
chk("⚠️ si falla, la tarjeta sigue para reintentar", btn(at, "chat_ok_a1") is not None and at.session_state["chat_history"][-1]["content"] == "⚠️ The sheet is busy.", at.session_state["chat_history"])
at.session_state["_esc"]["res"] = (True, "Sent.")
btn(at, "chat_ok_a1").click().run()
chk("...y reintentar funciona", len(at.session_state["_esc"]["log"]) == 2 and btn(at, "chat_ok_a1") is None)
at = app(cartas=[{"id": "b1", "tipo": "aviso", "titulo": "x", "detalle": "y", "datos": {}}, {"id": "b2", "tipo": "aviso", "titulo": "z", "detalle": "w", "datos": {}}])
btn(at, "chat_no_b1").click().run()
chk("con dos, cada botón toca la suya", btn(at, "chat_ok_b1") is None and btn(at, "chat_ok_b2") is not None)
CT.confirmar = _cf

print("\n=== verif_v640: %d OK, %d FALLOS ===" % (n_ok, len(fallos)))
for f in fallos:
    print("   -", f)
sys.exit(1 if fallos else 0)
