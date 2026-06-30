"""
Diagrama de planta (vista superior) del encaje de la cabina en el shaft.
Una imagen POR PISO, usando los valores de la matriz de la solución seleccionada.

Vista superior (mirando desde arriba):
  - Eje horizontal = ancho   (WL a la izquierda, WR a la derecha)
  - Eje vertical   = profundidad (FRENTE abajo = puertas; FONDO arriba)
  - Cabina = bloque rígido BKS + 2·RAIL (ancho) × TL (profundidad)
  - Apertura de puerta (BT) en el frente, con OL/OR a los lados
  - FR/FL = distancia de la pared frontal al riel (frente de la cabina)

SVG sin <marker>/<defs> → compatible con Streamlit (components.html) y
ReportLab (svglib.svg2rlg).
"""


def _f(v) -> str:
    try:
        return f"{float(v):.0f}"
    except Exception:
        return str(v)


def _state(value, lim, is_max=False):
    """(color_fondo, color_texto, simbolo). Verde dentro, naranja al límite, rojo fuera.

    is_max=False (WR/WL/FR/FL): seguro = value >= lim. Margen = value - lim.
    is_max=True  (OR/OL):       seguro = value <= lim. Margen = lim - value.
    """
    margin = (lim - value) if is_max else (value - lim)
    if margin < 0:   return "#E24B4A", "#FCEBEB", "X"    # rojo  (fuera de límite)
    if margin < 10:  return "#EF9F27", "#412402", "~"    # naranja (al límite)
    return "#3B6D11", "#EAF3DE", "OK"                    # verde (dentro)


def _clearance_px(v, vmax=300.0, lo=14.0, hi=92.0):
    """Mapea una holgura (mm) a píxeles de hueco visual (esquemático, comparable entre pisos)."""
    try:
        v = max(0.0, float(v))
    except Exception:
        v = 0.0
    px = lo + (min(v, vmax) / vmax) * (hi - lo)
    return px


def _label_box(cx, cy, text, sub, bg, fg, w=70, h=26):
    return (
        f'<rect x="{cx-w/2:.1f}" y="{cy-h/2:.1f}" width="{w}" height="{h}" rx="4" '
        f'fill="{bg}" fill-opacity="0.95"/>'
        f'<text x="{cx:.1f}" y="{cy-2:.1f}" text-anchor="middle" font-size="10" '
        f'fill="{fg}" font-weight="bold">{text}</text>'
        f'<text x="{cx:.1f}" y="{cy+10:.1f}" text-anchor="middle" font-size="8" '
        f'fill="{fg}">{sub}</text>'
    )


