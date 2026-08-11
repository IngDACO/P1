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
from core import clock


def _alerts_section(pid, grupo, project_name="", allow_report=False):
    """Alarmas abiertas del proyecto + resolver; si allow_report, el campo puede reportar."""
    if not alerts.is_configured():
        return
    usuario = st.session_state.get("auth", {}).get("usuario", "")
    abiertas = alerts.list_alerts(pid, "abierta")
    st.markdown(f"**{':red[:material/notifications:] ' + str(len(abiertas)) if abiertas else ':material/notifications:'} Alarmas / avisos**")
    if abiertas:
        for al in abiertas:
            emo = ":red[:material/error:]" if str(al.get("Tipo")) == "problema" else ":blue[:material/info:]"
            c = st.columns([6, 1])
            c[0].write(f"{emo} _{al.get('Fecha')}_ · **{al.get('CreadoPor')}**: {al.get('Mensaje')}")
            if c[1].button(":material/check_circle:", key=f"resolv_{al.get('ID')}", help="Marcar resuelta"):
                ok, msg = alerts.resolve_alert(al.get("ID"), usuario)
                if ok:
                    st.rerun()
                else:
                    st.error(msg)
    else:
        st.caption("Sin alarmas abiertas.")
    if allow_report:
        with st.expander(":material/report: Reportar un problema al administrador"):
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
    """Tarjeta KPI — delega en el SISTEMA DE DISEÑO (`core/theme.py`, v283) para que
    las ~20 tarjetas repartidas por la app hablen el mismo idioma visual. Firma
    intacta: `color` sigue tiñendo el valor y ahora también el borde de acento."""
    from core import theme
    _acc = color or theme.AZUL
    _val = f"color:{color};" if color else ""
    return (
        f'<div class="cpx-kpi" style="--cpx-accent:{_acc};min-width:104px;">'
        f'<div class="lbl">{theme._esc(label)}</div>'
        f'<div class="val" style="{_val}">{theme._esc(value)}</div>'
        '</div>'
    )


def _MI(name, color="", size="1.05em"):
    """Icono Material DENTRO de HTML (st.markdown unsafe_allow_html / tarjetas).
    El directivo `:material/x:` NO renderiza dentro de un <div>, pero la fuente que
    Streamlit ya carga sí, vía font-family inline. color='' → hereda del contenedor."""
    _c = f"color:{color};" if color else ""
    return (f"<span style=\"font-family:'Material Symbols Rounded';font-size:{size};"
            f"vertical-align:-2px;{_c}\">{name}</span>")


