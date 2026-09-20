# -*- coding: utf-8 -*-
"""v472 · la biblioteca tecnica: los invariantes que fallarian EN SILENCIO.

Ninguno de estos da un error en pantalla si se rompe — por eso hay guardian:
  1. las hojas GLOBALES  -> cada cliente acabaria con su propia biblioteca VACIA
  2. las hojas en el LOTE -> `registros(SHEET)` devuelve None y se lee vacio PARA
     SIEMPRE, sin un solo error (regla v353)
  3. `get_sheet` y no `_get_worksheet` -> escribir en un libro y leer de otro (v404)
  4. la descarga LAZY     -> un boton por ficha se baja TODO Drive en cada pasada (v147)
  5. solo el propietario sube (decision del usuario)
  6. el ORDEN de las escrituras con Drive (v343/v456)
  7. el ID no se recicla ni se cuenta por filas (v427/v428)
  8. `t` no vuelve a usarse como VARIABLE donde es la funcion de idioma (v446/v447)

Cada sonda se VALIDA contra un caso construido antes de creerse su cero (trampa n12).
"""
import ast
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)                       # los secrets se buscan desde el CWD (trampa n19)
sys.path.insert(0, RAIZ)

fallos, n_ok = [], 0


def ok(m, det=""):
    """⚠️ Acepta el 2º argumento y lo IGNORA, a proposito: el idioma de estos
    guardianes es `(ok if cond else fallo)(mensaje, detalle)`, asi que con `ok(m)`
    a secas el guardian **revienta justo cuando PASA** — y un guardian que revienta
    devuelve codigo != 0 siempre, o sea que una tanda entera de roturas saldria
    «cazada» sin probar nada (la leccion que el CONTROL de v463 destapo)."""
    global n_ok
    n_ok += 1
    print("   ok   " + m)


def fallo(m, det=""):
    fallos.append(m)
    print("   FALLO %s%s" % (m, ("  -> " + str(det)) if det else ""))


def fuente(mod):
    return io.open(os.path.join("core", mod + ".py"), encoding="utf-8").read()


def _fn(src, nombre):
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.FunctionDef) and n.name == nombre:
            return n
    return None


from core import hojas, home_ui, library as LIB, timeclock   # noqa: E402

_SRC_LIB = fuente("library")
_SRC_UI = fuente("library_ui")
_SRC_HOME = fuente("home_ui")


# ── 1 ────────────────────────────────────────────────────────────────────────
print("\n1. Las dos hojas son GLOBALES (una sola biblioteca, no una por cliente)")
_g = {str(x).lower() for x in timeclock.SHEETS_GLOBALES}
_faltan = [x for x in ("library", "librarymodels") if x not in _g]
(ok if not _faltan else fallo)(
    "Library y LibraryModels en SHEETS_GLOBALES", _faltan)

# ⚠️ Y se EJECUTA: que esten en el conjunto no prueba que el resolutor las mande al
# maestro (es lo unico que evita una biblioteca vacia por cliente).
try:
    _maestro = timeclock.sheet_id_para("Login", grupo="cliente1")
    _lib = timeclock.sheet_id_para("Library", grupo="cliente1")
    (ok if _lib == _maestro else fallo)(
        "`sheet_id_para('Library')` resuelve al MISMO libro que `Login` (el maestro)",
        "%r != %r" % (_lib, _maestro))
except Exception as e:
    fallo("no se pudo resolver el libro de Library", e)


# ── 2 ────────────────────────────────────────────────────────────────────────
print("\n2. Las dos hojas entran en el LOTE (regla v353: si no, se lee vacio SIEMPRE)")
_faltan = [x for x in ("Library", "LibraryModels") if x not in hojas.HOJAS_LECTURA]
(ok if not _faltan else fallo)("Library y LibraryModels en HOJAS_LECTURA", _faltan)


# ── 3 ────────────────────────────────────────────────────────────────────────
print("\n3. Las hojas se abren con `get_sheet` (el fallo REAL de v404)")
# `_get_worksheet` devuelve el libro del grupo de la SESION y el lector resuelve con
# `sheet_id_para`: mezclarlos hace escribir en un libro y leer de otro, en silencio.
_mal = []
for _nom in ("_ws", "_ws_modelos"):
    _f = _fn(_SRC_LIB, _nom)
    if _f is None:
        _mal.append("%s no existe" % _nom)
        continue
    _llam = {getattr(n.func, "attr", "") for n in ast.walk(_f) if isinstance(n, ast.Call)}
    if "get_sheet" not in _llam:
        _mal.append("%s no llama get_sheet" % _nom)
    if "_get_worksheet" in _llam:
        _mal.append("%s usa _get_worksheet (v404)" % _nom)
