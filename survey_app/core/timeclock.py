"""
Fichaje (clock in / clock out) con persistencia en Google Sheets.

Requiere en los Secrets de Streamlit:
  TIMECLOCK_SHEET_ID = "<id de la hoja>"
  [gcp_service_account]  ...credenciales de la cuenta de servicio...

Esquema de la hoja (una fila por sesión de trabajo):
  Nombre | PIN | Proyecto | Ubicacion | Clock In | Clock Out | Horas | Estado
"""
import logging
from datetime import datetime, timedelta, date, time
from time import sleep as _dormir   # ⚠️ `time` de arriba es datetime.time, NO el módulo

import streamlit as st
from core.i18n import t
from core import clock
from core.num import num as _num

logger = logging.getLogger(__name__)

from core import columnas   # módulo HOJA: sin ciclos

HEADERS = ["Name", "PIN", "Project", "Location",
           "Clock In", "Clock Out", "Hours", "Status", "Group", "Type", "User",
           "ProjectID"]
FMT = "%Y-%m-%d %H:%M:%S"
# Tipo de fichaje: 'general' (jornada del día) | 'proyecto' (segmento por proyecto).
# Filas antiguas sin Tipo se tratan como 'proyecto'.
TIPO_GENERAL  = "general"
TIPO_PROYECTO = "project"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]



def _libro_de(_hoja) -> str:
    """El id del libro que le toca a esta hoja AHORA (v378).

    Va como primer argumento del lector cacheado para que la clave distinga
    inquilinos. No se usa dentro: `hojas.registros` resuelve el libro por su
    cuenta; aquí solo hace falta que el VALOR entre en la clave.
    """
    try:
        from core import timeclock
        return timeclock.sheet_id_para(_hoja)
    except Exception:
        return ""

def _secrets_present() -> bool:
    """Chequeo barato (sin llamada a la API): ¿existen los secrets necesarios?"""
    try:
        return bool(st.secrets.get("gcp_service_account")) and \
               bool(st.secrets.get("TIMECLOCK_SHEET_ID"))
    except Exception:
        return False


# ── Reintento acotado ante 429 / 5xx (v290) ──────────────────
# gspread NO reintenta: un pico de cuota sube como APIError y rompía el render.
# El límite de Google es 60 lecturas/min por usuario y toda la app va con UNA
# cuenta de servicio, así que un rellenado de caché puede rozarlo.
#
# ⚠️ NO usar `gspread.http_client.BackOffHTTPClient`: la propia librería lo marca
#    "not production ready", y su contador `_NR_BACKOFF` SOLO se resetea cuando
#    acierta → ante un 429 sostenido encadena 2+4+8+…+128 s = más de 4 minutos de
#    sleep DENTRO del render. Aquí el techo son ~2.1 s, que es lo que aguanta una UI.
_ESPERAS = (0.6, 1.5)
_HTTP_CLS = None


def _http_client_cls():
    """Clase de cliente HTTP con reintento acotado (import perezoso de gspread,
    igual que el resto del módulo). Se construye una sola vez."""
    global _HTTP_CLS
    if _HTTP_CLS is None:
        from gspread.http_client import HTTPClient
        from gspread.exceptions import APIError

        class _ConReintento(HTTPClient):
            def request(self, *a, **kw):
                for espera in _ESPERAS:
                    try:
                        return super().request(*a, **kw)
                    except APIError as e:
                        cod = (getattr(e, "code", None)
                               or getattr(getattr(e, "response", None), "status_code", 0)
                               or 0)
                        # Solo se reintenta lo transitorio. Un 403/404 (permisos,
                        # hoja borrada) es un error REAL: insistir solo lo tapa.
                        if cod != 429 and cod < 500:
                            raise
                        _dormir(espera)
                return super().request(*a, **kw)   # último intento: si falla, propaga

        _HTTP_CLS = _ConReintento
    return _HTTP_CLS


# ── Un libro por empresa cliente (v359) ─────────────────────────
# Hojas que viven SIEMPRE en el libro maestro: son el registro de la app, no datos de
# un cliente. `Login` además se lee ANTES de saber a qué grupo perteneces.
SHEETS_GLOBALES = {"login", "grupos", "rieles", "manuales",
                   "groups", "rails", "manuals"}

# ── Pestañas en inglés, con respaldo al nombre viejo (v465) ───────────────────
# ⚠️ Esta capa NO es cosmética y no es opcional: `get_sheet` **crea** la hoja si no
# la encuentra, así que un libro que todavía tenga `Proyectos` mientras el código
# pide `Projects` haría que la app se fabricara una pestaña VACÍA y escribiera ahí
# —sin un solo error, con los datos intactos al lado y la pantalla en blanco—. Es
# el peor modo de fallo posible porque es silencioso.
# Con el respaldo, renombrar el libro y desplegar el código dejan de tener que ser
# simultáneos: el código acepta los DOS nombres. Se retira cuando los dos libros
# estén renombrados y verificados.
LEGADO = {
    "projects": "Proyectos", "activities": "Actividades",
    "groupings": "Agrupaciones", "documents": "Documentos",
    "alerts": "Alarmas", "groups": "Grupos", "credentials": "Credenciales",
    "expenses": "Gastos", "clients": "Clientes", "invoices": "Facturas",
    "payroll": "Nominas", "assets": "Activos",
    "assetcategories": "InvCategorias", "assetmovements": "MovimientosActivo",
    "absences": "Ausencias", "jobs": "Trabajos", "toolruns": "Calculos",
    "rails": "Rieles", "audittrail": "Auditoria", "purchaseorders": "Ordenes",
    "catalogue": "Catalogo", "quotes": "Cotizaciones",
    "timecorrections": "CorreccionesFichaje", "manuals": "Manuales",
}


def titulo_real(title: str, sheet_id: str = "") -> str:
    """El título que EXISTE en ESTE libro: el nuevo si está, si no el viejo.

    ⚠️ Cuesta 0 llamadas: sale del índice que `_libro()` ya construye y cachea
    (v290). Y si el índice no se puede leer, devuelve el nombre NUEVO en vez de
    adivinar — un fallo de red no puede hacer que se escriba en otra pestaña.
    """
    _t = str(title).strip()
    _viejo = LEGADO.get(_t.lower())
    if not _viejo:
        return _t
    try:
        _hojas, _cab = _libro(sheet_id or sheet_id_para(_t))
        if _t.lower() in (_hojas or {}):
            return _t
        if _viejo.lower() in (_hojas or {}):
            return _viejo
    except Exception as e:
        logger.warning("titulo_real: no se pudo leer el indice (%s): se usa %r", e, _t)
    return _t


def _sheet_maestro() -> str:
    return str(st.secrets["TIMECLOCK_SHEET_ID"])


