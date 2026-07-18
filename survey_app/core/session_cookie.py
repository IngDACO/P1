"""
Login persistente con cookie: la sesión sobrevive al refresco del navegador.

Guarda `usuario|token` (el mismo token de la sesión única) en una cookie del
navegador. Al abrir la app se valida contra la hoja Login: si el token sigue
siendo el de la sesión viva, se restaura la sesión sin volver a escribir la clave.

Usa `extra-streamlit-components` con **import perezoso**: si la librería no está
disponible, la app funciona igual, solo que sin persistencia (comportamiento previo).
"""
from datetime import datetime, timedelta

_COOKIE = "copex_session"
_DIAS   = 7


def _mgr():
    try:
        import extra_streamlit_components as stx
    except Exception:
        return None
    try:
        return stx.CookieManager(key="copex_cookie_mgr")
    except Exception:
        return None


def load() -> tuple:
    """(usuario, token) de la cookie, o (None, None)."""
    m = _mgr()
    if m is None:
        return None, None
    try:
        raw = m.get(_COOKIE)
        if raw and "|" in str(raw):
            u, t = str(raw).split("|", 1)
            return u.strip(), t.strip()
    except Exception:
        pass
    return None, None


def save(usuario: str, token: str):
    m = _mgr()
    if m is None:
        return
    try:
        m.set(_COOKIE, f"{usuario}|{token}",
              expires_at=datetime.now() + timedelta(days=_DIAS), key="copex_cookie_set")
    except Exception:
        pass


def clear():
    m = _mgr()
    if m is None:
        return
    try:
        m.delete(_COOKIE, key="copex_cookie_del")
    except Exception:
        pass
