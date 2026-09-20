"""¿Cuál es la ocurrencia que el AST no ve? (204 por texto vs 203 por AST)"""
import ast
import io
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")
for p in sorted(BASE.glob("core/*.py")) + [BASE / "app.py"]:
    src = io.open(p, encoding="utf-8").read()
    if "use_container_width=True" not in src:
        continue
    arb = ast.parse(src)
    reales = set()
    for n in ast.walk(arb):
        if isinstance(n, ast.Call):
            for kw in n.keywords:
                if kw.arg == "use_container_width":
                    reales.add(kw.value.lineno)
    for i, ln in enumerate(src.splitlines(), start=1):
        if "use_container_width=True" in ln:
            if i not in reales:
                print(f"NO ES ARGUMENTO  {p.name}:{i}  {ln.strip()[:110]}")
            elif ln.count("use_container_width=True") > 1:
                print(f"DOS EN UNA LÍNEA {p.name}:{i}  {ln.strip()[:110]}")