def sheet_id_para(title: str = "", grupo: str = None) -> str:
    """El libro que le toca a esta hoja. Vacío/desconocido → el maestro.

    ⚠️ La comprobación de GLOBAL va PRIMERO y devuelve sin consultar a `auth`: si no,
    `auth.group_sheet_id` leería `Grupos` —que es global— y se llamaría sin fin.
    """
    maestro = _sheet_maestro()
    if str(title).strip().lower() in SHEETS_GLOBALES:
        return maestro
    g = grupo
    if g is None:
        # v379: un ámbito declarado (`tenant.como_grupo`) manda sobre la sesión. Es lo
        # que permite que las vistas del PROPIETARIO recorran varios clientes: dentro
        # del `with`, toda lectura cae en el libro de ESE grupo aunque su sesión no
        # tenga ninguno. Sin esto, cada vuelta de `owner_digest` leía el maestro.
        try:
            from core import tenant
            g = tenant.grupo_activo() or None
        except Exception:
            g = None
    if g is None:
        try:                                  # como `clock.now()`: sale de la sesión (v173)
            g = str((st.session_state.get("auth") or {}).get("grupo", "") or "")
        except Exception:
            g = ""
    if not g:
        return maestro                        # propietario o sin sesión → el maestro
    try:
        from core import auth                 # perezoso: `auth` importa este módulo
        return auth.group_sheet_id(g) or maestro
    except Exception as e:
        logger.warning("timeclock: no se pudo resolver el libro de %r: %s", g, e)
        return maestro


def invalidar_libros():
    """Tras enlazar/desenlazar un libro hay que soltar los handles cacheados."""
    for fn in (_abrir, _cached_ws, _libro, get_sheet):
        try:
            fn.clear()
        except Exception as e:
            logger.warning("timeclock.invalidar_libros: %s: %s", fn, e)
    try:
        from core import hojas
        hojas.invalidar()
    except Exception:
        pass


@st.cache_resource(show_spinner=False)
def _abrir(sheet_id: str):
    """El Spreadsheet, cacheado POR LIBRO. Se autentica una vez por proceso."""
    import gspread
    from google.oauth2.service_account import Credentials
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=SCOPES)
    client = gspread.authorize(creds, http_client=_http_client_cls())
    return client.open_by_key(sheet_id)


@st.cache_resource(show_spinner=False)
def _cached_ws(sheet_id: str = ""):
    """Abre y cachea la worksheet del FICHAJE del libro que toque.

    ⚠️ `Sheet1` es por cliente, así que depende del grupo en sesión."""
    sheet_id = sheet_id or sheet_id_para("Sheet1")
    ws = _abrir(sheet_id).sheet1

    # Asegurar cabecera + migrar columnas faltantes (Grupo, Tipo, …)
    try:
        header = ws.row_values(1)
        if not header:
            ws.append_row(HEADERS)
        else:
            for i, h in enumerate(HEADERS, start=1):
                if h not in header:
                    if ws.col_count < i:
                        ws.add_cols(i - ws.col_count)
                    ws.update_cell(1, i, h)
    except Exception as e:
        # ⚠️ v323: mismo caso que en `get_sheet` — si la cabecera del fichaje no
        # migra, las escrituras por índice canónico se desalinean en silencio.
        logger.error("timeclock: no se pudo asegurar la cabecera del fichaje: %s "
                     "→ las escrituras pueden quedar desalineadas", e)
    return ws


def _get_worksheet():
    """Devuelve (worksheet, None) o (None, mensaje_error)."""
    if not _secrets_present():
        return None, t("The timeclock is not connected: credentials "
                       "(gcp_service_account) or TIMECLOCK_SHEET_ID are missing "
                       "from Secrets.")
    try:
        return _cached_ws(), None
    except Exception as e:
        # Error transitorio de la API (rate limit, red…). No es falta de config.
        return None, f"{t('Connection to Google Sheets temporarily unavailable')}: {e}"


@st.cache_resource(show_spinner=False)
def _libro(sheet_id: str = ""):
    """Índice del libro entero en 2 llamadas, en vez de 2 por hoja (v290).

    Cada `get_sheet(title)` hacía `ss.worksheet(title)` (1 llamada de metadata)
    + `row_values(1)` (1 lectura). Con las ~11 hojas del libro eso son ~22
    llamadas en un arranque frío — casi media cuota de Google (60 lecturas/min),
    que es lo que producía el 429. Aquí se traen TODAS las hojas con
    `worksheets()` (1 llamada) y TODAS las cabeceras con `values_batch_get` (1).

    Devuelve ({titulo_en_minúsculas: Worksheet}, {titulo_en_minúsculas: cabecera}).

    ⚠️ Una hoja AUSENTE del dict de cabeceras significa "no pude leerla", NO
       "está vacía". `get_sheet` debe releerla. Confundir las dos cosas
       escribiría una fila de cabecera ENCIMA de una hoja con datos.
    """
    ss = _abrir(sheet_id or sheet_id_para("Sheet1"))
    hojas = {w.title.strip().lower(): w for w in ss.worksheets()}
    cabeceras = {}
    if hojas:
        claves = list(hojas)
        try:
            # El API devuelve los valueRanges en el MISMO orden que los rangos.
            # Si vinieran menos, el zip los deja fuera → caen al respaldo. Seguro.
            resp = ss.values_batch_get([f"'{hojas[k].title}'!1:1" for k in claves])
            for k, vr in zip(claves, resp.get("valueRanges", [])):
                vals = vr.get("values") or []
                cabeceras[k] = vals[0] if vals else []
        except Exception:
            cabeceras = {}      # sin batch → cada hoja lee su cabecera, como antes
    return hojas, cabeceras


