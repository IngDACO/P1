# -*- coding: utf-8 -*-
"""v701 · Ciclo 7 → las cifras (H11, H19, H12, H13, H4): el coste al terminar, el beneficio estimado de una obra
cotizada, la variación entre periodos y lo cobrado por obra del asistente. Sin red ni escrituras: funciones puras,
sustitutos para lo que lee la hoja (guardados y devueltos al acabar, trampa 48) y un AppTest de «How much you make».

Los números son los de C7 (PRJ-0048) el 23/11/2026, al 11 %: $39,571 gastados ($39,000 el ascensor), $472 de mano de
obra, presupuesto $61,410 (el costo cotizado), $73,692 de precio, $52,610 de material y $8,800 de servicio cotizados.
"""
import ast
import json
import os
import sys

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:900]))
    if not cond:
        FALLOS.append(nombre)


from core import expenses as E, finance as F, projects as P, chat_tools as CT   # noqa: E402
from core import projects_ui as PU                                              # noqa: E402

C7 = {"total": 39571.4, "mano_obra": 472.0, "compras": 39099.4, "comprometido": 0.0, "presupuesto": 61410.0}
DESG = {"servicio": 8800.0, "material": 52610.0}

print("A. El coste al terminar (H19)")
r = E.costo_al_terminar(C7, 11, DESG)
chk("C7 cotizada al 11 %: mano de obra al ritmo (472×100/11) + el material cotizado (52,610) = 56,900.91",
    r["proyectado"] is not None and abs(r["proyectado"] - (472 * 100 / 11 + 52610)) < 0.02 and r["metodo"] == "cotizada", r)
chk("…NO la regla de tres de antes (39,571 × 100 / 11 = 359,740)", r["proyectado"] and r["proyectado"] < 100000, r)
r2 = E.costo_al_terminar(dict(C7, compras=60000.0, total=60472.0), 50, DESG)
chk("lo comprado de más que lo cotizado cuenta (60,000 > 52,610): 944 + 60,000",
    abs(r2["proyectado"] - (472 * 2 + 60000)) < 0.02, r2)
r3 = E.costo_al_terminar(dict(C7, comprometido=1500.0), 11, None)
chk("sin cotización: mano de obra al ritmo + lo comprado + lo pedido, SIN extrapolar las compras (ni suelo de presupuesto)",
    abs(r3["proyectado"] - (472 * 100 / 11 + 39099.4 + 1500)) < 0.02 and r3["metodo"] == "sin_cotizacion", r3)
chk("terminada (100 %): lo real", E.costo_al_terminar(C7, 100, DESG) == {"proyectado": 39571.4, "metodo": "real"})
chk("sin avance: sin proyección", E.costo_al_terminar(C7, 0, DESG)["proyectado"] is None)
chk("el umbral es el de Costs (v697): 10 %", E.AVANCE_MIN_PROYECCION == PU.AVANCE_MIN_PROYECCION == 10)


def _src_fn(ruta, nombre):
    arbol = ast.parse(open(ruta, encoding="utf-8").read())
    for n in ast.walk(arbol):
        if isinstance(n, ast.FunctionDef) and n.name == nombre:
            return ast.get_source_segment(open(ruta, encoding="utf-8").read(), n)
    return ""


_ge = _src_fn("core/expenses.py", "group_expenses")
chk("la vista de gastos del grupo usa la MISMA definición", "costo_al_terminar(" in _ge and "* 100.0 / av" not in _ge, _ge[:200])
_cmp = _src_fn("core/quotes.py", "comparacion")
chk("«Quoted vs. actual» también, y desde el 10 % como Costs",
    "costo_al_terminar(" in _cmp and "AVANCE_MIN_PROYECCION" in _cmp and "* 100.0 / av" not in _cmp, _cmp[-600:])

print("\nB. El beneficio estimado de una obra cotizada (H11)")
_REAL = {k: getattr(m, k) for m, ks in ((E, ("project_expenses", "labor_cost", "project_cost", "desglose_cotizado")),
                                        (P, ("es_cancelada", "ganancia_hora", "ganancia_fija", "get_project")))
         for k in ks}
