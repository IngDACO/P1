"""
Gestión de proyecto: cronograma (Gantt) + curva S de avance planificado.

El cronograma se genera automáticamente a partir de:
  - NS (número de paradas)  → escala las actividades que dependen de pisos
  - banderas del análisis   → cortes (OR/OL > límite), ajuste de shaft (BSR<BS)
Las duraciones y pesos son editables por el usuario; la curva S se recalcula.

Pesos con distribución en "S" (bajo al inicio, alto en el medio, bajo al final)
→ el avance acumulado planificado dibuja la clásica curva S.
"""
from datetime import date, timedelta

# (nombre, dur_base_dias, dias_por_parada, peso, condicion)
PHASES = [
    ("Survey y replanteo",                    1, 0.0,  3, None),
    ("Plomadas y líneas de referencia",       1, 0.2,  5, None),
    ("Brackets / soportes",                   1, 0.4,  8, None),
    ("Montaje de rieles (guías)",             2, 0.6, 18, None),
    ("Ajuste de hueco / cortes",              1, 0.2,  5, "cortes"),
    ("Ajuste de shaft (BSR < BS)",            1, 0.0,  4, "shaft"),
    ("Cabina y contrapeso",                   3, 0.0, 15, None),
    ("Puertas de rellano",                    1, 0.5, 14, None),
    ("Máquina y controlador",                 2, 0.0, 10, None),
    ("Cableado eléctrico",                    1, 0.3,  9, None),
    ("Nivelación y ajustes",                  2, 0.0,  5, None),
    ("Pruebas (carga, velocidad, seguridad)", 2, 0.0,  4, None),
    ("Certificación y entrega",               1, 0.0,  2, None),
]


def detect_flags(calc_results: dict) -> dict:
    """Determina qué actividades condicionales aplican, a partir del cálculo."""
    flags = {"cortes": False, "shaft": False}
    if not calc_results:
        return flags
    opt = calc_results.get("optimizer_result", {}) or {}
    best = opt.get("best")
    lim  = calc_results.get("limits", {}) or {}
    lim_or = float(lim.get("LIMIT_OR", 1e9))
    lim_ol = float(lim.get("LIMIT_OL", 1e9))
    if best and best.get("matrix"):
        for row in best["matrix"]:
            if float(row.get("OR", 0)) > lim_or or float(row.get("OL", 0)) > lim_ol:
                flags["cortes"] = True
                break
    bs = calc_results.get("bs_result", {}) or {}
    if bs.get("needed"):
        flags["shaft"] = True
    return flags


def build_schedule(ns: int, start_date: date, flags: dict,
                   custom_rows: list = None) -> dict:
    """
    Genera el cronograma. Si `custom_rows` viene (edición del usuario),
    usa sus duraciones/pesos en lugar de los automáticos.
    custom_rows: lista de dicts {nombre, duracion, peso}
    """
    ns = max(1, int(ns or 1))

    if custom_rows:
        base = [(r["nombre"], float(r["duracion"]), float(r["peso"])) for r in custom_rows]
    else:
        base = []
        for nombre, db, dpp, peso, cond in PHASES:
            if cond and not flags.get(cond):
                continue
            dur = max(1, round(db + dpp * ns))
            base.append((nombre, float(dur), float(peso)))

    # Normalizar pesos a 100
    total_peso = sum(p for _, _, p in base) or 1.0

    acts = []
    cur = 0.0
    for nombre, dur, peso in base:
        peso_n = round(peso * 100.0 / total_peso, 1)
        acts.append({
            "nombre":       nombre,
            "inicio":       cur,
            "duracion":     dur,
            "peso":         peso_n,
            "fecha_inicio": start_date + timedelta(days=int(cur)),
            "fecha_fin":    start_date + timedelta(days=int(cur + dur)),
        })
        cur += dur
    total_dias = cur

    # Curva S: % acumulado planificado por día (progreso lineal dentro de cada actividad)
    scurve = []
    d = 0.0
    while d <= total_dias + 0.001:
        pct = 0.0
        for a in acts:
            frac = (d - a["inicio"]) / a["duracion"] if a["duracion"] else 1.0
            frac = min(1.0, max(0.0, frac))
            pct += a["peso"] * frac
        scurve.append((d, round(pct, 1)))
        d += 1.0

    return {
        "activities":  acts,
        "total_dias":  int(total_dias),
        "scurve":      scurve,
        "start_date":  start_date,
        "fecha_fin":   start_date + timedelta(days=int(total_dias)),
    }


