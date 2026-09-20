# -*- coding: utf-8 -*-
"""F5b, tanda 2: los f-strings de `orders`, `catalogo` y `clientes`."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

CAMBIOS = [
    ("core/orders.py",
     'return False, (f"Se marcó recibida, pero el gasto NO se registró ({msg_g}). "',
     'return False, (f"{t(\'Marked as received, but the expense was NOT recorded\')} '
     '({msg_g}). "'),
    ("core/orders.py",
     'f"Orden recibida y cargada al proyecto ({valor:,.2f})."',
     'f"{t(\'Order received and charged to the project\')} ({valor:,.2f})."'),
    ("core/catalogo.py", 'f"Tipo no válido: {tipo}."',
     'f"{t(\'Invalid type\')}: {tipo}."'),
    ("core/catalogo.py",
     'return False, "Ningún campo reconocido: " + ", ".join(ignorados)',
     'return False, t("No recognised field") + ": " + ", ".join(ignorados)'),
    ("core/clientes.py", 'f"No se pudo abrir la hoja {CLIENTES_SHEET}: {e}"',
     'f"{t(\'Could not open sheet\')} {CLIENTES_SHEET}: {e}"'),
]

for rel, viejo, nuevo in CAMBIOS:
    f = R / rel
    src = f.read_text(encoding="utf-8")
    n = src.count(viejo)
    if n != 1:
        print(f"  ⚠️ {rel}: {n} coincidencias de {viejo[:56]!r}")
        continue
    f.write_text(src.replace(viejo, nuevo, 1), encoding="utf-8")
    print(f"  OK  {rel}: {viejo[:58]}")
