# -*- coding: utf-8 -*-
"""v699 · Lo visto verificando v698 en producción (23/11): el subtítulo del Gantt decía «33 days» con el plan ya en
días de trabajo (de lunes a viernes, D1 del ciclo 6). Se afirma sobre el SVG que se pinta, sin red ni escrituras."""
import os
import re
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


from core.schedule import build_schedule, schedule_svg                    # noqa: E402

_rows = [{"nombre": "A", "duracion": 2, "peso": 50, "orden": 1}, {"nombre": "B", "duracion": 3, "peso": 50, "orden": 2}]
_svg = schedule_svg(build_schedule(1, date(2026, 11, 22), {}, custom_rows=_rows), today_day=1)
_sub = re.findall(r'font-size="8\.5" fill="#5b6472">([^<]*)</text>', _svg)
chk("la sonda SABE ver el subtítulo (fechas y nº de actividades)", _sub and "2 activities" in _sub[0], _sub)
chk("el subtítulo dice «5 working days» (no «5 days»)", _sub and "· 5 working days ·" in _sub[0], _sub)
chk("…y el fin, el último día de trabajo (viernes 27/11)", _sub and "22/11/2026 → 27/11/2026" in _sub[0], _sub)

print()
print("verif_v699: %d FALLOS" % len(FALLOS) if FALLOS else "verif_v699: TODO OK")
sys.exit(1 if FALLOS else 0)
