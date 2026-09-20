"""¿Por que el pendiente de PRJ-0005 subio 1.137 USD en 40 minutos?

Medido en pantalla: 3292,80 -> 3305,76 -> 4442,88. Mi primera explicacion (una
sesion de fichaje abierta acumulando contra el reloj) NO da la magnitud: una
persona a 40 $/h + 15 $/h de ganancia son ~37 $ en 40 min, treinta veces menos.

Aqui se descompone el numero por sus PARTES, en vez de adivinar: ingreso, coste,
horas por persona, sesiones abiertas y el rastro de auditoria.

⚠️ SOLO LECTURA. No se escribe nada.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrador"}

from core import auditoria as A                                   # noqa: E402
from core import expenses as E                                    # noqa: E402
from core import finance as F                                     # noqa: E402
from core import invoices as I                                    # noqa: E402
from core import projects as P                                    # noqa: E402
from core import timeclock as T                                   # noqa: E402

G, PID = "cliente1", "PRJ-0005"
prj = P.get_project(PID)
print(f"== {PID} · {prj.get('Nombre')} · estado {prj.get('Estado')} ==\n")

print("-- el numero, por sus partes --")
rev = F.project_revenue(PID, G, prj)          # ⚠️ vive en finance, no en projects
for k in sorted(rev):
    if k not in ("sin_ganancia",):
        print(f"   {k:<18} {rev[k]}")
print(f"   sin_ganancia       {rev.get('sin_ganancia')}")
fact = I.facturado_por_proyecto(G).get(PID, 0.0)
pend = I.pendiente_de_facturar(PID, G, prj)
print(f"\n   facturado          {fact:,.2f}")
print(f"   PENDIENTE          {pend:,.2f}")

print("\n-- horas por persona (lo que alimenta el ingreso) --")
lb = E.labor_breakdown(PID, G)
for f in lb.get("filas", []):
    print(f"   {str(f.get('usuario')):<16} {f.get('horas'):>8} h "
          f"× tarifa {f.get('tarifa')} = {f.get('costo')}")
print(f"   TOTAL horas        {sum(f.get('horas', 0) for f in lb.get('filas', [])):.2f}")
print(f"   ganancia/hora      {P.ganancia_hora(PID, prj)}")   # firma: (pid, prj)

print("\n-- ¿hay alguna sesion de fichaje ABIERTA en el grupo? --")
abiertas = []
for r in T._cached_records():
    if str(r.get("Grupo", "")).strip().lower() != G:
        continue
    if str(r.get("Clock Out", "")).strip():
        continue
    abiertas.append((r.get("Usuario") or r.get("Nombre"), r.get("Tipo"),
                     r.get("Proyecto"), r.get("ProyectoID"), r.get("Clock In")))
if abiertas:
    for a in abiertas:
        print(f"   ABIERTA  {a}")
else:
    print("   ninguna")

print("\n-- rastro de auditoria de este proyecto --")
try:
    h = A.historial(G, "proyecto", PID)
except Exception as e:                                            # noqa: BLE001
    h = []
    print(f"   (no se pudo leer: {e!r})")
for r in h[-12:]:
    print(f"   {r.get('Fecha')}  {r.get('Usuario')}  {str(r.get('Cambios'))[:160]}")
if not h:
    print("   sin anotaciones")
