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


def _esc(s) -> str:
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


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


def sidebar_menu() -> str:
    """Renderiza el menú de iconos en el sidebar y devuelve la clave de la sección."""
    st.markdown("###### NAVEGACIÓN")
    sel = st.radio("Menú", [lbl for _, lbl in _SECCIONES], key="admin_nav",
                   label_visibility="collapsed")
    return _LBL2KEY.get(sel, "home")


# ── Barra superior (buscador + campana) ──────────────────────────
def render_topbar(grupo):
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
    from core import clock
    st.markdown(f"## 🏠 Home  ·  <span style='font-size:1rem;color:#6b7280;'>"
                f"{clock.today().strftime('%A %d/%m/%Y')}</span>", unsafe_allow_html=True)
    col_map, col_ag = st.columns([3, 2], gap="large")
    with col_map:
        st.markdown("#### 🗺 Proyectos en ejecución")
        _mapa_proyectos(grupo)
    with col_ag:
        st.markdown("#### 📋 Agenda de hoy")
        _agenda_hoy(grupo)


# ── Mapa de proyectos ────────────────────────────────────────────
@st.cache_data(ttl=86400, show_spinner=False)
def _geocode(direccion: str):
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


def _mapa_proyectos(grupo):
    from core import projects as P
    try:
        proys = [p for p in P.list_projects(grupo)
                 if str(p.get("Estado", "")) == "En progreso"]
    except Exception:
        proys = []
    if not proys:
        st.info("No hay proyectos en ejecución ahora mismo.")
        return

    filas, sin_ubic = [], []
    for p in proys:
        coord = _geocode(str(p.get("Ubicacion", "")))
        if coord:
            filas.append({"lat": coord[0], "lon": coord[1], "nombre": p.get("Nombre", "")})
        else:
            sin_ubic.append(str(p.get("Nombre", "")))

    if filas:
        st.map(pd.DataFrame(filas), latitude="lat", longitude="lon",
               color="#c0392b", size=80)
        st.caption("📍 " + "  ·  ".join(f["nombre"] for f in filas))
    else:
        st.info("Ninguno de los proyectos en ejecución tiene una ubicación geolocalizable todavía.")
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

    for f in filas:
        _fila_agenda(f)


def _fila_agenda(f):
    if f["etq"]:
        chip = (f'<span style="background:{f["color"]};color:#fff;padding:1px 9px;'
                f'border-radius:10px;font-size:0.78rem;white-space:nowrap;">{_esc(f["etq"])}</span>')
    else:
        chip = '<span style="color:#9aa7b8;font-size:0.78rem;">— sin asignar —</span>'
    extra = []
    if f["proy"]:
        extra.append(f'📁 {_esc(f["proy"])}')
    if f["nota"]:
        extra.append(_esc(f["nota"]))
    extra_html = (f'<div style="color:#6b7280;font-size:0.76rem;margin-top:1px;">'
                  f'{" · ".join(extra)}</div>' if extra else "")
    st.markdown(
        f'<div style="padding:6px 0;border-bottom:1px solid #eef1f5;">'
        f'<b style="font-size:0.9rem;">{_esc(f["nombre"])}</b> &nbsp; {chip}{extra_html}</div>',
        unsafe_allow_html=True)
