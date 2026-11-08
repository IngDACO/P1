# -*- coding: utf-8 -*-
"""v654 · La integridad de los datos (2ª versión de la revisión del código).

1. `update_cell` escribe TAL CUAL (RAW): Sheets ya no reinterpreta «00123», «=…» ni una fecha.
2. Los CSV que exporta la app no llevan ninguna celda que empiece como una fórmula.
3. Los IDs recién dados quedan reservados unos minutos: dos altas a la vez no se pisan.

Nada sale a la red ni escribe: el cliente de gspread y las lecturas van sustituidos.
"""
import ast
import io
import os
import re
import sys
import threading
import time

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:700]))
    if not cond:
        FALLOS.append(nombre)


def sec(t_):
    print(f"\n{'─' * 70}\n{t_}\n{'─' * 70}")


def src(rel):
    return io.open(os.path.join(RAIZ, rel), encoding="utf-8").read()


# ═════════════════════════════════════════════════════════════════════════════
sec("1. `update_cell` escribe TAL CUAL")
import gspread                                                          # noqa: E402
from gspread.worksheet import Worksheet                                 # noqa: E402
from core import timeclock as TC                                        # noqa: E402

_orig = Worksheet.update_cell
TC._instalar_escritura_cruda()
chk("tras instalarla, `Worksheet.update_cell` es la de la app", Worksheet.update_cell is TC._update_cell_en_crudo)
TC._instalar_escritura_cruda()
chk("...e instalarla otra vez no cambia nada", Worksheet.update_cell is TC._update_cell_en_crudo)


class _Cliente:
    def __init__(self):
        self.llamadas = []

    def values_update(self, sid, rango, params=None, body=None):
        self.llamadas.append((sid, rango, params, body))
        return {}


class _Hoja:
    title = "Login"
    spreadsheet_id = "LIBRO"

    def __init__(self):
        self.client = _Cliente()


_h = _Hoja()
Worksheet.update_cell(_h, 3, 2, "=00123")
_ll = _h.client.llamadas
chk("manda `valueInputOption` = RAW", _ll and str(_ll[0][2].get("valueInputOption")).upper().endswith("RAW"), _ll)
chk("...a la celda pedida (B3 de esa hoja) y con el valor tal cual",
    _ll and _ll[0][1] == "'Login'!B3" and _ll[0][3] == {"values": [["=00123"]]}, _ll)
chk("la de gspread era USER_ENTERED (lo que se arregla existe)",
    "user_entered" in __import__("inspect").getsource(_orig))
Worksheet.update_cell = _orig
_ab = next(n for n in ast.walk(ast.parse(src("core/timeclock.py")))
           if isinstance(n, ast.FunctionDef) and n.name == "_abrir")
chk("`_abrir` (el único sitio que abre un libro) la instala",
    any(isinstance(c, ast.Call) and getattr(c.func, "id", "") == "_instalar_escritura_cruda" for c in ast.walk(_ab)))
_FICHEROS = [os.path.relpath(os.path.join(dp, fn), RAIZ).replace("\\", "/")
             for dp, _d, fs in os.walk(RAIZ) if "__pycache__" not in dp for fn in fs if fn.endswith(".py")]


def _aperturas_de(texto):
    """Llamadas que abren un libro (`open_by_key`, `authorize`), por AST (no por texto)."""
    return [c.lineno for c in ast.walk(ast.parse(texto)) if isinstance(c, ast.Call)
            and getattr(c.func, "attr", getattr(c.func, "id", "")) in ("open_by_key", "authorize")]


def _user_entered_de(texto):
    """Lo que pide USER_ENTERED: la constante exacta, `ValueInputOption.user_entered` o `raw=False`
    (por AST: un docstring que lo NOMBRA no cuenta)."""
    out = []
    for n in ast.walk(ast.parse(texto)):
        if isinstance(n, ast.Constant) and n.value == "USER_ENTERED":
            out.append(n.lineno)
        elif isinstance(n, ast.Attribute) and n.attr == "user_entered":
            out.append(n.lineno)
        elif isinstance(n, ast.keyword) and n.arg == "raw" and isinstance(n.value, ast.Constant) and n.value.value is False:
            out.append(n.value.lineno)
    return out


