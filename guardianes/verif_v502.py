# -*- coding: utf-8 -*-
"""v502 · el RESPONSABLE de cada actividad: que el retraso tenga dueño.

Lo que protege:
  (a) la fila posicional contra su cabecera, con «Owner» AL FINAL (v363);
  (b) ⚠️ que un guardado PARCIAL no borre el responsable de las filas que no viajan
      — es el fallo que v499 tuvo con las predecesoras, y la tabla del campo guarda
      justo así (v162);
  (c) que el responsable LLEGUE a la pantalla que muestra el retraso, viajando como
      lista paralela a `avances` (el motor de plan no sabe de personas);
  (d) los tres puntos del cuadro sincronizados: fila, `column_config` y relectura
      — leer por la etiqueta en vez de por la clave es el KeyError de v471, que
      tumbaba el guardado entero;
  (e) que se GUARDE el login y se MUESTRE el nombre (el nombre se repite, v306/v413);
  (f) que el campo no edite responsables.
Todo EJECUTANDO donde se puede: importar no ejecuta (v378) y compilar no verifica nada.
"""
import ast
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Bobo", "nombre": "Bobo",
                            "rol": "administrator", "grupo": "cliente1"}

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


def _fuente(f):
    return io.open(os.path.join(RAIZ, f), encoding="utf-8").read()


from core import projects as P                                    # noqa: E402
from core import auth                                             # noqa: E402
from core import tabla                                            # noqa: E402

_TR_P = ast.parse(_fuente("core/projects.py"))
_SRC_UI = _fuente("core/projects_ui.py")
_TR_UI = ast.parse(_SRC_UI)


def _fn(tree, nombre):
    return next((n for n in ast.walk(tree)
                 if isinstance(n, ast.FunctionDef) and n.name == nombre), None)


# ═════ 1 · la hoja: la columna nueva no descuadra la fila (v363) ═════════════
print("\n[1] «Owner» al final, y las filas posicionales con ella dentro")
ck("«Owner» es la ULTIMA columna de Actividades", P.ACTIVITIES_HEADERS[-1], "Owner")
ck("...y su indice sale de la cabecera, no de un numero a mano",
   P._ACOL["Owner"], len(P.ACTIVITIES_HEADERS))

# ⚠️ v363: la columna nueva y el valor en la fila van en el MISMO cambio. Olvidarlo
# dejo `create_project` muerto tres versiones sin que nadie se enterara.
_cp = _fn(_TR_P, "create_project")
assert _cp is not None, "no se encontro create_project (el chequeo no probaria nada)"
_filas = [len(n.elts) for n in ast.walk(_cp)
          if isinstance(n, ast.List) and len(n.elts) == len(P.ACTIVITIES_HEADERS)]
ck("la fila de actividad de create_project tiene tantos valores como columnas",
   bool(_filas), True)

_aa = _fn(_TR_P, "add_activity")
assert _aa is not None, "no se encontro add_activity"
_ap = next((n for n in ast.walk(_aa) if isinstance(n, ast.Call)
            and getattr(n.func, "attr", "") == "append_row"), None)
assert _ap is not None, "add_activity ya no usa append_row (revisar el chequeo)"
ck("la fila de add_activity tambien",
   len(_ap.args[0].elts), len(P.ACTIVITIES_HEADERS))


# ═════ 2 · un guardado PARCIAL no borra responsables ═════════════════════════
print("\n[2] lo que el edit no trae, no se toca")


class _WS:
    def __init__(self, recs):
        self._recs, self.batch = recs, []

    def get_all_records(self, **kw):
        return [dict(r) for r in self._recs]

    def batch_update(self, batch, **kw):
        self.batch = batch


_RECS = [{"ProjectID": "PRJ-1", "Order": "1", "Name": "A1", "DurationDays": "4",
          "Weight": "10", "Progress": "0", "Predecessors": "", "Owner": "ana"},
         {"ProjectID": "PRJ-1", "Order": "2", "Name": "A2", "DurationDays": "4",
          "Weight": "10", "Progress": "0", "Predecessors": "1", "Owner": "beto"}]
_COL_OWNER = P._col_letter(P._ACOL["Owner"])


