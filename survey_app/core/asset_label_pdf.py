"""Etiqueta imprimible de un activo: QR + nombre + ID + datos, para pegar en el equipo."""
import io as _io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.i18n import d          # v436: la etiqueta va SIEMPRE en el idioma base

C_BRAND = colors.HexColor("#1a3a5c")
C_MUTE = colors.HexColor("#7a8699")


def generate_label_pdf(activo: dict, qr_png: bytes, grupo_nombre: str = "") -> bytes:
    ss = getSampleStyleSheet()
    nom = ParagraphStyle("nom", parent=ss["Normal"], fontSize=20, leading=23,
                         fontName="Helvetica-Bold", textColor=C_BRAND)
    idst = ParagraphStyle("idst", parent=ss["Normal"], fontSize=13, leading=16,
                          fontName="Helvetica-Bold")
    sub = ParagraphStyle("sub", parent=ss["Normal"], fontSize=10, leading=14, textColor=C_MUTE)

    buf = _io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm,
                            title=d("Label {id}", id=activo.get("ID", "")))
    story = []

    qr = Image(_io.BytesIO(qr_png), width=48 * mm, height=48 * mm)
    lineas = [Paragraph(str(activo.get("Name", "")), nom),
              Paragraph(str(activo.get("ID", "")), idst)]
    # ⚠️ Las ramas van por la CLAVE, nunca por el texto de la etiqueta: al traducir
    # «Marca/Modelo» a «Make/Model» la comparación por texto dejó de cumplirse y esa
    # línea desapareció de la etiqueta, sin ningún error. Es el modo de fallo típico
    # de una traducción, y lo cometí en el primer módulo que toqué.
    for lbl, key in ((d("Category"), "Category"), (d("Make/Model"), None), (d("Serial"), "Serial")):
        if key is None:
            v = " ".join(x for x in (str(activo.get("Brand", "")).strip(),
                                     str(activo.get("Model", "")).strip()) if x)
        else:
            v = str(activo.get(key, "")).strip()
        if v:
            lineas.append(Paragraph(f"{lbl}: {v}", sub))
    if grupo_nombre:
        lineas.append(Spacer(1, 4))
        lineas.append(Paragraph(str(grupo_nombre), sub))

    card = Table([[qr, lineas]], colWidths=[52 * mm, 122 * mm])
    card.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 1.2, C_BRAND),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12)]))
    story += [card]
    doc.build(story)
    return buf.getvalue()
