# -*- coding: utf-8 -*-
"""v674 · Lo visto verificando v673 desde el campo (ciclo 2): guardar un recibo decía «Receipt added (4.50).», el
importe sin moneda. Ahora «Receipt added: $4.50.», con miles («$1,234.50»).

Nada sale a la red ni escribe: `expenses.add` con una hoja de mentira.
"""
import os
import sys

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:600]))
    if not cond:
        FALLOS.append(nombre)


from core import expenses as E                                             # noqa: E402


class _WS:
    def __init__(self):
        self.app = []

    def get_all_records(self, **k):
        return []

    def append_row(self, row, **k):
        self.app.append(row)


_w = _WS()
_o = {k: getattr(E, k) for k in ("_ws", "_invalidate", "_next_id")}
try:
    E._ws = lambda: _w
    E._invalidate = lambda: None
    E._next_id = lambda recs: "G-00009"
    ok1, m1 = E.add("PRJ-1", "G", 4.5, creado_por="x")
    ok2, m2 = E.add("PRJ-1", "G", 1234.5, creado_por="x")
finally:
    for k, f in _o.items():
        setattr(E, k, f)
chk("«Receipt added: $4.50.» (salía «Receipt added (4.50).», sin moneda)", ok1 and m1 == "Receipt added: $4.50.", m1)
chk("…con miles: «Receipt added: $1,234.50.»", ok2 and m2 == "Receipt added: $1,234.50.", m2)
chk("…y la hoja guarda el NÚMERO, no el texto con «$»", len(_w.app) == 2 and _w.app[0][7] == "4.5"
    and _w.app[1][7] == "1234.5", [r[7] for r in _w.app])

print("\n" + ("TODO OK" if not FALLOS else f"{len(FALLOS)} FALLO(S): {FALLOS}"))
sys.exit(1 if FALLOS else 0)
