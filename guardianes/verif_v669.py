# -*- coding: utf-8 -*-
"""v669 · Una sola definición del dinero de una obra (ciclo 2, mejoras 1/5).

H12 el ingreso de una obra cotizada suma las variaciones APROBADAS.
H19 una obra CANCELADA vale lo facturado: nada por facturar (Resumen, Profitability, ficha, asistente).
H22 el Resumen separa lo GANADO y sin facturar del contrato que queda por delante.
H23 una obra POR HORAS tiene ganado lo trabajado: sin aviso de adelanto.
H29 facturar por encima de lo que queda se avisa, y la ficha dice lo facturado de más.
H20 una factura con cobros no se anula sin decir adónde va el dinero; una anulada con cobros se resuelve.
H10 el último cobro apuntado a mano se puede quitar, y queda en el historial.

Nada sale a la red ni escribe: funciones reales con sustitutos en memoria y una hoja de mentira.
"""
import ast
import io
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


from core import finance as F                                              # noqa: E402
from core import invoices as I                                             # noqa: E402
from core import projects as P                                             # noqa: E402
from core import expenses as E                                             # noqa: E402
from core import claims as CL                                              # noqa: E402
from core import quotes as Q                                               # noqa: E402

# los originales, para que un guion que venga detrás no herede un sustituto (trampa 48)
_ORIG = {"F.project_revenue": F.project_revenue, "I.facturado_por_proyecto": I.facturado_por_proyecto,
         "I.por_certificar": I.por_certificar, "I.pendiente_de_facturar": I.pendiente_de_facturar}


def _sustituir(obj, **kw):
    viejo = {k: getattr(obj, k) for k in kw}
    for k, v in kw.items():
        setattr(obj, k, v)
    return lambda: [setattr(obj, k, v) for k, v in viejo.items()]


# ═════════════════════════════════════════════════════════════════════════════
sec("1. El ingreso de la obra (H12 variaciones, H19 cancelada)")
_d1 = [_sustituir(E, project_expenses=lambda pid: {"total": 39286.4}, labor_cost=lambda pid, g: 0.0),
       _sustituir(P, ganancia_hora=lambda pid, prj=None: {}, ganancia_fija=lambda pid, prj=None: 0.0),
       _sustituir(Q, cotizacion_de_proyecto=lambda pid: {"Subtotal": "57055", "ID": "COT-0012"}),
       _sustituir(CL, valor_variaciones=lambda pid: 2500.0),
       _sustituir(I, facturado_por_proyecto=lambda g: {"PRJ-43": 0.0})]
try:
    _viva = F.project_revenue("PRJ-43", "G", {"ID": "PRJ-43", "Status": "In progress"})
    _canc = F.project_revenue("PRJ-43", "G", {"ID": "PRJ-43", "Status": "Cancelled"})
    _arch = F.project_revenue("PRJ-43", "G", {"ID": "PRJ-43", "Status": "Archived"})
    I.facturado_por_proyecto = lambda g: {"PRJ-43": 500.0}
    _canc5 = F.project_revenue("PRJ-43", "G", {"ID": "PRJ-43", "Status": "Cancelled"})
    _pend_canc = I.pendiente_de_facturar("PRJ-43", "G", {"ID": "PRJ-43", "Status": "Cancelled"})
    _pend_viva = I.pendiente_de_facturar("PRJ-43", "G", {"ID": "PRJ-43", "Status": "In progress"})
finally:
    for _d in _d1:
        _d()
chk("H12 · cotizada: el ingreso = cotización + variaciones aprobadas (57.055 + 2.500)",
    _viva["ingreso"] == 59555.0 and _viva.get("variaciones") == 2500.0 and _viva["modelo"] == "cotizado", _viva)
