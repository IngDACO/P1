# -*- coding: utf-8 -*-
"""v579 · FINANCE → PROFITABILITY, PROBADA ACCIÓN POR ACCIÓN (decisión del usuario: «dale con todo»).

  1. ⚠️ Una obra con ganancia FIJA salía «with no profit set… $0» con «ESTIMATED PROFIT $50»
     encima, «Margin % 0.0%» en la tabla y el «No margin» del Resumen la contaba (visto en
     producción poniendo $50 fijos a PRJ-0015): la regla era el % de MANO DE OBRA, que vale
     0 con la fija → `a_costo` (el modelo), la misma en las dos pantallas; y el margen, sobre
     el ingreso (la definición del Resumen).
  2. ⚠️ Con ganancia por hora para unos y no para otros, las horas de los demás se cobran a
     COSTO y nada lo decía (visto: Admin2 con ganancia, campo000 sin) → aviso con nombres.
  3. Cabeceras en español («Costo», «Ingreso estimado», «Ganancia», «Facturado»; y «Avance
     %», «Nota» en la tabla de avance del CAMPO): una configuración sin etiqueta pisaba la
     traducida → `tabla.cfg` conserva la etiqueta, y un barrido de toda la app.
  4. Céntimos (salía $133 por $132.55).   5. Cifras ACTIVAS: ordenan o abren lo pendiente
     de facturar (cada obra prepara su factura).   6. Avisos con un botón por obra.
  7. La tabla: un toque abre la obra en Costs, proyecto fijado y con su ID si se repite.
  8. El desplegable de obras sin movimiento, con `t()`, clave y botones.   9. Vacía: salida.

AppTest y el motor con sus fuentes sustituidas: ninguna hoja se toca.
"""
import ast
import io
import json
import os
import pathlib
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


def _func(rel, nombre):
    _a = ast.parse(io.open(os.path.join(RAIZ, rel), encoding="utf-8").read())
    return next((n for n in ast.walk(_a) if isinstance(n, ast.FunctionDef) and n.name == nombre), None)


# Los cuatro modelos de `project_revenue` tal como los devuelve (v360/v370/v373), y una
# localización interna, que no entra.
_REV = {
    "PRJ-1": {"costo": 100.0, "ingreso": 100.0, "ganancia": 0.0, "margen_pct": 0.0,
              "modelo": "a_costo", "sin_ganancia": ["ana"]},
    "PRJ-2": {"costo": 3.15, "ingreso": 53.15, "ganancia": 50.0, "margen_pct": 0.0,
              "modelo": "fija", "sin_ganancia": ["ana"]},
    "PRJ-3": {"costo": 200.0, "ingreso": 260.0, "ganancia": 60.0, "margen_pct": 30.0,
              "modelo": "rubro", "sin_ganancia": ["campo000"]},
    "PRJ-4": {"costo": 0.0, "ingreso": 0.0, "ganancia": 0.0, "margen_pct": 0.0,
              "modelo": "a_costo", "sin_ganancia": []},
}
_GE = {"proyectos": [{"id": "PRJ-1", "nombre": "Torre"}, {"id": "PRJ-2", "nombre": "Torre"},
                     {"id": "PRJ-3", "nombre": "Movil"}, {"id": "PRJ-4", "nombre": "Vacia"},
                     {"id": "LOC-1", "nombre": "Oficina", "interno": True}]}

# ══════════════════════════════════════════════════════════════════════════════
print("1. El motor: «sin ganancia» por el MODELO, margen sobre el ingreso, quién va a costo")
from core import finance as F, expenses as E, projects as P                  # noqa: E402
_o = (E.group_expenses, P.list_projects, F.project_revenue)
try:
    E.group_expenses = lambda g: _GE
    P.list_projects = lambda *a, **k: [{"ID": k_} for k_ in _REV]
    F.project_revenue = lambda pid, g, prj=None: dict(_REV[pid])
    _gp = F.group_profitability("G")
finally:
    E.group_expenses, P.list_projects, F.project_revenue = _o
