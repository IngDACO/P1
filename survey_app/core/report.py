"""
Generador de reporte PDF con ReportLab.
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# ── Colores ──────────────────────────────────
C_HEADER   = colors.HexColor("#1a3a5c")
C_SUBHEAD  = colors.HexColor("#2e6da4")
C_RED_BG   = colors.HexColor("#f1948a")
C_RED_DARK = colors.HexColor("#c0392b")
C_GREY     = colors.HexColor("#f2f2f2")
C_WHITE    = colors.white
C_BLACK    = colors.black

def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("ReportTitle",
        fontSize=18, textColor=C_WHITE, alignment=TA_CENTER,
        spaceAfter=4, fontName="Helvetica-Bold"))
    s.add(ParagraphStyle("SectionHead",
        fontSize=12, textColor=C_WHITE, alignment=TA_LEFT,
        spaceBefore=8, spaceAfter=4, fontName="Helvetica-Bold"))
    s.add(ParagraphStyle("SubHead",
        fontSize=10, textColor=C_SUBHEAD, alignment=TA_LEFT,
        spaceBefore=6, spaceAfter=2, fontName="Helvetica-Bold"))
    s.add(ParagraphStyle("Normal2",
        fontSize=9, textColor=C_BLACK, alignment=TA_LEFT,
        spaceAfter=2, fontName="Helvetica"))
    s.add(ParagraphStyle("SmallCenter",
        fontSize=7, textColor=colors.grey, alignment=TA_CENTER,
        fontName="Helvetica"))
    return s

def _header_table(title: str, styles):
    data = [[Paragraph(title, styles["ReportTitle"])]]
    t = Table(data, colWidths=[170*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), C_HEADER),
        ("ROUNDEDCORNERS", [4]),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    return t

def _section_header(text: str, styles):
    data = [[Paragraph(text, styles["SectionHead"])]]
    t = Table(data, colWidths=[170*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), C_SUBHEAD),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
    ]))
    return t

def _param_table(data_dict: dict, styles, cols=3):
    """Tabla de parámetros en N columnas."""
    items = [(k, f"{v:.2f}" if isinstance(v, float) else str(v))
             for k, v in data_dict.items() if v is not None]
    rows = []
    row = []
    for i, (k, v) in enumerate(items):
        row.append(Paragraph(f"<b>{k}</b>", styles["Normal2"]))
        row.append(Paragraph(v, styles["Normal2"]))
        if (i + 1) % cols == 0:
            rows.append(row)
            row = []
    if row:  # padding
        while len(row) < cols * 2:
            row.append(Paragraph("", styles["Normal2"]))
        rows.append(row)

    col_w = [28*mm, 20*mm] * cols
    t = Table(rows, colWidths=col_w)
    t.setStyle(TableStyle([
        ("GRID",       (0,0), (-1,-1), 0.3, colors.lightgrey),
        ("BACKGROUND", (0,0), (-1,-1), C_GREY),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
    ]))
    return t

def _survey_table(df, lim_map: dict, min_vals: dict, styles, title=""):
    """Tabla de matriz SURVEY con resaltado."""
    cols = list(df.columns)
    header = [Paragraph(f"<b>#</b>", styles["Normal2"])] + \
             [Paragraph(f"<b>{c}</b>", styles["Normal2"]) for c in cols]
    rows = [header]

    for idx, row in df.iterrows():
        data_row = [Paragraph(str(idx+1), styles["Normal2"])]
        for col in cols:
            val = row[col]
            data_row.append(Paragraph(f"{val:.1f}", styles["Normal2"]))
        rows.append(data_row)

    col_w = [12*mm] + [24*mm] * len(cols)
    t = Table(rows, colWidths=col_w)

    style_cmds = [
        ("GRID",       (0,0), (-1,-1), 0.3, colors.lightgrey),
        ("BACKGROUND", (0,0), (0,-1),  C_GREY),
        ("BACKGROUND", (0,0), (-1,0),  C_SUBHEAD),
        ("TEXTCOLOR",  (0,0), (-1,0),  C_WHITE),
        ("FONTNAME",   (0,0), (-1,0),  "Helvetica-Bold"),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
    ]

    for row_idx, (_, row) in enumerate(df.iterrows(), start=1):
        for col_idx, col in enumerate(cols, start=1):
            val     = row[col]
            lim     = lim_map.get(col)
            min_val = min_vals.get(f"MIN_{col}")
            if lim is not None and val < lim:
                if min_val is not None and abs(val - min_val) < 0.001:
                    style_cmds.append(
                        ("BACKGROUND", (col_idx, row_idx), (col_idx, row_idx), C_RED_DARK))
                    style_cmds.append(
                        ("TEXTCOLOR",  (col_idx, row_idx), (col_idx, row_idx), C_WHITE))
                    style_cmds.append(
                        ("FONTNAME",   (col_idx, row_idx), (col_idx, row_idx), "Helvetica-Bold"))
                else:
                    style_cmds.append(
                        ("BACKGROUND", (col_idx, row_idx), (col_idx, row_idx), C_RED_BG))

    t.setStyle(TableStyle(style_cmds))
    return t

def _summary_table(summary_list: list, styles):
    header = [Paragraph(f"<b>{k}</b>", styles["Normal2"]) for k in summary_list[0].keys()]
    rows   = [header]
    for item in summary_list:
        rows.append([Paragraph(str(v), styles["Normal2"]) for v in item.values()])
    n_cols = len(summary_list[0])
    col_w  = [170*mm / n_cols] * n_cols
    t = Table(rows, colWidths=col_w)
    t.setStyle(TableStyle([
        ("GRID",       (0,0), (-1,-1), 0.3, colors.lightgrey),
        ("BACKGROUND", (0,0), (-1,0),  C_SUBHEAD),
        ("TEXTCOLOR",  (0,0), (-1,0),  C_WHITE),
        ("FONTNAME",   (0,0), (-1,0),  "Helvetica-Bold"),
        ("BACKGROUND", (0,1), (-1,-1), C_GREY),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
    ]))
    return t


def generate_report(
    project_params: dict,
    calculated: dict,
    survey_original,    # DataFrame
    survey_adjusted,    # DataFrame
    lim_map: dict,
    analysis: dict,
    best: dict,
    bs_result: dict,
    survey_cols: list,
) -> bytes:
    """
    Genera el reporte PDF completo y retorna bytes.
    """
    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm
    )
    styles = _styles()
    story  = []
    sp     = lambda n=6: Spacer(1, n)

    # ── Portada / encabezado ─────────────────────
    story.append(_header_table("ELEVATOR SURVEY ANALYZER — REPORTE DE CÁLCULO", styles))
    story.append(sp(4))
    story.append(Paragraph(
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        styles["SmallCenter"]
    ))
    story.append(sp(10))

    # ── 1. Parámetros del proyecto ───────────────
    story.append(_section_header("1. PARÁMETROS DEL PROYECTO", styles))
    story.append(sp(4))

    # PDF params
    story.append(Paragraph("Extraídos del PDF", styles["SubHead"]))
    pdf_keys = ["BS","BT","BK","BKS","TK","TKA","TKS","TSW","TKSW","TS","SF1","SF2","SG","TG","BGS","BKF1","BKF2"]
    pdf_dict = {k: project_params.get(k) for k in pdf_keys if project_params.get(k) is not None}
    story.append(_param_table(pdf_dict, styles, cols=3))
    story.append(sp(4))

    # User params
    story.append(Paragraph("Ingresados por el usuario", styles["SubHead"]))
    user_keys = ["BSR","BC","FS","FRAME","RAIL","OMEGA_SIDE"]
    user_dict = {k: project_params.get(k) for k in user_keys if project_params.get(k) is not None}
    story.append(_param_table(user_dict, styles, cols=3))
    story.append(sp(8))

    # ── 2. Límites y valores derivados ──────────
    story.append(_section_header("2. LÍMITES Y VALORES DERIVADOS", styles))
    story.append(sp(4))

    limit_keys = ["LIMIT_WR","LIMIT_FR","LIMIT_OR","LIMIT_WL","LIMIT_FL","LIMIT_OL",
                  "LIMIT_OB","LIMIT_ZB","LIMIT_R","LIMIT_L"]
    story.append(Paragraph("Límites geométricos", styles["SubHead"]))
    story.append(_param_table(
        {k: calculated.get(k) for k in limit_keys if calculated.get(k) is not None},
        styles, cols=3
    ))
    story.append(sp(4))

    story.append(Paragraph("Offsets aplicados", styles["SubHead"]))
    off_keys = ["Offset_WR","Offset_FR","Offset_WL","Offset_FL"]
    story.append(_param_table(
        {k: calculated.get(k) for k in off_keys if calculated.get(k) is not None},
        styles, cols=2
    ))
    story.append(sp(4))

    story.append(Paragraph("Dimensiones de cabina", styles["SubHead"]))
    dim_keys = ["CS","TL","TLBC"]
    story.append(_param_table(
        {k: calculated.get(k) for k in dim_keys if calculated.get(k) is not None},
        styles, cols=3
    ))
    story.append(sp(8))

    # ── 3. Matriz SURVEY original ────────────────
    story.append(_section_header("3. MATRIZ SURVEY ORIGINAL (medidas en campo)", styles))
    story.append(sp(4))
    story.append(_survey_table(
        survey_original,
        {c: 9999 for c in survey_cols},  # sin resaltado
        {},
        styles
    ))
    story.append(sp(8))

    # ── 4. Matriz SURVEY ajustada ────────────────
    story.append(_section_header("4. MATRIZ SURVEY AJUSTADA (con offsets aplicados)", styles))
    story.append(sp(4))
    min_vals = {f"MIN_{c}": analysis[f"MIN_{c}"] for c in survey_cols}
    story.append(_survey_table(survey_adjusted, lim_map, min_vals, styles))
    story.append(sp(4))

    # Resumen ajustada
    summary = []
    for col in survey_cols:
        summary.append({
            "Columna":         col,
            "Limite (mm)":     f"{lim_map[col]:.2f}",
            "Fuera limite":    analysis[f"{col}_OFF_COUNT"],
            "Minimo (mm)":     f"{analysis[f'MIN_{col}']:.2f}",
            "Diferencia (mm)": f"{analysis[f'DIF_{col}']:.2f}",
        })
    story.append(_summary_table(summary, styles))
    story.append(sp(4))
    story.append(Paragraph(
        f"<b>MAX OFF RL:</b> {analysis['MAX_OFF_RL']:.2f} mm  &nbsp;&nbsp; "
        f"<b>MAX OFF FB:</b> {analysis['MAX_OFF_FB']:.2f} mm",
        styles["Normal2"]
    ))
    story.append(sp(8))

    # ── 5. Resultado optimización ────────────────
    story.append(PageBreak())
    story.append(_section_header("5. RESULTADO DE LA OPTIMIZACIÓN", styles))
    story.append(sp(4))

    if best:
        story.append(Paragraph(
            f"<b>Desplazamiento RL:</b> {best['rl']} mm  &nbsp;&nbsp; "
            f"<b>Desplazamiento FB:</b> {best['fb']} mm  &nbsp;&nbsp; "
            f"<b>Valores fuera de límite:</b> {best['total_off']}",
            styles["Normal2"]
        ))
        story.append(sp(4))
        best_df  = __import__('pandas').DataFrame(best["matrix"])
        best_min = {f"MIN_{c}": min(best_df[c]) for c in survey_cols}
        story.append(Paragraph("Matriz solución:", styles["SubHead"]))
        story.append(_survey_table(best_df, lim_map, best_min, styles))
        story.append(sp(4))

        final_summary = []
        for col in survey_cols:
            col_vals = [r[col] for r in best["matrix"]]
            final_summary.append({
                "Columna":         col,
                "Limite (mm)":     f"{lim_map[col]:.2f}",
                "Fuera limite":    sum(1 for v in col_vals if v < lim_map[col]),
                "Minimo (mm)":     f"{min(col_vals):.2f}",
                "Dif vs Limite":   f"{lim_map[col]-min(col_vals):.2f}",
            })
        story.append(_summary_table(final_summary, styles))
    else:
        story.append(Paragraph("No se encontró combinación válida.", styles["Normal2"]))

    story.append(sp(8))

    # ── 6. Análisis BSR vs BS ────────────────────
    story.append(_section_header("6. ANÁLISIS BSR vs BS", styles))
    story.append(sp(4))
    if not bs_result.get("needed"):
        story.append(Paragraph("BSR >= BS: No se requiere ajuste de shaft.", styles["Normal2"]))
    elif bs_result.get("step") is None:
        story.append(Paragraph(
            f"No se encontró paso en ningún rango. DIF BS = {bs_result.get('dif_original','N/A')} mm",
            styles["Normal2"]
        ))
    else:
        story.append(_param_table({
            "DIF BS (mm)":    bs_result.get("dif_original"),
            "Paso encontrado": bs_result.get("step"),
            "Rango":           bs_result.get("range"),
            "Zona":            bs_result.get("range_name"),
        }, styles, cols=2))

    story.append(sp(10))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(sp(4))
    story.append(Paragraph("Elevator Survey Analyzer — Documento generado automáticamente",
                            styles["SmallCenter"]))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
