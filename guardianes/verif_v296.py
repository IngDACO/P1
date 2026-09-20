"""v296: verifica que borrar la shell VIEJA del admin no toco a los otros roles.

Lo critico: propietario y campo SIGUEN usando esa nav. Se reconstruye el `_nav`
de cada rol leyendo el AST de app.py y se compara con el commit anterior (git).
"""
import ast, pathlib, re, subprocess, sys

BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")
APP = BASE / "app.py"
src = APP.read_text(encoding="utf-8")

ok = True
def check(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"         esperado: {esp!r}")


def navs_de(texto):
    """{rol: [labels]} por AST, resolviendo _L_* y _HERR de verdad.

    ⚠️ La 1ª versión usaba regex y NO capturaba la rama del propietario (su línea
    acaba en `+ _HERR  # sin fichaje`, sin `]`), así que devolvía None y el test
    pasaba en vacío (None == None). Con AST se evalúa la expresión completa,
    incluidas las sumas de listas.
    """
    a = ast.parse(texto)
    consts = {}
    for n in ast.walk(a):
        if isinstance(n, ast.Assign) and len(n.targets) == 1 \
           and isinstance(n.targets[0], ast.Name) and isinstance(n.value, ast.Constant):
            consts[n.targets[0].id] = n.value.value

    def ev(nodo):
        if isinstance(nodo, ast.Name):
            v = consts.get(nodo.id, f"<{nodo.id}?>")
            return v if isinstance(v, list) else [v]
        if isinstance(nodo, ast.Constant):
            return [nodo.value]
        if isinstance(nodo, ast.List):
            return [x for e in nodo.elts for x in ev(e)]
        if isinstance(nodo, ast.BinOp) and isinstance(nodo.op, ast.Add):
            return ev(nodo.left) + ev(nodo.right)
        return ["<?>"]

    for n in ast.walk(a):
        if isinstance(n, ast.Assign) and len(n.targets) == 1 \
           and getattr(n.targets[0], "id", "") == "_HERR":
            consts["_HERR"] = ev(n.value)

    out = {}
    for n in ast.walk(a):
        if not isinstance(n, ast.If):
            continue
        t = n.test
        if (isinstance(t, ast.Compare) and isinstance(t.left, ast.Name)
                and t.left.id == "_ROL" and t.comparators
                and isinstance(t.comparators[0], ast.Constant)):
            for s in n.body:
                if isinstance(s, ast.Assign) and getattr(s.targets[0], "id", "") == "_nav":
                    out[t.comparators[0].value] = ev(s.value)
    return out


print("== navegacion por rol: AHORA vs el commit ANTERIOR ==")
prev = subprocess.run(["git", "show", "HEAD:survey_app/app.py"],
                      cwd=r"C:\Users\diego\P1", capture_output=True, text=True,
                      encoding="utf-8").stdout
antes, ahora = navs_de(prev), navs_de(src)
# ⚠️ GUARDA CONTRA EL PASO EN VACIO: si el parser no encuentra la nav de un rol,
# comparar None con None daria "OK" sin haber verificado NADA. Eso me paso.
# v384: v299 BORRÓ la nav vieja de `app.py`, así que ya no hay nada que leer ni
# que comparar: estas dos afirmaciones fallaban por haber ganado. Lo que queda
# vivo es que la nav vieja NO vuelva (regla v140/v146).
for rol in ("propietario", "campo"):
    check(f"{rol}: la nav vieja sigue borrada", not ahora.get(rol))
check("administrador: su rama ya no existe", "administrador" not in ahora)
print(f"         (antes tenia: {antes.get('administrador')})")

print("\n== restos del panel viejo ==")
check("_L_GRUPO fuera", "_L_GRUPO" not in src)
check("render_group_panel fuera del import", "render_group_panel" not in src)
au = (BASE / "core" / "auth_ui.py").read_text(encoding="utf-8")
check("render_group_panel borrada", "def render_group_panel" not in au)
tot = sum(f.read_text(encoding="utf-8").count("_gruposec_pending")
          for f in list((BASE / "core").glob("*.py")) + [APP])
check("_gruposec_pending sin restos", tot, 0)

print("\n== los deep-links siguen apuntando a la shell NUEVA ==")
for f in ("core/auth_ui.py", "core/roster_ui.py"):
    t = (BASE / f).read_text(encoding="utf-8")
    check(f"{f}: conserva _admin_nav_pending", "_admin_nav_pending" in t)

print("\n== todo compila e importa ==")
import py_compile, importlib
sys.path.insert(0, str(BASE))
mods = sorted((BASE / "core").glob("*.py"))
for p in mods:
    py_compile.compile(str(p), doraise=True)
py_compile.compile(str(APP), doraise=True)
malos = []
for p in mods:
    try:
        importlib.import_module("core." + p.stem)
    except Exception as e:
        malos.append((p.stem, repr(e)[:70]))
check(f"{len(mods)-len(malos)}/{len(mods)} modulos importan", malos, [])

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
