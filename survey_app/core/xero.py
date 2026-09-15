# -*- coding: utf-8 -*-
"""Conexión con Xero por su API: conectar la organización y mandarle facturas (v488).

Fase 2.3-A. La 2.1 (v483) produce un CSV que alguien importa a mano; esto quita ese
paso para las facturas. El parte de horas a Xero Payroll (2.3-B) usará la misma
conexión, por eso los permisos de nómina se piden desde el principio (decisión del
usuario): así no hay que volver a autorizar cuando llegue.

## Lo que se verificó en la documentación de Xero, no de memoria
- Autorizar en `login.xero.com/identity/connect/authorize`, canjear en
  `identity.xero.com/connect/token` con Basic auth, y `GET api.xero.com/Connections`
  (filtrable por `authEventId`) para saber qué organización se autorizó.
- ⚠️ Una app creada desde marzo de 2026 **solo** tiene los scopes GRANULARES: las
  facturas son `accounting.invoices`, no `accounting.transactions` (que la
  especificación OpenAPI todavía lista).
- El token de acceso dura 30 min; el de refresco **rota en cada uso** y caduca a los
  60 días sin usarse.
- `PUT /Invoices` crea (no actualiza) y acepta `Idempotency-Key`; el enlace directo a
  una factura necesita el `ShortCode` de la organización.

## Dónde viven los tokens, y por qué ahí
En la pestaña **`XeroConnections` del libro MAESTRO**, cifrados con Fernet
(`XERO_TOKEN_KEY`). ⚠️ No en columnas de `Groups`: esa hoja se lee en CADA pantalla y
se cachea para todos (v339), y el token rota cada media hora de uso — cada rotación
invalidaría la caché de medio mundo. Y un token no tiene nada que hacer en una caché
compartida. Esta pestaña se lee FRESCA y solo cuando se usa Xero.
"""
import base64
import hashlib
import hmac
import json
import logging
import secrets as _aleatorio
import threading
import time
from urllib.parse import quote, urlencode

import streamlit as st

from core import clock, columnas, timeclock
from core.i18n import t
from core.num import col_letter as _col_letter

logger = logging.getLogger(__name__)

AUTH_URL = "https://login.xero.com/identity/connect/authorize"
TOKEN_URL = "https://identity.xero.com/connect/token"
CONNECTIONS_URL = "https://api.xero.com/Connections"
API_URL = "https://api.xero.com/api.xro/2.0"
PAYROLL_URL = "https://api.xero.com/payroll.xro/1.0"     # Payroll AU (v490)

SCOPES = ("offline_access",
          "accounting.invoices", "accounting.payments", "accounting.contacts",
          "accounting.settings",
          "payroll.employees", "payroll.timesheets", "payroll.settings")

SHEET = "XeroConnections"
HEADERS = ["Group", "TenantID", "TenantName", "ShortCode", "ConnectionID",
           "TokenEnc", "Status", "ConnectedBy", "ConnectedAt", "RefreshedAt"]
CONECTADA, CADUCADA = "connected", "expired"

# Cómo llegan las facturas a Xero. El dato es el CÓDIGO de Xero; la etiqueta se
# traduce al pintar (v442: traducir la opción dejaría la comparación muerta).
BORRADOR, APROBADA = "DRAFT", "AUTHORISED"
ESTADOS_ENVIO = (BORRADOR, APROBADA)
_VIVAS = {"DRAFT", "SUBMITTED", "AUTHORISED", "PAID"}   # DELETED/VOIDED no cuentan

_SECRETOS = ("XERO_CLIENT_ID", "XERO_CLIENT_SECRET", "XERO_TOKEN_KEY")
_STATE_MAX_S = 30 * 60          # un login con MFA puede tardar; más no hace falta
_TIMEOUT = 30
_POR_LOTE = 50                  # tope recomendado por Xero por petición
_GST_AU = 10.0                  # OUTPUT = «GST on Income», 10 %
_CUPO_MIN = 55                  # Xero: 60 llamadas/min por organización; margen de 5
_ESPERA_429 = 20                # un 429 con espera corta se reintenta UNA vez


def _norm(s) -> str:
    return str(s or "").strip().casefold()


# ─────────────────────────────────────────────────────────────────────────────
# Configuración (Secrets)
# ─────────────────────────────────────────────────────────────────────────────
def _secret(nombre: str) -> str:
    try:
        return str(st.secrets.get(nombre, "") or "").strip()
    except Exception:
        return ""


def redirect_uri() -> str:
    """La dirección a la que Xero devuelve al usuario.

    ⚠️ Xero la compara CARÁCTER A CARÁCTER con la registrada en su app (sin
    comodines), así que la pantalla enseña esta cadena exacta para copiarla.
    """
    propia = _secret("XERO_REDIRECT_URI")
    if propia:
        return propia
    base = _secret("APP_URL").rstrip("/")
    return f"{base}/" if base else ""


