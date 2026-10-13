# -*- coding: utf-8 -*-
"""v577 · FINANCE → HOURS, PROBADA ACCIÓN POR ACCIÓN (decisión del usuario: «dale con todo»).

  1. ⚠️ Un periodo sin fichajes dejaba la pantalla EN BLANCO → cifras a 0, aviso y el
     periodo más amplio a un toque («See last 7 days» / «See all»).
  2. ⚠️ Los periodos contaban un día de más («Week» = 8 días naturales, «Month» = 31) →
     «Last 7 days» / «Last 30 days» exactos; segmentado del kit (`cpxseg_gh_per`), recordado.
  3. Las cifras eran HTML → botones: ordenan la tabla por lo que cuentan o bajan a las obras.
  4. Tabla por persona con $ y céntimos («$40.00», salía «40.0»), y un toque abre la ficha.
  5. Textos con `t()` (el pie decía «+ $X interna»).
  6. «Company hours by project» POR ID (dos obras con el mismo nombre se sumaban en una),
     el nombre entero, y un toque abre la obra (o la localización).
  7. «Hours by person and project»: un toque en una celda abre esa obra; en la persona, su ficha.
  8. Horas tiene su rama en el menú de Finanzas y lo desconocido da un error VISIBLE.

AppTest y el motor con sus fuentes sustituidas: ninguna hoja se toca.
"""
import ast
import io
import json
import os
import sys
from datetime import timedelta

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


def _func(rel, nombre):
    _a = ast.parse(io.open(os.path.join(RAIZ, rel), encoding="utf-8").read())
    return next((n for n in ast.walk(_a) if isinstance(n, ast.FunctionDef) and n.name == nombre), None)


# ══════════════════════════════════════════════════════════════════════════════
print("1. El motor: el reparto por ID, y la ventana de días")
from core import timeclock as TC, clock, auth                               # noqa: E402
_hoy = clock.now().date()
_FIL = [
    # (usuario, tipo, pid, nombre de la fila, día, horas)
    ("ana", "proyecto", "PRJ-1", "Torre", _hoy, 3.0),
    ("ana", "proyecto", "PRJ-2", "Torre", _hoy, 2.0),        # ⚠️ el MISMO nombre, otra obra
    ("ana", "proyecto", "", "Vieja sin ID", _hoy, 1.0),
    ("ana", "general", "", "", _hoy, 8.0),
    ("ana", "proyecto", "PRJ-1", "Torre", _hoy - timedelta(days=6), 4.0),   # dentro de 7 días
    ("ana", "proyecto", "PRJ-1", "Torre", _hoy - timedelta(days=7), 100.0),  # fuera de 7 días
]
_o = {n: getattr(TC, n) for n in ("_cached_records", "mapa_nombres", "_ids_internos", "clave_de",
                                  "_row_segmentos", "_tipo_of", "pid_of", "_nombre_actual")}
_oa = {n: getattr(auth, n) for n in ("rate_map", "claves_conocidas")}
try:
    # ⚠️ el nombre sale de la columna «Project» de la fila (`_nombre_actual(pid, r["Project"])`):
    # sin ella la 1ª vuelta lo daba todo por «(no project)» — era la SONDA.
    TC._cached_records = lambda: [{"Group": "G", "Name": f[0], "Project": f[3], "_f": f} for f in _FIL]
    TC.mapa_nombres = lambda g="": {}
    TC._ids_internos = lambda g: set()
    TC.clave_de = lambda r, pn=None: r["_f"][0]
    TC._row_segmentos = lambda r: [(r["_f"][4], r["_f"][5])]
    TC._tipo_of = lambda r: r["_f"][1]
    TC.pid_of = lambda r: r["_f"][2]
    TC._nombre_actual = lambda pid, nom: nom
    auth.rate_map = lambda g: {"ana": 40.0}
    auth.claves_conocidas = lambda: {"ana"}
    _r = TC.group_hours("G", days=None)
    _a = _r[0] if _r else {}
    chk("devuelve el reparto por ID", isinstance(_a.get("por_proyecto_id"), dict), list(_a))
    chk("⚠️ dos obras con el MISMO nombre NO se suman en una (PRJ-1 y PRJ-2 por separado)",
        _a.get("por_proyecto_id", {}).get("PRJ-1") == 107.0
        and _a.get("por_proyecto_id", {}).get("PRJ-2") == 2.0, _a.get("por_proyecto_id"))
    chk("…con el nombre de cada una al lado",
        _a.get("nombres_proyecto", {}).get("PRJ-2") == "Torre", _a.get("nombres_proyecto"))
    chk("una fila vieja SIN ID queda por nombre («~nombre»: sin obra que abrir)",
        _a.get("por_proyecto_id", {}).get("~Vieja sin ID") == 1.0, _a.get("por_proyecto_id"))
    chk("el reparto por NOMBRE de siempre no cambia (las suma, como antes)",
        _a.get("por_proyecto", {}).get("Torre") == 109.0, _a.get("por_proyecto"))
    _r6 = TC.group_hours("G", days=6)
    _a6 = _r6[0] if _r6 else {}
    chk("⚠️ con days=6 entra el día de hace 6 (los 7 días de «Last 7 days») y no el de hace 7",
        _a6.get("por_proyecto_id", {}).get("PRJ-1") == 7.0, _a6.get("por_proyecto_id"))
