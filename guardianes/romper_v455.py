"""Roturas de v455."""
import os
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CORE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")
AQUI = pathlib.Path(__file__).parent
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}

ROTURAS = [
    ("finance.py",
     '''    mo    = E.labor_cost(pid, grupo)
    costo = round(mo + mat, 2)''',
     '''    mo    = E.labor_cost(pid, grupo) * (1 + 20 / 100.0)
    costo = round(mo + mat, 2)''',
     "vuelve la formula del % sobre la mano de obra"),

    ("projects.py",
     '''    "MargenMO",''',
     '''''',
     "⚠️ se quita MargenMO de HEADERS y la fila POSICIONAL descuadra"),

    ("quotes_ui.py",
     "_m = auth.group_margin_default(grupo)",
     "_m = 0.0",
     "la linea de cotizacion pierde su margen de partida"),
]

cazadas = 0
for i, (mod, viejo, nuevo, desc) in enumerate(ROTURAS, 1):
    p = CORE / mod
    bak = p.read_text(encoding="utf-8")
    n = bak.count(viejo)
    if n != 1:
        print(f"{i}. ANCLA x{n} — la rotura no probaria nada: {desc}")
        continue
    p.write_text(bak.replace(viejo, nuevo, 1), encoding="utf-8")
    r = subprocess.run([sys.executable, str(AQUI / "verif_v455.py")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       cwd=r"C:\Users\diego\P1\survey_app", env=ENV)
    p.write_text(bak, encoding="utf-8")
    ok = r.returncode != 0
    cazadas += ok
    print(f"{i}. {'CAZADA ' if ok else 'SE ESCAPA'} — {desc}")

print(f"\n{cazadas}/{len(ROTURAS)} roturas cazadas")
sys.exit(0 if cazadas == len(ROTURAS) else 1)
