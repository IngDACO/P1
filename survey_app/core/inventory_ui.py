"""📦 Inventario — UI de control de activos (v263, Fase 1).

KPIs + lista filtrable → ficha (foto, QR + etiqueta PDF, datos, valor depreciado,
edición, baja) + registro + catálogo de categorías. Solo admin/propietario.
Movimientos (entradas/salidas) y el escaneo que abre la ficha llegan en la Fase 2.
"""
import logging
import pandas as pd
import streamlit as st

from core import clock
from core import inventory as INV
from core.num import num as _num

logger = logging.getLogger(__name__)


def _creado_por() -> str:
    a = st.session_state.get("auth") or {}
    return str(a.get("usuario", "") or a.get("nombre", ""))


_EST_LBL = {"disponible": ":green[disponible]", "en_uso": ":blue[en uso]",
            "mantenimiento": ":orange[mantenimiento]", "dañado": ":red[dañado]",
            "baja": ":gray[baja]"}


def _ubic_txt(a) -> str:
    """Ubicación legible. ⚠️ Delega en `INV.ubic_str` (v306): esta función era una COPIA
    de la del backend, así que al hacer que el proyecto se guarde por ID solo se habría
    arreglado una de las dos y la lista seguiría enseñando `PRJ-0007` (el patrón de dos
    mecanismos para lo mismo que v140 mandó no repetir)."""
    return INV.ubic_str(a)


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
        _ps = [p for p in P.list_projects(grupo=grupo) if str(p.get("ID", "")).strip()]
        _lbl = P.etiqueta_proyectos(_ps)
        return [str(p.get("ID", "")) for p in _ps], _lbl
    except Exception:
        return [], {}


# ── Vista principal ──────────────────────────────────────────────
def render_inventario(grupo):
    st.markdown("## :material/inventory_2: Inventario de activos")
    if not INV.is_configured():
        st.info(":material/info: Configura Google Sheets para el inventario.")
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
    c[0].metric("Activos", r["n"])
    c[1].metric("Disponibles", est.get("disponible", 0))
    c[2].metric("En uso", est.get("en_uso", 0))
    c[3].metric("Valor actual", f"${r['valor_actual']:,.0f}",
                help=f"Valor de compra: ${r['valor_compra']:,.0f} (depreciado línea recta)")
    c[4].metric("Mant. vencido", r["mant_vencido"])

    if st.button(":material/add_circle: Registrar activo", type="primary", key="inv_new"):
        st.session_state["_inv_nuevo"] = True
        st.rerun()

    acts = INV.list_activos(grupo)
    if not acts:
        st.caption("Aún no hay activos. Registra el primero con «Registrar activo».")
        _categorias_expander(grupo)
        return

    f1, f2, f3 = st.columns([2, 1, 1])
    q = f1.text_input(":material/search: Buscar", key="inv_q",
                      placeholder="nombre, serie, marca…").strip().lower()
    cat_f = f2.selectbox("Categoría", ["Todas"] + INV.categorias(grupo), key="inv_catf")
    est_f = f3.selectbox("Estado", ["Todos"] + INV.ESTADOS, key="inv_estf")
    _rows = acts
    if q:
        _rows = [a for a in _rows if q in " ".join(
            str(a.get(k, "")) for k in ("Nombre", "Serie", "Marca", "Modelo", "ID")).lower()]
    if cat_f != "Todas":
        _rows = [a for a in _rows if str(a.get("Categoria", "")) == cat_f]
    if est_f != "Todos":
        _rows = [a for a in _rows if str(a.get("Estado", "")) == est_f]
    _rows = sorted(_rows, key=lambda a: str(a.get("Nombre", "")).lower())

    st.caption(f"Toca un activo para ver su ficha, su QR y gestionarlo. ({len(_rows)})")
    df = pd.DataFrame([{
        "Nombre":      a.get("Nombre", ""),
        "Categoría":   a.get("Categoria", "") or "—",
        "Estado":      a.get("Estado", ""),
        "Ubicación":   _ubic_txt(a),
        "Asignado a":  a.get("AsignadoA", "") or "—",
        "Valor":       round(INV.valor_actual(a), 0),
    } for a in _rows])
    _ev = st.dataframe(
        df, use_container_width=True, hide_index=True,
        on_select="rerun", selection_mode="single-row", key="inv_tbl",
        column_config={"Valor": st.column_config.NumberColumn("Valor", format="$%d")})
    _sr = list(_ev.selection.rows)
    if _sr:
        st.session_state["_inv_open"] = str(_rows[_sr[0]].get("ID", ""))
        st.session_state.pop("inv_tbl", None)
        st.rerun()

    _reportes(grupo)
    _categorias_expander(grupo)


