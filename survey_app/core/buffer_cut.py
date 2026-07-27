"""
Corte de buffers (buffer cutting).

Del plano se lee HKP = distancia entre el sticker de la cabina y el buffer de la
cabina cuando la cabina sirve el primer nivel. El usuario mide en obra el valor
real HKPR de cada buffer. El corte de cada buffer es:

    CutBuffer = HKP − HKPR

Todo en mm. Si CutBuffer < 0, no hay nada que cortar (el buffer real ya queda por
debajo del teórico → revisar en obra), se marca como aviso.
"""


def compute_buffer_cut(hkp: float, hkpr_list: list) -> dict:
    """hkp: valor del plano. hkpr_list: HKPR real de cada buffer.
    Devuelve {'HKP', 'buffers':[{'n','HKPR','CutBuffer','warn'}]}."""
    hkp = float(hkp or 0)
    buffers = []
    for i, hkpr in enumerate(hkpr_list, start=1):
        v = float(hkpr or 0)
        cut = round(hkp - v, 1)
        buffers.append({"n": i, "HKPR": v, "CutBuffer": cut, "warn": cut < 0})
    return {"HKP": hkp, "buffers": buffers}


# ══════════════════════════════════════════════════════════
#  Diagrama de cortes (v129)
# ══════════════════════════════════════════════════════════
def _mm(v) -> str:
    """mm: entero si lo es, 1 decimal si no (mismo criterio que diagrams._mm)."""
    try:
        v = float(v)
    except Exception:
        return str(v)
    return f"{v:.0f}" if abs(v - round(v)) < 0.05 else f"{v:.1f}"


