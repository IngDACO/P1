# -*- coding: utf-8 -*-
"""F5d, segunda pasada: los textos REALES de `email_notify` y `admin_digest`.

Los anclajes de la primera pasada no casaron porque las cadenas van con un espacio
final dentro de una concatenación (`"VENCIDOS: " + "; ".join(...)`), no sueltas.
Copiar el texto del fuente, no reescribirlo de memoria.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

C = [
    # ── email_notify: idioma BASE (sale de la empresa, regla v436) ──
    ("core/email_notify.py", '" ⚠️ (con push extra por pared)"',
     '" ⚠️ (with extra push for the wall)"'),
    ("core/email_notify.py",
     'f"DIF = {bs_result.get(\'dif_original\')} mm — No encontrado en rangos ❌"',
     'f"DIF = {bs_result.get(\'dif_original\')} mm — Not found in any range ❌"'),
    ("core/email_notify.py", "'Sí — Parada ' + str(p.get('WALL_STOP')) + ' lado '",
     "'Yes — Stop ' + str(p.get('WALL_STOP')) + ' side '"),
    ("core/email_notify.py", "'Sí — lado ' + str(p.get('CTRL_SIDE'))",
     "'Yes — side ' + str(p.get('CTRL_SIDE'))"),
    ("core/email_notify.py",
     '{"Adjuntos: plano PDF + " if pdf_bytes else ""}Matriz survey incluida arriba.',
     '{"Attachments: drawing PDF + " if pdf_bytes else ""}Survey matrix included above.'),
    ("core/email_notify.py", '<h3 style="color:#1a3a5c;margin-top:20px">Solución óptima</h3>',
     '<h3 style="color:#1a3a5c;margin-top:20px">Optimal solution</h3>'),

    # ── admin_digest: pantalla + contexto de la IA ──
    ("core/admin_digest.py",
     'L = [f"Grupo {d[\'grupo\']}: {d[\'n_activos\']} proyecto(s) activo(s) de {d[\'n_total\']}, "\n'
     '         f"avance promedio {d[\'avance_prom\']}%, {d[\'horas\']} horas registradas."]',
     'L = [f"{t(\'Group\')} {d[\'grupo\']}: {d[\'n_activos\']} "\n'
     '         + t("active project(s) of") + f" {d[\'n_total\']}, "\n'
     '         + t("average progress") + f" {d[\'avance_prom\']}%, {d[\'horas\']} "\n'
     '         + t("hours recorded.")]'),
    ("core/admin_digest.py", 'L.append("VENCIDOS: " + "; ".join(',
     'L.append(t("OVERDUE:") + " " + "; ".join('),
    ("core/admin_digest.py", 'f"{x[\'nombre\']} (hace {abs(x[\'dias\'])} d, fin {x[\'fin\']})"',
     'f"{x[\'nombre\']} ({abs(x[\'dias\'])} d {t(\'ago\')}, {t(\'end\')} {x[\'fin\']})"'),
    ("core/admin_digest.py", 'L.append("Por vencer (≤7 d): " + "; ".join(',
     'L.append(t("Due soon (≤7 d):") + " " + "; ".join('),
    ("core/admin_digest.py", 'f"{x[\'nombre\']} (en {x[\'dias\']} d, {x[\'fin\']})"',
     'f"{x[\'nombre\']} ({t(\'in\')} {x[\'dias\']} d, {x[\'fin\']})"'),
    ("core/admin_digest.py", 'L.append("En retraso (SPI): " + "; ".join(',
     'L.append(t("Behind schedule (SPI):") + " " + "; ".join('),
    ("core/admin_digest.py", 'L.append("Alarmas abiertas: " + "; ".join(',
     'L.append(t("Open alarms:") + " " + "; ".join('),
    ("core/admin_digest.py", 'L.append("Near miss recientes (≤7 d): "',
     'L.append(t("Recent near misses (≤7 d):") + " "'),
    ("core/admin_digest.py", 'L.append("Sin campo asignado: " + "; ".join(',
     'L.append(t("No field staff assigned:") + " " + "; ".join('),
    ("core/admin_digest.py",
     'L.append("Campo sin contacto completo (no se les puede notificar): "',
     'L.append(t("Field staff without full contact details "\n'
     '                   "(they cannot be notified):") + " "'),
    ("core/admin_digest.py",
     'L.append("Reciben las alarmas pero NO tienen email ni Telegram (la alarma "\n'
     '                 "queda en la app y no les llega): "',
     'L.append(t("They receive the alarms but have NO email or Telegram (the "\n'
     '                   "alarm stays in the app and never reaches them):") + " "'),
    ("core/admin_digest.py", 'L.append("Credenciales por vencer/vencidas: "',
     'L.append(t("Credentials expiring/expired:") + " "'),
    ("core/admin_digest.py", 'L.append("Sobre presupuesto: "',
     'L.append(t("Over budget:") + " "'),
    ("core/admin_digest.py", 'f"El grupo {grupo} no tiene proyectos."',
     'f"{t(\'Group\')} {grupo} {t(\'has no projects.\')}"'),
    ("core/admin_digest.py", '" (SIN contacto completo)"',
     '" " + t("(NO full contact details)")'),
    ("core/admin_digest.py", '"Usuarios de campo: "', 't("Field staff:") + " "'),
]

for rel, viejo, nuevo in C:
    p = R / rel
    src = p.read_text(encoding="utf-8")
    n = src.count(viejo)
    if n != 1:
        print(f"  ⚠️ {rel}: {n} de {viejo.splitlines()[0][:56]!r}")
        continue
    p.write_text(src.replace(viejo, nuevo, 1), encoding="utf-8")
    print(f"  OK  {rel}: {viejo.splitlines()[0][:56]}")
