# -*- coding: utf-8 -*-
"""v574 · FINANCE → PAYROLL, PROBADA ACCIÓN POR ACCIÓN (decisión del usuario: «Dale con todo»).

Visto en producción con dos colillas de PRUEBA (usuario ficticio, borradas):
  1. Las cifras eran HTML → botones que filtran.   2. Las anuladas desaparecían → filtro.
  3. Homónimo FALSO: quien tenía dos colillas salía «Nombre (login)».
  4. Dinero sin céntimos ($320.78 → «$321»).   5. «Periodo» crudo, ISO, el estado fuera de
     la vista, abrir con casilla.   6. Avisos sin `t()`.
  7. ⚠️ Anular: un clic, sin preguntar ni avisar → confirma, diferida, avisa; y una PAGADA
     no se anula (también en el motor).   8. ⚠️ «Mark as paid» sin vuelta atrás → deshacer.
  9. Estado crudo «emitida», fechas ISO.   10. Conceptos: tipo y importe fuera de la vista
     (601 px en 376) y el tipo crudo «deduccion».   11. PDF: «pagada (fecha)» en español,
     ISO, «cliente1» en vez del nombre legal y el ABN, «Colilla_».
 12-15. Generar: fechas, segmentado, la tarifa TRUNCADA por `$%,d`, quien no tiene tarifa
     solo se descubría después, textos sin `t()`.

AppTest con las fuentes sustituidas y los avisos pintados ANTES de la sección, como la
shell (trampa 41): ninguna hoja se toca.
"""
import ast
import io
import json
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
from core import payroll as N, payroll_ui as PU, auth, timeclock, clock, payslip_pdf, flash
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G",
                                     "nombre": "Jefa"})
st.session_state.setdefault("_LL", [])
clock.today = lambda *a, **k: dt.date(2026, 10, 13)
_CS = json.dumps([{"concepto": "Income tax withheld (PAYG)", "tipo": "deduccion", "monto": 32.08},
                  {"concepto": "Superannuation", "tipo": "aporte", "monto": 36.89}])
_N = [{"ID": "N1", "Group": "G", "User": "u1", "Name": "Ana", "PeriodFrom": "2026-09-01",
       "PeriodTo": "2026-09-07", "Hours": "10.5", "HourlyRate": "30.55", "Base": "320.78",
       "ConceptsJSON": _CS, "Net": "288.7", "PaymentDate": "", "Status": "emitida"},
      {"ID": "N2", "Group": "G", "User": "u1", "Name": "Ana", "PeriodFrom": "2026-09-08",
       "PeriodTo": "2026-09-14", "Hours": "4", "HourlyRate": "30.55", "Base": "122.2",
       "ConceptsJSON": "[]", "Net": "122.2", "PaymentDate": "2026-10-13", "Status": "pagada"},
      {"ID": "N3", "Group": "G", "User": "u2", "Name": "Beto", "PeriodFrom": "2026-09-01",
       "PeriodTo": "2026-09-07", "Hours": "5", "HourlyRate": "0", "Base": "0",
       "ConceptsJSON": "[]", "Net": "0", "PaymentDate": "", "Status": "anulada"}]
N.is_configured = lambda: True
def _lista(g=None, usuario=None, incluir_anuladas=False):
    return [dict(x) for x in _N if (incluir_anuladas or x["Status"] != "anulada")
            and (usuario is None or x["User"] == usuario)]
N.list_nominas = _lista
def _res(g):
    v = _lista(g)
    return {"a_pagar": round(sum(float(x["Net"]) for x in v if x["Status"] != "pagada"), 2),
            "pagado": round(sum(float(x["Net"]) for x in v if x["Status"] == "pagada"), 2), "n": len(v)}
N.resumen = _res
N.get_nomina = lambda nid: next((dict(x) for x in _N if x["ID"] == nid), {})
def _ll(nombre, ret):
    def f(*a, **k):
        st.session_state["_LL"].append((nombre,) + a)
        return ret
    return f
