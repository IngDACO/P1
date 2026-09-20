"""Prueba el guardián de v438 contra código ROTO a propósito (regla v410)."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
VERIF = Path(__file__).with_name("verif_v438.py")
F = {n: RAIZ / "core" / f"{n}.py"
     for n in ("plumb", "diagrams", "schedule", "rail_cut", "buffer_cut", "belting")}

ROTURAS = [
    ("una CLAVE de plumb_table se traduce (rompe el informe)",
     F["plumb"], '"Línea":          LINE_NAMES', '"Line":          LINE_NAMES'),
    ("una CLAVE de schedule_table se traduce",
     F["schedule"], '"Actividad":', '"Activity":'),
    ("una CLAVE de plumb_checks se traduce",
     F["plumb"], '"Medida":', '"Measurement":'),
    ("los NOMBRES de actividad se traducen (son dato del histórico)",
     F["schedule"], '"Plomadas y líneas de referencia"', '"Plumb lines and reference lines"'),
    ("el motor se importa como `d` pelado (taparía con las variables locales)",
     F["schedule"], "from core.i18n import d as _d", "from core.i18n import d"),
    ("una etiqueta del plano vuelve al español",
     F["diagrams"], '{_d("FRONT WALL — ACCESS")}', 'PARED FRONTAL — ACCESO'),
    ("una etiqueta de la plomada vuelve al español",
     F["plumb"], '_d("Left rail plumb line")', '"Plomo riel izquierdo"'),
    ("la leyenda del cronograma vuelve al español",
     F["schedule"], '(_d("Planned"), C_PLAN, False)', '("Planificado", C_PLAN, False)'),
    ("una etiqueta del corte de rieles vuelve al español",
     F["rail_cut"], '{_d("Counterweight")}', 'Contrapeso'),
    ("una etiqueta del corte de buffers vuelve al español",
     F["buffer_cut"], '{_d("CAR STICKER")}', 'STICKER DE CABINA'),
    ("una etiqueta del belting vuelve al español",
     F["belting"], '_d("below FFL")', '"por debajo del FFL"'),
    ("un diagrama vuelve a usar <marker> (svglib lo tiraría del PDF)",
     # ⚠️ apuntada al SVG que el test DIBUJA de verdad, no al stub 10x10 del
     # retorno temprano: una rotura en un camino que nadie ejercita no prueba nada.
     F["diagrams"], 'p.append("</svg>")',
     'p.append("<defs><marker id=\'a\'/></defs></svg>")'),
]


def corre():
    import os
    r = subprocess.run([sys.executable, str(VERIF)], cwd=str(RAIZ),
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return r.returncode


tmp = Path(tempfile.mkdtemp())
for f in F.values():
    shutil.copy2(f, tmp / f.name)

print("Estado SANO:")
print("  OK" if corre() == 0 else "  ⚠️ el guardián ya falla SIN romper nada")

cazadas = 0
for desc, fich, viejo, nuevo in ROTURAS:
    src = fich.read_text(encoding="utf-8")
    if src.count(viejo) < 1:
        print(f"  ⚠️ ANCLA MALA (0×): {desc}")
        continue
    fich.write_text(src.replace(viejo, nuevo, 1), encoding="utf-8")
    rc = corre()
    shutil.copy2(tmp / fich.name, fich)
    if rc != 0:
        cazadas += 1
        print(f"  cazada   {desc}")
    else:
        print(f"  !! NO SE CAZA  {desc}")

print("\nEstado restaurado:")
print("  OK" if corre() == 0 else "  ⚠️ NO restauró")
print(f"\n{cazadas}/{len(ROTURAS)} roturas cazadas")
sys.exit(0 if cazadas == len(ROTURAS) else 1)
