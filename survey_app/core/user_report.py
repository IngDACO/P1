"""
Informe del USUARIO (cliente) — versión limpia y profesional.
Se centra en la solución final de posicionamiento, con branding COPEX,
gráficos de planta, tabla de solución e interpretación IA orientada a
la implementación. NO incluye lógica interna, fórmulas ni log del optimizador.
"""
import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from core.diagrams import floor_plan_svg
from core.report import _svg_flowable
from core.schedule import schedule_svg, schedule_table

W          = 170 * mm
C_COPEX    = colors.HexColor("#1a3a5c")
C_COPEX2   = colors.HexColor("#2e6da4")
C_LIGHT    = colors.HexColor("#e8f1fb")
C_GREEN    = colors.HexColor("#1e8449")
C_RED      = colors.HexColor("#c0392b")
C_ORANGE   = colors.HexColor("#c07800")
C_WHITE    = colors.white


def _styles():
    s = getSampleStyleSheet()
    def add(name, **kw):
        if name not in s:
            s.add(ParagraphStyle(name, **kw))
    add("UTitle",  fontSize=26, textColor=C_WHITE, alignment=TA_LEFT, fontName="Helvetica-Bold", leading=28)
    add("USub",    fontSize=11, textColor=colors.HexColor("#b0c8e8"), alignment=TA_LEFT, fontName="Helvetica")
    add("USec",    fontSize=13, textColor=C_WHITE, alignment=TA_LEFT, fontName="Helvetica-Bold", spaceBefore=4, spaceAfter=2)
    add("UBody",   fontSize=10.5, textColor=colors.black, alignment=TA_LEFT, fontName="Helvetica", leading=15, spaceAfter=4)
    add("UInfo",   fontSize=9.5, textColor=colors.black, alignment=TA_LEFT, fontName="Helvetica", leading=13)
    add("UCell",   fontSize=9, textColor=colors.black, alignment=TA_CENTER, fontName="Helvetica")
    add("USmall",  fontSize=7.5, textColor=colors.grey, alignment=TA_CENTER, fontName="Helvetica")
    return s


def _sp(n=6): return Spacer(1, n)


