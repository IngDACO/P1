"""📦 Inventario — UI de control de activos (v263, Fase 1).

KPIs + lista filtrable → ficha (foto, QR + etiqueta PDF, datos, valor depreciado,
edición, baja) + registro + catálogo de categorías. Solo admin/propietario.
Movimientos (entradas/salidas) y el escaneo que abre la ficha llegan en la Fase 2.

v599 · probada pantalla por pantalla en producción: ver HISTORIAL.md («Inventory»).
"""
import functools
import logging
import zlib

from core.i18n import t, etiqueta as _etiqueta
import pandas as pd
import streamlit as st

from core import flash

from core import tenant
from core import clock
from core import inventory as INV
from core.num import num as _num, dmy as _dmy
from core import tabla
from core import ui_common as ui
from core import theme as T
from core.maps import literal_md

logger = logging.getLogger(__name__)

# ⚠️ v667 · Los CÓDIGOS del inventario (estado, condición, tipo de ubicación y de movimiento) se guardan en
# inglés en minúscula («good», «available», «warehouse») y salían así en pantalla, junto a «Equipment» con
# mayúscula (ciclo 1, H17). Se muestran con la primera en mayúscula; lo que escribe una persona (una
# categoría propia, el nombre del almacén) sale tal cual.
_CODIGOS = (set(INV.ESTADOS) | set(INV.CONDICIONES) | set(INV.UBIC_TIPOS) | set(INV.MOV_TIPOS)
            | {"other", "project", "user", "warehouse"})


def _etq(v, defecto=None) -> str:
    s = _etiqueta(v, defecto)
    return s[:1].upper() + s[1:] if s and (str(v) in _CODIGOS or s in _CODIGOS) else s


# v599 · el filtro de la cifra «Service overdue» (no es un estado guardado: es la fecha)
_FILTRO_MANT = "__mant__"
# Obras a las que ya no se manda nada (v599, como el Survey en v589 y guardar en v592)
_CERRADAS = ("Completed", "Cancelled", "Archived", "Closed")


def _creado_por() -> str:
    a = st.session_state.get("auth") or {}
    return str(a.get("usuario", "") or a.get("nombre", ""))


# ⚠️ Solo el COLOR. El TEXTO vive en `i18n.VALORES` desde v463: tenerlo aquí además
# dejaba DOS definiciones del mismo estado, y por eso la ficha del activo decía
# «available» y su tabla «disponible» — el mismo activo en dos idiomas a dos clics.
# ⚠️ Las CLAVES son el estado GUARDADO en la hoja. v469 las migró a inglés, y lo
# que hace que eso sea seguro es que la constante y sus comparaciones se movieron
# JUNTAS: `inventory.py` e `inventory_ui` comparan ahora contra el mismo valor
# canónico. Traducir solo una de las dos partes deja la rama MUERTA sin dar ningún
# error (v442, el Caso 1 de corte de rieles) — lo vigila `verif_v463`.
# Y una fila SIN migrar sigue casando porque `valores.canon` la traduce al LEER.
_EST_COLOR = {"available": "green", "in use": "blue", "maintenance": "orange",
              "damaged": "red", "written off": "gray"}


def _est_lbl(estado) -> str:
    """El estado del activo CON su color, en el idioma de la pantalla.

    ⚠️ Devuelve MARKDOWN de color, así que vale para `st.markdown` y NO para una celda
    de `st.dataframe`, que lo pintaría literal (`:green[available]`). En una tabla va
    `_etq(...)` pelado — que es el mismo texto, sin el color.
    """
    _e = str(estado)
    _c = _EST_COLOR.get(_e)
    return f":{_c}[{_etq(_e)}]" if _c else _etq(_e)


def _ubic_txt(a, nom=None) -> str:
    """Ubicación legible. ⚠️ Delega en `INV.ubic_str` (v306): esta función era una COPIA
    de la del backend, así que al hacer que el proyecto se guarde por ID solo se habría
    arreglado una de las dos y la lista seguiría enseñando `PRJ-0007` (el patrón de dos
    mecanismos para lo mismo que v140 mandó no repetir)."""
    return INV.ubic_str(a, _etq, nom)            # v691 · con `nom`, la persona por su nombre (H10)


def _tipo_mov(tp) -> str:
    """El tipo de un movimiento, para pantalla (v691: los avisos del campo y «visto» de la oficina)."""
    return {"field: has it": t("Field: has it"), "field: returned": t("Field: returned it"),
            "field: problem": t("Field: problem"), INV.VISTO: t("Office: seen")}.get(str(tp)) or _etq(str(tp))


def _motivo_baja_txt(k) -> str:
    """El motivo de una baja (v691, D4). La CLAVE es el dato."""
    return {"lost": t("Lost"), "broken beyond repair": t("Broken beyond repair"), "stolen": t("Stolen"),
            "sold": t("Sold"), "other": t("Other")}.get(str(k), str(k))


def _cuando(fecha) -> str:
    """«22/11/2026 10:20» de un «2026-11-22 10:20:05»."""
    _f = str(fecha or "")
    return _dmy(_f[:10]) + (" " + _f[11:16] if len(_f) >= 16 else "")


def _indice_de(opciones, actual) -> int:
    """v600 · Dónde PRESELECCIONAR un desplegable de ACCIÓN (el traslado nace con dónde está el
    activo). ⚠️ No es un valor guardado que se reescriba (lo que vigila verif_v487): si no está
    en la lista se preselecciona la primera, y el botón sigue desactivado hasta cambiar algo."""
    return opciones.index(actual) if actual in opciones else 0


def _fecha_input(label, valor, key, desde_hoy=False):
    """date_input opcional (None permitido) → devuelve ISO o ''.

    v599 · `desde_hoy`: no deja elegir un día pasado (la devolución prevista)."""
    d0 = None
    try:
        from datetime import date
        d0 = date.fromisoformat(str(valor)[:10]) if str(valor).strip() else None
    except Exception:
        d0 = None
    _kw = {"min_value": clock.today()} if desde_hoy else {}
    # ⚠️ v600 · que se pueda VACIAR: creado con la fecha, se borraba en pantalla y se enviaba la
    # de antes (la revisión de un activo no se podía quitar, visto en producción)
    v = ui.fecha_opcional(label, d0, key, format="DD/MM/YYYY", **_kw)
    return v.isoformat() if v else ""


def _usuarios(grupo):
    try:
        from core import auth
        return [str(u.get("User", "")) for u in auth.list_users(grupo)
                if str(u.get("User", "")).strip()]
    except Exception:
        return []


def _nombres(grupo) -> dict:
    """v599 · usuario → «Nombre (usuario)»: el responsable se elegía por el USUARIO
    («dmoreno»), que no es como se conoce a la gente."""
    try:
        from core import auth
        out = {}
        for u in auth.list_users(grupo):
            _u = str(u.get("User", "")).strip()
            _n = str(u.get("Name", "")).strip()
            if _u:
                out[_u] = f"{_n} ({_u})" if _n and _n != _u else _u
        return out
    except Exception:
        return {}


def _proyectos(grupo):
    """`(ids, etiqueta)` de los proyectos del grupo, para elegir destino.

    ⚠️ v306: se guarda el **ID** en `UbicacionRef`, no el nombre. Antes se guardaba el
    nombre y con dos proyectos homónimos era imposible saber en cuál está el activo
    (y renombrar un proyecto dejaba huérfano el histórico, como pasaba con las horas
    antes de v145). Las filas antiguas siguen leyéndose: `ubic_proyecto` resuelve el
    ID si lo es y, si no, muestra el texto tal cual.
    ⚠️ v599 · solo las ABIERTAS: ofrecía obras canceladas y entregadas (visto en producción,
    Penrith y Mascot), como el Survey hasta v589.
    """
    try:
        from core import projects as P
        # v422: **con las localizaciones internas**. Un activo vive en el ALMACÉN más
        # que en ninguna obra: excluirlas dejaría el inventario sin su ubicación natural.
        _ps = [p for p in P.list_projects(grupo=grupo, incluir_internos=True)
               if str(p.get("ID", "")).strip() and str(p.get("Status", "")) not in _CERRADAS]
        _lbl = P.etiqueta_con_id(_ps)          # v667 · con el ID y «location» a la vista (ciclo 1)
        return [str(p.get("ID", "")) for p in _ps], _lbl
    except Exception:
        return [], {}