_r = {r["id"]: r for r in _gp["rows"]}
chk("la localización no entra (v422)", "LOC-1" not in _r and len(_r) == 4, list(_r))
chk("⚠️ la de ganancia FIJA ($50, % de mano de obra 0) NO es «sin ganancia»",
    _r["PRJ-2"]["a_costo"] is False and _r["PRJ-2"]["margen"] == 0.0, _r["PRJ-2"])
chk("…la que no tiene ninguna, sí", _r["PRJ-1"]["a_costo"] is True and _r["PRJ-4"]["a_costo"] is True)
chk("…ni la de ganancia por hora", _r["PRJ-3"]["a_costo"] is False)
chk("⚠️ el margen, sobre el INGRESO (50 / 53.15 = 94.1 %; antes 0.0 %)",
    _r["PRJ-2"]["margen_ing"] == 94.1 and _r["PRJ-3"]["margen_ing"] == 23.1, (_r["PRJ-2"]["margen_ing"], _r["PRJ-3"]["margen_ing"]))
chk("…y sin ingreso no hay margen (None, no 0)", _r["PRJ-4"]["margen_ing"] is None, _r["PRJ-4"]["margen_ing"])
chk("⚠️ con ganancia por hora, quien no la tiene va a costo (campo000)",
    _r["PRJ-3"]["a_costo_personas"] == ["campo000"], _r["PRJ-3"]["a_costo_personas"])
chk("…y en una obra a costo o con solo la fija no se repite el aviso (es lo esperado)",
    _r["PRJ-1"]["a_costo_personas"] == [] and _r["PRJ-2"]["a_costo_personas"] == [])

# ══════════════════════════════════════════════════════════════════════════════
print("\n3. Las cabeceras: una configuración sin etiqueta ya no pisa la traducida")
import streamlit as st                                                      # noqa: E402
from core import tabla                                                       # noqa: E402
_c = tabla.cfg(None, {"Avance %": st.column_config.NumberColumn(min_value=0, max_value=100),
                      "Nota": st.column_config.TextColumn(help="x"),
                      "Costo": st.column_config.NumberColumn("Mine", format="%d")})
chk("⚠️ sin etiqueta → la traducida («Avance %» → «Progress %», «Nota» → «Note»)",
    _c["Avance %"]["label"] == "Progress %" and _c["Nota"]["label"] == "Note",
    (_c["Avance %"]["label"], _c["Nota"]["label"]))
chk("…sin perder lo suyo (límites, ayuda)",
    _c["Avance %"]["type_config"]["max_value"] == 100 and _c["Nota"]["help"] == "x")
chk("…y con etiqueta propia, manda la suya", _c["Costo"]["label"] == "Mine")
# Barrido de TODA la app: cada columna configurada sin etiqueta tiene traducción (si no,
# la cabecera sería la clave tal cual).
_sueltas = []
for p in sorted(pathlib.Path(RAIZ).rglob("*.py")):
    try:
        _tr = ast.parse(p.read_text(encoding="utf-8"))
    except Exception:
        continue
    for n in ast.walk(_tr):
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if (isinstance(k, ast.Constant) and isinstance(k.value, str) and isinstance(v, ast.Call)
                        and ast.unparse(v.func).startswith("st.column_config.")
                        and not v.args and not any(kw.arg == "label" for kw in v.keywords)
                        and k.value not in tabla.CABECERAS):
                    _sueltas.append(f"{p.name}:{v.lineno} {k.value!r}")
chk("⚠️ en toda la app, ninguna columna sin etiqueta NI traducción", not _sueltas, _sueltas)
_rgp = _func("core/projects_ui.py", "render_group_profitability")
_sinlab = [ast.unparse(k) for n in ast.walk(_rgp) if isinstance(n, ast.Dict)
           for k, v in zip(n.keys, n.values)
           if isinstance(v, ast.Call) and ast.unparse(v.func).startswith("st.column_config.")
           and not v.args and not any(kw.arg == "label" for kw in v.keywords)]
chk("…y en Profitability, todas con su etiqueta", not _sinlab, _sinlab)

# ══════════════════════════════════════════════════════════════════════════════
from streamlit.testing.v1 import AppTest                                    # noqa: E402

