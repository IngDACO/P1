"""Prueba `verif_v439.py` contra código ROTO (regla v410).

Un guardián que solo aprueba lo que ya funciona no demuestra nada. Cada rotura es un
fallo REAL que podría cometerse; si el guardián sigue en verde, está ciego.
Respalda, rompe, corre el guardián, restaura. Restaura SIEMPRE (incluso si revienta).
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
AQUI = Path(__file__).parent
GUARD = AQUI / "verif_v439.py"

ROTURAS = [
    # ⚠️ PARCIAL a propósito: es la peor variante (unos sitios leen la clave vieja y
    # otros la nueva) y la que un chequeo de presencia deja pasar.
    ("traducir UNA aparición de una clave de dato", "core/timeclock_ui.py",
     '"clock_in"', '"clock_start"'),

    ("el correo usa t() (idioma de la pantalla) en vez de _d",
     "core/notify.py",
     '_d("Open it in the app → 📋 My projects.")',
     't("Open it in the app → 📋 My projects.")'),

    # ⚠️ «Registrados» NO lleva acento ni palabra funcional: el detector de español no
    # lo ve. Lo tiene que cazar el chequeo POSITIVO (el inglés esperado ya no está).
    ("una etiqueta de campo vuelve al español", "core/prestart_ui.py",
     't("Recorded")', 't("Registrados")'),

    ("la variable del bucle vuelve a llamarse `t` (tapa el motor)",
     "core/ausencias_ui.py",
     "for _tp, cfg in AU.TIPOS.items():\n        s = AU.saldo(grupo, usuario, _tp)",
     "for t, cfg in AU.TIPOS.items():\n        s = AU.saldo(grupo, usuario, t)"),

    ("`t` local en timeclock (el UnboundLocalError de v437)",
     "core/timeclock_ui.py",
     "_ci = _dt.strptime(s[\"clock_in\"], timeclock.FMT)",
     "t = _dt.strptime(s[\"clock_in\"], timeclock.FMT)"),

    # ⚠️ Va en notify.py: `route_ui` NO tiene ni una llamada a logger, así que apuntar
    # ahí era una rotura sobre código que no existe — no probaba nada (v438).
    ("se envuelve un mensaje de LOG en _d()", "core/notify.py",
     'logger.warning("telegram getUpdates: %s", e)',
     'logger.warning(_d("telegram getUpdates: %s"), e)'),

    ("el motor deja de importarse a nivel de módulo", "core/route_ui.py",
     "from core.i18n import t", "# from core.i18n import t"),

    ("un cuerpo de correo vuelve al español", "core/alerts.py",
     '_d("Alert on project")', '"Alarma en proyecto"'),
]


def corre():
    r = subprocess.run([sys.executable, str(GUARD)], cwd=str(RAIZ),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode


print("guardián sobre el código SANO...")
if corre() != 0:
    print("  ⚠️ ya falla en sano — no tiene sentido seguir")
    sys.exit(1)
print("  OK (verde)\n")

ok = True
for i, (titulo, rel, viejo, nuevo) in enumerate(ROTURAS, 1):
    p = RAIZ / rel
    bak = p.with_suffix(p.suffix + ".bak_romper")
    shutil.copy2(p, bak)
    try:
        s = p.read_text(encoding="utf-8")
        if s.count(viejo) < 1:
            print(f"  {i}. ⚠️ ANCLA NO CASA — la rotura no se aplicó: {titulo}")
            ok = False
            continue
        p.write_text(s.replace(viejo, nuevo, 1), encoding="utf-8")
        rc = corre()
        estado = "CAZADA" if rc != 0 else "⚠️ NO LA VE"
        print(f"  {i}. {estado:12} {titulo}")
        ok = ok and rc != 0
    finally:
        shutil.copy2(bak, p)
        bak.unlink()

print(f"\nguardián tras restaurar: {'verde' if corre() == 0 else '⚠️ ROJO — algo no se restauró'}")
print(f"{len(ROTURAS)} roturas — " + ("las caza TODAS" if ok else "HAY CIEGAS"))
sys.exit(0 if ok else 1)
