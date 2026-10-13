# -*- coding: utf-8 -*-
"""v563 · GROUPINGS, PROBADA ACCIÓN POR ACCIÓN (decisión del usuario: «dale con todo»).

  1. ⚠️ «Delete group» no desagrupaba: sus ascensores se quedaban con el GroupingID de una
     agrupación borrada (visto en la hoja). Ahora el motor desagrupa ANTES y, si falla, no borra.
  2. ⚠️ Tras crear, el formulario seguía con el nombre y las obras marcadas → se vacía.
  3. Cabeceras del editor: sin `:material/…:` literal ni «In the grou…».
  4. «HOURS 0» con 0,45 h → un decimal.   5. Tarjetas en REJILLA (no se estira la última).
  6. Tabla: $, DD/MM/YYYY, ascensor fijado, prioridad.   7. Fuera la gráfica de barras.
  8. Curva S con el lenguaje de la ficha (naranja/verde, HOY, %, DD/MM).
  9. Tarjeta: «2 lifts», DD/MM/YYYY, una por fila si hay una sola.   10. Textos con `t()`.
 11. `&g=` en la URL.   12. «No changes to save.» neutro y sin escribir.
 13. Sin agrupaciones, «New group of lifts» abierto.
 +  El menú: tocar la sub-pestaña en la que estás cierra la obra/agrupación abierta.

AppTest y el motor con sus dependencias sustituidas: ninguna hoja se toca.
"""
import ast
import io
import os
import re
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
fallos, n_ok = [], 0


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("  ok   " + q)
    else:
        fallos.append(q)
        print("  FALLO " + q + (("  -> " + str(det)) if det != "" else ""))


def _desplegables(at):
    """Desplegables del árbol. ⚠️ AppTest clasifica un `st.expander` CON icono como `Status`
    (no `Expander`): buscar solo en `at.expander` no lo encuentra (medido)."""
    return list(at.expander) + list(at.status)


# ══════════════════════════════════════════════════════════════════════════════
print("1. ⚠️ El motor: borrar una agrupación DESAGRUPA sus ascensores")
from core import projects as P                                             # noqa: E402
_orig = {n: getattr(P, n) for n in ("_groupings_ws", "_find_row", "list_projects", "update_project")}


class _WS:
    def __init__(self):
        self.borradas = []

    def delete_rows(self, r):
        self.borradas.append(r)


_MIEMB = [{"ID": "PRJ-1", "GroupingID": "AGR-9", "WeightInGrouping": "1"},
          {"ID": "PRJ-2", "GroupingID": "AGR-9", "WeightInGrouping": "2"}]
try:
    for _falla in (False, True):
        ws, escritos = _WS(), []
        P._groupings_ws = lambda: (ws, None)
        P._find_row = lambda w, col, val: 3
        P.list_projects = lambda *a, **k: [dict(x) for x in _MIEMB] if k.get("agrupacion_id") == "AGR-9" else []

        def _upd(pid, campos, _f=_falla):
            escritos.append((pid, dict(campos)))
            return (False, "boom") if _f else (True, "")
        P.update_project = _upd
        ok, msg = P.delete_grouping("AGR-9", "G")
        if not _falla:
            chk("⚠️ desagrupa los DOS ascensores (GroupingID vacío, peso 0)",
                sorted(escritos) == [("PRJ-1", {"GroupingID": "", "WeightInGrouping": 0}),
                                     ("PRJ-2", {"GroupingID": "", "WeightInGrouping": 0})], escritos)
            chk("…y DESPUÉS borra la fila de la agrupación", ws.borradas == [3], ws.borradas)
            chk("el mensaje lo dice («2 lift(s) ungrouped»)", ok and "2 lift(s) ungrouped" in msg, msg)
        else:
            chk("⚠️ si desagrupar falla, la agrupación NO se borra (no deja huérfanos)",
                not ok and ws.borradas == [], (ok, ws.borradas))
finally:
    for n, f in _orig.items():
        setattr(P, n, f)

from streamlit.testing.v1 import AppTest                                    # noqa: E402

