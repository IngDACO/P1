# -*- coding: utf-8 -*-
"""Añade a verif_v478 el bloque 7: la barra superior en el movil.

⚠️ La sonda comprueba el ANCLA y el SUELO, no que «haya CSS»: un selector que no
casa no da ningun error (v304/v332), asi que afirmar «hay una @media» no probaria
nada. Lo que se afirma es lo que se MIDIO en la app real.
"""
import ast
import io

P = "verif_v478.py"
s = io.open(P, encoding="utf-8").read()

BLOQUE = '''
# ── 7 ────────────────────────────────────────────────────────────────────────
print("")
print("7. La barra superior cabe en UNA fila en el movil (medido: 112 -> 44 px)")
# ⚠️ MEDIDO en la app real con sesion de campo a 375x812, no leido: las 4 columnas
# se apilaban en TRES bandas y el titulo empezaba en y=196 — el 24% del telefono
# gastado en chrome antes de ver nada.
(ok if 'key="cpxtop"' in SRC_H else fallo)("la barra va en un contenedor con KEY")
# ⚠️ Anclado a la key y NO a `:first-of-type`, que depende del ORDEN del documento
# y se rompe en silencio si otra pantalla pinta una fila antes (v304/v332).
(ok if ".st-key-cpxtop" in SRC_H else fallo)("el CSS ancla a esa key")
(ok if ":first-of-type" not in SRC_H else fallo)("y NO al orden del documento")
(ok if "@media (max-width:640px)" in SRC_H else fallo)("acotado a pantallas estrechas")
# ⚠️ El suelo de 44 px NO es decoracion: sin el los botones quedaban en 26 px de
# ancho —bajo el minimo de 36 de v326/v327— y el movil es donde peor se pulsa.
(ok if "min-width:44px" in SRC_H else fallo)("con suelo de 44 px por boton (v326/v327)")
'''

A = '\nprint("")\nif fallos:'
if s.count(A) != 1:
    raise SystemExit("ancla no unica: %d" % s.count(A))
s = s.replace(A, BLOQUE + A)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v478.py: bloque 7 (la barra en el movil)")