def _subir_foto(archivo) -> str:
    """La foto a Drive (carpeta del inventario). Devuelve su ID o '' (v599: una sola vía,
    para el alta y para «Change photo»)."""
    from core import drive_store
    if not drive_store.is_available():
        return ""
    return drive_store.upload_to(drive_store.folder("COPEX Assets"),
                                 archivo.name, archivo.getvalue(),
                                 archivo.type or "image/jpeg")


def _norm(s) -> str:
    return " ".join(str(s or "").casefold().split())


def _k_dup(nombre, serie) -> str:
    """La casilla «registrar aunque se repita» va POR nombre y serie (como Catalogue, v582):
    marcarla para uno no vale para otro."""
    return f"inv_dup_{zlib.crc32((_norm(nombre) + '|' + _norm(serie)).encode('utf-8'))}"


def _plural(n, uno, varios) -> str:
    return t(uno, n=n) if n == 1 else t(varios, n=n)


# ── Vista principal ──────────────────────────────────────────────
def _filtrar(categoria="Todas", estado="Todos", ubicacion="Todas"):
    """v600 · UNA forma de llevar a la lista ya filtrada (las cifras, los nombres de categoría y
    las filas de los informes): limpia el resto de filtros y baja a la tabla. Se llama ANTES de
    pintar los filtros (botón de arriba o callback), que es cuando Streamlit deja asignarlos."""
    st.session_state["inv_q"] = ""
    st.session_state["inv_catf"] = categoria
    st.session_state["inv_estf"] = estado
    st.session_state["inv_ubicf"] = ubicacion
    st.session_state["_bajar_cpx_inv_tabla"] = True


def _ver_bajas():
    st.session_state["inv_ver_baja"] = True


