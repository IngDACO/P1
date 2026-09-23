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
    ("core/home_ui.py", '":material/receipt_long: Expenses"',
     '":material/receipt_long: Gastos"',
     "un display de la nav vuelve al espanol"),
    # ATENCION: el ID lleva emoji porque ES el identificador; traducirlo deja la
    # rama muerta y la navegacion rota sin dar ningun error.
    ("core/home_ui.py", '("💰 Gastos", ":material/receipt_long: Expenses")',
     '("💰 Expenses", ":material/receipt_long: Expenses")',
     "se traduce el ID de una sub-pestana"),
    ("core/projects_ui.py", '(t("Purchases / materials"), d["compras"])',
     '("Compras / materiales", d["compras"])',
     "una etiqueta del P&L vuelve al espanol"),
    # ⚠️ v515: el ancla decia '"Montaje de rieles (guías)"' y apuntaba a
    # `schedule.py`. Llevaba muerta desde v453, que es cuando esos nombres se migraron
    # al ingles: la rotura pretendia TRADUCIR un nombre espanol que ya no existia. Ahora
    # los nombres viven en el catalogo y la rotura va al reves, que es el riesgo de hoy.
    ("core/stages.py", '(PISTA_INSTALL, 6, "Shaft Climb & Bedplates", 13)',
     '(PISTA_INSTALL, 6, "Montaje de rieles (guías)", 13)',
     "se traduce un nombre de ETAPA (es dato de la hoja)"),
    ("core/inventory_ui.py", '"COPEX Activos"', '"COPEX Assets"',
     "se renombra la carpeta de Drive (dejaria los activos en la vieja)"),
    ("core/chat_agent.py", "Responde SIEMPRE en inglés técnico claro",
     "Responde siempre en español técnico claro",
     "el asistente vuelve a responder en espanol"),
    # ATENCION: el t() a nivel de modulo por QUINTA vez. Se congela al importar.
    ("core/invoices_ui.py", '"pendiente": (":gray[:material/schedule:]", "outstanding")',
     '"pendiente": ":gray[:material/schedule:] " + t("outstanding")',
     "vuelve un t() congelado en el dict de estados de factura"),
]


def corre():
    r = subprocess.run([sys.executable, str(AQUI / "verif_v449.py")], cwd=str(RAIZ),
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
    bak = f.with_suffix(".py.bak_r449")
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
