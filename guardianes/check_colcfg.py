# -*- coding: utf-8 -*-
"""¿Alguna `column_config` apunta a una columna que ya no existe?

Es el modo de fallo de traducir cabeceras de tabla: se cambia la clave de la fila y
se olvida la del `column_config` (o al revés). Streamlit **no da error**: la columna
simplemente pierde su formato, su ancho y su etiqueta, y la tabla se descoloca.
Mismo patrón que `Duración (d)` o `Elevador`: media traducción no falla, deja de casar.

⚠️ Se cuenta cuántas se miraron: un «0 huérfanas» sobre 0 tablas no es un aprobado.
"""


def _cc_dict(v):
    """El dict de `column_config`, venga literal o por `tabla.cfg(None, {...})`.

    ⚠️ CADUCADO en v450 y actualizado, no relajado: la configuración se movió a
    `tabla.cfg`, que traduce la CABECERA sin tocar la clave. Sin resolverlo, este
    chequeo dejaba de mirar las 66 tablas y avisaba de que «apenas miró nada» —
    que es justo lo que tiene que hacer, pero por el motivo equivocado.
    """
    if isinstance(v, ast.Call) and getattr(v.func, "attr", "") == "cfg":
        v = v.args[1] if len(v.args) > 1 else None
    return v if isinstance(v, ast.Dict) else None

import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")


def _fn_de(tr, nodo):
    for c in ast.walk(tr):
        if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for x in ast.walk(c):
                if x is nodo:
                    return c
    return None


malos, miradas = [], 0
for f in sorted(list((RAIZ / "core").glob("*_ui.py")) + [RAIZ / "app.py"]):
    tr = ast.parse(f.read_text(encoding="utf-8"))
    for n in ast.walk(tr):
        if not (isinstance(n, ast.Call)
                and getattr(n.func, "attr", "") in ("dataframe", "data_editor")):
            continue
        cc = _cc_dict(next((k.value for k in n.keywords if k.arg == "column_config"), None))
        if cc is None:
            continue
        miradas += 1
        claves = {k.value for k in cc.keys
                  if isinstance(k, ast.Constant) and isinstance(k.value, str)}
        fn = _fn_de(tr, n)
        if fn is None:
            continue
        # ⚠️ El ámbito es la FUNCIÓN, no el fichero: dos tablas distintas del mismo
        # módulo pueden tener columnas distintas, y mirar todo el fichero daría un
        # aprobado en falso (la clave existiría, pero en otra tabla).
        # ⚠️⚠️ Y hay que EXCLUIR el propio `column_config`: su dict también está
        # dentro de la función, así que contándolo el chequeo SE APROBABA A SÍ MISMO
        # y la resta salía vacía siempre. Con la mitad de la traducción rota delante
        # seguía diciendo «0 huérfanas» — lo destapó probarlo contra código roto.
        _cc_ids = {id(x) for x in ast.walk(cc)}
        filas = {k.value for d in ast.walk(fn) if isinstance(d, ast.Dict)
                 and id(d) not in _cc_ids
                 for k in d.keys
                 if isinstance(k, ast.Constant) and isinstance(k.value, str)}
        huerf = claves - filas - {"_index"}
        if huerf:
            malos.append(f"{f.name}:{n.lineno} {sorted(huerf)}")

for m in malos:
    print(f"  ⚠️ column_config sin fila que la respalde: {m}")
print(f"\n{miradas} tablas con column_config miradas · {len(malos)} huérfanas")
if miradas < 5:
    print("⚠️ el chequeo apenas miró nada: eso NO es un aprobado")
sys.exit(1 if (malos or miradas < 5) else 0)
