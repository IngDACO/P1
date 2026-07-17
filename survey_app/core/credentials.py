"""
Credenciales / tickets por usuario (White Card, Forklift, Dogging/Rigging, EWP,
licencia de conducir, etc.) con vencimiento, foto/documento en Drive y avisos.

Hoja `Credenciales`. El admin/propietario las gestiona (crea al usuario o después);
cada usuario ve las suyas en solo lectura. Las que están por vencer/vencidas entran
al radar del admin (admin_digest) y se avisan por email/Telegram (deduplicado).
"""
import logging
from datetime import date, datetime

import streamlit as st

from core import timeclock

logger = logging.getLogger(__name__)

SHEET   = "Credenciales"
HEADERS = ["ID", "Usuario", "Grupo", "Tipo", "Numero", "Clase", "Emision",
           "Vencimiento", "DriveID", "Archivo", "Nota", "UltimoAviso",
           "ActualizadoPor", "Fecha"]

# Catálogo de tipos (construcción AU) + "Otro" libre
CATALOGO = [
    "White Card", "Forklift (LF)", "Dogging (DG)", "Rigging Basic (RB)",
    "Rigging Intermediate (RI)", "Rigging Advanced (RA)", "EWP / Boom (WP)",
    "Working at Heights", "First Aid", "Driver License", "Otro",
]
CLASES_LICENCIA = ["", "C", "LR", "MR", "HR", "HC", "MC"]

DIAS_AVISO = 30   # umbral "por vencer"
FMT_FECHA  = "%Y-%m-%d"


def is_configured() -> bool:
    return timeclock._secrets_present()


def _ws():
    if not timeclock._secrets_present():
        return None
    try:
        return timeclock.get_sheet(SHEET, tuple(HEADERS))
    except Exception as e:
        logger.warning("credentials: no se pudo abrir la hoja: %s", e)
        return None


@st.cache_data(ttl=30, show_spinner=False)
def _records() -> list:
    w = _ws()
    if w is None:
        return []
    try:
        return w.get_all_records(numericise_ignore=["all"])
    except Exception:
        return []


def _invalidate():
    try:
        _records.clear()
    except Exception:
        pass


def _col(h):
    return HEADERS.index(h) + 1


def _col_letter(n):
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _parse(d):
    for f in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(d).strip()[:10], f).date()
        except Exception:
            pass
    return None


def status(vencimiento) -> str:
    """'' (sin vencimiento) | 'vigente' | 'por_vencer' (≤30 d) | 'vencido'."""
    v = _parse(vencimiento)
    if not v:
        return ""
    dd = (v - date.today()).days
    if dd < 0:
        return "vencido"
    if dd <= DIAS_AVISO:
        return "por_vencer"
    return "vigente"


def status_label(vencimiento) -> str:
    return {"vigente": "🟢 vigente", "por_vencer": "🟡 por vencer",
            "vencido": "🔴 vencido", "": "—"}[status(vencimiento)]


def dias_para(vencimiento):
    v = _parse(vencimiento)
    return (v - date.today()).days if v else None


# ── Lecturas ─────────────────────────────────────────────────────
def list_for(usuario) -> list:
    u = str(usuario or "").strip().lower()
    return [r for r in _records() if str(r.get("Usuario", "")).strip().lower() == u]


def list_group(grupo) -> list:
    g = str(grupo or "").strip()
    return [r for r in _records() if str(r.get("Grupo", "")) == g]


def expiring(grupo, days=DIAS_AVISO) -> list:
    """Credenciales del grupo por vencer (≤days) o vencidas, ordenadas por urgencia."""
    out = []
    for r in list_group(grupo):
        dd = dias_para(r.get("Vencimiento"))
        if dd is not None and dd <= days:
            out.append({"usuario": r.get("Usuario", ""), "tipo": r.get("Tipo", ""),
                        "vencimiento": r.get("Vencimiento", ""), "dias": dd,
                        "estado": status(r.get("Vencimiento"))})
    out.sort(key=lambda x: x["dias"])
    return out


# ── Escrituras ───────────────────────────────────────────────────
def _next_id(recs) -> str:
    mx = 0
    for r in recs:
        i = str(r.get("ID", ""))
        if i.startswith("CR-"):
            try:
                mx = max(mx, int(i.split("-")[1]))
            except Exception:
                pass
    return f"CR-{mx + 1:04d}"


def add(usuario, grupo, tipo, numero="", clase="", emision="", vencimiento="",
        drive_id="", archivo="", nota="", actualizado_por="") -> tuple:
    w = _ws()
    if w is None:
        return False, "Google Sheets no está configurado."
    if not str(tipo).strip():
        return False, "El tipo de credencial es obligatorio."
    try:
        cid = _next_id(w.get_all_records(numericise_ignore=["all"]))
        w.append_row([cid, str(usuario), str(grupo), str(tipo), str(numero), str(clase),
                      str(emision), str(vencimiento), str(drive_id), str(archivo),
                      str(nota), "", str(actualizado_por),
                      datetime.now().strftime("%Y-%m-%d %H:%M")],
                     value_input_option="RAW")
    except Exception as e:
        return False, f"Error guardando: {e}"
    _invalidate()
    return True, f"Credencial «{tipo}» agregada."