def floor_plan_svg(params: dict, limits: dict, row: dict, floor_idx: int,
                   lim_map: dict, ctrl_in_frame=False, ctrl_side=None,
                   is_last=False) -> str:
    """SVG de la planta de UN piso, con los valores de la fila `row` (matriz solución)."""
    bks   = float(params.get("BKS",  1200))
    rail  = float(params.get("RAIL", 12))
    bt    = float(params.get("BT",   900))
    cabin_w = bks + 2 * rail

    wl = float(row.get("WL", 0)); wr = float(row.get("WR", 0))
    fl = float(row.get("FL", 0)); fr = float(row.get("FR", 0))
    ol = float(row.get("OL", 0)); orr = float(row.get("OR", 0))

    lim_wl = float(lim_map.get("WL", 0)); lim_wr = float(lim_map.get("WR", 0))
    lim_fl = float(lim_map.get("FL", 0)); lim_fr = float(lim_map.get("FR", 0))
    lim_ol = float(lim_map.get("OL", 0)); lim_or = float(lim_map.get("OR", 0))

    # Controlador en frame reduce el límite OR/OL en el último piso
    if ctrl_in_frame and is_last:
        if ctrl_side == "R": lim_or -= 70
        if ctrl_side == "L": lim_ol -= 70

    wl_bg, wl_fg, wl_s = _state(wl, lim_wl)
    wr_bg, wr_fg, wr_s = _state(wr, lim_wr)
    fl_bg, fl_fg, fl_s = _state(fl, lim_fl)
    fr_bg, fr_fg, fr_s = _state(fr, lim_fr)
    ol_bg, ol_fg, ol_s = _state(ol, lim_ol, is_max=True)
    or_bg, or_fg, or_s = _state(orr, lim_or, is_max=True)

    # ── Lienzo (bandas fijas → todo cabe siempre) ───────────
    VW, VH = 520, 400

    # Horizontal: la cabina se desplaza según la asimetría WL/WR
    gWL = _clearance_px(wl, lo=18, hi=78)
    gWR = _clearance_px(wr, lo=18, hi=78)
    cab_x = 70 + gWL
    cab_w = max(200, VW - 140 - gWL - gWR)
    cab_r = cab_x + cab_w
    wall_l = cab_x - gWL
    wall_r = cab_r + gWR

    # Vertical: bandas fijas (fondo arriba, frente abajo)
    cab_y  = 62
    cab_h  = 210
    cab_b  = cab_y + cab_h
    wall_back = cab_y - 22
    gFL = _clearance_px(fl, lo=16, hi=42)
    gFR = _clearance_px(fr, lo=16, hi=42)
    wall_front_l = cab_b + gFL
    wall_front_r = cab_b + gFR

    # Apertura de puerta (BT) centrada en el frente
    bt_px  = cab_w * (bt / cabin_w) if cabin_w else cab_w * 0.7
    door_x = cab_x + (cab_w - bt_px) / 2
    door_r = door_x + bt_px

    p = []
    p.append(
        f'<svg viewBox="0 0 {VW} {VH}" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;max-width:{VW}px;font-family:system-ui,sans-serif;display:block;margin:0 auto">'
    )
    p.append(f'<text x="{VW/2:.1f}" y="22" text-anchor="middle" font-size="13" fill="#185FA5" font-weight="bold">PISO {floor_idx + 1}</text>')
    p.append(f'<text x="{VW/2:.1f}" y="36" text-anchor="middle" font-size="9" fill="#999">vista superior (planta) — esquemático</text>')

    # Paredes del shaft
    p.append(f'<line x1="{wall_l:.1f}" y1="{wall_back:.1f}" x2="{wall_r:.1f}" y2="{wall_back:.1f}" stroke="#888" stroke-width="2.5"/>')
    p.append(f'<line x1="{wall_l:.1f}" y1="{wall_back:.1f}" x2="{wall_l:.1f}" y2="{wall_front_l:.1f}" stroke="#888" stroke-width="2.5"/>')
    p.append(f'<line x1="{wall_r:.1f}" y1="{wall_back:.1f}" x2="{wall_r:.1f}" y2="{wall_front_r:.1f}" stroke="#888" stroke-width="2.5"/>')
    p.append(f'<line x1="{wall_l:.1f}" y1="{wall_front_l:.1f}" x2="{wall_r:.1f}" y2="{wall_front_r:.1f}" stroke="#888" stroke-width="2.5"/>')
    p.append(f'<text x="{(wall_l+wall_r)/2:.1f}" y="{max(wall_front_l,wall_front_r)+14:.1f}" text-anchor="middle" font-size="9" fill="#999">PARED FRONTAL (puertas)</text>')

    # Bloque cabina
    p.append(f'<rect x="{cab_x:.1f}" y="{cab_y:.1f}" width="{cab_w:.1f}" height="{cab_h:.1f}" rx="3" fill="#E6F1FB" stroke="#185FA5" stroke-width="2"/>')
    p.append(f'<text x="{cab_x+cab_w/2:.1f}" y="{cab_y+cab_h/2-4:.1f}" text-anchor="middle" font-size="11" fill="#185FA5" font-weight="bold">CABINA</text>')
    p.append(f'<text x="{cab_x+cab_w/2:.1f}" y="{cab_y+cab_h/2+9:.1f}" text-anchor="middle" font-size="9" fill="#378ADD">BKS+2RAIL = {_f(cabin_w)} mm</text>')

    # Rieles (esquinas frontales)
    p.append(f'<circle cx="{cab_x:.1f}" cy="{cab_b:.1f}" r="4" fill="#185FA5"/>')
    p.append(f'<circle cx="{cab_r:.1f}" cy="{cab_b:.1f}" r="4" fill="#185FA5"/>')

    # Apertura de puerta (BT)
    p.append(f'<line x1="{door_x:.1f}" y1="{cab_b:.1f}" x2="{door_r:.1f}" y2="{cab_b:.1f}" stroke="#185FA5" stroke-width="3"/>')
    p.append(f'<text x="{(door_x+door_r)/2:.1f}" y="{cab_b-5:.1f}" text-anchor="middle" font-size="8" fill="#185FA5">apertura BT={_f(bt)}</text>')

    # ── Badges (columnas izquierda/derecha + apertura) ──────
    # WL / WR a media altura
    p.append(_label_box(wall_l - 37, cab_y + cab_h*0.40, f"WL {_f(wl)}", f"lim {_f(lim_wl)} {wl_s}", wl_bg, wl_fg))
    p.append(_label_box(wall_r + 37, cab_y + cab_h*0.40, f"WR {_f(wr)}", f"lim {_f(lim_wr)} {wr_s}", wr_bg, wr_fg))
    # FL / FR más abajo (cerca de los rieles frontales)
    p.append(_label_box(wall_l - 37, cab_y + cab_h*0.78, f"FL {_f(fl)}", f"lim {_f(lim_fl)} {fl_s}", fl_bg, fl_fg))
    p.append(_label_box(wall_r + 37, cab_y + cab_h*0.78, f"FR {_f(fr)}", f"lim {_f(lim_fr)} {fr_s}", fr_bg, fr_fg))
    # OL / OR en la apertura (debajo de la pared frontal)
    oy = max(wall_front_l, wall_front_r) + 32
    p.append(_label_box(cab_x + cab_w*0.30, oy, f"OL {_f(ol)}", f"lim {_f(lim_ol)} {ol_s}", ol_bg, ol_fg, w=66))
    p.append(_label_box(cab_x + cab_w*0.70, oy, f"OR {_f(orr)}", f"lim {_f(lim_or)} {or_s}", or_bg, or_fg, w=66))

    p.append("</svg>")
    return "".join(p)


def render_floor_plans_html(params: dict, limits: dict, solution: dict | None,
                            lim_map: dict, ctrl_in_frame=False, ctrl_side=None) -> str:
    """HTML con la planta de TODOS los pisos (matriz solución) para components.html."""
    if not solution or not solution.get("matrix"):
        return "<p style='color:#888;font-family:system-ui'>No hay solución para graficar.</p>"
    mat = solution["matrix"]
    n   = len(mat)
    blocks = []
    for i, row in enumerate(mat):
        svg = floor_plan_svg(params, limits, row, i, lim_map,
                             ctrl_in_frame, ctrl_side, is_last=(i == n - 1))
        blocks.append(f'<div style="margin-bottom:18px">{svg}</div>')
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<style>body{margin:0;padding:0;background:transparent}</style></head><body>'
        + "".join(blocks) +
        '</body></html>'
    )
