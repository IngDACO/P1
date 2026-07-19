"""
Paquete de obra — PDF autocontenido para quien va a terreno.

Tras v119-v123 existian todas las piezas (planta tecnica, isometrica del hueco,
planta de plomado, isometrica de plomos, ficha de replanteo) pero sueltas: habia
que ir seccion por seccion descargandolas. Esto las junta en UN documento.

NO es el informe del cliente ni el de administracion: no lleva interpretaciones,
ni log, ni formulas. Solo lo que se necesita para replantear y montar:
  1. Cabecera del proyecto
  2. Isometrica del hueco (contexto espacial)
  3. Plantas por piso, a escala, con sus cotas
  4. Plomado: planta + isometrica + FICHA DE REPLANTEO (los numeros a medir)
"""
import io as _io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak)

from core.report import _svg_flowable
from core.diagrams import floor_plan_svg, shaft_iso_svg, floors_with_issues
from core.plumb import plumb_svg, plumb_iso_svg, plumb_card_svg

C_COPEX = colors.HexColor("#1a3a5c")
C_LIGHT = colors.HexColor("#e8f1fb")


def _estilos():
    s = getSampleStyleSheet()
    def add(n, **kw):
        if n not in s:
            s.add(ParagraphStyle(n, **kw))
    add("FTit",  fontSize=19, textColor=C_COPEX, fontName="Helvetica-Bold",
        alignment=TA_LEFT, leading=22)
    add("FSec",  fontSize=12, textColor=colors.white, fontName="Helvetica-Bold",
        alignment=TA_LEFT)
    add("FInfo", fontSize=9.5, textColor=colors.black, fontName="Helvetica", leading=13)
    add("FNota", fontSize=8, textColor=colors.HexColor("#7a8699"), fontName="Helvetica",
        leading=11)
    return s


def _banda(txt, ss, W):
    t = Table([[Paragraph(txt, ss["FSec"])]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_COPEX),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def field_pack_pdf(params: dict, limits: dict, solution: dict, lim_map: dict,
                   plumb: dict = None, ctrl_in_frame=False, ctrl_side=None,
                   meta: dict = None, solo_incidencias=False) -> bytes | None:
    """Genera el paquete de obra. Devuelve bytes del PDF o None si no hay solucion."""
    if not solution or not solution.get("matrix"):
        return None
    meta = meta or {}
    ss = _estilos()
    buf = _io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=14 * mm, bottomMargin=14 * mm,
                            title="Paquete de obra")
    W = doc.width
    proyecto = str(meta.get("proyecto") or "")
    mat = solution["matrix"]
    n   = len(mat)

    story = [Paragraph("Paquete de obra", ss["FTit"]), Spacer(1, 2),
             Paragraph("Documento de replanteo y montaje — no sustituye al informe técnico.",
                       ss["FNota"]), Spacer(1, 10)]

    ficha = [("Proyecto", proyecto or "—"),
             ("Cliente", str(meta.get("cliente") or "—")),
             ("Ubicación", str(meta.get("ubicacion") or "—")),
             ("Paradas", str(n)),
             ("Emitido", datetime.now().strftime("%d/%m/%Y %H:%M"))]
    t = Table([[Paragraph(f"<b>{k}</b>", ss["FInfo"]), Paragraph(v, ss["FInfo"])]
               for k, v in ficha], colWidths=[W * 0.26, W * 0.74])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), C_LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.white),
    ]))
    story += [t, Spacer(1, 14)]

    # ── 1. Isométrica del hueco ────────────────────────────
    iso = _svg_flowable(shaft_iso_svg(params, limits, solution, n, lim_map,
                                      proyecto=proyecto), W * 0.52)
    if iso is not None:
        story += [_banda("1 · El hueco", ss, W), Spacer(1, 8), iso, Spacer(1, 6),
                  Paragraph("Planta a escala real; la altura va comprimida. "
                            "Los niveles marcados en rojo tienen valores fuera de límite.",
                            ss["FNota"]), PageBreak()]

    # ── 2. Plantas por piso ────────────────────────────────
    pisos = list(range(n))
    if solo_incidencias:
        pisos = floors_with_issues(solution, lim_map) or pisos
    story += [_banda("2 · Plantas por piso", ss, W), Spacer(1, 6),
              Paragraph("Cotas en mm. Las cotas en <b>rojo</b> están fuera de límite. "
                        "Cuando una holgura es muy ajustada se añade un detalle ampliado.",
                        ss["FNota"]), Spacer(1, 8)]
    puestos = 0
    for i in pisos:
        if not (0 <= i < n):
            continue
        d = _svg_flowable(
            floor_plan_svg(params, limits, mat[i], i, lim_map, ctrl_in_frame, ctrl_side,
                           is_last=(i == n - 1),
                           rl=solution.get("rl", 0),
                           fb=solution.get("fb_applied", solution.get("fb", 0)),
                           n_floors=n, proyecto=proyecto), W * 0.74)
        if d is None:
            continue
        story += [d, Spacer(1, 8)]
        puestos += 1
        if puestos % 2 == 0 and i != pisos[-1]:
            story.append(PageBreak())

    # ── 3. Plomado ─────────────────────────────────────────
    if plumb:
        story.append(PageBreak())
        story += [_banda("3 · Replanteo de plomadas", ss, W), Spacer(1, 8)]
        pl = _svg_flowable(plumb_svg(plumb, proyecto=proyecto), W)
        if pl is not None:
            story += [pl, Spacer(1, 10)]
        pi = _svg_flowable(plumb_iso_svg(plumb, proyecto=proyecto), W * 0.48)
        if pi is not None:
            story += [pi, Spacer(1, 10)]
        pc = _svg_flowable(plumb_card_svg(plumb, proyecto=proyecto), W * 0.66)
        if pc is not None:
            story += [PageBreak(), _banda("4 · Ficha de replanteo", ss, W), Spacer(1, 8),
                      Paragraph("Los valores a medir con cinta en obra. La comprobación "
                                "de cierre debe dar BSR; si no cierra, hay error de medida.",
                                ss["FNota"]), Spacer(1, 8), pc]

    try:
        doc.build(story)
    except Exception:
        return None
    return buf.getvalue()
