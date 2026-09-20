# -*- coding: utf-8 -*-
"""Cierra en la regla GENERAL la ceguera que dejo escapar una rotura en v472.

`verif_v463` exigia `etiqueta(x) == x` y `canon(x) == x`. Las dos son ciertas para
cualquier cadena que el vocabulario NO conozca, asi que un valor en español que
nadie mapeo (`foto`, `bodega`, lo que sea) pasaba por delante — la mitad 2 del
fallo que el propio guardian describe en su docstring, sin chequeo que la cubriera.
Es `etiqueta()` devolviendo tal cual lo que no conoce (v462), del otro lado.

Medido antes de tocar: con las 3 entradas nuevas del vocabulario, los 78 valores de
negocio del repo pasan la invariante fuerte; los unicos fuera son los 6 ya exentos
con razon mas `manual` y `datasheet`, que se declaran aqui.
"""
import ast
import io

P = "verif_v463.py"
s = io.open(P, encoding="utf-8").read()

# ── 1. los dos exentos nuevos, con su razon (no una lista comoda) ─────────────
VIEJO1 = ('               ("payroll", "TIPOS", "devengo"), ("payroll", "TIPOS", "deduccion"),\n'
          '               ("payroll", "TIPOS", "aporte")}\n')

NUEVO1 = ('               ("payroll", "TIPOS", "devengo"), ("payroll", "TIPOS", "deduccion"),\n'
          '               ("payroll", "TIPOS", "aporte"),\n'
          '               # ⚠️ v472 · `manual` se escribe IGUAL en los dos idiomas, asi que\n'
          '               # mapearlo seria un «mapa espejo» (v450); y a `datasheet`, termino\n'
          '               # tecnico que en español se usa tal cual, habria que inventarle una\n'
          '               # clave que nadie escribe. Misma clase que los simbolos de arriba.\n'
          '               ("library", "TIPOS", "manual"),\n'
          '               ("library", "TIPOS", "datasheet")}\n')

# ── 2. la invariante que SI distingue un canonico de un español desconocido ───
VIEJO2 = ('            if i18n.etiqueta(_x) != _x:\n'
          '                _falta.append("%s.%s: %r → `etiqueta()` lo cambia a %r (sin migrar?)"\n'
          '                              % (_nom, _c, _x, i18n.etiqueta(_x)))\n'
          '            elif VALORES_MOD.canon(_x) != _x:\n'
          '                _falta.append("%s.%s: %r → `canon()` lo cambia a %r (no es canónico)"\n'
          '                              % (_nom, _c, _x, VALORES_MOD.canon(_x)))\n')

NUEVO2 = ('            if i18n.etiqueta(_x) != _x:\n'
          '                _falta.append("%s.%s: %r → `etiqueta()` lo cambia a %r (sin migrar?)"\n'
          '                              % (_nom, _c, _x, i18n.etiqueta(_x)))\n'
          '            elif VALORES_MOD.canon(_x) != _x:\n'
          '                _falta.append("%s.%s: %r → `canon()` lo cambia a %r (no es canónico)"\n'
          '                              % (_nom, _c, _x, VALORES_MOD.canon(_x)))\n'
          '            # ⚠️ AÑADIDA EN v472, y es la que faltaba. Las dos de arriba son\n'
          '            # CIERTAS para cualquier cadena que el vocabulario no conozca, asi\n'
          '            # que un valor en español SIN mapear pasaba por delante: `etiqueta()`\n'
          '            # devuelve tal cual lo que no conoce (v462). Se escapo una rotura\n'
          '            # real de v472 («un tipo vuelve al español») por este hueco.\n'
          '            # Que el valor sea un canonico CONOCIDO es lo unico que separa\n'
          '            # «esta migrado» de «nadie lo ha mirado nunca».\n'
          '            elif _x not in _CANON:\n'
          '                _falta.append("%s.%s: %r → no es un canonico conocido: o se mapea"\n'
          '                              " en i18n.VALORES, o se exime con razon"\n'
          '                              % (_nom, _c, _x))\n')

VIEJO3 = 'from core import valores as VALORES_MOD, inventory, catalogo\n'
NUEVO3 = ('from core import valores as VALORES_MOD, inventory, catalogo\n'
          '_CANON = set(i18n.VALORES.values())   # el vocabulario canonico COMPLETO\n')

for viejo, nuevo, etq in ((VIEJO1, NUEVO1, "exentos"),
                          (VIEJO3, NUEVO3, "_CANON"),
                          (VIEJO2, NUEVO2, "invariante")):
    if s.count(viejo) != 1:
        raise SystemExit("ancla %s: %d coincidencias" % (etq, s.count(viejo)))
    s = s.replace(viejo, nuevo)

ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v463.py: invariante fuerte + 2 exentos con razon")