from core import quotes as Q, claims as CL                                     # noqa: E402
_RQ, _RCL = Q.cotizacion_de_proyecto, CL.valor_variaciones
try:
    E.project_expenses = lambda pid: {"total": 39099.4}
    E.labor_cost = lambda pid, grupo: 472.0
    E.project_cost = lambda pid, grupo, comprometido=None: dict(C7)
    E.desglose_cotizado = lambda pid: dict(DESG)
    P.es_cancelada = lambda p: False
    P.ganancia_hora = lambda pid, prj=None: {}
    P.ganancia_fija = lambda pid, prj=None: 0.0
    Q.cotizacion_de_proyecto = lambda pid: {"ID": "COT-0018", "Number": "0009", "Version": "2", "Subtotal": "73692"}
    CL.valor_variaciones = lambda pid: 0.0

    def rev(av):
        return F.project_revenue("PRJ-0048", "cliente1", {"ID": "PRJ-0048", "Progress": str(av)})
    r0, r11, r100 = rev(0), rev(11), rev(100)
    chk("al 0 %: contra el costo COTIZADO (presupuesto 61,410) → 12,282, no 73,692 − 39,571 = 34,121",
        abs(r0["ganancia"] - 12282) < 0.01 and r0["ganancia_base"] == "presupuesto", (r0["ganancia"], r0.get("ganancia_base")))
    chk("al 11 %: contra el coste al terminar (56,900.91) → 16,791.09",
        abs(r11["ganancia"] - (73692 - (472 * 100 / 11 + 52610))) < 0.02 and r11["ganancia_base"] == "proyectada",
        (r11["ganancia"], r11.get("ganancia_base")))
    chk("terminada: contra lo real (73,692 − 39,571.40)", abs(r100["ganancia"] - (73692 - 39571.4)) < 0.01
        and r100["ganancia_base"] == "real", (r100["ganancia"], r100.get("ganancia_base")))
    chk("«costo» sigue siendo lo GASTADO (lo leen las demás pantallas)", r11["costo"] == 39571.4, r11["costo"])
    chk("…y lleva el número que ve el usuario (No. 0009 v2), no solo el ID interno",
        r11.get("cotizacion_numero") == "0009" and r11.get("cotizacion_version") == 2, r11)
finally:
    for k, v in _REAL.items():
        setattr(E if hasattr(E, k) and k in ("project_expenses", "labor_cost", "project_cost", "desglose_cotizado") else P, k, v)
    Q.cotizacion_de_proyecto, CL.valor_variaciones = _RQ, _RCL
_gp = _src_fn("core/finance.py", "group_profitability")
chk("el total de Profitability es la SUMA de las ganancias de cada obra (no ingreso − gastado)",
    'sum(_num(x["ganancia"]) for x in rows)' in _gp and "t_ing - t_costo" not in _gp, _gp[-300:])

print("\nC. La variación entre periodos (H12)")
v1 = F.variacion(33592, 250)
chk("$33,592 contra $250: en dinero (+$33,342), sin «13337%»", v1["en_dinero"] and v1["pct"] is None and v1["dif"] == 33342, v1)
v2 = F.variacion(-48506, 248)
chk("un beneficio que cambia de signo: en dinero", v2["en_dinero"] and v2["pct"] is None, v2)
v3 = F.variacion(120, 100)
chk("una base normal sigue en %: +20 %", not v3["en_dinero"] and v3["pct"] == 20.0, v3)
_kc = PU._kpi_card("Income", "$33,592", var=v1)
chk("la tarjeta dice «▲ $33,342 vs previous»", "▲ $33,342 vs previous" in _kc and "%" not in _kc.split("vs previous")[0][-12:], _kc)
_src_pu = open("core/projects_ui.py", encoding="utf-8").read()
chk("…y el Summary igual (las dos tarjetas que pintan «vs previous»)", _src_pu.count('t("{f} {d} vs previous")') == 2,
    _src_pu.count('t("{f} {d} vs previous")'))

