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
# v232: iconos Material (profesionales, monocromo, azul COPEX vía CSS) en vez de emoji.
# Las labels son display; la lógica usa la CLAVE, así que cambiarlas es seguro.
_SECCIONES = [
    ("home",          ":material/home: Home"),
    ("fichaje",       ":material/schedule: Fichaje"),
    ("planificacion", ":material/calendar_month: Planificación"),
    ("proyectos",     ":material/folder: Proyectos"),
    ("finanzas",      ":material/payments: Finanzas"),
    ("inventario",    ":material/inventory_2: Inventario"),
    ("herramientas",  ":material/build: Herramientas"),
    ("contactos",     ":material/contacts: Contactos"),
]
_LBL2KEY = {lbl: k for k, lbl in _SECCIONES}


# Sub-pestañas (nivel 2) de cada sección, centralizadas (v229): (clave_de_estado, [labels]).
# Antes estaban repartidas en cada `_seccion_*`; ahora también las usa el sidebar (acordeón).
# v232: cada sub = (id, display). El ID (con emoji) es el IDENTIFICADOR interno — lo usan
# los deep-links (`_ir_a`/`_admin_nav_pending`) y el match en `_seccion_*`, así que NO cambia.
# `display` es lo que se MUESTRA (icono Material). Solo cambia lo visible → cero riesgo.
_SUBSECCIONES = {
    "planificacion": ("adm_plan_sub", [
        ("🎛 Panel", ":material/dashboard: Panel"),
        ("🗺 Ruta del día", ":material/route: Ruta del día"),
        ("👷 Usuarios", ":material/badge: Usuarios")]),
    "proyectos": ("adm_proy_sub", [
        ("📊 Proyectos", ":material/format_list_bulleted: Proyectos"),
        ("🗂 Agrupaciones", ":material/account_tree: Agrupaciones")]),
    "finanzas": ("adm_fin_sub", [
        ("📊 Resumen", ":material/insights: Resumen"),
        ("💰 Gastos", ":material/receipt_long: Gastos"),
        ("🧾 Facturas", ":material/receipt: Facturas"),
        ("👥 Nóminas", ":material/payments: Nóminas"),
        ("⏱ Horas", ":material/schedule: Horas"),
        ("📈 Rentabilidad", ":material/trending_up: Rentabilidad")]),
    "herramientas": ("adm_herr_sub", [
        ("🧰 Inicio", ":material/apps: Inicio"),
        ("📐 Survey", ":material/architecture: Survey"),
        ("🔩 Plomada", ":material/straighten: Plomada"),
        ("✂️ Rieles", ":material/content_cut: Rieles"),
        ("🛡 Buffers", ":material/shield: Buffers"),
        ("🎗 Belting", ":material/swap_vert: Belting"),
        ("🦺 Pre-Start", ":material/health_and_safety: Pre-Start")]),
}
_SUBKEY = {k: v[0] for k, v in _SUBSECCIONES.items()}   # {seccion: clave_de_estado}


# ── La shell POR ROL (v297) ───────────────────────────────────────
# Hasta v296 esta shell era solo del administrador y propietario/campo seguían con
# la nav vieja de `app.py` (cabecera COPEX + radio horizontal). Para poder retirar
# aquella del todo, la shell pasa a servir a los tres roles.
#
# ⚠️ El rol se resuelve DENTRO (`_rol()`), no se pasa por parámetro: así NINGUNA
# firma cambia (`sidebar_menu()`, `render_admin_content(key, grupo)`, `_sub_header`)
# y el camino del admin queda byte a byte como estaba. Menos superficie, menos riesgo.

# CAMPO: se respeta su nav de siempre (Mis proyectos · Fichaje · Pre-Start · las 5
# técnicas · Mis credenciales · Mis colillas). El Pre-Start va SUELTO, no dentro de
# Herramientas: es seguridad de obra y su acción diaria (regla v154); enterrarlo un
# nivel le costaría un toque cada mañana justo a quien lo usa en el móvil.
_SECCIONES_CAMPO = [
    ("misproyectos", ":material/assignment: Mis proyectos"),
    ("fichaje",      ":material/schedule: Fichaje"),
    ("prestart",     ":material/health_and_safety: Pre-Start"),
    ("herramientas", ":material/build: Herramientas"),
    ("credenciales", ":material/badge: Mis credenciales"),
    ("colillas",     ":material/payments: Mis colillas"),
]
# Sus Herramientas son las 5 TÉCNICAS: el Pre-Start ya es sección propia, y
# duplicarlo lo dejaría en dos sitios (el patrón de v140 que evitamos).
_SUBSECCIONES_CAMPO = {
    "herramientas": (_SUBSECCIONES["herramientas"][0],
                     [(_i, _d) for _i, _d in _SUBSECCIONES["herramientas"][1]
                      if _i != "🦺 Pre-Start"]),
}

