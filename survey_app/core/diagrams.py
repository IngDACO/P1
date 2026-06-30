"""
Diagramas SVG del posicionamiento físico del bloque cabina.
Generados con datos reales del survey y la solución óptima.
Dos vistas: sección transversal (lateral) y perfil longitudinal (frontal).
"""


def _fmt(v: float) -> str:
    return f"{v:.0f}"


def lateral_diagram(params: dict, limits: dict, solution: dict | None) -> str:
    """
    Vista superior (sección transversal) — eje lateral.
    Muestra: hueco, bloque cabina, WR/WL, OR/OL, SF1/SF2, BT, RL.
    """
    # ── Valores físicos ──────────────────────────────────────
    bs      = float(params.get("BS",   1800))
    bsr     = float(params.get("BSR",  bs))
    bks     = float(params.get("BKS",  1200))
    rail    = float(params.get("RAIL", 12))
    sf1     = float(params.get("SF1",  280))
    sf2     = float(params.get("SF2",  280))
    bt      = float(params.get("BT",   900))
    frame   = float(params.get("FRAME",100))

    cabin_w = bks + 2 * rail
    rl      = float(solution["rl"]) if solution else 0.0

    lim_wr = float(limits.get("LIMIT_WR", sf2))
    lim_wl = float(limits.get("LIMIT_WL", sf1))
    lim_or = float(limits.get("LIMIT_OR", 110))
    lim_ol = float(limits.get("LIMIT_OL", 110))

    # WR/WL/OR/OL de la solución (peor nivel)
    if solution and solution.get("matrix"):
        mat    = solution["matrix"]
        wr_val = min(r["WR"] for r in mat)
        wl_val = min(r["WL"] for r in mat)
        or_val = max(r["OR"] for r in mat)
        ol_val = max(r["OL"] for r in mat)
    else:
        wr_val = sf2; wl_val = sf1
        or_val = 100; ol_val = 100

    def ok_color(val, lim, mode="min"):
        diff = val - lim if mode == "min" else lim - val
        if diff < 0:   return "#E24B4A", "#FCEBEB"   # rojo
        if diff < 10:  return "#EF9F27", "#412402"   # naranja
        return "#3B6D11", "#EAF3DE"                   # verde

    wr_sc, wr_fg = ok_color(wr_val, lim_wr, "min")
    wl_sc, wl_fg = ok_color(wl_val, lim_wl, "min")
    or_sc, or_fg = ok_color(or_val, lim_or, "max")
    ol_sc, ol_fg = ok_color(ol_val, lim_ol, "max")

    # ── Escala SVG ───────────────────────────────────────────
    VW, VH = 640, 320
    PAD_L, PAD_R, PAD_T, PAD_B = 20, 20, 60, 80
    draw_w = VW - PAD_L - PAD_R
    scale  = draw_w / bs

    # Posiciones X en SVG
    shaft_x  = PAD_L
    shaft_w  = bs   * scale
    cabin_x  = shaft_x + (sf1 - rl) * scale          # rl<0 → mueve cabina derecha
    cabin_sw = cabin_w * scale
    cabin_cx = cabin_x + cabin_sw / 2
    shaft_cx = shaft_x + shaft_w / 2

    shaft_y  = PAD_T + 10
    shaft_h  = VH - PAD_T - PAD_B - 20
    cabin_y  = shaft_y + (shaft_h - shaft_h * 0.7) / 2
    cabin_sh = shaft_h * 0.7

    # Apertura de puerta (BT centrada en cabina)
    door_x   = cabin_cx - (bt * scale) / 2
    door_w   = bt * scale

    # ── SVG ─────────────────────────────────────────────────
    arrow = ('M0,0 L5,3 L0,6 Z')

    def dim_line(x1, y, x2, label, color="#666", fg="white", below=False):
        ytext = y + 14 if below else y - 8
        ya1   = y + 5 if below else y - 5
        return (
            f'<defs><marker id="a{abs(hash(label))%9999}" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">'
            f'<path d="{arrow}" fill="{color}"/></marker>'
            f'<marker id="b{abs(hash(label))%9999}" markerWidth="6" markerHeight="6" refX="1" refY="3" orient="auto-start-reverse">'
            f'<path d="{arrow}" fill="{color}"/></marker></defs>'
            f'<line x1="{x1:.1f}" y1="{ya1:.1f}" x2="{x2:.1f}" y2="{ya1:.1f}" '
            f'stroke="{color}" stroke-width="1" '
            f'marker-start="url(#b{abs(hash(label))%9999})" marker-end="url(#a{abs(hash(label))%9999})"/>'
            f'<text x="{(x1+x2)/2:.1f}" y="{ytext:.1f}" text-anchor="middle" '
            f'font-size="10" fill="{color}">{label}</text>'
        )

    def badge(cx, cy, val, lim, bg, fg, label, is_or_ol=False):
        ok_sym = "✗" if (val > lim if is_or_ol else val < lim) else "✓"
        return (
            f'<rect x="{cx-28:.1f}" y="{cy-12:.1f}" width="56" height="24" rx="4" fill="{bg}" opacity="0.92"/>'
            f'<text x="{cx:.1f}" y="{cy-1:.1f}" text-anchor="middle" font-size="10" fill="{fg}" font-weight="500">{label} {_fmt(val)}</text>'
            f'<text x="{cx:.1f}" y="{cy+10:.1f}" text-anchor="middle" font-size="9" fill="{fg}">lím {_fmt(lim)} {ok_sym}</text>'
        )

    svg = f'''<svg viewBox="0 0 {VW} {VH}" xmlns="http://www.w3.org/2000/svg"
         style="width:100%;max-width:{VW}px;font-family:system-ui,sans-serif;display:block;margin:0 auto">

  <title>Sección transversal — posicionamiento lateral del bloque cabina</title>

  <!-- Etiqueta BS -->
  <text x="{shaft_x + shaft_w/2:.1f}" y="18" text-anchor="middle" font-size="12" fill="#888">
    BS = {_fmt(bs)} mm  (BSR = {_fmt(bsr)} mm)
  </text>

  <!-- Hueco externo -->
  <rect x="{shaft_x:.1f}" y="{shaft_y:.1f}" width="{shaft_w:.1f}" height="{shaft_h:.1f}"
        rx="3" fill="none" stroke="#888" stroke-width="2"/>

  <!-- Zona SF1 y SF2 (sombreada) -->
  <rect x="{shaft_x:.1f}" y="{shaft_y:.1f}" width="{sf1*scale:.1f}" height="{shaft_h:.1f}"
        rx="3" fill="#888" opacity="0.08"/>
  <rect x="{shaft_x+shaft_w-sf2*scale:.1f}" y="{shaft_y:.1f}" width="{sf2*scale:.1f}" height="{shaft_h:.1f}"
        fill="#888" opacity="0.08"/>

  <!-- Líneas límite WL y WR (punteadas) -->
  <line x1="{shaft_x+lim_wl*scale:.1f}" y1="{shaft_y-4:.1f}"
        x2="{shaft_x+lim_wl*scale:.1f}" y2="{shaft_y+shaft_h+4:.1f}"
        stroke="{wl_sc}" stroke-width="1" stroke-dasharray="4,3" opacity="0.7"/>
  <line x1="{shaft_x+shaft_w-lim_wr*scale:.1f}" y1="{shaft_y-4:.1f}"
        x2="{shaft_x+shaft_w-lim_wr*scale:.1f}" y2="{shaft_y+shaft_h+4:.1f}"
        stroke="{wr_sc}" stroke-width="1" stroke-dasharray="4,3" opacity="0.7"/>

  <!-- Bloque cabina -->
  <rect x="{cabin_x:.1f}" y="{cabin_y:.1f}" width="{cabin_sw:.1f}" height="{cabin_sh:.1f}"
        rx="3" fill="#E6F1FB" stroke="#185FA5" stroke-width="2" opacity="0.9"/>
  <text x="{cabin_cx:.1f}" y="{cabin_y + cabin_sh/2 - 6:.1f}" text-anchor="middle"
        font-size="11" fill="#185FA5" font-weight="500">BKS + 2×RAIL</text>
  <text x="{cabin_cx:.1f}" y="{cabin_y + cabin_sh/2 + 10:.1f}" text-anchor="middle"
        font-size="10" fill="#378ADD">{_fmt(cabin_w)} mm</text>

  <!-- Apertura de puerta (BT) -->
  <rect x="{door_x:.1f}" y="{cabin_y+cabin_sh-6:.1f}" width="{door_w:.1f}" height="12"
        fill="#185FA5" opacity="0.15"/>
  <line x1="{door_x:.1f}" y1="{cabin_y+cabin_sh-6:.1f}"
        x2="{door_x:.1f}" y2="{cabin_y+cabin_sh+6:.1f}"
        stroke="#185FA5" stroke-width="1.5"/>
  <line x1="{door_x+door_w:.1f}" y1="{cabin_y+cabin_sh-6:.1f}"
        x2="{door_x+door_w:.1f}" y2="{cabin_y+cabin_sh+6:.1f}"
        stroke="#185FA5" stroke-width="1.5"/>
  <text x="{cabin_cx:.1f}" y="{cabin_y+cabin_sh+18:.1f}" text-anchor="middle"
        font-size="10" fill="#185FA5">BT = {_fmt(bt)} mm</text>

  <!-- WL badge -->
  {badge(shaft_x + wl_val*scale/2, shaft_y + shaft_h/2, wl_val, lim_wl, wl_sc, wl_fg, "WL")}

  <!-- WR badge -->
  {badge(shaft_x+shaft_w - wr_val*scale/2, shaft_y + shaft_h/2, wr_val, lim_wr, wr_sc, wr_fg, "WR")}

  <!-- OR / OL badges (en la apertura) -->
  {badge(door_x - ol_val*scale/2 - 4, cabin_y + cabin_sh/2, ol_val, lim_ol, ol_sc, ol_fg, "OL", True)}
  {badge(door_x + door_w + or_val*scale/2 + 4, cabin_y + cabin_sh/2, or_val, lim_or, or_sc, or_fg, "OR", True)}

  <!-- SF1 label -->
  <text x="{shaft_x + sf1*scale/2:.1f}" y="{shaft_y+shaft_h+16:.1f}" text-anchor="middle"
        font-size="10" fill="#999">SF1 = {_fmt(sf1)}</text>

  <!-- SF2 label -->
  <text x="{shaft_x+shaft_w-sf2*scale/2:.1f}" y="{shaft_y+shaft_h+16:.1f}" text-anchor="middle"
        font-size="10" fill="#999">SF2 = {_fmt(sf2)}</text>

  <!-- Flecha RL -->
  {"" if abs(rl) < 0.5 else
   f'<defs><marker id="arl" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">'
   f'<path d="{arrow}" fill="#BA7517"/></marker></defs>'
   f'<line x1="{shaft_cx:.1f}" y1="{shaft_y+shaft_h+38:.1f}" '
   f'x2="{shaft_cx - rl*scale:.1f}" y2="{shaft_y+shaft_h+38:.1f}" '
   f'stroke="#BA7517" stroke-width="2" marker-end="url(#arl)"/>'
   f'<text x="{(shaft_cx + shaft_cx - rl*scale)/2:.1f}" y="{shaft_y+shaft_h+54:.1f}" '
   f'text-anchor="middle" font-size="11" fill="#BA7517" font-weight="500">'
   f'RL = {rl:+.1f} mm</text>'
  }
</svg>'''
    return svg


