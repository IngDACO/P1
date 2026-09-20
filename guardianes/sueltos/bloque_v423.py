

# ─────────────────────────────────────────────────────────────────────────────
# LOCALIZACIONES INTERNAS (v423) — oficina, almacén, taller
#
# Sección PROPIA, no un filtro dentro de la cartera (decisión del usuario): así la
# cartera de obras queda limpia y ninguna vista futura tiene que acordarse de
# excluirlas. El cerrojo de datos es de v422 (`list_projects(incluir_internos=False)`);
# esto es su cara visible — sin ella, una localización se podría crear y NO habría
# forma de verla, que es media aplicación de la regla v340.
#
# ⚠️ Lo que esta pantalla NO tiene, y es deliberado: cronograma, curva S, avance,
# SPI, presupuesto, margen, cliente y facturación. Una localización no se le entrega
# a nadie ni se le cobra a nadie; ponerle esas piezas sería volver a meterla en el
# mundo de la obra por la puerta de atrás.
# ─────────────────────────────────────────────────────────────────────────────

def _loc_datos(grupo):
    """Lo que necesita la lista, en una pasada (todo de cachés ya calientes)."""
    locs = P.list_locations(grupo, incluir_cerradas=True)
    horas, costos, alarmas = {}, {}, {}
    try:
        horas = P.project_hours_bulk(grupo)          # v422: ya incluye las internas
    except Exception:
        pass
    try:
        costos = {str(f["id"]): f for f in E.group_expenses(grupo)["proyectos"]
                  if f.get("interno")}
    except Exception:
        pass
    try:
        if alerts.is_configured():
            alarmas = alerts.open_counts_all()
    except Exception:
        pass
    return locs, horas, costos, alarmas


def _loc_personas(prj) -> list:
    return [x.strip() for x in str(prj.get("CampoAsignados", "")).split(";") if x.strip()]


def _cartera_localizaciones(locs, grupo, horas, costos, alarmas):
    """Tarjeta-botón por localización (patrón v223): toda la info ANTES de abrir."""
    if not locs:
        st.info(":material/info: Aún no hay localizaciones. Crea la oficina o el almacén "
                "aquí abajo para que el equipo pueda fichar, hacer su pre-start y "
                "cargarle gastos.")
        return
    # Abiertas primero, y dentro de cada grupo por gasto (donde más se va el dinero).
    _ord = sorted(locs, key=lambda p: (str(p.get("Estado")) != P.INTERNO_ABIERTA,
                                       -float((costos.get(str(p.get("ID")), {}) or {})
                                              .get("total", 0) or 0)))
    for _i in range(0, len(_ord), 2):
        _cols = st.columns(2, gap="medium")
        for _j, p in enumerate(_ord[_i:_i + 2]):
            pid = str(p.get("ID", ""))
            _c = costos.get(pid, {}) or {}
            _h = float(horas.get(pid, 0.0) or 0.0)
            _al = int(alarmas.get(pid, 0) or 0)
            _cerrada = str(p.get("Estado")) != P.INTERNO_ABIERTA
            _tipo = str(p.get("Tipo", "")) or "Interno"
            _ico = P.TIPO_ICONO.get(_tipo, ":material/business:")
            with _cols[_j].container(border=True, key=f"loccard_{pid}"):
                st.markdown(f"**{_ico} {p.get('Nombre') or '(sin nombre)'}**")
                _pie = [f"`{pid}`", _tipo]
                if _cerrada:
                    _pie.append(":material/lock: cerrada")
                st.caption(" · ".join(_pie))
                m1, m2, m3 = st.columns(3)
                m1.markdown(f"**{_h:,.0f} h**  \n<small>trabajadas</small>",
                            unsafe_allow_html=True)
                m2.markdown(f"**{theme.dinero(_c.get('total', 0), 0)}**  \n"
                            "<small>gastado</small>", unsafe_allow_html=True)
                m3.markdown(f"**{len(_loc_personas(p))}**  \n<small>asignados</small>",
                            unsafe_allow_html=True)
                if str(p.get("Ubicacion", "")).strip():
                    st.caption(f":material/place: {p.get('Ubicacion')}")
                if _al:
                    st.markdown(f":red[:material/notifications_active: {_al} aviso(s) abierto(s)]")
                if st.button("Abrir →", key=f"locopen_{pid}", width="stretch"):
                    st.session_state["_loc_open"] = pid
                    st.rerun()


