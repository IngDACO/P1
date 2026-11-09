"""v666 · Ciclo 1 → mejoras 4/5: PLANIFICACIÓN Y ASISTENTES (y lo visto verificando v665).

  H14 obras en marcha sin nadie en el tablero y jefes sin un día en su obra: Radar (con el botón a Assign),
      la ficha («Plan it») y el alta lo dicen;
  H30 el Management assistant ve un rango de hasta una semana y lo que a la semana le falta;
  H37 «Who could cover it» cuenta días y asignaciones por separado;
  H31 la nómina que cubre un día se mira AHORA (también la generada después), y el asistente sabe que no ve nóminas;
  H29 el idioma de la pregunta, con su NOMBRE;
  H34 «planificado» y «fichado aquí» por separado en el día del campo;
  H45 el gasto de una orden recibida dice «Order», no «Orden».
Todo con las hojas SUSTITUIDAS en memoria: nada sale ni se escribe.
"""
import ast
import datetime as dt
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "jefa", "rol": "administrator", "grupo": "G"}
from streamlit.testing.v1 import AppTest                         # noqa: E402

fallos, n_ok = [], 0


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("   ok   " + q)
    else:
        fallos.append(q)
        print("   FALLO " + q + (("  -> " + str(det)) if det != "" else ""))


def fuente(rel):
    return io.open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8").read()


def funcion(rel, nombre):
    s = fuente(rel)
    for n in ast.walk(ast.parse(s)):
        if isinstance(n, ast.FunctionDef) and n.name == nombre:
            return ast.get_source_segment(s, n) or ""
    return ""


ADMIN = '{"usuario": "jefa", "rol": "administrator", "grupo": "G", "nombre": "Jefa"}'
LUNES = dt.date(2026, 11, 9)

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("1. H14 · Lo que a la semana le falta (roster.sin_planificar)")
from core import roster as R, projects as P                      # noqa: E402
_PRJS = [
    {"ID": "PRJ-1", "Status": "In progress", "StartDate": "2026-11-02", "EndDateEst": "2026-12-01", "HeadInstallers": "lead1"},
    {"ID": "PRJ-2", "Status": "Planned", "StartDate": "2026-11-12", "EndDateEst": "2026-11-30", "HeadInstallers": "lead2"},
    {"ID": "PRJ-3", "Status": "Completed", "StartDate": "2026-11-01", "EndDateEst": "2026-11-20", "HeadInstallers": "lead3"},
    {"ID": "PRJ-4", "Status": "Planned", "StartDate": "2026-12-20", "EndDateEst": "2027-01-20", "HeadInstallers": ""},
    {"ID": "PRJ-5", "Status": "In progress", "StartDate": "2026-10-01", "EndDateEst": "2026-11-06", "HeadInstallers": ""},
    {"ID": "PRJ-6", "Status": "In progress", "StartDate": "2026-11-01", "EndDateEst": "", "HeadInstallers": "lead6"},
    {"ID": "PRJ-7", "Status": "In progress", "StartDate": "2026-11-01", "EndDateEst": "2026-12-01", "HeadInstallers": ""},
    {"ID": "PRJ-8", "Status": "On hold", "StartDate": "2026-11-01", "EndDateEst": "2026-12-01", "HeadInstallers": ""}]
_SEM = {"x": {"lun": {"asig": "PRJ-1"}},
        "lead2": {"mar": {"items": [{"a": "PRJ-2", "i": "07:00", "f": "15:30"}]}},
        "y": {"lun": {"asigs": ["LEAVE"]}, "mie": {"asig": "TRB-1"}}}
_TIDX = {f"PRJ-{i}": {"ProjectID": f"PRJ-{i}"} for i in range(1, 9)}
_TIDX["TRB-1"] = {"ProjectID": ""}
_o = (R.get_semana, R.trabajos_idx, P.list_projects)
try:
    # la semana se pide por su LUNES (la clave del tablero): otra fecha no tiene datos
    R.get_semana = lambda g, l: {k: dict(v) for k, v in _SEM.items()} if l == LUNES else {}
    R.trabajos_idx = lambda g: dict(_TIDX)
    P.list_projects = lambda *a, **k: [dict(p) for p in _PRJS]
    _sp = R.sin_planificar("G", LUNES)
    _sp2 = R.sin_planificar("G", "2026-11-11")            # un miércoles en texto: cuenta su semana
