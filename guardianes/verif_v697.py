# -*- coding: utf-8 -*-
"""v697 · Ciclo 6 → mejoras 3/3 (sin D1, que va aparte): cifras y pantallas (22/11).
- H18 · Home: «2d behind» / «2d ahead» en palabras, y «N behind» solo de las ACTIVAS;
- H19 · una etapa ya empezada no es «Next milestone … starts on»;
- H23 · con menos de un 10 % de avance no se proyecta el coste al terminar (salvo gasto ya por encima del presupuesto);
- H7 · Progress enseña el peso de cada actividad DENTRO de esta obra (suma 100);
- H20 · el cumplimiento por nombre; H24 · el recibo dice quién lo cargó;
- H2 · «Head installer/s» con la cuadrilla primero y los demás marcados; H3 · Assign: la cuadrilla primero, «nadie
  tiene X» antes de elegir, y asignar a quien no cumple se dice;
- y lo visto verificando v696: el aviso flotante, más estrecho y por encima del menú lateral.

Nada sale a la red ni escribe: sustitutos y AppTest.
"""
import ast
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


def _sustituir(obj, **kw):
    viejo = {k: getattr(obj, k) for k in kw}
    for k, v in kw.items():
        setattr(obj, k, v)
    return lambda: [setattr(obj, k, v) for k, v in viejo.items()]


def _fuente(rel):
    return open(os.path.join(RAIZ, rel), encoding="utf-8").read()


def _func(rel, nombre):
    return next((n for n in ast.walk(ast.parse(_fuente(rel)))
                 if isinstance(n, ast.FunctionDef) and n.name == nombre), None)


from streamlit.testing.v1 import AppTest                                   # noqa: E402
from core import projects as P, projects_ui as PU, alerts, theme           # noqa: E402

# ═════════════════════════════════════════════════════════════════
print("1. H18 · Home y la tarjeta de activas")
_pr = [{"ID": "P1", "Name": "Behind job", "Status": "In progress", "Progress": "40"},
       {"ID": "P2", "Name": "Ahead job", "Status": "In progress", "Progress": "3"},
       {"ID": "P9", "Name": "Old job", "Status": "Completed", "Progress": "100"}]
_rr = [_sustituir(P, list_projects=lambda grupo=None, agrupacion_id=None, incluir_archivados=False, incluir_internos=False:
                  [dict(p) for p in _pr], project_hours_bulk=lambda g: {},
                  delays_of_group=lambda g: {"P1": 3.0, "P9": 36.0}, aheads_of_group=lambda g: {"P2": 2.0},
                  es_activa=lambda p: p.get("Status") == "In progress"),
       _sustituir(alerts, is_configured=lambda: False)]
_k = PU._kpis("G")
chk("_kpis: «behind» cuenta solo las ACTIVAS (P1; no P9, que no lo está)", _k["riesgo"] == 1 and _k["activos"] == 2, _k)
chk("…y el pie dice «1 behind», no «all 2 behind»", PU._kpi_pies(_k)[0] == "1 behind", PU._kpi_pies(_k))
for _x in _rr:
    _x()
HOME = r'''
import streamlit as st
from core import home_ui as H, projects as P, alerts
_pr = [{"ID": "P1", "Name": "Behind job", "Status": "In progress", "Progress": "40"},
       {"ID": "P2", "Name": "Ahead job", "Status": "In progress", "Progress": "3"}]
P.list_projects = lambda grupo=None, agrupacion_id=None, incluir_archivados=False, incluir_internos=False: [dict(p) for p in _pr]
P.es_activa = lambda p: True
P.delays_of_group = lambda g: {"P1": 3.0}
P.aheads_of_group = lambda g: {"P2": 2.0}
alerts.is_configured = lambda: False
H._proyectos_home("G")
'''
at = AppTest.from_string(HOME, default_timeout=60).run()
_lb = [str(b.label) for b in at.button]
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("Home: «Behind job · 40% · … 3d behind» y «Ahead job · 3% · … 2d ahead»",
    any("Behind job" in x and "3d behind" in x for x in _lb) and any("Ahead job" in x and "2d ahead" in x for x in _lb), _lb)

