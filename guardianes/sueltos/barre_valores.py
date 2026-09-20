"""¿Dónde pinta la INTERFAZ un VALOR de dato sin pasarlo por `i18n.etiqueta()`?

⚠️ `i18n.VALORES` traduce los datos que viven en español en la hoja (estados, tipos,
roles, categorías) SIN tocarlos: solo cambia cómo se MUESTRAN. El mecanismo existe desde
v436 y **solo lo usan los 3 PDF** — la interfaz pinta el valor crudo. Es el patrón de
v131/v148: se escribe algo y nadie lo lee.

Se buscan las lecturas de las columnas que contienen esos valores.
"""
import ast, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

# columnas / claves cuyo CONTENIDO está en `i18n.VALORES`
COLS = {"Estado", "EstadoManual", "Tipo", "Rol", "Categoria", "Categoría",
        "estado", "tipo", "rol", "categoria", "estado_cobro"}

UI = sorted(p.stem for p in (RAIZ / "core").glob("*_ui.py"))
tot = 0
for m in UI:
    src = (RAIZ / f"core/{m}.py").read_text(encoding="utf-8")
    tr = ast.parse(src)
    usa_etq = "i18n.etiqueta" in src or re.search(r"from core\.i18n import .*\betiqueta\b", src)
    hits = []
    for n in ast.walk(tr):
        # x.get("Estado", …)  ó  x["Estado"]
        col = None
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
           and n.func.attr == "get" and n.args and isinstance(n.args[0], ast.Constant) \
           and n.args[0].value in COLS:
            col = n.args[0].value
        elif isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) \
                and n.slice.value in COLS:
            col = n.slice.value
        if col:
            hits.append((n.lineno, col))
    if hits:
        print(f"  {m:16} {len(hits):3} lecturas de un valor traducible"
              f"   ·  usa etiqueta(): {'SÍ' if usa_etq else 'NO'}")
        tot += len(hits)
print(f"\nTOTAL: {tot} lecturas en la interfaz")
