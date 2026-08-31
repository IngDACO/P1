"""Finanzas — Fase 1: margen y rentabilidad.

Cierra el lado que faltaba (INGRESO) sobre el lado del COSTO que ya existe. La
'tarifa de venta' de la mano de obra = costo × (1 + margen%). El margen sale del
proyecto (`Proyectos.MargenMO`) o, si está vacío, del default del grupo
(`Grupos.MargenDefault`, lo fija el propietario). Los materiales se facturan a
costo por defecto (el margen sobre materiales queda para una fase futura).

Reusa `expenses.labor_cost` / `expenses.project_expenses` / `expenses.group_expenses`
(el lado del costo) — aquí solo se aplica el margen y se compara contra el costo.
Es una estimación de facturación total; las facturas reales llegan en la Fase 2.
"""
import logging

from core import auth
from core import expenses as E
from core import projects as P
from core import timeclock
from core.num import num as _num

logger = logging.getLogger(__name__)


def project_margin(pid: str, grupo: str, prj: dict = None) -> float:
    """Margen % efectivo del proyecto: el suyo si está puesto, si no el default del grupo."""
    if prj is None:
        prj = P.get_project(pid) or {}
    raw = str(prj.get("MargenMO", "")).strip()
    if raw != "":
        return _num(raw)
    return auth.group_margin_default(grupo)


