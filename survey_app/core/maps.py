"""
Enlaces a Google Maps para las ubicaciones de la app.

Usa la URL de BÚSQUEDA de Maps (no requiere API key ni coordenadas): abre
cualquier texto de dirección/lugar. Helpers para markdown (Streamlit), HTML
(cabeceras con unsafe_allow_html, emails/Telegram) y la URL cruda (PDF).
"""
import urllib.parse

_BASE = "https://www.google.com/maps/search/?api=1&query="


def maps_url(location) -> str:
    """URL de Google Maps para el texto de ubicación, o '' si está vacío."""
    loc = str(location or "").strip()
    if not loc:
        return ""
    return _BASE + urllib.parse.quote(loc)


def maps_link_md(location, label=None) -> str:
    """Markdown '[📍 label](url)' para st.markdown/st.caption; '' si vacío."""
    url = maps_url(location)
    if not url:
        return ""
    lbl = str(label if label is not None else location).strip()
    return f"[📍 {lbl}]({url})"


def maps_link_html(location, label=None, color="#2e6da4") -> str:
    """Ancla HTML para cabeceras (unsafe_allow_html), email y Telegram; '' si vacío."""
    url = maps_url(location)
    if not url:
        return ""
    lbl = str(label if label is not None else location).strip()
    return (f'<a href="{url}" target="_blank" '
            f'style="color:{color};text-decoration:none;">📍 {lbl}</a>')
