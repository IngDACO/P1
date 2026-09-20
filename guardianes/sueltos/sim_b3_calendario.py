"""SIMULACIÓN etapa B3 — corregir Estado y repartir el calendario.

Dos correcciones sobre B2:

1. ⚠️ `Estado` es una columna ALMACENADA, no derivada al leer. La app siempre la
   reescribe junto al avance (`_recompute_project_avance` hace
   `update_project(pid, {"Avance": .., "Estado": derive_estado(..)})`). Mi script
   escribió solo `Avance`, así que una obra al 100% seguía diciendo
   «Planificado». Fallo del script, NO de la app — pero deja ver una fragilidad:
   escribir `Avance` por su cuenta deja el estado mintiendo, sin ningún aviso.

2. `build_schedule(8 paradas)` da un plan de ~33 días, así que empezar las torres
   en junio las dejaba TODAS vencidas. Con 4 obras vencidas de 9 y ninguna sana
   no se puede juzgar el camino normal: la app se vería como un panel de
   catástrofes. Se mueven dos torres a agosto para que haya de los dos tipos.

Reparto final buscado: 3 en curso sanas · 2 vencidas · 1 empezada sin avance ·
2 completadas · 1 futura.
"""
import sys
from datetime import date, timedelta

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st
st.session_state["auth"] = {"usuario": "Bobo", "grupo": "cliente1", "rol": "administrador"}

from core import projects as P, timeclock as T                      # noqa: E402

G = "cliente1"
HOY = date(2026, 8, 18)
SHIFT = {"PRJ-0007": 61, "PRJ-0008": 54}      # días a mover (junio → agosto)


def _d(s):
    try:
        return date.fromisoformat(str(s)[:10])
    except Exception:
        return None


# ── 1) mover las fechas REALES de las actividades de las 2 torres ─
ws = T.get_sheet("Actividades", tuple(P.ACTIVITIES_HEADERS))
recs = ws.get_all_records(numericise_ignore=["all"])
peticiones, movidas = [], 0
for i, r in enumerate(recs):
    pid = str(r.get("ProyectoID", ""))
    if pid not in SHIFT:
        continue
    delta = timedelta(days=SHIFT[pid])
    ini, fin = _d(r.get("FechaInicioReal")), _d(r.get("FechaFinReal"))
    if not ini and not fin:
        continue
    # ⚠️ tope en HOY: una fecha real en el futuro sería un absurdo (dice cuándo
    #    PASÓ algo). Sin el tope, mover +61 días mandaría media obra a octubre.
    n_ini = min(ini + delta, HOY).isoformat() if ini else ""
    n_fin = min(fin + delta, HOY).isoformat() if fin else ""
    peticiones.append({"range": f"G{i + 2}:H{i + 2}", "values": [[n_ini, n_fin]]})
    movidas += 1

if peticiones:
    ws.batch_update(peticiones, value_input_option="RAW")
print(f"== B3.1 fechas reales movidas: {movidas} actividades en 1 batch ==")

# ── 2) fechas del proyecto + Estado coherente con el avance ──────
P._invalidate()
NUEVAS = [f"PRJ-{n:04d}" for n in range(7, 16)]
print("\n== B3.2 estado y fechas ==")
for pid in NUEVAS:
    prj = P.get_project(pid) or {}
    campos = {}
    if pid in SHIFT:
        delta = timedelta(days=SHIFT[pid])
        for col in ("FechaInicio", "FechaFinEst"):
            d = _d(prj.get(col))
            if d:
                campos[col] = (d + delta).isoformat()
    avance = float(str(prj.get("Avance", 0) or 0))
    # ⚠️ Estado y Avance SIEMPRE juntos, como hace `_recompute_project_avance`
    campos["Estado"] = P.derive_estado(avance, str(prj.get("EstadoManual", "") or ""))
    P.update_project(pid, campos)

P._invalidate()
print(f"\n{'ID':<10}{'NOMBRE':<36}{'ESTADO':<13}{'AVANCE':>7}  {'INICIO':<11}{'FIN':<11} SITUACIÓN")
for p in P.list_projects(G, incluir_archivados=True):
    pid = str(p.get("ID"))
    if pid not in NUEVAS:
        continue
    av = float(str(p.get("Avance", 0) or 0))
    fin = _d(p.get("FechaFinEst"))
    ini = _d(p.get("FechaInicio"))
    if av >= 100:
        sit = "✅ terminada"
    elif fin and fin < HOY:
        sit = f"🔴 VENCIDA hace {(HOY - fin).days} d"
    elif ini and ini > HOY:
        sit = "⏳ aún no arranca"
    elif av <= 0:
        sit = "⚠️ empezó y 0% de avance"
    else:
        sit = "🟢 en curso"
    print(f"{pid:<10}{str(p.get('Nombre'))[:34]:<36}{str(p.get('Estado')):<13}{av:>6.1f}%  "
          f"{str(p.get('FechaInicio'))[:10]:<11}{str(p.get('FechaFinEst'))[:10]:<11} {sit}")
