"""
Tablero semanal de asignación de cuadrilla — UI del admin (v159).

Sección 📅 Planificación en 🛠 Mi grupo: la rejilla persona×día coloreada (como
el board del usuario), edición de la semana persona a persona, "copiar la semana
anterior" y el catálogo de trabajos.
"""
from datetime import timedelta, time as _time

import streamlit as st

from core import roster as R
from core import auth
from core import projects as P
from core import clock


def _to_time(hhmm, default="07:00") -> _time:
    """'HH:MM' → datetime.time (para st.time_input); cae al default si viene vacío/inválido."""
    for cand in (hhmm, default):
        try:
            hh, mm = str(cand).split(":")
            return _time(int(hh), int(mm))
        except Exception:
            continue
    return _time(7, 0)


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
        asigs = R.celda_asigs(datos, u["Usuario"], d)     # v274: varias por día
        if any(a not in R.ESTADOS for a in asigs):
            en_obra += 1
        elif asigs:                                       # solo estados (OFF/Leave/…)
            estado += 1
        else:
            sin.append(u.get("Nombre") or u["Usuario"])
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
            plan_asigs = R.celda_asigs(datos, usr, _dsel)          # v274: varias por día
            plan_pids = {R.proyecto_de(a, tidx) for a in plan_asigs if R.proyecto_de(a, tidx)}
            plan_lbl = ", ".join(R.etiqueta_de(a, tidx) for a in plan_asigs
                                 if R.proyecto_de(a, tidx)) or "—"
            solo_estados = bool(plan_asigs) and all(a in R.ESTADOS for a in plan_asigs)
            trabajos_sin_prj = [a for a in plan_asigs
                                if a not in R.ESTADOS and not R.proyecto_de(a, tidx)]
            reales = real.get(usr, [])
            real_pids = {e["pid"] for e in reales if e["pid"]}
            real_txt = ", ".join(e["nombre"] for e in reales) or "—"

            if plan_pids:
                falta = plan_pids - real_pids
                extra = real_pids - plan_pids
                if not real_pids:
                    n_sin += 1
                    filas.append((":orange[:material/warning:]", nom,
                                  f"asignado a {plan_lbl} · sin fichar aún"))
                elif not falta:
                    n_ok += 1
                    _ex = f" (+ también {real_txt})" if extra else ""
                    filas.append((":green[:material/check_circle:]", nom,
                                  f"{plan_lbl} — fichó donde tocaba{_ex}"))
                elif plan_pids & real_pids:
                    n_desvio += 1
                    filas.append((":orange[:material/warning:]", nom,
                                  f"asignado a {plan_lbl} · fichó en {real_txt} (faltan algunas)"))
                else:
                    n_desvio += 1
                    filas.append((":red[:material/cancel:]", nom,
                                  f"asignado a {plan_lbl} · fichó en {real_txt}"))
            elif solo_estados:
                if reales:
                    _est = ", ".join(R.etiqueta_de(a, tidx) for a in plan_asigs)
                    filas.append((":blue[:material/info:]", nom,
                                  f"marcado {_est} pero fichó en {real_txt}"))
                # OFF/Leave sin fichar: correcto, no se lista
            elif trabajos_sin_prj:                          # trabajo(s) sin enlace a PRJ
                _tr = ", ".join(R.etiqueta_de(a, tidx) for a in trabajos_sin_prj)
                filas.append(("—", nom, f"{_tr} (sin proyecto que comparar)"
                              + (f" · fichó en {real_txt}" if reales else "")))
            elif reales:                                    # sin plan pero fichó
                filas.append((":material/help:", nom, f"sin asignación · fichó en {real_txt}"))

        st.markdown(f":green[:material/check_circle:] {n_ok} donde tocaba  ·  :red[:material/cancel:] {n_desvio} en otro sitio  ·  "
                    f":orange[:material/warning:] {n_sin} sin fichar")
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


