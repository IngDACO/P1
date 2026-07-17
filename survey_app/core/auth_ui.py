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
    sec = st.radio("Sección",
                   ["🏢 Grupos", "👥 Usuarios", "📁 Proyectos", "🚆 Rieles", "📚 Manuales"],
                   horizontal=True, key="owner_sec", label_visibility="collapsed")
    st.markdown("---")
    if sec == "🏢 Grupos":
        _owner_grupos()
    elif sec == "👥 Usuarios":
        _owner_usuarios()
    elif sec == "📁 Proyectos":
        from core.projects_ui import render_owner_projects
        render_owner_projects()
    elif sec == "🚆 Rieles":
        _owner_rieles()
    else:
        _owner_manuales()


def _owner_manuales():
    """Banco de manuales para el agente de IA: subir/quitar (self-service)."""
    from core import manuals
    st.markdown("#### 📚 Banco de manuales del asistente")
    st.caption("El asistente de IA consulta estos manuales para responder dudas técnicas de "
               "instalación y **cita la fuente** (manual · sección · página).")

    # Pre-cargados (repo, solo lectura)
    pre = manuals.repo_manual_names()
    if pre:
        st.markdown("**Pre-cargados** (incluidos en la app):")
        for nm in pre:
            st.markdown(f"- 📖 {nm}")

    if not manuals.storage_available():
        st.info("Para subir manuales nuevos hace falta Google Drive + Sheets configurados "
                "(mismos secrets que documentos y fichaje).")
        return

    # Subidos por el propietario (Drive)
    st.markdown("---")
    st.markdown("**Subidos por ti:**")
    ups = manuals.list_uploaded()
    if ups:
        st.dataframe(pd.DataFrame([{
            "Manual": r.get("Nombre"),
            "Fragmentos": r.get("NumFrags"),
            "Fecha": r.get("Fecha"),
            "Por": r.get("SubidoPor"),
        } for r in ups]), hide_index=True, use_container_width=True)
        with st.expander("🗑 Quitar un manual"):
            opciones = {f"{r.get('Nombre')}  ·  {r.get('Fecha')}": r.get("ID") for r in ups}
            sel = st.selectbox("Manual", list(opciones.keys()), key="man_del_sel")
            if st.button("🗑 Eliminar", key="man_del_btn"):
                if manuals.delete_manual(opciones[sel]):
                    st.success("Manual eliminado.")
                    st.rerun()
                else:
                    st.error("No se pudo eliminar.")
    else:
        st.info("Aún no has subido manuales. Agrega el primero abajo.")

    with st.expander("➕ Subir manual", expanded=not ups):
        st.caption("Acepta un PDF con texto (no escaneado) o un ZIP con varios PDFs. "
                   "Evita PDFs enormes (>50 MB): se procesan en el navegador.")
        up = st.file_uploader("Archivo (PDF o ZIP)", type=["pdf", "zip"], key="man_up_file")
        nombre = st.text_input("Nombre del manual (ej. 'KONE MonoSpace')", key="man_up_name")
        if st.button("📥 Procesar y guardar", key="man_up_btn", disabled=up is None):
            if up is None:
                st.error("Selecciona un archivo.")
            else:
                nm = nombre.strip() or up.name.rsplit(".", 1)[0]
                with st.spinner("Extrayendo texto e indexando…"):
                    n, err = manuals.add_manual(
                        up.getvalue(), up.name, nm,
                        subido_por=st.session_state.auth.get("usuario", ""))
                if err:
                    st.error(err)
                else:
                    st.success(f"Manual «{nm}» agregado: {n} fragmentos indexados.")
                    st.rerun()


