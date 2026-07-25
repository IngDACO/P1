"""
Tablero semanal de asignación de cuadrilla — UI del admin (v159).

Sección 📅 Planificación en 🛠 Mi grupo: la rejilla persona×día coloreada (como
el board del usuario), edición de la semana persona a persona, "copiar la semana
anterior" y el catálogo de trabajos.
"""
from datetime import timedelta

import streamlit as st

from core import roster as R
from core import auth
from core import projects as P
from core import ui_common as ui


def _staff(grupo):
    """Personal de campo del grupo que va al tablero."""
    try:
        return [u for u in auth.list_users(grupo=grupo)
                if str(u.get("Rol", "")).lower() == "campo"]
    except Exception:
        return []


def _texto_sobre(hex_color) -> str:
    """Negro o blanco según la luminancia del fondo, para que el texto se lea."""
    try:
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return "#1f2937" if lum > 0.6 else "#ffffff"
    except Exception:
        return "#1f2937"


def _semana_activa() -> "date":
    """Lunes de la semana que se está viendo (en session_state)."""
    k = "ros_lunes"
    if k not in st.session_state:
        st.session_state[k] = R.lunes_de().isoformat()
    from datetime import date as _d
    y, m, dd = str(st.session_state[k]).split("-")
    return _d(int(y), int(m), int(dd))


def render_planificacion(grupo):
    st.markdown("#### 📅 Planificación de la semana")
    if not R.is_configured():
        st.warning("La planificación necesita Google Sheets configurado.")
        return

    staff = _staff(grupo)
    if not staff:
        st.info("Aún no tienes personal de campo. Créalo en 🔧 Usuarios de campo.")
        return

    lunes = _semana_activa()
    tidx  = R.trabajos_idx(grupo)
    datos = R.get_semana(grupo, lunes)

    # ── Navegación de semana ──
    n1, n2, n3, n4 = st.columns([1, 3, 1, 2])
    if n1.button("◀", key="ros_prev", use_container_width=True):
        st.session_state["ros_lunes"] = (lunes - timedelta(days=7)).isoformat()
        st.rerun()
    n2.markdown(f"<div style='text-align:center;font-weight:700;font-size:1.05rem;"
                f"padding-top:6px'>{R.rango_label(lunes)}</div>", unsafe_allow_html=True)
    if n3.button("▶", key="ros_next", use_container_width=True):
        st.session_state["ros_lunes"] = (lunes + timedelta(days=7)).isoformat()
        st.rerun()
    if n4.button("📋 Copiar semana anterior", key="ros_copy", use_container_width=True):
        ok, msg = R.copiar_semana(grupo, lunes - timedelta(days=7), lunes)
        (st.success if ok else st.warning)(msg)
        if ok:
            st.rerun()

    # ── Rejilla coloreada (el board) ──
    st.markdown(_grid_html(staff, lunes, datos, tidx), unsafe_allow_html=True)

    # ── Ir a un proyecto del tablero ──
    _ir_a_proyecto(grupo, staff, tidx, datos)

    # ── Editar la semana de una persona ──
    st.markdown("##### ✏️ Editar la semana de una persona")
    _nombre = {u["Usuario"]: (u.get("Nombre") or u["Usuario"]) for u in staff}
    _pers = ui.elegir("Persona", {f"{v} ({k})": k for k, v in _nombre.items()},
                      key="ros_editpers", vacio="— elige a quién asignar —")
    if _pers:
        _editar_persona(grupo, lunes, _pers, _nombre.get(_pers, _pers), tidx)

    # ── Plan vs real ──
    _plan_vs_real(grupo, lunes, staff, tidx)

    # ── Catálogo de trabajos ──
    _catalogo(grupo)


