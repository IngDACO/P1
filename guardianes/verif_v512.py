# -*- coding: utf-8 -*-
"""v512 · EL CATÁLOGO DE ETAPAS Y ACTIVIDADES.

Lo que protege:
  (a) ⚠️ la aritmética: toda pista suma 100, toda etapa suma 100 dentro de sí. El
      documento de origen llegó con la Stage 2 sumando **106%** y su encabezado
      contradiciendo la tabla de pesos — y no era la primera vez (los sub-grupos de la
      Stage 14 habían sumado 104). Un 6% de más es avance inflado, y el avance se cobra
      (v507/v510): esto tiene que ser un guardián, no una revisión a ojo;
  (b) ⚠️ que el plan de UNA obra sume exactamente 100 con las condicionales que lleve.
      Sin renormalizar, una obra sin falso coche daba 97,48% y un desmontaje 78,30%;
  (c) ⚠️ que tracción e hidráulico sean las DOS condicionales: son excluyentes, y si la
      que no aplica se quedara en el denominador el R3 no podría pasar del 85% jamás;
  (d) que el reparto ripout/instalación que declara el usuario **no se mueva** porque
      una obra lleve menos condicionales;
  (e) que ningún nombre se repita dentro de una etapa (había DOS «Speaker»);
  (f) que el módulo siga siendo HOJA: sin eso no se puede ejercitar nada;
  (g) que la basura no lance — un tipo desconocido, un pct absurdo, una etapa que no
      existe.
Todo EJECUTANDO: importar no ejecuta (v378) y compilar no verifica nada (v439).
"""
import ast
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

fallos, n_ok = [], 0


def ok(q):
    global n_ok
    n_ok += 1
    print(f"  ok   {q}")


def fallo(q, d=""):
    fallos.append(q)
    print(f"  *** FALLO  {q}" + (f"  -> {d}" if d else ""))


def ck(q, real, esp):
    ok(q) if real == esp else fallo(q, f"{real!r} != {esp!r}")


def cerca(q, real, esp, tol=0.01):
    ok(q) if abs(float(real) - float(esp)) <= tol else fallo(q, f"{real!r} != {esp!r}")


def _fuente(f):
    return io.open(os.path.join(RAIZ, f), encoding="utf-8").read()


from core import stages as S                                      # noqa: E402

TRAC = "Rip out mechanical components - traction"
HID = "Rip out mechanical components - hydraulic"


# ═════ 1 · la aritmetica, recalculada aqui ═══════════════════════════════════
# ⚠️ NO basta con llamar a `validar()` y exigir que devuelva vacio: si `validar()`
# estuviera roto, el chequeo pasaria en verde sin comprobar nada (trampa nº1). Las
# sumas se rehacen aqui, a mano, y ADEMAS se exige que `validar()` coincida.
print("\n[1] las sumas")
for _pista in S.PISTAS:
    _s = sum(e[3] for e in S.ETAPAS if e[0] == _pista)
    cerca("las etapas de %s suman 100" % _pista, _s, 100.0)

_malas = []
for (_p, _n), _acts in S.ACTIVIDADES.items():
    _s = sum(a[1] for a in _acts)
    if abs(_s - 100.0) > 0.05:
        _malas.append("%s/%s=%.2f" % (_p, _n, _s))
ck("toda etapa suma 100 en sus actividades", _malas, [])
ck("...y validar() dice lo mismo", S.validar(), [])

# La Stage 2 en concreto: es la que venia mal.
_s2 = next(e for e in S.ETAPAS if e[0] == S.PISTA_INSTALL and e[1] == 2)
ck("⚠️ Prepping pesa 3, no el 4 del encabezado del documento", _s2[3], 3)
cerca("⚠️ y sus actividades suman 100, no 106",
      sum(a[1] for a in S.actividades(S.PISTA_INSTALL, 2)), 100.0)
ck("...sin perder ninguna de las 14", len(S.actividades(S.PISTA_INSTALL, 2)), 14)

