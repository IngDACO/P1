# -*- coding: utf-8 -*-
"""⚠️ Regla v410: el guardián de v443, probado contra código ROTO.

Una rotura cuya ancla no case no prueba nada (v438/v439), así que el script lo dice
en vez de contarla como cazada.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

ROTURAS = [
    # ── red 4: fragmento de UNA palabra ──
    ("core/home_ui.py", 'f"{g[\'alarmas\']} alarms"', 'f"{g[\'alarmas\']} alarmas"',
     "un fragmento de UNA palabra vuelve al español"),
    # ── red 4: f-string a medio traducir ──
    ("core/invoices_ui.py",
     'help=f"Collected {_T.dinero(cob)} of {_T.dinero(total)}")',
     'help=f"Collected {_T.dinero(cob)} de {_T.dinero(total)}")',
     "una f-string queda a medio traducir"),
    ("core/projects_ui.py",
     '_l = (f"You have spent **{_T.dinero(cp[\'total\'], 0)}** of {_T.dinero(pres, 0)}"',
     '_l = (f"Llevas **{_T.dinero(cp[\'total\'], 0)}** de {_T.dinero(pres, 0)}"',
     "el titular de costos vuelve al español"),
    # ── el import que falta (NameError en producción) ──
    ("core/invoices_ui.py", "from core.i18n import t, d", "from core.i18n import t",
     "un módulo usa `d()` y deja de importarlo"),
    # ── el DATO: traducir la columna del editor rompería reabrir un cálculo ──
    ("core/rail_cut_ui.py", 'in_edit[f"Elevador {i+1}"]', 'in_edit[f"Lift {i+1}"]',
     "se traduce la columna PERSISTIDA del editor"),
    ("core/plumb_ui.py", 'disabled=["Elevador"]', 'disabled=["Lift"]',
     "se traduce la columna del editor de plomada"),
    # ── la tabla de resultado que va al PDF de obra ──
    ("core/rail_cut_ui.py", '_filas = [{d("Lift"): i + 1, "L (mm)"',
     '_filas = [{"Elevador": i + 1, "L (mm)"',
     "la tabla del PDF vuelve al español"),
]


def corre():
    r = subprocess.run([sys.executable, str(AQUI / "verif_v443.py")], cwd=str(RAIZ),
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
    bak = f.with_suffix(".py.bak_r443")
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
