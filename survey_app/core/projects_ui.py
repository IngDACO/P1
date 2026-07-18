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
from core import maps
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

# Colores de estado para las píldoras/barras (bg suave, texto oscuro de la misma familia)
_ESTADO_COLOR = {
    "En progreso": ("#e6f1fb", "#185fa5", "#2e6da4"),
    "Planificado": ("#f1f0ec", "#5f5e5a", "#888780"),
    "Completado":  ("#eaf3de", "#3b6d11", "#639922"),
    "En pausa":    ("#faeeda", "#854f0b", "#ba7517"),
    "Cancelado":   ("#fcebeb", "#a32d2d", "#e24b4a"),
}


def _estado_colors(est):
    return _ESTADO_COLOR.get(est, ("#f1f0ec", "#5f5e5a", "#888780"))


# ══════════════════════════════════════════════════════════════════════
# CENTRO DE CONTROL DEL GRUPO — cabecera con marca + KPIs
# ══════════════════════════════════════════════════════════════════════
def _delays(proys) -> dict:
    """{pid: días de retraso} (proyección SPI). Delega en core.projects.delays_for."""
    return P.delays_for(proys)


def _aheads(proys) -> dict:
    """{pid: días de adelanto} (proyección SPI)."""
    return P.aheads_for(proys)


def _kpis(grupo=None) -> dict:
    """Métricas de salud del grupo (1 lectura de cada hoja, todo cacheado)."""
    proys   = P.list_projects(grupo=grupo)
    horas   = P.project_hours_bulk(grupo)
    alarmas = alerts.open_counts_all() if alerts.is_configured() else {}
    ids     = {str(p.get("ID", "")) for p in proys}
    activos = [p for p in proys if str(p.get("Estado", "")) not in ("Completado", "Cancelado")]
    avances = [P._num(p.get("Avance")) for p in proys]
    return {
        "total":   len(proys),
        "activos": len(activos),
        "avg":     round(sum(avances) / len(avances)) if avances else 0,
        "riesgo":  len(_delays(proys)),
        "alarmas": sum(v for k, v in alarmas.items() if k in ids),
        "horas":   round(sum(horas.get(str(p.get("Nombre", "")), 0.0) for p in proys)),
    }


def _kpi_card(label, value, color=None):
    col = f"color:{color};" if color else ""
    return (
        '<div style="background:#ffffff;border:1px solid #e6e9ef;border-radius:12px;'
        'padding:12px 14px;flex:1;min-width:104px;">'
        f'<div style="font-size:12.5px;color:#6b7280;line-height:1.2;">{label}</div>'
        f'<div style="font-size:26px;font-weight:700;margin-top:2px;{col}">{value}</div>'
        '</div>'
    )


