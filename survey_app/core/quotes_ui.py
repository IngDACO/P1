"""📄 Cotizaciones — armar el precio desde el catálogo (v353).

⚠️ SIN cabecera propia: `home_ui._sub_header` ya pinta «Finanzas · Cotizaciones».
"""
import pandas as pd
import streamlit as st

from core import flash

from core import catalogo as CAT
from core import clock
from core import clientes as C
from core import quotes as Q
from core import tenant
from core import theme as T
from core.num import num as _num

_EST_FMT = {Q.BORRADOR: ":gray[:material/edit_note:] borrador",
            Q.ENVIADA: ":blue[:material/send:] enviada",
            Q.ACEPTADA: ":green[:material/check_circle:] aceptada",
            Q.RECHAZADA: ":gray[:material/block:] rechazada",
            Q.VENCIDA: ":red[:material/schedule:] vencida"}


def _creado_por() -> str:
    a = st.session_state.get("auth") or {}
    return str(a.get("usuario", "") or a.get("nombre", ""))


def render_cotizaciones(grupo):
    if not Q.is_configured():
        st.info(":material/info: Configura Google Sheets para cotizar.")
        return
    if st.session_state.get("_cot_nueva"):
        _nueva(grupo)
        return
    if st.session_state.get("_cot_open"):
        _detalle(grupo, st.session_state["_cot_open"])
        return

    r = Q.resumen(grupo)
    T.kpi_row([
        ("En la calle", T.dinero(r["en_calle"], 0),
         f"{r['por_estado'].get(Q.ENVIADA, 0)} enviada(s) sin respuesta", T.AMBAR),
        ("Ganado", T.dinero(r["ganado"], 0),
         f"{r['por_estado'].get(Q.ACEPTADA, 0)} aceptada(s)", T.VERDE),
        # ⚠️ sin cotizaciones decididas la conversión NO es 0%: es que aún no se puede
        # calcular. Un 0% ahí sería la trampa de v320 («sin asignar» que mentía).
        ("Conversión", f"{r['conversion']:.0f}%" if r["conversion"] is not None else "—",
         "de las decididas" if r["conversion"] is not None else "aún no hay decididas"),
        ("Cotizaciones", str(r["n"]), f"{r['por_estado'].get(Q.VENCIDA, 0)} vencida(s)"),
    ])

    if st.button(":material/add_circle: Nueva cotización", type="primary", key="cot_new_btn"):
        st.session_state["_cot_nueva"] = True
        st.rerun()

    cots = Q.list_cotizaciones(grupo)
    if not cots:
        st.caption("Todavía no hay cotizaciones. Empieza con «Nueva cotización» — "
                   "los artículos salen de :material/sell: Catálogo.")
        return

    _venc = [c for c in cots if Q.estado_de(c) == Q.VENCIDA]
    if _venc:
        st.warning(":material/schedule: **" + str(len(_venc)) + " cotización(es) vencida(s)** "
                   "sin respuesta: " + " · ".join(
                       f"{c.get('ClienteNombre','')} ({T.dinero(c.get('Total'), 0)})"
                       for c in _venc[:5])
                   + ". Saca una versión nueva si sigue en pie.")

    st.caption("Toca una cotización para ver el detalle, el PDF y marcar el resultado.")
    df = pd.DataFrame([{
        "Nº": str(c.get("Numero", "")) + (f" v{int(_num(c.get('Version'), 1))}"
                                          if _num(c.get("Version"), 1) > 1 else ""),
        "Cliente": c.get("ClienteNombre", "") or "—",
        "Fecha": c.get("Fecha", ""),
        "Vence": c.get("Validez", "") or "—",
        "Total": round(_num(c.get("Total")), 2),
        "Margen": round(_num(c.get("MargenPct")), 1),
        "Estado": Q.estado_de(c),
    } for c in cots])
    _ev = st.dataframe(df, use_container_width=True, hide_index=True,
                       on_select="rerun", selection_mode="single-row", key="cot_tbl",
                       column_config={
                           "Total": st.column_config.NumberColumn("Total", format="$%,.2f"),
                           "Margen": st.column_config.NumberColumn("Margen", format="%.1f%%")})
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
        st.warning(":material/sell: El catálogo está vacío. Da de alta productos y "
                   "servicios en :material/sell: Catálogo antes de cotizar.")
        return lineas
    etq = CAT.etiqueta_items(items)          # v306: el ID solo si el nombre se repite
    _sel = st.multiselect("Añadir del catálogo", list(etq),
                          format_func=lambda i: etq.get(i, i), key=f"{key}_sel",
                          help="Elige los artículos; luego ajustas cantidad y margen.")
    if _sel and st.button(":material/add: Añadir a la cotización", key=f"{key}_add"):
        _m = auth.group_margin_default(grupo)
        _ya = {l.get("catalogo_id") for l in lineas}
        for cid in _sel:
            if cid in _ya:
                continue
            lineas.append(Q.linea_de(CAT.get_item(cid), 1, _m))
        st.session_state[f"{key}_lineas"] = lineas
        st.rerun()

    if not lineas:
        st.caption("Sin líneas todavía.")
        return lineas

    st.markdown("**Líneas** — pon **cuánto quieres ganar** en cada rubro; "
                "el margen % y el precio salen solos")
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
        hide_index=True, use_container_width=True, key=f"{key}_ed",
        # ⚠️ v355: lo único que se teclea del precio es la GANANCIA. El margen y el
        # precio son consecuencia, y se muestran bloqueados para que quede claro.
        disabled=["Concepto", "Costo", "Margen %", "Precio"],
        column_config={
            "Costo": st.column_config.NumberColumn("Costo", format="$%,.2f",
                                                   help="Lo que te cuesta a ti. No lo ve el cliente."),
            "Ganancia $": st.column_config.NumberColumn(
                "Ganancia $", format="$%,.2f", min_value=0.0,
                help="Lo que quieres ganar en este rubro. El margen % se calcula solo."),
            "Margen %": st.column_config.NumberColumn("Margen %", format="%.1f%%",
                                                      help="Se calcula: ganancia ÷ costo."),
            "Precio": st.column_config.NumberColumn("Precio", format="$%,.2f",
                                                    help="Costo + ganancia. Es lo que ve el cliente."),
            "Cant.": st.column_config.NumberColumn("Cant.", min_value=0.0)})

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
    if st.button(":material/arrow_back: Cancelar", key="cot_new_back"):
        for k in ("_cot_nueva", "new_lineas", "new_sel"):
            st.session_state.pop(k, None)
        st.rerun()
    st.markdown("## :material/request_quote: Nueva cotización")

    fichas = C.list_clientes(grupo)
    if not fichas:
        st.warning(":material/contacts: No hay clientes. Créalos en :material/contacts: Contactos.")
        return
    _map = {f"{f.get('Nombre','')}": f for f in fichas}
    _cli = st.selectbox("Cliente", list(_map), key="cot_new_cli")

    lineas = st.session_state.get("new_lineas", [])
    lineas = _editor_lineas(grupo, "new", lineas)
    st.session_state["new_lineas"] = lineas

    imp = st.number_input("Impuesto %", min_value=0.0, step=1.0,
                          value=float(auth.group_tax_default(grupo)), key="cot_new_imp",
                          help="Sale del valor por defecto del grupo.")
    nota = st.text_area("Notas para el cliente (opcional)", key="cot_new_nota")

    if lineas:
        t = Q.totales(lineas, imp)
        _totales_html(t, imp)
        if st.button(":material/save: Crear cotización", type="primary",
                     key="cot_new_save", use_container_width=True):
            f = _map[_cli]
            ok, msg = Q.crear(grupo, f.get("ID", ""), f.get("Nombre", ""), lineas,
                              impuesto_pct=imp, nota=nota, creado_por=_creado_por())
            if ok:
                for k in ("_cot_nueva", "new_lineas", "new_sel"):
                    st.session_state.pop(k, None)
                st.session_state["_cot_open"] = msg
                st.rerun()
            else:
                st.error(msg)


