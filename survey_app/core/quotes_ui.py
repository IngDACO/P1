"""📄 Cotizaciones — armar el precio desde el catálogo (v353). v580 · probada acción por acción.

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
from core.num import num as _num, dmy as _dmy
from core import tabla

# ⚠️ SIN `t()`: se construye al IMPORTAR, cuando no hay sesión, así que la traducción
# quedaría congelada — el fallo de `invoices_ui._EST_FMT` (v449) y de otros cinco. Las
# CLAVES son el estado que guarda la hoja. El icono va aquí y la palabra la pone
# `_est_txt()` al PINTAR.
_EST_ICONO = {Q.BORRADOR: ":gray[:material/edit_note:]",
              Q.ENVIADA: ":blue[:material/send:]",
              Q.ACEPTADA: ":green[:material/check_circle:]",
              Q.RECHAZADA: ":gray[:material/block:]",
              Q.VENCIDA: ":red[:material/schedule:]"}
# v580 · el punto de color de la TABLA (el de Invoices, v569)
_EST_PUNTO = {Q.BORRADOR: "⚪", Q.ENVIADA: "🔵", Q.ACEPTADA: "🟢", Q.RECHAZADA: "⚫",
              Q.VENCIDA: "🔴"}
# Filtro de la lista: ID interno → (estados que entran, rótulo). Sin `t()` (se importa).
_FILTROS = {"Todas": (None, "All"),
            "Borrador": ((Q.BORRADOR,), "Draft"),
            "Enviadas": ((Q.ENVIADA, Q.VENCIDA), "Sent"),
            "Vencidas": ((Q.VENCIDA,), "Expired"),
            "Aceptadas": ((Q.ACEPTADA,), "Accepted"),
            "Rechazadas": ((Q.RECHAZADA,), "Rejected"),
            "Decididas": ((Q.ACEPTADA, Q.RECHAZADA), "Decided")}


def _est_txt(est) -> str:
    """El nombre del estado. ⚠️ v580 · una cotización VENCIDA es «expired»: `etiqueta` la da
    como «overdue» (el de las facturas) y la misma pantalla decía las dos cosas."""
    return t("expired") if str(est) == Q.VENCIDA else _etq(str(est))


def _est_fmt(est) -> str:
    """El estado de la cotización, con su icono, en el idioma de la PANTALLA."""
    return f"{_EST_ICONO.get(str(est), '')} {_est_txt(est)}".strip()


def _est_celda(c) -> str:
    """El estado en una CELDA: punto de color + la palabra (fuera del dict de la fila:
    verif_v452 mira que ninguna celda pinte en crudo un DATO de la hoja)."""
    _e = Q.estado_de(c)
    return f"{_EST_PUNTO.get(_e, '')} {_est_txt(_e)}"


def _num_txt(c) -> str:
    """«0003», o «0003 v2» si es una versión posterior."""
    _v = int(_num(c.get("Version"), 1))
    return str(c.get("Number", "")) + (f" v{_v}" if _v > 1 else "")


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

    # ── Las cifras, ACTIVAS (v580; eran HTML): cada una filtra la lista ──
    r = Q.resumen(grupo)
    _pe = r["por_estado"]
    _env, _ven = _pe.get(Q.ENVIADA, 0), _pe.get(Q.VENCIDA, 0)
    _K = [("calle", t("Out with clients"), T.dinero(r["en_calle"], 0),
           # ⚠️ v580 · el importe suma las VENCIDAS (siguen en la calle) y el pie no las
           # contaba: «$539 · 1 sent» con dos fuera
           (t("{n} sent · {v} expired", n=_env + _ven, v=_ven) if _ven
            else t("{n} sent, awaiting reply", n=_env)), "Enviadas"),
          ("gan", t("Won"), T.dinero(r["ganado"], 0),
           t("{n} accepted", n=_pe.get(Q.ACEPTADA, 0)), "Aceptadas"),
          # ⚠️ sin cotizaciones decididas la conversión NO es 0%: es que aún no se puede
          # calcular. Un 0% ahí sería la trampa de v320 («sin asignar» que mentía).
          ("conv", t("Conversion"), f"{r['conversion']:.0f}%" if r["conversion"] is not None else "—",
           t("of those decided") if r["conversion"] is not None else t("none decided yet"),
           "Decididas"),
          ("n", t("Quotes"), str(r["n"]), t("{v} expired", v=_ven), "Todas")]
    _css = []
    if r["en_calle"] > 0:
        _css.append(f".st-key-cpxkpi_cot_calle button{{border-left-color:{T.AMBAR}!important}}")
    if r["ganado"] > 0:
        _css.append(f".st-key-cpxkpi_cot_gan button{{border-left-color:{T.VERDE}!important}}"
                    f".st-key-cpxkpi_cot_gan button p:nth-child(2):not(:last-child)"
                    f"{{color:{T.VERDE}!important}}")
    if _css:
        st.markdown("<style>" + "".join(_css) + "</style>", unsafe_allow_html=True)
    # una fila que parte sola: 4 por fila, 2 en estrecho (v578; salían 3 + 1 estirada)
    st.markdown(T.por_fila("cpx_cot_kpis", 4), unsafe_allow_html=True)
    with st.container(key="cpx_cot_kpis"):
        for _col, (_s, _l, _v, _pie, _fl) in zip(st.columns(len(_K)), _K):
            if _col.button(f"{_l}\n\n{_v}\n\n{_pie}", key=f"cpxkpi_cot_{_s}", width="stretch"):
                st.session_state["_cot_filt_pending"] = _fl
                st.session_state["_cot_bajar"] = True
                st.rerun()

    if st.button(t(":material/add_circle: New quote"), type="primary", key="cot_new_btn"):
        st.session_state["_cot_nueva"] = True
        st.rerun()

    cots = Q.list_cotizaciones(grupo)
    if not cots:
        st.caption(t("No quotes yet. Start with «New quote» — the items come from :material/sell: Catalogue."))
        return

    # v580 · cada vencida, un botón que la abre (antes, sus nombres como texto)
    _venc = [c for c in cots if Q.estado_de(c) == Q.VENCIDA]
    if _venc:
        st.warning(t(":material/schedule: **{n} expired quote(s)** with no answer. Open one "
                     "to issue a new version if it still stands:", n=len(_venc)))
        for c in _venc[:8]:
            if st.button(f":material/open_in_new: {t('No.')} {_num_txt(c)} · "
                         f"{c.get('ClientName', '') or '—'} · {T.dinero(c.get('Total'), 0)}",
                         key=f"cotvenc_{c.get('ID')}", type="tertiary"):
                st.session_state["_cot_open"] = str(c.get("ID", ""))
                st.rerun()

    # ── El filtro (recordado) y la tabla: un toque abre ──
    _pp = st.session_state.pop("_cot_filt_pending", None)
    if _pp in _FILTROS:
        st.session_state["cpxseg_cot_filt"] = _pp
    _filt = st.radio(t("Filter"), list(_FILTROS), format_func=lambda o: t(_FILTROS[o][1]),
                     horizontal=True, key="cpxseg_cot_filt", label_visibility="collapsed",
                     persist_state="session")
    _entran = _FILTROS.get(_filt or "Todas", (None, ""))[0]
    _lista = [c for c in cots if _entran is None or Q.estado_de(c) in _entran]
    with st.container(key="cpx_cot_tabla"):
        from core import projects_ui as _PU
        _PU._bajar_a("cpx_cot_tabla", "_cot_bajar")
        if not _lista:
            st.caption(t("No quotes in this filter."))
            return
        _gen = st.session_state.get("_cot_tbl_gen", 0)
        # ⚠️ v580 · lo que se mira primero, delante (Status y el % se quedaban fuera de la
        # vista a 846 px), el número FIJADO, fechas DD/MM/YYYY, el estado con su color, y
        # `single-cell`: con `single-row` tocar la celda solo la enmarcaba (visto).
        _ev = st.dataframe(pd.DataFrame([{
            "Nº":      _num_txt(c),
            "Cliente": c.get("ClientName", "") or "—",
            "Estado":  _est_celda(c),
            "Total":   round(_num(c.get("Total")), 2),
            "Vence":   _dmy(c.get("ValidUntil")),
            "Fecha":   _dmy(c.get("Date")),
            "Markup":  round(_num(c.get("MarginPct")), 1),
        } for c in _lista]), width="stretch", hide_index=True, on_select="rerun",
            selection_mode="single-cell", key=f"cot_tbl_{_gen}",
            column_config=tabla.cfg(None, {
                "Nº":      st.column_config.TextColumn(t("No."), pinned=True),
                "Cliente": st.column_config.TextColumn(t("Client")),
                "Estado":  st.column_config.TextColumn(t("Status")),
                "Total":   st.column_config.NumberColumn(t("Total"), format="dollar"),
                "Vence":   st.column_config.TextColumn(t("Expires")),
                "Fecha":   st.column_config.TextColumn(t("Date")),
                # v580 · «Markup»: aquí es ganancia ÷ COSTO; el «Margin %» de Profitability y
                # del Resumen es ganancia ÷ ingreso, y con el mismo nombre se confundían
                "Markup":  st.column_config.NumberColumn(t("Markup %"), format="%.1f%%",
                                                         help=t("Profit ÷ cost."))}))
        st.caption(t(":material/touch_app: Tap a quote to see the detail, the PDF and record the outcome."))
    _s = getattr(_ev, "selection", None)
    _fs = [c[0] for c in (getattr(_s, "cells", None) or [])] or list(getattr(_s, "rows", None) or [])
    if _fs and 0 <= _fs[0] < len(_lista):
        # ⚠️ otra generación de clave: soltar la selección no llega al navegador (trampa 31)
        st.session_state["_cot_tbl_gen"] = _gen + 1
        st.session_state["_cot_open"] = str(_lista[_fs[0]].get("ID", ""))
        st.rerun()


# ── Nueva cotización ─────────────────────────────────────────────
def _editor_lineas(grupo, key: str, lineas: list) -> list:
    """Selector del catálogo + tabla editable (cantidad y **ganancia por línea**)."""
    from core import auth
    items = CAT.list_items(grupo)
    if not items:
        st.warning(t(":material/sell: The catalogue is empty. Add products and services in :material/sell: Catalogue before quoting."))
        return lineas
    etq = CAT.etiqueta_items(items)          # v306: el ID solo si el nombre se repite
    # v580 · el selector se VACÍA al añadir: otra generación de clave (soltar su estado no
    # llega al navegador, trampa 31) — se quedaba con lo elegido
    _sg = st.session_state.get(f"{key}_selgen", 0)
    _sel = st.multiselect(t("Add from the catalogue"), list(etq),
                          format_func=lambda i: etq.get(i, i), key=f"{key}_sel_{_sg}",
                          help=t("Choose the items; then adjust quantity and profit."))
    if _sel and st.button(t(":material/add: Add to the quote"), key=f"{key}_add"):
        _m = auth.group_margin_default(grupo)
        _ya = {l.get("catalogo_id") for l in lineas}
        lineas = list(lineas)
        for cid in _sel:
            if cid in _ya:
                continue
            lineas.append(Q.linea_de(CAT.get_item(cid), 1, _m))
        # ⚠️ v580 · lo añadido se GUARDA donde quien llama lo lee (`<key>_lineas`): en un
        # borrador ya creado nadie leía `ed<ID>_lineas` y la pasada siguiente volvía a las
        # líneas de la hoja — «Add to the quote» no añadía nada.
        st.session_state[f"{key}_lineas"] = lineas
        st.session_state[f"{key}_selgen"] = _sg + 1
        st.session_state[f"{key}_edgen"] = st.session_state.get(f"{key}_edgen", 0) + 1
        st.rerun()

    if not lineas:
        st.caption(t("No lines yet."))
        return lineas

    st.markdown(t("**Lines** — enter **how much you want to make** on each item; the markup % and the price follow on their own"))
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
        hide_index=True, width="stretch",
        key=f"{key}_ed_{st.session_state.get(f'{key}_edgen', 0)}",
        # ⚠️ v355: lo único que se teclea del precio es la GANANCIA. El % y el precio son
        # consecuencia, y se muestran bloqueados para que quede claro.
        disabled=["Concepto", "Costo", "Margen %", "Precio"],
        column_config=tabla.cfg(None, {
            "Costo": st.column_config.NumberColumn(t("Cost"), format="$%,.2f",
                                                   help=t("What it costs you. The client does not see this.")),
            "Ganancia $": st.column_config.NumberColumn(
                t("Profit $"), format="$%,.2f", min_value=0.0,
                help=t("How much you want to make on this item. The markup % is worked out for you.")),
            "Margen %": st.column_config.NumberColumn(t("Markup %"), format="%.1f%%",
                                                      help=t("Worked out as profit ÷ cost.")),
            "Precio": st.column_config.NumberColumn(t("Price"), format="$%,.2f",
                                                    help=t("Cost + profit. This is what the client sees.")),
            "Cant.": st.column_config.NumberColumn(t("Qty"), min_value=0.0),
            "Quitar": st.column_config.CheckboxColumn(t("Remove"))}))

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


def _desde_plano(grupo):
    """Sembrar las líneas de la cotización leyendo el PDF del plano (v509).

    ⚠️ AÑADE, nunca reemplaza (decisión del usuario): lo que ya se escribió a mano se
    queda. Pulsar dos veces duplica líneas, y eso se ve; perder lo escrito, no.
    """
    from core import catalogo as _CAT
    from core import plan_data as _PD
    from core import quote_from_plan as _QP

    with st.expander(t(":material/architecture: Price it from the drawing"), expanded=False, key="exp_cot_plano"):
        st.caption(t("Reads the PDF and proposes the lines whose quantity comes from the "
                     "drawing. You review them before saving — this is a starting point, "
                     "not a price."))
        # ⚠️ v582 · ANTES de leer el plano y con su botón: el aviso de abajo decía «Set the
        # rule on the items in Catalogue» y ese campo no existía; ahora existe, y se avisa
        # aquí, siempre pintado (un botón que solo sale tras «Propose lines» pierde el toque)
        if not any(_CAT.regla_de(i) != _QP.MANUAL for i in (_CAT.list_items(grupo) or [])):
            st.warning(t(":material/info: No catalogue item takes its quantity from the "
                         "drawing yet: each item says it in «Quantity from the drawing»."))
            if st.button(t(":material/sell: Set it in Catalogue"), key="cot_plano_cat",
                         type="tertiary"):
                from core import projects_ui as _PU
                _PU._ir_a("finanzas", "📚 Catálogo")
        _pdf = st.file_uploader(t("Drawing (PDF)"), type=["pdf"], key="cot_plano_pdf")
        if not _pdf:
            return
        if not st.button(t(":material/auto_awesome: Propose lines"), key="cot_plano_go",
                         width="stretch"):
            return

        _barra = st.progress(0.0, text=t("Reading the drawing…"))
        try:
            _plano = _PD.extraer_todo(
                _pdf, lambda f, txt: _barra.progress(min(1.0, f), text=txt))
        except Exception as e:
            _barra.empty()
            st.error("%s: %s" % (t("The drawing could not be read"), e))
            return
        _barra.empty()

        _items = _CAT.list_items(grupo) or []
        _r = _QP.proponer(_plano, _items)

        _p = _r["plano"]
        st.markdown(t("**The drawing says:** stops {n} · model {m} · rail {r}",
                      n=_p["ns"] or "—", m=_p["modelo"] or "—", r=_p["rail"] or "—"))

        if not _r["lineas"]:
            st.warning(t(":material/info: No catalogue item takes its quantity from the "
                         "drawing yet. Set the rule on the items in Catalogue."))
            return

        # ⚠️ Lo que NO se pudo calcular va ARRIBA y en rojo. Dejarlo abajo, o peor,
        # omitir esas líneas, haría la cotización más barata sin que nadie lo note —
        # y sub-cotizar en silencio se descubre al facturar, cuando ya se firmó.
        for _i in _r["incompletas"]:
            st.error(":material/priority_high: **%s** — %s. %s"
                     % (_i["nombre"], _i["motivo"], t("Set the quantity by hand.")))

        for _l in _r["lineas"]:
            st.markdown("· %s × **%s** = %s%s"
                        % (_l.get("descripcion", ""), _l.get("cantidad", 0),
                           T.dinero(_l.get("precio_total")),
                           (" :red[← %s]" % t("decide this one")) if _l.get("_falta") else ""))
        if _r["saltadas"]:
            st.caption(t("Not proposed (their quantity does not come from the drawing): {l}",
                         l=", ".join(_r["saltadas"][:8])))

        _st = st.session_state
        _st["new_lineas"] = list(_st.get("new_lineas") or []) + _QP.limpiar(_r["lineas"])
        _st["new_edgen"] = _st.get("new_edgen", 0) + 1
        flash.exito(t("{n} line(s) added. Review them before saving.",
                      n=len(_r["lineas"])))
        st.rerun()


_CLAVES_NUEVA = ("_cot_nueva", "new_lineas", "cot_new_cli", "cot_new_cli_nom", "cot_new_cli_cto",
                 "cot_new_cli_tel", "cot_new_cli_mail", "_cot_borrador")
# ⚠️ v583 · el BORRADOR del alta sobrevive a salir de Quotes (a «Set it in Catalogue», al
# menú): Streamlit borra un widget en cuanto una pasada no lo pinta, y volvías con las
# líneas (`new_lineas` no es un widget) pero sin cliente ni nota. Solo los campos SIN valor
# por defecto propio: el impuesto lleva `value=` (el de la empresa) y reasignarlo saca el
# aviso de Streamlit o lo reinicia — ese vuelve al de la empresa.
_BORRADOR = ("cot_new_cli_nom", "cot_new_cli_cto", "cot_new_cli_tel", "cot_new_cli_mail",
             "cot_new_nota")


def _limpiar_nueva():
    for k in _CLAVES_NUEVA:
        st.session_state.pop(k, None)
    for k in ("new_selgen", "new_edgen"):            # widgets nuevos para la próxima
        st.session_state[k] = st.session_state.get(k, 0) + 1


def _nueva(grupo):
    from core import auth
    if st.button(t(":material/arrow_back: Cancel"), key="cot_new_back"):
        _limpiar_nueva()
        st.rerun()
    st.markdown(t("## :material/request_quote: New quote"))
    # v583 · lo que Streamlit borró al salir, de vuelta (ANTES de crear los widgets)
    _borr = st.session_state.get("_cot_borrador") or {}
    for _k in _BORRADOR:
        if _k in _borr and _k not in st.session_state:
            st.session_state[_k] = _borr[_k]

    # ⚠️ v420: el cliente se puede crear AQUÍ. Antes, si era nuevo, había que salir a
    # Contactos, darlo de alta y volver a empezar la cotización — y si no había NINGÚN
    # cliente, esta pantalla ni siquiera dejaba entrar (`return`), así que el primer
    # presupuesto de una instalación nueva era imposible sin pasar antes por otra
    # sección. Cotizar es lo primero que se hace con un cliente nuevo: pedirle la ficha
    # de antemano es el orden al revés.
    fichas = C.list_clientes(grupo)
    _NUEVO = t("➕ New client")
    _map = {f"{f.get('Name','')}": f for f in fichas}
    # v583 · el cliente elegido, de vuelta solo si sigue siendo una opción (una ficha
    # borrada entretanto no se fuerza)
    if "cot_new_cli" not in st.session_state and _borr.get("cot_new_cli") in list(_map) + [_NUEVO]:
        st.session_state["cot_new_cli"] = _borr["cot_new_cli"]
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

    _desde_plano(grupo)                         # v509: sembrar líneas leyendo el PDF

    lineas = st.session_state.get("new_lineas", [])
    lineas = _editor_lineas(grupo, "new", lineas)
    st.session_state["new_lineas"] = lineas

    imp = st.number_input(t("Tax %"), min_value=0.0, step=1.0,
                          value=float(auth.group_tax_default(grupo)), key="cot_new_imp",
                          help=t("Taken from the company default."))
    nota = st.text_area(t("Notes for the client (optional)"), key="cot_new_nota",
                        help=t("They appear on the quote PDF."))
    # v583 · el borrador, en una clave que NO es de widget (esa no la borra nadie)
    st.session_state["_cot_borrador"] = {
        k: st.session_state[k] for k in ("cot_new_cli",) + _BORRADOR if k in st.session_state}

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
            _aviso_cli = None
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
                    f = {"ID": _res, "Name": _nom}
                else:
                    # ⚠️ El nombre ya existía: `create_cliente` no deja duplicados por
                    # grupo. En vez de dejar al usuario en un callejón —con la
                    # cotización entera escrita y sin poder guardarla—, se REUTILIZA esa
                    # ficha y se dice. Es coherente con la regla que la propia función
                    # impone: dentro de un grupo, ese nombre es UNO.
                    _ya = next((x for x in C.list_clientes(grupo, incluir_inactivos=True)
                                if C._norm(x.get("Name")) == C._norm(_nom)), None)
                    if not _ya:
                        st.error(t("The client could not be created: {e}", e=_res))
                        return
                    f = _ya
                    # ⚠️ se AVISA solo si la cotización se crea (abajo): encolado aquí, si
                    # crearla fallaba salía un clic tarde, en otra pantalla (trampa 41)
                    _aviso_cli = t(":material/info: A record already existed for **{n}**; "
                                   "the quote is linked to that one.", n=_nom)
            else:
                f = _map[_cli]
            ok, msg = Q.crear(grupo, f.get("ID", ""), f.get("Name", ""), lineas,
                              impuesto_pct=imp, nota=nota, creado_por=_creado_por())
            if ok:
                _limpiar_nueva()
                st.session_state["_cot_open"] = msg
                if _aviso_cli:
                    flash.info(_aviso_cli)
                # v580 · crear AVISA (salía la cotización sin decir nada)
                flash.exito(t("Quote No. {n} created.",
                              n=(Q.get_cotizacion(msg) or {}).get("Number", "")))
                st.rerun()
            else:
                if _aviso_cli:
                    st.info(_aviso_cli)
                st.error(msg)


def _totales_html(_tot: dict, imp_pct):
    """Totales + lo que el cliente NO ve (costo y ganancia), que es lo que te interesa."""
    T.kpi_row([
        (t("Subtotal"), T.dinero(_tot["subtotal"], 0), t("before tax")),
        (t("Tax"), T.dinero(_tot["impuesto"], 0), f"{_num(imp_pct):g}%"),
        (t("Total to client"), T.dinero(_tot["total"], 0), t("what they are charged"), T.AZUL),
        (t("Your profit"), T.dinero(_tot["ganancia"], 0),
         t("effective markup {p}%", p=f"{_tot['margen_pct']:.1f}"), T.VERDE),
    ])
    if _tot["horas"]:
        st.caption(t(":material/schedule: The quote includes **{h} service hours**. Once "
                     "accepted you can compare them against the hours clocked.",
                     h=f"{_tot['horas']:g}"))


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
    st.markdown(f"## :material/request_quote: {t('Quote No.')} {_num_txt(c)}")
    # v580 · fechas DD/MM/YYYY, la emisión, y de qué versión sale (decía «from COT-0003»,
    # el ID interno, sin traducir)
    _orig = Q.get_cotizacion(c.get("Source")) if str(c.get("Source", "")).strip() else {}
    st.markdown(f"**{c.get('ClientName', '') or '—'}**  ·  {_est_fmt(est)}"
                f"  ·  {t('issued')} {_dmy(c.get('Date'))}"
                f"  ·  {t('valid until')} {_dmy(c.get('ValidUntil'))}"
                + (f"  ·  {t('new version of v{v}', v=int(_num(_orig.get('Version'), 1)))}"
                   if _orig else ""))

    _base = Q.lineas_de(c)

    if est == Q.BORRADOR:
        _des = Q.desactualizadas(c)
        if _des:
            _txt = " · ".join(
                str(d["linea"].get("concepto", "")) + ": "
                + T.dinero(d["linea"].get("costo_total"))
                + (" → " + T.dinero(d["costo_hoy"]) if d["costo_hoy"] is not None
                   else " (" + d["motivo"] + ")")
                for d in _des[:6])
            st.warning(t(":material/sync_problem: **The catalogue changed** since you built "
                         "this quote: {x}. The quote's prices do NOT change on their own.")
                       .replace("{x}", _txt))
            if st.button(t(":material/sync: Refresh prices from the catalogue"),
                         key="cot_upd_" + str(cid),
                         help=t("Brings today's costs across while keeping what you want to make on each line.")):
                ok, msg = Q.actualizar_precios(cid)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
        _k = f"ed{cid}"
        # ⚠️ v580 · lo añadido sin guardar vive en `ed<ID>_lineas` (antes nadie lo leía)
        _trab = st.session_state.get(f"{_k}_lineas")
        nuevas = _editor_lineas(grupo, _k, _trab if _trab is not None else _base)
        # v580 · en el borrador también se cambian el impuesto y la nota
        _imp0, _nota0 = _num(c.get("TaxPct")), str(c.get("Note", "") or "")
        # ⚠️ sin `value=`: el valor inicial va a la sesión ANTES de crear el campo, y
        # «Discard» lo repone por el mismo camino (asignarlo después revienta, y con
        # `value=` + sesión Streamlit pinta un aviso)
        if st.session_state.pop(f"_cot_desc_{cid}", False):
            st.session_state[f"cot_imp_{cid}"] = float(_imp0)
            st.session_state[f"cot_nota_{cid}"] = _nota0
        st.session_state.setdefault(f"cot_imp_{cid}", float(_imp0))
        st.session_state.setdefault(f"cot_nota_{cid}", _nota0)
        _e1, _e2 = st.columns([1, 2])
        imp = _e1.number_input(t("Tax %"), min_value=0.0, step=1.0, key=f"cot_imp_{cid}")
        nota = _e2.text_area(t("Notes for the client (optional)"), key=f"cot_nota_{cid}",
                             height=68, help=t("They appear on the quote PDF."))
        _cambia = nuevas != _base or _num(imp) != _imp0 or str(nota) != _nota0
        if _cambia:
            _s1, _s2 = st.columns(2)
            if _s1.button(t(":material/save: Save changes"), key=f"cot_save_{cid}",
                          type="primary", width="stretch"):
                ok, msg = Q.guardar_lineas(cid, nuevas, impuesto_pct=imp, nota=nota)
                if ok:
                    st.session_state.pop(f"{_k}_lineas", None)
                    st.session_state[f"{_k}_edgen"] = st.session_state.get(f"{_k}_edgen", 0) + 1
                    flash.exito(msg)
                    st.rerun()
                else:
                    st.error(msg)
            if _s2.button(t(":material/undo: Discard changes"), key=f"cot_desc_{cid}",
                          width="stretch"):
                st.session_state.pop(f"{_k}_lineas", None)
                st.session_state[f"{_k}_edgen"] = st.session_state.get(f"{_k}_edgen", 0) + 1
                st.session_state[f"_cot_desc_{cid}"] = True
                st.rerun()
        _tot = Q.totales(nuevas, imp)
        _totales_html(_tot, imp)
    else:
        st.dataframe(pd.DataFrame([{
            "Concepto": l.get("concepto", ""),
            "Cant.": _num(l.get("cantidad")),
            "Precio": round(_num(l.get("precio_total")), 2),
        } for l in _base]), hide_index=True, width="stretch",
            column_config=tabla.cfg(None, {"Precio": st.column_config.NumberColumn(t("Price"), format="$%,.2f")}))
        _tot = Q.totales(_base, _num(c.get("TaxPct")))
        _totales_html(_tot, c.get("TaxPct"))
        if str(c.get("Note", "") or "").strip():
            st.caption(t(":material/sticky_note_2: Note for the client: {n}", n=str(c.get("Note"))))

    # ⚠️ v580 · la obra que nació de ella ya no existe: decirlo y dejar soltarla (la
    # cotización se quedaba «aceptada», atada a nada, sin poder cambiar de estado)
    _perdida = Q.proyecto_perdido(c)
    if _perdida:
        st.warning(t(":material/link_off: The project {p} created from this quote no longer "
                     "exists.", p=str(c.get("ProjectID"))))
        if st.button(t(":material/link_off: Unlink it"), key=f"cot_unlink_{cid}"):
            ok, msg = Q.desvincular_proyecto(cid)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()
    _con_obra = bool(str(c.get("ProjectID", "")).strip()) and not _perdida

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
    elif est in (Q.ACEPTADA, Q.RECHAZADA) and not str(c.get("ProjectID", "")).strip():
        # ⚠️ v580 · la vuelta atrás: un toque la aceptaba o rechazaba y no había forma de
        # deshacerlo (con obra ya creada, no: el motor lo impide)
        if a1.button(t(":material/undo: Undo — back to sent"), key=f"cot_undo_{cid}",
                     width="stretch"):
            ok, msg = Q.set_estado(cid, Q.ENVIADA)
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
                _nv = Q.get_cotizacion(msg) or {}
                flash.exito(t("Version {v} of No. {n} created.",
                              v=int(_num(_nv.get("Version"), 1)), n=_nv.get("Number", "")))
                st.rerun()
            else:
                st.error(msg)

    # ── PDF ──────────────────────────────────────────────────────
    try:
        from core import quote_pdf
        cli = next((x for x in C.list_clientes(grupo, incluir_inactivos=True)
                    if str(x.get("ID", "")) == str(c.get("ClientID", ""))), None)
        pdf = quote_pdf.generate_quote_pdf(c, cli, grupo)
        st.download_button(t(":material/download: Download quote (PDF)"), data=pdf,
                           file_name=f"Quote_{_num_txt(c).replace(' ', '_')}.pdf",
                           mime="application/pdf", key=f"cot_pdf_{cid}")
    except Exception as e:
        st.warning(t(":material/warning: The PDF could not be generated: {e}", e=e))

    # ── Fase 3: de cotización ganada a obra ──────────────────────
    if est == Q.ACEPTADA and not _con_obra and not _perdida:
        _crear_proyecto(grupo, c, _tot)
    elif _con_obra:
        _comparacion(cid, c)


def _crear_proyecto(grupo, c, _tot):
    """Aceptada y sin obra todavía: darla de alta con lo ya pactado."""
    from core import projects as P
    st.markdown("---")
    st.markdown(t("### :material/construction: Turn it into a project"))
    st.caption(t("It starts with the client, the budget and the margin you have just quoted. From there the usual flow follows: costs, hours and invoice."))
    with st.form("cot_prj_" + str(c.get("ID"))):
        c1, c2 = st.columns(2)
        # v580 · «No.», no «Nº»: el nombre se GUARDA en la obra
        nombre = c1.text_input(t("Project name"),
                               value=str(c.get("ClientName", "")) + " — No. "
                                     + str(c.get("Number", "")))
        # ⚠️ v580 · los tipos de la APP (los del alta normal): aquí iban los valores viejos
        # «Instalación», «Otro», y una instalación nacía SIN cronograma (PRJ-0024)
        tipo = c2.selectbox(t("Type"), list(P.TIPOS), format_func=_etq)
        c3, c4 = st.columns(2)
        ini = c3.date_input(t("Start date"), value=clock.today(grupo))
        ns = c4.number_input(t("Stops (NS)"), min_value=0, step=1, value=0,
                             help=t("Only an installation generates the standard schedule; with NS 0 the project starts with no activities."))
        ubic = st.text_input(t("Location (optional)"))
        st.info(t(":material/savings: Project budget: **{a}** — that is your quoted **cost**, "
                  "not the price to the client ({b}). That way the over-budget alert fires when "
                  "you are eating into the margin, not when you are already losing money.")
                .replace("{a}", T.dinero(_tot["costo"], 0))
                .replace("{b}", T.dinero(_tot["subtotal"], 0)))
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
        st.caption(t("Linked to project {x}.").replace("{x}", str(c.get("ProjectID"))))
        return
    st.markdown(t("### :material/compare_arrows: Quoted vs. actual —") + " " + comp["proyecto"])

    def _tarj(etq, d, unidad=""):
        _col = T.VERDE if d["dif"] <= 0 else T.ROJO
        _sig = "+" if d["dif"] > 0 else ""
        _val = (("%g " % d["real"]) + unidad).strip() if unidad else T.dinero(d["real"], 0)
        _cot = (("%g " % d["cotizado"]) + unidad).strip() if unidad else T.dinero(d["cotizado"], 0)
        # ⚠️ v580 · sin nada gastado todavía el % sale «-100%» y no dice nada: se dice eso
        if not _num(d["real"]):
            return (etq, _val, t("you quoted {x} · nothing yet", x=_cot), None)
        _pct = (" (" + _sig + ("%.0f" % d["pct"]) + "%)") if d["pct"] is not None else ""
        return (etq, _val, t("you quoted {x}", x=_cot) + _pct, _col)

    # ⚠️ La GANANCIA no se compara «real vs cotizada» a mitad de obra: hasta terminar,
    # lo no gastado parece ganancia. Se muestra la PROYECCIÓN al ritmo actual (v144) y
    # solo se llama «real» cuando el proyecto está al 100%.
    _gc = comp["ganancia_cotizada"]
    if comp["terminado"]:
        _g, _lbl_g, _pie = comp["ganancia_real"], t("Actual profit"), t("job finished")
    elif comp["ganancia_proyectada"] is not None:
        _g, _lbl_g = comp["ganancia_proyectada"], t("Projected profit")
        _pie = t("at the current rate · you quoted {x}", x=T.dinero(_gc, 0))
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
        st.caption(t(":material/trending_up: At the current rate the job will cost {a} "
                     "against the {b} quoted.")
                   .replace("{a}", T.dinero(comp["costo_proyectado"], 0))
                   .replace("{b}", T.dinero(comp["costo"]["cotizado"], 0)))
    _av = comp["avance"]
    if comp["costo"]["dif"] > 0 and _av < 100:
        st.warning(t(":material/warning: You are at **{m} above** what was quoted, with the "
                     "project at **{p}%**. At this rate the final profit will be lower than quoted.")
                   .replace("{m}", T.dinero(comp["costo"]["dif"], 0))
                   .replace("{p}", "%.0f" % _av))
    elif comp["costo"]["dif"] <= 0 and _av > 0:
        st.success(t(":material/check_circle: You are at **{m} below** what was quoted, with "
                     "the project at **{p}%**.")
                   .replace("{m}", T.dinero(abs(comp["costo"]["dif"]), 0))
                   .replace("{p}", "%.0f" % _av))
    if st.button(":material/folder: " + t("Open") + " " + comp["proyecto"], key="cot_prj_open_" + str(cid)):
        from core import home_ui
        st.session_state["_prjsel_pending"] = comp["proyecto_id"]
        st.session_state["_admin_open_proj"] = comp["proyecto_id"]
        home_ui.navegar("proyectos", "📊 Proyectos")