chk("…y el margen sale de ese ingreso", _viva["ganancia"] == round(59555 - 39286.4, 2), _viva)
chk("H19 · cancelada: vale lo FACTURADO (0) y enseña la pérdida (-39.286,40)",
    _canc["ingreso"] == 0.0 and _canc["ganancia"] == -39286.4 and _canc["modelo"] == "cancelada", _canc)
chk("…con un cargo facturado, ese cargo es su ingreso", _canc5["ingreso"] == 500.0, _canc5)
chk("…y no le queda nada por facturar; a la viva, el contrato menos lo facturado",
    _pend_canc == 0.0 and _pend_viva == 59055.0, (_pend_canc, _pend_viva))
chk("una ARCHIVADA no es cancelada: sigue con su precio (archivar no es no-cobrar, v369)",
    _arch["modelo"] == "cotizado" and _arch["ingreso"] == 59555.0, _arch)
chk("projects.es_cancelada solo con Cancelled",
    P.es_cancelada({"Status": "Cancelled"}) and not P.es_cancelada({"Status": "Archived"})
    and not P.es_cancelada({}) and not P.es_cancelada(None))
_n, _pr = funcion("core/finance.py", "project_revenue")
chk("…y la rama de la cancelada va ANTES que la de la cotización",
    0 < _pr.find("if P.es_cancelada(_p_est):") < _pr.find("if _cot:"), _pr[:200])

# ═════════════════════════════════════════════════════════════════════════════
sec("2. Lo certificable según el modelo (H23)")


def _cert(rev, fac, avance, pend=None):
    _d = [_sustituir(F, project_revenue=lambda pid, g, p=None: dict(rev)),
          _sustituir(I, facturado_por_proyecto=lambda g: {"P": fac})]
    if pend is not None:
        _d.append(_sustituir(I, pendiente_de_facturar=lambda pid, g, p=None: pend))
    try:
        return I.por_certificar("P", "G", {"ID": "P", "Progress": str(avance)})
    finally:
        for x in _d:
            x()


_tm0 = _cert({"ingreso": 0.45, "modelo": "a_costo", "ganancia_fija": 0.0}, 0.0, 0)
chk("por horas al 0 %: lo trabajado (0,45) es certificable, sin adelanto",
    _tm0["certificable"] == 0.45 and _tm0["adelanto"] == 0.0 and _tm0["modelo"] == "a_costo", _tm0)
_tmf = _cert({"ingreso": 1000.0, "modelo": "fija", "ganancia_fija": 400.0}, 0.0, 50)
chk("por horas con 400 de ganancia fija al 50 %: ganado 800, adelanto 200",
    _tmf["ganado"] == 800.0 and _tmf["certificable"] == 800.0 and _tmf["adelanto"] == 200.0, _tmf)
_co0 = _cert({"ingreso": 12780.0, "modelo": "cotizado"}, 3834.0, 0)
_co50 = _cert({"ingreso": 12780.0, "modelo": "cotizado"}, 3834.0, 50)
chk("cotizada al 0 %: nada certificable, todo adelanto (8.946)",
    _co0["certificable"] == 0 and _co0["adelanto"] == 8946.0, _co0)
chk("cotizada al 50 %: ganado 6.390, certificable 2.556, adelanto 6.390",
    _co50["ganado"] == 6390.0 and _co50["certificable"] == 2556.0 and _co50["adelanto"] == 6390.0, _co50)
_px = _cert({"ingreso": 12780.0, "modelo": "cotizado"}, 0.0, 0, pend=777.0)
chk("el pendiente sigue siendo pendiente_de_facturar (una sola definición)", _px["pendiente"] == 777.0, _px)
_canc0 = _cert({"ingreso": 0.0, "modelo": "cancelada"}, 0.0, 30)
chk("una cancelada: nada pendiente ni certificable", _canc0["pendiente"] == 0 and _canc0["certificable"] == 0, _canc0)

