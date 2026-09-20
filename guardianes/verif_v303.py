"""v303: HOME mas denso (KPIs con contexto junto al mapa, resumen compacto, 3 columnas)
       + fix de los deep-links del resumen del dia.

Chequeos que NO son "compila": el AST de los saltos de navegacion contra los IDs
reales de home_ui, los pies de las tarjetas contra el ancho medido, y que no quede
ni un resto del toggle borrado.
"""
import ast
import importlib
import pathlib
import py_compile
import sys
import tokenize

sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")

ok = True


def check(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"           esperado: {esp!r}")


def _sin_comentarios(ruta):
    """Codigo SIN comentarios ni docstrings (trampa nº2 de v289-v299: un grep cuenta
    mis propios comentarios como si el simbolo siguiera vivo)."""
    out = []
    with open(ruta, "rb") as fh:
        for tok in tokenize.tokenize(fh.readline):
            if tok.type == tokenize.COMMENT:
                continue
            out.append(tok.string)
    src = "\n".join(out)
    # fuera docstrings
    arbol = ast.parse(pathlib.Path(ruta).read_text(encoding="utf-8"))
    docs = set()
    for n in ast.walk(arbol):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            d = ast.get_docstring(n, clean=False)
            if d:
                docs.add(d)
    for d in docs:
        src = src.replace(d, "")
    return src


print("== 1) los IDs de sub-pestana existen DE VERDAD (el bug que cazamos) ==")
from core import home_ui as H

# ⚠️ La union de los TRES roles (v478): `navegar()` se usa tambien desde pantallas del
# CAMPO —el atajo de Fichaje a «avisar de una baja»— y su destino no existe en la nav
# del admin, que era contra la unica que se validaba.
# ⚠️ Esto ENSANCHA el universo a proposito: un destino valido solo para el campo pasaria
# aunque se llamara desde una pantalla de admin. Se asume, porque lo que este chequeo
# existe para cazar es el destino que no existe para NADIE —una errata o un ID
# renombrado, que navega a ninguna parte SIN dar error (el fallo real de v303)— y de
# que rol se ejecuta cada call-site no es decidible estaticamente.
_IDS = {}
for _tabla in (H._SUBSECCIONES, H._SUBSECCIONES_CAMPO, H._SUBSECCIONES_OWNER):
    for _sec, _v in _tabla.items():
        _IDS.setdefault(_sec, [])
        _IDS[_sec] += [i for i, _d in _v[1] if i not in _IDS[_sec]]
_SECS = {k for _t in (H._SECCIONES, H._SECCIONES_CAMPO, H._SECCIONES_OWNER)
         for k, _l in _t}
print(f"  secciones={sorted(_SECS)}")

# (a) los saltos con literales: _ir_a(...) / navegar(...) en todo el repo
_saltos = []
for p in sorted(BASE.rglob("*.py")):
    arbol = ast.parse(p.read_text(encoding="utf-8"))
    for n in ast.walk(arbol):
        if not isinstance(n, ast.Call):
            continue
        _nom = (n.func.id if isinstance(n.func, ast.Name) else
                n.func.attr if isinstance(n.func, ast.Attribute) else "")
        if _nom not in ("_ir_a", "navegar"):
            continue
        args = [a.value if isinstance(a, ast.Constant) else None for a in n.args]
        if len(args) >= 2 and isinstance(args[0], str) and isinstance(args[1], str):
            _saltos.append((p.name, n.lineno, args[0], args[1]))

# (b) las tuplas `inds` del resumen del dia: (slug, icon, lbl, urg, cnt, SECCION, SUB, ...)
_pu = ast.parse((BASE / "core" / "projects_ui.py").read_text(encoding="utf-8"))
_fn = next(n for n in ast.walk(_pu) if isinstance(n, ast.FunctionDef)
           and n.name == "_resumen_del_dia")
_inds = 0
for n in ast.walk(_fn):
    if isinstance(n, ast.Tuple) and len(n.elts) >= 8:
        e5, e6 = n.elts[5], n.elts[6]
        if isinstance(e5, ast.Constant) and isinstance(e6, ast.Constant) \
                and isinstance(e5.value, str) and isinstance(e6.value, str):
            _saltos.append(("projects_ui.py:inds", n.lineno, e5.value, e6.value))
            _inds += 1
check("los 9 indicadores del resumen se pudieron LEER", _inds, 9)   # no pasar en vacio

