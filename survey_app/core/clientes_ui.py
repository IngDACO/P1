"""👥 Contactos — gestión de clientes (CRM básico).

Lista de clientes → seleccionar uno abre su detalle: ficha de contacto editable,
resumen (proyectos/avance/horas/costo/alarmas) y sus proyectos (clickeables →
abren el proyecto en la sección Proyectos). El enlace cliente↔proyecto usa
`ClienteID` (ID-primero) con respaldo por el texto `Cliente` — ver `core/clientes.py`.
"""
import pandas as pd

from core.i18n import t, etiqueta as _etq
import streamlit as st

from core import flash

from core import alerts, expenses, maps
from core import clientes as C
from core import projects as P
from core.num import num as _num
from core import tabla


def _norm(s) -> str:
    return C._norm(s)


def _creado_por() -> str:
    a = st.session_state.get("auth") or {}
    return str(a.get("usuario", "") or a.get("nombre", ""))


def _agregados(proys, horas, alarmas, costos):
    """(activos, avance_prom, horas, costo, alarmas) de una lista de proyectos."""
    activos = [x for x in proys
               if str(x.get("Status", "")) not in ("Completed", "Cancelled", "Archived")]
    av = (sum(_num(x.get("Progress")) for x in proys) / len(proys)) if proys else 0.0
    hrs = sum(horas.get(str(x.get("ID", "")), 0.0) for x in proys)
    cost = sum(costos.get(str(x.get("ID", "")), 0.0) for x in proys)
    al = sum(int(_num(alarmas.get(str(x.get("ID", "")), 0))) for x in proys)
    return len(activos), av, hrs, cost, al


# Filtro de la lista de clientes (v575): ID interno → rótulo. ⚠️ Sin `t()` aquí: se
# construye al IMPORTAR (quedaría congelado, v445); se traduce al pintar.
_FILTROS_CLI = {"Todos": "All", "ConFicha": "With record", "SinFicha": "No record",
                "ConObras": "With jobs"}


def _horas(h) -> str:
    """«0 h» y no «0.0» (como las tarjetas de Locations, v565)."""
    return "0 h" if round(h, 1) == 0 else f"{h:,.1f} h"


def _vista_cli(key) -> str:
    """La cifra abierta en la ficha de ESTE cliente (otra ficha nace cerrada)."""
    return st.session_state.get(f"_cls_vista::{key}", "")


def _cifras_cliente(key, n, activos, av, hrs, cost, al, con_coste, con_alertas):
    """El resumen del cliente, ACTIVO (v571: eran `st.metric` que no se podían tocar):
    cada cifra abre debajo el desglose por obra con su filtro u orden (`_desglose_obras`);
    la misma otra vez lo cierra. Las alertas, que eran una línea suelta, son una cifra más."""
    from core import theme as _T
    # ⚠️ Pies CORTOS (el kit los recorta con «…» para que la fila mida igual): medido en
    # producción, a 800 px con el menú cada tarjeta deja 87 px de pie y «linked to this
    # client» (97) salía «linked to this c…». Todos ≤ 80 px con la fuente real.
    _K = [("prj", t("Projects"), str(n), t("of this client")),
          ("act", t("Active"), str(activos), t("not completed")),
          ("av", t("Avg. progress"), f"{av:.0f}%", t("across its jobs")),
          ("hrs", t("Hours"), _horas(hrs), t("clocked on jobs"))]
    if con_coste:
        _K.append(("cost", t("Total cost"), _T.dinero(cost, 0), t("charged to jobs")))
    if con_alertas:
        _K.append(("al", t("Open alerts"), str(al), t("on its jobs")))
    if al:
        st.markdown("<style>.st-key-cpxkpi_cls_al button{border-left-color:#c0392b!important}"
                    ".st-key-cpxkpi_cls_al button p:nth-child(2):not(:last-child)"
                    "{color:#c0392b!important}</style>", unsafe_allow_html=True)
    _cur = _vista_cli(key)
    # v576 · 2 por fila también en estrecho (a ≤640 px Streamlit apilaba las columnas)
    st.markdown(_T.dos_por_fila("cpx_cls_kpis"), unsafe_allow_html=True)
    _box = st.container(key="cpx_cls_kpis")
    for _i in range(0, len(_K), 2):
        for _col, (_s, _l, _v, _pie) in zip(_box.columns(2), _K[_i:_i + 2]):
            if _col.button(f"{_l}\n\n{_v}\n\n{_pie}", key=f"cpxkpi_cls_{_s}", width="stretch"):
                st.session_state[f"_cls_vista::{key}"] = "" if _cur == _s else _s
                st.session_state["_cls_bajar"] = _cur != _s
                st.rerun()


