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
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

C_HEADER   = colors.HexColor("#1a3a5c")
C_SUBHEAD  = colors.HexColor("#2e6da4")
C_ACCENT   = colors.HexColor("#e8f0fa")
C_RED_BG   = colors.HexColor("#f1948a")
C_RED_DARK = colors.HexColor("#c0392b")
C_GREEN_BG = colors.HexColor("#eafaf1")
C_GREEN    = colors.HexColor("#1e8449")
C_YELLOW   = colors.HexColor("#fef9e7")
C_GREY     = colors.HexColor("#f5f5f5")
C_FORMULA  = colors.HexColor("#f0f4ff")
C_WHITE    = colors.white
C_BLACK    = colors.black
C_BEST     = colors.HexColor("#d4efdf")

W = 170*mm

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
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),C_HEADER),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),("LEFTPADDING",(0,0),(-1,-1),8)]))
    return t

def _subheader(text, styles):
    t = Table([[Paragraph(text, styles["SectionHead"])]], colWidths=[W])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),C_SUBHEAD),("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),("LEFTPADDING",(0,0),(-1,-1),8)]))
    return t

def _calc_block(label, formula, substitution, result_str, styles, ok=None):
    if ok is True:    res_color = "#1e8449"
    elif ok is False: res_color = "#c0392b"
    else:             res_color = "#1a5276"
    rows = [
        [Paragraph(f"<b>{label}</b>", styles["Normal2"]), ""],
        [Paragraph(f"  Fórmula:       {formula}",      styles["FormulaLine"]), ""],
        [Paragraph(f"  Sustitución:   = {substitution}", styles["FormulaLine"]), ""],
        [Paragraph(f'  <font color="{res_color}"><b>Resultado:      {result_str}</b></font>', styles["ResultLine"]), ""],
    ]
    t = Table(rows, colWidths=[W*0.7, W*0.3])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), C_FORMULA),
        ("BACKGROUND",(0,3),(1,3),   C_GREEN_BG if ok else (C_RED_BG if ok is False else C_FORMULA)),
        ("GRID",      (0,0),(-1,-1), 0.3, colors.HexColor("#c8d8f0")),
        ("SPAN",      (0,0),(1,0)), ("SPAN",(0,1),(1,1)),
        ("SPAN",      (0,2),(1,2)), ("SPAN",(0,3),(1,3)),
        ("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2),
        ("LEFTPADDING",(0,0),(-1,-1),6),
    ]))
    return t

