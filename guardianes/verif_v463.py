# -*- coding: utf-8 -*-
"""v463 · un VALOR DE NEGOCIO no puede pintarse en espanol.

Generaliza el chequeo de v462, que estaba acotado a `correcciones`. El fallo tiene
DOS mitades y arreglar una sola no cambia nada en pantalla:
  1. la celda pinta el valor CRUDO, sin `etiqueta()`;
  2. el valor no esta en `i18n.VALORES`, asi que `etiqueta()` lo devuelve tal cual.
Ninguna de las 14 redes de i18n lo ve: todas miden el CODIGO y aqui el texto viene
de la HOJA.

Cada red se VALIDA contra un caso construido antes de creerse su cero (trampa n12).
"""
import ast
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)                       # los secrets se buscan desde el CWD (trampa n19)
sys.path.insert(0, RAIZ)

fallos = []
n_ok = 0


def ok(msg):
    global n_ok
    n_ok += 1
    print("   ok   " + msg)


def fallo(msg):
    fallos.append(msg)
    print("   FALLO " + msg)


def fuente(mod):
    return io.open(os.path.join("core", mod + ".py"), encoding="utf-8").read()


# ── LA RED: celdas de tabla que pintan una columna de negocio ──────
# ⚠️ Lista DECLARADA, no adivinada: son las columnas cuyo contenido es un valor de
# negocio (esta en `i18n.VALORES`). Se quedo corta una vez —le faltaba «Unidad» y una
# rotura se escapo—, asi que al añadir una columna de negocio hay que meterla aqui.
COLS = {"Status", "Category", "Type", "Role", "Unit", "Condition", "LocationType"}


def celdas_crudas(src):
    """(cabecera, columna) de cada valor de un dict-fila dentro de un pd.DataFrame
    que lee una columna de NEGOCIO sin pasar por etiqueta()/_etq()."""
    try:
        tr = ast.parse(src)
    except SyntaxError:
        return []
    out = []
    for n in ast.walk(tr):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "DataFrame"):
            continue
        for d in ast.walk(n):
            if not isinstance(d, ast.Dict):
                continue
            for k, v in zip(d.keys, d.values):
                if not (isinstance(k, ast.Constant) and isinstance(k.value, str)):
                    continue
                dump = ast.dump(v)
                # ⚠️ Las TRES formas en que el repo llama a la traduccion. Con
                # solo las dos primeras, un `etiqueta(...)` importado pelado
                # salia marcado siendo CORRECTO — la sonda midiendo por la
                # forma en que se escribio la primera vez (v450/v459).
                if ("attr='etiqueta'" in dump or "id='_etq'" in dump
                        or "id='etiqueta'" in dump):
                    continue          # ya se traduce
                for sub in ast.walk(v):
                    if (isinstance(sub, ast.Call)
                            and isinstance(sub.func, ast.Attribute)
                            and sub.func.attr == "get" and sub.args
                            and isinstance(sub.args[0], ast.Constant)
                            and sub.args[0].value in COLS):
                        # ⚠️ un .get() dentro de una COMPARACION no es un pintado
                        if any(isinstance(c, ast.Compare) for c in ast.walk(v)):
                            continue
                        out.append((k.value, sub.args[0].value))
    return out


print("1. La red distingue una celda cruda de una traducida")
_MALO = 'df = pd.DataFrame([{"Status": r.get("Status", "")} for r in xs])'
_BUENO = 'df = pd.DataFrame([{"Status": _etq(str(r.get("Status", "")))} for r in xs])'
if celdas_crudas(_MALO) and not celdas_crudas(_BUENO):
    ok("ve la cruda y no marca la traducida")
else:
    fallo("la red NO distingue: su cero no significaria nada")

print("")
print("2. Ninguna tabla pinta un valor de negocio CRUDO")
# ⚠️ El Tipo de una CREDENCIAL (White Card, Forklift...) ya esta en ingles y esta
# fuera del mapa a proposito: no hay nada que traducir ahi.
EXENTO = {("auth_ui.py", "Tipo")}
_crudas = []
for f in sorted(os.listdir("core")):
    if not f.endswith("_ui.py"):
        continue
    for cab, col in celdas_crudas(fuente(f[:-3])):
        if (f, cab) not in EXENTO:
            _crudas.append((f, cab, col))
