"""F2 (3/3) — los 9 últimos de los módulos de campo."""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

R = {
    "core/timeclock_ui.py": [
        # sale 3 veces (los tres caminos de fichaje): se sustituyen TODAS
        ('"  :material/schedule: Se abrió también tu jornada."',
         't("  :material/schedule: Your workday was opened too.")', True),
    ],
    "core/prestart_ui.py": [
        ('_kpi("Registrados"', '_kpi(t("Recorded")', False),
    ],
    "core/ausencias_ui.py": [
        ('f"{cfg[\'nombre\']} registrada ({res})." if not cfg["aprobacion"]',
         'f"{cfg[\'nombre\']} recorded ({res})." if not cfg["aprobacion"]', False),
        ('f"<b>{nombre}</b> ha registrado: <b>{cfg[\'nombre\']}</b>",',
         'f"<b>{nombre}</b> has recorded: <b>{cfg[\'nombre\']}</b>",', False),
        ('f"Del {desde} al {hasta}.",', 'f"From {desde} to {hasta}.",', False),
        ('f"Le quedan **{s[\'restantes\']:.0f}** de {s[\'asignados\']:.0f} días "',
         'f"They have **{s[\'restantes\']:.0f}** of {s[\'asignados\']:.0f} days "', False),
    ],
}

fallos = []
for rel, reps in R.items():
    s = (RAIZ / rel).read_text(encoding="utf-8")
    for o, nv, todas in reps:
        if s.count(nv) >= 1 and s.count(o) == 0:
            continue
        if (s.count(o) < 1) or (not todas and s.count(o) != 1):
            fallos.append(f"{rel} ({s.count(o)}x) {o[:75]!r}")
if fallos:
    print(f"{len(fallos)} anclas no casan:")
    for f in fallos:
        print("   ...", " | ".join(f.splitlines()))
    sys.exit(1)

for rel, reps in R.items():
    p = RAIZ / rel
    s = p.read_text(encoding="utf-8")
    n = 0
    for o, nv, todas in reps:
        c = s.count(o)
        if c:
            s = s.replace(o, nv) if todas else s.replace(o, nv, 1)
            n += c if todas else 1
    ast.parse(s)
    p.write_text(s, encoding="utf-8")
    print(f"  {rel:26} {n} reemplazos")
print("OK")
