"""
Corte de rieles (rail cutting).

Extrae LFKK y LFGK del PDF y calcula los cortes de riel para cada elevador
del shaft, en dos casos:

CASO 1 — el riel a cortar es el PRIMERO instalado (el de más abajo):
    A      = n2500·2500 + n5000·5000           (iguales para todos los elevadores)
    RC     = L + LFKK   (riel de cabina)
    RCW    = L + LFGK   (riel de contrapeso)
    CutRC  = RC − A     CutRCW = RCW − A        (L varía por elevador)

CASO 2 — el riel a cortar es el ÚLTIMO instalado (el de más arriba):
    El usuario llena RZ, RO, RF, RB por elevador. Dos sub-casos:
      penúltimo POR ENCIMA del FFL:  CutR* = LF − R*
      penúltimo POR DEBAJO del FFL:  CutR* = LF + R*
    (LFKK para RZ/RO ; LFGK para RF/RB)
"""
import logging
import re

logger = logging.getLogger(__name__)


# ── Extracción de LFKK / LFGK del PDF ────────────────────────
def extract_lf(pdf_file) -> dict:
    """Devuelve {'LFKK': float|None, 'LFGK': float|None} leídos del PDF."""
    result = {"LFKK": None, "LFGK": None}
    try:
        # Reusa la lectura cacheada: antes esto reparseaba el PDF entero (~71 s)
        from extractors.schindler import page_texts
        text = []
        for pos, plano in page_texts(pdf_file):
            text.append(pos or "")
            text.append(plano or "")
        full = "\n".join(text)
        for key in ("LFKK", "LFGK"):
            m = re.search(rf"{key}\s*[=:\s]\s*(-?\d+(?:[.,]\d+)?)", full, re.IGNORECASE)
            if m:
                result[key] = float(m.group(1).replace(",", "."))
    except Exception as e:
        logger.warning("rail_cut: extracción LF falló: %s", e)
    return result


# ── CASO 1 ───────────────────────────────────────────────────
def compute_case1(lfkk: float, lfgk: float, n2500: int, n5000: int,
                  L_list: list) -> dict:
    """
    L_list: lista con L de cada elevador.
    Devuelve dict con A y, por elevador, RC/RCW/CutRC/CutRCW.
    """
    A = int(n2500) * 2500.0 + int(n5000) * 5000.0
    elevadores = []
    for L in L_list:
        L = float(L or 0)
        rc  = L + float(lfkk)
        rcw = L + float(lfgk)
        elevadores.append({
            "L": L, "RC": rc, "RCW": rcw,
            "CutRC": rc - A, "CutRCW": rcw - A,
        })
    return {"A": A, "elevadores": elevadores}


# ── CASO 2 ───────────────────────────────────────────────────
def compute_case2(lfkk: float, lfgk: float, rows: list, subcaso: str) -> list:
    """
    rows: lista por elevador con {'RZ','RO','RF','RB'}.
    subcaso: 'encima'  → CutR* = LF − R*
             'debajo'  → CutR* = LF + R*
    RZ/RO usan LFKK ; RF/RB usan LFGK.
    """
    sign = -1.0 if subcaso == "encima" else 1.0
    out = []
    for r in rows:
        rz = float(r.get("RZ", 0) or 0)
        ro = float(r.get("RO", 0) or 0)
        rf = float(r.get("RF", 0) or 0)
        rb = float(r.get("RB", 0) or 0)
        out.append({
            "CutRZ": float(lfkk) + sign * rz,
            "CutRO": float(lfkk) + sign * ro,
            "CutRF": float(lfgk) + sign * rf,
            "CutRB": float(lfgk) + sign * rb,
        })
    return out


# ══════════════════════════════════════════════════════════
#  Diagrama de cortes (v130)
# ══════════════════════════════════════════════════════════
def _mm(v) -> str:
    try:
        v = float(v)
    except Exception:
        return str(v)
    return f"{v:.0f}" if abs(v - round(v)) < 0.05 else f"{v:.1f}"


