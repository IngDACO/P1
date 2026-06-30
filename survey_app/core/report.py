"""
Reporte PDF con trazabilidad completa — Fórmula → Sustitución → Resultado
Incluye cada paso del optimizador.
"""
import io
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from core.highlighting import (
    cell_state, ctrl_applies_to_cell, reportlab_commands, OR_OL_COLS,
)
from core.diagrams import floor_plan_svg

# ── Color para bloques de interpretación IA ──────────────
C_IA_BG     = colors.HexColor("#f0f7ff")
C_IA_BORDER = colors.HexColor("#2e6da4")

# ── Paleta de colores ────────────────────────────────────────
C_HEADER   = colors.HexColor("#1a3a5c")
C_SUBHEAD  = colors.HexColor("#2e6da4")
C_RED_BG   = colors.HexColor("#f1948a")
C_RED_DARK = colors.HexColor("#c0392b")
C_GREEN_BG = colors.HexColor("#eafaf1")
C_GREEN    = colors.HexColor("#1e8449")
C_GREY     = colors.HexColor("#f5f5f5")
C_FORMULA  = colors.HexColor("#f0f4ff")
C_ORANGE   = colors.HexColor("#e67e22")
C_BEST     = colors.HexColor("#d4efdf")
C_WHITE    = colors.white
C_BLACK    = colors.black

W = 170 * mm


def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("ReportTitle",  fontSize=16, textColor=C_WHITE,    alignment=TA_CENTER, fontName="Helvetica-Bold", spaceAfter=2))
    s.add(ParagraphStyle("ReportSub",    fontSize=9,  textColor=colors.HexColor("#b0c8e8"), alignment=TA_CENTER, fontName="Helvetica", spaceAfter=4))
    s.add(ParagraphStyle("SectionHead",  fontSize=11, textColor=C_WHITE,    alignment=TA_LEFT,   fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=2))
    s.add(ParagraphStyle("SubHead",      fontSize=10, textColor=C_SUBHEAD,  alignment=TA_LEFT,   fontName="Helvetica-Bold", spaceBefore=4, spaceAfter=2))
    s.add(ParagraphStyle("SubHead2",     fontSize=9,  textColor=C_SUBHEAD,  alignment=TA_LEFT,   fontName="Helvetica-Bold", spaceBefore=3, spaceAfter=1))
    s.add(ParagraphStyle("FormulaLine",  fontSize=9,  textColor=C_BLACK,    alignment=TA_LEFT,   fontName="Courier",        spaceBefore=0, spaceAfter=0))
    s.add(ParagraphStyle("ResultLine",   fontSize=10, textColor=C_GREEN,    alignment=TA_LEFT,   fontName="Courier-Bold",   spaceBefore=0, spaceAfter=2))
    s.add(ParagraphStyle("Normal2",      fontSize=9,  textColor=C_BLACK,    alignment=TA_LEFT,   fontName="Helvetica",      spaceAfter=2))
    s.add(ParagraphStyle("SmallCenter",  fontSize=7,  textColor=colors.grey,alignment=TA_CENTER, fontName="Helvetica"))
    s.add(ParagraphStyle("Note",         fontSize=8,  textColor=colors.HexColor("#777777"), alignment=TA_LEFT, fontName="Helvetica-Oblique", spaceAfter=2))
    s.add(ParagraphStyle("Mono",         fontSize=8,  textColor=C_BLACK,    alignment=TA_LEFT,   fontName="Courier",        spaceAfter=1))
    return s


def sp(n=5): return Spacer(1, n)


def _section_header(text, styles):
    t = Table([[Paragraph(text, styles["SectionHead"])]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_HEADER),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
    ]))
    return t


def _subheader(text, styles):
    t = Table([[Paragraph(text, styles["SectionHead"])]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_SUBHEAD),
        ("TOPPADDING",    (0,0),(-1,-1), 3),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
    ]))
    return t


def _calc_block(label, formula, substitution, result_str, styles, ok=None):
    if ok is True:    res_color = "#1e8449"
    elif ok is False: res_color = "#c0392b"
    else:             res_color = "#1a5276"
    rows = [
        [Paragraph(f"<b>{label}</b>", styles["Normal2"]), ""],
        [Paragraph(f"  Fórmula:       {formula}",        styles["FormulaLine"]), ""],
        [Paragraph(f"  Sustitución:   = {substitution}", styles["FormulaLine"]), ""],
        [Paragraph(f'  <font color="{res_color}"><b>Resultado:      {result_str}</b></font>', styles["ResultLine"]), ""],
    ]
    t = Table(rows, colWidths=[W*0.7, W*0.3])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), C_FORMULA),
        ("BACKGROUND",   (0,3),(1,3),   C_GREEN_BG if ok else (C_RED_BG if ok is False else C_FORMULA)),
        ("GRID",         (0,0),(-1,-1), 0.3, colors.HexColor("#c8d8f0")),
        ("SPAN",         (0,0),(1,0)), ("SPAN",(0,1),(1,1)),
        ("SPAN",         (0,2),(1,2)), ("SPAN",(0,3),(1,3)),
        ("TOPPADDING",   (0,0),(-1,-1), 2),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2),
        ("LEFTPADDING",  (0,0),(-1,-1), 6),
    ]))
    return t


def _param_table(data_dict, styles, cols=4):
    items = [(k, f"{v:.2f}" if isinstance(v, float) else str(v))
             for k,v in data_dict.items() if v is not None]
    if not items:
        return sp(2)
    rows, row = [], []
    for i, (k, v) in enumerate(items):
        row += [Paragraph(f"<b>{k}</b>", styles["Normal2"]), Paragraph(v, styles["Normal2"])]
        if (i + 1) % cols == 0:
            rows.append(row); row = []
    if row:
        while len(row) < cols * 2:
            row.append(Paragraph("", styles["Normal2"]))
        rows.append(row)
    t = Table(rows, colWidths=[W/(cols*2)] * cols * 2)
    t.setStyle(TableStyle([
        ("GRID",         (0,0),(-1,-1), 0.3, colors.lightgrey),
        ("BACKGROUND",   (0,0),(-1,-1), C_GREY),
        ("TOPPADDING",   (0,0),(-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
        ("LEFTPADDING",  (0,0),(-1,-1), 4),
    ]))
    return t


def _svg_flowable(svg_str, max_width):
    """Convierte un SVG (string) en un flowable Drawing escalado al ancho dado."""
    try:
        from svglib.svglib import svg2rlg
        drawing = svg2rlg(io.BytesIO(svg_str.encode("utf-8")))
        if drawing is None or drawing.width <= 0:
            return None
        sc = max_width / drawing.width
        drawing.width  *= sc
        drawing.height *= sc
        drawing.scale(sc, sc)
        drawing.hAlign = "CENTER"
        return drawing
    except Exception:
        return None


def _ia_block(text, styles, title="🤖 Interpretación técnica"):
    """Bloque visual para la interpretación generada por IA."""
    if not text or text.startswith("[Interpretación no disponible"):
        return sp(2)
    rows = [
        [Paragraph(f"<b>{title}</b>", styles["Note"])],
        [Paragraph(text, styles["Normal2"])],
    ]
    t = Table(rows, colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  C_IA_BORDER),
        ("TEXTCOLOR",     (0,0),(-1,0),  C_WHITE),
        ("BACKGROUND",    (0,1),(-1,-1), C_IA_BG),
        ("BOX",           (0,0),(-1,-1), 0.8, C_IA_BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("RIGHTPADDING",  (0,0),(-1,-1), 8),
    ]))
    return t


