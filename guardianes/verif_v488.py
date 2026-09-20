# -*- coding: utf-8 -*-
"""v488 · Conexión con Xero por API (fase 2.3-A): conectar y mandar facturas.

Lo que hay que proteger, y por qué cada cosa falla EN SILENCIO:

  (a) UNA definición de «factura repartida en líneas» para el CSV y la API. El CSV
      tiene que salir IDÉNTICO al de antes — ⚠️ el oráculo va ESCRITO aquí (huellas
      sacadas de la versión anterior), no de `git show HEAD`, que tras el commit
      tendría el código nuevo y dejaría el chequeo vacío (lección v484);
  (b) los tokens: cifrados, en el MAESTRO, nunca en una caché compartida ni en el log;
  (c) el `state` firmado: una autorización de otro usuario o empresa no se canjea;
  (d) el token de refresco ROTA: dos refrescos a la vez perderían una rotación, y un
      fallo al guardarlo no puede tirar la conexión;
  (e) no duplicar en Xero: sin poder comprobar el número, NO se envía;
  (f) lo que llega a Xero suma al centavo lo mismo que la factura emitida.
Todo lo que habla con Xero se EJECUTA con la red sustituida: nunca sale nada a Internet.
"""
import ast
import base64
import datetime as dt
import hashlib
import io
import json
import logging
import os
import re
import sys
import threading
import time

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)                      # los secrets se buscan desde el CWD (trampa n19)
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


def _func(arbol, nombre):
    for n in ast.walk(arbol):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == nombre:
            return n
    return None


from cryptography.fernet import Fernet                            # noqa: E402

from core import contable, invoices, timeclock                    # noqa: E402
from core import xero as X                                        # noqa: E402
from core import xero_ui as XU                                    # noqa: E402

# ═════ captura del log: ningún secreto puede acabar ahí ═════════════════════
_LOG = io.StringIO()
_manejador = logging.StreamHandler(_LOG)
_manejador.setLevel(logging.DEBUG)
logging.getLogger().addHandler(_manejador)
logging.getLogger().setLevel(logging.DEBUG)

CLAVE = Fernet.generate_key().decode()
SECRETOS = {"XERO_CLIENT_ID": "CID-prueba", "XERO_CLIENT_SECRET": "SECRETO-no-debe-salir",
            "XERO_TOKEN_KEY": CLAVE, "APP_URL": "https://copex.example.app"}
_secret_real = X._secret
X._secret = lambda n: SECRETOS.get(n, "")


# ═════ bancos: hoja y red falsas ═════════════════════════════════════════════
def _a1(celda):
    m = re.match(r"([A-Z]+)(\d+)$", celda)
    col = 0
    for ch in m.group(1):
        col = col * 26 + (ord(ch) - 64)
    return int(m.group(2)), col


class HojaFalsa:
    def __init__(self, cabecera, filas=None):
        self.vals = [list(cabecera)] + [list(f) for f in (filas or [])]
        self.lecturas = 0
        self.escrituras = 0
        self.falla_escribir = False

    def get_all_values(self):
        self.lecturas += 1
        return [list(r) for r in self.vals]

    def append_row(self, fila, value_input_option=None):
        self.escrituras += 1
        self.vals.append([str(x) for x in fila])

    def batch_update(self, rangos, value_input_option=None):
        if self.falla_escribir:
            raise RuntimeError("fallo de escritura simulado")
        self.escrituras += 1
        for r in rangos:
            fila, col = _a1(r["range"])
            while len(self.vals) < fila:
                self.vals.append([])
            f = self.vals[fila - 1]
            while len(f) < col:
                f.append("")
            f[col - 1] = r["values"][0][0]

    def fila(self, n):
        return dict(zip(self.vals[0], self.vals[n - 1] + [""] * len(self.vals[0])))


class Resp:
    def __init__(self, status, js=None, headers=None):
        self.status_code, self._js, self.headers = status, js, headers or {}
        self.text = json.dumps(js) if js is not None else ""

    def json(self):
        if self._js is None:
            raise ValueError("sin json")
        return self._js


LLAMADAS = []
RUTAS = []          # [(metodo, fragmento_url, funcion(kw) -> Resp)]


def http_falso(metodo, url, **kw):
    LLAMADAS.append((metodo, url, kw))
    for m, frag, fn in RUTAS:
        if m == metodo and frag in url:
            return fn(kw)
    return Resp(599, {"Message": "ruta no simulada"})


X._http = http_falso


def jwt(claims):
    cuerpo = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    return f"cabecera.{cuerpo}.firma"


def _reset(rutas=()):
    LLAMADAS.clear()
    RUTAS[:] = list(rutas)
    X._VIVOS.clear()
    X._PENDIENTES.clear()


# ═════ 1 · estructura: global, cabeceras, scopes, dependencia ═══════════════
print("\n[1] estructura")
ck("la pestaña de conexiones es GLOBAL (vive en el maestro)",
   "xeroconnections" in timeclock.SHEETS_GLOBALES, True)
try:
    _sid_x = timeclock.sheet_id_para(X.SHEET)
    _sid_login = timeclock.sheet_id_para("Login")
    _sid_proj = timeclock.sheet_id_para("Projects")
    # ⚠️ Con la sesión de un INQUILINO con libro propio: con el propietario (sin grupo)
    # todo cae al maestro y el chequeo pasaría sin significar nada (v473).
    ck("…y con sesión de inquilino se resuelve al MAESTRO, no a su libro",
       (_sid_x == _sid_login, _sid_x != _sid_proj), (True, True))
except Exception as e:
    fallo("no se pudo resolver el libro de la conexión", repr(e))

_H = invoices.FACTURAS_HEADERS
ck("las columnas de Xero van AL FINAL de Invoices", _H[-2:], ["XeroInvoiceID", "XeroSentAt"])
ck("…y detrás de TODAS las históricas (nada se cuela delante, v363)", _H[:19], [
    "ID", "Group", "ClientID", "ClientName", "Number", "Date", "ExpiryDate", "LinesJSON",
    "Subtotal", "TaxPct", "Tax", "Total", "Collected", "CollectionDate", "Status", "Note",
    "CreatedBy", "Created", "CollectionsJSON"])
_arb_inv = ast.parse(_fuente("core/invoices.py"))
_cf = _func(_arb_inv, "create_factura")
_filas = [n.value for n in ast.walk(_cf) if isinstance(n, ast.Assign)
          and any(isinstance(tg, ast.Name) and tg.id == "row" for tg in n.targets)
          and isinstance(n.value, ast.List)]