if not _crudas:
    ok("0 celdas crudas en los modulos de interfaz")
else:
    for f, cab, col in _crudas:
        fallo("%s pinta %r con .get(%r) sin etiqueta()" % (f, cab, col))

print("")
print("3. Todo valor de negocio que se MUESTRA esta en i18n.VALORES")
# ⚠️ Se DESCUBREN importando, no leyendo el AST: `correcciones.ESTADOS` y
# `ausencias.ESTADOS` se definen por NOMBRE —`ESTADOS = (PENDIENTE, APROBADA, ...)`—
# asi que un barrido de literales no los ve, y son justo los de v461 y v430. Y se
# descubren en vez de listarse: una lista fija hay que acordarse de ampliarla, que es
# el fallo que este guardian existe para no repetir.
import importlib

CONSTANTES = ("ESTADOS", "TIPOS", "TIPOS_INTERNOS", "CATEGORIAS", "CAT_DEFAULT",
              "ROLES", "UNIDADES", "UBIC_TIPOS", "CONDICIONES", "MOV_TIPOS")
# ⚠️ `roster.ESTADOS` fuera: sus claves (OFF/LEAVE/FORMACION) son identificadores y lo
# que se pinta es su `nombre`, ya en ingles. `credentials.CATALOGO` fuera: los tipos de
# ticket (White Card, Forklift...) ya estan en ingles y no son valores traducibles.
EXENTAS = {("roster", "ESTADOS"), ("credentials", "CATALOGO")}
# ⚠️ Valores exentos UNO A UNO y con razon: son simbolos de unidad, iguales en los
# dos idiomas. Mapearlos a si mismos seria un «mapa espejo», que v450 mando borrar.
EXENTOS_VAL = {("catalogo", "UNIDADES", "m"), ("catalogo", "UNIDADES", "m²"),
               ("catalogo", "UNIDADES", "kg"),
               # ⚠️ v469 · `payroll.TIPOS` se queda en ESPAÑOL a proposito, y no es
               # pereza: no vive en una columna sino DENTRO de `ConceptsJSON`, asi que
               # migrarlo obliga a reescribir el JSON de cada nomina del historico.
               # Es la misma clase que `schedule.PHASES` (v448/v453): migracion de
               # datos, no traduccion. Lo que si esta verificado — y es lo que hace
               # que la exencion sea segura — es que la constante, las escrituras
               # (`"tipo": "devengo"`) y las comparaciones (`_tp == "deduccion"`)
               # siguen las TRES en espanol: una traduccion a medias aqui dejaria de
               # restar las deducciones del neto, en silencio (el fallo de v447).
               ("payroll", "TIPOS", "devengo"), ("payroll", "TIPOS", "deduccion"),
               ("payroll", "TIPOS", "aporte"),
               # ⚠️ v472 · `manual` se escribe IGUAL en los dos idiomas, asi que
               # mapearlo seria un «mapa espejo» (v450); y a `datasheet`, termino
               # tecnico que en español se usa tal cual, habria que inventarle una
               # clave que nadie escribe. Misma clase que los simbolos de arriba.
               ("library", "TIPOS", "manual"),
               ("library", "TIPOS", "datasheet")}

