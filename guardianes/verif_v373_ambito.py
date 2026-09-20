"""Nombres libres y keys duplicadas en las funciones reescritas de v373.

⚠️ Al partir `_ganancia_section` en tres, cualquier variable que se quedara en la
función de origen daría NameError al abrir el desplegable — el fallo de v342/v126.
Y dos widgets con la misma `key` revientan la página.
"""
import ast
import builtins
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SRC = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\projects_ui.py")
arbol = ast.parse(SRC.read_text(encoding="utf-8"))
ok = True

# nombres disponibles a nivel de MÓDULO (⚠️ body, no walk: no descender a los def)
modulo = set(dir(builtins))
for n in arbol.body:
    if isinstance(n, (ast.Import, ast.ImportFrom)):
        modulo |= {(a.asname or a.name).split(".")[0] for a in n.names}
    elif isinstance(n, (ast.FunctionDef, ast.ClassDef)):
        modulo.add(n.name)
    elif isinstance(n, ast.Assign):
        modulo |= {t.id for t in n.targets if isinstance(t, ast.Name)}

DIANAS = ["_ganancia_section", "_editor_ganancia_hora", "_ganancia_fija_ui"]
print("== nombres sin resolver ==")
for nom in DIANAS:
    fn = next((n for n in ast.walk(arbol)
               if isinstance(n, ast.FunctionDef) and n.name == nom), None)
    if fn is None:
        print(f"   ‼️ falta {nom}")
        ok = False
        continue
    define = {a.arg for a in fn.args.args}
    usa = []
    for n in ast.walk(fn):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            define.add(n.id)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            define |= {(a.asname or a.name).split(".")[0] for a in n.names}
        elif isinstance(n, ast.comprehension) and isinstance(n.target, ast.Name):
            define.add(n.target.id)
        elif isinstance(n, ast.Lambda):
            define |= {a.arg for a in n.args.args}
        elif isinstance(n, ast.ExceptHandler) and n.name:
            define.add(n.name)
    for n in ast.walk(fn):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            if n.id not in define and n.id not in modulo:
                usa.append((n.id, n.lineno))
    libres = sorted(set(usa))
    ok &= not libres
    print(f"   {'✓' if not libres else '‼️'} {nom:<24} {libres or 'ninguno'}")

# keys de widget duplicadas en el módulo (solo las literales/f-string constantes)
print("\n== keys de widget nuevas, sin colisión ==")
keys = {}
for n in ast.walk(arbol):
    if isinstance(n, ast.Call):
        for kw in n.keywords:
            if kw.arg == "key":
                t = ast.unparse(kw.value)
                keys[t] = keys.get(t, 0) + 1
for k in ('f"gf_{pid}"', 'f"gf_save_{pid}"', 'f"gh_ed_{pid}"',
          'f"gh_save_{pid}"', 'f"gh_undo_{pid}"'):
    kk = k.replace('"', "'")
    n = keys.get(kk, 0)
    bien = n == 1
    ok &= bien
    print(f"   {'✓' if bien else '‼️ duplicada'} {kk} → {n}")

print("\n" + ("✅ ámbito y keys OK" if ok else "⚠️ REVISAR"))
sys.exit(0 if ok else 1)
