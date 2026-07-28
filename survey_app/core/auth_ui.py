"""
UI de login, barra de usuario y paneles de gestión (propietario / administrador).
"""
import os
import re
import time
import streamlit as st
import pandas as pd

from core import auth
from core import ui_common as ui
from core import clock


def _contacto_uno(sel, key_prefix="cc"):
    """Email + vinculación de Telegram de UN usuario. El Telegram lo vincula el
    admin después de que el usuario pulse Start en el bot."""
    from core import notify
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


def _fecha_input(col, label, valor_actual="", *, key):
    """Selector de fecha OPCIONAL para credenciales (v185). Precarga `valor_actual`
    (texto de la hoja) y devuelve ISO 'YYYY-MM-DD', o '' si se deja vacío. Al guardar
    siempre en ISO, un typo ya no puede desactivar en silencio la alerta de vencimiento."""
    from core import credentials as C
    import datetime as _dt
    lo, hi = _dt.date(2000, 1, 1), _dt.date(2100, 12, 31)
    ini = C._parse(valor_actual) if valor_actual else None
    if ini and not (lo <= ini <= hi):
        ini = None
    d = col.date_input(label, value=ini, key=key, format="YYYY-MM-DD",
                       min_value=lo, max_value=hi)
    return d.isoformat() if d else ""


def render_credenciales(usuario, grupo, editable=False, key_prefix="cr"):
    """Tickets/credenciales de un usuario. editable=True → admin gestiona (agregar/editar/
    eliminar, subir foto/documento); editable=False → solo lectura (el propio usuario)."""
    from core import credentials as C
    if not C.is_configured():
        st.info("Las credenciales necesitan Google Sheets configurado.")
        return
    creds = C.list_for(usuario)
    if creds:
        # KPIs de un vistazo (v186): vigentes / por vencer / vencidas
        _sts = [C.status(r.get("Vencimiento")) for r in creds]
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Credenciales", len(creds))
        k2.metric("🟢 Vigentes", sum(1 for s in _sts if s == "vigente"))
        k3.metric("🟡 Por vencer", sum(1 for s in _sts if s == "por_vencer"))
        k4.metric("🔴 Vencidas", sum(1 for s in _sts if s == "vencido"))
        st.dataframe(pd.DataFrame([{
            "Tipo": r.get("Tipo"), "Número": r.get("Numero"), "Clase": r.get("Clase"),
            "Emisión": r.get("Emision") or "—", "Vence": r.get("Vencimiento") or "—",
            "Estado": C.status_label(r.get("Vencimiento")),
        } for r in creds]), hide_index=True, use_container_width=True)
        # Documentos adjuntos agrupados (antes: botones sueltos apilados bajo la tabla)
        _docs = [r for r in creds if str(r.get("DriveID", "")).strip()]
        if _docs:
            with st.expander(f"⬇️ Documentos ({len(_docs)})"):
                from core import drive_store
                for r in _docs:
                    try:
                        st.download_button(f"⬇️ {r.get('Tipo')} — {r.get('Archivo', 'archivo')}",
                                           data=drive_store.download(str(r.get("DriveID", "")).strip()),
                                           file_name=r.get("Archivo", "credencial"),
                                           key=f"{key_prefix}_dl_{r.get('ID')}")
                    except Exception:
                        pass
    else:
        st.caption("Sin credenciales registradas.")

    if not editable:
        return
    admin_usr = st.session_state.get("auth", {}).get("usuario", "")

    with st.expander("➕ Agregar credencial"):
        with st.form(f"{key_prefix}_add_{usuario}", clear_on_submit=True):
            tipo = st.selectbox("Tipo", C.CATALOGO, key=f"{key_prefix}_tipo")
            tipo_otro = st.text_input("Especifica (si elegiste 'Otro')", key=f"{key_prefix}_tipootro")
            c1, c2 = st.columns(2)
            num   = c1.text_input("Número")
            clase = c2.selectbox("Clase (para licencia)", C.CLASES_LICENCIA, key=f"{key_prefix}_clase")
            c3, c4 = st.columns(2)
            emi = _fecha_input(c3, "Emisión", key=f"{key_prefix}_emi")
            ven = _fecha_input(c4, "Vencimiento (vacío si no vence)", key=f"{key_prefix}_ven")
            arch = st.file_uploader("Foto o documento (opcional)",
                                    type=["pdf", "png", "jpg", "jpeg"], key=f"{key_prefix}_file")
            nota = st.text_input("Nota")
            if st.form_submit_button("Agregar"):
                t = tipo_otro.strip() if (tipo == "Otro" and tipo_otro.strip()) else tipo
                did, fname = "", ""
                if arch is not None:
                    fname = arch.name
                    did = C.upload_file(usuario, t, arch.name, arch.getvalue(),
                                        arch.type or "application/octet-stream")
                    if not did:
                        st.warning("No se pudo subir el archivo a Drive; se guarda el resto.")
                ok, msg = C.add(usuario, grupo, t, num, clase, emi, ven, did, fname, nota, admin_usr)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()

    if creds:
        with st.expander("✏️ Editar / 🗑 eliminar credencial"):
            idmap = {f"{r.get('Tipo')} · {r.get('Numero') or 's/n'} ({r.get('ID')})": r for r in creds}
            sel = st.selectbox("Credencial", list(idmap.keys()), key=f"{key_prefix}_esel")
            r = idmap[sel]
            _kid = str(r.get("ID", ""))
            c1, c2 = st.columns(2)
            enum = c1.text_input("Número", value=r.get("Numero", ""), key=f"{key_prefix}_enum_{_kid}")
            even = _fecha_input(c2, "Vencimiento (vacío si no vence)", r.get("Vencimiento", ""),
                                key=f"{key_prefix}_even_{_kid}")
            enota = st.text_input("Nota", value=r.get("Nota", ""), key=f"{key_prefix}_enota_{_kid}")
            b1, b2 = st.columns(2)
            if b1.button("💾 Guardar", key=f"{key_prefix}_eupd"):
                ok, msg = C.update(r.get("ID"), {"Numero": enum, "Vencimiento": even, "Nota": enota,
                                                 "ActualizadoPor": admin_usr})
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()
            if b2.button("🗑 Eliminar", key=f"{key_prefix}_edel"):
                ok, msg = C.delete(r.get("ID"))
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()


