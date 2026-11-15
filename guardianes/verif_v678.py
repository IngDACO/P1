# -*- coding: utf-8 -*-
"""v678 · Planificar más rápido, y los asistentes (ciclo 3, mejoras 3/3).

H6  Assign con VARIOS días (y «Whole week»): una escritura por persona, sin pisar ausencias, libre = libre todos esos
    días; y el aviso dice a quién y cuándo.
H13 «My route» del campo: las obras de su tablero del día que elija, no todas las asignadas.
H14 el Field assistant ve su plan de otro día (`get_my_plan`), solo lo suyo y solo lectura.
H16 la tarjeta para decidir una ausencia dice quién puede cubrirla, con sus certificados.
H10 el Management assistant prepara mover o quitar días del tablero de una persona (`prepare_board_change`): tarjeta
    con cada día, Confirm, desde hoy y sin tocar ausencias (`roster.cambiar_dias`, una regla).

Nada sale a la red ni escribe: funciones reales con sustitutos; AppTest de las pantallas.
"""
import ast
import io
import json
import os
import sys
from datetime import date

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:900]))
    if not cond:
        FALLOS.append(nombre)


def src(rel):
    return io.open(os.path.join(RAIZ, rel), encoding="utf-8").read()


def funcion(rel, nombre):
    s = src(rel)
    for n in ast.walk(ast.parse(s)):
        if isinstance(n, ast.FunctionDef) and n.name == nombre:
            return n, ast.get_source_segment(s, n) or ""
    return None, ""


def _sustituir(obj, **kw):
    viejo = {k: getattr(obj, k) for k in kw}
    for k, v in kw.items():
        setattr(obj, k, v)
    return lambda: [setattr(obj, k, v) for k, v in viejo.items()]


from streamlit.testing.v1 import AppTest                                   # noqa: E402
from core import roster as R                                               # noqa: E402
from core import projects as P                                             # noqa: E402
from core import auth                                                      # noqa: E402
from core import chat_tools as CT                                          # noqa: E402
from core import credentials as CR                                         # noqa: E402
from core import ausencias as AU                                           # noqa: E402
from core import clock as CK                                               # noqa: E402

_ORIG = dict(gs=R.get_semana, gp=R.guardar_persona, ti=R.trabajos_idx, lp=P.list_projects, lu=auth.list_users)


def _c(*asigs, nota=""):
    return {"items": [{"a": a, "i": "07:00", "f": "15:30"} for a in asigs], "nota": nota}


L16, L23 = date(2026, 11, 16), date(2026, 11, 23)
SEMS = {L16: {"ana": {"lun": _c("PRJ-1"), "mar": _c("PRJ-1", "PRJ-2"), "mie": _c("LEAVE", nota="Annual leave · AUS-1"),
                      "jue": _c("PRJ-2"), "vie": _c("PRJ-1")}},
        L23: {"ana": {"lun": _c("PRJ-1")}}}
TIDX = {p: {"ID": p, "Name": n, "ProjectID": p} for p, n in (("PRJ-1", "Torre"), ("PRJ-2", "Muelle"), ("PRJ-3", "Faro"))}
ESC = []


def _ponte():
    ESC.clear()
    return [_sustituir(R, get_semana=lambda g, l: json.loads(json.dumps(SEMS.get(l, {}))), trabajos_idx=lambda g: dict(TIDX),
                       guardar_persona=lambda g, l, u, dias: (ESC.append((l, u, json.loads(json.dumps(dias)))), (True, "ok"))[1])]


def _items(cel):
    return [i["asig"] for i in R._norm_cell(cel)["items"]]


