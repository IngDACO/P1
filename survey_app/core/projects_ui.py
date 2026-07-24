"""
UI del panel de administración de proyectos (rol administrador).
Navegación con st.radio (NO st.tabs) para evitar mezcla de contenido.
"""
from datetime import timedelta

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
from core import survey_calc
from core import toolruns
from core import tool_save_ui
from core import credentials
from core import plan_data
from core import timeclock

# Opción neutra de los selectores de proyecto: sin ella, `st.selectbox`
# devuelve el primer elemento y se abre un proyecto que nadie eligió.
_VACIO = "— elige un proyecto —"
from core import ui_common as ui


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
    "En pausa": "⏸", "Cancelado": "🚫", "Archivado": "📦",
}

# Colores de estado para las píldoras/barras (bg suave, texto oscuro de la misma familia)
_ESTADO_COLOR = {
    "En progreso": ("#e6f1fb", "#185fa5", "#2e6da4"),
    "Planificado": ("#f1f0ec", "#5f5e5a", "#888780"),
    "Completado":  ("#eaf3de", "#3b6d11", "#639922"),
    "En pausa":    ("#faeeda", "#854f0b", "#ba7517"),
    "Cancelado":   ("#fcebeb", "#a32d2d", "#e24b4a"),
    "Archivado":   ("#eef1f5", "#6b7280", "#9aa7b8"),
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
        "riesgo":  len(P.delays_of_group(grupo)),
        "alarmas": sum(v for k, v in alarmas.items() if k in ids),
        "horas":   round(sum(horas.get(str(p.get("ID", "")), 0.0) for p in proys)),
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
        b1, b2 = st.columns(2)
        if b1.button("🔄 Actualizar resumen", key=f"brief_ref_{grupo}"):
            st.session_state.pop(key, None)
            st.rerun()
        if b2.button("📨 Enviármelo por Telegram/email", key=f"brief_send_{grupo}"):
            from core import notify
            _u = st.session_state.get("auth", {}).get("usuario", "")
            _txt = st.session_state.get(key, "")
            try:
                rr = notify.notify_user(_u, f"🔔 Resumen del día — {grupo}",
                                        [l for l in str(_txt).split("\n") if l.strip()])
                if rr.get("email") or rr.get("telegram"):
                    st.success("📨 Resumen enviado.")
                else:
                    st.warning("No tienes email/Telegram configurado en tu usuario.")
            except Exception as e:
                st.error(f"No se pudo enviar: {e}")


# Documentos: tipos y permisos por rol
# ⚠️ Esta lista es SOLO para el desplegable de subida manual.
# NO se usa para filtrar lo que se ve: el admin ve TODOS los tipos.
# Hasta v134 la vista filtraba por aqui, asi que los documentos generados por
# la app con un tipo ausente de la lista desaparecian EN SILENCIO: los
# Pre-Start (tipo "prestart", v97) llevaban 36 versiones invisibles y los
# calculos (tipo "calculo", v129) nacieron invisibles.
# ⚠️ "plano" NO va aquí: subirlo por el uploader genérico solo lo guardaba en
# Drive sin extraer a PlanoJSON, así que las herramientas no lo veían (v156). El
# plano se carga SOLO desde 📐 Datos del plano (_cargar_plano), que sí extrae.
_DOC_SUBIR  = ["informe_cliente", "informe_admin", "matriz_survey",
               "foto", "certificado", "otro"]
_DOC_TIPOS  = _DOC_SUBIR + ["plano"]           # para VER (el plano se sigue mostrando)
# El campo consulta lo que usa en obra: incluye el Pre-Start que firma y los
# calculos (plomada, cortes) que ejecuta.
_CAMPO_VER  = {"plano", "informe_cliente", "matriz_survey", "foto",
               "prestart", "calculo"}
_CAMPO_SUBE = ["foto"]                                                # campo solo sube fotos
_DOC_ICON   = {"plano": "📐", "informe_cliente": "📄", "informe_admin": "📑",
               "matriz_survey": "📊", "foto": "📷", "certificado": "🏅",
               "prestart": "🦺", "calculo": "🧮", "otro": "📎"}


def _a_fecha(v):
    """Texto de la hoja -> date, o None. Acepta lo que haya guardado de antes.

    ⚠️ Hasta v149 estas fechas eran `text_input` LIBRE y `project_schedule` hacia
    `.split("-")` con un `except` que caia a **hoy sin avisar**: escribir
    "16/07/2026" desplazaba el cronograma entero al dia 0 y falseaba curva S,
    retraso, proyeccion y radar del admin, en silencio.
    """
    from datetime import datetime as _dt
    s = str(v or "").strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return _dt.strptime(s[:10], fmt).date()
        except Exception:
            pass
    return None


def _iso(d) -> str:
    """date -> 'YYYY-MM-DD' (el unico formato que `project_schedule` sabe leer)."""
    try:
        return d.isoformat()
    except Exception:
        return ""


def _fecha_corta(v) -> str:
    """'2026-07-16 07:44:29' -> '16/07 07:44'. Devuelve '' si no se puede."""
    s = str(v or "").strip()
    if len(s) >= 16 and s[4] == "-" and s[7] == "-":
        return f"{s[8:10]}/{s[5:7]} {s[11:16]}"
    return s[:16]


def _cargar_plano(pid: str):
    """Sube el PDF del plano Y extrae sus datos a PlanoJSON (v156).

    ⚠️ El bug: subir el plano por el uploader genérico de 📎 Documentos solo lo
    guardaba en Drive; NO extraía a PlanoJSON, que es lo ÚNICO que leen las
    herramientas. Así que el plano quedaba invisible para ellas. Aquí se hace lo
    mismo que al crear el proyecto: subir + extraer + guardar.
    """
    with st.expander("📤 Cargar / actualizar el plano del proyecto"):
        st.caption("Sube el PDF y se extraen sus datos para que las herramientas "
                   "los usen sin volver a pedir el plano. Tarda ~1 min.")
        _pdf = st.file_uploader("PDF del plano", type=["pdf"], key=f"planoup_{pid}")
        _idk = f"planoup_id_{pid}"
        if _pdf is not None and st.session_state.get(_idk) != f"{_pdf.name}:{_pdf.size}":
            _barra = st.progress(0.0, text="Leyendo el plano…")
            try:
                res = plan_data.extraer_todo(
                    _pdf, progreso=lambda fr, txt: _barra.progress(
                        min(1.0, fr), text=f"Leyendo el plano… {txt}"))
                # 1) Datos → PlanoJSON (lo que leen las herramientas)
                plan_data.guardar(pid, res)
                # 2) El PDF a Drive + registro como documento (best-effort)
                try:
                    if drive_store.is_configured():
                        _fid = drive_store.upload(pid, _pdf.name, _pdf.getvalue(),
                                                  "application/pdf")
                        P.add_document(pid, _pdf.name, "plano", _fid,
                                       st.session_state.get("auth", {}).get("usuario", ""))
                except Exception:
                    pass
                _barra.empty()
                st.session_state[_idk] = f"{_pdf.name}:{_pdf.size}"   # guarda v112
                st.success(f"✅ Plano cargado — {plan_data.resumen(res)}. "
                           "Las herramientas ya lo usan.")
                st.rerun()
            except Exception as e:
                _barra.empty()
                st.error(f"No se pudo leer el plano: {e}")


def _plano_section(pid: str, prj: dict):
    """Qué se leyó del plano de este proyecto (columna PlanoJSON, v137) + cargarlo.

    ⚠️ El dato existía desde v137 y solo se poblaba **al crear el proyecto**. Un
    proyecto creado sin plano no tenía forma de recibirlo (subirlo en Documentos
    NO extraía), así que las herramientas no lo veían nunca. Ahora se carga aquí.
    """
    datos = plan_data.del_proyecto(pid)
    st.markdown("**📐 Datos del plano**")
    if not datos:
        st.caption("Este proyecto no tiene datos de plano guardados, así que las "
                   "herramientas le pedirán el PDF a quien las use. Cárgalo aquí "
                   "una vez y dejarán de pedirlo.")
        _cargar_plano(pid)
        return

    faltan = datos.get("faltan") or []
    n, tot = datos.get("n_params", 0), datos.get("n_total", 0)
    tarj = [_kpi_card("Parámetros", f"{n}/{tot}" if tot else str(n),
                      "#c0392b" if faltan else "#1e8449")]
    for k, et in (("ns", "Paradas (NS)"), ("rail", "Riel"), ("hkp", "HKP"),
                  ("hq", "HQ"), ("lfkk", "LFKK"), ("lfgk", "LFGK")):
        if datos.get(k) not in (None, ""):
            _v = datos[k]
            # El riel muestra código + altura (el valor RAIL que usan las herramientas).
            if k == "rail" and datos.get("rail_altura"):
                _v = f"{datos['rail']} · RAIL {datos['rail_altura']:.0f}"
            tarj.append(_kpi_card(et, _v))
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px">'
                + "".join(tarj) + "</div>", unsafe_allow_html=True)

    if faltan:
        st.warning("⚠️ El plano no dio: **" + ", ".join(str(x) for x in faltan)
                   + "**. Quien use una herramienta tendrá que escribirlos a mano.")
    else:
        st.caption("El plano dio todo lo que las herramientas necesitan.")

    par = datos.get("params") or {}
    if par:
        with st.expander(f"Ver los {len(par)} parámetros del plano"):
            st.dataframe(pd.DataFrame([{"Parámetro": k, "Valor": v}
                                       for k, v in sorted(par.items())]),
                         hide_index=True, use_container_width=True)
    _cargar_plano(pid)


def _galeria_fotos(fotos, pid, por_pagina=6):
    """Miniaturas de las fotos de obra.

    El campo **solo puede subir fotos**: son la unica ventana del admin a la obra
    y hasta ahora salian como una fila de texto (`📷 foto.jpg · foto`).
    Paginada a proposito: cada miniatura es una descarga de Drive, asi que
    mostrarlas todas de golpe es justo el problema que evita el resto de la
    seccion (ver `_documentos_section`).
    """
    kver = f"_fotos_n_{pid}"
    n_ver = int(st.session_state.get(kver, por_pagina))
    st.markdown(f"**📷 Fotos de obra** — {len(fotos)}")
    visibles = fotos[:n_ver]
    for fila in range(0, len(visibles), 3):
        cols = st.columns(3)
        for c, d in zip(cols, visibles[fila:fila + 3]):
            did = str(d.get("DriveID", ""))
            with c:
                try:
                    st.image(drive_store.download(did), use_container_width=True)
                except Exception:
                    st.caption("🖼 no disponible")
                pie = str(d.get("Nombre", ""))
                st.caption(f"{pie[:26]}\n\n{_fecha_corta(d.get('Fecha'))}"
                           + (f" · {d.get('SubidoPor')}" if d.get("SubidoPor") else ""))
    if len(fotos) > n_ver:
        if st.button(f"Ver {min(por_pagina, len(fotos) - n_ver)} más "
                     f"({len(fotos) - n_ver} restantes)", key=f"masfotos_{pid}"):
            st.session_state[kver] = n_ver + por_pagina
            st.rerun()


