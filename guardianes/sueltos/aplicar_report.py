# -*- coding: utf-8 -*-
"""Traduce el informe ADMIN (`report.py`) por AST y por POSICIÓN.

⚠️ Es un DOCUMENTO: va con `_d()` (alias, porque `d` ya es variable en `fstr()`),
que devuelve SIEMPRE el idioma base — un informe que sale de la empresa no cambia de
idioma según la pantalla de quien lo genera (regla v436).

⚠️ Se REFUSA traducir cualquier cadena que se use como ÍNDICE en el repo: son el
contrato con `schedule_table` / `plumb_table` (`'Actividad'`, `'Duración (d)'`,
`'Línea'`…), y traducirlas deja la lectura buscando una clave que no existe, sin dar
ningún error.
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

from dic_report import DIC                                         # noqa: E402

F = RAIZ / "core/report.py"

# ── 1 · qué cadenas se usan como ÍNDICE en algún módulo ──
indices = set()
for f in sorted(list((RAIZ / "core").glob("*.py")) + [RAIZ / "app.py"]):
    try:
        tr = ast.parse(f.read_text(encoding="utf-8"))
    except Exception:
        continue
    for n in ast.walk(tr):
        if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) \
           and isinstance(n.slice.value, str):
            indices.add(n.slice.value)
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "get" \
           and n.args and isinstance(n.args[0], ast.Constant) \
           and isinstance(n.args[0].value, str):
            indices.add(n.args[0].value)

peligro = sorted(set(DIC) & indices)
if peligro:
    print("⚠️ SE EXCLUYEN (se usan como índice en algún sitio):")
    for s in peligro:
        print(f"    {s[:70]!r}")
    for s in peligro:
        DIC.pop(s, None)

# ── 2 · el import del motor ──
src = F.read_text(encoding="utf-8")
if "from core.i18n import d as _d" not in src:
    # report.py no tiene logger: se ancla al import de highlighting
    ancla = "from core.highlighting import ("
    assert src.count(ancla) == 1, f"ancla del import: {src.count(ancla)}"
    src = src.replace(ancla, f"from core.i18n import d as _d\n{ancla}", 1)
    print("  import `d as _d` añadido")

# ── 3 · reescritura por POSICIÓN, de atrás hacia adelante ──
tr = ast.parse(src)
b = src.encode("utf-8")
lineas = b.split(b"\n")
puntos, saltados = [], []
for n in ast.walk(tr):
    if not (isinstance(n, ast.Constant) and isinstance(n.value, str)):
        continue
    if n.value not in DIC:
        continue
    if n.lineno != n.end_lineno:
        saltados.append((n.lineno, n.value[:44]))
        continue
    ini = sum(len(x) + 1 for x in lineas[:n.lineno - 1]) + n.col_offset
    fin = sum(len(x) + 1 for x in lineas[:n.end_lineno - 1]) + n.end_col_offset
    trozo = b[ini:fin].decode("utf-8")
    if not (trozo.startswith(('"', "'")) and trozo.endswith(('"', "'"))):
        saltados.append((n.lineno, n.value[:44]))
        continue
    q = trozo[0]
    if q in DIC[n.value]:
        q = "'" if q == '"' else '"'
    puntos.append((ini, fin, f'_d({q}{DIC[n.value]}{q})', n.value))

for ini, fin, nuevo, _ in sorted(puntos, reverse=True):
    b = b[:ini] + nuevo.encode("utf-8") + b[fin:]

nueva = b.decode("utf-8")
try:
    ast.parse(nueva)
except SyntaxError as e:
    print(f"  ✗ el resultado NO parsea, no se escribe: {e}")
    sys.exit(1)

F.write_text(nueva, encoding="utf-8")
print(f"\n{len(puntos)} cadenas traducidas ({len({p[3] for p in puntos})} distintas)")
if saltados:
    print(f"⚠️ {len(saltados)} saltadas (multilínea o no literales), a mano:")
    for ln, s in saltados:
        print(f"    L{ln}: {s!r}")