# ═════════════════════════════════════════════════════════════════════════════
sec("3. El Resumen: lo ganado aparte del contrato por delante (H22)")
_PRJS = [{"ID": "A", "Name": "Darling Park", "Status": "Planned"},
         {"ID": "B", "Name": "Parramatta", "Status": "In progress"},
         {"ID": "C", "Name": "Hecha", "Status": "Completed"}]
_DIN = {"A": {"pendiente": 79036.0, "certificable": 0.0, "adelanto": 79036.0},
        "B": {"pendiente": 10371.9, "certificable": 7644.09, "adelanto": 2727.81},
        "C": {"pendiente": 0.0, "certificable": 0.0, "adelanto": 0.0}}
_d3 = [_sustituir(P, list_projects=lambda **k: [dict(x) for x in _PRJS]),
       _sustituir(I, por_certificar=lambda pid, g, p=None: dict(_DIN[pid]))]
try:
    _din = I.dinero_por_proyecto("G")
    _sf = F.sin_facturar_ids("G")
    _sfc = F.contrato_sin_ganar_ids("G")
    _sf_viejo = F.sin_facturar("G")
finally:
    for _d in _d3:
        _d()
chk("dinero_por_proyecto: solo las que tienen algo por facturar", set(_din) == {"A", "B"}, _din)
chk("⚠️ «sin facturar» = lo GANADO: solo Parramatta (7.644,09); Darling Park al 0 % ya no",
    _sf == [("B", "Parramatta", 7644.09)], _sf)
chk("…y el contrato por delante, aparte: Darling Park 79.036 y Parramatta 2.727,81",
    _sfc == [("A", "Darling Park", 79036.0), ("B", "Parramatta", 2727.81)], _sfc)
chk("sin_facturar (nombre, importe) sigue la misma regla", _sf_viejo == [("Parramatta", 7644.09)], _sf_viejo)
_n, _rs = funcion("core/projects_ui.py", "render_pnl")
chk("el Resumen llama «Earned, not invoiced» a la cifra y lista el contrato aparte",
    't("Earned, not invoiced")' in _rs and "_sfc = F.contrato_sin_ganar_ids(grupo)" in _rs
    and "Contract still ahead, not earned yet" in _rs and 'key=f"pnlcon_{_pid}"' in _rs, _rs[-800:])
chk("…urgente solo si hay algo GANADO (no un $0 en rojo por un contrato por delante)",
    'T.dinero(sum(v for _p, _n, v in _sf), 0), bool(_sf), bool(_sf) or bool(_sfc),' in _rs)

# ═════════════════════════════════════════════════════════════════════════════
sec("4. Facturar de más (H29)")
_d4 = [_sustituir(F, project_revenue=lambda pid, g, p=None: {"ingreso": 12780.0}),
       _sustituir(I, facturado_por_proyecto=lambda g: {"PRJ-39": 12880.0, "PRJ-40": 250.0})]
try:
    _dm = I.facturado_de_mas("PRJ-39", "G", {})
finally:
    for _d in _d4:
        _d()
chk("facturado_de_mas: 12.880 facturados sobre 12.780 → 100", _dm == 100.0, _dm)
from core import invoices_ui as IU                                         # noqa: E402
# ⚠️ v670 · el aviso depende de si la obra está COTIZADA (variación) o va por horas (ganancia fija): estas son cotizadas
_o_cot = I.es_cotizada
I.es_cotizada = lambda pid: True
_P39 = {"ID": "PRJ-39", "Name": "C1 — Lift 1", "Status": "Completed"}
_P43 = {"ID": "PRJ-43", "Name": "C2 — Lift 1", "Status": "Cancelled"}
_av = IU.avisos_de_mas([{"concepto": "x", "importe": 100.0, "proyecto_id": "PRJ-39"}], "G",
                       {"PRJ-39": 0.0}, [_P39])
chk("una línea de $100 en una obra facturada entera AVISA: «$100.00 over the agreed price»",
    len(_av) == 1 and "over the agreed price" in _av[0] and "100.00" in _av[0] and "variation" in _av[0], _av)