def render_my_credentials():
    """Vista de solo lectura de las credenciales del usuario logueado."""
    a = st.session_state.get("auth", {})
    st.markdown("### 🎫 Mis credenciales")
    st.caption("Tus tickets y credenciales registrados por tu administrador. Muéstralos en obra si te los piden.")
    render_credenciales(a.get("usuario", ""), a.get("grupo", ""), editable=False, key_prefix="mycr")


_LOGO = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "icon-512.png")


def render_login() -> bool:
    """True si hay sesión iniciada. Si no, muestra el login y devuelve False."""
    if st.session_state.get("auth"):
        return True

    # ── Login persistente: restaurar desde la cookie (sobrevive al refresco) ──
    # ⚠️ El componente de cookies (extra-streamlit-components) NO entrega las cookies
    # en el PRIMER run tras un refresco: las reporta en un rerun posterior. Antes se
    # marcaba `_cookie_tried` en ese primer intento y NUNCA se reintentaba → refrescar
    # deslogueaba. Ahora se REINTENTA unos pocos reruns antes de rendirse.
    if not st.session_state.get("_cookie_done"):
        _u = _t = None
        try:
            from core import session_cookie
            _u, _t = session_cookie.load()
        except Exception:
            st.session_state["_cookie_done"] = True
        if _u and _t:
            st.session_state["_cookie_done"] = True
            try:
                _a = auth.validate_session(_u, _t)
            except Exception:
                _a = None
            if _a:
                st.session_state["auth"] = _a
                st.session_state["_hb_last"] = time.time()
                st.rerun()
        elif not st.session_state.get("_cookie_done"):
            # Todavía no llegan las cookies del navegador: dar unos reruns de gracia.
            _w = st.session_state.get("_cookie_waits", 0)
            if _w < 3:
                st.session_state["_cookie_waits"] = _w + 1
                time.sleep(0.2)
                st.rerun()
            st.session_state["_cookie_done"] = True

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
                try:    # login persistente (sobrevive el refresco)
                    from core import session_cookie
                    session_cookie.save(res["usuario"], tok)
                except Exception:
                    pass
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
        try:
            from core import session_cookie
            session_cookie.clear()
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

    # ── Zona horaria por grupo (v173) ──
    # Define en qué hora LOCAL se graban los registros de cada grupo (cada empresa
    # puede estar en otro país). Sin fijar → clock.DEFAULT_TZ.
    if grupos:
        with st.expander("🕐 Zona horaria de cada grupo"):
            st.caption("En qué hora local se graban los registros (fichaje, pre-start, "
                       f"alarmas…) de ese grupo. Sin fijar = {clock.DEFAULT_TZ}.")
            _gz = {g["Grupo"]: (g.get("Zona") or "") for g in grupos}
            gzsel = ui.elegir("Grupo", list(_gz.keys()), key="tz_g_sel", vacio="— elige un grupo —")
            if gzsel:
                _cur = _gz.get(gzsel) or clock.DEFAULT_TZ
                _opts = ["Australia/Sydney", "Australia/Brisbane", "Australia/Adelaide",
                         "Australia/Perth", "Australia/Darwin", "Pacific/Auckland",
                         "Europe/Madrid", "America/New_York", "America/Los_Angeles", "UTC"]
                if _cur not in _opts:
                    _opts = [_cur] + _opts
                znew = st.selectbox("Zona horaria (IANA)", _opts, index=_opts.index(_cur),
                                    key="tz_z_sel")
                try:
                    from zoneinfo import ZoneInfo
                    from datetime import datetime as _dtn
                    st.caption(f"En **{znew}** ahora son las "
                               f"**{_dtn.now(ZoneInfo(znew)).strftime('%H:%M')}**.  "
                               f"(Actual del grupo: {_gz.get(gzsel) or 'sin fijar'})")
                except Exception:
                    pass
                if st.button("💾 Guardar zona", key="tz_save"):
                    ok, msg = auth.set_group_timezone(gzsel, znew)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()

    if grupos:
        gsel = ui.elegir("Eliminar grupo", [g["Grupo"] for g in grupos],
                         key="del_g_sel", vacio="— ningún grupo —")
        if gsel:
            _ok_del = ui.confirmar_borrado("del_g_ok",
                                           f"Confirmo eliminar el grupo **{gsel}**")
            if st.button("🗑 Eliminar grupo", key="del_g_btn", disabled=not _ok_del):
                ok, msg = auth.delete_group(gsel)
                (st.success if ok else st.error)(msg)
                if ok: st.rerun()


