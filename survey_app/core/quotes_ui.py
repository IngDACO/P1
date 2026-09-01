"""📄 Cotizaciones — armar el precio desde el catálogo (v353).

⚠️ SIN cabecera propia: `home_ui._sub_header` ya pinta «Finanzas · Cotizaciones».
"""
import pandas as pd

from core.i18n import t, etiqueta as _etq
import streamlit as st

from core import flash

from core import catalogo as CAT
from core import clock
from core import clientes as C
from core import quotes as Q
from core import tenant
from core import theme as T
from core.num import num as _num
from core import tabla

# ⚠️ SIN `t()`: se construye al IMPORTAR, cuando no hay sesión, así que la traducción
# quedaría congelada — el fallo de `invoices_ui._EST_FMT` (v449) y de otros cinco. Las
# CLAVES son el estado que guarda la hoja. El icono va aquí y la palabra la pone
# `_est_fmt()` al PINTAR, con `etiqueta()`, que ya sabe traducir un valor de negocio.
_EST_ICONO = {Q.BORRADOR: ":gray[:material/edit_note:]",
              Q.ENVIADA: ":blue[:material/send:]",
              Q.ACEPTADA: ":green[:material/check_circle:]",
              Q.RECHAZADA: ":gray[:material/block:]",
              Q.VENCIDA: ":red[:material/schedule:]"}


def _est_fmt(est) -> str:
    """El estado de la cotización, con su icono, en el idioma de la PANTALLA."""
    return f"{_EST_ICONO.get(str(est), '')} {_etq(str(est))}".strip()


def _creado_por() -> str:
    a = st.session_state.get("auth") or {}
    return str(a.get("usuario", "") or a.get("nombre", ""))


def render_cotizaciones(grupo):
    if not Q.is_configured():
        st.info(t(":material/info: Configure Google Sheets to create quotes."))
        return
    if st.session_state.get("_cot_nueva"):
        _nueva(grupo)
        return
    if st.session_state.get("_cot_open"):
        _detalle(grupo, st.session_state["_cot_open"])
        return

    r = Q.resumen(grupo)
    T.kpi_row([
        (t("Out with clients"), T.dinero(r["en_calle"], 0),
         f"{r['por_estado'].get(Q.ENVIADA, 0)} sent, awaiting reply", T.AMBAR),
        (t("Won"), T.dinero(r["ganado"], 0),
         f"{r['por_estado'].get(Q.ACEPTADA, 0)} accepted", T.VERDE),
        # ⚠️ sin cotizaciones decididas la conversión NO es 0%: es que aún no se puede
        # calcular. Un 0% ahí sería la trampa de v320 («sin asignar» que mentía).
        (t("Conversion"), f"{r['conversion']:.0f}%" if r["conversion"] is not None else "—",
         t("of those decided") if r["conversion"] is not None else t("none decided yet")),
        (t("Quotes"), str(r["n"]), f"{r['por_estado'].get(Q.VENCIDA, 0)} expired"),
    ])

    if st.button(t(":material/add_circle: New quote"), type="primary", key="cot_new_btn"):
        st.session_state["_cot_nueva"] = True
        st.rerun()

    cots = Q.list_cotizaciones(grupo)
    if not cots:
        st.caption(t("No quotes yet. Start with «New quote» — the items come from :material/sell: Catalogue."))
        return

    _venc = [c for c in cots if Q.estado_de(c) == Q.VENCIDA]
    if _venc:
        st.warning(":material/schedule: **" + str(len(_venc)) + " expired quote(s)** with no answer: " + " · ".join(
                       f"{c.get('ClienteNombre','')} ({T.dinero(c.get('Total'), 0)})"
                       for c in _venc[:5])
                   + ". Issue a new version if it still stands.")

    st.caption(t("Tap a quote to see the detail, the PDF and record the outcome."))
    df = pd.DataFrame([{
        "Nº": str(c.get("Numero", "")) + (f" v{int(_num(c.get('Version'), 1))}"
                                          if _num(c.get("Version"), 1) > 1 else ""),
        "Cliente": c.get("ClienteNombre", "") or "—",
        "Fecha": c.get("Fecha", ""),
        "Vence": c.get("Validez", "") or "—",
        "Total": round(_num(c.get("Total")), 2),
        "Margin": round(_num(c.get("MargenPct")), 1),
        "Estado": _etq(Q.estado_de(c)),
    } for c in cots])
    _ev = st.dataframe(df, width="stretch", hide_index=True,
                       on_select="rerun", selection_mode="single-row", key="cot_tbl",
                       column_config=tabla.cfg(None, {
                           "Total": st.column_config.NumberColumn(t("Total"), format="$%,.2f"),
                           "Margin": st.column_config.NumberColumn(t("Margin"), format="%.1f%%")}))
    _sr = list(_ev.selection.rows)
    if _sr and _sr[0] < len(cots):
        st.session_state["_cot_open"] = str(cots[_sr[0]].get("ID", ""))
        st.session_state.pop("cot_tbl", None)
        st.rerun()


