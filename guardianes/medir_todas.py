# -*- coding: utf-8 -*-
"""Qué CABECERA se pinta de verdad en cada tabla, y qué VALOR literal sale en la celda.

⚠️ Una clave española NO es un fallo por sí sola: si su `column_config` la renombra,
en pantalla sale en inglés (patrón v444). Lo que se mide es la RESTA: claves de fila
que ningún `column_config` cubre → se pintan tal cual.

⚠️ Dos correcciones sobre la primera versión, que daba un recuento inflado:
  1. El mapa de dicts iba por NOMBRE de variable en TODO el módulo, así que el `rows`
     de una función se mezclaba con el `rows` de otra y cada tabla heredaba cabeceras
     ajenas. Ahora el ámbito es la FUNCIÓN.
  2. Contaba como «valor de celda» el argumento de `p.get("Nombre")`, que es una
     LECTURA de la hoja, no un texto que se pinte. Ahora solo cuentan los literales
     que son el valor en sí (o las dos ramas de un `x if c else y`).
"""
import ast
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

from barre_cortas import _sin                                      # noqa: E402
from barre_fstr_mixto import ES                                    # noqa: E402

UI = sorted(list((RAIZ / "core").glob("*_ui.py")) + [RAIZ / "app.py"])
_ES = {_sin(x) for x in ES}
TABLA = {"dataframe", "data_editor", "table"}


def _esp(s):
    return any(_sin(p) in _ES for p in re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñü]+", s))


def _claves(d):
    return [k.value for k in d.keys
            if isinstance(k, ast.Constant) and isinstance(k.value, str)]


def _lit(nodo, dentro_t):
    """El literal que ACABA en la celda: la constante, o las ramas de un if/else."""
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
        return [] if id(nodo) in dentro_t else [(nodo.lineno, nodo.value)]
    if isinstance(nodo, ast.IfExp):
        return _lit(nodo.body, dentro_t) + _lit(nodo.orelse, dentro_t)
    if isinstance(nodo, ast.BoolOp):
        return [x for v in nodo.values for x in _lit(v, dentro_t)]
    return []


def _funciones(tr):
    """Cada función con su cuerpo, SIN descender a las anidadas (ámbito propio)."""
    out = []
    for n in ast.walk(tr):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append(n)
    return out


def analiza(ruta):
    tr = ast.parse(Path(ruta).read_text(encoding="utf-8"))
    dentro_t = set()
    for n in ast.walk(tr):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
           and n.func.id in {"t", "d", "_d"}:
            dentro_t |= {id(x) for x in ast.walk(n)}

    out = []
    for fn in _funciones(tr):
        dicts = {}
        for n in ast.walk(fn):
            if isinstance(n, ast.Assign) and isinstance(n.value, ast.Dict):
                for tg in n.targets:
                    if isinstance(tg, ast.Name):
                        dicts.setdefault(tg.id, []).append(n.value)
            if isinstance(n, ast.Call) \
               and getattr(n.func, "attr", "") in {"append", "update"} \
               and isinstance(getattr(n.func, "value", None), ast.Name):
                for a in n.args:
                    if isinstance(a, ast.Dict):
                        dicts.setdefault(n.func.value.id, []).append(a)
                    elif isinstance(a, ast.Name) and a.id in dicts:
                        dicts.setdefault(n.func.value.id, []).extend(dicts[a.id])

        for n in ast.walk(fn):
            if not (isinstance(n, ast.Call)
                    and getattr(n.func, "attr", "") in TABLA):
                continue
            fuentes = {x.id for a in n.args for x in ast.walk(a)
                       if isinstance(x, ast.Name)}
            filas = [d for f in fuentes for d in dicts.get(f, [])]
            if not filas:
                continue
            cfg = set()
            for k in n.keywords:
                if k.arg == "column_config" and isinstance(k.value, ast.Dict):
                    cfg |= set(_claves(k.value))
            cab, vals = set(), set()
            for d in filas:
                for c in _claves(d):
                    if c not in cfg :
                        cab.add(c)
                for v in d.values:
                    for _ln, s in _lit(v, dentro_t):
                        s = s.strip()
                        if s and len(s) <= 40 and _esp(s):
                            vals.add(s)
            if cab or vals:
                out.append((fn.name, n.lineno, sorted(cab), sorted(vals)))
    return out


if __name__ == "__main__":
    tc = tv = 0
    for f in UI:
        res = analiza(f)
        if not res:
            continue
        print(f"\n── {f.name}")
        for fname, ln, cab, vals in res:
            print(f"   {fname}()  línea {ln}")
            if cab:
                print(f"      cabeceras SIN column_config: {cab}")
                tc += len(cab)
            if vals:
                print(f"      valores de celda:            {vals}")
                tv += len(vals)
    print(f"\n{tc} cabeceras y {tv} valores en español que SE PINTAN")
