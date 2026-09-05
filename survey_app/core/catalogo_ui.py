"""📚 Catálogo — productos y servicios con su costo (v352).

Base de las cotizaciones. ⚠️ SIN cabecera propia: `home_ui._sub_header` ya pinta
«Finanzas · Catálogo» encima — era el título duplicado que salió cuatro veces
(v212, v291, v314, v319).
"""
import pandas as pd

from core.i18n import t, etiqueta as _etq
import streamlit as st

from core import flash

from core import catalogo as CAT
from core import tenant
from core import theme as T
from core.num import num as _num
from core import tabla


def _creado_por() -> str:
    a = st.session_state.get("auth") or {}
    return str(a.get("usuario", "") or a.get("nombre", ""))


_TIPO_LBL = {CAT.PRODUCTO: ":material/inventory_2: product",
             CAT.SERVICIO: ":material/engineering: service"}


def render_catalogo(grupo):
    if not CAT.is_configured():
        st.info(t(":material/info: Configure Google Sheets to use the catalogue."))
        return
    if st.session_state.get("_cat_open"):
        _detalle(grupo, st.session_state["_cat_open"])
        return

    r = CAT.resumen(grupo)
    T.kpi_row([
        (t("Items"), str(r["n"]), t("active in the catalogue")),
        (t("Products"), str(r["productos"]), t("charged by quantity")),
        (t("Services"), str(r["servicios"]), t("charged by the hour")),
    ])

    # ⚠️ v340: si se puede desactivar, tiene que poder VOLVER — y verse cuántos hay.
    _ver_inact = st.checkbox(t(":material/archive: Show deactivated ones too"),
                             key="cat_ver_inact",
                             help=f"There are {r['inactivos']} deactivated. They are not deleted: "
                                  "old quotes must keep showing their name.")
    items = CAT.list_items(grupo, incluir_inactivos=_ver_inact)

    _c1, _c2 = st.columns([3, 2])
    _q = _c1.text_input(t("Search"), key="cat_q", placeholder=t("name, category…"),
                        label_visibility="collapsed")
    # ⚠️ Se comparan abajo (`_tipo == "Productos"`) → se traduce el display, no la opción.
    _TIPO = {"Todos": "All", "Productos": "Products", "Servicios": "Services"}
    _tipo = _c2.radio(t("Type"), list(_TIPO), format_func=lambda o: t(_TIPO[o]),
                      horizontal=True, key="cat_tipo", label_visibility="collapsed")
    if _q.strip():
        _n = _q.strip().casefold()
        items = [i for i in items
                 if _n in f"{i.get('Name','')} {i.get('Category','')} {i.get('Description','')}".casefold()]
    if _tipo == "Productos":
        items = [i for i in items if str(i.get("Type", "")) == CAT.PRODUCTO]
    elif _tipo == "Servicios":
        items = [i for i in items if str(i.get("Type", "")) == CAT.SERVICIO]

    if items:
        st.caption(t("Tap an item to edit it. **Cost** is what it costs you; the margin is set when quoting, line by line."))
        df = pd.DataFrame([{
            "Item": i.get("Name", ""),
            "Tipo": _etq(str(i.get("Type", ""))),
            "Category": _etq(str(i.get("Category", ""))) or "—",
            "Unidad": _etq(str(i.get("Unit", ""))) or "—",
            # ⚠️ NaN, no None: una columna ENTERA de None la deja pandas en
            # `object` y Streamlit pinta el literal «None» (pasaba con un
            # catalogo de solo productos).
            "Horas": (round(_num(i.get("EstHours")), 2)
                      if str(i.get("Type", "")) == CAT.SERVICIO else float("nan")),
            "Costo": CAT.costo_de(i, 1),
            "Activo": "🟢" if str(i.get("Active", "SI")).upper() != "NO" else "🔴",
        } for i in items])
        _ev = st.dataframe(df, width="stretch", hide_index=True,
                           on_select="rerun", selection_mode="single-row", key="cat_tbl",
                           column_config=tabla.cfg(None, {"Costo": st.column_config.NumberColumn(
                               t("Cost"), format="$%,.2f", help=t("Product: unit cost. Service: hours × rate."))}))
        _sr = list(_ev.selection.rows)
        if _sr and _sr[0] < len(items):
            st.session_state["_cat_open"] = str(items[_sr[0]].get("ID", ""))
            st.session_state.pop("cat_tbl", None)
            st.rerun()
        st.caption(f"{len(items)} item(s)")
    else:
        st.caption(t("No items yet. Create the first one below."))

    _alta(grupo)


