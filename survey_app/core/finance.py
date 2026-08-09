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


def pnl(grupo: str) -> dict:
    """Estado de resultados (P&L) del grupo: ingresos − costos = ganancia.

    Basado en lo REALMENTE facturado (facturas) y en las nóminas generadas + las
    compras — a diferencia de `group_profitability`, que es la estimación por margen.
    Además: cuentas por cobrar (facturas) y por pagar (nóminas). Imports perezosos
    de invoices/payroll para no crear ciclos (ambos dependen de este módulo).

      Ingresos    = Σ Total de facturas (no anuladas)
      Costo MO    = Σ Base + devengos + aportes de las nóminas (costo patronal)
      Costo total = Costo MO + compras (hoja Gastos)
      Ganancia    = Ingresos (facturado) − Costo total
    """
    from core import invoices as INV
    from core import payroll as PR

    facs = INV.list_facturas(grupo)                      # excluye anuladas
    facturado = round(sum(_num(f.get("Total")) for f in facs), 2)
    cobrado   = round(sum(_num(f.get("Cobrado")) for f in facs), 2)
    vencido   = round(sum(_num(f.get("Total")) - _num(f.get("Cobrado"))
                          for f in facs if INV.estado_cobro(f) == "vencida"), 2)

    nbase = ndev = nap = por_pagar = pagado = 0.0
    for n in PR.list_nominas(grupo):                     # excluye anuladas
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

    compras = round(sum(_num(r.get("compras")) for r in E.group_expenses(grupo)["proyectos"]), 2)
    costo_total = round(costo_nomina + compras, 2)
    ganancia = round(facturado - costo_total, 2)
    return {"facturado": facturado, "cobrado": cobrado,
            "por_cobrar": round(facturado - cobrado, 2), "vencido": vencido,
            "costo_nomina": costo_nomina, "compras": compras, "costo_total": costo_total,
            "ganancia": ganancia, "por_pagar": round(por_pagar, 2), "pagado": round(pagado, 2)}
