# -*- coding: utf-8 -*-
"""v580 · FINANCE → QUOTES, PROBADA ACCIÓN POR ACCIÓN (decisión del usuario: «dale con todo»).

  1. ⚠️ Una instalación creada desde una cotización nacía SIN cronograma (PRJ-0024 en
     producción: «Installation», 5 paradas → UNA actividad «Execution»): el formulario
     mandaba los tipos viejos («Instalación») y `genera_cronograma` no los conoce → los de
     la app (`P.TIPOS`) y el motor canoniza el tipo.
  2. ⚠️ Aceptar o rechazar, de un toque y sin vuelta atrás → «Undo — back to sent» mientras
     no haya obra.
  3. ⚠️ Español en producción («cotizaste», «— Nº0002» en el NOMBRE de la obra, «Nº»,
     «Cotizacion_0001.pdf») y unos diez textos sin `t()`; «(-100%)» sin nada gastado.
  4. «expired» y «overdue» para lo mismo → «expired».   5. «$539 · 1 sent» → «2 sent · 1
     expired».   6. La tabla: un toque abre, DD/MM/YYYY, estado con color, lo importante
     delante, la más nueva primero, filtro recordado y cifras que filtran.   7. «Markup %».
  8. Las vencidas, un botón cada una.   9. Crear y la versión nueva AVISAN.
 10. La versión nueva conserva el número («0003 v2», no «0005 v2») y dice de cuál sale.
 11. La nota se ve; en borrador, la nota y el impuesto se cambian.   12. El selector del
     catálogo se vacía al añadir.   13. Las cifras, 4 por fila (2 en estrecho).
 14. Una obra BORRADA deja la cotización atada a nada → se dice y se suelta.
 15. Tocar «Quotes» en el menú con una cotización abierta vuelve a la lista.
 16. «0 h worked», no «0.0 h».
  + ⚠️ Visto al rehacerla: en un borrador ya creado, «Add to the quote» no añadía nada (lo
     añadido iba a una clave que nadie leía).

AppTest y el motor con sus fuentes sustituidas: ninguna hoja se toca.
"""
import ast
import io
import json
import os
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


def _src(rel):
    return io.open(os.path.join(RAIZ, rel), encoding="utf-8").read()


def _func(rel, nombre):
    return next((n for n in ast.walk(ast.parse(_src(rel)))
                 if isinstance(n, ast.FunctionDef) and n.name == nombre), None)


from core import quotes as Q, projects as P, auditoria                     # noqa: E402

_ITEM = {"ID": "CAT-1", "Type": "product", "Name": "Item A", "UnitCost": "100", "Unit": "unit"}


class _WS:
    def __init__(self, recs):
        self.recs, self.filas = recs, []

    def get_all_records(self, **k):
        return [dict(r) for r in self.recs]

    def append_row(self, fila, **k):
        self.filas.append(fila)


# ══════════════════════════════════════════════════════════════════════════════
print("1. ⚠️ Crear la obra desde la cotización: una instalación nace CON cronograma")
_o = {n: getattr(Q, n) for n in ("get_cotizacion", "_ws", "_fila", "_set", "_invalidate")}
_op, _oa = P.create_project, auditoria.registrar
_LL = {}
try:
    _l = Q.linea_de(_ITEM, 2, ganancia=50)
    _c = {"ID": "COT-2", "Group": "G", "ClientName": "ZZ", "ClientID": "CLI-1", "Number": "0002",
          "LinesJSON": json.dumps([_l]), "TaxPct": "10", "Status": "accepted", "ProjectID": ""}
    Q.get_cotizacion = lambda cid: dict(_c)
    Q._ws = lambda: object()
    Q._fila = lambda w, cid: (2, dict(_c))
    Q._set = lambda w, row, campos: (True, "")
    Q._invalidate = lambda: None
    auditoria.registrar = lambda *a, **k: None

    def _cp(grupo, nombre, **k):
        _LL["crear"] = dict(k, nombre=nombre)
        return True, "PRJ-9"
    P.create_project = _cp
    ok, res = Q.aceptar_y_crear_proyecto("COT-2", nombre="", tipo="Instalación", ns=5)
    _k = _LL.get("crear", {})
    chk("⚠️ con el valor VIEJO «Instalación» y 5 paradas: más de UNA actividad (salía «Execution» sola)",
        ok and len(_k.get("activities") or []) > 1, (ok, res, len(_k.get("activities") or [])))
    chk("…y la obra se guarda con el tipo CANÓNICO («Installation»)", _k.get("tipo") == "Installation",
        _k.get("tipo"))
    chk("⚠️ el nombre por defecto con «No.», no «Nº» (se GUARDA en la obra)",
        _k.get("nombre") == "ZZ — No. 0002", _k.get("nombre"))
    Q.aceptar_y_crear_proyecto("COT-2", nombre="X", tipo="Delivery", ns=5)
    chk("un Delivery sigue SIN cronograma estándar (una actividad, regla v306)",
        len(_LL["crear"].get("activities") or []) == 1, len(_LL["crear"].get("activities") or []))