_av2 = IU.avisos_de_mas([{"importe": 60.0, "proyecto_id": "PRJ-39"}, {"importe": 50.0, "proyecto_id": "PRJ-39"}],
                        "G", {"PRJ-39": 100.0}, [_P39])
chk("…suma las líneas de la misma obra (60 + 50 sobre 100 → 10 de más)",
    len(_av2) == 1 and "10.00" in _av2[0], _av2)
chk("…dentro de lo que queda, nada", IU.avisos_de_mas([{"importe": 99.0, "proyecto_id": "PRJ-39"}], "G",
                                                      {"PRJ-39": 100.0}, [_P39]) == [])
_av3 = IU.avisos_de_mas([{"importe": 300.0, "proyecto_id": "PRJ-43"}], "G", {"PRJ-43": 0.0}, [_P43])
chk("…en una cancelada, el aviso de cargo fuera del precio", len(_av3) == 1 and "is cancelled" in _av3[0], _av3)
chk("…una línea sin obra no avisa", IU.avisos_de_mas([{"importe": 999.0, "proyecto_id": ""}], "G", {}, []) == [])
I.es_cotizada = _o_cot
_n, _nf = funcion("core/invoices_ui.py", "_nueva_factura")
_i_av = _nf.find("for _av in avisos_de_mas(_lineas, grupo, _pend_de, prjs):")
chk("los avisos se pintan tras el subtotal y ANTES de «Issue invoice»",
    _nf.find("Subtotal **{s}**") < _i_av < _nf.find("Issue invoice"), _i_av)
chk("con una obra sin nada por facturar se dice («Nothing left to invoice» / cancelada)",
    "Nothing left to invoice on **{p}**: its price is" in _nf and "is cancelled: nothing is left to invoice on it" in _nf)
chk("H23 · el aviso de adelanto mira lo certificable, no el avance",
    'if _c["certificable"] <= 0.005:' in _nf and 'if _c["avance"] <= 0:' in _nf
    and "what it has earned is already invoiced" in _nf)
_s_pui = src("core/projects_ui.py")
chk("la ficha dice lo facturado de más y que una cancelada ya no se factura",
    "_demas_cab = _INV.facturado_de_mas(pid, grupo, prj)" in _s_pui and "if _demas_cab > 0.5:" in _s_pui
    and "if P.es_cancelada(prj):" in _s_pui and "Cancelled · nothing more to invoice" in _s_pui)
chk("Profitability marca la cancelada y la archivada", 'if _e in ("Cancelled", "Archived"):' in _s_pui
    and '"estado": str((prjs.get(pid) or {}).get("Status", "")),' in src("core/finance.py"))

# ═════════════════════════════════════════════════════════════════════════════
sec("5. Cobros: quitar el último (H10), anular con cobros (H20)")
_CAB = list(I.FACTURAS_HEADERS)


def _fila(fid, num, cli, total, cob, hist, status="emitida"):
    r = {h: "" for h in _CAB}
    r.update({"ID": fid, "Group": "G", "ClientID": cli, "ClientName": cli, "Number": num, "Total": str(total),
              "Collected": str(cob), "Status": status, "CollectionsJSON": json.dumps(hist), "Date": "2026-11-10",
              "ExpiryDate": "2099-01-01"})
    return r


class _WS:
    def __init__(self, filas):
        self.filas = filas
        self.lotes, self.celdas = [], []

    def get_all_values(self):
        return [list(_CAB)] + [[r[h] for h in _CAB] for r in self.filas]

    def get_all_records(self, **k):
        return [dict(r) for r in self.filas]

    def batch_update(self, rangos, **k):
        self.lotes.append(rangos)

    def update_cell(self, fila, col, valor):
        self.celdas.append((fila, col, valor))


