"""
Survey Analyzer — UI Streamlit.
Solo presentación: toda la lógica de cálculo vive en core/.
"""
import streamlit as st
import streamlit.components.v1 as components
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from core.chat_agent      import get_chat_response
from core                 import notify
from core.survey_ui       import init_state, render_survey_tab

try:
    # utf-8-sig elimina el BOM que agrega PowerShell al escribir VERSION
    APP_VERSION = open(os.path.join(os.path.dirname(__file__), "VERSION"),
                       encoding="utf-8-sig").read().strip()
except Exception:
    APP_VERSION = "v?"

# Favicon = ícono COPEX (lado servidor, reemplaza el ícono de Streamlit)
try:
    from PIL import Image
    _PAGE_ICON = Image.open(os.path.join(os.path.dirname(__file__), "static", "icon-192.png"))
except Exception:
    _PAGE_ICON = "📐"

st.set_page_config(page_title=f"COPEX Survey Analyzer {APP_VERSION}",
                   layout="wide", page_icon=_PAGE_ICON)

# ══════════════════════════════════════════════════════
# OPTIMIZACIÓN MÓVIL (CSS responsive)
# ══════════════════════════════════════════════════════
st.markdown("""
<style>
/* En móvil: apilar columnas verticalmente (Streamlit no lo hace solo) */
@media (max-width: 640px) {
  div[data-testid="stHorizontalBlock"] {
    flex-wrap: wrap !important;
    gap: 0.35rem !important;
  }
  div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    min-width: 100% !important;
    flex: 1 1 100% !important;
  }
  /* Menos padding en pantalla pequeña → más espacio útil */
  .block-container {
    padding-top: 1rem !important;
    padding-left: 0.7rem !important;
    padding-right: 0.7rem !important;
  }
  /* Pestañas más compactas y con scroll horizontal si no caben */
  div[data-testid="stTabs"] button[data-baseweb="tab"] {
    padding: 0 10px !important;
    font-size: 0.85rem !important;
  }
  h1 { font-size: 1.4rem !important; }
  h2 { font-size: 1.2rem !important; }
  h3 { font-size: 1.05rem !important; }
  /* Botones más altos = más fáciles de tocar */
  div[data-testid="stButton"] button { min-height: 44px; }
}
/* Inputs con altura táctil cómoda en cualquier pantalla */
div[data-testid="stNumberInput"] input,
div[data-testid="stTextInput"] input { min-height: 40px; }
</style>
""", unsafe_allow_html=True)

# ── PWA: manifest + íconos + meta-tags (instalable con ícono COPEX) ──
components.html("""
<script>
try {
  var d = window.parent.document, h = d.head;
  var base = window.parent.location.origin + '/app/static/';
  function add(tag, attrs){ var e=d.createElement(tag); for(var k in attrs) e.setAttribute(k, attrs[k]); h.appendChild(e); }
  if(!d.querySelector('link[rel="manifest"]')){
    add('link', {rel:'manifest', href: base + 'manifest.webmanifest'});
    add('link', {rel:'apple-touch-icon', href: base + 'icon-192.png'});
    add('link', {rel:'icon', type:'image/png', sizes:'512x512', href: base + 'icon-512.png'});
    add('meta', {name:'apple-mobile-web-app-capable', content:'yes'});
    add('meta', {name:'mobile-web-app-capable', content:'yes'});
    add('meta', {name:'apple-mobile-web-app-status-bar-style', content:'black-translucent'});
    add('meta', {name:'apple-mobile-web-app-title', content:'COPEX'});
    add('meta', {name:'theme-color', content:'#1a3a5c'});
  }
} catch(e) {}
</script>
""", height=0)




# Agrupación de los parámetros del plano por significado (en vez de una grilla plana
# de 17 números iguales). Lo que no esté aquí se muestra igual, bajo "Otros".

# ══════════════════════════════════════════════════════
# INICIALIZACIÓN DE STATE
# ══════════════════════════════════════════════════════

init_state()

# ══════════════════════════════════════════════════════
# LOGIN — barrera de acceso
# ══════════════════════════════════════════════════════
from core.auth_ui import render_login, render_user_bar, render_owner_panel, render_group_panel
from core.auth import heartbeat, get_user

if not render_login():
    st.stop()

_ROL   = st.session_state.auth["rol"]
_GRUPO = st.session_state.auth.get("grupo", "")

