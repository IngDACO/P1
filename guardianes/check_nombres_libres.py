# -*- coding: utf-8 -*-
"""Ningún módulo de `core` usa un nombre que no existe (21/09/2026).

Por qué existe: esta familia mordió DOS veces el mismo día.
  · v502 → `_etq_us` ligado como variable donde ya era función de módulo:
    `UnboundLocalError` que tumbó la pantalla de detalle entera, en producción.
  · v509 → `theme.dinero(...)` en un módulo que importa `theme as T`: `NameError`
    esperando a que alguien abriera el desplegable.

Las dos son invisibles para `compileall` y para el import: Python solo se queja cuando
EJECUTA esa línea, y una línea dentro de un `if` o de un expander puede tardar semanas en
ejecutarse. `verif_v311` ya hacía este barrido, pero sobre UNA función.

⚠️ El barrido de nombres libres es famoso por los falsos positivos (trampa nº3:
argumentos de `lambda`, operador morsa, `__file__`…). Aquí se contemplan además los
ámbitos ENVOLVENTES —una función anidada que usa un local de su madre es legítima—,
`global`/`nonlocal`, los objetivos de `for`, `with … as`, `except … as` y las
comprensiones. Si aun así denunciara código sano, la red se estrecha: una que acusa a
los buenos se relaja y deja de proteger (la lección del `$` en v508).
"""
import ast
import builtins
import os
import pathlib
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

fallos, n_ok = [], 0


def ok(q):
    global n_ok
    n_ok += 1
    print(f"  ok   {q}")


def fallo(q, d=""):
    fallos.append(q)
    print(f"  *** FALLO  {q}" + (f"  -> {d}" if d else ""))


def ck(q, real, esp):
    ok(q) if real == esp else fallo(q, f"{real!r} != {esp!r}")


BUILTINS = set(dir(builtins)) | {"__file__", "__name__", "__doc__", "__package__"}