# ═════════════════════════════════════════════════════════════════════════════
print("1. H10 · `roster.cambiar_dias`: la regla")
_d = _ponte()
try:
    _q = R.cambiar_dias("G", "ana", "2026-11-16", "2026-11-20", "PRJ-1", hoy=L16)
    _esc_sin = list(ESC)
    _m = R.cambiar_dias("G", "ana", "2026-11-16", "2026-11-17", "PRJ-1", "PRJ-3", hoy=L16)
    _m2 = R.cambiar_dias("G", "ana", "2026-11-17", "2026-11-17", "PRJ-2", "PRJ-1", hoy=L16)
    _past = R.cambiar_dias("G", "ana", "2026-11-13", "2026-11-17", "PRJ-1", hoy=L16)
    _largo = R.cambiar_dias("G", "ana", "2026-11-16", "2026-12-31", "PRJ-1", hoy=L16)
    _igual = R.cambiar_dias("G", "ana", "2026-11-16", "2026-11-16", "PRJ-1", "PRJ-1", hoy=L16)
    _todo = R.cambiar_dias("G", "ana", "2026-11-16", "2026-11-17", "", hoy=L16)
    ESC.clear()
    _ap = R.cambiar_dias("G", "ana", "2026-11-19", "2026-11-23", "PRJ-1", aplicar=True, hoy=L16)
    _esc_ap = list(ESC)
finally:
    for x in _d:
        x()
_dq = {str(x["fecha"]): (_items_a, _items_d) for x in (_q[1] if _q[0] else [])
       for _items_a, _items_d in [([i["asig"] for i in x["antes"]], [i["asig"] for i in x["despues"]])]}
chk("quitar PRJ-1 del 16 al 20: lun, mar y vie cambian; el miércoles (ausencia) y el jueves (otra obra) no",
    _q[0] and _dq == {"2026-11-16": (["PRJ-1"], []), "2026-11-17": (["PRJ-1", "PRJ-2"], ["PRJ-2"]),
                      "2026-11-20": (["PRJ-1"], [])}, _q)
chk("…y sin `aplicar` NO escribe nada (es la vista de la tarjeta)", _esc_sin == [], _esc_sin)
_dm = {str(x["fecha"]): [(i["asig"], i["ini"], i["fin"]) for i in x["despues"]] for x in (_m[1] if _m[0] else [])}
chk("moverlos a PRJ-3: la misma franja en la obra nueva, sin tocar la otra obra del martes",
    _dm == {"2026-11-16": [("PRJ-3", "07:00", "15:30")], "2026-11-17": [("PRJ-2", "07:00", "15:30"), ("PRJ-3", "07:00", "15:30")]}, _dm)
chk("moverlos a una obra que ya tiene ese día: no se duplica", _m2[0] and [i["asig"] for i in _m2[1][0]["despues"]] == ["PRJ-1"], _m2)
chk("lo pasado no se toca: desde HOY", _past[0] is False and "from today on" in _past[1], _past)
chk("más de 31 días de una vez, no", _largo[0] is False and "31" in _largo[1], _largo)
chk("la misma obra de origen y destino, no", _igual[0] is False, _igual)
chk("sin obra: todo lo de esos días (y la ausencia, nunca)", _todo[0] and [[i["asig"] for i in x["despues"]] for x in _todo[1]] == [[], []], _todo)
_semanas = {str(l): d for l, u, d in _esc_ap}
chk("con `aplicar`: una escritura por semana (dos semanas → dos), con lo cambiado",
    _ap[0] and sorted(_semanas) == ["2026-11-16", "2026-11-23"] and _items(_semanas["2026-11-16"].get("vie")) == []
    and _items(_semanas["2026-11-23"].get("lun")) == [], _esc_ap)
chk("…y la ausencia del miércoles sigue intacta en lo escrito",
    _items(_semanas.get("2026-11-16", {}).get("mie")) == ["LEAVE"]
    and R._norm_cell(_semanas.get("2026-11-16", {}).get("mie"))["nota"] == "Annual leave · AUS-1", _semanas.get("2026-11-16"))

print("2. H10 · el asistente de gestión: preparar y confirmar")
USERS = [{"User": "ana", "Name": "Ana", "Role": "field", "Group": "G"},
         {"User": "bobo", "Name": "Bobo", "Role": "administrator", "Group": "G"}]
PRJS = [{"ID": "PRJ-1", "Name": "Torre", "Group": "G", "Status": "In progress", "Progress": "40", "FieldAssigned": "ana"},
        {"ID": "PRJ-3", "Name": "Faro", "Group": "G", "Status": "Planned", "Progress": "0", "RequiredCerts": "White Card",
         "FieldAssigned": ""},
        {"ID": "PRJ-9", "Name": "Vieja", "Group": "G", "Status": "Completed", "Progress": "100"}]
