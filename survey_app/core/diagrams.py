"""
Diagramas SVG del posicionamiento físico del bloque cabina.
Generados con datos reales del survey y la solución óptima.

SVG compatible con:
  - Streamlit (via st.components.v1.html)
  - ReportLab PDF (via svglib.svg2rlg)
Por eso NO se usan <marker> ni <defs>: las flechas se dibujan como <polygon>.

Dos vistas:
  - lateral_svg():  sección transversal (eje izquierda↔derecha)
  - frontal_svg():  perfil longitudinal (eje adelante↔atrás)
"""


def _f(v: float) -> str:
    return f"{v:.0f}"


# ── Helpers de dibujo (sin markers/defs) ─────────────────────
def _head(x, y, direction, color, size=5):
    """Punta de flecha como polígono. direction ∈ {left,right,up,down}."""
    s = size
    if direction == "right":
        pts = f"{x:.1f},{y:.1f} {x-s:.1f},{y-s*0.7:.1f} {x-s:.1f},{y+s*0.7:.1f}"
    elif direction == "left":
        pts = f"{x:.1f},{y:.1f} {x+s:.1f},{y-s*0.7:.1f} {x+s:.1f},{y+s*0.7:.1f}"
    elif direction == "up":
        pts = f"{x:.1f},{y:.1f} {x-s*0.7:.1f},{y+s:.1f} {x+s*0.7:.1f},{y+s:.1f}"
    else:  # down
        pts = f"{x:.1f},{y:.1f} {x-s*0.7:.1f},{y-s:.1f} {x+s*0.7:.1f},{y-s:.1f}"
    return f'<polygon points="{pts}" fill="{color}"/>'


def _dim(x1, x2, y, label, color="#666", fg="#666", below=False):
    """Línea de cota horizontal con dos puntas y etiqueta."""
    ytext = y + 14 if below else y - 7
    return (
        f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" '
        f'stroke="{color}" stroke-width="1"/>'
        f'{_head(x1, y, "left", color)}'
        f'{_head(x2, y, "right", color)}'
        f'<text x="{(x1+x2)/2:.1f}" y="{ytext:.1f}" text-anchor="middle" '
        f'font-size="10" fill="{fg}">{label}</text>'
    )


def _arrow(x1, x2, y, label, color):
    """Flecha simple (una punta al final) con etiqueta debajo."""
    direction = "right" if x2 >= x1 else "left"
    return (
        f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" '
        f'stroke="{color}" stroke-width="2"/>'
        f'{_head(x2, y, direction, color, 6)}'
        f'<text x="{(x1+x2)/2:.1f}" y="{y+16:.1f}" text-anchor="middle" '
        f'font-size="11" fill="{color}" font-weight="bold">{label}</text>'
    )


def _badge(cx, cy, label, val, lim, bg, fg, is_max=False):
    """Etiqueta rectangular con valor y límite."""
    sym = "X" if (val > lim if is_max else val < lim) else "OK"
    return (
        f'<rect x="{cx-29:.1f}" y="{cy-13:.1f}" width="58" height="26" rx="4" '
        f'fill="{bg}" fill-opacity="0.92"/>'
        f'<text x="{cx:.1f}" y="{cy-1:.1f}" text-anchor="middle" font-size="10" '
        f'fill="{fg}" font-weight="bold">{label} {_f(val)}</text>'
        f'<text x="{cx:.1f}" y="{cy+10:.1f}" text-anchor="middle" font-size="8" '
        f'fill="{fg}">lim {_f(lim)} {sym}</text>'
    )


def _state_colors(val, lim, is_max=False):
    """(stroke/bg, texto). Verde dentro, naranja cerca, rojo fuera."""
    diff = (val - lim) if is_max else (lim - val)
    if diff < 0:   return "#E24B4A", "#FCEBEB"   # rojo  (fuera)
    if diff < 10:  return "#EF9F27", "#412402"   # naranja (cerca)
    return "#3B6D11", "#EAF3DE"                   # verde (OK)


