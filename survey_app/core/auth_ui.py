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
from core import flash          # v365: mensajes que sobreviven al st.rerun()


def _contacto_uno(sel, key_prefix="cc"):
    """Email + vinculación de Telegram de UN usuario. El Telegram lo vincula el
    admin después de que el usuario pulse Start en el bot."""
    from core import notify
    rec = auth.get_user(sel)
    em  = st.text_input(":material/mail: Email", value=str(rec.get("Email", "")), key=f"{key_prefix}_em")
    if st.button("Guardar email", key=f"{key_prefix}_emb"):
        ok, msg = auth.set_contact(sel, email=em)
        (flash.exito if ok else st.error)(msg)
        if ok:
            st.rerun()
    st.markdown("**:material/send: Telegram**")
    tg = str(rec.get("TelegramChatID", "")).strip()
    if not notify.telegram_configured() or not notify.bot_username():
        # ⚠️ v368: antes esto era un callejón sin salida. Decía «no configurado» y ya:
        # ningún botón para vincular, y el usuario de campo quedaba bloqueado en la
        # entrada exigiéndosele justo esto. Ahora se dice que NO se le exige (el
        # bloqueo de `app.py` solo pide los canales que existen) y se ofrece la salida
        # manual, por si el chat_id se consiguió por otra vía.
        st.caption(":material/info: Telegram no está configurado en esta instalación "
                   "(falta el bot en Secrets), así que **no se le exige** para entrar. "
                   "Con el email basta.")
        with st.expander("Poner el chat_id a mano", icon=":material/edit:"):
            _man = st.text_input("Chat ID de Telegram", value=tg, key=f"{key_prefix}_tgman",
                                 help="Solo si ya lo tienes por otra vía. Sin bot "
                                      "configurado, la app no puede enviarle nada.")
            if st.button("Guardar chat_id", key=f"{key_prefix}_tgmanb"):
                ok, msg = auth.set_contact(sel, telegram=_man.strip())
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
    elif tg:
        st.success(":material/check_circle: Telegram vinculado.")
        if st.button("Desvincular Telegram", key=f"{key_prefix}_tgu"):
            auth.set_contact(sel, telegram="")
            st.rerun()
    else:
        bot  = notify.bot_username()
        code = re.sub(r"[^A-Za-z0-9_-]", "", sel) or "user"
        st.caption("1) El usuario abre el bot y pulsa **Start** (envíale este link):")
        st.code(f"https://t.me/{bot}?start={code}")
        st.caption("2) Cuando lo haya hecho, pulsa:")
        if st.button(":material/link: Vincular Telegram de este usuario", key=f"{key_prefix}_tgl"):
            cid = notify.telegram_find_chat_by_code(code)
            if cid:
                auth.set_contact(sel, telegram=cid)
                flash.exito(":material/check_circle: Telegram vinculado.")
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
        k2.metric(":material/check_circle: Vigentes", sum(1 for s in _sts if s == "vigente"))
        k3.metric(":material/schedule: Por vencer", sum(1 for s in _sts if s == "por_vencer"))
        k4.metric(":material/cancel: Vencidas", sum(1 for s in _sts if s == "vencido"))
        st.dataframe(pd.DataFrame([{
            "Tipo": r.get("Tipo"), "Número": r.get("Numero"), "Clase": r.get("Clase"),
            "Emisión": r.get("Emision") or "—", "Vence": r.get("Vencimiento") or "—",
            "Estado": C.status_label(r.get("Vencimiento")),
        } for r in creds]), hide_index=True, width="stretch")
        # Documentos adjuntos agrupados (antes: botones sueltos apilados bajo la tabla)
        _docs = [r for r in creds if str(r.get("DriveID", "")).strip()]
        if _docs:
            with st.expander(f":material/download: Documentos ({len(_docs)})"):
                from core import drive_store
                for r in _docs:
                    try:
                        st.download_button(f":material/download: {r.get('Tipo')} — {r.get('Archivo', 'archivo')}",
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

    with st.expander("Agregar credencial", icon=":material/add_circle:"):
        # 'Tipo' va FUERA del form (v189): así, al cambiarlo, la app se re-renderiza
        # y podemos mostrar solo los campos que aplican — "especifica" para 'Otro' y
        # "Clase" solo para licencia de conducir. Dentro de un form no hay rerun hasta
        # el submit, así que ahí no se puede condicionar. El Tipo queda seleccionado
        # tras agregar (cómodo para cargar varias del mismo tipo).
        tipo = st.selectbox("Tipo", C.CATALOGO, key=f"{key_prefix}_tipo")
        _es_otro = (tipo == "Otro")
        _es_lic  = (tipo == "Driver License")
        tipo_otro = (st.text_input("Especifica el tipo", key=f"{key_prefix}_tipootro")
                     if _es_otro else "")
        with st.form(f"{key_prefix}_add_{usuario}", clear_on_submit=True):
            if _es_lic:
                c1, c2 = st.columns(2)
                num   = c1.text_input("Número")
                clase = c2.selectbox("Clase (licencia)", C.CLASES_LICENCIA, key=f"{key_prefix}_clase")
            else:
                num   = st.text_input("Número")
                clase = ""
            c3, c4 = st.columns(2)
            emi = _fecha_input(c3, "Emisión", key=f"{key_prefix}_emi")
            ven = _fecha_input(c4, "Vencimiento (vacío si no vence)", key=f"{key_prefix}_ven")
            arch = st.file_uploader("Foto o documento (opcional)",
                                    type=["pdf", "png", "jpg", "jpeg"], key=f"{key_prefix}_file")
            nota = st.text_input("Nota")
            if st.form_submit_button("Agregar"):
                t = tipo_otro.strip() if (_es_otro and tipo_otro.strip()) else tipo
                did, fname = "", ""
                if arch is not None:
                    fname = arch.name
                    did = C.upload_file(usuario, t, arch.name, arch.getvalue(),
                                        arch.type or "application/octet-stream")
                    if not did:
                        st.warning("No se pudo subir el archivo a Drive; se guarda el resto.")
                ok, msg = C.add(usuario, grupo, t, num, clase, emi, ven, did, fname, nota, admin_usr)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()

    if creds:
        with st.expander("Editar / eliminar credencial", icon=":material/edit:"):
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
            if b1.button(":material/save: Guardar", key=f"{key_prefix}_eupd"):
                ok, msg = C.update(r.get("ID"), {"Numero": enum, "Vencimiento": even, "Nota": enota,
                                                 "ActualizadoPor": admin_usr})
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
            if b2.button(":material/delete: Eliminar", key=f"{key_prefix}_edel"):
                ok, msg = C.delete(r.get("ID"))
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()


def render_my_credentials():
    """Vista de solo lectura de las credenciales del usuario logueado."""
    a = st.session_state.get("auth", {})
    st.markdown("### :material/badge: Mis credenciales")
    st.caption("Tus tickets y credenciales registrados por tu administrador. Muéstralos en obra si te los piden.")
    render_credenciales(a.get("usuario", ""), a.get("grupo", ""), editable=False, key_prefix="mycr")


_LOGO = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "icon-512.png")


