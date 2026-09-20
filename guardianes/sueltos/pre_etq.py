"""¿Alguna función usa `_etq` como VARIABLE? (el fallo de v437/v439/v440, cuarta vez)

Python marca el nombre local en el ÁMBITO ENTERO de la función, así que un
`_etq = auth.etiqueta_usuarios(...)` en la línea 110 convierte el `_etq(...)` de la 136
en «'dict' object is not callable» — y ni compilar ni importar lo ven.
"""
import ast, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")


def _mismo_ambito(fn):
    out = []
    for h in fn.body:
        pila = [h]
        while pila:
            x = pila.pop()
            out.append(x)
            for c in ast.iter_child_nodes(x):
                if not isinstance(c, (ast.Lambda, ast.FunctionDef,
                                      ast.AsyncFunctionDef, ast.ClassDef)):
                    pila.append(c)
    return out


malos = []
for f in sorted((RAIZ / "core").glob("*_ui.py")) + [RAIZ / "app.py"]:
    tr = ast.parse(f.read_text(encoding="utf-8"))
    for fn in ast.walk(tr):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        nod = _mismo_ambito(fn)
        comp = {id(nn) for x in nod for g in (getattr(x, "generators", []) or [])
                for nn in ast.walk(g.target) if isinstance(nn, ast.Name)}
        st_ = [x.lineno for x in nod if isinstance(x, ast.Name)
               and isinstance(x.ctx, ast.Store) and x.id == "_etq" and id(x) not in comp]
        usa = [x.lineno for x in nod if isinstance(x, ast.Call)
               and isinstance(x.func, ast.Name) and x.func.id == "_etq"]
        if st_:
            malos.append(f"{f.name}:{fn.lineno} {fn.name}  asigna _etq en L{st_}"
                         + (f"  ⚠️ y LO LLAMA en L{usa}" if usa else "  (no lo llama)"))
print(f"{len(malos)} funciones asignan `_etq`:")
for m in malos:
    print("   ", m)
sys.exit(1 if any("LO LLAMA" in m for m in malos) else 0)
