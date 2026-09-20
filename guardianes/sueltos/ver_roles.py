# -*- coding: utf-8 -*-
"""Los 5 roles, leidos de la hoja YA MIGRADA, y que navegacion le tocaria a cada uno.

⚠️ Es la prueba que importa de la migracion de `Login.Role`: si un rol llegara sin
reconocer, `home_ui._secciones()` cae al default del CAMPO (v297, menor privilegio) y
un administrador se quedaria sin sus pantallas de gestion — sin dar ningun error.
"""
import sys

sys.path.insert(0, ".")
from core import auth, home_ui  # noqa: E402

print("%-12s %-16s %-12s %s" % ("USUARIO", "ROL (hoja)", "RECONOCIDO", "SECCIONES"))
malos = []
for u in auth.list_users():
    usr = u.get("Usuario") or u.get("User") or "?"
    rol = str(u.get("Role", ""))
    conocido = rol in auth.ROLES
    secs = home_ui._SECCIONES_ROL.get(rol)
    if secs is None:
        secs = home_ui._SECCIONES_ROL.get("field", {})
        cae_a_campo = True
    else:
        cae_a_campo = False
    claves = list(secs)[:5] if hasattr(secs, "__iter__") else []
    if not conocido or cae_a_campo:
        malos.append((usr, rol))
    print("%-12s %-16s %-12s %s" % (usr, rol, "si" if conocido else "NO", claves))

print("")
if malos:
    print("FALLO: %d cuenta(s) con rol sin reconocer -> caerian a la nav del CAMPO: %s"
          % (len(malos), malos))
    sys.exit(1)
print("OK: los %d roles se reconocen y cada uno conserva su navegacion"
      % len(auth.list_users()))