def project_revenue(pid: str, grupo: str, prj: dict = None) -> dict:
    """Costo vs ingreso estimado vs ganancia de un proyecto (si se facturara todo).

    {costo_mo, materiales, costo, margen_pct, mo_facturable, ingreso, ganancia}.
    """
    from core import projects as P
    mat = E.project_expenses(pid)["total"]        # los materiales van a COSTO (v360)
    gh  = P.ganancia_hora(pid, prj)
    # v373: ganancia FIJA de la obra. Se SUMA al modelo que aplique (rubro o margen),
    # porque responde a otra pregunta: «además de lo que gano con las horas, ¿cuánto
    # vale esta obra por sí misma?». Cubre el delivery y el suministro, donde el
    # margen sobre la mano de obra no tiene sobre qué aplicarse.
    fija = P.ganancia_fija(pid, prj)

    # ── v370: si la obra nació de una cotización ACEPTADA, el ingreso es el PRECIO
    # PACTADO, no una estimación desde el costo. Es un hecho, no una conjetura: el
    # cliente ya firmó ese número y adivinarlo con costo+margen es contradecir un dato
    # que ya se tiene (misma regla que v361: UNA definición del ingreso).
    # ⚠️ Sin esto, una obra cuyo valor NO está en las horas vale exactamente lo que
    # costó — los materiales van a costo en los DOS modelos (`ingreso = mo×(1+m) + mat`),
    # así que un delivery o un suministro salían con ganancia $0. Medido: PRJ-0016 en
    # $0 con $2.960 pactados, y el delivery de Bespoke en $380 habiendo facturado $5.200.
    # ⚠️ Se usa el **Subtotal** (sin impuesto) porque `invoices.facturado_por_proyecto`
    # suma los IMPORTES DE LÍNEA, también sin impuesto. Mezclar las dos bases haría que
    # `pendiente_de_facturar = ingreso − facturado` comparara peras con manzanas.
    try:
        from core import quotes as _Q
        _cot = _Q.cotizacion_de_proyecto(pid)
    except Exception as e:                        # cotizaciones sin configurar: no rompe
        logger.warning("project_revenue: no se pudo leer la cotización de %s: %s", pid, e)
        _cot = {}
    if _cot:
        _mo = E.labor_cost(pid, grupo)
        _ing = _num(_cot.get("Subtotal"))
        _costo = round(_mo + mat, 2)
        return {"costo_mo": round(_mo, 2), "materiales": round(mat, 2), "costo": _costo,
                # el % es CONSECUENCIA del precio pactado, no una entrada
                "margen_pct": round(100.0 * (_ing - _costo) / _costo, 2) if _costo > 0 else 0.0,
                "mo_facturable": round(_mo, 2), "ingreso": round(_ing, 2),
                "ganancia": round(_ing - _costo, 2), "modelo": "cotizado",
                "cotizacion": str(_cot.get("ID", "")),
                # ⚠️ La ganancia fija NO se suma aquí: la cotización ES el precio que el
                # cliente firmó. Sumarle algo encima inventaría un ingreso que nadie
                # aceptó. Se devuelve para poder AVISAR de que no se está usando.
                "ganancia_fija": 0.0, "fija_ignorada": round(fija, 2),
                # ⚠️ `sin_ganancia` avisa de que un trabajo se facturaría A COSTO. Con el
                # precio cerrado eso no puede pasar: se cobra lo pactado trabaje quien
                # trabaje, así que aquí no hay nada que avisar.
                "por_persona": [], "sin_ganancia": []}

    if gh:
        # ── v360: ganancia por RUBRO. El trabajador es un rubro: cada persona
        # aporta `horas × su ganancia/hora` en ESTA obra. El % ya no se teclea:
        # se deriva para poder mostrarlo.
        lb = E.labor_breakdown(pid, grupo)
        mo, gan_mo, detalle = 0.0, 0.0, []
        for it in lb.get("items", []):
            u, h, c = str(it.get("usuario", "")), _num(it.get("horas")), _num(it.get("costo"))
            g = _num(gh.get(u))
            mo += c
            gan_mo += h * g
            detalle.append({"usuario": u, "horas": round(h, 2), "costo": round(c, 2),
                            "ganancia_hora": g, "ganancia": round(h * g, 2)})
        mo, gan_mo = round(mo, 2), round(gan_mo, 2)
        costo   = round(mo + mat, 2)
        gan_tot = round(gan_mo + fija, 2)
        ingreso = round(costo + gan_tot, 2)
        return {"costo_mo": mo, "materiales": mat, "costo": costo,
                # el % pasa a ser CONSECUENCIA, no entrada
                # ⚠️ `margen_pct` sigue siendo ganancia de MANO DE OBRA sobre la mano de
                # obra, EXACTAMENTE como antes de v373: cambiarle el denominador para
                # meter la ganancia fija movería el % de todas las obras que no la usan,
                # en silencio (lo contrario de la regla de v360). El margen del conjunto
                # va en una clave APARTE.
                "margen_pct": round(100.0 * gan_mo / mo, 2) if mo > 0 else 0.0,
                "margen_total_pct": round(100.0 * gan_tot / costo, 2) if costo > 0 else 0.0,
                "mo_facturable": round(mo + gan_mo, 2), "ingreso": ingreso,
                "ganancia": gan_tot, "ganancia_mo": gan_mo,
                "ganancia_fija": round(fija, 2),
                "modelo": "rubro+fija" if fija > 0 else "rubro", "por_persona": detalle,
                # gente con horas y SIN ganancia puesta: su trabajo se facturaría a
                # costo y nadie lo notaría hasta ver el total (patrón v346)
                "sin_ganancia": [d["usuario"] for d in detalle
                                 if d["ganancia_hora"] <= 0 and d["horas"] > 0]}

    # ── Modelo viejo (respaldo): % sobre la mano de obra ──────────
    # ⚠️ Se conserva para que las obras anteriores a v360 NO cambien de cifra sin
    # que nadie lo pida. En cuanto se le ponga ganancia/hora, esa obra pasa al nuevo.
    mo  = E.labor_cost(pid, grupo)
    m   = project_margin(pid, grupo, prj)
    mo_fact = round(mo * (1 + m / 100.0), 2)
    costo   = round(mo + mat, 2)
    # ⚠️ La ganancia fija se suma también aquí: el caso que la motiva —un delivery sin
    # horas— vive justo en este modelo, donde `mo × (1+m)` no tiene sobre qué aplicarse
    # y el ingreso salía igual al costo. Con fija = 0 el resultado es IDÉNTICO al de
    # antes de v373, así que ninguna obra existente se mueve.
    ingreso = round(mo_fact + mat + fija, 2)
    return {"costo_mo": round(mo, 2), "materiales": round(mat, 2), "costo": costo,
            "margen_pct": m, "mo_facturable": mo_fact, "ingreso": ingreso,
            "margen_total_pct": round(100.0 * (ingreso - costo) / costo, 2) if costo > 0 else 0.0,
            "ganancia": round(ingreso - costo, 2),
            "ganancia_fija": round(fija, 2),
            "modelo": "margen+fija" if fija > 0 else "margen",
            "por_persona": [], "sin_ganancia": []}


