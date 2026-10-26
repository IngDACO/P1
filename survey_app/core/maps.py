"""
Enlaces a Google Maps para las ubicaciones de la app.

Usa la URL de BÚSQUEDA de Maps (no requiere API key ni coordenadas): abre
cualquier texto de dirección/lugar. Helpers para markdown (Streamlit), HTML
(cabeceras con unsafe_allow_html, emails/Telegram) y la URL cruda (PDF).
"""
import html
import re
import urllib.parse

_BASE = "https://www.google.com/maps/search/?api=1&query="
# v603 · lo que el markdown INTERPRETA dentro de la etiqueta de un enlace (cursivas, LaTeX,
# corchetes, HTML…). Escapado con «\» se lee tal cual: CommonMark admite escapar cualquier
# signo de puntuación ASCII, así que escapar de más no estropea nada.
_MD_ESPECIAL = re.compile(r"([\\`*_{}\[\]()<>#+!|~$-])")


def literal_md(texto) -> str:
    """v603 · El texto tal cual dentro de markdown (la etiqueta de un enlace).

    ⚠️ Medido en Streamlit 1.64 (mini-app de v602): «12 Smith St *gate 2*» salía «gate 2» en
    cursiva, sin los asteriscos."""
    return _MD_ESPECIAL.sub(r"\\\1", str(texto or ""))


def enlace_md(texto, url) -> str:
    """v603 · `[texto](url)` con el texto escapado y la URL sin nada que corte el enlace.

    ⚠️ Un email como enlace va SIEMPRE por aquí, nunca dentro de un `<a>` HTML: el markdown
    de Streamlit 1.64 vuelve a enlazar el email que es el TEXTO del `<a>`, y un enlace no cabe
    dentro de otro — el navegador deja uno VACÍO delante (medido en producción, la ficha del
    cliente). Y nunca el email suelto: el autoenlace se equivoca con «zz_prueba+obra*1@…»
    (enlaza solo «1@…»)."""
    _u = urllib.parse.quote(str(url or ""), safe=":/@+._-~!*',;=?&%#")
    return f"[{literal_md(texto)}]({_u})"


def maps_url(location) -> str:
    """URL de Google Maps para el texto de ubicación, o '' si está vacío."""
    loc = str(location or "").strip()
    if not loc:
        return ""
    return _BASE + urllib.parse.quote(loc)


def maps_link_md(location, label=None) -> str:
    """Markdown '[label](url)' para st.markdown/st.caption; '' si vacío.

    ⚠️ v589 · SIN el «📍» delante: tres sitios le ponían además `:material/place:` y salían
    dos iconos juntos (Survey, Home, la obra del campo). El icono lo pone quien lo pinta,
    el de Material como el resto de la app."""
    url = maps_url(location)
    if not url:
        return ""
    lbl = str(label if label is not None else location).strip()
    return f"[{literal_md(lbl)}]({url})"           # v603 · la dirección, TAL CUAL


def maps_link_html(location, label=None, color="#2e6da4") -> str:
    """Ancla HTML para cabeceras (unsafe_allow_html), email y Telegram; '' si vacío."""
    url = maps_url(location)
    if not url:
        return ""
    # ⚠️ v603 · escapada: «Shop 3 <Ground> & 4» salía «Shop 3 & 4» (el navegador se tragaba
    # «<Ground>» como una etiqueta HTML; medido en una mini-app)
    lbl = html.escape(str(label if label is not None else location).strip())
    return (f'<a href="{url}" target="_blank" '
            f'style="color:{color};text-decoration:none;">📍 {lbl}</a>')