# ── Nueva cotización ─────────────────────────────────────────────
def _editor_lineas(grupo, key: str, lineas: list) -> list:
    """Selector del catálogo + tabla editable (cantidad y **margen por línea**)."""
    from core import auth
    items = CAT.list_items(grupo)
    if not items:
        st.warning(t(":material/sell: The catalogue is empty. Add products and services in :material/sell: Catalogue before quoting."))
        return lineas
    etq = CAT.etiqueta_items(items)          # v306: el ID solo si el nombre se repite
    _sel = st.multiselect(t("Add from the catalogue"), list(etq),
                          format_func=lambda i: etq.get(i, i), key=f"{key}_sel",
                          help=t("Choose the items; then adjust quantity and margin."))
    if _sel and st.button(t(":material/add: Add to the quote"), key=f"{key}_add"):
        _m = auth.group_margin_default(grupo)
        _ya = {l.get("catalogo_id") for l in lineas}
        for cid in _sel:
            if cid in _ya:
                continue
            lineas.append(Q.linea_de(CAT.get_item(cid), 1, _m))
        st.session_state[f"{key}_lineas"] = lineas
        st.rerun()

    if not lineas:
        st.caption(t("No lines yet."))
        return lineas

    st.markdown(t("**Lines** — enter **how much you want to make** on each item; the margin % and the price follow on their own"))
    ed = st.data_editor(
        pd.DataFrame([{
            "Concepto": l.get("concepto", ""),
            "Cant.": _num(l.get("cantidad")),
            "Costo": _num(l.get("costo_total")),
            "Ganancia $": Q.ganancia_de(l),
            "Margen %": _num(l.get("margen_pct")),
            "Precio": _num(l.get("precio_total")),
            "Quitar": False,
        } for l in lineas]),
        hide_index=True, width="stretch", key=f"{key}_ed",
        # ⚠️ v355: lo único que se teclea del precio es la GANANCIA. El margen y el
        # precio son consecuencia, y se muestran bloqueados para que quede claro.
        disabled=["Concepto", "Costo", "Margen %", "Precio"],
        column_config=tabla.cfg(None, {
            "Costo": st.column_config.NumberColumn(t("Cost"), format="$%,.2f",
                                                   help=t("What it costs you. The client does not see this.")),
            "Ganancia $": st.column_config.NumberColumn(
                t("Profit $"), format="$%,.2f", min_value=0.0,
                help=t("How much you want to make on this item. The margin % is worked out for you.")),
            "Margen %": st.column_config.NumberColumn(t("Margin %"), format="%.1f%%",
                                                      help=t("Worked out as profit ÷ cost.")),
            "Precio": st.column_config.NumberColumn(t("Price"), format="$%,.2f",
                                                    help=t("Cost + profit. This is what the client sees.")),
            "Cant.": st.column_config.NumberColumn(t("Qty"), min_value=0.0)}))

    # ⚠️ La cantidad se reaplica sobre el artículo del catálogo (el costo depende de
    # ella); la ganancia, sobre el costo ya congelado.
    nuevas = []
    for i, l in enumerate(lineas):
        if i >= len(ed) or bool(ed.iloc[i]["Quitar"]):
            continue
        cant, gan = _num(ed.iloc[i]["Cant."]), _num(ed.iloc[i]["Ganancia $"])
        if cant <= 0:
            continue
        # ⚠️ v356: se escala sobre el costo unitario CONGELADO, sin volver al catálogo.
        # Antes se reconstruía desde el artículo, así que tocar una celda adoptaba en
        # silencio los precios nuevos. Adoptarlos es ahora un botón explícito.
        nuevas.append(Q.escalar(l, cant, ganancia=gan))
    return nuevas


