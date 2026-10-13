"""🧾 Facturas — cuentas por cobrar (Fase 2 del módulo financiero).

Lista de facturas → detalle (líneas, cobros, estado). "Nueva factura": eliges un
cliente y, opcional, un proyecto (o todos), precarga las líneas con lo pendiente
de facturar (ingreso estimado − ya facturado) y las editas libremente antes de
emitir. Impuesto (GST/IVA) con el default del grupo, editable.
"""
import pandas as pd

from core.i18n import t, d, etiqueta as _etq
from datetime import timedelta as _timedelta

import streamlit as st

from core import flash

from core import tenant
from core import auth, clock
from core import clientes as C
from core import invoices as I
from core import projects as P
from core.num import num as _num
from core import tabla


def _creado_por() -> str:
    a = st.session_state.get("auth") or {}
    return str(a.get("usuario", "") or a.get("nombre", ""))


# ⚠️ Sin `t()`: este dict se construye al IMPORTAR el módulo, cuando todavía no hay
# sesión, así que la traducción quedaría CONGELADA en el idioma de ese instante (el
# fallo de `auth.SESION_OCUPADA`, v445 — y van cinco). Las CLAVES son además el DATO
# que devuelve `invoices.estado_cobro`. La traducción va en `_est_fmt()`, al pintar.
# ⚠️ v569 · las PALABRAS son las de `i18n.etiqueta` (pending · partial · collected ·
# overdue · voided), las mismas de la tabla, de Contacts y del PDF: el detalle decía
# «outstanding» / «paid» y la lista «pending» / «collected» (visto en el recorrido).
_EST_FMT = {
    "pendiente": (":gray[:material/schedule:]", "pending"),
    "parcial":   (":orange[:material/payments:]", "partial"),
    "cobrada":   (":green[:material/check_circle:]", "collected"),
    "vencida":   (":red[:material/warning:]", "overdue"),
    "anulada":   (":gray[:material/block:]", "voided"),
}
# v569 · en una TABLA no se pintan `:color[...]` ni `:material/…:` (salen literales): ahí
# el estado lleva un punto de color.
_EST_PUNTO = {"pendiente": "⚪", "parcial": "🟠", "cobrada": "🟢", "vencida": "🔴",
              "anulada": "⚫"}
# Filtro de la lista: ID interno → (estados que entran, rótulo)
_FILTROS = {"Todas": (None, "All"),
            "Pendientes": (("pendiente", "parcial", "vencida"), "Outstanding"),
            "Vencidas": (("vencida",), "Overdue"),
            "Cobradas": (("cobrada",), "Collected"),
            "Anuladas": (("anulada",), "Voided")}


def _est_fmt(est: str) -> str:
    """El estado de cobro, con su icono, en el idioma de la PANTALLA."""
    _ic, _tx = _EST_FMT.get(str(est), ("", str(est)))
    return f"{_ic} {t(_tx)}".strip()


def _est_celda(f) -> str:
    """El estado en una CELDA de tabla: punto de color + la etiqueta traducida (v569).
    ⚠️ Fuera del dict de la fila: verif_v452 mira que ninguna celda llame en crudo a lo
    que devuelve un DATO de la hoja."""
    return f"{_EST_PUNTO.get(I.estado_cobro(f), '')} " + _etq(I.estado_cobro(f))


def _dmy(iso) -> str:
    """«2026-10-13» → «13/10/2026» (v569: la lista, los cobros y el PDF iban en ISO)."""
    s = str(iso or "").strip()[:10]
    try:
        y, m, dd = s.split("-")
        return f"{int(dd):02d}/{int(m):02d}/{y}"
    except Exception:
        return s or "—"