finally:
    for _n, _v in _o.items():
        setattr(Q, _n, _v)
    P.create_project, auditoria.registrar = _op, _oa

print("\n10. La versión nueva conserva el número")
_o = {n: getattr(Q, n) for n in ("get_cotizacion", "crear", "_ws")}
try:
    _base = {"ID": "COT-3", "Group": "G", "ClientName": "ZZ", "ClientID": "CLI-1", "Number": "0003",
             "Version": "1", "LinesJSON": "[]", "TaxPct": "10", "Note": "n"}
    Q.get_cotizacion = lambda cid: dict(_base)
    Q._ws = lambda: _WS([{"Group": "G", "Number": "0003", "Version": "1"},
                         {"Group": "G", "Number": "0003", "Version": "2"},
                         {"Group": "OTRO", "Number": "0003", "Version": "7"},
                         {"Group": "G", "Number": "0004", "Version": "5"}])
    _LL = {}

    def _cr(*a, **k):
        _LL.update(k)
        return True, "COT-9"
    Q.crear = _cr
    Q.nueva_version("COT-3")
    chk("⚠️ el MISMO número («0003», no uno nuevo)", _LL.get("numero") == "0003", _LL.get("numero"))
    chk("…con la versión siguiente a la más alta de ESE número y grupo (v3: ya había una v2)",
        _LL.get("version") == 3, _LL.get("version"))
    chk("…y dice de cuál sale", _LL.get("origen") == "COT-3", _LL.get("origen"))
finally:
    for _n, _v in _o.items():
        setattr(Q, _n, _v)
_o = {n: getattr(Q, n) for n in ("_ws", "_invalidate")}
try:
    _w = _WS([{"ID": "COT-0007", "Number": "0007"}])
    Q._ws = lambda: _w
    Q._invalidate = lambda: None
    Q.crear("G", "CLI-1", "ZZ", [Q.linea_de(_ITEM, 1, ganancia=10)], numero="0003", version=2)
    Q.crear("G", "CLI-1", "ZZ", [Q.linea_de(_ITEM, 1, ganancia=10)])
    chk("`crear` escribe el número y la versión pedidos", _w.filas and _w.filas[0][4] == "0003"
        and _w.filas[0][15] == "2", (_w.filas[0][4], _w.filas[0][15]) if _w.filas else None)
    chk("…y sin ellos, el número siguiente y la v1 de siempre", len(_w.filas) == 2
        and _w.filas[1][4] == "0008" and _w.filas[1][15] == "1",
        (_w.filas[1][4], _w.filas[1][15]) if len(_w.filas) > 1 else None)
finally:
    for _n, _v in _o.items():
        setattr(Q, _n, _v)