CTX = {"grupo": "G", "usuario": "bobo", "nombre": "Bobo", "rol": "administrator", "acciones": []}
_ADD = []
_d = _ponte() + [_sustituir(auth, list_users=lambda *a, **k: [dict(u) for u in USERS]),
                 _sustituir(P, list_projects=lambda *a, **k: [dict(p) for p in PRJS],
                            add_field_user=lambda pid, u: (_ADD.append((pid, u)), (True, 1))[1]),
                 _sustituir(CK, today=lambda *a, **k: L16),
                 _sustituir(CR, compliance=lambda u, req: {"cumple": False, "por_tipo": {}})]
try:
    _r1, _e1 = CT.ejecutar("prepare_board_change", {"person": "Ana", "from": "2026-11-16", "to": "2026-11-20",
                                                    "project_id": "PRJ-1"}, CTX)
    _card1 = dict(CTX["acciones"][-1]) if CTX["acciones"] else {}
    _r2, _e2 = CT.ejecutar("prepare_board_change", {"person": "Ana", "from": "2026-11-16", "project_id": "PRJ-1",
                                                    "move_to_project_id": "PRJ-3"}, CTX)
    _card2 = dict(CTX["acciones"][-1]) if len(CTX["acciones"]) > 1 else {}
    _r3, _e3 = CT.ejecutar("prepare_board_change", {"person": "Ana", "from": "2026-11-16", "move_to_project_id": "PRJ-9"},
                           dict(CTX, acciones=[]))
    _r4, _e4 = CT.ejecutar("prepare_board_change", {"person": "Ana", "from": "2026-11-18", "to": "2026-11-18"},
                           dict(CTX, acciones=[]))
    _r5, _e5 = CT.ejecutar("prepare_board_change", {"person": "Ana", "from": "2026-11-16"},
                           dict(CTX, rol="field", acciones=[]))
    ESC.clear()
    _ok_c, _msg_c = CT.confirmar(_card2, CTX)
    _esc_c = list(ESC)
    _ok_f, _msg_f = CT.confirmar(_card1, dict(CTX, rol="field"))
finally:
    for x in _d:
        x()
chk("prepara la tarjeta y dice que NO está hecho", not _e1 and "NOT DONE YET" in _r1, _r1)
chk("la tarjeta: «Board · free Ana · Torre», cada día que cambia y lo de la ausencia",
    _card1.get("tipo") == "tablero" and _card1.get("titulo") == "Board · free Ana · Torre"
    and "Mon 16/11/2026: Torre 07:00–15:30 → free" in _card1.get("detalle", "")
    and "Tue 17/11/2026: Torre 07:00–15:30, Muelle 07:00–15:30 → Muelle 07:00–15:30" in _card1.get("detalle", "")
    and "Wed" not in _card1.get("detalle", ""), _card1)
chk("moverlos a Faro avisa de los certificados que no tiene (y el modelo lo sabe)",
    "Board · Ana → Faro" == _card2.get("titulo") and "does not hold the certificates Faro requires: White Card"
    in _card2.get("detalle", "") and "warnings_on_the_card" in _r2, (_card2, _r2))
chk("a una obra terminada, no", _e3 and "is not running" in _r3, _r3)
chk("sin nada que cambiar (el miércoles es una ausencia), lo dice y no prepara nada", _e4 and "nothing to change" in _r4, _r4)
chk("el campo no tiene esta herramienta", _e5 and "Unknown tool" in _r5, _r5)
_sem_c = {str(l): d for l, u, d in _esc_c}
chk("Confirm: escribe lo de la tarjeta (el lunes 16 pasa a Faro) y la asigna a Faro",
    _ok_c and _items(_sem_c.get("2026-11-16", {}).get("lun")) == ["PRJ-3"] and ("PRJ-3", "ana") in _ADD, (_ok_c, _msg_c, _esc_c))
