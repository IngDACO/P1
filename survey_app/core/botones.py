"""Los botones PARTEN su texto en líneas en vez de recortarlo con «…» (v549, trampa nº33).

Streamlit 1.64 añadió `wrap` a los botones, y su valor por defecto (`None`, «decide
Streamlit») RECORTA en una sola línea la etiqueta de un botón colocado en una columna: en el
Home se leía «AC…» por «Active 3», «No contact det…», «installer leader CI · 88 wa…»; en
Fichaje, «Open workda…» y «Leave …». Fuera de columnas ya partía líneas. Había ~123 botones
en columnas (decisión del usuario: barrido de una vez).

→ En vez de tocar los ~123 sitios (y que se escapen los que nacen en bucles o los futuros),
el DEFECTO de la app pasa a `wrap=True`: el texto nunca se recorta. Quien quiera una sola línea
a propósito lo dice con `wrap=False` en su llamada (`setdefault`: lo explícito manda).

⚠️ `st.button` y compañía son métodos LIGADOS al DeltaGenerator principal en el momento de
importar streamlit (`button = _main.button` en su `__init__`): cambiar la clase no los
alcanza, así que se vuelven a ligar. Las columnas, la barra lateral y los formularios buscan
el método en la clase en cada llamada, y esos sí lo ven al cambiarla.
⚠️ Si una versión futura de Streamlit quita `wrap`, no se toca nada (se mira la firma).

## v562 · El clic que sobrevive a una pasada CORTADA

Un componente que se monta y envía su valor (el mapa del Home, la firma del Pre-Start, el
gestor de cookies al abrir la página) pide una pasada nueva. Si llega mientras corre la
pasada de un clic, Streamlit 1.64 la CORTA en el siguiente punto de control, y la pasada
nueva ya no lleva el clic: solo funde los disparadores si las dos peticiones están EN COLA,
no si una ya corre. Reproducido en una mini-app: con componente se perdieron 8 de 8 clics
(el primer «Not now» del Pre-Start, el primer «Generate the read», la primera pregunta del
chat: «al repetir, bien»).

→ Un botón con clave (y una entrega de formulario, y el `chat_input` con clave) recibe un
`on_click` que solo ANOTA el clic. Los callbacks corren ANTES del cuerpo de la pasada, así que
la nota queda aunque la pasada se corte. Al pintarse el botón: Streamlit dice True → se borra
la nota y True; dice False pero hay nota → se borra y True, UNA vez. La nota muere al final de
la primera pasada COMPLETA que no pinta ese botón (`fin_de_pasada`, al final de app.py) y, en
todo caso, a los `VIGENCIA_S` segundos: un clic nunca dispara un botón más tarde, en otra
pantalla. En la mini-app: 10 de 10 clics, ninguno doble.
⚠️ No se toca un botón con `on_click` propio (ya corre antes del cuerpo), ni uno sin clave
(no hay con qué reconocerlo), ni uno con la clave pasada por posición.
"""
import functools
import inspect
import time

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

METODOS = ("button", "download_button", "form_submit_button", "link_button")
_MARCA = "_copex_wrap_por_defecto"
_MARCA_CHAT = "_copex_chat_pegajoso"
_PEGAJOSOS = ("button", "form_submit_button")   # los que disparan una acción con su True
_PEND = "_clic_pendiente"
VIGENCIA_S = 15.0


def _acepta_wrap(fn) -> bool:
    try:
        return "wrap" in inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return False


def _pendientes() -> dict:
    p = st.session_state.get(_PEND)
    if not isinstance(p, dict):
        p = {}
        st.session_state[_PEND] = p
    return p


def _hora(v) -> float:
    return v[0] if isinstance(v, tuple) else float(v)


def _purgar(p: dict) -> None:
    ahora = time.monotonic()
    for _k in [k for k, v in p.items() if ahora - _hora(v) > VIGENCIA_S]:
        p.pop(_k, None)