def group_profitability(grupo: str) -> dict:
    """Rentabilidad de todos los proyectos del grupo. {rows:[...], totales:{...}}.

    Eficiente: reusa `expenses.group_expenses` (1 lectura cacheada que ya trae
    compras + mano de obra por proyecto) y aplica el margen por proyecto.
    """
    ge = E.group_expenses(grupo)
    # ⚠️ v360: esto REIMPLEMENTABA la fórmula del ingreso (`mo * (1 + m/100) + mat`).
    # Con el modelo por rubro dejó de coincidir: el detalle del proyecto decía
    # 3.628,80 y esta pantalla 3.475,68 — dos cifras de dinero para la misma obra.
    # Es el fallo de los cinco `_num` divergentes de v323, con importes. Ahora hay
    # UNA sola definición: `project_revenue`. No cuesta llamadas nuevas (lee de las
    # mismas cachés que `group_expenses`).
    prjs = {str(p.get("ID", "")): p
            for p in P.list_projects(grupo=grupo, incluir_archivados=True)}
    rows, t_costo, t_ing = [], 0.0, 0.0
    for r in ge["proyectos"]:
        # ⚠️ v422: una localización interna NO tiene rentabilidad — no se le factura a
        # nadie. Sin este corte saldría como una obra a **margen 0%** (con su aviso),
        # con pérdida garantizada, y arrastraría el total del grupo hacia abajo. Su
        # costo sí cuenta como estructura, y por eso `group_expenses` sí la trae.
        if r.get("interno"):
            continue
        pid = str(r["id"])
        rev = project_revenue(pid, grupo, prjs.get(pid))
        costo, ingreso = rev["costo"], rev["ingreso"]
        rows.append({"id": pid, "nombre": r["nombre"], "costo": costo,
                     "margen": rev["margen_pct"], "ingreso": ingreso,
                     "ganancia": rev["ganancia"],
                     # v360: qué modelo aplica («rubro» = importe por trabajador;
                     # «margen» = el % viejo). La pantalla lo dice para que un margen
                     # que ya no se teclea no parezca editable.
                     "modelo": rev.get("modelo", "margen"),
                     "sin_ganancia": rev.get("sin_ganancia", [])})
        t_costo += costo
        t_ing += ingreso
    return {"rows": rows,
            "totales": {"costo": round(t_costo, 2), "ingreso": round(t_ing, 2),
                        "ganancia": round(t_ing - t_costo, 2)}}


def _fecha(txt):
    """'YYYY-MM-DD…' → date, o None si no se puede leer."""
    from datetime import datetime
    s = str(txt or "").strip()[:10]
    if not s:
        return None
    for f in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, f).date()
        except Exception:
            pass
    return None


def _en_rango(txt, desde, hasta) -> bool:
    """¿Esa fecha cae en [desde, hasta]? Sin rango, todo entra.

    ⚠️ Una fila SIN fecha legible entra solo cuando NO hay periodo: con un periodo
    elegido, contarla sería inventarse en qué mes ocurrió — y en un P&L eso es
    cuadrar mal las cuentas, no un detalle de presentación.
    """
    if desde is None and hasta is None:
        return True
    d = _fecha(txt)
    if d is None:
        return False
    return (desde is None or d >= desde) and (hasta is None or d <= hasta)