@st.cache_resource(show_spinner=False)
def get_sheet(title: str, headers: tuple, grupo: str = None):
    """Devuelve el handle de una pestaña por título, cacheado como recurso.

    Crea la hoja y asegura/migra la cabecera UNA SOLA VEZ por proceso. Se apoya
    en `_libro()` para no pagar metadata+cabecera por hoja. Si la API falla,
    lanza excepción → NO se cachea → se reintenta en la próxima llamada."""
    # v359: cada hoja se busca en SU libro (global → maestro; si no, el del grupo).
    _sid = sheet_id_para(title, grupo)
    # v465: si el libro aun tiene el nombre viejo, se usa ESE. Sin esto, la rama
    # de abajo crearia una pestaña vacia y escribiria ahi, en silencio.
    title = titulo_real(title, _sid)
    hojas, cabeceras = _libro(_sid)
    clave = title.strip().lower()
    w = hojas.get(clave)

    if w is None:
        # ⚠️ Ahora solo se crea si la hoja NO está en el listado real del libro.
        # Antes bastaba con que `ss.worksheet(title)` lanzara —incluido por un
        # error de API—, así que un hipo podía crear una hoja duplicada.
        # ⚠️ v466: antes de CREAR, se refresca el indice UNA vez y se vuelve a mirar.
        # `_libro` vive en `@st.cache_resource`, que no caduca: si una hoja se renombro
        # despues de construirlo, el proceso creeria que no existe y se fabricaria una
        # pestaña VACIA donde ponerse a escribir, con los datos intactos al lado y sin
        # un solo error. Refrescar cuesta 2 llamadas y solo ocurre en este camino.
        try:
            _libro.clear()
            hojas, cabeceras = _libro(_sid)
            title = titulo_real(title, _sid)
            clave = title.strip().lower()
            w = hojas.get(clave)
        except Exception as e:
            logger.warning("get_sheet: no se pudo refrescar el indice: %s", e)
        if w is not None:
            return w
        ss = _abrir(_sid)
        w = ss.add_worksheet(title=title, rows=500, cols=len(headers))
        w.append_row(list(headers))
        hojas[clave] = w                     # el índice sigue vivo en el proceso
        cabeceras[clave] = list(headers)
        return w

    head = cabeceras.get(clave)
    if head is None:                         # no vino en el batch → leer como antes
        head = w.row_values(1)
    if not head:
        w.append_row(list(headers))
        cabeceras[clave] = list(headers)
    else:
        # Migración: agrega columnas faltantes en su posición canónica.
        # ⚠️ v468: se compara CANONIZANDO. Con `HEADERS` en inglés y la hoja todavía
        # en español, `h not in head` daría verdadero para TODAS y este bucle
        # reescribiría la fila 1 entera a ciegas — y si el orden de la hoja no
        # coincidiera al 100 % con el de HEADERS, dejaría datos bajo la cabecera
        # equivocada. Con la canonización, una columna vieja CUENTA como presente:
        # el renombrado de la fila 1 se hace aparte, verificado, no aquí.
        _head_canon = {columnas.canon(x) for x in head}
        for i, h in enumerate(headers, start=1):
            if columnas.canon(h) not in _head_canon:
                try:
                    if w.col_count < i:
                        w.add_cols(i - w.col_count)
                    w.update_cell(1, i, h)
                    head = head + [h] if i > len(head) else head
                except Exception as e:
                    # ⚠️ v323: esto era un `pass` mudo, y es el silencio más caro
                    # del repo. Los módulos calculan la columna donde escribir con
                    # el índice CANÓNICO de `HEADERS`; si la migración falla, la
                    # hoja se queda sin esa columna y las escrituras posteriores
                    # caen **desplazadas**, guardando cada dato en la columna de al
                    # lado. Sin rastro. Se registra como ERROR, no warning.
                    logger.error("timeclock: no se pudo migrar la columna %r (pos %d) "
                                 "de la hoja %r: %s  → las escrituras de esa hoja "
                                 "pueden quedar desalineadas", h, i, clave, e)
        cabeceras[clave] = head
    return w


def is_configured() -> bool:
    """Solo revisa si los secrets están presentes — sin llamar a la API
    (evita falsos negativos por límites de rate de Google)."""
    return _secrets_present()


def _now() -> str:
    return clock.now().strftime(FMT)


def _tipo_of(r) -> str:
    """Tipo de una fila; vacío se trata como 'proyecto' (compat filas antiguas)."""
    return (str(r.get("Type", "")).strip().lower() or TIPO_PROYECTO)


def pid_of(r) -> str:
    """ProyectoID de una fila de fichaje ('' en las filas anteriores a v145)."""
    return str(r.get("ProjectID", "")).strip()


def es_del_proyecto(r, pid: str, nombre: str) -> bool:
    """¿Este fichaje es de este proyecto? **ID primero, nombre como respaldo.**

    Mismo criterio que `_matches` usa con Usuario desde v106: las filas antiguas
    (sin ProyectoID) caen al nombre, normalizado sin may/min ni espacios.

    ⚠️ El nombre NO es identidad estable: renombrar un proyecto desligaba todo su
    historico de horas, y con el el costo de mano de obra. Por eso el ID manda.
    """
    rp = pid_of(r)
    if rp and pid:
        return rp == str(pid).strip()
    return (str(r.get("Project", "")).strip().casefold()
            == str(nombre or "").strip().casefold())


def mapa_nombres(grupo: str = "") -> dict:
    """{nombre_normalizado: [usuarios]} de las cuentas del grupo.

    Se calcula UNA vez por consulta y se pasa a `clave_de` en el bucle: `list_users`
    está cacheado, así que no cuesta llamadas, pero sí reconstruir el dict por fila.
    """
    from core import auth                  # perezoso: `auth` importa este módulo
    out = {}
    try:
        for u in auth.list_users(grupo):
            n = str(u.get("Name", "")).strip().casefold()
            if n:
                out.setdefault(n, []).append(str(u.get("User", "")).strip())
    except Exception as e:                 # sin Login legible no se resuelve nada,
        logger.warning("timeclock.mapa_nombres: %s", e)   # pero tampoco se rompe
    return out


def clave_de(r, por_nombre: dict = None) -> str:
    """La IDENTIDAD de un fichaje: el login si la fila lo trae; si no, resuelto por nombre.

    ⚠️ v363 — ÚNICA definición. Los fichajes anteriores a v106 no tienen columna
    `Usuario`, así que caían bajo su NOMBRE y **la misma persona salía partida en dos**:
    en producción, `campo1` (login) y `lksdfkldsf` (su nombre) son la misma y la pantalla
    de Horas la mostraba como dos filas, con las horas y el costo repartidos.

    v362 arregló esto en `expenses.labor_breakdown` y **el mismo patrón estaba copiado
    en 5 funciones más** (`group_hours`, `jornada_y_proyecto`, `horas_por_usuario_rango`,
    `proyectos_por_usuario_dia`, `spend_curve`), todas sin arreglar. Es exactamente el
    fallo de los cinco `_num` divergentes de v323: la misma regla escrita seis veces
    diverge en cuanto se toca una. Por eso vive aquí y las seis la llaman.

    ⚠️ El nombre solo se resuelve si pertenece a UNA sola cuenta: con homónimos
    —los hubo, `fijiofgjei` tenía dos— adivinar MEZCLARÍA a dos personas distintas,
    que es peor que dejarlas separadas.
    """
    u = str(r.get("User", "")).strip()
    if u:
        return u
    nom = str(r.get("Name", "")).strip()
    cand = (por_nombre or {}).get(nom.casefold(), [])
    return cand[0] if len(cand) == 1 else nom


def _matches(r, usuario: str, nombre: str, grupo: str) -> bool:
    """¿La fila es de este usuario? Identifica por **Usuario** (login, v106); las filas
    antiguas sin Usuario caen al Nombre visible."""
    if str(r.get("Group", "")).strip() != (grupo or "").strip():
        return False
    ru = str(r.get("User", "")).strip()
    if ru:
        return ru.lower() == (usuario or "").strip().lower()
    return str(r.get("Name", "")).strip() == (nombre or "").strip()