from core import i18n
from core import valores as VALORES_MOD, inventory, catalogo
_CANON = set(i18n.VALORES.values())   # el vocabulario canonico COMPLETO
_listas, _falta = [], []
for _f in sorted(os.listdir("core")):
    if not _f.endswith(".py") or _f.startswith("_"):
        continue
    _nom = _f[:-3]
    try:
        _mod = importlib.import_module("core." + _nom)
    except Exception:
        continue                      # un modulo que no importa lo caza otro guardian
    for _c in CONSTANTES:
        if (_nom, _c) in EXENTAS or not hasattr(_mod, _c):
            continue
        _v = getattr(_mod, _c)
        if not isinstance(_v, (list, tuple)):
            continue
        _vals = [x for x in _v if isinstance(x, str) and x]
        if not _vals:
            continue
        _listas.append("%s.%s" % (_nom, _c))
        for _x in _vals:
            if (_nom, _c, _x) in EXENTOS_VAL:
                continue
            # ⚠️ CADUCADO EN v469, INVERTIDO — no relajado. Hasta v468 se exigía que el
            # valor fuera CLAVE de `VALORES` (dato español → display inglés). v469 migra
            # el dato a inglés, así que ahora es el VALOR. El principio no cambia: un
            # valor que puede estar en una fila no puede mostrarse como otra cosa.
            # Dos invariantes lo cubren, y las dos cazan una constante que se quedara
            # a medio migrar (que es el peor caso: traducción parcial dentro de la
            # misma lista, v443/v450):
            #   • `etiqueta()` no lo reescribe  → si siguiera en español, lo haría
            #   • `canon()` lo deja igual      → la constante ES la forma canónica
            if i18n.etiqueta(_x) != _x:
                _falta.append("%s.%s: %r → `etiqueta()` lo cambia a %r (sin migrar?)"
                              % (_nom, _c, _x, i18n.etiqueta(_x)))
            elif VALORES_MOD.canon(_x) != _x:
                _falta.append("%s.%s: %r → `canon()` lo cambia a %r (no es canónico)"
                              % (_nom, _c, _x, VALORES_MOD.canon(_x)))
            # ⚠️ AÑADIDA EN v472, y es la que faltaba. Las dos de arriba son
            # CIERTAS para cualquier cadena que el vocabulario no conozca, asi
            # que un valor en español SIN mapear pasaba por delante: `etiqueta()`
            # devuelve tal cual lo que no conoce (v462). Se escapo una rotura
            # real de v472 («un tipo vuelve al español») por este hueco.
            # Que el valor sea un canonico CONOCIDO es lo unico que separa
            # «esta migrado» de «nadie lo ha mirado nunca».
            elif _x not in _CANON:
                _falta.append("%s.%s: %r → no es un canonico conocido: o se mapea"
                              " en i18n.VALORES, o se exime con razon"
                              % (_nom, _c, _x))

if len(_listas) < 8:
    fallo("solo se descubrieron %d listas: el chequeo estaria pasando en vacio" % len(_listas))
elif not _falta:
    ok("las %d listas descubiertas estan mapeadas (%s)" % (len(_listas), ", ".join(_listas)))
else:
    for _x in _falta:
        fallo("valor sin traduccion, saldria en espanol -> " + _x)

print("4. La constante y sus COMPARACIONES se movieron JUNTAS (sin ramas muertas)")
# ⚠️ CADUCADO EN v469, INVERTIDO — no relajado. Hasta v468 esto exigia que el valor
# siguiera en espanol, PORQUE traducir solo la constante deja la comparacion muerta y
# eso no da ningun error (v442: la rama del Caso 1 de corte de rieles). v469 traduce
# las DOS a la vez, asi que el riesgo no desaparece: cambia de forma. Lo que se
# comprueba ahora es justo el fallo que se quiere evitar — que no quede en el modulo
# una comparacion contra el literal VIEJO, que ya no puede casar nunca.
import re as _re
import tokenize as _tk, io as _io2


def _sin_comentarios(src):
    """⚠️ Un comentario NO es un uso (trampa nº2). Buscar la comparación por texto
    encontraba la nota que explica por qué existía — y daba un FALLO inexistente."""
    try:
        return "".join(
            "" if t.type == _tk.COMMENT else t.string + " "
            for t in _tk.generate_tokens(_io2.StringIO(src).readline))
    except Exception:
        return src

_PARES = [("inventory", inventory, "ESTADOS", {"en_uso": "in use", "disponible": "available",
                                              "mantenimiento": "maintenance",
                                              "dañado": "damaged", "baja": "written off"}),
          ("catalogo", catalogo, "TIPOS", {"producto": "product", "servicio": "service"})]
for _nm, _mod, _cte, _mapa in _PARES:
    _vals = list(getattr(_mod, _cte))
    _sin_migrar = [v for v in _mapa.values() if v not in _vals]
    if _sin_migrar:
        fallo("%s.%s no es canonico: falta %s" % (_nm, _cte, _sin_migrar))
        continue
    # el literal VIEJO no puede seguir en una comparacion de ninguno de los dos modulos
    _muertas = []
    for _f in ("core/%s.py" % _nm, "core/%s_ui.py" % _nm):
        if not os.path.exists(_f):
            continue
        _src = _sin_comentarios(io.open(_f, encoding="utf-8").read())
        for _viejo in _mapa:
            for _m in _re.finditer(r"[=!]=\s*[\"']%s[\"']" % _re.escape(_viejo), _src):
                _muertas.append("%s: %s" % (_f, _m.group(0)))
    if _muertas:
        fallo("%s: comparacion contra el literal VIEJO = rama MUERTA → %s"
              % (_nm, ", ".join(_muertas)))
    else:
        ok("%s.%s es canonico y no quedan comparaciones al valor viejo" % (_nm, _cte))