def render_facturas(grupo):
    # ⚠️ SIN cabecera propia: `home_ui._sub_header` ya pinta «Finanzas · X» encima.
    # Era el 5º título duplicado de la app (v212, v291, v314, v319 y este barrido).
    if not I.is_configured():
        st.info(t(":material/info: Configure Google Sheets to manage invoices."))
        return
    # ⚠️ v569 · ACCIÓN DIFERIDA (trampa 37): anular escribe en la hoja; el botón solo
    # apunta y relanza, y se hace aquí, antes de pintar nada. Y se AVISA: antes la
    # factura se anulaba sin ningún mensaje.
    _anu = st.session_state.pop("_fac_anular", None)
    if _anu:
        _ok, _msg = I.anular(_anu)
        (flash.exito if _ok else flash.error)(_msg)
        # ⚠️ v570 · y RELANZA: la shell pinta los avisos (`flash.mostrar`) ANTES de la
        # sección, así que lo encolado aquí salía en el clic SIGUIENTE, ya en la lista
        # (visto en producción). Es lo que hacen Absences y Time fixes.
        st.rerun()
    if st.session_state.get("_fac_nueva"):
        _nueva_factura(grupo)
        return
    if st.session_state.get("_fac_open"):
        _detalle_factura(grupo, st.session_state["_fac_open"])
        return

    facturas = I.list_facturas(grupo)
    cifras_cobro(facturas, "fac")

    if st.button(t(":material/add_circle: New invoice"), type="primary", key="fac_new_btn"):
        st.session_state["_fac_nueva"] = True
        st.rerun()

    if not facturas:
        st.caption(t("No invoices yet. Create the first one with «New invoice»."))
        return

    _rows = filtrar(facturas, "fac", "cpxseg_fac_filt")
    if not _rows:
        st.caption(t("No invoices in this filter."))
        return
    st.caption(t("Tap an invoice to see the detail and record payments."))
    _sel = tabla_facturas(_rows, "fac_tbl")
    if _sel:
        st.session_state["_fac_open"] = str(_sel.get("ID", ""))
        st.rerun()


# ── Lo COMÚN a Invoices y a la ficha del cliente (v570) ──────────
# ⚠️ La tabla de facturas de la ficha del cliente era una COPIA de esta y se quedó atrás
# (ISO, «Nº» sin traducir, casillas, dólares truncados, sin vencimiento ni saldo): visto
# verificando v569. Ahora las dos pantallas pintan con estas tres funciones.
def _saldo(f) -> float:
    """Lo que falta por cobrar. ⚠️ v570 · una ANULADA no debe nada: la tabla le ponía
    «Outstanding $44.00» (el detalle y el PDF ya decían 0)."""
    if I.estado_cobro(f) == "anulada":
        return 0.0
    return round(_num(f.get("Total")) - _num(f.get("Collected")), 2)


def cifras_cobro(facturas, pref):
    """Las 4 cifras de cobro como tarjetas-BOTÓN (v569): cada una aplica su filtro a la
    lista de abajo (`filtrar` con el mismo `pref`). Las anuladas no cuentan."""
    from core import theme as _T
    _fac = sum(_num(f.get("Total")) for f in facturas if str(f.get("Status", "")).lower() != "anulada")
    _cob = sum(_num(f.get("Collected")) for f in facturas if str(f.get("Status", "")).lower() != "anulada")
    _venc = sum(_num(f.get("Total")) - _num(f.get("Collected"))
                for f in facturas if I.estado_cobro(f) == "vencida")
    _K = [("fac", t("Invoiced"), _T.dinero(_fac, 0), t("all invoices"), "Todas"),
          ("cob", t("Collected"), _T.dinero(_cob, 0), t("received so far"), "Cobradas"),
          ("pen", t("Outstanding"), _T.dinero(_fac - _cob, 0), t("still to collect"), "Pendientes"),
          ("ven", t("Overdue"), _T.dinero(_venc, 0), t("past the due date"), "Vencidas")]
    # 2 por fila bajo 700 px (`@container`, el mismo reparto medido en Gastos, v568)
    _c = f".st-key-cpx_{pref}_kpis"
    _css = (f"<style>{_c}{{container-type:inline-size}}"
            f"@container (max-width:700px){{{_c} [data-testid='stHorizontalBlock']"
            f"{{flex-wrap:wrap!important}}{_c} [data-testid='stHorizontalBlock']"
            ">[data-testid='stColumn']{flex:0 1 calc(50% - 0.5rem)!important;"
            "min-width:calc(50% - 0.5rem)!important;width:calc(50% - 0.5rem)!important}}")
    if _venc > 0:
        _css += (f".st-key-cpxkpi_{pref}_ven button{{border-left-color:#c0392b!important}}"
                 f".st-key-cpxkpi_{pref}_ven button p:nth-child(2):not(:last-child)"
                 "{color:#c0392b!important}")
    st.markdown(_css + "</style>", unsafe_allow_html=True)
    with st.container(key=f"cpx_{pref}_kpis"):
        for _col, (_s, _l, _v, _pie, _fl) in zip(st.columns(4), _K):
            if _col.button(f"{_l}\n\n{_v}\n\n{_pie}", key=f"cpxkpi_{pref}_{_s}", width="stretch"):
                st.session_state[f"_{pref}_filt_pending"] = _fl
                st.rerun()


