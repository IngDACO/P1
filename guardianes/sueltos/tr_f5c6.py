# -*- coding: utf-8 -*-
"""F5c, remate: las etiquetas cortas y los ultimos mensajes.

ATENCION: `plumb.py` usa el alias `_d` (v438) porque `d` ya es variable ahi; los
diagramas van en idioma BASE porque viajan al PDF.
`tenant.py` es modulo HOJA (solo importa streamlit): se le anade `t` sin ciclo.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

# imports que faltan
for rel, ancla in (("core/plan_store.py", "logger = logging.getLogger(__name__)"),
                   ("core/tenant.py", "logger = logging.getLogger(__name__)")):
    f = R / rel
    s = f.read_text(encoding="utf-8")
    if "from core.i18n import t" in s:
        continue
    if s.count(ancla) != 1:
        print(f"  AVISO {rel}: ancla ambigua ({s.count(ancla)})")
        continue
    f.write_text(s.replace(ancla, f"from core.i18n import t\n{ancla}", 1),
                 encoding="utf-8")
    print(f"  OK  {rel}: import anadido")

C = [
    ("core/expenses.py", '(t("Labour"), C_MO), ("Compras", C_CO)',
     '(t("Labour"), C_MO), (t("Purchases"), C_CO)'),
    ("core/plumb.py", "f'plano {_n(bsc.get(\"bs_plano\"))} vs</text>'",
     "f'{_d(\"drawing\")} {_n(bsc.get(\"bs_plano\"))} vs</text>'"),
    ("core/plan_store.py", 'opc = [f"Usar el plano cargado \u00b7 {nom}", "Cargar otro plano"]',
     'opc = [f"{t(\'Use the loaded drawing\')} \u00b7 {nom}", t("Load another drawing")]'),
    ("core/calculations.py",
     'issues.append(f"FS ({fs}) < TSW ({tsw}): no hay espacio frontal de seguridad")',
     'issues.append(f"FS ({fs}) < TSW ({tsw}): '
     'no front safety clearance")'),
    ("core/tenant.py", 'f":material/lock: {etiqueta} no existe o no es de tu empresa."',
     'f":material/lock: {etiqueta} " + t("does not exist or is not yours.")'),
    ("core/excel_io.py", 'raise ValueError(f"No se pudo leer la hoja SURVEY: {e}")',
     'raise ValueError(f"Could not read the SURVEY sheet: {e}")'),
    ("core/excel_io.py",
     'raise ValueError(f"La hoja SURVEY debe tener {len(expected_cols)} columnas '
     '(encontradas: {len(df.columns)})")',
     'raise ValueError(f"The SURVEY sheet must have {len(expected_cols)} columns '
     '(found: {len(df.columns)})")'),
]

for rel, viejo, nuevo in C:
    f = R / rel
    s = f.read_text(encoding="utf-8")
    n = s.count(viejo)
    if n != 1:
        print(f"  AVISO {rel}: {n} de {viejo[:56]!r}")
        continue
    f.write_text(s.replace(viejo, nuevo, 1), encoding="utf-8")
    print(f"  OK  {rel}: {viejo[:56]}")
