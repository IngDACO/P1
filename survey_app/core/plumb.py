"""
Cálculo de ubicación de líneas de plomada (plumb lines).

Entrada (independiente del survey):
  BKS, RAIL, TKSW, LengthTemplate, SF1, SF2, BSR, BS
  Si BSR < BS: SG, TG, OMEGA_SIDE (R/L)

Salida:
  - DBP, DBPW, RW
  - Punto P, cortes C1/C2, distancias diagonales
  - 6 líneas verticales V1..V6 (posición X)

Modelo de encaje:
  El CONJUNTO rígido (plomos V1/V2 + paredes teóricas V3/V5 + template P/C1/C2)
  conserva sus distancias internas y se mueve como un bloque para encajar dentro
  del shaft real. Las paredes REALES V4/V6 son FIJAS (definen el shaft real).
  - BSR > BS → el conjunto se centra (holgura (BSR−BS)/2 a cada lado).
  - BSR < BS → el conjunto se acerca al lado Z (Z opuesto al Omega):
        Z está del lado opuesto al Omega:  Omega R → Z L,  Omega L → Z R
        LIMIT_ZB = SF1×0.3 (si Z izq) | SF2×0.3 (si Z der);  LIMIT_OB = (SG − TG/2)×0.3
        dif = BS − BSR
        sacrificio Z     = min(dif, LIMIT_ZB)         (se sacrifica Z primero)
        sacrificio Omega = max(0, dif − LIMIT_ZB)     (el resto lo absorbe Omega)
        Si sacrificio Omega > LIMIT_OB → no cabe (fuera de rango).
"""
import math

from core.diagrams import _hatch, _dim_h, _dim_v

EPS = 1e-9

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