# PROPIETARIO (v298): su nav vieja era Administración · Pre-Start · las 5 técnicas
# (sin fichaje — no ficha, decisión de v93). Las 6 pestañas internas de su panel
# pasan a ser sub-secciones de la shell.
_SECCIONES_OWNER = [
    ("administracion", ":material/shield_person: Administración"),
    ("prestart",       ":material/health_and_safety: Pre-Start"),
    ("herramientas",   ":material/build: Herramientas"),
]
_SUBSECCIONES_OWNER = {
    # ⚠️ La clave de estado es `owner_sec`, LA MISMA del radio viejo, a propósito:
    # hay un deep-link (`survey_ui` al guardar un survey) que escribe
    # `owner_sec = "📁 Proyectos"`. Reutilizarla lo mantiene vivo sin tocarlo.
    "administracion": ("owner_sec", [
        ("🌐 Resumen",   ":material/dashboard: Resumen"),
        ("🏢 Grupos",    ":material/business: Grupos"),
        ("👥 Usuarios",  ":material/group: Usuarios"),
        ("📁 Proyectos", ":material/folder: Proyectos"),
        ("🚆 Rieles",    ":material/train: Rieles"),
        ("📚 Manuales",  ":material/menu_book: Manuales")]),
    "herramientas": _SUBSECCIONES_CAMPO["herramientas"],   # las 5 técnicas, sin Pre-Start
}

_SECCIONES_ROL = {
    "administrador": _SECCIONES,
    "campo":         _SECCIONES_CAMPO,
    "propietario":   _SECCIONES_OWNER,
}
_SUBSECCIONES_ROL = {
    "administrador": _SUBSECCIONES,
    "campo":         _SUBSECCIONES_CAMPO,
    "propietario":   _SUBSECCIONES_OWNER,
}


def _rol() -> str:
    try:
        return str(st.session_state.get("auth", {}).get("rol", "")).strip().lower()
    except Exception:
        return ""


@st.cache_data(show_spinner=False)
def _version() -> str:
    """Versión desplegada, para el topbar. Mismo fichero y codificación que app.py
    (`utf-8-sig` quita el BOM que PowerShell escribe en VERSION)."""
    import os
    try:
        ruta = os.path.join(os.path.dirname(os.path.dirname(__file__)), "VERSION")
        return open(ruta, encoding="utf-8-sig").read().strip()
    except Exception:
        return ""


# ⚠️ El default de los dos es el del CAMPO (menor privilegio), NO el del admin.
# Desde v299 la shell sirve a TODOS los roles, así que este default decide qué ve
# un `Rol` que no reconozcamos (un typo en la hoja Login, un rol futuro a medio
# añadir). Caer en la nav de gestión sería regalar acceso por un error de dato.
def _secciones():
    return _SECCIONES_ROL.get(_rol(), _SECCIONES_CAMPO)


def _subsecciones():
    return _SUBSECCIONES_ROL.get(_rol(), _SUBSECCIONES_CAMPO)


def _lbl2key():
    return {lbl: k for k, lbl in _secciones()}


def _subkey():
    return {k: v[0] for k, v in _subsecciones().items()}


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
    lbl = next((l for k, l in _secciones() if k == seccion), None)
    if lbl:
        st.session_state["admin_nav"] = lbl
        st.session_state["_admin_expanded"] = seccion   # v230: desplegar la sección navegada
    _sk = _subkey()
    if sub_label and _sk.get(seccion):
        st.session_state[_sk[seccion]] = sub_label


def _track_history(cur):
    """Apila la sección de la que venimos, para el botón Atrás (v204). NO apila cuando
    el cambio fue un 'atrás' (para no rebotar). Tope de 20."""
    prev = st.session_state.get("_nav_cur")
    if prev is not None and prev != cur:
        if st.session_state.pop("_nav_back", False):
            pass                                   # venimos de un 'atrás'
        else:
            hist = st.session_state.setdefault("_nav_hist", [])
            hist.append(prev)
            del hist[:-20]
    st.session_state["_nav_cur"] = cur


def puede_atras() -> bool:
    return bool(st.session_state.get("_nav_hist"))


