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
import json
import streamlit as st

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
    """Escribe la cookie como PERSISTENTE (`max-age`) directamente en el documento de la
    app vía `window.parent.document.cookie`, NO con el `set` de extra-streamlit-components.

    v222 — motivo: el `set` de la librería dejaba la cookie como **de sesión** (sin
    expiración efectiva) → sobrevivía al refresco pero moría al **cerrar/reabrir** el
    navegador o la PWA instalada, y había que volver a loguear. `max-age` es inequívoco.
    La cookie va sobre el MISMO origen que lee `load()` (el componente de la librería se
    sirve desde el host de la app), así que la lectura la sigue viendo.

    ⚠️ Debe llamarse en un run que TERMINA (p.ej. `render_user_bar`), NUNCA justo antes de
    un `st.rerun()`: el rerun descarta los componentes del run en curso y no se escribiría.
    Es idempotente y 'rolling' (refresca los 7 días en cada visita)."""
    if not usuario or not token:
        return
    try:
        import streamlit.components.v1 as components
        secs = _DIAS * 24 * 3600
        cookie_str = f"{_COOKIE}={usuario}|{token}; max-age={secs}; path=/; SameSite=Lax"
        components.html(
            "<script>try{window.parent.document.cookie="
            + json.dumps(cookie_str) + ";}catch(e){}</script>",
            height=0, width=0)
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
