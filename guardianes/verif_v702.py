# -*- coding: utf-8 -*-
"""v702 · D3 del ciclo 7 («como se hace normalmente»): la certificación ES la factura (Progress Claim / Tax Invoice),
el depósito se recupera en proporción al avance, y New invoice sigue ofreciendo las líneas de la cotización tras un
depósito (con el depósito restado). Sin red ni escrituras: sustitutos guardados y devueltos al acabar (trampa 48).

Los números son los de C7 (PRJ-0048): contrato $73,692, depósito 30 % = $20,811.60 (factura 0007), retención 5 %;
una certificación al 10,6 % → trabajo $7,811.35, depósito recuperado $2,206.03, retención $390.57, neto $5,214.75.
"""
import io
import json
import os
import sys

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:900]))
    if not cond:
        FALLOS.append(nombre)


from core import claims as CL, invoices as I, projects as P, quotes as Q, contable   # noqa: E402

PID = "PRJ-0048"
DEP = {"ID": "FAC-0007", "Number": "0007", "Status": "emitida", "Collected": "10050", "Subtotal": "20811.6",
       "LinesJSON": json.dumps([{"concepto": "Deposit 30% — C7 — Northshore Lifts — Lift 1 (money)",
                                 "importe": 20811.6, "proyecto_id": PID}])}
OTRA = {"ID": "FAC-0050", "Number": "0050", "Status": "emitida", "Collected": "0", "Subtotal": "500",
        "LinesJSON": json.dumps([{"concepto": "Works — extra", "importe": 500, "proyecto_id": PID}])}
ANUL = {"ID": "FAC-0008", "Number": "0008", "Status": "anulada", "Collected": "0", "Subtotal": "100",
        "LinesJSON": json.dumps([{"concepto": "Deposit 1% — C7", "importe": 100, "proyecto_id": PID}])}

_G = {}


def guarda(mod, *nombres):
    for n in nombres:
        _G[(mod, n)] = getattr(mod, n)


def devuelve():
    for (mod, n), f in _G.items():
        setattr(mod, n, f)


guarda(I, "list_facturas", "create_factura", "get_factura", "anular", "_anular_factura")
guarda(CL, "_ws", "_siguiente", "_fila", "_set", "_invalidate", "contrato", "valor_variaciones", "reclamaciones",
       "retencion_pct", "retenido", "_records", "anular")