# ⚠️ v305: el reparto en filas usa `zip(st.columns(N), fila)`, y `zip` TRUNCA: si una
# fila tiene mas elementos que columnas, los sobrantes desaparecen SIN ERROR. Se
# comprueba que ninguna fila supere el numero de columnas y que las filas cubran los 9.
_cols = [c.args[0].value for c in ast.walk(_fn) if isinstance(c, ast.Call)
         and getattr(c.func, "attr", "") == "columns" and c.args
         and isinstance(c.args[0], ast.Constant)]
_cortes = [(s.slice.lower.value if s.slice.lower else 0,
            s.slice.upper.value if s.slice.upper else 9)
           for s in ast.walk(_fn) if isinstance(s, ast.Subscript)
           and isinstance(s.slice, ast.Slice)
           and isinstance(s.value, ast.Name) and s.value.id == "inds"]
check("el reparto en filas se pudo LEER", bool(_cols) and bool(_cortes), True)
check("ninguna fila tiene mas indicadores que columnas (zip truncaria)",
      [(a, b) for (a, b) in _cortes if (b - a) > max(_cols)], [])
check("las filas cubren los 9 indicadores, sin huecos ni solapes",
      sorted({i for a, b in _cortes for i in range(a, b)}), list(range(9)))
print(f"         filas={_cortes} · columnas={_cols}")
check("hay saltos que revisar (no es una lista vacia)", len(_saltos) >= 12, True)

_malos = [(f, l, s, sub) for (f, l, s, sub) in _saltos
          if s not in _SECS or (s in _IDS and sub not in _IDS[s])]
check("TODOS los saltos apuntan a un ID que existe", _malos, [])
print(f"         (revisados {len(_saltos)} saltos con destino literal)")

print("\n== 2) los KPIs: contexto sin lecturas nuevas y pie que CABE ==")
_src_pu = (BASE / "core" / "projects_ui.py").read_text(encoding="utf-8")
_fk = next(n for n in ast.walk(_pu) if isinstance(n, ast.FunctionDef)
           and n.name == "render_kpis")
# las llamadas de dentro: solo _kpis + columns/button/_ir_a → NADA de Sheets
_llam = sorted({(n.func.id if isinstance(n.func, ast.Name) else n.func.attr)
                for n in ast.walk(_fk) if isinstance(n, ast.Call)
                and isinstance(n.func, (ast.Name, ast.Attribute))})
check("render_kpis solo llama a _kpis (0 lecturas nuevas)",
      [c for c in _llam if c in ("list_projects", "project_hours_bulk",
                                 "group_hours", "open_counts_all", "group_digest")], [])
check("...y usa _kpis", "_kpis" in _llam)

# ⚠️ El limite del pie es de ANCHO (93 px utiles), no de caracteres: 'media de 12 obras'
# y 'los 12 en retraso' tienen 17 los dos y miden 94 px y 84 px. Contar caracteres daria
# un OK falso. Asi que se comprueba contra la lista de patrones MEDIDOS en el navegador:
# si aparece un pie nuevo, el test falla y hay que ir a medirlo, no a estimarlo.
import re
from core import projects_ui as _PU
_MEDIDOS = {           # patron (numeros -> #) : px medidos con el CSS real de theme.py
    # ⚠️ v441 (i18n): los pies pasaron al ingles y hubo que MEDIRLOS otra vez, que es lo
    # que este chequeo exige — no estimarlos. Y la sonda se CALIBRO antes de fiarse de
    # ella (trampa nº12): midiendo los pies españoles de arriba, este banco lee +2..+6 px
    # respecto al de v303, asi que se eligieron textos con margen para que ese sesgo no
    # decida. Los dos primeros candidatos NO cabian: "nobody clocked in" 98 y
    # "across the company" 106, sobre 93 utiles.
    "of # in total": 68, "none yet": 47, "all up to date": 71,
    "all # behind": 69, "# behind": 54,
    "no progress yet": 83, "of # jobs": 53, "of # job": 41,
    "no hours yet": 67, "company-wide": 79,
}
_UTIL = 93
_casos = [(0, 0, 0, 0), (0, 0, 7, 0), (1, 0, 1, 50), (2, 2, 2, 0), (3, 1, 5, 20),
          (12, 5, 20, 100), (99, 99, 99, 100), (12, 12, 12, 37), (1, 1, 1, 99)]
_vistos = set()
for _a, _r, _t, _av in _casos:
    for _h in (0, 1234):
        for _p in _PU._kpi_pies({"activos": _a, "riesgo": _r, "total": _t,
                                 "avg": _av, "horas": _h}):
            _vistos.add(re.sub(r"\d+", "#", _p))
check("se generaron pies que revisar (no es un set vacio)", len(_vistos) >= 8, True)
check("todo pie posible esta MEDIDO y cabe en 93 px",
      sorted(p for p in _vistos if _MEDIDOS.get(p, 999) > _UTIL), [])
