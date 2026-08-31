"""
UI de login, barra de usuario y paneles de gestión (propietario / administrador).
"""
import os

from core.i18n import t, etiqueta as _etq
import re
import time
from datetime import date
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
    em  = st.text_input(t(":material/mail: Email"), value=str(rec.get("Email", "")), key=f"{key_prefix}_em")
    if st.button(t("Save email"), key=f"{key_prefix}_emb"):
        ok, msg = auth.set_contact(sel, email=em)
        (flash.exito if ok else st.error)(msg)
        if ok:
            st.rerun()
    st.markdown(t("**:material/send: Telegram**"))
    tg = str(rec.get("TelegramChatID", "")).strip()
    if not notify.telegram_configured() or not notify.bot_username():
        # ⚠️ v368: antes esto era un callejón sin salida. Decía «no configurado» y ya:
        # ningún botón para vincular, y el usuario de campo quedaba bloqueado en la
        # entrada exigiéndosele justo esto. Ahora se dice que NO se le exige (el
        # bloqueo de `app.py` solo pide los canales que existen) y se ofrece la salida
        # manual, por si el chat_id se consiguió por otra vía.
        st.caption(t(":material/info: Telegram is not configured on this installation (the bot is missing from Secrets), so it is **not required** to sign in. Email is enough."))
        with st.expander(t("Enter the chat_id by hand"), icon=":material/edit:"):
            _man = st.text_input(t("Telegram chat ID"), value=tg, key=f"{key_prefix}_tgman",
                                 help=t("Only if you already have it another way. With no bot configured the app cannot send them anything."))
            if st.button(t("Save chat_id"), key=f"{key_prefix}_tgmanb"):
                ok, msg = auth.set_contact(sel, telegram=_man.strip())
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
    elif tg:
        st.success(t(":material/check_circle: Telegram linked."))
        if st.button(t("Unlink Telegram"), key=f"{key_prefix}_tgu"):
            auth.set_contact(sel, telegram="")
            st.rerun()
    else:
        bot  = notify.bot_username()
        code = re.sub(r"[^A-Za-z0-9_-]", "", sel) or "user"
        st.caption(t("1) The user opens the bot and presses **Start** (send them this link):"))
        st.code(f"https://t.me/{bot}?start={code}")
        st.caption(t("2) Once they have, press:"))
        if st.button(t(":material/link: Link this user's Telegram"), key=f"{key_prefix}_tgl"):
            cid = notify.telegram_find_chat_by_code(code)
            if cid:
                auth.set_contact(sel, telegram=cid)
                flash.exito(t(":material/check_circle: Telegram linked."))
                st.rerun()
            else:
                st.error(t("I could not find their message. Make sure they pressed Start and try again."))


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
        st.info(t("Credentials need Google Sheets configured."))
        return
    creds = C.list_for(usuario)
    if creds:
        # KPIs de un vistazo (v186): vigentes / por vencer / vencidas
        _sts = [C.status(r.get("Vencimiento")) for r in creds]
        k1, k2, k3, k4 = st.columns(4)
        k1.metric(t("Credentials"), len(creds))
        k2.metric(t(":material/check_circle: Valid"), sum(1 for s in _sts if s == "vigente"))
        k3.metric(t(":material/schedule: Expiring"), sum(1 for s in _sts if s == "por_vencer"))
        k4.metric(t(":material/cancel: Expired"), sum(1 for s in _sts if s == "vencido"))
        st.dataframe(pd.DataFrame([{
            "Tipo": r.get("Tipo"), "Número": r.get("Numero"), "Clase": r.get("Clase"),
            "Emisión": r.get("Emision") or "—", "Vence": r.get("Vencimiento") or "—",
            "Estado": C.status_label(r.get("Vencimiento")),
        } for r in creds]), hide_index=True, width="stretch")
        # Documentos adjuntos agrupados (antes: botones sueltos apilados bajo la tabla)
        _docs = [r for r in creds if str(r.get("DriveID", "")).strip()]
        if _docs:
            with st.expander(f":material/download: Documents ({len(_docs)})"):
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
        st.caption(t("No credentials recorded."))

    if not editable:
        return
    admin_usr = st.session_state.get("auth", {}).get("usuario", "")

    with st.expander(t("Add credential"), icon=":material/add_circle:"):
        # 'Tipo' va FUERA del form (v189): así, al cambiarlo, la app se re-renderiza
        # y podemos mostrar solo los campos que aplican — "especifica" para 'Otro' y
        # "Clase" solo para licencia de conducir. Dentro de un form no hay rerun hasta
        # el submit, así que ahí no se puede condicionar. El Tipo queda seleccionado
        # tras agregar (cómodo para cargar varias del mismo tipo).
        tipo = st.selectbox(t("Type"), C.CATALOGO, key=f"{key_prefix}_tipo")
        _es_otro = (tipo == "Otro")
        _es_lic  = (tipo == "Driver License")
        tipo_otro = (st.text_input(t("Specify the type"), key=f"{key_prefix}_tipootro")
                     if _es_otro else "")
        with st.form(f"{key_prefix}_add_{usuario}", clear_on_submit=True):
            if _es_lic:
                c1, c2 = st.columns(2)
                num   = c1.text_input(t("Number"))
                clase = c2.selectbox(t("Class (licence)"), C.CLASES_LICENCIA, key=f"{key_prefix}_clase")
            else:
                num   = st.text_input(t("Number"))
                clase = ""
            c3, c4 = st.columns(2)
            emi = _fecha_input(c3, "Emisión", key=f"{key_prefix}_emi")
            ven = _fecha_input(c4, "Expiry (blank if it does not expire)", key=f"{key_prefix}_ven")
            arch = st.file_uploader(t("Photo or document (optional)"),
                                    type=["pdf", "png", "jpg", "jpeg"], key=f"{key_prefix}_file")
            nota = st.text_input(t("Note"))
            if st.form_submit_button(t("Add")):
                _tp = tipo_otro.strip() if (_es_otro and tipo_otro.strip()) else tipo
                did, fname = "", ""
                if arch is not None:
                    fname = arch.name
                    did = C.upload_file(usuario, _tp, arch.name, arch.getvalue(),
                                        arch.type or "application/octet-stream")
                    if not did:
                        st.warning(t("The file could not be uploaded to Drive; everything else is saved."))
                ok, msg = C.add(usuario, grupo, t, num, clase, emi, ven, did, fname, nota, admin_usr)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()

    if creds:
        with st.expander(t("Edit / delete credential"), icon=":material/edit:"):
            idmap = {f"{r.get('Tipo')} · {r.get('Numero') or 's/n'} ({r.get('ID')})": r for r in creds}
            sel = st.selectbox(t("Credential"), list(idmap.keys()), key=f"{key_prefix}_esel")
            r = idmap[sel]
            _kid = str(r.get("ID", ""))
            c1, c2 = st.columns(2)
            enum = c1.text_input(t("Number"), value=r.get("Numero", ""), key=f"{key_prefix}_enum_{_kid}")
            even = _fecha_input(c2, "Expiry (blank if it does not expire)", r.get("Vencimiento", ""),
                                key=f"{key_prefix}_even_{_kid}")
            enota = st.text_input(t("Note"), value=r.get("Nota", ""), key=f"{key_prefix}_enota_{_kid}")
            b1, b2 = st.columns(2)
            if b1.button(t(":material/save: Save"), key=f"{key_prefix}_eupd"):
                ok, msg = C.update(r.get("ID"), {"Numero": enum, "Vencimiento": even, "Nota": enota,
                                                 "ActualizadoPor": admin_usr})
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
            if b2.button(t(":material/delete: Delete"), key=f"{key_prefix}_edel"):
                ok, msg = C.delete(r.get("ID"))
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()


