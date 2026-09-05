"""📦 Inventario — UI de control de activos (v263, Fase 1).

KPIs + lista filtrable → ficha (foto, QR + etiqueta PDF, datos, valor depreciado,
edición, baja) + registro + catálogo de categorías. Solo admin/propietario.
Movimientos (entradas/salidas) y el escaneo que abre la ficha llegan en la Fase 2.
"""
import logging

from core.i18n import t, etiqueta as _etq
import pandas as pd
import streamlit as st

from core import flash

from core import tenant
from core import clock
from core import inventory as INV
from core.num import num as _num
from core import tabla

logger = logging.getLogger(__name__)


def _creado_por() -> str:
    a = st.session_state.get("auth") or {}
    return str(a.get("usuario", "") or a.get("nombre", ""))


# ⚠️ Solo el COLOR. El TEXTO vive en `i18n.VALORES` desde v463: tenerlo aquí además
# dejaba DOS definiciones del mismo estado, y por eso la ficha del activo decía
# «available» y su tabla «disponible» — el mismo activo en dos idiomas a dos clics.
# ⚠️ Las CLAVES son el estado guardado en la hoja y NO se tocan: `inventory.py` e
# `inventory_ui` los comparan (`== "en_uso"`, `== "disponible"`), así que traducir el
# dato dejaría esas dos ramas muertas sin dar ningún error (v442).
_EST_COLOR = {"disponible": "green", "en_uso": "blue", "mantenimiento": "orange",
              "dañado": "red", "baja": "gray"}


def _est_lbl(estado) -> str:
    """El estado del activo CON su color, en el idioma de la pantalla.

    ⚠️ Devuelve MARKDOWN de color, así que vale para `st.markdown` y NO para una celda
    de `st.dataframe`, que lo pintaría literal (`:green[available]`). En una tabla va
    `_etq(...)` pelado — que es el mismo texto, sin el color.
    """
    _e = str(estado)
    _c = _EST_COLOR.get(_e)
    return f":{_c}[{_etq(_e)}]" if _c else _etq(_e)


def _ubic_txt(a) -> str:
    """Ubicación legible. ⚠️ Delega en `INV.ubic_str` (v306): esta función era una COPIA
    de la del backend, así que al hacer que el proyecto se guarde por ID solo se habría
    arreglado una de las dos y la lista seguiría enseñando `PRJ-0007` (el patrón de dos
    mecanismos para lo mismo que v140 mandó no repetir)."""
    return INV.ubic_str(a, _etq)


def _fecha_input(label, valor, key):
    """date_input opcional (None permitido) → devuelve ISO o ''. """
    d0 = None
    try:
        from datetime import date
        d0 = date.fromisoformat(str(valor)[:10]) if str(valor).strip() else None
    except Exception:
        d0 = None
    v = st.date_input(label, value=d0, key=key, format="YYYY-MM-DD")
    return v.isoformat() if v else ""


def _usuarios(grupo):
    try:
        from core import auth
        return [str(u.get("Usuario", "")) for u in auth.list_users(grupo)
                if str(u.get("Usuario", "")).strip()]
    except Exception:
        return []


def _proyectos(grupo):
    """`(ids, etiqueta)` de los proyectos del grupo, para elegir destino.

    ⚠️ v306: se guarda el **ID** en `UbicacionRef`, no el nombre. Antes se guardaba el
    nombre y con dos proyectos homónimos era imposible saber en cuál está el activo
    (y renombrar un proyecto dejaba huérfano el histórico, como pasaba con las horas
    antes de v145). Las filas antiguas siguen leyéndose: `ubic_proyecto` resuelve el
    ID si lo es y, si no, muestra el texto tal cual.
    """
    try:
        from core import projects as P
        # v422: **con las localizaciones internas**. Un activo vive en el ALMACÉN más
        # que en ninguna obra: excluirlas dejaría el inventario sin su ubicación natural.
        _ps = [p for p in P.list_projects(grupo=grupo, incluir_internos=True)
               if str(p.get("ID", "")).strip()]
        _lbl = P.etiqueta_proyectos(_ps)
        return [str(p.get("ID", "")) for p in _ps], _lbl
    except Exception:
        return [], {}


