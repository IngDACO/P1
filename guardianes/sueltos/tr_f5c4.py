# -*- coding: utf-8 -*-
"""F5c, cuarta pasada: los anclajes que no casaron, con el texto REAL.

ATENCION: `toolruns.HERRAMIENTAS` y `plan_data.USA` son dicts de MODULO, asi que un
`t()` ahi se congela al importar (v445/v446/v447: tercera vez). Sus valores pasan al
texto BASE en ingles, sin envolver. La CLAVE (`"survey"`, `"plomada"`...) no se toca:
se guarda en la hoja `Calculos` y la compara el reabrir-calculo (v441).
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

C = [
    ("core/plan_data.py",
     'faltan.append(f"RAIL (c\u00f3digo {out[\'rail\']} no est\u00e1 en el cat\u00e1logo de rieles)")',
     'faltan.append(f"RAIL ({t(\'code\')} {out[\'rail\']} "\n'
     '                      + t("is not in the rail catalogue") + ")")'),
    ("core/inventory.py", 'f"No se pudo abrir la hoja {title}: {e}"',
     'f"{t(\'Could not open sheet\')} {title}: {e}"'),
    ("core/rails.py", 'f"La referencia \'{referencia}\' ya existe."',
     'f"{t(\'Reference\')} \'{referencia}\' {t(\'already exists.\')}"'),
    ("core/rails.py", 'f"Riel \'{referencia}\' agregado."',
     'f"{t(\'Rail\')} \'{referencia}\' {t(\'added.\')}"'),
    # ATENCION: dict de modulo -> texto BASE, sin t()
    ("core/toolruns.py", '"survey":   "Survey de elevador",', '"survey":   "Lift survey",'),
    ("core/toolruns.py", '"plomada":  "L\u00edneas de plomada",', '"plomada":  "Plumb lines",'),
    ("core/toolruns.py", '"rieles":   "Corte de rieles",', '"rieles":   "Rail cutting",'),
    ("core/toolruns.py", '"buffers":  "Corte de buffers",', '"buffers":  "Buffer cutting",'),
]

for rel, viejo, nuevo in C:
    f = R / rel
    src = f.read_text(encoding="utf-8")
    n = src.count(viejo)
    if n != 1:
        print(f"  AVISO {rel}: {n} de {viejo[:56]!r}")
        continue
    f.write_text(src.replace(viejo, nuevo, 1), encoding="utf-8")
    print(f"  OK  {rel}: {viejo[:56]}")
