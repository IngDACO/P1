"""
UI de login y gestión de usuarios.
"""
import streamlit as st
import pandas as pd

from core import auth


def _banner():
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1a3a5c,#2e6da4);padding:20px 28px;
                border-radius:12px;margin-bottom:18px;text-align:center;">
      <div style="color:white;font-size:2rem;font-weight:900;letter-spacing:0.2em;">COPEX</div>
      <div style="color:#b0c8e8;font-size:0.9rem;">Elevator Survey Analyzer</div>
    </div>
    """, unsafe_allow_html=True)


def render_login() -> bool:
    """True si hay sesión iniciada. Si no, muestra el login y devuelve False."""
    if st.session_state.get("auth"):
        return True

    _banner()

    if not auth.is_configured():
        st.error("🔒 El acceso no está conectado a Google Sheets. "
                 "Configura las credenciales (gcp_service_account + TIMECLOCK_SHEET_ID) "
                 "en los Secrets de Streamlit Cloud.")
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
            if st.button("Iniciar sesión", type="primary", use_container_width=True):
                res = auth.verify_login(u, p)
                if res.get("ok"):
                    st.session_state["auth"] = {
                        "usuario": res["usuario"], "rol": res["rol"], "nombre": res["nombre"]
                    }
                    st.rerun()
                else:
                    st.error(res.get("error", "Error de autenticación."))
    return False


def render_user_bar():
    """Muestra el usuario logueado + botón de salir (en el sidebar)."""
    a = st.session_state.get("auth", {})
    rol_lbl = {"propietario": "👑 Propietario", "administrador": "🛠 Administrador",
               "campo": "🔧 Campo"}.get(a.get("rol"), a.get("rol", ""))
    st.markdown(f"**{a.get('nombre','')}**  \n{rol_lbl}")
    if st.button("🚪 Cerrar sesión", use_container_width=True, key="logout_btn"):
        for k in list(st.session_state.keys()):
            if k == "auth":
                del st.session_state[k]
        st.rerun()


def render_user_management():
    """Panel de gestión de usuarios (solo propietario)."""
    st.markdown("#### 👥 Gestión de usuarios")
    users = auth.list_users()
    if users:
        st.dataframe(pd.DataFrame(users), hide_index=True, use_container_width=True)

    with st.expander("➕ Crear usuario"):
        u  = st.text_input("Usuario", key="mu_u")
        nm = st.text_input("Nombre", key="mu_n")
        rl = st.selectbox("Rol", auth.ROLES, key="mu_rol")
        pw = st.text_input("Contraseña", type="password", key="mu_p")
        if st.button("Crear", key="mu_add"):
            ok, msg = auth.add_user(u, pw, rl, nm)
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()

    if users:
        with st.expander("🔑 Modificar usuario"):
            unames = [x["Usuario"] for x in users]
            sel = st.selectbox("Usuario", unames, key="mu_sel")
            np_ = st.text_input("Nueva contraseña", type="password", key="mu_np")
            if st.button("Cambiar contraseña", key="mu_chp"):
                if np_:
                    ok, msg = auth.set_password(sel, np_)
                    (st.success if ok else st.error)(msg)
                else:
                    st.warning("Ingresa la nueva contraseña.")
            nr = st.selectbox("Cambiar rol a", auth.ROLES, key="mu_nr")
            if st.button("Aplicar rol", key="mu_chr"):
                ok, msg = auth.set_role(sel, nr)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()
            c1, c2, c3 = st.columns(3)
            if c1.button("Activar", key="mu_act"):
                ok, msg = auth.set_active(sel, True);  (st.success if ok else st.error)(msg); st.rerun()
            if c2.button("Desactivar", key="mu_deact"):
                ok, msg = auth.set_active(sel, False); (st.success if ok else st.error)(msg); st.rerun()
            if c3.button("Eliminar", key="mu_del"):
                ok, msg = auth.delete_user(sel);       (st.success if ok else st.error)(msg); st.rerun()
