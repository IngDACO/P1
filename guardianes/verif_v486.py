# -*- coding: utf-8 -*-
"""v486 · Las cuatro tablas que pintaban «None» y la definicion UNICA de celda vacia.

⚠️ Lo que este guardian protege NO es «que no haya None»: es la CURA. v485 cambio el
None por NaN creyendo (y documentando) que NaN vacia la celda, y seguia pintando «None»
en produccion. Medido en 1.57 con una tabla por caso e interceptando `fillText`:

  | valor de la celda            | column_config de esa columna              | se pinta |
  |------------------------------|-------------------------------------------|----------|
  | nan / None / pd.NA           | ninguno · {} · Column() · NumberColumn ·  | «None»   |
  |                              | +format · TextColumn                      |          |
  | nan + Styler(na_rep="")      | —                                         | «None»   |
  | CADENA ("" o "$12.50")       | ninguno o Column()                        | vacio    |
  | ""                           | NumberColumn (con o sin formato)          | «None»   |

De ahi las dos piezas: el valor se formatea en Python (`tabla.celda`) y la columna se
declara con `tabla.derecha()` — NUNCA con `NumberColumn`, porque una columna TIPADA
convierte incluso la cadena vacia en nulo y vuelve a pintar «None».

Corre en la suite. Importar NO ejecuta (v378), asi que lo que decide se EJECUTA.
"""
import ast
import io
import sys
from pathlib import Path

sys.path.insert(0, ".")

_f = []


def ok(m):
    print("   ok   %s" % m)


def fallo(m):
    print("   FALLO %s" % m)
    _f.append(m)


def _arbol(ruta):
    return ast.parse(io.open(ruta, encoding="utf-8").read())


def _func(arbol, nombre):
    return next((n for n in ast.walk(arbol)
                 if isinstance(n, ast.FunctionDef) and n.name == nombre), None)


from core import tabla                                       # noqa: E402
from core.num import num as _num                             # noqa: E402

# los cuatro sitios: (fichero, funcion, columna, decimales, simbolo)
SITIOS = [
    ("core/contable_ui.py", "_partes_section", None, 2, ""),
    ("core/payroll_ui.py", "render_nominas", "Rate/h", 2, "$"),
    ("core/catalogo_ui.py", "render_catalogo", "Horas", 2, ""),
    ("core/inventory_ui.py", "_detalle", "Costo", 0, "$"),
]

print("1. `tabla.celda` EJECUTADA: que devuelve para cada entrada")
# ⚠️ El cero es un DATO, no una ausencia: quien trabajo 0 h cobra 0, y una celda vacia
# ahi afirmaria que no hay dato.
CASOS = [(None, ""), ("", ""), ("   ", ""), (float("nan"), ""), ("abc", ""),
         (0, "$0.00"), (12.5, "$12.50"), (1234.5, "$1,234.50")]
_mal = [(v, esp, tabla.celda(v, 2, "$")) for v, esp in CASOS
        if tabla.celda(v, 2, "$") != esp]
if _mal:
    for v, esp, got in _mal:
        fallo("celda(%r) -> %r, se esperaba %r" % (v, got, esp))
else:
    ok("los nulos dan vacio, el cero es un dato (%d casos)" % len(CASOS))

try:
    import pandas as _pd
    if tabla.celda(_pd.NA, 2, "$") != "":
        fallo("celda(pd.NA) deberia dar vacio")
    else:
        ok("pd.NA tambien da vacio")
except ImportError:
    fallo("pandas no disponible: el caso pd.NA no se comprobo")

# ⚠️ SIEMPRE una cadena. Si devolviera un float, la columna volveria a ser numerica
# y el nulo se pintaria «None» otra vez — el fallo entero de v485.
_tipos = {type(tabla.celda(v, 2, "$")).__name__ for v, _ in CASOS}
if _tipos != {"str"}:
    fallo("celda no devuelve siempre str: %s" % sorted(_tipos))
else:
    ok("devuelve SIEMPRE una cadena (si fuera float, volveria el «None»)")

print("")
print("2. El formato pinta IDENTICO al `NumberColumn` que sustituye")
# ⚠️ Son columnas de DINERO: si el formato cambiara, cada cifra de esas pantallas
# habria cambiado en silencio con el deploy. Ademas `%d` TRUNCA y `.0f` REDONDEA
# (trampa n20), asi que se compara contra el camino viejo COMPLETO: el `round()` que
# hacia el codigo + el printf de Streamlit.


def _viejo(v, dec):
    return ("$%s" % format(int(round(_num(v), 0)), ",")) if dec == 0 else \
           ("$%s" % format(round(_num(v), 2), ",.2f"))


DINERO = [0, 1, 128, 128.4, 128.5, 128.6, 129.5, 1234.5, 1234.56, 999999.99,
          42.5, 0.5, 2.675, 7.005,
          # ⚠️ los cinco formatos de separador de miles: es el fallo de v323, que yo
          # reintroduje en `celda` usando `float()` en vez de `num()` — y ahi era PEOR
          # que en v323, porque salia VACIO («no hay dato») en vez de $0.
          "1,234.56", "1.234,56", "1,234", "1234,56", "$1,500"]
_dif = [(v, d, _viejo(v, d), tabla.celda(v, d, "$"))
        for v in DINERO for d in (0, 2) if _viejo(v, d) != tabla.celda(v, d, "$")]
