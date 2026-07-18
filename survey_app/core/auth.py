"""
Autenticación y control de acceso por rol.

Usuarios en Google Sheets (hoja 'Login', mismo spreadsheet que el fichaje):
    Usuario | Password | Rol | Nombre | Activo

Roles: propietario, administrador, campo.
Contraseñas encriptadas con PBKDF2-SHA256 (nunca en texto plano).
"""
import hashlib
import hmac
import os
import time
import uuid

import streamlit as st

from core import timeclock

LOGIN_SHEET   = "Login"
# Columnas nuevas al final para no romper filas existentes (migración segura).
LOGIN_HEADERS = ["Usuario", "Password", "Rol", "Nombre", "Activo", "Grupo",
                 "SessionToken", "SessionTime", "Email", "TelegramChatID", "TarifaHora"]
GROUPS_SHEET   = "Grupos"
GROUPS_HEADERS = ["Grupo", "Descripcion", "Activo"]
ROLES         = ["propietario", "administrador", "campo", "conductor"]
_ACTIVE_OK    = ("", "SI", "SÍ", "YES", "Y", "TRUE", "1", "X")
# Columnas (1-based) en la hoja Login
_COL = {"Usuario": 1, "Password": 2, "Rol": 3, "Nombre": 4, "Activo": 5, "Grupo": 6,
        "SessionToken": 7, "SessionTime": 8, "Email": 9, "TelegramChatID": 10,
        "TarifaHora": 11}

# Sesión ÚNICA por cuenta ("primero gana"): un segundo login se bloquea mientras la
# sesión activa siga viva. El heartbeat marca vida; si se abandona > SESSION_TIMEOUT s,
# la cuenta se libera sola.
SESSION_TIMEOUT = 180


# ── Hash de contraseñas ──────────────────────────────────────
def hash_password(pw: str, iterations: int = 200_000) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt, iterations)
    return f"pbkdf2$sha256${iterations}${salt.hex()}${dk.hex()}"


def verify_password(pw: str, stored: str) -> bool:
    try:
        _algo, _h, iters, salt_hex, hash_hex = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"),
                                 bytes.fromhex(salt_hex), int(iters))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


# ── Conexión a la hoja Login ─────────────────────────────────
def is_configured() -> bool:
    return timeclock._secrets_present()


def _get_login_ws():
    # El handle (y la migración de columnas) se cachea una vez por proceso en
    # timeclock.get_sheet → no re-lee la cabecera en cada llamada.
    if not timeclock._secrets_present():
        return None, "El acceso no está configurado (faltan credenciales en Secrets)."
    try:
        return timeclock.get_sheet(LOGIN_SHEET, tuple(LOGIN_HEADERS)), None
    except Exception as e:
        return None, f"No se pudo abrir la hoja Login: {e}"


def _get_groups_ws():
    if not timeclock._secrets_present():
        return None, "El acceso no está configurado (faltan credenciales en Secrets)."
    try:
        return timeclock.get_sheet(GROUPS_SHEET, tuple(GROUPS_HEADERS)), None
    except Exception as e:
        return None, f"No se pudo abrir la hoja Grupos: {e}"


# ── Lectura CACHEADA del sheet Login (para rutas de display, no de sesión) ──
# list_users / get_user se llaman en CADA rerun de los paneles (p. ej. el
# dropdown de asignar campo, la gestión de contacto). Sin caché, cada slider
# disparaba una lectura del sheet. Se cachea 30 s y se invalida al escribir.
# OJO: las rutas críticas de sesión ("primero gana": start_session, heartbeat,
# end_session, verify_login) NO usan este caché — leen fresco para no permitir
# una 2ª sesión con datos vencidos.
@st.cache_data(ttl=30, show_spinner=False)
def _login_records_cached():
    lws, err = _get_login_ws()
    if err or lws is None:
        return []
    try:
        return lws.get_all_records(numericise_ignore=["all"])
    except Exception:
        return []


def _invalidate_login():
    try:
        _login_records_cached.clear()
    except Exception:
        pass


# ── Gestión de grupos ────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def _group_records() -> list:
    gws, err = _get_groups_ws()
    if err or gws is None:
        return []
    try:
        return gws.get_all_records(numericise_ignore=["all"])
    except Exception:
        return []


def _invalidate_groups():
    try:
        _group_records.clear()
    except Exception:
        pass


