# -*- coding: utf-8 -*-
"""v499 · las actividades se encadenan (dependencias con desfase y ruta crítica).

Lo que falla EN SILENCIO y hay que proteger:
  (a) un cronograma SIN dependencias tiene que salir EXACTAMENTE como hasta v498 — si no,
      todas las obras existentes cambian de fechas sin que nadie lo pida;
  (b) reordenar o borrar una actividad deja las referencias apuntando a OTRA: se remapean;
  (c) un ciclo colgaría el cálculo y una referencia rota daría un plan que empieza el día 0:
      los dos se detectan, se avisan y el plan se sigue dibujando;
  (d) la fila de actividades tiene que casar con su cabecera (v363);
  (e) las tablas editables se leen por la clave del CUADRO, no por la etiqueta (v471).
Todo EJECUTANDO.
"""
import ast
import datetime as dt
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
G = "cliente1"
st.session_state["auth"] = {"usuario": "admin", "nombre": "admin",
                            "rol": "administrator", "grupo": G}

fallos, n_ok = [], 0


def ok(que):
    global n_ok
    n_ok += 1
    print(f"  ok   {que}")


def fallo(que, detalle=""):
    fallos.append(que)
    print(f"  *** FALLO  {que}" + (f"  -> {detalle}" if detalle else ""))


def ck(que, real, esperado):
    ok(que) if real == esperado else fallo(que, f"{real!r} != {esperado!r}")


def _fuente(f):
    return io.open(os.path.join(RAIZ, f), encoding="utf-8").read()


from core import plan, projects as P                              # noqa: E402
from core.schedule import build_schedule, schedule_svg            # noqa: E402
from core import schedule as S499                                 # noqa: E402
import importlib.util                                             # noqa: E402
from pathlib import Path as _P499                                 # noqa: E402
AQUI = _P499(__file__).parent

A = lambda o, d, p="": {"orden": o, "duracion": d, "pred": p}     # noqa: E731

# ═════ 1 · el cálculo ════════════════════════════════════════════════════════
print("\n[1] el encadenado: cadena por defecto, paralelo, desfase y solape")
ck("lee «3;5-2»", plan.parse("3;5-2"), [(3, 0), (5, -2)])
ck("...y «4+3»", plan.parse("4+3"), [(4, 3)])
ck("«-» es sin predecesora", plan.parse("-"), [])
ck("lo ilegible se ignora (no revienta)", plan.parse("basura;2"), [(2, 0)])
ck("formatear es el inverso", plan.formatear([(3, 0), (5, -2), (4, 3)]), "3;5-2;4+3")

r = plan.calcular([A(1, 3), A(2, 5), A(3, 2)])
ck("vacío = detrás de la anterior (lo de hasta v498)",
   [(v["inicio"], v["fin"]) for v in r["por_orden"].values()], [(0.0, 3.0), (3.0, 8.0), (8.0, 10.0)])
r = plan.calcular([A(1, 3), A(2, 5, "-"), A(3, 2, "1+2"), A(4, 4, "2;3-1")])
ck("paralelo, espera y solape",
   [(v["inicio"], v["fin"]) for v in r["por_orden"].values()],
   [(0.0, 3.0), (0.0, 5.0), (5.0, 7.0), (6.0, 10.0)])
ck("...y la ruta crítica son las que no tienen holgura",
   [o for o, v in r["por_orden"].items() if v["critica"]], [1, 3, 4])
ck("...con el total del proyecto", r["total_dias"], 10.0)

# (c) ciclo y referencia rota
r = plan.calcular([A(1, 3, "2"), A(2, 5, "1")])
ck("un ciclo se rompe, se avisa y el plan se dibuja igual",
   ([m for m, _i, _o in r["avisos"]], [(v["inicio"], v["fin"]) for v in r["por_orden"].values()]),
   (["ciclo"], [(0.0, 3.0), (3.0, 8.0)]))
r = plan.calcular([A(1, 3), A(2, 5, "99")])
ck("una predecesora que no existe se avisa", [(m, o) for m, _i, o in r["avisos"]], [("falta", 99)])
ck("una actividad detrás de sí misma, también",
   [m for m, _i, _o in plan.calcular([A(1, 3, "1")])["avisos"]], ["ella_misma"])

# (b) remapear
ck("remapear sigue los números nuevos", plan.remapear("3;5-2", {3: 1, 5: 2}), "1;2-2")
ck("...y quita la referencia a la que ya no está", plan.remapear("3;5", {5: 2}), "2")
ck("...y si no queda ninguna, la deja sin predecesora", plan.remapear("3", {}), plan.SIN_PREDECESORA)

