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
from core import auth
from core import expenses as E
from core import projects as P


def _num(v, d=0.0) -> float:
    try:
        return float(str(v).replace(",", "."))
    except Exception:
        return d


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
    mo  = E.labor_cost(pid, grupo)
    mat = E.project_expenses(pid)["total"]
    m   = project_margin(pid, grupo, prj)
    mo_fact = round(mo * (1 + m / 100.0), 2)
    costo   = round(mo + mat, 2)
    ingreso = round(mo_fact + mat, 2)
    return {"costo_mo": round(mo, 2), "materiales": round(mat, 2), "costo": costo,
            "margen_pct": m, "mo_facturable": mo_fact, "ingreso": ingreso,
            "ganancia": round(ingreso - costo, 2)}


def group_profitability(grupo: str) -> dict:
    """Rentabilidad de todos los proyectos del grupo. {rows:[...], totales:{...}}.

    Eficiente: reusa `expenses.group_expenses` (1 lectura cacheada que ya trae
    compras + mano de obra por proyecto) y aplica el margen por proyecto.
    """
    ge = E.group_expenses(grupo)
    default_m = auth.group_margin_default(grupo)
    mmap = {str(p.get("ID", "")): str(p.get("MargenMO", "")).strip()
            for p in P.list_projects(grupo=grupo)}
    rows, t_costo, t_ing = [], 0.0, 0.0
    for r in ge["proyectos"]:
        pid = str(r["id"])
        mo, mat = _num(r["mano_obra"]), _num(r["compras"])
        raw = mmap.get(pid, "")
        m = _num(raw) if raw != "" else default_m
        costo   = mo + mat
        ingreso = mo * (1 + m / 100.0) + mat
        rows.append({"id": pid, "nombre": r["nombre"], "costo": round(costo, 2),
                     "margen": m, "ingreso": round(ingreso, 2),
                     "ganancia": round(ingreso - costo, 2)})
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

    facs = [f for f in INV.list_facturas(grupo)          # excluye anuladas
            if _en_rango(f.get("Fecha"), desde, hasta)]
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
            t = str(c.get("tipo", "")).lower()
            if t == "devengo":
                ndev += _num(c.get("monto"))
            elif t == "aporte":
                nap += _num(c.get("monto"))
        if str(n.get("Estado", "")).lower() == "pagada":
            pagado += _num(n.get("Neto"))
        else:
            por_pagar += _num(n.get("Neto"))
    costo_nomina = round(nbase + ndev + nap, 2)

    # Compras: MISMO conjunto de filas que suma `group_expenses` (las de proyectos de
    # este grupo), pero fila a fila para poder filtrar por fecha. Sin periodo el total
    # es identico al anterior — está comprobado en el test, no supuesto.
    _pids = {str(p.get("ID", "")) for p in P.list_projects(grupo=grupo,
                                                           incluir_archivados=True)}
    compras = round(sum(_num(r.get("Valor")) for r in E._records()
                        if str(r.get("ProyectoID", "")) in _pids
                        and _en_rango(r.get("Fecha"), desde, hasta)), 2)
    costo_total = round(costo_nomina + compras, 2)
    ganancia = round(facturado - costo_total, 2)
    return {"facturado": facturado, "cobrado": cobrado,
            "por_cobrar": round(facturado - cobrado, 2), "vencido": vencido,
            "costo_nomina": costo_nomina, "compras": compras, "costo_total": costo_total,
            "ganancia": ganancia, "por_pagar": round(por_pagar, 2), "pagado": round(pagado, 2),
            # v309: de dónde sale, para el desglose de la pantalla
            "por_cliente": _por_cliente(facs)}


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