# ════════════════════════════════════════════════════════════
# VISTA LATERAL — sección transversal
# ════════════════════════════════════════════════════════════
def lateral_svg(params: dict, limits: dict, solution: dict | None) -> str:
    bs    = float(params.get("BS",   1800))
    bsr   = float(params.get("BSR",  bs))
    bks   = float(params.get("BKS",  1200))
    rail  = float(params.get("RAIL", 12))
    sf1   = float(params.get("SF1",  280))
    sf2   = float(params.get("SF2",  280))
    bt    = float(params.get("BT",   900))

    cabin_w = bks + 2 * rail
    rl      = float(solution["rl"]) if solution else 0.0

    lim_wr = float(limits.get("LIMIT_WR", sf2))
    lim_wl = float(limits.get("LIMIT_WL", sf1))
    lim_or = float(limits.get("LIMIT_OR", 110))
    lim_ol = float(limits.get("LIMIT_OL", 110))

    if solution and solution.get("matrix"):
        mat = solution["matrix"]
        wr_val = min(r["WR"] for r in mat)
        wl_val = min(r["WL"] for r in mat)
        or_val = max(r["OR"] for r in mat)
        ol_val = max(r["OL"] for r in mat)
    else:
        wr_val, wl_val, or_val, ol_val = sf2, sf1, 100, 100

    wr_bg, wr_fg = _state_colors(wr_val, lim_wr)
    wl_bg, wl_fg = _state_colors(wl_val, lim_wl)
    or_bg, or_fg = _state_colors(or_val, lim_or, True)
    ol_bg, ol_fg = _state_colors(ol_val, lim_ol, True)

    VW, VH = 640, 300
    PAD_L, PAD_R, PAD_T, PAD_B = 20, 20, 50, 70
    scale = (VW - PAD_L - PAD_R) / bs

    sx  = PAD_L
    sw  = bs * scale
    scx = sx + sw / 2
    sy  = PAD_T + 8
    sh  = VH - PAD_T - PAD_B - 16

    cx  = sx + (sf1 - rl) * scale     # rl<0 → bloque a la derecha
    cw  = cabin_w * scale
    ccx = cx + cw / 2
    cy  = sy + (sh - sh * 0.7) / 2
    ch  = sh * 0.7

    door_x = ccx - (bt * scale) / 2
    door_w = bt * scale

    parts = [
        f'<svg viewBox="0 0 {VW} {VH}" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;max-width:{VW}px;font-family:system-ui,sans-serif;display:block;margin:0 auto">',
        f'<text x="{scx:.1f}" y="16" text-anchor="middle" font-size="12" fill="#888">'
        f'BS = {_f(bs)} mm  (BSR = {_f(bsr)} mm)</text>',
        # SF zonas
        f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{sf1*scale:.1f}" height="{sh:.1f}" fill="#888" fill-opacity="0.08"/>',
        f'<rect x="{sx+sw-sf2*scale:.1f}" y="{sy:.1f}" width="{sf2*scale:.1f}" height="{sh:.1f}" fill="#888" fill-opacity="0.08"/>',
        # Hueco
        f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{sw:.1f}" height="{sh:.1f}" rx="3" fill="none" stroke="#888" stroke-width="2"/>',
        # Limites WL/WR
        f'<line x1="{sx+lim_wl*scale:.1f}" y1="{sy-4:.1f}" x2="{sx+lim_wl*scale:.1f}" y2="{sy+sh+4:.1f}" stroke="{wl_bg}" stroke-width="1" stroke-dasharray="4,3"/>',
        f'<line x1="{sx+sw-lim_wr*scale:.1f}" y1="{sy-4:.1f}" x2="{sx+sw-lim_wr*scale:.1f}" y2="{sy+sh+4:.1f}" stroke="{wr_bg}" stroke-width="1" stroke-dasharray="4,3"/>',
        # Bloque cabina
        f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cw:.1f}" height="{ch:.1f}" rx="3" fill="#E6F1FB" stroke="#185FA5" stroke-width="2"/>',
        f'<text x="{ccx:.1f}" y="{cy+ch/2-5:.1f}" text-anchor="middle" font-size="11" fill="#185FA5" font-weight="bold">BKS + 2 RAIL</text>',
        f'<text x="{ccx:.1f}" y="{cy+ch/2+9:.1f}" text-anchor="middle" font-size="10" fill="#378ADD">{_f(cabin_w)} mm</text>',
        # Apertura puerta
        f'<rect x="{door_x:.1f}" y="{cy+ch-5:.1f}" width="{door_w:.1f}" height="10" fill="#185FA5" fill-opacity="0.15"/>',
        f'<text x="{ccx:.1f}" y="{cy+ch+18:.1f}" text-anchor="middle" font-size="10" fill="#185FA5">BT = {_f(bt)} mm</text>',
        # Badges laterales
        _badge(sx + wl_val*scale/2,        sy+sh/2, "WL", wl_val, lim_wl, wl_bg, wl_fg),
        _badge(sx + sw - wr_val*scale/2,   sy+sh/2, "WR", wr_val, lim_wr, wr_bg, wr_fg),
        # Badges apertura OL/OR
        _badge(max(sx+30, door_x - ol_val*scale/2 - 2), cy+ch/2, "OL", ol_val, lim_ol, ol_bg, ol_fg, True),
        _badge(min(sx+sw-30, door_x+door_w + or_val*scale/2 + 2), cy+ch/2, "OR", or_val, lim_or, or_bg, or_fg, True),
        # SF labels
        f'<text x="{sx+sf1*scale/2:.1f}" y="{sy+sh+16:.1f}" text-anchor="middle" font-size="10" fill="#999">SF1={_f(sf1)}</text>',
        f'<text x="{sx+sw-sf2*scale/2:.1f}" y="{sy+sh+16:.1f}" text-anchor="middle" font-size="10" fill="#999">SF2={_f(sf2)}</text>',
    ]
    if abs(rl) >= 0.5:
        parts.append(_arrow(scx, scx - rl*scale, sy+sh+44, f"RL = {rl:+.1f} mm", "#BA7517"))
    parts.append("</svg>")
    return "".join(parts)


