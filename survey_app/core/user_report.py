"""
Informe del CLIENTE — documento con formato de presentación.

Diseño: portada a sangre en azul COPEX, separadores de sección tipo diapositiva
(número grande + título), tarjetas KPI, bloque de veredicto con semáforo, tablas
con cabecera de color y filas alternas, diagramas protagonistas, glosario en
tarjetas y página de cierre con firma. Pie con paginación "X de Y" en todas las
páginas de contenido.

NO incluye lógica interna, fórmulas ni log del optimizador (regla de confidencialidad).
"""
import io
import logging
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as _canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from core.diagrams import floor_plan_svg, shaft_iso_svg
from core.report import _svg_flowable
from core.schedule import schedule_svg, schedule_table
from core.plumb    import (plumb_svg, plumb_table, plumb_checks,
                           plumb_iso_svg, plumb_card_svg)
from core import clock
from core.i18n import d

logger = logging.getLogger(__name__)

W          = 170 * mm
C_COPEX    = colors.HexColor("#1a3a5c")
C_COPEX2   = colors.HexColor("#2e6da4")
C_LIGHT    = colors.HexColor("#e8f1fb")
C_GREEN    = colors.HexColor("#1e8449")
C_RED      = colors.HexColor("#c0392b")
C_ORANGE   = colors.HexColor("#c07800")
C_WHITE    = colors.white
C_ZEBRA    = colors.HexColor("#f4f7fb")
C_MUTED    = colors.HexColor("#7fa8d4")

_LOGO = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "icon-512.png")


def numero_informe() -> str:
    """Nº de informe automático, único y ordenable: INF-AAAAMMDD-HHMM."""
    return clock.now().strftime("INF-%Y%m%d-%H%M")


def _styles():
    s = getSampleStyleSheet()
    def add(name, **kw):
        if name not in s:
            s.add(ParagraphStyle(name, **kw))
    add("UTitle",  fontSize=26, textColor=C_WHITE, alignment=TA_LEFT, fontName="Helvetica-Bold", leading=28)
    add("USub",    fontSize=11, textColor=colors.HexColor("#b0c8e8"), alignment=TA_LEFT, fontName="Helvetica")
    add("USec",    fontSize=13, textColor=C_WHITE, alignment=TA_LEFT, fontName="Helvetica-Bold", spaceBefore=4, spaceAfter=2)
    add("USecNum", fontSize=26, textColor=C_COPEX2, alignment=TA_CENTER, fontName="Helvetica-Bold", leading=28)
    add("USecSub", fontSize=8.5, textColor=colors.HexColor("#b0c8e8"), alignment=TA_LEFT, fontName="Helvetica")
    add("UBody",   fontSize=10.5, textColor=colors.black, alignment=TA_LEFT, fontName="Helvetica", leading=15, spaceAfter=4)
    add("UInfo",   fontSize=9.5, textColor=colors.black, alignment=TA_LEFT, fontName="Helvetica", leading=13)
    add("UCell",   fontSize=9, textColor=colors.black, alignment=TA_CENTER, fontName="Helvetica")
    add("USmall",  fontSize=7.5, textColor=colors.grey, alignment=TA_CENTER, fontName="Helvetica")
    add("UKpiLbl", fontSize=7.5, textColor=colors.HexColor("#666666"), alignment=TA_CENTER, fontName="Helvetica")
    add("UKpiVal", fontSize=17, textColor=C_COPEX, alignment=TA_CENTER, fontName="Helvetica-Bold", leading=20)
    add("UTerm",   fontSize=9, textColor=colors.black, alignment=TA_LEFT, fontName="Helvetica", leading=12)
    return s


def _sp(n=6): return Spacer(1, n)


