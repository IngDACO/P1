"""
Survey Analyzer — UI Streamlit.
Solo presentación: toda la lógica de cálculo vive en core/.
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# ⚠️ v536 · Un despliegue nuevo SIN los módulos viejos en memoria. El Cloud vuelve a
# ejecutar este `app.py` en cada pasada, pero los `core.*` ya importados se quedan como
# estaban: al desplegar v535, este archivo llamó a `estado_vivo.de_la_cuenta` —nueva— sobre
# el `estado_vivo` de v534 que seguía en memoria, y la app entera dio `AttributeError` hasta
# que se reinició a mano (CLAUDE.md lo avisaba como «Settings → Reboot app»; esta vez la
# dejó caída). Ahora: si la versión del disco no es con la que se importaron los módulos,
# se descartan TODOS los de la app y se vuelven a importar en esta misma pasada.
try:
    _V_DISCO = open(os.path.join(os.path.dirname(__file__), "VERSION"),
                    encoding="utf-8-sig").read().strip()
except Exception:
    _V_DISCO = "v?"
if "core" in sys.modules and getattr(sys.modules["core"], "_VERSION_CARGADA", None) != _V_DISCO:
    for _m in [m for m in list(sys.modules)
               if m in ("core", "extractors") or m.startswith(("core.", "extractors."))]:
        sys.modules.pop(_m, None)
import core as _core_pkg                                  # noqa: E402
_core_pkg._VERSION_CARGADA = _V_DISCO

from core import incrustar                                # noqa: E402

from core.i18n import t                                   # noqa: E402

from core.chat_agent      import get_chat_response
from core                 import notify
from core.survey_ui import init_state

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
# SISTEMA DE DISEÑO COPEX (v283) — antes que nada, para que TODA la app
# (incluido el login, la primera impresión) salga con la misma estética.
# ══════════════════════════════════════════════════════
from core import theme as _cpx_theme
_cpx_theme.inject()

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
    font-size:14px !important;
  }
  h1 { font-size:21px !important; }
  h2 { font-size:18px !important; }
  h3 { font-size:16px !important; }
  /* Botones más altos = más fáciles de tocar */
  div[data-testid="stButton"] button { min-height: 44px; }
}
/* Inputs con altura táctil cómoda en cualquier pantalla */
div[data-testid="stNumberInput"] input,
div[data-testid="stTextInput"] input { min-height: 40px; }
</style>
""", unsafe_allow_html=True)

# ── PWA: manifest + íconos + meta-tags (instalable con ícono COPEX) ──
incrustar.script("""
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
""")




# Agrupación de los parámetros del plano por significado (en vez de una grilla plana
# de 17 números iguales). Lo que no esté aquí se muestra igual, bajo "Otros".

# ══════════════════════════════════════════════════════
# INICIALIZACIÓN DE STATE
# ══════════════════════════════════════════════════════

init_state()

# ══════════════════════════════════════════════════════
# LOGIN — barrera de acceso
# ══════════════════════════════════════════════════════
from core.auth_ui import render_login, render_user_bar
from core.auth import heartbeat_en_fondo, heartbeat_olvidar, heartbeat_resultado, get_user

if not render_login():
    st.stop()

_ROL   = st.session_state.auth["rol"]
_GRUPO = st.session_state.auth.get("grupo", "")

# v534 · Lo tecleado en las herramientas sobrevive a cambiar de sección. Va en CADA pasada
# y antes de pintar nada: Streamlit borra el valor de un widget en cuanto una pasada no lo
# pinta (visto en producción: salir del Survey y volver dejaba los 23 parámetros a cero).
# ⚠️ Después del login, a propósito: en la pantalla de entrada no se conserva nada.
# ⚠️ Lo conservado es de UNA obra: si la herramienta vuelve con otra, se olvida (lo decide
# `plan_ui.selector_proyecto`, que es donde se sabe la obra).
from core import estado_vivo as _estado_vivo
# v535 · Los datos de trabajo son de UNA cuenta: si en esta pestaña entra otra, empieza
# limpia (antes, cerrar sesión solo quitaba la identidad y la siguiente cuenta veía los
# resultados y el historial del asistente de la anterior).
if _estado_vivo.de_la_cuenta(st.session_state.auth.get("usuario", "")):
    init_state()
_estado_vivo.pasada()


# Deep-link del QR del inventario: escanear `…?activo=ACT-####` abre esa ficha.
# Debe correr ANTES del sidebar (sidebar_menu aplica `_admin_nav_pending`). Solo
# el administrador tiene 📦 Inventario (nueva shell). Guard para no re-disparar.
if _ROL == "administrator":
    try:
        _scan = st.query_params.get("activo")
    except Exception:
        _scan = None
    if _scan and st.session_state.get("_scan_handled") != _scan:
        st.session_state["_scan_handled"] = _scan
        st.session_state["_admin_nav_pending"] = ("inventario", None)
        st.session_state["_inv_open"] = str(_scan)
        try:
            st.query_params.clear()
        except Exception:
            pass
        st.rerun()

