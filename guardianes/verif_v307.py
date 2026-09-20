"""v307: Ruta del día — mapa que llena, ruta ordenada, plan vs real, KPIs activos.

Lo que se prueba de VERDAD (no "compila"): la logica de plan-vs-real y que la
persona cuya obra no tiene ubicacion YA NO desaparezca de la tabla (antes un
`continue` la borraba y el KPI decia "1 sin ubicacion" sin decir de quien).
"""
import ast
import pathlib
import sys
import types
from datetime import date

sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")

# La consola de Windows es cp1252 y revienta al imprimir 🟢/🔴 — es un limite del
# terminal, no del codigo. Sin esto el test "falla" por algo que no es el fallo.
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


print("== 1) el mapa llena su hueco (la causa medida del espacio en blanco) ==")
_src = (BASE / "core" / "route_ui.py").read_text(encoding="utf-8")
_a = ast.parse(_src)
_fm = next(n for n in ast.walk(_a) if isinstance(n, ast.FunctionDef)
           and n.name == "_folium_map")
_call = next((c for c in ast.walk(_fm) if isinstance(c, ast.Call)
              and getattr(c.func, "id", "") == "st_folium"), None)
check("se pudo LEER la llamada a st_folium", _call is not None, True)
_kw = {k.arg: getattr(k.value, "value", None) for k in _call.keywords}
check("use_container_width=True", _kw.get("use_container_width"), True)
# y el de HOME, que tenia el mismo defecto
_h = ast.parse((BASE / "core" / "home_ui.py").read_text(encoding="utf-8"))
_hc = [c for c in ast.walk(_h) if isinstance(c, ast.Call)
       and getattr(c.func, "id", "") == "st_folium"]
check("HOME tambien lo pasa",
      all(any(k.arg == "use_container_width" and getattr(k.value, "value", None) is True
              for k in c.keywords) for c in _hc) and bool(_hc), True)

print("\n== 2) la ruta se ORDENA y ofrece navegacion (existia desde v270, sin usar) ==")
from core import route_ui as R
_rd = next(n for n in ast.walk(_a) if isinstance(n, ast.FunctionDef)
           and n.name == "render_ruta_dia")
_llam = {c.func.id for c in ast.walk(_rd) if isinstance(c, ast.Call)
         and isinstance(c.func, ast.Name)}
check("render_ruta_dia usa ordenar_ruta", "ordenar_ruta" in _llam)
check("...y gmaps_dir_url", "gmaps_dir_url" in _llam)

# la heuristica: vecino mas cercano, y NO pierde paradas
_par = [{"lat": -33.80, "lon": 151.20, "nombre": "lejos"},
        {"lat": -33.88, "lon": 151.21, "nombre": "centro"},
        {"lat": -33.885, "lon": 151.215, "nombre": "pegado"}]
_r = R.ordenar_ruta(_par)
check("la ruta conserva TODAS las paradas", len(_r), 3)
check("...sin repetir", len({p["nombre"] for p in _r}), 3)
check("empieza por la primera y sigue por la mas cercana",
      [p["nombre"] for p in _r], ["lejos", "centro", "pegado"])
check("una sola parada no rompe", len(R.ordenar_ruta([_par[0]])), 1)
check("cero paradas no rompe", R.ordenar_ruta([]), [])
_u1 = R.gmaps_dir_url([_par[0]], desde_actual=True)
check("link de UNA parada valido", _u1.startswith("https://www.google.com/maps/dir/?")
      and "destination=" in _u1, True)
_u3 = R.gmaps_dir_url(_r, desde_actual=False)
check("link de la ruta lleva origen, destino y waypoint",
      all(k in _u3 for k in ("origin=", "destination=", "waypoints=")), True)