def _desglose_obras(key, proys, horas, costos, alarmas, con_coste, con_alertas):
    """Las obras del cliente con lo que suman en el resumen (v571), con el filtro u orden
    de la cifra tocada. Un toque en una obra la abre (en Costs si se vino por el coste)."""
    _v = _vista_cli(key)
    if not _v:
        return
    from core import projects_ui as PU
    filas = [{"id": str(p.get("ID", "")), "nombre": str(p.get("Name", "")),
              "estado": str(p.get("Status", "")), "av": _num(p.get("Progress")),
              "hrs": float(horas.get(str(p.get("ID", "")), 0.0)),
              "cost": float(costos.get(str(p.get("ID", "")), 0.0)),
              "al": int(_num(alarmas.get(str(p.get("ID", "")), 0)))} for p in proys]
    filas.sort(key=lambda f: f["nombre"].lower())
    if _v == "act":
        filas = [f for f in filas if f["estado"] not in ("Completed", "Cancelled", "Archived")]
    elif _v == "av":
        filas.sort(key=lambda f: f["av"])
    elif _v == "hrs":
        filas.sort(key=lambda f: -f["hrs"])
    elif _v == "cost":
        filas.sort(key=lambda f: -f["cost"])
    elif _v == "al":
        filas = sorted([f for f in filas if f["al"]], key=lambda f: -f["al"])
    _tit = {"prj": t("All its projects"), "act": t("Its active projects (not completed)"),
            "av": t("Progress by project, least advanced first"), "hrs": t("Hours by project"),
            "cost": t("Cost by project"), "al": t("Projects with open alerts")}
    with st.container(border=True, key="cpx_cls_desglose"):
        PU._bajar_a("cpx_cls_desglose", "_cls_bajar")
        st.markdown(f"**{_tit.get(_v, '')}**")
        if not filas:
            st.caption(t("No project in this view."))
            return
        st.caption(t("Tap a project to open it."))
        df = pd.DataFrame([{
            "Proyecto": f["nombre"],
            "Estado":   _etq(f["estado"]),
            "Avance":   int(round(f["av"])),
            "Horas":    round(f["hrs"], 1),
            **({"Costo": round(f["cost"], 2)} if con_coste else {}),
            **({"Alarms": f["al"]} if con_alertas else {}),
        } for f in filas])
        _gk = "_cls_tbl_gen"
        _ev = st.dataframe(
            df, width="stretch", hide_index=True,
            on_select="rerun", selection_mode="single-cell",
            key=f"cls_tbl_{st.session_state.get(_gk, 0)}",
            column_config=tabla.cfg(None, {
                "Proyecto": st.column_config.TextColumn(t("Project"), pinned=True),
                "Avance": st.column_config.ProgressColumn(t("Progress"), min_value=0,
                                                          max_value=100, format="%d%%"),
                "Horas": st.column_config.NumberColumn(t("Hours"), format="%.1f h"),
                "Costo": st.column_config.NumberColumn(t("Cost"), format="$%,.2f"),
                "Alarms": st.column_config.NumberColumn(t("Open alerts"), format="%d"),
            }))
        PU._tabla_abre_obra(_ev, filas, _gk, "💰 Costos" if _v == "cost" else "📊 Estado")


