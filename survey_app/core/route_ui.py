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

from core.i18n import t
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
    # ⚠️ `use_container_width=True` (v307). El defecto de `st_folium` es `width=500`
    # FIJO, así que dentro de un bloque ancho el iframe ocupa todo pero el mapa se
    # dibuja a 500 px y el resto queda en BLANCO. Medido en vivo: iframe 1110 px con
    # el `.leaflet-container` a 500 → 610 px de aire. Era el hueco de la Ruta del día.
    st_folium(fmap, key=key, height=height, returned_objects=[],
              use_container_width=True)
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
        st.caption(t("You have no active sites assigned."))
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
        st.info(t("None of your sites has a map location yet. Ask your administrator to set it on the project."))
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

    st.markdown(t("**Suggested order** (nearest to farthest):"))
    for i, p in enumerate(ruta, 1):
        extra = f" · {p['cliente']}" if p["cliente"] else ""
        dirtxt = f" — {p['ubic']}" if p["ubic"] else ""
        st.markdown(f"{i}. **{p['nombre']}**{extra}{dirtxt}")

    url = gmaps_dir_url(ruta, desde_actual=True)
    if url:
        st.link_button(t("Open the route in Google Maps"), url,
                       icon=":material/navigation:", width="stretch")
        st.caption(t("Turn-by-turn navigation opens in Google Maps from your current location, going through every site in this order."))
    if sin_ubic:
        st.caption(t(":orange[:material/warning:] No location (they are left out of the route)") + ": "
                   + ", ".join(sin_ubic))