def _nueva_localizacion_form(grupo: str):
    """Alta de una localización interna.

    ⚠️ Pide MUCHO menos que una obra, y eso es el punto: sin NS, sin fechas, sin
    presupuesto, sin cliente y sin margen. `create_project` con `activities=None` la
    deja sin cronograma, y `derive_estado` la marca «Abierta» por su tipo (v422).
    """
    with st.expander("Nueva localización", icon=":material/add_circle:"):
        campos = []
        try:
            campos = [u["Usuario"] for u in auth.list_users(grupo)
                      if str(u.get("Rol", "")) == "campo"]
        except Exception:
            pass

        # ⚠️ FUERA del form (el mapa necesita reruns) e INLINE, sin expander propio:
        # esto ya vive dentro de un expander y Streamlit no permite anidarlos (v210).
        from core import location_ui
        st.markdown("**:material/map: Dónde está** — opcional, fija el pin")
        _lat, _lng = location_ui.location_picker("nlocloc")
        _ubi = (st.session_state.get("nlocloc_addr")
                or st.session_state.get("nlocloc_q") or "").strip()
        if _ubi:
            st.caption(f":material/place: Se guardará: **{_ubi}**")

        # Los asignados aquí son el «perfil de oficina» (v422): quien esté asignado de
        # forma permanente puede ficharla siempre. Fuera del form para poder avisar en
        # vivo de credenciales y contacto (misma razón que v127).
        asg = st.multiselect(":material/engineering: Quién trabaja aquí de forma habitual",
                             campos, key="nloc_asg",
                             help="Estar asignado aquí es lo que da acceso permanente a "
                                  "ficharla. Quien venga un día suelto se asigna desde "
                                  "Planificación, sin tocar esta lista.")
        if asg:
            _avisar_asignados(asg, grupo)

        with st.form("nloc_form"):
            nom = st.text_input("Nombre *", key="nloc_nom",
                                placeholder="Oficina Sydney, Almacén Chullora…")
            c1, c2 = st.columns(2)
            tipo = c1.selectbox("Tipo *", P.TIPOS_INTERNOS, key="nloc_tipo")
            resp = c2.text_input("Responsable", key="nloc_resp", placeholder="opcional")
            instr = st.text_area(":material/push_pin: Instrucciones / notas", key="nloc_ins",
                                 placeholder="Horario, accesos, normas del sitio…")
            _guardar = st.form_submit_button(":material/save: Crear localización",
                                             type="primary", width="stretch")
        if _guardar:
            if not nom.strip():
                st.error("El nombre es obligatorio.")
                return
            _ok, _res = P.create_project(
                grupo, nom.strip(), ubicacion=_ubi, ingeniero=resp.strip(),
                campo_asignados=asg, instrucciones=instr, tipo=tipo,
                lat="" if _lat is None else _lat,
                lng="" if _lng is None else _lng,
                creado_por=st.session_state.get("auth", {}).get("usuario", ""))
            if not _ok:
                st.error(f"No se pudo crear: {_res}")
                return
            if asg:
                _notificar_asignados(asg, {"ID": _res, "Nombre": nom.strip(),
                                           "Ubicacion": _ubi, "Grupo": grupo})
            for k in ("nloc_nom", "nloc_resp", "nloc_ins", "nloc_asg"):
                st.session_state.pop(k, None)
            flash.exito(f"Localización creada: {_res} · {nom.strip()}")
            st.session_state["_loc_open"] = _res
            st.rerun()


def _loc_equipo(pid, grupo):
    """Quién trabaja aquí y cuánto tiempo — el «seguimiento» que se pidió."""
    st.markdown("#### :material/engineering: Quién ha trabajado aquí")
    try:
        filas = E.labor_breakdown(pid, grupo) if E.is_configured() else {}
    except Exception as e:
        st.caption(f"No se pudieron leer las horas: {e}")
        return
    _p = (filas or {}).get("personas") or []
    if not _p:
        st.caption("Todavía nadie ha fichado aquí.")
        return
    _df = pd.DataFrame([{"Persona": r.get("nombre") or r.get("usuario"),
                         "Horas": round(float(r.get("horas", 0)), 2),
                         "Costo": float(r.get("costo", 0))} for r in _p])
    st.dataframe(_df, width="stretch", hide_index=True,
                 column_config={"Horas": st.column_config.NumberColumn(format="%.2f"),
                                "Costo": st.column_config.NumberColumn(format="$%,.2f")})
    _th = sum(float(r.get("horas", 0)) for r in _p)
    _tc = sum(float(r.get("costo", 0)) for r in _p)
    st.caption(f"**{_th:,.1f} h** · {theme.dinero(_tc)} — ⚠️ esto es costo de "
               "**estructura**: no se le carga a ninguna obra ni se le factura a nadie.")