def _esc(s) -> str:
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def rail_cut_svg(res: dict, caso: int = 1, n2500: int = 0, n5000: int = 0,
                 proyecto: str = "") -> str:
    """Diagrama de los cortes de riel.

    Hasta v129 esta herramienta daba SOLO numeros para una operacion
    irreversible. Ahora se ve de donde sale el corte.

    CASO 1 — alzado real: la pila de rieles estandar instalados (A) frente a la
    longitud requerida por elevador (RC / RCW). Lo que sobresale es el corte.
    CASO 2 — barras comparativas de los cuatro cortes por elevador: ahi no hay
    pila que dibujar, los valores vienen medidos en obra.
    """
    elevs = (res or {}).get("elevadores") or []
    if not elevs:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>'

    cab = ('<text x="18" y="26" font-size="11" fill="#1f2937" font-weight="bold">'
           'CORTE DE RIELES</text>')

    if caso == 1:
        A = float(res.get("A") or 0)
        req = []
        for e in elevs:
            req += [float(e["RC"]), float(e["RCW"])]
        vmax = max([A] + req) or 1.0

        n = len(elevs)
        paso = max(130, min(200, 640 // max(1, n)))
        VW = max(470, 100 + paso * n + 30)
        VH, TOP, ALTO = 366, 74, 196
        esc = ALTO / vmax
        base = TOP + ALTO
        p = [f'<svg viewBox="0 0 {VW} {VH}" xmlns="http://www.w3.org/2000/svg" '
             f'style="width:100%;max-width:{VW}px;font-family:Arial,Helvetica,sans-serif;'
             f'display:block;margin:0 auto">',
             f'<rect x="0" y="0" width="{VW}" height="{VH}" fill="#ffffff"/>', cab,
             f'<text x="18" y="40" font-size="8" fill="#5b6472">'
             f'Caso 1 &#183; pila instalada A = {_mm(A)} mm '
             f'({n2500}&#215;2500 + {n5000}&#215;5000) &#183; corte = requerido &#8722; A</text>']
        if proyecto:
            p.append(f'<text x="{VW-18}" y="26" text-anchor="end" font-size="9" '
                     f'fill="#1f2937" font-weight="bold">{_esc(proyecto)}</text>')

        yA = base - A * esc
        p.append(f'<line x1="74" y1="{yA:.1f}" x2="{VW-24}" y2="{yA:.1f}" '
                 f'stroke="#1a3a5c" stroke-width="1.2" stroke-dasharray="9,3,2,3"/>')
        p.append(f'<text x="{VW-22}" y="{yA-4:.1f}" text-anchor="end" font-size="8.5" '
                 f'fill="#1a3a5c">A {_mm(A)}</text>')

        # Pila estándar A como UN bloque. ⚠️ La app tiene los CONTEOS (n2500/n5000),
        # NO el orden de los rieles, así que NO se inventa la secuencia de la pila
        # (antes se dibujaban los 5000 abajo y los 2500 arriba, un orden ficticio).
        if A > 0:
            p.append(f'<rect x="30" y="{yA:.1f}" width="36" height="{A*esc:.1f}" '
                     f'fill="#eef2f7" stroke="#8a94a6" stroke-width="1.1"/>')
            p.append(f'<text x="48" y="{(yA+base)/2:.1f}" text-anchor="middle" '
                     f'font-size="8" fill="#5b6472" font-weight="bold">A</text>')
            p.append(f'<text x="48" y="{(yA+base)/2+11:.1f}" text-anchor="middle" '
                     f'font-size="6.5" fill="#667080">pila estándar</text>')

        # Piso: donde se apoya el PRIMER riel — el que se corta en el Caso 1.
        p.append(f'<line x1="26" y1="{base:.1f}" x2="{VW-24}" y2="{base:.1f}" '
                 f'stroke="#1f2937" stroke-width="1.5"/>')

        for i, e in enumerate(elevs):
            cx = 100 + paso * i
            for j, (lbl, largo, corte) in enumerate(
                    (("RC", e["RC"], e["CutRC"]), ("RCW", e["RCW"], e["CutRCW"]))):
                x = cx + j * 48
                largo, corte = float(largo), float(corte)
                y0 = base - largo * esc
                # Columna requerida (RC/RCW), desde el PISO (base) hacia arriba.
                p.append(f'<rect x="{x:.1f}" y="{y0:.1f}" width="36" '
                         f'height="{largo*esc:.1f}" fill="#f7fafd" '
                         f'stroke="#1a3a5c" stroke-width="1.1"/>')
                if abs(corte) > 0.05:
                    # ⚠️ El corte va en el PRIMER riel instalado (el de ABAJO), así
                    # que se marca AL PIE de la columna, no arriba. corte<0 = se
                    # recorta (rojo); corte>0 = falta y se añade al primer riel (verde).
                    h = min(abs(corte) * esc, largo * esc)
                    yc = base - h
                    stk, fll = (("#c0392b", "#fcebeb") if corte < 0
                                else ("#1e8449", "#e8f5e9"))
                    p.append(f'<rect x="{x:.1f}" y="{yc:.1f}" width="36" '
                             f'height="{h:.1f}" fill="{fll}" stroke="{stk}" '
                             f'stroke-width="1.0"/>')
                    p.append(f'<text x="{x+18:.1f}" y="{yc + h/2 + 3:.1f}" '
                             f'text-anchor="middle" font-size="8.5" fill="{stk}" '
                             f'font-weight="bold">{_mm(corte)}</text>')
                p.append(f'<text x="{x+18:.1f}" y="{base+14:.1f}" text-anchor="middle" '
                         f'font-size="7.5" fill="#1f2937">{lbl}</text>')
            p.append(f'<text x="{cx+42:.1f}" y="{base+31:.1f}" text-anchor="middle" '
                     f'font-size="8.5" fill="#1f2937" font-weight="bold">Elev. {i+1}</text>')
            p.append(f'<text x="{cx+42:.1f}" y="{base+43:.1f}" text-anchor="middle" '
                     f'font-size="7.5" fill="#5b6472">L {_mm(e["L"])}</text>')

        p.append(f'<rect x="18" y="{VH-26}" width="9" height="9" fill="#fcebeb" '
                 f'stroke="#c0392b" stroke-width="0.7"/>')
        p.append(f'<rect x="150" y="{VH-26}" width="9" height="9" fill="#e8f5e9" '
                 f'stroke="#1e8449" stroke-width="0.7"/>')
        # El corte va SIEMPRE en el 1er riel (el de abajo, primero instalado): la
        # leyenda lo dice y el color distingue recortar (rojo) de añadir (verde).
        p.append(f'<text x="32" y="{VH-18}" font-size="8" fill="#5b6472">'
                 f'recorta el 1er riel</text>')
        p.append(f'<text x="164" y="{VH-18}" font-size="8" fill="#5b6472">'
                 f'a&#241;ade al 1er riel &#183; el corte va en el riel de ABAJO '
                 f'(mismo valor con signo que la tabla)</text>')
        p.append("</svg>")
        return "".join(p)

    # ── CASO 2 — esquema de rieles (v178) ──
    # 4 rieles por elevador: cabina (RZ, RO) y contrapeso (RF, RB). Se marca el
    # ÚLTIMO riel instalado (el de ARRIBA) como el que se corta, con su valor.
    # ⚠️ El Caso 2 NO tiene longitudes (los valores se miden en obra): las alturas
    # de los rieles son ILUSTRATIVAS, uniformes, no a escala.
    rails = [("CutRZ", "RZ", "cabina"), ("CutRO", "RO", "cabina"),
             ("CutRF", "RF", "contra"), ("CutRB", "RB", "contra")]
    COL = {"cabina": "#1a3a5c", "contra": "#0e7490"}
    railW, gsmall, gpair, gelev, left = 26, 10, 22, 44, 44
    xs = [0, railW + gsmall, railW * 2 + gsmall + gpair, railW * 3 + gsmall * 2 + gpair]
    unit = xs[3] + railW
    n = len(elevs)
    VW = max(430, left + unit * n + gelev * max(0, n - 1) + 30)
    VH, TOP, H = 300, 96, 128
    base = TOP + H
    cutH = 15
    p = [f'<svg viewBox="0 0 {VW} {VH}" xmlns="http://www.w3.org/2000/svg" '
         f'style="width:100%;max-width:{VW}px;font-family:Arial,Helvetica,sans-serif;'
         f'display:block;margin:0 auto">',
         f'<rect x="0" y="0" width="{VW}" height="{VH}" fill="#ffffff"/>', cab,
         f'<text x="18" y="40" font-size="8" fill="#5b6472">'
         f'Caso 2 &#183; se corta el &#218;LTIMO riel (el de arriba) &#183; '
         f'alturas ilustrativas, no a escala</text>',
         f'<line x1="26" y1="{base}" x2="{VW-24}" y2="{base}" '
         f'stroke="#1f2937" stroke-width="1.5"/>']
    if proyecto:
        p.append(f'<text x="{VW-18}" y="26" text-anchor="end" font-size="9" '
                 f'fill="#1f2937" font-weight="bold">{_esc(proyecto)}</text>')
    for i, e in enumerate(elevs):
        ex = left + i * (unit + gelev)
        # Encabezados de grupo
        p.append(f'<text x="{ex + (xs[0]+xs[1]+railW)/2:.1f}" y="{TOP-24:.0f}" '
                 f'text-anchor="middle" font-size="7.5" fill="#5b6472" '
                 f'font-weight="bold">Cabina</text>')
        p.append(f'<text x="{ex + (xs[2]+xs[3]+railW)/2:.1f}" y="{TOP-24:.0f}" '
                 f'text-anchor="middle" font-size="7.5" fill="#5b6472" '
                 f'font-weight="bold">Contrapeso</text>')
        for j, (k, lbl, grp) in enumerate(rails):
            x = ex + xs[j]
            col = COL[grp]
            v = float(e.get(k) or 0)
            # Cuerpo del riel (altura ilustrativa)
            p.append(f'<rect x="{x:.1f}" y="{TOP}" width="{railW}" height="{H}" rx="3" '
                     f'fill="#f2f6fa" stroke="{col}" stroke-width="1.2"/>')
            # Banda de corte arriba (el último tramo instalado, el que se corta)
            p.append(f'<rect x="{x:.1f}" y="{TOP}" width="{railW}" height="{cutH}" '
                     f'fill="{col}" fill-opacity="0.85"/>')
            p.append(f'<line x1="{x-3:.1f}" y1="{TOP+cutH}" x2="{x+railW+3:.1f}" '
                     f'y2="{TOP+cutH}" stroke="#c0392b" stroke-width="1.0" '
                     f'stroke-dasharray="3,2"/>')
            # Valor del corte, arriba del riel
            p.append(f'<text x="{x+railW/2:.1f}" y="{TOP-6:.0f}" text-anchor="middle" '
                     f'font-size="8.5" fill="{col}" font-weight="bold">{_mm(v)}</text>')
            # Etiqueta del riel al pie
            p.append(f'<text x="{x+railW/2:.1f}" y="{base+13:.0f}" text-anchor="middle" '
                     f'font-size="7.5" fill="#1f2937">{lbl}</text>')
        p.append(f'<text x="{ex+unit/2:.1f}" y="{base+30:.0f}" text-anchor="middle" '
                 f'font-size="8.5" fill="#1f2937" font-weight="bold">Elevador {i+1}</text>')

    _cab, _con = COL["cabina"], COL["contra"]
    p.append(f'<rect x="18" y="{VH-26}" width="9" height="9" fill="{_cab}" '
             f'fill-opacity="0.85"/>')
    p.append(f'<text x="32" y="{VH-18}" font-size="8" fill="#5b6472">cabina (RZ, RO)</text>')
    p.append(f'<rect x="118" y="{VH-26}" width="9" height="9" fill="{_con}" '
             f'fill-opacity="0.85"/>')
    p.append(f'<text x="132" y="{VH-18}" font-size="8" fill="#5b6472">'
             f'contrapeso (RF, RB) &#183; el corte (mm) va en el riel de ARRIBA</text>')
    p.append("</svg>")
    return "".join(p)
