# -*- coding: utf-8 -*-
"""v509 contra la HOJA REAL (método v344): cotizar leyendo el plano.

  foto del catálogo → crear ítems CON regla → proponer sobre un plano → comprobar
  cantidades y la línea incompleta → borrar los ítems → segunda foto

⚠️ Lo que este ejercicio NO prueba: la extracción del PDF. Eso ya lo cubren el survey y
sus propios guardianes desde v137, y aquí haría falta un plano real que no tenemos en el
cliente de prueba. Se le pasa un plano ya extraído, que es la salida de `plan_data`.
Decirlo importa: un ejercicio que pretende probar más de lo que prueba es peor que uno
corto (la lección del «0» que solo vale para la forma medida, nº30).

Lo que SÍ prueba con datos reales: que la columna `QtyRule` se cree sola al final del
catálogo, que un ítem guardado con regla se lea de vuelta con ella, y que la propuesta
salga de los precios REALES del catálogo, no de unos inventados.
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
from core import catalogo as CAT                                  # noqa: E402
from core import quote_from_plan as QP                            # noqa: E402

GRUPO = "cliente1"
MARCA = "PRUEBA v509"
PLANO = {"ns": 8, "modelo": "3300", "rail": "T75-3/B"}

fallos, creados = [], []


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
    """⚠️ SOLO LECTURA, y si no se puede leer se ABORTA: una foto vacía aprueba
    cualquier cosa (es como el ejercicio de v505 pasó en falso la primera vez)."""
    try:
        v = _libro().worksheet(CAT.SHEET).get_all_values()
    except Exception as e:
        raise SystemExit("no se pudo leer %r: %r (la foto seria falsa)" % (CAT.SHEET, e))
    if not v or not v[0]:
        raise SystemExit("la hoja %r no tiene cabecera: la foto no vale" % CAT.SHEET)
    cab = v[0]
    ic = cab.index("QtyRule") if "QtyRule" in cab else -1
    return cab, ic, [f[0] for f in v[1:] if f]


cab0, ic0, ids0 = foto()
print("ANTES · %d columnas · «QtyRule»: %s (idx %d) · %d items"
      % (len(cab0), ic0 >= 0, ic0, len(ids0)))

try:
    # ── 1) items con regla, en el catálogo de verdad ─────────────────────────
    print("\n1) se crean tres items con regla")
    for nombre, costo, regla in ((MARCA + " movilizacion", 1500, QP.FIJA),
                                 (MARCA + " puerta rellano", 900, QP.POR_PARADA),
                                 (MARCA + " manual", 400, QP.MANUAL)):
        ok, cid = CAT.crear(GRUPO, nombre, CAT.PRODUCTO, costo_unit=costo,
                            descripcion=nombre, creado_por="Bobo", qty_rule=regla)
        print("   %-34s -> %s %s" % (nombre[:34], ok, cid))
        if ok:
            creados.append(cid)
    ck("se crearon los tres", len(creados), 3)
    CAT._invalidate()

    _cab, _ic, _ids = foto()
    ck("«QtyRule» existe y va AL FINAL", _ic, len(_cab) - 1)

    # ⚠️ esto PRIMERO: sin leerlos de vuelta, lo de abajo pasaria en vacio (trampa nº1)
    _mios = [i for i in (CAT.list_items(GRUPO) or []) if str(i.get("ID")) in creados]
    ck("los items se leen de vuelta de la hoja", len(_mios), 3)
    ck("...con su regla guardada",
       sorted(str(i.get("QtyRule", "")) for i in _mios),
       sorted([QP.FIJA, QP.MANUAL, QP.POR_PARADA]))

    # ── 2) la propuesta, con precios REALES del catálogo ─────────────────────
    print("\n2) propuesta sobre un plano de 8 paradas")
    r = QP.proponer(PLANO, _mios)
    for l in r["lineas"]:
        print("   %-34s cant=%-5s precio=%s" % (l["descripcion"][:34], l["cantidad"],
                                                l["precio_total"]))
    ck("se proponen DOS (la manual no)", len(r["lineas"]), 2)
    ck("...y la manual se dice, no desaparece",
       [s for s in r["saltadas"] if MARCA in s], [MARCA + " manual"])
    _puerta = next((l for l in r["lineas"] if "puerta" in l["descripcion"]), None)
    ck("la puerta va 8 veces", _puerta["cantidad"] if _puerta else None, 8.0)
    ck("...a 900 cada una = 7.200", _puerta["precio_total"] if _puerta else None, 7200.0)

    # ── 3) ⚠️ el plano sin paradas: nada se omite ────────────────────────────
    print("\n3) ⚠️ el mismo catalogo con un plano SIN paradas")
    r2 = QP.proponer({"ns": None}, _mios)
    ck("⚠️ se proponen las MISMAS dos lineas", len(r2["lineas"]), len(r["lineas"]))
    _p2 = next((l for l in r2["lineas"] if "puerta" in l["descripcion"]), None)
    ck("...la puerta vale CERO, no 900", _p2["precio_total"] if _p2 else None, 0.0)
    ck("...y se dice por que", bool(_p2 and _p2.get("_falta")), True)
    ck("la movilizacion no depende del plano y sigue en 1.500",
       next((l["precio_total"] for l in r2["lineas"] if "movilizacion" in l["descripcion"]),
            None), 1500.0)

finally:
    # ── 4) devolver el catálogo ──────────────────────────────────────────────
    print("\n4) se borran los items de prueba")
    try:
        lb = _libro(escribir=True)
        ws = lb.worksheet(CAT.SHEET)
        v = ws.get_all_values()
        filas = [n for n, f in enumerate(v[1:], start=2) if f and f[0] in creados]
        for n in sorted(filas, reverse=True):
            ws.delete_rows(n)
        print("   borradas %d fila(s)" % len(filas))
    except Exception as e:
        print("   *** NO se pudo limpiar: %r" % e)
    CAT._invalidate()

cab9, ic9, ids9 = foto()
print("\nDESPUES · %d columnas · %d items" % (len(cab9), len(ids9)))
ck("el catalogo quedo como estaba", ids9, ids0)

print("\n" + "=" * 70)
print("COTIZAR DESDE EL PLANO, HOJA REAL — " + ("TODO OK" if not fallos else "HAY FALLOS"))
for f in fallos:
    print("  - " + f)
sys.exit(1 if fallos else 0)
