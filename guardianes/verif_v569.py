# -*- coding: utf-8 -*-
"""v569 · FINANCE → INVOICES, PROBADA ACCIÓN POR ACCIÓN (decisión del usuario: «Dale con todo»).

  1. ⚠️ Anular: PREGUNTA, acción diferida y AVISA (un clic anulaba sin nada).
  2. ⚠️ Una anulada no debe nada: «nothing to collect» en pantalla; en el PDF, «VOID» y $0.
  3. El detalle dice cuándo se emitió, cuándo vence y cuántos días lleva vencida.
  4. Fechas DD/MM/YYYY (lista, cobros, PDF y selectores).   5. Un mismo nombre de estado
     (el de `etiqueta`) y punto de color en la tabla; «Due».   6. Textos con `t()`;
     «Invoice_….pdf».   7. Cifras ACTIVAS + filtro recordado.   8. Un toque abre la
     factura.   9. El cliente lleva a su ficha.   10. Nº fijado, lo importante delante.
 11. Sin obras, ni radio de una opción: se dice.

AppTest con las fuentes sustituidas: ninguna hoja se toca.
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


from streamlit.testing.v1 import AppTest                                    # noqa: E402

CAB = r'''
import datetime as dt
import json
import streamlit as st
from core import invoices_ui as IU, invoices as I, clientes as C, clock, xero_ui, contable
from core import projects as P
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G",
                                     "nombre": "Jefa"})
clock.today = lambda *a, **k: dt.date(2026, 10, 13)
st.session_state.setdefault("_LL", [])
def _f(fid, num, tot, cob, fecha, venc, status="emitida", cobros=None):
    return {"ID": fid, "Group": "G", "ClientID": "CLI-1", "ClientName": "Cliente Uno", "Number": num,
            "Date": fecha, "ExpiryDate": venc, "Total": str(tot), "Subtotal": str(round(tot / 1.1, 2)),
            "TaxPct": "10", "Tax": str(round(tot - tot / 1.1, 2)), "Collected": str(cob),
            "Status": status, "Note": "nota", "Created": fecha + " 10:00:00",
            "LinesJSON": json.dumps([{"concepto": "Linea", "importe": round(tot / 1.1, 2)}]),
            "CollectionsJSON": json.dumps(cobros or [])}
_FAC = [_f("FAC-1", "0001", 110, 0, "2026-10-13", "2026-10-27"),
        _f("FAC-2", "0002", 44, 0, "2026-09-19", "2026-10-03"),
        _f("FAC-3", "0003", 55, 55, "2026-09-01", "2026-09-15"),
        _f("FAC-4", "0004", 22, 0, "2026-09-02", "2026-09-16", status="anulada"),
        _f("FAC-5", "0005", 110, 20, "2026-10-01", "2026-10-30",
           cobros=[{"fecha": "2026-10-05", "monto": 20}])]
I.is_configured = lambda: True
I.list_facturas = lambda g=None, **k: [dict(x) for x in _FAC]
I.get_factura = lambda fid: next((dict(x) for x in _FAC if x["ID"] == fid), None)
def _anular(fid):
    st.session_state["_LL"].append(("anular", fid))
    return True, "Invoice voided."
I.anular = _anular
I.registrar_cobro = lambda *a, **k: (True, "Payment recorded.")
C.get_cliente = lambda cid: {"ID": cid, "Name": "Cliente Uno"}
C.list_clientes = lambda g=None, **k: [{"ID": "CLI-1", "Name": "Cliente Uno"}]
contable.identidad = lambda g: {}
xero_ui.boton_factura = lambda *a, **k: None
P.list_projects = lambda *a, **k: (
    [{"ID": "PRJ-9", "Name": "Archivada", "Group": "G", "ClientID": "CLI-1", "Status": "Archived"}]
    if k.get("incluir_archivados") and st.session_state.get("_CON_OBRAS") else [])
C.es_del_cliente = lambda p, cid, cn: True
I.pendiente_de_facturar = lambda *a, **k: 0.0
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    for _k, _v in (st.session_state.get("_PRE") or {}).items():
        st.session_state[_k] = _v
# ⚠️ v570 · los avisos se pintan ANTES de la sección, como la shell
# (`home_ui.render_admin_content`). Este guion los pintaba DESPUÉS, y así un aviso
# encolado sin `st.rerun()` salía aquí y en producción no (un clic tarde).
from core import flash
flash.mostrar()
IU.render_facturas("G")
'''


def _app(pre=None, **ss):
    a = AppTest.from_string(CAB, default_timeout=90)
    for k, v in ss.items():
        a.session_state[k] = v
    if pre:
        a.session_state["_PRE"] = pre
    a.run()
    return a


# ══════════════════════════════════════════════════════════════════════════════
print("1. La lista: cifras activas, filtro, tabla")
at = _app()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_kb = {b.key: b.label for b in at.button}
chk("⚠️ 4 cifras-BOTÓN", [k for k in _kb if str(k).startswith("cpxkpi_fac_")] ==
    ["cpxkpi_fac_fac", "cpxkpi_fac_cob", "cpxkpi_fac_pen", "cpxkpi_fac_ven"])
chk("…con sus importes (sin la anulada): Invoiced $319, Overdue $44",
    "\n\n\\$319\n\n" in _kb.get("cpxkpi_fac_fac", "") and "\n\n\\$44\n\n" in _kb.get("cpxkpi_fac_ven", ""),
    (_kb.get("cpxkpi_fac_fac"), _kb.get("cpxkpi_fac_ven")))
_df = at.dataframe[0]
_v = _df.value
chk("⚠️ lo importante delante: Nº, cliente, estado, saldo, vence",
    list(_v.columns)[:5] == ["Nº", "Cliente", "Estado", "Outstanding", "Vence"], list(_v.columns))
chk("⚠️ fechas DD/MM/YYYY (salían «2026-09-19»)",
    "03/10/2026" in list(_v["Vence"]) and "19/09/2026" in list(_v["Fecha"]), list(_v["Vence"]))
chk("⚠️ el estado con punto y la palabra COMPARTIDA («🔴 overdue», «⚪ pending», «🟢 collected»)",
    {"🔴 overdue", "⚪ pending", "🟢 collected", "⚫ voided", "🟠 partial"} == set(_v["Estado"]), set(_v["Estado"]))
_cfg = _df.proto.columns.replace(" ", "")
# ⚠️ Por JSON, no por texto: el JSON escapa «Nº» como º y la 1ª versión de la
# sonda buscaba el carácter literal (rojo con la tabla bien).
import json as _json                                                         # noqa: E402
_cj = _json.loads(_df.proto.columns)
chk("el Nº FIJADO, «Due» y dinero con céntimos",
    _cj.get("Nº", {}).get("pinned") is True and _cj.get("Vence", {}).get("label") == "Due"
    and "$%,.2f" in _cfg, {k: _cj.get(k) for k in ("Nº", "Vence", "Total")})
[b for b in at.button if b.key == "cpxkpi_fac_ven"][0].click()
at.run()
chk("⚠️ «Overdue» filtra la lista (solo la vencida)",
    at.session_state["cpxseg_fac_filt"] == "Vencidas" and list(at.dataframe[0].value["Nº"]) == ["0002"],
    list(at.dataframe[0].value["Nº"]))
[b for b in at.button if b.key == "cpxkpi_fac_pen"][0].click()
at.run()
chk("«Outstanding» = pendientes + parciales + vencidas",
    sorted(at.dataframe[0].value["Nº"]) == ["0001", "0002", "0005"], list(at.dataframe[0].value["Nº"]))
_src = io.open(os.path.join(RAIZ, "core", "invoices_ui.py"), encoding="utf-8").read()
_arb = ast.parse(_src)


def _fn(n):
    return next(x for x in ast.walk(_arb) if isinstance(x, ast.FunctionDef) and x.name == n)


# v570 · el selector se mudó a `filtrar` (el mismo para Invoices y la ficha del cliente)
_rad = [n for n in ast.walk(_fn("filtrar")) if isinstance(n, ast.Call) and ast.unparse(n.func) == "st.radio"]
chk("⚠️ el filtro se RECUERDA (`persist_state`)",
    _rad and any(k.arg == "persist_state" and ast.unparse(k.value) == "'session'" for k in _rad[0].keywords))
at = _app(pre={"fac_tbl_0": {"selection": {"rows": [], "columns": [], "cells": [(1, "Cliente")]}}})
chk("⚠️ un toque en una CELDA abre esa factura (la 2ª de la lista: 0005)",
    at.session_state["_fac_open"] == "FAC-5" and at.session_state["_fac_tbl_gen"] == 1
    if "_fac_open" in at.session_state else False)

print("\n2-3, 9. El detalle")
at = _app(_fac_open="FAC-2")
chk("el detalle se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_tx = " ¦ ".join([m.value for m in at.markdown] + [c.value for c in at.caption])
chk("«Invoice No. 0002» (por `t()`)", "Invoice No. 0002" in _tx)
chk("⚠️ cuándo se emitió, cuándo vence y cuántos días lleva vencida",
    "Issued 19/09/2026 · due 03/10/2026 · :red[10 days overdue]" in _tx, re.findall(r"Issued[^¦]*", _tx))
_cb = [b for b in at.button if b.key == "fac_cli_FAC-2"]
chk("el cliente es un botón", len(_cb) == 1)
_cb[0].click()
at.run()
chk("⚠️ …que abre su ficha en Contacts", at.session_state["_cli_open"] == "cliente uno"
    and at.session_state["_admin_nav_pending"] == ("contactos", None), at.session_state["_cli_open"])
at = _app(_fac_open="FAC-4")
chk("⚠️ ANULADA: «nothing to collect» y sin «Outstanding»",
    any("Voided: there is nothing to collect." in i.value for i in at.info) and not at.metric)
chk("…ni formulario de cobro ni «Void»", not [b for b in at.button if str(b.key).startswith("fac_anul_")])
at = _app(_fac_open="FAC-5")
_tx = " ¦ ".join(m.value for m in at.markdown)
chk("⚠️ los cobros con DD/MM/YYYY y el importe escapado", "- 05/10/2026: **\\$20.00**" in _tx,
    re.findall(r"- \d[^¦]*", _tx))
chk("la ayuda «Collected $20.00 of $110.00» (por `t()`)",
    at.metric and at.metric[0].proto.help == "Collected \\$20.00 of \\$110.00",
    at.metric[0].proto.help if at.metric else None)

print("\n1. ⚠️ Anular: pregunta, diferida y avisa")
at = _app(_fac_open="FAC-1")
[b for b in at.button if b.key == "fac_anul_FAC-1"][0].click()
at.run()
chk("⚠️ el primer clic PREGUNTA (no anula)",
    not [x for x in at.session_state["_LL"] if x[0] == "anular"]
    and any("Void invoice No. 0001?" in w.value for w in at.warning))
[b for b in at.button if b.key == "fac_anul_no_FAC-1"][0].click()
at.run()
chk("«Keep it» la deja como estaba", not [x for x in at.session_state["_LL"] if x[0] == "anular"]
    and not any("Void invoice No." in w.value for w in at.warning))
[b for b in at.button if b.key == "fac_anul_FAC-1"][0].click()
at.run()
[b for b in at.button if b.key == "fac_anul_si_FAC-1"][0].click()
at.run()
chk("⚠️ «Yes, void it» anula (UNA vez)", [x for x in at.session_state["_LL"] if x[0] == "anular"] ==
    [("anular", "FAC-1")], at.session_state["_LL"])
chk("⚠️ …y AVISA («Invoice voided.»)", any("Invoice voided." in s.value for s in at.success),
    [s.value for s in at.success])

print("\n11. La factura nueva")
at = _app(_fac_nueva=True)
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("⚠️ sin obras: ni radio de una sola opción, y se dice",
    not [r for r in at.radio if r.key == "fac_scope"]
    and any("This client has no jobs" in c.value for c in at.caption))
at = _app(_fac_nueva=True, _CON_OBRAS=True)
_chk = [c for c in at.checkbox if c.key == "fac_ver_arch"]
chk("la casilla de archivadas por `t()` («Include archived sites (1)»)",
    _chk and "Include archived sites (1)" in _chk[0].label, [c.label for c in at.checkbox])
_chk[0].check()
at.run()
_rd = [r for r in at.radio if r.key == "fac_scope"]
chk("con obras, el radio: «The whole client» (ID interno, solo se traduce al pintarlo)",
    _rd and _rd[0].value == "__todo__" and "The whole client" in list(_rd[0].options), _rd[0].options if _rd else None)
_di = [n for n in ast.walk(_arb) if isinstance(n, ast.Call) and ast.unparse(n.func).endswith("date_input")]
chk("⚠️ los TRES selectores de fecha en DD/MM/YYYY",
    len(_di) == 3 and all(any(k.arg == "format" and ast.unparse(k.value) == "'DD/MM/YYYY'" for k in n.keywords)
                          for n in _di), [ast.unparse(n)[:60] for n in _di])

print("\n2, 4, 6. El PDF y los textos")
from core import invoice_pdf, contable as _CT                               # noqa: E402
_ct0 = _CT.identidad
_CT.identidad = lambda g: {}
try:
    from pypdf import PdfReader
    _anul = {"ID": "F", "Group": "G", "Number": "0004", "Date": "2026-09-02", "ExpiryDate": "2026-09-16",
             "Total": "22", "Subtotal": "20", "Tax": "2", "TaxPct": "10", "Collected": "0",
             "Status": "anulada", "LinesJSON": "[]", "ClientName": "C"}
    _txt = "\n".join(p.extract_text() for p in PdfReader(io.BytesIO(
        invoice_pdf.generate_invoice_pdf(_anul, {}, "G"))).pages)
    chk("⚠️ el PDF de una anulada: «VOID» y «Balance due $0.00»",
        "VOID" in _txt and re.search(r"Balance due\s*\$0\.00", _txt) is not None, _txt[:400])
    chk("⚠️ fechas DD/MM/YYYY en el PDF (iban en ISO)", "02/09/2026" in _txt and "16/09/2026" in _txt
        and "2026-09-02" not in _txt, _txt[:300])
finally:
    _CT.identidad = _ct0
# ⚠️ Por las cadenas del AST: «Factura_» está en MI comentario (trampa 2: grep ≠ uso)
_ctes = [v.value for n in ast.walk(_arb) for v in ([n] if isinstance(n, ast.Constant) else
         (n.values if isinstance(n, ast.JoinedStr) else [])) if isinstance(v, ast.Constant)
         and isinstance(v.value, str)]
chk("el archivo se llama «Invoice_…» (no «Factura_»)",
    any(c == "Invoice_" for c in _ctes) and not any("Factura_" in c for c in _ctes))
from core import invoices_ui as _IU                                          # noqa: E402
chk("⚠️ el detalle usa las palabras de `etiqueta` (pending/collected, no outstanding/paid)",
    _IU._EST_FMT["pendiente"][1] == "pending" and _IU._EST_FMT["cobrada"][1] == "collected")
_lit = []
# v570 · y las tres funciones comunes de la lista
for fn in ("render_facturas", "_detalle_factura", "_nueva_factura", "cifras_cobro", "filtrar",
           "tabla_facturas"):
    for n in ast.walk(_fn(fn)):
        if (isinstance(n, ast.Call) and not ast.unparse(n.func).startswith("logger")
                and ast.unparse(n.func).split(".")[-1] in ("caption", "warning", "info", "error",
                                                            "success", "markdown", "button", "checkbox", "metric")):
            for a in n.args[:1]:
                if (isinstance(a, ast.Constant) and isinstance(a.value, str)
                        and re.search(r"[A-Za-z]{4}", re.sub(r":material/\w+:", "", a.value))
                        and not a.value.lstrip().startswith("<")):
                    _lit.append("%s:%d %s" % (fn, n.lineno, ast.unparse(a)[:60]))
                elif isinstance(a, ast.JoinedStr):
                    _t = "".join(v.value for v in a.values if isinstance(v, ast.Constant))
                    if re.search(r"[A-Za-z]{4,}\s+[A-Za-z]{2,}", re.sub(r":material/\w+:", "", _t)):
                        _lit.append("%s:%d %s" % (fn, n.lineno, ast.unparse(a)[:60]))
chk("⚠️ Invoices sin frases sueltas («Invoice No.», Subtotal, «Note:», archivadas…)", not _lit, _lit)

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("TODO OK")