def _cifras(r, est):
    """v599 · ACTIVAS (eran cinco `st.metric` mudas que a 859 px partían «AVAILABL / E» y
    «$91 / 9»): cada una filtra la lista y baja a ella; el valor abre los informes."""
    _K = [("n", t("Assets"), str(r["n"])),
          ("disp", t("Available"), str(est.get(INV.DISPONIBLE, 0))),
          ("uso", t("In use"), str(est.get(INV.EN_USO, 0))),
          ("valor", t("Current value"), f"${r['valor_actual']:,.0f}"),
          ("mant", t("Service overdue"), str(r["mant_vencido"]))]
    st.markdown(T.por_fila("cpx_inv_kpis", 3), unsafe_allow_html=True)
    with st.container(key="cpx_inv_kpis"):
        for _col, (_s, _l, _v) in zip(st.columns(len(_K)), _K):
            _h = (t("Purchase value: {x} (straight-line depreciated). Opens the value reports.",
                    x=f"${r['valor_compra']:,.0f}") if _s == "valor" else t("Show them in the list"))
            if _col.button(f"{_l}\n\n{_v}", key=f"cpxkpi_inv_{_s}", width="stretch", help=_h):
                if _s == "valor":
                    st.session_state["_inv_rep_gen"] = st.session_state.get("_inv_rep_gen", 0) + 1
                    st.session_state["_bajar_cpx_inv_rep"] = True
                else:
                    _filtrar(estado={"n": "Todos", "disp": INV.DISPONIBLE,
                                     "uso": INV.EN_USO, "mant": _FILTRO_MANT}[_s])
                st.rerun()


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
    # ⚠️ v487: por la CONSTANTE. Con "disponible"/"en_uso" marcaban 0 SIEMPRE desde
    # v469, que canoniza el estado al leer: `por_estado` trae "available"/"in use".
    _cifras(r, est)

    if st.button(t(":material/add_circle: Register asset"), type="primary", key="inv_new"):
        st.session_state["_inv_nuevo"] = True
        st.rerun()

    # ⚠️ v340: dar de baja un activo era un VIAJE SIN VUELTA — `dar_de_baja` marca
    # `Activo=NO` y la lista usaba el default, que lo oculta, sin casilla para verlo
    # ni forma de reactivarlo. Mismo fallo que tenían los clientes y que v149 ya
    # había resuelto para los proyectos.
    # ⚠️ v600 · los filtros se RECUERDAN (`persist_state`, como Catalogue y Accounting): al abrir
    # una ficha y volver se perdían todos (visto verificando v599: «Taladro» → «(2 assets)»)
    _ver_baja = st.checkbox(t(":material/archive: Show written-off ones too"),
                            key="inv_ver_baja", persist_state="session",
                            help=t("A written-off asset leaves the inventory but keeps its movement history and its QR code."))
    acts = INV.list_activos(grupo, incluir_baja=_ver_baja)
    _n_baja = len([a for a in INV.list_activos(grupo, incluir_baja=True)
                   if str(a.get("Active", "SI")).upper() in ("NO", "FALSE", "0")])
    if _n_baja and not _ver_baja:
        # v600 · ACTIVO: enseña las de baja (era un texto mudo junto a la casilla que lo hace)
        st.button(":material/inventory_2: " + _plural(_n_baja, "{n} written-off asset hidden — show it",
                                                       "{n} written-off assets hidden — show them"),
                  key="inv_ver_bajas_btn", type="tertiary", on_click=_ver_bajas)
    if not acts:
        st.caption(t("No assets yet. Register the first one with «Register asset»."))
        _categorias_expander(grupo)
        return

    q = st.text_input(t(":material/search: Search"), key="inv_q", persist_state="session",
                      placeholder=t("name, serial, brand, location…")).strip().lower()
    # ⚠️ Las opciones son el DATO (categoría y estado guardados) y se comparan abajo;
    # solo se traduce el display: el «todas/todos» con `t()` y el resto con
    # `etiqueta()`, que es quien sabe traducir un valor de negocio (v442).
    # ⚠️ v600 · en TRES columnas bajo la búsqueda: en [2, 1, 1] el estado elegido salía cortado
    # («Service ov…», a 859 px con el menú).
    f2, f3, f4 = st.columns(3)
    _cats_f = ["Todas"] + INV.categorias(grupo)
    # v691 · y las que TIENEN los activos aunque ya no estén en la lista (ciclo 5, H14: no se podía filtrar por ella)
    _cats_f += sorted({str(a.get("Category", "")).strip() for a in acts} - set(_cats_f) - {""})
    if st.session_state.get("inv_catf") not in _cats_f:     # una categoría ya quitada (o la de un informe)
        _cats_f.append(st.session_state.get("inv_catf"))
    cat_f = f2.selectbox(t("Category"), _cats_f,
                         format_func=lambda o: t("All") if o == "Todas" else _etq(o),
                         key="inv_catf", persist_state="session")
    est_f = f3.selectbox(t("Status"), ["Todos"] + INV.ESTADOS + [_FILTRO_MANT],
                         format_func=lambda o: (t("All") if o == "Todos" else
                                                t("Service overdue") if o == _FILTRO_MANT else _etq(o)),
                         key="inv_estf", persist_state="session")
    # v600 · por UBICACIÓN (lo piden las filas «By location» de los informes)
    ubic_f = f4.selectbox(t("Location"), ["Todas"] + INV.UBIC_TIPOS,
                          format_func=lambda o: t("All") if o == "Todas" else _etq(o),
                          key="inv_ubicf", persist_state="session")
    _rows = acts
    if q:
        _rows = [a for a in _rows if q in (" ".join(
            str(a.get(k, "")) for k in ("Name", "Serial", "Brand", "Model", "ID")) + " " + _ubic_txt(a)).lower()]
    if cat_f != "Todas":
        _rows = [a for a in _rows if str(a.get("Category", "")) == cat_f]
    if est_f == _FILTRO_MANT:
        _hoy = clock.today()
        _rows = [a for a in _rows if (INV._parse_date(a.get("NextService")) or _hoy) < _hoy]
    elif est_f != "Todos":
        _rows = [a for a in _rows if str(a.get("Status", "")) == est_f]
    if ubic_f != "Todas":
        _rows = [a for a in _rows if str(a.get("LocationType", "")) == ubic_f]
    _rows = sorted(_rows, key=lambda a: str(a.get("Name", "")).lower())

    _nom = _nombres(grupo)
    from core import projects_ui as _PU
    with st.container(key="cpx_inv_tabla"):          # v599 · destino de las cifras
        _PU._bajar_a("cpx_inv_tabla", "_bajar_cpx_inv_tabla", bloque="start")
        if not _rows:
            # v600 · con los filtros RECORDADOS, «nada coincide» necesita su salida (como v558)
            st.info(t("Nothing matches these filters."))
            st.button(t(":material/filter_alt_off: Show all"), key="inv_ver_todo", on_click=_filtrar)
            _reportes(grupo)
            _categorias_expander(grupo)
            return
        st.caption(t("Tap an asset to see its record, its QR code and manage it.") + " "
                   + _plural(len(_rows), "({n} asset)", "({n} assets)"))
        df = pd.DataFrame([{
            # v599 · el ID primero: dos activos con el MISMO nombre no se distinguían
            "ID":          a.get("ID", ""),
            "Nombre":      a.get("Name", ""),
            "Category":   _etq(str(a.get("Category", ""))) or "—",
            "Estado":      _etq(str(a.get("Status", ""))),
            "Location":   _ubic_txt(a, _nom),
            "Assigned to":  _nom.get(str(a.get("AssignedTo", "")), a.get("AssignedTo", "")) or "—",
            "Valor":       round(INV.valor_actual(a), 0),
        } for a in _rows])
        _ev = st.dataframe(
            df, width="stretch", hide_index=True,
            # ⚠️ v598 · `single-cell`, como Files en v592: con `single-row` un toque en la celda solo
            # la enmarcaba (la ficha se abría únicamente marcando la casilla).
            on_select="rerun", selection_mode="single-cell", key="inv_tbl",
            column_config=tabla.cfg(None, {
                "ID": st.column_config.TextColumn("ID", width=80, pinned=True),
                "Nombre": st.column_config.TextColumn(t("Name"), pinned=True),
                "Valor": st.column_config.NumberColumn(t("Value"), format="$%,d")}))
    _s = _ev.selection            # v598 · la fila de la CELDA tocada (o la de la casilla)
    _sr = [c[0] for c in (getattr(_s, "cells", None) or [])] or list(getattr(_s, "rows", None) or [])
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

    _nom = _nombres(grupo)
    st.markdown(f"## :material/inventory_2: {a.get('Name', '')}")
    st.markdown(f"**{a.get('ID', '')}**  ·  {_etq(str(a.get('Category', ''))) or '—'}  ·  "
                f"{_est_lbl(a.get('Status', ''))}")

    # ── Acciones (salida/entrada/traslado/mantenimiento) ──
    # ⚠️ v599 · JUSTO debajo del título: se llega escaneando el QR con el móvil, y las acciones
    # quedaban debajo de los valores y del propio QR que acababas de escanear.
    _est = str(a.get("Status", "")).lower()
    _cp = _creado_por()
    _avisos_del_campo(grupo, aid, _nom, _cp)          # v691 · D3: confirmar o dar por visto
    if _est == "written off":
        # v340: la vuelta. Antes un activo de baja no se podía reactivar desde la app.
        _mot = INV.motivo_baja(grupo, aid)
        _mk, _, _mn = _mot.partition(" — ")
        st.warning(t(":material/block: This asset is **written off**: it does not appear in the inventory unless you tick «Show written-off ones too».")
                   + (" " + t("Reason: {x}", x=literal_md(_motivo_baja_txt(_mk) + (f" — {_mn}" if _mn else "")))
                      if _mot else ""))
        # v691 · vuelve a un ALMACÉN y sin responsable (ciclo 5, H11: volvía «available» y en manos de alguien)
        _bod_r = st.text_input(t("Back to (store location)"), value=INV.ultima_bodega(grupo, aid) or "Store",
                               key=f"inv_react_bod_{aid}")
        if st.button(t(":material/restore: Reactivate this asset"),
                     key=f"inv_react_{aid}", type="primary"):
            ok, msg = INV.reactivar(aid, grupo, _cp, bodega=_bod_r)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()
    else:
        st.markdown(t("#### :material/swap_horiz: Actions"))
        # ⚠️ v600 · los campos de las acciones van por GENERACIÓN: tras registrar se quedaban con
        # lo tecleado y un 2º toque repetía el movimiento y su costo (visto verificando v599)
        _ag = st.session_state.get(f"_inv_acc_gen_{aid}", 0)

        def _nueva_gen():
            st.session_state[f"_inv_acc_gen_{aid}"] = _ag + 1

        if _est == "available":
            # v599 · a ANCHO COMPLETO: en media columna el nombre de la obra salía cortado
            with st.expander(t(":material/logout: Check out / hand over"), key=f"exp_inv_sal_{aid}"):
                _dt = st.selectbox(t("Destination"), ["project", "user", "other"],
                                   format_func=lambda o: t({"project": "a project",
                                                            "user": "a person",
                                                            "other": "somewhere else"}.get(o, o)),
                                   key=f"inv_sdt_{aid}_{_ag}")
                _ref = ""
                if _dt == "project":
                    # El VALOR es el ID (identidad); la etiqueta es el nombre (comodidad).
                    _pids, _plbl = _proyectos(grupo)
                    if _pids:
                        # v691 · sin preselección (ciclo 5, H8: nacía con la primera obra de la lista)
                        _ref = st.selectbox(t("Project"), _pids, key=f"inv_srp_{aid}_{_ag}",
                                            format_func=lambda i: _plbl.get(i, i), index=None,
                                            placeholder=t("— choose the project —"))
                    else:
                        st.info(t("There are no open jobs to send it to."))
                elif _dt == "user":
                    _us = _usuarios(grupo)
                    if _us:
                        # v691 · sin preselección (ciclo 5, H13: nacía con «asfgjjd (admin1)»)
                        _ref = st.selectbox(t("Person"), _us, key=f"inv_sru_{aid}_{_ag}",
                                            format_func=lambda u: _nom.get(u, u), index=None,
                                            placeholder=t("— choose the person —"))
                    else:
                        st.info(t("There are no users to hand it to."))
                else:
                    _ref = st.text_input(t("Destination"), key=f"inv_srt_{aid}_{_ag}")
                _resp = st.selectbox(t("Person responsible"), ["—"] + _usuarios(grupo),
                                     key=f"inv_srsp_{aid}_{_ag}",
                                     format_func=lambda u: u if u == "—" else _nom.get(u, u))
                if _dt == "project" and _resp == "—":
                    # v691 · ciclo 5, H7: salía a la obra sin nadie a cargo y su vuelta no se veía en ninguna parte
                    st.caption(t(":material/info: Nobody will be responsible for it on site: choose a person "
                                 "responsible if someone should bring it back."))
                _dev = _fecha_input(t("Expected return"), "", f"inv_sdev_{aid}_{_ag}", desde_hoy=True)
                _n = st.text_input(t("Note"), key=f"inv_snota_{aid}_{_ag}")
                if st.button(t(":material/check: Record check-out"), type="primary", key=f"inv_sbtn_{aid}_{_ag}",
                             disabled=(_dt in ("project", "user") and not _ref)):
                    _u = ("" if _resp == "—" else _resp) or (_ref if _dt == "user" else "")
                    ok, msg = INV.salida(aid, grupo, usuario=_u, hacia_tipo=_dt, hacia_ref=_ref,
                                         fecha_devolucion=_dev, nota=_n, creado_por=_cp)
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        _nueva_gen()
                        st.rerun()
        else:
            with st.expander(t(":material/login: Check in / return"), expanded=True, key=f"exp_inv_ent_{aid}"):
                # v667 · nace con el sitio de donde salió (su balda), no con «Store» (ciclo 1: se perdía)
                _bod = st.text_input(t("Store / return location"), value=INV.ultima_bodega(grupo, aid) or t("Store"),
                                     key=f"inv_ebod_{aid}_{_ag}")
                _n = st.text_input(t("Note"), key=f"inv_enota_{aid}_{_ag}")
                if st.button(t(":material/check: Record check-in"), type="primary", key=f"inv_ebtn_{aid}_{_ag}"):
                    ok, msg = INV.entrada(aid, grupo, bodega=_bod, nota=_n, creado_por=_cp)
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        _nueva_gen()
                        st.rerun()
        # v599 · apilados a ancho completo: el traslado elige ahora una obra, y en media
        # columna su nombre se cortaba como el de la salida
        with st.expander(t(":material/move_up: Transfer"), key=f"exp_inv_tr_{aid}"):
            # ⚠️ v600 · el panel NACE con donde está ahora (desactivado hasta que se cambie algo):
            # tras registrar volvía a «warehouse» vacío y un 2º toque lo trasladaba otra vez
            _t0, _r0 = str(a.get("LocationType", "")), str(a.get("LocationRef", "") or "")
            _tt = st.selectbox(t("New location (type)"), INV.UBIC_TIPOS, key=f"inv_ttt_{aid}_{_ag}",
                               index=_indice_de(INV.UBIC_TIPOS, _t0),
                               format_func=_etq)
            # ⚠️ v599 · una obra o una persona se ELIGEN (por su ID / usuario): era texto libre
            if _tt == "project":
                _pids, _plbl = _proyectos(grupo)
                _tr = (st.selectbox(t("Project"), _pids, key=f"inv_ttp_{aid}_{_ag}",
                                    index=_indice_de(_pids, _r0 if _t0 == _tt else None),
                                    format_func=lambda i: _plbl.get(i, i)) if _pids else "")
                if not _pids:
                    st.info(t("There are no open jobs to send it to."))
            elif _tt == "user":
                _us = _usuarios(grupo)
                _tr = (st.selectbox(t("Person"), _us, key=f"inv_ttu_{aid}_{_ag}",
                                    index=_indice_de(_us, _r0 if _t0 == _tt else None),
                                    format_func=lambda u: _nom.get(u, u)) if _us else "")
            else:
                # la clave lleva el TIPO: al cambiarlo, el detalle no arrastra el del otro sitio
                _tr = st.text_input(t("Detail"), value=_r0 if _t0 == _tt else "",
                                    key=f"inv_ttr_{aid}_{_tt}_{_ag}")
            if _tt == INV.REPARACION:
                st.caption(t("Sending it for repair marks it as under maintenance until it comes back."))
            _n = st.text_input(t("Note"), key=f"inv_tnota_{aid}_{_ag}")
            # v600 · a donde ya está no es un traslado (el motor también lo rechaza)
            _ya = (_tt == str(a.get("LocationType", ""))
                   and str(_tr or "").strip() == str(a.get("LocationRef", "") or "").strip())
            if _ya:
                st.caption(t("The asset is already there."))
            if st.button(t(":material/check: Transfer"), key=f"inv_tbtn_{aid}_{_ag}",
                         disabled=(_tt in ("project", "user") and not _tr) or _ya):
                ok, msg = INV.traslado(aid, grupo, _tt, _tr, nota=_n, creado_por=_cp)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    _nueva_gen()
                    st.rerun()
        with st.expander(t(":material/build: Service"), key=f"exp_inv_mt_{aid}"):
            _costo = st.number_input(t("Cost"), min_value=0.0, step=10.0, key=f"inv_mcosto_{aid}_{_ag}")
            _prox = _fecha_input(t("Next maintenance"), a.get("NextService"),
                                 f"inv_mprox_{aid}_{a.get('NextService', '')}_{_ag}")
            # v599 · decía «Leave the asset IN service», que se lee justo al revés (en uso)
            _enm = st.checkbox(t("Mark it as under maintenance (out of use)"), key=f"inv_menm_{aid}_{_ag}")
            _n = st.text_input(t("Note"), key=f"inv_mnota_{aid}_{_ag}")
            if st.button(t(":material/check: Record service"), key=f"inv_mbtn_{aid}_{_ag}",
                         disabled=not INV.servicio_con_datos(a, _costo, _prox, _n, _enm)):
                ok, msg = INV.mantenimiento(aid, grupo, costo=_costo, proximo=_prox, nota=_n,
                                            en_mant=_enm, creado_por=_cp)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    _nueva_gen()
                    st.rerun()

    izq, der = st.columns([3, 2])
    with izq:
        vc, va = _num(a.get("PurchaseValue")), INV.valor_actual(a)
        m1, m2 = st.columns(2)
        m1.metric(t("Purchase value"), f"${vc:,.0f}")
        m2.metric(t("Current value"), f"${va:,.0f}",
                  help=t("Straight-line depreciation over the useful life."))
        st.markdown(t("**Location:** {u}  ·  **Condition:** {c}", u=_ubic_txt(a, _nom),
                      c=_etq(str(a.get("Condition", ""))) or "—"))
        if str(a.get("AssignedTo", "")).strip():
            _asg = str(a.get("AssignedTo"))
            st.markdown(f"**{t('Assigned to')}:** {_nom.get(_asg, _asg)}")
        # ⚠️ v691 · la VUELTA, con o sin responsable (ciclo 5, H7: solo salía junto a «Assigned to», y una salida
        # a una obra sin responsable guardaba el 24/11 sin enseñarlo en ninguna parte)
        _fdv, _ddv = INV.vuelta_de(a)
        if _fdv and str(a.get("Status", "")) == "in use":
            st.markdown((f":red[:material/event_busy: {t('Due back')}: {_dmy(_fdv.isoformat())} · "
                         + t("{n} d late", n=-_ddv) + "]") if _ddv < 0 else
                        f":material/event: {t('Due back')}: {_dmy(_fdv.isoformat())}")
        _pm = str(a.get("NextService", "")).strip()
        if _pm:
            _pd = INV._parse_date(_pm)
            if _pd and _pd < clock.today():
                st.markdown(f":red[:material/build: {t('Maintenance OVERDUE')}: {_dmy(_pm)}]")
            else:
                st.markdown(":material/build: " + t("Next service: {f}", f=_dmy(_pm)))
        if str(a.get("Note", "")).strip():
            st.caption(a.get("Note"))
    with der:
        if a.get("PhotoDriveID"):
            try:
                from core import drive_store
                st.image(drive_store.download(a.get("PhotoDriveID")), width=220)
            except Exception:
                pass
        # v599 · la foto se cambia AQUÍ: el aviso del alta decía «Add it later from its record»
        # y la ficha no tenía cómo
        _fg = st.session_state.get(f"_inv_foto_gen_{aid}", 0)
        with st.expander(t(":material/photo_camera: Change photo") if a.get("PhotoDriveID")
                         else t(":material/photo_camera: Add a photo"), key=f"exp_inv_foto_{aid}"):
            _f = st.file_uploader(t("Photo"), type=["png", "jpg", "jpeg"], key=f"inv_foto_{aid}_{_fg}")
            if st.button(t(":material/save: Save photo"), key=f"inv_foto_btn_{aid}", disabled=_f is None):
                try:
                    _fid = _subir_foto(_f)
                except Exception as e:
                    logger.warning("inventory_ui: la foto del activo no subió a Drive: %s", e)
                    _fid = ""
                if _fid:
                    ok, msg = INV.update_activo(aid, {"PhotoDriveID": _fid})
                    if ok:
                        st.session_state[f"_inv_foto_gen_{aid}"] = _fg + 1
                        flash.exito(t("Photo saved."))
                        st.rerun()
                    st.error(msg)
                else:
                    st.error(t("The photo could not be uploaded to Drive."))

    # v599 · el QR y su etiqueta, PLEGADOS: se llega escaneándolo
    with st.expander(t(":material/qr_code_2: QR code and label"), key=f"exp_inv_qr_{aid}"):
        try:
            _png = INV.qr_png(aid)
            st.image(_png, width=170)
            if not INV.app_url():
                st.caption(t(":material/info: Set the APP_URL secret so the QR code opens the app."))
            try:
                from core import asset_label_pdf
                from core import contable as _CB
                # v691 · ciclo 5, H9: con el nombre LEGAL de la empresa (salía «cliente1», su identificador interno)
                _pdf = asset_label_pdf.generate_label_pdf(a, _png, _CB.identidad(grupo).get("legal") or grupo)
                st.download_button(t(":material/download: Label (PDF)"), data=_pdf,
                                   file_name=f"Asset_label_{aid}.pdf", mime="application/pdf",
                                   key=f"inv_lbl_{aid}")
                if not _CB.tiene_razon_social(grupo):
                    st.caption(t(":material/warning: The label shows «{g}»: the company has no legal name yet. The "
                                 "account owner sets it in Administration → Groups → «Tax identity and payment "
                                 "terms».", g=str(grupo)))
            except Exception as e:
                st.caption(t("The label could not be generated: {e}", e=e))
        except Exception as e:
            st.caption(t("The QR code could not be generated: {e}", e=e))

    # ── Historial ──
    st.markdown(t("#### :material/history: History"))
    movs = INV.list_movimientos(grupo, aid)
    if not movs:
        st.caption(t("No movements yet."))
    else:
        _mr = sorted(movs, key=lambda m: str(m.get("Created", "")), reverse=True)
        st.dataframe(pd.DataFrame([{
            "Fecha":   _dmy(m.get("Date", "")),      # v599 · DD/MM/YYYY (iba en ISO)
            "Tipo":    _tipo_mov(m.get("Type", "")),                                   # v691
            "Desde":   INV.ubic_texto(m.get("FromLocation", ""), _etq, _nom) or "—",   # v691 · H10
            "Hacia":   INV.ubic_texto(m.get("ToLocation", ""), _etq, _nom) or "—",
            "Usuario": _nom.get(str(m.get("User", "")), m.get("User", "")) or "—",
            # ⚠️ Cadena vacía, NO NaN: `st.dataframe` pinta cualquier nulo como el
            # literal «None» en gris y ninguna `column_config` lo evita — el cuadro
            # de lo medido está en `tabla.celda`. Lo que decía aquí («con NaN sale
            # vacia, medido») era FALSO: esta tabla seguía diciendo «None».
            "Costo":   (tabla.celda(m.get("Cost"), 0, "$")
                        if str(m.get("Cost", "")).strip() else ""),
            "Nota":    m.get("Note", "") or "",
        } for m in _mr]), width="stretch", hide_index=True,
            column_config=tabla.cfg(None, {"Costo": tabla.derecha(t("Cost"))}))

    # Editar
    st.markdown(t("#### :material/edit: Edit asset"))
    # ⚠️ v599 · Enter NO envía (con él se mandaba la edición a medias) y las fechas llevan en
    # la CLAVE lo guardado: con clave fija conservaban el valor de antes y «Save changes»
    # DESHACÍA el último mantenimiento (la próxima revisión volvió de 2027 a la vencida, visto
    # en producción).
    with st.form(f"inv_edit_{aid}", enter_to_submit=False):
        e1, e2 = st.columns(2)
        nombre = e1.text_input(t("Name"), value=a.get("Name", ""))
        cats = INV.categorias(grupo)
        # ⚠️ v487: los cuatro desplegables CONSERVAN el valor guardado aunque ya no
        # este en la lista (una categoria borrada). Antes mostraban la primera opcion
        # y «Save changes» la escribia encima, sin que nadie la eligiera.
        _cats, _ci = ui.opciones_con_actual(cats, a.get("Category"))
        categoria = e2.selectbox(t("Category"), _cats, index=_ci, format_func=_etq)
        marca = e1.text_input(t("Brand"), value=a.get("Brand", ""))
        modelo = e2.text_input(t("Model"), value=a.get("Model", ""))
        serie = e1.text_input(t("Serial no."), value=a.get("Serial", ""))
        # v599 · sin «in use» ni «written off»: los ponen la salida y la baja (desde aquí el
        # activo quedaba de baja en la ficha y en la lista a la vez, sin movimiento)
        _st0 = str(a.get("Status", ""))
        if _st0 in (INV.EN_USO, INV.BAJA):
            # ⚠️ v600 · FIJO: en un activo de baja se podía elegir «available» y quedaba oculto pero
            # disponible, sin movimiento (visto verificando v599); y uno prestado pasaba a
            # disponible con su responsable puesto. Se sale con la devolución o con «Reactivate».
            estado = e2.selectbox(t("Status"), [_st0], format_func=_etq, disabled=True,
                                  help=t("«In use» ends with the check-in and «written off» with «Reactivate»."))
        else:
            _ests, _ei = ui.opciones_con_actual(INV.ESTADOS_EDITABLES, a.get("Status"))
            estado = e2.selectbox(t("Status"), _ests, index=_ei, format_func=_etq,
                                  help=t("«In use» comes from the check-out and «written off» from Write off."))
        _conds, _cdi = ui.opciones_con_actual(INV.CONDICIONES, a.get("Condition"))
        condicion = e1.selectbox(t("Condition"), _conds, index=_cdi, format_func=_etq)
        _ubics, _ubi = ui.opciones_con_actual(INV.UBIC_TIPOS, a.get("LocationType"))
        ubic_t = e2.selectbox(t("Location (type)"), _ubics, index=_ubi, format_func=_etq)
        ubic_r = e1.text_input(t("Location (detail)"), value=a.get("LocationRef", ""),
                               help=t("Store or person holding it. If the asset is on a site, this holds the project ID (PRJ-####) — it is set automatically when the check-out is recorded; the list shows the name."))
        if str(a.get("LocationRef", "")).startswith("PRJ-"):
            e1.caption(f":material/folder: {INV.ubic_ref_label(a.get('LocationRef'))}")
        vc = e2.number_input(t("Purchase value"), min_value=0.0, step=10.0,
                             value=_num(a.get("PurchaseValue")))
        c3, c4 = st.columns(2)
        with c3:                                   # v599 · era una columna vacía
            f_compra = _fecha_input(t("Purchase date"), a.get("PurchaseDate"),
                                    f"inv_fc_{aid}_{a.get('PurchaseDate', '')}")
        # v667 · «%g»: 5 años se ve «5», no «5.00» (ciclo 1); medio año sigue cabiendo («2.5»)
        vida = c4.number_input(t("Useful life (years)"), min_value=0.0, step=1.0, format="%g",
                               value=_num(a.get("UsefulLifeYears")))
        with c3:
            prox = _fecha_input(t("Next maintenance"), a.get("NextService"),
                                f"inv_pm_{aid}_{a.get('NextService', '')}")
        nota = st.text_area(t("Note"), value=a.get("Note", ""), height=80)
        if st.form_submit_button(t(":material/save: Save changes"), type="primary"):
            ok, msg = INV.update_activo(aid, {
                "Name": nombre, "Category": categoria, "Brand": marca, "Model": modelo,
                "Serial": serie, "Status": estado, "Condition": condicion,
                "LocationType": ubic_t, "LocationRef": ubic_r, "PurchaseValue": vc,
                "PurchaseDate": f_compra, "UsefulLifeYears": vida, "NextService": prox, "Note": nota})
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()

    if _est != "written off":
        with st.expander(t(":material/block: Write off"), key=f"exp_inv_baja_{aid}"):
            st.caption(t("Takes the asset out of the inventory (it stays in the history). To see it again, tick «Show written-off ones too»."))
            # ⚠️ v691 · D4 del usuario (ciclo 5, H11): se daba de baja algo PRESTADO sin decirlo y sin motivo
            if _est == "in use" or str(a.get("AssignedTo", "")).strip():
                _q = _nom.get(str(a.get("AssignedTo", "")), str(a.get("AssignedTo", ""))) or "—"
                _fdb, _ = INV.vuelta_de(a)
                st.warning(t(":material/warning: It is out ({u}) with **{q}**{v}. Writing it off ends that; the "
                             "history keeps who had it.", u=_ubic_txt(a, _nom), q=_q,
                             v=(" " + t("until {f}", f=_dmy(_fdb.isoformat()))) if _fdb else ""))
            _mk = st.selectbox(t("Reason"), list(INV.MOTIVOS_BAJA), index=None, format_func=_motivo_baja_txt,
                               placeholder=t("— choose the reason —"), key=f"inv_baja_mk_{aid}")
            _mot = st.text_input(t("Note (optional)"), key=f"inv_baja_mot_{aid}")
            # v599 · con confirmación y con aviso (salía sin preguntar y sin decir nada)
            _conf = ui.confirmar_borrado(f"inv_baja_conf_{aid}", t("I confirm I want to write off this asset"))
            if st.button(t("Write off this asset"), key=f"inv_baja_{aid}", disabled=not (_conf and _mk)):
                _motivo = str(_mk or "") + (f" — {' '.join(str(_mot).split())}" if str(_mot).strip() else "")
                ok, msg = INV.dar_de_baja(aid, grupo, _motivo, _creado_por())
                if ok:
                    flash.exito(msg)
                    st.session_state.pop("_inv_open", None)
                    st.rerun()
                st.error(msg)


