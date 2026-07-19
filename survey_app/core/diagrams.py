"""
Diagrama de planta (vista superior) del encaje de la cabina en el shaft.
Una imagen POR PISO, usando los valores de la matriz de la solución seleccionada.

Lenguaje de PLANO TÉCNICO, no esquema: la planta va a proporción real (una sola
escala mm→px para ancho y profundidad), con muros achurados, cotas con líneas de
extensión y marcas diagonales, ejes de simetría y cajetín. El rojo se reserva
para las cotas fuera de límite. Cuando una holgura es muy ajustada se añade un
"DETALLE" ampliado con escala propia, porque a escala real no se distinguiría.

  - Eje horizontal = ancho   (WL a la izquierda, WR a la derecha)
  - Eje vertical   = profundidad (FRENTE abajo = puertas; FONDO arriba)
  - Cabina = bloque rígido BKS + 2·RAIL (ancho) × TL (profundidad)
  - Apertura de puerta (BT) centrada en su eje, con OL/OR a los lados
  - FR/FL = distancia de la pared frontal al riel (frente de la cabina)

`shaft_iso_svg` añade una isométrica del hueco completo para el informe: la
PLANTA va a escala real y la ALTURA comprimida (se declara en el subtítulo).

SVG sin <marker>/<defs> → compatible con Streamlit (components.html) y
ReportLab (svglib.svg2rlg).
"""










def _mm(v) -> str:
    """mm para cotas: entero si lo es, 1 decimal si no.

    El optimizador barre RL/FB en pasos de 0.5 mm y esos medios milimetros se
    propagan a la matriz (WL += rl, FR += fb...). Con .0f, una holgura real de
    71.5 se rotulaba "72": la cota afirmaba un valor que no es el medido.
    """
    try:
        v = float(v)
    except Exception:
        return str(v)
    return f"{v:.0f}" if abs(v - round(v)) < 0.05 else f"{v:.1f}"


def _n(v, d=0.0) -> float:
    try:
        return float(v)
    except Exception:
        return d


def _hatch(x, y, w, h, lado, step=9.0, color="#8a94a6", sw=0.6) -> str:
    """Achurado del muro con marcas diagonales sueltas (sin <pattern>: compatible svglib)."""
    p, t = [], 7.0
    if lado in ("top", "bottom"):
        i = x + step
        while i < x + w:
            p.append(f'<line x1="{i:.1f}" y1="{y+h:.1f}" x2="{i+t:.1f}" y2="{y:.1f}" '
                     f'stroke="{color}" stroke-width="{sw}"/>')
            i += step
    else:
        j = y + step
        while j < y + h:
            p.append(f'<line x1="{x:.1f}" y1="{j+t:.1f}" x2="{x+w:.1f}" y2="{j:.1f}" '
                     f'stroke="{color}" stroke-width="{sw}"/>')
            j += step
    return "".join(p)


def _dim_h(x1, x2, y, texto, color="#5f6b7a", tcolor=None, ext_desde=None, hacia="der") -> str:
    """Cota horizontal: líneas de extensión + línea de cota + marcas diagonales + valor."""
    tcolor = tcolor or "#1f2937"
    p = []
    if ext_desde is not None:
        p.append(f'<line x1="{x1:.1f}" y1="{ext_desde:.1f}" x2="{x1:.1f}" y2="{y+4:.1f}" '
                 f'stroke="{color}" stroke-width="0.5"/>')
        p.append(f'<line x1="{x2:.1f}" y1="{ext_desde:.1f}" x2="{x2:.1f}" y2="{y+4:.1f}" '
                 f'stroke="{color}" stroke-width="0.5"/>')
    p.append(f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" '
             f'stroke="{color}" stroke-width="0.6"/>')
    for xx in (x1, x2):
        p.append(f'<line x1="{xx-3:.1f}" y1="{y+3:.1f}" x2="{xx+3:.1f}" y2="{y-3:.1f}" '
                 f'stroke="{color}" stroke-width="0.7"/>')
    if (x2 - x1) < 36:                      # cota corta: valor afuera + directriz
        xt, anc = (x2 + 6, "start") if hacia == "der" else (x1 - 6, "end")
        p.append(f'<line x1="{x1 if hacia=="izq" else x2:.1f}" y1="{y:.1f}" '
                 f'x2="{xt + (4 if hacia=="der" else -4):.1f}" y2="{y:.1f}" '
                 f'stroke="{color}" stroke-width="0.5"/>')
        p.append(f'<text x="{xt:.1f}" y="{y-3:.1f}" text-anchor="{anc}" font-size="9" '
                 f'fill="{tcolor}">{texto}</text>')
    else:
        p.append(f'<text x="{(x1+x2)/2:.1f}" y="{y-4:.1f}" text-anchor="middle" font-size="9" '
                 f'fill="{tcolor}">{texto}</text>')
    return "".join(p)


