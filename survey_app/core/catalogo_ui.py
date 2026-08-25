"""📚 Catálogo — productos y servicios con su costo (v352).

Base de las cotizaciones. ⚠️ SIN cabecera propia: `home_ui._sub_header` ya pinta
«Finanzas · Catálogo» encima — era el título duplicado que salió cuatro veces
(v212, v291, v314, v319).
"""
import pandas as pd
import streamlit as st

from core import flash

from core import catalogo as CAT
from core import tenant
from core import theme as T
from core.num import num as _num


def _creado_por() -> str:
    a = st.session_state.get("auth") or {}
    return str(a.get("usuario", "") or a.get("nombre", ""))


_TIPO_LBL = {CAT.PRODUCTO: ":material/inventory_2: producto",
             CAT.SERVICIO: ":material/engineering: servicio"}


def render_catalogo(grupo):
    if not CAT.is_configured():
        st.info(":material/info: Configura Google Sheets para usar el catálogo.")
        return
    if st.session_state.get("_cat_open"):
        _detalle(grupo, st.session_state["_cat_open"])
        return

    r = CAT.resumen(grupo)
    T.kpi_row([
        ("Artículos", str(r["n"]), "activos en el catálogo"),
        ("Productos", str(r["productos"]), "se cobran por cantidad"),
        ("Servicios", str(r["servicios"]), "se cobran por horas"),
    ])

    # ⚠️ v340: si se puede desactivar, tiene que poder VOLVER — y verse cuántos hay.
    _ver_inact = st.checkbox(":material/archive: Ver también los desactivados",
                             key="cat_ver_inact",
                             help=f"Hay {r['inactivos']} desactivado(s). No se borran: "
                                  "las cotizaciones viejas deben seguir mostrando su nombre.")
    items = CAT.list_items(grupo, incluir_inactivos=_ver_inact)

    _c1, _c2 = st.columns([3, 2])
    _q = _c1.text_input("Buscar", key="cat_q", placeholder="nombre, categoría…",
                        label_visibility="collapsed")
    _tipo = _c2.radio("Tipo", ["Todos", "Productos", "Servicios"], horizontal=True,
                      key="cat_tipo", label_visibility="collapsed")
    if _q.strip():
        _n = _q.strip().casefold()
        items = [i for i in items
                 if _n in f"{i.get('Nombre','')} {i.get('Categoria','')} {i.get('Descripcion','')}".casefold()]
    if _tipo == "Productos":
        items = [i for i in items if str(i.get("Tipo", "")) == CAT.PRODUCTO]
    elif _tipo == "Servicios":
        items = [i for i in items if str(i.get("Tipo", "")) == CAT.SERVICIO]

    if items:
        st.caption("Toca un artículo para editarlo. **Costo** es lo que te cuesta a ti; "
                   "el margen se pone al cotizar, línea por línea.")
        df = pd.DataFrame([{
            "Artículo": i.get("Nombre", ""),
            "Tipo": str(i.get("Tipo", "")),
            "Categoría": i.get("Categoria", "") or "—",
            "Unidad": i.get("Unidad", "") or "—",
            "Horas": (round(_num(i.get("HorasEst")), 2)
                      if str(i.get("Tipo", "")) == CAT.SERVICIO else None),
            "Costo": CAT.costo_de(i, 1),
            "Activo": "🟢" if str(i.get("Activo", "SI")).upper() != "NO" else "🔴",
        } for i in items])
        _ev = st.dataframe(df, width="stretch", hide_index=True,
                           on_select="rerun", selection_mode="single-row", key="cat_tbl",
                           column_config={"Costo": st.column_config.NumberColumn(
                               "Costo", format="$%,.2f", help="Producto: costo unitario. "
                                                             "Servicio: horas × tarifa.")})
        _sr = list(_ev.selection.rows)
        if _sr and _sr[0] < len(items):
            st.session_state["_cat_open"] = str(items[_sr[0]].get("ID", ""))
            st.session_state.pop("cat_tbl", None)
            st.rerun()
        st.caption(f"{len(items)} artículo(s)")
    else:
        st.caption("Todavía no hay artículos. Crea el primero abajo.")

    _alta(grupo)


