# -*- coding: utf-8 -*-
"""v469 · Los VALORES de negocio pasan a ingles, con respaldo al valor viejo.

⚠️ Es el renombrado mas delicado de los cuatro. Una hoja mal nombrada deja la
pantalla vacia y una columna mal leida devuelve ""; los dos SE VEN. Un valor que
deja de casar NO se ve: la rama simplemente no entra.
"""
import ast
import io
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

from core import valores, payroll, auth

def _sin_canonizar(src, nombre):
    """Llamadas a `get_all_records` cuya SENTENCIA no pasa por `valores.canonizar`.

    ⚠️ Por sentencia y no por línea: `ast.unparse` normaliza la línea lógica entera,
    así que una llamada partida en varias líneas se mide igual que una de una sola.
    """
    fuera = []
    try:
        arbol = ast.parse(src)
    except SyntaxError:
        return fuera
    for st in ast.walk(arbol):
        if not isinstance(st, ast.stmt):
            continue
        hijos = [n for n in ast.iter_child_nodes(st)]
        texto = ""
        for h in hijos:
            if any(isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                   and c.func.attr == "get_all_records" for c in ast.walk(h)):
                texto = ast.unparse(st)
                break
        if texto and "valores.canonizar" not in texto:
            fuera.append("%s:%s" % (nombre, getattr(st, "lineno", 0)))
    return sorted(set(fuera))


def _funcion_de(_arb, ln):
    """La funcion mas INTERNA que contiene esa linea ('' si es de modulo)."""
    mejor, ancho = "", 10 ** 9
    for n in ast.walk(_arb):
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        fin = n.end_lineno or n.lineno
        if n.lineno <= ln <= fin and (fin - n.lineno) < ancho:
            mejor, ancho = n.name, fin - n.lineno
    return mejor


print("1. Ninguna comparacion queda contra un valor VIEJO")
# ⚠️ Estos son literales INTERNOS: su productor y su consumidor viven en el mismo
# modulo (`buscar()`, `inventory.alertas`) o son claves de session_state. No son
# valores de hoja, asi que traducirlos no traduciria nada.
# ⚠️ Reanclado en v472: iba por (fichero, LINEA) y cualquier edicion mas arriba
# lo desalineaba — v472 añadio codigo a `home_ui` y los tres falsos positivos
# volvieron. Peor: una comparacion REAL que cayera en ese numero quedaria
# eximida en silencio. Ahora va por (fichero, funcion, valor), que sobrevive a
# las ediciones de al lado y dice QUE se exime.
SALTAR = {("home_ui.py", "_abrir_resultado", "proyecto"),
          ("home_ui.py", "_alertas", "mantenimiento"),
          ("survey_ui.py", "render_survey_tab", "proyecto")}
quedan = []
for p in sorted(list(Path("core").glob("*.py")) + [Path("app.py")]):
    if p.name in ("valores.py", "i18n.py", "columnas.py"):
        continue
    src = p.read_text(encoding="utf-8").split("\n")
    _arb = ast.parse("\n".join(src))
    for n in ast.walk(_arb):
        if not isinstance(n, ast.Compare):
            continue
        for c in n.comparators:
            cand = []
            if isinstance(c, ast.Constant) and isinstance(c.value, str):
                cand = [(c.value, c.lineno)]
            if isinstance(c, (ast.List, ast.Tuple, ast.Set)):
                cand = [(e.value, e.lineno) for e in c.elts
                        if isinstance(e, ast.Constant) and isinstance(e.value, str)]
            for v, ln in cand:
                if v not in valores.LEGADO:
                    continue
                if (p.name, _funcion_de(_arb, ln), v) in SALTAR:
                    continue
                quedan.append("%s:%s %r" % (p.name, ln, v))
if quedan:
    for q in quedan[:10]:
        fallo("comparacion contra un valor viejo (rama MUERTA): %s" % q)
else:
    ok("0 comparaciones contra un valor viejo")