def clock_in(nombre: str, proyecto: str, ubicacion: str, grupo: str = "",
             tipo: str = TIPO_PROYECTO, usuario: str = "",
             proyecto_id: str = "", in_ts=None) -> tuple:
    """Registra un clock in (tipo 'general' o 'proyecto'). Devuelve (ok, mensaje).
    Un usuario puede tener a la vez UNA sesión general y UNA de proyecto abiertas.

    `in_ts` (datetime o str) permite fichar a una hora distinta de «ahora»: es el
    olvido de ENTRADA (v461) — llegué a las 7:00 y me acuerdo de fichar a las 9:00.
    ⚠️ Es el gemelo del `out_ts` que `clock_out` tiene desde v164; aquella versión
    resolvió la salida olvidada y dejó la entrada sin arreglo posible.
    """
    ws, err = _get_worksheet()
    if err:
        return False, err
    nombre = (nombre or "").strip()
    grupo  = (grupo or "").strip()
    tipo   = (tipo or TIPO_PROYECTO).strip().lower()
    if not nombre:
        return False, t("No user is signed in.")

    try:
        records = columnas.canonizar(ws.get_all_records(numericise_ignore=['all']))
    except Exception as e:
        return False, f"{t('Error reading the sheet')}: {e}"

    # ¿Ya hay una sesión abierta del MISMO tipo para este usuario+grupo?
    for r in records:
        if (_matches(r, usuario, nombre, grupo)
                and str(r.get("Status", "")).strip().upper() == "ABIERTO"
                and _tipo_of(r) == tipo):
            etq = t("workday") if tipo == TIPO_GENERAL else t("project")
            return False, (f"{t('You already have a clock in for')} {etq} "
                           f"{t('open since')} {r.get('Clock In')}.")

    # ⚠️ La hora se normaliza ANTES de escribir: la fila es POSICIONAL y este
    # valor va a la columna «Clock In», que es la que todo lo demás parsea.
    if in_ts is None:
        in_ts = _now()
    elif hasattr(in_ts, "strftime"):
        in_ts = in_ts.strftime(FMT)
    else:
        in_ts = str(in_ts)
    try:
        ws.append_row([nombre, "", proyecto or "", ubicacion or "",
                       in_ts, "", "", "ABIERTO", grupo, tipo, usuario or "",
                       str(proyecto_id or "")],
                      value_input_option="RAW")
    except Exception as e:
        return False, f"{t('Error writing the timeclock entry')}: {e}"
    _invalidate_records()
    etq = t("Workday (general)") if tipo == TIPO_GENERAL else t("Project")
    return True, f"✅ Clock IN {etq} {t('at')} {in_ts}."


def clock_out(nombre: str, grupo: str = "", tipo: str = TIPO_PROYECTO,
              usuario: str = "", out_ts=None) -> tuple:
    """Cierra la sesión abierta (del tipo indicado) de nombre+grupo. Devuelve (ok, mensaje).

    `out_ts` (datetime o str) permite cerrar a una hora distinta de «ahora»: lo usa
    el cierre de una sesión OLVIDADA de un día anterior (v164), para no registrar
    como trabajadas las horas de la noche que nadie hizo. Por defecto = ahora.
    """
    ws, err = _get_worksheet()
    if err:
        return False, err
    nombre = (nombre or "").strip()
    grupo  = (grupo or "").strip()
    tipo   = (tipo or TIPO_PROYECTO).strip().lower()
    if not nombre:
        return False, t("No user is signed in.")

    try:
        records = columnas.canonizar(ws.get_all_records(numericise_ignore=['all']))
    except Exception as e:
        return False, f"{t('Error reading the sheet')}: {e}"

    # Buscar la sesión abierta más reciente del tipo (de abajo hacia arriba)
    target_row = None
    target_in  = None
    for idx, r in enumerate(records):
        if (_matches(r, usuario, nombre, grupo)
                and str(r.get("Status", "")).strip().upper() == "ABIERTO"
                and _tipo_of(r) == tipo):
            target_row = idx + 2   # +2: fila 1 = cabecera, records 0-indexado
            target_in  = str(r.get("Clock In", ""))

    if target_row is None:
        etq = t("workday") if tipo == TIPO_GENERAL else t("project")
        return False, f"{t('You have no open clock in for')} {etq}."

    if out_ts is None:
        out_ts = _now()
    elif hasattr(out_ts, "strftime"):
        out_ts = out_ts.strftime(FMT)
    else:
        out_ts = str(out_ts)
    horas  = ""
    try:
        t_in  = datetime.strptime(target_in, FMT)
        t_out = datetime.strptime(out_ts, FMT)
        horas = round((t_out - t_in).total_seconds() / 3600.0, 2)
    except Exception:
        horas = ""

    try:
        # UNA sola escritura. Antes eran 3 update_cell = hasta 5 llamadas por salida.
        # Con todo el equipo fichando a la misma hora es justo el escenario del 429
        # que v80 arreglo en los proyectos. Columnas: F=Clock Out, G=Horas, H=Estado.
        ws.batch_update([{"range": f"F{target_row}:H{target_row}",
                          "values": [[out_ts, str(horas), "CERRADO"]]}],
                        value_input_option="RAW")
    except Exception as e:
        return False, f"{t('Error updating the timeclock entry')}: {e}"

    _invalidate_records()
    return True, (f"✅ Clock OUT {t('at')} {out_ts}. "
                  f"{t('Hours worked')}: {horas}.")