# ═════ 2 · el cronograma NO se mueve para lo que ya existe ═══════════════════
print("\n[2] sin dependencias, el cronograma sale como hasta v498")
# ⚠️ Oráculo SACADO DEL MÓDULO DE v498 (`oraculo_v499.py`) y escrito aquí LITERAL:
# compararlo con la salida del código actual no probaría nada (trampa nº1), y sacarlo
# de git dentro del guardián lo dejaría vacío en cuanto se hiciera el commit (v484).
# ⚠️ v515 · CADUCADO Y ACTUALIZADO, y el cambio lo hace MÁS fuerte, no más débil.
# La tabla congelada guardaba (días, nº de actividades) de las 11 fases de `PHASES`, que
# se BORRÓ: comparar contra ella era comparar contra un modelo que ya no existe, y el
# rojo no decía nada de la RED, que es lo único que v499 introdujo.
#
# Lo que v499 protege es «meter predecesoras no mueve un cronograma que ya existía». Eso
# se aísla dándole a las DOS implementaciones —la de v498 y la de hoy— las MISMAS filas,
# y comparando actividad por actividad en vez de dos totales: dos cronogramas distintos
# pueden durar lo mismo. 14 casos × 14-18 actividades, contra 14 pares de números.
#
# ⚠️ El PESO se compara aparte y se espera que DIFIERA: v513 cambió el redondeo a resto
# mayor a propósito, porque los pesos guardados sumaban 99,8. Meterlo en la misma
# afirmación la pondría roja por un cambio querido y acabaría relajándose entera.
_sp499 = importlib.util.spec_from_file_location(
    "old_sched_499", str(AQUI / "sueltos" / "schedule_v498.py"))
_old499 = importlib.util.module_from_spec(_sp499)
_sp499.loader.exec_module(_old499)
_CASOS = [(ns, rip) for ns in (1, 2, 3, 6, 8, 12, 20) for rip in (False, True)]
_mal, _n_act, _dif_peso = [], 0, 0
for _ns, _rip in _CASOS:
    _filas = S499.filas_de_etapas(
        "Ripout + Installation" if _rip else "Installation", _ns, ())
    _o = _old499.build_schedule(_ns, dt.date(2026, 9, 1), {}, custom_rows=_filas)
    _n = build_schedule(_ns, dt.date(2026, 9, 1), {}, custom_rows=_filas)
    if _o["total_dias"] != _n["total_dias"] or len(_o["activities"]) != len(_n["activities"]):
        _mal.append((_ns, _rip, "total"))
        continue
    for _x, _y in zip(_o["activities"], _n["activities"]):
        _n_act += 1
        if (_x["nombre"], _x["inicio"], _x["duracion"]) != \
           (_y["nombre"], _y["inicio"], _y["duracion"]):
            _mal.append((_ns, _rip, _x["nombre"]))
        _dif_peso += (_x["peso"] != _y["peso"])
# ⚠️ Antes de creerse el «0 diferencias» hay que afirmar que se comparó algo (trampa nº1).
ck(f"el oráculo de v498 y el de hoy comparan {len(_CASOS)} cronogramas de verdad",
   len(_CASOS) == 14 and _n_act > 150, True)
ck(f"...y la RED sale igual en las {_n_act} actividades", _mal, [])
ck("...y lo único que se movió son los pesos, que v513 cambió a propósito",
   _dif_peso > 0, True)
s = build_schedule(6, dt.date(2026, 9, 1), {})
ck("...y siguen encadenadas una detrás de otra",
   all(abs(s["activities"][i + 1]["inicio"] - (s["activities"][i]["inicio"] + s["activities"][i]["duracion"])) < 1e-6
       for i in range(len(s["activities"]) - 1)), True)
ck("...con TODAS en la ruta crítica (una cadena no tiene holgura)",
   all(a["critica"] for a in s["activities"]), True)

cr = [{"nombre": "A", "duracion": 3, "peso": 1, "orden": 1, "pred": ""},
      {"nombre": "B", "duracion": 5, "peso": 1, "orden": 2, "pred": "-"},
      {"nombre": "C", "duracion": 2, "peso": 1, "orden": 3, "pred": "1+2"},
      {"nombre": "D", "duracion": 4, "peso": 1, "orden": 4, "pred": "2;3-1"}]
s2 = build_schedule(1, dt.date(2026, 9, 1), {}, custom_rows=cr)
ck("con red: las fechas salen del encadenado",
   [(a["fecha_inicio"].isoformat(), a["critica"]) for a in s2["activities"]],
   [("2026-09-01", True), ("2026-09-01", False), ("2026-09-06", True), ("2026-09-07", True)])
ck("...y el proyecto dura lo que la ruta crítica", s2["total_dias"], 10)
_svg = schedule_svg(s2)
ck("el Gantt marca las críticas", _svg.count('stroke="#c0392b"'), 3)
ck("...y sigue sin <defs>/<marker> (svglib los tira, v39)",
   ("<marker" in _svg or "<defs" in _svg), False)