def _montar(filas):
    ws = _WS(filas)
    rastro = []
    from core import auditoria as AU
    deshacer = [_sustituir(I, _ws=lambda: (ws, None), _records=lambda: [dict(r) for r in ws.filas],
                           _invalidate=lambda: None),
                _sustituir(AU, registrar=lambda *a, **k: rastro.append((a, k)) or True)]
    return ws, rastro, deshacer


def _celdas(ws):
    """{(fila, letra): valor} de todo lo escrito por lotes."""
    out = {}
    for lote in ws.lotes:
        for r in lote:
            out[r["range"]] = r["values"][0][0]
    return out


from core.num import col_letter as _cl                                     # noqa: E402
_LC, _LJ, _LS = _cl(_CAB.index("Collected") + 1), _cl(_CAB.index("CollectionsJSON") + 1), _cl(_CAB.index("Status") + 1)

_m = {"fecha": "2026-11-10", "monto": 3000.0}
chk("último cobro quitable: el manual", I.ultimo_cobro_quitable({"CollectionsJSON": json.dumps([_m])})[0] == 0)
chk("…tras quitar el 2º, el 1º",
    I.ultimo_cobro_quitable({"CollectionsJSON": json.dumps(
        [_m, dict(_m, monto=50.0), {"monto": -50.0, "origen": I.QUITADO, "quita": 1}])})[0] == 0)
chk("…nunca uno de Xero ni tras una devolución",
    I.ultimo_cobro_quitable({"CollectionsJSON": json.dumps([dict(_m, origen="xero")])})[0] is None
    and I.ultimo_cobro_quitable({"CollectionsJSON": json.dumps(
        [_m, {"monto": -3000.0, "origen": I.DEVUELTO}])})[0] is None)

ws, rastro, desh = _montar([_fila("FAC-3", "0003", "CLI-7", 6276.05, 3000, [_m])])
try:
    _ok, _msg = I.quitar_ultimo_cobro("FAC-3", quien="Bobo")
finally:
    for _d in desh:
        _d()
_c = _celdas(ws)
_h = json.loads(_c.get(f"{_LJ}2", "[]"))
chk("H10 · quitar el cobro: Collected 3.000 → 0 en UNA escritura", _ok and _c.get(f"{_LC}2") == "0.0"
    and len(ws.lotes) == 1, (_ok, _msg, _c))
chk("…el historial lo guarda como movimiento contrario (con quién y cuál)",
    len(_h) == 2 and _h[1].get("origen") == I.QUITADO and _h[1].get("monto") == -3000.0
    and _h[1].get("quita") == 0 and _h[1].get("por") == "Bobo", _h)
chk("…y el rastro de cambios lo apunta", rastro and rastro[0][0][0] == "factura"
    and rastro[0][1].get("accion") == "quitar_cobro", rastro)

ws, rastro, desh = _montar([_fila("FAC-3", "0003", "CLI-7", 6276.05, 3000, [_m])])
try:
    _ok, _msg = I.anular("FAC-3")
finally:
    for _d in desh:
        _d()
chk("H20 · anular con $3,000 cobrados SIN decir adónde van: se niega y no escribe",
    # v670 · el importe con miles («$3,000.00»)
    not _ok and "3,000.00" in _msg and not ws.lotes and not ws.celdas, (_ok, _msg))
# ⚠️ trampa 55: la negativa está DOBLE (anular y sacar_cobros); cada una se prueba por su camino
chk("…y la negativa es la de `anular` (dice qué hacer con el dinero)", "say what happens with that money first" in _msg,
    _msg)
ws, rastro, desh = _montar([_fila("FAC-3", "0003", "CLI-7", 6276.05, 3000, [_m])])
try:
    _ok, _msg = I.sacar_cobros("FAC-3", None, anular_tambien=True)
finally:
    for _d in desh:
        _d()
chk("…y `sacar_cobros` por su lado tampoco anula sin destino", not _ok and not ws.lotes and "Choose what happens" in _msg,
    (_ok, _msg))

