# -*- coding: utf-8 -*-
"""Cuarta red, tanda 4: los 9 que la red solo vio al ampliarle el léxico.

⚠️ Estos NO los veía la primera versión de la red: su léxico eran palabras
FUNCIONALES (de, la, con…) y estos son SUSTANTIVOS sin acento («actividades»,
«pendiente», «adelantado», «retraso», «consumido»). Es la trampa nº28, y lo destapó
probar la red contra un caso construido en vez de fiarme de su «0».
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
F = Path(r"C:\Users\diego\P1\survey_app\core\projects_ui.py")

CAMBIOS = [
    ('f"{len(sched.get(\'activities\', []))} actividades"',
     'f"{len(sched.get(\'activities\', []))} activities"'),
    ('msgs.append(f":material/cleaning_services: Planificador: se quitaron {n} '
     'day(s) of those unassigned.")',
     'msgs.append(f":material/cleaning_services: Planner: {n} day(s) cleared '
     'for those unassigned.")'),
    ('_sit = (f"{_dl} d retraso" if _dl else (f"{_ah} d adelanto" if _ah else "\u2014"))',
     '_sit = (f"{_dl} d behind" if _dl else (f"{_ah} d ahead" if _ah else "\u2014"))'),
    ('+ (f"  \u00b7  :green[:material/check_circle:] {_na} adelantado(s)" if _na else ""))',
     '+ (f"  \u00b7  :green[:material/check_circle:] {_na} ahead" if _na else ""))'),
    ('f"Grouping budget ${tot_pres:,.0f} \u00b7 {_p}% consumido"',
     'f"Grouping budget ${tot_pres:,.0f} \u00b7 {_p}% used"'),
    ('"Situaci\u00f3n": (f"{delays[pid]:.0f} d retraso" if pid in delays',
     '"Situaci\u00f3n": (f"{delays[pid]:.0f} d behind" if pid in delays'),
    ('else (f"{aheads[pid]:.0f} d adelanto" if pid in aheads else "on time")),',
     'else (f"{aheads[pid]:.0f} d ahead" if pid in aheads else "on time")),'),
    ('_tit = f"Purchase orders ({len(_pend)} pendiente{\'s\' if len(_pend) != 1 else \'\'})"',
     '_tit = f"Purchase orders ({len(_pend)} pending)"'),
]

src = F.read_text(encoding="utf-8")
for viejo, nuevo in CAMBIOS:
    assert viejo in src, f"ANCLA NO CASA: {viejo[:72]!r}"
    assert src.count(viejo) == 1, f"ANCLA AMBIGUA ({src.count(viejo)}): {viejo[:60]!r}"
    src = src.replace(viejo, nuevo, 1)
    print(f"  OK  {viejo[:66]}")
F.write_text(src, encoding="utf-8")
print(f"\n{len(CAMBIOS)} cambios aplicados")