ck("la fila posicional de create_factura casa con la cabecera",
   bool(_filas) and len(_filas[0].elts) == len(_H), True)
ck("scopes GRANULARES: facturas con accounting.invoices",
   "accounting.invoices" in X.SCOPES and "accounting.transactions" not in X.SCOPES, True)
ck("offline_access (sin él no hay token de refresco)", "offline_access" in X.SCOPES, True)
ck("los permisos de nómina se piden desde el principio (decisión del usuario)",
   {"payroll.employees", "payroll.timesheets", "payroll.settings"} <= set(X.SCOPES), True)
ck("cryptography fijada en requirements",
   bool(re.search(r"^cryptography>=\d+,<\d+", _fuente("requirements.txt"), re.M)), True)
_cab_x = X.HEADERS
ck("la pestaña de conexiones no tiene columnas duplicadas", len(_cab_x), len(set(_cab_x)))

# ═════ 2 · el CSV sale idéntico (oráculo de la versión anterior) ════════════
print("\n[2] CSV de ventas: una definición y el mismo resultado de antes")
L = lambda xs: json.dumps(xs)  # noqa: E731
FACT = [
    {"ID": "FAC-0001", "Group": "g", "ClientID": "CLI-1", "ClientName": "Acme Pty",
     "Number": "0003", "Date": "2026-09-01", "ExpiryDate": "2026-09-15",
     "LinesJSON": L([{"concepto": "A", "importe": 33.33, "proyecto_id": "PRJ-1"},
                     {"concepto": "B", "importe": 33.33, "proyecto_id": "PRJ-2"},
                     {"concepto": "", "importe": 33.34, "proyecto_id": ""}]),
     "TaxPct": "10", "Tax": "10.00", "Status": "emitida"},
    {"ID": "FAC-0002", "Group": "g", "ClientID": "", "ClientName": "",
     "Number": "0001", "Date": "01/09/2026", "ExpiryDate": "",
     "LinesJSON": L([{"concepto": "Sin cliente ni vence", "importe": "1,234.56",
                      "proyecto_id": "PRJ-LARGO"}]),
     "TaxPct": "0", "Tax": "0", "Status": "emitida"},
    {"ID": "FAC-0003", "Group": "g", "ClientID": "CLI-2", "ClientName": "Anulada",
     "Number": "0002", "Date": "2026-09-02", "ExpiryDate": "2026-09-03",
     "LinesJSON": L([{"concepto": "x", "importe": 5}]), "TaxPct": "10", "Tax": "0.5",
     "Status": "anulada"},
    {"ID": "FAC-0004", "Group": "g", "ClientID": "CLI-2", "ClientName": "",
     "Number": "0004", "Date": "2026-09-03", "ExpiryDate": "2026-09-30",
     "LinesJSON": "[]", "TaxPct": "10", "Tax": "0", "Status": "emitida"},
    {"ID": "FAC-0005", "Group": "g", "ClientID": "CLI-2", "ClientName": "",
     "Number": "0005", "Date": "2026-09-04", "ExpiryDate": "fecha rara",
     "LinesJSON": L([{"concepto": "Z" * 300, "importe": 100, "proyecto_id": "PRJ-1"},
                     {"concepto": "neg", "importe": -20, "proyecto_id": "PRJ-2"}]),
     "TaxPct": "10", "Tax": "8.00", "Status": "Emitida"},
    {"ID": "FAC-0006", "Group": "g", "ClientID": "CLI-1", "ClientName": "Acme Pty",
     "Number": "0006", "Date": "2026-10-04", "ExpiryDate": "2026-10-18",
     "LinesJSON": L([{"concepto": "fuera de rango", "importe": 50}]),
     "TaxPct": "10", "Tax": "5", "Status": "void"},
]
CLI = [{"ID": "CLI-1", "Name": "Acme Pty", "Email": "a@example.com", "Address": "1 St"},
       {"ID": "CLI-2", "Name": "Beta, \"Ltd\"", "Email": "", "Address": "2\nSt"}]
ETQ = {"PRJ-1": "Torre Norte", "PRJ-2": "Torre Norte (PRJ-2)", "PRJ-LARGO": "X" * 60}
ORACULO = {
    ("xero", True): ("568b3696907e9d957d91a7f013acc59cd757584d27060c861bedb4b5f667c514", 6, 3, 3),
    ("xero", False): ("e917ebc5e6840a68b947b408fa4d5ad1303681e58c72283ba43591a1a257ec2b", 6, 3, 2),
    ("myob", True): ("893232336d52b45a0e863df59b6664405ea164b9615af80c75a1afe964cd8a5e", 6, 3, 3),
    ("myob", False): ("449820d49c60f6aa410c2c4d8628ea0fbc54c949925281ae187fb6be58b1f646", 6, 3, 2),
}
_orig = (contable.invoices.list_facturas, contable.clientes.list_clientes,
         contable.auth.group_text_setting, contable._etiquetas)
try:
    contable.invoices.list_facturas = lambda grupo=None, cliente_id=None: list(FACT)
    contable.clientes.list_clientes = lambda grupo, incluir_inactivos=False: list(CLI)
    contable._etiquetas = lambda g: dict(ETQ)
    for (perfil, seg), (huella, filas, docs, navisos) in ORACULO.items():
        _txt = {"AccountingJSON": json.dumps({"seguimiento": seg}), "ABN": ""}
        contable.auth.group_text_setting = (lambda g, field, default="", _t=_txt:
                                            _t.get(field, default) or default)
        r = contable.csv_ventas("g", perfil)
        ck(f"CSV {perfil} seguimiento={seg} idéntico al de la versión anterior",
           (hashlib.sha256(r["csv"].encode()).hexdigest(), r["filas"], r["documentos"],
            len(r["avisos"])), (huella, filas, docs, navisos))
finally:
    (contable.invoices.list_facturas, contable.clientes.list_clientes,
     contable.auth.group_text_setting, contable._etiquetas) = _orig
_arb_c = ast.parse(_fuente("core/contable.py"))
_llamadas_doc = [n for n in ast.walk(_func(_arb_c, "csv_ventas")) if isinstance(n, ast.Call)
                 and getattr(n.func, "id", "") == "documento_venta"]
ck("csv_ventas usa documento_venta (una definición)", len(_llamadas_doc), 1)
ck("…y ya no reparte el impuesto por su cuenta",
   any(getattr(n.func, "id", "") == "reparte_impuesto"
       for n in ast.walk(_func(_arb_c, "csv_ventas")) if isinstance(n, ast.Call)), False)