def configuracion() -> dict:
    """{ok, faltan:[secret], problemas:[texto], redirect}. No llama a nadie."""
    faltan = [n for n in _SECRETOS if not _secret(n)]
    if not redirect_uri():
        faltan.append("XERO_REDIRECT_URI")
    problemas = []
    if _secret("XERO_TOKEN_KEY"):
        try:
            _fernet()
        except ImportError:
            problemas.append(t("The «cryptography» package is not installed."))
        except Exception:
            problemas.append(t("XERO_TOKEN_KEY is not a valid key: generate it with "
                               "Fernet.generate_key()."))
    return {"ok": not faltan and not problemas, "faltan": faltan,
            "problemas": problemas, "redirect": redirect_uri()}


# ─────────────────────────────────────────────────────────────────────────────
# Cifrado del token y firma del «state»
# ─────────────────────────────────────────────────────────────────────────────
def _fernet():
    from cryptography.fernet import Fernet
    return Fernet(_secret("XERO_TOKEN_KEY").encode())


def _cifra(paquete: dict) -> str:
    return _fernet().encrypt(json.dumps(paquete).encode()).decode()


def _descifra(texto: str):
    """El paquete del token, o None si no se puede leer (clave cambiada, dato roto)."""
    try:
        return json.loads(_fernet().decrypt(str(texto or "").encode()).decode())
    except Exception as e:
        logger.warning("xero: token ilegible (%s)", type(e).__name__)
        return None


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _clave_state() -> bytes:
    # Derivada, no la clave de cifrado tal cual: una clave, un propósito.
    return hashlib.sha256(b"copex-xero-state|" + _secret("XERO_TOKEN_KEY").encode()).digest()


def firma_state(grupo: str, usuario: str, ahora=None) -> str:
    """El `state` de OAuth: empresa + usuario + hora, FIRMADO.

    ⚠️ La sesión de Streamlit NO sobrevive a la vuelta desde Xero (llega en una
    pestaña nueva), así que no se puede guardar nada en `session_state` para
    comprobarlo después. La firma permite verificar sin guardar: nadie puede
    fabricar un `state` para la empresa o el usuario de otro.
    """
    carga = json.dumps({"g": str(grupo or ""), "u": str(usuario or ""),
                        "ts": int(ahora if ahora is not None else time.time()),
                        "n": _aleatorio.token_urlsafe(8)},
                       separators=(",", ":")).encode()
    firma = hmac.new(_clave_state(), carga, hashlib.sha256).digest()
    return f"{_b64(carga)}.{_b64(firma)}"


def verifica_state(state: str, ahora=None) -> tuple:
    """(datos, motivo). `motivo` es "" si vale, "firma" o "caducado"."""
    try:
        a, b = str(state or "").split(".", 1)
        carga, firma = _unb64(a), _unb64(b)
    except Exception:
        return None, "firma"
    esperada = hmac.new(_clave_state(), carga, hashlib.sha256).digest()
    if not hmac.compare_digest(esperada, firma):
        return None, "firma"
    try:
        datos = json.loads(carga)
        edad = (ahora if ahora is not None else time.time()) - int(datos.get("ts", 0))
    except Exception:
        return None, "firma"
    if edad < -60 or edad > _STATE_MAX_S:
        return None, "caducado"
    return datos, ""


def url_autorizacion(grupo: str, usuario: str) -> str:
    # ⚠️ `quote`, no `quote_plus`: los scopes van separados por espacio y se envían
    # como %20, que es lo que dice la especificación de OAuth.
    return AUTH_URL + "?" + urlencode({
        "response_type": "code",
        "client_id": _secret("XERO_CLIENT_ID"),
        "redirect_uri": redirect_uri(),
        "scope": " ".join(SCOPES),
        "state": firma_state(grupo, usuario),
    }, quote_via=quote)


def url_factura(short_code: str, invoice_id: str) -> str:
    """Enlace directo a la factura en Xero (formato del servidor MCP oficial de Xero)."""
    if short_code:
        return f"https://go.xero.com/app/{short_code}/invoicing/view/{invoice_id}"
    return f"https://go.xero.com/AccountsReceivable/View.aspx?InvoiceID={invoice_id}"


# ─────────────────────────────────────────────────────────────────────────────
# HTTP
# ─────────────────────────────────────────────────────────────────────────────
def _http(metodo: str, url: str, **kw):
    """Único punto de salida a Internet: los guardianes lo sustituyen."""
    import requests
    kw.setdefault("timeout", _TIMEOUT)
    return requests.request(metodo, url, **kw)


def _json(resp):
    try:
        return resp.json()
    except Exception:
        return {}


def mensajes_error(js) -> list:
    """Los mensajes legibles de una respuesta de error de Xero, sin repetir."""
    out = []
    if isinstance(js, dict):
        for el in js.get("Elements") or []:
            for v in (el or {}).get("ValidationErrors") or []:
                if (v or {}).get("Message"):
                    out.append(str(v["Message"]))
        # ⚠️ v490 · Payroll AU devuelve los errores DENTRO de cada objeto de la lista
        # (`Timesheets[i].ValidationErrors`, `LeaveApplications[i].ValidationErrors`),
        # no en `Elements`. Sin mirar ahí, el aviso diría solo «A validation exception
        # occurred» y nadie sabría qué arreglar.
        for v in js.values():
            if isinstance(v, list):
                for el in v:
                    for ve in (el or {}).get("ValidationErrors") or [] if isinstance(el, dict) else []:
                        if (ve or {}).get("Message"):
                            out.append(str(ve["Message"]))
        for k in ("Message", "Detail", "detail", "title", "error_description", "error"):
            if not out and js.get(k):
                out.append(str(js[k]))
    return list(dict.fromkeys(out))


