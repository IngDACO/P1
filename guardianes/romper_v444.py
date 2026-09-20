# -*- coding: utf-8 -*-
"""⚠️ Regla v410: el guardián de v444, probado contra código ROTO."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

ROTURAS = [
    # media traducción: la fila vuelve al español y la column_config se queda
    ("core/projects_ui.py", '"Status": _sit', '"Situación": _sit',
     "una cabecera queda A MEDIAS (fila vs column_config)"),
    # el DATO: la columna del editor persistido en DatosJSON
    ("core/rail_cut_ui.py", 'disabled=["Riel"]', 'disabled=["Rail"]',
     "se traduce la columna PERSISTIDA del editor"),
    # el ID de sub-pestaña que compara `sub ==`
    ("core/projects_ui.py", '"📊 Proyectos", "Projects",', '"📊 Projects", "Projects",',
     "se traduce el ID de sub-pestaña (dejaría la rama muerta)"),
    # una etiqueta de indicador vuelve al español
    ("core/projects_ui.py", '":material/notifications:", "Alarms", True, _al_n,',
     '":material/notifications:", "Alarmas", True, _al_n,',
     "una etiqueta de indicador vuelve al español"),
    # el botón de navegar
    ("core/projects_ui.py", 'f"→ {t(\'Go to\')} {secn}"', 'f"→ Ir a {secn}"',
     "el botón de navegar vuelve al español"),
    # los chips de ausencias
    ("core/ausencias_ui.py", 'AU.APROBADA: "🟢 approved"', 'AU.APROBADA: "🟢 aprobada"',
     "un chip de estado vuelve al español"),
    # el buscador
    ("core/home_ui.py", '"persona": "People"', '"persona": "Personas"',
     "una etiqueta del buscador vuelve al español"),
]


def corre():
    r = subprocess.run([sys.executable, str(AQUI / "verif_v444.py")], cwd=str(RAIZ),
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
        print(f"  ⚠️ ANCLA NO CASA en {rel}: {viejo[:46]!r} — no prueba nada")
        continue
    ancladas += 1
    bak = f.with_suffix(".py.bak_r444")
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