ws, rastro, desh = _montar([_fila("FAC-3", "0003", "CLI-7", 6276.05, 3000, [_m])])
try:
    _ok, _msg = I.anular("FAC-3", I.DEVOLVER, quien="Bobo")
finally:
    for _d in desh:
        _d()
_c = _celdas(ws)
_h = json.loads(_c.get(f"{_LJ}2", "[]"))
chk("…devolviéndolos: anulada, Collected 0 y «refunded» en el historial, en UNA escritura",
    _ok and _c.get(f"{_LS}2") == "anulada" and _c.get(f"{_LC}2") == "0" and _h[-1].get("origen") == I.DEVUELTO
    and _h[-1].get("monto") == -3000.0 and len(ws.lotes) == 1 and "refunded" in _msg, (_ok, _msg, _c))

_FILAS = [_fila("FAC-3", "0003", "CLI-7", 6276.05, 3000, [_m]),
          _fila("FAC-7", "0007", "CLI-7", 5000, 0, []),
          _fila("FAC-8", "0008", "OTRO", 9000, 0, []),
          _fila("FAC-9", "0009", "CLI-7", 1000, 0, [])]
ws, rastro, desh = _montar([dict(x) for x in _FILAS])
try:
    _dest = [g.get("ID") for g in I.destinos_de_cobro(dict(_FILAS[0]))]
    _ok, _msg = I.anular("FAC-3", "FAC-7", quien="Bobo")
    _ok8, _msg8 = I.anular("FAC-3", "FAC-8")
finally:
    for _d in desh:
        _d()
chk("destinos: solo facturas del MISMO cliente con saldo para recibirlo (no la de otro, ni una de $1.000)",
    _dest == ["FAC-7"], _dest)
_c = _celdas(type("PrimerLote", (), {"lotes": ws.lotes[:1]})())
_hf = json.loads(_c.get(f"{_LJ}2", "[]"))
_hg = json.loads(_c.get(f"{_LJ}3", "[]"))
chk("…pasándolos a la 0007: la 0007 sube a 3.000 con «moved from 0003», la 0003 anulada a 0",
    _ok and _c.get(f"{_LC}3") == "3000.0" and _hg[-1].get("origen") == I.TRASPASO_ENTRA
    and _hg[-1].get("de") == "0003" and _c.get(f"{_LC}2") == "0" and _hf[-1].get("origen") == I.TRASPASO_SALE
    and _hf[-1].get("a") == "0007" and _c.get(f"{_LS}2") == "anulada" and "0007" in _msg, (_ok, _msg, _c))
chk("…a una factura de OTRO cliente: se niega", not _ok8 and len(ws.lotes) == 1, (_ok8, _msg8))

ws, rastro, desh = _montar([_fila("FAC-3", "0003", "CLI-7", 6276.05, 3000, [_m], status="anulada"),
                            _fila("FAC-7", "0007", "CLI-7", 5000, 0, [])])
try:
    _ok, _msg = I.sacar_cobros("FAC-3", I.DEVOLVER, quien="Bobo")
finally:
    for _d in desh:
        _d()
_c = _celdas(ws)
chk("una ANULADA con cobros (la 0003 del ciclo 2) se resuelve devolviéndolos, sin tocar su estado",
    _ok and _c.get(f"{_LC}2") == "0" and f"{_LS}2" not in _c, (_ok, _msg, _c))
ws, rastro, desh = _montar([_fila("FAC-1", "0001", "CLI-7", 100, 50, [dict(_m, monto=50.0)])])
try:
    _ok, _msg = I.sacar_cobros("FAC-1", I.DEVOLVER)
finally:
    for _d in desh:
        _d()
chk("…pero en una VIVA no (lo cobrado se corrige quitando el cobro)", not _ok and not ws.lotes, (_ok, _msg))
ws, rastro, desh = _montar([_fila("FAC-5", "0005", "CLI-6", 110, 0, [])])
try:
    _ok, _msg = I.anular("FAC-5")
