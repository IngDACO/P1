"""Roturas de v453. Un guardián que solo aprueba no demuestra nada."""
import os
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CORE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")
AQUI = pathlib.Path(__file__).parent
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}

ROTURAS = [
    ("projects_ui.py",
     '''st.warning(t(":material/stethoscope: Not started and already due: **{x}**.")
                   .replace("{x}", ", ".join(x["nombre"] for x in d["paradas"][:3])))''',
     '''st.warning(":material/stethoscope: Not started and already due: **"
                   + ", ".join(x["nombre"] for x in d["paradas"][:3]) + "**.")''',
     "una frase vuelve a partirse en una concatenacion"),

    ("quotes_ui.py",
     '.replace("{x}", str(c.get("ProyectoID"))))',
     ')',
     "⚠️ se quita el .replace() y el marcador {x} se pintaria LITERAL"),

    ("schedule.py", '"cortes"', '"cuts"',
     "⚠️ se traduce la BANDERA de PHASES (la compara detect_flags)"),

    ("payroll.py", '"tipo": "deduccion"', '"tipo": "deduction"',
     "⚠️ se traduce el TIPO del concepto (neto() dejaria de restar la deduccion)"),

    ("schedule.py", '("Puertas de rellano".replace("x","x"))', None, None),  # placeholder
    ("schedule.py", '"Landing doors"', '"Puertas de rellano"',
     "un nombre de actividad vuelve al espanol y deja de casar con la hoja migrada"),
]

cazadas = total = 0
for i, r in enumerate(ROTURAS, 1):
    mod, viejo, nuevo, desc = r
    if desc is None:
        continue
    total += 1
    p = CORE / mod
    bak = p.read_text(encoding="utf-8")
    n = bak.count(viejo)
    if n == 0:
        print(f"{i}. ANCLA MALA (0) — la rotura no probaria NADA: {desc}")
        continue
    p.write_text(bak.replace(viejo, nuevo, 1), encoding="utf-8")
    res = subprocess.run([sys.executable, str(AQUI / "verif_v453.py")],
                         capture_output=True, text=True, encoding="utf-8",
                         errors="replace", cwd=r"C:\Users\diego\P1\survey_app", env=ENV)
    p.write_text(bak, encoding="utf-8")
    ok = res.returncode != 0
    cazadas += ok
    print(f"{i}. {'CAZADA ' if ok else 'SE ESCAPA'} — {desc}")

print(f"\n{cazadas}/{total} roturas cazadas")
sys.exit(0 if cazadas == total else 1)