def _guardar(edits):
    ws = _WS(_RECS)
    _o = (P._activities_ws, P._invalidate, P._recompute_project_avance)
    try:
        P._activities_ws = lambda: (ws, None)
        P._invalidate = lambda: None
        P._recompute_project_avance = lambda pid: None
        P.save_activities("PRJ-1", edits)
    finally:
        (P._activities_ws, P._invalidate, P._recompute_project_avance) = _o
    return [b for b in ws.batch if b["range"].startswith(_COL_OWNER)]


# ⚠️ Control PRIMERO: si el caso positivo no escribe, el negativo pasa por el motivo
# equivocado y el «no borra» no significa nada (v459: el verde de base antes que nada).
_pos = _guardar([{"orden0": "1", "Name": "A1", "Owner": "carla"}])
ck("un edit CON responsable lo escribe en su columna",
   [(b["range"], b["values"]) for b in _pos],
   [(f"{_COL_OWNER}2", [["carla"]])])

_neg = _guardar([{"orden0": "1", "Name": "A1 renombrada"}])
ck("⚠️ un edit SIN responsable no toca esa columna (guardado parcial)", _neg, [])

_vac = _guardar([{"orden0": "1", "Name": "A1", "Owner": ""}])
ck("...pero vaciarlo A PROPOSITO si se escribe",
   [b["values"] for b in _vac], [[[""]]])


# ═════ 3 · el responsable llega a la pantalla del retraso ════════════════════
print("\n[3] de la hoja al diagnostico, como lista paralela")
_ACTS = [{"Name": "A1", "DurationDays": "4", "Weight": "10", "Order": "1",
          "Predecessors": "-", "Progress": "0", "Owner": "ana"},
         {"Name": "A2", "DurationDays": "4", "Weight": "10", "Order": "2",
          "Predecessors": "1", "Progress": "0", "Owner": ""},
         {"Name": "A3", "DurationDays": "4", "Weight": "10", "Order": "3",
          "Predecessors": "2", "Progress": "0", "Owner": "beto"}]
_o = (P.get_project, P.list_activities)
try:
    P.get_project = lambda pid: {"ProjectID": "PRJ-1", "StartDate": "2026-09-01"}
    P.list_activities = lambda pid: [dict(a) for a in _ACTS]
    _ps = P.project_schedule("PRJ-1")
finally:
    (P.get_project, P.list_activities) = _o

ck("project_schedule devuelve los responsables", _ps.get("owners"), ["ana", "", "beto"])
# ⚠️ `.get(... ) or []` y no `_ps["owners"]`: si la clave desaparece, el guardián tiene
# que DENUNCIARLO, no morir con un KeyError. Un guardián que revienta no prueba nada —
# la batería lo cuenta como «revienta, no cuenta» y la rotura se va de rositas.
ck("...uno por actividad, igual que los avances",
   len(_ps.get("owners") or []), len(_ps.get("avances") or []))

# ⚠️ `_diagnostico` indexa `owners` con el MISMO indice que `avances`. Si un dia el
# cronograma reordenara sus actividades, las dos listas mentirian a la vez — asi que
# lo que se afirma es que el nombre de la actividad y su dueño siguen casando.
_nom = [a["nombre"] for a in _ps["sched"]["activities"]]
ck("el orden del cronograma casa con el de las actividades guardadas",
   _nom, [a["Name"] for a in _ACTS])

_diag = _fn(_TR_UI, "_diagnostico")
assert _diag is not None, "no se encontro _diagnostico"
_sd = ast.unparse(_diag)
ck("_diagnostico lee `owners` de ps", "ps.get('owners')" in _sd, True)
ck("...y lo pasa a cada actividad", _sd.count("'owner': _ow"), 2)

_est = _fn(_TR_UI, "_estado_section")
assert _est is not None, "no se encontro _estado_section"
_se = ast.unparse(_est)
# ⚠️ Se cuentan las LLAMADAS por AST, no subcadenas: con un `in` basta que quede UNA de
# las dos y la otra se podria borrar sin que nadie se entere, y contar el texto cuenta
# ademas el `def _dueno(x):` — un 3 que parece un 2 mal puesto (el fallo de v500: el
# chequeo fallando por su propia construccion). Son DOS porque el dueño se pinta en lo
# que va tarde: la parada (no arranco) y la arrastrada (se paso de su ventana). Si un
# dia se decide mostrarlo en mas sitios, este numero sube A PROPOSITO y con la razon.
_llam = [n for n in ast.walk(_est) if isinstance(n, ast.Call)
         and getattr(n.func, "id", "") == "_dueno"]