# ── Detalle de un activo ─────────────────────────────────────────
def _detalle(grupo, aid):
    if st.button(":material/arrow_back: Volver al inventario", key="inv_back"):
        st.session_state.pop("_inv_open", None)
        st.rerun()
    a = INV.get_activo(aid)
    if not a:
        st.warning("Activo no encontrado.")
        st.session_state.pop("_inv_open", None)
        return

    st.markdown(f"## :material/inventory_2: {a.get('Nombre', '')}")
    st.markdown(f"**{a.get('ID', '')}**  ·  {a.get('Categoria', '') or '—'}  ·  "
                f"{_EST_LBL.get(a.get('Estado', ''), a.get('Estado', ''))}")

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
        m1.metric("Valor de compra", f"${vc:,.0f}")
        m2.metric("Valor actual", f"${va:,.0f}",
                  help="Depreciación línea recta según vida útil.")
        st.markdown(f"**Ubicación:** {_ubic_txt(a)}  ·  **Condición:** {a.get('Condicion', '') or '—'}")
        if str(a.get("AsignadoA", "")).strip():
            st.markdown(f"**Asignado a:** {a.get('AsignadoA')}"
                        + (f" · devolución {a.get('FechaDevolucion')}" if a.get("FechaDevolucion") else ""))
        _pm = str(a.get("ProximoMant", "")).strip()
        if _pm:
            _pd = INV._parse_date(_pm)
            if _pd and _pd < clock.today():
                st.markdown(f":red[:material/build: Mantenimiento VENCIDO: {_pm}]")
            else:
                st.markdown(f":material/build: Próximo mantenimiento: {_pm}")
        if str(a.get("Nota", "")).strip():
            st.caption(a.get("Nota"))

    with der:
        st.markdown("#### :material/qr_code_2: QR")
        try:
            _png = INV.qr_png(aid)
            st.image(_png, width=170)
            if not INV.app_url():
                st.caption(":material/info: Configura el secret APP_URL para que el QR abra la app.")
            try:
                from core import asset_label_pdf
                _pdf = asset_label_pdf.generate_label_pdf(a, _png, grupo)
                st.download_button(":material/download: Etiqueta (PDF)", data=_pdf,
                                   file_name=f"Etiqueta_{aid}.pdf", mime="application/pdf",
                                   key=f"inv_lbl_{aid}")
            except Exception as e:
                st.caption(f"No se pudo generar la etiqueta: {e}")
        except Exception as e:
            st.caption(f"No se pudo generar el QR: {e}")

    # ── Acciones (salida/entrada/traslado/mantenimiento) ──
    _est = str(a.get("Estado", "")).lower()
    _cp = _creado_por()
    if _est != "baja":
        st.markdown("#### :material/swap_horiz: Acciones")
        ac = st.columns(2)
        if _est == "disponible":
            with ac[0].expander(":material/logout: Salida / entregar"):
                _dt = st.selectbox("Destino", ["proyecto", "usuario", "otro"], key=f"inv_sdt_{aid}")
                if _dt == "proyecto":
                    # El VALOR es el ID (identidad); la etiqueta es el nombre (comodidad).
                    _pids, _plbl = _proyectos(grupo)
                    _ref = st.selectbox("Proyecto", _pids or ["(sin proyectos)"],
                                        key=f"inv_srp_{aid}",
                                        format_func=lambda i: _plbl.get(i, i))
                elif _dt == "usuario":
                    _ref = st.selectbox("Usuario", _usuarios(grupo) or ["(sin usuarios)"], key=f"inv_sru_{aid}")
                else:
                    _ref = st.text_input("Destino", key=f"inv_srt_{aid}")
                _resp = st.selectbox("Responsable", ["—"] + _usuarios(grupo), key=f"inv_srsp_{aid}")
                _dev = _fecha_input("Devolución esperada", "", f"inv_sdev_{aid}")
                _n = st.text_input("Nota", key=f"inv_snota_{aid}")
                if st.button(":material/check: Registrar salida", type="primary", key=f"inv_sbtn_{aid}"):
                    _u = ("" if _resp == "—" else _resp) or (_ref if _dt == "usuario" else "")
                    ok, msg = INV.salida(aid, grupo, usuario=_u, hacia_tipo=_dt, hacia_ref=_ref,
                                         fecha_devolucion=_dev, nota=_n, creado_por=_cp)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()
        else:
            with ac[0].expander(":material/login: Entrada / devolver", expanded=True):
                _bod = st.text_input("Bodega / ubicación de retorno", value="Bodega", key=f"inv_ebod_{aid}")
                _n = st.text_input("Nota", key=f"inv_enota_{aid}")
                if st.button(":material/check: Registrar entrada", type="primary", key=f"inv_ebtn_{aid}"):
                    ok, msg = INV.entrada(aid, grupo, bodega=_bod, nota=_n, creado_por=_cp)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()
        with ac[1].expander(":material/move_up: Traslado"):
            _tt = st.selectbox("Nueva ubicación (tipo)", INV.UBIC_TIPOS, key=f"inv_ttt_{aid}")
            _tr = st.text_input("Detalle", key=f"inv_ttr_{aid}")
            _n = st.text_input("Nota", key=f"inv_tnota_{aid}")
            if st.button(":material/check: Trasladar", key=f"inv_tbtn_{aid}"):
                ok, msg = INV.traslado(aid, grupo, _tt, _tr, nota=_n, creado_por=_cp)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()
        with ac[1].expander(":material/build: Mantenimiento"):
            _costo = st.number_input("Costo", min_value=0.0, step=10.0, key=f"inv_mcosto_{aid}")
            _prox = _fecha_input("Próximo mantenimiento", a.get("ProximoMant"), f"inv_mprox_{aid}")
            _enm = st.checkbox("Dejar el activo EN mantenimiento", key=f"inv_menm_{aid}")
            _n = st.text_input("Nota", key=f"inv_mnota_{aid}")
            if st.button(":material/check: Registrar mantenimiento", key=f"inv_mbtn_{aid}"):
                ok, msg = INV.mantenimiento(aid, grupo, costo=_costo, proximo=_prox, nota=_n,
                                            en_mant=_enm, creado_por=_cp)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()

    # ── Historial ──
    st.markdown("#### :material/history: Historial")
    movs = INV.list_movimientos(grupo, aid)
    if not movs:
        st.caption("Sin movimientos todavía.")
    else:
        _mr = sorted(movs, key=lambda m: str(m.get("Creado", "")), reverse=True)
        st.dataframe(pd.DataFrame([{
            "Fecha":   m.get("Fecha", ""),
            "Tipo":    m.get("Tipo", ""),
            "Desde":   m.get("DesdeUbic", "") or "—",
            "Hacia":   m.get("HaciaUbic", "") or "—",
            "Usuario": m.get("Usuario", "") or "—",
            "Costo":   (round(_num(m.get("Costo")), 0) if str(m.get("Costo", "")).strip() else None),
            "Nota":    m.get("Nota", "") or "",
        } for m in _mr]), use_container_width=True, hide_index=True,
            column_config={"Costo": st.column_config.NumberColumn("Costo", format="$%d")})

    # Editar
    st.markdown("#### :material/edit: Editar activo")
    with st.form(f"inv_edit_{aid}"):
        e1, e2 = st.columns(2)
        nombre = e1.text_input("Nombre", value=a.get("Nombre", ""))
        cats = INV.categorias(grupo)
        _ci = cats.index(a.get("Categoria")) if a.get("Categoria") in cats else 0
        categoria = e2.selectbox("Categoría", cats, index=_ci)
        marca = e1.text_input("Marca", value=a.get("Marca", ""))
        modelo = e2.text_input("Modelo", value=a.get("Modelo", ""))
        serie = e1.text_input("Nº de serie", value=a.get("Serie", ""))
        _ei = INV.ESTADOS.index(a.get("Estado")) if a.get("Estado") in INV.ESTADOS else 0
        estado = e2.selectbox("Estado", INV.ESTADOS, index=_ei)
        _cdi = INV.CONDICIONES.index(a.get("Condicion")) if a.get("Condicion") in INV.CONDICIONES else 0
        condicion = e1.selectbox("Condición", INV.CONDICIONES, index=_cdi)
        _ui = INV.UBIC_TIPOS.index(a.get("UbicacionTipo")) if a.get("UbicacionTipo") in INV.UBIC_TIPOS else 0
        ubic_t = e2.selectbox("Ubicación (tipo)", INV.UBIC_TIPOS, index=_ui)
        ubic_r = e1.text_input("Ubicación (detalle)", value=a.get("UbicacionRef", ""),
                               help="Bodega o usuario que lo tiene. Si el activo está en "
                                    "una obra, aquí va el ID del proyecto (PRJ-####) — se "
                                    "pone solo al registrar la salida; la lista muestra el "
                                    "nombre.")
        if str(a.get("UbicacionRef", "")).startswith("PRJ-"):
            e1.caption(f":material/folder: {INV.ubic_ref_label(a.get('UbicacionRef'))}")
        vc = e2.number_input("Valor de compra", min_value=0.0, step=10.0,
                             value=_num(a.get("ValorCompra")))
        c3, c4 = st.columns(2)
        f_compra = _fecha_input("Fecha de compra", a.get("FechaCompra"), f"inv_fc_{aid}")
        vida = c4.number_input("Vida útil (años)", min_value=0.0, step=1.0,
                               value=_num(a.get("VidaUtilAnios")))
        prox = _fecha_input("Próximo mantenimiento", a.get("ProximoMant"), f"inv_pm_{aid}")
        nota = st.text_area("Nota", value=a.get("Nota", ""), height=80)
        if st.form_submit_button(":material/save: Guardar cambios", type="primary"):
            ok, msg = INV.update_activo(aid, {
                "Nombre": nombre, "Categoria": categoria, "Marca": marca, "Modelo": modelo,
                "Serie": serie, "Estado": estado, "Condicion": condicion,
                "UbicacionTipo": ubic_t, "UbicacionRef": ubic_r, "ValorCompra": vc,
                "FechaCompra": f_compra, "VidaUtilAnios": vida, "ProximoMant": prox, "Nota": nota})
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()

    if str(a.get("Estado", "")).lower() != "baja":
        with st.expander(":material/block: Dar de baja"):
            st.caption("Retira el activo del inventario (queda en el histórico).")
            _mot = st.text_input("Motivo", key=f"inv_baja_mot_{aid}")
            if st.button("Dar de baja este activo", key=f"inv_baja_{aid}"):
                INV.dar_de_baja(aid, grupo, _mot, _creado_por())
                st.session_state.pop("_inv_open", None)
                st.rerun()