(ok if not _mal else fallo)("`_ws` y `_ws_modelos` usan `timeclock.get_sheet`", _mal)


# ── 4 ────────────────────────────────────────────────────────────────────────
print("\n4. La descarga es LAZY: ningun `download_button` dentro de un bucle (v147)")


def descargas_en_bucle(src):
    """`st.download_button` bajo un `for` = se baja TODO Drive en cada render."""
    out = []
    for n in ast.walk(ast.parse(src)):
        if not isinstance(n, (ast.For, ast.While)):
            continue
        for d in ast.walk(n):
            if (isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                    and d.func.attr == "download_button"):
                out.append("linea %d" % d.lineno)
    return out


_d = descargas_en_bucle(_SRC_UI)
(ok if not _d else fallo)("0 `download_button` dentro de un bucle", _d)

# ⚠️ La sonda, validada contra un caso construido: si no ve el caso malo, su cero
# no significa nada (trampa n12).
_probe = "import streamlit as st\nfor x in items:\n    st.download_button('d', data=b'')\n"
(ok if descargas_en_bucle(_probe) else fallo)(
    "la sonda de descargas VE el caso conocido-malo")

print("   · y la galeria esta PAGINADA (cada miniatura ES una descarga)")
_gal = _fn(_SRC_UI, "_galeria")


def _lista_pintada(fn):
    """El nombre de la coleccion que el bucle RECORRE (`for _ in range(0, len(X), 3)`).

    ⚠️ Se busca ESO y no la constante: `_POR_PAGINA` aparece CUATRO veces en
    `_galeria` (el total de paginas y los dos extremos del corte), asi que preguntar
    `"_POR_PAGINA" in dump` daba **verde con el corte BORRADO** — la trampa nº2
    (grep != uso) dentro del guardian, y por ahi se escapo una rotura real.
    """
    for n in ast.walk(fn):
        if not (isinstance(n, ast.For) and isinstance(n.iter, ast.Call)):
            continue
        if getattr(n.iter.func, "id", "") != "range":
            continue
        for a in ast.walk(n.iter):
            if (isinstance(a, ast.Call) and getattr(a.func, "id", "") == "len"
                    and a.args and isinstance(a.args[0], ast.Name)):
                return a.args[0].id
    return None


def _viene_de_un_corte(fn, nombre):
    """`nombre` se asigna de un CORTE (`fotos[a:b]`), no de la lista entera."""
    for n in ast.walk(fn):
        if not isinstance(n, ast.Assign):
            continue
        if not any(getattr(t_, "id", "") == nombre for t_ in n.targets):
            continue
        if isinstance(n.value, ast.Subscript) and isinstance(n.value.slice, ast.Slice):
            return True
    return False


_pint = _lista_pintada(_gal) if _gal is not None else None
_paginada = bool(_pint) and _viene_de_un_corte(_gal, _pint)
(ok if _paginada else fallo)(
    "lo que `_galeria` pinta viene de un CORTE, no de la lista entera", _pint)


# ── 5 ────────────────────────────────────────────────────────────────────────
print("\n5. Solo el PROPIETARIO sube o borra (decision del usuario)")
_rol_fn = _fn(_SRC_UI, "_puede_subir")
_owner = _rol_fn is not None and "owner" in [
    c.value for c in ast.walk(_rol_fn) if isinstance(c, ast.Constant) and isinstance(c.value, str)]
(ok if _owner else fallo)("`_puede_subir()` compara contra el rol `owner`")


def bajo_guardia(src, fn_name, llamadas):
    """¿Cada llamada de `llamadas` cuelga de un `if _puede_subir()`?"""
    f = _fn(src, fn_name)
    if f is None:
        return ["%s no existe" % fn_name]
    _prot = set()
    for n in ast.walk(f):
        if not isinstance(n, ast.If):
            continue
        if "_puede_subir" not in ast.dump(n.test):
            continue
        for d in ast.walk(n):
            if isinstance(d, ast.Call):
                _prot.add(getattr(d.func, "id", "") or getattr(d.func, "attr", ""))
    return [c for c in llamadas if c not in _prot]


