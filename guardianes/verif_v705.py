# -*- coding: utf-8 -*-
"""v705 · el aviso del 404 de Xero Payroll ya no dice que el parte «can still go by file» (Xero Payroll no importa
ficheros: el parte se teclea, lo dice la sección de al lado). Decisión del usuario, 24/11, al cerrar el ciclo 7.

Ejecutando `xero_nomina.datos` con Xero sustituido (sin red), y mirando el orden de Accounting: la frase dice
«just above», así que «Timesheet for payroll» tiene que ir ANTES del bloque de Xero Payroll.
"""
import ast
import os
import sys

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:900]))
    if not cond:
        FALLOS.append(nombre)


from core import xero as X, xero_nomina as XN                               # noqa: E402

_api = X._api
try:
    X._api = lambda g, m, r, **k: (404, {}, {})
    e = XN.datos("cliente1")["error"]
finally:
    X._api = _api
chk("el 404 sigue diciendo la causa y que esperar no lo arregla", "no Payroll AU" in e
    and "waiting does not change that" in e, e)
chk("…y el parte: «in «Timesheet for payroll», just above, to key into Xero»",
    "«Timesheet for payroll», just above, to key into Xero" in e, e)
chk("…sin «can still go by file» (Xero Payroll no importa ficheros)", "by file" not in e, e)

_src = open(os.path.join(RAIZ, "core", "contable_ui.py"), encoding="utf-8").read()
_f = next(n for n in ast.walk(ast.parse(_src)) if isinstance(n, ast.FunctionDef) and n.name == "_partes_section")
_cuerpo = ast.unparse(_f)
_render = next(n for n in ast.walk(ast.parse(_src)) if isinstance(n, ast.FunctionDef) and n.name == "render_contable")
_r = ast.unparse(_render)
chk("«just above» es verdad: la sección «Timesheet for payroll» va antes de `_partes_section`, y dentro de esta el "
    "fichero del parte va antes del bloque de Xero Payroll",
    -1 < _r.find("Timesheet for payroll") < _r.find("_partes_section(grupo)")
    and -1 < _cuerpo.find("_parte_csv(grupo, desde, hasta)") < _cuerpo.find("xero_ui.render_partes_xero(grupo)"),
    (_r.find("Timesheet for payroll"), _r.find("_partes_section(grupo)")))

print()
print("TODO OK" if not FALLOS else f"{len(FALLOS)} FALLO(S): {FALLOS}")
sys.exit(1 if FALLOS else 0)
