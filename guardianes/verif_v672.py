# -*- coding: utf-8 -*-
"""v672 · Documentos que salen hacia fuera, y formatos (ciclo 2, mejoras 4/5) + lo visto verificando v671.

H24 la factura dice cómo pagar (titular, BSB, cuenta, referencia = nº) y el contacto del emisor; se rellenan en
    «Tax identity and payment terms» y, si faltan, se avisa como con el ABN.
H11 sin el estado interno en los PDF (factura, certificación, cotización, colilla), o en palabras para quien lo lee.
H5  estados con mayúscula (`i18n.estado`): facturas, cotizaciones, colillas, certificaciones y el buscador.
H14 certificaciones: $ con miles, fechas DD/MM/YYYY, «10%» y «$0.00» sin signo.
H16 Accounting: «since DD/MM/YYYY HH:MM by <nombre>».
H28 la actividad parada: «should have started on 10/11 · 2-day activity», dentro de `t()`.
H26 el buscador encuentra «Invoice 0004», «4», «#4» y «no. 4», y el resultado de una factura dice «Overdue · $250.00».
H30 el rastro no apunta lo que no cambió, y el peso sin grupo no se reescribe.
v671 · la vista previa de Generate no da base a quien deja fuera; el aviso de la colilla de un administrador manda al
propietario; guardar el fondo de super o el nº de nómina dice lo que quedó.

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


from pypdf import PdfReader                                                # noqa: E402
from streamlit.testing.v1 import AppTest                                   # noqa: E402
from core import i18n                                                      # noqa: E402
from core import auth as A                                                 # noqa: E402
from core import contable as CB                                            # noqa: E402
from core import auditoria as AUD                                          # noqa: E402

# los originales: los guiones de AppTest corren en ESTE proceso y dejan sus sustitutos puestos (trampa 48)
_IDENTIDAD = CB.identidad
_GTS = A.group_text_setting


def _texto_pdf(b):
    return " ".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(b)).pages)


_ID_LLENA = {"abn": "12 345 678 901", "legal": "Harbour Lifts Pty Ltd", "plazo": 14,
             "direccion": "1 Test St, Sydney NSW 2000", "email": "accounts@harbour.test", "telefono": "02 9000 0000",
             "titular": "Harbour Lifts Pty Ltd", "bsb": "062-000", "cuenta": "12345678"}
_ID_SIN_BANCO = dict(_ID_LLENA, titular="", bsb="", cuenta="")

# ═════════════════════════════════════════════════════════════════════════════
sec("1. Estados con mayúscula (H5)")
chk("i18n.estado: el estado suelto con la primera en mayúscula, el dato igual",
    (i18n.estado("cobrada"), i18n.estado("aceptada"), i18n.estado("issued"), i18n.estado(""), i18n.estado("pagada"))
    == ("Collected", "Accepted", "Issued", "", "Paid"),
    (i18n.estado("cobrada"), i18n.estado("aceptada"), i18n.estado("issued")))
chk("…y `etiqueta` sigue en minúscula (va dentro de frases)", i18n.etiqueta("cobrada") == "collected")
from core import invoices_ui as IU                                         # noqa: E402
from core import quotes_ui as QU                                           # noqa: E402
from core import quotes as Q                                               # noqa: E402
from core import payroll_ui as PUI                                         # noqa: E402
chk("facturas: «Overdue», «Partial», «Collected» en el detalle y en la celda",
    IU._est_fmt("vencida").endswith("Overdue") and IU._est_fmt("parcial").endswith("Partial")
    and IU._est_celda({"Status": "anulada"}).endswith("Voided"), (IU._est_fmt("vencida"), IU._est_celda({"Status": "anulada"})))
chk("cotizaciones: «Accepted», «Draft», y la vencida «Expired»",
    (QU._est_txt(Q.ACEPTADA), QU._est_txt(Q.BORRADOR), QU._est_txt(Q.VENCIDA)) == ("Accepted", "Draft", "Expired"),
    (QU._est_txt(Q.ACEPTADA), QU._est_txt(Q.BORRADOR), QU._est_txt(Q.VENCIDA)))
chk("colillas: «Paid», «Issued» en la celda", PUI._est_celda({"Status": "pagada"}).endswith("Paid")
    and PUI._est_celda({"Status": "emitida"}).endswith("Issued"), PUI._est_celda({"Status": "pagada"}))
_n, _de = funcion("core/payroll_ui.py", "_detalle")
_n, _mc = funcion("core/payroll_ui.py", "render_mis_colillas")
chk("…en la cabecera del detalle, y «Paid on …» en las colillas de la persona",
    "_estado_txt(est)" in _de and "_etq(" not in _de and 't("Paid on {d}", d=_dmy(_pago))' in _mc)
_n, _bu = funcion("core/home_ui.py", "buscar")
chk("el buscador ya no tiene su propia mayúscula (`_mayus`): usa la de i18n", "_mayus" not in src("core/home_ui.py")
    and _bu.count("_estado_txt(") >= 3)

# ═════════════════════════════════════════════════════════════════════════════
sec("2. La identidad del grupo: contacto y datos de pago (H24)")
chk("Groups lleva las 6 columnas nuevas, AL FINAL", A.GROUPS_HEADERS[-6:] == [
    "Address", "ContactEmail", "ContactPhone", "BankAccountName", "BankBSB", "BankAccountNumber"], A.GROUPS_HEADERS[-7:])
_vals = {"ABN": "1", "LegalName": "L", "PaymentTermsDays": "30", "Address": "Dir", "ContactEmail": "e@x.test",
         "ContactPhone": "02", "BankAccountName": "Tit", "BankBSB": "062-000", "BankAccountNumber": "123456"}
_d = _sustituir(A, group_text_setting=lambda g, k, d="": _vals.get(k, d))
try:
    _idn = _IDENTIDAD("G")
finally:
    _d()
chk("contable.identidad las lee", (_idn["direccion"], _idn["email"], _idn["telefono"], _idn["titular"], _idn["bsb"],
                                    _idn["cuenta"], _idn["plazo"]) == ("Dir", "e@x.test", "02", "Tit", "062-000", "123456", 30),
    _idn)
chk("contacto_emisor: la dirección, y email · teléfono", CB.contacto_emisor(_ID_LLENA)
    == ["1 Test St, Sydney NSW 2000", "accounts@harbour.test · 02 9000 0000"], CB.contacto_emisor(_ID_LLENA))
chk("…y sin nada, ninguna línea (el PDF sale como antes)", CB.contacto_emisor({}) == [])
chk("tiene_datos_pago exige BSB Y cuenta", CB.tiene_datos_pago(_ID_LLENA) and not CB.tiene_datos_pago(_ID_SIN_BANCO)
    and not CB.tiene_datos_pago({"bsb": "062-000"}) and not CB.tiene_datos_pago({"cuenta": "1"}))
chk("bsb_normal: 6 cifras → «062-000»; otra cosa → vacío",
    (CB.bsb_normal("062000"), CB.bsb_normal("062 000"), CB.bsb_normal("062-000"), CB.bsb_normal("62000"),
     CB.bsb_normal("abc")) == ("062-000", "062-000", "062-000", "", ""))
chk("cuenta_ok: de 5 a 10 cifras", CB.cuenta_ok("12345678") and CB.cuenta_ok("1234 5678") and not CB.cuenta_ok("1234")
    and not CB.cuenta_ok("12345678901") and not CB.cuenta_ok("12a45"))
_n, _cf = funcion("core/contable.py", "aviso_sin_pago")
chk("el aviso dice dónde se ponen (Administration → Groups)", "Administration → Groups" in _cf and "t(" in _cf)
_txt_conta = src("core/contable.py")
chk("Accounting también avisa sin datos de pago, junto al del ABN",
    "if not tiene_datos_pago(ident):\n        avisos.append(aviso_sin_pago())" in _txt_conta)

# ═════════════════════════════════════════════════════════════════════════════
sec("3. El PDF de la factura (H24, H11)")
from core import invoice_pdf as IP                                         # noqa: E402


def _fac(tot, cob, status="emitida", venc="2026-11-24"):
    return {"ID": "FAC-4", "Group": "G", "Number": "0004", "Date": "2026-11-10", "ExpiryDate": venc,
            "ClientName": "C1 Harbour", "Total": str(tot), "Subtotal": str(tot), "TaxPct": "0", "Tax": "0",
            "Collected": str(cob), "Status": status, "Note": "", "LinesJSON": json.dumps([{"concepto": "Lift 1", "importe": tot}])}


def _pdf_fac(f, ident):
    _d = _sustituir(CB, identidad=lambda g: dict(ident))
    try:
        return _texto_pdf(IP.generate_invoice_pdf(f, {"Name": "C1 Harbour"}, "G"))
    finally:
        _d()


_tx = _pdf_fac(_fac(250, 0), _ID_LLENA)
chk("dice cómo pagar: titular, BSB, cuenta y la REFERENCIA = el nº de factura",
    "How to pay" in _tx and "062-000" in _tx and "12345678" in _tx and "Reference" in _tx
    and "Harbour Lifts Pty Ltd" in _tx, _tx[-500:])
_ref = _tx[_tx.find("Reference"):_tx.find("Reference") + 30]
chk("…con «0004» como referencia", "0004" in _ref, _ref)
chk("el emisor con su dirección y su email · teléfono", "1 Test St, Sydney NSW 2000" in _tx
    and "accounts@harbour.test · 02 9000 0000" in _tx, _tx[:400])
chk("H11 · sin «Status» (era «Status | partial»)", "Status" not in _tx, _tx[:600])
chk("…y sigue diciendo lo que importa: «Balance due $250.00»", "Balance due" in _tx and "$250.00" in _tx)
_tx = _pdf_fac(_fac(250, 250), _ID_LLENA)
chk("cobrada entera: sin «How to pay» (no queda nada que pagar)", "How to pay" not in _tx, _tx[-300:])
_tx = _pdf_fac(_fac(250, 0, "anulada"), _ID_LLENA)
chk("anulada: el sello VOID y sin «How to pay»", "VOID" in _tx and "How to pay" not in _tx, _tx[-300:])
_tx = _pdf_fac(_fac(250, 0), _ID_SIN_BANCO)
chk("sin BSB y cuenta, sin «How to pay» (mejor nada que medio dato)", "How to pay" not in _tx and "BSB" not in _tx,
    _tx[-300:])
_tx = _pdf_fac(_fac(250, 0), {"abn": "", "legal": "", "plazo": 14})
chk("una identidad VIEJA (sin las claves nuevas) no rompe el PDF", "TAX INVOICE" in _tx and "How to pay" not in _tx)
_tx = _pdf_fac(dict(_fac(250, 0), ClientName="<b>x"), dict(_ID_LLENA, direccion="<b>Calle & 1", titular="<i>T"))
chk("lo que escribe una persona va escapado (v653): «<b>Calle & 1» se ve tal cual", "<b>Calle & 1" in _tx
    and "<i>T" in _tx, _tx[:300])

# ═════════════════════════════════════════════════════════════════════════════
sec("4. La certificación, la cotización y la colilla (H24, H11, H14)")
from core import claim_pdf as CP                                           # noqa: E402
from core import claims as CL                                              # noqa: E402


def _clm(status="issued", antes=0.0, ret=0.0):
    return {"ID": "CLM-PRJ-0042-001", "Group": "G", "ProjectID": "PRJ-0042", "Number": "1", "Date": "2026-11-10",
            "PeriodTo": "2026-11-30", "PctComplete": "10", "ContractValue": "57055", "VariationsValue": "0",
            "WorkDone": "5705.5", "PreviouslyClaimed": str(antes), "RetentionPct": "5", "Retention": str(ret),
            "ThisClaim": "5705.5", "Status": status, "Note": "", "Type": ""}


def _pdf_clm(rec, ident=_ID_LLENA):
    _d = _sustituir(CB, identidad=lambda g: dict(ident))
    try:
        return _texto_pdf(CP.generate_claim_pdf(rec, [], {"Name": "C1"}, "G", {"Name": "Lift 1"}))
    finally:
        _d()


_tx = _pdf_clm(_clm())
chk("H14 · fechas DD/MM/YYYY (era «Date | 2026-11-10»)", "10/11/2026" in _tx and "30/11/2026" in _tx
    and "2026-11-10" not in _tx, _tx[:600])
chk("H14 · «Less previously claimed $0.00», sin signo (era «-$0.00»)", "-$0.00" not in _tx and "$0.00" in _tx, _tx)
chk("H11 · sin «Status | issued»", "Status" not in _tx and "issued" not in _tx.lower(), _tx[:600])
chk("H24 · dice cómo pagar, con el ID de la certificación como referencia",
    "How to pay" in _tx and "CLM-PRJ-0042-001" in _tx, _tx[-400:])
chk("…y el emisor con su contacto", "accounts@harbour.test" in _tx)
_tx = _pdf_clm(_clm(antes=1500, ret=285.28))
chk("un importe que se resta sigue con su «-»: «-$1,500.00» y «-$285.28»", "-$1,500.00" in _tx and "-$285.28" in _tx, _tx)
_tx = _pdf_clm(_clm(CL.ANULADA))
chk("anulada: el sello VOID y sin «How to pay»", "VOID" in _tx and "How to pay" not in _tx, _tx[-300:])
_tx = _pdf_clm(_clm(CL.PAGADA))
chk("pagada: sin «How to pay»", "How to pay" not in _tx, _tx[-300:])
chk("CL._dinero: «$5,657.73» (el aviso decía «net payable 5657.73»)", CL._dinero(5657.73) == "$5,657.73")
_n, _cr = funcion("core/claims.py", "crear_reclamacion")
_n2, _lb = funcion("core/claims.py", "crear_liberacion")
chk("…y los avisos de emitir lo usan; en claims.py no queda un importe con «%.2f» (la retención tampoco)",
    "_dinero(d[\"neto\"])" in _cr and "_dinero(_imp)" in _lb and '"%.2f"' not in src("core/claims.py"),
    (_cr[-200:], _lb[-200:]))
chk("…y con dos importes en el mismo aviso, escapados (dos «$» abren una fórmula, v309)",
    CL._dinero(1, escapado=True) == "\\$1.00" and "_dinero(_imp, escapado=True), held=_dinero(_pend, escapado=True)" in _lb)

from core import quote_pdf as QP                                           # noqa: E402
_d = _sustituir(CB, identidad=lambda g: dict(_ID_LLENA))
try:
    _tx = _texto_pdf(QP.generate_quote_pdf({"ID": "COT-6", "Group": "G", "Number": "0006", "Date": "2026-11-10",
                                             "ValidUntil": "2026-12-10", "ClientName": "C1", "Status": "enviada",
                                             "LinesJSON": "[]", "Version": "1"}, {"Name": "C1"}, "G"))
finally:
    _d()
chk("cotización: sin «Status» (H11) y con el contacto del emisor (H24)", "Status" not in _tx and "Sent" not in _tx
    and "accounts@harbour.test" in _tx, _tx[:600])

from core import payslip_pdf as PP                                         # noqa: E402


def _pdf_nom(status, pago=""):
    n = {"ID": "NOM-0002", "Group": "G", "User": "u1", "Name": "Ana", "PeriodFrom": "2026-11-03",
         "PeriodTo": "2026-11-09", "Hours": "7.99", "HourlyRate": "55", "Base": "439.45", "Net": "439.45",
         "Status": status, "PaymentDate": pago,
         "ConceptsJSON": json.dumps([{"concepto": "Superannuation", "tipo": "aporte", "monto": 50.54},
                                     {"concepto": "Income tax withheld (PAYG)", "tipo": "deduccion", "monto": 10}])}
    _d = [_sustituir(CB, identidad=lambda g: dict(_ID_LLENA)), _sustituir(A, get_user=lambda u: {"Name": "Ana"})]
    try:
        return _texto_pdf(PP.generate_payslip_pdf(n, "G"))
    finally:
        for x in _d:
            x()


_tx = _pdf_nom("pagada", "2026-11-09")
chk("colilla pagada: «Paid on 09/11/2026», sin «Status» (H11)", "Paid on" in _tx and "09/11/2026" in _tx
    and "Status" not in _tx, _tx[:700])
chk("…y el tipo de cada concepto con mayúscula (H5): «Earning», «Contribution», «Deduction»",
    "Earning" in _tx and "Contribution" in _tx and "Deduction" in _tx, _tx[:900])
chk("colilla sin pagar: «Not paid yet»", "Not paid yet" in _pdf_nom("emitida"))
chk("colilla anulada: «Void, not payable»", "Void, not payable" in _pdf_nom("anulada"))

# ═════════════════════════════════════════════════════════════════════════════
sec("5. Las pantallas de facturas: el aviso sin datos de pago (H24)")
_n, _nf = funcion("core/invoices_ui.py", "_nueva_factura")
chk("la factura nueva avisa ANTES de emitir", "_sin_pago = not _CB.tiene_datos_pago(_idn)" in _nf
    and "st.warning(_CB.aviso_sin_pago(icono=True))" in _nf
    and _nf.find("aviso_sin_pago") < _nf.find('key="fac_emit"'), "")
# ⚠️ y en la pantalla, no solo en el texto (romper_v672: con `if False:` la sonda de arriba seguía verde)
NUEVA = r'''
import streamlit as st
from core import invoices_ui as IU, clientes as C, projects as P, contable
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G", "nombre": "Jefa"})
C.list_clientes = lambda *a, **k: [{"ID": "CLI-1", "Name": "C1"}]
P.list_projects = lambda *a, **k: []
contable.identidad = lambda g: dict(st.session_state.get("_ID", {"abn": "1", "legal": "X", "plazo": 14}))
IU._nueva_factura("G")
'''
at = AppTest.from_string(NUEVA, default_timeout=60)
at.session_state["_fac_nueva"] = True
at.run()
chk("la factura nueva se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("…sin datos de pago, AVISA en pantalla antes de emitir", any("has no bank details" in w.value for w in at.warning),
    [w.value for w in at.warning])
at = AppTest.from_string(NUEVA, default_timeout=60)
at.session_state["_fac_nueva"] = True
at.session_state["_ID"] = dict(_ID_LLENA)
at.run()
chk("…y con ellos puestos, no", not any("has no bank details" in w.value for w in at.warning), [w.value for w in at.warning])

GUION = r'''
import datetime as dt
import json
import streamlit as st
from core import invoices as I, clientes as C, clock, contable, xero_ui, flash
clock.today = lambda *a, **k: dt.date(2026, 11, 10)
_F = {"ID": "FAC-6", "Group": "G", "ClientID": "CLI-1", "ClientName": "C1", "Number": "0006", "Date": "2026-10-20",
      "ExpiryDate": "2026-10-27", "Total": "250", "Subtotal": "250", "TaxPct": "0", "Tax": "0",
      "Collected": st.session_state.get("_COB", "0"), "Status": "emitida", "Note": "", "Created": "2026-10-20 10:00:00",
      "LinesJSON": "[]", "CollectionsJSON": "[]"}
I.is_configured = lambda: True
I.get_factura = lambda fid: dict(_F)
I.list_facturas = lambda g=None, cliente_id=None: [dict(_F)]
C.get_cliente = lambda cid: {"ID": cid, "Name": "C1"}
contable.identidad = lambda g: dict(st.session_state.get("_ID", {"abn": "1", "legal": "X", "plazo": 14}))
xero_ui.boton_factura = lambda g, f: None
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G", "nombre": "Jefa"})
st.session_state.setdefault("_fac_open", "FAC-6")
from core import invoices_ui as IU
flash.mostrar()
IU.render_facturas("G")
'''
at = AppTest.from_string(GUION, default_timeout=90)
at.run()
_cap = " ".join(c.value for c in at.caption)
_md = " ".join(m.value for m in at.markdown)
chk("el detalle de una factura se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("…junto al PDF, sin datos de pago: «doesn't say how to pay»", "doesn't say how to pay" in _cap, _cap[:500])
chk("…y el estado de la cabecera con mayúscula: «Overdue»", "Overdue" in _md, _md[:400])
at = AppTest.from_string(GUION, default_timeout=90)
at.session_state["_ID"] = dict(_ID_LLENA)
at.run()
chk("…con los datos de pago puestos, no avisa", "how to pay" not in " ".join(c.value for c in at.caption))
at = AppTest.from_string(GUION, default_timeout=90)
at.session_state["_COB"] = "250"
at.run()
chk("…y en una cobrada tampoco (no queda nada que pagar)", "how to pay" not in " ".join(c.value for c in at.caption))

# ═════════════════════════════════════════════════════════════════════════════
sec("6. «Tax identity and payment terms» (H24)")
FISC = r'''
import streamlit as st
from core import auth, auth_ui, flash
st.session_state.setdefault("_LL", [])
_G = {"Group": "G", "Description": "", "Active": "SI", "ABN": "1", "LegalName": "L", "PaymentTermsDays": "",
      "Address": "", "ContactEmail": "", "ContactPhone": "", "BankAccountName": "", "BankBSB": "", "BankAccountNumber": ""}
auth.list_groups = lambda *a, **k: [dict(_G)]
auth.grupos_con_libro_propio = lambda *a, **k: []
auth.group_sheet_id = lambda g: ""
auth.set_group_setting = lambda g, c, v: (st.session_state["_LL"].append((g, c, v)), (True, "ok"))[1]
flash.mostrar()
auth_ui._owner_grupos()
'''
at = AppTest.from_string(FISC, default_timeout=90)
at.run()
chk("la pantalla de grupos se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
at.selectbox(key="fisc_g_sel").set_value("G").run()
_keys = {x.key for x in at.text_input}
chk("tiene los campos de contacto y de banco", {"fisc_dir", "fisc_mail", "fisc_tel", "fisc_titular", "fisc_bsb",
                                                 "fisc_cuenta"} <= _keys, _keys)
chk("…y sin banco, lo avisa", any("No bank details yet" in w.value for w in at.warning), [w.value for w in at.warning])
at.text_input(key="fisc_bsb").set_value("06200").run()
at.text_input(key="fisc_cuenta").set_value("12345678").run()
at.button(key="fisc_save").click().run()
chk("un BSB de 5 cifras se rechaza y NO escribe nada", any("6 digits" in e.value for e in at.error)
    and not list(at.session_state["_LL"]), ([e.value for e in at.error], list(at.session_state["_LL"])))
at.text_input(key="fisc_bsb").set_value("062 000").run()
at.text_input(key="fisc_cuenta").set_value("").run()
at.button(key="fisc_save").click().run()
chk("BSB sin cuenta se rechaza (los dos o ninguno)", any("both the BSB and the account number" in e.value for e in at.error)
    and not list(at.session_state["_LL"]), [e.value for e in at.error])
at.text_input(key="fisc_cuenta").set_value("1234 5678").run()
at.text_input(key="fisc_mail").set_value("cuentas sin arroba").run()
at.button(key="fisc_save").click().run()
chk("un email que no lo es se rechaza", any("is not an email address" in e.value for e in at.error)
    and not list(at.session_state["_LL"]), [e.value for e in at.error])
at.text_input(key="fisc_mail").set_value("accounts@harbour.test").run()
at.button(key="fisc_save").click().run()
_ll = list(at.session_state["_LL"])
chk("con todo bien, escribe SOLO lo que cambió, normalizado (BSB «062-000», cuenta sin espacios)",
    sorted(_ll) == sorted([("G", "BankBSB", "062-000"), ("G", "BankAccountNumber", "12345678"),
                           ("G", "ContactEmail", "accounts@harbour.test")]), _ll)
chk("…sin reescribir el plazo vacío que se ve como 14 (H30)", not [x for x in _ll if x[1] == "PaymentTermsDays"], _ll)
_n, _og = funcion("core/auth_ui.py", "_owner_grupos")
chk("el aviso de lo guardado nombra los campos («Tax identity updated: BSB, …»)",
    't("Tax identity updated: {c}.", c=", ".join(_etq_fisc(c) for c in _cambian))' in _og)

# ═════════════════════════════════════════════════════════════════════════════
sec("7. Las certificaciones en pantalla (H14, H5)")
CLM = r'''
import streamlit as st
from core import claims_ui as CU, claims as CL, invoices as I, flash
st.session_state.setdefault("auth", {"usuario": "adm", "rol": "administrator", "grupo": "G", "nombre": "Adm"})
CL.is_configured = lambda: True
def _calc(pid, grupo, pct=None, prj=None):
    return {"contrato": 57055.0, "cotizacion": "COT-12", "variaciones": 0.0, "valor": 57055.0, "pct": 0.0,
            "hecho": 0.0, "antes": 0.0, "bruto": 0.0, "retencion_pct": 5.0, "retencion": 0.0, "neto": 0.0,
            "hay_contrato": True, "retenido_acumulado": 0.0, "retenido_liberado": 0.0, "retenido_pendiente": 0.0}
CL.calcular = _calc
CL.variaciones = lambda pid, estado=None: [{"ID": "VAR-1", "Number": "1", "Amount": "500", "Description": "Extra",
                                            "Status": "approved"}]
_C = [{"ID": "CLM-1", "Number": "1", "Date": "2026-11-10", "PctComplete": "10.0", "ThisClaim": "5955.5",
       "Retention": "297.77", "Status": st.session_state.get("_EST1", "issued"), "Type": ""}]
CL.reclamaciones = lambda pid, incluir_anuladas=False: [dict(c) for c in _C if incluir_anuladas or c["Status"] != "cancelled"]
CL.puede_liberar = lambda pid, prj=None: (False, "no")
I.is_configured = lambda: False
CU._descarga = lambda *a, **k: None
flash.mostrar()
CU.render("PRJ-43", "G", {"ID": "PRJ-43", "Status": "In progress", "Progress": "0"}, editable=True, key_prefix="clm")
'''
at = AppTest.from_string(CLM, default_timeout=90)
at.run()
_md = " ".join(m.value for m in at.markdown)
chk("las certificaciones se pintan sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("H14 · la lista: «#1 10/11/2026 · 10%» (era «2026-11-10 · 10.0%»)", "**#1** 10/11/2026 · 10% ·" in _md, _md[:700])
chk("H5 · la variación aprobada dice «Approved»", "Approved" in _md and ":gray[approved]" not in _md, _md[:900])
at = AppTest.from_string(CLM, default_timeout=90)
at.session_state["_EST1"] = "cancelled"
at.run()
_md = " ".join(m.value for m in at.markdown)
chk("una anulada: tachada y «Cancelled»", "~~**#1**" in _md and "· Cancelled" in _md, _md[:600])

# ═════════════════════════════════════════════════════════════════════════════
sec("8. Accounting: desde cuándo y quién (H16)")
XER = r'''
import streamlit as st
from core import xero_ui as XU, xero as X, auth, contable
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G", "nombre": "Jefa"})
X.configuracion = lambda: {"ok": True, "faltan": [], "problemas": [], "redirect": ""}
X.estado = lambda g: {"conectada": True, "estado": "ok", "tenant": "Demo Company (AU)",
                      "desde": "2026-09-15 17:56:50", "por": "admin2"}
auth.get_user = lambda u: {"User": u, "Name": "Bobo"} if u == "admin2" else {}
class _Alto(Exception):
    pass
def _alto(g):
    raise _Alto("fin de la prueba")
contable.mapa = _alto
XU.render_conexion("G")
'''
at = AppTest.from_string(XER, default_timeout=60)
at.run()
_md = " ".join(m.value for m in at.markdown)
chk("«Connected to Demo Company (AU) since 15/09/2026 17:56 by Bobo» (era «2026-09-15 17:56:50 · by Admin2»)",
    "since 15/09/2026 17:56 by Bobo" in _md and "2026-09-15" not in _md, _md[:500])

# ═════════════════════════════════════════════════════════════════════════════
sec("9. La actividad parada (H28)")
_tp = src("core/projects_ui.py")
# ⚠️ en las CADENAS del código, no en el texto: «it was due on» sigue en el comentario que explica el cambio (trampa 2)
_cads = [n.value for n in ast.walk(ast.parse(_tp)) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
chk("dice «should have started on … · N-day activity», dentro de t()",
    't(":red[:material/cancel:] **{n}** — not started, should have started on {f} · {d}-day activity",' in _tp
    and not [c for c in _cads if "it was due on" in c], [c for c in _cads if "it was due on" in c])

# ═════════════════════════════════════════════════════════════════════════════
sec("10. El rastro sin no-cambios (H30)")


class _WS:
    def __init__(self):
        self.filas = []

    def append_row(self, fila, value_input_option=None):
        self.filas.append(fila)


_ws = _WS()
from core import clock as _CK                                              # noqa: E402
from datetime import datetime as _DT  # noqa: E402
_d = [_sustituir(AUD, _ws=lambda: _ws, _invalidate=lambda: None), _sustituir(_CK, now=lambda *a, **k: _DT(2026, 11, 10, 9, 0))]
try:
    _r1 = AUD.registrar("cotizacion", "COT-6", {"Status": ["accepted", "accepted"]}, grupo="G")
    _r2 = AUD.registrar("proyecto", "PRJ-1", {"WeightInGrouping": ["1", 1.0], "Status": ["In progress", "Cancelled"]},
                        grupo="G")
    _r3 = AUD.registrar("cotizacion", "COT-6", {"Status": ["accepted", "accepted"], "ProjectID": ["", "PRJ-9"]}, grupo="G")
finally:
    for x in _d:
        x()
chk("«accepted → accepted» no se apunta (no escribe nada)", _r1 is False and len(_ws.filas) == 2, (_r1, _ws.filas))
_c2 = json.loads(_ws.filas[0][7]) if _ws.filas else {}
_c3 = json.loads(_ws.filas[1][7]) if len(_ws.filas) > 1 else {}
chk("«1 → 1.0» tampoco; lo que sí cambió, sí", _r2 and _c2 == {"Status": ["In progress", "Cancelled"]}, _c2)
chk("…y en uno mixto, solo el campo que cambió", _r3 and _c3 == {"ProjectID": ["", "PRJ-9"]}, _c3)
chk("el peso sin grupo se queda como está (no se reescribe 0 → 1.0)",
    '"WeightInGrouping": peso if ag_id else prj.get("WeightInGrouping", ""),' in _tp)

# ═════════════════════════════════════════════════════════════════════════════
sec("11. El buscador (H26)")
from core import home_ui as HU                                             # noqa: E402
from core import projects as P                                             # noqa: E402
from core import roster as R                                               # noqa: E402
from core import library as LIB                                            # noqa: E402
from core import inventory as INV                                          # noqa: E402
from core import invoices as I                                             # noqa: E402
from core import clock                                                     # noqa: E402
import streamlit as st                                                     # noqa: E402

_FACS = [{"ID": "FAC-4", "Number": "0004", "ClientName": "C1", "Date": "2026-10-20", "Total": "250",
          "Collected": "0", "ExpiryDate": "2026-10-27", "Status": "emitida"},
         {"ID": "FAC-14", "Number": "0014", "ClientName": "C9", "Date": "2026-10-21", "Total": "1000",
          "Collected": "1000", "ExpiryDate": "2026-11-27", "Status": "emitida"},
         {"ID": "FAC-24", "Number": "0024", "ClientName": "C3", "Date": "2026-11-01", "Total": "1000",
          "Collected": "400", "ExpiryDate": "2026-12-01", "Status": "emitida"}]
_COTS = [{"ID": "COT-6", "Number": "0006", "ClientName": "C1", "Status": "aceptada", "Version": "1"},
         {"ID": "COT-4", "Number": "0004", "ClientName": "C2", "Status": "enviada", "Version": "1"}]
_d = [_sustituir(HU, _rol=lambda: "administrator"),
      _sustituir(P, list_projects=lambda *a, **k: [{"ID": "PRJ-0040", "Name": "Lift 4", "Client": "C1"}]),
      _sustituir(A, list_users=lambda *a, **k: []), _sustituir(R, list_trabajos=lambda *a, **k: []),
      _sustituir(LIB, list_items=lambda *a, **k: []), _sustituir(INV, list_activos=lambda *a, **k: []),
      _sustituir(I, list_facturas=lambda *a, **k: [dict(x) for x in _FACS]),
      _sustituir(Q, list_cotizaciones=lambda *a, **k: [dict(x) for x in _COTS]),
      _sustituir(clock, today=lambda *a, **k: date(2026, 11, 10))]
try:
    _res = {q: HU.buscar(q, "G") for q in ("Invoice 0004", "invoice no. 4", "#4", "4", "0004", "Quote 4", "quote 6",
                                           "Invoice 4", "inv 14", "14", "invoice 24")}
finally:
    for x in _d:
        x()


def _primero(q):
    r = _res.get(q) or []
    return (r[0]["tipo"], r[0]["id"], r[0]["orden"]) if r else None


chk("«Invoice 0004» encuentra la 0004 PRIMERO (era «0 result(s)»)", _primero("Invoice 0004") == ("factura", "FAC-4", 0),
    _res.get("Invoice 0004"))
chk("«invoice no. 4» y «Invoice 4» también", _primero("invoice no. 4") == ("factura", "FAC-4", 0)
    and _primero("Invoice 4") == ("factura", "FAC-4", 0))
chk("…y «Invoice 4» NO trae la cotización 0004 (dijo factura)",
    not [x for x in _res.get("Invoice 4", []) if x["tipo"] == "cotizacion"], _res.get("Invoice 4"))
chk("«#4», «4» y «0004» traen la factura Y la cotización nº 4",
    all({("factura", "FAC-4"), ("cotizacion", "COT-4")} <= {(x["tipo"], x["id"]) for x in _res.get(q, [])}
        for q in ("#4", "4", "0004")), {q: [(x["tipo"], x["id"]) for x in _res.get(q, [])] for q in ("#4", "4", "0004")})
chk("…«4» (un carácter) SOLO trae documentos: no la obra PRJ-0040", not [x for x in _res.get("4", [])
                                                                       if x["tipo"] == "proyecto"], _res.get("4"))
chk("…y no confunde la 0014 con la 0004", not [x for x in _res.get("Invoice 0004", []) if x["id"] == "FAC-14"])
chk("«quote 6» → la cotización 0006; «Quote 4» → la 0004 y no la factura",
    _primero("quote 6") == ("cotizacion", "COT-6", 0) and _primero("Quote 4") == ("cotizacion", "COT-4", 0)
    and not [x for x in _res.get("Quote 4", []) if x["tipo"] == "factura"], (_res.get("quote 6"), _res.get("Quote 4")))
chk("«inv 14» → la 0014, y «14» la encuentra (además de lo que contenga «14»)",
    _primero("inv 14") == ("factura", "FAC-14", 0) and ("factura", "FAC-14") in {(x["tipo"], x["id"]) for x in _res["14"]})
_pie = (_res.get("Invoice 0004") or [{}])[0].get("pie", "")
chk("el resultado de la factura dice «Overdue · $250.00» (lo pendiente)", "Overdue" in _pie and "250.00" in _pie, _pie)
_pie14 = [x for x in _res.get("14", []) if x["id"] == "FAC-14"]
chk("…y una cobrada, «Collected» con su total", _pie14 and "Collected" in _pie14[0]["pie"]
    and "1,000.00" in _pie14[0]["pie"], _pie14)
_p24 = (_res.get("invoice 24") or [{}])[0]
chk("…y una a medio cobrar, «Partial» con lo que FALTA ($600.00 de $1,000.00)", _p24.get("id") == "FAC-24"
    and "Partial" in _p24.get("pie", "") and "600.00" in _p24.get("pie", "") and "1,000" not in _p24.get("pie", ""), _p24)
_pc = [x for x in _res.get("quote 6", []) if x["id"] == "COT-6"]
chk("la cotización sigue con su estado con mayúscula («Accepted»)", _pc and "Accepted" in _pc[0]["pie"], _pc)
chk("_num_documento: lo que NO es un número de documento no lo es",
    HU._num_documento("lift 4") is None and HU._num_documento("prj-0040") is None and HU._num_documento("") is None
    and HU._num_documento("no. 12") == (None, 12))

# ═════════════════════════════════════════════════════════════════════════════
sec("12. Lo visto verificando v671")
from core import payroll as PR                                             # noqa: E402
GEN = r'''
import datetime as dt
import streamlit as st
from core import payroll_ui as PUI, payroll as PR, timeclock as T, auth, clock, flash
from core import ausencias as AU
clock.today = lambda *a, **k: dt.date(2026, 11, 10)
st.session_state.setdefault("auth", {"usuario": "admin2", "rol": "administrator", "grupo": "G", "nombre": "Bobo"})
PR.is_configured = lambda: True
PR.list_nominas = lambda g=None, **k: []
PR.horas_sin_pagar = lambda g: []
T.horas_por_usuario_rango = lambda g, d, h, **k: {"campo000": {"nombre": "hjg,ujgjg", "horas": 180.65},
                                                  "admin2": {"nombre": "Bobo", "horas": 8.0}}
T.jornadas_abiertas = lambda g, d, h: {}
T.jornadas_largas = lambda g, **k: [{"usuario": "campo000", "cuenta": "campo000", "nombre": "hjg,ujgjg", "horas": 50.08,
    "entrada": "2026-10-30 06:31:00", "salida": "2026-11-01 08:36:00"}]
auth.rate_map = lambda g: {"campo000": 55.0, "admin2": 45.0}
auth.group_num_setting = lambda g, k, d: d
AU.excesos_por_decidir = lambda *a, **k: []
st.session_state.setdefault("_nom_gen", True)
flash.mostrar()
PUI.render_nominas("G")
'''
at = AppTest.from_string(GEN, default_timeout=90)
at.run()
chk("«Generate payroll» se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_df = at.dataframe[0].value if at.dataframe else None
_fila = {} if _df is None else {r["Usuario"]: r for r in _df.to_dict("records")}
_c = _fila.get("hjg,ujgjg", {})
chk("la vista previa NO da base a quien deja fuera la jornada de más de 16 h (era 180.65 h × 55 = 9,935.75)",
    _c and (_c.get("Base") is None or str(_c.get("Base")) == "nan") and "Left out" in str(_c.get("Nota", "")), _fila)
chk("…y a los demás sí («Bobo» 8 h × 45 = 360)", _fila.get("Bobo", {}).get("Base") == 360.0, _fila.get("Bobo"))
DET = r'''
import json
import streamlit as st
from core import payroll_ui as PUI, payroll as PR, auth, contable, flash
st.session_state.setdefault("auth", {"usuario": "admin2", "rol": "administrator", "grupo": "G", "nombre": "Bobo"})
_N = {"ID": "NOM-0003", "Group": "G", "User": "admin2", "Name": "Bobo", "PeriodFrom": "2026-11-03",
      "PeriodTo": "2026-11-09", "Hours": "0.13", "HourlyRate": "45", "Base": "5.85", "ConceptsJSON": "[]",
      "Net": "5.85", "Status": "emitida"}
PR.is_configured = lambda: True
PR.get_nomina = lambda nid: dict(_N)
PR.list_nominas = lambda g=None, **k: [dict(_N)]
contable.identidad = lambda g: {"abn": "1", "legal": "X", "plazo": 14}
auth.get_user = lambda u: {"User": u, "Name": "Bobo", "Role": st.session_state.get("_ROL", "administrator"),
                           "SuperFund": ""}
st.session_state.setdefault("_nom_open", "NOM-0003")
flash.mostrar()
PUI.render_nominas("G")
'''
at = AppTest.from_string(DET, default_timeout=90)
at.run()
_cap = " ".join(c.value for c in at.caption)
chk("la colilla de un ADMINISTRADOR manda al propietario (Administration → Users), no a Planning → Users",
    "Administration → Users" in _cap and "Planning → Users" not in _cap, _cap[:400])
at = AppTest.from_string(DET, default_timeout=90)
at.session_state["_ROL"] = "field"
at.run()
_cap = " ".join(c.value for c in at.caption)
chk("…y la de alguien de campo, a Planning → Users", "Planning → Users" in _cap, _cap[:400])
_n, _fu = funcion("core/auth_ui.py", "_ficha_usuario")
chk("guardar el fondo de super o el nº de nómina dice lo que quedó (no «Saved.»)",
    't("Super fund saved: {f}.", f=_lit(_sf.strip()))' in _fu and 't("Payroll ID saved: {p}.", p=_lit(_pid.strip()))' in _fu
    and 't("Super fund removed.")' in _fu)

print("\n" + ("TODO OK" if not FALLOS else f"{len(FALLOS)} FALLO(S): {FALLOS}"))
sys.exit(1 if FALLOS else 0)