def periodo_anterior(desde, hasta):
    """El periodo INMEDIATAMENTE anterior, de la misma duración (v341).

    Un administrador no pregunta «¿cuánto gané en agosto?», pregunta «¿voy mejor o
    peor que en julio?». El P&L tenía periodos pero ninguna comparación, así que la
    respuesta había que sacarla cambiando el filtro y acordándose del número.

    Se desplaza la ventana su propia duración hacia atrás: del 01/08 al 16/08 (16
    días) compara con del 16/07 al 31/07. ⚠️ Con «Todo» (sin fechas) no hay anterior
    posible — devuelve (None, None) y la UI no ofrece comparación.
    """
    if not desde or not hasta:
        return None, None
    from datetime import timedelta
    dias = (hasta - desde).days + 1
    return desde - timedelta(days=dias), desde - timedelta(days=1)


def variacion(actual, previo) -> dict:
    """{dif, pct, mejor} entre dos cifras. `pct` es None si no hay base con la que
    comparar (dividir por cero no es «infinito por ciento», es «no se puede decir»)."""
    a, p = _num(actual), _num(previo)
    dif = round(a - p, 2)
    pct = round(100.0 * dif / abs(p), 1) if abs(p) > 0.005 else None
    return {"dif": dif, "pct": pct, "mejor": dif > 0}


def pnl_comparado(grupo: str, desde=None, hasta=None) -> dict:
    """El P&L del periodo + el del anterior + la variación de cada cifra (v341).

    ⚠️ Cuesta 0 llamadas nuevas a Sheets: `pnl` lee de los mismos lectores cacheados
    (lote de v339), así que calcular el periodo anterior es solo volver a filtrar
    en memoria lo que ya está descargado.
    """
    act = pnl(grupo, desde, hasta)
    d0, h0 = periodo_anterior(desde, hasta)
    if d0 is None:
        return {"actual": act, "previo": None, "var": {}, "rango_previo": None}
    prev = pnl(grupo, d0, h0)
    campos = ("facturado", "cobrado", "costo_total", "costo_nomina", "compras", "ganancia")
    return {"actual": act, "previo": prev,
            "var": {k: variacion(act.get(k), prev.get(k)) for k in campos},
            "rango_previo": (d0, h0)}


