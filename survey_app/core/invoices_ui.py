"""🧾 Facturas — cuentas por cobrar (Fase 2 del módulo financiero).

Lista de facturas → detalle (líneas, cobros, estado). "Nueva factura": eliges un
cliente y, opcional, un proyecto (o todos), precarga las líneas con lo pendiente
de facturar (ingreso estimado − ya facturado) y las editas libremente antes de
emitir. Impuesto (GST/IVA) con el default del grupo, editable.
"""
import pandas as pd

from core.i18n import t, d
import streamlit as st

from core import flash

from core import tenant
from core import auth, clock
from core import clientes as C
from core import invoices as I
from core import projects as P
from core.num import num as _num


def _creado_por() -> str:
    a = st.session_state.get("auth") or {}
    return str(a.get("usuario", "") or a.get("nombre", ""))


_EST_FMT = {
    "pendiente": ":gray[:material/schedule:] pendiente",
    "parcial":   ":orange[:material/payments:] parcial",
    "cobrada":   ":green[:material/check_circle:] cobrada",
    "vencida":   ":red[:material/warning:] vencida",
    "anulada":   ":gray[:material/block:] anulada",
}


def render_facturas(grupo):
    # ⚠️ SIN cabecera propia: `home_ui._sub_header` ya pinta «Finanzas · X» encima.
    # Era el 5º título duplicado de la app (v212, v291, v314, v319 y este barrido).
    if not I.is_configured():
        st.info(t(":material/info: Configure Google Sheets to manage invoices."))
        return
    if st.session_state.get("_fac_nueva"):
        _nueva_factura(grupo)
        return
    if st.session_state.get("_fac_open"):
        _detalle_factura(grupo, st.session_state["_fac_open"])
        return

    facturas = I.list_facturas(grupo)
    # Totales del grupo (cuentas por cobrar)
    _fac = sum(_num(f.get("Total")) for f in facturas if str(f.get("Estado", "")).lower() != "anulada")
    _cob = sum(_num(f.get("Cobrado")) for f in facturas if str(f.get("Estado", "")).lower() != "anulada")
    _venc = sum(_num(f.get("Total")) - _num(f.get("Cobrado"))
                for f in facturas if I.estado_cobro(f) == "vencida")
    c = st.columns(4)
    c[0].metric(t("Invoiced"), f"${_fac:,.0f}")
    c[1].metric(t("Collected"), f"${_cob:,.0f}")
    c[2].metric(t("Outstanding"), f"${_fac - _cob:,.0f}")
    c[3].metric(t("Overdue"), f"${_venc:,.0f}")

    if st.button(t(":material/add_circle: New invoice"), type="primary", key="fac_new_btn"):
        st.session_state["_fac_nueva"] = True
        st.rerun()

    if not facturas:
        st.caption(t("No invoices yet. Create the first one with «New invoice»."))
        return

    st.caption(t("Tap an invoice to see the detail and record payments."))
    _rows = sorted(facturas, key=lambda f: str(f.get("Creado", "")), reverse=True)
    df = pd.DataFrame([{
        "Nº":        str(f.get("Numero", "")),
        "Cliente":   str(f.get("ClienteNombre", "") or "—"),
        "Fecha":     str(f.get("Fecha", "")),
        "Vence":     str(f.get("Vencimiento", "") or "—"),
        "Total":     round(_num(f.get("Total")), 0),
        "Cobrado":   round(_num(f.get("Cobrado")), 0),
        "Pendiente": round(_num(f.get("Total")) - _num(f.get("Cobrado")), 0),
        "Estado":    I.estado_cobro(f),
    } for f in _rows])
    _ev = st.dataframe(
        df, width="stretch", hide_index=True,
        on_select="rerun", selection_mode="single-row", key="fac_tbl",
        column_config={
            "Total":     st.column_config.NumberColumn(t("Total"), format="$%,d"),
            "Cobrado":   st.column_config.NumberColumn(t("Collected"), format="$%,d"),
            "Pendiente": st.column_config.NumberColumn(t("Outstanding"), format="$%,d"),
        })
    _sr = list(_ev.selection.rows)
    if _sr:
        st.session_state["_fac_open"] = str(_rows[_sr[0]].get("ID", ""))
        st.session_state.pop("fac_tbl", None)
        st.rerun()


