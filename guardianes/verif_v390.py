"""v390 · Vista por DÍA de la cuadrilla + sábado/domingo en la semana.

Lo que hay que proteger:
  (a) que añadir un día NO mueva ninguna fecha existente (`fecha_de_dia` es la base
      de todo el roster: si 'mar' dejara de ser lunes+1, se desplazaría la semana
      entera);
  (b) que un día extra CON datos se vea SIEMPRE — si dependiera del botón, planificar
      un sábado y recargar lo escondería (el fallo de v340);
  (c) que no se pueda quitar una columna con trabajo dentro;
  (d) que el tablero pinte el color de cada celda con el MISMO índice con el que
      genera su key (si los dos bucles divergen, cada celda coge el color de otra);
  (e) que los cuatro cortes de `weekday() > 4` sigan protegiendo el caso «no hay
      nada», pero ya no escondan un fin de semana planificado.
"""
import ast
import importlib
import pathlib
import py_compile
import sys
from datetime import date, timedelta

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


import streamlit as st                                       # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrator"}
from core import roster as R                                 # noqa: E402
from core import roster_ui as RU                             # noqa: E402

LUN = date(2026, 8, 10)          # lunes

print("== 1) ⚠️ añadir días NO mueve ninguna fecha existente ==")
# Si esto se rompe, TODA la planificación histórica se desplaza en silencio.
_esperado = {"lun": date(2026, 8, 10), "mar": date(2026, 8, 11), "mie": date(2026, 8, 12),
             "jue": date(2026, 8, 13), "vie": date(2026, 8, 14)}
check("los 5 días de siempre caen donde caían",
      {d: R.fecha_de_dia(LUN, d) for d in R.DIAS}, _esperado)
check("sábado = lunes + 5", R.fecha_de_dia(LUN, "sab"), date(2026, 8, 15))
check("domingo = lunes + 6", R.fecha_de_dia(LUN, "dom"), date(2026, 8, 16))
check("DIAS_TODOS va en el orden de weekday()",
      [R.DIAS_TODOS[date(2026, 8, 10 + i).weekday()] for i in range(7)],
      ["lun", "mar", "mie", "jue", "vie", "sab", "dom"])
check("todo día tiene etiqueta", [d for d in R.DIAS_TODOS if d not in R.DIAS_LABEL], [])

print("\n== 2) qué columnas se pintan ==")


def _sem(**celdas):
    return {"campo1": {d: {"items": [{"a": "PRJ-1", "i": "07:00", "f": "15:30"}],
                           "nota": ""} for d in celdas}}


check("semana normal → 5 columnas", R.dias_con_datos({}), R.DIAS)
check("pedido a mano → aparece el sábado",
      R.dias_con_datos({}, ["sab"]), R.DIAS + ["sab"])
# ⚠️ el caso que justifica el diseño: dato guardado, botón NO pulsado
check("con datos en sábado se ve AUNQUE no se haya pedido",
      R.dias_con_datos(_sem(sab=1)), R.DIAS + ["sab"])
check("sábado y domingo, en orden",
      R.dias_con_datos(_sem(dom=1), ["sab"]), R.DIAS + ["sab", "dom"])
check("una celda VACÍA en sábado no abre la columna",
      R.dias_con_datos({"campo1": {"sab": {"items": [], "nota": ""}}}), R.DIAS)
check("...pero una NOTA sola sí (es dato)",
      R.dias_con_datos({"campo1": {"sab": {"items": [], "nota": "traer llaves"}}}),
      R.DIAS + ["sab"])
check("nunca se pierde un día de la semana normal",
      all(d in R.dias_con_datos(_sem(sab=1), ["dom"]) for d in R.DIAS), True)

print("\n== 3) no se puede esconder trabajo (regla v340) ==")
check("dice QUIÉN tiene trabajo el sábado", R.dia_tiene_datos(_sem(sab=1), "sab"),
      ["campo1"])
check("día vacío → nadie", R.dia_tiene_datos(_sem(sab=1), "dom"), [])
_src = (BASE / "core" / "roster_ui.py").read_text(encoding="utf-8")
_arb = ast.parse(_src)
_cd = next(n for n in ast.walk(_arb) if isinstance(n, ast.FunctionDef)
           and n.name == "_control_dias")