def pnl(grupo: str, desde=None, hasta=None) -> dict:
    """Estado de resultados (P&L) del grupo: ingresos − costos = ganancia.

    Basado en lo REALMENTE facturado (facturas) y en las nóminas generadas + las
    compras — a diferencia de `group_profitability`, que es la estimación por margen.
    Además: cuentas por cobrar (facturas) y por pagar (nóminas). Imports perezosos
    de invoices/payroll para no crear ciclos (ambos dependen de este módulo).

      Ingresos    = Σ Total de facturas (no anuladas)
      Costo MO    = Σ Base + devengos + aportes de las nóminas (costo patronal)
      Costo total = Costo MO + compras (hoja Gastos)
      Ganancia    = Ingresos (facturado) − Costo total

    v309 — `desde`/`hasta` (date) acotan el periodo. Un P&L sin fechas decía
    "desde siempre", que no es un estado de resultados. Qué fecha manda en cada cosa:
      - factura → `Fecha` (cuándo se emitió)
      - nómina  → `PeriodoHasta` (el coste se devenga en el periodo que cierra,
        no el día que se pagó: si no, un pago tardío saltaría de mes)
      - compra  → `Fecha` del gasto
    ⚠️ Las compras se recorren de la hoja Gastos FILTRANDO por los proyectos del
    grupo — el mismo conjunto de filas que suma `group_expenses`, para que sin
    periodo el total salga idéntico al de antes (verificado en el test).
    """
    from core import invoices as INV
    from core import payroll as PR

    # ⚠️ v426 — LAS ANULADAS SE EXCLUYEN AQUÍ, A MANO.
    # Este comentario decía «excluye anuladas» y era FALSO: `list_facturas` NO filtra
    # por estado (a diferencia de `list_nominas`, que sí tiene `incluir_anuladas`).
    # O sea que el P&L contaba como ingreso las facturas ANULADAS — y anular es
    # justamente cómo se corrige una factura mal emitida. Medido en la hoja real: una
    # anulada de $1.100 con $400 cobrados inflaba `facturado`, `cobrado` y la
    # `ganancia` del grupo. Asimetría fea: los COSTOS anulados sí se excluían (las
    # nóminas), así que el error solo iba en la dirección de parecer más rentable.
    # ⚠️ No se arregla cambiando el DEFAULT de `list_facturas`: la lista de Facturas y
    # el detalle del cliente NECESITAN mostrarlas, y ocultarlas de raíz sería el fallo
    # de v340 (lo que se puede ocultar tiene que poder verse).
    facs = [f for f in INV.list_facturas(grupo)
            if str(f.get("Estado", "")).lower() != "anulada"
            and _en_rango(f.get("Fecha"), desde, hasta)]
    facturado = round(sum(_num(f.get("Total")) for f in facs), 2)
    cobrado   = round(sum(_num(f.get("Cobrado")) for f in facs), 2)
    vencido   = round(sum(_num(f.get("Total")) - _num(f.get("Cobrado"))
                          for f in facs if INV.estado_cobro(f) == "vencida"), 2)

    nbase = ndev = nap = por_pagar = pagado = 0.0
    for n in PR.list_nominas(grupo):                     # excluye anuladas
        if not _en_rango(n.get("PeriodoHasta"), desde, hasta):
            continue
        nbase += _num(n.get("Base"))
        for c in PR.conceptos_de(n):
            _tp = str(c.get("tipo", "")).lower()
            if _tp == "devengo":
                ndev += _num(c.get("monto"))
            elif _tp == "aporte":
                nap += _num(c.get("monto"))
        if str(n.get("Estado", "")).lower() == "pagada":
            pagado += _num(n.get("Neto"))
        else:
            por_pagar += _num(n.get("Neto"))
    costo_nomina = round(nbase + ndev + nap, 2)

    # Compras = TODAS las del grupo (v310, definición ÚNICA: la misma que usa la
    # pantalla de Gastos). Antes esto filtraba por los proyectos del grupo, y en v309
    # yo lo dejé incluyendo archivados mientras la pantalla de Gastos los excluía →
    # la misma pregunta tenía tres respuestas distintas en la app. Se cuenta por la
    # columna `Grupo`, así que una compra sin proyecto tampoco se pierde (la pantalla
    # la muestra aparte como huérfana).
    compras = round(sum(_num(r.get("Valor")) for r in E._records()
                        if str(r.get("Grupo", "")).strip() == str(grupo).strip()
                        and _en_rango(r.get("Fecha"), desde, hasta)), 2)
    costo_total = round(costo_nomina + compras, 2)
    ganancia = round(facturado - costo_total, 2)
    return {"facturado": facturado, "cobrado": cobrado,
            "por_cobrar": round(facturado - cobrado, 2), "vencido": vencido,
            "costo_nomina": costo_nomina, "compras": compras, "costo_total": costo_total,
            "ganancia": ganancia, "por_pagar": round(por_pagar, 2), "pagado": round(pagado, 2),
            # v309: de dónde sale, para el desglose de la pantalla
            "por_cliente": _por_cliente(facs)}


