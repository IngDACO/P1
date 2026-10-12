# -*- coding: utf-8 -*-
"""v568 · FINANCE → EXPENSES, PROBADA ACCIÓN POR ACCIÓN (decisión del usuario: «dale con todo»).

  1. ⚠️ «Projected at completion» sumaba el coste de HOY de obras sin avance → «Forecast»
     solo de las que la tienen, y dice cuántas no.     2. «% used» con un decimal bajo 10 %.
  3. ⚠️ Compras sin obra: el aviso mandaba «assign them from the receipt» y no había forma
     → se listan y cada una se asigna a una obra del grupo (`expenses.asignar_proyecto`).
  4. Estado con cabecera y en inglés (salía «sobre/pedido/riesgo»).   5. Textos con `t()`.
  6. CSV con cabeceras en inglés y `expenses_….csv`.   7. Dinero con $ y miles.
  8. Tarjetas ACTIVAS.   9. Tabla con presupuesto: un toque abre la obra en Costs.
 10. Sin presupuesto: un toque la abre en Data.   11. Avisos con botones por obra.
 12. Filas fijas de 4 (2 bajo 700 px), sin estirar la última — medido en una mini-app.
  +  «Receipt added» en inglés (salía «Recibo agregado»), y verif_v313 mira de verdad las
     TRES funciones (su `check` estaba fuera del bucle).

AppTest y el motor con sus fuentes sustituidas: ninguna hoja se toca.
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


# ══════════════════════════════════════════════════════════════════════════════
print("1. El motor: compras sin obra, asignarlas, y el recibo en inglés")
from core import expenses as E, projects as P                               # noqa: E402
_o = {n: getattr(E, n) for n in ("_records", "_ws", "_invalidate", "_next_id")}
_op = {n: getattr(P, n) for n in ("list_projects", "get_project")}
_REC = [{"ID": "G-1", "ProjectID": "PRJ-1", "Group": "G", "Date": "2026-09-01", "Amount": "10"},
        {"ID": "G-2", "ProjectID": "", "Group": "G", "Date": "2026-08-01", "Amount": "20"},
        {"ID": "G-3", "ProjectID": "PRJ-BORRADA", "Group": "G", "Date": "2026-09-20", "Amount": "30"},
        {"ID": "G-4", "ProjectID": "", "Group": "OTRA", "Date": "2026-09-21", "Amount": "40"},
        {"ID": "G-5", "ProjectID": "LOC-1", "Group": "G", "Date": "2026-09-22", "Amount": "50"}]
_LLAM = []


def _lp(*a, **k):
    _LLAM.append(k)
    return [{"ID": "PRJ-1", "Group": "G"}, {"ID": "LOC-1", "Group": "G"}]


class _WS:
    def __init__(self):
        self.cells, self.app = [], []

    def get_all_records(self, **k):
        return [dict(r) for r in _REC]

    def update_cell(self, r, c, v):
        self.cells.append((r, c, v))

    def append_row(self, row, **k):
        self.app.append(row)


try:
    E._records = lambda: [dict(r) for r in _REC]
    P.list_projects = _lp
    _h = E.huerfanos("G")
    chk("⚠️ las HUÉRFANAS del grupo: sin obra o de una borrada (no la de la oficina, no otro grupo)",
        [r["ID"] for r in _h] == ["G-3", "G-2"], [r["ID"] for r in _h])
    chk("…con el MISMO conjunto de obras que `group_expenses` (archivadas e internas)",
        _LLAM and _LLAM[-1].get("incluir_archivados") is True and _LLAM[-1].get("incluir_internos") is True,
        _LLAM[-1:])
    _w = _WS()
    E._ws = lambda: _w
    E._invalidate = lambda: None
    P.get_project = lambda pid: {"PRJ-1": {"ID": "PRJ-1", "Name": "Obra 1", "Group": "G"},
                                 "X-9": {"ID": "X-9", "Name": "Ajena", "Group": "OTRA"}}.get(pid)
    ok, msg = E.asignar_proyecto("G-2", "PRJ-1", "G")
    chk("⚠️ asignar una huérfana escribe SU ProjectID (fila 3, columna 2)",
        ok and _w.cells == [(3, 2, "PRJ-1")], (ok, msg, _w.cells))
    chk("…y lo dice («Purchase G-2 assigned to Obra 1.»)", msg == "Purchase G-2 assigned to Obra 1.", msg)
    for _gid, _pid, _q in (("G-2", "X-9", "⚠️ a una obra de OTRA empresa: no (cerrojo v351)"),
                           ("G-1", "PRJ-1", "⚠️ una compra que YA es de una obra: no se mueve"),
                           ("G-4", "PRJ-1", "una compra de otro grupo: «no encontrada»"),
                           ("G-99", "PRJ-1", "una que no existe: «no encontrada»")):
        _w.cells = []
        ok, msg = E.asignar_proyecto(_gid, _pid, "G")
        chk(_q + " — y NO escribe", not ok and _w.cells == [], (ok, msg, _w.cells))
    E._next_id = lambda recs: "G-00009"
    ok, msg = E.add("PRJ-1", "G", 12.5, creado_por="x")
    chk("«Receipt added (12.50).» (salía «Recibo agregado»)", ok and msg == "Receipt added (12.50).", msg)
finally:
    for n, f in _o.items():
        setattr(E, n, f)
    for n, f in _op.items():
        setattr(P, n, f)

from streamlit.testing.v1 import AppTest                                    # noqa: E402

CAB = r'''
import streamlit as st
from core import projects_ui as PU, expenses as E, projects as P, orders as O, incrustar
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G",
                                     "nombre": "Jefa"})
st.session_state.setdefault("_LL", [])
incrustar.script = lambda h, *a, **k: st.session_state["_LL"].append(("script", h))
def _f(i, nom, tot, pres, av=0.0, comp=0.0, over=False, over_comp=False, over_proj=False, interno=False):
    proy = round(tot * 100 / av, 2) if av > 0 and tot > 0 else None
    return {"id": i, "nombre": nom, "compras": round(tot * 0.4, 2), "mano_obra": round(tot * 0.6, 2),
            "total": tot, "presupuesto": pres, "pct": round(100 * tot / pres) if pres else None,
            "over": over, "comprometido": comp, "total_comp": tot + comp, "over_comp": over_comp,
            "avance": av, "proyectado": proy, "interno": interno, "over_proj": over_proj}
_MODO = st.session_state.get("_MODO", "lleno")
if _MODO == "lleno":
    _FILAS = [_f("PRJ-1", "Movil", 132.55, 42000), _f("PRJ-2", "Walker", 134.4, 45000),
              _f("PRJ-3", "Torre", 51000.0, 50000, av=80, over=True),
              _f("PRJ-4", "Pedido", 9000.0, 10000, av=50, comp=2500, over_comp=True, over_proj=True),
              _f("PRJ-5", "SinPres", 3.15, 0), _f("LOC-1", "Oficina", 400.0, 0, interno=True)]
    _HUER = {"n": 2, "total": 75.5}
else:                                   # lo de producción: dos obras al 0 %, sin pedidos
    _FILAS = [_f("PRJ-1", "Movil", 132.55, 42000), _f("PRJ-2", "Walker", 134.4, 45000),
              _f("PRJ-5", "SinPres", 3.15, 0)]
    _HUER = {"n": 0, "total": 0.0}
E.is_configured = lambda: True
E.group_expenses = lambda g: {"proyectos": [dict(x) for x in _FILAS],
                              "por_categoria": {"Materials": 128.0}, "huerfanos": _HUER,
                              "compras_grupo": sum(x["compras"] for x in _FILAS)}
E.huerfanos = lambda g: [{"ID": "G-41", "Date": "2026-09-02", "Supplier": "Bunnings",
                          "Category": "Materials", "Amount": "50.5", "Description": "Bolts"},
                         {"ID": "G-42", "Date": "2026-08-20", "Supplier": "Shell",
                          "Category": "Fuel", "Amount": "25", "Description": ""}]
def _asg(gid, pid, g):
    st.session_state["_LL"].append(("asignar", gid, pid, g))
    return True, "Purchase %s assigned." % gid
E.asignar_proyecto = _asg
O.atrasadas = lambda g: ([{"ProjectID": "PRJ-4", "Supplier": "Parts", "dias": 6}]
                         if _MODO == "lleno" else [])
P.list_projects = lambda *a, **k: [{"ID": x["id"], "Name": x["nombre"], "Group": "G"} for x in _FILAS]
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    for _k, _v in (st.session_state.get("_PRE") or {}).items():
        st.session_state[_k] = _v
PU.render_group_expenses("G")
from core import flash
flash.mostrar()
'''


def _app(modo="lleno", pre=None):
    a = AppTest.from_string(CAB, default_timeout=90)
    a.session_state["_MODO"] = modo
    if pre:
        a.session_state["_PRE"] = pre
    a.run()
    return a


# ══════════════════════════════════════════════════════════════════════════════
print("\n2. Lo de producción: dos obras al 0 % y una sin presupuesto")
at = _app("prod")
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_kb = {b.key: b.label for b in at.button}
chk("⚠️ «Forecast —» con «no progress yet» (antes «Projected at completion $270»)",
    _kb.get("cpxkpi_ge_prev", "") == "Forecast\n\n—\n\nno progress yet", _kb.get("cpxkpi_ge_prev"))
chk("⚠️ «% used 0.3%» (antes «0%»)", "\n\n0.3%\n\n" in _kb.get("cpxkpi_ge_pct", ""), _kb.get("cpxkpi_ge_pct"))
chk("el nombre de la cifra por lo que es («Cost charged to jobs», v313)",
    _kb.get("cpxkpi_ge_cost", "").startswith("Cost charged to jobs\n\n\\$270"), _kb.get("cpxkpi_ge_cost"))
chk("sin pedidos ni estructura, ni «Committed» ni «Overhead spend»",
    "cpxkpi_ge_comp" not in _kb and "cpxkpi_ge_int" not in _kb)

print("\n3, 8, 11-12. Todo lleno: tarjetas, detalles y avisos ACTIVOS")
at = _app()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_kb = {b.key: b.label for b in at.button}
chk("las 7 tarjetas, con «Committed» SEGUNDA",
    [k for k in _kb if str(k).startswith("cpxkpi_ge_")] ==
    ["cpxkpi_ge_cost", "cpxkpi_ge_comp", "cpxkpi_ge_pres", "cpxkpi_ge_pct", "cpxkpi_ge_prev",
     "cpxkpi_ge_sobrep", "cpxkpi_ge_int"], [k for k in _kb if str(k).startswith("cpxkpi_ge_")])
chk("⚠️ «Forecast» suma SOLO las obras con previsión y dice cuántas faltan",
    _kb.get("cpxkpi_ge_prev", "") == "Forecast\n\n\\$81,750\n\n3 job(s) with no forecast yet",
    _kb.get("cpxkpi_ge_prev"))
chk("⚠️ filas FIJAS de 4 columnas (2 filas para 7 tarjetas)",
    len([c for c in at.columns]) >= 8)
chk("los avisos con un botón por obra (pasada, en riesgo, con pedido, pedido atrasado)",
    all(k in _kb for k in ("geerr_0_PRJ-3", "gerisk_0_PRJ-4", "geoc_0_PRJ-4", "geatr_0_PRJ-4")),
    sorted(k for k in _kb if str(k).startswith("ge")))
chk("…en inglés («6 d late»)", "6 d late" in _kb.get("geatr_0_PRJ-4", ""), _kb.get("geatr_0_PRJ-4"))
[b for b in at.button if b.key == "geerr_0_PRJ-3"][0].click()
at.run()
chk("⚠️ el nombre del aviso abre la obra en Costs",
    at.session_state["_prjsel_pending"] == "PRJ-3" and at.session_state["_prj_sec_pending"] == "💰 Costos")

at = _app()
[b for b in at.button if b.key == "cpxkpi_ge_sobrep"][0].click()
at.run()
chk("⚠️ «Over budget» abre la lista de esas obras", "geover_0_PRJ-3" in {b.key for b in at.button})
at = _app()
[b for b in at.button if b.key == "cpxkpi_ge_comp"][0].click()
at.run()
_kb = {b.key: b.label for b in at.button}
chk("«Committed» abre las obras con material pedido (con su importe)",
    "gecomp_0_PRJ-4" in _kb and "2,500" in _kb.get("gecomp_0_PRJ-4", ""), sorted(_kb)[:12])
at = _app()
[b for b in at.button if b.key == "cpxkpi_ge_int"][0].click()
at.run()
chk("«Overhead spend» lleva a Locations",
    at.session_state["_admin_nav_pending"] == ("proyectos", "🏢 Localizaciones"))
at = _app()
[b for b in at.button if b.key == "cpxkpi_ge_cost"][0].click()
at.run()
_scr = [x for x in at.session_state["_LL"] if x[0] == "script"]
chk("⚠️ «Cost charged to jobs» baja la vista a la tabla (UNA vez)",
    len(_scr) == 1 and ".st-key-cpx_ge_tabla" in _scr[0][1], len(_scr))
at.run()
chk("…y no en la pasada siguiente", len([x for x in at.session_state["_LL"] if x[0] == "script"]) == 1)

print("\n3. ⚠️ Las compras sin obra se ven y se asignan")
at = _app()
chk("el aviso en inglés y sin prometer lo imposible",
    any("2 purchase(s) with no job" in w.value and "assign each one to its job below" in w.value
        for w in at.warning), [w.value for w in at.warning][:1])
_sel = at.selectbox(key="ge_huerf_sel_G-41")
_asg = [b for b in at.button if b.key == "ge_huerf_asg_G-41"][0]
chk("una fila por compra, con su obra por elegir y «Assign» desactivado hasta elegir",
    _sel is not None and _asg.disabled is True)
_sel.set_value("PRJ-1")
at.run()
[b for b in at.button if b.key == "ge_huerf_asg_G-41"][0].click()
at.run()
chk("⚠️ «Assign» escribe (acción diferida) con la obra elegida y el grupo",
    ("asignar", "G-41", "PRJ-1", "G") in at.session_state["_LL"], at.session_state["_LL"])
chk("…y lo dice", any("Purchase G-41 assigned." in s.value for s in at.success), [s.value for s in at.success])

print("\n4, 7, 9-10. Las tablas")
at = _app()
_df = at.dataframe[0] if at.dataframe else None
if _df is not None:
    _v = _df.value
    chk("⚠️ el estado con cabecera y en inglés (no «sobre/pedido/riesgo»)",
        list(_v["Status"]) == ["🟢 ok", "🟢 ok", "🔴 over", "🟠 ordered"], list(_v["Status"]))
    _cfg = _df.proto.columns.replace(" ", "")
    # ⚠️ El formato de CADA columna, no «está en algún sitio»: la 1ª versión buscaba
    # «$%,.2f» en toda la config y Committed lo tiene igual (escapó en romper_v568).
    def _fmt(col):
        _m = re.search(r'"' + re.escape(col) + r'":\{[^}]*?"format":"([^"]+)"', _cfg)
        return _m.group(1) if _m else None
    chk("⚠️ dinero con $ y miles en CADA columna (Cost, Committed, Budget), % con «%»",
        _fmt("Costo") == "$%,.2f" and _fmt("Comprometido") == "$%,.2f"
        and _fmt("Presupuesto") == "$%,.0f" and _fmt("%used") == "%.1f%%"
        and '"Costo":{"label":"Cost"' in _cfg,
        [(c, _fmt(c)) for c in ("Costo", "Comprometido", "Presupuesto", "%used")])
    chk("la previsión: «—» sin avance y «$63,750» con él",
        list(_v["Forecast"]) == ["—", "—", "$63,750", "$18,000"], list(_v["Forecast"]))
    chk("«% used» con un decimal (0.3)", list(_v["% used"])[0] == 0.3, list(_v["% used"]))
_rge = next(n for n in ast.walk(ast.parse(io.open(os.path.join(RAIZ, "core", "projects_ui.py"),
                                                    encoding="utf-8").read()))
            if isinstance(n, ast.FunctionDef) and n.name == "render_group_expenses")
_dfs = [n for n in ast.walk(_rge) if isinstance(n, ast.Call) and ast.unparse(n.func) == "st.dataframe"]
chk("⚠️ las DOS tablas con `single-cell` (un toque abre; antes casilla + «Open»)",
    len(_dfs) == 2 and all(any(k.arg == "selection_mode" and ast.unparse(k.value) == "'single-cell'"
                               for k in d.keywords) for d in _dfs))
at = _app(pre={"ge_tbl_0": {"selection": {"rows": [], "columns": [], "cells": [(2, "Costo")]}}})
chk("⚠️ una celda de la 3ª fila abre ESA obra en Costs",
    at.session_state["_prjsel_pending"] == "PRJ-3" and at.session_state["_prj_sec_pending"] == "💰 Costos"
    and at.session_state["_ge_tbl_gen"] == 1 if "_prjsel_pending" in at.session_state else False)
at = _app(pre={"ge_sin_0": {"selection": {"rows": [], "columns": [], "cells": [(0, "Proyecto")]}}})
chk("⚠️ en la de SIN presupuesto, la obra se abre en Data (para ponérselo)",
    at.session_state["_prjsel_pending"] == "PRJ-5" and at.session_state["_prj_sec_pending"] == "✏️ Datos"
    if "_prjsel_pending" in at.session_state else False)

print("\n5-6. Textos y CSV")
_csv = [n for n in ast.walk(_rge) if isinstance(n, ast.Call) and ast.unparse(n.func) == "st.download_button"]
chk("⚠️ el CSV se llama «expenses_…»", _csv and "expenses_" in ast.unparse(_csv[0]))
_dfcsv = [n for n in ast.walk(_rge) if isinstance(n, ast.Assign)
          and any(getattr(t, "id", "") == "_csv" for t in n.targets)]
_claves = [k.value for d in ast.walk(_dfcsv[0]) if isinstance(d, ast.Dict) for k in d.keys
           if isinstance(k, ast.Constant)] if _dfcsv else []
chk("…con cabeceras en INGLÉS (no «Proyecto/Presupuesto/Avance %/Proyeccion»)",
    _claves == ["Project", "Purchases", "Labour", "Total cost", "Budget", "% used", "Progress %", "Forecast"],
    _claves)
_lit = []
for n in ast.walk(_rge):
    if (isinstance(n, ast.Call) and not ast.unparse(n.func).startswith("logger")
            and ast.unparse(n.func).split(".")[-1] in ("caption", "warning", "info", "error",
                                                        "success", "markdown", "button", "expander")):
        for a in n.args[:1]:
            if (isinstance(a, ast.Constant) and isinstance(a.value, str)
                    and re.search(r"[A-Za-z]{4}", re.sub(r":material/\w+:", "", a.value))
                    and not a.value.lstrip().startswith("<")):
                _lit.append("%d %s" % (n.lineno, ast.unparse(a)[:60]))
            elif isinstance(a, ast.JoinedStr):
                _txt = "".join(v.value for v in a.values if isinstance(v, ast.Constant))
                if re.search(r"[A-Za-z]{4,}\s+[A-Za-z]{2,}", _txt):
                    _lit.append("%d %s" % (n.lineno, ast.unparse(a)[:60]))
chk("⚠️ Expenses sin frases sueltas (avisos, rubros, «Open»…)", not _lit, _lit)
# ⚠️ Por las CADENAS del AST, no por el texto del fichero: la 1ª versión encontró
# «Recibo agregado» en MI comentario explicativo (trampa 2: grep ≠ uso).
_cte_e = [n.value for n in ast.walk(ast.parse(io.open(os.path.join(RAIZ, "core", "expenses.py"),
                                                      encoding="utf-8").read()))
          if isinstance(n, ast.Constant) and isinstance(n.value, str)]
chk("sin «sobre/pedido/riesgo» ni «Recibo agregado»",
    not re.search(r"'(sobre|pedido|riesgo)'", ast.unparse(_rge))
    and not any("Recibo agregado" in c for c in _cte_e))

print("\n12. Disposición (medida en una mini-app con la función real)")
_s = ast.unparse(_rge)
chk("2 por fila bajo 700 px, ocultando las columnas vacías",
    "@container (max-width:700px)" in _s and ":not(:has([data-testid='stButton']))" in _s)
chk("filas fijas de 4 (`st.columns(4)` por tramo)", "st.columns(4)" in _s and "range(0, len(_K), 4)" in _s)

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("TODO OK")