def render_login() -> bool:
    """True si hay sesión iniciada. Si no, muestra el login y devuelve False."""
    if st.session_state.get("auth"):
        return True

    # ── Login persistente: restaurar desde la cookie (sobrevive al refresco) ──
    # El componente de cookies (extra-streamlit-components) entrega las cookies en un
    # rerun POSTERIOR al montaje (un mensaje del navegador por WebSocket). El enfoque
    # previo (v174→v187) BLOQUEABA con `time.sleep` + reruns forzados y se rendía a los
    # 3 intentos; pero durante el sleep el hilo no procesa ese mensaje, así que el rerun
    # con la cookie llegaba SIEMPRE después de rendirse → refrescar deslogueaba. Ahora
    # (v188) solo renderizamos el componente (manager persistente en session_state) y
    # dejamos que él dispare su propio rerun: se ve el login un instante y, al llegar la
    # cookie, se restaura sola. Tras un logout explícito NO se auto-restaura.
    if not st.session_state.get("_no_cookie_restore"):
        _u = _t = None
        try:
            from core import session_cookie
            _u, _t = session_cookie.load()
        except Exception:
            pass
        if _u and _t:
            try:
                _a = auth.validate_session(_u, _t)
            except Exception:
                _a = None
            if _a:
                st.session_state["auth"] = _a
                st.session_state["_hb_last"] = time.time()
                st.session_state["_remember_session"] = True   # v222: había cookie → recordar
                st.rerun()

    # ── Logo COPEX centrado (v201: ~40% más pequeño → columnas [2,1,2]) ──
    c = st.columns([2, 1, 2])
    with c[1]:
        if os.path.exists(_LOGO):
            st.image(_LOGO, width="stretch")
        else:
            st.markdown("<h1 style='text-align:center;letter-spacing:.2em;color:#1a3a5c'>COPEX</h1>",
                        unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;color:#5b6472;margin-top:-8px;font-size:16px;'>"
        "Gestión de instalación de elevadores"
        "<br><span style='font-size:13px;color:#8b95a5;'>Proyectos · Cuadrilla · Costos · "
        "Herramientas técnicas</span></p>",
        unsafe_allow_html=True)

    # ⚠️ v365: los mensajes que sobrevivieron a un rerun también se pintan AQUÍ. El
    # login ocurre ANTES de la shell, así que sin esto el «propietario creado, ahora
    # inicia sesión» del bootstrap se perdería igual que antes.
    flash.mostrar()

    if not auth.is_configured():
        st.error(":material/lock: El acceso no está conectado a Google Sheets. "
                 "Configura los Secrets (gcp_service_account + TIMECLOCK_SHEET_ID) en Streamlit Cloud.")
        return False

    try:
        first_run = not auth.has_any_user()
    except Exception:
        first_run = False

    # v284: el formulario dentro de una TARJETA (sistema de diseño). Se envuelve la
    # columna en un container con borde — un solo cambio de línea, sin reindentar el
    # cuerpo (evita la clase de bug de v120/v148).
    mid = st.columns([1, 2, 1])[1].container(border=True)
    with mid:
        if first_run:
            st.info(":material/shield_person: **Configuración inicial** — crea la cuenta de propietario.")
            u  = st.text_input("Usuario", key="setup_u")
            nm = st.text_input("Nombre", key="setup_n")
            p1 = st.text_input("Contraseña", type="password", key="setup_p1")
            p2 = st.text_input("Repetir contraseña", type="password", key="setup_p2")
            if st.button("Crear propietario", type="primary", width="stretch"):
                if not u or not p1:
                    st.error("Completa usuario y contraseña.")
                elif p1 != p2:
                    st.error("Las contraseñas no coinciden.")
                else:
                    ok, msg = auth.add_user(u, p1, "propietario", nm)
                    if ok:
                        flash.exito(msg + "  Ahora inicia sesión.")
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.markdown("#### Iniciar sesión")
            u = st.text_input("Usuario", key="login_u")
            p = st.text_input("Contraseña", type="password", key="login_p")
            # v221: la persistencia por cookie (v107/v188) pasa a ser OPCIONAL. Sin
            # tildar (por defecto) la sesión dura solo esta pestaña; al tildar se guarda
            # la cookie de 7 días y no hay que volver a escribir usuario/contraseña en
            # este dispositivo. Déjalo sin marcar en equipos compartidos.
            st.checkbox("Mantener la sesión iniciada en este dispositivo",
                        value=False, key="login_remember",
                        help="Si lo activas, este dispositivo recordará tu sesión ~7 días y "
                             "no tendrás que volver a escribir usuario y contraseña. "
                             "Déjalo sin marcar en un equipo compartido o público.")

            def _do_login(force=False):
                res = auth.verify_login(u, p)
                if not res.get("ok"):
                    st.error(res.get("error", "Error de autenticación."))
                    return
                if force:
                    auth.end_session(res["usuario"], None)   # cerrar la otra sesión
                ses_ok, tok = auth.start_session(res["usuario"])
                if not ses_ok:
                    # Solo es "sesión ocupada" cuando hay OTRA sesión de verdad;
                    # si la hoja no respondió, ofrecer "cerrar la otra sesión"
                    # mentiría (no hay ninguna que cerrar) y no arreglaría nada.
                    if tok == auth.SESION_OCUPADA:
                        st.session_state["_blocked_user"] = res["usuario"]
                    else:
                        st.session_state.pop("_blocked_user", None)
                    st.error(f":material/lock: {tok}")
                    return
                st.session_state.pop("_blocked_user", None)
                st.session_state["auth"] = {
                    "usuario": res["usuario"], "rol": res["rol"],
                    "nombre": res["nombre"], "grupo": res.get("grupo", ""),
                    "token": tok,
                }
                st.session_state["_hb_last"] = time.time()
                # v222: marcar si pidió recordar la sesión. La cookie NO se escribe aquí
                # (el st.rerun de abajo descartaría el componente); la escribe
                # render_user_bar en el próximo run (un render que TERMINA). Sin tildar →
                # sin cookie → la sesión dura solo la pestaña.
                st.session_state["_remember_session"] = bool(
                    st.session_state.get("login_remember", False))
                st.rerun()

            if st.button("Iniciar sesión", type="primary", width="stretch"):
                _do_login(force=False)

            if st.session_state.get("_blocked_user"):
                st.caption("Si eres **tú** y dejaste la sesión abierta en otro dispositivo, "
                           "puedes cerrarla e iniciar aquí.")
                if st.button(":material/lock_open: Cerrar la otra sesión e iniciar aquí",
                             width="stretch"):
                    _do_login(force=True)
    return False


