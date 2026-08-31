"""
Autenticación y control de acceso por rol.

Usuarios en Google Sheets (hoja 'Login', mismo spreadsheet que el fichaje):
    Usuario | Password | Rol | Nombre | Activo

Roles: propietario, administrador, campo.
Contraseñas encriptadas con PBKDF2-SHA256 (nunca en texto plano).
"""
import logging
import hashlib
import hmac
import os
import time
import uuid

import streamlit as st

from core.i18n import t
from core import timeclock

logger = logging.getLogger(__name__)

LOGIN_SHEET   = "Login"
# Columnas nuevas al final para no romper filas existentes (migración segura).
LOGIN_HEADERS = ["Usuario", "Password", "Rol", "Nombre", "Activo", "Grupo",
                 "SessionToken", "SessionTime", "Email", "TelegramChatID", "TarifaHora",
                 # v433: fecha de alta en la empresa. La usa el saldo de vacaciones,
                 # que en AU va por ANIVERSARIO de cada persona y no por año natural
                 # (decisión del usuario). Va AL FINAL → migra sola; una fila que no
                 # la traiga cae al año natural y la app lo DICE, en vez de dar un
                 # saldo que parece bueno y no lo es.
                 "FechaIngreso"]
GROUPS_SHEET   = "Grupos"
GROUPS_HEADERS = ["Grupo", "Descripcion", "Activo", "Zona", "MargenDefault", "ImpuestoDefault",
                  "SuperDefault", "RetencionDefault",
                  # v359: libro de Google propio de este cliente. Vacío = el
                  # maestro (así `cliente1` sigue donde estaba, sin migrar).
                  "SheetID"]
ROLES         = ["propietario", "administrador", "campo"]
_ACTIVE_OK    = ("", "SI", "SÍ", "YES", "Y", "TRUE", "1", "X")
# Columnas (1-based) en la hoja Login
# ⚠️ DERIVADO de LOGIN_HEADERS, nunca escrito a mano. Estaba a mano —un literal en
# paralelo a la lista de cabeceras— y al añadir `FechaIngreso` en v433 la columna se
# migró en la hoja pero `_COL` no la conocía: `set_fecha_ingreso` moría con
# «Error: 'FechaIngreso'». Solo se vio EJECUTÁNDOLA contra la hoja real; ni el
# guardián ni los imports lo detectan. Es la familia de `MargenPct` (v344) y de la
# fila posicional de v363: dos sitios que describen lo mismo y se desincronizan.
_COL = {h: i + 1 for i, h in enumerate(LOGIN_HEADERS)}

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
        return None, t("Access is not configured (credentials missing from Secrets).")
    try:
        return timeclock.get_sheet(LOGIN_SHEET, tuple(LOGIN_HEADERS)), None
    except Exception as e:
        return None, f"{t('Could not open the Login sheet')}: {e}"


def _get_groups_ws():
    if not timeclock._secrets_present():
        return None, t("Access is not configured (credentials missing from Secrets).")
    try:
        return timeclock.get_sheet(GROUPS_SHEET, tuple(GROUPS_HEADERS)), None
    except Exception as e:
        return None, f"{t('Could not open the Groups sheet')}: {e}"


# ── Lectura CACHEADA del sheet Login (para rutas de display, no de sesión) ──
# list_users / get_user se llaman en CADA rerun de los paneles (p. ej. el
# dropdown de asignar campo, la gestión de contacto). Sin caché, cada slider
# disparaba una lectura del sheet. Se cachea 30 s y se invalida al escribir.
# OJO: las rutas críticas de sesión ("primero gana": start_session, heartbeat,
# end_session, verify_login) NO usan este caché — leen fresco para no permitir
# una 2ª sesión con datos vencidos.
@st.cache_data(ttl=120, show_spinner=False)
def _login_records_cached():
    """Registros de "Login" (por lote, v339)."""
    from core import hojas          # perezoso: evita el ciclo con timeclock
    return hojas.registros("Login", LOGIN_HEADERS) or []


