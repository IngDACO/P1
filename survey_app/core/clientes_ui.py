"""👥 Contactos — gestión de clientes (CRM básico).

Lista de clientes → seleccionar uno abre su detalle: ficha de contacto editable,
resumen (proyectos/avance/horas/costo/alarmas) y sus proyectos (clickeables →
abren el proyecto en la sección Proyectos). El enlace cliente↔proyecto usa
`ClienteID` (ID-primero) con respaldo por el texto `Cliente` — ver `core/clientes.py`.
"""
import pandas as pd
import streamlit as st

from core import alerts, expenses, maps
from core import clientes as C
from core import projects as P
from core.num import num as _num


def _norm(s) -> str:
    return C._norm(s)


def _creado_por() -> str:
    a = st.session_state.get("auth") or {}
    return str(a.get("usuario", "") or a.get("nombre", ""))


def _agregados(proys, horas, alarmas, costos):
    """(activos, avance_prom, horas, costo, alarmas) de una lista de proyectos."""
    activos = [x for x in proys
               if str(x.get("Estado", "")) not in ("Completado", "Cancelado", "Archivado")]
    av = (sum(_num(x.get("Avance")) for x in proys) / len(proys)) if proys else 0.0
    hrs = sum(horas.get(str(x.get("ID", "")), 0.0) for x in proys)
    cost = sum(costos.get(str(x.get("ID", "")), 0.0) for x in proys)
    al = sum(int(_num(alarmas.get(str(x.get("ID", "")), 0))) for x in proys)
    return len(activos), av, hrs, cost, al


# ── Vista principal ──────────────────────────────────────────────
def render_contactos(grupo):
    st.markdown("## :material/contacts: Clientes")
    if not C.is_configured():
        st.info(":material/info: Configura Google Sheets para gestionar clientes.")
        return

    # Detalle abierto (clave = nombre normalizado del cliente)
    _open = st.session_state.get("_cli_open")
    if _open:
        _detalle_cliente(grupo, _open)
        return

    fichas  = C.list_clientes(grupo)
    proys   = P.list_projects(grupo=grupo)
    horas   = P.project_hours_bulk(grupo)
    alarmas = alerts.open_counts_all() if alerts.is_configured() else {}
    costos  = ({str(r["id"]): _num(r.get("total")) for r in expenses.group_expenses(grupo)["proyectos"]}
               if expenses.is_configured() else {})

    fichas_by_id   = {str(f.get("ID", "")): f for f in fichas}
    fichas_by_norm = {_norm(f.get("Nombre")): f for f in fichas}

    # Proyectos agrupados por cliente (ID-primero, respaldo por nombre)
    by_client = {}
    for p in proys:
        k, disp = C.client_key(p, fichas_by_id)
        if not k:
            continue
        by_client.setdefault(k, {"nombre": disp, "proys": []})["proys"].append(p)

    all_keys = set(by_client) | set(fichas_by_norm)
    if not all_keys:
        st.caption("Aún no hay clientes. Crea el primero, o crea proyectos con un cliente.")
        _nuevo_cliente_form(grupo)
        return

    rows = []
    for k in all_keys:
        f  = fichas_by_norm.get(k, {})
        pr = by_client.get(k, {}).get("proys", [])
        disp = f.get("Nombre") or by_client.get(k, {}).get("nombre") or "—"
        activos, av, hrs, cost, al = _agregados(pr, horas, alarmas, costos)
        rows.append({"key": k, "disp": disp, "ficha": bool(f),
                     "Contacto": f.get("Contacto", ""), "Telefono": f.get("Telefono", ""),
                     "Email": f.get("Email", ""), "total": len(pr), "activos": activos,
                     "av": av, "hrs": hrs, "cost": cost, "al": al})
    rows.sort(key=lambda r: (-r["activos"], -r["total"], r["disp"].lower()))

    # Fila de salud
    _con_ficha = sum(1 for r in rows if r["ficha"])
    c = st.columns(4)
    c[0].metric("Clientes", len(rows))
    c[1].metric("Con ficha", _con_ficha)
    c[2].metric("Sin ficha", len(rows) - _con_ficha)
    c[3].metric("Proyectos", sum(r["total"] for r in rows))

    # Buscador
    _q = st.text_input(":material/search: Buscar cliente, contacto, teléfono o email",
                       key="cli_q", placeholder="escribe para filtrar…").strip().lower()
    if _q:
        rows = [r for r in rows if _q in " ".join([
            r["disp"], r["Contacto"], r["Telefono"], r["Email"]]).lower()]
    st.caption(f"Toca un cliente para ver su ficha, su resumen y sus proyectos. "
               f"({len(rows)} cliente(s))")

    if not rows:
        st.info(":material/search_off: Ningún cliente coincide con la búsqueda.")
        _nuevo_cliente_form(grupo)
        return

    _hay_costo = expenses.is_configured()
    df = pd.DataFrame([{
        "Cliente":   r["disp"],
        "Ficha":     "sí" if r["ficha"] else "—",
        "Contacto":  r["Contacto"] or "—",
        "Teléfono":  r["Telefono"] or "—",
        "Email":     r["Email"] or "—",
        "Proyectos": r["total"],
        "Activos":   r["activos"],
        "Avance":    int(round(r["av"])),
        "Horas":     round(r["hrs"], 1),
        **({"Costo": round(r["cost"], 0)} if _hay_costo else {}),
        "Alarmas":   str(r["al"]) if r["al"] else "",
    } for r in rows])
    _colcfg = {"Avance": st.column_config.ProgressColumn(
        "Avance", min_value=0, max_value=100, format="%d%%")}
    if _hay_costo:
        _colcfg["Costo"] = st.column_config.NumberColumn("Costo", format="$%d")
    _ev = st.dataframe(
        df, use_container_width=True, hide_index=True,
        on_select="rerun", selection_mode="single-row", key="cli_tbl",
        column_config=_colcfg,
    )
    _sr = list(_ev.selection.rows)
    if _sr:
        st.session_state["_cli_open"] = rows[_sr[0]]["key"]
        st.session_state.pop("cli_tbl", None)   # evita re-abrir al volver
        st.rerun()

    _nuevo_cliente_form(grupo)