print(f"         {len(_vistos)} pies distintos, el mas ancho "
      f"{max(_MEDIDOS[p] for p in _vistos if p in _MEDIDOS)} px de {_UTIL}")

print("\n== 3) el toggle de la columna derecha se fue ENTERO ==")
for _f in ("home_ui.py", "projects_ui.py"):
    _code = _sin_comentarios(BASE / "core" / _f)
    check(f"{_f}: 0 restos de home_right_view", "home_right_view" not in _code)
print("\n== 4) el reparto de HOME ==")
_h = ast.parse((BASE / "core" / "home_ui.py").read_text(encoding="utf-8"))
_rh = next(n for n in ast.walk(_h) if isinstance(n, ast.FunctionDef)
           and n.name == "render_home")
# ⚠️ por AST, no por texto: `_sin_comentarios` une tokens con \n, asi que buscar
# "def render_home" como cadena contigua NO encuentra nada (falso "OK" en potencia).
check("render_home ya no instancia ningun radio",
      [n for n in ast.walk(_rh) if isinstance(n, ast.Call)
       and getattr(n.func, "attr", "") == "radio"], [])
_cols = [n for n in ast.walk(_rh) if isinstance(n, ast.Call)
         and getattr(n.func, "attr", "") == "columns"]
check("render_home crea UNA sola fila de columnas", len(_cols), 1)
check("...de TRES columnas", len(_cols[0].args[0].elts), 3)
_atrib = {n.attr for n in ast.walk(_rh) if isinstance(n, ast.Attribute)}
check("...y llama a render_kpis", "render_kpis" in _atrib)
check("...y sigue llamando a render_group_header", "render_group_header" in _atrib)

print("\n== 5) nombres libres en lo tocado (chequeo de v125) ==")
# ⚠️ Los nombres de MODULO se sacan del propio AST, no de una lista escrita a mano:
# con la lista manual, cualquier helper nuevo sale como falso positivo (paso con
# `_kpi_pies`) y la tentacion es apuntarlo a la lista en vez de mirar si es real.
import builtins
_BUILTINS = set(dir(builtins)) | {"__file__", "__name__"}


def _nivel_modulo(arbol):
    out = set()
    for n in arbol.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(n.name)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                out.add((a.asname or a.name).split(".")[0])
        elif isinstance(n, (ast.Assign, ast.AnnAssign)):
            for t in ([n.target] if isinstance(n, ast.AnnAssign) else n.targets):
                for sub in ast.walk(t):
                    if isinstance(sub, ast.Name):
                        out.add(sub.id)
        elif isinstance(n, ast.Try):            # imports perezosos en try/except
            for sub in ast.walk(n):
                if isinstance(sub, (ast.Import, ast.ImportFrom)):
                    for a in sub.names:
                        out.add((a.asname or a.name).split(".")[0])
    return out


def libres(fn, conocidos):
    asign, usados = set(conocidos), []
    for n in ast.walk(fn):
        if isinstance(n, ast.arg):
            asign.add(n.arg)
        elif isinstance(n, ast.Name):
            (asign.add(n.id) if isinstance(n.ctx, ast.Store) else usados.append(n.id))
        elif isinstance(n, ast.NamedExpr) and isinstance(n.target, ast.Name):
            asign.add(n.target.id)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                asign.add((a.asname or a.name).split(".")[0])
        elif isinstance(n, ast.ExceptHandler) and n.name:
            asign.add(n.name)
        elif isinstance(n, (ast.FunctionDef, ast.Lambda)):
            for a in getattr(n.args, "args", []):
                asign.add(a.arg)
            if isinstance(n, ast.FunctionDef):
                asign.add(n.name)
    return sorted({u for u in usados if u not in asign and u not in _BUILTINS})


for mod, arbol, nombres in (("projects_ui", _pu, ("render_group_header", "render_kpis",
                                                  "_kpi_pies", "_resumen_del_dia")),
                            ("home_ui", _h, ("render_home", "render_topbar",
                                             "_mapa_proyectos", "sidebar_menu"))):
    _mn = _nivel_modulo(arbol)
    for nm in nombres:
        f = next(n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef)
                 and n.name == nm)
        check(f"{mod}.{nm} sin nombres libres", libres(f, _mn), [])

print("\n== 6) compila e importa de verdad ==")
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

from core import projects_ui as PU
check("render_kpis existe y es llamable", callable(getattr(PU, "render_kpis", None)))
check("el CSS de 3 lineas esta en el sistema de diseno",
      'p:nth-child(2):not(:last-child)' in (BASE / "core" / "theme.py").read_text(encoding="utf-8"))

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
