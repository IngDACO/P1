"""EJERCICIO de la ESCRITURA DEL CAMPO — `projects.save_field_progress`.

Es el único camino por el que el campo escribe en la app (v162: una tabla, un
guardado). Se ejercitan sus 6 ramas contra la hoja REAL y se devuelve todo.

⚠️ Sospecha a probar (leyendo el código, sin afirmarla aún):
    aws.batch_update(...)         # escribe las actividades
    _recompute_project_avance(pid)   # ← lee `list_activities`, que está CACHEADA
    _invalidate()                    # ← la caché se tira DESPUÉS
Si la caché está caliente —y lo está siempre, porque la pantalla acaba de pintar
esa misma tabla para editarla— el % del proyecto se recalcularía con los avances
VIEJOS. El camino viejo (`update_activity_progress`) lo hacía bien: recomputaba
en memoria sobre las filas que acababa de leer frescas.
"""
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import gspread                                             # noqa: E402
import streamlit as st                                     # noqa: E402
from google.oauth2.service_account import Credentials      # noqa: E402

st.session_state["auth"] = {"usuario": "jlopez", "grupo": "cliente1", "rol": "campo"}

from core import projects as P, clock                      # noqa: E402

PID = "PRJ-0011"
G = "cliente1"
HOY = clock.today(G).isoformat()
ok_global = True

# ── lector CRUDO en solo lectura (regla v145: los helpers migran cabeceras) ──
RO = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
_gc = gspread.authorize(Credentials.from_service_account_info(
    dict(st.secrets["gcp_service_account"]), scopes=RO))
_libro = _gc.open_by_key(st.secrets["TIMECLOCK_SHEET_ID"])


def crudo():
    """(actividades del proyecto por orden, fila del proyecto) — sin pasar por la app."""
    act = _libro.worksheet("Actividades").get_all_records(numericise_ignore=["all"])
    prj = _libro.worksheet("Proyectos").get_all_records(numericise_ignore=["all"])
    a = {str(r.get("Orden")): r for r in act if str(r.get("ProyectoID")) == PID}
    p = next((r for r in prj if str(r.get("ID")) == PID), {})
    return a, p


def pinta(a, titulo):
    print(f"\n   {titulo}")
    for k in sorted(a, key=lambda x: int(x)):
        r = a[k]
        print(f"      orden={k:>3} av={str(r.get('Avance')):>6} "
              f"ini={str(r.get('FechaInicioReal')) or '—':<11} "
              f"fin={str(r.get('FechaFinReal')) or '—':<11} nota={str(r.get('Nota'))[:16]!r}")


def esperado(a):
    """El % que DEBERÍA tener el proyecto según las actividades que hay AHORA."""
    return P.compute_avance(list(a.values()))


print("=" * 74)
print("FOTO DEL ANTES")
print("=" * 74)
A0, P0 = crudo()
pinta(A0, f"{PID} — {P0.get('Nombre')}")
print(f"\n   proyecto: Avance={P0.get('Avance')} Estado={P0.get('Estado')} "
      f"EstadoManual={P0.get('EstadoManual')!r}")
BASE_AV, BASE_EST = str(P0.get("Avance")), str(P0.get("Estado"))

# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 74)
print("RONDA 1 — las ramas de v162, con la CACHÉ CALIENTE (como en la app)")
print("=" * 74)
# La pantalla del campo pinta la tabla ANTES de guardar, así que cuando se pulsa
# «Guardar avances» la caché de actividades lleva ya los valores viejos dentro.
_ = P.list_activities(PID)
_ = P.get_project(PID)
print("   (caché calentada: la app acaba de pintar esta misma tabla para editarla)")

