# -*- coding: utf-8 -*-
"""v664 · De la cotización a la obra y a la factura (mejoras 2/5 del ciclo 1).

1. «Propose lines» (desde el plano) pone el margen de la empresa, y lo que dice SOBREVIVE al rerun
   (resumen del plano, cantidades por decidir, no propuestos, duplicados).
2. El plano con que se cotizó viaja: se guarda en la cotización (DrawingJSON), pasa a la versión
   nueva y a la obra al aceptar (con el modelo); NS y ubicación ya puestos al convertir.
3. PDF de la cotización: un servicio con horas se cuenta en horas.
4. Factura nueva: propone lo certificable según el avance, avisa si es por adelantado, el importe
   va de segunda columna y avisa si la empresa no tiene ABN.
5. Orden recibida por otro importe: se dice lo recibido y la diferencia.

Nada sale a la red ni escribe: funciones reales con sustitutos en memoria.
"""
import ast
import io
import json
import os
import sys
from datetime import date, datetime

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:700]))
    if not cond:
        FALLOS.append(nombre)


def sec(t_):
    print(f"\n{'─' * 70}\n{t_}\n{'─' * 70}")


def src(rel):
    return io.open(os.path.join(RAIZ, rel), encoding="utf-8").read()


def funcion(rel, nombre):
    s = src(rel)
    for n in ast.walk(ast.parse(s)):
        if isinstance(n, ast.FunctionDef) and n.name == nombre:
            return n, ast.get_source_segment(s, n) or ""
    return None, ""


# ═════════════════════════════════════════════════════════════════════════════
sec("1. Proponer desde el plano")
from core import quote_from_plan as QP                                     # noqa: E402

_ITEM = {"ID": "CAT-1", "Type": "product", "Name": "Interlock", "Unit": "unit", "UnitCost": "185",
         "QtyRule": QP.POR_PARADA, "Active": "SI"}
_r20 = QP.proponer({"ns": 10}, [_ITEM], 20)
_l = (_r20.get("lineas") or [{}])[0]
chk("con el margen de la empresa: 10 × 185 a 20 % → beneficio 370, precio 2.220",
    abs(float(_l.get("margen_pct", 0)) - 20) < 0.01 and abs(float(_l.get("precio_total", 0)) - 2220) < 0.01, _l)
_n, _s = funcion("core/quotes_ui.py", "_desde_plano")
chk("_desde_plano pasa el margen de la empresa a proponer()",
    "_QP.proponer(_plano, _items, _A.group_margin_default(grupo))" in _s)
# ⚠️ lo que se dice DESPUÉS de proponer tiene que ir por flash: un st.* antes del rerun se pierde
_tras = _s[_s.find("_QP.proponer("):]
_st_tras = [c for c in ("st.markdown(", "st.error(", "st.caption(", "st.warning(", "st.info(") if c in _tras]
chk("tras proponer, nada se pinta con st.* (se perdía con el rerun): todo por flash", _st_tras == [], _st_tras)
chk("…el resumen del plano, las cantidades por decidir y los no propuestos van por flash",
    "flash.info(t(\"**The drawing says:**" in _tras and "flash.error(\":material/priority_high:" in _tras
    and "Not proposed (their «Quantity from the drawing» is" in _tras)
chk("…y un artículo que ya estaba se AVISA (sigue añadiendo, decisión del usuario v509)",
    "is now in the quote twice" in _tras and "_st[\"new_lineas\"] = _ya + _QP.limpiar(" in _tras
    and "        for _nuevo, _viejo in _dobles:\n            flash.aviso(" in _tras
    and 'if str(l.get("catalogo_id", "")) in _ids]' in _tras
    and '_ids = {str(l.get("catalogo_id", "")): l for l in _ya if l.get("catalogo_id")}' in _tras)
chk("…y el plano se guarda para la cotización", '_st["new_plano"] = _plano' in _tras)
_qu = src("core/quotes_ui.py")
chk("el plano viaja a Q.crear y se limpia con el resto del alta",
    'plano=st.session_state.get("new_plano"))' in _qu and '"new_plano"' in _qu.split("_CLAVES_NUEVA = (")[1][:120])

# ═════════════════════════════════════════════════════════════════════════════
sec("2. El plano de la cotización llega a la obra")
from core import quotes as Q                                               # noqa: E402

