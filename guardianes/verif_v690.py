# -*- coding: utf-8 -*-
"""v690 · Ciclo 5 → mejoras 2/4, los CLIENTES (22/11):
- H1 · el teléfono del cliente se valida («abc» se guardaba sin aviso);
- H2 · el nombre de un cliente se corrige en su ficha: la ficha, el texto de sus obras y sus borradores;
- H18 · archivar un cliente dice lo que tiene abierto y pide confirmación, con un texto cierto;
- H17 · la ficha enseña sus cotizaciones (un botón por trato) y «New quote for this client»;
- H19 · una obra cotizada sin facturar se factura con las líneas de la cotización o con un depósito en %;
- H23 / D2 · el campo ve la persona de contacto del cliente de su obra y su teléfono.

Nada sale a la red ni escribe: funciones reales con sustitutos (hojas FALSAS que apuntan lo escrito) y AppTest.
"""
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


def _sustituir(obj, **kw):
    viejo = {k: getattr(obj, k) for k in kw}
    for k, v in kw.items():
        setattr(obj, k, v)
    return lambda: [setattr(obj, k, v) for k, v in viejo.items()]


from streamlit.testing.v1 import AppTest                                   # noqa: E402
from core import clientes as C                                             # noqa: E402
from core import quotes as Q                                               # noqa: E402
from core import projects as P                                             # noqa: E402
from core import invoices as INV                                           # noqa: E402
from core import clock                                                     # noqa: E402


class _Hoja:
    """Una hoja FALSA: lee sus filas y apunta (y aplica) lo que se escribiría."""
    def __init__(self, cab, filas):
        self.cab, self.filas, self.escrito, self.anadido = list(cab), [dict(x) for x in filas], [], []

    def get_all_records(self, **k):
        return [dict(x) for x in self.filas]

    def append_row(self, fila, **k):
        self.anadido.append(list(fila))

    def batch_update(self, lote, **k):
        from core.num import col_letter
        self.escrito += lote
        for it in lote:
            _col = "".join(ch for ch in it["range"] if ch.isalpha())
            _row = int("".join(ch for ch in it["range"] if ch.isdigit()))
            _k = next(h for i, h in enumerate(self.cab) if col_letter(i + 1) == _col)
            self.filas[_row - 2][_k] = it["values"][0][0]


print("1. El teléfono (H1)")
for _t, _ok in (("", True), ("0400 000 000", True), ("+61 (2) 9000-1003", True), ("02.9000.1003", True),
                ("abc", False), ("0400 abc 000", False), ("12345", False)):
    chk(f"telefono_valido({_t!r}) = {_ok}", C.telefono_valido(_t) is _ok)
_CLI = [{"ID": "CLI-8", "Group": "G", "Name": "C5 — Bayview Lifts Pty Ltd", "ContactName": "Sam", "Phone": "0400 000 000",
         "Email": "c5@example.com", "Address": "1 Test St", "Notes": "", "Active": "SI"},
        {"ID": "CLI-2", "Group": "G", "Name": "Meridian", "Active": "SI"},
        {"ID": "CLI-9", "Group": "OTRA", "Name": "Otra Co", "Active": "SI"}]
_HC = _Hoja(C.CLIENTES_HEADERS, _CLI)
_d = [_sustituir(C, _ws=lambda: (_HC, None), _records=lambda: [dict(x) for x in _HC.filas], _invalidate=lambda: None)]
try:
    _ok, _m = C.create_cliente("G", "Nuevo", telefono="abc")
    chk("crear con el teléfono «abc» se rechaza y no escribe", not _ok and "phone number" in _m and not _HC.anadido, _m)
    _ok, _m = C.update_cliente("CLI-8", {"Phone": "call me"})
    chk("editar con el teléfono «call me» se rechaza y no escribe", not _ok and "phone number" in _m and not _HC.escrito, _m)
    _ok, _m = C.update_cliente("CLI-8", {"Name": "   "})
    chk("un nombre vacío se rechaza", not _ok and "name is required" in _m, _m)
finally:
    for x in _d:
        x()

print("2. Renombrar un cliente (H2)")
_HC = _Hoja(C.CLIENTES_HEADERS, _CLI)
_OBRAS = [{"ID": "PRJ-46", "Group": "G", "Name": "C5 — Lift 1", "Client": "C5 — Bayview Lifts Pty Ltd", "ClientID": "CLI-8"},
          {"ID": "PRJ-47", "Group": "G", "Name": "C5 — viejo", "Client": "c5 — bayview lifts pty ltd", "ClientID": ""},
          {"ID": "PRJ-48", "Group": "G", "Name": "Otra", "Client": "Meridian", "ClientID": "CLI-2"}]
