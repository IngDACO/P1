# -*- coding: utf-8 -*-
"""v554 · DAY ROUTE, PROBADA ACCIÓN POR ACCIÓN.

Recorrido en producción (09/10/2026, cuenta admin). Lo arreglado («Dale»):
  1. Un día FUTURO salía «⚠️ not clocked in» para todos (el martes 13) → «🗓️ planned»; hoy,
     «not clocked in yet» (como Compliance); un día pasado, «not clocked in».
  2. «Today's sites» / «with people today» en cualquier día → el día que se mira.
  3. «On site» contaba ASIGNACIONES (una persona en dos obras = 2; «2 of 2 people» con otra
     sin plan) y un día futuro nadie está en obra → «Planned», y cuenta personas.
  4. «Planned» y «No plan» llevaban al Panel en OTRA semana → la del día que se mira.
  5. «←» devolvía la pantalla a HOY (Streamlit purga el widget no pintado) → se recuerda.
  6. Las obras no se podían tocar → el nombre en su tarjeta abre la obra; «Sites» y
     «No location» con UNA obra la abren («No location» cuenta obras, no filas).
  7. «Friday 9 of October» (calco del español) → «Friday 9 October»; el aviso de fin de
     semana por `t()` y sin minúscula; las etiquetas de las tarjetas por `t()`.

AppTest con datos inventados; ninguna hoja se toca. «Hoy» = miércoles 07/10/2026.
"""
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
fallos, n_ok = [], 0


def ok(q):
    global n_ok
    n_ok += 1
    print("  ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("  FALLO %s%s" % (q, ("  -> " + str(det)) if det != "" else ""))


def chk(q, cond, det=""):
    (ok(q) if cond else fallo(q, det))


SRC = io.open(os.path.join("core", "route_ui.py"), encoding="utf-8").read()
_i = SRC.find("def render_ruta_dia(")
RD = SRC[_i:SRC.find("\ndef ", _i + 10)]

print("1. Estático")
chk("se encontró `render_ruta_dia` (no es un paso en vacío)", "rutadia_fecha" in RD)
# ⚠️ Por AST: cortar el texto en el primer «)» se quedaba en el de `t("Day")` y nunca veía
# los argumentos — la batería lo cazó (rotura escapada).
import ast                                                          # noqa: E402
_di = [n for n in ast.walk(ast.parse(SRC)) if isinstance(n, ast.Call)
       and getattr(n.func, "attr", "") == "date_input"
       and any(k.arg == "key" and getattr(k.value, "value", "") == "rutadia_fecha"
               for k in n.keywords)]
chk("se encontró el `date_input` de la fecha (no es un paso en vacío)", len(_di) == 1, len(_di))
chk("…y va SIN `value` (con él y el estado, Streamlit avisa en el log)",
    bool(_di) and not any(k.arg == "value" for k in _di[0].keywords) and len(_di[0].args) <= 1,
    [k.arg for k in _di[0].keywords] if _di else None)
# ⚠️ «On site» sigue en el COMENTARIO que explica el cambio: se busca el literal (trampa 2)
chk("ya no queda la etiqueta «On site» ni el « of » de la fecha",
    "engineering: On site" not in RD and "{fecha.day} of" not in RD)

print("\n2. Con clics reales (AppTest)")
from streamlit.testing.v1 import AppTest                             # noqa: E402

GUION = r'''
import datetime as dt
import streamlit as st
from core import route_ui as RT, auth, roster, projects as P, timeclock as TC, clock
from core import location_ui as LU

HOY = dt.date(2026, 10, 7)                                   # miércoles
if not hasattr(clock, "_v554_today"):
    clock._v554_today = clock.today
clock.today = lambda *a, **k: HOY
LU.geocode = lambda *a, **k: None
auth.list_users = lambda *a, **k: [
    {"User": u, "Name": n, "Role": "field", "Active": "SI"}
    for u, n in (("ana", "Ana"), ("beto", "Beto"), ("carl", "Carl"), ("dani", "Dani"))]
def _a(pid, et):
    return {"proyecto_id": pid, "etiqueta": et, "asig": pid, "ini": "", "fin": ""}
def _asig(g, u, f):
    if f.weekday() > 4:
        return []
    if f.weekday() == 4:                                     # viernes: solo Ana, en Torre
        return [_a("PRJ-1", "Torre")] if u == "ana" else []
    return {"ana": [_a("PRJ-1", "Torre"), _a("PRJ-2", "Redfen")],
            "beto": [_a("PRJ-3", "Sinpin")], "dani": [_a("PRJ-3", "Sinpin")]}.get(u, [])
roster.asignaciones_dia = _asig
roster.get_semana = lambda g, l: {}
P.get_project = lambda pid: {
    "PRJ-1": {"Name": "Torre", "Lat": "-33.80", "Lng": "151.20", "Location": "Calle 1"},
    "PRJ-2": {"Name": "Redfen", "Lat": "-33.90", "Lng": "151.10", "Location": "Calle 2"},
    "PRJ-3": {"Name": "Sinpin", "Lat": "", "Lng": "", "Location": ""}}.get(pid)
TC.proyectos_por_usuario_dia = lambda g, f: (
    {"ana": [{"pid": "PRJ-1", "nombre": "Torre"}]} if (f == HOY and st.session_state.get("_FICH")) else {})
if st.session_state.get("_OTRA"):
    st.write("otra pantalla")                                # el widget de la fecha NO se pinta
else:
    RT.render_ruta_dia("G")
'''


def b(at, k):
    x = [y for y in at.button if y.key == k]
    return x[0] if x else None


def lbl(at, k):
    x = b(at, k)
    return x.label.replace("\n\n", " | ") if x else None


def tabla(at):
    return at.dataframe[0].value.to_dict("records") if at.dataframe else []


def textos(at):
    return " | ".join([m.value for m in at.markdown] + [m.value for m in at.info])


def limpia(at):
    for k in ("_admin_nav_pending", "_prjsel_pending"):
        if k in at.session_state:
            del at.session_state[k]


at = AppTest.from_string(GUION, default_timeout=90)
at.run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])