def _avisos_del_campo(grupo, aid, _nom, _cp):
    """v691 · D3 del usuario: lo que el campo dijo de ESTE activo, para confirmarlo (el movimiento de verdad) o
    darlo por visto."""
    for x in INV.avisos_pendientes(grupo, aid):
        _q = literal_md(_nom.get(x["usuario"], x["usuario"]))
        _txt = {"has it": t("**{q}** says they have it ({c}).", q=_q, c=_cuando(x["fecha"])),
                "returned": t("**{q}** says they returned it ({c}).", q=_q, c=_cuando(x["fecha"])),
                "problem": t("**{q}** reports a problem ({c}): {n}", q=_q, c=_cuando(x["fecha"]),
                             n=literal_md(x["nota"]))}.get(x["tipo"], "")
        with st.container(border=True, key=f"cpx_inv_aviso_{x['id']}"):
            st.markdown(":material/campaign: " + _txt)
            _c1, _c2 = st.columns(2)
            ok = msg = None
            if x["tipo"] == "has it":
                if _c1.button(t(":material/check: Confirm: it is with them"), key=f"inv_avok_{x['id']}",
                              type="primary", width="stretch"):
                    ok, msg = INV.pasar_a(aid, grupo, x["usuario"], _cp)
            elif x["tipo"] == "returned":
                _bod = INV.ultima_bodega(grupo, aid) or "Store"
                if _c1.button(t(":material/check: Confirm the return ({b})", b=_bod), key=f"inv_avok_{x['id']}",
                              type="primary", width="stretch"):
                    ok, msg = INV.entrada(aid, grupo, bodega=_bod, nota="returned (from the field)", creado_por=_cp)
            else:
                _c1.caption(t("If it needs one, record a service above."))
            if _c2.button(t(":material/close: Dismiss"), key=f"inv_avno_{x['id']}", width="stretch"):
                ok, msg = INV.dar_por_visto(aid, grupo, x["id"], _cp)
            if ok is not None:
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()


