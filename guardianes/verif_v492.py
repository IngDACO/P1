# -*- coding: utf-8 -*-
"""v492 · Los ajustes contables se guardan por CLAVES, nunca volcando `mapa()` entero.

Lo que falla EN SILENCIO y hay que proteger:
  (a) volcar `mapa()` —lo guardado YA FUSIONADO con los valores de fábrica— congela en el
      grupo todos los valores por defecto: un cambio futuro en el código deja de llegarle;
  (b) guardar una clave no puede BORRAR las otras (las cuentas de MYOB al guardar las de
      Xero, o el plan de cuentas al guardar el emparejado);
  (c) si no se puede LEER lo guardado, NO se escribe: tratar el fallo como «vacío» y
      escribir solo lo nuevo borraría todo lo que había;
  (d) se lee FRESCO, no de la caché: fusionar sobre algo de hace 120 s pierde lo que otra
      sesión acaba de guardar;
  (e) una sola búsqueda de la fila del grupo para quien lee y quien escribe.
Todo EJECUTANDO con la hoja sustituida.
"""
import ast
import io
import json
import logging
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

fallos = []
n_ok = 0


def ok(que):
    global n_ok
    n_ok += 1
    print(f"  ok   {que}")


def fallo(que, detalle=""):
    fallos.append(que)
    print(f"  *** FALLO  {que}" + (f"  -> {detalle}" if detalle else ""))


def ck(que, real, esperado):
    if real == esperado:
        ok(que)
    else:
        fallo(que, f"{real!r} != {esperado!r}")


def _fuente(f):
    return io.open(os.path.join(RAIZ, f), encoding="utf-8").read()


from core import auth, contable, xero_nomina as XN               # noqa: E402

# ═════ 1 · guardar_claves EJECUTADO contra una hoja falsa ════════════════════
print("\n[1] guardar_claves: solo lo que se toca, y nada de lo que había se pierde")
_orig = (auth.group_text_setting_fresco, auth.set_group_setting, auth.group_text_setting)
_HOJA = {"AccountingJSON": ""}
_ESCRITO = []


def _leer_fresco(g, f, d=""):
    return _HOJA.get(f) or d


def _escribir(g, f, v):
    _ESCRITO.append((g, f, v))
    _HOJA[f] = v
    return True, "ok"


def _caso(inicial, cambios):
    _HOJA["AccountingJSON"] = inicial
    _ESCRITO.clear()
    res = contable.guardar_claves(G, cambios)
    escrito = json.loads(_ESCRITO[-1][2]) if _ESCRITO else None
    return res, escrito