def _section(text, styles):
    """Separador de sección tipo diapositiva: número grande + título sobre banda azul."""
    partes = str(text).split(".", 1)
    num = partes[0].strip() if len(partes) == 2 and partes[0].strip().isdigit() else ""
    tit = partes[1].strip() if len(partes) == 2 else str(text)
    izq = Paragraph(num.zfill(2) if num else "", styles["USecNum"])
    der = Paragraph(tit, styles["USec"])
    t = Table([[izq, der]], colWidths=[16 * mm, W - 16 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_COPEX),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (0, 0), 4), ("LEFTPADDING", (1, 0), (1, 0), 6),
    ]))
    return t


def _kpi_cards(items, styles):
    """Fila de tarjetas KPI: items = [(label, valor, color_hex|None), ...]."""
    celdas, cmds = [], [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("INNERGRID", (0, 0), (-1, -1), 3, C_WHITE),
    ]
    for i, (lbl, val, col) in enumerate(items):
        celdas.append(Paragraph(
            f'<font size=7.5 color="#666666">{lbl.upper()}</font><br/>'
            f'<font size=17 color="{col or "#1a3a5c"}"><b>{val}</b></font>', styles["UCell"]))
        cmds.append(("BACKGROUND", (i, 0), (i, 0), C_LIGHT))
    t = Table([celdas], colWidths=[W / len(items)] * len(items))
    t.setStyle(TableStyle(cmds))
    return t


def _veredicto(titulo, detalle, color, styles):
    """Bloque de veredicto con barra de color a la izquierda (se lee en 5 segundos)."""
    fondo = {C_GREEN: colors.HexColor("#eaf3de"),
             C_ORANGE: colors.HexColor("#faeeda"),
             C_RED: colors.HexColor("#fcebeb")}.get(color, C_LIGHT)
    txt = Paragraph(f'<font size=12 color="{color.hexval()[2:] and "#" + color.hexval()[2:]}">'
                    f'<b>{titulo}</b></font><br/><font size=9 color="#444444">{detalle}</font>',
                    styles["UInfo"])
    t = Table([["", txt]], colWidths=[4 * mm, W - 4 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), color),
        ("BACKGROUND", (1, 0), (1, 0), fondo),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (1, 0), (1, 0), 10),
    ]))
    return t


def _callout(texto, styles, color=C_COPEX2):
    """Recuadro destacado para lo accionable (no perderlo dentro de un párrafo)."""
    t = Table([["", Paragraph(texto, styles["UInfo"])]], colWidths=[3 * mm, W - 3 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), color),
        ("BACKGROUND", (1, 0), (1, 0), C_LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (1, 0), (1, 0), 8),
    ]))
    return t


def _zebra(cmds, n_filas, desde=1):
    """Filas alternas para las tablas (en vez de rejilla gris plana)."""
    for i in range(desde, n_filas):
        if (i - desde) % 2 == 1:
            cmds.append(("BACKGROUND", (0, i), (-1, i), C_ZEBRA))
    return cmds


class _NumeradoCanvas(_canvas.Canvas):
    """Canvas que numera 'Página X de Y' (necesita 2 pasadas) y dibuja el pie."""
    meta = {"proyecto": "", "informe": ""}

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._guardadas = []

    def showPage(self):
        self._guardadas.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._guardadas)
        for i, estado in enumerate(self._guardadas, start=1):
            self.__dict__.update(estado)
            if i > 1:                      # la portada no lleva pie ni acento
                self._pie(i, total)
            super().showPage()
        super().save()

    def _pie(self, pagina, total):
        w, h = A4
        self.saveState()
        # barra de acento lateral: hilo visual del documento
        self.setFillColor(C_COPEX2)
        self.rect(0, h * 0.25, 3 * mm, h * 0.5, fill=1, stroke=0)
        # pie
        self.setStrokeColor(colors.HexColor("#dbe4f0"))
        self.setLineWidth(0.5)
        self.line(20 * mm, 12 * mm, w - 20 * mm, 12 * mm)
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#8a94a6"))
        izq = " · ".join(x for x in (self.meta.get("proyecto"), self.meta.get("informe")) if x)
        self.drawString(20 * mm, 7.5 * mm, izq[:90])
        self.drawRightString(w - 20 * mm, 7.5 * mm, d("Page {a} of {b}", a=pagina, b=total))
        self.restoreState()