# ⚠️ Y que `validar()` SEPA VER un catalogo malo. Un validador roto devuelve lista
# vacia, que es indistinguible de «todo cuadra»: sin esto, su verde no informa de nada
# (trampa nº12 — una sonda no vale hasta probarla contra el caso conocido-malo).
print("\n[1b] el validador se valida")
_orig = dict(S.ACTIVIDADES)
try:
    S.ACTIVIDADES[(S.PISTA_INSTALL, 2)] = [("A", 60, False), ("B", 46, False)]
    ck("ve una etapa que suma 106", any("add up to 106" in x for x in S.validar()), True)
    S.ACTIVIDADES[(S.PISTA_INSTALL, 2)] = [("A", 50, False), ("A", 50, False)]
    ck("ve un nombre repetido", any("duplicate names" in x for x in S.validar()), True)
    S.ACTIVIDADES[(S.PISTA_INSTALL, 2)] = [("A", 100, False), ("B", 0, False)]
    ck("ve una actividad con peso 0", any("weight <= 0" in x for x in S.validar()), True)
    S.ACTIVIDADES.pop((S.PISTA_INSTALL, 2))
    ck("ve una etapa sin actividades", any("no activities" in x for x in S.validar()), True)
    S.ACTIVIDADES[("pista_inventada", 9)] = [("A", 100, False)]
    ck("ve actividades de una etapa inexistente",
       any("do not exist" in x for x in S.validar()), True)
finally:
    S.ACTIVIDADES.clear()
    S.ACTIVIDADES.update(_orig)
ck("⚠️ y el catalogo quedo como estaba", S.validar(), [])


# ═════ 2 · nombres unicos dentro de cada etapa ═══════════════════════════════
print("\n[2] nombres")
# ⚠️ El documento trae DOS «Speaker» en la Stage 10 (bajo cabina y techo) y son dos
# altavoces distintos. Con el mismo nombre el mapeo no podria elegir.
_rep = []
for (_p, _n), _acts in S.ACTIVIDADES.items():
    _nm = [a[0] for a in _acts]
    _rep += ["%s/%s:%s" % (_p, _n, x) for x in sorted(set(_nm)) if _nm.count(x) > 1]
ck("ningun nombre se repite dentro de su etapa", _rep, [])
ck("los dos altavoces se distinguen",
   sorted(a[0] for a in S.actividades(S.PISTA_INSTALL, 10) if "Speaker" in a[0]),
   ["Speaker (top of cabin)", "Speaker (under cabin)"])


# ═════ 3 · ⚠️ el plan de una obra suma 100 ═══════════════════════════════════
print("\n[3] el plan de una obra")
for _t, _c, _pc in (("Installation", (), None),
                    ("Installation", ("Install mirror",), None),
                    ("Ripout", (TRAC,), None),
                    ("Ripout", (HID,), None),
                    ("Ripout + Installation", (TRAC,), None),
                    ("Ripout + Installation", (HID,), 30)):
    _p = S.plan_de(_t, _c, _pc)
    _tot = sum(a["peso_en_obra"] for e in _p for a in e["actividades"])
    cerca("%s (pct=%s) suma 100" % (_t, _pc), _tot, 100.0)
    _te = sum(e["peso"] for e in _p)
    cerca("...y sus etapas tambien", _te, 100.0)

# ⚠️ La propiedad que evita el 85% eterno.
ck("tracción es condicional", any(a[0] == TRAC and a[2]
                                  for a in S.actividades(S.PISTA_RIPOUT, 3)), True)
ck("hidráulico tambien (son excluyentes)",
   any(a[0] == HID and a[2] for a in S.actividades(S.PISTA_RIPOUT, 3)), True)
_solo_trac = S.plan_de("Ripout", (TRAC,))
_nombres = [a["nombre"] for e in _solo_trac for a in e["actividades"]]
ck("⚠️ una obra de traccion NO lleva la actividad hidraulica", HID in _nombres, False)
ck("...pero si la de traccion", TRAC in _nombres, True)


