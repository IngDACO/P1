"""
Cálculo de ubicación de líneas de plomada (plumb lines).

Entrada (independiente del survey):
  BKS, RAIL, TKSW, LengthTemplate, SF1, SF2, BSR, BS
  Si BSR < BS: SG, TG, OMEGA_SIDE (R/L)

Salida:
  - DBP, DBPW, RW
  - Punto P, cortes C1/C2, distancias diagonales
  - 6 líneas verticales V1..V6 (posición X), con V4/V6 desplazadas si BSR<BS

Lógica de desplazamiento (BSR < BS):
  - Z está del lado opuesto al Omega:  Omega R → Z L,  Omega L → Z R
  - LIMIT_ZB = SF1×0.3 (si Z izquierda)  |  SF2×0.3 (si Z derecha)
  - LIMIT_OB = (SG − TG/2) × 0.3
  - Búsqueda lineal (paso 0.5) del `paso` sobre 3 rangos → paso ≈ (BS − BSR)
  - Se sacrifica primero Z, luego Omega:
        desp_z     = −min(paso, LIMIT_ZB)
        desp_omega = +max(0, paso − LIMIT_ZB)
"""
import math

STEP  = 0.5
EPS   = 1e-9
RMAX  = 1000.0

# Nombres propios de cada línea (V1..V6 son solo claves internas)
LINE_NAMES = {
    "V1": "Plomo riel izquierdo",
    "V2": "Plomo riel derecho",
    "V3": "Pared teórica izquierda",
    "V4": "Pared real izquierda",
    "V5": "Pared teórica derecha",
    "V6": "Pared real derecha",
}
# Versión corta para el diagrama (poco espacio)
LINE_SHORT = {
    "V1": "Riel I",  "V2": "Riel D",
    "V3": "Teór I",  "V5": "Teór D",
    "V4": "Real I",  "V6": "Real D",
}


def _search_paso(dif: float, limit_zb: float, limit_ob: float):
    """Búsqueda lineal (resta 0.5 constante) sobre 3 rangos. Devuelve (paso, rango, fuera_rango)."""
    rem  = dif
    cur  = STEP
    paso = 0.0
    rango = "Ninguno"

    # Rango 1: [0, LIMIT_ZB]
    while cur <= limit_zb + EPS and rem > EPS:
        rem -= STEP
        paso = cur
        if rem <= EPS:
            rango = "Rango 1 [0, ZB]"
            break
        cur += STEP

    # Rango 2: (LIMIT_ZB, LIMIT_ZB + LIMIT_OB]
    if rango == "Ninguno":
        while cur <= (limit_zb + limit_ob) + EPS and rem > EPS:
            rem -= STEP
            paso = cur
            if rem <= EPS:
                rango = "Rango 2 (ZB, ZB+OB]"
                break
            cur += STEP

    # Rango 3: (LIMIT_ZB + LIMIT_OB, 1000]
    if rango == "Ninguno":
        while cur <= RMAX + EPS and rem > EPS:
            rem -= STEP
            paso = cur
            if rem <= EPS:
                rango = "Rango 3 (ZB+OB, 1000]"
                break
            cur += STEP

    fuera = rem > EPS
    if fuera:
        rango = "FUERA DE RANGO (> 1000)"
    return paso, rango, fuera