def filtrar(facturas, pref, clave):
    """All / Outstanding / Overdue / Collected / Voided, RECORDADO (`persist_state`), y
    las facturas que entran. La cifra pulsada (`cifras_cobro`) se aplica aquí, antes
    de crear el selector."""
    _pp = st.session_state.pop(f"_{pref}_filt_pending", None)
    if _pp in _FILTROS:
        st.session_state[clave] = _pp
    _filt = st.radio(t("Filter"), list(_FILTROS), format_func=lambda o: t(_FILTROS[o][1]),
                     horizontal=True, key=clave, label_visibility="collapsed",
                     persist_state="session")
    _entran = _FILTROS.get(_filt or "Todas", (None, ""))[0]
    return [f for f in facturas if _entran is None or I.estado_cobro(f) in _entran]


def tabla_facturas(facturas, clave, con_cliente=True):
    """La tabla de facturas; devuelve la TOCADA (o None) y quien llama decide adónde ir.
    `clave` lleva generación: soltar el estado del widget no llega al navegador
    (trampa 31) y al volver la tabla reabriría la misma factura."""
    _rows = sorted(facturas, key=lambda f: str(f.get("Created", "")), reverse=True)
    # ⚠️ v569 · lo que se mira primero, delante (la columna de estado salía cortada a 800
    # px con el menú), el Nº FIJADO, fechas DD/MM/YYYY y el estado con su punto de color.
    df = pd.DataFrame([{
        "Nº":        str(f.get("Number", "")),
        "Cliente":   str(f.get("ClientName", "") or "—"),
        "Estado":    _est_celda(f),
        "Outstanding": _saldo(f),
        "Vence":     _dmy(f.get("ExpiryDate")),
        "Total":     round(_num(f.get("Total")), 2),
        "Cobrado":   round(_num(f.get("Collected")), 2),
        "Fecha":     _dmy(f.get("Date")),
    } for f in _rows])
    if not con_cliente:
        df = df.drop(columns=["Cliente"])
    _gk = f"_{clave}_gen"
    _gen = st.session_state.get(_gk, 0)
    _ev = st.dataframe(
        df, width="stretch", hide_index=True,
        # v569 · un toque en cualquier celda abre la factura (antes, solo la casilla)
        on_select="rerun", selection_mode="single-cell", key=f"{clave}_{_gen}",
        column_config=tabla.cfg(None, {
            "Nº":        st.column_config.TextColumn(t("No."), pinned=True),
            "Estado":    st.column_config.TextColumn(t("Status")),
            "Vence":     st.column_config.TextColumn(t("Due")),
            "Fecha":     st.column_config.TextColumn(t("Date")),
            "Total":     st.column_config.NumberColumn(t("Total"), format="$%,.2f"),
            "Cobrado":   st.column_config.NumberColumn(t("Collected"), format="$%,.2f"),
            "Outstanding": st.column_config.NumberColumn(t("Outstanding"), format="$%,.2f"),
        }))
    _s = getattr(_ev, "selection", None)
    _sr = [c[0] for c in (getattr(_s, "cells", None) or [])] or list(getattr(_s, "rows", None) or [])
    if _sr and 0 <= _sr[0] < len(_rows):
        st.session_state[_gk] = _gen + 1
        return _rows[_sr[0]]
    return None


