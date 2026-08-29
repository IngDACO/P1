"""
PDF del Pre-Start diario. Calca el formato CI Liftworx "Daily Pre-Start" (v172):
formulario blanco y negro con bordes, bandas grises por sección y recuadros de
notas. Marca = nombre del grupo (empresa). Los datos que captura la app se
reorganizan como el template: la Sección 1 es solo notas, y los 4 checks de
permisos/toolbox/subcontratistas/pre-operacionales van a la Sección 3 en la
sub-tabla "Circle one".
"""
import io
import logging

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from core.i18n import d          # v436: documento, idioma base
from core.prestart import CHECKS_S1, CHECKS_S3

# ⚠️ v383: `_celda_firma` registra en el log si una firma viene ilegible. Sin esta
# línea sería un NameError ESCONDIDO dentro de un `except` — el mismo fallo latente
# que apareció en `finance.py` en v370, que solo se ve ejercitando esa rama.
logger = logging.getLogger(__name__)
from core import maps
from core import clock

C_BLACK = colors.black
C_BAND  = colors.HexColor("#d9d9d9")     # banda gris de sección (como el template)
C_LINE  = colors.HexColor("#555555")     # bordes de las cajitas de respuesta
W = 180 * mm


def _esc(s) -> str:
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _styles():
    ss = getSampleStyleSheet()

    def add(name, **kw):
        ss.add(ParagraphStyle(name, **kw))
    add("PSBrand",  fontSize=16, textColor=C_BLACK, fontName="Helvetica-Bold", leading=18)
    add("PSTitle2", fontSize=12, textColor=C_BLACK, fontName="Helvetica-Bold", leading=14)
    add("PSProj",   fontSize=9,  textColor=colors.HexColor("#555555"), leading=12)
    add("PSInfo",   fontSize=9,  textColor=C_BLACK, leading=12)
    add("PSSec",    fontSize=10, textColor=C_BLACK, leading=13)
    add("PSBody",   fontSize=9,  textColor=C_BLACK, leading=13)
    add("PSQ",      fontSize=8.5, textColor=C_BLACK, leading=11)
    add("PSCirc",   fontSize=8,  textColor=colors.HexColor("#555555"),
        fontName="Helvetica-Bold", alignment=TA_CENTER)
    add("PSAns",    fontSize=8.5, textColor=colors.HexColor("#333333"),
        alignment=TA_CENTER, leading=10)
    add("PSAnsSel", fontSize=8.5, textColor=colors.white, fontName="Helvetica-Bold",
        alignment=TA_CENTER, leading=10)
    add("PSSmall",  fontSize=7.5, textColor=colors.grey, alignment=TA_CENTER)
    return ss


def _sp(n=6):
    return Spacer(1, n)


def _ans(options, selected, st):
    """Cajitas de respuesta: la opción marcada va con fondo negro (form 'rellenado')."""
    sel = str(selected or "").strip().upper()
    row = [Paragraph(o, st["PSAnsSel"] if o.upper() == sel else st["PSAns"]) for o in options]
    t = Table([row], colWidths=[10.5 * mm] * len(options))
    stl = [("GRID", (0, 0), (-1, -1), 0.5, C_LINE),
           ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
           ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)]
    for i, o in enumerate(options):
        if o.upper() == sel:
            stl.append(("BACKGROUND", (i, 0), (i, 0), C_BLACK))
    t.setStyle(TableStyle(stl))
    return t


def _celda_firma(a, st):
    """La firma DIBUJADA del asistente (v383), o sus iniciales si no la hay.

    ⚠️ Degrada en vez de romper: si el lienzo no estuvo disponible (o la imagen
    viene corrupta), la celda cae a las iniciales tecleadas y el Pre-Start se
    genera igual. Un PDF de seguridad no se puede quedar sin emitir porque una
    firma no se pudo pintar.
    """
    sig = a.get("sig")
    if sig:
        try:
            from reportlab.platypus import Image as RLImage
            # Ajustada a la columna de firma (16,3% del ancho útil), con margen.
            return RLImage(io.BytesIO(sig), width=25 * mm, height=8 * mm,
                           kind="proportional")
        except Exception as e:
            logger.warning("prestart_pdf: firma ilegible (%s); se usan las iniciales", e)
    return Paragraph(_esc(a.get("initial", "")) or "&nbsp;", st["PSQ"])


def _band(title, st, sub=""):
    inner = f"<b>{_esc(title)}</b>"
    if sub:
        inner += f"<br/><i>{_esc(sub)}</i>"
    t = Table([[Paragraph(inner, st["PSSec"])]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_BAND),
        ("BOX", (0, 0), (-1, -1), 0.6, C_BLACK),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def _notebox(text, st, holgura=26):
    """Recuadro con borde para las notas (como los espacios en blanco del template)."""
    p = Paragraph(_esc(text).replace("\n", "<br/>") or "&nbsp;", st["PSBody"])
    t = Table([[p]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, C_BLACK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5 + holgura),   # da altura al recuadro
    ]))
    return t