def _dim_v(y1, y2, x, texto, color="#5f6b7a", tcolor=None, ext_desde=None, hacia="abajo") -> str:
    """Cota vertical (valor rotado, como en un plano)."""
    tcolor = tcolor or "#1f2937"
    p = []
    if ext_desde is not None:
        p.append(f'<line x1="{ext_desde:.1f}" y1="{y1:.1f}" x2="{x+4:.1f}" y2="{y1:.1f}" '
                 f'stroke="{color}" stroke-width="0.5"/>')
        p.append(f'<line x1="{ext_desde:.1f}" y1="{y2:.1f}" x2="{x+4:.1f}" y2="{y2:.1f}" '
                 f'stroke="{color}" stroke-width="0.5"/>')
    p.append(f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}" '
             f'stroke="{color}" stroke-width="0.6"/>')
    for yy in (y1, y2):
        p.append(f'<line x1="{x-3:.1f}" y1="{yy+3:.1f}" x2="{x+3:.1f}" y2="{yy-3:.1f}" '
                 f'stroke="{color}" stroke-width="0.7"/>')
    if (y2 - y1) < 36:                      # cota corta: valor afuera + directriz
        yt = (y2 + 12) if hacia == "abajo" else (y1 - 8)
        p.append(f'<line x1="{x:.1f}" y1="{y2 if hacia=="abajo" else y1:.1f}" '
                 f'x2="{x:.1f}" y2="{yt + (2 if hacia=="abajo" else -2):.1f}" '
                 f'stroke="{color}" stroke-width="0.5"/>')
        p.append(f'<text x="{x-3:.1f}" y="{yt:.1f}" text-anchor="{"start" if hacia=="abajo" else "end"}" '
                 f'font-size="9" fill="{tcolor}" transform="rotate(-90 {x-3:.1f} {yt:.1f})">{texto}</text>')
    else:
        ym = (y1 + y2) / 2
        p.append(f'<text x="{x-4:.1f}" y="{ym:.1f}" text-anchor="middle" font-size="9" '
                 f'fill="{tcolor}" transform="rotate(-90 {x-4:.1f} {ym:.1f})">{texto}</text>')
    return "".join(p)