def _invalidate_login():
    # ⚠️ v339: además de la caché propia hay que tirar el LOTE compartido
    # (`hojas._lote`). Si no, tras escribir el dato seguiría saliendo del lote
    # cacheado hasta 120 s y parecería que no se guardó.
    from core import hojas
    hojas.invalidar()
    try:
        _login_records_cached.clear()
    except Exception:
        pass


# ── Gestión de grupos ────────────────────────────────────────
@st.cache_data(ttl=120, show_spinner=False)
def _group_records() -> list:
    """Registros de "Grupos" (por lote, v339)."""
    from core import hojas          # perezoso: evita el ciclo con timeclock
    return hojas.registros("Grupos", GROUPS_HEADERS) or []


def _invalidate_groups():
    # ⚠️ v339: además de la caché propia hay que tirar el LOTE compartido
    # (`hojas._lote`). Si no, tras escribir, el dato seguiría saliendo del lote
    # cacheado hasta 120 s y parecería que no se guardó.
    from core import hojas
    hojas.invalidar()
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
                    "Activo": "SI" if activo else "NO",
                    "Zona": str(r.get("Zona", "")).strip()})
    return out


def group_timezone(grupo: str) -> str:
    """Zona horaria del grupo (`Grupos.Zona`), o '' si no está configurada.

    La usa `core.clock` para grabar y comparar 'hoy' en la hora local del grupo
    (cada empresa puede estar en otro país). Lectura cacheada (`_group_records`)."""
    g = (grupo or "").strip().lower()
    if not g:
        return ""
    for r in _group_records():
        if str(r.get("Grupo", "")).strip().lower() == g:
            return str(r.get("Zona", "")).strip()
    return ""


def set_group_timezone(grupo: str, zona: str) -> tuple:
    """El propietario fija la zona horaria de un grupo (p.ej. 'Australia/Sydney')."""
    gws, err = _get_groups_ws()
    if err:
        return False, err
    try:
        col = gws.row_values(1).index("Zona") + 1
    except ValueError:
        return False, t("The Zona column does not exist yet in the Groups sheet.")
    for i, r in enumerate(gws.get_all_records(numericise_ignore=["all"])):
        if str(r.get("Grupo", "")).strip().lower() == (grupo or "").strip().lower():
            try:
                gws.update_cell(i + 2, col, str(zona or "").strip())
                _invalidate_groups()
                return True, "Zona horaria actualizada."
            except Exception as e:
                return False, f"Error: {e}"
    return False, "Grupo no encontrado."


def group_margin_default(grupo: str) -> float:
    """Margen (%) por defecto del grupo sobre la mano de obra (`Grupos.MargenDefault`).

    Es la base de la 'tarifa de venta': lo que se cobra al cliente por la MO =
    costo × (1 + margen%). Cada proyecto puede sobrescribirlo (`Proyectos.MargenMO`).
    Lectura cacheada (`_group_records`). 0.0 si no está configurado."""
    g = (grupo or "").strip().lower()
    if not g:
        return 0.0
    for r in _group_records():
        if str(r.get("Grupo", "")).strip().lower() == g:
            try:
                return float(str(r.get("MargenDefault", "") or 0).replace(",", "."))
            except Exception:
                return 0.0
    return 0.0


def set_group_margin_default(grupo: str, pct) -> tuple:
    """El propietario fija el margen % por defecto de un grupo."""
    gws, err = _get_groups_ws()
    if err:
        return False, err
    try:
        col = gws.row_values(1).index("MargenDefault") + 1
    except ValueError:
        return False, t("The MargenDefault column does not exist yet in the Groups sheet.")
    for i, r in enumerate(gws.get_all_records(numericise_ignore=["all"])):
        if str(r.get("Grupo", "")).strip().lower() == (grupo or "").strip().lower():
            try:
                gws.update_cell(i + 2, col, str(pct))
                _invalidate_groups()
                return True, t("Default margin updated.")
            except Exception as e:
                return False, f"Error: {e}"
    return False, "Grupo no encontrado."