# ── Detalle de una factura ───────────────────────────────────────
def _detalle_factura(grupo, fid):
    if st.button(t(":material/arrow_back: Back to invoices"), key="fac_back"):
        st.session_state.pop("_fac_open", None)
        st.rerun()
    f = I.get_factura(fid)
    if not f:
        st.warning(t("Invoice not found."))
        st.session_state.pop("_fac_open", None)
        return
    # v351: `get_factura` busca por ID en TODA la hoja, sin mirar el grupo.
    if not tenant.exigir(f, "Esta factura"):
        st.session_state.pop("_fac_open", None)
        return

    total, cob = _num(f.get("Total")), _num(f.get("Cobrado"))
    est = I.estado_cobro(f)
    st.markdown(f"## :material/receipt_long: Invoice No. {f.get('Numero', '')}")
    st.markdown(f"**{f.get('ClienteNombre', '') or '—'}**  ·  {_EST_FMT.get(est, est)}")

    izq, der = st.columns([3, 2])
    with izq:
        st.markdown(t("#### :material/list: Lines"))
        _ln = I.lineas_de(f)
        if _ln:
            st.dataframe(pd.DataFrame([{
                "Concepto": str(x.get("concepto", "")),
                "Importe":  round(_num(x.get("importe")), 2),
            } for x in _ln]), width="stretch", hide_index=True,
                column_config={"Importe": st.column_config.NumberColumn(t("Amount"), format="$%,.2f")})
        _imp_pct = _num(f.get("ImpuestoPct"))
        from core import theme as _T                      # v309: escapa el `$` (LaTeX)
        st.markdown(f"Subtotal: **{_T.dinero(_num(f.get('Subtotal')))}**  ·  "
                    f"Tax ({_imp_pct:.0f}%): **{_T.dinero(_num(f.get('Impuesto')))}**  ·  "
                    f"Total: **{_T.dinero(total)}**")
        if str(f.get("Nota", "")).strip():
            st.caption(f"Note: {f.get('Nota')}")
        try:
            from core import invoice_pdf
            _cli = C.get_cliente(str(f.get("ClienteID", ""))) if f.get("ClienteID") else {}
            _pdf = invoice_pdf.generate_invoice_pdf(f, _cli, grupo)
            st.download_button(t(":material/download: Download invoice (PDF)"), data=_pdf,
                               file_name=f"Factura_{f.get('Numero', '')}.pdf",
                               mime="application/pdf", key=f"fac_pdf_{fid}")
        except Exception as e:
            st.caption(f":material/warning: The PDF could not be generated: {e}")

    with der:
        st.markdown(t("#### :material/payments: Payments received"))
        # v309: el `help` llevaba DOS importes → perdía los símbolos de moneda.
        st.metric(t("Outstanding"), _T.dinero(total - cob),
                  help=f"Collected {_T.dinero(cob)} of {_T.dinero(total)}")
        if est != "anulada" and cob < total:
            with st.form(f"cob_{fid}"):
                _m = st.number_input(t("Record payment ($)"), min_value=0.0,
                                     max_value=float(round(total - cob, 2)),
                                     value=float(round(total - cob, 2)), step=50.0)
                _fch = st.date_input(t("Payment date"), value=clock.today())
                if st.form_submit_button(t(":material/check: Record payment"), type="primary"):
                    ok, msg = I.registrar_cobro(fid, _m, _fch.isoformat())
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()
        elif est == "cobrada":
            st.success(t(":material/check_circle: Invoice fully collected."))
        _cobros = I.cobros_de(f)
        if _cobros:
            st.caption(t("Payments recorded:"))
            for cb in _cobros:
                st.markdown(f"- {cb.get('fecha', '')}: **${_num(cb.get('monto')):,.2f}**")
        if str(f.get("Estado", "")).lower() != "anulada":
            with st.expander(t(":material/block: Void invoice")):
                st.caption(t("It is taken out of accounts receivable. This cannot be undone."))
                if st.button(t("Void this invoice"), key=f"fac_anul_{fid}"):
                    I.anular(fid)
                    st.rerun()


