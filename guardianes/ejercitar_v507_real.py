# -*- coding: utf-8 -*-
"""v507 contra la HOJA REAL (método v344): el ciclo entero del cobro de obra.

  foto → variación propuesta (no mueve el contrato) → aprobarla (sí lo mueve)
  → reclamar al 30% → reclamar al 50% (solo lo nuevo) → anular → borrar filas → foto

⚠️ Esta versión CREA dos hojas nuevas (`Variations`, `Claims`) en el libro del cliente.
Es lo que hace la primera escritura, igual que con `PurchaseOrders`. La foto de después
comprueba que la obra queda sin variaciones ni reclamaciones, pero **las hojas se quedan**
— crearlas es el comportamiento correcto, no basura de la prueba.

⚠️ La obra de prueba necesita una COTIZACIÓN ACEPTADA para tener valor de contrato. Si no
la tiene, el ejercicio lo dice y sale: inventarle un contrato sería probar otra cosa.
"""
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Bobo", "nombre": "Bobo",
                            "rol": "administrator", "grupo": "cliente1"}
import gspread                                                    # noqa: E402
from google.oauth2.service_account import Credentials             # noqa: E402
from core import claims as C                                      # noqa: E402
from core import projects as P                                    # noqa: E402

PID, GRUPO = "PRJ-0001", "cliente1"
MARCA = "PRUEBA v507 - puerta extra"

fallos, creadas = [], {"var": [], "clm": []}


def ck(q, real, esp):
    if real == esp:
        print("  ok   %s" % q)
    else:
        fallos.append(q)
        print("  *** FALLO  %s  -> %r != %r" % (q, real, esp))


def _libro(escribir=False):
    sc = ["https://www.googleapis.com/auth/spreadsheets"] if escribir else \
         ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    cr = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=sc)
    gc = gspread.authorize(cr)
    lib = gc.open_by_key(st.secrets["TIMECLOCK_SHEET_ID"])
    grp = lib.worksheet("Groups").get_all_values()
    sid = [f[grp[0].index("SheetID")] for f in grp[1:] if f and f[0] == GRUPO][0]
    return gc.open_by_key(sid)


def foto():
    """Filas de la obra en cada hoja. Una hoja que aún no existe cuenta como 0 filas
    —es legítimo antes de la primera escritura—, pero si existe y no se puede leer
    se ABORTA: una foto falsa aprueba cualquier cosa."""
    lb, out = _libro(), {}
    for hoja in (C.VARIACIONES, C.RECLAMACIONES):
        try:
            v = lb.worksheet(hoja).get_all_values()
        except gspread.WorksheetNotFound:
            out[hoja] = (0, [])
            continue
        except Exception as e:
            raise SystemExit("no se pudo leer %r: %r (la foto seria falsa)" % (hoja, e))
        if not v or not v[0]:
            out[hoja] = (0, [])
            continue
        out[hoja] = (len(v[0]), [f[0] for f in v[1:] if f and len(f) > 2 and f[2] == PID])
    return out


f0 = foto()
print("ANTES · %s: %d cols, %d filas de la obra · %s: %d cols, %d filas"
      % (C.VARIACIONES, f0[C.VARIACIONES][0], len(f0[C.VARIACIONES][1]),
         C.RECLAMACIONES, f0[C.RECLAMACIONES][0], len(f0[C.RECLAMACIONES][1])))

_contrato, _cot = C.contrato(PID)
_cot_propia = ""
# ⚠️ El contrato de PARTIDA, antes de que este ejercicio se cree el suyo. Es contra
# esto que se comprueba la vuelta al final: comparar con el de la cotización de prueba
# —que se borra— daría un falso fallo.
_contrato_inicial = _contrato