chk("…y lo dice: «Ana: 1 day(s) moved to Faro.»", _msg_c == "Ana: 1 day(s) moved to Faro.", _msg_c)
chk("una tarjeta de la oficina no la confirma el campo", _ok_f is False, _msg_f)
_def_of = [h["name"] for h in CT.definiciones("administrator", "bobo")]
_def_ca = [h["name"] for h in CT.definiciones("field", "ana")]
chk("la oficina tiene `prepare_board_change`; el campo, `get_my_plan` (y no al revés)",
    "prepare_board_change" in _def_of and "get_my_plan" in _def_ca and "prepare_board_change" not in _def_ca
    and "get_my_plan" not in _def_of, (_def_of, _def_ca))
_pa = src("core/chat_agent.py")
chk("el asistente de gestión sabe que lo puede preparar, y el de campo que ve su plan de otros días",
    "mover o quitar días del tablero de alguien" in _pa and "su plan de otros días" in _pa)

print("3. H14 · el plan del campo de otro día (`get_my_plan`)")
_PEDIDOS = []
_ASIG = {date(2026, 11, 16): [{"etiqueta": "Torre", "proyecto_id": "PRJ-1", "ini": "07:00", "fin": "15:30", "nota": "",
                               "es_estado": False}],
         date(2026, 11, 18): [{"etiqueta": "Leave", "proyecto_id": "", "ini": "", "fin": "", "nota": "Annual leave · AUS-1",
                               "es_estado": True}]}
_d = [_sustituir(R, asignaciones_dia=lambda g, u, f=None: (_PEDIDOS.append((g, u, f)), list(_ASIG.get(f, [])))[1]),
      _sustituir(CK, today=lambda *a, **k: date(2026, 11, 15))]
_CF = {"grupo": "G", "usuario": "ana", "nombre": "Ana", "rol": "field", "acciones": []}
try:
    _p1, _pe1 = CT.ejecutar("get_my_plan", {"date": "2026-11-16"}, _CF)
    _p2, _pe2 = CT.ejecutar("get_my_plan", {"date": "2026-11-16", "to": "2026-12-31"}, _CF)
finally:
    for x in _d:
        x()
_j1 = json.loads(_p1) if not _pe1 else {}
_j2 = json.loads(_p2) if not _pe2 else {}
chk("el lunes: Torre de 07:00 a 15:30", (_j1.get("days") or [{}])[0].get("planned", [{}])[0].get("what") == "Torre"
    and _j1["days"][0]["weekday"] == "Monday" and _j1["days"][0]["date"] == "16/11/2026", _p1)
chk("solo lo suyo: pregunta por la persona de la SESIÓN", _PEDIDOS and all(u == "ana" and g == "G" for g, u, f in _PEDIDOS), _PEDIDOS)
chk("una semana como mucho (7 días), con la ausencia dicha como tal",
    len(_j2.get("days", [])) == 7 and _j2["days"][2]["planned"][0]["absence_or_day_off"] is True, _p2[:400])

print("4. H16 · quién puede cubrir una ausencia, con sus certificados")
_SUB = {"2026-11-25": [{"nombre": "Beto", "cumple": True}, {"nombre": "Carl", "cumple": False}],
        "2026-11-26": [{"nombre": "Carl", "cumple": False}], "2026-11-27": []}
_d = [_sustituir(AU, sustitutos=lambda g, f, pid=None, excluir=None: list(_SUB.get(str(f), [])))]
try:
    _qc = CT._quien_cubre("G", "ana", [{"fecha": date(2026, 11, 25), "etiqueta": "Torre", "proyecto_id": "PRJ-1"},
                                       {"fecha": date(2026, 11, 26), "etiqueta": "Torre", "proyecto_id": "PRJ-1"},
                                       {"fecha": date(2026, 11, 27), "etiqueta": "Faro", "proyecto_id": "PRJ-3"}])
finally:
    for x in _d:
        x()
chk("las tres respuestas de la bandeja: con certificados, sin ellos, o nadie",
    _qc == ["Who could cover 25/11/2026 · Torre: free and holding the certificates: Beto",
            "Who could cover 26/11/2026 · Torre: free but WITHOUT the certificates the site requires: Carl",
            "Who could cover 27/11/2026 · Faro: nobody free that day"], _qc)
