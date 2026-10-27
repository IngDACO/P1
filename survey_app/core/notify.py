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
import html
import logging
import re

from core.i18n import d as _d
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


# ── ¿Qué contacto necesita un usuario de campo para usar la app? (v613) ──────
# ⚠️ Decisión del usuario (27/10/2026): «vamos a desactivar POR AHORA que se tenga que ligar a un
# Telegram para poder loguear», para probar con más usuarios de campo ficticios — un chat_id es una
# conversación REAL y no se inventa, así que con el Telegram obligatorio solo podía entrar uno. El
# email SIGUE siendo obligatorio. Para volver a exigirlo: True (la puerta de `app.py`, el resumen
# del admin y los paneles de usuarios leen esta MISMA regla: `contacto_campo_ok`).
TELEGRAM_OBLIGATORIO_CAMPO = False


def exige_telegram_campo() -> bool:
    """¿Se le exige el Telegram al campo? Solo si la política lo pide Y el bot existe (v368: no
    se exige un canal que no hay — sería un bloqueo sin salida)."""
    return bool(TELEGRAM_OBLIGATORIO_CAMPO and telegram_configured() and bot_username())


def contacto_campo_ok(u) -> bool:
    """La UNA definición de «el contacto de este usuario de campo está completo» (v613): el
    email siempre; el Telegram, solo si se exige. Antes la puerta, el resumen del admin y tres
    paneles pedían los dos por su cuenta: con la política cambiada habrían dicho «no puede usar
    la app» de quien sí puede."""
    u = u or {}
    if not str(u.get("Email", "")).strip():
        return False
    return (not exige_telegram_campo()) or bool(str(u.get("TelegramChatID", "")).strip())


def _tg(method: str) -> str:
    return f"https://api.telegram.org/bot{_sec('TELEGRAM_BOT_TOKEN')}/{method}"


def send_telegram(chat_id, text: str) -> bool:
    r = requests.post(_tg("sendMessage"),
                      json={"chat_id": chat_id, "text": text, "parse_mode": "HTML",
                            "disable_web_page_preview": True}, timeout=15)
    return r.ok


def telegram_diagnostico(code: str) -> dict:
    """Busca el chat_id **y dice POR QUÉ** si no lo encuentra.

    Devuelve {chat_id, motivo, detalle, n_updates}. `motivo` es una de:
      · ''            → encontrado
      · 'sin_token'   → no hay bot configurado en los secrets
      · 'webhook'     → ⚠️ hay un webhook activo: `getUpdates` NO puede leer nada
      · 'sin_mensajes'→ Telegram no tiene ningún mensaje pendiente para el bot
      · 'sin_codigo'  → llegaron mensajes, pero ninguno trae el código
      · 'error'       → la llamada falló (red, token inválido…)

    ⚠️ Existe porque antes las CINCO situaciones devolvían `None` y la pantalla decía
    lo mismo para todas, así que no había forma de saber qué arreglar (v325/v340).
    """
    if not telegram_configured():
        return {"chat_id": None, "motivo": "sin_token", "detalle": "", "n_updates": 0}
    try:
        r = requests.get(_tg("getUpdates"), params={"timeout": 0}, timeout=15)
        j = r.json()
    except Exception as e:
        logger.warning("telegram getUpdates: %s", e)
        return {"chat_id": None, "motivo": "error", "detalle": str(e), "n_updates": 0}

    # ⚠️ `requests` NO lanza con un status de error, así que un 409 —el que devuelve
    # Telegram cuando hay un WEBHOOK activo— llegaba aquí como una respuesta normal
    # con `result` vacío: sin excepción, sin log y sin pista de qué pasaba.
    if not j.get("ok", False):
        _cod = j.get("error_code")
        _des = str(j.get("description", ""))
        _motivo = "webhook" if (_cod == 409 or "webhook" in _des.lower()) else "error"
        logger.warning("telegram getUpdates no ok (%s): %s", _cod, _des)
        return {"chat_id": None, "motivo": _motivo, "detalle": _des, "n_updates": 0}

    ups = j.get("result", []) or []
    for u in reversed(ups):
        m = u.get("message") or {}
        if str(code) in str(m.get("text", "")):
            return {"chat_id": str(m.get("chat", {}).get("id", "")), "motivo": "",
                    "detalle": "", "n_updates": len(ups)}
    return {"chat_id": None,
            "motivo": "sin_mensajes" if not ups else "sin_codigo",
            "detalle": "", "n_updates": len(ups)}