_m = bajo_guardia(_SRC_UI, "render_biblioteca", ["_alta", "_catalogo"])
(ok if not _m else fallo)("el alta y el catalogo cuelgan de `_puede_subir()`", _m)
_m = bajo_guardia(_SRC_UI, "_detalle", ["delete_item"])
(ok if not _m else fallo)("el borrado cuelga de `_puede_subir()`", _m)


# ── 6 ────────────────────────────────────────────────────────────────────────
print("\n6. El ORDEN de las escrituras con Drive")


def _orden(fn_node, a, b):
    """Linea de la primera llamada `a` y de la primera `b` dentro de la funcion."""
    la = lb = None
    for n in ast.walk(fn_node):
        if not isinstance(n, ast.Call):
            continue
        _n = getattr(n.func, "attr", "") or getattr(n.func, "id", "")
        if _n == a and la is None:
            la = n.lineno
        if _n == b and lb is None:
            lb = n.lineno
    return la, lb


# subir: el ARCHIVO primero, la fila despues (si Drive falla, no queda una ficha que
# promete un documento que no existe) — el orden de v343.
_f = _fn(_SRC_UI, "_guardar")
_a, _b = _orden(_f, "upload_to", "add_item")
(ok if (_a and _b and _a < _b) else fallo)(
    "al FILAR: `upload_to` antes de `add_item`", "upload_to=%s add_item=%s" % (_a, _b))

# borrar: el ARCHIVO primero, la fila despues (al reves se pierde el DriveID con la
# fila y el archivo queda huerfano e inalcanzable) — el error de orden de v456.
_f = _fn(_SRC_UI, "_detalle")
_a, _b = _orden(_f, "delete", "delete_item")
(ok if (_a and _b and _a < _b) else fallo)(
    "al BORRAR: `delete` de Drive antes de `delete_item`", "delete=%s delete_item=%s" % (_a, _b))


# ── 7 ────────────────────────────────────────────────────────────────────────
print("\n7. El ID: ni se recicla (v427) ni se cuenta por filas (v428)")
_f = _fn(_SRC_LIB, "_next_id")
_dump = ast.dump(_f) if _f is not None else ""
(ok if "siguiente_id_libre" in _dump else fallo)(
    "`_next_id` salta los IDs referenciados (`siguiente_id_libre`)")
_cuenta = any(isinstance(n, ast.Call) and getattr(n.func, "id", "") == "len"
              for n in ast.walk(_f)) if _f is not None else False
(ok if not _cuenta else fallo)(
    "`_next_id` NO deriva el ID del NUMERO DE FILAS (el fallo real de v428)")

# ⚠️ La FIRMA, no el nombre (regla v135): `siguiente_id_libre(prefijo, maximo, propia=)`.
# Pasarla en otro orden lanza ValueError, que el `except` se traga -> el salto NO se
# aplica NUNCA y todo cae al max+1 de siempre, en silencio. Le pasaba a `correcciones`.
import inspect  # noqa: E402
_par = list(inspect.signature(hojas.siguiente_id_libre).parameters)
_lla = [n for n in ast.walk(_f) if isinstance(n, ast.Call)
        and getattr(n.func, "attr", "") == "siguiente_id_libre"]
_bien = bool(_lla) and all(
    len(c.args) == 2
    and isinstance(c.args[0], ast.Constant) and str(c.args[0].value).endswith("-")
    and all(k.arg in _par for k in c.keywords)
    for c in _lla)
(ok if _bien else fallo)(
    "la llamada casa con la firma `(prefijo, maximo, propia=…)`",
    "params=%s" % _par)


# ── 8 ────────────────────────────────────────────────────────────────────────
print("\n8. La fila posicional casa con HEADERS (el fallo que mato a create_project)")
_f = _fn(_SRC_LIB, "add_item")
_listas = [n for n in ast.walk(_f) if isinstance(n, ast.List) and len(n.elts) > 5]
(ok if _listas and len(_listas[0].elts) == len(LIB.HEADERS) else fallo)(
    "la fila de `add_item` tiene %d elementos = %d cabeceras"
    % (len(_listas[0].elts) if _listas else -1, len(LIB.HEADERS)))
# y la comprobacion en caliente sigue puesta (v306): un descuadre no puede escribirse
(ok if "Internal error: row does not match header" in _SRC_LIB else fallo)(
    "`add_item` se niega a escribir una fila descuadrada")


