"""
Fichaje (clock in / clock out) con persistencia en Google Sheets.

Requiere en los Secrets de Streamlit:
  TIMECLOCK_SHEET_ID = "<id de la hoja>"
  [gcp_service_account]  ...credenciales de la cuenta de servicio...

Esquema de la hoja (una fila por sesión de trabajo):
  Nombre | PIN | Proyecto | Ubicacion | Clock In | Clock Out | Horas | Estado
"""
from datetime import datetime, timedelta

import streamlit as st

HEADERS = ["Nombre", "PIN", "Proyecto", "Ubicacion",
           "Clock In", "Clock Out", "Horas", "Estado", "Grupo", "Tipo", "Usuario"]
FMT = "%Y-%m-%d %H:%M:%S"
# Tipo de fichaje: 'general' (jornada del conductor) | 'proyecto' (segmento por proyecto).
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


@st.cache_resource(show_spinner=False)
def _cached_ws():
    """Abre y cachea la worksheet. Se autentica UNA vez (no en cada rerun).
    Si falla, lanza excepción → no se cachea → se reintenta en la próxima llamada."""
    import gspread
    from google.oauth2.service_account import Credentials

    creds_info = dict(st.secrets["gcp_service_account"])
    sheet_id   = st.secrets["TIMECLOCK_SHEET_ID"]
    creds  = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    client = gspread.authorize(creds)
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
def get_sheet(title: str, headers: tuple):
    """Devuelve el handle de una pestaña por título, cacheado como recurso.

    Crea la hoja y asegura/migra la cabecera UNA SOLA VEZ por proceso. Antes,
    cada módulo (auth, projects, alerts, manuals…) hacía `ss.worksheet(title)`
    (metadata) + `row_values(1)` (cabecera) en CADA lectura → 2 llamadas extra
    por lectura. Con esto esas comprobaciones ocurren una vez y luego se reutiliza
    el handle. Si la API falla, lanza excepción → NO se cachea → se reintenta."""
    ws = _cached_ws()                      # conexión cacheada; lanza si la API falla
    ss = ws.spreadsheet
    try:
        w = ss.worksheet(title)
    except Exception:
        w = ss.add_worksheet(title=title, rows=500, cols=len(headers))
        w.append_row(list(headers))
        return w
    head = w.row_values(1)
    if not head:
        w.append_row(list(headers))
    else:
        # Migración: agrega columnas faltantes en su posición canónica.
        for i, h in enumerate(headers, start=1):
            if h not in head:
                try:
                    if w.col_count < i:
                        w.add_cols(i - w.col_count)
                    w.update_cell(1, i, h)
                except Exception:
                    pass
    return w


def is_configured() -> bool:
    """Solo revisa si los secrets están presentes — sin llamar a la API
    (evita falsos negativos por límites de rate de Google)."""
    return _secrets_present()


def _now() -> str:
    return datetime.now().strftime(FMT)


def _tipo_of(r) -> str:
    """Tipo de una fila; vacío se trata como 'proyecto' (compat filas antiguas)."""
    return (str(r.get("Tipo", "")).strip().lower() or TIPO_PROYECTO)


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
             tipo: str = TIPO_PROYECTO, usuario: str = "") -> tuple:
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
                       _now(), "", "", "ABIERTO", grupo, tipo, usuario or ""],
                      value_input_option="RAW")
    except Exception as e:
        return False, f"Error escribiendo el fichaje: {e}"
    _invalidate_records()
    etq = "Jornada (general)" if tipo == TIPO_GENERAL else "Proyecto"
    return True, f"✅ Clock IN {etq} a las {_now()}."


def clock_out(nombre: str, grupo: str = "", nota: str = "",
              tipo: str = TIPO_PROYECTO, usuario: str = "") -> tuple:
    """Cierra la sesión abierta (del tipo indicado) de nombre+grupo. Devuelve (ok, mensaje)."""
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

    out_ts = _now()
    horas  = ""
    try:
        t_in  = datetime.strptime(target_in, FMT)
        t_out = datetime.strptime(out_ts, FMT)
        horas = round((t_out - t_in).total_seconds() / 3600.0, 2)
    except Exception:
        horas = ""

    try:
        # Columnas: 6=Clock Out, 7=Horas, 8=Estado
        ws.update_cell(target_row, 6, out_ts)
        ws.update_cell(target_row, 7, str(horas))
        ws.update_cell(target_row, 8, "CERRADO")
        if nota:
            # anexar nota a Ubicacion (col 4) si viene
            prev = ws.cell(target_row, 4).value or ""
            ws.update_cell(target_row, 4, (prev + " | " + nota).strip(" |"))
    except Exception as e:
        return False, f"Error actualizando el fichaje: {e}"

    _invalidate_records()
    return True, f"✅ Clock OUT a las {out_ts}. Horas trabajadas: {horas}."


