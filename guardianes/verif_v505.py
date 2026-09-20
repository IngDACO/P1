# -*- coding: utf-8 -*-
"""v505 · el MATERIAL que bloquea una actividad: que el retraso tenga causa.

Quinto y último hueco de gestión de instalación. v499 puso las dependencias, v500 el
pronóstico, v501 la línea base, v502 el responsable. Esto pone la CAUSA: «la 3 no
arrancó porque espera el riel, que llega el 25».

Lo que protege:
  (a) la fila posicional contra su cabecera, con «ActivityOrder» AL FINAL (v363);
  (b) que solo bloquee lo PENDIENTE — una orden recibida ya no bloquea nada;
  (c) que una orden SIN actividad no bloquee a nadie (afirmarlo seria inventarselo);
  (d) ⚠️ que sin fecha esperada bloquee pero NO se diga atrasada: no se puede decir que
      algo llega tarde si nadie dijo cuando llegaba (mismo criterio que `atrasadas`);
  (e) que una celda con basura no tumbe la pantalla;
  (f) que el nº de Orden viaje hasta el diagnostico y la causa se pinte donde el sintoma;
  (g) que el CAMPO lo vea y NO lo pueda editar;
  (h) que la opcion «ninguna» lleve TEXTO (la leccion de v504: "" pinta «None»);
  (i) que las ordenes sean OPCIONALES — sin ellas la pantalla de estado sigue en pie.
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


from core import orders as O                                      # noqa: E402

_SRC_UI = _fuente("core/projects_ui.py")
_TR_UI = ast.parse(_SRC_UI)


def _fn(nombre):
    return next((n for n in ast.walk(_TR_UI)
                 if isinstance(n, ast.FunctionDef) and n.name == nombre), None)


# ═════ 1 · la hoja: la columna nueva no descuadra la fila (v363) ═════════════
print("\n[1] «ActivityOrder» al final, y la fila con ella dentro")
ck("«ActivityOrder» es la ULTIMA columna de Ordenes", O.HEADERS[-1], "ActivityOrder")
ck("...y su indice sale de la cabecera", O._COL["ActivityOrder"], len(O.HEADERS))

_tr_o = ast.parse(_fuente("core/orders.py"))
_cr = next(n for n in ast.walk(_tr_o) if isinstance(n, ast.FunctionDef) and n.name == "crear")
_ap = next((n for n in ast.walk(_cr) if isinstance(n, ast.Call)
            and getattr(n.func, "attr", "") == "append_row"), None)
assert _ap is not None, "crear ya no usa append_row (revisar el chequeo)"
ck("la fila de crear() tiene tantos valores como columnas",
   len(_ap.args[0].elts), len(O.HEADERS))
ck("...y `crear` acepta la actividad",
   "actividad" in [a.arg for a in _cr.args.args], True)


# ═════ 2 · bloqueos: EJECUTANDO, que es donde se ve ══════════════════════════
print("\n[2] que bloquea y que no")
HOY = dt.date.today()


def _ord(**kw):
    base = {"ID": "ORD-1", "ProjectID": "PRJ-1", "Status": O.PENDIENTE,
            "Supplier": "Acme", "Description": "Rieles T75", "ExpectedDate": "",
            "ActivityOrder": "3"}
    base.update(kw)
    return base


def _blq(regs, grupo=None):
    _o = O.list_for
    try:
        O.list_for = lambda pid, estado=None: [r for r in regs
                                               if estado is None or r["Status"] == estado]
        return O.bloqueos("PRJ-1", grupo)
    finally:
        O.list_for = _o


# ⚠️ Control PRIMERO (v459): si el caso positivo no bloquea, los negativos pasan por el
# motivo equivocado y no significan nada.
_r = _blq([_ord(ExpectedDate=(HOY - dt.timedelta(days=3)).strftime("%Y-%m-%d"))])
ck("una orden PENDIENTE ligada a la 3 la bloquea", sorted(_r), [3])
ck("...y con la fecha pasada se dice ATRASADA", _r[3][0]["tarde"], True)
ck("...con el proveedor y la descripcion, que es lo accionable",
   (_r[3][0]["proveedor"], _r[3][0]["descripcion"]), ("Acme", "Rieles T75"))

_r = _blq([_ord(ExpectedDate=(HOY + dt.timedelta(days=5)).strftime("%Y-%m-%d"))])
ck("con fecha futura bloquea pero NO esta atrasada", (list(_r), _r[3][0]["tarde"]), ([3], False))

# ⚠️ (d) el criterio de `atrasadas`: sin fecha no se puede afirmar que llega tarde
_r = _blq([_ord(ExpectedDate="")])
ck("⚠️ sin fecha esperada bloquea...", list(_r), [3])
ck("...pero NO se dice atrasada (nadie dijo cuando llegaba)",
   (_r[3][0]["tarde"], _r[3][0]["esperada"]), (False, None))

# ⚠️ (b) solo lo pendiente
ck("una orden RECIBIDA ya no bloquea", _blq([_ord(Status=O.RECIBIDA)]), {})
ck("...ni una CANCELADA", _blq([_ord(Status=O.CANCELADA)]), {})

# ⚠️ (c) sin actividad no se inventa a quien bloquea
ck("una orden sin actividad no bloquea a nadie", _blq([_ord(ActivityOrder="")]), {})

# ⚠️ (e) basura en la celda
ck("una celda con basura no tumba la pantalla", _blq([_ord(ActivityOrder="tres")]), {})

# varias ordenes sobre la misma actividad
_r = _blq([_ord(ID="ORD-1"), _ord(ID="ORD-2", Description="Tornilleria")])
ck("varias ordenes sobre la misma actividad se acumulan", len(_r.get(3, [])), 2)


# ═════ 3 · las ordenes son OPCIONALES ════════════════════════════════════════
print("\n[3] sin ordenes configuradas, la pantalla sigue en pie")
import core.projects_ui as PUI                                    # noqa: E402
_oc = O.is_configured
try:
    O.is_configured = lambda: False
    ck("sin Sheets de ordenes, `_bloqueos_de` devuelve {} y no lanza",
       PUI._bloqueos_de("PRJ-1", "cliente1"), {})
finally:
    O.is_configured = _oc

_ob = O.bloqueos
try:
    def _revienta(pid, grupo=None):
        raise RuntimeError("hoja caida")
    O.bloqueos = _revienta
    O.is_configured = lambda: True
    # ⚠️ La llamada va envuelta: si `_bloqueos_de` deja de tragarse el fallo, el
    # guardián tiene que DENUNCIARLO, no morir con él. Un guardián que revienta lo
    # cuenta la batería como «no cuenta» y la rotura se va de rositas — es la tercera
    # vez hoy con este mismo patrón (v502 con `_ps["owners"]`, v503 en la batería).
    try:
        _res = PUI._bloqueos_de("PRJ-1", "cliente1")
    except Exception as e:
        _res = "LANZO %s" % type(e).__name__
    ck("...y si la hoja revienta, tampoco tumba la pantalla de estado", _res, {})
finally:
    O.bloqueos, O.is_configured = _ob, _oc


# ═════ 4 · el nº de Orden viaja, y la causa se pinta con el sintoma ══════════
print("\n[4] de la orden al diagnostico, y del diagnostico a la pantalla")
_diag = _fn("_diagnostico")
assert _diag is not None, "no se encontro _diagnostico"
_sd = ast.unparse(_diag)
ck("_diagnostico lleva el nº de Orden de cada actividad", _sd.count("'orden': _or"), 2)

_est = _fn("_estado_section")
assert _est is not None, "no se encontro _estado_section"
_se = ast.unparse(_est)
# ⚠️ Se cuentan las LLAMADAS por AST, no subcadenas: con un `in` basta que quede UNA de
# las dos y la otra se podria borrar sin que nadie se entere, y el texto cuenta ademas
# el `def` (el fallo de v502 al contar `_dueno`). Son DOS: parada y arrastrada.
_ll = [n for n in ast.walk(_est) if isinstance(n, ast.Call)
       and getattr(n.func, "id", "") == "_espera"]
ck("la causa se pinta en la parada Y en la arrastrada", len(_ll), 2)
ck("...leyendo los bloqueos por el helper que degrada", "_bloqueos_de(pid, grupo)" in _se, True)


# ═════ 5 · el campo LO VE y no lo toca ═══════════════════════════════════════
print("\n[5] el campo")
_fa = _fn("_field_activities")
assert _fa is not None, "no se encontro _field_activities"
_sf = ast.unparse(_fa)
ck("el chequeo mira la tabla de verdad", "save_field_progress" in _sf, True)
ck("el campo VE que una actividad espera material", "_bloqueos_de(pid" in _sf, True)
# ⚠️ Que lo vea no es que lo edite: no puede haber columna de material en SU cuadro.
_kw = [k.arg for n in ast.walk(_fa) if isinstance(n, ast.Call)
       and getattr(n.func, "attr", "") == "data_editor" for k in n.keywords]
ck("...y su tabla editable sigue teniendo las columnas de siempre",
   ("ActivityOrder" in _sf or "Esperando" in _sf), False)


# ═════ 6 · la opcion «ninguna» lleva TEXTO (leccion de v504) ═════════════════
print("\n[6] el vacio con nombre")
_det = _fn("_detalle_proyecto") or _fn("_ordenes_section")
_so = ast.unparse(_fn("_ordenes_section"))
ck("la opcion «sin actividad» lleva texto, no la cadena vacia",
   "_SIN_ACT = t(" in _so and "[_SIN_ACT] +" in _so, True)
ck("...y al guardar vuelve a «» (no se guarda la etiqueta)",
   "'' if _act == _SIN_ACT else" in _so, True)
ck("se guarda el nº de ORDEN, no el nombre de la actividad",
   "_act.split(' · ', 1)[0]" in _so, True)

print("\n" + "=" * 70)
print(f"{n_ok + len(fallos)} comprobaciones — " + ("TODO OK" if not fallos else "HAY FALLOS"))
sys.exit(1 if fallos else 0)