# ── Sesión única: heartbeat (throttled) + expulsión si otro toma la cuenta ──
import time as _time
if _time.time() - st.session_state.get("_hb_last", 0) > 50:
    st.session_state["_hb_last"] = _time.time()
    _a = st.session_state.auth
    if not heartbeat(_a.get("usuario", ""), _a.get("token", "")):
        st.session_state.pop("auth", None)
        st.warning(":material/lock: Tu sesión se cerró: esta cuenta se abrió en otro dispositivo "
                   "(o expiró por inactividad). Vuelve a iniciar sesión.")
        st.stop()

# ── Avisos de vencimiento de credenciales (v187): al entrar, 1×/día/grupo ──
# Antes solo se disparaba al abrir el panel de usuarios de campo (frágil: si nadie
# lo abría, o el grupo no tenía admin, no se avisaba). Ahora corre al login de
# cualquier admin/propietario; el admin sobre su grupo, el propietario sobre todos.
# Deduplicado por día (session_state) y por 25 días en la hoja (UltimoAviso), y
# envuelto en try para no bloquear nunca la entrada.
if _ROL in ("administrador", "propietario"):
    try:
        from core import credentials as _cred, clock as _clk, auth as _auth
        if _cred.is_configured():
            _hoy = _clk.today()
            _grps = ([_GRUPO] if _ROL == "administrador"
                     else [g["Grupo"] for g in _auth.list_groups()])
            for _g in _grps:
                _kav = f"_credaviso_{_g}_{_hoy}"
                if _g and not st.session_state.get(_kav):
                    st.session_state[_kav] = True
                    _cred.notify_expiring(_g)
    except Exception:
        pass

# ── Contacto OBLIGATORIO para usuarios de campo (email + Telegram) ──
if _ROL == "campo" and not st.session_state.get("_contact_ok"):
    _rec = get_user(st.session_state.auth.get("usuario", ""))
    _has_mail = bool(str(_rec.get("Email", "")).strip())
    _has_tg   = bool(str(_rec.get("TelegramChatID", "")).strip())
    if _has_mail and _has_tg:
        st.session_state["_contact_ok"] = True
    else:
        st.markdown("### :material/lock: Falta configurar tu contacto")
        st.warning("Tu cuenta de campo necesita **email y Telegram** para usar la app. "
                   "El **email** lo carga tu administrador.")
        _pend = ([] if _has_mail else [":material/mail: Email (lo carga tu administrador)"]) + \
                ([] if _has_tg else [":material/send: Telegram"])
        st.info("Pendiente: " + "  ·  ".join(_pend))
        if not _has_tg and notify.telegram_configured() and notify.bot_username():
            import re as _re
            _bot  = notify.bot_username()
            _code = _re.sub(r"[^A-Za-z0-9_-]", "", st.session_state.auth.get("usuario", "")) or "user"
            st.markdown(f"**Tu único paso:** abre el bot y pulsa **Start** → "
                        f"[t.me/{_bot}](https://t.me/{_bot}?start={_code})")
            st.caption("Después, tu administrador te vincula. Recarga cuando esté listo.")
        if st.button(":material/sync: Ya está listo — revisar"):
            st.rerun()
        st.stop()

# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════
with st.sidebar:
    # ── Cabecera COPEX ─────────────────────────────────
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1a3a5c,#2e6da4);
                padding:14px 16px;border-radius:8px;margin-bottom:12px;">
        <div style="color:white;font-size:1.7rem;font-weight:900;
                    letter-spacing:0.18em;font-family:'Segoe UI',sans-serif;
                    line-height:1.1;">COPEX</div>
        <div style="color:#b0c8e8;font-size:0.72rem;margin-top:2px;">
            Elevator Survey Analyzer &nbsp;·&nbsp; {APP_VERSION}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Usuario logueado ────────────────────────────────
    render_user_bar()
    st.markdown("---")

    # ── Cronómetro de fichaje EN VIVO (v202): admin y campo, solo si estás fichado ──
    if _ROL in ("administrador", "campo"):
        from core.timeclock_ui import render_sidebar_chrono
        render_sidebar_chrono()

    # ── Navegación del admin (nueva UI, v190) ──
    if _ROL == "administrador":
        from core import home_ui as _home
        st.session_state["_admin_sec"] = _home.sidebar_menu()
        st.markdown("---")

    # ══════════════════════════════════════════════════
    # ASISTENTE IA — desplegable en sidebar
    # ══════════════════════════════════════════════════
    _agente_lbl = "Asistente de campo" if _ROL == "campo" else "Asistente de gestión"
    with st.expander(f":material/smart_toy: {_agente_lbl} COPEX", expanded=False):
        ctx_label = ":material/link: Con contexto del cálculo actual." if st.session_state.get("calc_results") else "Sin cálculo activo."
        _foco = ("Enfocado en la instalación en obra y el uso de la app en terreno."
                 if _ROL == "campo"
                 else "Enfocado en la gestión de proyectos e interpretación de resultados.")
        st.caption(f"{_foco} {ctx_label}")

        # Historial
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"],
                                 avatar="🧑‍🔧" if msg["role"] == "user" else "🤖"):
                st.markdown(msg["content"])

        # Input
        if prompt := st.chat_input("Escribe tu pregunta…", key="sidebar_chat_input"):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="🧑‍🔧"):
                st.markdown(prompt)
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Consultando…"):
                    _r = st.session_state.get("calc_results")
                    _response = get_chat_response(
                        user_message = prompt,
                        history      = st.session_state.chat_history[:-1],
                        calc_results = _r,
                        all_params   = _r["all_params"] if _r else None,
                        rol          = _ROL,
                        grupo        = _GRUPO,
                    )
                st.markdown(_response)
            st.session_state.chat_history.append({"role": "assistant", "content": _response})

        # Limpiar
        if st.session_state.chat_history:
            if st.button(":material/delete: Limpiar conversación", use_container_width=True, key="clear_chat_sb"):
                st.session_state.chat_history = []
                st.rerun()

# ══════════════════════════════════════════════════════
# ADMIN — nueva navegación (shell): top bar + contenido por sección (v190)
# Solo el administrador; owner/campo siguen con la cabecera + nav de abajo.
# ══════════════════════════════════════════════════════
if _ROL == "administrador":
    from core import home_ui as _home
    _home.render_topbar(_GRUPO)
    _home.render_admin_content(st.session_state.get("_admin_sec", "home"), _GRUPO)
    st.stop()

