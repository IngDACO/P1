"""
UI de login, barra de usuario y paneles de gestión (propietario / administrador).
"""
import os
import re
import time
import streamlit as st
import pandas as pd

from core import auth

_USER_COLS = ["Usuario", "Nombre", "Rol", "Grupo", "Activo", "Email"]  # tabla sin hash/tokens


def _field_contact_ui(campo_users, key_prefix="cc"):
    """Gestión de contacto OBLIGATORIO (email + Telegram) de usuarios de campo — solo admin/owner.
    El Telegram lo vincula el admin DESPUÉS de que el usuario pulse Start en el bot."""
    from core import notify
    if not campo_users:
        return
    faltan = [u["Usuario"] for u in campo_users
              if not (str(u.get("Email", "")).strip() and str(u.get("TelegramChatID", "")).strip())]
    with st.expander("📇 Contacto de campo (email + Telegram — OBLIGATORIO)", expanded=bool(faltan)):
        if faltan:
            st.warning("⚠️ Sin contacto completo (no pueden usar la app): " + ", ".join(faltan))
        sel = st.selectbox("Usuario de campo", [u["Usuario"] for u in campo_users],
                           key=f"{key_prefix}_sel")
        rec = auth.get_user(sel)
        em  = st.text_input("📧 Email", value=str(rec.get("Email", "")), key=f"{key_prefix}_em")
        if st.button("Guardar email", key=f"{key_prefix}_emb"):
            ok, msg = auth.set_contact(sel, email=em)
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()
        st.markdown("**📨 Telegram**")
        tg = str(rec.get("TelegramChatID", "")).strip()
        if not notify.telegram_configured() or not notify.bot_username():
            st.caption("Telegram no configurado (falta el bot en Secrets).")
        elif tg:
            st.success("✅ Telegram vinculado.")
            if st.button("Desvincular Telegram", key=f"{key_prefix}_tgu"):
                auth.set_contact(sel, telegram="")
                st.rerun()
        else:
            bot  = notify.bot_username()
            code = re.sub(r"[^A-Za-z0-9_-]", "", sel) or "user"
            st.caption("1) El usuario abre el bot y pulsa **Start** (envíale este link):")
            st.code(f"https://t.me/{bot}?start={code}")
            st.caption("2) Cuando lo haya hecho, pulsa:")
            if st.button("🔗 Vincular Telegram de este usuario", key=f"{key_prefix}_tgl"):
                cid = notify.telegram_find_chat_by_code(code)
                if cid:
                    auth.set_contact(sel, telegram=cid)
                    st.success("✅ Telegram vinculado.")
                    st.rerun()
                else:
                    st.error("No encontré su mensaje. Asegúrate de que pulsó Start y reintenta.")

_LOGO = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "icon-512.png")


def render_login() -> bool:
    """True si hay sesión iniciada. Si no, muestra el login y devuelve False."""
    if st.session_state.get("auth"):
        return True

    # ── Logo COPEX centrado ─────────────────────────────────
    c = st.columns([1, 1, 1])
    with c[1]:
        if os.path.exists(_LOGO):
            st.image(_LOGO, use_container_width=True)
        else:
            st.markdown("<h1 style='text-align:center;letter-spacing:.2em;color:#1a3a5c'>COPEX</h1>",
                        unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#888;margin-top:-8px'>Elevator Survey Analyzer</p>",
                unsafe_allow_html=True)

    if not auth.is_configured():
        st.error("🔒 El acceso no está conectado a Google Sheets. "
                 "Configura los Secrets (gcp_service_account + TIMECLOCK_SHEET_ID) en Streamlit Cloud.")
        return False

    try:
        first_run = not auth.has_any_user()
    except Exception:
        first_run = False

    mid = st.columns([1, 2, 1])[1]
    with mid:
        if first_run:
            st.info("👑 **Configuración inicial** — crea la cuenta de propietario.")
            u  = st.text_input("Usuario", key="setup_u")
            nm = st.text_input("Nombre", key="setup_n")
            p1 = st.text_input("Contraseña", type="password", key="setup_p1")
            p2 = st.text_input("Repetir contraseña", type="password", key="setup_p2")
            if st.button("Crear propietario", type="primary", use_container_width=True):
                if not u or not p1:
                    st.error("Completa usuario y contraseña.")
                elif p1 != p2:
                    st.error("Las contraseñas no coinciden.")
                else:
                    ok, msg = auth.add_user(u, p1, "propietario", nm)
                    if ok:
                        st.success(msg + "  Ahora inicia sesión.")
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.markdown("#### Iniciar sesión")
            u = st.text_input("Usuario", key="login_u")
            p = st.text_input("Contraseña", type="password", key="login_p")

            def _do_login(force=False):
                res = auth.verify_login(u, p)
                if not res.get("ok"):
                    st.error(res.get("error", "Error de autenticación."))
                    return
                if force:
                    auth.end_session(res["usuario"], None)   # cerrar la otra sesión
                ses_ok, tok = auth.start_session(res["usuario"])
                if not ses_ok:
                    st.session_state["_blocked_user"] = res["usuario"]
                    st.error(f"🔒 {tok}")
                    return
                st.session_state.pop("_blocked_user", None)
                st.session_state["auth"] = {
                    "usuario": res["usuario"], "rol": res["rol"],
                    "nombre": res["nombre"], "grupo": res.get("grupo", ""),
                    "token": tok,
                }
                st.session_state["_hb_last"] = time.time()
                st.rerun()

            if st.button("Iniciar sesión", type="primary", use_container_width=True):
                _do_login(force=False)

            if st.session_state.get("_blocked_user"):
                st.caption("Si eres **tú** y dejaste la sesión abierta en otro dispositivo, "
                           "puedes cerrarla e iniciar aquí.")
                if st.button("🔓 Cerrar la otra sesión e iniciar aquí",
                             use_container_width=True):
                    _do_login(force=True)
    return False