print("")
print("5. El texto del estado tiene UNA definicion; el color va aparte")
_inv = fuente("inventory_ui")
_tree = ast.parse(_inv)
_color = None
for n in _tree.body:
    if isinstance(n, ast.Assign) and any(
            isinstance(t_, ast.Name) and t_.id == "_EST_COLOR" for t_ in n.targets):
        _color = n.value
if _color is None:
    fallo("no existe _EST_COLOR: el texto volvio al modulo")
elif isinstance(_color, ast.Dict):
    _vals = [v.value for v in _color.values
             if isinstance(v, ast.Constant) and isinstance(v.value, str)]
    if all(" " not in v and "[" not in v for v in _vals):
        ok("_EST_COLOR guarda colores, no frases (%s)" % ", ".join(_vals))
    else:
        fallo("_EST_COLOR volvio a llevar el TEXTO: dos definiciones del estado")

# y la ficha tiene que seguir pintando EXACTAMENTE lo de antes
from core.inventory_ui import _est_lbl
# ⚠️ v469 migro las CLAVES a ingles; lo que este chequeo protege es que **el texto
# que ve la persona no cambie**, asi que se indexa por el valor canonico y se compara
# contra el MISMO resultado verbatim de v463. Si el dia de manana alguien toca el
# color o el texto, sigue saltando.
ANTES = {"available": ":green[available]", "in use": ":blue[in use]",
         "maintenance": ":orange[maintenance]", "damaged": ":red[damaged]",
         "written off": ":gray[written off]"}
_dif = [e for e in inventory.ESTADOS if _est_lbl(e) != ANTES.get(e)]
if not _dif:
    ok("la ficha del activo pinta lo mismo que antes de v463")
else:
    fallo("cambio lo que ve el usuario en la ficha: " + ", ".join(_dif))
# ⚠️ Y la fila SIN MIGRAR: durante la ventana entre el deploy y la migracion de la
# hoja, un activo puede seguir diciendo «disponible». `canon` lo traduce al leer, asi
# que la ficha tiene que acabar pintando exactamente lo mismo.
_legacy = {"disponible": "available", "en_uso": "in use", "mantenimiento": "maintenance",
           "dañado": "damaged", "baja": "written off"}
_mal = [v for v, c in _legacy.items()
        if VALORES_MOD.canon(v) != c or _est_lbl(VALORES_MOD.canon(v)) != ANTES[c]]
if not _mal:
    ok("un activo SIN migrar («disponible») sigue pintando lo mismo")
else:
    fallo("la fila vieja deja de resolver: " + ", ".join(_mal))

print("")
print("6. El markdown de color NO se cuela en una celda de tabla")
# `_est_lbl` devuelve ':green[...]', que st.dataframe pintaria LITERAL.
_mal = []
for n in ast.walk(_tree):
    if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == "DataFrame"):
        continue
    if "id='_est_lbl'" in ast.dump(n):
        _mal.append("DataFrame")
if not _mal:
    ok("_est_lbl no aparece dentro de ningun DataFrame")
else:
    fallo("_est_lbl dentro de un DataFrame: pintaria ':green[...]' literal")

print("")
print("7. La ubicacion que se ESCRIBE en el historial NO se traduce")
# ⚠️ `ubic_str` la usan 5 llamadas de `_log_mov` (el texto va a la HOJA) y 1 de
# pantalla. Traducir DENTRO metería ingles en el dato — el fallo que casi se cuela en
# v452 — asi que el traductor va por parametro y solo lo pasa la pantalla.
from core import inventory as _INV
_a = {"LocationType": "bodega", "LocationRef": "X"}
if _INV.ubic_str(_a) == "bodega: X":
    ok("sin traductor devuelve el dato en español (lo que se guarda)")
else:
    fallo("ubic_str traduce por defecto: el historial guardaria ingles -> %r"
          % _INV.ubic_str(_a))