def _totales_html(t: dict, imp_pct):
    """Totales + lo que el cliente NO ve (costo y ganancia), que es lo que te interesa."""
    T.kpi_row([
        ("Subtotal", T.dinero(t["subtotal"], 0), "antes de impuesto"),
        ("Impuesto", T.dinero(t["impuesto"], 0), f"{_num(imp_pct):g}%"),
        ("Total al cliente", T.dinero(t["total"], 0), "lo que se le cobra", T.AZUL),
        ("Tu ganancia", T.dinero(t["ganancia"], 0),
         f"margen efectivo {t['margen_pct']:.1f}%", T.VERDE),
    ])
    if t["horas"]:
        st.caption(f":material/schedule: La cotización incluye **{t['horas']:g} horas** de "
                   "servicio. Al aceptarla podrás compararlas con las horas fichadas.")


# ── Detalle ──────────────────────────────────────────────────────
def _detalle(grupo, cid):
    if st.button(":material/arrow_back: Volver a cotizaciones", key="cot_back"):
        st.session_state.pop("_cot_open", None)
        st.rerun()
    c = Q.get_cotizacion(cid)
    if not c:
        st.warning("Cotización no encontrada.")
        st.session_state.pop("_cot_open", None)
        return
    # v351: `get_cotizacion` busca por ID en toda la hoja, sin mirar el grupo.
    if not tenant.exigir(c, "Esta cotización"):
        st.session_state.pop("_cot_open", None)
        return

    est = Q.estado_de(c)
    _ver = int(_num(c.get("Version"), 1))
    st.markdown(f"## :material/request_quote: Cotización Nº {c.get('Numero', '')}"
                + (f"  ·  v{_ver}" if _ver > 1 else ""))
    st.markdown(f"**{c.get('ClienteNombre', '') or '—'}**  ·  {_EST_FMT.get(est, est)}"
                f"  ·  válida hasta {c.get('Validez', '') or '—'}"
                + (f"  ·  viene de {c.get('Origen')}" if c.get("Origen") else ""))

    lineas = Q.lineas_de(c)
    t = Q.totales(lineas, _num(c.get("ImpuestoPct")))

    if est == Q.BORRADOR:
        _des = Q.desactualizadas(c)
        if _des:
            _txt = " · ".join(
                str(d["linea"].get("concepto", "")) + ": "
                + T.dinero(d["linea"].get("costo_total"))
                + (" → " + T.dinero(d["costo_hoy"]) if d["costo_hoy"] is not None
                   else " (" + d["motivo"] + ")")
                for d in _des[:6])
            st.warning(":material/sync_problem: **El catálogo cambió** desde que armaste "
                       "esta cotización: " + _txt + ". Los precios de la cotización NO se "
                       "tocan solos.")
            if st.button(":material/sync: Actualizar precios desde el catálogo",
                         key="cot_upd_" + str(cid),
                         help="Trae los costos de hoy conservando lo que quieres ganar "
                              "en cada línea."):
                ok, msg = Q.actualizar_precios(cid)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
        nuevas = _editor_lineas(grupo, f"ed{cid}", lineas)
        if nuevas != lineas:
            if st.button(":material/save: Guardar cambios", key=f"cot_save_{cid}",
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
        } for l in lineas]), hide_index=True, use_container_width=True,
            column_config={"Precio": st.column_config.NumberColumn("Precio", format="$%,.2f")})
        _totales_html(t, c.get("ImpuestoPct"))

    # ── Acciones según el estado ─────────────────────────────────
    st.markdown("---")
    a1, a2, a3 = st.columns(3)
    if est == Q.BORRADOR:
        if a1.button(":material/send: Marcar como enviada", key=f"cot_env_{cid}",
                     type="primary", use_container_width=True):
            ok, msg = Q.set_estado(cid, Q.ENVIADA)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()
    elif est in (Q.ENVIADA, Q.VENCIDA):
        if a1.button(":material/check_circle: El cliente la aceptó", key=f"cot_ok_{cid}",
                     type="primary", use_container_width=True):
            ok, msg = Q.set_estado(cid, Q.ACEPTADA)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()
        if a2.button(":material/block: La rechazó", key=f"cot_no_{cid}",
                     use_container_width=True):
            ok, msg = Q.set_estado(cid, Q.RECHAZADA)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()
    if est != Q.BORRADOR:
        if a3.button(":material/content_copy: Nueva versión", key=f"cot_v2_{cid}",
                     use_container_width=True,
                     help="Clona esta cotización como borrador para cambiarla. La actual se conserva."):
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
        st.download_button(":material/download: Descargar cotización (PDF)", data=pdf,
                           file_name=f"Cotizacion_{c.get('Numero','')}.pdf",
                           mime="application/pdf", key=f"cot_pdf_{cid}")
    except Exception as e:
        st.warning(f":material/warning: No se pudo generar el PDF: {e}")

    # ── Fase 3: de cotización ganada a obra ──────────────────────
    if est == Q.ACEPTADA and not str(c.get("ProyectoID", "")).strip():
        _crear_proyecto(grupo, c, t)
    elif str(c.get("ProyectoID", "")).strip():
        _comparacion(cid, c)


