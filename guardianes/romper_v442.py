"""⚠️ Regla v410: los dos guardianes nuevos, probados contra código ROTO.

Se rompe a propósito y se comprueba que FALLAN. Una rotura cuya ancla no case no prueba
nada (v438/v439), así que el script lo dice en vez de contarla como cazada.
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
    # ── verif_v442 · red 3: etiquetas cortas ──
    ("verif_v442.py", "core/home_ui.py", '"unassigned"', '"sin asignar"',
     "una etiqueta corta vuelve al español"),
    # ⚠️ El ancla anterior (`t("Total cost")`) estaba DENTRO de `t()`, así que la red
    # 3 lo excluye a propósito y la rotura no probaba nada. Se apunta a la CLAVE de la
    # tabla, que es lo que esa red vigila.
    ("verif_v442.py", "core/projects_ui.py", '"Total cost": f["total"]',
     '"Costo total": f["total"]', "una cabecera de tabla vuelve al español"),
    # ── verif_v442 · los valores por etiqueta() ──
    ("verif_v442.py", "core/payroll_ui.py",
     "from core.i18n import t, etiqueta as _etq", "from core.i18n import t",
     "un módulo deja de importar `etiqueta`"),
    ("verif_v442.py", "core/payroll_ui.py",
     "            _etu = auth.etiqueta_usuarios", "            _etq = auth.etiqueta_usuarios",
     "alguien vuelve a usar `_etq` como variable"),
    ("verif_v442.py", "core/projects_ui.py",
     "P.ESTADOS_MANUAL,\n                                   format_func=_etq,",
     "P.ESTADOS_MANUAL,",
     "el selector de estado pierde el format_func"),
    # ── verif_ramas_muertas ──
    ("verif_ramas_muertas.py", "core/rail_cut_ui.py",
     "    if caso == _C1:", '    if caso.startswith("Caso 1"):',
     "una rama compara con una opción que ya no existe"),
]


def corre(guard):
    r = subprocess.run([sys.executable, str(AQUI / guard)], cwd=str(RAIZ),
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return r.returncode


for g in ("verif_v442.py", "verif_ramas_muertas.py"):
    rc = corre(g)
    print(f"{g:26} código SANO → {'OK' if rc == 0 else 'FALLA'}")
    if rc != 0:
        sys.exit(1)

cazadas = ancladas = 0
for guard, rel, viejo, nuevo, desc in ROTURAS:
    f = RAIZ / rel
    src = f.read_text(encoding="utf-8")
    if viejo not in src:
        print(f"  ⚠️ ANCLA NO CASA en {rel}: {viejo[:44]!r} — no prueba nada")
        continue
    ancladas += 1
    bak = f.with_suffix(".py.bak_r442")
    shutil.copy2(f, bak)
    try:
        f.write_text(src.replace(viejo, nuevo, 1), encoding="utf-8")
        ok = corre(guard) != 0
        cazadas += ok
        print(f"  {'CAZADA     ' if ok else '✗ SE ESCAPÓ'}  [{guard[6:-3]}] {desc}")
    finally:
        shutil.copy2(bak, f)
        bak.unlink()

fin = all(corre(g) == 0 for g in ("verif_v442.py", "verif_ramas_muertas.py"))
print(f"\ncódigo RESTAURADO → {'OK' if fin else 'FALLA'}")
print(f"{cazadas}/{ancladas} roturas cazadas ({len(ROTURAS)} intentadas)")
sys.exit(0 if (cazadas == ancladas == len(ROTURAS) and fin) else 1)
