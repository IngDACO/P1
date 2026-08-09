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
def geocode_candidates(direccion: str, limit: int = 6) -> list:
    """Candidatos [{lat, lon, label}] de Nominatim para una dirección. Cacheado 1 día.

    Antes se pedía `limit=1` y se tomaba el primer resultado → para una dirección en
    texto libre eso solía caer en una calle parecida de otro país/ciudad. Ahora se
    traen VARIAS opciones (con la dirección completa `display_name`) para elegir la
    correcta; el clic en el mapa sigue disponible para afinar el punto exacto.
    """
    d = (direccion or "").strip()
    if not d:
        return []
    try:
        import requests
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": d, "format": "jsonv2", "limit": limit, "addressdetails": 1},
            headers={"User-Agent": "COPEX-SurveyApp/1.0 (ingdaco)"}, timeout=8)
        out = []
        j = r.json()
        if isinstance(j, list):
            for it in j:
                try:
                    out.append({"lat": float(it["lat"]), "lon": float(it["lon"]),
                                "label": str(it.get("display_name", "")).strip()})
                except Exception:
                    pass
        return out
    except Exception:
        return []


def geocode(direccion: str):
    """(lat, lon) del mejor candidato, o None. Compat con `home_ui` (proyectos viejos)."""
    c = geocode_candidates(direccion, limit=1)
    return (c[0]["lat"], c[0]["lon"]) if c else None


def location_picker(key, lat=None, lng=None, direccion=""):
    """Buscar dirección + clic en el mapa. Devuelve (lat, lng) elegidos o (None, None).
    El punto vive en session_state (`{key}_lat/_lng`); inicializa con lat/lng del proyecto."""
    klat, klng, kclick = f"{key}_lat", f"{key}_lng", f"{key}_lastclick"
    if klat not in st.session_state:
        st.session_state[klat] = lat
        st.session_state[klng] = lng
    slat, slng = st.session_state.get(klat), st.session_state.get(klng)

    st.caption(":material/place: Busca la dirección, **elige el resultado correcto** y/o haz "
               "**clic en el mapa** para afinar el punto exacto.")
    c1, c2 = st.columns([4, 1])
    q = c1.text_input("Buscar dirección", value=direccion, key=f"{key}_q",
                      label_visibility="collapsed", placeholder=":material/search: Buscar dirección…")
    if c2.button("Buscar", key=f"{key}_btn", use_container_width=True):
        _cands = geocode_candidates(q)
        st.session_state[f"{key}_cands"] = _cands
        if not _cands:
            st.warning("No encontré esa dirección. Añade ciudad/estado/país, o haz clic en el mapa.")
        st.rerun()

    # Candidatos de la última búsqueda: uno se fija solo; varios → elige el correcto.
    _cands = st.session_state.get(f"{key}_cands") or []
    if len(_cands) == 1:
        st.session_state[klat] = _cands[0]["lat"]
        st.session_state[klng] = _cands[0]["lon"]
        st.session_state.pop(f"{key}_cands", None)
        st.rerun()
    elif len(_cands) > 1:
        _labels = [c["label"] for c in _cands]
        _sel = st.selectbox("¿Cuál es? Elige el resultado exacto:", ["—"] + _labels,
                            key=f"{key}_candsel")
        if _sel != "—":
            _c = _cands[_labels.index(_sel)]
            st.session_state[klat], st.session_state[klng] = _c["lat"], _c["lon"]
            st.session_state.pop(f"{key}_cands", None)
            st.session_state.pop(f"{key}_candsel", None)
            st.rerun()

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

    st.caption(":material/lightbulb: Para el punto EXACTO: cambia a **Satélite** (control arriba-derecha "
               "del mapa) y haz **clic sobre el techo del edificio**. Nominatim (OSM, gratis) suele "
               "quedarse a nivel de calle en Australia.")
    center = [slat, slng] if slat is not None else list(_SYDNEY)
    m = folium.Map(location=center, zoom_start=18 if slat is not None else 11,
                   tiles="OpenStreetMap")
    # Capa satélite (Esri World Imagery, sin API key): ver el edificio real y clicar
    # el punto exacto cuando el geocodificador solo llega a nivel de calle.
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery", name="Satélite", control=True).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    if slat is not None:
        folium.Marker(center, tooltip="Ubicación del proyecto",
                      icon=folium.Icon(color="red")).add_to(m)
    out = st_folium(m, key=f"{key}_map", height=420,
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