_UPD, _BORR = [], []
_d = [_sustituir(C, _ws=lambda: (_HC, None), _records=lambda: [dict(x) for x in _HC.filas], _invalidate=lambda: None),
      _sustituir(P, list_projects=lambda **k: [dict(x) for x in _OBRAS],
                 update_project=lambda pid, f: (_UPD.append((pid, dict(f))), (True, "ok"))[1]),
      _sustituir(Q, renombrar_cliente_borradores=lambda g, cid, n: (_BORR.append((g, cid, n)), 2)[1])]
try:
    _ok, _m = C.renombrar("CLI-8", "Meridian", "G")
    chk("a un nombre que ya tiene OTRO cliente del grupo, no", not _ok and "already exists" in _m and not _HC.escrito, _m)
    _ok, _m = C.renombrar("CLI-9", "X", "G")
    chk("un cliente de OTRA empresa no se renombra", not _ok, _m)
    _ok, _m = C.renombrar("CLI-8", "  C5 —  Bayview Lifts   (Sydney) ", "G")
    chk("renombrado (con los espacios limpios) en la ficha", _ok and _HC.filas[0]["Name"] == "C5 — Bayview Lifts (Sydney)",
        (_ok, _m, _HC.filas[0]["Name"]))
    chk("sus DOS obras (la de su ID y la que casaba por el nombre viejo) con el nombre nuevo Y su ID; la otra no",
        sorted(_UPD) == [("PRJ-46", {"Client": "C5 — Bayview Lifts (Sydney)", "ClientID": "CLI-8"}),
                         ("PRJ-47", {"Client": "C5 — Bayview Lifts (Sydney)", "ClientID": "CLI-8"})], _UPD)
    chk("sus borradores de cotización, también", _BORR == [("G", "CLI-8", "C5 — Bayview Lifts (Sydney)")], _BORR)
    chk("y lo dice: «2 project(s) and 2 draft quote(s)… keep the name they were issued with»",
        "2 project(s) and 2 draft quote(s)" in _m and "keep the name they were issued with" in _m, _m)
    _ok, _m = C.renombrar("CLI-8", "C5 — Bayview Lifts (Sydney)", "G")
    chk("el mismo nombre otra vez no escribe nada", _ok and "Nothing changed" in _m, _m)
finally:
    for x in _d:
        x()

print("3. Los borradores de cotización (solo los borradores de ESE cliente)")
_qr = lambda cid, cli, st_: {"ID": cid, "Group": "G", "ClientID": cli, "ClientName": "Viejo", "Status": st_,   # noqa: E731
                             "ValidUntil": "2026-12-30"}
_HQ = _Hoja(Q.HEADERS, [_qr("Q1", "CLI-8", "draft"), _qr("Q2", "CLI-8", "sent"), _qr("Q3", "CLI-2", "draft"),
                        _qr("Q4", "CLI-8", "draft")])
_d = [_sustituir(Q, _ws=lambda: _HQ, _invalidate=lambda: None), _sustituir(clock, today=lambda *a, **k: date(2026, 11, 22))]
try:
    _n = Q.renombrar_cliente_borradores("G", "CLI-8", "Nuevo")
    chk("2 cambiadas: Q1 y Q4; la enviada (Q2) y la de otro cliente (Q3), no",
        _n == 2 and [x["ClientName"] for x in _HQ.filas] == ["Nuevo", "Viejo", "Viejo", "Nuevo"],
        (_n, [x["ClientName"] for x in _HQ.filas]))
finally:
    for x in _d:
        x()

print("4. Lo que un cliente tiene abierto (H18)")
_L = [{"concepto": "Panel", "cantidad": 12.0, "costo_total": 3840.0, "precio_total": 4608.0}]
_QS = [{"ID": "C81", "Group": "G", "ClientID": "CLI-8", "Number": "0008", "Version": "1", "Status": "sent",
        "ValidUntil": "2026-12-30", "Total": "12170.4", "LinesJSON": json.dumps(_L)},
       {"ID": "C82", "Group": "G", "ClientID": "CLI-8", "Number": "0008", "Version": "2", "Status": "accepted",
        "ProjectID": "PRJ-46", "ValidUntil": "2026-12-30", "Total": "12170.4", "Subtotal": "11064", "LinesJSON": json.dumps(_L)},
       {"ID": "C91", "Group": "G", "ClientID": "CLI-8", "Number": "0009", "Version": "1", "Status": "sent",
        "ValidUntil": "2026-12-30", "Total": "500", "LinesJSON": json.dumps(_L)}]
