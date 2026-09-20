# -*- coding: utf-8 -*-
"""Corrige el bloque 2 de `verif_v469`, que afirmaba lo CONTRARIO de lo correcto."""
import io
import os

p = os.environ["SCRW"] + "/verif_v469.py"
s = io.open(p, encoding="utf-8").read()

VIEJO = '''# ⚠️ `Sheet1.Type` guarda el tipo de FICHAJE (`general`/`proyecto`) y `proyecto` es
# tambien un valor de UBIC_TIPOS: canonizando por nombre de columna, el fichaje
# pasaria a decir `project` mientras el codigo compara `TIPO_PROYECTO`.
if all(isinstance(x, tuple) and len(x) == 2 for x in valores.COLUMNAS):
    ok("la lista blanca son %d pares (hoja, columna)" % len(valores.COLUMNAS))
else:
    fallo("la lista blanca no esta por pares: podria tocar columnas homonimas")
if ("Sheet1", "Type") not in valores.COLUMNAS:
    ok("Sheet1.Type (el fichaje) queda FUERA")
else:
    fallo("Sheet1.Type esta dentro: el fichaje dejaria de casar")
_r = valores.canonizar([{"Type": "proyecto"}], "Sheet1")
if _r == [{"Type": "proyecto"}]:
    ok("y de hecho no lo toca")
else:
    fallo("el fichaje se canoniza: %r" % _r)'''

NUEVO = '''# ⚠️ ESTE BLOQUE AFIRMABA LO CONTRARIO DE LO CORRECTO, y por poco no cuesta caro.
# Se escribio cuando `TIPO_PROYECTO` todavia era `"proyecto"`: entonces canonizar esa
# columna SI rompia el fichaje (la fila diria `project` y el codigo comparaba
# `proyecto`). Al migrar la constante a `"project"`, la conclusion se invirtio —
# **dejarlo fuera es lo que rompe**: las ~500 filas del historico siguen diciendo
# `proyecto`, se leen sin canonizar y `_tipo_of(r) == TIPO_PROYECTO` es FALSO para
# todas, asi que ni una hora imputada a una obra cuenta como tal (nomina, costo de
# obra, conciliacion de v313 y reparto por proyecto, todo a cero, sin dar un error).
#
# ⚠️ O sea que el guardian estaba PROTEGIENDO el fallo: hacerle caso al rojo sin mirar
# el codigo acusado lo habria reintroducido. Es la regla v385 en su forma mas incomoda
# — el acusado tenia razon y el acusador no.
#
# Lo que SI se conserva, porque no ha cambiado, es el principio: la lista va por
# PAREJA y nunca por nombre de columna suelto, para que `proyecto` en `Sheet1.Type` y
# `proyecto` en `Assets.LocationType` no se pisen.
if all(isinstance(x, tuple) and len(x) == 2 for x in valores.COLUMNAS):
    ok("la lista blanca son %d pares (hoja, columna)" % len(valores.COLUMNAS))
else:
    fallo("la lista blanca no esta por pares: podria tocar columnas homonimas")
if ("Sheet1", "Type") in valores.COLUMNAS:
    ok("Sheet1.Type (el fichaje) esta DENTRO, o el historico no casaria")
else:
    fallo("Sheet1.Type quedo FUERA: ni una hora de obra del historico contaria")
# y se comprueba EJECUTANDO, en las dos direcciones
from core import timeclock as _TC                                  # noqa: E402
_esperado = {"proyecto": "project", "project": "project", "general": "general"}
_mal = [(v, valores.canonizar([{"Type": v}], "Sheet1")[0]["Type"])
        for v, e in _esperado.items()
        if valores.canonizar([{"Type": v}], "Sheet1")[0]["Type"] != e]
if not _mal:
    ok("la fila vieja, la nueva y la jornada acaban donde deben")
else:
    fallo("el fichaje no canoniza bien: %r" % _mal)
if _TC._tipo_of(valores.canonizar([{"Type": "proyecto"}], "Sheet1")[0]) == _TC.TIPO_PROYECTO:
    ok("...y la comparacion REAL del codigo casa con la fila del historico")
else:
    fallo("un segmento de proyecto del historico no cuenta como tal")'''

assert s.count(VIEJO) == 1, "ancla ausente o ambigua (%d)" % s.count(VIEJO)
io.open(p, "w", encoding="utf-8", newline="").write(s.replace(VIEJO, NUEVO))
print("bloque 2 de verif_v469 invertido")