finally:
    R.get_semana, R.trabajos_idx, P.list_projects = _o
chk("⚠️ obras en marcha esta semana SIN nadie: PRJ-6 y PRJ-7 (una con un trabajo sin obra y una baja no cuentan)",
    _sp["obras"] == ["PRJ-6", "PRJ-7"], _sp)
chk("…y no las terminadas, en pausa, futuras ni acabadas antes del lunes", not set(_sp["obras"]) & {"PRJ-3", "PRJ-4", "PRJ-5", "PRJ-8"})
chk("⚠️ jefes sin un día en SU obra: lead1 (PRJ-1, con otro en ella) y lead6; lead2 sí tiene su día",
    _sp["jefes"] == [("lead1", "PRJ-1"), ("lead6", "PRJ-6")], _sp["jefes"])
chk("…y con una fecha en texto a mitad de semana, la misma respuesta (pide su lunes)", _sp2 == _sp, _sp2)

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("2. H14 · El Radar")
G2 = r'''
import datetime as dt
import streamlit as st
from core import roster_ui as RU, projects as P, auth
st.session_state.setdefault("auth", ''' + ADMIN + r''')
P.list_projects = lambda *a, **k: [{"ID": "PRJ-6", "Name": "Obra Seis"}, {"ID": "PRJ-1", "Name": "Obra Uno"}]
auth.list_users = lambda g=None, **k: [{"User": "lead1", "Name": "Lead One"}, {"User": "lead6", "Name": "Lead Six"}]
RU._radar_personal("G", dt.date(2026, 11, 9), [], {}, scan=([], [], {}, {"choques": [], "certs": []}),
                   sp=st.session_state.get("_SP", {"obras": [], "jefes": []}))
'''
at = AppTest.from_string(G2, default_timeout=60)
at.session_state["_SP"] = {"obras": ["PRJ-6"], "jefes": [("lead6", "PRJ-6"), ("lead1", "PRJ-1")]}
at.run()
_b = {b.key: str(b.label) for b in at.button}
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("⚠️ la obra sin nadie, con su jefe al lado", "Obra Seis (PRJ-6)" in _b.get("radar_sp_0", "")
    and "head installer: Lead Six" in _b.get("radar_sp_0", ""), _b)
chk("…y el jefe sin días en una obra que SÍ tiene gente, aparte (no se repite el de PRJ-6)",
    "Lead One" in _b.get("radar_jf_0", "") and "Obra Uno (PRJ-1)" in _b.get("radar_jf_0", "") and "radar_jf_1" not in _b, _b)
at.button(key="radar_sp_0").click().run()
chk("⚠️ la línea ABRE Assign con la obra elegida", at.session_state["ai_prj"] == "PRJ-6"
    and at.session_state["_panel_tool"] == "asignar")
at = AppTest.from_string(G2, default_timeout=60).run()
chk("sin nada que decir, el mensaje de siempre",
    any("No shift clashes and no blocking certificates" in str(s.value) for s in at.success))
_rp = funcion("core/roster_ui.py", "render_planificacion")
chk("el Panel lo calcula una vez, lo cuenta en «Radar (n)» y se lo pasa",
    "_sp = R.sin_planificar(grupo, lunes)" in _rp
    and '_n_rad = len(_scan[0]) + len(_scan[1]) + len(_sp["obras"]) + len(_sp["jefes"])' in _rp
    and "_radar_personal(grupo, lunes, staff, tidx, scan=_scan, sp=_sp)" in _rp)

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("3. H14 · La ficha y el alta")
G3 = r'''
import streamlit as st
from core import projects_ui as PU, roster as R
st.session_state.setdefault("auth", st.session_state["_AUTH"])
R.sin_planificar = lambda g, l: st.session_state["_SP"]
PU._nombres_de = lambda us, g: [str(x).upper() for x in us]
PU._plan_semana_section("PRJ-6", "G", {"ID": "PRJ-6", "Status": st.session_state.get("_EST", "In progress")})
'''
OFI = {"usuario": "jefa", "rol": "administrator", "grupo": "G"}