_d = [_sustituir(Q, _records=lambda: [dict(x) for x in _QS]),
      _sustituir(INV, list_facturas=lambda g, cid=None: [{"Total": "1000", "Collected": "250", "Status": "emitida"},
                                                          {"Total": "900", "Collected": "0", "Status": "anulada"}]),
      _sustituir(clock, today=lambda *a, **k: date(2026, 11, 22))]
try:
    _ab = C.abierto("G", "CLI-8", [{"Status": "Planned"}, {"Status": "Completed"}, {"Status": "Cancelled"}])
    chk("1 obra sin terminar · 1 cotización esperando (la 0009; la 0008 está ganada) · $750.00 por cobrar (sin anuladas)",
        _ab == ["1 job(s) not finished", "1 quote(s) awaiting a reply", "$750.00 still to collect"], _ab)
finally:
    for x in _d:
        x()

print("5. La ficha del cliente (AppTest): nombre, cotizaciones, archivar")
FICHA = r'''
import json
import streamlit as st
from core import clientes_ui as CU, clientes as C, projects as P, alerts, expenses, invoices as INV, quotes as Q, clock
import datetime as dt
clock.today = lambda *a, **k: dt.date(2026, 11, 22)
_F = dict(st.session_state["_FICHA"])
C.ficha_de = lambda g, k: dict(_F)
C.get_cliente = lambda cid: dict(_F)
C.abierto = lambda g, cid, proys=None: st.session_state.get("_ABIERTO", [])
_LL = st.session_state.setdefault("_LL", [])
C.update_cliente = lambda cid, f: (_LL.append(("upd", cid, dict(f))), (True, "ok"))[1]
C.renombrar = lambda cid, n, g: (_LL.append(("ren", cid, n)), (True, "Client renamed: ok"))[1]
C.set_activo = lambda cid, a: (_LL.append(("act", cid, a)), (True, "Client archived."))[1]
P.list_projects = lambda **k: [{"ID": "PRJ-46", "Group": "G", "Name": "C5 — Lift 1", "Client": _F["Name"],
                                "ClientID": "CLI-8", "Status": "Planned", "Progress": "0"}]
P.project_hours_bulk = lambda g: {}
alerts.is_configured = lambda: False
expenses.is_configured = lambda: False
INV.is_configured = lambda: False
Q._records = lambda: [dict(x) for x in st.session_state["_QS"]]
st.session_state.setdefault("auth", {"usuario": "admin2", "rol": "administrator", "grupo": "G", "nombre": "Bobo"})
CU._detalle_cliente("G", "CLI-8")
'''
_FICHA = dict(_CLI[0])


def _ficha(**ss):
    a = AppTest.from_string(FICHA, default_timeout=90)
    a.session_state["_FICHA"] = ss.pop("_FICHA", _FICHA)
    a.session_state["_QS"] = _QS
    for k, v in ss.items():
        a.session_state[k] = v
    a.run()
    return a


def _txt(a):
    return " ¦ ".join(str(x.value) for x in list(a.markdown) + list(a.caption) + list(a.info) + list(a.warning)
                      + list(a.error)).replace("\\", "")


at = _ficha()
chk("la ficha se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("…con el NOMBRE en el formulario", any(x.label == "Client name *" and x.value == _FICHA["Name"] for x in at.text_input),
    [(x.label, x.value) for x in at.text_input])
# sin el escape del «$» de `theme.dinero` (lo pone a propósito: sin él Streamlit lo lee como LaTeX, v309)
_bq = {str(b.key): str(b.label).replace("\\", "") for b in at.button if str(b.key).startswith("cli_cot_")}
chk("un botón por TRATO: la 0008 con su v2 aceptada y «2 versions», y la 0009 enviada",
    "**No. 0008 v2** · Accepted · $12,170 · 2 versions" in _bq.get("cli_cot_C82", "")
    and "**No. 0009** · Sent · $500" in _bq.get("cli_cot_C91", "") and len(_bq) == 2, _bq)
at.button(key="cli_cot_C82").click().run()
chk("…que abre ESA cotización en Finance → Quotes", at.session_state["_cot_open"] == "C82"
    and at.session_state["_admin_nav_pending"] == ("finanzas", "📄 Cotizaciones"))
at = _ficha()
at.button(key="cli_newcot_CLI-8").click().run()
chk("«New quote for this client» abre el alta con el cliente ya elegido",
    at.session_state["_cot_nueva"] is True and at.session_state["cot_new_cli"] == _FICHA["Name"]
    and at.session_state["_admin_nav_pending"] == ("finanzas", "📄 Cotizaciones"))
