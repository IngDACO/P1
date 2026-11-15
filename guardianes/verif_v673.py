# -*- coding: utf-8 -*-
"""v673 · Asistente y fichas (ciclo 2, mejoras 5/5) + lo visto verificando v672.

H1  `get_money`: lo facturado y cobrado de una obra (con cada factura), y por cliente de siempre, con lo cobrado en
    facturas anuladas aparte; y la regla de no explicar una cifra con causas que no están en los datos.
H2  una obra terminada, cancelada o en pausa no pide Pre-Start ni false car.
H3  una obra terminada dice «Finished on <fecha del 100 %>» (ficha y asistente); y una cancelada o en pausa no
    proyecta en su Status (visto verificando v672).
H4  la ficha del cliente cuenta como activas las mismas obras que Home (`projects.es_activa`).
H17 «Already assigned to another project» solo con asignaciones vigentes.
v672 · «4» (una cifra) se busca: la pantalla del buscador lo paraba.

Nada sale a la red ni escribe: funciones reales con sustitutos; AppTest de las pantallas.
"""
import ast
import io
import os
import sys
from datetime import date

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:900]))
    if not cond:
        FALLOS.append(nombre)


def sec(t_):
    print(f"\n{'─' * 70}\n{t_}\n{'─' * 70}")


def src(rel):
    return io.open(os.path.join(RAIZ, rel), encoding="utf-8").read()


def funcion(rel, nombre):
    s = src(rel)
    for n in ast.walk(ast.parse(s)):
        if isinstance(n, ast.FunctionDef) and n.name == nombre:
            return n, ast.get_source_segment(s, n) or ""
    return None, ""


def _sustituir(obj, **kw):
    viejo = {k: getattr(obj, k) for k in kw}
    for k, v in kw.items():
        setattr(obj, k, v)
    return lambda: [setattr(obj, k, v) for k, v in viejo.items()]


import json                                                                # noqa: E402
from streamlit.testing.v1 import AppTest                                   # noqa: E402
from core import chat_tools as CT                                          # noqa: E402
from core import projects as P                                             # noqa: E402
from core import invoices as INV                                           # noqa: E402
from core import expenses as E                                             # noqa: E402
from core import finance as F                                              # noqa: E402
from core import clock                                                     # noqa: E402

# los originales: los guiones de AppTest corren en ESTE proceso y dejan sus sustitutos puestos (trampa 48)
_LIST_ACTS = P.list_activities


def _fac(fid, num, cli, tot, cob, lineas, status="emitida", venc="2026-12-01"):
    return {"ID": fid, "Number": num, "ClientName": cli, "Date": "2026-10-20", "ExpiryDate": venc, "Total": str(tot),
            "Collected": str(cob), "Status": status, "LinesJSON": json.dumps(lineas)}


_FACS = [_fac("F1", "0001", "C1", 1278.0, 1278.0, [{"concepto": "a", "importe": 1162.0, "proyecto_id": "PRJ-39"}]),
         # ⚠️ con DOS obras en la misma factura: si no, «lo de esta obra» y «la factura entera» dan lo mismo (escapó)
         _fac("F2", "0002", "C1", 12780.0, 12780.0, [{"concepto": "b", "importe": 10618.18, "proyecto_id": "PRJ-39"},
                                                     {"concepto": "b2", "importe": 1000.0, "proyecto_id": "PRJ-41"}]),
         _fac("F6", "0006", "C1", 250.0, 0.0, [{"concepto": "c", "importe": 250.0, "proyecto_id": "PRJ-40"}],
              venc="2026-10-27"),
         _fac("F3", "0003", "C2", 6276.05, 3000.0, [{"concepto": "d", "importe": 5705.5, "proyecto_id": "PRJ-43"}],
              status="anulada")]
_CTX = {"grupo": "G", "usuario": "admin2", "nombre": "Bobo", "rol": "administrator"}

