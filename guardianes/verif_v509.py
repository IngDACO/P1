# -*- coding: utf-8 -*-
"""v509 · COTIZAR LEYENDO EL PLANO.

Lo que protege:
  (a) las cuatro reglas y la cantidad que da cada una;
  (b) ⚠️ lo más importante: si el plano NO da el dato, la línea entra con cantidad CERO
      **y con el motivo**, y NO se omite. Omitirla haría la cotización más barata sin
      que nadie lo note, y sub-cotizar en silencio se descubre al facturar, cuando ya
      se firmó;
  (c) ⚠️ que nunca se invente un 1: un dato que el plano no da, no se adivina;
  (d) que un ítem MANUAL (o con regla desconocida) no se proponga;
  (e) que la basura en el plano no lance — un PDF trae de todo;
  (f) que las marcas `_regla`/`_falta` NO viajen a la cotización guardada: una línea
      guardada es un precio pactado, no una nota de cómo se propuso;
  (g) la fila posicional del catálogo contra su cabecera (v363);
  (h) que la pantalla AÑADA y no reemplace lo ya escrito (decisión del usuario);
  (i) que el núcleo siga siendo HOJA: sin `cantidad_de` puro no se puede ejercitar nada.
Todo EJECUTANDO: importar no ejecuta (v378) y compilar no verifica nada (v439).
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


from core import catalogo as CAT                                  # noqa: E402
from core import quote_from_plan as QP                            # noqa: E402

PLANO = {"ns": 8, "modelo": "3300", "rail": "T75-3/B"}
SIN_NS = {"ns": None, "modelo": "3300", "rail": "T75-3/B"}

ITEMS = [
    {"ID": "C1", "Name": "Site set-up", "Type": "product", "UnitCost": "1500",
     "Description": "Movilizacion", "QtyRule": QP.FIJA},
    {"ID": "C2", "Name": "Landing door", "Type": "product", "UnitCost": "900",
     "Description": "Puerta de rellano", "QtyRule": QP.POR_PARADA},
    {"ID": "C3", "Name": "Inter-floor", "Type": "product", "UnitCost": "120",
     "Description": "Cableado", "QtyRule": QP.POR_PARADA_MENOS_1},
    {"ID": "C4", "Name": "Special lift", "Type": "product", "UnitCost": "400",
     "Description": "Izaje", "QtyRule": QP.MANUAL},
    {"ID": "C5", "Name": "Sin regla", "Type": "product", "UnitCost": "50",
     "Description": "Sin regla"},
]


def _por(lineas, desc):
    return next((l for l in lineas if l.get("descripcion") == desc), None)


def _campo(lineas, desc, clave, sino="(la linea NO esta)"):
    """El valor de un campo de esa linea, o un aviso si la linea falta.

    ⚠️ `_por(...)["x"]` mata al guardián con TypeError justo cuando la rotura hace
    DESAPARECER la línea — que es precisamente el fallo más grave que vigila esta
    versión (omitir abarata en silencio). La batería lo contaba como «revienta, no
    cuenta» y la rotura se iba de rositas. Un guardián que muere no denuncia: es la
    quinta vez en el día con este mismo patrón.
    """
    l = _por(lineas, desc)
    return l.get(clave) if l else sino


# ═════ 1 · las reglas ════════════════════════════════════════════════════════
print("\n[1] cada regla da su cantidad")
ck("fija = 1 por obra", QP.cantidad_de(QP.FIJA, PLANO), (1, ""))
ck("por parada = NS", QP.cantidad_de(QP.POR_PARADA, PLANO), (8, ""))
ck("por parada menos 1", QP.cantidad_de(QP.POR_PARADA_MENOS_1, PLANO), (7, ""))
ck("manual no propone nada", QP.cantidad_de(QP.MANUAL, PLANO), (0, ""))
ck("el defecto es MANUAL (no se adivina)", QP.REGLA_DEFECTO, QP.MANUAL)


# ═════ 2 · ⚠️ el plano que no da el dato ═════════════════════════════════════
print("\n[2] cuando el plano no lo dice")
_c, _m = QP.cantidad_de(QP.POR_PARADA, SIN_NS)
ck("⚠️ cantidad CERO, nunca un 1 inventado", _c, 0)
ck("...y CON motivo, que es lo que obliga a decidir", bool(_m), True)
ck("...el motivo dice qué falta", "number of stops" in _m, True)
ck("una regla fija no depende del plano", QP.cantidad_de(QP.FIJA, SIN_NS), (1, ""))

# ⚠️ LA propiedad de seguridad de esta version: ninguna linea se cae de la propuesta.
_buena = QP.proponer(PLANO, ITEMS)
_mala = QP.proponer(SIN_NS, ITEMS)
ck("⚠️ sin el dato NO se omite ninguna linea (omitir abarata en silencio)",
   len(_mala["lineas"]), len(_buena["lineas"]))
ck("...y las incompletas se listan con nombre",
   sorted(x["nombre"] for x in _mala["incompletas"]), ["Inter-floor", "Landing door"])
ck("...con la buena no hay incompletas", _mala and _buena["incompletas"], [])
ck("⚠️ la linea incompleta vale CERO, no el precio de una unidad",
   _campo(_mala["lineas"], "Puerta de rellano", "precio_total"), 0.0)


# ═════ 3 · lo que NO se propone ══════════════════════════════════════════════
print("\n[3] lo que no sale del plano")
ck("un item MANUAL no se propone", _por(_buena["lineas"], "Izaje"), None)
ck("...ni uno sin regla", _por(_buena["lineas"], "Sin regla"), None)
ck("...y los dos se dicen, no desaparecen",
   sorted(_buena["saltadas"]), ["Sin regla", "Special lift"])


# ═════ 4 · los precios salen de quotes, no de aquí ═══════════════════════════
print("\n[4] las cantidades sobre el catalogo real")
ck("la puerta de rellano va 8 veces", _campo(_buena["lineas"], "Puerta de rellano", "cantidad"), 8.0)
ck("...por 900 = 7.200", _campo(_buena["lineas"], "Puerta de rellano", "precio_total"), 7200.0)
ck("el cableado va NS-1 = 7", _campo(_buena["lineas"], "Cableado", "cantidad"), 7.0)
ck("la movilizacion va 1", _campo(_buena["lineas"], "Movilizacion", "cantidad"), 1.0)
# ⚠️ Este modulo no calcula ni un importe: el precio lo pone `quotes.linea_de`, que es
# quien sabe de costos y margenes. Dos sitios que calculen precio es como se acaba
# cotizando distinto segun por donde entres (la regla de v361: UNA definicion).
# ⚠️ El chequeo va por AST: la primera version troceaba el fuente buscando la palabra
# «margen», que aparece en el propio docstring — fallaba por su propia construccion,
# el error de v500 otra vez.
_src = _fuente("core/quote_from_plan.py")
_arbol = ast.parse(_src)
_escribe_precio = sorted({
    t.id for n in ast.walk(_arbol) if isinstance(n, (ast.Assign, ast.AugAssign))
    for t in ast.walk(n.targets[0] if isinstance(n, ast.Assign) else n.target)
    if isinstance(t, ast.Name) and t.id in ("precio_total", "costo_unit", "margen_pct",
                                            "costo_total", "precio")})
ck("⚠️ el modulo no calcula ningun importe", _escribe_precio, [])
ck("...se los pide a quotes.linea_de",
   any(isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "linea_de"
       for n in ast.walk(_arbol)), True)


# ═════ 5 · basura en el plano ════════════════════════════════════════════════
print("\n[5] un PDF trae de todo")
for _v in ("ocho", "", None, [], {"x": 1}, -3):
    _r = QP.cantidad_de(QP.POR_PARADA, {"ns": _v})
    if _r != (0, QP._SIN_NS):
        fallo("ns=%r deberia dar (0, motivo)" % _v, _r)
        break
else:
    ok("ninguna basura lanza, y todas dan (0, motivo)")
ck("«3.0» del PDF se lee como 3", QP.cantidad_de(QP.POR_PARADA, {"ns": "3.0"}), (3, ""))
ck("un plano vacio no lanza", isinstance(QP.proponer({}, ITEMS), dict), True)
ck("...ni un catalogo vacio", QP.proponer(PLANO, [])["lineas"], [])


# ═════ 6 · las marcas no viajan a la cotizacion ══════════════════════════════
print("\n[6] lo que se guarda")
ck("la propuesta lleva marcas para la pantalla",
   sorted(k for k in _buena["lineas"][0] if k.startswith("_")), ["_falta", "_regla"])
ck("⚠️ limpiar() las quita antes de guardar",
   [k for l in QP.limpiar(_buena["lineas"]) for k in l if k.startswith("_")], [])
ck("...y no toca el resto de la linea",
   QP.limpiar(_buena["lineas"])[0]["precio_total"], _buena["lineas"][0]["precio_total"])


# ═════ 7 · la hoja y la pantalla ═════════════════════════════════════════════
print("\n[7] catalogo y pantalla")
ck("«QtyRule» es la ULTIMA columna del catalogo", CAT.HEADERS[-1], "QtyRule")
_tr = ast.parse(_fuente("core/catalogo.py"))
_cr = next(n for n in ast.walk(_tr) if isinstance(n, ast.FunctionDef) and n.name == "crear")
_ap = next((n for n in ast.walk(_cr) if isinstance(n, ast.Call)
            and getattr(n.func, "attr", "") == "append_row"), None)
assert _ap is not None, "catalogo.crear ya no usa append_row"
ck("la fila de crear() cuadra con la cabecera",
   len(_ap.args[0].elts), len(CAT.HEADERS))
ck("...y acepta la regla", "qty_rule" in [a.arg for a in _cr.args.args], True)

_ui = ast.parse(_fuente("core/quotes_ui.py"))
_dp = next((n for n in ast.walk(_ui) if isinstance(n, ast.FunctionDef)
            and n.name == "_desde_plano"), None)
assert _dp is not None, "no se encontro _desde_plano"
_sd = ast.unparse(_dp)
ck("⚠️ la pantalla AÑADE, no reemplaza lo ya escrito",
   "list(_st.get('new_lineas') or []) +" in _sd, True)
ck("...y limpia las marcas antes de sembrar", "_QP.limpiar(" in _sd, True)
ck("las incompletas se pintan como ERROR, no como nota", "st.error(" in _sd, True)


# ═════ 8 · el nucleo es HOJA ═════════════════════════════════════════════════
print("\n[8] sin ciclos")
_imp = [ast.unparse(n) for n in ast.parse(_src).body
        if isinstance(n, (ast.Import, ast.ImportFrom))]
ck("no importa nada de core a nivel de modulo",
   [i for i in _imp if "core" in i], [])

print("\n" + "=" * 70)
print(f"{n_ok + len(fallos)} comprobaciones — " + ("TODO OK" if not fallos else "HAY FALLOS"))
sys.exit(1 if fallos else 0)
