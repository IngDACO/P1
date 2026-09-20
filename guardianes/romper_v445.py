# -*- coding: utf-8 -*-
"""⚠️ Regla v410: el guardián de v445, probado contra código ROTO."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

ROTURAS = [
    ("core/auth.py", 't("User not found.")', '"Usuario no encontrado."',
     "un mensaje de login vuelve al español"),
    ("core/auth.py", 'from core.i18n import t\n', '',
     "auth deja de importar el motor (NameError en cada login)"),
    ("core/auth.py", '        _ts = int(float(rec.get("SessionTime", 0)))',
     '        t = int(float(rec.get("SessionTime", 0)))',
     "alguien vuelve a usar `t` como variable (taparía la función)"),
    ("core/auth.py", '"Usuario", "Password", "Rol"', '"User", "Password", "Role"',
     "se traduce un nombre de COLUMNA del libro"),
    ("core/timeclock.py", 'TIPO_GENERAL  = "general"', 'TIPO_GENERAL  = "workday"',
     "se traduce una constante que se guarda en la hoja"),
    # ⚠️ El ancla es el TROZO de la f-string, sin las comillas de alrededor: en el
    # fuente es `f"{t('…')} {etq}."`, así que envolverlo en comillas no casa nunca.
    ("core/timeclock.py", "{t('You have no open clock in for')}",
     "No tienes un clock in de",
     "un mensaje de fichaje vuelve al español"),
    # ⚠️ El centinela de sesión: si vuelve a llevar `t()`, queda congelado al
    # importar y una traducción parcial haría desaparecer el botón de «cerrar la
    # otra sesión» sin dar ningún error.
    ("core/auth.py",
     'SESION_OCUPADA = "This account already',
     'SESION_OCUPADA = t("This account already',
     "el centinela de sesion vuelve a llevar t() (se congela al importar)"),
]


def corre():
    r = subprocess.run([sys.executable, str(AQUI / "verif_v445.py")], cwd=str(RAIZ),
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return r.returncode


rc = corre()
print(f"código SANO → {'OK' if rc == 0 else 'FALLA'}")
if rc != 0:
    sys.exit(1)

cazadas = ancladas = 0
for rel, viejo, nuevo, desc in ROTURAS:
    f = RAIZ / rel
    src = f.read_text(encoding="utf-8")
    if viejo not in src:
        print(f"  ⚠️ ANCLA NO CASA en {rel}: {viejo[:44]!r} — no prueba nada")
        continue
    ancladas += 1
    bak = f.with_suffix(".py.bak_r445")
    shutil.copy2(f, bak)
    try:
        f.write_text(src.replace(viejo, nuevo, 1), encoding="utf-8")
        cazada = corre() != 0
        cazadas += cazada
        print(f"  {'CAZADA     ' if cazada else '✗ SE ESCAPÓ'}  {desc}")
    finally:
        shutil.copy2(bak, f)
        bak.unlink()

fin = corre() == 0
print(f"\ncódigo RESTAURADO → {'OK' if fin else 'FALLA'}")
print(f"{cazadas}/{ancladas} roturas cazadas ({len(ROTURAS)} intentadas)")
sys.exit(0 if (cazadas == ancladas == len(ROTURAS) and fin) else 1)