def corregir_fichaje(grupo, usuario, nombre, tipo, campo,
                     valor_actual, valor_nuevo) -> tuple:
    """Cambia la hora de entrada o de salida de UN fichaje. Devuelve (ok, msg).

    ⚠️ La fila se localiza por **usuario + hora actual + tipo**, no por su número:
    las filas se desplazan y una referencia posicional envejece mal. Esa terna es
    única — un usuario no puede tener dos fichajes del mismo tipo abiertos al mismo
    segundo (`clock_in` lo impide).

    ⚠️ **Las Horas se recalculan aquí.** Si se cambiara solo el timestamp, la
    columna `Horas` seguiría con el valor viejo y `_row_segmentos` la respeta para
    las filas cerradas de un solo día (v164) — o sea que la corrección no movería
    ni la nómina ni el costo de la obra, y nadie lo notaría.
    """
    ws, err = _get_worksheet()
    if err:
        return False, err
    campo = str(campo or "").strip()
    if campo not in ("Clock In", "Clock Out"):
        return False, t("Only the clock in or the clock out can be corrected.")
    if hasattr(valor_nuevo, "strftime"):
        valor_nuevo = valor_nuevo.strftime(FMT)
    valor_nuevo = str(valor_nuevo or "").strip()
    valor_actual = str(valor_actual or "").strip()
    try:
        registros = columnas.canonizar(ws.get_all_records(numericise_ignore=['all']))
    except Exception as e:
        return False, f"{t('Error reading the sheet')}: {e}"

    fila = None
    for i, r in enumerate(registros):
        if (_matches(r, usuario, nombre, grupo)
                and _tipo_of(r) == str(tipo or "").strip().lower()
                and str(r.get(campo, "")).strip() == valor_actual):
            fila, actual = i + 2, r
    if fila is None:
        return False, t("That time entry no longer exists with the given time.")

    _ci = valor_nuevo if campo == "Clock In" else str(actual.get("Clock In", ""))
    _co = valor_nuevo if campo == "Clock Out" else str(actual.get("Clock Out", ""))
    # ⚠️ Una sesión ABIERTA no tiene salida: sus horas se calculan al vuelo contra
    # el reloj, así que la columna se deja vacía en vez de escribir un 0 que
    # parecería una jornada de cero horas (el cero silencioso de v346).
    horas = ""
    if _ci and _co:
        try:
            _t0, _t1 = datetime.strptime(_ci, FMT), datetime.strptime(_co, FMT)
            if _t1 <= _t0:
                return False, t("The clock out must be after the clock in.")
            horas = round((_t1 - _t0).total_seconds() / 3600.0, 2)
        except Exception:
            horas = ""

    col = "E" if campo == "Clock In" else "F"
    try:
        _w = [{"range": f"{col}{fila}", "values": [[valor_nuevo]]}]
        if horas != "":
            _w.append({"range": f"G{fila}", "values": [[str(horas)]]})
        ws.batch_update(_w, value_input_option="RAW")
    except Exception as e:
        return False, f"{t('Error updating the timeclock entry')}: {e}"
    _invalidate_records()
    return True, f"{campo} → {valor_nuevo}"


@st.cache_data(ttl=120, show_spinner=False)
def _cached_records_cached(libro: str) -> list:
    """Filas del fichaje CACHEADAS (solo para lecturas de display: estado del reloj,"""
    from core import hojas          # perezoso: evita el ciclo con timeclock
    return hojas.registros("Sheet1", HEADERS) or []




def _cached_records():
    """Envoltorio: resuelve el libro y delega en la versión cacheada (v378).

    ⚠️ El id del libro va en la CLAVE de caché. Sin él, `st.cache_data` —que se
    comparte por PROCESO— servía al segundo cliente lo que dejó memoizado el
    primero: una fuga de datos entre inquilinos, no un problema de rendimiento.
    """
    return _cached_records_cached(_libro_de("Sheet1"))
def _invalidate_records():
    # ⚠️ v339: además de la caché propia hay que tirar el LOTE compartido
    # (`hojas._lote`). Si no, tras escribir, el dato seguiría saliendo del lote
    # cacheado hasta 120 s y parecería que no se guardó.
    from core import hojas
    hojas.invalidar()
    try:
        _cached_records_cached.clear()
    except Exception:
        pass


def elapsed_seconds(clock_in_str) -> int:
    """Segundos transcurridos desde un Clock In (para el cronómetro)."""
    try:
        return max(0, int((clock.now() - datetime.strptime(str(clock_in_str), FMT)).total_seconds()))
    except Exception:
        return 0


def _segmentos_dia(ci_str, fin_dt) -> list:
    """Parte el tramo [ci, fin] en segmentos por DÍA NATURAL: [(date, horas), …].

    Un fichaje que cruza medianoche (turno de noche o clock-out olvidado) NO es de
    un solo día: 21:00→05:00 son ~3 h del día 1 y ~5 h del día 2. Repartir así deja
    que «hoy» y el costo de M.O. caigan en el día correcto (v164). La suma de los
    segmentos = la duración total, así que los agregados por-usuario no cambian.
    """
    try:
        ci = datetime.strptime(str(ci_str), FMT)
    except Exception:
        return []
    if not isinstance(fin_dt, datetime) or fin_dt <= ci:
        return []
    segs, cur = [], ci
    while cur.date() < fin_dt.date():
        medianoche = datetime.combine(cur.date() + timedelta(days=1), time.min)
        segs.append((cur.date(), (medianoche - cur).total_seconds() / 3600.0))
        cur = medianoche
    segs.append((cur.date(), (fin_dt - cur).total_seconds() / 3600.0))
    return segs


def _row_segmentos(r) -> list:
    """Segmentos por día de UNA fila de fichaje. Abierta = hasta ahora; cerrada =
    hasta el Clock Out. Si la salida no parsea, cae a las Horas guardadas (1 día)."""
    ci = str(r.get("Clock In", ""))
    if str(r.get("Status", "")).strip().upper() == "ABIERTO":
        return _segmentos_dia(ci, clock.now())
    try:
        fin = datetime.strptime(str(r.get("Clock Out", "")), FMT)
    except Exception:
        try:
            d = datetime.strptime(ci, FMT).date()
        except Exception:
            return []
        h = _num(r.get("Hours"))
        return [(d, h)] if h > 0 else []
    segs = _segmentos_dia(ci, fin)
    # Fila cerrada de UN solo día: respeta las Horas GUARDADAS (lo que ya veía el
    # reporte del admin) en vez de recomputar del timestamp → el total con days=None
    # queda IDÉNTICO. Solo las que cruzan medianoche se reparten por segmento.
    if len(segs) == 1:
        h = _num(r.get("Hours"))
        return [(segs[0][0], h)] if h > 0 else []
    return segs


def open_sessions(nombre: str, grupo: str = "", usuario: str = "") -> dict:
    """{'general': {clock_in,proyecto}|None, 'proyecto': {...}|None} de sesiones ABIERTAS."""
    out = {TIPO_GENERAL: None, TIPO_PROYECTO: None}
    try:
        for r in _cached_records():          # lectura cacheada (display)
            if (_matches(r, usuario, nombre, grupo)
                    and str(r.get("Status", "")).strip().upper() == "ABIERTO"):
                out[_tipo_of(r)] = {"clock_in": str(r.get("Clock In", "")),
                                    "proyecto": str(r.get("Project", "")),
                                    "proyecto_id": pid_of(r)}
    except Exception:
        pass
    return out


def open_now(grupo: str) -> list:
    """Sesiones ABIERTAS ahora mismo en el grupo (para el 'estado en vivo', v281):
    [{usuario, nombre, tipo, proyecto, proyecto_id, clock_in, segundos}]."""
    out = []
    try:
        for r in _cached_records():
            if str(r.get("Group", "")).strip() != str(grupo).strip():
                continue
            if str(r.get("Status", "")).strip().upper() != "ABIERTO":
                continue
            _ci = str(r.get("Clock In", ""))
            out.append({"usuario": str(r.get("User", "")), "nombre": str(r.get("Name", "")),
                        "tipo": _tipo_of(r), "proyecto": str(r.get("Project", "")),
                        "proyecto_id": pid_of(r), "clock_in": _ci,
                        "segundos": elapsed_seconds(_ci)})
    except Exception:
        pass
    return out


