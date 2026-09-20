# -*- coding: utf-8 -*-
"""v465 · Las pestañas pasan a nombre INGLES, con respaldo al viejo.

⚠️ El fallo que este guardian existe para impedir NO es una excepcion: `get_sheet`
CREA la hoja si no la encuentra, asi que un nombre que no case hace que la app se
fabrique una pestaña VACIA y escriba ahi — sin un solo error, con los datos
intactos al lado y la pantalla en blanco.
"""
import ast
import importlib
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir(r"C:\Users\diego\P1\survey_app")   # ⚠️ o no se encuentran los secrets (v19)
sys.path.insert(0, os.getcwd())
import streamlit as st
st.session_state["auth"] = {"usuario": "dacox", "rol": "owner", "grupo": "cliente1"}

_fallos = []
def ok(m):    print("   ok   %s" % m)
def fallo(m): print("   FALLO %s" % m); _fallos.append(m)

from core import timeclock, hojas

LEGADO = timeclock.LEGADO

print("1. Toda constante *_SHEET esta en ingles y tiene respaldo")
consts = {}
for p in sorted(Path("core").glob("*.py")):
    try:
        m = importlib.import_module("core." + p.stem)
    except Exception:
        continue
    for n in dir(m):
        v = getattr(m, n, None)
        if n.endswith("SHEET") and isinstance(v, str):
            consts["%s.%s" % (p.stem, n)] = v
sin_respaldo = [k for k, v in consts.items()
                if v.lower() in {x.lower() for x in LEGADO.values()}]
if sin_respaldo:
    for k in sin_respaldo:
        fallo("%s sigue con el nombre viejo (%r)" % (k, consts[k]))
else:
    ok("%d constantes, ninguna con el nombre viejo" % len(consts))

# ⚠️ Login/PreStarts/Roster/Sheet1 ya estaban en ingles y no entran en LEGADO.
# ⚠️ v472 · `Library`/`LibraryModels` tampoco, y por una razon DISTINTA que
# conviene no confundir: aquellas ya existian en ingles; estas **nacieron
# despues del renombrado**, asi que no han tenido nunca un nombre español y no
# hay nada con lo que ser compatible. Que `get_sheet` las cree la primera vez
# es lo CORRECTO aqui, no el fallo que este bloque vigila.
# ⚠️ v488 · `XeroConnections`, por la MISMA razon que la biblioteca: nacio en ingles
# despues del renombrado. CADUCADO por un cambio deliberado, no relajado: la regla
# sigue exigiendo respaldo a cualquier hoja que SI haya tenido nombre español.
_YA = {"login", "prestarts", "roster", "sheet1", "library", "librarymodels",
       "xeroconnections"}
huerfanas = [k for k, v in consts.items()
             if v.lower() not in LEGADO and v.lower() not in _YA]
if huerfanas:
    for k in huerfanas:
        fallo("%s (%r) no tiene entrada en LEGADO: si el libro aun tiene el nombre "
              "viejo, la app crearia una hoja VACIA" % (k, consts[k]))
else:
    ok("cada hoja renombrada tiene su respaldo en LEGADO")

print("")
print("2. Ningun modulo nombra una hoja con el nombre viejo")
VIEJOS = {v for v in LEGADO.values()}
ABREN = {"get_sheet", "registros", "invalidar_hoja", "worksheet"}
malos = []
for p in sorted(list(Path("core").glob("*.py")) + [Path("app.py")]):
    if p.name == "timeclock.py":
        continue                      # ahi vive el mapa a proposito
    a = ast.parse(p.read_text(encoding="utf-8"))
    for n in ast.walk(a):
        if isinstance(n, ast.Call):
            nom = n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
            if nom in ABREN:
                for arg in n.args:
                    if isinstance(arg, ast.Constant) and arg.value in VIEJOS:
                        malos.append("%s:%s %r" % (p.name, n.lineno, arg.value))
if malos:
    for m in malos:
        fallo("abre una hoja por su nombre viejo: %s" % m)
else:
    ok("0 llamadas con el nombre viejo")

