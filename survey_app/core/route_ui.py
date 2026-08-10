"""
Ruta del día (v270): las obras en el mapa, ordenadas para ir a terreno.

- Técnico de campo (`render_mi_ruta`): SUS obras activas asignadas en el mapa,
  ordenadas de la más cercana a la más lejana, con un botón que abre la navegación
  paso a paso en Google Maps pasando por todas las paradas.
- Admin (`render_ruta_dia`): a dónde va HOY cada persona de la cuadrilla (según el
  roster), una parada por obra, para planear el día.

El ORDEN se calcula con una heurística "vecino más cercano" (pura Python, sin coste
ni API). La navegación real por carretera la hace **Google Maps por link** (URL de
direcciones), así que NO gasta la API de geocodificación/Directions.
"""
import math
import urllib.parse
import streamlit as st


# ── Geometría / orden ────────────────────────────────────────────
def _haversine(a, b) -> float:
    """Distancia aproximada en km entre (lat, lon) a y (lat, lon) b."""
    R = 6371.0
    la1, lo1 = math.radians(a[0]), math.radians(a[1])
    la2, lo2 = math.radians(b[0]), math.radians(b[1])
    dla, dlo = la2 - la1, lo2 - lo1
    h = math.sin(dla / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlo / 2) ** 2
    return 2 * R * math.asin(min(1.0, math.sqrt(h)))


def ordenar_ruta(paradas: list, inicio=None) -> list:
    """Ordena paradas [{lat,lon,...}] por vecino más cercano (greedy).

    `inicio`=(lat,lon) opcional (p.ej. dónde arranca el técnico); si es None se
    empieza por la primera parada de la lista.
    """
    rest = list(paradas)
    if not rest:
        return []
    ruta = []
    if inicio is not None:
        actual = tuple(inicio)
    else:
        primero = rest.pop(0)
        ruta.append(primero)
        actual = (primero["lat"], primero["lon"])
    while rest:
        j = min(range(len(rest)),
                key=lambda i: _haversine(actual, (rest[i]["lat"], rest[i]["lon"])))
        p = rest.pop(j)
        ruta.append(p)
        actual = (p["lat"], p["lon"])
    return ruta


def gmaps_dir_url(paradas: list, desde_actual: bool = True) -> str:
    """URL de Google Maps con navegación por todas las paradas EN ORDEN.

    Google traza la ruta real por carretera desde el link (no usa la API de
    Directions → gratis). Con `desde_actual` el trayecto arranca en la ubicación
    actual del teléfono; si no, arranca en la primera parada.
    """
    pts = [(p["lat"], p["lon"]) for p in paradas]
    if not pts:
        return ""
    q = {"api": "1", "travelmode": "driving"}
    if desde_actual:
        q["destination"] = f"{pts[-1][0]},{pts[-1][1]}"
        wpts = pts[:-1]
    else:
        q["origin"] = f"{pts[0][0]},{pts[0][1]}"
        q["destination"] = f"{pts[-1][0]},{pts[-1][1]}"
        wpts = pts[1:-1]
    if wpts:
        q["waypoints"] = "|".join(f"{la},{lo}" for la, lo in wpts)
    return "https://www.google.com/maps/dir/?" + urllib.parse.urlencode(q, safe=",|")


# ── Coordenadas / mapa ───────────────────────────────────────────
def _coords_de(prj) -> tuple:
    """(lat, lon) de un proyecto: coords guardadas (precisas) o, de respaldo, el
    geocode de su texto de Ubicacion (proyectos viejos). None si no hay."""
    from core import location_ui
    lat = location_ui.to_float(prj.get("Lat"))
    lon = location_ui.to_float(prj.get("Lng"))
    if lat is None or lon is None:
        c = location_ui.geocode(str(prj.get("Ubicacion", "")))
        if c:
            lat, lon = c
    return (lat, lon) if (lat is not None and lon is not None) else None