def _revienta(*a, **k):
    raise RuntimeError("la hoja no contesta")


_d = [_sustituir(AU, sustitutos=_revienta)]
try:
    try:
        _qe = CT._quien_cubre("G", "ana", [{"fecha": date(2026, 11, 25), "etiqueta": "Torre", "proyecto_id": "PRJ-1"}])
    except Exception as e:
        _qe = e
finally:
    for x in _d:
        x()
chk("si no se puede leer quién está libre, la tarjeta sale igual (sin esas líneas)", _qe == [], _qe)
_n, _pd = funcion("core/chat_tools.py", "_preparar_decision_ausencia")
chk("y van en la tarjeta de aprobar (si deja días libres en el tablero)", "lineas += _quien_cubre(g, usuario, _chq)" in _pd)

# ═════════════════════════════════════════════════════════════════════════════
print("5. H6 · Assign con varios días (AppTest)")
ASIG = r'''
import json, datetime as dt
import streamlit as st
from core import roster as R, roster_ui as RU, projects as P, credentials as C, flash, clock
clock.today = lambda *a, **k: dt.date(2026, 11, 17)
L = dt.date(2026, 11, 16)
def _c(*a):
    return {"items": [{"a": x, "i": "07:00", "f": "15:30"} for x in a], "nota": ""}
SEM = {"ana": {}, "beto": {"mar": _c("PRJ-2")}, "carl": {"jue": {"items": [{"a": "LEAVE", "i": "", "f": ""}], "nota": "Sick leave · AUS-2"}}}
R.get_semana = lambda g, l: json.loads(json.dumps(SEM))
st.session_state.setdefault("_GP", [])
R.guardar_persona = lambda g, l, u, d: (st.session_state["_GP"].append((u, json.loads(json.dumps(d)))), (True, "ok"))[1]
P.list_projects = lambda *a, **k: [{"ID": "PRJ-1", "Name": "Torre", "Status": "In progress"}]
P.get_project = lambda pid: {"ID": pid, "Name": "Torre", "RequiredCerts": ""}
P.add_field_user = lambda pid, u: (True, 1)
st.session_state.setdefault("_FL", [])
flash.exito = lambda m: st.session_state["_FL"].append(m)
STAFF = [{"User": u, "Name": n} for u, n in (("ana", "Ana"), ("beto", "Beto"), ("carl", "Carl"))]
RU._etq = lambda staff=None, grupo="": {"ana": "Ana", "beto": "Beto", "carl": "Carl"}
RU._asignacion_inteligente("G", L, STAFF, {}, dias=R.DIAS)
'''
at = AppTest.from_string(ASIG, default_timeout=120)
at.run()
at.selectbox(key="ai_prj").select("PRJ-1").run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_ms = [m for m in at.multiselect if m.key == "ai_dias"]
chk("«Days» con varios, y por defecto HOY (martes 17/11)", bool(_ms) and list(_ms[0].value) == ["mar"],
    [list(m.value) for m in _ms])
at.checkbox(key="ai_semana").check().run()
_cap = " ¦ ".join(c.value for c in at.caption)
_ops = list(at.multiselect(key="ai_pick").options) if any(m.key == "ai_pick" for m in at.multiselect) else []
chk("«Whole week»: libre = libre TODOS los días (Beto choca el martes y Carl está de baja el jueves: salen con su día)",
    any("Ana" in o for o in _ops) and not any("Beto" in o or "Carl" in o for o in _ops)
    and "Beto (Tue)" in _cap and "Carl (Thu)" in _cap, (_ops, _cap))
at.multiselect(key="ai_pick").select(next(o for o in _ops if "Ana" in o)).run()
at.button(key="ai_go").click().run()
_gp = {u: d for u, d in at.session_state["_GP"]}
chk("una escritura por persona con los cinco días (Ana)", list(_gp) == ["ana"] and set(_gp.get("ana", {})) == set(R.DIAS)
    and all(_items(_gp["ana"][d]) == ["PRJ-1"] for d in R.DIAS), _gp)