def _documentos_section(pid: str):
    """📎 Documentos con permisos por rol (leido de session_state.auth).

    ⚠️ v147: **la descarga deja de ser ansiosa.** `st.download_button(data=...)`
    evalua `data` al RENDERIZAR, asi que la version anterior se bajaba de Drive
    **todos** los documentos del proyecto en cada pasada, antes de que nadie
    pulsara nada (cacheado 5 min, pero con fotos de obra eso crece sin techo).
    Ahora se listan con sus metadatos y solo se descarga **el que eliges**.
    """
    st.markdown("**📎 Documentos**")
    if not drive_store.is_configured():
        st.caption("🔒 Almacenamiento en Drive no configurado (faltan los secrets `[gdrive]`).")
        return
    a = st.session_state.get("auth", {})
    rol, usuario = a.get("rol", ""), a.get("usuario", "")
    es_campo     = rol == "campo"
    # Admin/propietario: ver_tipos = None -> SIN filtro, para que un tipo
    # nuevo generado por la app no vuelva a desaparecer de la vista (v134).
    ver_tipos    = _CAMPO_VER if es_campo else None
    sube_tipos   = _CAMPO_SUBE if es_campo else _DOC_SUBIR
    puede_borrar = rol in ("administrador", "propietario")

    docs = [d for d in P.list_documents(pid)
            if ver_tipos is None or str(d.get("Tipo", "")) in ver_tipos]
    fotos = [d for d in docs if str(d.get("Tipo", "")) == "foto"]
    resto = [d for d in docs if str(d.get("Tipo", "")) != "foto"]

    if fotos:
        _galeria_fotos(fotos, pid)
        st.markdown("")

    if resto:
        # Quien subio cada cosa y cuando: estaba guardado desde v74 y la vista
        # lo tiraba. Es lo que permite auditar de donde salio un documento.
        st.dataframe(pd.DataFrame([{
            "": _DOC_ICON.get(str(d.get("Tipo")), "📎"),
            "Documento": d.get("Nombre"),
            "Tipo": d.get("Tipo"),
            "Subido por": d.get("SubidoPor"),
            "Fecha": _fecha_corta(d.get("Fecha")),
        } for d in resto]), hide_index=True, use_container_width=True)
    elif not fotos:
        st.caption("Sin documentos todavía.")

    if docs:
        # ⚠️ Con dict comprehension, dos documentos de igual nombre y minuto
        # (subida masiva de fotos) colisionan y uno quedaria SIN poder bajarse.
        _mapa = {}
        for d in docs:
            _et = (f"{_DOC_ICON.get(str(d.get('Tipo')), '📎')} {d.get('Nombre')}"
                   f"  ·  {_fecha_corta(d.get('Fecha'))}")
            if _et in _mapa:                       # desempate por DriveID
                _et = f"{_et} · {str(d.get('DriveID',''))[-6:]}"
            _mapa[_et] = d
        _sel = ui.elegir("Descargar un documento", _mapa, key=f"dldoc_{pid}",
                         vacio="— elige un documento —")
        if _sel:                                   # solo AQUI se toca Drive
            _did = str(_sel.get("DriveID", ""))
            c1, c2 = st.columns([4, 1]) if puede_borrar else [st.container(), None]
            try:
                c1.download_button("⬇️ Descargar " + str(_sel.get("Nombre")),
                                   data=drive_store.download(_did),
                                   file_name=str(_sel.get("Nombre")),
                                   key=f"dlbtn_{pid}_{_did}", use_container_width=True)
            except Exception as e:
                c1.error(f"No se pudo descargar: {e}")
            if puede_borrar and c2 is not None:
                if c2.button("🗑", key=f"deld_{pid}_{_did}", use_container_width=True):
                    drive_store.delete(_did)
                    P.delete_document_record(pid, _did)
                    st.rerun()

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


def _nuevo_proyecto_form(grupo: str, key: str = "nuevo"):
    """Crear un proyecto desde cero, sin pasar por el Survey (v135).

    Antes el proyecto SOLO nacía del survey ("Guardar como proyecto"), así que
    no se podía dar de alta una obra hasta tener el survey hecho. Ahora el
    proyecto es la entidad principal y el survey una herramienta que lo
    alimenta, igual que Plomadas o los cortes.

    El cronograma se genera de las actividades estándar a partir del NS, que es
    lo único que necesita `build_schedule` — no hace falta el survey.
    """
    import datetime as _dt
    from core.schedule import build_schedule

    with st.expander("➕ Nuevo proyecto"):
        campos = []
        try:
            campos = [u["Usuario"] for u in auth.list_users(grupo)
                      if str(u.get("Rol", "")) == "campo"]
        except Exception:
            pass

        # ── Plano del elevador (fuera del form, para poder prellenar) ──
        # De aqui salen NS y los parametros que usan las 5 herramientas. Se lee
        # UNA vez: despues nadie vuelve a subir el PDF (antes se subia en cada
        # herramienta y cada una lo reparseaba, 30-70 s por vez).
        st.markdown("**📄 Plano del elevador** — opcional, pero recomendado")
        st.caption("Se leen los datos del plano una sola vez y quedan en el proyecto: "
                   "el equipo de campo ya no tendrá que cargar el PDF en ninguna herramienta.")
        _pdf = st.file_uploader("PDF del plano", type=["pdf"], key=f"np_pdf_{key}")
        _kd = f"np_plano_{key}"
        if _pdf is not None and st.session_state.get(f"{_kd}_id") != f"{_pdf.name}:{_pdf.size}":
            _barra = st.progress(0.0, text="Leyendo el plano…")
            def _prog(fr, txt):
                _barra.progress(min(1.0, fr), text=f"Leyendo el plano… {txt}")
            try:
                st.session_state[_kd] = plan_data.extraer_todo(_pdf, progreso=_prog)
                st.session_state[f"{_kd}_bytes"] = _pdf.getvalue()
            except Exception as e:
                st.session_state[_kd] = None
                st.error(f"No se pudo leer el plano: {e}")
            # Guarda de identidad: sin esto se reextraería en CADA rerun (v112)
            st.session_state[f"{_kd}_id"] = f"{_pdf.name}:{_pdf.size}"
            _barra.empty()
            st.rerun()

        _plano = st.session_state.get(_kd)
        if _plano:
            st.success(f"✅ Plano leído — {plan_data.resumen(_plano)}")
            if _plano.get("faltan"):
                with st.expander(f"⚠️ {len(_plano['faltan'])} dato(s) que el plano no dio"):
                    st.caption("Habrá que ingresarlos a mano en la herramienta que los use. "
                               "Se listan para que no queden en cero sin que nadie lo note.")
                    st.write(", ".join(_plano["faltan"]))

        asg = st.multiselect("👷 Usuarios de campo asignados", campos,
                             key=f"np_asg_{key}")
        if asg:
            _avisar_asignados(asg)

        with st.form(f"np_form_{key}"):
            c1, c2 = st.columns(2)
            nom = c1.text_input("Nombre del proyecto *", key=f"np_nom_{key}")
            cli = c2.text_input("Cliente", key=f"np_cli_{key}")
            ubi = c1.text_input("Ubicación", key=f"np_ubi_{key}",
                                help="Se enlaza a Google Maps en toda la app.")
            mod = c2.text_input("Modelo de elevador", key=f"np_mod_{key}",
                                value=str((_plano or {}).get("rail") or ""),
                                help="Prellenado con el código de riel del plano, si se leyó.")
            ing = c1.text_input("Ingeniero responsable", key=f"np_ing_{key}")
            _ns0 = 2
            try:
                _ns0 = max(2, min(50, int(float((_plano or {}).get("ns") or 2))))
            except Exception:
                pass
            ns = c2.number_input("Número de paradas (NS) *", min_value=2, max_value=50,
                                 value=_ns0, step=1, key=f"np_ns_{key}",
                                 help=("Leído del plano." if (_plano or {}).get("ns")
                                       else "Define la duración de las actividades."))
            f_ini = c1.date_input("Fecha de inicio", value=_dt.date.today(),
                                  key=f"np_ini_{key}")
            pres = c2.number_input("💰 Presupuesto (0 = sin presupuesto)", min_value=0.0,
                                   step=100.0, key=f"np_pres_{key}")
            instr = st.text_area("📌 Instrucciones particulares", key=f"np_ins_{key}",
                                 placeholder="Indicaciones específicas para el equipo…")
            inds = st.text_area("📝 Inducciones (un link por línea)", key=f"np_ind_{key}",
                                placeholder="https://...",
                                help="Se envían por Telegram/email a los asignados.")
            enviar = st.form_submit_button("➕ Crear proyecto", use_container_width=True)

        if enviar:
            if not nom.strip():
                st.error("El nombre del proyecto es obligatorio.")
                return
            # Incluye archivados: crear un homonimo de uno archivado tambien confunde.
            dups = [f"{p.get('ID')} · {p.get('Nombre')}"
                    for p in P.list_projects(grupo, incluir_archivados=True)
                    if " ".join(str(p.get("Nombre") or "").lower().split())
                    == " ".join(nom.lower().split())]
            if dups and not st.session_state.get(f"np_dup_{key}"):
                st.warning("⚠️ Ya existe un proyecto con ese nombre: "
                           + ", ".join(dups)
                           + ". Si es otro elevador, marca la casilla y crea de nuevo.")
                st.checkbox("Crear aunque el nombre se repita", key=f"np_dup_{key}")
                return

            sched = build_schedule(int(ns), f_ini, {})
            ok, res = P.create_project(
                grupo=grupo, nombre=nom.strip(), cliente=cli, ubicacion=ubi,
                modelo=mod, ns=int(ns), ingeniero=ing, campo_asignados=asg,
                fecha_inicio=f_ini.strftime("%Y-%m-%d"),
                fecha_fin_est=(sched["fecha_fin"].strftime("%Y-%m-%d")
                               if sched.get("fecha_fin") else ""),
                activities=sched.get("activities", []),
                creado_por=st.session_state.get("auth", {}).get("usuario", ""),
                instrucciones=instr, induccion_links=inds, presupuesto=pres)
            if not ok:
                st.error(f"No se pudo crear: {res}")
                return

            # Datos del plano + PDF, para que ninguna herramienta vuelva a pedirlo
            if _plano:
                try:
                    plan_data.guardar(res, _plano)
                except Exception as e:
                    st.warning(f"El proyecto se creó, pero no se guardaron los datos "
                               f"del plano: {e}")
                _pb = st.session_state.get(f"{_kd}_bytes")
                if _pb and drive_store.is_configured() and drive_store.is_available():
                    try:
                        fid = drive_store.upload(res, "plano.pdf", _pb, "application/pdf")
                        P.add_document(res, "plano.pdf", "plano", fid,
                                       st.session_state.get("auth", {}).get("usuario", ""))
                    except Exception:
                        st.caption("📎 El plano no se pudo archivar en Drive.")
                for _k in (_kd, f"{_kd}_bytes", f"{_kd}_id"):
                    st.session_state.pop(_k, None)

            st.success(f"✅ Proyecto **{res}** creado con "
                       f"{len(sched.get('activities', []))} actividades"
                       + (" y los datos del plano cargados." if _plano else ".")
                       + " El survey y las demás herramientas ya pueden alimentarlo.")
            if asg:
                _notificar_asignados(asg, {
                    "Nombre": nom.strip(), "Cliente": cli, "Ubicacion": ubi,
                    "FechaInicio": f_ini.strftime("%Y-%m-%d"),
                    "FechaFinEst": (sched["fecha_fin"].strftime("%Y-%m-%d")
                                    if sched.get("fecha_fin") else ""),
                    "InduccionLinks": inds})


def _avisar_asignados(usuarios):
    """Avisa de credenciales vencidas o contacto incompleto ANTES de asignar."""
    sin_contacto, cred_mal = [], []
    for u in usuarios:
        try:
            info = auth.get_user(u) or {}
            if not (str(info.get("Email", "")).strip()
                    and str(info.get("TelegramChatID", "")).strip()):
                sin_contacto.append(u)
        except Exception:
            pass
        try:
            for c in credentials.list_for(u):
                if credentials.status(c.get("Vencimiento")) in ("vencido", "por_vencer"):
                    cred_mal.append(f"{u} — {c.get('Tipo', 'credencial')}: "
                                    f"{credentials.status_label(c.get('Vencimiento'))}")
        except Exception:
            pass
    if cred_mal:
        st.warning("🎫 **Credenciales a revisar antes de mandarlos a obra:**\n\n"
                   + "\n".join(f"- {x}" for x in cred_mal))
    if sin_contacto:
        st.warning("📵 **Sin contacto completo (email + Telegram):** "
                   + ", ".join(sin_contacto)
                   + ". No recibirán la asignación ni las inducciones.")


