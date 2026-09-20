"""F2 — los 14 fragmentos que la herramienta deja a mano.

Son partes de f-string partidas en DOS líneas del fuente: el AST las da como un solo
Constant de `lineno` a `end_lineno`, y sustituir ese rango dentro de una f-string
reescribiría también la continuación. Se cambian por texto, con ancla única.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

R = {
    "core/timeclock_ui.py": [
        ('"** y hoy todavía **no hay Pre-Start** registrado en esa obra."',
         '"** and there is still **no Pre-Start** recorded on that site today."'),
        ('"**. La charla de seguridad de hoy ya está registrada, pero "\n'
         '                   "**tú no constas entre quienes la firmaron**."',
         '"**. Today\'s safety talk is already recorded, but "\n'
         '                   "**you are not among those who signed it**."'),
    ],
    "core/prestart_ui.py": [
        ('" charlas** registradas en esta obra. Se te ofrece la más reciente; "\n'
         '                       "si firmaste otra, díselo a quien la registró."',
         '" talks** recorded on this site. The most recent one is offered; "\n'
         '                       "if you signed a different one, tell whoever recorded it."'),
        ('" como hoja de anexo, sin tocar el documento original."',
         '" as an annex sheet, without touching the original document."'),
        ('" control(es) en NO. El administrador queda avisado."',
         '" control(s) answered NO. The administrator has been notified."'),
    ],
    "core/ausencias_ui.py": [
        ('":material/event_available: Tu año de vacaciones va del **"',
         '":material/event_available: Your leave year runs from **"'),
        ('"** (desde que entraste, el "', '"** (since you started, on "'),
        ('":material/help: Contamos por año natural (**"',
         '":material/help: We are counting by calendar year (**"'),
        ('"**) porque no consta tu fecha de alta. Pídele a tu responsable "\n'
         '                   "que la cargue y el saldo pasará a contar desde tu aniversario."',
         '"**) because your start date is not on record. Ask your manager "\n'
         '                   "to enter it and the balance will count from your anniversary."'),
        ('" este año (usados "', '" this year (used "'),
        ('"). Habla con tu responsable."', '"). Talk to your manager."'),
        ('" día(s)** de "', '" day(s)** of "'),
        ('" día(s)** y te quedan **"', '" day(s)** and you have **"'),
    ],
    "core/route_ui.py": [
        ('". La semana normal es de "\n'
         '                    "lunes a viernes; el fin de semana se añade desde el Panel."',
         '". The normal week is "\n'
         '                    "Monday to Friday; the weekend is added from the Panel."'),
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

import ast
for rel, reps in R.items():
    p = RAIZ / rel
    s = p.read_text(encoding="utf-8")
    n = 0
    for o, nv in reps:
        if s.count(o) == 1:
            s = s.replace(o, nv, 1)
            n += 1
    ast.parse(s)                      # no se escribe un fichero roto
    p.write_text(s, encoding="utf-8")
    print(f"  {rel:26} {n} reemplazos")
print("OK")
