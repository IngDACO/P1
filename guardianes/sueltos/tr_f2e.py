"""F2 (5/5) — los 7 últimos. Con esto los 4 módulos de campo quedan sin español.

De los 11 que quedaban, CUATRO son claves de dato y se quedan como están:
`a.get("grupo", "")` (columna de la hoja Login) y `{"dias": 0}` (clave del dict que
devuelve `resumen_semana`). Traducirlas rompería la lectura sin dar ningún error.
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

R = {
    "core/timeclock_ui.py": [
        # valor por defecto del cronómetro: se ve si un llamador no pasa `label`
        ('def _chronometer(clock_in_str, label="En curso"',
         'def _chronometer(clock_in_str, label="In progress"'),
    ],
    "core/prestart_ui.py": [
        ('st.caption("Firma")', 'st.caption(t("Signature"))'),
        ('st.text_input("Iniciales", key=f"ps_att_ini_{_k}"',
         'st.text_input(t("Initials"), key=f"ps_att_ini_{_k}"'),
    ],
    "core/ausencias_ui.py": [
        ('pie=f"de {s[\'asignados\']:.0f} · usados {s[\'usados\']:.0f}"',
         'pie=f"{t(\'of\')} {s[\'asignados\']:.0f} · {t(\'used\')} {s[\'usados\']:.0f}"'),
        ('_l.append(f"Nota: {nota}")', '_l.append(f"{t(\'Note\')}: {nota}")'),
    ],
    "core/route_ui.py": [
        ('else (sin_plan[0] if len(sin_plan) == 1 else f"{len(sin_plan)} personas"))',
         'else (sin_plan[0] if len(sin_plan) == 1\n'
         '                       else f"{len(sin_plan)} {t(\'people\')}"))'),
    ],
}

fallos = []
for rel, reps in R.items():
    s = (RAIZ / rel).read_text(encoding="utf-8")
    for o, nv in reps:
        if s.count(nv) >= 1 and s.count(o) == 0:
            continue
        if s.count(o) != 1:
            fallos.append(f"{rel} ({s.count(o)}x) {o[:72]!r}")
if fallos:
    print(f"{len(fallos)} anclas no casan:")
    for f in fallos:
        print("   ...", " | ".join(f.splitlines()))
    sys.exit(1)

for rel, reps in R.items():
    p = RAIZ / rel
    s = p.read_text(encoding="utf-8")
    n = 0
    for o, nv in reps:
        if s.count(o) == 1:
            s = s.replace(o, nv, 1)
            n += 1
    ast.parse(s)
    p.write_text(s, encoding="utf-8")
    print(f"  {rel:26} {n} reemplazos")
print("OK")
