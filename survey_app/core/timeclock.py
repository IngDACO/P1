"""
Fichaje (clock in / clock out) con persistencia en Google Sheets.

Requiere en los Secrets de Streamlit:
  TIMECLOCK_SHEET_ID = "<id de la hoja>"
  [gcp_service_account]  ...credenciales de la cuenta de servicio...

Esquema de la hoja (una fila por sesión de trabajo):
  Nombre | PIN | Proyecto | Ubicacion | Clock In | Clock Out | Horas | Estado
"""
from datetime import datetime, timedelta, date, time
from time import sleep as _dormir   # ⚠️ `time` de arriba es datetime.time, NO el módulo

import streamlit as st
from core import clock

HEADERS = ["Nombre", "PIN", "Proyecto", "Ubicacion",
           "Clock In", "Clock Out", "Horas", "Estado", "Grupo", "Tipo", "Usuario",
           "ProyectoID"]
FMT = "%Y-%m-%d %H:%M:%S"
# Tipo de fichaje: 'general' (jornada del día) | 'proyecto' (segmento por proyecto).
# Filas antiguas sin Tipo se tratan como 'proyecto'.
TIPO_GENERAL  = "general"
TIPO_PROYECTO = "proyecto"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


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


@st.cache_resource(show_spinner=False)
def _cached_ws():
    """Abre y cachea la worksheet. Se autentica UNA vez (no en cada rerun).
    Si falla, lanza excepción → no se cachea → se reintenta en la próxima llamada."""
    import gspread
    from google.oauth2.service_account import Credentials

    creds_info = dict(st.secrets["gcp_service_account"])
    sheet_id   = st.secrets["TIMECLOCK_SHEET_ID"]
    creds  = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    client = gspread.authorize(creds, http_client=_http_client_cls())
    ws     = client.open_by_key(sheet_id).sheet1

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
    except Exception:
        pass
    return ws


def _get_worksheet():
    """Devuelve (worksheet, None) o (None, mensaje_error)."""
    if not _secrets_present():
        return None, ("El fichaje no está conectado: faltan credenciales "
                      "(gcp_service_account) o TIMECLOCK_SHEET_ID en los Secrets.")
    try:
        return _cached_ws(), None
    except Exception as e:
        # Error transitorio de la API (rate limit, red…). No es falta de config.
        return None, f"Conexión temporalmente no disponible con Google Sheets: {e}"


@st.cache_resource(show_spinner=False)
def _libro():
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
    ss = _cached_ws().spreadsheet
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
def get_sheet(title: str, headers: tuple):
    """Devuelve el handle de una pestaña por título, cacheado como recurso.

    Crea la hoja y asegura/migra la cabecera UNA SOLA VEZ por proceso. Se apoya
    en `_libro()` para no pagar metadata+cabecera por hoja. Si la API falla,
    lanza excepción → NO se cachea → se reintenta en la próxima llamada."""
    hojas, cabeceras = _libro()
    clave = title.strip().lower()
    w = hojas.get(clave)

    if w is None:
        # ⚠️ Ahora solo se crea si la hoja NO está en el listado real del libro.
        # Antes bastaba con que `ss.worksheet(title)` lanzara —incluido por un
        # error de API—, así que un hipo podía crear una hoja duplicada.
        ss = _cached_ws().spreadsheet
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
        for i, h in enumerate(headers, start=1):
            if h not in head:
                try:
                    if w.col_count < i:
                        w.add_cols(i - w.col_count)
                    w.update_cell(1, i, h)
                    head = head + [h] if i > len(head) else head
                except Exception:
                    pass
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
    return (str(r.get("Tipo", "")).strip().lower() or TIPO_PROYECTO)


def pid_of(r) -> str:
    """ProyectoID de una fila de fichaje ('' en las filas anteriores a v145)."""
    return str(r.get("ProyectoID", "")).strip()


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
    return (str(r.get("Proyecto", "")).strip().casefold()
            == str(nombre or "").strip().casefold())


def _matches(r, usuario: str, nombre: str, grupo: str) -> bool:
    """¿La fila es de este usuario? Identifica por **Usuario** (login, v106); las filas
    antiguas sin Usuario caen al Nombre visible."""
    if str(r.get("Grupo", "")).strip() != (grupo or "").strip():
        return False
    ru = str(r.get("Usuario", "")).strip()
    if ru:
        return ru.lower() == (usuario or "").strip().lower()
    return str(r.get("Nombre", "")).strip() == (nombre or "").strip()


