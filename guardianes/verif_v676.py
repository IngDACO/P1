# -*- coding: utf-8 -*-
"""v676 · El tablero y las obras cerradas (ciclo 3, mejoras 1/3).

H4  una obra cerrada (terminada, cancelada o archivada) ya no se queda en el tablero sin que nadie lo vea: el Radar la
    señala con el botón para liberarla desde mañana, no «bloquea» certificados, «Copy previous week» no la copia (y lo
    dice), y la lista de cierre de una obra terminada cuenta sus días en el tablero y ofrece liberarlos.
H3  en sábado o domingo el Panel (y el plan del campo, y la ruta del día) abre en la semana SIGUIENTE, y «Free on Monday».
H11 Compliance de un día que aún no ha llegado: lo planificado, sin avisos.
H5  una obra que aún no ha empezado: «The job starts on …», sin «day -1».
H15 una ausencia sin fines de semana no los marca en el tablero, y una celda de ausencia no abre sus columnas.

Nada sale a la red ni escribe: funciones reales con sustitutos y hojas de mentira; AppTest de las pantallas.
"""
import ast
import io
import json
import os
import sys
from datetime import date, timedelta

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
from core import ausencias as AU                                           # noqa: E402

# los originales (trampa 48: los guiones de AppTest dejan sus sustitutos puestos en ESTE proceso)
_LIST_PROJECTS, _GET_SEMANA, _GUARDAR, _TIDX = P.list_projects, R.get_semana, R.guardar_persona, R.trabajos_idx


def _c(*asigs, nota=""):
    return {"items": [{"a": a, "i": "07:00", "f": "15:30"} for a in asigs], "nota": nota}


# ═════════════════════════════════════════════════════════════════════════════
print("1. La semana que toca planificar (H3)")
chk("semana_de_trabajo: el domingo 15/11 → la del lunes 16/11; el sábado 21/11 → la del 23/11",
    R.semana_de_trabajo(date(2026, 11, 15)) == date(2026, 11, 16) and R.semana_de_trabajo(date(2026, 11, 21)) == date(2026, 11, 23))
chk("…y un día laborable, su propia semana (miércoles 18/11 → 16/11; lunes 16/11 → 16/11)",
    R.semana_de_trabajo(date(2026, 11, 18)) == date(2026, 11, 16) and R.semana_de_trabajo(date(2026, 11, 16)) == date(2026, 11, 16))
_n, _sa = funcion("core/roster_ui.py", "_semana_activa")
chk("el Panel y el plan del campo abren en esa semana (`_semana_activa`)", "R.semana_de_trabajo()" in _sa)

print("2. Obras cerradas (H4)")
_PRJ = [{"ID": "PRJ-1", "Status": "In progress", "Progress": "40"}, {"ID": "PRJ-C", "Status": "Completed", "Progress": "100"},
        {"ID": "PRJ-X", "Status": "Cancelled", "Progress": "10"}, {"ID": "PRJ-A", "Status": "Archived", "Progress": "60"},
        {"ID": "PRJ-F", "Status": "In progress", "Progress": "100"}, {"ID": "PRJ-H", "Status": "On hold", "Progress": "20"}]
_d = _sustituir(P, list_projects=lambda *a, **k: [dict(x) for x in _PRJ])
try:
    _ce = P.ids_cerradas("G")
finally:
    _d()
chk("ids_cerradas: terminadas (también al 100 %), canceladas y archivadas; no las en marcha ni en pausa",
    _ce == {"PRJ-C", "PRJ-X", "PRJ-A", "PRJ-F"}, _ce)
_SEM = {"ana": {"lun": _c("PRJ-C"), "mar": _c("PRJ-C", "PRJ-1"), "mie": _c("PRJ-1")},
        "beto": {"jue": _c("PRJ-1")}, "carl": {"lun": _c("PRJ-X"), "vie": {"items": [], "nota": "solo nota"}}}
_eoc = sorted(R.en_obras_cerradas(_SEM, {"PRJ-C", "PRJ-X"}, {}))
chk("en_obras_cerradas: por persona y obra, con sus días", _eoc == [("ana", "PRJ-C", ["lun", "mar"]), ("carl", "PRJ-X", ["lun"])], _eoc)
_sc = R._sin_cerradas(_SEM["ana"], {"PRJ-C"}, {})
chk("_sin_cerradas: quita lo de la obra cerrada y deja lo demás (y el día que se queda vacío, fuera)",
    "lun" not in _sc and [i["a"] for i in _sc["mar"]["items"]] == ["PRJ-1"] and [i["a"] for i in _sc["mie"]["items"]] == ["PRJ-1"], _sc)
_esc = []
_d = [_sustituir(R, get_semana=lambda g, l: json.loads(json.dumps(_SEM)), trabajos_idx=lambda g: {},
                 guardar_persona=lambda g, l, u, dias: (_esc.append((u, dias)), (True, "ok"))[1])]
