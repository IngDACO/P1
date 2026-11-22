# -*- coding: utf-8 -*-
"""v700 · H28 del ciclo 6: el fin previsto por la cadena (`plan.pronostico`) dejaba que lo que faltaba de una
actividad EMPEZADA corriera desde hoy sin sus predecesoras, y todo lo de detrás la seguía. En C6 (puertas en 4 de 8
plantas antes de tiempo) la obra «terminaba» el día 18,7 de 33: «14d ahead»; con la regla nueva, 30,7 (≈2 d por
delante: lo ganado en Set Up, Prepping y las puertas). Ahora: lo hecho fuera de orden se GANA y lo que falta espera a
las de delante. Puro, sin red ni escrituras."""
import os
import sys
from datetime import date

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:900]))
    if not cond:
        FALLOS.append(nombre)


from core import plan                                                     # noqa: E402
from core.schedule import build_schedule, schedule_projection             # noqa: E402

# C6 tal como está (23/11/2026): 14 etapas en cadena, Set Up al 85,1 % y Prepping al 23,6 %, y las puertas
# (etapa 7) al 8 % con inicio real el 21/11 = día −1. Hoy = día 0.
DUR = [2, 1, 2, 3, 2, 4, 4, 1, 2, 3, 3, 1, 2, 3]
AV = [85.1, 23.6, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0]
INI = {0: -1, 1: 0, 6: -1}


def c6(pred7=""):
    return [{"orden": i + 1, "duracion": DUR[i], "pred": (pred7 if i == 6 else ""), "avance": AV[i],
             "ini_real": INI.get(i), "fin_real": None} for i in range(14)]


r = plan.pronostico(c6(), 0)
# a mano: Set Up 0 + 2×0,149 = 0,298 · Prepping espera a Set Up: 0,298 + 0,764 = 1,062 · 3–6 en cadena: 12,062 ·
# las puertas esperan a la 6: 12,062 + 4×0,92 = 15,742 · 8–14 (15 días): 30,742
chk("C6: la obra termina el día 30,74 de 33 (con la regla vieja, 18,68)", abs(r["total_dias"] - 30.742) < 0.01,
    r["total_dias"])
chk("…lo que falta de las puertas empieza al acabar la 6 (12,06) y acaba en 15,74",
    abs(r["por_orden"][7]["fin"] - 15.742) < 0.01, r["por_orden"][7])
chk("…lo hecho fuera de orden se GANA: Prepping acaba en 1,062 (no 1,298, que sería tirar su 23,6 %)",
    abs(r["por_orden"][2]["fin"] - 1.062) < 0.01, r["por_orden"][2])
chk("…el inicio REAL de las puertas no se toca (−1: lo que pasó, pasó)", r["por_orden"][7]["inicio"] == -1,
    r["por_orden"][7])
_crit = sorted(o for o, v in r["por_orden"].items() if v["critica"])
chk("…el camino crítico pasa por cabina, contrapeso y motor (3–6), que retienen las puertas", _crit == list(range(1, 15)),
    _crit)

# Una que DE VERDAD va en paralelo (sin predecesora, «-»): no espera, como antes
r2 = plan.pronostico(c6(pred7="-"), 0)
chk("declarada en paralelo («-»), las puertas no esperan: acaban en 3,68", abs(r2["por_orden"][7]["fin"] - 3.68) < 0.01,
    r2["por_orden"][7])

# En ORDEN, con las de delante ya hechas: igual que antes (desde hoy)
A = [{"orden": 1, "duracion": 2, "pred": "", "avance": 100, "ini_real": 0, "fin_real": 2},
     {"orden": 2, "duracion": 1, "pred": "", "avance": 100, "ini_real": 2, "fin_real": 3},
     {"orden": 3, "duracion": 4, "pred": "", "avance": 50, "ini_real": 3, "fin_real": None},
     {"orden": 4, "duracion": 2, "pred": "", "avance": 0, "ini_real": None, "fin_real": None}]
r3 = plan.pronostico(A, 4)
chk("en orden y con lo de delante hecho, lo que falta corre desde hoy: 4 + 2 = 6, y la 4 acaba en 8",
    abs(r3["por_orden"][3]["fin"] - 6) < 1e-6 and abs(r3["total_dias"] - 8) < 1e-6, r3)
# (el crítico de siempre: la 3 empezó justo al acabar la 2, así que lo hecho también entra; sin la regla nueva, igual)
chk("…y su camino crítico es el de siempre (1–4: cada una empezó al acabar la anterior)",
    sorted(o for o, v in r3["por_orden"].items() if v["critica"]) == [1, 2, 3, 4], r3["por_orden"])

# De punta a punta, por donde lo lee la app: `schedule_projection` (Home «Nd ahead/behind» y el fin previsto)
_rows = [{"nombre": f"E{i + 1}", "duracion": DUR[i], "peso": 7, "orden": i + 1, "pred": ""} for i in range(14)]
sched = build_schedule(1, date(2026, 11, 22), {}, custom_rows=_rows)
win = [((INI.get(i)), None) for i in range(14)]
pr = schedule_projection(sched, AV, 0, win)
chk("Home: C6 sale ≈2 d por delante (dias_cadena −2,3; con la regla vieja, −14,3)",
    pr.get("dias_cadena") is not None and abs(pr["dias_cadena"] + 2.3) < 0.06, pr.get("dias_cadena"))
chk("…y el fin previsto es un día de trabajo de enero de 2027, no de diciembre",
    pr.get("fecha_cadena") is not None and pr["fecha_cadena"].year == 2027 and pr["fecha_cadena"].weekday() < 5,
    pr.get("fecha_cadena"))

print()
print("verif_v700: %d FALLOS" % len(FALLOS) if FALLOS else "verif_v700: TODO OK")
sys.exit(1 if FALLOS else 0)