def ir_atras():
    hist = st.session_state.get("_nav_hist") or []
    if hist:
        st.session_state["_nav_back"] = True       # que _track_history no lo re-apile
        navegar(hist.pop())


def sidebar_menu() -> str:
    """Menú lateral de 2 niveles (v229): secciones (nivel 1) y, bajo la ACTIVA, sus
    sub-pestañas (nivel 2) indentadas y clickeables → se va DIRECTO desde el sidebar
    (acordeón: solo la activa despliega sus hijas). Los botones se estilan como ítems de
    menú vía CSS `.st-key-…` (verificado en vivo). Devuelve la clave de la sección activa."""
    _aplicar_nav_pending()                     # aplica saltos de los elementos activos
    _SECS, _SUBS = _secciones(), _subsecciones()
    _cur_lbl = st.session_state.get("admin_nav") or _SECS[0][1]
    # ⚠️ El default cae a la PRIMERA sección DEL ROL, no a "home": el campo no tiene
    # Home, así que un `admin_nav` heredado de otro rol dejaría la shell en blanco.
    _cur = _lbl2key().get(_cur_lbl, _SECS[0][0])
    # v230: sección DESPLEGADA en el sidebar. Puede diferir de la ACTIVA porque
    # "desplegar" ya NO navega (antes tocar la sección abría su 1ª sub-pestaña de una).
    # Por defecto la activa está desplegada; "" = todo plegado.
    _exp = st.session_state.get("_admin_expanded")
    if _exp is None:
        _exp = _cur

    # Botones como ítems de menú + resaltado del activo (sección y sub).
    # ⚠️ Prefijo `navsec_`/`navsub_` (NO `nav_`): `[class*="st-key-nav_"]` también matchearía
    # `st-key-nav_back_btn` (el botón ← del topbar, v205) y lo restylearía.
    _css = ["<style>",
            '[class*="st-key-navsec_"] button,[class*="st-key-navsub_"] button{'
            'border:none!important;background:transparent!important;box-shadow:none!important;'
            'justify-content:flex-start!important;padding:5px 12px!important;min-height:0!important;}',
            '[class*="st-key-navsec_"] button p,[class*="st-key-navsub_"] button p{'
            'text-align:left!important;width:100%!important;}',
            '[class*="st-key-navsub_"] button{padding-left:26px!important;font-size:.85rem!important;}',
            # v232: el ICONO Material (único <span> del <p>) en azul COPEX; el texto, por defecto.
            '[class*="st-key-navsec_"] button p span,[class*="st-key-navsub_"] button p span{'
            'color:#2e6da4!important;}',
            # sección ACTIVA: highlight + azul oscuro (texto e icono).
            f'.st-key-navsec_{_cur} button{{background:#e8eef6!important;color:#1e4e79!important;'
            'font-weight:600!important;border-radius:8px!important;}',
            f'.st-key-navsec_{_cur} button p span{{color:#1e4e79!important;}}']
    # La sub activa solo se resalta si la sección activa es además la desplegada.
    if _exp == _cur and _cur in _SUBS:
        _sk, _subs = _SUBS[_cur]
        _cursub = st.session_state.get(_sk) or _subs[0][0]
        _idx_sub = next((_i for _i, (_sid, _d) in enumerate(_subs) if _sid == _cursub), None)
        if _idx_sub is not None:
            _css.append(f'.st-key-navsub_{_cur}_{_idx_sub} button{{'
                        'background:#e8eef6!important;color:#1e4e79!important;'
                        'font-weight:600!important;border-radius:8px!important;}'
                        f'.st-key-navsub_{_cur}_{_idx_sub} button p span'
                        '{color:#1e4e79!important;}')
    _css.append("</style>")
    st.markdown("".join(_css), unsafe_allow_html=True)

    st.markdown("###### NAVEGACIÓN")
    for _k, _lbl in _SECS:
        _has = _k in _SUBS
        _open = _has and _k == _exp
        _mark = ("  ▾" if _open else ("  ▸" if _has else ""))
        if st.button(_lbl + _mark, key=f"navsec_{_k}", use_container_width=True):
            if _has:
                # v230: SOLO desplegar/plegar; NO navegar → no se carga el contenido de la
                # sub-pestaña hasta que se toca una hija (evita "abrir todo de una vez").
                st.session_state["_admin_expanded"] = ("" if _open else _k)
                st.rerun()
            else:
                st.session_state["_admin_expanded"] = _k    # sin hijas → navega directo
                navegar(_k)
        if _open:                              # acordeón: solo la DESPLEGADA muestra sus hijas
            _sk, _subs = _SUBS[_k]
            for _i, (_sid, _sdisp) in enumerate(_subs):
                if st.button(_sdisp, key=f"navsub_{_k}_{_i}", use_container_width=True):
                    st.session_state["_admin_expanded"] = _k
                    navegar(_k, _sid)          # navega con el ID interno (deep-links intactos)
    _track_history(_cur)
    return _cur


