# -*- coding: utf-8 -*-
"""v570 · LO VISTO VERIFICANDO v569 (decisión del usuario: «Si continua»).

  1. ⚠️ El aviso de una ACCIÓN DIFERIDA salía un clic tarde: la shell pinta los avisos
     (`flash.mostrar`) ANTES de la sección, y anular una factura (v569) o asignar una
     compra sin obra (v568) encolaban el suyo DESPUÉS y no relanzaban. Visto en
     producción: «Invoice voided.» apareció en el clic siguiente, ya en la lista.
     → Barrido de TODA la app: ningún aviso de `flash` sin un `st.rerun()` que se
     ejecute detrás (en su rama, o en quien llama al helper).
     → Y ningún guion de prueba pinta los avisos DESPUÉS de la sección: así es como
     verif_v568 y verif_v569 dieron por bueno lo que en producción fallaba.
  2. ⚠️ La tabla de Invoices daba «Outstanding $44.00» a una ANULADA → $0.
  3. La tabla de facturas de la ficha del cliente era una COPIA que se quedó atrás (ISO,
     «Nº», casillas, dólares truncados, sin vencimiento ni saldo) → es LA de Invoices
     (`invoices_ui.tabla_facturas`), con sus cifras ACTIVAS y su filtro.

AppTest con las fuentes sustituidas: ninguna hoja se toca.
"""
import ast
import glob
import io
import json
import os
import re
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
GUAR = os.path.dirname(os.path.abspath(__file__))
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
print("1. ⚠️ Ningún aviso de `flash` se queda para el clic siguiente")
_FL = {"exito", "aviso", "error", "info", "poner"}


def _es_flash(c):
    f = c.func
    if isinstance(f, ast.Attribute) and f.attr in _FL and isinstance(f.value, ast.Name) and f.value.id == "flash":
        return True
    # `(flash.exito if ok else flash.error)(msg)`
    return isinstance(f, ast.IfExp) and any(isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name)
                                             and x.value.id == "flash" for x in (f.body, f.orelse))


def _es_rerun(s):
    return (isinstance(s, ast.Expr) and isinstance(s.value, ast.Call)
            and isinstance(s.value.func, ast.Attribute) and s.value.func.attr == "rerun")


def _rerun_que_corre(s, amb, linea):
    """Un rerun que SE EJECUTA: incondicional, o en un `if` cuya condición ya estaba
    DECIDIDA al encolar el aviso (`if ok:`), o dentro de un `with`/`try`.
    ⚠️ Uno bajo `if st.button(...)` solo corre si se pulsa ESE botón: con él como prueba,
    los dos fallos pasaban (1ª sonda).
    ⚠️ Y uno bajo `if _sel:` tampoco, si `_sel` se asigna DESPUÉS del aviso (es lo que
    devuelve una tabla que se pinta más abajo): la 2ª sonda —«un `if` sin llamadas»— lo
    daba por bueno y romper_v570 la pilló escapando dos roturas de Invoices."""
    if _es_rerun(s):
        return True
    if isinstance(s, ast.If):
        if any(isinstance(x, ast.Call) for x in ast.walk(s.test)):
            return False
        # lo asignado ENTRE el aviso y este `if` (un `ok` reasignado en otra rama MÁS
        # ABAJO no cuenta: la 3ª sonda miraba toda la función y dio 61 en falso)
        _entre = _asignados(amb, linea, s.lineno)
        if any(isinstance(x, ast.Name) and x.id in _entre for x in ast.walk(s.test)):
            return False
        return any(_rerun_que_corre(b, amb, linea) for b in s.body)
    if isinstance(s, (ast.With, ast.Try)):
        return any(_rerun_que_corre(b, amb, linea) for b in s.body)
    return False


def _asignados(ambito, desde, hasta):
    """Los nombres a los que el ámbito asigna algo entre las líneas `desde` y `hasta`."""
    out = set()
    for x in ast.walk(ambito):
        if not desde < getattr(x, "lineno", 0) < hasta:
            continue
        if isinstance(x, ast.Assign):
            dest = x.targets
        elif isinstance(x, (ast.AugAssign, ast.AnnAssign, ast.NamedExpr, ast.For)):
            dest = [x.target]
        else:
            continue
        out |= {nn.id for d in dest for nn in ast.walk(d) if isinstance(nn, ast.Name)}
    return out


