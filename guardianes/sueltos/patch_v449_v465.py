# -*- coding: utf-8 -*-
"""Dos rojos de la suite, cada uno por su motivo. Ninguno es «relajar el guardian».

· v449 daba un FALSO POSITIVO: `'Ripout + Instalación'` es una **CLAVE de
  `i18n.VALORES`**, o sea el español HEREDADO que el mapa traduce al mostrar — dato,
  no mensaje. Lo marcaba porque su heuristica cuenta 3+ palabras y ahi el `+` cuenta
  como una; `'En progreso'` y las demas claves son de dos y por eso nunca lo habian
  disparado. La exclusion se DERIVA del propio mapa, no se escribe a mano.

· v465 SI decia algo con sentido —una hoja renombrada necesita entrada en `LEGADO` o,
  si el libro aun tiene el nombre viejo, `get_sheet` **crea una hoja VACIA** y se pone
  a escribir ahi—, pero `Library` y `LibraryModels` **nacieron en ingles**: nunca
  tuvieron nombre español, asi que no hay nada con lo que ser compatible. Entran en
  `_YA`, que es la exencion que ya existia justo para eso.
"""
import ast
import io

# ── v449 ─────────────────────────────────────────────────────────────────────
P = "verif_v449.py"
s = io.open(P, encoding="utf-8").read()
VIEJO = ('_bk = {}\n'
         'for f in INT:\n'
         '    if f.name in EXCL_MOD:\n'
         '        continue\n'
         '    c = M.clasifica(f)\n'
         '    r = sorted({s for _, s in c["RETORNO"] + c["OTRO"] if _es_msg(s)})\n')
NUEVO = ('_bk = {}\n'
         '# ⚠️ Las CLAVES de `i18n.VALORES` son el español HEREDADO: el dato viejo que el\n'
         '# mapa traduce al MOSTRAR (v442/v469). No son mensajes y no se traducen — son\n'
         '# la mitad izquierda del diccionario. Se derivan del mapa en vez de listarse,\n'
         '# porque una lista a mano en paralelo a la verdad es lo que se queda vieja.\n'
         'from core import i18n as _i18n_legado                                # noqa: E402\n'
         '_LEGADO_ES = set(_i18n_legado.VALORES)\n'
         'for f in INT:\n'
         '    if f.name in EXCL_MOD:\n'
         '        continue\n'
         '    c = M.clasifica(f)\n'
         '    r = sorted({s for _, s in c["RETORNO"] + c["OTRO"]\n'
         '                if _es_msg(s) and s not in _LEGADO_ES})\n')
if s.count(VIEJO) != 1:
    raise SystemExit("v449: ancla no unica (%d)" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v449.py: las claves del vocabulario heredado no son mensajes")

# ── v465 ─────────────────────────────────────────────────────────────────────
P = "verif_v465.py"
s = io.open(P, encoding="utf-8").read()
VIEJO = ('# ⚠️ Login/PreStarts/Roster/Sheet1 ya estaban en ingles y no entran en LEGADO.\n'
         '_YA = {"login", "prestarts", "roster", "sheet1"}\n')
NUEVO = ('# ⚠️ Login/PreStarts/Roster/Sheet1 ya estaban en ingles y no entran en LEGADO.\n'
         '# ⚠️ v472 · `Library`/`LibraryModels` tampoco, y por una razon DISTINTA que\n'
         '# conviene no confundir: aquellas ya existian en ingles; estas **nacieron\n'
         '# despues del renombrado**, asi que no han tenido nunca un nombre español y no\n'
         '# hay nada con lo que ser compatible. Que `get_sheet` las cree la primera vez\n'
         '# es lo CORRECTO aqui, no el fallo que este bloque vigila.\n'
         '_YA = {"login", "prestarts", "roster", "sheet1", "library", "librarymodels"}\n')
if s.count(VIEJO) != 1:
    raise SystemExit("v465: ancla no unica (%d)" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v465.py: las dos hojas nuevas, exentas con su razon")