# ── Detalle de una factura ───────────────────────────────────────
def _detalle_factura(grupo, fid):
    if st.button(t(":material/arrow_back: Back to invoices"), key="fac_back"):
        st.session_state.pop("_fac_open", None)
        st.session_state.pop("_fac_anular_conf", None)
        st.rerun()
    f = I.get_factura(fid)
    if not f:
        st.warning(t("Invoice not found."))
        st.session_state.pop("_fac_open", None)
        return
    # v351: `get_factura` busca por ID en TODA la hoja, sin mirar el grupo.
    if not tenant.exigir(f, t("This invoice")):
        st.session_state.pop("_fac_open", None)
        return

    from core import theme as _T                          # v309: escapa el `$` (LaTeX)
    total, cob = _num(f.get("Total")), _num(f.get("Collected"))
    est = I.estado_cobro(f)
    _anulada = est == "anulada"
    st.markdown(t("## :material/receipt_long: Invoice No. {n}").replace("{n}", str(f.get("Number", ""))))
    # v569 · el cliente LLEVA a su ficha de Contacts (era texto)
    _cn = str(f.get("ClientName", "") or "")
    _c1, _c2 = st.columns([3, 2])
    if _cn and _c1.button(f":material/contacts: **{_cn}**", key=f"fac_cli_{fid}", type="tertiary"):
        st.session_state["_cli_open"] = C._norm(_cn)
        st.session_state.pop("_fac_open", None)
        st.session_state["_admin_nav_pending"] = ("contactos", None)
        st.rerun()
    _c2.markdown(_est_fmt(est))
    # ⚠️ v569 · CUÁNDO se emitió y CUÁNDO vence (no salía en ningún sitio: «overdue» sin
    # decir desde cuándo).
    _fecha = [t("Issued {f}").replace("{f}", _dmy(f.get("Date"))),
              t("due {v}").replace("{v}", _dmy(f.get("ExpiryDate")))]
    if est == "vencida":
        try:
            _dias = (clock.today(grupo) - pd.Timestamp(str(f.get("ExpiryDate"))[:10]).date()).days
            _fecha.append(":red[" + t("{n} days overdue").replace("{n}", str(_dias)) + "]")
        except Exception:
            pass
    st.caption(" · ".join(_fecha))

    izq, der = st.columns([3, 2])
    with izq:
        st.markdown(t("#### :material/list: Lines"))
        _ln = I.lineas_de(f)
        if _ln:
            st.dataframe(pd.DataFrame([{
                "Concepto": str(x.get("concepto", "")),
                "Importe":  round(_num(x.get("importe")), 2),
            } for x in _ln]), width="stretch", hide_index=True,
                column_config=tabla.cfg(None, {"Importe": st.column_config.NumberColumn(t("Amount"), format="$%,.2f")}))
        _imp_pct = _num(f.get("TaxPct"))
        st.markdown(t("Subtotal: **{s}**  ·  Tax ({p}%): **{i}**  ·  Total: **{t}**")
                    .replace("{s}", _T.dinero(_num(f.get("Subtotal"))))
                    .replace("{p}", f"{_imp_pct:.0f}").replace("{i}", _T.dinero(_num(f.get("Tax"))))
                    .replace("{t}", _T.dinero(total)))
        if str(f.get("Note", "")).strip():
            st.caption(t("Note: {x}").replace("{x}", str(f.get("Note"))))
        try:
            from core import invoice_pdf
            _cli = C.get_cliente(str(f.get("ClientID", ""))) if f.get("ClientID") else {}
            _pdf = invoice_pdf.generate_invoice_pdf(f, _cli, grupo)
            # v569 · «Invoice_», no «Factura_» (el archivo lo recibe el cliente)
            st.download_button(t(":material/download: Download invoice (PDF)"), data=_pdf,
                               file_name=f"Invoice_{f.get('Number', '')}.pdf",
                               mime="application/pdf", key=f"fac_pdf_{fid}")
        except Exception as e:
            st.caption(t(":material/warning: The PDF could not be generated: {e}").replace("{e}", str(e)))
        # v488: la factura en Xero (o el botón para mandarla).
        from core import xero_ui
        xero_ui.boton_factura(grupo, f)

    with der:
        st.markdown(t("#### :material/payments: Payments received"))
        if _anulada:
            # ⚠️ v569 · una anulada NO debe nada: decía «OUTSTANDING $44.00»
            st.info(t(":material/block: Voided: there is nothing to collect."))
        else:
            # v309: el `help` llevaba DOS importes → perdía los símbolos de moneda.
            st.metric(t("Outstanding"), _T.dinero(total - cob),
                      help=t("Collected {c} of {t}").replace("{c}", _T.dinero(cob))
                      .replace("{t}", _T.dinero(total)))
        if not _anulada and cob < total:
            with st.form(f"cob_{fid}"):
                _m = st.number_input(t("Record payment ($)"), min_value=0.0,
                                     max_value=float(round(total - cob, 2)),
                                     value=float(round(total - cob, 2)), step=50.0)
                _fch = st.date_input(t("Payment date"), value=clock.today(), format="DD/MM/YYYY")
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
                st.markdown(f"- {_dmy(cb.get('fecha', ''))}: **{_T.dinero(_num(cb.get('monto')))}**")
        if not _anulada:
            with st.expander(t(":material/block: Void invoice"), key=f"exp_fac_anul_{fid}"):
                st.caption(t("It is taken out of accounts receivable. This cannot be undone."))
                # ⚠️ v569 · PREGUNTA antes (un clic anulaba, sin vuelta atrás) y la acción
                # va diferida a `render_facturas` (trampa 37).
                if st.session_state.get("_fac_anular_conf") == fid:
                    st.warning(t("Void invoice No. {n}? It cannot be undone.")
                               .replace("{n}", str(f.get("Number", ""))))
                    _y, _k = st.columns(2)
                    if _y.button(t(":material/block: Yes, void it"), key=f"fac_anul_si_{fid}",
                                 type="primary"):
                        st.session_state.pop("_fac_anular_conf", None)
                        st.session_state["_fac_anular"] = fid
                        st.rerun()
                    if _k.button(t("Keep it"), key=f"fac_anul_no_{fid}"):
                        st.session_state.pop("_fac_anular_conf", None)
                        st.rerun()
                elif st.button(t("Void this invoice"), key=f"fac_anul_{fid}"):
                    st.session_state["_fac_anular_conf"] = fid
                    st.rerun()


