"""Ámbito por función: ¿está `theme` y `can_delete` DONDE se usan? (lección v342)."""
import ast
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
S = io.open(r"C:\Users\diego\P1\survey_app\core\projects_ui.py", encoding="utf-8").read()
A = ast.parse(S)

for nom in ("_detalle_proyecto", "_cartera_lista", "_cartera_clickeable",
            "_panel_proyectos", "_ir_a_facturar"):
    fn = next((n for n in ast.walk(A) if isinstance(n, ast.FunctionDef) and n.name == nom), None)
    if fn is None:
        print(f"{nom}: NO EXISTE")
        continue
    t = ast.get_source_segment(S, fn) or ""
    alias = set()
    for n in ast.walk(fn):
        if isinstance(n, ast.ImportFrom):
            for al in n.names:
                alias.add(al.asname or al.name)
    args = [x.arg for x in fn.args.args]
    usa_theme = "theme." in t
    tiene_theme = "theme" in alias
    usa_cd = "can_delete" in t
    tiene_cd = "can_delete" in args or "can_delete" in {
        x.id for n in ast.walk(fn) if isinstance(n, ast.Assign)
        for x in ast.walk(n) if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store)}
    print(f"{nom}")
    print(f"   args            : {args}")
    print(f"   usa `theme.`    : {usa_theme}   importa theme: {tiene_theme}"
          + ("   ⚠️ NameError" if usa_theme and not tiene_theme else ""))
    print(f"   usa can_delete  : {usa_cd}   definido: {tiene_cd}"
          + ("   ⚠️ NameError" if usa_cd and not tiene_cd else ""))