chk("la sonda ve una apertura y un USER_ENTERED conocidos (y no un docstring que lo nombra)",
    _aperturas_de("c = gspread.authorize(x)\nc.open_by_key(k)\n") == [1, 2]
    and len(_user_entered_de('w.update(v, value_input_option="USER_ENTERED")\nw.update(v, raw=False)\n'
                             'x = ValueInputOption.user_entered\n')) == 3
    and _user_entered_de('def f():\n    """manda SIEMPRE `USER_ENTERED`"""\n') == [])
_aperturas = [rel for rel in _FICHEROS if _aperturas_de(src(rel))]
chk("...y de verdad es el único (`open_by_key`/`authorize` solo en timeclock)", _aperturas == ["core/timeclock.py"], _aperturas)
_ue = {rel: _user_entered_de(src(rel)) for rel in _FICHEROS if _user_entered_de(src(rel))}
chk("ninguna escritura de la app pide USER_ENTERED (ni `raw=False`)", _ue == {}, _ue)

# ═════════════════════════════════════════════════════════════════════════════
sec("2. Los CSV, sin fórmulas")
from core import csv_seguro as CS                                       # noqa: E402

_casos = {"=HYPERLINK(\"x\")": "'=HYPERLINK(\"x\")", "@SUM(A1)": "'@SUM(A1)", "+cmd|' /C calc'!A0": "'+cmd|' /C calc'!A0",
          "-2+3": "'-2+3", "\tx": "'\tx", "\rx": "'\rx", "- pending": "'- pending",
          "-120.00": "-120.00", "+61 412 345 678": "+61 412 345 678", "(02) 9999 0000": "(02) 9999 0000",
          "Normal text": "Normal text", "": "", "-": "-"}
_mal = {k: CS.celda(k) for k, v in _casos.items() if CS.celda(k) != v}
chk("cada celda, como debe (13 casos: fórmulas con «'», números y teléfonos intactos)", not _mal, _mal)
chk("los números no se tocan", CS.celda(-5) == -5 and CS.celda(3.5) == 3.5 and CS.celda(None) is None)
import pandas as pd                                                      # noqa: E402

_df = pd.DataFrame([{"Project": "=1+1", "Cost": -10.5, "Note": "ok"}])
_t = CS.tabla(_df)
chk("`tabla`: el texto peligroso con «'», el número intacto",
    _t.iloc[0]["Project"] == "'=1+1" and _t.iloc[0]["Cost"] == -10.5 and _t.iloc[0]["Note"] == "ok", _t.to_dict())
from core import contable                                                # noqa: E402

_csv = contable._escribe(["Supplier", "Amount"], [["=WEBSERVICE(\"x\")", "-5.00"]])
chk("la exportación contable (`contable._escribe`) sale neutralizada",
    "'=WEBSERVICE" in _csv and ",-5.00" in _csv and not re.search(r'(^|,)"?=', _csv, re.M), _csv)
# toda escritura de CSV de la app pasa por `csv_seguro`
_usos = []
for dp, _d, fs in os.walk(RAIZ):
    if "__pycache__" in dp:
        continue
    for fn in fs:
        if fn.endswith(".py") and fn != "csv_seguro.py":
            rel = os.path.relpath(os.path.join(dp, fn), RAIZ).replace("\\", "/")
            for c in ast.walk(ast.parse(src(rel))):
                if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == "to_csv":
                    base = c.func.value
                    ok = isinstance(base, ast.Call) and getattr(base.func, "attr", "") == "tabla"
                    _usos.append((rel, c.lineno, ok))
                if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == "writerow":
                    a0 = c.args[0] if c.args else None
                    ok = isinstance(a0, ast.Call) and getattr(a0.func, "attr", "") == "fila"
                    _usos.append((rel, c.lineno, ok))
