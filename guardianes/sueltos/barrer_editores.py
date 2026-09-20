# -*- coding: utf-8 -*-
"""⚠️ El TERCER sitio que v468 no reviso: el cuerpo que LEE el DataFrame editado.

v468 documento dos formas del fallo —11 claves de `column_config` renombradas sin la
fila, y 4 del caso contrario— pero no miro las LECTURAS del resultado. Y ahi no se
pierde el formato: `_ed.iloc[i]["Hours"]` sobre una fila cuya clave es "Horas" lanza
**KeyError** y la pantalla revienta. Lleva asi desde v468, invisible porque la demo
esta vacia.

Se buscan, por funcion, las claves que la fila DEFINE contra las que el codigo LEE.
"""
import ast
import io
import os


def claves_de(nodo):
    """Claves de cualquier dict literal dentro del nodo (filas o dict-de-columnas)."""
    out = set()
    for d in ast.walk(nodo):
        if isinstance(d, ast.Dict):
            for k in d.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    out.add(k.value)
    return out


hits = []
for f in sorted(os.listdir("core")):
    if not f.endswith(".py"):
        continue
    src = io.open("core/" + f, encoding="utf-8").read()
    a = ast.parse(src)
    for fn in [x for x in ast.walk(a) if isinstance(x, ast.FunctionDef)]:
        # 1) toda variable de esta funcion a la que se le asigna algo con dicts
        var = {}
        for nd in ast.walk(fn):
            if isinstance(nd, ast.Assign) and len(nd.targets) == 1 \
               and isinstance(nd.targets[0], ast.Name):
                k = claves_de(nd.value)
                if k:
                    var.setdefault(nd.targets[0].id, set()).update(k)
        # 2) el resultado del editor: `X = st.data_editor(algo, ...)`
        for nd in ast.walk(fn):
            if not (isinstance(nd, ast.Assign) and len(nd.targets) == 1
                    and isinstance(nd.targets[0], ast.Name)
                    and isinstance(nd.value, ast.Call)
                    and getattr(nd.value.func, "attr", "") in ("data_editor", "dataframe")):
                continue
            res = nd.targets[0].id
            filas = claves_de(nd.value)
            if nd.value.args:
                for x in ast.walk(nd.value.args[0]):
                    if isinstance(x, ast.Name) and x.id in var:
                        filas |= var[x.id]
            if not filas:
                continue
            # 3) lecturas por clave sobre ESE resultado
            for sub in ast.walk(fn):
                if not (isinstance(sub, ast.Subscript)
                        and isinstance(sub.slice, ast.Constant)
                        and isinstance(sub.slice.value, str)):
                    continue
                base = sub.value
                # `res["k"]`  o  `res.iloc[i]["k"]`
                nom = ""
                if isinstance(base, ast.Name):
                    nom = base.id
                elif isinstance(base, ast.Subscript) and isinstance(base.value, ast.Attribute) \
                        and isinstance(base.value.value, ast.Name):
                    nom = base.value.value.id
                if nom != res:
                    continue
                k = sub.slice.value
                if k not in filas:
                    hits.append("%s:%d  LEE %r de `%s` y la fila tiene %s"
                                % (f, sub.lineno, k, res, sorted(filas)))

print("LECTURAS por una clave que la fila NO tiene (KeyError): %d" % len(hits))
for h in sorted(set(hits)):
    print("   " + h)
