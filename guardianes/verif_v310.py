"""v310: UNA definicion de gasto del grupo (los archivados vuelven a contar).

⚠️ El test de v309 dio un OK FALSO porque el mock devolvia la misma lista de
proyectos con y sin `incluir_archivados`. Aqui el mock lo RESPETA, que es lo unico
que permite detectar la diferencia.
"""
import ast
import importlib
import pathlib
import py_compile
import sys
from datetime import date

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


# ── Datos calcados de la hoja REAL auditada ──────────────────────
PROYS = [
    {"ID": "PRJ-0001", "Group": "cliente1", "Name": "prueba1", "Status": "Archivado",
     "Progress": "0", "Budget": "0"},
    {"ID": "PRJ-0005", "Group": "cliente1", "Name": "prueba2", "Status": "Planificado",
     "Progress": "0", "Budget": "10000"},
    {"ID": "PRJ-0006", "Group": "cliente1", "Name": "prueba 3", "Status": "Planificado",
     "Progress": "0", "Budget": "8000"},
]
GASTOS = [
    {"ID": "G-00001", "ProjectID": "PRJ-0001", "Group": "cliente1", "Amount": "1000",
     "Category": "Herramientas", "Date": "2026-07-28"},
    {"ID": "G-00002", "ProjectID": "PRJ-0001", "Group": "cliente1", "Amount": "500",
     "Category": "Materiales", "Date": "2026-07-28"},
]
HUERFANO = {"ID": "G-00003", "ProjectID": "", "Group": "cliente1", "Amount": "200",
            "Category": "Otros", "Date": "2026-08-02"}

import core.expenses as E
import core.projects as P


def _mock(gastos, con_huerfano=False):
    """⚠️ El mock RESPETA `incluir_archivados`: si devuelve siempre lo mismo, el test
    no puede ver la diferencia — que es justo el fallo del test de v309."""
    filas = list(gastos) + ([HUERFANO] if con_huerfano else [])
    return (lambda **k: [p for p in PROYS
                         if k.get("incluir_archivados") or p["Status"] != "Archivado"],
            lambda: filas)


def _limpiar_cache():
    """⚠️ `group_expenses` está CACHEADA (v108). Sin esto, la 2ª llamada con el mismo
    grupo devuelve el resultado de la 1ª y el test 'falla' por algo que no es el
    fallo — me pasó: el caso del huérfano daba 1500 en vez de 1700."""
    for f in (E.group_expenses, E._records):
        try:
            f.clear()
        except Exception:
            pass


print("== 1) el KPI vuelve a contar el proyecto archivado ==")
_o = (P.list_projects, E._records, E.labor_cost)
P.list_projects, E._records = _mock(GASTOS)
E.labor_cost = lambda pid, grupo: 0.0
_limpiar_cache()
try:
    ge = E.group_expenses("cliente1")
finally:
    P.list_projects, E._records, E.labor_cost = _o

_ids = [f["id"] for f in ge["proyectos"]]
check("el proyecto ARCHIVADO entra en las filas", "PRJ-0001" in _ids)
check("compras del grupo (la definicion unica)", ge["compras_grupo"], 1500.0)
check("Σ compras por proyecto == total del grupo",
      round(sum(f["compras"] for f in ge["proyectos"]), 2), ge["compras_grupo"])
check("la torta y el KPI ya suman lo MISMO",
      round(sum(ge["por_categoria"].values()), 2), ge["compras_grupo"])
check("0 huerfanos en los datos reales", ge["huerfanos"]["n"], 0)

print("\n== 2) una compra SIN proyecto no se pierde ==")
P.list_projects, E._records = _mock(GASTOS, con_huerfano=True)
E.labor_cost = lambda pid, grupo: 0.0
_limpiar_cache()
try:
    ge2 = E.group_expenses("cliente1")
finally:
    P.list_projects, E._records, E.labor_cost = _o
    _limpiar_cache()
check("se cuenta en el total del grupo", ge2["compras_grupo"], 1700.0)
check("...y se REPORTA como huerfana", ge2["huerfanos"], {"n": 1, "total": 200.0})
check("...pero NO se cuela en ningun proyecto",
      round(sum(f["compras"] for f in ge2["proyectos"]), 2), 1500.0)
check("total del grupo == Σ proyectos + huerfanos",
      round(sum(f["compras"] for f in ge2["proyectos"]) + ge2["huerfanos"]["total"], 2),
      ge2["compras_grupo"])

print("\n== 3) el P&L usa LA MISMA definicion (era la 3a respuesta distinta) ==")
from core import finance as F
import core.invoices as INV
import core.payroll as PR

_o2 = (INV.list_facturas, INV.estado_cobro, PR.list_nominas, PR.conceptos_de,
       E._records, P.list_projects)
INV.list_facturas = lambda g: []
INV.estado_cobro = lambda f: "emitida"
PR.list_nominas = lambda g: []
PR.conceptos_de = lambda n: []
P.list_projects, E._records = _mock(GASTOS, con_huerfano=True)
try:
    d = F.pnl("cliente1")
    d_jul = F.pnl("cliente1", date(2026, 7, 1), date(2026, 7, 31))
finally:
    (INV.list_facturas, INV.estado_cobro, PR.list_nominas, PR.conceptos_de,
     E._records, P.list_projects) = _o2
check("P&L compras == compras del grupo", d["compras"], ge2["compras_grupo"])
check("...incluye la huerfana (no se pierde dinero)", d["compras"], 1700.0)
check("con periodo sigue filtrando", d_jul["compras"], 1500.0)

print("\n== 4) el grafico duplicado se fue ==")
_src = (BASE / "core" / "projects_ui.py").read_text(encoding="utf-8")
_a = ast.parse(_src)
_fn = next(n for n in ast.walk(_a) if isinstance(n, ast.FunctionDef)
           and n.name == "render_group_expenses")
_barras = [n.lineno for n in ast.walk(_fn) if isinstance(n, ast.Call)
           and getattr(n.func, "id", "") == "_barras_html"]
_tortas = [n.lineno for n in ast.walk(_fn) if isinstance(n, ast.Call)
           and getattr(n.func, "id", "") == "_torta_html"]
check("0 bloques de barras (eran los mismos numeros que la torta)", _barras, [])
check("1 torta (la que pidio el usuario en v224)", len(_tortas), 1)
check("0 restos de los helpers borrados",
      _src.count("_blq_categorias_g") + _src.count("_blq_reparto_g"), 0)

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
    elif isinstance(n, (ast.FunctionDef, ast.Lambda)):
        for x in getattr(n.args, "args", []):
            asign.add(x.arg)
check("render_group_expenses sin nombres libres",
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
