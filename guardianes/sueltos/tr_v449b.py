# -*- coding: utf-8 -*-
"""v449, resto: las etiquetas sueltas que quedaban en la interfaz."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

C = [
    ("core/roster_ui.py", 'st.caption(":material/block: Ocupados esa franja: "',
     'st.caption(":material/block: " + t("Busy in that slot") + ": "'),
    ("core/survey_ui.py",
     'st.caption(":material/attach_file: Documentos archivados, salvo: "',
     'st.caption(":material/attach_file: " + t("Documents filed, except") + ": "'),
    ("core/auth_ui.py",
     'chips = [(":green[:material/check_circle:] Activo" if activo '
     'else ":red[:material/cancel:] Inactivo"),',
     'chips = [(":green[:material/check_circle:] " + t("Active") if activo\n'
     '              else ":red[:material/cancel:] " + t("Inactive")),'),
    ("core/auth_ui.py", '":material/schedule: Fichando ahora" if fichando else ""',
     '":material/schedule: " + t("Clocked in now") if fichando else ""'),
    ("core/auth_ui.py", '":green[:material/contact_page:] Contacto OK" if contacto_ok',
     '":green[:material/contact_page:] " + t("Contact OK") if contacto_ok'),
]

for rel, viejo, nuevo in C:
    p = R / rel
    s = p.read_text(encoding="utf-8")
    n = s.count(viejo)
    if n != 1:
        print(f"  AVISO {rel}: {n} de {viejo.splitlines()[0][:58]!r}")
        continue
    p.write_text(s.replace(viejo, nuevo, 1), encoding="utf-8")
    print(f"  OK  {rel}: {viejo.splitlines()[0][:58]}")
