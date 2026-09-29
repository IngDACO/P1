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
entrar en la suite, y cubre las 52 baterias de una pasada (regla v385: si se puede
comprobar sin tocar produccion, hazlo estatico).
"""
import ast
import io
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AQUI = Path(__file__).parent
APP = Path(r"C:\Users\diego\P1\survey_app")

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
    o desde `core` («x.py»). Se prueban las dos, que es lo que hacen ellas."""
    for cand in (APP / p, APP / "core" / p):
        if cand.is_file():
            return cand
    return None


# ⚠️ v524 · Lo que un elemento de la tupla VALE sin ejecutar nada. Hasta aqui solo se leian
# LITERALES, y una tupla con el fichero en una constante (`UI = "core/daily_log_ui.py"`,
# como escriben romper_v522 y romper_v523) salia con None y se saltaba como «rotura
# desactivada a proposito» — en SILENCIO. Las 30 de romper_v523 no se vigilaron nunca, y
# cuatro llevaban muertas desde el cambio siguiente. Es la trampa nº30: el «0 muertas» valia
# solo para la forma que este chequeo sabia leer.
_NO_SE = object()


def _consts(arbol):
    """Las constantes de TEXTO de nivel de modulo de una bateria."""
    out = {}
    for n in arbol.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 \
                and isinstance(n.targets[0], ast.Name):
            v = _valor(n.value, out)
            if isinstance(v, str):
                out[n.targets[0].id] = v
    return out


def _valor(nodo, consts):
    """Literal, constante del modulo o suma de textos; si no, `_NO_SE`."""
    if isinstance(nodo, ast.Constant):
        return nodo.value
    if isinstance(nodo, ast.Name) and nodo.id in consts:
        return consts[nodo.id]
    if isinstance(nodo, ast.BinOp) and isinstance(nodo.op, ast.Add):
        a, b = _valor(nodo.left, consts), _valor(nodo.right, consts)
        if isinstance(a, str) and isinstance(b, str):
            return a + b
    return _NO_SE


def _tuplas(arbol):
    """Las tuplas literales asignadas a ROTURAS/CONTROL (o dentro de esa lista).

    ⚠️ No se busca «cualquier tupla del fichero»: una bateria trae tuplas para otras
    cosas y contarlas aqui inflaria el numero de anclas revisadas, que es justo lo que
    hace que un recuento deje de significar algo.
    """
    out = []
    for n in ast.walk(arbol):
        if not isinstance(n, ast.Assign):
            continue
        if not any(getattr(t, "id", "") in ("ROTURAS", "CONTROL") for t in n.targets):
            continue
        val = n.value
        elems = val.elts if isinstance(val, (ast.List, ast.Tuple)) else []
        if isinstance(val, ast.Tuple):          # CONTROL suele ser UNA tupla suelta
            out.append(val)
            continue
        for e in elems:
            if isinstance(e, ast.Tuple):
                out.append(e)
    return out