def render_group_header(grupo: str):
    """Banda de marca del grupo + fila de KPIs (centro de control del admin)."""
    st.markdown(
        '<div style="background:linear-gradient(135deg,#1a3a5c 0%,#2e6da4 100%);'
        'padding:14px 18px;border-radius:12px;display:flex;align-items:center;gap:12px;'
        'margin-bottom:14px;">'
        f'<span style="line-height:1;">{_MI("business", "#fff", "26px")}</span>'
        '<div style="min-width:0;">'
        f'<div style="color:#fff;font-size:1.25rem;font-weight:800;line-height:1.1;">{grupo}</div>'
        '<div style="color:#b0c8e8;font-size:0.8rem;margin-top:2px;">Centro de control del grupo</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )
    if not P.is_configured():
        return
    k = _kpis(grupo)
    # v199: métricas ACTIVAS (clic → sección) en vez de tarjetas pasivas. "En riesgo"
    # y "Alarmas" salieron de aquí (v197): viven en los indicadores del resumen.
    # v283: se ven como TARJETA KPI (clase `cpxkpi_` del sistema de diseño) sin dejar
    # de ser botones — la métrica sigue llevando a su sección.
    m1, m2, m3 = st.columns(3)
    if m1.button(f":material/folder: {k['activos']} proyectos activos",
                 key="cpxkpi_activos", use_container_width=True):
        _ir_a("proyectos", "📊 Proyectos")
    if m2.button(f":material/trending_up: {k['avg']}% de avance promedio",
                 key="cpxkpi_avance", use_container_width=True):
        _ir_a("proyectos", "📊 Proyectos")
    if m3.button(f":material/schedule: {k['horas']} h registradas",
                 key="cpxkpi_horas", use_container_width=True):
        _ir_a("finanzas", "⏱ Horas")
    _resumen_del_dia(grupo)


def _ir_a(seccion, sub_label=None):
    """Salta a una sección (y sub-pestaña) del admin. Lo lee home_ui._aplicar_nav_pending
    en el siguiente run (antes de instanciar los radios). Usado por los elementos ACTIVOS."""
    st.session_state["_admin_nav_pending"] = (seccion, sub_label)
    st.rerun()


def _resumen_del_dia(grupo: str):
    """Resumen del día — estructura fija + elementos ACTIVOS (v199): cada indicador es
    un botón; al clickearlo muestra sus 'cuáles' + un botón para ir a la sección a actuar.
    La lectura de IA va en su propio desplegable, bajo demanda."""
    from core import admin_digest
    try:
        d = admin_digest.group_digest(grupo)
    except Exception:
        return

    _al_n = sum(a["n"] for a in d["alarmas"])
    # slug, icono, etiqueta, urgente, count, sección, sub_pestaña, nombre_sección, detalle()
    inds = [
        ("retrasos", ":material/error:", "En retraso", True, len(d["retrasos"]),
         "proyectos", ":material/bar_chart: Proyectos", "Proyectos",
         lambda: ", ".join(f"{r['nombre']} ({r['dias']}d)" for r in d["retrasos"][:15])),
        ("vencidos", ":material/block:", "Vencidos", True, len(d["vencidos"]),
         "proyectos", ":material/bar_chart: Proyectos", "Proyectos",
         lambda: ", ".join(f"{v['nombre']} ({v['fin']})" for v in d["vencidos"][:15])),
        ("porvencer", ":material/event:", "Por vencer", False, len(d["por_vencer"]),
         "proyectos", ":material/bar_chart: Proyectos", "Proyectos",
         lambda: ", ".join(f"{v['nombre']} ({v['dias']}d)" for v in d["por_vencer"][:15])),
        ("sinasig", ":material/engineering:", "Sin asignar", False, len(d["sin_asignar"]),
         "proyectos", ":material/bar_chart: Proyectos", "Proyectos",
         lambda: ", ".join(s["nombre"] for s in d["sin_asignar"][:15])),
        ("sincont", ":material/contact_page:", "Sin contacto", False, len(d["campo_sin_contacto"]),
         "planificacion", ":material/engineering: Usuarios", "Usuarios",
         lambda: ", ".join(d["campo_sin_contacto"][:15])),
        ("cred", ":material/badge:", "Credenciales", False, len(d.get("cred_venc", [])),
         "planificacion", ":material/engineering: Usuarios", "Usuarios",
         lambda: ", ".join(f"{c['tipo']}·{c['usuario']} ({c['dias']}d)"
                           for c in d.get("cred_venc", [])[:15])),
        ("alarmas", ":material/notifications:", "Alarmas", True, _al_n,
         "proyectos", ":material/bar_chart: Proyectos", "Proyectos",
         lambda: ", ".join(f"{a['nombre']} ({a['n']})" for a in d["alarmas"][:15])),
        ("near", ":material/health_and_safety:", "Near miss", False, len(d["near_miss"]),
         "proyectos", ":material/bar_chart: Proyectos", "Proyectos",
         lambda: ", ".join(f"{n['proyecto']} ({n['fecha']})" for n in d["near_miss"][:15])),
        ("sobrep", ":material/payments:", "Sobre presup.", False, len(d.get("sobre_presupuesto", [])),
         "finanzas", ":material/payments: Gastos", "Gastos",
         lambda: f"{len(d.get('sobre_presupuesto', []))} proyecto(s) sobre presupuesto"),
    ]
    _urg = sum(c for (_s, _i, _l, u, c, *_r) in inds if u)
    _tot = sum(c for (_s, _i, _l, _u, c, *_r) in inds)

    with st.expander(":material/notifications: Resumen del día", expanded=True):
        if _tot == 0:
            st.markdown(f"<span style='color:#1e8449;font-weight:600;'>{_MI('check_circle')} Todo en orden.</span>",
                        unsafe_allow_html=True)
        elif _urg:
            st.markdown(f"<span style='color:#c0392b;font-weight:600;'>{_MI('error')} {_urg} urgente(s)</span>"
                        f" · {_tot} pendiente(s)", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color:#c77700;font-weight:600;'>{_MI('schedule')} {_tot} pendiente(s)</span>",
                        unsafe_allow_html=True)

        # colorear cada botón-indicador por severidad (clase st-key-<key>, v169)
        _css = ["<style>"]
        for _slug, _i, _l, _urgb, _cnt, *_r in inds:
            _bg, _fg = (("#fdecec", "#c0392b") if _urgb else ("#fff4e0", "#c77700")) \
                       if _cnt else ("#f4f6f9", "#9aa7b8")
            _css.append(f".st-key-resind_{_slug} button{{background:{_bg}!important;"
                        f"color:{_fg}!important;border-color:{_bg}!important;}}")
        _css.append("</style>")
        st.markdown("".join(_css), unsafe_allow_html=True)

        st.caption("Toca un indicador para ver el detalle e ir a resolverlo.")
        for _i0 in range(0, len(inds), 3):          # 3 filas de 3 (nombres visibles)
            for _col, (slug, icon, lbl, _urgb, cnt, _sec, _sub, _secn, _fn) in \
                    zip(st.columns(3), inds[_i0:_i0 + 3]):
                if _col.button(f"{icon} {lbl} · {cnt}", key=f"resind_{slug}",
                               use_container_width=True):
                    _cur = st.session_state.get("_res_sel")
                    st.session_state["_res_sel"] = None if _cur == slug else slug
                    st.rerun()

        sel = st.session_state.get("_res_sel")
        it = next((x for x in inds if x[0] == sel), None) if sel else None
        if it:
            slug, icon, lbl, _urgb, cnt, sec, sub, secn, fn = it
            st.markdown(f"**{icon} {lbl} — {cnt}**")
            if cnt:
                st.caption(fn())
                if st.button(f"→ Ir a {secn}", key=f"go_{slug}", type="primary"):
                    _ir_a(sec, sub)
            else:
                st.caption("Sin pendientes aquí. :green[:material/check_circle:]")

        # 4) lectura del asistente (IA) — su propio desplegable, bajo demanda
        with st.expander(":material/forum: Lectura del asistente (IA)"):
            key = f"_brief_{grupo}"
            if key in st.session_state:
                st.markdown(st.session_state[key])
                b1, b2 = st.columns(2)
                if b1.button(":material/refresh: Actualizar", key=f"brief_ref_{grupo}"):
                    st.session_state.pop(key, None)
                    st.rerun()
                if b2.button(":material/send: Enviármelo", key=f"brief_send_{grupo}"):
                    from core import notify
                    _u = st.session_state.get("auth", {}).get("usuario", "")
                    _txt = st.session_state.get(key, "")
                    try:
                        rr = notify.notify_user(_u, f"🔔 Resumen del día — {grupo}",
                                                [l for l in str(_txt).split("\n") if l.strip()])
                        if rr.get("email") or rr.get("telegram"):
                            st.success(":material/send: Resumen enviado.")
                        else:
                            st.warning("No tienes email/Telegram configurado en tu usuario.")
                    except Exception as e:
                        st.error(f"No se pudo enviar: {e}")
            else:
                st.caption("El asistente redacta el estado del grupo en pocas frases, "
                           "con una recomendación.")
                if st.button("✨ Generar lectura", key=f"brief_gen_{grupo}"):
                    with st.spinner("Preparando…"):
                        from core import chat_agent
                        st.session_state[key] = chat_agent.admin_briefing(grupo)
                    st.rerun()


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
# Etiquetas legibles para el filtro de tipo del buscador (v165).
_TIPO_LABEL = {"plano": "Plano", "informe_cliente": "Informe cliente",
               "informe_admin": "Informe admin", "matriz_survey": "Matriz survey",
               "foto": "Fotos", "certificado": "Certificados",
               "prestart": "Pre-Start", "calculo": "Cálculos", "otro": "Otros"}
_TIPO_ORDER = ["plano", "informe_cliente", "informe_admin", "matriz_survey",
               "calculo", "prestart", "foto", "certificado", "otro"]
# Reabrir un cálculo en su herramienta (v148): solo estas 4 guardan entradas.
_CALC_NAV   = {"plomada": "🔩 Líneas de plomada", "rieles": "✂️ Corte de rieles",
               "buffers": "🛡 Corte de buffers", "belting": "🎗 Belting"}


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
    with st.expander(":material/upload: Cargar / actualizar el plano del proyecto"):
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
                st.success(":material/check_circle: Plano cargado — alimenta tus 5 herramientas técnicas.")
                st.rerun()
            except Exception as e:
                _barra.empty()
                st.error(f"No se pudo leer el plano: {e}")


def _plano_herramientas_html(datos) -> str:
    """Tabla: qué le da el plano a CADA una de las 5 herramientas técnicas (v175).

    El plano alimenta las cinco por igual; se muestran juntas para que no parezca
    que solo cuentan los 17 parámetros del survey.
    """
    filas = []
    for h in plan_data.por_herramienta(datos):
        chips = []
        for label, val in h["items"]:
            if val not in (None, ""):
                chips.append(
                    '<span style="display:inline-block;background:#e8f5e9;color:#1b5e20;'
                    'border-radius:6px;padding:2px 8px;margin:2px 3px;font-size:12px;">'
                    f'{label}: <b>{val}</b></span>')
            else:
                chips.append(
                    '<span style="display:inline-block;background:#fdecea;color:#b71c1c;'
                    'border-radius:6px;padding:2px 8px;margin:2px 3px;font-size:12px;">'
                    f'{label}: {_MI('warning','#e0a021')} falta</span>')
        filas.append(
            '<tr><td style="padding:6px 10px;white-space:nowrap;font-weight:600;'
            'vertical-align:top;border-bottom:1px solid #eef1f5;">'
            f'{h["tool"]}</td><td style="padding:5px 6px;border-bottom:1px solid #eef1f5;">'
            f'{"".join(chips)}</td></tr>')
    return ('<table style="border-collapse:collapse;width:100%;margin:4px 0 8px;">'
            + "".join(filas) + "</table>")


def _plano_section(pid: str, prj: dict):
    """Qué se leyó del plano de este proyecto (columna PlanoJSON, v137) + cargarlo.

    ⚠️ El dato existía desde v137 y solo se poblaba **al crear el proyecto**. Un
    proyecto creado sin plano no tenía forma de recibirlo (subirlo en Documentos
    NO extraía), así que las herramientas no lo veían nunca. Ahora se carga aquí.
    """
    datos = plan_data.del_proyecto(pid)
    st.markdown("**:material/description: Datos del plano**")
    if not datos:
        st.caption("Este proyecto no tiene datos de plano guardados, así que las "
                   "herramientas le pedirán el PDF a quien las use. Cárgalo aquí "
                   "una vez y dejarán de pedirlo.")
        _cargar_plano(pid)
        return

    st.caption("Un solo plano alimenta **tus 5 herramientas técnicas** — todas por igual:")
    st.markdown(_plano_herramientas_html(datos), unsafe_allow_html=True)
    if not (datos.get("faltan") or []):
        st.caption(":material/check_circle: El plano dio todo lo que las herramientas necesitan.")

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
    seccion (ver `_archivos_section`).
    """
    kver = f"_fotos_n_{pid}"
    n_ver = int(st.session_state.get(kver, por_pagina))
    st.markdown(f"**:material/photo_camera: Fotos de obra** — {len(fotos)}")
    visibles = fotos[:n_ver]
    for fila in range(0, len(visibles), 3):
        cols = st.columns(3)
        for c, d in zip(cols, visibles[fila:fila + 3]):
            did = str(d.get("DriveID", ""))
            with c:
                _b = None
                try:
                    _b = drive_store.download(did)     # cacheado 5 min
                    st.image(_b, use_container_width=True)
                except Exception:
                    st.caption(":material/broken_image: no disponible")
                pie = str(d.get("Nombre", ""))
                st.caption(f"{pie[:26]}\n\n{_fecha_corta(d.get('Fecha'))}"
                           + (f" · {d.get('SubidoPor')}" if d.get("SubidoPor") else ""))
                # Reutiliza los bytes ya bajados para la miniatura: descarga directa
                # de la foto sin una segunda llamada a Drive.
                if _b is not None:
                    st.download_button(":material/download:", data=_b, file_name=pie or f"{did}.jpg",
                                       key=f"fdl_{pid}_{did}", use_container_width=True)
    if len(fotos) > n_ver:
        if st.button(f"Ver {min(por_pagina, len(fotos) - n_ver)} más "
                     f"({len(fotos) - n_ver} restantes)", key=f"masfotos_{pid}"):
            st.session_state[kver] = n_ver + por_pagina
            st.rerun()


def _archivos_section(pid: str):
    """:material/attach_file: Archivos: UNA lista buscable de todo lo del proyecto (v165).

    Antes eran DOS sub-secciones (Documentos y Cálculos) con tres selectores
    distintos y listas planas: con muchos archivos, encontrar uno era el problema.
    Ahora hay una sola lista con búsqueda por nombre, filtro por tipo (con
    contadores) y orden, que reduce a la vez la tabla, la galería y el descargador.

    `list_documents` ya es la UNIÓN de todo (informes, matriz, fotos, pre-starts y
    los PDF de cálculos, que `toolruns.registrar` archiva como documento tipo
    "calculo" con el MISMO DriveID que su fila). Se casa cada cálculo con su
    toolrun por DriveID para ofrecer «reabrir en la herramienta» sin duplicarlo.
    """
    from collections import Counter
    st.markdown("**:material/folder: Archivos**")
    if not drive_store.is_configured():
        st.caption(":material/lock: Almacenamiento en Drive no configurado (faltan los secrets `[gdrive]`).")
        return
    a = st.session_state.get("auth", {})
    rol, usuario = a.get("rol", ""), a.get("usuario", "")
    es_campo     = rol == "campo"
    # Admin/propietario: ver_tipos = None -> SIN filtro (un tipo nuevo generado por
    # la app no vuelve a desaparecer de la vista, v134). El campo ve lo suyo.
    ver_tipos    = _CAMPO_VER if es_campo else None
    sube_tipos   = _CAMPO_SUBE if es_campo else _DOC_SUBIR
    puede_borrar = rol in ("administrador", "propietario")

    # ── Unir documentos + cálculos reabribles sin PDF (casados por DriveID) ──
    docs = [d for d in P.list_documents(pid)
            if ver_tipos is None or str(d.get("Tipo", "")) in ver_tipos]
    runs = toolruns.list_for(pid) if toolruns.is_configured() else []
    runs_by_drive = {str(r.get("DriveID", "")).strip(): r
                     for r in runs if str(r.get("DriveID", "")).strip()}
    entries, casados = [], set()
    for d in docs:
        tipo = str(d.get("Tipo", ""))
        did  = str(d.get("DriveID", "")).strip()
        run  = runs_by_drive.get(did) if tipo == "calculo" else None
        if run:
            casados.add(did)
        entries.append({
            "tipo": tipo, "label": _TIPO_LABEL.get(tipo, tipo or "otro"),
            "nombre": str(d.get("Nombre", "")), "fecha": str(d.get("Fecha", "")),
            "por": str(d.get("SubidoPor", "")), "did": did,
            "resumen": str(run.get("Resumen", "")) if run else "",
            "doc": d, "run": run})
    # Cálculos con entradas guardadas pero SIN PDF archivado (Drive estaba caído):
    # no son un "archivo" descargable, pero sí se pueden reabrir. No se pierden.
    if ver_tipos is None or "calculo" in ver_tipos:
        for r in runs:
            did = str(r.get("DriveID", "")).strip()
            if did and did in casados:
                continue
            if not toolruns.entradas_de(r):
                continue
            h = str(r.get("Herramienta", ""))
            entries.append({
                "tipo": "calculo", "label": _TIPO_LABEL["calculo"],
                "nombre": (f"{toolruns.HERRAMIENTAS.get(h, '')} "
                           f"{str(r.get('Resumen', ''))[:40]}").strip(),
                "fecha": str(r.get("Fecha", "")), "por": str(r.get("Usuario", "")),
                "did": did, "resumen": str(r.get("Resumen", "")),
                "doc": None, "run": r})

    if not entries:
        st.caption("Sin archivos todavía.")
        _subir_documento(pid, es_campo, sube_tipos, usuario)
        return

    # ── Barra para acotar: buscar + tipo (con contadores) + orden ──
    cuenta = Counter(e["tipo"] for e in entries)
    tipos = ["Todos"] + [t for t in _TIPO_ORDER if t in cuenta] \
            + [t for t in cuenta if t not in _TIPO_ORDER]

    def _tlabel(t):
        return (f"Todos ({len(entries)})" if t == "Todos"
                else f"{_TIPO_LABEL.get(t, t)} ({cuenta[t]})")

    c1, c2, c3 = st.columns([2, 1.5, 1.5])
    q = c1.text_input(":material/search: Buscar", key=f"arch_q_{pid}",
                      placeholder="nombre, tipo…").strip().lower()
    tsel = c2.selectbox("Tipo", tipos, format_func=_tlabel, key=f"arch_t_{pid}")
    orden = c3.selectbox("Orden", ["Más reciente", "Más antiguo", "Nombre A–Z", "Tipo"],
                         key=f"arch_o_{pid}")

    vis = entries
    if tsel != "Todos":
        vis = [e for e in vis if e["tipo"] == tsel]
    if q:
        vis = [e for e in vis
               if q in f"{e['nombre']} {e['label']} {e['resumen']} {e['por']}".lower()]
    if orden == "Más reciente":
        vis = sorted(vis, key=lambda e: e["fecha"], reverse=True)
    elif orden == "Más antiguo":
        vis = sorted(vis, key=lambda e: e["fecha"])
    elif orden == "Nombre A–Z":
        vis = sorted(vis, key=lambda e: e["nombre"].lower())
    else:
        vis = sorted(vis, key=lambda e: (e["label"], e["fecha"]))

    if len(vis) != len(entries):
        st.caption(f"Mostrando **{len(vis)}** de {len(entries)} archivos.")

    # ── Galería de fotos (solo las que pasan el filtro; sigue siendo lazy) ──
    fotos = [e["doc"] for e in vis if e["tipo"] == "foto"]
    if fotos:
        _galeria_fotos(fotos, pid)
        st.markdown("")

    # ── Tabla del resto: CLICABLE — tocar una fila muestra su descarga ──
    # La descarga sigue siendo lazy: `st.download_button(data=…)` evalúa `data` al
    # renderizar, así que un botón por fila bajaría TODO Drive en cada pasada (el
    # problema de v147). Con selección de fila, solo se descarga la elegida.
    resto = [e for e in vis if e["tipo"] != "foto"]
    if resto:
        _ev = st.dataframe(pd.DataFrame([{
            "Archivo": e["nombre"], "Tipo": e["label"],
            "Subido por": e["por"], "Fecha": _fecha_corta(e["fecha"]),
        } for e in resto]), hide_index=True, use_container_width=True,
            on_select="rerun", selection_mode="single-row", key=f"arch_tbl_{pid}")
        st.caption(":material/touch_app: Toca una fila para descargar o reabrir ese archivo.")
        try:
            _rows = list(_ev.selection.rows)
        except Exception:
            _rows = []
        # Clamp: si cambiaste el filtro con una fila elegida, el índice podría
        # apuntar fuera de la lista actual — no abrir un archivo equivocado.
        if _rows and _rows[0] < len(resto):
            _acciones_archivo(pid, resto[_rows[0]], puede_borrar)

    if not vis:
        st.info("Ningún archivo coincide con el filtro.")

    _subir_documento(pid, es_campo, sube_tipos, usuario)


def _acciones_archivo(pid, e, puede_borrar):
    """Descargar / reabrir / borrar el archivo elegido. Solo aquí se descarga."""
    did = e["did"]
    run = e.get("run")
    h = str((run or {}).get("Herramienta", ""))
    reabrible = bool(run) and h in _CALC_NAV and bool(toolruns.entradas_de(run))
    es_doc = e.get("doc") is not None

    if did:
        try:
            st.download_button(":material/download: Descargar " + (e["nombre"] or "archivo"),
                               data=drive_store.download(did),
                               file_name=e["nombre"] or f"{did}.pdf",
                               key=f"arch_dl_{pid}_{did}", use_container_width=True)
        except Exception as ex:
            st.error(f"No se pudo descargar: {ex}")
    if reabrible:
        if st.button(":material/replay: Reabrir en la herramienta", key=f"arch_reab_{pid}",
                     use_container_width=True):
            if tool_save_ui.pedir_reapertura(run, h, _CALC_NAV[h]):
                st.rerun()
            else:
                st.warning("Este cálculo no guardó sus entradas (es anterior a v148).")
    if puede_borrar and es_doc:
        if st.button(":material/delete: Borrar", key=f"arch_del_{pid}_{did or e['nombre']}",
                     use_container_width=True):
            if did:
                drive_store.delete(did)
            P.delete_document_record(pid, did)
            st.rerun()
    if not did and not reabrible:
        st.caption("Este cálculo no tiene PDF archivado ni entradas para reabrir.")


def _subir_documento(pid, es_campo, sube_tipos, usuario):
    """Subir un documento (el campo solo puede subir fotos)."""
    with st.expander("Subir documento", icon=":material/upload_file:"):
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
                except Exception as ex:
                    st.error(f"No se pudo subir: {ex}")


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

    with st.expander("Nuevo proyecto", icon=":material/add_circle:"):
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
        st.markdown("**:material/description: Plano del elevador** — opcional, pero recomendado")
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
            # v272: prellenar NS desde el plano AQUÍ (session_state), no con `value=` en el
            # form. El widget NS ya se instanció antes de subir el plano y Streamlit ignora
            # `value=` si la key ya existe → el prellenado no tomaba (NS se quedaba en 2).
            _pl = st.session_state.get(_kd) or {}
            try:
                st.session_state[f"np_ns_{key}"] = max(2, min(50, int(float(_pl.get("ns") or 2))))
            except Exception:
                pass
            _mdl = str(_pl.get("modelo") or "").strip()   # v273: PRODUCT LINE del plano
            if _mdl:
                st.session_state[f"np_mod_{key}"] = _mdl
            # Guarda de identidad: sin esto se reextraería en CADA rerun (v112)
            st.session_state[f"{_kd}_id"] = f"{_pdf.name}:{_pdf.size}"
            _barra.empty()
            st.rerun()

        _plano = st.session_state.get(_kd)
        if _plano:
            st.success(":material/check_circle: Plano leído — alimenta tus **5 herramientas técnicas**:")
            st.markdown(_plano_herramientas_html(_plano), unsafe_allow_html=True)

        asg = st.multiselect(":material/engineering: Usuarios de campo asignados", campos,
                             key=f"np_asg_{key}")
        _certs = st.multiselect(":material/badge: Certificados que exige el proyecto", credentials.CATALOGO,
                                key=f"np_certs_{key}",
                                help="Al asignar personal se avisa y marca a quien no los cumpla.")
        if asg:
            _avisar_asignados(asg, grupo, certs_req=_certs)

        # ── Ubicación en el mapa (fuera del form: el mapa necesita reruns) — v194 ──
        # v210: inline (sin expander propio) — este bloque ya vive dentro del expander
        # "➕ Nuevo proyecto", y Streamlit no permite expanders anidados.
        from core import location_ui
        st.markdown("**:material/map: Ubicación en el mapa** — opcional, fija el pin del proyecto")
        _nplat, _nplng = location_ui.location_picker(f"nploc_{key}")

        # ── Cliente: elegir uno existente o escribir uno nuevo (fuera del form) ──
        from core import clientes as _C
        _cli_fichas = _C.list_clientes(grupo)
        _cli_names = [str(c.get("Nombre", "")) for c in _cli_fichas]
        _CLI_OTRO = "➕ Otro (escribir uno nuevo)"
        _cli_sel = st.selectbox(":material/contacts: Cliente",
                                ["— sin cliente —"] + _cli_names + [_CLI_OTRO],
                                key=f"np_clisel_{key}",
                                help="Elige un cliente de Contactos o escribe uno nuevo.")
        _cli_new = ""
        if _cli_sel == _CLI_OTRO:
            _cli_new = st.text_input("Nombre del nuevo cliente", key=f"np_clinew_{key}")

        # NS lo controla session_state (prellenado del plano arriba); la Ubicación se toma de
        # la dirección que buscaste en el mapa → ya no se pide dos veces (v272).
        st.session_state.setdefault(f"np_ns_{key}", 2)
        _ubi_auto = (st.session_state.get(f"nploc_{key}_addr")
                     or st.session_state.get(f"nploc_{key}_q") or "").strip()
        if _ubi_auto:
            st.caption(f":material/place: Ubicación que se guardará: **{_ubi_auto}**")

        with st.form(f"np_form_{key}"):
            nom = st.text_input("Nombre del proyecto *", key=f"np_nom_{key}")
            c1, c2 = st.columns(2)
            ing = c1.text_input("Ingeniero responsable", key=f"np_ing_{key}")
            ns = c2.number_input("Número de paradas (NS) *", min_value=2, max_value=50,
                                 step=1, key=f"np_ns_{key}",
                                 help=("Leído del plano." if (_plano or {}).get("ns")
                                       else "Define la duración de las actividades."))
            f_ini = c1.date_input("Fecha de inicio", value=clock.today(),
                                  key=f"np_ini_{key}")
            # La fecha de FIN no se teclea: sale del NS + las actividades estándar de
            # instalación (`build_schedule`), cuyas duraciones escalan con el NS. Preview:
            try:
                _sch_prev = build_schedule(int(ns), f_ini, {})
                c1.caption(":material/event_available: Fin estimado: "
                           f"**{_sch_prev['fecha_fin'].strftime('%d/%m/%Y')}** "
                           f"({_sch_prev['total_dias']} días) — del NS y las actividades estándar.")
            except Exception:
                pass
            pres = c2.number_input(":material/payments: Presupuesto (0 = sin presupuesto)", min_value=0.0,
                                   step=100.0, key=f"np_pres_{key}")
            mod = st.text_input("Modelo de elevador", key=f"np_mod_{key}",
                                placeholder="opcional",
                                help="Prellenado del plano (PRODUCT LINE), si se leyó. Editable.")
            instr = st.text_area(":material/push_pin: Instrucciones particulares", key=f"np_ins_{key}",
                                 placeholder="Indicaciones específicas para el equipo…")
            inds = st.text_area(":material/description: Inducciones (un link por línea)", key=f"np_ind_{key}",
                                placeholder="https://...",
                                help="Se envían por Telegram/email a los asignados.")
            enviar = st.form_submit_button(":material/add_circle: Crear proyecto",
                                           use_container_width=True)

        if enviar:
            if not nom.strip():
                st.error("El nombre del proyecto es obligatorio.")
                return
            # Ubicación = la dirección que se buscó en el mapa (ya no hay campo aparte).
            ubi = (st.session_state.get(f"nploc_{key}_addr")
                   or st.session_state.get(f"nploc_{key}_q") or "").strip()
            # Incluye archivados: crear un homonimo de uno archivado tambien confunde.
            dups = [f"{p.get('ID')} · {p.get('Nombre')}"
                    for p in P.list_projects(grupo, incluir_archivados=True)
                    if " ".join(str(p.get("Nombre") or "").lower().split())
                    == " ".join(nom.lower().split())]
            if dups and not st.session_state.get(f"np_dup_{key}"):
                st.warning(":material/warning: Ya existe un proyecto con ese nombre: "
                           + ", ".join(dups)
                           + ". Si es otro elevador, marca la casilla y crea de nuevo.")
                st.checkbox("Crear aunque el nombre se repita", key=f"np_dup_{key}")
                return

            # Cliente elegido/escrito → texto + ClienteID (v255)
            if _cli_sel in _cli_names:
                cli = _cli_sel
                _cli_id = next((str(c.get("ID", "")) for c in _cli_fichas
                                if str(c.get("Nombre", "")) == _cli_sel), "")
            elif _cli_sel == _CLI_OTRO:
                cli, _cli_id = _cli_new.strip(), ""
            else:
                cli, _cli_id = "", ""

            sched = build_schedule(int(ns), f_ini, {})
            ok, res = P.create_project(
                grupo=grupo, nombre=nom.strip(), cliente=cli, cliente_id=_cli_id, ubicacion=ubi,
                modelo=mod, ns=int(ns), ingeniero=ing, campo_asignados=asg,
                fecha_inicio=f_ini.strftime("%Y-%m-%d"),
                fecha_fin_est=(sched["fecha_fin"].strftime("%Y-%m-%d")
                               if sched.get("fecha_fin") else ""),
                activities=sched.get("activities", []),
                creado_por=st.session_state.get("auth", {}).get("usuario", ""),
                instrucciones=instr, induccion_links=inds, presupuesto=pres,
                lat=("" if _nplat is None else _nplat),
                lng=("" if _nplng is None else _nplng),
                certs_req=";".join(_certs))
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
                        st.caption(":material/attach_file: El plano no se pudo archivar en Drive.")
                for _k in (_kd, f"{_kd}_bytes", f"{_kd}_id"):
                    st.session_state.pop(_k, None)

            st.success(f":material/check_circle: Proyecto **{res}** creado con "
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
                # v219: auto-poblar el planificador con el proyecto entre sus fechas.
                _autoagenda(grupo, res, asg, [], f_ini,
                            sched.get("fecha_fin") if sched.get("fecha_fin") else None)


def _autoagenda(grupo, pid, nuevos, quitados, fecha_ini, fecha_fin):
    """Sincroniza el planificador con la asignación del proyecto (v219): pone a los
    NUEVOS asignados en el proyecto entre sus fechas (Lun–Vie, solo celdas vacías) y
    quita del planificador a los DESASIGNADOS. Best-effort; informa el resultado."""
    from core import roster as R
    msgs = []
    try:
        if nuevos and fecha_ini and fecha_fin:
            r = R.autopoblar_proyecto(grupo, pid, nuevos, fecha_ini, fecha_fin)
            if r["llenadas"]:
                _oc = (f" · {r['ocupadas']} día(s) ya ocupados se respetaron"
                       if r["ocupadas"] else "")
                msgs.append(f":material/calendar_month: Planificador: {r['llenadas']} día(s) asignados a "
                            f"{len(nuevos)} persona(s) en {r['semanas']} semana(s){_oc}.")
            elif r["ocupadas"]:
                msgs.append(":material/calendar_month: Planificador: los días del rango ya estaban ocupados; "
                            "no se pisó nada.")
        elif nuevos and not fecha_fin:
            msgs.append(":material/calendar_month: El proyecto no tiene **fecha de fin**, así que no se "
                        "auto-planificó. Ponla en :material/edit: Datos, o planifica a mano en "
                        ":material/calendar_month: Planificación.")
    except Exception:
        pass
    try:
        if quitados:
            n = R.limpiar_proyecto(grupo, pid, quitados)
            if n:
                msgs.append(f":material/cleaning_services: Planificador: se quitaron {n} día(s) de los desasignados.")
    except Exception:
        pass
    for m in msgs:
        st.caption(m)


def _avisar_asignados(usuarios, grupo=None, exclude_pid=None, certs_req=None):
    """Avisos ANTES de asignar (v219): contacto, credenciales, si YA está en otro
    proyecto (y hasta cuándo), y cumplimiento de los certificados que EXIGE el proyecto.
    Todo informativo — no bloquea (una asignación con solapes o pendientes puede ser
    deliberada). `exclude_pid` = el proyecto actual (no se cuenta a sí mismo)."""
    sin_contacto, cred_mal = [], []
    no_cumplen, cert_pv = [], []          # feature 3: certificados requeridos

    # feature 1: otros proyectos activos donde ya está cada usuario asignado.
    otros = {}
    if grupo:
        try:
            for p in P.list_projects(grupo):
                if str(p.get("ID", "")) == str(exclude_pid or ""):
                    continue
                if str(p.get("Estado", "")) in ("Completado", "Cancelado"):
                    continue
                for u in [x.strip() for x in str(p.get("CampoAsignados", "")).split(";")
                          if x.strip()]:
                    otros.setdefault(u, []).append(p)
        except Exception:
            pass

    ocupados = []
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
                # los tipos REQUERIDOS por el proyecto los cubre el chequeo de abajo
                if certs_req and str(c.get("Tipo", "")).strip() in certs_req:
                    continue
                if credentials.status(c.get("Vencimiento")) in ("vencido", "por_vencer"):
                    cred_mal.append(f"{u} — {c.get('Tipo', 'credencial')}: "
                                    f"{credentials.status_label(c.get('Vencimiento'))}")
        except Exception:
            pass
        for p in otros.get(u, []):
            _fin = str(p.get("FechaFinEst", "")).strip()
            ocupados.append(f"**{u}** → :material/apartment: {p.get('Nombre', '')}"
                            + (f" (hasta {_fin})" if _fin else ""))
        if certs_req:
            try:
                comp = credentials.compliance(u, certs_req)
                faltan = [t for t in certs_req if comp["por_tipo"].get(t) in ("falta", "vencido")]
                pv = [t for t in certs_req if comp["por_tipo"].get(t) == "por_vencer"]
                if faltan:
                    no_cumplen.append(f"**{u}**: " + ", ".join(
                        f"{t} ({'falta' if comp['por_tipo'][t] == 'falta' else 'vencido'})"
                        for t in faltan))
                if pv:
                    cert_pv.append(f"**{u}**: " + ", ".join(f"{t}" for t in pv))
            except Exception:
                pass

    if ocupados:
        st.info(":material/push_pin: **Ya asignados a otro proyecto:**\n\n"
                + "\n".join(f"- {x}" for x in ocupados))
    if no_cumplen:
        st.error(":material/cancel: **No cumplen los certificados que exige el proyecto:**\n\n"
                 + "\n".join(f"- {x}" for x in no_cumplen))
    if cert_pv:
        st.warning(":material/schedule: **Certificados requeridos POR VENCER (renovar):**\n\n"
                   + "\n".join(f"- {x}" for x in cert_pv))
    if cred_mal:
        st.warning(":material/badge: **Otras credenciales a revisar antes de mandarlos a obra:**\n\n"
                   + "\n".join(f"- {x}" for x in cred_mal))
    if sin_contacto:
        st.warning(":material/warning: **Sin contacto completo (email + Telegram):** "
                   + ", ".join(sin_contacto)
                   + ". No recibirán la asignación ni las inducciones.")


def _cumplimiento_equipo(pid, grupo, prj):
    """Tabla VIVA de cumplimiento de certificados del equipo asignado (v219): asignados
    × certificados requeridos, ✅/🟡/🔴/—. Solo si el proyecto define requeridos."""
    req = [x.strip() for x in str(prj.get("CertsReq", "")).split(";") if x.strip()]
    if not req:
        return
    st.markdown("**:material/verified_user: Cumplimiento de certificados del equipo**")
    asign = [x.strip() for x in str(prj.get("CampoAsignados", "")).split(";") if x.strip()]
    if not asign:
        st.caption("Sin usuarios de campo asignados todavía.")
        return
    _ico = {"vigente": "vigente", "por_vencer": "por vencer", "vencido": "vencido", "falta": "—"}
    filas = []
    for u in asign:
        comp = credentials.compliance(u, req)
        fila = {"Usuario": u, "Cumple": "sí" if comp["cumple"] else "NO"}
        for t in req:
            fila[t] = _ico.get(comp["por_tipo"].get(t, "falta"), "—")
        filas.append(fila)
    st.dataframe(pd.DataFrame(filas), hide_index=True, use_container_width=True)
    st.caption(":green[:material/check_circle:] vigente · :orange[:material/schedule:] por vencer (renovar) · :red[:material/cancel:] vencido · — falta.  "
               "**Cumple** = ningún certificado requerido vencido ni faltante.")


def _notificar_asignados(usuarios, info_prj):
    """Envía la asignación e informa SIEMPRE del resultado (no falla en silencio)."""
    if not notify.any_channel_configured():
        st.caption(":material/mail: Sin canales de aviso configurados (Gmail / Telegram).")
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
        st.caption(f":material/mail: {n} usuario(s) de campo notificado(s).")
    elif n:
        st.warning(f":material/mail: Notificados {n} de {len(usuarios)}. Al resto le falta contacto.")
    else:
        st.warning(":material/warning: No se pudo notificar a nadie: revisa email y Telegram "
                   "en :material/build: Mi grupo → Usuarios.")


def _field_users(grupo):
    """Usuarios de campo del grupo (para asignar a un proyecto)."""
    try:
        return [u["Usuario"] for u in auth.list_users(grupo)
                if str(u.get("Rol", "")) == "campo"]
    except Exception:
        return []


# ── Panel de proyectos ───────────────────────────────────────────
def _cartera_clickeable(proys, alarmas, delays, aheads, costos):
    """Cartera de proyectos como TARJETAS con toda la info ANTES de abrir (v223, opción A
    elegida por el usuario): nombre, estado + % avance (barra real), cliente, fechas,
    % de presupuesto ejecutado, nº de usuarios asignados y alertas. Se abre con «Abrir».
    Borde izq = salud (rojo=retraso, verde=adelanto, azul=en curso). Rejilla de 2 col,
    ordenada por urgencia. El contenedor keyed permite colorear el borde (verificado)."""
    import html as _htmlmod

    def esc(s):
        return _htmlmod.escape(str(s or ""))

    def _ddmm(s):
        s = str(s or "").strip()[:10]
        if not s:
            return "—"
        from datetime import datetime as _dt
        for _f in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return _dt.strptime(s, _f).strftime("%d/%m")
            except Exception:
                pass
        return "—"

    _pill = {"En progreso": ("#e8eef6", "#1e4e79"), "Planificado": ("#f0efe8", "#5f5e5a"),
             "Completado": ("#e8f5ee", "#1e6e4e"), "En pausa": ("#faeeda", "#8a5a0b"),
             "Cancelado": ("#fbeaea", "#a12d2d"), "Archivado": ("#eceff3", "#5f5e5a")}

    def _salud(pid):
        return "#c0392b" if delays.get(pid) else ("#1e8449" if aheads.get(pid) else "#2e6da4")

    proys = sorted(proys, key=lambda p: (-delays.get(str(p.get("ID", "")), 0),
                                         -alarmas.get(str(p.get("ID", "")), 0)))

    # Borde izquierdo por salud en cada tarjeta (contenedor keyed = .st-key-cart_<i>, v223).
    _css = ["<style>"]
    for _i, p in enumerate(proys):
        _css.append(f".st-key-cart_{_i}{{border-left:4px solid "
                    f"{_salud(str(p.get('ID', '')))}!important;}}")
    _css.append("</style>")
    st.markdown("".join(_css), unsafe_allow_html=True)

    for _r in range(0, len(proys), 2):
        _cols = st.columns(2)
        for _j in range(2):
            _idx = _r + _j
            if _idx >= len(proys):
                break
            p = proys[_idx]
            _pid = str(p.get("ID", ""))
            _av = max(0, min(100, int(P._num(p.get("Avance")))))
            _dl, _ah, _al = delays.get(_pid, 0), aheads.get(_pid, 0), alarmas.get(_pid, 0)
            _col = _salud(_pid)
            _est = str(p.get("Estado", "") or "—")
            _pbg, _pfg = _pill.get(_est, ("#eceff3", "#5f5e5a"))
            _users = len([x for x in str(p.get("CampoAsignados", "")).split(";") if x.strip()])
            _c = costos.get(_pid) or {}
            if P._num(_c.get("presupuesto")) > 0:
                _ppto = f"{int(round(P._num(_c.get('pct'))))}% ppto" + (" " + _MI("warning", "#e0a021") if _c.get("over") else "")
            else:
                _ppto = "s/ppto"
            _chips = f"{_MI('payments')} {_ppto} · {_MI('engineering')} {_users}"
            if _dl:
                _chips += f" · {_MI('cancel','#d64541')} {_dl}d"
            elif _ah:
                _chips += f" · {_MI('check_circle','#1e9e57')} {_ah}d"
            if _al:
                _chips += f" · {_MI('notifications')} {_al}"
            _html = (
                "<div style='display:flex;justify-content:space-between;align-items:center;"
                "gap:8px;margin-bottom:6px;'>"
                "<div style='display:flex;align-items:center;gap:7px;min-width:0;'>"
                f"<span style='width:9px;height:9px;border-radius:50%;background:{_col};"
                "flex:none;'></span>"
                "<span style='font-weight:700;font-size:15px;overflow:hidden;"
                f"text-overflow:ellipsis;white-space:nowrap;'>{esc(p.get('Nombre', ''))}</span></div>"
                f"<span style='background:{_pbg};color:{_pfg};font-size:11.5px;padding:2px 8px;"
                f"border-radius:6px;white-space:nowrap;'>{esc(_est)}</span></div>"
                "<div style='display:flex;align-items:center;gap:8px;margin-bottom:6px;'>"
                "<div style='flex:1;height:7px;background:#eef1f5;border-radius:20px;"
                "overflow:hidden;'>"
                f"<div style='height:100%;width:{_av}%;background:#2e6da4;"
                "border-radius:20px;'></div></div>"
                f"<span style='font-size:12.5px;font-weight:600;color:#374151;'>{_av}%</span></div>"
                f"<div style='font-size:12.5px;color:#6b7280;margin-bottom:5px;'>{_MI('person')} "
                f"{esc(p.get('Cliente', '') or '—')} · {_MI('calendar_month')} {_ddmm(p.get('FechaInicio'))} → "
                f"{_ddmm(p.get('FechaFinEst'))}</div>"
                f"<div style='font-size:12.5px;color:#374151;'>{_chips}</div>")
            with _cols[_j].container(border=True, key=f"cart_{_idx}"):
                st.markdown(_html, unsafe_allow_html=True)
                if st.button("Abrir →", key=f"cartbtn_{_idx}", use_container_width=True):
                    st.session_state["_admin_open_proj"] = _pid
                    st.rerun()


def _cartera_lista(proys, alarmas, delays, aheads, costos):
    """Vista LISTA de la cartera (v228): la típica tabla — proyectos por filas, datos por
    columnas — CLICKEABLE (seleccionar una fila abre el detalle, igual que las tarjetas).
    Alternativa a `_cartera_clickeable`; se elige con el toggle de vista."""
    proys = sorted(proys, key=lambda p: (-delays.get(str(p.get("ID", "")), 0),
                                         -alarmas.get(str(p.get("ID", "")), 0)))

    def _ddmm(s):
        s = str(s or "").strip()[:10]
        if not s:
            return "—"
        from datetime import datetime as _dt
        for _f in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return _dt.strptime(s, _f).strftime("%d/%m/%y")
            except Exception:
                pass
        return "—"

    _rows = []
    for p in proys:
        _pid = str(p.get("ID", ""))
        _dl, _ah, _al = delays.get(_pid, 0), aheads.get(_pid, 0), alarmas.get(_pid, 0)
        _c = costos.get(_pid) or {}
        _ppto = (f"{int(round(P._num(_c.get('pct'))))}%" + (" over" if _c.get("over") else "")
                 if P._num(_c.get("presupuesto")) > 0 else "—")
        _users = len([x for x in str(p.get("CampoAsignados", "")).split(";") if x.strip()])
        _sit = (f"{_dl} d retraso" if _dl else (f"{_ah} d adelanto" if _ah else "—"))
        _rows.append({
            "Proyecto": str(p.get("Nombre", "")),
            "Estado": str(p.get("Estado", "") or "—"),
            "Avance": max(0, min(100, int(P._num(p.get("Avance"))))),
            "Cliente": str(p.get("Cliente", "") or "—"),
            "Inicio": _ddmm(p.get("FechaInicio")),
            "Fin": _ddmm(p.get("FechaFinEst")),
            "Ppto": _ppto,
            "Usuarios": _users,
            "Situación": _sit,
            "Alertas": str(_al) if _al else "",
        })
    _ev = st.dataframe(
        pd.DataFrame(_rows), hide_index=True, use_container_width=True,
        on_select="rerun", selection_mode="single-row", key="cart_tbl",
        column_config={"Avance": st.column_config.ProgressColumn(
            "Avance", min_value=0, max_value=100, format="%d%%")})
    st.caption(":material/touch_app: Toca una fila para abrir el proyecto.  "
               "Ppto = % del presupuesto ejecutado (:orange[:material/warning:] si se pasó) y over = sobre presupuesto.")
    try:
        _sr = list(_ev.selection.rows)
    except Exception:
        _sr = []
    if _sr and _sr[0] < len(proys):
        st.session_state["_admin_open_proj"] = str(proys[_sr[0]].get("ID", ""))
        st.session_state.pop("cart_tbl", None)   # limpia la selección → no re-abre al volver
        st.rerun()


def _panel_proyectos(grupo: str):
    # ── Proyecto ABIERTO (de una tarjeta, de HOME "ver completo", o del crear) ──
    _pp = st.session_state.pop("_prjsel_pending", None)
    if _pp:
        st.session_state["_admin_open_proj"] = str(_pp)
    _open = st.session_state.get("_admin_open_proj")
    if _open:
        if st.button("← Volver a la cartera", key="pp_back_cartera"):
            st.session_state.pop("_admin_open_proj", None)
            st.rerun()
        st.markdown("---")
        _detalle_proyecto(str(_open), grupo)
        return

    # ── Cartera (tarjetas clickeables → abren el detalle) ──
    _ver_arch = st.checkbox(":material/archive: Ver también los archivados", key="ver_arch_admin",
                            help="Los archivados no salen en listas ni informes; "
                                 "ábrelos desde aquí para restaurarlos.")
    proys = P.list_projects(grupo=grupo, incluir_archivados=_ver_arch)
    if not _ver_arch:
        _n_arch = len([p for p in P.list_projects(grupo=grupo, incluir_archivados=True)
                       if str(p.get("Estado", "")) == P.ARCHIVADO])
        if _n_arch:
            st.caption(f":material/inventory_2: {_n_arch} proyecto(s) archivado(s) oculto(s).")
    if not proys:
        # ⚠️ El formulario va ANTES del return: desde v135 el survey ya no crea
        # proyectos, así que si aquí se cortara no habría forma de crear el primero.
        st.info("Todavía no hay proyectos en este grupo. Crea el primero aquí; "
                "después el Survey y las demás herramientas podrán alimentarlo.")
        _nuevo_proyecto_form(grupo, key="adm")
        return

    # % de presupuesto ejecutado por proyecto — de group_expenses (1 lectura CACHEADA,
    # no N): {pid: {pct, presupuesto, over, ...}}. v223.
    costos = {}
    try:
        from core import expenses as _exp
        _ge = _exp.group_expenses(grupo)
        costos = {str(r.get("id")): r for r in (_ge.get("proyectos") or [])}
    except Exception:
        pass
    alarmas = alerts.open_counts_all() if alerts.is_configured() else {}
    delays = P.delays_of_group(grupo)     # {pid: días de retraso} (cacheado)
    aheads = P.aheads_of_group(grupo)     # {pid: días de adelanto} (cacheado)

    # ── Filtro rápido (v209): búsqueda + chips, en doble columna ──
    _fc1, _fc2 = st.columns([2, 3])
    _q = _fc1.text_input("Buscar", key="cart_q", label_visibility="collapsed",
                         placeholder="Buscar proyecto o cliente…")
    _filt = _fc2.radio("Filtro", ["Todos", "🔴 Retraso", "🟢 Adelanto", "⏸ En pausa"],
                       format_func=lambda o: {"🔴 Retraso": ":red[:material/trending_down:] Retraso",
                                              "🟢 Adelanto": ":green[:material/trending_up:] Adelanto",
                                              "⏸ En pausa": ":material/pause: En pausa"}.get(o, o),
                       horizontal=True, key="cart_filt", label_visibility="collapsed")
    _ql = (_q or "").strip().lower()

    def _pasa(p):
        _pid = str(p.get("ID", ""))
        if _ql and _ql not in f"{p.get('Nombre', '')} {p.get('Cliente', '')}".lower():
            return False
        if _filt == "🔴 Retraso":
            return bool(delays.get(_pid))
        if _filt == "🟢 Adelanto":
            return bool(aheads.get(_pid))
        if _filt == "⏸ En pausa":
            return str(p.get("Estado", "")) == "En pausa"
        return True
    _proys_f = [p for p in proys if _pasa(p)]

    _nr, _na = len(delays), len(aheads)
    _hc1, _hc2 = st.columns([3, 2])
    _hc1.markdown(f"**Cartera — {len(_proys_f)} de {len(proys)}**"
                  + (f"  ·  :red[:material/cancel:] {_nr} con retraso" if _nr else "")
                  + (f"  ·  :green[:material/check_circle:] {_na} adelantado(s)" if _na else ""))
    # v228: toggle de vista — tarjetas (resumen visual) o lista (tabla clásica).
    _view = _hc2.radio("Vista", ["📋 Lista", "🃏 Tarjetas"], horizontal=True,
                       format_func=lambda o: {"🃏 Tarjetas": ":material/grid_view: Tarjetas",
                                              "📋 Lista": ":material/list: Lista"}.get(o, o),
                       key="cart_view", label_visibility="collapsed")
    if not _proys_f:
        st.caption("Ningún proyecto coincide con el filtro.")
    elif _view == "📋 Lista":
        _cartera_lista(_proys_f, alarmas, delays, aheads, costos)
    else:
        st.caption("Cada tarjeta muestra el resumen; toca «Abrir» para ver el detalle.")
        _cartera_clickeable(_proys_f, alarmas, delays, aheads, costos)
    # `_nuevo_proyecto_form` ya se pliega solo (tiene su propio expander) → no envolver
    # otra vez, o quedan dos expanders "Nuevo proyecto" anidados (v210).
    _nuevo_proyecto_form(grupo, key="adm")


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
            sub = f"{_MI('business')} {p.get('Grupo')} · " + sub
        ubic = str(p.get("Ubicacion", "") or "")
        ubic_html = (f'<div style="font-size:11.5px;white-space:nowrap;overflow:hidden;'
                     f'text-overflow:ellipsis;">{maps.maps_link_html(ubic, ubic, color="#2e6da4")}</div>'
                     if ubic else "")
        alarm = (f'<div style="width:44px;text-align:center;flex:none;color:#c0392b;'
                 f'font-size:12.5px;font-weight:600;">{_MI('notifications')} {na}</div>'
                 if na else '<div style="width:44px;flex:none;"></div>')
        # Retraso (rojo) / adelanto (verde) → borde + badge de días
        d, adel = delays.get(pid), aheads.get(pid)
        card_border = "border:1px solid #e6e9ef"
        retraso_badge = ""
        if d:
            card_border = "border:1px solid #e6e9ef;border-left:4px solid #c0392b"
            retraso_badge = (f'<span style="font-size:12px;padding:3px 9px;border-radius:20px;'
                             f'background:#fcebeb;color:#a32d2d;white-space:nowrap;flex:none;'
                             f'font-weight:600;">{_MI('alarm')} {d:.0f} d</span>')
        elif adel:
            card_border = "border:1px solid #e6e9ef;border-left:4px solid #1e8449"
            retraso_badge = (f'<span style="font-size:12px;padding:3px 9px;border-radius:20px;'
                             f'background:#eaf3de;color:#3b6d11;white-space:nowrap;flex:none;'
                             f'font-weight:600;">{_MI('trending_up')} {adel:.0f} d</span>')
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
            f'color:{fg};white-space:nowrap;flex:none;">{est}</span>'
            '<div style="width:118px;flex:none;">'
            '<div style="display:flex;justify-content:space-between;font-size:11.5px;'
            f'color:#6b7280;margin-bottom:3px;"><span>Avance</span>'
            f'<span style="color:#1f2937;font-weight:600;">{av:.0f}%</span></div>'
            '<div style="height:6px;background:#eef1f5;border-radius:20px;overflow:hidden;">'
            f'<div style="height:100%;width:{av:.0f}%;background:{bar};"></div></div>'
            '</div>'
            f'<div style="width:54px;text-align:right;flex:none;font-size:12px;color:#6b7280;">'
            f'{_MI("schedule")} {hrs:.0f}h</div>'
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
    with st.expander(":material/push_pin: Instrucciones e inducciones del proyecto", expanded=bool(links)):
        if instr:
            st.markdown("**Instrucciones particulares**")
            st.markdown(instr)
        if links:
            st.markdown("**Inducciones a diligenciar**")
            for l in links:
                st.markdown(f"- [{l}]({l})")
            if allow_send and notify.any_channel_configured():
                asignados = [x.strip() for x in str(prj.get("CampoAsignados", "")).split(";") if x.strip()]
                if asignados and st.button(":material/send: Reenviar inducción a los asignados",
                                           key=f"send_ind_{pid}"):
                    n = 0
                    for un in asignados:
                        try:
                            rr = notify.notify_induction(un, prj.get("Nombre", ""), links)
                            if rr.get("email") or rr.get("telegram"):
                                n += 1
                        except Exception:
                            pass
                    st.success(f":material/send: Enviado a {n} usuario(s) de campo.")


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


def _equipo_proyecto(pid, grupo):
    """:material/engineering: Quién ha trabajado en ESTE proyecto y cuántas horas (v216). El dato ya
    estaba (labor_breakdown, usado en 💰 Costos); aquí se surfacea, sin el costo."""
    try:
        from core import expenses as E
        if not E.is_configured():
            return
        _lb = E.labor_breakdown(pid, grupo)
    except Exception:
        return
    st.markdown("**:material/groups: Quién ha trabajado aquí**")
    if not _lb["items"]:
        st.caption("Nadie ha fichado horas a este proyecto todavía.")
        return
    st.dataframe(pd.DataFrame([{"Persona": x["usuario"], "Horas": x["horas"]}
                               for x in _lb["items"]]),
                 hide_index=True, use_container_width=True)
    st.caption(f"Total: **{_lb['horas']:.1f} h**")


def _estado_section(pid: str, grupo: str, prj: dict):
    """Pestaña :material/bar_chart: Estado (v211: doble columna arriba — cómo va | alarmas + equipo; el
    ritmo, el desglose y el cronograma van a ancho completo abajo)."""
    ps = P.project_schedule(pid)
    if not (ps and ps["sched"].get("activities")):
        _alerts_section(pid, grupo, prj.get("Nombre", ""), allow_report=False)
        st.info("Este proyecto no tiene actividades, así que no hay cronograma "
                "que seguir. Añádelas en :material/edit: Datos.")
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

    # ── KPIs (tarjetas, no st.metric planos) ──
    _fin = (proj["fecha_proj"].strftime("%d/%m/%Y")
            if proj.get("fecha_proj") else "—")
    _pd  = proj.get("proj_dias")
    _cf  = "#c0392b" if (_pd is not None and _pd > 0.5) else (
           "#1e8449" if (_pd is not None and _pd < -0.5) else None)
    _est = ("En fecha" if abs(dg) < 0.5
            else f"{abs(dg):.0f} d {'de retraso' if dg > 0 else 'de adelanto'}")
    # v212: "Avance real" ya está en la cabecera del detalle (métrica + barra) → no
    # repetirlo aquí. "Debería ir" y "Desvío" se leen contra ese avance de la cabecera.
    tarj = [_kpi_card("Debería ir", f"{d['pv']:.0f}%"),
            _kpi_card("Desvío", f"{dv:+.0f}%", _col),
            _kpi_card("Situación", _est, "#c0392b" if dg > 0.5 else None),
            _kpi_card("Fin proyectado", _fin, _cf)]

    # ── Doble columna (v211): cómo va (izq) | alarmas (der) ──
    _izq, _der = st.columns([3, 2], gap="large")
    with _izq:
        st.markdown(f"<div style='font-size:17px;margin-bottom:8px'>{_tit} "
                    f"<span style='color:#6b7280;font-size:14px'>· {_dia_txt}</span></div>",
                    unsafe_allow_html=True)
        st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:10px">'
                    + "".join(tarj) + "</div>", unsafe_allow_html=True)
    with _der:
        _alerts_section(pid, grupo, prj.get("Nombre", ""), allow_report=False)
        st.markdown("")
        _equipo_proyecto(pid, grupo)

    # ── Cumplimiento de certificados del equipo (si el proyecto exige alguno) ──
    _cumplimiento_equipo(pid, grupo, prj)

    # ── El ritmo: mas accionable que el SPI ──
    if d["ritmo_real"] is not None and d["ritmo_nec"] is not None:
        if d["dias_rest"] <= 0:
            st.warning(f":material/schedule: La fecha de fin planificada ya pasó y queda "
                       f"**{100 - d['ev']:.0f}%** por completar.")
        elif d["factor"] and d["factor"] > 1.15:
            st.error(f":material/schedule: Vas a **{d['ritmo_real']:.1f} %/día** y necesitas "
                     f"**{d['ritmo_nec']:.1f} %/día** para llegar a la fecha: "
                     f"hay que **acelerar ×{d['factor']:.1f}** en los "
                     f"{d['dias_rest']:.0f} días que quedan.")
        elif d["factor"] and d["factor"] < 0.85:
            st.success(f":material/schedule: Vas a **{d['ritmo_real']:.1f} %/día** y con "
                       f"**{d['ritmo_nec']:.1f} %/día** llegas: hay margen.")
        else:
            st.info(f":material/schedule: Vas a **{d['ritmo_real']:.1f} %/día**, justo el ritmo "
                    f"que hace falta ({d['ritmo_nec']:.1f} %/día).")

    # ── Que tocaba hoy vs que se esta haciendo: el porque del retraso ──
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**:material/push_pin: Tocaba hoy**")
        if not d["tocaban"]:
            st.caption("Ninguna actividad tiene su ventana abierta hoy.")
        for x in d["tocaban"]:
            if x["avance"] <= 0:
                st.markdown(f":red[:material/cancel:] **{x['nombre']}** — sin empezar, arrancaba el "
                            f"{x['desde'].strftime('%d/%m')} ({x['dur']:.0f} d)")
            else:
                st.markdown(f":green[:material/check_circle:] {x['nombre']} — {x['avance']:.0f}%")
    with c2:
        st.markdown("**:material/pending_actions: En curso ahora**")
        if not d["en_curso"]:
            st.caption("Ninguna actividad entre 1% y 99%.")
        for x in d["en_curso"]:
            st.markdown(("⏳ " if x["tarde"] else "▶️ ")
                        + f"{x['nombre']} — {x['avance']:.0f}%"
                        + (" _(arrastrada)_" if x["tarde"] else ""))

    # El diagnostico: el equipo sigue en trabajo viejo y lo de hoy no arranca
    if d["paradas"] and d["arrastradas"]:
        st.warning(":material/stethoscope: El equipo sigue terminando **"
                   + ", ".join(x["nombre"] for x in d["arrastradas"][:3])
                   + "**, así que **"
                   + ", ".join(x["nombre"] for x in d["paradas"][:3])
                   + "** aún no ha arrancado. Ahí está el retraso.")
    elif d["paradas"]:
        st.warning(":material/stethoscope: Sin empezar y ya tocaba: **"
                   + ", ".join(x["nombre"] for x in d["paradas"][:3]) + "**.")

    if d["proximo"]:
        st.caption(f":material/flag: Próximo hito: **{d['proximo']['nombre']}** arranca el "
                   f"{d['proximo']['fecha'].strftime('%d/%m/%Y')} "
                   f"(en {d['proximo']['faltan']:.0f} días).")

    # ── La grafica ──
    st.markdown("**:material/calendar_month: Cronograma y avance**")
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
        f'color:{_fg};white-space:nowrap;">{est}</span></div>'
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
    # v234: format_func muestra iconos Material; las OPCIONES siguen siendo el ID (con
    # emoji) → el match de abajo y cualquier deep-link no cambian.
    _sec = st.radio("Sección del proyecto",
                    ["📊 Estado", "✏️ Datos", "💰 Costos", "📎 Archivos"],
                    format_func=lambda o: {"📊 Estado": ":material/insights: Estado",
                                           "✏️ Datos": ":material/edit: Datos",
                                           "💰 Costos": ":material/payments: Costos",
                                           "📎 Archivos": ":material/folder: Archivos"}.get(o, o),
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
        asignados = st.multiselect(":material/engineering: Usuarios de campo asignados", _opts,
                                   default=_actuales, key=f"asig_{pid}")
        _ecerts = st.multiselect(
            ":material/badge: Certificados que exige el proyecto", credentials.CATALOGO,
            default=[x.strip() for x in str(prj.get("CertsReq", "")).split(";") if x.strip()],
            key=f"certs_{pid}",
            help="Al asignar personal se avisa y marca a quien no los cumpla.")
        # feature 1 (ya en otro proyecto) + feature 3 (cumplimiento vs certs requeridos)
        _avisar_asignados(asignados, grupo, exclude_pid=pid, certs_req=_ecerts)

        # ── Ubicación en el mapa (fuera del form: el mapa necesita reruns) — v193 ──
        from core import location_ui
        with st.expander("Ubicación en el mapa (pin del proyecto)", icon=":material/map:",
                         expanded=not location_ui.to_float(prj.get("Lat"))):
            _plat, _plng = location_ui.location_picker(
                f"edloc_{pid}",
                lat=location_ui.to_float(prj.get("Lat")),
                lng=location_ui.to_float(prj.get("Lng")),
                direccion=str(prj.get("Ubicacion", "")))

        # ── Cliente: elegir existente o escribir uno nuevo (fuera del form) — v256 ──
        from core import clientes as _C
        _cli_fichas = _C.list_clientes(grupo)
        _cli_names = [str(c.get("Nombre", "")) for c in _cli_fichas]
        _CLI_NONE, _CLI_OTRO = "— sin cliente —", "➕ Otro (escribir uno nuevo)"
        _opts_cli = [_CLI_NONE] + _cli_names + [_CLI_OTRO]
        _cur_cid = str(prj.get("ClienteID", "")).strip()
        _cur_txt = str(prj.get("Cliente", "")).strip()
        _cur_name = ""
        if _cur_cid:
            _cur_name = next((str(c.get("Nombre", "")) for c in _cli_fichas
                              if str(c.get("ID", "")) == _cur_cid), "")
        if not _cur_name and _cur_txt:
            _cur_name = next((n for n in _cli_names if _C._norm(n) == _C._norm(_cur_txt)), "")
        _cidx = (_opts_cli.index(_cur_name) if _cur_name
                 else (_opts_cli.index(_CLI_OTRO) if _cur_txt else 0))
        _ecli_sel = st.selectbox(":material/contacts: Cliente", _opts_cli, index=_cidx,
                                 key=f"ed_clisel_{pid}",
                                 help="Elige un cliente de Contactos o escribe uno nuevo.")
        _ecli_new = ""
        if _ecli_sel == _CLI_OTRO:
            _ecli_new = st.text_input("Nombre del nuevo cliente",
                                      value=(_cur_txt if not _cur_name else ""),
                                      key=f"ed_clinew_{pid}")

        # ── Editar datos ──
        with st.form(f"edit_{pid}"):
            st.markdown("**Datos del proyecto**")
            nombre   = st.text_input("Nombre", value=prj.get("Nombre", ""))
            e1, e2 = st.columns(2)
            ubic     = e1.text_input("Ubicación", value=prj.get("Ubicacion", ""))
            modelo   = e2.text_input("Modelo", value=prj.get("Modelo", ""))
            ing      = e1.text_input("Ingeniero", value=prj.get("Ingeniero", ""))
            # Calendario, no texto libre: ver `_a_fecha`. El valor se guarda
            # siempre en ISO, que es lo unico que `project_schedule` sabe leer.
            f_ini    = e2.date_input("Fecha inicio", value=_a_fecha(prj.get("FechaInicio")),
                                     format="YYYY-MM-DD")
            f_fin    = e1.date_input("Fecha fin estimada", value=_a_fecha(prj.get("FechaFinEst")),
                                     format="YYYY-MM-DD")
            instr    = st.text_area(":material/push_pin: Instrucciones particulares", value=prj.get("Instrucciones", ""))
            ind      = st.text_area(":material/description: Inducciones (un link por línea)",
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
            presup  = st.number_input(":material/payments: Presupuesto del proyecto (0 = sin presupuesto)",
                                      min_value=0.0, step=100.0, value=P._num(prj.get("Presupuesto")))
            _defm = auth.group_margin_default(grupo)
            _m0 = (P._num(prj.get("MargenMO")) if str(prj.get("MargenMO", "")).strip() != ""
                   else float(_defm))
            margen  = st.number_input(
                ":material/trending_up: Margen sobre mano de obra (%) — lo que cobras al cliente",
                min_value=0.0, max_value=500.0, step=1.0, value=_m0,
                help=f"Venta de la MO = costo × (1+margen). Default del grupo: {_defm:.0f}% "
                     f"(lo fija el propietario en Grupos).")

            if st.form_submit_button(":material/save: Guardar cambios", use_container_width=True):
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
                    # Cliente elegido/escrito → texto + ClienteID (v256)
                    if _ecli_sel in _cli_names:
                        cliente = _ecli_sel
                        _ecli_id = next((str(c.get("ID", "")) for c in _cli_fichas
                                         if str(c.get("Nombre", "")) == _ecli_sel), "")
                    elif _ecli_sel == _CLI_OTRO:
                        cliente, _ecli_id = _ecli_new.strip(), ""
                    else:
                        cliente, _ecli_id = "", ""
                    P.update_project(pid, {   # todo en UNA escritura (batch) → sin rate limit
                        "Nombre": nombre, "Cliente": cliente, "ClienteID": _ecli_id,
                        "Ubicacion": ubic, "Modelo": modelo,
                        "Ingeniero": ing, "FechaInicio": f_ini, "FechaFinEst": f_fin,
                        "CampoAsignados": ";".join(asignados),
                        "AgrupacionID": ag_id, "PesoEnAgrupacion": peso,
                        "EstadoManual": est_man, "Estado": P.derive_estado(avance, est_man),
                        "Instrucciones": instr, "InduccionLinks": ind, "Presupuesto": presup,
                        "MargenMO": margen,
                        "Lat": "" if _plat is None else _plat,
                        "Lng": "" if _plng is None else _plng,
                        "CertsReq": ";".join(_ecerts),
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
                    # v219: sincronizar el planificador — poner a los nuevos en el
                    # proyecto entre sus fechas y quitar del roster a los desasignados.
                    _quitados = [x for x in actuales if x not in asignados]
                    _autoagenda(grupo, pid, nuevos, _quitados, f_ini, f_fin)
                    st.toast("Cambios guardados." + (f"  :material/send: {_sent} notificado(s)." if _sent else ""))
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
            if st.button(":material/save: Guardar tabla de actividades", key=f"savetbl_{pid}"):
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

        with st.expander("Agregar / eliminar actividad (recalcula el % automáticamente)",
                         icon=":material/playlist_add:"):
            with st.form(f"addact_{pid}", clear_on_submit=True):
                st.markdown("**:material/add: Agregar actividad**")
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
                st.markdown("**:material/delete: Eliminar actividad**")
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
            st.info(":material/inventory_2: Este proyecto está **archivado**: no aparece en las listas "
                    "ni en los informes, pero no se ha perdido nada.")
            if st.button(":material/recycling: Restaurar proyecto", key=f"unarch_{pid}",
                         use_container_width=True):
                ok, msg = P.set_archivado(pid, False)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()
        else:
            with st.expander(":material/inventory_2: Archivar proyecto"):
                st.caption("Desaparece de las listas y de los informes, pero se "
                           "conserva entero y puede restaurarse cuando quieras. "
                           "Es lo recomendado al cerrar una obra.")
                if st.button(":material/inventory_2: Archivar", key=f"arch_{pid}", use_container_width=True):
                    ok, msg = P.set_archivado(pid, True)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()

        # Borrado de verdad: SOLO propietario. `delete_project` quita el proyecto
        # y sus actividades, pero deja huerfanos documentos (con sus archivos en
        # Drive), gastos, calculos, pre-starts, alarmas y fichajes — por eso se
        # enseña el inventario antes y se exige teclear el nombre.
        if st.session_state.get("auth", {}).get("rol") == "propietario":
            with st.expander(":material/delete_forever: Eliminar definitivamente (irreversible)"):
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
        with st.expander(":material/sync: Reconstruir proyecto en el Survey (regenerar informes)"):
            st.caption("Carga los parámetros y la matriz guardados en la pestaña :material/architecture: Survey. "
                       "Luego pulsa **Calcular** allí para regenerar diagramas e informes.")
            if st.button(":material/sync: Cargar este proyecto en el Survey", key=f"rebuild_{pid}"):
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
                    st.success(":material/check_circle: Cargado. Ve a **:material/architecture: Survey** y pulsa **Calcular** para regenerar todo.")
        # ── Archivos del proyecto (buscable) ──
        _archivos_section(pid)


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
            f":material/event: **La entrega la marca «{proj['critico']}»** — proyectada para "
            f"**{_fecha}**" + (f", con **{_d:.0f} días de retraso**." if _d else
                               ", en fecha.")
            + "  Es donde más rinde reforzar.")
    if proj.get("sin_datos"):
        st.caption("Sin cronograma para proyectar: " + ", ".join(proj["sin_datos"]))

    if tot_pres > 0:
        _p = round(100 * tot_c / tot_pres)
        (st.error if tot_c > tot_pres else st.caption)(
            f"Presupuesto de la agrupación ${tot_pres:,.0f} · {_p}% consumido"
            + (" :red[:material/block:] SOBRE PRESUPUESTO" if tot_c > tot_pres else ""))

    # ── Curva S CONSOLIDADA (plan vs real de todo el conjunto) ──
    try:
        cur = P.grouping_curve(aid, grupo)
    except Exception:
        cur = {}
    if cur and cur.get("fechas"):
        st.markdown("**:material/trending_up: Avance del conjunto — plan vs real**")
        _df = pd.DataFrame({"Planificado": cur["plan"], "Real": cur["real"]},
                           index=pd.to_datetime(cur["fechas"]))
        st.line_chart(_df, height=240)
        st.caption("Ponderado por el peso de cada elevador. La curva real se corta en HOY.")

    # ── Comparativa entre elevadores ──
    # En un edificio son unidades casi gemelas, así que la desviación respecto
    # al promedio delata al que se sale de lo normal.
    st.markdown("**:material/analytics: Comparativa entre elevadores**")
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
            "Situación": (f"{delays[pid]:.0f} d retraso" if pid in delays
                     else (f"{aheads[pid]:.0f} d adelanto" if pid in aheads else "en fecha")),
            "Horas": _hs[i], "vs media h": _dev(_hs[i], _hm),
            "Costo": _cs[i], "vs media $": _dev(_cs[i], _cm),
            "Alertas": _na or "",
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    st.caption("«vs media» compara cada elevador con el promedio de la agrupación; "
               "solo se marca si se desvía 15% o más.")

    _out = [r["Elevador"] for r in rows if r["vs media h"].startswith("+")]
    if _out:
        st.info(":material/warning: Consumen bastantes más horas que sus gemelos: **"
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
                     f'font-weight:600;">{_MI('alarm')} {gap:.0f} d</span>')
        elif gap and gap < -0.5:
            borde = "border:1px solid #e6e9ef;border-left:4px solid #1e8449"
            badge = (f'<span style="font-size:12px;padding:3px 9px;border-radius:20px;'
                     f'background:#eaf3de;color:#3b6d11;white-space:nowrap;flex:none;'
                     f'font-weight:600;">{_MI('trending_up')} {abs(gap):.0f} d</span>')
        punto = "#c0392b" if (gap and gap > 0.5) else ("#1e8449" if av >= 100 else "#2e6da4")

        sub = f"{aid} · {len(miemb)} elevador(es)"
        if a.get("Descripcion"):
            sub += f" · {a['Descripcion']}"
        entrega = (f'<div style="font-size:11.5px;color:#6b7280;">{_MI('event')} entrega '
                   f'<b>{fecha.strftime("%d/%m/%Y")}</b>'
                   + (f' — la marca {critico}' if critico else "") + '</div>'
                   if fecha else
                   '<div style="font-size:11.5px;color:#9aa7b8;">sin cronograma para proyectar</div>')
        alarm = (f'<div style="width:44px;text-align:center;flex:none;color:#c0392b;'
                 f'font-size:12.5px;font-weight:600;">{_MI('notifications')} {n_al}</div>'
                 if n_al else '<div style="width:44px;flex:none;"></div>')

        parts.append(
            f'<div style="display:flex;align-items:center;gap:12px;padding:11px 14px;'
            f'{borde};border-radius:10px;margin-bottom:8px;background:#fff;">'
            f'<div style="width:9px;height:9px;border-radius:50%;background:{punto};flex:none;"></div>'
            '<div style="flex:1;min-width:0;">'
            f'<div style="font-size:14px;font-weight:600;color:#1f2937;white-space:nowrap;'
            f'overflow:hidden;text-overflow:ellipsis;">{_MI('account_tree')} {a.get("Nombre","")}</div>'
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
                ":material/warning: Ya en otra", help="Marcarlo aquí lo MUEVE a esta agrupación."),
        })
    out = {}
    for _, r in ed.iterrows():
        if bool(r["En la agrupación"]):
            pid = str(r["Proyecto"]).rsplit("(", 1)[-1].rstrip(")")
            out[pid] = float(r["Peso"] or 1.0)
    return out


def _cartera_agrupaciones(ags, grupo):
    """Agrupaciones como botones CLICKEABLES (v214): tocar abre su tablero. Fondo =
    avance consolidado; borde = salud (entrega del elevador más lento). Ordenadas por
    urgencia. Mismo lenguaje que la cartera de proyectos."""
    proys_all = P.list_projects(grupo=grupo)
    alarmas = alerts.open_counts_all() if alerts.is_configured() else {}
    try:
        proyecc = P.projections_by_group(grupo)
    except Exception:
        proyecc = {}
    rows = []
    for a in ags:
        aid = str(a.get("ID", ""))
        miemb = [p for p in proys_all if str(p.get("AgrupacionID", "")) == aid]
        av = P.grouping_progress(aid)["avance"]
        fecha, gap = None, 0.0
        for p in miemb:
            _d = proyecc.get(str(p.get("ID", "")))
            if _d and _d.get("fecha") and (fecha is None or _d["fecha"] > fecha):
                fecha, gap = _d["fecha"], _d.get("gap") or 0.0
        n_al = sum(alarmas.get(str(p.get("ID", "")), 0) for p in miemb)
        rows.append({"a": a, "aid": aid, "n": len(miemb), "av": av,
                     "gap": gap, "n_al": n_al, "fecha": fecha})
    rows.sort(key=lambda r: -r["gap"])

    _css = ["<style>"]
    for _i, r in enumerate(rows):
        _av = max(0, min(100, int(r["av"])))
        _col = "#c0392b" if r["gap"] > 0.5 else ("#1e8449" if r["gap"] < -0.5 else "#2e6da4")
        _tint = "#fdecec" if r["gap"] > 0.5 else ("#e8f5ee" if r["gap"] < -0.5 else "#e8eef6")
        _css.append(
            f".st-key-agrc_{_i} button{{background:linear-gradient(to right,"
            f"{_tint} {_av}%,#f4f6f9 {_av}%)!important;border-left:5px solid {_col}!important;"
            "justify-content:flex-start!important;padding-left:12px!important;}"
            f".st-key-agrc_{_i} button>div{{justify-content:flex-start!important;width:100%!important;}}"
            f".st-key-agrc_{_i} button p{{text-align:left!important;width:100%!important;}}")
    _css.append("</style>")
    st.markdown("".join(_css), unsafe_allow_html=True)

    for _r0 in range(0, len(rows), 2):
        _cols = st.columns(2)
        for _j in range(2):
            _idx = _r0 + _j
            if _idx >= len(rows):
                break
            r = rows[_idx]
            _av = max(0, min(100, int(r["av"])))
            _extra = ""
            if r["gap"] > 0.5:
                _extra += f" · :material/alarm: {r['gap']:.0f}d"
            elif r["gap"] < -0.5:
                _extra += f" · :material/trending_up: {abs(r['gap']):.0f}d"
            if r["n_al"]:
                _extra += f" · :material/notifications: {r['n_al']}"
            if r["fecha"]:
                _extra += f" · :material/event: {r['fecha'].strftime('%d/%m')}"
            _lbl = f"**:material/account_tree: {r['a'].get('Nombre', '')}** · {r['n']} elev · {_av}%{_extra}"
            if _cols[_j].button(_lbl, key=f"agrc_{_idx}", use_container_width=True):
                st.session_state["_admin_open_agr"] = r["aid"]
                st.rerun()


def _panel_agrupaciones(grupo: str):
    ags = P.list_groupings(grupo=grupo)
    todos = P.list_projects(grupo=grupo)
    nom_ags = {a["ID"]: a["Nombre"] for a in ags}

    # ── Agrupación ABIERTA (de una tarjeta) → tablero + gestión, sin anidar ──
    _open = st.session_state.get("_admin_open_agr")
    if _open:
        _ag = next((a for a in ags if str(a.get("ID", "")) == str(_open)), None)
        if st.button("← Volver a las agrupaciones", key="agr_back"):
            st.session_state.pop("_admin_open_agr", None)
            st.rerun()
        if not _ag:
            st.warning("Agrupación no encontrada.")
            st.session_state.pop("_admin_open_agr", None)
            return
        _dashboard_agrupacion(_ag, grupo)      # sin expanders internos → seguro
        st.markdown("---")
        with st.expander(":material/build: Proyectos de esta agrupación"):
            st.caption("Marca los elevadores que la componen. Al quitar uno se "
                       "**desagrupa**, no se borra.")
            _act = {str(p.get("ID")): P._num(p.get("PesoEnAgrupacion")) or 1.0
                    for p in P.list_projects(grupo=grupo, agrupacion_id=_ag["ID"])}
            _sel = _miembros_editor(nom_ags, todos, f"agmem_{_ag['ID']}", _act)
            if len(_sel) > 12:
                st.warning(f"{len(_sel)} proyectos: cada cambio es una escritura "
                           "en la hoja; puede tardar unos segundos.")
            if st.button(":material/save: Guardar los proyectos de la agrupación",
                         key=f"agmemsave_{_ag['ID']}", use_container_width=True):
                with st.spinner("Guardando..."):
                    ok, msg = P.set_grouping_members(_ag["ID"], _sel, grupo)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()
        with st.expander(":material/delete: Eliminar agrupación"):
            st.caption("Los proyectos no se borran; solo se desagrupan.")
            _ok_del = ui.confirmar_borrado("del_agr_ok", "Confirmo eliminar esta agrupación")
            if st.button("Eliminar agrupación", disabled=not _ok_del, key="del_agr_btn"):
                ok, msg = P.delete_grouping(_ag["ID"])
                (st.success if ok else st.error)(msg)
                if ok:
                    st.session_state.pop("_admin_open_agr", None)
                    st.rerun()
        return

    # ── Lista de agrupaciones CLICKEABLES ──
    if ags:
        st.markdown(f"**Agrupaciones — {len(ags)}**")
        st.caption("Toca una agrupación para abrir su tablero.")
        _cartera_agrupaciones(ags, grupo)
    else:
        st.info("No hay agrupaciones. Crea una abajo y elige qué elevadores la componen.")

    # ── Crear: la agrupación se arma CON sus proyectos (v141), plegada ──
    with st.expander("Nueva agrupación", icon=":material/create_new_folder:"):
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


# ── Panel del PROPIETARIO: todos los proyectos (todos los grupos) ──
def render_owner_projects():
    st.markdown("### :material/folder: Todos los proyectos")
    if not P.is_configured():
        st.warning("La gestión de proyectos necesita Google Sheets configurado.")
        return
    _ver_arch = st.checkbox(":material/archive: Ver también los archivados", key="ver_arch_owner")
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
            st.info("Aún no hay grupos. Crea uno en **:material/business: Grupos** para poder "
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
            "Alertas":     f"{_na}" if _na else "",
            "Cliente":   p.get("Cliente"),
            "Ubicación": ubic,
            "Mapa":        maps.maps_url(ubic),
            "Estado":    est,
            "Retraso": f"{_d:.0f} d" if _d else "",
            "Adelanto": f"{_ad:.0f} d" if _ad else "",
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
                + (f"  ·  :red[:material/cancel:] {len(delays)} con retraso" if delays else "")
                + (f"  ·  :green[:material/check_circle:] {len(aheads)} adelantado(s)" if aheads else ""))
    st.markdown(_portfolio_html(proys, _hb, alarmas, ags, delays, aheads, show_group=True),
                unsafe_allow_html=True)

    with st.expander(":material/assignment: Ver tabla detallada"):
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                     column_config={"Mapa": st.column_config.LinkColumn("Mapa", display_text="Abrir")})

    st.markdown("#### :material/search: Abrir proyecto")
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
    if st.button(":material/save: Guardar avances", key=f"fldsave_{pid}", use_container_width=True):
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
    st.markdown("### :material/assignment: Mis proyectos")
    if not P.is_configured():
        st.warning("La gestión de proyectos necesita Google Sheets configurado.")
        return

    # ── Planificación de la semana (el campo ve toda la cuadrilla) ──
    try:
        from core import roster, roster_ui
        if roster.is_configured():
            _aa = roster.asignaciones_dia(grupo, usuario)   # v274/v277: varias, con franja
            if _aa:
                _parts = []
                for a in _aa:
                    if not a.get("etiqueta"):
                        continue
                    _fl = roster.franja_label(a.get("ini", ""), a.get("fin", ""))
                    _parts.append(a["etiqueta"] + (f" {_fl}" if _fl else ""))
                _ets = " · ".join(_parts)
                _nt = next((a["nota"] for a in _aa if str(a.get("nota", "")).strip()), "")
                _n = f" · {_nt}" if _nt else ""
                _est = all(a.get("es_estado") for a in _aa)
                (st.info if _est else st.success)(
                    f":material/calendar_month: **Hoy:** {_ets}{_n}")
            with st.expander(":material/calendar_month: Ver la planificación de la semana (toda la cuadrilla)"):
                roster_ui.render_board_readonly(grupo, resaltar_usuario=usuario)
    except Exception:
        pass

    # ── Mi ruta del día (v270): mis obras en el mapa, ordenadas para ir a terreno ──
    with st.expander(":material/route: Mi ruta (mis obras en el mapa)"):
        try:
            from core import route_ui
            route_ui.render_mi_ruta(usuario, grupo)
        except Exception:
            st.caption("No se pudo cargar la ruta ahora mismo.")

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
                   "Si fichas en :material/schedule: Fichaje, se abre solo.")
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
    tarj = [_kpi_card("Estado", est),
            _kpi_card("Avance del proyecto", f"{avance:.0f}%"),
            _kpi_card("Cliente", prj.get("Cliente") or "—")]
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px">'
                + "".join(tarj) + "</div>", unsafe_allow_html=True)
    st.progress(min(1.0, avance / 100.0))
    if _ub:
        st.caption(":material/place: " + maps.maps_link_md(_ub, _ub))

    # ── Sub-navegación (radio, NO st.tabs — regla v56; como el detalle del admin) ──
    _sec = st.radio("Sección", ["🏗 Avance", "🚨 Avisos", "💰 Recibos", "📎 Archivos"],
                    format_func=lambda o: {"🏗 Avance": ":material/trending_up: Avance",
                                           "🚨 Avisos": ":material/report: Avisos",
                                           "💰 Recibos": ":material/receipt: Recibos",
                                           "📎 Archivos": ":material/folder: Archivos"}.get(o, o),
                    horizontal=True, key="fld_sec", label_visibility="collapsed")
    st.markdown("---")
    if _sec == "🏗 Avance":
        _induccion_section(pid, prj, grupo, allow_send=False)
        _field_activities(pid)
    elif _sec == "🚨 Avisos":
        _alerts_section(pid, grupo, prj.get("Nombre", ""), allow_report=True)
    elif _sec == "💰 Recibos":
        render_expenses(pid, grupo, can_delete=False, key_prefix="fld")
    else:   # :material/attach_file: Archivos
        _archivos_section(pid)


# ── Gastos / compras por proyecto (admin, campo) ──
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


def _torta_html(pares, total) -> str:
    """Diagrama de torta (pie) con CSS `conic-gradient` + leyenda (color · rubro · $ · %).
    Sin dependencias de charting (nada de plotly/matplotlib): mismo enfoque HTML que
    `_barras_html`, se renderiza en `st.markdown`. Para el gasto por rubro del grupo
    (mano de obra + cada categoría de compra). v224."""
    pares = [(k, float(v)) for k, v in pares if v and float(v) > 0]
    if not pares or total <= 0:
        return ""
    _pal = ["#2e6da4", "#BA7517", "#1e8449", "#8e44ad", "#c0392b", "#16a085",
            "#e67e22", "#2980b9", "#d4537e", "#7f8c8d", "#f1c40f", "#34495e"]
    _stops, _leg, _acc = [], [], 0.0
    for _i, (et, val) in enumerate(pares):
        _pct = 100.0 * val / total
        _col = _pal[_i % len(_pal)]
        _stops.append(f"{_col} {_acc:.2f}% {_acc + _pct:.2f}%")
        _acc += _pct
        _leg.append(
            '<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">'
            f'<span style="width:12px;height:12px;border-radius:3px;background:{_col};'
            'flex:none;"></span>'
            f'<span style="flex:1;font-size:12.5px;color:#374151;overflow:hidden;'
            f'text-overflow:ellipsis;white-space:nowrap;">{et}</span>'
            f'<span style="font-size:12.5px;font-weight:600;color:#1f2937;">${val:,.0f}</span>'
            f'<span style="width:40px;flex:none;text-align:right;font-size:11.5px;'
            f'color:#9aa7b8;">{_pct:.0f}%</span></div>')
    _grad = "conic-gradient(" + ", ".join(_stops) + ")"
    # v225: centrado — se agrupan torta + leyenda y la leyenda se ACOTA (antes flex:1
    # la estiraba a todo el ancho y el monto/% se iban al borde → "todo separado").
    return (
        '<div style="display:flex;align-items:center;justify-content:center;gap:32px;'
        'flex-wrap:wrap;margin-top:4px;">'
        f'<div style="width:150px;height:150px;border-radius:50%;background:{_grad};'
        'flex:none;"></div>'
        f'<div style="width:300px;max-width:100%;">{"".join(_leg)}</div></div>')


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
              "contra qué comparar el gasto. Se define en :material/edit: Datos.")
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
        st.caption(_l + ("  :red[:material/block:] SOBRE PRESUPUESTO" if cp["over"] else ""))

    # ── Reparto del costo | Compras por categoría (doble columna, v213) ──
    _rep = cp["total"] > 0
    _cat = gastos.get("por_categoria") or {}

    def _blq_reparto():
        st.markdown("**Reparto del costo**")
        st.markdown(_barras_html([("Mano de obra", cp["mano_obra"]),
                                  ("Compras", cp["compras"])], cp["total"]),
                    unsafe_allow_html=True)

    def _blq_categorias():
        st.markdown("**Compras por categoría**")
        st.markdown(_barras_html(sorted(_cat.items(), key=lambda x: -x[1]),
                                 gastos["total"], "#BA7517"), unsafe_allow_html=True)

    if _rep and _cat:
        _bc1, _bc2 = st.columns(2, gap="large")
        with _bc1:
            _blq_reparto()
        with _bc2:
            _blq_categorias()
    elif _rep:
        _blq_reparto()
    elif _cat:
        _blq_categorias()

    # ── Mano de obra por persona: labor_cost solo daba el total ──
    if lb["items"]:
        st.markdown("**Mano de obra por persona**")
        st.dataframe(pd.DataFrame([{
            "Usuario": x["usuario"], "Horas": x["horas"],
            "Tarifa/h": x["tarifa"], "Costo": x["costo"],
        } for x in lb["items"]]), hide_index=True, use_container_width=True)
        if lb["sin_tarifa"]:
            st.warning(":material/warning: Sin tarifa/hora, así que sus horas suman **$0** al costo: **"
                       + ", ".join(lb["sin_tarifa"]) + "**. Se fija en :material/build: Usuarios.")

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
    with st.expander("Cargar recibo", icon=":material/receipt:"):
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
        # v213: recibos ACTIVOS — tocar uno muestra su foto inline (antes: tabla
        # redundante + botones de solo-descarga).
        with st.expander(f":material/receipt_long: Recibos ({len(items)})"):
            st.caption("Toca un recibo para ver la foto.")
            for r in items:
                _rid = str(r.get("ID", ""))
                _did = str(r.get("DriveID", "")).strip()
                _lbl = f":material/receipt_long: {r.get('Fecha')} · {r.get('Categoria')} · ${E._num(r.get('Valor')):,.0f}"
                _ex = " · ".join(x for x in [str(r.get('Proveedor') or ''),
                                             str(r.get('Descripcion') or '')] if x)
                if _ex:
                    _lbl += f" · {_ex}"
                cc = st.columns([6, 1])
                if _did:
                    if cc[0].button(_lbl, key=f"{key_prefix}_open_{_rid}",
                                    use_container_width=True):
                        _cur = st.session_state.get(f"{key_prefix}_rcb")
                        st.session_state[f"{key_prefix}_rcb"] = None if _cur == _rid else _rid
                        st.rerun()
                else:
                    cc[0].caption(_lbl + " · sin archivo")
                if can_delete and cc[1].button(":material/delete:", key=f"{key_prefix}_del_{_rid}"):
                    ok, msg = E.delete(r.get("ID"))
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.session_state.pop(f"{key_prefix}_rcb", None)
                        st.rerun()

            # ── Recibo abierto: foto inline (imagen) o descarga (PDF) ──
            _sel = st.session_state.get(f"{key_prefix}_rcb")
            _ro = next((x for x in items if str(x.get("ID")) == str(_sel)), None) if _sel else None
            if _ro and str(_ro.get("DriveID", "")).strip():
                _arch = str(_ro.get("Archivo", "recibo"))
                try:
                    from core import drive_store
                    _data = drive_store.download(str(_ro.get("DriveID", "")).strip())
                    if _arch.lower().endswith((".png", ".jpg", ".jpeg")):
                        st.image(_data, caption=_arch, use_container_width=True)
                    else:
                        st.info(f":material/description: {_arch} — es un PDF; descárgalo para verlo.")
                    st.download_button(":material/download: Descargar recibo", data=_data, file_name=_arch,
                                       key=f"{key_prefix}_dlrcb_{_sel}")
                except Exception:
                    st.caption("No se pudo cargar el archivo del recibo.")


# ── Reporte del ADMIN: gastos de todos los proyectos del grupo ──
def render_pnl(grupo: str):
    """Resumen financiero del grupo (Fase 4): ingresos − costos = ganancia + cuentas.

    Lo REALMENTE facturado (facturas) menos los costos (nóminas + compras). La
    sub-pestaña «Rentabilidad» es la estimación por margen; esto es lo ejecutado.
    """
    from core import finance as F
    st.markdown("#### :material/insights: Resumen financiero (P&L)")
    st.caption("Lo realmente facturado menos los costos (nóminas + compras) = ganancia. "
               "«Rentabilidad» es la estimación por margen; esto es lo ejecutado.")
    d = F.pnl(grupo)
    if d["facturado"] == 0 and d["costo_total"] == 0:
        st.info(":material/info: Aún no hay facturas ni costos (nóminas/compras) registrados.")
        return
    c = st.columns(3)
    c[0].metric("Ingresos (facturado)", f"${d['facturado']:,.0f}")
    c[1].metric("Costos", f"${d['costo_total']:,.0f}")
    c[2].metric("Ganancia", f"${d['ganancia']:,.0f}",
                delta=(f"{(100 * d['ganancia'] / d['facturado']):.0f}% margen"
                       if d["facturado"] > 0 else None))
    st.markdown("---")
    a, b = st.columns(2)
    with a:
        st.markdown("**:material/trending_up: Ingresos (cuentas por cobrar)**")
        st.markdown(f"- Facturado: **${d['facturado']:,.2f}**")
        st.markdown(f"- Cobrado: **${d['cobrado']:,.2f}**")
        _pc = f"- Por cobrar: **${d['por_cobrar']:,.2f}**"
        if d["vencido"] > 0:
            _pc += f"  ·  :red[vencido ${d['vencido']:,.0f}]"
        st.markdown(_pc)
    with b:
        st.markdown("**:material/trending_down: Costos (cuentas por pagar)**")
        st.markdown(f"- Nóminas (sueldos + super): **${d['costo_nomina']:,.2f}**")
        st.markdown(f"- Compras / materiales: **${d['compras']:,.2f}**")
        st.markdown(f"- Por pagar (nóminas): **${d['por_pagar']:,.2f}**  ·  pagado ${d['pagado']:,.0f}")


def render_group_profitability(grupo: str):
    """Rentabilidad del grupo (Fase 1 finanzas): costo vs ingreso estimado = ganancia.

    Estimación de facturación total (MO × (1+margen) + materiales a costo). Las
    facturas reales (con cobrado/pendiente) llegan en la Fase 2.
    """
    from core import finance as F
    st.markdown("#### :material/trending_up: Rentabilidad del grupo")
    st.caption("Lo que costó cada proyecto (mano de obra + materiales) frente a lo que "
               "cobrarías (MO × (1 + margen) + materiales) = tu ganancia estimada. El margen sale "
               "de cada proyecto (o del default del grupo); se cambia en ✏️ Datos del proyecto.")
    data = F.group_profitability(grupo)
    if not data["rows"]:
        st.info(":material/info: Aún no hay proyectos con costo registrado (horas o compras).")
        return
    t = data["totales"]
    c = st.columns(3)
    c[0].metric("Costo total", f"${t['costo']:,.0f}")
    c[1].metric("Ingreso estimado", f"${t['ingreso']:,.0f}")
    c[2].metric("Ganancia estimada", f"${t['ganancia']:,.0f}")
    df = pd.DataFrame([{
        "Proyecto":         r["nombre"],
        "Costo":            round(r["costo"], 0),
        "Margen":           int(round(r["margen"])),
        "Ingreso estimado": round(r["ingreso"], 0),
        "Ganancia":         round(r["ganancia"], 0),
    } for r in sorted(data["rows"], key=lambda x: -x["ganancia"])])
    st.dataframe(df, use_container_width=True, hide_index=True, column_config={
        "Costo":            st.column_config.NumberColumn("Costo", format="$%d"),
        "Margen":           st.column_config.NumberColumn("Margen", format="%d%%"),
        "Ingreso estimado": st.column_config.NumberColumn("Ingreso estimado", format="$%d"),
        "Ganancia":         st.column_config.NumberColumn("Ganancia", format="$%d"),
    })


def render_group_expenses(grupo: str):
    from core import expenses as E
    st.markdown("#### :material/payments: Gastos del grupo")
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
        st.error(f":material/block: **{n_over} proyecto(s) ya sobre presupuesto:** "
                 + ", ".join(f["nombre"] for f in filas if f["over"]))
    if n_over_p:
        st.warning(f":material/warning: **{n_over_p} más se saldrá(n) al ritmo actual** (aún dentro hoy): "
                   + ", ".join(f["nombre"] for f in filas if f["over_proj"] and not f["over"]))

    # ── Reparto del costo | Compras por categoría (doble columna, v215) ──
    _catg = ge["por_categoria"]

    def _blq_reparto_g():
        st.markdown("**Reparto del costo del grupo**")
        st.markdown(_barras_html(
            [("Mano de obra", sum(f["mano_obra"] for f in filas)),
             ("Compras", sum(f["compras"] for f in filas))], tot),
            unsafe_allow_html=True)

    def _blq_categorias_g():
        st.markdown("**Compras por categoría**")
        _c = sorted(_catg.items(), key=lambda x: -x[1])
        st.markdown(_barras_html(_c, sum(v for _, v in _c), "#BA7517"),
                    unsafe_allow_html=True)

    if tot > 0 and _catg:
        _gc1, _gc2 = st.columns(2, gap="large")
        with _gc1:
            _blq_reparto_g()
        with _gc2:
            _blq_categorias_g()
    elif tot > 0:
        _blq_reparto_g()
    elif _catg:
        _blq_categorias_g()

    # ── Torta: gasto por rubro (Mano de obra + categorías) a ancho completo (v224) ──
    _rubros = [("Mano de obra", sum(f["mano_obra"] for f in filas))]
    _rubros += sorted(_catg.items(), key=lambda x: -x[1])
    _rubros = [(k, v) for k, v in _rubros if v and v > 0]
    if _rubros:
        st.markdown("**Gasto por rubro**")
        st.markdown(_torta_html(_rubros, sum(v for _, v in _rubros)),
                    unsafe_allow_html=True)

    # ── Proyectos CON presupuesto (tabla CLICKEABLE → abre el proyecto, v215) ──
    if con_pres:
        st.markdown("**Proyectos con presupuesto**")
        _gev = st.dataframe(pd.DataFrame([{
            "Proyecto": f["nombre"], "Costo": f["total"], "Presupuesto": f["presupuesto"],
            "% consumido": f["pct"], "Avance %": f["avance"],
            "Proyección": f["proyectado"] if f["proyectado"] is not None else "—",
            "": ("sobre" if f["over"] else ("riesgo" if f["over_proj"] else "ok")),
        } for f in con_pres]), hide_index=True, use_container_width=True,
            on_select="rerun", selection_mode="single-row", key="ge_tbl")
        st.caption(":material/touch_app: Toca una fila y «Abrir» para ir a ese proyecto. **Proyección** = costo al "
                   "terminar al ritmo actual. sobre = ya se pasó · riesgo = se pasará · ok = dentro.")
        try:
            _grows = list(_gev.selection.rows)
        except Exception:
            _grows = []
        if _grows and _grows[0] < len(con_pres):
            _gf = con_pres[_grows[0]]
            if st.button(f"→ Abrir {_gf['nombre']}", key="ge_open", type="primary"):
                st.session_state["_prjsel_pending"] = str(_gf.get("id", ""))
                _ir_a("proyectos", "📊 Proyectos")

    # ── Proyectos SIN presupuesto: solo costo, y aviso ──
    if sin_pres:
        st.markdown("**Proyectos sin presupuesto asignado**")
        st.dataframe(pd.DataFrame([{
            "Proyecto": f["nombre"], "Compras": f["compras"],
            "Mano de obra": f["mano_obra"], "Costo total": f["total"],
        } for f in sin_pres]), hide_index=True, use_container_width=True)
        st.caption(f"{len(sin_pres)} proyecto(s) sin presupuesto: no hay contra qué comparar "
                   "su gasto. Se define en el detalle del proyecto → :material/edit: Datos.")

    # (Compras por categoría se muestra arriba, en doble columna con el reparto — v215.)

    # ── Export para contabilidad ──
    _csv = pd.DataFrame([{
        "Proyecto": f["nombre"], "Compras": f["compras"], "Mano de obra": f["mano_obra"],
        "Costo total": f["total"], "Presupuesto": f["presupuesto"],
        "% consumido": f["pct"], "Avance %": f["avance"], "Proyeccion": f["proyectado"],
    } for f in filas])
    st.download_button(":material/download: Exportar CSV (contabilidad)",
                       data=_csv.to_csv(index=False).encode("utf-8"),
                       file_name=f"gastos_{grupo}.csv", mime="text/csv", key="ge_csv")


# ── Reporte del ADMIN: horas de TODOS los usuarios del grupo ──
def render_group_hours(grupo: str):
    from datetime import datetime
    from core import timeclock
    st.markdown("#### :material/schedule: Horas del grupo")
    if not timeclock.is_configured():
        st.warning("El fichaje necesita Google Sheets configurado.")
        return

    per = st.radio("Periodo", ["Hoy", "Semana", "Mes", "Todo"], horizontal=True,
                   key="gh_per", label_visibility="collapsed")
    now = clock.now()
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
    # ⚠️ Dos logins distintos pueden compartir Nombre: sin el Login se volverian
    # indistinguibles. Se añade el login SOLO a los que colisionan, no a todos.
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
    # v215: tabla CLICKEABLE → abre la ficha de la persona (Planificación · Usuarios).
    _hev = st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True,
                        on_select="rerun", selection_mode="single-row", key="gh_tbl")
    st.caption(":material/touch_app: Toca una persona y «Abrir ficha» para gestionarla.")
    try:
        _hrows = list(_hev.selection.rows)
    except Exception:
        _hrows = []
    if _hrows and _hrows[0] < len(data):
        _hd = data[_hrows[0]]
        _hn = _hd.get("nombre") or _hd["usuario"]
        if st.button(f"→ Abrir ficha de {_hn}", key="gh_open", type="primary"):
            st.session_state["gp_fichasel"] = f"{_hn} ({_hd['usuario']})"
            _ir_a("planificacion", "👷 Usuarios")

    if _dudoso:
        st.caption("«—» en *sin asignar*: esa persona imputó a proyectos más horas que las "
                   "de su jornada, así que el dato no es fiable (fichó al proyecto sin abrir "
                   "jornada). Se corrige a partir de v150; el histórico anterior queda así.")
    _sin_tar = [_etiqueta(d) for d in data
                if d["proyecto"] > 0 and not d["tarifa"]]
    if _sin_tar:
        st.warning(":material/warning: Sin **tarifa/hora**, así que su costo sale $0: **"
                   + ", ".join(_sin_tar) + "**. Se fija en :material/build: Usuarios.")

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

    # ── Horas por PERSONA y PROYECTO (v216) ──────────────────────────────────
    # Responde "¿cuántas horas gastó cada usuario en cada proyecto?". El dato ya
    # lo trae group_hours en por_proyecto; aquí se muestra como matriz.
    _proys = sorted({p for d in data for p in d["por_proyecto"]})
    if _proys:
        st.divider()
        st.markdown("**:material/search: Horas por persona y proyecto**")
        _mat = []
        for d in data:
            _pp = d["por_proyecto"]
            if not _pp:
                continue
            _fila = {"Persona": _etiqueta(d)}
            for _p in _proys:
                _h = _pp.get(_p, 0.0)
                _fila[_p] = round(_h, 2) if _h else ""
            _mat.append(_fila)
        if _mat:
            st.dataframe(pd.DataFrame(_mat), use_container_width=True, hide_index=True)
            st.caption("Cada celda: horas que esa persona imputó a ese proyecto en el periodo. "
                       "Las columnas son los proyectos.")