# ── Vista principal ──────────────────────────────────────────────
def render_inventario(grupo):
    st.markdown(t("## :material/inventory_2: Asset inventory"))
    if not INV.is_configured():
        st.info(t(":material/info: Configure Google Sheets for the inventory."))
        return
    if st.session_state.get("_inv_nuevo"):
        _registro(grupo)
        return
    if st.session_state.get("_inv_open"):
        _detalle(grupo, st.session_state["_inv_open"])
        return

    r = INV.resumen(grupo)
    est = r["por_estado"]
    c = st.columns(5)
    c[0].metric(t("Assets"), r["n"])
    c[1].metric(t("Available"), est.get("disponible", 0))
    c[2].metric(t("In use"), est.get("en_uso", 0))
    c[3].metric(t("Current value"), f"${r['valor_actual']:,.0f}",
                help=f"Purchase value: ${r['valor_compra']:,.0f} (straight-line depreciated)")
    c[4].metric(t("Service overdue"), r["mant_vencido"])

    if st.button(t(":material/add_circle: Register asset"), type="primary", key="inv_new"):
        st.session_state["_inv_nuevo"] = True
        st.rerun()

    # ⚠️ v340: dar de baja un activo era un VIAJE SIN VUELTA — `dar_de_baja` marca
    # `Activo=NO` y la lista usaba el default, que lo oculta, sin casilla para verlo
    # ni forma de reactivarlo. Mismo fallo que tenían los clientes y que v149 ya
    # había resuelto para los proyectos.
    _ver_baja = st.checkbox(t(":material/archive: Show written-off ones too"),
                            key="inv_ver_baja",
                            help=t("A written-off asset leaves the inventory but keeps its movement history and its QR code."))
    acts = INV.list_activos(grupo, incluir_baja=_ver_baja)
    _n_baja = len([a for a in INV.list_activos(grupo, incluir_baja=True)
                   if str(a.get("Activo", "SI")).upper() in ("NO", "FALSE", "0")])
    if _n_baja and not _ver_baja:
        st.caption(f":material/inventory_2: {_n_baja} written-off asset(s) hidden.")
    if not acts:
        st.caption(t("No assets yet. Register the first one with «Register asset»."))
        _categorias_expander(grupo)
        return

    f1, f2, f3 = st.columns([2, 1, 1])
    q = f1.text_input(t(":material/search: Search"), key="inv_q",
                      placeholder=t("name, serial, brand…")).strip().lower()
    # ⚠️ Las opciones son el DATO (categoría y estado guardados) y se comparan abajo;
    # solo se traduce el display: el «todas/todos» con `t()` y el resto con
    # `etiqueta()`, que es quien sabe traducir un valor de negocio (v442).
    cat_f = f2.selectbox(t("Category"), ["Todas"] + INV.categorias(grupo),
                         format_func=lambda o: t("All") if o == "Todas" else _etq(o),
                         key="inv_catf")
    est_f = f3.selectbox(t("Status"), ["Todos"] + INV.ESTADOS,
                         format_func=lambda o: t("All") if o == "Todos" else _etq(o),
                         key="inv_estf")
    _rows = acts
    if q:
        _rows = [a for a in _rows if q in " ".join(
            str(a.get(k, "")) for k in ("Nombre", "Serie", "Marca", "Modelo", "ID")).lower()]
    if cat_f != "Todas":
        _rows = [a for a in _rows if str(a.get("Categoria", "")) == cat_f]
    if est_f != "Todos":
        _rows = [a for a in _rows if str(a.get("Estado", "")) == est_f]
    _rows = sorted(_rows, key=lambda a: str(a.get("Nombre", "")).lower())

    st.caption(f"Tap an asset to see its record, its QR code and manage it. ({len(_rows)})")
    df = pd.DataFrame([{
        "Nombre":      a.get("Nombre", ""),
        "Category":   _etq(str(a.get("Categoria", ""))) or "—",
        "Estado":      _etq(str(a.get("Estado", ""))),
        "Location":   _ubic_txt(a),
        "Assigned to":  a.get("AsignadoA", "") or "—",
        "Valor":       round(INV.valor_actual(a), 0),
    } for a in _rows])
    _ev = st.dataframe(
        df, width="stretch", hide_index=True,
        on_select="rerun", selection_mode="single-row", key="inv_tbl",
        column_config=tabla.cfg(None, {"Valor": st.column_config.NumberColumn(t("Value"), format="$%,d")}))
    _sr = list(_ev.selection.rows)
    if _sr:
        st.session_state["_inv_open"] = str(_rows[_sr[0]].get("ID", ""))
        st.session_state.pop("inv_tbl", None)
        st.rerun()

    _reportes(grupo)
    _categorias_expander(grupo)