chk("Quotes tiene la columna DrawingJSON, al FINAL (migra sola)", Q.HEADERS[-1] == "DrawingJSON", Q.HEADERS[-3:])


class _WS:
    def __init__(self):
        self.filas = []

    def append_row(self, fila, **k):
        self.filas.append(fila)


_w = _WS()
_PLANO = {"ns": 10, "modelo": "ES1_R2", "params": {"TKSW": 980}}
_o = (Q._ws, Q._ids_frescos, Q._id_libre, Q._invalidate)
Q._ws = lambda: _w
Q._ids_frescos = lambda: (7, 4)
Q._id_libre = lambda mx: "COT-0008"
Q._invalidate = lambda: None
try:
    _ok = Q.crear("g1", "CLI-1", "C1", [{"concepto": "x", "cantidad": 1, "costo_total": 10, "precio_total": 12,
                                         "margen_pct": 20}], 10, plano=_PLANO)
    _ok2 = Q.crear("g1", "CLI-1", "C1", [{"concepto": "x", "cantidad": 1, "costo_total": 10, "precio_total": 12,
                                          "margen_pct": 20}], 10)
finally:
    Q._ws, Q._ids_frescos, Q._id_libre, Q._invalidate = _o
_f = _w.filas[0] if _w.filas else []
chk("crear escribe UNA columna por cabecera, con el plano en DrawingJSON",
    _ok[0] and len(_f) == len(Q.HEADERS) and json.loads(_f[Q.HEADERS.index("DrawingJSON")]).get("ns") == 10,
    (_ok, len(_f), len(Q.HEADERS)))
_abre = []
_o1 = Q._ws
Q._ws = lambda: (_abre.append(1), _WS())[1]
try:
    _r0 = Q.crear("g1", "CLI-1", "C1", [], 10)
    _r1 = Q.crear("g1", "CLI-1", "  ", [{"concepto": "x", "cantidad": 1, "costo_total": 10, "precio_total": 12}], 10)
finally:
    Q._ws = _o1
chk("⚠️ sin líneas o sin cliente, crear rechaza SIN abrir la hoja (abrirla migra la cabecera = escribe)",
    _r0[0] is False and _r1[0] is False and _abre == [], (_r0, _r1, _abre))
chk("…y sin plano, la celda vacía (no «None» ni «{}»)", _ok2[0] and _w.filas[1][-1] == "", _w.filas[1][-1:] if len(_w.filas) > 1 else None)
chk("plano_de lee lo guardado y {} si no hay o está roto",
    Q.plano_de({"DrawingJSON": json.dumps(_PLANO)}) == _PLANO and Q.plano_de({}) == {} and Q.plano_de({"DrawingJSON": "{roto"}) == {}
    and Q.plano_de({"DrawingJSON": "[1, 2]"}) == {})
_n, _nv = funcion("core/quotes.py", "nueva_version")
chk("una versión nueva conserva el plano", 'plano=str(c.get("DrawingJSON") or "")' in _nv)

# aceptar → la obra nace con el plano y el modelo
from core import projects as P                                             # noqa: E402
from core import plan_data as PD                                           # noqa: E402

_cap = {}
_C = {"ID": "COT-0008", "Group": "g1", "ClientID": "CLI-1", "ClientName": "C1", "Number": "0005", "TaxPct": "10",
      "Status": "sent", "ProjectID": "", "DrawingJSON": json.dumps(_PLANO),
      "LinesJSON": json.dumps([{"concepto": "x", "cantidad": 1, "costo_total": 100, "precio_total": 120,
                                "margen_pct": 20}])}
_o2 = (Q.get_cotizacion, P.create_project, PD.guardar, Q._ws, Q._fila, Q._set, Q._invalidate)
Q.get_cotizacion = lambda cid: dict(_C)
P.create_project = lambda *a, **k: (_cap.setdefault("crear", (a, k)), (True, "PRJ-9999"))[1]
PD.guardar = lambda pid, datos: (_cap.setdefault("plano", (pid, datos)), (True, ""))[1]
Q._ws = lambda: object()
Q._fila = lambda w, cid: (2, dict(_C))
Q._set = lambda w, row, campos: (True, "")
Q._invalidate = lambda: None
try:
    from core import auditoria as _AU
    _o3 = _AU.registrar
    _AU.registrar = lambda *a, **k: None
    _res = Q.aceptar_y_crear_proyecto("COT-0008", nombre="C1 L1", tipo="Installation",
                                      fecha_inicio=date(2026, 11, 9), ns=10, ubicacion="1 Macquarie St")
