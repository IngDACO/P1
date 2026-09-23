# -*- coding: utf-8 -*-
"""v470 · el tipo «Ripout + Installation».

⚠️ Lo que este guardián protege NO es la fase nueva: es que los TRES caminos que dan
de alta un proyecto decidan el cronograma con la MISMA regla. Hasta v470 la pregunta
«¿este tipo genera cronograma?» se hacía en tres sitios y uno comparaba contra el
LITERAL, así que añadir un tipo a dos de ellos lo dejaba comportándose como «Other»
**sin dar ningún error** — es el fallo de v454, donde una obra creada desde cotización
nació con CERO actividades y se quedó clavada en 0% para siempre.

Todo se comprueba EJECUTANDO: importar no ejecuta (v378) y este fallo vive dentro de
la función, no en su firma.
"""
import ast
import io
import os
import sys
from datetime import date

sys.path.insert(0, os.path.abspath("."))

fallos = []
n_ok = 0


def ok(m, det=""):
    # ⚠️ Acepta el detalle y lo ignora: el idioma `(ok if cond else fallo)(msg, det)`
    # llama a las dos con la misma firma, y sin esto revienta justo cuando PASA.
    global n_ok
    n_ok += 1
    print("   ok   %s" % m)


def fallo(m, det=""):
    fallos.append(m)
    print("   FALLO %s%s" % (m, ("  -> " + str(det)) if det else ""))


def sec(t):
    print("\n%s" % t)


from core import projects as P, schedule as S, quotes as Q   # noqa: E402

# ── 1 ────────────────────────────────────────────────────────────────────────
sec("1. El tipo existe y esta completo")
ok_tipo = P.TIPO_RIPOUT_INST in P.TIPOS
(ok if ok_tipo else fallo)("el tipo esta en P.TIPOS (%s)" % (P.TIPOS,))
# ⚠️ Sin icono, la tarjeta y la ficha caen al generico y el tipo se ve como una
# localizacion interna (`:material/business:`), que es lo contrario de lo que es.
(ok if P.TIPO_RIPOUT_INST in P.TIPO_ICONO else fallo)("...y tiene su icono propio")

# ── 2 ────────────────────────────────────────────────────────────────────────
sec("2. UNA sola definicion de «este tipo genera cronograma»")
# ⚠️ «Ripout» paso a True el 22/09/2026: el catalogo le dio sus propias etapas (ver la
# nota larga del apartado 5). Lo que v470 protege es que haya UNA sola definicion, no
# cual es la respuesta para cada tipo.
_casos = {P.TIPO_INSTALACION: True, P.TIPO_RIPOUT_INST: True,
          "Ripout": True, "Delivery": False, "Other": False, "": False}
_mal = [t for t, e in _casos.items() if P.genera_cronograma(t) is not e]
(ok if not _mal else fallo)("genera_cronograma acierta en los %d tipos" % len(_casos),
                            "fallan: %s" % _mal)
_mal2 = [t for t in _casos if P.con_ripout(t) != (t == P.TIPO_RIPOUT_INST)]
(ok if not _mal2 else fallo)("con_ripout solo es cierto para el tipo combinado", _mal2)

# ⚠️ Y NADIE puede volver a comparar el literal: seria la segunda definicion.
_lits, LIT = [], {"Installation", "Ripout + Installation"}
for _f in sorted(os.listdir("core")):
    if not _f.endswith(".py"):
        continue
    _src = io.open("core/" + _f, encoding="utf-8").read()
    for _n in ast.walk(ast.parse(_src)):
        if isinstance(_n, ast.Compare):
            for _c in _n.comparators:
                if isinstance(_c, ast.Constant) and _c.value in LIT:
                    _lits.append("%s:%d" % (_f, _n.lineno))
(ok if not _lits else fallo)("0 comparaciones contra el literal del tipo", _lits)

# ⚠️ El DEFAULT de `quotes.aceptar_y_crear_proyecto` sigue siendo un literal, y a
# proposito: `projects` se importa DENTRO de esa funcion y reestructurar el grafo de
# imports de un modulo de 600 lineas por un valor por defecto es mas riesgo que valor.
# Lo que se hace en su lugar es afirmar la invariante — si alguien renombra la
# constante, el default apuntaria a un tipo que ya no existe y el proyecto naceria
# con un tipo desconocido, en silencio.
_def = None
for _n in ast.walk(ast.parse(io.open("core/quotes.py", encoding="utf-8").read())):
    if isinstance(_n, ast.FunctionDef) and _n.name == "aceptar_y_crear_proyecto":
        _args = [a.arg for a in _n.args.args]
        _defs = _n.args.defaults
        _i = _args.index("tipo") - (len(_args) - len(_defs))
        _def = _defs[_i].value