print("   a) HOY (miércoles 07/10)")
chk("la fecha dice «Wednesday 7 October» (sin «of»)", "Wednesday 7 October" in textos(at)
    and " of October" not in textos(at), textos(at)[:200])
chk("⚠️ «Planned» cuenta PERSONAS: Ana (2 obras), Beto y Dani = 3 de 4",
    lbl(at, "cpxkpi_rd_obra") == ":material/engineering: Planned | 3 | of 4 people",
    lbl(at, "cpxkpi_rd_obra"))
chk("«No location» cuenta OBRAS sin pin: 1 (Beto y Dani van a la misma)", (lbl(at, "cpxkpi_rd_sinubic") or "").split(" | ")[1:2] == ["1"],
    lbl(at, "cpxkpi_rd_sinubic"))
chk("«No plan» = Carl", lbl(at, "cpxkpi_rd_sinplan") == ":material/help: No plan | 1 | Carl",
    lbl(at, "cpxkpi_rd_sinplan"))
chk("«Sites» hoy: «with people today»", (lbl(at, "cpxkpi_rd_sitios") or "").endswith("with people today"),
    lbl(at, "cpxkpi_rd_sitios"))
chk("la lista se titula «Today's sites»", "**Today's sites** — in travel order" in textos(at))
_est = [r["Status"] for r in tabla(at)]
chk("⚠️ hoy, sin fichar: «not clocked in yet»",
    bool(_est) and all(e == "⚠️ not clocked in yet" for e in _est), _est)
at.session_state["_FICH"] = True
at.run()
_est = {r["Site"]: r["Status"] for r in tabla(at) if r["Persona"] == "Ana"}
chk("hoy, fichada en Torre: Torre «clocked in here» y Redfen «clocked in at Torre»",
    _est.get("Torre") == "🟢 clocked in here" and _est.get("Redfen") == "🔴 clocked in at Torre", _est)
at.session_state["_FICH"] = False

print("   b) las obras se abren")
limpia(at)
b(at, "rd_prj_1").click()
at.run()
chk("⚠️ el nombre de la obra 1 en su tarjeta la abre en Proyectos",
    at.session_state["_prjsel_pending"] in ("PRJ-1", "PRJ-2")
    and at.session_state["_admin_nav_pending"] == ("proyectos", "📊 Proyectos"))
limpia(at)
b(at, "cpxkpi_rd_sinubic").click()
at.run()
chk("⚠️ «No location» con UNA obra sin pin abre ESA obra (PRJ-3)",
    "_prjsel_pending" in at.session_state and at.session_state["_prjsel_pending"] == "PRJ-3")