def _notificar_asignados(usuarios, info_prj):
    """Envía la asignación e informa SIEMPRE del resultado (no falla en silencio)."""
    if not notify.any_channel_configured():
        st.caption("📨 Sin canales de aviso configurados (Gmail / Telegram).")
        return
    n = 0
    for u in usuarios:
        try:
            rr = notify.notify_assignment(u, info_prj)
            if rr.get("email") or rr.get("telegram"):
                n += 1
        except Exception:
            pass
    if n == len(usuarios):
        st.caption(f"📨 {n} usuario(s) de campo notificado(s).")
    elif n:
        st.warning(f"📨 Notificados {n} de {len(usuarios)}. Al resto le falta contacto.")
    else:
        st.warning("📵 No se pudo notificar a nadie: revisa email y Telegram "
                   "en 🛠 Mi grupo → Usuarios.")


def _calculos_section(pid: str):
    """Historial de cálculos de las herramientas para este proyecto.

    v129/v130 hicieron que Plomadas, Corte de rieles, Corte de buffers y Belting
    escribieran en la hoja `Calculos`… pero NADIE la leía: los datos entraban y
    no había forma de verlos. Esto cierra ese lazo, que es justo lo que se pidió
    ("cada vez que se use una herramienta debe alimentar la base del proyecto").
    """
    st.markdown("**🧮 Cálculos de herramientas**")
    if not toolruns.is_configured():
        st.caption("🔒 Requiere Google Sheets configurado.")
        return

    runs = toolruns.list_for(pid)
    if not runs:
        st.caption("Sin cálculos guardados. Desde 🔩 Plomadas, ✂️ Corte de rieles, "
                   "🛡 Corte de buffers o 🎗 Belting, pulsa **Guardar en el proyecto**.")
        return

    st.dataframe(pd.DataFrame([{
        "": toolruns.HERRAMIENTAS.get(str(r.get("Herramienta", "")),
                                      str(r.get("Herramienta", "")) or "🧮"),
        "Fecha": _fecha_corta(r.get("Fecha")), "Por": r.get("Usuario"),
        "Resumen": r.get("Resumen"),
    } for r in runs]), hide_index=True, use_container_width=True)

    # ── Reabrir un calculo en su herramienta (v148) ──
    # `DatosJSON` guardaba solo los RESULTADOS, asi que un calculo no se podia
    # retomar: para cambiar un dato habia que teclearlo todo otra vez. Desde
    # v148 se guardan tambien las ENTRADAS y esto las devuelve a la herramienta.
    _NAV = {"plomada": "🔩 Líneas de plomada", "rieles": "✂️ Corte de rieles",
            "buffers": "🛡 Corte de buffers", "belting": "🎗 Belting"}
    _reab = {f"{toolruns.HERRAMIENTAS.get(str(r.get('Herramienta','')), '🧮')} "
             f"{_fecha_corta(r.get('Fecha'))} · {r.get('Resumen','')[:40]}": r
             for r in runs
             if toolruns.entradas_de(r) and str(r.get("Herramienta","")) in _NAV}
    if _reab:
        _r = ui.elegir("↩️ Reabrir un cálculo en su herramienta", _reab,
                       key=f"reab_{pid}", vacio="— elige un cálculo —")
        if _r and st.button("↩️ Reabrir en la herramienta", key=f"reabbtn_{pid}",
                            use_container_width=True):
            _h = str(_r.get("Herramienta", ""))
            if tool_save_ui.pedir_reapertura(_r, _h, _NAV[_h]):
                st.rerun()
            else:
                st.warning("Este cálculo no guardó sus entradas (es anterior a v148).")
    elif runs:
        st.caption("Los cálculos anteriores a v148 no guardaron sus entradas, "
                   "así que solo puede descargarse su PDF.")

    # Descarga bajo demanda: igual que en Documentos, el `data=` de
    # download_button se evalua al renderizar y bajaba TODOS los PDF a la vez.
    _conpdf = {f"{toolruns.HERRAMIENTAS.get(str(r.get('Herramienta','')), '🧮')} "
               f"{_fecha_corta(r.get('Fecha'))} · {r.get('Usuario')}": r
               for r in runs if str(r.get("DriveID", "")).strip()}
    if _conpdf:
        _r = ui.elegir("Descargar el PDF de un cálculo", _conpdf,
                       key=f"dlcalc_{pid}", vacio="— elige un cálculo —")
        if _r:
            try:
                st.download_button(
                    "⬇️ Descargar PDF", data=drive_store.download(str(_r.get("DriveID"))),
                    file_name=str(_r.get("Archivo") or f"{_r.get('ID')}.pdf"),
                    key=f"dlcalbtn_{pid}_{_r.get('ID')}", use_container_width=True)
            except Exception as e:
                st.error(f"PDF no disponible: {e}")


def _field_users(grupo):
    """Usuarios de campo del grupo (para asignar a un proyecto)."""
    try:
        return [u["Usuario"] for u in auth.list_users(grupo)
                if str(u.get("Rol", "")) == "campo"]
    except Exception:
        return []


# ── Panel de proyectos ───────────────────────────────────────────
def _panel_proyectos(grupo: str):
    _ver_arch = st.checkbox("📦 Ver también los archivados", key="ver_arch_admin",
                            help="Los archivados no salen en listas ni informes; "
                                 "ábrelos desde aquí para restaurarlos.")
    proys = P.list_projects(grupo=grupo, incluir_archivados=_ver_arch)
    if not _ver_arch:
        _n_arch = len([p for p in P.list_projects(grupo=grupo, incluir_archivados=True)
                       if str(p.get("Estado", "")) == P.ARCHIVADO])
        if _n_arch:
            st.caption(f"📦 {_n_arch} proyecto(s) archivado(s) oculto(s).")
    if not proys:
        # ⚠️ El formulario va ANTES del return: desde v135 el survey ya no crea
        # proyectos, asi que si aqui se cortara no habria forma de crear el
        # primero (la app quedaria sin arranque posible).
        st.info("Todavía no hay proyectos en este grupo. Crea el primero aquí; "
                "después el Survey y las demás herramientas podrán alimentarlo.")
        _nuevo_proyecto_form(grupo, key="adm")
        return

    # ── Cartera de proyectos (lista de tarjetas) ──
    ags = {a["ID"]: a["Nombre"] for a in P.list_groupings(grupo=grupo)}
    horas = P.project_hours_bulk(grupo)   # 1 sola lectura del fichaje
    alarmas = alerts.open_counts_all() if alerts.is_configured() else {}
    delays = P.delays_of_group(grupo)     # {pid: días de retraso} (cacheado)
    aheads = P.aheads_of_group(grupo)     # {pid: días de adelanto} (cacheado)
    _nr, _na = len(delays), len(aheads)
    st.markdown(f"**Cartera — {len(proys)} proyecto(s)**"
                + (f"  ·  🔴 {_nr} con retraso" if _nr else "")
                + (f"  ·  🟢 {_na} adelantado(s)" if _na else ""))
    st.markdown(_portfolio_html(proys, horas, alarmas, ags, delays, aheads),
                unsafe_allow_html=True)

    _nuevo_proyecto_form(grupo, key="adm")

    # ── Abrir proyecto (detalle / edición) ──
    st.markdown("#### 🔎 Abrir proyecto")
    idmap = {f"{p.get('ID')} · {p.get('Nombre')}": p.get("ID") for p in proys}
    # Proyecto pendiente de abrir (viene del Survey al guardar). Se aplica antes
    # de instanciar el selectbox, nunca despues.
    _pp = st.session_state.pop("_prjsel_pending", None)
    if _pp:
        _match = next((k for k in idmap if k.startswith(str(_pp))), None)
        if _match:
            st.session_state["adminproj_sel"] = _match
    # ⚠️ Opción vacía la PRIMERA: un selectbox sin placeholder devuelve siempre
    # el primer elemento, asi que al entrar se abria el detalle de un proyecto
    # arbitrario — ruido visual y 8 lecturas de datos que nadie pidio.
    _opts = [_VACIO] + list(idmap.keys())
    sel = st.selectbox("Proyecto", _opts, key="adminproj_sel",
                       label_visibility="collapsed")
    if sel and sel != _VACIO:
        st.markdown("---")
        _detalle_proyecto(idmap[sel], grupo)
    else:
        st.caption("Elige un proyecto de la lista para ver su detalle.")


def _portfolio_html(proys, horas, alarmas, ags, delays=None, aheads=None,
                    show_group=False) -> str:
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
        hrs = horas.get(str(p.get("ID", "")), 0.0)
        na  = alarmas.get(pid, 0)
        ag  = ags.get(str(p.get("AgrupacionID", "")), "")
        sub = f"{pid} · {str(p.get('Cliente','')) or '—'}" + (f" · {ag}" if ag else "")
        if show_group and p.get("Grupo"):
            sub = f"🏢 {p.get('Grupo')} · " + sub
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


def _diagnostico(ps: dict) -> dict:
    """Traduce el cronograma a lo accionable. Todo sale de `ps`; no lee nada nuevo.

    ⚠️ "SPI 0.47" no le dice nada a nadie en obra. Lo que sí: a qué ritmo vas, a
    qué ritmo tendrías que ir, **qué actividad tocaba hoy y sigue sin arrancar**
    y cuál es el próximo hito. Eso es lo que explica el retraso; el % solo lo
    constata.
    """
    sched = ps["sched"]
    acts  = sched["activities"]
    av    = ps.get("avances") or []
    proj  = ps.get("proj") or {}
    hoy   = ps["today_day"]
    total = max(1, sched["total_dias"])
    ini   = sched["start_date"]

    ev = proj.get("ev", 0.0)

    # Ritmo: %/dia hecho vs %/dia que hace falta para llegar a la fecha
    ritmo_real = (ev / hoy) if hoy and hoy > 0 else None
    dias_rest  = total - hoy
    ritmo_nec  = ((100.0 - ev) / dias_rest) if dias_rest > 0 else None
    factor     = (ritmo_nec / ritmo_real) if (ritmo_real and ritmo_real > 0.01
                                              and ritmo_nec) else None

    tocaban, en_curso, proximo = [], [], None
    for i, a in enumerate(acts):
        pct  = float(av[i]) if i < len(av) else 0.0
        fin  = a["inicio"] + a["duracion"]
        f_i  = ini + timedelta(days=int(a["inicio"]))
        # `inicio < hoy` (estricto): el dia en que se abre la ventana aun no
        # cuenta como retraso — si no, un proyecto recien creado nace en rojo.
        if a["inicio"] < hoy <= fin and pct < 100:
            tocaban.append({"nombre": a["nombre"], "avance": pct,
                            "desde": f_i, "dur": a["duracion"]})
        if 0 < pct < 100:
            en_curso.append({"nombre": a["nombre"], "avance": pct,
                             "tarde": hoy > fin})     # arrastrada: ya paso su ventana
        if proximo is None and a["inicio"] > hoy:
            proximo = {"nombre": a["nombre"], "fecha": f_i,
                       "faltan": a["inicio"] - hoy}

    # Sin arrancar y ya tocaba: es LA causa del retraso, no un detalle
    paradas = [x for x in tocaban if x["avance"] <= 0]
    return {"ritmo_real": ritmo_real, "ritmo_nec": ritmo_nec, "factor": factor,
            "dias_rest": dias_rest, "tocaban": tocaban, "paradas": paradas,
            "en_curso": en_curso, "arrastradas": [x for x in en_curso if x["tarde"]],
            "proximo": proximo, "ev": ev, "pv": proj.get("pv", 0.0)}