(ok if _def == P.TIPO_INSTALACION else fallo)(
    "el default de aceptar_y_crear_proyecto sigue casando con la constante", _def)

# ── 3 ────────────────────────────────────────────────────────────────────────
sec("3. El cronograma: el desmontaje va DELANTE y escala con NS")
# ⚠️ v515 · CADUCADO Y ACTUALIZADO, no relajado (regla v385). Esta seccion afirmaba
# «es UNA actividad llamada FASE_RIPOUT», y `FASE_RIPOUT` se BORRO: el desmontaje pasa a
# ser las etapas de la pista `ripout` del catalogo. Lo que v470 protege sigue vivo —que
# `ripout=True` meta el desmontaje DELANTE, que crezca con las paradas, que alargue la
# obra y que guardar el cronograma editado no lo duplique—, asi que se afirma el
# PRINCIPIO y los numeros se DERIVAN del catalogo (trampa nº16).
from core import stages as _SR                                     # noqa: E402
_NOM_RIP = [e[2] for e in _SR.etapas(_SR.PISTA_RIPOUT)]
_s6 = S.build_schedule(6, date(2026, 1, 5), {}, ripout=True)
_n6 = S.build_schedule(6, date(2026, 1, 5), {}, ripout=False)
_acts = _s6["activities"]
(ok if _NOM_RIP and _acts and _acts[0]["nombre"] in _NOM_RIP else fallo)(
    "la primera actividad es del desmontaje (%s)" % (_NOM_RIP[0] if _NOM_RIP else "?"),
    _acts[0]["nombre"] if _acts else "(sin actividades)")
(ok if len(_acts) == len(_n6["activities"]) + len(_NOM_RIP) else fallo)(
    "aporta exactamente sus %d etapas (%d vs %d)"
    % (len(_NOM_RIP), len(_acts), len(_n6["activities"])))


def _dias_rip(ns):
    """Los dias del DESMONTAJE, no los de su primera fila: el catalogo reparte los
    dias de la pista entre sus etapas, asi que mirar solo la primera puede quedarse
    plana por el suelo de un dia mientras el desmontaje entero si crece."""
    return sum(a["duracion"] for a in S.build_schedule(
        ns, date(2026, 1, 5), {}, ripout=True)["activities"]
        if a["nombre"] in _NOM_RIP)


_d3, _d12 = _dias_rip(3), _dias_rip(12)
(ok if _d12 > _d3 else fallo)(
    "su duracion crece con el NS (3 paradas: %s d · 12 paradas: %s d)" % (_d3, _d12))
# ⚠️ y el proyecto ENTERO dura mas, no solo esa fila
(ok if _s6["total_dias"] > _n6["total_dias"] else fallo)(
    "el proyecto dura mas que una instalacion sola (%s vs %s d)"
    % (_s6["total_dias"], _n6["total_dias"]))
# ⚠️ los pesos se renormalizan a 100: si no, el avance del proyecto no llegaria a 100%
_tot = round(sum(a["peso"] for a in _acts), 1)
(ok if abs(_tot - 100.0) < 0.6 else fallo)("los pesos suman 100 (%.1f)" % _tot)

# ⚠️ `custom_rows` NO puede volver a insertarla: ahi las filas son las que el usuario
# ya edito, y anteponerla otra vez la duplicaria en CADA guardado del cronograma.
_rows = [{"nombre": a["nombre"], "duracion": a["duracion"], "peso": a["peso"]}
         for a in _acts]
_re = S.build_schedule(6, date(2026, 1, 5), {}, custom_rows=_rows, ripout=True)
_cuenta = sum(1 for a in _re["activities"] if a["nombre"] in _NOM_RIP)
(ok if _cuenta == len(_NOM_RIP) else fallo)(
    "guardar el cronograma editado no duplica el desmontaje (%d de %d etapas)"
    % (_cuenta, len(_NOM_RIP)))