# ═════ 4 · el reparto declarado no se mueve ══════════════════════════════════
print("\n[4] el reparto entre pistas")


def _rip(t, c, pc):
    return sum(e["peso"] for e in S.plan_de(t, c, pc) if e["pista"] == S.PISTA_RIPOUT)


cerca("con pct=30, el desmontaje vale 30", _rip("Ripout + Installation", (TRAC,), 30), 30.0)
# ⚠️ Esto es lo que se rompio en la primera version: renormalizando sobre el TOTAL, un
# desmontaje con menos condicionales encogia solo y 30 salia 28,08.
cerca("...y sigue valiendo 30 con la variante hidraulica",
      _rip("Ripout + Installation", (HID,), 30), 30.0)
cerca("...y con TODOS los condicionales de desmontaje",
      _rip("Ripout + Installation", (TRAC, HID, "Build working deck(s)",
                                     "Retain/preserve components for reuse"), 30), 30.0)
cerca("sin pct, se usa el arranque de 14", _rip("Ripout + Installation", (TRAC,), None),
      S.PCT_RIPOUT_DEFECTO)
ck("una obra de una sola pista no reparte nada",
   _rip("Installation", (), 30), 0.0)


# ═════ 5 · los dos pesos se llaman distinto a proposito ══════════════════════
print("\n[5] peso de catalogo vs peso en obra")
# ⚠️ Son numeros legitimamente distintos: el de catalogo ignora que esta obra no lleve
# ciertos condicionales. Llamarlos igual es como se acaba enseñando un avance y
# reclamando otro (v361), asi que el chequeo exige que DIFIERAN donde deben diferir.
_cat = S.peso_catalogo("Installation", S.PISTA_INSTALL, 4, "Install cabin sill")
_plan = next(a["peso_en_obra"] for e in S.plan_de("Installation", ())
             for a in e["actividades"] if a["nombre"] == "Install cabin sill")
ck("el de catalogo no renormaliza", round(_cat, 4), round(11 * 4 / 100.0, 4))
ck("⚠️ y el de la obra es MAYOR (absorbe lo que dejan los condicionales)",
   _plan > _cat, True)


# ═════ 6 · basura ════════════════════════════════════════════════════════════
print("\n[6] entradas raras")
for _t in ("", None, "Delivery", "Other", "cualquier cosa"):
    if S.plan_de(_t, ()) != []:
        fallo("un tipo sin pistas deberia dar plan vacio", _t)
        break
else:
    ok("un tipo sin etapas da plan vacio, no una excepcion")
ck("una etapa que no existe da lista vacia", S.actividades("install", 99), [])
ck("...y peso 0, no un error", S.peso_etapa("Installation", "install", 99), 0.0)
ck("una actividad que no existe pesa 0",
   S.peso_catalogo("Installation", S.PISTA_INSTALL, 4, "no existe"), 0.0)
for _pc in (-50, 0, 100, 500, None):
    _p = S.plan_de("Ripout + Installation", (TRAC,), _pc)
    _tot = sum(a["peso_en_obra"] for e in _p for a in e["actividades"])
    if abs(_tot - 100.0) > 0.01:
        fallo("pct=%r deberia seguir sumando 100" % _pc, _tot)
        break
else:
    ok("ningun pct absurdo rompe la suma")

# ⚠️ Que la suma siga dando 100 NO prueba que el pct se recorte: con pct=500 el reparto
# queda 500 / −400 y **sigue sumando 100**. La comprobacion de arriba pasaba por su
# propia construccion, y la rotura correspondiente se escapaba de la bateria. El daño
# real de no recortar son pesos NEGATIVOS: una actividad con peso negativo haria que
# terminarla RESTARA avance, y el avance se cobra.
_negativos = []
for _pc in (-50, 0, 100, 500, 1e9, None):
    for _e in S.plan_de("Ripout + Installation", (TRAC,), _pc):
        if _e["peso"] < 0:
            _negativos.append("etapa %s/%s con pct=%r" % (_e["pista"], _e["numero"], _pc))
        _negativos += ["%s con pct=%r" % (a["nombre"], _pc)
                       for a in _e["actividades"] if a["peso_en_obra"] < 0]