def real_scurve(sched: dict, avances: list, upto_day=None) -> list:
    """Curva S REAL (avance ganado): Σ peso_i · (avance_i/100) · frac_planificada_i(d).
    `avances` = lista alineada con sched['activities'] (avance % 0-100 de cada actividad).
    Se construye SOLO hasta `upto_day` (p.ej. hoy): no se extiende hasta la fecha final."""
    acts  = sched["activities"]
    total = max(1, sched["total_dias"])
    top   = total if upto_day is None else max(0, min(int(upto_day), total))
    curve = []
    d = 0.0
    while d <= top + 0.001:
        pct = 0.0
        for a, av in zip(acts, avances):
            frac = (d - a["inicio"]) / a["duracion"] if a["duracion"] else 1.0
            frac = min(1.0, max(0.0, frac))
            pct += a["peso"] * (float(av) / 100.0) * frac
        curve.append((d, round(pct, 1)))
        d += 1.0
    return curve


def _scurve_at(sched: dict, day: float) -> float:
    """% planificado (curva S) en un día dado (interpolado)."""
    sc = sched["scurve"]
    if day <= sc[0][0]:
        return sc[0][1]
    if day >= sc[-1][0]:
        return sc[-1][1]
    for (d0, p0), (d1, p1) in zip(sc, sc[1:]):
        if d0 <= day <= d1:
            return p0 if d1 == d0 else p0 + (p1 - p0) * (day - d0) / (d1 - d0)
    return sc[-1][1]


def _day_at_pct(sched: dict, pct: float) -> float:
    """Día en que la curva S planificada alcanza un % dado (inverso, interpolado)."""
    sc = sched["scurve"]
    pct = max(0.0, min(100.0, pct))
    if pct <= sc[0][1]:
        return sc[0][0]
    if pct >= sc[-1][1]:
        return sc[-1][0]
    for (d0, p0), (d1, p1) in zip(sc, sc[1:]):
        if p0 <= pct <= p1:
            return d0 if p1 == p0 else d0 + (d1 - d0) * (pct - p0) / (p1 - p0)
    return sc[-1][0]


def schedule_projection(sched: dict, avances: list, today_day) -> dict:
    """Proyección avance-vs-fecha (earned value).
      EV (real)  = Σ peso·avance/100  (lo efectivamente hecho)
      PV (plan)  = curva S en hoy
      desvío     = EV − PV  (+ adelantado, − atrasado)
      dias_gap   = hoy − día en que el plan alcanzaba EV  (+ retraso, − adelanto)
      SPI        = EV / PV ;  fin proyectado = inicio + total/SPI
    """
    acts  = sched["activities"]
    total = max(1, sched["total_dias"])
    start = sched["start_date"]

    ev = round(sum(a["peso"] * (float(av) / 100.0) for a, av in zip(acts, avances)), 1)
    t_c = max(0, min(int(today_day), total))
    pv  = round(_scurve_at(sched, t_c), 1)
    desvio = round(ev - pv, 1)

    d_equiv  = _day_at_pct(sched, ev)
    dias_gap = round(float(today_day) - d_equiv, 1)     # + retraso, − adelanto

    spi = (ev / pv) if pv > 0 else None
    if spi and spi > 0:
        proj_total = total / spi
        proj_dias  = round(proj_total - total, 1)         # + tarde, − antes
        fecha_proj = start + timedelta(days=int(round(proj_total)))
    else:
        proj_dias, fecha_proj = None, None

    return {
        "ev": ev, "pv": pv, "desvio": desvio, "dias_gap": dias_gap,
        "spi": round(spi, 2) if spi else None,
        "proj_dias": proj_dias, "fecha_proj": fecha_proj,
        "today_day": t_c, "total": total,
    }


