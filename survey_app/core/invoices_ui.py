"""🧾 Facturas — cuentas por cobrar (Fase 2 del módulo financiero).

Lista de facturas → detalle (líneas, cobros, estado). "Nueva factura": eliges un
cliente y, opcional, un proyecto (o todos), precarga las líneas con lo pendiente
de facturar (ingreso estimado − ya facturado) y las editas libremente antes de
emitir. Impuesto (GST/IVA) con el default del grupo, editable.
"""
import pandas as pd
import streamlit as st

from core import auth, clock
from core import clientes as C
from core import invoices as I
from core import projects as P


def _num(v, d=0.0) -> float:
    try:
        return float(str(v).replace(",", "."))
    except Exception:
        return d


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
    st.markdown("## :material/receipt_long: Facturas")
    if not I.is_configured():
        st.info(":material/info: Configura Google Sheets para gestionar facturas.")
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
    c[0].metric("Facturado", f"${_fac:,.0f}")
    c[1].metric("Cobrado", f"${_cob:,.0f}")
    c[2].metric("Por cobrar", f"${_fac - _cob:,.0f}")
    c[3].metric("Vencido", f"${_venc:,.0f}")

    if st.button(":material/add_circle: Nueva factura", type="primary", key="fac_new_btn"):
        st.session_state["_fac_nueva"] = True
        st.rerun()

    if not facturas:
        st.caption("Aún no hay facturas. Crea la primera con «Nueva factura».")
        return

    st.caption("Toca una factura para ver el detalle y registrar cobros.")
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
        df, use_container_width=True, hide_index=True,
        on_select="rerun", selection_mode="single-row", key="fac_tbl",
        column_config={
            "Total":     st.column_config.NumberColumn("Total", format="$%d"),
            "Cobrado":   st.column_config.NumberColumn("Cobrado", format="$%d"),
            "Pendiente": st.column_config.NumberColumn("Pendiente", format="$%d"),
        })
    _sr = list(_ev.selection.rows)
    if _sr:
        st.session_state["_fac_open"] = str(_rows[_sr[0]].get("ID", ""))
        st.session_state.pop("fac_tbl", None)
        st.rerun()


# ── Detalle de una factura ───────────────────────────────────────
def _detalle_factura(grupo, fid):
    if st.button(":material/arrow_back: Volver a facturas", key="fac_back"):
        st.session_state.pop("_fac_open", None)
        st.rerun()
    f = I.get_factura(fid)
    if not f:
        st.warning("Factura no encontrada.")
        st.session_state.pop("_fac_open", None)
        return

    total, cob = _num(f.get("Total")), _num(f.get("Cobrado"))
    est = I.estado_cobro(f)
    st.markdown(f"## :material/receipt_long: Factura Nº {f.get('Numero', '')}")
    st.markdown(f"**{f.get('ClienteNombre', '') or '—'}**  ·  {_EST_FMT.get(est, est)}")

    izq, der = st.columns([3, 2])
    with izq:
        st.markdown("#### :material/list: Líneas")
        _ln = I.lineas_de(f)
        if _ln:
            st.dataframe(pd.DataFrame([{
                "Concepto": str(x.get("concepto", "")),
                "Importe":  round(_num(x.get("importe")), 2),
            } for x in _ln]), use_container_width=True, hide_index=True,
                column_config={"Importe": st.column_config.NumberColumn("Importe", format="$%.2f")})
        _imp_pct = _num(f.get("ImpuestoPct"))
        st.markdown(f"Subtotal: **${_num(f.get('Subtotal')):,.2f}**  ·  "
                    f"Impuesto ({_imp_pct:.0f}%): **${_num(f.get('Impuesto')):,.2f}**  ·  "
                    f"Total: **${total:,.2f}**")
        if str(f.get("Nota", "")).strip():
            st.caption(f"Nota: {f.get('Nota')}")
        try:
            from core import invoice_pdf
            _cli = C.get_cliente(str(f.get("ClienteID", ""))) if f.get("ClienteID") else {}
            _pdf = invoice_pdf.generate_invoice_pdf(f, _cli, grupo)
            st.download_button(":material/download: Descargar factura (PDF)", data=_pdf,
                               file_name=f"Factura_{f.get('Numero', '')}.pdf",
                               mime="application/pdf", key=f"fac_pdf_{fid}")
        except Exception as e:
            st.caption(f":material/warning: No se pudo generar el PDF: {e}")

    with der:
        st.markdown("#### :material/payments: Cobros")
        st.metric("Por cobrar", f"${total - cob:,.2f}", help=f"Cobrado ${cob:,.2f} de ${total:,.2f}")
        if est != "anulada" and cob < total:
            with st.form(f"cob_{fid}"):
                _m = st.number_input("Registrar cobro ($)", min_value=0.0,
                                     max_value=float(round(total - cob, 2)),
                                     value=float(round(total - cob, 2)), step=50.0)
                _fch = st.date_input("Fecha del cobro", value=clock.today())
                if st.form_submit_button(":material/check: Registrar cobro", type="primary"):
                    ok, msg = I.registrar_cobro(fid, _m, _fch.isoformat())
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()
        elif est == "cobrada":
            st.success(":material/check_circle: Factura cobrada por completo.")
        _cobros = I.cobros_de(f)
        if _cobros:
            st.caption("Cobros registrados:")
            for cb in _cobros:
                st.markdown(f"- {cb.get('fecha', '')}: **${_num(cb.get('monto')):,.2f}**")
        if str(f.get("Estado", "")).lower() != "anulada":
            with st.expander(":material/block: Anular factura"):
                st.caption("La saca de las cuentas por cobrar. No se puede deshacer.")
                if st.button("Anular esta factura", key=f"fac_anul_{fid}"):
                    I.anular(fid)
                    st.rerun()


