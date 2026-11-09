# -*- coding: utf-8 -*-
"""v670 · Confirmar antes de tirar o cerrar (ciclo 2, mejoras 2/5) + lo visto verificando v669.

H6  «Mark as sent» con cambios sin guardar los guarda antes.
H7  cancelar una orden pregunta, y una cancelada se reabre.
H8  el gasto de una orden: «from order …, no supplier invoice», y se le adjunta la factura del proveedor.
H9  borrar un recibo pregunta; el gasto de una orden solo se quita deshaciendo la recepción.
H13 el % de la certificación fuera del formulario, la vista previa le sigue, y certificar más de lo hecho avisa.
H18 cancelar o pausar una obra se confirma con lo que queda abierto, libera el tablero desde hoy y lo dice a la gente.
H21 cancelar una certificación pregunta, las anuladas quedan tachadas, y una obra cancelada no certifica.
v669 · importes con miles en los avisos de cobros, el nombre en el historial, y la salida correcta en una obra sin
cotización (ganancia fija, no variación).

Nada sale a la red ni escribe: funciones reales con sustitutos y hojas de mentira; AppTest de las pantallas.
"""
import ast
import io
import json
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


def _sustituir(obj, **kw):
    viejo = {k: getattr(obj, k) for k in kw}
    for k, v in kw.items():
        setattr(obj, k, v)
    return lambda: [setattr(obj, k, v) for k, v in viejo.items()]


from streamlit.testing.v1 import AppTest                                   # noqa: E402
from core import orders as O                                               # noqa: E402
from core import expenses as E                                             # noqa: E402
from core import claims as CL                                              # noqa: E402
from core import roster as R                                               # noqa: E402
from core import invoices as I                                             # noqa: E402
from core import projects as P                                             # noqa: E402

# los originales: los guiones de AppTest corren en ESTE proceso y dejan sus sustitutos puestos (trampa 48)
_PUEDE_LIBERAR = CL.puede_liberar


class _WS:
    """Hoja de mentira: registros, valores y lo escrito."""
    def __init__(self, cab, filas):
        self.cab, self.filas, self.lotes, self.celdas, self.borradas = list(cab), filas, [], [], []

    def get_all_records(self, **k):
        return [dict(r) for r in self.filas]

    def get_all_values(self):
        return [list(self.cab)] + [[str(r.get(h, "")) for h in self.cab] for r in self.filas]

    def batch_update(self, rangos, **k):
        self.lotes.append(rangos)

    def update_cell(self, f, c, v):
        self.celdas.append((f, c, v))

    def delete_rows(self, n):
        self.borradas.append(n)


# ═════════════════════════════════════════════════════════════════════════════
sec("1. Órdenes: reabrir y deshacer la recepción (H7, H9)")
_ORD = {h: "" for h in O.HEADERS}


def _orden(oid, est, gid=""):
    r = dict(_ORD)
    r.update({"ID": oid, "Group": "G", "ProjectID": "P1", "Supplier": "Lift Parts", "Amount": "38500", "Status": est,
              "ExpenseID": gid})
    return r


_borrados = []
ws = _WS(O.HEADERS, [_orden("ORD-1", O.CANCELADA), _orden("ORD-2", O.RECIBIDA, "G-00004"), _orden("ORD-3", O.PENDIENTE)])
_d = [_sustituir(O, _ws=lambda: ws, _invalidate=lambda: None),
      _sustituir(E, delete=lambda gid, de_orden=False: (_borrados.append((gid, de_orden)), (True, "Receipt deleted."))[1])]
try:
    _r1 = O.reabrir("ORD-1")
    _r3 = O.reabrir("ORD-3")
    _u2 = O.deshacer_recepcion("ORD-2")
    _u3 = O.deshacer_recepcion("ORD-3")
    _c2 = O.cancelar("ORD-2")
finally:
    for x in _d:
        x()