def list_groups(only_active: bool = False) -> list:
    """Grupos (lectura CACHEADA: se llamaba en cada render de los paneles del propietario)."""
    out = []
    for r in _group_records():
        activo = str(r.get("Activo", "SI")).strip().upper() in _ACTIVE_OK
        if only_active and not activo:
            continue
        out.append({"Grupo": str(r.get("Grupo", "")),
                    "Descripcion": str(r.get("Descripcion", "")),
                    "Activo": "SI" if activo else "NO"})
    return out


def add_group(nombre: str, descripcion: str = "") -> tuple:
    gws, err = _get_groups_ws()
    if err:
        return False, err
    nombre = (nombre or "").strip()
    if not nombre:
        return False, "El nombre del grupo es obligatorio."
    for r in gws.get_all_records(numericise_ignore=["all"]):
        if str(r.get("Grupo", "")).strip().lower() == nombre.lower():
            return False, f"El grupo '{nombre}' ya existe."
    try:
        gws.append_row([nombre, descripcion, "SI"], value_input_option="RAW")
    except Exception as e:
        return False, f"Error creando grupo: {e}"
    _invalidate_groups()
    return True, f"Grupo '{nombre}' creado."


def delete_group(nombre: str) -> tuple:
    gws, err = _get_groups_ws()
    if err:
        return False, err
    for i, r in enumerate(gws.get_all_records(numericise_ignore=["all"])):
        if str(r.get("Grupo", "")).strip().lower() == (nombre or "").strip().lower():
            try:
                gws.delete_rows(i + 2)
                _invalidate_groups()
                return True, f"Grupo '{nombre}' eliminado."
            except Exception as e:
                return False, f"Error: {e}"
    return False, "Grupo no encontrado."


def _records(lws):
    return lws.get_all_records(numericise_ignore=["all"])


def _find_row(lws, usuario):
    """Devuelve (row_index_1based, record) o (None, None)."""
    usuario = (usuario or "").strip().lower()
    for i, r in enumerate(_records(lws)):
        if str(r.get("Usuario", "")).strip().lower() == usuario:
            return i + 2, r
    return None, None


# ── Autenticación ────────────────────────────────────────────
def has_any_user() -> bool:
    lws, err = _get_login_ws()
    if err:
        return True   # si no se puede leer, no ofrecer setup inicial
    try:
        return len(_records(lws)) > 0
    except Exception:
        return True


def verify_login(usuario: str, pw: str) -> dict:
    lws, err = _get_login_ws()
    if err:
        return {"ok": False, "error": err}
    usuario = (usuario or "").strip()
    for r in _records(lws):
        if str(r.get("Usuario", "")).strip().lower() == usuario.lower():
            activo = str(r.get("Activo", "SI")).strip().upper()
            if activo not in _ACTIVE_OK:
                return {"ok": False, "error": "Usuario inactivo."}
            if verify_password(pw, str(r.get("Password", ""))):
                return {"ok": True,
                        "usuario": str(r.get("Usuario", "")),
                        "rol":     str(r.get("Rol", "campo")).strip().lower(),
                        "nombre":  str(r.get("Nombre", "")) or usuario,
                        "grupo":   str(r.get("Grupo", "")).strip()}
            return {"ok": False, "error": "Contraseña incorrecta."}
    return {"ok": False, "error": "Usuario no encontrado."}


# ── Sesión única por cuenta ("primero gana") ─────────────────
def _session_active(rec) -> bool:
    """¿La cuenta tiene una sesión viva? (token no vacío y heartbeat reciente)."""
    if not str(rec.get("SessionToken", "")).strip():
        return False
    try:
        t = int(float(rec.get("SessionTime", 0)))
    except Exception:
        t = 0
    return (int(time.time()) - t) < SESSION_TIMEOUT


def start_session(usuario: str) -> tuple:
    """Intenta abrir sesión única. (True, token) si la cuenta está libre;
    (False, motivo) si ya hay una sesión activa en otro dispositivo."""
    lws, err = _get_login_ws()
    if err:
        return False, err
    row, rec = _find_row(lws, usuario)
    if row is None:
        return False, "Usuario no encontrado."
    if _session_active(rec):
        return False, "Esta cuenta ya tiene una sesión activa en otro dispositivo."
    token = uuid.uuid4().hex
    try:
        lws.update_cell(row, _COL["SessionToken"], token)
        lws.update_cell(row, _COL["SessionTime"], str(int(time.time())))
    except Exception as e:
        return False, f"No se pudo iniciar sesión: {e}"
    return True, token


