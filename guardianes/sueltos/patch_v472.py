# -*- coding: utf-8 -*-
"""Arregla las DOS comprobaciones por las que se escaparon dos roturas.

⚠️ Va por fichero y no por heredoc: un `\n` escrito en un heredoc llega mangullado
(trampa nº26, y es la SEXTA vez que muerde).
"""
import ast
import io

P = "verif_v472.py"
s = io.open(P, encoding="utf-8").read()

# ── 1. paginacion: de «aparece la constante» a «lo pintado viene de un CORTE» ──
VIEJO1 = ('_gal = _fn(_SRC_UI, "_galeria")\n'
          '_paginada = _gal is not None and "_POR_PAGINA" in ast.dump(_gal)\n'
          '(ok if _paginada else fallo)("`_galeria` usa `_POR_PAGINA` para paginar")\n')

NUEVO1 = '''_gal = _fn(_SRC_UI, "_galeria")


def _lista_pintada(fn):
    """El nombre de la coleccion que el bucle RECORRE (`for _ in range(0, len(X), 3)`).

    ⚠️ Se busca ESO y no la constante: `_POR_PAGINA` aparece CUATRO veces en
    `_galeria` (el total de paginas y los dos extremos del corte), asi que preguntar
    `"_POR_PAGINA" in dump` daba **verde con el corte BORRADO** — la trampa nº2
    (grep != uso) dentro del guardian, y por ahi se escapo una rotura real.
    """
    for n in ast.walk(fn):
        if not (isinstance(n, ast.For) and isinstance(n.iter, ast.Call)):
            continue
        if getattr(n.iter.func, "id", "") != "range":
            continue
        for a in ast.walk(n.iter):
            if (isinstance(a, ast.Call) and getattr(a.func, "id", "") == "len"
                    and a.args and isinstance(a.args[0], ast.Name)):
                return a.args[0].id
    return None


def _viene_de_un_corte(fn, nombre):
    """`nombre` se asigna de un CORTE (`fotos[a:b]`), no de la lista entera."""
    for n in ast.walk(fn):
        if not isinstance(n, ast.Assign):
            continue
        if not any(getattr(t_, "id", "") == nombre for t_ in n.targets):
            continue
        if isinstance(n.value, ast.Subscript) and isinstance(n.value.slice, ast.Slice):
            return True
    return False


_pint = _lista_pintada(_gal) if _gal is not None else None
_paginada = bool(_pint) and _viene_de_un_corte(_gal, _pint)
(ok if _paginada else fallo)(
    "lo que `_galeria` pinta viene de un CORTE, no de la lista entera", _pint)
'''

# ── 2. tipos canonicos: la igualdad no podia fallar nunca ─────────────────────
VIEJO2 = ('from core import i18n, valores as VAL  # noqa: E402\n'
          '_m = [x for x in LIB.TIPOS\n'
          '      if i18n.etiqueta(x) != x or VAL.canon(x) != x]\n'
          '(ok if not _m else fallo)("los %d tipos son su propia forma canonica"'
          ' % len(LIB.TIPOS), _m)\n')

NUEVO2 = '''from core import i18n, valores as VAL  # noqa: E402

# ⚠️ `etiqueta(x) == x` NO sirve para esto, y es la leccion de v462 mordiendo del
# otro lado: `etiqueta()` devuelve TAL CUAL lo que no conoce, asi que esa igualdad
# es cierta para un canonico Y para un español que nadie mapeo (`foto`, `bodega`,
# cualquier cosa). Era una afirmacion que **no podia fallar nunca**, y por ahi se
# escapo la rotura. Lo que si distingue: el valor tiene que ser un canonico CONOCIDO.
_CANON = set(i18n.VALORES.values())
# ⚠️ Exentos UNO A UNO y con razon, como los simbolos de v463 — no una lista comoda:
#   · `manual` se escribe IGUAL en los dos idiomas: mapearlo seria un «mapa espejo»,
#     que v450 mando borrar.
#   · `datasheet` es el termino tecnico que se usa tal cual en español; inventarle
#     una clave («ficha tecnica») seria adivinar un dato que nadie escribe.
_EXENTOS = {"manual", "datasheet"}
_m = [x for x in LIB.TIPOS if x not in _CANON and x not in _EXENTOS]
(ok if not _m else fallo)(
    "los %d tipos son canonicos conocidos (o exentos con razon)" % len(LIB.TIPOS), _m)

# ⚠️ La sonda, VALIDADA contra un caso conocido-malo antes de creerse su cero
# (trampa nº12): si no viera un tipo en español, el «0» de arriba no diria nada.
_vistos = [x for x in ("foto", "diagrama") if x not in _CANON and x not in _EXENTOS]
(ok if len(_vistos) == 2 else fallo)("la sonda VE un tipo en español si vuelve", _vistos)
# Y que `etiqueta()` los traduzca es lo que hace que el DATO viejo se siga viendo bien.
_tr = [(x, i18n.etiqueta(x)) for x in ("foto", "diagrama")]
(ok if all(a != b for a, b in _tr) else fallo)(
    "`etiqueta()` traduce el español heredado de esos tipos", _tr)
'''

for viejo, nuevo, etq in ((VIEJO1, NUEVO1, "paginacion"), (VIEJO2, NUEVO2, "tipos")):
    if s.count(viejo) != 1:
        raise SystemExit("ancla %s: %d coincidencias (esperaba 1)" % (etq, s.count(viejo)))
    s = s.replace(viejo, nuevo)

ast.parse(s)                      # no se escribe nada que no compile
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v472.py parcheado (las 2 comprobaciones) y compila")