def _guardar_celda(grupo, lunes, usuario, datos, dia, items, nota, toda_semana):
    """Escribe UNA celda (o toda la semana) con VARIAS asignaciones, cada una con su franja
    horaria, + una nota por día (v277). `items` = [{'asig','ini','fin'}]. `guardar_persona`
    omite las vacías → items vacío + nota vacía = limpiar."""
    sem = dict(datos.get(usuario, {}) or {})
    cell = {"items": [{"a": it["asig"], "i": it.get("ini", ""), "f": it.get("fin", "")}
                      for it in (items or []) if it.get("asig")],
            "nota": nota}
    if toda_semana:
        for d in R.DIAS:
            sem[d] = dict(cell)
    else:
        sem[dia] = cell
    return R.guardar_persona(grupo, lunes, usuario, sem)


def _cumplimiento_celda(usuario, pid):
    """Dentro del popover: avisa si el usuario cumple los certificados que EXIGE el
    proyecto (CertsReq). Reusa `credentials.compliance` (v219). Silencioso si el
    proyecto no exige certificados."""
    try:
        prj = P.get_project(pid)
        certs = [c.strip() for c in str((prj or {}).get("CertsReq", "")).split(";")
                 if c.strip()]
        if not certs:
            return
        from core import credentials
        comp = credentials.compliance(usuario, certs)
        _ic = {"vigente": "🟢", "por_vencer": "🟡", "vencido": "🔴", "falta": "⚪"}
        bits = " · ".join(f"{_ic.get(e, '⚪')} {t}" for t, e in comp["por_tipo"].items())
        if comp["cumple"]:
            st.success(f"Cumple los certificados del proyecto: {bits}")
        else:
            st.warning(f":material/warning: No cumple todos los certificados: {bits}")
    except Exception:
        pass


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
    _wk = lunes.strftime("%Y%m%d")   # las keys llevan la SEMANA: al navegar semanas, una
                                     # celda no hereda la selección de otra (evita pisar datos).
    op = _opciones(grupo, tidx)
    op_real = [(e, v) for e, v in op if v != ""]        # sin el neutro (para el multiselect)
    etq = [e for e, _ in op_real]
    val_by_etq = {e: v for e, v in op_real}
    etq_by_val = {v: e for e, v in op_real}

    # 1) CSS de color por celda (color de la 1ª asignación; las vacías, tenues).
    css = []
    for pi, u in enumerate(staff):
        for di, d in enumerate(dias):
            idx = pi * len(dias) + di
            _asigs = R.celda_asigs(datos, u["Usuario"], d)
            asig = _asigs[0] if _asigs else ""
            key = f"roscel_{_wk}_{idx}"
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
            items_cur = R.celda_items(datos, usuario, d)              # v277: con franja
            asigs = [it["asig"] for it in items_cur]
            fr_cur = {it["asig"]: (it["ini"], it["fin"]) for it in items_cur}
            nota = R.celda(datos, usuario, d).get("nota", "")
            # etiqueta del trigger: "Proyecto 7:00–15:30 · Otro …"
            _trig = []
            for it in items_cur:
                _fl = R.franja_label(it["ini"], it["fin"])
                _trig.append(R.etiqueta_de(it["asig"], tidx) + (f" {_fl}" if _fl else ""))
            et = " · ".join(_trig)
            with col.popover(et or "＋", key=f"roscel_{_wk}_{idx}", use_container_width=True):
                f = R.fecha_de_dia(lunes, d)
                st.caption(f"**{_esc(nom)}** · {R.DIAS_LABEL[d]} {f.strftime('%d/%m')}")
                _def = [etq_by_val[a] for a in asigs if a in etq_by_val]
                _sel = st.multiselect("Asignaciones del día (puedes elegir varias)",
                                      etq, default=_def, key=f"pva_{_wk}_{idx}")
                _selvals = [val_by_etq[e] for e in _sel]
                # Por cada asignación: si es PROYECTO/TRABAJO → franja horaria (default 7:00–15:30)
                # + aviso de cumplimiento de certificados. Los estados (OFF/Leave) no llevan franja.
                _items = []
                for _v in _selvals:
                    if _v in R.ESTADOS:
                        _items.append({"asig": _v, "ini": "", "fin": ""})
                        continue
                    _pv = R.proyecto_de(_v, tidx)
                    if _pv:
                        _cumplimiento_celda(usuario, _pv)
                    _ci, _cf = fr_cur.get(_v, R.TURNO_DEFAULT)
                    _c1, _c2 = st.columns(2)
                    _ti = _c1.time_input(f"{R.etiqueta_de(_v, tidx)} · inicio",
                                         value=_to_time(_ci, R.TURNO_DEFAULT[0]),
                                         key=f"pvi_{_wk}_{idx}_{_v}", step=900)
                    _tf = _c2.time_input(f"{R.etiqueta_de(_v, tidx)} · fin",
                                         value=_to_time(_cf, R.TURNO_DEFAULT[1]),
                                         key=f"pvf_{_wk}_{idx}_{_v}", step=900)
                    _items.append({"asig": _v, "ini": _ti.strftime("%H:%M"),
                                   "fin": _tf.strftime("%H:%M")})
                _nota = st.text_input("Nota (para todo el día)", value=nota, key=f"pvn_{_wk}_{idx}",
                                      placeholder="vehículo, equipo…")
                _all = st.checkbox("Aplicar a toda la semana", key=f"pvw_{_wk}_{idx}")
                if st.button(":material/save: Guardar", key=f"pvs_{_wk}_{idx}", type="primary",
                             use_container_width=True):
                    ok, msg = _guardar_celda(grupo, lunes, usuario, datos, d,
                                             _items, _nota, _all)
                    if ok:
                        # cada PROYECTO agendado mete al usuario como asignado del proyecto
                        # → acceso desde su cuenta (no quita a nadie de otros).
                        for _it in _items:
                            _pv = R.proyecto_de(_it["asig"], tidx)
                            if _pv:
                                try:
                                    P.add_field_user(_pv, usuario)
                                except Exception:
                                    pass
                        st.rerun()
                    else:
                        st.error(msg)
                # Abrir cada proyecto elegido (un botón por proyecto).
                for _v in _selvals:
                    _pv = R.proyecto_de(_v, tidx)
                    if _pv and st.button(f"→ {R.etiqueta_de(_v, tidx)}",
                                         key=f"pvo_{_wk}_{idx}_{_v}", use_container_width=True):
                        st.session_state["_prjsel_pending"] = _pv
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
            items = R.celda_items(datos, usr, d)              # v277: con franja horaria
            nota  = R.celda(datos, usr, d).get("nota", "")
            if items:
                _chips = []
                for it in items:
                    _bg = R.color_de(it["asig"], tidx)
                    _fl = R.franja_label(it["ini"], it["fin"])
                    _fh = (f'<span style="opacity:.85;font-weight:400;"> · {_esc(_fl)}</span>'
                           if _fl else "")
                    _chips.append(
                        f'<div style="background:{_bg};color:{_texto_sobre(_bg)};'
                        f'border-radius:5px;padding:2px 5px;margin-bottom:2px;font-weight:600;">'
                        f'{_esc(R.etiqueta_de(it["asig"], tidx))}{_fh}</div>')
                cont = "".join(_chips)
                if nota:
                    cont += (f'<div style="font-size:10.5px;opacity:0.8;color:#4b5563;">'
                             f'{_esc(nota)}</div>')
            else:
                cont = "&nbsp;"
            celdas.append(f'<td style="padding:4px 5px;background:#fff;'
                          f'font-size:11.5px;line-height:1.25;vertical-align:top;">'
                          f'{cont}</td>')
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
            op.append((str(p.get("Nombre", "")), str(p.get("ID", ""))))
    except Exception:
        pass
    for r in R.list_trabajos(grupo):
        num = str(r.get("Numero", "")).strip()
        op.append((f"{num}. {r.get('Nombre','')}" if num else f"{r.get('Nombre','')}",
                   str(r.get("ID", ""))))
    for k, v in R.ESTADOS.items():
        op.append((str(v["nombre"]), k))
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
