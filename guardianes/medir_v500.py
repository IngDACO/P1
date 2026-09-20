# -*- coding: utf-8 -*-
"""¿Qué cambia si el fin previsto sale de la CADENA en vez del SPI?

Se mide ANTES de tocar ninguna pantalla (v360): un cambio así mueve cifras en la cartera,
las agrupaciones y el radar, y no se cambia en frío lo que nadie ha comparado.
"""
import datetime as dt
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Bobo", "nombre": "Bobo",
                            "rol": "administrator", "grupo": "cliente1"}
from core import projects as P                                    # noqa: E402
from core.schedule import build_schedule, schedule_projection     # noqa: E402

INI = dt.date(2026, 9, 1)


def caso(nombre, duraciones, avances, hoy, preds=None, windows=None):
    filas = [{"nombre": "A%d" % (i + 1), "duracion": d, "peso": 10,
              "orden": i + 1, "pred": (preds[i] if preds else "")}
             for i, d in enumerate(duraciones)]
    s = build_schedule(1, INI, {}, custom_rows=filas)
    pr = schedule_projection(s, avances, hoy, windows)
    plan_d = s["total_dias"]
    spi_d = None   # v500: el SPI ya no produce fecha
    cad_d = pr["dias_cadena"]
    print("  %-46s plan %2dd · SPI: %-18s · CADENA: %s" % (
        nombre, plan_d,
        ("%+.1f d (%s)" % (spi_d, pr["fecha_proj"].strftime("%d/%m"))) if spi_d is not None else "— (sin base)",
        "%+.1f d (%s) · mandan %s" % (cad_d, pr["fecha_cadena"].strftime("%d/%m"),
                                      pr["criticas_cadena"])))


print("CASOS CONSTRUIDOS · 4 actividades de 5 días encadenadas (plan 20 d)")
D = [5, 5, 5, 5]
caso("día 0, nada hecho", D, [0, 0, 0, 0], 0)
caso("día 10, las 2 primeras al 100%", D, [100, 100, 0, 0], 10)
caso("día 10, al 50% del avance TOTAL pero la 1 sin tocar",
     D, [0, 100, 100, 0], 10)
caso("día 10, todo al 25% (nada terminado)", D, [25, 25, 25, 25], 10)
caso("día 15, solo la 1 terminada", D, [100, 0, 0, 0], 15)

print("\nEL CASO QUE EL SPI NO VE · la que bloquea a todas, sin empezar")
caso("3 en paralelo hechas, la del final sin empezar",
     [5, 5, 5, 5], [100, 100, 100, 0], 10, preds=["-", "-", "-", "1;2;3"])

print("\nOBRA REAL (PRJ-0001)")
r = P.project_schedule("PRJ-0001")
if r:
    pr, s = r["proj"], r["sched"]
    print("  plan: %d d (fin %s) · hoy = día %d" % (
        s["total_dias"], s["fecha_fin"].strftime("%d/%m/%Y"), r["today_day"]))
    print("  SPI   : %s (ritmo; ya no da fecha)" % pr["spi"])
    print("  CADENA:      → fin %s (%+.1f d) · mandan las actividades %s" % (
        pr["fecha_cadena"].strftime("%d/%m/%Y"), pr["dias_cadena"], pr["criticas_cadena"]))
