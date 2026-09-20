# -*- coding: utf-8 -*-
"""v495 · fase 2.3-C: los cobros vienen de Xero (dirección Xero → COPEX).

Lo que falla EN SILENCIO y hay que proteger:
  (a) una factura en BORRADOR en Xero tiene AmountPaid = 0: sincronizar desde ella
      pondría a CERO un cobro real apuntado en COPEX;
  (b) `AmountCredited` (notas de crédito, anticipos) NO es dinero recibido: sumarlo
      diría «cobrado» de algo que nadie pagó;
  (c) idempotencia: pulsar el botón dos veces no puede cobrar dos veces ni apuntar dos
      líneas en el historial;
  (d) un fallo de red no puede hacer que las facturas parezcan borradas en Xero;
  (e) una anulada en Xero (VOIDED/DELETED) no se toca aquí;
  (f) una escritura por lote, no una por factura (techo de 60 llamadas/min).
Todo EJECUTANDO con Xero y la hoja sustituidos: nunca sale nada a Internet.
"""
import ast
import io
import json
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


from core import invoices, xero as X, xero_ui                     # noqa: E402

CAB = ["ID", "Group", "ClientID", "ClientName", "Number", "Date", "ExpiryDate",
       "LinesJSON", "Subtotal", "TaxPct", "Tax", "Total", "Collected", "CollectionDate",
       "Status", "Note", "CreatedBy", "Created", "CollectionsJSON",
       "XeroInvoiceID", "XeroSentAt"]


class _WS:
    """Hoja falsa: cuenta lecturas y escrituras (una por lote es el requisito)."""

    def __init__(self, filas):
        self.filas = [list(CAB)] + [list(f) for f in filas]
        self.lecturas = 0
        self.escrituras = []

    def get_all_values(self):
        self.lecturas += 1
        return [list(r) for r in self.filas]

    def batch_update(self, rangos, value_input_option=None):
        self.escrituras.append(rangos)
        import re as _re
        for r in rangos:
            m = _re.match(r"([A-Z]+)(\d+)", r["range"])
            col = 0
            for ch in m.group(1):
                col = col * 26 + (ord(ch) - 64)
            self.filas[int(m.group(2)) - 1][col - 1] = r["values"][0][0]


def _fila(fid, numero, total, cobrado, xid, estado="emitida", hist=None):
    f = {"ID": fid, "Group": G, "Number": numero, "Total": total, "Collected": cobrado,
         "Status": estado, "XeroInvoiceID": xid,
         "CollectionsJSON": json.dumps(hist or [])}
    return [f.get(c, "") for c in CAB]


def _dicc(fila):
    return dict(zip(CAB, fila))


def _montar(filas, respuesta, status=200):
    """Sustituye la hoja y Xero. `respuesta` = lista de facturas como las devuelve Xero."""
    ws = _WS(filas)
    llamadas = []

    def _api(grupo, metodo, ruta, *, params=None, cuerpo=None, cabeceras=None, base=None):
        llamadas.append((metodo, ruta, dict(params or {})))
        if status != 200:
            return status, {"Message": "boom"}, {}
        pedidos = set((params or {}).get("IDs", "").split(","))
        return 200, {"Invoices": [i for i in respuesta if i["InvoiceID"] in pedidos]}, {}

    invoices._ws = lambda: (ws, "")
    invoices._invalidate = lambda: None
    # ⚠️ El `list_facturas` REAL no excluye las anuladas (lo comprobé): si el falso las
    # filtrara, estaría haciendo el trabajo del código y la guarda de xero.py quedaría
    # sin probar — un mock que hace lo que auditas garantiza un OK falso (v309/v310).
    invoices.list_facturas = lambda g, cliente_id=None: [_dicc(r) for r in ws.filas[1:]]
    X._api = _api
    return ws, llamadas