def group_num_setting(grupo: str, field: str, default: float = 0.0) -> float:
    """Lee un ajuste numérico del grupo (columna `field` de Grupos). Cacheado.

    Usado por los defaults de nómina (SuperDefault, RetencionDefault). `default`
    si el grupo/columna no está."""
    g = (grupo or "").strip().lower()
    if not g:
        return default
    for r in _group_records():
        if str(r.get("Grupo", "")).strip().lower() == g:
            raw = str(r.get(field, "")).strip()
            if raw == "":
                return default
            try:
                return float(raw.replace(",", "."))
            except Exception:
                return default
    return default


def set_group_num_setting(grupo: str, field: str, val) -> tuple:
    """Fija un ajuste numérico del grupo (columna `field`)."""
    gws, err = _get_groups_ws()
    if err:
        return False, err
    try:
        col = gws.row_values(1).index(field) + 1
    except ValueError:
        return False, f"{t('The column')} {field} {t('does not exist yet in the Groups sheet.')}"
    for i, r in enumerate(gws.get_all_records(numericise_ignore=["all"])):
        if str(r.get("Grupo", "")).strip().lower() == (grupo or "").strip().lower():
            try:
                gws.update_cell(i + 2, col, str(val))
                _invalidate_groups()
                return True, f"{field} actualizado."
            except Exception as e:
                return False, f"Error: {e}"
    return False, "Grupo no encontrado."


def group_tax_default(grupo: str) -> float:
    """Impuesto (%) por defecto del grupo para facturas (GST/IVA). `Grupos.ImpuestoDefault`.

    Editable por factura. Australia = 10 (GST). Lectura cacheada. 0.0 si no está."""
    g = (grupo or "").strip().lower()
    if not g:
        return 0.0
    for r in _group_records():
        if str(r.get("Grupo", "")).strip().lower() == g:
            try:
                return float(str(r.get("ImpuestoDefault", "") or 0).replace(",", "."))
            except Exception:
                return 0.0
    return 0.0


def set_group_tax_default(grupo: str, pct) -> tuple:
    """El propietario fija el impuesto % por defecto (GST/IVA) de un grupo."""
    gws, err = _get_groups_ws()
    if err:
        return False, err
    try:
        col = gws.row_values(1).index("ImpuestoDefault") + 1
    except ValueError:
        return False, t("The ImpuestoDefault column does not exist yet in the Groups sheet.")
    for i, r in enumerate(gws.get_all_records(numericise_ignore=["all"])):
        if str(r.get("Grupo", "")).strip().lower() == (grupo or "").strip().lower():
            try:
                gws.update_cell(i + 2, col, str(pct))
                _invalidate_groups()
                return True, t("Default tax updated.")
            except Exception as e:
                return False, f"Error: {e}"
    return False, "Grupo no encontrado."


def add_group(nombre: str, descripcion: str = "", zona: str = "") -> tuple:
    gws, err = _get_groups_ws()
    if err:
        return False, err
    nombre = (nombre or "").strip()
    if not nombre:
        return False, t("The group name is required.")
    for r in gws.get_all_records(numericise_ignore=["all"]):
        if str(r.get("Grupo", "")).strip().lower() == nombre.lower():
            return False, f"{t('Group')} '{nombre}' {t('already exists.')}"
    try:
        gws.append_row([nombre, descripcion, "SI", zona], value_input_option="RAW")
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
                return True, f"{t('Group')} '{nombre}' {t('deleted.')}"
            except Exception as e:
                return False, f"Error: {e}"
    return False, "Grupo no encontrado."