def compute_plumb(inp: dict, survey_disp: dict = None) -> dict:
    """Calcula todas las magnitudes de plomada. `inp` es un dict con las entradas.

    Modo independiente (survey_disp=None): el encaje lo resuelve el propio plomado
    (centrado si BSR>BS, sacrificio Z→Omega si BSR<BS).

    Modo integrado al survey (survey_disp={"rl":.., "fb":..}): el desplazamiento del
    conjunto lo determina el SURVEY (NO se usa la lógica Z/Omega):
      - lateral: el conjunto se desplaza −rl  (rl<0 = derecha → X+)
      - profundidad: DBPW = TKSW − 150 + fb   (fb>0 aleja los plomos de la pared frontal)
    """
    bks  = float(inp["BKS"]);  rail = float(inp["RAIL"])
    tksw = float(inp["TKSW"]); lt   = float(inp["LengthTemplate"])
    sf1  = float(inp["SF1"]);  sf2  = float(inp["SF2"])
    bsr  = float(inp["BSR"]);  bs   = float(inp["BS"])

    fb = float(survey_disp.get("fb", 0.0)) if survey_disp else 0.0

    # ── Base ────────────────────────────────────────────────
    dbp  = bks + rail
    dbpw = tksw - 150.0 + fb        # +fb (survey): plomos se alejan de la pared frontal
    rw   = dbpw - lt

    P  = (dbp / 2.0, rw)
    C1 = (0.0, dbpw)
    C2 = (dbp, dbpw)
    d1 = math.hypot(P[0] - C1[0], P[1] - C1[1])
    d2 = math.hypot(P[0] - C2[0], P[1] - C2[1])

    # ── Líneas (posición inicial del conjunto) ──────────────
    # Conjunto RÍGIDO (se mueve junto): plomos V1/V2, paredes teóricas V3/V5, template P/C1/C2.
    # Paredes REALES V4/V6 = el shaft real → FIJAS (nunca se mueven).
    rail2 = rail / 2.0
    half  = (bsr - bs) / 2.0        # (BSR−BS)/2 : >0 si shaft real más grande

    x_v1 = 0.0
    x_v2 = dbp
    x_v3 = 0.0 - (sf1 + rail2)      # pared teórica izq  (conjunto)
    x_v5 = dbp + (sf2 + rail2)      # pared teórica der  (conjunto)
    x_v4 = x_v3 - half              # pared REAL izq  (fija)
    x_v6 = x_v5 + half              # pared REAL der  (fija)

    desp = 0.0                      # desplazamiento único del conjunto
    displacement = None

    if survey_disp is not None:
        # ── Desplazamiento determinado por el SURVEY (no Z/Omega) ──
        rl   = float(survey_disp.get("rl", 0.0))
        desp = -rl                  # rl<0 (derecha) → conjunto a la derecha (X+)
        displacement = {
            "origen": "survey", "rl": rl, "fb": fb, "desp_conjunto": desp,
        }
    # ── Encaje del conjunto dentro del shaft real (modo independiente) ──
    elif bsr < bs:
        # Shaft real más pequeño → el conjunto no cabe: se acerca al lado Z
        # (sacrifica hasta LIMIT_ZB) y el resto lo absorbe Omega.
        sg    = float(inp.get("SG", 0));  tg = float(inp.get("TG", 0))
        omega = str(inp.get("OMEGA_SIDE", "R")).upper()
        omega = omega if omega in ("R", "L") else "R"

        z_side   = "L" if omega == "R" else "R"     # Z opuesto al Omega
        limit_zb = (sf1 if z_side == "L" else sf2) * 0.3
        limit_ob = (sg - tg / 2.0) * 0.3
        dif      = bs - bsr                          # cuánto sobra el conjunto

        z_sac     = min(dif, limit_zb)               # sacrificio lado Z (≤ LIMIT_ZB)
        omega_sac = max(0.0, dif - limit_zb)         # resto → lado Omega
        fuera     = omega_sac > limit_ob + EPS       # no cabe ni sacrificando ambos

        # Desplazar el CONJUNTO hacia el lado Z (paredes reales fijas):
        # la pared teórica del lado Z queda z_sac por fuera de su pared real.
        if z_side == "L":
            desp = (x_v4 - z_sac) - x_v3
        else:
            desp = (x_v6 + z_sac) - x_v5

        displacement = {
            "omega_side": omega, "z_side": z_side,
            "limit_zb": limit_zb, "limit_ob": limit_ob, "dif_bs": dif,
            "z_sacrificio": z_sac, "omega_sacrificio": omega_sac,
            "desp_conjunto": desp, "fuera_rango": fuera,
        }
    elif bsr > bs:
        # Shaft real más grande → el conjunto ya queda centrado en su posición
        # inicial (holgura half a cada lado). desp = 0.
        displacement = {"centrado": True, "holgura_lado": half}

    # ── Aplicar el desplazamiento SOLO al conjunto (V4/V6 fijas) ──
    x_v1f = x_v1 + desp;  x_v2f = x_v2 + desp
    x_v3f = x_v3 + desp;  x_v5f = x_v5 + desp

    # ── Eje CERO = pared REAL izquierda (V4) ────────────────
    # Todo el sistema se mide desde V4 (referencia física fija en obra).
    off = x_v4
    def _o(x):
        return x - off

    # Posiciones finales (medidas desde la pared real izquierda = eje cero)
    v1f = _o(x_v1f); v2f = _o(x_v2f); v6f = _o(x_v6)

    # ── Distancias de verificación en campo: plomo ↔ pared real ──
    verif = {
        "plomo_izq_pared_izq": v1f,          # pared real izq → plomo izq
        "plomo_der_pared_der": v6f - v2f,    # plomo der → pared real der
    }

    # ── Autochequeos ────────────────────────────────────────
    # BS del plano vs sus componentes. Si no cuadran, TODO el encaje diverge en
    # silencio (las paredes reales se calculan con (BSR−BS)/2), asi que un BS mal
    # leido del plano situaria los plomos donde no van sin ninguna senal.
    bs_comp = sf1 + bks + 2 * rail + sf2
    bs_check = {"bs_plano": bs, "bs_componentes": bs_comp,
                "dif": bs - bs_comp, "ok": abs(bs - bs_comp) < 0.5}

    # Cierre de obra: di + DBP + dd debe dar BSR. Es una IDENTIDAD del modelo
    # (se cumple siempre que BS sea coherente), asi que su valor esta en obra:
    # el instalador mide di y dd con cinta y comprueba que cierran contra BSR.
    cierre_suma = verif["plomo_izq_pared_izq"] + dbp + verif["plomo_der_pared_der"]
    cierre = {"suma": cierre_suma, "bsr": bsr, "dif": cierre_suma - bsr,
              "ok": abs(cierre_suma - bsr) < 0.5}

    return {
        "dbp": dbp, "dbpw": dbpw, "rw": rw,
        "bsr": bsr, "bs": bs,
        "bs_check": bs_check, "cierre": cierre,
        "P":  (_o(P[0]  + desp), P[1]),
        "C1": (_o(C1[0] + desp), C1[1]),
        "C2": (_o(C2[0] + desp), C2[1]),
        "d1": d1, "d2": d2,
        "lines": {
            "V1": {"x0": _o(x_v1), "x": v1f},
            "V2": {"x0": _o(x_v2), "x": v2f},
            "V3": {"x0": _o(x_v3), "x": _o(x_v3f)},
            "V4": {"x0": _o(x_v4), "x": _o(x_v4)},   # = 0  (pared real izq = eje cero)
            "V5": {"x0": _o(x_v5), "x": _o(x_v5f)},
            "V6": {"x0": _o(x_v6), "x": v6f},        # pared real der — FIJA
        },
        "verif": verif,
        "displacement": displacement,
    }


def _n(v) -> str:
    """mm: entero si lo es, 1 decimal si no.

    DBPW = TKSW − 150 + fb arrastra el fb del survey, que va en pasos de 0.5 mm
    (ver v122): con .0f un 886.5 se rotulaba "886".
    """
    try:
        v = float(v)
    except Exception:
        return str(v)
    return f"{v:.0f}" if abs(v - round(v)) < 0.05 else f"{v:.1f}"