ck("la pantalla del retraso pinta el dueño en la parada Y en la arrastrada",
   len(_llam), 2)
# ⚠️ Se traduce por `_etq_us`, la funcion de modulo (L54), no llamando a
# `auth.etiqueta_usuarios` a mano: es la definicion UNICA y desempata homonimos sobre
# TODO el grupo, no sobre la lista visible — si no, la misma persona seria «Mei Chen» en
# una pantalla y «Mei Chen (mchen)» en otra (v413). Aqui decia `etiqueta_usuarios` porque
# yo lo habia reimplementado; al usar el helper, la afirmacion pasa a ser esta.
ck("...traduciendo el login a nombre con la definicion unica", "_etq_us(" in _se, True)


# ═════ 4 · los tres puntos del cuadro, sincronizados (v471) ══════════════════
print("\n[4] fila, column_config y relectura dicen lo mismo")
_det = _fn(_TR_UI, "_detalle_proyecto")
assert _det is not None, "no se encontro _detalle_proyecto"
_sdet = ast.unparse(_det)

# ⚠️ Nada de grep sobre el fichero entero (trampa nº2): se mira el AST de la funcion,
# y ademas se exige que el bloque del editor de actividades exista — si un dia se
# mueve a otra funcion, este chequeo tiene que ponerse ROJO, no pasar en vacio.
ck("el editor de actividades sigue en esta funcion", "acted_" in _sdet, True)

_claves = [n for n in ast.walk(_det) if isinstance(n, ast.Constant)
           and n.value == "Responsable"]
ck("«Responsable» aparece en los TRES puntos (fila, config, relectura)",
   len(_claves) >= 3, True)
ck("la relectura devuelve el campo que la hoja entiende",
   "'Owner': _login_de.get(" in _sdet, True)
ck("...y las opciones salen de la gente asignada a la obra",
   "_asig_now" in _sdet and "_op_lbl" in _sdet, True)

# ⚠️ Un responsable guardado de alguien ya NO asignado tiene que seguir en la lista:
# si no, su fila se pinta vacia y el primer guardado lo borra sin que nadie lo pida.
ck("los dueños ya guardados entran en las opciones aunque no esten asignados",
   "_due0" in _sdet and "+ [o for o in _due0 if o]" in _sdet, True)

ck("la cabecera esta declarada en tabla.CABECERAS (v450)",
   tabla.CABECERAS.get("Responsable"), "Owner")

# ⚠️ El «sin responsable» tiene que tener TEXTO. Con la cadena vacia, un
# `SelectboxColumn` pinta la palabra «None» en cada celda sin dueño — medido en
# produccion interceptando `fillText`, 20 veces en la columna Owner. No se ve en el DOM
# ni compilando: solo leyendo el canvas (v398/nº18). Y la vuelta tiene que dar "" sola,
# porque el mapa inverso se construye de `_lbl_de` y esa clave no esta ahi.
ck("la opcion «sin responsable» lleva texto, no la cadena vacia",
   "_SIN = t(" in _sdet and "_op_lbl = [_SIN]" in _sdet, True)
ck("...y una fila sin dueño usa esa opcion, no «»",
   "_lbl_de.get(str(a.get('Owner', '') or '').strip(), _SIN)" in _sdet, True)


# ═════ 5 · nombre a la vista, LOGIN en la hoja ═══════════════════════════════
print("\n[5] el login es la identidad; el nombre es comodidad")
_us = [{"User": "ana", "Name": "Ana"},
       {"User": "b1", "Name": "Beto"},
       {"User": "b2", "Name": "Beto"}]
_e = auth.etiqueta_usuarios(_us)
ck("un nombre unico se muestra tal cual", _e["ana"], "Ana")
ck("⚠️ un nombre REPETIDO lleva el login detras", (_e["b1"], _e["b2"]),
   ("Beto (b1)", "Beto (b2)"))
# El mapa etiqueta->login que usa la pantalla solo es fiable si no hay dos etiquetas
# iguales: dos filas indistinguibles guardarian el responsable equivocado.
ck("las etiquetas son unicas (el mapa inverso no pierde a nadie)",
   len(set(_e.values())), len(_e))


