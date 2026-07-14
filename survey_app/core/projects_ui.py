"""
UI del panel de administración de proyectos (rol administrador).
Navegación con st.radio (NO st.tabs) para evitar mezcla de contenido.
"""
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from core import projects as P
from core import auth
from core import drive_store
from core import notify
from core import alerts
from core.schedule import schedule_svg


def _alerts_section(pid, grupo, project_name="", allow_report=False):
    """Alarmas abiertas del proyecto + resolver; si allow_report, el campo puede reportar."""
    if not alerts.is_configured():
        return
    usuario = st.session_state.get("auth", {}).get("usuario", "")
    abiertas = alerts.list_alerts(pid, "abierta")
    st.markdown(f"**{'🔴 ' + str(len(abiertas)) if abiertas else '🔔'} Alarmas / avisos**")
    if abiertas:
        for al in abiertas:
            emo = "🔴" if str(al.get("Tipo")) == "problema" else "🔵"
            c = st.columns([6, 1])
            c[0].write(f"{emo} _{al.get('Fecha')}_ · **{al.get('CreadoPor')}**: {al.get('Mensaje')}")
            if c[1].button("✅", key=f"resolv_{al.get('ID')}", help="Marcar resuelta"):
                ok, msg = alerts.resolve_alert(al.get("ID"), usuario)
                if ok:
                    st.rerun()
                else:
                    st.error(msg)
    else:
        st.caption("Sin alarmas abiertas.")
    if allow_report:
        with st.expander("🔴 Reportar un problema al administrador"):
            msg = st.text_area("Describe el problema o inconveniente en obra", key=f"rep_{pid}")
            if st.button("Enviar alarma", key=f"repb_{pid}"):
                if not msg.strip():
                    st.error("Escribe el problema.")
                else:
                    with st.spinner("Enviando alarma..."):
                        ok, res = alerts.report_problem(pid, grupo, msg.strip(), usuario, project_name)
                    (st.success if ok else st.error)("Alarma enviada al administrador." if ok else res)
                    if ok:
                        st.rerun()


_ESTADO_EMOJI = {
    "Planificado": "🕓", "En progreso": "🚧", "Completado": "✅",
    "En pausa": "⏸", "Cancelado": "🚫",
}

# Documentos: tipos y permisos por rol
_DOC_TIPOS  = ["plano", "informe_cliente", "informe_admin", "matriz_survey",
               "foto", "certificado", "otro"]
_CAMPO_VER  = {"plano", "informe_cliente", "matriz_survey", "foto"}   # campo puede consultar
_CAMPO_SUBE = ["foto"]                                                # campo solo sube fotos
_DOC_ICON   = {"plano": "📐", "informe_cliente": "📄", "informe_admin": "📑",
               "matriz_survey": "📊", "foto": "📷", "certificado": "🏅", "otro": "📎"}


def _documentos_section(pid: str):
    """Sección 📎 Documentos con permisos por rol (leído de session_state.auth)."""
    st.markdown("**📎 Documentos**")
    if not drive_store.is_configured():
        st.caption("🔒 Almacenamiento en Drive no configurado (faltan los secrets `[gdrive]`).")
        return
    a = st.session_state.get("auth", {})
    rol, usuario = a.get("rol", ""), a.get("usuario", "")
    es_campo     = rol == "campo"
    ver_tipos    = _CAMPO_VER if es_campo else set(_DOC_TIPOS)
    sube_tipos   = _CAMPO_SUBE if es_campo else _DOC_TIPOS
    puede_borrar = rol in ("administrador", "propietario")

    docs = [d for d in P.list_documents(pid) if str(d.get("Tipo", "")) in ver_tipos]
    if docs:
        for d in docs:
            did = str(d.get("DriveID", ""))
            cols = st.columns([5, 2, 1] if puede_borrar else [6, 2])
            cols[0].write(f"{_DOC_ICON.get(str(d.get('Tipo')), '📎')} {d.get('Nombre')}  "
                          f"· _{d.get('Tipo')}_")
            try:
                cols[1].download_button("⬇️ Descargar", data=drive_store.download(did),
                                        file_name=str(d.get("Nombre")),
                                        key=f"dl_{pid}_{did}", use_container_width=True)
            except Exception:
                cols[1].caption("no disponible")
            if puede_borrar and cols[2].button("🗑", key=f"deld_{pid}_{did}",
                                               use_container_width=True):
                drive_store.delete(did)
                P.delete_document_record(pid, did)
                st.rerun()
    else:
        st.caption("Sin documentos todavía.")

    with st.expander("➕ Subir documento"):
        if es_campo:
            st.caption("Como usuario de campo, solo puedes subir **fotos**.")
        up   = st.file_uploader("Archivo", key=f"updoc_{pid}")
        tipo = st.selectbox("Tipo", sube_tipos, key=f"uptipo_{pid}")
        if st.button("Subir", key=f"upbtn_{pid}"):
            if up is None:
                st.error("Elige un archivo primero.")
            else:
                try:
                    fid = drive_store.upload(pid, up.name, up.getvalue(),
                                             up.type or "application/octet-stream")
                    P.add_document(pid, up.name, tipo, fid, usuario)
                    st.success("Documento subido.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo subir: {e}")


