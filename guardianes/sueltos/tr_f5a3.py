# -*- coding: utf-8 -*-
"""F5a, tercera pasada: los f-strings de `auth.py` y `timeclock.py`.

⚠️ `etq` («jornada»/«proyecto») es la ETIQUETA que se pinta dentro del mensaje, no
un dato: `_tipo_of` compara contra las constantes `TIPO_GENERAL`/`TIPO_PROYECTO`, y
lo que se guarda en la columna `Tipo` de la hoja son esas constantes, no este texto.
Comprobado antes de tocarlo.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

CAMBIOS = [
    # ── auth.py ──
    ("core/auth.py", '"La columna Zona aún no existe en la hoja Grupos."',
     't("The Zona column does not exist yet in the Groups sheet.")'),
    ("core/auth.py", '"La columna MargenDefault aún no existe en la hoja Grupos."',
     't("The MargenDefault column does not exist yet in the Groups sheet.")'),
    ("core/auth.py", '"La columna ImpuestoDefault aún no existe en la hoja Grupos."',
     't("The ImpuestoDefault column does not exist yet in the Groups sheet.")'),
    ("core/auth.py", 'f"La columna {field} aún no existe en la hoja Grupos."',
     'f"{t(\'The column\')} {field} {t(\'does not exist yet in the Groups sheet.\')}"'),
    ("core/auth.py", 'f"El grupo \'{nombre}\' ya existe."',
     'f"{t(\'Group\')} \'{nombre}\' {t(\'already exists.\')}"'),
    ("core/auth.py", 'f"Grupo \'{nombre}\' eliminado."',
     'f"{t(\'Group\')} \'{nombre}\' {t(\'deleted.\')}"'),
    ("core/auth.py", 'f"Tarifa de \'{usuario}\' actualizada."',
     'f"{t(\'Rate for\')} \'{usuario}\' {t(\'updated.\')}"'),
    ("core/auth.py", 'f"El usuario \'{usuario}\' ya existe."',
     'f"{t(\'User\')} \'{usuario}\' {t(\'already exists.\')}"'),
    ("core/auth.py", 'f"Usuario \'{usuario}\' creado ({rol})."',
     'f"{t(\'User\')} \'{usuario}\' {t(\'created\')} ({rol})."'),
    ("core/auth.py", 'f"Grupo de \'{usuario}\' → {grupo}."',
     'f"{t(\'Group for\')} \'{usuario}\' → {grupo}."'),
    ("core/auth.py", 'f"Contraseña de \'{usuario}\' actualizada."',
     'f"{t(\'Password for\')} \'{usuario}\' {t(\'updated.\')}"'),
    ("core/auth.py", 'f"Rol de \'{usuario}\' → {rol}."',
     'f"{t(\'Role for\')} \'{usuario}\' → {rol}."'),
    ("core/auth.py", 'f"Usuario \'{usuario}\' eliminado."',
     'f"{t(\'User\')} \'{usuario}\' {t(\'deleted.\')}"'),

    # ── timeclock.py ──
    ("core/timeclock.py",
     '"El fichaje no está conectado: faltan credenciales '
     '(gcp_service_account) o TIMECLOCK_SHEET_ID."',
     't("The timeclock is not connected: credentials (gcp_service_account) '
     'or TIMECLOCK_SHEET_ID are missing.")'),
    ("core/timeclock.py",
     'etq = "jornada" if tipo == TIPO_GENERAL else "proyecto"\n'
     '            return False, f"Ya tienes un clock in de {etq} abierto desde '
     '{r.get(\'Clock In\')}."',
     'etq = t("workday") if tipo == TIPO_GENERAL else t("project")\n'
     '            return False, (f"{t(\'You already have a clock in for\')} {etq} "\n'
     '                           f"{t(\'open since\')} {r.get(\'Clock In\')}.")'),
    ("core/timeclock.py",
     'etq = "Jornada (general)" if tipo == TIPO_GENERAL else "Proyecto"\n'
     '    return True, f"✅ Clock IN {etq} a las {_now()}."',
     'etq = t("Workday (general)") if tipo == TIPO_GENERAL else t("Project")\n'
     '    return True, f"✅ Clock IN {etq} {t(\'at\')} {_now()}."'),
    ("core/timeclock.py",
     'etq = "jornada" if tipo == TIPO_GENERAL else "proyecto"\n'
     '        return False, f"No tienes un clock in de {etq} abierto."',
     'etq = t("workday") if tipo == TIPO_GENERAL else t("project")\n'
     '        return False, f"{t(\'You have no open clock in for\')} {etq}."'),
    ("core/timeclock.py",
     'return True, f"✅ Clock OUT a las {out_ts}. Horas trabajadas: {horas}."',
     'return True, (f"✅ Clock OUT {t(\'at\')} {out_ts}. "\n'
     '                  f"{t(\'Hours worked\')}: {horas}.")'),
]

for rel, viejo, nuevo in CAMBIOS:
    f = R / rel
    src = f.read_text(encoding="utf-8")
    if viejo not in src:
        print(f"  ⚠️ ANCLA NO CASA en {rel}: {viejo.splitlines()[0][:58]!r}")
        continue
    n = src.count(viejo)
    if n != 1:
        print(f"  ⚠️ AMBIGUA ({n}) en {rel}: {viejo.splitlines()[0][:50]!r}")
        continue
    f.write_text(src.replace(viejo, nuevo, 1), encoding="utf-8")
    print(f"  OK  {rel}: {viejo.splitlines()[0][:56]}")