def render_equipo_campo(usuario, grupo):
    """🧰 «My equipment» del CAMPO (v691, D3 del usuario, ciclo 5 H15/H12): lo que tiene a su cargo y, por el QR o por
    el ID de la etiqueta, la ficha de cualquier equipo de su empresa en SOLO LECTURA, con «I have it», «I returned
    it» y «Report a problem», que la oficina confirma. Escanear el QR no hacía nada para el campo."""
    st.markdown(t("## :material/construction: My equipment"))
    if not INV.is_configured():
        st.info(t(":material/info: Configure Google Sheets for the inventory."))
        return
    _nom = _nombres(grupo)
    if st.session_state.get("_equipo_open"):
        _ficha_campo(grupo, usuario, str(st.session_state["_equipo_open"]), _nom)
        return
    _mios = sorted(INV.de_la_persona(grupo, usuario), key=lambda a: str(a.get("Name", "")).lower())
    if not _mios:
        st.caption(t("No company equipment is signed out to you."))
    for a in _mios:
        _fd, _dd = INV.vuelta_de(a)
        _l = f"**{literal_md(a.get('Name', ''))}** · {a.get('ID', '')}"
        if _fd:
            _l += " · " + (t("{n} d late", n=-_dd) if _dd < 0 else t("back by {f}", f=_dmy(_fd.isoformat())))
        if st.button(":material/construction: " + _l, key=f"inv_campo_{a.get('ID', '')}", width="stretch"):
            st.session_state["_equipo_open"] = str(a.get("ID", ""))
            st.rerun()
    # un solo campo: Enter envía (la regla de v617 es para los de 2 o más)
    with st.form("inv_campo_buscar"):
        _id = st.text_input(t("Asset ID on the label"), placeholder=t("e.g. {id}", id="ACT-0001"),
                            help=t("Or scan its QR code with the phone camera."))
        if st.form_submit_button(t(":material/search: Open")):
            _a = INV.get_activo(str(_id or "").strip().upper())
            if _a and str(_a.get("Group", "")) == str(grupo):
                st.session_state["_equipo_open"] = str(_a.get("ID", ""))
                st.rerun()
            st.error(t("There is no asset with that ID."))


