"""
Gestión de proyecto: cronograma (Gantt) + curva S de avance planificado.

El cronograma se genera automáticamente a partir de:
  - NS (número de paradas)  → escala las actividades que dependen de pisos
  - banderas del análisis   → cortes (OR/OL > límite), ajuste de shaft (BSR<BS)
Las duraciones y pesos son editables por el usuario; la curva S se recalcula.

Pesos con distribución en "S" (bajo al inicio, alto en el medio, bajo al final)
→ el avance acumulado planificado dibuja la clásica curva S.
"""

from core.i18n import d as _d
from datetime import date, timedelta

from core import plan
from core.num import num as _num          # v512/v323: UNA definición de num()

# ⚠️ v515 · `PHASES`, `FASE_RIPOUT` y `detect_flags` SE BORRARON. Eran las 11 fases
# ideales que este módulo inventaba cuando nadie le pasaba filas, más la de desmontaje
# (v470) y las dos banderas que el survey calculaba (`cortes`, `shaft`).
#
# No se adaptaron: el usuario decidió que las actividades con las que se trabaja son
# las del CATÁLOGO (`core/stages.py`, v512) y las anteriores ya no van. v512 cambió los
# dos caminos que crean obras —cotización aceptada y alta manual— y el survey se quedó
# atrás: su informe le enseñaba al cliente once actividades de las que **ni una** existía
# en la obra que salía de esa misma cotización. Medido: 0 nombres en común de 11.
#
# ⚠️ Lo que se pierde con las banderas NO es información, es una duplicación peor. Los
# cortes por OR/OL siguen en el veredicto de portada del informe del cliente y en su
# sección 3, **piso por piso**, que es lo que se usa en obra; el BS/BSR sigue en su
# sección. Lo que desaparece es una barra de Gantt que decía lo mismo con menos detalle.
#
# ⚠️ Y el desmontaje ya no es UNA actividad: son las cuatro etapas de la pista `ripout`
# del catálogo, con sus 30 actividades. `ripout=True` sigue significando lo mismo para
# quien llama —«esta obra incluye desmontaje»—, pero ahora se traduce a un TIPO de
# proyecto, que es donde vive esa decisión desde v512.


# ── v512: el cronograma sale del CATÁLOGO de etapas ──────────────────────────
# (días de base, días por parada) de cada pista. ⚠️ El catálogo de `stages` es de PESO,
# no de tiempo: tus documentos ponderan esfuerzo y no dicen cuánto dura nada. Estos dos
# números salen de lo que esta misma función venía suponiendo — `PHASES` sumaba 17 días
# de base y 2,0 por parada, y `FASE_RIPOUT` 3 y 0,5 —, así que una obra de 8 paradas
# sigue dando los ~33 días de instalación de siempre. Son un ARRANQUE, como los pesos.
DIAS_POR_PISTA = {"install": (17.0, 2.0), "ripout": (3.0, 0.5)}