def render_group_header(grupo: str):
    """Banda de marca del grupo + fila de KPIs (centro de control del admin)."""
    st.markdown(
        '<div style="background:linear-gradient(135deg,#1a3a5c 0%,#2e6da4 100%);'
        'padding:14px 18px;border-radius:12px;display:flex;align-items:center;gap:12px;'
        'margin-bottom:14px;">'
        '<span style="font-size:26px;line-height:1;">🏢</span>'
        '<div style="min-width:0;">'
        f'<div style="color:#fff;font-size:1.25rem;font-weight:800;line-height:1.1;">{grupo}</div>'
        '<div style="color:#b0c8e8;font-size:0.8rem;margin-top:2px;">Centro de control del grupo</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )
    if not P.is_configured():
        return
    k = _kpis(grupo)
    cards = (
        _kpi_card("Proyectos activos", k["activos"])
        + _kpi_card("Avance promedio", f'{k["avg"]}%')
        + _kpi_card("En riesgo", k["riesgo"], "#c0392b" if k["riesgo"] else "#1f2937")
        + _kpi_card("Alarmas abiertas", k["alarmas"], "#d97706" if k["alarmas"] else "#1f2937")
        + _kpi_card("Horas registradas", k["horas"])
    )
    st.markdown(
        f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:6px;">{cards}</div>',
        unsafe_allow_html=True,
    )
    _resumen_del_dia(grupo)


def _resumen_del_dia(grupo: str):
    """Resumen del día del grupo: chips de pendientes + briefing IA (1 vez por sesión)."""
    from core import admin_digest
    try:
        d = admin_digest.group_digest(grupo)
    except Exception:
        return
    with st.expander("🔔 Resumen del día", expanded=True):
        chips = []
        if d["vencidos"]:           chips.append(f"⛔ {len(d['vencidos'])} vencido(s)")
        if d["por_vencer"]:         chips.append(f"📅 {len(d['por_vencer'])} por vencer")
        if d["retrasos"]:           chips.append(f"🔴 {len(d['retrasos'])} en retraso")
        if d["alarmas"]:            chips.append(f"🔔 {sum(a['n'] for a in d['alarmas'])} alarma(s)")
        if d["near_miss"]:          chips.append(f"🦺 {len(d['near_miss'])} near miss")
        if d["sin_asignar"]:        chips.append(f"👷 {len(d['sin_asignar'])} sin asignar")
        if d["campo_sin_contacto"]: chips.append(f"📇 {len(d['campo_sin_contacto'])} sin contacto")
        if d.get("cred_venc"):      chips.append(f"🎫 {len(d['cred_venc'])} credenciales")
        if d.get("sobre_presupuesto"): chips.append(f"💸 {len(d['sobre_presupuesto'])} sobre presupuesto")
        if chips:
            st.markdown("  ".join(f"`{c}`" for c in chips))
        else:
            st.success("Sin pendientes urgentes. ✅")

        key = f"_brief_{grupo}"
        if key not in st.session_state:
            with st.spinner("Preparando tu resumen…"):
                from core import chat_agent
                st.session_state[key] = chat_agent.admin_briefing(grupo)
        st.markdown(st.session_state[key])
        if st.button("🔄 Actualizar resumen", key=f"brief_ref_{grupo}"):
            st.session_state.pop(key, None)
            st.rerun()


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


# ── Panel de proyectos ───────────────────────────────────────────
def _panel_proyectos(grupo: str):
    proys = P.list_projects(grupo=grupo)
    if not proys:
        st.info("Todavía no hay proyectos en este grupo. Los proyectos se crean desde "
                "la pestaña **Survey** con el botón **💾 Guardar como proyecto** "
                "(tras calcular).")
        return

    # ── Cartera de proyectos (lista de tarjetas) ──
    ags = {a["ID"]: a["Nombre"] for a in P.list_groupings(grupo=grupo)}
    horas = P.project_hours_bulk(grupo)   # 1 sola lectura del fichaje
    alarmas = alerts.open_counts_all() if alerts.is_configured() else {}
    delays = _delays(proys)               # {pid: días de retraso}
    aheads = _aheads(proys)               # {pid: días de adelanto}
    _nr, _na = len(delays), len(aheads)
    st.markdown(f"**Cartera — {len(proys)} proyecto(s)**"
                + (f"  ·  🔴 {_nr} con retraso" if _nr else "")
                + (f"  ·  🟢 {_na} adelantado(s)" if _na else ""))
    st.markdown(_portfolio_html(proys, horas, alarmas, ags, delays, aheads),
                unsafe_allow_html=True)

    # ── Abrir proyecto (detalle / edición) ──
    st.markdown("#### 🔎 Abrir proyecto")
    idmap = {f"{p.get('ID')} · {p.get('Nombre')}": p.get("ID") for p in proys}
    sel = st.selectbox("Proyecto", list(idmap.keys()), key="adminproj_sel",
                       label_visibility="collapsed")
    if sel:
        st.markdown("---")
        _detalle_proyecto(idmap[sel], grupo)


def _portfolio_html(proys, horas, alarmas, ags, delays=None, aheads=None) -> str:
    """Lista de tarjetas de proyecto: punto de estado, nombre/cliente, ubicación,
    píldora, barra de avance, horas y badges de alarmas / retraso / adelanto.
    Retraso → borde rojo + badge ⏰ · Adelanto → borde verde + badge ⏩."""
    delays = delays or {}
    aheads = aheads or {}
    parts = []
    for p in proys:
        est = str(p.get("Estado", ""))
        bg, fg, bar = _estado_colors(est)
        av  = P._num(p.get("Avance"))
        nom = str(p.get("Nombre", "")) or "(sin nombre)"
        pid = str(p.get("ID", ""))
        hrs = horas.get(str(p.get("Nombre", "")), 0.0)
        na  = alarmas.get(pid, 0)
        ag  = ags.get(str(p.get("AgrupacionID", "")), "")
        sub = f"{pid} · {str(p.get('Cliente','')) or '—'}" + (f" · {ag}" if ag else "")
        ubic = str(p.get("Ubicacion", "") or "")
        ubic_html = (f'<div style="font-size:11.5px;white-space:nowrap;overflow:hidden;'
                     f'text-overflow:ellipsis;">{maps.maps_link_html(ubic, ubic, color="#2e6da4")}</div>'
                     if ubic else "")
        alarm = (f'<div style="width:44px;text-align:center;flex:none;color:#c0392b;'
                 f'font-size:12.5px;font-weight:600;">🔔 {na}</div>'
                 if na else '<div style="width:44px;flex:none;"></div>')
        # Retraso (rojo) / adelanto (verde) → borde + badge de días
        d, adel = delays.get(pid), aheads.get(pid)
        card_border = "border:1px solid #e6e9ef"
        retraso_badge = ""
        if d:
            card_border = "border:1px solid #e6e9ef;border-left:4px solid #c0392b"
            retraso_badge = (f'<span style="font-size:12px;padding:3px 9px;border-radius:20px;'
                             f'background:#fcebeb;color:#a32d2d;white-space:nowrap;flex:none;'
                             f'font-weight:600;">⏰ {d:.0f} d</span>')
        elif adel:
            card_border = "border:1px solid #e6e9ef;border-left:4px solid #1e8449"
            retraso_badge = (f'<span style="font-size:12px;padding:3px 9px;border-radius:20px;'
                             f'background:#eaf3de;color:#3b6d11;white-space:nowrap;flex:none;'
                             f'font-weight:600;">⏩ {adel:.0f} d</span>')
        parts.append(
            f'<div style="display:flex;align-items:center;gap:12px;padding:11px 14px;'
            f'{card_border};border-radius:10px;margin-bottom:8px;background:#fff;">'
            f'<div style="width:9px;height:9px;border-radius:50%;background:{bar};flex:none;"></div>'
            '<div style="flex:1;min-width:0;">'
            f'<div style="font-size:14px;font-weight:600;color:#1f2937;white-space:nowrap;'
            f'overflow:hidden;text-overflow:ellipsis;">{nom}</div>'
            f'<div style="font-size:12px;color:#6b7280;white-space:nowrap;overflow:hidden;'
            f'text-overflow:ellipsis;">{sub}</div>'
            + ubic_html +
            '</div>'
            + retraso_badge +
            f'<span style="font-size:12px;padding:3px 10px;border-radius:20px;background:{bg};'
            f'color:{fg};white-space:nowrap;flex:none;">{_ESTADO_EMOJI.get(est,"")} {est}</span>'
            '<div style="width:118px;flex:none;">'
            '<div style="display:flex;justify-content:space-between;font-size:11.5px;'
            f'color:#6b7280;margin-bottom:3px;"><span>Avance</span>'
            f'<span style="color:#1f2937;font-weight:600;">{av:.0f}%</span></div>'
            '<div style="height:6px;background:#eef1f5;border-radius:20px;overflow:hidden;">'
            f'<div style="height:100%;width:{av:.0f}%;background:{bar};"></div></div>'
            '</div>'
            f'<div style="width:54px;text-align:right;flex:none;font-size:12px;color:#6b7280;">'
            f'⏱ {hrs:.0f}h</div>'
            + alarm +
            '</div>'
        )
    return "".join(parts)


def _induccion_section(pid, prj, grupo=None, allow_send=False):
    """Muestra instrucciones particulares + inducciones (links) del proyecto.
    Si allow_send, el admin puede (re)enviarlas por Telegram/email a los asignados."""
    instr = str(prj.get("Instrucciones", "") or "").strip()
    links = P.parse_links(prj.get("InduccionLinks", ""))
    if not instr and not links:
        return
    with st.expander("📌 Instrucciones e inducciones del proyecto", expanded=bool(links)):
        if instr:
            st.markdown("**Instrucciones particulares**")
            st.markdown(instr)
        if links:
            st.markdown("**Inducciones a diligenciar**")
            for l in links:
                st.markdown(f"- [{l}]({l})")
            if allow_send and notify.any_channel_configured():
                asignados = [x.strip() for x in str(prj.get("CampoAsignados", "")).split(";") if x.strip()]
                if asignados and st.button("📨 Reenviar inducción a los asignados",
                                           key=f"send_ind_{pid}"):
                    n = 0
                    for un in asignados:
                        try:
                            rr = notify.notify_induction(un, prj.get("Nombre", ""), links)
                            if rr.get("email") or rr.get("telegram"):
                                n += 1
                        except Exception:
                            pass
                    st.success(f"📨 Enviado a {n} usuario(s) de campo.")


def _detalle_proyecto(pid: str, grupo: str = None):
    prj = P.get_project(pid)
    if not prj:
        st.error("Proyecto no encontrado.")
        return
    # El grupo se toma del propio proyecto (así el propietario puede abrir cualquiera)
    grupo = str(prj.get("Grupo", "")) or (grupo or "")

    avance = P._num(prj.get("Avance"))
    est    = str(prj.get("Estado", ""))
    _bg, _fg, _bar = _estado_colors(est)
    _cli  = str(prj.get("Cliente", "")) or "—"
    _ubic = (" · " + maps.maps_link_html(prj.get("Ubicacion"))) if prj.get("Ubicacion") else ""
    st.markdown(
        f'<div style="border:1px solid #e6e9ef;border-left:4px solid {_bar};border-radius:10px;'
        'padding:12px 16px;margin-bottom:10px;background:#fff;">'
        '<div style="display:flex;align-items:center;justify-content:space-between;gap:10px;'
        'flex-wrap:wrap;">'
        f'<div style="font-size:1.15rem;font-weight:800;color:#1f2937;">{prj.get("Nombre","")}</div>'
        f'<span style="font-size:12px;padding:3px 11px;border-radius:20px;background:{_bg};'
        f'color:{_fg};white-space:nowrap;">{_ESTADO_EMOJI.get(est,"")} {est}</span></div>'
        f'<div style="font-size:12.5px;color:#6b7280;margin-top:3px;">{_cli}{_ubic}</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    c1.metric("Avance", f"{avance:.0f}%")
    c2.metric("Horas trabajadas", f"{P.project_hours(prj.get('Nombre'), grupo):.1f}")
    st.progress(min(1.0, avance / 100.0))

    # ── Instrucciones e inducciones ──
    _induccion_section(pid, prj, grupo, allow_send=True)

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
        instr    = st.text_area("📌 Instrucciones particulares", value=prj.get("Instrucciones", ""))
        ind      = st.text_area("📝 Inducciones (un link por línea)",
                                value=prj.get("InduccionLinks", ""),
                                help="Al asignar un usuario de campo se le envían por Telegram/email.")

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
        presup  = st.number_input("💰 Presupuesto del proyecto (0 = sin presupuesto)",
                                  min_value=0.0, step=100.0, value=P._num(prj.get("Presupuesto")))

        if st.form_submit_button("💾 Guardar cambios", use_container_width=True):
            ag_id = "" if ag_sel == "(ninguna)" else ag_sel.split(" · ")[0]
            P.update_project(pid, {   # todo en UNA escritura (batch) → sin rate limit
                "Nombre": nombre, "Cliente": cliente, "Ubicacion": ubic, "Modelo": modelo,
                "Ingeniero": ing, "FechaInicio": f_ini, "FechaFinEst": f_fin,
                "CampoAsignados": ";".join(asignados),
                "AgrupacionID": ag_id, "PesoEnAgrupacion": peso,
                "EstadoManual": est_man, "Estado": P.derive_estado(avance, est_man),
                "Instrucciones": instr, "InduccionLinks": ind, "Presupuesto": presup,
            })
            # Notificar a los usuarios de campo recién asignados
            nuevos = [x for x in asignados if x not in actuales]
            _sent = 0
            if nuevos:
                _info = {"Nombre": nombre, "Cliente": cliente, "Ubicacion": ubic,
                         "FechaInicio": f_ini, "FechaFinEst": f_fin, "InduccionLinks": ind}
                for un in nuevos:
                    try:
                        rr = notify.notify_assignment(un, _info)
                        if rr.get("email") or rr.get("telegram"):
                            _sent += 1
                    except Exception:
                        pass
            # Si cambiaron las inducciones, reenviarlas a los ya asignados
            if str(ind).strip() != str(prj.get("InduccionLinks", "")).strip():
                _links = P.parse_links(ind)
                if _links:
                    for un in [x for x in asignados if x not in nuevos]:
                        try:
                            notify.notify_induction(un, nombre, _links)
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

    # ── Gastos / compras ──
    render_expenses(pid, grupo, can_delete=True, key_prefix="adm")

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
    delays = _delays(proys)
    aheads = _aheads(proys)
    rows = []
    for p in proys:
        est = str(p.get("Estado", ""))
        pid = str(p.get("ID", ""))
        _na = alarmas.get(pid, 0)
        _d  = delays.get(pid)
        _ad = aheads.get(pid)
        ubic = str(p.get("Ubicacion", "") or "")
        rows.append({
            "ID":        p.get("ID"),
            "Grupo":     p.get("Grupo"),
            "Proyecto":  p.get("Nombre"),
            "🔔":        f"🔴 {_na}" if _na else "",
            "Cliente":   p.get("Cliente"),
            "Ubicación": ubic,
            "🗺":        maps.maps_url(ubic),
            "Estado":    f"{_ESTADO_EMOJI.get(est, '')} {est}".strip(),
            "⏰ Retraso": f"{_d:.0f} d" if _d else "",
            "⏩ Adelanto": f"{_ad:.0f} d" if _ad else "",
            "Avance %":  P._num(p.get("Avance")),
            "Horas":     P.project_hours(p.get("Nombre"), p.get("Grupo")),
            "Agrupación": ags.get(str(p.get("AgrupacionID", "")), ""),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                 column_config={"🗺": st.column_config.LinkColumn("🗺", display_text="Abrir")})

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
        st.caption(f"{maps.maps_link_md(prj.get('Ubicacion'))}  ·  Cliente: {prj.get('Cliente','—')}")
    elif prj.get("Cliente"):
        st.caption(f"Cliente: {prj.get('Cliente','—')}")

    # ── Instrucciones e inducciones del proyecto (solo lectura) ──
    _induccion_section(pid, prj, grupo, allow_send=False)

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

    # ── Gastos / compras (campo carga recibos) ──
    st.markdown("---")
    render_expenses(pid, grupo, can_delete=False, key_prefix="fld")

    # ── Documentos (campo: sube fotos, consulta planos/informe cliente/matriz/fotos) ──
    st.markdown("---")
    _documentos_section(pid)


# ── Vista del CONDUCTOR: proyectos del grupo (solo lectura, datos básicos) ──
def render_conductor_projects(grupo: str):
    st.markdown("### 📋 Proyectos del grupo")
    st.caption("Datos básicos para ubicarte y fichar. No incluye avances ni actividades.")
    if not P.is_configured():
        st.warning("La lista de proyectos necesita Google Sheets configurado.")
        return
    proys = P.list_projects(grupo=grupo)
    if not proys:
        st.info("No hay proyectos en el grupo.")
        return
    rows = [{
        "ID":        p.get("ID"),
        "Proyecto":  p.get("Nombre"),
        "Cliente":   p.get("Cliente"),
        "Ubicación": str(p.get("Ubicacion", "") or ""),
        "🗺":        maps.maps_url(p.get("Ubicacion")),
    } for p in proys]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                 column_config={"🗺": st.column_config.LinkColumn("🗺", display_text="Abrir")})

    # ── Cargar recibos (combustible, peajes, materiales…) ──
    st.markdown("---")
    idmap = {f"{p.get('Nombre')} ({p.get('ID')})": p.get("ID") for p in proys}
    sel = st.selectbox("Cargar recibo al proyecto", list(idmap.keys()), key="cond_exp_sel")
    if sel:
        render_expenses(idmap[sel], grupo, can_delete=False, key_prefix="cond")


# ── Gastos / compras por proyecto (admin, campo, conductor) ──
def render_expenses(pid, grupo, can_delete=False, key_prefix="ex"):
    from core import expenses as E
    if not E.is_configured():
        return
    st.markdown("#### 💰 Gastos / compras")
    cost = E.project_cost(pid, grupo)
    m1, m2, m3 = st.columns(3)
    m1.metric("Compras", f"${cost['compras']:,.0f}")
    m2.metric("Mano de obra", f"${cost['mano_obra']:,.0f}")
    m3.metric("Costo total", f"${cost['total']:,.0f}")
    if cost["presupuesto"] > 0:
        st.progress(min(1.0, (cost["pct"] or 0) / 100.0))
        txt = f"Presupuesto ${cost['presupuesto']:,.0f} · {cost['pct']}% consumido"
        (st.error if cost["over"] else st.caption)(txt + (" ⛔ SOBRE PRESUPUESTO" if cost["over"] else ""))

    with st.expander("➕ Cargar recibo"):
        with st.form(f"{key_prefix}_add_{pid}", clear_on_submit=True):
            c1, c2 = st.columns(2)
            cat = c1.selectbox("Categoría", E.CATEGORIAS, key=f"{key_prefix}_cat")
            val = c2.number_input("Valor total del recibo", min_value=0.0, step=1.0, key=f"{key_prefix}_val")
            prov = c1.text_input("Proveedor", key=f"{key_prefix}_prov")
            desc = c2.text_input("Descripción", key=f"{key_prefix}_desc")
            f = st.file_uploader("Foto / PDF del recibo", type=["pdf", "png", "jpg", "jpeg"],
                                 key=f"{key_prefix}_file")
            if st.form_submit_button("Guardar recibo"):
                if val <= 0:
                    st.error("Ingresa el valor del recibo.")
                else:
                    did, fn = "", ""
                    if f is not None:
                        fn = f.name
                        did = E.upload_receipt(pid, f.name, f.getvalue(), f.type or "application/octet-stream")
                    ok, msg = E.add(pid, grupo, val, cat, prov, desc, did, fn,
                                    st.session_state.get("auth", {}).get("usuario", ""))
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()

    items = E.project_expenses(pid)["items"]
    if items:
        st.dataframe(pd.DataFrame([{
            "Fecha": r.get("Fecha"), "Categoría": r.get("Categoria"),
            "Proveedor": r.get("Proveedor"), "Descripción": r.get("Descripcion"),
            "Valor": E._num(r.get("Valor")), "Por": r.get("CreadoPor"),
        } for r in items]), hide_index=True, use_container_width=True)
        with st.expander(f"📎 Recibos ({len(items)})"):
            for r in items:
                did = str(r.get("DriveID", "")).strip()
                cc = st.columns([5, 1])
                lbl = f"{r.get('Fecha')} · {r.get('Categoria')} · ${E._num(r.get('Valor')):.0f}"
                if did:
                    try:
                        from core import drive_store
                        cc[0].download_button("⬇️ " + lbl, data=drive_store.download(did),
                                              file_name=r.get("Archivo", "recibo"),
                                              key=f"{key_prefix}_dl_{r.get('ID')}")
                    except Exception:
                        cc[0].caption(lbl)
                else:
                    cc[0].caption(lbl + " (sin archivo)")
                if can_delete and cc[1].button("🗑", key=f"{key_prefix}_del_{r.get('ID')}"):
                    ok, msg = E.delete(r.get("ID"))
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()


# ── Reporte del ADMIN: gastos de todos los proyectos del grupo ──
def render_group_expenses(grupo: str):
    from core import expenses as E
    st.markdown("#### 💰 Gastos del grupo")
    if not E.is_configured():
        st.warning("Los gastos necesitan Google Sheets configurado.")
        return
    ge = E.group_expenses(grupo)
    filas = ge["proyectos"]
    if not filas:
        st.info("No hay proyectos en el grupo.")
        return
    df = pd.DataFrame([{
        "Proyecto": f["nombre"], "Compras": f["compras"], "Mano de obra": f["mano_obra"],
        "Costo total": f["total"], "Presupuesto": f["presupuesto"],
        "% ": f["pct"] if f["pct"] is not None else "",
    } for f in filas])
    st.dataframe(df, use_container_width=True, hide_index=True)
    tot = sum(f["total"] for f in filas)
    st.metric("Costo total del grupo", f"${tot:,.0f}")

    # ── Gráficas ──
    _conc = [f for f in filas if f["total"] > 0]
    if _conc:
        st.markdown("**Costo por proyecto** (compras vs mano de obra)")
        st.bar_chart(pd.DataFrame(
            {"Compras": [f["compras"] for f in _conc],
             "Mano de obra": [f["mano_obra"] for f in _conc]},
            index=[f["nombre"] for f in _conc]))
    if ge["por_categoria"]:
        st.markdown("**Compras por categoría**")
        _cat = dict(sorted(ge["por_categoria"].items(), key=lambda x: -x[1]))
        st.bar_chart(pd.DataFrame({"Total": list(_cat.values())}, index=list(_cat.keys())))
        st.dataframe(pd.DataFrame([{"Categoría": k, "Total": v} for k, v in _cat.items()]),
                     hide_index=True, use_container_width=True)
    st.download_button("⬇️ Exportar CSV (contabilidad)", data=df.to_csv(index=False).encode("utf-8"),
                       file_name=f"gastos_{grupo}.csv", mime="text/csv", key="ge_csv")


# ── Reporte del ADMIN: horas de TODOS los usuarios del grupo ──
def render_group_hours(grupo: str):
    from datetime import datetime
    from core import timeclock
    st.markdown("#### ⏱ Horas del grupo")
    if not timeclock.is_configured():
        st.warning("El fichaje necesita Google Sheets configurado.")
        return
    st.caption("Total de horas por usuario (jornada general de conductores + horas por proyecto). "
               "**Sin asignar** = tiempo de jornada no imputado a un proyecto (transporte/espera).")

    per = st.radio("Periodo", ["Hoy", "Semana", "Mes", "Todo"], horizontal=True,
                   key="gh_per", label_visibility="collapsed")
    now = datetime.now()
    if per == "Hoy":
        days = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds() / 86400.0
    else:
        days = {"Semana": 7, "Mes": 30, "Todo": None}[per]

    data = timeclock.group_hours(grupo, days=days)
    if not data:
        st.info("Sin fichajes en el periodo.")
        return

    st.dataframe(pd.DataFrame([{
        "Usuario":       d.get("nombre") or d["usuario"],
        "Login":         d["usuario"],
        "Jornada (h)":   d["general"],
        "Proyectos (h)": d["proyecto"],
        "Sin asignar (h)": d["sin_asignar"],
    } for d in data]), use_container_width=True, hide_index=True)

    with st.expander("🔎 Desglose por proyecto"):
        for d in data:
            if d["por_proyecto"]:
                st.markdown(f"**{d.get('nombre') or d['usuario']}**")
                st.dataframe(pd.DataFrame(
                    [{"Proyecto": k, "Horas": v} for k, v in
                     sorted(d["por_proyecto"].items(), key=lambda x: -x[1])],
                ), use_container_width=True, hide_index=True)
