# -*- coding: utf-8 -*-
"""v526 · EL SELECTOR DE OBRA DEL CAMPO GUARDA EL ID (y dos detalles vistos en producción).

La prueba de v525 EN PRODUCCIÓN destapó que, al confirmar un parte, el trabajador volvía a
«— choose a project —»: el desplegable guardaba la ETIQUETA, que lleva el estado
(«— Planned»), y al acreditar lo primero la obra pasaba a «In progress» — la etiqueta
guardada dejaba de existir y Streamlit tiraba la selección. Pasaba también al marcar a mano
y al completar una obra. Lo que protege, EJECUTANDO la pantalla con AppTest:
  (a) ⚠️ cambiar el ESTADO de la obra elegida no la des-elige;
  (b) un valor viejo (la etiqueta de antes de v526) se rescata por su ID, y una obra que ya
      no es suya vuelve a «elegir» sin reventar;
  (c) lo de antes sigue: una sola obra se abre sola (v480) y el fichaje abierto elige la suya;
  (d) un parte de OTRO día enseña cuándo se escribió SIN segundos;
  (e) la caja del asistente, en el idioma base y por `t()`.
"""
import ast
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

fallos, n_ok = [], 0


def ok(q, det=""):
    global n_ok
    n_ok += 1
    print("   ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("   FALLO %s%s" % (q, ("  -> " + str(det)) if det else ""))


def sec(x):
    print("\n" + x)
    print("-" * 70)


def chk(q, cond, det=""):
    (ok if cond else fallo)(q, det)


from streamlit.testing.v1 import AppTest                          # noqa: E402

APP = r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "campo000", "nombre": "Field Test",
                                     "rol": "field", "grupo": "cliente1"})
from core import projects as P, projects_ui as PU, timeclock, roster, route_ui
from core import stage_progress_ui as SPU

ss = st.session_state
ss.setdefault("_estado", {"PRJ-1": "Planned", "PRJ-2": "Planned"})
ss.setdefault("_obras", ["PRJ-1", "PRJ-2"])
ss.setdefault("_fichado", "")
NOMBRES = {"PRJ-1": "Job A", "PRJ-2": "Job B"}


def _prj(pid):
    return {"ID": pid, "Name": NOMBRES[pid], "Status": ss["_estado"][pid], "Progress": "0",
            "Client": "Test client", "Type": "Installation", "Location": ""}


P.is_configured = lambda: True
P.list_projects_for_field = lambda u, grupo=None, incluir_internos=False: [
    _prj(p) for p in ss["_obras"]]
P.get_project = lambda pid: _prj(pid) if pid in NOMBRES else None
P.es_interno = lambda prj: False
timeclock.open_sessions = lambda n, g, u: (
    {timeclock.TIPO_PROYECTO: {"proyecto": ss["_fichado"]}} if ss["_fichado"] else {})