def _records(lws):
    return lws.get_all_records(numericise_ignore=["all"])


def _find_row(lws, usuario):
    """Devuelve (row_index_1based, record) o (None, None).

    ⚠️ Un fallo de la API se PROPAGA a propósito (no se traga aquí). `(None, None)`
    significa "el usuario no está en la hoja", y las rutas de sesión lo interpretan
    como EXPULSAR. Si esta función se tragara un 429/503 y devolviera `(None, None)`,
    un hipo de Google echaría a todo el mundo. Cada llamador decide qué hacer ante
    un error de lectura — ver `heartbeat`/`validate_session`/`start_session`.
    """
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
                return {"ok": False, "error": t("Inactive user.")}
            if verify_password(pw, str(r.get("Password", ""))):
                return {"ok": True,
                        "usuario": str(r.get("Usuario", "")),
                        "rol":     str(r.get("Rol", "campo")).strip().lower(),
                        "nombre":  str(r.get("Nombre", "")) or usuario,
                        "grupo":   str(r.get("Grupo", "")).strip()}
            return {"ok": False, "error": t("Wrong password.")}
    return {"ok": False, "error": t("User not found.")}


# ── Sesión única por cuenta ("primero gana") ─────────────────
# Motivo EXACTO del bloqueo por conflicto de sesión. Es una constante (y no un
# literal suelto) porque la UI la compara para decidir si ofrece el botón
# "cerrar la otra sesión e iniciar aquí": ese botón solo tiene sentido cuando
# hay otra sesión de verdad, no cuando la hoja no respondió.
#
# ⚠️ NO lleva `t()`: esto se evalúa AL IMPORTAR el módulo, cuando todavía no hay
# sesión, así que la traducción quedaría CONGELADA en el idioma de ese momento — y
# con el diccionario español lleno, el usuario vería inglés aquí y solo aquí. Peor
# aún: si alguien lo "arreglara" traduciendo un lado de la comparación y no el otro,
# `tok == SESION_OCUPADA` dejaría de casar y **el botón de «cerrar la otra sesión»
# desaparecería** sin dar ningún error. La constante es el CENTINELA (dato interno,
# se compara) y la traducción va donde se PINTA (`auth_ui`), que es la misma
# separación etiqueta/dato de todo el módulo i18n.
SESION_OCUPADA = "This account already has an active session on another device."


def _session_active(rec) -> bool:
    """¿La cuenta tiene una sesión viva? (token no vacío y heartbeat reciente)."""
    if not str(rec.get("SessionToken", "")).strip():
        return False
    # ⚠️ NO `t`: ese nombre es la función de traducción a nivel de módulo, y usarlo
    # aquí la taparía en TODO el ámbito de la función — el fallo de v437/v439/v440.
    # Renombrado ANTES de traducir, que es el orden que evita el daño (pre_i18n).
    try:
        _ts = int(float(rec.get("SessionTime", 0)))
    except Exception:
        _ts = 0
    return (int(time.time()) - _ts) < SESSION_TIMEOUT


def start_session(usuario: str) -> tuple:
    """Intenta abrir sesión única. (True, token) si la cuenta está libre;
    (False, motivo) si ya hay una sesión activa en otro dispositivo."""
    lws, err = _get_login_ws()
    if err:
        return False, err
    try:
        row, rec = _find_row(lws, usuario)
    except Exception:
        # Sin leer la hoja no se puede saber si la cuenta ya tiene sesión activa.
        # Se BLOQUEA (no se abre a ciegas) pero con un mensaje accionable.
        return False, t("Could not verify the session (the sheet did not respond). Try again in a few seconds.")
    if row is None:
        return False, t("User not found.")
    if _session_active(rec):
        return False, SESION_OCUPADA
    token = uuid.uuid4().hex
    try:
        lws.update_cell(row, _COL["SessionToken"], token)
        lws.update_cell(row, _COL["SessionTime"], str(int(time.time())))
    except Exception as e:
        return False, f"{t('Could not sign in')}: {e}"
    return True, token


