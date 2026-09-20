# -*- coding: utf-8 -*-
"""¿Que columna se pinta con su CLAVE cruda?

Una clave sin entrada en `tabla.CABECERAS` no basta para acusar: la tabla puede pasar
su propia etiqueta en el `extra` de `tabla.cfg(None, {...})`. Se mira lo uno Y lo otro,
o el barrido acusa columnas perfectamente etiquetadas (el error del medidor de v450).
"""
import ast
import io
import os
import re
import sys

sys.path.insert(0, ".")
from core import tabla  # noqa: E402

# una clave se ve en español si lleva acento o es una palabra española reconocible
ESP = re.compile(r"[áéíóúñÁÉÍÓÚÑ]|^(Fecha|Estado|Tipo|Cliente|Horas|Costo|Nombre|Grupo|"
                 r"Unidad|Clase|Vence|Fragmentos|Contacto|Avance|Persona|Concepto|"
                 r"Precio|Ganancia|Ganas|Cant|Peso|Actividad|Orden|Nota|Riel|Elevador|"
                 r"Margen|D.as|Inicio|Fin)")


def claves_de(nodo):
    out = set()
    for d in ast.walk(nodo):
        if isinstance(d, ast.Dict):
            for k in d.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    out.add(k.value)
    return out


crudas = []
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
            # etiquetas LOCALES: el `extra` que esta tabla pasa a `tabla.cfg`
            locales = set()
            for kw in n.keywords:
                if kw.arg != "column_config":
                    continue
                for d in ast.walk(kw.value):
                    if isinstance(d, ast.Dict):
                        for k, v in zip(d.keys, d.values):
                            if not (isinstance(k, ast.Constant)
                                    and isinstance(k.value, str)):
                                continue
                            # solo cuenta si la columna lleva LABEL (1er posicional)
                            tiene = isinstance(v, ast.Call) and v.args
                            if tiene:
                                locales.add(k.value)
            for k in sorted(filas):
                if k in tabla.CABECERAS or k in locales:
                    continue
                if ESP.search(k):
                    crudas.append("%s:%d  %r" % (f, n.lineno, k))

print("Columnas que se pintarian con su clave CRUDA y en español: %d" % len(crudas))
for c in sorted(set(crudas)):
    print("   " + c)