# ── 4 ────────────────────────────────────────────────────────────────────────
sec("4. Los TRES caminos deciden igual (el fallo de v454)")
_src_ui = io.open("core/projects_ui.py", encoding="utf-8").read()
_src_q = io.open("core/quotes.py", encoding="utf-8").read()
(ok if "P.genera_cronograma(_tipo)" in _src_ui else fallo)(
    "el alta a mano delega en el helper")
(ok if "P.genera_cronograma(tipo)" in _src_q else fallo)(
    "aceptar una cotizacion delega en el helper")
# ⚠️ v512: antes se exigia `ripout=P.con_ripout(...)`, que es como se le pedia la fase
# de desmontaje al modelo de `PHASES`. Ese modelo ya no se usa en las altas: el
# cronograma sale del catalogo de etapas y el desmontaje son sus 4 etapas propias. Lo
# que v470 protege NO es esa palabra, es que **los dos caminos de alta armen el plan
# igual, y que la vista previa arme lo MISMO que la creacion** — que es por donde se
# perdio v454. Eso se afirma ahora, con el mecanismo de hoy.
(ok if _src_ui.count("_filas_etapas(_tipo, ns, key)") >= 2 else fallo)(
    "el alta arma el plan igual en la creacion Y en su vista previa",
    _src_ui.count("_filas_etapas(_tipo, ns, key)"))
(ok if "filas_de_etapas(" in _src_q else fallo)(
    "aceptar una cotizacion arma el plan con el mismo catalogo")
# ⚠️ v515 · ESCAPE CAZADO POR LA BATERIA: lo de arriba mira el TEXTO, y quitarle
# `custom_rows=_filas` a la llamada dejaba la linea que calcula `_filas` intacta — o sea
# verde con el cronograma saliendo del DEFECTO. Para una instalacion da lo mismo, pero
# una obra combinada naceria con 14 etapas en vez de 18 y sin sus condicionales, en
# silencio. Se afirma sobre la LLAMADA: los dos caminos que CREAN obra le pasan sus
# filas. (El survey no: el suyo es un documento y toma el defecto a proposito, v515.)
_sin_filas = []
for _f, _s in (("core/quotes.py", _src_q), ("core/projects_ui.py", _src_ui)):
    for _n in ast.walk(ast.parse(_s)):
        if (isinstance(_n, ast.Call)
                and getattr(_n.func, "attr", getattr(_n.func, "id", "")) == "build_schedule"
                and not any(k.arg == "custom_rows" for k in _n.keywords)):
            _sin_filas.append("%s:%d" % (_f, _n.lineno))
(ok if not _sin_filas else fallo)(
    "ninguna de las dos altas llama a build_schedule sin sus filas", _sin_filas)
(ok if "ripout=P.con_ripout" not in _src_ui and "ripout=P.con_ripout" not in _src_q
 else fallo)("...y ningun alta quedo colgada del modelo viejo")

# ── 5 ────────────────────────────────────────────────────────────────────────
sec("5. Lo que NO cambia")
# ⚠️ Una instalacion normal tiene que salir EXACTAMENTE igual que sin `ripout`: si se
# moviera, este parametro estaria cambiando el plan de obras que no llevan desmontaje.
# ⚠️ v515: se comparaba contra `PHASES`, borrada. El patron se conserva —la lista
# COMPLETA, no su longitud— pero contra el catalogo, que es de donde salen hoy.
_ins = S.build_schedule(6, date(2026, 1, 5), {})
(ok if [a["nombre"] for a in _ins["activities"]] ==
 [e[2] for e in _SR.etapas(_SR.PISTA_INSTALL)] else fallo)(
    "una instalacion normal son EXACTAMENTE las etapas de instalacion del catalogo")
(ok if _ins["total_dias"] == _n6["total_dias"] else fallo)(
    "...y su duracion (ripout=False es el defecto)")
# ⚠️ DECISION CAMBIADA, y conviene que se lea: en v470 el usuario decidio que «Ripout»
# a secas NO tuviera cronograma. El motivo era concreto — no existian actividades de
# desmontaje, asi que lo unico que se le podia dar eran las 11 fases de INSTALACION, y
# eso habria ensuciado avance, SPI y el radar con trabajo que esa obra no hace.
# El 22/09/2026 el usuario decidio lo contrario, y el motivo de antes ya no aplica: el
# catalogo le da sus 4 etapas y ~20 actividades PROPIAS. No es la misma pregunta
# contestada al reves; es otra pregunta.
_ripout_solo = P.genera_cronograma("Ripout")
(ok if _ripout_solo is True else fallo)(
    "el «Ripout» a secas YA tiene cronograma, y es el suyo (v512)")
