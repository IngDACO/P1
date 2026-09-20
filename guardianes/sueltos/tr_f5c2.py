# -*- coding: utf-8 -*-
"""F5c, segunda pasada: los mensajes REPETIDOS y el import de manuals.

Los 11 que no casaron aparecen varias veces y son literalmente el mismo mensaje, asi
que van TODAS las apariciones. Se comprueba la cuenta: si manana una de ellas fuera
otra cosa, el numero cambia y salta.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

# manuals no tiene `logger = logging...`: se ancla al ultimo import de la stdlib
f = R / "core/manuals.py"
s = f.read_text(encoding="utf-8")
if "from core.i18n import t" not in s:
    a = "import zipfile\n"
    assert s.count(a) == 1
    f.write_text(s.replace(a, a + "\nfrom core.i18n import t\n", 1), encoding="utf-8")
    print("  OK  core/manuals.py: import anadido")

GS = '"Google Sheets no esta configurado."'.replace("esta", "est\u00e1")
GS_EN = 't("Google Sheets is not configured.")'

CAMBIOS = [
    ("core/expenses.py", GS, GS_EN, 2),
    ("core/roster.py", GS, GS_EN, 4),
    ("core/roster.py", '"Trabajo no encontrado."', 't("Job not found.")', 2),
    ("core/inventory.py", '"Activo no encontrado."', 't("Asset not found.")', 5),
    ("core/credentials.py", GS, GS_EN, 3),
    ("core/credentials.py", '"Credencial no encontrada."',
     't("Credential not found.")', 2),
    ("core/payroll.py", '"N\u00f3mina no encontrada."', 't("Payslip not found.")', 4),
    ("core/prestart.py", '"No se pudo abrir la hoja de pre-starts."',
     't("Could not open the pre-starts sheet.")', 2),
    ("core/plan_data.py", '"Corte de rieles"', 't("Rail cutting")', 3),
    ("core/plan_data.py", '"Corte de buffers"', 't("Buffer cutting")', 2),
    ("core/plan_data.py", '"Par\u00e1metros del hueco"', 't("Shaft parameters")', 3),
]

for rel, viejo, nuevo, n_esp in CAMBIOS:
    p = R / rel
    src = p.read_text(encoding="utf-8")
    n = src.count(viejo)
    if n != n_esp:
        print(f"  AVISO {rel}: esperaba {n_esp} y hay {n} de {viejo[:44]!r}")
        continue
    p.write_text(src.replace(viejo, nuevo), encoding="utf-8")
    print(f"  OK  {rel}: {n}x {viejo[:46]}")
