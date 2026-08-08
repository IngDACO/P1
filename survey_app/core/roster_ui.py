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
from core import clock


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


def _cobertura_hoy(lunes, staff, datos):
    """Cobertura del día en vista (hoy si cae en la semana, si no el lunes): en obra /
    sin asignar (con nombres) / OFF-Leave — para ver los huecos de un vistazo (v217)."""
    off = (clock.today() - lunes).days
    d = R.DIAS[off] if 0 <= off <= 4 else R.DIAS[0]
    fecha = R.fecha_de_dia(lunes, d)
    en_obra, estado, sin = 0, 0, []
    for u in staff:
        asig = str(R.celda(datos, u["Usuario"], d).get("asig", ""))
        if not asig:
            sin.append(u.get("Nombre") or u["Usuario"])
        elif asig in R.ESTADOS:
            estado += 1
        else:
            en_obra += 1
    partes = [f":green[:material/check_circle:] **{en_obra}** en obra"]
    if sin:
        _n = ", ".join(sin[:4]) + ("…" if len(sin) > 4 else "")
        partes.append(f":orange[:material/warning:] **{len(sin)}** sin asignar ({_esc(_n)})")
    else:
        partes.append(":green[:material/check_circle:] nadie sin asignar")
    if estado:
        partes.append(f":gray[:material/crop_square:] **{estado}** OFF/Leave")
    st.markdown(f"**{R.DIAS_LABEL[d]} {fecha.strftime('%d/%m')}** · " + " · ".join(partes))


def render_planificacion(grupo):
    st.markdown("#### :material/calendar_month: Planificación de la semana")
    if not R.is_configured():
        st.warning("La planificación necesita Google Sheets configurado.")
        return

    staff = _staff(grupo)
    if not staff:
        st.info("Aún no tienes personal de campo. Créalo en :material/build: Usuarios de campo.")
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
    if n4.button(":material/assignment: Copiar semana anterior", key="ros_copy", use_container_width=True):
        ok, msg = R.copiar_semana(grupo, lunes - timedelta(days=7), lunes)
        (st.success if ok else st.warning)(msg)
        if ok:
            st.rerun()

    # ── Cobertura del día (dónde está la cuadrilla, dónde hay huecos) ──
    _cobertura_hoy(lunes, staff, datos)

    # ── Tablero EDITABLE EN SITIO: toca una celda para asignar/editar ahí mismo ──
    st.caption("Toca una celda para **asignar o editar ahí mismo** (una vacía ＋ también "
               "asigna). Si el trabajo enlaza a un proyecto, dentro tienes «→ Abrir proyecto».")
    _tablero_editable(grupo, lunes, staff, datos, tidx)

    # ── Plan vs real ──
    _plan_vs_real(grupo, lunes, staff, tidx)

    # ── Catálogo de trabajos ──
    _catalogo(grupo)


def _plan_vs_real(grupo, lunes, staff, tidx):
    """Compara la asignacion del dia (si enlaza a PRJ) contra donde ficho cada uno.

    Solo tiene sentido para trabajos enlazados a un proyecto: un delivery o un
    estado (OFF/Leave) no tiene fichaje contra que comparar. Decision de v161.
    """
    from datetime import date as _date
    from core import timeclock
    with st.expander(":material/search: Plan vs real (lo asignado contra lo fichado)"):
        if not timeclock.is_configured():
            st.caption("Necesita el fichaje configurado.")
            return
        # Día a comparar: hoy si cae en la semana vista, si no el lunes.
        hoy = clock.today()
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
                    filas.append((":blue[:material/info:]", nom, f"marcado {R.etiqueta_de(asig, tidx)} "
                                  f"pero fichó en {real_txt}"))
                # OFF/Leave sin fichar: correcto, no se lista
            elif plan_pid:
                if plan_pid in real_pids:
                    n_ok += 1
                    filas.append((":green[:material/check_circle:]", nom, f"{R.etiqueta_de(asig, tidx)} — fichó donde tocaba"))
                elif real_pids:
                    n_desvio += 1
                    filas.append((":red[:material/cancel:]", nom, f"asignado a {R.etiqueta_de(asig, tidx)} · "
                                  f"fichó en {real_txt}"))
                else:
                    n_sin += 1
                    filas.append((":orange[:material/warning:]", nom, f"asignado a {R.etiqueta_de(asig, tidx)} · "
                                  "sin fichar aún"))
            elif asig:                                  # trabajo sin enlace a PRJ
                filas.append(("—", nom, f"{R.etiqueta_de(asig, tidx)} "
                              "(sin proyecto que comparar)"
                              + (f" · fichó en {real_txt}" if reales else "")))
            elif reales:                                # sin plan pero ficho
                filas.append(("❔", nom, f"sin asignación · fichó en {real_txt}"))

        st.markdown(f"`:green[:material/check_circle:] {n_ok} donde tocaba`  `:red[:material/cancel:] {n_desvio} en otro sitio`  "
                    f"`:orange[:material/warning:] {n_sin} sin fichar`")
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