CAB = r'''
import datetime as dt
import streamlit as st
from core import projects_ui as PU, projects as P, alerts, expenses as E
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G",
                                     "nombre": "Jefa"})
_hoy = dt.date(2026, 10, 12)
_pr = [{"ID": "PRJ-1", "Name": "Lift A", "Status": "In progress", "Progress": "40",
        "WeightInGrouping": "1", "GroupingID": "AGR-9", "Group": "G"},
       {"ID": "PRJ-2", "Name": "Lift B", "Status": "Planned", "Progress": "0",
        "WeightInGrouping": "2", "GroupingID": "AGR-9", "Group": "G"}]
P.list_projects = lambda *a, **k: [dict(x) for x in _pr]
P.grouping_progress = lambda gid: {"avance": 13.3, "n_proyectos": 2}
P.delays_of_group = lambda g: {"PRJ-2": 13.0}
P.aheads_of_group = lambda g: {}
P.project_hours_bulk = lambda g: {"PRJ-1": 0.24, "PRJ-2": 0.21}
alerts.is_configured = lambda: True
alerts.open_counts_all = lambda: {}
P.grouping_projection = lambda gid, g: {
    "fecha": dt.date(2026, 11, 9), "critico": "Lift B", "critico_id": "PRJ-2", "sin_datos": [],
    "detalle": [{"id": "PRJ-1", "fecha": dt.date(2026, 10, 29)},
                {"id": "PRJ-2", "fecha": dt.date(2026, 11, 9)}]}
P.projections_by_group = lambda g: {"PRJ-2": {"fecha": dt.date(2026, 11, 9), "gap": 13.0}}
E.is_configured = lambda: True
E.project_cost = lambda pid, g: {"total": 132.55 if pid == "PRJ-1" else 3.15, "presupuesto": 21000}
_f = [dt.date(2026, 9, 7) + dt.timedelta(days=i * 5) for i in range(12)]
P.grouping_curve = lambda gid, g: {"fechas": _f, "plan": [min(100, i * 9) for i in range(12)],
                                   "real": [0.0 if d <= _hoy else None for d in _f], "hoy": _hoy}
st.session_state.setdefault("_LLAMADAS", [])
def _set(gid, sel, g):
    st.session_state["_LLAMADAS"].append(("set", gid, dict(sel)))
    return True, "2 project(s) updated."
P.set_grouping_members = _set
def _del(gid, g=None):
    st.session_state["_LLAMADAS"].append(("del", gid, g))
    return True, "Grouping deleted; 2 lift(s) ungrouped."
P.delete_grouping = _del
def _crea(g, n, d):
    st.session_state["_LLAMADAS"].append(("crea", n))
    return True, "AGR-10"
P.create_grouping = _crea
'''

# ══════════════════════════════════════════════════════════════════════════════
print("\n2. El tablero de una agrupación")
G_DASH = CAB + r'''
PU._dashboard_agrupacion({"ID": "AGR-9", "Name": "Test"}, "G")
'''
at = AppTest.from_string(G_DASH, default_timeout=90)
at.run()
chk("⚠️ el tablero se pinta sin excepción (con `theme` al alcance)", not at.exception,
    [e.value for e in at.exception][:1])
_html = " ".join(m.value for m in at.markdown)
chk("⚠️ «Hours» con un decimal (0,45 h no es «0»)", re.search(r">0\.[45] h<", _html) is not None,
    re.findall(r"HOURS|Hours.{0,80}", _html)[:1])
chk("⚠️ tarjetas en REJILLA con `auto-fill` (la última no se estira)",
    "display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr))" in _html)
chk("el coste total sale «$136»", ">$136<" in _html)
_cap = " ".join(c.value for c in at.caption)
chk("presupuesto con su importe y su % («42,000» · «1% used»)", "42,000" in _cap and "% used" in _cap, _cap)
_charts = at.get("vega_lite_chart")
chk("⚠️ UNA sola gráfica (la de barras, fuera)", len(_charts) == 1, len(_charts))
_spec = _charts[0].proto.spec if _charts else ""
chk("⚠️ curva S: plan naranja y real verde, como la de la ficha",
    "#BA7517" in _spec and "#1e8449" in _spec, _spec[:200])
chk("…con el eje en DD/MM, el % y la línea de HOY",
    "%d/%m" in _spec and "'%'" in _spec and "TODAY" in _spec)
chk("la leyenda en inglés («Planned» / «Actual»; antes la vigilaba romper_v452)",
    '"Planned"' in _spec and '"Actual"' in _spec and "Planificado" not in _spec)
_df = at.dataframe[0] if at.dataframe else None
chk("se pinta la tabla comparativa", _df is not None)
if _df is not None:
    _v = _df.value
    chk("⚠️ entrega con AÑO («29/10/2026»)", list(_v["Entrega prev."]) == ["29/10/2026", "09/11/2026"],
        list(_v["Entrega prev."]))
    chk("el ascensor va PRIMERO y el avance después (prioridad)", list(_v.columns)[:3] == ["Elevador", "Avance %", "Pace"],
        list(_v.columns))
    _cfg = _df.proto.columns.replace(" ", "")
    chk("⚠️ el ascensor queda FIJADO", re.search(r'"Elevador":\{[^}]*"pinned":true', _cfg) is not None, _cfg[:300])
    chk("⚠️ el coste con $ («$%,.2f»)", '"Cost":{' in _cfg and "$%,.2f" in _cfg, _cfg[:300])
    chk("el avance como BARRA dentro de la tabla", '"type_config":{"type":"progress"' in _cfg.replace(" ", "")
        or '"progress"' in _cfg, _cfg[:300])