CAB = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
from core import projects_ui as PU, finance as F, expenses as E, projects as P, invoices as INV, auth
st.session_state["auth"] = {"rol": "administrator", "usuario": "adm", "nombre": "Adm", "grupo": "G"}
_REV = %r
_GE = %r
_MODO = st.session_state.get("_MODO", "lleno")
if _MODO == "perdida":
    _REV = dict(_REV, **{"PRJ-3": {"costo": 200.0, "ingreso": 80.0, "ganancia": -120.0,
                                   "margen_pct": -60.0, "modelo": "cotizado", "sin_ganancia": []}})
E.group_expenses = lambda g: (_GE if _MODO != "vacio" else {"proyectos": []})
P.list_projects = lambda *a, **k: [{"ID": k_} for k_ in _REV]
P.get_project = lambda pid: {"ID": pid, "Name": "x", "Client": "", "Group": "G"}
F.project_revenue = lambda pid, g, prj=None: dict(_REV[pid])
INV.facturado_por_proyecto = lambda g: {"PRJ-3": 100.0}
auth.list_users = lambda grupo=None, **k: [{"User": "campo000", "Name": "Campo Cero", "Role": "field"}]
from core import clientes as _C
_C.list_clientes = lambda g, **k: []
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    for _k, _v in (st.session_state.get("_PRE") or {}).items():
        st.session_state[_k] = _v