def _nueva(grupo):
    from core import auth
    if st.button(t(":material/arrow_back: Cancel"), key="cot_new_back"):
        for k in ("_cot_nueva", "new_lineas", "new_sel", "cot_new_cli",
                  "cot_new_cli_nom", "cot_new_cli_cto",
                  "cot_new_cli_tel", "cot_new_cli_mail"):
            st.session_state.pop(k, None)
        st.rerun()
    st.markdown(t("## :material/request_quote: New quote"))

    # ⚠️ v420: el cliente se puede crear AQUÍ. Antes, si era nuevo, había que salir a
    # Contactos, darlo de alta y volver a empezar la cotización — y si no había NINGÚN
    # cliente, esta pantalla ni siquiera dejaba entrar (`return`), así que el primer
    # presupuesto de una instalación nueva era imposible sin pasar antes por otra
    # sección. Cotizar es lo primero que se hace con un cliente nuevo: pedirle la ficha
    # de antemano es el orden al revés.
    fichas = C.list_clientes(grupo)
    _NUEVO = "➕ New client"
    _map = {f"{f.get('Nombre','')}": f for f in fichas}
    _cli = st.selectbox(t("Client"), list(_map) + [_NUEVO], key="cot_new_cli",
                        index=len(_map) if not fichas else 0)
    _nuevo_cli = {}
    if _cli == _NUEVO:
        with st.container(border=True):
            st.caption(t(":material/person_add: Their record will be created in Contacts when the quote is saved, and linked to it."))
            n1, n2 = st.columns(2)
            _nuevo_cli["nombre"] = n1.text_input(t("Client name *"),
                                                 key="cot_new_cli_nom")
            _nuevo_cli["contacto"] = n2.text_input(t("Contact person"),
                                                   key="cot_new_cli_cto")
            _nuevo_cli["telefono"] = n1.text_input(t("Phone"), key="cot_new_cli_tel")
            _nuevo_cli["email"] = n2.text_input(t("Email"), key="cot_new_cli_mail")

    lineas = st.session_state.get("new_lineas", [])
    lineas = _editor_lineas(grupo, "new", lineas)
    st.session_state["new_lineas"] = lineas

    imp = st.number_input(t("Tax %"), min_value=0.0, step=1.0,
                          value=float(auth.group_tax_default(grupo)), key="cot_new_imp",
                          help=t("Taken from the company default."))
    nota = st.text_area(t("Notes for the client (optional)"), key="cot_new_nota")

    if lineas:
        _tot = Q.totales(lineas, imp)
        _totales_html(_tot, imp)
        if st.button(t(":material/save: Create quote"), type="primary",
                     key="cot_new_save", width="stretch"):
            # ⚠️ v420: si el cliente es nuevo, su ficha se crea PRIMERO y solo si sale
            # bien se crea la cotización. Al revés quedaría una cotización sin
            # `ClienteID`, y ese enlace es el que usa `aceptar_y_crear_proyecto` (v354)
            # para que la obra nazca con su cliente — sin él, luego facturarla no
            # encuentra la ficha (el fallo que costó v357).
            if _cli == _NUEVO:
                _nom = str(_nuevo_cli.get("nombre", "")).strip()
                if not _nom:
                    st.error(t("The client name is required."))
                    return
                _ok_c, _res = C.create_cliente(
                    grupo, _nom, contacto=_nuevo_cli.get("contacto", ""),
                    telefono=_nuevo_cli.get("telefono", ""),
                    email=_nuevo_cli.get("email", ""), creado_por=_creado_por())
                if _ok_c:
                    f = {"ID": _res, "Nombre": _nom}
                else:
                    # ⚠️ El nombre ya existía: `create_cliente` no deja duplicados por
                    # grupo. En vez de dejar al usuario en un callejón —con la
                    # cotización entera escrita y sin poder guardarla—, se REUTILIZA esa
                    # ficha y se dice. Es coherente con la regla que la propia función
                    # impone: dentro de un grupo, ese nombre es UNO.
                    _ya = next((x for x in C.list_clientes(grupo, incluir_inactivos=True)
                                if C._norm(x.get("Nombre")) == C._norm(_nom)), None)
                    if not _ya:
                        st.error(f"The client could not be created: {_res}")
                        return
                    f = _ya
                    st.info(f":material/info: A record already existed for **{_nom}**; "
                            f"the quote is linked to that one.")
            else:
                f = _map[_cli]
            ok, msg = Q.crear(grupo, f.get("ID", ""), f.get("Nombre", ""), lineas,
                              impuesto_pct=imp, nota=nota, creado_por=_creado_por())
            if ok:
                for k in ("_cot_nueva", "new_lineas", "new_sel", "cot_new_cli",
                  "cot_new_cli_nom", "cot_new_cli_cto",
                  "cot_new_cli_tel", "cot_new_cli_mail"):
                    st.session_state.pop(k, None)
                st.session_state["_cot_open"] = msg
                st.rerun()
            else:
                st.error(msg)