def _ir_a_proyecto(grupo, staff, tidx, datos):
    """Botones para saltar al detalle de un proyecto que aparece en la semana.

    El board es HTML (celdas coloreadas), así que no se puede hacer la celda
    clicable como un `st.dataframe`; en su lugar se ofrece un botón por cada
    proyecto DISTINTO enlazado en la semana visible. Navega con el patrón
    `_prjsel_pending` (v126) + cambiar la sección del grupo a 📊 Proyectos
    (`_gruposec_pending`, aplicado antes del radio en `render_group_panel`).
    """
    pids = []
    for u in staff:
        for d in R.DIAS:
            asig = str(R.celda(datos, u["Usuario"], d).get("asig", ""))
            pid = R.proyecto_de(asig, tidx)
            if pid and pid not in pids:
                pids.append(pid)
    if not pids:
        return
    # Solo los navegables: existen y no están archivados (list_projects los oculta).
    nombres = {str(p.get("ID")): str(p.get("Nombre") or p.get("ID"))
               for p in P.list_projects(grupo=grupo)}
    items = sorted(((pid, nombres[pid]) for pid in pids if pid in nombres),
                   key=lambda x: x[1].lower())
    if not items:
        return
    st.markdown("##### 🔗 Ir a un proyecto del tablero")
    st.caption("Abre el detalle del proyecto sin salir de la cuadrilla.")
    for fila in range(0, len(items), 3):
        cols = st.columns(3)
        for c, (pid, nom) in zip(cols, items[fila:fila + 3]):
            if c.button(f"🔗 {nom}", key=f"ros_go_{pid}", use_container_width=True):
                st.session_state["_prjsel_pending"] = pid
                st.session_state["_gruposec_pending"] = "📊 Proyectos"
                st.rerun()


def _plan_vs_real(grupo, lunes, staff, tidx):
    """Compara la asignacion del dia (si enlaza a PRJ) contra donde ficho cada uno.

    Solo tiene sentido para trabajos enlazados a un proyecto: un delivery o un
    estado (OFF/Leave) no tiene fichaje contra que comparar. Decision de v161.
    """
    from datetime import date as _date
    from core import timeclock
    with st.expander("🔍 Plan vs real (lo asignado contra lo fichado)"):
        if not timeclock.is_configured():
            st.caption("Necesita el fichaje configurado.")
            return
        # Día a comparar: hoy si cae en la semana vista, si no el lunes.
        hoy = _date.today()
        _idx_def = (hoy - lunes).days if 0 <= (hoy - lunes).days <= 4 else 0
        _dsel = st.radio("Día", R.DIAS, index=_idx_def, horizontal=True,
                         format_func=lambda d: f"{R.DIAS_LABEL[d]} "
                         f"{R.fecha_de_dia(lunes, d).strftime('%d/%m')}",
                         key="pvr_dia", label_visibility="collapsed")
        fecha = R.fecha_de_dia(lunes, _dsel)
        datos = R.get_semana(grupo, lunes)
        real  = timeclock.proyectos_por_usuario_dia(grupo, fecha)

        n_ok = n_desvio = n_sin = 0
        filas = []
        for u in staff:
            usr = u["Usuario"]
            nom = u.get("Nombre") or usr
            c = R.celda(datos, usr, _dsel)
            asig = str(c.get("asig", ""))
            plan_pid = R.proyecto_de(asig, tidx)
            es_estado = asig in R.ESTADOS
            reales = real.get(usr, [])
            real_pids = {e["pid"] for e in reales if e["pid"]}
            real_txt = ", ".join(e["nombre"] for e in reales) or "—"

            if es_estado:
                if reales:
                    filas.append(("ℹ️", nom, f"marcado {R.etiqueta_de(asig, tidx)} "
                                  f"pero fichó en {real_txt}"))
                # OFF/Leave sin fichar: correcto, no se lista
            elif plan_pid:
                if plan_pid in real_pids:
                    n_ok += 1
                    filas.append(("🟢", nom, f"{R.etiqueta_de(asig, tidx)} — fichó donde tocaba"))
                elif real_pids:
                    n_desvio += 1
                    filas.append(("🔴", nom, f"asignado a {R.etiqueta_de(asig, tidx)} · "
                                  f"fichó en {real_txt}"))
                else:
                    n_sin += 1
                    filas.append(("⚠️", nom, f"asignado a {R.etiqueta_de(asig, tidx)} · "
                                  "sin fichar aún"))
            elif asig:                                  # trabajo sin enlace a PRJ
                filas.append(("—", nom, f"{R.etiqueta_de(asig, tidx)} "
                              "(sin proyecto que comparar)"
                              + (f" · fichó en {real_txt}" if reales else "")))
            elif reales:                                # sin plan pero ficho
                filas.append(("❔", nom, f"sin asignación · fichó en {real_txt}"))

        st.markdown(f"`🟢 {n_ok} donde tocaba`  `🔴 {n_desvio} en otro sitio`  "
                    f"`⚠️ {n_sin} sin fichar`")
        if not filas:
            st.caption("Nada que comparar este día (sin asignaciones a proyecto ni fichajes).")
        for ic, nom, txt in filas:
            st.markdown(f"{ic}  **{_esc(nom)}** — {_esc(txt)}")


