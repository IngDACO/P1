# -*- coding: utf-8 -*-
"""v487 · Los desplegables que SOBRESCRIBIAN en silencio y las KPIs de inventario en 0.

El patron `L.index(v) if v in L else 0` delante de un desplegable que EDITA: si el valor
guardado no esta en L —una categoria borrada, un rol mal tecleado, un color fuera de la
paleta— se muestra la PRIMERA opcion y «Guardar» la escribe encima, sin que nadie la
eligiera. Estaba en 12 sitios de 6 pantallas (inventario, catalogo, proyectos,
localizaciones, usuarios y planificacion). El de Usuarios era el peor: su defecto era
"campo" —español desde v469—, asi que un usuario sin rol salia con OWNER preseleccionado.

Las KPIs y las escrituras en español las vigila `verif_v469` (bloque 10); el EJECUTADO
de las pantallas, `check_v487_smoke`. Este mira el patron en TODO el repo.
"""
import ast
import io
import sys
from pathlib import Path

sys.path.insert(0, ".")
_f = []


def ok(m):
    print("   ok   %s" % m)


def fallo(m):
    print("   FALLO %s" % m)
    _f.append(m)


def _arbol(p):
    return ast.parse(io.open(p, encoding="utf-8").read())


def _func_de(arb, ln):
    mejor = None
    for n in ast.walk(arb):
        if isinstance(n, ast.FunctionDef) and n.lineno <= ln <= (n.end_lineno or n.lineno):
            if mejor is None or n.lineno > mejor.lineno:
                mejor = n
    return mejor.name if mejor else "<modulo>"


# ⚠️ Exentos por (fichero, FUNCION), no por numero de linea: una linea se mueve con
# cualquier edicion de arriba y reabre el falso positivo — o exime en silencio una
# comparacion real que caiga en ese numero (v472). Cada uno con su razon.
# ⚠️ Los nombres de la primera version eran SUPUESTOS y 4 de 5 no existian: lo cazo la
# comprobacion de «exentos que siguen existiendo» de abajo (v135 otra vez).
EXENTOS = {
    ("i18n.py", "selector"): "idioma de la SESION: preferencia, no un dato que se guarde",
    ("roster_ui.py", "render_planificacion"): "elige el DIA que se mira (radio): navegacion",
    ("roster_ui.py", "_cumplimiento"): "elige el DIA que se mira (radio): navegacion",
    ("library.py", "set_modelo_activo"): "POSICION de una cabecera, con el orden de HEADERS por defecto",
    ("library.py", "delete_item"): "POSICION de la cabecera ID, con el orden de HEADERS por defecto",
}


def _patron(arb):
    for n in ast.walk(arb):
        if (isinstance(n, ast.IfExp) and isinstance(n.orelse, ast.Constant)
                and n.orelse.value == 0 and isinstance(n.body, ast.Call)
                and getattr(n.body.func, "attr", "") == "index"
                and isinstance(n.test, ast.Compare) and n.test.ops
                and isinstance(n.test.ops[0], ast.In)):
            yield n


print("1. El patron que sobrescribe en silencio no queda en ningun desplegable")
# ⚠️ Sonda validada contra el patron construido antes de creerse su cero (trampa n12).
_caso = ast.parse("i = L.index(v) if v in L else 0\n")
(ok if list(_patron(_caso)) else fallo)("la sonda VE el patron construido")

_malos, _vistos = [], set()
for p in sorted(Path("core").glob("*.py")) + [Path("app.py")]:
    arb = _arbol(p)
    for n in _patron(arb):
        clave = (p.name, _func_de(arb, n.lineno))
        if clave in EXENTOS:
            _vistos.add(clave)
            continue
        _malos.append("%s:%d en %s()" % (p.name, n.lineno, clave[1]))
(ok if not _malos else fallo)(
    "0 sitios fuera de los exentos" + ("" if not _malos else " -> " + " · ".join(_malos)))
