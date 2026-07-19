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
import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as _canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from core.diagrams import floor_plan_svg
from core.report import _svg_flowable
from core.schedule import schedule_svg, schedule_table
from core.plumb    import plumb_svg, plumb_table, plumb_checks

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
    return datetime.now().strftime("INF-%Y%m%d-%H%M")


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
        self.drawRightString(w - 20 * mm, 7.5 * mm, f"Página {pagina} de {total}")
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
    canv.drawString(20 * mm, h - 110 * mm, "INFORME TÉCNICO")
    canv.setFillColor(C_WHITE)
    canv.setFont("Helvetica-Bold", 24)
    canv.drawString(20 * mm, h - 121 * mm, "Posicionamiento")
    canv.drawString(20 * mm, h - 133 * mm, "de elevador")
    canv.setFillColor(C_COPEX2)
    canv.rect(20 * mm, h - 140 * mm, 22 * mm, 1.6 * mm, fill=1, stroke=0)

    # Ficha del proyecto
    y0 = 38 * mm
    canv.setFillColor(colors.HexColor("#24476b"))
    canv.rect(16 * mm, y0, w - 32 * mm, 46 * mm, fill=1, stroke=0)
    filas = [("Cliente", meta.get("cliente") or "—", "Informe", meta.get("informe") or "—"),
             ("Proyecto", meta.get("proyecto") or "—", "Fecha", meta.get("fecha") or "—"),
             ("Ubicación", meta.get("ubicacion") or "—", "Paradas", str(meta.get("ns") or "—"))]
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
    canv.drawString(20 * mm, 22 * mm, f"Preparado por: {meta.get('ingeniero') or '—'}")
    canv.drawString(20 * mm, 17 * mm, "COPEX · Elevator Survey Analyzer")
    canv.restoreState()