def render_board_readonly(grupo, resaltar_usuario=""):
    """Tablero de la semana en SOLO LECTURA (para el campo: ve toda la cuadrilla).

    Decisión del usuario: el campo ve el board completo para saber con quién va a
    cada obra. Resalta su propia fila.
    """
    if not R.is_configured():
        return
    staff = _staff(grupo)
    if not staff:
        return
    lunes = _semana_activa()
    tidx  = R.trabajos_idx(grupo)
    datos = R.get_semana(grupo, lunes)

    c1, c2, c3 = st.columns([1, 3, 1])
    if c1.button("◀", key="rosf_prev", use_container_width=True):
        st.session_state["ros_lunes"] = (lunes - timedelta(days=7)).isoformat()
        st.rerun()
    c2.markdown(f"<div style='text-align:center;font-weight:700;padding-top:6px'>"
                f"{R.rango_label(lunes)}</div>", unsafe_allow_html=True)
    if c3.button("▶", key="rosf_next", use_container_width=True):
        st.session_state["ros_lunes"] = (lunes + timedelta(days=7)).isoformat()
        st.rerun()
    st.markdown(_grid_html(staff, lunes, datos, tidx, resaltar_usuario),
                unsafe_allow_html=True)


def _grid_html(staff, lunes, datos, tidx, resaltar="") -> str:
    ths = ['<th style="text-align:left;padding:6px 8px;font-size:12px;color:#6b7280;'
           'position:sticky;left:0;background:#fff;">Persona</th>']
    for d in R.DIAS:
        f = R.fecha_de_dia(lunes, d)
        ths.append(f'<th style="padding:6px 8px;font-size:12px;color:#6b7280;'
                   f'min-width:120px;">{R.DIAS_LABEL[d]} {f.strftime("%d/%m")}</th>')
    filas = []
    for u in staff:
        usr = u["Usuario"]
        nom = u.get("Nombre") or usr
        _mio = (str(usr) == str(resaltar))
        _nbg = "#fff7e6" if _mio else "#fff"
        celdas = [f'<td style="padding:5px 8px;font-size:13px;font-weight:{"800" if _mio else "600"};'
                  f'color:#1f2937;white-space:nowrap;position:sticky;left:0;background:{_nbg};'
                  f'border-right:1px solid #eef1f5;">{"👉 " if _mio else ""}{_esc(nom)}</td>']
        for d in R.DIAS:
            c = R.celda(datos, usr, d)
            asig = str(c.get("asig", ""))
            nota = str(c.get("nota", ""))
            bg   = R.color_de(asig, tidx)
            fg   = _texto_sobre(bg) if asig else "#9aa7b8"
            et   = R.etiqueta_de(asig, tidx)
            cont = (f'<div style="font-weight:600;">{_esc(et)}</div>' if et else "")
            if nota:
                cont += f'<div style="font-size:10.5px;opacity:0.85;">{_esc(nota)}</div>'
            celdas.append(f'<td style="padding:5px 7px;background:{bg};color:{fg};'
                          f'border-radius:6px;font-size:11.5px;line-height:1.25;'
                          f'vertical-align:top;">{cont or "&nbsp;"}</td>')
        filas.append("<tr>" + "".join(celdas) + "</tr>")
    return ('<div style="overflow-x:auto;margin:10px 0;">'
            '<table style="border-collapse:separate;border-spacing:3px;width:100%;">'
            "<thead><tr>" + "".join(ths) + "</tr></thead>"
            "<tbody>" + "".join(filas) + "</tbody></table></div>")


def _opciones(grupo, tidx):
    """[(etiqueta, valor)] para el selector de asignación: neutro + estados + trabajos."""
    op = [("— sin asignar —", "")]
    for k, v in R.ESTADOS.items():
        op.append((f"🟥 {v['nombre']}" if k != "OFF" else f"⬜ {v['nombre']}", k))
    for r in R.list_trabajos(grupo):
        num = str(r.get("Numero", "")).strip()
        op.append((f"{num}. {r.get('Nombre','')}" if num else str(r.get("Nombre", "")),
                   str(r.get("ID", ""))))
    return op