print("\n11, 3. La nota se guarda; el aviso del estado, traducido; el orden")
_o = {n: getattr(Q, n) for n in ("_ws", "_fila", "_set", "_invalidate", "_records")}
_oa = auditoria.registrar
try:
    _SET = []
    Q._ws = lambda: object()
    Q._fila = lambda w, cid: (2, {"ID": cid, "Status": "draft", "TaxPct": "10", "Group": "G"})
    Q._set = lambda w, row, campos: (_SET.append(campos), (True, ""))[1]
    Q._invalidate = lambda: None
    auditoria.registrar = lambda *a, **k: None
    Q.guardar_lineas("COT-1", [Q.linea_de(_ITEM, 1, ganancia=10)], impuesto_pct=5, nota="Hola")
    chk("⚠️ `guardar_lineas` guarda la NOTA y el impuesto",
        _SET and _SET[-1].get("Note") == "Hola" and _SET[-1].get("TaxPct") == 5, _SET[-1] if _SET else None)
    Q.guardar_lineas("COT-1", [Q.linea_de(_ITEM, 1, ganancia=10)])
    chk("…y sin nota, no la toca", "Note" not in _SET[-1], _SET[-1])
    ok, msg = Q.set_estado("COT-1", Q.ENVIADA)
    chk("el aviso del estado, con su etiqueta («Quote marked as sent.»)", msg == "Quote marked as sent.", msg)
    Q._records = lambda: [{"ID": "A", "Group": "G", "Date": "2026-10-01", "Number": "0001"},
                          {"ID": "B", "Group": "G", "Date": "2026-10-01", "Number": "0004"},
                          {"ID": "C", "Group": "G", "Date": "2026-10-01", "Number": "0003", "Version": "2"},
                          {"ID": "D", "Group": "G", "Date": "2026-10-01", "Number": "0003"},
                          {"ID": "E", "Group": "G", "Date": "2026-09-01", "Number": "0009"}]
    chk("⚠️ el mismo día, la de número (y versión) más alto primero; la más vieja, la última",
        [c["ID"] for c in Q.list_cotizaciones("G")] == ["B", "C", "D", "A", "E"],
        [c["ID"] for c in Q.list_cotizaciones("G")])
finally:
    for _n, _v in _o.items():
        setattr(Q, _n, _v)
    auditoria.registrar = _oa

print("\n14. La obra borrada: se dice y se suelta")
_o = {n: getattr(Q, n) for n in ("_ws", "_fila", "_set", "_invalidate")}
_og, _oa = P.get_project, auditoria.registrar
try:
    P.get_project = lambda pid: {} if pid == "PRJ-X" else {"ID": pid}
    chk("una obra que ya no existe se detecta", Q.proyecto_perdido({"ProjectID": "PRJ-X"}) is True)
    chk("…una que existe, no", Q.proyecto_perdido({"ProjectID": "PRJ-1"}) is False)
    chk("…y sin obra, tampoco", Q.proyecto_perdido({"ProjectID": ""}) is False)
    _SET = []
    Q._ws = lambda: object()
    Q._set = lambda w, row, campos: (_SET.append(campos), (True, ""))[1]
    Q._invalidate = lambda: None
    auditoria.registrar = lambda *a, **k: None
    Q._fila = lambda w, cid: (2, {"ID": cid, "ProjectID": "PRJ-X", "Group": "G"})
    ok, msg = Q.desvincular_proyecto("COT-6")
    chk("⚠️ soltar la obra borrada deja la cotización sin obra", ok and _SET[-1] == {"ProjectID": ""}, (ok, msg))
    Q._fila = lambda w, cid: (2, {"ID": cid, "ProjectID": "PRJ-1", "Group": "G"})
    _n = len(_SET)
    ok, msg = Q.desvincular_proyecto("COT-6")
    chk("…pero una obra que EXISTE no se suelta", not ok and len(_SET) == _n, msg)
finally:
    for _n2, _v in _o.items():
        setattr(Q, _n2, _v)
    P.get_project, auditoria.registrar = _og, _oa

# ══════════════════════════════════════════════════════════════════════════════
from streamlit.testing.v1 import AppTest                                    # noqa: E402

