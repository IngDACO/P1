# -*- coding: utf-8 -*-
"""NEGOCIO.md contra la VERSION desplegada: que el brief no se quede atrás.

## Por qué existe

El brief estratégico se desfasó **dos veces**: decía v75 con la app en v481, y v484 con
la app en v509. Las dos veces la regla «actualizarlo en el mismo lote» estaba escrita en
el propio documento, y las dos veces falló, porque depende de que alguien se acuerde.
Una regla que depende de la memoria no es un mecanismo. Esto sí se corre entero antes de
cada despliegue (regla v385), así que no se puede ignorar.

## ⚠️ Lo que este guardián NO dice

Mide una **forma**: que el número de versión que el brief declara esté cerca del
desplegado. Un verde significa *«el número coincide»*, **no** *«el brief es cierto»*: no
detecta que una fila de la tabla siga diciendo «no existe» sobre algo construido ayer.
Es la trampa nº30 aplicada a la documentación —un «0» solo vale para la forma que esa
red ve— y se escribe aquí en vez de dejar que el verde tranquilice.

Lo que SÍ caza es el fallo que de verdad ocurrió: el documento quedándose 25 o 400
versiones atrás sin que nadie lo note.

## El umbral no es una constante inventada

Es el número de filas de versión que `CLAUDE.md` mantiene a la vista (regla de ese
documento: un deploy agrega una y borra la más vieja). Si el brief se quedó más atrás
que la ventana que el chat técnico ve de un vistazo, está desfasado. Derivar el número
del propio código en vez de fijarlo a mano es la lección de v395 (trampa nº16: un
guardián atado a una constante caduca cuando la constante cambia a propósito).
"""
import io
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

P1 = Path(__file__).resolve().parent.parent
VERSION = P1 / "survey_app" / "VERSION"
NEGOCIO = P1 / "NEGOCIO.md"
CLAUDE = P1 / "CLAUDE.md"

UMBRAL_POR_DEFECTO = 15
SIN_DATOS = 2
MARCADOR = "Ultima puesta al dia del estado de hecho"

fallos, n_ok = [], 0


def ok(q):
    global n_ok
    n_ok += 1
    print("  ok   %s" % q)


def fallo(q, d=""):
    fallos.append(q)
    print("  *** FALLO  %s" % q + ("  -> %s" % d if d else ""))


def ck(q, real, esp):
    ok(q) if real == esp else fallo(q, "%r != %r" % (real, esp))


def _leer(p):
    """El texto del fichero, o None.

    ⚠️ Devuelve None en vez de lanzar. Un guardián que muere no denuncia: fue el
    patrón que se repitió CINCO veces en un solo día durante v505-v509.
    """
    try:
        return io.open(str(p), encoding="utf-8-sig").read()
    except Exception as e:
        print("  (no se pudo leer %s: %r)" % (p.name, e))
        return None


def _sin_tildes(s):
    """El marcador se compara sin tildes: el documento las lleva y el fichero puede
    guardarse con cualquier normalizacion unicode. Comparar la forma acentuada es
    atarse a un detalle que no es el que importa."""
    tabla = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "Á": "A", "É": "E",
             "Í": "I", "Ó": "O", "Ú": "U", "ñ": "n", "Ñ": "N"}
    return "".join(tabla.get(c, c) for c in str(s or ""))


def version_desplegada(txt):
    """El entero de «vNNN» del fichero VERSION, o None."""
    m = re.search(r"v(\d+)", str(txt or ""))
    return int(m.group(1)) if m else None


def version_del_brief(txt):
    """La ultima version que el brief declara cubrir, o None si falta el marcador.

    ⚠️ Si el marcador no esta, devuelve None y eso acaba en ROJO, nunca en verde: sin
    el no se puede saber a que version corresponde el documento, y un «no lo se» que
    pasa en verde es el paso en vacio de la trampa nº1.
    """
    for linea in str(txt or "").splitlines():
        if MARCADOR in _sin_tildes(linea):
            vs = re.findall(r"v(\d+)", linea)
            return int(vs[-1]) if vs else None
    return None