chk("cada `.to_csv` y cada `writerow` de la app pasa por `csv_seguro` (y hay alguno)",
    len(_usos) >= 5 and all(x[2] for x in _usos), [x for x in _usos if not x[2]] or len(_usos))

# ═════════════════════════════════════════════════════════════════════════════
sec("3. Los IDs recién dados, reservados")
from core import hojas as H                                              # noqa: E402

_o = (H.ids_referenciados, H._libro_de)
H.ids_referenciados = lambda prefijo, propia="", sheet_id="": set()
H._libro_de = lambda propia: "LIBRO-A" if propia != "OtraHoja" else "LIBRO-B"
H._RESERVADOS.clear()
try:
    a = H.siguiente_id_libre("FAC-", 39, propia="Invoices")
    b = H.siguiente_id_libre("FAC-", 39, propia="Invoices")
    chk("dos altas que leyeron el MISMO máximo salen con números distintos", (a, b) == ("FAC-0040", "FAC-0041"), (a, b))
    H._RESERVADOS.clear()
    _res, _hilos = [], []
    for _ in range(12):
        h = threading.Thread(target=lambda: _res.append(H.siguiente_id_libre("PRJ-", 10, propia="Projects")))
        _hilos.append(h)
        h.start()
    for h in _hilos:
        h.join()
    chk("12 a la vez desde hilos: 12 IDs distintos", len(set(_res)) == 12, sorted(_res))
    H._RESERVADOS.clear()
    _l = H.siguientes_ids_libres("NOM-", 5, cuantos=3, propia="Payroll")
    _l2 = H.siguientes_ids_libres("NOM-", 5, cuantos=2, propia="Payroll")
    chk("en lote también: 3 y luego 2, sin repetir", _l == ["NOM-0006", "NOM-0007", "NOM-0008"]
        and _l2 == ["NOM-0009", "NOM-0010"], (_l, _l2))
    H._RESERVADOS.clear()
    x1 = H.siguiente_id_libre("FAC-", 39, propia="Invoices")
    x2 = H.siguiente_id_libre("FAC-", 39, propia="OtraHoja")
    chk("otro libro no se ve afectado (cada empresa numera lo suyo)", x1 == x2 == "FAC-0040", (x1, x2))
    _ot = H.time.time
    H.time.time = lambda: _ot() + H.RESERVA_S + 1
    try:
        x3 = H.siguiente_id_libre("FAC-", 39, propia="Invoices")
    finally:
        H.time.time = _ot
    chk(f"pasados {H.RESERVA_S} s, un ID que no llegó a escribirse se vuelve a dar", x3 == "FAC-0040", x3)
    H._RESERVADOS.clear()
    H.ids_referenciados = lambda prefijo, propia="", sheet_id="": {"FAC-0040"}
    chk("lo referenciado en otras hojas se sigue saltando (v427)",
        H.siguiente_id_libre("FAC-", 39, propia="Invoices") == "FAC-0041")
finally:
    H.ids_referenciados, H._libro_de = _o
    H._RESERVADOS.clear()
_gen = [rel for rel in ("core/invoices.py", "core/projects.py", "core/expenses.py", "core/alerts.py",
                        "core/clientes.py", "core/orders.py", "core/payroll.py", "core/quotes.py")
        if "siguiente_id_libre" not in src(rel) and "siguientes_ids_libres" not in src(rel)]
chk("los generadores de facturas, obras, gastos, avisos, clientes, órdenes, nóminas y presupuestos pasan por ahí",
    _gen == [], _gen)

print("\n" + ("TODO OK" if not FALLOS else f"{len(FALLOS)} FALLOS: " + " | ".join(FALLOS)))
sys.exit(1 if FALLOS else 0)
