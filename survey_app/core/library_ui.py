"""📚 Technical library — fotos, manuales y fichas por MARCA · MODELO · SECCIÓN (v472).

Pantalla de CONSULTA para todos y de GESTIÓN para el propietario (decisión del
usuario: «solo el propietario sube»). Es una sección SIN sub-pestañas, así que su
título va aquí — `_sub_header` solo lo pinta cuando la sección tiene subs (v320).

⚠️ La descarga es LAZY, y no es un detalle de rendimiento: `st.download_button`
evalúa `data=` **al RENDERIZAR**, no al pulsar, así que un botón por ficha se bajaría
de Drive TODO el material en cada pasada. Es el fallo que costó v147, y aquí sería
peor: una biblioteca crece sin techo. Se elige la ficha y solo entonces se baja ESA.
Por lo mismo la galería va PAGINADA: cada miniatura ES una descarga.
"""
import pandas as pd
import streamlit as st

from core import flash
from core import library as LIB
from core import tabla
from core import theme as T
from core.i18n import t, etiqueta as _etq

_POR_PAGINA = 6          # ⚠️ cada miniatura es una descarga de Drive (v147)


def _rol() -> str:
    try:
        return str(st.session_state.get("auth", {}).get("rol", "")).strip().lower()
    except Exception:
        return ""


def _usuario() -> str:
    a = st.session_state.get("auth") or {}
    return str(a.get("usuario", "") or a.get("nombre", ""))


def _puede_subir() -> bool:
    """Solo el propietario alimenta la biblioteca (decisión del usuario: control de
    calidad del material). Todos los demás CONSULTAN."""
    return _rol() == "owner"


def _drive():
    """El módulo de Drive, o None si no está conectado. ⚠️ Import perezoso y
    tolerante: sin Drive la biblioteca tiene que seguir LISTANDO su catálogo — solo
    se queda sin previsualizar y sin descargar (el criterio de v383 con la firma)."""
    try:
        from core import drive_store
        return drive_store if drive_store.is_available() else None
    except Exception:
        return None


# ── la pantalla ──────────────────────────────────────────────────────────────
def render_biblioteca(grupo=None):
    """⚠️ `grupo` se acepta y se IGNORA: la shell despacha todas las secciones con la
    misma firma, y la biblioteca es GLOBAL (una sola para toda la instalación)."""
    st.markdown("## " + t(":material/menu_book: Technical library"))
    if not LIB.is_configured():
        st.info(t(":material/info: Configure Google Sheets to use the library."))
        return

    if st.session_state.get("_lib_open"):
        _detalle(st.session_state["_lib_open"])
        return

    r = LIB.resumen()
    T.kpi_row([
        (t("Items"), str(r["total"]), t("photos, manuals and datasheets")),
        (t("Brands"), str(r["marcas"]), t("in the catalogue")),
        (t("Models"), str(r["modelos"]), t("filed in the catalogue")),
        (t("Sections"), str(len(r["por_seccion"])), t("of the lift covered")),
    ])

    _q, _marca, _modelo, _seccion, _tipo = _barra()
    items = LIB.buscar(_q, marca=_marca, modelo=_modelo, seccion=_seccion, tipo=_tipo)

    if not items:
        _vacio(r)
    else:
        st.caption(t("{n} item(s). Tap one to open it.", n=len(items)))
        _fotos = [i for i in items if str(i.get("Type", "")) == "photo"]
        _resto = [i for i in items if str(i.get("Type", "")) != "photo"]
        if _fotos:
            _galeria(_fotos)
        if _resto:
            _tabla(_resto)

    if _puede_subir():
        st.markdown("---")
        _alta()
        _catalogo()
    else:
        st.caption(t("Only the owner adds material to the library. Ask them to file "
                     "anything worth keeping."))