from core import stages as _S                                     # noqa: E402

(ok if [e[2] for e in _S.etapas(_S.PISTA_RIPOUT)] ==
 [a["nombre"] for a in S.build_schedule(
     6, date(2026, 1, 5), {},
     custom_rows=S.filas_de_etapas("Ripout", 6, (_S.EXCLUYENTES["demolicion"]["opciones"][0],)),
 )["activities"]] else fallo)(
    "...con SUS etapas de desmontaje, no con las de instalacion")

# ── 6 ────────────────────────────────────────────────────────────────────────
sec("6. Lo que se le DICE al usuario")
# ⚠️ Los dos `help` decian «Only Installation…» y al anadir el tipo pasaron a ser
# FALSOS. Un texto que miente sobre el codigo es la familia del comentario de
# `use_container_width` (v405) y del de `inventory_ui` (v469).
(ok if "Only «Installation»" not in _src_ui else fallo)(
    "ningun texto sigue diciendo «Only Installation»")

# ⚠️ Cambiar el tipo NO regenera el cronograma (regenerarlo borraria el avance ya
# reportado, v135). Eso es correcto, pero hasta v470 pasaba en SILENCIO: la obra
# quedaba marcada como ripout y su plan sin el desmontaje. El aviso va por CONDICION
# —un evento se perderia en el primer rerun (v375/v383)— y DONDE se arregla (v395).
# ⚠️ v515: el aviso dice «stages», no «activity»: el desmontaje dejo de ser UNA
# actividad. El literal se declara UNA vez para que las dos afirmaciones de abajo no
# puedan quedarse desparejadas (una verde y la otra vigilando un texto que ya no esta).
_TXT_AV = "has no strip-out stages"
_av = _TXT_AV in _src_ui
(ok if _av else fallo)("se avisa si el tipo pide desmontaje y el plan no lo tiene")
_bajo_cond = False
for _n in ast.walk(ast.parse(_src_ui)):
    if isinstance(_n, ast.If):
        _seg = ast.get_source_segment(_src_ui, _n) or ""
        if _TXT_AV in _seg and "con_ripout" in _seg:
            _bajo_cond = True
(ok if _bajo_cond else fallo)("...y cuelga de `con_ripout`, no de un evento")

# ⚠️ Si un marcador no casa con su kwarg, el `{x}` se pinta LITERAL y no salta nada
# (v453). Se lee la llamada DEL CODIGO, no una copia: mi primera version reproducia la
# cadena aqui y por eso una rotura real SE ESCAPO — es el fallo de v412, un chequeo que
# reproduce lo que audita en vez de leerlo pasa con el codigo roto.
# Y va sobre TODO el repo, no solo sobre el aviso nuevo: la regla es general.
import re as _re                                                 # noqa: E402
_desc = []
for _f in sorted(os.listdir("core")):
    if not _f.endswith(".py"):
        continue
    _s = io.open("core/" + _f, encoding="utf-8").read()
    for _n in ast.walk(ast.parse(_s)):
        if not (isinstance(_n, ast.Call) and _n.keywords):
            continue
        _fn = getattr(_n.func, "id", "") or getattr(_n.func, "attr", "")
        if _fn not in ("t", "d", "_d", "_t") or not _n.args:
            continue
        _a0 = _n.args[0]
        if not (isinstance(_a0, ast.Constant) and isinstance(_a0.value, str)):
            continue
        _marc = set(_re.findall(r"\{(\w+)\}", _a0.value))
        _kw = {k.arg for k in _n.keywords if k.arg}
        _sin = _marc - _kw
        if _sin:
            _desc.append("%s:%d %s" % (_f, _n.lineno, sorted(_sin)))
(ok if not _desc else fallo)(
    "0 marcadores sin su kwarg en las llamadas a t()/d() del repo", _desc[:5])

print("")
if fallos:
    print("HAY FALLOS: %d de %d" % (len(fallos), len(fallos) + n_ok))
    sys.exit(1)
print("TODO OK - %d comprobaciones" % n_ok)