_esc = {r["range"]: r["values"][0][0] for lote in ws.lotes for r in lote}
from core.num import col_letter as _cl                                     # noqa: E402
_S, _X = _cl(O._COL["Status"]), _cl(O._COL["ExpenseID"])
chk("H7 · reabrir una cancelada la pone pendiente", _r1[0] and _esc.get(f"{_S}2") == O.PENDIENTE, (_r1, _esc))
chk("…y una pendiente no se «reabre»", not _r3[0], _r3)
chk("H9 · deshacer la recepción: pendiente, sin gasto apuntado, y el gasto se BORRA con de_orden=True",
    _u2[0] and _esc.get(f"{_S}3") == O.PENDIENTE and _esc.get(f"{_X}3") == "" and _borrados == [("G-00004", True)],
    (_u2, _esc, _borrados))
chk("…solo una recibida", not _u3[0], _u3)
chk("cancelar una recibida remite a deshacer la recepción", not _c2[0] and "undo the receipt" in _c2[1], _c2)

_d = [_sustituir(O, de_un_gasto=lambda gid, grupo=None: {"ID": "ORD-2"} if gid == "G-00004" else {})]
_we = _WS(E.HEADERS, [{"ID": "G-00004", "Amount": "39200"}, {"ID": "G-00005", "Amount": "86.4"}])
_d.append(_sustituir(E, _ws=lambda: _we, _invalidate=lambda: None))
try:
    _e4 = E.delete("G-00004")
    _e5 = E.delete("G-00005")
    _e4b = E.delete("G-00004", de_orden=True)
finally:
    for x in _d:
        x()
chk("⚠️ el gasto de una orden NO se borra suelto (remite a la orden)", not _e4[0] and "ORD-2" in _e4[1], _e4)
chk("…un recibo normal sí, y el de la orden con de_orden=True", _e5[0] and _e4b[0] and _we.borradas == [3, 2],
    (_e5, _e4b, _we.borradas))
_we = _WS(E.HEADERS, [{"ID": "G-00004", "Amount": "39200"}])
_d = [_sustituir(E, _ws=lambda: _we, _invalidate=lambda: None)]
try:
    _a = E.adjuntar("G-00004", "DRIVE-1", "factura.pdf")
    _a0 = E.adjuntar("G-00004", "", "factura.pdf")
finally:
    for x in _d:
        x()
_ea = {r["range"]: r["values"][0][0] for lote in _we.lotes for r in lote}
chk("H8 · adjuntar la factura del proveedor al gasto (DriveID y File)", _a[0] and "DRIVE-1" in _ea.values()
    and "factura.pdf" in _ea.values(), (_a, _ea))
chk("…sin fichero subido, no", not _a0[0], _a0)

# ═════════════════════════════════════════════════════════════════════════════
sec("2. Recibos y órdenes en pantalla (AppTest)")
RECIBOS = r'''
import streamlit as st
from core import projects_ui as PU, expenses as E, orders as O, flash
st.session_state.setdefault("auth", {"usuario": "adm", "rol": "administrator", "grupo": "G", "nombre": "Adm"})
st.session_state.setdefault("_LL", [])
E.is_configured = lambda: True
E.project_expenses = lambda pid: {"total": 39286.4, "items": [
    {"ID": "G-00004", "Date": "2026-11-10", "Category": "Materials", "Supplier": "Lift Parts", "Amount": "39200",
     "Description": "Order ORD-2 · MRL", "DriveID": "", "CreatedBy": "adm"},
    {"ID": "G-00005", "Date": "2026-11-10", "Category": "Materials", "Supplier": "Bunnings", "Amount": "86.4",
     "Description": "fixings", "DriveID": "", "CreatedBy": "adm"}]}
E.delete = lambda gid, de_orden=False: (st.session_state["_LL"].append(("delete", gid)), (True, "Receipt deleted."))[1]
O.is_configured = lambda: True
_ORDS = [{"ID": "ORD-1", "Status": "cancelled", "Supplier": "Bracket Co", "Amount": "1200", "Description": "brackets",
          "Date": "2026-11-10", "ExpenseID": ""},
         {"ID": "ORD-2", "Status": "received", "Supplier": "Lift Parts", "Amount": "38500", "Description": "MRL",
          "Date": "2026-11-10", "ExpenseID": "G-00004"},
         {"ID": "ORD-3", "Status": "pending", "Supplier": "Rail Co", "Amount": "4200", "Description": "rails",
          "Date": "2026-11-10", "ExpenseID": ""}]
O.list_for = lambda pid, estado=None: [dict(o) for o in _ORDS if estado is None or o["Status"] == estado]
O.valor_recibido = lambda o: 39200.0 if o.get("ID") == "ORD-2" else None
O.cancelar = lambda oid: (st.session_state["_LL"].append(("cancelar", oid)), (True, "Order cancelled."))[1]
O.reabrir = lambda oid: (st.session_state["_LL"].append(("reabrir", oid)), (True, "Order reopened."))[1]
O.deshacer_recepcion = lambda oid: (st.session_state["_LL"].append(("deshacer", oid)), (True, "Receipt undone."))[1]
flash.mostrar()
if st.session_state.get("_QUE") == "ordenes":
    PU._ordenes_section("P1", "G", editable=True, key_prefix="ord")
else:
    PU.render_expenses("P1", "G", can_delete=True, key_prefix="adm", ver_costos=False)
'''