def floor_plan_svg(params: dict, limits: dict, row: dict, floor_idx: int,
                   lim_map: dict, ctrl_in_frame=False, ctrl_side=None,
                   is_last=False, rl=0.0, fb=0.0, n_floors=None, proyecto="") -> str:
    """Planta de UN piso con lenguaje de PLANO TÉCNICO, a escala real.

    - Geometría en proporción verdadera (una sola escala mm→px para ancho y profundidad).
    - Muros achurados, cotas con líneas de extensión y marcas diagonales, cajetín.
    - Ejes de simetría: eje de cabina vs eje de apertura → cota de OFFSET_CABIN.
    - Posición de DISEÑO en línea fantasma + cotas RL/FB cuando hay desplazamiento.
    - "DETALLE A": si alguna holgura es muy pequeña (<25 mm) se amplía esa esquina.
    """
    bks   = _n(params.get("BKS"), 1200.0)
    rail  = _n(params.get("RAIL"), 12.0)
    bt    = _n(params.get("BT"), 900.0)
    cab_w = bks + 2 * rail

    wl = _n(row.get("WL")); wr = _n(row.get("WR"))
    fl = _n(row.get("FL")); fr = _n(row.get("FR"))
    ol = _n(row.get("OL")); orr = _n(row.get("OR"))

    lim_wl = _n(lim_map.get("WL")); lim_wr = _n(lim_map.get("WR"))
    lim_fl = _n(lim_map.get("FL")); lim_fr = _n(lim_map.get("FR"))
    lim_ol = _n(lim_map.get("OL")); lim_or = _n(lim_map.get("OR"))
    if ctrl_in_frame and is_last:
        if ctrl_side == "R": lim_or -= 70
        if ctrl_side == "L": lim_ol -= 70

    # ── Geometría real (mm) ────────────────────────────────
    # Eje de profundidad tomado de la identidad EXACTA de calculations.py (l.98):
    #   BC_CALC = TS − TKSW − TK/2 − 25   ⇒   TS = TKSW + TK/2 + 25 + BC_CALC
    # Es decir: desde la pared frontal, TKSW (en obra = FL/FR) llega al EJE DE
    # RIELES, y ese eje está a MEDIA profundidad del cuerpo de cabina (TK/2), no
    # en su frente. Situar el frente de la cabina a (FL+FR)/2 la sacaba del hueco.
    ancho_int = wl + cab_w + wr
    tk        = _n(params.get("TK"), 0.0)
    eje_riel  = max(1.0, (fl + fr) / 2.0)          # pared frontal → eje de rieles
    bc        = _n(limits.get("BC_CALC"), 0.0)
    prof_int  = (_n(params.get("TS"), 0.0)
                 or (eje_riel + tk / 2 + 25 + max(bc, 0.0)))
    if ancho_int <= 0 or prof_int <= 0 or tk <= 0:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>'

    # ── Lienzo y escala (una sola, ancho y profundidad) ────
    VW, VH = 660, 470
    AX, AY, AW, AH = 100, 66, 360, 250          # área de dibujo
    esc = min(AW / ancho_int, AH / prof_int)
    w_px, h_px = ancho_int * esc, prof_int * esc
    x0 = AX + (AW - w_px) / 2                    # interior del hueco
    y0 = AY + (AH - h_px) / 2
    x1, y1 = x0 + w_px, y0 + h_px                # y1 = pared frontal

    mur = 9.0                                    # espesor visual del muro
    p = [f'<svg viewBox="0 0 {VW} {VH}" xmlns="http://www.w3.org/2000/svg" '
         f'style="width:100%;max-width:{VW}px;font-family:Arial,Helvetica,sans-serif;'
         f'display:block;margin:0 auto">',
         f'<rect x="0" y="0" width="{VW}" height="{VH}" fill="#ffffff"/>']

    # ── Muros (achurados) ──────────────────────────────────
    p.append(_hatch(x0 - mur, y0 - mur, w_px + 2 * mur, mur, "top"))
    p.append(_hatch(x0 - mur, y1, w_px + 2 * mur, mur, "bottom"))
    p.append(_hatch(x0 - mur, y0, mur, h_px, "left"))
    p.append(_hatch(x1, y0, mur, h_px, "right"))
    p.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w_px:.1f}" height="{h_px:.1f}" '
             f'fill="none" stroke="#1f2937" stroke-width="2.2"/>')

    # ── Cabina (posición real) ─────────────────────────────
    cx0 = x0 + wl * esc
    cw  = cab_w * esc
    ch  = tk * esc
    cy0 = y1 - (eje_riel + tk / 2) * esc           # fondo de la cabina
    cy1 = cy0 + ch                                 # frente de la cabina
    y_rl = y1 - fl * esc                           # eje de riel izquierdo
    y_rr = y1 - fr * esc                           # eje de riel derecho

    # Posición de DISEÑO (fantasma) — solo si el desplazamiento se distingue a escala
    _rl, _fb = _n(rl), _n(fb)
    hay_desp = abs(_rl) > 0.05 or abs(_fb) > 0.05
    if hay_desp and (abs(_rl) * esc > 2 or abs(_fb) * esc > 2):
        gx0, gy0 = cx0 - _rl * esc, cy0 + _fb * esc
        p.append(f'<rect x="{gx0:.1f}" y="{gy0:.1f}" width="{cw:.1f}" height="{ch:.1f}" '
                 f'fill="none" stroke="#9aa7b8" stroke-width="1" stroke-dasharray="6,4"/>')
        p.append(f'<text x="{gx0+4:.1f}" y="{gy0-3:.1f}" font-size="7" fill="#9aa7b8">POS. DISEÑO</text>')

    p.append(f'<rect x="{cx0:.1f}" y="{cy0:.1f}" width="{cw:.1f}" height="{ch:.1f}" '
             f'fill="#f7fafd" stroke="#1a3a5c" stroke-width="1.6"/>')
    p.append(f'<text x="{cx0+cw/2:.1f}" y="{cy0+ch/2-2:.1f}" text-anchor="middle" '
             f'font-size="10" fill="#1a3a5c" letter-spacing="0.08em">CABINA</text>')
    p.append(f'<text x="{cx0+cw/2:.1f}" y="{cy0+ch/2+11:.1f}" text-anchor="middle" '
             f'font-size="7.5" fill="#7a8699">BKS+2·RAIL = {cab_w:.0f} mm</text>')

    # Rieles: sobre los laterales, a la profundidad medida en obra (FL / FR)
    for rx, ry in ((cx0, y_rl), (cx0 + cw, y_rr)):
        p.append(f'<rect x="{rx-4:.1f}" y="{ry-5:.1f}" width="8" height="10" fill="#1a3a5c"/>')
        p.append(f'<line x1="{rx-13:.1f}" y1="{ry:.1f}" x2="{rx+13:.1f}" y2="{ry:.1f}" '
                 f'stroke="#1a3a5c" stroke-width="0.6" stroke-dasharray="7,2,1.5,2"/>')

    # ── Apertura de puerta — posicionada con los datos MEDIDOS ──
    # OL/OR se miden desde el borde de la cabina hasta la apertura (ver
    # LIMIT_OL/OR = BKS/2 + RAIL/2 − BT/2 − FRAME). Antes la apertura se
    # centraba en un eje calculado y luego se rotulaba con OL/OR: el número
    # no correspondía al tramo realmente dibujado.
    eje_cab = cx0 + cw / 2
    dx0, dx1 = cx0 + ol * esc, cx0 + (cab_w - orr) * esc
    if dx1 - dx0 < 6:                      # datos incoherentes → apertura nominal
        dx0, dx1 = eje_cab - bt * esc / 2, eje_cab + bt * esc / 2
    eje_ap = (dx0 + dx1) / 2
    marco = max(0.0, ((dx1 - dx0) - bt * esc) / 2)      # FRAME a cada lado

    p.append(f'<line x1="{dx0+marco:.1f}" y1="{y1:.1f}" x2="{dx1-marco:.1f}" y2="{y1:.1f}" '
             f'stroke="#1a3a5c" stroke-width="3.4"/>')
    if marco > 0.7:                        # marcos de la puerta
        for _mx in (dx0, dx1 - marco):
            p.append(f'<rect x="{_mx:.1f}" y="{y1-2.5:.1f}" width="{marco:.1f}" height="5" '
                     f'fill="#8a94a6"/>')
    p.append(f'<text x="{eje_ap:.1f}" y="{y1+mur+22:.1f}" text-anchor="middle" font-size="8" '
             f'fill="#5f6b7a">APERTURA BT {bt:.0f}</text>')

    # ── Ejes: cabina vs apertura ─────────────────────
    p.append(f'<line x1="{eje_cab:.1f}" y1="{y0-mur-6:.1f}" x2="{eje_cab:.1f}" y2="{y1+mur+6:.1f}" '
             f'stroke="#9aa7b8" stroke-width="0.7" stroke-dasharray="9,3,2,3"/>')
    d_ejes = (eje_ap - eje_cab) / esc if esc else 0.0   # mm reales entre ejes
    if abs(d_ejes) > 0.5:
        p.append(f'<line x1="{eje_ap:.1f}" y1="{cy1-30:.1f}" x2="{eje_ap:.1f}" y2="{y1+mur+6:.1f}" '
                 f'stroke="#2e6da4" stroke-width="0.7" stroke-dasharray="9,3,2,3"/>')
        _lado = "R" if d_ejes > 0 else "L"
        p.append(_dim_h(min(eje_cab, eje_ap), max(eje_cab, eje_ap), cy1 - 22,
                        f"EJES {_mm(abs(d_ejes))}→{_lado}",
                        color="#2e6da4", tcolor="#2e6da4"))

    # ── Cotas (rojo si incumple) ───────────────────
    def _c(v, lim, es_max=False):
        return "#c0392b" if ((v > lim) if es_max else (v < lim)) else "#1f2937"

    yd = y0 - mur - 16
    p.append(_dim_h(x0, cx0, yd, f"WL {_mm(wl)}", tcolor=_c(wl, lim_wl),
                    ext_desde=y0 - mur, hacia="izq"))
    p.append(_dim_h(cx0 + cw, x1, yd, f"WR {_mm(wr)}", tcolor=_c(wr, lim_wr),
                    ext_desde=y0 - mur, hacia="der"))

    xd = x0 - mur - 26
    # FL/FR: pared frontal → EJE DE RIELES (que es justo lo que se mide en obra)
    p.append(_dim_v(y_rl, y1, xd, f"FL {_mm(fl)}", tcolor=_c(fl, lim_fl), ext_desde=x0 - mur))
    p.append(_dim_v(y_rr, y1, x1 + mur + 16, f"FR {_mm(fr)}", tcolor=_c(fr, lim_fr),
                    ext_desde=x1 + mur))
    p.append(_dim_v(cy0, cy1, x1 + mur + 42, f"TK {_mm(tk)}", ext_desde=x1 + mur))
    bc_dib = prof_int - (eje_riel + tk / 2)            # holgura trasera dibujada
    if bc_dib * esc > 3:
        p.append(_dim_v(y0, cy0, xd - 20, f"BC {_mm(bc_dib)}", ext_desde=x0 - mur))

    yo = y1 + mur + 34
    p.append(_dim_h(cx0, dx0, yo, f"OL {_mm(ol)}", tcolor=_c(ol, lim_ol, True),
                    ext_desde=y1 + mur, hacia="izq"))
    p.append(_dim_h(dx1, cx0 + cw, yo, f"OR {_mm(orr)}", tcolor=_c(orr, lim_or, True),
                    ext_desde=y1 + mur, hacia="der"))

    # Rótulos de orientación
    p.append(f'<text x="{x0-mur:.1f}" y="{y0-mur-30:.1f}" font-size="8" fill="#7a8699" '
             f'letter-spacing="0.1em">FONDO DEL HUECO</text>')
    p.append(f'<text x="{x0-mur:.1f}" y="{y1+mur+50:.1f}" font-size="8" fill="#7a8699" '
             f'letter-spacing="0.1em">PARED FRONTAL — ACCESO</text>')

    # ── DETALLE A: se amplía la holgura crítica (<25 mm) ───
    crit = min([(wl, "WL", lim_wl), (wr, "WR", lim_wr)], key=lambda z: z[0])
    if crit[0] < 25:
        bx, by, bw, bh = 492, 66, 152, 116
        z = max(3.0, min(40.0, 34.0 / max(0.5, crit[0] * esc)))
        p.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="#fbfcfe" '
                 f'stroke="#1f2937" stroke-width="0.8"/>')
        p.append(f'<text x="{bx+6}" y="{by+14}" font-size="8.5" fill="#1f2937" '
                 f'font-weight="bold">DETALLE A — {crit[1]}</text>')
        p.append(f'<text x="{bx+6}" y="{by+25}" font-size="7.5" fill="#7a8699">ampliado ×{z:.0f}</text>')
        gap = crit[0] * esc * z
        mx, my = bx + 30, by + 46
        p.append(_hatch(mx - 10, my, 10, 52, "left"))
        p.append(f'<line x1="{mx:.1f}" y1="{my:.1f}" x2="{mx:.1f}" y2="{my+52:.1f}" '
                 f'stroke="#1f2937" stroke-width="2"/>')
        p.append(f'<rect x="{mx+gap:.1f}" y="{my+6:.1f}" width="{max(24, bx+bw-16-(mx+gap)):.1f}" '
                 f'height="40" fill="#f7fafd" stroke="#1a3a5c" stroke-width="1.4"/>')
        col = "#c0392b" if crit[0] < crit[2] else "#1f2937"
        p.append(_dim_h(mx, mx + gap, my + 62, f"{_mm(crit[0])} mm", tcolor=col, ext_desde=my + 52))
        # marca en el dibujo principal
        p.append(f'<circle cx="{(x0 if crit[1] == "WL" else x1):.1f}" '
                 f'cy="{cy0+ch/2:.1f}" r="9" '
                 f'fill="none" stroke="#c0392b" stroke-width="1"/>')

    # ── Desplazamiento aplicado (siempre legible, aunque sea sub-píxel) ──
    if hay_desp:
        dxb, dyb = 492, 200
        p.append(f'<rect x="{dxb}" y="{dyb}" width="152" height="52" fill="#f7fafd" '
                 f'stroke="#1a3a5c" stroke-width="0.8"/>')
        p.append(f'<text x="{dxb+6}" y="{dyb+15}" font-size="8" fill="#1a3a5c" '
                 f'font-weight="bold">DESPLAZAMIENTO</text>')
        p.append(f'<text x="{dxb+6}" y="{dyb+30}" font-size="8" fill="#1f2937">'
                 f'RL {_rl:+.1f} mm  (lateral)</text>')
        p.append(f'<text x="{dxb+6}" y="{dyb+44}" font-size="8" fill="#1f2937">'
                 f'FB {_fb:+.1f} mm  (frontal)</text>')

    # ── Cajetín ────────────────────────────────────────────
    tx, ty, tw, th = 492, 336, 152, 86
    p.append(f'<rect x="{tx}" y="{ty}" width="{tw}" height="{th}" fill="none" '
             f'stroke="#1f2937" stroke-width="0.9"/>')
    for dy in (24, 46, 66):
        p.append(f'<line x1="{tx}" y1="{ty+dy}" x2="{tx+tw}" y2="{ty+dy}" '
                 f'stroke="#1f2937" stroke-width="0.5"/>')
    _tot = f" / {n_floors}" if n_floors else ""
    p.append(f'<text x="{tx+6}" y="{ty+16}" font-size="9.5" fill="#1f2937" '
             f'font-weight="bold">PISO {floor_idx+1}{_tot}</text>')
    p.append(f'<text x="{tx+6}" y="{ty+38}" font-size="7.5" fill="#5f6b7a">'
             f'Proporción real · cotas en mm</text>')
    p.append(f'<text x="{tx+6}" y="{ty+59}" font-size="7.5" fill="#5f6b7a">'
             f'{(proyecto or "COPEX")[:24]}</text>')
    p.append(f'<text x="{tx+6}" y="{ty+79}" font-size="7" fill="#7a8699">'
             f'Planta · vista superior</text>')

    # Leyenda de color
    p.append(f'<rect x="{tx}" y="{ty+th+8}" width="9" height="9" fill="#fcebeb" '
             f'stroke="#c0392b" stroke-width="0.6"/>')
    p.append(f'<text x="{tx+14}" y="{ty+th+16}" font-size="7" fill="#7a8699">valor fuera de límite</text>')

    p.append("</svg>")
    return "".join(p)