# ── Nueva factura ────────────────────────────────────────────────
def _nueva_factura(grupo):
    if st.button(t(":material/arrow_back: Cancel"), key="fac_new_back"):
        st.session_state.pop("_fac_nueva", None)
        st.rerun()
    st.markdown(t("## :material/add_circle: New invoice"))

    fichas = C.list_clientes(grupo)
    if not fichas:
        st.info(t(":material/info: Create a client first in 👥 Contacts."))
        return
    _by_name = {c.get("Nombre", ""): c for c in fichas}
    cli_sel = st.selectbox(t(":material/contacts: Client"), list(_by_name.keys()), key="fac_cli")
    cli = _by_name.get(cli_sel, {})
    cid = str(cli.get("ID", ""))
    cnorm = C._norm(cli.get("Nombre"))

    # Proyectos del cliente (para precargar y para el desplegable de líneas)
    prjs = [p for p in P.list_projects(grupo=grupo) if C.es_del_cliente(p, cid, cnorm)]
    # ⚠️ v369: `list_projects` oculta los ARCHIVADOS (v149) y **archivar no es no-cobrar**:
    # lo normal es archivar al terminar y facturar después. Hasta ahora solo entraban por
    # el atajo desde la ficha del proyecto (v358); desde el alta manual eran inalcanzables.
    # Misma pieza que ya usan la cartera (v149), Contactos e Inventario (v340): casilla +
    # cuántas hay ocultas. Va ANTES del radio porque cambia sus opciones (regla v111).
    _arch = [p for p in P.list_projects(grupo=grupo, incluir_archivados=True)
             if C.es_del_cliente(p, cid, cnorm)
             and str(p.get("ID", "")) not in {str(x.get("ID", "")) for x in prjs}]
    if _arch:
        if st.checkbox(f":material/archive: Include archived sites ({len(_arch)})",
                       key="fac_ver_arch",
                       help=t("Archiving is not the same as not charging: the usual thing is to archive when the job ends and invoice afterwards.")):
            prjs = prjs + _arch

    # ⚠️ v358: si el atajo desde el proyecto apunta a una obra que no está en la lista, se
    # añade igualmente — si no, el formulario se abría sin esa opción y la preselección no
    # hacía nada, en silencio. Se conserva aunque exista la casilla: el atajo debe
    # funcionar sin obligar a marcar nada.
    _peek = st.session_state.get("_fac_prj_pending")
    if _peek and str(_peek) not in {str(p.get("ID", "")) for p in prjs}:
        _extra = P.get_project(str(_peek)) or {}
        if _extra and str(_extra.get("Grupo", "")) == str(grupo):
            prjs = prjs + [_extra]
    # ⚠️ v306: por ID, no por nombre. Antes el alcance y la línea de la factura se casaban
    # con `{Nombre: ID}`: con dos proyectos homónimos el radio mostraba DOS opciones
    # idénticas, el filtro casaba con AMBOS y el importe se enlazaba al proyecto
    # equivocado — es decir, se facturaba mal, no solo se veía mal.
    _lbl = P.etiqueta_proyectos(prjs)              # {ID: etiqueta única}
    # Se marca cuál está archivada: si no, en el radio son indistinguibles de las activas
    # y no se ve por qué aparece una obra que se creía cerrada.
    _ids_arch = {str(p.get("ID", "")) for p in _arch}
    _lbl = {k: (v + " · archivada" if k in _ids_arch else v) for k, v in _lbl.items()}
    _pid_by_lbl = {v: k for k, v in _lbl.items()}
    prj_names = [_lbl[str(p.get("ID", ""))] for p in prjs]

    # ⚠️ Al DESMARCAR la casilla, la opción elegida puede desaparecer. Un `st.radio` cuyo
    # valor guardado ya no está entre las opciones revienta (es el fallo que v358 evitó al
    # no preseleccionar una etiqueta inexistente). Se suelta ANTES de instanciarlo.
    if st.session_state.get("fac_scope") not in ["The whole client"] + prj_names:
        st.session_state.pop("fac_scope", None)

    # v357: atajo desde el proyecto. Llega el ID y AQUÍ se resuelve su etiqueta, que es
    # donde se conoce el conjunto con el que se calculó (v306). Se aplica ANTES de
    # instanciar el radio: escribir la clave de un widget ya creado revienta (v111).
    _av = st.session_state.pop("_fac_aviso_cli", None)
    if _av:
        st.warning(":material/contacts: That project has the client **" + str(_av)
                   + "**, which is not a :material/contacts: Contacts record. Choose the client by hand, or link the project to its record so the shortcut works next time.")
    _pend_pid = st.session_state.pop("_fac_prj_pending", None)
    if _pend_pid:
        _et = _lbl.get(str(_pend_pid))
        if _et in prj_names:
            st.session_state["fac_scope"] = _et
        else:
            # ⚠️ Antes, si el proyecto no estaba en la lista, `_et` era None y NO se
            # decía nada: el usuario acababa en «Todo el cliente» sin saber por qué.
            st.info(t(":material/info: That project could not be preselected for this client (check which client it is linked to). Choose the scope by hand."))
    _scope = st.radio(t("Scope"), ["The whole client"] + prj_names, horizontal=True, key="fac_scope")
    _scope_prjs = (prjs if _scope == "The whole client"
                   else [p for p in prjs if _lbl.get(str(p.get("ID", ""))) == _scope])

    # Precarga: una línea por proyecto con lo pendiente de facturar
    _pre = []
    for p in _scope_prjs:
        pend = I.pendiente_de_facturar(str(p.get("ID", "")), grupo, p)
        if pend > 0:
            _pre.append({"Concepto": f"{d('Works')} — {p.get('Nombre', '')}",
                         "Proyecto": _lbl.get(str(p.get("ID", "")), ""), "Importe": pend})
    if not _pre:
        _pre = [{"Concepto": "", "Proyecto": "(ninguno)", "Importe": 0.0}]

    st.caption(t("Invoice lines — edit, add or remove. The «Project» links the line so it is not invoiced twice."))
    _ed = st.data_editor(
        pd.DataFrame(_pre), num_rows="dynamic", width="stretch", key="fac_lineas",
        column_config={
            "Concepto": st.column_config.TextColumn(t("Item"), width="large"),
            "Proyecto": st.column_config.SelectboxColumn(
                t("Project"), options=["(ninguno)"] + prj_names, required=False),
            "Importe":  st.column_config.NumberColumn(t("Amount"), format="$%,.2f", min_value=0.0),
        })

    c1, c2, c3 = st.columns(3)
    _fecha = c1.date_input(t("Date"), value=clock.today(), key="fac_fecha")
    _venc = c2.date_input(t("Due date"), value=clock.today(), key="fac_venc")
    _imp = c3.number_input(t("Tax % (GST/VAT)"), min_value=0.0, max_value=100.0, step=1.0,
                           value=float(auth.group_tax_default(grupo)), key="fac_imp")
    _nota = st.text_input(t("Note (optional)"), key="fac_nota")

    # Vista previa de totales
    _lineas = []
    for _, r in _ed.iterrows():
        imp = _num(r.get("Importe"))
        con = str(r.get("Concepto", "")).strip()
        if imp == 0 and not con:
            continue
        pnom = str(r.get("Proyecto", ""))
        _lineas.append({"concepto": con, "importe": imp,
                        "proyecto_id": _pid_by_lbl.get(pnom, "")})
    _sub = round(sum(l["importe"] for l in _lineas), 2)
    _impv = round(_sub * _imp / 100.0, 2)
    # ⚠️ `theme.dinero` escapa el `$`: con dos importes en la misma línea Streamlit
    # renderizaba esto como una FÓRMULA LaTeX ilegible (v309).
    from core import theme as _T
    st.markdown(f"Subtotal **{_T.dinero(_sub)}**  ·  Tax **{_T.dinero(_impv)}**  ·  "
                f"Total **{_T.dinero(_sub + _impv)}**")

    if st.button(t(":material/receipt_long: Issue invoice"), type="primary", key="fac_emit"):
        if not _lineas:
            st.error(t("Add at least one line with an amount."))
            return
        ok, res = I.create_factura(
            grupo=grupo, cliente_id=cid, cliente_nombre=cli.get("Nombre", ""),
            lineas=_lineas, impuesto_pct=_imp, fecha=_fecha.isoformat(),
            vencimiento=_venc.isoformat(), nota=_nota, creado_por=_creado_por())
        if ok:
            st.session_state.pop("_fac_nueva", None)
            st.session_state["_fac_open"] = res
            st.rerun()
        else:
            st.error(res)