# ══════════════════════════════════════════════════════════════════════════════
print("\n3. La lista y el alta")
G_LISTA = CAB + r'''
P.list_groupings = lambda grupo=None: [{"ID": "AGR-9", "Name": "Test", "Group": "G"}]
PU._panel_agrupaciones("G")
'''
at = AppTest.from_string(G_LISTA, default_timeout=90)
at.run()
chk("la lista se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_b = [b for b in at.button if b.key == "agrc_0"]
_lbl = _b[0].label if _b else ""
chk("⚠️ la tarjeta dice «2 lifts» (no «elev») y la fecha con año", "2 lifts" in _lbl and "elev" not in _lbl
    and "09/11/2026" in _lbl, _lbl)
chk("con UNA sola agrupación, una tarjeta por fila (a todo el ancho)", len(at.columns) == 1, len(at.columns))
chk("con agrupaciones, «New group of lifts» empieza plegado",
    [e.proto.expanded for e in _desplegables(at) if "New group" in e.proto.label] == [False],
    [(e.proto.label, e.proto.expanded) for e in _desplegables(at)])
chk("la regla de una por fila si no caben dos (`@container`)",
    any("@container (max-width:620px){.st-key-cpx_agr_cartas" in m.value for m in at.markdown))

G_ALTA = CAB + r'''
P.list_groupings = lambda grupo=None: []
# v570 · los avisos ANTES de la sección, como la shell (ver verif_v569/v570)
from core import flash
flash.mostrar()
PU._panel_agrupaciones("G")
'''
at = AppTest.from_string(G_ALTA, default_timeout=90)
at.run()
chk("sin agrupaciones se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("⚠️ sin agrupaciones, «New group of lifts» empieza ABIERTO",
    [e.proto.expanded for e in _desplegables(at) if "New group" in e.proto.label] == [True],
    [(e.proto.label, e.proto.expanded) for e in _desplegables(at)])
_ed = [d for d in at.get("arrow_data_frame")] if False else None
at.text_input(key="nueva_agr_nom").set_value("Nueva")
[b for b in at.button if b.key == "nueva_agr_btn"][0].click()
at.run()
chk("se crea («crea Nueva»)", ("crea", "Nueva") in at.session_state["_LLAMADAS"], at.session_state["_LLAMADAS"])
chk("⚠️ tras crear, el formulario nace VACÍO (otra generación de claves)",
    at.session_state["_agr_new_gen"] == 1 and at.text_input(key="nueva_agr_nom_1").value == "")
chk("el aviso lo dice («Grouping created (AGR-10)»)",
    any("Grouping created (AGR-10)" in s.value for s in at.success), [s.value for s in at.success])

# ══════════════════════════════════════════════════════════════════════════════
print("\n4. Una agrupación abierta: miembros y borrado")
G_ABIERTA = CAB + r'''
P.list_groupings = lambda grupo=None: [{"ID": "AGR-9", "Name": "Test", "Group": "G"}]
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    st.session_state["_admin_open_agr"] = "AGR-9"
# v570 · los avisos ANTES de la sección, como la shell (ver verif_v569/v570)
from core import flash
flash.mostrar()
PU._panel_agrupaciones("G")
'''
at = AppTest.from_string(G_ABIERTA, default_timeout=90)
at.run()
chk("se abre sin excepción", not at.exception, [e.value for e in at.exception][:1])
[b for b in at.button if b.key == "agmemsave_AGR-9"][0].click()
at.run()
chk("⚠️ guardar SIN cambios no escribe nada", not [x for x in at.session_state["_LLAMADAS"] if x[0] == "set"],
    at.session_state["_LLAMADAS"])
chk("…y lo dice en un aviso NEUTRO (no verde)",
    any("No changes to save." in i.value for i in at.info) and not any("No changes" in s.value for s in at.success),
    ([i.value for i in at.info], [s.value for s in at.success]))
at.checkbox(key="del_agr_ok").check()
at.run()
[b for b in at.button if b.key == "del_agr_btn"][0].click()
at.run()
chk("⚠️ «Delete group» llama al motor CON el grupo (para desagrupar)",
    ("del", "AGR-9", "G") in at.session_state["_LLAMADAS"], at.session_state["_LLAMADAS"])
chk("…y vuelve a la lista", "_admin_open_agr" not in at.session_state)

print("\n5. Cabeceras del editor y textos")
PUS = io.open(os.path.join(RAIZ, "core", "projects_ui.py"), encoding="utf-8").read()
_t = ast.parse(PUS)
_me = next(n for n in ast.walk(_t) if isinstance(n, ast.FunctionDef) and n.name == "_miembros_editor")
_src = ast.unparse(_me)
chk("⚠️ ninguna cabecera con `:material/` (las tablas lo pintan literal)", ":material/" not in _src)
chk("«In group» como cabecera de la casilla (no «In the grou…»)", "CheckboxColumn(t('In group')" in _src)
_lit = []
for fn in ("_dashboard_agrupacion", "_cartera_agrupaciones", "_panel_agrupaciones"):
    _f = next(n for n in ast.walk(_t) if isinstance(n, ast.FunctionDef) and n.name == fn)
    for n in ast.walk(_f):
        if isinstance(n, ast.Call) and ast.unparse(n.func) in ("st.caption", "st.warning", "st.spinner",
                                                                "st.markdown", "flash.exito", "flash.aviso"):
            for a in n.args[:1]:
                if isinstance(a, ast.JoinedStr) or (isinstance(a, ast.Constant) and isinstance(a.value, str)
                                                     and re.search(r"[A-Za-z]{4}", a.value)
                                                     and not a.value.lstrip().startswith("<")):
                    _lit.append("%s:%d %s" % (fn, n.lineno, ast.unparse(a)[:60]))
chk("⚠️ textos de Groupings con `t()` (sin literales ni f-strings sueltos)", not _lit, _lit)

# ══════════════════════════════════════════════════════════════════════════════
print("\n6. La URL y el menú")
G_URL = r'''
import streamlit as st
from core import home_ui
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G"})
st.session_state["adm_proy_sub"] = st.session_state.get("_SUB", "🗂 Agrupaciones")
if st.session_state.get("_AGR"):
    st.session_state["_admin_open_agr"] = st.session_state["_AGR"]
if st.session_state.get("_PRJ"):
    st.session_state["_admin_open_proj"] = st.session_state["_PRJ"]
home_ui._estado_a_url("proyectos")
'''
at = AppTest.from_string(G_URL, default_timeout=60)
at.session_state["_AGR"] = "AGR-9"
at.session_state["_PRJ"] = "PRJ-1"
at.run()
_q = {k: (v[0] if isinstance(v, list) else v) for k, v in dict(at.query_params).items()}
chk("⚠️ con una agrupación abierta, la URL lleva g=AGR-9", _q.get("g") == "AGR-9", _q)
chk("…y no un `&p=` de una obra abierta antes (no pinta en Groupings)", "p" not in _q, _q)
at = AppTest.from_string(G_URL, default_timeout=60)
at.session_state["_SUB"] = "📊 Proyectos"
at.session_state["_PRJ"] = "PRJ-1"
at.session_state["_AGR"] = "AGR-9"
at.run()
_q = {k: (v[0] if isinstance(v, list) else v) for k, v in dict(at.query_params).items()}
chk("en la lista de obras sigue `&p=` (y sin `&g=`)", _q.get("p") == "PRJ-1" and "g" not in _q, _q)

G_URL2 = r'''
import streamlit as st
from core import home_ui
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G"})
home_ui._url_a_estado()
'''
at = AppTest.from_string(G_URL2, default_timeout=60)
at.query_params["s"] = "proyectos"
at.query_params["t"] = "agrupaciones"
at.query_params["g"] = "AGR-9"
at.run()
chk("⚠️ un enlace con `&g=` abre esa agrupación", at.session_state["_admin_open_agr"] == "AGR-9"
    if "_admin_open_agr" in at.session_state else False)

G_MENU = r'''
import streamlit as st
from core import home_ui
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G"})
_lbl = dict(home_ui._secciones())["proyectos"]
st.session_state.setdefault("admin_nav", _lbl)
st.session_state.setdefault("_admin_expanded", "proyectos")
st.session_state.setdefault("adm_proy_sub", "🗂 Agrupaciones")
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    st.session_state["_admin_open_agr"] = "AGR-9"
    st.session_state["_admin_open_proj"] = "PRJ-1"
st.session_state.setdefault("_url_leida", True)
with st.sidebar:
    home_ui.sidebar_menu()
'''
at = AppTest.from_string(G_MENU, default_timeout=60)
at.run()
chk("el menú se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_sub = [b for b in at.button if b.key == "navsub_proyectos_1"]
chk("se localiza «Groupings» en el menú", len(_sub) == 1)
if _sub:
    _sub[0].click()
    at.run()
    chk("⚠️ tocar «Groupings» estando en Groupings CIERRA la agrupación abierta",
        "_admin_open_agr" not in at.session_state)
    chk("…y no toca la obra abierta en la otra sub-pestaña", "_admin_open_proj" in at.session_state)

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("TODO OK")