def _estado_section(pid: str, grupo: str, prj: dict):
    """Pestaña 📊 Estado: alarmas, cronograma y el diagnostico de por que vas asi."""
    _alerts_section(pid, grupo, prj.get("Nombre", ""), allow_report=False)

    ps = P.project_schedule(pid)
    if not (ps and ps["sched"].get("activities")):
        st.info("Este proyecto no tiene actividades, así que no hay cronograma "
                "que seguir. Añádelas en ✏️ Datos.")
        return

    d    = _diagnostico(ps)
    proj = ps.get("proj") or {}
    dv   = proj.get("desvio", 0.0)
    dg   = proj.get("dias_gap", 0.0)

    # ── Titular: una frase que diga como va, antes de cualquier numero ──
    if dv <= -1:
        _tit, _col = (f"Vas **{abs(dv):.0f} puntos por debajo** del plan", "#c0392b")
    elif dv >= 1:
        _tit, _col = (f"Vas **{dv:.0f} puntos por encima** del plan", "#1e8449")
    else:
        _tit, _col = ("Vas **en línea con el plan**", "#2e6da4")
    # ⚠️ proj["today_day"] viene CLAMPADO al total: en un proyecto pasado de fecha
    # diria "día 29 de 29" llevando 40. El real es ps["today_day"].
    _hoy_real = ps["today_day"]
    _tot      = proj.get("total", 0)
    _dia_txt  = (f"día {_hoy_real} de {_tot}" if _hoy_real <= _tot
                 else f"día {_hoy_real} — {_hoy_real - _tot} más de los {_tot} planificados")
    st.markdown(f"<div style='font-size:17px;margin-bottom:8px'>{_tit} "
                f"<span style='color:#6b7280;font-size:14px'>· {_dia_txt}</span></div>",
                unsafe_allow_html=True)

    # ── KPIs (tarjetas, no st.metric planos) ──
    _fin = (proj["fecha_proj"].strftime("%d/%m/%Y")
            if proj.get("fecha_proj") else "—")
    _pd  = proj.get("proj_dias")
    _cf  = "#c0392b" if (_pd is not None and _pd > 0.5) else (
           "#1e8449" if (_pd is not None and _pd < -0.5) else None)
    _est = ("En fecha" if abs(dg) < 0.5
            else f"{abs(dg):.0f} d {'de retraso' if dg > 0 else 'de adelanto'}")
    tarj = [_kpi_card("Avance real", f"{d['ev']:.0f}%"),
            _kpi_card("Debería ir", f"{d['pv']:.0f}%"),
            _kpi_card("Desvío", f"{dv:+.0f}%", _col),
            _kpi_card("Situación", _est, "#c0392b" if dg > 0.5 else None),
            _kpi_card("Fin proyectado", _fin, _cf)]
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:10px">'
                + "".join(tarj) + "</div>", unsafe_allow_html=True)

    # ── El ritmo: mas accionable que el SPI ──
    if d["ritmo_real"] is not None and d["ritmo_nec"] is not None:
        if d["dias_rest"] <= 0:
            st.warning(f"⏱ La fecha de fin planificada ya pasó y queda "
                       f"**{100 - d['ev']:.0f}%** por completar.")
        elif d["factor"] and d["factor"] > 1.15:
            st.error(f"⏱ Vas a **{d['ritmo_real']:.1f} %/día** y necesitas "
                     f"**{d['ritmo_nec']:.1f} %/día** para llegar a la fecha: "
                     f"hay que **acelerar ×{d['factor']:.1f}** en los "
                     f"{d['dias_rest']:.0f} días que quedan.")
        elif d["factor"] and d["factor"] < 0.85:
            st.success(f"⏱ Vas a **{d['ritmo_real']:.1f} %/día** y con "
                       f"**{d['ritmo_nec']:.1f} %/día** llegas: hay margen.")
        else:
            st.info(f"⏱ Vas a **{d['ritmo_real']:.1f} %/día**, justo el ritmo "
                    f"que hace falta ({d['ritmo_nec']:.1f} %/día).")

    # ── Que tocaba hoy vs que se esta haciendo: el porque del retraso ──
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**📌 Tocaba hoy**")
        if not d["tocaban"]:
            st.caption("Ninguna actividad tiene su ventana abierta hoy.")
        for x in d["tocaban"]:
            if x["avance"] <= 0:
                st.markdown(f"🔴 **{x['nombre']}** — sin empezar, arrancaba el "
                            f"{x['desde'].strftime('%d/%m')} ({x['dur']:.0f} d)")
            else:
                st.markdown(f"🟢 {x['nombre']} — {x['avance']:.0f}%")
    with c2:
        st.markdown("**🔧 En curso ahora**")
        if not d["en_curso"]:
            st.caption("Ninguna actividad entre 1% y 99%.")
        for x in d["en_curso"]:
            st.markdown(("⏳ " if x["tarde"] else "▶️ ")
                        + f"{x['nombre']} — {x['avance']:.0f}%"
                        + (" _(arrastrada)_" if x["tarde"] else ""))

    # El diagnostico: el equipo sigue en trabajo viejo y lo de hoy no arranca
    if d["paradas"] and d["arrastradas"]:
        st.warning("🩺 El equipo sigue terminando **"
                   + ", ".join(x["nombre"] for x in d["arrastradas"][:3])
                   + "**, así que **"
                   + ", ".join(x["nombre"] for x in d["paradas"][:3])
                   + "** aún no ha arrancado. Ahí está el retraso.")
    elif d["paradas"]:
        st.warning("🩺 Sin empezar y ya tocaba: **"
                   + ", ".join(x["nombre"] for x in d["paradas"][:3]) + "**.")

    if d["proximo"]:
        st.caption(f"🎯 Próximo hito: **{d['proximo']['nombre']}** arranca el "
                   f"{d['proximo']['fecha'].strftime('%d/%m/%Y')} "
                   f"(en {d['proximo']['faltan']:.0f} días).")

    # ── La grafica ──
    st.markdown("**📆 Cronograma y avance**")
    n = len(ps["sched"]["activities"])
    components.html(
        '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
        + schedule_svg(ps["sched"], real_curve=ps["real"], today_day=ps["today_day"],
                       avances=ps.get("avances"), proj=proj,
                       titulo=prj.get("Nombre", ""))
        + '</body></html>',
        height=int(300 + n * 21), scrolling=False,
    )
    st.caption("La **banda de color** entre las dos curvas es la brecha contra el "
               "plan (roja si vas por detrás, verde si por delante). ● rojo = la "
               "actividad ya debería haber arrancado.")


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
    c2.metric("Horas trabajadas",
              f"{P.project_hours(prj.get('Nombre'), grupo, pid=pid):.1f}")
    st.progress(min(1.0, avance / 100.0))

    # ── Sub-navegacion: 11 secciones en un scroll unico era el mismo
    # problema que tenia el Survey antes de v114. Radio, NO st.tabs (v56).
    _sec = st.radio("Sección del proyecto",
                    ["📊 Estado", "✏️ Datos", "💰 Costos", "📎 Archivos"],
                    horizontal=True, key="prj_detalle_sec",
                    label_visibility="collapsed")
    st.markdown("---")

    if _sec == "📊 Estado":
        # ── Alarmas / avisos del proyecto ──
        _estado_section(pid, grupo, prj)

    elif _sec == "✏️ Datos":
        # ── Instrucciones e inducciones ──
        _induccion_section(pid, prj, grupo, allow_send=True)


        # ── Asignar campo: FUERA del form ──
        # Dentro de un `st.form` los widgets no escriben en session_state hasta
        # el submit, asi que un aviso "en vivo" ahi dentro es imposible. Es el
        # mismo motivo por el que v127 lo saco del form en el Survey; aqui se
        # habia quedado dentro, y asignar gente a un proyecto EXISTENTE es la
        # accion del dia a dia.
        _campos_disp = _field_users(grupo)
        _actuales = [x.strip() for x in str(prj.get("CampoAsignados", "")).split(";")
                     if x.strip()]
        _opts = sorted(set(_campos_disp) | set(_actuales))
        asignados = st.multiselect("👷 Usuarios de campo asignados", _opts,
                                   default=_actuales, key=f"asig_{pid}")
        _avisar_asignados(asignados)      # credenciales vencidas / contacto faltante

        # ── Editar datos ──
        with st.form(f"edit_{pid}"):
            st.markdown("**Datos del proyecto**")
            e1, e2 = st.columns(2)
            nombre   = e1.text_input("Nombre", value=prj.get("Nombre", ""))
            cliente  = e2.text_input("Cliente", value=prj.get("Cliente", ""))
            ubic     = e1.text_input("Ubicación", value=prj.get("Ubicacion", ""))
            modelo   = e2.text_input("Modelo", value=prj.get("Modelo", ""))
            ing      = e1.text_input("Ingeniero", value=prj.get("Ingeniero", ""))
            # Calendario, no texto libre: ver `_a_fecha`. El valor se guarda
            # siempre en ISO, que es lo unico que `project_schedule` sabe leer.
            f_ini    = e2.date_input("Fecha inicio", value=_a_fecha(prj.get("FechaInicio")),
                                     format="YYYY-MM-DD")
            f_fin    = e1.date_input("Fecha fin estimada", value=_a_fecha(prj.get("FechaFinEst")),
                                     format="YYYY-MM-DD")
            instr    = st.text_area("📌 Instrucciones particulares", value=prj.get("Instrucciones", ""))
            ind      = st.text_area("📝 Inducciones (un link por línea)",
                                    value=prj.get("InduccionLinks", ""),
                                    help="Al asignar un usuario de campo se le envían por Telegram/email.")

            actuales = _actuales

            ags = P.list_groupings(grupo=grupo)
            ag_opts = ["(ninguna)"] + [f"{a['ID']} · {a['Nombre']}" for a in ags]
            ag_cur  = str(prj.get("AgrupacionID", ""))
            ag_idx  = next((i for i, a in enumerate(ags) if a["ID"] == ag_cur), None)
            ag_sel  = st.selectbox("Agrupación", ag_opts,
                                   index=(ag_idx + 1) if ag_idx is not None else 0)
            # Peso por defecto 1: si queda en 0 el avance de la agrupación da 0
            # aunque los elevadores estén al 100% (Σpeso·avance / Σpeso).
            peso    = st.number_input("Peso en la agrupación", min_value=0.0, step=0.5,
                                      value=P._num(prj.get("PesoEnAgrupacion")) or 1.0,
                                      help="Cuánto pesa este elevador en el avance "
                                           "consolidado de su agrupación.")
            est_man = st.selectbox("Estado manual (override)", P.ESTADOS_MANUAL,
                                   index=P.ESTADOS_MANUAL.index(str(prj.get("EstadoManual", "")))
                                   if str(prj.get("EstadoManual", "")) in P.ESTADOS_MANUAL else 0)
            presup  = st.number_input("💰 Presupuesto del proyecto (0 = sin presupuesto)",
                                      min_value=0.0, step=100.0, value=P._num(prj.get("Presupuesto")))

            if st.form_submit_button("💾 Guardar cambios", use_container_width=True):
                # Validar sin `st.stop()`: pararia el render de TODO lo que va
                # debajo (actividades, archivar...) y la pagina quedaria a medias.
                _err = ""
                if not str(nombre).strip():
                    _err = "El nombre del proyecto no puede quedar vacío."
                elif f_ini and f_fin and f_fin < f_ini:
                    _err = "La fecha de fin no puede ser anterior a la de inicio."
                f_ini, f_fin = _iso(f_ini), _iso(f_fin)
                if _err:
                    st.error(_err)
                else:
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
                _orden = ui.elegir("Actividad a eliminar", _dmap, key=f"delact_{pid}",
                                   vacio="— ninguna —")
                if _orden is not None:
                    _ok_del = ui.confirmar_borrado(f"delactok_{pid}",
                                                   "Confirmo eliminar esta actividad")
                    if st.button("Eliminar", key=f"delactb_{pid}", disabled=not _ok_del):
                        ok, msg = P.delete_activity(pid, _orden)
                        (st.success if ok else st.error)(msg)
                        if ok:
                            _aviso_cambio("Se eliminó una actividad del cronograma.")
                            st.rerun()
        # ── Archivar / eliminar ──
        _archivado = str(prj.get("Estado", "")) == P.ARCHIVADO
        if _archivado:
            st.info("📦 Este proyecto está **archivado**: no aparece en las listas "
                    "ni en los informes, pero no se ha perdido nada.")
            if st.button("♻️ Restaurar proyecto", key=f"unarch_{pid}",
                         use_container_width=True):
                ok, msg = P.set_archivado(pid, False)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()
        else:
            with st.expander("📦 Archivar proyecto"):
                st.caption("Desaparece de las listas y de los informes, pero se "
                           "conserva entero y puede restaurarse cuando quieras. "
                           "Es lo recomendado al cerrar una obra.")
                if st.button("📦 Archivar", key=f"arch_{pid}", use_container_width=True):
                    ok, msg = P.set_archivado(pid, True)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()

        # Borrado de verdad: SOLO propietario. `delete_project` quita el proyecto
        # y sus actividades, pero deja huerfanos documentos (con sus archivos en
        # Drive), gastos, calculos, pre-starts, alarmas y fichajes — por eso se
        # enseña el inventario antes y se exige teclear el nombre.
        if st.session_state.get("auth", {}).get("rol") == "propietario":
            with st.expander("🗑 Eliminar definitivamente (irreversible)"):
                _aso = P.datos_asociados(pid)
                _hay = {k: v for k, v in _aso.items() if v}
                st.warning("Se borrarán el proyecto y sus actividades. **No se puede "
                           "deshacer.** Casi siempre lo que quieres es archivarlo.")
                if _hay:
                    st.markdown("Quedará sin proyecto: "
                                + " · ".join(f"**{v}** {k.lower()}"
                                             for k, v in _hay.items()))
                    st.caption("Esas filas y sus archivos en Drive NO se borran: "
                               "quedan apuntando a un proyecto que ya no existe.")
                _tecleado = st.text_input(
                    f"Escribe «{prj.get('Nombre','')}» para confirmar", key=f"delnom_{pid}")
                if st.button("Eliminar definitivamente", key=f"del_{pid}",
                             use_container_width=True,
                             disabled=(_tecleado.strip() != str(prj.get("Nombre", "")).strip())):
                    ok, msg = P.delete_project(pid)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()

    elif _sec == "💰 Costos":
        # ── Gastos / compras ──
        render_expenses(pid, grupo, can_delete=True, key_prefix="adm")

    elif _sec == "📎 Archivos":
        _plano_section(pid, prj)
        st.markdown("---")

        # ── Reconstruir el survey guardado ──
        with st.expander("🔄 Reconstruir proyecto en el Survey (regenerar informes)"):
            st.caption("Carga los parámetros y la matriz guardados en la pestaña 📐 Survey. "
                       "Luego pulsa **Calcular** allí para regenerar diagramas e informes.")
            if st.button("🔄 Cargar este proyecto en el Survey", key=f"rebuild_{pid}"):
                full = P.get_project_full(pid)
                params, matriz = full.get("params") or {}, full.get("matriz") or []
                if not params:
                    st.error("Este proyecto no tiene parámetros guardados.")
                else:
                    for k, v in params.items():
                        try:
                            st.session_state[f"inp_{k}"] = float(v)
                        except Exception:
                            pass
                    if params.get("NS"):
                        try:
                            st.session_state["ns"] = int(float(params["NS"]))
                        except Exception:
                            pass
                    if matriz:
                        try:
                            st.session_state["survey_df"] = pd.DataFrame(matriz)
                        except Exception:
                            pass
                    st.session_state["proyecto"]  = str(prj.get("Nombre", ""))
                    st.session_state["ingeniero"] = str(prj.get("Ingeniero", ""))
                    st.session_state["_rebuilt_from"] = str(prj.get("Nombre", ""))
                    st.success("✅ Cargado. Ve a **📐 Survey** y pulsa **Calcular** para regenerar todo.")
        # ── Cálculos de herramientas ──
        _calculos_section(pid)

        # ── Documentos ──
        _documentos_section(pid)



