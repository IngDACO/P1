"""Roturas de la DUODECIMA red. La nº2 es la que de verdad importa: es el fallo
que yo mismo introduje y que compilaba — traducir el estado que se ESCRIBE en la
hoja de Google."""
import os
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CORE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")
AQUI = pathlib.Path(__file__).parent
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}

ROTURAS = [
    ("invoices_ui.py", '"Estado":    _etq(I.estado_cobro(f))', '"Estado":    I.estado_cobro(f)',
     "la celda de Facturas vuelve a mostrar el estado en crudo"),
    ("projects_ui.py", '"Estado": P.derive_estado(0, est, tipo),',
     '"Estado": _etq(P.derive_estado(0, est, tipo)),',
     "⚠️ se traduce el estado que se ESCRIBE en la hoja (guardaria ingles en Sheets)"),
    ("quotes_ui.py", '"Estado": _etq(Q.estado_de(c))', '"Estado": Q.estado_de(c)',
     "la celda de Cotizaciones vuelve al crudo"),
    ("clientes_ui.py", "from core.i18n import t, etiqueta as _etq",
     "from core.i18n import t",
     "un modulo usa _etq sin importarlo (NameError al abrir la pantalla)"),
    ("projects_ui.py", 't(":material/check_circle: open"))', '":material/check_circle: abierta")',
     "un ternario ASIMETRICO: una rama traducida y la otra en espanol"),
    ("auth_ui.py", 'else t("missing")))', 'else "falta"))',
     "la columna Contacto vuelve a mezclar `yes` y `falta`"),
    ("projects_ui.py", '{t("Planned"): cur["plan"], t("Actual"): cur["real"]}',
     '{"Planificado": cur["plan"], "Real": cur["real"]}',
     "la leyenda del chart consolidado vuelve a ser un literal espanol"),
    ("projects_ui.py", '{t("Progress %"): [r["Avance %"] for r in rows]}',
     '{"Avance %": [r["Avance %"] for r in rows]}',
     "la leyenda del bar_chart de avance vuelve a literal"),
    ("quotes_ui.py", 'st.success(":material/check_circle: " + t("You are at") + " **"',
     'st.success(":material/check_circle: Vas **"',
     "vuelve el «Vas» espanol en la rama hermana de `You are at`"),
]

cazadas = 0
for i, (mod, viejo, nuevo, desc) in enumerate(ROTURAS, 1):
    p = CORE / mod
    bak = p.read_text(encoding="utf-8")
    n = bak.count(viejo)
    if n == 0:
        print(f"{i}. ANCLA MALA (0) — la rotura no probaria NADA: {desc}")
        continue
    p.write_text(bak.replace(viejo, nuevo, 1), encoding="utf-8")
    r = subprocess.run([sys.executable, str(AQUI / "verif_v452.py")],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=r"C:\Users\diego\P1\survey_app", env=ENV)
    p.write_text(bak, encoding="utf-8")
    ok = r.returncode != 0
    cazadas += ok
    print(f"{i}. {'CAZADA ' if ok else 'SE ESCAPA'} — {desc}")

print(f"\n{cazadas}/{len(ROTURAS)} roturas cazadas")
sys.exit(0 if cazadas == len(ROTURAS) else 1)
