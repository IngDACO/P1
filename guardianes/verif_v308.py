"""v308: Fichaje — fix del nombre guardado, semana en curso y dos columnas.

Lo importante: (a) que a la hoja vuelva a ir el NOMBRE del proyecto y no la
etiqueta con el ID, (b) que la semana sea NATURAL (lunes→hoy) y no una ventana
movil, y (c) que la reindentacion no haya movido nada de sitio.
"""
import ast
import importlib
import pathlib
import py_compile
import sys
from datetime import datetime, timedelta

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


print("== 1) a la hoja va el NOMBRE, no la etiqueta (el fallo de v306) ==")
_src = (BASE / "core" / "timeclock_ui.py").read_text(encoding="utf-8")
_a = ast.parse(_src)
_fn = next(n for n in ast.walk(_a) if isinstance(n, ast.FunctionDef)
           and n.name == "render_timeclock_tab")
# ⚠️ v480 · Esto afirmaba la FORMA («0 `next(...)`, 3 `_nom_de.get`») y caducó en
# cuanto apareció un cuarto sitio donde fichar. El fallo de v306 no era usar `next`:
# era que el NOMBRE escrito en la hoja saliera de la ETIQUETA del desplegable (que
# lleva el ID detrás con homónimos), dejando fichajes con un nombre inventado. Ahora
# se afirma ESO, y sirve para una llamada o para diez.
_vars_nom = {t.id for n in ast.walk(_fn) if isinstance(n, ast.Assign)
             for t in n.targets if isinstance(t, ast.Name)
             if isinstance(n.value, ast.Call)
             and getattr(n.value.func, "attr", "") == "get"
             and getattr(getattr(n.value.func, "value", None), "id", "") == "_nom_de"}
_fichadas = [n for n in ast.walk(_fn) if isinstance(n, ast.Call)
             and getattr(n.func, "attr", "") == "fichar_proyecto"]
check("hay al menos un sitio donde se ficha", len(_fichadas) >= 1, True)
_mal = [n.lineno for n in _fichadas
        if not (len(n.args) >= 2 and isinstance(n.args[1], ast.Name)
                and n.args[1].id in _vars_nom)]
check("TODA llamada a fichar_proyecto toma el nombre de `_nom_de`", _mal, [])
# ⚠️ Sonda validada contra el fallo de v306 reconstruido: si no ve ESE caso, su cero
# no vale nada (trampa nº12).
_p = ast.parse("def f():\n _x = next(iter(idmap))\n"
               " timeclock.fichar_proyecto(nombre, _x, g, u, pid)\n")
_pf = [n for n in ast.walk(_p) if isinstance(n, ast.FunctionDef)][0]
_pv = {t.id for n in ast.walk(_pf) if isinstance(n, ast.Assign)
       for t in n.targets if isinstance(t, ast.Name)
       if isinstance(n.value, ast.Call)
       and getattr(n.value.func, "attr", "") == "get"
       and getattr(getattr(n.value.func, "value", None), "id", "") == "_nom_de"}
_pm = [n.lineno for n in ast.walk(_pf) if isinstance(n, ast.Call)
       and getattr(n.func, "attr", "") == "fichar_proyecto"
       and not (len(n.args) >= 2 and isinstance(n.args[1], ast.Name)
                and n.args[1].id in _pv)]
check("la sonda VE el fallo de v306 reconstruido (control)", bool(_pm), True)
check("`_nom_de` se construye con ID->Nombre", "_nom_de = {str(p.get(\"ID\"" in _src)

print("\n== 2) 'cambiar de proyecto' excluye el actual por ID ==")
check("usa proyecto_id de la sesion abierta", '_pid_actual = str(prj.get("proyecto_id"' in _src)
# simulacion de la expresion tal cual esta escrita
def _otros(idmap, pid_actual, nombre_guardado):
    return {k: v for k, v in idmap.items()
            if (v != pid_actual if pid_actual else k != nombre_guardado)}

_IDMAP = {"prueba (PRJ-0007)": "PRJ-0007", "prueba (PRJ-0008)": "PRJ-0008",
          "Torre Norte": "PRJ-0001"}
_r = _otros(_IDMAP, "PRJ-0007", "prueba")
check("con homonimos NO se ofrece el proyecto actual",
      sorted(_r.values()), ["PRJ-0001", "PRJ-0008"])
check("...y si el fichaje es viejo (sin ID) cae al nombre",
      sorted(_otros({"Torre Norte": "PRJ-0001", "Otra": "PRJ-0002"},
                    "", "Torre Norte").values()), ["PRJ-0002"])

print("\n== 3) la semana es NATURAL (lunes → hoy) ==")
from core import timeclock as T

_HOY = T.clock.now().date()
_LUNES = _HOY - timedelta(days=_HOY.weekday())