# ══════════════════════════════════════════════════════
# CABECERA PRINCIPAL
# ══════════════════════════════════════════════════════
st.markdown(f"""
<div style="background:linear-gradient(135deg,#1a3a5c 0%,#2e6da4 100%);
            padding:clamp(14px,4vw,22px) clamp(16px,5vw,32px);border-radius:12px;
            margin-bottom:20px;display:flex;justify-content:space-between;
            align-items:center;gap:12px;flex-wrap:wrap;">
    <div style="min-width:0;">
        <div style="color:white;font-size:clamp(1.6rem,7vw,2.4rem);font-weight:900;
                    letter-spacing:0.18em;font-family:'Segoe UI',sans-serif;
                    line-height:1.0;">COPEX</div>
        <div style="color:#b0c8e8;font-size:clamp(0.8rem,3vw,1rem);margin-top:4px;font-weight:400;">
            Elevator Survey Analyzer
        </div>
    </div>
    <div style="text-align:right;">
        <div style="color:#b0c8e8;font-size:0.75rem;">Versión</div>
        <div style="color:white;font-size:clamp(1.1rem,4vw,1.4rem);font-weight:700;
                    font-family:'Courier New',monospace;">{APP_VERSION}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Navegación con selector (NO st.tabs → evita el bug de mezcla de contenido).
# Solo se renderiza la sección seleccionada; no hay paneles ocultos que se filtren.
_L_SURVEY = "📐 Survey de elevador"
_L_PLUMB  = "🔩 Líneas de plomada"
_L_RAIL   = "✂️ Corte de rieles"
_L_BUFFER = "🛡 Corte de buffers"
_L_BELT   = "🎗 Belting"
_L_PRESTART = "🦺 Pre-Start diario"
_L_CLOCK  = "⏱ Fichaje"
_L_OWNER  = "👑 Administración"
_L_GRUPO  = "🛠 Mi grupo"
_L_FIELDPROJ = "📋 Mis proyectos"
_L_MYCRED    = "🎫 Mis credenciales"
_L_MYPAY     = "🧾 Mis colillas"

# Orden de las pestañas por rol (el panel de cada rol va primero).
# Las 5 HERRAMIENTAS TÉCNICAS van juntas; el Survey es una más (la más potente),
# no un caso aparte. El Pre-Start NO es una herramienta técnica: es un formato de
# SEGURIDAD de obra, así que va con lo operativo (fichaje/proyectos), no con ellas.
_HERR = [_L_SURVEY, _L_PLUMB, _L_RAIL, _L_BUFFER, _L_BELT]   # herramientas técnicas
if _ROL == "propietario":
    _nav = [_L_OWNER, _L_PRESTART] + _HERR          # sin fichaje
elif _ROL == "administrador":
    _nav = [_L_GRUPO, _L_CLOCK, _L_PRESTART] + _HERR
elif _ROL == "campo":
    _nav = [_L_FIELDPROJ, _L_CLOCK, _L_PRESTART] + _HERR + [_L_MYCRED, _L_MYPAY]
else:
    _nav = [_L_PRESTART] + _HERR + [_L_CLOCK]

# Navegación pendiente (p.ej. "abrir el proyecto recién creado" desde el Survey).
# Se aplica ANTES de instanciar el radio: escribir la clave de un widget ya
# creado lanza excepción (misma regla que el import de Excel, v111).
_np = st.session_state.pop("_nav_pending", None)
if _np in _nav:
    st.session_state["main_nav"] = _np

_NAV_DISPLAY = {
    _L_SURVEY: ":material/architecture: Survey de elevador",
    _L_PLUMB:  ":material/straighten: Líneas de plomada",
    _L_RAIL:   ":material/content_cut: Corte de rieles",
    _L_BUFFER: ":material/shield: Corte de buffers",
    _L_BELT:   ":material/swap_vert: Belting",
    _L_PRESTART: ":material/health_and_safety: Pre-Start diario",
    _L_CLOCK:  ":material/schedule: Fichaje",
    _L_OWNER:  ":material/shield_person: Administración",
    _L_GRUPO:  ":material/build: Mi grupo",
    _L_FIELDPROJ: ":material/assignment: Mis proyectos",
    _L_MYCRED: ":material/badge: Mis credenciales",
    _L_MYPAY: ":material/payments: Mis colillas",
}
_seccion = st.radio("Navegación", _nav, horizontal=True,
                    format_func=lambda o: _NAV_DISPLAY.get(o, o),
                    key="main_nav", label_visibility="collapsed")
st.markdown("---")

if _seccion == _L_SURVEY:

    # ── Aplicar valores importados (Excel) ANTES de crear los widgets ──
    # Streamlit prohíbe escribir st.session_state[k] de un widget ya instanciado,
    # así que el import deja los valores "pendientes" y se aplican aquí, arriba del todo.
    # ⚠️ Streamlit DESCARTA el estado de un widget que no se renderiza en el rerun.
    # Como el Survey está en 2 fases, al pasar a "Resultados" los parámetros, el NS y
    # la configuración (que solo se dibujan en "Datos") se perderían. Re-asignarlos aquí
    # —antes de crear ningún widget— los mantiene vivos entre fases.
    render_survey_tab(_ROL, _GRUPO)


elif _seccion == _L_PLUMB:
    from core.plumb_ui import render_plumb_tab
    render_plumb_tab()

elif _seccion == _L_RAIL:
    from core.rail_cut_ui import render_rail_cut_tab
    render_rail_cut_tab()

elif _seccion == _L_BUFFER:
    from core.buffer_cut_ui import render_buffer_cut_tab
    render_buffer_cut_tab()

elif _seccion == _L_BELT:
    from core.belting_ui import render_belting_tab
    render_belting_tab()

elif _seccion == _L_PRESTART:
    from core.prestart_ui import render_prestart_tab
    render_prestart_tab()

elif _seccion == _L_CLOCK:
    from core.timeclock_ui import render_timeclock_tab
    render_timeclock_tab()

elif _seccion == _L_FIELDPROJ:
    from core.projects_ui import render_field_projects
    render_field_projects(st.session_state.auth.get("usuario", ""), _GRUPO)

elif _seccion == _L_MYCRED:
    from core.auth_ui import render_my_credentials
    render_my_credentials()

elif _seccion == _L_MYPAY:
    from core.payroll_ui import render_mis_colillas
    render_mis_colillas(st.session_state.auth.get("usuario", ""), _GRUPO)

elif _seccion == _L_OWNER:
    render_owner_panel()

elif _seccion == _L_GRUPO:
    render_group_panel(_GRUPO)