def compute_plumb(inp: dict) -> dict:
    """Calcula todas las magnitudes de plomada. `inp` es un dict con las entradas."""
    bks  = float(inp["BKS"]);  rail = float(inp["RAIL"])
    tksw = float(inp["TKSW"]); lt   = float(inp["LengthTemplate"])
    sf1  = float(inp["SF1"]);  sf2  = float(inp["SF2"])
    bsr  = float(inp["BSR"]);  bs   = float(inp["BS"])

    # ── Base ────────────────────────────────────────────────
    dbp  = bks + rail
    dbpw = tksw - 150.0
    rw   = dbpw - lt

    P  = (dbp / 2.0, rw)
    C1 = (0.0, dbpw)
    C2 = (dbp, dbpw)
    d1 = math.hypot(P[0] - C1[0], P[1] - C1[1])
    d2 = math.hypot(P[0] - C2[0], P[1] - C2[1])

    # ── 6 líneas verticales (posición inicial) ──────────────
    rail2 = rail / 2.0
    half  = (bsr - bs) / 2.0     # negativo cuando BSR < BS

    x_v1 = 0.0
    x_v2 = dbp
    x_v3 = 0.0 - (sf1 + rail2)
    x_v4 = x_v3 - half
    x_v5 = dbp + (sf2 + rail2)
    x_v6 = x_v5 + half

    x_v4_final = x_v4
    x_v6_final = x_v6

    displacement = None

    # ── Desplazamiento si BSR < BS ──────────────────────────
    if bsr < bs:
        sg    = float(inp.get("SG", 0));  tg = float(inp.get("TG", 0))
        omega = str(inp.get("OMEGA_SIDE", "R")).upper()
        omega = omega if omega in ("R", "L") else "R"

        z_side      = "L" if omega == "R" else "R"
        linea_z     = "V4" if z_side == "L" else "V6"   # V3/V4 = izquierda
        linea_omega = "V6" if z_side == "L" else "V4"

        limit_zb = (sf1 if z_side == "L" else sf2) * 0.3
        limit_ob = (sg - tg / 2.0) * 0.3
        dif      = bs - bsr

        paso, rango, fuera = _search_paso(dif, limit_zb, limit_ob)

        # Se sacrifica primero Z, luego Omega
        desp_z     = -min(paso, limit_zb)
        desp_omega = +max(0.0, paso - limit_zb)

        if linea_z == "V4":
            x_v4_final = x_v4 + desp_z
            x_v6_final = x_v6 + desp_omega
        else:  # linea_z == V6
            x_v6_final = x_v6 + desp_z
            x_v4_final = x_v4 + desp_omega

        displacement = {
            "omega_side":  omega,
            "z_side":      z_side,
            "linea_z":     linea_z,
            "linea_omega": linea_omega,
            "limit_zb":    limit_zb,
            "limit_ob":    limit_ob,
            "dif_bs":      dif,
            "paso":        paso,
            "rango":       rango,
            "fuera_rango": fuera,
            "desp_z":      desp_z,
            "desp_omega":  desp_omega,
        }

    return {
        "dbp": dbp, "dbpw": dbpw, "rw": rw,
        "P": P, "C1": C1, "C2": C2, "d1": d1, "d2": d2,
        "lines": {
            "V1": {"x0": x_v1, "x": x_v1},
            "V2": {"x0": x_v2, "x": x_v2},
            "V3": {"x0": x_v3, "x": x_v3},
            "V4": {"x0": x_v4, "x": x_v4_final},
            "V5": {"x0": x_v5, "x": x_v5},
            "V6": {"x0": x_v6, "x": x_v6_final},
        },
        "displacement": displacement,
    }


def _n(v) -> str:
    try:    return f"{float(v):.0f}"
    except Exception: return str(v)