def _ficha_campo(grupo, usuario, aid, _nom):
    """La ficha de un equipo para el campo: qué es, dónde está, quién lo tiene, cuándo vuelve y su revisión."""
    if st.button(t(":material/arrow_back: Back to my equipment"), key="inv_campo_back"):
        st.session_state.pop("_equipo_open", None)
        st.rerun()
    a = INV.get_activo(aid)
    # el de OTRA empresa responde como si no existiera (regla v351)
    if not a or str(a.get("Group", "")) != str(grupo):
        st.warning(t("Asset not found."))
        return
    st.markdown(f"### {literal_md(a.get('Name', ''))}")
    st.caption(f"{a.get('ID', '')} · {_etq(str(a.get('Category', ''))) or '—'} · {_etq(str(a.get('Status', '')))}")
    if a.get("PhotoDriveID"):
        try:
            from core import drive_store
            st.image(drive_store.download(a.get("PhotoDriveID")), width=220)
        except Exception:
            pass
    _asg = str(a.get("AssignedTo", "") or "").strip()
    st.markdown(t("**Where it is:** {u}", u=literal_md(_ubic_txt(a, _nom))))
    st.markdown(t("**With:** {q}", q=literal_md(_nom.get(_asg, _asg)) if _asg else t("nobody")))
    _fd, _dd = INV.vuelta_de(a)
    if _fd and str(a.get("Status", "")) == "in use":
        st.markdown((f":red[{t('Due back')}: {_dmy(_fd.isoformat())} · " + t("{n} d late", n=-_dd) + "]")
                    if _dd < 0 else f"**{t('Due back')}:** {_dmy(_fd.isoformat())}")
    _pm = INV._parse_date(a.get("NextService"))
    if _pm:
        st.markdown((f":red[:material/build: {t('Service overdue')}: {_dmy(_pm.isoformat())}]")
                    if _pm < clock.today() else f":material/build: {t('Next service: {f}', f=_dmy(_pm.isoformat()))}")
    _mio = _asg == str(usuario) or (str(a.get("LocationType", "")) == "user"
                                    and str(a.get("LocationRef", "")).strip() == str(usuario))
    _esp = {x["tipo"]: x for x in INV.avisos_pendientes(grupo, aid) if x["usuario"] == str(usuario)}
    for _k, _txt in (("has it", t("You told the office you have it: waiting for them to confirm.")),
                     ("returned", t("You told the office you returned it: waiting for them to confirm.")),
                     ("problem", t("The office has your note about a problem."))):
        if _k in _esp:
            st.info(":material/schedule: " + _txt)
    if str(a.get("Status", "")) == INV.BAJA:
        st.caption(t("This asset is written off."))
        return
    ok = msg = None
    _c1, _c2 = st.columns(2)
    if not _mio and "has it" not in _esp:
        if _c1.button(t(":material/back_hand: I have it"), key=f"inv_campo_tengo_{aid}", type="primary",
                      width="stretch"):
            ok, msg = INV.avisar_desde_campo(aid, grupo, usuario, "has it")
    if _mio and "returned" not in _esp:
        if _c1.button(t(":material/assignment_return: I returned it"), key=f"inv_campo_devolvi_{aid}",
                      type="primary", width="stretch"):
            ok, msg = INV.avisar_desde_campo(aid, grupo, usuario, "returned")
    with st.expander(t(":material/report: Report a problem"), key=f"exp_inv_campo_prob_{aid}"):
        # por GENERACIÓN: vaciar la caja quitando su valor no llega al navegador (trampa 31)
        _gp = st.session_state.get(f"_inv_campo_pg_{aid}", 0)
        _n = st.text_area(t("What is wrong with it?"), key=f"inv_campo_prob_{aid}_{_gp}", height=80)
        if st.button(t(":material/send: Send to the office"), key=f"inv_campo_probbtn_{aid}",
                     disabled=not str(_n or "").strip()):
            ok, msg = INV.avisar_desde_campo(aid, grupo, usuario, "problem", _n)
            if ok:
                st.session_state[f"_inv_campo_pg_{aid}"] = _gp + 1
    if ok is not None:
        (flash.exito if ok else st.error)(msg)
        if ok:
            st.rerun()


