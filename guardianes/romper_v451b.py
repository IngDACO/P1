"""Las tres roturas de la DECIMA red: el guardian de v451 tiene que cazarlas.

Un guardian que solo aprueba lo que ya funciona no demuestra nada (regla v410).
"""
import os
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CORE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")
AQUI = pathlib.Path(__file__).parent
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}

ROTURAS = [
    # 1. El segmented_control de Localizaciones se queda sin format_func -> pinta
    #    sus 5 IDs CRUDOS («Equipo · Gastos · Pre-Start · Archivos · Datos»).
    ("projects_ui.py",
     '        format_func=lambda o: {"\U0001F465 Equipo": t(":material/groups: Team"),',
     '        XX_format_func_borrado = {"\U0001F465 Equipo": t(":material/groups: Team"),',
     "el segmented_control de Localizaciones pierde su format_func"),
    # 2. La sub-pestana del detalle vuelve al espanol Y sin t() (traduccion a medias).
    ("projects_ui.py",
     '"\u270F\uFE0F Datos": t(":material/edit: Data"),',
     '"\u270F\uFE0F Datos": ":material/edit: Datos",',
     "la sub-pestana «Datos» vuelve al espanol y pierde su t()"),
    # 3. El tipo de proyecto deja de pasar por etiqueta() -> se veria el valor crudo
    #    guardado en la hoja.
    ("quotes_ui.py", "format_func=_etq", "format_func=str",
     "el tipo de proyecto deja de pasar por etiqueta()"),
    # 4. «avance» vuelve al HTML del detalle.
    ("projects_ui.py", "f'<b>{_av}%</b> ' + t('progress') + '</span>'",
     "f'<b>{_av}%</b> avance</span>'",
     "«avance» vuelve a mezclarse con «h worked»"),
    # 5. Una cabecera <th> vuelve a llevar texto literal.
    ("roster_ui.py", 'background:#fff;">' + "' + t('Person') + '" + '</th>',
     'background:#fff;">Persona</th>',
     "una cabecera <th> del roster vuelve al espanol"),
]

cazadas = 0
for i, (mod, viejo, nuevo, desc) in enumerate(ROTURAS, 1):
    p = CORE / mod
    bak = p.read_text(encoding="utf-8")
    _n = bak.count(viejo)
    # ⚠️ CERO ocurrencias = la rotura no probaria NADA (el ancla ya no existe y el
    # guardian aprobaria sin haberse ejercitado). Varias SI valen: se rompen todas,
    # y se dice cuantas para que el numero no pase desapercibido.
    if _n == 0:
        print(f"{i}. ANCLA MALA (0 ocurrencias) — la rotura no probaria NADA: {desc}")
        continue
    if _n > 1:
        desc += f"  [rompe las {_n} ocurrencias]"
    p.write_text(bak.replace(viejo, nuevo), encoding="utf-8")
    r = subprocess.run([sys.executable, str(AQUI / "verif_v451.py")],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=r"C:\Users\diego\P1\survey_app", env=ENV)
    p.write_text(bak, encoding="utf-8")
    ok = r.returncode != 0
    cazadas += ok
    print(f"{i}. {'CAZADA ' if ok else 'SE ESCAPA'} — {desc}")

print(f"\n{cazadas}/{len(ROTURAS)} roturas cazadas")
sys.exit(0 if cazadas == len(ROTURAS) else 1)
