"""F1d — los correos y las alarmas, en inglés. Con esto F1 queda completo.

Van con `_d` (idioma BASE, alias porque `d` ya es variable en los dos módulos): un
correo o un Telegram SALE de la app, así que su idioma no puede depender de cómo tenga
la pantalla quien lo dispara — igual que una factura (regla de v436).

⚠️ NO se tocan `"Fecha"` ni `"Usuario"` de `alerts.py`: son NOMBRES DE COLUMNA de la
hoja `Alarmas`, no etiquetas. Traducirlos escribiría en la columna de al lado.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

Q = chr(34)   # comilla doble, para no pelearme con el escapado

NOTIFY = [
    ('subject = f"📋 Nuevo proyecto asignado: {nombre}"',
     'subject = f"📋 {_d(' + Q + 'New project assigned' + Q + ')}: {nombre}"'),

    ('_ubic_line = (f\'Ubicación: <a href="{_ubic_url}">{_ubic}</a>\' if _ubic_url\n'
     '                  else f"Ubicación: {_ubic or \'—\'}")',
     '_ubic_line = (f\'{_d("Location")}: <a href="{_ubic_url}">{_ubic}</a>\' if _ubic_url\n'
     '                  else f"{_d(' + Q + 'Location' + Q + ')}: {_ubic or \'—\'}")'),

    ('f"Te asignaron al proyecto <b>{nombre}</b>.",\n'
     '        f"Cliente: {prj.get(\'Cliente\', \'—\')}",\n'
     '        _ubic_line,\n'
     '        f"Inicio: {prj.get(\'FechaInicio\', \'—\')}  ·  Fin est.: {prj.get(\'FechaFinEst\', \'—\')}",',
     'f"{_d(' + Q + 'You have been assigned to project' + Q + ')} <b>{nombre}</b>.",\n'
     '        f"{_d(' + Q + 'Client' + Q + ')}: {prj.get(\'Cliente\', \'—\')}",\n'
     '        _ubic_line,\n'
     '        f"{_d(' + Q + 'Start' + Q + ')}: {prj.get(\'FechaInicio\', \'—\')}  ·  "\n'
     '        f"{_d(' + Q + 'Est. finish' + Q + ')}: {prj.get(\'FechaFinEst\', \'—\')}",'),

    ('lines.append("📝 <b>Inducciones a completar:</b>")',
     'lines.append(f"📝 <b>{_d(' + Q + 'Inductions to complete' + Q + ')}:</b>")'),

    ('lines.append("Ábrelo en la app → 📋 Mis proyectos.")',
     'lines.append(_d("Open it in the app → 📋 My projects."))'),

    ('subject = f"📝 Inducciones del proyecto {project_name}"',
     'subject = f"📝 {_d(' + Q + 'Project inductions' + Q + ')}: {project_name}"'),

    ('lines = [f"Completa las inducciones del proyecto <b>{project_name}</b>:"]',
     'lines = [f"{_d(' + Q + 'Complete the inductions for project' + Q + ')} '
     '<b>{project_name}</b>:"]'),
]

ALERTS = [
    ('return None, "Google Sheets no está configurado."',
     'return None, _d("Google Sheets is not configured.")'),

    ('return None, f"No se pudo abrir la hoja {ALERTS_SHEET}: {e}"',
     'return None, f"{_d(' + Q + 'Could not open sheet' + Q + ')} {ALERTS_SHEET}: {e}"'),

    ('return True, "Alarma resuelta."', 'return True, _d("Alert resolved.")'),
    ('return False, "Alarma no encontrada."', 'return False, _d("Alert not found.")'),

    ('f"Alarma en proyecto {project_name or pid}",\n'
     '            [f"<b>Problema reportado</b> por {creado_por}:", mensaje,\n'
     '             f"Proyecto: {project_name or pid}."])',
     'f"{_d(' + Q + 'Alert on project' + Q + ')} {project_name or pid}",\n'
     '            [f"<b>{_d(' + Q + 'Problem reported by' + Q + ')}</b> {creado_por}:", mensaje,\n'
     '             f"{_d(' + Q + 'Project' + Q + ')}: {project_name or pid}."])'),

    ('f"Actualización en {project_name or pid}",\n'
     '                [f"El administrador actualizó el proyecto <b>{project_name or pid}</b>:", mensaje])',
     'f"{_d(' + Q + 'Update on' + Q + ')} {project_name or pid}",\n'
     '                [f"{_d(' + Q + 'The administrator updated project' + Q + ')} '
     '<b>{project_name or pid}</b>:", mensaje])'),
]

TODO = [("core/notify.py", NOTIFY), ("core/alerts.py", ALERTS)]

fallos = []
for rel, reps in TODO:
    s = (RAIZ / rel).read_text(encoding="utf-8")
    for o, nv in reps:
        if s.count(nv) == 1 and s.count(o) == 0:
            continue
        if s.count(o) != 1:
            fallos.append(f"{rel} ({s.count(o)}x) {o[:80]!r}")
if fallos:
    print(f"{len(fallos)} anclas no casan:")
    for f in fallos:
        print("   ...", " | ".join(f.splitlines()))
    sys.exit(1)

for rel, reps in TODO:
    p = RAIZ / rel
    s = p.read_text(encoding="utf-8")
    n = 0
    for o, nv in reps:
        if s.count(o) == 1:
            s = s.replace(o, nv, 1)
            n += 1
    if "from core.i18n import d as _d" not in s:
        # ⚠️ alias: `d` ya es variable en los dos módulos y taparía la función en el
        # ámbito entero de su función (el fallo de v437).
        m = re.search(r"^(from|import) .+$", s, re.M)
        assert m, rel
        s = s[:m.end()] + chr(10) + chr(10) + "from core.i18n import d as _d" + s[m.end():]
    p.write_text(s, encoding="utf-8")
    print(f"  {rel:20} {n} reemplazos")
print("OK")
