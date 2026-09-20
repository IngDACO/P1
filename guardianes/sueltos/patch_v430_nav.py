# -*- coding: utf-8 -*-
"""v430 exigia que «ausencias» fuera SECCION del campo; v478 la bajo un nivel.

⚠️ CADUCADO y ACTUALIZADO (regla v385): v430 la puso suelta a proposito —«pedir un dia
o avisar de una baja no es un proyecto ni una herramienta, y enterrarla un nivel le
costaria un toque a quien la usa desde el movil»— y v478 la agrupa con las otras dos
«mias» a peticion del usuario.

La regla NO se relaja: lo que protegia es que **el campo llegue a sus ausencias**, y
eso se sigue afirmando —ahora como sub-pestaña—. Y el toque que perdio en el menu se
comprueba tambien: v478 le puso un atajo desde Fichaje, que es la pantalla que esa
persona abre la mañana que se levanta enferma, asi que la razon original de v430 sigue
cubierta por otra via **y el guardian lo exige**.
"""
import ast
import io

P = "verif_v430.py"
s = io.open(P, encoding="utf-8").read()

VIEJO = '''chk("el campo tiene la sección «ausencias»",
    "ausencias" in [k for k, _ in H._SECCIONES_CAMPO])
'''

NUEVO = '''# ⚠️ CADUCADO en v478 y ACTUALIZADO: «ausencias» dejo de ser seccion suelta y es
# sub-pestaña de «Self-service» (peticion del usuario: la nav del campo de 8 a 6).
# Lo que v430 protegia —que el campo LLEGUE a sus ausencias— se sigue afirmando.
_ids_auto = [i for i, _d in H._SUBSECCIONES_CAMPO.get("autogestion", ("", []))[1]]
chk("el campo llega a sus ausencias (seccion o sub-pestaña)",
    "ausencias" in [k for k, _ in H._SECCIONES_CAMPO] or "\\U0001F334 Ausencias" in _ids_auto)
# ⚠️ Y la razon por la que v430 la dejo SUELTA —avisar de una baja es urgente y se
# hace desde el movil— sigue cubierta: v478 le dio un atajo desde Fichaje. Sin esto,
# agrupar habria costado un toque justo la mañana que alguien se levanta enfermo.
_tc = io.open("core/timeclock_ui.py", encoding="utf-8").read()
chk("...y avisar de una baja tiene atajo desde Fichaje (v478)",
    'navegar("autogestion"' in _tc)
'''

if s.count(VIEJO) != 1:
    raise SystemExit("ancla no unica: %d" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)

# el guardian usa `io`? si no, se importa
if "\nimport io" not in s and "\nimport io\n" not in s:
    s = s.replace("import ast", "import ast\nimport io", 1)

ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v430.py: alcanzable + el atajo que cubre su razon original")
