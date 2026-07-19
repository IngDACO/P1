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


def buffer_cut_svg(res: dict) -> str:
    """Alzado esquemático del corte de cada buffer.

    Hasta v128 esta herramienta daba SOLO números para una operación
    irreversible (cortar). El dibujo muestra, por buffer: el nivel de plano
    (HKP), el real medido (HKPR) y el trozo a cortar, que es la diferencia.

    La escala vertical es COMÚN a todos los buffers (así se comparan entre sí)
    pero NO es la del hueco: se ajusta al rango de valores para que un corte de
    pocos mm siga siendo visible. Se declara en el pie.
    """
    bufs = (res or {}).get("buffers") or []
    if not bufs:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>'

    hkp = float(res.get("HKP") or 0)
    vals = [float(b["HKPR"]) for b in bufs] + [hkp]
    vmin, vmax = min(vals), max(vals)
    if vmax - vmin < 1:
        vmin, vmax = vmin - 5, vmax + 5

    n = len(bufs)
    paso = max(78, min(150, 620 // max(1, n)))
    VW = max(420, 90 + paso * n + 40)
    VH, TOP, ALTO = 300, 66, 150
    esc = ALTO / (vmax - vmin)

    def Y(v):
        return TOP + (vmax - float(v)) * esc

    p = [f'<svg viewBox="0 0 {VW} {VH}" xmlns="http://www.w3.org/2000/svg" '
         f'style="width:100%;max-width:{VW}px;font-family:Arial,Helvetica,sans-serif;'
         f'display:block;margin:0 auto">',
         f'<rect x="0" y="0" width="{VW}" height="{VH}" fill="#ffffff"/>',
         f'<text x="18" y="26" font-size="11" fill="#1f2937" font-weight="bold">'
         f'CORTE DE BUFFERS</text>',
         f'<text x="18" y="40" font-size="8" fill="#7a8699">'
         f'HKP del plano {_mm(hkp)} mm · corte = HKP − HKPR · '
         f'escala vertical ajustada al rango</text>']

    # Nivel de plano (HKP): referencia comun
    yh = Y(hkp)
    p.append(f'<line x1="70" y1="{yh:.1f}" x2="{VW-24}" y2="{yh:.1f}" '
             f'stroke="#1a3a5c" stroke-width="1.2" stroke-dasharray="9,3,2,3"/>')
    p.append(f'<text x="{VW-22}" y="{yh-4:.1f}" text-anchor="end" font-size="8.5" '
             f'fill="#1a3a5c">HKP {_mm(hkp)}</text>')

    for i, b in enumerate(bufs):
        cx = 90 + paso * i + paso * 0.34
        hkpr = float(b["HKPR"])
        corte = float(b["CutBuffer"])
        yr = Y(hkpr)
        col = "#c0392b" if b.get("warn") else "#1a3a5c"

        # cuerpo del buffer, desde su nivel real hacia abajo
        p.append(f'<rect x="{cx-19:.1f}" y="{yr:.1f}" width="38" '
                 f'height="{max(6.0, TOP+ALTO+22-yr):.1f}" fill="#eef2f7" '
                 f'stroke="#8a94a6" stroke-width="1"/>')
        p.append(f'<line x1="{cx-24:.1f}" y1="{yr:.1f}" x2="{cx+24:.1f}" y2="{yr:.1f}" '
                 f'stroke="{col}" stroke-width="2"/>')

        # trozo a cortar (entre el real y el de plano)
        if abs(corte) > 0.05:
            y0v, y1v = (yr, yh) if corte > 0 else (yh, yr)
            p.append(f'<rect x="{cx-19:.1f}" y="{min(y0v,y1v):.1f}" width="38" '
                     f'height="{abs(y1v-y0v):.1f}" fill="#fcebeb" fill-opacity="0.9" '
                     f'stroke="#c0392b" stroke-width="0.8"/>')
            for k in range(3):
                yy = min(y0v, y1v) + abs(y1v - y0v) * (k + 1) / 4
                p.append(f'<line x1="{cx-19:.1f}" y1="{yy:.1f}" x2="{cx+19:.1f}" '
                         f'y2="{yy-5:.1f}" stroke="#c0392b" stroke-width="0.5"/>')
            p.append(f'<text x="{cx:.1f}" y="{(y0v+y1v)/2+3:.1f}" text-anchor="middle" '
                     f'font-size="9" fill="#c0392b" font-weight="bold">{_mm(corte)}</text>')

        p.append(f'<text x="{cx:.1f}" y="{TOP+ALTO+40:.1f}" text-anchor="middle" '
                 f'font-size="8.5" fill="#1f2937" font-weight="bold">Buffer {b["n"]}</text>')
        p.append(f'<text x="{cx:.1f}" y="{TOP+ALTO+52:.1f}" text-anchor="middle" '
                 f'font-size="7.5" fill="#7a8699">HKPR {_mm(hkpr)}</text>')
        if b.get("warn"):
            p.append(f'<text x="{cx:.1f}" y="{TOP+ALTO+64:.1f}" text-anchor="middle" '
                     f'font-size="7.5" fill="#c0392b">revisar</text>')

    p.append(f'<rect x="18" y="{VH-26}" width="9" height="9" fill="#fcebeb" '
             f'stroke="#c0392b" stroke-width="0.7"/>')
    p.append(f'<text x="32" y="{VH-18}" font-size="8" fill="#7a8699">'
             f'material a cortar</text>')
    p.append("</svg>")
    return "".join(p)