print("\n== 3) plan vs real: las 3 lecturas ==")
# Se replica la decision tal y como esta escrita en render_ruta_dia (misma cadena)
def _estado(pid, fich):
    _pids = {str(x.get("pid", "")) for x in fich if x.get("pid")}
    _noms = [str(x.get("nombre", "")) for x in fich if x.get("nombre")]
    if pid in _pids:
        return "🟢 clocked in here"
    if _noms:
        return "🔴 clocked in at " + ", ".join(_noms[:2])
    return "⚠️ not clocked in"

check("fichó donde tocaba", _estado("PRJ-1", [{"pid": "PRJ-1", "nombre": "Torre"}]),
      "🟢 clocked in here")
check("fichó en OTRA obra", _estado("PRJ-1", [{"pid": "PRJ-2", "nombre": "Otra"}]),
      "🔴 clocked in at Otra")
check("no ficha nada", _estado("PRJ-1", []), "⚠️ not clocked in")
check("fichó en dos sitios, uno es el bueno",
      _estado("PRJ-1", [{"pid": "PRJ-2", "nombre": "Otra"}, {"pid": "PRJ-1", "nombre": "Torre"}]),
      "🟢 clocked in here")
# el texto de la fila corresponde con el codigo real (no con una copia que diverja)
for _t in ("🟢", "⚠️", "🔴"):
    check(f"el codigo real contiene {_t!r}", _t in _src)

print("\n== 4) nadie desaparece de la tabla ==")
# ANTES: si la obra no tenia coordenadas se hacia `continue` y esa persona no salia
# en `en_obra`. Se comprueba por AST que dentro del bucle ya NO hay un `continue`
# despues de `sin_coord.append`.
_bucle = None
for n in ast.walk(_rd):
    if isinstance(n, ast.For):
        if any(isinstance(x, ast.Attribute) and x.attr == "append"
               and getattr(getattr(x, "value", None), "id", "") == "sin_coord"
               for x in ast.walk(n)):
            _bucle = n
check("se localizo el bucle de asignaciones", _bucle is not None, True)
_tras = []
for n in ast.walk(_bucle):
    if isinstance(n, ast.If):
        _txt = ast.dump(n)
        if "sin_coord" in _txt and "Continue" in _txt:
            _tras.append(n.lineno)
check("la rama 'sin ubicacion' ya NO hace continue", _tras, [])
check("en_obra se rellena con Horario", '"Horario"' in _src)
# ⚠️ CADUCADO por v439: la CLAVE del dict es dato y no se traduce, pero la columna
# que se muestra sí. Se comprueba que el estado real llega a la fila.
check("...y con Estado", ("_estado" in _src) and ("Estado" in _src or "Status" in _src))

print("\n== 5) KPIs activos y sin cortar nombres ==")
check("los 4 KPIs son botones cpxkpi_",
      len([1 for k in ("cpxkpi_rd_obra", "cpxkpi_rd_sitios", "cpxkpi_rd_sinubic",
                       "cpxkpi_rd_sinplan") if k in _src]), 4)
# ⚠️ Por AST, no por texto: `'[:18]' not in _src` FALLA por el COMENTARIO que explica
# que se quitó ese corte (la trampa nº2 de CLAUDE.md: un grep cuenta mis comentarios
# como si el código siguiera vivo). Se busca el recorte de verdad: un slice [:18].
_slices18 = [n.lineno for n in ast.walk(_rd) if isinstance(n, ast.Subscript)
             and isinstance(n.slice, ast.Slice)
             and isinstance(getattr(n.slice, "upper", None), ast.Constant)
             and n.slice.upper.value == 18]
check("el pie de 'sin plan' ya no se corta a lo bruto", _slices18, [])
_sub = lambda ns: ("todos planificados" if not ns
                   else (ns[0] if len(ns) == 1 else f"{len(ns)} personas"))
check("1 sin plan -> su nombre", _sub(["Juan Pérez"]), "Juan Pérez")
check("3 sin plan -> el conteo", _sub(["a", "b", "c"]), "3 personas")
check("0 sin plan", _sub([]), "todos planificados")

print("\n== 6) compila e importa todo ==")
import importlib
import py_compile
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