# ── Vista principal ──────────────────────────────────────────────
def render_contactos(grupo):
    st.markdown(t("## :material/contacts: Clients"))
    if not C.is_configured():
        st.info(t(":material/info: Configure Google Sheets to manage clients."))
        return

    # Detalle abierto (clave = nombre normalizado del cliente)
    _open = st.session_state.get("_cli_open")
    if _open:
        _detalle_cliente(grupo, _open)
        return

    # ⚠️ v340: archivar un cliente era un VIAJE SIN VUELTA. `set_activo(cid, False)`
    # lo marca `Activo=NO` y las 5 llamadas a `list_clientes` usaban el default, que
    # los oculta — sin casilla para verlos ni botón para restaurar. Desaparecía y no
    # había forma de recuperarlo desde la app. Es exactamente lo que v149 arregló
    # para los proyectos y a los clientes nunca se les aplicó.
    _ver_arch = st.checkbox(t(":material/archive: Show archived ones too"),
                            key="cli_ver_arch",
                            help=t("Archived ones stop being listed, but are not deleted: their projects, hours and invoices stay intact."))
    fichas  = C.list_clientes(grupo, incluir_inactivos=_ver_arch)
    _n_arch = len([f for f in C.list_clientes(grupo, incluir_inactivos=True)
                   if str(f.get("Active", "SI")).upper() in ("NO", "FALSE", "0")])
    if _n_arch and not _ver_arch:
        st.caption(t(":material/inventory_2: {n} archived client(s) hidden.", n=_n_arch))
    proys   = P.list_projects(grupo=grupo)
    horas   = P.project_hours_bulk(grupo)
    alarmas = alerts.open_counts_all() if alerts.is_configured() else {}
    costos  = ({str(r["id"]): _num(r.get("total")) for r in expenses.group_expenses(grupo)["proyectos"]}
               if expenses.is_configured() else {})

    fichas_by_id   = {str(f.get("ID", "")): f for f in fichas}
    fichas_by_norm = {_norm(f.get("Name")): f for f in fichas}

    # Proyectos agrupados por cliente (ID-primero, respaldo por nombre)
    by_client = {}
    for p in proys:
        k, disp = C.client_key(p, fichas_by_id)
        if not k:
            continue
        by_client.setdefault(k, {"nombre": disp, "proys": []})["proys"].append(p)

    all_keys = set(by_client) | set(fichas_by_norm)
    if not all_keys:
        st.caption(t("No clients yet. Create the first one, or create projects with a client."))
        _nuevo_cliente_form(grupo)
        return

    rows = []
    for k in all_keys:
        f  = fichas_by_norm.get(k, {})
        pr = by_client.get(k, {}).get("proys", [])
        disp = f.get("Name") or by_client.get(k, {}).get("nombre") or "—"
        activos, av, hrs, cost, al = _agregados(pr, horas, alarmas, costos)
        rows.append({"key": k, "disp": disp, "ficha": bool(f),
                     "ContactName": f.get("ContactName", ""), "Phone": f.get("Phone", ""),
                     "Email": f.get("Email", ""), "total": len(pr), "activos": activos,
                     "av": av, "hrs": hrs, "cost": cost, "al": al})
    rows.sort(key=lambda r: (-r["activos"], -r["total"], r["disp"].lower()))

    # Fila de salud · ⚠️ v575 · ACTIVA (eran `st.metric` que no se podían tocar): cada cifra
    # aplica su filtro a la lista, con el mismo selector recordado que Invoices y Payroll.
    _con_ficha = sum(1 for r in rows if r["ficha"])
    _K = [("tot", t("Clients"), len(rows), t("in the list"), "Todos"),
          ("con", t("With record"), _con_ficha, t("contact details saved"), "ConFicha"),
          ("sin", t("No record"), len(rows) - _con_ficha, t("only from their jobs"), "SinFicha"),
          ("prj", t("Projects"), sum(r["total"] for r in rows), t("linked to clients"), "ConObras")]
    from core import theme as _T
    st.markdown(_T.dos_por_fila("cpx_clis_kpis"), unsafe_allow_html=True)   # v576 · 2 por fila en estrecho
    with st.container(key="cpx_clis_kpis"):
        for _col, (_s, _l, _v, _pie, _fl) in zip(st.columns(4), _K):
            if _col.button(f"{_l}\n\n{_v}\n\n{_pie}", key=f"cpxkpi_clis_{_s}", width="stretch"):
                st.session_state["_clis_filt_pending"] = _fl
                st.rerun()
    _pp = st.session_state.pop("_clis_filt_pending", None)
    if _pp in _FILTROS_CLI:
        st.session_state["cpxseg_clis_filt"] = _pp
    _filt = st.radio(t("Filter"), list(_FILTROS_CLI), format_func=lambda o: t(_FILTROS_CLI[o]),
                     horizontal=True, key="cpxseg_clis_filt", label_visibility="collapsed",
                     persist_state="session")
    if _filt == "ConFicha":
        rows = [r for r in rows if r["ficha"]]
    elif _filt == "SinFicha":
        rows = [r for r in rows if not r["ficha"]]
    elif _filt == "ConObras":
        rows = [r for r in rows if r["total"]]

    # Buscador
    _q = st.text_input(t(":material/search: Search client, contact, phone or email"),
                       key="cli_q", placeholder=t("type to filter…")).strip().lower()
    if _q:
        rows = [r for r in rows if _q in " ".join([
            r["disp"], r["ContactName"], r["Phone"], r["Email"]]).lower()]
    st.caption(t("Tap a client to see its record, summary and projects. ({n} client(s))",
                 n=len(rows)))

    if not rows:
        st.info(t(":material/search_off: No client matches the search or the filter."))
        _nuevo_cliente_form(grupo)
        return

    _hay_costo = expenses.is_configured()
    df = pd.DataFrame([{
        "Cliente":   r["disp"],
        "Ficha":     t("yes") if r["ficha"] else "—",
        "Contacto":  r["ContactName"] or "—",
        "Phone":  r["Phone"] or "—",
        "Email":     r["Email"] or "—",
        "Projects": r["total"],
        "Active":   r["activos"],
        "Avance":    int(round(r["av"])),
        "Horas":     round(r["hrs"], 1),
        **({"Costo": round(r["cost"], 2)} if _hay_costo else {}),
        "Alarms":   str(r["al"]) if r["al"] else "",
    } for r in rows])
    # ⚠️ Las claves tienen que ser las de la FILA ("Avance"/"Costo"), no la etiqueta.
    # v468 las renombro aqui y no arriba, asi que las dos quedaban HUERFANAS: la barra
    # de progreso no se aplicaba y —peor— la columna de dinero perdia su `$%,d`, o sea
    # que v468 reintrodujo ahi el fallo de v399 (el importe sin separador de miles).
    _colcfg = {"Avance": st.column_config.ProgressColumn(
        t("Progress"), min_value=0, max_value=100, format="%d%%")}
    if _hay_costo:
        # v571 · con céntimos, como el resto de tablas de dinero (Expenses, Invoices): salía
        # en dólares enteros (`round(…, 0)` + `$%,d`).
        _colcfg["Costo"] = st.column_config.NumberColumn(t("Cost"), format="$%,.2f")
    # ⚠️ v575 · un toque en cualquier celda abre la ficha (era la casilla), y la clave lleva
    # GENERACIÓN: soltar el estado del widget (`pop`) no llega al navegador (trampa 31).
    _colcfg["Cliente"] = st.column_config.TextColumn(t("Client"), pinned=True)
    _gen = st.session_state.get("_cli_tbl_gen", 0)
    _ev = st.dataframe(
        df, width="stretch", hide_index=True,
        on_select="rerun", selection_mode="single-cell", key=f"cli_tbl_{_gen}",
        column_config=tabla.cfg(None, _colcfg),
    )
    _s = getattr(_ev, "selection", None)
    _sr = [c[0] for c in (getattr(_s, "cells", None) or [])] or list(getattr(_s, "rows", None) or [])
    if _sr and 0 <= _sr[0] < len(rows):
        st.session_state["_cli_tbl_gen"] = _gen + 1
        st.session_state["_cli_open"] = rows[_sr[0]]["key"]
        st.rerun()

    _nuevo_cliente_form(grupo)