def _tras(n, par):
    """(True, None) si detrás del statement de `n` —en su lista o en la de un ancestro,
    hasta la función— hay un rerun que corre; si no, (False, la función)."""
    while not isinstance(n, ast.stmt):
        n = par[n]
    _amb, _l0 = n, n.lineno
    while par.get(_amb) is not None and not isinstance(_amb, (ast.FunctionDef, ast.AsyncFunctionDef)):
        _amb = par[_amb]
    while True:
        pa = par.get(n)
        if pa is None:
            return False, None
        for campo in ("body", "orelse", "finalbody"):
            lst = getattr(pa, campo, None)
            if isinstance(lst, list) and n in lst:
                if any(_rerun_que_corre(s, _amb, _l0) for s in lst[lst.index(n) + 1:]):
                    return True, None
                break
        if isinstance(pa, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return False, pa
        n = pa


def barrido(fuentes):
    """{(fichero, función): [líneas]} de los avisos que se pintarían un clic tarde.
    Se libran: los `on_change`/`on_click` (corren ANTES del cuerpo, y la cola se pinta
    en esa misma pasada) y los helpers cuyos llamadores relanzan todos detrás."""
    arb = {}
    for p, src in fuentes.items():
        t = ast.parse(src)
        arb[p] = (t, {ch: n for n in ast.walk(t) for ch in ast.iter_child_nodes(n)})
    callbacks = set()
    for t, _ in arb.values():
        for c in ast.walk(t):
            if isinstance(c, ast.Call):
                for k in c.keywords:
                    if k.arg in ("on_change", "on_click") and isinstance(k.value, (ast.Name, ast.Attribute)):
                        callbacks.add(k.value.id if isinstance(k.value, ast.Name) else k.value.attr)

    def llamadas_a(nombre):
        out = []
        for t, par in arb.values():
            for c in ast.walk(t):
                if isinstance(c, ast.Call):
                    f = c.func
                    nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
                    if nm == nombre:
                        out.append((c, par))
        return out
    malos = {}
    for p, (t, par) in arb.items():
        for c in [n for n in ast.walk(t) if isinstance(n, ast.Call) and _es_flash(n)]:
            ok, fn = _tras(c, par)
            if ok:
                continue
            if fn is not None:
                if fn.name in callbacks:
                    continue
                ll = llamadas_a(fn.name)
                if ll and all(_tras(cc, pp)[0] for cc, pp in ll):
                    continue
            malos.setdefault((os.path.basename(p), fn.name if fn else "<módulo>"), []).append(c.lineno)
    return malos


# ⚠️ Trampa 12: una sonda NEGATIVA no vale hasta ver que SABE ver el caso malo.
_CASOS = {"m.py": '''
def diferida():
    x = st.session_state.pop("_a", None)
    if x:
        ok, msg = hacer(x)
        (flash.exito if ok else flash.error)(msg)
    if st.button("otra"):
        st.rerun()
def diferida_sel():
    x = st.session_state.pop("_a", None)
    if x:
        ok, msg = hacer(x)
        (flash.exito if ok else flash.error)(msg)
    _sel = tabla()
    if _sel:
        st.rerun()
def bien():
    if st.button("b"):
        flash.exito("b")
        st.rerun()
def bien_si_ok():
    ok, msg = hacer(1)
    (flash.exito if ok else st.error)(msg)
    if ok:
        st.rerun()
def helper():
    flash.aviso("h")
def llama():
    if st.button("c"):
        helper()
        st.rerun()
def cb():
    flash.exito("cb")
st.radio("r", [1], on_change=cb)
'''}
_m = barrido(_CASOS)
chk("la sonda VE los casos malos (rerun bajo OTRO botón, o bajo lo que una tabla devuelve "
    "DESPUÉS) y solo esos", sorted(_m) == [("m.py", "diferida"), ("m.py", "diferida_sel")], _m)

_FUENTES = {p: io.open(p, encoding="utf-8").read() for p in sorted(glob.glob(os.path.join("core", "*.py")))}
_FUENTES["app.py"] = io.open("app.py", encoding="utf-8").read()
_malos = barrido(_FUENTES)
# `xero_ui.procesar_retorno` se llama desde app.py ANTES de la shell → su cola se pinta
# en esa misma pasada. Se libra solo mientras ese orden siga siendo verdad (derivado).
_app = ast.parse(_FUENTES["app.py"])


def _linea(nombre):
    return min((n.lineno for n in ast.walk(_app) if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute) and n.func.attr == nombre), default=None)


_l_ret, _l_shell = _linea("procesar_retorno"), _linea("render_admin_content")
chk("app.py procesa el retorno de Xero ANTES de pintar la shell (su excepción se deriva)",
    bool(_l_ret and _l_shell) and _l_ret < _l_shell, (_l_ret, _l_shell))
if _l_ret and _l_shell and _l_ret < _l_shell:
    _malos.pop(("xero_ui.py", "procesar_retorno"), None)
chk("⚠️ ningún aviso de `flash` sin un `st.rerun()` que se ejecute detrás (toda la app)",
    not _malos, _malos)