def _owner_usuarios():
    """Gestión de usuarios del propietario (v184): mismo estilo que el administrador
    — una tabla-resumen y luego la ficha 360° por persona (una sola selección),
    en vez de los 3 desplegables sueltos de antes."""
    users = auth.list_users()

    # ── Tabla-resumen de todos los usuarios (+ contacto ✅/⚠️) ──
    if users:
        _rows = []
        for u in users:
            es_campo = str(u.get("Rol", "")).lower() == "campo"
            _cont = ("—" if not es_campo
                     else ("✅" if (str(u.get("Email", "")).strip()
                                    and str(u.get("TelegramChatID", "")).strip())
                           else "⚠️ falta"))
            _rows.append({"Usuario": u.get("Usuario", ""), "Nombre": u.get("Nombre", ""),
                          "Rol": u.get("Rol", ""), "Grupo": u.get("Grupo", "") or "—",
                          "Activo": u.get("Activo", "SI"),
                          "Email": u.get("Email", "") or "—", "Contacto": _cont})
        st.dataframe(pd.DataFrame(_rows), hide_index=True, use_container_width=True)
        _faltan = [u["Usuario"] for u in users
                   if str(u.get("Rol", "")).lower() == "campo"
                   and not (str(u.get("Email", "")).strip()
                            and str(u.get("TelegramChatID", "")).strip())]
        if _faltan:
            st.warning("⚠️ Campo sin contacto completo (no pueden usar la app): "
                       + ", ".join(_faltan))

    # ── Crear usuario (rol + grupo) ──
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

    # ── Gestionar un usuario: ficha 360° (una sola selección) ──
    if users:
        st.markdown("#### 👤 Gestionar un usuario")
        _gf = ui.elegir("Filtrar por grupo", [g["Grupo"] for g in auth.list_groups()],
                        key="ow_ficha_gfil", vacio="— todos los grupos —")
        _cands = [u for u in users if (not _gf or str(u.get("Grupo", "")) == _gf)]
        _map = {f"{u['Nombre'] or u['Usuario']} ({u['Usuario']}) · {u.get('Grupo') or 'sin grupo'}": u
                for u in _cands}
        _elegido = ui.elegir("Usuario", _map, key="ow_fichasel", vacio="— elige un usuario —")
        if _elegido:
            st.markdown("---")
            _ficha_usuario(_elegido, _elegido.get("Grupo", ""),
                           owner=True, sel_key="ow_fichasel")