# ═════════════════════════════════════════════════════════════════
print("2. H19 · el próximo hito no es una etapa ya empezada")
_sched = {"activities": [{"nombre": "Set Up", "inicio": 0, "duracion": 2, "orden": 1},
                         {"nombre": "Prepping", "inicio": 2, "duracion": 1, "orden": 2},
                         {"nombre": "Plumbing", "inicio": 3, "duracion": 2, "orden": 3}],
          "total_dias": 5, "start_date": date(2026, 11, 22)}
_d = PU._diagnostico({"sched": _sched, "avances": [85, 24, 0], "owners": [], "proj": {}, "today_day": 0})
chk("con Prepping al 24 %, el hito es Plumbing", _d["proximo"] and _d["proximo"]["nombre"] == "Plumbing", _d["proximo"])
_d = PU._diagnostico({"sched": _sched, "avances": [85, 0, 0], "owners": [], "proj": {}, "today_day": 0})
chk("…con Prepping a 0, es Prepping (como siempre)", _d["proximo"] and _d["proximo"]["nombre"] == "Prepping", _d["proximo"])

# ═════════════════════════════════════════════════════════════════
print("3. H23 · sin proyección con muy poco avance")
chk("AVANCE_MIN_PROYECCION = 10", PU.AVANCE_MIN_PROYECCION == 10)
COST = r'''
import streamlit as st
from core import projects_ui as PU, projects as P, expenses as E
P.get_project = lambda pid: {"ID": pid, "Progress": st.session_state["_AV"], "Type": "Installation"}
P.es_interno = lambda prj: False
E.cost_projection = lambda pid, g: {"presupuesto": 40000.0, "proyectado": 1980.0, "total": st.session_state["_TOT"],
                                     "compras": 48.0, "mano_obra": 15.0}
E.labor_breakdown = lambda pid, g: {"items": [], "horas": 0}
PU._margen_section = lambda *a, **k: None
try:
    PU._costos_section("PRJ-47", "G", [], False, "k")
except Exception as e:
    st.session_state["_ERR"] = repr(e)
'''
at = AppTest.from_string(COST, default_timeout=60)
at.session_state["_AV"], at.session_state["_TOT"] = "3", 63.35
at.run()
_txt = " ".join(str(x.value) for x in list(at.info) + list(at.success) + list(at.error))
chk("con un 3 %: «Too early to project the cost: $63 spent so far with 3% progress…» y no «within the budget»",
    "Too early to project the cost" in _txt and "within the budget" not in _txt, (_txt[:300],
                                                                                   at.session_state["_ERR"] if "_ERR" in at.session_state else ""))
at = AppTest.from_string(COST, default_timeout=60)
at.session_state["_AV"], at.session_state["_TOT"] = "25", 63.35
at.run()
_txt = " ".join(str(x.value) for x in list(at.info) + list(at.success) + list(at.error))
chk("con un 25 %: la proyección de siempre («within the budget»)", "within the budget" in _txt, _txt[:300])
at = AppTest.from_string(COST, default_timeout=60)
at.session_state["_AV"], at.session_state["_TOT"] = "3", 45000.0
at.run()
_txt = " ".join(str(x.value) for x in list(at.info) + list(at.success) + list(at.error))
chk("con un 3 % pero el gasto ya por ENCIMA del presupuesto: no se esconde («Too early» no sale)",
    "Too early to project the cost" not in _txt, _txt[:300])

