# -*- coding: utf-8 -*-
"""Los 15 restos de `report.py`: f-strings y bloques ASCII.

⚠️ Ninguno lo vio el barrido del FUENTE (son trozos de f-string y líneas de un
diagrama ASCII). Los encontró **leer el texto del PDF generado** — la lección de
v438: para afirmar «no queda nada», medir sobre la SALIDA.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
F = Path(r"C:\Users\diego\P1\survey_app\core\report.py")

C = [
    ('f"    TKSW    = {tksw:.0f} mm   (pared frontal -> centro riel)"',
     'f"    TKSW    = {tksw:.0f} mm   (front wall -> rail centre)"'),
    ('f"    TK/2    = {tk2:.0f} mm   (centro riel -> fondo cabina)"',
     'f"    TK/2    = {tk2:.0f} mm   (rail centre -> car rear)"'),
    ('f"    BC_CALC = {bc_calc:.0f} mm   (espacio libre detras de cabina)"',
     'f"    BC_CALC = {bc_calc:.0f} mm   (free space behind the car)"'),
    ('f"LIMIT ZB = {zb_sf} x 0.3  (Z lado {z_side}, opuesto al Omega={omega})"',
     'f"LIMIT ZB = {zb_sf} x 0.3  (Z side {z_side}, opposite Omega={omega})"'),
    ('f"DIF {col} = {dif_v:.2f} mm  |  {off_c} valor(es) fuera de límite"',
     'f"DIF {col} = {dif_v:.2f} mm  |  {off_c} value(s) out of limit"'),
    ('f"  - TSW={fstr(\'TSW\')} vs FS={fstr(\'FS\')} - '
     'FS-TSW={fv(\'FS\')-fv(\'TSW\'):.1f} mm - FB extra activo: ',
     'f"  - TSW={fstr(\'TSW\')} vs FS={fstr(\'FS\')} - '
     'FS-TSW={fv(\'FS\')-fv(\'TSW\'):.1f} mm - FB extra active: '),
    ('f"  - Controlador en frame: ', 'f"  - Controller in frame: '),
    ('f"Iteraciones con el menor número de valores OFF '
     '({best_total if best_total is not None else \'N/A\'}):"',
     'f"Iterations with the fewest OFF values '
     '({best_total if best_total is not None else \'N/A\'}):"'),
    ('f"Se muestran {len(min_off_steps)} de {len(valid_steps)} iteraciones válidas "',
     'f"Showing {len(min_off_steps)} of {len(valid_steps)} valid iterations "'),
    ('f"(solo las que alcanzan el mínimo de {best_total} valor(es) fuera de límite)."',
     'f"(only those reaching the minimum of {best_total} value(s) out of limit)."'),
    ('f"Candidatos con mínimo OFF: {n_sol}  |  '
     'Valores fuera de límite: {best[\'total_off\']}"',
     'f"Candidates with minimum OFF: {n_sol}  |  '
     'Values out of limit: {best[\'total_off\']}"'),
    ('f"{prefix}Solución {idx_sol+1} de {n_sol} — RL = {sol[\'rl\']} mm  |  '
     'FB = {sol[\'fb\']} mm{fb_suffix}"',
     'f"{prefix}Solution {idx_sol+1} of {n_sol} — RL = {sol[\'rl\']} mm  |  '
     'FB = {sol[\'fb\']} mm{fb_suffix}"'),
    ('Paragraph(f"Inicio: {schedule[\'start_date\'].strftime(\'%d/%m/%Y\')}  |  "\n'
     '                            f"Fin estimado: '
     '{schedule[\'fecha_fin\'].strftime(\'%d/%m/%Y\')}  |  "\n'
     '                            f"Duración: {schedule[\'total_dias\']} días"',
     'Paragraph(f"Start: {schedule[\'start_date\'].strftime(\'%d/%m/%Y\')}  |  "\n'
     '                            f"Estimated finish: '
     '{schedule[\'fecha_fin\'].strftime(\'%d/%m/%Y\')}  |  "\n'
     '                            f"Duration: {schedule[\'total_dias\']} days"'),
    ('f"Fecha: {clock.now().strftime(\'%d/%m/%Y %H:%M\')}"',
     'f"Date: {clock.now().strftime(\'%d/%m/%Y %H:%M\')}"'),
    # el bloque de criterios, partido en dos líneas dentro de un _calc_block
    ('"Criterio 1: menor número de valores fuera de límite\\n'
     'Criterio 2 (desempate): menor desplazamiento total |RL| + |FB|"',
     '"Criterion 1: fewest values out of limit\\n'
     'Criterion 2 (tie-break): lowest total displacement |RL| + |FB|"'),
    # el diagrama ASCII
    ('"|          riel         |  cabina |               |25|"',
     '"|          rail         |   car   |               |25|"'),
]

src = F.read_text(encoding="utf-8")
for viejo, nuevo in C:
    n = src.count(viejo)
    if n != 1:
        print(f"  ⚠️ {n} de {viejo.splitlines()[0][:60]!r}")
        continue
    src = src.replace(viejo, nuevo, 1)
    print(f"  OK  {viejo.splitlines()[0][:60]}")
F.write_text(src, encoding="utf-8")
