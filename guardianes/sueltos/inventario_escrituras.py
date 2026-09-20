"""Inventario de TODO lo que escribe en la app, y quién lo ha ejercitado.

Sin esto, «probar todas las funciones» es una intención: no se sabe cuántas son ni
cuáles se han tocado. Aquí sale el número, por AST y no por grep (un nombre en un
comentario no es un uso — trampa nº2).

Una función ESCRIBE si llama, directa o transitivamente, a algo que toca Sheets o
Drive: `append_row(s)`, `update`, `update_cell`, `batch_update`, `delete_rows`,
`clear`, o `drive_store.upload/upload_to/delete`.

Y se considera EJERCITADA si algún script del scratchpad la llama de verdad — otra
vez por AST, y sin contar el fichero que la define.
"""
import ast
import io
import pathlib
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CORE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")
APP = pathlib.Path(r"C:\Users\diego\P1\survey_app\app.py")
SCRATCH = pathlib.Path(__file__).parent

PRIMITIVAS = {"append_row", "append_rows", "update_cell", "batch_update",
              "delete_rows", "update_cells", "add_worksheet", "resize",
              "values_update", "values_append", "values_batch_clear"}
DRIVE = {"upload", "upload_to", "delete"}

# ── 1) todas las funciones del core, con lo que llaman ───────────────────────
llama = defaultdict(set)        # "modulo.func" -> {nombres llamados}
escribe_directo = set()
publicas = {}


def _nombre_llamada(n):
    f = n.func
    if isinstance(f, ast.Attribute):
        return f.attr
    if isinstance(f, ast.Name):
        return f.id
    return ""


for p in sorted(CORE.glob("*.py")) + [APP]:
    mod = p.stem
    try:
        arb = ast.parse(io.open(p, encoding="utf-8").read())
    except Exception as e:                                        # noqa: BLE001
        print(f"  (no se pudo leer {p.name}: {e})")
        continue
    for fn in [n for n in ast.walk(arb) if isinstance(n, ast.FunctionDef)]:
        clave = f"{mod}.{fn.name}"
        publicas[clave] = not fn.name.startswith("_")
        for c in [n for n in ast.walk(fn) if isinstance(n, ast.Call)]:
            nom = _nombre_llamada(c)
            if not nom:
                continue
            llama[clave].add(nom)
            if nom in PRIMITIVAS:
                escribe_directo.add(clave)
            if nom in DRIVE and isinstance(c.func, ast.Attribute):
                base = getattr(c.func.value, "id", "") or getattr(c.func.value, "attr", "")
                if "drive" in str(base).lower():
                    escribe_directo.add(clave)

# ── 2) propagación: quien llama a un escritor, escribe ───────────────────────
por_nombre = defaultdict(set)
for clave in llama:
    por_nombre[clave.split(".", 1)[1]].add(clave)

escriben = set(escribe_directo)
for _ in range(12):                       # punto fijo; 12 sobra para esta profundidad
    nuevos = set()
    for clave, llamadas in llama.items():
        if clave in escriben:
            continue
        for nom in llamadas:
            if any(c in escriben for c in por_nombre.get(nom, ())):
                nuevos.add(clave)
                break
    if not nuevos:
        break
    escriben |= nuevos

pub_escriben = sorted(c for c in escriben if publicas.get(c))

# ⚠️ El número bruto engaña: la propagación marca como «escribe» a CUALQUIER lector,
# porque `get_sheet` migra la cabecera al acceder (regla v145). Es cierto, pero no es
# lo que hay que ejercitar. Tres cubos distintos:
#   · MUTADOR   — llama directo a append/update/batch/Drive. Esta es la superficie real.
#   · PANTALLA  — un `render_*` de un módulo `_ui`: se ejercita abriendo la pantalla.
#   · LECTOR    — solo escribe por la migración de cabecera; no hay nada que ejercitar.
def cubo(clave):
    mod, fn = clave.split(".", 1)
    if clave in escribe_directo:
        return "PANTALLA" if (mod.endswith("_ui") or mod == "app") else "MUTADOR"
    return "PANTALLA" if (mod.endswith("_ui") or mod == "app") else "LECTOR"


cubos = defaultdict(list)
for c in pub_escriben:
    cubos[cubo(c)].append(c)

# ── 3) ¿quién las ha ejercitado? ─────────────────────────────────────────────
usadas = defaultdict(set)
for s in sorted(SCRATCH.glob("*.py")):
    if s.name == pathlib.Path(__file__).name:
        continue
    try:
        arb = ast.parse(io.open(s, encoding="utf-8").read())
    except Exception:
        continue
    nombres = {_nombre_llamada(n) for n in ast.walk(arb) if isinstance(n, ast.Call)}
    for clave in pub_escriben:
        if clave.split(".", 1)[1] in nombres:
            usadas[clave].add(s.name)

print(f"{len(publicas)} funciones en core+app · {len(escriben)} escriben "
      f"· {len(pub_escriben)} de ellas son PÚBLICAS\n")

print("== la superficie, por lo que hace de verdad ==")
for k in ("MUTADOR", "PANTALLA", "LECTOR"):
    _n = len(cubos[k])
    _ej = sum(1 for c in cubos[k] if usadas.get(c))
    print(f"  {k:<9} {_n:>3}   ejercitadas {_ej:>3} · sin ejercitar {_n - _ej:>3}")

_falta = [c for c in cubos["MUTADOR"] if not usadas.get(c)]
print(f"\n== MUTADORES sin ejercitar ({len(_falta)}) — la lista de trabajo ==")
_pm = defaultdict(list)
for c in _falta:
    _pm[c.split(".", 1)[0]].append(c.split(".", 1)[1])
for m in sorted(_pm):
    print(f"  {m:<14} {', '.join(sorted(_pm[m]))}")
print("\n" + "=" * 70 + "\n")

sin = [c for c in pub_escriben if not usadas.get(c)]
con = [c for c in pub_escriben if usadas.get(c)]
print(f"EJERCITADAS por algún script : {len(con)}")
print(f"NUNCA ejercitadas            : {len(sin)}\n")

print("== nunca ejercitadas, por módulo ==")
porm = defaultdict(list)
for c in sin:
    porm[c.split(".", 1)[0]].append(c.split(".", 1)[1])
for m in sorted(porm, key=lambda k: -len(porm[k])):
    print(f"  {m:<16} {len(porm[m]):>2}  {', '.join(sorted(porm[m])[:8])}"
          + (" …" if len(porm[m]) > 8 else ""))

print("\n== ejercitadas (para no repetir trabajo) ==")
for c in sorted(con):
    print(f"  {c:<42} {', '.join(sorted(usadas[c])[:3])}")
