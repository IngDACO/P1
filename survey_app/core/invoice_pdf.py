"""PDF de factura (tax invoice) para enviar al cliente.

Una página A4: marca del grupo + «TAX INVOICE», datos (nº/fecha/vencimiento/estado),
«Bill to» (cliente + contacto de su ficha), tabla de líneas, y totales (subtotal ·
impuesto · total · cobrado · por cobrar).
Mismo lenguaje visual que `tool_pdf` (reportlab platypus).

⚠️ El texto va en INGLÉS y pasa por `i18n.d()`, que ignora el idioma de la interfaz
(v436): este documento sale de la empresa y su idioma no puede depender de cómo tenga
la pantalla quien pulsa el botón.
⚠️ El ESTADO se muestra con `i18n.etiqueta()`: en la hoja sigue siendo `"cobrada"` /
`"vencida"` —así lo compara `estado_cobro` y medio módulo de finanzas— y solo cambia
cómo se lee.
"""
import io as _io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core import invoices as I
from core import i18n
from core.i18n import d
from core.num import num as _num

C_BRAND = colors.HexColor("#1a3a5c")
C_LIGHT = colors.HexColor("#e8f1fb")
C_MUTE  = colors.HexColor("#7a8699")


def _money(v) -> str:
    return f"${_num(v):,.2f}"


def generate_invoice_pdf(factura: dict, cliente: dict = None, grupo_nombre: str = "") -> bytes:
    ss = getSampleStyleSheet()
    H  = ParagraphStyle("H",  parent=ss["Normal"], fontSize=9, leading=12)
    Hb = ParagraphStyle("Hb", parent=ss["Normal"], fontSize=9, leading=12, fontName="Helvetica-Bold")
    sm = ParagraphStyle("sm", parent=ss["Normal"], fontSize=8, textColor=C_MUTE, leading=11)
    mk = ParagraphStyle("mk", parent=ss["Normal"], fontSize=14, fontName="Helvetica-Bold", textColor=C_BRAND)
    ti = ParagraphStyle("ti", parent=ss["Normal"], fontSize=18, fontName="Helvetica-Bold", textColor=C_BRAND)

    buf = _io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm,
                            title=d("Invoice {n}", n=factura.get("Number", "")))
    story = []

    marca = grupo_nombre or str(factura.get("Group", ""))
    head = Table([[Paragraph(str(marca), mk), Paragraph(d("TAX INVOICE"), ti)]],
                 colWidths=[90 * mm, 88 * mm])
    head.setStyle(TableStyle([("ALIGN", (1, 0), (1, 0), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [head, Spacer(1, 10)]

    est = I.estado_cobro(factura)
    meta = Table([
        [Paragraph(d("Invoice no."), sm), Paragraph(str(factura.get("Number", "")), Hb)],
        [Paragraph(d("Date"), sm), Paragraph(str(factura.get("Date", "")), H)],
        [Paragraph(d("Due"), sm), Paragraph(str(factura.get("ExpiryDate", "") or "—"), H)],
        [Paragraph(d("Status"), sm), Paragraph(i18n.etiqueta(est), H)],
    ], colWidths=[24 * mm, 34 * mm])
    meta.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))

    cli = cliente or {}
    bill = [Paragraph(f"<b>{d('Bill to')}</b>", Hb),
            Paragraph(str(factura.get("ClientName", "") or cli.get("Name", "") or "—"), H)]
    for k in ("ContactName", "Address", "Email", "Phone"):
        v = str(cli.get(k, "")).strip()
        if v:
            bill.append(Paragraph(v, sm))
    info = Table([[bill, meta]], colWidths=[104 * mm, 74 * mm])
    info.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [info, Spacer(1, 12)]

    data = [[Paragraph(f"<b>{d('Description')}</b>", ParagraphStyle("hh", parent=Hb, textColor=colors.white)),
             Paragraph(f"<b>{d('Amount')}</b>", ParagraphStyle("hr", parent=Hb, textColor=colors.white))]]
    for ln in I.lineas_de(factura):
        data.append([Paragraph(str(ln.get("concepto", "")), H), Paragraph(_money(ln.get("importe")), H)])
    t = Table(data, colWidths=[133 * mm, 45 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_BRAND),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, C_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#c3ccd8")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story += [t, Spacer(1, 8)]

    imp_pct = _num(factura.get("TaxPct"))
    por_cobrar = _num(factura.get("Total")) - _num(factura.get("Collected"))
    tot = Table([
        [d("Subtotal"), _money(factura.get("Subtotal"))],
        [d("Tax ({pct}%)", pct=f"{imp_pct:.0f}"), _money(factura.get("Tax"))],
        [d("TOTAL"), _money(factura.get("Total"))],
        [d("Paid"), _money(factura.get("Collected"))],
        [d("Balance due"), _money(por_cobrar)],
    ], colWidths=[48 * mm, 40 * mm], hAlign="RIGHT")
    tot.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"), ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LINEABOVE", (0, 2), (-1, 2), 0.6, C_BRAND),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"), ("TEXTCOLOR", (0, 2), (-1, 2), C_BRAND),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    story += [tot, Spacer(1, 10)]

    if str(factura.get("Note", "")).strip():
        story += [Paragraph(f"<b>{d('Note:')}</b> {factura.get('Note')}", sm)]

    doc.build(story)
    return buf.getvalue()