N.anular = _ll("anular", (True, "Payslip voided."))
N.deshacer_pago = _ll("deshacer", (True, "Payment undone: the payslip is unpaid again."))
N.marcar_pagada = _ll("pagar", (True, "Payslip marked as paid."))
N.update_conceptos = _ll("conceptos", (True, "Payslip updated."))
payslip_pdf.generate_payslip_pdf = lambda f, g: b"%PDF-1.4"
auth.list_users = lambda *a, **k: [{"User": "u1", "Name": "Ana"}, {"User": "u2", "Name": "Beto"}]
timeclock.jornada_y_proyecto = lambda *a, **k: {}
timeclock.horas_por_usuario_rango = lambda g, d, h: {"u1": {"nombre": "Ana", "horas": 10.5},
                                                     "u3": {"nombre": "Ciro", "horas": 2.0}}
auth.rate_map = lambda g: {"u1": 30.55}
auth.group_num_setting = lambda g, k, d: d
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    for _k, _v in (st.session_state.get("_PRE") or {}).items():
        st.session_state[_k] = _v
flash.mostrar()
if st.session_state.get("_CAMPO"):
    PU.render_mis_colillas("u1", "G")
else:
    PU.render_nominas("G")
'''


def _app(pre=None, **ss):
    a = AppTest.from_string(CAB, default_timeout=90)
    for k, v in ss.items():
        a.session_state[k] = v
    if pre:
        a.session_state["_PRE"] = pre
    a.run()
    return a


def _clic(at, key):
    [b for b in at.button if b.key == key][0].click()
    at.run()


def _llamadas(at, nombre):
    return [x for x in at.session_state["_LL"] if x[0] == nombre]


# ══════════════════════════════════════════════════════════════════════════════
print("1-6. La lista")
at = _app()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_kb = {b.key: b.label for b in at.button if str(b.key).startswith("cpxkpi_nom_")}
chk("⚠️ tres cifras-BOTÓN (eran HTML)", list(_kb) == ["cpxkpi_nom_apag", "cpxkpi_nom_pag", "cpxkpi_nom_tot"],
    list(_kb))
chk("…con CÉNTIMOS y sus pies traducibles: «\\$288.70 · 1 issued and unpaid», «\\$122.20 · 1 paid», «2 · 2 period(s)»",
    _kb.get("cpxkpi_nom_apag", "").split("\n\n")[1:] == ["\\$288.70", "1 issued and unpaid"]
    and _kb.get("cpxkpi_nom_pag", "").split("\n\n")[1:] == ["\\$122.20", "1 paid"]
    and _kb.get("cpxkpi_nom_tot", "").split("\n\n")[1:] == ["2", "2 period(s)"], _kb)
_df = at.dataframe[0]
_v = _df.value
chk("⚠️ las ANULADAS se ven (All): 3 filas", len(_v) == 3, len(_v))
chk("lo importante delante: persona, estado, neto, periodo",
    list(_v.columns) == ["Usuario", "Estado", "Neto", "Periodo", "Horas", "Base", "Rate/h"], list(_v.columns))
chk("⚠️ sin homónimo FALSO: «Ana» con dos colillas sale «Ana» (salía «Ana (u1)»)",
    set(_v["Usuario"]) == {"Ana", "Beto"}, set(_v["Usuario"]))
chk("⚠️ periodo DD/MM/YYYY", "01/09/2026 → 07/09/2026" in list(_v["Periodo"]), list(_v["Periodo"]))
chk("estado con punto y TRADUCIDO", set(_v["Estado"]) == {"🟠 issued", "🟢 paid", "⚫ voided"}, set(_v["Estado"]))
chk("⚠️ el neto con céntimos (288.7, no 289)", 288.7 in list(_v["Neto"]), list(_v["Neto"]))
_cj = json.loads(_df.proto.columns)
_enum = _df.proto.DESCRIPTOR.fields_by_name["selection_mode"].enum_type
chk("⚠️ persona FIJADA, «Period» traducido, dinero `$%,.2f`, un toque",
    _cj.get("Usuario", {}).get("pinned") is True and _cj.get("Periodo", {}).get("label") == "Period"
    and _cj.get("Neto", {}).get("type_config", {}).get("format") == "$%,.2f"
    and _cj.get("Base", {}).get("type_config", {}).get("format") == "$%,.2f"
    and [_enum.values_by_number[x].name for x in _df.proto.selection_mode] == ["SINGLE_CELL"],
    {k: _cj.get(k) for k in ("Usuario", "Periodo", "Neto")})
chk("el pie con céntimos y sin contar las anuladas (\\$442.98 · \\$410.90)",
    any("3 payslip(s) · base pay \\$442.98 · net \\$410.90" in c.value for c in at.caption),
    [c.value for c in at.caption])
_sb = [s for s in at.selectbox if s.key == "nom_per_filt"]
chk("⚠️ el selector de periodo, DD/MM/YYYY y «All periods»",
    _sb and list(_sb[0].options) == ["All periods", "08/09/2026 → 14/09/2026", "01/09/2026 → 07/09/2026"],
    _sb[0].options if _sb else None)
_clic(at, "cpxkpi_nom_apag")
chk("⚠️ «To pay» filtra (solo la emitida)", at.session_state["cpxseg_nom_filt"] == "PorPagar"
    and list(at.dataframe[0].value["Neto"]) == [288.7], list(at.dataframe[0].value["Neto"]))
_clic(at, "cpxkpi_nom_pag")
chk("«Paid» filtra (solo la pagada)", list(at.dataframe[0].value["Neto"]) == [122.2])
at.radio(key="cpxseg_nom_filt").set_value("Anuladas")
at.run()
chk("⚠️ «Voided» enseña la anulada", list(at.dataframe[0].value["Usuario"]) == ["Beto"])
_rd = [r for r in at.radio if r.key == "cpxseg_nom_filt"]
chk("…y el filtro se RECUERDA (`persist_state`)",
    "persist_state" in io.open(os.path.join(RAIZ, "core", "payroll_ui.py"), encoding="utf-8").read()
    and _rd and list(_rd[0].options) == ["All", "To pay", "Paid", "Voided"], _rd[0].options if _rd else None)
at = _app(pre={"nom_tbl_0": {"selection": {"rows": [], "columns": [], "cells": [(0, "Periodo")]}}})
chk("⚠️ un toque en una CELDA abre esa colilla", at.session_state["_nom_open"] == "N2"
    and at.session_state["_nom_tbl_gen"] == 1 if "_nom_open" in at.session_state else False)

# ══════════════════════════════════════════════════════════════════════════════
print("\n7-10. El detalle")
at = _app(_nom_open="N1")
chk("el detalle se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_tx = " ¦ ".join(m.value for m in at.markdown)
chk("⚠️ título y línea por `t()`, DD/MM/YYYY y el estado TRADUCIDO (decía «status: emitida»)",
    "Payslip — Ana" in _tx and "Period **01/09/2026 → 07/09/2026**" in _tx and "issued" in _tx
    and "emitida" not in _tx, re.findall(r"Period[^¦]*", _tx))
_edv = at.dataframe[0]
_ecj = json.loads(_edv.proto.columns)
chk("⚠️ el editor ENSEÑA el tipo legible («Deduction», «Employer contribution»; salía «deduccion»)",
    list(_edv.value["Type"]) == ["Deduction", "Employer contribution"], list(_edv.value["Type"]))
chk("⚠️ …y el concepto no se come el ancho (era `width=\"large\"`: tipo e importe fuera de la vista)",
    "width" not in _ecj.get("Concepto", {}) and _ecj.get("Monto", {}).get("width") == "small",
    {k: _ecj.get(k) for k in ("Concepto", "Monto")})
chk("el formulario de pago con fecha DD/MM/YYYY",
    [d.proto.format for d in at.date_input] == ["DD/MM/YYYY"], [d.proto.format for d in at.date_input])
_clic(at, "nom_save_N1")
_cc = _llamadas(at, "conceptos")
chk("⚠️ los conceptos vuelven al DATO al guardar (el editor enseña «Deduction»/«Employer contribution»)",
    _cc and [c["tipo"] for c in _cc[0][2]] == ["deduccion", "aporte"], _cc)
at = _app(_nom_open="N1")
_clic(at, "nom_anul_N1")
chk("⚠️ el primer clic PREGUNTA (no anula)", not _llamadas(at, "anular")
    and any("Void this payslip?" in w.value for w in at.warning))
_clic(at, "nom_anul_no_N1")
chk("«Keep it» la deja", not _llamadas(at, "anular") and not any("Void this payslip?" in w.value for w in at.warning))
_clic(at, "nom_anul_N1")
_clic(at, "nom_anul_si_N1")
chk("⚠️ «Yes, void it» anula UNA vez", [x[1] for x in _llamadas(at, "anular")] == ["N1"], _llamadas(at, "anular"))
chk("⚠️ …y AVISA en esa misma vista (los avisos, ANTES de la sección: trampa 41)",
    any("Payslip voided." in s.value for s in at.success), [s.value for s in at.success])

at = _app(_nom_open="N2")
chk("PAGADA: «Paid on 13/10/2026.»", any("Paid on 13/10/2026." in s.value for s in at.success),
    [s.value for s in at.success])
chk("⚠️ una pagada NO ofrece anular (ni guardar conceptos)",
    not [b for b in at.button if str(b.key).startswith(("nom_anul_", "nom_save_"))])
_clic(at, "nom_desh_N2")
chk("⚠️ deshacer el pago PREGUNTA", not _llamadas(at, "deshacer")
    and any("Undo the payment of this payslip?" in w.value for w in at.warning))
_clic(at, "nom_desh_si_N2")
chk("⚠️ …«Yes, undo it» lo deshace UNA vez y avisa",
    [x[1] for x in _llamadas(at, "deshacer")] == ["N2"]
    and any("Payment undone" in s.value for s in at.success), (_llamadas(at, "deshacer"), [s.value for s in at.success]))
at = _app(_nom_open="N3")
chk("ANULADA: lo dice, sin pagar ni anular",
    any("Voided: it is not paid" in i.value for i in at.info)
    and not at.date_input and not [b for b in at.button if str(b.key).startswith(("nom_anul_", "nom_desh_"))])

# ══════════════════════════════════════════════════════════════════════════════
print("\n7. El motor: una pagada no se anula; deshacer vuelve a emitida")
import importlib                                                           # noqa: E402
from core import payroll as _N                                             # noqa: E402
# ⚠️ El guion de AppTest corre en ESTE proceso y dejó sus sustituciones puestas en el
# módulo (`N.anular = …`): la 1ª versión probaba el doble, no el motor. Se recarga.
_N = importlib.reload(_N)


class _WS:
    def __init__(self):
        self.esc = []

    def update_cell(self, *a):
        self.esc.append(("cell",) + a)

    def batch_update(self, cambios, **k):
        self.esc.append(("batch", cambios))


_ws = _WS()
_o = {n: getattr(_N, n) for n in ("_ws", "_find_row", "get_nomina", "_invalidate")}
try:
    _N._ws = lambda: (_ws, None)
    _N._find_row = lambda w, nid: 5
    _N._invalidate = lambda: None
    _N.get_nomina = lambda nid: {"ID": nid, "Status": "pagada"}
    ok, msg = _N.anular("NX")
    chk("⚠️ el MOTOR se niega a anular una pagada (y no escribe)", ok is False and not _ws.esc
        and "undo the payment first" in msg, (ok, msg, _ws.esc))
    ok, msg = _N.deshacer_pago("NX")
    _vals = [c["values"][0][0] for c in _ws.esc[0][1]] if _ws.esc else []
    chk("deshacer: Status «emitida» y la fecha de pago vacía", ok and _vals == ["emitida", ""], _vals)
finally:
    for n, f in _o.items():
        setattr(_N, n, f)

# ══════════════════════════════════════════════════════════════════════════════
print("\n12-15. Generar")
at = _app(_nom_gen=True)
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("la frecuencia, SEGMENTADA (`cpxseg_`)", [r.key for r in at.radio] == ["cpxseg_nom_per"])
chk("⚠️ fechas DD/MM/YYYY", [d.proto.format for d in at.date_input] == ["DD/MM/YYYY", "DD/MM/YYYY"])
chk("⚠️ quien NO tiene tarifa se dice ANTES de generar (y el botón a Users)",
    any("No hourly rate: **Ciro**" in w.value for w in at.warning)
    and [b for b in at.button if b.key == "nom_gen_ir_users"], [w.value for w in at.warning])
_g = at.dataframe[0]
_gj = json.loads(_g.proto.columns)
chk("⚠️ la tarifa con CÉNTIMOS (`$%,d` la truncaba: $30.55 → «$30»)",
    list(_g.value["Rate/h"]) == [30.55, 0.0] and _gj.get("Rate/h", {}).get("type_config", {}).get("format") == "$%,.2f",
    (list(_g.value["Rate/h"]), _gj.get("Rate/h")))
chk("…y la nota en su fila", list(_g.value["Nota"]) == ["", "no rate — will be skipped"], list(_g.value["Nota"]))
chk("«2 user(s)» por `t()`", any("**2 user(s)** with workday hours in the period:" in m.value for m in at.markdown))

# ══════════════════════════════════════════════════════════════════════════════
print("\n11. La colilla (PDF) y «My payslips»")
from core import payslip_pdf as _P, contable as _CT                       # noqa: E402
_P = importlib.reload(_P)          # (el guion lo dejó sustituido por un PDF vacío)
_ct0 = _CT.identidad
_CT.identidad = lambda g: {"legal": "Acme Lifts Pty Ltd", "abn": "12 345 678 901", "plazo": 14}
try:
    from pypdf import PdfReader
    _nom = {"ID": "N2", "Group": "cliente1", "Name": "Ana", "PeriodFrom": "2026-09-08",
            "PeriodTo": "2026-09-14", "Hours": "4", "HourlyRate": "30.55", "Base": "122.2",
            "ConceptsJSON": "[]", "Net": "122.2", "PaymentDate": "2026-10-13", "Status": "pagada"}
    _txt = "\n".join(p.extract_text() for p in PdfReader(io.BytesIO(_P.generate_payslip_pdf(_nom, "cliente1"))).pages)
    chk("⚠️ el EMPLEADOR con su nombre legal y su ABN (decía «cliente1»)",
        "Acme Lifts Pty Ltd" in _txt and "ABN 12 345 678 901" in _txt and "cliente1" not in _txt, _txt[:200])
    chk("⚠️ periodo DD/MM/YYYY y el estado TRADUCIDO con su fecha («paid (13/10/2026)»)",
        "08/09/2026 → 14/09/2026" in _txt and "paid (13/10/2026)" in _txt and "pagada" not in _txt, _txt[:400])
finally:
    _CT.identidad = _ct0
from core.num import dmy                                                    # noqa: E402
chk("`num.dmy`: ISO → DD/MM/YYYY, lo vacío «—», lo ya bien igual",
    [dmy("2026-10-13"), dmy(""), dmy("13/10/2026"), dmy("2026-10-13 09:00:00")] ==
    ["13/10/2026", "—", "13/10/2026", "13/10/2026"])
at = _app(_CAMPO=True)
chk("«My payslips»: DD/MM/YYYY", not at.exception and any("01/09/2026 → 07/09/2026" in m.value for m in at.markdown),
    [m.value for m in at.markdown][:3])
_arb = ast.parse(io.open(os.path.join(RAIZ, "core", "payroll_ui.py"), encoding="utf-8").read())
_ctes = [v.value for n in ast.walk(_arb) for v in ([n] if isinstance(n, ast.Constant) else
         (n.values if isinstance(n, ast.JoinedStr) else [])) if isinstance(v, ast.Constant)
         and isinstance(v.value, str)]
# (por las f-string: `ast.walk` visita cada constante DOS veces —suelta y dentro de su
# f-string— y la 1ª sonda contaba 4 donde hay 2)
_fs = [n for n in ast.walk(_arb) if isinstance(n, ast.JoinedStr) and n.values
       and isinstance(n.values[0], ast.Constant) and n.values[0].value == "Payslip_"]
chk("los archivos se llaman «Payslip_…» (no «Colilla_»): la colilla del admin y la del campo",
    len(_fs) == 2 and not any("Colilla" in c for c in _ctes), (len(_fs), [c for c in _ctes if "Colilla" in c]))


def _frase(tx):
    tx = re.sub(r":material/\w+:", "", tx)
    return not tx.lstrip().startswith("<") and len(re.findall(r"[A-Za-z]{2,}", tx)) >= 2


_DISP = {"caption", "markdown", "info", "warning", "success", "error", "button", "exito", "aviso",
         "metric", "form_submit_button", "expander", "radio", "selectbox", "date_input", "number_input"}
_lit = []
for n in ast.walk(_arb):
    if isinstance(n, ast.Call) and isinstance(n.func, (ast.Attribute, ast.Name)):
        _fn = n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id
        if _fn in _DISP:
            for a in n.args[:1]:
                if (isinstance(a, ast.Constant) and isinstance(a.value, str) and _frase(a.value)) or \
                        (isinstance(a, ast.JoinedStr) and _frase("".join(
                            v.value for v in a.values if isinstance(v, ast.Constant)))):
                    _lit.append("%d %s" % (n.lineno, ast.unparse(a)[:50]))
chk("⚠️ ningún texto de pantalla sin `t()` en Payroll (avisos, pies, generar)", not _lit, _lit)

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("TODO OK")