def filas_de_etapas(tipo, ns: int, condicionales=(), pct_ripout=None) -> list:
    """Las etapas de esta obra como filas de cronograma: `{nombre, duracion, peso}`.

    Sustituye a `PHASES` (v512). La diferencia de fondo no es la lista: es que el
    **avance de cada etapa ya no se teclea**, se calcula desde sus actividades. Aquí
    solo se arma el esqueleto temporal.

    ⚠️ El peso viene YA renormalizado por `stages.plan_de`, que descuenta las
    condicionales que esta obra no lleva. `build_schedule` vuelve a normalizar a 100 por
    su cuenta, lo cual es inofensivo —normalizar algo que ya suma 100 no lo mueve— y se
    deja así para no tocar un camino que usan los cronogramas editados a mano.

    ⚠️ La duración se reparte por peso DENTRO de su pista, no sobre el total: si no, en
    una obra combinada el desmontaje heredaría días de la instalación y al revés.
    """
    from core import stages as _S
    plan_obra = _S.plan_de(tipo, condicionales, pct_ripout)
    if not plan_obra:
        return []
    n = max(1, int(_num(ns) or 1))
    # Peso de cada etapa DENTRO de su pista (el del plan es sobre la obra entera).
    por_pista = {}
    for e in plan_obra:
        por_pista[e["pista"]] = por_pista.get(e["pista"], 0.0) + float(e["peso"])
    # ⚠️ Los días se reparten por RESTO MAYOR, no redondeando cada etapa por su cuenta.
    # Redondeando una a una, catorce etapas no suman los mismos días que las once fases
    # del modelo viejo y la fecha de entrega se movía **hasta 3 días** — medido: de 30
    # números de paradas, solo 7 daban la misma fecha. Con el reparto del resto, el
    # total es exactamente `base + por_parada × NS`, que es la misma fórmula de antes, y
    # la entrega no se mueve para NINGÚN número de paradas.
    filas = []
    for pista in por_pista:
        idx = [i for i, e in enumerate(plan_obra) if e["pista"] == pista]
        base, por_parada = DIAS_POR_PISTA.get(pista, (1.0, 0.0))
        objetivo = max(len(idx), int(round(base + por_parada * n)))
        exactos = [objetivo * float(plan_obra[i]["peso"]) / por_pista[pista] for i in idx]
        # Suelo de UN día: una etapa de medio día saldría en 0 y la red de v499 la
        # trataría como instantánea, arrastrando mal todo lo que va detrás.
        dias = [max(1, int(x)) for x in exactos]
        resto = objetivo - sum(dias)
        if resto > 0:
            # Los días que faltan van a las etapas que más perdieron al truncar.
            for j in sorted(range(len(idx)), key=lambda k: -(exactos[k] - int(exactos[k])))[:resto]:
                dias[j] += 1
        for k, i in enumerate(idx):
            filas.append({
                "nombre": plan_obra[i]["nombre"],
                "duracion": float(dias[k]),
                "peso": float(plan_obra[i]["peso"]),
                "orden": i + 1,
                "pred": "",      # vacío = detrás de la anterior (v499): no mueve nada
            })
    return sorted(filas, key=lambda f: f["orden"])