print("1. Cada ancla de cada bateria existe todavia en el fichero que nombra")
_bats = sorted(AQUI.glob("romper_*.py"))
_rev = _vivas = 0
_muertas, _sin_leer, _ilegibles = [], [], []
_rev_por_bat = {}
for b in _bats:
    try:
        arbol = ast.parse(io.open(b, encoding="utf-8").read())
    except SyntaxError as e:
        fallo("%s no compila: %s" % (b.name, e))
        continue
    _c = _consts(arbol)
    for tup in _tuplas(arbol):
        vals = [_valor(c, _c) for c in tup.elts]
        # ⚠️ Lo que no se puede saber sin ejecutar se CUENTA y se dice, no se salta callado.
        if any(v is _NO_SE for v in vals):
            _ilegibles.append("%s:%d" % (b.name, tup.lineno))
            continue
        # ⚠️ Un None LITERAL en la tupla = rotura desactivada a proposito (las baterias
        # las saltan mirando su descripcion). No se cuenta ni como viva ni como muerta.
        if any(v is None for v in vals) or not all(isinstance(v, str) for v in vals):
            continue
        # ⚠️ NO se adivina cual de las cadenas es el ancla por su POSICION. Las 52
        # baterias usan al menos cuatro formas distintas —(desc, fichero, viejo, nuevo),
        # (fichero, desc, viejo, nuevo), (fichero, viejo, nuevo, desc) y (guardian,
        # fichero, viejo, nuevo, desc)— y mi primera version, que leia «la cadena de
        # detras del .py», denuncio 60 anclas de las que buena parte eran DESCRIPCIONES
        # sanas. Acusar codigo sano es el fallo de v385, y aqui habria llevado a
        # «arreglar» cincuenta baterias que funcionan.
        #
        # Lo que SI se puede afirmar sin adivinar: si NINGUNA de las cadenas de la tupla
        # aparece en el fichero que la propia tupla nombra, esa rotura no puede parchear
        # nada. Es una afirmacion mas debil y por eso no tiene falsos positivos.
        _ficheros = [(v, _resuelve(v)) for v in vals if v.endswith(".py")]
        _prod = [(v, d) for v, d in _ficheros if d is not None]
        if not _prod:
            # Ninguna ruta de produccion: o nombra un guardian (v442 lo hace) o la
            # arma en tiempo de ejecucion. No se puede juzgar, y se dice.
            _sin_leer.append("%s:%d" % (b.name, tup.lineno))
            continue
        _rev += 1
        _rev_por_bat[b.name] = _rev_por_bat.get(b.name, 0) + 1
        _textos = [v for v in vals if not v.endswith(".py") and len(v) >= 10]
        _hay = False
        for _v, _d in _prod:
            _src = io.open(_d, encoding="utf-8").read()
            if any(x in _src for x in _textos):
                _hay = True
                break
        if _hay:
            _vivas += 1
        else:
            _muertas.append("%s:%d -> ninguna de sus %d cadenas esta en %s: %r"
                            % (b.name, tup.lineno, len(_textos),
                               ", ".join(v for v, _ in _prod),
                               (_textos[0][:60] if _textos else "(sin texto)")))

# ⚠️ Antes de celebrar el «0 muertas» hay que afirmar que se ha mirado ALGO: con un
# parser que no encontrara ninguna tupla, esto saldria verde sin revisar nada (trampa nº1).
(ok if len(_bats) >= 40 else fallo)("se encontraron las baterias (%d)" % len(_bats))
(ok if _rev >= 300 else fallo)("...y se leyeron sus anclas (%d revisadas)" % _rev)
# ⚠️ v524 · La sonda SABE leer una bateria escrita con constantes (trampa nº12): si no,
# el arreglo de arriba podria no estar haciendo nada y esto seguiria en verde.
(ok if _rev_por_bat.get("romper_v523.py", 0) >= 25 else fallo)(
    "...incluidas las que nombran el fichero con una CONSTANTE (romper_v523: %d)"
    % _rev_por_bat.get("romper_v523.py", 0))
# ⚠️ v524 · Lo que sigue sin poder leerse se DECLARA, con el mismo trinquete que las
# muertas: 128 tuplas de 21 baterias viejas arman el ancla con `%`, `.join()`, listas o
# subindices, y leerlas exigiria ejecutarlas. Hasta hoy se saltaban CALLADAS; ahora se
# cuentan en cada pasada, y una bateria NUEVA escrita asi pone esto en rojo — que es lo
# que habria cazado a romper_v523 el dia que nacio.
ILEGIBLES = {
    "romper_v430_reanclado.py": 3, "romper_v437.py": 10, "romper_v438.py": 12,
    "romper_v447.py": 1, "romper_v448.py": 1, "romper_v459.py": 1, "romper_v482.py": 9,
    "romper_v483.py": 11, "romper_v484.py": 6, "romper_v486.py": 5, "romper_v487.py": 1,
    "romper_v488.py": 17, "romper_v490.py": 16, "romper_v501.py": 3, "romper_v502.py": 6,
    "romper_v505.py": 5, "romper_v506.py": 3, "romper_v509.py": 3, "romper_v510.py": 3,
    "romper_v512.py": 7, "romper_v514.py": 5,
}
_il = {}
for s in _ilegibles:
    _il[s.split(":")[0]] = _il.get(s.split(":")[0], 0) + 1
_il_mas = {b: n for b, n in _il.items() if n > ILEGIBLES.get(b, 0)}
_il_menos = {b: ILEGIBLES[b] - _il.get(b, 0) for b in ILEGIBLES if _il.get(b, 0) < ILEGIBLES[b]}
(ok if not _il_mas else fallo)(
    "ninguna bateria NUEVA se escribe en una forma que no se sabe leer (%d ilegibles, "
    "%d declaradas)" % (len(_ilegibles), sum(ILEGIBLES.values())))