ck("⚠️ ningun peso sale NEGATIVO con ningun pct", _negativos[:3], [])


# ═════ 7 · sigue siendo modulo HOJA ══════════════════════════════════════════
print("\n[7] sin ciclos")
_src = io.open(os.path.join(RAIZ, "core/stages.py"), encoding="utf-8").read()
_imp = [ast.unparse(n) for n in ast.parse(_src).body
        if isinstance(n, (ast.Import, ast.ImportFrom))]
ck("no importa nada de core", [i for i in _imp if "core" in i], [])
ck("...ni streamlit ni gspread",
   [i for i in _imp if "streamlit" in i or "gspread" in i], [])
ck("el catalogo trae las 18 etapas", len(S.ETAPAS), 18)
ck("...y 173 actividades", sum(len(v) for v in S.ACTIVIDADES.values()), 173)
ck("el juego de pesos esta versionado", bool(S.VERSION), True)

# ═════ 8 · el cronograma sale del catalogo ═══════════════════════════════════
print("\n[8] el cronograma")
from datetime import date                                         # noqa: E402

from core import schedule as SC                                   # noqa: E402

ck("una instalacion da 14 etapas", len(SC.filas_de_etapas("Installation", 8)), 14)
ck("un desmontaje da 4", len(SC.filas_de_etapas("Ripout", 8, (TRAC,))), 4)
ck("la combinada da 18", len(SC.filas_de_etapas("Ripout + Installation", 8, (TRAC,))), 18)
ck("un tipo sin etapas da lista vacia", SC.filas_de_etapas("Delivery", 8), [])

# ⚠️ La duracion total es EXACTAMENTE la formula de siempre (base + por_parada × NS).
# El modelo viejo no lo cumplia: `PHASES` redondeaba cada fase por su cuenta y su total
# se desviaba un dia en NS impares (medido: 7, 9, 11, 13, 27, 29, 31, 33). El nuevo
# reparte el resto, asi que no se desvia nunca — y por eso, donde las dos fechas de
# entrega difieren, la que estaba mal era la vieja.
_mal, _ceros = [], []
for _ns in range(1, 41):
    _obj = {"Installation": 17 + 2 * _ns,
            "Ripout": round(3 + 0.5 * _ns),
            # ⚠️ La combinada tiene que dar la suma de las dos. Sin este caso, repartir
            # los dias sobre el TOTAL en vez de por pista se escapaba de la bateria: en
            # una obra de una sola pista el divisor es 100 igualmente, asi que la rotura
            # era invisible salvo en la combinada.
            "Ripout + Installation": (17 + 2 * _ns) + round(3 + 0.5 * _ns)}
    for _t, _esperado in _obj.items():
        _f = SC.filas_de_etapas(_t, _ns, (TRAC,))
        _suma = sum(f["duracion"] for f in _f)
        if abs(_suma - _esperado) > 0.001:
            _mal.append((_t, _ns, _suma, _esperado))
        # ⚠️ Y el suelo de un dia se mira en TODO el rango, no solo en NS=8: ahi el
        # reparto del resto devuelve el dia que el truncado quito, asi que quitar el
        # suelo no se notaba y la rotura pasaba por delante.
        _ceros += [(_t, _ns, f["nombre"]) for f in _f if f["duracion"] < 1]
ck("⚠️ la duracion total cuadra con la formula en NS 1..40", _mal[:3], [])
ck("⚠️ ninguna etapa dura menos de un dia, en ningun NS", _ceros[:3], [])

