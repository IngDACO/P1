"""La forma exacta de cada lector cacheado de inquilino + su `_invalidate`.

Sin esto no se puede parchear: hay al menos tres formas distintas (sin parámetros,
con `title`, y las de `timeclock`/`roster`), y el `_invalidate` de cada módulo
limpia por nombre — si el nombre cambia y el `except` se lo traga, la caché deja de
limpiarse y nadie se entera (la regresión de v344).
"""
import ast
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")

# Los que leen hojas GLOBALES no tienen fuga: su libro es siempre el maestro.
GLOBALES = {("auth.py", "_login_records_cached"), ("auth.py", "_group_records"),
            ("rails.py", "_records"), ("manuals.py", "_drive_records")}

for f in sorted(BASE.glob("*.py")):
    try:
        src = f.read_text(encoding="utf-8")
        arbol = ast.parse(src)
    except Exception:
        continue
    lineas = src.splitlines()
    objetivo = []
    for n in ast.walk(arbol):
        if not isinstance(n, ast.FunctionDef):
            continue
        deco = " ".join(ast.unparse(d) for d in n.decorator_list)
        cuerpo = ast.unparse(n)
        es_lector = ("cache_data" in deco
                     and any(p in cuerpo for p in ("hojas.registros", "get_all_records")))
        if es_lector and (f.name, n.name) not in GLOBALES:
            objetivo.append(n)
        if n.name in ("_invalidate", "_invalidate_records", "_invalidate_login"):
            objetivo.append(n)
    if not objetivo:
        continue
    print("=" * 70)
    print(f"### {f.name}")
    print("=" * 70)
    for n in sorted(objetivo, key=lambda x: x.lineno):
        ini = min([d.lineno for d in n.decorator_list] + [n.lineno]) - 1
        fin = n.end_lineno
        # sin los docstrings largos: interesa la MECÁNICA
        cuerpo = [l for l in lineas[ini:fin]]
        if len(cuerpo) > 16:
            cuerpo = cuerpo[:8] + ["        ...", ] + cuerpo[-6:]
        print("\n".join(cuerpo))
        print("-" * 40)