def frontal_diagram(params: dict, limits: dict, solution: dict | None) -> str:
    """
    Vista lateral (perfil longitudinal) — eje frontal.
    Muestra: TS, FS, TSW, TKSW, TL, BC_CALC, FR/FL, FB.
    """
    ts      = float(params.get("TS",    1500))
    fs      = float(params.get("FS",    200))
    tsw     = float(params.get("TSW",   120))
    tksw    = float(params.get("TKSW",  230))
    tl      = float(limits.get("TL",    ts * 0.7))
    bc_calc = float(limits.get("BC_CALC", ts - tl))
    fb      = float(solution.get("fb_applied", solution.get("fb", 0))) if solution else 0.0

    lim_fr  = float(limits.get("LIMIT_FR", tksw - 150))
    lim_fl  = float(limits.get("LIMIT_FL", tksw - 150))

    if solution and solution.get("matrix"):
        mat    = solution["matrix"]
        fr_val = min(r["FR"] for r in mat)
        fl_val = min(r["FL"] for r in mat)
    else:
        fr_val = tksw; fl_val = tksw

    def ok_color_min(val, lim):
        d = val - lim
        if d < 0:  return "#E24B4A", "#FCEBEB"
        if d < 10: return "#EF9F27", "#412402"
        return "#3B6D11", "#EAF3DE"

    fr_sc, fr_fg = ok_color_min(fr_val, lim_fr)
    fl_sc, fl_fg = ok_color_min(fl_val, lim_fl)

    VW, VH   = 640, 280
    PAD_L, PAD_R, PAD_T, PAD_B = 30, 30, 50, 60
    draw_d   = VW - PAD_L - PAD_R
    scale    = draw_d / ts

    shaft_x  = PAD_L
    shaft_w  = ts * scale
    shaft_y  = PAD_T
    shaft_h  = VH - PAD_T - PAD_B

    fs_w     = fs   * scale
    tsw_w    = tsw  * scale
    cabin_x  = shaft_x + (tksw + fb) * scale
    cabin_w  = tl  * scale
    bc_x     = cabin_x + cabin_w
    bc_w     = bc_calc * scale

    mid_y    = shaft_y + shaft_h / 2
    rail_x   = shaft_x + (tksw + fb) * scale   # centro del riel
    rail_size = 8

    arrow = 'M0,0 L5,3 L0,6 Z'

    svg = f'''<svg viewBox="0 0 {VW} {VH}" xmlns="http://www.w3.org/2000/svg"
         style="width:100%;max-width:{VW}px;font-family:system-ui,sans-serif;display:block;margin:0 auto">

  <title>Perfil longitudinal — posicionamiento frontal del bloque cabina</title>

  <!-- Etiqueta TS -->
  <text x="{shaft_x + shaft_w/2:.1f}" y="18" text-anchor="middle" font-size="12" fill="#888">
    TS = {_fmt(ts)} mm
  </text>

  <!-- Hueco externo -->
  <rect x="{shaft_x:.1f}" y="{shaft_y:.1f}" width="{shaft_w:.1f}" height="{shaft_h:.1f}"
        rx="3" fill="none" stroke="#888" stroke-width="2"/>

  <!-- Zona FS -->
  <rect x="{shaft_x:.1f}" y="{shaft_y:.1f}" width="{fs_w:.1f}" height="{shaft_h:.1f}"
        fill="#EF9F27" opacity="0.10" rx="3"/>
  <text x="{shaft_x + fs_w/2:.1f}" y="{shaft_y+shaft_h+16:.1f}" text-anchor="middle"
        font-size="10" fill="#BA7517">FS={_fmt(fs)}</text>

  <!-- Zona TSW (umbral) -->
  <rect x="{shaft_x + fs_w - tsw_w:.1f}" y="{shaft_y + shaft_h*0.35:.1f}"
        width="{tsw_w:.1f}" height="{shaft_h*0.3:.1f}"
        fill="#185FA5" opacity="0.15" rx="2"/>
  <text x="{shaft_x + fs_w - tsw_w/2:.1f}" y="{shaft_y+shaft_h+16:.1f}" text-anchor="middle"
        font-size="10" fill="#185FA5">TSW={_fmt(tsw)}</text>

  <!-- Bloque cabina -->
  <rect x="{cabin_x:.1f}" y="{shaft_y+shaft_h*0.15:.1f}"
        width="{cabin_w:.1f}" height="{shaft_h*0.7:.1f}"
        rx="3" fill="#E6F1FB" stroke="#185FA5" stroke-width="1.5" opacity="0.9"/>
  <text x="{cabin_x + cabin_w/2:.1f}" y="{mid_y - 4:.1f}" text-anchor="middle"
        font-size="10" fill="#185FA5" font-weight="500">TL = {_fmt(tl)} mm</text>

  <!-- BC_CALC -->
  <rect x="{bc_x:.1f}" y="{shaft_y + shaft_h*0.3:.1f}"
        width="{bc_w:.1f}" height="{shaft_h*0.4:.1f}"
        fill="#7F77DD" opacity="0.12" rx="2"/>
  <text x="{bc_x + bc_w/2:.1f}" y="{mid_y + 4:.1f}" text-anchor="middle"
        font-size="10" fill="#534AB7">BC={_fmt(bc_calc)}</text>

  <!-- Centro del riel (círculo) -->
  <circle cx="{rail_x:.1f}" cy="{mid_y:.1f}" r="{rail_size}" fill="#185FA5" opacity="0.8"/>
  <text x="{rail_x:.1f}" y="{mid_y+16:.1f}" text-anchor="middle" font-size="9" fill="#185FA5">●riel</text>

  <!-- Línea límite FR/FL -->
  <line x1="{shaft_x + lim_fr*scale:.1f}" y1="{shaft_y-4:.1f}"
        x2="{shaft_x + lim_fr*scale:.1f}" y2="{shaft_y+shaft_h+4:.1f}"
        stroke="{fr_sc}" stroke-width="1.2" stroke-dasharray="5,3" opacity="0.8"/>
  <text x="{shaft_x + lim_fr*scale:.1f}" y="{shaft_y-8:.1f}" text-anchor="middle"
        font-size="9" fill="{fr_sc}">LIM FR/FL</text>

  <!-- FR badge (distancia pared frontal → riel) -->
  <defs>
    <marker id="afr1" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
      <path d="{arrow}" fill="{fr_sc}"/></marker>
    <marker id="afr2" markerWidth="6" markerHeight="6" refX="1" refY="3" orient="auto-start-reverse">
      <path d="{arrow}" fill="{fr_sc}"/></marker>
  </defs>
  <line x1="{shaft_x:.1f}" y1="{shaft_y + shaft_h*0.88:.1f}"
        x2="{rail_x:.1f}" y2="{shaft_y + shaft_h*0.88:.1f}"
        stroke="{fr_sc}" stroke-width="1.2"
        marker-start="url(#afr2)" marker-end="url(#afr1)"/>
  <rect x="{(shaft_x+rail_x)/2-32:.1f}" y="{shaft_y+shaft_h*0.88+4:.1f}"
        width="64" height="18" rx="3" fill="{fr_sc}" opacity="0.9"/>
  <text x="{(shaft_x+rail_x)/2:.1f}" y="{shaft_y+shaft_h*0.88+16:.1f}" text-anchor="middle"
        font-size="10" fill="{fr_fg}" font-weight="500">FR {_fmt(fr_val)} mm</text>

  <!-- FB arrow -->
  {"" if abs(fb) < 0.5 else
   f'<defs><marker id="afb" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">'
   f'<path d="{arrow}" fill="#BA7517"/></marker></defs>'
   f'<line x1="{shaft_x+tksw*scale:.1f}" y1="{shaft_y+shaft_h+38:.1f}" '
   f'x2="{rail_x:.1f}" y2="{shaft_y+shaft_h+38:.1f}" '
   f'stroke="#BA7517" stroke-width="2" marker-end="url(#afb)"/>'
   f'<text x="{(shaft_x+tksw*scale+rail_x)/2:.1f}" y="{shaft_y+shaft_h+54:.1f}" '
   f'text-anchor="middle" font-size="11" fill="#BA7517" font-weight="500">'
   f'FB = {fb:+.1f} mm</text>'
  }

  <!-- TKSW label -->
  <text x="{shaft_x + tksw*scale/2:.1f}" y="{shaft_y+shaft_h+16:.1f}" text-anchor="middle"
        font-size="10" fill="#888">TKSW={_fmt(tksw)}</text>
</svg>'''
    return svg


def render_diagrams_html(params: dict, limits: dict, solution: dict | None) -> str:
    """Retorna el HTML completo con ambos diagramas para usar con st.markdown."""
    lat = lateral_diagram(params, limits, solution)
    fro = frontal_diagram(params, limits, solution)
    return f"""
<div style="display:flex;flex-direction:column;gap:24px;">
  <div>
    <p style="font-size:12px;color:#888;margin:0 0 8px;font-weight:500;
              text-transform:uppercase;letter-spacing:.06em;">
      Vista superior — sección transversal (eje lateral)
    </p>
    {lat}
  </div>
  <div>
    <p style="font-size:12px;color:#888;margin:0 0 8px;font-weight:500;
              text-transform:uppercase;letter-spacing:.06em;">
      Vista lateral — perfil longitudinal (eje frontal)
    </p>
    {fro}
  </div>
</div>
"""
