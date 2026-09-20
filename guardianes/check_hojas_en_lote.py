# -*- coding: utf-8 -*-
"""Toda hoja que se lea por LOTE está en el lote (21/09/2026).

Por qué existe: `hojas.registros(SHEET)` **sin cabeceras** devuelve `None` cuando esa
hoja no está en `HOJAS_LECTURA`. El módulo que la lee no recibe un error — recibe una
lista vacía, y lee **VACÍO PARA SIEMPRE**. La fila está escrita en el libro y la app no
la ve.

Ya mordió dos veces: v461 (`TimeCorrections`) lo dejó anotado en un comentario, y v507
(`Variations`, `Claims`) volvió a caer en lo mismo pese a ese aviso. Un comentario no es
una red; esto sí.

⚠️ Solo mira lecturas SIN cabeceras. Con cabeceras, `registros(t, cabeceras)` cae a
`get_sheet`, que crea la hoja y funciona fuera del lote — a costa de una llamada suelta,
que es otro problema (v339) pero no un vacío silencioso.
"""
import ast
import os
import pathlib
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Bobo", "rol": "administrator", "grupo": "cliente1"}

from core import hojas                                            # noqa: E402

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


def _consts(mod_ast):
    """{nombre: valor} de las constantes de texto del módulo — de ahí salen los SHEET."""
    out = {}
    for n in mod_ast.body:
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) \
                and isinstance(n.value.value, str):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    out[t.id] = n.value.value
    return out


def sin_cabeceras(mod_ast, consts):
    """Los títulos que ese módulo lee por lote SIN cabeceras."""
    out = set()
    for n in ast.walk(mod_ast):
        if not (isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "registros"):
            continue
        if len(n.args) != 1:            # con cabeceras: cae a get_sheet, otro camino
            continue
        a = n.args[0]
        if isinstance(a, ast.Constant) and isinstance(a.value, str):
            out.add(a.value)
        elif isinstance(a, ast.Name) and a.id in consts:
            out.add(consts[a.id])
    return out


LOTE = set(hojas.HOJAS_LECTURA)

print("\n[1] ninguna hoja se lee por lote estando fuera del lote")
fuera = {}
for p in sorted(pathlib.Path(os.path.join(RAIZ, "core")).glob("*.py")):
    try:
        tr = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        continue
    _c = _consts(tr)
    faltan = sorted(t for t in sin_cabeceras(tr, _c) if t not in LOTE)
    if faltan:
        fuera[p.name] = faltan

ck("⚠️ ninguna leeria VACIO PARA SIEMPRE", fuera, {})
if fuera:
    for m, hs in sorted(fuera.items()):
        print("        %s -> %s" % (m, ", ".join(hs)))

print("\n[2] la red sabe ver el caso conocido-malo")
# ⚠️ Un «0 fuera» no vale nada hasta demostrar que la sonda detecta uno (nº12).
_malo = ast.parse('SHEET = "HojaFantasma"\n'
                  'def f():\n    return hojas.registros(SHEET)\n')
ck("detecta una hoja fuera del lote",
   sorted(t for t in sin_cabeceras(_malo, _consts(_malo)) if t not in LOTE),
   ["HojaFantasma"])
_bueno = ast.parse('SHEET = "Projects"\n'
                   'def f():\n    return hojas.registros(SHEET)\n')
ck("...y no denuncia a una que si esta",
   sorted(t for t in sin_cabeceras(_bueno, _consts(_bueno)) if t not in LOTE), [])
_concab = ast.parse('SHEET = "HojaFantasma"\n'
                    'def f():\n    return hojas.registros(SHEET, HEADERS)\n')
ck("...ni a una leida CON cabeceras, que es otro camino",
   sorted(t for t in sin_cabeceras(_concab, _consts(_concab)) if t not in LOTE), [])

print("\n[3] las que ya mordieron siguen dentro")
for h in ("TimeCorrections", "Variations", "Claims", "PurchaseOrders"):
    ck("«%s» esta en el lote" % h, h in LOTE, True)

print("\n" + "=" * 70)
print(f"{n_ok + len(fallos)} comprobaciones — " + ("TODO OK" if not fallos else "HAY FALLOS"))
sys.exit(1 if fallos else 0)