def _ia_text(text, styles):
    """Devuelve SIEMPRE una lista de flowables."""
    if not text or str(text).startswith("[Interpretación no disponible"):
        return [Paragraph("<i>Interpretación no disponible.</i>", styles["UBody"])]
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

    fecha  = datetime.now().strftime("%d/%m/%Y")
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
    _cortes = "requiere cortes" in str(ia.get("cortes", "")).lower() or "cortar" in str(ia.get("cortes", "")).lower()
    if best is None:
        _col, _tit = C_RED, "No se encontró una solución válida"
        _det = "Con los parámetros y medidas actuales no hay una combinación que cumpla los límites."
    elif _off == 0:
        _col, _tit = C_GREEN, "El hueco es apto para la instalación"
        _det = "La solución propuesta cumple todos los límites" + (
               ", con los cortes indicados en la sección 3." if _cortes else ", sin valores fuera de límite.")
    else:
        _col, _tit = C_ORANGE, "Apto con observaciones"
        _det = (f"La solución deja {_off} valor(es) fuera de límite que requieren atención "
                "antes o durante el montaje.")
    story += [_veredicto(_tit, _det, _col, styles), _sp(10)]

    # ── Ficha del proyecto (datos ampliados) ────────────────
    def _fila(l1, v1, l2, v2):
        return [Paragraph(f"<b>{l1}</b>", styles["UInfo"]), Paragraph(str(v1), styles["UInfo"]),
                Paragraph(f"<b>{l2}</b>", styles["UInfo"]), Paragraph(str(v2), styles["UInfo"])]
    it = Table([
        _fila("Cliente", meta["cliente"], "Nº de informe", n_inf),
        _fila("Proyecto", meta["proyecto"], "Fecha", fecha),
        _fila("Ubicación", meta["ubicacion"], "Modelo", meta["modelo"]),
        _fila("Ingeniero responsable", meta["ingeniero"], "Número de paradas", meta["ns"]),
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
    _idx = ["1. Resumen de la solución", "2. Posicionamiento final", "3. Cortes necesarios",
            "4. Matriz de la solución", "5. Diagramas de planta por piso"]
    if schedule and schedule.get("activities"):
        _idx.append("6. Cronograma y curva S")
    _idx += ["7. Implementación en obra", "8. Verificación final"]
    if plumb:
        _idx.append("9. Esquema de plomado definitivo")
    _idx += ["10. Alcance y metodología", "11. Glosario de términos", "12. Conclusiones"]
    story += [Paragraph("<b>Contenido</b>", styles["UBody"]), _sp(3)]
    _ic = Table([[Paragraph(f"· {x}", styles["UInfo"])] for x in _idx], colWidths=[W])
    _ic.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story += [_ic, _sp(12)]

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
        story += [_kpi_cards([
            ("Desplazamiento lateral (RL)", f"{rl:+.1f} mm", None),
            ("Desplazamiento frontal (FB)", f"{fb:+.1f} mm", None),
            ("Valores fuera de límite", f"{off}", "#1e8449" if off == 0 else "#c0392b"),
            ("Paradas", str(meta["ns"]), None),
        ], styles), _sp(8)]
        story += [_callout(
            f"<b>Acción principal:</b> desplazar el bloque de cabina <b>{abs(rl):.1f} mm</b> hacia "
            f"{'la derecha' if rl >= 0 else 'la izquierda'} y <b>{abs(fb):.1f} mm</b> hacia "
            f"{'atrás' if fb >= 0 else 'adelante'} respecto a la posición de diseño.", styles), _sp(8)]
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
        st.setStyle(TableStyle(_zebra([
            ("BACKGROUND", (0, 0), (-1, 0), C_COPEX2),
            ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
            ("LINEBELOW", (0, 0), (-1, 0), 0.8, C_COPEX),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ], len(trows))))
        story += [st, _sp(10)]

    # ── Implementación y verificación ───────────────────────
    story += [PageBreak(), _section("7. Implementación en obra", styles), _sp(5)]
    story += list(_ia_text(ia.get("implementacion"), styles))
    story += [_sp(10)]
    story += [_section("8. Verificación final", styles), _sp(5)]
    story += list(_ia_text(ia.get("verificacion"), styles))

    # ── Esquema de plomado definitivo ───────────────────────
    if plumb:
        _pd = plumb.get("displacement") or {}
        story += [PageBreak(), _section("9. Esquema de plomado definitivo", styles), _sp(4),
                  Paragraph("Ubicación final de las líneas de plomada con los desplazamientos del "
                            "análisis. El conjunto (plomos, paredes teóricas y template) se desplaza "
                            "en bloque; las paredes reales quedan fijas. El eje cero es la pared real "
                            "izquierda.", styles["UBody"]), _sp(4)]
        if _pd.get("origen") == "survey":
            story += [Paragraph(
                f"Desplazamiento aplicado: lateral = <b>{_pd.get('rl', 0):.1f} mm</b> · "
                f"frontal = <b>{_pd.get('fb', 0):.1f} mm</b>.", styles["UBody"]), _sp(4)]
        pdraw = _svg_flowable(plumb_svg(plumb), W)
        if pdraw is not None:
            story += [pdraw, _sp(6)]
        phead = [Paragraph(f"<b>{h}</b>", styles["UCell"]) for h in
                 ["Línea", "X inicial (mm)", "X final (mm)", "Desplazada"]]
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
        story += [Paragraph("<b>Verificación en campo — distancias plomo ↔ pared real</b>",
                            styles["UBody"]), _sp(2)]
        chead = [Paragraph(f"<b>{h}</b>", styles["UCell"]) for h in ["Medida", "Distancia (mm)"]]
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
    story += [PageBreak(), _section("10. Alcance y metodología", styles), _sp(5)]
    story += [Paragraph(
        "Este informe determina la <b>posición óptima del bloque de cabina</b> (rieles y guías) dentro "
        "del hueco existente, a partir de las medidas tomadas en obra nivel a nivel y de los parámetros "
        "del plano del fabricante.", styles["UBody"])]
    story += [Paragraph(
        "<b>Qué se midió:</b> en cada parada se registran las holguras laterales (izquierda y derecha), "
        "la distancia de la pared frontal al eje de rieles y el espacio disponible a cada lado de la "
        "apertura de puerta de rellano.", styles["UBody"])]
    story += [Paragraph(
        "<b>Cómo se evalúa:</b> cada medida se compara contra su límite admisible. Se busca la "
        "combinación de desplazamiento lateral y frontal que minimiza los incumplimientos, respetando "
        "las restricciones físicas del hueco y, cuando aplica, la pared limitante y el controlador "
        "integrado en el marco.", styles["UBody"]), _sp(4)]
    story += [_callout(
        "<b>Limitaciones y validez.</b> Las conclusiones se basan en las medidas aportadas y en los "
        "parámetros del plano vigentes a la fecha del informe. Cambios en el hueco, en el equipo o "
        "medidas tomadas con criterios distintos pueden alterar el resultado. Los valores están "
        "expresados en milímetros y deben verificarse en obra antes del montaje definitivo.",
        styles, color=C_ORANGE), _sp(10)]

    # ── 11. Glosario (tarjetas, no una tabla gris) ──────────
    story += [_section("11. Glosario de términos", styles), _sp(5)]
    _terms = [
        ("RL", "Desplazamiento lateral del bloque de cabina respecto al diseño."),
        ("FB", "Desplazamiento frontal (hacia el fondo o hacia la puerta)."),
        ("WR / WL", "Holgura entre el bloque de cabina y la pared derecha / izquierda."),
        ("FR / FL", "Distancia de la pared frontal al eje del riel derecho / izquierdo."),
        ("OR / OL", "Espacio a la derecha / izquierda en la apertura de puerta de rellano."),
        ("BS / BSR", "Ancho del hueco según plano / ancho realmente medido en obra."),
        ("Plomada", "Línea vertical de referencia para alinear los rieles en toda la altura."),
        ("Corte", "Material a retirar cuando la apertura supera el límite admisible."),
    ]
    _cards, _fila_t = [], []
    for i, (t, d) in enumerate(_terms):
        _fila_t.append(Paragraph(f"<b>{t}</b><br/><font size=8 color='#555555'>{d}</font>",
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
    story += [PageBreak(), _section("12. Conclusiones", styles), _sp(5)]
    story += [_veredicto(_tit, _det, _col, styles), _sp(8)]
    if best:
        _concl = [
            f"El posicionamiento propuesto es RL {best.get('rl', 0):+.1f} mm y "
            f"FB {best.get('fb_applied', best.get('fb', 0)):+.1f} mm.",
            "Los diagramas de planta muestran, piso a piso, cómo queda el encaje de la cabina.",
        ]
        if _off:
            _concl.append(f"Quedan {_off} valor(es) fuera de límite: revisar las celdas marcadas en "
                          "la matriz antes de fijar los brackets.")
        else:
            _concl.append("No quedan valores fuera de límite con la solución adoptada.")
        _concl.append("Verificar en obra las distancias de plomada indicadas antes del montaje definitivo.")
        for _c in _concl:
            story += [Paragraph(f"· {_c}", styles["UBody"])]
    story += [_sp(16)]

    _firma = Table([
        [Paragraph("<font size=8 color='#666666'>PREPARADO POR</font><br/><br/><br/>"
                   "_______________________________<br/>"
                   f"<b>{meta['ingeniero']}</b><br/>"
                   "<font size=8 color='#666666'>Ingeniero responsable · COPEX</font>", styles["UInfo"]),
         Paragraph("<font size=8 color='#666666'>RECIBIDO POR</font><br/><br/><br/>"
                   "_______________________________<br/>"
                   f"<b>{meta['cliente']}</b><br/>"
                   "<font size=8 color='#666666'>Nombre, cargo y fecha</font>", styles["UInfo"])],
    ], colWidths=[W / 2, W / 2])
    _firma.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story += [_firma, _sp(14)]
    story += [HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey), _sp(4),
              Paragraph(f"COPEX · Elevator Survey Analyzer · {n_inf} · Generado el {fecha}",
                        styles["USmall"])]

    doc.build(story, onFirstPage=lambda c, d: _portada(c, d, meta),
              canvasmaker=_NumeradoCanvas)
    buf.seek(0)
    return buf.getvalue()