def _ligados(nodo, incluir_args=True):
    """Nombres que ESE ámbito liga, sin descender a ámbitos hijos."""
    out = set()
    if incluir_args and isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
        a = nodo.args
        for x in list(a.posonlyargs) + list(a.args) + list(a.kwonlyargs):
            out.add(x.arg)
        for x in (a.vararg, a.kwarg):
            if x:
                out.add(x.arg)

    def rec(n, raiz=False):
        for h in ast.iter_child_nodes(n):
            if isinstance(h, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out.add(h.name)              # el nombre SÍ se liga aquí; su cuerpo no
                continue
            if isinstance(h, ast.Lambda):
                continue
            if isinstance(h, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                continue                     # su ámbito es propio
            if isinstance(h, ast.Name) and isinstance(h.ctx, (ast.Store, ast.Del)):
                out.add(h.id)
            elif isinstance(h, ast.NamedExpr) and isinstance(h.target, ast.Name):
                out.add(h.target.id)         # operador morsa (trampa nº3)
            elif isinstance(h, (ast.Import, ast.ImportFrom)):
                for x in h.names:
                    out.add((x.asname or x.name).split(".")[0])
            elif isinstance(h, ast.ExceptHandler) and h.name:
                out.add(h.name)
            elif isinstance(h, (ast.Global, ast.Nonlocal)):
                out.update(h.names)
            rec(h)
    rec(nodo, raiz=True)
    return out


def _libres(fn, envolventes):
    """Nombres LEÍDOS en `fn` que no liga nadie: ni él, ni sus ámbitos envolventes.

    ⚠️ Las comprensiones se tratan como ÁMBITOS PROPIOS y se recorren recursivamente,
    pasando hacia dentro lo que ya es visible. El primer intento las resolvía de una
    pasada, así que una comprensión DENTRO de otra —`[{k: v for k, v in x.items()}
    for x in xs]`— denunciaba `k` y `v` como libres: los ligaba la interior y el
    barrido solo miraba los objetivos de la exterior. Denunció nueve módulos sanos.
    """
    malos = set()

    def rec(n, visibles):
        for h in ast.iter_child_nodes(n):
            if isinstance(h, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                              ast.Lambda)):
                continue                     # se visita aparte, con su propio ámbito
            if isinstance(h, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                _propios = {t.id for g in h.generators for t in ast.walk(g.target)
                            if isinstance(t, ast.Name)}
                rec(h, visibles | _propios)   # su ámbito, y lo de fuera sigue visible
                continue
            if isinstance(h, ast.Name) and isinstance(h.ctx, ast.Load) \
                    and h.id not in visibles:
                malos.add(h.id)
            rec(h, visibles)

    rec(fn, set(envolventes) | _ligados(fn) | BUILTINS)
    return malos


def revisar(ruta):
    try:
        tr = ast.parse(ruta.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return {}
    nivel_mod = _ligados(tr, incluir_args=False)
    out = {}

    def _directas(nodo):
        """Funciones anidadas de PRIMER nivel: no se desciende a las de dentro.

        ⚠️ `ast.walk` aplana la anidación, y con él una función de tercer nivel se
        comprobaba contra el ámbito de su ABUELA, saltándose a la madre. Así
        `survey_ui._highlight` —anidada en `make_highlighter(lim_map, min_vals, …)` y
        que cierra sobre sus ARGUMENTOS— salía denunciada con seis nombres, siendo
        código perfectamente correcto.
        """
        out_f = []

        def rec(n):
            for h in ast.iter_child_nodes(n):
                if isinstance(h, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out_f.append(h)
                    continue                  # su interior lo ve su propia pasada
                if isinstance(h, (ast.ClassDef, ast.Lambda)):
                    continue
                rec(h)
        rec(nodo)
        return out_f

    def andar(nodo, envolventes):
        for h in _directas(nodo):
            _m = _libres(h, envolventes)
            if _m:
                out.setdefault(h.name, set()).update(_m)
            andar(h, set(envolventes) | _ligados(h))

    for n in tr.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _m = _libres(n, nivel_mod)
            if _m:
                out.setdefault(n.name, set()).update(_m)
            andar(n, set(nivel_mod) | _ligados(n))
        elif isinstance(n, ast.ClassDef):
            for m in n.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    _mm = _libres(m, nivel_mod)
                    if _mm:
                        out.setdefault("%s.%s" % (n.name, m.name), set()).update(_mm)
    return out


print("\n[1] ningun modulo de core usa un nombre que no existe")
rotos = {}
for p in sorted(pathlib.Path(os.path.join(RAIZ, "core")).glob("*.py")):
    r = revisar(p)
    if r:
        rotos[p.name] = {k: sorted(v) for k, v in r.items()}

ck("⚠️ 0 nombres libres en core", rotos, {})
if rotos:
    for m, fns in sorted(rotos.items()):
        for fn, ns in sorted(fns.items()):
            print("        %s :: %s -> %s" % (m, fn, ", ".join(ns)))

print("\n[2] la red sabe ver, y sabe NO denunciar (nº12 y nº3)")
import tempfile                                                    # noqa: E402
_casos = [
    ("nombre inexistente", "def f():\n    return theme.dinero(1)\n", True),
    ("alias correcto", "from core import theme as T\ndef f():\n    return T.dinero(1)\n", False),
    ("cierre sobre un local de la madre",
     "def a():\n    x = 1\n    def b():\n        return x\n    return b()\n", False),
    ("argumento de lambda", "def f():\n    return (lambda y: y + 1)(2)\n", False),
    ("operador morsa", "def f(s):\n    if (m := s.find('a')) > 0:\n        return m\n    return 0\n", False),
    ("objetivo de comprension", "def f(xs):\n    return [i * 2 for i in xs]\n", False),
    ("with ... as", "def f(p):\n    with open(p) as fh:\n        return fh.read()\n", False),
    ("except ... as", "def f():\n    try:\n        pass\n    except ValueError as e:\n        return e\n", False),
    # el falso positivo que tuvo: una funcion de tercer nivel que cierra sobre los
    # ARGUMENTOS de su madre (es `survey_ui._highlight` reducido a lo esencial)
    ("tercer nivel cerrando sobre los args de su madre",
     "def a():\n    def b(x, y):\n        def c(df):\n            return x + y\n"
     "        return c\n    return b\n", False),
    ("comprension ANIDADA",
     "def f(xs):\n    return [{k: v for k, v in x.items()} for x in xs]\n", False),
    ("def anidado llamado por su nombre",
     "def f():\n    def g():\n        return 1\n    return g()\n", False),
]
with tempfile.TemporaryDirectory() as _td:
    for etq, src, espera_malo in _casos:
        _p = pathlib.Path(_td) / "caso.py"
        _p.write_text(src, encoding="utf-8")
        ck(("detecta: " if espera_malo else "no denuncia: ") + etq,
           bool(revisar(_p)), espera_malo)

print("\n" + "=" * 70)
print(f"{n_ok + len(fallos)} comprobaciones — " + ("TODO OK" if not fallos else "HAY FALLOS"))
sys.exit(1 if fallos else 0)
