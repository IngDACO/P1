# -*- coding: utf-8 -*-
"""Cuarta red, tanda 2: roster_ui + las cabeceras de tabla que van al PDF de obra.

⚠️ Las columnas del EDITOR DE ENTRADA (`plb_bsr_df`, `rc_L_df`) NO se tocan: el
`_snapshot` de v148 las guarda en `DatosJSON` con su nombre, y en la hoja real
`CAL-0002` ya tiene una con la columna `Elevador`. Renombrarla rompería «reabrir
el cálculo». Solo se traducen las tablas de RESULTADO, que se construyen y se
consumen en el sitio (y encima viajan al PDF que se lleva a obra).
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

CAMBIOS = [
    # ⚠️ Los 7 de roster_ui ya se aplicaron (5 por script + 2 a mano).

    # ── tablas de RESULTADO de las herramientas (van al PDF de obra) ──
    ("core/rail_cut_ui.py",
     'cols = {f"Elevador {i+1}": [round(per_elev_values[i][lab], 1) for lab in labels]',
     'cols = {f"{d(\'Lift\')} {i+1}": [round(per_elev_values[i][lab], 1) for lab in labels]'),
    ("core/rail_cut_ui.py",
     '_filas = [{"Elevador": i + 1, "L (mm)": round(x["L"], 1),',
     '_filas = [{d("Lift"): i + 1, "L (mm)": round(x["L"], 1),'),
    ("core/rail_cut_ui.py",
     '_filas = [{"Elevador": i + 1,\n'
     '                       **{k: round(float(x.get(k) or 0), 1)',
     '_filas = [{d("Lift"): i + 1,\n'
     '                       **{k: round(float(x.get(k) or 0), 1)'),
    ("core/belting_ui.py",
     '"Elevador":  r["elevador"],',
     'd("Lift"):   r["elevador"],'),
    ("core/belting_ui.py",
     '"Posici\u00f3n":  f"{abs(r[\'dsts\']):.0f} mm "',
     'd("Position"): f"{abs(r[\'dsts\']):.0f} mm "'),
    ("core/plumb_ui.py",
     'format_func=lambda i: f"Elevador {i}", key="plb_sel_e")',
     'format_func=lambda i: f"{t(\'Lift\')} {i}", key="plb_sel_e")'),
    ("core/plumb_ui.py",
     '_pr = (f"{_pr_base} \u00b7 Elevador {sel}" if _pr_base else f"Elevador {sel}")',
     '_pr = (f"{_pr_base} \u00b7 {d(\'Lift\')} {sel}" if _pr_base else f"{d(\'Lift\')} {sel}")'),
]

for rel, viejo, nuevo in CAMBIOS:
    f = R / rel
    src = f.read_text(encoding="utf-8")
    assert viejo in src, f"ANCLA NO CASA en {rel}: {viejo[:70]!r}"
    assert src.count(viejo) == 1, f"ANCLA AMBIGUA ({src.count(viejo)}) en {rel}"
    f.write_text(src.replace(viejo, nuevo, 1), encoding="utf-8")
    print(f"  OK  {rel}: {viejo.splitlines()[0][:56]}")
print(f"\n{len(CAMBIOS)} cambios aplicados")