def fichar_proyecto(nombre: str, proyecto: str, grupo: str = "", usuario: str = "",
                    proyecto_id: str = "") -> tuple:
    """Ficha a un proyecto y, si no hay jornada general abierta, la abre tambien.

    Decision del usuario (v150): los dos relojes son para TODOS, pero sin cobrar
    un toque extra cada mañana. La jornada general es el tiempo pagado y el
    segmento de proyecto es a que se imputa; `group_hours` deriva de ahi
    `sin_asignar` (traslados y espera). Si el proyecto pudiera ficharse sin
    jornada, ese numero dejaria de significar nada.

    Devuelve (ok, mensaje, jornada_abierta_automaticamente).
    """
    abiertas = open_sessions(nombre, grupo, usuario)
    auto = False
    if not abiertas.get(TIPO_GENERAL):
        ok_g, _ = clock_in(nombre, "", "", grupo, tipo=TIPO_GENERAL, usuario=usuario)
        auto = bool(ok_g)
    ok, msg = clock_in(nombre, proyecto, "", grupo, tipo=TIPO_PROYECTO,
                       usuario=usuario, proyecto_id=proyecto_id)
    return ok, msg, auto


def cerrar_jornada(nombre: str, grupo: str = "", usuario: str = "") -> tuple:
    """Cierra la jornada general y, de paso, el segmento de proyecto si sigue abierto."""
    abiertas = open_sessions(nombre, grupo, usuario)
    if abiertas.get(TIPO_PROYECTO):
        clock_out(nombre, grupo, tipo=TIPO_PROYECTO, usuario=usuario)
    return clock_out(nombre, grupo, tipo=TIPO_GENERAL, usuario=usuario)


def resumen_hoy(nombre: str, grupo: str = "", usuario: str = "") -> dict:
    """Horas de HOY de esta persona: jornada, imputado a proyectos y sin asignar.

    El cronometro solo dice cuanto llevas desde que fichaste; esto dice cuanto
    llevas EN EL DIA, que es lo que se quiere saber. Dia natural, no ultimas 24 h.
    """
    hoy = clock.now().date()
    out = {"general": 0.0, "proyecto": 0.0, "sin_asignar": 0.0, "por_proyecto": {}}
    for r in _cached_records():                      # lectura cacheada (display)
        if not _matches(r, usuario, nombre, grupo):
            continue
        # Solo el segmento de HOY: una sesión que empezó ayer y sigue —o cerró hoy
        # de madrugada— aporta sus horas de hoy, no 0 (antes se descartaba la fila
        # entera si el Clock In no era hoy, y el cronómetro decía otra cosa).
        h = sum(hh for d, hh in _row_segmentos(r) if d == hoy)
        if h <= 0:
            continue
        if _tipo_of(r) == TIPO_GENERAL:
            out["general"] += h
        else:
            out["proyecto"] += h
            pn = _nombre_actual(pid_of(r), r.get("Project", "")) or t("(no project)")
            out["por_proyecto"][pn] = round(out["por_proyecto"].get(pn, 0.0) + h, 2)
    out["general"] = round(out["general"], 2)
    out["proyecto"] = round(out["proyecto"], 2)
    out["sin_asignar"] = round(max(0.0, out["general"] - out["proyecto"]), 2)
    return out


def resumen_semana(nombre: str, grupo: str = "", usuario: str = "") -> dict:
    """Horas de esta persona en la SEMANA EN CURSO (lunes → hoy): {general, proyecto, dias}.

    Es la pregunta que se hace quien ficha ("¿cuánto llevo esta semana?"), y no se podía
    responder: `resumen_hoy` solo cuenta el día. Misma fuente cacheada, así que **no añade
    ni una lectura de Sheets** ([[constraint-cuota-sheets]]).

    ⚠️ Semana NATURAL desde el lunes, no "últimas 168 horas": un lunes por la mañana
    tiene que decir ~0, no arrastrar el viernes anterior. `group_hours(days=7)` es una
    ventana móvil y por eso no vale aquí (además, con `days=0` se interpretaría como
    'todo el histórico').
    """
    hoy = clock.now(grupo).date()
    lunes = hoy - timedelta(days=hoy.weekday())
    out = {"general": 0.0, "proyecto": 0.0, "dias": 0}
    _dias = set()
    for r in _cached_records():                      # lectura cacheada (display)
        if not _matches(r, usuario, nombre, grupo):
            continue
        for d, hh in _row_segmentos(r):
            if hh <= 0 or not (lunes <= d <= hoy):
                continue
            if _tipo_of(r) == TIPO_GENERAL:
                out["general"] += hh
                _dias.add(d)
            else:
                out["proyecto"] += hh
    out["general"] = round(out["general"], 2)
    out["proyecto"] = round(out["proyecto"], 2)
    out["dias"] = len(_dias)                         # días con jornada abierta
    return out


def mis_fichajes(nombre: str, grupo: str = "", usuario: str = "", limite: int = 8) -> list:
    """Los ultimos fichajes de esta persona (los suyos, no los del grupo)."""
    filas = []
    for r in _cached_records():
        if not _matches(r, usuario, nombre, grupo):
            continue
        filas.append({
            "tipo": _tipo_of(r),
            "proyecto": _nombre_actual(pid_of(r), r.get("Project", "")),
            "entrada": str(r.get("Clock In", "")),
            "salida": str(r.get("Clock Out", "")),
            "horas": _num(r.get("Hours")),
            "abierto": str(r.get("Status", "")).strip().upper() == "ABIERTO",
        })
    filas.sort(key=lambda x: x["entrada"], reverse=True)
    return filas[:limite]


def switch_project(nombre: str, grupo: str, new_proyecto: str, ubicacion: str = "",
                   usuario: str = "", new_pid: str = "") -> tuple:
    """Cambia de proyecto en 1 toque: cierra el segmento activo (si hay) y abre el nuevo."""
    clock_out(nombre, grupo, tipo=TIPO_PROYECTO, usuario=usuario)   # si no hay, se ignora
    return clock_in(nombre, new_proyecto, ubicacion, grupo, tipo=TIPO_PROYECTO,
                    usuario=usuario, proyecto_id=new_pid)


def _nombre_actual(pid: str, nombre_fila: str) -> str:
    """Nombre vigente del proyecto a partir de su ID; si no hay ID, el de la fila.

    Import perezoso a proposito: `projects` importa `timeclock`, asi que arriba
    seria una dependencia circular.
    """
    nom = str(nombre_fila or "").strip()
    if not str(pid or "").strip():
        return nom
    try:
        from core import projects as P
        prj = P.get_project(str(pid).strip())
        return str(prj.get("Name", "")).strip() or nom if prj else nom
    except Exception:
        return nom


