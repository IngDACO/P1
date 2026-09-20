"""v311: detalle de proyecto — titular sin asteriscos, columnas equilibradas,
cronograma ancho SIN romper el PDF de los informes.

Lo critico es lo ultimo: el mismo SVG alimenta la app y los dos informes PDF.
"""
import ast
import importlib
import pathlib
import py_compile
import re
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


print("== 1) el titular ya no enseña los asteriscos ==")
_src = (BASE / "core" / "projects_ui.py").read_text(encoding="utf-8")
_a = ast.parse(_src)
_fn = next(n for n in ast.walk(_a) if isinstance(n, ast.FunctionDef)
           and n.name == "_estado_section")
# Los titulares son las asignaciones a `_tit_html`. Buscarlos por "texto que
# contenga 'puntos por'" tambien pillaba el COMENTARIO que explica el fallo → 5 en
# vez de 3 (la trampa de siempre: mis propios comentarios contados como codigo).
_tits = []
for n in ast.walk(_fn):
    if isinstance(n, ast.Assign) and any(
            isinstance(t, ast.Tuple) and any(getattr(e, "id", "") == "_tit_html"
                                             for e in t.elts) for t in n.targets):
        _v = n.value.elts[0] if isinstance(n.value, ast.Tuple) else n.value

        # ⚠️ CADUCADO en v452 y ACTUALIZADO, no relajado: al pasar el titular por
        # `t()` dos de los tres dejaron de ser una f-string y pasaron a ser una
        # CONCATENACION (`t("You are") + f" <b>..." + t("plan")`), o sea un BinOp.
        # El lector solo entendia JoinedStr/Constant, asi que leia 1 de 3 y daba rojo
        # con el codigo correcto. Lo que la regla de v311 protege NO es la forma del
        # literal: es que el enfasis vaya en `<b>` y NUNCA en `**`, porque el markdown
        # no se procesa dentro de HTML (en pantalla salian los asteriscos). Eso se
        # sigue comprobando igual — solo se ensancha el lector.
        def _txt(nodo):
            if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
                return nodo.value
            if isinstance(nodo, ast.JoinedStr):
                return "".join(x.value for x in nodo.values
                               if isinstance(x, ast.Constant))
            if isinstance(nodo, ast.BinOp) and isinstance(nodo.op, ast.Add):
                return _txt(nodo.left) + _txt(nodo.right)
            if isinstance(nodo, ast.Call):
                # t("...") -> su argumento; y en un METODO (`t("...").replace(...)`)
                # tambien el RECEPTOR, que es donde vive el texto de verdad.
                _r = getattr(nodo.func, "value", None)
                return (_txt(_r) if _r is not None else "") +                        "".join(_txt(x) for x in nodo.args)
            return ""

        _t = _txt(_v)
        if _t:
            _tits.append(_t)
_con_ast = _tits
check("se leyeron los 3 titulares", len(_con_ast), 3)
check("ninguno lleva `**` (no se procesa dentro de HTML)",
      [t for t in _con_ast if "**" in t], [])
check("...y llevan <b>", all("<b>" in t for t in _con_ast))

print("\n== 2) el PDF de los informes NO cambia ==")
from core import schedule as S
import inspect

_sig = inspect.signature(S.schedule_svg)
check("`vw` es parametro", "vw" in _sig.parameters)
check("...con el 760 de SIEMPRE por defecto", _sig.parameters["vw"].default, 760)
# los informes llaman sin `vw` → lienzo identico
for f in ("report.py", "user_report.py"):
    _s = (BASE / "core" / f).read_text(encoding="utf-8")
    _calls = [m for m in re.findall(r"schedule_svg\([^)]*\)", _s)]
    check(f"{f}: ninguna llamada pasa vw", [c for c in _calls if "vw" in c], [])

# Cronograma REAL (`build_schedule`), no un dict a mano: al inventarlo le faltaba
# la clave 'scurve' y el test petaba por su culpa, no por el codigo.
_SCH = S.build_schedule(6, date(2026, 7, 10), {})
_svg_pdf  = S.schedule_svg(_SCH)
_svg_app  = S.schedule_svg(_SCH, vw=1280)
_vb = lambda s: re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', s).groups()
check("PDF: lienzo 760 (como antes)", _vb(_svg_pdf)[0], "760")
check("APP: lienzo 1280", _vb(_svg_app)[0], "1280")
check("el ALTO no cambia con el ancho (solo se ensancha)",
      _vb(_svg_pdf)[1], _vb(_svg_app)[1])
