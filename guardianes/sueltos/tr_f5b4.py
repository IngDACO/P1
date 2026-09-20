# -*- coding: utf-8 -*-
"""F5b, tanda 4: los cuatro mensajes que estaban PARTIDOS en dos lineas."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

CAMBIOS = [
    ("core/quotes.py",
     'return False, ("Solo se pueden actualizar precios en un borrador. Esta ya se "\n'
     '                       "envi\u00f3: saca una versi\u00f3n nueva.")',
     'return False, t("Prices can only be updated on a draft. This one was "\n'
     '                        "already sent: create a new version.")'),
    ("core/quotes.py",
     'return False, ("Esta cotizaci\u00f3n ya no es un borrador. Crea una versi\u00f3n nueva "\n'
     '                       "para cambiarla.")',
     'return False, t("This quote is no longer a draft. Create a new version "\n'
     '                        "to change it.")'),
    ("core/quotes.py", 'f"No se pudo crear el proyecto: {res}"',
     'f"{t(\'Could not create the project\')}: {res}"'),
    ("core/projects.py", 'f"Error guardando actividades: {ex}"',
     'f"{t(\'Error saving activities\')}: {ex}"'),
]

for rel, viejo, nuevo in CAMBIOS:
    f = R / rel
    src = f.read_text(encoding="utf-8")
    n = src.count(viejo)
    if n != 1:
        print(f"  AVISO {rel}: {n} coincidencias de {viejo.splitlines()[0][:52]!r}")
        continue
    f.write_text(src.replace(viejo, nuevo, 1), encoding="utf-8")
    print(f"  OK  {rel}: {viejo.splitlines()[0][:56]}")