try:
    auth.group_text_setting_fresco = _leer_fresco
    auth.set_group_setting = _escribir
    # ⚠️ Si guardar_claves leyera de la CACHÉ (lo que no debe), vería esto y no la hoja.
    auth.group_text_setting = lambda g, f, d="": '{"CACHE_VIEJA": 1}' if f == "AccountingJSON" else d

    res, esc = _caso("", {"xero_empleados": {"tenant": "T1", "map": {"ana": "E1"}}})
    ck("desde vacío escribe SOLO la clave tocada (no congela los de fábrica)",
       (res[0], sorted(esc or {})), (True, ["xero_empleados"]))
    ck("...y en la columna AccountingJSON", _ESCRITO[-1][1] if _ESCRITO else None, "AccountingJSON")

    res, esc = _caso(json.dumps({"cuentas": {"myob": {"Fuel": "6-9999"}}, "moneda": "NZD"}),
                     {"cuentas": {"xero": {"Fuel": "449"}}})
    ck("guardar las cuentas de Xero NO borra las de MYOB (fusión de un nivel)",
       (esc or {}).get("cuentas"), {"myob": {"Fuel": "6-9999"}, "xero": {"Fuel": "449"}})
    ck("...ni otras claves guardadas", (esc or {}).get("moneda"), "NZD")

    res, esc = _caso(json.dumps({"xero_empleados": {"tenant": "T1", "map": {"ana": "E1", "bea": "E2"}}}),
                     {"xero_empleados": {"tenant": "T1", "map": {"ana": "E1"}}})
    ck("un emparejado QUITADO desaparece (el map se sustituye, no se acumula)",
       (esc or {}).get("xero_empleados"), {"tenant": "T1", "map": {"ana": "E1"}})

    res, esc = _caso(json.dumps({"xero_estado": "DRAFT", "seguimiento": False}),
                     {"xero_estado": "AUTHORISED"})
    ck("un valor simple se sustituye y el resto se queda",
       esc, {"xero_estado": "AUTHORISED", "seguimiento": False})

    ck("no lee de la caché (no aparece la clave que solo existe en la caché)",
       "CACHE_VIEJA" in json.dumps(esc or {}), False)

    # (c) fallo de lectura → no se escribe
    def _revienta(*a, **k):
        raise RuntimeError("429 cuota")
    auth.group_text_setting_fresco = _revienta
    _ESCRITO.clear()
    res = contable.guardar_claves(G, {"xero_estado": "DRAFT"})
    ck("si NO se puede leer lo guardado, NO escribe", (res[0], len(_ESCRITO)), (False, 0))
    ck("...y lo dice", "could not be read" in str(res[1]), True)
    auth.group_text_setting_fresco = _leer_fresco

    # ilegible → se reemplaza, dejando rastro
    _logs = []

    class _H(logging.Handler):
        def emit(self, rec):
            _logs.append(rec.getMessage())
    _h = _H()
    contable.logger.addHandler(_h)
    res, esc = _caso("{esto no es json", {"xero_estado": "DRAFT"})
    contable.logger.removeHandler(_h)
    ck("un JSON ilegible (nadie podía leerlo) se reemplaza por lo nuevo",
       (res[0], esc), (True, {"xero_estado": "DRAFT"}))
    ck("...y deja rastro en el log", any("ilegible" in m for m in _logs), True)

    # (a) el escritor real del emparejado
    _HOJA["AccountingJSON"] = ""
    _ESCRITO.clear()
    XN.guardar_emparejado(G, "T9", {"juan": "E7", "pepe": ""})
    ck("guardar_emparejado (el caso visto en producción) escribe SOLO xero_empleados",
       json.loads(_ESCRITO[-1][2]) if _ESCRITO else None,
       {"xero_empleados": {"tenant": "T9", "map": {"juan": "E7"}}})

    # y el lector sigue viendo lo de fábrica debajo
    auth.group_text_setting = lambda g, f, d="": _HOJA.get(f) or d
    m = contable.mapa(G)
    ck("mapa() sigue dando los de fábrica + lo guardado",
       (m.get("cuentas", {}).get("xero", {}).get(contable.VENTAS), sorted(m["xero_empleados"]["map"])),
       ("200", ["juan"]))
finally:
    (auth.group_text_setting_fresco, auth.set_group_setting, auth.group_text_setting) = _orig

# ═════ 2 · la lectura fresca y la escritura comparten la fila ════════════════
print("\n[2] auth: lectura fresca y escritura, una sola búsqueda de la fila")


class _WS:
    def __init__(self, filas):
        self.filas = filas
        self.escrito = []

    def row_values(self, i):
        return self.filas[0]

    def get_all_records(self, numericise_ignore=None):
        h = self.filas[0]
        return [dict(zip(h, r)) for r in self.filas[1:]]

    def update_cell(self, r, c, v):
        self.escrito.append((r, c, v))


_og = (auth._get_groups_ws, auth._invalidate_groups)
try:
    ws = _WS([["Group", "Description", "AccountingJSON"],
              ["otra", "", '{"a": 1}'],
              ["cliente1", "", '{"b": 2}']])
    auth._get_groups_ws = lambda: (ws, None)
    auth._invalidate_groups = lambda: None
    ck("group_text_setting_fresco lee la fila del grupo", auth.group_text_setting_fresco("Cliente1", "AccountingJSON"), '{"b": 2}')
    ck("set_group_setting escribe en ESA fila", (auth.set_group_setting("cliente1", "AccountingJSON", "X")[0], ws.escrito), (True, [(3, 3, "X")]))
    try:
        auth.group_text_setting_fresco("no-existe", "AccountingJSON")
        fallo("un grupo inexistente LANZA (no devuelve vacío)")
    except LookupError:
        ok("un grupo inexistente LANZA (no devuelve vacío)")
    auth._get_groups_ws = lambda: (None, "sin conexión")
    try:
        auth.group_text_setting_fresco("cliente1", "AccountingJSON")
        fallo("sin hoja LANZA (no devuelve vacío)")
    except RuntimeError:
        ok("sin hoja LANZA (no devuelve vacío)")
    ck("set_group_setting sin hoja devuelve el error sin escribir", auth.set_group_setting("cliente1", "X", 1)[0], False)
finally:
    (auth._get_groups_ws, auth._invalidate_groups) = _og

_ta = ast.parse(_fuente("core/auth.py"))
_fns = {n.name: n for n in _ta.body if isinstance(n, ast.FunctionDef)}