at = _ficha(_FICHA=dict(_FICHA, Active="NO"))
chk("…y a un cliente ARCHIVADO no se le ofrece (el alta no lo tiene en la lista)",
    not any(str(b.key) == "cli_newcot_CLI-8" for b in at.button))
chk("…y su aviso dice la verdad: «A client with jobs still shows in the list through them»",
    "A client with jobs still shows in the list through them" in _txt(at), _txt(at)[:400])

at = _ficha(_ABIERTO=["1 job(s) not finished", "1 quote(s) awaiting a reply"])
chk("archivar con cosas abiertas lo DICE: «This client still has: 1 job(s) not finished · 1 quote(s)…»",
    "This client still has: 1 job(s) not finished · 1 quote(s) awaiting a reply." in _txt(at), _txt(at)[-600:])
chk("…y «Archive this record» está PARADO hasta confirmar", at.button(key="cli_arch_CLI-8").disabled)
at.checkbox(key="cli_arch_conf_CLI-8").check().run()
at.button(key="cli_arch_CLI-8").click().run()
chk("…confirmado, archiva", ("act", "CLI-8", False) in at.session_state["_LL"], at.session_state["_LL"])
at = _ficha()
chk("sin nada abierto, se archiva sin casilla", not at.button(key="cli_arch_CLI-8").disabled
    and not any(str(c.key) == "cli_arch_conf_CLI-8" for c in at.checkbox))

at = _ficha()
next(x for x in at.text_input if x.label == "Client name *").set_value("C5 — Bayview (Sydney)")
next(b for b in at.button if "Save record" in str(b.label)).click().run()
chk("«Save record» con el nombre cambiado guarda lo demás y RENOMBRA",
    ("ren", "CLI-8", "C5 — Bayview (Sydney)") in at.session_state["_LL"]
    and any(x[0] == "upd" for x in at.session_state["_LL"]), at.session_state["_LL"])
chk("…y la ficha queda abierta por su ID", at.session_state["_cli_open"] == "CLI-8")

print("6. Facturar una obra cotizada: sus líneas o un depósito (H19)")
FAC = r'''
import json
import datetime as dt
import pandas as pd
import streamlit as st
from core import invoices_ui as IU, invoices as I, clientes as C, projects as P, quotes as Q, clock, auth, contable
clock.today = lambda *a, **k: dt.date(2026, 11, 22)
C.list_clientes = lambda *a, **k: [{"ID": "CLI-8", "Name": "C5", "Group": "G"}]
P.list_projects = lambda **k: [{"ID": "PRJ-46", "Group": "G", "Name": "C5 — Lift 1", "Client": "C5", "ClientID": "CLI-8",
                                "Status": "Planned", "Progress": "0"}]
I.por_certificar = lambda pid, g, p=None: {"pendiente": 11064.0, "certificable": 0.0, "avance": 0.0, "ganado": 0.0}
I.es_cotizada = lambda pid: True
I.facturado_por_proyecto = lambda g: {"PRJ-46": st.session_state.get("_YA", 0.0)}
_L = [{"concepto": "Panel", "cantidad": 12.0, "precio_total": 4608.0},
      {"concepto": "Commissioning", "cantidad": 1.0, "precio_total": 1632.0},
      {"concepto": "Interlock", "cantidad": 12.0, "precio_total": 2664.0},
      {"concepto": "Crane hire", "cantidad": 1.0, "precio_total": 2160.0}]
Q.cotizacion_de_proyecto = lambda pid: {"ID": "C82", "Number": "0008", "Version": "2", "Subtotal": "11064",
                                        "LinesJSON": json.dumps(_L)}
contable.identidad = lambda g: {"abn": "1", "plazo": 14, "legal": "X"}
contable.tiene_datos_pago = lambda i: True
auth.group_tax_default = lambda g: 10.0
IU.avisos_de_mas = lambda *a, **k: []
st.session_state.setdefault("auth", {"usuario": "admin2", "rol": "administrator", "grupo": "G", "nombre": "Bobo"})
st.session_state.setdefault("_fac_prj_pending", "PRJ-46")
IU._nueva_factura("G")
'''


def _fac(**ss):
    a = AppTest.from_string(FAC, default_timeout=90)
    for k, v in ss.items():
        a.session_state[k] = v
    a.run()
    return a