def render_user_bar():
    """Usuario logueado + grupo + botón salir (sidebar)."""
    a = st.session_state.get("auth", {})
    rol_lbl = {"propietario": "👑 Propietario", "administrador": "🛠 Administrador",
               "campo": "🔧 Campo"}.get(a.get("rol"), a.get("rol", ""))
    grupo = a.get("grupo") or ("todos" if a.get("rol") == "propietario" else "—")
    st.markdown(f"**{a.get('nombre','')}**  \n{rol_lbl}  \n🏢 {grupo}")
    if st.button("🚪 Cerrar sesión", use_container_width=True, key="logout_btn"):
        try:
            auth.end_session(a.get("usuario", ""), a.get("token"))   # libera la cuenta
        except Exception:
            pass
        if "auth" in st.session_state:
            del st.session_state["auth"]
        st.rerun()


# ════════════════════════════════════════════════════════════
# PANEL DEL PROPIETARIO — grupos + todos los usuarios
# ════════════════════════════════════════════════════════════
def _owner_grupos():
    grupos = auth.list_groups()
    if grupos:
        st.dataframe(pd.DataFrame(grupos), hide_index=True, use_container_width=True)
    else:
        st.info("Aún no hay grupos. Crea el primero abajo.")
    with st.form("form_grupo", clear_on_submit=True):
        gn = st.text_input("Nombre del grupo (empresa cliente)")
        gd = st.text_input("Descripción (opcional)")
        if st.form_submit_button("➕ Crear grupo"):
            ok, msg = auth.add_group(gn, gd)
            (st.success if ok else st.error)(msg)
            if ok: st.rerun()
    if grupos:
        gsel = st.selectbox("Eliminar grupo", [g["Grupo"] for g in grupos], key="del_g_sel")
        if st.button("🗑 Eliminar grupo", key="del_g_btn"):
            ok, msg = auth.delete_group(gsel)
            (st.success if ok else st.error)(msg)
            if ok: st.rerun()


def _owner_usuarios():
    users = auth.list_users()
    if users:
        _df   = pd.DataFrame(users)
        _cols = [c for c in _USER_COLS if c in _df.columns]
        st.dataframe(_df[_cols] if _cols else _df, hide_index=True, use_container_width=True)
    grupo_opts = [""] + [g["Grupo"] for g in auth.list_groups()]

    with st.expander("➕ Crear usuario"):
        with st.form("form_user", clear_on_submit=True):
            u  = st.text_input("Usuario")
            nm = st.text_input("Nombre")
            rl = st.selectbox("Rol", auth.ROLES)
            gr = st.selectbox("Grupo", grupo_opts,
                              help="Propietario puede ir sin grupo; admin y campo requieren grupo.")
            pw = st.text_input("Contraseña", type="password")
            em = st.text_input("📧 Email (obligatorio para campo)")
            if st.form_submit_button("Crear usuario"):
                if rl == "campo" and not em.strip():
                    st.error("El email es obligatorio para usuarios de campo.")
                else:
                    ok, msg = auth.add_user(u, pw, rl, nm, gr)
                    if ok and em.strip():
                        auth.set_contact(u, email=em)
                    (st.success if ok else st.error)(msg)
                    if ok: st.rerun()

    _campo = [x for x in users if str(x.get("Rol", "")).lower() == "campo"]
    _field_contact_ui(_campo, key_prefix="ow_cc")

    if users:
        with st.expander("🔑 Modificar usuario"):
            sel = st.selectbox("Usuario", [x["Usuario"] for x in users], key="ow_sel")
            np_ = st.text_input("Nueva contraseña", type="password", key="ow_np")
            if st.button("Cambiar contraseña", key="ow_chp"):
                if np_:
                    ok, msg = auth.set_password(sel, np_); (st.success if ok else st.error)(msg)
                else:
                    st.warning("Ingresa la contraseña.")
            cr1, cr2 = st.columns(2)
            nr = cr1.selectbox("Rol", auth.ROLES, key="ow_nr")
            if cr1.button("Aplicar rol", key="ow_chr"):
                ok, msg = auth.set_role(sel, nr); (st.success if ok else st.error)(msg); st.rerun()
            ng = cr2.selectbox("Grupo", grupo_opts, key="ow_ng")
            if cr2.button("Aplicar grupo", key="ow_chg"):
                ok, msg = auth.set_group(sel, ng); (st.success if ok else st.error)(msg); st.rerun()
            a1, a2, a3 = st.columns(3)
            if a1.button("Activar", key="ow_act"):
                ok, msg = auth.set_active(sel, True);  (st.success if ok else st.error)(msg); st.rerun()
            if a2.button("Desactivar", key="ow_de"):
                ok, msg = auth.set_active(sel, False); (st.success if ok else st.error)(msg); st.rerun()
            if a3.button("Eliminar", key="ow_del"):
                ok, msg = auth.delete_user(sel);       (st.success if ok else st.error)(msg); st.rerun()


