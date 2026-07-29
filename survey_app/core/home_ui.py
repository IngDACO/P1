"""
Nueva navegación del ADMIN (v190) — primer pase, "para ver cómo se va viendo".

- Menú lateral de iconos (en el sidebar): Home · Fichaje · Planificación · Proyectos ·
  Finanzas · Inventario · Herramientas · Contactos.
- Barra superior: buscador + campana de alertas (popover).
- HOME real (doble columna): mapa de proyectos en ejecución (izq) + agenda de hoy
  desde el roster (der).
- Los demás apartados son placeholders ("en construcción"); se integrarán uno a uno.

Alcance: SOLO el rol administrador (owner/campo siguen con su navegación actual).
El mapa geocodifica la `Ubicacion` de texto con OpenStreetMap/Nominatim (sin API key,
cacheado). Cuando se valide el look, se decide Google Maps y/o un campo de coordenadas.
"""
import streamlit as st
import pandas as pd


# ── Menú lateral (iconos) ────────────────────────────────────────
_SECCIONES = [
    ("home",          "🏠  Home"),
    ("fichaje",       "⏱  Fichaje"),
    ("planificacion", "📅  Planificación"),
    ("proyectos",     "📁  Proyectos"),
    ("finanzas",      "💰  Finanzas"),
    ("inventario",    "📦  Inventario"),
    ("herramientas",  "🛠  Herramientas"),
    ("contactos",     "👥  Contactos"),
]
_LBL2KEY = {lbl: k for k, lbl in _SECCIONES}


_SUBKEY = {"planificacion": "adm_plan_sub", "proyectos": "adm_proy_sub",
           "finanzas": "adm_fin_sub", "herramientas": "adm_herr_sub"}


def navegar(seccion, sub_label=None):
    """Deja pendiente saltar a una sección (y sub-pestaña) del admin. Lo usan los
    elementos ACTIVOS (indicadores del resumen, métricas, pines…). Reejecuta."""
    st.session_state["_admin_nav_pending"] = (seccion, sub_label)
    st.rerun()


def _aplicar_nav_pending():
    """Aplica un salto pendiente ANTES de instanciar los radios (regla v111): se
    escribe la clave del widget antes de crearlo, nunca después."""
    p = st.session_state.pop("_admin_nav_pending", None)
    if not p:
        return
    seccion, sub_label = p if isinstance(p, (tuple, list)) else (p, None)
    lbl = next((l for k, l in _SECCIONES if k == seccion), None)
    if lbl:
        st.session_state["admin_nav"] = lbl
    if sub_label and _SUBKEY.get(seccion):
        st.session_state[_SUBKEY[seccion]] = sub_label


def sidebar_menu() -> str:
    """Renderiza el menú de iconos en el sidebar y devuelve la clave de la sección."""
    _aplicar_nav_pending()                     # aplica saltos de los elementos activos
    st.markdown("###### NAVEGACIÓN")
    sel = st.radio("Menú", [lbl for _, lbl in _SECCIONES], key="admin_nav",
                   label_visibility="collapsed")
    return _LBL2KEY.get(sel, "home")


# ── Barra superior (buscador + campana) ──────────────────────────
def render_topbar(grupo):
    # v201: la cabecera negra de Streamlit + el hueco superior quitaban espacio en la
    # vista del admin. La hacemos transparente (sin ocultarla, para no perder el botón
    # de desplegar el sidebar) y reducimos el padding superior del contenido.
    st.markdown("<style>header[data-testid='stHeader']{background:transparent;}"
                "div.block-container{padding-top:2.4rem !important;}</style>",
                unsafe_allow_html=True)
    c1, c2 = st.columns([9, 1])
    with c1:
        st.text_input("Buscar", key="topbar_search", label_visibility="collapsed",
                      placeholder="🔎  Buscar proyectos, personas, trabajos…")
    with c2:
        _campana(grupo)
    st.markdown("<hr style='margin:2px 0 14px 0;border:none;border-top:1px solid #e6e9ef;'>",
                unsafe_allow_html=True)


