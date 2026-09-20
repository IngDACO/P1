# -*- coding: utf-8 -*-
"""El TIPO es un dato de la hoja: va por `etiqueta()`, no por `t()`.

Lo cazo el guardian general de v463 en cuanto se le puso la invariante fuerte, y es
la mitad 1 del fallo de v462: la celda pintaba el valor CRUDO. `t()` traduce
literales de INTERFAZ contra el catalogo; un valor que viene de la hoja se traduce
con `i18n.etiqueta()`, que es justo el mecanismo para valores de negocio (v442).
Con `t()`, una fila heredada que diga `foto` se pintaria `foto` en una tabla cuyo
encabezado ya esta en ingles — traduccion a medias dentro de la misma tabla (v450).

⚠️ `Section` se queda con `t()` a proposito: ese vocabulario nacio en INGLES y no
esta en `i18n.VALORES`, asi que `etiqueta()` lo devolveria tal cual; con `t()` al
menos puede traducirse el dia que se llene el catalogo español.
"""
import ast
import io

P = "C:\\Users\\diego\\P1\\survey_app\\core\\library_ui.py"
s = io.open(P, encoding="utf-8").read()

CAMBIOS = [
    # la celda de la tabla
    ('        "Type": t(str(it.get("Type", ""))),\n',
     '        "Type": etiqueta(str(it.get("Type", ""))),\n'),
    # el chip de la ficha
    ('        T.chip(t(str(it.get("Type", "")))),\n',
     '        T.chip(etiqueta(str(it.get("Type", "")))),\n'),
    # el import
    ('from core.i18n import t\n',
     'from core.i18n import t, etiqueta\n'),
]

for viejo, nuevo in CAMBIOS:
    if s.count(viejo) != 1:
        raise SystemExit("ancla no unica (%d): %r" % (s.count(viejo), viejo[:40]))
    s = s.replace(viejo, nuevo)

ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("core/library_ui.py: el Type va por etiqueta() en la tabla y en la ficha")