roster.is_configured = lambda: False
route_ui.render_mi_ruta = lambda u, g: None
PU._induccion_section = lambda *a, **k: None
SPU.render = lambda pid, grupo, prj, key_prefix="": (st.caption("AVANCE DE " + pid) or True)
PU.render_field_projects("campo000", "cliente1")
'''


def _app(**estado):
    at = AppTest.from_string(APP, default_timeout=90)
    for k, v in estado.items():
        at.session_state[k] = v
    return at.run()


def _sel(at):
    return next((s for s in at.selectbox if s.key == "fieldproj_sel"), None)


def _abierta(at):
    return [c.value for c in at.caption if c.value.startswith("AVANCE DE ")]


# ═════════════════════════════════════════════════════════════════
sec("1. ⚠️ Cambiar el ESTADO de la obra elegida no la des-elige (el fallo de producción)")
at = _app()
chk("la pantalla se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
s = _sel(at)
chk("dos obras: nada elegido de entrada",
    s is not None and s.value == "— choose a project —" and _abierta(at) == [],
    None if s is None else s.value)
chk("las opciones se VEN con su nombre, ID y estado",
    s is not None and "Job B (PRJ-2) — Planned" in s.options, None if s is None else s.options)
if s is not None:
    s.set_value("PRJ-2")
    at.run()
chk("elegida Job B: se abre", _abierta(at) == ["AVANCE DE PRJ-2"], _abierta(at))
at.session_state["_estado"] = {"PRJ-1": "Planned", "PRJ-2": "In progress"}
at.run()
s = _sel(at)
chk("⚠️ pasa a «In progress» (lo primero acreditado) y SIGUE elegida",
    s is not None and s.value == "PRJ-2" and _abierta(at) == ["AVANCE DE PRJ-2"],
    (None if s is None else s.value, _abierta(at)))
chk("...y la etiqueta ya dice el estado nuevo",
    s is not None and "Job B (PRJ-2) — In progress" in s.options, None if s is None else s.options)
at.session_state["_estado"] = {"PRJ-1": "Planned", "PRJ-2": "Completed"}
at.run()
chk("...y al COMPLETARSE, también", _abierta(at) == ["AVANCE DE PRJ-2"], _abierta(at))

# ═════════════════════════════════════════════════════════════════
sec("2. Valores que ya no casan")
at = _app(fieldproj_sel="Job B (PRJ-2) — Planned")
s = _sel(at)
chk("una ETIQUETA de antes de v526 se rescata por su ID",
    not at.exception and s is not None and s.value == "PRJ-2" and _abierta(at) == ["AVANCE DE PRJ-2"],
    (None if s is None else s.value, [e.value for e in at.exception][:1]))
at = _app(fieldproj_sel="PRJ-9")
s = _sel(at)
chk("una obra que ya no es suya vuelve a «elegir», sin reventar",
    not at.exception and s is not None and _abierta(at) == [],
    (None if s is None else s.value, [e.value for e in at.exception][:1]))

# ═════════════════════════════════════════════════════════════════
sec("3. Lo de antes sigue igual")
at = _app(_obras=["PRJ-1"])
s = _sel(at)
chk("una sola obra se abre sola (v480), guardando su ID",
    s is not None and s.value == "PRJ-1" and _abierta(at) == ["AVANCE DE PRJ-1"],
    (None if s is None else s.value, _abierta(at)))
at = _app(_fichado="Job B")
s = _sel(at)
chk("con fichaje abierto en Job B, se abre ESA",
    s is not None and s.value == "PRJ-2" and _abierta(at) == ["AVANCE DE PRJ-2"],
    (None if s is None else s.value, _abierta(at)))

# ═════════════════════════════════════════════════════════════════
sec("4. Un parte de OTRO día: cuándo se escribió, sin segundos")
APP_DL = r'''
import datetime as _dt
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "otro", "nombre": "x", "rol": "field",
                                     "grupo": "cliente1"})
from core import clock, daily_log as DL, daily_log_ui as DLU
LOGS = [{"ID": "LOG-1", "ProjectID": "P", "Date": "2026-09-26", "Author": "campo000",
         "Created": "2026-09-29 16:35:28", "Text": "Installed header"},
        {"ID": "LOG-2", "ProjectID": "P", "Date": "2026-09-29", "Author": "campo000",
         "Created": "2026-09-29 17:02:11", "Text": "Shaft wiring done"}]
DL.partes = lambda pid, autor=None, dia=None: [dict(r) for r in LOGS]
DL.dias_cubiertos = lambda pid: 2
clock.today = lambda grupo=None: _dt.date(2026, 9, 29)
DLU.render_admin("P", "cliente1")
'''
at = AppTest.from_string(APP_DL, default_timeout=90).run()
_md = " | ".join(m.value for m in at.markdown)
chk("de otro día: «2026-09-29 16:35», sin «:28»",
    "2026-09-26 · campo000 · 2026-09-29 16:35" in _md and "16:35:28" not in _md, _md[:300])
chk("del mismo día: solo la hora", "2026-09-29 · campo000 · 17:02" in _md
    and "17:02:11" not in _md, _md[:300])

# ═════════════════════════════════════════════════════════════════
sec("5. La caja del asistente, en el idioma base y por `t()`")
_a = ast.parse(io.open("app.py", encoding="utf-8").read())
_ci = [n for n in ast.walk(_a) if isinstance(n, ast.Call)
       and getattr(n.func, "attr", "") == "chat_input"]
chk("hay una caja del asistente (la sonda ve lo que busca)", len(_ci) >= 1, len(_ci))
chk("su texto va por `t()`, en inglés",
    all(n.args and isinstance(n.args[0], ast.Call) and getattr(n.args[0].func, "id", "") == "t"
        and n.args[0].args and "Ask your question" in str(getattr(n.args[0].args[0], "value", ""))
        for n in _ci), [ast.unparse(n)[:80] for n in _ci])

print("")
print("=" * 70)
if fallos:
    print("%d comprobaciones — %d FALLOS" % (n_ok + len(fallos), len(fallos)))
    for f in fallos:
        print("   · %s" % f)
    sys.exit(1)
print("%d comprobaciones — TODO OK" % n_ok)
