# -*- coding: utf-8 -*-
"""v481 · El campo no ve el dinero de la obra (decisión del usuario).

Lo que hay que proteger:
  (a) que al campo NO se le pinte el bloque de costos — comprobado EJECUTANDO
      `render_expenses`, no leyendo el `if`: importar no ejecuta (v378);
  (b) que a gestión SÍ se le pinte, o el arreglo habría roto la pantalla del admin
      en vez de proteger la del campo (una sonda negativa sin caso positivo no vale);
  (c) que el campo conserve LO SUYO: cargar recibos y verlos;
  (d) que el interruptor sea `ver_costos` y NO `can_delete`: ese dice «puede borrar
      recibos», y quien mañana quiera dejar al campo borrar los suyos le abriría las
      finanzas sin enterarse;
  (e) que por defecto sea False — un sitio de llamada que se olvide falla CERRADO.
"""
import ast
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)                      # los secrets se buscan desde el CWD (trampa n19)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "campo000", "nombre": "campo000",
                            "rol": "field", "grupo": "cliente1"}

fallos = []
n_ok = 0


def ok(m, det=""):
    """⚠️ Acepta el 2º argumento y lo IGNORA: con `ok(m)` a secas el guardian revienta
    justo cuando PASA, y uno que revienta devuelve != 0 SIEMPRE (v459/v463)."""
    global n_ok
    n_ok += 1
    print("   ok   " + m)


def fallo(m, det=""):
    fallos.append(m)
    print("   FALLO " + m + (" -> %r" % (det,) if det else ""))


SRC = io.open(os.path.join("core", "projects_ui.py"), encoding="utf-8").read()
ARB = ast.parse(SRC)


def funcion(nombre):
    return next((n for n in ARB.body
                 if isinstance(n, ast.FunctionDef) and n.name == nombre), None)


# ── 1 ────────────────────────────────────────────────────────────────────────
print("1. El interruptor dice lo que hace, y por defecto falla CERRADO")
_re = funcion("render_expenses")
_args = [a.arg for a in _re.args.args]
(ok if "ver_costos" in _args else fallo)("`render_expenses` tiene `ver_costos`", _args)
# el defecto de ver_costos
_defs = dict(zip(_args[-len(_re.args.defaults):], _re.args.defaults)) if _re.args.defaults else {}
_d = _defs.get("ver_costos")
(ok if isinstance(_d, ast.Constant) and _d.value is False else fallo)(
    "y por defecto es False (un olvido no enseña dinero)")
# ⚠️ NO puede ser `can_delete` quien decida: ese permiso es otra cosa
_cs = funcion("_costos_section")
(ok if _cs else fallo)("el bloque de dinero vive en su propia funcion")
_llamadas = [n for n in ast.walk(_re)
             if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "_costos_section"]
_guardas = [ast.unparse(n.test) for n in ast.walk(_re)
            if isinstance(n, ast.If) and "_costos_section" in ast.unparse(n)]
(ok if _guardas == ["ver_costos"] else fallo)(
    "y se pinta SOLO bajo `ver_costos`, no bajo `can_delete`", _guardas)

# ── 2 ────────────────────────────────────────────────────────────────────────
print("")
print("2. Los sitios de llamada: gestion si, campo no")
_sitios = {}
for n in ast.walk(ARB):
    if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "render_expenses":
        _kw = {k.arg: ast.unparse(k.value) for k in n.keywords}
        _sitios[_kw.get("key_prefix", "?")] = _kw
(ok if len(_sitios) == 3 else fallo)("siguen siendo 3 sitios de llamada", sorted(_sitios))
(ok if _sitios.get("'fld'", {}).get("ver_costos") is None else fallo)(
    "el CAMPO no lo pide", _sitios.get("'fld'"))
for _k in ("'adm'", "'loc'"):
    (ok if _sitios.get(_k, {}).get("ver_costos") == "True" else fallo)(
        "gestion (%s) SI lo pide" % _k, _sitios.get(_k))

# ── 3 ────────────────────────────────────────────────────────────────────────
print("")
print("3. Lo que se movio: el dinero fuera, los recibos dentro")
_t_cs = ast.unparse(_cs)
_t_re = ast.unparse(_re)
for _pieza, _marca in (("las tarjetas de costo", "Total cost"),
                       ("el presupuesto", "Budget"),
                       ("la mano de obra POR PERSONA", "Labour by person"),
                       ("las ordenes de compra", "_ordenes_section"),
                       ("la curva de gasto", "spend_curve")):
    (ok if _marca in _t_cs and _marca not in _t_re else fallo)(
        "%s ya no esta en la pantalla del campo" % _pieza)
for _pieza, _marca in (("cargar recibo", "Upload receipt"),
                       ("ver los recibos", "Receipts (")):
    (ok if _marca in _t_re else fallo)("el campo conserva: %s" % _pieza)

# ── 4 ────────────────────────────────────────────────────────────────────────
print("")
print("4. EJECUTADO: al campo no se le llama ese bloque; a gestion si")
# ⚠️ Importar no ejecuta (v378). Y una sonda NEGATIVA («no se llamo») no vale nada sin
# el caso POSITIVO al lado: si `render_expenses` reventara antes de llegar, tambien
# saldria «no se llamo» y parecería que protege (trampa n12).
from core import projects_ui as PU                                # noqa: E402
_orig = PU._costos_section
_vistas = []
PU._costos_section = lambda *a, **k: _vistas.append(a[0] if a else "?")
try:
    _vistas.clear()
    PU.render_expenses("PRJ-0001", "cliente1", can_delete=False, key_prefix="g481f")
    (ok if not _vistas else fallo)("con el campo NO se pinta el bloque de dinero", _vistas)
    _vistas.clear()
    PU.render_expenses("PRJ-0001", "cliente1", can_delete=True, key_prefix="g481a",
                       ver_costos=True)
    (ok if _vistas else fallo)("...y con gestion SI se pinta (caso positivo)")
except Exception as e:
    fallo("render_expenses revienta al ejecutarse", "%s: %s" % (type(e).__name__, e))
finally:
    PU._costos_section = _orig

print("")
if fallos:
    print("HAY FALLOS: %d" % len(fallos))
    sys.exit(1)
print("TODO OK - %d comprobaciones" % n_ok)