def _survey_table(df, lim_map, min_vals, styles, cut_cols=None,
                  ctrl_in_frame=False, ctrl_side=None, max_vals=None):
    """
    Tabla SURVEY con resaltado.  Usa core.highlighting para decidir colores.
    cut_cols: columnas OR/OL en Caso 2 (naranja en lugar de rojo).
    """
    cut_cols = cut_cols or []
    max_vals = max_vals or {}
    total_rows = len(df)
    cols   = list(df.columns)
    header = [Paragraph("<b>#</b>", styles["Normal2"])] + \
             [Paragraph(f"<b>{c}</b>", styles["Normal2"]) for c in cols]
    rows = [header]
    for idx, row in df.iterrows():
        cells = [Paragraph(str(idx + 1), styles["Normal2"])]
        for c in cols:
            val = row[c]
            cells.append(Paragraph(
                f"{val:.1f}" if isinstance(val, (int, float)) else str(val),
                styles["Normal2"],
            ))
        rows.append(cells)
    col_w = [12*mm] + [(W - 12*mm) / len(cols)] * len(cols)
    t = Table(rows, colWidths=col_w)
    cmds = [
        ("GRID",         (0,0),(-1,-1), 0.3, colors.lightgrey),
        ("BACKGROUND",   (0,0),(-1,0),  C_SUBHEAD),
        ("TEXTCOLOR",    (0,0),(-1,0),  C_WHITE),
        ("FONTNAME",     (0,0),(-1,0),  "Helvetica-Bold"),
        ("BACKGROUND",   (0,1),(0,-1),  C_GREY),
        ("TOPPADDING",   (0,0),(-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
        ("LEFTPADDING",  (0,0),(-1,-1), 4),
        ("ALIGN",        (0,0),(-1,-1), "CENTER"),
    ]
    for ri_off, (_, row) in enumerate(df.iterrows()):
        ri = ri_off + 1
        for ci_off, col in enumerate(cols):
            ci = ci_off + 1
            if col not in lim_map:
                continue
            val = row[col]
            if not isinstance(val, (int, float)):
                continue
            state = cell_state(
                value       = val,
                col         = col,
                lim         = lim_map[col],
                min_val     = min_vals.get(f"MIN_{col}"),
                max_val     = max_vals.get(f"MAX_{col}"),
                in_cut_cols = col in cut_cols,
                ctrl_applies= ctrl_applies_to_cell(ri_off, total_rows, col, ctrl_in_frame, ctrl_side),
            )
            for attr, value in reportlab_commands(state, colors):
                cmds.append((attr, (ci, ri), (ci, ri), value))
    t.setStyle(TableStyle(cmds))
    return t


def _diagram_block(title, lines, styles):
    """Caja esquemática con texto monoespaciado (esquema no proporcional)."""
    content = [[Paragraph(f"<b>{title}</b>", styles["SubHead2"])]]
    for line in lines:
        safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        content.append([Paragraph(safe, styles["Mono"])])
    t = Table(content, colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  C_HEADER),
        ("TEXTCOLOR",     (0,0), (-1,0),  C_WHITE),
        ("BACKGROUND",    (0,1), (-1,-1), colors.HexColor("#f4f7fb")),
        ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#b0c0d8")),
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
    ]))
    return t


# ── Diagramas ASCII actualizados ───────────────────────────────
def _dg_bc_calc(ts, tksw, tk, bc_calc):
    tk2 = tk / 2
    return [
        "  Perfil longitudinal (vista lateral, no proporcional):",
        "",
        "  PARED                                              FONDO",
        "  FRONTAL                                            HUECO",
        "    |                                                  |",
        "    |<-- TKSW -->@-- TK/2 --|-- ... --|<-- BC_CALC -->|",
        "    |          riel         |  cabina |               |25|",
        "    +---------------------------------+---------------+--+",
        "    |        BLOQUE CABINA = TL                       |  |",
        "    +-------------------------------------------------+--+",
        "",
        f"    TKSW    = {tksw:.0f} mm   (pared frontal -> centro riel)",
        f"    TK/2    = {tk2:.0f} mm   (centro riel -> fondo cabina)",
        f"    BC_CALC = {bc_calc:.0f} mm   (espacio libre detras de cabina)",
        f"    25 mm    (holgura minima de seguridad al fondo)",
        f"    TS      = {ts:.0f} mm  =  TKSW + TK/2 + BC_CALC + 25",
    ]


def _dg_lateral_limits(lwl, lol, lwr, lor, bks, rail, offset_cabin, offset_side):
    return [
        "  Seccion transversal (vista superior, no proporcional):",
        "",
        f"  Cabina desplazada hacia: {offset_side}   OFFSET_CABIN = {offset_cabin:.0f} mm",
        "",
        "  PARED IZQ                                            PARED DER",
        "    |<-- WL -->|<-RAIL-|<---- BKS ---->|-RAIL->|<-- WR -->|",
        "    |          | Rail L              Rail R    |          |",
        "    |          +------------------------------+           |",
        "    |          |       BLOQUE CABINA          |           |",
        "    |          |       (BKS + 2*RAIL)         |           |",
        "    |          +------------------------------+           |",
        "    |          |<-OL->|<- BT (puerta) ->|<-OR->|          |",
        "    |          +------------------------------+           |",
        "",
        f"    LIMIT WL = {lwl:.1f} mm   |   LIMIT WR = {lwr:.1f} mm",
        f"    LIMIT OL = {lol:.1f} mm   |   LIMIT OR = {lor:.1f} mm",
        f"    BKS = {bks:.0f} mm   |   RAIL = {rail:.0f} mm",
        "",
        "  OR/OL: si v > LIMIT -> requiere CORTE en la apertura de la puerta",
    ]


def _dg_rl(lr, ll, max_rl):
    return [
        "  (no proporcional)   RL < 0 = hacia der.   |   RL > 0 = hacia izq.",
        "",
        "         SKIP                VALIDO                 SKIP",
        "  <-----------[------------------------------------]----------->  RL (mm)",
        f"          -LIMIT_R                            +LIMIT_L",
        f"          = {-lr:.1f} mm                        = +{ll:.1f} mm",
        "",
        f"  Rango total evaluado: -{max_rl:.1f} mm  a  +{max_rl:.1f} mm  (paso 0.5 mm)",
    ]