at = _fac()
chk("la factura nueva se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_rad = next((r for r in at.radio if str(r.key) == "fac_modo_PRJ-46"), None)
chk("una obra cotizada sin facturar ofrece «Invoice it as»: precio pendiente · líneas de la cotización · depósito",
    _rad is not None and list(_rad.options) == ["The price still to invoice", "The quote's lines", "A deposit (%)"],
    getattr(_rad, "options", None))
chk("…y el aviso del adelanto dice que se puede elegir arriba", "For a deposit or the quote's lines, choose it above" in _txt(at),
    _txt(at)[:500])


def _lineas(a):
    """Las filas del editor de líneas: el `Dataframe` de AppTest que es editable (`editing_mode` ≠ 0)."""
    for x in a.dataframe:
        if x.proto.editing_mode:
            return [(str(r["Concepto"]), round(float(r["Importe"]), 2)) for r in x.value.to_dict("records")]
    return []


chk("por defecto, una línea con todo lo pendiente (como antes)", _lineas(at) == [("Works — C5 — Lift 1", 11064.0)],
    _lineas(at))
at.radio(key="fac_modo_PRJ-46").set_value("lineas").run()
chk("«The quote's lines» pone las CUATRO líneas de la 0008 v2, con su cantidad y su precio",
    _lineas(at) == [("Panel × 12", 4608.0), ("Commissioning", 1632.0), ("Interlock × 12", 2664.0),
                    ("Crane hire", 2160.0)], _lineas(at))
chk("…y lo dice: «The lines of the accepted quote No. 0008 v2»", "The lines of the accepted quote **No. 0008 v2**" in _txt(at),
    _txt(at)[:500])
at.radio(key="fac_modo_PRJ-46").set_value("deposito").run()
chk("«A deposit (%)» al 30 %: una línea de $3,319.20", _lineas(at) == [("Deposit 30% — C5 — Lift 1", 3319.2)], _lineas(at))
at.number_input(key="fac_dep_PRJ-46").set_value(50.0).run()
chk("…al 50 %: $5,532.00", _lineas(at) == [("Deposit 50% — C5 — Lift 1", 5532.0)], _lineas(at))
at = _fac(_YA=2000.0)
chk("con algo ya facturado en la obra no se ofrece (las líneas de la cotización la facturarían dos veces)",
    not any(str(r.key) == "fac_modo_PRJ-46" for r in at.radio))

print("7. El contacto del cliente para el campo (D2)")
CAMPO = r'''
import streamlit as st
from core import projects_ui as PU, clientes as C
C.get_cliente = lambda cid: {"ID": cid, "ContactName": "Sam <b>Site</b>", "Phone": st.session_state.get("_TEL", "0400 000 000")}
PU._contacto_cliente_campo(dict(st.session_state["_PRJ"]))
'''


def _campo(prj, **ss):
    a = AppTest.from_string(CAMPO, default_timeout=60)
    a.session_state["_PRJ"] = prj
    for k, v in ss.items():
        a.session_state[k] = v
    a.run()
    return a, " ¦ ".join(str(x.value) for x in a.markdown)


at, _m = _campo({"ID": "PRJ-46", "ClientID": "CLI-8", "Type": "Installation"})
chk("con ficha enlazada: «Client contact: Sam…» y el teléfono para LLAMAR (tel:0400000000)",
    "Client contact: Sam &lt;b&gt;Site&lt;/b&gt;" in _m and 'href="tel:0400000000"' in _m and ">0400 000 000<" in _m, _m)
at, _m = _campo({"ID": "PRJ-46", "ClientID": "CLI-8", "Type": "Installation"}, _TEL="abc")
chk("un teléfono sin dígitos no hace enlace", "tel:" not in _m and "Sam" in _m, _m)
at, _m = _campo({"ID": "PRJ-46", "ClientID": "", "Client": "C5", "Type": "Installation"})
chk("sin ficha enlazada no se adivina nada", not _m.strip(), _m)

import ast                                                                  # noqa: E402
_fp = next(n for n in ast.walk(ast.parse(open(os.path.join(RAIZ, "core", "projects_ui.py"), encoding="utf-8").read()))
           if isinstance(n, ast.FunctionDef) and n.name == "render_field_projects")
chk("«My projects» del campo LLAMA a `_contacto_cliente_campo(prj)` (si no, lo de arriba no se ve)",
    any(isinstance(c, ast.Call) and ast.unparse(c.func) == "_contacto_cliente_campo" for c in ast.walk(_fp)))

print("\n" + ("TODO OK" if not FALLOS else f"{len(FALLOS)} FALLO(S): {FALLOS}"))
sys.exit(1 if FALLOS else 0)