def plumb_svg(res: dict, proyecto: str = "") -> str:
    """Planta de replanteo de plomadas — PLANO TÉCNICO a escala real.

    ⚠️ La versión anterior escalaba X e Y por separado (vertical 1.7× la
    horizontal): el triángulo plantilla→plomos, que es justo lo que se mide con
    cinta en obra, salía deformado. Aquí va UNA sola escala mm→px.

    Referencias: eje X desde la pared REAL izquierda (V4 = 0); eje Y = profundidad
    desde la pared frontal (0 = frontal, crece hacia el fondo).
    """
    lines = res["lines"]
    dbp, dbpw, rw = res["dbp"], res["dbpw"], res["rw"]
    P, C1, C2 = res["P"], res["C1"], res["C2"]
    bsr = float(res.get("bsr") or lines["V6"]["x"] or 1.0)

    if bsr <= 0 or dbpw <= 0:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>'

    VW, VH = 660, 470
    AX, AY, AW, AH = 92, 62, 366, 252
    esc = min(AW / bsr, AH / dbpw)
    w_px, h_px = bsr * esc, dbpw * esc
    px0 = AX + (AW - w_px) / 2                      # pared real izquierda
    py1 = AY + AH                                   # pared frontal (abajo)
    px1 = px0 + w_px

    def SX(x):  return px0 + x * esc                # mm desde pared real izq
    def SY(d):  return py1 - d * esc                # mm de profundidad

    mur = 9.0
    p = [f'<svg viewBox="0 0 {VW} {VH}" xmlns="http://www.w3.org/2000/svg" '
         f'style="width:100%;max-width:{VW}px;font-family:Arial,Helvetica,sans-serif;'
         f'display:block;margin:0 auto">',
         f'<rect x="0" y="0" width="{VW}" height="{VH}" fill="#ffffff"/>']

    # ── Muros reales (el shaft medido en obra) ─────────────
    p.append(_hatch(px0 - mur, SY(dbpw) - 14, mur, h_px + 14, "left"))
    p.append(_hatch(px1, SY(dbpw) - 14, mur, h_px + 14, "right"))
    p.append(_hatch(px0 - mur, py1, w_px + 2 * mur, mur, "bottom"))
    for xx in (px0, px1):
        p.append(f'<line x1="{xx:.1f}" y1="{SY(dbpw)-14:.1f}" x2="{xx:.1f}" y2="{py1:.1f}" '
                 f'stroke="#1f2937" stroke-width="2.2"/>')
    p.append(f'<line x1="{px0:.1f}" y1="{py1:.1f}" x2="{px1:.1f}" y2="{py1:.1f}" '
             f'stroke="#1f2937" stroke-width="2.2"/>')
    p.append(f'<text x="{px0:.1f}" y="{py1+mur+30:.1f}" font-size="8" fill="#7a8699" '
             f'letter-spacing="0.1em">PARED FRONTAL</text>')

    # ── Paredes teóricas (del plano) ───────────────────────
    for nm in ("V3", "V5"):
        xt = SX(lines[nm]["x"])
        p.append(f'<line x1="{xt:.1f}" y1="{SY(dbpw)-14:.1f}" x2="{xt:.1f}" y2="{py1:.1f}" '
                 f'stroke="#9aa7b8" stroke-width="0.9" stroke-dasharray="9,3,2,3"/>')
        p.append(f'<text x="{xt:.1f}" y="{SY(dbpw)-19:.1f}" text-anchor="middle" font-size="7" '
                 f'fill="#9aa7b8">pared teórica</text>')

    # ── Plomos (V1/V2) — en planta son puntos; el hilo cae en vertical ──
    yC = SY(dbpw)
    for nm in ("V1", "V2"):
        xp = SX(lines[nm]["x"])
        p.append(f'<line x1="{xp:.1f}" y1="{yC-14:.1f}" x2="{xp:.1f}" y2="{py1:.1f}" '
                 f'stroke="#1a3a5c" stroke-width="0.7" stroke-dasharray="9,3,2,3"/>')
        p.append(f'<circle cx="{xp:.1f}" cy="{yC:.1f}" r="4.6" fill="#ffffff" '
                 f'stroke="#1a3a5c" stroke-width="1.8"/>')
        p.append(f'<circle cx="{xp:.1f}" cy="{yC:.1f}" r="1.5" fill="#1a3a5c"/>')
    p.append(f'<text x="{SX(lines["V1"]["x"]):.1f}" y="{yC-11:.1f}" text-anchor="middle" '
             f'font-size="8" fill="#1a3a5c" font-weight="bold">C1</text>')
    p.append(f'<text x="{SX(lines["V2"]["x"]):.1f}" y="{yC-11:.1f}" text-anchor="middle" '
             f'font-size="8" fill="#1a3a5c" font-weight="bold">C2</text>')

    # ── Plantilla: punto P y las dos cuerdas que se miden con cinta ──
    xP, yP = SX(P[0]), SY(P[1])
    for C, dist, lado in ((C1, res["d1"], -1), (C2, res["d2"], 1)):
        xc, yc = SX(C[0]), SY(C[1])
        p.append(f'<line x1="{xP:.1f}" y1="{yP:.1f}" x2="{xc:.1f}" y2="{yc:.1f}" '
                 f'stroke="#1a7f5a" stroke-width="1.4"/>')
        p.append(f'<text x="{(xP+xc)/2 + lado*10:.1f}" y="{(yP+yc)/2:.1f}" '
                 f'text-anchor="{"end" if lado < 0 else "start"}" font-size="9" '
                 f'fill="#1a7f5a" font-weight="bold">{_n(dist)}</text>')
    p.append(f'<line x1="{xP-9:.1f}" y1="{yP:.1f}" x2="{xP+9:.1f}" y2="{yP:.1f}" '
             f'stroke="#1f2937" stroke-width="1.6"/>')
    p.append(f'<line x1="{xP:.1f}" y1="{yP-9:.1f}" x2="{xP:.1f}" y2="{yP+9:.1f}" '
             f'stroke="#1f2937" stroke-width="1.6"/>')
    p.append(f'<text x="{xP+11:.1f}" y="{yP+11:.1f}" font-size="9" fill="#1f2937" '
             f'font-weight="bold">P</text>')
    p.append(f'<text x="{xP+11:.1f}" y="{yP+21:.1f}" font-size="7" fill="#7a8699">plantilla</text>')

    # ── Cotas ──────────────────────────────────────────────
    p.append(_dim_h(SX(lines["V1"]["x"]), SX(lines["V2"]["x"]), yC - 30,
                    f"DBP {_n(dbp)}", color="#1a3a5c", tcolor="#1a3a5c"))
    vf = res.get("verif") or {}
    di = vf.get("plomo_izq_pared_izq", 0.0)
    dd = vf.get("plomo_der_pared_der", 0.0)
    yv = py1 + mur + 16
    p.append(_dim_h(px0, SX(lines["V1"]["x"]), yv, f"di {_n(di)}",
                    color="#b5651d", tcolor="#b5651d", ext_desde=py1, hacia="izq"))
    p.append(_dim_h(SX(lines["V2"]["x"]), px1, yv, f"dd {_n(dd)}",
                    color="#b5651d", tcolor="#b5651d", ext_desde=py1, hacia="der"))

    xd = px0 - mur - 22
    p.append(_dim_v(SY(dbpw), py1, xd, f"DBPW {_n(dbpw)}", ext_desde=px0 - mur))
    p.append(_dim_v(SY(rw), py1, xd - 22, f"RW {_n(rw)}", ext_desde=px0 - mur))
    if abs(dbpw - rw) * esc > 6:
        p.append(_dim_v(SY(dbpw), SY(rw), px1 + mur + 18,
                        f"LT {_n(dbpw - rw)}", ext_desde=px1 + mur))

    # ── Columna derecha: cierre, aviso de BS y cajetín ─────
    cx, cy = 492, 62
    cierre = res.get("cierre") or {}
    p.append(f'<rect x="{cx}" y="{cy}" width="152" height="66" fill="#f7fafd" '
             f'stroke="#1a3a5c" stroke-width="0.8"/>')
    p.append(f'<text x="{cx+6}" y="{cy+15}" font-size="8" fill="#1a3a5c" '
             f'font-weight="bold">COMPROBAR EN OBRA</text>')
    p.append(f'<text x="{cx+6}" y="{cy+31}" font-size="8.5" fill="#1f2937">'
             f'di + DBP + dd</text>')
    p.append(f'<text x="{cx+6}" y="{cy+45}" font-size="8.5" fill="#1f2937">'
             f'{_n(di)} + {_n(dbp)} + {_n(dd)}</text>')
    p.append(f'<text x="{cx+6}" y="{cy+59}" font-size="9" fill="#1a7f5a" '
             f'font-weight="bold">= {_n(cierre.get("suma", 0))} = BSR</text>')

    yb = cy + 78
    bsc = res.get("bs_check") or {}
    if bsc and not bsc.get("ok", True):
        p.append(f'<rect x="{cx}" y="{yb}" width="152" height="60" fill="#fcebeb" '
                 f'stroke="#c0392b" stroke-width="0.9"/>')
        p.append(f'<text x="{cx+6}" y="{yb+15}" font-size="8" fill="#c0392b" '
                 f'font-weight="bold">⚠ BS INCOHERENTE</text>')
        p.append(f'<text x="{cx+6}" y="{yb+30}" font-size="7.5" fill="#1f2937">'
                 f'plano {_n(bsc.get("bs_plano"))} vs</text>')
        p.append(f'<text x="{cx+6}" y="{yb+42}" font-size="7.5" fill="#1f2937">'
                 f'componentes {_n(bsc.get("bs_componentes"))}</text>')
        p.append(f'<text x="{cx+6}" y="{yb+54}" font-size="7.5" fill="#c0392b">'
                 f'dif {_n(bsc.get("dif"))} mm — revisar</text>')
        yb += 70

    # Sacrificio Z/Omega (solo modo independiente con BSR &lt; BS)
    disp = res.get("displacement") or {}
    if disp.get("z_sacrificio") is not None:
        alto = 76
        fuera = disp.get("fuera_rango")
        p.append(f'<rect x="{cx}" y="{yb}" width="152" height="{alto}" '
                 f'fill="{"#fcebeb" if fuera else "#f7fafd"}" '
                 f'stroke="{"#c0392b" if fuera else "#9aa7b8"}" stroke-width="0.8"/>')
        p.append(f'<text x="{cx+6}" y="{yb+15}" font-size="8" fill="#1a3a5c" '
                 f'font-weight="bold">AJUSTE BSR &lt; BS</text>')
        p.append(f'<text x="{cx+6}" y="{yb+30}" font-size="7.5" fill="#1f2937">'
                 f'sobra {_n(disp.get("dif_bs"))} mm</text>')
        p.append(f'<text x="{cx+6}" y="{yb+44}" font-size="7.5" fill="#1f2937">'
                 f'lado Z ({disp.get("z_side","")}): {_n(disp.get("z_sacrificio"))}</text>')
        p.append(f'<text x="{cx+6}" y="{yb+58}" font-size="7.5" fill="#1f2937">'
                 f'lado Omega: {_n(disp.get("omega_sacrificio"))}</text>')
        if fuera:
            p.append(f'<text x="{cx+6}" y="{yb+71}" font-size="7.5" fill="#c0392b" '
                     f'font-weight="bold">NO CABE — revisar</text>')
        yb += alto + 10

    tx, ty = 492, 348
    p.append(f'<rect x="{tx}" y="{ty}" width="152" height="76" fill="none" '
             f'stroke="#1f2937" stroke-width="0.9"/>')
    for dy in (24, 46):
        p.append(f'<line x1="{tx}" y1="{ty+dy}" x2="{tx+152}" y2="{ty+dy}" '
                 f'stroke="#1f2937" stroke-width="0.5"/>')
    p.append(f'<text x="{tx+6}" y="{ty+16}" font-size="9.5" fill="#1f2937" '
             f'font-weight="bold">REPLANTEO DE PLOMADAS</text>')
    p.append(f'<text x="{tx+6}" y="{ty+38}" font-size="7.5" fill="#5f6b7a">'
             f'Proporción real · cotas en mm</text>')
    p.append(f'<text x="{tx+6}" y="{ty+60}" font-size="7.5" fill="#5f6b7a">'
             f'{(proyecto or "COPEX")[:24]}</text>')
    p.append(f'<text x="{tx+6}" y="{ty+71}" font-size="7" fill="#7a8699">'
             f'Origen X: pared real izquierda</text>')

    p.append("</svg>")
    return "".join(p)