limpia(at)
b(at, "cpxkpi_rd_sitios").click()
at.run()
chk("«Sites» con DOS obras lleva a la cartera (sin abrir ninguna)",
    "_prjsel_pending" not in at.session_state
    and at.session_state["_admin_nav_pending"] == ("proyectos", "📊 Proyectos"))
limpia(at)

print("   c) un día PASADO (martes 06/10)")
b(at, "rd_prev").click()
at.run()
_est = [r["Status"] for r in tabla(at)]
chk("pasado: «not clocked in» (sin «yet»)", bool(_est) and all(e == "⚠️ not clocked in" for e in _est), _est)
chk("…y la lista dice el día («Sites on Tuesday 6 October»)",
    "**Sites on Tuesday 6 October** — in travel order" in textos(at), textos(at)[:300])

print("   d) un día FUTURO (jueves 08/10)")
b(at, "rd_next").click()
at.run()
b(at, "rd_next").click()
at.run()
_est = [r["Status"] for r in tabla(at)]
chk("⚠️ futuro: «planned», sin aviso", bool(_est) and all(e == "🗓️ planned" for e in _est), _est)
chk("…«Sites» dice «with people that day»", (lbl(at, "cpxkpi_rd_sitios") or "").endswith("with people that day"),
    lbl(at, "cpxkpi_rd_sitios"))

print("   e) el viernes 09/10 (una sola obra)")
b(at, "rd_next").click()
at.run()
b(at, "cpxkpi_rd_sitios").click()
at.run()
chk("«Sites» con UNA obra la abre", "_prjsel_pending" in at.session_state
    and at.session_state["_prjsel_pending"] == "PRJ-1")
limpia(at)

print("   f) fin de semana")
b(at, "rd_next").click()
at.run()
_inf = " ".join(m.value for m in at.info)
chk("el sábado: «Nothing is planned for this Saturday.» (con mayúscula)",
    "Nothing is planned for this Saturday." in _inf, _inf)

print("   g) el Panel, en la semana del día que se mira")
b(at, "rd_next").click()
at.run()
b(at, "rd_next").click()
at.run()                                            # lunes 12/10, OTRA semana
b(at, "rd_next").click()
at.run()                                            # martes 13/10
chk("estamos en el martes 13 (no es un paso en vacío)", "Tuesday 13 October" in textos(at))
b(at, "cpxkpi_rd_sinplan").click()
at.run()
chk("⚠️ «No plan» abre el Panel en la semana del 12/10",
    at.session_state["ros_lunes"] == "2026-10-12"
    and at.session_state["_admin_nav_pending"] == ("planificacion", "🎛 Panel"))
at.session_state["ros_lunes"] = "2026-10-05"
limpia(at)
b(at, "cpxkpi_rd_obra").click()
at.run()
chk("«Planned» también", at.session_state["ros_lunes"] == "2026-10-12")
limpia(at)

print("   h) volver recuerda el día")
at.session_state["_OTRA"] = True
at.run()                                            # la fecha no se pinta: Streamlit la purga
chk("la otra pantalla purga el widget de la fecha (la prueba no es en vacío)",
    "rutadia_fecha" not in at.session_state)
at.session_state["_OTRA"] = False
at.run()
chk("⚠️ al volver, sigue en el martes 13 (no vuelve a hoy)", "Tuesday 13 October" in textos(at),
    textos(at)[:120])
chk("sin excepción en todo el recorrido", not at.exception, [e.value for e in at.exception][:1])

print("\n3. La premisa del `date_input` sin `value`")
# ⚠️ Una sonda del LOG no sirve aquí: en AppTest esa regla de Streamlit no corre (sin
# runtime), así que «0 avisos» saldría hasta provocándolo — comprobado: el caso
# conocido-bueno tampoco lo daba (trampa nº12). Lo que SÍ se puede afirmar es la premisa
# del arreglo, en el propio Streamlit instalado (el del Cloud, fijado en requirements):
# el `date_input` solo pasa `default_value` a la regla cuando `value` no es "today".
import streamlit as _st_mod                                         # noqa: E402
_tw = io.open(os.path.join(os.path.dirname(_st_mod.__file__), "elements", "widgets",
                           "time_widgets.py"), encoding="utf-8").read()
chk("Streamlit %s: sin `value` (=\"today\") el `date_input` no avisa" % _st_mod.__version__,
    'default_value=value if value != "today" else None' in _tw)

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
