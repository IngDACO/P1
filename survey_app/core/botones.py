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
"""
import functools
import inspect

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

METODOS = ("button", "download_button", "form_submit_button", "link_button")
_MARCA = "_copex_wrap_por_defecto"


def _acepta_wrap(fn) -> bool:
    try:
        return "wrap" in inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return False


def _envolver(orig):
    @functools.wraps(orig)
    def _con_wrap(self, *args, **kwargs):
        kwargs.setdefault("wrap", True)
        return orig(self, *args, **kwargs)
    setattr(_con_wrap, _MARCA, True)
    return _con_wrap


def instalar() -> list:
    """Pone `wrap=True` por defecto. Idempotente. Devuelve los tipos que quedaron cubiertos."""
    hechos = []
    for nom in METODOS:
        orig = getattr(DeltaGenerator, nom, None)
        if orig is None:
            continue
        if not getattr(orig, _MARCA, False):
            if not _acepta_wrap(orig):
                continue                          # otra versión de Streamlit: no se toca
            setattr(DeltaGenerator, nom, _envolver(orig))
        # el alias del módulo (`st.button`) se vuelve a ligar al principal
        _alias = getattr(st, nom, None)
        _principal = getattr(_alias, "__self__", None)
        if isinstance(_principal, DeltaGenerator):
            setattr(st, nom, getattr(_principal, nom))
        hechos.append(nom)
    return hechos