def _badge(n, color="#2e6da4") -> str:
    return (f'<div style="background:{color};color:#fff;width:24px;height:24px;'
            f'border-radius:50%;border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.4);'
            f'display:flex;align-items:center;justify-content:center;'
            f'font:bold 12px sans-serif">{n}</div>')


def _folium_map(marcadores, ruta_coords=None, numerado=True, key="ruta_map",
                height=380) -> bool:
    """Dibuja el mapa. `marcadores`=[{lat,lon,label,popup,color?}]; `ruta_coords`=
    [[lat,lon],...] para la polilínea del recorrido (o None). Devuelve False si
    folium no está disponible (para caer a un respaldo)."""
    try:
        import folium
        from streamlit_folium import st_folium
    except Exception:
        return False
    lats = [m["lat"] for m in marcadores]
    lons = [m["lon"] for m in marcadores]
    fmap = folium.Map(location=[sum(lats) / len(lats), sum(lons) / len(lons)],
                      zoom_start=12)
    if ruta_coords and len(ruta_coords) >= 2:
        folium.PolyLine(ruta_coords, color="#2e6da4", weight=3, opacity=0.75,
                        dash_array="6,8").add_to(fmap)
    for i, mk in enumerate(marcadores, 1):
        if numerado:
            icon = folium.DivIcon(html=_badge(i, mk.get("color", "#2e6da4")),
                                  icon_size=(28, 28), icon_anchor=(14, 14))
        else:
            icon = folium.Icon(color="blue", icon="briefcase", prefix="fa")
        folium.Marker([mk["lat"], mk["lon"]], tooltip=mk.get("label", ""),
                      popup=mk.get("popup"), icon=icon).add_to(fmap)
    if len(marcadores) >= 2:
        fmap.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])
    st_folium(fmap, key=key, height=height, returned_objects=[])
    return True


def _mapa_respaldo(marcadores):
    import pandas as pd
    st.map(pd.DataFrame([{"lat": m["lat"], "lon": m["lon"]} for m in marcadores]))


# ── Vista del CAMPO: mi ruta ─────────────────────────────────────
def render_mi_ruta(usuario, grupo):
    """Las obras activas del técnico, ordenadas, con navegación a Google Maps."""
    from core import projects as P
    _INACTIVOS = ("Completado", "Cancelado", "Archivado")
    try:
        proys = [p for p in P.list_projects_for_field(usuario, grupo=grupo)
                 if str(p.get("Estado", "")) not in _INACTIVOS]
    except Exception:
        proys = []
    if not proys:
        st.caption("No tienes obras activas asignadas.")
        return

    paradas, sin_ubic = [], []
    for p in proys:
        c = _coords_de(p)
        if c:
            paradas.append({"lat": c[0], "lon": c[1],
                            "nombre": str(p.get("Nombre", "")),
                            "cliente": str(p.get("Cliente", "")),
                            "ubic": str(p.get("Ubicacion", ""))})
        else:
            sin_ubic.append(str(p.get("Nombre", "")))

    if not paradas:
        st.info("Ninguna de tus obras tiene ubicación en el mapa todavía. "
                "Pídele al administrador que la fije en el proyecto.")
        return

    ruta = ordenar_ruta(paradas)
    marcs = [{"lat": p["lat"], "lon": p["lon"], "label": f"{i}. {p['nombre']}",
              "popup": f"{i}. {p['nombre']}"
                       + (f" · {p['cliente']}" if p["cliente"] else "")}
             for i, p in enumerate(ruta, 1)]
    coords = [[p["lat"], p["lon"]] for p in ruta]
    if not _folium_map(marcs, ruta_coords=coords, numerado=True,
                       key=f"miruta_{usuario}"):
        _mapa_respaldo(marcs)

    st.markdown("**Orden sugerido** (de la más cercana a la más lejana):")
    for i, p in enumerate(ruta, 1):
        extra = f" · {p['cliente']}" if p["cliente"] else ""
        dirtxt = f" — {p['ubic']}" if p["ubic"] else ""
        st.markdown(f"{i}. **{p['nombre']}**{extra}{dirtxt}")

    url = gmaps_dir_url(ruta, desde_actual=True)
    if url:
        st.link_button("Abrir la ruta en Google Maps", url,
                       icon=":material/navigation:", use_container_width=True)
        st.caption("La navegación paso a paso la abre Google Maps desde tu "
                   "ubicación actual, pasando por todas las obras en este orden.")
    if sin_ubic:
        st.caption(":orange[:material/warning:] Sin ubicación (no entran en la ruta): "
                   + ", ".join(sin_ubic))


