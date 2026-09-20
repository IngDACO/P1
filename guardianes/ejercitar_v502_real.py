# -*- coding: utf-8 -*-
"""v502 contra la HOJA REAL (método v344): foto → poner responsable → verificar leyendo
→ ⚠️ GUARDADO PARCIAL (la prueba que importa) → restaurar → segunda foto.

Lo que se viene a probar contra datos de verdad, no contra mis mocks:
  (a) que la columna «Owner» se crea sola al final, sin descuadrar las filas que ya están;
  (b) que el responsable se guarda y se relee;
  (c) ⚠️ que un guardado PARCIAL —el patrón del campo, v162— NO lo borra. Esto es lo que
      ningún test con datos inventados puede afirmar de la hoja de verdad.
Obra de prueba en `cliente1`. Todo lo escrito se devuelve a su valor original.
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
from core import projects as P                                    # noqa: E402
from core import auth                                             # noqa: E402

PID = "PRJ-0001"


def foto():
    """⚠️ SOLO LECTURA: los helpers de la app MIGRAN cabeceras al acceder (v145), así que
    una «foto» hecha con ellos ya sería una escritura."""
    c = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    gc = gspread.authorize(c)
    lib = gc.open_by_key(st.secrets["TIMECLOCK_SHEET_ID"])
    grp = lib.worksheet("Groups").get_all_values()
    sid = [f[grp[0].index("SheetID")] for f in grp[1:] if f and f[0] == "cliente1"][0]
    v = gc.open_by_key(sid).worksheet("Activities").get_all_values()
    cab = v[0]
    ico = cab.index("Owner") if "Owner" in cab else -1
    ino = cab.index("Name") if "Name" in cab else -1
    filas = [f for f in v[1:] if f and f[0] == PID]
    return cab, ico, [(f[1] if len(f) > 1 else "",
                       f[ino] if ino >= 0 and len(f) > ino else "",
                       f[ico] if ico >= 0 and len(f) > ico else "") for f in filas]


cab0, ico0, filas0 = foto()
print("ANTES · %d columnas · «Owner» en la hoja: %s (idx %d)"
      % (len(cab0), ico0 >= 0, ico0))
print("        actividades de %s: %s" % (PID, filas0))

acts = P.list_activities(PID)          # ⚠️ este acceso CREA la columna si falta (migración)
if not acts:
    raise SystemExit("la obra %s no tiene actividades: no hay nada que ejercitar" % PID)
orden0 = acts[0].get("Order")
nombre0 = acts[0].get("Name")
dueno0 = str(acts[0].get("Owner", "") or "")
print("\ntras la migración: %d columnas · actividad %s = %r · responsable %r"
      % (len(P.ACTIVITIES_HEADERS), orden0, nombre0, dueno0))

_us = [u.get("User") for u in (auth.list_users("cliente1") or []) if u.get("User")]
NUEVO = next((u for u in _us if u != dueno0), "bobo")
print("responsable de prueba: %r  (de %d usuarios del grupo)" % (NUEVO, len(_us)))

fallos = []


def ck(q, real, esp):
    if real == esp:
        print("  ok   %s" % q)
    else:
        fallos.append(q)
        print("  *** FALLO  %s  -> %r != %r" % (q, real, esp))


try:
    # ── 1) poner el responsable y releerlo DE LA HOJA ────────────────────────
    print("\n1) se pone el responsable")
    ok, msg = P.save_activities(PID, [{"orden0": orden0, "Owner": NUEVO}])
    print("   save_activities -> %s · %s" % (ok, msg))
    _, ico, filas = foto()
    ck("«Owner» existe en la hoja y es la ULTIMA columna", ico, len(cab0) if ico0 < 0 else ico0)
    ck("el responsable quedó escrito en la hoja",
       next((d for o, n, d in filas if o == str(orden0)), None), NUEVO)
    ck("la app lo relee igual",
       str(next(a for a in P.list_activities(PID) if a.get("Order") == orden0)
           .get("Owner", "")), NUEVO)

    # ── 2) ⚠️ GUARDADO PARCIAL: la prueba que importa ────────────────────────
    print("\n2) ⚠️ guardado PARCIAL (sin la clave Owner): no puede borrarlo")
    ok, msg = P.save_activities(PID, [{"orden0": orden0,
                                       "Name": str(nombre0) + " (tocada)"}])
    print("   save_activities -> %s · %s" % (ok, msg))
    _, _, filas = foto()
    _fila = next(((n, d) for o, n, d in filas if o == str(orden0)), (None, None))
    ck("el nombre SÍ cambió (el guardado parcial hizo algo)",
       _fila[0], str(nombre0) + " (tocada)")
    ck("⚠️ y el responsable SIGUE AHÍ", _fila[1], NUEVO)

finally:
    # ── 3) devolver todo a su sitio ──────────────────────────────────────────
    print("\n3) se devuelve la obra a su estado")
    P.save_activities(PID, [{"orden0": orden0, "Name": nombre0, "Owner": dueno0}])

cab9, ico9, filas9 = foto()
print("\nDESPUES · %d columnas · actividades: %s" % (len(cab9), filas9))
ck("la obra quedó como estaba (nombres y responsables)",
   [(o, n, d) for o, n, d in filas9], [(o, n, d) for o, n, d in filas0]
   if ico0 >= 0 else [(o, n, "") for o, n, d in filas0])

print("\n" + "=" * 70)
print("EJERCICIO CONTRA LA HOJA REAL — " + ("TODO OK" if not fallos else "HAY FALLOS"))
for f in fallos:
    print("  - " + f)
sys.exit(1 if fallos else 0)