def _g3(sp, auth=OFI, est="In progress"):
    a = AppTest.from_string(G3, default_timeout=60)
    a.session_state["_AUTH"], a.session_state["_SP"], a.session_state["_EST"] = auth, sp, est
    return a.run()


at = _g3({"obras": ["PRJ-6"], "jefes": []})
chk("⚠️ sin nadie esta semana: el aviso y «Plan it»", not at.exception
    and any("Nobody is planned on this job this week" in str(w.value) for w in at.warning)
    and [b for b in at.button if b.key == "plan_sp_PRJ-6"])
at.button(key="plan_sp_PRJ-6").click().run()
chk("…«Plan it» lleva a Planning → Panel con Assign y la obra elegida",
    at.session_state["ai_prj"] == "PRJ-6" and at.session_state["_panel_tool"] == "asignar"
    and tuple(at.session_state["_admin_nav_pending"]) == ("planificacion", "🎛 Panel"))
at = _g3({"obras": [], "jefes": [("lead1", "PRJ-6")]})
chk("…con gente pero sin su jefe, una línea", any("Head installer LEAD1: no day on this job this week" in str(c.value)
                                                  for c in at.caption))
chk("…nada para el campo ni para una obra completada",
    not _g3({"obras": ["PRJ-6"], "jefes": []}, auth={"usuario": "f1", "rol": "field", "grupo": "G"}).warning
    and not _g3({"obras": ["PRJ-6"], "jefes": []}, est="Completed").warning)
_es = funcion("core/projects_ui.py", "_estado_section")
chk("la pestaña Status lo enseña arriba", 0 <= _es.find("_plan_semana_section(pid, grupo, prj)") < _es.find("ps = P.project_schedule(pid)"))
chk("el alta, si el tablero no pudo llenar nada, dice que la obra se queda sin nadie y dónde arreglarlo",
    "so **nobody is planned on this job yet**. Use «Plan it» in its Status tab" in funcion("core/projects_ui.py", "_autoagenda"))

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("4. H37 · «Who could cover it»")
_au = fuente("core/ausencias_ui.py")
chk("cuenta los DÍAS distintos, y las asignaciones aparte cuando no coinciden",
    '_nd = len({c["fecha"] for c in ch})' in _au
    and 't("Who could cover it ({n} day(s))").replace("{n}", str(_nd)) if _nd == len(ch)' in _au
    and 't("Who could cover it ({d} day(s) · {n} assignments)")' in _au and "with st.expander(_tit_c," in _au)

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("5. H31 · La nómina que cubre un día, AHORA")
from core import correcciones as CO, payroll as PR                # noqa: E402
_o = PR.list_nominas
try:
    PR.list_nominas = lambda g, *a, **k: [{"ID": "NOM-2", "User": "u1", "PeriodFrom": "2026-11-03", "PeriodTo": "2026-11-09"}]
    _n1 = CO.nomina_de({"User": "u1", "NewValue": "2026-11-04 14:30", "PayslipCovers": ""}, "G")
    _n2 = CO.nomina_de({"User": "u1", "NewValue": "2026-11-04 14:30", "PayslipCovers": "NOM-1"}, "G")
    _n3 = CO.nomina_de({"User": "u1", "NewValue": "2026-11-12 14:30", "PayslipCovers": ""}, "G")
    _n4 = CO.nomina_de({"User": "u2", "NewValue": "2026-11-04 14:30", "PayslipCovers": ""}, "G")
finally:
    PR.list_nominas = _o
chk("⚠️ sin anotar al crearla, la nómina generada DESPUÉS se ve (NOM-2)", _n1 == "NOM-2", _n1)
chk("…la anotada manda; fuera del periodo o de otra persona, nada", _n2 == "NOM-1" and _n3 == "" and _n4 == "", (_n2, _n3, _n4))
_ct = fuente("core/chat_tools.py")
chk("la pantalla, la bandeja y la tarjeta del asistente preguntan ahí",
    "_nom_id = C.nomina_de(r, grupo)" in fuente("core/correcciones_ui.py")
    and '"already_on_payslip": CO.nomina_de(r, g),' in _ct and '_nom = CO.nomina_de(r, ctx["grupo"])' in _ct)