def _loc_prestarts(pid):
    """Historial de pre-starts de la localización (un almacén también tiene riesgos)."""
    st.markdown("#### :material/health_and_safety: Pre-Start")
    try:
        from core import prestart
        regs = prestart.list_for(pid) if prestart.is_configured() else []
    except Exception as e:
        st.caption(f"No se pudo leer el historial: {e}")
        return
    if not regs:
        st.caption("Sin pre-starts registrados en esta localización.")
        return
    from core import prestart
    for r in regs[:10]:
        d = prestart.leer(r)
        _mal = d.get("near_miss") == "YES" or d.get("n_no", 0) > 0
        st.markdown(f"{'🔴' if _mal else '🟢'} **{d.get('fecha', '')}** · "
                    f"{d.get('facilitador', '')} · {len(d.get('asistentes', []))} asistente(s)")


def _detalle_localizacion(pid: str, grupo: str):
    prj = P.get_project(pid)
    if not prj:
        st.warning("No se encontró la localización.")
        st.session_state.pop("_loc_open", None)
        return
    # ⚠️ Cerrojo de aislamiento (v351): esta vista trae el objeto por ID GLOBAL, igual
    # que el detalle de proyecto, factura, nómina y activo. Sin esto, editar la URL
    # abriría la oficina de otra empresa cliente.
    if not tenant.exigir(prj, "Esta localización"):
        return
    if not P.es_interno(prj):
        st.warning("Ese ID no es una localización interna.")
        st.session_state.pop("_loc_open", None)
        return

    if st.button(":material/arrow_back: Volver a localizaciones", key="loc_back"):
        st.session_state.pop("_loc_open", None)
        st.rerun()

    _tipo = str(prj.get("Tipo", "")) or "Interno"
    _cerrada = str(prj.get("Estado")) != P.INTERNO_ABIERTA
    with st.container(border=True):
        st.markdown(f"### {P.TIPO_ICONO.get(_tipo, ':material/business:')} "
                    f"{prj.get('Nombre') or '(sin nombre)'}")
        _c = [f"`{pid}`", _tipo,
              (":material/lock: cerrada" if _cerrada else ":material/check_circle: abierta")]
        if str(prj.get("Ingeniero", "")).strip():
            _c.append(f"resp. {prj.get('Ingeniero')}")
        st.caption(" · ".join(_c))
        if str(prj.get("Ubicacion", "")).strip():
            st.markdown(maps.maps_link_md(prj.get("Ubicacion")))
    if str(prj.get("Instrucciones", "")).strip():
        st.info(prj.get("Instrucciones"))

    _sec = st.segmented_control(
        "Sección", ["👥 Equipo", "💰 Gastos", "🦺 Pre-Start", "📎 Archivos", "✏️ Datos"],
        default="👥 Equipo", key="cpxseg_loc_sec", label_visibility="collapsed")
    _sec = _sec or "👥 Equipo"

    if _sec == "👥 Equipo":
        a, b = st.columns([3, 2])
        with a:
            _loc_equipo(pid, grupo)
        with b:
            st.markdown("#### :material/badge: Asignados de forma habitual")
            _ppl = _loc_personas(prj)
            if _ppl:
                for u in _ppl:
                    st.markdown(f"· {u}")
                st.caption("Pueden ficharla siempre. Para un día suelto, asígnala "
                           "desde Planificación.")
            else:
                st.caption("Nadie asignado de forma permanente. Solo podrán ficharla "
                           "quienes la tengan puesta hoy en Planificación.")
            _alerts_section(pid, grupo, project_name=prj.get("Nombre"))
    elif _sec == "💰 Gastos":
        render_expenses(pid, grupo, can_delete=True, key_prefix="loc")
    elif _sec == "🦺 Pre-Start":
        _loc_prestarts(pid)
    elif _sec == "📎 Archivos":
        _archivos_section(pid)
    else:
        _editar_localizacion(pid, grupo, prj)