def _alta(grupo):
    with st.expander(":material/add_circle: Nuevo artículo"):
        # ⚠️ El tipo va FUERA del form: dentro, los widgets no escriben hasta el submit
        # y no se podrían mostrar solo los campos que aplican (misma razón que v189/v306).
        tipo = st.radio("Tipo", list(CAT.TIPOS), horizontal=True, key="cat_new_tipo",
                        format_func=lambda t: _TIPO_LBL.get(t, t))
        with st.form("cat_new"):
            c1, c2 = st.columns(2)
            nombre = c1.text_input("Nombre", placeholder="p. ej. Riel T75-3/B")
            categoria = c2.selectbox("Categoría", CAT.categorias(grupo), key="cat_new_cat")
            if tipo == CAT.SERVICIO:
                c3, c4 = st.columns(2)
                horas = c3.number_input("Horas estimadas", min_value=0.0, step=0.5,
                                        help="Lo que se compara luego contra las horas fichadas.")
                tarifa = c4.number_input("Tarifa/hora (costo)", min_value=0.0, step=5.0)
                costo, unidad = 0.0, "hora"
            else:
                c3, c4 = st.columns(2)
                costo = c3.number_input("Costo unitario", min_value=0.0, step=1.0)
                unidad = c4.selectbox("Unidad", CAT.UNIDADES, key="cat_new_uni")
                horas = tarifa = 0.0
            desc = st.text_input("Descripción (opcional)",
                                 placeholder="lo que verá el cliente en la cotización")
            if st.form_submit_button(":material/save: Guardar artículo",
                                     width="stretch"):
                ok, msg = CAT.crear(grupo, nombre, tipo=tipo, costo_unit=costo,
                                    horas_est=horas, tarifa_hora=tarifa, unidad=unidad,
                                    categoria=categoria, descripcion=desc,
                                    creado_por=_creado_por())
                if ok:
                    flash.exito(f"Artículo {msg} creado.")
                    st.rerun()
                else:
                    st.error(msg)


def _detalle(grupo, cid):
    if st.button(":material/arrow_back: Volver al catálogo", key="cat_back"):
        st.session_state.pop("_cat_open", None)
        st.rerun()
    it = CAT.get_item(cid)
    if not it:
        st.warning("Artículo no encontrado.")
        st.session_state.pop("_cat_open", None)
        return
    # v351: `get_item` busca por ID en TODA la hoja, sin mirar el grupo.
    if not tenant.exigir(it, "Este artículo"):
        st.session_state.pop("_cat_open", None)
        return

    es_serv = str(it.get("Tipo", "")) == CAT.SERVICIO
    activo = str(it.get("Activo", "SI")).upper() != "NO"
    st.markdown(f"## :material/sell: {it.get('Nombre', '')}")
    st.markdown(f"**{it.get('ID', '')}**  ·  {_TIPO_LBL.get(str(it.get('Tipo','')), '')}"
                f"  ·  {it.get('Categoria', '') or '—'}  ·  "
                f"costo {T.dinero(CAT.costo_de(it, 1))}"
                + ("" if activo else "  ·  :red[desactivado]"))

    with st.form(f"cat_edit_{cid}"):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre", value=str(it.get("Nombre", "")))
        categoria = c2.selectbox("Categoría", CAT.categorias(grupo),
                                 index=max(0, CAT.categorias(grupo).index(str(it.get("Categoria", "")))
                                           if str(it.get("Categoria", "")) in CAT.categorias(grupo) else 0))
        if es_serv:
            c3, c4 = st.columns(2)
            horas = c3.number_input("Horas estimadas", min_value=0.0, step=0.5,
                                    value=float(_num(it.get("HorasEst"))))
            tarifa = c4.number_input("Tarifa/hora (costo)", min_value=0.0, step=5.0,
                                     value=float(_num(it.get("TarifaHora"))))
            campos = {"HorasEst": horas, "TarifaHora": tarifa}
        else:
            c3, c4 = st.columns(2)
            costo = c3.number_input("Costo unitario", min_value=0.0, step=1.0,
                                    value=float(_num(it.get("CostoUnit"))))
            unidad = c4.selectbox("Unidad", CAT.UNIDADES,
                                  index=max(0, list(CAT.UNIDADES).index(str(it.get("Unidad", "")))
                                            if str(it.get("Unidad", "")) in CAT.UNIDADES else 0))
            campos = {"CostoUnit": costo, "Unidad": unidad}
        desc = st.text_input("Descripción", value=str(it.get("Descripcion", "")))
        if st.form_submit_button(":material/save: Guardar cambios", width="stretch"):
            campos.update({"Nombre": nombre, "Categoria": categoria, "Descripcion": desc})
            ok, msg = CAT.actualizar(cid, campos)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()

    st.caption("Cambiar el costo **no altera** las cotizaciones ya emitidas: cada línea "
               "guarda su propia copia del precio pactado.")

    # ⚠️ v340: desactivar SIEMPRE con vuelta, y en el mismo sitio.
    if activo:
        with st.expander(":material/archive: Desactivar artículo"):
            st.caption("Deja de ofrecerse al cotizar, pero no se borra: las cotizaciones "
                       "que ya lo usan siguen mostrándolo.")
            if st.button(":material/archive: Desactivar", key=f"cat_off_{cid}",
                         width="stretch"):
                ok, msg = CAT.set_activo(cid, False)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
    else:
        st.warning(":material/block: Este artículo está **desactivado**: no aparece al "
                   "cotizar salvo que marques «Ver también los desactivados».")
        if st.button(":material/restore: Reactivar", key=f"cat_on_{cid}", type="primary"):
            ok, msg = CAT.set_activo(cid, True)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()