def render_owner_panel():
    st.markdown("### 👑 Administración")
    # Sub-navegación con radio (NO st.tabs anidado → evita mezcla de contenido)
    sec = st.radio("Sección",
                   ["🌐 Resumen", "🏢 Grupos", "👥 Usuarios", "📁 Proyectos", "🚆 Rieles", "📚 Manuales"],
                   horizontal=True, key="owner_sec", label_visibility="collapsed")
    st.markdown("---")
    if sec == "🌐 Resumen":
        _owner_resumen()
    elif sec == "🏢 Grupos":
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


def _owner_resumen():
    """Resumen multi-grupo del propietario: estado de cada empresa cliente."""
    from core import admin_digest
    st.markdown("#### 🌐 Resumen de todos los grupos")
    from core import projects as _P
    if not _P.is_configured():
        st.warning("Necesita Google Sheets configurado.")
        return
    with st.spinner("Reuniendo el estado de cada grupo…"):
        data = admin_digest.owner_digest()
    if not data:
        st.info("Aún no hay grupos con datos.")
        return
    st.dataframe(pd.DataFrame([{
        "Grupo": d["grupo"], "Activos": d["activos"], "Avance %": d["avance"],
        "🔴 Retraso": d["retrasos"], "🔔 Alarmas": d["alarmas"],
        "⛔ Vencidos": d["vencidos"], "🎫 Credenciales": d["cred_venc"],
        "💸 Sobre pres.": d["sobre_presupuesto"],
    } for d in data]), hide_index=True, use_container_width=True)
    _urg = [d for d in data if d["pendientes"]]
    if _urg:
        st.warning("Grupos con pendientes: " + ", ".join(d["grupo"] for d in _urg))
    else:
        st.success("Ningún grupo tiene pendientes urgentes. ✅")


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
            _mid = ui.elegir("Manual", opciones, key="man_del_sel",
                             vacio="— ningún manual —")
            if _mid:
                _ok_del = ui.confirmar_borrado("man_del_ok",
                                               "Confirmo eliminar este manual")
                if st.button("🗑 Eliminar", key="man_del_btn", disabled=not _ok_del):
                    if manuals.delete_manual(_mid):
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
def _ficha_usuario(u, grupo, owner=False, sel_key="gp_fichasel"):
    """Ficha 360° de UN usuario: identidad, acceso, contacto, credenciales y su
    trabajo (v153). Antes había que elegir a la persona en 3 desplegables distintos
    (contacto / modificar / credenciales); ahora se gestiona todo desde aquí.

    owner=True (v184): además de contraseña/tarifa/estado, la pestaña Acceso deja
    reasignar Rol y Grupo (lo que antes solo tenía el panel disperso del propietario).
    sel_key: clave del selector externo, para limpiarla al eliminar al usuario."""
    from core import credentials as C
    from core import projects as P
    from core import timeclock as T
    from core import expenses as E
    sel   = u["Usuario"]
    es_campo = u["Rol"].lower() == "campo"
    k = f"fu_{sel}"

    # ── Estado de un vistazo ──
    contacto_ok = bool(str(u.get("Email", "")).strip()
                       and str(u.get("TelegramChatID", "")).strip())
    activo = str(u.get("Activo", "")).strip().upper() in ("SI", "TRUE", "1", "SÍ")
    try:
        _ses = T.open_sessions(u.get("Nombre") or sel, grupo, sel)
        fichando = bool(_ses.get(T.TIPO_GENERAL) or _ses.get(T.TIPO_PROYECTO))
    except Exception:
        fichando = False
    chips = [("🟢 Activo" if activo else "🔴 Inactivo"),
             ("🕐 Fichando ahora" if fichando else ""),
             (("📇 Contacto OK" if contacto_ok else "⚠️ Sin contacto")
              if es_campo else "")]
    st.markdown(f"**{u.get('Nombre') or sel}**  ·  _{u['Rol']}_  ·  "
                + "  ·  ".join(c for c in chips if c))

    _sec = st.radio("Sección del usuario",
                    ["🔑 Acceso", "📇 Contacto", "🎫 Credenciales", "📊 Su trabajo", "🗑"],
                    horizontal=True, key=f"{k}_sec", label_visibility="collapsed")

    if _sec == "🔑 Acceso":
        np_ = st.text_input("Nueva contraseña", type="password", key=f"{k}_np")
        if st.button("Cambiar contraseña", key=f"{k}_chp"):
            if np_:
                ok, msg = auth.set_password(sel, np_); (st.success if ok else st.error)(msg)
            else:
                st.error("Escribe la nueva contraseña.")
        if owner:   # el propietario también reasigna rol y grupo (v184)
            _gopts = [""] + [g["Grupo"] for g in auth.list_groups()]
            _rc, _gc = st.columns(2)
            _rcur = str(u.get("Rol", "") or "campo")
            _nrol = _rc.selectbox("Rol", auth.ROLES,
                                  index=auth.ROLES.index(_rcur) if _rcur in auth.ROLES else 0,
                                  key=f"{k}_rol")
            if _rc.button("Aplicar rol", key=f"{k}_chrol"):
                ok, msg = auth.set_role(sel, _nrol); (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()
            _gcur = str(u.get("Grupo", "") or "")
            _ngrp = _gc.selectbox("Grupo", _gopts,
                                  index=_gopts.index(_gcur) if _gcur in _gopts else 0,
                                  key=f"{k}_grp")
            if _gc.button("Aplicar grupo", key=f"{k}_chgrp"):
                ok, msg = auth.set_group(sel, _ngrp); (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()
        tar = st.number_input("💵 Tarifa por hora (para costear la mano de obra)",
                              min_value=0.0, step=1.0,
                              value=float(str(u.get("TarifaHora", "") or 0).replace(",", ".") or 0),
                              key=f"{k}_tar")
        if st.button("Guardar tarifa", key=f"{k}_savetar"):
            ok, msg = auth.set_rate(sel, tar); (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()
        if activo:
            if st.button("🔴 Desactivar (no podrá entrar)", key=f"{k}_de"):
                ok, msg = auth.set_active(sel, False); (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()
        else:
            if st.button("🟢 Activar", key=f"{k}_act"):
                ok, msg = auth.set_active(sel, True); (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()

    elif _sec == "📇 Contacto":
        if not es_campo:
            st.caption("El contacto (email + Telegram) solo es obligatorio para "
                       "usuarios de campo. Puedes registrarlo igual.")
        elif not contacto_ok:
            st.warning("⚠️ Sin contacto completo **no puede usar la app** y no recibe "
                       "asignaciones ni inducciones.")
        _contacto_uno(sel, key_prefix=f"{k}_cc")

    elif _sec == "🎫 Credenciales":
        render_credenciales(sel, grupo, editable=True, key_prefix=f"{k}_cr")

    elif _sec == "📊 Su trabajo":
        # Todo lo asociado a la persona, en solo lectura.
        c1, c2, c3 = st.columns(3)
        try:
            gh = next((d for d in T.group_hours(grupo, days=None)
                       if d["usuario"] == sel), None)
            _h = (gh["general"] + gh["proyecto"]) if gh else 0.0
        except Exception:
            _h = 0.0
        rec = E.by_user(grupo, sel) if E.is_configured() else {"n": 0, "total": 0.0}
        asg = ([p for p in P.list_projects(grupo=grupo)
                if sel in [x.strip() for x in str(p.get("CampoAsignados", "")).split(";")]]
               if es_campo else [])
        c1.metric("Horas registradas", f"{_h:.1f}")
        c2.metric("Recibos cargados", rec["n"])
        c3.metric("Proyectos asignados", len(asg))
        if asg:
            st.caption("**Asignado a:** " + " · ".join(str(p.get("Nombre")) for p in asg))
        if rec["n"]:
            st.caption(f"Ha cargado recibos por **${rec['total']:,.0f}** en total.")
        st.caption("Las horas y los recibos se gestionan desde ⏱ Fichaje y el detalle "
                   "de cada proyecto; aquí es un resumen de solo lectura.")

    else:  # 🗑 eliminar
        st.warning("Eliminar quita al usuario y su acceso. Sus fichajes, recibos y "
                   "credenciales ya registrados **no se borran** (quedan a su nombre).")
        if ui.confirmar_borrado(f"{k}_delok", f"Confirmo eliminar a «{sel}»"):
            if st.button("Eliminar definitivamente", key=f"{k}_del"):
                ok, msg = auth.delete_user(sel); (st.success if ok else st.error)(msg)
                if ok:
                    st.session_state.pop(sel_key, None)
                    st.rerun()


def _grupo_usuarios(grupo):
    from core import credentials as C
    users = auth.list_users(grupo=grupo)
    gente = [u for u in users if u["Rol"].lower() == "campo"]

    # Aviso de vencimientos (email/Telegram) una vez por sesión
    if C.is_configured() and not st.session_state.get(f"_credaviso_{grupo}"):
        st.session_state[f"_credaviso_{grupo}"] = True
        try:
            C.notify_expiring(grupo)
        except Exception:
            pass

    # ── Panorama: tabla-resumen con semáforos ──
    if gente:
        _rows = []
        for u in gente:
            es_campo = u["Rol"].lower() == "campo"
            _cont = ("—" if not es_campo
                     else ("✅" if (str(u.get("Email", "")).strip()
                                    and str(u.get("TelegramChatID", "")).strip())
                           else "⚠️ falta"))
            _rows.append({"Usuario": u["Usuario"], "Nombre": u["Nombre"],
                          "Rol": u["Rol"], "Activo": u["Activo"],
                          "Tarifa/h": u.get("TarifaHora", "") or "—", "Contacto": _cont})
        st.dataframe(pd.DataFrame(_rows), hide_index=True, use_container_width=True)
    else:
        st.info("Aún no tienes usuarios de campo. Crea uno abajo.")

    # ── Matriz de compliance (panorama de credenciales) ──
    if gente and C.is_configured():
        try:
            tipos, filas = C.matrix(grupo)
            if tipos:
                with st.expander("🗂 Matriz de credenciales (usuarios × tickets)"):
                    st.caption("🟢 vigente · 🟡 por vencer (≤30 d) · 🔴 vencido · — no registrada")
                    st.dataframe(pd.DataFrame(filas), hide_index=True, use_container_width=True)
        except Exception:
            pass

    # ── Crear usuario (plegado) ──
    with st.expander("➕ Crear usuario de campo"):
        with st.form("form_campo", clear_on_submit=True):
            u  = st.text_input("Usuario")
            nm = st.text_input("Nombre")
            pw = st.text_input("Contraseña", type="password")
            em = st.text_input("📧 Email (OBLIGATORIO para campo)")
            st.caption("El Telegram se vincula en su ficha tras crearlo.")
            if st.form_submit_button("Crear"):
                if not em.strip():
                    st.error("El email es obligatorio para usuarios de campo.")
                else:
                    ok, msg = auth.add_user(u, pw, "campo", nm, grupo)
                    if ok and em.strip():
                        auth.set_contact(u, email=em)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()

    # ── Ficha de UN usuario (elegir y gestionar todo) ──
    if gente:
        st.markdown("#### 👤 Gestionar un usuario")
        _map = {f"{u['Nombre'] or u['Usuario']} ({u['Usuario']})": u for u in gente}
        _elegido = ui.elegir("Usuario", _map, key="gp_fichasel",
                             vacio="— elige un usuario —")
        if _elegido:
            st.markdown("---")
            _ficha_usuario(_elegido, grupo)


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

    # Sección pendiente (p.ej. "abrir un proyecto del tablero de Planificación"):
    # se aplica ANTES de instanciar el radio, nunca después (regla v111, como
    # main_nav con _nav_pending).
    _gsp = st.session_state.pop("_gruposec_pending", None)
    if _gsp:
        st.session_state["grupo_sec"] = _gsp
    sec = st.radio("Sección",
                   ["📊 Proyectos", "🗂 Agrupaciones", "📅 Planificación",
                    "⏱ Horas", "💰 Gastos", "🔧 Usuarios de campo"],
                   horizontal=True, key="grupo_sec", label_visibility="collapsed")
    st.markdown("---")
    if sec == "📊 Proyectos":
        PU._panel_proyectos(grupo)
    elif sec == "🗂 Agrupaciones":
        PU._panel_agrupaciones(grupo)
    elif sec == "📅 Planificación":
        from core import roster_ui
        roster_ui.render_planificacion(grupo)
    elif sec == "⏱ Horas":
        PU.render_group_hours(grupo)
    elif sec == "💰 Gastos":
        PU.render_group_expenses(grupo)
    else:
        _grupo_usuarios(grupo)
