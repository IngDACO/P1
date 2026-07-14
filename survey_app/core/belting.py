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


def belting_svg(results: list) -> str:
    """Diagrama conceptual (no a escala): cabina DSTS por debajo del FFL del piso más alto,
    una columna por elevador. Sin <marker>/<defs> (compat)."""
    n = max(1, len(results))
    colw = 160
    ML, MT = 20, 46
    VW = ML * 2 + n * colw
    VH = 300

    p = [f'<svg viewBox="0 0 {VW} {VH}" xmlns="http://www.w3.org/2000/svg" '
         f'style="width:100%;max-width:{VW}px;font-family:system-ui,sans-serif;display:block;margin:0 auto">']
    p.append(f'<text x="{VW/2:.0f}" y="20" text-anchor="middle" font-size="13" fill="#1a3a5c" '
             f'font-weight="bold">Belting — posición de la cabina bajo el FFL del piso más alto</text>')
    p.append(f'<text x="{VW/2:.0f}" y="36" text-anchor="middle" font-size="9" fill="#888">'
             f'DSTS = cuánto baja la cabina (mm) · esquema no a escala</text>')

    ffl_y = MT + 18
    cab_y = MT + 150   # techo de la cabina (visualmente separado)
    cab_h = 70
    for i, r in enumerate(results):
        x0 = ML + i * colw
        w  = colw - 30
        cx = x0 + w / 2

        # marco del hueco
        p.append(f'<rect x="{x0:.1f}" y="{ffl_y:.1f}" width="{w:.1f}" height="{cab_y + cab_h - ffl_y:.1f}" '
                 f'fill="none" stroke="#ddd" stroke-width="1"/>')
        # FFL del piso más alto
        p.append(f'<line x1="{x0:.1f}" y1="{ffl_y:.1f}" x2="{x0+w:.1f}" y2="{ffl_y:.1f}" '
                 f'stroke="#c0392b" stroke-width="2"/>')
        p.append(f'<text x="{x0+3:.1f}" y="{ffl_y-4:.1f}" font-size="8.5" fill="#c0392b">FFL piso más alto</text>')
        # cabina
        p.append(f'<rect x="{x0+15:.1f}" y="{cab_y:.1f}" width="{w-30:.1f}" height="{cab_h:.1f}" '
                 f'rx="3" fill="#dbe6f2" stroke="#2e6da4" stroke-width="1.2"/>')
        p.append(f'<text x="{cx:.1f}" y="{cab_y+cab_h/2+3:.1f}" text-anchor="middle" font-size="9" '
                 f'fill="#2e6da4">Cabina</text>')
        # cota DSTS (del FFL al techo de la cabina)
        dimx = x0 + 6
        p.append(f'<line x1="{dimx:.1f}" y1="{ffl_y:.1f}" x2="{dimx:.1f}" y2="{cab_y:.1f}" '
                 f'stroke="#BA7517" stroke-width="1.2"/>')
        for yy in (ffl_y, cab_y):
            p.append(f'<line x1="{dimx-3:.1f}" y1="{yy:.1f}" x2="{dimx+3:.1f}" y2="{yy:.1f}" '
                     f'stroke="#BA7517" stroke-width="1.2"/>')
        p.append(f'<text x="{dimx+5:.1f}" y="{(ffl_y+cab_y)/2:.1f}" font-size="9" fill="#BA7517" '
                 f'font-weight="bold">DSTS {r["dsts"]:.0f}</text>')
        # etiqueta elevador
        p.append(f'<text x="{cx:.1f}" y="{cab_y+cab_h+18:.1f}" text-anchor="middle" font-size="9.5" '
                 f'fill="#333" font-weight="bold">Elevador {r["elevador"]}</text>')
    p.append("</svg>")
    return "".join(p)