_arb_x = ast.parse(_fuente("core/xero.py"))
ck("el envío a Xero usa la MISMA definición",
   any(isinstance(n, ast.Attribute) and n.attr == "documento_venta"
       for n in ast.walk(_func(_arb_x, "enviar_facturas"))), True)

# ═════ 3 · state firmado y cifrado ═══════════════════════════════════════════
print("\n[3] state firmado y token cifrado")
s1 = X.firma_state(G, "admin")
d1, m1 = X.verifica_state(s1)
ck("un state recién firmado se verifica", (bool(d1), m1, d1["g"], d1["u"]), (True, "", G, "admin"))
_carga, _firma = s1.split(".")
_otro = base64.urlsafe_b64encode(json.dumps({"g": "OTRA", "u": "admin", "ts": int(time.time()),
                                             "n": "x"}, separators=(",", ":")).encode()
                                 ).decode().rstrip("=")
ck("cambiar la empresa dentro del state rompe la firma",
   X.verifica_state(f"{_otro}.{_firma}")[1], "firma")
ck("un state de hace 31 min está caducado",
   X.verifica_state(X.firma_state(G, "admin", ahora=time.time() - 31 * 60))[1], "caducado")
ck("basura no se acepta", X.verifica_state("no-es-un-state")[1], "firma")
SECRETOS["XERO_TOKEN_KEY"] = Fernet.generate_key().decode()
ck("con OTRA clave el state anterior no vale", X.verifica_state(s1)[1], "firma")
SECRETOS["XERO_TOKEN_KEY"] = CLAVE
_url = X.url_autorizacion(G, "admin")
ck("la URL de autorización pide los scopes separados por %20",
   "scope=offline_access%20accounting.invoices" in _url, True)
ck("…y la redirect URI exacta derivada de APP_URL",
   "redirect_uri=https%3A%2F%2Fcopex.example.app%2F" in _url, True)
_paq = {"a": "ACCESO-secreto", "r": "REFRESCO-secreto", "e": 1}
_cif = X._cifra(_paq)
ck("el paquete del token se cifra (no aparece en claro)",
   "ACCESO-secreto" not in _cif and "REFRESCO-secreto" not in _cif, True)
ck("…y se descifra igual", X._descifra(_cif), _paq)
SECRETOS["XERO_TOKEN_KEY"] = Fernet.generate_key().decode()
ck("con la clave cambiada no se descifra (None, sin excepción)", X._descifra(_cif), None)
SECRETOS["XERO_TOKEN_KEY"] = "no-es-una-clave"
_c = X.configuracion()
ck("una clave inválida se DICE en la configuración", (_c["ok"], bool(_c["problemas"])), (False, True))
SECRETOS["XERO_TOKEN_KEY"] = CLAVE
_sin = dict(SECRETOS)
SECRETOS.clear()
_c = X.configuracion()
ck("sin secretos se listan los que faltan (incluida la redirect URI)",
   set(_c["faltan"]), {"XERO_CLIENT_ID", "XERO_CLIENT_SECRET", "XERO_TOKEN_KEY", "XERO_REDIRECT_URI"})
SECRETOS.update(_sin)
ck("con todo configurado, ok", X.configuracion()["ok"], True)

# ═════ 4 · conectar ══════════════════════════════════════════════════════════
print("\n[4] completar la conexión")
HOJA = HojaFalsa(X.HEADERS)
_EXISTE = {"si": False}


def _ws_falso(crear=True):
    if crear:
        _EXISTE["si"] = True
        return HOJA
    return HOJA if _EXISTE["si"] else None


X._ws = _ws_falso


def _token_ok(access, refresh, **extra):
    def fn(kw):
        return Resp(200, dict({"access_token": access, "refresh_token": refresh,
                               "expires_in": 1800, "token_type": "Bearer"}, **extra))
    return fn


ACC1 = jwt({"authentication_event_id": "evt-1", "sub": "u"})
_reset([
    ("POST", "identity.xero.com/connect/token", _token_ok(ACC1, "R1")),
    ("GET", "api.xero.com/Connections", lambda kw: Resp(200, [
        {"id": "con-1", "tenantId": "ten-1", "tenantType": "ORGANISATION",
         "tenantName": "Demo Company (AU)", "updatedDateUtc": "2026-09-15T01:00:00"}])),
    ("GET", "/Organisation", lambda kw: Resp(200, {"Organisations": [{"ShortCode": "!abc1"}]})),
])
okc, msg, avisos = X.completar_conexion(G, "admin", "CODIGO-1", X.firma_state(G, "admin"))
ck("la conexión se completa", okc, True)
_post = [c for c in LLAMADAS if c[0] == "POST"][0]
ck("el canje lleva code, grant y la redirect URI exacta",
   (_post[2]["data"]["grant_type"], _post[2]["data"]["code"], _post[2]["data"]["redirect_uri"]),
   ("authorization_code", "CODIGO-1", "https://copex.example.app/"))
ck("…con Basic auth (client_id:secret)",
   _post[2]["headers"]["Authorization"],
   "Basic " + base64.b64encode(b"CID-prueba:SECRETO-no-debe-salir").decode())
_get_con = [c for c in LLAMADAS if "Connections" in c[1]][0]
ck("las conexiones se filtran por el evento de ESTA autorización",
   _get_con[2]["params"], {"authEventId": "evt-1"})
_f2 = HOJA.fila(2)
ck("se guarda organización, código corto, conexión y estado",
   (_f2["Group"], _f2["TenantID"], _f2["TenantName"], _f2["ShortCode"], _f2["ConnectionID"],
    _f2["Status"], _f2["ConnectedBy"]),
   (G, "ten-1", "Demo Company (AU)", "!abc1", "con-1", X.CONECTADA, "admin"))
ck("el token se guarda CIFRADO", ACC1 not in _f2["TokenEnc"] and "R1" not in _f2["TokenEnc"]
   and X._descifra(_f2["TokenEnc"])["r"] == "R1", True)