for b, n in sorted(_il_mas.items()):
    print("        %s: %d ilegibles, %d declaradas" % (b, n, ILEGIBLES.get(b, 0)))
(ok if not _il_menos else fallo)("...y lo declarado sigue exacto (nada leido sin bajarlo)")
for b, n in sorted(_il_menos.items()):
    print("        %s: %d menos — bajar ILEGIBLES a %d" % (b, n, _il.get(b, 0)))

# ⚠️ DEUDA DECLARADA, no exceptuada. Al nacer este chequeo (v515) habia 15 anclas
# muertas repartidas en 11 baterias, TODAS colaterales de la migracion al ingles
# (v441-v453) y del renombrado de hojas (v465): el ancla nombra una columna, un estado o
# una hoja que se renombro a proposito y nadie volvio a la bateria. No se arreglan aqui
# porque son de otros dominios —facturas, inventario, correcciones, roster— y cada una
# necesita entender que protegia y volver a correr su bateria entera.
#
# ⚠️ Esto NO es una lista de excepciones: es un TRINQUETE. Falla si alguna bateria tiene
# MAS muertas de las declaradas (rot nuevo) y TAMBIEN si tiene MENOS (la declaracion se
# quedo vieja). Lo segundo es lo que impide que esta lista se convierta en el mismo
# problema que viene a denunciar: en cuanto alguien repare una, el chequeo obliga a
# bajar el numero aqui. Y las 15 se imprimen en cada pasada, o sea que la deuda se ve.
DEUDA = {
    "romper_v440.py": 1, "romper_v441.py": 1, "romper_v446.py": 1,
    "romper_v450.py": 1, "romper_v452.py": 2,
    "romper_v455.py": 1, "romper_v459.py": 2, "romper_v461.py": 3,
    "romper_v472.py": 2, "romper_v502.py": 1,
}
_por_bat = {}
for m in _muertas:
    _por_bat[m.split(":")[0]] = _por_bat.get(m.split(":")[0], 0) + 1
_nuevas = {b: n for b, n in _por_bat.items() if n > DEUDA.get(b, 0)}
_arregladas = {b: DEUDA[b] - _por_bat.get(b, 0) for b in DEUDA
               if _por_bat.get(b, 0) < DEUDA[b]}
(ok if not _nuevas else fallo)(
    "ninguna bateria tiene anclas muertas nuevas (%d muertas, %d declaradas)"
    % (len(_muertas), sum(DEUDA.values())))
for b, n in sorted(_nuevas.items()):
    print("        %s: %d muertas, %d declaradas" % (b, n, DEUDA.get(b, 0)))
(ok if not _arregladas else fallo)(
    "...y la deuda declarada sigue siendo exacta (nada reparado sin bajarla)")
for b, n in sorted(_arregladas.items()):
    print("        %s: %d reparada(s) — bajar DEUDA a %d" % (b, n, _por_bat.get(b, 0)))

print("")
print("   deuda viva (%d anclas, todas de la migracion al ingles):" % len(_muertas))
for m in _muertas:
    print("        %s" % m)

print("")
print("2. La sonda SABE ver un ancla muerta (trampa nº12)")
# ⚠️ Un «0 muertas» no vale nada si el lector no sabe reconocer una muerta cuando la
# hay. Se comprueba con un caso conocido-malo, sin tocar ningun fichero.
_falso = "ESTE TEXTO NO ESTA EN NINGUN MODULO DE PRODUCCION xyzzy"
_ref = _resuelve("core/schedule.py")
(ok if _ref is not None else fallo)("se resuelve un fichero de produccion conocido")
(ok if _ref and _falso not in io.open(_ref, encoding="utf-8").read() else fallo)(
    "...y un ancla inventada NO se encuentra en el (o el chequeo de arriba no valdria)")
(ok if _resuelve("core/no_existe_este_modulo.py") is None else fallo)(
    "...y un fichero inexistente se reconoce como tal")

print("")
if _sin_leer:
    print("(%d tuplas no analizadas: no casan con la forma (fichero, ancla, ...))"
          % len(_sin_leer))
    for s in _sin_leer[:6]:
        print("        %s" % s)

print("")
if _fallos:
    print("FALLOS: %d" % len(_fallos))
    sys.exit(1)
print("TODO OK - %d comprobaciones" % _n_ok)
