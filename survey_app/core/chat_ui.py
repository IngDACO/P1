# -*- coding: utf-8 -*-
"""Las tarjetas del Field assistant (v640): lo que ha preparado y espera un toque de la persona.

Nivel 2 de autonomía, decisión del usuario: el asistente deja lista la acción (el parte, el aviso a la
oficina, la ausencia), y solo pasa cuando la persona pulsa **Confirm**. Lo que prepara vive en la
SESIÓN, no en la hoja: si se cierra la sesión, no ha pasado nada.
"""
import streamlit as st

from core import chat_tools as CT
from core.i18n import t
from core.maps import literal_md

_LISTA = "_chat_acciones"
_PET = "_chat_pet"


def pendientes() -> list:
    """Las tarjetas que esperan. ⚠️ La MISMA lista en toda la sesión: el asistente añade a esta."""
    return st.session_state.setdefault(_LISTA, [])


def olvidar() -> None:
    """Al limpiar la conversación se van también: una tarjeta sin su contexto no se entiende."""
    st.session_state[_LISTA] = []
    st.session_state.pop(_PET, None)


def _pedir(aid, si) -> None:
    st.session_state[_PET] = {"id": aid, "si": si}


def _contexto() -> dict:
    """⚠️ De la sesión, como al preparar: quién confirma es quien está aquí, no lo que diga la tarjeta."""
    a = st.session_state.get("auth", {}) or {}
    return {"usuario": a.get("usuario", ""), "nombre": a.get("nombre") or a.get("usuario", ""),
            "grupo": a.get("grupo", ""), "rol": a.get("rol", "")}


def atender() -> None:
    """Lo pedido, ANTES de pintar (trampa 37). ⚠️ La tarjeta sale de la lista antes de ejecutar: un
    doble toque no la encuentra y no manda dos veces a la oficina. Si falla vuelve, para reintentar:
    quien dictó un parte en la obra no lo repite."""
    pet = st.session_state.pop(_PET, None)
    if not pet:
        return
    lista = pendientes()
    a = next((x for x in lista if x.get("id") == pet.get("id")), None)
    if a is None:
        return
    lista.remove(a)
    _hist = st.session_state.setdefault("chat_history", [])
    if not pet.get("si"):
        _hist.append({"role": "assistant", "content": t("Cancelled: {x}. Nothing was sent.", x=literal_md(a["titulo"]))})
        return
    with st.spinner(t("Saving…")):
        ok, msg = CT.confirmar(a, _contexto())
    if not ok:
        lista.append(a)
    _hist.append({"role": "assistant", "content": ("✅ " if ok else "⚠️ ") + str(msg)})


def tarjetas() -> None:
    for a in pendientes():
        with st.container(border=True):
            st.markdown(f"**{literal_md(a['titulo'])}**")
            st.markdown(literal_md(a["detalle"]).replace("\n", "  \n"))
            st.caption(t("Nothing happens until you confirm."))
            c1, c2 = st.columns(2)
            c1.button(t(":material/check: Confirm"), key=f"chat_ok_{a['id']}", type="primary", width="stretch",
                      on_click=_pedir, args=(a["id"], True))
            c2.button(t("Cancel"), key=f"chat_no_{a['id']}", width="stretch",
                      on_click=_pedir, args=(a["id"], False))