def heartbeat(usuario: str, token: str) -> bool:
    """Marca vida si el token sigue vigente. False si fue desplazado (o expiró y lo tomó otro)."""
    lws, err = _get_login_ws()
    if err:
        return True   # error transitorio de la API → no expulsar
    try:
        row, rec = _find_row(lws, usuario)
    except Exception:
        # Misma razón que el `if err` de arriba: la lectura también puede fallar
        # por un 429/503 de Google. Sin esta guarda el traceback subía hasta app.py
        # y tumbaba la app entera — y el heartbeat es la PRIMERA llamada a Sheets
        # de cada carga de página, así que era siempre la que se comía el fallo.
        return True
    if row is None:
        return False
    if str(rec.get("SessionToken", "")).strip() != str(token):
        return False
    try:
        lws.update_cell(row, _COL["SessionTime"], str(int(time.time())))
    except Exception as e:
        # El silencio es DELIBERADO (v289: un hipo de la API no puede tumbar la
        # app, y el heartbeat es la primera llamada de cada carga). Pero mudo del
        # todo tampoco: sin rastro, una racha de 429 parece "la sesión se cae sola".
        logger.warning("auth: heartbeat de %s no pudo escribir: %s", usuario, e)
    return True


def validate_session(usuario: str, token: str) -> dict:
    """Para el login persistente (cookie): si el token coincide con la sesión viva
    del usuario, devuelve sus datos de login; si no, {}."""
    if not (str(usuario).strip() and str(token).strip()):
        return {}
    lws, err = _get_login_ws()
    if err:
        return {}
    try:
        _, rec = _find_row(lws, usuario)
    except Exception:
        return {}   # no se pudo leer → no restaurar (se pide login, no se rompe)
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
        return False, t("User not found.")
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
        except Exception as e:
            # ⚠️ Si esto falla, el token sigue vivo en la hoja y la sesión única
            # (v75) BLOQUEA el siguiente login durante 180 s: el usuario cierra
            # sesión, vuelve a entrar y le dice "ya hay una sesión activa".
            logger.warning("auth: no se pudo liberar la sesión de %s: %s "
                           "→ su próximo login puede salir bloqueado", usuario, e)


# ── Gestión de usuarios ──────────────────────────────────────
# ⚠️ Lo que NUNCA sale de `list_users`: el hash de la contraseña y el token de sesión.
# La proyección existe por eso (v79: la tabla de usuarios no enseña el hash), no por
# capricho — así que no se puede sustituir por «devuelve la fila entera».
_CAMPOS_SECRETOS = ("Password", "SessionToken", "SessionTime")


def list_users(grupo: str = None) -> list:
    """Todos los usuarios, o solo los de un grupo si se indica (lectura cacheada).

    ⚠️ Devuelve **todas las columnas de `LOGIN_HEADERS` menos las secretas**, no una
    lista escrita a mano. Estaba a mano y, al añadir `FechaIngreso` (v433), el dato se
    guardaba bien y **`list_users` lo borraba al leerlo**: la hoja tenía la fecha y
    cualquier pantalla que preguntara por aquí veía "". No lanza, no avisa — la
    columna simplemente no existe para quien la lee. Misma familia que `auth._COL`
    escrito a mano: dos sitios que describen las mismas columnas.
    """
    _campos = [h for h in LOGIN_HEADERS if h not in _CAMPOS_SECRETOS]
    out = []
    for r in _login_records_cached():
        g = str(r.get("Grupo", "")).strip()
        if grupo is not None and g.lower() != grupo.strip().lower():
            continue
        fila = {h: str(r.get(h, "")) for h in _campos}
        fila["Grupo"] = g
        fila["Activo"] = str(r.get("Activo", "SI"))
        out.append(fila)
    return out