print("")
print("2. La lista blanca va por (HOJA, COLUMNA), no por nombre de columna")
# ⚠️ ESTE BLOQUE AFIRMABA LO CONTRARIO DE LO CORRECTO, y por poco no cuesta caro.
# Se escribio cuando `TIPO_PROYECTO` todavia era `"proyecto"`: entonces canonizar esa
# columna SI rompia el fichaje (la fila diria `project` y el codigo comparaba
# `proyecto`). Al migrar la constante a `"project"`, la conclusion se invirtio —
# **dejarlo fuera es lo que rompe**: las ~500 filas del historico siguen diciendo
# `proyecto`, se leen sin canonizar y `_tipo_of(r) == TIPO_PROYECTO` es FALSO para
# todas, asi que ni una hora imputada a una obra cuenta como tal (nomina, costo de
# obra, conciliacion de v313 y reparto por proyecto, todo a cero, sin dar un error).
#
# ⚠️ O sea que el guardian estaba PROTEGIENDO el fallo: hacerle caso al rojo sin mirar
# el codigo acusado lo habria reintroducido. Es la regla v385 en su forma mas incomoda
# — el acusado tenia razon y el acusador no.
#
# Lo que SI se conserva, porque no ha cambiado, es el principio: la lista va por
# PAREJA y nunca por nombre de columna suelto, para que `proyecto` en `Sheet1.Type` y
# `proyecto` en `Assets.LocationType` no se pisen.
if all(isinstance(x, tuple) and len(x) == 2 for x in valores.COLUMNAS):
    ok("la lista blanca son %d pares (hoja, columna)" % len(valores.COLUMNAS))
else:
    fallo("la lista blanca no esta por pares: podria tocar columnas homonimas")
if ("Sheet1", "Type") in valores.COLUMNAS:
    ok("Sheet1.Type (el fichaje) esta DENTRO, o el historico no casaria")
else:
    fallo("Sheet1.Type quedo FUERA: ni una hora de obra del historico contaria")
# y se comprueba EJECUTANDO, en las dos direcciones
from core import timeclock as _TC                                  # noqa: E402
_esperado = {"proyecto": "project", "project": "project", "general": "general"}
_mal = [(v, valores.canonizar([{"Type": v}], "Sheet1")[0]["Type"])
        for v, e in _esperado.items()
        if valores.canonizar([{"Type": v}], "Sheet1")[0]["Type"] != e]
if not _mal:
    ok("la fila vieja, la nueva y la jornada acaban donde deben")
else:
    fallo("el fichaje no canoniza bien: %r" % _mal)
if _TC._tipo_of(valores.canonizar([{"Type": "proyecto"}], "Sheet1")[0]) == _TC.TIPO_PROYECTO:
    ok("...y la comparacion REAL del codigo casa con la fila del historico")
else:
    fallo("un segmento de proyecto del historico no cuenta como tal")

print("")
print("3. Canoniza el valor y NO el texto libre")
_f1 = valores.canonizar([{"Status": "En progreso", "Name": "Materiales SA",
                          "Note": "pendiente de revisar"}], "Projects")[0]
if _f1["Status"] == "In progress":
    ok("el valor de la columna de negocio se traduce")
else:
    fallo("no traduce el valor: %r" % _f1["Status"])
if _f1["Name"] == "Materiales SA" and _f1["Note"] == "pendiente de revisar":
    ok("el texto libre se queda intacto (nombre y nota)")
else:
    fallo("reescribio texto libre: %r" % _f1)
if valores.canonizar([{"Status": "En progreso"}]) == [{"Status": "En progreso"}]:
    ok("sin hoja no toca nada (no adivina)")
else:
    fallo("canoniza sin saber la hoja")

print("")
print("4. Las constantes de negocio estan en ingles")
CONST = ("ESTADOS", "ESTADOS_MANUAL", "TIPOS", "TIPOS_INTERNOS", "CATEGORIAS",
         "CAT_DEFAULT", "ROLES", "UNIDADES", "UBIC_TIPOS", "CONDICIONES", "MOV_TIPOS")
viejos = []
for p in sorted(Path("core").glob("*.py")):
    if p.stem in ("payroll", "roster", "valores", "i18n"):
        continue
    try:
        m = importlib.import_module("core." + p.stem)
    except Exception:
        continue
    for n in CONST:
        v = getattr(m, n, None)
        if isinstance(v, (list, tuple)):
            viejos += ["%s.%s=%r" % (p.stem, n, x) for x in v
                       if isinstance(x, str) and x in valores.LEGADO]
if viejos:
    for v in viejos[:8]:
        fallo("constante con valor viejo: %s" % v)
else:
    ok("ninguna constante de negocio conserva un valor viejo")