# ── Registro de un activo ────────────────────────────────────────
def _registro(grupo):
    if st.button(t(":material/arrow_back: Cancel"), key="inv_new_back"):
        st.session_state.pop("_inv_nuevo", None)
        st.session_state.pop("_inv_dupde", None)
        st.rerun()
    st.markdown(t("## :material/add_circle: Register asset"))

    # Foto fuera del form (uploader se procesa al enviar)
    _foto = st.file_uploader(t("Photo (optional)"), type=["png", "jpg", "jpeg"], key="inv_foto")

    # ⚠️ v599 · formulario por GENERACIÓN y SIN enviar con Enter: un Enter lo mandaba a medias y
    # dos envíos crearon ACT-0001 y ACT-0002 en un segundo, iguales (visto en producción).
    _g = st.session_state.get("_inv_reg_gen", 0)
    _dup = st.session_state.get("_inv_dupde") or {}
    with st.form(f"inv_reg_{_g}", enter_to_submit=False):
        c1, c2 = st.columns(2)
        nombre = c1.text_input(t("Asset name *"), key=f"inv_reg_nom_{_g}")
        # v691 · sin preselección (ciclo 5, H8: nacía con «Consumable»)
        categoria = c2.selectbox(t("Category *"), INV.categorias(grupo), format_func=_etq,
                                 key=f"inv_reg_cat_{_g}", index=None, placeholder=t("— choose the category —"))
        marca = c1.text_input(t("Brand"), key=f"inv_reg_mar_{_g}")
        modelo = c2.text_input(t("Model"), key=f"inv_reg_mod_{_g}")
        serie = c1.text_input(t("Serial no."), key=f"inv_reg_ser_{_g}")
        condicion = c2.selectbox(t("Condition"), INV.CONDICIONES, format_func=_etq,
                                 key=f"inv_reg_con_{_g}")
        # v599 · nace en el almacén o en reparación (a una obra se va con la salida)
        ubic_t = c1.selectbox(t("Location (type)"), INV.UBIC_TIPOS_ALTA, format_func=_etq,
                              key=f"inv_reg_ut_{_g}",
                              help=t("To send it to a job or hand it to someone, register it and use «Check out»."))
        ubic_r = c2.text_input(t("Location (detail)"), help=t("Store or workshop."),
                               key=f"inv_reg_ur_{_g}")
        vc = c1.number_input(t("Purchase value"), min_value=0.0, step=10.0, key=f"inv_reg_vc_{_g}")
        vida = c2.number_input(t("Useful life (years)"), min_value=0.0, step=1.0, format="%g",   # v667
                               help=t("Used for depreciation. 0 = do not depreciate."),
                               key=f"inv_reg_vida_{_g}")
        c3, c4 = st.columns(2)
        with c3:
            f_compra = _fecha_input(t("Purchase date"), "", f"inv_reg_fc_{_g}")
        with c4:
            prox = _fecha_input(t("Next maintenance"), "", f"inv_reg_pm_{_g}")
        nota = st.text_area(t("Note"), height=70, key=f"inv_reg_nota_{_g}")
        if _dup:
            st.warning(t(":material/warning: There is already an asset with that name or serial: {x}. "
                         "If it is a different one, tick the box and register again.",
                         x=_dup.get("dups", "")))
            st.checkbox(t("Register it even though it is repeated"),
                        key=_k_dup(_dup.get("nombre", ""), _dup.get("serie", "")))
        crear = st.form_submit_button(t(":material/add: Register"), type="primary")

    if crear:
        if not str(nombre).strip():
            st.error(t("The name is required."))
            return
        if not categoria:                            # v691 · H8
            st.error(t("Choose the category."))
            return
        _dups = INV.homonimos(grupo, nombre, serie)
        if _dups and not st.session_state.get(_k_dup(nombre, serie)):
            st.session_state["_inv_dupde"] = {
                "nombre": nombre, "serie": serie,
                "dups": ", ".join(f"{d.get('ID', '')} «{d.get('Name', '')}»" for d in _dups[:3])}
            st.rerun()
        foto_id, _sin_foto = "", False
        if _foto is not None:
            try:
                foto_id = _subir_foto(_foto)
            except Exception as e:
                # ⚠️ v323: era un `pass` mudo. El activo se creaba igual (correcto,
                # la foto es accesoria) pero el usuario ADJUNTÓ una foto y se le
                # decía que todo fue bien: creía tenerla guardada y no estaba.
                logger.warning("inventory_ui: la foto del activo no subió a Drive: %s", e)
                _sin_foto = True
        ok, res = INV.create_activo(
            grupo=grupo, nombre=nombre, categoria=categoria, marca=marca, modelo=modelo,
            serie=serie, foto_id=foto_id, fecha_compra=f_compra, valor_compra=vc,
            vida_util=vida, condicion=condicion, ubicacion_tipo=ubic_t, ubicacion_ref=ubic_r,
            proximo_mant=prox, nota=nota, creado_por=_creado_por())
        if ok:
            st.session_state["_inv_reg_gen"] = _g + 1
            st.session_state.pop("_inv_dupde", None)
            st.session_state.pop("_inv_nuevo", None)
            st.session_state["_inv_open"] = res
            # v599 · con mensaje (no decía nada)
            flash.exito(t("Asset {id} «{n}» registered.", id=res, n=str(nombre).strip()))
            if _sin_foto:
                # (encolado aquí, delante de SU `st.rerun()`: si el alta falla no queda colgado — v570)
                flash.aviso(t(":material/warning: The asset is registered, but **the photo could not be uploaded** to Drive. Add it later from its record."))
            st.rerun()
        else:
            st.error(res)