def _editar_localizacion(pid, grupo, prj):
    campos = []
    try:
        campos = [u["Usuario"] for u in auth.list_users(grupo)
                  if str(u.get("Rol", "")) == "campo"]
    except Exception:
        pass
    _actuales = _loc_personas(prj)
    # Fuera del form: para avisar en vivo de contacto/credenciales al asignar (v149).
    _asg = st.multiselect(":material/engineering: Quién trabaja aquí de forma habitual",
                          sorted(set(campos) | set(_actuales)), default=_actuales,
                          key=f"eloc_asg_{pid}")
    _nuevos = [u for u in _asg if u not in _actuales]
    if _nuevos:
        _avisar_asignados(_nuevos, grupo, exclude_pid=pid)

    with st.form(f"eloc_form_{pid}"):
        nom = st.text_input("Nombre *", value=str(prj.get("Nombre", "")),
                            key=f"eloc_nom_{pid}")
        c1, c2 = st.columns(2)
        _tp = str(prj.get("Tipo", "")) or P.TIPOS_INTERNOS[0]
        tipo = c1.selectbox("Tipo *", P.TIPOS_INTERNOS,
                            index=P.TIPOS_INTERNOS.index(_tp) if _tp in P.TIPOS_INTERNOS else 0,
                            key=f"eloc_tipo_{pid}")
        resp = c2.text_input("Responsable", value=str(prj.get("Ingeniero", "")),
                             key=f"eloc_resp_{pid}")
        # ⚠️ «Cerrada» es el estado propio de una localización (v422): no tiene avance,
        # así que «En pausa»/«Completado» no significan nada aquí.
        _est_act = str(prj.get("EstadoManual", "")) or ""
        _opts = ["", P.INTERNO_CERRADA, P.ARCHIVADO]
        est = st.selectbox("Estado", _opts,
                           index=_opts.index(_est_act) if _est_act in _opts else 0,
                           format_func=lambda v: {"": "Abierta",
                                                  P.INTERNO_CERRADA: "Cerrada",
                                                  P.ARCHIVADO: "Archivada"}.get(v, v),
                           key=f"eloc_est_{pid}",
                           help="Cerrada = ya no se usa, pero su histórico se conserva. "
                                "Archivada = además desaparece de la lista.")
        instr = st.text_area(":material/push_pin: Instrucciones / notas",
                             value=str(prj.get("Instrucciones", "")),
                             key=f"eloc_ins_{pid}")
        _guardar = st.form_submit_button(":material/save: Guardar", type="primary",
                                         width="stretch")
    if _guardar:
        if not nom.strip():
            st.error("El nombre es obligatorio.")
            return
        _ok, _msg = P.update_project(pid, {
            "Nombre": nom.strip(), "Tipo": tipo,
            "Ingeniero": resp.strip(), "Instrucciones": instr,
            "CampoAsignados": ";".join(_asg),
            "EstadoManual": est,
            "Estado": P.derive_estado(0, est, tipo),
        })
        if not _ok:
            st.error(_msg)
            return
        if _nuevos:
            _notificar_asignados(_nuevos, {"ID": pid, "Nombre": nom.strip(),
                                           "Ubicacion": prj.get("Ubicacion", ""),
                                           "Grupo": grupo})
        flash.exito("Localización actualizada.")
        st.rerun()


def render_localizaciones(grupo: str):
    """🏢 Localizaciones internas: oficina, almacén, taller.

    ⚠️ SIN título propio: `home_ui._sub_header` ya pinta «Proyectos · Localizaciones».
    Repetirlo ha pasado cuatro veces (v212, v291, v314, v319).
    """
    _abierta = st.session_state.get("_loc_open")
    if _abierta:
        _detalle_localizacion(str(_abierta), grupo)
        return

    locs, horas, costos, alarmas = _loc_datos(grupo)
    _abiertas = [p for p in locs if str(p.get("Estado")) == P.INTERNO_ABIERTA]
    _h = sum(float(horas.get(str(p.get("ID")), 0) or 0) for p in locs)
    _g = sum(float((costos.get(str(p.get("ID")), {}) or {}).get("total", 0) or 0)
             for p in locs)
    _n = len({u for p in locs for u in _loc_personas(p)})

    k = st.columns(4)
    with k[0]:
        _kpi_card("Localizaciones", str(len(_abiertas)),
                  pie=f"de {len(locs)}" if len(locs) != len(_abiertas) else "abiertas")
    with k[1]:
        _kpi_card("Horas trabajadas", f"{_h:,.0f}", pie="no se cargan a obra")
    with k[2]:
        _kpi_card("Gasto de estructura", theme.dinero(_g, 0), pie="no se factura")
    with k[3]:
        _kpi_card("Personas", str(_n), pie="asignadas de forma habitual")

    st.caption("Oficinas, almacenes y talleres: aquí se ficha, se hace el pre-start y "
               "se cargan los gastos de administración. **No tienen cronograma ni "
               "avance, y su costo nunca se le carga a una obra ni se le factura a "
               "un cliente.**")
    _cartera_localizaciones(locs, grupo, horas, costos, alarmas)
    _nueva_localizacion_form(grupo)
