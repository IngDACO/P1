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


def _secret(*names):
    """Primer secret no vacío de la lista (o None). Tolerante a que no exista st.secrets."""
    try:
        for n in names:
            v = st.secrets.get(n)
            if v:
                return str(v).strip()
    except Exception:
        pass
    return None


def geocoder_activo() -> str:
    """Qué motor de geocodificación está en uso: 'google' (preciso) o 'osm' (aproximado)."""
    return "google" if _secret("GOOGLE_MAPS_API_KEY", "GOOGLE_GEOCODING_API_KEY") else "osm"


def _google_geocode(d: str, key: str, pais: str) -> list:
    """Geocodificación con Google (precisa, con número de casa en AU)."""
    try:
        import requests
        r = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": d, "key": key, "region": (pais or "au").lower()},
            timeout=8)
        j = r.json()
        out = []
        if j.get("status") == "OK":
            for it in j.get("results", []):
                loc = it.get("geometry", {}).get("location", {})
                try:
                    out.append({"lat": float(loc["lat"]), "lon": float(loc["lng"]),
                                "label": str(it.get("formatted_address", "")).strip(),
                                "exacto": it.get("geometry", {}).get("location_type")
                                          in ("ROOFTOP", "RANGE_INTERPOLATED")})
                except Exception:
                    pass
        return out
    except Exception:
        return []


def _nominatim_geocode(d: str, limit: int, pais: str) -> list:
    """Respaldo gratuito (OpenStreetMap). Restringe el país para no caer en otra nación."""
    try:
        import requests
        params = {"q": d, "format": "jsonv2", "limit": limit, "addressdetails": 1}
        if pais:
            params["countrycodes"] = pais.lower()   # evita "259 Cleveland St" en EE.UU.
        r = requests.get(
            "https://nominatim.openstreetmap.org/search", params=params,
            headers={"User-Agent": "COPEX-SurveyApp/1.0 (ingdaco)"}, timeout=8)
        out = []
        j = r.json()
        if isinstance(j, list):
            for it in j:
                try:
                    out.append({"lat": float(it["lat"]), "lon": float(it["lon"]),
                                "label": str(it.get("display_name", "")).strip(),
                                "exacto": it.get("addresstype") in
                                          ("building", "house", "amenity")})
                except Exception:
                    pass
        return out
    except Exception:
        return []


@st.cache_data(ttl=86400, show_spinner=False)
def geocode_candidates(direccion: str, limit: int = 6) -> list:
    """Candidatos [{lat, lon, label, exacto}] para una dirección. Cacheado 1 día.

    Prioriza **Google Geocoding** si hay API key en secrets (`GOOGLE_MAPS_API_KEY`):
    es la única vía que ubica el NÚMERO de casa exacto en Australia. Si no hay key,
    cae a **Nominatim/OSM** restringido al país (gratis, pero a nivel de calle: OSM
    no tiene todos los números de casa de AU). El clic en el mapa queda como afine.
    """
    d = (direccion or "").strip()
    if not d:
        return []
    pais = _secret("GEO_PAIS", "GEO_COUNTRY") or "au"
    key = _secret("GOOGLE_MAPS_API_KEY", "GOOGLE_GEOCODING_API_KEY")
    if key:
        g = _google_geocode(d, key, pais)
        if g:
            return g[:limit]
    return _nominatim_geocode(d, limit, pais)


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

    st.caption(":material/place: Escribe la dirección y pulsa **Buscar**: la app la ubica sola. "
               "Si hay varias coincidencias, elige la correcta. (Opcional: clic en el mapa para afinar.)")
    if geocoder_activo() == "google":
        st.caption("🎯 Precisión: **Google** (número de casa exacto).")
    else:
        st.caption("≈ Precisión aproximada (OpenStreetMap). Falta la API key de Google "
                   "para ubicar el número exacto.")
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

    center = [slat, slng] if slat is not None else list(_SYDNEY)
    m = folium.Map(location=center, zoom_start=17 if slat is not None else 11)
    if slat is not None:
        folium.Marker(center, tooltip="Ubicación del proyecto",
                      icon=folium.Icon(color="red")).add_to(m)
    out = st_folium(m, key=f"{key}_map", height=360,
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
