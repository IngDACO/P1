# -*- coding: utf-8 -*-
"""HTML incrustado en un recuadro (iframe): dibujos, cronómetros y scripts de página (v532).

## Por qué existe

Hasta v531 la app llamaba 22 veces a `st.components.v1.html`, que Streamlit anuncia que
quitará («will be removed after 2026-06-01», visto en los logs del Cloud). La sustituta es
`st.iframe`. En Streamlit 1.64 las dos generan el MISMO elemento —un iframe con el HTML en
`srcdoc`, el mismo sandbox, el mismo acceso a la página—, pero `st.iframe` cambia dos cosas
que aquí importan, y este módulo las neutraliza en UN solo sitio:

1. **Siempre permite scroll** (`scrolling="auto"`). Antes, los dibujos iban con
   `scrolling=False`: si algo se salía de su caja se recortaba sin barra. Con `st.iframe`
   aparecería una barra de scroll donde antes no había ninguna (el cronómetro del sidebar,
   por ejemplo, se sale unos píxeles por los márgenes del documento). `dibujo()` inyecta
   `overflow:hidden` en el documento, así que se ve EXACTAMENTE como antes.
2. **No admite altura 0**, y los scripts invisibles (cookie de sesión, botón «atrás», la
   cabecera de la PWA) iban a altura 0. `script()` usa 1 px transparente: con «content» el
   recuadro vale 150 px hasta la primera medida, un salto al cargar.

⚠️ Los scripts siguen tocando `window.parent` (la página de la app que contiene su
recuadro), igual que antes. NO se pasan a `st.html`, que no usa recuadro: ahí
`window.parent` sería la página que envuelve el Cloud y escribirían en el documento
equivocado.

Módulo HOJA: solo importa `streamlit`.
"""
import streamlit as st

_SIN_SCROLL = "<style>html,body{overflow:hidden}</style>"


def dibujo(html, alto, scroll=False, ajustar=None):
    """Un dibujo (SVG/HTML) en su recuadro.

    Sin `scroll`, lo que se salga de la caja se recorta sin barra (el comportamiento de
    `scrolling=False`); con `scroll=True`, barra solo si hace falta.

    ⚠️ v535 · `ajustar` (por defecto, sin `scroll`): el recuadro MIDE lo que mide el dibujo
    (`height="content"` de `st.iframe`). Con alto fijo, en una pantalla estrecha el SVG
    encogía con el ancho y debajo quedaba un hueco en blanco —medido en producción: 379 px
    de cronograma en un recuadro de 648, 256 de isométrica en 650—. Streamlit le añade al
    documento un script que mide el cuerpo y avisa a la página (al cargar, al cambiar el
    DOM y al cambiar de ancho), así que el dibujo de un desplegable cerrado se mide al
    abrirlo. `alto` solo cuenta con `ajustar=False`: los cronómetros (alto exacto del menú
    y de la columna, v534) y las plantas apiladas con `scroll` (hasta 8000 px).
    """
    if ajustar is None:
        ajustar = not scroll
    h = str(html or "")
    if not scroll:
        # ⚠️ El estilo va DENTRO del <body> si lo hay: delante de un `<!DOCTYPE>` lo
        # anularía y el documento pasaría a modo quirks. Un fragmento sin <body> ya se
        # pintaba sin doctype, así que ahí puede ir delante.
        _i = h.lower().find("<body")
        if _i >= 0:
            _j = h.find(">", _i)
            h = h[:_j + 1] + _SIN_SCROLL + h[_j + 1:] if _j >= 0 else _SIN_SCROLL + h
        else:
            h = _SIN_SCROLL + h
    return st.iframe(h, height="content" if ajustar else max(1, int(alto)))


def script(js):
    """Un `<script>` invisible que actúa sobre la página de la app (`window.parent`).

    1 px transparente y sin márgenes: `st.iframe` no admite altura 0.
    """
    return st.iframe('<html><body style="margin:0">' + str(js or "") + "</body></html>",
                     height=1)