# ── Vista del ADMIN: ruta del día de la cuadrilla ────────────────
def render_ruta_dia(grupo):
    """A dónde va hoy cada persona de campo (según el roster), en un mapa + tabla."""
    from core import auth, roster, projects as P
    from core import clock

    st.markdown("#### :material/route: Ruta del día de la cuadrilla")
    st.caption("A dónde va cada persona de campo según la planificación. "
               "Elige el día para verlo.")
    fecha = st.date_input("Día", value=clock.today(grupo), key="rutadia_fecha",
                          format="DD/MM/YYYY")

    try:
        campos = [u for u in auth.list_users(grupo)
                  if str(u.get("Rol", "")) == "campo"
                  and str(u.get("Activo", "SI")).strip().upper() in auth._ACTIVE_OK]
    except Exception:
        campos = []
    if not campos:
        st.info("No hay usuarios de campo en el grupo.")
        return

    sitios = {}        # pid -> {nombre, lat, lon, personas:[]}
    en_obra = []       # filas de la tabla
    sin_coord, sin_prj, sin_plan = [], [], []
    for u in campos:
        usr = str(u.get("Usuario", ""))
        nom = str(u.get("Nombre", "") or usr)
        try:
            aa = roster.asignaciones_dia(grupo, usr, fecha)   # v274: varias por día
        except Exception:
            aa = []
        if not aa:
            sin_plan.append(nom)
            continue
        for a in aa:
            pid = str(a.get("proyecto_id", "")).strip()
            if not pid:
                sin_prj.append(f"{nom} — {a.get('etiqueta') or a.get('asig')}")
                continue
            prj = P.get_project(pid)
            if not prj:
                sin_prj.append(f"{nom} — (obra no encontrada)")
                continue
            obra = str(prj.get("Nombre", ""))
            c = _coords_de(prj)
            if not c:
                sin_coord.append(f"{nom} → {obra}")
                continue
            s = sitios.setdefault(pid, {"nombre": obra, "lat": c[0], "lon": c[1],
                                        "personas": []})
            s["personas"].append(nom)
            en_obra.append({"Persona": nom, "Obra": obra,
                            "Dirección": str(prj.get("Ubicacion", ""))})

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("En obra", len(en_obra))
    k2.metric("Sitios", len(sitios))
    k3.metric("Sin ubicación", len(sin_coord))
    k4.metric("Sin plan", len(sin_plan))

    if sitios:
        marcs = []
        for s in sitios.values():
            pers = ", ".join(s["personas"])
            marcs.append({"lat": s["lat"], "lon": s["lon"],
                          "label": f"{s['nombre']} ({len(s['personas'])})",
                          "popup": f"{s['nombre']} — {pers}"})
        if not _folium_map(marcs, numerado=False, key="rutadia_map", height=420):
            _mapa_respaldo(marcs)
    else:
        st.info("Nadie tiene una obra con ubicación asignada para ese día.")

    if en_obra:
        import pandas as pd
        st.dataframe(pd.DataFrame(en_obra), hide_index=True,
                     use_container_width=True)

    if sin_coord:
        st.caption(":orange[:material/warning:] Obra sin ubicación en el mapa: "
                   + " · ".join(sin_coord))
    if sin_prj:
        st.caption(":material/info: Asignado a un estado/otro (no es obra): "
                   + " · ".join(sin_prj))
    if sin_plan:
        st.caption(":material/help: Sin planificación ese día: " + ", ".join(sin_plan))
