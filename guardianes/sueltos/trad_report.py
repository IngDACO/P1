# -*- coding: utf-8 -*-
"""Lo que quedaba en español dentro del informe ADMIN (v450).

⚠️ v448 dio este informe por cerrado y quedaban **31 literales** que se PINTAN en el
PDF: cabeceras de tabla, rótulos de fórmula y el pie. Su guardián generaba el PDF y
leía su texto, pero solo comprobaba las líneas que sabía buscar — otro «0» que valía
para la forma medida y no para el documento.

Va todo con `_d()` (alias de `d`, porque `d` ya es variable en `fstr()`): es un
DOCUMENTO y sale de la empresa, así que su idioma no puede depender de la pantalla de
quien lo genera (regla v436).
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RUTA = Path(r"C:\Users\diego\P1\survey_app\core\report.py")

CAMBIOS = [
    ('f"  Sustitución:   = {substitution}"', 'f"  {_d(\'Substitution\')}:   = {substitution}"', 1),
    ('<b>Resultado:      {result_str}</b>', '<b>{_d(\'Result\')}:      {result_str}</b>', 1),
    ('f"  Cabina desplazada hacia: {offset_side}',
     'f"  {_d(\'Car offset towards\')}: {offset_side}', 1),
    ('f"  Rango total evaluado: -{max_rl:.1f}',
     'f"  {_d(\'Total range evaluated\')}: -{max_rl:.1f}', 1),
    ('(paso 0.5 mm)', '({_d(\'step\')} 0.5 mm)', 1),
    ('"Col.", "Límite", "Criterio", "# Viol.", "Niveles incumplidos", "DIF (mm)", "Estado"',
     '_d("Col."), _d("Limit"), _d("Criterion"), _d("# Viol."), _d("Levels out of limit"), _d("DIF (mm)"), _d("Status")', 1),
    ('f"Generado: {clock.now()', 'f"{_d(\'Generated\')}: {clock.now()', 1),
    ('Paragraph("<b>Condición / Parámetro</b>"',
     'Paragraph(f"<b>{_d(\'Condition / Parameter\')}</b>"', 2),
    ('"Offset OR = Offset WR  (mismo desplazamiento lateral)"',
     '_d("Offset OR = Offset WR  (same lateral shift)")', 1),
    ('"Offset OL = Offset WL  (mismo desplazamiento lateral)"',
     '_d("Offset OL = Offset WL  (same lateral shift)")', 1),
    ('f"Total pasos RL evaluados: ', 'f"{_d(\'Total RL steps evaluated\')}: ', 1),
    ('f"Total pasos FB evaluados: ', 'f"{_d(\'Total FB steps evaluated\')}: ', 1),
    ('Paragraph("7.3  Resultado final"', 'Paragraph(f"7.3  {_d(\'Final result\')}"', 1),
    ('f"Seleccionado: RL=', 'f"{_d(\'Selected\')}: RL=', 1),
    ('mm, FB iterado={best[\'fb\']:.1f} mm, FB aplicado=',
     'mm, FB iterated={best[\'fb\']:.1f} mm, FB applied=', 1),
    ('prefix    = "SELECCIONADA - "', 'prefix    = _d("SELECTED") + " - "', 1),
    ('lbl   = "Máximo (mm)"', 'lbl   = _d("Maximum (mm)")', 1),
    ('lbl   = "Mínimo (mm)"', 'lbl   = _d("Minimum (mm)")', 1),
    ('_calc_block("Condición",', '_calc_block(_d("Condition"),', 1),
    ('"DIF BS = BS - BSR  (cuando BSR < BS)"', '_d("DIF BS = BS - BSR  (when BSR < BS)")', 1),
    ('_calc_block("Rango 3 — Zona extendida"', '_calc_block(_d("Range 3 — Extended zone")', 1),
    ('_calc_block("Resultado", "Paso encontrado"',
     '_calc_block(_d("Result"), _d("Step found")', 1),
    ('["Actividad", "Inicio", "Fin", "Días", "Peso %"]',
     '[_d("Activity"), _d("Start"), _d("End"), _d("Days"), _d("Weight %")]', 1),
    ('f"Desplazamiento aplicado: lateral (rl) = ',
     'f"{_d(\'Applied shift\')}: lateral (rl) = ', 1),
    ('["Línea", "X inicial (mm)", "X final (mm)", "Desplazada"]',
     '[_d("Line"), _d("X start (mm)"), _d("X end (mm)"), _d("Shifted")]', 1),
    ('Paragraph("<b>Verificación en campo — distancias plomo ↔ pared real</b>"',
     'Paragraph(f"<b>{_d(\'Field check — plumb line ↔ real wall distances\')}</b>"', 1),
]


def main():
    src = RUTA.read_text(encoding="utf-8")
    tot = 0
    for viejo, nuevo, veces in CAMBIOS:
        n = src.count(viejo)
        if n != veces:
            raise SystemExit(f"{viejo[:60]!r} aparece {n}, esperaba {veces}")
        src = src.replace(viejo, nuevo)
        tot += veces
    ast.parse(src)
    RUTA.write_text(src, encoding="utf-8", newline="")
    print(f"{tot} textos del informe ADMIN traducidos")


if __name__ == "__main__":
    main()
