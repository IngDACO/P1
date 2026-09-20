# -*- coding: utf-8 -*-
"""Dos arreglos de la misma tanda, y ninguno es «relajar el guardian».

1. `library_ui` importaba `etiqueta` PELADO; los otros cuatro modulos de interfaz
   que la usan hacen `etiqueta as _etq`. Se alinea con la convencion (v461).
2. Y la sonda de v463 se ENSANCHA igual, porque solo reconocia `i18n.etiqueta(...)`
   o `_etq(...)`: con el nombre pelado marcaba **codigo correcto**. Un falso
   positivo no es inofensivo — es lo que hace que un guardian acabe ignorandose
   (v450), y ademas empuja a «arreglar» lo que ya estaba bien (v385).
"""
import ast
import io

UI = "C:\\Users\\diego\\P1\\survey_app\\core\\library_ui.py"
s = io.open(UI, encoding="utf-8").read()
for viejo, nuevo in (
        ("from core.i18n import t, etiqueta\n", "from core.i18n import t, etiqueta as _etq\n"),
        ('"Type": etiqueta(str(it.get("Type", ""))),', '"Type": _etq(str(it.get("Type", ""))),'),
        ('T.chip(etiqueta(str(it.get("Type", "")))),', 'T.chip(_etq(str(it.get("Type", "")))),')):
    if s.count(viejo) != 1:
        raise SystemExit("ancla UI no unica (%d): %r" % (s.count(viejo), viejo[:40]))
    s = s.replace(viejo, nuevo)
ast.parse(s)
io.open(UI, "w", encoding="utf-8", newline="").write(s)
print("core/library_ui.py -> usa `_etq`, como los otros cuatro modulos")

G = "verif_v463.py"
g = io.open(G, encoding="utf-8").read()
VIEJO = ('                if "attr=\'etiqueta\'" in dump or "id=\'_etq\'" in dump:\n'
         '                    continue          # ya se traduce\n')
NUEVO = ('                # ⚠️ Las TRES formas en que el repo llama a la traduccion. Con\n'
         '                # solo las dos primeras, un `etiqueta(...)` importado pelado\n'
         '                # salia marcado siendo CORRECTO — la sonda midiendo por la\n'
         '                # forma en que se escribio la primera vez (v450/v459).\n'
         '                if ("attr=\'etiqueta\'" in dump or "id=\'_etq\'" in dump\n'
         '                        or "id=\'etiqueta\'" in dump):\n'
         '                    continue          # ya se traduce\n')
if g.count(VIEJO) != 1:
    raise SystemExit("ancla guardian no unica: %d" % g.count(VIEJO))
g = g.replace(VIEJO, NUEVO)
ast.parse(g)
io.open(G, "w", encoding="utf-8", newline="").write(g)
print("verif_v463.py -> la sonda reconoce las 3 formas")
