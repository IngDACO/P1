"""¿Cuál de los 227 es DATO y no etiqueta?

⚠️ Traducir un DATO no da ningún error: el matching deja de funcionar en silencio. Se
marca todo texto que ADEMÁS aparezca en una comparación (`x == "…"`, `in [...]`), como
clave de dict, o en OTRO módulo del repo — los tres olores de «esto se compara».
"""
import ast, json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

cand = {e["txt"] for e in json.loads(Path("f5_pendientes.json").read_text(encoding="utf-8"))
        if not e["css"]}

comparados, claves, donde = set(), set(), {}
for f in list(RAIZ.rglob("*.py")):
    try:
        tr = ast.parse(f.read_text(encoding="utf-8"))
    except Exception:
        continue
    for n in ast.walk(tr):
        if isinstance(n, ast.Compare):
            for x in [n.left] + list(n.comparators):
                for c in ast.walk(x):
                    if isinstance(c, ast.Constant) and c.value in cand:
                        comparados.add(c.value)
        if isinstance(n, ast.Dict):
            for k in n.keys:
                if isinstance(k, ast.Constant) and k.value in cand:
                    claves.add(k.value)
        if isinstance(n, ast.Constant) and n.value in cand:
            donde.setdefault(n.value, set()).add(f.name)

print(f"{len(cand)} candidatos\n")
print("=== APARECEN EN UNA COMPARACIÓN (posible DATO) ===")
for s in sorted(comparados):
    print(f"  {sorted(donde.get(s, []))}  {s[:80]!r}")
print("\n=== SON CLAVE DE UN DICT ===")
for s in sorted(claves):
    print(f"  {sorted(donde.get(s, []))}  {s[:80]!r}")
print("\n=== APARECEN EN MÁS DE UN FICHERO ===")
for s, fs in sorted(donde.items()):
    if len(fs) > 1:
        print(f"  {sorted(fs)}  {s[:80]!r}")