def _param_table(data_dict, styles, cols=4):
    items = [(k, f"{v:.2f}" if isinstance(v, float) else str(v))
             for k,v in data_dict.items() if v is not None]
    if not items: return sp(2)
    rows, row = [], []
    for i,(k,v) in enumerate(items):
        row += [Paragraph(f"<b>{k}</b>", styles["Normal2"]), Paragraph(v, styles["Normal2"])]
        if (i+1) % cols == 0: rows.append(row); row=[]
    if row:
        while len(row) < cols*2: row.append(Paragraph("", styles["Normal2"]))
        rows.append(row)
    t = Table(rows, colWidths=[W/(cols*2)]*cols*2)
    t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.3,colors.lightgrey),("BACKGROUND",(0,0),(-1,-1),C_GREY),("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),("LEFTPADDING",(0,0),(-1,-1),4)]))
    return t

C_ORANGE = colors.HexColor("#e67e22")

def _survey_table(df, lim_map, min_vals, styles, cut_cols=None,
                  ctrl_in_frame=False, ctrl_side=None, max_vals=None):
    """
    cut_cols: columnas OR/OL en Caso 2 — naranja si val > eff_lim.
    ctrl_in_frame / ctrl_side: reducen el límite −70 mm en la última fila.
    max_vals: dict {MAX_OR, MAX_OL, ...} — resaltado oscuro en el valor máximo de cut_cols.
    """
    cut_cols     = cut_cols or []
    max_vals     = max_vals or {}
    last_data_ri = len(df)
    cols   = list(df.columns)
    header = [Paragraph("<b>#</b>", styles["Normal2"])] + [Paragraph(f"<b>{c}</b>", styles["Normal2"]) for c in cols]
    rows   = [header]
    for idx, row in df.iterrows():
        cells = [Paragraph(str(idx+1), styles["Normal2"])]
        for c in cols:
            val = row[c]
            cells.append(Paragraph(f"{val:.1f}" if isinstance(val, (int, float)) else str(val), styles["Normal2"]))
        rows.append(cells)
    col_w = [12*mm] + [(W-12*mm)/len(cols)]*len(cols)
    t = Table(rows, colWidths=col_w)
    cmds = [
        ("GRID",(0,0),(-1,-1),0.3,colors.lightgrey),
        ("BACKGROUND",(0,0),(-1,0),C_SUBHEAD),("TEXTCOLOR",(0,0),(-1,0),C_WHITE),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("BACKGROUND",(0,1),(0,-1),C_GREY),
        ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("LEFTPADDING",(0,0),(-1,-1),4),("ALIGN",(0,0),(-1,-1),"CENTER"),
    ]
    for ri,(_, row) in enumerate(df.iterrows(), start=1):
        for ci, col in enumerate(cols, start=1):
            if col not in lim_map:
                continue
            val = row[col]; lim = lim_map[col]
            min_val = min_vals.get(f"MIN_{col}")
            max_val = max_vals.get(f"MAX_{col}")
            if not isinstance(val, (int, float)):
                continue
            eff_lim = lim
            if ctrl_in_frame and ri == last_data_ri:
                if col == "OR" and ctrl_side == "R":
                    eff_lim = lim - 70
                elif col == "OL" and ctrl_side == "L":
                    eff_lim = lim - 70
            if col in cut_cols:
                # OR/OL Caso 2: naranja si está bajo el límite (gap insuficiente → requiere corte);
                # naranja oscuro en el valor máximo (DIF = LIMIT − MAX)
                if val < eff_lim:
                    if max_val is not None and abs(val - max_val) < 0.001:
                        cmds += [("BACKGROUND",(ci,ri),(ci,ri),C_RED_DARK),
                                  ("TEXTCOLOR",(ci,ri),(ci,ri),C_WHITE),
                                  ("FONTNAME",(ci,ri),(ci,ri),"Helvetica-Bold")]
                    else:
                        cmds += [("BACKGROUND",(ci,ri),(ci,ri),C_ORANGE),
                                  ("TEXTCOLOR",(ci,ri),(ci,ri),C_WHITE),
                                  ("FONTNAME",(ci,ri),(ci,ri),"Helvetica-Bold")]
            else:
                if val < eff_lim:
                    if min_val is not None and abs(val-min_val)<0.001:
                        cmds += [("BACKGROUND",(ci,ri),(ci,ri),C_RED_DARK),("TEXTCOLOR",(ci,ri),(ci,ri),C_WHITE),("FONTNAME",(ci,ri),(ci,ri),"Helvetica-Bold")]
                    else:
                        cmds.append(("BACKGROUND",(ci,ri),(ci,ri),C_RED_BG))
    t.setStyle(TableStyle(cmds)); return t

def _diagram_block(title, lines, styles):
    """Caja esquemática con texto monoespaciado (esquema no proporcional)."""
    content = [[Paragraph(f"<b>{title}</b>", styles["SubHead2"])]]
    for line in lines:
        safe = line.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
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


def _dg_bc_calc(ts, tksw, tk, bc_calc):
    tk2 = tk / 2
    return [
        "  Vista lateral del hueco (no proporcional):",
        "",
        "  pared                                          fondo del hueco",
        "  frontal                                               |",
        "    |                                                   |",
        "    +--------+---------------------------+----------+---+",
        "    |        |         CABINA            |  BC_CALC |25 |",
        "    | [TKSW] |        [TK / 2]           |          |mm |",
        "    +--------+---------------------------+----------+---+",
        "",
        f"    TKSW    = {tksw:.0f} mm",
        f"    TK/2    = {tk2:.0f} mm",
        f"    BC_CALC = {bc_calc:.0f} mm   (espacio libre detras de cabina)",
        f"    25 mm   (holgura minima de seguridad al fondo)",
        f"    TS      = {ts:.0f} mm  =  {tksw:.0f} + {tk2:.0f} + {bc_calc:.0f} + 25",
    ]


def _dg_lateral_limits(lwl, lol, lwr, lor, bks, offset_cabin, offset_side):
    return [
        "  Seccion transversal del hueco (no proporcional, vista superior):",
        "",
        f"  Cabina desplazada hacia: {offset_side}   OFFSET_CABIN = {offset_cabin:.0f} mm",
        "",
        "     LIMIT OL  LIMIT WL  [---BKS---]  LIMIT WR  LIMIT OR",
        "  ---[OL]------[WL]------[  CABINA ]-----[WR]------[OR]---",
        "",
        f"    LIMIT OL   = {lol:.1f} mm   |   LIMIT OR   = {lor:.1f} mm",
        f"    LIMIT WL   = {lwl:.1f} mm   |   LIMIT WR   = {lwr:.1f} mm",
        f"    BKS (dist. entre rieles de cabina) = {bks:.0f} mm",
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


def _summary_table(summary_list, styles):
    if not summary_list: return sp(2)
    header = [Paragraph(f"<b>{k}</b>", styles["Normal2"]) for k in summary_list[0]]
    rows   = [header] + [[Paragraph(str(v), styles["Normal2"]) for v in item.values()] for item in summary_list]
    t = Table(rows, colWidths=[W/len(summary_list[0])]*len(summary_list[0]))
    t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.3,colors.lightgrey),("BACKGROUND",(0,0),(-1,0),C_SUBHEAD),("TEXTCOLOR",(0,0),(-1,0),C_WHITE),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("BACKGROUND",(0,1),(-1,-1),C_GREY),("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),("LEFTPADDING",(0,0),(-1,-1),4)]))
    return t

# ════════════════════════════════════════════════════════════
def generate_report(project_params, calculated, survey_original,
                    survey_adjusted, lim_map, analysis,
                    optimizer_result, bs_result, survey_cols):

    best          = optimizer_result.get("best")          if optimizer_result else None
    all_solutions = optimizer_result.get("all_solutions", []) if optimizer_result else []
    step_log      = optimizer_result.get("step_log", [])  if optimizer_result else []

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    styles = _styles()
    story  = []
    p      = project_params

    def fv(key):
        v = p.get(key, calculated.get(key, 0.0))
        return float(v) if v is not None else 0.0
    def fs(key, d=2):
        v = p.get(key, calculated.get(key, 0.0))
        return f"{float(v):.{d}f}" if v is not None else "0.00"

    # ── PORTADA ──────────────────────────────────────────────
    tt = Table([
        [Paragraph("ELEVATOR SURVEY ANALYZER", styles["ReportTitle"])],
        [Paragraph("Reporte de cálculo con trazabilidad completa — incluyendo cada paso del optimizador", styles["ReportSub"])]
    ], colWidths=[W])
    tt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),C_HEADER),("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10)]))
    story += [tt, sp(4), Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y  %H:%M')}", styles["SmallCenter"]), sp(10)]

    # ── 1. PARÁMETROS DE ENTRADA ─────────────────────────────
    story += [_section_header("1. PARÁMETROS DE ENTRADA", styles), sp(4)]
    story += [Paragraph("1.1  Extraídos del PDF", styles["SubHead"])]
    story += [_param_table({k: p.get(k) for k in ["BS","BT","BK","BKS","TK","TKA","TKS","TSW","TKSW","TS","SF1","SF2","SG","TG","BGS","BKF1","BKF2"]}, styles), sp(6)]
    story += [Paragraph("1.2  Ingresados por el usuario", styles["SubHead"])]
    story += [_param_table({k: p.get(k) for k in ["BSR","FS","FRAME","RAIL","OFFSET_CABIN","OFFSET_SIDE","OMEGA_SIDE"]}, styles, cols=4), sp(8)]

    # ── 2. DIMENSIONES DE CABINA ─────────────────────────────
    story += [_section_header("2. DIMENSIONES DE CABINA", styles), sp(4)]
    cs        = fv("TK") + fv("TKA")
    tl        = cs + fv("TKS") + fv("TSW")
    bc_calc_v = fv("BC_CALC")
    tlbc      = tl + bc_calc_v
    story += [
        _calc_block("CS — Profundidad total de cabina",
            "CS = TK + TKA",
            f"{fs('TK')} + {fs('TKA')}",
            f"CS = {cs:.2f} mm", styles), sp(3),
        _calc_block("TL — Longitud total cabina a umbral",
            "TL = CS + TKS + TSW",
            f"{cs:.2f} + {fs('TKS')} + {fs('TSW')}",
            f"TL = {tl:.2f} mm", styles), sp(3),
        _calc_block("BC_CALC — Espacio libre detras de la cabina",
            "BC_CALC = TS - TKSW - (TK / 2) - 25",
            f"{fs('TS')} - {fs('TKSW')} - ({fs('TK')} / 2) - 25",
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
    lwr = fv("SF2") + fv("RAIL")/2
    lfr = fv("TKSW") - 150
    lwl = fv("SF1") + fv("RAIL")/2
    lfl = fv("TKSW") - 150
    _base_ol = fv("BKS")/2 + fv("RAIL")/2 - fv("BT")/2 - fv("FRAME")
    _off_c   = fv("OFFSET_CABIN")
    _off_s   = p.get("OFFSET_SIDE", "R")
    lor = _base_ol + _off_c if _off_s == "L" else _base_ol - _off_c
    lol = _base_ol - _off_c if _off_s == "L" else _base_ol + _off_c
    lob_raw = (fv("SG") - fv("TG")/2) * 0.3
    omega   = p.get("OMEGA_SIDE", "R")
    # Z siempre opuesto al Omega:
    # Omega=R → Z=L → LIMIT ZB usa SF1
    # Omega=L → Z=R → LIMIT ZB usa SF2
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
        _calc_block("LIMIT WR",  "LIMIT WR = SF2 + (RAIL / 2)",    f"{fs('SF2')} + ({fs('RAIL')} / 2)", f"LIMIT WR = {lwr:.2f} mm", styles), sp(3),
        _calc_block("LIMIT WL",  "LIMIT WL = SF1 + (RAIL / 2)",    f"{fs('SF1')} + ({fs('RAIL')} / 2)", f"LIMIT WL = {lwl:.2f} mm", styles), sp(3),
        _calc_block("Base OR/OL", "Base = (BKS/2) + (RAIL/2) − (BT/2) − FRAME",
            f"({fs('BKS')}/2) + ({fs('RAIL')}/2) − ({fs('BT')}/2) − {fs('FRAME')}",
            f"Base = {(fv('BKS')/2 + fv('RAIL')/2 - fv('BT')/2 - fv('FRAME')):.2f} mm", styles), sp(3),
        _calc_block("LIMIT OR",
            f"LIMIT OR = Base {'+ OFFSET_CABIN' if p.get('OFFSET_SIDE','R')=='L' else '− OFFSET_CABIN'}  (offset lado {p.get('OFFSET_SIDE','R')})",
            f"{(fv('BKS')/2 + fv('RAIL')/2 - fv('BT')/2 - fv('FRAME')):.2f} {'+' if p.get('OFFSET_SIDE','R')=='L' else '−'} {fs('OFFSET_CABIN')}",
            f"LIMIT OR = {lor:.2f} mm", styles), sp(3),
        _calc_block("LIMIT OL",
            f"LIMIT OL = Base {'− OFFSET_CABIN' if p.get('OFFSET_SIDE','R')=='L' else '+ OFFSET_CABIN'}  (offset lado {p.get('OFFSET_SIDE','R')})",
            f"{(fv('BKS')/2 + fv('RAIL')/2 - fv('BT')/2 - fv('FRAME')):.2f} {'−' if p.get('OFFSET_SIDE','R')=='L' else '+'} {fs('OFFSET_CABIN')}",
            f"LIMIT OL = {lol:.2f} mm", styles), sp(6),
        _diagram_block("Seccion transversal — Limites laterales",
            _dg_lateral_limits(lwl, lol, lwr, lor, fv("BKS"),
                               fv("OFFSET_CABIN"), p.get("OFFSET_SIDE","R")), styles), sp(6),
        Paragraph("3.2  Límites frontales", styles["SubHead"]),
        _calc_block("LIMIT FR",  "LIMIT FR = TKSW - 150",          f"{fs('TKSW')} - 150",               f"LIMIT FR = {lfr:.2f} mm", styles), sp(3),
        _calc_block("LIMIT FL",  "LIMIT FL = TKSW - 150",          f"{fs('TKSW')} - 150",               f"LIMIT FL = {lfl:.2f} mm", styles), sp(6),
        Paragraph("3.3  Límites Omega / Zona B", styles["SubHead"]),
        _calc_block("LIMIT OB (raw)", "LIMIT OB = (SG − (TG/2)) × 0.3",
            f"({fs('SG')} − ({fs('TG')}/2)) × 0.3",
            f"LIMIT OB raw = {lob_raw:.2f} mm", styles), sp(3),
        _calc_block("LIMIT ZB (raw)",
            f"LIMIT ZB = {zb_sf} × 0.3  (Z lado {z_side}, opuesto al Omega={omega})",
            f"{fs(zb_sf)} × 0.3",
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
    off_wr = lwr - wrt + (bsr - bs)/2
    off_wl = lwl - wlt + (bsr - bs)/2
    story += [
        Paragraph("Totales de la última fila de la matriz SURVEY:", styles["Note"]),
        _param_table({"WRT": wrt, "FRT": frt, "ORT": fv("ORT"), "WLT": wlt, "FLT": flt, "OLT": fv("OLT")}, styles, cols=3), sp(4),
        _calc_block("Offset FR", "Offset FR = LIMIT FR − FRT",
            f"{lfr:.2f} − {frt:.2f}", f"Offset FR = {off_fr:.2f} mm", styles), sp(3),
        _calc_block("Offset FL", "Offset FL = LIMIT FL − FLT",
            f"{lfl:.2f} − {flt:.2f}", f"Offset FL = {off_fl:.2f} mm", styles), sp(3),
        _calc_block("Offset WR", "Offset WR = LIMIT WR − WRT + ((BSR−BS)/2)",
            f"{lwr:.2f} − {wrt:.2f} + (({bsr:.2f}−{bs:.2f})/2) = {lwr:.2f} − {wrt:.2f} + {(bsr-bs)/2:.2f}",
            f"Offset WR = {off_wr:.2f} mm", styles), sp(3),
        _calc_block("Offset WL", "Offset WL = LIMIT WL − WLT + ((BSR−BS)/2)",
            f"{lwl:.2f} − {wlt:.2f} + (({bsr:.2f}−{bs:.2f})/2) = {lwl:.2f} − {wlt:.2f} + {(bsr-bs)/2:.2f}",
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
        if col in ("OR", "OL"):
            # DIF = LIMIT − MAX: positivo = incluso el MAX está bajo el límite (requiere corte)
            formula_text = f"DIF {col} = LIMIT {col} − MAX {col}"
            subst_text   = f"{lim:.2f} − {max_v:.2f}"
        else:
            formula_text = f"DIF {col} = LIMIT {col} − MIN {col}"
            subst_text   = f"{lim:.2f} − {min_v:.2f}"
        story += [_calc_block(f"DIF {col}",
            formula_text, subst_text,
            f"DIF {col} = {dif_v:.2f} mm  |  {off_c} valor(es) fuera de límite",
            styles, ok=(dif_v<=0)), sp(3)]

    max_rl = analysis["MAX_OFF_RL"]; max_fb = analysis["MAX_OFF_FB"]
    story += [sp(3),
        _calc_block("MAX OFF RL",
            "MAX OFF RL = max(DIF WR, DIF WL)  [OR/OL gestionados como restricción dura en optimizador]",
            f"max({analysis['DIF_WR']:.2f}, {analysis['DIF_WL']:.2f})",
            f"MAX OFF RL = {max_rl:.2f} mm", styles), sp(3),
        _calc_block("MAX OFF FB", "MAX OFF FB = max(DIF FR, DIF FL)",
            f"max({analysis['DIF_FR']:.2f}, {analysis['DIF_FL']:.2f})",
            f"MAX OFF FB = {max_fb:.2f} mm", styles), sp(8)]

    # ── 7. OPTIMIZACIÓN — CADA PASO ─────────────────────────
    story += [PageBreak(), _section_header("7. OPTIMIZACIÓN — TRAZABILIDAD COMPLETA DE CADA PASO", styles), sp(4)]

    story += [
        Paragraph("7.1  Parámetros del optimizador", styles["SubHead"]),
        _calc_block("Rango de búsqueda RL",
            "RL ∈ [−MAX OFF RL, +MAX OFF RL]  paso 0.5 mm",
            f"[{-max_rl:.2f}, {max_rl:.2f}]",
            f"Total pasos RL evaluados: {int(max_rl*2/0.5)+1}", styles), sp(3),
        _calc_block("Rango de búsqueda FB",
            "FB ∈ [−MAX OFF FB, +MAX OFF FB]  paso 0.5 mm",
            f"[{-max_fb:.2f}, {max_fb:.2f}]",
            f"Total pasos FB evaluados: {int(max_fb*2/0.5)+1}", styles), sp(4),
        Paragraph("Restricciones aplicadas en cada paso:", styles["SubHead2"]),
        Paragraph(f"  • Si RL < 0: |RL| ≤ LIMIT R = {lr:.2f} mm", styles["Normal2"]),
        Paragraph(f"  • Si RL > 0: |RL| ≤ LIMIT L = {ll:.2f} mm", styles["Normal2"]),
        Paragraph(f"  • Pared limitante: {'Sí — Parada ' + str(p.get('WALL_STOP','?')) + ' lado ' + str(p.get('WALL_SIDE','?')) if p.get('WALL_LIMITING') else 'No aplica'}", styles["Normal2"]),
        Paragraph(f"  • TSW={fs('TSW')} vs FS={fs('FS')} — FS−TSW={fv('FS')-fv('TSW'):.1f} mm — FB extra activo: {'Sí' if fv('FS') > fv('TSW') and p.get('WALL_LIMITING') else 'No'}", styles["Normal2"]),
        Paragraph(
            f"  • Controlador en frame: {'Sí — lado ' + str(p.get('CTRL_SIDE','?')) + ' → último nivel: LIMIT_O' + str(p.get('CTRL_SIDE','?')) + ' − 70 mm' if p.get('CTRL_IN_FRAME') else 'No'}",
            styles["Normal2"]),
        sp(4),
        _diagram_block("Diagrama de rango RL",
            _dg_rl(lr, ll, max_rl), styles), sp(4),
        _diagram_block("Diagrama de rango FB",
            _dg_fb(max_fb, fv("FB_MAX_BACK"), fv("BC_CALC"), fv("DIF_TSW_FS")), styles), sp(6),
    ]

    # Tabla de todos los pasos
    story += [Paragraph("7.2  Log de todos los pasos evaluados", styles["SubHead"]), sp(3)]

    valid_steps = [s for s in step_log if s.get("status") == "VALID"]

    story += [Paragraph(f"Total combinaciones evaluadas: {len(step_log)}  |  Válidas: {len(valid_steps)}", styles["Note"]), sp(3)]

    # Pasos VÁLIDOS — solo mostrar los que tienen el menor número de OFF
    best_total = best["total_off"] if best else None
    min_off_steps = [s for s in valid_steps if s.get("total_off") == best_total] if best_total is not None else valid_steps

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

    best_rl = best["rl"] if best else None
    best_fb = best["fb"] if best else None
    opt_pairs = {(s["rl"], s["fb"]) for s in all_solutions}

    # Encabezado
    hdr = [
        Paragraph("<b>RL</b>",      styles["Normal2"]),
        Paragraph("<b>FB</b>",      styles["Normal2"]),
        Paragraph("<b>FB aplic.</b>",styles["Normal2"]),
        Paragraph("<b>OFF</b>",     styles["Normal2"]),
        Paragraph("<b>WR</b>",      styles["Normal2"]),
        Paragraph("<b>FR</b>",      styles["Normal2"]),
        Paragraph("<b>OR</b>",      styles["Normal2"]),
        Paragraph("<b>WL</b>",      styles["Normal2"]),
        Paragraph("<b>FL</b>",      styles["Normal2"]),
        Paragraph("<b>OL</b>",      styles["Normal2"]),
        Paragraph("<b>Estado</b>",  styles["Normal2"]),
    ]
    valid_rows = [hdr]
    for s in min_off_steps:
        obc        = s.get("off_by_col", {})
        fb_aplic   = s.get("fb_applied", s["fb"])
        is_opt     = (s["rl"], s["fb"]) in opt_pairs
        estado     = Paragraph("✅ ÓPTIMO" if is_opt else "", styles["Normal2"])
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
        ("TOPPADDING", (0,0),(-1,-1), 2),("BOTTOMPADDING",(0,0),(-1,-1),2),
        ("LEFTPADDING",(0,0),(-1,-1), 3),("FONTSIZE",(0,1),(-1,-1),7),
    ]
    for ri, s in enumerate(min_off_steps, start=1):
        if (s["rl"], s["fb"]) in opt_pairs:
            cmds_v.append(("BACKGROUND", (0,ri),(-1,ri), C_BEST))
            cmds_v.append(("FONTNAME",   (0,ri),(-1,ri), "Helvetica-Bold"))
        obc = s.get("off_by_col",{})
        for ci, col in enumerate(["WR","FR","OR","WL","FL","OL"], start=4):
            if obc.get(col, 0) > 0:
                cmds_v.append(("BACKGROUND",(ci,ri),(ci,ri), C_RED_BG))
    t_valid.setStyle(TableStyle(cmds_v))
    story += [t_valid, sp(6)]

    # Resultado final optimizador
    story += [Paragraph("7.3  Resultado final", styles["SubHead"]), sp(3)]
    if best:
        n_sol     = len(all_solutions)
        best_pair_r = (best["rl"], best["fb"])
        # Ordenar: mejor solución primero
        sorted_sols = sorted(
            all_solutions,
            key=lambda s: (0 if (s["rl"], s["fb"]) == best_pair_r else 1, abs(s["rl"]) + abs(s["fb"]))
        )
        story += [
            _calc_block("Resumen de optimización",
                "Criterio 1: menor número de valores fuera de límite\nCriterio 2 (desempate): menor desplazamiento total |RL| + |FB aplicado|",
                f"Candidatos con mínimo OFF: {n_sol}  |  Valores fuera de límite: {best['total_off']}",
                f"Seleccionado: RL={best['rl']:.1f} mm, FB iterado={best['fb']:.1f} mm, FB aplicado={best.get('fb_applied', best['fb']):.1f} mm",
                styles, ok=(best["total_off"]==0)),
            sp(6),
        ]
        for idx_sol, sol in enumerate(sorted_sols):
            is_best   = (sol["rl"], sol["fb"]) == best_pair_r
            prefix    = "⭐ SELECCIONADA — " if is_best else ""
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
            # Caso 2: agregar CUT OR / CUT OL con ajuste de controlador en último nivel
            if not wall_limiting:
                lor_v        = lim_map["OR"]
                lol_v        = lim_map["OL"]
                last_sol_idx = len(sol_df) - 1
                cut_or_vals, cut_ol_vals = [], []
                for i, (or_v, ol_v) in enumerate(zip(sol_df["OR"], sol_df["OL"])):
                    or_lim = lor_v - 70 if (rpt_ctrl and rpt_ctrl_side == "R" and i == last_sol_idx) else lor_v
                    ol_lim = lol_v - 70 if (rpt_ctrl and rpt_ctrl_side == "L" and i == last_sol_idx) else lol_v
                    cut_or_vals.append(f"{or_lim - or_v:.1f}" if or_lim - or_v > 0 else "")
                    cut_ol_vals.append(f"{ol_lim - ol_v:.1f}" if ol_lim - ol_v > 0 else "")
                sol_df.insert(3, "CUT OR", cut_or_vals)
                sol_df.insert(7, "CUT OL", cut_ol_vals)
            story  += [_survey_table(sol_df, lim_map, sol_min, styles,
                                     cut_cols=rpt_cut_cols, max_vals=sol_max,
                                     ctrl_in_frame=rpt_ctrl, ctrl_side=rpt_ctrl_side), sp(3)]
            if not wall_limiting:
                story += [Paragraph(
                    "CUT OR = LIMIT OR − OR  /  CUT OL = LIMIT OL − OL  "
                    "(déficit vs límite mínimo; positivo = gap insuficiente → requiere corte; vacío = dentro del límite)",
                    styles["Note"]), sp(3)]
            sol_sum = []
            for col in survey_cols:
                cv  = [r[col] for r in sol["matrix"]]
                lim = lim_map[col]
                if col in ("OR", "OL"):
                    ext = max(cv); dif = lim - ext
                    off = sum(1 for v in cv if v < lim)
                    lbl = "Máximo (mm)"
                else:
                    ext = min(cv); dif = lim - ext
                    off = sum(1 for v in cv if v < lim)
                    lbl = "Mínimo (mm)"
                sol_sum.append({
                    "Columna":       col,
                    "Límite (mm)":   f"{lim:.2f}",
                    "Fuera límite":  off,
                    lbl:             f"{ext:.2f}",
                    "Dif vs Límite": f"{dif:.2f}",
                })
            story += [_summary_table(sol_sum, styles), sp(6)]
    else:
        story += [Paragraph("⚠️ No se encontró combinación válida.", styles["Normal2"]), sp(8)]

    # ── 8. BSR vs BS ─────────────────────────────────────────
    story += [PageBreak(), _section_header("8. ANÁLISIS BSR vs BS", styles), sp(4)]
    if not bs_result.get("needed"):
        story += [_calc_block("Condición","BSR ≥ BS  →  Sin ajuste requerido",
            f"{fs('BSR')} ≥ {fs('BS')}", "No se requiere ajuste de shaft", styles, ok=True), sp(6)]
    else:
        dif_bs = bs_result.get("dif_original", 0)
        story += [
            _calc_block("DIF BS","DIF BS = BS − BSR  (cuando BSR < BS)",
                f"{fs('BS')} − {fs('BSR')}", f"DIF BS = {dif_bs:.2f} mm", styles, ok=False), sp(4),
            Paragraph("Búsqueda del paso en los 3 rangos (paso 0.5 mm):", styles["SubHead2"]),
            _calc_block("Rango 1 — Zona ZB","Ciclos de 0 hasta LIMIT ZB",
                f"[0  →  {lzb:.2f}]","Buscando paso donde la resta de DIF BS llega a 0", styles), sp(3),
            _calc_block("Rango 2 — Zona OB","Ciclos de LIMIT ZB hasta (LIMIT ZB + LIMIT OB)",
                f"[{lzb:.2f}  →  {lzb+lob:.2f}]","Buscando paso donde la resta de DIF BS llega a 0", styles), sp(3),
            _calc_block("Rango 3 — Zona extendida","Ciclos de (LIMIT ZB + LIMIT OB) hasta 1000",
                f"[{lzb+lob:.2f}  →  1000]","Buscando paso donde la resta de DIF BS llega a 0", styles), sp(4),
        ]
        if bs_result.get("step") is not None:
            story += [_calc_block("✅ Resultado","Paso encontrado",
                f"Rango: {bs_result.get('range')}  |  Zona: {bs_result.get('range_name')}",
                f"Paso = {bs_result.get('step')} mm", styles, ok=True)]
        else:
            story += [Paragraph("⚠️ No se encontró paso en ningún rango.", styles["Normal2"])]
        story.append(sp(8))

    # ── PIE ──────────────────────────────────────────────────
    story += [sp(8), HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey), sp(4),
              Paragraph("Elevator Survey Analyzer — Reporte generado automáticamente", styles["SmallCenter"]),
              Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["SmallCenter"])]

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()
