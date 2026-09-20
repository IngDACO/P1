# -*- coding: utf-8 -*-
"""El ORÁCULO del cronograma, sacado del módulo de v498 (no del actual).

⚠️ Comparar la salida del código nuevo consigo misma no probaría nada (trampa nº1).
Los números que salen de aquí se escriben LITERALES en verif_v499.py — sacarlos de
git dentro del guardián lo dejaría vacío en cuanto se haga el commit (lección v484).
"""
import datetime as dt
import importlib.util
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
AQUI = os.path.dirname(os.path.abspath(__file__))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "admin", "nombre": "admin",
                            "rol": "administrator", "grupo": "cliente1"}

_spec = importlib.util.spec_from_file_location(
    "sched_v498", os.path.join(AQUI, "schedule_v498.py"))
old = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(old)

from core.schedule import build_schedule as nuevo                 # noqa: E402

INICIO = dt.date(2026, 9, 1)
print("   NS  rip   | v498 (dias, n) | v499 (dias, n) | iguales")
print("   " + "-" * 56)
filas, difs = [], 0
for ns in (1, 2, 3, 6, 8, 12, 20):
    for rip in (False, True):
        o = old.build_schedule(ns, INICIO, {}, ripout=rip)
        n = nuevo(ns, INICIO, {}, ripout=rip)
        a = (o["total_dias"], len(o["activities"]))
        b = (n["total_dias"], len(n["activities"]))
        difs += (a != b)
        filas.append((ns, rip, a))
        print(f"   {ns:2d}  {str(rip):5s} | {str(a):14s} | {str(b):14s} | {a == b}")

# ⚠️ Y no basta con el total: dos cronogramas distintos pueden durar lo mismo.
# Se comparan TODAS las fechas y pesos, actividad por actividad.
detalle = 0
for ns in (1, 2, 3, 6, 8, 12, 20):
    for rip in (False, True):
        o = old.build_schedule(ns, INICIO, {}, ripout=rip)
        n = nuevo(ns, INICIO, {}, ripout=rip)
        for x, y in zip(o["activities"], n["activities"]):
            if (x["nombre"], x["inicio"], x["duracion"], x["peso"]) != \
               (y["nombre"], y["inicio"], y["duracion"], y["peso"]):
                detalle += 1

print("\n   totales distintos: %d   ·   actividades distintas: %d" % (difs, detalle))
print("\n   ESPERADO = {")
for ns, rip, a in filas:
    print("       (%d, %s): (%s, %d)," % (ns, rip, a[0], a[1]))
print("   }")