def render_user_bar():
    """Usuario logueado + grupo + botón salir (sidebar)."""
    a = st.session_state.get("auth", {})
    # v222: (re)escribir la cookie PERSISTENTE si el usuario pidió recordar la sesión.
    # Va AQUÍ (render que TERMINA, en el sidebar de cada página logueada), no en
    # _do_login (que hace st.rerun y descartaría el componente). Idempotente y rolling.
    if a and st.session_state.get("_remember_session"):
        try:
            from core import session_cookie
            session_cookie.save(a.get("usuario", ""), a.get("token", ""))
        except Exception:
            pass
    rol_lbl = {"propietario": ":material/shield_person: Propietario",
               "administrador": ":material/manage_accounts: Administrador",
               "campo": ":material/engineering: Campo"}.get(a.get("rol"), a.get("rol", ""))
    grupo = a.get("grupo") or ("todos" if a.get("rol") == "propietario" else "—")
    st.markdown(f"**{a.get('nombre','')}**  \n{rol_lbl}  \n:material/business: {grupo}")
    if st.button(":material/logout: Cerrar sesión", width="stretch", key="logout_btn"):
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
        st.session_state["_no_cookie_restore"] = True   # no auto-restaurar tras salir (v188)
        st.session_state.pop("_remember_session", None)  # v222: dejar de escribir la cookie
        st.rerun()