# ═════════════════════════════════════════════════════════════════════════════
sec("1. get_money: lo facturado y cobrado, por obra y por cliente (H1)")
_PRJ = {"ID": "PRJ-39", "Name": "Lift 1", "Group": "G", "Status": "Completed", "Progress": "100"}
_d = [_sustituir(CT, _obra=lambda e, c: dict(_PRJ), _mis_obras=lambda c: [dict(_PRJ)]),
      _sustituir(INV, list_facturas=lambda *a, **k: [dict(x) for x in _FACS], pendiente_de_facturar=lambda *a, **k: 0.0,
                 pendiente_por_proyecto=lambda *a, **k: {}),
      _sustituir(E, project_cost=lambda *a, **k: {"presupuesto": 0, "total": 2000, "compras": 1500, "mano_obra": 500,
                                                  "comprometido": 0, "pct": 0, "over": False, "over_comp": False},
                 over_budget=lambda *a, **k: []),
      _sustituir(F, project_revenue=lambda *a, **k: {"ingreso": 12780.18, "ganancia": 10780.18},
                 pnl=lambda *a, **k: {"facturado": 0, "ingresos": 0, "impuesto": 0, "cobrado": 0, "por_cobrar": 0,
                                      "vencido": 0, "costo_nomina": 0, "compras": 0, "costo_total": 0, "ganancia": 0,
                                      "por_pagar": 0},
                 group_profitability=lambda *a, **k: {"rows": [], "totales": {}}),
      _sustituir(clock, today=lambda *a, **k: date(2026, 11, 16))]
try:
    _o = CT._dinero({"project_id": "PRJ-39"}, _CTX)
    _g = CT._dinero({}, _CTX)
finally:
    for x in _d:
        x()
chk("la obra dice lo FACTURADO (sin impuesto), solo SUS líneas: 11,780.18 (era solo «pending 0»)",
    _o.get("invoiced_ex_tax") == 11780.18,
    _o.get("invoiced_ex_tax"))
_nums = [f["number"] for f in _o.get("invoices", [])]
chk("…y cada factura suya, con su estado y lo cobrado (0001 y 0002, no la 0006 de otra obra)",
    _nums == ["0001", "0002"] and all(f["status"] == "cobrada" for f in _o["invoices"])
    and _o["invoices"][1]["this_job_lines_ex_tax"] == 10618.18 and _o["invoices"][1]["invoice_collected"] == 12780.0,
    _o.get("invoices"))
chk("…y la regla de leer: no explicar con causas que no están", "Do not explain a figure with a cause" in
    str(_o.get("how_to_read", "")), _o.get("how_to_read"))
_cli = {c["client"]: c for c in _g.get("by_client_all_time", [])}
chk("por cliente: C1 con 3 facturas, $14,308 facturados y $14,058 cobrados (supuso «if 0006 is the only one»)",
    _cli.get("C1", {}).get("invoices") == 3 and _cli["C1"]["invoiced_incl_tax"] == 14308.0
    and _cli["C1"]["collected"] == 14058.0, _cli.get("C1"))
chk("…con lo que falta y lo vencido (la 0006, $250)", _cli.get("C1", {}).get("to_collect") == 250.0
    and _cli["C1"]["overdue"] == 250.0, _cli.get("C1"))
chk("…y lo cobrado en una ANULADA va aparte, sin contar como facturado ($3,000 de C2)",
    _cli.get("C2", {}).get("collected_on_voided_invoices") == 3000.0 and _cli["C2"]["invoices"] == 0
    and _cli["C2"]["invoiced_incl_tax"] == 0.0, _cli.get("C2"))
chk("…y la empresa también lleva la regla de leer", "how_to_read" in _g)
_desc = next((x["description"] for x in CT.LECTURA_OFICINA if x["name"] == "get_money"), "")
chk("la descripción de la herramienta lo anuncia (lo que pide el modelo depende de ella, trampa 52)",
    "what was invoiced (and each invoice with its status" in _desc and "by client (all time)" in _desc, _desc)

# ═════════════════════════════════════════════════════════════════════════════
sec("2. Pre-Start y false car: no en una obra terminada, cancelada o en pausa (H2)")
from core import prestart as PS                                            # noqa: E402
from core import falsecar as FC                                            # noqa: E402
_d = [_sustituir(PS, hecho_hoy=lambda *a, **k: False, pendiente_de_firma=lambda *a, **k: False),
      _sustituir(FC, activo=lambda *a, **k: True, hecho_hoy=lambda *a, **k: False, pendiente_hoy=lambda *a, **k: FC.HACER),
      _sustituir(clock, today=lambda *a, **k: date(2026, 11, 16))]