# ── Detalle de un cliente ────────────────────────────────────────
def _detalle_cliente(grupo, key):
    if st.button(t(":material/arrow_back: Back to clients"), key="cli_back"):
        st.session_state.pop("_cli_open", None)
        st.rerun()

    fichas = C.list_clientes(grupo)
    fichas_by_norm = {_norm(f.get("Name")): f for f in fichas}
    fichas_by_id   = {str(f.get("ID", "")): f for f in fichas}
    f = fichas_by_norm.get(key, {})
    cid = str(f.get("ID", ""))
    proys = [p for p in P.list_projects(grupo=grupo) if C.es_del_cliente(p, cid, key)]
    disp = f.get("Name") or (proys[0].get("Client") if proys else key)

    st.markdown(f"## :material/apartment: {disp}")
    if not f:
        st.info(t(":material/info: This client **has no record yet** — it comes from its projects. Fill in the contact below and save to create the record (and be able to link projects)."))

    izq, der = st.columns([3, 2])

    # Ficha de contacto (crea si no existe, edita si existe)
    with izq:
        st.markdown(t("#### :material/contact_page: Contact record"))
        with st.form(f"cli_form_{key}"):
            _con = st.text_input(t("Contact person"), value=f.get("ContactName", ""))
            cc = st.columns(2)
            _tel  = cc[0].text_input(t("Phone"), value=f.get("Phone", ""))
            _mail = cc[1].text_input(t("Email"), value=f.get("Email", ""))
            _dir  = st.text_input(t("Address"), value=f.get("Address", ""))
            _notas = st.text_area(t("Notes"), value=f.get("Notes", ""), height=110)
            _save = st.form_submit_button(t(":material/save: Save record"), type="primary")
        if _save:
            campos = {"ContactName": _con, "Phone": _tel, "Email": _mail,
                      "Address": _dir, "Notes": _notas}
            if cid:
                ok, msg = C.update_cliente(cid, campos)
            else:
                ok, msg = C.create_cliente(grupo, disp, _con, _tel, _mail, _dir,
                                           _notas, creado_por=_creado_por())
            if ok:
                flash.exito(t("Record saved."))
                st.rerun()
            else:
                st.error(msg)
        if f.get("Address"):
            st.markdown(maps.maps_link_md(f.get("Address"), t("See the address on the map")))

    # Resumen
    with der:
        st.markdown(t("#### :material/insights: Summary"))
        horas   = P.project_hours_bulk(grupo)
        _con_al = alerts.is_configured()
        alarmas = alerts.open_counts_all() if _con_al else {}
        _con_gx = expenses.is_configured()
        costos  = ({str(r["id"]): _num(r.get("total")) for r in expenses.group_expenses(grupo)["proyectos"]}
                   if _con_gx else {})
        activos, av, hrs, cost, al = _agregados(proys, horas, alarmas, costos)
        _cifras_cliente(key, len(proys), activos, av, hrs, cost, al, _con_gx, _con_al)
        if cid:
            # v340: archivar y RESTAURAR. Antes solo se podía archivar y el cliente
            # desaparecía sin vuelta atrás.
            _ficha = C.get_cliente(cid)
            _archivado = str(_ficha.get("Active", "SI")).upper() in ("NO", "FALSE", "0")
            if _archivado:
                st.warning(t(":material/archive: This record is **archived**: it does not show in the list unless you tick «Show archived ones too»."))
                if st.button(t(":material/restore: Restore this record"),
                             key=f"cli_rest_{cid}", type="primary"):
                    ok, msg = C.set_activo(cid, True)
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()
            else:
                with st.expander(t(":material/archive: Archive client"), key=f"exp_cli_arch_{cid}"):
                    st.caption(t("It stops being listed; its projects are untouched. To see it again, tick «Show archived ones too» in the list."))
                    if st.button(t("Archive this record"), key=f"cli_arch_{cid}"):
                        C.set_activo(cid, False)
                        st.session_state.pop("_cli_open", None)
                        st.rerun()

    # v571 · lo que abre una cifra del resumen, a TODO el ancho (la columna es estrecha)
    _desglose_obras(key, proys, horas, costos, alarmas, _con_gx, _con_al)

    # Proyectos del cliente (ancho completo, clickeables)
    st.markdown(t("#### :material/folder: Projects for this client"))
    if not proys:
        st.caption(t("No linked projects yet."))
    else:
        cols = st.columns(2)
        for i, p in enumerate(sorted(proys, key=lambda x: str(x.get("Name", "")).lower())):
            pid = str(p.get("ID", ""))
            # v571 · el estado es un DATO de la hoja: se muestra con `etiqueta` (salía crudo)
            _lbl = f"**{p.get('Name', '')}** · {_etq(p.get('Status', ''))} · {int(_num(p.get('Progress')))}%"
            if cols[i % 2].button(_lbl, key=f"cli_prj_{pid}", width="stretch"):
                st.session_state["_prjsel_pending"] = pid
                st.session_state["_admin_nav_pending"] = ("proyectos", "📊 Proyectos")
                st.rerun()

    # Vincular más proyectos (necesita ficha con ID)
    if cid:
        otros = [p for p in P.list_projects(grupo=grupo) if not C.es_del_cliente(p, cid, key)]
        if otros:
            with st.expander(t(":material/link: Link other projects to this client"), key=f"exp_cli_link_{cid}"):
                st.caption(t("Useful if the project has different text in «Client» or was left unlinked."))
                _opts = {f"{p.get('Name', '')} ({p.get('ID', '')})": str(p.get("ID", ""))
                         for p in otros}
                _sel = st.multiselect(t("Projects to link"), list(_opts.keys()),
                                      key=f"cli_link_{cid}")
                if st.button(t(":material/link: Link selected"), key=f"cli_linkbtn_{cid}"):
                    if _sel:
                        for _lbl in _sel:
                            P.update_project(_opts[_lbl], {"ClientID": cid, "Client": disp})
                        flash.exito(t("{n} project(s) linked.", n=len(_sel)))
                        st.rerun()
                    else:
                        st.warning(t("Choose at least one project."))

    # ── Estado de cuenta: facturas del cliente (v259) ──
    from core import invoices as INV
    if cid and INV.is_configured():
        # ⚠️ v570 · las cifras, el filtro y la tabla son los de Invoices (`invoices_ui`):
        # esta era una COPIA que se quedó atrás — fecha ISO, «Nº» sin traducir, casillas,
        # dólares truncados (`%,d`), sin vencimiento ni saldo, y cifras que no se tocaban.
        from core import invoices_ui as IU
        st.markdown(t("#### :material/receipt: Invoicing"))
        _facs = INV.list_facturas(grupo, cid)
        IU.cifras_cobro(_facs, "clf")
        if _facs:
            _fr = IU.filtrar(_facs, "clf", f"cpxseg_clf_filt_{cid}")
            if not _fr:
                st.caption(t("No invoices in this filter."))
            else:
                _fsel = IU.tabla_facturas(_fr, f"cli_facs_{cid}", con_cliente=False)
                if _fsel:
                    st.session_state["_fac_open"] = str(_fsel.get("ID", ""))
                    st.session_state["_admin_nav_pending"] = ("finanzas", "🧾 Facturas")
                    st.rerun()
        else:
            st.caption(t("No invoices yet."))
        if st.button(t(":material/add_circle: New invoice for this client"), key=f"cli_newfac_{cid}"):
            st.session_state["_fac_nueva"] = True
            st.session_state["fac_cli"] = disp   # preselecciona el cliente en el form de factura
            st.session_state["_admin_nav_pending"] = ("finanzas", "🧾 Facturas")
            st.rerun()


# ── Alta de cliente ──────────────────────────────────────────────
def _nuevo_cliente_form(grupo):
    with st.expander(t(":material/add_circle: New client"), key="exp_cli_new"):
        with st.form("cli_nuevo"):
            _nom = st.text_input(t("Client name *"))
            cc = st.columns(2)
            _con = cc[0].text_input(t("Contact person"))
            _tel = cc[1].text_input(t("Phone"))
            cc2 = st.columns(2)
            _mail = cc2[0].text_input(t("Email"))
            _dir  = cc2[1].text_input(t("Address"))
            _notas = st.text_area(t("Notes"), height=80)
            _crear = st.form_submit_button(t(":material/add: Create client"), type="primary")
        if _crear:
            ok, msg = C.create_cliente(grupo, _nom, _con, _tel, _mail, _dir, _notas,
                                       creado_por=_creado_por())
            if ok:
                flash.exito(t("Client created."))
                st.session_state["_cli_open"] = _norm(_nom)
                st.rerun()
            else:
                st.error(msg)