# ═════ 6 · el campo no edita responsables ════════════════════════════════════
print("\n[6] quien puede tocarlo")
# ⚠️ La tabla editable del campo esta en `_field_activities`, NO en
# `render_field_projects` (que solo la llama). Mirar la de fuera daba un OK en VACIO:
# no habia ninguna tabla ahi que pudiera traer la columna (trampa nº1).
_fc = _fn(_TR_UI, "_field_activities")
assert _fc is not None, "no se encontro _field_activities"
_sfc = ast.unparse(_fc)
ck("el chequeo mira la tabla de verdad (la que guarda el avance)",
   "save_field_progress" in _sfc, True)
ck("⚠️ la tabla del campo no trae la columna Responsable",
   ("Responsable" in _sfc or "'Owner'" in _sfc), False)

# ═════ 7 · RED NUEVA: ligar un nombre que ya es funcion del modulo ═══════════
print("\n[7] nadie sombrea una funcion de modulo que su propia funcion llama")
# ⚠️ Esta red nace de un fallo REAL de v502 que se fue a produccion: puse
# `_etq_us = auth.etiqueta_usuarios(...)` dentro de `_detalle_proyecto`, donde `_etq_us`
# ya era la funcion de modulo (L54) y esa misma funcion la LLAMA mas arriba (L2428).
# Python marca el nombre local en el ambito ENTERO, asi que la llamada anterior reventaba
# con UnboundLocalError. Es la trampa nº29 (los dos fallos de v439) y NO la vio nadie:
# ni `compileall`, ni el import, ni los 135 guardianes — porque nada EJECUTA esa funcion.
# Lo vio la pantalla, en produccion. Esta red lo caza estaticamente.
# ⚠️ Se mira el ORDEN: un `def` anidado antes de su unica llamada es legitimo (pasa en
# `roster_ui._cumplimiento` con `_hm`, y ahi no hay fallo). Lo que revienta es LLAMAR
# antes de LIGAR.
import pathlib                                                    # noqa: E402


def _ligaduras(fn):
    out = {}

    def walk(n, raiz=False):
        for h in ast.iter_child_nodes(n):
            if isinstance(h, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                if not raiz:
                    out.setdefault(getattr(h, "name", ""), []).append(h.lineno)
                continue
            if isinstance(h, ast.Name) and isinstance(h.ctx, ast.Store):
                out.setdefault(h.id, []).append(h.lineno)
            walk(h)
    walk(fn, raiz=True)
    return out


_sombras = []
for _p in sorted(pathlib.Path(os.path.join(RAIZ, "core")).glob("*.py")):
    _t = ast.parse(io.open(_p, encoding="utf-8").read())
    _mods = {n.name for n in _t.body if isinstance(n, ast.FunctionDef)}
    for _f in [n for n in ast.walk(_t) if isinstance(n, ast.FunctionDef)]:
        for _nom, _lin in _ligaduras(_f).items():
            if _nom not in _mods or _nom == _f.name:
                continue
            _ll = [n.lineno for n in ast.walk(_f)
                   if isinstance(n, ast.Call) and getattr(n.func, "id", "") == _nom]
            if _ll and min(_ll) < min(_lin):
                _sombras.append("%s:%s llama %s en L%d y lo liga en L%d"
                                % (_p.name, _f.name, _nom, min(_ll), min(_lin)))
# afirmacion POSITIVA de que la red SABE ver (v459): se valida contra un caso conocido
_CASO = ast.parse("def h():\n    pass\n\ndef f():\n    h()\n    h = 1\n    return h\n")
_mods_c = {n.name for n in _CASO.body if isinstance(n, ast.FunctionDef)}
_fc = [n for n in ast.walk(_CASO) if isinstance(n, ast.FunctionDef) and n.name == "f"][0]
_lig_c = _ligaduras(_fc)
_ll_c = [n.lineno for n in ast.walk(_fc)
         if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "h"]
ck("la red SABE ver el caso conocido-malo (si no, su «0» no vale nada)",
   bool(_ll_c and min(_ll_c) < min(_lig_c["h"])), True)
ck("⚠️ ningun modulo de core sombrea asi", _sombras, [])

print("\n" + "=" * 70)
print(f"{n_ok + len(fallos)} comprobaciones — " + ("TODO OK" if not fallos else "HAY FALLOS"))
sys.exit(1 if fallos else 0)