def _pide_token(datos: dict) -> tuple:
    """(ok, json | código de error). ⚠️ Nunca registra el token ni la respuesta."""
    basic = base64.b64encode(
        f"{_secret('XERO_CLIENT_ID')}:{_secret('XERO_CLIENT_SECRET')}".encode()).decode()
    try:
        r = _http("POST", TOKEN_URL, data=datos,
                  headers={"Authorization": f"Basic {basic}",
                           "Accept": "application/json"})
    except Exception as e:
        logger.warning("xero: no se pudo contactar el servidor de tokens: %s",
                       type(e).__name__)
        return False, "red"
    js = _json(r)
    if r.status_code != 200 or not isinstance(js, dict) or not js.get("access_token"):
        return False, str((js or {}).get("error") or f"HTTP {r.status_code}")
    return True, js


def _paquete(js: dict, previo: dict = None) -> dict:
    return {"a": js["access_token"],
            "r": js.get("refresh_token") or (previo or {}).get("r", ""),
            "e": int(time.time()) + int(js.get("expires_in") or 1800) - 60}


def _claims(jwt: str) -> dict:
    """El cuerpo del token de acceso, SIN verificar la firma: viene directo del
    servidor de tokens por TLS, y solo se lee el id del evento de autorización."""
    try:
        return json.loads(_unb64(str(jwt).split(".")[1]))
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# La pestaña de conexiones
# ─────────────────────────────────────────────────────────────────────────────
def _ws(crear: bool = True):
    """La pestaña. Con `crear=False` devuelve None si aún no existe.

    ⚠️ Un lector de PANTALLA no puede crearla: `get_sheet` crea la hoja que no
    encuentra, y un «lector que escribe» es la regla de v145. Solo la primera
    conexión la crea.
    """
    if crear:
        return timeclock.get_sheet(SHEET, tuple(HEADERS))
    sid = timeclock.sheet_id_para(SHEET)
    hojas, _cab = timeclock._libro(sid)
    return hojas.get(timeclock.titulo_real(SHEET, sid).strip().lower())


def _leer(ws) -> tuple:
    """(cabecera canónica, [(nº de fila, dict)]) leídos FRESCOS."""
    vals = ws.get_all_values() or []
    cab = [columnas.canon(h) for h in (vals[0] if vals else HEADERS)]
    filas = [(i, {h: (fila[j] if j < len(fila) else "") for j, h in enumerate(cab)})
             for i, fila in enumerate(vals[1:], start=2)]
    return cab, filas


def _escribe(ws, n: int, cab: list, campos: dict):
    """Escribe los campos de UNA fila por el nombre de su columna, en 1 llamada."""
    rangos = [{"range": f"{_col_letter(cab.index(k) + 1)}{n}", "values": [[str(v)]]}
              for k, v in campos.items() if k in cab]
    if rangos:
        ws.batch_update(rangos, value_input_option="RAW")


def _invalida():
    try:
        _estados_cached.clear()
    except Exception:
        pass


@st.cache_data(ttl=300, show_spinner=False)
def _estados_cached(libro: str) -> list:
    """Las conexiones SIN el token: lo que la pantalla necesita para pintar.

    ⚠️ El token no entra nunca en esta caché (se comparte por proceso). Y el
    parámetro NO empieza por «_»: Streamlit lo dejaría fuera de la clave (v378).
    """
    ws = _ws(crear=False)
    if ws is None:
        return []
    _cab, filas = _leer(ws)
    return [{k: v for k, v in r.items() if k != "TokenEnc"} | {"_con_token": bool(r.get("TokenEnc"))}
            for _n, r in filas]


def estado(grupo: str) -> dict:
    """{conectada, estado, tenant, short_code, por, desde} de la empresa. Cacheado."""
    vacio = {"conectada": False, "estado": "", "tenant": "", "tenant_id": "",
             "short_code": "", "por": "", "desde": ""}
    if not configuracion()["ok"]:
        return vacio
    try:
        filas = _estados_cached(timeclock.sheet_id_para(SHEET))
    except Exception as e:
        logger.warning("xero: no se pudo leer el estado de la conexión: %s", e)
        return vacio
    for r in filas:
        if _norm(r.get("Group")) == _norm(grupo):
            est = str(r.get("Status", "") or "")
            return {"conectada": est == CONECTADA and r.get("_con_token", False),
                    "estado": est, "tenant": r.get("TenantName", ""),
                    "tenant_id": r.get("TenantID", ""),
                    "short_code": r.get("ShortCode", ""),
                    "por": r.get("ConnectedBy", ""), "desde": r.get("ConnectedAt", "")}
    return vacio


# ─────────────────────────────────────────────────────────────────────────────
# Token vigente (con refresco y rotación)
# ─────────────────────────────────────────────────────────────────────────────
_CERROJO = threading.Lock()
_CERROJOS = {}
_PENDIENTES = {}        # token ya rotado en Xero que no se pudo guardar en la hoja
# Token vigente en memoria del proceso: sin esto, CADA llamada a la API releería la
# hoja (una factura son 3-5 llamadas) contra el techo de 60 lecturas/min de la única
# cuenta de servicio. Caduca con el propio token y se tira al desconectar o con un 401.
_VIVOS = {}