print("")
print("5. La NOMINA queda fuera a proposito, y sigue calculando")
# ⚠️ `payroll.TIPOS` vive dentro de ConceptsJSON, no en una columna: la canonizacion
# al leer no lo alcanza, asi que renombrarlo mataria `neto()` contra las nominas ya
# emitidas. Se comprueba que sigue en español Y que el neto sale bien.
if payroll.TIPOS == ["devengo", "deduccion", "aporte"]:
    ok("payroll.TIPOS sigue en español (es dato dentro de un JSON)")
else:
    fallo("payroll.TIPOS se migro: las nominas ya emitidas dejarian de sumar → %r"
          % payroll.TIPOS)
_conc = [{"tipo": "devengo", "monto": 100}, {"tipo": "deduccion", "monto": 30},
         {"tipo": "aporte", "monto": 50}]
_n = payroll.neto(1000, _conc)
if abs(_n - 1070.0) < 0.01:
    ok("neto(1000, +100 −30, aporte 50) = %.2f (el aporte no descuenta)" % _n)
else:
    fallo("el neto cambio: %.2f (esperado 1070.00)" % _n)

print("")
print("6. Los lectores CRUDOS tambien canonizan valores")
sin = []
for p in sorted(Path("core").glob("*.py")):
    if p.stem in ("hojas", "valores", "columnas"):
        continue
    src = p.read_text(encoding="utf-8")
    if "get_all_records" not in src:
        continue
    hojas_val = {h for (h, _c) in valores.COLUMNAS}
    tiene = any(getattr(importlib.import_module("core." + p.stem), n, None) in hojas_val
                for n in dir(importlib.import_module("core." + p.stem)) if n.endswith("SHEET"))
    if tiene:
        sin += _sin_canonizar(src, p.name)
if sin:
    for s in sin:
        fallo("lee una hoja de valores sin canonizarlos: %s" % s)
else:
    ok("las lecturas crudas de hojas con valores canonizan")

# ⚠️ La sonda se VALIDA en las DOS direcciones antes de creerse su cero (trampa nº12):
# tiene que cazar la lectura cruda Y no marcar la que canoniza partida en dos líneas
# — su versión anterior comparaba TEXTO por línea y denunciaba código correcto, que
# es lo que empuja a «arreglar» lo que está bien (v385) y lo que ya pasó en v472.
_MALO = "def f(ws):\n    recs = ws.get_all_records(numericise_ignore=['all'])\n    return recs\n"
_BUENO = ("def f(ws):\n    recs = valores.canonizar(columnas.canonizar(\n"
          "        ws.get_all_records(numericise_ignore=['all'])), SHEET)\n    return recs\n")
if bool(_sin_canonizar(_MALO, "x.py")) and _sin_canonizar(_BUENO, "x.py") == []:
    ok("la sonda ve la lectura cruda y NO marca la partida en dos lineas")
else:
    fallo("la sonda del bloque 6 no distingue: cruda=%s partida=%s"
          % (_sin_canonizar(_MALO, "x.py"), _sin_canonizar(_BUENO, "x.py")))

print("")
print("7. Contra la hoja REAL: el rol llega canonico, venga como venga")
# ⚠️ Este bloque decia «con la hoja en español» y media eso. Al MIGRAR la hoja (v469,
# 5 celdas de Login.Role) la afirmacion se convirtio en la IDENTIDAD, asi que su verde
# dejo de probar la canonizacion sin que nada lo dijera — un chequeo que afirma una
# cosa y mide otra es la trampa nº1. Ahora se comprueban las DOS direcciones, y la de
# la fila sin migrar con un caso CONSTRUIDO, porque en la hoja ya no queda ninguna.
try:
    u = auth.get_user("dacox")
    if not u:
        print("   ⚠️ no hay usuario 'dacox': el chequeo no puede afirmar nada")
        sys.exit(2)
    if u.get("Role") in ("owner", "administrator", "field"):
        ok("hoja MIGRADA: get_user('dacox').Role = %r (identidad)" % u.get("Role"))
    else:
        fallo("el rol llega %r: no es canonico" % u.get("Role"))
    # y la fila SIN migrar, que es lo que la capa de compatibilidad existe para cubrir
    _vieja = valores.canonizar([{"Role": "propietario"}, {"Role": "campo"}], "Login")
    if [r["Role"] for r in _vieja] == ["owner", "field"]:
        ok("hoja SIN migrar: 'propietario'/'campo' -> 'owner'/'field' (canonizacion)")
    else:
        fallo("una fila vieja de Login no canoniza: %r" % _vieja)
except SystemExit:
    raise
except Exception as e:
    fallo("no se pudo leer la hoja real: %s" % e)