def _alertas(grupo) -> list:
    """Alertas para la campana. De momento: credenciales por vencer/vencidas del grupo.
    (Más fuentes —retrasos de proyecto, sobrepresupuesto— se sumarán después.)"""
    out = []
    try:
        from core import credentials as C
        if C.is_configured():
            for e in C.expiring(grupo)[:10]:
                est = "🔴 vencida" if e["dias"] < 0 else f"🟡 vence en {e['dias']} d"
                out.append(f"🎫 {e['tipo']} · {e['usuario']} — {est}")
    except Exception:
        pass
    return out


def _campana(grupo):
    try:
        alerts = _alertas(grupo)
    except Exception:
        alerts = []
    label = f"🔔 {len(alerts)}" if alerts else "🔔"
    with st.popover(label, use_container_width=True):
        st.markdown("**🔔 Alertas**")
        if not alerts:
            st.caption("Sin alertas por ahora.")
        for a in alerts:
            st.markdown(f"- {a}")


# ── Router de contenido ──────────────────────────────────────────
def render_admin_content(key, grupo):
    if key == "home":
        render_home(grupo)
    elif key == "fichaje":
        from core.timeclock_ui import render_timeclock_tab
        render_timeclock_tab()
    elif key == "planificacion":
        _seccion_planificacion(grupo)
    elif key == "proyectos":
        _seccion_proyectos(grupo)
    elif key == "finanzas":
        _seccion_finanzas(grupo)
    elif key == "inventario":
        _placeholder("📦 Inventario", "Control de inventario — módulo nuevo, en desarrollo.")
    elif key == "herramientas":
        _seccion_herramientas(grupo)
    elif key == "contactos":
        _placeholder("👥 Contactos", "Nuevo apartado de contactos — se desarrollará luego.")
    else:
        render_home(grupo)


def _subnav(titulo, opciones, key):
    """Sub-menú horizontal dentro de un apartado (mismo estilo que la nav actual)."""
    st.markdown(f"## {titulo}")
    sel = st.radio("sub", opciones, horizontal=True, key=key, label_visibility="collapsed")
    st.markdown("---")
    return sel


def _seccion_planificacion(grupo):
    # v191: la gestión de usuarios vive aquí (decisión del usuario), junto al tablero.
    sub = _subnav("📅 Planificación", ["📋 Tablero", "👷 Usuarios"], "adm_plan_sub")
    if sub == "📋 Tablero":
        from core import roster_ui
        roster_ui.render_planificacion(grupo)
    else:
        from core.auth_ui import _grupo_usuarios
        _grupo_usuarios(grupo)


def _seccion_proyectos(grupo):
    from core import projects_ui as PU
    sub = _subnav("📁 Proyectos", ["📊 Proyectos", "🗂 Agrupaciones"], "adm_proy_sub")
    if sub == "📊 Proyectos":
        PU._panel_proyectos(grupo)
    else:
        PU._panel_agrupaciones(grupo)


def _seccion_finanzas(grupo):
    from core import projects_ui as PU
    sub = _subnav("💰 Finanzas", ["💰 Gastos", "⏱ Horas"], "adm_fin_sub")
    if sub == "💰 Gastos":
        PU.render_group_expenses(grupo)
    else:
        PU.render_group_hours(grupo)


def _seccion_herramientas(grupo):
    rol = st.session_state.get("auth", {}).get("rol", "administrador")
    sub = _subnav("🛠 Herramientas",
                  ["📐 Survey", "🔩 Plomada", "✂️ Rieles", "🛡 Buffers", "🎗 Belting", "🦺 Pre-Start"],
                  "adm_herr_sub")
    if sub == "📐 Survey":
        from core.survey_ui import render_survey_tab
        render_survey_tab(rol, grupo)
    elif sub == "🔩 Plomada":
        from core.plumb_ui import render_plumb_tab
        render_plumb_tab()
    elif sub == "✂️ Rieles":
        from core.rail_cut_ui import render_rail_cut_tab
        render_rail_cut_tab()
    elif sub == "🛡 Buffers":
        from core.buffer_cut_ui import render_buffer_cut_tab
        render_buffer_cut_tab()
    elif sub == "🎗 Belting":
        from core.belting_ui import render_belting_tab
        render_belting_tab()
    else:
        from core.prestart_ui import render_prestart_tab
        render_prestart_tab()


