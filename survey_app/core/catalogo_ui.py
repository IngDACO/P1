"""📚 Catálogo — productos y servicios con su costo (v352). v582 · probada acción por acción.

Base de las cotizaciones. ⚠️ SIN cabecera propia: `home_ui._sub_header` ya pinta
«Finanzas · Catálogo» encima — era el título duplicado que salió cuatro veces
(v212, v291, v314, v319).
"""
import zlib

import pandas as pd

from core.i18n import t, etiqueta as _etq
import streamlit as st

from core import flash

from core import catalogo as CAT
from core import quote_from_plan as QP
from core import tenant
from core import theme as T
from core.num import num as _num
from core import tabla
from core import ui_common as ui


def _creado_por() -> str:
    a = st.session_state.get("auth") or {}
    return str(a.get("usuario", "") or a.get("nombre", ""))


# v582 · con mayúscula (salía «product / service»), y por `t()` donde se pintan
_TIPO_LBL = {CAT.PRODUCTO: ":material/inventory_2: Product",
             CAT.SERVICIO: ":material/engineering: Service"}
_TIPO_TXT = {CAT.PRODUCTO: "Product", CAT.SERVICIO: "Service"}
# Filtro de la lista: ID interno → rótulo. ⚠️ Se comparan abajo (`_tipo == "Productos"`):
# se traduce el display, no la opción.
_FILT = {"Todos": "All", "Productos": "Products", "Servicios": "Services"}


def _tipo_txt(i) -> str:
    return t(_TIPO_TXT.get(str(i.get("Type", "")), "")) or _etq(str(i.get("Type", "")))


def _uni_txt(i) -> str:
    """La unidad en la tabla. ⚠️ v582 · un servicio NO tiene unidad (cuesta horas × tarifa
    × cantidad): los guardados antes llevan «hora», en español."""
    if str(i.get("Type", "")) == CAT.SERVICIO:
        return "—"
    return _etq(str(i.get("Unit", ""))) or "—"


def _activo_txt(i) -> str:
    return ("🟢 " + t("active") if str(i.get("Active", "SI")).upper() != "NO"
            else "🔴 " + t("deactivated"))


def _regla_lbl(r) -> str:
    return t(QP.ETIQUETAS.get(r, r))


_AYUDA_REGLA = ("Used by Quotes → «Price it from the drawing»: the quantity of this item is "
                "taken from the PDF of the drawing (fixed, one per stop, or one per stop "
                "minus one). «Manual» = you set it by hand on each quote.")