def _portada(canv, doc, meta):
    """Portada a sangre: azul COPEX, logo, título y ficha del proyecto."""
    w, h = A4
    canv.saveState()
    canv.setFillColor(C_COPEX)
    canv.rect(0, 0, w, h, fill=1, stroke=0)
    canv.setFillColor(C_COPEX2)
    canv.rect(0, h - 9 * mm, w, 9 * mm, fill=1, stroke=0)

    if os.path.exists(_LOGO):
        try:
            canv.drawImage(_LOGO, 20 * mm, h - 48 * mm, width=20 * mm, height=20 * mm,
                           mask="auto", preserveAspectRatio=True)
        except Exception:
            pass

    canv.setFillColor(C_WHITE)
    canv.setFont("Helvetica-Bold", 32)
    canv.drawString(20 * mm, h - 66 * mm, "COPEX")
    canv.setFillColor(C_MUTED)
    canv.setFont("Helvetica", 9)
    canv.drawString(20 * mm, h - 72 * mm, "Elevator Survey Analyzer")

    canv.setFillColor(C_MUTED)
    canv.setFont("Helvetica", 9)
    canv.drawString(20 * mm, h - 110 * mm, d("TECHNICAL REPORT"))
    canv.setFillColor(C_WHITE)
    canv.setFont("Helvetica-Bold", 24)
    canv.drawString(20 * mm, h - 121 * mm, d("Elevator"))
    canv.drawString(20 * mm, h - 133 * mm, d("positioning"))
    canv.setFillColor(C_COPEX2)
    canv.rect(20 * mm, h - 140 * mm, 22 * mm, 1.6 * mm, fill=1, stroke=0)

    # Ficha del proyecto
    y0 = 38 * mm
    canv.setFillColor(colors.HexColor("#24476b"))
    canv.rect(16 * mm, y0, w - 32 * mm, 46 * mm, fill=1, stroke=0)
    filas = [(d("Client"), meta.get("cliente") or "—", d("Report"), meta.get("informe") or "—"),
             (d("Project"), meta.get("proyecto") or "—", d("Date"), meta.get("fecha") or "—"),
             (d("Location"), meta.get("ubicacion") or "—", d("Stops"), str(meta.get("ns") or "—"))]
    yy = y0 + 36 * mm
    for l1, v1, l2, v2 in filas:
        canv.setFont("Helvetica", 7.5); canv.setFillColor(C_MUTED)
        canv.drawString(22 * mm, yy, l1.upper())
        canv.drawString(w / 2 + 6 * mm, yy, l2.upper())
        canv.setFont("Helvetica-Bold", 10.5); canv.setFillColor(C_WHITE)
        canv.drawString(22 * mm, yy - 6 * mm, str(v1)[:38])
        canv.drawString(w / 2 + 6 * mm, yy - 6 * mm, str(v2)[:24])
        yy -= 15 * mm

    canv.setFont("Helvetica", 7.5); canv.setFillColor(C_MUTED)
    canv.drawString(20 * mm, 22 * mm, d("Prepared by: {x}", x=meta.get("ingeniero") or "—"))
    canv.drawString(20 * mm, 17 * mm, "COPEX · Elevator Survey Analyzer")
    canv.restoreState()


def _ia_text(text, styles):
    """Devuelve SIEMPRE una lista de flowables."""
    if not text or str(text).startswith("[Interpretation unavailable"):
        return [Paragraph(f"<i>{d('Interpretation not available.')}</i>", styles["UBody"])]
    parts = [p.strip() for p in str(text).split("\n") if p.strip()]
    return [Paragraph(para, styles["UBody"]) for para in parts]