def _totales_html(_tot: dict, imp_pct):
    """Totales + lo que el cliente NO ve (costo y ganancia), que es lo que te interesa."""
    T.kpi_row([
        (t("Subtotal"), T.dinero(_tot["subtotal"], 0), t("before tax")),
        (t("Tax"), T.dinero(_tot["impuesto"], 0), f"{_num(imp_pct):g}%"),
        (t("Total to client"), T.dinero(_tot["total"], 0), t("what they are charged"), T.AZUL),
        (t("Your profit"), T.dinero(_tot["ganancia"], 0),
         f"effective margin {_tot['margen_pct']:.1f}%", T.VERDE),
    ])
    if _tot["horas"]:
        st.caption(f":material/schedule: The quote includes **{_tot['horas']:g} service hours**. Once accepted "
                   "you can compare them against the hours clocked.")


# ── Detalle ──────────────────────────────────────────────────────
def _detalle(grupo, cid):
    if st.button(t(":material/arrow_back: Back to quotes"), key="cot_back"):
        st.session_state.pop("_cot_open", None)
        st.rerun()
    c = Q.get_cotizacion(cid)
    if not c:
        st.warning(t("Quote not found."))
        st.session_state.pop("_cot_open", None)
        return
    # v351: `get_cotizacion` busca por ID en toda la hoja, sin mirar el grupo.
    if not tenant.exigir(c, t("This quote")):
        st.session_state.pop("_cot_open", None)
        return

    est = Q.estado_de(c)
    _ver = int(_num(c.get("Version"), 1))
    st.markdown(f"## :material/request_quote: {t('Quote No.')} {c.get('Numero', '')}"
                + (f"  ·  v{_ver}" if _ver > 1 else ""))
    st.markdown(f"**{c.get('ClienteNombre', '') or '—'}**  ·  {_est_fmt(est)}"
                f"  ·  {t('valid until')} {c.get('Validez', '') or '—'}"
                + (f"  ·  from {c.get('Origen')}" if c.get("Origen") else ""))

    lineas = Q.lineas_de(c)
    _tot = Q.totales(lineas, _num(c.get("ImpuestoPct")))

    if est == Q.BORRADOR:
        _des = Q.desactualizadas(c)
        if _des:
            _txt = " · ".join(
                str(d["linea"].get("concepto", "")) + ": "
                + T.dinero(d["linea"].get("costo_total"))
                + (" → " + T.dinero(d["costo_hoy"]) if d["costo_hoy"] is not None
                   else " (" + d["motivo"] + ")")
                for d in _des[:6])
            st.warning(":material/sync_problem: **The catalogue changed** since you built this quote: " + _txt + ". The quote's prices do NOT change on their own.")
            if st.button(t(":material/sync: Refresh prices from the catalogue"),
                         key="cot_upd_" + str(cid),
                         help=t("Brings today's costs across while keeping what you want to make on each line.")):
                ok, msg = Q.actualizar_precios(cid)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
        nuevas = _editor_lineas(grupo, f"ed{cid}", lineas)
        if nuevas != lineas:
            if st.button(t(":material/save: Save changes"), key=f"cot_save_{cid}",
                         type="primary"):
                ok, msg = Q.guardar_lineas(cid, nuevas)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
        _totales_html(Q.totales(nuevas, _num(c.get("ImpuestoPct"))), c.get("ImpuestoPct"))
    else:
        st.dataframe(pd.DataFrame([{
            "Concepto": l.get("concepto", ""),
            "Cant.": _num(l.get("cantidad")),
            "Precio": round(_num(l.get("precio_total")), 2),
        } for l in lineas]), hide_index=True, width="stretch",
            column_config=tabla.cfg(None, {"Precio": st.column_config.NumberColumn(t("Price"), format="$%,.2f")}))
        _totales_html(_tot, c.get("ImpuestoPct"))

    # ── Acciones según el estado ─────────────────────────────────
    st.markdown("---")
    a1, a2, a3 = st.columns(3)
    if est == Q.BORRADOR:
        if a1.button(t(":material/send: Mark as sent"), key=f"cot_env_{cid}",
                     type="primary", width="stretch"):
            ok, msg = Q.set_estado(cid, Q.ENVIADA)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()
    elif est in (Q.ENVIADA, Q.VENCIDA):
        if a1.button(t(":material/check_circle: The client accepted it"), key=f"cot_ok_{cid}",
                     type="primary", width="stretch"):
            ok, msg = Q.set_estado(cid, Q.ACEPTADA)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()
        if a2.button(t(":material/block: They rejected it"), key=f"cot_no_{cid}",
                     width="stretch"):
            ok, msg = Q.set_estado(cid, Q.RECHAZADA)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()
    if est != Q.BORRADOR:
        if a3.button(t(":material/content_copy: New version"), key=f"cot_v2_{cid}",
                     width="stretch",
                     help=t("Clones this quote as a draft so you can change it. The current one is kept.")):
            ok, msg = Q.nueva_version(cid, creado_por=_creado_por())
            if ok:
                st.session_state["_cot_open"] = msg
                st.rerun()
            else:
                st.error(msg)

    # ── PDF ──────────────────────────────────────────────────────
    try:
        from core import quote_pdf
        cli = next((x for x in C.list_clientes(grupo, incluir_inactivos=True)
                    if str(x.get("ID", "")) == str(c.get("ClienteID", ""))), None)
        pdf = quote_pdf.generate_quote_pdf(c, cli, grupo)
        st.download_button(t(":material/download: Download quote (PDF)"), data=pdf,
                           file_name=f"Cotizacion_{c.get('Numero','')}.pdf",
                           mime="application/pdf", key=f"cot_pdf_{cid}")
    except Exception as e:
        st.warning(f":material/warning: The PDF could not be generated: {e}")

    # ── Fase 3: de cotización ganada a obra ──────────────────────
    if est == Q.ACEPTADA and not str(c.get("ProyectoID", "")).strip():
        _crear_proyecto(grupo, c, _tot)
    elif str(c.get("ProyectoID", "")).strip():
        _comparacion(cid, c)