def build_schedule(ns: int, start_date: date, condicionales=None,
                   custom_rows: list = None, ripout: bool = False) -> dict:
    """
    Genera el cronograma. Si `custom_rows` viene (edición del usuario),
    usa sus duraciones/pesos en lugar de los automáticos.
    custom_rows: lista de dicts {nombre, duracion, peso}

    Sin `custom_rows`, las filas salen del CATÁLOGO (v515). Antes salían de `PHASES`,
    que ya no existe: quien no traiga filas propias recibe las MISMAS etapas que la
    obra real, no una lista paralela que se queda vieja sola.

    `ripout=True` = esta obra incluye el desmontaje del ascensor existente. ⚠️ Desde
    v515 eso no es UNA actividad antepuesta (v470) sino un TIPO de proyecto: son las
    cuatro etapas de la pista `ripout`, con sus 30 actividades, y van con el resto en un
    solo 100%. ⚠️ NO aplica sobre `custom_rows`: ahí las filas son las que el usuario ya
    editó y el tipo quedó sellado en el plan de la obra (`StagePlanJSON`).

    ⚠️ `condicionales` sustituye al `flags` de antes, que era un dict de banderas del
    survey (`cortes`, `shaft`). Ahora son los NOMBRES de las actividades condicionales
    del catálogo que esta obra lleva. Se acepta un dict —lo que pasaban los llamantes
    viejos— y se leen sus claves verdaderas, así que `{}` sigue queriendo decir «ninguna».
    """
    ns = max(1, int(ns or 1))

    if custom_rows:
        base = [(r["nombre"], float(r["duracion"]), float(r["peso"])) for r in custom_rows]
        # v499: cada fila puede traer su orden y sus predecesoras («3;5-2»)
        red = [{"orden": r.get("orden", i + 1), "duracion": float(r["duracion"]),
                "pred": r.get("pred", "")} for i, r in enumerate(custom_rows)]
    else:
        if isinstance(condicionales, dict):
            _cond = [k for k, v in condicionales.items() if v]
        else:
            _cond = list(condicionales or ())
        _tipo = "Ripout + Installation" if ripout else "Installation"
        base = [(r["nombre"], float(r["duracion"]), float(r["peso"]))
                for r in filas_de_etapas(_tipo, ns, _cond)]

    # Normalizar pesos a 100
    total_peso = sum(p for _, _, p in base) or 1.0

    # ⚠️ v499: el inicio de cada actividad sale de la RED (`plan.calcular`), no de acumular
    # duraciones. Con la columna vacía, cada una va detrás de la anterior — exactamente lo
    # que hacía esta función hasta v498, así que un cronograma existente no se mueve.
    if not custom_rows:
        red = [{"orden": i + 1, "duracion": d, "pred": ""} for i, (_n, d, _p) in enumerate(base)]
    calc = plan.calcular(red)
    avisos_plan = calc["avisos"]

    # ⚠️ v512: los pesos normalizados se reparten por RESTO MAYOR. Redondeando cada uno
    # a un decimal por su cuenta, catorce o dieciocho actividades sumaban **99,8** en la
    # hoja en vez de 100. El avance no se veía afectado —`compute_avance` divide por
    # Σpeso, así que es escala-invariante— pero la columna que mira el usuario mentía, y
    # un plan cuyos pesos no suman 100 invita a buscar un error que no existe.
    # Lo encontró el ejercicio contra la hoja REAL, no el guardián: este comprobaba los
    # pesos que salen de `filas_de_etapas` (exactos) y no los que escribe esta función.
    # El fallo vivía justo en la frontera entre las dos capas.
    # ⚠️ `_du`, no `_d`: `_d` es la funcion de display de i18n a nivel de modulo.
    # Aqui no se filtraria (una comprension tiene ambito propio), pero es el patron
    # que tumbo v439 y v503 en sitios donde SI se filtra, y `verif_v438` lo caza.
    _pn = [round(p * 100.0 / total_peso, 1) for _n, _du, p in base]
    _resto = round(100.0 - sum(_pn), 1)
    if _pn and abs(_resto) >= 0.05:
        # La décima que falta (o sobra) va a la actividad más grande: es donde menos se
        # nota en proporción, y así no aparece en una etapa pequeña como un pico raro.
        _pn[max(range(len(_pn)), key=lambda k: _pn[k])] = round(
            _pn[max(range(len(_pn)), key=lambda k: _pn[k])] + _resto, 1)

    acts = []
    for i, (nombre, dur, peso) in enumerate(base):
        peso_n = _pn[i]
        _r = calc["por_orden"].get(int(red[i]["orden"]), {"inicio": 0.0, "fin": dur, "critica": False})
        acts.append({
            "nombre":       nombre,
            "inicio":       _r["inicio"],
            "duracion":     dur,
            "peso":         peso_n,
            "critica":      _r["critica"],
            "orden":        int(red[i]["orden"]),
            "pred":         str(red[i].get("pred", "") or ""),
            "fecha_inicio": start_date + timedelta(days=int(_r["inicio"])),
            "fecha_fin":    start_date + timedelta(days=int(_r["inicio"] + dur)),
        })
    total_dias = calc["total_dias"]

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
        # v499: lo que el encadenado no pudo resolver (ciclo, referencia que ya no existe).
        # Va en el resultado para que la PANTALLA lo diga: un plan mal encadenado se
        # dibuja igual, y hay que poder verlo para arreglarlo.
        "avisos_plan": avisos_plan,
    }