def conciliacion_mo(grupo: str, desde=None, hasta=None) -> dict:
    """El puente entre **lo que pagas** y **lo que cargas a las obras** (v313).

    Modelo del negocio (fijado por el usuario): se paga **toda la jornada fichada**,
    esté o no imputada a un proyecto, **más los aportes de ley**; y al cliente se le
    cobran **las horas imputadas a su obra** por la tarifa, más un factor de ganancia.
    Las dos cifras son correctas y responden preguntas distintas — el problema era que
    no había forma de ver por qué no coinciden. Esta es la cadena, y CIERRA:

        cargado a obras (horas de proyecto × tarifa)
        − horas cobradas que no se pagaron   (imputadas SIN jornada abierta)
        + horas pagadas que no se cargaron   (jornada sin imputar: traslados, espera)
        = base a pagar
        + aportes de ley (super)
        = costo real de la mano de obra

    ⚠️ `sin_explicar` NO es decorado: si alguien editó a mano una nómina, la cadena
    deja de cerrar y hay que DECIRLO en vez de cuadrar el número a la fuerza.
    """
    from core import payroll as PR

    hp = timeclock.jornada_y_proyecto(grupo, desde, hasta)
    rates = auth.rate_map(grupo)

    # v325: quien ya NO está dado de alta no es un «falta ponerle tarifa» — no hay
    # fila donde ponerla. Se cuenta aparte para que el pendiente siga siendo
    # accionable y no arrastre gente que nadie puede arreglar.
    conocidas = auth.claves_conocidas()
    cargado = cobrado_no_pagado = pagado_no_cargado = interno = 0.0
    sin_tarifa, de_baja = [], []
    for clave, h in hp.items():
        _tar = _num(rates.get(clave, 0))
        cargado += h["proyecto"] * _tar
        # v422: el trabajo en oficina/almacén se paga y NO se le carga a ningún
        # cliente. Queda dentro de `pagado_no_cargado` (que es lo que es) y además se
        # devuelve suelto, para poder decir a QUÉ se fue ese hueco en vez de dejarlo
        # como un residuo anónimo — hoy son 172 h en el grupo real.
        interno += h.get("interno", 0.0) * _tar
        _d = (h["proyecto"] - h["jornada"]) * _tar
        if _d > 0:
            cobrado_no_pagado += _d
        else:
            pagado_no_cargado += -_d
        if _tar <= 0 and (h["jornada"] > 0 or h["proyecto"] > 0):
            _vivo = (not conocidas or clave in conocidas
                     or str(h.get("nombre", "")) in conocidas)
            (sin_tarifa if _vivo else de_baja).append(h["nombre"])

    # Lo REALMENTE liquidado en nóminas del periodo (por `PeriodoHasta`, como el P&L)
    base_nom = aportes = ausencias = 0.0
    for n in PR.list_nominas(grupo):
        if not _en_rango(n.get("PeriodoHasta"), desde, hasta):
            continue
        base_nom += _num(n.get("Base"))
        for c in PR.conceptos_de(n):
            _t = str(c.get("tipo", "")).lower()
            if _t == "aporte":
                aportes += _num(c.get("monto"))
            # v430: vacaciones y bajas pagadas. Van como DEVENGO y NO en `Base`
            # (`Base` es lo trabajado, que es contra lo que se contrasta la jornada
            # fichada), así que sin contarlas aquí el «costo real» las perdería —
            # y es dinero que sale de caja igual que el resto.
            elif _t == "devengo" and str(c.get("origen", "")) == "ausencia":
                ausencias += _num(c.get("monto"))

    base_teorica = cargado - cobrado_no_pagado + pagado_no_cargado
    return {
        "cargado":            round(cargado, 2),
        # v422: la parte de `pagado_no_cargado` que SÍ tiene explicación: estructura.
        "interno":            round(interno, 2),
        "cobrado_no_pagado":  round(cobrado_no_pagado, 2),
        "pagado_no_cargado":  round(pagado_no_cargado, 2),
        "base_teorica":       round(base_teorica, 2),
        "base_nomina":        round(base_nom, 2),
        "ausencias":          round(ausencias, 2),
        "aportes":            round(aportes, 2),
        "costo_real":         round(base_nom + ausencias + aportes, 2),
        # lo que la cadena no explica: nóminas editadas a mano, o trabajo aún sin nómina
        "sin_explicar":       round(base_teorica - base_nom, 2),
        "sin_tarifa":         sorted(set(sin_tarifa)),
        "de_baja":            sorted(set(de_baja)),
    }