check("area util de barras: de 430 a 950 px",
      (760 - 214 - 116, 1280 - 214 - 116), (430, 950))
check("sin <defs>/<marker> (svglib-compat) en el ancho",
      ("<defs" in _svg_app) or ("<marker" in _svg_app), False)

print("\n== 3) el alto del iframe deja de recortar el pie ==")
for n in (3, 8, 11):
    _acts  = _SCH["activities"][:n]
    _nreal = len(_acts)     # ⚠️ build_schedule(6) da 11 actividades: pedir 13 o 25
    _s = S.schedule_svg({**_SCH, "activities": _acts})   # comparaba n DISTINTOS
    _h = float(re.search(r'viewBox="0 0 [\d.]+ ([\d.]+)"', _s).group(1))
    check(f"n={_nreal}: alto declarado == alto real del SVG",
          float(S.schedule_svg_alto(_nreal)), _h)
check("la formula vieja se quedaba corta (300+n*21 < VH)",
      300 + 13 * 21 < S.schedule_svg_alto(13), True)
check(f"  (13 actividades: antes {300 + 13 * 21}, ahora {S.schedule_svg_alto(13)})", True)

print("\n== 4) el PDF sigue generándose de verdad ==")
try:
    from core.report import _svg_flowable
    _fl = _svg_flowable(_svg_pdf, 450)
    check("svglib convierte el SVG del informe", _fl is not None)
    check("...y con un ancho razonable", getattr(_fl, "width", 0) > 0, True)
except Exception as e:
    check(f"svglib convierte el SVG del informe ({e!r})", False)

print("\n== 5) las columnas ya no enfrentan corto contra largo ==")
_cols = [n for n in ast.walk(_fn) if isinstance(n, ast.Call)
         and getattr(n.func, "attr", "") == "columns"]
check("una sola fila de columnas (antes 2)", len(_cols), 1)
check("...de [3, 2]", [e.value for e in _cols[0].args[0].elts], [3, 2])
# el bloque largo (actividades) y el largo (alarmas) van uno en cada columna
_withs = []
for n in ast.walk(_fn):
    if isinstance(n, ast.With):
        _txt = ast.dump(n)
        # ⚠️ CADUCADO por v440 (i18n F3): la etiqueta pasó al inglés. Lo que la regla
        # protege es que EXISTA una columna con las actividades enfrentada a las
        # alarmas (v311), no cómo se llama.
        _withs.append(("alerts" in _txt,
                       "Actividades" in _txt or "Activities" in _txt))
check("hay una columna con las ACTIVIDADES", any(x[1] for x in _withs))
check("y otra con las ALARMAS", any(x[0] for x in _withs))
# ⚠️ Sobre el codigo SIN comentarios: el unico "Tocaba hoy" que queda es el COMENTARIO
# que explica la fusion, y un grep crudo lo cuenta como codigo vivo (trampa nº2 de
# CLAUDE.md — ya van tres veces en esta tanda).
import io
import tokenize
_sin_com = "".join(t.string for t in
                   tokenize.generate_tokens(io.StringIO(_src).readline)
                   if t.type != tokenize.COMMENT)
check("los dos bloques separados ya no existen",
      "Tocaba hoy" not in _sin_com and "En curso ahora" not in _sin_com)

print("\n== 6) nombres libres + compila + importa ==")
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
        # ⚠️ 20/09/2026 (v502): añadia los ARGUMENTOS de un `def` anidado pero nunca su
        # NOMBRE, asi que cualquier funcion auxiliar definida dentro de _estado_section
        # salia denunciada como «nombre libre» en todas sus llamadas. Codigo sano acusado
        # por el chequeo — la familia de la trampa nº3 (lambdas, morsa, __file__), que ya
        # documenta que este barrido se autoengaña si no se contemplan las ligaduras.
        # Lo destapo `_dueno` en v502; habria pasado con cualquier `def` anidado.
        asign.add(getattr(n, "name", ""))
        for x in getattr(n.args, "args", []):
            asign.add(x.arg)
check("_estado_section sin nombres libres",
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