def _owner_rieles():
    """Catálogo de rieles: referencia → medidas (para autocompletar RAIL desde el plano)."""
    from core import rails
    st.markdown("#### 🚆 Catálogo de rieles")
    st.caption("Al cargar un plano, el lector detecta el código del **CAR GUIDE RAIL** y "
               "autocompleta **RAIL** con la *altura del diente desde la espalda* de esta tabla.")
    if not rails.is_configured():
        st.warning("Necesita Google Sheets configurado.")
        return
    data = rails.list_rieles()
    if data:
        st.dataframe(pd.DataFrame([{
            "Referencia": r.get("Referencia"),
            "Altura diente desde espalda (RAIL)": r.get("AlturaDiente"),
            "Ancho diente": r.get("AnchoDiente"),
        } for r in data]), hide_index=True, use_container_width=True)
    else:
        st.info("Catálogo vacío. Agrega el primer riel abajo.")

    with st.expander("➕ Agregar riel", expanded=not data):
        with st.form("form_riel", clear_on_submit=True):
            ref = st.text_input("Referencia (ej. T75-3/B)")
            rc1, rc2 = st.columns(2)
            alt = rc1.number_input("Altura del diente desde la espalda (RAIL) mm",
                                   min_value=0.0, step=0.5)
            anc = rc2.number_input("Ancho del diente (mm)", min_value=0.0, step=0.5)
            if st.form_submit_button("Agregar"):
                if not ref.strip():
                    st.error("La referencia es obligatoria.")
                else:
                    ok, msg = rails.add_riel(ref.strip(), anc, alt)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()

    if data:
        with st.expander("✏️ Editar / 🗑 eliminar riel"):
            refs = [r.get("Referencia") for r in data]
            sel  = st.selectbox("Referencia", refs, key="riel_sel")
            _cur = rails.get_rail(sel) or {}
            ec1, ec2 = st.columns(2)
            el = ec1.number_input("Altura diente desde espalda (RAIL)", min_value=0.0, step=0.5,
                                  value=float(_cur.get("altura") or 0.0), key="riel_el")
            ea = ec2.number_input("Ancho diente", min_value=0.0, step=0.5,
                                  value=float(_cur.get("ancho") or 0.0), key="riel_ea")
            b1, b2 = st.columns(2)
            if b1.button("💾 Guardar", key="riel_save"):
                ok, msg = rails.update_riel(sel, ea, el)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()
            if b2.button("🗑 Eliminar", key="riel_del"):
                ok, msg = rails.delete_riel(sel)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()


# ════════════════════════════════════════════════════════════
# PANEL DEL ADMINISTRADOR — su grupo (proyectos + usuarios de campo)
# ════════════════════════════════════════════════════════════
def _grupo_usuarios(grupo):
    users = auth.list_users(grupo=grupo)
    campo = [u for u in users if u["Rol"].lower() == "campo"]
    gente = [u for u in users if u["Rol"].lower() in ("campo", "conductor")]
    if gente:
        _rows = [{"Usuario": u["Usuario"], "Nombre": u["Nombre"],
                  "Rol": u["Rol"], "Activo": u["Activo"],
                  "Contacto": ("—" if u["Rol"].lower() == "conductor"
                               else ("✅" if (str(u.get("Email", "")).strip()
                                              and str(u.get("TelegramChatID", "")).strip())
                                     else "⚠️ falta"))} for u in gente]
        st.dataframe(pd.DataFrame(_rows), hide_index=True, use_container_width=True)
    else:
        st.info("Aún no tienes usuarios de campo ni conductores.")

    with st.expander("➕ Crear usuario (campo o conductor)"):
        with st.form("form_campo", clear_on_submit=True):
            u  = st.text_input("Usuario")
            nm = st.text_input("Nombre")
            pw = st.text_input("Contraseña", type="password")
            rl = st.selectbox("Rol", ["campo", "conductor"], key="gp_newrol")
            em = st.text_input("📧 Email (OBLIGATORIO para campo)")
            st.caption("Campo: el Telegram se vincula abajo tras crearlo. "
                       "Conductor: no requiere email/Telegram.")
            if st.form_submit_button("Crear"):
                if rl == "campo" and not em.strip():
                    st.error("El email es obligatorio para usuarios de campo.")
                else:
                    ok, msg = auth.add_user(u, pw, rl, nm, grupo)
                    if ok and rl == "campo" and em.strip():
                        auth.set_contact(u, email=em)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()

    _field_contact_ui(campo, key_prefix="gp_cc")

    if gente:
        with st.expander("🔑 Modificar usuario (campo / conductor)"):
            sel = st.selectbox("Usuario", [x["Usuario"] for x in gente], key="gp_sel")
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
    if not grupo:
        st.markdown("### 🛠 Mi grupo")
        st.warning("Tu cuenta no tiene un grupo asignado. Contacta al propietario.")
        return

    from core import projects_ui as PU
    PU.render_group_header(grupo)        # banda de marca + KPIs (centro de control)

    if not PU.P.is_configured():
        st.warning("La gestión del grupo necesita Google Sheets configurado "
                   "(gcp_service_account + TIMECLOCK_SHEET_ID en los Secrets).")
        return

    sec = st.radio("Sección",
                   ["📊 Proyectos", "🗂 Agrupaciones", "⏱ Horas", "🔧 Usuarios de campo"],
                   horizontal=True, key="grupo_sec", label_visibility="collapsed")
    st.markdown("---")
    if sec == "📊 Proyectos":
        PU._panel_proyectos(grupo)
    elif sec == "🗂 Agrupaciones":
        PU._panel_agrupaciones(grupo)
    elif sec == "⏱ Horas":
        PU.render_group_hours(grupo)
    else:
        _grupo_usuarios(grupo)