def proyectos_por_usuario_dia(grupo: str, fecha) -> dict:
    """{clave_usuario: [{'pid','nombre'}]} de los proyectos que cada persona FICHÓ
    ese día (segmentos de tipo proyecto). Para el 'plan vs real' del roster (v161):
    comparar donde se le ASIGNÓ contra donde ficho de verdad."""
    if isinstance(fecha, date) and not isinstance(fecha, datetime):
        fecha_d = fecha
    else:
        try:
            fecha_d = datetime.strptime(str(fecha)[:10], "%Y-%m-%d").date()
        except Exception:
            return {}
    out = {}
    _pn = mapa_nombres(grupo)               # v363: resolver identidad una sola vez
    for r in _cached_records():
        if str(r.get("Group", "")).strip() != str(grupo).strip():
            continue
        if _tipo_of(r) != TIPO_PROYECTO:
            continue
        # Cuenta el proyecto en CADA día que se trabajó (no solo el del Clock In):
        # un segmento nocturno que cruza medianoche se trabajó en los dos días.
        if fecha_d not in {d for d, hh in _row_segmentos(r) if hh > 0}:
            continue
        clave = clave_de(r, _pn)
        entry = {"pid": pid_of(r),
                 "nombre": _nombre_actual(pid_of(r), r.get("Project", ""))}
        if not entry["pid"] and not entry["nombre"]:
            continue                              # fichaje sin proyecto: nada que comparar
        out.setdefault(clave, [])
        if entry not in out[clave]:
            out[clave].append(entry)
    return out


def horas_por_usuario_rango(grupo: str, desde, hasta) -> dict:
    """{clave: {nombre, horas}} — horas de JORNADA (general) por usuario en [desde, hasta].

    Para la nómina (pago por periodo). Usa los segmentos por día (v164), así una
    sesión que cruza medianoche cuenta el tramo real de cada día dentro del rango.
    `desde`/`hasta` son date; el rango es inclusivo.
    """
    grupo = (grupo or "").strip()
    # `desde`/`hasta` pueden llegar como date (date_input) o como ISO string
    # (payroll.generar pasa `.isoformat()`). Los segmentos son `date`, así que hay
    # que comparar date con date (str <= date → TypeError).
    from datetime import date as _date, datetime as _datetime

    def _to_date(v):
        if isinstance(v, _datetime):
            return v.date()
        if isinstance(v, _date):
            return v
        try:
            return _datetime.strptime(str(v)[:10], "%Y-%m-%d").date()
        except Exception:
            return None
    desde, hasta = _to_date(desde), _to_date(hasta)
    if desde is None or hasta is None:
        return {}
    out = {}
    _pn = mapa_nombres(grupo)               # v363: resolver identidad una sola vez
    for r in _cached_records():
        if str(r.get("Group", "")).strip() != grupo:
            continue
        if _tipo_of(r) != TIPO_GENERAL:
            continue
        clave = clave_de(r, _pn)
        nombre = str(r.get("Name", "")).strip() or clave
        if not clave:
            continue
        h = sum(hh for d, hh in _row_segmentos(r) if desde <= d <= hasta)
        if h <= 0:
            continue
        a = out.setdefault(clave, {"nombre": nombre, "horas": 0.0})
        a["horas"] += h
    return {k: {"nombre": v["nombre"], "horas": round(v["horas"], 2)} for k, v in out.items()}


def horas_por_usuario_dia(grupo: str, desde, hasta) -> dict:
    """`{clave: {date: horas}}` — jornada fichada de cada persona, DÍA A DÍA.

    Mismo recorrido y mismos segmentos que `horas_por_usuario_rango` (v164), solo que
    sin agregar: lo necesita `ausencias.horas_pagadas_grupo` para no pagar dos veces
    el mismo día. Un total por periodo no sirve ahí — hay que saber QUÉ días.
    """
    from datetime import date as _date, datetime as _datetime

    def _to_date(v):
        if isinstance(v, _datetime):
            return v.date()
        if isinstance(v, _date):
            return v
        try:
            return _datetime.strptime(str(v)[:10], "%Y-%m-%d").date()
        except Exception:
            return None
    desde, hasta = _to_date(desde), _to_date(hasta)
    if desde is None or hasta is None:
        return {}
    grupo = (grupo or "").strip()
    out = {}
    _pn = mapa_nombres(grupo)
    for r in _cached_records():
        if str(r.get("Group", "")).strip() != grupo:
            continue
        if _tipo_of(r) != TIPO_GENERAL:
            continue
        clave = clave_de(r, _pn)
        if not clave:
            continue
        for d, hh in _row_segmentos(r):
            if desde <= d <= hasta and hh > 0:
                _u = out.setdefault(clave, {})
                _u[d] = round(_u.get(d, 0.0) + hh, 2)
    return out


def jornada_y_proyecto(grupo: str, desde=None, hasta=None) -> dict:
    """`{clave: {nombre, jornada, proyecto}}` — horas de JORNADA y horas IMPUTADAS a
    proyectos de cada persona en [desde, hasta] (fechas `date`; None = todo).

    Es el dato que hacía falta para conciliar (v313): el modelo del negocio es
    **se paga la jornada** (esté o no en un proyecto) y **se carga a la obra lo
    imputado**, así que la diferencia entre las dos columnas ES el hueco entre lo
    que sale de caja y lo que se le puede cobrar al cliente. `group_hours` no vale
    aquí porque su ventana es móvil (`days`) y el P&L trabaja con un rango.

    ⚠️ v422 — `proyecto` cuenta SOLO las horas imputadas a una OBRA. Las fichadas a una
    localización interna (oficina, almacén) van aparte, en `interno`. No es un matiz de
    presentación: `conciliacion_mo` llama `cargado` a `proyecto × tarifa` y lo rotula
    «cargado a obras», que es literalmente *lo que se le cobra al cliente*. Sin separar,
    el primer fichaje en la oficina habría inflado esa cifra con overhead que nadie
    factura, y el número habría cambiado de significado sin que nadie lo notara.
    ⚠️ La cadena de v313 sigue cerrando igual: lo interno pasa a contarse como jornada
    no imputada, que es exactamente lo que es.
    """
    grupo = (grupo or "").strip()
    out = {}
    _pn = mapa_nombres(grupo)               # v363: resolver identidad una sola vez
    _int = _ids_internos(grupo)             # v422: qué PRJ-#### son estructura
    for r in _cached_records():
        if str(r.get("Group", "")).strip() != grupo:
            continue
        clave = clave_de(r, _pn)
        if not clave:
            continue
        h = sum(hh for d, hh in _row_segmentos(r)
                if (desde is None or d >= desde) and (hasta is None or d <= hasta))
        if h <= 0:
            continue
        a = out.setdefault(clave, {"nombre": str(r.get("Name", "")).strip() or clave,
                                   "jornada": 0.0, "proyecto": 0.0, "interno": 0.0})
        if _tipo_of(r) == TIPO_GENERAL:
            a["jornada"] += h
        elif str(r.get("ProjectID", "")).strip() in _int:
            a["interno"] += h
        else:
            a["proyecto"] += h
    for a in out.values():
        for k in ("jornada", "proyecto", "interno"):
            a[k] = round(a[k], 2)
    return out


