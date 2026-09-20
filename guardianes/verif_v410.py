"""v410: la rejilla del Panel no puede desaparecer en silencio.

El CSS de la rejilla cuelga de que la cabecera y las filas se dibujen DENTRO de dos
contenedores con key (`roshead` y `rosgrid`). Si alguien devuelve esas columnas a
`st.columns(...)` —lo natural al editar—, el selector deja de casar y **la rejilla se
va sin que nada falle**: la app se ve «casi bien» y nadie lo nota. Es el modo de fallo
de v304 (el CSS del menú caducado) y v332 (`stMain` es un `<section>`).

Se afirma sobre el PRINCIPIO, no sobre los colores ni los píxeles (regla v392): que las
columnas del tablero cuelguen de los contenedores keyed, y que el CSS traiga sus reglas
y la exclusión de lo que va DENTRO de una celda.
"""
import ast
import io
import sys
import tokenize
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
F = Path(r"C:\Users\diego\P1\survey_app\core\roster_ui.py")

ok = True


def chk(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"           esperado: {esp!r}")


src = F.read_text(encoding="utf-8")
# ⚠️ Sin comentarios: los míos nombran `rosgrid`/`st.columns` y un grep los contaría
# como uso (trampa nº2, que ya ha mordido seis veces en este repo).
sin_com = tokenize.untokenize(
    [t for t in tokenize.generate_tokens(io.StringIO(src).readline)
     if t.type != tokenize.COMMENT])
arb = ast.parse(sin_com)
f = next((n for n in ast.walk(arb)
          if isinstance(n, ast.FunctionDef) and n.name == "_tablero_editable"), None)
chk("existe `_tablero_editable`", f is not None)

# ── 1) Los contenedores existen y con las keys que usa el CSS ────────────────
keys = set()
for n in ast.walk(f):
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
            and n.func.attr == "container":
        for kw in n.keywords:
            if kw.arg == "key" and isinstance(kw.value, ast.Constant):
                keys.add(kw.value.value)
chk("se crea el contenedor `roshead`", "roshead" in keys)
chk("se crea el contenedor `rosgrid`", "rosgrid" in keys)

# ── 2) Las columnas del TABLERO cuelgan de ellos, no de `st` ─────────────────
# Las que están dentro del popover (la franja horaria) SÍ pueden ser `st.columns`:
# van dentro de la celda y el CSS las excluye a propósito.
def dentro_de_popover(nodo, fn):
    """¿El nodo cae dentro de un `with ....popover(...)`?"""
    pila = [(fn, [])]
    while pila:
        cur, ancestros = pila.pop()
        for hijo in ast.iter_child_nodes(cur):
            camino = ancestros + [cur]
            if hijo is nodo:
                return any(isinstance(a, ast.With) and any(
                    isinstance(it.context_expr, ast.Call)
                    and isinstance(it.context_expr.func, ast.Attribute)
                    and it.context_expr.func.attr == "popover"
                    for it in a.items) for a in camino)
            pila.append((hijo, camino))
    return False


fuera, dentro = [], []
for n in ast.walk(f):
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
            and n.func.attr == "columns":
        base = getattr(n.func.value, "id", "?")
        (dentro if dentro_de_popover(n, f) else fuera).append((n.lineno, base))

print(f"         columnas del tablero: {fuera}")
print(f"         columnas dentro de la celda (excluidas a propósito): {dentro}")
chk("hay columnas de tablero que auditar (si no, el chequeo pasa en vacío)",
    len(fuera) >= 2)
# ⚠️ ACTUALIZADO en v411 (regla v385: caducado, no relajado — con la razón al lado).
# Antes se exigía literalmente `_head`/`_grid`. v411 añadió un contenedor POR FILA
# (`_row`, con key `rosrow_…`) para poder pintar la franja alterna por key, así que las
# columnas de las filas ya no cuelgan de `_grid` sino de `_row`. Lo que la regla protege
# NO es el nombre de la variable: es que **ninguna columna del tablero cuelgue de `st`
# directamente**, porque entonces cae fuera de los contenedores keyed y la rejilla, la
# zebra y la columna de hoy se van sin que nada falle.
chk("...y TODAS cuelgan de un contenedor keyed, ninguna de `st`",
    all(b in ("_head", "_grid", "_row") for _, b in fuera))

# ── 3) El CSS trae sus reglas ───────────────────────────────────────────────
# Se mira el literal del `st.markdown` de estilos, no el fichero entero, para que un
# comentario que mencione `.st-key-rosgrid` no dé un OK falso.
css = "".join(n.value for n in ast.walk(f)
              if isinstance(n, ast.Constant) and isinstance(n.value, str)
              and "st-key-" in n.value)
for regla in (".st-key-rosgrid", ".st-key-roshead"):
    chk(f"el CSS estila `{regla}`", regla in css)
chk("la fila lleva borde inferior forzado (sin `!important` no gana: medido)",
    "border-bottom: 1px solid #e6eaf0 !important" in css)
chk("los días llevan línea vertical", "border-right: 1px solid #dfe5ec" in css)
chk("la última columna no cierra la tabla por fuera",
    ':last-child { border-right: none; }' in css or ":last-child" in css)
# ⚠️ Se comprueba el SELECTOR COMPLETO, no dos subcadenas sueltas. La primera versión
# miraba `'st-key-roscel_' in css and 'border: none !important' in css` y daba OK
# CON LA EXCLUSIÓN BORRADA: las dos existen por otros motivos (el CSS de densidad
# estila `[class*="st-key-roscel_"] button`, y el de `pnm_` ya trae
# `border: none !important`). Lo delató probar el guardián contra el código roto —
# sin esa prueba, habría quedado un chequeo que solo aprueba.
_EXCL = '.st-key-rosgrid [class*="st-key-roscel_"] [data-testid="stHorizontalBlock"]'
chk("lo de DENTRO de una celda queda excluido de la rejilla", _EXCL in css)

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