def heartbeat(usuario: str, token: str) -> bool:
    """Marca vida si el token sigue vigente. False si fue desplazado (o expiró y lo tomó otro)."""
    lws, err = _get_login_ws()
    if err:
        return True   # error transitorio de la API → no expulsar
    row, rec = _find_row(lws, usuario)
    if row is None:
        return False
    if str(rec.get("SessionToken", "")).strip() != str(token):
        return False
    try:
        lws.update_cell(row, _COL["SessionTime"], str(int(time.time())))
    except Exception:
        pass
    return True


def validate_session(usuario: str, token: str) -> dict:
    """Para el login persistente (cookie): si el token coincide con la sesión viva
    del usuario, devuelve sus datos de login; si no, {}."""
    if not (str(usuario).strip() and str(token).strip()):
        return {}
    lws, err = _get_login_ws()
    if err:
        return {}
    _, rec = _find_row(lws, usuario)
    if not rec:
        return {}
    if str(rec.get("SessionToken", "")).strip() != str(token).strip():
        return {}
    if str(rec.get("Activo", "SI")).strip().upper() not in _ACTIVE_OK:
        return {}
    return {"usuario": str(rec.get("Usuario", "")),
            "rol":     str(rec.get("Rol", "campo")).strip().lower(),
            "nombre":  str(rec.get("Nombre", "")) or usuario,
            "grupo":   str(rec.get("Grupo", "")).strip(),
            "token":   token}


def get_user(usuario: str) -> dict:
    """Registro del usuario (dict) o {} si no existe/no se puede leer (cacheado).
    Uso para contacto/display; las rutas de sesión leen fresco vía _find_row."""
    usuario = (usuario or "").strip().lower()
    for r in _login_records_cached():
        if str(r.get("Usuario", "")).strip().lower() == usuario:
            return r
    return {}


def set_contact(usuario: str, email: str = None, telegram: str = None) -> tuple:
    """Actualiza Email y/o TelegramChatID del usuario (para notificaciones)."""
    lws, err = _get_login_ws()
    if err:
        return False, err
    row, _ = _find_row(lws, usuario)
    if row is None:
        return False, "Usuario no encontrado."
    try:
        if email is not None:
            lws.update_cell(row, _COL["Email"], str(email).strip())
        if telegram is not None:
            lws.update_cell(row, _COL["TelegramChatID"], str(telegram).strip())
    except Exception as e:
        return False, f"Error guardando contacto: {e}"
    _invalidate_login()
    return True, "Contacto actualizado."


def end_session(usuario: str, token: str = None):
    """Libera la cuenta al cerrar sesión (solo si el token coincide, o forzado si token=None)."""
    lws, err = _get_login_ws()
    if err:
        return
    row, rec = _find_row(lws, usuario)
    if row is None:
        return
    if token is None or str(rec.get("SessionToken", "")).strip() == str(token):
        try:
            lws.update_cell(row, _COL["SessionToken"], "")
            lws.update_cell(row, _COL["SessionTime"], "")
        except Exception:
            pass


# ── Gestión de usuarios ──────────────────────────────────────
def list_users(grupo: str = None) -> list:
    """Todos los usuarios, o solo los de un grupo si se indica (lectura cacheada)."""
    out = []
    for r in _login_records_cached():
        g = str(r.get("Grupo", "")).strip()
        if grupo is not None and g.lower() != grupo.strip().lower():
            continue
        out.append({
            "Usuario": str(r.get("Usuario", "")),
            "Rol":     str(r.get("Rol", "")),
            "Nombre":  str(r.get("Nombre", "")),
            "Grupo":   g,
            "Activo":  str(r.get("Activo", "SI")),
            "Email":          str(r.get("Email", "")),
            "TelegramChatID": str(r.get("TelegramChatID", "")),
            "TarifaHora":     str(r.get("TarifaHora", "")),
        })
    return out


def set_rate(usuario: str, tarifa) -> tuple:
    """Tarifa por hora del usuario (para costear la mano de obra)."""
    lws, err = _get_login_ws()
    if err:
        return False, err
    row, _ = _find_row(lws, usuario)
    if row is None:
        return False, "Usuario no encontrado."
    try:
        lws.update_cell(row, _COL["TarifaHora"], str(tarifa))
    except Exception as e:
        return False, f"Error: {e}"
    _invalidate_login()
    return True, f"Tarifa de '{usuario}' actualizada."


