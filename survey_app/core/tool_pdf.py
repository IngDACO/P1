"""
PDF de resultado para las herramientas de cálculo.

Un único generador para Plomadas, Corte de rieles, Corte de buffers y Belting:
así las cuatro salen con la misma cara (y la misma que el paquete de obra del
Survey) en vez de que cada una invente la suya.

Estructura: cabecera + ficha del proyecto + dibujos + tabla de resultados +
notas. Los dibujos entran como SVG vía `report._svg_flowable` (svglib), así que
valen los mismos SVG que ya se muestran en pantalla.
"""
import io as _io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle)

from core.report import _svg_flowable

C_COPEX = colors.HexColor("#1a3a5c")
C_LIGHT = colors.HexColor("#e8f1fb")
C_ZEBRA = colors.HexColor("#f4f7fb")


def _estilos():
    s = getSampleStyleSheet()
    def add(n, **kw):
        if n not in s:
            s.add(ParagraphStyle(n, **kw))
    add("TTit",  fontSize=18, textColor=C_COPEX, fontName="Helvetica-Bold",
        alignment=TA_LEFT, leading=21)
    add("TSub",  fontSize=9, textColor=colors.HexColor("#7a8699"),
        fontName="Helvetica", leading=12)
    add("TCell", fontSize=8.5, textColor=colors.black, fontName="Helvetica")
    add("THead", fontSize=8.5, textColor=colors.white, fontName="Helvetica-Bold")
    add("TNota", fontSize=8, textColor=colors.HexColor("#7a8699"),
        fontName="Helvetica", leading=11)
    return s


def _tabla(filas, ss, W):
    """filas = lista de dicts (misma forma que las tablas de la app)."""
    if not filas:
        return None
    cols = list(filas[0].keys())
    data = [[Paragraph(str(c), ss["THead"]) for c in cols]]
    for f in filas:
        data.append([Paragraph(str(f.get(c, "")), ss["TCell"]) for c in cols])
    t = Table(data, colWidths=[W / len(cols)] * len(cols), repeatRows=1)
    cmds = [("BACKGROUND", (0, 0), (-1, 0), C_COPEX),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#c3ccd8"))]
    for i in range(1, len(data)):
        if i % 2 == 0:
            cmds.append(("BACKGROUND", (0, i), (-1, i), C_ZEBRA))
    t.setStyle(TableStyle(cmds))
    return t


def tool_pdf(titulo: str, meta: dict = None, svgs: list = None,
             tablas: list = None, notas: list = None,
             ancho_svg: float = 0.92) -> bytes | None:
    """Arma el PDF de una herramienta.

    svgs   : lista de strings SVG (o (svg, ancho_relativo))
    tablas : lista de (subtitulo, filas)
    notas  : lista de strings al pie
    """
    meta = meta or {}
    ss = _estilos()
    buf = _io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm,
                            rightMargin=15 * mm, topMargin=14 * mm,
                            bottomMargin=14 * mm, title=titulo)
    W = doc.width

    story = [Paragraph(titulo, ss["TTit"]), Spacer(1, 2),
             Paragraph("COPEX · " + datetime.now().strftime("%d/%m/%Y %H:%M"),
                       ss["TSub"]), Spacer(1, 10)]

    ficha = [(k, v) for k, v in meta.items() if str(v or "").strip()]
    if ficha:
        t = Table([[Paragraph(f"<b>{k}</b>", ss["TCell"]),
                    Paragraph(str(v), ss["TCell"])] for k, v in ficha],
                  colWidths=[W * 0.26, W * 0.74])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), C_LIGHT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.white),
        ]))
        story += [t, Spacer(1, 12)]

    for item in (svgs or []):
        svg, rel = item if isinstance(item, (tuple, list)) else (item, ancho_svg)
        d = _svg_flowable(svg, W * rel)
        if d is not None:
            story += [d, Spacer(1, 10)]

    for sub, filas in (tablas or []):
        if sub:
            story.append(Paragraph(f"<b>{sub}</b>", ss["TCell"]))
            story.append(Spacer(1, 4))
        t = _tabla(filas, ss, W)
        if t is not None:
            story += [t, Spacer(1, 10)]

    for n in (notas or []):
        story.append(Paragraph(n, ss["TNota"]))

    try:
        doc.build(story)
    except Exception:
        return None
    return buf.getvalue()