def _placeholder(titulo, desc=""):
    st.markdown(f"## {titulo}")
    st.info("🚧 **En construcción** — este apartado se está rediseñando."
            + (f"\n\n{desc}" if desc else ""))


# ── HOME ─────────────────────────────────────────────────────────
def render_home(grupo):
    # v192: el "Centro de control del grupo" (KPIs + resumen del día) vivía en la
    # cabecera de "Mi grupo"; al reorganizar la nav quedó sin sitio → se reubica aquí,
    # que es la nueva landing. Reusa la función tal cual (no se duplica lógica).
    from core import projects_ui as PU
    PU.render_group_header(grupo)
    col_map, col_ag = st.columns([3, 2], gap="large")
    with col_map:
        st.markdown("#### 🗺 Proyectos activos")
        _mapa_proyectos(grupo)
    with col_ag:
        st.markdown("#### 📋 Agenda de hoy")
        _agenda_hoy(grupo)


# ── Mapa de proyectos ────────────────────────────────────────────
def _mapa_proyectos(grupo):
    from core import projects as P
    from core import location_ui
    # v195: "activos" = Planificado + En progreso. Antes filtraba solo "En progreso",
    # así que un proyecto recién creado (avance 0 → Planificado) nunca aparecía.
    _ACTIVOS = ("Planificado", "En progreso")
    try:
        proys = [p for p in P.list_projects(grupo)
                 if str(p.get("Estado", "")) in _ACTIVOS]
    except Exception:
        proys = []
    if not proys:
        st.info("No hay proyectos activos ahora mismo.")
        return

    filas, sin_ubic = [], []
    for p in proys:
        # v193: coordenadas guardadas (preciso). Respaldo para proyectos viejos aún
        # sin fijar: geocodificar su Ubicacion de texto (transición sin romper).
        lat = location_ui.to_float(p.get("Lat"))
        lng = location_ui.to_float(p.get("Lng"))
        if lat is None or lng is None:
            coord = location_ui.geocode(str(p.get("Ubicacion", "")))
            if coord:
                lat, lng = coord
        if lat is not None and lng is not None:
            filas.append({"lat": lat, "lon": lng, "nombre": str(p.get("Nombre", "")),
                          "pid": str(p.get("ID", ""))})
        else:
            sin_ubic.append(str(p.get("Nombre", "")))

    if filas:
        try:
            import folium
            from streamlit_folium import st_folium
            clat = sum(f["lat"] for f in filas) / len(filas)
            clon = sum(f["lon"] for f in filas) / len(filas)
            m = folium.Map(location=[clat, clon], zoom_start=11)
            for f in filas:
                folium.Marker([f["lat"], f["lon"]], popup=f["nombre"], tooltip=f["nombre"],
                              icon=folium.Icon(color="red")).add_to(m)
            _out = st_folium(m, key="home_map", height=380,
                             returned_objects=["last_object_clicked"])
            st.caption("📍 Toca un pin para abrir el proyecto.")
            # v199: pin ACTIVO → abre ese proyecto (reusa _prjsel_pending del panel)
            _clk = (_out or {}).get("last_object_clicked")
            if _clk:
                _cc = (round(float(_clk["lat"]), 6), round(float(_clk["lng"]), 6))
                if st.session_state.get("_home_map_click") != _cc:
                    st.session_state["_home_map_click"] = _cc
                    _best = min(filas, key=lambda r: (r["lat"] - _cc[0]) ** 2
                                + (r["lon"] - _cc[1]) ** 2)
                    if (abs(_best["lat"] - _cc[0]) < 1e-3
                            and abs(_best["lon"] - _cc[1]) < 1e-3 and _best["pid"]):
                        st.session_state["_prjsel_pending"] = _best["pid"]
                        navegar("proyectos", "📊 Proyectos")
        except Exception:
            st.map(pd.DataFrame(filas), latitude="lat", longitude="lon",
                   color="#c0392b", size=80)
            st.caption("📍 " + "  ·  ".join(f["nombre"] for f in filas))
    else:
        st.info("Ninguno de los proyectos en ejecución tiene ubicación todavía. "
                "Fíjala editando el proyecto → 🗺 Ubicación en el mapa.")
    if sin_ubic:
        st.caption("⚠️ Sin ubicación en el mapa: " + ", ".join(sin_ubic))