finally:
    Q.get_cotizacion, P.create_project, PD.guardar, Q._ws, Q._fila, Q._set, Q._invalidate = _o2
    _AU.registrar = _o3
chk("la sonda: la obra se crea (el camino se ejecuta)", _res == (True, "PRJ-9999") and "crear" in _cap, (_res, list(_cap)))
chk("…con el MODELO del plano", (_cap.get("crear") or ((), {}))[1].get("modelo") == "ES1_R2", (_cap.get("crear") or ((), {}))[1].get("modelo"))
chk("…y los datos del plano guardados en la obra nueva", _cap.get("plano") == ("PRJ-9999", _PLANO), _cap.get("plano"))
_n, _cp = funcion("core/quotes_ui.py", "_crear_proyecto")
chk("Turn it into a project: NS del plano y ubicación de la ficha del cliente",
    "_ns_pl = _QP._ns(Q.plano_de(c))" in _cp and "value=min(50, _ns_pl) if _ns_pl >= 2 else 2" in _cp
    and 'C.get_cliente(str(c.get("ClientID", "")))' in _cp and "value=_dir0" in _cp)

# ═════════════════════════════════════════════════════════════════════════════
sec("3. PDF de la cotización: horas de un servicio")
from core import quote_pdf as QPDF                                         # noqa: E402
from pypdf import PdfReader                                                 # noqa: E402

_cot = {"ID": "COT-1", "Number": "0005", "Date": "2026-11-09", "ValidUntil": "2026-12-09", "Status": "draft",
        "ClientName": "C1", "Subtotal": "12780", "TaxPct": "10", "Tax": "1278", "Total": "14058",
        "LinesJSON": json.dumps([
            {"concepto": "Installation labour", "tipo": "service", "cantidad": 1, "horas": 160,
             "costo_total": 8800, "precio_total": 10560, "unidad": ""},
            {"concepto": "Interlock", "tipo": "product", "cantidad": 10, "unidad": "unit",
             "costo_total": 1850, "precio_total": 2220}])}
_pdf = QPDF.generate_quote_pdf(_cot, {}, "cliente1")
_txt = " ".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(_pdf)).pages)
chk("la mano de obra sale «160 h» (decía «1»)", "160 h" in _txt, _txt[:400])
chk("…y un producto sigue con su cantidad (10)", "Interlock\n10\n" in _txt, _txt[:400])

# ═════════════════════════════════════════════════════════════════════════════
sec("4. Factura nueva")
from core import invoices as I                                             # noqa: E402
from core import finance as F                                              # noqa: E402

_o4 = (F.project_revenue, I.facturado_por_proyecto)
# ⚠️ v669 · con «modelo»: lo certificable depende de él (una obra por horas tiene ganado lo trabajado, H23 del
# ciclo 2). Esta prueba es la de una obra COTIZADA, que se gana con el avance.
F.project_revenue = lambda pid, g, p=None: {"ingreso": 12780.0, "modelo": "cotizado"}
I.facturado_por_proyecto = lambda g: {"PRJ-1": 3834.0}
try:
    _c0 = I.por_certificar("PRJ-1", "g1", {"ID": "PRJ-1", "Progress": "0"})
    _c50 = I.por_certificar("PRJ-1", "g1", {"ID": "PRJ-1", "Progress": "50"})
    _c100 = I.por_certificar("PRJ-1", "g1", {"ID": "PRJ-1", "Progress": "100"})
finally:
    F.project_revenue, I.facturado_por_proyecto = _o4
chk("al 0 %: nada certificable, 8.946 pendientes", _c0["certificable"] == 0 and _c0["pendiente"] == 8946.0, _c0)
chk("al 50 %: ganado 6.390, certificable 2.556", _c50["ganado"] == 6390.0 and _c50["certificable"] == 2556.0, _c50)
chk("al 100 %: certificable = pendiente", _c100["certificable"] == _c100["pendiente"] == 8946.0, _c100)
_o4b = I.pendiente_de_facturar
I.pendiente_de_facturar = lambda pid, g, p=None: 777.0
try:
    _cx = I.por_certificar("PRJ-1", "g1", {"ID": "PRJ-1", "Progress": "0"})
