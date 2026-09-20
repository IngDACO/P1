"""v298 · Fase 2: el PROPIETARIO pasa a la shell nueva."""
import sys, inspect, pathlib
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

def como(rol, usuario="x", grupo="g"):
    st.session_state["auth"] = {"rol": rol, "usuario": usuario, "grupo": grupo, "nombre": "N"}


print("== A) los otros dos roles NO cambian ==")
como("administrator", "admin1")
# ⚠️ CADUCADO en v472 y ACTUALIZADO (regla v385): «intactas» era igualdad
# EXACTA y v472 le añade la Biblioteca a los tres roles a proposito. Lo que
# este guardian vino a proteger en la migracion de v298 es que a los otros dos
# roles no se les PIERDA nada, no que no puedan ganar una seccion nunca.
_ADMIN_VIEJAS = ["home", "fichaje", "planificacion", "proyectos", "finanzas",
                 "inventario", "herramientas", "contactos"]
_adm_secs = [k for k, _ in H._secciones()]
check("admin: no pierde ninguna seccion",
      [x for x in _ADMIN_VIEJAS if x not in _adm_secs], [])
check("admin: lo nuevo va DESPUES (no le reordena la nav)",
      _adm_secs[:len(_ADMIN_VIEJAS)], _ADMIN_VIEJAS)
check("admin: subsecciones intactas", H._subsecciones() is H._SUBSECCIONES)
como("field", "campo1")
# ⚠️ CADUCADO en v430 y actualizado (regla v385): exigia la lista EXACTA, y v430 le
# anade «ausencias» a proposito. Lo que protege es que la migracion no le QUITE nada
# al campo — asi que se comprueba contencion, no igualdad.
_C430 = [k for k, _ in H._secciones()]
# ⚠️ ACTUALIZADO en v478 (regla v385): `credenciales` y `colillas` pasaron a ser
# sub-pestañas de «Self-service» a peticion del usuario. La regla NO se relaja —al
# campo no se le puede perder nada—, solo se mide como ALCANZABLE, sea seccion o
# sub-seccion. Misma correccion que en `verif_v297`.
_ALC_C = set(_C430) | {i for _k, (_c, _its) in H._SUBSECCIONES_CAMPO.items()
                       for i, _d in _its}
_ALIAS_C = {"credenciales": "\U0001F3AB Credenciales",
            "colillas": "\U0001F4B0 Colillas"}
check("campo: sigue LLEGANDO a todas sus pantallas (v297/v478)",
      [x for x in ["misproyectos", "fichaje", "prestart", "herramientas",
                   "credenciales", "colillas"]
       if x not in _ALC_C and _ALIAS_C.get(x) not in _ALC_C], [])

print("\n== B) el PROPIETARIO conserva TODO lo que tenia ==")
como("owner", "dacox", "")
_secs = [k for k, _ in H._secciones()]
# ⚠️ CADUCADO en v472 y ACTUALIZADO por la misma razon: el propietario gana la
# Biblioteca (decision del usuario: la sube el, y todos consultan). Se afirma
# el principio —no pierde ninguna de sus 3 y lo nuevo va detras— y de paso
# sigue vigilada la de al lado: SIN fichaje (no ficha, v93).
_OWNER_VIEJAS = ["administracion", "prestart", "herramientas"]
check("propietario: no pierde ninguna de sus 3 secciones",
      [x for x in _OWNER_VIEJAS if x not in _secs], [])
check("propietario: lo nuevo va DESPUES", _secs[:len(_OWNER_VIEJAS)],
      _OWNER_VIEJAS)
check("SIN fichaje (no ficha, v93)", "fichaje" not in _secs)
_adm = H._subsecciones()["administracion"]
check("sub-key = owner_sec (deep-link de survey_ui intacto)", _adm[0], "owner_sec")
# ⚠️ CADUCADO en v482 y ACTUALIZADO: se añadió «📈 Cuota» (el medidor de consumo de
# la API). La afirmación era una LISTA A MANO de 6 IDs, así que cualquier pestaña nueva
# la ponía roja aunque no se hubiera perdido nada — el guardián atado a la FORMA de
# v392. Lo que de verdad protege es que el propietario **no pierda** ninguna y que las
# nuevas vayan DESPUÉS, que es como no se le reordena el menú a quien ya lo usa (v297).
_ADM_VIEJAS = ["🌐 Resumen", "🏢 Grupos", "👥 Usuarios", "📁 Proyectos", "🚆 Rieles",
               "📚 Manuales"]