# ── Registro de un activo ────────────────────────────────────────
def _registro(grupo):
    if st.button(":material/arrow_back: Cancelar", key="inv_new_back"):
        st.session_state.pop("_inv_nuevo", None)
        st.rerun()
    st.markdown("## :material/add_circle: Registrar activo")

    # Foto fuera del form (uploader se procesa al enviar)
    _foto = st.file_uploader("Foto (opcional)", type=["png", "jpg", "jpeg"], key="inv_foto")

    with st.form("inv_reg"):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre del activo *")
        categoria = c2.selectbox("Categoría", INV.categorias(grupo))
        marca = c1.text_input("Marca")
        modelo = c2.text_input("Modelo")
        serie = c1.text_input("Nº de serie")
        condicion = c2.selectbox("Condición", INV.CONDICIONES)
        ubic_t = c1.selectbox("Ubicación (tipo)", INV.UBIC_TIPOS)
        ubic_r = c2.text_input("Ubicación (detalle)", help="Bodega, proyecto o usuario.")
        vc = c1.number_input("Valor de compra", min_value=0.0, step=10.0)
        vida = c2.number_input("Vida útil (años)", min_value=0.0, step=1.0,
                               help="Para la depreciación. 0 = no depreciar.")
        f_compra = _fecha_input("Fecha de compra", "", "inv_reg_fc")
        prox = _fecha_input("Próximo mantenimiento", "", "inv_reg_pm")
        nota = st.text_area("Nota", height=70)
        crear = st.form_submit_button(":material/add: Registrar", type="primary")

    if crear:
        if not str(nombre).strip():
            st.error("El nombre es obligatorio.")
            return
        foto_id = ""
        if _foto is not None:
            try:
                from core import drive_store
                if drive_store.is_available():
                    foto_id = drive_store.upload_to(drive_store.folder("COPEX Activos"),
                                                    _foto.name, _foto.getvalue(),
                                                    _foto.type or "image/jpeg")
            except Exception as e:
                # ⚠️ v323: era un `pass` mudo. El activo se creaba igual (correcto,
                # la foto es accesoria) pero el usuario ADJUNTÓ una foto y se le
                # decía que todo fue bien: creía tenerla guardada y no estaba.
                logger.warning("inventory_ui: la foto del activo no subió a Drive: %s", e)
                st.warning(":material/warning: El activo se registra, pero **la foto no "
                           "se pudo subir** a Drive. Añádela luego desde su ficha.")
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
    with st.expander(":material/insights: Reportes de valor"):
        ca, cb = st.columns(2)
        with ca:
            st.markdown("**Por categoría**")
            st.dataframe(pd.DataFrame([{
                "Categoría": k, "Activos": v["n"],
                "Compra": round(v["compra"], 0), "Actual": round(v["actual"], 0),
            } for k, v in sorted(rep["por_categoria"].items())]),
                use_container_width=True, hide_index=True,
                column_config={"Compra": st.column_config.NumberColumn("Compra", format="$%d"),
                               "Actual": st.column_config.NumberColumn("Actual", format="$%d")})
        with cb:
            st.markdown("**Por ubicación**")
            st.dataframe(pd.DataFrame([{
                "Ubicación": k, "Activos": v["n"], "Valor actual": round(v["actual"], 0),
            } for k, v in sorted(rep["por_ubicacion"].items())]),
                use_container_width=True, hide_index=True,
                column_config={"Valor actual": st.column_config.NumberColumn("Valor actual", format="$%d")})


def _categorias_expander(grupo):
    with st.expander(":material/category: Categorías"):
        st.caption("Las de por defecto siempre están; aquí añades/quitas las tuyas.")
        st.write(" · ".join(INV.categorias(grupo)))
        cc = st.columns([3, 1])
        _nueva = cc[0].text_input("Nueva categoría", key="inv_cat_new",
                                  label_visibility="collapsed", placeholder="Nueva categoría…")
        if cc[1].button(":material/add: Añadir", key="inv_cat_add"):
            ok, msg = INV.add_categoria(grupo, _nueva)
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()
        _quitar = st.selectbox("Quitar una categoría propia", ["—"] + INV.categorias(grupo),
                               key="inv_cat_del")
        if _quitar != "—" and st.button(":material/delete: Quitar", key="inv_cat_delbtn"):
            ok, msg = INV.del_categoria(grupo, _quitar)
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()
