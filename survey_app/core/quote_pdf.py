"""PDF de cotización para enviar al cliente (v353).

Misma cara que `invoice_pdf` a propósito: quien recibe la cotización y luego la factura
tiene que ver dos documentos de la misma casa. Una página A4: marca del grupo +
«COTIZACIÓN», datos (Nº/fecha/**validez**/estado), «Para», tabla de líneas y totales.

⚠️ El cliente NO ve el costo ni el margen. Solo concepto, cantidad y precio — el desglose
de lo que te cuesta es tuyo. Es la diferencia entre una cotización y una hoja de cálculo
interna, y por eso las columnas se arman aquí y no se vuelca la línea entera.
"""
import io as _io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core import quotes as Q
from core.num import num as _num

C_BRAND = colors.HexColor("#1a3a5c")
C_LIGHT = colors.HexColor("#e8f1fb")
C_MUTE = colors.HexColor("#7a8699")


def _money(v) -> str:
    return f"${_num(v):,.2f}"


def generate_quote_pdf(cot: dict, cliente: dict = None, grupo_nombre: str = "") -> bytes:
    ss = getSampleStyleSheet()
    H = ParagraphStyle("H", parent=ss["Normal"], fontSize=9, leading=12)
    Hb = ParagraphStyle("Hb", parent=ss["Normal"], fontSize=9, leading=12, fontName="Helvetica-Bold")
    sm = ParagraphStyle("sm", parent=ss["Normal"], fontSize=8, textColor=C_MUTE, leading=11)
    mk = ParagraphStyle("mk", parent=ss["Normal"], fontSize=14, fontName="Helvetica-Bold", textColor=C_BRAND)
    ti = ParagraphStyle("ti", parent=ss["Normal"], fontSize=18, fontName="Helvetica-Bold", textColor=C_BRAND)

    buf = _io.BytesIO()
    num = str(cot.get("Numero", ""))
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm,
                            title=f"Cotización {num}")
    story = []

    marca = grupo_nombre or str(cot.get("Grupo", ""))
    head = Table([[Paragraph(str(marca), mk), Paragraph("COTIZACIÓN", ti)]],
                 colWidths=[90 * mm, 88 * mm])
    head.setStyle(TableStyle([("ALIGN", (1, 0), (1, 0), "RIGHT"),
                              ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [head, Spacer(1, 10)]

    _ver = int(_num(cot.get("Version"), 1))
    meta = Table([
        [Paragraph("Nº", sm), Paragraph(num + (f"  ·  v{_ver}" if _ver > 1 else ""), Hb)],
        [Paragraph("Fecha", sm), Paragraph(str(cot.get("Fecha", "")), H)],
        [Paragraph("Válida hasta", sm), Paragraph(str(cot.get("Validez", "") or "—"), Hb)],
        [Paragraph("Estado", sm), Paragraph(Q.estado_de(cot), H)],
    ], colWidths=[26 * mm, 34 * mm])
    meta.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 1),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))

    cli = cliente or {}
    para = [Paragraph("<b>Para</b>", Hb),
            Paragraph(str(cot.get("ClienteNombre", "") or cli.get("Nombre", "") or "—"), H)]
    for k in ("Contacto", "Direccion", "Email", "Telefono"):
        v = str(cli.get(k, "") or "").strip()
        if v:
            para.append(Paragraph(v, sm))
    bloque = Table([[para, meta]], colWidths=[102 * mm, 76 * mm])
    bloque.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [bloque, Spacer(1, 12)]

    # ── Líneas: SIN costo ni margen (ver el módulo) ──────────────
    filas = [[Paragraph("<b>Concepto</b>", Hb), Paragraph("<b>Cant.</b>", Hb),
              Paragraph("<b>Importe</b>", Hb)]]
    for l in Q.lineas_de(cot):
        txt = str(l.get("concepto", ""))
        desc = str(l.get("descripcion", "") or "").strip()
        celda = [Paragraph(txt, H)] + ([Paragraph(desc, sm)] if desc else [])
        cant = _num(l.get("cantidad"))
        uni = str(l.get("unidad", "") or "")
        cant_txt = f"{cant:g}" + (f" {uni}" if uni and uni != "unidad" else "")
        filas.append([celda, Paragraph(cant_txt, H),
                      Paragraph(_money(l.get("precio_total")), H)])
    tab = Table(filas, colWidths=[112 * mm, 24 * mm, 42 * mm], repeatRows=1)
    tab.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_LIGHT),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, C_BRAND),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.HexColor("#dfe4ec")),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [tab, Spacer(1, 10)]

    imp_pct = _num(cot.get("ImpuestoPct"))
    tot = [["Subtotal", _money(cot.get("Subtotal"))]]
    if imp_pct > 0:
        tot.append([f"Impuesto ({imp_pct:g}%)", _money(cot.get("Impuesto"))])
    tot.append(["TOTAL", _money(cot.get("Total"))])
    t = Table([[Paragraph(a, Hb if a == "TOTAL" else H),
                Paragraph(b, Hb if a == "TOTAL" else H)] for a, b in tot],
              colWidths=[42 * mm, 34 * mm], hAlign="RIGHT")
    t.setStyle(TableStyle([("ALIGN", (1, 0), (1, -1), "RIGHT"),
                           ("LINEABOVE", (0, len(tot) - 1), (-1, len(tot) - 1), 0.6, C_BRAND),
                           ("TOPPADDING", (0, 0), (-1, -1), 3),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    story += [t, Spacer(1, 14)]

    nota = str(cot.get("Nota", "") or "").strip()
    if nota:
        story += [Paragraph("<b>Notas</b>", Hb), Paragraph(nota, H), Spacer(1, 8)]
    story += [Paragraph(
        f"Cotización válida hasta el {cot.get('Validez', '') or '—'}. "
        "Precios sujetos a confirmación por escrito una vez vencida esa fecha.", sm)]

    doc.build(story)
    return buf.getvalue()