def _app(guion, que=None):
    a = AppTest.from_string(guion, default_timeout=90)
    if que:
        a.session_state["_QUE"] = que
    a.run()
    return a


def _ll(a):
    try:
        return list(a.session_state["_LL"])
    except KeyError:
        return []


at = _app(RECIBOS)
chk("los recibos se pintan sin excepción", not at.exception, [e.value for e in at.exception][:1])
_kb = {b.key for b in at.button}
_cap = " ".join(c.value for c in at.caption)
chk("H8 · el gasto de la orden: «from order ORD-2, no supplier invoice»",
    "from order ORD-2, no supplier invoice" in _cap, _cap[:400])
chk("H9 · …sin papelera; el recibo normal sí la tiene", "adm_del_G-00004" not in _kb and "adm_del_G-00005" in _kb,
    sorted(_kb))
chk("H8 · …y se le puede adjuntar la factura del proveedor",
    any(u.key == "adm_adj_G-00004" for u in at.get("file_uploader")), [u.key for u in at.get("file_uploader")])
at.button(key="adm_del_G-00005").click().run()
chk("H9 · la papelera PREGUNTA con el importe (no borra todavía)",
    any("Delete this receipt of" in w.value and "86.40" in w.value for w in at.warning)
    and not [x for x in _ll(at) if x[0] == "delete"], ([w.value for w in at.warning], _ll(at)))
at.button(key="adm_delsi_G-00005").click().run()
chk("…y «Yes, delete it» lo borra (una vez)", [x for x in _ll(at) if x[0] == "delete"] == [("delete", "G-00005")],
    _ll(at))

at = _app(RECIBOS, "ordenes")
chk("las órdenes se pintan sin excepción", not at.exception, [e.value for e in at.exception][:1])
_kb = {b.key for b in at.button}
chk("H7 · la cancelada se puede reabrir; la recibida, deshacer su recepción",
    "ord_ordre_ORD-1" in _kb and "ord_ordun_ORD-2" in _kb and "ord_ordc_ORD-3" in _kb, sorted(_kb))
at.button(key="ord_ordc_ORD-3").click().run()
chk("H7 · «Cancel» PREGUNTA con el importe y el proveedor (no cancela todavía)",
    any("Cancel order ORD-3 for" in w.value and "4,200.00" in w.value for w in at.warning)
    and not [x for x in _ll(at) if x[0] == "cancelar"], ([w.value for w in at.warning], _ll(at)))
