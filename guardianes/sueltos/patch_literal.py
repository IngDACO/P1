# -*- coding: utf-8 -*-
"""`T.section` emite HTML: ahi `:material/...:` NO se interpreta y sale LITERAL.

Visto en produccion, mirando la pantalla — no leyendo el codigo: la cabecera de la
galeria pintaba `:material_photo_library: Photos`. Es la leccion de v443 (el markdown
no se procesa dentro de `unsafe_allow_html`) y del literal de v375, y **los dos unicos
sitios del repo que le pasan `:material/` a `T.section` eran mios**: la convencion del
kit es texto plano, y la incumpli yo.
"""
import ast
import io

P = "C:\\Users\\diego\\P1\\survey_app\\core\\library_ui.py"
s = io.open(P, encoding="utf-8").read()

CAMBIOS = [
    ('    T.section(t(":material/photo_library: Photos"), t("{n} photo(s)", n=len(fotos)))\n',
     '    # ⚠️ Sin `:material/…:`: `T.section` emite HTML y ahi el icono no se\n'
     '    # interpreta — saldria el literal en pantalla (v443, y se vio en produccion).\n'
     '    T.section(t("Photos"), t("{n} photo(s)", n=len(fotos)))\n'),
    ('    T.section(t(":material/description: Documents"), t("{n} item(s)", n=len(items)))\n',
     '    T.section(t("Documents"), t("{n} item(s)", n=len(items)))\n'),
]

for viejo, nuevo in CAMBIOS:
    if s.count(viejo) != 1:
        raise SystemExit("ancla no unica (%d): %r" % (s.count(viejo), viejo[:50]))
    s = s.replace(viejo, nuevo)

ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("core/library_ui.py: las 2 cabeceras de seccion, sin sintaxis de icono")