def render_my_credentials():
    """Vista de solo lectura de las credenciales del usuario logueado."""
    a = st.session_state.get("auth", {})
    st.markdown(t("### :material/badge: My credentials"))
    st.caption(t("Your tickets and credentials as recorded by your administrator. Show them on site if you are asked for them."))
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
        "<p style='text-align:center;color:#5b6472;margin-top:-8px;font-size:16px;'>Lift installation management<br><span style='font-size:13px;color:#8b95a5;'>Projects · Crew · Costs · Technical tools</span></p>",
        unsafe_allow_html=True)

    # ⚠️ v365: los mensajes que sobrevivieron a un rerun también se pintan AQUÍ. El
    # login ocurre ANTES de la shell, así que sin esto el «propietario creado, ahora
    # inicia sesión» del bootstrap se perdería igual que antes.
    flash.mostrar()

    if not auth.is_configured():
        st.error(t(":material/lock: Sign-in is not connected to Google Sheets. Configure the Secrets (gcp_service_account + TIMECLOCK_SHEET_ID) in Streamlit Cloud."))
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
            st.info(t(":material/shield_person: **Initial setup** — create the owner account."))
            u  = st.text_input(t("Username"), key="setup_u")
            nm = st.text_input(t("Name"), key="setup_n")
            p1 = st.text_input(t("Password"), type="password", key="setup_p1")
            p2 = st.text_input(t("Repeat password"), type="password", key="setup_p2")
            if st.button(t("Create owner"), type="primary", width="stretch"):
                if not u or not p1:
                    st.error(t("Fill in username and password."))
                elif p1 != p2:
                    st.error(t("The passwords do not match."))
                else:
                    ok, msg = auth.add_user(u, p1, "propietario", nm)
                    if ok:
                        flash.exito(msg + "  Now sign in.")
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.markdown(t("#### Sign in"))
            u = st.text_input(t("Username"), key="login_u")
            p = st.text_input(t("Password"), type="password", key="login_p")
            # v221: la persistencia por cookie (v107/v188) pasa a ser OPCIONAL. Sin
            # tildar (por defecto) la sesión dura solo esta pestaña; al tildar se guarda
            # la cookie de 7 días y no hay que volver a escribir usuario/contraseña en
            # este dispositivo. Déjalo sin marcar en equipos compartidos.
            st.checkbox(t("Keep me signed in on this device"),
                        value=False, key="login_remember",
                        help=t("If you turn this on, this device will remember your session for about 7 days and you will not have to type your username and password again. Leave it unticked on a shared or public computer."))

            def _do_login(force=False):
                res = auth.verify_login(u, p)
                if not res.get("ok"):
                    st.error(res.get("error", "Authentication error."))
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

            if st.button(t("Sign in"), type="primary", width="stretch"):
                _do_login(force=False)

            if st.session_state.get("_blocked_user"):
                st.caption(t("If this is **you** and you left the session open on another device, you can close it and sign in here."))
                if st.button(t(":material/lock_open: Close the other session and sign in here"),
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
    if st.button(t(":material/logout: Sign out"), width="stretch", key="logout_btn"):
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
        st.info(t("No companies yet. Create the first one below."))
    with st.form("form_grupo", clear_on_submit=True):
        gn = st.text_input(t("Company name (client company)"))
        gd = st.text_input(t("Description (optional)"))
        if st.form_submit_button(t(":material/add: Create company")):
            ok, msg = auth.add_group(gn, gd)
            (flash.exito if ok else st.error)(msg)
            if ok: st.rerun()

    # ── Libro de Google propio de cada cliente (v359) ──
    # Aislamiento de datos: cada empresa puede vivir en su propio fichero, en vez de
    # compartirlo separada solo por una columna `Grupo`.
    if grupos:
        with st.expander(t("Each client's data workbook"), icon=":material/menu_book:"):
            st.caption(t("Each client company can have its **own Google Sheets file**, so its data does not share a file with anyone else's. Empty = it uses the master workbook."))
            _gl = ui.elegir(t("Company"), [g["Grupo"] for g in grupos], key="gsheet_sel",
                            vacio="— elige un grupo —")
            if _gl:
                _sid_now = auth.group_sheet_id(_gl)
                st.markdown(t(":material/info: Create a blank spreadsheet, **share it as editor** with the app's service account, and paste its link or its ID here."))
                _nuevo = st.text_input(t("Workbook link or ID"), value=_sid_now,
                                       key="gsheet_val",
                                       placeholder="https://docs.google.com/spreadsheets/d/…")
                _c1, _c2 = st.columns(2)
                if _c1.button(t(":material/link: Save link"), key="gsheet_save",
                              width="stretch"):
                    ok, msg = auth.set_group_sheet_id(_gl, _nuevo)
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()
                if _sid_now and _c2.button(t(":material/link_off: Back to the master"),
                                           key="gsheet_del", width="stretch"):
                    ok, msg = auth.set_group_sheet_id(_gl, "")
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()
                if _sid_now:
                    st.success(":material/check_circle: **" + _gl + "** uses its own spreadsheet. `Login`, `Grupos` and `Rieles` stay in the master book: they are the app's own register, not that client's data.")
            # ⚠️ El límite se DICE. Un consolidado al que le faltan clientes sin avisar
            # es peor que no tenerlo (ver v359).
            _fuera = auth.grupos_con_libro_propio()
            if _fuera:
                st.warning(":material/warning: With clients in separate books, the **owner's consolidated summaries** still only count the ones in the master book. Left out of the consolidation: **"
                           + ", ".join(_fuera) + "**. Each client does see all of their own data.")

    # ── Zona horaria por grupo (v173) ──
    # Define en qué hora LOCAL se graban los registros de cada grupo (cada empresa
    # puede estar en otro país). Sin fijar → clock.DEFAULT_TZ.
    if grupos:
        with st.expander(t("Each company's time zone"), icon=":material/schedule:"):
            st.caption(t("The local time in which that company's records are written "
                         "(time clock, pre-start, alerts…). Not set = ")
                       + f"{clock.DEFAULT_TZ}.")
            _gz = {g["Grupo"]: (g.get("Zona") or "") for g in grupos}
            gzsel = ui.elegir(t("Company"), list(_gz.keys()), key="tz_g_sel", vacio="— elige un grupo —")
            if gzsel:
                _cur = _gz.get(gzsel) or clock.DEFAULT_TZ
                _opts = ["Australia/Sydney", "Australia/Brisbane", "Australia/Adelaide",
                         "Australia/Perth", "Australia/Darwin", "Pacific/Auckland",
                         "Europe/Madrid", "America/New_York", "America/Los_Angeles", "UTC"]
                if _cur not in _opts:
                    _opts = [_cur] + _opts
                znew = st.selectbox(t("Time zone (IANA)"), _opts, index=_opts.index(_cur),
                                    key="tz_z_sel")
                try:
                    from zoneinfo import ZoneInfo
                    from datetime import datetime as _dtn
                    st.caption(f"In **{znew}** it is now "
                               f"**{_dtn.now(ZoneInfo(znew)).strftime('%H:%M')}**.  "
                               f"(Company's current one: {_gz.get(gzsel) or 'not set'})")
                except Exception:
                    pass
                if st.button(t(":material/save: Save time zone"), key="tz_save"):
                    ok, msg = auth.set_group_timezone(gzsel, znew)
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()

    # ── Margen de facturación por defecto por grupo (v257) ──
    if grupos:
        with st.expander(t("Default invoicing margin"), icon=":material/trending_up:"):
            st.caption(t("Profit (%) on the labour charged to the client. Each project can override it (✏️ Data). It is the basis of the sell rate and of profitability."))
            gmsel = ui.elegir(t("Company"), [g["Grupo"] for g in grupos], key="mg_g_sel",
                              vacio="— elige un grupo —")
            if gmsel:
                def _f_mg(v):
                    try:
                        return float(str(v).replace(",", ".") or 0)
                    except Exception:
                        return 0.0
                _curm = next((_f_mg(g.get("MargenDefault")) for g in grupos if g["Grupo"] == gmsel), 0.0)
                mnew = st.number_input(t("Default margin (%)"), min_value=0.0, max_value=500.0,
                                       step=1.0, value=_curm, key="mg_val")
                if st.button(t(":material/save: Save margin"), key="mg_save"):
                    ok, msg = auth.set_group_margin_default(gmsel, mnew)
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()

    # ── Impuesto de facturación por defecto (GST/IVA) por grupo (v258) ──
    if grupos:
        with st.expander(t("Default invoicing tax (GST/VAT)"), icon=":material/receipt_long:"):
            st.caption(t("Applied by default to new invoices; editable per invoice. Australia = 10 (GST)."))
            gtsel = ui.elegir(t("Company"), [g["Grupo"] for g in grupos], key="tx_g_sel",
                              vacio="— elige un grupo —")
            if gtsel:
                def _f_tx(v):
                    try:
                        return float(str(v).replace(",", ".") or 0)
                    except Exception:
                        return 0.0
                _curt = next((_f_tx(g.get("ImpuestoDefault")) for g in grupos if g["Grupo"] == gtsel), 0.0)
                tnew = st.number_input(t("Default tax (%)"), min_value=0.0, max_value=100.0,
                                       step=1.0, value=_curt, key="tx_val")
                if st.button(t(":material/save: Save tax"), key="tx_save"):
                    ok, msg = auth.set_group_tax_default(gtsel, tnew)
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()

    # ── Nómina: super y retención por defecto por grupo (v260) ──
    if grupos:
        with st.expander(t("Payroll: default super and withholding"), icon=":material/payments:"):
            st.caption(t("These are preloaded when payroll is generated; editable per payslip. Australia: super ~11.5%. This is not a certified tax calculation."))
            gnsel = ui.elegir(t("Company"), [g["Grupo"] for g in grupos], key="nomcfg_g_sel",
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
                _sup = nc1.number_input(t("Superannuation % (employer contribution)"), min_value=0.0, max_value=100.0,
                                        step=0.5, value=_f_n(_g.get("SuperDefault"), 11.5), key="nom_supdef")
                _ret = nc2.number_input(t("Tax withholding % (deduction)"), min_value=0.0, max_value=100.0,
                                        step=1.0, value=_f_n(_g.get("RetencionDefault"), 0.0), key="nom_retdef")
                if st.button(t(":material/save: Save payroll settings"), key="nomcfg_save"):
                    ok1, _m1 = auth.set_group_num_setting(gnsel, "SuperDefault", _sup)
                    ok2, _m2 = auth.set_group_num_setting(gnsel, "RetencionDefault", _ret)
                    if ok1 and ok2:
                        flash.exito(t("Payroll settings updated."))
                        st.rerun()
                    else:
                        st.error(_m1 if not ok1 else _m2)

    if grupos:
        gsel = ui.elegir(t("Delete company"), [g["Grupo"] for g in grupos],
                         key="del_g_sel", vacio="— ningún grupo —")
        if gsel:
            _ok_del = ui.confirmar_borrado("del_g_ok",
                                           f"I confirm I want to delete the company **{gsel}**")
            if st.button(t(":material/delete: Delete company"), key="del_g_btn", disabled=not _ok_del):
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
            st.warning(":material/warning: Field users without full contact details (they cannot use the app): "
                       + ", ".join(_faltan))

    # ── Crear usuario (rol + grupo) ──
    grupo_opts = [""] + [g["Grupo"] for g in auth.list_groups()]
    with st.expander(t("Create user"), icon=":material/person_add:"):
        with st.form("form_user", clear_on_submit=True):
            u  = st.text_input(t("Username"))
            nm = st.text_input(t("Name"))
            rl = st.selectbox(t("Role"), auth.ROLES)
            gr = st.selectbox(t("Company"), grupo_opts,
                              help=t("An owner can have no company; admin and field users need one."))
            pw = st.text_input(t("Password"), type="password")
            em = st.text_input(t(":material/mail: Email (required for field users)"))
            if st.form_submit_button(t("Create user")):
                if rl == "campo" and not em.strip():
                    st.error(t("Email is required for field users."))
                else:
                    ok, msg = auth.add_user(u, pw, rl, nm, gr)
                    if ok and em.strip():
                        auth.set_contact(u, email=em)
                    (flash.exito if ok else st.error)(msg)
                    if ok: st.rerun()

    # ── Gestionar un usuario: ficha 360° (una sola selección) ──
    if users:
        st.markdown(t("#### :material/manage_accounts: Manage a user"))
        _gf = ui.elegir(t("Filter by company"), [g["Grupo"] for g in auth.list_groups()],
                        key="ow_ficha_gfil", vacio="— all companies —")
        _cands = [u for u in users if (not _gf or str(u.get("Grupo", "")) == _gf)]
        _map = {f"{u['Nombre'] or u['Usuario']} ({u['Usuario']}) · {u.get('Grupo') or "no company"}": u
                for u in _cands}
        _elegido = ui.elegir(t("Username"), _map, key="ow_fichasel", vacio="— choose a user —")
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
    st.markdown(t("#### :material/public: Summary of all companies"))
    from core import projects as _P
    if not _P.is_configured():
        st.warning(t("This needs Google Sheets configured."))
        return
    with st.spinner("Gathering the status of each company…"):
        data = admin_digest.owner_digest()
    if not data:
        st.info(t("No companies with data yet."))
        return
    st.dataframe(pd.DataFrame([{
        "Grupo": d["grupo"], "Activos": d["activos"], "Avance %": d["avance"],
        "Retraso": d["retrasos"], "Alarmas": d["alarmas"],
        "Vencidos": d["vencidos"], "Credenciales": d["cred_venc"],
        "Sobre pres.": d["sobre_presupuesto"],
    } for d in data]), hide_index=True, width="stretch")
    _urg = [d for d in data if d["pendientes"]]
    if _urg:
        st.warning("Companies with pending items: " + ", ".join(d["grupo"] for d in _urg))
    else:
        st.success(t("No company has anything urgent pending."))


def _owner_manuales():
    """Banco de manuales para el agente de IA: subir/quitar (self-service)."""
    from core import manuals
    st.markdown(t("#### :material/menu_book: The assistant's manual library"))
    st.caption(t("The AI assistant consults these manuals to answer technical installation questions and **cites the source** (manual · section · page)."))

    # Pre-cargados (repo, solo lectura)
    pre = manuals.repo_manual_names()
    if pre:
        st.markdown(t("**Preloaded** (shipped with the app):"))
        for nm in pre:
            st.markdown(f"- :material/menu_book: {nm}")

    if not manuals.storage_available():
        st.info(t("Uploading new manuals needs Google Drive + Sheets configured (the same secrets as documents and the time clock)."))
        return

    # Subidos por el propietario (Drive)
    st.markdown("---")
    st.markdown(t("**Uploaded by you:**"))
    ups = manuals.list_uploaded()
    if ups:
        st.dataframe(pd.DataFrame([{
            "Manual": r.get("Nombre"),
            "Fragmentos": r.get("NumFrags"),
            "Fecha": r.get("Fecha"),
            "Por": r.get("SubidoPor"),
        } for r in ups]), hide_index=True, width="stretch")
        with st.expander(t("Remove a manual"), icon=":material/delete:"):
            opciones = {f"{r.get('Nombre')}  ·  {r.get('Fecha')}": r.get("ID") for r in ups}
            _mid = ui.elegir(t("Manual"), opciones, key="man_del_sel",
                             vacio="— ningún manual —")
            if _mid:
                _ok_del = ui.confirmar_borrado("man_del_ok",
                                               t("I confirm I want to delete this manual"))
                if st.button(t(":material/delete: Delete"), key="man_del_btn", disabled=not _ok_del):
                    if manuals.delete_manual(_mid):
                        flash.exito(t("Manual deleted."))
                        st.rerun()
                    else:
                        st.error(t("It could not be deleted."))
    else:
        st.info(t("You have not uploaded any manuals yet. Add the first one below."))

    with st.expander(t("Upload manual"), icon=":material/upload_file:", expanded=not ups):
        st.caption(t("It accepts a PDF with text (not scanned) or a ZIP with several PDFs. Avoid huge PDFs (>50 MB): they are processed in the browser."))
        up = st.file_uploader(t("File (PDF or ZIP)"), type=["pdf", "zip"], key="man_up_file")
        nombre = st.text_input(t("Manual name (e.g. 'KONE MonoSpace')"), key="man_up_name")
        if st.button(t(":material/upload: Process and save"), key="man_up_btn", disabled=up is None):
            if up is None:
                st.error(t("Choose a file."))
            else:
                nm = nombre.strip() or up.name.rsplit(".", 1)[0]
                with st.spinner("Extrayendo texto e indexando…"):
                    n, err = manuals.add_manual(
                        up.getvalue(), up.name, nm,
                        subido_por=st.session_state.auth.get("usuario", ""))
                if err:
                    st.error(err)
                else:
                    flash.exito(f"Manual «{nm}» added: {n} fragments indexed.")
                    st.rerun()


def _owner_rieles():
    """Catálogo de rieles: referencia → medidas (para autocompletar RAIL desde el plano)."""
    from core import rails
    st.markdown(t("#### :material/train: Rail catalogue"))
    st.caption(t("When a drawing is loaded, the reader detects the **CAR GUIDE RAIL** code and fills in **RAIL** with the *tooth height from the back* from this table."))
    if not rails.is_configured():
        st.warning(t("This needs Google Sheets configured."))
        return
    data = rails.list_rieles()
    if data:
        st.dataframe(pd.DataFrame([{
            "Referencia": r.get("Referencia"),
            "Altura diente desde espalda (RAIL)": r.get("AlturaDiente"),
            "Ancho diente": r.get("AnchoDiente"),
        } for r in data]), hide_index=True, width="stretch")
    else:
        st.info(t("The catalogue is empty. Add the first rail below."))

    with st.expander(t("Add rail"), icon=":material/add_circle:", expanded=not data):
        with st.form("form_riel", clear_on_submit=True):
            ref = st.text_input(t("Reference (e.g. T75-3/B)"))
            rc1, rc2 = st.columns(2)
            alt = rc1.number_input(t("Tooth height from the back (RAIL) mm"),
                                   min_value=0.0, step=0.5)
            anc = rc2.number_input(t("Tooth width (mm)"), min_value=0.0, step=0.5)
            if st.form_submit_button(t("Add")):
                if not ref.strip():
                    st.error(t("The reference is required."))
                else:
                    ok, msg = rails.add_riel(ref.strip(), anc, alt)
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()

    if data:
        with st.expander(t("Edit / delete rail"), icon=":material/edit:"):
            refs = [r.get("Referencia") for r in data]
            sel  = st.selectbox(t("Reference"), refs, key="riel_sel")
            _cur = rails.get_rail(sel) or {}
            ec1, ec2 = st.columns(2)
            el = ec1.number_input(t("Tooth height from back (RAIL)"), min_value=0.0, step=0.5,
                                  value=float(_cur.get("altura") or 0.0), key="riel_el")
            ea = ec2.number_input(t("Tooth width"), min_value=0.0, step=0.5,
                                  value=float(_cur.get("ancho") or 0.0), key="riel_ea")
            b1, b2 = st.columns(2)
            if b1.button(t(":material/save: Save"), key="riel_save"):
                ok, msg = rails.update_riel(sel, ea, el)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
            if b2.button(t(":material/delete: Delete"), key="riel_del"):
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
             ((":green[:material/contact_page:] Contacto OK" if contacto_ok else ":orange[:material/warning:] No contact details")
              if es_campo else "")]
    st.markdown(f"**{u.get('Nombre') or sel}**  ·  _{_etq(str(u['Rol']))}_  ·  "
                + "  ·  ".join(c for c in chips if c))

    # v237: format_func muestra iconos Material; las OPCIONES siguen siendo el ID (emoji)
    # → el match de abajo (if _sec == "🔑 Acceso"…) no cambia.
    _sec = st.radio(t("User section"),
                    ["🔑 Acceso", "📇 Contacto", "🎫 Credenciales", "📊 Su trabajo", "🗑"],
                    format_func=lambda o: {"🔑 Acceso": ":material/key: Acceso",
                                           "📇 Contacto": ":material/contact_page: Contacto",
                                           "🎫 Credenciales": ":material/badge: Credentials",
                                           "📊 Su trabajo": ":material/work: Their work",
                                           "🗑": ":material/delete:"}.get(o, o),
                    horizontal=True, key=f"{k}_sec", label_visibility="collapsed")

    if _sec == "🔑 Acceso":
        _a1, _a2 = st.columns(2)      # v227: contraseña | tarifa lado a lado
        with _a1:
            np_ = st.text_input(t("New password"), type="password", key=f"{k}_np")
            if st.button(t("Change password"), key=f"{k}_chp", width="stretch"):
                if np_:
                    ok, msg = auth.set_password(sel, np_); (st.success if ok else st.error)(msg)
                else:
                    st.error(t("Type the new password."))
        with _a2:
            tar = st.number_input(t(":material/payments: Hourly rate"), min_value=0.0, step=1.0,
                                  value=float(str(u.get("TarifaHora", "") or 0).replace(",", ".") or 0),
                                  key=f"{k}_tar", help=t("Used to cost the labour."))
            if st.button(t("Save rate"), key=f"{k}_savetar", width="stretch"):
                ok, msg = auth.set_rate(sel, tar); (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
        # ⚠️ v433: la FECHA DE ALTA decide el año de vacaciones de esa persona (en AU
        # va por aniversario, no por año natural). Sin ella el saldo se estima por año
        # natural y la pantalla del campo lo dice, así que aquí se ve qué falta.
        _f1, _f2 = st.columns(2)
        with _f1:
            _fi = auth.fecha_ingreso(sel)
            _nf = st.date_input(t(":material/event_available: Start date at the company"),
                                value=_fi, key=f"{k}_fing", format="YYYY-MM-DD",
                                min_value=date(1990, 1, 1), max_value=date(2100, 12, 31),
                                help=t("Their leave year is counted from here."))
        with _f2:
            st.caption("")
            if st.button(t("Save start date"), key=f"{k}_savefing", width="stretch"):
                ok, msg = auth.set_fecha_ingreso(sel, _nf)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
        if not _fi:
            st.caption(t(":material/warning: With no start date their leave balance is counted by calendar year (1 Jan – 31 Dec), not from their anniversary."))
        if owner:   # el propietario también reasigna rol y grupo (v184)
            _gopts = [""] + [g["Grupo"] for g in auth.list_groups()]
            _rc, _gc = st.columns(2)
            _rcur = str(u.get("Rol", "") or "campo")
            _nrol = _rc.selectbox(t("Role"), auth.ROLES,
                                  index=auth.ROLES.index(_rcur) if _rcur in auth.ROLES else 0,
                                  key=f"{k}_rol")
            if _rc.button(t("Apply role"), key=f"{k}_chrol"):
                ok, msg = auth.set_role(sel, _nrol); (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
            _gcur = str(u.get("Grupo", "") or "")
            _ngrp = _gc.selectbox(t("Company"), _gopts,
                                  index=_gopts.index(_gcur) if _gcur in _gopts else 0,
                                  key=f"{k}_grp")
            if _gc.button(t("Apply company"), key=f"{k}_chgrp"):
                ok, msg = auth.set_group(sel, _ngrp); (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
        if activo:
            if st.button(t(":material/block: Deactivate (they will not be able to sign in)"), key=f"{k}_de",
                         width="stretch"):
                ok, msg = auth.set_active(sel, False); (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
        else:
            if st.button(t(":material/check_circle: Activate"), key=f"{k}_act", width="stretch"):
                ok, msg = auth.set_active(sel, True); (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()

    elif _sec == "📇 Contacto":
        if not es_campo:
            st.caption(t("Contact details (email + Telegram) are only required for field users. You can record them anyway."))
        elif not contacto_ok:
            st.warning(t(":material/warning: Without complete contact details they **cannot use the app** and receive no assignments or inductions."))
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
        # v422: **con las internas**. Esto es «dónde trabaja esta persona», y para
        # alguien de oficina su asignación permanente ES la oficina: sin ellas, su
        # ficha diría «0 proyectos asignados» teniendo su sitio asignado.
        asg = ([p for p in P.list_projects(grupo=grupo, incluir_internos=True)
                if sel in [x.strip() for x in str(p.get("CampoAsignados", "")).split(";")]]
               if es_campo else [])
        c1.metric(t("Hours recorded"), f"{_h:.1f}")
        c2.metric(t("Receipts uploaded"), rec["n"])
        c3.metric(t("Projects assigned"), len(asg))

        # v227: proyectos asignados CLICKEABLES → abren el proyecto (elementos activos).
        if asg:
            st.markdown(t("**Assigned to** — tap to open:"))
            _ac = st.columns(2)
            for _i, _p in enumerate(asg):
                if _ac[_i % 2].button(f":material/apartment: {_p.get('Nombre', '')}", key=f"{k}_gp_{_i}",
                                      width="stretch"):
                    st.session_state["_prjsel_pending"] = str(_p.get("ID", ""))
                    st.session_state["_admin_nav_pending"] = ("proyectos", "📊 Proyectos")
                    st.rerun()
        elif es_campo:
            st.caption(t("No projects assigned."))

        # Horas por proyecto de esta persona (del fichaje): dónde ha puesto su tiempo.
        if _pp:
            st.markdown("**Hours per project:** "
                        + " · ".join(f"{_n} {_hh:.1f} h"
                                     for _n, _hh in sorted(_pp.items(), key=lambda x: -x[1])))
        if rec["n"]:
            st.caption(f"They have uploaded receipts totalling **${rec['total']:,.0f}** in all.")
        st.caption(t("Hours and receipts are managed from :material/schedule: Time clock and each project's detail; this is a summary."))

    else:  # 🗑 eliminar
        st.warning(t("Deleting removes the user and their access. Their time entries, receipts and credentials already recorded **are not deleted** (they stay under their name)."))
        if ui.confirmar_borrado(f"{k}_delok", f"I confirm I want to delete «{sel}»"):
            if st.button(t("Delete permanently"), key=f"{k}_del"):
                ok, msg = auth.delete_user(sel); (flash.exito if ok else st.error)(msg)
                if ok:
                    st.session_state.pop(sel_key, None)
                    st.rerun()


def _crear_usuario_form(grupo):
    """Alta de un usuario de campo (email obligatorio; el Telegram se vincula luego)."""
    with st.form("form_campo", clear_on_submit=True):
        u  = st.text_input(t("Username"))
        nm = st.text_input(t("Name"))
        pw = st.text_input(t("Password"), type="password")
        em = st.text_input(t(":material/mail: Email (REQUIRED for field users)"))
        st.caption(t("Telegram is linked from their record once created."))
        if st.form_submit_button(t("Create")):
            if not em.strip():
                st.error(t("Email is required for field users."))
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
        st.info(t("You have no field users yet. Create the first one here."))
        with st.expander(t("Create field user"), icon=":material/person_add:", expanded=True):
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
    _linea = f":material/group: **{len(gente)}** people · :green[:material/check_circle:] **{_nact}** active"
    if _nsc:
        _linea += f" · :orange[:material/warning:] **{_nsc}** with no contact details"
    if _npv:
        _linea += f" · :orange[:material/schedule:] **{_npv}** cred. expiring"
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
            ":material/notifications_off: **This company's alerts do not reach "
            f"{len(_sc)}** of their recipients: "
            + ", ".join(f"**{x['usuario']}** ({_etq(str(x['rol']))})" for x in _sc)
            + ". With no email and no Telegram, the alert stays inside the app. Fix it by adding an email on their profile.")

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
    st.caption(t(":material/touch_app: Tap a row to open and manage that person's record.  Credentials: valid / expiring / expired / — not recorded."))
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
                with st.expander(t("Credentials matrix (users × tickets)"),
                                 icon=":material/table_chart:"):
                    st.caption(t("Credentials: valid / expiring (≤30 d) / expired / — not recorded"))
                    st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
        except Exception:
            pass
    with st.expander(t("Create field user"), icon=":material/person_add:"):
        _crear_usuario_form(grupo)