_txt = ast.get_source_segment(_src, _cd) or ""
check("el botón de quitar se deshabilita con datos dentro", "disabled=bool(con)" in _txt)
# ⚠️ CADUCADO por el i18n de v441 (la app pasó al inglés), NO es una regresión: la
# conducta —avisar de quién tiene trabajo ese día— está intacta. Se reancla a la
# parte ESTABLE (que el `help` NOMBRE a esas personas) en vez de a la frase, que es
# justo lo que el cambio de idioma mueve.
check("...y explica por qué (nombra a quien tiene trabajo)",
      "help=" in _txt and "con[:3]" in _txt and "len(con)" in _txt)

print("\n== 3b) auto-poblar: el fin de semana NO se llena por defecto (v392) ==")
# ⚠️ Al asignar personal a una obra se rellena su planificador entre las fechas del
# proyecto. Si eso llenara sáb/dom siempre, la excepción se volvería norma y todo el
# mundo acabaría con el fin de semana ocupado. Pero si en ESA semana ya hay alguien
# trabajando el sábado, dejar fuera al recién asignado obliga a añadirlo a mano.
import json as _json                                            # noqa: E402


class _WSFake:
    def __init__(self, filas):
        self.vals = [["ID", "Group", "Week", "User", "DataJSON"]] + filas
        self.updates, self.nuevas = [], []

    def get_all_values(self):
        return self.vals

    def batch_update(self, ups, **k):
        self.updates.extend(ups)

    def append_rows(self, rows, **k):
        self.nuevas.extend(rows)


def _celda(pid, i="", f=""):
    return {"items": [{"a": pid, "i": i, "f": f}], "nota": ""}


def _corre(filas):
    ws = _WSFake(filas)
    _o = R._ws_roster
    R._ws_roster = lambda: ws
    try:
        res = R.autopoblar_proyecto("cliente1", "PRJ-9", ["nuevo"],
                                    LUN, LUN + timedelta(days=6))
    finally:
        R._ws_roster = _o
    # qué días acabó teniendo el usuario nuevo
    escrito = {}
    for r in ws.nuevas:
        escrito = _json.loads(r[4] or "{}")
    for u in ws.updates:
        escrito = _json.loads(u["values"][0][0] or "{}")
    # ⚠️ ordenado por DÍA, no alfabéticamente: `sorted()` pone «jue» antes que «lun»
    # y el test fallaba en falso contra un código correcto (la lección de v372).
    return res, sorted(escrito.keys(), key=R.DIAS_TODOS.index)


_SEM = LUN.isoformat()
_r1, _d1 = _corre([])                                    # semana virgen
check("semana sin nadie el sábado → solo Lun–Vie", _d1, R.DIAS)
check("...y rellena los 5", _r1["llenadas"], 5)

_r2, _d2 = _corre([["R1", "cliente1", _SEM, "otro",
                    _json.dumps({"sab": _celda("PRJ-1")})]])
check("alguien YA trabaja ese sábado → el nuevo también lo cubre",
      _d2, R.DIAS + ["sab"])
check("...son 6 días", _r2["llenadas"], 6)

_r3, _d3 = _corre([["R1", "cliente1", _SEM, "otro",
                    _json.dumps({"dom": _celda("PRJ-1")})]])
check("solo domingo trabajado → solo domingo se añade", _d3, R.DIAS + ["dom"])

_r4, _d4 = _corre([["R1", "cliente1", _SEM, "otro",
                    _json.dumps({"sab": {"items": [], "nota": ""}})]])
check("una celda VACÍA en sábado no lo abre", _d4, R.DIAS)

# ⚠️ el rango de fechas del proyecto sigue mandando
ws = _WSFake([["R1", "cliente1", _SEM, "otro", _json.dumps({"sab": _celda("PRJ-1")})]])
_o = R._ws_roster
R._ws_roster = lambda: ws
try:
    _r5 = R.autopoblar_proyecto("cliente1", "PRJ-9", ["nuevo"],
                                LUN, LUN + timedelta(days=2))   # lun–mié
finally:
    R._ws_roster = _o
_d5 = (sorted(_json.loads(ws.nuevas[0][4]).keys(), key=R.DIAS_TODOS.index)
       if ws.nuevas else [])
check("fuera de las fechas del proyecto no se rellena", _d5, ["lun", "mar", "mie"])

print("\n== 4) el rango de fechas no miente ==")
check("Lun–Vie", R.rango_label(LUN), "10/08 – 14/08/2026")
check("con sábado, el rango llega al sábado",
      R.rango_label(LUN, R.DIAS + ["sab"]), "10/08 – 15/08/2026")