# ═════════════════════════════════════════════════════════════════
print("4. H7 · Progress: el peso dentro de ESTA obra")
SPG = r'''
import streamlit as st
from core import stage_progress_ui as SPU, stage_progress as SP
SP.is_configured = lambda: True
SP.version_desfasada = lambda prj: ""
SP.creditos = lambda pid, etapa=None: []
SP.detalle = lambda pid, prj: [{"orden": 1, "nombre": "Set Up", "pct": 0, "informativas": [],
                                "actividades": [{"nombre": "Receive toolbox", "peso_en_etapa": 6, "pct": 0},
                                                {"nombre": "Resto", "peso_en_etapa": 88, "pct": 0}]}]
st.session_state.setdefault("auth", {"usuario": "campo000"})
SPU.render("PRJ-T", "G", {"ID": "PRJ-T"}, key_prefix="fld")
'''
at = AppTest.from_string(SPG, default_timeout=60).run()
_lb = [str(c.label) for c in at.checkbox]
chk("«Receive toolbox · 6.4%» (6 de 94), no «6.0%»: los de la etapa suman 100",
    any(x.startswith("Receive toolbox") and "6.4%" in x for x in _lb)
    and any(x.startswith("Resto") and "93.6%" in x for x in _lb), _lb)

# ═════════════════════════════════════════════════════════════════
print("5. H20 · el cumplimiento por nombre; H24 · quién cargó el recibo; H2 · head installer")
CUM = r'''
import streamlit as st
from core import projects_ui as PU, credentials
credentials.compliance = lambda u, req: {"cumple": u != "helper 1", "por_tipo": {r: "vigente" for r in req}}
PU._etq_us = lambda us: {"campo000": "hjg,ujgjg", "helper 1": "helper 1"}
PU._cumplimiento_equipo("PRJ-47", "G", {"RequiredCerts": "Working at Heights", "FieldAssigned": "campo000;helper 1"})
'''
at = AppTest.from_string(CUM, default_timeout=60).run()
_df = at.dataframe[0].value if at.dataframe else None
chk("la tabla dice «hjg,ujgjg» (el nombre), no «campo000»",
    _df is not None and list(_df["User"]) == ["hjg,ujgjg", "helper 1"], None if _df is None else list(_df["User"]))
_cs = ast.unparse(_func("core/projects_ui.py", "render_expenses"))       # la lista de recibos vive aquí
chk("el recibo: «· by NOMBRE» con quien lo cargó (`CreatedBy`)",
    "_por = str(r.get('CreatedBy', '') or '').strip()" in _cs and "t('by {x}'" in _cs)
_src = _fuente("core/projects_ui.py")
chk("al crear: la cuadrilla primero y los demás «not in the crew»",
    "_hi = [u for u in campos if u in (asg or [])] + [u for u in campos if u not in (asg or [])]" in _src
    and 't("not in the crew")' in _src)
chk("…y al editar, igual", "_cmp_ed = [u for u in _cmp_ed if u in (asignados or [])]" in _src)

# ═════════════════════════════════════════════════════════════════
print("6. H3 · Assign")
_ai = ast.unparse(_func("core/roster_ui.py", "_asignacion_inteligente"))
chk("la cuadrilla primero (antes que «cumple»)", "libres.sort(key=lambda f: (0 if f['usr'] in _crew else 1, 0 if f['cumple'] else 1, f['nom']))" in _ai, _ai[:200])
chk("«Nobody in the company holds a valid …» antes de elegir",
    "Nobody in the company holds a valid {c}" in _ai and "_nadie = [c for c in certs if not any(" in _ai)
chk("la etiqueta dice «crew»", "t('crew') if f['usr'] in _crew" in _ai)
chk("asignar a quien no cumple se dice («Assigned without …»)", "Assigned without {c}: {who}." in _ai
    and _ai.find("Assigned without") > _ai.find("_hechos.append"))

# ═════════════════════════════════════════════════════════════════
print("7. El aviso flotante, entero (lo visto verificando v696)")
_css = theme._CSS
_i = _css.find(".st-key-cpx_flash {")
_b = _css[_i:_css.find("}", _i)]
chk("480 px como mucho", "width: min(480px, calc(100vw - 32px)) !important" in _b, _b)
chk("y por ENCIMA del menú lateral (999991)", "z-index: 1000000" in _b, _b)

print()
print("verif_v697: %d FALLOS" % len(FALLOS) if FALLOS else "verif_v697: TODO OK")
sys.exit(1 if FALLOS else 0)