# ════════════════════════════════════════════════════════════
# PANEL DEL PROPIETARIO — grupos + todos los usuarios
# ════════════════════════════════════════════════════════════
def _owner_grupos():
    grupos = auth.list_groups()
    if grupos:
        st.dataframe(pd.DataFrame(grupos), hide_index=True, width="stretch")
    else:
        st.info("Aún no hay grupos. Crea el primero abajo.")
    with st.form("form_grupo", clear_on_submit=True):
        gn = st.text_input("Nombre del grupo (empresa cliente)")
        gd = st.text_input("Descripción (opcional)")
        if st.form_submit_button(":material/add: Crear grupo"):
            ok, msg = auth.add_group(gn, gd)
            (flash.exito if ok else st.error)(msg)
            if ok: st.rerun()

    # ── Libro de Google propio de cada cliente (v359) ──
    # Aislamiento de datos: cada empresa puede vivir en su propio fichero, en vez de
    # compartirlo separada solo por una columna `Grupo`.
    if grupos:
        with st.expander("Libro de datos de cada cliente", icon=":material/menu_book:"):
            st.caption("Cada empresa cliente puede tener su **propio archivo de Google "
                       "Sheets**, para que sus datos no compartan fichero con los de "
                       "otra. Vacío = usa el libro maestro.")
            _gl = ui.elegir("Grupo", [g["Grupo"] for g in grupos], key="gsheet_sel",
                            vacio="— elige un grupo —")
            if _gl:
                _sid_now = auth.group_sheet_id(_gl)
                st.markdown(":material/info: Crea una hoja de cálculo en blanco, "
                            "**compártela como editor** con la cuenta de servicio de la "
                            "app, y pega aquí su enlace o su ID.")
                _nuevo = st.text_input("Enlace o ID del libro", value=_sid_now,
                                       key="gsheet_val",
                                       placeholder="https://docs.google.com/spreadsheets/d/…")
                _c1, _c2 = st.columns(2)
                if _c1.button(":material/link: Guardar enlace", key="gsheet_save",
                              width="stretch"):
                    ok, msg = auth.set_group_sheet_id(_gl, _nuevo)
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()
                if _sid_now and _c2.button(":material/link_off: Volver al maestro",
                                           key="gsheet_del", width="stretch"):
                    ok, msg = auth.set_group_sheet_id(_gl, "")
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()
                if _sid_now:
                    st.success(":material/check_circle: **" + _gl + "** usa su propio "
                               "libro. `Login`, `Grupos` y `Rieles` siguen en el maestro: "
                               "son el registro de la app, no datos suyos.")
            # ⚠️ El límite se DICE. Un consolidado al que le faltan clientes sin avisar
            # es peor que no tenerlo (ver v359).
            _fuera = auth.grupos_con_libro_propio()
            if _fuera:
                st.warning(":material/warning: Con clientes en libros aparte, los "
                           "**resúmenes consolidados del propietario** todavía solo "
                           "cuentan los del maestro. Fuera del consolidado: **"
                           + ", ".join(_fuera) + "**. Cada cliente sí ve lo suyo completo.")

    # ── Zona horaria por grupo (v173) ──
    # Define en qué hora LOCAL se graban los registros de cada grupo (cada empresa
    # puede estar en otro país). Sin fijar → clock.DEFAULT_TZ.
    if grupos:
        with st.expander("Zona horaria de cada grupo", icon=":material/schedule:"):
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
                if st.button(":material/save: Guardar zona", key="tz_save"):
                    ok, msg = auth.set_group_timezone(gzsel, znew)
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()

    # ── Margen de facturación por defecto por grupo (v257) ──
    if grupos:
        with st.expander("Margen de facturación por defecto", icon=":material/trending_up:"):
            st.caption("Ganancia (%) sobre la mano de obra que se cobra al cliente. Cada proyecto "
                       "puede sobrescribirlo (✏️ Datos). Base de la 'tarifa de venta' y la rentabilidad.")
            gmsel = ui.elegir("Grupo", [g["Grupo"] for g in grupos], key="mg_g_sel",
                              vacio="— elige un grupo —")
            if gmsel:
                def _f_mg(v):
                    try:
                        return float(str(v).replace(",", ".") or 0)
                    except Exception:
                        return 0.0
                _curm = next((_f_mg(g.get("MargenDefault")) for g in grupos if g["Grupo"] == gmsel), 0.0)
                mnew = st.number_input("Margen por defecto (%)", min_value=0.0, max_value=500.0,
                                       step=1.0, value=_curm, key="mg_val")
                if st.button(":material/save: Guardar margen", key="mg_save"):
                    ok, msg = auth.set_group_margin_default(gmsel, mnew)
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()

    # ── Impuesto de facturación por defecto (GST/IVA) por grupo (v258) ──
    if grupos:
        with st.expander("Impuesto de facturación por defecto (GST/IVA)", icon=":material/receipt_long:"):
            st.caption("Se aplica por defecto a las facturas nuevas; editable por factura. "
                       "Australia = 10 (GST).")
            gtsel = ui.elegir("Grupo", [g["Grupo"] for g in grupos], key="tx_g_sel",
                              vacio="— elige un grupo —")
            if gtsel:
                def _f_tx(v):
                    try:
                        return float(str(v).replace(",", ".") or 0)
                    except Exception:
                        return 0.0
                _curt = next((_f_tx(g.get("ImpuestoDefault")) for g in grupos if g["Grupo"] == gtsel), 0.0)
                tnew = st.number_input("Impuesto por defecto (%)", min_value=0.0, max_value=100.0,
                                       step=1.0, value=_curt, key="tx_val")
                if st.button(":material/save: Guardar impuesto", key="tx_save"):
                    ok, msg = auth.set_group_tax_default(gtsel, tnew)
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()

    # ── Nómina: super y retención por defecto por grupo (v260) ──
    if grupos:
        with st.expander("Nómina: super y retención por defecto", icon=":material/payments:"):
            st.caption("Se precargan al generar una nómina; editables por nómina. "
                       "Australia: super ~11.5%. No es cálculo fiscal certificado.")
            gnsel = ui.elegir("Grupo", [g["Grupo"] for g in grupos], key="nomcfg_g_sel",
                              vacio="— elige un grupo —")
            if gnsel:
                def _f_n(v, dflt):
                    s = str(v).strip()
                    if s == "":
                        return dflt
                    try:
                        return float(s.replace(",", "."))
                    except Exception:
                        return dflt
                _g = next((g for g in grupos if g["Grupo"] == gnsel), {})
                nc1, nc2 = st.columns(2)
                _sup = nc1.number_input("Superannuation % (aporte)", min_value=0.0, max_value=100.0,
                                        step=0.5, value=_f_n(_g.get("SuperDefault"), 11.5), key="nom_supdef")
                _ret = nc2.number_input("Retención de impuesto % (deducción)", min_value=0.0, max_value=100.0,
                                        step=1.0, value=_f_n(_g.get("RetencionDefault"), 0.0), key="nom_retdef")
                if st.button(":material/save: Guardar nómina", key="nomcfg_save"):
                    ok1, _m1 = auth.set_group_num_setting(gnsel, "SuperDefault", _sup)
                    ok2, _m2 = auth.set_group_num_setting(gnsel, "RetencionDefault", _ret)
                    if ok1 and ok2:
                        flash.exito("Configuración de nómina actualizada.")
                        st.rerun()
                    else:
                        st.error(_m1 if not ok1 else _m2)

    if grupos:
        gsel = ui.elegir("Eliminar grupo", [g["Grupo"] for g in grupos],
                         key="del_g_sel", vacio="— ningún grupo —")
        if gsel:
            _ok_del = ui.confirmar_borrado("del_g_ok",
                                           f"Confirmo eliminar el grupo **{gsel}**")
            if st.button(":material/delete: Eliminar grupo", key="del_g_btn", disabled=not _ok_del):
                ok, msg = auth.delete_group(gsel)
                (flash.exito if ok else st.error)(msg)
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
                     else ("sí" if (str(u.get("Email", "")).strip()
                                    and str(u.get("TelegramChatID", "")).strip())
                           else "falta"))
            _rows.append({"Usuario": u.get("Usuario", ""), "Nombre": u.get("Nombre", ""),
                          "Rol": u.get("Rol", ""), "Grupo": u.get("Grupo", "") or "—",
                          "Activo": u.get("Activo", "SI"),
                          "Email": u.get("Email", "") or "—", "Contacto": _cont})
        st.dataframe(pd.DataFrame(_rows), hide_index=True, width="stretch")
        _faltan = [u["Usuario"] for u in users
                   if str(u.get("Rol", "")).lower() == "campo"
                   and not (str(u.get("Email", "")).strip()
                            and str(u.get("TelegramChatID", "")).strip())]
        if _faltan:
            st.warning(":material/warning: Campo sin contacto completo (no pueden usar la app): "
                       + ", ".join(_faltan))

    # ── Crear usuario (rol + grupo) ──
    grupo_opts = [""] + [g["Grupo"] for g in auth.list_groups()]
    with st.expander("Crear usuario", icon=":material/person_add:"):
        with st.form("form_user", clear_on_submit=True):
            u  = st.text_input("Usuario")
            nm = st.text_input("Nombre")
            rl = st.selectbox("Rol", auth.ROLES)
            gr = st.selectbox("Grupo", grupo_opts,
                              help="Propietario puede ir sin grupo; admin y campo requieren grupo.")
            pw = st.text_input("Contraseña", type="password")
            em = st.text_input(":material/mail: Email (obligatorio para campo)")
            if st.form_submit_button("Crear usuario"):
                if rl == "campo" and not em.strip():
                    st.error("El email es obligatorio para usuarios de campo.")
                else:
                    ok, msg = auth.add_user(u, pw, rl, nm, gr)
                    if ok and em.strip():
                        auth.set_contact(u, email=em)
                    (flash.exito if ok else st.error)(msg)
                    if ok: st.rerun()

    # ── Gestionar un usuario: ficha 360° (una sola selección) ──
    if users:
        st.markdown("#### :material/manage_accounts: Gestionar un usuario")
        _gf = ui.elegir("Filtrar por grupo", [g["Grupo"] for g in auth.list_groups()],
                        key="ow_ficha_gfil", vacio="— todos los grupos —")
        _cands = [u for u in users if (not _gf or str(u.get("Grupo", "")) == _gf)]
        _map = {f"{u['Nombre'] or u['Usuario']} ({u['Usuario']}) · {u.get('Grupo') or 'sin grupo'}": u
                for u in _cands}
        _elegido = ui.elegir("Usuario", _map, key="ow_fichasel", vacio="— elige un usuario —")
        if _elegido:
            st.markdown("---")
            # ⚠️ v379: la ficha muestra el TRABAJO de esa persona (horas, recibos,
            # proyectos, credenciales), que viven en el libro de SU grupo (v359). La
            # sesión del propietario no tiene grupo, así que sin declarar el ámbito
            # esos bloques salían vacíos. `Login` es global y se lee igual.
            from core import tenant as _tnt
            with _tnt.como_grupo(_elegido.get("Grupo", "")):
                _ficha_usuario(_elegido, _elegido.get("Grupo", ""),
                               owner=True, sel_key="ow_fichasel")