check("con domingo, al domingo",
      R.rango_label(LUN, R.DIAS + ["sab", "dom"]), "10/08 – 16/08/2026")
# v394: versión corta para la barra (la larga necesita ~140 px y su columna tiene 56)
check("corto: sin año", R.rango_label(LUN, corto=True), "10 – 14/08")
check("corto: respeta el sábado añadido",
      R.rango_label(LUN, R.DIAS + ["sab"], corto=True), "10 – 15/08")
check("⚠️ el largo NO cambia (lo usan el board del campo y el guardián de v290)",
      R.rango_label(LUN), "10/08 – 14/08/2026")

print("\n== 5) ⚠️ el tablero: color y key con el MISMO índice ==")
_tb = next(n for n in ast.walk(_arb) if isinstance(n, ast.FunctionDef)
           and n.name == "_tablero_editable")
_ttxt = ast.get_source_segment(_src, _tb) or ""
check("recorre `dias` (parámetro), no R.DIAS", "for d in R.DIAS" not in _ttxt)
check("el índice se calcula igual en los dos bucles",
      _ttxt.count("idx = pi * len(dias) + di"), 2)
# ⚠️ CADUCADO por v440 (i18n F3): el texto pasó al inglés a propósito.
# Lo que protege es que el multiselect reciba `dias` (los VISIBLES), no R.DIAS.
check("el multiselect de días usa los visibles",
      '"Aplicar a estos días", dias' in _ttxt
      or 't("Apply to these days"), dias' in _ttxt)
check("la etiqueta del check sigue a los días visibles",
      "R.DIAS_LABEL[dias[0]]" in _ttxt and "R.DIAS_LABEL[dias[-1]]" in _ttxt)

print("\n== 6) el fin de semana ya no se corta a ciegas ==")
_hu = (BASE / "core" / "home_ui.py").read_text(encoding="utf-8")
_ru = (BASE / "core" / "route_ui.py").read_text(encoding="utf-8")
_ro = (BASE / "core" / "roster.py").read_text(encoding="utf-8")
check("agenda de Home: ya no corta por ser fin de semana",
      "Hoy es fin de semana — la planificación es de lunes a viernes." not in _hu)
check("...y solo se calla si NO hay datos", "R.dia_tiene_datos(sem, dia)" in _hu)
check("ruta del día: comprueba datos antes de rendirse", "dia_tiene_datos" in _ru)
check("asignaciones_dia ya no descarta sáb/dom",
      "if fecha.weekday() > 4:                     # sáb/dom: no hay rejilla" not in _ro)
check("el radar escanea los 7 días", "for d in R.DIAS_TODOS:" in _src)

print("\n== 7) el eje horario es UNO solo (no dos aritméticas) ==")
_v1 = next(n for n in ast.walk(_arb) if isinstance(n, ast.FunctionDef)
           and n.name == "_vista_dia")
_v2 = next(n for n in ast.walk(_arb) if isinstance(n, ast.FunctionDef)
           and n.name == "_vista_dia_cuadrilla")
for _n, _f in (("vista de una persona", _v1), ("vista de la cuadrilla", _v2)):
    _t = ast.get_source_segment(_src, _f) or ""
    check(f"{_n} usa `_eje_de`", "_eje_de(" in _t)
    check(f"{_n} NO recalcula el eje a mano", "// 60 - 1) * 60" not in _t)


def _it(a, i, f):
    return {"asig": a, "ini": i, "fin": f}


check("el eje del turno estándar no cambió",
      RU._eje_de([_it("A", "07:00", "15:30")]), (360, 1020))

print("\n== 8) EJECUTAR la vista de cuadrilla (importar no ejecuta, v378) ==")
TIDX = {"PRJ-0005": {"ID": "PRJ-0005", "Name": "Meriton", "Color": "#1d9e75",
                     "ProjectID": "PRJ-0005", "Number": ""},
        "PRJ-0006": {"ID": "PRJ-0006", "Name": "Green Square", "Color": "#d85a30",
                     "ProjectID": "PRJ-0006", "Number": ""}}
STAFF = [{"User": "campo1", "Name": "Jaime López"},
         {"User": "campo2", "Name": "Mei Chen"},
         {"User": "campo3", "Name": "Tom O'Brien"}]


def _datos(dia, porusuario):
    return {u: {dia: {"items": [{"a": a, "i": i, "f": f} for a, i, f in its],
                      "nota": ""}} for u, its in porusuario.items()}