# ── Informes y categorías ────────────────────────────────────────
def _reportes(grupo):
    rep = INV.reporte_valor(grupo)
    if not rep["por_categoria"]:
        return
    from core import projects_ui as _PU
    _g = st.session_state.get("_inv_rep_gen", 0)
    _abre = _g > 0                  # la cifra del valor los ABRE (la condición va en la clave, v547)
    with st.container(key="cpx_inv_rep"):           # v599 · destino de la cifra del valor
        _PU._bajar_a("cpx_inv_rep", "_bajar_cpx_inv_rep", bloque="start")
        # ⚠️ v599 · A ANCHO COMPLETO, una debajo de otra: en dos columnas las cifras salían
        # cortadas sin aviso («$4» por $419) y la columna «Current» ni se veía. Y la ubicación
        # traducida (salía «project»/«warehouse» en bruto).
        with st.expander(t(":material/insights: Value reports"), key=f"exp_inv_rep_{_abre}_{_g}",
                         expanded=_abre):
            # ⚠️ v600 · ACTIVAS: un toque en una fila lleva a la lista con ese filtro (eran cifras
            # mudas). Por callback, que corre ANTES de pintar los filtros de arriba.
            _sg = st.session_state.get("_inv_rep_sel_gen", 0)
            _cats = [k for k, _v in sorted(rep["por_categoria"].items())]
            _ubis = [k for k, _v in sorted(rep["por_ubicacion"].items())]
            st.caption(t("Tap a row to see those assets in the list."))
            st.markdown(t("**By category**"))
            st.dataframe(pd.DataFrame([{
                "Category": _etq(k), "Active": v["n"],
                "Compra": round(v["compra"], 0), "Actual": round(v["actual"], 0),
            } for k, v in sorted(rep["por_categoria"].items())]),
                width="stretch", hide_index=True, key=f"inv_rep_cat_{_sg}",
                on_select=functools.partial(_tocar_informe, f"inv_rep_cat_{_sg}", _cats, "categoria"),
                selection_mode="single-cell",
                column_config=tabla.cfg(None, {"Compra": st.column_config.NumberColumn(t("Purchase"), format="$%,d"),
                               "Actual": st.column_config.NumberColumn(t("Current"), format="$%,d")}))
            st.markdown(t("**By location**"))
            st.dataframe(pd.DataFrame([{
                "Location": _etq(k), "Active": v["n"], "Valor actual": round(v["actual"], 0),
            } for k, v in sorted(rep["por_ubicacion"].items())]),
                width="stretch", hide_index=True, key=f"inv_rep_ubi_{_sg}",
                on_select=functools.partial(_tocar_informe, f"inv_rep_ubi_{_sg}", _ubis, "ubicacion"),
                selection_mode="single-cell",
                column_config=tabla.cfg(None, {"Valor actual": st.column_config.NumberColumn(t("Current value"), format="$%,d")}))


def _tocar_informe(clave, filas, campo):
    """v600 · Callback de una fila de los informes: a la lista con ese filtro (y la tabla nace
    sin selección: otra generación, así el MISMO toque vuelve a funcionar)."""
    _sel = (st.session_state.get(clave) or {}).get("selection") or {}
    _cel = list(_sel.get("cells") or []) or [[r] for r in (_sel.get("rows") or [])]
    st.session_state["_inv_rep_sel_gen"] = st.session_state.get("_inv_rep_sel_gen", 0) + 1
    if not _cel or not (0 <= int(_cel[0][0]) < len(filas)):
        return
    _v = filas[int(_cel[0][0])]
    if campo == "categoria":
        _filtrar(categoria=_v if _v != "—" else "Todas")
    else:
        _filtrar(ubicacion=_v if _v in INV.UBIC_TIPOS else "Todas")


def _tocar_categoria(clave):
    """v600 · Callback de un nombre de categoría: a la lista filtrada por ella."""
    _v = st.session_state.get(clave)
    st.session_state["_inv_cat_pill_gen"] = st.session_state.get("_inv_cat_pill_gen", 0) + 1
    if _v:
        _filtrar(categoria=_v)


def _categorias_expander(grupo):
    with st.expander(t(":material/category: Categories"), key="exp_inv_cats"):
        st.caption(t("The default ones are always there; here you add/remove your own. "
                     "Tap one to see its assets in the list."))
        # ⚠️ v600 · ACTIVAS: cada categoría lleva a la lista filtrada por ella (era una línea de texto)
        _pg = st.session_state.get("_inv_cat_pill_gen", 0)
        st.pills(t("Categories"), INV.categorias(grupo), format_func=_etq, key=f"inv_cat_pills_{_pg}",
                 on_change=_tocar_categoria, args=(f"inv_cat_pills_{_pg}",),
                 label_visibility="collapsed")
        # v599 · el campo se VACÍA tras añadir (se quedaba con lo escrito); se asigna antes de
        # pintarlo, que es cuando Streamlit lo admite (trampa 31: vaciar es ASIGNAR)
        if st.session_state.pop("_inv_cat_limpiar", False):
            st.session_state["inv_cat_new"] = ""
        cc = st.columns([3, 1])
        _nueva = cc[0].text_input(t("New category"), key="inv_cat_new",
                                  label_visibility="collapsed", placeholder=t("New category…"))
        if cc[1].button(t(":material/add: Add"), key="inv_cat_add"):
            ok, msg = INV.add_categoria(grupo, _nueva)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.session_state["_inv_cat_limpiar"] = True
                st.rerun()
        # v599 · solo las PROPIAS: ofrecía las de fábrica y al quitarlas respondía «Not found…»
        _propias = INV.categorias_propias(grupo)
        if not _propias:
            st.caption(t("You have not added any category of your own yet."))
            return
        _quitar = st.selectbox(t("Remove one of your categories"), ["—"] + _propias,
                               key="inv_cat_del")
        _uso, _dest = [], None
        if _quitar != "—":
            # ⚠️ v691 · ciclo 5, H14: se quitaba en uso sin avisar y el filtro dejaba de ofrecerla
            _uso = INV.en_uso_categoria(grupo, _quitar)
            if _uso:
                st.warning(t(":material/warning: {n} asset(s) use «{c}»: choose the category to move them to.",
                             n=len(_uso), c=_etq(_quitar)))
                _dest = st.selectbox(t("Move them to"), [c for c in INV.categorias(grupo) if c != _quitar],
                                     index=None, format_func=_etq, placeholder=t("— choose the category —"),
                                     key="inv_cat_dest")
        if _quitar != "—" and st.button(t(":material/delete: Remove"), key="inv_cat_delbtn",
                                         disabled=bool(_uso) and not _dest):
            ok, msg = INV.del_categoria(grupo, _quitar, mover_a=_dest or "")
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()