def render_owner_seccion(sec: str):
    """Despacho de UNA sub-sección de Administración (v298).

    Extraído de `render_owner_panel` para que la shell nueva (`home_ui`) lo use
    con su propio menú, sin duplicar el if/elif en dos sitios — dos mecanismos
    vivos para lo mismo es lo que v140 dejó como regla que no se repite.
    Los IDs conservan el emoji: son el identificador que usan los deep-links
    (p. ej. `survey_ui` escribe `owner_sec = "📁 Proyectos"`).
    """
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
    st.markdown("#### :material/public: Resumen de todos los grupos")
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
        "Retraso": d["retrasos"], "Alarmas": d["alarmas"],
        "Vencidos": d["vencidos"], "Credenciales": d["cred_venc"],
        "Sobre pres.": d["sobre_presupuesto"],
    } for d in data]), hide_index=True, width="stretch")
    _urg = [d for d in data if d["pendientes"]]
    if _urg:
        st.warning("Grupos con pendientes: " + ", ".join(d["grupo"] for d in _urg))
    else:
        st.success("Ningún grupo tiene pendientes urgentes.")


def _owner_manuales():
    """Banco de manuales para el agente de IA: subir/quitar (self-service)."""
    from core import manuals
    st.markdown("#### :material/menu_book: Banco de manuales del asistente")
    st.caption("El asistente de IA consulta estos manuales para responder dudas técnicas de "
               "instalación y **cita la fuente** (manual · sección · página).")

    # Pre-cargados (repo, solo lectura)
    pre = manuals.repo_manual_names()
    if pre:
        st.markdown("**Pre-cargados** (incluidos en la app):")
        for nm in pre:
            st.markdown(f"- :material/menu_book: {nm}")

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
        } for r in ups]), hide_index=True, width="stretch")
        with st.expander("Quitar un manual", icon=":material/delete:"):
            opciones = {f"{r.get('Nombre')}  ·  {r.get('Fecha')}": r.get("ID") for r in ups}
            _mid = ui.elegir("Manual", opciones, key="man_del_sel",
                             vacio="— ningún manual —")
            if _mid:
                _ok_del = ui.confirmar_borrado("man_del_ok",
                                               "Confirmo eliminar este manual")
                if st.button(":material/delete: Eliminar", key="man_del_btn", disabled=not _ok_del):
                    if manuals.delete_manual(_mid):
                        flash.exito("Manual eliminado.")
                        st.rerun()
                    else:
                        st.error("No se pudo eliminar.")
    else:
        st.info("Aún no has subido manuales. Agrega el primero abajo.")

    with st.expander("Subir manual", icon=":material/upload_file:", expanded=not ups):
        st.caption("Acepta un PDF con texto (no escaneado) o un ZIP con varios PDFs. "
                   "Evita PDFs enormes (>50 MB): se procesan en el navegador.")
        up = st.file_uploader("Archivo (PDF o ZIP)", type=["pdf", "zip"], key="man_up_file")
        nombre = st.text_input("Nombre del manual (ej. 'KONE MonoSpace')", key="man_up_name")
        if st.button(":material/upload: Procesar y guardar", key="man_up_btn", disabled=up is None):
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
                    flash.exito(f"Manual «{nm}» agregado: {n} fragmentos indexados.")
                    st.rerun()