def render_catalogo(grupo):
    if not CAT.is_configured():
        st.info(t(":material/info: Configure Google Sheets to use the catalogue."))
        return
    if st.session_state.get("_cat_open"):
        _detalle(grupo, st.session_state["_cat_open"])
        return

    # ── Las cifras, ACTIVAS (v582; eran HTML): cada una filtra la lista ──
    r = CAT.resumen(grupo)
    _K = [("n", t("Items"), str(r["n"]), t("active in the catalogue"), "Todos"),
          ("prod", t("Products"), str(r["productos"]), t("charged by quantity"), "Productos"),
          ("serv", t("Services"), str(r["servicios"]), t("charged by the hour"), "Servicios")]
    st.markdown(T.por_fila("cpx_cat_kpis", 3), unsafe_allow_html=True)
    with st.container(key="cpx_cat_kpis"):
        for _col, (_s, _l, _v, _pie, _fl) in zip(st.columns(len(_K)), _K):
            if _col.button(f"{_l}\n\n{_v}\n\n{_pie}", key=f"cpxkpi_cat_{_s}", width="stretch",
                           help=t("Show them in the list")):
                st.session_state["_cat_tipo_pending"] = _fl
                st.session_state["_cat_bajar"] = True
                st.rerun()

    # ⚠️ v340: si se puede desactivar, tiene que poder VOLVER — y verse cuántos hay.
    _ver_inact = st.checkbox(t(":material/archive: Show deactivated ones too"),
                             key="cat_ver_inact",
                             help=t("{n} deactivated. They are not deleted: old quotes must "
                                    "keep showing their name.", n=r["inactivos"]))
    items = CAT.list_items(grupo, incluir_inactivos=_ver_inact)

    # Lo pendiente se escribe ANTES de crear los widgets (regla v111)
    _qp = st.session_state.pop("_cat_q_pending", None)
    if _qp is not None:
        st.session_state["cat_q"] = _qp
    _tp = st.session_state.pop("_cat_tipo_pending", None)
    if _tp in _FILT:
        st.session_state["cpxseg_cat_tipo"] = _tp
    _c1, _c2 = st.columns([3, 2])
    _q = _c1.text_input(t("Search"), key="cat_q", placeholder=t("name, category…"),
                        label_visibility="collapsed")
    # v582 · recordado al volver (como el de Quotes y el de Invoices)
    _tipo = _c2.radio(t("Type"), list(_FILT), format_func=lambda o: t(_FILT[o]),
                      horizontal=True, key="cpxseg_cat_tipo", label_visibility="collapsed",
                      persist_state="session")
    if _q.strip():
        _n = _q.strip().casefold()
        items = [i for i in items
                 if _n in f"{i.get('Name','')} {i.get('Category','')} {i.get('Description','')}".casefold()]
    if _tipo == "Productos":
        items = [i for i in items if str(i.get("Type", "")) == CAT.PRODUCTO]
    elif _tipo == "Servicios":
        items = [i for i in items if str(i.get("Type", "")) == CAT.SERVICIO]

    with st.container(key="cpx_cat_tabla"):
        from core import projects_ui as _PU
        _PU._bajar_a("cpx_cat_tabla", "_cat_bajar")
        if items:
            st.caption(t("Tap an item to edit it. **Cost** is what it costs you; the margin is set when quoting, line by line."))
            _gen = st.session_state.get("_cat_tbl_gen", 0)
            # ⚠️ v582 · el costo DELANTE (a 846 px con el menú y en el móvil se quedaba fuera
            # de la vista), el nombre FIJADO, y `single-cell`: con `single-row` tocar la celda
            # solo la enmarcaba (visto, como en Quotes antes de v580).
            df = pd.DataFrame([{
                "Item": i.get("Name", ""),
                "Costo": CAT.costo_de(i, 1),
                "Tipo": _tipo_txt(i),
                "Category": _etq(str(i.get("Category", ""))) or "—",
                "Unidad": _uni_txt(i),
                # ⚠️ Cadena vacía, NO NaN: `st.dataframe` pinta cualquier nulo como el
                # literal «None» en gris, con o sin `column_config` (cuadro de lo medido
                # en `tabla.celda`). Un producto no tiene horas, y se veía «None».
                "Horas": (tabla.celda(i.get("EstHours"), 2)
                          if str(i.get("Type", "")) == CAT.SERVICIO else ""),
                "Activo": _activo_txt(i),
            } for i in items])
            # «Active» solo cuando se ven los desactivados: si no, era una columna de 🟢
            if not _ver_inact:
                df = df.drop(columns=["Activo"])
            _ev = st.dataframe(df, width="stretch", hide_index=True,
                               on_select="rerun", selection_mode="single-cell",
                               key=f"cat_tbl_{_gen}",
                               column_config=tabla.cfg(None, {
                                   "Item": st.column_config.TextColumn(t("Item"), pinned=True),
                                   "Costo": st.column_config.NumberColumn(
                                       t("Cost"), format="$%,.2f",
                                       help=t("Product: unit cost. Service: hours × rate.")),
                                   "Tipo": st.column_config.TextColumn(t("Type")),
                                   "Unidad": st.column_config.TextColumn(t("Unit")),
                                   "Horas": tabla.derecha(t("Hours")),
                                   "Activo": st.column_config.TextColumn(t("Status"))}))
            _s = getattr(_ev, "selection", None)
            _fs = ([c[0] for c in (getattr(_s, "cells", None) or [])]
                   or list(getattr(_s, "rows", None) or []))
            if _fs and 0 <= _fs[0] < len(items):
                # ⚠️ otra generación de clave: soltar la selección no llega al navegador
                # (trampa 31)
                st.session_state["_cat_tbl_gen"] = _gen + 1
                st.session_state["_cat_open"] = str(items[_fs[0]].get("ID", ""))
                st.rerun()
            st.caption(t("1 item") if len(items) == 1 else t("{n} items", n=len(items)))
        elif r["n"] + r["inactivos"] == 0:
            st.caption(t("No items yet. Create the first one below."))
        else:
            # ⚠️ v582 · una búsqueda sin resultados decía «No items yet» con tres artículos
            st.caption(t("Nothing matches this search or filter."))
            if st.button(t(":material/filter_alt_off: Show all"), key="cat_ver_todo",
                         type="tertiary"):
                st.session_state["_cat_q_pending"] = ""
                st.session_state["_cat_tipo_pending"] = "Todos"
                st.rerun()

    _alta(grupo, vacio=(r["n"] + r["inactivos"] == 0))


