"""v404 · El catálogo de rieles escribe y lee EL MISMO libro.

El fallo que cierra: `Rieles` es una hoja GLOBAL (vive en el maestro desde v359), pero
`rails._ws()` la abría con `timeclock._get_worksheet()`, que devuelve el libro DEL GRUPO
de la sesión. Resultado: se escribía en el libro del cliente y se leía del maestro, así
que un riel nuevo no se encontraba nunca y **RAIL se quedaba en 0** al cargar un plano.

Lo que se protege es el PRINCIPIO, no el nombre de una función: escritura y lectura
tienen que resolver el mismo libro. Si mañana cambia `get_sheet`, esto sigue valiendo.
"""
import ast
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrator"}

from core import hojas, rails, timeclock                          # noqa: E402

ok = True


def check(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"           esperado: {esp!r}")


print("== 1) ⚠️ el mismo libro, medido en vivo ==")
w, err = rails._ws()
check("la hoja se abre", err, None)
_escribe = w.spreadsheet.id if w is not None else ""
_lee = timeclock.sheet_id_para(rails.RIELES_SHEET)
print(f"         escribe en {_escribe}")
print(f"         lee de     {_lee}")
check("escritura y lectura resuelven el MISMO libro", _escribe, _lee)
check("...y ese libro es el MAESTRO (Rieles es global, v359)",
      _lee, timeclock._sheet_maestro())
# ⚠️ y que NO sea el del grupo: si algún día coincidieran por accidente, este check
# lo dice. El de la demo es distinto del maestro, así que la comparación informa.
_del_grupo = timeclock.sheet_id_para("Proyectos", "cliente1")
if _del_grupo != timeclock._sheet_maestro():
    check("no es el libro del grupo", _escribe != _del_grupo, True)

print("\n== 2) los dos caminos VEN lo mismo ==")
_por_lote = len(rails.list_rieles())
_directo = len(w.get_all_records(numericise_ignore=["all"])) if w else -1
check("hay catálogo que comparar (si no, el test pasa en vacío)", _por_lote > 0, True)
check("mismo número de rieles por los dos caminos", _por_lote, _directo)

print("\n== 3) al escribir se tiran las DOS cachés ==")
src = io.open(r"C:\Users\diego\P1\survey_app\core\rails.py", encoding="utf-8").read()
arb = ast.parse(src)
_inv = next((n for n in ast.walk(arb) if isinstance(n, ast.FunctionDef)
             and n.name == "_invalidate"), None)
check("existe `_invalidate`", _inv is not None, True)
_t = ast.get_source_segment(src, _inv) or ""
# ⚠️ CADUCADO en v482 y ACTUALIZADO: la llamada dejó de ser pelada — ahora recibe el
# TÍTULO de la hoja (`hojas.invalidar(RIELES_SHEET)`) para limpiar SOLO el libro donde
# vive, en vez de la caché de todos los clientes. La regla no cambia: el lote se tiene
# que tirar, o el riel nuevo no se ve en 120 s. Se afirma sobre la LLAMADA, no sobre su
# forma exacta, que es lo que la hizo caducar.
_inv_calls = [n for n in ast.walk(_inv) if isinstance(n, ast.Call)
              and getattr(n.func, "attr", "") == "invalidar"
              and getattr(getattr(n.func, "value", None), "id", "") == "hojas"]
check("⚠️ tira el LOTE de v339 (si no, el riel nuevo no se ve en 120 s)",
      len(_inv_calls) >= 1, True)
# ⚠️ Y `Rails` es hoja GLOBAL: si se le pasara el título de una hoja de inquilino,
# limpiaría el libro del grupo y el maestro se quedaría con el riel viejo.
check("...y dice de QUE hoja, para no limpiar el libro equivocado (v482)",
      all(c.args or c.keywords for c in _inv_calls), True)
check("...y también la caché del módulo", "_records.clear()" in _t, True)
# ⚠️ Por AST: buscar la subcadena `_invalidate()` da True por el propio `def`, y el
# docstring de esta función habla de ella. grep ≠ uso (trampa nº2).
check("⚠️ y no se llama a sí misma (el reemplazo en masa se mordió una vez)",
      [n for n in ast.walk(_inv) if isinstance(n, ast.Call)
       and getattr(n.func, "id", "") == "_invalidate"], [])
_escritores = [n.name for n in ast.walk(arb) if isinstance(n, ast.FunctionDef)
               and n.name in ("add_riel", "update_riel", "delete_riel")]
check("los 3 escritores existen", sorted(_escritores),
      ["add_riel", "delete_riel", "update_riel"])
for _e in _escritores:
    _fn = next(n for n in ast.walk(arb) if isinstance(n, ast.FunctionDef) and n.name == _e)
    _st = ast.get_source_segment(src, _fn) or ""
    check(f"{_e} invalida", "_invalidate()" in _st, True)

print("\n== 4) ya no se usa el lector que devolvía el libro del grupo ==")
# ⚠️ Por AST y no por subcadena: el docstring de `_ws` NOMBRA `_get_worksheet` para
# explicar el fallo, y un `in src` lo contaba como uso — la trampa nº2, dentro del
# propio guardián escrito para vigilar esto.
_usos = [n for n in ast.walk(arb)
         if isinstance(n, ast.Attribute) and n.attr == "_get_worksheet"]
check("ninguna llamada REAL a `_get_worksheet` en rails.py", _usos, [])
check("...y sí se usa `get_sheet`",
      any(isinstance(n, ast.Attribute) and n.attr == "get_sheet" for n in ast.walk(arb)),
      True)

print("\n== 5) las sondas SABEN ver el caso roto ==")
_roto = ast.parse("def f():\n    timeclock._get_worksheet()\n")
check("la sonda del lector viejo lo detecta cuando está",
      bool([n for n in ast.walk(_roto)
            if isinstance(n, ast.Attribute) and n.attr == "_get_worksheet"]), True)
_rec = ast.parse("def _invalidate():\n    _invalidate()\n")
check("la sonda de la recursión la detecta cuando está",
      bool([n for n in ast.walk(_rec) if isinstance(n, ast.Call)
            and getattr(n.func, "id", "") == "_invalidate"]), True)

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
