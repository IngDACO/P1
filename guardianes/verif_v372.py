"""GUARDIÁN v372 — la escritura del campo.

Tres cosas, ninguna comprobable a ojo:

1. ⚠️ **El orden invalidar → recomputar.** `_recompute_project_avance` lee
   `list_activities`, que está CACHEADA 120 s. Si corre ANTES de `_invalidate()`
   recalcula el % del proyecto con las actividades VIEJAS — y la caché está
   caliente siempre, porque la pantalla acaba de pintar esa tabla para editarla.
2. **La celda borrada.** `int(NaN)` reventaba el guardado entero.
3. **El aviso sobrevive al rerun** (v365): un `st.warning` antes de `st.rerun()`
   no llega nunca a la pantalla.
"""
import ast
import pathlib
import sys
import tokenize
import io

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")
ok = True


def sin_comentarios(src: str) -> str:
    """⚠️ Trampa nº2: un grep sobre el fuente cuenta MIS PROPIOS comentarios."""
    out = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type != tokenize.COMMENT:
            out.append(tok)
    return tokenize.untokenize(out)


def llamadas(nodo):
    """{nombre: [líneas]} de las llamadas hechas DENTRO de esta función."""
    out = {}
    for n in ast.walk(nodo):
        if isinstance(n, ast.Call):
            f = n.func
            nom = getattr(f, "id", None) or getattr(f, "attr", None)
            if nom:
                out.setdefault(nom, []).append(n.lineno)
    return out


# ── 1) orden invalidar → recomputar, en TODAS las funciones ─────────
print("== 1. ⚠️ invalidar ANTES de recomputar (la caché es de 120 s) ==")
arbol = ast.parse(BASE.joinpath("projects.py").read_text(encoding="utf-8"))
vistos = 0
for fn in [n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef)]:
    c = llamadas(fn)
    if "_recompute_project_avance" not in c or "_invalidate" not in c:
        continue
    vistos += 1
    inv, rec = min(c["_invalidate"]), min(c["_recompute_project_avance"])
    bien = inv < rec
    ok &= bien
    print(f"   {'✓' if bien else '‼️'} {fn.name:<24} invalidar L{inv} · recomputar L{rec}"
          + ("" if bien else "  ← RECALCULA CON LA CACHÉ VIEJA"))
if vistos < 4:
    ok = False
    print(f"   ‼️ solo se revisaron {vistos} funciones: el chequeo pasó en VACÍO")
else:
    print(f"   ({vistos} funciones revisadas)")

# ⚠️ Y las que recomputan SIN invalidar: `update_activity_progress` es legítima
#    (recomputa en memoria sobre filas que acaba de leer frescas), pero cualquier
#    otra que llame a `_recompute_project_avance` tras escribir y no invalide,
#    tiene el mismo fallo.
print("\n   -- funciones que recomputan sin invalidar (deben recomputar EN MEMORIA) --")
for fn in [n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef)]:
    c = llamadas(fn)
    if "_recompute_project_avance" in c and "_invalidate" not in c:
        print(f"      ⚠️ {fn.name} — revisar a mano")

# ── 2) la celda borrada no revienta el guardado ─────────────────────
print("\n== 2. la celda de avance BORRADA (NaN) ==")
src_ui = BASE.joinpath("projects_ui.py").read_text(encoding="utf-8")
fn_ui = next(n for n in ast.walk(ast.parse(src_ui))
             if isinstance(n, ast.FunctionDef) and n.name == "_field_activities")
cuerpo = ast.unparse(fn_ui)
_guarda = "pd.isna" in cuerpo
ok &= _guarda
print(f"   {'✓' if _guarda else '‼️'} se comprueba `pd.isna` antes de convertir")
# el int() no puede aplicarse al valor CRUDO del editor sin pasar por la guarda
_crudo = "int(r['Avance %'])" in cuerpo.replace('"', "'")
ok &= not _crudo
print(f"   {'✓' if not _crudo else '‼️'} no queda ningún `int(r[\"Avance %\"])` sin proteger")
_nota = 'if pd.isna(_nt) else' in cuerpo
ok &= _nota
print(f"   {'✓' if _nota else '‼️'} la nota vacía se guarda como '' (no como el texto 'nan')")

# ── 3) el aviso llega a la pantalla ─────────────────────────────────
print("\n== 3. ⚠️ el aviso sobrevive al `st.rerun()` (v365) ==")
# En la rama que hace rerun el aviso tiene que ir por `flash`; en la que NO,
# tiene que pintarse directo (encolarlo lo dejaría de fantasma en otra pantalla).
rama_rerun = rama_sin = None
for n in ast.walk(fn_ui):
    if isinstance(n, ast.If) and ast.unparse(n.test).startswith("not cambios"):
        rama_sin, rama_rerun = ast.unparse(n.body), ast.unparse(n.orelse)
if rama_rerun is None:
    ok = False
    print("   ‼️ no se encontró la rama del guardado")
else:
    a = "flash.aviso" in rama_rerun and "st.rerun" in rama_rerun
    b = "st.warning" in rama_sin and "flash" not in rama_sin
    ok &= a and b
    print(f"   {'✓' if a else '‼️'} con rerun → el aviso va por `flash` (llega tras la recarga)")
    print(f"   {'✓' if b else '‼️'} sin rerun → se pinta directo (no queda de fantasma)")

# ── 4) ámbito del import (regla v342/v366: presencia ≠ ámbito) ──────
print("\n== 4. `flash` importado a nivel de MÓDULO, no dentro de otra función ==")
mod = ast.parse(sin_comentarios(src_ui))
_nivel_modulo = any(
    isinstance(n, ast.ImportFrom) and any(al.name == "flash" for al in n.names)
    for n in mod.body                      # ⚠️ body, NO walk: no descender a los def
)
ok &= _nivel_modulo
print(f"   {'✓' if _nivel_modulo else '‼️ NameError esperando'} import de módulo: {_nivel_modulo}")

print("\n" + ("✅ v372 OK: se invalida antes de recomputar, la celda vacía no rompe "
              "y el aviso llega" if ok else "⚠️ REVISAR"))
sys.exit(0 if ok else 1)
