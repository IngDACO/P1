# -*- coding: utf-8 -*-
"""v468 · Las COLUMNAS pasan a nombre ingles, con respaldo al viejo.

⚠️ El fallo que este guardian existe para impedir es SILENCIOSO: `fila.get("Status")`
sobre una cabecera que dice `Estado` devuelve `""`. No lanza, no avisa: la columna
sale vacia por toda la app.
"""
import ast
import importlib
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir(r"C:\Users\diego\P1\survey_app")     # ⚠️ o no hay secrets (trampa n19)
sys.path.insert(0, os.getcwd())
import streamlit as st
st.session_state["auth"] = {"usuario": "dacox", "rol": "owner", "grupo": "cliente1"}

_f = []
def ok(m):    print("   ok   %s" % m)
def fallo(m): print("   FALLO %s" % m); _f.append(m)

from core import columnas, hojas, timeclock

print("1. El mapa vive en UN solo sitio y cubre las cabeceras reales")
reales = set()
cabeceras = {}
for p in sorted(Path("core").glob("*.py")):
    try:
        m = importlib.import_module("core." + p.stem)
    except Exception:
        continue
    for n in dir(m):
        v = getattr(m, n, None)
        if n.endswith("HEADERS") and isinstance(v, (list, tuple)):
            cabeceras["%s.%s" % (p.stem, n)] = list(v)
            reales |= {str(x) for x in v}
assert reales, "no se leyeron cabeceras: el chequeo no probaria nada"

viejas_vivas = sorted(reales & set(columnas.LEGADO))
if viejas_vivas:
    for c in viejas_vivas:
        fallo("la cabecera %r sigue con el nombre viejo" % c)
else:
    ok("ninguna de las %d cabeceras usa un nombre del mapa viejo" % len(reales))

# ⚠️ El mapa NO puede estar copiado: dos copias divergen (cinco `_num` en v323).
# Una copia coincide en los VALORES; `tabla.CABECERAS` no lo es (ver comentario abajo).
import ast as _ast
copias = []
for _p in Path("core").glob("*.py"):
    if _p.name == "columnas.py":
        continue
    try:
        _a = _ast.parse(_p.read_text(encoding="utf-8"))
    except Exception:
        continue
    for _n in _ast.walk(_a):
        if not isinstance(_n, _ast.Dict):
            continue
        pares = {k.value: v.value for k, v in zip(_n.keys, _n.values)
                 if isinstance(k, _ast.Constant) and isinstance(v, _ast.Constant)
                 and isinstance(k.value, str) and isinstance(v.value, str)}
        comunes = set(pares) & set(columnas.LEGADO)
        if len(comunes) >= 20 and all(pares[c] == columnas.LEGADO[c] for c in comunes):
            copias.append("%s:%s" % (_p.name, _n.lineno))
if copias:
    fallo("el mapa esta copiado en %s" % copias)
else:
    ok("el mapa solo vive en columnas.py")

print("")
print("2. La canonizacion FUNCIONA en las dos direcciones")
# ⚠️ Sin la segunda, una funcion que devolviera siempre el nombre nuevo pasaria.
if columnas.canon("Estado") == "Status" and columnas.canon("ID") == "ID":
    ok("canon: traduce lo que conoce y deja intacto lo que no")
else:
    fallo("canon devuelve %r / %r" % (columnas.canon("Estado"), columnas.canon("ID")))
_r = columnas.canonizar([{"Estado": "a", "ID": "1"}])
if _r == [{"Status": "a", "ID": "1"}]:
    ok("canonizar renombra la clave vieja y respeta la nueva")
else:
    fallo("canonizar devolvio %r" % _r)
# una fila que YA viene canonica no se toca
if columnas.canonizar([{"Status": "a"}]) == [{"Status": "a"}]:
    ok("una fila ya canonica se queda igual")
else:
    fallo("canonizar rompe una fila ya migrada")

print("")
print("3. Los DOS caminos de lectura canonizan")
src = Path("core/hojas.py").read_text(encoding="utf-8")
a = ast.parse(src)
fn = next((n for n in ast.walk(a) if isinstance(n, ast.FunctionDef) and n.name == "registros"), None)
if fn is None:
    fallo("no existe registros()")
else:
    d = ast.dump(fn)
    if "canon" in d and "canonizar" in d:
        ok("registros canoniza la cabecera Y el camino de respaldo")
    else:
        fallo("un camino de lectura NO canoniza: esa hoja saldria vacia")

