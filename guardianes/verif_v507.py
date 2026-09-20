# -*- coding: utf-8 -*-
"""v507 · COBRO DE OBRA: variaciones y reclamaciones de avance.

Lo que protege:
  (a) la aritmética de la reclamación, que es donde un error no se ve y se COBRA mal;
  (b) ⚠️ que una variación PROPUESTA no sea dinero — meterla en el valor de contrato
      sería reclamar trabajo que el cliente no ha aceptado;
  (c) ⚠️ que si el avance BAJA no se genere una devolución en silencio: eso es una nota
      de crédito, otro documento con otras consecuencias;
  (d) que lo acumulado se lleve en `WorkDone` y NO sumando netos: la retención se
      descuenta del pago, no del trabajo hecho (si no, la obra no llega nunca al 100%);
  (e) ⚠️ que el valor de contrato sea el **Subtotal** de la cotización aceptada — la
      misma base que `finance` e `invoices`, o los totales comparan peras con manzanas;
  (f) que sin cotización aceptada no se pueda emitir nada, y se diga;
  (g) que una variación ya decidida no se pueda re-decidir por debajo de reclamaciones
      ya emitidas con ese valor;
  (h) que solo se pueda anular la ÚLTIMA reclamación;
  (i) las filas posicionales contra sus cabeceras (v363), en las DOS hojas.
Todo EJECUTANDO: importar no ejecuta (v378) y compilar no verifica nada (v439).
"""
import ast
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Bobo", "nombre": "Bobo",
                            "rol": "administrator", "grupo": "cliente1"}

fallos, n_ok = [], 0


def ok(q):
    global n_ok
    n_ok += 1
    print(f"  ok   {q}")


def fallo(q, d=""):
    fallos.append(q)
    print(f"  *** FALLO  {q}" + (f"  -> {d}" if d else ""))


def ck(q, real, esp):
    ok(q) if real == esp else fallo(q, f"{real!r} != {esp!r}")


def _fuente(f):
    return io.open(os.path.join(RAIZ, f), encoding="utf-8").read()


from core import claims as C                                      # noqa: E402

VARS, CLMS = [], []


def _montar(contrato=100000.0, cot="QUO-1", ret=5.0):
    C.contrato = lambda pid: (contrato, cot)
    C.retencion_pct = lambda g: ret
    C._records = lambda hoja: (VARS if hoja == C.VARIACIONES else CLMS)


def _d(pct):
    return C.calcular("PRJ-1", "g", pct)


# ═════ 1 · la aritmética ═════════════════════════════════════════════════════
print("\n[1] lo que se puede reclamar")
_montar()
r = _d(30)
ck("primera reclamacion al 30%",
   (r["valor"], r["hecho"], r["antes"], r["bruto"], r["retencion"], r["neto"]),
   (100000.0, 30000.0, 0.0, 30000.0, 1500.0, 28500.0))

CLMS = [{"ProjectID": "PRJ-1", "Number": "1", "WorkDone": "30000",
         "Retention": "1500", "ThisClaim": "30000", "Status": C.EMITIDA}]
_montar()
r = _d(50)
ck("la segunda solo reclama lo NUEVO",
   (r["hecho"], r["antes"], r["bruto"], r["neto"]), (50000.0, 30000.0, 20000.0, 19000.0))

# ⚠️ (d) lo acumulado sale de WorkDone, no de sumar netos. Si se sumaran los netos, el
# «antes» seria 28.500 y la obra nunca llegaria al 100%: la retencion se descuenta del
# PAGO, no del trabajo hecho.
ck("⚠️ lo acumulado sale de WorkDone, no de los netos", r["antes"], 30000.0)
ck("...y la retencion acumulada se lleva aparte", r["retenido_acumulado"], 1500.0)


# ═════ 2 · ⚠️ una variación PROPUESTA no es dinero ═══════════════════════════
print("\n[2] que cuenta como valor de contrato")
VARS = [{"ProjectID": "PRJ-1", "Number": "1", "Amount": "10000", "Status": C.APROBADA},
        {"ProjectID": "PRJ-1", "Number": "2", "Amount": "7000", "Status": C.PROPUESTA},
        {"ProjectID": "PRJ-1", "Number": "3", "Amount": "3000", "Status": C.RECHAZADA}]
_montar()
ck("⚠️ solo la APROBADA entra en el valor", _d(50)["valor"], 110000.0)
ck("...y el valor de las variaciones lo dice", _d(50)["variaciones"], 10000.0)
# una reduccion de alcance es un importe NEGATIVO, y existe en obra
VARS = [{"ProjectID": "PRJ-1", "Number": "1", "Amount": "-4000", "Status": C.APROBADA}]
_montar()
ck("una reduccion de alcance RESTA del contrato", _d(50)["valor"], 96000.0)


# ═════ 3 · ⚠️ si el avance baja, no se devuelve dinero ═══════════════════════
print("\n[3] el avance que retrocede")
VARS = []
_montar()
r = _d(20)                                    # ya se reclamaron 30.000
ck("⚠️ el bruto es CERO, no negativo", r["bruto"], 0.0)
ck("...y el neto tambien", r["neto"], 0.0)
ck("...y la retencion de este periodo, cero", r["retencion"], 0.0)