def generate_anexo_firmas_pdf(info: dict) -> bytes:
    """Hoja de ANEXO con las firmas de quien se incorporó a la obra más tarde (v403).

    ⚠️ Se ANEXA, no se reescribe, y no es una preferencia de estilo: **las firmas
    originales solo viven dentro del PDF ya emitido** — la hoja guarda nombre e
    iniciales, nunca la imagen (v383) —, así que regenerar el documento entero
    BORRARÍA la firma de quien sí estuvo en la charla de las 7:00. Y aunque se
    pudieran recuperar, un documento de seguridad firmado no se reescribe: se le
    añade una hoja, con su hora, igual que circula la hoja en papel.

    `info` = {marca, ps_id, fecha, proyecto, location,
              firmas: [{name, initial, sig, hora}]}
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=12 * mm, bottomMargin=12 * mm,
                            title=d("Signature addendum {id}", id=info.get("ps_id", "")))
    st = _styles()
    el = [Paragraph(_esc(info.get("marca", "")), st["PSBrand"]), _sp(2),
          _band(d("SIGNATURE ADDENDUM — people who joined after the briefing"), st,
                d("These people clocked on site after this Pre-Start was issued and "
                  "signed on arrival.")),
          _sp(4)]

    ref = [[Paragraph("<b>Pre-Start</b><br/>" + _esc(info.get("ps_id", "")), st["PSInfo"]),
            Paragraph(f"<b>{d('Date')}</b><br/>" + _esc(info.get("fecha", "")), st["PSInfo"]),
            Paragraph("<b>Proyecto</b><br/>" + _esc(info.get("proyecto", "")), st["PSInfo"]),
            Paragraph("<b>Location</b><br/>" + _esc(info.get("location", "")), st["PSInfo"])]]
    t = Table(ref, colWidths=[W * 0.18, W * 0.18, W * 0.32, W * 0.32])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, C_BLACK),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 5),
                           ("TOPPADDING", (0, 0), (-1, -1), 4),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    el += [t, _sp(8)]

    filas = [[Paragraph("<b>Print name</b>", st["PSQ"]),
              Paragraph("<b>Initial</b>", st["PSQ"]),
              Paragraph("<b>Signature</b>", st["PSQ"]),
              Paragraph(f"<b>{d('Time')}</b>", st["PSQ"])]]
    for a in (info.get("firmas") or []):
        filas.append([Paragraph(_esc(a.get("name", "")), st["PSBody"]),
                      Paragraph(_esc(a.get("initial", "")), st["PSQ"]),
                      _celda_firma(a, st),
                      Paragraph(_esc(a.get("hora", "")), st["PSQ"])])
    # ⚠️ Mismo reparto que la tabla de asistentes del documento original: la columna
    # de firma se lleva el 16,3% que v383 tuvo que reequilibrar, porque con el 9%
    # de antes hasta el encabezado se partía por la mitad.
    tf = Table(filas, colWidths=[W * 0.42, W * 0.12, W * 0.30, W * 0.16])
    tf.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, C_BLACK),
                            ("BACKGROUND", (0, 0), (-1, 0), C_BAND),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 5),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    el += [tf, _sp(10),
           Paragraph(d("This addendum does not modify the original Pre-Start: it is "
                       "attached to it. Each signature keeps the time it was taken."),
                     st["PSSmall"])]
    doc.build(el)
    return buf.getvalue()


def generate_prestart_pdf(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=14 * mm, bottomMargin=12 * mm)
    st = _styles()
    story = []
    grupo = str(data.get("grupo", "") or "COPEX")
    proyecto = str(data.get("proyecto_nombre", "") or "")

    # ── Cabecera (marca = grupo, sin banda de color) ──
    story += [Paragraph(_esc(grupo), st["PSBrand"]),
              Paragraph("Daily Pre-Start", st["PSTitle2"])]
    if proyecto:
        story += [Paragraph(d("Project: ") + _esc(proyecto), st["PSProj"])]
    story += [_sp(8)]

    # ── Fila: Date · Time · Location · Facilitated by (bordeada, como el template) ──
    f = data.get("fecha")
    fecha_s = f.strftime("%d/%m/%Y") if hasattr(f, "strftime") else str(f)
    loc = str(data.get("location", "") or "")
    loc_url = maps.maps_url(loc)
    loc_html = (f'<a href="{loc_url}" color="#1a3a5c">{_esc(loc)}</a>'
                if (loc and loc_url) else (_esc(loc) or "—"))
    info = Table([[
        Paragraph(f"<b>Date:</b> {fecha_s}", st["PSInfo"]),
        Paragraph(f"<b>Time:</b> {_esc(data.get('hora', '')) or '—'}", st["PSInfo"]),
        Paragraph(f"<b>Location:</b> {loc_html}", st["PSInfo"]),
        Paragraph(f"<b>Facilitated by:</b> {_esc(data.get('facilitador', '')) or '—'}", st["PSInfo"]),
    ]], colWidths=[W * 0.20, W * 0.16, W * 0.37, W * 0.27])
    info.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, C_BLACK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [info, _sp(8)]

    # ── 1. Planned work activities today (solo notas, como el template) ──
    story += [_band("1. Planned work activities today", st,
                    "Discuss today's planned activities and review the SWMS for these "
                    "activities. Note key points below."),
              _notebox(data.get("activities_notes", ""), st, holgura=34), _sp(8)]

    # ── 2. Discuss any issues, hazard / near miss reports ──
    story += [_band("2. Discuss any issues, hazard / near miss reports", st,
                    "Note the key points/actions discussed below."),
              _notebox(data.get("near_miss_desc", ""), st, holgura=26)]
    nm_row = Table([[Paragraph("Near Miss/Hazard Report submitted", st["PSQ"]),
                     _ans(["NO", "YES"], data.get("near_miss", ""), st)]],
                   colWidths=[W * 0.70, W * 0.30])
    nm_row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (1, 0), (1, 0), "LEFT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (0, 0), 2),
    ]))
    story += [nm_row, _sp(8)]

    # ── 3. Shaft Protection & other daily checks ──
    story += [_band("3. Shaft Protection & other daily checks", st)]
    s3 = data.get("s3", {})
    srows = [[Paragraph(label, st["PSQ"]), _ans(["NO", "YES", "N/A"], s3.get(key, ""), st)]
             for key, label in CHECKS_S3]
    stab = Table(srows, colWidths=[W * 0.62, W * 0.38])
    stab.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, C_BLACK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (1, 0), (1, -1), "LEFT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [stab]

    # Sub-tabla "Circle one" con los 4 checks (permisos/toolbox/subcontratistas/preop)
    s1 = data.get("s1", {})

    def _qa(idx):
        key, label = CHECKS_S1[idx]
        return Paragraph(label, st["PSQ"]), _ans(["YES", "NO", "N/A"], s1.get(key, ""), st)
    q0, a0 = _qa(0); q1, a1 = _qa(1); q2, a2 = _qa(2); q3, a3 = _qa(3)
    circ = Table([
        [Paragraph("", st["PSQ"]), Paragraph("Circle one", st["PSCirc"]),
         Paragraph("", st["PSQ"]), Paragraph("Circle one", st["PSCirc"])],
        [q0, a0, q1, a1],
        [q2, a2, q3, a3],
    ], colWidths=[W * 0.30, W * 0.20, W * 0.30, W * 0.20])
    circ.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, C_BLACK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, -1), "CENTER"), ("ALIGN", (3, 0), (3, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [circ, _sp(8)]

    # ── 4. General Notes ──
    story += [_band("4. General Notes", st),
              _notebox(data.get("general_notes", ""), st, holgura=40), _sp(8)]

    # ── 5. Attendees (3 pares Print Name · Initial, como el template) ──
    story += [_band("5. Attendees", st)]
    att = [a for a in data.get("attendees", [])
           if str(a.get("name", "")).strip() or str(a.get("initial", "")).strip()]
    hdr = []
    for _ in range(3):
        hdr += [Paragraph("<b>Print Name</b>", st["PSQ"]),
                Paragraph("<b>Signature</b>", st["PSQ"])]
    rows = [hdr]
    grupos = [att[i:i + 3] for i in range(0, len(att), 3)] or [[]]
    if not att:
        grupos = [[], []]                              # 2 filas en blanco si no hay asistentes
    for g in grupos:
        row = []
        for j in range(3):
            a = g[j] if j < len(g) else {}
            row += [Paragraph(_esc(a.get("name", "")) or "&nbsp;", st["PSQ"]),
                    _celda_firma(a, st)]
        rows.append(row)
    # ⚠️ v383: la columna de firma medía 9% del ancho —dimensionada para DOS
    # INICIALES— y una firma dibujada no cabe: el propio encabezado se partía como
    # «Signatur / e». Se reequilibra dándole sitio al trazo. Lo delató extraer el
    # texto del PDF generado; a ojo en el código no se ve.
    attab = Table(rows, colWidths=[W * 0.17, W * 0.163] * 3)
    attab.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, C_BLACK),
        ("BACKGROUND", (0, 0), (-1, 0), C_BAND),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [attab, _sp(10)]

    story += [Paragraph(d("Generated on {f} · {g}", f=clock.now().strftime("%d/%m/%Y %H:%M"),
                          g=_esc(grupo)),
                        st["PSSmall"])]

    doc.build(story)
    return buf.getvalue()
