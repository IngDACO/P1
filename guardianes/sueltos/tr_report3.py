# -*- coding: utf-8 -*-
"""Los últimos 8 de `report.py`, con el texto REAL copiado del fichero.

⚠️ Mis entradas del diccionario no casaban al carácter (una palabra distinta, un
`|RL| + |FB aplicado|` en vez de `|RL| + |FB|`…). Copiar el texto del fuente en vez
de reescribirlo de memoria es lo que hace que un ancla case.

⚠️ Lo que queda en español en el PDF DESPUÉS de esto son los **nombres de actividad**
del cronograma (`Montaje de rieles (guías)`…): son DATO, viven en la hoja
`Actividades`, y traducirlos dejaría los proyectos viejos en español y los nuevos en
inglés sin forma de casarlos. Van con la migración del histórico, no aquí (v438).
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
F = Path(r"C:\Users\diego\P1\survey_app\core\report.py")

C = [
    ('"    |          riel         |  cabina |               |25|"',
     '"    |          rail         |   car   |               |25|"'),
    ('"  OR/OL: si v > LIMIT -> requiere CORTE en la apertura de la puerta"',
     '"  OR/OL: if v > LIMIT -> a CUT is required at the door opening"'),
    ('"Análisis del estado de la cabina ajustada ANTES de aplicar cualquier "\n'
     '            "desplazamiento de optimización. Permite identificar qué límites se incumplen "\n'
     '            "y en qué niveles, como punto de partida para evaluar las mejoras obtenidas."',
     '_d("State of the adjusted car BEFORE applying any optimisation "\n'
     '               "displacement. It shows which limits are breached and at which "\n'
     '               "levels, as the starting point for judging the improvement.")'),
    ('"Criterio 1: menor número de valores fuera de límite\\n'
     'Criterio 2 (desempate): menor desplazamiento total |RL| + |FB aplicado|"',
     '_d("Criterion 1: fewest values out of limit\\n'
     'Criterion 2 (tie-break): lowest total displacement |RL| + |FB applied|")'),
    ('Paragraph("Vista superior del encaje de la cabina en el shaft, piso a piso "\n'
     '                        "(matriz de la solución seleccionada). Verde = dentro de límite, "\n'
     '                        "naranja = al límite, rojo = fuera.", styles["Note"])',
     'Paragraph(_d("Top view of how the car fits in the shaft, floor by floor "\n'
     '                           "(matrix of the selected solution). Green = within limit, "\n'
     '                           "orange = at the limit, red = out."), styles["Note"])'),
    ('Paragraph("Plomado con los desplazamientos determinados por el survey. El conjunto "\n'
     '                            "(plomos + paredes teóricas + template) se desplaza en bloque; las paredes "\n'
     '                            "reales quedan fijas. Eje cero = pared real izquierda.", styles["Note"])',
     'Paragraph(_d("Plumb lines with the displacements determined by the survey. The "\n'
     '                               "assembly (plumb lines + theoretical walls + template) moves "\n'
     '                               "as a block; the real walls stay fixed. Zero axis = left "\n'
     '                               "real wall."), styles["Note"])'),
]

src = F.read_text(encoding="utf-8")
for viejo, nuevo in C:
    n = src.count(viejo)
    if n != 1:
        print(f"  ⚠️ {n} de {viejo.splitlines()[0][:62]!r}")
        continue
    src = src.replace(viejo, nuevo, 1)
    print(f"  OK  {viejo.splitlines()[0][:62]}")
F.write_text(src, encoding="utf-8")
