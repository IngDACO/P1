"""¿Qué hay ya en las tres semanas, y qué se fichó de verdad en la pasada?

La semana pasada es la única donde el plan se puede CONTRASTAR con la realidad
(Cumplimiento: 🟢 fichó donde tocaba · 🔴 fichó en otra obra · ⚠️ no fichó). Para que
esos tres estados salgan, el plan tiene que sembrarse MIRANDO los fichajes reales.

SOLO LECTURA.
"""
import datetime as dt
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrador", "nombre": "dmoreno"}

from core import clock, roster as R, timeclock as T               # noqa: E402

G = "cliente1"
LUNES = R.lunes_de(clock.today(G))
print(f"hoy {clock.today(G)} · lunes actual {LUNES}\n")

for k in (-1, 0, 1):
    lu = LUNES + dt.timedelta(days=7 * k)
    datos = R.get_semana(G, lu)
    n = sum(len(R.celda_items(datos, u, d)) for u in datos for d in R.DIAS_TODOS)
    ch = sum(1 for u in datos for d in R.DIAS_TODOS
             for i in R.celda_items(datos, u, d) if i["ini"])
    etiqueta = {-1: "pasada", 0: "ACTUAL", 1: "siguiente"}[k]
    print(f"  semana {lu} ({etiqueta:<9}): {len(datos)} filas · {n} asignaciones · {ch} con franja")

print("\n== qué se FICHÓ la semana pasada (para poder contrastar) ==")
lu0 = LUNES - dt.timedelta(days=7)
por_dia = defaultdict(set)
for r in T._cached_records():
    if str(r.get("Grupo", "")).strip().lower() != G:
        continue
    ci = str(r.get("Clock In", ""))[:10]
    if not ci:
        continue
    try:
        f = dt.date.fromisoformat(ci)
    except Exception:
        continue
    if lu0 <= f <= lu0 + dt.timedelta(days=6):
        pid = str(r.get("ProyectoID", "")).strip()
        if pid:
            por_dia[(str(r.get("Usuario", "")), f)].add(pid)

if not por_dia:
    print("  (no hay fichajes con proyecto esa semana)")
for (usr, f), pids in sorted(por_dia.items()):
    print(f"  {usr:<10} {f} ({R.DIAS_TODOS[f.weekday()]}) → {sorted(pids)}")