print("\n9. Ningun ROL literal fuera de `auth.ROLES` llega a las funciones que validan")
# ⚠️ El hueco que dejo pasar «Invalid role» en v475: el barrido de arriba mira
# COMPARACIONES y estos entraban como ARGUMENTO. Los nombres de funcion se declaran
# (son las que validan contra ROLES); los roles validos se DERIVAN de la constante.
_FN_ROL = {"add_user", "set_role"}


def roles_literales(src):
    """[(funcion, valor, linea)] de cada rol literal pasado a una de esas funciones."""
    try:
        arbol = ast.parse(src)
    except SyntaxError:
        return []
    out = []
    for n in ast.walk(arbol):
        if not isinstance(n, ast.Call):
            continue
        fn = getattr(n.func, "attr", None) or getattr(n.func, "id", None) or ""
        if fn not in _FN_ROL:
            continue
        for a in list(n.args) + [k.value for k in n.keywords]:
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                out.append((fn, a.value, n.lineno))
    return out


# la sonda, validada contra un caso construido antes de creerse su cero (trampa nº12)
_MALO = 'auth.add_user(u, pw, "campo", nm, grupo)'
_BUENO = 'auth.add_user(u, pw, "field", nm, grupo)'
_ve_malo = [v for _fn2, v, _l2 in roles_literales(_MALO) if v not in auth.ROLES]
_ve_bueno = [v for _fn2, v, _l2 in roles_literales(_BUENO) if v not in auth.ROLES]
(ok if (_ve_malo and not _ve_bueno) else fallo)(
    "la sonda ve el rol viejo y no marca el canonico")

_malos = []
# ⚠️ `_fich`, NO `_f`: `_f` es la LISTA DE FALLOS de este guardian. Usarla como
# variable de bucle la deja valiendo "app.py" y el veredicto final cuenta
# `len("app.py")` = 6 fallos que no existen — el shadowing de v440, aqui dentro.
for _fich in sorted(os.listdir("core")) + ["app.py"]:
    _ruta = os.path.join("core", _fich) if _fich != "app.py" else "app.py"
    if not _ruta.endswith(".py"):
        continue
    for _fn, _v, _ln in roles_literales(open(_ruta, encoding="utf-8").read()):
        if _v not in auth.ROLES:
            _malos.append("%s:%d %s(… %r …) — no esta en ROLES=%s"
                          % (os.path.basename(_ruta), _ln, _fn, _v, auth.ROLES))
# ⚠️ `ok()` de este guardian acepta UN solo argumento: el detalle va en el mensaje.
(ok if not _malos else fallo)(
    "todas las llamadas pasan un rol de `auth.ROLES`"
    + ("" if not _malos else " -> " + " · ".join(_malos)))

print("")
print("10. v487 · el valor viejo tampoco se BUSCA ni se ESCRIBE")
import ast as _ast9
from pathlib import Path as _P9
from core import valores as _V9

_VIEJOS9 = {k for k, v in _V9.LEGADO.items() if k != v}
_COLS9 = {c for _, c in _V9.COLUMNAS}


def _es_viejo9(n):
    return (isinstance(n, _ast9.Constant) and isinstance(n.value, str)
            and n.value in _VIEJOS9)