_ESC = [
    ("mezcla: con hora, sin hora y libre",
     {"campo1": [("PRJ-0005", "07:00", "15:30")],
      "campo2": [("PRJ-0006", "", "")], "campo3": []}),
    ("una persona que se pisa a sí misma",
     {"campo1": [("PRJ-0005", "07:00", "15:30"), ("PRJ-0006", "07:00", "15:30")]}),
    ("NADIE con franja horaria (no debe dibujar eje)",
     {"campo1": [("PRJ-0005", "", "")], "campo2": [("PRJ-0006", "", "")]}),
    ("día completamente vacío", {}),
    ("franja mal tecleada", {"campo1": [("PRJ-0005", "15:30", "07:00")]}),
]
for _nom, _d in _ESC:
    try:
        RU._vista_dia_cuadrilla("cliente1", LUN, STAFF, _datos("sab", _d), TIDX, "sab")
        check(f"corre: {_nom}", True)
    except Exception as e:
        check(f"corre: {_nom}", f"{type(e).__name__}: {e}", True)
try:
    RU._control_dias(LUN, _sem(sab=1), R.DIAS + ["sab"])
    check("corre: _control_dias con un sábado ocupado", True)
except Exception as e:
    check("corre: _control_dias con un sábado ocupado", f"{type(e).__name__}: {e}", True)

print("\n== 9) la vista Día en la pantalla ==")
_rp = next(n for n in ast.walk(_arb) if isinstance(n, ast.FunctionDef)
           and n.name == "render_planificacion")
_rtxt = ast.get_source_segment(_src, _rp) or ""
check("3 opciones en el toggle", '["📋 Tablero", "🕐 Día", "👀 Disponibilidad"]' in _rtxt)
check("los valores viejos NO cambiaron (el radio guarda su estado)",
      '"📋 Tablero"' in _rtxt and '"👀 Disponibilidad"' in _rtxt)
check("la vista Día se despacha", "_vista_dia_cuadrilla(" in _rtxt)
check("los días visibles se calculan una vez", "R.dias_con_datos(datos," in _rtxt)
check("y se pasan al tablero", "dias=dias" in _rtxt)

print("\n== 10) tamaños de fuente en la escala de v333 ==")
import re                                                     # noqa: E402
_ESCALA = {11, 12, 13, 14, 16, 18, 21, 26, 34}
_nuevo = "\n".join(ast.get_source_segment(_src, f) or "" for f in
                   (_v2, _cd, next(n for n in ast.walk(_arb)
                                   if isinstance(n, ast.FunctionDef)
                                   and n.name == "_ticks_html")))
_malos = [int(m) for m in re.findall(r"font-size:(\d+)px", _nuevo) if int(m) not in _ESCALA]
check("0 fuera de la escala", _malos, [])
check("...y se miró algo", len(re.findall(r"font-size:(\d+)px", _nuevo)) >= 3, True)

print("\n== 11) keys, nombres libres, compila e importa ==")
_keys = [ast.get_source_segment(_src, kw.value) for n in ast.walk(_arb)
         if isinstance(n, ast.Call) for kw in n.keywords if kw.arg == "key"]
check("0 keys literales repetidas",
      sorted({k for k in _keys if k and _keys.count(k) > 1}), [])
import builtins                                               # noqa: E402
_B = set(dir(builtins)) | {"__file__"}
_mod = set()
for n in _arb.body:
    if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
        _mod.add(n.name)
    elif isinstance(n, (ast.Import, ast.ImportFrom)):
        for x in n.names:
            _mod.add((x.asname or x.name).split(".")[0])
    elif isinstance(n, ast.Assign):
        for t in n.targets:
            for s in ast.walk(t):
                if isinstance(s, ast.Name):
                    _mod.add(s.id)
for _f in ("_vista_dia_cuadrilla", "_control_dias", "_extra_pedidos", "_eje_de",
           "_ticks_html", "_cobertura_hoy", "_panel_kpis", "render_planificacion",
           "_tablero_editable", "_grid_html", "_disponibilidad_html", "_cumplimiento",
           "_asignacion_inteligente"):
    _node = next(n for n in ast.walk(_arb) if isinstance(n, ast.FunctionDef)
                 and n.name == _f)
    asign, usados = set(_mod) | _B, []
    for n in ast.walk(_node):
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
    check(f"{_f} sin nombres libres",
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