def _num(v) -> float:
    try:
        return float(str(v).replace(",", ".").strip() or 0)
    except Exception:
        return 0.0


@st.cache_data(ttl=20, show_spinner=False)
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
        return max(0, int((datetime.now() - datetime.strptime(str(clock_in_str), FMT)).total_seconds()))
    except Exception:
        return 0


def open_sessions(nombre: str, grupo: str = "", usuario: str = "") -> dict:
    """{'general': {clock_in,proyecto}|None, 'proyecto': {...}|None} de sesiones ABIERTAS."""
    out = {TIPO_GENERAL: None, TIPO_PROYECTO: None}
    try:
        for r in _cached_records():          # lectura cacheada (display)
            if (_matches(r, usuario, nombre, grupo)
                    and str(r.get("Estado", "")).strip().upper() == "ABIERTO"):
                out[_tipo_of(r)] = {"clock_in": str(r.get("Clock In", "")),
                                    "proyecto": str(r.get("Proyecto", ""))}
    except Exception:
        pass
    return out


def switch_project(nombre: str, grupo: str, new_proyecto: str, ubicacion: str = "",
                   usuario: str = "") -> tuple:
    """Cambia de proyecto en 1 toque: cierra el segmento activo (si hay) y abre el nuevo."""
    clock_out(nombre, grupo, tipo=TIPO_PROYECTO, usuario=usuario)   # si no hay, se ignora
    return clock_in(nombre, new_proyecto, ubicacion, grupo, tipo=TIPO_PROYECTO, usuario=usuario)


def group_hours(grupo: str, days=None) -> list:
    """Resumen de horas por usuario del grupo (para el admin). days=None=todo, 7=semana.
    Devuelve [{usuario, general, proyecto, sin_asignar, por_proyecto{nombre:horas}}]. Las
    sesiones abiertas cuentan con el tiempo transcurrido hasta ahora."""
    records = _cached_records()             # lectura cacheada (display)
    grupo = (grupo or "").strip()
    desde = (datetime.now() - timedelta(days=days)) if days else None
    agg = {}
    for r in records:
        if str(r.get("Grupo", "")).strip() != grupo:
            continue
        # Clave por USUARIO (login); filas antiguas sin Usuario caen al Nombre.
        clave  = str(r.get("Usuario", "")).strip() or str(r.get("Nombre", "")).strip()
        nombre = str(r.get("Nombre", "")).strip() or clave
        if not clave:
            continue
        ci = str(r.get("Clock In", ""))
        if desde:
            try:
                if datetime.strptime(ci, FMT) < desde:
                    continue
            except Exception:
                continue
        estado = str(r.get("Estado", "")).strip().upper()
        h = round(elapsed_seconds(ci) / 3600.0, 2) if estado == "ABIERTO" else _num(r.get("Horas"))
        if h <= 0:
            continue
        a = agg.setdefault(clave, {"general": 0.0, "proyecto": 0.0, "por": {}, "nombre": nombre})
        if _tipo_of(r) == TIPO_GENERAL:
            a["general"] += h
        else:
            a["proyecto"] += h
            pn = str(r.get("Proyecto", "")) or "(sin proyecto)"
            a["por"][pn] = a["por"].get(pn, 0.0) + h
    out = []
    for clave, a in agg.items():
        out.append({
            "usuario": clave,
            "nombre": a.get("nombre", clave),
            "general": round(a["general"], 2),
            "proyecto": round(a["proyecto"], 2),
            "sin_asignar": round(max(0.0, a["general"] - a["proyecto"]), 2),
            "por_proyecto": {k: round(v, 2) for k, v in a["por"].items()},
        })
    out.sort(key=lambda x: -(x["general"] or x["proyecto"]))
    return out
