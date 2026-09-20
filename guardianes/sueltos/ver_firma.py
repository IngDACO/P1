"""¿Se firmó de verdad el Pre-Start de `prueba2`? (la sesión del panel no lo puede ver)

Lo que pasa en el navegador del usuario no llega al panel: son sesiones distintas. Pero
firmar ESCRIBE, así que el rastro está en la hoja: el asistente nuevo lleva `tarde: true`
y su hora. SOLO LECTURA.
"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrador", "nombre": "dmoreno"}

from core import clock, prestart as PS                            # noqa: E402
from core.num import parse_date as _pd                            # noqa: E402

G, HOY = "cliente1", clock.today(G := "cliente1")
print(f"hoy {HOY}\n== pre-starts de hoy ==")
for r in PS._records():
    if _pd(r.get("Fecha")) != HOY:
        continue
    try:
        asis = json.loads(r.get("Asistentes", "") or "[]")
    except Exception:
        asis = []
    tarde = [a for a in asis if a.get("tarde")]
    print(f"\n  {r.get('ID')} · {r.get('ProyectoID')} · facilitador {r.get('Facilitador')}")
    print(f"     DriveID: {r.get('DriveID') or '(sin PDF archivado)'}")
    for a in asis:
        marca = f"  ← FIRMÓ AL LLEGAR ({a.get('hora')})" if a.get("tarde") else ""
        print(f"     · {a.get('name'):<16} ini={a.get('initial'):<4} "
              f"firmado={a.get('firmado')}{marca}")
    if tarde:
        print(f"     >>> {len(tarde)} firma(s) tardía(s): el camino de v403 se EJERCITÓ")

print("\n== ¿a quién le sigue faltando firmar en prueba2? ==")
for u in ("asfgjjd", "dmoreno", "Marcus Chen"):
    p = PS.pendiente_de_firma("PRJ-0005", G, u)
    print(f"  {u:<14} {'le falta → ' + str(p.get('id')) if p else 'no le falta (ya consta)'}")