def _nnorm(s) -> str:
    return " ".join(str(s or "").casefold().split())


def _k_dup(n) -> str:
    """La casilla «guardar aunque se repita» va POR NOMBRE: marcarla para uno no vale
    para otro (la lección de v558 en el alta de obras)."""
    return f"cat_dup_{zlib.crc32(_nnorm(n).encode('utf-8'))}"


def _alta(grupo, vacio=False):
    # v582 · con el catálogo vacío el alta se abre sola: es lo único que hay que hacer
    # ⚠️ la condición va en la CLAVE (verif_v547): con clave, el desplegable recuerda su estado
    with st.expander(t(":material/add_circle: New item"), key=f"exp_cat_new_{vacio}",
                     expanded=vacio):
        # ⚠️ El tipo va FUERA del form: dentro, los widgets no escriben hasta el submit
        # y no se podrían mostrar solo los campos que aplican (misma razón que v189/v306).
        tipo = st.radio(t("Type"), list(CAT.TIPOS), horizontal=True, key="cat_new_tipo",
                        format_func=lambda _k: t(_TIPO_LBL.get(_k, _k)))
        # ⚠️ v582 · otra GENERACIÓN de formulario tras crear: se quedaba lleno, y un segundo
        # toque en «Save item» creó otro idéntico (visto en producción: CAT-00001 y 00002)
        _g = st.session_state.get("_cat_new_gen", 0)
        _dupde = st.session_state.get("_cat_dupde") or {}
        with st.form(f"cat_new_{_g}"):
            c1, c2 = st.columns(2)
            nombre = c1.text_input(t("Name"), placeholder=t("e.g. Rail T75-3/B"),
                                   key=f"cat_new_nom_{_g}")
            if _dupde:
                st.warning(t(":material/warning: There is already an item called «{n}»: {x}. "
                             "If it is a different item, tick the box and save again.",
                             n=_dupde.get("visto", ""), x=_dupde.get("dups", "")))
                st.checkbox(t("Save even though the name is repeated"),
                            key=_k_dup(_dupde.get("nombre", "")))
            # v582 · por defecto la del TIPO (era «Engineering», la primera por orden)
            _cats, _ci = ui.opciones_con_actual(CAT.categorias(grupo),
                                                CAT.categoria_defecto(tipo))
            categoria = c2.selectbox(t("Category"), _cats, index=_ci,
                                     key=f"cat_new_cat_{tipo}_{_g}")
            if tipo == CAT.SERVICIO:
                c3, c4 = st.columns(2)
                horas = c3.number_input(t("Estimated hours"), min_value=0.0, step=0.5,
                                        help=t("This is what gets compared later against the hours clocked."),
                                        key=f"cat_new_h_{_g}")
                tarifa = c4.number_input(t("Rate/hour (cost)"), min_value=0.0, step=5.0,
                                         key=f"cat_new_r_{_g}")
                costo, unidad = 0.0, ""
            else:
                c3, c4 = st.columns(2)
                costo = c3.number_input(t("Unit cost"), min_value=0.0, step=1.0,
                                        key=f"cat_new_c_{_g}")
                unidad = c4.selectbox(t("Unit"), CAT.UNIDADES, key=f"cat_new_uni_{_g}",
                                      format_func=_etq)
                horas = tarifa = 0.0
            # ⚠️ v582 · sin esto «Price it from the drawing» no podía proponer NADA: todos los
            # artículos nacían «manual» y la cotización mandaba a ponerlo aquí, donde no estaba
            regla = st.selectbox(t("Quantity from the drawing"), list(QP.REGLAS),
                                 format_func=_regla_lbl, key=f"cat_new_regla_{_g}",
                                 help=t(_AYUDA_REGLA))
            desc = st.text_input(t("Description (optional)"),
                                 placeholder=t("what the client will see on the quote"),
                                 key=f"cat_new_desc_{_g}")
            if st.form_submit_button(t(":material/save: Save item"),
                                     width="stretch"):
                _dups = CAT.homonimos(grupo, nombre)
                if _dups and not st.session_state.get(_k_dup(nombre)):
                    st.session_state["_cat_dupde"] = {
                        "nombre": _nnorm(nombre), "visto": str(nombre).strip(),
                        "dups": ", ".join(str(d.get("ID", "")) for d in _dups[:3])}
                    st.rerun()
                ok, msg = CAT.crear(grupo, nombre, tipo=tipo, costo_unit=costo,
                                    horas_est=horas, tarifa_hora=tarifa, unidad=unidad,
                                    categoria=categoria, descripcion=desc,
                                    creado_por=_creado_por(), qty_rule=regla)
                if ok:
                    st.session_state["_cat_new_gen"] = _g + 1
                    st.session_state.pop("_cat_dupde", None)
                    # v582 · el NOMBRE (decía «Item CAT-00001 created.»)
                    flash.exito(t("Item «{n}» created.", n=str(nombre).strip()))
                    st.rerun()
                else:
                    st.error(msg)