if not _cot:
    # ⚠️ La obra de prueba no tiene contrato. Se le crea UNA cotización, se enlaza y se
    # acepta ESCRIBIENDO en la hoja —no con `aceptar_y_crear_proyecto`, que crearía un
    # proyecto nuevo que luego habría que limpiar también—, y se borra al final.
    # Mientras dura, `finance` verá esta obra como «cotizada»: es transitorio y se
    # devuelve. Inventar el contrato en memoria probaría otra cosa.
    print("\n0) la obra no tiene contrato: se le crea una cotizacion de prueba")
    from core import quotes as Q
    ok0, msg0 = Q.crear(GRUPO, "", "Cliente de prueba",
                        [{"descripcion": MARCA + " (contrato)", "cantidad": 1,
                          "costo_unit": 60000.0, "margen_pct": 0.0,
                          "precio_total": 100000.0}],
                        0.0, None, "", "Bobo", "")
    print("   quotes.crear -> %s · %s" % (ok0, msg0))
    Q._invalidate() if hasattr(Q, "_invalidate") else None
    _nueva = sorted(Q._records(), key=lambda r: str(r.get("ID", "")))[-1]
    _cot_propia = str(_nueva.get("ID", ""))
    _w = Q._ws()
    _fila_q, _ = Q._fila(_w, _cot_propia) if hasattr(Q, "_fila") else (None, None)
    if _fila_q:
        Q._set(_w, _fila_q, {"ProjectID": PID, "Status": Q.ACEPTADA})
    Q._invalidate() if hasattr(Q, "_invalidate") else None
    _contrato, _cot = C.contrato(PID)

print("        contrato: %.2f (cotizacion %s)" % (_contrato, _cot or "—"))
if not _cot:
    raise SystemExit("no se pudo dar contrato a %s: sin valor de contrato no hay nada "
                     "que reclamar, y inventarlo seria probar otra cosa." % PID)

try:
    # ── 1) una variación PROPUESTA no mueve el contrato ──────────────────────
    print("\n1) variacion propuesta")
    ok, msg = C.crear_variacion(PID, GRUPO, MARCA, 5000, "", "Bobo")
    print("   crear_variacion -> %s · %s" % (ok, msg))
    ck("se creo", ok, True)
    C._invalidate()
    _mias = [v for v in C.variaciones(PID) if str(v.get("Description", "")) == MARCA]
    creadas["var"] = [v.get("ID") for v in _mias]
    # ⚠️ Esto PRIMERO: sin ello, «no mueve el contrato» pasa igual cuando la variación
    # no se ha leído — que es justo lo que ocultó que `Variations` estaba fuera del lote
    # de `hojas` y se leía vacío para siempre. Un chequeo que aprueba por ausencia de
    # datos no comprueba nada (trampa nº1).
    ck("la variacion se lee de vuelta de la hoja", len(_mias) >= 1, True)
    ck("...y esta PROPUESTA", str(_mias[0].get("Status", "")) if _mias else "", C.PROPUESTA)
    ck("⚠️ propuesta: NO mueve el valor de contrato",
       C.calcular(PID, GRUPO, 0)["valor"], _contrato)

    # ── 2) aprobarla sí lo mueve ─────────────────────────────────────────────
    print("\n2) se aprueba")
    ok2, msg2 = C.decidir_variacion(creadas["var"][0], True, "Bobo", GRUPO)
    print("   decidir_variacion -> %s · %s" % (ok2, msg2))
    C._invalidate()
    _valor = C.calcular(PID, GRUPO, 0)["valor"]
    ck("⚠️ aprobada: SI lo mueve", round(_valor - _contrato, 2), 5000.0)

    # ── 3) reclamar al 30% ───────────────────────────────────────────────────
    print("\n3) reclamacion al 30%")
    d30 = C.calcular(PID, GRUPO, 30)
    ok3, msg3 = C.crear_reclamacion(PID, GRUPO, 30, "", "", "Bobo")
    print("   crear_reclamacion -> %s · %s" % (ok3, msg3))
    ck("se emitio", ok3, True)
    C._invalidate()
    _r = C.reclamaciones(PID)
    creadas["clm"] = [x.get("ID") for x in _r]
    ck("queda una reclamacion", len(_r), 1)
    from core.num import num as _num
    ck("...con el trabajo hecho congelado", round(_num(_r[-1].get("WorkDone")), 2), d30["hecho"])
    ck("...y la retencion que tocaba", round(_num(_r[-1].get("Retention")), 2), d30["retencion"])

    # ── 4) al 50% solo se reclama lo NUEVO ───────────────────────────────────
    print("\n4) reclamacion al 50%: solo lo nuevo")
    d50 = C.calcular(PID, GRUPO, 50)
    ck("⚠️ el «ya reclamado» sale de la reclamacion anterior", d50["antes"], d30["hecho"])
    ok4, _ = C.crear_reclamacion(PID, GRUPO, 50, "", "", "Bobo")
    ck("se emitio la segunda", ok4, True)
    C._invalidate()
    _r = C.reclamaciones(PID)
    creadas["clm"] = [x.get("ID") for x in _r]
    ck("hay dos", len(_r), 2)
    ck("...y la segunda reclama solo la diferencia",
       round(_num(_r[-1].get("ThisClaim")), 2), d50["bruto"])

    # ── 5) no se puede anular la del medio ───────────────────────────────────
    print("\n5) anular")
    ok5, msg5 = C.anular(_r[0].get("ID"))
    ck("⚠️ anular la PRIMERA se rechaza", ok5, False)
    ok6, _ = C.anular(_r[-1].get("ID"))
    ck("...y la ultima si", ok6, True)
    C._invalidate()
    ck("⚠️ anulada, deja de contar como reclamado",
       C.calcular(PID, GRUPO, 50)["antes"], d30["hecho"])

