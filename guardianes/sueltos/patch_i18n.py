# -*- coding: utf-8 -*-
"""Mete en el vocabulario los valores de negocio que nadie mapeo.

Medido antes de tocar: de 78 valores de negocio del repo, 11 quedaban fuera del
vocabulario canonico y 6 ya estaban EXENTOS con razon (los simbolos `m`/`m²`/`kg`
de v463 y los 3 de `payroll`, que siguen en español a proposito). Los otros 5 son
huecos reales: 4 de la biblioteca (v472) y **uno de v470**, que añadio un tipo de
proyecto y no lo mapeo — el fallo de v462 («un valor nuevo no entra solo en el
mapa, y no da ningun error») repetido dos versiones despues.

⚠️ `manual` y `datasheet` NO se añaden: mapear `manual`→`manual` seria un «mapa
espejo» (v450 los mando borrar) y a `datasheet` habria que inventarle una clave
española que nadie escribe. Van EXENTOS y con la razon escrita, como los simbolos.
"""
import ast
import io

P = "C:\\Users\\diego\\P1\\survey_app\\core\\i18n.py"
s = io.open(P, encoding="utf-8").read()

VIEJO = ('    "Instalación": "Installation", "Delivery": "Delivery", "Ripout": "Ripout",\n'
         '    "Otro": "Other", "Oficina": "Office", "Almacén": "Warehouse",'
         ' "Taller": "Workshop",\n')

NUEVO = ('    "Instalación": "Installation", "Delivery": "Delivery", "Ripout": "Ripout",\n'
         '    "Otro": "Other", "Oficina": "Office", "Almacén": "Warehouse",'
         ' "Taller": "Workshop",\n'
         '    # ⚠️ v472 · lo añadio v470 y se quedo FUERA del mapa: el tipo existia y\n'
         '    # `etiqueta()` lo devolvia tal cual, asi que ni salia mal hoy ni saltaba\n'
         '    # nada — el hueco silencioso de v462. Mismo molde que sus cuatro hermanos.\n'
         '    "Ripout + Instalación": "Ripout + Installation",\n'
         '    # tipo de material de la biblioteca tecnica (v472). `manual` y `datasheet`\n'
         '    # no estan a proposito: el primero se escribe igual en los dos idiomas\n'
         '    # (seria un mapa espejo) y al segundo habria que inventarle una clave.\n'
         '    "foto": "photo", "diagrama": "diagram",\n')

if s.count(VIEJO) != 1:
    raise SystemExit("ancla no unica: %d" % s.count(VIEJO))

s = s.replace(VIEJO, NUEVO)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("core/i18n.py: +3 entradas (2 de v472, 1 de v470)")