# ── Panel de agrupaciones ────────────────────────────────────────
def _dashboard_agrupacion(ag, grupo):
    """Vista consolidada de una agrupación (un edificio con varios elevadores).

    ⚠️ El avance consolidado (promedio ponderado) NO responde la pregunta que
    importa: el edificio se entrega cuando termina **el último** elevador, no el
    promedio. De ahí la fecha de entrega del conjunto y el elevador crítico.
    """
    from core import expenses as E
    aid = ag["ID"]
    proys = P.list_projects(grupo=grupo, agrupacion_id=aid)
    if not proys:
        st.info("Esta agrupación aún no tiene elevadores. Añádelos abajo.")
        return

    pr      = P.grouping_progress(aid)
    delays  = P.delays_of_group(grupo)
    aheads  = P.aheads_of_group(grupo)
    horas   = P.project_hours_bulk(grupo)
    alarmas = alerts.open_counts_all() if alerts.is_configured() else {}
    proj    = P.grouping_projection(aid, grupo)

    tot_h    = sum(horas.get(str(p.get("ID", "")), 0.0) for p in proys)
    costos   = [E.project_cost(p.get("ID"), grupo) for p in proys] if E.is_configured() else []
    tot_c    = sum(c["total"] for c in costos)
    tot_pres = sum(c["presupuesto"] for c in costos)
    n_alarm  = sum(alarmas.get(str(p.get("ID", "")), 0) for p in proys)
    n_retras = sum(1 for p in proys if str(p.get("ID", "")) in delays)

    # ── Tarjetas KPI (mismo lenguaje que la cartera de proyectos) ──
    _fecha = (proj["fecha"].strftime("%d/%m/%Y") if proj.get("fecha") else "—")
    _col_f = "#c0392b" if n_retras else "#1e8449"
    tarjetas = [
        _kpi_card("Avance consolidado", f"{pr['avance']:.0f}%"),
        _kpi_card("Elevadores", pr["n_proyectos"]),
        _kpi_card("Entrega del conjunto", _fecha, _col_f),
        _kpi_card("Con retraso", n_retras, "#c0392b" if n_retras else None),
        _kpi_card("Alarmas", n_alarm, "#c0392b" if n_alarm else None),
        _kpi_card("Horas", f"{tot_h:.0f}"),
        _kpi_card("Costo total", f"${tot_c:,.0f}"),
    ]
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:10px">'
                + "".join(tarjetas) + "</div>", unsafe_allow_html=True)
    st.progress(min(1.0, pr["avance"] / 100.0))

    # ── Quién manda la fecha de entrega ──
    if proj.get("critico"):
        _d = delays.get(proj["critico_id"])
        st.markdown(
            f"🎯 **La entrega la marca «{proj['critico']}»** — proyectada para "
            f"**{_fecha}**" + (f", con **{_d:.0f} días de retraso**." if _d else
                               ", en fecha.")
            + "  Es donde más rinde reforzar.")
    if proj.get("sin_datos"):
        st.caption("Sin cronograma para proyectar: " + ", ".join(proj["sin_datos"]))

    if tot_pres > 0:
        _p = round(100 * tot_c / tot_pres)
        (st.error if tot_c > tot_pres else st.caption)(
            f"Presupuesto de la agrupación ${tot_pres:,.0f} · {_p}% consumido"
            + (" ⛔ SOBRE PRESUPUESTO" if tot_c > tot_pres else ""))

    # ── Curva S CONSOLIDADA (plan vs real de todo el conjunto) ──
    try:
        cur = P.grouping_curve(aid, grupo)
    except Exception:
        cur = {}
    if cur and cur.get("fechas"):
        st.markdown("**📈 Avance del conjunto — plan vs real**")
        _df = pd.DataFrame({"Planificado": cur["plan"], "Real": cur["real"]},
                           index=pd.to_datetime(cur["fechas"]))
        st.line_chart(_df, height=240)
        st.caption("Ponderado por el peso de cada elevador. La curva real se corta en HOY.")

    # ── Comparativa entre elevadores ──
    # En un edificio son unidades casi gemelas, así que la desviación respecto
    # al promedio delata al que se sale de lo normal.
    st.markdown("**🔍 Comparativa entre elevadores**")
    _hs = [horas.get(str(p.get("ID", "")), 0.0) for p in proys]
    _cs = [c.get("total", 0) for c in costos] if costos else [0] * len(proys)
    _hm = (sum(_hs) / len(_hs)) if _hs else 0
    _cm = (sum(_cs) / len(_cs)) if _cs else 0

    def _dev(v, med):
        if med <= 0:
            return ""
        d = round(100 * (v - med) / med)
        return f"{d:+d}%" if abs(d) >= 15 else "≈"

    rows = []
    for i, p in enumerate(proys):
        pid = str(p.get("ID", ""))
        _na = alarmas.get(pid, 0)
        _pf = next((x["fecha"] for x in proj.get("detalle", []) if x["id"] == pid), None)
        rows.append({
            "Elevador": p.get("Nombre"), "Estado": p.get("Estado"),
            "Avance %": P._num(p.get("Avance")),
            "Peso": P._num(p.get("PesoEnAgrupacion")),
            "Entrega prev.": _pf.strftime("%d/%m") if _pf else "—",
            "⏰/⏩": (f"⏰ {delays[pid]:.0f} d" if pid in delays
                     else (f"⏩ {aheads[pid]:.0f} d" if pid in aheads else "en fecha")),
            "Horas": _hs[i], "vs media h": _dev(_hs[i], _hm),
            "Costo": _cs[i], "vs media $": _dev(_cs[i], _cm),
            "🔔": _na or "",
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    st.caption("«vs media» compara cada elevador con el promedio de la agrupación; "
               "solo se marca si se desvía 15% o más.")

    _out = [r["Elevador"] for r in rows if r["vs media h"].startswith("+")]
    if _out:
        st.info("⚠️ Consumen bastantes más horas que sus gemelos: **"
                + ", ".join(_out) + "**. Vale la pena mirar por qué.")

    st.bar_chart(pd.DataFrame({"Avance %": [r["Avance %"] for r in rows]},
                              index=[r["Elevador"] for r in rows]))



def _agrupaciones_html(ags, grupo) -> str:
    """Tarjetas de agrupación — mismo lenguaje que la cartera de proyectos.

    La idea es ver lo relevante de cada edificio SIN entrar: cuántos elevadores,
    avance consolidado, **cuándo se entrega el conjunto** y si algún elevador la
    está retrasando. La tabla plana anterior no decía nada de eso.
    """
    proys_all = P.list_projects(grupo=grupo)
    horas     = P.project_hours_bulk(grupo)
    alarmas   = alerts.open_counts_all() if alerts.is_configured() else {}
    proyecc   = P.projections_by_group(grupo)      # cacheado 60 s
    from core import expenses as E
    hay_costos = E.is_configured()

    parts = []
    for a in ags:
        aid   = str(a.get("ID", ""))
        miemb = [p for p in proys_all if str(p.get("AgrupacionID", "")) == aid]
        pr    = P.grouping_progress(aid)
        av    = pr["avance"]

        # Fecha del conjunto = la del elevador MÁS LENTO (no el promedio)
        fecha, critico, gap = None, "", 0.0
        for p in miemb:
            d = proyecc.get(str(p.get("ID", "")))
            if not d or not d.get("fecha"):
                continue
            if fecha is None or d["fecha"] > fecha:
                fecha, critico, gap = d["fecha"], str(p.get("Nombre", "")), d.get("gap") or 0.0

        n_al  = sum(alarmas.get(str(p.get("ID", "")), 0) for p in miemb)
        hrs   = sum(horas.get(str(p.get("ID", "")), 0.0) for p in miemb)
        costo = (sum(E.project_cost(p.get("ID"), grupo)["total"] for p in miemb)
                 if hay_costos and miemb else 0)

        borde = "border:1px solid #e6e9ef"
        badge = ""
        if gap and gap > 0.5:
            borde = "border:1px solid #e6e9ef;border-left:4px solid #c0392b"
            badge = (f'<span style="font-size:12px;padding:3px 9px;border-radius:20px;'
                     f'background:#fcebeb;color:#a32d2d;white-space:nowrap;flex:none;'
                     f'font-weight:600;">⏰ {gap:.0f} d</span>')
        elif gap and gap < -0.5:
            borde = "border:1px solid #e6e9ef;border-left:4px solid #1e8449"
            badge = (f'<span style="font-size:12px;padding:3px 9px;border-radius:20px;'
                     f'background:#eaf3de;color:#3b6d11;white-space:nowrap;flex:none;'
                     f'font-weight:600;">⏩ {abs(gap):.0f} d</span>')
        punto = "#c0392b" if (gap and gap > 0.5) else ("#1e8449" if av >= 100 else "#2e6da4")

        sub = f"{aid} · {len(miemb)} elevador(es)"
        if a.get("Descripcion"):
            sub += f" · {a['Descripcion']}"
        entrega = (f'<div style="font-size:11.5px;color:#6b7280;">🎯 entrega '
                   f'<b>{fecha.strftime("%d/%m/%Y")}</b>'
                   + (f' — la marca {critico}' if critico else "") + '</div>'
                   if fecha else
                   '<div style="font-size:11.5px;color:#9aa7b8;">sin cronograma para proyectar</div>')
        alarm = (f'<div style="width:44px;text-align:center;flex:none;color:#c0392b;'
                 f'font-size:12.5px;font-weight:600;">🔔 {n_al}</div>'
                 if n_al else '<div style="width:44px;flex:none;"></div>')

        parts.append(
            f'<div style="display:flex;align-items:center;gap:12px;padding:11px 14px;'
            f'{borde};border-radius:10px;margin-bottom:8px;background:#fff;">'
            f'<div style="width:9px;height:9px;border-radius:50%;background:{punto};flex:none;"></div>'
            '<div style="flex:1;min-width:0;">'
            f'<div style="font-size:14px;font-weight:600;color:#1f2937;white-space:nowrap;'
            f'overflow:hidden;text-overflow:ellipsis;">🗂 {a.get("Nombre","")}</div>'
            f'<div style="font-size:12px;color:#6b7280;white-space:nowrap;overflow:hidden;'
            f'text-overflow:ellipsis;">{sub}</div>' + entrega +
            '</div>' + badge +
            '<div style="width:118px;flex:none;">'
            '<div style="height:7px;background:#eef1f5;border-radius:20px;overflow:hidden;">'
            f'<div style="height:7px;width:{min(100, max(0, av)):.0f}%;background:{punto};"></div>'
            '</div>'
            f'<div style="font-size:11.5px;color:#6b7280;margin-top:3px;text-align:right;">'
            f'{av:.0f}%</div></div>'
            f'<div style="width:74px;text-align:right;flex:none;font-size:12px;color:#6b7280;">'
            f'{hrs:.0f} h' + (f'<br>${costo:,.0f}' if costo else '') + '</div>'
            + alarm + '</div>')
    return "".join(parts)


def _miembros_editor(ags_proys, todos, key, pesos_actuales=None):
    """Tabla para elegir QUÉ proyectos componen una agrupación y con qué peso.

    Devuelve {pid: peso} de los marcados. Peso por defecto **1** (todos cuentan
    igual): antes había que ponerlo a mano en cada proyecto y, si quedaba en 0,
    el avance de la agrupación daba 0 aunque los elevadores fueran al 100%.
    """
    pesos_actuales = pesos_actuales or {}
    filas = []
    for p in todos:
        pid = str(p.get("ID", ""))
        otra = str(p.get("AgrupacionID", ""))
        filas.append({
            "En la agrupación": pid in pesos_actuales,
            "Proyecto": f"{p.get('Nombre')} ({pid})",
            "Peso": float(pesos_actuales.get(pid, 1.0)),
            "Avance %": P._num(p.get("Avance")),
            "Ya en otra": (ags_proys.get(otra, "") if otra and otra not in
                           (None, "") and pid not in pesos_actuales else ""),
        })
    if not filas:
        st.caption("No hay proyectos en el grupo todavía.")
        return {}
    ed = st.data_editor(
        pd.DataFrame(filas), hide_index=True, use_container_width=True,
        num_rows="fixed", key=key,
        disabled=["Proyecto", "Avance %", "Ya en otra"],
        column_config={
            "En la agrupación": st.column_config.CheckboxColumn(width="small"),
            "Peso": st.column_config.NumberColumn(
                min_value=0.0, step=0.5,
                help="Cuánto pesa este elevador en el avance consolidado."),
            "Ya en otra": st.column_config.TextColumn(
                "⚠️ Ya en otra", help="Marcarlo aquí lo MUEVE a esta agrupación."),
        })
    out = {}
    for _, r in ed.iterrows():
        if bool(r["En la agrupación"]):
            pid = str(r["Proyecto"]).rsplit("(", 1)[-1].rstrip(")")
            out[pid] = float(r["Peso"] or 1.0)
    return out


def _panel_agrupaciones(grupo: str):
    ags = P.list_groupings(grupo=grupo)
    todos = P.list_projects(grupo=grupo)
    nom_ags = {a["ID"]: a["Nombre"] for a in ags}

    if ags:
        st.markdown(f"**Agrupaciones — {len(ags)}**")
        st.markdown(_agrupaciones_html(ags, grupo), unsafe_allow_html=True)

        # ── Abrir una agrupación (sin preselección: v138/v139) ──
        st.markdown("#### 📊 Abrir agrupación")
        _amap = {f"{a['ID']} · {a['Nombre']}": a for a in ags}
        _ag = ui.elegir("Agrupación", _amap, key="agr_dash_sel",
                        vacio="— elige una agrupación —", label_visibility="collapsed")
        if _ag:
            _dashboard_agrupacion(_ag, grupo)
            st.markdown("---")
            with st.expander("🔧 Proyectos de esta agrupación"):
                st.caption("Marca los elevadores que la componen. Al quitar uno se "
                           "**desagrupa**, no se borra.")
                _act = {str(p.get("ID")): P._num(p.get("PesoEnAgrupacion")) or 1.0
                        for p in P.list_projects(grupo=grupo,
                                                 agrupacion_id=_ag["ID"])}
                _sel = _miembros_editor(nom_ags, todos, f"agmem_{_ag['ID']}", _act)
                if len(_sel) > 12:
                    st.warning(f"{len(_sel)} proyectos: cada cambio es una escritura "
                               "en la hoja; puede tardar unos segundos.")
                if st.button("💾 Guardar los proyectos de la agrupación",
                             key=f"agmemsave_{_ag['ID']}", use_container_width=True):
                    with st.spinner("Guardando..."):
                        ok, msg = P.set_grouping_members(_ag["ID"], _sel, grupo)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()
    else:
        st.info("No hay agrupaciones. Crea una abajo y elige qué elevadores la componen.")

    # ── Crear: la agrupación se arma CON sus proyectos (v141) ──
    # Plegada, como "➕ Nuevo proyecto": no es lo que se viene a hacer a diario.
    with st.expander("➕ Nueva agrupación"):
        st.caption("Los proyectos se crean primero; aquí eliges cuáles forman parte.")
        nom = st.text_input("Nombre de la agrupación", key="nueva_agr_nom")
        des = st.text_input("Descripción (opcional)", key="nueva_agr_des")
        _nuevos = _miembros_editor(nom_ags, todos, "agmem_nueva")
        if st.button("Crear agrupación", key="nueva_agr_btn", use_container_width=True):
            if not nom.strip():
                st.error("El nombre es obligatorio.")
            else:
                ok, res = P.create_grouping(grupo, nom.strip(), des.strip())
                if not ok:
                    st.error(res)
                else:
                    _n = 0
                    if _nuevos:
                        with st.spinner("Asignando proyectos..."):
                            ok2, msg2 = P.set_grouping_members(res, _nuevos, grupo)
                        _n = len(_nuevos)
                        if not ok2:
                            st.warning(f"Agrupación creada, pero: {msg2}")
                    st.success(f"Agrupación creada ({res})"
                               + (f" con {_n} elevador(es)." if _n else
                                  ". Añádele elevadores desde su panel."))
                    st.rerun()

    if ags:
        st.markdown("#### 🗑 Eliminar agrupación")
        delmap = {f"{a['ID']} · {a['Nombre']}": a["ID"] for a in ags}
        _agr = ui.elegir("Agrupación", delmap, key="del_agr_sel",
                         vacio="— ninguna —")
        st.caption("Los proyectos no se borran; solo se desagrupan.")
        if _agr:
            _ok_del = ui.confirmar_borrado("del_agr_ok",
                                           "Confirmo eliminar esta agrupación")
            if st.button("Eliminar agrupación", disabled=not _ok_del):
                ok, msg = P.delete_grouping(_agr)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()



# ── Panel del PROPIETARIO: todos los proyectos (todos los grupos) ──
def render_owner_projects():
    st.markdown("### 📁 Todos los proyectos")
    if not P.is_configured():
        st.warning("La gestión de proyectos necesita Google Sheets configurado.")
        return
    _ver_arch = st.checkbox("📦 Ver también los archivados", key="ver_arch_owner")
    proys = P.list_projects(incluir_archivados=_ver_arch)   # todos los grupos
    _grupos = []
    try:
        _grupos = [g["Grupo"] for g in auth.list_groups(only_active=True)]
    except Exception:
        pass
    if _grupos:
        _g = st.selectbox("Grupo para el nuevo proyecto", _grupos, key="own_np_grupo")
        _nuevo_proyecto_form(_g, key="own")
    if not proys:
        if not _grupos:
            st.info("Aún no hay grupos. Crea uno en **🏢 Grupos** para poder "
                    "registrar proyectos.")
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
            "Horas":     P.project_hours(p.get("Nombre"), p.get("Grupo"),
                                        pid=str(p.get("ID", ""))),
            "Agrupación": ags.get(str(p.get("AgrupacionID", "")), ""),
        })
    # Cartera de tarjetas (mismo look del admin) + tabla detallada abajo
    _hb = {}
    for p in proys:
        _hb[str(p.get("ID", ""))] = P.project_hours(p.get("Nombre"), p.get("Grupo"),
                                                    pid=str(p.get("ID", "")))
    st.markdown(f"**Cartera — {len(proys)} proyecto(s)**"
                + (f"  ·  🔴 {len(delays)} con retraso" if delays else "")
                + (f"  ·  🟢 {len(aheads)} adelantado(s)" if aheads else ""))
    st.markdown(_portfolio_html(proys, _hb, alarmas, ags, delays, aheads, show_group=True),
                unsafe_allow_html=True)

    with st.expander("📋 Ver tabla detallada"):
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                     column_config={"🗺": st.column_config.LinkColumn("🗺", display_text="Abrir")})

    st.markdown("#### 🔎 Abrir proyecto")
    idmap = {f"{p.get('Grupo')} · {p.get('ID')} · {p.get('Nombre')}": p.get("ID") for p in proys}
    _opts = [_VACIO] + list(idmap.keys())
    sel = st.selectbox("Proyecto", _opts, key="ownerproj_sel")
    if sel and sel != _VACIO:
        _detalle_proyecto(idmap[sel])