# ── Detalle de un activo ─────────────────────────────────────────
def _detalle(grupo, aid):
    if st.button(t(":material/arrow_back: Back to inventory"), key="inv_back"):
        st.session_state.pop("_inv_open", None)
        st.rerun()
    a = INV.get_activo(aid)
    if not a:
        st.warning(t("Asset not found."))
        st.session_state.pop("_inv_open", None)
        return
    # v351: entra por el QR (`?activo=`), que puede ser el de otra empresa.
    if not tenant.exigir(a, t("This asset")):
        st.session_state.pop("_inv_open", None)
        return

    st.markdown(f"## :material/inventory_2: {a.get('Nombre', '')}")
    st.markdown(f"**{a.get('ID', '')}**  ·  {_etq(str(a.get('Categoria', ''))) or '—'}  ·  "
                f"{_est_lbl(a.get('Estado', ''))}")

    izq, der = st.columns([3, 2])
    with izq:
        if a.get("FotoDriveID"):
            try:
                from core import drive_store
                st.image(drive_store.download(a.get("FotoDriveID")), width=220)
            except Exception:
                pass
        vc, va = _num(a.get("ValorCompra")), INV.valor_actual(a)
        m1, m2 = st.columns(2)
        m1.metric(t("Purchase value"), f"${vc:,.0f}")
        m2.metric(t("Current value"), f"${va:,.0f}",
                  help=t("Straight-line depreciation over the useful life."))
        st.markdown(f"**Location:** {_ubic_txt(a)}  ·  **Condition:** {_etq(str(a.get('Condicion', ''))) or '—'}")
        if str(a.get("AsignadoA", "")).strip():
            st.markdown(f"**{t('Assigned to')}:** {a.get('AsignadoA')}"
                        + (f" · {t('due back')} {a.get('FechaDevolucion')}" if a.get("FechaDevolucion") else ""))
        _pm = str(a.get("ProximoMant", "")).strip()
        if _pm:
            _pd = INV._parse_date(_pm)
            if _pd and _pd < clock.today():
                st.markdown(f":red[:material/build: {t('Maintenance OVERDUE')}: {_pm}]")
            else:
                st.markdown(f":material/build: Next service: {_pm}")
        if str(a.get("Nota", "")).strip():
            st.caption(a.get("Nota"))

    with der:
        st.markdown(t("#### :material/qr_code_2: QR code"))
        try:
            _png = INV.qr_png(aid)
            st.image(_png, width=170)
            if not INV.app_url():
                st.caption(t(":material/info: Set the APP_URL secret so the QR code opens the app."))
            try:
                from core import asset_label_pdf
                _pdf = asset_label_pdf.generate_label_pdf(a, _png, grupo)
                st.download_button(t(":material/download: Label (PDF)"), data=_pdf,
                                   file_name=f"Etiqueta_{aid}.pdf", mime="application/pdf",
                                   key=f"inv_lbl_{aid}")
            except Exception as e:
                st.caption(f"The label could not be generated: {e}")
        except Exception as e:
            st.caption(f"The QR code could not be generated: {e}")

    # ── Acciones (salida/entrada/traslado/mantenimiento) ──
    _est = str(a.get("Estado", "")).lower()
    _cp = _creado_por()
    if _est != "baja":
        st.markdown(t("#### :material/swap_horiz: Actions"))
        ac = st.columns(2)
        if _est == "disponible":
            with ac[0].expander(t(":material/logout: Check out / hand over")):
                _dt = st.selectbox(t("Destination"), ["proyecto", "usuario", "otro"],
                                   format_func=lambda o: t({"proyecto": "a project",
                                                            "usuario": "a person",
                                                            "otro": "somewhere else"}.get(o, o)),
                                   key=f"inv_sdt_{aid}")
                if _dt == "proyecto":
                    # El VALOR es el ID (identidad); la etiqueta es el nombre (comodidad).
                    _pids, _plbl = _proyectos(grupo)
                    _ref = st.selectbox(t("Project"), _pids or ["(no projects)"],
                                        key=f"inv_srp_{aid}",
                                        format_func=lambda i: _plbl.get(i, i))
                elif _dt == "usuario":
                    _ref = st.selectbox(t("User"), _usuarios(grupo) or ["(no users)"], key=f"inv_sru_{aid}")
                else:
                    _ref = st.text_input(t("Destination"), key=f"inv_srt_{aid}")
                _resp = st.selectbox(t("Person responsible"), ["—"] + _usuarios(grupo), key=f"inv_srsp_{aid}")
                _dev = _fecha_input(t("Expected return"), "", f"inv_sdev_{aid}")
                _n = st.text_input(t("Note"), key=f"inv_snota_{aid}")
                if st.button(t(":material/check: Record check-out"), type="primary", key=f"inv_sbtn_{aid}"):
                    _u = ("" if _resp == "—" else _resp) or (_ref if _dt == "usuario" else "")
                    ok, msg = INV.salida(aid, grupo, usuario=_u, hacia_tipo=_dt, hacia_ref=_ref,
                                         fecha_devolucion=_dev, nota=_n, creado_por=_cp)
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()
        else:
            with ac[0].expander(t(":material/login: Check in / return"), expanded=True):
                _bod = st.text_input(t("Store / return location"), value=t("Store"), key=f"inv_ebod_{aid}")
                _n = st.text_input(t("Note"), key=f"inv_enota_{aid}")
                if st.button(t(":material/check: Record check-in"), type="primary", key=f"inv_ebtn_{aid}"):
                    ok, msg = INV.entrada(aid, grupo, bodega=_bod, nota=_n, creado_por=_cp)
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()
        with ac[1].expander(t(":material/move_up: Transfer")):
            _tt = st.selectbox(t("New location (type)"), INV.UBIC_TIPOS, key=f"inv_ttt_{aid}")
            _tr = st.text_input(t("Detail"), key=f"inv_ttr_{aid}")
            _n = st.text_input(t("Note"), key=f"inv_tnota_{aid}")
            if st.button(t(":material/check: Transfer"), key=f"inv_tbtn_{aid}"):
                ok, msg = INV.traslado(aid, grupo, _tt, _tr, nota=_n, creado_por=_cp)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
        with ac[1].expander(t(":material/build: Service")):
            _costo = st.number_input(t("Cost"), min_value=0.0, step=10.0, key=f"inv_mcosto_{aid}")
            _prox = _fecha_input(t("Next maintenance"), a.get("ProximoMant"), f"inv_mprox_{aid}")
            _enm = st.checkbox(t("Leave the asset IN service"), key=f"inv_menm_{aid}")
            _n = st.text_input(t("Note"), key=f"inv_mnota_{aid}")
            if st.button(t(":material/check: Record service"), key=f"inv_mbtn_{aid}"):
                ok, msg = INV.mantenimiento(aid, grupo, costo=_costo, proximo=_prox, nota=_n,
                                            en_mant=_enm, creado_por=_cp)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()

    # ── Historial ──
    st.markdown(t("#### :material/history: History"))
    movs = INV.list_movimientos(grupo, aid)
    if not movs:
        st.caption(t("No movements yet."))
    else:
        _mr = sorted(movs, key=lambda m: str(m.get("Creado", "")), reverse=True)
        st.dataframe(pd.DataFrame([{
            "Fecha":   m.get("Fecha", ""),
            "Tipo":    _etq(str(m.get("Tipo", ""))),
            "Desde":   INV.ubic_texto(m.get("DesdeUbic", ""), _etq) or "—",
            "Hacia":   INV.ubic_texto(m.get("HaciaUbic", ""), _etq) or "—",
            "Usuario": m.get("Usuario", "") or "—",
            # ⚠️ NaN y no None: si TODA la columna es None, pandas la deja en
            # `object` y Streamlit pinta el literal «None»; con NaN es float y
            # sale vacia (medido, no supuesto).
            "Costo":   (round(_num(m.get("Costo")), 0) if str(m.get("Costo", "")).strip()
                        else float("nan")),
            "Nota":    m.get("Nota", "") or "",
        } for m in _mr]), width="stretch", hide_index=True,
            column_config=tabla.cfg(None, {"Costo": st.column_config.NumberColumn(t("Cost"), format="$%,d")}))

    # Editar
    st.markdown(t("#### :material/edit: Edit asset"))
    with st.form(f"inv_edit_{aid}"):
        e1, e2 = st.columns(2)
        nombre = e1.text_input(t("Name"), value=a.get("Nombre", ""))
        cats = INV.categorias(grupo)
        _ci = cats.index(a.get("Categoria")) if a.get("Categoria") in cats else 0
        categoria = e2.selectbox(t("Category"), cats, index=_ci)
        marca = e1.text_input(t("Brand"), value=a.get("Marca", ""))
        modelo = e2.text_input(t("Model"), value=a.get("Modelo", ""))
        serie = e1.text_input(t("Serial no."), value=a.get("Serie", ""))
        _ei = INV.ESTADOS.index(a.get("Estado")) if a.get("Estado") in INV.ESTADOS else 0
        estado = e2.selectbox(t("Status"), INV.ESTADOS, index=_ei)
        _cdi = INV.CONDICIONES.index(a.get("Condicion")) if a.get("Condicion") in INV.CONDICIONES else 0
        condicion = e1.selectbox(t("Condition"), INV.CONDICIONES, index=_cdi)
        _ui = INV.UBIC_TIPOS.index(a.get("UbicacionTipo")) if a.get("UbicacionTipo") in INV.UBIC_TIPOS else 0
        ubic_t = e2.selectbox(t("Location (type)"), INV.UBIC_TIPOS, index=_ui)
        ubic_r = e1.text_input(t("Location (detail)"), value=a.get("UbicacionRef", ""),
                               help=t("Store or person holding it. If the asset is on a site, this holds the project ID (PRJ-####) — it is set automatically when the check-out is recorded; the list shows the name."))
        if str(a.get("UbicacionRef", "")).startswith("PRJ-"):
            e1.caption(f":material/folder: {INV.ubic_ref_label(a.get('UbicacionRef'))}")
        vc = e2.number_input(t("Purchase value"), min_value=0.0, step=10.0,
                             value=_num(a.get("ValorCompra")))
        c3, c4 = st.columns(2)
        f_compra = _fecha_input("Purchase date", a.get("FechaCompra"), f"inv_fc_{aid}")
        vida = c4.number_input(t("Useful life (years)"), min_value=0.0, step=1.0,
                               value=_num(a.get("VidaUtilAnios")))
        prox = _fecha_input(t("Next maintenance"), a.get("ProximoMant"), f"inv_pm_{aid}")
        nota = st.text_area(t("Note"), value=a.get("Nota", ""), height=80)
        if st.form_submit_button(t(":material/save: Save changes"), type="primary"):
            ok, msg = INV.update_activo(aid, {
                "Nombre": nombre, "Categoria": categoria, "Marca": marca, "Modelo": modelo,
                "Serie": serie, "Estado": estado, "Condicion": condicion,
                "UbicacionTipo": ubic_t, "UbicacionRef": ubic_r, "ValorCompra": vc,
                "FechaCompra": f_compra, "VidaUtilAnios": vida, "ProximoMant": prox, "Nota": nota})
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()

    if str(a.get("Estado", "")).lower() != "baja":
        with st.expander(t(":material/block: Write off")):
            st.caption(t("Takes the asset out of the inventory (it stays in the history). To see it again, tick «Show written-off ones too»."))
            _mot = st.text_input(t("Reason"), key=f"inv_baja_mot_{aid}")
            if st.button(t("Write off this asset"), key=f"inv_baja_{aid}"):
                INV.dar_de_baja(aid, grupo, _mot, _creado_por())
                st.session_state.pop("_inv_open", None)
                st.rerun()
    else:
        # v340: la vuelta. Antes un activo de baja no se podía reactivar desde la app.
        st.warning(t(":material/block: This asset is **written off**: it does not appear in the inventory unless you tick «Show written-off ones too»."))
        if st.button(t(":material/restore: Reactivate this asset"),
                     key=f"inv_react_{aid}", type="primary"):
            ok, msg = INV.update_activo(aid, {"Activo": "SI", "Estado": "disponible"})
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()