def _barra():
    """Buscador + la taxonomía. ⚠️ Los desplegables se ENCADENAN: los modelos salen
    de la marca elegida, así que no se puede pedir un par que no existe."""
    c1, c2 = st.columns([3, 2])
    q = c1.text_input(t("Search"), key="lib_q", label_visibility="collapsed",
                      placeholder=t("title, notes, brand, model, file name…"))
    tipo = c2.selectbox(t("Type"), [""] + list(LIB.TIPOS), key="lib_tipo",
                        label_visibility="collapsed",
                        format_func=lambda x: t("All types") if not x else t(x))

    c3, c4, c5 = st.columns(3)
    _marcas = LIB.marcas()
    marca = c3.selectbox(t("Brand"), [""] + _marcas, key="lib_marca",
                         format_func=lambda x: t(LIB.SIN_MARCA) if not x else x)
    # ⚠️ Sin marca no se ofrecen modelos: un modelo suelto no identifica nada (hay
    # códigos que se repiten entre fabricantes) y la lista sería inmanejable.
    _modelos = LIB.modelos_de(marca) if marca else []
    modelo = c4.selectbox(t("Model"), [""] + _modelos, key="lib_modelo",
                          disabled=not marca,
                          format_func=lambda x: t(LIB.SIN_MODELO) if not x else x,
                          help=None if marca else t("Pick a brand first."))
    seccion = c5.selectbox(t("Section"), [""] + list(LIB.SECCIONES), key="lib_seccion",
                           format_func=lambda x: t("All sections") if not x else t(x))
    return q, marca, (modelo if marca else ""), seccion, tipo


def _vacio(r):
    """⚠️ Un «no hay resultados» tiene DOS causas y confundirlas manda a buscar donde
    no hay nada: la biblioteca puede estar vacía, o los filtros pueden estar de más."""
    if r["total"] == 0:
        st.info(t(":material/info: The library is empty. The owner files the first "
                  "material from this screen."))
    else:
        st.warning(t(":material/search_off: Nothing matches those filters. "
                     "The library has {n} item(s) in total.", n=r["total"]))


def _etiqueta(it) -> str:
    _m = " · ".join(x for x in (str(it.get("Brand", "")).strip(),
                                str(it.get("Model", "")).strip()) if x)
    return _m or t("no brand")