@st.cache_data(ttl=120, show_spinner=False)
def _ids_internos(grupo: str) -> set:
    """{PRJ-####} de las localizaciones internas del grupo (v422).

    ⚠️ La clave de caché es el GRUPO, y con eso basta para no repetir la fuga entre
    inquilinos de v378: allí la clave era solo el título de la hoja mientras el libro
    salía de la sesión; aquí cada grupo tiene su libro, así que `grupo` es una clave
    MÁS específica que el libro, no menos. Y no empieza por guión bajo — que es lo que
    dejó inerte aquel arreglo, porque `st.cache_data` excluye de la clave los
    argumentos cuyo nombre empieza por `_`.

    Incluye las cerradas: una localización que se cierra no des-hace las horas que se
    le ficharon, y seguirlas contando como obra las convertiría en facturables.
    """
    try:
        from core import projects as P
        return {str(p.get("ID", "")) for p in P.list_locations(grupo, incluir_cerradas=True)}
    except Exception:
        return set()


def group_hours(grupo: str, days=None) -> list:
    """Resumen de horas por usuario del grupo (para el admin). days=None=todo, 7=semana.
    Devuelve [{usuario, general, proyecto, interno, sin_asignar, por_proyecto{nombre:horas}}].
    Las sesiones abiertas cuentan con el tiempo transcurrido hasta ahora.

    ⚠️ v422: `proyecto` y `costo` son SOLO obra; el trabajo en oficina/almacén va en
    `interno`/`costo_interno`. El KPI que come esto se llama «M.O. cargada a obras»
    (v320) y meterle estructura lo haría mentir. `por_proyecto` sí las lista —esa
    tabla responde *dónde puso su tiempo*, y el almacén es una respuesta legítima."""
    records = _cached_records()             # lectura cacheada (display)
    grupo = (grupo or "").strip()
    desde = (clock.now() - timedelta(days=days)).date() if days else None
    agg = {}
    _pn = mapa_nombres(grupo)               # v363: resolver identidad una sola vez
    _int = _ids_internos(grupo)             # v422: qué PRJ-#### son estructura
    for r in records:
        if str(r.get("Group", "")).strip() != grupo:
            continue
        # Clave por USUARIO (login); las filas antiguas sin Usuario se resuelven por
        # su Nombre contra las cuentas del grupo (v363, `clave_de`).
        clave  = clave_de(r, _pn)
        nombre = str(r.get("Name", "")).strip() or clave
        if not clave:
            continue
        # Horas por DÍA de la fila, filtradas a la ventana. Partir en medianoche hace
        # que «Hoy»/«Semana» cuenten el tramo REAL de cada día: una sesión que cruzó
        # medianoche ya no se excluye entera (por el día del Clock In) ni se cuenta
        # toda en un solo día. Con days=None (Todo) el total es IDÉNTICO al anterior,
        # porque Σsegmentos = duración de la fila.
        h = sum(hh for d, hh in _row_segmentos(r) if desde is None or d >= desde)
        if h <= 0:
            continue
        a = agg.setdefault(clave, {"general": 0.0, "proyecto": 0.0, "interno": 0.0,
                                   "por": {}, "nombre": nombre})
        if _tipo_of(r) == TIPO_GENERAL:
            a["general"] += h
        else:
            a["interno" if str(pid_of(r)).strip() in _int else "proyecto"] += h
            # Con ID se resuelve al nombre ACTUAL: si el proyecto se renombro,
            # sus horas viejas ya no salen bajo dos etiquetas distintas.
            pn = _nombre_actual(pid_of(r), r.get("Project", "")) or t("(no project)")
            a["por"][pn] = a["por"].get(pn, 0.0) + h
    # Tarifa/hora por usuario, para el costo de mano de obra (misma fuente que
    # expenses.labor_cost). Import perezoso: auth no depende de timeclock.
    try:
        from core import auth
        rates = auth.rate_map(grupo)
        # v325: sin grupo → alguien movido de grupo sigue existiendo y no se
        # puede decir que "ya no está".
        conocidas = auth.claves_conocidas()
    except Exception:
        rates, conocidas = {}, set()

    out = []
    for clave, a in agg.items():
        gen, pro, itn = a["general"], a["proyecto"], a["interno"]
        # ⚠️ `sin_asignar` = jornada − proyectos SOLO tiene sentido si la jornada
        # cubre lo imputado. Si se imputo a proyectos MAS que la jornada abierta
        # (fichajes de proyecto sin abrir jornada, lo normal antes de v150), el
        # resultado es INDETERMINADO, no 0: marcarlo en vez de un cero que engaña.
        # Umbral de 3 min: por debajo es ruido de redondeo (dos tramos que cierran
        # con segundos de diferencia), no un dato realmente incompleto.
        indet = (pro + itn) > gen + 0.05
        tarifa = float(rates.get(clave, 0.0) or 0.0)
        out.append({
            "usuario": clave,
            "nombre": a.get("nombre", clave),
            "general": round(gen, 2),
            "proyecto": round(pro, 2),
            # v422: la jornada se reparte en obra + estructura + lo que aún no se sabe.
            # Restar `itn` hace que «sin asignar» signifique de verdad «sin explicar»,
            # en vez de mezclar el trabajo de oficina con el hueco. Con 0 localizaciones
            # `itn` vale 0 y NINGUNA cifra actual se mueve.
            "interno": round(itn, 2),
            "sin_asignar": round(max(0.0, gen - pro - itn), 2),
            "sin_asignar_indet": indet,
            "tarifa": tarifa,
            # v325: ¿sigue dada de alta? Si no, su tarifa 0 no es "falta ponerla"
            # sino "no hay fila donde ponerla". Sin `conocidas` (fallo al leer) se
            # asume que sí, para no acusar de baja a nadie por un error de lectura.
            "existe": (not conocidas) or clave in conocidas
                      or a.get("nombre", "") in conocidas,
            "costo": round(pro * tarifa, 2),      # costo = horas imputadas A OBRA × tarifa
            "costo_interno": round(itn * tarifa, 2),   # v422: estructura, no se factura
            "por_proyecto": {k: round(v, 2) for k, v in a["por"].items()},
        })
    out.sort(key=lambda x: -(x["general"] or x["proyecto"]))
    return out
