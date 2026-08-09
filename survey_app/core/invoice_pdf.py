"""PDF de factura (tax invoice) para enviar al cliente.

Una página A4: marca del grupo + «FACTURA / TAX INVOICE», datos (Nº/fecha/
vencimiento/estado), «Facturar a» (cliente + contacto de su ficha), tabla de
líneas, y totales (subtotal · impuesto · total · cobrado · por cobrar).
Mismo lenguaje visual que `tool_pdf` (reportlab platypus).
"""
import io as _io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core import invoices as I

C_BRAND = colors.HexColor("#1a3a5c")
C_LIGHT = colors.HexColor("#e8f1fb")
C_MUTE  = colors.HexColor("#7a8699")


def _num(v, d=0.0) -> float:
    try:
        return float(str(v).replace(",", "."))
    except Exception:
        return d


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
                            title=f"Factura {factura.get('Numero', '')}")
    story = []

    marca = grupo_nombre or str(factura.get("Grupo", ""))
    head = Table([[Paragraph(str(marca), mk), Paragraph("FACTURA / TAX INVOICE", ti)]],
                 colWidths=[90 * mm, 88 * mm])
    head.setStyle(TableStyle([("ALIGN", (1, 0), (1, 0), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [head, Spacer(1, 10)]

    est = I.estado_cobro(factura)
    meta = Table([
        [Paragraph("Nº", sm), Paragraph(str(factura.get("Numero", "")), Hb)],
        [Paragraph("Fecha", sm), Paragraph(str(factura.get("Fecha", "")), H)],
        [Paragraph("Vencimiento", sm), Paragraph(str(factura.get("Vencimiento", "") or "—"), H)],
        [Paragraph("Estado", sm), Paragraph(est, H)],
    ], colWidths=[24 * mm, 34 * mm])
    meta.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))

    cli = cliente or {}
    bill = [Paragraph("<b>Facturar a</b>", Hb),
            Paragraph(str(factura.get("ClienteNombre", "") or cli.get("Nombre", "") or "—"), H)]
    for k in ("Contacto", "Direccion", "Email", "Telefono"):
        v = str(cli.get(k, "")).strip()
        if v:
            bill.append(Paragraph(v, sm))
    info = Table([[bill, meta]], colWidths=[104 * mm, 74 * mm])
    info.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [info, Spacer(1, 12)]

    data = [[Paragraph("<b>Concepto</b>", ParagraphStyle("hh", parent=Hb, textColor=colors.white)),
             Paragraph("<b>Importe</b>", ParagraphStyle("hr", parent=Hb, textColor=colors.white))]]
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

    imp_pct = _num(factura.get("ImpuestoPct"))
    por_cobrar = _num(factura.get("Total")) - _num(factura.get("Cobrado"))
    tot = Table([
        ["Subtotal", _money(factura.get("Subtotal"))],
        [f"Impuesto ({imp_pct:.0f}%)", _money(factura.get("Impuesto"))],
        ["TOTAL", _money(factura.get("Total"))],
        ["Cobrado", _money(factura.get("Cobrado"))],
        ["Por cobrar", _money(por_cobrar)],
    ], colWidths=[48 * mm, 40 * mm], hAlign="RIGHT")
    tot.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"), ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LINEABOVE", (0, 2), (-1, 2), 0.6, C_BRAND),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"), ("TEXTCOLOR", (0, 2), (-1, 2), C_BRAND),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    story += [tot, Spacer(1, 10)]

    if str(factura.get("Nota", "")).strip():
        story += [Paragraph(f"<b>Nota:</b> {factura.get('Nota')}", sm)]

    doc.build(story)
    return buf.getvalue()
