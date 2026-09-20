# -*- coding: utf-8 -*-
"""La línea base, en los casos que deciden si sirve o no."""
import datetime as dt
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from core import baseline as BL                                   # noqa: E402
from core.schedule import build_schedule                          # noqa: E402

INI = dt.date(2026, 9, 1)


def plan(durs, preds=None):
    filas = [{"nombre": "A%d" % (i + 1), "duracion": d, "peso": 10, "orden": i + 1,
              "pred": (preds[i] if preds else "")} for i, d in enumerate(durs)]
    return build_schedule(1, INI, {}, custom_rows=filas)


s1 = plan([4, 4, 4])
bl = BL.fijar({}, s1, "Bobo", "2026-09-17 09:00")
print("1) se fija por primera vez")
print("   original: entrega %s · total %s · %d actividades"
      % (bl["original"]["entrega"], bl["original"]["total"], len(bl["original"]["acts"])))
print("   historial: %d (aún no se ha replanificado)" % len(bl["historial"]))

print("\n2) se alarga la 2ª de 4 a 8 días (lo que antes no dejaba rastro)")
s2 = plan([4, 8, 4])
c = BL.comparar(s2, bl)
print("   entrega acordada %s → hoy %s  (%+.1f d)" % (c["entrega_base"], c["entrega_hoy"], c["movio"]))
for f in c["actividades"]:
    print("   · A%d %s: %s → %s d, empieza %+.1f d después"
          % (f["orden"], f["estado"], f["dur_base"], f["dur_hoy"], f["movio"] or 0))

print("\n3) se RE-FIJA (el cliente aprueba el plan nuevo)")
bl2 = BL.fijar(bl, s2, "Bobo", "2026-09-20 10:00")
print("   original INTACTA: %s (total %s)" % (bl2["original"]["entrega"], bl2["original"]["total"]))
print("   vigente        : %s (total %s)" % (bl2["vigente"]["entrega"], bl2["vigente"]["total"]))
print("   replanificaciones: %d · la última movió %+.1f d"
      % (len(bl2["historial"]), bl2["historial"][-1]["movio"]))

print("\n4) ⚠️ tras re-fijar, se sigue comparando contra la ORIGINAL")
c2 = BL.comparar(s2, bl2)
print("   movió %+.1f d respecto a lo acordado · replanificaciones: %d"
      % (c2["movio"], c2["replanificaciones"]))

print("\n5) se AÑADE una actividad y se BORRA otra (se casan por ORDEN, no por posición)")
s3 = plan([4, 8, 4, 3])
c3 = BL.comparar(s3, bl)
print("   " + " · ".join("A%d %s" % (f["orden"], f["estado"]) for f in c3["actividades"]))
s4 = plan([4])
c4 = BL.comparar(s4, bl)
print("   con solo la 1ª: " + " · ".join("A%d %s" % (f["orden"], f["estado"])
                                         for f in c4["actividades"]))

print("\n6) sin línea base, no se compara nada (la obra va como hasta v500)")
print("   %s" % BL.comparar(s1, {}))

print("\n7) el plan NO cambió: 0 filas que reportar")
print("   %s" % BL.comparar(s1, bl)["actividades"])
