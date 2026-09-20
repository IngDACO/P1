"""PRE-VUELO: ¿qué módulos usan `t` / `d` / `_d` como VARIABLE?

⚠️ Se corre ANTES de traducir un módulo, no después. Si `t` ya es una variable o un
parámetro en una función y la traducción le mete una llamada `t(...)`, Python marca el
nombre local en el ÁMBITO ENTERO y la función revienta:
  · `t = Q.totales(...)` más arriba  → UnboundLocalError en la primera etiqueta
  · `def f(..., t)` o `for t in ...` → `t("…")` llama a un dict/str → TypeError
No lo ve `compileall`, no lo ve importar el módulo: solo se ve ejecutando la pantalla.
Pasó en v437 (glosario), en v439 (fichaje y ausencias) y otra vez en `quotes_ui` — las
tres veces DESPUÉS de traducir, con el daño ya escrito.

    python pre_i18n.py core/projects_ui.py core/auth_ui.py ...

Salida: por módulo, las funciones que habría que renombrar ANTES de tocarlo.
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")


def _mismo_ambito(fn):
    """Nodos de ESTA función. NO desciende a lambdas ni a funciones anidadas: tienen
    su propio ámbito, así que un `lambda t: …` no tapa nada (trampa nº3)."""
    out = []
    for h in fn.body:
        pila = [h]
        while pila:
            n = pila.pop()
            out.append(n)
            for c in ast.iter_child_nodes(n):
                if not isinstance(c, (ast.Lambda, ast.FunctionDef,
                                      ast.AsyncFunctionDef, ast.ClassDef)):
                    pila.append(c)
    return out


def _objetivos_comprension(nodos):
    """ids de los Name que son VARIABLE de una comprensión.

    ⚠️ En Python 3 una comprensión tiene su PROPIO ámbito, así que
    `[t for t, e in ...]` NO liga `t` en la función que la contiene y no tapa nada.
    Contarlos daba falsos positivos en `roster_ui._radar_scan` y
    `_cumplimiento_celda`, que están perfectamente bien. Es la trampa nº3.
    """
    fuera = set()
    for n in nodos:
        for g in getattr(n, "generators", []) or []:
            for nn in ast.walk(g.target):
                if isinstance(nn, ast.Name):
                    fuera.add(id(nn))
    return fuera


def revisar(rel):
    tr = ast.parse((RAIZ / rel).read_text(encoding="utf-8"))
    hallazgos = []
    for fn in ast.walk(tr):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        nod = _mismo_ambito(fn)
        _comp = _objetivos_comprension(nod)
        args = {a.arg for a in fn.args.args + fn.args.kwonlyargs + fn.args.posonlyargs}
        for nm in ("t", "d", "_d"):
            sitios = sorted({n.lineno for n in nod
                             if isinstance(n, ast.Name)
                             and isinstance(n.ctx, ast.Store) and n.id == nm
                             and id(n) not in _comp})
            if nm in args:
                sitios.insert(0, fn.lineno)
            if sitios:
                hallazgos.append((fn.name, fn.lineno, nm, sitios))
    return hallazgos


total = 0
for rel in sys.argv[1:]:
    h = revisar(rel)
    total += len(h)
    estado = f"{len(h)} a renombrar" if h else "limpio"
    print(f"{rel:28} {estado}")
    for nombre, ln, nm, sitios in h:
        print(f"     `{nm}` en {nombre}() def:{ln} → asignado en {sitios[:6]}")
print(f"\n{total} funciones que habría que renombrar ANTES de traducir"
      if total else "\nTodos limpios: se puede traducir sin renombrar nada")
