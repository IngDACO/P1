# -*- coding: utf-8 -*-
"""Dos chequeos de verif_v482 que la batería de roturas demostró flojos.

1. «el contador no lanza» se probaba con argumentos basura que **nunca llegan a
   fallar**, así que el chequeo pasaba igual con el `except` convertido en `raise`:
   no distinguía nada. Ahora se le pasa un objeto cuyo `str()` revienta, que es la
   única forma de ejercitar de verdad esa guarda.
2. Faltaba comprobar que no haya IDs de sub-sección DUPLICADOS: dos entradas iguales
   pintan dos botones que llevan al mismo sitio y el despachador no puede
   distinguirlos.
"""
import io

P = "verif_v482.py"
s = io.open(P, encoding="utf-8").read()

V = """try:
    metrics.anota(None, None)
    metrics.anota(123, object())
    ok("con argumentos basura no lanza")
except Exception as _e:
    fallo("el contador propago una excepcion", str(_e))"""

N = '''class _Explota:
    """Su `str()` revienta. Es la unica forma de comprobar de verdad que `anota` se
    traga lo suyo: con argumentos «basura» normales no llega a fallar nunca, asi que
    ese chequeo no distinguia nada — lo destapo la bateria de roturas, no leerlo."""

    def __str__(self):
        raise RuntimeError("boom")


try:
    metrics.anota(None, None)
    metrics.anota("GET", _Explota())
    ok("ni con un argumento que revienta al convertirlo a texto")
except Exception as _e:
    fallo("el contador propago una excepcion", str(_e))'''

V2 = """    "la sub-seccion nueva va la ULTIMA (v297)", _ids)"""
N2 = '''    "la sub-seccion nueva va la ULTIMA (v297)", _ids)
# ⚠️ Y ninguna repetida: dos entradas con el mismo ID pintan dos botones que llevan al
# mismo sitio, y el despachador no puede distinguirlos.
(ok if len(_ids) == len(set(_ids)) else fallo)(
    "sin IDs duplicados", [i for i in _ids if _ids.count(i) > 1])'''

for etq, a in (("anota", V), ("ultima", V2)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))
s = s.replace(V, N).replace(V2, N2)
compile(s, P, "exec")
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v482: sonda de excepcion con un caso que SI revienta + IDs sin duplicar")