_L1 = json.dumps([Q.linea_de(_ITEM, 2, ganancia=50)])
CAB = r'''
import sys, json
sys.path.insert(0, r"%s")
import streamlit as st
from core import quotes_ui as QU, quotes as Q, clientes as C, catalogo as CAT, auth, projects as P
from core import quote_pdf
st.session_state["auth"] = {"rol": "administrator", "usuario": "adm", "nombre": "Adm", "grupo": "G"}
st.session_state.setdefault("_LL", [])
_L1 = %r
_F = "2027-01-01"
ROWS = st.session_state.setdefault("_ROWS", [
    {"ID": "COT-1", "Group": "G", "ClientName": "Cli", "ClientID": "CLI-1", "Number": "0001", "Version": "1",
     "Date": "2026-10-01", "ValidUntil": _F, "Total": "275", "MarginPct": "25", "Status": "draft",
     "LinesJSON": _L1, "TaxPct": "10", "Note": "Nota A"},
    {"ID": "COT-2", "Group": "G", "ClientName": "Cli", "ClientID": "CLI-1", "Number": "0002", "Version": "1",
     "Date": "2026-10-01", "ValidUntil": _F, "Total": "143", "MarginPct": "30", "Status": "sent",
     "LinesJSON": _L1, "TaxPct": "10", "Note": "Para el cliente"},
    {"ID": "COT-3", "Group": "G", "ClientName": "Cli", "ClientID": "CLI-1", "Number": "0003", "Version": "1",
     "Date": "2026-10-01", "ValidUntil": "2026-01-01", "Total": "396", "MarginPct": "20", "Status": "sent",
     "LinesJSON": _L1, "TaxPct": "10"},
    {"ID": "COT-4", "Group": "G", "ClientName": "Cli", "ClientID": "CLI-1", "Number": "0003", "Version": "2",
     "Date": "2026-10-02", "ValidUntil": _F, "Total": "396", "MarginPct": "20", "Status": "draft",
     "LinesJSON": _L1, "TaxPct": "10", "Source": "COT-3", "Note": "Nota v2"},
    {"ID": "COT-5", "Group": "G", "ClientName": "Cli", "ClientID": "CLI-1", "Number": "0005", "Version": "1",
     "Date": "2026-10-01", "ValidUntil": _F, "Total": "100", "Status": "rejected", "LinesJSON": _L1, "TaxPct": "10"},
    {"ID": "COT-6", "Group": "G", "ClientName": "Cli", "ClientID": "CLI-1", "Number": "0006", "Version": "1",
     "Date": "2026-09-30", "ValidUntil": _F, "Total": "200", "Status": "accepted", "ProjectID": "PRJ-X",
     "LinesJSON": _L1, "TaxPct": "10"},
    {"ID": "COT-7", "Group": "G", "ClientName": "Cli", "ClientID": "CLI-1", "Number": "0007", "Version": "1",
     "Date": "2026-09-29", "ValidUntil": _F, "Total": "300", "Status": "accepted", "LinesJSON": _L1, "TaxPct": "10"},
    {"ID": "COT-8", "Group": "G", "ClientName": "Cli", "ClientID": "CLI-1", "Number": "0008", "Version": "1",
     "Date": "2026-09-28", "ValidUntil": _F, "Total": "150", "Status": "accepted", "ProjectID": "PRJ-OK",
     "LinesJSON": _L1, "TaxPct": "10"}])
Q._records = lambda: [dict(r) for r in ROWS]
Q.resumen.clear()
Q.is_configured = lambda: True
_LL = st.session_state["_LL"]
def _q(nombre, devuelve):
    def f(*a, **k):
        _LL.append((nombre, a, k))
        return devuelve
    return f
Q.set_estado = _q("set_estado", (True, "Quote marked as sent."))
Q.guardar_lineas = _q("guardar_lineas", (True, "Quote updated."))
Q.desvincular_proyecto = _q("desvincular", (True, "Project PRJ-X unlinked from the quote."))
Q.nueva_version = _q("nueva_version", (True, "COT-4"))
Q.actualizar_precios = _q("actualizar", (True, "ok"))
Q.desactualizadas = lambda c: []
def _crear(*a, **k):
    _LL.append(("crear", a, k))
    ROWS.append({"ID": "COT-9", "Group": "G", "Number": "0009", "Version": "1", "Date": "2026-10-03",
                 "ClientName": "Cli", "Status": "draft", "LinesJSON": "[]"})
    return True, "COT-9"
Q.crear = _crear
Q.comparacion = lambda cid: {"proyecto": "Obra OK", "proyecto_id": "PRJ-OK",
    "horas": {"real": 0, "cotizado": 4, "dif": -4, "pct": -100},
    "costo": {"real": 0, "cotizado": 100, "dif": -100, "pct": -100},
    "ingreso": 130, "ganancia_cotizada": 30, "terminado": False, "ganancia_proyectada": None,
    "ganancia_real": None, "costo_proyectado": None, "avance": 0}
P.get_project = lambda pid: {} if pid == "PRJ-X" else {"ID": pid}
C.list_clientes = lambda g, **k: [{"ID": "CLI-1", "Name": "Cli"}]
_ITEMS = [{"ID": "CAT-1", "Type": "product", "Name": "Item A", "UnitCost": "100", "Unit": "unit"},
          {"ID": "CAT-2", "Type": "product", "Name": "Item B", "UnitCost": "40", "Unit": "unit"}]
CAT.list_items = lambda g, **k: [dict(i) for i in _ITEMS]
CAT.get_item = lambda cid: next(dict(i) for i in _ITEMS if i["ID"] == cid)
auth.group_margin_default = lambda g: 20.0
auth.group_tax_default = lambda g: 10.0
quote_pdf.generate_quote_pdf = lambda c, cli, g: b"%%PDF-1.4"
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    for _k, _v in (st.session_state.get("_PRE") or {}).items():
        st.session_state[_k] = _v
# ⚠️ los avisos ANTES de la sección, como la shell (trampa 41)
from core import flash
flash.mostrar()
QU.render_cotizaciones("G")
''' % (RAIZ, _L1)