def _galeria(fotos):
    """Fotos en rejilla. ⚠️ PAGINADA a propósito (v147): cada miniatura baja los bytes
    de Drive, así que pintarlas todas reintroduce el problema que la lazyness evita."""
    T.section(t(":material/photo_library: Photos"), t("{n} photo(s)", n=len(fotos)))
    dr = _drive()
    if dr is None:
        st.caption(t("Drive is not connected: the photos are listed but cannot be shown."))
    _pag = int(st.session_state.get("_lib_pag", 0))
    _tot = max(1, (len(fotos) + _POR_PAGINA - 1) // _POR_PAGINA)
    _pag = max(0, min(_pag, _tot - 1))
    _vis = fotos[_pag * _POR_PAGINA:(_pag + 1) * _POR_PAGINA]

    for _f in range(0, len(_vis), 3):
        cols = st.columns(3)
        for _c, it in zip(cols, _vis[_f:_f + 3]):
            _did = str(it.get("DriveID", "")).strip()
            if dr is not None and _did:
                try:
                    _c.image(dr.download(_did), width="stretch")
                except Exception:
                    _c.caption(t(":material/broken_image: could not be loaded"))
            _c.caption("**%s**" % it.get("Title", ""))
            _c.caption("%s · %s" % (_etiqueta(it), t(str(it.get("Section", "")))))
            if _c.button(t(":material/open_in_new: Open"),
                         key="libfoto_%s" % it.get("ID", _f), width="stretch"):
                st.session_state["_lib_open"] = str(it.get("ID", ""))
                st.rerun()

    if _tot > 1:
        p1, p2, p3 = st.columns([1, 2, 1])
        if p1.button(t(":material/chevron_left: Previous"), key="lib_prev",
                     disabled=_pag <= 0, width="stretch"):
            st.session_state["_lib_pag"] = _pag - 1
            st.rerun()
        p2.caption(t("Page {a} of {b}", a=_pag + 1, b=_tot))
        if p3.button(t(":material/chevron_right: Next"), key="lib_next",
                     disabled=_pag >= _tot - 1, width="stretch"):
            st.session_state["_lib_pag"] = _pag + 1
            st.rerun()


def _tabla(items):
    T.section(t(":material/description: Documents"), t("{n} item(s)", n=len(items)))
    df = pd.DataFrame([{
        "Title": it.get("Title", ""),
        "Brand": str(it.get("Brand", "")) or "—",
        "Model": str(it.get("Model", "")) or "—",
        "Section": t(str(it.get("Section", ""))),
        "Type": _etq(str(it.get("Type", ""))),
        "Date": str(it.get("Date", ""))[:10],
    } for it in items])
    _ev = st.dataframe(df, width="stretch", hide_index=True,
                       on_select="rerun", selection_mode="single-row", key="lib_tbl",
                       column_config=tabla.cfg(None, {
                           "Title": st.column_config.TextColumn(t("Title"), width=280)}))
    _sr = list(_ev.selection.rows)
    if _sr and _sr[0] < len(items):
        st.session_state["_lib_open"] = str(items[_sr[0]].get("ID", ""))
        # ⚠️ Se suelta la selección: si no, al volver la tabla la reabre sola (v226/v228).
        st.session_state.pop("lib_tbl", None)
        st.rerun()


def _detalle(lid):
    if st.button(t(":material/arrow_back: Back to the library"), key="lib_back"):
        st.session_state.pop("_lib_open", None)
        st.rerun()
    it = LIB.get_item(lid)
    if not it:
        st.error(t("That item is no longer in the library."))
        return

    st.markdown("### " + str(it.get("Title", "")))
    st.markdown(" ".join([
        T.chip(_etiqueta(it)),
        T.chip(t(str(it.get("Section", ""))), T.VERDE),
        T.chip(_etq(str(it.get("Type", "")))),
    ]), unsafe_allow_html=True)
    if str(it.get("Notes", "")).strip():
        st.markdown(str(it.get("Notes", "")))
    st.caption(t("Filed by {who} on {when}",
                 who=str(it.get("UploadedBy", "")) or "—",
                 when=str(it.get("Date", ""))[:16] or "—"))

    _did = str(it.get("DriveID", "")).strip()
    dr = _drive()
    if _did and dr is not None:
        _bytes = None
        try:
            _bytes = dr.download(_did)       # aquí SÍ: es UNA ficha, la que se eligió
        except Exception as e:
            st.error("%s: %s" % (t("Could not download the file"), e))
        if _bytes:
            if str(it.get("Type", "")) == "photo":
                st.image(_bytes, width="stretch")
            st.download_button(t(":material/download: Download"), data=_bytes,
                               file_name=str(it.get("FileName", "")) or "file",
                               mime=str(it.get("MimeType", "")) or "application/octet-stream",
                               key="lib_dl")
    elif _did:
        st.caption(t("Drive is not connected: the file cannot be downloaded right now."))
    else:
        st.caption(t("This entry has no attached file — it is a note."))

    if _puede_subir():
        with st.expander(t(":material/delete: Remove from the library")):
            _ok = st.checkbox(t("I confirm I want to remove it"), key="lib_del_ok")
            if st.button(t(":material/delete: Remove"), key="lib_del",
                         disabled=not _ok, type="primary"):
                # ⚠️ El archivo de Drive PRIMERO: al revés se pierde el DriveID con la
                # fila y el archivo queda huérfano, inalcanzable desde la app — que es
                # exactamente el error de orden de v456.
                if _did and dr is not None:
                    try:
                        dr.delete(_did)
                    except Exception as e:
                        st.warning("%s: %s" % (t("The file could not be deleted from Drive"), e))
                ok, msg = LIB.delete_item(lid)
                if ok:
                    st.session_state.pop("_lib_open", None)
                    flash.exito(msg)
                    st.rerun()
                else:
                    st.error(msg)


# ── gestión (solo propietario) ───────────────────────────────────────────────
def _alta():
    with st.expander(t(":material/add_circle: File new material")):
        _marcas = LIB.marcas()
        if not _marcas:
            st.info(t(":material/info: There are no brands yet. Add one in the "
                      "catalogue below before filing material."))
        # ⚠️ Marca y modelo van FUERA del `st.form`: dentro, los widgets no escriben
        # hasta el submit, así que el desplegable de modelos no podría reaccionar a la
        # marca elegida (misma razón que v127/v189/v306).
        c1, c2 = st.columns(2)
        marca = c1.selectbox(t("Brand"), [""] + _marcas, key="lib_up_marca",
                             format_func=lambda x: t(LIB.SIN_MARCA) if not x else x)
        modelo = c2.selectbox(t("Model"), [""] + (LIB.modelos_de(marca) if marca else []),
                              key="lib_up_modelo", disabled=not marca,
                              format_func=lambda x: t(LIB.SIN_MODELO) if not x else x)

        with st.form("lib_up"):
            titulo = st.text_input(t("Title"),
                                   placeholder=t("e.g. Controller board layout"))
            c3, c4 = st.columns(2)
            seccion = c3.selectbox(t("Section"), LIB.SECCIONES, key="lib_up_sec",
                                   format_func=t)
            tipo = c4.selectbox(t("Type"), LIB.TIPOS, key="lib_up_tipo", format_func=t)
            notas = st.text_area(t("Notes (optional)"), height=80,
                                 placeholder=t("what it shows, where it was taken, "
                                               "anything worth knowing later"))
            up = st.file_uploader(t("File (photo, PDF, datasheet…)"), key="lib_up_file")
            if st.form_submit_button(t(":material/save: File it"), width="stretch"):
                _guardar(titulo, seccion, tipo, marca, modelo, notas, up)


def _guardar(titulo, seccion, tipo, marca, modelo, notas, up):
    """⚠️ El archivo se sube ANTES de escribir la fila: si Drive falla, no queda una
    ficha que promete un documento que no existe. Al revés sí quedaría, y encima sin
    forma de saber cuál (el orden que v343 fijó para las órdenes de compra)."""
    if not str(titulo or "").strip():
        st.error(t("The title is required."))
        return
    drive_id = filename = mime = ""
    if up is not None:
        dr = _drive()
        if dr is None:
            st.error(t("Drive is not connected, so the file cannot be stored. "
                       "Save it without a file or connect Drive first."))
            return
        try:
            drive_id = dr.upload_to(dr.folder(LIB.FOLDER_NAME), up.name,
                                    up.getvalue(), up.type or "application/octet-stream")
            filename, mime = up.name, (up.type or "")
        except Exception as e:
            st.error("%s: %s" % (t("The file could not be uploaded"), e))
            return
    ok, msg = LIB.add_item(titulo, seccion, tipo, marca=marca, modelo=modelo,
                           notas=notas, drive_id=drive_id, filename=filename,
                           mime=mime, creado_por=_usuario())
    if ok:
        flash.exito(t("Filed as {id}.", id=msg))
        st.rerun()
    else:
        # ⚠️ Si la fila no se escribió y el archivo SÍ subió, queda huérfano en Drive.
        # Se DICE, en vez de dejar basura invisible: la pantalla de mantenimiento de
        # Drive (v456) es la que lo recoge.
        if drive_id:
            st.warning(t("The file went up to Drive but the entry was not saved. "
                         "Check Drive maintenance."))
        st.error(msg)


def _catalogo():
    """Marcas y modelos. ⚠️ Se mantiene como el catálogo de rieles (decisión del
    usuario): se ELIGEN de una lista, no se teclean — una marca escrita a mano se
    escribe de tres formas distintas y deja de agrupar nada."""
    with st.expander(t(":material/sell: Brands and models")):
        _ver_inact = st.checkbox(t(":material/archive: Show deactivated ones too"),
                                 key="lib_cat_inact",
                                 help=t("Deactivating hides a model from the pickers; "
                                        "the material already filed under it stays."))
        filas = LIB.list_modelos(incluir_inactivos=_ver_inact)
        if filas:
            st.dataframe(
                pd.DataFrame([{
                    "Brand": f.get("Brand", ""),
                    "Model": f.get("Model", "") or "—",
                    "Active": "🟢" if str(f.get("Active", "SI")).upper() != "NO" else "🔴",
                } for f in filas]),
                width="stretch", hide_index=True, column_config=tabla.cfg())
        else:
            st.caption(t("No brands yet."))

        with st.form("lib_cat_new"):
            c1, c2 = st.columns(2)
            _mk = c1.text_input(t("Brand"), placeholder=t("e.g. Schindler"))
            # ⚠️ El modelo puede ir VACÍO a propósito: hay material de una marca sin
            # modelo concreto (un catálogo general), y exigirlo lo dejaría fuera.
            _md = c2.text_input(t("Model (optional)"), placeholder=t("e.g. 3300"))
            if st.form_submit_button(t(":material/add: Add to catalogue"),
                                     width="stretch"):
                ok, msg = LIB.add_modelo(_mk, _md)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()

        if filas:
            _op = {"%s · %s" % (f.get("Brand", ""), f.get("Model", "") or "—"): f
                   for f in filas}
            _sel = st.selectbox(t("Activate / deactivate"), [""] + list(_op),
                                key="lib_cat_sel",
                                format_func=lambda x: t("— pick one —") if not x else x)
            if _sel:
                _f = _op[_sel]
                _act = str(_f.get("Active", "SI")).upper() != "NO"
                if st.button(t(":material/toggle_off: Deactivate") if _act
                             else t(":material/toggle_on: Reactivate"), key="lib_cat_tog"):
                    ok, msg = LIB.set_modelo_activo(_f.get("Brand", ""),
                                                    _f.get("Model", ""), not _act)
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()