ck("los avisos del encadenado viajan en el resultado", "avisos_plan" in s2, True)

# ═════ 3 · la hoja: fila y cabecera casan (v363) ═════════════════════════════
print("\n[3] la fila de actividades casa con su cabecera")
# ⚠️ CADUCADO y re-anclado el 20/09/2026 (v502). Decia `ACTIVITIES_HEADERS[-1] ==
# "Predecessors"`, y v502 añadio «Owner» detras —legitimamente, AL FINAL— asi que se puso
# rojo sin que nada estuviera mal: una afirmacion atada a la FORMA caduca en cuanto la
# forma cambia a proposito (trampa nº16). Lo que v499 vino a proteger no es «soy la
# ultima» sino «no me coli EN MEDIO», que es lo que desplaza cada escritura posicional
# (v363). Asi que se afirma el PRINCIPIO: las columnas ANTERIORES a «Predecessors» son
# exactamente las nueve que ya existian. Insertar una en medio la pone roja; añadir otra
# detras, no — que es justo la diferencia que importa.
_PREV_V499 = ["ProjectID", "Order", "Name", "DurationDays", "Weight", "Progress",
              "ActualStartDate", "ActualEndDate", "Note"]
ck("«Predecessors» no se colo en medio: detras de las de siempre",
   P.ACTIVITIES_HEADERS[:P.ACTIVITIES_HEADERS.index("Predecessors")], _PREV_V499)
_tr = ast.parse(_fuente("core/projects.py"))


def _largo_fila(fn_nombre, marca):
    fn = next(n for n in ast.walk(_tr) if isinstance(n, ast.FunctionDef) and n.name == fn_nombre)
    for n in ast.walk(fn):
        if isinstance(n, ast.List) and marca in ast.unparse(n):
            return len(n.elts)
    return -1


ck("la fila de create_project tiene tantos valores como columnas",
   _largo_fila("create_project", "Actividad"), len(P.ACTIVITIES_HEADERS))
ck("...y la de add_activity también",
   _largo_fila("add_activity", "str(orden)"), len(P.ACTIVITIES_HEADERS))

# ═════ 4 · guardar y borrar remapean, EJECUTADO ══════════════════════════════
print("\n[4] reordenar y borrar no dejan referencias apuntando a otra actividad")
CAB = list(P.ACTIVITIES_HEADERS)


class _WS:
    def __init__(self, filas):
        self.filas = [list(CAB)] + [list(f) for f in filas]
        self.escrituras = []

    def get_all_records(self, numericise_ignore=None):
        return [dict(zip(CAB, r)) for r in self.filas[1:]]

    def get_all_values(self):
        return [list(r) for r in self.filas]

    def batch_update(self, rangos, value_input_option=None):
        import re as _re
        self.escrituras.append(rangos)
        for r in rangos:
            m = _re.match(r"([A-Z]+)(\d+)", r["range"])
            col = 0
            for ch in m.group(1):
                col = col * 26 + (ord(ch) - 64)
            self.filas[int(m.group(2)) - 1][col - 1] = r["values"][0][0]


def _fila(orden, nombre, pred=""):
    d = {"ProjectID": "PRJ-1", "Order": str(orden), "Name": nombre, "DurationDays": "3",
         "Weight": "10", "Progress": "0", "Predecessors": pred}
    return [d.get(c, "") for c in CAB]


_o = (P._activities_ws, P._invalidate, P._recompute_project_avance)
try:
    P._invalidate = lambda: None
    P._recompute_project_avance = lambda pid: None
    ws = _WS([_fila(1, "A"), _fila(2, "B", "1"), _fila(3, "C", "2+2")])
    P._activities_ws = lambda: (ws, "")
    # se intercambian la 2 y la 3
    P.save_activities("PRJ-1", [{"orden0": "1", "Order": 1}, {"orden0": "2", "Order": 3},
                                {"orden0": "3", "Order": 2}])
    _preds = {r["Order"]: r["Predecessors"] for r in ws.get_all_records()}
    ck("al reordenar, las referencias siguen apuntando a la MISMA actividad",
       _preds, {"1": "", "3": "1", "2": "3+2"})

    ws2 = _WS([_fila(1, "A"), _fila(2, "B", "1"), _fila(3, "C", "1;2+2")])
    P._activities_ws = lambda: (ws2, "")
    P.limpiar_predecesoras("PRJ-1", 2)
    ck("al borrar una actividad, quien la tenía de predecesora la suelta",
       {r["Order"]: r["Predecessors"] for r in ws2.get_all_records()},
       {"1": "", "2": "1", "3": "1"})

    ws3 = _WS([_fila(1, "A"), _fila(2, "B", "1")])
    P._activities_ws = lambda: (ws3, "")
    P.save_activities("PRJ-1", [{"orden0": "2", "Order": 2, "Predecessors": "1+3"}])
    ck("lo que se escribe en «detrás de» se guarda",
       {r["Order"]: r["Predecessors"] for r in ws3.get_all_records()}, {"1": "", "2": "1+3"})

    # ⚠️ El caso que importa: un guardado PARCIAL (solo la fila tocada). Si el mapa
    # saliera de los `edits`, las que no viajan quedarían fuera y `remapear` tiraría
    # sus referencias — el plan entero reescrito en silencio. Hoy el único llamador
    # manda la tabla completa, así que esto protege al SIGUIENTE.
    ws4 = _WS([_fila(1, "A"), _fila(2, "B", "1"), _fila(3, "C", "1;2+2")])
    P._activities_ws = lambda: (ws4, "")
    P.save_activities("PRJ-1", [{"orden0": "1", "Order": 1, "Name": "A (renombrada)"}])
    ck("guardar UNA fila no borra las predecesoras de las demás",
       {r["Order"]: r["Predecessors"] for r in ws4.get_all_records()},
       {"1": "", "2": "1", "3": "1;2+2"})