# ── Vista del ADMIN: ruta del día de la cuadrilla ────────────────
def render_ruta_dia(grupo):
    """A dónde va hoy cada persona de campo (según el roster), en un mapa + tabla."""
    from core import auth, roster, projects as P
    from core import clock

    # ⚠️ v314: SIN cabecera propia. `home_ui._sub_header` ya pinta "Planificación ·
    # Ruta del día" justo encima, así que este `#### Ruta del día de la cuadrilla`
    # repetía el título en la misma pantalla (mismo caso que el Panel en v291 y el
    # % de avance duplicado en v212). La explicación se va al `help` del selector:
    # gastaba una línea entera para decir lo que el título ya dice.
    from datetime import timedelta as _td

    # Salto de día pendiente: se aplica ANTES de instanciar el date_input, porque
    # escribir la clave de un widget YA creado es un error (regla v111).
    _salto = st.session_state.pop("_rd_salto", 0)
    if _salto:
        _b = st.session_state.get("rutadia_fecha") or clock.today(grupo)
        st.session_state["rutadia_fecha"] = _b + _td(days=_salto)

    # El `date_input` ocupaba los 1340 px de ancho para una fecha. Se acota y a su
    # lado van los saltos de día (esta pantalla se mira "hoy, y mañana qué").
    cf, cp, cn, cd = st.columns([1.6, 0.7, 0.7, 4])
    fecha = cf.date_input(t("Day"), value=clock.today(grupo), key="rutadia_fecha",
                          format="DD/MM/YYYY",
                          help=t("Where each field member is going according to the plan."))
    cp.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    cn.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if cp.button(":material/chevron_left:", key="rd_prev", width="stretch",
                 help=t("Previous day")):
        st.session_state["_rd_salto"] = -1
        st.rerun()
    if cn.button(":material/chevron_right:", key="rd_next", width="stretch",
                 help=t("Next day")):
        st.session_state["_rd_salto"] = 1
        st.rerun()
    _DIAS_L = [t("Monday"), t("Tuesday"), t("Wednesday"), t("Thursday"), t("Friday"),
               t("Saturday"), t("Sunday")]
    _MES_L = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
              "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    with cd:
        st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
        st.markdown(f":gray[{_DIAS_L[fecha.weekday()]} {fecha.day} of "
                    f"{_MES_L[fecha.month]}]")
    # ⚠️ v390: el fin de semana ya se puede planificar, así que aquí solo se corta
    # si REALMENTE no hay nada ese día — antes se cortaba por ser sábado y eso
    # ocultaría una ruta que alguien acaba de planificar. (El corte sigue haciendo
    # falta: sin él, un sábado normal saldría con todo el mundo «sin plan» y sin
    # que nada dijera por qué.)
    if fecha.weekday() > 4:
        from core import roster as _R
        try:
            _hay = _R.dia_tiene_datos(_R.get_semana(grupo, _R.lunes_de(fecha)),
                                      _R.DIAS_TODOS[fecha.weekday()])
        except Exception:
            _hay = []
        if not _hay:
            st.info(":material/weekend: Nothing is planned for this "
                    f"{_DIAS_L[fecha.weekday()].lower()}. The normal week is Monday to "
                    "Friday; the weekend is added from the Panel.")
            return

    try:
        campos = [u for u in auth.list_users(grupo)
                  if str(u.get("Rol", "")) == "campo"
                  and str(u.get("Activo", "SI")).strip().upper() in auth._ACTIVE_OK]
    except Exception:
        campos = []
    if not campos:
        st.info(t("There are no field users in the group."))
        return

    # ── Dónde ficharon DE VERDAD (v307) ──────────────────────────
    # El mismo dato que usa «Cumplimiento» en el Panel (v161/v293), ya cacheado: sin
    # esto la pantalla solo dice el PLAN, y la pregunta del admin a las 9 de la mañana
    # es si cada uno está donde debe. {clave_usuario: [{pid, nombre}]}
    from core import timeclock
    try:
        real = timeclock.proyectos_por_usuario_dia(grupo, fecha)
    except Exception:
        real = {}

    sitios = {}        # pid -> {nombre, lat, lon, personas:[], dir}
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
        # lo FICHADO por esta persona ese día (la clave es el login; nombre de respaldo)
        _fich = real.get(usr) or real.get(nom) or []
        _fich_pids = {str(x.get("pid", "")) for x in _fich if x.get("pid")}
        _fich_noms = [str(x.get("nombre", "")) for x in _fich if x.get("nombre")]
        for a in aa:
            pid = str(a.get("proyecto_id", "")).strip()
            if not pid:
                sin_prj.append(f"{nom} — {a.get('etiqueta') or a.get('asig')}")
                continue
            prj = P.get_project(pid)
            if not prj:
                sin_prj.append(f"{nom} — ({t('site not found')})")
                continue
            obra = str(prj.get("Nombre", ""))
            # Plan vs real, con las MISMAS tres lecturas que el Panel:
            if pid in _fich_pids:
                _estado = t("🟢 clocked in here")
            elif _fich_noms:
                _estado = t("🔴 clocked in at") + " " + ", ".join(_fich_noms[:2])
            else:
                _estado = t("⚠️ not clocked in")
            c = _coords_de(prj)
            if not c:
                sin_coord.append(f"{nom} → {obra}")
            else:
                s = sitios.setdefault(pid, {"nombre": obra, "lat": c[0], "lon": c[1],
                                            "personas": [],
                                            "dir": str(prj.get("Ubicacion", ""))})
                s["personas"].append(nom)
            # ⚠️ La fila entra AUNQUE la obra no tenga ubicación: antes se hacía
            # `continue` y esa persona desaparecía de la tabla — el KPI decía "1 sin
            # ubicación" y no había forma de ver de quién se trataba.
            en_obra.append({"Persona": nom,
                            "Horario": roster.franja_label(a.get("ini"), a.get("fin")) or t("full day"),
                            t("Site"): obra, t("Status"): _estado,
                            t("Address"): str(prj.get("Ubicacion", "")) or "—"})

    # ── KPIs ACTIVOS, con contexto (mismo criterio que HOME en v303) ──
    _n_pers = len(campos)
    _nav = _KPI_NAV
    k1, k2, k3, k4 = st.columns(4)
    if k1.button(f":material/engineering: On site\n\n{len(en_obra)}\n\n"
                 f"{t('of')} {_n_pers} {t('person') if _n_pers == 1 else t('people')}",
                 key="cpxkpi_rd_obra", width="stretch"):
        _nav("planificacion", "🎛 Panel")
    if k2.button(f"{t(':material/location_on: Sites')}\n\n{len(sitios)}\n\n"
                 + (t("with people today") if sitios else t("none today")),
                 key="cpxkpi_rd_sitios", width="stretch"):
        _nav("proyectos", "📊 Proyectos")
    if k3.button(f":material/wrong_location: No location\n\n{len(sin_coord)}\n\n"
                 + (t("set the pin") if sin_coord else t("all located")),
                 key="cpxkpi_rd_sinubic", width="stretch"):
        _nav("proyectos", "📊 Proyectos")
    # ⚠️ El pie NO se corta a lo bruto: `", ".join(nombres)[:18]` partía un nombre por
    # la mitad. Con una persona se dice quién es; con varias, cuántas.
    _sub_plan = (t("all planned") if not sin_plan
                 else (sin_plan[0] if len(sin_plan) == 1
                       else f"{len(sin_plan)} {t('people')}"))
    if k4.button(f":material/help: No plan\n\n{len(sin_plan)}\n\n{_sub_plan}",
                 key="cpxkpi_rd_sinplan", width="stretch"):
        _nav("planificacion", "🎛 Panel")

    if not sitios:
        st.info(t("Nobody has a site with a location assigned for that day."))
    else:
        # ── Mapa + sitios, lado a lado (v307) ────────────────────
        # Antes el mapa iba a ancho completo (dibujándose a 500 px) y la mitad derecha
        # de la pantalla quedaba vacía. Además se ORDENAN las paradas y se ofrece la
        # navegación: `ordenar_ruta`/`gmaps_dir_url` existen desde v270 y esta vista,
        # que se llama «Ruta del día», no las usaba — solo las usaba el campo.
        ruta = ordenar_ruta(list(sitios.values()))
        col_map, col_side = st.columns([3, 2], gap="large")
        with col_map:
            marcs = [{"lat": s["lat"], "lon": s["lon"],
                      "label": f"{i}. {s['nombre']} ({len(s['personas'])})",
                      "popup": f"{i}. {s['nombre']} — " + ", ".join(s["personas"])}
                     for i, s in enumerate(ruta, 1)]
            if not _folium_map(marcs, ruta_coords=[[s["lat"], s["lon"]] for s in ruta],
                               numerado=True, key="rutadia_map", height=420):
                _mapa_respaldo(marcs)
        with col_side:
            st.markdown(t("**Today's sites** — in travel order"))
            for i, s in enumerate(ruta, 1):
                with st.container(border=True, key=f"rdsitio_{i}"):
                    _n = len(s["personas"])
                    st.markdown(
                        f"**{i}. {s['nombre']}**  \n"
                        f":gray[{s['dir'] or t('no address')}]  \n"
                        f":material/group: {_n} persona{'' if _n == 1 else 's'} · "
                        + ", ".join(s["personas"]))
                    st.link_button(t("Directions"), gmaps_dir_url([s], desde_actual=True),
                                   icon=":material/navigation:",
                                   width="stretch")
            if len(ruta) > 1:
                st.link_button(t("Open the full route in Google Maps"),
                               gmaps_dir_url(ruta, desde_actual=False),
                               icon=":material/route:", width="stretch",
                               type="primary")

    if en_obra:
        import pandas as pd
        st.markdown(t("**Who goes where**"))
        st.dataframe(pd.DataFrame(en_obra), hide_index=True,
                     width="stretch")
        st.caption(t(":material/info: 'Status' compares the plan against the actual clock-ins for that day."))

    if sin_coord:
        st.caption(t(":orange[:material/warning:] Site with no map location (left out of "
                     "the route)") + ": " + " · ".join(sin_coord))
    if sin_prj:
        st.caption(t(":material/info: Assigned to a status/other (not a site)") + ": "
                   + " · ".join(sin_prj))


def _KPI_NAV(seccion, sub):
    """Salta a otra sección del admin. Import perezoso: `home_ui` importa este módulo,
    así que a nivel de módulo sería circular."""
    from core import home_ui
    home_ui.navegar(seccion, sub)