def real_scurve(sched: dict, avances: list, upto_day=None, windows=None) -> list:
    """Curva S REAL = avance GANADO acumulado, construido SOLO hasta HOY (`upto_day`).

    Cada actividad aporta `peso·(avance/100)`, repartido sobre su ventana REAL
    [inicio_real, fin_real] si se conoce; si no, sobre [inicio_proyecto (0), hoy].
    Clave: en el día de HOY la curva llega al **avance real total** (no se descuenta
    al futuro aunque el trabajo se haya hecho antes de la fecha planificada).
    `windows` = lista alineada con las actividades, cada una (s_day, f_day) o None."""
    acts  = sched["activities"]
    total = max(1, sched["total_dias"])
    top   = total if upto_day is None else max(0, min(int(upto_day), total))
    curve = []
    d = 0.0
    while d <= top + 0.001:
        pct = 0.0
        for i, (a, av) in enumerate(zip(acts, avances)):
            e = a["peso"] * (float(av) / 100.0)          # avance ganado de la actividad
            if e <= 0:
                continue
            s_raw, f_raw = (windows[i] if windows and i < len(windows) else (None, None))
            s = 0.0 if s_raw is None else float(s_raw)    # inicio real, o inicio del proyecto
            f = top  if f_raw is None else float(f_raw)   # fin real, o HOY (en curso)
            s = min(max(0.0, s), top)
            f = min(max(s, f), top)
            if d >= f:
                frac = 1.0
            elif d <= s:
                frac = 0.0
            else:
                frac = (d - s) / (f - s) if f > s else 1.0
            pct += e * frac
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