_f8 = SC.filas_de_etapas("Ripout + Installation", 8, (TRAC,))
cerca("los pesos siguen sumando 100", sum(f["peso"] for f in _f8), 100.0)
# ⚠️ Y sobre todo: los pesos QUE SE GUARDAN. Los de arriba salen de `filas_de_etapas` y
# son exactos; `build_schedule` los renormaliza y redondea a un decimal, y ahí catorce
# actividades sumaban **99,8** en la hoja. Comprobar solo la capa de arriba dejaba el
# fallo justo en la frontera entre las dos — lo encontró el ejercicio contra la hoja
# real, no este guardián. Se barren los tres tipos y varios NS porque el desvío depende
# de cuántas actividades haya y de cómo caigan los decimales.
_desv = []
for _t, _c in (("Installation", ()), ("Ripout + Installation", (TRAC,)),
               ("Ripout", (TRAC,))):
    for _ns in (1, 4, 8, 13, 20, 33):
        _s = SC.build_schedule(_ns, date(2026, 10, 1), {},
                               custom_rows=SC.filas_de_etapas(_t, _ns, _c))
        _tot = round(sum(a["peso"] for a in _s["activities"]), 1)
        if abs(_tot - 100.0) > 0.001:
            _desv.append((_t, _ns, _tot))
ck("⚠️ los pesos GUARDADOS suman 100 exacto", _desv[:3], [])
# El modelo viejo comparte la misma normalizacion, asi que tambien tiene que cuadrar.
_vd = [(_ns, round(sum(a["peso"] for a in SC.build_schedule(
    _ns, date(2026, 10, 1), {})["activities"]), 1)) for _ns in (6, 8, 20)]
ck("...tambien por el camino del survey", [x for x in _vd if abs(x[1] - 100.0) > 0.001], [])
ck("el orden va de 1 a N sin huecos",
   [f["orden"] for f in _f8], list(range(1, len(_f8) + 1)))
# ⚠️ Predecesora vacia = «detras de la anterior» (v499). Poner algo aqui cambiaria la
# red de un cronograma recien creado sin que nadie lo haya pedido.
ck("las predecesoras nacen vacias", {f["pred"] for f in _f8}, {""})

_s = SC.build_schedule(8, date(2026, 10, 1), {}, custom_rows=_f8)
ck("build_schedule las acepta", len(_s["activities"]), 18)
ck("...y les pone fecha de fin", bool(_s.get("fecha_fin")), True)
ck("el desmontaje va PRIMERO", _s["activities"][0]["nombre"], "Set Up (rip-out)")
for _ns in ("", None, 0, -5, "ocho"):
    try:
        SC.filas_de_etapas("Installation", _ns)
    except Exception as e:
        fallo("ns=%r no deberia lanzar" % _ns, repr(e))
        break
else:
    ok("un NS basura no lanza")

# ═════ 9 · el alta de obra usa el catalogo ═══════════════════════════════════
print("\n[9] el alta")
import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Bobo", "nombre": "Bobo",
                            "rol": "administrator", "grupo": "cliente1"}
from core import projects as P                                    # noqa: E402

ck("«StagePlanJSON» es la ULTIMA columna de Proyectos (v363)",
   P.PROJECTS_HEADERS[-1], "StagePlanJSON")
_tp = ast.parse(_fuente("core/projects.py"))
_cp = next((n for n in ast.walk(_tp) if isinstance(n, ast.FunctionDef)
            and n.name == "create_project"), None)
assert _cp is not None, "no existe create_project"
ck("...y create_project la acepta", "stage_plan" in [a.arg for a in _cp.args.args], True)
# ⚠️ El valor tiene que ir en la MISMA fila posicional: añadir la columna sin la linea
# es lo que dejo `create_project` MUERTO durante tres versiones (v363, v360).
_fila = next((n for n in ast.walk(_cp) if isinstance(n, ast.Assign)
              and getattr(n.targets[0], "id", "") == "row"), None)
assert _fila is not None, "no se encontro la fila posicional de create_project"
ck("⚠️ la fila posicional cuadra con la cabecera",
   len(_fila.value.elts), len(P.PROJECTS_HEADERS))

