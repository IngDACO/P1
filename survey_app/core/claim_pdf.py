"""PDF de reclamación de avance y de liberación de retención (v510).

El documento que se le MANDA al cliente. Hasta v509 la app calculaba la reclamación
—contrato, variaciones, avance, bruto, retención, neto— y el contratista la volvía a
armar en Excel para enviarla: media función, que como argumento de venta es peor que
ninguna, porque promete y no entrega.

Una página A4, mismo lenguaje visual que `invoice_pdf` (reportlab platypus): emisor con
identidad fiscal + título, datos del documento, «Claim to», el valor del contrato con
sus variaciones APROBADAS **detalladas una a una**, y el cálculo de arriba abajo hasta
el neto a pagar.

⚠️ Detallar las variaciones no es adorno. Una reclamación que solo dice «valor de
contrato ajustado: 128.400» le pide al cliente que pague contra un número que no puede
comprobar; enumerarlas es lo que convierte el documento en algo discutible línea a línea
en vez de una cifra a tomar o dejar.

⚠️ El texto va en INGLÉS y pasa por `i18n.d()`, que ignora el idioma de la interfaz
(v436): el documento sale de la empresa y su idioma no puede depender de cómo tenga la
pantalla quien pulsa el botón.

⚠️ **Este PDF no invoca ninguna ley y es a propósito.** Una reclamación bajo el marco de
*Security of Payment* tiene que declararlo, pero el texto exacto y sus consecuencias
cambian por estado (NSW, VIC y QLD no piden lo mismo) y declararlo mal tiene efectos
legales reales. Así que el módulo **no** lo escribe solo: quien sepa lo pone en la nota,
que viaja íntegra al documento. Es el criterio de v506 —la app no certifica cumplimiento
de nada— aplicado aquí.
"""
import io as _io
import logging

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core import i18n
from core.i18n import d
from core.num import num as _num

C_BRAND = colors.HexColor("#1a3a5c")
C_LIGHT = colors.HexColor("#e8f1fb")
C_MUTE = colors.HexColor("#7a8699")

logger = logging.getLogger(__name__)


def _money(v) -> str:
    return f"${_num(v):,.2f}"


def _es_liberacion(rec: dict) -> bool:
    """⚠️ Se pregunta a `claims`, no se compara la cadena aquí: la clase de documento
    la define UN sitio (regla v361). Si el módulo no está, se trata como reclamación de
    avance, que es lo que son todas las filas anteriores a v510."""
    try:
        from core import claims
        return claims.es_liberacion(rec)
    except Exception as e:
        logger.warning("claim_pdf: no se pudo resolver la clase de documento: %s", e)
        return False