def _crear_proyecto(grupo, c, _tot):
    """Aceptada y sin obra todavía: darla de alta con lo ya pactado."""
    st.markdown("---")
    st.markdown(t("### :material/construction: Turn it into a project"))
    st.caption(t("It starts with the client, the budget and the margin you have just quoted. From there the usual flow follows: costs, hours and invoice."))
    with st.form("cot_prj_" + str(c.get("ID"))):
        c1, c2 = st.columns(2)
        nombre = c1.text_input(t("Project name"),
                               value=str(c.get("ClienteNombre", "")) + " — Nº"
                                     + str(c.get("Numero", "")))
        tipo = c2.selectbox(t("Type"), ["Instalación", "Delivery", "Ripout", "Otro"],
                            format_func=_etq)
        c3, c4 = st.columns(2)
        ini = c3.date_input(t("Start date"), value=clock.today(grupo))
        ns = c4.number_input(t("Stops (NS)"), min_value=0, step=1, value=0,
                             help=t("Only an installation generates the standard schedule; with NS 0 the project starts with no activities."))
        ubic = st.text_input(t("Location (optional)"))
        st.info(":material/savings: Project budget: **"
                + T.dinero(_tot["costo"], 0) + "** — that is your quoted **cost**, not the price to the client (" + T.dinero(_tot["subtotal"], 0) + "). That way the over-budget alert fires when you are eating into the margin, not when you are already losing money.")
        if st.form_submit_button(t(":material/add_circle: Create the project"),
                                 type="primary", width="stretch"):
            ok, msg = Q.aceptar_y_crear_proyecto(
                c.get("ID"), nombre=nombre, tipo=tipo, fecha_inicio=ini,
                ns=ns, ubicacion=ubic, creado_por=_creado_por())
            if ok:
                flash.exito(t("Project") + " " + str(msg) + " " + t("created from this quote."))
                st.rerun()
            else:
                st.error(msg)