def _barre9(fuentes):
    """(busquedas, escrituras) sobre {nombre: arbol}."""
    # ⚠️ Discriminador de las BUSQUEDAS: muchas palabras viejas son tambien CLAVES
    # internas de diccionarios que la propia app construye (`usuario`, `proyecto`,
    # `entrada`, `pendiente`…), y buscarlas ahi es correcto. Lo que falla es buscar una
    # clave que NADIE mete a mano: esa solo puede venir de los DATOS, y los datos llegan
    # canonizados. Sin este matiz la red daba 171 falsos positivos (v450: un detector
    # que grita sobre lo que esta bien acaba ignorandose).
    construidas = set()
    for arb in fuentes.values():
        for n in _ast9.walk(arb):
            if isinstance(n, _ast9.Dict):
                construidas |= {k.value for k in n.keys if isinstance(k, _ast9.Constant)}
            elif isinstance(n, _ast9.Assign):
                for tg in n.targets:
                    if isinstance(tg, _ast9.Subscript) and isinstance(tg.slice, _ast9.Constant):
                        construidas.add(tg.slice.value)
            elif isinstance(n, _ast9.Call) and getattr(n.func, "id", "") == "dict":
                construidas |= {kw.arg for kw in n.keywords if kw.arg}
    busq, escr = [], []
    for nom, arb in fuentes.items():
        for n in _ast9.walk(arb):
            if (isinstance(n, _ast9.Call) and getattr(n.func, "attr", "") == "get"
                    and n.args and _es_viejo9(n.args[0])
                    and n.args[0].value not in construidas):
                busq.append("%s:%d .get(%r)" % (nom, n.lineno, n.args[0].value))
            elif (isinstance(n, _ast9.Subscript) and _es_viejo9(n.slice)
                    and isinstance(n.ctx, _ast9.Load) and n.slice.value not in construidas):
                busq.append("%s:%d [%r]" % (nom, n.lineno, n.slice.value))
            elif isinstance(n, _ast9.Dict):
                for k, v in zip(n.keys, n.values):
                    if isinstance(k, _ast9.Constant) and k.value in _COLS9 and _es_viejo9(v):
                        escr.append("%s:%d {%r: %r}" % (nom, v.lineno, k.value, v.value))
            elif (isinstance(n, _ast9.Assign) and len(n.targets) == 1
                    and isinstance(n.targets[0], _ast9.Subscript)
                    and isinstance(n.targets[0].slice, _ast9.Constant)
                    and n.targets[0].slice.value in _COLS9 and _es_viejo9(n.value)):
                escr.append("%s:%d [%r] = %r" % (nom, n.lineno, n.targets[0].slice.value,
                                                 n.value.value))
            elif isinstance(n, _ast9.BoolOp) and isinstance(n.op, _ast9.Or):
                for v in n.values[1:]:
                    if _es_viejo9(v):
                        escr.append("%s:%d or %r" % (nom, v.lineno, v.value))
        for f in [x for x in _ast9.walk(arb) if isinstance(x, _ast9.FunctionDef)]:
            if not any(isinstance(c, _ast9.Call) and getattr(c.func, "attr", "")
                       in ("append_row", "append_rows") for c in _ast9.walk(f)):
                continue
            for lst in [x for x in _ast9.walk(f) if isinstance(x, _ast9.List)]:
                for sub in _ast9.walk(lst):
                    if _es_viejo9(sub):
                        escr.append("%s:%d fila de %s(): %r" % (nom, sub.lineno, f.name,
                                                                 sub.value))
    return sorted(set(busq)), sorted(set(escr))


# ⚠️ La red se VALIDA contra el fallo real construido antes de creerse su cero (trampa
# n12): una clave vieja que nadie construye, una escritura y un defecto por `or`.
_caso9 = _ast9.parse(
    "def resumen():\n"
    "    por = {}\n"
    "    for a in xs:\n"
    "        por[a.get('Status')] = 1\n"
    "    return por\n"
    "def kpi(est):\n"
    "    return est.get('disponible', 0)\n"
    "def alta(w):\n"
    "    w.append_row(['A1', 'disponible'])\n"
    "def rol(u):\n"
    "    return u.get('Role') or 'campo'\n"
    "def sano(r):\n"
    "    d = {'usuario': 1}\n"
    "    return r.get('usuario')\n")
_b9, _e9 = _barre9({"caso": _caso9})
(ok if (any("disponible" in x for x in _b9) and any("disponible" in x for x in _e9)
        and any("campo" in x for x in _e9) and not any("usuario" in x for x in _b9))
 else fallo)("la red VE el fallo construido (busqueda, fila y `or`) y NO marca la clave interna"
             + ("" if _b9 else " -> no vio nada: %r %r" % (_b9, _e9)))

_fuentes9 = {}
for _p9 in sorted(_P9("core").glob("*.py")) + [_P9("app.py")]:
    _fuentes9[_p9.name] = _ast9.parse(io.open(_p9, encoding="utf-8").read())
_b9, _e9 = _barre9(_fuentes9)
(ok if not _b9 else fallo)(
    "ninguna BUSQUEDA de un valor viejo que nadie construye (dejaba KPIs en 0)"
    + ("" if not _b9 else " -> " + " · ".join(_b9)))
(ok if not _e9 else fallo)(
    "ninguna ESCRITURA ni defecto con un valor viejo (hoja mezclada / owner preseleccionado)"
    + ("" if not _e9 else " -> " + " · ".join(_e9)))

print("")
if _f:
    print("FALLOS: %d" % len(_f))
    sys.exit(1)
print("TODO OK - v469")