def generate_claim_pdf(rec: dict, variaciones: list = None, cliente: dict = None,
                       grupo_nombre: str = "", proyecto: dict = None,
                       retenido: dict = None) -> bytes:
    """Los bytes del PDF de esta reclamación (o liberación).

    `rec` es la fila YA GUARDADA, no un cálculo: un documento cuenta lo que se pactó en
    su momento, no lo que daría la fórmula hoy (misma regla que las líneas de cotización
    en v352). Por eso todas las cifras salen de `rec` y ninguna se recalcula aquí.
    """
    rec = rec or {}
    ss = getSampleStyleSheet()
    H = ParagraphStyle("H", parent=ss["Normal"], fontSize=9, leading=12)
    Hb = ParagraphStyle("Hb", parent=ss["Normal"], fontSize=9, leading=12,
                        fontName="Helvetica-Bold")
    sm = ParagraphStyle("sm", parent=ss["Normal"], fontSize=8, textColor=C_MUTE, leading=11)
    mk = ParagraphStyle("mk", parent=ss["Normal"], fontSize=14, fontName="Helvetica-Bold",
                        textColor=C_BRAND)
    ti = ParagraphStyle("ti", parent=ss["Normal"], fontSize=18, fontName="Helvetica-Bold",
                        textColor=C_BRAND)

    _lib = _es_liberacion(rec)
    _titulo = d("RETENTION RELEASE") if _lib else d("PROGRESS CLAIM")

    buf = _io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm,
                            title="%s %s" % (_titulo, rec.get("Number", "")))
    story = []

    # ── emisor: la identidad FISCAL, no el nombre interno del grupo ──────────
    # Mismo criterio que v483 en la factura: un documento que pide dinero lleva el
    # nombre legal y el ABN de quien lo pide. Import perezoso y degradando: un fallo
    # leyendo la identidad no puede impedir emitir el documento.
    _grp = str(rec.get("Group", "")) or grupo_nombre
    _ident = {}
    try:
        from core import contable
        _ident = contable.identidad(_grp)
    except Exception as e:
        logger.warning("claim_pdf: no se pudo leer la identidad fiscal de %s: %s", _grp, e)
    marca = str(_ident.get("legal") or "").strip() or grupo_nombre or _grp
    _emisor = [Paragraph(str(marca), mk)]
    if str(_ident.get("abn") or "").strip():
        _emisor.append(Paragraph(f"{d('ABN')} {_ident['abn']}", sm))
    head = Table([[_emisor, Paragraph(_titulo, ti)]], colWidths=[90 * mm, 88 * mm])
    head.setStyle(TableStyle([("ALIGN", (1, 0), (1, 0), "RIGHT"),
                              ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [head, Spacer(1, 10)]

    # ── cabecera: de quién es la obra y qué documento es ─────────────────────
    _filas_meta = [
        [Paragraph(d("Claim no."), sm), Paragraph(str(rec.get("Number", "")), Hb)],
        [Paragraph(d("Date"), sm), Paragraph(str(rec.get("Date", "")), H)],
    ]
    if str(rec.get("PeriodTo", "")).strip():
        _filas_meta.append([Paragraph(d("Period to"), sm),
                            Paragraph(str(rec.get("PeriodTo")), H)])
    _filas_meta.append([Paragraph(d("Status"), sm),
                        Paragraph(i18n.etiqueta(str(rec.get("Status", ""))), H)])
    meta = Table(_filas_meta, colWidths=[24 * mm, 34 * mm])
    meta.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 1),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))

    _prj = proyecto or {}
    cli = cliente or {}
    bill = [Paragraph(f"<b>{d('Claim to')}</b>", Hb),
            Paragraph(str(cli.get("Name", "") or _prj.get("Client", "") or "—"), H)]
    for k in ("ContactName", "Address", "Email", "Phone"):
        v = str(cli.get(k, "")).strip()
        if v:
            bill.append(Paragraph(v, sm))
    if str(_prj.get("Name", "")).strip():
        bill += [Spacer(1, 4), Paragraph(f"<b>{d('Job')}</b>", Hb),
                 Paragraph(str(_prj.get("Name")), H)]
        if str(_prj.get("Location", "")).strip():
            bill.append(Paragraph(str(_prj.get("Location")), sm))
    info = Table([[bill, meta]], colWidths=[104 * mm, 74 * mm])
    info.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [info, Spacer(1, 12)]

    _est_tab = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_BRAND),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, C_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#c3ccd8")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)])

    if not _lib:
        # ── el valor del contrato, con cada variación a la vista ─────────────
        _cv = _num(rec.get("ContractValue"))
        _vv = _num(rec.get("VariationsValue"))
        filas = [[d("Contract"), d("Amount")],
                 [d("Original contract sum"), _money(_cv)]]
        _aprob = [v for v in (variaciones or [])
                  if str(v.get("Status", "")) == "approved"]
        for v in _aprob:
            filas.append(["%s %s — %s" % (d("Variation"), v.get("Number", ""),
                                          str(v.get("Description", ""))[:70]),
                          _money(v.get("Amount"))])
        # ⚠️ Si las variaciones suman algo pero no llega ni una detallada, se dice en vez
        # de callar: el total NO se toca (sale de la fila congelada), pero el cliente
        # tiene que saber que hay un importe que este papel no desglosa.
        if not _aprob and round(_vv, 2) != 0:
            filas.append([d("Approved variations"), _money(_vv)])
        filas.append([d("Adjusted contract sum"), _money(_cv + _vv)])
        t1 = Table(filas, colWidths=[133 * mm, 45 * mm])
        t1.setStyle(_est_tab)
        t1.setStyle(TableStyle([("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                                ("LINEABOVE", (0, -1), (-1, -1), 0.6, C_BRAND)]))
        story += [t1, Spacer(1, 10)]

        # ── el cálculo, de arriba abajo ──────────────────────────────────────
        _pct = _num(rec.get("PctComplete"))
        _hecho = _num(rec.get("WorkDone"))
        _antes = _num(rec.get("PreviouslyClaimed"))
        _ret_pct = _num(rec.get("RetentionPct"))
        _ret = _num(rec.get("Retention"))
        _bruto = _num(rec.get("ThisClaim"))
        calc = Table([
            [d("This claim"), d("Amount")],
            [d("Work completed to date ({pct}%)", pct=f"{_pct:g}"), _money(_hecho)],
            [d("Less previously claimed"), "-" + _money(_antes)],
            [d("Value of this claim"), _money(_bruto)],
            [d("Less retention ({pct}%)", pct=f"{_ret_pct:g}"), "-" + _money(_ret)],
            [d("NET AMOUNT PAYABLE"), _money(_bruto - _ret)],
        ], colWidths=[133 * mm, 45 * mm])
        calc.setStyle(_est_tab)
        calc.setStyle(TableStyle([
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, -1), (-1, -1), C_BRAND),
            ("LINEABOVE", (0, -1), (-1, -1), 0.8, C_BRAND),
            ("LINEABOVE", (0, 3), (-1, 3), 0.4, colors.HexColor("#c3ccd8"))]))
        story += [calc, Spacer(1, 10)]
    else:
        # ── la liberación: contra qué se pide ────────────────────────────────
        _r = retenido or {}
        _imp = _num(rec.get("ThisClaim"))
        filas = [[d("Retention"), d("Amount")],
                 [d("Retention held to date"), _money(_r.get("retenido"))]]
        # Lo ya devuelto ANTES de este documento: el acumulado incluye este mismo.
        _antes_lib = round(_num(_r.get("liberado")) - _imp, 2)
        if _antes_lib > 0:
            filas.append([d("Less previously released"), "-" + _money(_antes_lib)])
        filas += [[d("Released in this claim"), _money(_imp)],
                  [d("NET AMOUNT PAYABLE"), _money(_imp)]]
        t2 = Table(filas, colWidths=[133 * mm, 45 * mm])
        t2.setStyle(_est_tab)
        t2.setStyle(TableStyle([
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, -1), (-1, -1), C_BRAND),
            ("LINEABOVE", (0, -1), (-1, -1), 0.8, C_BRAND)]))
        story += [t2, Spacer(1, 10)]
        # ⚠️ Lo que queda retenido se dice SIEMPRE, también cuando es 0: en una
        # liberación parcial —las dos mitades habituales en AU— el cliente necesita
        # saber que esto no cierra la retención, y el silencio se leería como que sí.
        _queda = _num(_r.get("pendiente"))
        story += [Paragraph(d("Retention still held after this release: {amount}",
                              amount=_money(_queda)), sm), Spacer(1, 6)]

    if str(rec.get("Note", "")).strip():
        story += [Paragraph(f"<b>{d('Note:')}</b> {rec.get('Note')}", sm)]

    doc.build(story)
    return buf.getvalue()
