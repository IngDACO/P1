# -*- coding: utf-8 -*-
"""Las tarjetas del Field assistant (v640): lo que ha preparado y espera un toque de la persona.

Nivel 2 de autonomía, decisión del usuario: el asistente deja lista la acción (el parte, el aviso a la
oficina, la ausencia), y solo pasa cuando la persona pulsa **Confirm**. Lo que prepara vive en la
SESIÓN, no en la hoja: si se cierra la sesión, no ha pasado nada.

v641 · Y lo que le da continuidad: la conversación se recuerda (`chat_memoria`) y se le puede mandar una
foto, que se reduce antes de enviarla y no se guarda en ningún sitio.
"""
import base64
import io
import logging

import streamlit as st

from core import chat_memoria as CM
from core import chat_tools as CT
from core.i18n import t
from core.maps import literal_md

logger = logging.getLogger(__name__)

_LISTA = "_chat_acciones"
_PET = "_chat_pet"
_RECORDADA = "_chat_recordada"
MAX_LADO = 1568           # el lado que la API usa sin reescalar: más grande solo cuesta más subirla
MAX_FOTO_MB = 15
TIPOS_FOTO = ["jpg", "jpeg", "png", "webp"]


def _es_campo() -> bool:
    return str((st.session_state.get("auth") or {}).get("rol", "")) == "field"


def recordar() -> None:
    """Trae la conversación guardada, UNA vez por sesión. Por ahora solo del campo: la oficina es el
    siguiente agente del recorrido. ⚠️ No pisa una conversación que ya esté en marcha."""
    if st.session_state.get(_RECORDADA) or not _es_campo():
        return
    st.session_state[_RECORDADA] = True
    if not st.session_state.get("chat_history"):
        a = _contexto()
        st.session_state["chat_history"] = CM.cargar(a["usuario"], a["grupo"])


def memorizar() -> None:
    """Guarda la conversación tal como está. Solo del campo."""
    if _es_campo():
        a = _contexto()
        CM.guardar(a["usuario"], a["grupo"], st.session_state.get("chat_history") or [])


def opciones_foto(rol) -> dict:
    """Lo que `st.chat_input` necesita para aceptar una foto, solo en el campo."""
    if rol != "field":
        return {}
    return {"accept_file": True, "file_type": TIPOS_FOTO, "max_upload_size": MAX_FOTO_MB}


def foto_para_api(archivo) -> str:
    """La foto en JPEG y reducida, en base64. ⚠️ Girada según su EXIF: el móvil guarda la orientación
    aparte, y sin esto el asistente la leería de lado."""
    from PIL import Image, ImageOps
    with Image.open(archivo) as im:
        _im = ImageOps.exif_transpose(im).convert("RGB")
    _im.thumbnail((MAX_LADO, MAX_LADO))
    b = io.BytesIO()
    _im.save(b, "JPEG", quality=85)
    return base64.b64encode(b.getvalue()).decode("ascii")


def leer_entrada(valor) -> tuple:
    """`(texto, fotos)` de lo que devuelve `st.chat_input`: texto a secas, o con archivos si los acepta."""
    if isinstance(valor, str):
        return valor, []
    txt = str(getattr(valor, "text", "") or "").strip()
    fotos = []
    for a in list(getattr(valor, "files", None) or [])[:1]:
        try:
            fotos.append(foto_para_api(a))
        except Exception as e:
            logger.warning("chat_ui: foto ilegible: %s", e)
            st.warning(t("That photo could not be read. Try another one."))
    return (txt or (t("What can you tell me from this photo?") if fotos else "")), fotos


def pendientes() -> list:
    """Las tarjetas que esperan. ⚠️ La MISMA lista en toda la sesión: el asistente añade a esta."""
    return st.session_state.setdefault(_LISTA, [])


def olvidar() -> None:
    """Al limpiar la conversación se van también: una tarjeta sin su contexto no se entiende. v641 · Y
    la memoria: limpiar tiene que dejarla limpia, no solo la pantalla."""
    st.session_state[_LISTA] = []
    st.session_state.pop(_PET, None)
    if _es_campo():
        a = _contexto()
        CM.borrar(a["usuario"], a["grupo"])


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
        memorizar()
        return
    with st.spinner(t("Saving…")):
        ok, msg = CT.confirmar(a, _contexto())
    if not ok:
        lista.append(a)
    _hist.append({"role": "assistant", "content": ("✅ " if ok else "⚠️ ") + str(msg)})
    memorizar()


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