def telegram_find_chat_by_code(code: str):
    """El chat_id de quien mandó '/start <code>', o None.

    ⚠️ UNA sola definición de la búsqueda: delega en `telegram_diagnostico` en vez de
    repetir el recorrido (la lección de los cinco `_num` divergentes de v323).
    """
    return telegram_diagnostico(code).get("chat_id")


# ── Alto nivel ───────────────────────────────────────────────────
def any_channel_configured() -> bool:
    return email_configured() or telegram_configured()


# v603 · las etiquetas que la app pone A PROPÓSITO en un aviso (y que Telegram admite)
_ETQ_OK = re.compile(r"&lt;(/?(?:b|i|u|s|code|pre)|br\s*/?)&gt;")
_A_OK = re.compile(r'&lt;a href="([^"<>]*)"&gt;')


def html_seguro(texto: str) -> str:
    """v603 · El cuerpo de un aviso con el texto de las PERSONAS escapado.

    ⚠️ Los avisos llevan en HTML (correo y Telegram, `parse_mode` HTML) lo que alguien
    escribió: la alarma del campo, el nombre de la obra, la dirección, la lectura de la IA. Sin
    escapar, «hueco < 20 mm & riel torcido» llegaba RECORTADO por correo (el «<…» se lee como
    una etiqueta: medido en el navegador, «Shop 3 <Ground> & 4» salía «Shop 3 & 4»), y
    Telegram pide escapar todo «<», «>» y «&» que no sean una etiqueta (su documentación),
    así que el aviso podía no llegar. Se escapa TODO y se devuelven las etiquetas de la app
    (`<b>`, `<i>`, `<a href="…">`, `<br>`…): ninguna llamada tiene que acordarse.
    """
    s = html.escape(str(texto or ""), quote=False)
    s = _ETQ_OK.sub(r"<\1>", s)
    s = _A_OK.sub(r'<a href="\1">', s)
    return s.replace("&lt;/a&gt;", "</a>")


def notify_user(usuario: str, subject: str, lines: list, link: str = None) -> dict:
    """Envía a `usuario` por los canales que tenga configurados. Devuelve {email, telegram}."""
    rec = auth.get_user(usuario)
    res = {"email": False, "telegram": False}
    if not rec:
        return res
    text = "\n".join(lines)
    if link:
        text += f"\n\n{link}"
    text = html_seguro(text)                      # v603 · el texto ajeno, escapado
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
    nombre = prj.get("Name") or prj.get("nombre") or ""
    subject = f"📋 {_d("New project assigned")}: {nombre}"
    _ubic = str(prj.get("Location", "") or "")
    _ubic_url = maps.maps_url(_ubic)
    _ubic_line = (f'{_d("Location")}: <a href="{_ubic_url}">{_ubic}</a>' if _ubic_url
                  else f"{_d("Location")}: {_ubic or '—'}")
    lines = [
        f"{_d("You have been assigned to project")} <b>{nombre}</b>.",
        f"{_d("Client")}: {prj.get('Client', '—')}",
        _ubic_line,
        f"{_d("Start")}: {prj.get('StartDate', '—')}  ·  "
        f"{_d("Est. finish")}: {prj.get('EndDateEst', '—')}",
    ]
    _links = [l.strip() for l in str(prj.get("InductionLinks", "") or "").splitlines() if l.strip()]
    if _links:
        lines.append(f"📝 <b>{_d("Inductions to complete")}:</b>")
        lines += [f'• <a href="{l}">{l}</a>' for l in _links]
    lines.append(_d("Open it in the app → 📋 My projects."))
    return notify_user(usuario, subject, lines, _sec("APP_URL", _APP_URL_DEFAULT))


def notify_induction(usuario: str, project_name: str, links: list) -> dict:
    """Envía (o reenvía) los links de inducción de un proyecto a un usuario de campo."""
    links = [str(l).strip() for l in (links or []) if str(l).strip()]
    if not links:
        return {"email": False, "telegram": False}
    subject = f"📝 {_d("Project inductions")}: {project_name}"
    lines = [f"{_d("Complete the inductions for project")} <b>{project_name}</b>:"]
    lines += [f'• <a href="{l}">{l}</a>' for l in links]
    return notify_user(usuario, subject, lines)
