# -*- coding: utf-8 -*-
"""Toda rotura de toda bateria tiene que seguir apuntando a codigo QUE EXISTE.

⚠️ El fallo que este guardian existe para impedir se vio en v515 y llevaba TRES
versiones ocurriendo: `romper_v470` anunciaba «5 de 13 roturas cazadas» y las otras
ocho decian «ancla ausente». CINCO de esas ocho llevaban muertas desde v512, cuando el
modelo de fases se cambio a proposito y nadie volvio a la bateria.

Una bateria con anclas muertas es PEOR que no tenerla: sigue imprimiendo un recuento
que parece cobertura, y la rotura que ya no se aplica es justo la que nadie va a
comprobar a mano. Es la trampa nº16 (un guardian atado a una FORMA caduca cuando la
forma cambia a proposito) aplicada a las baterias en vez de a las afirmaciones.

⚠️ Y el motivo de que se pudra en SILENCIO es estructural: las `romper_*` NO estan en
`run_suite.py` porque modifican el arbol (v455), asi que nadie las corre salvo cuando se
toca su version. Este chequeo es ESTATICO —no escribe ni un byte— asi que si puede
entrar en la suite (regla v385: si se puede comprobar sin tocar produccion, hazlo estatico).

⚠️ v575 · LECTURA FUERTE (`anclas_lectura.py`). Hasta v574 una rotura era «viva» si
CUALQUIERA de sus cadenas aparecia en el fichero, solo se miraban las listas ROTURAS/CONTROL
y 52 tuplas «ilegibles» se contaban sin evaluarse. Tres huecos, los tres con muertas dentro:
la cadena de REEMPLAZO de romper_v442 si estaba en el codigo (su ancla, no); romper_v430 y
v436 llaman a su lista CASOS (nueve muertas que nunca se revisaron); y romper_v449/v483
escondian una cada una entre las ilegibles. La lectura fuerte identifico 27 muertas en 12
baterias (la deuda declarada era 10): todas re-ancladas a la forma de hoy, con la misma
rotura, y sus baterias re-corridas. Desde aqui: CERO muertas, CERO ilegibles y CERO formas
sin leer — sin lista de deuda. Una bateria nueva en una forma que no se sabe leer pone esto
en rojo: o se escribe en una forma legible, o se enseña la forma a `anclas_lectura.py`.
"""
import io
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AQUI = Path(__file__).parent
APP = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(AQUI))
import anclas_lectura as A                                         # noqa: E402

_fallos = []
_n_ok = 0


def ok(m):
    global _n_ok
    _n_ok += 1
    print("   ok   %s" % m)


def fallo(m):
    _fallos.append(m)
    print("   FALLO %s" % m)


def _resuelve(p):
    """Las baterias nombran el fichero de dos maneras: desde `survey_app` («core/x.py»)
    o desde `core` («x.py»)."""
    for cand in (APP / p, APP / "core" / p):
        if cand.is_file():
            return cand
    return None


print("1. Cada ancla de cada bateria, identificada por su POSICION, existe en su fichero")
_r = A.todas()
# ⚠️ Antes de celebrar el «0 muertas» hay que afirmar que se ha mirado ALGO (trampa nº1)
(ok if _r["baterias"] >= 100 else fallo)("se encontraron las baterias (%d)" % _r["baterias"])
(ok if _r["vivas"] >= 1300 else fallo)("...y se leyeron sus anclas (%d vivas)" % _r["vivas"])
(ok if not _r["muertas"] else fallo)(
    "ninguna bateria tiene un ancla MUERTA (%d)" % len(_r["muertas"]))
for m in _r["muertas"]:
    print("        %s" % m)
(ok if not _r["ilegibles"] else fallo)(
    "...ni una lista que no se pueda evaluar sin ejecutarla (%d)" % len(_r["ilegibles"]))
for m in _r["ilegibles"]:
    print("        %s" % m)
(ok if not _r["sin_forma"] else fallo)(
    "...ni una tupla cuya ancla no se sepa SITUAR (%d) — enseñar la forma a anclas_lectura.py"
    % len(_r["sin_forma"]))
