"""v297 · Fase 1: el CAMPO pasa a la shell nueva.

Lo critico: (a) el ADMIN no cambia nada, (b) el campo conserva TODAS sus secciones,
(c) cada seccion enruta a la funcion correcta y con la firma correcta.
"""
import sys, ast, inspect, pathlib
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st
from core import home_ui as H

ok = True
def check(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"         esperado: {esp!r}")


def como(rol, usuario="campo1"):
    st.session_state["auth"] = {"rol": rol, "usuario": usuario, "grupo": "g", "nombre": "N"}


print("== A) el ADMIN no cambia ==")
como("administrator", "admin1")
# ⚠️ CADUCADO en v472 y ACTUALIZADO (regla v385, trampa nº16): exigia la lista
# EXACTA, asi que se puso rojo al añadir «biblioteca» a proposito — fallaba por
# haber ganado. Es la misma correccion que v430 le hizo al bloque del campo, unas
# lineas mas abajo. Lo que protege: al admin no se le pierde nada Y lo nuevo va
# DESPUES (si se colara en medio, se le reordena la nav a quien ya la usaba).
_ADMIN_VIEJAS = ["home", "fichaje", "planificacion", "proyectos", "finanzas",
                 "inventario", "herramientas", "contactos"]
_adm_secs = [k for k, _ in H._secciones()]
check("no se pierde ninguna seccion del admin",
      [x for x in _ADMIN_VIEJAS if x not in _adm_secs], [])
check("...y las que se anadan van DESPUES (no reordenan su nav)",
      _adm_secs[:len(_ADMIN_VIEJAS)], _ADMIN_VIEJAS)
check("subsecciones = las de siempre", H._subsecciones() is H._SUBSECCIONES)
check("herramientas incluye Pre-Start",
      "🦺 Pre-Start" in [i for i, _ in H._subsecciones()["herramientas"][1]])
check("_subkey igual al de antes", H._subkey(), H._SUBKEY)
check("_lbl2key igual al de antes", H._lbl2key(), H._LBL2KEY)

print("\n== B) el CAMPO conserva TODO lo que tenia ==")
como("field")
_secs = [k for k, _ in H._secciones()]
# ⚠️ CADUCADO en v430 y actualizado (regla v385, trampa nº16): esto exigia la lista
# EXACTA de 6, asi que se puso rojo al AÑADIR «ausencias» a proposito — fallaba por
# haber ganado algo. Lo que la regla protege no es el numero: es que al campo no se
# le PIERDA nada de la nav que tenia antes de la migracion. Contencion, no igualdad.
_VIEJAS = ["misproyectos", "fichaje", "prestart", "herramientas",
           "credenciales", "colillas"]
# ⚠️ CADUCADO en v478 y ACTUALIZADO: `credenciales` y `colillas` ya no son secciones
# de primer nivel — v478 las bajo, con `ausencias`, a sub-pestañas de «Self-service»
# (peticion del usuario: la nav del campo de 8 a 6, que en un movil se nota). La regla
# NO se relaja: sigue siendo «no se le pierde nada», solo que ahora alcanzable como
# seccion **o** como sub-seccion, que es lo que le importa a quien la usa.
_ALCANZABLE = set(_secs) | {i for _k, (_c, _its) in H._subsecciones().items()
                            for i, _d in _its}
_ALIAS = {"credenciales": "🎫 Credenciales", "colillas": "💰 Colillas",
          "ausencias": "🌴 Ausencias"}
check("el campo sigue LLEGANDO a todo lo que tenia (seccion o sub-seccion)",
      [x for x in _VIEJAS
       if x not in _ALCANZABLE and _ALIAS.get(x) not in _ALCANZABLE], [])
# ⚠️ Y lo que sigue siendo seccion conserva su ORDEN: mover algo a un submenu es una
# decision; REORDENARLE la nav a quien ya la usaba, no.
_SIGUEN = [x for x in _VIEJAS if x in _secs]
check("...y lo que sigue siendo seccion no se reordena",
      _secs[:len(_SIGUEN)], _SIGUEN)
check("las tres «mias» estan juntas bajo un solo nivel (v478)",
      sorted(i for i, _d in H._subsecciones().get("autogestion", ("", []))[1]),
      sorted(_ALIAS.values()))
