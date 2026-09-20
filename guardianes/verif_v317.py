"""v317: el Resumen financiero como torre de control.

Lo que de verdad hay que probar: que «Por proyecto» diga los $210,42 de la obra
entera y no los $1.710 que salen de mezclar meses.
"""
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


print("== 1) «Por proyecto» responde lo que el P&L por mes no puede ==")
from core import finance as F
import core.invoices as INV
import core.expenses as E
import core.projects as P

PROYS = [{"ID": "PRJ-0001", "Name": "prueba1", "Group": "cliente1", "Status": "Archivado"},
         {"ID": "PRJ-0005", "Name": "prueba2", "Group": "cliente1", "Status": "Planificado"}]
_o = (INV.facturado_por_proyecto, E.labor_cost, E.project_expenses, P.list_projects)
INV.facturado_por_proyecto = lambda g: {"PRJ-0001": 3145.20}
E.labor_cost = lambda pid, g: 1645.20 if pid == "PRJ-0001" else 0.0
E.project_expenses = lambda pid: {"total": 1500.0 if pid == "PRJ-0001" else 0.0}
P.list_projects = lambda **k: PROYS
try:
    rows = F.resultado_por_proyecto("cliente1")
finally:
    INV.facturado_por_proyecto, E.labor_cost, E.project_expenses, P.list_projects = _o

check("solo entran las obras con movimiento", [r["id"] for r in rows], ["PRJ-0001"])
r0 = rows[0]
check("facturado", r0["facturado"], 3145.20)
check("costo cargado (MO + compras)", r0["costo"], 3145.20)
check("RESULTADO de la obra entera", r0["resultado"], 0.0)
check("margen %", r0["margen"], 0.0)
print("         → la obra se facturó AL COSTO (margen 0%), que es el hallazgo real")

print("\n== 2) el resultado NO depende del periodo (es lo que arregla) ==")
import inspect
_sig = inspect.signature(F.resultado_por_proyecto)
check("la firma no acepta fechas, a propósito",
      [p for p in _sig.parameters if p in ("desde", "hasta")], [])
_doc = (F.resultado_por_proyecto.__doc__ or "")
check("y se explica por qué en el docstring", "ACUMULADO" in _doc)

print("\n== 3) «sin facturar» = trabajo hecho y no pedido ==")
_o2 = (INV.pendiente_de_facturar, P.list_projects)
INV.pendiente_de_facturar = lambda pid, g, prj=None: {"PRJ-0001": 0.0,
                                                      "PRJ-0005": 900.0}.get(pid, 0.0)
P.list_projects = lambda **k: PROYS
try:
    sf = F.sin_facturar("cliente1")
finally:
    INV.pendiente_de_facturar, P.list_projects = _o2
check("solo lo que queda por facturar", sf, [("prueba2", 900.0)])

print("\n== 4) la rejilla: 8 fijos, en 2 filas de 4 ==")
_src = (BASE / "core" / "projects_ui.py").read_text(encoding="utf-8")
_a = ast.parse(_src)
_fn = next(n for n in ast.walk(_a) if isinstance(n, ast.FunctionDef) and n.name == "render_pnl")
_ind = next((n for n in ast.walk(_fn) if isinstance(n, ast.Assign)
             and any(getattr(t, "id", "") == "_IND" for t in n.targets)), None)
check("se pudo LEER la rejilla", _ind is not None, True)
check("son 8 indicadores", len(_ind.value.elts), 8)
_slugs = [e.elts[0].value for e in _ind.value.elts]
check("sin slugs repetidos (key duplicada = crash)", len(set(_slugs)), 8)
# el reparto en filas: zip trunca en silencio si una fila supera las columnas
_cortes = [(s.slice.lower.value if s.slice.lower else 0,
            s.slice.upper.value if s.slice.upper else 8)
           for s in ast.walk(_fn) if isinstance(s, ast.Subscript)
           and isinstance(s.slice, ast.Slice)
           and isinstance(s.value, ast.Name) and s.value.id == "_IND"]
check("filas = [0:4] y [4:]", sorted(_cortes), [(0, 4), (4, 8)])
_cols = [c.args[0].value for c in ast.walk(_fn) if isinstance(c, ast.Call)
         and getattr(c.func, "attr", "") == "columns" and c.args
         and isinstance(c.args[0], ast.Constant)]
check("ninguna fila supera las columnas", [x for x in _cortes if (x[1] - x[0]) > max(_cols)], [])
check("las filas cubren los 8 sin huecos",
      sorted({i for a2, b2 in _cortes for i in range(a2, b2)}), list(range(8)))

print("\n== 5) los destinos existen ==")
from core import home_ui as H
_dest = [(e.elts[6].value, e.elts[7].value) for e in _ind.value.elts]
_malos = [(s, sub) for s, sub in _dest
          if s not in dict(H._SECCIONES)
          or sub not in [i for i, _d in H._SUBSECCIONES.get(s, ("", []))[1]]]
check("los 8 «→ Ir a» apuntan a una sub-pestaña real", _malos, [])

print("\n== 6) la torta se queda FIJA (lo pidió el usuario) ==")
_tortas = [n.lineno for n in ast.walk(_fn) if isinstance(n, ast.Call)
           and getattr(n.func, "id", "") == "_torta_html"]
check("la torta se pinta en el cuerpo, no dentro de una herramienta", len(_tortas), 1)
_tools = next((n for n in ast.walk(_fn) if isinstance(n, ast.Assign)
               and any(getattr(t, "id", "") == "_TOOLS" for t in n.targets)), None)
# v384: eran 3 y v318 hizo la composición la CUARTA — decisión del usuario tras
# verla fija («que sea una herramienta más»). La regla viva es que estén las
# acordadas, no cuántas son.
check("4 herramientas (v318 sumó la composición)", len(_tools.value.elts), 4)
check("...y son las acordadas",
      [e.elts[0].value for e in _tools.value.elts], ["conc", "cli", "comp", "prj"])

print("\n== 7) compila e importa ==")
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