_orig = (invoices._ws, invoices._invalidate, invoices.list_facturas, X._api)
try:
    # ═════ 1 · el caso normal: Xero cobró, COPEX se pone al día ══════════════
    print("\n[1] lo cobrado en Xero entra en COPEX")
    ws, llam = _montar([_fila("FAC-0001", "0001", 1100, 0, "X1")],
                       [{"InvoiceID": "X1", "Status": "AUTHORISED", "AmountPaid": 1100,
                         "AmountCredited": 0, "FullyPaidOnDate": "/Date(1789603200000+0000)/"}])
    r = X.traer_cobros(G)
    ck("la factura se actualiza", [(x[1], x[2], x[3]) for x in r["actualizadas"]],
       [("0001", 0.0, 1100.0)])
    f = _dicc(ws.filas[1])
    ck("...y la hoja queda con lo que dice Xero", f["Collected"], "1100.0")
    ck("...con la fecha en que Xero la dio por pagada", f["CollectionDate"], "2026-09-17")
    ck("...y el historial apunta el movimiento con su origen",
       json.loads(f["CollectionsJSON"]), [{"fecha": "2026-09-17", "monto": 1100.0, "origen": "xero"}])
    ck("una lectura y UNA escritura para el lote", (ws.lecturas, len(ws.escrituras)), (1, 1))

    # (c) segunda pasada: nada que hacer
    r2 = X.traer_cobros(G)
    ck("pulsar otra vez no cobra dos veces (ni apunta otra línea)",
       (len(r2["actualizadas"]), [x[1] for x in r2["iguales"]], len(ws.escrituras)),
       (0, ["0001"], 1))
    ck("...y el historial sigue con UNA línea",
       len(json.loads(_dicc(ws.filas[1])["CollectionsJSON"])), 1)

    # ═════ 2 · el fallo silencioso: la factura sigue en borrador ══════════════
    print("\n[2] una factura en borrador en Xero NO pone a cero lo cobrado aquí")
    for est in ("DRAFT", "SUBMITTED"):
        ws, _l = _montar([_fila("FAC-0002", "0002", 500, 300, "X2")],
                         [{"InvoiceID": "X2", "Status": est, "AmountPaid": 0, "AmountCredited": 0}])
        r = X.traer_cobros(G)
        ck(f"{est}: se avisa y NO se toca el cobro de COPEX",
           ([x[1] for x in r["en_borrador"]], _dicc(ws.filas[1])["Collected"], len(ws.escrituras)),
           (["0002"], 300, 0))

    # ═════ 3 · anuladas en Xero, crédito, y Xero manda ═══════════════════════
    print("\n[3] anuladas, notas de crédito y descuadres")
    for est in ("VOIDED", "DELETED"):
        ws, _l = _montar([_fila("FAC-0003", "0003", 500, 300, "X3")],
                         [{"InvoiceID": "X3", "Status": est, "AmountPaid": 0, "AmountCredited": 0}])
        r = X.traer_cobros(G)
        ck(f"{est} en Xero: se avisa y no se cambia nada aquí",
           ([(x[1], x[2]) for x in r["muertas"]], len(ws.escrituras)), ([("0003", est)], 0))

    ws, _l = _montar([_fila("FAC-0004", "0004", 1000, 0, "X4")],
                     [{"InvoiceID": "X4", "Status": "PAID", "AmountPaid": 400,
                       "AmountCredited": 600, "FullyPaidOnDate": ""}])
    r = X.traer_cobros(G)
    ck("una nota de crédito NO se cuenta como cobrada, y se avisa",
       (_dicc(ws.filas[1])["Collected"], [(x[1], x[2]) for x in r["con_credito"]]),
       ("400.0", [("0004", 600.0)]))

    ws, _l = _montar([_fila("FAC-0005", "0005", 900, 900, "X5")],
                     [{"InvoiceID": "X5", "Status": "AUTHORISED", "AmountPaid": 200,
                       "AmountCredited": 0}])
    r = X.traer_cobros(G)
    ck("si en Xero hay MENOS cobrado, manda Xero y se avisa del antes/después",
       ([(x[2], x[3]) for x in r["actualizadas"]], _dicc(ws.filas[1])["Collected"]),
       ([(900.0, 200.0)], "200.0"))
    ck("...y el historial guarda el movimiento NEGATIVO",
       json.loads(_dicc(ws.filas[1])["CollectionsJSON"])[-1]["monto"], -700.0)

    # ═════ 4 · lo que no se consulta, y lo que no se acusa ═══════════════════
    print("\n[4] qué facturas se consultan y qué NO se afirma")
    ws, llam = _montar([_fila("FAC-0006", "0006", 100, 0, "X6"),
                        _fila("FAC-0007", "0007", 100, 0, ""),            # sin enviar
                        _fila("FAC-0008", "0008", 100, 0, "X8", "anulada")],
                       [{"InvoiceID": "X6", "Status": "PAID", "AmountPaid": 100,
                         "AmountCredited": 0}])
    r = X.traer_cobros(G)
    ck("solo se preguntan las que están en Xero y no están anuladas aquí",
       sorted(llam[0][2]["IDs"].split(",")), ["X6"])
    ck("...y se actualiza la que Xero cobró", [x[1] for x in r["actualizadas"]], ["0006"])

    ws, _l = _montar([_fila("FAC-0009", "0009", 100, 0, "X9")], [])       # Xero no la devuelve
    r = X.traer_cobros(G)
    ck("una que Xero no devuelve se dice (¿borrada allí?)",
       [x[1] for x in r["no_encontradas"]], ["0009"])

    ws, _l = _montar([_fila("FAC-0010", "0010", 100, 50, "XA")], [], status=401)
    r = X.traer_cobros(G)
    ck("un fallo de red NO acusa de borradas ni escribe",
       (bool(r["errores"]), r["no_encontradas"], len(ws.escrituras)), (True, [], 0))

    # (f) por lotes
    filas = [_fila(f"FAC-1{i:03d}", f"1{i:03d}", 10, 0, f"Y{i}") for i in range(45)]
    ws, llam = _montar(filas, [{"InvoiceID": f"Y{i}", "Status": "PAID", "AmountPaid": 10,
                                "AmountCredited": 0} for i in range(45)])
    r = X.traer_cobros(G)
    ck("45 facturas se preguntan en 2 llamadas y se escriben en UNA",
       (len(llam), len(ws.escrituras), len(r["actualizadas"])), (2, 1, 45))

    # ═════ 5 · sincronizar_cobros a solas ════════════════════════════════════
    print("\n[5] sincronizar_cobros: guardas propias")
    ws = _WS([_fila("FAC-0011", "0011", 100, 0, "XB")])
    invoices._ws = lambda: (ws, "")
    ok_, r = invoices.sincronizar_cobros({}, "2026-09-16")
    ck("sin cambios no lee ni escribe nada", (ok_, r, ws.lecturas), (True, {"cambiadas": [], "iguales": []}, 0))
    ws2 = _WS([_fila("FAC-0011", "0011", 100, 0, "XB")])
    ws2.filas[0] = [c for c in CAB if c != "CollectionsJSON"]
    invoices._ws = lambda: (ws2, "")
    ok_, msg = invoices.sincronizar_cobros({"FAC-0011": {"cobrado": 50, "fecha": "2026-09-16"}}, "2026-09-16")
    ck("una hoja sin la columna del historial da error en vez de escribir al lado",
       (ok_, len(ws2.escrituras)), (False, 0))
