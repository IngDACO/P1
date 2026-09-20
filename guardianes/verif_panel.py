"""Verificacion de la barra unificada del Panel (v291).

Chequeos de la casa: nombres libres (AST), uso-antes-de-asignar, keys sin
duplicar, y que no quede cabecera duplicada ni el caption huerfano.
"""
import sys, ast, re, pathlib
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

P = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\roster_ui.py")
src = P.read_text(encoding="utf-8")
arbol = ast.parse(src)
fn = next(n for n in arbol.body
          if isinstance(n, ast.FunctionDef) and n.name == "render_planificacion")

ok = True


def check(nombre, cond, extra=""):
    global ok
    ok = ok and cond
    print(f"  {'OK ' if cond else 'FALLO'}  {nombre}{(' -> ' + str(extra)) if extra else ''}")


# 1) nombres libres: todo lo usado debe estar definido (args, locales, globals, builtins)
globales = {n.name for n in arbol.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
for n in arbol.body:
    if isinstance(n, ast.Assign):
        globales |= {t.id for t in n.targets if isinstance(t, ast.Name)}
    if isinstance(n, (ast.Import, ast.ImportFrom)):
        globales |= {(a.asname or a.name.split(".")[0]) for a in n.names}
import builtins
locales = {a.arg for a in fn.args.args}
# ⚠️ Los argumentos de las lambdas anidadas SON locales suyos: sin esto salen como
# "libres" (falso positivo ya documentado en v138: `lambda o:` y `lambda d:`).
for nodo in ast.walk(fn):
    if isinstance(nodo, ast.Lambda):
        locales |= {a.arg for a in nodo.args.args}
usados = {}
for nodo in ast.walk(fn):
    if isinstance(nodo, ast.Name):
        if isinstance(nodo.ctx, ast.Store):
            locales.add(nodo.id)
        else:
            usados.setdefault(nodo.id, nodo.lineno)
    elif isinstance(nodo, (ast.comprehension,)):
        pass
libres = sorted(k for k in usados
                if k not in locales and k not in globales and not hasattr(builtins, k))
check("0 nombres libres", not libres, libres)

# 2) uso-antes-de-asignar para las variables de la barra
prim_asig, prim_uso = {}, {}
for nodo in ast.walk(fn):
    if isinstance(nodo, ast.Name):
        d = prim_asig if isinstance(nodo.ctx, ast.Store) else prim_uso
        d.setdefault(nodo.id, nodo.lineno)
        if isinstance(nodo.ctx, ast.Store):
            prim_asig[nodo.id] = min(prim_asig[nodo.id], nodo.lineno)
malos = [v for v in ("b1", "b2", "b3", "b4", "b5", "_vista", "lunes", "staff", "datos", "tidx")
         if v in prim_uso and v in prim_asig and prim_uso[v] < prim_asig[v]]
check("nada se usa antes de asignarse", not malos, malos)

# 3) keys de widget sin duplicar en TODO el modulo
keys = re.findall(r'key\s*=\s*[\'"]([^\'"]+)[\'"]', src)
dups = sorted({k for k in keys if keys.count(k) > 1})
check("keys de widget sin duplicar", not dups, dups)

# 4) las columnas de la barra se usan todas una vez
# ⚠️ v392 (CADUCADO, actualizado con la razón): esto exigía literalmente `b5`, o sea
# se ató a que la barra tuviera CINCO columnas. v392 la dejó en cuatro y bajó «Copiar
# semana anterior» a la fila de la cobertura, porque con TRES vistas el segmentado
# necesita ~330 px y en una ventana de 780 le tocaban 163 → se partía en vertical.
# Lo que v291 defiende NO es el número de columnas: es que el chrome entre los KPIs y
# el tablero no vuelva a ser cuatro bandas apiladas. Siguen siendo DOS filas (barra +
# cobertura), así que la regla se cumple. El número de columnas se DERIVA ahora de la
# propia línea, para que reordenar la barra no vuelva a dar un rojo por la forma.
_asig = re.search(r"\n\s*(b\d(?:\s*,\s*b\d)+)\s*=\s*st\.columns", src)
check("la barra sigue siendo UNA fila de columnas", bool(_asig))
_cols = [c.strip() for c in _asig.group(1).split(",")] if _asig else []
check("...con al menos 4 columnas", len(_cols) >= 4, True)
for b in _cols:
    check(f"columna {b} usada", len(re.findall(rf"\b{b}\.", src)) == 1)
# y el chrome no se ha vuelto a partir en bandas: la cobertura sigue compartiendo fila
check("la cobertura comparte fila (no es una banda suelta)",
      "_cc1, _cc2, _cc3 = st.columns(" in src)

# 5) ya NO hay cabecera propia ni caption huerfano
# ⚠️ Buscar la STRING pelada da falso positivo: mi propio comentario la menciona.
# Lo que importa es que no exista la LLAMADA que la pintaba.
_llamadas_md = [ast.get_source_segment(src, n) or "" for n in ast.walk(arbol)
                if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and n.func.attr in ("markdown", "header", "subheader", "title")]
check("ninguna llamada pinta 'Panel de personal'",
      not [c for c in _llamadas_md if "Panel de personal" in c])
check("sin el caption viejo", "para su ficha rápida." not in src)
# ⚠️ CADUCADO por v440 (i18n F3): el texto pasó al inglés a propósito.
check("el hint vive en el help del toggle",
      "help=" in src and ("ficha rápida" in src or "Quick view of this person" in src))

# 6) la vista se lee ANTES del if que la usa
ln_radio = src.index("_vista = b4.radio")
ln_if = src.index('if _vista == "👀 Disponibilidad"')
check("_vista se asigna antes del if", ln_radio < ln_if)

# 7) compila e importa de verdad
import py_compile
py_compile.compile(str(P), doraise=True)
import core.roster_ui as RU
check("compila + importa", callable(RU.render_planificacion))

# 8) bandas antes del tablero (lo que se queria reducir)
print("\n  bandas entre los KPIs y el tablero: 2 (barra + cobertura). Antes: 4.")
print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
