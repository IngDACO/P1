# -*- coding: utf-8 -*-
"""Los 8 ultimos de `report.py`.

ATENCION: `"[Interpretacion no disponible"` NO es texto de pantalla: es el PREFIJO
que `_ia_block` compara para saber si la IA fallo. Se traduce, pero hay que traducir
tambien QUIEN lo produce, o la comparacion deja de casar en silencio.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

C = [
    ("core/report.py", 'f"  F\u00f3rmula:       {formula}"', 'f"  Formula:       {formula}"'),
    ("core/report.py", '"    25 mm    (holgura minima de seguridad al fondo)"',
     '"    25 mm    (minimum safety clearance at the rear)"'),
    ("core/report.py",
     '"                         FB_MAX_BACK = 0.0  (sin desplazamiento hacia atras)"',
     '"                         FB_MAX_BACK = 0.0  (no rearward displacement)"'),
    ("core/report.py", '"                     VALIDO  (BC_CALC no restringe el rango FB)"',
     '"                     VALID  (BC_CALC does not restrict the FB range)"'),
    ("core/report.py",
     'f"Total combinaciones evaluadas: {len(step_log)}  |  V\u00e1lidas: {len(valid_steps)}"',
     'f"Total combinations evaluated: {len(step_log)}  |  Valid: {len(valid_steps)}"'),
    ("core/report.py",
     '"CUT OR = OR - LIMIT OR  /  CUT OL = OL - LIMIT OL  "\n'
     '                    "(valor a cortar si supera el l\u00edmite; vac\u00edo = dentro del l\u00edmite)"',
     '_d("CUT OR = OR - LIMIT OR  /  CUT OL = OL - LIMIT OL  "\n'
     '                       "(amount to cut if it exceeds the limit; blank = within)")'),
]

for rel, viejo, nuevo in C:
    p = R / rel
    s = p.read_text(encoding="utf-8")
    n = s.count(viejo)
    if n != 1:
        print(f"  AVISO {rel}: {n} de {viejo.splitlines()[0][:56]!r}")
        continue
    p.write_text(s.replace(viejo, nuevo, 1), encoding="utf-8")
    print(f"  OK  {viejo.splitlines()[0][:60]}")