def _editar_persona(grupo, lunes, usuario, nombre, tidx):
    op = _opciones(grupo, tidx)
    etiquetas = [e for e, _ in op]
    valores   = [v for _, v in op]
    datos = R.get_semana(grupo, lunes)
    dias_out = {}
    st.caption(f"Semana de **{nombre}** · {R.rango_label(lunes)}")
    for d in R.DIAS:
        c = R.celda(datos, usuario, d)
        cur = str(c.get("asig", ""))
        idx = valores.index(cur) if cur in valores else 0
        f = R.fecha_de_dia(lunes, d)
        cc = st.columns([1.2, 3, 3])
        cc[0].markdown(f"<div style='padding-top:8px;font-weight:600'>{R.DIAS_LABEL[d]} "
                       f"<span style='color:#9aa7b8;font-weight:400'>{f.strftime('%d/%m')}</span></div>",
                       unsafe_allow_html=True)
        sel = cc[1].selectbox("asig", etiquetas, index=idx,
                              key=f"ros_{usuario}_{lunes}_{d}_a", label_visibility="collapsed")
        nota = cc[2].text_input("nota", value=str(c.get("nota", "")),
                                key=f"ros_{usuario}_{lunes}_{d}_n",
                                label_visibility="collapsed",
                                placeholder="Nota: vehículo, equipo, horario…")
        dias_out[d] = {"asig": valores[etiquetas.index(sel)], "nota": nota}
    if st.button(f"💾 Guardar la semana de {nombre}", key=f"ros_save_{usuario}",
                 use_container_width=True):
        ok, msg = R.guardar_persona(grupo, lunes, usuario, dias_out)
        (st.success if ok else st.error)(msg)
        if ok:
            st.rerun()


def _catalogo(grupo):
    with st.expander("🎨 Catálogo de trabajos"):
        st.caption("Los trabajos del tablero: número, nombre y color. El enlace a un "
                   "proyecto es opcional — conecta el trabajo con el fichaje y los costos.")
        trabajos = R.list_trabajos(grupo, incluir_inactivos=True)
        if trabajos:
            for r in trabajos:
                _act = str(r.get("Activo", "SI")).upper() in ("SI", "SÍ", "TRUE", "1")
                cc = st.columns([0.5, 4, 2, 1.5])
                cc[0].markdown(f"<div style='width:20px;height:20px;border-radius:5px;"
                               f"background:{r.get('Color','#2e6da4')};margin-top:4px'></div>",
                               unsafe_allow_html=True)
                _prj = str(r.get("ProyectoID", "")).strip()
                cc[1].markdown(f"**{str(r.get('Numero','')).strip()}. {r.get('Nombre','')}**"
                               + (f"  ·  🔗 {_prj}" if _prj else "")
                               + ("" if _act else "  ·  _inactivo_"))
                if cc[2].button("Activar" if not _act else "Desactivar",
                                key=f"trab_act_{r.get('ID')}"):
                    R.set_activo_trabajo(r.get("ID"), not _act)
                    st.rerun()
        else:
            st.caption("Aún no hay trabajos. Añade el primero abajo.")

        st.markdown("**➕ Nuevo trabajo**")
        c1, c2 = st.columns([1, 3])
        num = c1.text_input("Número", key="trab_num", placeholder="89")
        nom = c2.text_input("Nombre", key="trab_nom", placeholder="Talavera")
        c3, c4 = st.columns(2)
        _colmap = {n: h for n, h in R.PALETA}
        colnom = c3.selectbox("Color", list(_colmap.keys()), key="trab_col")
        _prjmap = {f"{p.get('Nombre')} ({p.get('ID')})": str(p.get("ID"))
                   for p in P.list_projects(grupo=grupo)}
        prj = ui.elegir("Proyecto (opcional)", _prjmap, key="trab_prj",
                        vacio="— sin enlace a proyecto —")
        st.markdown(f"<div style='width:100%;height:8px;border-radius:4px;"
                    f"background:{_colmap[colnom]}'></div>", unsafe_allow_html=True)
        if st.button("Crear trabajo", key="trab_add", use_container_width=True):
            if not nom.strip():
                st.error("El nombre es obligatorio.")
            else:
                ok, res = R.add_trabajo(grupo, num, nom, _colmap[colnom], prj or "")
                (st.success if ok else st.error)(
                    f"Trabajo creado ({res})." if ok else res)
                if ok:
                    st.rerun()


def _esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