_fl = list(at.session_state["_FL"])
chk("el aviso dice a quién y cuándo", _fl == ["Ana → «Torre» on Mon 16/11, Tue 17/11, Wed 18/11, Thu 19/11, Fri 20/11, "
                                             "07:00–15:30."], _fl)
from core import roster_ui as RU                                           # noqa: E402
_GPD = []
_d = [_sustituir(R, guardar_persona=lambda g, l, u, d: (_GPD.append(json.loads(json.dumps(d))), (True, "ok"))[1])]
try:
    RU._asignar_dias("G", L16, "carl", {"jue": _c("LEAVE", nota="Sick leave · AUS-2"), "mar": _c("PRJ-2")}, R.DIAS,
                     "PRJ-1", "07:00", "15:30")
finally:
    for x in _d:
        x()
_gc = _GPD[0] if _GPD else {}
chk("`_asignar_dias`: una escritura, sin pisar la ausencia del jueves ni la otra obra del martes",
    len(_GPD) == 1 and _items(_gc.get("jue")) == ["LEAVE"] and _items(_gc.get("mar")) == ["PRJ-2", "PRJ-1"]
    and _items(_gc.get("lun")) == ["PRJ-1"], _GPD)

print("6. H13 · «My route» del campo: las obras de su tablero de ese día (AppTest)")
RUTA = r'''
import datetime as dt
import streamlit as st
from core import route_ui as RT, roster as R, projects as P, clock
clock.today = lambda *a, **k: dt.date(2026, 11, 16)
PR = {"PRJ-1": {"ID": "PRJ-1", "Name": "Torre", "Group": "G", "Status": "In progress", "Location": "1 George St"},
      "PRJ-2": {"ID": "PRJ-2", "Name": "Muelle", "Group": "G", "Status": "In progress", "Location": "2 Pitt St"},
      "PRJ-X": {"ID": "PRJ-X", "Name": "Ajena", "Group": "OTRO", "Status": "In progress"}}
ASG = {dt.date(2026, 11, 16): [{"proyecto_id": "PRJ-1", "es_estado": False}, {"proyecto_id": "PRJ-X", "es_estado": False},
                               {"proyecto_id": "", "es_estado": True}]}
R.asignaciones_dia = lambda g, u, f=None: list(ASG.get(f, []))
P.get_project = lambda pid: dict(PR.get(pid, {}))
P.list_projects_for_field = lambda u, grupo=None, **k: [dict(PR["PRJ-1"]), dict(PR["PRJ-2"])]
RT._coords_de = lambda p: (-33.86, 151.2) if p.get("ID") == "PRJ-1" else (-33.87, 151.21)
RT._folium_map = lambda *a, **k: True
RT.render_mi_ruta("ana", "G")
'''
at = AppTest.from_string(RUTA, default_timeout=60)
at.run()
_md = " ¦ ".join(m.value for m in at.markdown)
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("hoy: solo la obra de su tablero (Torre), ni la otra asignada ni la de otra empresa",
    "**Torre**" in _md and "Muelle" not in _md and "Ajena" not in _md, _md[:500])
at.date_input(key="miruta_dia").set_value(date(2026, 11, 17)).run()
chk("un día sin nada: «Nothing is planned for you on Tue 17/11/2026»",
    "Nothing is planned for you on Tue 17/11/2026" in " ".join(i.value for i in at.info), [i.value for i in at.info])
at.toggle(key="miruta_todas").set_value(True).run()
_md = " ¦ ".join(m.value for m in at.markdown)
chk("«All my active sites»: las de siempre", "**Torre**" in _md and "**Muelle**" in _md, _md[:500])

# devolver lo real (trampa 48)
R.get_semana, R.guardar_persona, R.trabajos_idx = _ORIG["gs"], _ORIG["gp"], _ORIG["ti"]
P.list_projects, auth.list_users = _ORIG["lp"], _ORIG["lu"]

print()
print(f"=== {('TODO OK' if not FALLOS else str(len(FALLOS)) + ' FALLO(S)')} ===")
if FALLOS:
    print("FALLOS:", FALLOS)
sys.exit(1 if FALLOS else 0)