def _id_clic(self, nom, args, kwargs):
    """Con qué se reconoce el clic de este botón, o None si no se puede (no se toca)."""
    if kwargs.get("on_click") is not None or len(args) > 1:
        return None
    key = kwargs.get("key")
    if key is not None:
        return f"{nom}:{key}"
    if nom == "form_submit_button":
        # Las 28 entregas de la app van sin clave: su formulario + su etiqueta.
        try:
            from streamlit.elements.lib.form_utils import current_form_id
            fid = current_form_id(self)
        except Exception:
            fid = ""
        etq = args[0] if args else kwargs.get("label")
        if fid and etq is not None:
            return f"{nom}:{fid}:{etq}"
    return None


def _envolver(orig, nom):
    pegajoso = nom in _PEGAJOSOS

    @functools.wraps(orig)
    def _con_wrap(self, *args, **kwargs):
        kwargs.setdefault("wrap", True)
        k = _id_clic(self, nom, args, kwargs) if pegajoso else None
        if k is None:
            return orig(self, *args, **kwargs)

        def _anota():
            _pendientes()[k] = time.monotonic()

        kwargs["on_click"] = _anota
        r = orig(self, *args, **kwargs)
        p = _pendientes()
        _purgar(p)
        nota = p.pop(k, None)
        if kwargs.get("disabled"):
            return bool(r)                        # deshabilitado: la nota no lo dispara
        return bool(r) or nota is not None
    setattr(_con_wrap, _MARCA, True)
    return _con_wrap


def _envolver_chat(orig):
    @functools.wraps(orig)
    def _chat(self, *args, **kwargs):
        key = kwargs.get("key")
        if key is None or kwargs.get("on_submit") is not None or len(args) > 1:
            return orig(self, *args, **kwargs)
        k = f"chat_input:{key}"

        def _anota():
            v = st.session_state.get(key)
            if v:
                _pendientes()[k] = (time.monotonic(), v)

        kwargs["on_submit"] = _anota
        r = orig(self, *args, **kwargs)
        p = _pendientes()
        _purgar(p)
        nota = p.pop(k, None)
        if r:
            return r
        return nota[1] if isinstance(nota, tuple) else r
    setattr(_chat, _MARCA_CHAT, True)
    return _chat


def fin_de_pasada() -> None:
    """Al final de una pasada COMPLETA (app.py): las notas que quedan son de botones que esta
    pasada no pintó → no deben dispararse en otra pantalla más tarde."""
    try:
        p = st.session_state.get(_PEND)
        if isinstance(p, dict) and p:
            p.clear()
    except Exception:
        pass


def instalar() -> list:
    """Pone `wrap=True` por defecto y el clic que sobrevive (v562). Idempotente. Devuelve
    los tipos que quedaron cubiertos."""
    hechos = []
    for nom in METODOS:
        orig = getattr(DeltaGenerator, nom, None)
        if orig is None:
            continue
        if not getattr(orig, _MARCA, False):
            if not _acepta_wrap(orig):
                continue                          # otra versión de Streamlit: no se toca
            setattr(DeltaGenerator, nom, _envolver(orig, nom))
        # el alias del módulo (`st.button`) se vuelve a ligar al principal
        _alias = getattr(st, nom, None)
        _principal = getattr(_alias, "__self__", None)
        if isinstance(_principal, DeltaGenerator):
            setattr(st, nom, getattr(_principal, nom))
        hechos.append(nom)
    _oc = getattr(DeltaGenerator, "chat_input", None)
    if _oc is not None:
        if not getattr(_oc, _MARCA_CHAT, False):
            setattr(DeltaGenerator, "chat_input", _envolver_chat(_oc))
        _p = getattr(getattr(st, "chat_input", None), "__self__", None)
        if isinstance(_p, DeltaGenerator):
            st.chat_input = getattr(_p, "chat_input")
        hechos.append("chat_input")
    return hechos