# ⚠️ Los TRES tipos con etapas generan cronograma. «Ripout» quedaba fuera cuando no
# tenia actividades propias; dejarlo fuera ahora lo condenaria a la unica actividad
# «Execution» y a un 0% eterno (el fallo de v454, al reves).
for _t in ("Installation", "Ripout", "Ripout + Installation"):
    ck("«%s» genera cronograma" % _t, P.genera_cronograma(_t), True)
for _t in ("Delivery", "Other", ""):
    ck("«%s» NO genera cronograma" % (_t or "vacio"), P.genera_cronograma(_t), False)

_pj = P.plan_nuevo("Ripout + Installation", (TRAC,), 30)
_leido = P.plan_etapas({"StagePlanJSON": _pj})
ck("el plan sellado se relee", _leido.get("pct_ripout"), 30.0)
ck("...con su version de pesos", _leido.get("version"), S.VERSION)
ck("...y sus condicionales", _leido.get("condicionales"), [TRAC])
# ⚠️ Una obra anterior a v512 no tiene plan, y eso NO es un error: toda la cartera
# existente tiene que seguir funcionando igual el dia del despliegue.
ck("una obra sin plan da {}, no un fallo", P.plan_etapas({}), {})
ck("...y un plan ilegible tambien", P.plan_etapas({"StagePlanJSON": "{roto"}), {})
ck("un plan que no es un dict no cuela",
   P.plan_etapas({"StagePlanJSON": "[1,2,3]"}), {})

# Los dos caminos de alta tienen que pasar por el catalogo, no por PHASES.
_tq = ast.parse(_fuente("core/quotes.py"))
_ac = next((n for n in ast.walk(_tq) if isinstance(n, ast.FunctionDef)
            and n.name == "aceptar_y_crear_proyecto"), None)
assert _ac is not None, "no existe aceptar_y_crear_proyecto"
_sac = ast.unparse(_ac)
ck("aceptar cotizacion arma el plan desde las etapas",
   "filas_de_etapas" in _sac, True)
ck("...y sella el plan en la obra", "stage_plan=plan_json" in _sac, True)
ck("...y acepta las condicionales",
   "condicionales" in [a.arg for a in _ac.args.args], True)
_ui = _fuente("core/projects_ui.py")
# ⚠️ Por AST, NO por subcadena: `"_pregunta_etapas(" in _ui` es cierto por culpa de la
# propia **definición** de la función, así que el chequeo pasaba aunque nadie la
# llamara — y la rotura correspondiente se escapaba de la batería. Es la trampa nº2
# (grep no es uso) en su forma más tonta: el texto que busco lo escribí yo al definirla.
_tui = ast.parse(_ui)
_llamadas_ui = {getattr(n.func, "id", "") for n in ast.walk(_tui)
                if isinstance(n, ast.Call)}
ck("el alta a mano LLAMA a _pregunta_etapas", "_pregunta_etapas" in _llamadas_ui, True)
ck("...y a _filas_etapas", "_filas_etapas" in _llamadas_ui, True)
# Y que el resultado se USE para frenar el alta, no solo se calcule.
ck("...y lo pendiente frena la creacion",
   "if _pendientes:" in _ui, True)
ck("...y sella el plan", "stage_plan=(P.plan_nuevo(" in _ui, True)
# ⚠️ Que no quede ningun camino de ALTA llamando al modelo viejo. `ripout=` era como se
# le pedia la fase de desmontaje a `PHASES`: si sobrevive en un alta, esa obra nace con
# el cronograma anterior y nadie se entera (es el fallo de v454, tres sitios y uno mal).
ck("⚠️ ningun alta pide ya la fase vieja de ripout",
   [l.strip()[:60] for l in _ui.splitlines() if "ripout=P.con_ripout" in l], [])
ck("...tampoco al aceptar una cotizacion", "ripout=P.con_ripout" in _sac, False)

print("\n" + "=" * 70)
print(f"{n_ok + len(fallos)} comprobaciones — " + ("TODO OK" if not fallos else "HAY FALLOS"))
sys.exit(1 if fallos else 0)