# ── Detalle de un cliente ────────────────────────────────────────
def _detalle_cliente(grupo, key):
    if st.button(":material/arrow_back: Volver a clientes", key="cli_back"):
        st.session_state.pop("_cli_open", None)
        st.rerun()

    fichas = C.list_clientes(grupo)
    fichas_by_norm = {_norm(f.get("Nombre")): f for f in fichas}
    fichas_by_id   = {str(f.get("ID", "")): f for f in fichas}
    f = fichas_by_norm.get(key, {})
    cid = str(f.get("ID", ""))
    proys = [p for p in P.list_projects(grupo=grupo) if C.es_del_cliente(p, cid, key)]
    disp = f.get("Nombre") or (proys[0].get("Cliente") if proys else key)

    st.markdown(f"## :material/apartment: {disp}")
    if not f:
        st.info(":material/info: Este cliente aún **no tiene ficha** — sale de sus proyectos. "
                "Completa el contacto abajo y guarda para crear su ficha (y poder vincular proyectos).")

    izq, der = st.columns([3, 2])

    # Ficha de contacto (crea si no existe, edita si existe)
    with izq:
        st.markdown("#### :material/contact_page: Ficha de contacto")
        with st.form(f"cli_form_{key}"):
            _con = st.text_input("Persona de contacto", value=f.get("Contacto", ""))
            cc = st.columns(2)
            _tel  = cc[0].text_input("Teléfono", value=f.get("Telefono", ""))
            _mail = cc[1].text_input("Email", value=f.get("Email", ""))
            _dir  = st.text_input("Dirección", value=f.get("Direccion", ""))
            _notas = st.text_area("Notas", value=f.get("Notas", ""), height=110)
            _save = st.form_submit_button(":material/save: Guardar ficha", type="primary")
        if _save:
            campos = {"Contacto": _con, "Telefono": _tel, "Email": _mail,
                      "Direccion": _dir, "Notas": _notas}
            if cid:
                ok, msg = C.update_cliente(cid, campos)
            else:
                ok, msg = C.create_cliente(grupo, disp, _con, _tel, _mail, _dir,
                                           _notas, creado_por=_creado_por())
            if ok:
                st.success("Ficha guardada.")
                st.rerun()
            else:
                st.error(msg)
        if f.get("Direccion"):
            st.markdown(maps.maps_link_md(f.get("Direccion"), "Ver dirección en el mapa"))

    # Resumen
    with der:
        st.markdown("#### :material/insights: Resumen")
        horas   = P.project_hours_bulk(grupo)
        alarmas = alerts.open_counts_all() if alerts.is_configured() else {}
        costos  = ({str(r["id"]): _num(r.get("total")) for r in expenses.group_expenses(grupo)["proyectos"]}
                   if expenses.is_configured() else {})
        activos, av, hrs, cost, al = _agregados(proys, horas, alarmas, costos)
        r1 = st.columns(2)
        r1[0].metric("Proyectos", len(proys))
        r1[1].metric("Activos", activos)
        r2 = st.columns(2)
        r2[0].metric("Avance prom.", f"{av:.0f}%")
        r2[1].metric("Horas", f"{hrs:.1f}")
        if expenses.is_configured():
            st.metric("Costo total", f"${cost:,.0f}")
        if al:
            st.markdown(f":red[:material/notifications:] **{al}** alarma(s) abierta(s)")
        if cid:
            with st.expander(":material/archive: Archivar cliente"):
                st.caption("Deja de listarse; sus proyectos no se tocan.")
                if st.button("Archivar esta ficha", key=f"cli_arch_{cid}"):
                    C.set_activo(cid, False)
                    st.session_state.pop("_cli_open", None)
                    st.rerun()

    # Proyectos del cliente (ancho completo, clickeables)
    st.markdown("#### :material/folder: Proyectos de este cliente")
    if not proys:
        st.caption("Aún no tiene proyectos vinculados.")
    else:
        cols = st.columns(2)
        for i, p in enumerate(sorted(proys, key=lambda x: str(x.get("Nombre", "")).lower())):
            pid = str(p.get("ID", ""))
            _lbl = f"**{p.get('Nombre', '')}** · {p.get('Estado', '')} · {int(_num(p.get('Avance')))}%"
            if cols[i % 2].button(_lbl, key=f"cli_prj_{pid}", use_container_width=True):
                st.session_state["_prjsel_pending"] = pid
                st.session_state["_admin_nav_pending"] = ("proyectos", "📊 Proyectos")
                st.rerun()

    # Vincular más proyectos (necesita ficha con ID)
    if cid:
        otros = [p for p in P.list_projects(grupo=grupo) if not C.es_del_cliente(p, cid, key)]
        if otros:
            with st.expander(":material/link: Vincular otros proyectos a este cliente"):
                st.caption("Útil si el proyecto tiene otro texto en «Cliente» o quedó sin vincular.")
                _opts = {f"{p.get('Nombre', '')} ({p.get('ID', '')})": str(p.get("ID", ""))
                         for p in otros}
                _sel = st.multiselect("Proyectos a vincular", list(_opts.keys()),
                                      key=f"cli_link_{cid}")
                if st.button(":material/link: Vincular seleccionados", key=f"cli_linkbtn_{cid}"):
                    if _sel:
                        for _lbl in _sel:
                            P.update_project(_opts[_lbl], {"ClienteID": cid, "Cliente": disp})
                        st.success(f"{len(_sel)} proyecto(s) vinculado(s).")
                        st.rerun()
                    else:
                        st.warning("Elige al menos un proyecto.")

    # ── Estado de cuenta: facturas del cliente (v259) ──
    from core import invoices as INV
    if cid and INV.is_configured():
        st.markdown("#### :material/receipt: Facturación")
        rc = INV.resumen_cliente(grupo, cid)
        fc = st.columns(4)
        fc[0].metric("Facturado", f"${rc['facturado']:,.0f}")
        fc[1].metric("Cobrado", f"${rc['cobrado']:,.0f}")
        fc[2].metric("Pendiente", f"${rc['pendiente']:,.0f}")
        fc[3].metric("Vencido", f"${rc['vencido']:,.0f}")
        _facs = INV.list_facturas(grupo, cid)
        if _facs:
            _fr = sorted(_facs, key=lambda x: str(x.get("Creado", "")), reverse=True)
            _fdf = pd.DataFrame([{
                "Nº":      str(x.get("Numero", "")),
                "Fecha":   str(x.get("Fecha", "")),
                "Total":   round(_num(x.get("Total")), 0),
                "Cobrado": round(_num(x.get("Cobrado")), 0),
                "Estado":  INV.estado_cobro(x),
            } for x in _fr])
            _fev = st.dataframe(
                _fdf, use_container_width=True, hide_index=True,
                on_select="rerun", selection_mode="single-row", key=f"cli_facs_{cid}",
                column_config={"Total": st.column_config.NumberColumn("Total", format="$%d"),
                               "Cobrado": st.column_config.NumberColumn("Cobrado", format="$%d")})
            _fs = list(_fev.selection.rows)
            if _fs:
                st.session_state["_fac_open"] = str(_fr[_fs[0]].get("ID", ""))
                st.session_state["_admin_nav_pending"] = ("finanzas", "🧾 Facturas")
                st.session_state.pop(f"cli_facs_{cid}", None)
                st.rerun()
        else:
            st.caption("Sin facturas todavía.")
        if st.button(":material/add_circle: Nueva factura para este cliente", key=f"cli_newfac_{cid}"):
            st.session_state["_fac_nueva"] = True
            st.session_state["fac_cli"] = disp   # preselecciona el cliente en el form de factura
            st.session_state["_admin_nav_pending"] = ("finanzas", "🧾 Facturas")
            st.rerun()


# ── Alta de cliente ──────────────────────────────────────────────
def _nuevo_cliente_form(grupo):
    with st.expander(":material/add_circle: Nuevo cliente"):
        with st.form("cli_nuevo"):
            _nom = st.text_input("Nombre del cliente *")
            cc = st.columns(2)
            _con = cc[0].text_input("Persona de contacto")
            _tel = cc[1].text_input("Teléfono")
            cc2 = st.columns(2)
            _mail = cc2[0].text_input("Email")
            _dir  = cc2[1].text_input("Dirección")
            _notas = st.text_area("Notas", height=80)
            _crear = st.form_submit_button(":material/add: Crear cliente", type="primary")
        if _crear:
            ok, msg = C.create_cliente(grupo, _nom, _con, _tel, _mail, _dir, _notas,
                                       creado_por=_creado_por())
            if ok:
                st.success("Cliente creado.")
                st.session_state["_cli_open"] = _norm(_nom)
                st.rerun()
            else:
                st.error(msg)