def schedule_projection(sched: dict, avances: list, today_day, windows=None) -> dict:
    """Proyección avance-vs-fecha (earned value).
      EV (real)  = Σ peso·avance/100  (lo efectivamente hecho)
      PV (plan)  = curva S en hoy
      desvío     = EV − PV  (+ adelantado, − atrasado)
      dias_gap   = hoy − día en que el plan alcanzaba EV  (+ retraso, − adelanto)
      SPI        = EV / PV   (ritmo: a qué velocidad se avanza)
      fin previsto = por la CADENA (`plan.pronostico`), NO por el SPI — v500
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

    # ⚠️ v500: el SPI se CONSERVA porque responde otra pregunta —a qué ritmo se avanza—,
    # pero ya no produce una fecha. Tener dos respuestas a «cuándo termina» es como
    # Rentabilidad y el detalle acabaron dando dos ingresos distintos para la misma obra
    # (v361): mientras coinciden nadie lo nota, y el día que discrepan ya está en pantalla.
    spi = (ev / pv) if pv > 0 else None

    # El fin previsto, por la CADENA. El SPI es una regla de tres sobre el % de
    # avance, así que reparte el retraso entre todas las actividades por igual; la cadena
    # sabe QUÉ falta y qué arrastra qué — una obra al 50% en la mitad del plazo va «en
    # hora» para el SPI aunque la actividad que bloquea a las demás no haya empezado.
    red = [{"orden":    a.get("orden", i + 1),
            "duracion": a["duracion"],
            "pred":     a.get("pred", ""),
            "avance":   (avances[i] if i < len(avances) else 0),
            "ini_real": (windows[i][0] if windows and i < len(windows) else None),
            "fin_real": (windows[i][1] if windows and i < len(windows) else None)}
           for i, a in enumerate(acts)]
    _pr = plan.pronostico(red, today_day)
    fin_cadena = _pr["total_dias"]
    dias_cadena = round(fin_cadena - total, 1)            # + tarde, − antes
    fecha_cadena = start + timedelta(days=int(round(fin_cadena)))
    # las que MANDAN en esa fecha: son las que hay que empujar para recuperar
    criticas_cadena = [o for o, v in _pr["por_orden"].items() if v["critica"]]

    return {
        "ev": ev, "pv": pv, "desvio": desvio, "dias_gap": dias_gap,
        "spi": round(spi, 2) if spi else None,
        "fecha_cadena": fecha_cadena, "dias_cadena": dias_cadena,
        "criticas_cadena": criticas_cadena,
        "today_day": t_c, "total": total,
    }


def _esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def schedule_svg_alto(n_actividades: int, vw: int = 760) -> int:
    """Alto REAL del SVG (v311). El `components.html` que lo envuelve necesita una
    altura fija en px y estaba puesta a ojo (`300 + n*21`), **18 px menos** que el
    SVG → el pie del gráfico se recortaba. Aquí sale de la misma fórmula que `VH`,
    así que no pueden volver a divergir.
    """
    return 52 + n_actividades * 21 + 34 + 170 + 36 + 26


def schedule_svg(sched: dict, real_curve: list = None, today_day: float = None,
                 avances: list = None, proj: dict = None, titulo: str = "",
                 vw: int = 760, animar: bool = False) -> str:
    """Gantt + curva S con el lenguaje de los planos técnicos (v143).

    El problema de la version anterior no era estetico: la BRECHA entre plan y
    real —que es toda la historia— había que deducirla comparando dos lineas
    finas. Aqui la brecha se RELLENA (roja si vas por detras, verde si por
    delante), asi se ve cuanto y desde cuando de un vistazo.

    Ademas: areas con cuerpo, HOY como banda que cruza TAMBIEN el Gantt (antes
    solo la curva), proyeccion al ritmo actual en trazo discontinuo, y jerarquia
    en las barras: terminada / en curso / **deberia haber empezado** / futura.

    `proj` es lo que devuelve schedule_projection. OJO: su `dias_cadena` es la
    DIFERENCIA contra el plan (+ tarde / − antes), no el dia absoluto.

    Sin <marker>/<defs> → compatible con Streamlit y svglib.
    """
    acts  = sched["activities"]
    total = max(1, sched["total_dias"])
    start = sched["start_date"]
    n     = len(acts)

    # ⚠️ v311: `vw` es PARÁMETRO, con el 760 de siempre por defecto. En la app el
    # gráfico se pedía a 760 px y quedaba centrado en un contenedor de 1340 con 290 px
    # de margen a cada lado — y con `ML=214`/`MR=116` las barras vivían en 430 px.
    # NO se sube el default: este mismo SVG va a los informes PDF (report/user_report),
    # donde svglib lo escala al ancho de la página; con un lienzo más ancho y el mismo
    # alto, la misma altura se repartiría entre 13 filas aplastadas. La app pide ancho;
    # el PDF se queda como estaba.
    VW, ML, MR, MT = int(vw), 214, 116, 52
    rowH, gap, sc_h, xaxis_h = 21, 34, 170, 36
    gantt_h   = n * rowH
    VH        = MT + gantt_h + gap + sc_h + xaxis_h + 26
    pw        = VW - ML - MR
    gantt_top = MT
    sc_top    = gantt_top + gantt_h + gap

    # ⚠️ v500: el dia absoluto en que se terminaria SEGUN LA CADENA (dias_cadena es el
    # DELTA). Antes salia del ritmo (SPI); si esta clave se quedara con el nombre viejo,
    # la proyeccion DESAPARECERIA del grafico sin dar ningun error.
    proj_total = None
    if proj and proj.get("dias_cadena") is not None:
        proj_total = total + float(proj["dias_cadena"])

    # El eje se estira para que quepa la proyeccion, pero con TOPE: si el ritmo
    # actual da una fecha lejanisima, estirar hasta alli aplastaria el Gantt (que
    # es el contenido principal). Pasado el tope la proyeccion se dibuja hasta el
    # borde y la fecha se rotula con "▸".
    tope    = total * 1.32
    fin_eje = max(1.0, min(max(total, proj_total or 0), tope))
    if today_day is not None:                 # HOY SIEMPRE tiene que caber:
        fin_eje = max(fin_eje, float(today_day))   # si no, un proyecto pasado de
                                                   # fecha perdia su marca de HOY
    proj_x  = min(proj_total, fin_eje) if proj_total else None
    proj_cortada = bool(proj_total and proj_total > fin_eje + 0.01)

    def sx(day): return ML + (day / fin_eje) * pw
    def sy(pct): return sc_top + (1 - pct / 100.0) * sc_h

    C_PLAN, C_REAL, C_HOY, C_GRIS = "#BA7517", "#1e8449", "#c0392b", "#9aa7b8"
    p = [f'<svg viewBox="0 0 {VW} {VH}" xmlns="http://www.w3.org/2000/svg" '
         f'style="width:100%;max-width:{VW}px;font-family:Arial,Helvetica,sans-serif;'
         f'display:block;margin:0 auto">',
         f'<rect x="0" y="0" width="{VW}" height="{VH}" fill="#ffffff"/>',
         # ── Trazado animado de las curvas (v336) ────────────────────────
         # ⚠️ Solo con `animar=True`, que SOLO pasan los dos call-sites de PANTALLA.
         # El mismo SVG va al PDF por `svglib` (report.py / user_report.py) y ahí un
         # `<style>` con @keyframes es, en el mejor caso, ignorado. Por defecto
         # `animar=False` → el PDF sale byte a byte como hasta ahora.
         #
         # Aquí la animación ES el dato: la curva se traza de izquierda a derecha,
         # así que el tiempo se lee como tiempo. Es lo único puramente expresivo de
         # todo el lote y está ganado.
         ('<style>'
          '@keyframes cpx-trazar{to{stroke-dashoffset:0}}'
          '.cpx-traza{stroke-dasharray:4000;stroke-dashoffset:4000;'
          'animation:cpx-trazar .9s cubic-bezier(.25,.6,.3,1) forwards}'
          '.cpx-traza-2{animation-delay:.18s}'
          '@media (prefers-reduced-motion:reduce){'
          '.cpx-traza{animation:none;stroke-dashoffset:0}}'
          '</style>') if animar else "",
         f'<text x="18" y="24" font-size="13" fill="#1a3a5c" font-weight="bold">'
         f'{_d("SCHEDULE AND PROGRESS")}</text>',
         f'<text x="18" y="39" font-size="8.5" fill="#5b6472">'
         f'{_esc(titulo) + " · " if titulo else ""}'
         f'{start.strftime("%d/%m/%Y")} → {sched["fecha_fin"].strftime("%d/%m/%Y")} · '
         f'{total} {_d("days")} · {n} {_d("activities")}</text>']

    # ── Rejilla vertical: la comparten Gantt y curva ────────
    step = 5 if fin_eje > 15 else (2 if fin_eje > 6 else 1)
    d = 0
    while d <= fin_eje:
        x = sx(d)
        p.append(f'<line x1="{x:.1f}" y1="{gantt_top-6:.1f}" x2="{x:.1f}" '
                 f'y2="{sc_top+sc_h:.1f}" stroke="#f0f2f6" stroke-width="1"/>')
        d += step

    # ── Banda de HOY: cruza Gantt Y curva (antes solo la curva) ──
    if today_day is not None and 0 <= today_day <= fin_eje:
        hx = sx(today_day)
        p.append(f'<rect x="{hx-2:.1f}" y="{gantt_top-6:.1f}" width="4" '
                 f'height="{sc_top+sc_h-gantt_top+6:.1f}" fill="{C_HOY}" fill-opacity="0.09"/>')
        p.append(f'<line x1="{hx:.1f}" y1="{gantt_top-6:.1f}" x2="{hx:.1f}" '
                 f'y2="{sc_top+sc_h:.1f}" stroke="{C_HOY}" stroke-width="1.1" '
                 f'stroke-dasharray="5,3"/>')
        p.append(f'<text x="{hx:.1f}" y="{gantt_top-11:.1f}" text-anchor="middle" '
                 f'font-size="8.5" fill="{C_HOY}" font-weight="bold">{_d("TODAY")}</text>')

    # ── Gantt con jerarquia ─────────────────────────────────
    for i, a in enumerate(acts):
        y  = gantt_top + i * rowH
        av = max(0.0, min(100.0, float(avances[i])
                          if (avances and i < len(avances)) else 0.0))
        x0, x1 = sx(a["inicio"]), sx(a["inicio"] + a["duracion"])
        w = max(2.0, x1 - x0)

        # ¿deberia estar en curso hoy?
        ventana = (today_day is not None
                   and a["inicio"] <= today_day <= a["inicio"] + a["duracion"])
        if av >= 100:
            col, txt = C_REAL, "#6b7280"          # terminada
        elif av > 0:
            col, txt = "#2e6da4", "#1f2937"       # en curso
        elif ventana:
            col, txt = C_HOY, C_HOY               # tocaba y no ha arrancado
        else:
            col, txt = C_GRIS, C_GRIS             # futura

        nm = a["nombre"]
        if len(nm) > 32:
            nm = nm[:31] + "…"
        if ventana and av < 100:
            p.append(f'<text x="6" y="{y+rowH*0.70:.1f}" font-size="9" fill="{C_HOY}">●</text>')
        p.append(f'<text x="15" y="{y+rowH*0.70:.1f}" font-size="9.5" fill="{txt}">'
                 f'{_esc(nm)}</text>')
        # ⚠️ v499: la barra de una actividad de la RUTA CRÍTICA lleva borde marcado. Es
        # la información que trae el encadenado: atrasar ESAS atrasa la entrega; las otras
        # tienen holgura. Solo el borde — el relleno ya dice el estado (terminada/en curso).
        _cri = bool(a.get("critica"))
        p.append(f'<rect x="{x0:.1f}" y="{y+3:.1f}" width="{w:.1f}" height="{rowH-8}" '
                 f'rx="2.5" fill="#eef1f5" stroke="{"#c0392b" if _cri else "#dfe4ec"}" '
                 f'stroke-width="{1.4 if _cri else 0.7}"/>')
        if av > 0:
            p.append(f'<rect x="{x0:.1f}" y="{y+3:.1f}" width="{w*av/100.0:.1f}" '
                     f'height="{rowH-8}" rx="2.5" fill="{col}" fill-opacity="0.92"/>')
        elif ventana:
            for k in range(int(w // 7) + 1):      # achurado = tocaba y sigue en 0
                xx = x0 + 4 + k * 7
                if xx < x0 + w - 1:
                    p.append(f'<line x1="{xx:.1f}" y1="{y+rowH-6:.1f}" x2="{xx+5:.1f}" '
                             f'y2="{y+4:.1f}" stroke="{C_HOY}" stroke-width="0.6" '
                             f'stroke-opacity="0.5"/>')
        p.append(f'<text x="{x0+w+5:.1f}" y="{y+rowH*0.70:.1f}" font-size="8" '
                 f'fill="{txt}">{av:.0f}%</text>')

    # ── Curva S: rejilla ────────────────────────────────────
    for pct in (0, 25, 50, 75, 100):
        yy = sy(pct)
        p.append(f'<line x1="{ML:.1f}" y1="{yy:.1f}" x2="{VW-MR:.1f}" y2="{yy:.1f}" '
                 f'stroke="{"#c3ccd8" if pct in (0, 100) else "#f0f2f6"}" stroke-width="1"/>')
        p.append(f'<text x="{ML-7:.1f}" y="{yy+3:.1f}" text-anchor="end" font-size="8" '
                 f'fill="{C_GRIS}">{pct}%</text>')

    plan = sched["scurve"]

    # ── LA BRECHA rellena: lo que antes habia que deducir a ojo ──
    if real_curve and len(real_curve) > 1:
        arriba = " ".join(f"{sx(dd):.1f},{sy(_scurve_at(sched, dd)):.1f}"
                          for dd, _ in real_curve)
        abajo  = " ".join(f"{sx(dd):.1f},{sy(pc):.1f}" for dd, pc in reversed(real_curve))
        atras  = real_curve[-1][1] < _scurve_at(sched, real_curve[-1][0])
        p.append(f'<polygon points="{arriba} {abajo}" '
                 f'fill="{C_HOY if atras else C_REAL}" fill-opacity="0.15"/>')
        # area bajo la real, para que tenga cuerpo
        base = sy(0)
        p.append(f'<polygon points="{sx(real_curve[0][0]):.1f},{base:.1f} '
                 + " ".join(f"{sx(dd):.1f},{sy(pc):.1f}" for dd, pc in real_curve)
                 + f' {sx(real_curve[-1][0]):.1f},{base:.1f}" '
                 f'fill="{C_REAL}" fill-opacity="0.10"/>')

    p.append('<polyline points="'
             + " ".join(f"{sx(dd):.1f},{sy(pc):.1f}" for dd, pc in plan)
             + f'" fill="none" stroke="{C_PLAN}" stroke-width="2.4"'
             + (' class="cpx-traza"' if animar else "") + "/>")
    if real_curve:
        p.append('<polyline points="'
                 + " ".join(f"{sx(dd):.1f},{sy(pc):.1f}" for dd, pc in real_curve)
                 + f'" fill="none" stroke="{C_REAL}" stroke-width="2.8"'
                 + (' class="cpx-traza cpx-traza-2"' if animar else "") + "/>")
        if len(real_curve) > 1:
            ddl, pcl = real_curve[-1]
            p.append(f'<circle cx="{sx(ddl):.1f}" cy="{sy(pcl):.1f}" r="4" fill="#ffffff" '
                     f'stroke="{C_REAL}" stroke-width="2"/>')
            p.append(f'<text x="{sx(ddl)+7:.1f}" y="{sy(pcl)-6:.1f}" font-size="9" '
                     f'fill="{C_REAL}" font-weight="bold">{pcl:.0f}%</text>')

    # ── Proyeccion al ritmo actual ──────────────────────────
    C_PROJ = C_REAL
    if proj_x and real_curve and len(real_curve) > 1:
        ddl, pcl = real_curve[-1]
        tarde  = proj_total > total + 0.5
        C_PROJ = C_HOY if tarde else C_REAL
        # si esta recortada, la pendiente se mantiene y se corta en el borde
        y_fin = (sy(pcl) + (sy(100) - sy(pcl)) * (proj_x - ddl) / (proj_total - ddl)
                 if proj_total > ddl else sy(100))
        p.append(f'<line x1="{sx(ddl):.1f}" y1="{sy(pcl):.1f}" x2="{sx(proj_x):.1f}" '
                 f'y2="{y_fin:.1f}" stroke="{C_PROJ}" stroke-width="1.6" '
                 f'stroke-dasharray="6,4" stroke-opacity="0.85"/>')
        if not proj_cortada:
            p.append(f'<circle cx="{sx(proj_x):.1f}" cy="{sy(100):.1f}" r="3.5" '
                     f'fill="{C_PROJ}"/>')
        if proj.get("fecha_cadena"):
            _fp = proj["fecha_cadena"].strftime("%d/%m")
            p.append(f'<text x="{sx(proj_x) - (4 if proj_cortada else 0):.1f}" '
                     f'y="{y_fin - 8:.1f}" '
                     f'text-anchor="{"end" if proj_cortada else "middle"}" font-size="8.5" '
                     f'fill="{C_PROJ}" font-weight="bold">'
                     f'{_fp}{" ▸" if proj_cortada else ""}</text>')
    # fin planificado
    p.append(f'<line x1="{sx(total):.1f}" y1="{sy(0):.1f}" x2="{sx(total):.1f}" '
             f'y2="{sy(100):.1f}" stroke="{C_PLAN}" stroke-width="1" '
             f'stroke-dasharray="3,3" stroke-opacity="0.7"/>')

    # ── Leyenda ─────────────────────────────────────────────
    lgx, lgy = ML, sc_top + sc_h + 30
    leyenda = [(_d("Planned"), C_PLAN, False), (_d("Actual"), C_REAL, False)]
    if real_curve and len(real_curve) > 1:
        leyenda.append((_d("Gap"), C_HOY, True))
    if proj_x and real_curve and len(real_curve) > 1:      # igual que al dibujarla
        leyenda.append((_d("Projection at current rate"), C_PROJ, True))
    for et, col, tenue in leyenda:
        p.append(f'<rect x="{lgx:.1f}" y="{lgy-7:.1f}" width="13" height="3.5" '
                 f'fill="{col}"' + (' fill-opacity="0.28"' if tenue else '') + '/>')
        p.append(f'<text x="{lgx+18:.1f}" y="{lgy:.1f}" font-size="8" '
                 f'fill="#5b6472">{et}</text>')
        lgx += 30 + len(et) * 5.4

    # ── Eje de fechas ───────────────────────────────────────
    xaxis_y = sc_top + sc_h
    d = 0
    while d <= fin_eje:
        x = sx(d)
        p.append(f'<line x1="{x:.1f}" y1="{xaxis_y:.1f}" x2="{x:.1f}" y2="{xaxis_y+4:.1f}" '
                 f'stroke="{C_GRIS}" stroke-width="1"/>')
        p.append(f'<text x="{x:.1f}" y="{xaxis_y+15:.1f}" text-anchor="middle" '
                 f'font-size="7.5" fill="#5b6472">'
                 f'{(start + timedelta(days=int(d))).strftime("%d/%m")}</text>')
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
