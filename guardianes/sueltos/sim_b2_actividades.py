"""SIMULACIÓN etapa B2 — el cronograma de las 9 obras nuevas.

⚠️ `create_project` NO genera cronograma: solo escribe las actividades que le
pasan. La regla de v306 («solo Instalación genera el plan estándar; el resto
nace con UNA actividad genérica») vive en el FORMULARIO, no en el modelo. Así
que aquí se replica exactamente lo que hace `projects_ui` (líneas 1001-1013),
en vez de inventar un cronograma distinto al que crearía la app.

Se escribe TODO en un solo `append_rows`: 9 obras × ~11 actividades serían ~99
llamadas si se usara `add_activity`, y el techo son 60/min (v339).

Las fechas reales se ponen aquí con valores COHERENTES con el calendario de cada
obra. Por el camino normal (`save_field_progress`, v162) se pondrían todas a HOY
—correcto cuando el campo reporta día a día, irreal para una obra de junio— y la
curva S real saldría plana.
"""
import sys
from datetime import date, timedelta

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st
st.session_state["auth"] = {"usuario": "Bobo", "grupo": "cliente1", "rol": "administrador"}

from core import projects as P, timeclock as T                      # noqa: E402
from core.schedule import build_schedule                            # noqa: E402

G = "cliente1"
HOY = date(2026, 8, 18)

# pid → (tipo, ns, inicio, fin_manual, avance objetivo)
NUEVAS = {
    "PRJ-0007": ("Instalación", 8, date(2026, 6, 1),  None,               62),
    "PRJ-0008": ("Instalación", 8, date(2026, 6, 15), None,               45),
    "PRJ-0009": ("Instalación", 8, date(2026, 7, 6),  None,               18),
    "PRJ-0010": ("Ripout",      0, date(2026, 7, 20), date(2026, 8, 14),  70),
    "PRJ-0011": ("Instalación", 6, date(2026, 9, 8),  None,                0),
    "PRJ-0012": ("Otro",        0, date(2026, 5, 4),  date(2026, 9, 30),  55),
    "PRJ-0013": ("Otro",        0, date(2026, 8, 3),  date(2026, 12, 18),  0),
    "PRJ-0014": ("Delivery",    0, date(2026, 7, 27), date(2026, 7, 31), 100),
    "PRJ-0015": ("Otro",        0, date(2026, 8, 10), date(2026, 8, 12), 100),
}

ws = T.get_sheet("Actividades", tuple(P.ACTIVITIES_HEADERS))
existentes = {str(r.get("ProyectoID")) for r in ws.get_all_records(numericise_ignore=["all"])}

filas, resumen = [], []
for pid, (tipo, ns, ini, fin_manual, objetivo) in NUEVAS.items():
    if pid in existentes:
        print(f"   {pid} ya tiene actividades, se salta")
        continue

    # ── el cronograma, igual que projects_ui:1001-1013
    if tipo == "Instalación":
        sched = build_schedule(int(ns), ini, {})
        acts = sched.get("activities", [])
        fin = sched["fecha_fin"] if sched.get("fecha_fin") else fin_manual
    else:
        dias = max(1, ((fin_manual - ini).days + 1) if fin_manual else 1)
        acts = [{"nombre": "Ejecución", "duracion": dias, "peso": 1}]
        fin = fin_manual

    pesos = [float(a.get("peso", a.get("Peso", 0)) or 0) for a in acts]
    total = sum(pesos) or 1.0
    restante = objetivo * total / 100.0

    cursor = ini                      # para repartir las fechas reales por el calendario
    for i, (a, w) in enumerate(zip(acts, pesos)):
        if restante <= 0:
            av = 0
        elif restante >= w:
            av = 100
            restante -= w
        else:
            av = int(round(restante / w * 100)) if w else 0
            restante = 0

        dur = int(float(a.get("duracion", a.get("DuracionDias", 1)) or 1))
        f_ini_real = f_fin_real = ""
        if av > 0:
            f_ini_real = cursor.isoformat()
            # ⚠️ una actividad al 100% tiene fin real; una a medias NO (sigue
            #    abierta). Rellenar los dos sería inventar que ya terminó.
            if av >= 100:
                f_fin_real = min(cursor + timedelta(days=max(0, dur - 1)), HOY).isoformat()
            cursor = min(cursor + timedelta(days=dur), HOY)

        filas.append([pid, str(i + 1), a.get("nombre", a.get("Nombre", f"Actividad {i+1}")),
                      str(dur), str(w), str(av), f_ini_real, f_fin_real, ""])

    avance = round(sum(w * av for w, av in
                       zip(pesos, [float(f[5]) for f in filas[-len(acts):]])) / total, 1)
    resumen.append((pid, tipo, len(acts), avance, fin))

print(f"== B2. {len(filas)} actividades en UN append_rows ==")
if filas:
    ws.append_rows(filas, value_input_option="RAW")
    P._invalidate()

# ── el Avance del proyecto y, en Instalación, el fin que calcula el cronograma
for pid, tipo, n, avance, fin in resumen:
    campos = {"Avance": str(avance)}
    if fin:
        campos["FechaFinEst"] = fin.isoformat() if hasattr(fin, "isoformat") else str(fin)
    P.update_project(pid, campos)
print("   avance y fecha de fin escritos\n")

P._invalidate()
print("== estado ==")
for p in P.list_projects(G, incluir_archivados=True):
    pid = str(p.get("ID"))
    if pid not in NUEVAS:
        continue
    acts = P.list_activities(pid)
    hechas = sum(1 for a in acts if float(str(a.get("Avance", 0) or 0)) >= 100)
    print(f"   {pid}  {str(p.get('Nombre'))[:34]:<35} {str(p.get('Estado')):<12} "
          f"{str(p.get('Avance')):>5}%  {hechas}/{len(acts)} act.  fin={p.get('FechaFinEst')}")