# ── Agenda de hoy (desde el roster) ──────────────────────────────
def _agenda_hoy(grupo):
    from core import roster as R
    from core import auth
    from core import clock
    from core import projects as P

    hoy = clock.today()
    if hoy.weekday() > 4:
        st.info("Hoy es fin de semana — la planificación es de lunes a viernes.")
        return

    dia = R.DIAS[hoy.weekday()]
    lunes = R.lunes_de(hoy)
    try:
        sem = R.get_semana(grupo, lunes)
        tidx = R.trabajos_idx(grupo)
    except Exception:
        sem, tidx = {}, {}

    staff = [u for u in auth.list_users(grupo) if str(u.get("Rol", "")).lower() == "campo"]
    if not staff:
        st.info("No hay personal de campo en el grupo.")
        return

    try:
        pmap = {str(p.get("ID", "")): str(p.get("Nombre", "")) for p in P.list_projects(grupo)}
    except Exception:
        pmap = {}

    st.caption(f"{R.DIAS_LABEL[dia]} · {len(staff)} personas")

    n_asig = n_off = n_leave = n_sin = 0
    filas = []
    for u in staff:
        usr = u["Usuario"]
        nombre = u.get("Nombre") or usr
        c = R.celda(sem, usr, dia)
        asig = str(c.get("asig", ""))
        nota = str(c.get("nota", "")).strip()
        if asig in R.ESTADOS:
            if asig == "OFF":
                n_off += 1
            elif asig == "LEAVE":
                n_leave += 1
        elif asig:
            n_asig += 1
        else:
            n_sin += 1
        filas.append({
            "usuario": usr,
            "nombre": nombre,
            "etq": R.etiqueta_de(asig, tidx),
            "color": R.color_de(asig, tidx),
            "nota": nota,
            "proy": pmap.get(R.proyecto_de(asig, tidx), ""),
            "asig": asig,
        })

    # resumen
    st.markdown(
        f"<div style='margin:2px 0 8px 0;font-size:0.85rem;color:#374151;'>"
        f"<b>{n_asig}</b> asignados &nbsp;·&nbsp; <b>{n_off}</b> OFF &nbsp;·&nbsp; "
        f"<b>{n_leave}</b> leave &nbsp;·&nbsp; <b>{n_sin}</b> sin asignar</div>",
        unsafe_allow_html=True)

    # v199: cada persona es un BOTÓN → su ficha (Planificación · Usuarios). El borde
    # izquierdo del botón lleva el color de su trabajo (mantiene el lenguaje visual).
    _css = ["<style>"]
    for _i, f in enumerate(filas):
        _css.append(f".st-key-agper_{_i} button{{border-left:5px solid {f['color']}!important;"
                    "justify-content:flex-start!important;text-align:left!important;}")
    _css.append("</style>")
    st.markdown("".join(_css), unsafe_allow_html=True)

    for _i, f in enumerate(filas):
        _lbl = f"{f['nombre']} · {f['etq'] or 'sin asignar'}"
        _hlp = " · ".join(x for x in (f.get("proy"), f.get("nota")) if x) or None
        if st.button(_lbl, key=f"agper_{_i}", use_container_width=True, help=_hlp):
            _u = f.get("usuario", "")
            _nom = f.get("nombre", "") or _u
            st.session_state["gp_fichasel"] = f"{_nom} ({_u})"   # pre-selecciona la persona
            navegar("planificacion", "👷 Usuarios")
