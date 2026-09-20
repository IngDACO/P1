# -*- coding: utf-8 -*-
"""F5c, quinta y última pasada: los 25 mensajes multilínea que quedaban.

⚠️ Los textos de correo/Telegram de `credentials.notify_expiring` van en idioma BASE
**sin `t()`**: salen de la empresa y su idioma no puede depender de la pantalla de
quien los dispara (regla v436). Lo mismo el mensaje de la ALARMA del pre-start, que
llega por Telegram/email a los administradores.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

C = [
    # ── roster ──
    ("core/roster.py", 'return False, "No se pudo eliminar."',
     'return False, t("Could not delete.")'),
    ("core/roster.py",
     'return True, (f"Trabajo eliminado del catálogo. Se conserva el histórico: "\n'
     '                      f"sigue viéndose con su nombre y color en {usos} "\n'
     '                      f"{\'día ya planificado\' if usos == 1 else \'días ya planificados\'}.")',
     'return True, (t("Job removed from the catalogue. The history is kept: it "\n'
     '                        "still shows with its name and colour on") + f" {usos} "\n'
     '                      + (t("day already planned") if usos == 1\n'
     '                         else t("days already planned")) + ".")'),

    # ── inventory: «Dado de baja» es la NOTA que se escribe, en base ──
    ("core/inventory.py", '"Nota": (motivo or "Dado de baja")',
     '"Nota": (motivo or "Decommissioned")'),

    # ── credentials: pantalla con t(), correo en BASE ──
    ("core/credentials.py", 'f"Credencial «{tipo}» agregada."',
     'f"{t(\'Credential\')} «{tipo}» {t(\'added.\')}"'),
    ("core/credentials.py", 'f"Error guardando: {e}"',
     'f"{t(\'Error saving\')}: {e}"'),
    # ⚠️ correo/Telegram → idioma BASE, sin t()
    ("core/credentials.py", 'estado = "VENCIDA" if dd < 0 else f"vence en {dd} d"',
     'estado = "EXPIRED" if dd < 0 else f"expires in {dd} d"'),
    ("core/credentials.py", 'subject = f"🎫 Credencial {estado}: {tipo} ({usr})"',
     'subject = f"🎫 Credential {estado}: {tipo} ({usr})"'),
    ("core/credentials.py",
     'lines = [f"La credencial <b>{tipo}</b> de <b>{usr}</b> '
     '{(\'está VENCIDA\' if dd < 0 else f\'vence en {dd} días\')}"',
     'lines = [f"The <b>{tipo}</b> credential for <b>{usr}</b> '
     '{(\'has EXPIRED\' if dd < 0 else f\'expires in {dd} days\')}"'),
    ("core/credentials.py", '"Actualízala en la app → Usuarios → Credenciales."',
     '"Update it in the app → Users → Credentials."'),

    # ── prestart ──
    ("core/prestart.py", 'f"No se encontró el Pre-Start {ps_id}."',
     'f"{t(\'Pre-Start not found\')}: {ps_id}."'),
    ("core/prestart.py", 'f"No se pudo guardar la firma: {e}"',
     'f"{t(\'Could not save the signature\')}: {e}"'),
    ("core/prestart.py", 'f"No se pudo generar el PDF: {e}"',
     'f"{t(\'Could not generate the PDF\')}: {e}"'),
    ("core/prestart.py", 'f"No se pudo registrar el pre-start: {e}"',
     'f"{t(\'Could not record the pre-start\')}: {e}"'),
    ("core/prestart.py",
     'f"Esta obra ya tiene el Pre-Start de hoy ({_ids}), registrado por "\n'
     '                f"{_ya[-1].get(\'Facilitador\') or \'—\'}. Si solo faltas tú por constar, "\n'
     '                f"fírmalo en vez de crear otro. Si de verdad hubo una SEGUNDA charla "\n'
     '                f"(otro turno u otra cuadrilla), márcalo y se registra igual.")',
     't("This job already has today\'s Pre-Start") + f" ({_ids}), "\n'
     '                + t("recorded by") + f" {_ya[-1].get(\'Facilitador\') or \'—\'}. "\n'
     '                + t("If you are only missing from the list, sign it instead of "\n'
     '                    "creating another one. If there really was a SECOND briefing "\n'
     '                    "(another shift or crew), tick the box and it is recorded "\n'
     '                    "anyway."))'),
    # ⚠️ las dos ALARMAS van por Telegram/email → idioma BASE
    ("core/prestart.py", 'msg = "Near Miss/Hazard reportado en el Pre-Start"',
     'msg = "Near Miss/Hazard reported in the Pre-Start"'),
    ("core/prestart.py", 'msg = (f"Pre-Start con {len(no_ok)} control(es) en NO: "',
     'msg = (f"Pre-Start with {len(no_ok)} control(s) marked NO: "'),

    # ── rails ──
    ("core/rails.py",
     'return None, ("El catálogo de rieles no está conectado: faltan credenciales "\n'
     '                      "(gcp_service_account) o TIMECLOCK_SHEET_ID en los Secrets.")',
     'return None, t("The rail catalogue is not connected: credentials "\n'
     '                       "(gcp_service_account) or TIMECLOCK_SHEET_ID are missing "\n'
     '                       "from Secrets.")'),
]

for rel, viejo, nuevo in C:
    f = R / rel
    src = f.read_text(encoding="utf-8")
    n = src.count(viejo)
    if n != 1:
        print(f"  ⚠️ {rel}: {n} de {viejo.splitlines()[0][:58]!r}")
        continue
    f.write_text(src.replace(viejo, nuevo, 1), encoding="utf-8")
    print(f"  OK  {rel}: {viejo.splitlines()[0][:58]}")