print("\nD. Lo cobrado por obra, para el asistente (H13)")
f1 = {"Number": "0007", "Subtotal": "20811.6", "Total": "22892.76", "Collected": "10050",
      "LinesJSON": json.dumps([{"concepto": "Deposit 30%", "importe": 20811.6, "proyecto_id": "PRJ-0048"}])}
a1 = CT._factura_de_obra(f1, "PRJ-0048")
chk("la 0007 es entera de C7: «this_job_collected» 10,050 y «only_this_job»", a1["this_job_collected"] == 10050
    and a1["only_this_job"] is True, a1)
f2 = {"Number": "0099", "Subtotal": "400", "Total": "440", "Collected": "200",
      "LinesJSON": json.dumps([{"importe": 100, "proyecto_id": "A"}, {"importe": 300, "proyecto_id": "B"}])}
a2 = CT._factura_de_obra(f2, "A")
chk("una factura de dos obras: la parte de A (100 de 400) de lo cobrado (200) = 50", a2["this_job_collected"] == 50
    and a2["only_this_job"] is False, a2)
_din = _src_fn("core/chat_tools.py", "_dinero")
chk("get_money de una obra dice contra qué sale el beneficio, el coste al terminar y lo cobrado de la obra",
    all(k in _din for k in ('"estimated_profit_is_on"', '"cost_at_completion"', '"collected_for_this_job"')), _din[:300])

print("\nE. «How much you make on this job» de una obra cotizada (H4), con AppTest")
from streamlit.testing.v1 import AppTest                                       # noqa: E402
GUION = r'''
import streamlit as st
from core import projects_ui as PU, finance as F, expenses as E, projects as P
st.session_state.setdefault("auth", {"usuario": "Admin2", "rol": "administrator", "grupo": "cliente1"})
F.project_revenue = lambda pid, grupo=None, prj=None: {
    "modelo": "cotizado", "cotizacion": "COT-0018", "cotizacion_numero": "0009", "cotizacion_version": 2,
    "ingreso": 73692.0, "ganancia": 16791.09, "margen_pct": 29.51, "costo": 39571.4, "costo_estimado": 56900.91,
    "ganancia_base": "proyectada", "fija_ignorada": 0.0, "sin_ganancia": []}
E.labor_breakdown = lambda pid, grupo: {"items": [{"usuario": "campo000", "horas": 8.6, "costo": 472.0}]}
P.ganancia_hora = lambda pid, prj=None: {}
P.ganancia_fija = lambda pid, prj=None: 0.0
PU._ganancia_section("PRJ-0048", "cliente1")
'''
_RPR, _RLB, _RGH, _RGF = F.project_revenue, E.labor_breakdown, P.ganancia_hora, P.ganancia_fija
try:
    at = AppTest.from_string(GUION, default_timeout=60).run()
    _txt = " ".join(x.value for x in at.success)
    chk("dice «quote No. 0009 v2», el precio y la ganancia esperada, no «COT-0018» ni «The 0% follows»",
        "No. 0009 v2" in _txt and "$73,692" in _txt.replace("\\$", "$") and "16,791" in _txt
        and "COT-0018" not in _txt and "follows from that price" not in _txt, _txt)
    chk("…y contra qué costo sale («cost expected at completion, $56,901»)",
        "cost expected at completion" in _txt and "56,901" in _txt, _txt)
    _ni = [x.label for x in at.number_input]
    chk("con precio pactado ya no ofrece «Fixed profit» (no se usa)", not any("Fixed profit" in s for s in _ni), _ni)
    chk("ni la tabla de ganancia por hora", len(at.get("arrow_data_frame")) == 0 and not at.exception,
        [str(e) for e in at.exception][:2])
finally:
    F.project_revenue, E.labor_breakdown, P.ganancia_hora, P.ganancia_fija = _RPR, _RLB, _RGH, _RGF

print()
print("verif_v701: %d FALLOS" % len(FALLOS) if FALLOS else "verif_v701: TODO OK")
sys.exit(1 if FALLOS else 0)
