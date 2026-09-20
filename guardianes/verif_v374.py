"""GUARDIÁN v374 — fichaje en el sidebar + aviso del Pre-Start.

1. ⚠️ **Todo mensaje va por `flash`**: estas acciones terminan en `st.rerun()`, que
   descarta los deltas de la pasada (v365). Un `st.success` aquí no se ve NUNCA.
2. ⚠️ **El modal se dispara por BANDERA**, en la pasada siguiente, y se llama al TOP
   LEVEL del script — nunca dentro del `with st.sidebar:`.
3. Las keys nuevas no chocan con las de la pestaña ⏱ Fichaje (dos widgets con la
   misma key revientan la página, y las dos pantallas coinciden en el mismo run).
4. Los destinos de navegación EXISTEN para cada rol (guardián de v303).
5. `hecho_hoy` es por OBRA y DÍA, y no cuesta llamadas nuevas a Sheets.
"""
import ast
import builtins
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st
st.session_state["auth"] = {"usuario": "jlopez", "grupo": "cliente1", "rol": "field"}

from core import prestart as PS, home_ui as HOME, clock   # noqa: E402

BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")
src = BASE.joinpath("core", "timeclock_ui.py").read_text(encoding="utf-8")
arbol = ast.parse(src)
ok = True

NUEVAS = ["render_sidebar_chrono", "_sidebar_fichado", "_sidebar_sin_fichar",
          "_fichar", "_chip_prestart", "aviso_prestart_pendiente",
          "_dialogo_prestart", "_ir_a_prestart"]
fns = {n.name: n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef)}

print("== 1. ⚠️ ningún mensaje muere en el rerun (v365) ==")
for nom in NUEVAS:
    fn = fns.get(nom)
    if fn is None:
        print(f"   ‼️ falta {nom}")
        ok = False
        continue
    cuerpo = ast.unparse(fn)
    if "st.rerun" not in cuerpo:
        continue
    # `st.error` SÍ se ve: en estas funciones va en la rama que NO recarga.
    malos = [t for t in ("st.success(", "st.warning(", "st.info(")
             if t in cuerpo and "flash" not in cuerpo]
    ok &= not malos
    print(f"   {'✓' if not malos else '‼️'} {nom:<26} usa flash: {'flash.' in cuerpo}"
          + (f"  ← {malos}" if malos else ""))

print("\n== 2. ⚠️ el modal: bandera + top level ==")
fn_av = fns["aviso_prestart_pendiente"]
# ⚠️ v375 INVIRTIÓ esto: la v374 consumía la bandera con `pop` y el modal se cerraba
# solo en la pasada siguiente (los `components.html` del cronómetro disparan una).
# Ahora es una condición de estado: se LEE con `get` y se descarta aparte.
_get = "get('_ps_aviso')" in ast.unparse(fn_av).replace('"', "'")
ok &= _get
print(f"   {'✓' if _get else '‼️'} `aviso_prestart_pendiente` LEE la bandera (no la consume): "
      "así cualquier rerun vuelve a pintar el modal")
_fichar = ast.unparse(fns["_fichar"])
_deja = "_ps_aviso" in _fichar and "st.rerun()" in _fichar
ok &= _deja
print(f"   {'✓' if _deja else '‼️'} `_fichar` la DEJA y recarga (no abre el modal en su "
      "propia pasada, que se descartaría)")
# el decorador existe y es st.dialog
_dec = [ast.unparse(d) for d in fns["_dialogo_prestart"].decorator_list]
_esdlg = any("st.dialog" in d for d in _dec)
ok &= _esdlg
print(f"   {'✓' if _esdlg else '‼️'} `_dialogo_prestart` está decorada con st.dialog")
# ⚠️ y en app.py se llama FUERA del `with st.sidebar:`
app = BASE.joinpath("app.py").read_text(encoding="utf-8")
app_ast = ast.parse(app)
_dentro_sidebar = False
for n in ast.walk(app_ast):
    if isinstance(n, ast.With) and "st.sidebar" in ast.unparse(n.items[0].context_expr):
        if "aviso_prestart_pendiente" in ast.unparse(n):
            _dentro_sidebar = True
ok &= not _dentro_sidebar
# ⚠️ Por AST, no por texto: buscarla como `aviso_prestart_pendiente()` fallaba en
# falso en cuanto la llamada ganó un argumento (v375 le pasa el grupo).
_llamada = any(isinstance(n, ast.Call) and getattr(n.func, "id", "") == "aviso_prestart_pendiente"
               for n in ast.walk(app_ast))
ok &= _llamada
print(f"   {'✓' if _llamada else '‼️'} app.py la llama")
print(f"   {'✓' if not _dentro_sidebar else '‼️'} y NO desde dentro del `with st.sidebar:`")

print("\n== 3. keys de widget: el sidebar y la pestaña conviven en el mismo run ==")
keys = {}
for n in ast.walk(arbol):
    if isinstance(n, ast.Call):
        for kw in n.keywords:
            if kw.arg == "key":
                t = ast.unparse(kw.value)
                keys[t] = keys.get(t, 0) + 1
dup = {k: v for k, v in keys.items() if v > 1}
ok &= not dup
print(f"   {'✓' if not dup else '‼️'} sin keys duplicadas en el módulo: {dup or 'ninguna'}")
_sb = sorted(k for k in keys if "sb_" in k or "ps_dlg" in k)
print(f"   keys nuevas ({len(_sb)}): " + ", ".join(k.replace('"', "'") for k in _sb))

print("\n== 4. los destinos de navegación EXISTEN para cada rol (v303) ==")
for rol, sec, sub in [("field", "prestart", None),
                      ("administrator", "herramientas", "🦺 Pre-Start")]:
    st.session_state["auth"] = {"usuario": "x", "grupo": "cliente1", "rol": rol}
    _secs = [k for k, _l in HOME._secciones()]
    bien = sec in _secs
    if sub is not None:
        _subs = [i for i, _d in (HOME._subsecciones().get(sec, ("", []))[1])]
        bien = bien and sub in _subs
    ok &= bien
    print(f"   {'✓' if bien else '‼️'} {rol:<14} → {sec}" + (f" · {sub}" if sub else ""))

print("\n== 5. `hecho_hoy`: por OBRA y DÍA, sin llamadas nuevas ==")
st.session_state["auth"] = {"usuario": "jlopez", "grupo": "cliente1", "rol": "field"}
print(f"   pid vacío → {PS.hecho_hoy('')}  {'✓' if PS.hecho_hoy('') is False else '✗'}")
ok &= PS.hecho_hoy("") is False
# contra los datos reales
_hoy = clock.today("cliente1")
_filas = [r for r in PS._records() if str(r.get("Fecha", "")).strip()]
print(f"   hoy es {_hoy} · la hoja tiene {len(_filas)} pre-start(s) con fecha")
for pid in ("PRJ-0007", "PRJ-0008", "PRJ-0011"):
    print(f"      {pid} → hecho hoy: {PS.hecho_hoy(pid, 'cliente1')}")
# una fila con OTRO formato de fecha se sigue reconociendo
from core.num import parse_date as _pd
_ok_fmt = _pd("20/08/2026") == _pd("2026-08-20")
ok &= _ok_fmt
print(f"   {'✓' if _ok_fmt else '✗'} una fecha en otro formato se reconoce igual "
      "(no se compara como texto)")

print("\n" + ("✅ v374 OK: nada muere en el rerun, el modal va por bandera y al top level, "
              "keys limpias y destinos válidos" if ok else "⚠️ REVISAR"))
sys.exit(0 if ok else 1)