def _fila(dia, h_ini, horas, tipo, proy=""):
    ci = datetime.combine(dia, datetime.min.time()) + timedelta(hours=h_ini)
    co = ci + timedelta(hours=horas)
    return {"Name": "Ana", "User": "ana", "Group": "g", "Project": proy,
            "Clock In": ci.strftime(T.FMT), "Clock Out": co.strftime(T.FMT),
            "Hours": f"{horas:.2f}", "Type": tipo, "ProjectID": ""}


_ROWS = [
    _fila(_LUNES, 8, 8, T.TIPO_GENERAL),                       # lunes de ESTA semana
    _fila(_LUNES, 8, 6, T.TIPO_PROYECTO, "Torre"),
    _fila(_LUNES - timedelta(days=3), 8, 8, T.TIPO_GENERAL),   # semana ANTERIOR
    _fila(_LUNES - timedelta(days=7), 8, 8, T.TIPO_GENERAL),   # lunes pasado
]
_orig = T._cached_records
T._cached_records = lambda: _ROWS
try:
    s = T.resumen_semana("Ana", "g", "ana")
finally:
    T._cached_records = _orig
check("suma SOLO la semana en curso (8 h, no 24)", s["general"], 8.0)
check("...y lo imputado a proyecto", s["proyecto"], 6.0)
check("...y cuenta 1 dia con jornada", s["dias"], 1)
check("un lunes NO arrastra el viernes anterior (ventana movil daria 16+)",
      s["general"] < 16, True)

print("\n== 4) la reindentacion no movio nada de sitio ==")
_cols = [n for n in ast.walk(_fn) if isinstance(n, ast.Call)
         and getattr(n.func, "attr", "") == "columns"]
check("hay columnas en la pantalla", len(_cols) >= 1, True)
_withs = {}
for n in _fn.body:
    if isinstance(n, ast.With):
        it = n.items[0].context_expr
        _withs[getattr(it, "id", getattr(it, "attr", "?"))] = sorted(
            {k.value.value for x in ast.walk(n) if isinstance(x, ast.Call)
             for k in x.keywords
             if k.arg == "key" and isinstance(k.value, ast.Constant)})
check("la Jornada se queda con SUS botones",
      _withs.get("col_jor"), ["tc_gen_in", "tc_gen_out"])
# ⚠️ v480 · Era una lista a mano y caducó al añadir `tc_prj_solo`. Lo que protege es
# que la reindentación no haya movido un widget de columna, y eso se DERIVA: en la
# columna del Proyecto solo puede haber keys suyas, y ninguna puede estar en las dos.
_kp = _withs.get("_prj_ctx") or []
_kj = _withs.get("col_jor") or []
check("el Proyecto solo tiene keys suyas",
      [k for k in _kp if not (k.startswith("tc_prj") or k.startswith("tc_switch"))], [])
check("y ninguna key está en las dos columnas", sorted(set(_kp) & set(_kj)), [])
check("la columna del Proyecto no se quedó vacía", len(_kp) >= 4, True)
# ninguna key duplicada en toda la pantalla (una reindentacion mala puede duplicar)
_keys = [k.value.value for x in ast.walk(_fn) if isinstance(x, ast.Call)
         for k in x.keywords if k.arg == "key" and isinstance(k.value, ast.Constant)]
check("0 keys de widget duplicadas", [k for k in set(_keys) if _keys.count(k) > 1], [])

print("\n== 5) el estado ya no es una tarjeta KPI ==")
check("las tarjetas son 4 y ninguna es 'Estado'",
      '_tarjeta("Estado"' not in _src)
check("hay franja de estado", 'border-left:4px solid {_col}' in _src)
# ⚠️ CADUCADO por v439 (i18n F2): la etiqueta pasó al inglés vía t(). Lo que la
# regla protege es que la tarjeta de la SEMANA exista (resumen_semana, v308).
check("y tarjeta de la semana",
      '_tarjeta(t("This week")' in _src or '_tarjeta("Esta semana"' in _src)

print("\n== 6) nombres libres + compila + importa ==")
import builtins
_B = set(dir(builtins)) | {"__file__"}


def _mod_names(arbol):
    out = set()
    for n in arbol.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(n.name)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for x in n.names:
                out.add((x.asname or x.name).split(".")[0])
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                for s in ast.walk(t):
                    if isinstance(s, ast.Name):
                        out.add(s.id)
    return out


def libres(fn, conocidos):
    asign, usados = set(conocidos), []
    for n in ast.walk(fn):
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
            for x in getattr(n.args, "args", []):
                asign.add(x.arg)
    return sorted({u for u in usados if u not in asign and u not in _B})


check("render_timeclock_tab sin nombres libres", libres(_fn, _mod_names(_a)), [])
_tc = ast.parse((BASE / "core" / "timeclock.py").read_text(encoding="utf-8"))
_rs = next(n for n in ast.walk(_tc) if isinstance(n, ast.FunctionDef)
           and n.name == "resumen_semana")
check("resumen_semana sin nombres libres", libres(_rs, _mod_names(_tc)), [])

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