if _dif:
    for v, d, a, b in _dif:
        fallo("formato distinto con %r (dec=%d): viejo %s, nuevo %s" % (v, d, a, b))
else:
    ok("%d valores x 2 formatos: 0 diferencias" % len(DINERO))

print("")
print("3. `celda` usa `num`, NO `float()` (la leccion de v323)")
_c = _func(_arbol("core/tabla.py"), "celda")
if _c is None:
    fallo("no existe `tabla.celda`")
else:
    _llam = {getattr(n.func, "id", "") for n in ast.walk(_c) if isinstance(n, ast.Call)}
    if "_num" not in _llam and "num" not in _llam:
        fallo("`celda` no llama a num(): un importe con separador de miles saldria VACIO")
    elif "float" in _llam:
        fallo("`celda` vuelve a usar float(): revienta con «1,234.56»")
    else:
        ok("llama a num() y no a float()")

print("")
print("4. `derecha` degrada si Streamlit no soporta `alignment`")
# ⚠️ `requirements.txt` admite desde 1.39 y `alignment` es reciente: sin la guarda, un
# Streamlit sin ese parametro tumbaria la tabla ENTERA. Perder la alineacion es un
# detalle; una tabla que no pinta, no.
_d = _func(_arbol("core/tabla.py"), "derecha")
if _d is None:
    fallo("no existe `tabla.derecha`")
elif not any(isinstance(n, ast.ExceptHandler) for n in ast.walk(_d)):
    fallo("`derecha` no tiene respaldo: reventaria en un Streamlit sin `alignment`")
else:
    _cfg = tabla.derecha("X")
    if not isinstance(_cfg, dict) or _cfg.get("label") != "X":
        fallo("derecha() no devuelve una config utilizable: %r" % (_cfg,))
    else:
        ok("tiene respaldo y devuelve una config con su etiqueta")

print("")
print("5. Los cuatro sitios pasan por `tabla.celda`")
for ruta, fn, col, _dec, _sim in SITIOS:
    f_ = _func(_arbol(ruta), fn)
    if f_ is None:
        fallo("%s: no existe %s()" % (ruta, fn))
        continue
    _usa = any(isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "celda"
               and getattr(getattr(n.func, "value", None), "id", "") == "tabla"
               for n in ast.walk(f_))
    (ok if _usa else fallo)("%s · %s usa tabla.celda" % (Path(ruta).name, fn))

print("")
print("6. Ninguna columna alimentada por `celda` lleva `NumberColumn`")
# ⚠️ ESTE es el hallazgo que decide el arreglo: una columna TIPADA convierte incluso la
# cadena vacia en nulo y vuelve a pintar «None» (medido, caso _I). Asi que las dos
# piezas van juntas o ninguna sirve.
for ruta, fn, col, _dec, _sim in SITIOS:
    if col is None:
        continue
    f_ = _func(_arbol(ruta), fn)
    _tipada = False
    for n in ast.walk(f_):
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if (isinstance(k, ast.Constant) and k.value == col
                        and isinstance(v, ast.Call)
                        and getattr(v.func, "attr", "") in ("NumberColumn",
                                                            "TextColumn")):
                    _tipada = True
    if _tipada:
        fallo("%s: la columna %r sigue tipada -> la cadena vacia se pinta «None»"
              % (Path(ruta).name, col))
    else:
        ok("%s · %r sin NumberColumn" % (Path(ruta).name, col))

print("")
print("7. `tabla` importado a nivel de MODULO (ambito, no presencia)")
# ⚠️ La leccion de v342/v366/v423: un import DENTRO de otra funcion hace creer que el
# modulo esta disponible, y el NameError solo aparece al ABRIR la pantalla.
for ruta, _fn, _c, _d2, _s in SITIOS:
    _t = _arbol(ruta)
    _mod = {a.asname or a.name.split(".")[-1]
            for n in _t.body if isinstance(n, (ast.Import, ast.ImportFrom))
            for a in n.names}
    (ok if "tabla" in _mod else fallo)("%s importa tabla a nivel de modulo"
                                       % Path(ruta).name)

print("")
print("8. `tabla.py` sigue siendo modulo HOJA")
# ⚠️ Lo importan los 23 modulos de interfaz: si empezara a importar un modulo de datos,
# cualquiera de ellos podria entrar en un ciclo.
_HOJA_OK = {"streamlit", "core.i18n", "core.num"}
# ⚠️ Hay que mirar los NOMBRES, no solo el modulo: `from core import projects` tiene
# `module == "core"` —que no empieza por "core."— asi que mirando solo el modulo la
# rotura pasaba. La red veia una sola forma de escribir el import, otra vez.
_imp = set()
for n in _arbol("core/tabla.py").body:
    if isinstance(n, ast.Import):
        _imp |= {a.name for a in n.names}
    elif isinstance(n, ast.ImportFrom) and n.module:
        if n.module == "core":
            _imp |= {"core.%s" % a.name for a in n.names}
        else:
            _imp.add(n.module)
_fuera = {m for m in _imp if m.startswith("core.")} - _HOJA_OK
if _fuera:
    fallo("tabla.py importa de core: %s (deja de ser hoja)" % sorted(_fuera))
else:
    ok("solo %s" % ", ".join(sorted(_imp)))

print("")
if _f:
    print("%d FALLO(S) - v486" % len(_f))
    sys.exit(1)
print("TODO OK - v486")
