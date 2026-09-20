# -*- coding: utf-8 -*-
"""⚠️ Regla v410: el guardián de v446, probado contra código ROTO."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

ROTURAS = [
    ("core/quotes.py", 't("Quote not found.")', '"Cotización no encontrada."',
     "un mensaje de cotizaciones vuelve al español"),
    ("core/projects.py", 'return "En progreso"', 'return t("In progress")',
     "se traduce el ESTADO que se escribe en la hoja"),
    ("core/ausencias.py", '{"nombre": "Annual leave"', '{"nombre": t("Annual leave")',
     "vuelve el `t()` congelado dentro de TIPOS"),
    ("core/ausencias.py", '"estado_roster": "LEAVE",\n                 "aprobacion": True',
     '"estado_roster": "Leave",\n                 "aprobacion": True',
     "se traduce el estado que va al TABLERO"),
    ("core/orders.py", 't("The order value must be greater than 0.")',
     '"El valor de la orden debe ser mayor que 0."',
     "un mensaje de órdenes vuelve al español"),
    ("core/catalogo.py", "from core.i18n import t\n", "",
     "catalogo deja de importar el motor"),
    ("core/clientes.py", 't("The client name is required.")',
     '"El nombre del cliente es obligatorio."',
     "un mensaje de clientes vuelve al español"),
]


def corre():
    r = subprocess.run([sys.executable, str(AQUI / "verif_v446.py")], cwd=str(RAIZ),
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
        print(f"  ⚠️ ANCLA NO CASA en {rel}: {viejo.splitlines()[0][:46]!r}")
        continue
    ancladas += 1
    bak = f.with_suffix(".py.bak_r446")
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