finally:
    (P._activities_ws, P._invalidate, P._recompute_project_avance) = _o

# ═════ 5 · las dos tablas editables, leídas por su clave ═════════════════════
print("\n[5] las tablas editables se leen por la clave del cuadro (v471), y hay «detrás de»")
_ui = ast.parse(_fuente("core/projects_ui.py"))


def _lee(fn_nombre):
    fn = next(n for n in ast.walk(_ui) if isinstance(n, ast.FunctionDef) and n.name == fn_nombre)
    return {s.slice.value for s in ast.walk(fn)
            if isinstance(s, ast.Subscript) and isinstance(s.slice, ast.Constant)
            and isinstance(s.slice.value, str) and isinstance(s.value, ast.Name) and s.value.id == "r"}


_act = _lee("_detalle_proyecto")
ck("la tabla de actividades ya NO lee «Weight»/«Order» (era KeyError desde v468)",
   ({"Weight", "Order"} & _act), set())
ck("...lee «Peso»/«Orden»/«Detras»", {"Peso", "Orden", "Detras"} <= _act, True)
_fld = _lee("_field_activities")
ck("el avance del campo ya NO lee «Note» (mismo KeyError)", "Note" in _fld, False)
ck("...lee «Nota»", "Nota" in _fld, True)
_src_ui = _fuente("core/projects_ui.py")
ck("el editor ofrece la columna «After» con su ayuda",
   ('"Detras": st.column_config.TextColumn(' in _src_ui and "After" in _src_ui), True)
ck("y la pantalla dice cuando el encadenado no cuadra", "avisos_plan" in _src_ui, True)

# ═════ 6 · la pantalla llega a los avisos por la ruta REAL ═══════════════════
print("\n[6] el aviso del encadenado llega a la pantalla")
# ⚠️ La UI los saca con `project_schedule(pid)["sched"]["avisos_plan"]`. Si la FORMA del
# dato fuera otra, los avisos no saldrían NUNCA y nada lo diría (regla v135). Se compara
# la cadena de claves que usa la pantalla contra lo que la función DEVUELVE de verdad,
# sin leer la hoja (el techo es de 60 lecturas/min, v339).
_ps = next(n for n in ast.walk(ast.parse(_fuente("core/projects.py")))
           if isinstance(n, ast.FunctionDef) and n.name == "project_schedule")
_claves = set()
for _n in ast.walk(_ps):
    if isinstance(_n, ast.Return) and isinstance(_n.value, ast.Dict):
        _claves |= {k.value for k in _n.value.keys if isinstance(k, ast.Constant)}
ck("project_schedule devuelve «sched» (la 1ª clave de la cadena)", "sched" in _claves, True)

_fn_det = next(n for n in ast.walk(_ui)
               if isinstance(n, ast.FunctionDef) and n.name == "_detalle_proyecto")
_cadena = [ast.unparse(n) for n in ast.walk(_fn_det)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
           and n.func.attr == "get" and "avisos_plan" in ast.unparse(n)]
ck("...y la pantalla pide «avisos_plan» sobre «sched», no sobre la raíz",
   bool(_cadena) and "'sched'" in _cadena[0].replace('"', "'"), True)
# ⚠️ Y `project_schedule` devuelve None si la obra no tiene actividades: sin la guarda,
# el detalle reventaría con AttributeError en una obra recién creada.
ck("...y se protege del None (obra sin actividades)",
   bool(_cadena) and "or {}" in _cadena[0], True)

print("\n" + "=" * 70)
print(f"{n_ok + len(fallos)} comprobaciones — " + ("TODO OK" if not fallos else "HAY FALLOS"))
sys.exit(1 if fallos else 0)
