"""GUARDIÁN v378 — el libro entra en la clave de caché, y las invalidaciones apuntan bien.

Dos cosas, y la segunda es la que más miedo da:

1. Todo lector cacheado de hoja de INQUILINO lleva `_libro` como primer parámetro.
   Sin él, `st.cache_data` —compartido por PROCESO— sirve al segundo cliente lo que
   memoizó el primero.
2. ⚠️ Todo `X.clear()` dentro de una invalidación apunta a una función REALMENTE
   decorada con `cache_data`. Si apunta al envoltorio, `.clear()` lanza
   AttributeError, el `except` se lo traga y **la caché deja de limpiarse sin que
   nadie se entere** — la regresión de v344, que vivió 4 versiones.
"""
import ast
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")

# ⚠️ Estas cinco NO se pueden derivar: leen con `get_all_records` sobre un worksheet
# ya resuelto, asi que en el AST no aparece el titulo de la hoja. Se quedan a mano y
# con su razon; las demas se DERIVAN (ver `_lee_solo_globales`).
GLOBALES_OK = {("auth.py", "_login_records_cached"), ("auth.py", "_group_records"),
               ("rails.py", "_records_cached"), ("rails.py", "_records"),
               ("manuals.py", "_drive_records")}


def _sheets_globales():
    """Los titulos de hoja GLOBAL, leidos de `timeclock.SHEETS_GLOBALES`.

    ⚠️ Se leen de ahi y no de una copia: una lista a mano en paralelo a la verdad es
    justo lo que dejo este guardian denunciando un modulo global como si fuera una
    fuga (v433/v434). Ojo: la constante esta en MINUSCULAS porque la comprobacion
    real es `.lower()`.
    """
    arbol = ast.parse((BASE / "timeclock.py").read_text(encoding="utf-8"))
    for n in ast.walk(arbol):
        if (isinstance(n, ast.Assign)
                and any(getattr(t_, "id", "") == "SHEETS_GLOBALES" for t_ in n.targets)):
            try:
                return {str(x).lower() for x in ast.literal_eval(n.value)}
            except Exception:
                return set()
    return set()


GLOBALES = _sheets_globales()


def _lee_solo_globales(fn, mod_consts):
    """La funcion lee UNICAMENTE hojas globales -> no puede haber fuga entre libros.

    Devuelve False si no se puede resolver ni una hoja: **no afirmar nada es mas
    seguro que eximir por no haber sabido mirar** (un falso negativo aqui es una fuga
    de datos entre empresas, que es lo que v378 vino a cerrar).
    """
    titulos = []
    for n in ast.walk(fn):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "registros" and n.args):
            continue
        a = n.args[0]
        if isinstance(a, ast.Constant) and isinstance(a.value, str):
            titulos.append(a.value)
        elif isinstance(a, ast.Name) and a.id in mod_consts:
            titulos.append(mod_consts[a.id])
        else:
            return False              # una hoja que no se pudo resolver
    return bool(titulos) and all(t_.lower() in GLOBALES for t_ in titulos)
ok = True

print("== 1. lectores cacheados de inquilino: ¿llevan el libro en la clave? ==")
sin_libro = []
for f in sorted(BASE.glob("*.py")):
    arbol = ast.parse(f.read_text(encoding="utf-8"))
    # constantes de MODULO que son cadenas: para resolver `registros(SHEET, ...)`
    _consts = {}
    for _n in arbol.body:
        if (isinstance(_n, ast.Assign) and isinstance(_n.value, ast.Constant)
                and isinstance(_n.value.value, str)):
            for _t in _n.targets:
                if isinstance(_t, ast.Name):
                    _consts[_t.id] = _n.value.value
    for n in ast.walk(arbol):
        if not isinstance(n, ast.FunctionDef):
            continue
        deco = " ".join(ast.unparse(d) for d in n.decorator_list)
        cuerpo = ast.unparse(n)
        if "cache_data" not in deco:
            continue
        if not any(p in cuerpo for p in ("hojas.registros", "get_all_records")):
            continue
        if (f.name, n.name) in GLOBALES_OK:
            continue
        if _lee_solo_globales(n, _consts):
            continue      # hoja GLOBAL: todas las sesiones leen el MISMO libro
        params = [a.arg for a in n.args.args]
        if not params or "libro" not in params[0].lower():
            sin_libro.append(f"{f.name}:{n.name}({', '.join(params)})  ← sin el libro")
        elif params[0].startswith("_"):
            # ⚠️ LA TRAMPA QUE HIZO INERTE EL PRIMER INTENTO: `st.cache_data` trata
            # los argumentos cuyo nombre empieza por guión bajo como NO HASHABLES y
            # **los deja fuera de la clave**. La firma decía lo correcto y la caché
            # seguía sin distinguir inquilinos. Solo lo delató instrumentar quién se
            # ejecutaba de verdad: el lector no corría en la segunda llamada.
            sin_libro.append(f"{f.name}:{n.name}({params[0]})  ← empieza por «_», "
                             "Streamlit lo EXCLUYE de la clave")
ok &= not sin_libro
print(f"   {'✓ todos' if not sin_libro else '‼️ LA CLAVE NO DISTINGUE EL LIBRO:'}")
for s in sin_libro:
    print(f"      {s}")

print("\n== 2. ⚠️ las invalidaciones apuntan a la función CACHEADA (trampa v344) ==")
malas = []
for f in sorted(BASE.glob("*.py")):
    src = f.read_text(encoding="utf-8")
    arbol = ast.parse(src)
    cacheadas = {n.name for n in ast.walk(arbol)
                 if isinstance(n, ast.FunctionDef)
                 and any("cache" in ast.unparse(d) for d in n.decorator_list)}
    planas = {n.name for n in ast.walk(arbol)
              if isinstance(n, ast.FunctionDef) and n.name not in cacheadas}
    for n in ast.walk(arbol):
        if not isinstance(n, ast.FunctionDef) or "invalidate" not in n.name:
            continue
        for c in ast.walk(n):
            # X.clear()
            if (isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                    and c.func.attr == "clear" and isinstance(c.func.value, ast.Name)):
                nom = c.func.value.id
                if nom in planas:
                    malas.append(f"{f.name}:{n.name} → {nom}.clear() pero {nom} NO está cacheada")
            # for fn in (X, Y): fn.clear()
            if isinstance(c, ast.Tuple):
                for el in c.elts:
                    if isinstance(el, ast.Name) and el.id in planas and el.id != "hojas":
                        malas.append(f"{f.name}:{n.name} → limpia {el.id}, que NO está cacheada")
ok &= not malas
print(f"   {'✓ todas apuntan a la cacheada' if not malas else '‼️ APUNTAN AL ENVOLTORIO:'}")
for m in malas:
    print(f"      {m}")

print("\n== 3. todos los módulos importan ==")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import importlib                                            # noqa: E402
fallos = []
for f in sorted(BASE.glob("*.py")):
    if f.name.startswith("__"):
        continue
    try:
        importlib.import_module(f"core.{f.stem}")
    except Exception as e:
        fallos.append(f"{f.name}: {type(e).__name__}: {e}")
ok &= not fallos
print(f"   {'✓ los ' + str(len(list(BASE.glob('*.py')))) + ' módulos importan' if not fallos else '‼️'}")
for x in fallos:
    print(f"      {x}")

print("\n" + ("✅ v378 OK: el libro está en la clave y las invalidaciones apuntan bien"
              if ok else "⚠️ REVISAR"))
sys.exit(0 if ok else 1)
