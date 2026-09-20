"""Cinco versiones ROTAS: el guardian de v451 tiene que cazarlas todas."""
import pathlib, shutil, subprocess, sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CORE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")
AQUI = pathlib.Path(__file__).parent
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}

ROTURAS = [
 ("survey_ui.py", 'st.markdown(f"**{t(_titulo)}**")', 'st.markdown(f"**{_titulo}**")',
  "la traduccion vuelve a NO aplicarse al pintar"),
 ("survey_ui.py", '(":material/crop_free: Shaft",            ["BS", "TS"])',
  '(":material/crop_free: Hueco",            ["BS", "TS"])',
  "un grupo vuelve al espanol"),
 ("survey_ui.py", '{_FASE_DATOS: t(":material/edit: Survey data"),',
  '{_FASE_DATOS: ":material/edit: Survey data",',
  "media traduccion en el format_func de la fase"),
 ("projects_ui.py", 'st.info(t(":material/info: There are no invoices',
  'st.info((":material/info: There are no invoices',
  "un ternario de display pierde su t()"),
 ("survey_ui.py", '(":material/elevator: Car",               ["BK", "TK", "BKS"])',
  '(":material/elevator: ' + 't' + '(\\"Car\\")",               ["BK", "TK", "BKS"])',
  "se mete t() DENTRO de la constante de modulo (se congelaria)"),
]

cazadas = 0
for i, (mod, viejo, nuevo, desc) in enumerate(ROTURAS, 1):
    p = CORE / mod
    bak = p.read_text(encoding="utf-8")
    if bak.count(viejo) != 1:
        print(f"{i}. ‼️ ANCLA MALA ({bak.count(viejo)} ocurrencias) — la rotura no probaria NADA: {desc}")
        continue
    p.write_text(bak.replace(viejo, nuevo), encoding="utf-8")
    r = subprocess.run([sys.executable, str(AQUI / "verif_v451.py")],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=r"C:\Users\diego\P1\survey_app", env=ENV)
    p.write_text(bak, encoding="utf-8")
    ok = r.returncode != 0
    cazadas += ok
    print(f"{i}. {'CAZADA ' if ok else '‼️ SE ESCAPA'} — {desc}")

print(f"\n{cazadas}/{len(ROTURAS)} roturas cazadas")
sys.exit(0 if cazadas == len(ROTURAS) else 1)
