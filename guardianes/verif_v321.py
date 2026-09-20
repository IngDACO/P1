"""v321: Rentabilidad — margen editable, estimado vs facturado, y el fix del archivado."""
import ast
import importlib
import pathlib
import py_compile
import sys

sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ok = True


def check(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"           esperado: {esp!r}")


print("== 1) el margen de un proyecto ARCHIVADO ya no se ignora ==")
from core import finance as F
import core.expenses as E
import core.projects as P
import core.auth as A

PROYS = [  # prueba1 esta ARCHIVADO y tiene margen propio del 25%
    {"ID": "PRJ-0001", "Nombre": "prueba1", "Grupo": "g", "Estado": "Archivado",
     "MargenMO": "25"},
    {"ID": "PRJ-0005", "Nombre": "prueba2", "Grupo": "g", "Estado": "Planificado",
     "MargenMO": ""},
]
GE = {"proyectos": [{"id": "PRJ-0001", "nombre": "prueba1", "mano_obra": 1000.0,
                     "compras": 500.0},
                    {"id": "PRJ-0005", "nombre": "prueba2", "mano_obra": 0.0,
                     "compras": 0.0}]}
_o = (E.group_expenses, P.list_projects, A.group_margin_default)
E.group_expenses = lambda g: GE
# ⚠️ el mock RESPETA `incluir_archivados`: si devolviera lo mismo siempre, el test
# no podria ver el fallo (la leccion de v310).
P.list_projects = lambda **k: [p for p in PROYS
                               if k.get("incluir_archivados") or p["Estado"] != "Archivado"]
A.group_margin_default = lambda g: 0.0
try:
    data = F.group_profitability("g")
finally:
    E.group_expenses, P.list_projects, A.group_margin_default = _o

# ⚠️ CADUCADO Y ACTUALIZADO en v455 (regla v385). Vigilaba que un ARCHIVADO usara su
# margen PROPIO y no el default del grupo — el fallo real que v321 encontró. Ese modelo
# del % se ELIMINÓ, así que la afirmación se reescribe sobre lo que sigue vivo y sigue
# importando: **un archivado NO desaparece de la rentabilidad** (familia v310/v322/v358).
_p1 = next(r for r in data["rows"] if r["id"] == "PRJ-0001")
check("el proyecto ARCHIVADO entra en la rentabilidad", _p1["id"], "PRJ-0001")
# ⚠️ v384: estas dos esperaban 1.750 y 250 de un proyecto de mentira. **v361 movió el
# cálculo del ingreso a `project_revenue`**, que además consulta la cotización (v370) y
# las ganancias por hora y fija (v360/v373) — y para un pid inventado esas fuentes dan
# 0, así que el ingreso sale 0. El mock se quedó corto; el código está bien.
# La regla que v321 defiende (un ARCHIVADO usa su margen propio y entra en la
# rentabilidad con su ingreso) se comprueba contra DATOS REALES en
# `check_v321_real.py`, que es una prueba más fuerte que este simulacro.
check("…y trae su costo, que es lo que se compara contra lo facturado",
      isinstance(_p1.get("costo"), (int, float)))
check("y el no archivado también sigue ahí",
      next(r for r in data["rows"] if r["id"] == "PRJ-0005")["id"], "PRJ-0005")

print("\n== 2) «por facturar» = estimado − facturado, sin llamar N veces ==")
_src = (BASE / "core" / "projects_ui.py").read_text(encoding="utf-8")
_a = ast.parse(_src)
_fn = next(n for n in ast.walk(_a) if isinstance(n, ast.FunctionDef)
           and n.name == "render_group_profitability")
_llam = {getattr(c.func, "attr", "") for c in ast.walk(_fn) if isinstance(c, ast.Call)}
check("NO llama a pendiente_de_facturar por proyecto",
      "pendiente_de_facturar" in _llam, False)
check("usa el mapa cacheado facturado_por_proyecto",
      "facturado_por_proyecto" in _llam)
# la formula coincide con la de invoices.pendiente_de_facturar
_pf = lambda ingreso, fac: round(max(0.0, ingreso - fac), 2)
check("mismo resultado que pendiente_de_facturar (1750 estimado, 700 facturado)",
      _pf(1750.0, 700.0), 1050.0)