def clock_in(nombre: str, proyecto: str, ubicacion: str, grupo: str = "",
             tipo: str = TIPO_PROYECTO, usuario: str = "",
             proyecto_id: str = "") -> tuple:
    """Registra un clock in (tipo 'general' o 'proyecto'). Devuelve (ok, mensaje).
    Un usuario puede tener a la vez UNA sesión general y UNA de proyecto abiertas."""
    ws, err = _get_worksheet()
    if err:
        return False, err
    nombre = (nombre or "").strip()
    grupo  = (grupo or "").strip()
    tipo   = (tipo or TIPO_PROYECTO).strip().lower()
    if not nombre:
        return False, "No hay usuario en sesión."

    try:
        records = ws.get_all_records(numericise_ignore=['all'])
    except Exception as e:
        return False, f"Error leyendo la hoja: {e}"

    # ¿Ya hay una sesión abierta del MISMO tipo para este usuario+grupo?
    for r in records:
        if (_matches(r, usuario, nombre, grupo)
                and str(r.get("Estado", "")).strip().upper() == "ABIERTO"
                and _tipo_of(r) == tipo):
            etq = "jornada" if tipo == TIPO_GENERAL else "proyecto"
            return False, f"Ya tienes un clock in de {etq} abierto desde {r.get('Clock In')}."

    try:
        ws.append_row([nombre, "", proyecto or "", ubicacion or "",
                       _now(), "", "", "ABIERTO", grupo, tipo, usuario or "",
                       str(proyecto_id or "")],
                      value_input_option="RAW")
    except Exception as e:
        return False, f"Error escribiendo el fichaje: {e}"
    _invalidate_records()
    etq = "Jornada (general)" if tipo == TIPO_GENERAL else "Proyecto"
    return True, f"✅ Clock IN {etq} a las {_now()}."


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
        return False, "No hay usuario en sesión."

    try:
        records = ws.get_all_records(numericise_ignore=['all'])
    except Exception as e:
        return False, f"Error leyendo la hoja: {e}"

    # Buscar la sesión abierta más reciente del tipo (de abajo hacia arriba)
    target_row = None
    target_in  = None
    for idx, r in enumerate(records):
        if (_matches(r, usuario, nombre, grupo)
                and str(r.get("Estado", "")).strip().upper() == "ABIERTO"
                and _tipo_of(r) == tipo):
            target_row = idx + 2   # +2: fila 1 = cabecera, records 0-indexado
            target_in  = str(r.get("Clock In", ""))

    if target_row is None:
        etq = "jornada" if tipo == TIPO_GENERAL else "proyecto"
        return False, f"No tienes un clock in de {etq} abierto."

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
        return False, f"Error actualizando el fichaje: {e}"

    _invalidate_records()
    return True, f"✅ Clock OUT a las {out_ts}. Horas trabajadas: {horas}."


def _num(v) -> float:
    try:
        return float(str(v).replace(",", ".").strip() or 0)
    except Exception:
        return 0.0


@st.cache_data(ttl=120, show_spinner=False)
def _cached_records() -> list:
    """Filas del fichaje CACHEADAS (solo para lecturas de display: estado del reloj,
    resumen de horas). Las rutas de ESCRITURA leen fresco. Se invalida al fichar."""
    ws, err = _get_worksheet()
    if err or ws is None:
        return []
    try:
        return ws.get_all_records(numericise_ignore=['all'])
    except Exception:
        return []


def _invalidate_records():
    try:
        _cached_records.clear()
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
    if str(r.get("Estado", "")).strip().upper() == "ABIERTO":
        return _segmentos_dia(ci, clock.now())
    try:
        fin = datetime.strptime(str(r.get("Clock Out", "")), FMT)
    except Exception:
        try:
            d = datetime.strptime(ci, FMT).date()
        except Exception:
            return []
        h = _num(r.get("Horas"))
        return [(d, h)] if h > 0 else []
    segs = _segmentos_dia(ci, fin)
    # Fila cerrada de UN solo día: respeta las Horas GUARDADAS (lo que ya veía el
    # reporte del admin) en vez de recomputar del timestamp → el total con days=None
    # queda IDÉNTICO. Solo las que cruzan medianoche se reparten por segmento.
    if len(segs) == 1:
        h = _num(r.get("Horas"))
        return [(segs[0][0], h)] if h > 0 else []
    return segs


