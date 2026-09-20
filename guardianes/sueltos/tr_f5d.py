# -*- coding: utf-8 -*-
"""F5d: correos (`email_notify`) y radar del admin (`admin_digest`).

⚠️ `email_notify` va en idioma BASE **sin `t()`**: es un correo que sale de la
empresa (regla v436).
⚠️ `admin_digest.digest_text` alimenta DOS cosas: el resumen que se PINTA y el
contexto que se le pasa a la IA. Va con `t()` — el prompt de la IA se construye con
lo mismo, y que el modelo lea inglés es lo coherente con el resto.
⚠️ `d` ya es variable en 3 funciones de `admin_digest`, así que solo entra `t`.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

# import solo para admin_digest (email_notify va en base, sin motor)
f = R / "core/admin_digest.py"
s = f.read_text(encoding="utf-8")
if "from core.i18n import t" not in s:
    a = "logger = logging.getLogger(__name__)"
    assert s.count(a) == 1, s.count(a)
    f.write_text(s.replace(a, f"from core.i18n import t\n{a}", 1), encoding="utf-8")
    print("  OK  admin_digest: import añadido")

C = [
    # ── email_notify: idioma BASE, sin t() ──
    ("core/email_notify.py", '"⚠️ (con push extra por pared)"',
     '"⚠️ (with extra push for the wall)"'),
    ("core/email_notify.py", '"Valores fuera de límite"', '"Values out of limit"'),
    ("core/email_notify.py", '"OFF por columna"', '"OFF per column"'),
    ("core/email_notify.py", '"BSR ≥ BS — Sin ajuste requerido ✅"',
     '"BSR ≥ BS — No adjustment required ✅"'),
    ("core/email_notify.py", '"Ctrl en frame"', '"Ctrl in frame"'),

    # ── admin_digest: pantalla + contexto de la IA ──
    ("core/admin_digest.py", '"VENCIDOS:"', 't("OVERDUE:")'),
    ("core/admin_digest.py", '"Por vencer (≤7 d):"', 't("Due soon (≤7 d):")'),
    ("core/admin_digest.py", '"En retraso (SPI):"', 't("Behind schedule (SPI):")'),
    ("core/admin_digest.py", '"Alarmas abiertas:"', 't("Open alarms:")'),
    ("core/admin_digest.py", '"Sin campo asignado:"', 't("No field staff assigned:")'),
    ("core/admin_digest.py",
     '"Campo sin contacto completo (no se les puede notificar):"',
     't("Field staff without full contact details (they cannot be notified):")'),
    ("core/admin_digest.py", '"Credenciales por vencer/vencidas:"',
     't("Credentials expiring/expired:")'),
    ("core/admin_digest.py", '"Sobre presupuesto:"', 't("Over budget:")'),
    ("core/admin_digest.py", '"Sin pendientes urgentes."', 't("No urgent items.")'),
    ("core/admin_digest.py", '"Usuarios de campo:"', 't("Field staff:")'),
    ("core/admin_digest.py", '"(SIN contacto completo)"',
     't("(NO full contact details)")'),
]

for rel, viejo, nuevo in C:
    p = R / rel
    src = p.read_text(encoding="utf-8")
    n = src.count(viejo)
    if n != 1:
        print(f"  ⚠️ {rel}: {n} de {viejo[:52]!r}")
        continue
    p.write_text(src.replace(viejo, nuevo, 1), encoding="utf-8")
    print(f"  OK  {rel}: {viejo[:52]}")
