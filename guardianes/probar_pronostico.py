# -*- coding: utf-8 -*-
"""El pronóstico por la cadena, contra los casos que deciden el dominio."""
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from core import plan                                             # noqa: E402


def A(o, d, pred="", av=0, ir=None, fr=None):
    return {"orden": o, "duracion": d, "pred": pred, "avance": av,
            "ini_real": ir, "fin_real": fr}


def fin(acts, hoy):
    return plan.pronostico(acts, hoy)["total_dias"]


print("CADENA de 3 actividades de 4 días (plan = 12 días)")
CAD = [A(1, 4), A(2, 4), A(3, 4)]
print("  plan (calcular)            :", plan.calcular(CAD)["total_dias"])

print("\n1) día 0, nada empezado           -> %.1f  (= el plan)" % fin(CAD, 0))

print("\n2) día 6 y NADA empezado          -> %.1f" % fin(CAD, 6))
print("   (el plan decía 12; como no puede arrancar en el pasado, empieza hoy: 6+12=18)")

print("\n3) día 6, la 1 terminada el 4 y la 2 al 50%%")
c3 = [A(1, 4, av=100, ir=0, fr=4), A(2, 4, av=50, ir=4), A(3, 4)]
r3 = plan.pronostico(c3, 6)
print("   fin: %.1f · por actividad: %s" % (
    r3["total_dias"], {o: (round(v["inicio"], 1), round(v["fin"], 1)) for o, v in r3["por_orden"].items()}))
print("   (a la 2 le quedan 2 d desde HOY -> 8; la 3 va detrás -> 12: EN PLAZO)")

print("\n4) lo mismo pero la 2 solo al 10%%")
c4 = [A(1, 4, av=100, ir=0, fr=4), A(2, 4, av=10, ir=4), A(3, 4)]
print("   fin: %.1f  (le quedan 3.6 d desde hoy -> 9.6; +4 = 13.6: 1.6 d TARDE)" % fin(c4, 6))

print("\n5) la 1 terminó ANTES (día 2) y todo lo demás sin empezar, hoy = 2")
c5 = [A(1, 4, av=100, ir=0, fr=2), A(2, 4), A(3, 4)]
print("   fin: %.1f  (la cadena se ADELANTA: 2+4+4 = 10 < 12)" % fin(c5, 2))

print("\n6) EN PARALELO: la 2 no depende de la 1 y va tarde")
c6 = [A(1, 4, av=100, ir=0, fr=4), A(2, 10, "-", av=0), A(3, 4, "1")]
r6 = plan.pronostico(c6, 6)
print("   fin: %.1f · críticas: %s" % (
    r6["total_dias"], [o for o, v in r6["por_orden"].items() if v["critica"]]))
print("   (manda la 2, que es la que no se ha tocado: 6+10 = 16)")

print("\n7) con DESFASE: la 3 va detrás de la 1 con 2 d de espera")
c7 = [A(1, 4, av=100, ir=0, fr=4), A(2, 4), A(3, 4, "1+2")]
print("   fin: %.1f" % fin(c7, 4))

print("\n8) TODO terminado -> el fin es el REAL, no se mueve aunque hoy sea muy posterior")
c8 = [A(1, 4, av=100, ir=0, fr=3), A(2, 4, av=100, ir=3, fr=7), A(3, 4, av=100, ir=7, fr=9)]
print("   fin: %.1f  (hoy=30)" % fin(c8, 30))

print("\n9) obra sin actividades")
print("   fin: %.1f" % fin([], 5))