def _esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def schedule_svg(sched: dict, real_curve: list = None, today_day: float = None,
                 avances: list = None) -> str:
    """SVG con Gantt (arriba) + curva S (abajo) compartiendo el eje de tiempo.
    Sin <marker>/<defs> → compatible con Streamlit y svglib.

    Si `real_curve` (de real_scurve) viene, se superpone la curva REAL (verde) sobre la
    planificada (naranja) y se marca la línea `today_day` ("HOY").
    Si `avances` viene (alineado con las actividades), cada barra del Gantt se "llena"
    según el % de avance de esa actividad (verde si 100%). Sin `avances`, barra sólida."""
    acts  = sched["activities"]
    total = max(1, sched["total_dias"])
    start = sched["start_date"]
    n     = len(acts)

    VW    = 700
    ML    = 210          # margen izq. para nombres
    MR    = 40
    MT    = 46
    rowH  = 22
    gantt_h = n * rowH
    gap   = 30
    sc_h  = 150          # alto curva S
    xaxis_h = 34
    VH    = MT + gantt_h + gap + sc_h + xaxis_h

    pw = VW - ML - MR
    def sx(day): return ML + (day / total) * pw

    p = [f'<svg viewBox="0 0 {VW} {VH}" xmlns="http://www.w3.org/2000/svg" '
         f'style="width:100%;max-width:{VW}px;font-family:system-ui,sans-serif;display:block;margin:0 auto">']
    p.append(f'<text x="{VW/2:.0f}" y="20" text-anchor="middle" font-size="14" '
             f'fill="#1a3a5c" font-weight="bold">Cronograma y curva S del proyecto</text>')
    p.append(f'<text x="{VW/2:.0f}" y="36" text-anchor="middle" font-size="9" fill="#888">'
             f'{start.strftime("%d/%m/%Y")} → {sched["fecha_fin"].strftime("%d/%m/%Y")}  ·  '
             f'{total} días  ·  {n} actividades</text>')

    # ── Gantt ───────────────────────────────────────────────
    gantt_top = MT
    # líneas verticales de referencia (cada ~5 días)
    step = 5 if total > 15 else (2 if total > 6 else 1)
    d = 0
    while d <= total:
        x = sx(d)
        p.append(f'<line x1="{x:.1f}" y1="{gantt_top:.1f}" x2="{x:.1f}" '
                 f'y2="{gantt_top+gantt_h+sc_h+gap:.1f}" stroke="#eee" stroke-width="1"/>')
        d += step

    for i, a in enumerate(acts):
        y = gantt_top + i * rowH
        # nombre
        nm = a["nombre"]
        if len(nm) > 30: nm = nm[:29] + "…"
        p.append(f'<text x="6" y="{y+rowH*0.68:.1f}" font-size="9.5" fill="#333">{_esc(nm)}</text>')
        # barra
        x0 = sx(a["inicio"]); x1 = sx(a["inicio"] + a["duracion"])
        w  = max(2, x1 - x0)
        if avances is not None:
            av = max(0.0, min(100.0, float(avances[i]) if i < len(avances) else 0.0))
            # fondo tenue (planificado) + relleno según avance
            p.append(f'<rect x="{x0:.1f}" y="{y+3:.1f}" width="{w:.1f}" height="{rowH-8}" '
                     f'rx="3" fill="#dbe6f2" stroke="#2e6da4" stroke-width="0.7"/>')
            fw = w * av / 100.0
            if fw > 0.5:
                col = "#27ae60" if av >= 100 else "#2e6da4"
                p.append(f'<rect x="{x0:.1f}" y="{y+3:.1f}" width="{fw:.1f}" height="{rowH-8}" '
                         f'rx="3" fill="{col}"/>')
            p.append(f'<text x="{x1+4:.1f}" y="{y+rowH*0.68:.1f}" font-size="8" fill="#2e6da4">'
                     f'{a["peso"]:.0f}% · {av:.0f}%</text>')
        else:
            p.append(f'<rect x="{x0:.1f}" y="{y+3:.1f}" width="{w:.1f}" height="{rowH-8}" '
                     f'rx="3" fill="#2e6da4"/>')
            p.append(f'<text x="{x1+4:.1f}" y="{y+rowH*0.68:.1f}" font-size="8" fill="#2e6da4">'
                     f'{a["peso"]:.0f}%</text>')

    # ── Curva S ─────────────────────────────────────────────
    sc_top = gantt_top + gantt_h + gap
    def sy(pct): return sc_top + (1 - pct/100.0) * sc_h
    # ejes/grilla horizontal 0/25/50/75/100
    for pct in (0, 25, 50, 75, 100):
        yy = sy(pct)
        p.append(f'<line x1="{ML:.1f}" y1="{yy:.1f}" x2="{VW-MR:.1f}" y2="{yy:.1f}" '
                 f'stroke="{"#ccc" if pct in (0,100) else "#eee"}" stroke-width="1"/>')
        p.append(f'<text x="{ML-6:.1f}" y="{yy+3:.1f}" text-anchor="end" font-size="8" fill="#999">{pct}%</text>')
    p.append(f'<text x="{ML-6:.1f}" y="{sc_top-4:.1f}" text-anchor="end" font-size="8.5" '
             f'fill="#BA7517" font-weight="bold">Avance</text>')
    # polilínea de la curva S planificada
    pts = " ".join(f"{sx(dd):.1f},{sy(pc):.1f}" for dd, pc in sched["scurve"])
    p.append(f'<polyline points="{pts}" fill="none" stroke="#BA7517" stroke-width="2.5"/>')
    # puntos
    for dd, pc in sched["scurve"]:
        if int(dd) % max(1, step) == 0:
            p.append(f'<circle cx="{sx(dd):.1f}" cy="{sy(pc):.1f}" r="2.2" fill="#BA7517"/>')

    # ── Curva S REAL superpuesta + línea HOY ────────────────
    if real_curve:
        rpts = " ".join(f"{sx(dd):.1f},{sy(pc):.1f}" for dd, pc in real_curve)
        p.append(f'<polyline points="{rpts}" fill="none" stroke="#2e8b57" stroke-width="2.5"/>')
        for dd, pc in real_curve:
            if int(dd) % max(1, step) == 0:
                p.append(f'<circle cx="{sx(dd):.1f}" cy="{sy(pc):.1f}" r="2.2" fill="#2e8b57"/>')
        # leyenda (arriba a la derecha del área de la curva)
        lgx = VW - MR - 140
        lgy = sc_top + 9
        p.append(f'<rect x="{lgx:.1f}" y="{lgy-6:.1f}" width="12" height="3" fill="#BA7517"/>')
        p.append(f'<text x="{lgx+16:.1f}" y="{lgy:.1f}" font-size="8" fill="#666">Planificada</text>')
        p.append(f'<rect x="{lgx+78:.1f}" y="{lgy-6:.1f}" width="12" height="3" fill="#2e8b57"/>')
        p.append(f'<text x="{lgx+94:.1f}" y="{lgy:.1f}" font-size="8" fill="#666">Real</text>')
    if today_day is not None and 0 <= today_day <= total:
        hx = sx(today_day)
        p.append(f'<line x1="{hx:.1f}" y1="{sc_top:.1f}" x2="{hx:.1f}" y2="{sc_top+sc_h:.1f}" '
                 f'stroke="#c0392b" stroke-width="1.2" stroke-dasharray="4,3"/>')
        p.append(f'<text x="{hx:.1f}" y="{sc_top-4:.1f}" text-anchor="middle" font-size="8" '
                 f'fill="#c0392b" font-weight="bold">HOY</text>')

    # ── Eje X (fechas) ──────────────────────────────────────
    xaxis_y = sc_top + sc_h
    d = 0
    while d <= total:
        x = sx(d)
        fecha = (start + timedelta(days=int(d)))
        p.append(f'<line x1="{x:.1f}" y1="{xaxis_y:.1f}" x2="{x:.1f}" y2="{xaxis_y+4:.1f}" stroke="#999" stroke-width="1"/>')
        p.append(f'<text x="{x:.1f}" y="{xaxis_y+15:.1f}" text-anchor="middle" font-size="7.5" fill="#666">'
                 f'{fecha.strftime("%d/%m")}</text>')
        d += step
    p.append("</svg>")
    return "".join(p)


def schedule_table(sched: dict) -> list:
    """Filas para tabla / editor."""
    rows = []
    for a in sched["activities"]:
        rows.append({
            "Actividad":   a["nombre"],
            "Inicio":      a["fecha_inicio"].strftime("%d/%m/%Y"),
            "Fin":         a["fecha_fin"].strftime("%d/%m/%Y"),
            "Duración (d)": int(a["duracion"]),
            "Peso (%)":    a["peso"],
        })
    return rows
