# -*- coding: utf-8 -*-
"""Liga el arbol a una variable: `_funcion_de` lo necesita y se parseaba en linea.

⚠️ El NameError lo delato EJECUTAR el guardian, no leerlo — y este es el modo de
fallo que mas engaña: **un guardian que revienta devuelve codigo != 0 SIEMPRE**, asi
que parece un rojo del codigo auditado cuando el roto es el guardian (v459/v463).
"""
import ast
import io

P = "verif_v469.py"
s = io.open(P, encoding="utf-8").read()

VIEJO = '    for n in ast.walk(ast.parse("\\n".join(src))):\n'
NUEVO = '    _arb = ast.parse("\\n".join(src))\n    for n in ast.walk(_arb):\n'

if s.count(VIEJO) != 1:
    raise SystemExit("ancla del parse no unica: %d" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO).replace("_funcion_de(arbol, ln)", "_funcion_de(_arb, ln)")

if "_funcion_de(_arb, ln)" not in s:
    raise SystemExit("la llamada no quedo reescrita")

ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v469.py: arbol ligado a `_arb`")
