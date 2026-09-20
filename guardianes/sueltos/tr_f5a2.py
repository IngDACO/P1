# -*- coding: utf-8 -*-
"""F5a, segunda pasada: los mensajes REPETIDOS de `auth.py` y `timeclock.py`.

La primera pasada exigía ancla ÚNICA y saltó los que aparecen varias veces
(`"Usuario no encontrado."` sale 10 veces). Aquí se sustituyen TODAS las
apariciones, porque son literalmente el mismo mensaje — ⚠️ y se comprueba cuántas
había: si mañana una de ellas fuera otra cosa, el número cambia y salta.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

# (fichero, viejo, nuevo, cuántas se esperan)
CAMBIOS = [
    ("core/auth.py",
     '"El acceso no está configurado (faltan credenciales en Secrets)."',
     't("Access is not configured (credentials missing from Secrets).")', 2),
    ("core/auth.py", '"Usuario no encontrado."', 't("User not found.")', 10),
    ("core/auth.py", '"Rol inválido."', 't("Invalid role.")', 2),
    ("core/timeclock.py", '"No hay usuario en sesión."',
     't("No user is signed in.")', 2),
    ("core/timeclock.py", 'f"Error leyendo la hoja: {e}"',
     'f"{t(\'Error reading the sheet\')}: {e}"', 2),
]

for rel, viejo, nuevo, n_esp in CAMBIOS:
    f = R / rel
    src = f.read_text(encoding="utf-8")
    n = src.count(viejo)
    if n != n_esp:
        print(f"  ⚠️ {rel}: esperaba {n_esp} y hay {n} de {viejo[:44]!r} — NO se toca")
        continue
    f.write_text(src.replace(viejo, nuevo), encoding="utf-8")
    print(f"  OK  {rel}: {n}x {viejo[:50]}")
