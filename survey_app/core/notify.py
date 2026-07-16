"""
Notificaciones gratuitas (Email + Telegram) — p.ej. al asignar un proyecto a un
usuario de campo, se le avisa al instante con los datos del proyecto.

Secrets:
  GMAIL_USER / GMAIL_APP_PASS   (email; ya existen para el informe admin)
  TELEGRAM_BOT_TOKEN            (bot de Telegram, de @BotFather)
  TELEGRAM_BOT_USERNAME         (sin @; para el link de vinculación)
  APP_URL                       (link a la app; opcional)

Degrada con gracia: usa los canales configurados y para los que el usuario tenga contacto.
"""
import logging
import smtplib
from email.mime.text import MIMEText

import requests
import streamlit as st

from core import auth

logger = logging.getLogger(__name__)
_APP_URL_DEFAULT = "https://dwl6s39d7u3yfwfkbpcpah.streamlit.app/"


def _sec(k, d=""):
    try:
        return st.secrets.get(k, d)
    except Exception:
        return d


# ── Email (Gmail SMTP) ───────────────────────────────────────────
def email_configured() -> bool:
    return bool(_sec("GMAIL_USER") and _sec("GMAIL_APP_PASS"))


def send_email(to: str, subject: str, html: str) -> bool:
    u, p = _sec("GMAIL_USER"), _sec("GMAIL_APP_PASS")
    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = u
    msg["To"] = to
    with smtplib.SMTP("smtp.gmail.com", 587) as s:
        s.starttls()
        s.login(u, p)
        s.sendmail(u, [to], msg.as_bytes())
    return True


# ── Telegram (Bot API) ───────────────────────────────────────────
def telegram_configured() -> bool:
    return bool(_sec("TELEGRAM_BOT_TOKEN"))


def bot_username() -> str:
    return str(_sec("TELEGRAM_BOT_USERNAME", "")).lstrip("@")


def _tg(method: str) -> str:
    return f"https://api.telegram.org/bot{_sec('TELEGRAM_BOT_TOKEN')}/{method}"


def send_telegram(chat_id, text: str) -> bool:
    r = requests.post(_tg("sendMessage"),
                      json={"chat_id": chat_id, "text": text, "parse_mode": "HTML",
                            "disable_web_page_preview": True}, timeout=15)
    return r.ok


def telegram_find_chat_by_code(code: str):
    """Busca en getUpdates un mensaje '/start <code>' y devuelve el chat_id (vinculación)."""
    try:
        r = requests.get(_tg("getUpdates"), params={"timeout": 0}, timeout=15)
        for u in reversed(r.json().get("result", [])):
            m = u.get("message") or {}
            if str(code) in str(m.get("text", "")):
                return str(m.get("chat", {}).get("id", ""))
    except Exception as e:
        logger.warning("telegram getUpdates: %s", e)
    return None


# ── Alto nivel ───────────────────────────────────────────────────
def any_channel_configured() -> bool:
    return email_configured() or telegram_configured()


def notify_user(usuario: str, subject: str, lines: list, link: str = None) -> dict:
    """Envía a `usuario` por los canales que tenga configurados. Devuelve {email, telegram}."""
    rec = auth.get_user(usuario)
    res = {"email": False, "telegram": False}
    if not rec:
        return res
    text = "\n".join(lines)
    if link:
        text += f"\n\n{link}"
    email = str(rec.get("Email", "")).strip()
    if email and email_configured():
        try:
            res["email"] = send_email(email, subject, text.replace("\n", "<br>"))
        except Exception as e:
            logger.warning("notify email a %s: %s", usuario, e)
    tg = str(rec.get("TelegramChatID", "")).strip()
    if tg and telegram_configured():
        try:
            res["telegram"] = send_telegram(tg, text)
        except Exception as e:
            logger.warning("notify telegram a %s: %s", usuario, e)
    return res


def notify_assignment(usuario: str, prj: dict) -> dict:
    """Avisa a un usuario de campo que le asignaron un proyecto (con sus datos)."""
    from core import maps
    nombre = prj.get("Nombre") or prj.get("nombre") or ""
    subject = f"📋 Nuevo proyecto asignado: {nombre}"
    _ubic = str(prj.get("Ubicacion", "") or "")
    _ubic_url = maps.maps_url(_ubic)
    _ubic_line = (f'Ubicación: <a href="{_ubic_url}">{_ubic}</a>' if _ubic_url
                  else f"Ubicación: {_ubic or '—'}")
    lines = [
        f"Te asignaron al proyecto <b>{nombre}</b>.",
        f"Cliente: {prj.get('Cliente', '—')}",
        _ubic_line,
        f"Inicio: {prj.get('FechaInicio', '—')}  ·  Fin est.: {prj.get('FechaFinEst', '—')}",
        "Ábrelo en la app → 📋 Mis proyectos.",
    ]
    return notify_user(usuario, subject, lines, _sec("APP_URL", _APP_URL_DEFAULT))
