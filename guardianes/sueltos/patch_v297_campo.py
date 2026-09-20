# -*- coding: utf-8 -*-
"""v297 pasa de «siguen siendo SECCIONES» a «el campo sigue LLEGANDO a todo».

⚠️ CADUCADO en v478 y ACTUALIZADO (regla v385, trampa nº16): exigia que credenciales y
colillas fueran SECCIONES de primer nivel, y v478 las bajo —con ausencias— a
sub-pestañas de «Self-service», a peticion del usuario. Fallaba por un cambio
deliberado, no por una perdida.

Lo que la regla protege es lo mismo de siempre y **no se relaja**: al campo no se le
puede PERDER nada de lo que tenia. Solo cambia como se mide — alcanzable como seccion
**o** como sub-seccion, que es lo que de verdad importa para quien la usa.
"""
import ast
import io

P = "verif_v297.py"
s = io.open(P, encoding="utf-8").read()

VIEJO = '''_VIEJAS = ["misproyectos", "fichaje", "prestart", "herramientas",
           "credenciales", "colillas"]
check("no se pierde ninguna de las 6 secciones que el campo ya tenia",
      [s for s in _VIEJAS if s not in _secs], [])
check("...y las que se anadan van DESPUES (no reordenan su nav)",
      _secs[:len(_VIEJAS)], _VIEJAS)
'''

NUEVO = '''_VIEJAS = ["misproyectos", "fichaje", "prestart", "herramientas",
           "credenciales", "colillas"]
# ⚠️ CADUCADO en v478 y ACTUALIZADO: `credenciales` y `colillas` ya no son secciones
# de primer nivel — v478 las bajo, con `ausencias`, a sub-pestañas de «Self-service»
# (peticion del usuario: la nav del campo de 8 a 6, que en un movil se nota). La regla
# NO se relaja: sigue siendo «no se le pierde nada», solo que ahora alcanzable como
# seccion **o** como sub-seccion, que es lo que le importa a quien la usa.
_ALCANZABLE = set(_secs) | {i for _k, (_c, _its) in H._subsecciones().items()
                            for i, _d in _its}
_ALIAS = {"credenciales": "🎫 Credenciales", "colillas": "💰 Colillas",
          "ausencias": "🌴 Ausencias"}
check("el campo sigue LLEGANDO a todo lo que tenia (seccion o sub-seccion)",
      [x for x in _VIEJAS
       if x not in _ALCANZABLE and _ALIAS.get(x) not in _ALCANZABLE], [])
# ⚠️ Y lo que sigue siendo seccion conserva su ORDEN: mover algo a un submenu es una
# decision; REORDENARLE la nav a quien ya la usaba, no.
_SIGUEN = [x for x in _VIEJAS if x in _secs]
check("...y lo que sigue siendo seccion no se reordena",
      _secs[:len(_SIGUEN)], _SIGUEN)
check("las tres «mias» estan juntas bajo un solo nivel (v478)",
      sorted(i for i, _d in H._subsecciones().get("autogestion", ("", []))[1]),
      sorted(_ALIAS.values()))
'''

VIEJO2 = '''check("nada perdido: las 5 tecnicas + los 6 apartados operativos",
      [x for x in _VIEJAS + _herr if x not in _cubre], [])
'''
NUEVO2 = '''check("nada perdido: las 5 tecnicas + los 6 apartados operativos",
      [x for x in _VIEJAS + _herr
       if x not in _cubre and _ALIAS.get(x) not in _ALCANZABLE], [])
'''

for viejo, nuevo, etq in ((VIEJO, NUEVO, "contencion"), (VIEJO2, NUEVO2, "cobertura")):
    if s.count(viejo) != 1:
        raise SystemExit("ancla %s: %d" % (etq, s.count(viejo)))
    s = s.replace(viejo, nuevo)

ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v297.py: alcanzable como seccion o sub-seccion; el orden de las que quedan, intacto")