def umbral(txt_claude):
    """Las filas de version que CLAUDE.md mantiene a la vista."""
    n = len([l for l in str(txt_claude or "").splitlines() if l.startswith("| v")])
    return n if n > 0 else UMBRAL_POR_DEFECTO


def veredicto(app, brief, tope):
    """(ok, motivo) -> ok es True/False/None. Funcion PURA: es la que se autovalida
    abajo contra casos conocidos, que es lo unico que hace que un verde signifique
    algo (trampa nº12: una sonda no vale hasta probar que ve el caso malo)."""
    if app is None:
        return None, "no se pudo leer la VERSION desplegada"
    if brief is None:
        return False, ("NEGOCIO.md no declara a que version corresponde: falta la "
                       "linea «%s»" % MARCADOR)
    d = app - brief
    if d > tope:
        return False, ("el brief va %d versiones por detras (declara v%d, la app esta "
                       "en v%d) y el tope son %d" % (d, brief, app, tope))
    return True, ("el brief declara v%d y la app va por v%d: %d de diferencia, tope %d"
                  % (brief, app, d, tope))


# ═════ 0 · la sonda sabe ver el caso conocido-malo ═══════════════════════════
# ⚠️ Esto va PRIMERO y a proposito. Un guardian que solo se prueba contra el estado
# actual (verde) no demuestra que sepa ponerse rojo, y entonces su verde no informa
# de nada. Es la leccion de v375 y de v408: antes de afirmar «no pasa nada»,
# comprobar que la sonda VE el caso cuando pasa.
print("\n[0] la sonda se valida contra casos conocidos")
for _args, _esp, _etq in (((600, 509, 15), False, "25 versiones por detras -> rojo"),
                          ((525, 509, 15), False, "una por encima del tope -> rojo"),
                          ((524, 509, 15), True, "justo EN el tope -> verde"),
                          ((509, 509, 15), True, "al dia -> verde"),
                          ((400, 509, 15), True, "el brief por delante -> verde"),
                          ((509, None, 15), False, "sin marcador -> rojo, no verde"),
                          ((None, 509, 15), None, "sin VERSION -> ni verde ni rojo")):
    ck("autovalidacion: %s" % _etq, veredicto(*_args)[0], _esp)

# El umbral se deriva, no se inventa: se comprueba que el derivador sepa contar.
ck("el umbral sale de las filas de CLAUDE.md",
   umbral("| v509 | x |\n| v508 | y |\ntexto\n| v507 | z |"), 3)
ck("...y si no hay filas, cae al valor por defecto en vez de dar 0",
   umbral("sin tabla"), UMBRAL_POR_DEFECTO)
ck("el marcador se reconoce con tildes",
   version_del_brief("*Última puesta al día del estado de hecho: 21/09/2026 (v485-v509).*"),
   509)
ck("...y una sola version tambien",
   version_del_brief("Ultima puesta al dia del estado de hecho: 01/01/2026 (v100)."), 100)


# ═════ 1 · el brief contra la app, de verdad ═════════════════════════════════
print("\n[1] el brief contra la app")
_tv, _tn, _tc = _leer(VERSION), _leer(NEGOCIO), _leer(CLAUDE)

if _tv is None or _tn is None:
    print("\nSIN DATOS: falta %s" % ("survey_app/VERSION" if _tv is None else "NEGOCIO.md"))
    sys.exit(SIN_DATOS)

_app = version_desplegada(_tv)
_brief = version_del_brief(_tn)
_tope = umbral(_tc)
_ok, _motivo = veredicto(_app, _brief, _tope)

if _ok is None:
    print("\nSIN DATOS: %s" % _motivo)
    sys.exit(SIN_DATOS)
if _ok:
    ok("NEGOCIO.md esta al dia: " + _motivo)
else:
    fallo("NEGOCIO.md se quedo atras", _motivo)
    print("\n  Que hacer: actualizar el estado de NEGOCIO.md contra el repositorio")
    print("  (no contra la memoria) y mover la linea del marcador a la version de hoy.")
    print("  ⚠️ Y NO basta con cambiar el numero: lo que se desfasa es la tabla de")
    print("  «lo que NO existe todavia», que es la que decide si se puede vender.")

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos), "TODO OK" if not fallos else "HAY FALLOS"))
sys.exit(1 if fallos else 0)