# ⚠️ Y un exento que ya no existe se DICE: una lista de exenciones que envejece acaba
# eximiendo una funcion nueva con el mismo nombre sin que nadie lo decidiera.
_muertos = sorted(set(EXENTOS) - _vistos)
(ok if not _muertos else fallo)(
    "todos los exentos siguen existiendo" + ("" if not _muertos else " -> %s" % _muertos))

print("")
print("2. `opciones_con_actual` EJECUTADO")
from core import ui_common as ui  # noqa: E402
CASOS = [((["a", "b"], "b"), (["a", "b"], 1)),
         ((["a", "b"], "z"), (["z", "a", "b"], 0)),        # se CONSERVA
         ((["a", "b"], ""), (["a", "b"], 0)),              # vacio: nada que proteger
         ((["a", "b"], None), (["a", "b"], 0)),
         ((["", "a"], ""), (["", "a"], 0)),                # el vacio SI esta en la lista
         ((("a", "b"), "  "), (["a", "b"], 0))]           # solo espacios no es un dato
_mal = [(e, ui.opciones_con_actual(*e), s) for e, s in CASOS if ui.opciones_con_actual(*e) != s]
(ok if not _mal else fallo)("%d casos" % len(CASOS) + ("" if not _mal else " -> %r" % _mal))
# ⚠️ no puede mutar la lista que recibe: son constantes de modulo (ESTADOS, ROLES…) y
# anteponerle un valor las cambiaria para TODA la app hasta reiniciar el proceso.
_L = ["a", "b"]
ui.opciones_con_actual(_L, "z")
(ok if _L == ["a", "b"] else fallo)("no muta la lista que recibe (son constantes de modulo)")

print("")
print("3. Las pantallas editan con el helper")
USOS = {"inventory_ui.py": 4, "catalogo_ui.py": 2, "projects_ui.py": 3,
        "auth_ui.py": 2, "roster_ui.py": 1}
for fich, n_min in USOS.items():
    arb = _arbol(Path("core") / fich)
    n = sum(1 for c in ast.walk(arb) if isinstance(c, ast.Call)
            and getattr(c.func, "attr", "") == "opciones_con_actual")
    (ok if n >= n_min else fallo)("%s: %d usos (minimo %d)" % (fich, n, n_min))
    _mod = {a.asname or a.name for x in arb.body
            if isinstance(x, (ast.Import, ast.ImportFrom)) for a in x.names}
    (ok if "ui" in _mod else fallo)("%s importa ui_common a nivel de MODULO" % fich)

print("")
print("4. Usuarios: el rol por defecto es CANONICO (no «campo»)")
from core import auth  # noqa: E402
_src = io.open("core/auth_ui.py", encoding="utf-8").read()
_arb = ast.parse(_src)
_defs = [v.value for n in ast.walk(_arb) if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or)
         for v in n.values[1:] if isinstance(v, ast.Constant) and isinstance(v.value, str)
         and n.values[0] is not None and "Role" in ast.unparse(n.values[0])]
(ok if _defs and all(d in auth.ROLES for d in _defs) else fallo)(
    "los defectos del rol estan en ROLES: %r" % _defs)

print("")
print("5. El color de un trabajo fuera de la paleta se CONSERVA al guardar")
# ⚠️ Anteponerlo al desplegable no basta: el guardado hacia `_colmap[_cn]`, que con un
# valor que no es un nombre de la paleta lanza KeyError y el formulario no guardaria.
_r = io.open("core/roster_ui.py", encoding="utf-8").read()
(ok if '_colmap.get(_cn, _cn)' in _r and '_colmap[_cn]' not in _r else fallo)(
    "el guardado usa `_colmap.get(_cn, _cn)`")

print("")
if _f:
    print("%d FALLO(S) - v487" % len(_f))
    sys.exit(1)
print("TODO OK - v487")