finally:
    (invoices._ws, invoices._invalidate, invoices.list_facturas, X._api) = _orig

# ═════ 6 · una sola definición del parser de fechas ══════════════════════════
print("\n[6] el parser de fechas de Xero, una sola definición")
import datetime as _d                                            # noqa: E402
from core import xero_nomina as XN                               # noqa: E402
ck("xero.de_fecha lee el formato de Xero", X.de_fecha("/Date(1573171200000+0000)/"), _d.date(2019, 11, 8))
ck("...y también YYYY-MM-DD", X.de_fecha("2026-09-16"), _d.date(2026, 9, 16))
ck("...y basura da None", X.de_fecha("no"), None)
# ⚠️ Por la LLAMADA y no por el texto: «de_fecha» sale también en el comentario de la
# función, así que buscarlo como subcadena aprobaba una copia del parser (trampa nº2).
_de_ms = next(n for n in ast.walk(ast.parse(_fuente("core/xero_nomina.py")))
              if isinstance(n, ast.FunctionDef) and n.name == "de_ms")
ck("xero_nomina.de_ms DELEGA (no hay dos parsers)",
   (any(isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "de_fecha"
        for n in ast.walk(_de_ms)),
    any(isinstance(n, ast.Attribute) and getattr(n, "attr", "") in ("search", "fromtimestamp")
        for n in ast.walk(_de_ms))), (True, False))
