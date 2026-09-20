"""Guardianes v323 — helpers unificados, IDs frescos y silencios rotos.

Lo que protege, y por qué cada uno estaba mal:
1. `num()` — las 5 variantes de `_num` devolvían **0.0** ante un separador de
   miles (`1,234.56`). Y lo más importante: NO puede cambiar lo que la app
   escribe hoy (float plano), así que se compara contra las variantes viejas.
2. `parse_date()` — `invoices`/`inventory` solo aceptaban ISO; una fecha
   `16/08/2026` se leía `None` y esa factura caía fuera del P&L.
3. `_next_id` no puede leer de la caché (120 s desde v290) o repite un ID, y el
   ID es la identidad de todo.
4. Ningún `except` mudo puede tragarse una ESCRITURA.
5. `notify_expiring` corre en cada login de admin: 0 escrituras dentro del bucle.
"""
import ast
import importlib
import pathlib
import py_compile
import random
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(BASE))
OK = True


def _fuentes():
    for p in sorted(BASE.rglob("*.py")):
        if "scratchpad" not in str(p):
            yield p


print("== 1) compila e importa ==")
mods = sorted((BASE / "core").glob("*.py"))
for p in mods:
    py_compile.compile(str(p), doraise=True)
py_compile.compile(str(BASE / "app.py"), doraise=True)
fallos = []
for p in mods:
    try:
        importlib.import_module("core." + p.stem)
    except Exception as e:
        fallos.append((p.stem, repr(e)[:90]))
print(f"   {len(mods) - len(fallos)}/{len(mods)} módulos + app.py")
for f in fallos:
    print("    FALLO", f)
OK &= not fallos

from core.num import col_letter, num, parse_date          # noqa: E402

print("\n== 2) num(): el separador de miles ya no vale $0 ==")
CASOS = [("1234.56", 1234.56), ("1,234.56", 1234.56), ("$1,234.56", 1234.56),
         ("1234,56", 1234.56), ("1.234,56", 1234.56), ("1,234", 1234.0),
         ("-1,234.56", -1234.56), ("1,234,567.89", 1234567.89),
         ("1.234", 1.234),          # solo punto → decimal (lo que escribe la app)
         ("37.75", 37.75), ("8.97", 8.97), ("  42 ", 42.0), ("$0.00", 0.0),
         ("", 0.0), (None, 0.0), ("abc", 0.0), (0, 0.0), (3, 3.0), (2.5, 2.5),
         (True, 0.0)]               # bool ES int en Python: no debe colarse
mal = [c for c, e in CASOS if abs(num(c) - e) > 1e-9]
print(f"   {len(CASOS)} casos · fallan: {len(mal)} {mal}")
OK &= not mal

print("\n== 3) …y NO cambia ni un número de los que la app ya escribió ==")
random.seed(7)
difs = 0
for _ in range(5000):
    v = str(round(random.uniform(-99999, 99999), 2))
    if abs(num(v) - float(v)) > 1e-9:                 # variante `float(v)`
        difs += 1
    if abs(num(v) - float(v.replace(",", "."))) > 1e-9:   # la variante de ×9
        difs += 1
print(f"   5000 importes en formato de la app · diferencias: {difs}")
OK &= (difs == 0)

print("\n== 4) parse_date() acepta lo que invoices/inventory tiraban ==")
FECHAS = [("2026-08-16", "2026-08-16"), ("16/08/2026", "2026-08-16"),
          ("16-08-2026", "2026-08-16"), ("2026/08/16", "2026-08-16"),
          ("2026-08-16 09:30", "2026-08-16"), ("", "None"), ("basura", "None")]
mal = [f for f, e in FECHAS if str(parse_date(f)) != e]
print(f"   {len(FECHAS)} casos · fallan: {len(mal)} {mal}")
OK &= not mal

print("\n== 5) col_letter() pasa de la columna Z (las hojas tienen 20-30) ==")
mal = [n for n, e in [(1, "A"), (26, "Z"), (27, "AA"), (30, "AD"), (52, "AZ")]
       if col_letter(n) != e]
print(f"   fallan: {len(mal)} {mal}")
OK &= not mal

