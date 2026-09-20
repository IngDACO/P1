"""⚠️ Regla v410: un guardián que solo aprueba el código sano no demuestra nada.

Se rompe el código a propósito, se corre `verif_v441` y se comprueba que FALLA. Cada
rotura apunta a UN chequeo distinto; una rotura cuya ancla no case no prueba nada (la
lección de v438/v439), así que el script lo dice en vez de sumarla como cazada.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
GUARD = AQUI / "verif_v441.py"

ROTURAS = [
    # ── chequeo 1: el invariante de posición ──
    ("core/inventory_ui.py",
     'st.markdown(t("#### :material/qr_code_2: QR code"))',
     'st.markdown("#### :material/qr_code_2: QR code")',
     "1 · se desenvuelve una etiqueta y queda suelta"),
    # ── chequeo 2: las siglas del plano ──
    ("core/rail_cut_ui.py", "LFKK", "LARGO_KK",
     "2 · se traduce una SIGLA del plano"),
    # ── chequeo 3: nadie tapa `t` ──
    ("core/belting_ui.py", "def render_belting_tab():",
     "def render_belting_tab():\n    t = 1",
     "3 · una variable tapa la función `t`"),
    # ── chequeo 4: importa el motor y carga ──
    ("core/buffer_cut_ui.py", "from core.i18n import t, d", "from core.i18n import d",
     "4 · el módulo deja de importar `t`"),
    # ── chequeo 5: LA RED NUEVA (frases sin envolver) ──
    ("core/payroll_ui.py", '"All periods"', '"Todos los periodos"',
     "5 · una frase vuelve al español SIN envolver"),
    ("core/projects_ui.py", '"= real cost of labour"', '"= costo real de la mano de obra"',
     "5 · una frase de la conciliación vuelve al español"),
    # ── chequeo 6: el PDF de las herramientas ──
    ("core/plumb_ui.py", 'd("Plumb setting-out")', '"Replanteo de plomadas"',
     "6 · el título del PDF vuelve al español"),
    ("core/belting_ui.py", 'from core.i18n import t, d', 'from core.i18n import t',
     "6 · el módulo deja de importar `d` (documento sin idioma base)"),
    ("core/buffer_cut_ui.py", 'herramienta="buffers"', 'herramienta="buffer_cutting"',
     "6 · se traduce la CLAVE de toolruns (que es DATO)"),
]


def corre():
    r = subprocess.run([sys.executable, str(GUARD)], cwd=str(RAIZ),
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return r.returncode


rc0 = corre()
print(f"código SANO → {'OK' if rc0 == 0 else 'FALLA'}  (esperado OK)")
if rc0 != 0:
    sys.exit(1)

cazadas = ancladas = 0
for rel, viejo, nuevo, desc in ROTURAS:
    f = RAIZ / rel
    src = f.read_text(encoding="utf-8")
    if viejo not in src:
        print(f"  ⚠️ ANCLA NO CASA en {rel}: {viejo[:44]!r} — no prueba nada")
        continue
    ancladas += 1
    bak = f.with_suffix(".py.bak_romper")
    shutil.copy2(f, bak)
    try:
        f.write_text(src.replace(viejo, nuevo), encoding="utf-8")
        ok = corre() != 0
        cazadas += ok
        print(f"  {'CAZADA     ' if ok else '✗ SE ESCAPÓ'}  {desc}")
    finally:
        shutil.copy2(bak, f)
        bak.unlink()

rc1 = corre()
print(f"\ncódigo RESTAURADO → {'OK' if rc1 == 0 else 'FALLA'}")
print(f"{cazadas}/{ancladas} roturas cazadas ({len(ROTURAS)} intentadas)")
sys.exit(0 if (cazadas == ancladas == len(ROTURAS) and rc1 == 0) else 1)