chk("…y la bandeja le dice que NO ve las nóminas (y dónde están)",
    '"payslips": "You cannot see payslips.' in _ct and "say you cannot see payroll" in _ct)

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("6. H30 · El equipo de una semana")
from core import chat_tools as CT, admin_digest as AD, auth as AUTH, ausencias as AUS, credentials as CRD  # noqa: E402
from core import timeclock as TC, clock                           # noqa: E402
ctx = {"usuario": "jefa", "grupo": "G", "rol": "administrator", "nombre": "Jefa"}
_o = (TC.open_now, AUTH.list_users, AUTH.etiqueta_usuarios, R.asignaciones_dia, AUS.ausentes_en, AD.nombres_usuarios,
      R.sin_planificar, CRD.expiring, CT._mis_obras, clock.today)
try:
    TC.open_now = lambda g: []
    AUTH.list_users = lambda g=None, **k: [{"User": "f1", "Role": "field", "Name": "F One"}]
    AUTH.etiqueta_usuarios = lambda us, *a, **k: {str(u.get("User")): str(u.get("Name")) for u in us}
    R.asignaciones_dia = lambda g, u, d: ([{"etiqueta": "Obra Uno", "proyecto_id": "PRJ-1", "nota": ""}]
                                          if d.weekday() < 5 else [])
    AUS.ausentes_en = lambda g, d: ([{"ID": "AUS-1", "User": "f2", "Name": "F Two", "Type": "annual", "From": "2026-11-10",
                                      "To": "2026-11-11", "Status": "approved"}] if d.day in (10, 11) else [])
    AD.nombres_usuarios = lambda: {}
    R.sin_planificar = lambda g, l: {"obras": ["PRJ-6"], "jefes": [("lead1", "PRJ-1")]}
    CRD.expiring = lambda g: []
    CT._mis_obras = lambda c: [{"ID": "PRJ-6", "Name": "Obra Seis"}, {"ID": "PRJ-1", "Name": "Obra Uno"}]
    clock.today = lambda *a, **k: LUNES
    _w = CT._equipo({"date": "2026-11-09", "to": "2026-11-15"}, ctx)
    _d1 = CT._equipo({"date": "2026-11-09"}, ctx)
    _negs = []
    for e in ({"date": "2026-11-09", "to": "2026-11-08"}, {"date": "2026-11-09", "to": "2026-11-16"}):
        try:
            CT._equipo(e, ctx)
            _negs.append(None)
        except CT._Negado as x:
            _negs.append(str(x))
finally:
    (TC.open_now, AUTH.list_users, AUTH.etiqueta_usuarios, R.asignaciones_dia, AUS.ausentes_en, AD.nombres_usuarios,
     R.sin_planificar, CRD.expiring, CT._mis_obras, clock.today) = _o
chk("⚠️ la semana entera: lo planificado de cada día, con su fecha (5 días laborables)",
    len(_w["planned"]) == 5 and _w["planned"][0]["date"] == "09/11/2026" and _w["planned"][-1]["date"] == "13/11/2026"
    and _w.get("to") == "15/11/2026", _w["planned"][:2])
chk("…una ausencia de dos días, UNA vez", len(_w["absent"]) == 1, _w["absent"])
chk("⚠️ y lo que a la semana le falta, como el Radar",
    _w["the_week_on_the_board"].get("running_jobs_with_nobody_planned") == [{"project_id": "PRJ-6", "job": "Obra Seis"}]
    and _w["the_week_on_the_board"].get("head_installers_with_no_day_on_their_job") == [
        {"who": "lead1", "project_id": "PRJ-1", "job": "Obra Uno"}], _w["the_week_on_the_board"])
