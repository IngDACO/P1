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
           "Clock In", "Clock Out", "Horas", "Estado"]
FMT = "%Y-%m-%d %H:%M:%S"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _get_worksheet():
    """Devuelve (worksheet, None) o (None, mensaje_error)."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except Exception:
        return None, "Falta la librería gspread/google-auth en el entorno."

    creds_info = st.secrets.get("gcp_service_account")
    sheet_id   = st.secrets.get("TIMECLOCK_SHEET_ID")
    if not creds_info:
        return None, "No hay credenciales de Google (gcp_service_account) en los Secrets."
    if not sheet_id:
        return None, "Falta TIMECLOCK_SHEET_ID en los Secrets."

    try:
        creds  = Credentials.from_service_account_info(dict(creds_info), scopes=SCOPES)
        client = __import__("gspread").authorize(creds)
        ws     = client.open_by_key(sheet_id).sheet1
    except Exception as e:
        return None, f"No se pudo abrir la hoja: {e}"

    # Asegurar cabecera
    try:
        first = ws.row_values(1)
        if first != HEADERS:
            if not first:
                ws.append_row(HEADERS)
            elif first[:1] and first[0] != "Nombre":
                ws.insert_row(HEADERS, 1)
    except Exception:
        pass

    return ws, None


def is_configured() -> bool:
    ws, _ = _get_worksheet()
    return ws is not None


def _now() -> str:
    return datetime.now().strftime(FMT)


def clock_in(nombre: str, pin: str, proyecto: str, ubicacion: str) -> tuple:
    """Registra un clock in. Devuelve (ok, mensaje)."""
    ws, err = _get_worksheet()
    if err:
        return False, err
    nombre = (nombre or "").strip()
    pin    = str(pin or "").strip()
    if not nombre or not pin:
        return False, "Ingresa nombre y PIN."

    try:
        records = ws.get_all_records()
    except Exception as e:
        return False, f"Error leyendo la hoja: {e}"

    # ¿Ya hay una sesión abierta para este nombre+PIN?
    for r in records:
        if (str(r.get("Nombre", "")).strip() == nombre
                and str(r.get("PIN", "")).strip() == pin
                and str(r.get("Estado", "")).strip().upper() == "ABIERTO"):
            return False, f"Ya tienes un clock in abierto desde {r.get('Clock In')}. Haz clock out primero."

    try:
        ws.append_row([nombre, pin, proyecto or "", ubicacion or "",
                       _now(), "", "", "ABIERTO"])
    except Exception as e:
        return False, f"Error escribiendo el fichaje: {e}"
    return True, f"✅ Clock IN registrado a las {_now()}."


def clock_out(nombre: str, pin: str, nota: str = "") -> tuple:
    """Cierra la sesión abierta del nombre+PIN. Devuelve (ok, mensaje)."""
    ws, err = _get_worksheet()
    if err:
        return False, err
    nombre = (nombre or "").strip()
    pin    = str(pin or "").strip()
    if not nombre or not pin:
        return False, "Ingresa nombre y PIN."

    try:
        records = ws.get_all_records()
    except Exception as e:
        return False, f"Error leyendo la hoja: {e}"

    # Buscar la sesión abierta más reciente (de abajo hacia arriba)
    target_row = None
    target_in  = None
    for idx, r in enumerate(records):
        if (str(r.get("Nombre", "")).strip() == nombre
                and str(r.get("PIN", "")).strip() == pin
                and str(r.get("Estado", "")).strip().upper() == "ABIERTO"):
            target_row = idx + 2   # +2: fila 1 = cabecera, records 0-indexado
            target_in  = str(r.get("Clock In", ""))

    if target_row is None:
        return False, "No hay un clock in abierto para ese nombre + PIN."

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
        return ws.get_all_records()
    except Exception:
        return []
