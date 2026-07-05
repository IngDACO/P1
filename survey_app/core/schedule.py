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


def _esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def schedule_svg(sched: dict) -> str:
    """SVG con Gantt (arriba) + curva S (abajo) compartiendo el eje de tiempo.
    Sin <marker>/<defs> → compatible con Streamlit y svglib."""
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
        p.append(f'<rect x="{x0:.1f}" y="{y+3:.1f}" width="{max(2,x1-x0):.1f}" height="{rowH-8}" '
                 f'rx="3" fill="#2e6da4"/>')
        # peso al final de la barra
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
    # polilínea de la curva S
    pts = " ".join(f"{sx(dd):.1f},{sy(pc):.1f}" for dd, pc in sched["scurve"])
    p.append(f'<polyline points="{pts}" fill="none" stroke="#BA7517" stroke-width="2.5"/>')
    # puntos
    for dd, pc in sched["scurve"]:
        if int(dd) % max(1, step) == 0:
            p.append(f'<circle cx="{sx(dd):.1f}" cy="{sy(pc):.1f}" r="2.2" fill="#BA7517"/>')

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
