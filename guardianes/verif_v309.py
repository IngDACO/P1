"""v309: el fallo del '$' (LaTeX) + periodo en el P&L + desglose y enlaces.

Lo critico: (a) que NO quede ninguna cadena con dos '$' sin escapar en toda la
app, (b) que el P&L SIN periodo de exactamente lo mismo que antes (si el filtro
cambia los totales historicos, hemos roto la contabilidad).
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


print("== 1) GUARDIAN: 0 cadenas con dos '$' sin escapar ==")
TEXTO = {"markdown", "caption", "write", "info", "warning", "success", "error",
         "metric", "button", "link_button", "checkbox", "radio", "selectbox",
         "text_input", "number_input", "expander"}


def literales(nodo):
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
        return nodo.value
    if isinstance(nodo, ast.JoinedStr):
        out = ""
        for v in nodo.values:
            out += v.value if (isinstance(v, ast.Constant)
                               and isinstance(v.value, str)) else "\x00"
        return out
    return ""


hits, n_arch = [], 0
for p in sorted(BASE.rglob("*.py")):
    n_arch += 1
    try:
        a = ast.parse(p.read_text(encoding="utf-8"))
    except Exception:
        continue
    for n in ast.walk(a):
        if not (isinstance(n, ast.Call) and getattr(n.func, "attr", "") in TEXTO):
            continue
        for arg in list(n.args) + [k.value for k in n.keywords]:
            t = literales(arg)
            # `\$` YA es el escape correcto → no cuenta
            sin_esc = t.replace("\\$", "")
            if sin_esc.count("$") >= 2:
                hits.append(f"{p.name}:{n.lineno} {sin_esc[:60]!r}")
check(f"se recorrieron {n_arch} ficheros", n_arch > 40, True)
check("0 cadenas con dos '$' sin escapar", hits, [])

print("\n== 2) theme.dinero ==")
from core import theme as T
check("escapa el simbolo", T.dinero(1234.5), "\\$1,234.50")
# ⚠️ Lo que importa NO es el redondeo que a mi me parezca: es que `dinero` imprima
# EXACTAMENTE lo mismo que el `f"${x:,.Nf}"` que habia antes. Si cambiara, cada
# cifra de las pantallas de dinero cambiaria en silencio con este deploy.
_iguales = all(T.dinero(v, n) == f"\\${v:,.{n}f}"
               for v in (0, 1, 1234.5, 1234.4, 0.005, 99999.999, -80.2, 1287.0)
               for n in (0, 2))
check("imprime IGUAL que el formato anterior (incl. redondeo al par de Python)",
      _iguales)
check("None no rompe", T.dinero(None), "\\$0.00")
check("texto basura no rompe", T.dinero("x"), "\\$0.00")
check("negativo", T.dinero(-80.2), "\\$-80.20")

print("\n== 3) el P&L SIN periodo da EXACTAMENTE lo de antes ==")
from core import finance as F

_FACS = [{"Total": "1000", "Collected": "1000", "Date": "2026-08-05",
          "ClientName": "Acme", "ExpiryDate": "2026-09-01"},
         {"Total": "500", "Collected": "0", "Date": "2026-07-05",
          "ClientName": "Beta", "ExpiryDate": "2026-07-20"}]
_NOMS = [{"Base": "300", "Net": "300", "Status": "pagada", "ConceptsJSON": "[]",
          "PeriodTo": "2026-08-15"},
         {"Base": "200", "Net": "200", "Status": "emitida", "ConceptsJSON": "[]",
          "PeriodTo": "2026-07-15"}]
# ⚠️ v384: las filas llevan `Grupo` porque **v310 cambió la definición** de las
# compras del P&L: pasó de «filtrar por los proyectos del grupo» a «filtrar por la
# columna Grupo», para que una compra sin proyecto no se perdiera y para que la
# misma pregunta dejara de tener tres respuestas en la app. La fixture se quedó en
# la definición vieja, así que TODAS las compras se caían y el test daba 0.
_GASTOS = [{"Group": "g", "ProjectID": "PRJ-1", "Amount": "50", "Date": "2026-08-10"},
           {"Group": "g", "ProjectID": "PRJ-1", "Amount": "70", "Date": "2026-07-10"},
           {"Group": "OTRO", "ProjectID": "OTRO", "Amount": "999",
            "Date": "2026-08-10"}]   # otro grupo: NO debe entrar

import core.invoices as INV
import core.payroll as PR
import core.expenses as E
import core.projects as P

_o = (INV.list_facturas, INV.estado_cobro, PR.list_nominas, PR.conceptos_de,
      E._records, P.list_projects)
INV.list_facturas = lambda g: _FACS
INV.estado_cobro = lambda f: ("vencida" if f.get("ExpiryDate", "") < "2026-08-15"
                              and float(f["Collected"]) < float(f["Total"]) else "emitida")
PR.list_nominas = lambda g: _NOMS
PR.conceptos_de = lambda n: []
E._records = lambda: _GASTOS
P.list_projects = lambda **k: [{"ID": "PRJ-1"}]
try:
    todo = F.pnl("g")
    agosto = F.pnl("g", date(2026, 8, 1), date(2026, 8, 31))
finally:
    (INV.list_facturas, INV.estado_cobro, PR.list_nominas, PR.conceptos_de,
     E._records, P.list_projects) = _o

check("TODO · facturado", todo["facturado"], 1500.0)
check("TODO · costo nomina", todo["costo_nomina"], 500.0)
check("TODO · compras (solo proyectos del grupo)", todo["compras"], 120.0)
check("TODO · ganancia", todo["ganancia"], 880.0)
check("TODO · el gasto de OTRO grupo NO entra", todo["compras"] != 1119.0, True)

print("  -- con periodo (agosto) --")
check("AGO · solo la factura de agosto", agosto["facturado"], 1000.0)
check("AGO · solo la nomina que cierra en agosto", agosto["costo_nomina"], 300.0)
check("AGO · solo la compra de agosto", agosto["compras"], 50.0)
check("AGO · ganancia", agosto["ganancia"], 650.0)
check("el periodo NO es un superconjunto (filtra de verdad)",
      agosto["facturado"] < todo["facturado"], True)

print("\n== 4) fechas: la fila sin fecha no se inventa un mes ==")
check("sin rango, una fila sin fecha ENTRA", F._en_rango("", None, None), True)
check("con rango, una fila sin fecha NO entra",
      F._en_rango("", date(2026, 8, 1), date(2026, 8, 31)), False)
check("fecha basura tampoco", F._en_rango("ayer", date(2026, 8, 1), None), False)
check("limite inferior incluido", F._en_rango("2026-08-01", date(2026, 8, 1), None), True)
check("limite superior incluido",
      F._en_rango("2026-08-31", None, date(2026, 8, 31)), True)
check("fuera por un dia", F._en_rango("2026-09-01", None, date(2026, 8, 31)), False)

print("\n== 5) desglose honesto ==")
check("hay desglose por cliente", [c for c, _ in todo["por_cliente"]], ["Acme", "Beta"])
check("...ordenado desc", [v for _, v in todo["por_cliente"]], [1000.0, 500.0])
_src = (BASE / "core" / "projects_ui.py").read_text(encoding="utf-8")
check("NO se inventa 'ganancia por proyecto'", "ganancia por proyecto" not in _src.lower()
      or "inventado" in _src.lower())
# ⚠️ v384: v317 reestructuró el resumen financiero y los destinos pasaron a ser
# DATOS de las tuplas de indicadores, no llamadas literales `_ir_a(...)`. Lo que hay
# que proteger sigue siendo lo mismo: que desde el dinero se pueda llegar a Facturas
# y a Nóminas, y que esos IDs existan de verdad (el fallo de v303).
_dest = [('"finanzas", "🧾 Facturas"', "🧾 Facturas"),
         ('"finanzas", "👥 Nóminas"', "👥 Nóminas")]
from core import home_ui as _H309
_subs_fin = [i for i, _ in _H309._SUBSECCIONES["finanzas"][1]]
check("el P&L puede llegar a Facturas y a Nóminas",
      all(patron in _src for patron, _ in _dest))
check("...y esos IDs de sub-pestaña existen",
      all(sid in _subs_fin for _, sid in _dest))
from core import home_ui as H
_ids = [i for i, _ in H._SUBSECCIONES["finanzas"][1]]
check("...y esos IDs existen", all(x in _ids for x in ("🧾 Facturas", "👥 Nóminas")))

print("\n== 6) compila e importa ==")
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