_campo = {"grupo": "G", "usuario": "campo000", "nombre": "Ana", "rol": "field"}
try:
    _r = {k: CT._estado_del_dia(p, "PRJ-1", c) for k, p, c in [
        ("hecha", {"Status": "Completed", "Progress": "100"}, _CTX),
        ("al100", {"Status": "In progress", "Progress": "100"}, _campo),
        ("cancelada", {"Status": "Cancelled", "Progress": "10"}, _CTX),
        ("pausa", {"Status": "On hold", "Progress": "40"}, _campo),
        ("viva_of", {"Status": "In progress", "Progress": "40"}, _CTX),
        ("viva_campo", {"Status": "In progress", "Progress": "40"}, _campo)]}
finally:
    for x in _d:
        x()
chk("terminada (Completed o al 100 %), cancelada y en pausa: nada que reclamar, y por qué",
    all(_r[k]["pre_start"] == "not_required" and _r[k]["false_car_check"] == "not_required" and _r[k].get("why")
        for k in ("hecha", "al100", "cancelada", "pausa")), _r)
chk("…«the job is complete» / «the job is cancelled»", _r["hecha"]["why"] == "the job is complete"
    and _r["cancelada"]["why"] == "the job is cancelled", (_r["hecha"], _r["cancelada"]))
chk("una obra viva sigue pidiéndolo (oficina y campo)", _r["viva_of"]["pre_start"] == "missing"
    and _r["viva_campo"]["pre_start"] == "missing" and _r["viva_campo"]["false_car_check"] == "missing", _r)

# ═════════════════════════════════════════════════════════════════════════════
sec("3. «Finished on» en una obra terminada (H3)")


def _act(o, av, fin=""):
    return {"ProjectID": "PRJ-9", "Order": str(o), "Name": f"Act {o}", "DurationDays": "5", "Weight": "50",
            "Progress": str(av), "ActualStartDate": "2026-11-02" if av else "", "ActualEndDate": fin, "Note": ""}


chk("fecha_terminada: la ÚLTIMA fecha de fin real, si todas están al 100 %",
    P.fecha_terminada("x", [_act(1, 100, "2026-11-10"), _act(2, 100, "2026-11-12")]) == date(2026, 11, 12))
chk("…None si alguna no está acabada, o si no hay fechas",
    P.fecha_terminada("x", [_act(1, 100, "2026-11-10"), _act(2, 60)]) is None
    and P.fecha_terminada("x", [_act(1, 100)]) is None and P.fecha_terminada("x", []) is None)
chk("es_completada: al 100 % o «Completed»", P.es_completada({"Progress": "100"}) and P.es_completada({"Status": "Completed"})
    and not P.es_completada({"Status": "In progress", "Progress": "99"}))
_d = [_sustituir(P, list_activities=lambda pid: [_act(1, 100, "2026-11-10"), _act(2, 100, "2026-11-12")])]
try:
    _f1 = P.fin_de_obra({"ID": "PRJ-9", "Status": "Completed", "Progress": "100", "EndDateEst": "2026-12-16"})
    _f2 = P.fin_de_obra({"ID": "PRJ-9", "Status": "In progress", "Progress": "40", "EndDateEst": "2026-12-16"})
finally:
    for x in _d:
        x()
chk("fin_de_obra: terminada → «finished_on 12/11/2026» (era el fin estimado, 16/12/2026)", _f1 == {"finished_on": "12/11/2026"}, _f1)
chk("…y en marcha, «estimated_finish»", _f2 == {"estimated_finish": "16/12/2026"}, _f2)
_t = src("core/chat_tools.py")
chk("el asistente lo usa en sus tres listas de obras (no queda «estimated_finish» a mano)",
    _t.count("**_fin_de_obra(") == 3 and '"estimated_finish": dmy(' not in _t, _t.count("**_fin_de_obra("))
_n, _cp = funcion("core/projects_ui.py", "_completada")
chk("la ficha usa la MISMA regla de terminada", "P.es_completada(prj)" in _cp)

