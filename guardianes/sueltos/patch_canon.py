# -*- coding: utf-8 -*-
"""Las dos lecturas FRESCAS de la biblioteca pasan por `columnas.canonizar`.

Es la convencion del repo (alerts, ausencias, auth… todas lo hacen) y es inofensiva
cuando las claves ya son canonicas: `canonizar` renombra las VIEJAS y **no pisa** la
que ya viene bien. Se alinea el codigo con la convencion en vez de eximirlo en el
guardian (criterio de v461), que ademas evita hacer crecer una lista de exenciones.
"""
import ast
import io

P = "C:\\Users\\diego\\P1\\survey_app\\core\\library.py"
s = io.open(P, encoding="utf-8").read()

CAMBIOS = [
    ('        actuales = ws.get_all_records(numericise_ignore=["all"])\n',
     '        actuales = columnas.canonizar(\n'
     '            ws.get_all_records(numericise_ignore=["all"]))\n'),
    ('        for r in ws.get_all_records(numericise_ignore=["all"]):\n',
     '        for r in columnas.canonizar(\n'
     '                ws.get_all_records(numericise_ignore=["all"])):\n'),
    ('from core import hojas, timeclock\n',
     'from core import columnas, hojas, timeclock\n'),
]

for viejo, nuevo in CAMBIOS:
    if s.count(viejo) != 1:
        raise SystemExit("ancla no unica (%d): %r" % (s.count(viejo), viejo[:45]))
    s = s.replace(viejo, nuevo)

ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("core/library.py: las 2 lecturas frescas canonizan (convencion del repo)")
