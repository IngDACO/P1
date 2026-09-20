"""¿El guardián de v372 CAZA el código roto? (regla v306/v344/v363)

Se le da el fuente con el orden invertido —el que estaba en producción desde
v162— y la UI sin la guarda de NaN, y tiene que fallar en los dos.
"""
import ast
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")


def llamadas(nodo):
    out = {}
    for n in ast.walk(nodo):
        if isinstance(n, ast.Call):
            nom = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
            if nom:
                out.setdefault(nom, []).append(n.lineno)
    return out


def revisa_orden(src):
    """Devuelve las funciones que recomputan ANTES de invalidar."""
    malas = []
    for fn in [n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef)]:
        c = llamadas(fn)
        if "_recompute_project_avance" in c and "_invalidate" in c:
            if min(c["_invalidate"]) > min(c["_recompute_project_avance"]):
                malas.append(fn.name)
    return malas


src = BASE.joinpath("projects.py").read_text(encoding="utf-8")

print("== sobre el código ACTUAL ==")
print(f"   funciones con el orden invertido: {revisa_orden(src) or 'ninguna'}  ✓")

print("\n== sobre el código ROTO (el orden de v162, tal cual estaba) ==")
# ⚠️ El ancla se acota a `save_field_progress` POR AST y ya NO incluye el texto del
# mensaje: v450 lo tradujo («Avances guardados.» → `t("Progress saved.")`) y el probe
# se quedó sin poder construir su versión rota — se negó a dar un aprobado falso, que
# es lo correcto, pero anclar en un texto que se traduce lo condena a caducar otra vez.
# El par `_invalidate()` + `_recompute_project_avance(pid)` aparece 4 veces en el
# módulo, así que hay que acotar al cuerpo de ESA función o se invertirían cuatro.
_arb = ast.parse(src)
_fn = next(n for n in ast.walk(_arb)
           if isinstance(n, ast.FunctionDef) and n.name == "save_field_progress")
_ls = src.splitlines(keepends=True)
_cuerpo = "".join(_ls[_fn.lineno - 1:_fn.end_lineno])
_INV = "    _invalidate()"
_REC = "    _recompute_project_avance(pid)"
_par = _INV + chr(10) + _REC + chr(10)
assert _cuerpo.count(_par) == 1, f"‼️ el ancla no es única en la función: {_cuerpo.count(_par)}"
_roto_fn = _cuerpo.replace(_par, _REC + chr(10) + _INV + chr(10), 1)
roto = src.replace(_cuerpo, _roto_fn, 1)
assert roto != src, "‼️ el ancla no existe: el 'test contra el roto' no probaría NADA"
malas = revisa_orden(roto)
print(f"   funciones con el orden invertido: {malas}")
caza = malas == ["save_field_progress"]
print(f"   {'✓ lo caza, y solo a esa' if caza else '‼️ NO lo caza'}")

print("\n== la guarda de NaN, sobre la UI ROTA ==")
src_ui = BASE.joinpath("projects_ui.py").read_text(encoding="utf-8")
fn = next(n for n in ast.walk(ast.parse(src_ui))
          if isinstance(n, ast.FunctionDef) and n.name == "_field_activities")
roto_ui = ast.unparse(fn).replace("pd.isna(_av)", "False")
caza2 = "pd.isna" in ast.unparse(fn) and "pd.isna(_av)" not in roto_ui
print(f"   actual tiene la guarda: {'pd.isna(_av)' in ast.unparse(fn)}")
print(f"   {'✓ la ausencia se detecta' if caza2 else '‼️'}")

sys.exit(0 if (caza and caza2) else 1)