def _owner_rieles():
    """Catálogo de rieles: referencia → medidas (para autocompletar RAIL desde el plano)."""
    from core import rails
    st.markdown("#### :material/train: Catálogo de rieles")
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
        } for r in data]), hide_index=True, width="stretch")
    else:
        st.info("Catálogo vacío. Agrega el primer riel abajo.")

    with st.expander("Agregar riel", icon=":material/add_circle:", expanded=not data):
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
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()

    if data:
        with st.expander("Editar / eliminar riel", icon=":material/edit:"):
            refs = [r.get("Referencia") for r in data]
            sel  = st.selectbox("Referencia", refs, key="riel_sel")
            _cur = rails.get_rail(sel) or {}
            ec1, ec2 = st.columns(2)
            el = ec1.number_input("Altura diente desde espalda (RAIL)", min_value=0.0, step=0.5,
                                  value=float(_cur.get("altura") or 0.0), key="riel_el")
            ea = ec2.number_input("Ancho diente", min_value=0.0, step=0.5,
                                  value=float(_cur.get("ancho") or 0.0), key="riel_ea")
            b1, b2 = st.columns(2)
            if b1.button(":material/save: Guardar", key="riel_save"):
                ok, msg = rails.update_riel(sel, ea, el)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
            if b2.button(":material/delete: Eliminar", key="riel_del"):
                ok, msg = rails.delete_riel(sel)
                (flash.exito if ok else st.error)(msg)
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
    chips = [(":green[:material/check_circle:] Activo" if activo else ":red[:material/cancel:] Inactivo"),
             (":material/schedule: Fichando ahora" if fichando else ""),
             ((":green[:material/contact_page:] Contacto OK" if contacto_ok else ":orange[:material/warning:] Sin contacto")
              if es_campo else "")]
    st.markdown(f"**{u.get('Nombre') or sel}**  ·  _{u['Rol']}_  ·  "
                + "  ·  ".join(c for c in chips if c))

    # v237: format_func muestra iconos Material; las OPCIONES siguen siendo el ID (emoji)
    # → el match de abajo (if _sec == "🔑 Acceso"…) no cambia.
    _sec = st.radio("Sección del usuario",
                    ["🔑 Acceso", "📇 Contacto", "🎫 Credenciales", "📊 Su trabajo", "🗑"],
                    format_func=lambda o: {"🔑 Acceso": ":material/key: Acceso",
                                           "📇 Contacto": ":material/contact_page: Contacto",
                                           "🎫 Credenciales": ":material/badge: Credenciales",
                                           "📊 Su trabajo": ":material/work: Su trabajo",
                                           "🗑": ":material/delete:"}.get(o, o),
                    horizontal=True, key=f"{k}_sec", label_visibility="collapsed")

    if _sec == "🔑 Acceso":
        _a1, _a2 = st.columns(2)      # v227: contraseña | tarifa lado a lado
        with _a1:
            np_ = st.text_input("Nueva contraseña", type="password", key=f"{k}_np")
            if st.button("Cambiar contraseña", key=f"{k}_chp", width="stretch"):
                if np_:
                    ok, msg = auth.set_password(sel, np_); (st.success if ok else st.error)(msg)
                else:
                    st.error("Escribe la nueva contraseña.")
        with _a2:
            tar = st.number_input(":material/payments: Tarifa por hora", min_value=0.0, step=1.0,
                                  value=float(str(u.get("TarifaHora", "") or 0).replace(",", ".") or 0),
                                  key=f"{k}_tar", help="Para costear la mano de obra.")
            if st.button("Guardar tarifa", key=f"{k}_savetar", width="stretch"):
                ok, msg = auth.set_rate(sel, tar); (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
        if owner:   # el propietario también reasigna rol y grupo (v184)
            _gopts = [""] + [g["Grupo"] for g in auth.list_groups()]
            _rc, _gc = st.columns(2)
            _rcur = str(u.get("Rol", "") or "campo")
            _nrol = _rc.selectbox("Rol", auth.ROLES,
                                  index=auth.ROLES.index(_rcur) if _rcur in auth.ROLES else 0,
                                  key=f"{k}_rol")
            if _rc.button("Aplicar rol", key=f"{k}_chrol"):
                ok, msg = auth.set_role(sel, _nrol); (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
            _gcur = str(u.get("Grupo", "") or "")
            _ngrp = _gc.selectbox("Grupo", _gopts,
                                  index=_gopts.index(_gcur) if _gcur in _gopts else 0,
                                  key=f"{k}_grp")
            if _gc.button("Aplicar grupo", key=f"{k}_chgrp"):
                ok, msg = auth.set_group(sel, _ngrp); (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
        if activo:
            if st.button(":material/block: Desactivar (no podrá entrar)", key=f"{k}_de",
                         width="stretch"):
                ok, msg = auth.set_active(sel, False); (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
        else:
            if st.button(":material/check_circle: Activar", key=f"{k}_act", width="stretch"):
                ok, msg = auth.set_active(sel, True); (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()

    elif _sec == "📇 Contacto":
        if not es_campo:
            st.caption("El contacto (email + Telegram) solo es obligatorio para "
                       "usuarios de campo. Puedes registrarlo igual.")
        elif not contacto_ok:
            st.warning(":material/warning: Sin contacto completo **no puede usar la app** y no recibe "
                       "asignaciones ni inducciones.")
        _contacto_uno(sel, key_prefix=f"{k}_cc")

    elif _sec == "🎫 Credenciales":
        render_credenciales(sel, grupo, editable=True, key_prefix=f"{k}_cr")

    elif _sec == "📊 Su trabajo":
        c1, c2, c3 = st.columns(3)
        try:
            gh = next((d for d in T.group_hours(grupo, days=None)
                       if d["usuario"] == sel), None)
        except Exception:
            gh = None
        _h = (gh["general"] + gh["proyecto"]) if gh else 0.0
        _pp = (gh.get("por_proyecto") or {}) if gh else {}
        rec = E.by_user(grupo, sel) if E.is_configured() else {"n": 0, "total": 0.0}
        asg = ([p for p in P.list_projects(grupo=grupo)
                if sel in [x.strip() for x in str(p.get("CampoAsignados", "")).split(";")]]
               if es_campo else [])
        c1.metric("Horas registradas", f"{_h:.1f}")
        c2.metric("Recibos cargados", rec["n"])
        c3.metric("Proyectos asignados", len(asg))

        # v227: proyectos asignados CLICKEABLES → abren el proyecto (elementos activos).
        if asg:
            st.markdown("**Asignado a** — toca para abrir:")
            _ac = st.columns(2)
            for _i, _p in enumerate(asg):
                if _ac[_i % 2].button(f":material/apartment: {_p.get('Nombre', '')}", key=f"{k}_gp_{_i}",
                                      width="stretch"):
                    st.session_state["_prjsel_pending"] = str(_p.get("ID", ""))
                    st.session_state["_admin_nav_pending"] = ("proyectos", "📊 Proyectos")
                    st.rerun()
        elif es_campo:
            st.caption("Sin proyectos asignados.")

        # Horas por proyecto de esta persona (del fichaje): dónde ha puesto su tiempo.
        if _pp:
            st.markdown("**Horas por proyecto:** "
                        + " · ".join(f"{_n} {_hh:.1f} h"
                                     for _n, _hh in sorted(_pp.items(), key=lambda x: -x[1])))
        if rec["n"]:
            st.caption(f"Ha cargado recibos por **${rec['total']:,.0f}** en total.")
        st.caption("Las horas y los recibos se gestionan desde :material/schedule: Fichaje y el detalle de "
                   "cada proyecto; aquí es un resumen.")

    else:  # 🗑 eliminar
        st.warning("Eliminar quita al usuario y su acceso. Sus fichajes, recibos y "
                   "credenciales ya registrados **no se borran** (quedan a su nombre).")
        if ui.confirmar_borrado(f"{k}_delok", f"Confirmo eliminar a «{sel}»"):
            if st.button("Eliminar definitivamente", key=f"{k}_del"):
                ok, msg = auth.delete_user(sel); (flash.exito if ok else st.error)(msg)
                if ok:
                    st.session_state.pop(sel_key, None)
                    st.rerun()


def _crear_usuario_form(grupo):
    """Alta de un usuario de campo (email obligatorio; el Telegram se vincula luego)."""
    with st.form("form_campo", clear_on_submit=True):
        u  = st.text_input("Usuario")
        nm = st.text_input("Nombre")
        pw = st.text_input("Contraseña", type="password")
        em = st.text_input(":material/mail: Email (OBLIGATORIO para campo)")
        st.caption("El Telegram se vincula en su ficha tras crearlo.")
        if st.form_submit_button("Crear"):
            if not em.strip():
                st.error("El email es obligatorio para usuarios de campo.")
            else:
                ok, msg = auth.add_user(u, pw, "campo", nm, grupo)
                if ok and em.strip():
                    auth.set_contact(u, email=em)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()


def _grupo_usuarios(grupo):
    """👷 Usuarios de campo (v226): panorama ACTIVO — fila de salud del equipo + tabla
    CLICKEABLE (al seleccionar una fila se abre la ficha 360° de esa persona, en vez del
    desplegable aparte que había). La ficha (`_ficha_usuario`) no cambia.
    El aviso de vencimientos ya NO se dispara aquí (desde v187 corre al login, app.py)."""
    from core import credentials as C
    users = auth.list_users(grupo=grupo)
    gente = [u for u in users if u["Rol"].lower() == "campo"]

    if not gente:
        st.info("Aún no tienes usuarios de campo. Crea el primero aquí.")
        with st.expander("Crear usuario de campo", icon=":material/person_add:", expanded=True):
            _crear_usuario_form(grupo)
        return

    # ── Ficha abierta (`_gu_open` = usuario) — fuente de verdad, para: (a) deep-links
    #    "Nombre (usuario)" desde la agenda de HOME (v200) y Finanzas·Horas (v215), que
    #    ya no encuentran el desplegable viejo; (b) que la ficha persista entre sus
    #    propios reruns; (c) cerrarla al eliminar al usuario. ──
    _deep = st.session_state.pop("gp_fichasel", None)
    if _deep:
        _du = (_deep.rsplit("(", 1)[-1].rstrip(")").strip()
               if "(" in str(_deep) else str(_deep).strip())
        st.session_state["_gu_open"] = _du
        st.session_state.pop("gu_tbl", None)      # descarta cualquier selección previa
    _op = st.session_state.get("_gu_open")
    if _op and not any(u["Usuario"] == _op for u in gente):   # p.ej. tras eliminarlo
        st.session_state.pop("_gu_open", None)
        st.session_state.pop("gu_tbl", None)

    # ── Salud de credenciales por usuario (1 lectura CACHEADA) ──
    _peor = {}          # {usuario_lower: 'vencido'|'por_vencer'|'vigente'}
    if C.is_configured():
        _rank = {"vencido": 3, "por_vencer": 2, "vigente": 1}
        try:
            for r in C.list_group(grupo):
                _uu = str(r.get("Usuario", "")).strip().lower()
                _s = C.status(r.get("Vencimiento"))
                if _s and _rank.get(_s, 0) > _rank.get(_peor.get(_uu, ""), 0):
                    _peor[_uu] = _s
        except Exception:
            pass
    _ico = {"vencido": "vencido", "por_vencer": "por vencer", "vigente": "vigente"}

    def _activo(u):
        return str(u.get("Activo", "")).strip().upper() in ("SI", "TRUE", "1", "SÍ")

    def _cont_ok(u):
        return bool(str(u.get("Email", "")).strip()
                    and str(u.get("TelegramChatID", "")).strip())

    # ── Fila de SALUD del equipo (de un vistazo) ──
    _nact = sum(1 for u in gente if _activo(u))
    _nsc = sum(1 for u in gente if not _cont_ok(u))
    _npv = sum(1 for u in gente if _peor.get(u["Usuario"].strip().lower()) == "por_vencer")
    _nvc = sum(1 for u in gente if _peor.get(u["Usuario"].strip().lower()) == "vencido")
    _linea = f":material/group: **{len(gente)}** personas · :green[:material/check_circle:] **{_nact}** activos"
    if _nsc:
        _linea += f" · :orange[:material/warning:] **{_nsc}** sin contacto"
    if _npv:
        _linea += f" · :orange[:material/schedule:] **{_npv}** cred. por vencer"
    if _nvc:
        _linea += f" · :red[:material/cancel:] **{_nvc}** cred. vencida(s)"
    st.markdown(_linea)

    # ⚠️ Quién RECIBE las alarmas del grupo y no tiene por dónde recibirlas. La
    # alarma se escribe igual, pero no sale de la app: solo la ve quien entre a
    # mirar — y desde v373 un control de seguridad en NO abre alarma. Va AQUÍ,
    # que es donde se carga el email, y no en el resumen del día (su rejilla es de
    # nueve indicadores fijos, v305). Estas cuentas no salen en la tabla de abajo:
    # son administradores y propietarios, no personal de campo.
    try:
        from core import admin_digest as _ad
        _sc = (_ad.group_digest(grupo) or {}).get("avisos_sin_canal") or []
    except Exception:
        _sc = []
    if _sc:
        st.warning(
            ":material/notifications_off: **Las alarmas de este grupo no le llegan a "
            f"{len(_sc)}** de sus destinatarios: "
            + ", ".join(f"**{x['usuario']}** ({x['rol']})" for x in _sc)
            + ". Sin email ni Telegram, el aviso queda dentro de la app. "
              "Se arregla cargándoles un email en su ficha.")

    # ── Tabla CLICKEABLE → abre la ficha de esa persona ──
    _rows = [{
        "Usuario": u["Usuario"], "Nombre": u["Nombre"] or u["Usuario"],
        "Activo": "sí" if _activo(u) else "no",
        "Contacto": "sí" if _cont_ok(u) else "falta",
        "Credenciales": _ico.get(_peor.get(u["Usuario"].strip().lower()), "—"),
        "Tarifa/h": u.get("TarifaHora", "") or "—",
    } for u in gente]
    _ev = st.dataframe(pd.DataFrame(_rows), hide_index=True, width="stretch",
                       on_select="rerun", selection_mode="single-row", key="gu_tbl")
    st.caption(":material/touch_app: Toca una fila para abrir y gestionar la ficha de esa persona.  "
               "Credenciales: vigente / por vencer / vencido / — sin registrar.")
    try:
        _sr = list(_ev.selection.rows)
    except Exception:
        _sr = []
    if _sr and _sr[0] < len(gente):
        st.session_state["_gu_open"] = gente[_sr[0]]["Usuario"]
    _op = st.session_state.get("_gu_open")
    _oi = next((i for i, u in enumerate(gente) if u["Usuario"] == _op), None) if _op else None
    if _oi is not None:
        st.markdown("---")
        # sel_key por defecto (gp_fichasel, ya popeado aquí): al eliminar deja `_gu_open`
        # apuntando al usuario borrado → el bloque de arriba cierra la ficha en el rerun.
        _ficha_usuario(gente[_oi], grupo)

    # ── Secundarios: matriz de credenciales + crear usuario ──
    if C.is_configured():
        try:
            tipos, filas = C.matrix(grupo)
            if tipos:
                with st.expander("Matriz de credenciales (usuarios × tickets)",
                                 icon=":material/table_chart:"):
                    st.caption("Credenciales: vigente / por vencer (≤30 d) / vencido / — no registrada")
                    st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
        except Exception:
            pass
    with st.expander("Crear usuario de campo", icon=":material/person_add:"):
        _crear_usuario_form(grupo)


