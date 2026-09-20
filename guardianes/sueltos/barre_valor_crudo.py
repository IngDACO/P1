# -*- coding: utf-8 -*-
"""¿Queda algún sitio que PINTE un valor de dato en crudo, sin `etiqueta()`?

El fallo que lo motiva (v450): `_cumplimiento_equipo` tenía su propio mapa
`{"vigente": "vigente", "por_vencer": "por vencer", …}`, así que las celdas salían
en español mientras `i18n.VALORES` ya sabía traducirlos.

⚠️ El mismo literal es DATO en una comparación y ETIQUETA en un valor de dict, así
que no se puede decidir por la cadena: hay que mirar QUÉ HACE cada aparición.
Se marca solo la que está en posición de VALOR (de un dict o de un `x if c else y`),
que es la que acaba en pantalla; las de comparación y las de índice se dejan.
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

from core.i18n import VALORES                                      # noqa: E402

UI = sorted(list((RAIZ / "core").glob("*_ui.py")) + [RAIZ / "app.py"])
DATOS = set(VALORES)


def _en_t(tr):
    dentro = set()
    for n in ast.walk(tr):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
           and n.func.id in {"t", "d", "_d", "_etq", "etiqueta"}:
            dentro |= {id(x) for x in ast.walk(n)}
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "etiqueta":
            dentro |= {id(x) for x in ast.walk(n)}
    return dentro


def revisa(ruta):
    tr = ast.parse(ruta.read_text(encoding="utf-8"))
    dentro = _en_t(tr)
    # posiciones que NO son pantalla: comparaciones e índices
    seguro = set()
    for n in ast.walk(tr):
        if isinstance(n, ast.Compare):
            for x in [n.left] + list(n.comparators):
                seguro |= {id(y) for y in ast.walk(x)}
        if isinstance(n, ast.Subscript):
            seguro |= {id(y) for y in ast.walk(n.slice)}
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") in {"get", "setdefault"} \
           and n.args:
            seguro |= {id(y) for y in ast.walk(n.args[0])}

    out = []
    for n in ast.walk(tr):
        # valor de un dict literal
        if isinstance(n, ast.Dict):
            for v in n.values:
                for x in ast.walk(v):
                    if isinstance(x, ast.Constant) and isinstance(x.value, str) \
                       and x.value in DATOS and id(x) not in dentro and id(x) not in seguro:
                        out.append((x.lineno, x.value))
        # rama de un `x if c else y`
        if isinstance(n, ast.IfExp):
            for v in (n.body, n.orelse):
                if isinstance(v, ast.Constant) and isinstance(v.value, str) \
                   and v.value in DATOS and id(v) not in dentro and id(v) not in seguro:
                    out.append((v.lineno, v.value))
    return sorted(set(out))


if __name__ == "__main__":
    tot = 0
    for f in UI:
        hits = revisa(f)
        if hits:
            print(f"\n── {f.name}")
            for ln, s in hits:
                print(f"   L{ln}: {s!r}")
            tot += len(hits)
    print(f"\n{tot} valores de dato pintados en crudo")