def fecha_ingreso(usuario: str):
    """Fecha de alta en la empresa como `date`, o None si no está puesta.

    ⚠️ Devuelve None —no una fecha inventada— cuando falta o no se entiende: quien
    llama tiene que poder DECIR que está estimando, en vez de enseñar un saldo que
    parece exacto (el patrón de v325 con «sin tarifa» vs «de baja»).
    """
    from core.num import parse_date as _pd
    try:
        return _pd((get_user(usuario) or {}).get("FechaIngreso"))
    except Exception:
        return None


def set_fecha_ingreso(usuario: str, fecha) -> tuple:
    """Fija la fecha de alta (ISO). Decide el año de vacaciones de esa persona."""
    lws, err = _get_login_ws()
    if err:
        return False, err
    row, rec = _find_row(lws, usuario)
    if row is None:
        return False, t("User not found.")
    _antes = dict(rec or {})
    _val = "" if not fecha else str(fecha)[:10]
    try:
        lws.update_cell(row, _COL["FechaIngreso"], _val)
    except Exception as e:
        return False, f"Error: {e}"
    _invalidate_login()
    # v342: mueve el saldo de vacaciones de esa persona → deja rastro.
    try:
        from core import auditoria
        auditoria.registrar("usuario", usuario,
                            auditoria.diff(_antes, {"FechaIngreso": _val}),
                            grupo=str(_antes.get("Grupo", "")))
    except Exception as e:
        logger.warning("auth.set_fecha_ingreso: auditoría: %s", e)
    return True, t("Start date updated.")


def set_rate(usuario: str, tarifa) -> tuple:
    """Tarifa por hora del usuario (para costear la mano de obra)."""
    lws, err = _get_login_ws()
    if err:
        return False, err
    row, rec = _find_row(lws, usuario)
    if row is None:
        return False, t("User not found.")
    _antes = dict(rec or {})            # v342: el ANTES, de la fila que ya se leyó
    try:
        lws.update_cell(row, _COL["TarifaHora"], str(tarifa))
    except Exception as e:
        return False, f"Error: {e}"
    _invalidate_login()
    # ⚠️ v342: la tarifa decide lo que se le paga a una persona y lo que se le cobra
    # al cliente. Es el cambio que más merece dejar rastro.
    try:
        from core import auditoria
        auditoria.registrar("usuario", usuario,
                            auditoria.diff(_antes, {"TarifaHora": tarifa}),
                            grupo=str(_antes.get("Grupo", "")))
    except Exception as e:
        # Deja RASTRO (regla v323): `registrar` logea lo suyo, pero si revienta
        # `diff` o el import, el apunte se perdía en silencio.
        logger.warning("auth: no se pudo auditar la tarifa de %s: %s", usuario, e)
    return True, f"{t('Rate for')} '{usuario}' {t('updated.')}"


def etiqueta_usuarios(users) -> dict:
    """`{usuario: etiqueta}` — el Nombre, con el LOGIN detrás **solo si se repite**.

    Misma regla que `projects.etiqueta_proyectos` (v306) aplicada a las personas: el
    login es la identidad y el nombre es comodidad, y el nombre PUEDE repetirse. En el
    grupo real hay dos logins llamados `lksdfkldsf` y dos `fijiofgjei`, así que una
    tabla que muestre solo el nombre deja filas que no se pueden distinguir — pasó en
    Nóminas (v319) y ya había pasado en el reporte de Horas (v151).

    `users` = iterable de dicts con `Usuario` y `Nombre`.
    """
    _n = {}
    for u in users or []:
        _n[str(u.get("Nombre") or "")] = _n.get(str(u.get("Nombre") or ""), 0) + 1
    out = {}
    for u in users or []:
        _u = str(u.get("Usuario") or "")
        _nom = str(u.get("Nombre") or "") or _u
        out[_u] = f"{_nom} ({_u})" if _n.get(str(u.get("Nombre") or ""), 0) > 1 else _nom
    return out


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