def _dg_fb(max_fb, fb_max_back, bc_calc, dif_tsw_fs):
    lines = ["  (no proporcional)   FB < 0 = hacia adelante   |   FB > 0 = hacia atras", ""]
    if fb_max_back <= 0:
        lines += [
            "           VALIDO              |              SKIP",
            "  <----------------------------|]-------------------------------->  FB (mm)",
            f"  -MAX_OFF_FB={-max_fb:.1f}              0                      +MAX_OFF_FB=+{max_fb:.1f}",
            f"                         FB_MAX_BACK = 0.0  (sin desplazamiento hacia atras)",
        ]
    elif fb_max_back >= max_fb:
        lines += [
            "                     VALIDO  (BC_CALC no restringe el rango FB)",
            "  <----------------------------------------------------------->  FB (mm)",
            f"  -MAX_OFF_FB={-max_fb:.1f}                         +MAX_OFF_FB=+{max_fb:.1f}",
        ]
    else:
        lines += [
            "             VALIDO                              |   SKIP",
            "  <-------------------------------------[--------]------------>  FB (mm)",
            f"  -MAX_OFF_FB={-max_fb:.1f}             FB_MAX_BACK=+{fb_max_back:.1f}   +MAX_OFF_FB=+{max_fb:.1f}",
        ]
    lines += [
        "",
        f"  BC_CALC = {bc_calc:.1f} mm  |  DIF_TSW_FS = {dif_tsw_fs:.1f} mm  |  FB_MAX_BACK = {fb_max_back:.1f} mm",
    ]
    return lines


def _violations_block(surv_list, lim_map, survey_cols, styles,
                       ctrl_in_frame=False, ctrl_side=None):
    """
    Devuelve elementos de story con el análisis de violaciones:
      - Tabla resumen: col | límite | criterio | # viol | niveles | DIF | estado
      - Matriz por nivel: # | WR | FR | OR | WL | FL | OL | viol.
    """
    elements = []
    total_rows = len(surv_list)

    # ── Calcular violaciones ────────────────────────────────────
    col_viols = {}
    cell_data = {}
    for col in survey_cols:
        if col not in lim_map:
            continue
        lim = lim_map[col]
        col_viols[col] = []
        for i, row in enumerate(surv_list):
            v  = row.get(col, 0) if isinstance(row, dict) else float(row[col])
            el = lim
            if ctrl_applies_to_cell(i, total_rows, col, ctrl_in_frame, ctrl_side):
                el -= 70
            if col in OR_OL_COLS:
                viol   = v > el
                excess = round(v - el, 1)
            else:
                viol   = v < el
                excess = round(el - v, 1)
            if viol:
                col_viols[col].append(i + 1)
            cell_data[(i, col)] = (viol, round(v, 1), el, excess)

    # ── Tabla resumen por columna ───────────────────────────────
    hdr_s = [Paragraph(f"<b>{h}</b>", styles["Normal2"]) for h in
             ["Col.", "Límite", "Criterio", "# Viol.", "Niveles incumplidos", "DIF (mm)", "Estado"]]
    rows_s = [hdr_s]
    for col in survey_cols:
        if col not in lim_map:
            continue
        lim   = lim_map[col]
        viols = col_viols.get(col, [])
        n     = len(viols)
        crit  = "v > LIM" if col in OR_OL_COLS else "v < LIM"
        vals  = [row.get(col, 0) if isinstance(row, dict) else float(row[col])
                 for row in surv_list]
        dif   = max(vals) - lim if col in OR_OL_COLS else lim - min(vals)
        rows_s.append([
            Paragraph(f"<b>{col}</b>",                                       styles["Normal2"]),
            Paragraph(f"{lim:.1f}",                                          styles["Normal2"]),
            Paragraph(crit,                                                   styles["Normal2"]),
            Paragraph(str(n),                                                 styles["Normal2"]),
            Paragraph(", ".join(str(l) for l in viols) if viols else "—",   styles["Normal2"]),
            Paragraph(f"{dif:.2f}",                                          styles["Normal2"]),
            Paragraph("FAIL" if n else "OK",                                  styles["Normal2"]),
        ])
    cw_s = [20*mm, 20*mm, 22*mm, 16*mm, 44*mm, 26*mm, 22*mm]
    t_s  = Table(rows_s, colWidths=cw_s)
    cmds_s = [
        ("GRID",         (0,0), (-1,-1), 0.3, colors.lightgrey),
        ("BACKGROUND",   (0,0), (-1,0),  C_SUBHEAD),
        ("TEXTCOLOR",    (0,0), (-1,0),  C_WHITE),
        ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
        ("BACKGROUND",   (0,1), (-1,-1), C_GREY),
        ("TOPPADDING",   (0,0), (-1,-1), 3),
        ("BOTTOMPADDING",(0,0), (-1,-1), 3),
        ("LEFTPADDING",  (0,0), (-1,-1), 4),
    ]
    for ri, col in enumerate(survey_cols, start=1):
        if col_viols.get(col):
            cmds_s.append(("BACKGROUND", (0, ri), (-1, ri), C_RED_BG))
    t_s.setStyle(TableStyle(cmds_s))
    elements += [t_s, sp(4)]

    # ── Matriz por nivel ────────────────────────────────────────
    ncols = len(survey_cols)
    hdr_l = ([Paragraph("<b>#</b>", styles["Normal2"])] +
              [Paragraph(f"<b>{c}</b>", styles["Normal2"]) for c in survey_cols] +
              [Paragraph("<b>Viol.</b>", styles["Normal2"])])
    rows_l = [hdr_l]
    cmds_l = [
        ("GRID",         (0,0), (-1,-1), 0.3, colors.lightgrey),
        ("BACKGROUND",   (0,0), (-1,0),  C_SUBHEAD),
        ("TEXTCOLOR",    (0,0), (-1,0),  C_WHITE),
        ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
        ("TOPPADDING",   (0,0), (-1,-1), 3),
        ("BOTTOMPADDING",(0,0), (-1,-1), 3),
        ("LEFTPADDING",  (0,0), (-1,-1), 3),
        ("ALIGN",        (0,0), (-1,-1), "CENTER"),
    ]
    cw_l = [12*mm] + [(W - 26*mm) / ncols] * ncols + [14*mm]
    for i in range(len(surv_list)):
        n_viol = 0
        cells  = [Paragraph(str(i + 1), styles["Normal2"])]
        for ci, col in enumerate(survey_cols, start=1):
            viol, val, el, excess = cell_data.get((i, col), (False, 0, 0, 0))
            cells.append(Paragraph(f"{val:.1f}", styles["Normal2"]))
            cmds_l.append(("BACKGROUND", (ci, i+1), (ci, i+1),
                            C_RED_BG if viol else C_GREEN_BG))
            if viol:
                n_viol += 1
        cells.append(Paragraph(str(n_viol) if n_viol else "OK", styles["Normal2"]))
        if n_viol:
            cmds_l.append(("BACKGROUND", (ncols+1, i+1), (ncols+1, i+1), C_RED_BG))
        rows_l.append(cells)
    t_l = Table(rows_l, colWidths=cw_l)
    t_l.setStyle(TableStyle(cmds_l))
    elements.append(t_l)

    return elements