def _cerrojo(grupo: str):
    """Uno por empresa, reentrante.

    ⚠️ El token de refresco ROTA en cada uso. Dos sesiones refrescando a la vez
    usarían el mismo token viejo y una de las dos rotaciones se perdería. El
    cerrojo serializa: la segunda relee la hoja y encuentra el token nuevo.
    """
    with _CERROJO:
        return _CERROJOS.setdefault(_norm(grupo), threading.RLock())


def _token(grupo: str, forzar: bool = False) -> tuple:
    """(ok, {access, tenant_id, short_code} | mensaje)."""
    with _cerrojo(grupo):
        memo = _VIVOS.get(_norm(grupo))
        if memo and not forzar and memo["e"] > time.time():
            return True, dict(memo["vivo"], access=memo["a"])
        _VIVOS.pop(_norm(grupo), None)
        try:
            ws = _ws(crear=False)
            if ws is None:
                return False, t("This company is not connected to Xero.")
            cab, filas = _leer(ws)
        except Exception as e:
            logger.warning("xero: lectura de la conexión falló: %s", e)
            return False, t("The Xero connection could not be read. Try again.")
        n, fila = next(((i, r) for i, r in filas if _norm(r.get("Group")) == _norm(grupo)),
                       (None, {}))
        if n is None or not fila.get("TokenEnc") or not fila.get("TenantID"):
            return False, t("This company is not connected to Xero.")

        paquete = _PENDIENTES.get(_norm(grupo)) or _descifra(fila["TokenEnc"])
        if paquete is None:
            return False, t("The saved Xero connection cannot be read (did XERO_TOKEN_KEY "
                            "change?). Connect again.")
        vivo = {"tenant_id": fila["TenantID"], "short_code": fila.get("ShortCode", "")}

        if not forzar and not _PENDIENTES.get(_norm(grupo)) and paquete.get("e", 0) > time.time():
            _VIVOS[_norm(grupo)] = {"vivo": vivo, "a": paquete["a"], "e": paquete["e"]}
            return True, dict(vivo, access=paquete["a"])

        if forzar or paquete.get("e", 0) <= time.time():
            ok, js = _pide_token({"grant_type": "refresh_token",
                                  "refresh_token": paquete.get("r", "")})
            if not ok:
                if js == "invalid_grant":
                    try:
                        _escribe(ws, n, cab, {"Status": CADUCADA})
                    except Exception as e:
                        logger.error("xero: no se pudo marcar la conexión caducada: %s", e)
                    _PENDIENTES.pop(_norm(grupo), None)
                    _invalida()
                    return False, t("The Xero connection expired (unused for 60 days, or "
                                    "revoked in Xero). Connect again.")
                return False, t("Xero did not renew the access ({e}). Try again.", e=js)
            paquete = _paquete(js, paquete)

        try:
            _escribe(ws, n, cab, {"TokenEnc": _cifra(paquete), "Status": CONECTADA,
                                  "RefreshedAt": clock.now().strftime("%Y-%m-%d %H:%M:%S")})
            _PENDIENTES.pop(_norm(grupo), None)
        except Exception as e:
            # ⚠️ El token YA rotó en Xero: el viejo de la hoja deja de valer en 30 min.
            # Se guarda en memoria y se reintenta en la próxima llamada, en vez de
            # perder la conexión por un fallo de escritura puntual.
            _PENDIENTES[_norm(grupo)] = paquete
            logger.error("xero: token renovado pero NO guardado (%s); se reintentará", e)
        _invalida()
        _VIVOS[_norm(grupo)] = {"vivo": vivo, "a": paquete["a"], "e": paquete["e"]}
        return True, dict(vivo, access=paquete["a"])


_LLAMADAS = {}
_CERROJO_CUPO = threading.Lock()


def _espera_cupo(tenant_id: str, ahora=None):
    """Segundos a esperar para no pasar de `_CUPO_MIN` llamadas en 60 s a ESA
    organización, y apunta la llamada. Función separada para poder probarla.

    ⚠️ v490 · El parte de un equipo son ~4 llamadas por persona: con 15 personas ya
    se pasa de 60/min y Xero responde 429 a mitad del envío, dejando a unos con parte
    y a otros sin él. Esperar un poco es mejor que un envío a medias.
    """
    ahora = time.time() if ahora is None else ahora
    with _CERROJO_CUPO:
        marcas = [m for m in _LLAMADAS.get(tenant_id, []) if ahora - m < 60]
        espera = 0.0
        if len(marcas) >= _CUPO_MIN:
            espera = max(0.0, 60 - (ahora - marcas[0]) + 0.1)
        marcas.append(ahora + espera)
        _LLAMADAS[tenant_id] = marcas
        return espera


