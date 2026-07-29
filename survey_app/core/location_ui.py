"""
Selector de ubicación de un proyecto (v193): buscar dirección + clic en el mapa
para fijar el pin, guardando las COORDENADAS (Lat/Lng) en el proyecto. Así el mapa
de HOME solo lee coordenadas —preciso, sin geocodificar cada vez—.

Usa folium + streamlit-folium (sin API key, OpenStreetMap). Import perezoso: si la
librería no está, cae a entrada manual de coordenadas (la app no se rompe).

⚠️ El mapa necesita reruns para capturar el clic, así que este selector debe ir
FUERA de cualquier `st.form` (igual que el multiselect de asignados en el detalle).
"""
import streamlit as st

_SYDNEY = (-33.8688, 151.2093)   # centro por defecto si aún no hay pin


def to_float(v):
    """Texto/valor → float, o None si vacío/inválido. 0,0 se trata como 'sin ubicación'
    (no es un punto real para obras y evita pines en el golfo de Guinea)."""
    try:
        f = float(v)
        return f if (f or f == 0.0) and abs(f) > 1e-9 else None
    except Exception:
        return None


@st.cache_data(ttl=86400, show_spinner=False)
def geocode(direccion: str):
    """(lat, lon) de una dirección de texto vía Nominatim (sin key), o None. Cacheado 1 día."""
    d = (direccion or "").strip()
    if not d:
        return None
    try:
        import requests
        r = requests.get("https://nominatim.openstreetmap.org/search",
                         params={"q": d, "format": "json", "limit": 1},
                         headers={"User-Agent": "COPEX-SurveyApp/1.0"}, timeout=6)
        j = r.json()
        if isinstance(j, list) and j:
            return float(j[0]["lat"]), float(j[0]["lon"])
    except Exception:
        pass
    return None


def location_picker(key, lat=None, lng=None, direccion=""):
    """Buscar dirección + clic en el mapa. Devuelve (lat, lng) elegidos o (None, None).
    El punto vive en session_state (`{key}_lat/_lng`); inicializa con lat/lng del proyecto."""
    klat, klng, kclick = f"{key}_lat", f"{key}_lng", f"{key}_lastclick"
    if klat not in st.session_state:
        st.session_state[klat] = lat
        st.session_state[klng] = lng
    slat, slng = st.session_state.get(klat), st.session_state.get(klng)

    st.caption("📍 Busca la dirección y/o haz **clic en el mapa** para fijar el punto exacto.")
    c1, c2 = st.columns([4, 1])
    q = c1.text_input("Buscar dirección", value=direccion, key=f"{key}_q",
                      label_visibility="collapsed", placeholder="🔎 Buscar dirección…")
    if c2.button("Buscar", key=f"{key}_btn", use_container_width=True):
        coord = geocode(q)
        if coord:
            st.session_state[klat], st.session_state[klng] = coord
            st.rerun()
        else:
            st.warning("No encontré esa dirección. Prueba con más detalle o haz clic en el mapa.")

    try:
        import folium
        from streamlit_folium import st_folium
    except Exception:
        st.info("Mapa no disponible; ingresa las coordenadas a mano (las ves en Google Maps: "
                "clic derecho → coordenadas).")
        m1, m2 = st.columns(2)
        _la = m1.text_input("Lat", value="" if slat is None else str(slat), key=f"{key}_mlat")
        _ln = m2.text_input("Lng", value="" if slng is None else str(slng), key=f"{key}_mlng")
        return to_float(_la), to_float(_ln)

    center = [slat, slng] if slat is not None else list(_SYDNEY)
    m = folium.Map(location=center, zoom_start=16 if slat is not None else 10)
    if slat is not None:
        folium.Marker(center, tooltip="Ubicación del proyecto",
                      icon=folium.Icon(color="red")).add_to(m)
    out = st_folium(m, key=f"{key}_map", height=340,
                    returned_objects=["last_clicked"])

    clicked = (out or {}).get("last_clicked")
    if clicked:
        cc = (round(float(clicked["lat"]), 7), round(float(clicked["lng"]), 7))
        if st.session_state.get(kclick) != cc:      # solo un clic NUEVO mueve el pin
            st.session_state[kclick] = cc
            st.session_state[klat], st.session_state[klng] = cc
            st.rerun()

    slat, slng = st.session_state.get(klat), st.session_state.get(klng)
    if slat is not None:
        st.caption(f"Coordenadas fijadas: **{slat:.5f}, {slng:.5f}**")
    else:
        st.caption("_Sin ubicación fijada aún._")
    return slat, slng