# ── Barra superior (buscador + campana) ──────────────────────────
def _mobile_back_trap():
    """Atrapa el gesto/botón de retroceso del móvil (que CERRABA la app, al ser una sola
    página) y lo redirige al botón '← Atrás' interno (v205). Corre en el iframe del
    componente pero toca `window.parent` (mismo origen: sandbox con allow-same-origin).
    Mantiene una entrada de historial 'trampa' para que el back nunca salga de la app."""
    import streamlit.components.v1 as components
    components.html(
        "<script>(function(){try{var P=window.parent;if(P.__copexBack)return;"
        "P.__copexBack=true;P.history.pushState({c:1},'');"
        "P.addEventListener('popstate',function(){P.history.pushState({c:1},'');"
        "var b=P.document.querySelector('.st-key-nav_back_btn button');"
        "if(b&&!b.disabled){b.click();}});}catch(e){}})();</script>",
        height=0)


def render_topbar(grupo):
    # v201: la cabecera negra de Streamlit + el hueco superior quitaban espacio en la
    # vista del admin. La hacemos transparente (sin ocultarla, para no perder el botón
    # de desplegar el sidebar) y reducimos el padding superior del contenido.
    # v303: el padding era 2.4rem y se veía como una franja en blanco sobre el
    # buscador. Lo que tapaba la cabecera oscura es la regla de al lado
    # (`background:transparent`), no el hueco → 2.4rem → 1rem.
    st.markdown("<style>header[data-testid='stHeader']{background:transparent;}"
                "div.block-container{padding-top:1rem !important;}</style>",
                unsafe_allow_html=True)
    cback, c1, cver, c2 = st.columns([1, 7, 1.4, 1])
    with cback:
        if st.button("←", key="nav_back_btn", help="Volver atrás",
                     use_container_width=True, disabled=not puede_atras()):
            ir_atras()
    with c1:
        # El buscador aún no tiene backend; para el CAMPO además sería ruido (su nav
        # es corta y todo lo suyo cuelga de "Mis proyectos"). Solo gestión.
        if _rol() != "campo":
            st.text_input("Buscar", key="topbar_search", label_visibility="collapsed",
                          placeholder="Buscar proyectos, personas, trabajos…")
    with cver:
        # v297: la versión vivía en la banda azul COPEX de la nav vieja. Esa banda no
        # vuelve (el admin lleva sin ella desde v190 y no se echó en falta), pero la
        # versión sí: se usa a diario para saber qué hay desplegado.
        st.markdown(f"<div style='text-align:right;padding-top:8px;font-size:.78rem;"
                    f"color:#9aa7b8;font-family:monospace'>{_version()}</div>",
                    unsafe_allow_html=True)
    with c2:
        _campana(grupo)
    st.markdown("<hr style='margin:2px 0 14px 0;border:none;border-top:1px solid #e6e9ef;'>",
                unsafe_allow_html=True)
    _mobile_back_trap()      # el back del móvil hace lo mismo que el botón '←'


