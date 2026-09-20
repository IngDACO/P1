"""v299 · Fase 3: la nav VIEJA se borró. Verificacion final."""
import sys, ast, re, pathlib, inspect
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st

BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")
ok = True
def check(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"         esperado: {esp!r}")

src_app = (BASE / "app.py").read_text(encoding="utf-8")

print("== A) no queda NADA de la nav vieja ==")
# ⚠️ Sobre el CODIGO, no sobre el texto: mis propios comentarios mencionan
# `main_nav` y COPEX al documentar lo borrado, y un grep crudo los cuenta como
# si siguieran vivos (mismo falso positivo que en v296).
import io, tokenize
def _sin_comentarios(t):
    out = []
    for tok in tokenize.generate_tokens(io.StringIO(t).readline):
        if tok.type != tokenize.COMMENT:
            out.append(tok.string)
    return "\n".join(out)
_cod = _sin_comentarios(src_app)
for n in ("_L_SURVEY", "_L_OWNER", "_L_GRUPO", "_NAV_DISPLAY", "_HERR",
          "main_nav", "_nav_pending", "_SHELL_NUEVA", "render_owner_panel"):
    check(f"sin {n} (en CODIGO)", not re.search(rf"\b{n}\b", _cod))
# La marca COPEX SIGUE VIVA a proposito (titulo, favicon, PWA y la cabecera del
# SIDEBAR). Lo que murio es el BANNER principal: antes habia 2 bloques con la
# marca, ahora debe quedar 1 (el del sidebar).
check("solo queda 1 banner de marca (el del sidebar)",
      src_app.count("Elevator Survey Analyzer"), 1)
check("...y el sidebar lo conserva", "Cabecera COPEX" in src_app)
au = (BASE / "core" / "auth_ui.py").read_text(encoding="utf-8")
check("render_owner_panel borrada", "def render_owner_panel" not in au)
check("...pero render_owner_seccion vive", "def render_owner_seccion" in au)

print("\n== B) `_nav_pending` no tiene ni lectores ni escritores ==")
_esc = []
for f in list((BASE / "core").glob("*.py")) + [BASE / "app.py"]:
    t = f.read_text(encoding="utf-8")
    if re.search(r'["\']_nav_pending["\']', t):
        _esc.append(f.name)
check("0 referencias en todo el repo", _esc, [])

print("\n== C) los DOS flujos convertidos siguen vivos ==")
sv = (BASE / "core" / "survey_ui.py").read_text(encoding="utf-8")
check("survey: 'Abrir proyecto' usa _admin_nav_pending",
      "_admin_nav_pending" in sv and '"administracion", "📁 Proyectos"' in sv)
check("...y sigue fijando el proyecto", "_prjsel_pending" in sv)
ts = (BASE / "core" / "tool_save_ui.py").read_text(encoding="utf-8")
check("reabrir calculo usa _admin_nav_pending",
      '"_admin_nav_pending"] = ("herramientas"' in ts)

from core import home_ui as H
pu = (BASE / "core" / "projects_ui.py").read_text(encoding="utf-8")
_m = re.search(r"_CALC_NAV\s*=\s*\{(.*?)\}", pu, re.S)
_subs_ids = [i for i, _ in H._SUBSECCIONES["herramientas"][1]]
_calc_ids = re.findall(r':\s*"([^"]+)"', _m.group(1))
check("_CALC_NAV apunta a sub-pestañas REALES de Herramientas",
      [i for i in _calc_ids if i not in _subs_ids], [])
print(f"         {_calc_ids}")

print("\n== D) los 3 roles siguen resolviendo su nav ==")
def como(rol):
    st.session_state["auth"] = {"rol": rol, "usuario": "u", "grupo": "g", "nombre": "N"}
# ⚠️ CADUCADO en v430 y actualizado (regla v385, trampa nº16): el numero se fijaba a
# mano (campo=6) y v430 le anade «ausencias», asi que se ponia rojo por un cambio
# deliberado. Lo que la regla protege es que CADA ROL resuelva SU nav y no la de
# otro — el numero se DERIVA ahora de la propia constante, que es lo que no puede
# divergir; y se comprueba ademas que los tres sean distintos entre si.
_ROLNAV = {"administrator": H._SECCIONES, "field": H._SECCIONES_CAMPO,
           "owner": H._SECCIONES_OWNER}
for rol, cte in _ROLNAV.items():
    como(rol)
    check(f"{rol}: resuelve SU nav ({len(cte)} secciones)",
          [k for k, _ in H._secciones()], [k for k, _ in cte])
check("y las tres navs son distintas entre si",
      len({tuple(k for k, _ in c) for c in _ROLNAV.values()}), 3)

print("\n== E) menor privilegio ante un Rol desconocido ==")
como("typo_en_la_hoja")
check("cae a la nav del CAMPO, no a la del admin",
      [k for k, _ in H._secciones()], [k for k, _ in H._SECCIONES_CAMPO])
check("y sus subsecciones también", H._subsecciones(), H._SUBSECCIONES_CAMPO)

print("\n== F) app.py: la shell es el unico camino ==")
a = ast.parse(src_app)
check("render_topbar se llama", "render_topbar" in src_app)
check("render_admin_content se llama", "render_admin_content" in src_app)
check("ya no hay st.stop() de la shell (nada debajo)",
      src_app.count("_home.render_admin_content"), 1)
print(f"         app.py: {len(src_app.splitlines())} lineas")

print("\n== G) compila e importa ==")
import py_compile, importlib
mods = sorted((BASE / "core").glob("*.py"))
for p in mods:
    py_compile.compile(str(p), doraise=True)
py_compile.compile(str(BASE / "app.py"), doraise=True)
malos = []
for p in mods:
    try:
        importlib.import_module("core." + p.stem)
    except Exception as e:
        malos.append((p.stem, repr(e)[:70]))
check(f"{len(mods)-len(malos)}/{len(mods)} modulos + app.py", malos, [])

print("\n== H) nombres libres en app.py (nivel de modulo) ==")
import builtins
# ⚠️ `__file__` es un global del modulo y el operador MORSA (`if x := ...`) es una
# asignacion que mi recorrido no contaba: los dos salian como "sin definir".
definidos = set(dir(builtins)) | {"__file__", "__name__", "__doc__"}
for n in ast.walk(a):
    if isinstance(n, ast.NamedExpr) and isinstance(n.target, ast.Name):
        definidos.add(n.target.id)
    if isinstance(n, (ast.Import, ast.ImportFrom)):
        definidos |= {(al.asname or al.name.split(".")[0]) for al in n.names}
    elif isinstance(n, ast.Assign):
        definidos |= {t.id for t in n.targets if isinstance(t, ast.Name)}
    elif isinstance(n, (ast.FunctionDef, ast.ClassDef)):
        definidos.add(n.name)
    elif isinstance(n, (ast.For, ast.comprehension)):
        tgt = getattr(n, "target", None)
        if isinstance(tgt, ast.Name):
            definidos.add(tgt.id)
    elif isinstance(n, ast.ExceptHandler) and n.name:
        definidos.add(n.name)
libres = sorted({x.id for x in ast.walk(a) if isinstance(x, ast.Name)
                 and isinstance(x.ctx, ast.Load) and x.id not in definidos})
check("0 nombres sin definir", libres, [])

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
