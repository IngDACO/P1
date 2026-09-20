"""F3-A · los 2 que `aplicar.py` deja a mano.

Son partes de f-string partidas en DOS líneas del fuente: el AST las da como un solo
Constant de `lineno` a `end_lineno`, así que sustituir ese rango reescribiría también la
continuación. Se cambian por texto, con ancla única.
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

R = {
    "core/catalogo_ui.py": [
        # ⚠️ En dos anclas de UNA línea cada una: copiar el sangrado exacto de la
        # continuación a mano es como se falla (34 espacios, no 29).
        ('{r[\'inactivos\']} desactivado(s). No se borran: "',
         '{r[\'inactivos\']} deactivated. They are not deleted: "'),
        ('"las cotizaciones viejas deben seguir mostrando su nombre.")',
         '"old quotes must keep showing their name.")'),
    ],
    "core/clientes_ui.py": [
        ('f"Toca un cliente para ver su ficha, su resumen y sus proyectos. "',
         'f"Tap a client to see its record, summary and projects. "'),
    ],
}

fallos = []
for rel, reps in R.items():
    s = (RAIZ / rel).read_text(encoding="utf-8")
    for o, nv in reps:
        if s.count(nv) == 1 and s.count(o) == 0:
            continue
        if s.count(o) != 1:
            fallos.append(f"{rel} ({s.count(o)}x) {o[:70]!r}")
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