# ── 9 ────────────────────────────────────────────────────────────────────────
print("\n9. `t` no se usa como VARIABLE donde es la funcion de idioma (v446/v447)")


def t_como_variable(src):
    """Modulos que importan `t` de i18n y ademas lo usan como nombre corriente.
    ⚠️ Es el fallo REAL que v472 encontro en `home_ui.buscar`: la asignacion se
    renombro y tres usos se quedaron -> AttributeError que el `except` se tragaba, y
    el buscador no devolvia un trabajo NUNCA."""
    tr = ast.parse(src)
    _importa = any(isinstance(n, ast.ImportFrom) and n.module == "core.i18n"
                   and any(a.name == "t" and not a.asname for a in n.names)
                   for n in ast.walk(tr))
    if not _importa:
        return []
    out = []
    for n in ast.walk(tr):
        # asignado (`t = ...`), variable de bucle (`for t in ...`) o arg de funcion
        if isinstance(n, ast.Assign):
            for d in n.targets:
                if isinstance(d, ast.Name) and d.id == "t":
                    out.append("asignado en linea %d" % n.lineno)
        if isinstance(n, ast.For) and isinstance(n.target, ast.Name) and n.target.id == "t":
            out.append("variable de bucle en linea %d" % n.lineno)
        # llamado como si fuera un dict/fila: `t.get(...)`, `t["x"]`
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and isinstance(n.func.value, ast.Name) and n.func.value.id == "t"):
            out.append("`t.%s(...)` en linea %d" % (n.func.attr, n.lineno))
    return out


_mal = {}
for _f2 in sorted(os.listdir("core")):
    if not _f2.endswith(".py"):
        continue
    _r = t_como_variable(fuente(_f2[:-3]))
    if _r:
        _mal[_f2] = _r
(ok if not _mal else fallo)("ningun modulo usa `t` como variable", _mal)

# ⚠️ La sonda, validada contra el codigo ROTO de verdad (el que habia hasta v472).
_probe = ('from core.i18n import t\n'
          'def f(xs):\n'
          '    for _trb in xs:\n'
          '        return t.get("Number", "")\n')
(ok if t_como_variable(_probe) else fallo)(
    "la sonda de `t` VE el caso conocido-malo (el fallo real de v440)")


# ── 10 ───────────────────────────────────────────────────────────────────────
print("\n10. La seccion existe en los TRES roles y el despachador la compara por ID")
_m = [l for l in ("_SECCIONES", "_SECCIONES_CAMPO", "_SECCIONES_OWNER")
      if "biblioteca" not in [k for k, _ in getattr(home_ui, l)]]
(ok if not _m else fallo)("`biblioteca` en las tres listas de secciones", _m)
(ok if 'elif key == "biblioteca":' in _SRC_HOME else fallo)(
    "el despachador compara contra el ID exacto (un display navega a ninguna parte)")
# y NO tiene sub-pestañas, asi que su titulo lo pinta ELLA (v320: si no, se queda sin cabecera)
(ok if "biblioteca" not in home_ui._SUBSECCIONES else fallo)(
    "`biblioteca` no declara sub-pestañas")
(ok if 'st.markdown("## " + t(' in _SRC_UI else fallo)(
    "`render_biblioteca` pinta su propio titulo (v320)")


# ── 11 ───────────────────────────────────────────────────────────────────────
print("\n11. El buscador global (v330) encuentra material, EJECUTANDO")
import core.auth, core.projects, core.roster  # noqa: E402
core.projects.list_projects = lambda *a, **k: []
core.auth.list_users = lambda *a, **k: []
core.roster.list_trabajos = lambda *a, **k: [
    {"ID": "TRB-0007", "Name": "Grua Talavera", "Number": "89", "Active": "SI"}]
LIB._records = lambda: [
    {"ID": "LIB-0002", "Brand": "KONE", "Model": "MonoSpace", "Section": "Car door",
     "Type": "manual", "Title": "Door operator manual", "Notes": "", "Date": "2026-09-05"}]
_r = home_ui.buscar("monospace", "cliente1")
(ok if any(x["tipo"] == "biblioteca" for x in _r) else fallo)(
    "buscar('monospace') devuelve la ficha de biblioteca", _r)