def update(cred_id, fields: dict) -> tuple:
    w = _ws()
    if w is None:
        return False, "Google Sheets no está configurado."
    try:
        recs = w.get_all_records(numericise_ignore=["all"])
    except Exception as e:
        return False, f"Error leyendo: {e}"
    for i, r in enumerate(recs):
        if str(r.get("ID", "")) == str(cred_id):
            row = i + 2
            batch = [{"range": f"{_col_letter(_col(k))}{row}", "values": [[str(v)]]}
                     for k, v in fields.items() if k in HEADERS]
            if batch:
                try:
                    w.batch_update(batch, value_input_option="RAW")
                except Exception as e:
                    return False, f"Error actualizando: {e}"
            _invalidate()
            return True, "Credencial actualizada."
    return False, "Credencial no encontrada."


def delete(cred_id) -> tuple:
    w = _ws()
    if w is None:
        return False, "Google Sheets no está configurado."
    try:
        recs = w.get_all_records(numericise_ignore=["all"])
    except Exception as e:
        return False, f"Error leyendo: {e}"
    for i, r in enumerate(recs):
        if str(r.get("ID", "")) == str(cred_id):
            did = str(r.get("DriveID", "")).strip()
            if did:
                try:
                    from core import drive_store
                    drive_store.delete(did)
                except Exception:
                    pass
            try:
                w.delete_rows(i + 2)
            except Exception as e:
                return False, f"Error: {e}"
            _invalidate()
            return True, "Credencial eliminada."
    return False, "Credencial no encontrada."


_FOLDER = "COPEX Credenciales"


def upload_file(usuario, tipo, filename, data, mime="application/octet-stream") -> str:
    """Sube la foto/documento de una credencial a Drive. Devuelve el fileId (o '')."""
    try:
        from core import drive_store
        if not drive_store.is_available():
            return ""
        safe = f"{usuario}_{tipo}_{filename}".replace("/", "-").replace(" ", "_")
        return drive_store.upload_to(drive_store.folder(_FOLDER), safe, data, mime)
    except Exception as e:
        logger.warning("credentials.upload_file: %s", e)
        return ""


# ── Avisos de vencimiento (deduplicado por UltimoAviso) ───────────
def notify_expiring(grupo, days=DIAS_AVISO) -> int:
    """Avisa (email/Telegram) al admin/propietario + al usuario dueño de cada credencial
    por vencer/vencida, sin repetir dentro de ~25 días. Devuelve nº de avisos enviados."""
    w = _ws()
    if w is None:
        return 0
    try:
        from core import notify, auth
    except Exception:
        return 0
    try:
        recs = w.get_all_records(numericise_ignore=["all"])
    except Exception:
        return 0

    # destinatarios admin/propietario del grupo
    admins = []
    try:
        for u in auth.list_users():
            rol = str(u.get("Rol", "")).lower()
            if rol == "propietario" or (rol == "administrador" and str(u.get("Grupo", "")) == str(grupo)):
                admins.append(u["Usuario"])
    except Exception:
        pass

    hoy = date.today()
    enviados = 0
    for i, r in enumerate(recs):
        if str(r.get("Grupo", "")) != str(grupo):
            continue
        dd = dias_para(r.get("Vencimiento"))
        if dd is None or dd > days:
            continue
        # dedup: no reenviar si ya se avisó hace <25 días
        ult = _parse(r.get("UltimoAviso"))
        if ult and (hoy - ult).days < 25:
            continue
        tipo = r.get("Tipo", "")
        usr  = r.get("Usuario", "")
        estado = "VENCIDA" if dd < 0 else f"vence en {dd} d"
        subject = f"🎫 Credencial {estado}: {tipo} ({usr})"
        lines = [f"La credencial <b>{tipo}</b> de <b>{usr}</b> {('está VENCIDA' if dd < 0 else f'vence en {dd} días')}"
                 f" ({r.get('Vencimiento','')}).", "Actualízala en la app → Usuarios → Credenciales."]
        dests = list(dict.fromkeys(admins + [usr]))
        sent_any = False
        for d in dests:
            try:
                rr = notify.notify_user(d, subject, lines)
                if rr.get("email") or rr.get("telegram"):
                    sent_any = True
            except Exception:
                pass
        if sent_any:
            enviados += 1
            try:
                w.update_cell(i + 2, _col("UltimoAviso"), hoy.strftime(FMT_FECHA))
            except Exception:
                pass
    if enviados:
        _invalidate()
    return enviados