try:
    _ok, _msg = R.copiar_semana("G", date(2026, 11, 9), date(2026, 11, 16), cerradas={"PRJ-C", "PRJ-X"})
finally:
    for x in _d:
        x()
_por = {u: d for u, d in _esc}
chk("copiar_semana: lo de las obras cerradas NO se copia (ana sin el lunes de PRJ-C; carl solo con su nota)",
    _ok and "lun" not in _por.get("ana", {}) and set(_por.get("carl", {})) == {"vie"} and "beto" in _por, _por)
_n, _rp = funcion("core/roster_ui.py", "_radar_personal")
_n2, _rs = funcion("core/roster_ui.py", "_radar_scan")
chk("el Radar las cuenta y las enseña, y no les busca certificados",
    "_radar_cerradas(grupo, _ce)" in _rp and "len({pid for _u, pid, _d in _ce})" in _rp
    and "if not pid or pid in _cerradas:" in _rs, "")

# ═════════════════════════════════════════════════════════════════════════════
print("3. El Panel en DOMINGO, con una obra cerrada en el tablero (AppTest)")
GUION = r'''
import json, datetime
import streamlit as st
from core import roster as R, roster_ui as RU, auth, projects as P, credentials as C
from core import timeclock as TC, clock as CK
DOM = datetime.date(2026, 11, 15)
SIG = datetime.date(2026, 11, 16)
CK.today = lambda *a, **k: DOM
def _c(*asigs):
    return {"items": [{"a": a, "i": "07:00", "f": "15:30"} for a in asigs], "nota": ""}
SEMS = {SIG: {"ana": {"lun": _c("PRJ-C"), "mar": _c("PRJ-C")}, "beto": {"lun": _c("PRJ-1")}},
        SIG - datetime.timedelta(days=7): {"ana": {"lun": _c("PRJ-1")}}}
FILAS = [{"Group": "G", "Week": l.isoformat(), "User": u, "DataJSON": json.dumps(d)}
         for l, sem in SEMS.items() for u, d in sem.items()]
R._roster_records = lambda: FILAS
R._trab_records = lambda: []
R.is_configured = lambda: True
R._ws_roster = lambda: None
R.sin_planificar = lambda *a, **k: {"obras": [], "jefes": []}
st.session_state.setdefault("_LL", [])
R.limpiar_proyecto = lambda g, pid, usuarios=None, desde=None: (st.session_state["_LL"].append((pid, str(desde))), 2)[1]
TC.is_configured = lambda: False
TC.open_now = lambda g: []
TC.jornadas_largas = lambda *a, **k: []
USERS = [{"User": u, "Name": n, "Role": "field", "Group": "G"} for u, n in (("ana", "Ana"), ("beto", "Beto"), ("carl", "Carl"))]
auth.list_users = lambda *a, **k: USERS
auth.get_user = lambda u: next((x for x in USERS if x["User"] == u), None)
PRJ = [{"ID": "PRJ-1", "Name": "Torre", "Group": "G", "Status": "In progress", "Progress": "40"},
       {"ID": "PRJ-C", "Name": "Lift terminado", "Group": "G", "Status": "Completed", "Progress": "100"}]
P.list_projects = lambda *a, **k: [dict(p) for p in PRJ]
P.get_project = lambda pid: dict(next((p for p in PRJ if p["ID"] == pid), {}), RequiredCerts="White Card")
C.compliance = lambda usr, certs: {"cumple": False, "por_tipo": {"White Card": "vencido"}}
C.list_for = lambda u: []
if st.session_state.get("_TOOL"):
    st.session_state["_panel_tool"] = st.session_state["_TOOL"]
RU.render_planificacion("G")
'''
at = AppTest.from_string(GUION, default_timeout=120)
at.run()
chk("el Panel se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_md = " ¦ ".join(m.value for m in at.markdown)
_bt = {b.key: str(b.label) for b in at.button}
chk("H3 · el domingo 15/11 abre en la semana del 16/11 (no en la que acaba)", "16" in _md and ("16 – 20/11" in _md or "16/11" in _md)
    and at.session_state["ros_lunes"] == "2026-11-16", (at.session_state["ros_lunes"], _md[:300]))
chk("H3 · y la tarjeta dice «Free on Monday» con los libres del lunes (carl)", "Free on Monday" in _bt.get("cpxkpi_pnl_libres", "")
    and "Carl" in _bt.get("cpxkpi_pnl_libres", ""), _bt.get("cpxkpi_pnl_libres"))
chk("H4 · el Radar cuenta la obra cerrada (sin el certificado «que bloquea» en ella: solo beto en PRJ-1)",
    any("Radar (2)" in str(b.label) for b in at.button), [str(b.label) for b in at.button if "Radar" in str(b.label)])
at = AppTest.from_string(GUION, default_timeout=120)
at.session_state["_TOOL"] = "radar"
at.run()
_md = " ¦ ".join(m.value for m in at.markdown)
_bl = [str(b.label) for b in at.button]
chk("H4 · el Radar dice «Planned on a closed job» con la obra, «completed» y quién (Ana, 2 d)",
    "Planned on a closed job" in _md and "Lift terminado (PRJ-C) · completed — Ana (2 d)" in _md, _md[:900])
chk("H4 · …y los certificados que «bloquean» ya no hablan de la obra cerrada",
    not any("Lift terminado" in x for x in _bl if x.startswith("Ana →")), _bl)
_kl = [b for b in at.button if b.key == "radar_cerr_PRJ-C"]
chk("H4 · …con el botón para liberarla desde mañana", bool(_kl), [b.key for b in at.button])
if _kl:
    _kl[0].click().run()
    chk("H4 · …que la quita del tablero desde el LUNES 16/11 (mañana), no antes", ("PRJ-C", "2026-11-16") in
        list(at.session_state["_LL"]), list(at.session_state["_LL"]))
_n, _cc = funcion("core/roster_ui.py", "_confirmar_copia")
chk("H4 · «Copy previous week» avisa de lo que NO copia y copia sin las cerradas",
    "Not copied (the job is closed)" in _cc and "cerradas=_cerradas" in _cc)

# ═════════════════════════════════════════════════════════════════════════════
print("4. Compliance de un día que aún no ha llegado (H11)")
at = AppTest.from_string(GUION.replace("TC.is_configured = lambda: False", "TC.is_configured = lambda: True\n"
                                        "TC.proyectos_por_usuario_dia = lambda g, f: {}"), default_timeout=120)
at.session_state["_TOOL"] = "cumpl"
at.run()
_inf = " ".join(i.value for i in at.info)
_md = " ¦ ".join(m.value for m in at.markdown)
chk("Compliance se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("el lunes (aún no ha llegado) dice «hasn't started yet: 2 planned on a job», sin «not clocked in»",
    "hasn't started yet: 2 planned on a job" in _inf and "not clocked in" not in _md, (_inf, _md[:400]))

# ═════════════════════════════════════════════════════════════════════════════
print("5. La ausencia y el fin de semana (H15)")
chk("dias_con_datos: un sábado con solo una AUSENCIA no abre la columna", R.dias_con_datos({"ana": {"sab": _c("LEAVE")}}) == R.DIAS)
# v677 · con la NOTA que deja de verdad `aplicar_al_roster` («Sick leave · AUS-0009»): sin ella, el chk de arriba pasaba
# en vacío y en producción la semana del 30/11 seguía abriendo sábado y domingo (trampa 1)
chk("…tampoco con la nota que deja la ausencia («Sick leave · AUS-0009»)",
    R.dias_con_datos({"ana": {"sab": _c("LEAVE", nota="Sick leave · AUS-0009"),
                              "dom": _c("OFF", nota="Day off · AUS-0010")}}) == R.DIAS)
chk("…y una nota escrita en un día vacío sí la abre", R.dias_con_datos({"ana": {"sab": {"items": [], "nota": "van"}}})
    == R.DIAS + ["sab"])
chk("…uno con trabajo, sí", R.dias_con_datos({"ana": {"sab": _c("PRJ-1")}}) == R.DIAS + ["sab"])
_W = {}
_d = [_sustituir(R, get_semana=lambda g, l: json.loads(json.dumps(_W.get(str(l), {}))),
                 guardar_persona=lambda g, l, u, dias: (_W.__setitem__(str(l), {u: dias}), (True, "ok"))[1])]
try:
    _W.clear()
    _W["2026-11-30"] = {"ana": {"dom": _c("PRJ-1")}}
    AU.aplicar_al_roster({"ID": "AUS-9", "Type": "enfermedad", "User": "ana", "Group": "G", "From": "2026-12-01",
                          "To": "2026-12-08", "IncludesWeekends": ""})
    _s1 = dict(_W)
    _W.clear()
    AU.aplicar_al_roster({"ID": "AUS-8", "Type": "vacaciones", "User": "ana", "Group": "G", "From": "2026-12-04",
                          "To": "2026-12-07", "IncludesWeekends": "SI"})
    _s2 = dict(_W)
finally:
    for x in _d:
        x()
_dias1 = set(_s1.get("2026-11-30", {}).get("ana", {}))
chk("una baja SIN fines de semana no marca el sábado (vacío), y SÍ el domingo que tenía trabajo (se libera)",
    {"mar", "mie", "jue", "vie"} <= _dias1 and "sab" not in _dias1 and "dom" in _dias1
    and "AUS-9" in str(_s1["2026-11-30"]["ana"]["dom"]), _s1)
chk("…y una CON fines de semana los marca", {"sab", "dom"} <= set(_s2.get("2026-11-30", {}).get("ana", {})), _s2)

# ═════════════════════════════════════════════════════════════════════════════
print("6. La ficha: antes de empezar (H5) y la lista de cierre con el tablero (H4)")
ESTADO = r'''
import datetime as dt
import streamlit as st
from core import projects_ui as PU, projects as P, clock, alerts
from core import roster as R
clock.today = lambda *a, **k: dt.date(2026, 11, 15)
st.session_state.setdefault("auth", {"usuario": "admin2", "rol": "administrator", "grupo": "G", "nombre": "Bobo"})
_AV = st.session_state.get("_AV", 0)
_P = {"ID": "PRJ-9", "Group": "G", "Name": "Lift 9", "Status": "Completed" if _AV >= 100 else "Planned",
      "Progress": str(_AV), "StartDate": st.session_state.get("_INI", "2026-11-16"), "EndDateEst": "2026-12-11",
      "Type": "Installation"}
def _a(o, av, ini, fin):
    return {"ProjectID": "PRJ-9", "Order": str(o), "Name": "Act %d" % o, "DurationDays": "5", "Weight": "50",
            "Progress": str(av), "ActualStartDate": ini, "ActualEndDate": fin, "Note": ""}
_A = ([_a(1, 100, "2026-11-02", "2026-11-06"), _a(2, 100, "2026-11-06", "2026-11-09")] if _AV >= 100
      else [_a(1, 0, "", ""), _a(2, 0, "", "")])
P.get_project = lambda pid: dict(_P)
P.list_activities = lambda pid: [dict(a) for a in _A]
alerts.is_configured = lambda: False
R.sin_planificar = lambda *a, **k: {"obras": [], "jefes": []}
R.dias_desde = lambda g, pid, desde: ({"ana": 3, "beto": 2} if _AV >= 100 else {})
st.session_state.setdefault("_LL", [])
R.limpiar_proyecto = lambda g, pid, usuarios=None, desde=None: (st.session_state["_LL"].append((pid, str(desde))), 5)[1]
PU._bloqueos_de = lambda *a, **k: {}
PU._cumplimiento_equipo = lambda *a, **k: None
PU._nombres_de = lambda us, g: ["Ana" if u == "ana" else "Beto" for u in us]
from core import tareas as TA
TA.is_configured = lambda: False
PU._estado_section("PRJ-9", "G", dict(_P))
'''
at = AppTest.from_string(ESTADO, default_timeout=90)
at.run()
_tx = " ¦ ".join(x.value for x in list(at.markdown) + list(at.warning) + list(at.error))
chk("H5 · una obra que empieza mañana: «The job starts on 16/11/2026 (tomorrow)», sin «day -1» ni puntos",
    not at.exception and "starts on 16/11/2026</b> (tomorrow)" in _tx and "day -1" not in _tx and "points" not in _tx
    and "Starts on" in _tx and "Working days planned" in _tx, ([e.value for e in at.exception][:1], _tx[:600]))
at = AppTest.from_string(ESTADO, default_timeout=90)
at.session_state["_INI"] = "2026-11-20"
at.run()
_tx = " ¦ ".join(x.value for x in at.markdown)
chk("…y una que empieza en 5 días, «(in 5 days)»", "(in 5 days)" in _tx, _tx[:300])
at = AppTest.from_string(ESTADO, default_timeout=90)
at.session_state["_AV"] = 100
at.run()
_w = " ".join(w.value for w in at.warning)
chk("H4 · la lista de cierre de una obra TERMINADA cuenta sus días en el tablero desde mañana (5: Ana, Beto)",
    not at.exception and "**5** day(s) still on the board from tomorrow: Ana, Beto" in _w, ([e.value for e in at.exception][:1], _w[:500]))
_b = [b for b in at.button if b.key == "cierre_lib_PRJ-9"]
chk("H4 · …con el botón «Free it on the board from tomorrow»", bool(_b), [b.key for b in at.button])
if _b:
    _b[0].click().run()
    chk("H4 · …que libera DESDE MAÑANA (16/11)", ("PRJ-9", "2026-11-16") in list(at.session_state["_LL"]),
        list(at.session_state["_LL"]))

print("7. La ruta del día en domingo (H3)")
_rt = src("core/route_ui.py")
chk("sin nada planificado ese día de fin de semana, abre en el LUNES (`semana_de_trabajo`)",
    "if _hoy.weekday() >= 5:" in _rt and "_ini = _R.semana_de_trabajo(_hoy)" in _rt)

print("\n" + ("TODO OK" if not FALLOS else f"{len(FALLOS)} FALLO(S): {FALLOS}"))
sys.exit(1 if FALLOS else 0)
