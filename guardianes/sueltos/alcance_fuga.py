"""¿Cuántos lectores cacheados NO distinguen el libro? (alcance de la fuga)

Un lector es vulnerable si: está decorado con `st.cache_data`, lee una hoja
(por `hojas.registros` o `get_all_records`) y **ninguno de sus parámetros
identifica el libro o el grupo**. En ese caso la clave de caché no distingue
inquilinos y el segundo cliente recibe lo del primero.
"""
import ast
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")

PISTAS_LECTURA = ("hojas.registros", "get_all_records", "values_batch_get", "get_all_values")
PISTAS_LIBRO = ("libro", "sheet_id", "sheetid", "grupo", "group")

vulnerables, seguros = [], []
for f in sorted(BASE.glob("*.py")):
    try:
        arbol = ast.parse(f.read_text(encoding="utf-8"))
    except Exception:
        continue
    for n in ast.walk(arbol):
        if not isinstance(n, ast.FunctionDef):
            continue
        deco = " ".join(ast.unparse(d) for d in n.decorator_list)
        if "cache_data" not in deco and "cache_resource" not in deco:
            continue
        cuerpo = ast.unparse(n)
        if not any(p in cuerpo for p in PISTAS_LECTURA):
            continue
        params = [a.arg for a in n.args.args]
        tiene = any(any(p in a.lower() for p in PISTAS_LIBRO) for a in params)
        fila = (f.name, n.name, params, "cache_resource" if "cache_resource" in deco else "cache_data")
        (seguros if tiene else vulnerables).append(fila)

print("== ⚠️ LECTORES CACHEADOS QUE NO DISTINGUEN EL LIBRO ==")
for mod, fn, params, tipo in vulnerables:
    print(f"   {mod:<20} {fn:<26} ({', '.join(params) or 'sin parámetros'})   [{tipo}]")
print(f"\n   {len(vulnerables)} vulnerables")

print("\n== los que SÍ llevan el libro o el grupo en la clave ==")
for mod, fn, params, tipo in seguros:
    print(f"   {mod:<20} {fn:<26} ({', '.join(params)})   [{tipo}]")
print(f"\n   {len(seguros)} seguros")

print("\n== módulos afectados ==")
mods = sorted({m for m, _f, _p, _t in vulnerables})
print("   " + ", ".join(mods))
print(f"   {len(mods)} módulos")