_reset([("POST", "connect/token", _token_ok(ACC1, "R1"))])
okx, msgx, _a = X.completar_conexion(G, "admin", "CODIGO-2", X.firma_state(G, "otro-usuario"))
ck("un state de OTRO usuario no se canjea… y no llama a Xero", (okx, len(LLAMADAS)), (False, 0))
okx, msgx, _a = X.completar_conexion(G, "admin", "CODIGO-2", X.firma_state("otra-empresa", "admin"))
ck("…ni uno de OTRA empresa", (okx, len(LLAMADAS)), (False, 0))
ACC2 = jwt({"authentication_event_id": "evt-2"})
_reset([
    ("POST", "connect/token", _token_ok(ACC2, "R2")),
    ("GET", "Connections", lambda kw: Resp(200, [
        {"id": "con-2", "tenantId": "ten-2", "tenantType": "ORGANISATION",
         "tenantName": "Otra Org"}])),
    ("GET", "/Organisation", lambda kw: Resp(200, {"Organisations": [{"ShortCode": "!zz"}]})),
])
okc2, _m, avisos2 = X.completar_conexion(G, "admin", "CODIGO-3", X.firma_state(G, "admin"))
ck("reconectar a otra organización ACTUALIZA la fila (no duplica)",
   (okc2, len(HOJA.vals), HOJA.fila(2)["TenantID"]), (True, 2, "ten-2"))
ck("…y avisa de que la anterior puede seguir conectada en Xero", bool(avisos2), True)

# ═════ 5 · token: refresco, rotación, cerrojo ═══════════════════════════════
print("\n[5] token vigente, refresco y rotación")


def _pon_token(access, refresh, expira):
    HOJA.vals[1][X.HEADERS.index("TokenEnc")] = X._cifra({"a": access, "r": refresh, "e": expira})
    HOJA.vals[1][X.HEADERS.index("Status")] = X.CONECTADA


_pon_token("VIGENTE", "RV", time.time() + 900)
_reset()
okt, tok = X._token(G)
ck("con el token vigente NO se llama a Xero", (okt, tok["access"], len(LLAMADAS)), (True, "VIGENTE", 0))
_lect = HOJA.lecturas
X._token(G)
ck("la segunda llamada sale de memoria (0 lecturas de la hoja)", HOJA.lecturas, _lect)

_pon_token("CADUCADO", "R-VIEJO", time.time() - 10)
_reset([("POST", "connect/token", _token_ok("NUEVO", "R-NUEVO"))])
okt, tok = X._token(G)
_ref = [c for c in LLAMADAS if c[0] == "POST"]
ck("caducado → UN refresco con el token de refresco viejo",
   (okt, tok["access"], len(_ref), _ref[0][2]["data"]["refresh_token"],
    _ref[0][2]["data"]["grant_type"]), (True, "NUEVO", 1, "R-VIEJO", "refresh_token"))
ck("…y el token ROTADO se guarda cifrado en la hoja",
   X._descifra(HOJA.fila(2)["TokenEnc"])["r"], "R-NUEVO")

_pon_token("CADUCADO", "R-CONC", time.time() - 10)
_contador = {"n": 0}
_puerta = threading.Event()


def _refresco_lento(kw):
    _contador["n"] += 1
    _puerta.wait(0.3)
    return Resp(200, {"access_token": "CONC", "refresh_token": "R-CONC2", "expires_in": 1800})


_reset([("POST", "connect/token", _refresco_lento)])
_res = []
hilos = [threading.Thread(target=lambda: _res.append(X._token(G))) for _ in range(4)]
for h in hilos:
    h.start()
for h in hilos:
    h.join()
ck("4 sesiones a la vez con el token caducado → UN solo refresco (cerrojo)",
   (_contador["n"], all(r[0] for r in _res)), (1, True))

_pon_token("CADUCADO", "R-REVOCADO", time.time() - 10)
_reset([("POST", "connect/token", lambda kw: Resp(400, {"error": "invalid_grant"}))])
okt, msg = X._token(G)
ck("invalid_grant → no conectada y la conexión queda marcada CADUCADA",
   (okt, HOJA.fila(2)["Status"]), (False, X.CADUCADA))

_pon_token("CADUCADO", "R-A", time.time() - 10)
HOJA.falla_escribir = True
_reset([("POST", "connect/token", _token_ok("ROTADO", "R-B"))])
okt, tok = X._token(G)
ck("si falla GUARDAR el token rotado, la llamada sigue y queda PENDIENTE en memoria",
   (okt, bool(X._PENDIENTES.get(G))), (True, True))
HOJA.falla_escribir = False
X._VIVOS.clear()
LLAMADAS.clear()
okt, tok = X._token(G)
ck("…la siguiente usa el pendiente SIN volver a refrescar y lo guarda",
   (okt, len(LLAMADAS), X._descifra(HOJA.fila(2)["TokenEnc"])["r"], bool(X._PENDIENTES.get(G))),
   (True, 0, "R-B", False))

_pon_token("VIGENTE401", "R-401", time.time() + 900)
_seq = {"n": 0}


def _dos_intentos(kw):
    _seq["n"] += 1
    return Resp(401, {"Detail": "token revocado"}) if _seq["n"] == 1 else Resp(200, {"Invoices": []})


_reset([("GET", "/Invoices", _dos_intentos),
        ("POST", "connect/token", _token_ok("TRAS401", "R-402"))])
st_, js, _h = X._api(G, "GET", "/Invoices")
ck("un 401 fuerza UN refresco y reintenta una vez",
   (st_, _seq["n"], len([c for c in LLAMADAS if c[0] == "POST"])), (200, 2, 1))
_reset([("GET", "/Invoices", lambda kw: Resp(401, {"Detail": "no"})),
        ("POST", "connect/token", _token_ok("OTRO", "R-403"))])
st_, js, _h = X._api(G, "GET", "/Invoices")
ck("…dos 401 seguidos ya se devuelven (no bucle)",
   (st_, len([c for c in LLAMADAS if c[0] == "GET"])), (401, 2))

