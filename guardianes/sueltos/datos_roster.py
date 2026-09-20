"""¿Cómo son de verdad los días con VARIAS asignaciones? (decide el diseño)

Una línea de tiempo solo tiene sentido si las asignaciones traen hora. Si casi
ninguna la trae, dibujar un eje horario sería inventarse una precisión que el dato
no tiene — y quedaría un gráfico vacío con pinta de roto.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                     # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1", "rol": "administrador"}

from core import roster as R                               # noqa: E402

G = "cliente1"
try:
    print("turno estándar:", R.TURNO_ESTANDAR)
except Exception:
    print("turno estándar: (constante no encontrada con ese nombre)")

filas = R._roster_records()
print(f"\n== {len(filas)} filas persona×semana en la hoja ==")

total_dias = con_varias = con_hora = sin_hora = 0
ejemplos = []
semanas = set()
for f in filas:
    if str(f.get("Grupo", "")) != G:
        continue
    semanas.add(str(f.get("Semana", "")))
    import json
    try:
        datos = json.loads(f.get("DatosJSON") or "{}")
    except Exception:
        continue
    for dia, celda in (datos or {}).items():
        items = R._norm_cell(celda)["items"]
        if not items:
            continue
        total_dias += 1
        if len(items) > 1:
            con_varias += 1
            if len(ejemplos) < 6:
                ejemplos.append((f.get("Usuario"), f.get("Semana"), dia, items))
        for it in items:
            if it["ini"] or it["fin"]:
                con_hora += 1
            else:
                sin_hora += 1

print(f"   semanas distintas: {len(semanas)}")
print(f"   días-persona con algo: {total_dias}")
print(f"   …de ellos con MÁS DE UNA asignación: {con_varias}")
print(f"\n   asignaciones CON franja horaria: {con_hora}")
print(f"   asignaciones SIN hora (día completo): {sin_hora}")

print("\n== ejemplos de días con varias ==")
for u, sem, dia, items in ejemplos:
    detalle = " · ".join(f"{it['asig']}[{it['ini'] or '—'}→{it['fin'] or '—'}]" for it in items)
    print(f"   {u:<12} {sem} {dia}: {detalle}")

if not con_varias:
    print("\n   ⚠️ NO hay ningún día con varias asignaciones en los datos actuales:")
    print("      habrá que crear uno para poder probar la vista.")
