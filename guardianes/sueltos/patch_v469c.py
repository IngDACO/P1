# -*- coding: utf-8 -*-
"""El cuerpo del helper se quedo con el nombre viejo del parametro.

⚠️ Mi `replace` alcanzo tambien la DEFINICION (`def _funcion_de(arbol, ln)`), asi que
el parametro paso a `_arb` y el cuerpo siguio diciendo `arbol` → NameError. Es
renombrar en UN paso lo que son DOS —la definicion y todos sus usos—, que es la
leccion de v446/v447, cometida dentro de un parche.
"""
import ast
import io

P = "verif_v469.py"
s = io.open(P, encoding="utf-8").read()

VIEJO = ('def _funcion_de(_arb, ln):\n'
         '    """La funcion mas INTERNA que contiene esa linea (\'\' si es de modulo)."""\n'
         '    mejor, ancho = "", 10 ** 9\n'
         '    for n in ast.walk(arbol):\n')
NUEVO = ('def _funcion_de(_arb, ln):\n'
         '    """La funcion mas INTERNA que contiene esa linea (\'\' si es de modulo)."""\n'
         '    mejor, ancho = "", 10 ** 9\n'
         '    for n in ast.walk(_arb):\n')

if s.count(VIEJO) != 1:
    raise SystemExit("ancla del helper no unica: %d" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)

if "arbol" in s.replace("_arb", ""):
    resto = [ln for ln in s.split("\n") if "arbol" in ln and "_arb" not in ln]
    if resto:
        raise SystemExit("quedan usos de `arbol`: %r" % resto[:3])

ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v469.py: definicion y usos, los dos con `_arb`")