def claves_conocidas(grupo: str = None) -> set:
    """Las claves (Usuario **y** Nombre) de la gente que SIGUE dada de alta (v325).

    Sirve para distinguir dos cosas que se veían iguales y no lo son: alguien con
    horas fichadas y tarifa 0 puede ser **una tarifa que falta poner** (se arregla
    en Usuarios) o **una cuenta que ya no existe** (p. ej. el rol conductor, que se
    eliminó en v163, dejando sus fichajes históricos huérfanos). Lo segundo NO se
    arregla poniendo una tarifa: no hay fila donde ponerla.

    ⚠️ Sin `grupo` mira TODA la hoja: alguien movido a otro grupo sigue existiendo,
    y decir que "ya no está" sería falso. Sale de `list_users` (cacheado) → 0
    llamadas nuevas a Sheets.
    """
    out = set()
    for u in list_users(grupo):
        for k in ("Usuario", "Nombre"):
            v = str(u.get(k, "") or "").strip()
            if v:
                out.add(v)
    return out


def add_user(usuario: str, pw: str, rol: str, nombre: str = "",
             grupo: str = "", activo: bool = True) -> tuple:
    lws, err = _get_login_ws()
    if err:
        return False, err
    usuario = (usuario or "").strip()
    if not usuario or not pw:
        return False, t("Username and password are required.")
    if rol not in ROLES:
        return False, t("Invalid role.")
    if rol in ("administrador", "campo") and not (grupo or "").strip():
        return False, t("Administrator and field users must belong to a group.")
    row, _ = _find_row(lws, usuario)
    if row is not None:
        return False, f"{t('User')} '{usuario}' {t('already exists.')}"
    try:
        lws.append_row([usuario, hash_password(pw), rol, nombre or usuario,
                        "SI" if activo else "NO", (grupo or "").strip()],
                       value_input_option="RAW")
    except Exception as e:
        return False, f"{t('Error creating user')}: {e}"
    _invalidate_login()
    return True, f"{t('User')} '{usuario}' {t('created')} ({rol})."


def set_group(usuario: str, grupo: str) -> tuple:
    lws, err = _get_login_ws()
    if err:
        return False, err
    row, _ = _find_row(lws, usuario)
    if row is None:
        return False, t("User not found.")
    try:
        lws.update_cell(row, _COL["Grupo"], (grupo or "").strip())
    except Exception as e:
        return False, f"Error: {e}"
    _invalidate_login()
    return True, f"{t('Group for')} '{usuario}' → {grupo or t('(no group)')}."


def set_password(usuario: str, pw: str) -> tuple:
    lws, err = _get_login_ws()
    if err:
        return False, err
    if not pw:
        return False, t("The password cannot be empty.")
    row, _ = _find_row(lws, usuario)
    if row is None:
        return False, t("User not found.")
    try:
        lws.update_cell(row, 2, hash_password(pw))
    except Exception as e:
        return False, f"Error: {e}"
    _invalidate_login()
    return True, f"{t('Password for')} '{usuario}' {t('updated.')}"


def set_role(usuario: str, rol: str) -> tuple:
    if rol not in ROLES:
        return False, t("Invalid role.")
    lws, err = _get_login_ws()
    if err:
        return False, err
    row, _ = _find_row(lws, usuario)
    if row is None:
        return False, t("User not found.")
    try:
        lws.update_cell(row, 3, rol)
    except Exception as e:
        return False, f"Error: {e}"
    _invalidate_login()
    return True, f"{t('Role for')} '{usuario}' → {rol}."


def set_active(usuario: str, activo: bool) -> tuple:
    lws, err = _get_login_ws()
    if err:
        return False, err
    row, _ = _find_row(lws, usuario)
    if row is None:
        return False, t("User not found.")
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
        return False, t("User not found.")
    try:
        lws.delete_rows(row)
    except Exception as e:
        return False, f"Error: {e}"
    _invalidate_login()
    return True, f"{t('User')} '{usuario}' {t('deleted.')}"