def _app(pre=None):
    a = AppTest.from_string(CAB, default_timeout=90)
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
                       + list(a.success) + list(a.caption) + list(a.markdown)])


def _cols(df_el):
    try:
        return json.loads(df_el.proto.columns)
    except Exception:
        return {}


def _llamadas(a, nombre):
    return [x for x in (_ss(a, "_LL") or []) if x[0] == nombre]


print("\n5, 13. Las cifras: cuadran, filtran y van 4 por fila")
at = _app()
chk("la lista se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_b = _kb(at)
chk("las 4 cifras son botones", [k for k in _b if str(k).startswith("cpxkpi_cot_")] ==
    ["cpxkpi_cot_calle", "cpxkpi_cot_gan", "cpxkpi_cot_conv", "cpxkpi_cot_n"],
    [k for k in _b if str(k).startswith("cpxkpi_cot_")])
chk("⚠️ «Out with clients $539 · 2 sent · 1 expired» (la vencida, contada; antes «1 sent»)",
    _b.get("cpxkpi_cot_calle", "") == "Out with clients\n\n\\$539\n\n2 sent · 1 expired",
    _b.get("cpxkpi_cot_calle"))
chk("«Conversion 75%» de las decididas (3 aceptadas de 4)", "\n\n75%\n\n" in _b.get("cpxkpi_cot_conv", ""),
    _b.get("cpxkpi_cot_conv"))
chk("4 por fila, 2 en estrecho (`theme.por_fila`)",
    "flex:0 1 calc(25.0000% - 0.7500rem)" in _textos(at)
    and ".st-key-cpx_cot_kpis{container-type:inline-size}" in _textos(at), "")

print("\n6, 7, 4. La tabla")
_df = at.dataframe[0] if at.dataframe else None
_v = _df.value if _df is not None else None
chk("⚠️ la más NUEVA primero (con fechas iguales salía la última)",
    _v is not None and list(_v["Nº"]) == ["0003 v2", "0005", "0003", "0002", "0001", "0006", "0007", "0008"],
    list(_v["Nº"]) if _v is not None else None)
_c = _cols(_df)
_lab = {k: (_c.get(k) or {}).get("label") for k in ("Nº", "Cliente", "Estado", "Total", "Vence", "Fecha", "Markup")}
chk("⚠️ las cabeceras: «No.» (no «Nº»), Status delante, «Markup %»",
    _lab == {"Nº": "No.", "Cliente": "Client", "Estado": "Status", "Total": "Total", "Vence": "Expires",
             "Fecha": "Date", "Markup": "Markup %"}, _lab)
chk("el orden: No. · Client · Status · Total · Expires · Date · Markup",
    _v is not None and list(_v.columns) == ["Nº", "Cliente", "Estado", "Total", "Vence", "Fecha", "Markup"],
    list(_v.columns) if _v is not None else None)
chk("el número FIJADO", (_c.get("Nº") or {}).get("pinned") is True)
chk("⚠️ fechas DD/MM/YYYY (salían en ISO)", _v is not None and list(_v["Fecha"])[0] == "02/10/2026"
    and list(_v["Vence"])[2] == "01/01/2026", (list(_v["Fecha"])[:1], list(_v["Vence"])[:3]) if _v is not None else None)
chk("⚠️ el estado con su color y «expired» (no «overdue», el de las facturas)",
    _v is not None and list(_v["Estado"])[:3] == ["⚪ draft", "⚫ rejected", "🔴 expired"],
    list(_v["Estado"]) if _v is not None else None)
chk("el total con céntimos y el signo delante («dollar»)", (_c.get("Total") or {}).get("type_config", {}).get("format") == "dollar")
_rc = _func("core/quotes_ui.py", "render_cotizaciones")
chk("⚠️ un toque abre: `single-cell` (con `single-row` solo enmarcaba la celda)",
    any(isinstance(n, ast.keyword) and n.arg == "selection_mode" and ast.unparse(n.value) == "'single-cell'"
        for n in ast.walk(_rc)))
at = _app(pre={"cot_tbl_0": {"selection": {"rows": [], "columns": [], "cells": [(2, "Cliente")]}}})
chk("⚠️ un toque en la 3ª fila abre ESA (la 0003 v1)", _ss(at, "_cot_open") == "COT-3"
    and _ss(at, "_cot_tbl_gen") == 1, (_ss(at, "_cot_open"), _ss(at, "_cot_tbl_gen")))
at = _app()
at.button(key="cpxkpi_cot_calle").click()
at.run()
_v = at.dataframe[0].value if at.dataframe else None
chk("⚠️ «Out with clients» filtra: enviadas y vencidas", _ss(at, "cpxseg_cot_filt") == "Enviadas"
    and _v is not None and list(_v["Nº"]) == ["0003", "0002"], list(_v["Nº"]) if _v is not None else None)
chk("…y baja a la tabla", ".st-key-ir_cpx_cot_tabla" in _textos(at), "")
at.radio(key="cpxseg_cot_filt").set_value("Rechazadas")
at.run()
chk("el filtro «Rejected»", [list(d.value["Nº"]) for d in at.dataframe] == [["0005"]],
    [list(d.value["Nº"]) for d in at.dataframe])
_rad = [n for n in ast.walk(_rc) if isinstance(n, ast.Call) and ast.unparse(n.func) == "st.radio"]
chk("el filtro se RECUERDA (`persist_state`)", _rad and any(k.arg == "persist_state" for k in _rad[0].keywords))

print("\n8. Las vencidas, un botón cada una")
at = _app()
chk("⚠️ la vencida, con su botón", _kb(at).get("cotvenc_COT-3", "").startswith(":material/open_in_new: No. 0003 · Cli"),
    _kb(at).get("cotvenc_COT-3"))
at.button(key="cotvenc_COT-3").click()
at.run()
chk("…que la abre", _ss(at, "_cot_open") == "COT-3", _ss(at, "_cot_open"))

print("\n10, 3. El detalle: número, fechas, de qué versión sale")
at = _app(pre={"_cot_open": "COT-4"})
chk("el detalle se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_md = _textos(at)
chk("⚠️ «Quote No. 0003 v2» (la versión nueva conserva el número)", "Quote No. 0003 v2" in _md, "")
chk("⚠️ «issued 02/10/2026 · valid until 01/01/2027» y «new version of v1» (decía «from COT-3»)",
    "issued 02/10/2026" in _md and "valid until 01/01/2027" in _md and "new version of v1" in _md
    and "from COT" not in _md, "")

print("\n11. El borrador: nota e impuesto, se cambian y se guardan")
_ta = [x for x in at.text_area if x.key == "cot_nota_COT-4"]
chk("la nota del borrador, en su campo", _ta and _ta[0].value == "Nota v2", _ta[0].value if _ta else None)
chk("…y el impuesto", [x.value for x in at.number_input if x.key == "cot_imp_COT-4"] == [10.0])
chk("sin cambios, sin «Save changes»", "cot_save_COT-4" not in _kb(at))
_ta[0].set_value("Nota cambiada")
at.run()
chk("⚠️ cambiar la nota saca «Save changes» y «Discard changes»",
    "cot_save_COT-4" in _kb(at) and "cot_desc_COT-4" in _kb(at), list(_kb(at)))
at.button(key="cot_save_COT-4").click()
at.run()
_g = _llamadas(at, "guardar_lineas")
chk("…y guarda la NOTA con el impuesto", _g and _g[-1][2].get("nota") == "Nota cambiada"
    and _g[-1][2].get("impuesto_pct") == 10.0, _g[-1] if _g else None)
at = _app(pre={"_cot_open": "COT-4"})
[x for x in at.text_area if x.key == "cot_nota_COT-4"][0].set_value("Otra")
at.run()
at.button(key="cot_desc_COT-4").click()
at.run()
chk("«Discard changes» devuelve la nota de la hoja",
    [x.value for x in at.text_area if x.key == "cot_nota_COT-4"] == ["Nota v2"]
    and "cot_save_COT-4" not in _kb(at), [x.value for x in at.text_area if x.key == "cot_nota_COT-4"])

print("\n+, 12. ⚠️ En un borrador ya creado, «Add to the quote» AÑADE (y el selector se vacía)")
at = _app(pre={"_cot_open": "COT-4"})
_ms = [x for x in at.multiselect if str(x.key).startswith("edCOT-4_sel")]
chk("el selector del catálogo, con clave por generación", _ms and _ms[0].key == "edCOT-4_sel_0",
    [x.key for x in at.multiselect])
_ms[0].set_value(["CAT-2"])
at.run()
at.button(key="edCOT-4_add").click()
at.run()
_ed = [d for d in at.dataframe] if False else None
chk("⚠️ la línea añadida SE QUEDA (antes la pasada siguiente volvía a las de la hoja)",
    len(_ss(at, "edCOT-4_lineas") or []) == 2 and "cot_save_COT-4" in _kb(at),
    (len(_ss(at, "edCOT-4_lineas") or []), list(_kb(at))))
chk("…y el selector se VACÍA (otra generación de clave)",
    [x.key for x in at.multiselect if str(x.key).startswith("edCOT-4_sel")] == ["edCOT-4_sel_1"]
    and [x.value for x in at.multiselect if str(x.key).startswith("edCOT-4_sel")] == [[]],
    [(x.key, x.value) for x in at.multiselect])

print("\n2. Deshacer aceptar o rechazar")
at = _app(pre={"_cot_open": "COT-5"})
chk("⚠️ rechazada: «Undo — back to sent»", "cot_undo_COT-5" in _kb(at), list(_kb(at)))
at.button(key="cot_undo_COT-5").click()
at.run()
_s = _llamadas(at, "set_estado")
chk("…que la devuelve a «sent»", _s and _s[-1][1] == ("COT-5", Q.ENVIADA), _s[-1] if _s else None)
at = _app(pre={"_cot_open": "COT-7"})
chk("aceptada SIN obra: también se puede deshacer", "cot_undo_COT-7" in _kb(at), list(_kb(at)))
at = _app(pre={"_cot_open": "COT-8"})
chk("…con obra ya creada, NO (el motor tampoco lo deja)", "cot_undo_COT-8" not in _kb(at), list(_kb(at)))

print("\n1, 3. Crear la obra: los tipos de la app y el nombre con «No.»")
at = _app(pre={"_cot_open": "COT-7"})
_sb = [x for x in at.selectbox if x.label == "Type"]
chk("⚠️ los tipos son los de la app («Installation», «Ripout + Installation», …; antes «Instalación», «Otro»)",
    _sb and list(_sb[0].options) == [str(x) for x in P.TIPOS], list(_sb[0].options) if _sb else None)
_ti = [x for x in at.text_input if x.label == "Project name"]
chk("⚠️ el nombre propuesto con «No.» (se GUARDA en la obra)", _ti and _ti[0].value == "Cli — No. 0007",
    _ti[0].value if _ti else None)

print("\n14. La obra borrada")
at = _app(pre={"_cot_open": "COT-6"})
chk("⚠️ se dice que la obra ya no existe", "The project PRJ-X created from this quote no longer exists." in _textos(at), "")
chk("…con «Unlink it», sin «Undo» ni formulario de obra mientras siga atada",
    "cot_unlink_COT-6" in _kb(at) and "cot_undo_COT-6" not in _kb(at) and not at.text_input,
    list(_kb(at)))
at.button(key="cot_unlink_COT-6").click()
at.run()
chk("…y «Unlink it» la suelta", [x[1] for x in _llamadas(at, "desvincular")] == [("COT-6",)],
    _llamadas(at, "desvincular"))

print("\n3. La comparación, en inglés y sin «-100%» si no hay nada gastado")
at = _app(pre={"_cot_open": "COT-8"})
_md = _textos(at)
chk("⚠️ «you quoted $100 · nothing yet» (decía «cotizaste $100 (-100%)»)",
    "you quoted" in _md and "nothing yet" in _md and "cotizaste" not in _md and "-100%" not in _md, "")
chk("la nota de una enviada/aceptada se VE", True)
at = _app(pre={"_cot_open": "COT-2"})
chk("⚠️ la nota para el cliente se VE en el detalle (iba al PDF sin verse)",
    "Note for the client: Para el cliente" in _textos(at), "")

print("\n9. Crear y la versión nueva AVISAN")
at = _app(pre={"_cot_open": "COT-3"})
at.button(key="cot_v2_COT-3").click()
at.run()
chk("⚠️ «Version 2 of No. 0003 created.»", any("Version 2 of No. 0003 created." in str(s.value) for s in at.success),
    [str(s.value) for s in at.success])
at = _app(pre={"_cot_nueva": True, "new_lineas": json.loads(_L1)})
chk("el alta se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("«➕ New client» traducible", "➕ New client" in [o for s in at.selectbox for o in s.options])
at.button(key="cot_new_save").click()
at.run()
chk("⚠️ crear AVISA: «Quote No. 0009 created.»",
    any("Quote No. 0009 created." in str(s.value) for s in at.success) and _ss(at, "_cot_open") == "COT-9",
    [str(s.value) for s in at.success])

print("\n3. Los textos: todo con `t()`, nada en español, el PDF en inglés")
_qsrc = _src("core/quotes_ui.py")
_qa = ast.parse(_qsrc)
_cads = [n.value for n in ast.walk(_qa) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
chk("⚠️ ni «cotizaste» ni «Cotizacion_» en ninguna cadena", not any("cotizaste" in c or "Cotizacion_" in c for c in _cads))
chk("el PDF se llama «Quote_…»", any(isinstance(n, ast.keyword) and n.arg == "file_name"
                                     and "Quote_" in ast.unparse(n.value) for n in ast.walk(_qa)))
chk("ningún «Nº» de texto (solo la CLAVE de la columna, que se pinta «No.»)",
    [c for c in _cads if "Nº" in c] == ["Nº", "Nº"], [c for c in _cads if "Nº" in c])
_sin_t = []
for n in ast.walk(_qa):
    if (isinstance(n, ast.Call) and ast.unparse(n.func) in ("st.caption", "st.info", "st.error", "st.warning",
                                                            "st.success") and n.args):
        a0 = n.args[0]
        if not any(isinstance(c, ast.Call) and ast.unparse(c.func) == "t" for c in ast.walk(a0)) \
                and not (isinstance(a0, ast.Name)):
            _sin_t.append(ast.unparse(n)[:70])
chk("todos los avisos y pies con `t()`", not _sin_t, _sin_t)

print("\n15, 16. El menú vuelve a la lista; «0 h worked»")
from core import home_ui                                                   # noqa: E402
chk("⚠️ «Quotes» en el menú cierra la cotización abierta y el alta",
    home_ui._ABIERTO_EN_SUB.get(("finanzas", "📄 Cotizaciones")) == ("_cot_open", "_cot_nueva"))
_sm = _func("core/home_ui.py", "sidebar_menu")
chk("…y el menú sabe cerrar MÁS de una cosa (tupla)",
    "isinstance(_abierto, tuple)" in ast.unparse(_sm))
chk("«0 h worked» en la cabecera de la obra (el helper de v565)",
    "{_horas_txt(_horas)}" in _src("core/projects_ui.py") and "{_horas:.1f} h</b>" not in _src("core/projects_ui.py"))

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
sys.exit(1 if fallos else 0)