def floors_with_issues(solution: dict | None, lim_map: dict) -> list:
    """Índices de los pisos con algún valor fuera de límite (para no dibujarlos todos)."""
    if not solution or not solution.get("matrix"):
        return []
    out = []
    for i, row in enumerate(solution["matrix"]):
        for col, lim in (lim_map or {}).items():
            v = row.get(col)
            if v is None:
                continue
            fuera = (v > lim) if col in ("OR", "OL") else (v < lim)
            if fuera:
                out.append(i)
                break
    return out


def render_floor_plans_html(params: dict, limits: dict, solution: dict | None,
                            lim_map: dict, ctrl_in_frame=False, ctrl_side=None,
                            floors=None) -> str:
    """HTML con la planta de los pisos (matriz solución) para components.html.
    `floors`: lista de índices a dibujar (None = todos). El índice real del piso se
    conserva, así las etiquetas siguen siendo correctas aunque se filtre."""
    if not solution or not solution.get("matrix"):
        return "<p style='color:#888;font-family:system-ui'>No hay solución para graficar.</p>"
    mat = solution["matrix"]
    n   = len(mat)
    blocks = []
    for i, row in enumerate(mat):
        if floors is not None and i not in floors:
            continue
        svg = floor_plan_svg(params, limits, row, i, lim_map,
                             ctrl_in_frame, ctrl_side, is_last=(i == n - 1),
                             rl=solution.get("rl", 0), fb=solution.get("fb_applied", solution.get("fb", 0)),
                             n_floors=n, proyecto=str(params.get("PROYECTO", "")))
        blocks.append(f'<div style="margin-bottom:18px">{svg}</div>')
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<style>body{margin:0;padding:0;background:transparent}</style></head><body>'
        + "".join(blocks) +
        '</body></html>'
    )


