"""Todo literal que ALIMENTA el PDF de las herramientas (tool_pdf / render_guardar).

⚠️ El invariante de v441 mide funciones de DISPLAY (`st.*`). Un PDF NO es display: es un
documento que sale a obra, así que sus literales se quedaron fuera del barrido — y por eso
hay que mirarlos aparte. Regla v436/v439: un documento va en el idioma BASE (`d`), no en el
de la pantalla de quien lo genera.
"""
import ast, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
DEST = {"tool_pdf", "render_guardar"}


def _lits(nodo):
    """Todas las cadenas literales dentro de un nodo, incluidas las de f-string."""
    out = []
    for x in ast.walk(nodo):
        if isinstance(x, ast.Constant) and isinstance(x.value, str):
            s = x.value.strip()
            if s and any(c.isalpha() for c in s):
                out.append((x.lineno, s))
    return out


for rel in ["core/plumb_ui.py", "core/rail_cut_ui.py", "core/buffer_cut_ui.py",
            "core/belting_ui.py", "core/tool_pdf.py", "core/tool_save_ui.py"]:
    tr = ast.parse((RAIZ / rel).read_text(encoding="utf-8"))
    hall = []
    for c in ast.walk(tr):
        if not isinstance(c, ast.Call):
            continue
        fn = c.func.id if isinstance(c.func, ast.Name) else getattr(c.func, "attr", "")
        if fn not in DEST:
            continue
        for a in list(c.args) + [k.value for k in c.keywords]:
            hall += _lits(a)
    if rel == "core/tool_pdf.py":                 # el módulo entero: su chrome
        hall = _lits(tr)
    if hall:
        print(f"\n=== {rel}  ({len(hall)}) ===")
        for ln, s in sorted(set(hall)):
            print(f"  {ln:5}  {s[:90]!r}")