# ═════ 4 · los límites del porcentaje ════════════════════════════════════════
print("\n[4] el porcentaje")
CLMS = []
_montar()
ck("un avance por encima de 100 se recorta", _d(150)["pct"], 100.0)
ck("...y uno negativo, a cero", _d(-20)["pct"], 0.0)
ck("al 100% se reclama el valor entero", _d(100)["hecho"], 100000.0)


# ═════ 5 · sin cotización aceptada no hay nada que reclamar ══════════════════
print("\n[5] la obra sin contrato")
_montar(contrato=0.0, cot="")
r = _d(50)
ck("⚠️ se dice que no hay contrato", r["hay_contrato"], False)
_o = C._ws
try:
    C._ws = lambda h, hh: object()            # que no falle por Sheets
    ok2, msg2 = C.crear_reclamacion("PRJ-1", "g", 50)
    ck("...y no deja emitir", ok2, False)
    ck("...diciendo por que", "accepted quote" in msg2, True)
finally:
    C._ws = _o


# ═════ 6 · ⚠️ el valor de contrato es el SUBTOTAL, no el Total ═══════════════
print("\n[6] la base de comparacion")
_src = _fuente("core/claims.py")
# Misma base que finance/invoices: mezclar base con y sin impuesto descuadra los totales
ck('⚠️ `contrato` lee «Subtotal»', 'c.get("Subtotal")' in _src, True)
ck("...y NO el Total", 'c.get("Total")' in _src, False)


# ═════ 7 · las decisiones no se rehacen ══════════════════════════════════════
print("\n[7] lo decidido, decidido")
_tr = ast.parse(_src)
# ⚠️ Estos dos se comprueban EJECUTANDO, no buscando el nombre de una variable en el
# fuente: una rotura que deja la asignacion y quita el `if` pasaba el chequeo de texto
# tan campante (grep ≠ uso, trampa nº2). Lo que importa es que RECHACE.
CLMS = [{"ProjectID": "PRJ-1", "Number": "1", "WorkDone": "30000", "Status": C.EMITIDA},
        {"ProjectID": "PRJ-1", "Number": "2", "WorkDone": "50000", "Status": C.EMITIDA}]
_montar()
_o = (C._ws, C._fila, C._set)
try:
    C._ws = lambda h, hh: object()
    C._set = lambda w, col, fila, campos: (True, "")
    C._fila = lambda w, h, cid: (2, {"ProjectID": "PRJ-1", "Number": "1",
                                     "Status": C.EMITIDA, "Group": "g"})
    _ok, _msg = C.anular("CLM-1")
    ck("⚠️ anular una reclamacion que NO es la ultima se rechaza", _ok, False)
    ck("...diciendo por que", "latest claim" in _msg, True)

    C._fila = lambda w, h, cid: (3, {"ProjectID": "PRJ-1", "Number": "2",
                                     "Status": C.EMITIDA, "Group": "g"})
    ck("...y la ULTIMA si se puede anular", C.anular("CLM-2")[0], True)

    # una variacion ya decidida no se re-decide
    C._fila = lambda w, h, vid: (2, {"Status": C.APROBADA, "Group": "g"})
    _ok2, _msg2 = C.decidir_variacion("VAR-1", False, "Bobo", "g")
    ck("⚠️ una variacion ya decidida no se re-decide", _ok2, False)
    ck("...diciendo por que", "already decided" in _msg2, True)
    C._fila = lambda w, h, vid: (2, {"Status": C.PROPUESTA, "Group": "g"})
    ck("...y una PROPUESTA si se decide", C.decidir_variacion("VAR-2", True, "Bobo", "g")[0], True)
finally:
    (C._ws, C._fila, C._set) = _o
CLMS = []


# ═════ 8 · las filas posicionales (v363), en las dos hojas ═══════════════════
print("\n[8] filas contra cabeceras")
for fn, headers, etq in (("crear_variacion", C.V_HEADERS, "Variations"),
                         ("crear_reclamacion", C.C_HEADERS, "Claims")):
    _f = next(n for n in ast.walk(_tr) if isinstance(n, ast.FunctionDef) and n.name == fn)
    _ap = next((n for n in ast.walk(_f) if isinstance(n, ast.Call)
                and getattr(n.func, "attr", "") == "append_row"), None)
    assert _ap is not None, "%s ya no usa append_row" % fn
    ck("la fila de %s cuadra con %s" % (fn, etq), len(_ap.args[0].elts), len(headers))

ck("los indices salen de la cabecera (Variations)", C._VCOL["Status"],
   C.V_HEADERS.index("Status") + 1)
ck("los indices salen de la cabecera (Claims)", C._CCOL["Retention"],
   C.C_HEADERS.index("Retention") + 1)


# ═════ 9 · una anulada no cuenta para lo reclamado ═══════════════════════════
print("\n[9] la anulada")
CLMS = [{"ProjectID": "PRJ-1", "Number": "1", "WorkDone": "30000", "Retention": "1500",
         "Status": C.ANULADA}]
_montar()
ck("⚠️ una reclamacion ANULADA no cuenta como ya reclamado", _d(50)["antes"], 0.0)

print("\n" + "=" * 70)
print(f"{n_ok + len(fallos)} comprobaciones — " + ("TODO OK" if not fallos else "HAY FALLOS"))
sys.exit(1 if fallos else 0)
