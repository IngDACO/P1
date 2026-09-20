# -*- coding: utf-8 -*-
"""F5a — los mensajes de BACKEND que la interfaz pinta: `auth.py` y `timeclock.py`.

Son los dos módulos cuyos mensajes se ven más veces al día (cada login y cada
fichaje). ⚠️ NO se tocan:
  · los **nombres de columna** que viajan en el mismo `return` (`"Usuario"`,
    `"Nombre"`, `"Estado"`…): son el DATO del libro;
  · los mensajes de **logger**, que nadie ve (v439: `logger.warning` y `st.warning`
    comparten nombre de atributo, y filtrar por atributo metió 92 en la primera pasada).

⚠️ Y el orden importa: la local `t` de `auth._session_active` se renombró ANTES
(pre_i18n), no después — que es como se rompieron v437, v439 y v440.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

IMPORTS = [
    # ⚠️ `i18n` solo importa `logging` y `streamlit`: es módulo HOJA, así que
    # importarlo desde el backend no crea ciclo (comprobado, no supuesto).
    ("core/auth.py", "from core import timeclock",
     "from core.i18n import t\nfrom core import timeclock"),
    # ⚠️ En `timeclock` solo entra `t`: `d` ya es variable en 3 funciones y taparía
    # la del motor en todo su ámbito.
    ("core/timeclock.py", "from core import clock",
     "from core.i18n import t\nfrom core import clock"),
]

CAMBIOS = [
    # ── auth.py ──
    ("core/auth.py",
     '"El acceso no está configurado (faltan credenciales en Secrets)."',
     't("Access is not configured (credentials missing from Secrets).")'),
    ("core/auth.py", 'f"No se pudo abrir la hoja Login: {e}"',
     'f"{t(\'Could not open the Login sheet\')}: {e}"'),
    ("core/auth.py", 'f"No se pudo abrir la hoja Grupos: {e}"',
     'f"{t(\'Could not open the Groups sheet\')}: {e}"'),
    ("core/auth.py", '"El nombre del grupo es obligatorio."',
     't("The group name is required.")'),
    ("core/auth.py", '"Margen por defecto actualizado."',
     't("Default margin updated.")'),
    ("core/auth.py", '"Impuesto por defecto actualizado."',
     't("Default tax updated.")'),
    ("core/auth.py", '"Grupo devuelto al libro maestro."',
     't("Group returned to the master workbook.")'),
    ("core/auth.py", '"Fecha de ingreso actualizada."',
     't("Start date updated.")'),
    ("core/auth.py", '"Contraseña incorrecta."', 't("Wrong password.")'),
    ("core/auth.py", '"Usuario no encontrado."', 't("User not found.")'),
    ("core/auth.py", '"Usuario inactivo."', 't("Inactive user.")'),
    ("core/auth.py", '"Usuario y contraseña son obligatorios."',
     't("Username and password are required.")'),
    ("core/auth.py", '"La contraseña no puede estar vacía."',
     't("The password cannot be empty.")'),
    ("core/auth.py", '"Rol inválido."', 't("Invalid role.")'),
    ("core/auth.py",
     '"Los usuarios administrador y de campo deben pertenecer a un grupo."',
     't("Administrator and field users must belong to a group.")'),
    ("core/auth.py", '"Esta cuenta ya tiene una sesión activa en otro dispositivo."',
     't("This account already has an active session on another device.")'),
    ("core/auth.py",
     '"No se pudo verificar la sesión (la hoja no respondió). '
     'Reintenta en unos segundos."',
     't("Could not verify the session (the sheet did not respond). '
     'Try again in a few seconds.")'),
    ("core/auth.py", 'f"No se pudo iniciar sesión: {e}"',
     'f"{t(\'Could not sign in\')}: {e}"'),
    ("core/auth.py", 'f"Error creando usuario: {e}"',
     'f"{t(\'Error creating user\')}: {e}"'),
    ("core/auth.py", 'f"Ese libro ya es de: {g.get(\'Grupo\')}."',
     'f"{t(\'That workbook already belongs to\')}: {g.get(\'Grupo\')}."'),

    # ── timeclock.py ──
    ("core/timeclock.py",
     '"El fichaje no está conectado: faltan credenciales '
     '(gcp_service_account) o TIMECLOCK_SHEET_ID."',
     't("The timeclock is not connected: credentials (gcp_service_account) '
     'or TIMECLOCK_SHEET_ID are missing.")'),
    ("core/timeclock.py", '"No hay usuario en sesión."',
     't("No user is signed in.")'),
    ("core/timeclock.py", 'f"Conexión temporalmente no disponible con Google Sheets: {e}"',
     'f"{t(\'Connection to Google Sheets temporarily unavailable\')}: {e}"'),
    ("core/timeclock.py", 'f"Error leyendo la hoja: {e}"',
     'f"{t(\'Error reading the sheet\')}: {e}"'),
    ("core/timeclock.py", 'f"Error escribiendo el fichaje: {e}"',
     'f"{t(\'Error writing the timeclock entry\')}: {e}"'),
    ("core/timeclock.py", 'f"Error actualizando el fichaje: {e}"',
     'f"{t(\'Error updating the timeclock entry\')}: {e}"'),
]

for rel, viejo, nuevo in IMPORTS + CAMBIOS:
    f = R / rel
    src = f.read_text(encoding="utf-8")
    if viejo not in src:
        print(f"  ⚠️ ANCLA NO CASA en {rel}: {viejo[:62]!r}")
        continue
    n = src.count(viejo)
    if n != 1:
        print(f"  ⚠️ ANCLA AMBIGUA ({n}) en {rel}: {viejo[:52]!r}")
        continue
    f.write_text(src.replace(viejo, nuevo, 1), encoding="utf-8")
    print(f"  OK  {rel}: {viejo[:58]}")
