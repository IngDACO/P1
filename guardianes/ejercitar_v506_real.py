# -*- coding: utf-8 -*-
"""v506 contra la HOJA REAL (método v344): el expediente de una obra de verdad.

  foto de Documentos → leer el expediente como lo ve la pantalla → adjuntar un documento
  contra un ítem de tercero → ver que ese ítem pasa a OK → borrar la fila → segunda foto

Lo que se viene a probar con datos de verdad, no con contextos que yo invento:
  (a) que la columna «HandoverItem» se cree sola al final, sin descuadrar las filas que
      ya estén en Documentos;
  (b) que el RECOLECTOR (`handover_ui.contexto`) reúna la obra real sin lanzar — es el
      trozo que los mocks no tocan;
  (c) ⚠️ que un ítem de tercero pase a OK **solo** cuando hay un documento contra él.

⚠️ No se sube nada a Drive: se registra la fila con un DriveID de prueba y se borra. El
expediente no lee Drive para decidir el estado, así que la prueba es válida.
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
from core import handover as H                                    # noqa: E402
from core import handover_ui as HU                                # noqa: E402
from core import projects as P                                    # noqa: E402

PID, GRUPO = "PRJ-0001", "cliente1"
ITEM, MARCA = "safe_to_operate", "PRUEBA v506.pdf"


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
    """⚠️ SOLO LECTURA, y si no se puede leer se ABORTA: una foto vacía aprueba
    cualquier cosa (es como el ejercicio de v505 pasó en falso la primera vez)."""
    try:
        v = _libro().worksheet(P.DOCUMENTS_SHEET).get_all_values()
    except Exception as e:
        raise SystemExit("no se pudo leer %r: %r (la foto seria falsa)" % (P.DOCUMENTS_SHEET, e))
    if not v or not v[0]:
        raise SystemExit("la hoja %r no tiene cabecera: la foto no vale" % P.DOCUMENTS_SHEET)
    cab = v[0]
    ic = cab.index("HandoverItem") if "HandoverItem" in cab else -1
    return cab, ic, [f[1] if len(f) > 1 else "" for f in v[1:] if f]


fallos = []


def ck(q, real, esp):
    if real == esp:
        print("  ok   %s" % q)
    else:
        fallos.append(q)
        print("  *** FALLO  %s  -> %r != %r" % (q, real, esp))


cab0, ic0, nombres0 = foto()
print("ANTES · %d columnas · «HandoverItem»: %s (idx %d) · %d documentos"
      % (len(cab0), ic0 >= 0, ic0, len(nombres0)))

prj = P.get_project(PID) or {}
if not prj:
    raise SystemExit("la obra %s no existe" % PID)

# ── 1) el expediente de la obra REAL, tal como lo ve la pantalla ─────────────
print("\n1) el expediente de %s, con sus datos de verdad" % PID)
ctx = HU.contexto(PID, GRUPO, prj)
filas = H.estado(ctx)
res = H.resumen(filas)
print("   resumen: %d en regla · %d parciales · %d faltan"
      % (res["ok"], res["parcial"], res["falta"]))
ck("el recolector devuelve los TRECE items", len(filas), 13)
ck("...y ninguno se queda sin estado",
   sorted({f["estado"] for f in filas}) != [], True)
for f in filas:
    if f["fuente"] == H.COPEX:
        print("      (%s) %-34s %-8s %s" % (f["letra"], f["nombre"][:34], f["estado"],
                                            f["detalle"][:52]))
for m in H.incoherencias(ctx):
    print("   ⚠️  %s" % m["texto"])

_antes = next(f["estado"] for f in filas if f["clave"] == ITEM)
ck("⚠️ el item de tercero empieza faltando", _antes, H.FALTA)

# ── 2) adjuntar un documento contra ese ítem ─────────────────────────────────
print("\n2) se adjunta un documento contra «%s»" % ITEM)
ok, msg = P.add_document(PID, MARCA, "certificado", "drive-id-de-prueba-v506",
                         "Bobo", handover_item=ITEM)
print("   add_document -> %s · %s" % (ok, msg))
ck("se registro", ok, True)
P._invalidate()

_cab, _ic, _nom = foto()
ck("«HandoverItem» existe y va AL FINAL", _ic, len(_cab) - 1)
ck("el documento esta en la hoja", MARCA in _nom, True)

ctx2 = HU.contexto(PID, GRUPO, prj)
_f2 = H.estado(ctx2)
ck("⚠️ ahora ese item pasa a OK", next(f["estado"] for f in _f2 if f["clave"] == ITEM), H.OK)
ck("...diciendo con qué documento",
   MARCA in next(f["detalle"] for f in _f2 if f["clave"] == ITEM), True)
ck("y NINGUN otro item de tercero se contagia",
   sorted({f["estado"] for f in _f2 if f["fuente"] == H.TERCERO and f["clave"] != ITEM}),
   [H.FALTA])

# ── 3) limpiar ───────────────────────────────────────────────────────────────
print("\n3) se borra la fila de prueba")
try:
    lb = _libro(escribir=True)
    ws = lb.worksheet(P.DOCUMENTS_SHEET)
    v = ws.get_all_values()
    i = v[0].index("Name")
    filas_p = [n for n, f in enumerate(v[1:], start=2) if len(f) > i and f[i] == MARCA]
    for n in sorted(filas_p, reverse=True):
        ws.delete_rows(n)
    print("   borradas %d fila(s)" % len(filas_p))
except Exception as e:
    print("   *** NO se pudo limpiar: %r" % e)
P._invalidate()

cab9, ic9, nombres9 = foto()
print("\nDESPUES · %d columnas · %d documentos" % (len(cab9), len(nombres9)))
ck("la hoja quedo como estaba", nombres9, nombres0)
ck("el item vuelve a faltar",
   next(f["estado"] for f in H.estado(HU.contexto(PID, GRUPO, prj)) if f["clave"] == ITEM),
   H.FALTA)

print("\n" + "=" * 70)
print("EXPEDIENTE CONTRA LA HOJA REAL — " + ("TODO OK" if not fallos else "HAY FALLOS"))
for f in fallos:
    print("  - " + f)
sys.exit(1 if fallos else 0)