for m in _r["sin_forma"]:
    print("        %s" % m)
# ⚠️ v581 · Un ancla que casa DOS veces en una batería que exige una sola («?? ancla x2»)
# es una rotura que se SALTA: romper_v559 llevaba una desde v577 (la tabla de Hours repetía
# la línea de Costs con más sangría) y aquí contaba como «viva». Las baterías viejas de
# `replace(..., 1)` rompen la PRIMERA a propósito («traducir UNA aparición»): se cuentan,
# no se exigen (las 13 de hoy se revisaron una a una en v581).
(ok if not _r["repetidas_unica"] else fallo)(
    "...ni un ancla REPETIDA en una batería que exige una sola (%d)" % len(_r["repetidas_unica"]))
for m in _r["repetidas_unica"]:
    print("        %s" % m)
print("        (repetidas en baterías de «la primera», a propósito: %d)"
      % len(_r["repetidas_primera"]))

print("")
print("2. La sonda SABE ver un ancla muerta (trampa nº12), en las formas que se le escapaban")
# ⚠️ Un «0 muertas» no vale nada si el lector no sabe reconocer una muerta cuando la hay.
# Se comprueba con baterías CONSTRUIDAS en memoria, sin tocar ningun fichero.
_REF = "core/schedule.py"
_VIVA = 'def schedule_svg('
_MUERTA = "ESTE TEXTO NO ESTA EN NINGUN MODULO xyzzy"
(ok if _resuelve(_REF) and _VIVA in io.open(_resuelve(_REF), encoding="utf-8").read() else fallo)(
    "el caso conocido-bueno existe de verdad (%s en %s)" % (_VIVA, _REF))
_CASOS = {
    # el hueco de romper_v442: el REEMPLAZO sí está en el código; el ancla, no
    "reemplazo presente, ancla muerta": (
        "ROTURAS = [('desc', %r, %r, %r)]\nfor desc, rel, viejo, nuevo in ROTURAS:\n    pass\n"
        % (_REF, _MUERTA, _VIVA), 1),
    # el hueco de romper_v430/v436: la lista no se llama ROTURAS
    "lista llamada CASOS": (
        "CASOS = [('t', %r, %r, 'x')]\nfor i, (tit, rel, a, b) in enumerate(CASOS, 1):\n    pass\n"
        % (_REF, _MUERTA), 1),
    # el hueco de las «ilegibles»: el ancla se arma con `.join()` y una constante
    "ancla armada con .join()": (
        "N = chr(10)\nROTURAS = [('d', %r, [(N.join([%r, %r]), 'x')])]\n"
        "for desc, rel, cambios in ROTURAS:\n    pass\n" % (_REF, _MUERTA, "b"), 1),
    "la tupla pasada a una función (`prueba(*r)`)": (
        "def prueba(desc, fich, viejo, nuevo):\n    pass\nROTURAS = [('d', %r, %r, 'x')]\n"
        "for r in ROTURAS:\n    prueba(*r)\n" % (_REF, _MUERTA), 1),
    "conocido-bueno (no debe salir muerta)": (
        "ROTURAS = [('d', %r, %r, 'x')]\nfor desc, rel, viejo, nuevo in ROTURAS:\n    pass\n"
        % (_REF, _VIVA), 0),
}
for _n, (_src, _esperadas) in _CASOS.items():
    _a = A.analiza(AQUI / "romper_sonda.py", fuente=_src)
    _bien = len(_a["muertas"]) == _esperadas and not _a["ilegibles"] and not _a["sin_forma"]
    (ok if _bien else fallo)("%s: %d muerta(s), como debe" % (_n, _esperadas) if _bien
                             else "%s: %s" % (_n, _a))
(ok if _resuelve("core/no_existe_este_modulo.py") is None else fallo)(
    "...y un fichero inexistente se reconoce como tal")

print("")
if _fallos:
    print("FALLOS: %d" % len(_fallos))
    sys.exit(1)
print("TODO OK - %d comprobaciones" % _n_ok)