def _alertas(grupo) -> list:
    """Alertas para la campana. De momento: credenciales por vencer/vencidas del grupo.
    (Más fuentes —retrasos de proyecto, sobrepresupuesto— se sumarán después.)

    ⚠️ Para el CAMPO solo salen las SUYAS (v297): la lista del grupo son las
    credenciales de todos sus compañeros — dato de gestión, no suyo. Y el
    inventario (activos sin devolver, mantenimientos) es cosa del admin.
    """
    out = []
    _es_campo = (_rol() == "campo")
    _yo = str(st.session_state.get("auth", {}).get("usuario", "")).strip().lower()

    # ── PROPIETARIO (v298): no tiene UN grupo, así que se agrega por grupo ──
    # Reusa `owner_digest()` (v107, cacheado 60 s), que ya recorre todos los grupos:
    # no se inventa un recorrido nuevo ni se multiplican las lecturas de Sheets.
    if _rol() == "propietario":
        try:
            from core import admin_digest
            for g in admin_digest.owner_digest():
                _p = []
                if g["retrasos"]:
                    _p.append(f"{g['retrasos']} en retraso")
                if g["alarmas"]:
                    _p.append(f"{g['alarmas']} alarmas")
                if g["vencidos"]:
                    _p.append(f"{g['vencidos']} vencidos")
                if g["cred_venc"]:
                    _p.append(f"{g['cred_venc']} credenciales")
                if g["sobre_presupuesto"]:
                    _p.append(f"{g['sobre_presupuesto']} sobre presupuesto")
                if _p:
                    out.append(f":material/business: **{g['grupo']}** — " + " · ".join(_p))
        except Exception:
            pass
        return out
    try:
        from core import credentials as C
        if C.is_configured():
            for e in C.expiring(grupo)[:10]:
                if _es_campo and str(e.get("usuario", "")).strip().lower() != _yo:
                    continue
                est = ":red[:material/cancel:] vencida" if e["dias"] < 0 else f":orange[:material/schedule:] vence en {e['dias']} d"
                out.append(f":material/badge: {e['tipo']} · {e['usuario']} — {est}")
    except Exception:
        pass
    try:
        from core import inventory as INV
        if INV.is_configured() and not _es_campo:
            for e in INV.alertas(grupo)[:10]:
                if e["tipo"] == "mantenimiento":
                    out.append(f":material/build: {e['activo']} — "
                               f":red[mantenimiento vencido hace {e['dias']} d]")
                else:
                    out.append(f":material/inventory_2: {e['activo']} — "
                               f":red[no devuelto hace {e['dias']} d]"
                               + (f" ({e['usuario']})" if e.get("usuario") else ""))
    except Exception:
        pass
    return out


def _campana(grupo):
    try:
        alerts = _alertas(grupo)
    except Exception:
        alerts = []
    label = (f":material/notifications: {len(alerts)}" if alerts
             else ":material/notifications:")
    with st.popover(label, use_container_width=True):
        st.markdown(":material/notifications: **Alertas**")
        if not alerts:
            st.caption("Sin alertas por ahora.")
        for a in alerts:
            st.markdown(f"- {a}")


# ── Router de contenido ──────────────────────────────────────────
def render_admin_content(key, grupo):
    # ── Secciones propias del CAMPO (v297) ───────────────────────
    # Se cablean a las MISMAS funciones que ya usaba su nav vieja: es una
    # reconexión, no una reescritura (igual que hizo v191 con el admin).
    if key == "administracion":            # PROPIETARIO (v298)
        from core.auth_ui import render_owner_seccion
        render_owner_seccion(_sub_header("administracion"))
        return

    if key in ("misproyectos", "prestart", "credenciales", "colillas"):
        _usr = st.session_state.get("auth", {}).get("usuario", "")
        if key == "misproyectos":
            from core.projects_ui import render_field_projects
            render_field_projects(_usr, grupo)
        elif key == "prestart":
            from core.prestart_ui import render_prestart_tab
            render_prestart_tab()
        elif key == "credenciales":
            from core.auth_ui import render_my_credentials
            render_my_credentials()
        else:
            from core.payroll_ui import render_mis_colillas
            render_mis_colillas(_usr, grupo)
        return

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
        from core.inventory_ui import render_inventario
        render_inventario(grupo)
    elif key == "herramientas":
        _seccion_herramientas(grupo)
    elif key == "contactos":
        from core.clientes_ui import render_contactos
        render_contactos(grupo)
    else:
        # ⚠️ El fallback NO puede ser `render_home`: es del admin (KPIs del grupo,
        # mapa, agenda) y el campo no tiene esa sección. Cae a la PRIMERA de su rol.
        _prim = _secciones()[0][0]
        if _prim != key:
            render_admin_content(_prim, grupo)


def _sub_header(seccion):
    """Cabecera del contenido con la sub-pestaña ACTUAL. El selector de nivel 2 vive en el
    sidebar; esto solo da contexto. Devuelve el ID de la sub activa (default = la primera) y
    muestra su display con icono. Título = la label de la sección (de `_SECCIONES`). v232."""
    titulo = next((l for k, l in _secciones() if k == seccion), seccion)
    _sk, _subs = _subsecciones()[seccion]
    _ids = [_i for _i, _d in _subs]
    sub = st.session_state.get(_sk)
    if sub not in _ids:
        sub = _ids[0]
    _disp = next((_d for _i, _d in _subs if _i == sub), sub)
    st.markdown(f"## {titulo}  ·  {_disp}")
    st.markdown("---")
    return sub