def rate_map(grupo: str = None) -> dict:
    """Tarifas/hora indexadas por **Usuario** y también por Nombre (respaldo para
    los fichajes antiguos, anteriores a la columna Usuario)."""
    m = {}
    for u in list_users(grupo):
        try:
            v = float(str(u.get("TarifaHora", "") or 0).replace(",", "."))
        except Exception:
            v = 0.0
        if u.get("Usuario"):
            m[u["Usuario"]] = v
        if u.get("Nombre"):
            m.setdefault(u["Nombre"], v)
    return m


def add_user(usuario: str, pw: str, rol: str, nombre: str = "",
             grupo: str = "", activo: bool = True) -> tuple:
    lws, err = _get_login_ws()
    if err:
        return False, err
    usuario = (usuario or "").strip()
    if not usuario or not pw:
        return False, "Usuario y contraseña son obligatorios."
    if rol not in ROLES:
        return False, "Rol inválido."
    if rol in ("administrador", "campo") and not (grupo or "").strip():
        return False, "Los usuarios administrador y de campo deben pertenecer a un grupo."
    row, _ = _find_row(lws, usuario)
    if row is not None:
        return False, f"El usuario '{usuario}' ya existe."
    try:
        lws.append_row([usuario, hash_password(pw), rol, nombre or usuario,
                        "SI" if activo else "NO", (grupo or "").strip()],
                       value_input_option="RAW")
    except Exception as e:
        return False, f"Error creando usuario: {e}"
    _invalidate_login()
    return True, f"Usuario '{usuario}' creado ({rol})."


def set_group(usuario: str, grupo: str) -> tuple:
    lws, err = _get_login_ws()
    if err:
        return False, err
    row, _ = _find_row(lws, usuario)
    if row is None:
        return False, "Usuario no encontrado."
    try:
        lws.update_cell(row, _COL["Grupo"], (grupo or "").strip())
    except Exception as e:
        return False, f"Error: {e}"
    _invalidate_login()
    return True, f"Grupo de '{usuario}' → {grupo or '(sin grupo)'}."


def set_password(usuario: str, pw: str) -> tuple:
    lws, err = _get_login_ws()
    if err:
        return False, err
    if not pw:
        return False, "La contraseña no puede estar vacía."
    row, _ = _find_row(lws, usuario)
    if row is None:
        return False, "Usuario no encontrado."
    try:
        lws.update_cell(row, 2, hash_password(pw))
    except Exception as e:
        return False, f"Error: {e}"
    _invalidate_login()
    return True, f"Contraseña de '{usuario}' actualizada."


def set_role(usuario: str, rol: str) -> tuple:
    if rol not in ROLES:
        return False, "Rol inválido."
    lws, err = _get_login_ws()
    if err:
        return False, err
    row, _ = _find_row(lws, usuario)
    if row is None:
        return False, "Usuario no encontrado."
    try:
        lws.update_cell(row, 3, rol)
    except Exception as e:
        return False, f"Error: {e}"
    _invalidate_login()
    return True, f"Rol de '{usuario}' → {rol}."


def set_active(usuario: str, activo: bool) -> tuple:
    lws, err = _get_login_ws()
    if err:
        return False, err
    row, _ = _find_row(lws, usuario)
    if row is None:
        return False, "Usuario no encontrado."
    try:
        lws.update_cell(row, 5, "SI" if activo else "NO")
    except Exception as e:
        return False, f"Error: {e}"
    _invalidate_login()
    return True, f"'{usuario}' {'activado' if activo else 'desactivado'}."


def delete_user(usuario: str) -> tuple:
    lws, err = _get_login_ws()
    if err:
        return False, err
    row, _ = _find_row(lws, usuario)
    if row is None:
        return False, "Usuario no encontrado."
    try:
        lws.delete_rows(row)
    except Exception as e:
        return False, f"Error: {e}"
    _invalidate_login()
    return True, f"Usuario '{usuario}' eliminado."


# ── Helpers de rol ───────────────────────────────────────────
def can_reports(rol: str) -> bool:
    return rol in ("propietario", "administrador")