def open_sessions(nombre: str, grupo: str = "", usuario: str = "") -> dict:
    """{'general': {clock_in,proyecto}|None, 'proyecto': {...}|None} de sesiones ABIERTAS."""
    out = {TIPO_GENERAL: None, TIPO_PROYECTO: None}
    try:
        for r in _cached_records():          # lectura cacheada (display)
            if (_matches(r, usuario, nombre, grupo)
                    and str(r.get("Estado", "")).strip().upper() == "ABIERTO"):
                out[_tipo_of(r)] = {"clock_in": str(r.get("Clock In", "")),
                                    "proyecto": str(r.get("Proyecto", "")),
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
            if str(r.get("Grupo", "")).strip() != str(grupo).strip():
                continue
            if str(r.get("Estado", "")).strip().upper() != "ABIERTO":
                continue
            _ci = str(r.get("Clock In", ""))
            out.append({"usuario": str(r.get("Usuario", "")), "nombre": str(r.get("Nombre", "")),
                        "tipo": _tipo_of(r), "proyecto": str(r.get("Proyecto", "")),
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
            pn = _nombre_actual(pid_of(r), r.get("Proyecto", "")) or "(sin proyecto)"
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
            "proyecto": _nombre_actual(pid_of(r), r.get("Proyecto", "")),
            "entrada": str(r.get("Clock In", "")),
            "salida": str(r.get("Clock Out", "")),
            "horas": _num(r.get("Horas")),
            "abierto": str(r.get("Estado", "")).strip().upper() == "ABIERTO",
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
        return str(prj.get("Nombre", "")).strip() or nom if prj else nom
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
    for r in _cached_records():
        if str(r.get("Grupo", "")).strip() != str(grupo).strip():
            continue
        if _tipo_of(r) != TIPO_PROYECTO:
            continue
        # Cuenta el proyecto en CADA día que se trabajó (no solo el del Clock In):
        # un segmento nocturno que cruza medianoche se trabajó en los dos días.
        if fecha_d not in {d for d, hh in _row_segmentos(r) if hh > 0}:
            continue
        clave = str(r.get("Usuario", "")).strip() or str(r.get("Nombre", "")).strip()
        entry = {"pid": pid_of(r),
                 "nombre": _nombre_actual(pid_of(r), r.get("Proyecto", ""))}
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
    for r in _cached_records():
        if str(r.get("Grupo", "")).strip() != grupo:
            continue
        if _tipo_of(r) != TIPO_GENERAL:
            continue
        clave = str(r.get("Usuario", "")).strip() or str(r.get("Nombre", "")).strip()
        nombre = str(r.get("Nombre", "")).strip() or clave
        if not clave:
            continue
        h = sum(hh for d, hh in _row_segmentos(r) if desde <= d <= hasta)
        if h <= 0:
            continue
        a = out.setdefault(clave, {"nombre": nombre, "horas": 0.0})
        a["horas"] += h
    return {k: {"nombre": v["nombre"], "horas": round(v["horas"], 2)} for k, v in out.items()}


def group_hours(grupo: str, days=None) -> list:
    """Resumen de horas por usuario del grupo (para el admin). days=None=todo, 7=semana.
    Devuelve [{usuario, general, proyecto, sin_asignar, por_proyecto{nombre:horas}}]. Las
    sesiones abiertas cuentan con el tiempo transcurrido hasta ahora."""
    records = _cached_records()             # lectura cacheada (display)
    grupo = (grupo or "").strip()
    desde = (clock.now() - timedelta(days=days)).date() if days else None
    agg = {}
    for r in records:
        if str(r.get("Grupo", "")).strip() != grupo:
            continue
        # Clave por USUARIO (login); filas antiguas sin Usuario caen al Nombre.
        clave  = str(r.get("Usuario", "")).strip() or str(r.get("Nombre", "")).strip()
        nombre = str(r.get("Nombre", "")).strip() or clave
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
        a = agg.setdefault(clave, {"general": 0.0, "proyecto": 0.0, "por": {},
                                   "nombre": nombre})
        if _tipo_of(r) == TIPO_GENERAL:
            a["general"] += h
        else:
            a["proyecto"] += h
            # Con ID se resuelve al nombre ACTUAL: si el proyecto se renombro,
            # sus horas viejas ya no salen bajo dos etiquetas distintas.
            pn = _nombre_actual(pid_of(r), r.get("Proyecto", "")) or "(sin proyecto)"
            a["por"][pn] = a["por"].get(pn, 0.0) + h
    # Tarifa/hora por usuario, para el costo de mano de obra (misma fuente que
    # expenses.labor_cost). Import perezoso: auth no depende de timeclock.
    try:
        from core import auth
        rates = auth.rate_map(grupo)
    except Exception:
        rates = {}

    out = []
    for clave, a in agg.items():
        gen, pro = a["general"], a["proyecto"]
        # ⚠️ `sin_asignar` = jornada − proyectos SOLO tiene sentido si la jornada
        # cubre lo imputado. Si se imputo a proyectos MAS que la jornada abierta
        # (fichajes de proyecto sin abrir jornada, lo normal antes de v150), el
        # resultado es INDETERMINADO, no 0: marcarlo en vez de un cero que engaña.
        # Umbral de 3 min: por debajo es ruido de redondeo (dos tramos que cierran
        # con segundos de diferencia), no un dato realmente incompleto.
        indet = pro > gen + 0.05
        tarifa = float(rates.get(clave, 0.0) or 0.0)
        out.append({
            "usuario": clave,
            "nombre": a.get("nombre", clave),
            "general": round(gen, 2),
            "proyecto": round(pro, 2),
            "sin_asignar": round(max(0.0, gen - pro), 2),
            "sin_asignar_indet": indet,
            "tarifa": tarifa,
            "costo": round(pro * tarifa, 2),      # costo = horas imputadas × tarifa
            "por_proyecto": {k: round(v, 2) for k, v in a["por"].items()},
        })
    out.sort(key=lambda x: -(x["general"] or x["proyecto"]))
    return out