def _seccion_planificacion(grupo):
    # v191: la gestión de usuarios vive aquí (decisión del usuario), junto al tablero.
    sub = _sub_header("planificacion")
    if sub == "🎛 Panel":
        from core import roster_ui
        roster_ui.render_planificacion(grupo)
    elif sub == "🗺 Ruta del día":
        from core import route_ui
        route_ui.render_ruta_dia(grupo)
    else:
        from core.auth_ui import _grupo_usuarios
        _grupo_usuarios(grupo)


def _seccion_proyectos(grupo):
    from core import projects_ui as PU
    sub = _sub_header("proyectos")
    if sub == "📊 Proyectos":
        PU._panel_proyectos(grupo)
    else:
        PU._panel_agrupaciones(grupo)


def _seccion_finanzas(grupo):
    from core import projects_ui as PU
    sub = _sub_header("finanzas")
    if sub == "📊 Resumen":
        PU.render_pnl(grupo)
    elif sub == "💰 Gastos":
        PU.render_group_expenses(grupo)
    elif sub == "🧾 Facturas":
        from core.invoices_ui import render_facturas
        render_facturas(grupo)
    elif sub == "👥 Nóminas":
        from core.payroll_ui import render_nominas
        render_nominas(grupo)
    elif sub == "📈 Rentabilidad":
        PU.render_group_profitability(grupo)
    else:
        PU.render_group_hours(grupo)


def _hub_herramientas():
    """Hub/entrada de Herramientas (v231): una tarjeta por herramienta (qué hace + Abrir).
    «Abrir» navega a la sub-pestaña de esa herramienta."""
    st.caption("Elige una herramienta:")
    _desc = {
        "📐 Survey": "Posicionamiento del hueco y matriz de solución; genera los informes "
                     "del cliente y de obra.",
        "🔩 Plomada": "Líneas de plomada y replanteo; distancias de verificación en obra.",
        "✂️ Rieles": "Cuánto cortar de cada riel de guía (Caso 1 / Caso 2).",
        "🛡 Buffers": "Cuánto cortar de cada buffer (HKP − HKPR).",
        "🎗 Belting": "Altura a la que dejar la cabina para instalar los belts (DSTS).",
        "🦺 Pre-Start": "Charla diaria de seguridad de obra (Daily Pre-Start).",
    }
    # display (icono) desde _SUBSECCIONES (consistente con el sidebar); navega con el ID.
    _herr = [(_id, _d) for _id, _d in _subsecciones()["herramientas"][1] if _id != "🧰 Inicio"]
    for _r in range(0, len(_herr), 3):
        _cols = st.columns(3, gap="medium")
        for _j in range(3):
            _i = _r + _j
            if _i >= len(_herr):
                break
            _id, _dispv = _herr[_i]
            with _cols[_j].container(border=True):
                st.markdown(f"#### {_dispv}")
                st.caption(_desc.get(_id, ""))
                if st.button("Abrir →", key=f"hubherr_{_i}", use_container_width=True):
                    navegar("herramientas", _id)


def _seccion_herramientas(grupo):
    rol = st.session_state.get("auth", {}).get("rol", "administrador")
    sub = _sub_header("herramientas")
    if sub == "🧰 Inicio":
        _hub_herramientas()
    elif sub == "📐 Survey":
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
    st.info(":material/construction: **En construcción** — este apartado se está rediseñando."
            + (f"\n\n{desc}" if desc else ""))


# ── HOME ─────────────────────────────────────────────────────────
def render_home(grupo):
    # v192: el "Centro de control del grupo" (KPIs + resumen del día) vivía en la
    # cabecera de "Mi grupo"; al reorganizar la nav quedó sin sitio → se reubica aquí,
    # que es la nueva landing. Reusa la función tal cual (no se duplica lógica).
    # v303: TRES columnas en vez de [3, 2] + toggle. El toggle (v203) obligaba a
    # elegir entre proyectos Y agenda, y lo elegido quedaba en el 40% del ancho:
    # de ahí venía lo de "arrinconados", y el ancho sobrante de ahí venía lo de
    # "vacía". La interfaz del admin es de PC (decisión del usuario), así que el
    # único contra —que en móvil las 3 columnas se apilan— no aplica aquí.
    from core import projects_ui as PU
    PU.render_group_header(grupo)
    col_map, col_pro, col_ag = st.columns([2, 1.5, 1.5], gap="large")
    with col_map:
        PU.render_kpis(grupo)          # los 3 KPIs son la cabecera de esta columna
        st.markdown("#### :material/map: Proyectos activos")
        _mapa_proyectos(grupo)
    with col_pro:
        st.markdown("#### :material/folder: Proyectos")
        _proyectos_home(grupo)
    with col_ag:
        st.markdown("#### :material/list: Agenda de hoy")
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
            st.caption(":material/place: Toca un pin para abrir el proyecto.")
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
                        # v206: el pin abre el RESUMEN del proyecto en la columna de
                        # Proyectos, sin salir de HOME. El "ver completo" va dentro.
                        # v303: ya no hay que cambiar de pestaña — esa columna está
                        # siempre a la vista, así que `home_right_view` desaparece.
                        st.session_state["_home_proj_sel"] = _best["pid"]
                        st.rerun()
        except Exception:
            st.map(pd.DataFrame(filas), latitude="lat", longitude="lon",
                   color="#c0392b", size=80)
            st.caption(":material/place: " + "  ·  ".join(f["nombre"] for f in filas))
    else:
        st.info("Ninguno de los proyectos en ejecución tiene ubicación todavía. "
                "Fíjala editando el proyecto → :material/map: Ubicación en el mapa.")
    if sin_ubic:
        st.caption(":orange[:material/warning:] Sin ubicación en el mapa: " + ", ".join(sin_ubic))