def render_owner_panel():
    st.markdown("### 👑 Administración")
    # Sub-navegación con radio (NO st.tabs anidado → evita mezcla de contenido)
    sec = st.radio("Sección", ["🏢 Grupos", "👥 Usuarios", "📁 Proyectos"],
                   horizontal=True, key="owner_sec", label_visibility="collapsed")
    st.markdown("---")
    if sec == "🏢 Grupos":
        _owner_grupos()
    elif sec == "👥 Usuarios":
        _owner_usuarios()
    else:
        from core.projects_ui import render_owner_projects
        render_owner_projects()


# ════════════════════════════════════════════════════════════
# PANEL DEL ADMINISTRADOR — su grupo (proyectos + usuarios de campo)
# ════════════════════════════════════════════════════════════
def _grupo_usuarios(grupo):
    users = auth.list_users(grupo=grupo)
    campo = [u for u in users if u["Rol"].lower() == "campo"]
    if campo:
        _rows = [{"Usuario": u["Usuario"], "Nombre": u["Nombre"], "Activo": u["Activo"],
                  "Contacto": "✅" if (str(u.get("Email", "")).strip()
                                       and str(u.get("TelegramChatID", "")).strip())
                              else "⚠️ falta"} for u in campo]
        st.dataframe(pd.DataFrame(_rows), hide_index=True, use_container_width=True)
    else:
        st.info("Aún no tienes usuarios de campo.")

    with st.expander("➕ Crear usuario de campo"):
        with st.form("form_campo", clear_on_submit=True):
            u  = st.text_input("Usuario")
            nm = st.text_input("Nombre")
            pw = st.text_input("Contraseña", type="password")
            em = st.text_input("📧 Email (OBLIGATORIO)")
            st.caption("El Telegram se vincula abajo, después de crearlo (el usuario pulsa Start en el bot).")
            if st.form_submit_button("Crear"):
                if not em.strip():
                    st.error("El email es obligatorio para usuarios de campo.")
                else:
                    ok, msg = auth.add_user(u, pw, "campo", nm, grupo)
                    if ok:
                        auth.set_contact(u, email=em)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()

    _field_contact_ui(campo, key_prefix="gp_cc")

    if campo:
        with st.expander("🔑 Modificar usuario de campo"):
            sel = st.selectbox("Usuario", [x["Usuario"] for x in campo], key="gp_sel")
            np_ = st.text_input("Nueva contraseña", type="password", key="gp_np")
            if st.button("Cambiar contraseña", key="gp_chp"):
                if np_:
                    ok, msg = auth.set_password(sel, np_); (st.success if ok else st.error)(msg)
            b1, b2, b3 = st.columns(3)
            if b1.button("Activar", key="gp_act"):
                ok, msg = auth.set_active(sel, True);  (st.success if ok else st.error)(msg); st.rerun()
            if b2.button("Desactivar", key="gp_de"):
                ok, msg = auth.set_active(sel, False); (st.success if ok else st.error)(msg); st.rerun()
            if b3.button("Eliminar", key="gp_del"):
                ok, msg = auth.delete_user(sel);       (st.success if ok else st.error)(msg); st.rerun()


def render_group_panel(grupo: str):
    st.markdown(f"### 🛠 Grupo: {grupo or '(sin grupo)'}")
    if not grupo:
        st.warning("Tu cuenta no tiene un grupo asignado. Contacta al propietario.")
        return

    sec = st.radio("Sección", ["📁 Proyectos", "🔧 Usuarios de campo"],
                   horizontal=True, key="grupo_sec", label_visibility="collapsed")
    st.markdown("---")
    if sec == "📁 Proyectos":
        from core.projects_ui import render_admin_projects
        render_admin_projects(grupo)
    else:
        _grupo_usuarios(grupo)
