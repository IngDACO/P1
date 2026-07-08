"""
Fichaje (clock in / clock out) con persistencia en Google Sheets.

Requiere en los Secrets de Streamlit:
  TIMECLOCK_SHEET_ID = "<id de la hoja>"
  [gcp_service_account]  ...credenciales de la cuenta de servicio...

Esquema de la hoja (una fila por sesión de trabajo):
  Nombre | PIN | Proyecto | Ubicacion | Clock In | Clock Out | Horas | Estado
"""
from datetime import datetime

import streamlit as st

HEADERS = ["Nombre", "PIN", "Proyecto", "Ubicacion",
           "Clock In", "Clock Out", "Horas", "Estado", "Grupo"]
USERS_HEADERS = ["Nombre", "PIN", "Activo"]
USERS_SHEET   = "Usuarios"
FMT = "%Y-%m-%d %H:%M:%S"
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

    # Asegurar cabecera + migración de la columna Grupo
    try:
        header = ws.row_values(1)
        if not header:
            ws.append_row(HEADERS)
        elif "Grupo" not in header:
            need = len(HEADERS)
            if ws.col_count < need:
                ws.add_cols(need - ws.col_count)
            ws.update_cell(1, need, "Grupo")
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


def is_configured() -> bool:
    """Solo revisa si los secrets están presentes — sin llamar a la API
    (evita falsos negativos por límites de rate de Google)."""
    return _secrets_present()


def _get_users_ws():
    """Devuelve (worksheet 'Usuarios', None) o (None, error). La crea si no existe."""
    ws_main, err = _get_worksheet()
    if err:
        return None, err
    ss = ws_main.spreadsheet
    try:
        uws = ss.worksheet(USERS_SHEET)
    except Exception:
        try:
            uws = ss.add_worksheet(title=USERS_SHEET, rows=200, cols=3)
            uws.append_row(USERS_HEADERS)
        except Exception as e:
            return None, f"No se pudo crear la hoja de usuarios: {e}"
    # Asegurar cabecera
    try:
        if not uws.row_values(1):
            uws.append_row(USERS_HEADERS)
    except Exception:
        pass
    return uws, None


def validate_user(nombre: str, pin: str) -> tuple:
    """Verifica Nombre+PIN contra la hoja 'Usuarios'. Devuelve (ok, mensaje)."""
    uws, err = _get_users_ws()
    if err:
        return False, err
    try:
        recs = uws.get_all_records(numericise_ignore=['all'])
    except Exception as e:
        return False, f"Error leyendo usuarios: {e}"

    nombre = (nombre or "").strip()
    pin    = str(pin or "").strip()

    if not recs:
        return False, ("No hay usuarios autorizados. Agrega Nombre + PIN en la "
                       "pestaña 'Usuarios' de la hoja de Google.")

    for r in recs:
        if (str(r.get("Nombre", "")).strip().lower() == nombre.lower()
                and str(r.get("PIN", "")).strip() == pin):
            activo = str(r.get("Activo", "SI")).strip().upper()
            if activo in ("", "SI", "SÍ", "YES", "Y", "TRUE", "1", "X"):
                return True, "ok"
            return False, f"Usuario '{nombre}' está inactivo."
    return False, "Nombre o PIN incorrecto (o no autorizado)."


def _now() -> str:
    return datetime.now().strftime(FMT)


def clock_in(nombre: str, proyecto: str, ubicacion: str, grupo: str = "") -> tuple:
    """Registra un clock in con la identidad del login. Devuelve (ok, mensaje)."""
    ws, err = _get_worksheet()
    if err:
        return False, err
    nombre = (nombre or "").strip()
    grupo  = (grupo or "").strip()
    if not nombre:
        return False, "No hay usuario en sesión."

    try:
        records = ws.get_all_records(numericise_ignore=['all'])
    except Exception as e:
        return False, f"Error leyendo la hoja: {e}"

    # ¿Ya hay una sesión abierta para este nombre+grupo?
    for r in records:
        if (str(r.get("Nombre", "")).strip() == nombre
                and str(r.get("Grupo", "")).strip() == grupo
                and str(r.get("Estado", "")).strip().upper() == "ABIERTO"):
            return False, f"Ya tienes un clock in abierto desde {r.get('Clock In')}. Haz clock out primero."

    try:
        ws.append_row([nombre, "", proyecto or "", ubicacion or "",
                       _now(), "", "", "ABIERTO", grupo],
                      value_input_option="RAW")
    except Exception as e:
        return False, f"Error escribiendo el fichaje: {e}"
    return True, f"✅ Clock IN registrado a las {_now()}."


def clock_out(nombre: str, grupo: str = "", nota: str = "") -> tuple:
    """Cierra la sesión abierta del nombre+grupo. Devuelve (ok, mensaje)."""
    ws, err = _get_worksheet()
    if err:
        return False, err
    nombre = (nombre or "").strip()
    grupo  = (grupo or "").strip()
    if not nombre:
        return False, "No hay usuario en sesión."

    try:
        records = ws.get_all_records(numericise_ignore=['all'])
    except Exception as e:
        return False, f"Error leyendo la hoja: {e}"

    # Buscar la sesión abierta más reciente (de abajo hacia arriba)
    target_row = None
    target_in  = None
    for idx, r in enumerate(records):
        if (str(r.get("Nombre", "")).strip() == nombre
                and str(r.get("Grupo", "")).strip() == grupo
                and str(r.get("Estado", "")).strip().upper() == "ABIERTO"):
            target_row = idx + 2   # +2: fila 1 = cabecera, records 0-indexado
            target_in  = str(r.get("Clock In", ""))

    if target_row is None:
        return False, "No tienes un clock in abierto."

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

    return True, f"✅ Clock OUT a las {out_ts}. Horas trabajadas: {horas}."


def get_records() -> list:
    """Devuelve todas las filas como lista de dicts (para mostrar)."""
    ws, err = _get_worksheet()
    if err:
        return []
    try:
        return ws.get_all_records(numericise_ignore=['all'])
    except Exception:
        return []