# v488 · Vuelta desde Xero (`?code=&state=`): llega en una pestaña NUEVA, así que se
# procesa aquí, después del login y antes del sidebar, como el deep-link del QR. Solo
# importa `xero_ui` si la URL trae esos parámetros: el resto de pasadas no paga nada.
try:
    _xq = st.query_params
    _xero_vuelta = bool(_xq.get("state")) and bool(_xq.get("code") or _xq.get("error"))
except Exception:
    _xero_vuelta = False
if _xero_vuelta:
    from core import xero_ui as _xui
    _xui.procesar_retorno(_ROL, _GRUPO)

# ── Sesión única: heartbeat (throttled) + expulsión si otro toma la cuenta ──
# ⚠️ v528 · En SEGUNDO PLANO: la página ya no espera a que Google conteste (~1,9 s de clic
# parado cada 50 s, medido en producción). Se expulsa con lo que dijo el ÚLTIMO heartbeat
# que terminó, mirado en CADA pasada (cuesta un dict, 0 llamadas): así el aviso llega en
# la primera pasada después de que el hilo lo descubra, no 50 s más tarde.
import time as _time
_a = st.session_state.auth
if heartbeat_resultado(_a.get("usuario", ""), _a.get("token", "")) is False:
    # v533 · El veredicto se usa UNA vez: si se quedara guardado, una sesión restaurada
    # después con la misma cookie saldría expulsada sin volver a preguntar a la hoja.
    heartbeat_olvidar(_a.get("usuario", ""), _a.get("token", ""))
    st.session_state.pop("auth", None)
    st.warning(t(":material/lock: Your session was closed: this account was opened on another device (or it expired through inactivity). Sign in again."))
    st.stop()
if _time.time() - st.session_state.get("_hb_last", 0) > 50:
    st.session_state["_hb_last"] = _time.time()
    heartbeat_en_fondo(_a.get("usuario", ""), _a.get("token", ""))

# ── Avisos de vencimiento de credenciales (v187): al entrar, 1×/día/grupo ──
# Antes solo se disparaba al abrir el panel de usuarios de campo (frágil: si nadie
# lo abría, o el grupo no tenía admin, no se avisaba). Ahora corre al login de
# cualquier admin/propietario; el admin sobre su grupo, el propietario sobre todos.
# Deduplicado por día (session_state) y por 25 días en la hoja (UltimoAviso), y
# envuelto en try para no bloquear nunca la entrada.
if _ROL in ("administrator", "owner"):
    try:
        from core import credentials as _cred, clock as _clk, auth as _auth
        if _cred.is_configured():
            _hoy = _clk.today()
            _grps = ([_GRUPO] if _ROL == "administrator"
                     else [g["Group"] for g in _auth.list_groups()])
            for _g in _grps:
                _kav = f"_credaviso_{_g}_{_hoy}"
                if _g and not st.session_state.get(_kav):
                    st.session_state[_kav] = True
                    # ⚠️ v379: el propietario recorre TODOS los grupos y cada uno vive
                    # en su libro (v359); su sesión no tiene grupo, así que sin este
                    # ámbito las N vueltas leían las credenciales del maestro y no
                    # avisaba de ninguna. Para el admin resuelve a su mismo libro.
                    from core import tenant as _tnt
                    with _tnt.como_grupo(_g):
                        _cred.notify_expiring(_g)
    except Exception:
        pass