def _crear_proyecto(grupo, c, t):
    """Aceptada y sin obra todavía: darla de alta con lo ya pactado."""
    st.markdown("---")
    st.markdown("### :material/construction: Convertirla en proyecto")
    st.caption("Nace con el cliente, el presupuesto y el margen que acabas de cotizar. "
               "Desde ahí sigue el flujo de siempre: costos, horas y factura.")
    with st.form("cot_prj_" + str(c.get("ID"))):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre del proyecto",
                               value=str(c.get("ClienteNombre", "")) + " — Nº"
                                     + str(c.get("Numero", "")))
        tipo = c2.selectbox("Tipo", ["Instalación", "Delivery", "Ripout", "Otro"])
        c3, c4 = st.columns(2)
        ini = c3.date_input("Fecha de inicio", value=clock.today(grupo))
        ns = c4.number_input("Paradas (NS)", min_value=0, step=1, value=0,
                             help="Solo la instalación genera el cronograma estándar; "
                                  "con NS 0 el proyecto nace sin actividades.")
        ubic = st.text_input("Ubicación (opcional)")
        st.info(":material/savings: Presupuesto del proyecto: **"
                + T.dinero(t["costo"], 0) + "** — es tu **costo** cotizado, no el precio "
                "al cliente (" + T.dinero(t["subtotal"], 0) + "). Así la alerta de "
                "sobre-presupuesto salta cuando te comes el margen, no cuando ya "
                "estás perdiendo dinero.")
        if st.form_submit_button(":material/add_circle: Crear el proyecto",
                                 type="primary", use_container_width=True):
            ok, msg = Q.aceptar_y_crear_proyecto(
                c.get("ID"), nombre=nombre, tipo=tipo, fecha_inicio=ini,
                ns=ns, ubicacion=ubic, creado_por=_creado_por())
            if ok:
                flash.exito("Proyecto " + str(msg) + " creado desde esta cotización.")
                st.rerun()
            else:
                st.error(msg)