# ════════════════════════════════════════════════════════════
# VISTA FRONTAL — perfil longitudinal
# ════════════════════════════════════════════════════════════
def frontal_svg(params: dict, limits: dict, solution: dict | None) -> str:
    ts    = float(params.get("TS",   1500))
    fs    = float(params.get("FS",   200))
    tsw   = float(params.get("TSW",  120))
    tksw  = float(params.get("TKSW", 230))
    tl    = float(limits.get("TL",   ts * 0.7))
    bc    = float(limits.get("BC_CALC", ts - tl))
    fb    = float(solution.get("fb_applied", solution.get("fb", 0))) if solution else 0.0

    lim_fr = float(limits.get("LIMIT_FR", tksw - 150))

    if solution and solution.get("matrix"):
        mat = solution["matrix"]
        fr_val = min(r["FR"] for r in mat)
    else:
        fr_val = tksw

    fr_bg, fr_fg = _state_colors(fr_val, lim_fr)

    VW, VH = 640, 270
    PAD_L, PAD_R, PAD_T, PAD_B = 30, 30, 46, 56
    scale = (VW - PAD_L - PAD_R) / ts

    sx = PAD_L
    sw = ts * scale
    sy = PAD_T
    sh = VH - PAD_T - PAD_B

    fs_w   = fs  * scale
    tsw_w  = tsw * scale
    cx     = sx + (tksw + fb) * scale
    cw     = tl * scale
    bc_x   = cx + cw
    bc_w   = bc * scale
    mid_y  = sy + sh / 2
    rail_x = sx + (tksw + fb) * scale

    parts = [
        f'<svg viewBox="0 0 {VW} {VH}" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;max-width:{VW}px;font-family:system-ui,sans-serif;display:block;margin:0 auto">',
        f'<text x="{sx+sw/2:.1f}" y="16" text-anchor="middle" font-size="12" fill="#888">TS = {_f(ts)} mm</text>',
        # FS zona
        f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{fs_w:.1f}" height="{sh:.1f}" fill="#EF9F27" fill-opacity="0.10" rx="3"/>',
        f'<text x="{sx+fs_w/2:.1f}" y="{sy+sh+15:.1f}" text-anchor="middle" font-size="10" fill="#BA7517">FS={_f(fs)}</text>',
        # TSW zona
        f'<rect x="{sx+fs_w-tsw_w:.1f}" y="{sy+sh*0.35:.1f}" width="{tsw_w:.1f}" height="{sh*0.3:.1f}" fill="#185FA5" fill-opacity="0.15" rx="2"/>',
        f'<text x="{sx+fs_w-tsw_w/2:.1f}" y="{sy-4:.1f}" text-anchor="middle" font-size="9" fill="#185FA5">TSW={_f(tsw)}</text>',
        # Hueco
        f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{sw:.1f}" height="{sh:.1f}" rx="3" fill="none" stroke="#888" stroke-width="2"/>',
        # Bloque cabina
        f'<rect x="{cx:.1f}" y="{sy+sh*0.15:.1f}" width="{cw:.1f}" height="{sh*0.7:.1f}" rx="3" fill="#E6F1FB" stroke="#185FA5" stroke-width="1.5"/>',
        f'<text x="{cx+cw/2:.1f}" y="{mid_y-3:.1f}" text-anchor="middle" font-size="10" fill="#185FA5" font-weight="bold">TL = {_f(tl)} mm</text>',
        # BC zona
        f'<rect x="{bc_x:.1f}" y="{sy+sh*0.3:.1f}" width="{bc_w:.1f}" height="{sh*0.4:.1f}" fill="#7F77DD" fill-opacity="0.12" rx="2"/>',
        f'<text x="{bc_x+bc_w/2:.1f}" y="{mid_y+4:.1f}" text-anchor="middle" font-size="9" fill="#534AB7">BC={_f(bc)}</text>',
        # Centro riel
        f'<circle cx="{rail_x:.1f}" cy="{mid_y:.1f}" r="7" fill="#185FA5" fill-opacity="0.85"/>',
        # Limite FR
        f'<line x1="{sx+lim_fr*scale:.1f}" y1="{sy-4:.1f}" x2="{sx+lim_fr*scale:.1f}" y2="{sy+sh+4:.1f}" stroke="{fr_bg}" stroke-width="1.2" stroke-dasharray="5,3"/>',
        f'<text x="{sx+lim_fr*scale:.1f}" y="{sy-6:.1f}" text-anchor="middle" font-size="9" fill="{fr_bg}">LIM FR/FL</text>',
        # FR dimension
        _dim(sx, rail_x, sy+sh*0.9, "", fr_bg, fr_bg),
        f'<rect x="{(sx+rail_x)/2-30:.1f}" y="{sy+sh*0.9+4:.1f}" width="60" height="17" rx="3" fill="{fr_bg}" fill-opacity="0.92"/>',
        f'<text x="{(sx+rail_x)/2:.1f}" y="{sy+sh*0.9+16:.1f}" text-anchor="middle" font-size="10" fill="{fr_fg}" font-weight="bold">FR {_f(fr_val)}</text>',
        # TKSW label
        f'<text x="{sx+tksw*scale/2:.1f}" y="{sy+sh+15:.1f}" text-anchor="middle" font-size="10" fill="#888">TKSW={_f(tksw)}</text>',
    ]
    if abs(fb) >= 0.5:
        parts.append(_arrow(sx+tksw*scale, rail_x, sy+sh+40, f"FB = {fb:+.1f} mm", "#BA7517"))
    parts.append("</svg>")
    return "".join(parts)


# ── Wrapper HTML para Streamlit (components.html) ───────────
def render_diagrams_html(params: dict, limits: dict, solution: dict | None) -> str:
    lat = lateral_svg(params, limits, solution)
    fro = frontal_svg(params, limits, solution)
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>body{{margin:0;padding:0;background:transparent;font-family:system-ui,sans-serif}}
.lbl{{font-size:12px;color:#888;margin:0 0 6px;font-weight:600;text-transform:uppercase;letter-spacing:.06em}}
.box{{margin-bottom:20px}}</style></head>
<body>
  <div class="box">
    <p class="lbl">Vista superior — sección transversal (lateral)</p>
    {lat}
  </div>
  <div class="box">
    <p class="lbl">Vista lateral — perfil longitudinal (frontal)</p>
    {fro}
  </div>
</body></html>"""