chk("…y los dos de producción relanzan: anular (Invoices) y asignar (Expenses)",
    ("invoices_ui.py", "render_facturas") not in _malos
    and ("projects_ui.py", "render_group_expenses") not in _malos
    and "_fac_anular" in _FUENTES[os.path.join("core", "invoices_ui.py")]
    and "_ge_asignar" in _FUENTES[os.path.join("core", "projects_ui.py")])

print("\n   …y ningún guion de prueba pinta los avisos DESPUÉS de la sección")
_SEC = re.compile(r"\.(render_\w+|_panel_\w+)\(")
_mal_orden, _vistos = [], 0
for g in sorted(glob.glob(os.path.join(GUAR, "verif_v*.py"))):
    try:
        _t = ast.parse(io.open(g, encoding="utf-8").read())
    except SyntaxError:
        continue
    for n in ast.walk(_t):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and "flash.mostrar()" in n.value:
            _s = n.value
            _m1 = _SEC.search(_s)
            if not _m1:
                continue
            _vistos += 1
            if _s.index("flash.mostrar()") > _m1.start():
                _mal_orden.append(os.path.basename(g))
chk("⚠️ los guiones que pintan una sección + avisos los pintan ANTES (como la shell)",
    _vistos >= 5 and not _mal_orden, (_vistos, _mal_orden))

# ══════════════════════════════════════════════════════════════════════════════
from streamlit.testing.v1 import AppTest                                    # noqa: E402

DATOS = r'''
import datetime as dt
import json
import streamlit as st
from core import invoices as I, clientes as C, clock
clock.today = lambda *a, **k: dt.date(2026, 10, 13)
def _f(fid, num, tot, cob, fecha, venc, status="emitida"):
    return {"ID": fid, "Group": "G", "ClientID": "CLI-1", "ClientName": "Cliente Uno", "Number": num,
            "Date": fecha, "ExpiryDate": venc, "Total": str(tot), "Subtotal": str(round(tot / 1.1, 2)),
            "TaxPct": "10", "Tax": str(round(tot - tot / 1.1, 2)), "Collected": str(cob),
            "Status": status, "Note": "", "Created": fecha + " 10:00:00", "LinesJSON": "[]",
            "CollectionsJSON": "[]"}
_FAC = [_f("FAC-1", "0001", 110.4, 50, "2026-10-13", "2026-10-27"),
        _f("FAC-2", "0002", 44, 0, "2026-09-19", "2026-10-03", status="anulada"),
        _f("FAC-3", "0003", 22, 0, "2026-09-23", "2026-10-07")]
I.is_configured = lambda: True
I.list_facturas = lambda g=None, cliente_id=None: [dict(x) for x in _FAC]
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G",
                                     "nombre": "Jefa"})
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    for _k, _v in (st.session_state.get("_PRE") or {}).items():
        st.session_state[_k] = _v
'''
G_LISTA = DATOS + r'''
from core import flash, invoices_ui as IU
flash.mostrar()
IU.render_facturas("G")
'''
G_CLI = DATOS + r'''
from core import flash, clientes_ui as CU, projects as P, alerts, expenses
C.list_clientes = lambda g=None, **k: [{"ID": "CLI-1", "Name": "Cliente Uno", "Group": "G"}]
C.get_cliente = lambda cid: {"ID": cid, "Name": "Cliente Uno", "Active": "SI"}
C.es_del_cliente = lambda p, cid, cn: False
P.list_projects = lambda *a, **k: []
P.project_hours_bulk = lambda g: {}
alerts.is_configured = lambda: False
expenses.is_configured = lambda: False
flash.mostrar()
CU._detalle_cliente("G", "cliente uno")
'''