# ── Proyectos (vista compacta de HOME) ───────────────────────────
def _resumen_proyecto_home(grupo, pid):
    """Resumen de UN proyecto en la columna derecha de HOME (v206): datos clave + botón
    para ir al proyecto completo. Se abre al tocar un pin del mapa o un proyecto de la lista."""
    from core import projects as P
    from core import alerts
    if st.button("← Volver a la lista", key="hpr_back"):
        st.session_state.pop("_home_proj_sel", None)
        st.rerun()
    prj = next((p for p in P.list_projects(grupo, incluir_archivados=True)
                if str(p.get("ID", "")) == str(pid)), None)
    if not prj:
        st.warning("Proyecto no encontrado.")
        return
    av = max(0, min(100, int(P._num(prj.get("Avance")))))
    try:
        dl = P.delays_of_group(grupo).get(str(pid), 0)
        ah = P.aheads_of_group(grupo).get(str(pid), 0)
        al = (alerts.open_counts_all() if alerts.is_configured() else {}).get(str(pid), 0)
    except Exception:
        dl = ah = al = 0
    _sem = ":red[:material/cancel:]" if dl else (":green[:material/check_circle:]" if ah else ":orange[:material/schedule:]")
    _bar = "#c0392b" if dl else ("#1e8449" if ah else "#2e6da4")

    def _e(s):
        return str(s or "").replace("&", "&amp;").replace("<", "&lt;")

    st.markdown(f"### {_e(prj.get('Nombre'))}")
    st.markdown(
        f"<div style='background:#f0f2f5;border-radius:8px;height:14px;overflow:hidden;"
        f"margin:2px 0 8px;'><div style='background:{_bar};height:100%;width:{av}%;'></div></div>",
        unsafe_allow_html=True)
    bits = [f":material/bar_chart: **{av}%**", f"{_sem} {_e(prj.get('Estado'))}"]
    if prj.get("Cliente"):
        bits.append(f":material/business: {_e(prj.get('Cliente'))}")
    if dl:
        bits.append(f":red[:material/schedule:] {dl} d de retraso")
    elif ah:
        bits.append(f":green[:material/schedule:] {ah} d de adelanto")
    if al:
        bits.append(f":material/notifications: {al} alarma(s)")
    st.markdown("  ·  ".join(bits))
    _fi = str(prj.get("FechaInicio", "") or "—")
    _ff = str(prj.get("FechaFinEst", "") or "—")
    st.caption(f":material/calendar_month: {_fi} → {_ff}" + (f"  ·  :material/elevator: {_e(prj.get('NS'))} paradas" if prj.get("NS") else ""))
    _asg = [x.strip() for x in str(prj.get("CampoAsignados", "")).split(";") if x.strip()]
    if _asg:
        st.caption(f":material/engineering: {', '.join(_asg[:6])}")
    _ub = str(prj.get("Ubicacion", "") or "")
    if _ub:
        try:
            from core import maps
            st.markdown(":material/place: " + maps.maps_link_md(_ub))
        except Exception:
            st.caption(f":material/place: {_ub}")
    st.markdown("")
    if st.button("→ Ver proyecto completo", key="hpr_full", type="primary",
                 use_container_width=True):
        st.session_state.pop("_home_proj_sel", None)
        st.session_state["_prjsel_pending"] = str(pid)
        navegar("proyectos", "📊 Proyectos")