def _usos(grupo, cid):
    """Dónde se usa (v582): cada cotización con una línea de este artículo, y un toque
    la abre. Las líneas guardan `catalogo_id`, así que esto no adivina por el nombre."""
    try:
        from core import quotes as Q
        from core import quotes_ui as QU
        cots = Q.con_item(grupo, cid)
    except Exception as e:
        st.caption(f"{t('Could not read the quotes')}: {e}")
        return
    if not cots:
        st.caption(t(":material/request_quote: Not used in any quote yet."))
        return
    st.markdown(t("**:material/request_quote: Used in 1 quote**") if len(cots) == 1
                else t("**:material/request_quote: Used in {n} quotes**", n=len(cots)))
    for c in cots[:8]:
        if st.button(f":material/open_in_new: {t('No.')} {QU._num_txt(c)} · "
                     f"{c.get('ClientName', '') or '—'} · {QU._est_txt(Q.estado_de(c))} · "
                     f"{T.dinero(c.get('Total'), 0)}",
                     key=f"cat_uso_{c.get('ID')}", type="tertiary"):
            # ⚠️ v583 · el ALTA de cotización, si seguía abierta (p. ej. tras «Set it in
            # Catalogue»), va DELANTE de la cotización pedida: visto en producción, el botón
            # abría «New quote». Se cierra el alta; su borrador se conserva (`_cot_borrador`,
            # `new_lineas`) y vuelve con «New quote».
            st.session_state.pop("_cot_nueva", None)
            st.session_state["_cot_open"] = str(c.get("ID", ""))
            from core import projects_ui as _PU
            _PU._ir_a("finanzas", "📄 Cotizaciones")
    if len(cots) > 8:
        st.caption(t("…and {n} more in Quotes.", n=len(cots) - 8))