def generate_user_report(project_params, calculated, optimizer_result,
                         lim_map, survey_cols, interpretation_user, schedule=None,
                         plumb=None):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=18 * mm)
    styles = _styles()
    story  = []
    p      = project_params
    ia     = interpretation_user or {}
    best   = optimizer_result.get("best") if optimizer_result else None

    fecha  = clock.now().strftime("%d/%m/%Y")
    n_inf  = numero_informe()
    meta = {
        "proyecto":  str(p.get("PROYECTO", "") or "—"),
        "cliente":   str(p.get("CLIENTE", "") or p.get("PROYECTO", "") or "—"),
        "ubicacion": str(p.get("UBICACION", "") or "—"),
        "modelo":    str(p.get("MODELO", "") or "—"),
        "ingeniero": str(p.get("INGENIERO", "") or "—"),
        "ns":        p.get("NS", "—"),
        "fecha":     fecha,
        "informe":   n_inf,
    }
    _NumeradoCanvas.meta = {"proyecto": meta["proyecto"], "informe": n_inf}

    # ── Página 1: portada (se dibuja en el canvas) ──────────
    story += [Spacer(1, 1), PageBreak()]

    # ── Veredicto: lo primero que ve el cliente ─────────────
    _off = int(best.get("total_off", 0)) if best else -1
    # ⚠️ v437: si hay cortes se decide con los DATOS (`interpretation.cortes_por_piso`),
    # no leyendo el texto que escribió la IA. Antes era
    # `"requiere cortes" in ia["cortes"]`: frágil ya —basta con que el modelo redacte
    # distinto— e imposible al pasar el informe al inglés, porque esa frase española
    # no casaría nunca y el veredicto diría «sin valores fuera de límite» en un hueco
    # que sí necesita cortarse.
    # ⚠️ El parámetro se llama `calculated` (es lo que `calculate_limits` devuelve).
    # Mi primera versión escribió `limits` y el `except` de abajo se tragó el
    # NameError dejando `_cortes = False` para siempre: solo lo delató GENERAR el PDF
    # y leer el log. Un `except` alrededor de código recién escrito esconde justo el
    # fallo que acabas de introducir (v323 · v338 · v344).
    try:
        from core.interpretation import cortes_por_piso
        _cortes = bool(cortes_por_piso(calculated or {}, best or {}))
    except Exception as e:
        logger.warning("user_report: no se pudieron calcular los cortes: %s", e)
        _cortes = False
    if best is None:
        _col, _tit = C_RED, d("No valid solution was found")
        _det = d("With the current parameters and site measurements there is no "
                 "combination that meets the limits.")
    elif _off == 0:
        _col, _tit = C_GREEN, d("The shaft is suitable for installation")
        _det = d("The proposed solution meets every limit") + (
               d(", with the cuts listed in section 3.") if _cortes
               else d(", with no values out of limit."))
    else:
        _col, _tit = C_ORANGE, d("Suitable with observations")
        _det = d("The solution leaves {n} value(s) out of limit that need attention "
                 "before or during installation.", n=_off)
    story += [_veredicto(_tit, _det, _col, styles), _sp(10)]

    # ── Ficha del proyecto (datos ampliados) ────────────────
    def _fila(l1, v1, l2, v2):
        return [Paragraph(f"<b>{l1}</b>", styles["UInfo"]), Paragraph(str(v1), styles["UInfo"]),
                Paragraph(f"<b>{l2}</b>", styles["UInfo"]), Paragraph(str(v2), styles["UInfo"])]
    it = Table([
        _fila(d("Client"), meta["cliente"], d("Report no."), n_inf),
        _fila(d("Project"), meta["proyecto"], d("Date"), fecha),
        _fila(d("Location"), meta["ubicacion"], d("Model"), meta["modelo"]),
        _fila(d("Engineer in charge"), meta["ingeniero"], d("Number of stops"), meta["ns"]),
    ], colWidths=[W * 0.24, W * 0.30, W * 0.22, W * 0.24])
    _cmds_it = [
        ("BACKGROUND", (0, 0), (-1, -1), C_LIGHT),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, C_WHITE),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]
    it.setStyle(TableStyle(_cmds_it))
    story += [it, _sp(12)]

    # ── Índice ──────────────────────────────────────────────
    _idx = [d("1. Solution summary"), d("2. Final positioning"), d("3. Cuts required"),
            d("4. Solution matrix"), d("5. Floor plan diagrams")]
    if schedule and schedule.get("activities"):
        _idx.append(d("6. Schedule and S-curve"))
    _idx += [d("7. Site implementation"), d("8. Final verification")]
    if plumb:
        _idx.append(d("9. Final plumb line layout"))
    _idx += [d("10. Scope and methodology"), d("11. Glossary"), d("12. Conclusions")]
    story += [Paragraph(f"<b>{d('Contents')}</b>", styles["UBody"]), _sp(3)]
    _ic = Table([[Paragraph(f"· {x}", styles["UInfo"])] for x in _idx], colWidths=[W])
    _ic.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story += [_ic, _sp(12)]

    # ── Resumen ejecutivo ───────────────────────────────────
    story += [_section(d("1. Solution summary"), styles), _sp(5)]
    story += _ia_text(ia.get("resumen"), styles)
    story += [_sp(10)]

    # ── Solución final (RL/FB) ──────────────────────────────
    story += [_section(d("2. Final positioning"), styles), _sp(5)]
    if best:
        rl = best.get("rl", 0)
        fb = best.get("fb_applied", best.get("fb", 0))
        off = best.get("total_off", 0)
        story += [_kpi_cards([
            (d("Lateral shift (RL)"), f"{rl:+.1f} mm", None),
            (d("Front shift (FB)"), f"{fb:+.1f} mm", None),
            (d("Values out of limit"), f"{off}", "#1e8449" if off == 0 else "#c0392b"),
            (d("Stops"), str(meta["ns"]), None),
        ], styles), _sp(8)]
        story += [_callout(
            d("<b>Main action:</b> shift the car block <b>{lat} mm</b> to the {dir_lat} "
              "and <b>{frt} mm</b> to the {dir_frt}, relative to the design position.",
              lat=f"{abs(rl):.1f}", frt=f"{abs(fb):.1f}",
              dir_lat=d("right") if rl >= 0 else d("left"),
              dir_frt=d("rear") if fb >= 0 else d("front")), styles), _sp(8)]
    else:
        story += [Paragraph(d("No valid solution was found."), styles["UBody"]), _sp(8)]

    story += [Paragraph(f"<b>{d('Shifts to carry out:')}</b>", styles["UBody"])]
    story += list(_ia_text(ia.get("desplazamientos"), styles))
    story += [_sp(10)]

    # ── Cortes ──────────────────────────────────────────────
    story += [_section(d("3. Cuts required"), styles), _sp(5)]
    story += list(_ia_text(ia.get("cortes"), styles))
    story += [_sp(10)]

    # ── Matriz de la solución ───────────────────────────────
    if best and best.get("matrix"):
        story += [_section(d("4. Solution matrix (by floor)"), styles), _sp(5)]
        header = [Paragraph(f"<b>{d('Floor')}</b>", styles["UCell"])] + \
                 [Paragraph(f"<b>{c}</b>", styles["UCell"]) for c in survey_cols]
        rows = [header]
        cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), C_COPEX2),
            ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
            ("LINEBELOW", (0, 0), (-1, 0), 0.8, C_COPEX),
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
        t.setStyle(TableStyle(_zebra(cmds, len(rows))))
        story += [t, _sp(4),
                  Paragraph(d("Cells in red: values needing attention (clearance below the minimum, "
                              "or an opening that requires cutting)."), styles["USmall"]), _sp(10)]

    # ── Diagramas de planta por piso ────────────────────────
    if best and best.get("matrix"):
        story += [PageBreak(), _section(d("5. Shaft diagrams"), styles), _sp(4),
                  Paragraph(d("Floor plans drawn to real proportion, with every dimension checked "
                              "against its limit. Dimensions in <b>red</b> are out of limit; the "
                              "rest comply. Where a clearance is very tight, an enlarged "
                              "<b>Detail</b> of that corner is added."),
                            styles["UInfo"]), _sp(6)]
        mat = best["matrix"]
        n   = len(mat)
        rpt_lim = {c: lim_map[c] for c in ["WR", "FR", "OR", "WL", "FL", "OL"]}
        c_in = p.get("CTRL_IN_FRAME", False); c_side = p.get("CTRL_SIDE")

        _iso = _svg_flowable(shaft_iso_svg(p, calculated, best, n, rpt_lim,
                                           proyecto=meta["proyecto"]), W * 0.52)
        if _iso is not None:
            story += [_iso, _sp(10), PageBreak()]

        drawn = 0
        for i, mrow in enumerate(mat):
            svg  = floor_plan_svg(p, calculated, mrow, i, rpt_lim, c_in, c_side,
                                  is_last=(i == n - 1),
                                  rl=best.get("rl", 0),
                                  fb=best.get("fb_applied", best.get("fb", 0)),
                                  n_floors=n, proyecto=meta["proyecto"])
            draw = _svg_flowable(svg, W * 0.66)
            if draw is not None:
                story += [draw, _sp(6)]
                drawn += 1
                if drawn % 2 == 0 and i < n - 1:
                    story += [PageBreak()]

    # ── Cronograma y curva S ────────────────────────────────
    if schedule and schedule.get("activities"):
        story += [PageBreak(), _section(d("6. Project schedule and S-curve"), styles), _sp(4),
                  Paragraph(d("Start: <b>{ini}</b>  ·  Estimated finish: <b>{fin}</b>  ·  "
                              "Total duration: <b>{n} days</b>.",
                              ini=schedule["start_date"].strftime("%d/%m/%Y"),
                              fin=schedule["fecha_fin"].strftime("%d/%m/%Y"),
                              n=schedule["total_dias"]), styles["UBody"]), _sp(4)]
        sdraw = _svg_flowable(schedule_svg(schedule), W)
        if sdraw is not None:
            story += [sdraw, _sp(6)]
        # tabla de actividades
        srows = schedule_table(schedule)
        thead = [Paragraph(f"<b>{h}</b>", styles["UCell"]) for h in
                 [d("Activity"), d("Start"), d("Finish"), d("Days"), d("Weight %")]]
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
        st.setStyle(TableStyle(_zebra([
            ("BACKGROUND", (0, 0), (-1, 0), C_COPEX2),
            ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
            ("LINEBELOW", (0, 0), (-1, 0), 0.8, C_COPEX),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ], len(trows))))
        story += [st, _sp(10)]

    # ── Implementación y verificación ───────────────────────
    story += [PageBreak(), _section(d("7. Site implementation"), styles), _sp(5)]
    story += list(_ia_text(ia.get("implementacion"), styles))
    story += [_sp(10)]
    story += [_section(d("8. Final verification"), styles), _sp(5)]
    story += list(_ia_text(ia.get("verificacion"), styles))

    # ── Esquema de plomado definitivo ───────────────────────
    if plumb:
        _pd = plumb.get("displacement") or {}
        story += [PageBreak(), _section(d("9. Final plumb line layout"), styles), _sp(4),
                  Paragraph(d("Final position of the plumb lines including the shifts from the "
                              "analysis. The assembly (plumb lines, theoretical walls and "
                              "template) moves as one block; the real walls stay fixed. The "
                              "zero axis is the left real wall."), styles["UBody"]), _sp(4)]
        if _pd.get("origen") == "survey":
            story += [Paragraph(
                d("Shift applied: lateral = <b>{a} mm</b> · front = <b>{b} mm</b>.",
                  a=f"{_pd.get('rl', 0):.1f}", b=f"{_pd.get('fb', 0):.1f}"), styles["UBody"]), _sp(4)]
        pdraw = _svg_flowable(plumb_svg(plumb, proyecto=meta["proyecto"]), W)
        if pdraw is not None:
            story += [pdraw, _sp(6)]
        piso = _svg_flowable(plumb_iso_svg(plumb, proyecto=meta["proyecto"]), W * 0.50)
        if piso is not None:
            story += [piso, _sp(8)]
        pfic = _svg_flowable(plumb_card_svg(plumb, proyecto=meta["proyecto"]), W * 0.62)
        if pfic is not None:
            story += [_callout(d("<b>Set-out card</b> — the values to measure with a tape on "
                                 "site. The closing check must add up to BSR."), styles),
                      _sp(4), pfic, _sp(6)]
        phead = [Paragraph(f"<b>{h}</b>", styles["UCell"]) for h in
                 [d("Line"), d("Initial X (mm)"), d("Final X (mm)"), d("Shifted")]]
        ptrows = [phead]
        for r in plumb_table(plumb):
            ptrows.append([Paragraph(str(r["Línea"]), styles["UInfo"]),
                           Paragraph(str(r["X inicial (mm)"]), styles["UCell"]),
                           Paragraph(str(r["X final (mm)"]), styles["UCell"]),
                           Paragraph(str(r["Desplazada"]), styles["UCell"])])
        ptab = Table(ptrows, colWidths=[W * 0.40, W * 0.20, W * 0.20, W * 0.20])
        ptab.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("BACKGROUND", (0, 0), (-1, 0), C_COPEX2),
            ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story += [ptab, _sp(6)]

        # Distancias de verificación en campo (plomo ↔ pared real)
        story += [Paragraph(f"<b>{d('Site verification — plumb line ↔ real wall distances')}</b>",
                            styles["UBody"]), _sp(2)]
        chead = [Paragraph(f"<b>{h}</b>", styles["UCell"]) for h in [d("Measurement"), d("Distance (mm)")]]
        ctrows = [chead]
        for r in plumb_checks(plumb):
            ctrows.append([Paragraph(str(r["Medida"]), styles["UInfo"]),
                           Paragraph(str(r["Distancia (mm)"]), styles["UCell"])])
        ctab = Table(ctrows, colWidths=[W * 0.72, W * 0.28])
        ctab.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("BACKGROUND", (0, 0), (-1, 0), C_COPEX2),
            ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story += [ctab, _sp(10)]

    # ── 10. Alcance y metodología ───────────────────────────
    story += [PageBreak(), _section(d("10. Scope and methodology"), styles), _sp(5)]
    story += [Paragraph(
        d("This report determines the <b>optimum position of the car block</b> (rails and "
          "guides) within the existing shaft, based on the measurements taken on site level "
          "by level and on the parameters of the manufacturer's drawing."), styles["UBody"])]
    story += [Paragraph(
        d("<b>What was measured:</b> at every stop we record the side clearances (left and "
          "right), the distance from the front wall to the rail axis, and the space available "
          "on each side of the landing door opening."), styles["UBody"])]
    story += [Paragraph(
        d("<b>How it is assessed:</b> every measurement is compared against its allowable "
          "limit. We look for the combination of lateral and front shift that minimises the "
          "breaches, respecting the physical constraints of the shaft and, where it applies, "
          "the limiting wall and the controller built into the frame."), styles["UBody"]), _sp(4)]
    story += [_callout(
        d("<b>Limitations and validity.</b> The conclusions are based on the measurements "
          "supplied and on the drawing parameters current at the date of this report. Changes "
          "to the shaft or to the equipment, or measurements taken to different criteria, may "
          "alter the result. All values are in millimetres and must be verified on site before "
          "final installation."),
        styles, color=C_ORANGE), _sp(10)]

    # ── 11. Glosario (tarjetas, no una tabla gris) ──────────
    story += [_section(d("11. Glossary"), styles), _sp(5)]
    _terms = [
        ("RL", d("Lateral shift of the car block relative to the design.")),
        ("FB", d("Front shift (towards the rear wall or towards the door).")),
        ("WR / WL", d("Clearance between the car block and the right / left wall.")),
        ("FR / FL", d("Distance from the front wall to the right / left rail axis.")),
        ("OR / OL", d("Space to the right / left in the landing door opening.")),
        ("BS / BSR", d("Shaft width per drawing / width actually measured on site.")),
        (d("Plumb line"), d("Vertical reference line used to align the rails over the "
                            "full height.")),
        (d("Cut"), d("Material to be removed when the opening exceeds the allowable limit.")),
    ]
    _cards, _fila_t = [], []
    # ⚠️ La variable del bucle NO puede llamarse `d`: taparía a la función `d()` del
    # motor de idiomas en TODA la función (Python la marca local en el ámbito entero),
    # y las etiquetas de arriba reventarían con UnboundLocalError. Lo cazó generar el
    # PDF de verdad — ni compilar ni importar lo ven.
    for i, (_term, _def) in enumerate(_terms):
        _fila_t.append(Paragraph(f"<b>{_term}</b><br/><font size=8 color='#555555'>{_def}</font>",
                                 styles["UTerm"]))
        if len(_fila_t) == 2:
            _cards.append(_fila_t); _fila_t = []
    if _fila_t:
        _fila_t.append(Paragraph("", styles["UTerm"])); _cards.append(_fila_t)
    _gt = Table(_cards, colWidths=[W / 2, W / 2])
    _gt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_LIGHT),
        ("INNERGRID", (0, 0), (-1, -1), 3, C_WHITE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story += [_gt, _sp(12)]

    # ── 12. Conclusiones y firma (cierra como abrió) ────────
    story += [PageBreak(), _section(d("12. Conclusions"), styles), _sp(5)]
    story += [_veredicto(_tit, _det, _col, styles), _sp(8)]
    if best:
        _concl = [
            d("The proposed positioning is RL {rl} mm and FB {fb} mm.",
              rl=f"{best.get('rl', 0):+.1f}",
              fb=f"{best.get('fb_applied', best.get('fb', 0)):+.1f}"),
            d("The floor plans show, level by level, how the car fits in the shaft."),
        ]
        if _off:
            _concl.append(d("{n} value(s) remain out of limit: review the cells marked in the "
                            "matrix before fixing the brackets.", n=_off))
        else:
            _concl.append(d("No values remain out of limit with the solution adopted."))
        _concl.append(d("Verify the plumb line distances shown on site before final installation."))
        for _c in _concl:
            story += [Paragraph(f"· {_c}", styles["UBody"])]
    story += [_sp(16)]

    _firma = Table([
        [Paragraph(f"<font size=8 color='#666666'>{d('PREPARED BY')}</font><br/><br/><br/>"
                   "_______________________________<br/>"
                   f"<b>{meta['ingeniero']}</b><br/>"
                   f"<font size=8 color='#666666'>{d('Engineer in charge')} · COPEX</font>",
                   styles["UInfo"]),
         Paragraph(f"<font size=8 color='#666666'>{d('RECEIVED BY')}</font><br/><br/><br/>"
                   "_______________________________<br/>"
                   f"<b>{meta['cliente']}</b><br/>"
                   f"<font size=8 color='#666666'>{d('Name, position and date')}</font>",
                   styles["UInfo"])],
    ], colWidths=[W / 2, W / 2])
    _firma.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story += [_firma, _sp(14)]
    story += [HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey), _sp(4),
              Paragraph(d("COPEX · Elevator Survey Analyzer · {n} · Generated on {f}",
                          n=n_inf, f=fecha), styles["USmall"])]

    # ⚠️ El argumento NO se llama `d` (era `lambda c, d:`): aquí sería inofensivo —la
    # lambda tiene su propio ámbito— pero está a una edición de repetir el fallo del
    # glosario, y el guardián prohíbe el nombre en todo el módulo por eso mismo.
    doc.build(story, onFirstPage=lambda c, _doc: _portada(c, _doc, meta),
              canvasmaker=_NumeradoCanvas)
    buf.seek(0)
    return buf.getvalue()