def _comparacion(cid, c):
    """Cotizado contra real: lo que hace que cotizar sirva para gestionar."""
    st.markdown("---")
    comp = Q.comparacion(cid)
    if not comp:
        st.caption("Linked to project " + str(c.get("ProyectoID")) + ".")
        return
    st.markdown(t("### :material/compare_arrows: Quoted vs. actual —") + " " + comp["proyecto"])

    def _tarj(etq, d, unidad=""):
        _col = T.VERDE if d["dif"] <= 0 else T.ROJO
        _sig = "+" if d["dif"] > 0 else ""
        _val = (("%g " % d["real"]) + unidad).strip() if unidad else T.dinero(d["real"], 0)
        _cot = (("%g " % d["cotizado"]) + unidad).strip() if unidad else T.dinero(d["cotizado"], 0)
        _pct = (" (" + _sig + ("%.0f" % d["pct"]) + "%)") if d["pct"] is not None else ""
        return (etq, _val, "cotizaste " + _cot + _pct, _col)

    # ⚠️ La GANANCIA no se compara «real vs cotizada» a mitad de obra: hasta terminar,
    # lo no gastado parece ganancia. Se muestra la PROYECCIÓN al ritmo actual (v144) y
    # solo se llama «real» cuando el proyecto está al 100%.
    _gc = comp["ganancia_cotizada"]
    if comp["terminado"]:
        _g, _lbl_g, _pie = comp["ganancia_real"], t("Actual profit"), t("job finished")
    elif comp["ganancia_proyectada"] is not None:
        _g, _lbl_g = comp["ganancia_proyectada"], t("Projected profit")
        _pie = "at the current rate · you quoted " + T.dinero(_gc, 0)
    else:
        _g, _lbl_g, _pie = None, t("Projected profit"), t("there is no progress and no cost yet")
    _cg = T.VERDE if (_g is not None and _g >= _gc) else (T.ROJO if _g is not None else None)
    T.kpi_row([
        _tarj(t("Hours"), comp["horas"], "h"),
        _tarj(t("Cost"), comp["costo"]),
        (t("Revenue"), T.dinero(comp["ingreso"], 0), t("what the client accepted")),
        (_lbl_g, T.dinero(_g, 0) if _g is not None else "—", _pie, _cg),
    ])
    if comp["costo_proyectado"] is not None:
        st.caption(":material/trending_up: At the current rate the job will cost "
                   + T.dinero(comp["costo_proyectado"], 0) + " against the "
                   + T.dinero(comp["costo"]["cotizado"], 0) + " " + t("quoted."))
    _av = comp["avance"]
    if comp["costo"]["dif"] > 0 and _av < 100:
        st.warning(":material/warning: " + t("You are at") + " **" + T.dinero(comp["costo"]["dif"], 0)
                   + " above** what was quoted, with the project at **"
                   + ("%.0f" % _av) + "%**. At this rate the final profit will be lower than quoted.")
    elif comp["costo"]["dif"] <= 0 and _av > 0:
        st.success(":material/check_circle: " + t("You are at") + " **"
                   + T.dinero(abs(comp["costo"]["dif"]), 0) + " below** what was quoted, with the project at " + ("%.0f" % _av) + "%.")
    if st.button(":material/folder: " + t("Open") + " " + comp["proyecto"], key="cot_prj_open_" + str(cid)):
        from core import home_ui
        st.session_state["_prjsel_pending"] = comp["proyecto_id"]
        st.session_state["_admin_open_proj"] = comp["proyecto_id"]
        home_ui.navegar("proyectos", "📊 Proyectos")
