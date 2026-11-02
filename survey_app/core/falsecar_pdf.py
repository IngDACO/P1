# -*- coding: utf-8 -*-
"""PDF del Daily False Car Checklist (v636): calca el formato de CI Liftworx (marca pequeña, título
grande, tabla con serifa, y debajo la persona, la firma y la fecha). Marca = nombre del grupo, como
el Pre-Start (v172). Lo único que no está en el papel es la línea de la obra y el número del registro:
el papel va en la carpeta de la obra, y sin ellos este PDF no diría de dónde es."""
import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core import falsecar as FC
from core.i18n import d
from core.num import dmy
from core.prestart_pdf import W, _celda_firma, _esc, _styles

_MARCA = ParagraphStyle("FCMarca", fontName="Helvetica-Oblique", fontSize=10, leading=12)
_TIT = ParagraphStyle("FCTit", fontName="Helvetica-Bold", fontSize=24, leading=28)
_SUB = ParagraphStyle("FCSub", fontName="Helvetica", fontSize=11.5, leading=15)
_OBRA = ParagraphStyle("FCObra", fontName="Helvetica", fontSize=9, leading=12,
                       textColor=colors.HexColor("#555555"))
_CEL = ParagraphStyle("FCCel", fontName="Times-Roman", fontSize=10.5, leading=12.5)
_CENT = ParagraphStyle("FCCent", parent=_CEL, alignment=TA_CENTER)
_PIE = ParagraphStyle("FCPie", fontName="Helvetica", fontSize=11, leading=14)


def _marca_resultado(res) -> Paragraph:
    """✓ o X. ⚠️ El ✓ con ZapfDingbats, y como el carácter ✓: Helvetica no lo tiene, y a ZapfDingbats
    hay que dárselo en Unicode (con su byte, «3», reportlab pinta un cuadro negro: visto en el PDF)."""
    if res == FC.PASA:
        return Paragraph('<font name="ZapfDingbats" size="13">✓</font>', _CENT)
    if res == FC.FALLA:
        return Paragraph('<font name="Helvetica-Bold" size="12">X</font>', _CENT)
    return Paragraph("&nbsp;", _CENT)


def generate_pdf(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=11 * mm, bottomMargin=9 * mm,
                            title=d("Daily False Car Checklist {id}", id=data.get("id", "")))
    st = _styles()
    _obra = [x for x in (_esc(data.get("proyecto_nombre", "")), _esc(data.get("id", ""))) if x]
    el = [Paragraph(_esc(data.get("grupo", "")), _MARCA), Spacer(1, 7),
          Paragraph(d(FC.TITULO), _TIT), Spacer(1, 3),
          Paragraph(d(FC.SUBTITULO), _SUB),
          Paragraph(d("Project: ") + " · ".join(_obra), _OBRA), Spacer(1, 8)]

    _res = data.get("resultados") or {}
    filas = [[Paragraph(x, _CENT) for x in ("No.", "Inspection items", "Inspection results", "Remarks")]]
    for n, (k, texto) in enumerate(FC.CHECKS, 1):
        _r = _res.get(k) or {}
        filas.append([Paragraph(str(n), _CENT),
                      Paragraph(_esc(texto).replace("\n", "<br/>"), _CEL),
                      _marca_resultado(_r.get("res")),
                      Paragraph(_esc(_r.get("nota", "")), _CEL)])
    tab = Table(filas, colWidths=[W * 0.07, W * 0.56, W * 0.18, W * 0.19], repeatRows=1)
    tab.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    el += [tab, Spacer(1, 12)]

    pie = Table([[Paragraph("Name of person conducting daily check", _PIE),
                  Paragraph(_esc(data.get("nombre", "")), _PIE)],
                 [Paragraph("Signature", _PIE),
                  _celda_firma({"sig": data.get("firma"), "initial": data.get("iniciales", "")}, st)],
                 [Paragraph("Date of Daily Check", _PIE),
                  Paragraph(_esc(dmy(data.get("fecha"))) + " · " + _esc(data.get("hora", "")), _PIE)]],
                colWidths=[W * 0.5, W * 0.5])
    pie.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.6, colors.black),
                             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                             ("TOPPADDING", (0, 0), (-1, -1), 5),
                             ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                             ("LEFTPADDING", (0, 0), (-1, -1), 6)]))
    el += [pie]
    doc.build(el)
    return buf.getvalue()
