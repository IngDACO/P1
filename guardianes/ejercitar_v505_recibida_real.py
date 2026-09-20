# -*- coding: utf-8 -*-
"""v505 · la rama RECIBIDA contra la HOJA REAL (método v344).

Es la que quedó sin ejercitar el 20/09: recibir una orden **crea una fila en `Expenses`**
y la app no sabe borrarla, así que se probó con `cancelar`. Aquí se prueba de verdad, y
se limpia a mano lo que la app no puede: la fila del gasto y la de la orden.

  foto de LAS DOS hojas → crear ligada → bloquea → RECIBIR → deja de bloquear
  → borrar gasto + orden → segunda foto IDÉNTICA a la primera

⚠️ Toca contabilidad de la obra de prueba. Si algo falla a medias, el resumen dice qué
quedó suelto y con qué ID, para no dejar un gasto fantasma sin que nadie se entere.
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
from core import expenses as E                                    # noqa: E402
from core import projects as P                                    # noqa: E402

PID, GRUPO, PROV = "PRJ-0001", "cliente1", "PRUEBA v505 RECIBIDA"


def _libro(escribir=False):
    sc = ["https://www.googleapis.com/auth/spreadsheets"] if escribir else \
         ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    c = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=sc)
    gc = gspread.authorize(c)
    lib = gc.open_by_key(st.secrets["TIMECLOCK_SHEET_ID"])
    grp = lib.worksheet("Groups").get_all_values()
    sid = [f[grp[0].index("SheetID")] for f in grp[1:] if f and f[0] == GRUPO][0]
    return gc.open_by_key(sid)


def foto():
    """⚠️ SOLO LECTURA, y si una hoja no se puede leer se ABORTA: una foto vacía
    aprobaría cualquier cosa (la trampa nº1, que ya mordió en el ejercicio hermano)."""
    lb = _libro()
    out = {}
    for hoja in (O.SHEET, E.SHEET):
        try:
            v = lb.worksheet(hoja).get_all_values()
        except Exception as e:
            raise SystemExit("no se pudo leer %r: %r (la foto seria falsa)" % (hoja, e))
        if not v or not v[0]:
            raise SystemExit("la hoja %r no tiene cabecera: la foto no vale" % hoja)
        out[hoja] = (len(v[0]), [f[0] for f in v[1:] if f])
    return out


fallos, oid, gid = [], None, None


def ck(q, real, esp):
    if real == esp:
        print("  ok   %s" % q)
    else:
        fallos.append(q)
        print("  *** FALLO  %s  -> %r != %r" % (q, real, esp))


f0 = foto()
print("ANTES · %s: %d cols, %d filas · %s: %d cols, %d filas"
      % (O.SHEET, f0[O.SHEET][0], len(f0[O.SHEET][1]),
         E.SHEET, f0[E.SHEET][0], len(f0[E.SHEET][1])))

acts = P.list_activities(PID)
ORDEN = int(P._num(acts[1].get("Order")))
print("        se ligara a la actividad %s (%r)" % (ORDEN, acts[1].get("Name")))

try:
    print("\n1) crear la orden ligada")
    ok, msg = O.crear(PID, GRUPO, PROV, 77.77, descripcion="Material de prueba (v505)",
                      fecha_esperada="2026-12-31", creado_por="Bobo", actividad=str(ORDEN))
    ck("la orden se creo", ok, True)
    oid = msg.split()[1]
    O._invalidate()
    ck("bloquea la actividad %s" % ORDEN, ORDEN in O.bloqueos(PID, GRUPO), True)

    print("\n2) ⚠️ RECIBIRLA (esto crea el gasto)")
    ok2, msg2 = O.marcar_recibida(oid, creado_por="Bobo")
    print("   marcar_recibida -> %s · %s" % (ok2, msg2))
    ck("se recibio", ok2, True)
    O._invalidate()
    E._invalidate() if hasattr(E, "_invalidate") else None
    ck("⚠️ recibida, deja de bloquear", ORDEN in O.bloqueos(PID, GRUPO), False)

    _r = [x for x in O.list_for(PID) if str(x.get("ID")) == oid]
    gid = str(_r[0].get("ExpenseID", "")).strip() if _r else ""
    ck("...y quedo enlazada a su gasto", bool(gid), True)
    print("   gasto creado: %s" % gid)

finally:
    print("\n3) limpiar lo que la app no sabe borrar")
    lb = _libro(escribir=True)
    for hoja, col, val in ((E.SHEET, "ID", gid), (O.SHEET, "ID", oid)):
        if not val:
            continue
        try:
            ws = lb.worksheet(hoja)
            v = ws.get_all_values()
            i = v[0].index(col)
            filas = [n for n, f in enumerate(v[1:], start=2) if len(f) > i and f[i] == val]
            for n in sorted(filas, reverse=True):
                ws.delete_rows(n)
            print("   %s: borrada(s) %d fila(s) de %s" % (hoja, len(filas), val))
        except Exception as e:
            print("   *** NO se pudo limpiar %s en %s: %r" % (val, hoja, e))
    O._invalidate()

f9 = foto()
print("\nDESPUES · %s: %d cols, %d filas · %s: %d cols, %d filas"
      % (O.SHEET, f9[O.SHEET][0], len(f9[O.SHEET][1]),
         E.SHEET, f9[E.SHEET][0], len(f9[E.SHEET][1])))
ck("la hoja de ordenes quedo como estaba", f9[O.SHEET], f0[O.SHEET])
ck("la de gastos tambien (no queda contabilidad de prueba)", f9[E.SHEET], f0[E.SHEET])
O._invalidate()
ck("ninguna actividad queda bloqueada", O.bloqueos(PID, GRUPO), {})

print("\n" + "=" * 70)
print("RAMA RECIBIDA CONTRA LA HOJA REAL — " + ("TODO OK" if not fallos else "HAY FALLOS"))
for f in fallos:
    print("  - " + f)
sys.exit(1 if fallos else 0)
