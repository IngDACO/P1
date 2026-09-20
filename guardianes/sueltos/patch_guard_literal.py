# -*- coding: utf-8 -*-
"""Chequeo permanente: ninguna pieza HTML del kit puede recibir `:material/…:`.

Lo destapo MIRAR LA PANTALLA en produccion, no leer el codigo ni ningun guardian: la
cabecera de la galeria pintaba `:material_photo_library: Photos`. `theme.section`,
`chip`, `kpi_row` y `_kpi_card` emiten HTML crudo, y ahi Streamlit no interpreta la
sintaxis de icono (v443). Va general —todo el repo, no solo la biblioteca— porque el
fallo no tiene nada de particular de este modulo, y **la sonda se valida contra un
caso construido** antes de creerse su cero (trampa nº12).
"""
import ast
import io

P = "verif_v472.py"
s = io.open(P, encoding="utf-8").read()

BLOQUE = '''

# ── 13 ───────────────────────────────────────────────────────────────────────
print("\\n13. Ninguna pieza HTML del kit recibe sintaxis de icono")
# ⚠️ `theme.section/chip/kpi_row/_kpi_card` pintan HTML con `unsafe_allow_html`, y ahi
# `:material/…:` NO se interpreta: sale el literal en pantalla (v443). Se vio en
# produccion, mirando — ningun guardian lo veia.
_HTML_KIT = {"section", "chip", "kpi_row", "_kpi_card"}


def iconos_en_html(src):
    try:
        arbol = ast.parse(src)
    except SyntaxError:
        return []
    fuera = []
    for n in ast.walk(arbol):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
            continue
        if n.func.attr not in _HTML_KIT:
            continue
        for sub in ast.walk(n):
            if (isinstance(sub, ast.Constant) and isinstance(sub.value, str)
                    and ":material/" in sub.value):
                fuera.append((n.func.attr, sub.value[:40]))
    return fuera


# la sonda, validada en las dos direcciones antes de creerse su cero
_MALO = 'T.section(t(":material/photo_library: Photos"))'
_BUENO = 'T.section(t("Photos"))\\nst.button(":material/save: Save")'
(ok if iconos_en_html(_MALO) and not iconos_en_html(_BUENO) else fallo)(
    "la sonda ve el icono en una pieza HTML y no marca el de un boton")

_kit = []
for _f in sorted(os.listdir("core")):
    if _f.endswith(".py"):
        _kit += [("%s: %s(%r)" % (_f, a, v))
                 for a, v in iconos_en_html(io.open(os.path.join("core", _f),
                                                    encoding="utf-8").read())]
(ok if not _kit else fallo)("0 piezas HTML del kit con sintaxis de icono", _kit)
'''

ANCLA = '\n\nprint("")\nif fallos:'
if s.count(ANCLA) != 1:
    raise SystemExit("ancla final no unica: %d" % s.count(ANCLA))
s = s.replace(ANCLA, BLOQUE + ANCLA)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v472.py: bloque 13 (iconos en piezas HTML del kit)")
