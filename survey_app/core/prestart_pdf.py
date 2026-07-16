"""
PDF del Pre-Start diario. Marca = nombre del grupo (empresa). Reproduce el formato:
encabezado, datos, secciones 1-5 con checks YES/NO/N-A, asistentes y notas.
"""
import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)

from core.prestart import CHECKS_S1, CHECKS_S3
from core import maps

C_DARK  = colors.HexColor("#1a3a5c")
C_MED   = colors.HexColor("#2e6da4")
C_LIGHT = colors.HexColor("#e8f1fb")
C_GREEN = colors.HexColor("#1e8449")
C_RED   = colors.HexColor("#c0392b")
C_GREY  = colors.HexColor("#888888")
W = 170 * mm


def _styles():
    ss = getSampleStyleSheet()
    def add(name, **kw):
        ss.add(ParagraphStyle(name, **kw))
    add("PSTitle",  fontSize=20, textColor=colors.white, alignment=TA_LEFT, fontName="Helvetica-Bold")
    add("PSSub",    fontSize=11, textColor=colors.HexColor("#b0c8e8"), alignment=TA_LEFT)
    add("PSSec",    fontSize=11, textColor=colors.white, fontName="Helvetica-Bold")
    add("PSInfo",   fontSize=9.5, textColor=colors.black, leading=13)
    add("PSBody",   fontSize=9.5, textColor=colors.black, leading=13)
    add("PSQ",      fontSize=9,   textColor=colors.black, leading=12)
    add("PSSmall",  fontSize=7.5, textColor=colors.grey, alignment=TA_CENTER)
    return ss


def _sp(n=6):
    return Spacer(1, n)


def _ans_color(v):
    v = str(v).upper()
    if v == "YES":
        return C_GREEN
    if v == "NO":
        return C_RED
    return C_GREY


def _section(text, st):
    t = Table([[Paragraph(text, st["PSSec"])]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_MED),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def _checks_table(items, answers, st):
    rows = []
    for key, label in items:
        v = str(answers.get(key, "") or "—")
        rows.append([Paragraph(label, st["PSQ"]),
                     Paragraph(f"<b>{v}</b>", st["PSQ"])])
    t = Table(rows, colWidths=[W * 0.82, W * 0.18])
    style = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c8d8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
    ]
    for i, (key, _l) in enumerate(items):
        style.append(("TEXTCOLOR", (1, i), (1, i), _ans_color(answers.get(key, ""))))
    t.setStyle(TableStyle(style))
    return t


def generate_prestart_pdf(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm)
    st = _styles()
    story = []
    grupo = str(data.get("grupo", "") or "COPEX")

    # ── Cabecera (marca = grupo) ──
    hdr = Table([[Paragraph(grupo, st["PSTitle"])],
                 [Paragraph("Daily Pre-Start", st["PSSub"])]], colWidths=[W])
    hdr.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_DARK),
        ("LEFTPADDING", (0, 0), (-1, -1), 16), ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (0, 0), 14), ("BOTTOMPADDING", (0, 0), (0, 0), 0),
        ("TOPPADDING", (0, 1), (0, 1), 0), ("BOTTOMPADDING", (0, 1), (0, 1), 14),
    ]))
    story += [hdr, _sp(10)]

    # ── Datos ──
    f = data.get("fecha")
    fecha_s = f.strftime("%d/%m/%Y") if hasattr(f, "strftime") else str(f)
    loc = str(data.get("location", "") or "")
    loc_url = maps.maps_url(loc)
    loc_para = Paragraph(f'<a href="{loc_url}" color="#2e6da4">{loc}</a>' if loc_url else "—", st["PSInfo"])
    info = Table([
        [Paragraph("<b>Proyecto</b>", st["PSInfo"]), Paragraph(str(data.get("proyecto_nombre", "—")), st["PSInfo"]),
         Paragraph("<b>Fecha</b>", st["PSInfo"]), Paragraph(fecha_s, st["PSInfo"])],
        [Paragraph("<b>Location</b>", st["PSInfo"]), loc_para,
         Paragraph("<b>Hora</b>", st["PSInfo"]), Paragraph(str(data.get("hora", "—") or "—"), st["PSInfo"])],
        [Paragraph("<b>Facilitated by</b>", st["PSInfo"]), Paragraph(str(data.get("facilitador", "—") or "—"), st["PSInfo"]),
         Paragraph("", st["PSInfo"]), Paragraph("", st["PSInfo"])],
    ], colWidths=[W * 0.20, W * 0.34, W * 0.14, W * 0.32])
    info.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c8d8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [info, _sp(12)]

    # ── 1. Planned work activities ──
    story += [_section("1. Planned work activities today", st), _sp(5),
              _checks_table(CHECKS_S1, data.get("s1", {}), st)]
    if data.get("activities_notes"):
        story += [_sp(4), Paragraph("<b>Notas:</b> " + str(data["activities_notes"]), st["PSBody"])]
    story += [_sp(10)]

    # ── 2. Issues / hazard / near miss ──
    story += [_section("2. Issues, hazard / near miss reports", st), _sp(5)]
    nm = str(data.get("near_miss", "NO")).upper()
    nm_hex = {"YES": "#c0392b", "NO": "#1e8449"}.get(nm, "#888888")  # YES = riesgo (rojo)
    story += [Paragraph(f"Near Miss/Hazard Report submitted: "
                        f"<font color='{nm_hex}'><b>{nm}</b></font>", st["PSBody"])]
    if data.get("near_miss_desc"):
        story += [_sp(3), Paragraph(str(data["near_miss_desc"]), st["PSBody"])]
    story += [_sp(10)]

    # ── 3. Shaft protection ──
    story += [_section("3. Shaft Protection & other daily checks", st), _sp(5),
              _checks_table(CHECKS_S3, data.get("s3", {}), st), _sp(10)]

    # ── 4. General notes ──
    story += [_section("4. General Notes", st), _sp(5),
              Paragraph(str(data.get("general_notes", "") or "—"), st["PSBody"]), _sp(10)]

    # ── 5. Attendees ──
    story += [_section("5. Attendees", st), _sp(5)]
    att = data.get("attendees", [])
    rows = [[Paragraph("<b>Print Name</b>", st["PSQ"]), Paragraph("<b>Initial</b>", st["PSQ"])]]
    for a in att:
        nm2 = str(a.get("name", "")).strip()
        ini = str(a.get("initial", "")).strip()
        if nm2 or ini:
            rows.append([Paragraph(nm2 or "—", st["PSQ"]), Paragraph(ini or "—", st["PSQ"])])
    if len(rows) == 1:
        rows.append([Paragraph("—", st["PSQ"]), Paragraph("—", st["PSQ"])])
    at = Table(rows, colWidths=[W * 0.70, W * 0.30])
    at.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c8d8f0")),
        ("BACKGROUND", (0, 0), (-1, 0), C_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [at, _sp(12)]

    story += [HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#c8d8f0")), _sp(4),
              Paragraph(f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} · {grupo}", st["PSSmall"])]

    doc.build(story)
    return buf.getvalue()
