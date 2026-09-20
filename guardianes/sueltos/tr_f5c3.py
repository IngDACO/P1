# -*- coding: utf-8 -*-
"""F5c, tercera pasada: los 45 restantes + el `t()` congelado de `plan_data`.

⚠️ `plan_data.USA` se construye a nivel de módulo: los `t()` que metí ahí quedaban
CONGELADOS al importar. Es la tercera vez en tres versiones (v445 `auth`, v446
`ausencias`, y ahora esta) — el guardián de v445 lo caza las tres. La constante
guarda el texto BASE y la traducción va a `por_herramienta()`, que es quien lo pinta.

⚠️ Los textos de correo/Telegram de `credentials` NO llevan `t()`: salen de la
empresa y van en idioma base (regla v436).
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

C = [
    # ── plan_data: quitar el t() congelado (queda el texto BASE) ──
    ("core/plan_data.py", '"rail":    t("Survey (RAIL from the catalogue)"),',
     '"rail":    "Survey (RAIL from the catalogue)",'),
    ("core/plan_data.py", '"hkp":     t("Buffer cutting"),', '"hkp":     "Buffer cutting",'),
    ("core/plan_data.py", '"lfkk":    t("Rail cutting"),', '"lfkk":    "Rail cutting",'),
    ("core/plan_data.py", '"lfgk":    t("Rail cutting"),', '"lfgk":    "Rail cutting",'),
    ("core/plan_data.py", 'f"RAIL (código {rail} no está en el catálogo de rieles)"',
     'f"RAIL ({t(\'code\')} {rail} {t(\'is not in the rail catalogue\')})"'),

    # ── expenses / inventory: etiquetas que se pintan ──
    ("core/expenses.py", '"Mano de obra"', 't("Labour")'),
    ("core/inventory.py", 'f"No se pudo abrir la hoja {hoja}: {e}"',
     'f"{t(\'Could not open sheet\')} {hoja}: {e}"'),

    # ── payroll / invoices ──
    ("core/payroll.py", 'f"No se pudo abrir la hoja {NOMINAS_SHEET}: {e}"',
     'f"{t(\'Could not open sheet\')} {NOMINAS_SHEET}: {e}"'),
    ("core/invoices.py", 'f"No se pudo abrir la hoja {FACTURAS_SHEET}: {e}"',
     'f"{t(\'Could not open sheet\')} {FACTURAS_SHEET}: {e}"'),

    # ── manuals ──
    ("core/manuals.py", 'f"No se pudo leer el archivo: {e}"',
     'f"{t(\'Could not read the file\')}: {e}"'),
    ("core/manuals.py", 'f"No se pudo guardar el manual: {e}"',
     'f"{t(\'Could not save the manual\')}: {e}"'),

    # ── rails ──
    ("core/rails.py", 'f"La referencia \'{ref}\' ya existe."',
     'f"{t(\'Reference\')} \'{ref}\' {t(\'already exists.\')}"'),
    ("core/rails.py", 'f"Riel \'{ref}\' agregado."',
     'f"{t(\'Rail\')} \'{ref}\' {t(\'added.\')}"'),
    ("core/rails.py", 'f"No se pudo abrir la hoja {RIELES_SHEET}: {e}"',
     'f"{t(\'Could not open sheet\')} {RIELES_SHEET}: {e}"'),

    # ── toolruns: los VALORES de HERRAMIENTAS (las claves NO) ──
    ("core/toolruns.py", '"survey": "Survey de elevador"', '"survey": t("Lift survey")'),
    ("core/toolruns.py", '"plomada": "Líneas de plomada"', '"plomada": t("Plumb lines")'),
    ("core/toolruns.py", '"rieles": "Corte de rieles"', '"rieles": t("Rail cutting")'),
    ("core/toolruns.py", '"buffers": "Corte de buffers"',
     '"buffers": t("Buffer cutting")'),
]

for rel, viejo, nuevo in C:
    f = R / rel
    src = f.read_text(encoding="utf-8")
    n = src.count(viejo)
    if n != 1:
        print(f"  ⚠️ {rel}: {n} de {viejo[:56]!r}")
        continue
    f.write_text(src.replace(viejo, nuevo, 1), encoding="utf-8")
    print(f"  OK  {rel}: {viejo[:56]}")