_ids_adm = [i for i, _ in _adm[1]]
check("Administracion no pierde ninguna de sus pestañas",
      [x for x in _ADM_VIEJAS if x not in _ids_adm], [])
check("y lo nuevo va DESPUES (no le reordena el menu a nadie)",
      _ids_adm[:len(_ADM_VIEJAS)], _ADM_VIEJAS)
check("sin IDs duplicados", [i for i in _ids_adm if _ids_adm.count(i) > 1], [])
check("Herramientas = las 5 tecnicas", [i for i, _ in H._subsecciones()["herramientas"][1]],
      ["🧰 Inicio", "📐 Survey", "🔩 Plomada", "✂️ Rieles", "🛡 Buffers", "🎗 Belting"])

print("\n== C) los IDs son los MISMOS que el radio viejo ==")
src_au = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\auth_ui.py").read_text(encoding="utf-8")
import re
_viejo = re.search(r'st\.radio\("Sección",\s*\n?\s*(\[[^\]]+\])', src_au)
_ids_viejo = re.findall(r'"([^"]+)"', _viejo.group(1)) if _viejo else []
# v384: `render_owner_panel` se borró en v299, así que no hay radio viejo contra
# el que comparar. Lo que importa —y se comprueba— es que los IDs del propietario
# sigan siendo los que usan sus deep-links.
# ⚠️ Lo que este chequeo protege son los DEEP-LINKS: `survey_ui` escribe
# `owner_sec = "📁 Proyectos"`, así que renombrar un ID rompería la navegación sin dar
# ningún error. Eso no depende de CUÁNTAS pestañas haya, así que se afirma sobre los
# IDs históricos, no sobre el total.
check("los IDs historicos del propietario intactos (deep-links)",
      [x for x in _ADM_VIEJAS if x not in _ids_adm], [])

print("\n== D) el despacho se comparte (no duplicado) ==")
from core import auth_ui as AU
check("render_owner_seccion existe", callable(AU.render_owner_seccion))
check("render_owner_panel ya no existe (v299)", "def render_owner_panel" not in src_au)
_n_dispatch = src_au.count('if sec == "🌐 Resumen"')
check("el if/elif existe UNA sola vez", _n_dispatch, 1)
src_h = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\home_ui.py").read_text(encoding="utf-8")
check("la shell llama al mismo despacho", "render_owner_seccion(_sub_header" in src_h)

print("\n== E) campana del propietario: agregada por grupo ==")
from core import admin_digest as AD
AD.owner_digest = lambda: [
    {"grupo": "cliente1", "activos": 3, "avance": 40, "retrasos": 2, "alarmas": 1,
     "vencidos": 0, "cred_venc": 1, "sobre_presupuesto": 0, "pendientes": True},
    {"grupo": "cliente2", "activos": 1, "avance": 90, "retrasos": 0, "alarmas": 0,
     "vencidos": 0, "cred_venc": 0, "sobre_presupuesto": 0, "pendientes": False},
]
como("owner", "dacox", "")
_a = H._alertas("")
check("solo los grupos CON pendientes", len(_a), 1)
check("dice el grupo", "cliente1" in _a[0])
# ⚠️ CADUCADO por v439/v443 (i18n): las tres piezas del desglose pasaron al inglés.
# «behind schedule» se tradujo en v439 y «alarms»/«credentials» en v443 — eran
# fragmentos de f-string de UNA palabra, invisibles para las tres redes anteriores.
# La regla que se protege es que el desglose CUENTE cada tipo de pendiente.
check("y el desglose", "2 behind schedule" in _a[0] and "1 alarms" in _a[0]
      and "1 credentials" in _a[0])
print(f"         {_a[0]}")

print("\n== F) app.py: los TRES roles en la shell ==")
src_app = pathlib.Path(r"C:\Users\diego\P1\survey_app\app.py").read_text(encoding="utf-8")
# v384: `_SHELL_NUEVA` listaba los roles que YA usaban la shell nueva mientras
# convivía con la vieja. v299 la hizo incondicional y borró la bandera, así que este
# `split` reventaba con IndexError. Lo que queda vivo: que app.py NO enrute por rol
# —la shell sirve a los tres— y que un rol desconocido caiga en la del campo.
check("app.py ya no enruta por rol (shell incondicional, v299)",
      "_SHELL_NUEVA" not in src_app)
from core import home_ui as _H
check("home_ui resuelve las secciones de los 3 roles",
      sorted(_H._SECCIONES_ROL.keys()),
      ["administrator", "field", "owner"])

print("\n== G) compila e importa ==")
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
check(f"{len(mods)-len(malos)}/{len(mods)} modulos + app.py", malos, [])

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