# ═════ 6 · mandar facturas ═══════════════════════════════════════════════════
print("\n[6] enviar facturas")
_pon_token("ENVIO", "R-ENV", time.time() + 900)
HOJA.vals[1][X.HEADERS.index("TenantID")] = "ten-2"
FACTS = {
    "FAC-A": {"ID": "FAC-A", "Group": G, "ClientID": "CLI-1", "ClientName": "Acme Pty",
              "Number": "0101", "Date": "2026-09-10", "ExpiryDate": "2026-09-24",
              "LinesJSON": L([{"concepto": "Instalación", "importe": 33.33, "proyecto_id": "PRJ-1"},
                              {"concepto": "Material", "importe": 33.33, "proyecto_id": "PRJ-2"},
                              {"concepto": "Extra", "importe": 33.34, "proyecto_id": ""}]),
              "Subtotal": "100.00", "TaxPct": "10", "Tax": "10.00", "Total": "110.00",
              "Status": "emitida"},
    "FAC-B": {"ID": "FAC-B", "Group": G, "ClientID": "CLI-1", "ClientName": "Acme Pty",
              "Number": "0102", "Date": "2026-09-11", "ExpiryDate": "2026-09-25",
              "LinesJSON": L([{"concepto": "Ya en Xero", "importe": 50}]),
              "TaxPct": "10", "Tax": "5", "Status": "emitida"},
    "FAC-C": {"ID": "FAC-C", "Group": G, "ClientID": "CLI-1", "ClientName": "Acme Pty",
              "Number": "0103", "Date": "2026-09-12", "ExpiryDate": "",
              "LinesJSON": L([{"concepto": "GST raro", "importe": 50}]),
              "TaxPct": "15", "Tax": "7.5", "Status": "emitida"},
    "FAC-D": {"ID": "FAC-D", "Group": "otra-empresa", "ClientID": "", "ClientName": "Ajena",
              "Number": "0104", "Date": "2026-09-12", "LinesJSON": L([{"concepto": "x", "importe": 1}]),
              "TaxPct": "0", "Tax": "0", "Status": "emitida"},
    "FAC-E": {"ID": "FAC-E", "Group": G, "ClientName": "Acme Pty", "Number": "0105",
              "Date": "2026-09-12", "LinesJSON": L([{"concepto": "x", "importe": 1}]),
              "TaxPct": "0", "Tax": "0", "Status": "emitida", "XeroInvoiceID": "ya-tiene"},
}
MARCAS = []
_orig6 = (invoices.get_factura, invoices.marcar_xero, contable.mapa, contable._etiquetas,
          contable.fichas_clientes)
invoices.get_factura = lambda fid: dict(FACTS.get(fid, {}))
invoices.marcar_xero = lambda marcas, cuando: (MARCAS.append(dict(marcas)) or (True, ""))
_CFG = {"cuentas": {"xero": {contable.VENTAS: "200"}}, "seguimiento": True,
        "categoria_seguimiento": "Project", "xero_estado": "DRAFT"}
contable.mapa = lambda g: json.loads(json.dumps(_CFG))
contable._etiquetas = lambda g: {"PRJ-1": "Torre Norte", "PRJ-2": "Torre Sur"}
contable.fichas_clientes = lambda g: {"CLI-1": {"Name": "Acme Pty"}}

PUTS = []


def _put_invoices(kw):
    PUTS.append(kw)
    inv = kw["json"]["Invoices"]
    return Resp(200, {"Invoices": [dict(i, InvoiceID=f"XID-{i['InvoiceNumber']}", HasErrors=False,
                                        ValidationErrors=[]) for i in inv]})


OPCIONES_CREADAS = []


def _crear_opcion(kw):
    OPCIONES_CREADAS.append(kw["json"]["Name"])
    return Resp(200, {"Options": [{"Name": kw["json"]["Name"]}]})


RUTAS_ENVIO = [
    ("GET", "/Invoices", lambda kw: Resp(200, {"Invoices": [
        {"Type": "ACCREC", "InvoiceNumber": "0102", "InvoiceID": "XID-EXISTENTE", "Status": "AUTHORISED"},
        {"Type": "ACCREC", "InvoiceNumber": "0101", "InvoiceID": "XID-BORRADA", "Status": "DELETED"},
        {"Type": "ACCPAY", "InvoiceNumber": "0101", "InvoiceID": "XID-FACTURA-PROVEEDOR",
         "Status": "AUTHORISED"}]})),
    ("GET", "/TrackingCategories", lambda kw: Resp(200, {"TrackingCategories": [
        {"Name": "project", "TrackingCategoryID": "TC-1", "Status": "ACTIVE",
         "Options": [{"Name": "TORRE NORTE", "Status": "ACTIVE"}]}]})),
    ("PUT", "/TrackingCategories/TC-1/Options", _crear_opcion),
    ("PUT", "/Invoices", _put_invoices),
]
_reset(RUTAS_ENVIO)
res = X.enviar_facturas(G, ["FAC-A", "FAC-B", "FAC-C", "FAC-D", "FAC-E"])
ck("A se envía", [x[0] for x in res["enviadas"]], ["FAC-A"])
ck("B ya estaba en Xero con ese número: se ENLAZA, no se duplica",
   [(x[0], x[2]) for x in res["vinculadas"]], [("FAC-B", "XID-EXISTENTE")])
_err = {x[0]: x[2] for x in res["errores"]}
ck("C (15 %) no se manda: Xero es GST 10 %", "FAC-C" in _err and any("10%" in m for m in _err["FAC-C"]), True)
ck("D es de otra empresa: «no encontrada» (el cerrojo de v351 también aquí)", "FAC-D" in _err, True)
ck("E ya tiene ID de Xero: no se reenvía", "FAC-E" in _err, True)
_get_inv = [c for c in LLAMADAS if c[0] == "GET" and c[1].endswith("/Invoices")][0]
ck("la comprobación previa busca SOLO los números que se van a mandar (A y B)",
   _get_inv[2]["params"], {"InvoiceNumbers": "0101,0102"})
ck("…una factura BORRADA o de PROVEEDOR con el mismo número no bloquea", "FAC-A" in [x[0] for x in res["enviadas"]], True)
ck("se crea en Xero SOLO la opción de seguimiento que falta (y no la categoría)",
   OPCIONES_CREADAS, ["Torre Sur"])
ck("un solo PUT de facturas", len(PUTS), 1)
_put = PUTS[0]
_inv = _put["json"]["Invoices"]
ck("el PUT lleva solo A", [i["InvoiceNumber"] for i in _inv], ["0101"])
ck("…con summarizeErrors=false y clave de idempotencia",
   (_put["params"], _put["headers"].get("Idempotency-Key", "").startswith("copex-"),
    _put["headers"]["xero-tenant-id"]), ({"summarizeErrors": "false"}, True, "ten-2"))
_a = _inv[0]
ck("ACCREC, borrador, importes SIN impuesto",
   (_a["Type"], _a["Status"], _a["LineAmountTypes"], _a["Contact"], _a["Date"], _a["DueDate"]),
   ("ACCREC", "DRAFT", "Exclusive", {"Name": "Acme Pty"}, "2026-09-10", "2026-09-24"))
