"""
Plano de la sesión — un solo PDF para todas las herramientas.

Hasta v127 cada herramienta pedía su PROPIO plano: Survey, Plomadas, Corte de
rieles, Corte de buffers y Belting tenían cinco `file_uploader` distintos, así
que el técnico subía el mismo archivo hasta cinco veces para el mismo elevador.
Y `extractors/schindler.py` ya tenía todos los extractores juntos, o sea que un
único PDF puede alimentarlas todas.

El Survey guarda el plano al cargarlo (`guardar`) y las demás lo ofrecen con
`selector()`, que devuelve un objeto tipo fichero **con atributo `.name`**:
los llamadores lo usan como guarda de identidad (`pdf.name != ..._pdf_name`),
el patrón obligatorio para uploaders con efectos (v112).
"""
import io

import streamlit as st

from core.i18n import t

_K_NOM = "_plano_nombre"
_K_BYT = "_plano_bytes"


def guardar(nombre, datos) -> None:
    """Registra el plano de la sesión. Silencioso si falta algo."""
    if not nombre or not datos:
        return
    st.session_state[_K_NOM] = str(nombre)
    st.session_state[_K_BYT] = datos


def actual() -> tuple:
    """(nombre, bytes) del plano de la sesión, o (None, None)."""
    return st.session_state.get(_K_NOM), st.session_state.get(_K_BYT)


def limpiar() -> None:
    for k in (_K_NOM, _K_BYT):
        st.session_state.pop(k, None)


class _Plano(io.BytesIO):
    """BytesIO con `.name`, para que sustituya a un UploadedFile sin tocar
    la lógica de los llamadores."""

    def __init__(self, datos, nombre):
        super().__init__(datos)
        self.name = nombre


def selector(label: str, key: str, ayuda: str = "") -> object:
    """Ofrece el plano de la sesión o pide uno nuevo. Devuelve fichero o None.

    Todo lo que se sube por aquí queda registrado como plano de la sesión, así
    que da igual en qué herramienta empieces: las demás lo heredan.
    """
    nom, byt = actual()
    if nom and byt:
        opc = [f"{t('Use the loaded drawing')} · {nom}", t("Load another drawing")]
        elec = st.radio(label, opc, key=f"{key}_src", horizontal=True,
                        label_visibility="visible", help=ayuda or None)
        if elec == opc[0]:
            return _Plano(byt, nom)

    up = st.file_uploader(label if not (nom and byt) else t("New drawing (PDF)"),
                          type=["pdf"], key=key, help=ayuda or None)
    if up is not None:
        try:
            guardar(up.name, up.getvalue())
            up.seek(0)
        except Exception:
            pass
    return up