def _api(grupo: str, metodo: str, ruta: str, *, params=None, cuerpo=None,
         cabeceras=None, base: str = API_URL) -> tuple:
    """(status, json, cabeceras). status 0 = no se llegó a llamar (mensaje en json)."""
    ok, tok = _token(grupo)
    if not ok:
        return 0, {"Message": tok}, {}
    r = None
    refrescado = esperado = False
    while True:
        h = {"Authorization": f"Bearer {tok['access']}", "xero-tenant-id": tok["tenant_id"],
             "Accept": "application/json"}
        h.update(cabeceras or {})
        pausa = _espera_cupo(tok["tenant_id"])
        if pausa:
            time.sleep(pausa)
        try:
            r = _http(metodo, base + ruta, params=params, json=cuerpo, headers=h)
        except Exception as e:
            logger.warning("xero: %s %s falló: %s", metodo, ruta, type(e).__name__)
            return 0, {"Message": t("Xero could not be reached. Try again.")}, {}
        # ⚠️ Un 401 con un token que creíamos vigente (revocado antes de tiempo): se
        # fuerza UN refresco y se reintenta una vez; dos 401 seguidos ya son reales.
        if r.status_code == 401 and not refrescado:
            refrescado = True
            ok, tok = _token(grupo, forzar=True)
            if not ok:
                return 0, {"Message": tok}, {}
            continue
        # ⚠️ Un 429 con una espera CORTA se reintenta una vez; con una larga se devuelve
        # (colgar la pantalla un minuto sin decir nada es peor que un aviso).
        if r.status_code == 429 and not esperado:
            try:
                segundos = float(dict(getattr(r, "headers", {}) or {}).get("Retry-After") or 0)
            except (TypeError, ValueError):
                segundos = 0
            if 0 < segundos <= _ESPERA_429:
                esperado = True
                time.sleep(segundos)
                continue
        break
    return r.status_code, _json(r), dict(getattr(r, "headers", {}) or {})


# ─────────────────────────────────────────────────────────────────────────────
# Conectar y desconectar
# ─────────────────────────────────────────────────────────────────────────────
def completar_conexion(grupo: str, usuario: str, code: str, state: str) -> tuple:
    """Canjea el código de la vuelta desde Xero. (ok, mensaje, avisos)."""
    datos, motivo = verifica_state(state)
    if datos is None:
        if motivo == "caducado":
            return False, t("The Xero link expired before it was used. Connect again."), []
        return False, t("That Xero authorisation could not be verified. Connect again "
                        "from Finance → Accounting."), []
    if _norm(datos.get("g")) != _norm(grupo) or _norm(datos.get("u")) != _norm(usuario):
        return False, t("That Xero authorisation was started by another user or company. "
                        "Connect again from your own session."), []

    ok, js = _pide_token({"grant_type": "authorization_code", "code": code,
                          "redirect_uri": redirect_uri()})
    if not ok:
        if js == "red":
            return False, t("Xero could not be reached. Try again."), []
        return False, t("Xero did not accept the authorisation ({e}). Connect again.",
                        e=js), []
    paquete = _paquete(js)

    # ⚠️ Con el id del evento, Xero devuelve SOLO las organizaciones de esta
    # autorización. Sin él devolvería todas las del usuario, así que se toma la más
    # reciente.
    evento = _claims(paquete["a"]).get("authentication_event_id", "")
    try:
        r = _http("GET", CONNECTIONS_URL, params={"authEventId": evento} if evento else None,
                  headers={"Authorization": f"Bearer {paquete['a']}",
                           "Accept": "application/json"})
        conexiones = _json(r) if r.status_code == 200 else []
    except Exception as e:
        logger.warning("xero: lectura de conexiones falló: %s", type(e).__name__)
        conexiones = []
    orgs = [c for c in (conexiones if isinstance(conexiones, list) else [])
            if str(c.get("tenantType", "")).upper() == "ORGANISATION"]
    if not orgs:
        return False, t("Xero did not return any organisation for this authorisation."), []
    orgs.sort(key=lambda c: str(c.get("updatedDateUtc") or c.get("createdDateUtc") or ""),
              reverse=True)
    elegida = orgs[0]
    avisos = []
    if len(orgs) > 1:
        avisos.append(t("Several organisations were authorised; COPEX uses «{o}». Remove "
                        "the others in Xero if you do not need them.",
                        o=elegida.get("tenantName", "")))

    corto = ""
    try:
        r2 = _http("GET", API_URL + "/Organisation",
                   headers={"Authorization": f"Bearer {paquete['a']}",
                            "xero-tenant-id": elegida["tenantId"],
                            "Accept": "application/json"})
        if r2.status_code == 200:
            corto = str(((_json(r2).get("Organisations") or [{}])[0]).get("ShortCode") or "")
    except Exception as e:
        logger.warning("xero: no se pudo leer la organización: %s", type(e).__name__)
    if not corto:
        avisos.append(t("Xero did not give the organisation code; «Open in Xero» links "
                        "will go to Xero's home instead of the invoice."))

    try:
        ws = _ws(crear=True)
        cab, filas = _leer(ws)
        n, previa = next(((i, x) for i, x in filas if _norm(x.get("Group")) == _norm(grupo)),
                         (None, {}))
        campos = {"Group": grupo, "TenantID": elegida.get("tenantId", ""),
                  "TenantName": elegida.get("tenantName", ""), "ShortCode": corto,
                  "ConnectionID": elegida.get("id", ""), "TokenEnc": _cifra(paquete),
                  "Status": CONECTADA, "ConnectedBy": usuario,
                  "ConnectedAt": clock.now().strftime("%Y-%m-%d %H:%M:%S"),
                  "RefreshedAt": ""}
        if n is None:
            ws.append_row([str(campos.get(h, "")) for h in HEADERS],
                          value_input_option="RAW")
        else:
            _escribe(ws, n, cab, campos)
    except Exception as e:
        logger.error("xero: conexión autorizada pero NO guardada: %s", e)
        return False, t("Xero authorised the connection but it could not be saved. "
                        "Connect again."), avisos
    _PENDIENTES.pop(_norm(grupo), None)
    _VIVOS.pop(_norm(grupo), None)
    _invalida()

    viejo = str(previa.get("ConnectionID", "") or "")
    if viejo and viejo != elegida.get("id") and previa.get("TenantID") != elegida.get("tenantId"):
        avisos.append(t("The previous organisation «{o}» may still list COPEX as a connected "
                        "app in Xero; remove it there if it is no longer used.",
                        o=previa.get("TenantName", "")))
    return True, t("Connected to Xero: {o}.", o=elegida.get("tenantName", "")), avisos


