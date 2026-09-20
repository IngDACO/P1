# -*- coding: utf-8 -*-
"""v449, cierre: las 11 ultimas etiquetas de la interfaz.

ATENCION: `"COPEX Activos"` es el NOMBRE DE UNA CARPETA DE DRIVE — cambiarlo crearia
una carpeta nueva y los activos ya subidos quedarian en la vieja. NO se toca.
Los `format_func` traducen el DISPLAY; la CLAVE (con emoji) es el ID y se queda.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

C = [
    ("core/inventory_ui.py", 'tenant.exigir(a, "Este activo")',
     'tenant.exigir(a, t("This asset"))'),
    ("core/invoices_ui.py", '"pendiente": ":gray[:material/schedule:] pendiente",',
     '"pendiente": ":gray[:material/schedule:] " + t("outstanding"),'),
    ("core/projects_ui.py",
     '"\U0001f4ce Archivos": ":material/folder: Archivos"}.get(o, o),',
     '"\U0001f4ce Archivos": ":material/folder: Files"}.get(o, o),'),
    ("core/projects_ui.py", '"\U0001f6a8 Avisos": ":material/report: Avisos",',
     '"\U0001f6a8 Avisos": ":material/report: Alerts",'),
    ("core/projects_ui.py", '"\U0001f4b0 Recibos": ":material/receipt: Recibos",',
     '"\U0001f4b0 Recibos": ":material/receipt: Receipts",'),
    ("core/projects_ui.py",
     '"\U0001f4ce Archivos": ":material/folder: Archivos"}.get(o, o))',
     '"\U0001f4ce Archivos": ":material/folder: Files"}.get(o, o))'),
    ("core/projects_ui.py", '("Compras / materiales", d["compras"])',
     '(t("Purchases / materials"), d["compras"])'),
    ("core/quotes_ui.py", 'st.warning(":material/warning: Llevas **"',
     'st.warning(":material/warning: " + t("You are at") + " **"'),
    ("core/roster_ui.py",
     '"\U0001f440 Disponibilidad": ":material/event_available: Libres"}.get(o, o))',
     '"\U0001f440 Disponibilidad": ":material/event_available: Free"}.get(o, o))'),
    ("core/timeclock_ui.py", '_chronometer(gen["clock_in"], "Llevas abierta", _AZUL, "chrono_gen")',
     '_chronometer(gen["clock_in"], t("Open for"), _AZUL, "chrono_gen")'),
]

for rel, viejo, nuevo in C:
    p = R / rel
    s = p.read_text(encoding="utf-8")
    n = s.count(viejo)
    if n != 1:
        print(f"  AVISO {rel}: {n} de {viejo[:58]!r}")
        continue
    p.write_text(s.replace(viejo, nuevo, 1), encoding="utf-8")
    print(f"  OK  {rel}: {viejo[:58]}")