# ── Helpers de rol ───────────────────────────────────────────
def can_reports(rol: str) -> bool:
    return rol in ("propietario", "administrador")



# ── Libro propio por cliente (v359) ──────────────────────────────
def group_sheet_id(grupo: str) -> str:
    """ID del libro de Google de este grupo. Vacío = usa el maestro.

    ⚠️ Lee de `Grupos`, que es una hoja GLOBAL: `timeclock` la resuelve al maestro
    ANTES de preguntar aquí, o esto se llamaría a sí mismo sin fin.
    """
    if not grupo:
        return ""
    for g in _group_records():
        if str(g.get("Grupo", "")).strip().casefold() == str(grupo).strip().casefold():
            return str(g.get("SheetID", "") or "").strip()
    return ""


def set_group_sheet_id(grupo: str, sheet_id) -> tuple:
    """Enlaza el grupo con su libro. `sheet_id` vacío lo devuelve al maestro."""
    gws, err = _get_groups_ws()
    if err:
        return False, err
    sid = str(sheet_id or "").strip()
    # ⚠️ Se acepta la URL completa además del ID: es lo que se copia del navegador.
    if "/spreadsheets/d/" in sid:
        sid = sid.split("/spreadsheets/d/")[1].split("/")[0]
    if sid:
        otros = [str(g.get("Grupo")) for g in _group_records()
                 if str(g.get("SheetID", "")).strip() == sid
                 and str(g.get("Grupo", "")).strip().casefold() != str(grupo).strip().casefold()]
        if otros:
            # dos clientes en el mismo libro es justo lo que este cambio viene a evitar
            return False, f"{t('That workbook already belongs to')}: {', '.join(otros)}."
    try:
        recs = gws.get_all_records(numericise_ignore=["all"])
    except Exception as e:
        return False, f"Error leyendo: {e}"
    for i, g in enumerate(recs):
        if str(g.get("Grupo", "")).strip().casefold() == str(grupo).strip().casefold():
            try:
                gws.update_cell(i + 2, GROUPS_HEADERS.index("SheetID") + 1, sid)
            except Exception as e:
                return False, f"Error guardando: {e}"
            _invalidate_groups()
            try:
                from core import timeclock
                timeclock.invalidar_libros()
            except Exception:
                pass
            return True, ("Libro enlazado." if sid else t("Group returned to the master workbook."))
    return False, "Grupo no encontrado."


def grupos_con_libro_propio() -> list:
    """Grupos que ya viven en su propio libro de Google (v359).

    Lo usan las vistas CONSOLIDADAS del propietario para avisar de que su resumen
    no los incluye todavía (ver el límite documentado en v359)."""
    return [str(g.get("Grupo", "")) for g in _group_records()
            if str(g.get("SheetID", "") or "").strip()]


def grupos_por_libro() -> list:
    """UN grupo representante por cada LIBRO distinto (v379).

    Es lo que necesitan las vistas del propietario para recorrer todos los clientes:
    se lee una vez POR LIBRO, no una vez por grupo.

    ⚠️ Si tres grupos comparten el maestro, leerlo tres veces **triplicaría las
    filas** — y cada fila ya lleva su columna `Grupo`, así que una sola lectura del
    libro trae lo de los tres. Agrupar por libro no es una optimización: es lo que
    evita duplicar datos en el consolidado.
    """
    vistos, out = set(), []
    for g in _group_records():
        nombre = str(g.get("Grupo", "")).strip()
        if not nombre:
            continue
        sid = str(g.get("SheetID", "") or "").strip()      # vacío = el maestro
        if sid in vistos:
            continue
        vistos.add(sid)
        out.append((nombre, sid))
    return out