def desconectar(grupo: str) -> tuple:
    """Quita la conexión en Xero y la borra aquí. (ok, mensaje)."""
    with _cerrojo(grupo):
        aviso = ""
        ok, tok = _token(grupo)
        try:
            ws = _ws(crear=False)
            cab, filas = _leer(ws) if ws is not None else (HEADERS, [])
        except Exception as e:
            logger.warning("xero: lectura para desconectar falló: %s", e)
            return False, t("The Xero connection could not be read. Try again.")
        n, fila = next(((i, r) for i, r in filas if _norm(r.get("Group")) == _norm(grupo)),
                       (None, {}))
        if n is None:
            return True, t("This company was not connected to Xero.")
        # ⚠️ Primero en Xero, después aquí: al revés, un fallo a mitad dejaría a COPEX
        # conectada en Xero sin forma de quitarlo desde la app.
        cid = str(fila.get("ConnectionID", "") or "")
        if ok and cid:
            try:
                r = _http("DELETE", f"{CONNECTIONS_URL}/{cid}",
                          headers={"Authorization": f"Bearer {tok['access']}"})
                if r.status_code not in (200, 204, 404):
                    aviso = t("Xero did not confirm it; remove COPEX in Xero → Settings → "
                              "Connected apps too.")
            except Exception as e:
                logger.warning("xero: DELETE de la conexión falló: %s", type(e).__name__)
                aviso = t("Xero could not be reached; remove COPEX in Xero → Settings → "
                          "Connected apps too.")
        elif cid:
            aviso = t("The connection had already lapsed; remove COPEX in Xero → Settings → "
                      "Connected apps if it is still listed.")
        try:
            _escribe(ws, n, cab, {h: "" for h in HEADERS if h != "Group"})
        except Exception as e:
            logger.error("xero: no se pudo borrar la conexión local: %s", e)
            return False, t("The connection could not be removed here. Try again.")
        _PENDIENTES.pop(_norm(grupo), None)
        _VIVOS.pop(_norm(grupo), None)
        _invalida()
        return True, " ".join(x for x in (t("Xero disconnected."), aviso) if x)


# ─────────────────────────────────────────────────────────────────────────────
# Facturas
# ─────────────────────────────────────────────────────────────────────────────
def estado_envio(grupo: str) -> str:
    """Borrador o aprobada, según los ajustes contables de la empresa."""
    from core import contable
    v = str(contable.mapa(grupo).get("xero_estado", BORRADOR) or BORRADOR).upper()
    return v if v in ESTADOS_ENVIO else BORRADOR


def payload_factura(doc: dict, *, cuenta: str, estado: str, categoria: str = "",
                    opciones: dict = None) -> dict:
    """La factura tal como la pide `PUT /Invoices`. Función PURA (sin red).

    `opciones` = {opción de COPEX: nombre EXACTO de la opción en Xero}; la línea
    solo lleva seguimiento si su opción está ahí.
    ⚠️ Importes SIEMPRE sin impuesto (`Exclusive`) y el impuesto de cada línea el
    REPARTIDO de `documento_venta` — la misma regla que el CSV (v483): así la
    factura suma en Xero lo mismo, al centavo, que la que se emitió aquí.
    """
    from core import contable
    codigo = contable.IMPUESTOS_XERO[doc["clave_impuesto"]][0]
    opciones = opciones or {}
    lineas = []
    for ln in doc["lineas"]:
        item = {"Description": ln["descripcion"], "Quantity": 1,
                "UnitAmount": round(ln["neto"], 2), "AccountCode": cuenta,
                "TaxType": codigo, "TaxAmount": round(ln["impuesto"], 2)}
        if categoria and opciones.get(ln["opcion"]):
            item["Tracking"] = [{"Name": categoria, "Option": opciones[ln["opcion"]]}]
        lineas.append(item)
    distintas = {ln["opcion"] for ln in doc["lineas"] if ln["opcion"]}
    return {"Type": "ACCREC", "Contact": {"Name": doc["contacto"]},
            "InvoiceNumber": doc["numero"],
            "Reference": (next(iter(distintas)) if len(distintas) == 1 else "")[:255],
            "Date": doc["fecha"].isoformat(), "DueDate": doc["vence"].isoformat(),
            "LineAmountTypes": "Exclusive", "Status": estado, "LineItems": lineas}