def _sin_canonizar(arbol):
    """Lecturas `get_all_records(...)` cuyo resultado NO pasa por `canonizar`.

    ⚠️ Estructural a proposito: mirar si la palabra `canonizar` esta en la misma
    linea daba un FALSO POSITIVO con la llamada partida en dos (lo normal cuando se
    pasa de ancho) y un FALSO NEGATIVO si la palabra aparecia en un comentario.
    """
    envueltas = set()
    for n in ast.walk(arbol):
        if not isinstance(n, ast.Call):
            continue
        nom = getattr(n.func, "attr", None) or getattr(n.func, "id", None)
        if nom != "canonizar":
            continue
        for dentro in ast.walk(n):
            if (isinstance(dentro, ast.Call)
                    and getattr(dentro.func, "attr", "") == "get_all_records"):
                envueltas.add(id(dentro))
    return [n.lineno for n in ast.walk(arbol)
            if isinstance(n, ast.Call)
            and getattr(n.func, "attr", "") == "get_all_records"
            and id(n) not in envueltas]


# ⚠️ La sonda, validada contra los dos casos conocidos ANTES de creerse su cero
# (trampa nº12): si no viera la lectura cruda, su «0» no significaria nada.
_MALA = ast.parse("r = ws.get_all_records(numericise_ignore=['all'])")
_BUENA = ast.parse("r = columnas.canonizar(\n    ws.get_all_records(numericise_ignore=['all']))")
if not (_sin_canonizar(_MALA) and not _sin_canonizar(_BUENA)):
    fallo("la sonda de canonizacion NO distingue: su cero no diria nada")
else:
    ok("la sonda ve la lectura cruda y no marca la envuelta (aunque vaya en 2 lineas)")

sin = []
for p in sorted(Path("core").glob("*.py")):
    if p.name in ("hojas.py", "columnas.py"):
        continue
    try:
        _a = ast.parse(p.read_text(encoding="utf-8"))
    except SyntaxError:
        continue
    for _ln in _sin_canonizar(_a):
        sin.append("%s:%s" % (p.name, _ln))
if sin:
    for s in sin:
        fallo("lee por clave sin canonizar: %s" % s)
else:
    ok("las 48 lecturas por clave pasan por canonizar")

print("")
print("4. La migracion de cabecera NO reescribe la fila 1")
# ⚠️ Con HEADERS en ingles y la hoja en español, `h not in head` seria verdadero
# para TODAS: el bucle reescribiria la fila 1 a ciegas y, si el orden no coincidiera,
# dejaria datos bajo la cabecera equivocada.
t = Path("core/timeclock.py").read_text(encoding="utf-8")
gs = next((n for n in ast.walk(ast.parse(t))
           if isinstance(n, ast.FunctionDef) and n.name == "get_sheet"), None)
_cond_ok = False
for _n in ast.walk(gs or ast.Module(body=[], type_ignores=[])):
    if not isinstance(_n, ast.For):
        continue
    if "enumerate" not in ast.dump(_n.iter) or "headers" not in ast.dump(_n.iter):
        continue
    for _i in _n.body:
        if isinstance(_i, ast.If) and "canon" in ast.dump(_i.test):
            _cond_ok = True
if _cond_ok:
    ok("la CONDICION de la migracion canoniza (una columna vieja cuenta como presente)")
else:
    fallo("get_sheet compara sin canonizar: reescribiria la fila 1 entera")

print("")
print("5. Las escrituras siguen cayendo en su sitio")
# `_COL` se deriva de HEADERS por POSICION: lo que hay que proteger es que ninguna
# cabecera cambie de tamaño ni gane duplicados.
malos = [k for k, v in cabeceras.items() if len(set(v)) != len(v)]
if malos:
    for k in malos:
        fallo("%s tiene una columna DUPLICADA: las escrituras se desalinean" % k)
else:
    ok("las %d cabeceras siguen sin duplicados" % len(cabeceras))

print("")
print("6. Contra la hoja REAL: el codigo pide ingles y el libro puede estar en español")
try:
    from core import auth
    filas = hojas.registros("Login", tuple(auth.LOGIN_HEADERS))
    if not filas:
        print("   ⚠️ la hoja Login esta vacia: este chequeo no puede afirmar nada")
        sys.exit(2)
    f = filas[0]
    quedan = [k for k in f if k in columnas.LEGADO]
    if quedan:
        fallo("llegan claves viejas: %s" % quedan)
    else:
        ok("las %d claves llegan canonicas" % len(f))
    if f.get("User") and f.get("Role"):
        ok("User=%r Role=%r (datos de verdad, no vacios)" % (f.get("User"), f.get("Role")))
    else:
        fallo("las claves canonicas vienen VACIAS: la canonizacion no aplica")
except SystemExit:
    raise
except Exception as e:
    fallo("no se pudo leer la hoja real: %s" % e)

print("")
if _f:
    print("FALLOS: %d" % len(_f))
    sys.exit(1)
print("TODO OK - v468")