# ── Registro de un activo ────────────────────────────────────────
def _registro(grupo):
    if st.button(t(":material/arrow_back: Cancel"), key="inv_new_back"):
        st.session_state.pop("_inv_nuevo", None)
        st.rerun()
    st.markdown(t("## :material/add_circle: Register asset"))

    # Foto fuera del form (uploader se procesa al enviar)
    _foto = st.file_uploader(t("Photo (optional)"), type=["png", "jpg", "jpeg"], key="inv_foto")

    with st.form("inv_reg"):
        c1, c2 = st.columns(2)
        nombre = c1.text_input(t("Asset name *"))
        categoria = c2.selectbox(t("Category"), INV.categorias(grupo))
        marca = c1.text_input(t("Brand"))
        modelo = c2.text_input(t("Model"))
        serie = c1.text_input(t("Serial no."))
        condicion = c2.selectbox(t("Condition"), INV.CONDICIONES)
        ubic_t = c1.selectbox(t("Location (type)"), INV.UBIC_TIPOS)
        ubic_r = c2.text_input(t("Location (detail)"), help=t("Store, project or user."))
        vc = c1.number_input(t("Purchase value"), min_value=0.0, step=10.0)
        vida = c2.number_input(t("Useful life (years)"), min_value=0.0, step=1.0,
                               help=t("Used for depreciation. 0 = do not depreciate."))
        f_compra = _fecha_input("Purchase date", "", "inv_reg_fc")
        prox = _fecha_input(t("Next maintenance"), "", "inv_reg_pm")
        nota = st.text_area(t("Note"), height=70)
        crear = st.form_submit_button(t(":material/add: Register"), type="primary")

    if crear:
        if not str(nombre).strip():
            st.error(t("The name is required."))
            return
        foto_id = ""
        if _foto is not None:
            try:
                from core import drive_store
                if drive_store.is_available():
                    foto_id = drive_store.upload_to(drive_store.folder("COPEX Assets"),
                                                    _foto.name, _foto.getvalue(),
                                                    _foto.type or "image/jpeg")
            except Exception as e:
                # ⚠️ v323: era un `pass` mudo. El activo se creaba igual (correcto,
                # la foto es accesoria) pero el usuario ADJUNTÓ una foto y se le
                # decía que todo fue bien: creía tenerla guardada y no estaba.
                logger.warning("inventory_ui: la foto del activo no subió a Drive: %s", e)
                st.warning(t(":material/warning: The asset is registered, but **the photo could not be uploaded** to Drive. Add it later from its record."))
        ok, res = INV.create_activo(
            grupo=grupo, nombre=nombre, categoria=categoria, marca=marca, modelo=modelo,
            serie=serie, foto_id=foto_id, fecha_compra=f_compra, valor_compra=vc,
            vida_util=vida, condicion=condicion, ubicacion_tipo=ubic_t, ubicacion_ref=ubic_r,
            proximo_mant=prox, nota=nota, creado_por=_creado_por())
        if ok:
            st.session_state.pop("_inv_nuevo", None)
            st.session_state["_inv_open"] = res
            st.rerun()
        else:
            st.error(res)