def _guardar_celda(grupo, lunes, usuario, datos, dia, asig, nota, toda_semana):
    """Escribe UNA celda (o toda la semana) reusando la semana actual de la persona.
    `guardar_persona` omite las celdas vacías, así que asig+nota vacíos = limpiar."""
    sem = dict(datos.get(usuario, {}) or {})
    if toda_semana:
        for d in R.DIAS:
            sem[d] = {"asig": asig, "nota": nota}
    else:
        sem[dia] = {"asig": asig, "nota": nota}
    return R.guardar_persona(grupo, lunes, usuario, sem)


def _tablero_editable(grupo, lunes, staff, datos, tidx):
    """Board del admin EDITABLE EN SITIO (v217): cada celda es un `st.popover`
    coloreado con el color de su trabajo (clase `st-key-<key>` sobre el trigger —
    verificado en vivo antes de construir). Al tocar la celda se edita AHÍ MISMO
    (asignación + nota, con «aplicar a toda la semana») y, si el trabajo enlaza a un
    proyecto, se salta a su detalle — sin salir del tablero ni un formulario aparte.
    Una celda vacía (＋) también asigna en sitio. Reemplaza el editor por-persona de
    abajo (v159). El board del campo sigue siendo el HTML de `_grid_html`.
    """
    dias = R.DIAS
    op = _opciones(grupo, tidx)
    etiquetas = [e for e, _ in op]
    valores   = [v for _, v in op]

    # 1) CSS de color por celda (una regla por celda; las vacías, tenues).
    css = []
    for pi, u in enumerate(staff):
        for di, d in enumerate(dias):
            idx = pi * len(dias) + di
            asig = str(R.celda(datos, u["Usuario"], d).get("asig", ""))
            key = f"roscel_{idx}"
            if asig:
                bg = R.color_de(asig, tidx)
                css.append(f".st-key-{key} button{{background:{bg}!important;"
                           f"color:{_texto_sobre(bg)}!important;border-color:{bg}!important;}}")
            else:
                css.append(f".st-key-{key} button{{background:#f8fafc!important;"
                           f"color:#b6c0cd!important;border:1px dashed #e2e8f0!important;}}")
    if css:
        st.markdown("<style>" + "".join(css) + "</style>", unsafe_allow_html=True)

    # 2) Cabecera (persona + días)
    anchos = [1.4] + [1] * len(dias)
    h = st.columns(anchos)
    h[0].markdown("<div style='font-size:12px;color:#6b7280'>Persona</div>",
                  unsafe_allow_html=True)
    for i, d in enumerate(dias):
        f = R.fecha_de_dia(lunes, d)
        h[i + 1].markdown(f"<div style='font-size:12px;color:#6b7280'>{R.DIAS_LABEL[d]} "
                          f"{f.strftime('%d/%m')}</div>", unsafe_allow_html=True)

    # 3) Filas: nombre + una celda-popover por día
    for pi, u in enumerate(staff):
        usuario = u["Usuario"]
        nom = u.get("Nombre") or usuario
        cols = st.columns(anchos)
        cols[0].markdown(f"<div style='padding-top:8px;font-weight:600;font-size:13px'>"
                         f"{_esc(nom)}</div>", unsafe_allow_html=True)
        for di, d in enumerate(dias):
            idx = pi * len(dias) + di
            col = cols[di + 1]
            c = R.celda(datos, usuario, d)
            asig = str(c.get("asig", ""))
            nota = str(c.get("nota", ""))
            pid  = R.proyecto_de(asig, tidx)
            et   = R.etiqueta_de(asig, tidx)
            with col.popover(et or "＋", key=f"roscel_{idx}", use_container_width=True):
                f = R.fecha_de_dia(lunes, d)
                st.caption(f"**{_esc(nom)}** · {R.DIAS_LABEL[d]} {f.strftime('%d/%m')}")
                _i = valores.index(asig) if asig in valores else 0
                _sel = st.selectbox("Asignación", etiquetas, index=_i, key=f"pva_{idx}")
                _nota = st.text_input("Nota", value=nota, key=f"pvn_{idx}",
                                      placeholder="vehículo, equipo, horario…")
                _all = st.checkbox("Aplicar a toda la semana", key=f"pvw_{idx}")
                if st.button(":material/save: Guardar", key=f"pvs_{idx}", type="primary",
                             use_container_width=True):
                    _nueva = valores[etiquetas.index(_sel)]
                    ok, msg = _guardar_celda(grupo, lunes, usuario, datos, d,
                                             _nueva, _nota, _all)
                    if ok:
                        st.rerun()
                    else:
                        st.error(msg)
                if pid and st.button("→ Abrir proyecto", key=f"pvo_{idx}",
                                     use_container_width=True):
                    # Navega al detalle en la nav NUEVA del admin y (por si acaso) la
                    # vieja: se fija el pending que lee cada shell antes de sus radios.
                    st.session_state["_prjsel_pending"] = pid
                    st.session_state["_admin_nav_pending"] = ("proyectos", "📊 Proyectos")
                    st.session_state["_gruposec_pending"] = "📊 Proyectos"
                    st.rerun()
            if nota:
                col.caption(nota)


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
                  f'border-right:1px solid #eef1f5;">{"<span style=\"font-family:&#39;Material Symbols Rounded&#39;;vertical-align:-2px\">arrow_forward</span> " if _mio else ""}{_esc(nom)}</td>']
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
    """[(etiqueta, valor)] para el selector: neutro + PROYECTOS (directo) + trabajos
    (no-proyecto) + estados. Un proyecto ya es asignable por sí mismo (v218): no hay que
    crear un 'trabajo' que lo enlace. Los proyectos completados/cancelados no se ofrecen."""
    op = [("— sin asignar —", "")]
    try:
        for p in P.list_projects(grupo=grupo):
            if str(p.get("Estado", "")) in ("Completado", "Cancelado"):
                continue
            op.append((f":material/apartment: {p.get('Nombre','')}", str(p.get("ID", ""))))
    except Exception:
        pass
    for r in R.list_trabajos(grupo):
        num = str(r.get("Numero", "")).strip()
        op.append((f":material/build: {num}. {r.get('Nombre','')}" if num else f":material/build: {r.get('Nombre','')}",
                   str(r.get("ID", ""))))
    for k, v in R.ESTADOS.items():
        op.append((f":gray[:material/crop_square:] {v['nombre']}" if k == "OFF" else f":red[:material/cancel:] {v['nombre']}", k))
    return op