def _detalle(grupo, cid):
    if st.button(t(":material/arrow_back: Back to catalogue"), key="cat_back"):
        st.session_state.pop("_cat_open", None)
        st.rerun()
    it = CAT.get_item(cid)
    if not it:
        st.warning(t("Item not found."))
        st.session_state.pop("_cat_open", None)
        return
    # v351: `get_item` busca por ID en TODA la hoja, sin mirar el grupo.
    if not tenant.exigir(it, t("This item")):
        st.session_state.pop("_cat_open", None)
        return

    _t0 = str(it.get("Type", ""))
    activo = str(it.get("Active", "SI")).upper() != "NO"
    st.markdown(f"## :material/sell: {it.get('Name', '')}")
    st.markdown(f"**{it.get('ID', '')}**  ·  {t(_TIPO_LBL.get(_t0, ''))}"
                f"  ·  {_etq(str(it.get('Category', ''))) or '—'}  ·  "
                f"{t('cost')} {T.dinero(CAT.costo_de(it, 1))}"
                + ("" if activo else "  ·  :red[" + t("inactive") + "]"))

    # ⚠️ v582 · el TIPO se puede corregir (un artículo creado con el tipo equivocado no tenía
    # arreglo). FUERA del form por lo mismo que en el alta: los campos cambian con él.
    # ⚠️ v487: el tipo GUARDADO se conserva aunque no sea uno de hoy (con `index-o-0`, uno
    # viejo pasaba a «Product» al guardar sin que nadie lo eligiera)
    _tipos, _ti = ui.opciones_con_actual(list(CAT.TIPOS), _t0)
    tipo = st.radio(t("Type"), _tipos, horizontal=True, key=f"cat_ed_tipo_{cid}", index=_ti,
                    format_func=lambda _k: t(_TIPO_LBL[_k]) if _k in _TIPO_LBL else _etq(_k),
                    help=t("Changing it does not alter quotes already issued: each line "
                           "keeps its own copy of the agreed price."))
    es_serv = tipo == CAT.SERVICIO
    with st.form(f"cat_edit_{cid}"):
        c1, c2 = st.columns(2)
        nombre = c1.text_input(t("Name"), value=str(it.get("Name", "")))
        # ⚠️ v487: conserva la categoria/unidad guardada aunque ya no este en la lista.
        _cats, _ci = ui.opciones_con_actual(CAT.categorias(grupo), it.get("Category", ""))
        categoria = c2.selectbox(t("Category"), _cats, index=_ci)
        if es_serv:
            c3, c4 = st.columns(2)
            horas = c3.number_input(t("Estimated hours"), min_value=0.0, step=0.5,
                                    value=float(_num(it.get("EstHours"))))
            tarifa = c4.number_input(t("Rate/hour (cost)"), min_value=0.0, step=5.0,
                                     value=float(_num(it.get("HourlyRate"))))
            # v582 · un servicio sin unidad (ver `catalogo.crear`)
            campos = {"EstHours": horas, "HourlyRate": tarifa, "Unit": ""}
        else:
            c3, c4 = st.columns(2)
            costo = c3.number_input(t("Unit cost"), min_value=0.0, step=1.0,
                                    value=float(_num(it.get("UnitCost"))))
            _unis, _uni = ui.opciones_con_actual(CAT.UNIDADES, it.get("Unit", ""))
            if _t0 != CAT.PRODUCTO:
                # v582 · de servicio a producto: no trae unidad (o trae la «hora» de antes)
                _unis, _uni = list(CAT.UNIDADES), 0
            unidad = c4.selectbox(t("Unit"), _unis, index=_uni, format_func=_etq)
            campos = {"UnitCost": costo, "Unit": unidad}
        _rg = CAT.regla_de(it)
        regla = st.selectbox(t("Quantity from the drawing"), list(QP.REGLAS),
                             index=list(QP.REGLAS).index(_rg), format_func=_regla_lbl,
                             help=t(_AYUDA_REGLA))
        desc = st.text_input(t("Description"), value=str(it.get("Description", "")))
        if st.form_submit_button(t(":material/save: Save changes"), width="stretch"):
            campos.update({"Name": nombre, "Category": categoria, "Description": desc,
                           "Type": tipo, "QtyRule": regla})
            ok, msg = CAT.actualizar(cid, campos)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()

    st.caption(t("Changing the cost **does not alter** quotes already issued: each line keeps its own copy of the agreed price."))
    _usos(grupo, cid)

    # ⚠️ v340: desactivar SIEMPRE con vuelta, y en el mismo sitio.
    if activo:
        with st.expander(t(":material/archive: Deactivate item"), key=f"exp_cat_off_{cid}"):
            st.caption(t("It stops being offered when quoting, but is not deleted: quotes already using it keep showing it."))
            if st.button(t(":material/archive: Deactivate"), key=f"cat_off_{cid}",
                         width="stretch"):
                ok, msg = CAT.set_activo(cid, False)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
    else:
        # ⚠️ v582 · decía que se ofrece al cotizar si marcas «Show deactivated ones too»:
        # esa casilla solo está en ESTA lista, y la cotización solo ofrece los activos
        st.warning(t(":material/block: This item is **deactivated**: it is not offered when quoting. Reactivate it to quote it again."))
        if st.button(t(":material/restore: Reactivate"), key=f"cat_on_{cid}", type="primary"):
            ok, msg = CAT.set_activo(cid, True)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()