def floor_plans_pdf(params: dict, limits: dict, solution: dict | None, lim_map: dict,
                    ctrl_in_frame=False, ctrl_side=None, floors=None,
                    titulo="Diagramas de posicionamiento") -> bytes | None:
    """PDF suelto con los diagramas de planta (para enviar a obra sin el informe completo)."""
    if not solution or not solution.get("matrix"):
        return None
    try:
        import io as _io
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from core.report import _svg_flowable
    except Exception:
        return None

    buf = _io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=14 * mm, bottomMargin=14 * mm)
    W  = doc.width
    ss = getSampleStyleSheet()
    story = [Paragraph(titulo, ss["Title"]), Spacer(1, 8)]
    mat, n = solution["matrix"], len(solution["matrix"])
    puestos = 0
    for i, row in enumerate(mat):
        if floors is not None and i not in floors:
            continue
        svg = floor_plan_svg(params, limits, row, i, lim_map,
                             ctrl_in_frame, ctrl_side, is_last=(i == n - 1),
                             rl=solution.get("rl", 0), fb=solution.get("fb_applied", solution.get("fb", 0)),
                             n_floors=n, proyecto=str(params.get("PROYECTO", "")))
        dib = _svg_flowable(svg, W)
        if dib is None:
            continue
        if puestos and puestos % 2 == 0:
            story.append(PageBreak())
        story += [Paragraph(f"Piso {i + 1}", ss["Heading3"]), dib, Spacer(1, 10)]
        puestos += 1
    if not puestos:
        return None
    try:
        doc.build(story)
    except Exception:
        return None
    return buf.getvalue()