# ── Contacto obligatorio para usuarios de campo (v79) ────────────────
# ⚠️ v368: SOLO se exige un canal que EXISTA. Antes se pedían email **y** Telegram
# siempre, aunque el bot no estuviera en Secrets — y entonces el bloqueo no tenía
# salida por ningún lado: la pantalla no podía mostrar el link de Start (ese bloque
# está condicionado a `telegram_configured()`), y el admin tampoco tenía botón para
# vincular, porque su ficha muestra «Telegram no configurado». Resultado real: 7 de
# los 8 usuarios de campo del grupo encerrados fuera de la app, sin forma de entrar.
# Es el patrón de v325/v340 — un pendiente que NADIE puede cerrar es peor que no
# tenerlo: exigir un canal inexistente no protege nada, solo deja gente fuera.
if _ROL == "field" and not st.session_state.get("_contact_ok"):
    _rec = get_user(st.session_state.auth.get("usuario", ""))
    _has_mail = bool(str(_rec.get("Email", "")).strip())
    _has_tg   = bool(str(_rec.get("TelegramChatID", "")).strip())
    # ¿el canal Telegram existe en esta instalación?
    try:
        _tg_hay = bool(notify.telegram_configured() and notify.bot_username())
    except Exception:
        _tg_hay = False
    _falta_mail = not _has_mail
    _falta_tg   = _tg_hay and not _has_tg          # si no hay bot, no se exige

    if not _falta_mail and not _falta_tg:
        st.session_state["_contact_ok"] = True
    else:
        st.markdown(t("### :material/lock: Your contact details are missing"))
        # ⚠️ Se dice QUIÉN lo resuelve, no solo qué falta: el email no lo puede poner
        # el propio usuario (lo carga su administrador), así que un «pendiente: email»
        # a secas lo deja mirando una pared sin saber a quién pedírselo.
        if _falta_mail and _falta_tg:
            st.warning(t("Your account needs **email and Telegram**. The **email is entered by your administrator**; you link the Telegram yourself with the step below."))
        elif _falta_mail:
            st.warning(t("Your account needs an **email**, and your administrator enters it. Let them know and sign in again — you cannot set it from here."))
        else:
            st.warning(t("All that is left is linking your **Telegram**. That is your step, right below."))

        if _falta_tg:
            import re as _re
            _bot  = notify.bot_username()
            _code = _re.sub(r"[^A-Za-z0-9_-]", "", st.session_state.auth.get("usuario", "")) or "user"
            st.markdown(f"**Your step:** open the bot and press **Start** → "
                        f"[t.me/{_bot}](https://t.me/{_bot}?start={_code})")
            st.caption(t("Your administrator then links you from your record."))
        if st.button(t(":material/sync: It is done — check again")):
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
        <div style="color:white;font-size:26px;font-weight:900;
                    letter-spacing:0.18em;font-family:'Segoe UI',sans-serif;
                    line-height:1.1;">COPEX</div>
        <div style="color:#b0c8e8;font-size:12px;margin-top:2px;">
            Elevator Survey Analyzer &nbsp;·&nbsp; {APP_VERSION}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Usuario logueado ────────────────────────────────
    render_user_bar()
    st.markdown("---")

    # ── Cronómetro de fichaje EN VIVO (v202): admin y campo, solo si estás fichado ──
    if _ROL in ("administrator", "field"):
        from core.timeclock_ui import render_sidebar_chrono
        render_sidebar_chrono()

    # ── Menú de secciones (v299: para TODOS los roles) ──
    # `sidebar_menu` resuelve las secciones POR ROL internamente (home_ui._secciones).
    from core import home_ui as _home
    st.session_state["_admin_sec"] = _home.sidebar_menu()
    st.markdown("---")

    # ══════════════════════════════════════════════════
    # ASISTENTE IA — desplegable en sidebar
    # ══════════════════════════════════════════════════
    _agente_lbl = "Field assistant" if _ROL == "field" else "Management assistant"
    with st.expander(f":material/smart_toy: {_agente_lbl} COPEX", expanded=False):
        ctx_label = ":material/link: With the current calculation as context." if st.session_state.get("calc_results") else "No active calculation."
        _foco = ("Focused on installing on site and using the app in the field."
                 if _ROL == "field"
                 else "Focused on project management and interpreting results.")
        st.caption(f"{_foco} {ctx_label}")

        # Historial
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"],
                                 avatar="🧑‍🔧" if msg["role"] == "user" else "🤖"):
                st.markdown(msg["content"])

        # Input
        # v526 · Estaba en español y sin `t()` (visto en producción): el idioma base es el
        # inglés, y ningún barrido de i18n miraba `st.chat_input` (trampa nº30).
        if prompt := st.chat_input(t("Ask your question…"), key="sidebar_chat_input"):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="🧑‍🔧"):
                st.markdown(prompt)
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner(t("Searching…")):
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
            if st.button(t(":material/delete: Clear the conversation"), width="stretch", key="clear_chat_sb"):
                st.session_state.chat_history = []
                st.rerun()

# ══════════════════════════════════════════════════════
# CONTENIDO — shell única: top bar + la sección activa
# v190 admin · v297 campo · v298 propietario · v299 se borró la nav vieja
# (cabecera COPEX + radio `main_nav` + su if/elif de enrutado, 132 líneas).
# Ya NO es condicional: los tres roles pasan por aquí y `home_ui` resuelve sus
# secciones. Un rol desconocido cae a las del CAMPO (menor privilegio).
# ══════════════════════════════════════════════════════
from core import home_ui as _home
_home.render_topbar(_GRUPO)

# ── Aviso del Pre-Start tras fichar (v374) ────────────────────────
# ⚠️ Va AQUÍ, al top level del script, y NO dentro del `with st.sidebar:` de arriba:
# el modal se pinta en el contenedor activo, y así es como se verificó en vivo.
# Se dispara por bandera en la pasada SIGUIENTE al fichaje, porque el `st.rerun()`
# de la acción descarta los deltas de la suya (v365).
if _ROL in ("administrator", "field"):
    from core.timeclock_ui import aviso_prestart_pendiente
    aviso_prestart_pendiente(_GRUPO)
# El default NO puede ser "home" fijo: campo y propietario no tienen esa sección;
# `render_admin_content` cae a la primera del rol (v297).
_home.render_admin_content(st.session_state.get("_admin_sec", ""), _GRUPO)

# ══════════════════════════════════════════════════════