# ── Pestaña del usuario de CAMPO: mis proyectos ──────────────────
def _field_activities(pid):
    """Tabla editable del avance del campo (v162): una tabla, un guardado.

    Antes eran N expandibles con un guardado cada uno (hasta 5 update_cell por
    actividad). Ahora `save_field_progress` escribe solo lo que cambio en 1 batch,
    y las fechas reales se registran solas (no se teclean).
    """
    st.markdown("#### Actividades — actualiza tu avance")
    acts = P.list_activities(pid)
    if not acts:
        st.caption("Este proyecto no tiene actividades registradas.")
        return
    _df = pd.DataFrame([{
        "N": int(P._num(a.get("Orden"))),
        "Actividad": a.get("Nombre"),
        "Avance %": int(P._num(a.get("Avance"))),
        "Inicio real": str(a.get("FechaInicioReal", "")) or "—",
        "Fin real": str(a.get("FechaFinReal", "")) or "—",
        "Nota": str(a.get("Nota", "")),
    } for a in acts])
    _ed = st.data_editor(
        _df, hide_index=True, use_container_width=True, num_rows="fixed",
        key=f"fldacts_{pid}",
        disabled=["N", "Actividad", "Inicio real", "Fin real"],
        column_config={
            "Avance %": st.column_config.NumberColumn(min_value=0, max_value=100, step=5,
                                                      help="Tu avance en esta actividad"),
            "Nota": st.column_config.TextColumn(help="Opcional"),
        })
    st.caption("Las fechas se registran solas: **inicio** al pasar de 0, **fin** al llegar a 100.")
    if st.button("💾 Guardar avances", key=f"fldsave_{pid}", use_container_width=True):
        cambios = []
        for i, a in enumerate(acts):
            r = _ed.iloc[i]
            nav, nnota = int(r["Avance %"]), str(r["Nota"])
            if nav != int(P._num(a.get("Avance"))) or nnota != str(a.get("Nota", "")):
                cambios.append({"orden": a.get("Orden"), "avance": nav, "nota": nnota})
        if not cambios:
            st.info("No cambiaste ningún avance.")
        else:
            ok, msg = P.save_field_progress(pid, cambios)
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()