print("\n== 6) no vuelve a haber copias locales divergentes ==")
copias = []
for p in _fuentes():
    if p.name == "num.py":
        continue
    a = ast.parse(p.read_text(encoding="utf-8"))
    for n in ast.walk(a):
        if isinstance(n, ast.FunctionDef) and n.name in ("_num", "_parse_date", "_col_letter"):
            copias.append(f"{p.name}:{n.lineno} {n.name}")
print(f"   definiciones locales: {len(copias)} {copias}")
OK &= not copias

print("\n== 7) …y donde se usan, están importadas ==")
falta = []
for p in _fuentes():
    a = ast.parse(p.read_text(encoding="utf-8"))
    usa = {n.func.id for n in ast.walk(a) if isinstance(n, ast.Call)
           and isinstance(n.func, ast.Name)
           and n.func.id in ("_num", "_parse_date", "_col_letter")}
    if not usa:
        continue
    imp = set()
    for n in ast.walk(a):
        if isinstance(n, ast.ImportFrom) and n.module == "core.num":
            imp |= {(x.asname or x.name) for x in n.names}
    if usa - imp:
        falta.append(f"{p.name}: {sorted(usa - imp)}")
print(f"   sin importar: {len(falta)} {falta}")
OK &= not falta

print("\n== 8) _next_id NUNCA lee de la caché (repetiría un ID) ==")
cache = []
for p in _fuentes():
    a = ast.parse(p.read_text(encoding="utf-8"))
    for n in a.body:
        if isinstance(n, ast.FunctionDef) and n.name == "_next_id":
            # ⚠️ Por AST y por NOMBRE EXACTO de la llamada. Buscar la subcadena
            # `_records(` marcaba `w.get_all_records(...)` —que es justo la lectura
            # FRESCA que se quiere— y acusaba a `catalogo` y `orders` de un fallo
            # que no tenían. Es la trampa nº2 del proyecto: grep ≠ uso.
            llama_cache = any(
                isinstance(c, ast.Call)
                and (getattr(c.func, "id", None) in ("_records", "_fichaje_records")
                     or getattr(c.func, "attr", None) in ("_records", "_fichaje_records"))
                for c in ast.walk(n))
            if llama_cache:
                cache.append(p.name)
print(f"   usan _records(): {len(cache)} {cache}")
OK &= not cache

print("\n== 9) ningún `except` mudo se traga una ESCRITURA ==")
ESCR = {"update_cell", "append_row", "append_rows", "batch_update", "delete_rows",
        "insert_row", "update_project", "add_document", "update", "upload",
        "upload_to", "add_worksheet", "create_project", "save_activities",
        "set_archivado", "registrar", "submit"}
graves = []
for p in _fuentes():
    a = ast.parse(p.read_text(encoding="utf-8"))
    for t in ast.walk(a):
        if not isinstance(t, ast.Try):
            continue
        if not any(len(h.body) == 1 and isinstance(h.body[0], (ast.Pass, ast.Continue))
                   for h in t.handlers):
            continue
        for c in ast.walk(t):
            if isinstance(c, ast.Call):
                nm = (c.func.attr if isinstance(c.func, ast.Attribute)
                      else getattr(c.func, "id", ""))
                if nm in ESCR:
                    graves.append(f"{p.name}:{t.lineno} {nm}")
                    break
print(f"   quedan: {len(graves)} {graves}")
OK &= not graves

print("\n== 10) notify_expiring (cada login de admin): 0 escrituras en bucle ==")
HOT = {"update_cell", "append_row", "append_rows", "delete_rows", "insert_row"}
enbucle = []
for p in _fuentes():
    a = ast.parse(p.read_text(encoding="utf-8"))
    for fn in [x for x in ast.walk(a) if isinstance(x, ast.FunctionDef)]:
        if fn.name != "notify_expiring":
            continue
        for b in ast.walk(fn):
            if isinstance(b, (ast.For, ast.While)):
                for c in ast.walk(b):
                    if isinstance(c, ast.Call):
                        nm = c.func.attr if isinstance(c.func, ast.Attribute) else ""
                        if nm in HOT:
                            enbucle.append(f"{p.name}::{fn.name} {nm} L{c.lineno}")
print(f"   escrituras dentro del bucle: {len(enbucle)} {enbucle}")
OK &= not enbucle

print("\n" + ("TODO OK" if OK else "HAY FALLOS"))
sys.exit(0 if OK else 1)