finally:
    # ── 6) devolver la obra ──────────────────────────────────────────────────
    print("\n6) se borran las filas de prueba")
    try:
        lb = _libro(escribir=True)
        for hoja, ids in ((C.VARIACIONES, creadas["var"]), (C.RECLAMACIONES, creadas["clm"])):
            if not ids:
                continue
            ws = lb.worksheet(hoja)
            v = ws.get_all_values()
            filas = [n for n, f in enumerate(v[1:], start=2) if f and f[0] in ids]
            for n in sorted(filas, reverse=True):
                ws.delete_rows(n)
            print("   %s: borradas %d fila(s)" % (hoja, len(filas)))
        # y la cotización de prueba, si la creó este ejercicio
        if _cot_propia:
            from core import quotes as Q
            ws = lb.worksheet(Q.SHEET if hasattr(Q, "SHEET") else "Quotes")
            v = ws.get_all_values()
            fq = [n for n, f in enumerate(v[1:], start=2) if f and f[0] == _cot_propia]
            for n in sorted(fq, reverse=True):
                ws.delete_rows(n)
            print("   cotizacion de prueba %s: borradas %d fila(s)" % (_cot_propia, len(fq)))
            Q._invalidate() if hasattr(Q, "_invalidate") else None
    except Exception as e:
        print("   *** NO se pudo limpiar: %r" % e)
    C._invalidate()

f9 = foto()
print("\nDESPUES · %s: %d filas de la obra · %s: %d filas"
      % (C.VARIACIONES, len(f9[C.VARIACIONES][1]),
         C.RECLAMACIONES, len(f9[C.RECLAMACIONES][1])))
ck("la obra queda sin variaciones de prueba",
   f9[C.VARIACIONES][1], f0[C.VARIACIONES][1])
ck("...ni reclamaciones", f9[C.RECLAMACIONES][1], f0[C.RECLAMACIONES][1])
ck("y el valor de contrato vuelve a su estado de partida",
   C.calcular(PID, GRUPO, 0)["valor"], _contrato_inicial)

print("\n" + "=" * 70)
print("COBRO DE OBRA CONTRA LA HOJA REAL — " + ("TODO OK" if not fallos else "HAY FALLOS"))
for f in fallos:
    print("  - " + f)
sys.exit(1 if fallos else 0)