def _section(text, styles):
    t = Table([[Paragraph(text, styles["USec"])]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_COPEX2),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def _ia_text(text, styles):
    """Devuelve SIEMPRE una lista de flowables."""
    if not text or str(text).startswith("[Interpretación no disponible"):
        return [Paragraph("<i>Interpretación no disponible.</i>", styles["UBody"])]
    parts = [p.strip() for p in str(text).split("\n") if p.strip()]
    return [Paragraph(para, styles["UBody"]) for para in parts]


def generate_user_report(project_params, calculated, optimizer_result,
                         lim_map, survey_cols, interpretation_user, schedule=None):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm, topMargin=16 * mm, bottomMargin=16 * mm)
    styles = _styles()
    story  = []
    p      = project_params
    ia     = interpretation_user or {}
    best   = optimizer_result.get("best") if optimizer_result else None

    # ── Cabecera COPEX ──────────────────────────────────────
    hdr = Table([[
        Paragraph("COPEX", styles["UTitle"]),
    ], [
        Paragraph("Informe de posicionamiento de elevador", styles["USub"]),
    ]], colWidths=[W])
    hdr.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_COPEX),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (0, 0), 14),
        ("BOTTOMPADDING", (0, 0), (0, 0), 0),
        ("TOPPADDING", (0, 1), (0, 1), 0),
        ("BOTTOMPADDING", (0, 1), (0, 1), 14),
    ]))
    story += [hdr, _sp(10)]

    # ── Datos del proyecto ──────────────────────────────────
    fecha = datetime.now().strftime("%d/%m/%Y  %H:%M")
    info_rows = [
        [Paragraph("<b>Proyecto / Cliente</b>", styles["UInfo"]), Paragraph(str(p.get("PROYECTO", "") or "—"), styles["UInfo"]),
         Paragraph("<b>Fecha</b>", styles["UInfo"]), Paragraph(fecha, styles["UInfo"])],
        [Paragraph("<b>Ingeniero responsable</b>", styles["UInfo"]), Paragraph(str(p.get("INGENIERO", "") or "—"), styles["UInfo"]),
         Paragraph("<b>Número de paradas</b>", styles["UInfo"]), Paragraph(str(p.get("NS", "—")), styles["UInfo"])],
    ]
    it = Table(info_rows, colWidths=[W * 0.24, W * 0.30, W * 0.22, W * 0.24])
    it.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c8d8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [it, _sp(12)]

    # ── Resumen ejecutivo ───────────────────────────────────
    story += [_section("1. Resumen de la solución", styles), _sp(5)]
    story += _ia_text(ia.get("resumen"), styles)
    story += [_sp(10)]

    # ── Solución final (RL/FB) ──────────────────────────────
    story += [_section("2. Posicionamiento final", styles), _sp(5)]
    if best:
        rl = best.get("rl", 0)
        fb = best.get("fb_applied", best.get("fb", 0))
        off = best.get("total_off", 0)
        cards = Table([[
            Paragraph(f"<font size=8 color='#666'>DESPLAZAMIENTO LATERAL (RL)</font><br/>"
                      f"<font size=18 color='#1a3a5c'><b>{rl:+.1f} mm</b></font>", styles["UCell"]),
            Paragraph(f"<font size=8 color='#666'>DESPLAZAMIENTO FRONTAL (FB)</font><br/>"
                      f"<font size=18 color='#1a3a5c'><b>{fb:+.1f} mm</b></font>", styles["UCell"]),
            Paragraph(f"<font size=8 color='#666'>VALORES FUERA DE LÍMITE</font><br/>"
                      f"<font size=18 color='{'#1e8449' if off == 0 else '#c0392b'}'><b>{off}</b></font>", styles["UCell"]),
        ]], colWidths=[W / 3] * 3)
        cards.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), C_LIGHT),
            ("BOX", (0, 0), (-1, -1), 0.5, C_COPEX2),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, C_WHITE),
            ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story += [cards, _sp(8)]
    else:
        story += [Paragraph("No se encontró una solución válida.", styles["UBody"]), _sp(8)]

    story += [Paragraph("<b>Desplazamientos a realizar:</b>", styles["UBody"])]
    story += list(_ia_text(ia.get("desplazamientos"), styles))
    story += [_sp(10)]

    # ── Cortes ──────────────────────────────────────────────
    story += [_section("3. Cortes necesarios", styles), _sp(5)]
    story += list(_ia_text(ia.get("cortes"), styles))
    story += [_sp(10)]

    # ── Matriz de la solución ───────────────────────────────
    if best and best.get("matrix"):
        story += [_section("4. Matriz de la solución (por piso)", styles), _sp(5)]
        header = [Paragraph("<b>Piso</b>", styles["UCell"])] + \
                 [Paragraph(f"<b>{c}</b>", styles["UCell"]) for c in survey_cols]
        rows = [header]
        cmds = [
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("BACKGROUND", (0, 0), (-1, 0), C_COPEX2),
            ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        for i, mrow in enumerate(best["matrix"]):
            cells = [Paragraph(str(i + 1), styles["UCell"])]
            for ci, c in enumerate(survey_cols, start=1):
                v = mrow.get(c, 0)
                cells.append(Paragraph(f"{v:.1f}", styles["UCell"]))
                lim = lim_map.get(c)
                if lim is not None:
                    bad = (v > lim) if c in ("OR", "OL") else (v < lim)
                    if bad:
                        cmds.append(("BACKGROUND", (ci, i + 1), (ci, i + 1), colors.HexColor("#f9d6d1")))
            rows.append(cells)
        col_w = [16 * mm] + [(W - 16 * mm) / len(survey_cols)] * len(survey_cols)
        t = Table(rows, colWidths=col_w)
        t.setStyle(TableStyle(cmds))
        story += [t, _sp(4),
                  Paragraph("Celdas en rojo: valores que requieren atención (holgura por debajo del "
                            "mínimo, o apertura que requiere corte).", styles["USmall"]), _sp(10)]

    # ── Diagramas de planta por piso ────────────────────────
    if best and best.get("matrix"):
        story += [PageBreak(), _section("5. Diagramas de planta por piso", styles), _sp(4),
                  Paragraph("Vista superior del encaje de la cabina en el hueco, piso a piso. "
                            "Verde = correcto, naranja = al límite, rojo = requiere ajuste/corte.",
                            styles["UInfo"]), _sp(6)]
        mat = best["matrix"]
        n   = len(mat)
        rpt_lim = {c: lim_map[c] for c in ["WR", "FR", "OR", "WL", "FL", "OL"]}
        c_in = p.get("CTRL_IN_FRAME", False); c_side = p.get("CTRL_SIDE")
        drawn = 0
        for i, mrow in enumerate(mat):
            svg  = floor_plan_svg(p, calculated, mrow, i, rpt_lim, c_in, c_side, is_last=(i == n - 1))
            draw = _svg_flowable(svg, W * 0.66)
            if draw is not None:
                story += [draw, _sp(6)]
                drawn += 1
                if drawn % 2 == 0 and i < n - 1:
                    story += [PageBreak()]

    # ── Cronograma y curva S ────────────────────────────────
    if schedule and schedule.get("activities"):
        story += [PageBreak(), _section("6. Cronograma y curva S del proyecto", styles), _sp(4),
                  Paragraph(f"Inicio: <b>{schedule['start_date'].strftime('%d/%m/%Y')}</b>  ·  "
                            f"Fin estimado: <b>{schedule['fecha_fin'].strftime('%d/%m/%Y')}</b>  ·  "
                            f"Duración total: <b>{schedule['total_dias']} días</b>.", styles["UBody"]), _sp(4)]
        sdraw = _svg_flowable(schedule_svg(schedule), W)
        if sdraw is not None:
            story += [sdraw, _sp(6)]
        # tabla de actividades
        srows = schedule_table(schedule)
        thead = [Paragraph(f"<b>{h}</b>", styles["UCell"]) for h in
                 ["Actividad", "Inicio", "Fin", "Días", "Peso %"]]
        trows = [thead]
        for r in srows:
            trows.append([
                Paragraph(str(r["Actividad"]), styles["UInfo"]),
                Paragraph(r["Inicio"], styles["UCell"]),
                Paragraph(r["Fin"], styles["UCell"]),
                Paragraph(str(r["Duración (d)"]), styles["UCell"]),
                Paragraph(str(r["Peso (%)"]), styles["UCell"]),
            ])
        st = Table(trows, colWidths=[W * 0.40, W * 0.16, W * 0.16, W * 0.12, W * 0.16])
        st.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("BACKGROUND", (0, 0), (-1, 0), C_COPEX2),
            ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story += [st, _sp(10)]

    # ── Implementación y verificación ───────────────────────
    story += [PageBreak(), _section("7. Implementación en obra", styles), _sp(5)]
    story += list(_ia_text(ia.get("implementacion"), styles))
    story += [_sp(10)]
    story += [_section("8. Verificación final", styles), _sp(5)]
    story += list(_ia_text(ia.get("verificacion"), styles))

    # ── Pie ─────────────────────────────────────────────────
    story += [_sp(14), HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey), _sp(4),
              Paragraph("COPEX — Informe de posicionamiento de elevador", styles["USmall"]),
              Paragraph(f"Generado el {fecha}", styles["USmall"])]

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()