ck("las líneas suman el SUBTOTAL emitido al centavo",
   round(sum(li["UnitAmount"] * li["Quantity"] for li in _a["LineItems"]), 2), 100.00)
ck("…y el impuesto REPARTIDO suma el de la factura al centavo (no 9.99)",
   (round(sum(li["TaxAmount"] for li in _a["LineItems"]), 2), [li["TaxAmount"] for li in _a["LineItems"]]),
   (10.00, [3.33, 3.33, 3.34]))
ck("código de impuesto de la API (OUTPUT) y cuenta de ventas",
   {(li["TaxType"], li["AccountCode"]) for li in _a["LineItems"]}, {("OUTPUT", "200")})
ck("seguimiento con los nombres EXACTOS de Xero; la línea sin obra va sin él",
   [li.get("Tracking") for li in _a["LineItems"]],
   [[{"Name": "project", "Option": "TORRE NORTE"}], [{"Name": "project", "Option": "Torre Sur"}], None])
ck("se marcan aquí la enviada Y la enlazada (una sola escritura)",
   MARCAS, [{"FAC-A": "XID-0101", "FAC-B": "XID-EXISTENTE"}])

_reset([("GET", "/Invoices", lambda kw: Resp(500, {"Message": "caído"})), ("PUT", "/Invoices", _put_invoices)])
PUTS.clear()
MARCAS.clear()
res = X.enviar_facturas(G, ["FAC-A"])
ck("sin poder COMPROBAR el número en Xero NO se envía nada",
   (len(PUTS), res["enviadas"], len(res["errores"]), MARCAS), (0, [], 1, []))

_reset([("GET", "/Invoices", lambda kw: Resp(200, {"Invoices": []})),
        ("GET", "/TrackingCategories", lambda kw: Resp(200, {"TrackingCategories": []})),
        ("PUT", "/Invoices", _put_invoices)])
PUTS.clear()
OPCIONES_CREADAS.clear()
res = X.enviar_facturas(G, ["FAC-A"])
ck("sin la categoría en Xero: se envía SIN seguimiento, sin crearla, y se avisa",
   (len(PUTS), all("Tracking" not in li for li in PUTS[0]["json"]["Invoices"][0]["LineItems"]),
    OPCIONES_CREADAS, bool(res["avisos"])), (1, True, [], True))

_reset([("GET", "/Invoices", lambda kw: Resp(200, {"Invoices": []})),
        ("GET", "/TrackingCategories", lambda kw: Resp(200, {"TrackingCategories": []})),
        ("PUT", "/Invoices", lambda kw: Resp(429, {}, {"Retry-After": "37"}))])
res = X.enviar_facturas(G, ["FAC-A"])
ck("un 429 se cuenta como error legible con la espera de Xero",
   (res["enviadas"], "37" in " ".join(res["errores"][0][2])), ([], True))

_reset([("GET", "/Invoices", lambda kw: Resp(200, {"Invoices": []})),
        ("GET", "/TrackingCategories", lambda kw: Resp(200, {"TrackingCategories": []})),
        ("PUT", "/Invoices", lambda kw: Resp(200, {"Invoices": [
            {"InvoiceNumber": "0101", "InvoiceID": "00000000-0000-0000-0000-000000000000",
             "HasErrors": True, "ValidationErrors": [{"Message": "Account code '200' is not a valid code"}]}]}))])
MARCAS.clear()
res = X.enviar_facturas(G, ["FAC-A"])
ck("el error de validación de Xero llega TAL CUAL y no se marca nada",
   (res["enviadas"], res["errores"][0][2], MARCAS),
   ([], ["Account code '200' is not a valid code"], []))
_CFG["cuentas"] = {"xero": {contable.VENTAS: ""}}
_reset()
res = X.enviar_facturas(G, ["FAC-A"])
ck("sin cuenta de ventas no sale ni una llamada", (len(LLAMADAS), bool(res["errores"])), (0, True))
_CFG["cuentas"] = {"xero": {contable.VENTAS: "200"}}
(invoices.get_factura, invoices.marcar_xero, contable.mapa, contable._etiquetas,
 contable.fichas_clientes) = _orig6

# ═════ 7 · marcar_xero real: 1 lectura + 1 escritura, por NOMBRE de columna ══
print("\n[7] marcar en la hoja de facturas")
_hoja_inv = HojaFalsa(_H, [["FAC-1"] + [""] * 20, ["FAC-2"] + [""] * 20, ["FAC-3"] + [""] * 20])
_orig_ws = invoices._ws
invoices._ws = lambda: (_hoja_inv, None)
okm, _ = invoices.marcar_xero({"FAC-1": "X1", "FAC-3": "X3"}, "2026-09-15 10:00:00")
ck("marca las dos con 1 lectura y 1 escritura",
   (okm, _hoja_inv.lecturas, _hoja_inv.escrituras), (True, 1, 1))
ck("…en las columnas XeroInvoiceID / XeroSentAt de su fila",
   (_hoja_inv.fila(2)["XeroInvoiceID"], _hoja_inv.fila(3)["XeroInvoiceID"],
    _hoja_inv.fila(4)["XeroInvoiceID"], _hoja_inv.fila(4)["XeroSentAt"]),
   ("X1", "", "X3", "2026-09-15 10:00:00"))
_vieja = HojaFalsa(_H[:19], [["FAC-1"] + [""] * 18])
invoices._ws = lambda: (_vieja, None)
okm, msgm = invoices.marcar_xero({"FAC-1": "X1"}, "hoy")
ck("una hoja SIN las columnas nuevas da error y NO escribe al lado",
   (okm, _vieja.escrituras), (False, 0))
invoices._ws = _orig_ws

# ═════ 8 · desconectar: primero en Xero ══════════════════════════════════════
print("\n[8] desconectar")
_pon_token("DESC", "R-DESC", time.time() + 900)
HOJA.vals[1][X.HEADERS.index("ConnectionID")] = "con-2"
_orden = []
_orig_esc = X._escribe


def _escribe_espia(ws, n, cab, campos):
    _orden.append("local")
    return _orig_esc(ws, n, cab, campos)


X._escribe = _escribe_espia
_reset([("DELETE", "Connections/con-2", lambda kw: (_orden.append("xero") or Resp(204)))])
okd, msgd = X.desconectar(G)
X._escribe = _orig_esc
ck("DELETE en Xero ANTES de borrar la conexión aquí", (okd, _orden[:2]), (True, ["xero", "local"]))
ck("…y la fila queda sin token ni organización",
   (HOJA.fila(2)["TokenEnc"], HOJA.fila(2)["TenantID"], HOJA.fila(2)["Status"], HOJA.fila(2)["Group"]),
   ("", "", "", G))