ESTADO = r'''
import datetime as dt
import streamlit as st
from core import projects_ui as PU, projects as P, clock, alerts
from core import roster as R
# HOY dentro de la ventana de la actividad 2 (07/11 → 12/11): solo así es «parada» (`_diagnostico`, `tocaban`)
clock.today = lambda *a, **k: dt.date(2026, 11, 10)
st.session_state.setdefault("auth", {"usuario": "admin2", "rol": "administrator", "grupo": "G", "nombre": "Bobo"})
_ST, _AV = st.session_state.get("_ST", "In progress"), st.session_state.get("_AV", 40)
_P = {"ID": "PRJ-9", "Group": "G", "Name": "Lift 9", "Status": _ST, "Progress": str(_AV), "StartDate": "2026-11-02",
      "EndDateEst": "2026-11-30", "Type": "Installation"}
def _a(o, av, ini, fin):
    return {"ProjectID": "PRJ-9", "Order": str(o), "Name": "Act %d" % o, "DurationDays": "5", "Weight": "50",
            "Progress": str(av), "ActualStartDate": ini, "ActualEndDate": fin, "Note": ""}
if _AV >= 100:
    _A = [_a(1, 100, "2026-11-02", "2026-11-06"), _a(2, 100, "2026-11-06", "2026-11-09")]
else:      # la 1 acabada a tiempo y la 2 sin empezar: una actividad PARADA de verdad (si no, el CONTROL pasa en vacío)
    _A = [_a(1, 100, "2026-11-02", "2026-11-06"), _a(2, 0, "", "")]
P.get_project = lambda pid: dict(_P)
P.list_activities = lambda pid: [dict(a) for a in _A]
alerts.is_configured = lambda: False
R.sin_planificar = lambda *a, **k: {"obras": [], "jefes": []}
PU.lista_cierre = lambda *a, **k: []
PU._bloqueos_de = lambda *a, **k: {}
PU._cumplimiento_equipo = lambda *a, **k: None
PU._estado_section("PRJ-9", "G", dict(_P))
'''


def _estado(st_, av):
    a = AppTest.from_string(ESTADO, default_timeout=90)
    a.session_state["_ST"] = st_
    a.session_state["_AV"] = av
    a.run()
    return a, " ¦ ".join(m.value for m in a.markdown) + " ¦ " + " ¦ ".join(
        x.value for x in list(a.warning) + list(a.error) + list(a.info) + list(a.success))


at, _tx = _estado("Completed", 100)
chk("la pestaña Status de una obra TERMINADA se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("…dice «The job finished on 09/11/2026», con «Finished on» frente a lo planificado (30/11, -21 d)",
    "finished on 09/11/2026" in _tx and "Finished on" in _tx and "30/11/2026" in _tx and "-21 d" in _tx, _tx[:900])
chk("…y sin «Projected finish» ni puntos de retraso", "Projected finish" not in _tx and "points behind" not in _tx, _tx[:900])
at, _tx = _estado("Cancelled", 50)
chk("la de una obra CANCELADA se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("…dice que no hay plan que seguir, sin «Projected finish», ni retraso, ni actividad «should have started»",
    "cancelled</b>: there is no plan to follow" in _tx and "Projected finish" not in _tx and "points behind" not in _tx
    and "should have started" not in _tx and "Not started and already due" not in _tx, _tx[:900])
at, _tx = _estado("On hold", 50)
chk("…y la de una en PAUSA, «the plan is paused»", "on hold</b>: the plan is paused" in _tx
    and "Projected finish" not in _tx and "should have started" not in _tx, _tx[:900])
at, _tx = _estado("In progress", 50)
chk("CONTROL: una en marcha sigue con su proyección y su actividad parada", "Projected finish" in _tx
    and ("should have started" in _tx or "Not started and already due" in _tx), _tx[:900])

# ═════════════════════════════════════════════════════════════════════════════
sec("4. La ficha del cliente: «activa» como Home (H4)")
from core import clientes_ui as CU                                         # noqa: E402
_proys = [{"ID": str(i), "Status": s, "Progress": "10"} for i, s in
          enumerate(["Planned", "In progress", "On hold", "Cancelled", "Completed", "Archived", "In progress"])]
_act_n = CU._agregados(_proys, {}, {}, {})[0]
chk("cuenta solo las planificadas o en curso (3 de 7; antes 4: contaba la de pausa y las canceladas)",
    _act_n == 3 == sum(1 for p in _proys if P.es_activa(p)), _act_n)
