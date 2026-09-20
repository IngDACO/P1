"""Las lecturas de un VALOR traducible que además LLEGAN a pantalla.

⚠️ Solo esas se envuelven en `i18n.etiqueta()`. Envolver una COMPARACIÓN
(`if p["Estado"] == "En pausa"`) rompería el matching sin dar ningún error — que es la
regla de oro de toda esta migración.

Se marca una lectura como «se pinta» si está dentro del argumento de una función de
display, dentro de un f-string que lo está, o dentro de un dict que se pasa a una tabla.
"""
import ast, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

COLS = {"Estado", "EstadoManual", "Tipo", "Rol", "Categoria", "Categoría",
        "estado", "tipo", "rol", "categoria", "estado_cobro"}
DISPLAY = {"markdown", "caption", "write", "success", "info", "warning", "error",
           "metric", "subheader", "header", "title", "text", "dataframe", "table",
           "button", "radio", "selectbox", "expander", "popover", "toast", "chip",
           "kpi_row", "_kpi_card", "_kpi", "exito", "aviso"}


def _lee_valor(n):
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
       and n.func.attr == "get" and n.args and isinstance(n.args[0], ast.Constant) \
       and n.args[0].value in COLS:
        return n.args[0].value
    if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) \
       and n.slice.value in COLS:
        return n.slice.value
    return None


UI = sorted(p.stem for p in (RAIZ / "core").glob("*_ui.py"))
tot = 0
for m in UI:
    tr = ast.parse((RAIZ / f"core/{m}.py").read_text(encoding="utf-8"))
    pintadas = []
    for c in ast.walk(tr):
        if not isinstance(c, ast.Call):
            continue
        fn = c.func.id if isinstance(c.func, ast.Name) else getattr(c.func, "attr", "")
        if fn not in DISPLAY:
            continue
        for a in list(c.args) + [k.value for k in c.keywords]:
            for x in ast.walk(a):
                col = _lee_valor(x)
                if col:
                    pintadas.append((x.lineno, col, fn))
    if pintadas:
        print(f"\n=== {m} ({len(pintadas)}) ===")
        for ln, col, fn in sorted(set(pintadas)):
            print(f"  L{ln:<5} {col:14} → st.{fn}")
        tot += len(set(pintadas))
print(f"\nTOTAL que SE PINTAN: {tot}")