def plumb_svg(res: dict) -> str:
    """Diagrama SVG (planta de plantilla) — compatible con Streamlit y svglib."""
    lines = res["lines"]
    dbp, dbpw, rw = res["dbp"], res["dbpw"], res["rw"]
    P, C1, C2 = res["P"], res["C1"], res["C2"]

    xs = [d["x"] for d in lines.values()] + [d["x0"] for d in lines.values()] + [0.0, dbp]
    xmin, xmax = min(xs), max(xs)
    if xmax - xmin < 1: xmax = xmin + 1
    ys = [dbpw, rw]
    ymin, ymax = min(ys), max(ys)
    if ymax - ymin < 1: ymin -= 5; ymax += 5

    VW, VH = 660, 420
    ML, MR, MT, MB = 48, 48, 46, 72
    pw, ph = VW - ML - MR, VH - MT - MB
    padx = (xmax - xmin) * 0.10 + 8
    pady = (ymax - ymin) * 0.35 + 12
    x0, x1 = xmin - padx, xmax + padx
    y0, y1 = ymin - pady, ymax + pady

    def sx(x): return ML + (x - x0) / (x1 - x0) * pw
    def sy(y): return MT + (y1 - y) / (y1 - y0) * ph   # eje Y hacia arriba

    COL = {
        "V1": "#185FA5", "V2": "#185FA5",
        "V3": "#888888", "V5": "#888888",
        "V4": "#3B6D11", "V6": "#3B6D11",
    }
    p = [f'<svg viewBox="0 0 {VW} {VH}" xmlns="http://www.w3.org/2000/svg" '
         f'style="width:100%;max-width:{VW}px;font-family:system-ui,sans-serif;display:block;margin:0 auto">']

    p.append(f'<text x="{VW/2:.1f}" y="20" text-anchor="middle" font-size="13" fill="#185FA5" '
             f'font-weight="bold">Ubicación de líneas de plomada</text>')

    # Marco del área de plot
    p.append(f'<rect x="{ML:.1f}" y="{MT:.1f}" width="{pw:.1f}" height="{ph:.1f}" '
             f'fill="none" stroke="#ddd" stroke-width="1"/>')

    # Líneas horizontales DBPW y RW
    p.append(f'<line x1="{ML:.1f}" y1="{sy(dbpw):.1f}" x2="{ML+pw:.1f}" y2="{sy(dbpw):.1f}" '
             f'stroke="#6b3fa0" stroke-width="1.8"/>')
    p.append(f'<text x="{ML+pw+3:.1f}" y="{sy(dbpw)+3:.1f}" font-size="9" fill="#6b3fa0">DBPW {_n(dbpw)}</text>')
    p.append(f'<line x1="{ML:.1f}" y1="{sy(rw):.1f}" x2="{ML+pw:.1f}" y2="{sy(rw):.1f}" '
             f'stroke="#BA7517" stroke-width="1.8"/>')
    p.append(f'<text x="{ML+pw+3:.1f}" y="{sy(rw)+3:.1f}" font-size="9" fill="#BA7517">RW {_n(rw)}</text>')

    # Líneas de distancia P-C1 y P-C2 (punteadas)
    for C, dist in [(C1, res["d1"]), (C2, res["d2"])]:
        p.append(f'<line x1="{sx(P[0]):.1f}" y1="{sy(P[1]):.1f}" x2="{sx(C[0]):.1f}" y2="{sy(C[1]):.1f}" '
                 f'stroke="#1D9E75" stroke-width="1.3" stroke-dasharray="4,3"/>')
    p.append(f'<text x="{(sx(P[0])+sx(C1[0]))/2-6:.1f}" y="{(sy(P[1])+sy(C1[1]))/2:.1f}" '
             f'font-size="8" fill="#1D9E75" text-anchor="end">{_n(res["d1"])}</text>')
    p.append(f'<text x="{(sx(P[0])+sx(C2[0]))/2+6:.1f}" y="{(sy(P[1])+sy(C2[1]))/2:.1f}" '
             f'font-size="8" fill="#1D9E75">{_n(res["d2"])}</text>')

    # Líneas verticales V1..V6
    for i, (name, d) in enumerate(lines.items()):
        col   = COL[name]
        xf    = sx(d["x"])
        moved = abs(d["x"] - d["x0"]) > 1e-6
        dash  = "" if name in ("V1", "V2") else ' stroke-dasharray="5,3"'
        # posición inicial tenue si se desplazó
        if moved:
            xi = sx(d["x0"])
            p.append(f'<line x1="{xi:.1f}" y1="{MT:.1f}" x2="{xi:.1f}" y2="{MT+ph:.1f}" '
                     f'stroke="{col}" stroke-width="1" stroke-dasharray="2,4" opacity="0.35"/>')
        p.append(f'<line x1="{xf:.1f}" y1="{MT:.1f}" x2="{xf:.1f}" y2="{MT+ph:.1f}" '
                 f'stroke="{col}" stroke-width="2"{dash}/>')
        # etiqueta arriba (altura alterna para no chocar)
        ly = MT - 6 if i % 2 == 0 else MT - 18
        p.append(f'<text x="{xf:.1f}" y="{ly:.1f}" text-anchor="middle" font-size="8.5" '
                 f'fill="{col}" font-weight="bold">{LINE_SHORT.get(name, name)}</text>')
        p.append(f'<text x="{xf:.1f}" y="{MT+ph+12:.1f}" text-anchor="middle" font-size="8" '
                 f'fill="{col}">{_n(d["x"])}</text>')

    # Punto P y cortes C1/C2
    p.append(f'<circle cx="{sx(P[0]):.1f}" cy="{sy(P[1]):.1f}" r="4.5" fill="#111" stroke="#fff" stroke-width="1"/>')
    p.append(f'<text x="{sx(P[0]):.1f}" y="{sy(P[1])-8:.1f}" text-anchor="middle" font-size="8" fill="#111">P</text>')
    for C, lbl in [(C1, "C1"), (C2, "C2")]:
        cx, cy = sx(C[0]), sy(C[1])
        p.append(f'<line x1="{cx-4:.1f}" y1="{cy-4:.1f}" x2="{cx+4:.1f}" y2="{cy+4:.1f}" stroke="#6b3fa0" stroke-width="2"/>')
        p.append(f'<line x1="{cx-4:.1f}" y1="{cy+4:.1f}" x2="{cx+4:.1f}" y2="{cy-4:.1f}" stroke="#6b3fa0" stroke-width="2"/>')
        p.append(f'<text x="{cx:.1f}" y="{cy+16:.1f}" text-anchor="middle" font-size="8" fill="#6b3fa0">{lbl}</text>')

    # Leyenda
    ly = VH - 34
    leg = [("Plomos de riel", "#185FA5"), ("Paredes teóricas", "#888888"),
           ("Paredes reales", "#3B6D11"), ("DBPW", "#6b3fa0"), ("RW", "#BA7517")]
    lx = ML
    for txt, c in leg:
        p.append(f'<rect x="{lx:.1f}" y="{ly:.1f}" width="12" height="8" fill="{c}"/>')
        p.append(f'<text x="{lx+16:.1f}" y="{ly+8:.1f}" font-size="8" fill="#555">{txt}</text>')
        lx += 28 + len(txt) * 4.6
    p.append("</svg>")
    return "".join(p)


def plumb_table(res: dict) -> list:
    """Devuelve filas para una tabla (lista de dicts)."""
    rows = []
    for name, d in res["lines"].items():
        moved = abs(d["x"] - d["x0"]) > 1e-6
        rows.append({
            "Línea":          LINE_NAMES.get(name, name),
            "X inicial (mm)": round(d["x0"], 2),
            "X final (mm)":   round(d["x"], 2),
            "Desplazada":     "Sí" if moved else "—",
        })
    return rows