# ── Nueva factura ────────────────────────────────────────────────
def _nueva_factura(grupo):
    if st.button(t(":material/arrow_back: Cancel"), key="fac_new_back"):
        st.session_state.pop("_fac_nueva", None)
        st.session_state.pop("_fac_cli_sin_ficha", None)      # v558
        st.rerun()
    st.markdown(t("## :material/add_circle: New invoice"))

    fichas = C.list_clientes(grupo)
    if not fichas:
        # ⚠️ v558 · era un callejón: «Invoice» desde la tarjeta de una obra cuyo cliente es
        # TEXTO («Cliente de prueba», sin ficha) llegaba aquí con un «Create a client
        # first» sin botón ni nombre (visto en producción). Y el atajo dejaba colgados
        # su aviso y su obra, que salían más tarde en otra factura.
        # ⚠️ El nombre se GUARDA mientras se está aquí: el clic del botón es otra pasada,
        # y en ella el aviso del atajo ya se habría consumido (lo cazó verif_v558).
        _av0 = st.session_state.pop("_fac_aviso_cli", None)
        if _av0:
            st.session_state["_fac_cli_sin_ficha"] = _av0
        _cli_obra = st.session_state.get("_fac_cli_sin_ficha")
        st.session_state.pop("_fac_prj_pending", None)
        if _cli_obra and _cli_obra != "—":
            st.info(t(":material/info: Invoices need a client record, and this company has none yet. This job's client, **{c}**, only exists as text on the job: create its record and come back — the job is matched by name.",
                      c=_cli_obra))
            if st.button(t(":material/contacts: Create the record for {c}", c=_cli_obra),
                         key="fac_ir_cli", type="primary"):
                # El detalle de Contacts de un cliente SIN ficha ya sabe crearla (v255):
                # se abre por su nombre normalizado.
                st.session_state["_cli_open"] = C._norm(_cli_obra)
                st.session_state.pop("_fac_nueva", None)
                st.session_state.pop("_fac_cli_sin_ficha", None)
                st.session_state["_admin_nav_pending"] = ("contactos", None)
                st.rerun()
        else:
            st.info(t(":material/info: Invoices need a client record, and this company has none yet."))
            if st.button(t(":material/contacts: Go to Contacts"), key="fac_ir_cli", type="primary"):
                st.session_state.pop("_fac_nueva", None)
                st.session_state.pop("_fac_cli_sin_ficha", None)
                st.session_state["_admin_nav_pending"] = ("contactos", None)
                st.rerun()
        return
    st.session_state.pop("_fac_cli_sin_ficha", None)          # ya hay fichas: no aplica
    # (Por NOMBRE es seguro aquí: `create_cliente` no deja dos clientes con el mismo
    # nombre en un grupo.)
    _by_name = {c.get("Name", ""): c for c in fichas}
    cli_sel = st.selectbox(t(":material/contacts: Client"), list(_by_name.keys()), key="fac_cli")
    cli = _by_name.get(cli_sel, {})
    cid = str(cli.get("ID", ""))
    cnorm = C._norm(cli.get("Name"))

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
        if st.checkbox(t(":material/archive: Include archived sites ({n})").replace("{n}", str(len(_arch))),
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
        if _extra and str(_extra.get("Group", "")) == str(grupo):
            prjs = prjs + [_extra]
    # ⚠️ v306: por ID, no por nombre. Antes el alcance y la línea de la factura se casaban
    # con `{Nombre: ID}`: con dos proyectos homónimos el radio mostraba DOS opciones
    # idénticas, el filtro casaba con AMBOS y el importe se enlazaba al proyecto
    # equivocado — es decir, se facturaba mal, no solo se veía mal.
    _lbl = P.etiqueta_proyectos(prjs)              # {ID: etiqueta única}
    # Se marca cuál está archivada: si no, en el radio son indistinguibles de las activas
    # y no se ve por qué aparece una obra que se creía cerrada.
    _ids_arch = {str(p.get("ID", "")) for p in _arch}
    _lbl = {k: (v + " " + t("· archived") if k in _ids_arch else v) for k, v in _lbl.items()}
    _pid_by_lbl = {v: k for k, v in _lbl.items()}
    prj_names = [_lbl[str(p.get("ID", ""))] for p in prjs]

    # ⚠️ Al DESMARCAR la casilla, la opción elegida puede desaparecer. Un `st.radio` cuyo
    # valor guardado ya no está entre las opciones revienta (es el fallo que v358 evitó al
    # no preseleccionar una etiqueta inexistente). Se suelta ANTES de instanciarlo.
    # v569 · la opción «todo el cliente» es un ID interno: se TRADUCE al pintarla, y
    # comparar con un texto traducido es lo que verif_v436 prohíbe.
    if st.session_state.get("fac_scope") not in ["__todo__"] + prj_names:
        st.session_state.pop("fac_scope", None)

    # v357: atajo desde el proyecto. Llega el ID y AQUÍ se resuelve su etiqueta, que es
    # donde se conoce el conjunto con el que se calculó (v306). Se aplica ANTES de
    # instanciar el radio: escribir la clave de un widget ya creado revienta (v111).
    _av = st.session_state.pop("_fac_aviso_cli", None)
    if _av:
        st.warning(t(":material/contacts: That project has the client **{c}**, which is not a "
                     ":material/contacts: Contacts record. Choose the client by hand, or link the "
                     "project to its record so the shortcut works next time.").replace("{c}", str(_av)))
    _pend_pid = st.session_state.pop("_fac_prj_pending", None)
    if _pend_pid:
        _et = _lbl.get(str(_pend_pid))
        if _et in prj_names:
            st.session_state["fac_scope"] = _et
        else:
            # ⚠️ Antes, si el proyecto no estaba en la lista, `_et` era None y NO se
            # decía nada: el usuario acababa en «Todo el cliente» sin saber por qué.
            st.info(t(":material/info: That project could not be preselected for this client (check which client it is linked to). Choose the scope by hand."))
    # ⚠️ v569 · sin obras, un «Scope» de UNA sola opción no deja elegir nada: se dice en
    # una línea. El radio sigue aquí (detrás de la casilla y del reset, regla v111).
    if prj_names:
        _scope = st.radio(t("Scope"), ["__todo__"] + prj_names, horizontal=True, key="fac_scope",
                          format_func=lambda o: t("The whole client") if o == "__todo__" else o)
    else:
        _scope = "__todo__"
        st.caption(t(":material/info: This client has no jobs: the invoice lines are free text."))
    _scope_prjs = (prjs if _scope == "__todo__"
                   else [p for p in prjs if _lbl.get(str(p.get("ID", ""))) == _scope])

    # Precarga: una línea por proyecto con lo pendiente de facturar
    _pre = []
    for p in _scope_prjs:
        pend = I.pendiente_de_facturar(str(p.get("ID", "")), grupo, p)
        if pend > 0:
            _pre.append({"Concepto": f"{d('Works')} — {p.get('Name', '')}",
                         "Project": _lbl.get(str(p.get("ID", "")), ""), "Importe": pend})
    if not _pre:
        _pre = [{"Concepto": "", "Project": "(none)", "Importe": 0.0}]

    st.caption(t("Invoice lines — edit, add or remove. The «Project» links the line so it is not invoiced twice."))
    _ed = st.data_editor(
        pd.DataFrame(_pre), num_rows="dynamic", width="stretch", key="fac_lineas",
        column_config=tabla.cfg(None, {
            "Concepto": st.column_config.TextColumn(t("Item"), width="large"),
            "Project": st.column_config.SelectboxColumn(
                t("Project"), options=["(none)"] + prj_names, required=False),
            "Importe":  st.column_config.NumberColumn(t("Amount"), format="$%,.2f", min_value=0.0),
        }))

    try:
        from core import contable
        _plazo = int(contable.identidad(grupo).get("plazo") or 14)
    except Exception:
        _plazo = 14                       # sin plazo configurado, el estándar de la casa

    c1, c2, c3 = st.columns(3)
    _fecha = c1.date_input(t("Date"), value=clock.today(), key="fac_fecha", format="DD/MM/YYYY")
    # ⚠️ v483 — el vencimiento nacía HOY, o sea que toda factura entraba VENCIDA el
    # mismo día: el «vencido» del resumen financiero y el estado de la lista se
    # disparaban al instante, y al exportarla a la contabilidad llegaba en mora sin
    # haberla mandado. Ahora sale del plazo de pago del grupo (14 días por defecto).
    _venc = c2.date_input(t("Due date"),
                          value=clock.today() + _timedelta(days=_plazo),
                          key="fac_venc", format="DD/MM/YYYY")
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
        pnom = str(r.get("Project", ""))
        _lineas.append({"concepto": con, "importe": imp,
                        "proyecto_id": _pid_by_lbl.get(pnom, "")})
    _sub = round(sum(l["importe"] for l in _lineas), 2)
    _impv = round(_sub * _imp / 100.0, 2)
    # ⚠️ `theme.dinero` escapa el `$`: con dos importes en la misma línea Streamlit
    # renderizaba esto como una FÓRMULA LaTeX ilegible (v309).
    from core import theme as _T
    st.markdown(t("Subtotal **{s}**  ·  Tax **{i}**  ·  Total **{t}**")
                .replace("{s}", _T.dinero(_sub)).replace("{i}", _T.dinero(_impv))
                .replace("{t}", _T.dinero(_sub + _impv)))

    if st.button(t(":material/receipt_long: Issue invoice"), type="primary", key="fac_emit"):
        if not _lineas:
            st.error(t("Add at least one line with an amount."))
            return
        ok, res = I.create_factura(
            grupo=grupo, cliente_id=cid, cliente_nombre=cli.get("Name", ""),
            lineas=_lineas, impuesto_pct=_imp, fecha=_fecha.isoformat(),
            vencimiento=_venc.isoformat(), nota=_nota, creado_por=_creado_por())
        if ok:
            st.session_state.pop("_fac_nueva", None)
            st.session_state["_fac_open"] = res
            st.rerun()
        else:
            st.error(res)