finally:
    for _n, _v in _o.items():
        setattr(TC, _n, _v)
    for _n, _v in _oa.items():
        setattr(auth, _n, _v)

# ══════════════════════════════════════════════════════════════════════════════
from streamlit.testing.v1 import AppTest                                    # noqa: E402

CAB = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
from core import projects_ui as PU, timeclock, projects as P
st.session_state["auth"] = {"rol": "administrator", "usuario": "adm", "nombre": "Adm", "grupo": "G"}
st.session_state.setdefault("_DAYS", [])


def _p(u, nom, gen, pro, itn, tar, por, indet=False, existe=True):
    return {"usuario": u, "nombre": nom, "general": gen, "proyecto": pro, "interno": itn,
            "sin_asignar": round(max(0.0, gen - pro - itn), 2), "sin_asignar_indet": indet,
            "tarifa": tar, "existe": existe, "costo": round(pro * tar, 2),
            "costo_interno": round(itn * tar, 2),
            "por_proyecto_id": {k: v for k, (n, v) in por.items()},
            "nombres_proyecto": {k: n for k, (n, v) in por.items()}}


_MODO = st.session_state.get("_MODO", "lleno")
if _MODO == "lleno":
    _D = [_p("ana", "Ana", 10.0, 6.0, 1.5, 40.0, {"PRJ-1": ("Torre", 4.0), "PRJ-2": ("Torre", 2.0),
                                                  "LOC-1": ("Oficina", 1.5)}),
          _p("cal", "Cal", 12.0, 0.0, 0.0, 30.0, {}),
          _p("bob", "Bob", 5.0, 3.5, 0.0, 0.0, {"PRJ-1": ("Torre", 1.0), "~Viejo": ("Viejo", 2.5)})]
elif _MODO == "sin_estructura":
    _D = [_p("ana", "Ana", 10.0, 6.0, 0.0, 40.0, {"PRJ-1": ("Torre", 6.0)})]
elif _MODO == "dudoso":
    _D = [_p("ana", "Ana", 2.0, 6.0, 0.0, 40.0, {"PRJ-1": ("Torre", 6.0)}, indet=True)]
else:
    _D = []


def _gh(g, days=None):
    st.session_state["_DAYS"].append(days)
    return [dict(d) for d in _D]


timeclock.is_configured = lambda: True
timeclock.group_hours = _gh
P.list_locations = lambda g=None, incluir_cerradas=False: [{"ID": "LOC-1", "Group": "G"}]
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    for _k, _v in (st.session_state.get("_PRE") or {}).items():
        st.session_state[_k] = _v