finally:
    for _d in desh:
        _d()
chk("sin cobros, anular sigue como siempre (una celda)", _ok and ws.celdas == [(2, I._FCOL["Status"], "anulada")],
    (_ok, ws.celdas))

# ═════════════════════════════════════════════════════════════════════════════
sec("6. La pantalla del detalle (AppTest)")
from streamlit.testing.v1 import AppTest                                   # noqa: E402

GUION = r'''
import datetime as dt
import json
import streamlit as st
from core import invoices as I, clientes as C, clock, contable, xero_ui, flash
clock.today = lambda *a, **k: dt.date(2026, 11, 10)
_M = {"fecha": "2026-11-10", "monto": 3000.0}
def _f(fid, num, tot, cob, hist, status="emitida"):
    return {"ID": fid, "Group": "G", "ClientID": "CLI-7", "ClientName": "C2 Coastal", "Number": num,
            "Date": "2026-11-10", "ExpiryDate": "2026-11-24", "Total": str(tot), "Subtotal": str(tot),
            "TaxPct": "0", "Tax": "0", "Collected": str(cob), "Status": status, "Note": "",
            "Created": "2026-11-10 10:00:00", "LinesJSON": "[]", "CollectionsJSON": json.dumps(hist)}
_FAC = {"FAC-3": _f("FAC-3", "0003", 6276.05, 3000, [_M], st.session_state.get("_EST", "emitida")),
        "FAC-7": _f("FAC-7", "0007", 5000, 0, [])}
I.is_configured = lambda: True
I.get_factura = lambda fid: dict(_FAC.get(fid, {}))
I.list_facturas = lambda g=None, cliente_id=None: [dict(x) for x in _FAC.values()]
C.get_cliente = lambda cid: {"ID": cid, "Name": "C2 Coastal"}
contable.identidad = lambda g: {"abn": "1", "legal": "X", "plazo": 14}
xero_ui.boton_factura = lambda g, f: None
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G", "nombre": "Jefa"})
st.session_state.setdefault("_fac_open", "FAC-3")
from core import invoices_ui as IU
flash.mostrar()
IU.render_facturas("G")
'''
at = AppTest.from_string(GUION, default_timeout=90)
at.run()
chk("el detalle de una factura con un cobro se pinta sin excepción", not at.exception,
    [e.value for e in at.exception][:1])
_bl = {b.key: b.label for b in at.button}
chk("H10 · «Remove the last payment ($3,000.00)»", any("Remove the last payment" in str(v) and "3,000.00" in str(v)
                                                       for v in _bl.values()), _bl)
_rd = [r for r in at.radio if r.key == "fac_anul_dest_FAC-3"]
_ops = [str(o) for o in (_rd[0].options if _rd else [])]
chk("H20 · el desplegable de anular pregunta adónde va el dinero: devolverlo o pasarlo a la 0007",
    len(_ops) == 2 and "Refund it to the client" in _ops[0] and "invoice No. 0007" in _ops[1]
    and "5,000.00" in _ops[1], (_ops, [r.key for r in at.radio]))
at.button(key="fac_qui_FAC-3").click().run()
chk("…«Remove» PREGUNTA antes con el importe y la fecha",
    any("Remove the payment of" in w.value and "10/11/2026" in w.value for w in at.warning),
    [w.value for w in at.warning])
at = AppTest.from_string(GUION, default_timeout=90)
at.session_state["_EST"] = "anulada"
at.run()
chk("una ANULADA con cobros se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("…avisa del dinero que no cuenta en ningún sitio y ofrece resolverlo",
    any("not counted anywhere" in w.value for w in at.warning) and "fac_res_ok_FAC-3" in {b.key for b in at.button}
    and [r for r in at.radio if r.key == "fac_res_FAC-3"], [w.value for w in at.warning])
chk("…y en una anulada no se ofrece quitar cobros", "fac_qui_FAC-3" not in {b.key for b in at.button})