def render_field_projects(usuario: str, grupo: str):
    st.markdown("### 📋 Mis proyectos")
    if not P.is_configured():
        st.warning("La gestión de proyectos necesita Google Sheets configurado.")
        return

    # ── Planificación de la semana (el campo ve toda la cuadrilla) ──
    try:
        from core import roster, roster_ui
        if roster.is_configured():
            _hoy = roster.asignacion_dia(grupo, usuario)
            if _hoy and _hoy.get("etiqueta"):
                _n = f" · {_hoy['nota']}" if str(_hoy.get("nota", "")).strip() else ""
                (st.info if _hoy.get("es_estado") else st.success)(
                    f"📅 **Hoy:** {_hoy['etiqueta']}{_n}")
            with st.expander("📅 Ver la planificación de la semana (toda la cuadrilla)"):
                roster_ui.render_board_readonly(grupo, resaltar_usuario=usuario)
    except Exception:
        pass

    proys = P.list_projects_for_field(usuario, grupo=grupo)
    if not proys:
        st.info("No tienes proyectos asignados todavía. El administrador te asigna a un proyecto.")
        return

    idmap = {f"{p.get('Nombre')} ({p.get('ID')}) — {p.get('Estado')}": p.get("ID")
             for p in proys}
    # Si el usuario tiene fichaje abierto, se abre ESE proyecto: es donde está
    # trabajando ahora (mismo criterio que usan las herramientas desde v137).
    _opts = [_VACIO] + list(idmap.keys())
    if "fieldproj_sel" not in st.session_state:
        _fich = ""
        try:
            _au = st.session_state.get("auth", {}) or {}
            _ses = timeclock.open_sessions(_au.get("nombre", ""), grupo, usuario)
            _fich = str((_ses.get(timeclock.TIPO_PROYECTO)
                         or _ses.get(timeclock.TIPO_GENERAL)
                         or {}).get("proyecto", "")).strip()
        except Exception:
            pass
        if _fich:
            _m = next((k for k in idmap if k.startswith(_fich + " (")), None)
            if _m:
                st.session_state["fieldproj_sel"] = _m
    sel = st.selectbox("Proyecto asignado", _opts, key="fieldproj_sel")
    if not sel or sel == _VACIO:
        st.caption("Elige el proyecto en el que estás trabajando. "
                   "Si fichas en ⏱ Fichaje, se abre solo.")
        return
    pid = idmap[sel]
    prj = P.get_project(pid)
    if not prj:
        st.error("Proyecto no encontrado.")
        return

    # ── Cabecera: tarjetas KPI (mismo lenguaje que el resto) ──
    avance = P._num(prj.get("Avance"))
    est    = str(prj.get("Estado", ""))
    _ub = str(prj.get("Ubicacion", "") or "")
    tarj = [_kpi_card("Estado", f"{_ESTADO_EMOJI.get(est, '')} {est}".strip()),
            _kpi_card("Avance del proyecto", f"{avance:.0f}%"),
            _kpi_card("Cliente", prj.get("Cliente") or "—")]
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px">'
                + "".join(tarj) + "</div>", unsafe_allow_html=True)
    st.progress(min(1.0, avance / 100.0))
    if _ub:
        st.caption("📍 " + maps.maps_link_md(_ub, _ub))

    # ── Sub-navegación (radio, NO st.tabs — regla v56; como el detalle del admin) ──
    _sec = st.radio("Sección", ["🏗 Avance", "🚨 Avisos", "💰 Recibos", "📎 Archivos"],
                    horizontal=True, key="fld_sec", label_visibility="collapsed")
    st.markdown("---")
    if _sec == "🏗 Avance":
        _induccion_section(pid, prj, grupo, allow_send=False)
        _field_activities(pid)
    elif _sec == "🚨 Avisos":
        _alerts_section(pid, grupo, prj.get("Nombre", ""), allow_report=True)
    elif _sec == "💰 Recibos":
        render_expenses(pid, grupo, can_delete=False, key_prefix="fld")
    else:   # 📎 Archivos
        _calculos_section(pid)
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
    sel = st.selectbox("Cargar recibo al proyecto", [_VACIO] + list(idmap.keys()),
                       key="cond_exp_sel")
    if sel and sel != _VACIO:
        render_expenses(idmap[sel], grupo, can_delete=False, key_prefix="cond")


# ── Gastos / compras por proyecto (admin, campo, conductor) ──
def _barras_html(pares, total, color="#2e6da4") -> str:
    """Barras horizontales ordenadas: etiqueta · barra · valor · %.

    Para desgloses cortos (categorias de gasto, personas). Un `st.bar_chart` aqui
    obliga a leer un eje para nada; la barra con su numero al lado se lee sola.
    """
    if not pares or total <= 0:
        return ""
    out = []
    for et, val in pares:
        pct = 100.0 * float(val) / total
        out.append(
            '<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">'
            f'<div style="width:118px;flex:none;font-size:12.5px;color:#374151;'
            f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{et}</div>'
            '<div style="flex:1;height:9px;background:#eef1f5;border-radius:20px;'
            'overflow:hidden;">'
            f'<div style="height:9px;width:{max(1.5, pct):.1f}%;background:{color};'
            f'border-radius:20px;"></div></div>'
            f'<div style="width:96px;flex:none;text-align:right;font-size:12.5px;'
            f'color:#1f2937;font-weight:600;">${float(val):,.0f}</div>'
            f'<div style="width:42px;flex:none;text-align:right;font-size:11.5px;'
            f'color:#9aa7b8;">{pct:.0f}%</div></div>')
    return "".join(out)