# su nav VIEJA (app.py): Mis proyectos · Fichaje · Pre-Start · 5 tecnicas · Mis cred · Mis colillas
_herr = [i for i, _ in H._subsecciones()["herramientas"][1]]
check("Herramientas = Inicio + las 5 TECNICAS", _herr,
      ["🧰 Inicio", "📐 Survey", "🔩 Plomada", "✂️ Rieles", "🛡 Buffers", "🎗 Belting"])
check("Pre-Start NO se duplica dentro de Herramientas", "🦺 Pre-Start" not in _herr)
check("...y sigue existiendo como seccion propia", "prestart" in _secs)
_cubre = set(_secs) | set(_herr)
# ⚠️ Tambien caducado por lo mismo: era `== 12`. Se comprueba la COBERTURA (que las
# 5 tecnicas y los 6 apartados operativos sigan alcanzables), no el total exacto.
check("nada perdido: las 5 tecnicas + los 6 apartados operativos",
      [x for x in _VIEJAS + _herr
       if x not in _cubre and _ALIAS.get(x) not in _ALCANZABLE], [])

print("\n== C) el router llama a la funcion correcta, con su firma ==")
from core import projects_ui, prestart_ui, auth_ui, payroll_ui, timeclock_ui
_esperado = {
    "misproyectos": (projects_ui.render_field_projects, 2),
    "prestart":     (prestart_ui.render_prestart_tab, 0),
    "credenciales": (auth_ui.render_my_credentials, 0),
    "colillas":     (payroll_ui.render_mis_colillas, 2),
    "fichaje":      (timeclock_ui.render_timeclock_tab, 0),
}
for k, (fn, nargs) in _esperado.items():
    _n = len([p for p in inspect.signature(fn).parameters.values()
              if p.default is inspect.Parameter.empty
              and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)])
    check(f"{k} -> {fn.__name__} con {nargs} arg oblig.", _n, nargs)

# ⚠️ ACTUALIZADO en v478: `credenciales` y `colillas` ya no son claves de SECCION —
# el router llega a ellas por el ID de su sub-pestaña dentro de «autogestion». Lo que
# hay que proteger no es el nombre de la rama, sino que **cada pantalla del campo la
# siga sirviendo su funcion**. Se comprueba el ID EXACTO (con su emoji): comparar
# contra el display navega a ninguna parte y no da ningun error (el fallo de v303).
src = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\home_ui.py").read_text(encoding="utf-8")
for k in ("misproyectos", "prestart", "autogestion"):
    check(f"router contempla la seccion '{k}'", f'"{k}"' in src)
for k in ("\U0001F3AB Credenciales", "\U0001F4B0 Colillas"):
    check(f"router despacha el ID exacto '{k}'", f'"{k}"' in src)
for _fn in ("render_my_credentials", "render_mis_colillas", "render_mis_ausencias"):
    check(f"router llama a {_fn}", _fn in src)

print("\n== D) la campana del campo solo muestra LO SUYO ==")
import core.credentials as C, core.inventory as INV
C.is_configured = lambda: True
C.expiring = lambda g: [{"tipo": "White Card", "usuario": "campo1", "dias": -3},
                        {"tipo": "Forklift", "usuario": "OTRO", "dias": 5}]
INV.is_configured = lambda: True
INV.alertas = lambda g: [{"tipo": "mantenimiento", "activo": "Taladro", "dias": 4}]
como("field")
_a = H._alertas("g")
check("solo su credencial", len(_a), 1)
check("es la suya", "campo1" in _a[0])
check("sin inventario (es del admin)", all("Taladro" not in x for x in _a))
como("administrator", "admin1")
_a = H._alertas("g")
check("el admin las ve TODAS + inventario", len(_a), 3)

print("\n== E) fallback: una seccion desconocida no rompe ==")
como("field")
check("cae a la 1a del rol (misproyectos)", H._secciones()[0][0], "misproyectos")
como("administrator", "admin1")
check("el admin cae a home", H._secciones()[0][0], "home")

print("\n== F) version en el topbar ==")
check("lee VERSION", H._version().startswith("v"))
print(f"         {H._version()}")

print("\n== G) compila e importa todo ==")
import py_compile, importlib
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")
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
check(f"{len(mods)-len(malos)}/{len(mods)} modulos", malos, [])
# v384: `_SHELL_NUEVA` era la bandera que convivía con la nav vieja. v299 hizo la
# shell incondicional y la quitó: exigirla ahora es exigir el andamio después de
# construir el edificio.
check("la bandera _SHELL_NUEVA ya no hace falta (shell incondicional, v299)",
      "_SHELL_NUEVA" not in (BASE / "app.py").read_text(encoding="utf-8"))

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
