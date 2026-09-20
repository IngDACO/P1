# -*- coding: utf-8 -*-
"""Dos guardianes de nav, actualizados por el cambio de v478."""
import ast
import io

# ── v303: los destinos de `navegar()` dependen del ROL ───────────────────────
P = "verif_v303.py"
s = io.open(P, encoding="utf-8").read()
VIEJO = '''_IDS = {sec: [i for i, _d in v[1]] for sec, v in H._SUBSECCIONES.items()}
_SECS = {k for k, _l in H._SECCIONES}
'''
NUEVO = '''# ⚠️ La union de los TRES roles (v478): `navegar()` se usa tambien desde pantallas del
# CAMPO —el atajo de Fichaje a «avisar de una baja»— y su destino no existe en la nav
# del admin, que era contra la unica que se validaba.
# ⚠️ Esto ENSANCHA el universo a proposito: un destino valido solo para el campo pasaria
# aunque se llamara desde una pantalla de admin. Se asume, porque lo que este chequeo
# existe para cazar es el destino que no existe para NADIE —una errata o un ID
# renombrado, que navega a ninguna parte SIN dar error (el fallo real de v303)— y de
# que rol se ejecuta cada call-site no es decidible estaticamente.
_IDS = {}
for _tabla in (H._SUBSECCIONES, H._SUBSECCIONES_CAMPO, H._SUBSECCIONES_OWNER):
    for _sec, _v in _tabla.items():
        _IDS.setdefault(_sec, [])
        _IDS[_sec] += [i for i, _d in _v[1] if i not in _IDS[_sec]]
_SECS = {k for _t in (H._SECCIONES, H._SECCIONES_CAMPO, H._SECCIONES_OWNER)
         for k, _l in _t}
'''
if s.count(VIEJO) != 1:
    raise SystemExit("v303: ancla %d" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v303.py: destinos validados contra la nav de los TRES roles")

# ── v298: la misma contencion que v297 ───────────────────────────────────────
P = "verif_v298.py"
s = io.open(P, encoding="utf-8").read()
VIEJO2 = '''check("campo: no pierde ninguna de sus secciones (v297)",
      [s for s in ["misproyectos", "fichaje", "prestart", "herramientas",
                   "credenciales", "colillas"] if s not in _C430], [])
'''
NUEVO2 = '''# ⚠️ ACTUALIZADO en v478 (regla v385): `credenciales` y `colillas` pasaron a ser
# sub-pestañas de «Self-service» a peticion del usuario. La regla NO se relaja —al
# campo no se le puede perder nada—, solo se mide como ALCANZABLE, sea seccion o
# sub-seccion. Misma correccion que en `verif_v297`.
_ALC_C = set(_C430) | {i for _k, (_c, _its) in H._SUBSECCIONES_CAMPO.items()
                       for i, _d in _its}
_ALIAS_C = {"credenciales": "\\U0001F3AB Credenciales",
            "colillas": "\\U0001F4B0 Colillas"}
check("campo: sigue LLEGANDO a todas sus pantallas (v297/v478)",
      [x for x in ["misproyectos", "fichaje", "prestart", "herramientas",
                   "credenciales", "colillas"]
       if x not in _ALC_C and _ALIAS_C.get(x) not in _ALC_C], [])
'''
if s.count(VIEJO2) != 1:
    raise SystemExit("v298: ancla %d" % s.count(VIEJO2))
s = s.replace(VIEJO2, NUEVO2)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v298.py: alcanzable como seccion o sub-seccion")