def _field_users(grupo):
    """Usuarios de campo del grupo (para asignar a un proyecto)."""
    try:
        return [u["Usuario"] for u in auth.list_users(grupo)
                if str(u.get("Rol", "")) == "campo"]
    except Exception:
        return []


def render_admin_projects(grupo: str):
    st.markdown(f"### 📁 Proyectos — {grupo}")
    if not P.is_configured():
        st.warning("La gestión de proyectos necesita Google Sheets configurado "
                   "(gcp_service_account + TIMECLOCK_SHEET_ID en los Secrets).")
        return

    sec = st.radio("Sección", ["📊 Proyectos", "🗂 Agrupaciones"],
                   horizontal=True, key="adminproj_sec", label_visibility="collapsed")
    st.markdown("---")
    if sec == "📊 Proyectos":
        _panel_proyectos(grupo)
    else:
        _panel_agrupaciones(grupo)


# ── Panel de proyectos ───────────────────────────────────────────
def _panel_proyectos(grupo: str):
    proys = P.list_projects(grupo=grupo)
    if not proys:
        st.info("Todavía no hay proyectos en este grupo. Los proyectos se crean desde "
                "la pestaña **Survey** con el botón **💾 Guardar como proyecto** "
                "(tras calcular).")
        return

    # Resumen de estado
    ags = {a["ID"]: a["Nombre"] for a in P.list_groupings(grupo=grupo)}
    horas = P.project_hours_bulk(grupo)   # 1 sola lectura del fichaje
    alarmas = alerts.open_counts_all() if alerts.is_configured() else {}
    rows = []
    for p in proys:
        est = str(p.get("Estado", ""))
        _na = alarmas.get(str(p.get("ID", "")), 0)
        rows.append({
            "ID":        p.get("ID"),
            "Proyecto":  p.get("Nombre"),
            "🔔":        f"🔴 {_na}" if _na else "",
            "Cliente":   p.get("Cliente"),
            "Estado":    f"{_ESTADO_EMOJI.get(est, '')} {est}".strip(),
            "Avance %":  P._num(p.get("Avance")),
            "Horas":     horas.get(str(p.get("Nombre", "")), 0.0),
            "Agrupación": ags.get(str(p.get("AgrupacionID", "")), ""),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Detalle / edición
    st.markdown("#### 🔎 Abrir proyecto")
    idmap = {f"{p.get('ID')} · {p.get('Nombre')}": p.get("ID") for p in proys}
    sel = st.selectbox("Proyecto", list(idmap.keys()), key="adminproj_sel")
    if sel:
        _detalle_proyecto(idmap[sel], grupo)


def _detalle_proyecto(pid: str, grupo: str = None):
    prj = P.get_project(pid)
    if not prj:
        st.error("Proyecto no encontrado.")
        return
    # El grupo se toma del propio proyecto (así el propietario puede abrir cualquiera)
    grupo = str(prj.get("Grupo", "")) or (grupo or "")

    avance = P._num(prj.get("Avance"))
    est    = str(prj.get("Estado", ""))
    c1, c2, c3 = st.columns(3)
    c1.metric("Estado", f"{_ESTADO_EMOJI.get(est,'')} {est}".strip())
    c2.metric("Avance", f"{avance:.0f}%")
    c3.metric("Horas trabajadas", f"{P.project_hours(prj.get('Nombre'), grupo):.1f}")
    st.progress(min(1.0, avance / 100.0))

    # ── Alarmas / avisos del proyecto ──
    _alerts_section(pid, grupo, prj.get("Nombre", ""), allow_report=False)

    # ── Cronograma: curva S planificada vs real ──
    ps = P.project_schedule(pid)
    if ps and ps["sched"].get("activities"):
        st.markdown("**📆 Cronograma — curva S planificada vs real**")
        st.caption("Naranja = planificada (original) · Verde = real (avance del campo) · "
                   "línea roja = HOY.")
        n = len(ps["sched"]["activities"])
        components.html(
            '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
            + schedule_svg(ps["sched"], real_curve=ps["real"],
                           today_day=ps["today_day"], avances=ps.get("avances"))
            + '</body></html>',
            height=int(280 + n * 22), scrolling=False,
        )

        # ── Proyección avance vs fecha (earned value) ──
        proj = ps.get("proj")
        if proj and proj.get("pv", 0) > 0:
            dv, dg = proj["desvio"], proj["dias_gap"]
            icon = "🟢" if dv >= 1 else ("🔴" if dv <= -1 else "🟡")
            st.markdown(f"**🔮 Proyección (avance vs fecha)**  {icon}")
            q1, q2, q3 = st.columns(3)
            q1.metric("Desvío hoy", f"{dv:+.0f}%",
                      help="Avance real − planificado a la fecha de hoy")
            q2.metric("Estado hoy",
                      "En fecha" if abs(dg) < 0.5
                      else f"{abs(dg):.0f} d {'retraso' if dg > 0 else 'adelanto'}")
            if proj["proj_dias"] is not None and proj["fecha_proj"]:
                q3.metric("Fin proyectado", proj["fecha_proj"].strftime("%d/%m/%Y"))
                pdi = proj["proj_dias"]
                fin = ("a tiempo" if abs(pdi) < 0.5
                       else f"**{abs(pdi):.0f} días de {'retraso' if pdi > 0 else 'adelanto'}**")
                st.caption(f"A este ritmo (SPI = {proj['spi']}) terminarías {fin}.  "
                           f"Real {proj['ev']:.0f}% vs planificado {proj['pv']:.0f}% "
                           f"al día {proj['today_day']} de {proj['total']}.")
            else:
                q3.metric("Fin proyectado", "—")
                st.caption(f"Real {proj['ev']:.0f}% vs planificado {proj['pv']:.0f}% "
                           f"al día {proj['today_day']} de {proj['total']}. Sin avance suficiente "
                           "para proyectar la fecha de fin.")

    # ── Editar datos ──
    with st.form(f"edit_{pid}"):
        st.markdown("**Datos del proyecto**")
        e1, e2 = st.columns(2)
        nombre   = e1.text_input("Nombre", value=prj.get("Nombre", ""))
        cliente  = e2.text_input("Cliente", value=prj.get("Cliente", ""))
        ubic     = e1.text_input("Ubicación", value=prj.get("Ubicacion", ""))
        modelo   = e2.text_input("Modelo", value=prj.get("Modelo", ""))
        ing      = e1.text_input("Ingeniero", value=prj.get("Ingeniero", ""))
        f_ini    = e2.text_input("Fecha inicio", value=prj.get("FechaInicio", ""))
        f_fin    = e1.text_input("Fecha fin estimada", value=prj.get("FechaFinEst", ""))

        campos_disp = _field_users(grupo)
        actuales = [x.strip() for x in str(prj.get("CampoAsignados", "")).split(";") if x.strip()]
        # opciones = union para no perder asignados que ya no estén en la lista
        opts = sorted(set(campos_disp) | set(actuales))
        asignados = st.multiselect("Usuarios de campo asignados", opts, default=actuales)

        ags = P.list_groupings(grupo=grupo)
        ag_opts = ["(ninguna)"] + [f"{a['ID']} · {a['Nombre']}" for a in ags]
        ag_cur  = str(prj.get("AgrupacionID", ""))
        ag_idx  = next((i for i, a in enumerate(ags) if a["ID"] == ag_cur), None)
        ag_sel  = st.selectbox("Agrupación", ag_opts,
                               index=(ag_idx + 1) if ag_idx is not None else 0)
        peso    = st.number_input("Peso en la agrupación", min_value=0.0, step=1.0,
                                  value=P._num(prj.get("PesoEnAgrupacion")))
        est_man = st.selectbox("Estado manual (override)", P.ESTADOS_MANUAL,
                               index=P.ESTADOS_MANUAL.index(str(prj.get("EstadoManual", "")))
                               if str(prj.get("EstadoManual", "")) in P.ESTADOS_MANUAL else 0)

        if st.form_submit_button("💾 Guardar cambios", use_container_width=True):
            ag_id = "" if ag_sel == "(ninguna)" else ag_sel.split(" · ")[0]
            P.update_project(pid, {   # todo en UNA escritura (batch) → sin rate limit
                "Nombre": nombre, "Cliente": cliente, "Ubicacion": ubic, "Modelo": modelo,
                "Ingeniero": ing, "FechaInicio": f_ini, "FechaFinEst": f_fin,
                "CampoAsignados": ";".join(asignados),
                "AgrupacionID": ag_id, "PesoEnAgrupacion": peso,
                "EstadoManual": est_man, "Estado": P.derive_estado(avance, est_man),
            })
            # Notificar a los usuarios de campo recién asignados
            nuevos = [x for x in asignados if x not in actuales]
            _sent = 0
            if nuevos:
                _info = {"Nombre": nombre, "Cliente": cliente, "Ubicacion": ubic,
                         "FechaInicio": f_ini, "FechaFinEst": f_fin}
                for un in nuevos:
                    try:
                        rr = notify.notify_assignment(un, _info)
                        if rr.get("email") or rr.get("telegram"):
                            _sent += 1
                    except Exception:
                        pass
            # Aviso de cambio al campo ya asignado (los nuevos ya recibieron la asignación)
            try:
                alerts.notify_change(pid, grupo, "Se actualizaron los datos del proyecto.",
                                     st.session_state.get("auth", {}).get("usuario", ""),
                                     [x for x in asignados if x not in nuevos], nombre)
            except Exception:
                pass
            st.toast("Cambios guardados." + (f"  📨 {_sent} notificado(s)." if _sent else ""))
            st.rerun()

    # helper: avisar al campo asignado de un cambio del admin
    _asig_now = [x.strip() for x in str(prj.get("CampoAsignados", "")).split(";") if x.strip()]
    def _aviso_cambio(txt):
        try:
            alerts.notify_change(pid, grupo, txt,
                                 st.session_state.get("auth", {}).get("usuario", ""),
                                 _asig_now, prj.get("Nombre", ""))
        except Exception:
            pass

    # ── Actividades: tabla EDITABLE (nombre/días/peso/orden); avance = campo ──
    st.markdown("**Actividades del cronograma** — tabla editable · el avance lo pone el campo")
    acts = P.list_activities(pid)
    if acts:
        _adf = pd.DataFrame([{
            "Orden": int(P._num(a.get("Orden"))),
            "Actividad": a.get("Nombre"),
            "Días": int(P._num(a.get("DuracionDias")) or 1),
            "Peso": P._num(a.get("Peso")),
            "Avance %": P._num(a.get("Avance")),
        } for a in acts])
        _edited = st.data_editor(
            _adf, use_container_width=True, hide_index=True, num_rows="fixed",
            key=f"acted_{pid}", disabled=["Avance %"],
            column_config={
                "Orden": st.column_config.NumberColumn("Orden", min_value=1, step=1,
                                                       help="Cambia el número para reordenar"),
                "Días":  st.column_config.NumberColumn("Días", min_value=1, step=1),
                "Peso":  st.column_config.NumberColumn("Peso", min_value=0.0, step=1.0,
                                                       help="Peso relativo (el % se calcula proporcional)"),
            })
        st.caption("Edita nombre, días, peso y el orden; el avance % es de solo lectura (lo actualiza el campo).")
        if st.button("💾 Guardar tabla de actividades", key=f"savetbl_{pid}"):
            edits = []
            for i, a in enumerate(acts):
                r = _edited.iloc[i]
                edits.append({"orden0": a.get("Orden"),
                              "Nombre": str(r["Actividad"]).strip(),
                              "DuracionDias": int(r["Días"]),
                              "Peso": float(r["Peso"]),
                              "Orden": int(r["Orden"])})
            ok, msg = P.save_activities(pid, edits)
            (st.success if ok else st.error)(msg)
            if ok:
                _aviso_cambio("Se actualizó la tabla de actividades del cronograma.")
                st.rerun()
    else:
        st.caption("Sin actividades registradas.")

    with st.expander("➕ Agregar / 🗑 eliminar actividad (recalcula el % automáticamente)"):
        with st.form(f"addact_{pid}", clear_on_submit=True):
            st.markdown("**➕ Agregar actividad**")
            an = st.text_input("Nombre")
            ac1, ac2 = st.columns(2)
            ad = ac1.number_input("Duración (días)", min_value=1, value=2, step=1)
            ap = ac2.number_input("Peso (relativo a las demás)", min_value=0.0, value=10.0, step=1.0)
            if st.form_submit_button("Agregar"):
                if not an.strip():
                    st.error("El nombre es obligatorio.")
                else:
                    ok, msg = P.add_activity(pid, an.strip(), ad, ap)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        _aviso_cambio(f"Se agregó la actividad: {an.strip()}.")
                        st.rerun()
        if acts:
            st.markdown("**🗑 Eliminar actividad**")
            _dmap = {f"{int(P._num(a.get('Orden')))} · {a.get('Nombre')}": a.get("Orden")
                     for a in acts}
            dsel = st.selectbox("Actividad a eliminar", list(_dmap.keys()), key=f"delact_{pid}")
            if st.button("Eliminar", key=f"delactb_{pid}"):
                ok, msg = P.delete_activity(pid, _dmap[dsel])
                (st.success if ok else st.error)(msg)
                if ok:
                    _aviso_cambio("Se eliminó una actividad del cronograma.")
                    st.rerun()

    # ── Documentos ──
    _documentos_section(pid)

    # ── Eliminar ──
    with st.expander("🗑 Eliminar proyecto"):
        st.warning("Esto elimina el proyecto y sus actividades. No se puede deshacer.")
        if st.button("Eliminar definitivamente", key=f"del_{pid}"):
            ok, msg = P.delete_project(pid)
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()


# ── Panel de agrupaciones ────────────────────────────────────────
def _panel_agrupaciones(grupo: str):
    ags = P.list_groupings(grupo=grupo)
    if ags:
        rows = []
        for a in ags:
            pr = P.grouping_progress(a["ID"])
            rows.append({
                "ID": a["ID"], "Agrupación": a["Nombre"],
                "Proyectos": pr["n_proyectos"], "Avance %": pr["avance"],
                "Descripción": a.get("Descripcion", ""),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No hay agrupaciones. Crea una para agrupar varios elevadores con pesos.")

    st.markdown("#### ➕ Nueva agrupación")
    with st.form("nueva_agr"):
        nom = st.text_input("Nombre de la agrupación")
        des = st.text_input("Descripción (opcional)")
        if st.form_submit_button("Crear agrupación"):
            if not nom.strip():
                st.error("El nombre es obligatorio.")
            else:
                ok, msg = P.create_grouping(grupo, nom.strip(), des.strip())
                (st.success if ok else st.error)(f"Agrupación creada ({msg})" if ok else msg)
                if ok:
                    st.rerun()

    if ags:
        st.markdown("#### 🗑 Eliminar agrupación")
        delmap = {f"{a['ID']} · {a['Nombre']}": a["ID"] for a in ags}
        d = st.selectbox("Agrupación", list(delmap.keys()), key="del_agr_sel")
        st.caption("Los proyectos no se borran; solo se desagrupan.")
        if st.button("Eliminar agrupación"):
            ok, msg = P.delete_grouping(delmap[d])
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()


# ── Panel del PROPIETARIO: todos los proyectos (todos los grupos) ──
def render_owner_projects():
    st.markdown("### 📁 Todos los proyectos")
    if not P.is_configured():
        st.warning("La gestión de proyectos necesita Google Sheets configurado.")
        return
    proys = P.list_projects()   # todos los grupos
    if not proys:
        st.info("Aún no hay proyectos en ningún grupo.")
        return
    ags = {a["ID"]: a["Nombre"] for a in P.list_groupings()}
    alarmas = alerts.open_counts_all() if alerts.is_configured() else {}
    rows = []
    for p in proys:
        est = str(p.get("Estado", ""))
        _na = alarmas.get(str(p.get("ID", "")), 0)
        rows.append({
            "ID":        p.get("ID"),
            "Grupo":     p.get("Grupo"),
            "Proyecto":  p.get("Nombre"),
            "🔔":        f"🔴 {_na}" if _na else "",
            "Cliente":   p.get("Cliente"),
            "Estado":    f"{_ESTADO_EMOJI.get(est, '')} {est}".strip(),
            "Avance %":  P._num(p.get("Avance")),
            "Horas":     P.project_hours(p.get("Nombre"), p.get("Grupo")),
            "Agrupación": ags.get(str(p.get("AgrupacionID", "")), ""),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("#### 🔎 Abrir proyecto")
    idmap = {f"{p.get('Grupo')} · {p.get('ID')} · {p.get('Nombre')}": p.get("ID") for p in proys}
    sel = st.selectbox("Proyecto", list(idmap.keys()), key="ownerproj_sel")
    if sel:
        _detalle_proyecto(idmap[sel])


# ── Pestaña del usuario de CAMPO: mis proyectos ──────────────────
def render_field_projects(usuario: str, grupo: str):
    st.markdown("### 📋 Mis proyectos")
    if not P.is_configured():
        st.warning("La gestión de proyectos necesita Google Sheets configurado.")
        return

    proys = P.list_projects_for_field(usuario, grupo=grupo)
    if not proys:
        st.info("No tienes proyectos asignados todavía. El administrador te asigna a un proyecto.")
        return

    idmap = {f"{p.get('Nombre')} ({p.get('ID')}) — {p.get('Estado')}": p.get("ID")
             for p in proys}
    sel = st.selectbox("Proyecto asignado", list(idmap.keys()), key="fieldproj_sel")
    if not sel:
        return
    pid = idmap[sel]
    prj = P.get_project(pid)
    if not prj:
        st.error("Proyecto no encontrado.")
        return

    avance = P._num(prj.get("Avance"))
    est    = str(prj.get("Estado", ""))
    c1, c2 = st.columns(2)
    c1.metric("Estado", f"{_ESTADO_EMOJI.get(est,'')} {est}".strip())
    c2.metric("Avance del proyecto", f"{avance:.0f}%")
    st.progress(min(1.0, avance / 100.0))
    if prj.get("Ubicacion"):
        st.caption(f"📍 {prj.get('Ubicacion')}  ·  Cliente: {prj.get('Cliente','—')}")

    # ── Alarmas: reportar problema + ver avisos ──
    _alerts_section(pid, grupo, prj.get("Nombre", ""), allow_report=True)

    st.markdown("#### Actividades — actualiza tu avance")
    acts = P.list_activities(pid)
    if not acts:
        st.caption("Este proyecto no tiene actividades registradas.")
    for a in acts:
        orden  = a.get("Orden")
        nombre = a.get("Nombre")
        cur    = P._num(a.get("Avance"))
        icon   = "✅" if cur >= 100 else ("🚧" if cur > 0 else "🕓")
        with st.expander(f"{icon} {orden}. {nombre} — {cur:.0f}%"):
            new = st.slider("Avance %", 0, 100, int(cur), key=f"act_{pid}_{orden}")
            fc1, fc2 = st.columns(2)
            fi = fc1.text_input("Inicio real (YYYY-MM-DD)", value=a.get("FechaInicioReal", ""),
                                key=f"fi_{pid}_{orden}")
            ff = fc2.text_input("Fin real (YYYY-MM-DD)", value=a.get("FechaFinReal", ""),
                                key=f"ff_{pid}_{orden}")
            nota = st.text_input("Nota", value=a.get("Nota", ""), key=f"nt_{pid}_{orden}")
            if st.button("💾 Guardar avance", key=f"sv_{pid}_{orden}"):
                ok, msg = P.update_activity_progress(pid, orden, new, fi, ff, nota)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()

    # ── Documentos (campo: sube fotos, consulta planos/informe cliente/matriz/fotos) ──
    st.markdown("---")
    _documentos_section(pid)