# ⚠️ Y la otra fuente que el mismo fallo tenia rota: los TRABAJOS
_r = home_ui.buscar("talavera", "cliente1")
(ok if any(x["tipo"] == "trabajo" for x in _r) else fallo)(
    "buscar('talavera') devuelve el TRABAJO (roto desde v440 hasta v472)", _r)


# ── 12 ───────────────────────────────────────────────────────────────────────
print("\n12. Los valores de `TIPOS` son canonicos (no saldrian en español)")
from core import i18n, valores as VAL  # noqa: E402

# ⚠️ `etiqueta(x) == x` NO sirve para esto, y es la leccion de v462 mordiendo del
# otro lado: `etiqueta()` devuelve TAL CUAL lo que no conoce, asi que esa igualdad
# es cierta para un canonico Y para un español que nadie mapeo (`foto`, `bodega`,
# cualquier cosa). Era una afirmacion que **no podia fallar nunca**, y por ahi se
# escapo la rotura. Lo que si distingue: el valor tiene que ser un canonico CONOCIDO.
_CANON = set(i18n.VALORES.values())
# ⚠️ Exentos UNO A UNO y con razon, como los simbolos de v463 — no una lista comoda:
#   · `manual` se escribe IGUAL en los dos idiomas: mapearlo seria un «mapa espejo»,
#     que v450 mando borrar.
#   · `datasheet` es el termino tecnico que se usa tal cual en español; inventarle
#     una clave («ficha tecnica») seria adivinar un dato que nadie escribe.
_EXENTOS = {"manual", "datasheet"}
_m = [x for x in LIB.TIPOS if x not in _CANON and x not in _EXENTOS]
(ok if not _m else fallo)(
    "los %d tipos son canonicos conocidos (o exentos con razon)" % len(LIB.TIPOS), _m)

# ⚠️ La sonda, VALIDADA contra un caso conocido-malo antes de creerse su cero
# (trampa nº12): si no viera un tipo en español, el «0» de arriba no diria nada.
_vistos = [x for x in ("foto", "diagrama") if x not in _CANON and x not in _EXENTOS]
(ok if len(_vistos) == 2 else fallo)("la sonda VE un tipo en español si vuelve", _vistos)
# Y que `etiqueta()` los traduzca es lo que hace que el DATO viejo se siga viendo bien.
_tr = [(x, i18n.etiqueta(x)) for x in ("foto", "diagrama")]
(ok if all(a != b for a, b in _tr) else fallo)(
    "`etiqueta()` traduce el español heredado de esos tipos", _tr)


# ── 13 ───────────────────────────────────────────────────────────────────────
print("\n13. Ninguna pieza HTML del kit recibe sintaxis de icono")
# ⚠️ `theme.section/chip/kpi_row/_kpi_card` pintan HTML con `unsafe_allow_html`, y ahi
# `:material/…:` NO se interpreta: sale el literal en pantalla (v443). Se vio en
# produccion, mirando — ningun guardian lo veia.
_HTML_KIT = {"section", "chip", "kpi_row", "_kpi_card"}


def iconos_en_html(src):
    try:
        arbol = ast.parse(src)
    except SyntaxError:
        return []
    fuera = []
    for n in ast.walk(arbol):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
            continue
        if n.func.attr not in _HTML_KIT:
            continue
        for sub in ast.walk(n):
            if (isinstance(sub, ast.Constant) and isinstance(sub.value, str)
                    and ":material/" in sub.value):
                fuera.append((n.func.attr, sub.value[:40]))
    return fuera


# la sonda, validada en las dos direcciones antes de creerse su cero
_MALO = 'T.section(t(":material/photo_library: Photos"))'
_BUENO = 'T.section(t("Photos"))\nst.button(":material/save: Save")'
(ok if iconos_en_html(_MALO) and not iconos_en_html(_BUENO) else fallo)(
    "la sonda ve el icono en una pieza HTML y no marca el de un boton")

_kit = []
for _f in sorted(os.listdir("core")):
    if _f.endswith(".py"):
        _kit += [("%s: %s(%r)" % (_f, a, v))
                 for a, v in iconos_en_html(io.open(os.path.join("core", _f),
                                                    encoding="utf-8").read())]
(ok if not _kit else fallo)("0 piezas HTML del kit con sintaxis de icono", _kit)


print("")
if fallos:
    print("HAY FALLOS: %d de %d" % (len(fallos), len(fallos) + n_ok))
    sys.exit(1)
print("TODO OK - %d comprobaciones" % n_ok)