guarda(P, "get_project")
guarda(Q, "cotizacion_de_proyecto")
guarda(contable, "identidad")
try:
    print("A. El depósito de una obra (y lo que no es depósito)")
    I.list_facturas = lambda grupo=None, cliente_id=None: [DEP, ANUL]
    dp = CL.deposito_de(PID, "cliente1")
    chk("el depósito facturado (0007, $20,811.60); la anulada (0008) no cuenta", dp["deposito"] == 20811.6
        and dp["numeros"] == ["0007"] and dp["recuperado"] == 0 and dp["otras"] == 0, dp)
    I.list_facturas = lambda grupo=None, cliente_id=None: [DEP, OTRA, ANUL, {
        "ID": "FAC-0010", "Number": "0010", "Status": "emitida", "Collected": "0", "Subtotal": "5214.75",
        "LinesJSON": json.dumps([{"concepto": "Progress claim #1", "importe": 7811.35, "proyecto_id": PID,
                                  "tipo": "certificacion", "reclamacion": "CLM-PRJ-0048-001"},
                                 {"concepto": "Less deposit", "importe": -2206.03, "proyecto_id": PID,
                                  "tipo": "menos_deposito", "reclamacion": "CLM-PRJ-0048-001"},
                                 {"concepto": "Less retention", "importe": -390.57, "proyecto_id": PID,
                                  "tipo": "menos_retencion", "reclamacion": "CLM-PRJ-0048-001"}])}]
    dp2 = CL.deposito_de(PID, "cliente1")
    chk("lo ya recuperado por una certificación (2,206.03) y lo pendiente (18,605.57)", dp2["recuperado"] == 2206.03
        and dp2["pendiente"] == 18605.57, dp2)
    chk("…y lo facturado aparte, ni depósito ni certificación (la «Works — extra», 500)", dp2["otras"] == 500, dp2)

    print("\nB. Lo que se puede certificar, con el depósito restado")
    I.list_facturas = lambda grupo=None, cliente_id=None: [DEP]
    CL.contrato = lambda pid: (73692.0, "COT-0018")
    CL.valor_variaciones = lambda pid: 0.0
    CL.reclamaciones = lambda pid, incluir_anuladas=False: []
    CL.retencion_pct = lambda grupo: 5.0
    CL.retenido = lambda pid: {"retenido": 0.0, "liberado": 0.0, "pendiente": 0.0}
    d = CL.calcular(PID, "cliente1", 10.6, {"ID": PID})
    chk("al 10,6 %: trabajo 7,811.35 − depósito 2,206.03 − retención 390.57 = neto 5,214.75",
        d["bruto"] == 7811.35 and d["menos_deposito"] == 2206.03 and d["retencion"] == 390.57 and d["neto"] == 5214.75, d)
    CL.reclamaciones = lambda pid, incluir_anuladas=False: [{"WorkDone": "66322.8", "Number": "1"}]
    I.list_facturas = lambda grupo=None, cliente_id=None: [DEP, {
        "ID": "FAC-0011", "Number": "0011", "Status": "emitida", "Collected": "0", "Subtotal": "1",
        "LinesJSON": json.dumps([{"concepto": "Less deposit", "importe": -18730.44, "proyecto_id": PID,
                                  "tipo": "menos_deposito", "reclamacion": "CLM-PRJ-0048-001"}])}]
    d100 = CL.calcular(PID, "cliente1", 100, {"ID": PID})
    chk("al 100 %: se recupera lo que queda del depósito (2,081.16), todo", d100["menos_deposito"] == 2081.16, d100)

    print("\nC. Emitir una certificación emite SU factura")
    I.list_facturas = lambda grupo=None, cliente_id=None: [DEP]
    CL.reclamaciones = lambda pid, incluir_anuladas=False: []

    class _W:
        def __init__(self):
            self.filas = []

        def append_row(self, fila, value_input_option=None):
            self.filas.append(fila)
    _w = _W()
    _sets, _facs = [], []
    CL._ws = lambda hoja, headers: _w
    CL._siguiente = lambda hoja, headers, pid: 1
    CL._invalidate = lambda: None
    CL._fila = lambda w, hoja, oid: (7, {"ID": oid})
    CL._set = lambda w, col, fila, campos: (_sets.append((fila, campos)) or (True, ""))
    P.get_project = lambda pid: {"ID": PID, "Name": "C7 — Northshore Lifts — Lift 1 (money)",
                                 "ClientID": "CLI-0009", "Client": "C7 — Northshore Lifts Pty Ltd (test)"}
    Q.cotizacion_de_proyecto = lambda pid: {"ID": "COT-0018", "TaxPct": "10", "ClientID": "CLI-0009"}
    contable.identidad = lambda grupo: {"plazo": 14}
    I.create_factura = lambda grupo, cliente_id, cliente_nombre, lineas, impuesto_pct=0.0, fecha="", \
        vencimiento="", numero="", nota="", creado_por="": (_facs.append(
            {"cli": cliente_id, "nom": cliente_nombre, "lineas": lineas, "imp": impuesto_pct, "venc": vencimiento})
            or (True, "FAC-0010"))
    I.get_factura = lambda fid: {"ID": fid, "Number": "0010"}
    ok, msg = CL.crear_reclamacion(PID, "cliente1", 10.6, "", "", "Admin2", None)
    chk("emite la certificación y dice su factura («invoice No. 0010 issued»)", ok and "invoice No. 0010" in msg
        and len(_w.filas) == 1, (ok, msg))
    _ls = _facs[0]["lineas"] if _facs else []
    chk("la factura: el valor del periodo, «Less deposit» y «Less retention», enlazadas a la certificación",
        [round(x["importe"], 2) for x in _ls] == [7811.35, -2206.03, -390.57]
        and [x["tipo"] for x in _ls] == ["certificacion", "menos_deposito", "menos_retencion"]
        and all(x["reclamacion"] == "CLM-PRJ-0048-001" and x["proyecto_id"] == PID for x in _ls), _ls)
    chk("…del cliente de la obra, con el impuesto de su cotización y el plazo del grupo",
        _facs and _facs[0]["cli"] == "CLI-0009" and _facs[0]["imp"] == 10.0 and _facs[0]["venc"], _facs[:1])
    I.create_factura = lambda *a, **k: (False, "boom")
    _sets.clear()
    ok2, msg2 = CL.crear_reclamacion(PID, "cliente1", 10.6, "", "", "Admin2", None)
    chk("si la factura falla, la certificación NO se queda (anulada) y se dice", not ok2 and "boom" in msg2
        and _sets and _sets[-1][1].get("Status") == CL.ANULADA, (ok2, msg2, _sets))

    print("\nD. Anular la certificación anula su factura (y con cobros, se para)")
    CL.reclamaciones = lambda pid, incluir_anuladas=False: [{"ID": "CLM-PRJ-0048-001", "Number": "1", "Status": "issued"}]
    CL._fila = lambda w, hoja, oid: (7, {"ID": oid, "ProjectID": PID, "Number": "1", "Group": "cliente1"})
    _CLAIM_FAC = {"ID": "FAC-0010", "Number": "0010", "Status": "emitida", "Collected": "1000", "Subtotal": "5214.75",
                  "LinesJSON": json.dumps([{"concepto": "Progress claim #1", "importe": 7811.35, "proyecto_id": PID,
                                            "tipo": "certificacion", "reclamacion": "CLM-PRJ-0048-001"}])}
    I.list_facturas = lambda grupo=None, cliente_id=None: [DEP, _CLAIM_FAC]
    _anul = []
    I.anular = lambda fid, destino_cobros=None, quien="", _desde_reclamacion=False: (
        _anul.append((fid, _desde_reclamacion)) or (True, "Invoice voided."))
    _sets.clear()
    ok3, msg3 = CL.anular("CLM-PRJ-0048-001")
    chk("con cobros en su factura: se para y manda a Invoices (donde se decide qué pasa con el dinero)",
        not ok3 and "Invoices" in msg3 and not _anul and not _sets, (ok3, msg3))
    _CLAIM_FAC["Collected"] = "0"
    ok4, msg4 = CL.anular("CLM-PRJ-0048-001")
    chk("sin cobros: anula su factura (desde la certificación) y la certificación", ok4 and _anul == [("FAC-0010", True)]
        and _sets and _sets[-1][1].get("Status") == CL.ANULADA and "0010" in msg4, (ok4, msg4, _anul))

    print("\nE. Anular en Invoices la factura de una certificación")
    devuelve_i = _G[(I, "anular")]
    I.anular = devuelve_i
    I.get_factura = lambda fid: dict(_CLAIM_FAC)
    _voids, _cancels = [], []
    I._anular_factura = lambda f, fid, destino_cobros=None, quien="": (_voids.append(fid) or (True, "Invoice voided."))
    CL.anular = lambda cid, _con_factura=True: (_cancels.append((cid, _con_factura)) or (True, "x"))
    CL._records = lambda hoja: [{"ID": "CLM-PRJ-0048-001", "ProjectID": PID, "Number": "1", "Status": "issued"},
                                {"ID": "CLM-PRJ-0048-002", "ProjectID": PID, "Number": "2", "Status": "issued"}]
    CL.reclamaciones = lambda pid, incluir_anuladas=False: CL._records("Claims")
    ok5, msg5 = I.anular("FAC-0010")
    chk("la de una certificación que NO es la última: se niega («only the latest claim»)", not ok5
        and "latest claim" in msg5 and not _voids, (ok5, msg5))
    CL._records = lambda hoja: [{"ID": "CLM-PRJ-0048-001", "ProjectID": PID, "Number": "1", "Status": "issued"}]
    ok6, msg6 = I.anular("FAC-0010")
    chk("la de la última: la anula y cancela la certificación (sin volver a tocar la factura)", ok6
        and _voids == ["FAC-0010"] and _cancels == [("CLM-PRJ-0048-001", False)] and "claim" in msg6, (ok6, msg6))
