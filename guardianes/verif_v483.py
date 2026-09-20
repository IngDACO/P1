# -*- coding: utf-8 -*-
"""v483 · Identidad fiscal + exportación contable (fase 2.0 y 2.1).

Lo que hay que proteger, y por qué cada cosa falla EN SILENCIO si se rompe:

  (a) el ABN y la razón social en el PDF — un documento titulado «TAX INVOICE» sin
      ABN es incompleto ante la ATO y nada lo señala;
  (b) que los importes salgan SIEMPRE sin impuesto, con el impuesto aparte: si el
      criterio cambiara según el caso, la casilla «inclusive/exclusive» del importador
      se contestaría mal y el GST del cliente saldría torcido;
  (c) que el impuesto REPARTIDO sume exactamente el de la factura — redondear línea a
      línea da diferencias de centavos contra un documento ya emitido;
  (d) que el mapa de cuentas sea POR PERFIL: los códigos de Xero no existen en MYOB,
      y MYOB rechaza la fila entera sin decir por qué;
  (e) que el vencimiento salga del plazo del grupo y no de HOY (entraba vencida);
  (f) que la sub-sección se despache por su ID EXACTO y quede UNA sola al `else`.
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
st.session_state["auth"] = {"usuario": "admin", "nombre": "admin",
                            "rol": "administrator", "grupo": "cliente1"}

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


def _func(mod, nombre):
    for n in ast.walk(ast.parse(_fuente(mod))):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == nombre:
            return n
    return None


from core import auth, contable, expenses, invoices                # noqa: E402

# ═════ 1 · las 4 columnas nuevas, AL FINAL de la cabecera ═══════════════════
print("\n[1] Groups: identidad fiscal y plazo de pago")
_H = auth.GROUPS_HEADERS
for c in ("ABN", "LegalName", "PaymentTermsDays", "AccountingJSON"):
    ck(f"la columna {c} existe", c in _H, True)
# ⚠️ Al final: una columna insertada en medio DESPLAZA todas las siguientes, y las
# filas se escriben por POSICIÓN (el fallo que mató `create_project` 3 versiones, v363).
ck("las nuevas van AL FINAL (migran solas)",
   _H[-4:], ["ABN", "LegalName", "PaymentTermsDays", "AccountingJSON"])
ck("sin duplicados en la cabecera", len(_H), len(set(_H)))

# ⚠️ Una sola definición del setter: `set_group_num_setting` nunca fue numérica, y
# dejar los dos nombres es la duplicación que se desincroniza (v323).
ck("el setter genérico tiene un solo nombre",
   hasattr(auth, "set_group_setting") and not hasattr(auth, "set_group_num_setting"), True)
ck("existe el lector de TEXTO", hasattr(auth, "group_text_setting"), True)
_resto = [f for f in os.listdir(os.path.join(RAIZ, "core")) if f.endswith(".py")]
_viejos = [f for f in _resto if "set_group_num_setting" in _fuente(f"core/{f}")
           and f != "auth.py"]
ck("ningún llamador usa el nombre viejo", _viejos, [])

# ═════ 2 · identidad: se EJECUTA (importar no ejecuta, v378) ════════════════
print("\n[2] identidad() contra la hoja real")
_id = contable.identidad("cliente1")
ck("devuelve las tres claves", sorted(_id), ["abn", "legal", "plazo"])
# ⚠️ Sin razón social cae al nombre del grupo: un grupo sin migrar se comporta como
# antes en vez de sacar una factura sin emisor.
ck("la razón social cae al nombre del grupo", bool(_id["legal"]), True)
ck("el plazo tiene un valor usable", _id["plazo"] >= 0, True)
ck("un grupo inexistente no revienta", contable.identidad("zzz-no-existe")["plazo"], 14)

# ═════ 3 · el mapa se DERIVA, no se escribe a mano ══════════════════════════
print("\n[3] mapa contable")
# ⚠️ Las categorías salen de la lista REAL de gastos: copiarlas dejaría una categoría
# nueva exportándose con la cuenta vacía —en MYOB, una fila rechazada— sin avisar (v433).
ck("las categorías se derivan de expenses", list(contable.CATEGORIAS),
   list(expenses.CATEGORIAS))
_m = contable.mapa("cliente1")
ck("hay cuentas para los dos perfiles", sorted(_m["cuentas"]), ["myob", "xero"])
# ⚠️ POR PERFIL: 200 en Xero no existe en MYOB.
ck("la cuenta de ventas NO es la misma en los dos",
   _m["cuentas"]["xero"][contable.VENTAS] != _m["cuentas"]["myob"][contable.VENTAS], True)
for p in ("xero", "myob"):
    _falt = [c for c in contable.CATEGORIAS if c not in _m["cuentas"][p]]
    ck(f"[{p}] ninguna categoría sin cuenta por defecto", _falt, [])

# ⚠️ Lo guardado SOBRESCRIBE, nunca sustituye: si sustituyera, una categoría añadida
# después de guardar el JSON saldría vacía.
_old = auth.group_text_setting
try:
    auth.group_text_setting = (lambda g, f, d="": '{"cuentas": {"xero": {"Fuel": "999"}}}'
                               if f == "AccountingJSON" else d)
    _m2 = contable.mapa("cliente1")
    ck("lo guardado sobrescribe la cuenta tocada", _m2["cuentas"]["xero"]["Fuel"], "999")
    ck("...y CONSERVA las demás", _m2["cuentas"]["xero"]["Materials"],
       contable._CUENTAS_DEFECTO["xero"]["Materials"])
    ck("...y conserva el OTRO perfil entero",
       _m2["cuentas"]["myob"], contable._CUENTAS_DEFECTO["myob"])
    auth.group_text_setting = lambda g, f, d="": "{no es json" if f == "AccountingJSON" else d
    ck("un JSON ilegible degrada a los de fábrica, no revienta",
       contable.mapa("cliente1")["cuentas"]["xero"][contable.VENTAS],
       contable._CUENTAS_DEFECTO["xero"][contable.VENTAS])
finally:
    auth.group_text_setting = _old

# ═════ 4 · el reparto del impuesto CUADRA ═══════════════════════════════════
print("\n[4] reparte_impuesto")
_casos = [
    ([33.33, 33.33, 33.34], 10.00),     # ⚠️ línea a línea daría 9.99
    ([100.0, 200.0, 700.0], 100.00),
    ([0.333, 0.333, 0.334], 0.10),
    ([1000.0], 100.00),
    ([33.33] * 30, 99.99),
    ([0.0, 0.0], 0.0),
    ([-50.0, 150.0], 10.0),             # una línea negativa (descuento)
]
for imp, tot in _casos:
    _p = contable.reparte_impuesto(imp, tot)
    ck(f"cuadra con {len(imp)} líneas y total {tot}", round(sum(_p), 2), round(tot, 2))
ck("sin líneas devuelve vacío", contable.reparte_impuesto([], 10.0), [])
# ⚠️ El caso tiene que ser uno que el ingenuo NO resuelva, o no prueba nada.
_ing = round(sum(round(x * 0.10, 2) for x in [33.33, 33.33, 33.34]), 2)
ck("el caso elegido NO lo resuelve el redondeo ingenuo", _ing == 10.0, False)

# ═════ 5 · los CSV: columnas, criterio único y contenido ════════════════════
print("\n[5] los dos perfiles")
_X = contable.PERFILES["xero"]["ventas"]
for c in ("*ContactName", "*InvoiceNumber", "*InvoiceDate", "*DueDate", "*Description",
          "*Quantity", "*UnitAmount", "*AccountCode", "*TaxType"):
    ck(f"Xero trae la obligatoria {c}", c in _X, True)
ck("Xero lleva el seguimiento por proyecto", "TrackingOption1" in _X, True)
ck("MYOB lleva Job (su equivalente)", "Job" in contable.PERFILES["myob"]["ventas"], True)
# ⚠️ La 4ª de MYOB es el PO del CLIENTE / la factura del PROVEEDOR: la app no tiene
# ninguno, así que va vacía — llenarla con el proyecto sería un dato que no es ese.
_fm = _func("core/contable.py", "_fila_myob")
_lit = [n for n in ast.walk(_fm) if isinstance(n, ast.List)][0].elts
ck("la 4ª columna de MYOB va VACÍA",
   isinstance(_lit[3], ast.Constant) and _lit[3].value == "", True)

# ⚠️ Nombres de impuesto: verificados en la doc de Xero (tabla de Australia).
ck("impuesto de venta con GST", contable.IMPUESTOS_XERO["venta_con"][1], "GST on Income")
ck("impuesto de venta sin GST", contable.IMPUESTOS_XERO["venta_sin"][1], "GST Free Income")
ck("impuesto de compra con GST", contable.IMPUESTOS_XERO["compra_con"][1], "GST on Expenses")
ck("y el código para la API de 2.3", contable.IMPUESTOS_XERO["venta_con"][0], "OUTPUT")

# ⚠️ UN SOLO CRITERIO: el importe siempre sin impuesto. Se comprueba EJECUTANDO sobre
# el gasto real del grupo, no leyendo el código.
import csv as _csv                                                 # noqa: E402
_r = contable.csv_compras("cliente1", "xero", None, None)
_f = list(_csv.DictReader(io.StringIO(_r["csv"])))
if not _f:
    fallo("no hay ningún gasto con el que comprobar el criterio de impuesto",
          "sin datos, este bloque no afirma nada")
else:
    _pct = auth.group_tax_default("cliente1")
    _neto, _imp = float(_f[0]["*UnitAmount"]), float(_f[0]["TaxAmount"])
    ck("neto + impuesto reconstruye el bruto del recibo",
       round(_neto * (1 + _pct / 100.0) - (_neto + _imp), 2), 0.0)
    _rm = list(_csv.DictReader(io.StringIO(
        contable.csv_compras("cliente1", "myob", None, None)["csv"])))
    ck("MYOB da las dos columnas y son coherentes",
       round(float(_rm[0]["Inc-Tax Amount"]) - float(_rm[0]["Amount"]), 2),
       round(_imp, 2))

ck("un perfil desconocido no revienta",
   contable.csv_ventas("cliente1", "sap", None, None)["filas"], 0)

# ⚠️ Lo anterior afirma la CONSTANTE, y eso no basta: intercambiar el desempaquetado
# (`nombre, cod = …`) deja la constante perfecta y escribe **el código** en el fichero,
# que Xero rechaza fila a fila. Lo destapó la batería de roturas, no leerlo. Así que se
# comprueba lo que el CSV PRODUCE, y en las dos ramas (con GST y sin GST).
ck("[compras reales] el impuesto exportado es el NOMBRE, no el código",
   _f[0]["*TaxType"] if _f else "", contable.IMPUESTOS_XERO["compra_con"][1])

_lf = invoices.list_facturas
try:
    def _falsa(pct):
        return [{"ID": "ZZZ", "Group": "cliente1", "ClientID": "", "ClientName": "ZZZ",
                 "Number": "9999", "Date": "08/09/2026", "ExpiryDate": "22/09/2026",
                 "LinesJSON": '[{"concepto": "ZZZ", "importe": 100}]',
                 "Subtotal": "100", "TaxPct": str(pct), "Tax": str(pct),
                 "Total": "110", "Collected": "0", "Status": "emitida"}]
    invoices.list_facturas = lambda g=None, cliente_id=None: _falsa(10)
    _v = list(_csv.DictReader(io.StringIO(
        contable.csv_ventas("cliente1", "xero", None, None)["csv"])))
    ck("[ventas construidas] con GST sale el nombre de Xero",
       _v[0]["*TaxType"], contable.IMPUESTOS_XERO["venta_con"][1])
    ck("...y NO el código de la API", _v[0]["*TaxType"] == "OUTPUT", False)
    invoices.list_facturas = lambda g=None, cliente_id=None: _falsa(0)
    _v0 = list(_csv.DictReader(io.StringIO(
        contable.csv_ventas("cliente1", "xero", None, None)["csv"])))
    ck("[ventas construidas] sin GST sale la rama exenta",
       _v0[0]["*TaxType"], contable.IMPUESTOS_XERO["venta_sin"][1])
    # ⚠️ Y el CONTROL de la sonda: si no supiera distinguirlo, los dos casos darían lo
    # mismo y el cero no significaría nada (trampa nº12).
    ck("la sonda distingue las dos ramas", _v[0]["*TaxType"] != _v0[0]["*TaxType"], True)
    ck("una anulada NO se exporta",
       (lambda: (setattr(invoices, "list_facturas",
                         lambda g=None, cliente_id=None: [dict(_falsa(10)[0],
                                                               Status="anulada")])
                 or contable.csv_ventas("cliente1", "xero", None, None)["filas"]))(), 0)
finally:
    invoices.list_facturas = _lf

# ⚠️ La opción de seguimiento cae al ID cuando la etiqueta no cabe: recortarla podría
# dar la MISMA opción a dos obras, y el costo de una se cargaría a la otra.
ck("etiqueta corta -> etiqueta", contable._opcion_seguimiento("PRJ-1", "Torre A"), "Torre A")
ck("etiqueta larga -> el ID", contable._opcion_seguimiento("PRJ-1", "T" * 60), "PRJ-1")
ck("sin etiqueta -> el ID", contable._opcion_seguimiento("PRJ-1", ""), "PRJ-1")

# ⚠️ Sin fecha legible NO se puede afirmar que la fila está dentro del periodo.
import datetime as _dt                                             # noqa: E402
ck("fila sin fecha queda fuera de un periodo",
   contable._rango("", _dt.date(2026, 1, 1), _dt.date(2026, 12, 31)), False)
ck("sin periodo, una fila sin fecha tampoco entra", contable._rango("", None, None), False)

# ═════ 6 · el PDF de la factura ═════════════════════════════════════════════
print("\n[6] el PDF lleva la identidad fiscal")
from core import invoice_pdf                                       # noqa: E402
from pypdf import PdfReader                                        # noqa: E402

_fac = {"ID": "ZZZ", "Group": "cliente1", "ClientName": "ZZZ Cliente", "Number": "9999",
        "Date": "2026-09-08", "ExpiryDate": "2026-09-22", "Subtotal": "100",
        "TaxPct": "10", "Tax": "10", "Total": "110", "Collected": "0",
        "LinesJSON": '[{"concepto": "ZZZ", "importe": 100}]', "Status": "emitida"}
_orig = contable.identidad
try:
    contable.identidad = lambda g: {"abn": "99 999 999 999", "legal": "ZZZ Legal Pty Ltd",
                                    "plazo": 14}
    _t = "\n".join(p.extract_text() or "" for p in
                   PdfReader(io.BytesIO(invoice_pdf.generate_invoice_pdf(_fac, {}, "cliente1"))).pages)
    ck("el PDF dice TAX INVOICE", "TAX INVOICE" in _t, True)
    ck("y lleva el ABN", "99 999 999 999" in _t, True)
    ck("y la razón social", "ZZZ Legal Pty Ltd" in _t, True)
    # ⚠️ Sin ABN el PDF NO puede reventar: se emite igual, sin esa línea.
    contable.identidad = lambda g: {"abn": "", "legal": "", "plazo": 14}
    _t2 = "\n".join(p.extract_text() or "" for p in
                    PdfReader(io.BytesIO(invoice_pdf.generate_invoice_pdf(_fac, {}, "Marca"))).pages)
    ck("sin ABN se emite igual", "TAX INVOICE" in _t2, True)
    ck("...y cae a la marca del grupo", "Marca" in _t2, True)
    # ⚠️ Y si la lectura de la identidad FALLA tampoco puede impedir facturar.
    def _revienta(g):
        raise RuntimeError("boom")
    contable.identidad = _revienta
    _t3 = "\n".join(p.extract_text() or "" for p in
                    PdfReader(io.BytesIO(invoice_pdf.generate_invoice_pdf(_fac, {}, "Marca"))).pages)
    ck("un fallo leyendo la identidad no impide emitir", "TAX INVOICE" in _t3, True)
finally:
    contable.identidad = _orig

# ⚠️ El módulo tiene logger propio: el `except` lo usa, y sin él sería un NameError
# latente justo donde nadie mira (v370/v423).
ck("invoice_pdf tiene logger de módulo",
   "logger = logging.getLogger" in _fuente("core/invoice_pdf.py"), True)

# ═════ 7 · el vencimiento sale del PLAZO, no de hoy ═════════════════════════
print("\n[7] vencimiento por defecto")
_src = _fuente("core/invoices_ui.py")
_venc = None
for n in ast.walk(ast.parse(_src)):
    if (isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "date_input"
            and any(k.arg == "key" and getattr(k.value, "value", "") == "fac_venc"
                    for k in n.keywords)):
        _venc = n
_val = next((k.value for k in (_venc.keywords if _venc else []) if k.arg == "value"), None)
# Antes era `clock.today()` pelado; ahora tiene que SUMAR algo.
ck("el vencimiento ya no es HOY pelado", isinstance(_val, ast.BinOp), True)
ck("...y lo que suma es el plazo del grupo",
   "_plazo" in ast.unparse(_val) if _val is not None else False, True)

# ═════ 8 · navegación ═══════════════════════════════════════════════════════
print("\n[8] la sub-sección")
from core import home_ui                                           # noqa: E402
_ids = [i for i, _ in home_ui._SUBSECCIONES["finanzas"][1]]
ck("la sub-sección existe", "📤 Contable" in _ids, True)
# ⚠️ La ÚLTIMA: una nueva no le reordena el menú a quien ya lo usa (v297).
ck("va la última", _ids[-1], "📤 Contable")
ck("sin IDs duplicados", len(_ids), len(set(_ids)))

_fin = _func("core/home_ui.py", "_seccion_finanzas")
_cmp = [ast.literal_eval(n.comparators[0]) for n in ast.walk(_fin)
        if isinstance(n, ast.Compare) and isinstance(n.left, ast.Name)
        and n.left.id == "sub" and isinstance(n.comparators[0], ast.Constant)]
ck("se despacha por el ID EXACTO (no por el display)", "📤 Contable" in _cmp, True)
# ⚠️ Exactamente UNA puede quedarse sin comparar (la del `else`): dos significan que
# un ID cambió en un lado y no en el otro, y esa rama queda muerta (v449).
ck("exactamente una sub-sección cae al else", len([i for i in _ids if i not in _cmp]), 1)

# ═════ 9 · nada de alcanzar el interior de otro módulo ══════════════════════
print("\n[9] higiene")
_c = _fuente("core/contable.py")
ck("contable no usa el lector PRIVADO de expenses", "expenses._records" in _c, False)
ck("...usa el público", "expenses.list_group" in _c, True)
ck("expenses expone list_group", hasattr(expenses, "list_group"), True)
# ⚠️ `t()` formatea Y protege un placeholder mal escrito; hacerlo por fuera se salta
# esa guarda y una traducción con un typo dejaría la pantalla en blanco.
for f in ("core/contable.py", "core/contable_ui.py"):
    _mal = [ast.unparse(n)[:60] for n in ast.walk(ast.parse(_fuente(f)))
            if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "format"
            and isinstance(n.func.value, ast.Call)
            and getattr(n.func.value.func, "id", "") in ("t", "d")]
    ck(f"{f}: las variables van dentro de t()", _mal, [])

print("\n" + "=" * 72)
print(f"{n_ok} comprobaciones OK · {len(fallos)} fallos")
if fallos:
    for f in fallos:
        print("   -", f)
sys.exit(1 if fallos else 0)