at.button(key="ord_ordsi_ORD-3").click().run()
chk("…y «Yes» la cancela", ("cancelar", "ORD-3") in _ll(at), _ll(at))
at = _app(RECIBOS, "ordenes")
at.button(key="ord_ordun_ORD-2").click().run()
chk("H9 · «Undo the receipt» pregunta con lo que costó ($39,200)",
    any("Undo the receipt of ORD-2" in w.value and "39,200.00" in w.value for w in at.warning), [w.value for w in at.warning])
at.button(key="ord_ordsi_ORD-2").click().run()
chk("…y «Yes» la deshace", ("deshacer", "ORD-2") in _ll(at), _ll(at))
at = _app(RECIBOS, "ordenes")
at.button(key="ord_ordre_ORD-1").click().run()
chk("«Reopen» reabre", ("reabrir", "ORD-1") in _ll(at), _ll(at))

# ═════════════════════════════════════════════════════════════════════════════
sec("3. Cotización: «Mark as sent» guarda antes (H6)")
from core import quotes as Q                                               # noqa: E402
_L1 = json.dumps([Q.linea_de({"ID": "CAT-1", "Type": "product", "Name": "Item A", "UnitCost": "100", "Unit": "unit"},
                             2, ganancia=50)])
COT = r'''
import streamlit as st
from core import quotes_ui as QU, quotes as Q, clientes as C, catalogo as CAT, auth, projects as P, quote_pdf, flash
st.session_state.setdefault("auth", {"rol": "administrator", "usuario": "adm", "nombre": "Adm", "grupo": "G"})
st.session_state.setdefault("_LL", [])
ROWS = [{"ID": "COT-4", "Group": "G", "ClientName": "Cli", "ClientID": "CLI-1", "Number": "0003", "Version": "2",
         "Date": "2026-10-02", "ValidUntil": "2027-01-01", "Total": "396", "Status": "draft", "LinesJSON": %r,
         "TaxPct": "10", "Note": "Nota v2"}]
Q._records = lambda: [dict(r) for r in ROWS]
Q.is_configured = lambda: True
def _q(n, dev):
    def f(*a, **k):
        st.session_state["_LL"].append((n, a, k))
        return dev
    return f
Q.set_estado = _q("set_estado", (True, "Quote marked as sent."))
Q.guardar_lineas = _q("guardar_lineas", (True, "Quote updated."))
Q.desactualizadas = lambda c: []
P.get_project = lambda pid: {}
C.list_clientes = lambda g, **k: [{"ID": "CLI-1", "Name": "Cli"}]
CAT.list_items = lambda g, **k: []
auth.group_margin_default = lambda g: 20.0
auth.group_tax_default = lambda g: 10.0
quote_pdf.generate_quote_pdf = lambda c, cli, g: b"%%PDF-1.4"
st.session_state.setdefault("_cot_open", "COT-4")
flash.mostrar()
QU.render_cotizaciones("G")
''' % (_L1,)
at = AppTest.from_string(COT, default_timeout=90)
at.run()
chk("el borrador se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_lb = {b.key: b.label for b in at.button}
chk("sin cambios: «Mark as sent»", "Mark as sent" in _lb.get("cot_env_COT-4", "")
    and "Save and" not in _lb.get("cot_env_COT-4", ""), _lb.get("cot_env_COT-4"))
[x for x in at.number_input if x.key == "cot_imp_COT-4"][0].set_value(0.0)
at.run()
_lb = {b.key: b.label for b in at.button}
chk("⚠️ con un cambio sin guardar: «Save and mark as sent»", "Save and mark as sent" in _lb.get("cot_env_COT-4", ""),
    _lb.get("cot_env_COT-4"))
at.button(key="cot_env_COT-4").click().run()
_ll2 = [x[0] for x in _ll(at)]
_g = [x for x in _ll(at) if x[0] == "guardar_lineas"]
chk("⚠️ …y al pulsarlo GUARDA (con el impuesto nuevo) y DESPUÉS la marca enviada",
    _ll2 == ["guardar_lineas", "set_estado"] and _g and _g[0][2].get("impuesto_pct") == 0.0, _ll(at))

# ═════════════════════════════════════════════════════════════════════════════
sec("4. Certificaciones (H13, H21)")
CLM = r'''
import streamlit as st
from core import claims_ui as CU, claims as CL, invoices as I, flash
st.session_state.setdefault("_LL", [])
st.session_state.setdefault("auth", {"usuario": "adm", "rol": "administrator", "grupo": "G", "nombre": "Adm"})
CL.is_configured = lambda: True
def _calc(pid, grupo, pct=None, prj=None):
    real = 0.0
    p = real if pct is None else float(pct)
    hecho = round(57055.0 * p / 100, 2)
    ret = round(hecho * 0.05, 2)
    return {"contrato": 57055.0, "cotizacion": "COT-12", "variaciones": 0.0, "valor": 57055.0, "pct": p,
            "hecho": hecho, "antes": 0.0, "bruto": hecho, "retencion_pct": 5.0, "retencion": ret,
            "neto": round(hecho - ret, 2), "hay_contrato": True, "retenido_acumulado": 297.77,
            "retenido_liberado": 0.0, "retenido_pendiente": 297.77}
CL.calcular = _calc
CL.variaciones = lambda pid, estado=None: []
_C = [{"ID": "CLM-1", "Number": "1", "Date": "2026-11-10", "PctComplete": "10.0", "ThisClaim": "5955.5",
       "Retention": "297.77", "Status": st.session_state.get("_EST1", "issued"), "Type": ""}]
CL.reclamaciones = lambda pid, incluir_anuladas=False: [dict(c) for c in _C if incluir_anuladas or c["Status"] != "cancelled"]
CL.anular = lambda cid: (st.session_state["_LL"].append(("anular", cid)), (True, "Claim cancelled."))[1]
CL.puede_liberar = lambda pid, prj=None: (False, "no")
I.is_configured = lambda: False
CU._descarga = lambda *a, **k: None
flash.mostrar()
CU.render("PRJ-43", "G", {"ID": "PRJ-43", "Status": st.session_state.get("_PST", "In progress"), "Progress": "0"},
          editable=True, key_prefix="clm")
'''
at = AppTest.from_string(CLM, default_timeout=90)
at.run()
chk("las certificaciones se pintan sin excepción", not at.exception, [e.value for e in at.exception][:1])
_ni = [x for x in at.number_input if x.key == "clm_pct_PRJ-43"]
chk("H13 · el % va FUERA del formulario (con su clave)", bool(_ni), [x.key for x in at.number_input])
_ni[0].set_value(10.0)
at.run()
_md = " ".join(m.value for m in at.markdown)
chk("H13 · …y la vista previa le sigue al escribirlo (10 % → work done $5,705.50, net $5,420.22)",
    "Progress **10.0%**" in _md and "5,705.50" in _md and "5,420.22" in _md, _md[:500])
chk("H13 · certificar más de lo hecho AVISA (10 % con la obra al 0 %)",
    any("This claims **10.0%** with the job at **0.0%**" in w.value for w in at.warning), [w.value for w in at.warning])
_n, _ru = funcion("core/claims_ui.py", "render")
chk("…y el formulario emite con ESE % (no uno propio)", "pid, grupo, _pct, _hasta.strftime" in _ru
    and "Progress to claim (%)" not in _ru[_ru.find("with st.form(f\"{key_prefix}_new_{pid}\""):], "")
at.button(key="clm_void_CLM-1").click().run()
chk("H21 · «Cancel» PREGUNTA con el neto (no anula todavía)",
    any("Cancel claim #1 (net" in w.value for w in at.warning) and not [x for x in _ll(at) if x[0] == "anular"],
    ([w.value for w in at.warning], _ll(at)))
at.button(key="clm_voidsi_CLM-1").click().run()
chk("…y «Yes, cancel it» la anula", ("anular", "CLM-1") in _ll(at), _ll(at))
at = AppTest.from_string(CLM, default_timeout=90)
at.session_state["_EST1"] = "cancelled"
at.run()
_md = " ".join(m.value for m in at.markdown)
chk("H21 · una anulada sigue en la lista, TACHADA y «cancelled»", "~~**#1**" in _md and "· cancelled" in _md, _md[:600])
at = AppTest.from_string(CLM, default_timeout=90)
at.session_state["_PST"] = "Cancelled"
at.run()
chk("H21 · en una obra cancelada no se certifica (sin %, sin «Issue claim») y se dice",
    not [x for x in at.number_input if x.key == "clm_pct_PRJ-43"]
    and not [b for b in at.button if "Issue claim" in str(b.label)]
    and any("This job is cancelled: no more progress claims" in i.value for i in at.info), [i.value for i in at.info])
_d = [_sustituir(CL, retenido=lambda pid: {"retenido": 297.77, "liberado": 0.0, "pendiente": 297.77})]
try:
    _pl = _PUEDE_LIBERAR("PRJ-43", {"Status": "Cancelled", "Progress": "10"})
    _pl2 = _PUEDE_LIBERAR("PRJ-43", {"Status": "In progress", "Progress": "10"})
    _pl3 = _PUEDE_LIBERAR("PRJ-43", {"Status": "Completed", "Progress": "100"})
finally:
    for x in _d:
        x()
chk("H21 · la retención de una obra cancelada se puede pedir; la de una viva al 10 %, no", _pl[0] and not _pl2[0],
    (_pl, _pl2))
# ⚠️ el camino del 100 % formatea lo retenido: en v670 lo rompí reutilizando su nombre (lo cazó verif_v510)
chk("…y al 100 % se puede, diciendo cuánto (297.77)", _pl3[0] and "297.77" in _pl3[1], _pl3)

# ═════════════════════════════════════════════════════════════════════════════
sec("5. Cancelar o pausar una obra (H18)")
_HOY = date(2026, 11, 10)
_FILAS = [{"ID": "ROS-1", "Group": "G", "Week": "2026-11-09", "User": "hl",
           "DataJSON": json.dumps({"lun": {"items": [{"a": "PRJ-43", "i": "07:00", "f": "15:30"}]},
                                   "mar": {"items": [{"a": "PRJ-43", "i": "07:00", "f": "15:30"}]},
                                   "mie": {"items": [{"a": "PRJ-43", "i": "07:00", "f": "15:30"}]},
                                   "jue": {"items": [{"a": "PRJ-9", "i": "07:00", "f": "15:30"}]}})}]
_d = [_sustituir(R, _roster_records=lambda: [dict(f) for f in _FILAS])]
try:
    _dd = R.dias_desde("G", "PRJ-43", _HOY)
finally:
    for x in _d:
        x()
chk("roster.dias_desde: desde el martes 10/11, 2 días de PRJ-43 (el lunes ya pasó; el jueves es otra obra)",
    _dd == {"hl": 2}, _dd)
_wr = _WS(R.ROSTER_HEADERS, [dict(f) for f in _FILAS])
_d = [_sustituir(R, _ws_roster=lambda: _wr, _invalidate=lambda: None)]
try:
    _nq = R.limpiar_proyecto("G", "PRJ-43", desde=_HOY)
finally:
    for x in _d:
        x()
_nuevo = json.loads(_wr.lotes[0][0]["values"][0][0]) if _wr.lotes else {}
chk("limpiar_proyecto(desde=hoy) quita solo martes y miércoles: el lunes y el jueves se quedan",
    _nq == 2 and set(_nuevo) == {"lun", "jue"}, (_nq, _nuevo))

from core import projects_ui as PU                                         # noqa: E402
from core import claims as _CLm                                            # noqa: E402
_d = [_sustituir(I, is_configured=lambda: True, list_facturas=lambda g, cliente_id=None: [
          {"ID": "FAC-3", "Number": "0003", "Total": "6276.05", "Collected": "3000", "Status": "emitida",
           "ExpiryDate": "2099-01-01", "LinesJSON": json.dumps([{"importe": 5705.5, "proyecto_id": "PRJ-43"}])},
          {"ID": "FAC-9", "Number": "0009", "Total": "100", "Collected": "0", "Status": "emitida",
           "ExpiryDate": "2099-01-01", "LinesJSON": json.dumps([{"importe": 100, "proyecto_id": "PRJ-1"}])}]),
      _sustituir(_CLm, is_configured=lambda: True,
                 reclamaciones=lambda pid, incluir_anuladas=False: [
                     {"Number": "1", "Status": "issued", "ThisClaim": "5955.5", "Retention": "297.77", "Type": ""}],
                 retenido=lambda pid: {"retenido": 297.77, "liberado": 0.0, "pendiente": 297.77}),
      _sustituir(O, is_configured=lambda: True,
                 list_for=lambda pid, estado=None: [{"ID": "ORD-5", "Supplier": "Rail Co", "Amount": "4200"}]),
      _sustituir(R, dias_desde=lambda g, pid, desde: {"hl": 2}),
      _sustituir(PU, _nombres_de=lambda us, g: ["helper leader CI 1" if u == "hl" else u for u in us])]
try:
    _la = PU.lista_abierta("PRJ-43", "G", {"ID": "PRJ-43", "FieldAssigned": "hl"})
finally:
    for x in _d:
        x()
_lt = " | ".join(_la)
chk("lista_abierta: factura por cobrar ($3,276.05), certificación emitida, retención, orden, tablero y gente",
    "Invoice No. 0003" in _lt and "3,276.05" in _lt and "Claim #1 issued and not paid" in _lt
    and "297.77" in _lt and "Order ORD-5" in _lt and "**2 day(s)** on the board" in _lt
    and "Assigned to it: helper leader CI 1" in _lt and "0009" not in _lt, _la)

CIERRE = r'''
import streamlit as st
from core import projects_ui as PU, roster as R, flash
st.session_state.setdefault("_LL", [])
PU.lista_abierta = lambda pid, g, prj: ["Invoice No. 0003: **$3,276.05** still to collect."]
R.dias_desde = lambda g, pid, desde: {"hl": 2}
PU._guardar_datos_obra = lambda pid, g, prj, campos, ctx, cierre="", liberar=False: (
    st.session_state["_LL"].append(("guardar", cierre, liberar, campos.get("ManualStatus"))), st.rerun())
_PEND = {"campos": {"ManualStatus": st.session_state.get("_EST", "Cancelled")}, "ctx": {}, "est": st.session_state.get("_EST", "Cancelled")}
st.session_state.setdefault("_prj_cierre_PRJ-43", _PEND)
if st.session_state.get("_prj_cierre_PRJ-43"):
    PU._confirmar_cierre("PRJ-43", "G", {"ID": "PRJ-43", "FieldAssigned": "hl"}, st.session_state["_prj_cierre_PRJ-43"])
'''
at = AppTest.from_string(CIERRE, default_timeout=90)
at.run()
chk("la pregunta de cancelar se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("H18 · «Cancel this job?» con lo que queda abierto",
    any("Cancel this job?" in m.value for m in at.markdown)
    and any("Still open on it" in w.value and "3,276.05" in w.value for w in at.warning), [w.value for w in at.warning])
_cb = [c for c in at.checkbox if c.key == "cierre_lib_PRJ-43"]
chk("…con la casilla de quitarla del tablero desde hoy (2 días), marcada", _cb and _cb[0].value is True
    and "(2 day(s))" in _cb[0].label, [(c.key, c.label) for c in at.checkbox])
chk("…y dice que se avisará a la gente de que está CANCELADA",
    any("told the job is cancelled" in c.value for c in at.caption), [c.value for c in at.caption])
at.button(key="cierre_si_PRJ-43").click().run()
chk("«Yes, cancel it» guarda con cierre=Cancelled y liberando el tablero",
    ("guardar", "Cancelled", True, "Cancelled") in _ll(at), _ll(at))
at = AppTest.from_string(CIERRE, default_timeout=90)
at.run()
at.button(key="cierre_no_PRJ-43").click().run()
chk("«Back (nothing saved)» no guarda nada", not [x for x in _ll(at) if x[0] == "guardar"], _ll(at))

_s_pui = src("core/projects_ui.py")
_n, _det = funcion("core/projects_ui.py", "_detalle_proyecto")
chk("el formulario NO guarda directamente un paso a Cancelled/On hold: lo deja pendiente y pregunta",
    'if est_man in ("Cancelled", "On hold") and est_man != str(prj.get("ManualStatus", "") or ""):' in _det
    and 'st.session_state[f"_prj_cierre_{pid}"] = {"campos": _campos, "ctx": _ctx, "est": est_man}' in _det
    and "_guardar_datos_obra(pid, grupo, prj, _campos, _ctx)" in _det
    and _det.find("_confirmar_cierre(pid, grupo, prj, _cierre_pend)") < _det.find('with st.form(f"edit_{pid}"'), "")
_n, _gd = funcion("core/projects_ui.py", "_guardar_datos_obra")
chk("al cancelar, el aviso DICE «cancelled» a todos los asignados y libera desde hoy",
    '"This job has been cancelled. You are off it from today."' in _gd
    and "asignados if cierre else" in _gd and "_R.limpiar_proyecto(grupo, pid, desde=clock.today(grupo))" in _gd)

# ═════════════════════════════════════════════════════════════════════════════
sec("6. Lo visto verificando v669")
chk("los avisos de cobros con miles («$3,000.00», decían «$3000.00»)", I._dinero(3000) == "$3,000.00"
    and '"$%.2f"' not in src("core/invoices.py"), I._dinero(3000))
from core import auth as A                                                 # noqa: E402
from core import invoices_ui as IU                                         # noqa: E402
_d = [_sustituir(A, get_user=lambda u: {"User": "Admin2", "Name": "Bobo"} if u == "Admin2" else {})]
try:
    _nm = (IU._nombre_de("Admin2"), IU._nombre_de("nadie"), IU._nombre_de(""))
finally:
    for x in _d:
        x()
chk("el historial de cobros dice el NOMBRE (Bobo), no el login", _nm == ("Bobo", "nadie", ""), _nm)
HIST = r'''
import json
import streamlit as st
from core import invoices_ui as IU, auth
auth.get_user = lambda u: {"User": "Admin2", "Name": "Bobo"} if u == "Admin2" else {}
IU._historial_cobros({"CollectionsJSON": json.dumps([{"fecha": "2026-11-10", "monto": 3000},
    {"fecha": "2026-11-10", "monto": -3000, "origen": "refunded", "por": "Admin2"}])})
'''
at = AppTest.from_string(HIST, default_timeout=60)
at.run()
_mh = " ".join(m.value for m in at.markdown)
chk("…y así se PINTA: «-$3,000.00 · refunded to the client (Bobo)»", "refunded to the client (Bobo)" in _mh
    and "Admin2" not in _mh, _mh)
_d = [_sustituir(I, es_cotizada=lambda pid: False)]
try:
    _av = IU.avisos_de_mas([{"importe": 250.0, "proyecto_id": "PRJ-40"}], "G", {"PRJ-40": 0.45},
                           [{"ID": "PRJ-40", "Name": "C1 — Lift 2", "Status": "Planned"}])
finally:
    for x in _d:
        x()
chk("obra SIN cotización: el aviso de facturar de más sugiere la ganancia fija, no una variación",
    len(_av) == 1 and "fixed profit" in _av[0] and "variation" not in _av[0], _av)
chk("…y la ficha también (según `es_cotizada`)", "if _INV.es_cotizada(pid):" in _s_pui
    and "there as a fixed profit." in _s_pui)

print("\n" + ("TODO OK" if not FALLOS else f"{len(FALLOS)} FALLO(S): {FALLOS}"))
sys.exit(1 if FALLOS else 0)
