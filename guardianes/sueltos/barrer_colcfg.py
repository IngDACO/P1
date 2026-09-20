# -*- coding: utf-8 -*-
"""`column_config` que apunta a una columna que la fila NO tiene.

⚠️ `verif_v444` ya vigila esto y estaba VERDE con dos huerfanos delante en
`clientes_ui`: su `column_config` llega en una VARIABLE (`_colcfg`), no como dict
literal en la llamada. Es el mismo agujero del medidor de v450 — hay que resolver la
variable dentro de la funcion, no solo mirar lo que hay inline.

No es cosmetico: la columna pierde su formato. En `clientes_ui` la de dinero perdio su
`$%,d`, o sea que v468 reintrodujo ahi el fallo de v399.
"""
import ast
import io
import os
import sys

sys.path.insert(0, ".")
from core import tabla  # noqa: E402

GLOBAL = set(tabla.CABECERAS)


def claves_de(nodo):
    out = set()
    for d in ast.walk(nodo):
        if isinstance(d, ast.Dict):
            for k in d.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    out.add(k.value)
    return out


hits = []
for f in sorted(os.listdir("core")):
    if not f.endswith("_ui.py"):
        continue
    src = io.open("core/" + f, encoding="utf-8").read()
    a = ast.parse(src)
    for fn in [x for x in ast.walk(a) if isinstance(x, ast.FunctionDef)]:
        var = {}
        for nd in ast.walk(fn):
            if isinstance(nd, ast.Assign) and len(nd.targets) == 1 \
               and isinstance(nd.targets[0], ast.Name):
                k = claves_de(nd.value)
                if k:
                    var.setdefault(nd.targets[0].id, set()).update(k)
            # `_colcfg["X"] = ...`  tambien define una clave
            if isinstance(nd, ast.Assign) and len(nd.targets) == 1 \
               and isinstance(nd.targets[0], ast.Subscript) \
               and isinstance(nd.targets[0].value, ast.Name) \
               and isinstance(nd.targets[0].slice, ast.Constant):
                var.setdefault(nd.targets[0].value.id, set()).add(nd.targets[0].slice.value)
        for n in ast.walk(fn):
            if not (isinstance(n, ast.Call) and getattr(n.func, "attr", "") in
                    ("dataframe", "data_editor") and n.args):
                continue
            filas = claves_de(n.args[0])
            for x in ast.walk(n.args[0]):
                if isinstance(x, ast.Name) and x.id in var:
                    filas |= var[x.id]
            if not filas:
                continue
            cfg = set()
            for kw in n.keywords:
                if kw.arg != "column_config":
                    continue
                cfg |= claves_de(kw.value)
                for x in ast.walk(kw.value):
                    if isinstance(x, ast.Name) and x.id in var:
                        cfg |= var[x.id]
            # ⚠️ el mapa GLOBAL de `tabla.CABECERAS` no cuenta: cubre a proposito
            # claves que esta tabla no tiene.
            huerf = sorted(c for c in cfg - filas if c not in GLOBAL)
            if huerf:
                hits.append("%s:%d  column_config para %s, que la fila no tiene"
                            % (f, n.lineno, huerf))

print("column_config HUERFANOS: %d" % len(hits))
for h in sorted(set(hits)):
    print("   " + h)