# ══════════════════════════════════════════════════════════
#  Vistas 3D del replanteo de plomadas
# ══════════════════════════════════════════════════════════
_PCX, _PCY = 0.866, 0.5          # isométrica 30°


def _p3(x, y, z, ox, oy, k, kz):
    """(ancho, profundidad, altura) en mm → px. Z hacia arriba."""
    return (ox + (x - y) * _PCX * k, oy + (x + y) * _PCY * k - z * kz)


def _pol(pts, fill, stroke, sw=1.0, op=1.0, dash=""):
    d = " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<polygon points="{d}" fill="{fill}" fill-opacity="{op}" '
            f'stroke="{stroke}" stroke-width="{sw}"{da} stroke-linejoin="round"/>')


def plumb_iso_svg(res: dict, altura: float = 0.0, proyecto: str = "") -> str:
    """Isométrica del hueco con los DOS HILOS DE PLOMADA cayendo desde arriba.

    Es la vista que la planta no puede dar: el replanteo es una operación
    VERTICAL. Ancho y profundidad van a escala real; la ALTURA es esquemática
    (el plomado no aporta la altura del hueco) y así se declara en el pie.
    Solo se dibujan los planos que el plomado conoce de verdad —paredes reales
    izquierda/derecha y pared frontal—; el fondo se deja abierto.
    """
    lines = res["lines"]
    dbp, dbpw, rw = res["dbp"], res["dbpw"], res["rw"]
    P, C1, C2 = res["P"], res["C1"], res["C2"]
    bsr = float(res.get("bsr") or lines["V6"]["x"] or 0.0)
    if bsr <= 0 or dbpw <= 0:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>'

    D = dbpw * 1.15                       # profundidad dibujada (solo contexto)
    H = float(altura) if altura and altura > 0 else 3000.0

    VW, VH = 470, 620
    k    = (VW - 190) / ((bsr + D) * _PCX)
    diam = (bsr + D) * _PCY * k
    kz   = max(0.0005, (VH - 210 - diam) / H)
    ox   = VW / 2 + (D - bsr) * _PCX * k / 2
    oy   = 104 + H * kz

    A = lambda x, y, z: _p3(x, y, z, ox, oy, k, kz)
    p = [f'<svg viewBox="0 0 {VW} {VH}" xmlns="http://www.w3.org/2000/svg" '
         f'style="width:100%;max-width:{VW}px;font-family:Arial,Helvetica,sans-serif;'
         f'display:block;margin:0 auto">',
         f'<rect x="0" y="0" width="{VW}" height="{VH}" fill="#ffffff"/>']

    # Solera del foso + las tres paredes que el plomado sí conoce
    p.append(_pol([A(0, 0, 0), A(bsr, 0, 0), A(bsr, D, 0), A(0, D, 0)],
                  "#eef2f7", "#c3ccd8", 0.9))
    p.append(_pol([A(0, 0, 0), A(0, D, 0), A(0, D, H), A(0, 0, H)],
                  "#f5f8fb", "#c3ccd8", 0.9))                      # pared real izq
    p.append(_pol([A(bsr, 0, 0), A(bsr, D, 0), A(bsr, D, H), A(bsr, 0, H)],
                  "#f5f8fb", "#c3ccd8", 0.9))                      # pared real der
    p.append(_pol([A(0, 0, 0), A(bsr, 0, 0), A(bsr, 0, H), A(0, 0, H)],
                  "#fafcfe", "#c3ccd8", 0.9))                      # pared frontal

    # Los DOS HILOS: caen desde el techo hasta la solera
    for nm, et in (("V1", "C1"), ("V2", "C2")):
        xw = lines[nm]["x"]
        (ax, ay), (bx, by) = A(xw, dbpw, H), A(xw, dbpw, 0)
        p.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" '
                 f'stroke="#1a3a5c" stroke-width="1.7"/>')
        p.append(f'<circle cx="{ax:.1f}" cy="{ay:.1f}" r="3.2" fill="#1a3a5c"/>')
        # peso del plomo, justo encima de la solera
        (px_, py_) = A(xw, dbpw, H * 0.045)
        p.append(f'<polygon points="{px_-3.4:.1f},{py_-9:.1f} {px_+3.4:.1f},{py_-9:.1f} '
                 f'{px_:.1f},{py_+3:.1f}" fill="#1a3a5c"/>')
        p.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="3.4" fill="#ffffff" '
                 f'stroke="#1a3a5c" stroke-width="1.5"/>')
        p.append(f'<text x="{bx+7:.1f}" y="{by+4:.1f}" font-size="8.5" fill="#1a3a5c" '
                 f'font-weight="bold">{et}</text>')

    # Plantilla en la solera + las dos cuerdas que se miden con cinta
    (tx_, ty_) = A(P[0], P[1], 0)
    for C, dist in ((C1, res["d1"]), (C2, res["d2"])):
        (cx_, cy_) = A(C[0], C[1], 0)
        p.append(f'<line x1="{tx_:.1f}" y1="{ty_:.1f}" x2="{cx_:.1f}" y2="{cy_:.1f}" '
                 f'stroke="#1a7f5a" stroke-width="1.4"/>')
        p.append(f'<text x="{(tx_+cx_)/2:.1f}" y="{(ty_+cy_)/2-4:.1f}" text-anchor="middle" '
                 f'font-size="8" fill="#1a7f5a" font-weight="bold">{_n(dist)}</text>')
    p.append(f'<circle cx="{tx_:.1f}" cy="{ty_:.1f}" r="3.6" fill="#1f2937"/>')
    p.append(f'<text x="{tx_:.1f}" y="{ty_+15:.1f}" text-anchor="middle" font-size="8.5" '
             f'fill="#1f2937" font-weight="bold">P</text>')

    # Aristas vivas
    for a, b in (((0, 0, 0), (0, 0, H)), ((bsr, 0, 0), (bsr, 0, H))):
        (ax, ay), (bx, by) = A(*a), A(*b)
        p.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" '
                 f'stroke="#8a94a6" stroke-width="0.9"/>')

    p.append(f'<text x="18" y="26" font-size="11" fill="#1f2937" font-weight="bold">'
             f'PLOMADAS — VISTA ISOMÉTRICA</text>')
    p.append(f'<text x="18" y="40" font-size="8" fill="#7a8699">'
             f'{(proyecto or "COPEX")[:38]} · planta a escala, altura esquemática</text>')

    fy = VH - 62
    p.append(f'<rect x="18" y="{fy}" width="{VW-36}" height="42" fill="#f7fafd" '
             f'stroke="#c3ccd8" stroke-width="0.8"/>')
    for j, (et, va) in enumerate((("DBP", f"{_n(dbp)} mm"),
                                  ("DBPW", f"{_n(dbpw)} mm"),
                                  ("RW", f"{_n(rw)} mm"))):
        cx_ = 18 + (VW - 36) * (j + 0.5) / 3
        p.append(f'<text x="{cx_:.0f}" y="{fy+17}" text-anchor="middle" font-size="7.5" '
                 f'fill="#7a8699">{et}</text>')
        p.append(f'<text x="{cx_:.0f}" y="{fy+32}" text-anchor="middle" font-size="10" '
                 f'fill="#1f2937">{va}</text>')
    p.append("</svg>")
    return "".join(p)