print("")
print("3. HOJAS_LECTURA usa los nombres nuevos (o el lote se saltaria esas hojas)")
viejas_en_lote = [h for h in hojas.HOJAS_LECTURA if h in VIEJOS]
if viejas_en_lote:
    fallo("HOJAS_LECTURA aun trae %s" % viejas_en_lote)
else:
    ok("las %d del lote estan en ingles" % len(hojas.HOJAS_LECTURA))

print("")
print("4. El respaldo FUNCIONA contra el libro real")
# ⚠️ Se valida en las DOS direcciones: si solo se comprobara que devuelve algo,
# una funcion que devolviera siempre el nombre nuevo pasaria igual (trampa n1).
_r = timeclock.titulo_real("Projects")
if _r in ("Projects", "Proyectos"):
    ok("titulo_real('Projects') -> %r (el que EXISTE en el libro)" % _r)
else:
    fallo("titulo_real('Projects') devolvio %r" % _r)
if timeclock.titulo_real("Login") == "Login":
    ok("una hoja sin renombrar se devuelve tal cual")
else:
    fallo("titulo_real toco una hoja que no debia")
if timeclock.titulo_real("NoExisteEstaHoja") == "NoExisteEstaHoja":
    ok("un titulo desconocido se devuelve intacto")
else:
    fallo("titulo_real invento un nombre para una hoja desconocida")

print("")
print("5. get_sheet resuelve el titulo ANTES de decidir si crea")
src = Path("core/timeclock.py").read_text(encoding="utf-8")
a = ast.parse(src)
fn = next((n for n in ast.walk(a)
           if isinstance(n, ast.FunctionDef) and n.name == "get_sheet"), None)
if fn is None:
    fallo("no se encontro get_sheet")
else:
    l_res = next((n.lineno for n in ast.walk(fn)
                  if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "titulo_real"), None)
    l_add = next((n.lineno for n in ast.walk(fn)
                  if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "add_worksheet"), None)
    if l_res and l_add and l_res < l_add:
        ok("titulo_real (L%s) va antes de add_worksheet (L%s)" % (l_res, l_add))
    else:
        fallo("get_sheet podria CREAR una hoja vacia sin haber mirado el nombre viejo")

print("")
print("6. El indice de pestañas se REPARA solo (v466)")
# ⚠️ `_libro` vive en `@st.cache_resource`, que NO caduca. Si una hoja se renombra
# despues de construirlo, el proceso se queda pidiendo el nombre viejo PARA TODA SU
# VIDA: el lote falla en cada pasada y las pantallas salen a CERO con los datos
# intactos en el libro. Paso de verdad al renombrar al ingles y solo se arreglaba
# reiniciando a mano.
_h = ast.parse(Path("core/hojas.py").read_text(encoding="utf-8"))
_lote = next((n for n in ast.walk(_h)
              if isinstance(n, ast.FunctionDef) and n.name == "_lote"), None)
_limpia = any(isinstance(c, ast.Call) and getattr(c.func, "attr", "") == "clear"
              and "_libro" in ast.dump(c.func)
              for h in ast.walk(_lote or ast.Module(body=[], type_ignores=[]))
              if isinstance(h, ast.ExceptHandler) for c in ast.walk(h))
if _limpia:
    ok("si el lote falla, `_lote` tira el indice para que se reconstruya")
else:
    fallo("el lote falla y el indice se queda viejo: las pantallas saldrian a CERO")

_t = ast.parse(Path("core/timeclock.py").read_text(encoding="utf-8"))
_gs = next((n for n in ast.walk(_t)
            if isinstance(n, ast.FunctionDef) and n.name == "get_sheet"), None)
_lc = next((n.lineno for n in ast.walk(_gs)
            if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "clear"), None)
_la = next((n.lineno for n in ast.walk(_gs)
            if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "add_worksheet"), None)
if _lc and _la and _lc < _la:
    ok("get_sheet refresca el indice (L%s) ANTES de crear (L%s)" % (_lc, _la))
else:
    fallo("get_sheet crearia una hoja vacia por tener el indice viejo")

print("")
if _fallos:
    print("FALLOS: %d" % len(_fallos))
    sys.exit(1)
print("TODO OK - v465")
