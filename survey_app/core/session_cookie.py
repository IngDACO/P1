"""
Login persistente con cookie: la sesión sobrevive al refresco del navegador.

Guarda `usuario|token` (el mismo token de la sesión única) en una cookie del
navegador. Al abrir la app se valida contra la hoja Login: si el token sigue
siendo el de la sesión viva, se restaura la sesión sin volver a escribir la clave.

Usa `extra-streamlit-components` con **import perezoso**: si la librería no está
disponible, la app funciona igual, solo que sin persistencia (comportamiento previo).

v188 — el CookieManager se crea UNA sola vez por sesión y se guarda en
`session_state`. Antes se instanciaba en cada llamada/rerun; combinado con los
`sleep`+rerun forzados del login, el componente nunca llegaba a entregar la cookie
tras un refresco (ver core/auth_ui.render_login). Ahora `load()` solo renderiza el
componente y devuelve lo que haya; el propio componente dispara el rerun cuando el
navegador entrega la cookie.
"""
import streamlit as st
from datetime import datetime, timedelta

_COOKIE  = "copex_session"
_DIAS    = 7
_MGR_KEY = "_cookie_mgr"


def _manager():
    """CookieManager ÚNICO por sesión (o None si la librería no está disponible).
    Guardarlo en session_state evita re-montar el componente en cada rerun, que era
    lo que impedía que el navegador entregara la cookie tras un refresco (v188)."""
    if _MGR_KEY not in st.session_state:
        try:
            import extra_streamlit_components as stx
            st.session_state[_MGR_KEY] = stx.CookieManager(key="copex_cookie_mgr")
        except Exception:
            st.session_state[_MGR_KEY] = None
    return st.session_state[_MGR_KEY]


def available() -> bool:
    """True si hay persistencia por cookie (librería presente)."""
    return _manager() is not None


def load() -> tuple:
    """(usuario, token) de la cookie, o (None, None).

    Renderiza el componente (necesario para que el navegador entregue las cookies).
    Devuelve (None, None) hasta que llegan; el componente dispara un rerun cuando
    ya las tiene, así que basta con llamarlo en cada run mientras no haya sesión."""
    m = _manager()
    if m is None:
        return None, None
    try:
        cookies = m.get_all(key="copex_cookie_get") or {}
        raw = cookies.get(_COOKIE)
        if raw and "|" in str(raw):
            u, t = str(raw).split("|", 1)
            return u.strip(), t.strip()
    except Exception:
        pass
    return None, None


def save(usuario: str, token: str):
    m = _manager()
    if m is None:
        return
    try:
        m.set(_COOKIE, f"{usuario}|{token}",
              expires_at=datetime.now() + timedelta(days=_DIAS), key="copex_cookie_set")
    except Exception:
        pass


def clear():
    m = _manager()
    if m is None:
        return
    try:
        m.delete(_COOKIE, key="copex_cookie_del")
    except Exception:
        pass
