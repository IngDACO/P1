# -*- coding: utf-8 -*-
"""Las tarjetas del Field assistant (v640): lo que ha preparado y espera un toque de la persona.

Nivel 2 de autonomía, decisión del usuario: el asistente deja lista la acción (el parte, el aviso a la
oficina, la ausencia), y solo pasa cuando la persona pulsa **Confirm**. Lo que prepara vive en la
SESIÓN, no en la hoja: si se cierra la sesión, no ha pasado nada.

v641 · Y lo que le da continuidad: la conversación se recuerda (`chat_memoria`) y se le puede mandar una
foto, que se reduce antes de enviarla y no se guarda en ningún sitio.

v644 · La oficina también: sus tarjetas (las cinco de `chat_tools.PREPARAR_OFICINA`) y su memoria,
cada uno la suya. La foto, todavía solo el campo; el propietario, ni memoria: va con su recorrido.
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


_CON_MEMORIA = ("field", "administrator")       # v644 · el propietario, con su recorrido


def _recuerda() -> bool:
    return str((st.session_state.get("auth") or {}).get("rol", "")) in _CON_MEMORIA


def recordar() -> None:
    """Trae la conversación guardada, UNA vez por sesión: del campo y, desde v644, de la oficina; cada
    uno la suya. ⚠️ No pisa una conversación que ya esté en marcha."""
    if st.session_state.get(_RECORDADA) or not _recuerda():
        return
    st.session_state[_RECORDADA] = True
    if not st.session_state.get("chat_history"):
        a = _contexto()
        st.session_state["chat_history"] = CM.cargar(a["usuario"], a["grupo"])


def memorizar() -> None:
    """Guarda la conversación tal como está."""
    if _recuerda():
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
    from PIL import ImageOps
    from core import imagenes             # v655 · solo JPEG, PNG y WEBP
    with imagenes.abrir(archivo) as im:
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
    if _recuerda():
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
        # v645 · `app`: lo escribe la APP, no el asistente; así le llega al modelo (`chat_agent._para_el_modelo`)
        _hist.append({"role": "assistant", "content": t("Cancelled: {x}. Nothing was sent.", x=literal_md(a["titulo"])),
                      "app": "cancel", "card": a["titulo"]})
        memorizar()
        return
    with st.spinner(t("Saving…")):
        # v646 · con la lista: confirmar un parte puede dejar la tarjeta para acreditar lo que dice
        ok, msg = CT.confirmar(a, {**_contexto(), "acciones": lista})
    if not ok:
        lista.append(a)
    _hist.append({"role": "assistant", "content": ("✅ " if ok else "⚠️ ") + str(msg), "app": "confirm", "card": a["titulo"]})
    memorizar()


def tarjetas() -> None:
    for a in pendientes():
        with st.container(border=True):
            st.markdown(f"**{literal_md(a['titulo'])}**")
            st.markdown(literal_md(a["detalle"]).replace("\n", "  \n"))
            st.caption(t("Nothing happens until you confirm."))
            c1, c2 = st.columns(2)
            # Sin icono: a 300 px de menú lateral, cada botón mide 89 y el icono echa el texto a otra línea
            c1.button(t("Confirm"), key=f"chat_ok_{a['id']}", type="primary", width="stretch",
                      on_click=_pedir, args=(a["id"], True))
            c2.button(t("Cancel"), key=f"chat_no_{a['id']}", width="stretch",
                      on_click=_pedir, args=(a["id"], False))


# ─────────────────────────────────────────────────────────────────────────────
# v707 · La burbuja: el asistente en su propio panel, fuera del menú lateral
# ─────────────────────────────────────────────────────────────────────────────
# Decisión del usuario (24/11, al repasar el marco de la app): «cuando se tiene un chat largo con el agente se sube
# demasiado el menú» — con DOS mensajes el desplegable del menú lateral medía 2014 px y el menú lateral pasaba de 1184
# a 3159. Ahora una burbuja flotante abre la conversación en un panel a la derecha, a toda la altura (`st.dialog` con
# `position="right"`). Es un fragmento: escribir solo vuelve a pintar el panel, no la página.
_ABIERTO = "_chat_abierto"          # ⚠️ no `_chat_open`: las claves `_…_open…` cuentan como cambio de vista (v603)


def _abrir_chat() -> None:
    st.session_state[_ABIERTO] = True


def _cerrar_chat() -> None:
    st.session_state[_ABIERTO] = False


def titulo_asistente(rol) -> str:
    return "Field assistant" if rol == "field" else "Management assistant"


def burbuja(rol, grupo) -> None:
    """La burbuja (abajo a la derecha, encima de la insignia de Streamlit Cloud; el estilo, en `theme`) y, si está
    abierto, el panel. ⚠️ Se vuelve a abrir en CADA pasada mientras `_chat_abierto`: así una pasada entera (la de otro
    botón de la página) no lo cierra; lo cierra la X, Esc o un clic fuera (`on_dismiss`)."""
    st.button(":material/smart_toy:", key="cpx_chat_burbuja", type="primary", on_click=_abrir_chat,
              help=t(titulo_asistente(rol)))
    if st.session_state.get(_ABIERTO):
        st.dialog(f"{titulo_asistente(rol)} COPEX", width="small", position="right", icon=":material/smart_toy:",
                  on_dismiss=_cerrar_chat)(conversacion)(rol, grupo)


def _rerun_panel() -> None:
    """Vuelve a pintar SOLO el panel (es un fragmento); si se está pintando dentro de una pasada entera, la página."""
    try:
        st.rerun(scope="fragment")
    except st.errors.StreamlitAPIException:
        st.rerun()


def conversacion(rol, grupo) -> None:
    """La conversación con el asistente (hasta v706, en el desplegable del menú lateral de `app.py`, igual)."""
    from core.chat_agent import get_chat_response
    ctx_label = ":material/link: With the current calculation as context." if st.session_state.get("calc_results") else "No active calculation."
    _foco = ("Focused on installing on site and using the app in the field."
             if rol == "field"
             else "Focused on project management and interpreting results.")
    st.caption(f"{_foco} {ctx_label}")
    if rol == "field":
        st.caption(t("Your conversation is kept for 14 days. You can attach a photo."))
    elif rol == "administrator":
        st.caption(t("Your conversation is kept for 14 days."))   # v644 · la foto, todavía solo el campo

    # v640 · Lo confirmado o cancelado, ANTES de pintar el historial (trampa 37)
    recordar()                       # v641 · la conversación guardada, una vez por sesión
    atender()

    # Historial — v707 · en su caja, con su scroll, que baja sola (`autoscroll`): lo de esta pasada se pinta DENTRO
    # (antes salía debajo del cuadro de escribir) y el cuadro queda siempre abajo, a la vista. El alto, en `theme`.
    _caja = st.container(height=440, autoscroll=True, border=False, key="cpx_chat_hist")
    with _caja:
        for msg in st.session_state.setdefault("chat_history", []):
            with st.chat_message(msg["role"],
                                 avatar="🧑‍🔧" if msg["role"] == "user" else "🤖"):
                st.markdown(msg["content"])
        tarjetas()

    # Input
    # v526 · Estaba en español y sin `t()` (visto en producción): el idioma base es el
    # inglés, y ningún barrido de i18n miraba `st.chat_input` (trampa nº30).
    _entrada = st.chat_input(t("Ask your question…"), key="sidebar_chat_input", **opciones_foto(rol))
    prompt, _fotos = leer_entrada(_entrada) if _entrada else ("", [])
    if prompt:
        _tarjetas_antes = len(pendientes())
        # v641 · En el historial, la marca de la foto: la imagen va solo en esta pregunta
        _dicho = f"📷 {prompt}" if _fotos else prompt
        st.session_state.chat_history.append({"role": "user", "content": _dicho})
        with _caja, st.chat_message("user", avatar="🧑‍🔧"):
            st.markdown(_dicho)
        with _caja, st.chat_message("assistant", avatar="🤖"):
            with st.spinner(t("Searching…")):
                _r = st.session_state.get("calc_results")
                _response = get_chat_response(
                    user_message = prompt,
                    history      = st.session_state.chat_history[:-1],
                    calc_results = _r,
                    all_params   = _r["all_params"] if _r else None,
                    rol          = rol,
                    grupo        = grupo,
                    # v639 · De la sesión: es quien decide de quién son los datos que mira
                    usuario      = st.session_state.get("auth", {}).get("usuario", ""),
                    nombre       = st.session_state.get("auth", {}).get("nombre", ""),
                    acciones     = pendientes(),
                    fotos        = _fotos,
                )
            st.markdown(_response)
        st.session_state.chat_history.append({"role": "assistant", "content": _response})
        memorizar()                  # después de responder: lo que tarde no se hace esperar
        if len(pendientes()) > _tarjetas_antes:
            _rerun_panel()               # la tarjeta nueva va debajo de lo que acaba de decir (v707: solo el panel)

    # Limpiar
    if st.session_state.chat_history:
        if st.button(t(":material/delete: Clear the conversation"), width="stretch", key="clear_chat_sb"):
            st.session_state.chat_history = []
            olvidar()
            _rerun_panel()