def _summary_table(summary_list, styles):
    if not summary_list:
        return sp(2)
    header = [Paragraph(f"<b>{k}</b>", styles["Normal2"]) for k in summary_list[0]]
    rows   = [header] + [[Paragraph(str(v), styles["Normal2"]) for v in item.values()] for item in summary_list]
    t = Table(rows, colWidths=[W/len(summary_list[0])] * len(summary_list[0]))
    t.setStyle(TableStyle([
        ("GRID",         (0,0),(-1,-1), 0.3, colors.lightgrey),
        ("BACKGROUND",   (0,0),(-1,0),  C_SUBHEAD),
        ("TEXTCOLOR",    (0,0),(-1,0),  C_WHITE),
        ("FONTNAME",     (0,0),(-1,0),  "Helvetica-Bold"),
        ("BACKGROUND",   (0,1),(-1,-1), C_GREY),
        ("TOPPADDING",   (0,0),(-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
        ("LEFTPADDING",  (0,0),(-1,-1), 4),
    ]))
    return t


# ════════════════════════════════════════════════════════════
def generate_report(project_params, calculated, survey_original,
                    survey_adjusted, lim_map, analysis,
                    optimizer_result, bs_result, survey_cols,
                    interpretation=None):

    best          = optimizer_result.get("best")          if optimizer_result else None
    all_solutions = optimizer_result.get("all_solutions", []) if optimizer_result else []
    step_log      = optimizer_result.get("step_log", [])  if optimizer_result else []

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    styles = _styles()
    story  = []
    p      = project_params
    ia     = interpretation or {}   # dict con interpretaciones por sección

    def fv(key):
        v = p.get(key, calculated.get(key, 0.0))
        return float(v) if v is not None else 0.0
    def fstr(key, d=2):
        v = p.get(key, calculated.get(key, 0.0))
        return f"{float(v):.{d}f}" if v is not None else "0.00"

    # ── PORTADA ──────────────────────────────────────────────
    tt = Table([
        [Paragraph("ELEVATOR SURVEY ANALYZER", styles["ReportTitle"])],
        [Paragraph("Reporte de cálculo con trazabilidad completa — incluyendo cada paso del optimizador", styles["ReportSub"])]
    ], colWidths=[W])
    tt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_HEADER),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
    ]))
    story += [tt, sp(4),
              Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y  %H:%M')}", styles["SmallCenter"]),
              sp(10)]

    # ── 1. PARÁMETROS DE ENTRADA ─────────────────────────────
    story += [_section_header("1. PARÁMETROS DE ENTRADA", styles), sp(4)]
    story += [Paragraph("1.1  Extraídos del PDF", styles["SubHead"])]
    story += [_param_table({k: p.get(k) for k in
        ["BS","BT","BK","BKS","TK","TKA","TKS","TSW","TKSW","TS","SF1","SF2","SG","TG","BGS","BKF1","BKF2"]
    }, styles), sp(6)]
    story += [Paragraph("1.2  Ingresados por el usuario", styles["SubHead"])]
    story += [_param_table({k: p.get(k) for k in
        ["BSR","FS","FRAME","RAIL","OFFSET_CABIN"]
    }, styles, cols=5), sp(6)]

    # ── 1.3  Condiciones y configuración ──────────────────────
    story += [Paragraph("1.3  Condiciones y configuración del proyecto", styles["SubHead"])]
    wall_lim   = p.get("WALL_LIMITING", False)
    ctrl_fr    = p.get("CTRL_IN_FRAME", False)
    wall_stop_ = p.get("WALL_STOP")
    wall_side_ = p.get("WALL_SIDE")
    ctrl_s_    = p.get("CTRL_SIDE")
    ns_        = p.get("NS", "—")

    def _yn(b):   return "SI" if b else "NO"
    def _side(s): return str(s) if s else "—"

    cfg_rows = [
        [Paragraph("<b>Condición / Parámetro</b>", styles["Normal2"]),
         Paragraph("<b>Valor</b>",                 styles["Normal2"]),
         Paragraph("<b>Condición / Parámetro</b>", styles["Normal2"]),
         Paragraph("<b>Valor</b>",                 styles["Normal2"])],
        [Paragraph("Número de paradas (NS)",        styles["Normal2"]),
         Paragraph(str(ns_),                        styles["Normal2"]),
         Paragraph("Lado del Omega",                styles["Normal2"]),
         Paragraph(_side(p.get("OMEGA_SIDE")),      styles["Normal2"])],
        [Paragraph("Lado offset cabina",            styles["Normal2"]),
         Paragraph(_side(p.get("OFFSET_SIDE")),     styles["Normal2"]),
         Paragraph("Offset cabina (mm)",            styles["Normal2"]),
         Paragraph(f"{p.get('OFFSET_CABIN', 0):.1f}", styles["Normal2"])],
        [Paragraph("Pared limitante?",              styles["Normal2"]),
         Paragraph(_yn(wall_lim),                   styles["Normal2"]),
         Paragraph("Parada limitante / Lado pared", styles["Normal2"]),
         Paragraph(f"{int(wall_stop_) if wall_stop_ is not None else '—'} / {_side(wall_side_)}", styles["Normal2"])],
        [Paragraph("Controlador en frame?",         styles["Normal2"]),
         Paragraph(_yn(ctrl_fr),                    styles["Normal2"]),
         Paragraph("Lado del controlador",          styles["Normal2"]),
         Paragraph(_side(ctrl_s_),                  styles["Normal2"])],
    ]
    cfg_cw = [W*0.35, W*0.15, W*0.35, W*0.15]
    cfg_t  = Table(cfg_rows, colWidths=cfg_cw)
    cfg_cmds = [
        ("GRID",          (0,0), (-1,-1), 0.3, colors.lightgrey),
        ("BACKGROUND",    (0,0), (-1,0),  C_HEADER),
        ("TEXTCOLOR",     (0,0), (-1,0),  C_WHITE),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("BACKGROUND",    (0,1), (-1,-1), C_GREY),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 5),
    ]
    if wall_lim:
        cfg_cmds += [("BACKGROUND",(1,3),(1,3), C_GREEN_BG),
                     ("FONTNAME",  (1,3),(1,3), "Helvetica-Bold")]
    if ctrl_fr:
        cfg_cmds += [("BACKGROUND",(1,4),(1,4), C_GREEN_BG),
                     ("FONTNAME",  (1,4),(1,4), "Helvetica-Bold")]
    cfg_t.setStyle(TableStyle(cfg_cmds))
    story += [cfg_t, sp(4)]
    story += [_ia_block(ia.get("parametros"), styles,
                        "🤖 Interpretación — Geometría y configuración del proyecto"), sp(8)]

    # ── 2. DIMENSIONES DE CABINA ─────────────────────────────
    story += [_section_header("2. DIMENSIONES DE CABINA", styles), sp(4)]
    cs        = fv("TK") + fv("TKA")
    tl        = cs + fv("TKS") + fv("TSW")
    bc_calc_v = fv("BC_CALC")
    tlbc      = tl + bc_calc_v
    story += [
        _calc_block("CS — Profundidad total de cabina",
            "CS = TK + TKA",
            f"{fstr('TK')} + {fstr('TKA')}",
            f"CS = {cs:.2f} mm", styles), sp(3),
        _calc_block("TL — Profundidad del bloque cabina (riel a riel)",
            "TL = CS + TKS + TSW",
            f"{cs:.2f} + {fstr('TKS')} + {fstr('TSW')}",
            f"TL = {tl:.2f} mm", styles), sp(3),
        _calc_block("BC_CALC — Espacio libre detras de la cabina",
            "BC_CALC = TS - TKSW - (TK / 2) - 25",
            f"{fstr('TS')} - {fstr('TKSW')} - ({fstr('TK')} / 2) - 25",
            f"BC_CALC = {bc_calc_v:.2f} mm", styles), sp(3),
        _calc_block("TLBC — Longitud total con espacio trasero",
            "TLBC = TL + BC_CALC",
            f"{tl:.2f} + {bc_calc_v:.2f}",
            f"TLBC = {tlbc:.2f} mm", styles), sp(4),
        _diagram_block("Perfil longitudinal del hueco",
            _dg_bc_calc(fv("TS"), fv("TKSW"), fv("TK"), bc_calc_v), styles), sp(8),
    ]

    # ── 3. LÍMITES GEOMÉTRICOS ───────────────────────────────
    story += [_section_header("3. LÍMITES GEOMÉTRICOS", styles), sp(4)]
    lwr = fv("SF2") + fv("RAIL") / 2
    lfr = fv("TKSW") - 150
    lwl = fv("SF1") + fv("RAIL") / 2
    lfl = fv("TKSW") - 150
    _base_ol = fv("BKS")/2 + fv("RAIL")/2 - fv("BT")/2 - fv("FRAME")
    _off_c   = fv("OFFSET_CABIN")
    _off_s   = p.get("OFFSET_SIDE", "R")
    lor = _base_ol + _off_c if _off_s == "L" else _base_ol - _off_c
    lol = _base_ol - _off_c if _off_s == "L" else _base_ol + _off_c
    lob_raw = (fv("SG") - fv("TG")/2) * 0.3
    omega   = p.get("OMEGA_SIDE", "R")
    if omega == "R":
        lzb_raw = fv("SF1") * 0.3
        lob, lzb, lr, ll = lor, lol, lob_raw, lzb_raw
        z_side, zb_sf   = "L", "SF1"
    else:
        lzb_raw = fv("SF2") * 0.3
        lob, lzb, lr, ll = lol, lor, lzb_raw, lob_raw
        z_side, zb_sf   = "R", "SF2"

    story += [
        Paragraph("3.1  Límites laterales", styles["SubHead"]),
        _calc_block("LIMIT WR",  "LIMIT WR = SF2 + (RAIL / 2)",
            f"{fstr('SF2')} + ({fstr('RAIL')} / 2)", f"LIMIT WR = {lwr:.2f} mm", styles), sp(3),
        _calc_block("LIMIT WL",  "LIMIT WL = SF1 + (RAIL / 2)",
            f"{fstr('SF1')} + ({fstr('RAIL')} / 2)", f"LIMIT WL = {lwl:.2f} mm", styles), sp(3),
        _calc_block("Base OR/OL", "Base = (BKS/2) + (RAIL/2) - (BT/2) - FRAME",
            f"({fstr('BKS')}/2) + ({fstr('RAIL')}/2) - ({fstr('BT')}/2) - {fstr('FRAME')}",
            f"Base = {_base_ol:.2f} mm", styles), sp(3),
        _calc_block("LIMIT OR",
            f"LIMIT OR = Base {'+ OFFSET_CABIN' if _off_s=='L' else '- OFFSET_CABIN'}  (offset lado {_off_s})",
            f"{_base_ol:.2f} {'+' if _off_s=='L' else '-'} {fstr('OFFSET_CABIN')}",
            f"LIMIT OR = {lor:.2f} mm", styles), sp(3),
        _calc_block("LIMIT OL",
            f"LIMIT OL = Base {'- OFFSET_CABIN' if _off_s=='L' else '+ OFFSET_CABIN'}  (offset lado {_off_s})",
            f"{_base_ol:.2f} {'-' if _off_s=='L' else '+'} {fstr('OFFSET_CABIN')}",
            f"LIMIT OL = {lol:.2f} mm", styles), sp(6),
        _diagram_block("Seccion transversal — Limites laterales",
            _dg_lateral_limits(lwl, lol, lwr, lor, fv("BKS"), fv("RAIL"),
                               fv("OFFSET_CABIN"), _off_s), styles), sp(6),
        Paragraph("3.2  Límites frontales", styles["SubHead"]),
        _calc_block("LIMIT FR",  "LIMIT FR = TKSW - 150",
            f"{fstr('TKSW')} - 150", f"LIMIT FR = {lfr:.2f} mm", styles), sp(3),
        _calc_block("LIMIT FL",  "LIMIT FL = TKSW - 150",
            f"{fstr('TKSW')} - 150", f"LIMIT FL = {lfl:.2f} mm", styles), sp(6),
        Paragraph("3.3  Límites Omega / Zona B", styles["SubHead"]),
        _calc_block("LIMIT OB (raw)", "LIMIT OB = (SG - (TG/2)) x 0.3",
            f"({fstr('SG')} - ({fstr('TG')}/2)) x 0.3",
            f"LIMIT OB raw = {lob_raw:.2f} mm", styles), sp(3),
        _calc_block("LIMIT ZB (raw)",
            f"LIMIT ZB = {zb_sf} x 0.3  (Z lado {z_side}, opuesto al Omega={omega})",
            f"{fstr(zb_sf)} x 0.3",
            f"LIMIT ZB raw = {lzb_raw:.2f} mm", styles), sp(4),
        Paragraph(
            f"<b>Omega lado {omega}  |  Z lado {z_side}:</b>  "
            f"LIMIT OB = {lob:.2f} mm  |  LIMIT ZB = {lzb:.2f} mm  |  "
            f"LIMIT R = {lr:.2f} mm  |  LIMIT L = {ll:.2f} mm",
            styles["Normal2"]), sp(8),
    ]

    # ── 4. OFFSETS ───────────────────────────────────────────
    story += [PageBreak(), _section_header("4. CÁLCULO DE OFFSETS", styles), sp(4)]
    wrt = fv("WRT"); frt = fv("FRT"); wlt = fv("WLT"); flt = fv("FLT")
    bsr = fv("BSR"); bs  = fv("BS")
    off_fr = lfr - frt
    off_fl = lfl - flt
    off_wr = lwr - wrt + (bsr - bs) / 2
    off_wl = lwl - wlt + (bsr - bs) / 2
    story += [
        Paragraph("Totales de la última fila de la matriz SURVEY:", styles["Note"]),
        _param_table({"WRT": wrt, "FRT": frt, "ORT": fv("ORT"), "WLT": wlt, "FLT": flt, "OLT": fv("OLT")}, styles, cols=3), sp(4),
        _calc_block("Offset FR", "Offset FR = LIMIT FR - FRT",
            f"{lfr:.2f} - {frt:.2f}", f"Offset FR = {off_fr:.2f} mm", styles), sp(3),
        _calc_block("Offset FL", "Offset FL = LIMIT FL - FLT",
            f"{lfl:.2f} - {flt:.2f}", f"Offset FL = {off_fl:.2f} mm", styles), sp(3),
        _calc_block("Offset WR", "Offset WR = LIMIT WR - WRT + ((BSR-BS)/2)",
            f"{lwr:.2f} - {wrt:.2f} + (({bsr:.2f}-{bs:.2f})/2)",
            f"Offset WR = {off_wr:.2f} mm", styles), sp(3),
        _calc_block("Offset WL", "Offset WL = LIMIT WL - WLT + ((BSR-BS)/2)",
            f"{lwl:.2f} - {wlt:.2f} + (({bsr:.2f}-{bs:.2f})/2)",
            f"Offset WL = {off_wl:.2f} mm", styles), sp(3),
        _calc_block("Offset OR", "Offset OR = Offset WR  (mismo desplazamiento lateral)",
            f"= {off_wr:.2f} mm",
            f"Offset OR = {off_wr:.2f} mm", styles), sp(3),
        _calc_block("Offset OL", "Offset OL = Offset WL  (mismo desplazamiento lateral)",
            f"= {off_wl:.2f} mm",
            f"Offset OL = {off_wl:.2f} mm", styles), sp(8),
    ]

    # ── 5. MATRIZ ORIGINAL ───────────────────────────────────
    story += [_section_header("5. MATRIZ SURVEY — MEDIDAS EN CAMPO", styles), sp(4),
              Paragraph("Valores medidos en obra antes de aplicar offsets:", styles["Note"]), sp(4),
              _survey_table(survey_original, {c: 9999 for c in survey_cols}, {}, styles), sp(8)]

    # ── 6. MATRIZ AJUSTADA ───────────────────────────────────
    story += [_section_header("6. MATRIZ SURVEY AJUSTADA Y ANÁLISIS", styles), sp(4)]
    min_vals = {f"MIN_{c}": analysis[f"MIN_{c}"] for c in survey_cols}
    max_vals = {f"MAX_{c}": analysis.get(f"MAX_{c}", analysis[f"MIN_{c}"]) for c in survey_cols}
    wall_limiting  = p.get("WALL_LIMITING", False)
    rpt_cut_cols   = ["OR", "OL"] if not wall_limiting else []
    rpt_ctrl       = p.get("CTRL_IN_FRAME", False)
    rpt_ctrl_side  = p.get("CTRL_SIDE", None)
    story += [_survey_table(survey_adjusted, lim_map, min_vals, styles,
                            cut_cols=rpt_cut_cols, max_vals=max_vals,
                            ctrl_in_frame=rpt_ctrl, ctrl_side=rpt_ctrl_side), sp(6)]

    # DIF por columna
    story += [Paragraph("6.1  Diferencias respecto a límites (columna por columna)", styles["SubHead"]), sp(3)]
    for col in survey_cols:
        lim   = lim_map[col]; min_v = analysis[f"MIN_{col}"]
        max_v = analysis.get(f"MAX_{col}", min_v)
        dif_v = analysis[f"DIF_{col}"]; off_c = analysis[f"{col}_OFF_COUNT"]
        if col in OR_OL_COLS:
            formula_text = f"DIF {col} = MAX {col} - LIMIT {col}"
            subst_text   = f"{max_v:.2f} - {lim:.2f}"
        else:
            formula_text = f"DIF {col} = LIMIT {col} - MIN {col}"
            subst_text   = f"{lim:.2f} - {min_v:.2f}"
        story += [_calc_block(f"DIF {col}",
            formula_text, subst_text,
            f"DIF {col} = {dif_v:.2f} mm  |  {off_c} valor(es) fuera de límite",
            styles, ok=(dif_v <= 0)), sp(3)]

    max_rl = analysis["MAX_OFF_RL"]; max_fb = analysis["MAX_OFF_FB"]
    if wall_limiting:
        max_rl_formula = "MAX OFF RL = max(DIF WR, DIF WL, max(0,DIF OR), max(0,DIF OL))  [Caso 1: OR/OL cuentan]"
        max_rl_subst   = (f"max({analysis['DIF_WR']:.2f}, {analysis['DIF_WL']:.2f}, "
                          f"{max(0.0,analysis['DIF_OR']):.2f}, {max(0.0,analysis['DIF_OL']):.2f})")
    else:
        max_rl_formula = "MAX OFF RL = max(DIF WR, DIF WL)  [Caso 2: OR/OL no cuentan como OFF]"
        max_rl_subst   = f"max({analysis['DIF_WR']:.2f}, {analysis['DIF_WL']:.2f})"
    story += [sp(3),
        _calc_block("MAX OFF RL", max_rl_formula, max_rl_subst,
            f"MAX OFF RL = {max_rl:.2f} mm", styles), sp(3),
        _calc_block("MAX OFF FB", "MAX OFF FB = max(DIF FR, DIF FL)",
            f"max({analysis['DIF_FR']:.2f}, {analysis['DIF_FL']:.2f})",
            f"MAX OFF FB = {max_fb:.2f} mm", styles), sp(6)]

    # ── 6.2 ESTADO INICIAL ─────────────────────────────────────
    story += [
        Paragraph("6.2  Estado inicial — límites incumplidos antes de la optimización",
                  styles["SubHead"]),
        sp(2),
        Paragraph(
            "Análisis del estado de la cabina ajustada ANTES de aplicar cualquier "
            "desplazamiento de optimización. Permite identificar qué límites se incumplen "
            "y en qué niveles, como punto de partida para evaluar las mejoras obtenidas.",
            styles["Note"]),
        sp(3),
    ]
    surv_list_adj = (survey_adjusted.to_dict("records")
                     if hasattr(survey_adjusted, "to_dict") else list(survey_adjusted))
    story += _violations_block(surv_list_adj, lim_map, survey_cols, styles,
                                rpt_ctrl, rpt_ctrl_side)
    story += [sp(4),
              _ia_block(ia.get("estado_inicial"), styles,
                        "🤖 Interpretación — Estado inicial del hueco"), sp(3),
              _ia_block(ia.get("desplazamientos"), styles,
                        "🤖 Interpretación — Desplazamientos requeridos"), sp(8)]

    # ── 7. OPTIMIZACIÓN ───────────────────────────────────────
    story += [PageBreak(), _section_header("7. OPTIMIZACIÓN — TRAZABILIDAD COMPLETA DE CADA PASO", styles), sp(4)]

    story += [
        Paragraph("7.1  Parámetros del optimizador", styles["SubHead"]),
        _calc_block("Rango de búsqueda RL",
            "RL ∈ [-MAX OFF RL, +MAX OFF RL]  paso 0.5 mm",
            f"[{-max_rl:.2f}, {max_rl:.2f}]",
            f"Total pasos RL evaluados: {int(max_rl*2/0.5)+1}", styles), sp(3),
        _calc_block("Rango de búsqueda FB",
            "FB ∈ [-MAX OFF FB, +MAX OFF FB]  paso 0.5 mm",
            f"[{-max_fb:.2f}, {max_fb:.2f}]",
            f"Total pasos FB evaluados: {int(max_fb*2/0.5)+1}", styles), sp(4),
        Paragraph("Restricciones aplicadas en cada paso:", styles["SubHead2"]),
        Paragraph(f"  - Si RL < 0: |RL| <= LIMIT R = {lr:.2f} mm", styles["Normal2"]),
        Paragraph(f"  - Si RL > 0: |RL| <= LIMIT L = {ll:.2f} mm", styles["Normal2"]),
        Paragraph(f"  - Pared limitante: {'Si - Parada ' + str(p.get('WALL_STOP','?')) + ' lado ' + str(p.get('WALL_SIDE','?')) if wall_limiting else 'No aplica'}", styles["Normal2"]),
        Paragraph(f"  - TSW={fstr('TSW')} vs FS={fstr('FS')} - FS-TSW={fv('FS')-fv('TSW'):.1f} mm - FB extra activo: {'Si' if fv('FS') > fv('TSW') and wall_limiting else 'No'}", styles["Normal2"]),
        Paragraph(
            f"  - Controlador en frame: {'Si - lado ' + str(p.get('CTRL_SIDE','?')) + ' -> ultimo nivel: LIMIT_O' + str(p.get('CTRL_SIDE','?')) + ' - 70 mm' if rpt_ctrl else 'No'}",
            styles["Normal2"]),
        sp(4),
        _diagram_block("Diagrama de rango RL",
            _dg_rl(lr, ll, max_rl), styles), sp(4),
        _diagram_block("Diagrama de rango FB",
            _dg_fb(max_fb, fv("FB_MAX_BACK"), fv("BC_CALC"), fv("DIF_TSW_FS")), styles), sp(6),
    ]

    # ── 7.2  Log de todos los pasos ─────────────────────────────
    story += [Paragraph("7.2  Log de todos los pasos evaluados", styles["SubHead"]), sp(3)]

    valid_steps = [s for s in step_log if s.get("status") == "VALID"]

    story += [Paragraph(f"Total combinaciones evaluadas: {len(step_log)}  |  Válidas: {len(valid_steps)}", styles["Note"]), sp(3)]

    best_total = best["total_off"] if best else None
    min_off_steps = [s for s in valid_steps if s.get("total_off") == best_total] \
                    if best_total is not None else valid_steps

    story += [
        Paragraph(
            f"Iteraciones con el menor número de valores OFF ({best_total if best_total is not None else 'N/A'}):",
            styles["SubHead2"]
        ),
        Paragraph(
            f"Se muestran {len(min_off_steps)} de {len(valid_steps)} iteraciones válidas "
            f"(solo las que alcanzan el mínimo de {best_total} valor(es) fuera de límite).",
            styles["Note"]
        ),
        sp(2)
    ]

    opt_pairs = {(s["rl"], s["fb"]) for s in all_solutions}

    hdr = [Paragraph(f"<b>{h}</b>", styles["Normal2"]) for h in
           ["RL", "FB", "FB aplic.", "OFF", "WR", "FR", "OR", "WL", "FL", "OL", "Estado"]]
    valid_rows = [hdr]
    for s in min_off_steps:
        obc        = s.get("off_by_col", {})
        fb_aplic   = s.get("fb_applied", s["fb"])
        is_opt     = (s["rl"], s["fb"]) in opt_pairs
        estado     = Paragraph("OPTIMO" if is_opt else "", styles["Normal2"])
        fb_extra   = abs(fb_aplic - s["fb"]) > 0.01
        fb_aplic_p = Paragraph(
            f'<font color="#e67e22"><b>{fb_aplic:.1f}*</b></font>' if fb_extra
            else f"{fb_aplic:.1f}",
            styles["Mono"])
        row = [
            Paragraph(f"{s['rl']:.1f}",     styles["Mono"]),
            Paragraph(f"{s['fb']:.1f}",     styles["Mono"]),
            fb_aplic_p,
            Paragraph(f"{s['total_off']}",  styles["Mono"]),
            Paragraph(f"{obc.get('WR',0)}", styles["Mono"]),
            Paragraph(f"{obc.get('FR',0)}", styles["Mono"]),
            Paragraph(f"{obc.get('OR',0)}", styles["Mono"]),
            Paragraph(f"{obc.get('WL',0)}", styles["Mono"]),
            Paragraph(f"{obc.get('FL',0)}", styles["Mono"]),
            Paragraph(f"{obc.get('OL',0)}", styles["Mono"]),
            estado,
        ]
        valid_rows.append(row)

    cw = [W*0.08]*10 + [W*0.20]
    t_valid = Table(valid_rows, colWidths=cw)
    cmds_v = [
        ("GRID",       (0,0),(-1,-1), 0.3, colors.lightgrey),
        ("BACKGROUND", (0,0),(-1,0),  C_SUBHEAD),
        ("TEXTCOLOR",  (0,0),(-1,0),  C_WHITE),
        ("FONTNAME",   (0,0),(-1,0),  "Helvetica-Bold"),
        ("BACKGROUND", (0,1),(-1,-1), C_GREY),
        ("TOPPADDING", (0,0),(-1,-1), 2),
        ("BOTTOMPADDING",(0,0),(-1,-1),2),
        ("LEFTPADDING",(0,0),(-1,-1), 3),
        ("FONTSIZE",   (0,1),(-1,-1), 7),
    ]
    for ri, s in enumerate(min_off_steps, start=1):
        if (s["rl"], s["fb"]) in opt_pairs:
            cmds_v.append(("BACKGROUND", (0,ri),(-1,ri), C_BEST))
            cmds_v.append(("FONTNAME",   (0,ri),(-1,ri), "Helvetica-Bold"))
        obc = s.get("off_by_col", {})
        for ci, col in enumerate(["WR","FR","OR","WL","FL","OL"], start=4):
            if obc.get(col, 0) > 0:
                cmds_v.append(("BACKGROUND", (ci,ri),(ci,ri), C_RED_BG))
    t_valid.setStyle(TableStyle(cmds_v))
    story += [t_valid, sp(6)]

    # ── 7.3  Resultado final ────────────────────────────────────
    story += [Paragraph("7.3  Resultado final", styles["SubHead"]), sp(3)]
    if best:
        n_sol     = len(all_solutions)
        best_pair_r = (best["rl"], best["fb"])
        # Ordenar consistente con el optimizer: usar fb_applied
        sorted_sols = sorted(
            all_solutions,
            key=lambda s: (
                0 if (s["rl"], s["fb"]) == best_pair_r else 1,
                abs(s["rl"]) + abs(s.get("fb_applied", s["fb"]))
            )
        )
        story += [
            _calc_block("Resumen de optimización",
                "Criterio 1: menor número de valores fuera de límite\nCriterio 2 (desempate): menor desplazamiento total |RL| + |FB aplicado|",
                f"Candidatos con mínimo OFF: {n_sol}  |  Valores fuera de límite: {best['total_off']}",
                f"Seleccionado: RL={best['rl']:.1f} mm, FB iterado={best['fb']:.1f} mm, FB aplicado={best.get('fb_applied', best['fb']):.1f} mm",
                styles, ok=(best["total_off"] == 0)),
            sp(6),
        ]
        for idx_sol, sol in enumerate(sorted_sols):
            is_best   = (sol["rl"], sol["fb"]) == best_pair_r
            prefix    = "SELECCIONADA - " if is_best else ""
            fb_ap     = sol.get("fb_applied", sol["fb"])
            fb_suffix = f"  |  FB aplic. = {fb_ap:.1f} mm" if abs(fb_ap - sol["fb"]) > 0.01 else ""
            story += [
                _subheader(f"{prefix}Solución {idx_sol+1} de {n_sol} — RL = {sol['rl']} mm  |  FB = {sol['fb']} mm{fb_suffix}", styles),
                sp(3),
                Paragraph("Matriz con desplazamientos aplicados:", styles["Note"]), sp(3),
            ]
            sol_df  = pd.DataFrame(sol["matrix"])
            sol_min = {f"MIN_{c}": min(sol_df[c]) for c in survey_cols}
            sol_max = {f"MAX_{c}": max(sol_df[c]) for c in survey_cols}
            if not wall_limiting:
                lor_v        = lim_map["OR"]
                lol_v        = lim_map["OL"]
                last_sol_idx = len(sol_df) - 1
                cut_or_vals, cut_ol_vals = [], []
                for i, (or_v, ol_v) in enumerate(zip(sol_df["OR"], sol_df["OL"])):
                    or_lim = lor_v - 70 if (rpt_ctrl and rpt_ctrl_side == "R" and i == last_sol_idx) else lor_v
                    ol_lim = lol_v - 70 if (rpt_ctrl and rpt_ctrl_side == "L" and i == last_sol_idx) else lol_v
                    cut_or_vals.append(f"{or_v - or_lim:.1f}" if or_v - or_lim > 0 else "")
                    cut_ol_vals.append(f"{ol_v - ol_lim:.1f}" if ol_v - ol_lim > 0 else "")
                sol_df.insert(3, "CUT OR", cut_or_vals)
                sol_df.insert(7, "CUT OL", cut_ol_vals)
            story  += [_survey_table(sol_df, lim_map, sol_min, styles,
                                     cut_cols=rpt_cut_cols, max_vals=sol_max,
                                     ctrl_in_frame=rpt_ctrl, ctrl_side=rpt_ctrl_side), sp(3)]
            if not wall_limiting:
                story += [Paragraph(
                    "CUT OR = OR - LIMIT OR  /  CUT OL = OL - LIMIT OL  "
                    "(valor a cortar si supera el límite; vacío = dentro del límite)",
                    styles["Note"]), sp(3)]
            sol_sum = []
            for col in survey_cols:
                cv  = [r[col] for r in sol["matrix"]]
                lim = lim_map[col]
                if col in OR_OL_COLS:
                    ext   = max(cv); dif = ext - lim
                    off   = sum(1 for v in cv if v > lim)
                    lbl   = "Máximo (mm)"
                    viols = [str(i+1) for i,v in enumerate(cv) if v > lim]
                else:
                    ext   = min(cv); dif = lim - ext
                    off   = sum(1 for v in cv if v < lim)
                    lbl   = "Mínimo (mm)"
                    viols = [str(i+1) for i,v in enumerate(cv) if v < lim]
                sol_sum.append({
                    "Columna":       col,
                    "Límite (mm)":   f"{lim:.2f}",
                    "Fuera límite":  off,
                    "Niveles":       ", ".join(viols) if viols else "—",
                    lbl:             f"{ext:.2f}",
                    "Dif vs Límite": f"{dif:.2f}",
                })
            story += [_summary_table(sol_sum, styles), sp(6)]
    else:
        story += [Paragraph("No se encontró combinación válida.", styles["Normal2"]), sp(4)]

    story += [_ia_block(ia.get("solucion_optima"), styles,
                        "🤖 Interpretación — Solución óptima encontrada"), sp(3)]
    if ia.get("evasion_pared"):
        story += [_ia_block(ia.get("evasion_pared"), styles,
                            "🤖 Interpretación — Evasión de pared limitante"), sp(3)]
    story += [sp(4)]

    # ── 8. DIAGRAMA DE POSICIONAMIENTO — PLANTA POR PISO ──────
    story += [PageBreak(), _section_header("8. DIAGRAMA DE POSICIONAMIENTO — PLANTA POR PISO", styles), sp(2),
              Paragraph("Vista superior del encaje de la cabina en el shaft, piso a piso "
                        "(matriz de la solución seleccionada). Verde = dentro de límite, "
                        "naranja = al límite, rojo = fuera.", styles["Note"]), sp(4)]
    diag_sol = best if best else None
    if diag_sol and diag_sol.get("matrix"):
        mat        = diag_sol["matrix"]
        n_fl       = len(mat)
        rpt_limmap = {c: lim_map[c] for c in ["WR", "FR", "OR", "WL", "FL", "OL"]}
        c_in_frame = p.get("CTRL_IN_FRAME", False)
        c_side     = p.get("CTRL_SIDE", None)
        drawn = 0
        for i, row in enumerate(mat):
            svg  = floor_plan_svg(p, calculated, row, i, rpt_limmap,
                                  c_in_frame, c_side, is_last=(i == n_fl - 1))
            draw = _svg_flowable(svg, W * 0.66)
            if draw is not None:
                story += [draw, sp(6)]
                drawn += 1
                if drawn % 2 == 0 and i < n_fl - 1:
                    story += [PageBreak()]
        if drawn == 0:
            story += [Paragraph("Diagrama no disponible en este entorno.", styles["Note"]), sp(6)]
    else:
        story += [Paragraph("No hay solución para graficar.", styles["Note"]), sp(6)]

    # ── 9. BSR vs BS ─────────────────────────────────────────
    story += [PageBreak(), _section_header("9. ANÁLISIS BSR vs BS", styles), sp(4)]
    if not bs_result.get("needed"):
        story += [_calc_block("Condición", "BSR >= BS  ->  Sin ajuste requerido",
            f"{fstr('BSR')} >= {fstr('BS')}", "No se requiere ajuste de shaft",
            styles, ok=True), sp(6)]
    else:
        dif_bs = bs_result.get("dif_original", 0)
        story += [
            _calc_block("DIF BS", "DIF BS = BS - BSR  (cuando BSR < BS)",
                f"{fstr('BS')} - {fstr('BSR')}", f"DIF BS = {dif_bs:.2f} mm",
                styles, ok=False), sp(4),
            Paragraph("Búsqueda del paso en los 3 rangos (paso 0.5 mm):", styles["SubHead2"]),
            _calc_block("Rango 1 — Zona ZB", "Ciclos de 0 hasta LIMIT ZB",
                f"[0  ->  {lzb:.2f}]", "Buscando paso donde la resta de DIF BS llega a 0", styles), sp(3),
            _calc_block("Rango 2 — Zona OB", "Ciclos de LIMIT ZB hasta (LIMIT ZB + LIMIT OB)",
                f"[{lzb:.2f}  ->  {lzb+lob:.2f}]", "Buscando paso donde la resta de DIF BS llega a 0", styles), sp(3),
            _calc_block("Rango 3 — Zona extendida", "Ciclos de (LIMIT ZB + LIMIT OB) hasta 1000",
                f"[{lzb+lob:.2f}  ->  1000]", "Buscando paso donde la resta de DIF BS llega a 0", styles), sp(4),
        ]
        if bs_result.get("step") is not None:
            story += [_calc_block("Resultado", "Paso encontrado",
                f"Rango: {bs_result.get('range')}  |  Zona: {bs_result.get('range_name')}",
                f"Paso = {bs_result.get('step')} mm", styles, ok=True)]
        else:
            story += [Paragraph("No se encontró paso en ningún rango.", styles["Normal2"])]
        story.append(sp(4))

    story += [_ia_block(ia.get("bsr_vs_bs"), styles,
                        "🤖 Interpretación — Análisis BSR vs BS"), sp(6)]

    # ── 10. CONSIDERACIONES FINALES ──────────────────────────
    if ia.get("consideraciones"):
        story += [
            _section_header("10. CONSIDERACIONES FINALES Y PUNTOS A VERIFICAR EN CAMPO", styles),
            sp(4),
            _ia_block(ia.get("consideraciones"), styles,
                      "🤖 Puntos críticos para el equipo de instalación"),
            sp(8),
        ]

    # ── PIE ──────────────────────────────────────────────────
    story += [sp(8), HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey), sp(4),
              Paragraph("Elevator Survey Analyzer — Reporte generado automáticamente", styles["SmallCenter"]),
              Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["SmallCenter"])]

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()
