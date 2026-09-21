# -*- coding: utf-8 -*-
"""v510 contra la HOJA REAL (método v344): la columna, la migración y el documento.

  foto de `Claims` → forzar la migración → comprobar que «Type» se creó AL FINAL →
  leer de vuelta las filas que ya había → generar el PDF de una reclamación REAL →
  segunda foto

⚠️ Lo que este ejercicio NO prueba: emitir una liberación de verdad. Para eso hace
falta una obra al 100% CON retención acumulada, y crearla implicaría aceptar una
cotización en el cliente de prueba — que es justo la basura que dejó `verif_v370` en
rojo en v509. La escritura está cubierta en `verif_v510` con la hoja sustituida, que
comprueba la fila entera campo por campo. Decirlo importa: un ejercicio que aparenta
probar más de lo que prueba es peor que uno corto (nº30).

⚠️ Lo que SÍ prueba con datos reales, y es lo que no se puede simular: que la columna
se cree sola al final de una hoja que YA TIENE FILAS, que esas filas seleccionen a
leerse con la clave nueva vacía en vez de romperse, y que el PDF se genere a partir de
una fila tal y como sale de Sheets —con todo en texto— y no de un dict bonito mío.
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
from core import claims as CL                                     # noqa: E402
from core import claim_pdf as PDF                                 # noqa: E402

GRUPO = "cliente1"
fallos = []


def ck(q, real, esp):
    if real == esp:
        print("  ok   %s" % q)
    else:
        fallos.append(q)
        print("  *** FALLO  %s  -> %r != %r" % (q, real, esp))


def _libro():
    """⚠️ SOLO LECTURA: este ejercicio no escribe ni una fila, así que ni pide permiso
    de escritura. El único cambio que provoca es la columna, y la hace la app."""
    cr = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    gc = gspread.authorize(cr)
    lib = gc.open_by_key(st.secrets["TIMECLOCK_SHEET_ID"])
    grp = lib.worksheet("Groups").get_all_values()
    sid = [f[grp[0].index("SheetID")] for f in grp[1:] if f and f[0] == GRUPO][0]
    return gc.open_by_key(sid)


def foto():
    """⚠️ Si no se puede leer se ABORTA: una foto vacía aprueba cualquier cosa, que es
    como el ejercicio de v505 pasó en falso la primera vez."""
    try:
        v = _libro().worksheet(CL.RECLAMACIONES).get_all_values()
    except Exception as e:
        raise SystemExit("no se pudo leer %r: %r (la foto seria falsa)"
                         % (CL.RECLAMACIONES, e))
    if not v or not v[0]:
        raise SystemExit("la hoja %r no tiene cabecera: la foto no vale" % CL.RECLAMACIONES)
    cab = v[0]
    return cab, [f[0] for f in v[1:] if f]


cab0, ids0 = foto()
print("ANTES · %d columnas · «Type»: %s · %d reclamaciones"
      % (len(cab0), "Type" in cab0, len(ids0)))

# ── 1) la migración: la columna la crea la propia app ────────────────────────
print("\n1) se fuerza la migracion de la cabecera")
_w = CL._ws(CL.RECLAMACIONES, CL.C_HEADERS)
ck("la hoja se abre", _w is not None, True)
CL._invalidate()

cab1, ids1 = foto()
print("   ahora %d columnas: %s" % (len(cab1), cab1[-3:]))
ck("«Type» existe", "Type" in cab1, True)
ck("...y va AL FINAL (v363)", cab1[-1], "Type")
ck("no se perdio ninguna fila por el camino", ids1, ids0)

# ── 2) las filas que YA estaban se leen con la clave nueva ───────────────────
print("\n2) lo que ya habia, leido de vuelta")
_rs = [r for r in (CL._records(CL.RECLAMACIONES) or [])]
ck("se leen todas las filas", len(_rs), len(ids1))
if _rs:
    ck("...y ninguna revienta al preguntar por su clase",
       [r for r in _rs if CL.es_liberacion(r) not in (True, False)], [])
    ck("⚠️ una fila anterior a v510 NO se toma por liberacion",
       any(CL.es_liberacion(r) for r in _rs if str(r.get("Type", "")) == ""), False)
else:
    print("  (la hoja no tiene reclamaciones: lo de abajo se salta)")

# ── 3) una obra de prueba: escribir, leer de vuelta, liberar y limpiar ───────
# ⚠️ La primera versión de este ejercicio se conformaba con lo de arriba y la hoja real
# tiene CERO reclamaciones, así que los apartados 2 y 3 se saltaban enteros y el
# ejercicio terminaba en «TODO OK» sin haber probado ni el ida y vuelta de la columna
# ni el PDF. Un verde que solo significa «no había datos» es el paso en vacío (nº1).
PID = "PRJ-V510-TEST"
PRJ = {"ID": PID, "Name": "Ejercicio v510", "Progress": "100"}
_creadas = []


def _hoja_escritura():
    cr = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets"])
    gc = gspread.authorize(cr)
    lib = gc.open_by_key(st.secrets["TIMECLOCK_SHEET_ID"])
    grp = lib.worksheet("Groups").get_all_values()
    sid = [f[grp[0].index("SheetID")] for f in grp[1:] if f and f[0] == GRUPO][0]
    return gc.open_by_key(sid).worksheet(CL.RECLAMACIONES)


print("\n3) una reclamacion de prueba, escrita a mano en la hoja")
_ws_real = _hoja_escritura()
# Se siembra DIRECTA porque emitirla con `crear_reclamacion` exigiría una cotización
# aceptada, y aceptar cotizaciones en el cliente de prueba es la basura que dejó
# `verif_v370` en rojo en v509. Lo que aquí importa es la fila, no cómo nació.
_fila_prueba = ["CLM-%s-001" % PID, GRUPO, PID, "1", "2026-09-01", "2026-09-30",
                "100", "60000", "0", "60000", "0", "5", "3000", "60000",
                CL.EMITIDA, "Ejercicio v510", "Bobo", "2026-09-01 10:00", ""]
_ws_real.append_row(_fila_prueba, value_input_option="RAW")
_creadas.append(_fila_prueba[0])
CL._invalidate()

try:
    _mias = [r for r in (CL.reclamaciones(PID) or [])]
    ck("la reclamacion se lee de vuelta desde la hoja", len(_mias), 1)
    ck("⚠️ con la columna nueva VACIA, no como liberacion",
       CL.es_liberacion(_mias[0]) if _mias else "(no hay fila)", False)
    _ret = CL.retenido(PID)
    ck("lo retenido sale de la hoja real", _ret["retenido"], 3000.0)
    ck("...y todo sigue pendiente", _ret["pendiente"], 3000.0)

    # ── 4) la liberacion, con el ESCRITOR DE LA APP ──────────────────────────
    print("\n4) la liberacion, escrita por la app contra la hoja real")
    _ok_l, _msg_l = CL.crear_liberacion(PID, GRUPO, 1200, "Primera mitad", "Bobo", PRJ)
    print("   crear_liberacion -> %s · %s" % (_ok_l, _msg_l))
    ck("se emite", _ok_l, True)
    _tras = [r for r in (CL.reclamaciones(PID) or [])]
    _lib = [r for r in _tras if CL.es_liberacion(r)]
    ck("⚠️ se lee de vuelta COMO liberacion (la columna viaja)", len(_lib), 1)
    if _lib:
        _creadas.append(str(_lib[0].get("ID", "")))
        ck("...sin retener nada", float(_lib[0].get("Retention") or 0), 0.0)
        ck("...por el importe pedido", float(_lib[0].get("ThisClaim") or 0), 1200.0)
    _ret2 = CL.retenido(PID)
    print("   retenido %.2f · liberado %.2f · pendiente %.2f"
          % (_ret2["retenido"], _ret2["liberado"], _ret2["pendiente"]))
    ck("⚠️ el pendiente baja en la hoja real", _ret2["pendiente"], 1800.0)
    ck("...y lo retenido NO cambia", _ret2["retenido"], 3000.0)
    _ok2, _mot2 = CL.puede_liberar(PID, PRJ)
    ck("todavia se puede pedir la otra mitad", _ok2, True)

    # ── 5) el PDF sobre las filas REALES ─────────────────────────────────────
    print("\n5) los dos documentos, desde filas de Sheets")
    from io import BytesIO
    from pypdf import PdfReader

    def _txt(b):
        return "\n".join((p.extract_text() or "")
                         for p in PdfReader(BytesIO(b)).pages)

    _avance = [r for r in _tras if not CL.es_liberacion(r)]
    _b1 = PDF.generate_claim_pdf(_avance[0] if _avance else {}, CL.variaciones(PID),
                                 {}, GRUPO, PRJ, _ret2)
    _t1 = _txt(_b1)
    ck("⚠️ la sonda sabe leer el PDF real", "PROGRESS CLAIM" in _t1.upper(), True)
    ck("la reclamacion lleva su neto", "57,000.00" in _t1, True)
    _b2 = PDF.generate_claim_pdf(_lib[0] if _lib else {}, CL.variaciones(PID), {},
                                 GRUPO, PRJ, _ret2)
    _t2 = _txt(_b2)
    ck("la liberacion se titula distinto", "RETENTION RELEASE" in _t2.upper(), True)
    ck("...y dice lo que queda retenido", "1,800.00" in _t2, True)
    print("   %d y %d bytes" % (len(_b1), len(_b2)))

finally:
    # ── 6) devolver la hoja como estaba ──────────────────────────────────────
    print("\n6) se borran las filas de prueba")
    try:
        _v = _ws_real.get_all_values()
        _n = [i for i, f in enumerate(_v[1:], start=2)
              if f and (f[0] in _creadas or (len(f) > 2 and f[2] == PID))]
        for i in sorted(_n, reverse=True):
            _ws_real.delete_rows(i)
        print("   borradas %d fila(s)" % len(_n))
    except Exception as e:
        print("   *** NO se pudo limpiar: %r" % e)
        fallos.append("quedo basura en la hoja")
    CL._invalidate()

cab9, ids9 = foto()
print("\nDESPUES · %d columnas · %d reclamaciones" % (len(cab9), len(ids9)))
ck("no se creo ni se borro ninguna fila", ids9, ids0)

print("\n" + "=" * 70)
print("PDF DE RECLAMACION Y RETENCION, HOJA REAL — "
      + ("TODO OK" if not fallos else "HAY FALLOS"))
for f in fallos:
    print("  - " + f)
sys.exit(1 if fallos else 0)
