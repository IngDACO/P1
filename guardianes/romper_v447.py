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
    # ⚠️ LA rotura que importa: si `_tp` vuelve a llamarse `t`, la comparación con la
    # función de idioma es siempre False y **las deducciones dejan de restarse del
    # neto a pagar**. No da error: cambia el dinero, en silencio.
    ("core/payroll.py", 'elif _tp == "deduccion":', 'elif t == "deduccion":',
     "vuelve el `t` que hace que la DEDUCCION no reste del neto"),
    ("core/credentials.py", 't("Credential not found.")', '"Credencial no encontrada."',
     "un mensaje de credenciales vuelve al espanol"),
    ("core/toolruns.py", '"rieles":   "Rail cutting",', '"rieles":   t("Rail cutting"),',
     "vuelve un t() congelado en HERRAMIENTAS"),
    ("core/plan_data.py", '"hkp":     "Buffer cutting",', '"hkp":     t("Buffer cutting"),',
     "vuelve un t() congelado en USA"),
    # ⚠️ El salto de línea va como `chr(10)`: escrito como `\n` dentro de un heredoc
    # de bash se convierte en un salto REAL y rompe el literal (trampa nº26, cuarta vez).
    ("core/roster.py", "from core.i18n import t" + chr(10), "",
     "roster deja de importar el motor"),
    ("core/inventory.py", 't("Asset not found.")', '"Activo no encontrado."',
     "un mensaje de inventario vuelve al espanol"),
    ("core/manuals.py", 'for _w in d:', 'for _tok in d:',
     "la variable del bucle vuelve a tapar el TOKENIZADOR `_tok`"),
]


def corre():
    r = subprocess.run([sys.executable, str(AQUI / "verif_v447.py")], cwd=str(RAIZ),
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
    bak = f.with_suffix(".py.bak_r447")
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