# ⚠️ los avisos ANTES de la sección, como la shell (trampa 41)
from core import flash
flash.mostrar()
PU.render_group_profitability("G")
''' % (RAIZ, _REV, _GE)


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


print("\n1-2, 6. Los avisos, por el modelo y ACTIVOS")
at = _app()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_w = [str(x.value) for x in at.warning]
_w0 = [x for x in _w if "no profit set" in x]
chk("⚠️ «no profit set» cuenta 2 (la a costo y la vacía), NO la de ganancia fija",
    _w0 and "**2 job(s) with no profit set**" in _w0[0], _w0)
_b = _kb(at)
chk("…con un botón por obra, sin la fija (y con el ID: las dos «Torre»)",
    [v for k, v in _b.items() if str(k).startswith("rentmar_")]
    == [":material/open_in_new: Torre (PRJ-1)", ":material/open_in_new: Vacia"],
    [v for k, v in _b.items() if str(k).startswith("rentmar_")])
chk("⚠️ el aviso de horas a COSTO, con el NOMBRE (no el login)",
    any("Hours invoiced at cost" in x for x in _w)
    and [v for k, v in _b.items() if str(k).startswith("rentpar_")]
    == [":material/open_in_new: Movil · Campo Cero"],
    [v for k, v in _b.items() if str(k).startswith("rentpar_")])
[b for b in at.button if str(b.key).startswith("rentmar_0_")][0].click()
at.run()
chk("tocar la obra del aviso la abre en sus Costs (donde se pone la ganancia)",
    _ss(at, "_prjsel_pending") == "PRJ-1" and _ss(at, "_prj_sec_pending") == "💰 Costos"
    and _ss(at, "_admin_nav_pending") == ("proyectos", "📊 Proyectos"), _ss(at, "_prjsel_pending"))

print("\n5. Las cifras, ACTIVAS")
at = _app()
_b = _kb(at)
chk("las 5 cifras son botones, en orden",
    [k for k in _b if str(k).startswith("cpxkpi_rent_")] ==
    ["cpxkpi_rent_cost", "cpxkpi_rent_ing", "cpxkpi_rent_gan", "cpxkpi_rent_fac", "cpxkpi_rent_pdt"],
    [k for k in _b if str(k).startswith("cpxkpi_rent_")])
chk("«Cost charged» (el nombre que fijó v313) y los importes",
    _b.get("cpxkpi_rent_cost", "").startswith("Cost charged\n\n\\$303") and
    _b.get("cpxkpi_rent_ing", "").startswith("Estimated revenue\n\n\\$413"), _b.get("cpxkpi_rent_cost"))
chk("la ganancia dice qué parte del ingreso es (110 / 413.15 = 26.6 %)",
    _b.get("cpxkpi_rent_gan", "") == "Estimated profit\n\n\\$110\n\n26.6% of revenue", _b.get("cpxkpi_rent_gan"))
chk("«To invoice» con cuántas obras", _b.get("cpxkpi_rent_pdt", "").endswith("\n\n3 job(s) pending"),
    _b.get("cpxkpi_rent_pdt"))
chk("3 por fila, 2 en estrecho (`theme.por_fila`, v578)",
    "flex:0 1 calc(33.3333% - 0.6667rem)" in _textos(at)
    and ".st-key-cpx_rent_kpis{container-type:inline-size}" in _textos(at), "")
chk("la ganancia en verde si gana", "cpxkpi_rent_gan button{border-left-color:#1e8449" in _textos(at), "")
_ap = _app("perdida")
chk("⚠️ …y en ROJO si pierde (una obra con precio pactado bajo el costo)",
    "cpxkpi_rent_gan button{border-left-color:#c0392b" in _textos(_ap), "")
at.button(key="cpxkpi_rent_cost").click()
at.run()
_v = at.dataframe[0].value if at.dataframe else None
chk("⚠️ tocar «Cost charged» ordena la tabla por costo (Movil $200 primero)",
    _ss(at, "_rent_orden") == "costo" and _v is not None and list(_v["Proyecto"])[:1] == ["Movil"]
    and list(_v["Proyecto"]) == ["Movil", "Torre (PRJ-1)", "Torre (PRJ-2)"],
    list(_v["Proyecto"]) if _v is not None else None)
chk("…lo dice y baja a la tabla",
    "Sorted by «Cost charged», highest first." in _textos(at) and ".st-key-ir_cpx_rent_tabla" in _textos(at), "")
at.button(key="cpxkpi_rent_pdt").click()
at.run()
_b = _kb(at)
chk("⚠️ «To invoice» abre lo pendiente, mayor primero, y cada obra prepara SU factura",
    [v for k, v in _b.items() if str(k).startswith("rentfac_")]
    == [":material/receipt: Movil · \\$160", ":material/receipt: Torre (PRJ-1) · \\$100",
        ":material/receipt: Torre (PRJ-2) · \\$53"],
    [v for k, v in _b.items() if str(k).startswith("rentfac_")])
at.button(key="rentfac_PRJ-3").click()
at.run()
chk("…tocar una abre el alta de factura con esa obra", _ss(at, "_fac_prj_pending") == "PRJ-3"
    and _ss(at, "_admin_nav_pending") == ("finanzas", "🧾 Facturas"), _ss(at, "_fac_prj_pending"))
at = _app(pre={"_rent_vista": "pdt"})
at.button(key="cpxkpi_rent_pdt").click()
at.run()
chk("un segundo toque en «To invoice» lo cierra", not [k for k in _kb(at) if str(k).startswith("rentfac_")],
    [k for k in _kb(at) if str(k).startswith("rentfac_")])

print("\n3-4, 7. La tabla")
at = _app()
_df = at.dataframe[0] if at.dataframe else None
_c = _cols(_df)
_lab = {k: (_c.get(k) or {}).get("label") for k in ("Proyecto", "Cost", "Revenue", "Profit", "Margin",
                                                    "Invoiced", "To invoice")}
chk("⚠️ las cabeceras en INGLÉS (salían «Costo», «Ingreso estimado», «Ganancia», «Facturado»)",
    _lab == {"Proyecto": "Project", "Cost": "Cost", "Revenue": "Est. revenue", "Profit": "Est. profit",
             "Margin": "Margin %", "Invoiced": "Invoiced", "To invoice": "To invoice"}, _lab)
chk("⚠️ el dinero con céntimos y el signo delante («dollar»; salía «$%,d», $133 por $132.55)",
    all((_c.get(k) or {}).get("type_config", {}).get("format") == "dollar"
        for k in ("Cost", "Revenue", "Profit", "Invoiced", "To invoice")), "")
chk("…y los importes sin redondear", _df is not None and list(_df.value["Revenue"]) == [260.0, 53.15, 100.0],
    list(_df.value["Revenue"]) if _df is not None else None)
chk("el proyecto FIJADO", (_c.get("Proyecto") or {}).get("pinned") is True, _c.get("Proyecto"))
chk("⚠️ el margen sobre el ingreso, y la fija ya no sale a 0.0 %",
    _df is not None and list(_df.value["Margin"]) == ["23.1%", "94.1%", "0.0%"],
    list(_df.value["Margin"]) if _df is not None else None)
chk("ordenada por ganancia por defecto (Movil, Torre fija, Torre a costo)",
    _df is not None and list(_df.value["Proyecto"]) == ["Movil", "Torre (PRJ-2)", "Torre (PRJ-1)"],
    list(_df.value["Proyecto"]) if _df is not None else None)
_dfs = [n for n in ast.walk(_rgp) if isinstance(n, ast.Call) and ast.unparse(n.func) == "st.dataframe"]
chk("un toque: `single-cell`", len(_dfs) == 1 and any(
    k.arg == "selection_mode" and ast.unparse(k.value) == "'single-cell'" for k in _dfs[0].keywords))
at = _app(pre={"rent_tbl_0": {"selection": {"rows": [], "columns": [], "cells": [(1, "Cost")]}}})
chk("⚠️ un toque en la 2ª fila abre ESA obra (la Torre fija, PRJ-2) en sus Costs",
    _ss(at, "_prjsel_pending") == "PRJ-2" and _ss(at, "_prj_sec_pending") == "💰 Costos"
    and _ss(at, "_rent_tbl_gen") == 1, (_ss(at, "_prjsel_pending"), _ss(at, "_rent_tbl_gen")))
chk("…de solo lectura (v455)", "st.data_editor" not in ast.unparse(_rgp))

print("\n8-9. Sin movimiento y vacía")
at = _app()
_ex = [e for e in list(at.expander) + list(at.status)]
chk("⚠️ el desplegable de obras sin movimiento, con clave y traducido",
    any("1 job(s) with no movement" in str(getattr(e, "label", "")) for e in _ex)
    and any(isinstance(n, ast.Call) and ast.unparse(n.func) == "st.expander"
            and any(k.arg == "key" for k in n.keywords)
            and isinstance(n.args[0], ast.Call) and ast.unparse(n.args[0].func) == "t"
            for n in ast.walk(_rgp)), [getattr(e, "label", "") for e in _ex])
chk("…y cada obra, un botón", [v for k, v in _kb(at).items() if str(k).startswith("rentsin_")]
    == [":material/open_in_new: Vacia"], [k for k in _kb(at) if str(k).startswith("rentsin_")])
at = _app("vacio")
chk("vacía: el aviso de siempre", "No projects with recorded cost yet" in _textos(at), "")
at.button(key="rent_ir_proy").click()
at.run()
chk("⚠️ …y una salida, a Projects", _ss(at, "_admin_nav_pending") == ("proyectos", "📊 Proyectos"),
    _ss(at, "_admin_nav_pending"))
_sin_t = [ast.unparse(n)[:60] for n in ast.walk(_rgp)
          if isinstance(n, ast.Call) and ast.unparse(n.func) in ("st.caption", "st.info", "st.warning")
          and n.args and not any(isinstance(c, ast.Call) and ast.unparse(c.func) == "t"
                                 for c in ast.walk(n.args[0]))]
chk("todos los avisos y pies con `t()`", not _sin_t, _sin_t)

print("\n1. El «No margin» del Resumen, con la MISMA regla")
_pnl = _func("core/projects_ui.py", "render_pnl")
_sm = [n for n in ast.walk(_pnl) if isinstance(n, ast.Assign)
       and any(getattr(t_, "id", "") == "_sinmar" for t_ in n.targets)]
chk("⚠️ `_sinmar` cuenta las obras `a_costo` (no las de % de mano de obra 0)",
    _sm and "a_costo" in ast.unparse(_sm[0]) and "margen" not in ast.unparse(_sm[0]),
    ast.unparse(_sm[0])[:120] if _sm else "")

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
sys.exit(1 if fallos else 0)