# ⚠️ los avisos ANTES de la sección, como la shell (trampa 41)
from core import flash
flash.mostrar()
PU.render_group_hours("G")
''' % RAIZ


def _app(modo="lleno", pre=None):
    a = AppTest.from_string(CAB, default_timeout=90)
    a.session_state["_MODO"] = modo
    if pre:
        a.session_state["_PRE"] = pre
    a.run()
    return a


def _ss(a, k, d=None):
    try:
        return a.session_state[k]
    except KeyError:
        return d


def _kb(a):
    return {b.key: b.label for b in a.button}


def _textos(a):
    return " | ".join([str(x.value) for x in list(a.info) + list(a.error) + list(a.warning)
                       + list(a.caption) + list(a.markdown)])


def _cols(df_el):
    try:
        return json.loads(df_el.proto.columns)
    except Exception:
        return {}


# ══════════════════════════════════════════════════════════════════════════════
print("\n2. El periodo: segmentado, recordado y exacto")
_rgh = _func("core/projects_ui.py", "render_group_hours")
_rad = [n for n in ast.walk(_rgh) if isinstance(n, ast.Call) and ast.unparse(n.func) == "st.radio"]
_kw = {k.arg: ast.unparse(k.value) for k in (_rad[0].keywords if _rad else [])}
chk("el selector es el segmentado del kit (`cpxseg_gh_per`)", _kw.get("key") == "'cpxseg_gh_per'", _kw)
chk("…y se RECUERDA al salir y volver (`persist_state`)", _kw.get("persist_state") == "'session'", _kw)
at = _app()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_r = at.radio(key="cpxseg_gh_per")
chk("⚠️ los rótulos dicen lo que cuentan («Last 7 days», «Last 30 days»)",
    list(_r.options) == ["Today", "Last 7 days", "Last 30 days", "All"], list(_r.options))
chk("abre en «Today»", _r.value == "Hoy", _r.value)
_d0 = (_ss(at, "_DAYS") or [None])[-1]
chk("«Today» pide lo que va de HOY (entre 0 y 1 día, nunca 0: 0 sería «todo»)",
    isinstance(_d0, float) and 0 < _d0 <= 1, _d0)
_dias = {}
for _o in ("Week", "Mes", "Todo"):
    at.radio(key="cpxseg_gh_per").set_value(_o)
    at.run()
    _dias[_o] = (_ss(at, "_DAYS") or [None])[-1]
chk("⚠️ «Last 7 days» pide 6 (hoy + 6 atrás = 7; con 7 eran OCHO días naturales)",
    _dias.get("Week") == 6, _dias)
chk("⚠️ «Last 30 days» pide 29", _dias.get("Mes") == 29, _dias)
chk("«All» pide todo (None)", _dias.get("Todo") is None and "Todo" in _dias, _dias)

# ══════════════════════════════════════════════════════════════════════════════
print("\n1. Un periodo vacío ya no deja la pantalla en blanco")
at = _app("vacio")
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_b = _kb(at)
chk("⚠️ las cifras se quedan (a 0)",
    all(k in _b for k in ("cpxkpi_gh_pers", "cpxkpi_gh_jorn", "cpxkpi_gh_proy", "cpxkpi_gh_sina",
                          "cpxkpi_gh_cost")) and "\n\n0.0 h\n\n" in _b.get("cpxkpi_gh_jorn", ""), _b)
chk("…con el aviso de que no hay fichajes", "No time entries in this period." in _textos(at), _textos(at))
chk("…y el periodo más amplio a un toque (desde «Today»: 7 días y todo)",
    _b.get("gh_ver_Week") == "See last 7 days" and _b.get("gh_ver_Todo") == "See all",
    {k: v for k, v in _b.items() if str(k).startswith("gh_ver_")})
[b for b in at.button if b.key == "gh_ver_Week"][0].click()
at.run()
chk("«See last 7 days» cambia el periodo", at.radio(key="cpxseg_gh_per").value == "Week",
    at.radio(key="cpxseg_gh_per").value)
chk("…y desde ahí solo ofrece «See all»",
    "gh_ver_Week" not in _kb(at) and "gh_ver_Todo" in _kb(at), list(_kb(at)))
at.radio(key="cpxseg_gh_per").set_value("Todo")
at.run()
chk("en «All» no ofrece nada más amplio (ni botones que no llevan a nada)",
    not [k for k in _kb(at) if str(k).startswith("gh_ver_")], list(_kb(at)))

# ══════════════════════════════════════════════════════════════════════════════
print("\n3, 5. Las cifras ACTIVAS y en inglés")
at = _app()
_b = _kb(at)
chk("las 6 cifras son botones, en orden (con estructura)",
    [k for k in _b if str(k).startswith("cpxkpi_gh_")] ==
    ["cpxkpi_gh_pers", "cpxkpi_gh_jorn", "cpxkpi_gh_proy", "cpxkpi_gh_intn", "cpxkpi_gh_sina",
     "cpxkpi_gh_cost"], [k for k in _b if str(k).startswith("cpxkpi_gh_")])
chk("2 por fila en estrecho (`theme.dos_por_fila` sobre su contenedor, v576)",
    ".st-key-cpx_gh_kpis{container-type:inline-size}" in _textos(at), "")
chk("«People» cuenta a quien tiene horas (3)", _b.get("cpxkpi_gh_pers", "").startswith("People\n\n3\n\n"),
    _b.get("cpxkpi_gh_pers"))
chk("⚠️ el pie del coste en inglés: «+ $60 on overhead» (decía «+ $X interna»)",
    _b.get("cpxkpi_gh_cost", "").endswith("\n\n+ \\$60 on overhead"), _b.get("cpxkpi_gh_cost"))
chk("…y ninguna «interna» en la función",
    not any(isinstance(n, ast.Constant) and isinstance(n.value, str) and "interna" in n.value
            for n in ast.walk(_rgh)))
chk("el % sin asignar en el pie de su cifra («% of the workday»)",
    "of the workday" in _b.get("cpxkpi_gh_sina", ""), _b.get("cpxkpi_gh_sina"))
at2 = _app("sin_estructura")
chk("sin estructura, ni la cifra «On overhead» (v425)",
    "cpxkpi_gh_intn" not in _kb(at2), list(_kb(at2)))
at.button(key="cpxkpi_gh_jorn").click()
at.run()
chk("⚠️ tocar «Workday» ordena la tabla por jornada (Cal 12 h primero)",
    _ss(at, "_gh_orden") == "general" and list(at.dataframe[0].value["User"])[:1] == ["Cal"],
    (_ss(at, "_gh_orden"), list(at.dataframe[0].value["User"]) if at.dataframe else None))
chk("…y lo dice («Sorted by «Workday», highest first.»)",
    "Sorted by «Workday», highest first." in _textos(at), "")
chk("…y baja la vista a la tabla (la marca se consume)",
    ".st-key-ir_cpx_gh_tabla" in _textos(at) and _ss(at, "_gh_bajar_tabla") is None, "")
at.button(key="cpxkpi_gh_cost").click()
at.run()
chk("«Labour charged to jobs» ordena por coste (Ana $240 primero)",
    list(at.dataframe[0].value["User"])[:1] == ["Ana"], list(at.dataframe[0].value["User"]))
at.button(key="cpxkpi_gh_proy").click()
at.run()
chk("«On projects» baja a las horas por obra",
    _ss(at, "_gh_orden") == "obras" and ".st-key-ir_cpx_gh_proy" in _textos(at), _ss(at, "_gh_orden"))
at3 = _app("dudoso")
_b3 = _kb(at3)
chk("con horas imposibles, «Unallocated —» y «cannot be worked out»",
    _b3.get("cpxkpi_gh_sina", "") == "Unallocated\n\n—\n\ncannot be worked out", _b3.get("cpxkpi_gh_sina"))
chk("…el aviso, en inglés y con la persona",
    any("charged MORE hours to jobs than their workday (Ana)" in str(e.value) for e in at3.error),
    [str(e.value)[:80] for e in at3.error])
chk("…y la cifra en rojo", ".st-key-cpxkpi_gh_sina button{border-left-color:#c0392b" in _textos(at3), "")
_sin_t = []
for n in ast.walk(_rgh):
    if (isinstance(n, ast.Call) and ast.unparse(n.func) in ("st.caption", "st.info", "st.error",
                                                            "st.warning") and n.args):
        if not any(isinstance(c, ast.Call) and ast.unparse(c.func) == "t" for c in ast.walk(n.args[0])):
            _sin_t.append(ast.unparse(n)[:60])
chk("todos los avisos y pies con `t()`", not _sin_t, _sin_t)

# ══════════════════════════════════════════════════════════════════════════════
print("\n4. La tabla por persona")
at = _app()
_df = at.dataframe[0] if at.dataframe else None
_v = _df.value if _df is not None else None
chk("⚠️ la tarifa con $ y céntimos («$40.00»; salía «40.0») y «—» sin tarifa",
    _v is not None and list(_v["Rate/h"]) == ["$40.00", "$30.00", "—"], list(_v["Rate/h"]) if _v is not None else None)
_c = _cols(_df) if _df is not None else {}
chk("el coste con $ y céntimos (`$%,.2f`)", "$%,.2f" in json.dumps(_c), "")
chk("la persona FIJADA a la izquierda", '"pinned": true' in json.dumps(_c).lower(), "")
_dfs = [n for n in ast.walk(_rgh) if isinstance(n, ast.Call) and ast.unparse(n.func) == "st.dataframe"]
chk("⚠️ las TRES tablas con `single-cell` (un toque abre)",
    len(_dfs) == 3 and all(any(k.arg == "selection_mode" and ast.unparse(k.value) == "'single-cell'"
                               for k in d.keywords) for d in _dfs), len(_dfs))
at = _app(pre={"gh_tbl_0": {"selection": {"rows": [], "columns": [], "cells": [(2, "Shift (h)")]}}})
chk("⚠️ un toque en la 3ª fila abre la ficha de ESA persona en Users",
    _ss(at, "gp_fichasel") == "Bob (bob)"
    and _ss(at, "_admin_nav_pending") == ("planificacion", "👷 Usuarios"), _ss(at, "gp_fichasel"))
chk("…y la tabla cambia de clave (al volver no reabre la misma, trampa 31)", _ss(at, "_gh_tbl_gen") == 1,
    _ss(at, "_gh_tbl_gen"))

# ══════════════════════════════════════════════════════════════════════════════
print("\n6. Las horas por obra: por ID, enteras, y un toque abre")
at = _app()
_dp = at.dataframe[1] if len(at.dataframe) > 1 else None
_vp = list(_dp.value["Proyecto"]) if _dp is not None else []
chk("⚠️ dos obras con el mismo nombre, SEPARADAS y con su ID (mayor primero)",
    _vp == ["Torre (PRJ-1)", "Viejo", "Torre (PRJ-2)", "Oficina"], _vp)
chk("…con su peso en barra (ProgressColumn)", '"progress"' in json.dumps(_cols(_dp)).lower(), "")
at = _app(pre={"gh_ptbl_0": {"selection": {"rows": [], "columns": [], "cells": [(2, "Horas")]}}})
chk("⚠️ tocar «Torre (PRJ-2)» abre ESA obra (no la otra Torre)",
    _ss(at, "_prjsel_pending") == "PRJ-2"
    and _ss(at, "_admin_nav_pending") == ("proyectos", "📊 Proyectos"), _ss(at, "_prjsel_pending"))
at = _app(pre={"gh_ptbl_0": {"selection": {"rows": [], "columns": [], "cells": [(3, "Proyecto")]}}})
chk("⚠️ tocar una LOCALIZACIÓN la abre en Locations (no en la cartera)",
    _ss(at, "_loc_open") == "LOC-1" and _ss(at, "_prjsel_pending") is None
    and _ss(at, "_admin_nav_pending") == ("proyectos", "🏢 Localizaciones"), _ss(at, "_loc_open"))
at = _app(pre={"gh_ptbl_0": {"selection": {"rows": [], "columns": [], "cells": [(1, "Proyecto")]}}})
chk("una fila vieja sin ID no lleva a ninguna parte (y no reabre: otra clave)",
    _ss(at, "_admin_nav_pending") is None and _ss(at, "_gh_ptbl_gen") == 1, _ss(at, "_admin_nav_pending"))

# ══════════════════════════════════════════════════════════════════════════════
print("\n7. La matriz persona × obra")
at = _app()
_dm = at.dataframe[2] if len(at.dataframe) > 2 else None
chk("solo las personas con horas en obras (Cal no)",
    _dm is not None and list(_dm.value["Persona"]) == ["Ana", "Bob"],
    list(_dm.value["Persona"]) if _dm is not None else None)
chk("…y las obras por ID (las dos Torre, en columnas distintas)",
    _dm is not None and "Torre (PRJ-1)" in _dm.value.columns and "Torre (PRJ-2)" in _dm.value.columns,
    list(_dm.value.columns) if _dm is not None else None)
at = _app(pre={"gh_mtbl_0": {"selection": {"rows": [], "columns": [], "cells": [(1, "Torre (PRJ-1)")]}}})
chk("⚠️ tocar una celda abre ESA obra", _ss(at, "_prjsel_pending") == "PRJ-1", _ss(at, "_prjsel_pending"))
at = _app(pre={"gh_mtbl_0": {"selection": {"rows": [], "columns": [], "cells": [(0, "Oficina")]}}})
chk("…la de una localización, en Locations", _ss(at, "_loc_open") == "LOC-1", _ss(at, "_loc_open"))
at = _app(pre={"gh_mtbl_0": {"selection": {"rows": [], "columns": [], "cells": [(1, "Persona")]}}})
chk("⚠️ tocar el NOMBRE abre la ficha de esa persona (la 2ª fila de la matriz es Bob: Cal no está)",
    _ss(at, "gp_fichasel") == "Bob (bob)"
    and _ss(at, "_admin_nav_pending") == ("planificacion", "👷 Usuarios"), _ss(at, "gp_fichasel"))

# ══════════════════════════════════════════════════════════════════════════════
print("\n8. El menú de Finanzas")
_fin = _func("core/home_ui.py", "_seccion_finanzas")
_ifs = [n for n in ast.walk(_fin) if isinstance(n, ast.If) and isinstance(n.test, ast.Compare)
        and ast.unparse(n.test) == "sub == '⏱ Horas'"]
chk("⚠️ Horas tiene su rama propia", len(_ifs) == 1, len(_ifs))
_else = _ifs[0].orelse if _ifs else []
chk("…y lo desconocido cae a un error VISIBLE (no a Horas)",
    len(_else) == 1 and "st.error" in ast.unparse(_else[0]) and "render_group_hours" not in ast.unparse(_else),
    ast.unparse(_else[0])[:80] if _else else "")

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
sys.exit(1 if fallos else 0)
