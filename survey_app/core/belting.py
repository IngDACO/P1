"""
Belting — altura a la que dejar la cabina (por debajo del FFL del piso más alto)
para instalar los belts, respetando el recorrido de diseño.

Datos:
  Del plano:   HGP (striker↔buffer del contrapeso con la cabina en el último piso), HQ (travel height).
  Del usuario: HGPR (distancia REAL striker↔buffer del contrapeso).  → por elevador.

Cálculo (todo en mm; HGP/HGPR/HQ/DSTS en mm):
  DSTS = HGPR − HGP − (HQ/1000)
  · HQ/1000 = elongación del belt sobre el recorrido (≈0.1% del travel).
  · DSTS > 0 = cuánto BAJA la cabina respecto al FFL del piso más alto.
"""


def compute_dsts(hgp, hq, hgpr) -> float:
    return float(hgpr) - float(hgp) - float(hq) / 1000.0


def compute_belting(hgp, hq, hgpr_list) -> list:
    """DSTS por elevador. hgpr_list = lista de HGPR (uno por elevador)."""
    out = []
    for i, h in enumerate(hgpr_list):
        out.append({"elevador": i + 1, "hgpr": float(h),
                    "dsts": round(compute_dsts(hgp, hq, h), 1)})
    return out


def _mm(v) -> str:
    try:
        v = float(v)
    except Exception:
        return str(v)
    return f"{v:.0f}" if abs(v - round(v)) < 0.05 else f"{v:.1f}"


def _esc(s) -> str:
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def belting_svg(results: list, proyecto: str = "") -> str:
    """Diagrama por elevador (v183, replanteado).

    DSTS es la posición CON SIGNO de la cabina respecto al FFL del piso más alto:
    DSTS > 0 = la cabina baja esa distancia POR DEBAJO del FFL; DSTS < 0 = queda
    POR ENCIMA. El dibujo antiguo ponía la cabina siempre debajo en una posición
    fija, contradiciendo a la tabla y sin reflejar la magnitud. Ahora el FFL es la
    línea de referencia común y cada cabina se coloca a su DSTS con signo, a escala
    ampliada común para comparar entre elevadores. Sin <marker>/<defs> (compat)."""
    results = results or []
    n = max(1, len(results))
    RED, AMBER, CABF, CABS = "#c0392b", "#b5731a", "#dbe6f2", "#2e6da4"
    GRID, INK, MUT = "#e6e9ef", "#333333", "#8a8f99"

    colw = 150
    ML = 24
    VW = ML * 2 + n * colw
    VH = 300
    y_ffl = 134            # línea FFL común (referencia)
    BAND = 66              # px del mayor |DSTS|
    cab_h = 44
    frame_top, frame_bot = 58, 252

    dstss = [float(r["dsts"]) for r in results]
    maxabs = max((abs(d) for d in dstss), default=0.0)
    esc = (BAND / maxabs) if maxabs > 0.05 else 0.0     # mm → px

    p = [f'<svg viewBox="0 0 {VW} {VH}" xmlns="http://www.w3.org/2000/svg" '
         f'style="width:100%;max-width:{VW}px;font-family:Arial,Helvetica,sans-serif;'
         f'display:block;margin:0 auto">',
         f'<rect x="0" y="0" width="{VW}" height="{VH}" fill="#ffffff"/>',
         f'<text x="18" y="22" font-size="12" fill="#1a3a5c" font-weight="bold">'
         f'BELTING — posición de la cabina respecto al FFL del piso más alto</text>',
         f'<text x="18" y="36" font-size="8.5" fill="{MUT}">'
         f'DSTS = cuánto baja (+, por debajo) o sube (−, por encima) la cabina · '
         f'posición a escala ampliada</text>']
    if proyecto:
        p.append(f'<text x="{VW-18}" y="22" text-anchor="end" font-size="9" '
                 f'fill="#1f2937" font-weight="bold">{_esc(proyecto)}</text>')

    # ── FFL: línea de referencia común a todos los elevadores ──
    p.append(f'<line x1="{ML}" y1="{y_ffl}" x2="{VW-ML}" y2="{y_ffl}" '
             f'stroke="{RED}" stroke-width="2"/>')
    p.append(f'<text x="{ML+2}" y="{y_ffl-4}" font-size="8.5" fill="{RED}" '
             f'font-weight="bold">FFL piso más alto</text>')

    for i, r in enumerate(results):
        x0 = ML + i * colw
        w = colw - 34
        cx = x0 + w / 2
        dsts = float(r["dsts"])
        hgpr = float(r.get("hgpr", 0))
        roof = y_ffl + dsts * esc            # techo de la cabina (con signo)

        # marco del hueco (guía)
        p.append(f'<rect x="{x0:.1f}" y="{frame_top}" width="{w:.1f}" '
                 f'height="{frame_bot-frame_top}" fill="none" stroke="{GRID}" '
                 f'stroke-width="1"/>')
        # cabina, colocada a su DSTS
        cabw = w - 46
        p.append(f'<rect x="{cx-cabw/2:.1f}" y="{roof:.1f}" width="{cabw:.1f}" '
                 f'height="{cab_h}" rx="3" fill="{CABF}" stroke="{CABS}" '
                 f'stroke-width="1.2"/>')
        p.append(f'<text x="{cx:.1f}" y="{roof+cab_h/2+3:.1f}" text-anchor="middle" '
                 f'font-size="9" fill="{CABS}">Cabina</text>')

        # cota DSTS: del FFL al techo de la cabina (línea; el valor va al pie
        # para no solaparse con la cabina cuando el DSTS es pequeño/negativo)
        dimx = x0 + 12
        if abs(roof - y_ffl) > 1:
            ya, yb = (y_ffl, roof) if roof >= y_ffl else (roof, y_ffl)
            p.append(f'<line x1="{dimx:.1f}" y1="{ya:.1f}" x2="{dimx:.1f}" y2="{yb:.1f}" '
                     f'stroke="{AMBER}" stroke-width="1.3"/>')
            for yy in (ya, yb):
                p.append(f'<line x1="{dimx-3:.1f}" y1="{yy:.1f}" x2="{dimx+3:.1f}" '
                         f'y2="{yy:.1f}" stroke="{AMBER}" stroke-width="1.3"/>')

        # etiquetas al pie (línea base fija, alineadas entre elevadores)
        if dsts > 0.05:
            _dir, _dc = "por debajo del FFL", RED
        elif dsts < -0.05:
            _dir, _dc = "por encima del FFL", CABS
        else:
            _dir, _dc = "en el FFL", MUT
        p.append(f'<text x="{cx:.1f}" y="266" text-anchor="middle" font-size="9.5" '
                 f'fill="{INK}" font-weight="bold">Elevador {r["elevador"]}</text>')
        p.append(f'<text x="{cx:.1f}" y="279" text-anchor="middle" font-size="9" '
                 f'fill="{_dc}" font-weight="bold">DSTS {_mm(dsts)} mm</text>')
        p.append(f'<text x="{cx:.1f}" y="290" text-anchor="middle" font-size="7.5" '
                 f'fill="{MUT}">{_dir} · HGPR {_mm(hgpr)}</text>')

    p.append("</svg>")
    return "".join(p)