okt, _m = X._token(G)
ck("tras desconectar ya no hay token (tampoco en memoria)", okt, False)

# ═════ 9 · la caché de pantalla nunca lleva el token ═════════════════════════
print("\n[9] la caché de estado")
_pon_token("CACHE", "R-CACHE", time.time() + 900)
HOJA.vals[1][X.HEADERS.index("TenantName")] = "Demo Company (AU)"
HOJA.vals[1][X.HEADERS.index("TenantID")] = "ten-2"
HOJA.vals[1][X.HEADERS.index("ShortCode")] = "!zz"      # la sección 8 los borró al desconectar
_arb_cache = _func(_arb_x, "_estados_cached")
ck("la caché de estado tiene su parámetro de libro SIN guion bajo (v378)",
   [a.arg for a in _arb_cache.args.args], ["libro"])
X._estados_cached.clear()
_filas_cache = X._estados_cached("libro-prueba")
ck("las filas cacheadas NO llevan el token", all("TokenEnc" not in f for f in _filas_cache), True)
ck("…y el estado sí sabe que está conectada", X.estado(G)["conectada"], True)
_HOJA_NO = {"si": False}
X._ws = lambda crear=True: (HOJA if crear else None)
X._estados_cached.clear()
ck("un lector de PANTALLA no crea la pestaña (v145)", X.estado(G)["conectada"], False)
X._ws = _ws_falso

# ═════ 10 · la interfaz se EJECUTA ═══════════════════════════════════════════
print("\n[10] pantallas")
from core import flash, home_ui                                    # noqa: E402

PINT = {"link": [], "button": [], "radio": [], "info": 0, "code": [], "caption": []}
_g = {}


class _Ctx:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _espia(nombre, fn):
    _g[nombre] = getattr(st, nombre)
    setattr(st, nombre, fn)


_espia("link_button", lambda label, url, **kw: PINT["link"].append((label, url)))
_espia("button", lambda label, **kw: PINT["button"].append(label) or False)
_espia("radio", lambda label, opciones, **kw: PINT["radio"].append((label, list(opciones), kw)) or opciones[0])
_espia("info", lambda *a, **kw: PINT.__setitem__("info", PINT["info"] + 1))
_espia("code", lambda txt, **kw: PINT["code"].append(txt))
_espia("caption", lambda txt, **kw: PINT["caption"].append(txt))
_espia("markdown", lambda *a, **kw: None)
_espia("warning", lambda *a, **kw: None)
_espia("expander", lambda *a, **kw: _Ctx())


class _Col:
    # ⚠️ `c1.button(...)` es un método del contenedor, NO `st.button`: sin delegar aquí,
    # espiar `st.button` no vería el «Yes, disconnect» y su chequeo pasaría en vacío.
    def button(self, *a, **kw):
        return st.button(*a, **kw)


