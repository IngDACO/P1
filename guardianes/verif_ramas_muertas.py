"""⚠️ ¿Alguna rama quedó MUERTA al traducir la opción de un radio y no su comparación?

El fallo real (introducido en v441 y cazado por casualidad al leer un aviso de cambio):

    caso = st.radio("¿Qué riel se corta?",
                    ["Case 1 — first installed (the bottom one)",   ← traducida
                     "Case 2 — last installed (the top one)"])
    ...
    if caso.startswith("Caso 1"):                                    ← NO traducida
        …

`startswith` deja de casar **para siempre**, la rama no se ejecuta nunca y la herramienta
cae en silencio a la otra: ni error, ni traza, ni test rojo — solo un cálculo equivocado.
Es la regla de oro de toda la migración («traducir un DATO no da error, deja de casar»)
mordiendo desde el lado del que traduce.

⚠️ Dos versiones anteriores de este guardián dieron **0 con la rama muerta delante**:
  1. contando el texto del fichero → un comentario mío («# CASO 1») hacía creer que el
     valor existía. Es la trampa nº2 (grep ≠ uso) DENTRO del guardián.
  2. preguntando «¿lo produce alguien en el repo?» → `'Caso 1 · A '`, una etiqueta del
     PDF, casaba como prefijo. Demasiado laxo.
La afirmación correcta es LOCAL y concreta: lo que se compara tiene que salir de las
OPCIONES de ese mismo widget.
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
WIDGETS = {"radio", "selectbox", "select_slider", "segmented_control", "pills"}


def _consts(tr):
    """Constantes de cadena asignadas a un nombre (`_C1 = "Case 1 …"`).

    ⚠️ Hace falta porque el propio arreglo de la rama muerta puso las opciones en
    constantes — y sin resolverlas el guardián dejaba de ver ese widget: mi corrección
    habría CEGADO al chequeo que la encontró. Un guardián que solo entiende literales
    deja de mirar justo el código que se ha hecho más robusto.
    """
    out = {}
    for n_ in ast.walk(tr):
        if isinstance(n_, ast.Assign) and isinstance(n_.value, ast.Constant)            and isinstance(n_.value.value, str):
            for tg in n_.targets:
                if isinstance(tg, ast.Name):
                    out[tg.id] = n_.value.value
    return out


def _dicts(tr):
    """Dicts de cadena→cadena asignados a un nombre (`_PER = {"Este mes": "This month"}`).

    ⚠️ Segunda vez que el propio arreglo ciega al guardián (v450): al pasar las
    opciones a `format_func` se escriben como `list(_PER)`, y un chequeo que solo
    entiende listas literales deja de mirar ESE widget — justo el que se acaba de
    tocar. Probado: sin esto, traducir la clave de `_PER` (la opción que se compara)
    pasaba en verde con la rama muerta delante.
    """
    out = {}
    for n_ in ast.walk(tr):
        if isinstance(n_, ast.Assign) and isinstance(n_.value, ast.Dict):
            claves = [k.value for k in n_.value.keys
                      if isinstance(k, ast.Constant) and isinstance(k.value, str)]
            if claves and len(claves) == len(n_.value.keys):
                for tg in n_.targets:
                    if isinstance(tg, ast.Name):
                        out[tg.id] = claves
    return out


def _opciones(call, consts, dicts=None):
    """Las opciones de un widget: literales, constantes locales o `list(DICT)`."""
    cand = list(call.args[1:2]) + [k.value for k in call.keywords if k.arg == "options"]
    for a in cand:
        # `list(_PER)` / `list(_PER.keys())` → las CLAVES, que son las opciones reales
        if isinstance(a, ast.Call) and getattr(a.func, "id", "") == "list" and a.args:
            base = a.args[0]
            nom = getattr(base, "id", None) or getattr(getattr(base, "value", None), "id", None)
            if nom and (dicts or {}).get(nom):
                return list(dicts[nom])
        if isinstance(a, (ast.List, ast.Tuple)):
            ops = []
            for e in a.elts:
                if isinstance(e, ast.Constant) and isinstance(e.value, str):
                    ops.append(e.value)
                elif isinstance(e, ast.Name) and e.id in consts:
                    ops.append(consts[e.id])
            # solo sirve si se resolvieron TODAS: con una sin resolver no se puede afirmar
            if ops and len(ops) == len(a.elts):
                return ops
    return None


def _fn_de(tr, nodo):
    """La función que contiene un nodo (para acotar el ámbito de la variable)."""
    for f in ast.walk(tr):
        if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for x in ast.walk(f):
                if x is nodo:
                    return f
    return None


muertas = 0
mirados = 0
for f in sorted(RAIZ.rglob("*.py")):
    try:
        tr = ast.parse(f.read_text(encoding="utf-8"))
    except Exception:
        continue
    # variable ← widget con opciones literales
    _CT = _consts(tr)
    _DC = _dicts(tr)
    ligadas = {}
    for n in ast.walk(tr):
        if not (isinstance(n, ast.Assign) and isinstance(n.value, ast.Call)):
            continue
        c = n.value
        if getattr(c.func, "attr", "") not in WIDGETS:
            continue
        ops = _opciones(c, _CT, _DC)
        if not ops:
            continue
        for tg in n.targets:
            if isinstance(tg, ast.Name):
                ligadas[tg.id] = (ops, _fn_de(tr, n), n.lineno)

    for var, (ops, fn, ln0) in ligadas.items():
        ambito = fn if fn is not None else tr
        for n in ast.walk(ambito):
            usos = []
            if isinstance(n, ast.Compare) and isinstance(n.left, ast.Name) \
               and n.left.id == var:
                for x in n.comparators:
                    if isinstance(x, ast.Constant) and isinstance(x.value, str):
                        usos.append(("==", x.value, n.lineno))
                    if isinstance(x, (ast.List, ast.Tuple, ast.Set)):
                        for e in x.elts:
                            if isinstance(e, ast.Constant) and isinstance(e.value, str):
                                usos.append(("in", e.value, n.lineno))
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
               and n.func.attr in ("startswith", "endswith") \
               and isinstance(n.func.value, ast.Name) and n.func.value.id == var \
               and n.args and isinstance(n.args[0], ast.Constant):
                usos.append((n.func.attr, n.args[0].value, n.lineno))
            for modo, val, ln in usos:
                mirados += 1
                if modo == "startswith":
                    ok = any(o.startswith(val) for o in ops)
                elif modo == "endswith":
                    ok = any(o.endswith(val) for o in ops)
                else:
                    ok = val in ops
                if not ok:
                    muertas += 1
                    print(f"  ⚠️ RAMA MUERTA  {f.name}:{ln}  `{var}.{modo}({val!r})`")
                    print(f"                  opciones del widget (L{ln0}): {ops}")

print(f"\n{mirados} comparaciones contra opciones de un widget · {muertas} MUERTAS")
if not mirados:
    print("⚠️ el chequeo no miró nada: eso NO es un aprobado")
sys.exit(1 if (muertas or not mirados) else 0)