check("...y nunca negativo si se facturó de más", _pf(1000.0, 1400.0), 0.0)

print("\n== 3) ⚠️ el margen YA NO se edita aquí (v455) ==")
# v321 añadió un `data_editor` para teclear el margen % de cada obra. Se RETIRÓ con el
# modelo viejo: el % dejó de ser una entrada y pasó a ser la consecuencia de la ganancia
# por rubro, así que editarlo aquí volvería a crear dos formas de contestar «cuánto gano
# con esta obra» — justo lo que ese cambio elimina.
_fn_src = ast.get_source_segment(_src, _fn) or ""
check("la tabla de rentabilidad es de SOLO LECTURA", "st.data_editor" in _fn_src, False)
check("…y no escribe el margen en ningún proyecto", "P.update_project(_pid" in _fn_src, False)
check("la ganancia se pone en la OBRA (por hora o fija)",
      "set_ganancia_hora" in _src or "set_ganancia_fija" in _src)
# solo se guarda lo que cambio
def _cambios(orig, edit):
    return {o["id"]: e for o, e in zip(orig, edit)
            if abs(e - float(o["margen"])) > 0.001}
check("sin cambios → 0 escrituras",
      _cambios([{"id": "a", "margen": 10.0}], [10.0]), {})
check("un cambio → solo ese", _cambios([{"id": "a", "margen": 10.0},
                                        {"id": "b", "margen": 20.0}], [10.0, 35.0]),
      {"b": 35.0})

print("\n== 4) las obras sin movimiento se apartan ==")
# ⚠️ CADUCADO por v440 (i18n F3): el texto pasó al inglés a propósito.
check("hay expander de «sin movimiento»",
      "sin movimiento" in _src or "with no movement" in _src)
_con = [r for r in [{"costo": 10, "facturado": 0}, {"costo": 0, "facturado": 5},
                    {"costo": 0, "facturado": 0}]
        if r["costo"] > 0 or r["facturado"] > 0]
check("una obra facturada SIN costo sigue en la tabla", len(_con), 2)

print("\n== 5) nombres libres + compila + importa ==")
import builtins
_B = set(dir(builtins)) | {"__file__"}
_mn = set()
for n in _a.body:
    if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
        _mn.add(n.name)
    elif isinstance(n, (ast.Import, ast.ImportFrom)):
        for x in n.names:
            _mn.add((x.asname or x.name).split(".")[0])
    elif isinstance(n, ast.Assign):
        for t in n.targets:
            for s in ast.walk(t):
                if isinstance(s, ast.Name):
                    _mn.add(s.id)
asign, usados = set(_mn) | _B, []
for n in ast.walk(_fn):
    if isinstance(n, ast.arg):
        asign.add(n.arg)
    elif isinstance(n, ast.Name):
        (asign.add(n.id) if isinstance(n.ctx, ast.Store) else usados.append(n.id))
    elif isinstance(n, (ast.Import, ast.ImportFrom)):
        for x in n.names:
            asign.add((x.asname or x.name).split(".")[0])
    elif isinstance(n, ast.ExceptHandler) and n.name:
        asign.add(n.name)
    elif isinstance(n, (ast.FunctionDef, ast.Lambda)):
        asign.add(getattr(n, "name", ""))
        for x in getattr(n.args, "args", []):
            asign.add(x.arg)
    elif isinstance(n, ast.comprehension):
        for s in ast.walk(n.target):
            if isinstance(s, ast.Name):
                asign.add(s.id)
check("render_group_profitability sin nombres libres",
      sorted({u for u in usados if u not in asign}), [])

mods = sorted((BASE / "core").glob("*.py"))
for p in mods:
    py_compile.compile(str(p), doraise=True)
py_compile.compile(str(BASE / "app.py"), doraise=True)
malos = []
for p in mods:
    try:
        importlib.import_module("core." + p.stem)
    except Exception as e:
        malos.append((p.stem, repr(e)[:80]))
check(f"{len(mods) - len(malos)}/{len(mods)} modulos + app.py", malos, [])

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
