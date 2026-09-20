# -*- coding: utf-8 -*-
"""La exencion de v469 deja de estar anclada a NUMEROS DE LINEA.

⚠️ `SALTAR` guardaba (fichero, linea). Los tres son falsos positivos legitimos
—literales INTERNOS cuyo productor y consumidor viven en el mismo modulo—, pero el
ancla es fragil en las dos direcciones: **cualquier edicion mas arriba reabre el
falso positivo** (es lo que acaba de pasar: v472 añadio codigo a `home_ui` y las
lineas 661/761 pasaron a 696/801) y, peor, una comparacion REAL que caiga algun dia
en ese numero quedaria eximida sin que nadie lo note.

Se reancla a (fichero, FUNCION, valor), que es estable ante ediciones de al lado y
ademas dice QUE se esta eximiendo, no en que renglon estaba.
"""
import ast
import io

P = "verif_v469.py"
s = io.open(P, encoding="utf-8").read()

VIEJO = 'SALTAR = {("home_ui.py", 661), ("home_ui.py", 761), ("survey_ui.py", 131)}\n'
NUEVO = ('# ⚠️ Reanclado en v472: iba por (fichero, LINEA) y cualquier edicion mas arriba\n'
         '# lo desalineaba — v472 añadio codigo a `home_ui` y los tres falsos positivos\n'
         '# volvieron. Peor: una comparacion REAL que cayera en ese numero quedaria\n'
         '# eximida en silencio. Ahora va por (fichero, funcion, valor), que sobrevive a\n'
         '# las ediciones de al lado y dice QUE se exime.\n'
         'SALTAR = {("home_ui.py", "_abrir_resultado", "proyecto"),\n'
         '          ("home_ui.py", "_alertas", "mantenimiento"),\n'
         '          ("survey_ui.py", "render_survey_tab", "proyecto")}\n')
if s.count(VIEJO) != 1:
    raise SystemExit("ancla SALTAR no unica: %d" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)

# el bucle tiene que conocer la funcion que CONTIENE cada comparacion
VIEJO2 = ('            for v, ln in cand:\n'
          '                if v in valores.LEGADO and (p.name, ln) not in SALTAR:\n'
          '                    quedan.append("%s:%s %r" % (p.name, ln, v))\n')
NUEVO2 = ('            for v, ln in cand:\n'
          '                if v not in valores.LEGADO:\n'
          '                    continue\n'
          '                if (p.name, _funcion_de(arbol, ln), v) in SALTAR:\n'
          '                    continue\n'
          '                quedan.append("%s:%s %r" % (p.name, ln, v))\n')
if s.count(VIEJO2) != 1:
    raise SystemExit("ancla del bucle no unica: %d" % s.count(VIEJO2))
s = s.replace(VIEJO2, NUEVO2)

# el helper, justo antes del bloque 1
VIEJO3 = 'print("1. Ninguna comparacion queda contra un valor VIEJO")\n'
NUEVO3 = ('def _funcion_de(arbol, ln):\n'
          '    """La funcion mas INTERNA que contiene esa linea (\'\' si es de modulo)."""\n'
          '    mejor, ancho = "", 10 ** 9\n'
          '    for n in ast.walk(arbol):\n'
          '        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):\n'
          '            continue\n'
          '        fin = n.end_lineno or n.lineno\n'
          '        if n.lineno <= ln <= fin and (fin - n.lineno) < ancho:\n'
          '            mejor, ancho = n.name, fin - n.lineno\n'
          '    return mejor\n'
          '\n'
          '\n'
          'print("1. Ninguna comparacion queda contra un valor VIEJO")\n')
if s.count(VIEJO3) != 1:
    raise SystemExit("ancla del print no unica: %d" % s.count(VIEJO3))
s = s.replace(VIEJO3, NUEVO3)

ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v469.py: exencion por (fichero, funcion, valor), no por linea")