def plumb_detail_svg(res: dict, proyecto: str = "") -> str:
    """Detalle 3D del replanteo: plantilla, plomos y las dos cuerdas, ampliado.

    Es la vista de ejecución: qué se apoya, dónde y qué se mide.
    """
    lines = res["lines"]
    dbp = res["dbp"]
    P, C1, C2 = res["P"], res["C1"], res["C2"]
    lt = res["dbpw"] - res["rw"]
    if dbp <= 0:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>'

    x1, x2 = lines["V1"]["x"], lines["V2"]["x"]
    xmin = min(x1, P[0]) - dbp * 0.16
    xmax = max(x2, P[0]) + dbp * 0.16
    W = xmax - xmin
    # El detalle solo aporta si ensena lo que la planta NO puede: la CAIDA del
    # hilo. Con una altura corta quedaba un plano inclinado con el mismo
    # triangulo que la planta, pero deformado por la proyeccion -> ruido.
    Dp = max(lt * 1.35, dbp * 0.22)
    Hh = dbp * 0.72                          # altura de hilo mostrada

    # Presupuesto de lienzo: el alto debe cubrir la altura de hilo MAS el rombo
    # del plano; si no, el plomo C2 (la esquina mas baja) se sale por abajo.
    VW, VH = 560, 470
    k    = (VW - 90) / ((W + Dp) * _PCX)
    diam = (W + Dp) * _PCY * k
    kz   = k
    if 74 + Hh * kz + diam > VH - 26:            # no cabe -> reescalar
        k    = (VH - 100) / ((W + Dp) * _PCY + Hh)
        kz   = k
        diam = (W + Dp) * _PCY * k
    ox = VW / 2 + (Dp - W) * _PCX * k / 2
    oy = 74 + Hh * kz

    A = lambda x, y, z: _p3(x - xmin, y, z, ox, oy, k, kz)
    p = [f'<svg viewBox="0 0 {VW} {VH}" xmlns="http://www.w3.org/2000/svg" '
         f'style="width:100%;max-width:{VW}px;font-family:Arial,Helvetica,sans-serif;'
         f'display:block;margin:0 auto">',
         f'<rect x="0" y="0" width="{VW}" height="{VH}" fill="#ffffff"/>']

    # Plano de referencia
    p.append(_pol([A(xmin, 0, 0), A(xmax, 0, 0), A(xmax, Dp, 0), A(xmin, Dp, 0)],
                  "#f2f5f9", "#c3ccd8", 0.8))

    yC, yP = res["dbpw"], res["rw"]
    yC_r = min(Dp * 0.82, Dp - 1)                 # profundidad relativa dibujada
    yP_r = max(1.0, yC_r - lt * k / k)
    yP_r = max(1.0, yC_r - lt)

    # Regla de la plantilla (de P hacia la línea de plomos)
    (bx0, by0) = A(P[0], yP_r, 0)
    (bx1, by1) = A(P[0], yC_r, 0)
    p.append(f'<line x1="{bx0:.1f}" y1="{by0:.1f}" x2="{bx1:.1f}" y2="{by1:.1f}" '
             f'stroke="#b5651d" stroke-width="3" />')
    p.append(f'<text x="{(bx0+bx1)/2-10:.1f}" y="{(by0+by1)/2+14:.1f}" text-anchor="end" '
             f'font-size="8.5" fill="#b5651d">LT {_n(lt)}</text>')

    # Hilos de plomada bajando hasta el plano
    for xw, et in ((x1, "C1"), (x2, "C2")):
        (ax, ay) = A(xw, yC_r, Hh)
        (bx, by) = A(xw, yC_r, 0)
        p.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" '
                 f'stroke="#1a3a5c" stroke-width="1.8"/>')
        (wx, wy) = A(xw, yC_r, Hh * 0.13)
        p.append(f'<polygon points="{wx-4:.1f},{wy-11:.1f} {wx+4:.1f},{wy-11:.1f} '
                 f'{wx:.1f},{wy+4:.1f}" fill="#1a3a5c"/>')
        p.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="4" fill="#ffffff" '
                 f'stroke="#1a3a5c" stroke-width="1.7"/>')
        p.append(f'<text x="{ax:.1f}" y="{ay-7:.1f}" text-anchor="middle" font-size="9" '
                 f'fill="#1a3a5c" font-weight="bold">{et}</text>')

    # Cuerdas medidas con cinta
    (px_, py_) = A(P[0], yP_r, 0)
    for xw, dist, lado in ((x1, res["d1"], -1), (x2, res["d2"], 1)):
        (cx_, cy_) = A(xw, yC_r, 0)
        p.append(f'<line x1="{px_:.1f}" y1="{py_:.1f}" x2="{cx_:.1f}" y2="{cy_:.1f}" '
                 f'stroke="#1a7f5a" stroke-width="1.7"/>')
        p.append(f'<text x="{(px_+cx_)/2 + lado*6:.1f}" y="{(py_+cy_)/2-5:.1f}" '
                 f'text-anchor="middle" font-size="9.5" fill="#1a7f5a" '
                 f'font-weight="bold">{_n(dist)}</text>')
    p.append(f'<circle cx="{px_:.1f}" cy="{py_:.1f}" r="4.4" fill="#1f2937"/>')
    p.append(f'<text x="{px_:.1f}" y="{py_+16:.1f}" text-anchor="middle" font-size="9" '
             f'fill="#1f2937" font-weight="bold">P</text>')

    # DBP entre plomos
    (dx0, dy0) = A(x1, yC_r, 0)
    (dx1, dy1) = A(x2, yC_r, 0)
    p.append(f'<line x1="{dx0:.1f}" y1="{dy0+22:.1f}" x2="{dx1:.1f}" y2="{dy1+22:.1f}" '
             f'stroke="#1a3a5c" stroke-width="0.8"/>')
    p.append(f'<text x="{(dx0+dx1)/2:.1f}" y="{(dy0+dy1)/2+36:.1f}" text-anchor="middle" '
             f'font-size="9" fill="#1a3a5c">DBP {_n(dbp)}</text>')

    p.append(f'<text x="18" y="26" font-size="11" fill="#1f2937" font-weight="bold">'
             f'DETALLE DE REPLANTEO</text>')
    p.append(f'<text x="18" y="40" font-size="8" fill="#7a8699">'
             f'plantilla, plomos y cuerdas a medir · {(proyecto or "COPEX")[:30]}</text>')
    p.append("</svg>")
    return "".join(p)