_espia("columns", lambda n, **kw: [_Col() for _ in range(n if isinstance(n, int) else len(n))])
_espia("checkbox", lambda *a, **kw: False)
_espia("spinner", lambda *a, **kw: _Ctx())
from core import theme as T                                        # noqa: E402
_sec = T.section
T.section = lambda *a, **kw: None
try:
    _sin = dict(SECRETOS)
    SECRETOS.clear()
    XU.render_conexion(G)
    ck("sin configurar: dice qué falta y enseña la redirect URI a registrar",
       (PINT["info"] >= 1, bool(PINT["code"]), PINT["link"]), (True, True, []))
    SECRETOS.update(_sin)
    PINT["link"].clear()
    X._ws = lambda crear=True: None
    X._estados_cached.clear()
    XU.render_conexion(G)
    ck("sin conectar: botón «Connect to Xero» con la URL de autorización",
       len(PINT["link"]) == 1 and PINT["link"][0][1].startswith(X.AUTH_URL), True)
    X._ws = _ws_falso
    X._estados_cached.clear()
    PINT["link"].clear()
    PINT["radio"].clear()
    _orig_pend = XU._pendientes
    XU._pendientes = lambda g, d, h: {"pendientes": ["FAC-A", "FAC-B"], "enviables": 3}
    _orig_mapa = contable.mapa
    contable.mapa = lambda g: {"cuentas": {"xero": {contable.VENTAS: "200"}}, "xero_estado": "DRAFT"}
    XU.render_conexion(G)
    ck("conectada: el estado de envío es un radio con los CÓDIGOS de Xero como dato (v442)",
       (PINT["radio"][0][1], PINT["radio"][0][2].get("format_func") is not None),
       (["DRAFT", "AUTHORISED"], True))
    ck("…y ofrece mandar las pendientes del periodo",
       any("Send" in b and "2" in b for b in PINT["button"]), True)
    # ⚠️ v489: sin facturas en el periodo NO puede decir «ya están todas en Xero».
    # ⚠️ La sonda compara la frase ENTERA: «already in Xero» también sale en el pie de
    # «Disconnect» y daba un rojo que no existía.
    PINT["caption"].clear()
    XU._pendientes = lambda g, d, h: {"pendientes": [], "enviables": 0}
    XU.render_conexion(G)
    ck("periodo SIN facturas: dice que no hay nada que mandar, no que ya están todas",
       (any("no invoices to send" in c for c in PINT["caption"]),
        any("Every invoice of this period is already in Xero" in c for c in PINT["caption"])), (True, False))
    PINT["caption"].clear()
    XU._pendientes = lambda g, d, h: {"pendientes": [], "enviables": 2}
    XU.render_conexion(G)
    ck("…y con todas mandadas, sí lo dice",
       any("Every invoice of this period is already in Xero" in c for c in PINT["caption"]), True)
    # ⚠️ v489: desconectar es un BOTÓN que pregunta; el desplegable con casilla parecía
    # el botón y no hacía nada (visto en producción). Sin la confirmación, NO desconecta.
    ck("desconectar se ofrece como botón visible (no un desplegable)",
       any("Disconnect Xero" in b for b in PINT["button"]), True)
    _desc = []
    _orig_desc = X.desconectar
    X.desconectar = lambda g: (_desc.append(g) or (True, "ok"))
    _orig_btn = st.button
    st.button = lambda label, **kw: (PINT["button"].append(label) or
                                     kw.get("key") == "xero_desconectar_pedir")
    _orig_rerun = st.rerun
    st.rerun = lambda: None
    st.session_state.pop("_xero_confirmar_desconexion", None)
    XU.render_conexion(G)
    ck("pulsar «Disconnect Xero» solo PIDE confirmación (todavía no desconecta)",
       (st.session_state.get("_xero_confirmar_desconexion"), _desc), (True, []))
    PINT["button"].clear()
    st.button = lambda label, **kw: (PINT["button"].append(label) or
                                     kw.get("key") == "xero_desconectar_si")
    XU.render_conexion(G)
    ck("«Yes, disconnect» desconecta esta empresa y cierra la pregunta",
       (_desc, st.session_state.get("_xero_confirmar_desconexion")), ([G], None))
    st.session_state["_xero_confirmar_desconexion"] = True
    _desc.clear()
    st.button = lambda label, **kw: (PINT["button"].append(label) or
                                     kw.get("key") == "xero_desconectar_no")
    XU.render_conexion(G)
    ck("«Cancel» no desconecta y cierra la pregunta",
       (_desc, st.session_state.get("_xero_confirmar_desconexion")), ([], None))
    st.button, st.rerun, X.desconectar = _orig_btn, _orig_rerun, _orig_desc
    XU._pendientes = _orig_pend
    contable.mapa = _orig_mapa
    PINT["link"].clear()
    XU.boton_factura(G, {"ID": "FAC-Z", "Group": G, "XeroInvoiceID": "XID-9", "XeroSentAt": "hoy"})
    ck("una factura ya en Xero enlaza a ELLA con el código corto de la organización",
       PINT["link"][-1][1], "https://go.xero.com/app/!zz/invoicing/view/XID-9")

    # ── la vuelta desde Xero ──
    class QP(dict):
        def get(self, k, d=None):
            return dict.get(self, k, d)

        def clear(self):
            dict.clear(self)

    _qp = QP(code="CODIGO-UI", state="STATE-UI", scope="x")
    _orig_qp = st.query_params
    st.query_params = _qp
    _llam = []
    _orig_comp = X.completar_conexion
    X.completar_conexion = lambda g, u, c, s: (_llam.append((g, u, c, s)) or (True, "ok", []))
    _nav = []
    _orig_nav = home_ui.navegar
    home_ui.navegar = lambda sec, sub=None: _nav.append((sec, sub))
    st.session_state.pop("_xero_retorno", None)
    XU.procesar_retorno("field", G)
    ck("un usuario de CAMPO no procesa la vuelta", (_llam, _nav), ([], []))
    XU.procesar_retorno("administrator", G)
    ck("el admin canjea el código UNA vez con su usuario y empresa",
       _llam, [(G, "admin", "CODIGO-UI", "STATE-UI")])
    ck("…limpia la URL (el código es de un solo uso) y vuelve a Contable",
       (dict(_qp), _nav), ({}, [("finanzas", "📤 Contable")]))
    _qp.update(code="CODIGO-UI", state="STATE-UI")
    XU.procesar_retorno("administrator", G)
    ck("un rerun con el MISMO state no vuelve a canjear", len(_llam), 1)
    st.query_params = _orig_qp
    X.completar_conexion = _orig_comp
    home_ui.navegar = _orig_nav
    _ids = [s for s, _l in home_ui._SUBSECCIONES["finanzas"][1]]
    ck("el destino de la vuelta EXISTE en la navegación (v303)", "📤 Contable" in _ids, True)
except Exception as e:
    import traceback
    fallo("las pantallas revientan", f"{type(e).__name__}: {e}")
    traceback.print_exc()
finally:
    for n, f in _g.items():
        setattr(st, n, f)
    T.section = _sec
    flash.mostrar = flash.mostrar

# ═════ 11 · enganches en app.py / contable_ui / invoices_ui ══════════════════
print("\n[11] enganches")
_app = _fuente("app.py")
_i_login = _app.find("if not render_login():")
_i_xero = _app.find("_xui.procesar_retorno(_ROL, _GRUPO)")
_i_hb = _app.find("if not heartbeat(")
ck("app.py procesa la vuelta DESPUÉS del login y ANTES del heartbeat",
   0 < _i_login < _i_xero < _i_hb, True)
_arb_cu = ast.parse(_fuente("core/contable_ui.py"))
ck("la pantalla Contable pinta la conexión con el periodo del CSV",
   any(isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "render_conexion"
       and [getattr(a, "id", "") for a in n.args] == ["grupo", "desde", "hasta"]
       for n in ast.walk(_arb_cu)), True)
_arb_iu = ast.parse(_fuente("core/invoices_ui.py"))
_det = _func(_arb_iu, "_detalle_factura")
ck("el detalle de factura ofrece Xero, DESPUÉS del cerrojo de empresa (v351)",
   any(isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "boton_factura"
       for n in ast.walk(_det)), True)
_lin_cerrojo = min(n.lineno for n in ast.walk(_det) if isinstance(n, ast.Call)
                   and getattr(n.func, "attr", "") == "exigir")
_lin_boton = min(n.lineno for n in ast.walk(_det) if isinstance(n, ast.Call)
                 and getattr(n.func, "attr", "") == "boton_factura")
ck("…(orden por línea)", _lin_cerrojo < _lin_boton, True)
ck("xero.py no usa `requests` fuera de `_http` (un único punto de salida)",
   [n.lineno for n in ast.walk(_arb_x) if isinstance(n, ast.Attribute)
    and getattr(n.value, "id", "") == "requests" and n.lineno not in
    range(_func(_arb_x, "_http").lineno, _func(_arb_x, "_http").end_lineno + 1)], [])

# ═════ 12 · ningún secreto en el log ═════════════════════════════════════════
print("\n[12] el log")
_log = _LOG.getvalue()
_filtrados = [s for s in ("SECRETO-no-debe-salir", "R-VIEJO", "R-NUEVO", "ACCESO-secreto",
                          "REFRESCO-secreto", CLAVE, ACC1, "R-B", "ROTADO")
              if s and s in _log]
ck("ni el client secret, ni tokens, ni la clave aparecen en el log", _filtrados, [])
ck("…y el log sí registró cosas (la sonda ve)", len(_log) > 0, True)

X._secret = _secret_real
print("\n" + "=" * 74)
print(f"{n_ok} comprobaciones OK · {len(fallos)} fallos")
if fallos:
    for f in fallos:
        print("   -", f)
sys.exit(1 if fallos else 0)
