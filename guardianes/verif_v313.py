"""v313: conciliar «lo que pagas» con «lo que cargas a las obras».

El chequeo que importa: que la CADENA cierre, y que cierre con los numeros REALES
del usuario (los de sus capturas), no con un ejemplo comodo.
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


print("== 1) la cadena cierra con los datos REALES del usuario ==")
# De las capturas: campo1 32.17 jornada / 32.16 proyecto @40; lksdfkldsf 0 / 8.97 @40;
# asfgjjd 8.69 / 8.69 sin tarifa; fijiofgjei 1.18 / 0 sin tarifa.
HP = {"campo1":     {"nombre": "lksdfkldsf", "jornada": 32.17, "proyecto": 32.16},
      "lksdfkldsf": {"nombre": "lksdfkldsf", "jornada": 0.0,   "proyecto": 8.97},
      "asfgjjd":    {"nombre": "asfgjjd",    "jornada": 8.69,  "proyecto": 8.69},
      "fijiofgjei": {"nombre": "fijiofgjei", "jornada": 1.18,  "proyecto": 0.0}}
RATES = {"campo1": 40.0, "lksdfkldsf": 40.0}          # los otros sin tarifa
NOMS = [{"Base": "1286.80", "PeriodoHasta": "2026-08-09", "Estado": "pagada",
         "ConceptosJSON": '[{"concepto":"Superannuation","tipo":"aporte","monto":147.98}]'}]

from core import finance as F
import core.timeclock as TC
import core.auth as A
import core.payroll as PR

_o = (TC.jornada_y_proyecto, A.rate_map, PR.list_nominas, PR.conceptos_de)
TC.jornada_y_proyecto = lambda g, d=None, h=None: HP
A.rate_map = lambda g: RATES
PR.list_nominas = lambda g, **k: NOMS
PR.conceptos_de = lambda n: [{"concepto": "Superannuation", "tipo": "aporte",
                              "monto": 147.98}]
try:
    c = F.conciliacion_mo("cliente1")
finally:
    TC.jornada_y_proyecto, A.rate_map, PR.list_nominas, PR.conceptos_de = _o

check("cargado a obras (= lo que se factura)", c["cargado"], 1645.20)
check("horas cobradas sin pagar (el 2º login)", c["cobrado_no_pagado"], 358.80)
check("horas pagadas sin cargar (traslados)", c["pagado_no_cargado"], 0.40)
check("base que deberia pagarse", c["base_teorica"], 1286.80)
check("base realmente en nominas", c["base_nomina"], 1286.80)
check("aportes de ley (super 11.5%)", c["aportes"], 147.98)
check("costo real de la mano de obra", c["costo_real"], 1434.78)
check("LA CADENA CIERRA (nada sin explicar)", c["sin_explicar"], 0.0)
# v384: v325 partió esta lista en `sin_tarifa` (a quien SÍ se le puede poner) y
# `de_baja` (cuentas que ya no existen). Que `fijiofgjei` no salga aquí es el
# arreglo funcionando, no un fallo.
check("avisa solo de quien SÍ tiene arreglo", c["sin_tarifa"], ["asfgjjd"])
check("y la cuenta de baja va aparte (v325)", "fijiofgjei" in (c.get("de_baja") or []))
# el numero que el usuario pregunto: costo real vs lo que dice el P&L
check("coincide con el costo_nomina del P&L (1434.78)", c["costo_real"], 1434.78)

print("\n== 2) `sin_explicar` NO se cuadra a la fuerza ==")
TC.jornada_y_proyecto = lambda g, d=None, h=None: HP
A.rate_map = lambda g: RATES
PR.list_nominas = lambda g, **k: [{"Base": "1000.00", "PeriodoHasta": "2026-08-09",
                                   "ConceptosJSON": "[]"}]      # nomina editada a mano
PR.conceptos_de = lambda n: []
try:
    c2 = F.conciliacion_mo("cliente1")
finally:
    TC.jornada_y_proyecto, A.rate_map, PR.list_nominas, PR.conceptos_de = _o
check("una nomina editada a mano se DELATA", c2["sin_explicar"], 286.80)
check("...y no se toca la base teorica", c2["base_teorica"], 1286.80)

print("\n== 3) identidad de la cadena, con casos al azar ==")
import random
random.seed(7)
for _ in range(200):
    _hp = {f"u{i}": {"nombre": f"u{i}",
                     "jornada": round(random.uniform(0, 40), 2),
                     "proyecto": round(random.uniform(0, 40), 2)} for i in range(4)}
    _rt = {f"u{i}": round(random.choice([0, 25, 40, 62.5]), 2) for i in range(4)}
    TC.jornada_y_proyecto = lambda g, d=None, h=None, _x=_hp: _x
    A.rate_map = lambda g, _x=_rt: _x
    PR.list_nominas = lambda g, **k: []
    PR.conceptos_de = lambda n: []
    try:
        r = F.conciliacion_mo("g")
    finally:
        pass
    _izq = round(r["cargado"] - r["cobrado_no_pagado"] + r["pagado_no_cargado"], 2)
    if abs(_izq - r["base_teorica"]) > 0.02:
        check("la identidad falla con", (_hp, _rt), None)
        break
else:
    check("cargado − cobrado_no_pagado + pagado_no_cargado == base_teorica (200 casos)", True)
TC.jornada_y_proyecto, A.rate_map, PR.list_nominas, PR.conceptos_de = _o

print("\n== 4) las pantallas nombran la cifra por lo que es ==")
_src = (BASE / "core" / "projects_ui.py").read_text(encoding="utf-8")
# ⚠️ CADUCADO por v440 (i18n F3): el texto pasó al inglés a propósito.
check("P&L: «Costos (lo que pagas)»",
      "Costos (lo que pagas)" in _src or "Costs (what you pay)" in _src)
check("Gastos: «Costo cargado a obras»",
      "Costo cargado a obras" in _src or "Cost charged to jobs" in _src)
# v384: dejó de ser un `st.metric` y se pinta con `_kpi_card`. El nombre —que es
# lo que v313 vino a fijar para no llamar «costo» a tres cosas— sigue igual.
check("Rentabilidad: «Costo cargado»",
      '"Costo cargado"' in _src or '"Cost charged"' in _src)
# ⚠️ CADUCADO Y ACTUALIZADO en v455 (regla v385): el aviso ya no puede hablar de
# «margen 0%» porque ese modelo se ELIMINÓ — la ganancia va por rubro. Lo que esta
# regla protege no es la palabra «margen», sino que la pantalla AVISE cuando una obra
# no tiene ganancia puesta: sin ese aviso, «ganancia estimada 0» parece un fallo de la
# app en vez de un dato que falta (patrón v346, un cero silencioso).
check("aviso de obra SIN ganancia puesta",
      "with no profit set" in _src or "no profit set" in _src)
check("el bloque de conciliacion existe", "conciliacion_mo" in _src)

print("\n== 5) nombres libres + compila + importa ==")
_a = ast.parse(_src)
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
for _nm in ("render_pnl", "render_group_profitability", "render_group_expenses"):
    _f = next(n for n in ast.walk(_a) if isinstance(n, ast.FunctionDef) and n.name == _nm)
    asign, usados = set(_mn) | _B, []
    for n in ast.walk(_f):
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
    # v384: se excluye el `e` de `except ... as e` — falso positivo conocido de este
# chequeo desde v145 (su ámbito no sigue el orden textual).
check(f"{_nm} sin nombres libres",
      sorted({u for u in usados if u not in asign and u != "e"}), [])

_fc = ast.parse((BASE / "core" / "finance.py").read_text(encoding="utf-8"))
_cm = next(n for n in ast.walk(_fc) if isinstance(n, ast.FunctionDef)
           and n.name == "conciliacion_mo")
_mnf = set()
for n in _fc.body:
    if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
        _mnf.add(n.name)
    elif isinstance(n, (ast.Import, ast.ImportFrom)):
        for x in n.names:
            _mnf.add((x.asname or x.name).split(".")[0])
asign, usados = set(_mnf) | _B, []
for n in ast.walk(_cm):
    if isinstance(n, ast.arg):
        asign.add(n.arg)
    elif isinstance(n, ast.Name):
        (asign.add(n.id) if isinstance(n.ctx, ast.Store) else usados.append(n.id))
    elif isinstance(n, (ast.Import, ast.ImportFrom)):
        for x in n.names:
            asign.add((x.asname or x.name).split(".")[0])
check("conciliacion_mo sin nombres libres",
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