def _llama(fn, nombre):
    return any(isinstance(c, ast.Call) and getattr(c.func, "id", getattr(c.func, "attr", "")) == nombre
               for c in ast.walk(fn))


ck("set_group_setting y la lectura fresca usan la MISMA búsqueda (_grupo_fresco)",
   (_llama(_fns["set_group_setting"], "_grupo_fresco"), _llama(_fns["group_text_setting_fresco"], "_grupo_fresco")),
   (True, True))
ck("la lectura fresca NO pasa por la caché", _llama(_fns["group_text_setting_fresco"], "_group_records"), False)

# ═════ 3 · estático: nadie vuelve a volcar mapa() ════════════════════════════
print("\n[3] estático: ningún escritor vuelca mapa() ni escribe AccountingJSON por su cuenta")
_mods = sorted(f for f in os.listdir("core") if f.endswith(".py")) + ["../app.py"]
_viejo, _directos, _volcados = [], [], []
_arboles = {}
for f in _mods:
    p = os.path.join("core", f)
    tr = ast.parse(_fuente(p))
    _arboles[f] = tr
    for n in ast.walk(tr):
        if isinstance(n, (ast.FunctionDef, ast.Attribute, ast.Name)):
            nombre = getattr(n, "name", None) or getattr(n, "attr", None) or getattr(n, "id", None)
            if nombre == "guardar_mapa":
                _viejo.append(f"{f}:{n.lineno}")
        if isinstance(n, ast.Call) and getattr(n.func, "attr", getattr(n.func, "id", "")) == "set_group_setting":
            if any(isinstance(a, ast.Constant) and a.value == "AccountingJSON" for a in n.args):
                _directos.append(f)
    # dentro de cada función: lo que se pasa a guardar_claves no puede venir de mapa()
    for fn in [x for x in ast.walk(tr) if isinstance(x, ast.FunctionDef)]:
        asign = {}
        for a in ast.walk(fn):
            if isinstance(a, ast.Assign):
                for tg in a.targets:
                    if isinstance(tg, ast.Name):
                        asign[tg.id] = ast.unparse(a.value)
        for c in ast.walk(fn):
            if isinstance(c, ast.Call) and getattr(c.func, "attr", "") == "guardar_claves":
                for arg in c.args[1:]:
                    txt = ast.unparse(arg)
                    if isinstance(arg, ast.Name):
                        txt = asign.get(arg.id, txt)
                    if "mapa(" in txt or "dict(cfg" in txt or txt.strip() == "cfg":
                        _volcados.append(f"{f}:{fn.name}")

ck("guardar_mapa ya no existe (ni definición ni llamadas)", _viejo, [])
ck("solo contable.py escribe AccountingJSON", sorted(set(_directos)), ["contable.py"])
ck("ningún guardar_claves recibe mapa()/cfg entero", _volcados, [])
# la sonda de volcados, validada contra el caso roto construido (trampa nº12)
_roto = ast.parse("def w(grupo):\n    cfg = dict(contable.mapa(grupo))\n    cfg['x'] = 1\n"
                  "    return contable.guardar_claves(grupo, cfg)\n")
_hit = []
for fn in [x for x in ast.walk(_roto) if isinstance(x, ast.FunctionDef)]:
    asign = {tg.id: ast.unparse(a.value) for a in ast.walk(fn) if isinstance(a, ast.Assign)
             for tg in a.targets if isinstance(tg, ast.Name)}
    for c in ast.walk(fn):
        if isinstance(c, ast.Call) and getattr(c.func, "attr", "") == "guardar_claves":
            for arg in c.args[1:]:
                txt = asign.get(arg.id, "") if isinstance(arg, ast.Name) else ast.unparse(arg)
                if "mapa(" in txt:
                    _hit.append(fn.name)
ck("...y esa sonda SÍ caza un volcado construido", _hit, ["w"])

_escritores = {("xero_nomina.py", "guardar_emparejado"), ("xero_ui.py", "_guardar_estado"),
               ("contable_ui.py", "_editor_cuentas"), ("contable_ui.py", "_editor_conceptos")}
for f, nombre in sorted(_escritores):
    fn = next((x for x in ast.walk(_arboles[f]) if isinstance(x, ast.FunctionDef) and x.name == nombre), None)
    ck(f"{f}:{nombre} guarda con guardar_claves", bool(fn) and _llama(fn, "guardar_claves"), True)

print("\n" + "=" * 70)
print(f"{n_ok + len(fallos)} comprobaciones — " + ("TODO OK" if not fallos else "HAY FALLOS"))
sys.exit(1 if fallos else 0)