print("\n2. ⚠️ Una ANULADA no debe nada en la tabla de Invoices")
at = AppTest.from_string(G_LISTA, default_timeout=90)
at.run()
chk("la lista se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_v = at.dataframe[0].value
_sal = dict(zip(_v["Nº"], _v["Outstanding"]))
chk("⚠️ «Outstanding» de la anulada 0002 = 0 (decía 44.00); las otras, su saldo",
    _sal.get("0002") == 0.0 and _sal.get("0001") == 60.4 and _sal.get("0003") == 22.0, _sal)

print("\n3. La ficha del cliente: la MISMA tabla, cifras activas y filtro")
at = AppTest.from_string(G_CLI, default_timeout=90)
at.run()
chk("la ficha se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_kb = {b.key: b.label for b in at.button}
chk("⚠️ 4 cifras-BOTÓN (eran `st.metric`, sin tocar)",
    [k for k in _kb if str(k).startswith("cpxkpi_clf_")] ==
    ["cpxkpi_clf_fac", "cpxkpi_clf_cob", "cpxkpi_clf_pen", "cpxkpi_clf_ven"]
    and not [m for m in at.metric if m.label in ("Invoiced", "Overdue")], list(_kb))
chk("…sin céntimos y sin la anulada: Invoiced $132 (110.40 + 22), Overdue $22",
    "\n\n\\$132\n\n" in _kb.get("cpxkpi_clf_fac", "") and "\n\n\\$22\n\n" in _kb.get("cpxkpi_clf_ven", ""),
    (_kb.get("cpxkpi_clf_fac"), _kb.get("cpxkpi_clf_ven")))
chk("…en 2 por fila bajo 700 px (su propio recuadro)",
    any(".st-key-cpx_clf_kpis{container-type:inline-size}" in m.value for m in at.markdown))
_df = at.dataframe[0]
_v = _df.value
chk("⚠️ las columnas de Invoices, sin la del cliente (es SU ficha)",
    list(_v.columns) == ["Nº", "Estado", "Outstanding", "Vence", "Total", "Cobrado", "Fecha"], list(_v.columns))
chk("⚠️ fechas DD/MM/YYYY (salía «2026-09-23»)",
    "23/09/2026" in list(_v["Fecha"]) and "07/10/2026" in list(_v["Vence"]), list(_v["Fecha"]))
chk("estado con punto («🔴 overdue», «⚫ voided»)", {"🔴 overdue", "⚫ voided", "🟠 partial"} == set(_v["Estado"]),
    set(_v["Estado"]))
_cj = json.loads(_df.proto.columns)
chk("⚠️ «No.» fijado y dinero con céntimos (era «Nº» y `$%,d`, que TRUNCA)",
    _cj.get("Nº", {}).get("label") == "No." and _cj.get("Nº", {}).get("pinned") is True
    and all(_cj.get(c, {}).get("type_config", {}).get("format") == "$%,.2f"
            for c in ("Total", "Cobrado", "Outstanding")),
    {k: _cj.get(k) for k in ("Nº", "Total")})
_enum = _df.proto.DESCRIPTOR.fields_by_name["selection_mode"].enum_type
_modos = [_enum.values_by_number[v].name for v in _df.proto.selection_mode]
chk("⚠️ un toque en CUALQUIER celda (era la casilla)", _modos == ["SINGLE_CELL"], _modos)
[b for b in at.button if b.key == "cpxkpi_clf_ven"][0].click()
at.run()
chk("⚠️ «Overdue» filtra SU tabla (solo la 0003) y lo recuerda por cliente",
    at.session_state["cpxseg_clf_filt_CLI-1"] == "Vencidas"
    and list(at.dataframe[0].value["Nº"]) == ["0003"], list(at.dataframe[0].value["Nº"]))
_rd = [r for r in at.radio if r.key == "cpxseg_clf_filt_CLI-1"]
chk("…con el mismo selector que Invoices (All · Outstanding · Overdue · Collected · Voided)",
    _rd and list(_rd[0].options) == ["All", "Outstanding", "Overdue", "Collected", "Voided"],
    _rd[0].options if _rd else None)
[b for b in at.button if b.key == "cpxkpi_clf_cob"][0].click()
at.run()
chk("«Collected» sin ninguna: «No invoices in this filter.»",
    any("No invoices in this filter." in c.value for c in at.caption) and not at.dataframe)
at = AppTest.from_string(G_CLI, default_timeout=90)
at.session_state["_PRE"] = {"cli_facs_CLI-1_0": {"selection": {"rows": [], "columns": [],
                                                                 "cells": [(1, "Fecha")]}}}
at.run()
chk("⚠️ tocar la 2ª fila (0003: van por fecha de alta, la más nueva arriba) abre ESA factura en Invoices",
    at.session_state["_fac_open"] == "FAC-3"
    and at.session_state["_admin_nav_pending"] == ("finanzas", "🧾 Facturas")
    and at.session_state["_cli_facs_CLI-1_gen"] == 1
    if "_fac_open" in at.session_state else False)

print("\n   …y la ficha ya no tiene tabla propia")
# ⚠️ Por el AST de `_detalle_cliente`: la 1ª sonda buscaba «$%,d» en TODO el módulo y la
# columna «Cost» de la LISTA de clientes también lo lleva (rojo con la ficha bien).
_dc = next(n for n in ast.walk(ast.parse(_FUENTES[os.path.join("core", "clientes_ui.py")]))
           if isinstance(n, ast.FunctionDef) and n.name == "_detalle_cliente")
_ll = [ast.unparse(n.func) for n in ast.walk(_dc) if isinstance(n, ast.Call)]
chk("la ficha usa los tres helpers de Invoices y ya no arma tabla propia",
    all(x in _ll for x in ("IU.cifras_cobro", "IU.filtrar", "IU.tabla_facturas"))
    and "st.dataframe" not in _ll and not any(x.endswith("estado_cobro") for x in _ll), _ll[-12:])

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("TODO OK")