def _clave_idempotencia(grupo: str, cuerpo: dict) -> str:
    # ⚠️ Con franja de 10 minutos: si Xero guardara la respuesta de un fallo pasajero
    # con la misma clave, la factura quedaría bloqueada un día entero. Duplicados en
    # ventanas largas los evita la comprobación previa por número.
    base = json.dumps(cuerpo, sort_keys=True) + f"|{grupo}|{int(time.time() // 600)}"
    return "copex-" + hashlib.sha256(base.encode()).hexdigest()[:40]


def _ya_en_xero(grupo: str, numeros: list) -> tuple:
    """({número: {InvoiceID, Status}}, error). Solo facturas de venta vivas."""
    encontradas, error = {}, ""
    simples = [x for x in numeros if "," not in x and '"' not in x]
    raros = [x for x in numeros if x not in simples and '"' not in x]
    consultas = [{"InvoiceNumbers": ",".join(simples)}] if simples else []
    consultas += [{"where": f'InvoiceNumber=="{x}"'} for x in raros]
    for params in consultas:
        status, js, _h = _api(grupo, "GET", "/Invoices", params=params)
        if status != 200:
            error = "; ".join(mensajes_error(js)) or f"HTTP {status}"
            continue
        for inv in (js or {}).get("Invoices") or []:
            if (str(inv.get("Type", "")).upper() == "ACCREC"
                    and str(inv.get("Status", "")).upper() in _VIVAS):
                encontradas[str(inv.get("InvoiceNumber", ""))] = {
                    "InvoiceID": inv.get("InvoiceID", ""), "Status": inv.get("Status", "")}
    return encontradas, error


def _seguimiento(grupo: str, categoria: str, opciones: set) -> tuple:
    """(nombre EXACTO de la categoría en Xero, {opción COPEX: nombre en Xero}, avisos).

    Crea las OPCIONES que falten. ⚠️ La categoría y las opciones se casan sin
    distinguir mayúsculas, pero lo que se MANDA es el nombre tal como está en Xero:
    mandar «Project» a una organización que la tiene como «project» es apostar a
    que Xero perdone la diferencia.

    ⚠️ La CATEGORÍA no se crea: Xero admite solo dos activas, y ocupar una en la
    contabilidad del cliente sin preguntar no es cosa de COPEX. Si no existe, las
    líneas van sin seguimiento y se dice.
    """
    if not categoria or not opciones:
        return "", {}, []
    status, js, _h = _api(grupo, "GET", "/TrackingCategories")
    if status != 200:
        return "", {}, [t("The tracking categories could not be read in Xero; the invoices "
                      "go without project tracking.")]
    cat = next((c for c in (js or {}).get("TrackingCategories") or []
                if _norm(c.get("Name")) == _norm(categoria)
                and str(c.get("Status", "ACTIVE")).upper() == "ACTIVE"), None)
    if cat is None:
        return "", {}, [t("Xero has no tracking category «{c}»: create it there to get cost "
                      "and revenue per job. The invoices go without it.", c=categoria)]
    existentes = {_norm(o.get("Name")): o.get("Name") for o in cat.get("Options") or []
                  if str(o.get("Status", "ACTIVE")).upper() == "ACTIVE"}
    mapa, avisos = {}, []
    for op in sorted(opciones):
        if _norm(op) in existentes:
            mapa[op] = existentes[_norm(op)]
            continue
        st_, js2, _h = _api(grupo, "PUT",
                            f"/TrackingCategories/{cat.get('TrackingCategoryID')}/Options",
                            cuerpo={"Name": op})
        if st_ == 200:
            mapa[op] = op
        else:
            avisos.append(t("The tracking option «{o}» could not be created in Xero ({e}); "
                            "those lines go without it.",
                            o=op, e="; ".join(mensajes_error(js2)) or f"HTTP {st_}"))
    return str(cat.get("Name") or categoria), mapa, avisos