# ── Nueva factura ────────────────────────────────────────────────
def _nueva_factura(grupo):
    if st.button(":material/arrow_back: Cancelar", key="fac_new_back"):
        st.session_state.pop("_fac_nueva", None)
        st.rerun()
    st.markdown("## :material/add_circle: Nueva factura")

    fichas = C.list_clientes(grupo)
    if not fichas:
        st.info(":material/info: Primero crea un cliente en 👥 Contactos.")
        return
    _by_name = {c.get("Nombre", ""): c for c in fichas}
    cli_sel = st.selectbox(":material/contacts: Cliente", list(_by_name.keys()), key="fac_cli")
    cli = _by_name.get(cli_sel, {})
    cid = str(cli.get("ID", ""))
    cnorm = C._norm(cli.get("Nombre"))

    # Proyectos del cliente (para precargar y para el desplegable de líneas)
    prjs = [p for p in P.list_projects(grupo=grupo) if C.es_del_cliente(p, cid, cnorm)]
    prj_names = [p.get("Nombre", "") for p in prjs]
    _pid_by_name = {p.get("Nombre", ""): str(p.get("ID", "")) for p in prjs}

    _scope = st.radio("Alcance", ["Todo el cliente"] + prj_names, horizontal=True, key="fac_scope")
    _scope_prjs = prjs if _scope == "Todo el cliente" else [p for p in prjs if p.get("Nombre", "") == _scope]

    # Precarga: una línea por proyecto con lo pendiente de facturar
    _pre = []
    for p in _scope_prjs:
        pend = I.pendiente_de_facturar(str(p.get("ID", "")), grupo, p)
        if pend > 0:
            _pre.append({"Concepto": f"Trabajos — {p.get('Nombre', '')}",
                         "Proyecto": p.get("Nombre", ""), "Importe": pend})
    if not _pre:
        _pre = [{"Concepto": "", "Proyecto": "(ninguno)", "Importe": 0.0}]

    st.caption("Líneas de la factura — edita, agrega o quita. El «Proyecto» enlaza la línea para "
               "no volver a facturarla.")
    _ed = st.data_editor(
        pd.DataFrame(_pre), num_rows="dynamic", use_container_width=True, key="fac_lineas",
        column_config={
            "Concepto": st.column_config.TextColumn("Concepto", width="large"),
            "Proyecto": st.column_config.SelectboxColumn(
                "Proyecto", options=["(ninguno)"] + prj_names, required=False),
            "Importe":  st.column_config.NumberColumn("Importe", format="$%.2f", min_value=0.0),
        })

    c1, c2, c3 = st.columns(3)
    _fecha = c1.date_input("Fecha", value=clock.today(), key="fac_fecha")
    _venc = c2.date_input("Vencimiento", value=clock.today(), key="fac_venc")
    _imp = c3.number_input("Impuesto % (GST/IVA)", min_value=0.0, max_value=100.0, step=1.0,
                           value=float(auth.group_tax_default(grupo)), key="fac_imp")
    _nota = st.text_input("Nota (opcional)", key="fac_nota")

    # Vista previa de totales
    _lineas = []
    for _, r in _ed.iterrows():
        imp = _num(r.get("Importe"))
        con = str(r.get("Concepto", "")).strip()
        if imp == 0 and not con:
            continue
        pnom = str(r.get("Proyecto", ""))
        _lineas.append({"concepto": con, "importe": imp,
                        "proyecto_id": _pid_by_name.get(pnom, "")})
    _sub = round(sum(l["importe"] for l in _lineas), 2)
    _impv = round(_sub * _imp / 100.0, 2)
    st.markdown(f"Subtotal **${_sub:,.2f}**  ·  Impuesto **${_impv:,.2f}**  ·  "
                f"Total **${_sub + _impv:,.2f}**")

    if st.button(":material/receipt_long: Emitir factura", type="primary", key="fac_emit"):
        if not _lineas:
            st.error("Agrega al menos una línea con importe.")
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
