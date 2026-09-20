# -*- coding: utf-8 -*-
"""Cierra el hueco de `verif_v444`: cuando el `column_config` llega en una VARIABLE.

⚠️ v444 ya documenta que el chequeo «se aprobaba a si mismo» al contar su propio dict
como fila. Lo arreglo excluyendo el nodo `cc`… pero eso solo cubre el dict INLINE. Si
llega por variable (`_colcfg = {...}` y luego `tabla.cfg(None, _colcfg)`), ese dict
sigue viviendo en la funcion y sus claves entran en `filas` — el mismo autoengaño por
otra puerta. Por eso `verif_v444` estaba VERDE con dos huerfanos delante en
`clientes_ui`, uno de los cuales le costo a la columna de dinero su `$%,d`.
"""
import io
import os

p = os.environ["SCRW"] + "/verif_v444.py"
s = io.open(p, encoding="utf-8").read()

VIEJO = '''def _cc_dict(v):
    """El dict de `column_config`, venga literal o por `tabla.cfg(None, {...})`.

    ⚠️ v450 movió la configuración a `tabla.cfg`, que traduce la CABECERA sin tocar la
    clave. Sin resolverlo, un chequeo que solo entiende `ast.Dict` deja de mirar todas
    las tablas y devuelve 0 — que parece un aprobado y no lo es.
    """
    import ast as _a
    if isinstance(v, _a.Call) and getattr(v.func, "attr", "") == "cfg":
        v = v.args[1] if len(v.args) > 1 else None
    return v if isinstance(v, _a.Dict) else None'''

NUEVO = '''def _cc_dict(v, fn=None):
    """El dict de `column_config`, venga literal, por `tabla.cfg(None, {...})` o por
    una VARIABLE.

    ⚠️ v450 movió la configuración a `tabla.cfg`, que traduce la CABECERA sin tocar la
    clave. Sin resolverlo, un chequeo que solo entiende `ast.Dict` deja de mirar todas
    las tablas y devuelve 0 — que parece un aprobado y no lo es.

    ⚠️ v471: y si llega por VARIABLE (`_colcfg = {...}` → `tabla.cfg(None, _colcfg)`)
    hay que resolverla, por dos motivos. Uno, si no, esa tabla no se mira. Y dos, el
    grave: ese dict sigue viviendo en la función, así que sus claves entraban en
    `filas` y **el chequeo se aprobaba a sí mismo otra vez, por otra puerta** — estaba
    VERDE con dos huérfanas delante en `clientes_ui`, y una le costó a la columna de
    dinero su formato `$%,d` (o sea, reintrodujo el fallo de v399).
    """
    import ast as _a
    if isinstance(v, _a.Call) and getattr(v.func, "attr", "") == "cfg":
        v = v.args[1] if len(v.args) > 1 else None
    if isinstance(v, _a.Name) and fn is not None:
        # el ULTIMO valor asignado a esa variable dentro de la función
        for nd in _a.walk(fn):
            if isinstance(nd, _a.Assign) and len(nd.targets) == 1 \\
               and isinstance(nd.targets[0], _a.Name) \\
               and nd.targets[0].id == v.id and isinstance(nd.value, _a.Dict):
                return nd.value
        return None
    return v if isinstance(v, _a.Dict) else None'''

assert s.count(VIEJO) == 1, "ancla de _cc_dict ausente (%d)" % s.count(VIEJO)
s = s.replace(VIEJO, NUEVO)

# la llamada: ahora necesita la funcion contenedora, que se calcula mas abajo.
V2 = '''        cc = _cc_dict(cc)
        if cc is None:
            continue
        miradas += 1
        claves = {k.value for k in cc.keys
                  if isinstance(k, ast.Constant) and isinstance(k.value, str)}
        fn = _fn_de(tr, nd)
        if fn is None:
            continue'''
N2 = '''        fn = _fn_de(tr, nd)
        if fn is None:
            continue
        cc = _cc_dict(cc, fn)
        if cc is None:
            continue
        miradas += 1
        claves = {k.value for k in cc.keys
                  if isinstance(k, ast.Constant) and isinstance(k.value, str)}'''
assert s.count(V2) == 1, "ancla de la llamada ausente (%d)" % s.count(V2)
s = s.replace(V2, N2)

# ⚠️ Y `_colcfg["X"] = ...` tambien define claves del column_config: hay que
# excluirlas de `filas` igual que las del dict.
V3 = '''        _cc = {id(x) for x in ast.walk(cc)}'''
N3 = '''        _cc = {id(x) for x in ast.walk(cc)}
        # ⚠️ `_colcfg["Cost"] = ...` añade una clave al column_config, no a la fila:
        # sin esto volveria a contarse como columna existente.
        _cc_vars = {t_.value.id for t_ in
                    [x.targets[0] for x in ast.walk(fn)
                     if isinstance(x, ast.Assign) and len(x.targets) == 1]
                    if isinstance(t_, ast.Subscript) and isinstance(t_.value, ast.Name)}'''
assert s.count(V3) == 1, "ancla de _cc ausente"
s = s.replace(V3, N3)

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("verif_v444: resuelve el column_config por variable")