# ══════════════════════════════════════════════════════════
#  Vista isométrica del hueco (para el informe)
# ══════════════════════════════════════════════════════════
_ISO_CX, _ISO_CY = 0.866, 0.5          # cos30 / sin30


def _iso(x, y, z, ox, oy, k, kz=None):
    """(mm) → (px). Isométrica 30°, Z arriba. `kz` permite comprimir la altura."""
    return (ox + (x - y) * _ISO_CX * k,
            oy + (x + y) * _ISO_CY * k - z * (kz if kz is not None else k))


def _poly(pts, fill, stroke, sw=1.0, op=1.0):
    d = " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)
    return (f'<polygon points="{d}" fill="{fill}" fill-opacity="{op}" '
            f'stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/>')


def shaft_iso_svg(params: dict, limits: dict, solution: dict, ns: int,
                  lim_map: dict, proyecto="", h_piso=3000.0) -> str:
    """Isométrica del hueco completo: pisos apilados, cabina en su posición y
    pisos con incidencia marcados en rojo.

    Planta y profundidad van a escala real; la ALTURA es esquemática (h_piso
    nominal) porque el paso entre niveles no forma parte del survey.
    """
    ns = max(1, int(ns or 1))
    rows = (solution or {}).get("matrix") or []
    bks  = _n(params.get("BKS"), 1200.0)
    rail = _n(params.get("RAIL"), 12.0)
    bt   = _n(params.get("BT"), 900.0)
    cab_w = bks + 2 * rail

    r0 = rows[0] if rows else {}
    wl = _n(r0.get("WL"), 50.0); wr = _n(r0.get("WR"), 50.0)
    fl = _n(r0.get("FL"), 60.0); fr = _n(r0.get("FR"), 60.0)
    W  = wl + cab_w + wr
    tl = _n(limits.get("TL"), 0.0) or 1400.0
    D  = _n(params.get("TS"), 0.0) or ((fl + fr) / 2 + tl + _n(limits.get("BC_CALC")))
    H  = ns * h_piso
    if W <= 0 or D <= 0:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>'

    # Planta a escala real; ALTURA con su propia escala (comprimida) — de lo
    # contrario 18 m contra 1,3 m dan una astilla ilegible. Se declara en el pie.
    # Lienzo VERTICAL: un hueco es alto. La planta va a escala real; la altura
    # se comprime de forma moderada (se declara en el subtítulo), que es la
    # convención en esquemas de hueco — sin comprimir, 18 m contra 1,3 m dan
    # una astilla ilegible; comprimida al máximo, deja de leerse como hueco.
    VW, VH = 460, 700
    k    = (VW - 190) / ((W + D) * _ISO_CX)
    diam = (W + D) * _ISO_CY * k
    kz   = max(0.0005, (VH - 200 - diam) / H)
    ox   = VW / 2 + (D - W) * _ISO_CX * k / 2
    oy   = 96 + H * kz

    malos = set(floors_with_issues(solution, lim_map) or [])
    p = [f'<svg viewBox="0 0 {VW} {VH}" xmlns="http://www.w3.org/2000/svg" '
         f'style="width:100%;max-width:{VW}px;font-family:Arial,Helvetica,sans-serif;'
         f'display:block;margin:0 auto">',
         f'<rect x="0" y="0" width="{VW}" height="{VH}" fill="#ffffff"/>']

    A = lambda x, y, z: _iso(x, y, z, ox, oy, k, kz)

    # Caras del fondo (las dos paredes que quedan detrás en isométrica)
    p.append(_poly([A(0, 0, 0), A(0, D, 0), A(0, D, H), A(0, 0, H)],
                   "#eef2f7", "#c3ccd8", 0.8))
    p.append(_poly([A(0, 0, 0), A(W, 0, 0), A(W, 0, H), A(0, 0, H)],
                   "#f5f8fb", "#c3ccd8", 0.8))
    p.append(_poly([A(0, 0, 0), A(W, 0, 0), A(W, D, 0), A(0, D, 0)],
                   "#e3e9f0", "#c3ccd8", 0.8))          # foso

    # Losas de cada nivel + rótulo
    for i in range(ns):
        z = (i + 1) * h_piso
        malo = i in malos
        col_l = "#c0392b" if malo else "#9aa7b8"
        p.append(_poly([A(0, 0, z), A(W, 0, z), A(W, D, z), A(0, D, z)],
                       "#fbe9e7" if malo else "#f7fafd", col_l, 1.0 if malo else 0.7, 0.55))
        lx, ly = A(0, 0, z)
        p.append(f'<text x="{lx-12:.1f}" y="{ly+4:.1f}" text-anchor="end" font-size="8.5" '
                 f'fill="{"#c0392b" if malo else "#7a8699"}" '
                 f'{"font-weight=\'bold\'" if malo else ""}>P{i+1}</text>')
        # apertura de puerta en la pared de acceso (y = D, la más cercana)
        e = (W - bt) / 2
        p.append(_poly([A(e, D, z - h_piso * 0.72), A(e + bt, D, z - h_piso * 0.72),
                        A(e + bt, D, z), A(e, D, z)], "#ffffff", "#1a3a5c", 1.1))

    # Cabina (bloque) en el nivel 1, a escala en planta.
    # Misma identidad que la planta: FL/FR llegan al EJE DE RIELES, que está a
    # media profundidad del cuerpo de cabina (TK/2), no en su frente.
    eje_riel = max(1.0, (fl + fr) / 2)
    cz0, cz1 = h_piso * 0.12, h_piso * 0.12 + h_piso * 0.72
    cx_a, cx_b = wl, wl + cab_w
    _tk  = _n(params.get("TK"), 0.0) or tl
    cy_b = D - eje_riel + _tk / 2           # cara frontal de la cabina (lado acceso)
    cy_a = D - eje_riel - _tk / 2
    # Solo las caras que MIRAN al observador: x = cx_b (derecha) e y = cy_b (frente).
    top  = [A(cx_a, cy_a, cz1), A(cx_b, cy_a, cz1), A(cx_b, cy_b, cz1), A(cx_a, cy_b, cz1)]
    der  = [A(cx_b, cy_a, cz0), A(cx_b, cy_a, cz1), A(cx_b, cy_b, cz1), A(cx_b, cy_b, cz0)]
    fren = [A(cx_a, cy_b, cz0), A(cx_b, cy_b, cz0), A(cx_b, cy_b, cz1), A(cx_a, cy_b, cz1)]
    p.append(_poly(der,  "#1a3a5c", "#12293f", 1.0, 0.80))
    p.append(_poly(fren, "#2e6da4", "#12293f", 1.0, 0.92))
    p.append(_poly(top,  "#4d8fd0", "#12293f", 1.0, 0.95))
    tcx = sum(a for a, _ in top) / 4; tcy = sum(b for _, b in top) / 4
    p.append(f'<text x="{tcx:.1f}" y="{tcy+3:.1f}" text-anchor="middle" font-size="9" '
             f'fill="#ffffff" letter-spacing="0.08em">CABINA</text>')

    # Aristas vivas del hueco
    for a, b in [((0, 0, 0), (0, 0, H)), ((W, 0, 0), (W, 0, H)), ((0, D, 0), (0, D, H))]:
        (ax, ay), (bx, by) = A(*a), A(*b)
        p.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" '
                 f'stroke="#8a94a6" stroke-width="0.9"/>')

    # Ficha de datos (las cotas detalladas viven en la planta)
    fy = VH - 74
    p.append(f'<rect x="18" y="{fy}" width="{VW-36}" height="42" fill="#f7fafd" '
             f'stroke="#c3ccd8" stroke-width="0.8"/>')
    for j, (et, va) in enumerate([("Ancho del hueco", f"{W:.0f} mm"),
                                  ("Profundidad", f"{D:.0f} mm"),
                                  ("Bloque cabina", f"{cab_w:.0f} mm")]):
        cx_ = 18 + (VW - 36) * (j + 0.5) / 3
        p.append(f'<text x="{cx_:.0f}" y="{fy+17}" text-anchor="middle" font-size="7.5" '
                 f'fill="#7a8699">{et}</text>')
        p.append(f'<text x="{cx_:.0f}" y="{fy+32}" text-anchor="middle" font-size="10" '
                 f'fill="#1f2937">{va}</text>')

    # Cajetín
    p.append(f'<text x="18" y="26" font-size="11" fill="#1f2937" font-weight="bold">'
             f'VISTA ISOMÉTRICA DEL HUECO</text>')
    p.append(f'<text x="18" y="40" font-size="8" fill="#7a8699">'
             f'{(proyecto or "COPEX")[:40]} · {ns} paradas · planta a escala, '
             f'altura comprimida (no a escala)</text>')
    if malos:
        p.append(f'<rect x="18" y="{VH-24}" width="9" height="9" fill="#fbe9e7" '
                 f'stroke="#c0392b" stroke-width="0.7"/>')
        p.append(f'<text x="32" y="{VH-16}" font-size="8" fill="#7a8699">'
                 f'nivel con valores fuera de límite</text>')
    p.append("</svg>")
    return "".join(p)