chk("…sin «to», un día como antes", len(_d1["planned"]) == 1 and "to" not in _d1, _d1["planned"])
chk("…y «to» antes de la fecha o a más de 6 días se niega", all(_negs) and "at most 6 days" in _negs[1], _negs)
chk("la herramienta get_team acepta «to»", '"to": {"type": "string", "description": "YYYY-MM-DD, optional: up to 6 days after date' in _ct)

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("7. H34 · Planificado y fichado, por separado")
from core import credentials as CR2                                # noqa: E402
_o = (TC.open_sessions, TC.olvidos, R.asignaciones_dia, CT._mis_obras, P.get_project, CT._estado_del_dia, CR2.list_for, clock.today)
try:
    TC.open_sessions = lambda n, g, u: {TC.TIPO_PROYECTO: {"proyecto_id": "PRJ-39", "proyecto": "C1"}}
    TC.olvidos = lambda s: False
    R.asignaciones_dia = lambda g, u, d: [{"proyecto_id": "PRJ-38", "etiqueta": "Obra 38", "nota": ""}]
    CT._mis_obras = lambda c: []
    P.get_project = lambda pid: {"ID": pid, "Name": "Obra " + pid}
    CT._estado_del_dia = lambda prj, pid, c: {}
    CR2.list_for = lambda u: []
    clock.today = lambda *a, **k: LUNES
    _md = CT._mi_dia({}, {"usuario": "f1", "grupo": "G", "rol": "field", "nombre": "F One"})
finally:
    (TC.open_sessions, TC.olvidos, R.asignaciones_dia, CT._mis_obras, P.get_project, CT._estado_del_dia, CR2.list_for,
     clock.today) = _o
_j = {x["project_id"]: x for x in _md["jobs_today"]}
chk("⚠️ la obra donde solo FICHÓ no sale como planificada",
    _j["PRJ-39"]["planned_for_you_today"] is False and _j["PRJ-39"]["you_are_clocked_in_here"] is True, _j)
chk("…y la del tablero sí", _j["PRJ-38"]["planned_for_you_today"] is True and _j["PRJ-38"]["you_are_clocked_in_here"] is False, _j)
chk("…y la descripción de get_my_day lo dice", "never call a job planned just because they clocked in" in _ct)

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("8. H29 · El idioma, con su nombre")
from core import chat_agent as CA                                 # noqa: E402
_casos = [("Which active jobs have nobody planned on the board this week?", "English"),
          ("¿Qué obras no tienen a nadie esta semana?", "Spanish"), ("que obras tiene campo000 hoy", "Spanish"),
          ("Who is off tomorrow?", "English"), ("PRJ-0039?", ""), ("ok", "")]
chk("idioma_de acierta inglés, español (con y sin acentos) y no adivina lo que no se puede",
    all(CA.idioma_de(q) == v for q, v in _casos), [(q, CA.idioma_de(q)) for q, _ in _casos])
_en = CA._idioma_tras_datos("Which active jobs have nobody planned on the board this week?")
_xx = CA._idioma_tras_datos("PRJ-0039?")
chk("⚠️ el recordatorio NOMBRA el idioma cuando se sabe", "in English:" in _en and "Write your whole answer in English" in _en, _en)
chk("…y si no, el de siempre (el idioma de la pregunta)", "in the language of that question" in _xx, _xx)

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("9. H45 · El gasto de una orden recibida, en inglés")
from core import orders as O, expenses as E                      # noqa: E402
_cap = {}
_o = (E.add, E._records)
try:
    E.add = lambda *a, **k: (_cap.update(k), (True, "ok"))[1]
    E._records = lambda *a, **k: []
    O._crear_gasto({"ID": "ORD-00001", "ProjectID": "PRJ-1", "Group": "G", "Supplier": "S", "Description": "10 interlocks",
                    "Category": "Materials"}, 1910.0)
finally:
    E.add, E._records = _o
chk("⚠️ «Order ORD-00001 · 10 interlocks» (era «Orden»)", _cap.get("descripcion") == "Order ORD-00001 · 10 interlocks", _cap)

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
for f in fallos:
    print("  - " + f)
sys.exit(1 if fallos else 0)
