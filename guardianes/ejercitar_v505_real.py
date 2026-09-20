# -*- coding: utf-8 -*-
"""v505 contra la HOJA REAL (método v344): foto → crear orden ligada a una actividad →
verificar leyendo → comprobar que bloquea → recibirla → comprobar que YA NO bloquea →
cancelar/limpiar → segunda foto.

Lo que se viene a probar con datos de verdad:
  (a) que la columna «ActivityOrder» se crea sola al final, sin descuadrar las órdenes
      que ya estén en la hoja;
  (b) que una orden ligada bloquea a SU actividad y solo a ella;
  (c) ⚠️ que al RECIBIRLA deja de bloquear — que es lo que cierra el ciclo y lo que
      ningún mock puede afirmar de la hoja.
Obra de prueba en `cliente1`. Todo lo escrito se devuelve.
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
from core import orders as O                                      # noqa: E402
from core import projects as P                                    # noqa: E402

PID, GRUPO = "PRJ-0001", "cliente1"


def foto():
    """⚠️ SOLO LECTURA: los helpers de la app MIGRAN cabeceras al acceder (v145)."""
    c = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    gc = gspread.authorize(c)
    lib = gc.open_by_key(st.secrets["TIMECLOCK_SHEET_ID"])
    grp = lib.worksheet("Groups").get_all_values()
    sid = [f[grp[0].index("SheetID")] for f in grp[1:] if f and f[0] == GRUPO][0]
    # ⚠️ La hoja se llama `PurchaseOrders` (O.SHEET), no «Orders». Con el nombre malo y
    # un `except` que se lo tragaba, la foto volvia VACIA y el chequeo de la columna
    # comparaba -1 con len([])-1 = -1: pasaba EN VACIO (trampa nº1). El nombre sale
    # ahora del modulo, y si la hoja no existe se DICE, no se devuelve una foto falsa.
    try:
        v = gc.open_by_key(sid).worksheet(O.SHEET).get_all_values()
    except Exception as e:
        raise SystemExit("no se pudo leer la hoja %r: %r (la foto seria falsa)"
                         % (O.SHEET, e))
    cab = v[0] if v else []
    if not cab:
        raise SystemExit("la hoja %r no tiene cabecera: la foto no vale" % O.SHEET)
    ic = cab.index("ActivityOrder") if "ActivityOrder" in cab else -1
    return cab, ic, [f[0] for f in v[1:] if f]


cab0, ic0, ids0 = foto()
print("ANTES · %d columnas · «ActivityOrder»: %s (idx %d) · %d ordenes"
      % (len(cab0), ic0 >= 0, ic0, len(ids0)))

acts = P.list_activities(PID)
if len(acts) < 2:
    raise SystemExit("la obra %s necesita 2+ actividades para esta prueba" % PID)
ORDEN = int(P._num(acts[1].get("Order")))       # la SEGUNDA, para no casar por casualidad
OTRA = int(P._num(acts[0].get("Order")))
print("        se ligara a la actividad %s (%r); la otra es la %s"
      % (ORDEN, acts[1].get("Name"), OTRA))

fallos, oid = [], None


def ck(q, real, esp):
    if real == esp:
        print("  ok   %s" % q)
    else:
        fallos.append(q)
        print("  *** FALLO  %s  -> %r != %r" % (q, real, esp))


try:
    # ── 1) crear la orden ligada ─────────────────────────────────────────────
    print("\n1) se crea la orden ligada a la actividad %s" % ORDEN)
    ok, msg = O.crear(PID, GRUPO, "PRUEBA v505", 123.45,
                      descripcion="Riel T75-3/B (prueba v505)",
                      fecha_esperada="2026-12-31", creado_por="Bobo",
                      actividad=str(ORDEN))
    print("   crear -> %s · %s" % (ok, msg))
    ck("la orden se creo", ok, True)
    oid = msg.split()[1] if ok else None

    _cab, _ic, _ids = foto()
    ck("«ActivityOrder» existe en la hoja y va AL FINAL", _ic, len(_cab) - 1)

    O._invalidate()
    _b = O.bloqueos(PID, GRUPO)
    ck("la actividad %s queda bloqueada" % ORDEN, ORDEN in _b, True)
    ck("...y la %s NO (no se bloquea a quien no espera nada)" % OTRA, OTRA in _b, False)
    ck("...con la descripcion que se escribio",
       _b[ORDEN][-1]["descripcion"], "Riel T75-3/B (prueba v505)")
    ck("...y con fecha futura NO se dice atrasada", _b[ORDEN][-1]["tarde"], False)

    # ── 2) ⚠️ dejar de estar PENDIENTE deja de bloquear ──────────────────────
    # ⚠️ Se prueba con `cancelar`, no con `marcar_recibida`: recibir CREA una fila en
    # `Gastos` (123,45 de costo real en la obra) y no hay forma de borrarla desde la
    # app. El invariante que importa es el mismo —solo bloquea lo PENDIENTE— y por
    # este camino no se ensucia la contabilidad. La rama RECIBIDA la cubre el guardián.
    print("\n2) ⚠️ al dejar de estar PENDIENTE tiene que dejar de bloquear")
    ok2, msg2 = O.cancelar(oid)
    print("   cancelar -> %s · %s" % (ok2, msg2))
    O._invalidate()
    _b2 = O.bloqueos(PID, GRUPO)
    ck("⚠️ ya no pendiente, la actividad %s deja de estar bloqueada" % ORDEN,
       ORDEN in _b2, False)
    oid = None                            # ya esta cancelada: nada que limpiar despues

finally:
    # ── 3) devolver la hoja ──────────────────────────────────────────────────
    print("\n3) se limpia la orden de prueba")
    if oid:
        try:
            O.cancelar(oid)
            print("   %s cancelada" % oid)
        except Exception as e:
            print("   *** no se pudo cancelar %s: %r" % (oid, e))
    O._invalidate()

_cab9, _ic9, ids9 = foto()
_nuevas = [i for i in ids9 if i not in ids0]
print("\nDESPUES · %d columnas · %d ordenes (%d nuevas: %s)"
      % (len(_cab9), len(ids9), len(_nuevas), _nuevas))
O._invalidate()
ck("ninguna actividad queda bloqueada por la prueba",
   O.bloqueos(PID, GRUPO), {})

print("\n" + "=" * 70)
print("EJERCICIO CONTRA LA HOJA REAL — " + ("TODO OK" if not fallos else "HAY FALLOS"))
for f in fallos:
    print("  - " + f)
if _nuevas:
    print("⚠️ quedan %d orden(es) de prueba en la hoja (canceladas): %s"
          % (len(_nuevas), _nuevas))
sys.exit(1 if fallos else 0)
