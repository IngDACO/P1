# -*- coding: utf-8 -*-
"""v558 · PROJECTS → la cartera y el alta «New project», probadas acción por acción.

Recorrido en producción (10/10/2026, cuenta admin, 1024 px). Lo arreglado («Dale»):
  1. ⚠️ La columna «Pace» no salía: v444 dejó «Situación» y «Estado» las dos como
     «Status» y en un dict la segunda PISA a la primera. Lo mismo en la comparativa de
     Agrupaciones. + barrido de TODA la app: ningún dict literal con una clave repetida.
  2. ⚠️ Una obra con nombre repetido no se podía crear NUNCA (la casilla «Create even
     though…» desaparecía al marcarla y su valor con ella).
  3. ⚠️ «Estimated finish» dentro del form: no se movía al cambiar NS o inicio.
  4. ⚠️ Crear un Delivery u Other ESCRIBÍA la obra y reventaba (`sched` sin definir).
  5. Tras crear: se abre la obra nueva, avisos por flash y el alta vuelve a nacer vacía.
  6. Tarjetas: «\\$133» con la barra, «33.0d», «ppto»/«s/ppto».
  7. «Invoice» sin fichas en Contacts era un callejón → nombre del cliente + botón.
  8. Mapa: «:material/search:» literal en el buscador, 500 px fijos, aviso perdido.
  9. Selectores segmentados, «All types», contadores activos que cuentan lo que se ve,
     vista y filtros recordados al volver (`persist_state="session"`), «Clear filters».
 10. Home: «Go to Projects» de un indicador abre la cartera con lo que se tocó.
 11. Fechas del alta en DD/MM/YYYY; `return` en vez de `st.stop()`.

AppTest con datos inventados; ninguna hoja se toca (crear, listar, avisos… sustituidos).
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


def ok(q):
    global n_ok
    n_ok += 1
    print("  ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("  FALLO %s%s" % (q, ("  -> " + str(det)) if det != "" else ""))


def chk(q, cond, det=""):
    (ok(q) if cond else fallo(q, det))


def fuente(rel):
    return io.open(os.path.join(RAIZ, rel), encoding="utf-8").read()


def funcs(src):
    return {n.name: n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef)}


def kw(call, nombre):
    for k in call.keywords:
        if k.arg == nombre:
            return k.value
    return None


def es_llamada(n, attr):
    return (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == attr)


# ══════════════════════════════════════════════════════════════════════════════
print("0. Estático")
# ── (a) ningún dict literal con una clave repetida, en TODA la app ──
_rep = []
_n_dicts = 0
for d, _, fs in os.walk(RAIZ):
    if any(x in d for x in (".git", "__pycache__", ".venv")):
        continue
    for f in fs:
        if f.endswith(".py"):
            p = os.path.join(d, f)
            for nd in ast.walk(ast.parse(io.open(p, encoding="utf-8").read())):
                if isinstance(nd, ast.Dict):
                    _n_dicts += 1
                    _vis = set()
                    for k in nd.keys:
                        if isinstance(k, ast.Constant):
                            if k.value in _vis:
                                _rep.append("%s:%d %r" % (os.path.relpath(p, RAIZ), k.lineno, k.value))
                            _vis.add(k.value)
chk("se recorren los dicts de la app (%d)" % _n_dicts, _n_dicts > 500, _n_dicts)
chk("⚠️ ningún dict literal con una clave REPETIDA (la 2ª pisa a la 1ª en silencio)",
    not _rep, _rep)

PUS = fuente(os.path.join("core", "projects_ui.py"))
FN = funcs(PUS)
# ── (b) el alta: NS y fechas FUERA del form; sin st.stop; DD/MM/YYYY ──
_np = FN.get("_nuevo_proyecto_form")
chk("existe `_nuevo_proyecto_form`", _np is not None)
_form = [w for w in ast.walk(_np) if isinstance(w, ast.With)
         and any(es_llamada(i.context_expr, "form") for i in w.items)]
chk("el alta tiene su `st.form`", len(_form) == 1, len(_form))
_dentro = {id(n) for w in _form for n in ast.walk(w)}
_ns = [n for n in ast.walk(_np) if es_llamada(n, "number_input")
       and isinstance(kw(n, "key"), ast.JoinedStr) and "np_ns_" in ast.unparse(kw(n, "key"))]
chk("se localiza el NS", len(_ns) == 1, len(_ns))
chk("⚠️ el NS va FUERA del form (si no, la fecha estimada no se mueve)",
    _ns and id(_ns[0]) not in _dentro)
_di = [n for n in ast.walk(_np) if es_llamada(n, "date_input")]
chk("dos fechas en el alta (inicio y fin manual)", len(_di) == 2, len(_di))
chk("⚠️ las fechas del alta FUERA del form", all(id(n) not in _dentro for n in _di))
chk("las fechas del alta en DD/MM/YYYY",
    all(isinstance(kw(n, "format"), ast.Constant) and kw(n, "format").value == "DD/MM/YYYY"
        for n in _di))
_stop = [n for n in ast.walk(_np) if es_llamada(n, "stop")]
chk("el alta no usa `st.stop()`", not _stop)
_sched = [n for n in ast.walk(_np) if isinstance(n, ast.Name) and n.id == "sched"]
_fuera_if = []
for n in ast.walk(_np):
    if isinstance(n, ast.If) and "_es_inst" in ast.unparse(n.test):
        _fuera_if += [id(x) for x in ast.walk(n.body[0])] if False else [id(x) for b in n.body for x in ast.walk(b)]
chk("⚠️ `sched` solo se usa en la rama de instalación (Delivery reventaba)",
    _sched and all(id(x) in _fuera_if for x in _sched), len(_sched))
# ── (c) el mapa ──
LUI = fuente(os.path.join("core", "location_ui.py"))
_fol = [n for n in ast.walk(ast.parse(LUI)) if isinstance(n, ast.Call)
        and getattr(n.func, "id", "") == "st_folium"]
chk("el mapa del alta a lo ancho (`use_container_width=True`)",
    len(_fol) == 1 and isinstance(kw(_fol[0], "use_container_width"), ast.Constant)
    and kw(_fol[0], "use_container_width").value is True)
# barrido: ningún `placeholder` con un icono (no los interpreta)
_ph = []
for d, _, fs in os.walk(RAIZ):
    if any(x in d for x in (".git", "__pycache__", ".venv")):
        continue
    for f in fs:
        if f.endswith(".py"):
            for n in ast.walk(ast.parse(io.open(os.path.join(d, f), encoding="utf-8").read())):
                if isinstance(n, ast.Call):
                    v = kw(n, "placeholder")
                    if v is not None and ":material/" in ast.unparse(v):
                        _ph.append("%s:%d" % (f, n.lineno))
chk("⚠️ ningún `placeholder` con «:material/…:» (sale literal)", not _ph, _ph)
# ── (d) la cartera ──
_pp = ast.unparse(FN["_panel_proyectos"])
for k in ("cpxseg_cart_filt", "cpxseg_cart_view"):
    chk("selector segmentado: clave «%s»" % k, k in _pp)
_persist = [n for n in ast.walk(FN["_panel_proyectos"]) if isinstance(n, ast.Call)
            and isinstance(kw(n, "persist_state"), ast.Constant)
            and kw(n, "persist_state").value == "session"]
chk("⚠️ los 5 controles de la cartera se recuerdan (`persist_state=\"session\"`)",
    len(_persist) == 5, len(_persist))
_cc = ast.unparse(FN["_cartera_clickeable"])
chk("las tarjetas usan `dinero_html` (HTML), no `dinero` (escapado)",
    "dinero_html(" in _cc and "theme.dinero(_pf, 0)}</b>" not in _cc)
from core import theme                                                   # noqa: E402
chk("`dinero_html(133)` = «$133» sin barra", theme.dinero_html(133, 0) == "$133",
    theme.dinero_html(133, 0))
chk("…y `dinero` sigue escapado para markdown", theme.dinero(133, 0) == "\\$133")

from streamlit.testing.v1 import AppTest                                  # noqa: E402

# ══════════════════════════════════════════════════════════════════════════════
GUION_CARTERA = r'''
import streamlit as st
from core import projects as P, projects_ui as PU, alerts, expenses, invoices
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G"})
_PRJ = [
    {"ID": "PRJ-0001", "Group": "G", "Name": "PRUEBA MOVIL", "Client": "Cliente de prueba",
     "Type": "Installation", "Status": "Planned", "Progress": "0", "FieldAssigned": "a",
     "StartDate": "2026-09-07", "EndDateEst": "2026-10-02"},
    {"ID": "PRJ-0002", "Group": "G", "Name": "88 walker st", "Client": "Cairn",
     "Type": "Ripout + Installation", "Status": "Planned", "Progress": "0", "FieldAssigned": "a;b",
     "StartDate": "2026-09-20", "EndDateEst": "2026-10-25"},
    {"ID": "PRJ-0015", "Group": "G", "Name": "ZZ PRUEBA", "Client": "Cliente de prueba",
     "Type": "Installation", "Status": "Planned", "Progress": "0", "FieldAssigned": "",
     "StartDate": "2026-09-28", "EndDateEst": "2026-10-27"},
]
P.list_projects = lambda *a, **k: [dict(p) for p in _PRJ]
P.delays_of_group = lambda g: {"PRJ-0001": 33.0, "PRJ-0002": 20.0}
P.aheads_of_group = lambda g: {}
alerts.is_configured = lambda: False
expenses.group_expenses = lambda g: {"proyectos": [
    {"id": "PRJ-0001", "pct": 12.4, "presupuesto": 1000, "over": False}]}
invoices.pendiente_por_proyecto = lambda g: {"PRJ-0001": 133.0, "PRJ-0002": 134.0}
# ⚠️ AppTest corre en el MISMO proceso: sustituir la función en el módulo la deja
# sustituida para los guiones siguientes. Se guarda la de verdad para el del alta.
if not hasattr(PU, "_v558_np"):
    PU._v558_np = PU._nuevo_proyecto_form
PU._nuevo_proyecto_form = lambda *a, **k: None
if st.session_state.get("_fuera"):
    st.write("OTRA PANTALLA")
else:
    PU._panel_proyectos("G")
'''


def b(at, k):
    x = [y for y in at.button if y.key == k]
    return x[0] if x else None


def textos(at):
    return " | ".join([m.value for m in at.markdown] + [m.value for m in at.caption])


def radio(at, k):
    x = [r for r in at.radio if r.key == k]
    return x[0] if x else None


print("\n1. La cartera")
at = AppTest.from_string(GUION_CARTERA, default_timeout=90)
at.run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_df = at.dataframe[0].value if at.dataframe else None
_cols = list(_df.columns) if _df is not None else []
chk("⚠️ la Lista trae la columna «Pace»", "Pace" in _cols, _cols)
chk("…y «Status» es el ESTADO de la obra («Planned»), no el ritmo",
    _df is not None and list(_df["Status"]) == ["Planned"] * 3, _df["Status"].tolist() if _df is not None else "")
chk("el ritmo en días ENTEROS («33 d behind»)",
    _df is not None and _df["Pace"].tolist()[:2] == ["33 d behind", "20 d behind"],
    _df["Pace"].tolist() if _df is not None else "")
_sel = [s for s in at.selectbox if s.key == "cart_tipo"]
chk("el tipo dice «All types» (no «Todos»)",
    _sel and "All types" in _sel[0].options and "Todos" not in _sel[0].options,
    _sel[0].options if _sel else "")
chk("selector de filtro segmentado (cpxseg_cart_filt)", radio(at, "cpxseg_cart_filt") is not None)
chk("selector de vista segmentado (cpxseg_cart_view)", radio(at, "cpxseg_cart_view") is not None)
_bn = b(at, "cart_cnt_retraso")
chk("⚠️ «2 behind schedule» es un BOTÓN", _bn is not None and "2 behind schedule" in _bn.label,
    _bn.label if _bn else "")
_bn.click()
at.run()
chk("…que filtra Behind: «2 of 3»", radio(at, "cpxseg_cart_filt").value == "🔴 Retraso"
    and "Portfolio — 2 of 3" in textos(at), radio(at, "cpxseg_cart_filt").value)
b(at, "cart_cnt_retraso").click()
at.run()
chk("…y otro toque vuelve a All: «3 of 3»", radio(at, "cpxseg_cart_filt").value == "Todos"
    and "Portfolio — 3 of 3" in textos(at))
[s for s in at.selectbox if s.key == "cart_tipo"][0].set_value("Ripout + Installation")
at.run()
chk("⚠️ con el tipo, el contador cuenta LO QUE SE VE («1 behind», no 2)",
    "1 behind schedule" in b(at, "cart_cnt_retraso").label, b(at, "cart_cnt_retraso").label)
[s for s in at.selectbox if s.key == "cart_tipo"][0].set_value("Todos")
radio(at, "cpxseg_cart_view").set_value("🃏 Tarjetas")
at.run()
_t = textos(at)
chk("tarjetas: «$133» SIN barra", "$133" in _t and "\\$133" not in _t)
chk("tarjetas: «33 d», sin «33.0d»", " 33 d" in _t and "33.0d" not in _t)
chk("tarjetas: «12% of budget» y «no budget», sin «ppto»",
    "12% of budget" in _t and "no budget" in _t and "ppto" not in _t)

print("\n2. Recordar vista y filtros al volver")
radio(at, "cpxseg_cart_filt").set_value("🔴 Retraso")
at.run()
at.session_state["_fuera"] = True
at.run()
chk("fuera de la cartera no se pinta", not at.radio)
at.session_state["_fuera"] = False
at.run()
chk("⚠️ al volver sigue en Tarjetas", radio(at, "cpxseg_cart_view").value == "🃏 Tarjetas",
    radio(at, "cpxseg_cart_view").value)
chk("⚠️ …y con el filtro Behind", radio(at, "cpxseg_cart_filt").value == "🔴 Retraso",
    radio(at, "cpxseg_cart_filt").value)

print("\n3. Lo que pide el Home")
at.session_state["_cart_pending"] = {"solo": {"motivo": "Overdue", "ids": ["PRJ-0001"]}}
at.run()
_t = textos(at)
chk("⚠️ solo la obra del indicador: «1 of 3»", "Portfolio — 1 of 3" in _t, _t[:200])
chk("…dice de dónde viene («From Home: only **Overdue** (1)»)",
    "From Home: only **Overdue** (1)" in _t)
chk("…y empieza LIMPIO (filtro All)", radio(at, "cpxseg_cart_filt").value == "Todos")
b(at, "cart_solo_x").click()
at.run()
chk("«Show all» lo quita: «3 of 3»", "Portfolio — 3 of 3" in textos(at)
    and "_cart_solo" not in at.session_state)
at.session_state["_cart_pending"] = {"filtro": "🔴 Retraso"}
at.run()
chk("«Behind schedule» del Home abre con el filtro Behind",
    radio(at, "cpxseg_cart_filt").value == "🔴 Retraso" and "Portfolio — 2 of 3" in textos(at))
radio(at, "cpxseg_cart_filt").set_value("🟢 Adelanto")
at.run()
_bl = b(at, "cart_limpiar")
chk("sin coincidencias: botón «Clear filters»", _bl is not None
    and "No project matches the filter." in textos(at))
_bl.click()
at.run()
chk("…que deja «3 of 3»", "Portfolio — 3 of 3" in textos(at)
    and radio(at, "cpxseg_cart_filt").value == "Todos")

# ══════════════════════════════════════════════════════════════════════════════
GUION_ALTA = r'''
import datetime as dt
import streamlit as st
from core import projects as P, projects_ui as PU, clientes as C, location_ui as L, auth, clock
if not hasattr(clock, "_v558_today"):
    clock._v558_today = clock.today
clock.today = lambda *a, **k: dt.date(2026, 10, 10)
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G"})
st.session_state.setdefault("_LOG", [])
LOG = st.session_state["_LOG"]
P.list_projects = lambda *a, **k: [{"ID": "PRJ-0002", "Name": "88 walker st"}]
def _crear(**k):
    LOG.append(("crear", k.get("nombre"), k.get("tipo"), k.get("fecha_fin_est"),
                len(k.get("activities") or [])))
    return True, "PRJ-0099"
P.create_project = _crear
PU._field_users = lambda g: []
C.list_clientes = lambda g: []
if not hasattr(L, "_v558_lp"):
    L._v558_lp = L.location_picker          # el de verdad, para el guion del mapa
L.location_picker = lambda k: (None, None)
auth.list_users = lambda *a, **k: []
getattr(PU, "_v558_np", PU._nuevo_proyecto_form)("G", key=st.session_state.get("_clave", "adm"))
'''


def fin_estimada(at):
    return [c.value for c in at.caption if "Estimated finish" in c.value]


def crear(at):
    [x for x in at.button if "Create project" in str(x.label)][0].click()
    at.run()


def log(at):
    return list(at.session_state["_LOG"])


def flashes(at):
    return list(at.session_state["_flash_cola"]) if "_flash_cola" in at.session_state else []


print("\n4. El alta: fecha estimada viva")
at = AppTest.from_string(GUION_ALTA, default_timeout=90)
at.run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_f0 = fin_estimada(at)
at.number_input(key="np_ns_adm").set_value(4)
at.run()
_f1 = fin_estimada(at)
chk("⚠️ cambiar el NS mueve la fecha estimada SIN enviar", _f0 and _f1 and _f0 != _f1, (_f0, _f1))
chk("…y dice la que se va a guardar («04/11/2026 (25 days)»)",
    _f1 and "**04/11/2026** (25 days)" in _f1[0], _f1)

print("\n5. Nombre repetido")
at.text_input(key="np_nom_adm").set_value("88 Walker  St")
crear(at)
chk("avisa del duplicado", any("already exists: PRJ-0002" in w.value for w in at.warning))
_cb = [c for c in at.checkbox if str(c.key).startswith("np_dup_adm_")]
chk("⚠️ la casilla está (dentro del form)", len(_cb) == 1, [c.key for c in at.checkbox])
chk("…y no se creó nada", not log(at), log(at))
_cb[0].check()
at.run()
chk("⚠️ marcarla NO la borra (sigue ahí y marcada)",
    [c.value for c in at.checkbox if str(c.key).startswith("np_dup_adm_")] == [True])
crear(at)
chk("⚠️ con la casilla, la obra homónima SE CREA", log(at)[:1] == [("crear", "88 Walker  St", "Installation", "2026-11-04", log(at)[0][4] if log(at) else -1)],
    log(at))

print("\n6. Tras crear")
chk("⚠️ se abre la obra nueva", at.session_state["_admin_open_proj"] == "PRJ-0099"
    if "_admin_open_proj" in at.session_state else False)
chk("el aviso de éxito va por flash (sobrevive al rerun)",
    any("PRJ-0099" in str(x) for x in flashes(at)), flashes(at))
chk("⚠️ el alta vuelve a nacer VACÍA (otra generación)",
    at.session_state["_np_gen_adm"] == 1 and at.text_input(key="np_nom_adm1").value == "",
    at.session_state["_np_gen_adm"] if "_np_gen_adm" in at.session_state else "")

print("\n7. Delivery (no tiene cronograma)")
at = AppTest.from_string(GUION_ALTA, default_timeout=90)
at.run()
at.selectbox(key="np_tipo_adm").set_value("Delivery")
at.run()
at.date_input(key="np_fin_adm").set_value(__import__("datetime").date(2026, 10, 20))
at.text_input(key="np_nom_adm").set_value("Entrega")
crear(at)
chk("⚠️ crear un Delivery NO revienta", not at.exception, [e.value for e in at.exception][:1])
chk("…se escribe con su fecha de fin y 1 actividad",
    log(at) == [("crear", "Entrega", "Delivery", "2026-10-20", 1)], log(at))
chk("…y se abre", at.session_state["_admin_open_proj"] == "PRJ-0099"
    if "_admin_open_proj" in at.session_state else False)

print("\n8. Alta del propietario")
at = AppTest.from_string(GUION_ALTA, default_timeout=90)
at.session_state["_clave"] = "own"
at.run()
at.text_input(key="np_nom_own").set_value("Torre")
crear(at)
chk("el propietario: se elige la obra nueva en su selector",
    "ownerproj_sel" in at.session_state and at.session_state["ownerproj_sel"] == "G · PRJ-0099 · Torre")
chk("…y no toca el abierto del admin", "_admin_open_proj" not in at.session_state)

# ══════════════════════════════════════════════════════════════════════════════
print("\n9. Factura sin fichas en Contacts")
GUION_FAC = r'''
import streamlit as st
from core import invoices_ui as IU, clientes as C
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G"})
C.list_clientes = lambda *a, **k: []
IU._nueva_factura("G")
'''
at = AppTest.from_string(GUION_FAC, default_timeout=60)
at.session_state["_fac_nueva"] = True
at.session_state["_fac_aviso_cli"] = "Cliente de prueba"
at.session_state["_fac_prj_pending"] = "PRJ-0001"
at.run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("⚠️ dice qué cliente («**Cliente de prueba**»)",
    any("**Cliente de prueba**" in i.value for i in at.info), [i.value for i in at.info])
chk("lo que dejó el atajo NO se queda colgado",
    "_fac_aviso_cli" not in at.session_state and "_fac_prj_pending" not in at.session_state)
_bf = b(at, "fac_ir_cli")
chk("⚠️ hay un botón para crear su ficha", _bf is not None and "Cliente de prueba" in _bf.label)
_bf.click()
at.run()
_co = at.session_state["_cli_open"] if "_cli_open" in at.session_state else None
_nv = at.session_state["_admin_nav_pending"] if "_admin_nav_pending" in at.session_state else None
chk("…que abre ESE cliente en Contacts", _co == "cliente de prueba"
    and tuple(_nv or ()) == ("contactos", None), (_co, _nv, [e.value for e in at.exception][:1]))

# ══════════════════════════════════════════════════════════════════════════════
print("\n10. Home: «Go to Projects» abre lo que se tocó")
GUION_HOME = r'''
import streamlit as st
from core import projects_ui as PU, admin_digest, auth
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G"})
auth.list_users = lambda *a, **k: []
admin_digest.group_digest = lambda g: {
    "retrasos": [{"id": "PRJ-0001", "nombre": "A", "dias": 33}],
    "vencidos": [{"id": "PRJ-0001", "nombre": "A", "fin": "2026-10-02", "dias": -8}],
    "por_vencer": [], "sin_asignar": [{"id": "PRJ-0015", "nombre": "Z"}],
    "alarmas": [], "near_miss": [], "campo_sin_contacto": [], "cred_venc": [],
    "sobre_presupuesto": []}
PU._resumen_del_dia("G")
'''
at = AppTest.from_string(GUION_HOME, default_timeout=60)
at.session_state["_admin_open_proj"] = "PRJ-0002"
at.run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
b(at, "resind_vencidos").click()
at.run()
b(at, "go_vencidos").click()
at.run()
chk("⚠️ «Overdue → Go to Projects» pide SOLO esas obras",
    at.session_state["_cart_pending"] == {"solo": {"motivo": "Overdue", "ids": ["PRJ-0001"]}}
    if "_cart_pending" in at.session_state else False)
chk("…y la cartera, no la obra que estuviera abierta", "_admin_open_proj" not in at.session_state)
at = AppTest.from_string(GUION_HOME, default_timeout=60)
at.run()
b(at, "resind_retrasos").click()
at.run()
b(at, "go_retrasos").click()
at.run()
chk("⚠️ «Behind schedule → Go to Projects» pide el filtro Behind",
    at.session_state["_cart_pending"] == {"filtro": "🔴 Retraso"}
    if "_cart_pending" in at.session_state else False)

# ══════════════════════════════════════════════════════════════════════════════
print("\n11. El buscador del mapa")
GUION_MAPA = r'''
import streamlit as st
from core import location_ui as L
L.geocode_candidates = lambda q, limit=5: []
getattr(L, "_v558_lp", L.location_picker)("np")
'''
at = AppTest.from_string(GUION_MAPA, default_timeout=60)
at.run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_ti = at.text_input(key="np_q")
chk("el placeholder sin «:material/»", ":material/" not in str(_ti.placeholder), _ti.placeholder)
chk("el icono va por `icon=`", "search" in str(getattr(_ti.proto, "icon", "")), getattr(_ti.proto, "icon", ""))
_ti.set_value("zzz")
b(at, "np_btn").click()
at.run()
chk("⚠️ «I could not find that address» llega (flash), no se pierde en el rerun",
    any("could not find that address" in str(x) for x in flashes(at)), flashes(at))

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("TODO OK")