_n, _cc = funcion("core/clientes_ui.py", "_cifras_cliente")
_n2, _do = funcion("core/clientes_ui.py", "_desglose_obras")
chk("…con el pie de lo que cuenta, y el desglose con la misma regla", 't("planned/ongoing")' in _cc
    and 'P.es_activa({"Status": f["estado"]})' in _do and "not completed" not in _cc + _do)

# ═════════════════════════════════════════════════════════════════════════════
sec("5. «Already assigned to another project», solo lo vigente (H17)")
from core import projects_ui as PU                                         # noqa: E402
from core import auth as A                                                 # noqa: E402
from core import credentials as CR                                         # noqa: E402
from core import ausencias as AUS                                          # noqa: E402
_OTRAS = [{"ID": "PRJ-1", "Name": "Acabó el 29/10", "Status": "In progress", "EndDateEst": "2026-10-29", "FieldAssigned": "h1"},
          {"ID": "PRJ-2", "Name": "Sigue hasta diciembre", "Status": "In progress", "EndDateEst": "2026-12-20", "FieldAssigned": "h1"},
          {"ID": "PRJ-3", "Name": "En pausa", "Status": "On hold", "EndDateEst": "2026-12-20", "FieldAssigned": "h1"},
          {"ID": "PRJ-4", "Name": "Planificada sin fecha", "Status": "Planned", "EndDateEst": "", "FieldAssigned": "h1"},
          {"ID": "PRJ-5", "Name": "Cancelada", "Status": "Cancelled", "EndDateEst": "2026-12-20", "FieldAssigned": "h1"},
          {"ID": "PRJ-43", "Name": "Esta misma", "Status": "In progress", "EndDateEst": "2026-12-20", "FieldAssigned": "h1"}]
_d = [_sustituir(P, list_projects=lambda *a, **k: [dict(x) for x in _OTRAS]),
      _sustituir(A, get_user=lambda u: {"User": u, "Name": "helper 1", "Email": "h1@example.com", "Active": "SI"},
                 list_users=lambda *a, **k: [{"User": "h1", "Name": "helper 1"}]),
      _sustituir(CR, list_for=lambda u: []), _sustituir(AUS, list_group=lambda *a, **k: []),
      _sustituir(clock, today=lambda *a, **k: date(2026, 11, 16))]
try:
    _av = PU.avisos_asignacion(["h1"], "G", exclude_pid="PRJ-43")
finally:
    for x in _d:
        x()
_oc = " ".join(_av.get("ocupados", []))
chk("avisa de la que sigue y de la planificada sin fecha", "Sigue hasta diciembre" in _oc and "Planificada sin fecha" in _oc, _oc)
chk("…y NO de la que acabó (29/10), la de pausa, la cancelada ni la propia",
    not any(x in _oc for x in ("Acabó el 29/10", "En pausa", "Cancelada", "Esta misma")), _oc)

# ═════════════════════════════════════════════════════════════════════════════
sec("6. El buscador con una cifra (visto verificando v672)")
BUSQ = r'''
import streamlit as st
from core import home_ui as HU
st.session_state.setdefault("_LL", [])
HU.buscar = lambda q, g: (st.session_state["_LL"].append(q), [])[1]
HU._pantalla_busqueda(st.session_state.get("_Q", "4"), "G")
'''
at = AppTest.from_string(BUSQ, default_timeout=60)
at.run()
_cap = " ".join(c.value for c in at.caption)
chk("«4» se busca (era «Type at least two letters.»)", list(at.session_state["_LL"]) == ["4"]
    and "Type at least two letters" not in _cap, (list(at.session_state["_LL"]), _cap))
at = AppTest.from_string(BUSQ, default_timeout=60)
at.session_state["_Q"] = "a"
at.run()
chk("…y una LETRA sigue pidiendo dos (con una, todo coincidiría)", not list(at.session_state["_LL"])
    and "Type at least two letters" in " ".join(c.value for c in at.caption))

print("\n" + ("TODO OK" if not FALLOS else f"{len(FALLOS)} FALLO(S): {FALLOS}"))
sys.exit(1 if FALLOS else 0)