def _alta(grupo):
    with st.expander(t(":material/add_circle: New item")):
        # ⚠️ El tipo va FUERA del form: dentro, los widgets no escriben hasta el submit
        # y no se podrían mostrar solo los campos que aplican (misma razón que v189/v306).
        tipo = st.radio(t("Type"), list(CAT.TIPOS), horizontal=True, key="cat_new_tipo",
                        format_func=lambda _k: _TIPO_LBL.get(_k, _k))
        with st.form("cat_new"):
            c1, c2 = st.columns(2)
            nombre = c1.text_input(t("Name"), placeholder=t("e.g. Rail T75-3/B"))
            categoria = c2.selectbox(t("Category"), CAT.categorias(grupo), key="cat_new_cat")
            if tipo == CAT.SERVICIO:
                c3, c4 = st.columns(2)
                horas = c3.number_input(t("Estimated hours"), min_value=0.0, step=0.5,
                                        help=t("This is what gets compared later against the hours clocked."))
                tarifa = c4.number_input(t("Rate/hour (cost)"), min_value=0.0, step=5.0)
                costo, unidad = 0.0, "hora"
            else:
                c3, c4 = st.columns(2)
                costo = c3.number_input(t("Unit cost"), min_value=0.0, step=1.0)
                unidad = c4.selectbox(t("Unit"), CAT.UNIDADES, key="cat_new_uni")
                horas = tarifa = 0.0
            desc = st.text_input(t("Description (optional)"),
                                 placeholder=t("what the client will see on the quote"))
            if st.form_submit_button(t(":material/save: Save item"),
                                     width="stretch"):
                ok, msg = CAT.crear(grupo, nombre, tipo=tipo, costo_unit=costo,
                                    horas_est=horas, tarifa_hora=tarifa, unidad=unidad,
                                    categoria=categoria, descripcion=desc,
                                    creado_por=_creado_por())
                if ok:
                    flash.exito(f"Item {msg} created.")
                    st.rerun()
                else:
                    st.error(msg)


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

    es_serv = str(it.get("Type", "")) == CAT.SERVICIO
    activo = str(it.get("Active", "SI")).upper() != "NO"
    st.markdown(f"## :material/sell: {it.get('Name', '')}")
    st.markdown(f"**{it.get('ID', '')}**  ·  {_TIPO_LBL.get(str(it.get('Type','')), '')}"
                f"  ·  {_etq(str(it.get('Category', ''))) or '—'}  ·  "
                f"cost {T.dinero(CAT.costo_de(it, 1))}"
                + ("" if activo else "  ·  :red[" + t("inactive") + "]"))

    with st.form(f"cat_edit_{cid}"):
        c1, c2 = st.columns(2)
        nombre = c1.text_input(t("Name"), value=str(it.get("Name", "")))
        categoria = c2.selectbox(t("Category"), CAT.categorias(grupo),
                                 index=max(0, CAT.categorias(grupo).index(str(it.get("Category", "")))
                                           if str(it.get("Category", "")) in CAT.categorias(grupo) else 0))
        if es_serv:
            c3, c4 = st.columns(2)
            horas = c3.number_input(t("Estimated hours"), min_value=0.0, step=0.5,
                                    value=float(_num(it.get("EstHours"))))
            tarifa = c4.number_input(t("Rate/hour (cost)"), min_value=0.0, step=5.0,
                                     value=float(_num(it.get("HourlyRate"))))
            campos = {"EstHours": horas, "HourlyRate": tarifa}
        else:
            c3, c4 = st.columns(2)
            costo = c3.number_input(t("Unit cost"), min_value=0.0, step=1.0,
                                    value=float(_num(it.get("UnitCost"))))
            unidad = c4.selectbox(t("Unit"), CAT.UNIDADES,
                                  index=max(0, list(CAT.UNIDADES).index(str(it.get("Unit", "")))
                                            if str(it.get("Unit", "")) in CAT.UNIDADES else 0))
            campos = {"UnitCost": costo, "Unit": unidad}
        desc = st.text_input(t("Description"), value=str(it.get("Description", "")))
        if st.form_submit_button(t(":material/save: Save changes"), width="stretch"):
            campos.update({"Name": nombre, "Category": categoria, "Description": desc})
            ok, msg = CAT.actualizar(cid, campos)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()

    st.caption(t("Changing the cost **does not alter** quotes already issued: each line keeps its own copy of the agreed price."))

    # ⚠️ v340: desactivar SIEMPRE con vuelta, y en el mismo sitio.
    if activo:
        with st.expander(t(":material/archive: Deactivate item")):
            st.caption(t("It stops being offered when quoting, but is not deleted: quotes already using it keep showing it."))
            if st.button(t(":material/archive: Deactivate"), key=f"cat_off_{cid}",
                         width="stretch"):
                ok, msg = CAT.set_activo(cid, False)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
    else:
        st.warning(t(":material/block: This item is **deactivated**: it does not appear when quoting unless you tick «Show deactivated ones too»."))
        if st.button(t(":material/restore: Reactivate"), key=f"cat_on_{cid}", type="primary"):
            ok, msg = CAT.set_activo(cid, True)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()