# ═════════════════════════════════════════════════════════════════════════════
sec("7. El Resumen con AppTest: lo ganado y el contrato por delante (H22)")
RESUMEN = r'''
import datetime as dt
import streamlit as st
from core import projects_ui as PU, projects as P, finance as F, clock
from core import expenses as E
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G", "nombre": "Jefa"})
clock.today = lambda *a, **k: dt.date(2026, 11, 10)
_V = {"facturado": 0.0, "ingresos": 0.0, "impuesto": 0.0, "cobrado": 0.0, "por_cobrar": 0.0, "vencido": 0.0,
      "costo_nomina": 0.0, "compras": 0.0, "costo_total": 0.0, "ganancia": 0.0, "por_pagar": 0.0, "pagado": 0.0,
      "por_cliente": []}
F.pnl = lambda g, desde=None, hasta=None: dict(_V)
F.conciliacion_mo = lambda g, desde=None, hasta=None: {
    "cargado": 0.0, "cobrado_no_pagado": 0.0, "pagado_no_cargado": 0.0, "base_teorica": 0.0, "base_nomina": 0.0,
    "ausencias": 0.0, "aportes": 0.0, "costo_real": 0.0, "sin_explicar": 0.0, "interno": 0.0, "de_baja": [],
    "sin_tarifa": [], "sin_tarifa_claves": {}}
F.sin_facturar_ids = lambda g: list(st.session_state.get("_SF", []))
F.contrato_sin_ganar_ids = lambda g: [("PRJ-38", "Darling Park", 79036.5)]
F.group_profitability = lambda g: {"rows": []}
F.resultado_por_proyecto = lambda g: []
E.over_budget = lambda g: []
P.get_project = lambda pid: {"ID": pid, "Name": "Darling Park", "Client": "", "Group": "G"}
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    st.session_state["cpxseg_pnl_per"] = "Todo"
PU.render_pnl("G")
'''


def _resumen(sf):
    a = AppTest.from_string(RESUMEN, default_timeout=90)
    a.session_state["_SF"] = sf
    a.run()
    _b = [b for b in a.button if b.key == "pnlind_sinfac"]
    if _b:
        _b[0].click()
        a.run()
    return a


at = _resumen([("PRJ-26", "Parramatta", 7644.09)])
chk("el Resumen se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_kb = {b.key: b.label for b in at.button}
chk("«Earned, not invoiced» enseña lo GANADO ($7,644), no el contrato",
    _kb.get("pnlind_sinfac", "").endswith("Earned, not invoiced\n\n\\$7,644"), _kb.get("pnlind_sinfac"))
chk("…su detalle lista la obra ganada Y el contrato por delante, cada una con su botón",
    "pnlfac_PRJ-26" in _kb and "pnlcon_PRJ-38" in _kb
    and any("Contract still ahead, not earned yet" in c.value and "79,036" in c.value for c in at.caption),
    (sorted(_kb), [c.value for c in at.caption][:6]))
at = _resumen([])
_kb = {b.key: b.label for b in at.button}
chk("solo con contrato por delante: la cifra en $0, el detalle se abre y dice el contrato",
    _kb.get("pnlind_sinfac", "").endswith("\\$0") and "pnlcon_PRJ-38" in _kb
    and any("Everything worked has been invoiced." in c.value for c in at.caption), (sorted(_kb)))

# deshacer lo que pudiera quedar sustituido (trampa 48)
F.project_revenue = _ORIG["F.project_revenue"]
I.facturado_por_proyecto = _ORIG["I.facturado_por_proyecto"]
I.por_certificar = _ORIG["I.por_certificar"]
I.pendiente_de_facturar = _ORIG["I.pendiente_de_facturar"]

print("\n" + ("TODO OK" if not FALLOS else f"{len(FALLOS)} FALLO(S): {FALLOS}"))
sys.exit(1 if FALLOS else 0)