finally:
    I.pendiente_de_facturar = _o4b
chk("el pendiente ES pendiente_de_facturar (una sola definición)", _cx["pendiente"] == 777.0, _cx)
_n, _nf = funcion("core/invoices_ui.py", "_nueva_factura")
chk("la línea propone lo certificable con avance y avisa del adelanto",
    'imp = _c["certificable"]' in _nf and "**in advance**" in _nf and "claimable now (the line takes that)" in _nf, _nf[:300])
chk("…cada caso por su rama: sin avance, el pendiente con aviso; con avance a medias, lo certificable",
    # ⚠️ v669 · la rama del adelanto mira lo CERTIFICABLE (no el avance): en una obra por horas lo trabajado ya
    # está ganado con el avance a 0 (H23 del ciclo 2); el «no progress yet» sigue dentro, con avance 0
    'if _c["certificable"] <= 0.005:\n            imp = pend\n            if _c["avance"] <= 0:\n                _notas.append(t(":material/warning:' in _nf
    and 'elif _c["certificable"] + 0.5 < pend:\n            imp = _c["certificable"]\n            _notas.append(' in _nf
    and '_c = I.por_certificar(str(p.get("ID", "")), grupo, p)' in _nf)
chk("…y las notas se PINTAN antes de la tabla", _nf.find("    for _n in _notas:\n        st.markdown(_n)\n") >= 0
    and _nf.find("    for _n in _notas:\n        st.markdown(_n)\n") < _nf.find('key="fac_lineas"'))
chk("el IMPORTE va de segunda columna (datos y tabla)",
    '"Importe": imp, "Project":' in _nf
    and _nf.find('"Importe":  st.column_config.NumberColumn') < _nf.find('"Project": st.column_config.SelectboxColumn'))
_ia = _nf.find("    if _sin_abn:\n        st.warning(t(\":material/warning: This company has no ABN")
chk("sin ABN se avisa ANTES de emitir", 0 <= _ia < _nf.find("Issue invoice")
    and '_sin_abn = not str(_CB.identidad(grupo).get("abn") or "").strip()' in _nf, _ia)
_n, _df_ = funcion("core/invoices_ui.py", "_detalle_factura")
chk("…y al lado del PDF de una factura emitida",
    'if not str(_CB.identidad(grupo).get("abn") or "").strip():\n'
    '                st.caption(t(":material/warning: This PDF says «TAX INVOICE» but the company has no ABN yet."))'
    in _df_)

# ═════════════════════════════════════════════════════════════════════════════
sec("5. Orden recibida por otro importe")
from core import orders as O                                               # noqa: E402
from core import expenses as E                                             # noqa: E402

_o5 = E._records
E._records = lambda *a, **k: [{"ID": "GAS-1", "Amount": "1910"}, {"ID": "GAS-2", "Amount": "50"}]
try:
    _v1 = O.valor_recibido({"ExpenseID": "GAS-1", "Amount": "1850"})
    _v0 = O.valor_recibido({"ExpenseID": "", "Amount": "1850"})
    _vx = O.valor_recibido({"ExpenseID": "GAS-9", "Amount": "1850"})
finally:
    E._records = _o5
chk("valor_recibido = el importe de su gasto (1.910), None sin gasto o si no está",
    _v1 == 1910.0 and _v0 is None and _vx is None, (_v1, _v0, _vx))
_pu = src("core/projects_ui.py")
_io = _pu.find("                if _est == O.RECIBIDA:\n                    _rv = O.valor_recibido(o)\n"
               "                    if _rv is not None and abs(_rv - _n(o.get(\"Amount\"))) > 0.005:\n"
               "                        _df = _rv - _n(o.get(\"Amount\"))\n"
               "                        _lin += (\"  \" + t(\"received **{r}** ({d} vs ordered)\")")
chk("la línea de la orden dice lo recibido y la diferencia, ANTES de pintarse",
    0 <= _io < _pu.find("                st.markdown(_lin)\n", _io) and '.replace("{r}", theme.dinero(_rv))' in _pu
    and '.replace("{d}", ("+" if _df > 0 else "−") + theme.dinero(abs(_df))))' in _pu, _io)

print("\n" + ("TODO OK" if not FALLOS else f"{len(FALLOS)} FALLOS: " + " | ".join(FALLOS)))
sys.exit(1 if FALLOS else 0)
