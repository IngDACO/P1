"""Colilla de pago (payslip) en PDF para el usuario.

Una página: empleador (grupo) + «COLILLA DE PAGO / PAYSLIP», datos del empleado
y periodo, base (horas × tarifa), devengos, deducciones, neto a pagar, y los
aportes patronales (super) como informativo.
"""
import io as _io
import json

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from core.num import num as _num

C_BRAND = colors.HexColor("#1a3a5c")
C_LIGHT = colors.HexColor("#e8f1fb")
C_MUTE  = colors.HexColor("#7a8699")


def _money(v) -> str:
    return f"${_num(v):,.2f}"


def _conceptos(nom):
    try:
        return json.loads(nom.get("ConceptosJSON", "") or "[]")
    except Exception:
        return []


def generate_payslip_pdf(nomina: dict, grupo_nombre: str = "") -> bytes:
    ss = getSampleStyleSheet()
    H  = ParagraphStyle("H",  parent=ss["Normal"], fontSize=9, leading=12)
    Hb = ParagraphStyle("Hb", parent=ss["Normal"], fontSize=9, leading=12, fontName="Helvetica-Bold")
    sm = ParagraphStyle("sm", parent=ss["Normal"], fontSize=8, textColor=C_MUTE, leading=11)
    mk = ParagraphStyle("mk", parent=ss["Normal"], fontSize=14, fontName="Helvetica-Bold", textColor=C_BRAND)
    ti = ParagraphStyle("ti", parent=ss["Normal"], fontSize=16, fontName="Helvetica-Bold", textColor=C_BRAND)

    buf = _io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm,
                            title=f"Colilla {nomina.get('Nombre', '')}")
    story = []

    marca = grupo_nombre or str(nomina.get("Grupo", ""))
    head = Table([[Paragraph(str(marca), mk), Paragraph("COLILLA DE PAGO / PAYSLIP", ti)]],
                 colWidths=[90 * mm, 88 * mm])
    head.setStyle(TableStyle([("ALIGN", (1, 0), (1, 0), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [head, Spacer(1, 10)]

    est = str(nomina.get("Estado", "emitida"))
    if est == "pagada" and str(nomina.get("FechaPago", "")).strip():
        est = f"pagada ({nomina.get('FechaPago')})"
    emp = Table([
        [Paragraph("Empleado", sm), Paragraph(str(nomina.get("Nombre", "")), Hb),
         Paragraph("Periodo", sm), Paragraph(f"{nomina.get('PeriodoDesde', '')} → {nomina.get('PeriodoHasta', '')}", H)],
        [Paragraph("Horas", sm), Paragraph(f"{_num(nomina.get('Horas')):.2f} h", H),
         Paragraph("Estado", sm), Paragraph(est, H)],
    ], colWidths=[22 * mm, 67 * mm, 22 * mm, 67 * mm])
    emp.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                             ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    story += [emp, Spacer(1, 12)]

    conceptos = _conceptos(nomina)
    base = _num(nomina.get("Base"))
    data = [[Paragraph("<b>Concepto</b>", ParagraphStyle("hh", parent=Hb, textColor=colors.white)),
             Paragraph("<b>Tipo</b>", ParagraphStyle("ht", parent=Hb, textColor=colors.white)),
             Paragraph("<b>Monto</b>", ParagraphStyle("hr", parent=Hb, textColor=colors.white))]]
    data.append([Paragraph(f"Mano de obra ({_num(nomina.get('Horas')):.2f} h × {_money(nomina.get('TarifaHora'))})", H),
                 Paragraph("devengo", H), Paragraph(_money(base), H)])
    for c in conceptos:
        data.append([Paragraph(str(c.get("concepto", "")), H),
                     Paragraph(str(c.get("tipo", "")), H), Paragraph(_money(c.get("monto")), H)])
    t = Table(data, colWidths=[110 * mm, 30 * mm, 38 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_BRAND),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, C_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#c3ccd8")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    story += [t, Spacer(1, 8)]

    dev = sum(_num(c.get("monto")) for c in conceptos if str(c.get("tipo", "")).lower() == "devengo")
    ded = sum(_num(c.get("monto")) for c in conceptos if str(c.get("tipo", "")).lower() == "deduccion")
    ap  = sum(_num(c.get("monto")) for c in conceptos if str(c.get("tipo", "")).lower() == "aporte")
    tot = Table([
        ["Bruto (base + devengos)", _money(base + dev)],
        ["Deducciones", _money(ded)],
        ["NETO A PAGAR", _money(nomina.get("Neto"))],
    ], colWidths=[50 * mm, 40 * mm], hAlign="RIGHT")
    tot.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"), ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LINEABOVE", (0, 2), (-1, 2), 0.6, C_BRAND),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"), ("TEXTCOLOR", (0, 2), (-1, 2), C_BRAND),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    story += [tot]
    if ap > 0:
        story += [Spacer(1, 6),
                  Paragraph(f"Aportes patronales (no descontados al empleado): {_money(ap)}", sm)]
    story += [Spacer(1, 6),
              Paragraph("Documento generado por la app; los importes de ley deben validarse.", sm)]

    doc.build(story)
    return buf.getvalue()