def _comparacion(cid, c):
    """Cotizado contra real: lo que hace que cotizar sirva para gestionar."""
    st.markdown("---")
    comp = Q.comparacion(cid)
    if not comp:
        st.caption("Enlazada al proyecto " + str(c.get("ProyectoID")) + ".")
        return
    st.markdown("### :material/compare_arrows: Cotizado vs. real — " + comp["proyecto"])

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
        _g, _etq, _pie = comp["ganancia_real"], "Ganancia real", "obra terminada"
    elif comp["ganancia_proyectada"] is not None:
        _g, _etq = comp["ganancia_proyectada"], "Ganancia proyectada"
        _pie = "al ritmo actual · cotizaste " + T.dinero(_gc, 0)
    else:
        _g, _etq, _pie = None, "Ganancia proyectada", "aún no hay avance ni costo"
    _cg = T.VERDE if (_g is not None and _g >= _gc) else (T.ROJO if _g is not None else None)
    T.kpi_row([
        _tarj("Horas", comp["horas"], "h"),
        _tarj("Costo", comp["costo"]),
        ("Ingreso", T.dinero(comp["ingreso"], 0), "lo que aceptó el cliente"),
        (_etq, T.dinero(_g, 0) if _g is not None else "—", _pie, _cg),
    ])
    if comp["costo_proyectado"] is not None:
        st.caption(":material/trending_up: Al ritmo actual la obra costará "
                   + T.dinero(comp["costo_proyectado"], 0) + " contra los "
                   + T.dinero(comp["costo"]["cotizado"], 0) + " cotizados.")
    _av = comp["avance"]
    if comp["costo"]["dif"] > 0 and _av < 100:
        st.warning(":material/warning: Llevas **" + T.dinero(comp["costo"]["dif"], 0)
                   + " por encima** de lo cotizado con el proyecto al **"
                   + ("%.0f" % _av) + "%**. A este ritmo la ganancia final será menor "
                   "que la cotizada.")
    elif comp["costo"]["dif"] <= 0 and _av > 0:
        st.success(":material/check_circle: Vas **"
                   + T.dinero(abs(comp["costo"]["dif"]), 0) + " por debajo** de lo "
                   "cotizado con el proyecto al " + ("%.0f" % _av) + "%.")
    if st.button(":material/folder: Abrir " + comp["proyecto"], key="cot_prj_open_" + str(cid)):
        from core import home_ui
        st.session_state["_prjsel_pending"] = comp["proyecto_id"]
        st.session_state["_admin_open_proj"] = comp["proyecto_id"]
        home_ui.navegar("proyectos", "📊 Proyectos")