def plumb_card_svg(res: dict, proyecto: str = "") -> str:
    """Ficha de replanteo: SOLO los números que se miden en obra, en grande.

    En el andamio no hace falta un plano bonito: hacen falta cinco números
    legibles desde el móvil o impresos en A5.
    """
    vf = res.get("verif") or {}
    cierre = res.get("cierre") or {}
    items = [
        ("DBP", res["dbp"],  "entre los dos plomos"),
        ("d1",  res["d1"],   "plantilla P → plomo C1"),
        ("d2",  res["d2"],   "plantilla P → plomo C2"),
        ("di",  vf.get("plomo_izq_pared_izq", 0.0), "pared real izq → C1"),
        ("dd",  vf.get("plomo_der_pared_der", 0.0), "C2 → pared real der"),
    ]
    VW, fila = 470, 52
    VH = 96 + fila * len(items) + 58
    p = [f'<svg viewBox="0 0 {VW} {VH}" xmlns="http://www.w3.org/2000/svg" '
         f'style="width:100%;max-width:{VW}px;font-family:Arial,Helvetica,sans-serif;'
         f'display:block;margin:0 auto">',
         f'<rect x="0" y="0" width="{VW}" height="{VH}" fill="#ffffff"/>',
         f'<rect x="0" y="0" width="{VW}" height="58" fill="#1a3a5c"/>',
         f'<text x="20" y="26" font-size="15" fill="#ffffff" font-weight="bold">'
         f'FICHA DE REPLANTEO</text>',
         f'<text x="20" y="45" font-size="9.5" fill="#b0c8e8">'
         f'{(proyecto or "COPEX")[:44]} · medidas en mm</text>']

    y = 76
    for i, (cod, val, desc) in enumerate(items):
        if i % 2 == 1:
            p.append(f'<rect x="0" y="{y-16:.0f}" width="{VW}" height="{fila}" fill="#f4f7fb"/>')
        p.append(f'<text x="20" y="{y+8:.0f}" font-size="17" fill="#1a3a5c" '
                 f'font-weight="bold">{cod}</text>')
        p.append(f'<text x="{VW-20}" y="{y+10:.0f}" text-anchor="end" font-size="23" '
                 f'fill="#1f2937" font-weight="bold">{_n(val)}</text>')
        p.append(f'<text x="66" y="{y+8:.0f}" font-size="9" fill="#7a8699">{desc}</text>')
        y += fila

    p.append(f'<rect x="0" y="{y-14:.0f}" width="{VW}" height="46" fill="#eaf3de"/>')
    p.append(f'<text x="20" y="{y+4:.0f}" font-size="9.5" fill="#3b6d11" '
             f'font-weight="bold">COMPROBACIÓN</text>')
    p.append(f'<text x="20" y="{y+20:.0f}" font-size="10" fill="#1f2937">'
             f'di + DBP + dd = {_n(cierre.get("suma", 0))} = BSR</text>')
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


def plumb_checks(res: dict) -> list:
    """Distancias de verificación en campo: de cada plomo a su pared real (mm)."""
    v = res.get("verif") or {}
    return [
        {"Medida": "Pared real izquierda → plomo riel izquierdo",
         "Distancia (mm)": round(v.get("plomo_izq_pared_izq", 0.0), 1)},
        {"Medida": "Plomo riel derecho → pared real derecha",
         "Distancia (mm)": round(v.get("plomo_der_pared_der", 0.0), 1)},
    ]