ck("...y sigue dando lo mismo", XN.de_ms("/Date(1573171200000+0000)/"), _d.date(2019, 11, 8))

# ═════ 7 · la pantalla ═══════════════════════════════════════════════════════
print("\n[7] la pantalla: el botón y el resumen")
_tr = ast.parse(_fuente("core/xero_ui.py"))
_fns = {n.name: n for n in ast.walk(_tr) if isinstance(n, ast.FunctionDef)}
ck("existe el resumen de cobros", "_flash_cobros" in _fns, True)
ck("...y `theme` se importa DENTRO (en este módulo es local, v423)",
   any(isinstance(n, ast.ImportFrom) and any(a.asname == "T" for a in n.names)
       for n in ast.walk(_fns["_flash_cobros"])), True)
_conx = ast.unparse(_fns["render_conexion"])
ck("el botón existe y llama a traer_cobros",
   ("xero_traer_cobros" in _conx, "traer_cobros" in _conx), (True, True))
ck("...y la pantalla cuenta cada caso",
   all(k in ast.unparse(_fns["_flash_cobros"])
       for k in ("actualizadas", "iguales", "en_borrador", "con_credito", "muertas",
                 "no_encontradas", "errores")), True)

_msgs = []
_origf = (xero_ui.flash.exito, xero_ui.flash.info, xero_ui.flash.aviso, xero_ui.flash.error)
try:
    xero_ui.flash.exito = lambda m: _msgs.append(("exito", m))
    xero_ui.flash.info = lambda m: _msgs.append(("info", m))
    xero_ui.flash.aviso = lambda m: _msgs.append(("aviso", m))
    xero_ui.flash.error = lambda m: _msgs.append(("error", m))
    xero_ui._flash_cobros({"actualizadas": [("FAC-1", "0001", 0.0, 1100.0)],
                           "iguales": [("FAC-2", "0002")],
                           "en_borrador": [("FAC-3", "0003")],
                           "muertas": [("FAC-4", "0004", "VOIDED")],
                           "con_credito": [("FAC-5", "0005", 600.0)],
                           "no_encontradas": [("FAC-6", "0006")],
                           "errores": ["HTTP 401"], "avisos": ["ojo"]})
finally:
    (xero_ui.flash.exito, xero_ui.flash.info, xero_ui.flash.aviso, xero_ui.flash.error) = _origf
ck("el resumen EJECUTADO dice los siete casos", len(_msgs), 8)
ck("...con el importe formateado y escapado (v309)",
   any("1,100" in m and "\\$" in m for _t, m in _msgs), True)
ck("...y el borrador explica que así no llegará cobro",
   any("draft" in m.lower() and "no payment" in m.lower() for _t, m in _msgs), True)

print("\n" + "=" * 70)
print(f"{n_ok + len(fallos)} comprobaciones — " + ("TODO OK" if not fallos else "HAY FALLOS"))
sys.exit(1 if fallos else 0)