def render_expenses(pid, grupo, can_delete=False, key_prefix="ex"):
    """Costos del proyecto (v144).

    ⚠️ Antes respondia solo "cuanto llevas gastado". La pregunta accionable es
    **cuanto vas a gastar**: la barra de presupuesto se ponia roja al pasarse,
    o sea cuando ya no se puede hacer nada. Ahora la proyeccion al terminar va
    arriba del todo.
    """
    from core import expenses as E
    if not E.is_configured():
        return

    cp    = E.cost_projection(pid, grupo)      # incluye todo lo de project_cost
    lb    = E.labor_breakdown(pid, grupo)
    gastos = E.project_expenses(pid)
    pres  = cp["presupuesto"]
    proy  = cp["proyectado"]

    # ── Titular: una frase antes de cualquier numero ──
    if proy and pres > 0 and proy > pres * 1.02:
        _t = (f"A este ritmo el proyecto costara **${proy:,.0f}**, "
              f"**${proy - pres:,.0f} por encima** del presupuesto")
        _c, _fn = "#c0392b", st.error
    elif proy and pres > 0:
        _t = (f"A este ritmo el proyecto costara **${proy:,.0f}**, dentro "
              f"del presupuesto de ${pres:,.0f}")
        _c, _fn = "#1e8449", st.success
    elif cp["total"] > 0 and pres <= 0:
        _t = ("Este proyecto **no tiene presupuesto asignado**, así que no hay "
              "contra qué comparar el gasto. Se define en ✏️ Datos.")
        _c, _fn = "#6b7280", st.info
    else:
        _t, _c, _fn = ("Todavía no hay costos registrados en este proyecto.",
                       "#6b7280", st.info)

    # ── Tarjetas KPI ──
    tarj = [_kpi_card("Costo total", f"${cp['total']:,.0f}"),
            _kpi_card("Compras", f"${cp['compras']:,.0f}"),
            _kpi_card("Mano de obra", f"${cp['mano_obra']:,.0f}"),
            _kpi_card("Presupuesto", f"${pres:,.0f}" if pres > 0 else "—"),
            _kpi_card("Costará al terminar", f"${proy:,.0f}" if proy else "—", _c)]
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:10px">'
                + "".join(tarj) + "</div>", unsafe_allow_html=True)
    _fn(_t)

    if pres > 0:
        st.progress(min(1.0, (cp["pct"] or 0) / 100.0))
        _l = f"Llevas **${cp['total']:,.0f}** de ${pres:,.0f} · **{cp['pct']}% consumido**"
        if cp["avance"] > 0:
            _l += f" con **{cp['avance']:.0f}% de avance**"
            if cp["por_punto"]:
                _l += f" (${cp['por_punto']:,.0f} por punto)"
        st.caption(_l + ("  ⛔ SOBRE PRESUPUESTO" if cp["over"] else ""))

    # ── Reparto compras / mano de obra ──
    if cp["total"] > 0:
        st.markdown("**Reparto del costo**")
        st.markdown(_barras_html([("Mano de obra", cp["mano_obra"]),
                                  ("Compras", cp["compras"])], cp["total"]),
                    unsafe_allow_html=True)

    # ── Gasto por categoria: se calculaba desde v105 y la pestaña lo tiraba ──
    _cat = gastos.get("por_categoria") or {}
    if _cat:
        st.markdown("**Compras por categoría**")
        st.markdown(_barras_html(sorted(_cat.items(), key=lambda x: -x[1]),
                                 gastos["total"], "#BA7517"),
                    unsafe_allow_html=True)

    # ── Mano de obra por persona: labor_cost solo daba el total ──
    if lb["items"]:
        st.markdown("**Mano de obra por persona**")
        st.dataframe(pd.DataFrame([{
            "Usuario": x["usuario"], "Horas": x["horas"],
            "Tarifa/h": x["tarifa"], "Costo": x["costo"],
        } for x in lb["items"]]), hide_index=True, use_container_width=True)
        if lb["sin_tarifa"]:
            st.warning("⚠️ Sin tarifa/hora, así que sus horas suman **$0** al costo: **"
                       + ", ".join(lb["sin_tarifa"]) + "**. Se fija en 🔧 Usuarios.")

    # ── Curva de gasto acumulado ──
    _curva = E.spend_curve(pid, grupo)
    _svg   = E.spend_svg(_curva, proy, str(P.get_project(pid).get("Nombre", ""))) if _curva else ""
    if _svg:
        components.html(
            '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
            + _svg + '</body></html>', height=320, scrolling=False)
        st.caption("Coste acumulado día a día. La línea discontinua gris es el "
                   "presupuesto; la de color, dónde acabas al ritmo actual.")
    elif _curva:
        st.caption("Hace falta más de un movimiento para dibujar la curva de gasto.")

    # ── Cargar recibo ──
    with st.expander("➕ Cargar recibo"):
        with st.form(f"{key_prefix}_add_{pid}", clear_on_submit=True):
            c1, c2 = st.columns(2)
            cat = c1.selectbox("Categoría", E.CATEGORIAS, key=f"{key_prefix}_cat")
            val = c2.number_input("Valor total del recibo", min_value=0.0, step=1.0,
                                  key=f"{key_prefix}_val")
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
                        did = E.upload_receipt(pid, f.name, f.getvalue(),
                                               f.type or "application/octet-stream")
                    ok, msg = E.add(pid, grupo, val, cat, prov, desc, did, fn,
                                    st.session_state.get("auth", {}).get("usuario", ""))
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()

    items = gastos["items"]
    if items:
        with st.expander(f"🧾 Detalle de compras ({len(items)})"):
            st.dataframe(pd.DataFrame([{
                "Fecha": r.get("Fecha"), "Categoría": r.get("Categoria"),
                "Proveedor": r.get("Proveedor"), "Descripción": r.get("Descripcion"),
                "Valor": E._num(r.get("Valor")), "Por": r.get("CreadoPor"),
            } for r in items]), hide_index=True, use_container_width=True)
            for r in items:
                did = str(r.get("DriveID", "")).strip()
                cc = st.columns([5, 1])
                lbl = f"{r.get('Fecha')} · {r.get('Categoria')} · ${E._num(r.get('Valor')):,.0f}"
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

    tot     = sum(f["total"] for f in filas)
    tot_pres = sum(f["presupuesto"] for f in filas)
    tot_proj = sum((f["proyectado"] or f["total"]) for f in filas)
    con_pres = [f for f in filas if f["presupuesto"] > 0]
    sin_pres = [f for f in filas if f["presupuesto"] <= 0]
    n_over   = sum(1 for f in filas if f["over"])
    n_over_p = sum(1 for f in filas if f["over_proj"] and not f["over"])
    pct_grupo = round(100 * tot / tot_pres) if tot_pres > 0 else None

    # ── KPIs del grupo ──
    tarj = [_kpi_card("Costo actual", f"${tot:,.0f}"),
            _kpi_card("Presupuesto", f"${tot_pres:,.0f}" if tot_pres else "—"),
            _kpi_card("% consumido", f"{pct_grupo}%" if pct_grupo is not None else "—",
                      "#c0392b" if (pct_grupo or 0) > 100 else None),
            _kpi_card("Proyección al terminar", f"${tot_proj:,.0f}",
                      "#c0392b" if (tot_pres and tot_proj > tot_pres) else None),
            _kpi_card("Sobre presupuesto", n_over, "#c0392b" if n_over else None)]
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px">'
                + "".join(tarj) + "</div>", unsafe_allow_html=True)

    if n_over:
        st.error(f"⛔ **{n_over} proyecto(s) ya sobre presupuesto:** "
                 + ", ".join(f["nombre"] for f in filas if f["over"]))
    if n_over_p:
        st.warning(f"⚠️ **{n_over_p} más se saldrá(n) al ritmo actual** (aún dentro hoy): "
                   + ", ".join(f["nombre"] for f in filas if f["over_proj"] and not f["over"]))

    # ── Reparto compras vs mano de obra ──
    if tot > 0:
        st.markdown("**Reparto del costo del grupo**")
        st.markdown(_barras_html(
            [("Mano de obra", sum(f["mano_obra"] for f in filas)),
             ("Compras", sum(f["compras"] for f in filas))], tot),
            unsafe_allow_html=True)

    # ── Proyectos CON presupuesto: costo, proyección y % ──
    if con_pres:
        st.markdown("**Proyectos con presupuesto**")
        st.dataframe(pd.DataFrame([{
            "Proyecto": f["nombre"], "Costo": f["total"], "Presupuesto": f["presupuesto"],
            "% consumido": f["pct"], "Avance %": f["avance"],
            "Proyección": f["proyectado"] if f["proyectado"] is not None else "—",
            "": ("⛔" if f["over"] else ("⚠️" if f["over_proj"] else "✅")),
        } for f in con_pres]), hide_index=True, use_container_width=True)
        st.caption("**Proyección** = lo que costará al terminar al ritmo de gasto actual "
                   "(costo ÷ avance). ⛔ ya se pasó · ⚠️ se pasará al ritmo actual · ✅ dentro.")

    # ── Proyectos SIN presupuesto: solo costo, y aviso ──
    if sin_pres:
        st.markdown("**Proyectos sin presupuesto asignado**")
        st.dataframe(pd.DataFrame([{
            "Proyecto": f["nombre"], "Compras": f["compras"],
            "Mano de obra": f["mano_obra"], "Costo total": f["total"],
        } for f in sin_pres]), hide_index=True, use_container_width=True)
        st.caption(f"{len(sin_pres)} proyecto(s) sin presupuesto: no hay contra qué comparar "
                   "su gasto. Se define en el detalle del proyecto → ✏️ Datos.")

    # ── Compras por categoría ──
    if ge["por_categoria"]:
        st.markdown("**Compras por categoría**")
        _cat = sorted(ge["por_categoria"].items(), key=lambda x: -x[1])
        st.markdown(_barras_html(_cat, sum(v for _, v in _cat), "#BA7517"),
                    unsafe_allow_html=True)

    # ── Export para contabilidad ──
    _csv = pd.DataFrame([{
        "Proyecto": f["nombre"], "Compras": f["compras"], "Mano de obra": f["mano_obra"],
        "Costo total": f["total"], "Presupuesto": f["presupuesto"],
        "% consumido": f["pct"], "Avance %": f["avance"], "Proyeccion": f["proyectado"],
    } for f in filas])
    st.download_button("⬇️ Exportar CSV (contabilidad)",
                       data=_csv.to_csv(index=False).encode("utf-8"),
                       file_name=f"gastos_{grupo}.csv", mime="text/csv", key="ge_csv")


# ── Reporte del ADMIN: horas de TODOS los usuarios del grupo ──
def render_group_hours(grupo: str):
    from datetime import datetime
    from core import timeclock
    st.markdown("#### ⏱ Horas del grupo")
    if not timeclock.is_configured():
        st.warning("El fichaje necesita Google Sheets configurado.")
        return

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

    # ── Totales del grupo (KPIs) ──
    tot_jorn = sum(d["general"] for d in data)
    tot_proy = sum(d["proyecto"] for d in data)
    tot_sina = sum(d["sin_asignar"] for d in data)
    tot_cost = sum(d["costo"] for d in data)
    activos  = sum(1 for d in data if d["general"] or d["proyecto"])
    pct_sina = (100 * tot_sina / tot_jorn) if tot_jorn > 0 else 0
    _dudoso  = [d for d in data if d["sin_asignar_indet"]]

    tarj = [_kpi_card("Personas", activos),
            _kpi_card("Jornada", f"{tot_jorn:.1f} h"),
            _kpi_card("En proyectos", f"{tot_proy:.1f} h"),
            _kpi_card("Sin asignar", f"{tot_sina:.1f} h",
                      "#c0392b" if pct_sina > 25 else None),
            _kpi_card("Costo M.O.", f"${tot_cost:,.0f}")]
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:6px">'
                + "".join(tarj) + "</div>", unsafe_allow_html=True)
    if tot_jorn > 0:
        st.caption(f"**{pct_sina:.0f}%** de la jornada del grupo fue traslados y espera "
                   "(sin asignar). El costo de M.O. = horas imputadas × tarifa de cada persona.")

    # ── Tabla por persona (con costo; sin el Login técnico) ──
    # ⚠️ Dos logins pueden compartir Nombre (en los datos reales, `conductor` y
    # `fijiofgjei` se llaman igual): sin el Login se volverian indistinguibles.
    # Se añade el login SOLO a los que colisionan, no a todos.
    from collections import Counter as _Counter
    _nombres = _Counter((d.get("nombre") or d["usuario"]) for d in data)

    def _etiqueta(d):
        nom = d.get("nombre") or d["usuario"]
        return f"{nom} ({d['usuario']})" if _nombres[nom] > 1 else nom

    filas = []
    for d in data:
        _sa = ("—" if d["sin_asignar_indet"] else f"{d['sin_asignar']:.2f}")
        filas.append({
            "Usuario": _etiqueta(d),
            "Jornada (h)": d["general"],
            "En proyectos (h)": d["proyecto"],
            "Sin asignar (h)": _sa,
            "Tarifa/h": d["tarifa"] or "—",
            "Costo M.O.": d["costo"] or 0,
        })
    st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

    if _dudoso:
        st.caption("«—» en *sin asignar*: esa persona imputó a proyectos más horas que las "
                   "de su jornada, así que el dato no es fiable (fichó al proyecto sin abrir "
                   "jornada). Se corrige a partir de v150; el histórico anterior queda así.")
    _sin_tar = [_etiqueta(d) for d in data
                if d["proyecto"] > 0 and not d["tarifa"]]
    if _sin_tar:
        st.warning("⚠️ Sin **tarifa/hora**, así que su costo sale $0: **"
                   + ", ".join(_sin_tar) + "**. Se fija en 🔧 Usuarios.")

    # ── Reparto por proyecto (a qué elevador va el tiempo del grupo) ──
    por_proy = {}
    for d in data:
        for nom, h in d["por_proyecto"].items():
            por_proy[nom] = por_proy.get(nom, 0.0) + h
    if por_proy:
        st.markdown("**Horas del grupo por proyecto**")
        _tot = sum(por_proy.values()) or 1
        for nom, h in sorted(por_proy.items(), key=lambda x: -x[1]):
            st.markdown(
                '<div style="display:flex;align-items:center;gap:10px;margin-bottom:5px;">'
                f'<div style="width:190px;flex:none;font-size:13px;color:#374151;'
                f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{nom}</div>'
                '<div style="flex:1;height:9px;background:#eef1f5;border-radius:20px;">'
                f'<div style="height:9px;width:{100*h/_tot:.0f}%;background:#2e6da4;'
                'border-radius:20px;"></div></div>'
                f'<div style="width:64px;flex:none;text-align:right;font-size:13px;'
                f'font-weight:600;color:#1f2937;">{h:.1f} h</div></div>',
                unsafe_allow_html=True)