cambios = [
    {"orden": "1", "avance": 40,  "nota": "arranca hoy"},   # 0→>0 : pone inicio real
    {"orden": "2", "avance": 100},                          # 0→100: inicio Y fin
    {"orden": "3", "avance": 0,   "nota": "sin empezar"},   # sigue en 0: solo nota
    {"orden": "4", "avance": 150},                          # fuera de rango → 100
    {"orden": "5", "avance": -5},                           # fuera de rango → 0
    {"orden": "99", "avance": 50},                          # no existe → se ignora
]
ok, msg = P.save_field_progress(PID, cambios)
print(f"   save_field_progress → {ok} · {msg}")
ok_global &= ok

A1, P1 = crudo()
pinta(A1, "DESPUÉS de la ronda 1 (leído en crudo)")

print("\n   -- comprobación de cada rama --")
# ⚠️ Comparar NUMÉRICO, no como texto: la hoja guarda `str(float)`, así que 40
#    se lee "40.0" y `"40.0" == "40"` da un FALLO EN FALSO (me pasó en la 1ª
#    pasada: 5 ✗ que eran de mi test, no del código).
casos = [
    ("1", 40,  HOY, "",   "arranca: avance + inicio real, sin fin"),
    ("2", 100, HOY, HOY,  "de 0 a 100 de una: inicio Y fin el mismo día"),
    ("3", 0,   "",  "",   "sigue en 0: NO se inventa fecha de inicio"),
    ("4", 100, HOY, HOY,  "150 se recorta a 100"),
    ("5", 0,   "",  "",   "-5 se recorta a 0"),
]
for orden, av, fi, ff, que in casos:
    r = A1[orden]
    bien = (abs(P._num(r.get("Avance")) - av) < 0.001
            and str(r.get("FechaInicioReal")) == fi
            and str(r.get("FechaFinReal")) == ff)
    ok_global &= bien
    print(f"      {'✓' if bien else '✗'} orden {orden}: {que}")
    if not bien:
        print(f"          esperaba av={av} ini={fi!r} fin={ff!r} · "
              f"salió av={r.get('Avance')} ini={r.get('FechaInicioReal')!r} "
              f"fin={r.get('FechaFinReal')!r}")
_n3 = str(A1["3"].get("Nota"))
print(f"      {'✓' if _n3 == 'sin empezar' else '✗'} la nota se guarda ({_n3!r})")
ok_global &= _n3 == "sin empezar"
_sin99 = "99" not in A1
print(f"      {'✓' if _sin99 else '✗'} el orden inexistente se ignora sin romper")
ok_global &= _sin99

# ── ⚠️ el % del proyecto ──
print("\n   -- ⚠️ el % del PROYECTO --")
_esp = esperado(A1)
_real = P._num(P1.get("Avance"))
print(f"      actividades en la hoja  → el proyecto DEBERÍA ir al {_esp}%")
print(f"      lo que la app escribió  → {_real}%")
if abs(_esp - _real) < 0.05:
    print("      ✓ coinciden")
else:
    ok_global = False
    print(f"      ‼️ NO coinciden: se quedó {_esp - _real:.1f} puntos por detrás")
    print("         → `_recompute_project_avance` corre ANTES de `_invalidate()`,")
    print("           así que recalcula con las actividades de la CACHÉ (las viejas).")
    print(f"      estado escrito: {P1.get('Estado')!r} (con {_esp}% debería ser "
          f"{P.derive_estado(_esp, str(P0.get('EstadoManual','')))!r})")

# ── ¿es la caché? prueba de causa: mismo guardado, caché FRÍA ──
print("\n   -- prueba de causa: repetir con la caché FRÍA --")
P._invalidate()
time.sleep(1)
ok2, _ = P.save_field_progress(PID, [{"orden": "1", "avance": 41}])
A1b, P1b = crudo()
_esp2, _real2 = esperado(A1b), P._num(P1b.get("Avance"))
print(f"      con la caché vacía → esperado {_esp2}% · escrito {_real2}%  "
      f"{'✓ coincide' if abs(_esp2 - _real2) < 0.05 else '✗'}")
