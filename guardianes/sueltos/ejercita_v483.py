# -*- coding: utf-8 -*-
"""Ejercita v483 CONTRA LA HOJA REAL y deja producción como estaba.

Método de v344: foto → ejercitar → verificar LEYENDO → limpiar → segunda foto.
Un test con datos que me invento no prueba nada; contra la hoja sí.

Lo que se ejercita y no se puede ejercitar de otra forma:
  · las 4 columnas nuevas de `Groups` migran solas y se escriben;
  · el ABN aparece en el PDF de la factura, que es el hallazgo de la versión;
  · el reparto del impuesto CUADRA con un caso que línea a línea NO cuadraría;
  · el vencimiento sale del plazo del grupo.
"""
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "admin", "nombre": "admin",
                            "rol": "administrator", "grupo": "cliente1"}

from core import auth, clientes, contable, invoices, invoice_pdf   # noqa: E402

G = "cliente1"
fallos = []


def ck(que, real, esperado):
    ok = real == esperado
    print(f"  {'ok  ' if ok else '*** FALLO'} {que}: {real!r}"
          + ("" if ok else f"  (esperado {esperado!r})"))
    if not ok:
        fallos.append(que)


# ── FOTO ────────────────────────────────────────────────────────────────────
print("=" * 72)
_facs0 = len(invoices.list_facturas(G))
_ident0 = contable.identidad(G)
print(f"  ANTES: facturas={_facs0} · identidad={_ident0}")

# ── 1 · las 4 columnas nuevas se escriben (migran solas) ────────────────────
print("-" * 72)
for campo, valor in (("ABN", "12 345 678 901"),
                     ("LegalName", "ZZZ Prueba v483 Pty Ltd"),
                     ("PaymentTermsDays", "30")):
    ok, msg = auth.set_group_setting(G, campo, valor)
    ck(f"escribe {campo}", ok, True)
auth._invalidate_groups()
_id = contable.identidad(G)
ck("lee el ABN", _id["abn"], "12 345 678 901")
ck("lee la razon social", _id["legal"], "ZZZ Prueba v483 Pty Ltd")
ck("lee el plazo", _id["plazo"], 30)

# ── 2 · una factura con redondeo que NO cuadraría línea a línea ─────────────
print("-" * 72)
_cli = clientes.list_clientes(G, incluir_inactivos=True)
_cid = str(_cli[0].get("ID", "")) if _cli else ""
_cnom = str(_cli[0].get("Name", "")) if _cli else "ZZZ Cliente prueba"
print(f"  cliente usado: {_cnom} ({_cid or 'sin ficha'})")

_lineas = [{"concepto": "ZZZ prueba A", "importe": 33.33, "proyecto_id": ""},
           {"concepto": "ZZZ prueba B", "importe": 33.33, "proyecto_id": ""},
           {"concepto": "ZZZ prueba C", "importe": 33.34, "proyecto_id": ""}]
ok, fid = invoices.create_factura(G, _cid, _cnom, _lineas, impuesto_pct=10.0,
                                  vencimiento="", nota="ZZZ PRUEBA v483",
                                  creado_por="admin")
ck("crea la factura", ok, True)
print("  id:", fid)

f = invoices.get_factura(fid)
_tax = float(f.get("Tax"))
ck("impuesto de la factura", round(_tax, 2), 10.0)
# ⚠️ Redondear cada línea por su cuenta daría 3.33*3 = 9.99, un céntimo menos.
_ingenuo = round(sum(round(l["importe"] * 0.10, 2) for l in _lineas), 2)
print(f"  linea a linea daria {_ingenuo} (un centavo menos que {round(_tax, 2)})")
ck("el ingenuo NO cuadra (si cuadrara, el caso no probaria nada)", _ingenuo == 10.0, False)

# ── 3 · el CSV reparte el impuesto y CUADRA ─────────────────────────────────
print("-" * 72)
r = contable.csv_ventas(G, "xero", None, None)
import csv as _csv
import io as _io
filas = list(_csv.DictReader(_io.StringIO(r["csv"])))
mias = [x for x in filas if x["*InvoiceNumber"] == str(f.get("Number"))]
ck("3 filas exportadas", len(mias), 3)
_suma = round(sum(float(x["TaxAmount"]) for x in mias), 2)
ck("la suma del impuesto CUADRA con la factura", _suma, round(_tax, 2))
_neto = round(sum(float(x["*UnitAmount"]) for x in mias), 2)
ck("el neto cuadra con el subtotal", _neto, round(float(f.get("Subtotal")), 2))
ck("las obligatorias de Xero no van vacias",
   all(x["*ContactName"] and x["*InvoiceDate"] and x["*DueDate"]
       and x["*Description"] and x["*AccountCode"] and x["*TaxType"] for x in mias), True)
ck("el impuesto de venta es el nombre de Xero", mias[0]["*TaxType"], "GST on Income")
print("  reparto:", [x["TaxAmount"] for x in mias])

# ── 4 · el ABN llega al PDF ─────────────────────────────────────────────────
print("-" * 72)
pdf = invoice_pdf.generate_invoice_pdf(f, {}, G)
from pypdf import PdfReader                                        # noqa: E402
txt = "\n".join(p.extract_text() or "" for p in PdfReader(_io.BytesIO(pdf)).pages)
ck("el PDF dice TAX INVOICE", "TAX INVOICE" in txt, True)
ck("el PDF lleva el ABN", "12 345 678 901" in txt, True)
ck("el PDF lleva la razon social", "ZZZ Prueba v483 Pty Ltd" in txt, True)
ck("y NO el nombre interno del grupo", "cliente1" in txt, False)

# ── LIMPIEZA ────────────────────────────────────────────────────────────────
print("-" * 72)
w, err = invoices._ws()
if err:
    fallos.append("no se pudo abrir la hoja para limpiar: " + str(err))
else:
    fila = invoices._find_row(w, fid)
    if fila:
        w.delete_rows(fila)
        invoices._invalidate()
        print(f"  borrada la fila {fila} de la factura de prueba")
    else:
        fallos.append("no se encontro la fila de la factura de prueba")

for campo, valor in (("ABN", _ident0["abn"]),
                     ("LegalName", ""),
                     ("PaymentTermsDays", "")):
    auth.set_group_setting(G, campo, valor)
auth._invalidate_groups()

# ── SEGUNDA FOTO ────────────────────────────────────────────────────────────
print("-" * 72)
ck("facturas como al empezar", len(invoices.list_facturas(G)), _facs0)
_idf = contable.identidad(G)
ck("identidad restaurada (abn)", _idf["abn"], _ident0["abn"])
ck("identidad restaurada (plazo por defecto)", _idf["plazo"], 14)

print("=" * 72)
print(f"{'TODO OK' if not fallos else str(len(fallos)) + ' FALLOS: ' + str(fallos)}")
sys.exit(1 if fallos else 0)