def resultado_por_proyecto(grupo: str) -> list:
    """Cada obra: lo facturado contra lo que costó. `[{id, nombre, facturado, mo,
    compras, costo, resultado, margen}]`, solo las que tienen algo.

    ⚠️ **ACUMULADO a propósito: ignora el selector de periodo.** Casar un ingreso con
    los costos que lo produjeron es justo lo que un P&L por mes natural NO puede hacer:
    en el grupo real la factura es del 09/08 y las compras del 28/07, así que «Este mes»
    daba una ganancia de $1.710 cuando la obra entera dejó $210,42. Una obra se mide de
    principio a fin, no por meses.

    ⚠️ El costo aquí es el **cargado a la obra** (horas imputadas × tarifa + compras),
    NO lo que sale de caja: los aportes de ley y las horas sin imputar no son de ninguna
    obra en concreto — los cubre el margen. Ver `conciliacion_mo`.
    """
    from core import invoices as INV

    fac = INV.facturado_por_proyecto(grupo)
    out = []
    for p in P.list_projects(grupo=grupo, incluir_archivados=True):
        pid = str(p.get("ID", ""))
        f = _num(fac.get(pid, 0))
        mo = _num(E.labor_cost(pid, grupo))
        co = _num(E.project_expenses(pid).get("total"))
        if f <= 0 and mo <= 0 and co <= 0:
            continue                       # obra sin movimiento: no aporta nada al cuadro
        costo = round(mo + co, 2)
        out.append({"id": pid, "nombre": str(p.get("Nombre", "")),
                    "facturado": round(f, 2), "mo": round(mo, 2), "compras": round(co, 2),
                    "costo": costo, "resultado": round(f - costo, 2),
                    "margen": (round(100.0 * (f - costo) / f, 1) if f > 0 else None)})
    return sorted(out, key=lambda r: -r["facturado"])


def sin_facturar(grupo: str) -> list:
    """`[(nombre, importe)]` de obras con trabajo hecho y aún NO facturado.

    Es dinero ganado que no se ha pedido. No estaba en ninguna pantalla: había que
    entrar a crear una factura para enterarse.
    """
    # ⚠️ v397: delega en `invoices.pendiente_por_proyecto`, que es LA definición del
    # pendiente por obra. Antes repetía el bucle aquí y la cartera habría sido una
    # tercera copia — el patrón que causó los cinco `_num` divergentes de v323.
    from core import invoices as INV
    _pend = INV.pendiente_por_proyecto(grupo)
    _nom = {str(p.get("ID", "")): str(p.get("Nombre", ""))
            for p in P.list_projects(grupo=grupo, incluir_archivados=True)}
    out = [(_nom.get(pid, pid), v) for pid, v in _pend.items()]
    return sorted(out, key=lambda x: -x[1])


def _por_cliente(facs) -> list:
    """[(cliente, facturado)] ordenado desc. Del lado del INGRESO se puede desglosar
    honestamente porque la factura lleva cliente.

    ⚠️ Por el lado del COSTO no se puede repartir igual: las nóminas son por PERSONA
    y no por obra, así que un "ganancia por proyecto" saldría inventado. Por eso el
    desglose de costo que se muestra es su composición (nóminas vs compras) y no un
    reparto por proyecto.
    """
    agg = {}
    for f in facs:
        k = str(f.get("ClienteNombre", "")).strip() or "(sin cliente)"
        agg[k] = agg.get(k, 0.0) + _num(f.get("Total"))
    return sorted(((k, round(v, 2)) for k, v in agg.items() if v), key=lambda x: -x[1])