print("      (si con la caché fría coincide y con la caliente no, la causa es el ORDEN)")

# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 74)
print("RONDA 2 — reapertura: una actividad al 100% que baja")
print("=" * 74)
_ = P.list_activities(PID)                    # caché caliente otra vez
ok3, msg3 = P.save_field_progress(PID, [{"orden": "2", "avance": 60}])
print(f"   save_field_progress → {ok3} · {msg3}")
A2, _P2 = crudo()
r2 = A2["2"]
_reab = (abs(P._num(r2.get("Avance")) - 60) < 0.001
         and str(r2.get("FechaFinReal")) == ""
         and str(r2.get("FechaInicioReal")) == HOY)
ok_global &= _reab
print(f"   {'✓' if _reab else '✗'} al reabrir se BORRA el fin real y se CONSERVA el inicio "
      f"(av={r2.get('Avance')} ini={r2.get('FechaInicioReal')!r} fin={r2.get('FechaFinReal')!r})")

# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 74)
print("RONDA 3 — completar una que YA tenía inicio (no debe reescribirlo)")
print("=" * 74)
ok4, msg4 = P.save_field_progress(PID, [{"orden": "1", "avance": 100}])
print(f"   save_field_progress → {ok4} · {msg4}")
A3, _P3 = crudo()
r1 = A3["1"]
_comp = (abs(P._num(r1.get("Avance")) - 100) < 0.001
         and str(r1.get("FechaInicioReal")) == HOY     # el de la ronda 1, sin tocar
         and str(r1.get("FechaFinReal")) == HOY)
ok_global &= _comp
print(f"   {'✓' if _comp else '✗'} conserva el inicio original y pone el fin "
      f"(ini={r1.get('FechaInicioReal')!r} fin={r1.get('FechaFinReal')!r})")

# ── sin cambios ──
ok5, msg5 = P.save_field_progress(PID, [])
print(f"\n   lista vacía → {ok5} · {msg5!r}  "
      f"{'✓ no escribe nada' if 'Sin cambios' in msg5 else '✗'}")
ok_global &= "Sin cambios" in msg5

# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 74)
print("DEVOLVER TODO A SU SITIO")
print("=" * 74)
aws, err = P._activities_ws()
if err:
    print(f"   ‼️ no se pudo abrir Actividades: {err}")
    ok_global = False
else:
    recs = aws.get_all_records(numericise_ignore=["all"])
    filas = {str(r.get("Orden")): i + 2 for i, r in enumerate(recs)
             if str(r.get("ProyectoID")) == PID}
    batch = []
    for orden, orig in A0.items():
        fila = filas.get(orden)
        if not fila:
            continue
        for campo in ("Avance", "FechaInicioReal", "FechaFinReal", "Nota"):
            batch.append({"range": f"{P._col_letter(P._ACOL[campo])}{fila}",
                          "values": [[str(orig.get(campo, ""))]]})
    aws.batch_update(batch, value_input_option="RAW")
    P._invalidate()
    P.update_project(PID, {"Avance": P._num(BASE_AV), "Estado": BASE_EST})
    P._invalidate()

AF, PF = crudo()
pinta(AF, "ESTADO FINAL")
print(f"\n   proyecto: Avance={PF.get('Avance')} Estado={PF.get('Estado')}")
_igual = all(
    str(AF[k].get(c, "")) == str(A0[k].get(c, ""))
    for k in A0 for c in ("Avance", "FechaInicioReal", "FechaFinReal", "Nota")
) and P._num(PF.get("Avance")) == P._num(BASE_AV) and str(PF.get("Estado")) == BASE_EST
ok_global &= _igual
print(f"   {'✓ TODO devuelto, sin rastro' if _igual else '‼️ QUEDÓ RASTRO — revisar'}")

print("\n" + "=" * 74)
print("✅ escritura del campo verificada" if ok_global else "⚠️ HAY HALLAZGOS — ver arriba")