def _proyectos_home(grupo):
    """Datos importantes de los proyectos activos, compacto y clickeable (v203). Al tocar
    un proyecto (o un pin del mapa) se abre su RESUMEN aquí mismo (v206), con botón para ir
    al proyecto completo. Ordenados por urgencia."""
    if st.session_state.get("_home_proj_sel"):
        _resumen_proyecto_home(grupo, str(st.session_state["_home_proj_sel"]))
        return
    from core import projects as P
    from core import alerts
    _ACTIVOS = ("Planificado", "En progreso")
    try:
        proys = [p for p in P.list_projects(grupo) if str(p.get("Estado", "")) in _ACTIVOS]
    except Exception:
        proys = []
    if not proys:
        st.info("No hay proyectos activos ahora mismo.")
        return
    try:
        delays = P.delays_of_group(grupo)
        aheads = P.aheads_of_group(grupo)
        alarmas = alerts.open_counts_all() if alerts.is_configured() else {}
    except Exception:
        delays, aheads, alarmas = {}, {}, {}

    # urgencia: primero los de más retraso, luego más alarmas, luego menor avance
    def _urg(p):
        _pid = str(p.get("ID", ""))
        return (-delays.get(_pid, 0), -alarmas.get(_pid, 0), P._num(p.get("Avance")))
    proys.sort(key=_urg)

    st.caption(f"{len(proys)} activo(s) · ordenados por urgencia")
    _css = ["<style>"]
    for _i, p in enumerate(proys):
        _pid = str(p.get("ID", ""))
        _av = max(0, min(100, int(P._num(p.get("Avance")))))
        _dl, _ah = delays.get(_pid, 0), aheads.get(_pid, 0)
        _col = "#c0392b" if _dl else ("#1e8449" if _ah else "#2e6da4")
        _tint = "#fdecec" if _dl else ("#e8f5ee" if _ah else "#e8eef6")
        _css.append(
            f".st-key-hp_{_i} button{{background:linear-gradient(to right,"
            f"{_tint} {_av}%, #f4f6f9 {_av}%)!important;border-left:4px solid {_col}!important;"
            "justify-content:flex-start!important;text-align:left!important;}")
    _css.append("</style>")
    st.markdown("".join(_css), unsafe_allow_html=True)

    for _i, p in enumerate(proys):
        _pid = str(p.get("ID", ""))
        _av = max(0, min(100, int(P._num(p.get("Avance")))))
        _dl, _ah, _al = delays.get(_pid, 0), aheads.get(_pid, 0), alarmas.get(_pid, 0)
        _extra = ""
        if _dl:
            _extra += f" · :material/schedule: {_dl}d"
        elif _ah:
            _extra += f" · :material/schedule: {_ah}d"
        if _al:
            _extra += f" · :material/notifications: {_al}"
        _lbl = f"{p.get('Nombre', '')} · {_av}%{_extra}"
        if st.button(_lbl, key=f"hp_{_i}", use_container_width=True):
            st.session_state["_home_proj_sel"] = _pid      # v206: abre el resumen aquí
            st.rerun()


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
        items = R.celda_items(sem, usr, dia)          # v277: varias por día, con franja
        asigs = [it["asig"] for it in items]
        nota = R.celda(sem, usr, dia).get("nota", "").strip()
        reales = [a for a in asigs if a not in R.ESTADOS]
        if reales:
            n_asig += 1
        elif "OFF" in asigs:
            n_off += 1
        elif "LEAVE" in asigs:
            n_leave += 1
        else:
            n_sin += 1
        _etqs = []
        for it in items:
            _fl = R.franja_label(it["ini"], it["fin"])
            _etqs.append(R.etiqueta_de(it["asig"], tidx) + (f" {_fl}" if _fl else ""))
        filas.append({
            "usuario": usr,
            "nombre": nombre,
            "etqs": _etqs,
            "color": R.color_de(asigs[0] if asigs else "", tidx),
            "nota": nota,
            "proys": [p for p in (pmap.get(R.proyecto_de(a, tidx), "") for a in asigs) if p],
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
        _etqs = " · ".join(x for x in f.get("etqs", []) if x)
        _lbl = f"{f['nombre']} · {_etqs or 'sin asignar'}"
        _hlp = " · ".join(list(f.get("proys", [])) + ([f["nota"]] if f.get("nota") else [])) or None
        if st.button(_lbl, key=f"agper_{_i}", use_container_width=True, help=_hlp):
            _u = f.get("usuario", "")
            _nom = f.get("nombre", "") or _u
            st.session_state["gp_fichasel"] = f"{_nom} ({_u})"   # pre-selecciona la persona
            navegar("planificacion", "👷 Usuarios")