def _esc(s) -> str:
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def buffer_cut_svg(res: dict, proyecto: str = "") -> str:
    """Alzado esquemático del corte de cada buffer (v182, replanteado).

    HKP y HKPR NO son alturas: son la HOLGURA (distancia) entre el sticker de la
    cabina y el borde superior del buffer — dos elementos que no se tocan. HKP es
    la de diseño (del plano) y HKPR la medida en obra. Cortar el buffer baja su
    borde superior y por tanto AGRANDA la holgura; el corte = HKP − HKPR es la
    rebanada que se quita del borde superior para pasar de HKPR a HKP.

    Por eso el dibujo muestra, arriba, el sticker (barra fija) y, común a todos,
    la línea HKP (dónde debe quedar el borde superior del buffer tras cortar).
    Por buffer: el borde real (a HKPR del sticker) y, si HKPR < HKP, la rebanada
    roja entre el borde real y la línea HKP = lo que se corta. Si HKPR > HKP la
    holgura ya es mayor que la de diseño: nada que cortar, se marca «revisar».

    La holgura sticker↔buffer no va a escala (rótulo ≈); el corte sí, a escala
    ampliada para que unos pocos mm se vean. Se declara en el pie.
    """
    bufs = (res or {}).get("buffers") or []
    if not bufs:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>'

    NAVY, RED, REDBG = "#1a3a5c", "#c0392b", "#fdecec"
    AMBER, AMBERBG = "#c77700", "#fff4e0"
    GREY, GREYLN, INK, MUT, GREEN = "#eef2f7", "#8a94a6", "#1f2937", "#7a8699", "#1e8449"

    hkp = float(res.get("HKP") or 0)
    n = len(bufs)
    paso = max(96, min(150, 660 // max(1, n)))
    LEFT = 78
    VW = max(460, LEFT + paso * n + 26)
    VH = 300

    y_stick = 60                 # borde inferior del sticker (referencia)
    STICK_H = 11
    GAP_VIS = 72                 # holgura visual sticker→línea HKP (NO a escala)
    y_hkp = y_stick + GAP_VIS    # línea HKP: borde superior de diseño (común)
    CUT_BAND = 56                # px del mayor corte por encima de la línea HKP
    BUF_H = 58                   # alto esquemático del cuerpo del buffer
    y_bot = y_hkp + BUF_H        # base (piso) del buffer

    cuts = [float(b["CutBuffer"]) for b in bufs]
    maxc = max((abs(c) for c in cuts), default=0.0)
    esc = (CUT_BAND / maxc) if maxc > 0.05 else 0.0    # mm → px (corte)
    bw = min(48, int(paso * 0.5))

    x0, x1 = LEFT - 44, VW - 20
    p = [f'<svg viewBox="0 0 {VW} {VH}" xmlns="http://www.w3.org/2000/svg" '
         f'style="width:100%;max-width:{VW}px;font-family:Arial,Helvetica,sans-serif;'
         f'display:block;margin:0 auto">',
         f'<rect x="0" y="0" width="{VW}" height="{VH}" fill="#ffffff"/>',
         f'<text x="18" y="24" font-size="11" fill="{INK}" font-weight="bold">'
         f'CORTE DE BUFFERS</text>',
         f'<text x="18" y="37" font-size="8" fill="{MUT}">'
         f'cortar el buffer baja su borde y agranda la holgura sticker↔buffer '
         f'hasta HKP = {_mm(hkp)} mm · corte = HKP − HKPR</text>']
    if proyecto:
        p.append(f'<text x="{VW-18}" y="24" text-anchor="end" font-size="9" '
                 f'fill="{INK}" font-weight="bold">{_esc(proyecto)}</text>')

    # ── Sticker de cabina (barra fija, referencia común) ──
    p.append(f'<rect x="{x0}" y="{y_stick-STICK_H}" width="{x1-x0}" height="{STICK_H}" '
             f'fill="{NAVY}"/>')
    p.append(f'<text x="{(x0+x1)/2:.0f}" y="{y_stick-2}" text-anchor="middle" '
             f'font-size="8" fill="#ffffff" font-weight="bold">STICKER DE CABINA</text>')

    # ── Línea HKP: borde superior de diseño (común a todos) ──
    p.append(f'<line x1="{x0}" y1="{y_hkp}" x2="{x1}" y2="{y_hkp}" '
             f'stroke="{NAVY}" stroke-width="1.3" stroke-dasharray="9,3,2,3"/>')
    p.append(f'<text x="{x1}" y="{y_hkp-4}" text-anchor="end" font-size="8.5" '
             f'fill="{NAVY}" font-weight="bold">HKP diseño {_mm(hkp)}</text>')

    # ── Cota de la holgura HKP en el margen izquierdo (no a escala: ≈) ──
    xd = 24
    ymid = (y_stick + y_hkp) / 2
    p.append(f'<line x1="{xd}" y1="{y_stick}" x2="{xd}" y2="{y_hkp}" '
             f'stroke="{MUT}" stroke-width="0.9"/>')
    p.append(f'<path d="M{xd-3},{y_stick+5} L{xd},{y_stick} L{xd+3},{y_stick+5}" '
             f'fill="none" stroke="{MUT}" stroke-width="0.9"/>')
    p.append(f'<path d="M{xd-3},{y_hkp-5} L{xd},{y_hkp} L{xd+3},{y_hkp-5}" '
             f'fill="none" stroke="{MUT}" stroke-width="0.9"/>')
    p.append(f'<rect x="{xd-6}" y="{ymid-6:.0f}" width="12" height="12" fill="#ffffff"/>')
    p.append(f'<text x="{xd}" y="{ymid+3:.0f}" text-anchor="middle" font-size="9" '
             f'fill="{MUT}">≈</text>')
    p.append(f'<text x="{xd}" y="{y_hkp+11}" text-anchor="middle" font-size="7.5" '
             f'fill="{MUT}">HKP</text>')

    for i, b in enumerate(bufs):
        cx = LEFT + paso * i + paso * 0.5
        hkpr = float(b["HKPR"])
        corte = float(b["CutBuffer"])
        warn = bool(b.get("warn"))
        xL = cx - bw / 2

        if warn:
            # HKPR > HKP: el borde real queda POR DEBAJO de la línea de diseño
            # (holgura ya mayor). No hay nada que cortar → revisar.
            yreal = min(y_bot - 10, y_hkp + (abs(corte) * esc if esc else 16))
            p.append(f'<rect x="{xL:.1f}" y="{yreal:.1f}" width="{bw}" '
                     f'height="{y_bot-yreal:.1f}" fill="{GREY}" stroke="{GREYLN}" '
                     f'stroke-width="1"/>')
            # hueco de más entre la línea HKP y el borde real (falta material)
            p.append(f'<rect x="{xL:.1f}" y="{y_hkp}" width="{bw}" '
                     f'height="{yreal-y_hkp:.1f}" fill="{AMBERBG}" stroke="{AMBER}" '
                     f'stroke-width="0.8" stroke-dasharray="3,2"/>')
            p.append(f'<line x1="{xL-4:.1f}" y1="{yreal:.1f}" x2="{cx+bw/2+4:.1f}" '
                     f'y2="{yreal:.1f}" stroke="{AMBER}" stroke-width="2"/>')
            p.append(f'<text x="{cx:.1f}" y="{(y_hkp+yreal)/2+3:.1f}" text-anchor="middle" '
                     f'font-size="8" fill="{AMBER}" font-weight="bold">revisar</text>')
        else:
            # cuerpo final del buffer: borde superior en la línea HKP (tras cortar)
            p.append(f'<rect x="{xL:.1f}" y="{y_hkp}" width="{bw}" height="{BUF_H}" '
                     f'fill="{GREY}" stroke="{GREYLN}" stroke-width="1"/>')
            if corte > 0.05 and esc:
                yreal = y_hkp - corte * esc          # borde real, por encima de HKP
                hslice = y_hkp - yreal
                # rebanada a cortar (borde real → línea HKP)
                p.append(f'<rect x="{xL:.1f}" y="{yreal:.1f}" width="{bw}" '
                         f'height="{hslice:.1f}" fill="{REDBG}" stroke="{RED}" '
                         f'stroke-width="0.9"/>')
                nb = max(2, int(hslice // 6))
                for k in range(nb):
                    yy = yreal + hslice * (k + 1) / (nb + 1)
                    p.append(f'<line x1="{xL:.1f}" y1="{yy:.1f}" x2="{cx+bw/2:.1f}" '
                             f'y2="{yy-5:.1f}" stroke="{RED}" stroke-width="0.5"/>')
                # borde real (nivel medido, a HKPR del sticker)
                p.append(f'<line x1="{xL-4:.1f}" y1="{yreal:.1f}" x2="{cx+bw/2+4:.1f}" '
                         f'y2="{yreal:.1f}" stroke="{RED}" stroke-width="2"/>')
                if hslice >= 13:
                    p.append(f'<text x="{cx:.1f}" y="{(yreal+y_hkp)/2+3:.1f}" '
                             f'text-anchor="middle" font-size="8.5" fill="{RED}" '
                             f'font-weight="bold">{_mm(corte)}</text>')
                p.append(f'<text x="{cx:.1f}" y="{yreal-4:.1f}" text-anchor="middle" '
                         f'font-size="7.5" fill="{RED}">borde real</text>')
            else:
                # corte ≈ 0: el borde real ya coincide con el de diseño
                p.append(f'<line x1="{xL-4:.1f}" y1="{y_hkp}" x2="{cx+bw/2+4:.1f}" '
                         f'y2="{y_hkp}" stroke="{GREEN}" stroke-width="2"/>')
                p.append(f'<text x="{cx:.1f}" y="{y_hkp-4:.1f}" text-anchor="middle" '
                         f'font-size="7.5" fill="{GREEN}">sin corte</text>')

        # etiqueta bajo cada buffer
        _cc = RED if (corte > 0.05 and not warn) else (AMBER if warn else GREEN)
        p.append(f'<text x="{cx:.1f}" y="{y_bot+16:.0f}" text-anchor="middle" '
                 f'font-size="8.5" fill="{INK}" font-weight="bold">Buffer {b["n"]}</text>')
        p.append(f'<text x="{cx:.1f}" y="{y_bot+28:.0f}" text-anchor="middle" '
                 f'font-size="7.5" fill="{MUT}">HKPR {_mm(hkpr)}</text>')
        p.append(f'<text x="{cx:.1f}" y="{y_bot+40:.0f}" text-anchor="middle" '
                 f'font-size="7.5" fill="{_cc}" font-weight="bold">'
                 f'corte {_mm(corte)}</text>')

    # ── Leyenda ──
    p.append(f'<rect x="18" y="{VH-24}" width="9" height="9" fill="{REDBG}" '
             f'stroke="{RED}" stroke-width="0.7"/>')
    p.append(f'<text x="31" y="{VH-16}" font-size="7.5" fill="{MUT}">material a cortar '
             f'(rebaja el buffer hasta HKP)</text>')
    p.append(f'<rect x="230" y="{VH-24}" width="9" height="9" fill="{AMBERBG}" '
             f'stroke="{AMBER}" stroke-width="0.7" stroke-dasharray="2,1.5"/>')
    p.append(f'<text x="243" y="{VH-16}" font-size="7.5" fill="{MUT}">holgura ya mayor '
             f'que HKP → revisar</text>')
    p.append(f'<text x="{VW-18}" y="{VH-16}" text-anchor="end" font-size="7" fill="{MUT}">'
             f'holgura ≈ no a escala · corte a escala ampliada</text>')
    p.append("</svg>")
    return "".join(p)