# ── Categorías (catálogo editable) ───────────────────────────────
def _reportes(grupo):
    rep = INV.reporte_valor(grupo)
    if not rep["por_categoria"]:
        return
    with st.expander(t(":material/insights: Value reports")):
        ca, cb = st.columns(2)
        with ca:
            st.markdown(t("**By category**"))
            st.dataframe(pd.DataFrame([{
                "Category": k, "Active": v["n"],
                "Compra": round(v["compra"], 0), "Actual": round(v["actual"], 0),
            } for k, v in sorted(rep["por_categoria"].items())]),
                width="stretch", hide_index=True,
                column_config=tabla.cfg(None, {"Compra": st.column_config.NumberColumn(t("Purchase"), format="$%,d"),
                               "Actual": st.column_config.NumberColumn(t("Current"), format="$%,d")}))
        with cb:
            st.markdown(t("**By location**"))
            st.dataframe(pd.DataFrame([{
                "Location": k, "Active": v["n"], "Valor actual": round(v["actual"], 0),
            } for k, v in sorted(rep["por_ubicacion"].items())]),
                width="stretch", hide_index=True,
                column_config=tabla.cfg(None, {"Valor actual": st.column_config.NumberColumn(t("Current value"), format="$%,d")}))


def _categorias_expander(grupo):
    with st.expander(t(":material/category: Categories")):
        st.caption(t("The default ones are always there; here you add/remove your own."))
        st.write(" · ".join(INV.categorias(grupo)))
        cc = st.columns([3, 1])
        _nueva = cc[0].text_input(t("New category"), key="inv_cat_new",
                                  label_visibility="collapsed", placeholder=t("New category…"))
        if cc[1].button(t(":material/add: Add"), key="inv_cat_add"):
            ok, msg = INV.add_categoria(grupo, _nueva)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()
        _quitar = st.selectbox(t("Remove one of your categories"), ["—"] + INV.categorias(grupo),
                               key="inv_cat_del")
        if _quitar != "—" and st.button(t(":material/delete: Remove"), key="inv_cat_delbtn"):
            ok, msg = INV.del_categoria(grupo, _quitar)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()