def _catalogo(grupo):
    with st.expander(":material/palette: Catálogo de trabajos (lo que NO es un proyecto)"):
        st.caption("Para trabajos que **no** son un proyecto: entregas, cursos, policía, "
                   "traslados… Los **proyectos se asignan directo** en el tablero (ya son un "
                   "trabajo en sí mismos), no hace falta crearlos aquí.")
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
                               + (f"  ·  :material/link: {_prj}" if _prj else "")
                               + ("" if _act else "  ·  _inactivo_"))
                if cc[2].button("Activar" if not _act else "Desactivar",
                                key=f"trab_act_{r.get('ID')}"):
                    R.set_activo_trabajo(r.get("ID"), not _act)
                    st.rerun()
        else:
            st.caption("Aún no hay trabajos. Añade el primero abajo.")

        st.markdown("**:material/add: Nuevo trabajo** (no-proyecto)")
        c1, c2, c3 = st.columns([1, 2.5, 1.5])
        num = c1.text_input("Número", key="trab_num", placeholder="89")
        nom = c2.text_input("Nombre", key="trab_nom", placeholder="Entrega / Curso / Traslado…")
        _colmap = {n: h for n, h in R.PALETA}
        colnom = c3.selectbox("Color", list(_colmap.keys()), key="trab_col")
        st.markdown(f"<div style='width:100%;height:8px;border-radius:4px;"
                    f"background:{_colmap[colnom]}'></div>", unsafe_allow_html=True)
        if st.button("Crear trabajo", key="trab_add", use_container_width=True):
            if not nom.strip():
                st.error("El nombre es obligatorio.")
            else:
                ok, res = R.add_trabajo(grupo, num, nom, _colmap[colnom], "")
                (st.success if ok else st.error)(
                    f"Trabajo creado ({res})." if ok else res)
                if ok:
                    st.rerun()


def _esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
