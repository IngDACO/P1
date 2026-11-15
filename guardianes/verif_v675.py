# -*- coding: utf-8 -*-
"""v675 · Lo visto verificando v673 desde la oficina (15/11):
- la pestaña Status de una obra cancelada o en pausa decía aún «Next milestone: … starts on 19/11 (in 4 days)»;
- `get_money` no decía de qué obra es cada factura abierta («I can't tell which job 0006 belongs to»), y de un cliente
  con solo facturas anuladas decía «It has no invoices».

Nada sale a la red ni escribe: funciones reales con sustitutos; AppTest de la pestaña.
"""
import json
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


def _sustituir(obj, **kw):
    viejo = {k: getattr(obj, k) for k in kw}
    for k, v in kw.items():
        setattr(obj, k, v)
    return lambda: [setattr(obj, k, v) for k, v in viejo.items()]


from streamlit.testing.v1 import AppTest                                   # noqa: E402
from core import chat_tools as CT                                          # noqa: E402
from core import invoices as INV                                           # noqa: E402
from core import expenses as E                                             # noqa: E402
from core import finance as F                                              # noqa: E402
from core import clock                                                     # noqa: E402


def _fac(fid, num, cli, tot, cob, lineas, status="emitida", venc="2026-12-01"):
    return {"ID": fid, "Number": num, "ClientName": cli, "Date": "2026-10-20", "ExpiryDate": venc, "Total": str(tot),
            "Collected": str(cob), "Status": status, "LinesJSON": json.dumps(lineas)}


_FACS = [_fac("F6", "0006", "C1", 250.0, 0.0, [{"concepto": "c", "importe": 150.0, "proyecto_id": "PRJ-0040"},
                                               {"concepto": "c2", "importe": 50.0, "proyecto_id": "PRJ-0040"},
                                               {"concepto": "c3", "importe": 50.0, "proyecto_id": "PRJ-0042"},
                                               {"concepto": "sin obra", "importe": 0.0}], venc="2026-10-27"),
         _fac("F3", "0003", "C2", 6276.05, 0.0, [{"concepto": "d", "importe": 5705.5, "proyecto_id": "PRJ-0043"}],
              status="anulada")]
_CTX = {"grupo": "G", "usuario": "admin2", "nombre": "Bobo", "rol": "administrator"}

print("1. get_money: la obra de cada factura abierta, y las anuladas por cliente")
_d = [_sustituir(CT, _mis_obras=lambda c: []),
      _sustituir(INV, list_facturas=lambda *a, **k: [dict(x) for x in _FACS], pendiente_por_proyecto=lambda *a, **k: {}),
      _sustituir(E, over_budget=lambda *a, **k: []),
      _sustituir(F, pnl=lambda *a, **k: {"facturado": 0, "ingresos": 0, "impuesto": 0, "cobrado": 0, "por_cobrar": 0,
                                         "vencido": 0, "costo_nomina": 0, "compras": 0, "costo_total": 0, "ganancia": 0,
                                         "por_pagar": 0},
                 group_profitability=lambda *a, **k: {"rows": [], "totales": {}}),
      _sustituir(clock, today=lambda *a, **k: date(2026, 11, 16))]
try:
    _g = CT._dinero({}, _CTX)
finally:
    for x in _d:
        x()
_ab = {f["number"]: f for f in _g.get("open_invoices", [])}
chk("la 0006 abierta dice sus obras, sin repetir y sin las líneas sin obra: PRJ-0040 y PRJ-0042",
    _ab.get("0006", {}).get("jobs") == ["PRJ-0040", "PRJ-0042"], _ab.get("0006"))
_cli = {c["client"]: c for c in _g.get("by_client_all_time", [])}
chk("C2, con solo una anulada: 0 facturas que cuenten y 1 ANULADA (decía «It has no invoices»)",
    _cli.get("C2", {}).get("invoices") == 0 and _cli["C2"].get("voided_invoices") == 1, _cli.get("C2"))
chk("…y C1, 0 anuladas", _cli.get("C1", {}).get("voided_invoices") == 0, _cli.get("C1"))

print("2. La pestaña Status: sin «Next milestone» en una obra cancelada o en pausa")
ESTADO = r'''
import datetime as dt
import streamlit as st
from core import projects_ui as PU, projects as P, clock, alerts
from core import roster as R
clock.today = lambda *a, **k: dt.date(2026, 11, 10)
st.session_state.setdefault("auth", {"usuario": "admin2", "rol": "administrator", "grupo": "G", "nombre": "Bobo"})
_ST = st.session_state.get("_ST", "In progress")
_P = {"ID": "PRJ-9", "Group": "G", "Name": "Lift 9", "Status": _ST, "Progress": "33", "StartDate": "2026-11-02",
      "EndDateEst": "2026-12-15", "Type": "Installation"}
def _a(o, av, ini, fin):
    return {"ProjectID": "PRJ-9", "Order": str(o), "Name": "Act %d" % o, "DurationDays": "5", "Weight": "33",
            "Progress": str(av), "ActualStartDate": ini, "ActualEndDate": fin, "Note": ""}
# la 1 acabada, la 2 en su ventana (hoy) y la 3 por delante: hay un «próximo hito» de verdad
_A = [_a(1, 100, "2026-11-02", "2026-11-06"), _a(2, 0, "", ""), _a(3, 0, "", "")]
P.get_project = lambda pid: dict(_P)
P.list_activities = lambda pid: [dict(a) for a in _A]
alerts.is_configured = lambda: False
R.sin_planificar = lambda *a, **k: {"obras": [], "jefes": []}
PU.lista_cierre = lambda *a, **k: []
PU._bloqueos_de = lambda *a, **k: {}
PU._cumplimiento_equipo = lambda *a, **k: None
PU._estado_section("PRJ-9", "G", dict(_P))
'''


def _estado(st_):
    a = AppTest.from_string(ESTADO, default_timeout=90)
    a.session_state["_ST"] = st_
    a.run()
    return a, " ¦ ".join(x.value for x in list(a.markdown) + list(a.caption))


at, _tx = _estado("In progress")
chk("CONTROL: una obra en marcha dice su «Next milestone» (la sonda lo ve)", not at.exception and "Next milestone" in _tx,
    ([e.value for e in at.exception][:1], _tx[:600]))
for _s in ("Cancelled", "On hold"):
    at, _tx = _estado(_s)
    chk(f"una obra «{_s}» se pinta sin excepción y SIN «Next milestone»", not at.exception and "Next milestone" not in _tx,
        ([e.value for e in at.exception][:1], _tx[:600]))

print("\n" + ("TODO OK" if not FALLOS else f"{len(FALLOS)} FALLO(S): {FALLOS}"))
sys.exit(1 if FALLOS else 0)