if _INV.ubic_str(_a, i18n.etiqueta) == "warehouse: X":
    ok("con traductor devuelve el texto de pantalla")
else:
    fallo("ubic_str no traduce ni pasandole el traductor")
_src_inv = fuente("inventory")
import ast as _ast
for _n in _ast.walk(_ast.parse(_src_inv)):
    if (isinstance(_n, _ast.Call) and isinstance(_n.func, _ast.Name)
            and _n.func.id == "_log_mov"):
        if "etiqueta" in _ast.dump(_n) or "etq" in _ast.dump(_n):
            fallo("una escritura de _log_mov traduce la ubicacion")


print("")
print("8. Ningun sitio MEZCLA un valor migrado con uno sin migrar")
# ⚠️ Es el peor caso de una migracion (v443/v450): el productor devuelve el valor
# nuevo y el consumidor indexa por el viejo, asi que la rama no casa NUNCA y no da
# ningun error. Paso de verdad en v469: `invoices.estado_cobro` devolvia `anulada`,
# `cobrada`, `vencida` y `parcial` en espanol y `pending` migrado, asi que el chip de
# factura perdia icono y color y salia el texto crudo.
#
# ⚠️ La red va sobre `i18n.VALORES` (vocabulario COMPLETO), NO sobre `valores.LEGADO`
# (solo lo que se migro): con LEGADO era CIEGA a este caso exacto, porque los cuatro
# estados espanoles no estan en el mapa de migracion. Un valor migrado FUERA de ese
# mapa es justo donde duele.
_VIEJO = set(i18n.VALORES)
_NUEVO = set(i18n.VALORES.values())
_AMBOS = _VIEJO & _NUEVO           # neutros (Delivery, Ripout...): no informan


def _mezclas():
    _out = []
    for _f in sorted(os.listdir("core")):
        if not _f.endswith(".py"):
            continue
        _a = ast.parse(io.open("core/" + _f, encoding="utf-8").read())
        for _n in ast.walk(_a):
            if isinstance(_n, ast.FunctionDef):
                _r = {_x.value.value for _x in ast.walk(_n)
                      if isinstance(_x, ast.Return)
                      and isinstance(_x.value, ast.Constant)
                      and isinstance(_x.value.value, str)}
                _v, _c = sorted((_r & _VIEJO) - _AMBOS), sorted((_r & _NUEVO) - _AMBOS)
                if _v and _c:
                    _out.append("return %s.%s: sin migrar=%s migrado=%s"
                                % (_f, _n.name, _v, _c))
            if isinstance(_n, ast.Dict):
                _k = {_x.value for _x in _n.keys
                      if isinstance(_x, ast.Constant) and isinstance(_x.value, str)}
                _v, _c = sorted((_k & _VIEJO) - _AMBOS), sorted((_k & _NUEVO) - _AMBOS)
                if _v and _c:
                    _out.append("claves %s:%d: sin migrar=%s migrado=%s"
                                % (_f, _n.lineno, _v, _c))
    return _out


# ⚠️ Validar la sonda ANTES de creerse su cero: se reintroduce la mezcla REAL de v469
# y tiene que verla. Sin este paso, un "0 mezclas" no significa nada (trampa nº12).
_pinv = "core/invoices.py"
_orig = io.open(_pinv, encoding="utf-8").read()
try:
    io.open(_pinv, "w", encoding="utf-8", newline="").write(
        _orig.replace('    return "pendiente"', '    return "pending"', 1))
    _ve = [m for m in _mezclas() if "invoices.py" in m]
finally:
    io.open(_pinv, "w", encoding="utf-8", newline="").write(_orig)
if _ve:
    ok("la sonda ve el caso conocido-bueno (%s)" % _ve[0][:60])
else:
    fallo("la sonda esta CIEGA: su cero no significaria nada")

_mz = _mezclas()
if not _mz:
    ok("0 mezclas en los %d modulos de core" % len([f for f in os.listdir("core")
                                                    if f.endswith(".py")]))
else:
    for _m in _mz:
        fallo("MEZCLA -> " + _m)

print("")
if fallos:
    print("FALLOS: %d" % len(fallos))
    sys.exit(1)
print("TODO OK - %d comprobaciones" % n_ok)