finally:
    devuelve()

print("\nF. El PDF de la certificación resta el depósito")
from core import claim_pdf                                                      # noqa: E402
_rec = {"Number": "1", "Date": "2026-11-23", "PctComplete": "10.6", "ContractValue": "73692", "VariationsValue": "0",
        "WorkDone": "7811.35", "PreviouslyClaimed": "0", "RetentionPct": "5", "Retention": "390.57",
        "ThisClaim": "7811.35", "Status": "issued", "_menos_deposito": 2206.03}
try:
    from pypdf import PdfReader
    _pdf = claim_pdf.generate_claim_pdf(_rec, [], {}, "cliente1", {"Name": "C7"}, {})
    _tx = " ".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(_pdf)).pages)
    chk("«Less deposit recovered» y el neto 5,214.75", "Less deposit recovered" in _tx and "5,214.75" in _tx, _tx[-500:])
    _pdf0 = claim_pdf.generate_claim_pdf(dict(_rec, _menos_deposito=0), [], {}, "cliente1", {"Name": "C7"}, {})
    _tx0 = " ".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(_pdf0)).pages)
    chk("…y sin depósito, sin esa línea (neto 7,420.78, como siempre)", "Less deposit" not in _tx0
        and "7,420.78" in _tx0, _tx0[-400:])
except Exception as e:
    chk("el PDF se genera", False, str(e))

print("\nG. Las pantallas")
_cu = open("core/claims_ui.py", encoding="utf-8").read()
chk("Claims: la vista previa con «− deposit» y «Open invoice No.» en vez de «Mark paid» cuando hay factura",
    "− deposit {dp}" in _cu and 'Open invoice No. {n}' in _cu and "elif b1.button(t(\"Mark paid\")" in _cu)
# (la frase va partida en dos cadenas en el fuente: se buscan los dos trozos)
chk("…y el aviso de cobro doble solo por lo facturado que NO es depósito", "outside claims and " in _cu
    and "Claims do not subtract it" in _cu and "Claims are " not in _cu)
_iu = open("core/invoices_ui.py", encoding="utf-8").read()
chk("New invoice: «Invoice it as» también tras un depósito, y «Less deposit» restando",
    "if I.es_cotizada(_pid1) and _solo_dep:" in _iu and 'if _num((_dep1 or {}).get("pendiente")) > 0:' in _iu
    and 'Less deposit (invoice No. {n})' in _iu and '"Importe": -round(_num(_dep1["pendiente"]), 2)' in _iu)
chk("…la columna «Amount» admite negativos, y una factura de total ≤ 0 no se emite",
    'format="$%,.2f", min_value=0.0' not in _iu and "if _sub <= 0:" in _iu)

print()
print("verif_v702: %d FALLOS" % len(FALLOS) if FALLOS else "verif_v702: TODO OK")
sys.exit(1 if FALLOS else 0)