def enviar_facturas(grupo: str, fids: list) -> dict:
    """Manda facturas a Xero. {enviadas, vinculadas, errores, avisos}.

    - `enviadas`   [(fid, número, InvoiceID)] — creadas ahora.
    - `vinculadas` [(fid, número, InvoiceID)] — ya estaban en Xero con ese número:
      se ENLAZAN en vez de crear un duplicado.
    - `errores`    [(fid, número, [mensajes])].
    Nunca lanza: todo fallo vuelve como error legible.
    """
    from core import contable, invoices

    res = {"enviadas": [], "vinculadas": [], "errores": [], "avisos": []}
    with _cerrojo(grupo):
        cfg = contable.mapa(grupo)
        cuenta = str(cfg.get("cuentas", {}).get("xero", {}).get(contable.VENTAS, "")).strip()
        estado_xero = estado_envio(grupo)
        etq = contable._etiquetas(grupo)
        fichas = contable.fichas_clientes(grupo)
        seg = bool(cfg.get("seguimiento", True))
        categoria = str(cfg.get("categoria_seguimiento", "Project") or "").strip()

        docs, vistos = [], set()
        for fid in dict.fromkeys(str(x) for x in (fids or [])):
            f = invoices.get_factura(fid)
            numero = str(f.get("Number", "")) if f else ""
            if not f or _norm(f.get("Group")) != _norm(grupo):
                res["errores"].append((fid, numero, [t("Invoice not found.")]))
                continue
            if str(f.get("XeroInvoiceID", "") or "").strip():
                res["errores"].append((fid, numero, [t("It is already in Xero.")]))
                continue
            doc = contable.documento_venta(f, etq, fichas)
            problemas = []
            if doc is None:
                problemas.append(t("It is voided or has no lines."))
            else:
                if not doc["contacto"].strip():
                    problemas.append(t("It has no client name."))
                if not doc["fecha"]:
                    problemas.append(t("Its date cannot be read."))
                if doc["pct"] and abs(doc["pct"] - _GST_AU) > 1e-9:
                    problemas.append(t("Its tax is {p}% and Xero's «GST on Income» is 10%.",
                                       p=f"{doc['pct']:g}"))
                if not doc["numero"].strip():
                    problemas.append(t("It has no number."))
                elif '"' in doc["numero"]:
                    # ⚠️ No se puede buscar en Xero por ese número, y enviar sin
                    # comprobar es como aparecen duplicados.
                    problemas.append(t("Its number contains quotes and cannot be checked "
                                       "in Xero."))
                elif doc["numero"] in vistos:
                    problemas.append(t("Another invoice in this batch has the same number."))
            if not cuenta:
                problemas.append(t("No Xero sales account is set (Accounting → Chart of "
                                   "accounts)."))
            if problemas:
                res["errores"].append((fid, numero, problemas))
                continue
            vistos.add(doc["numero"])
            docs.append((fid, doc))
        if not docs:
            return res

        existentes, err = _ya_en_xero(grupo, [d["numero"] for _f, d in docs])
        if err:
            # ⚠️ Sin poder comprobar qué hay en Xero NO se envía: crear a ciegas es
            # como aparecen dos facturas con el mismo número en la contabilidad.
            for fid, doc in docs:
                res["errores"].append((fid, doc["numero"], [
                    t("Xero could not be checked for this number ({e}); nothing was sent.",
                      e=err)]))
            return res
        marcas, nuevos = {}, []
        for fid, doc in docs:
            if doc["numero"] in existentes:
                xid = existentes[doc["numero"]]["InvoiceID"]
                res["vinculadas"].append((fid, doc["numero"], xid))
                marcas[fid] = xid
            else:
                nuevos.append((fid, doc))

        cat_xero, mapa_op, avisos = "", {}, []
        if seg and nuevos:
            cat_xero, mapa_op, avisos = _seguimiento(grupo, categoria,
                                                     {ln["opcion"] for _f, d in nuevos
                                                      for ln in d["lineas"] if ln["opcion"]})
        res["avisos"] += avisos

        for i in range(0, len(nuevos), _POR_LOTE):
            lote = nuevos[i:i + _POR_LOTE]
            cuerpo = {"Invoices": [payload_factura(d, cuenta=cuenta, estado=estado_xero,
                                                   categoria=cat_xero if mapa_op else "",
                                                   opciones=mapa_op) for _f, d in lote]}
            status, js, cab = _api(grupo, "PUT", "/Invoices",
                                   params={"summarizeErrors": "false"}, cuerpo=cuerpo,
                                   cabeceras={"Idempotency-Key":
                                              _clave_idempotencia(grupo, cuerpo)})
            if status == 429:
                espera = str((cab or {}).get("Retry-After", "") or "")
                msg = t("Xero is limiting requests; try again in {s} s.", s=espera or "60")
                res["errores"] += [(fid, d["numero"], [msg]) for fid, d in lote]
                continue
            devueltas = (js or {}).get("Invoices") if isinstance(js, dict) else None
            if status not in (200, 400) or not isinstance(devueltas, list) \
                    or len(devueltas) != len(lote):
                msgs = mensajes_error(js) or [f"HTTP {status}"]
                res["errores"] += [(fid, d["numero"], msgs) for fid, d in lote]
                continue
            for (fid, doc), inv in zip(lote, devueltas):
                errs = [str(v.get("Message")) for v in inv.get("ValidationErrors") or []
                        if v.get("Message")]
                xid = str(inv.get("InvoiceID", "") or "")
                if inv.get("HasErrors") or errs or not xid \
                        or xid == "00000000-0000-0000-0000-000000000000":
                    res["errores"].append((fid, doc["numero"], errs or [t("Xero rejected it.")]))
                else:
                    res["enviadas"].append((fid, doc["numero"], xid))
                    marcas[fid] = xid

        if marcas:
            ok, msg = invoices.marcar_xero(marcas, clock.now().strftime("%Y-%m-%d %H:%M:%S"))
            if not ok:
                res["avisos"].append(t("The invoices reached Xero but could not be marked "
                                       "here ({e}); sending them again links them instead of "
                                       "duplicating.", e=msg))
    return res
