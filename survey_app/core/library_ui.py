"""📚 Technical library — fotos, manuales y fichas por MARCA · MODELO · SECCIÓN (v472).

Pantalla de CONSULTA para todos y de GESTIÓN para el propietario (decisión del
usuario: «solo el propietario sube»). Es una sección SIN sub-pestañas, así que su
título va aquí — `_sub_header` solo lo pinta cuando la sección tiene subs (v320).

⚠️ La descarga es LAZY, y no es un detalle de rendimiento: `st.download_button`
evalúa `data=` **al RENDERIZAR**, no al pulsar, así que un botón por ficha se bajaría
de Drive TODO el material en cada pasada. Es el fallo que costó v147, y aquí sería
peor: una biblioteca crece sin techo. Se elige la ficha y solo entonces se baja ESA.
Por lo mismo la galería va PAGINADA — y desde v604 con MINIATURAS (`drive_store.miniaturas`:
reducidas, en paralelo y guardadas), no con la foto entera.

v604 · el recorrido de Library (con las 750 piezas reales del usuario): los 218 documentos
—páginas de manual en JPEG— se abrían SIN imagen; 101 títulos repetidos sin decir qué página
es; 9,1 s al abrir y 4-6 s por página; en el móvil una foto por fila (los documentos a 4543
px); los filtros se perdían al abrir una pieza; el alta repetía. Ver HISTORIAL v604.
"""
import html as _h

import pandas as pd
import streamlit as st

from core import flash
from core import library as LIB
from core import maps
from core import tabla
from core import theme as T
from core.i18n import t, etiqueta as _etq
from core.num import dmy

_POR_PAGINA = 12         # ⚠️ cada miniatura es una descarga de Drive (v147) — reducida desde v604

_TIPOS_FILTRO = ["", "photo", LIB.DOCUMENTOS, "manual", "datasheet", "diagram", "other"]
_EXT_IMAGEN = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp")

# v604 · la galería: 3 por fila SIEMPRE (también en el móvil, donde Streamlit las apilaba una
# por fila: 6 fotos = 3600 px), miniaturas cuadradas iguales y la pieza ENTERA se toca — el
# botón «Open» va encima, transparente (medido en una mini-app: cubre la miniatura entera).
_CSS_GALERIA = (
    "<style>"
    ".st-key-lib_gal [data-testid='stHorizontalBlock']{flex-wrap:nowrap!important;gap:0.5rem!important}"
    ".st-key-lib_gal [data-testid='stHorizontalBlock']>[data-testid='stColumn']{min-width:0!important;"
    "flex:1 1 0!important;width:auto!important}"
    ".st-key-lib_gal [data-testid='stVerticalBlock']:has(> [data-testid='stHorizontalBlock'])"
    "{gap:1rem!important}"
    ".st-key-lib_gal [class*='st-key-libtile_']{position:relative;gap:0.25rem!important;border-radius:8px}"
    ".st-key-lib_gal [class*='st-key-libtile_']:hover{outline:2px solid #2e6da4;outline-offset:2px}"
    ".st-key-lib_gal [class*='st-key-libfoto_']{position:absolute!important;inset:0;z-index:2;"
    "margin:0!important;width:100%!important;height:100%!important}"
    ".st-key-lib_gal [class*='st-key-libfoto_'] [data-testid='stButton'],"
    ".st-key-lib_gal [class*='st-key-libfoto_'] button{width:100%!important;height:100%!important;opacity:0}"
    ".st-key-lib_gal img{border-radius:8px}"
    ".st-key-lib_gal .lib-ph{aspect-ratio:1/1;border-radius:8px;background:#eef1f5}"
    # v605 · la insignia «3/30», FUERA del flujo (su bloque ocupaba sitio y la subía 10 px)
    ".st-key-lib_gal [data-testid='stElementContainer']:has(.lib-pag){position:absolute!important;"
    "top:6px;left:6px;z-index:1;width:auto!important;pointer-events:none}"
    ".st-key-lib_gal .lib-pag{background:rgba(26,58,92,.85);color:#fff;font-size:12px;font-weight:600;"
    "padding:1px 7px;border-radius:10px}"
    ".st-key-lib_gal .lib-tt{font-size:13px;font-weight:600;line-height:1.25;display:-webkit-box;"
    "-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}"
    ".st-key-lib_gal .lib-ts{font-size:12px;color:#667080;white-space:nowrap;overflow:hidden;"
    "text-overflow:ellipsis}"
    "</style>")


# v605 · en estrecho (≤700 px de bloque) las 16 secciones, UNA fila que se desliza de lado: en el
# móvil ocupaban ~320 px y la galería empezaba a 958 (medido). La ELEGIDA va la primera
# (`aria-checked`, el contrato de accesibilidad del `st.pills`), para que no quede escondida.
_CSS_SECCIONES = (
    "<style>.st-key-lib_secs{container-type:inline-size}"
    "@container (max-width:700px){"
    ".st-key-lib_secs [data-testid='stButtonGroup']>div{flex-wrap:nowrap!important;"
    "overflow-x:auto!important;padding-bottom:6px}"
    ".st-key-lib_secs [data-testid='stButtonGroup'] button{flex:0 0 auto!important}"
    ".st-key-lib_secs [data-testid='stButtonGroup'] button[aria-checked='true']{order:-1}}</style>")


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


def _plural(n, uno, varios) -> str:
    return t(uno, n=n) if n == 1 else t(varios, n=n)


def _mayus(s) -> str:
    """«photo» → «Photo». Solo la PRESENTACIÓN: el texto sale de `etiqueta()` (una sola
    definición, i18n.VALORES — v463), y la hoja guarda el valor en minúsculas."""
    s = str(s or "")
    return s[:1].upper() + s[1:]


def _tipo(v) -> str:
    """v604 · cómo se LEE un tipo: salían «photo» / «manual» en la tabla, la ficha y el filtro.
    ⚠️ No en VALORES: «other» y «manual» son también datos de Inventory y del parte diario,
    y allí cambiarían de cara."""
    return _mayus(_etq(str(v or "")))


def _fecha(v) -> str:
    """«28/09/2026 17:56» (v604: salía «2026-09-28 17:56»; la regla de v584)."""
    s = str(v or "").strip()
    if not s:
        return "—"
    return (dmy(s[:10]) + (" " + s[11:16] if len(s) >= 16 else "")).strip()


def _pagina(it, pags) -> str:
    """«3/30» si la pieza comparte título con otras (si no, nada)."""
    nm = pags.get(str(it.get("ID", "")))
    return "%d/%d" % nm if nm else ""


def _titulo(it, pags) -> str:
    """El título y, si lo comparte con otras piezas, qué página es: «… — manual page (3/30)»."""
    base = str(it.get("Title", "")).strip()
    nm = pags.get(str(it.get("ID", "")))
    return "%s (%d/%d)" % (base, nm[0], nm[1]) if nm else base


def _es_imagen(it) -> bool:
    """⚠️ v604 · por el ARCHIVO, no por el tipo: los 218 «manual»/«diagram»/«other» de la
    biblioteca son JPEG (páginas fotografiadas) y se abrían sin imagen, solo con «Download»."""
    if str(it.get("MimeType", "")).lower().startswith("image/"):
        return True
    return str(it.get("FileName", "")).lower().endswith(_EXT_IMAGEN)


# ── acciones (en `on_click`: corren ANTES de la pasada, v561) ─────────────────
_FILTROS = ("lib_q", "lib_tipo", "lib_marca", "lib_modelo")


def _abrir(lid, nav, de=None):
    """Abre una pieza y recuerda la lista por la que se navega (las fotos o los documentos
    de los resultados de ahora, `de`), para su «Previous / Next» y para volver a su sitio."""
    st.session_state["_lib_open"] = str(lid)
    st.session_state["_lib_nav"] = [str(x) for x in nav]
    if de:
        st.session_state["_lib_nav_de"] = de


def _volver():
    """A la biblioteca, en la página de la galería donde está la foto que se miraba (con
    «Next» se puede haber ido más allá de la que se abrió) y bajando a ella."""
    lid = st.session_state.pop("_lib_open", None)
    nav = st.session_state.get("_lib_nav") or []
    if lid in nav and st.session_state.get("_lib_nav_de") == "fotos":
        st.session_state["_lib_pag"] = nav.index(lid) // _POR_PAGINA
        st.session_state["_bajar_lib_gal"] = True
    elif lid in nav:
        st.session_state["_bajar_lib_docs"] = True


def _ver_todo():
    for k in _FILTROS:
        st.session_state[k] = ""
    st.session_state["lib_seccion"] = None


def _cifra(s):
    """v604 · las cifras FILTRAN y BAJAN (eran HTML que no se tocaba)."""
    if s == "tot":
        _ver_todo()
        st.session_state["_bajar_cpx_lib_res"] = True
    elif s == "fot":
        st.session_state["lib_tipo"] = "photo"
        st.session_state["_bajar_lib_gal"] = True
    elif s == "doc":
        st.session_state["lib_tipo"] = LIB.DOCUMENTOS
        st.session_state["_bajar_lib_docs"] = True
    elif s == "sec":
        st.session_state["lib_seccion"] = None
        st.session_state["_bajar_lib_secs"] = True


def _ir_pagina(p):
    st.session_state["_lib_pag"] = p
    st.session_state["_bajar_lib_gal"] = True     # v604 · al PRINCIPIO de la página nueva


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

    from core import projects_ui as _PU
    r = LIB.resumen()
    _cifras(r)

    _q, _marca, _modelo, _tipo_f = _barra()
    base = LIB.buscar(_q, marca=_marca, modelo=_modelo, tipo=_tipo_f)
    _seccion = _secciones(base)
    items = [i for i in base if not _seccion or str(i.get("Section", "")) == _seccion]
    # ⚠️ v604 · otra búsqueda u otro filtro = la página 1: la galería se quedaba en la página
    # de ANTES («Page 2 of 89» de la biblioteca entera tras volver de «governor»).
    _firma = (_q, _tipo_f, _marca, _modelo, _seccion)
    if st.session_state.get("_lib_pag_firma") not in (None, _firma):
        st.session_state["_lib_pag"] = 0
    st.session_state["_lib_pag_firma"] = _firma
    pags = LIB.paginas()

    with st.container(key="cpx_lib_res"):
        _PU._bajar_a("cpx_lib_res", "_bajar_cpx_lib_res", bloque="start")
        if not items:
            _vacio(r)
        else:
            st.caption(_plural(len(items), "{n} item. Tap it to open it.",
                               "{n} items. Tap one to open it."))
            _fotos = [i for i in items if str(i.get("Type", "")) == "photo"]
            _resto = [i for i in items if str(i.get("Type", "")) != "photo"]
            if _fotos:
                _galeria(_fotos, pags, _PU)
            if _resto:
                _tabla(_resto, pags, _PU)

    if _puede_subir():
        st.markdown("---")
        _alta()
        _catalogo()
    else:
        st.caption(t("Only the owner adds material to the library. Ask them to file "
                     "anything worth keeping."))


def _cifras(r):
    """v604 · ACTIVAS: todo · las fotos · los documentos · las secciones. Sustituyen a
    «Brands 2 · Models 0» (datos del catálogo: la marca está en los filtros). Dos por fila en
    estrecho (a 859 px salían 3 + 1)."""
    _n_fot = int(r["por_tipo"].get("photo", 0))
    _K = [("tot", t("Items"), r["total"], t("photos, manuals and datasheets")),
          ("fot", t("Photos"), _n_fot, t("taken on site")),
          ("doc", t("Documents"), r["total"] - _n_fot, t("manuals, diagrams and other")),
          ("sec", t("Sections"), len(r["por_seccion"]), t("of the lift covered"))]
    st.markdown(T.dos_por_fila("cpx_lib_kpis"), unsafe_allow_html=True)
    with st.container(key="cpx_lib_kpis"):
        for _col, (_s, _l, _v, _pie) in zip(st.columns(4), _K):
            _col.button(f"{_l}\n\n{_v}\n\n{_pie}", key=f"cpxkpi_lib_{_s}", width="stretch",
                        on_click=_cifra, args=(_s,))


def _barra():
    """Buscador + la taxonomía. ⚠️ Los desplegables se ENCADENAN: los modelos salen
    de la marca elegida, así que no se puede pedir un par que no existe.
    ⚠️ v604 · RECORDADOS (`persist_state`): al abrir una pieza y volver se perdían («governor»
    → las 750)."""
    c1, c2 = st.columns([3, 2])
    q = c1.text_input(t("Search"), key="lib_q", label_visibility="collapsed",
                      persist_state="session",
                      placeholder=t("title, notes, brand, model, file name…"))
    tipo = c2.selectbox(t("Type"), _TIPOS_FILTRO, key="lib_tipo",
                        label_visibility="collapsed", persist_state="session",
                        format_func=lambda x: (t("All types") if not x else
                                               t("All documents") if x == LIB.DOCUMENTOS else
                                               _tipo(x)))

    c3, c4 = st.columns(2)
    _marcas = LIB.marcas()
    marca = c3.selectbox(t("Brand"), [""] + _marcas, key="lib_marca", persist_state="session",
                         format_func=lambda x: t(LIB.SIN_MARCA) if not x else x)
    # ⚠️ Sin marca no se ofrecen modelos: un modelo suelto no identifica nada (hay
    # códigos que se repiten entre fabricantes) y la lista sería inmanejable.
    _modelos = LIB.modelos_de(marca) if marca else []
    modelo = c4.selectbox(t("Model"), [""] + _modelos, key="lib_modelo",
                          disabled=not marca, persist_state="session",
                          format_func=lambda x: t(LIB.SIN_MODELO) if not x else x,
                          help=None if marca else t("Pick a brand first."))
    return q, marca, (modelo if marca else ""), tipo


def _secciones(base):
    """v604 · las secciones, PÍLDORAS con cuántas piezas hay en cada una con la búsqueda de
    ahora (era un desplegable mudo): «Car · 159» se toca y filtra.

    ⚠️ v606 · solo las que TIENEN piezas con la búsqueda y los filtros de ahora (y la elegida,
    aunque se quede en cero, para poder soltarla): con «Documents» salían «Controller · 0»,
    «Shaft · 0»… que en la fila del móvil solo estorbaban (visto verificando v605). Que las
    opciones cambien no rompe nada: un valor que ya no está, Streamlit lo suelta solo (v604)."""
    from core import projects_ui as _PU
    _n = {}
    for i in base:
        _n[str(i.get("Section", ""))] = _n.get(str(i.get("Section", "")), 0) + 1
    _elegida = st.session_state.get("lib_seccion")
    _ops = [s for s in LIB.SECCIONES if _n.get(s) or s == _elegida]
    if not _ops:
        return ""
    st.markdown(_CSS_SECCIONES, unsafe_allow_html=True)
    with st.container(key="lib_secs"):
        _PU._bajar_a("lib_secs", "_bajar_lib_secs", bloque="start")
        return st.pills(t("Section"), _ops, selection_mode="single", key="lib_seccion",
                        persist_state="session",
                        format_func=lambda s: "%s · %d" % (t(s), _n.get(s, 0))) or ""


def _vacio(r):
    """⚠️ Un «no hay resultados» tiene DOS causas y confundirlas manda a buscar donde
    no hay nada: la biblioteca puede estar vacía, o los filtros pueden estar de más."""
    if r["total"] == 0:
        st.info(t(":material/info: The library is empty. The owner files the first "
                  "material from this screen."))
    else:
        st.warning(_plural(r["total"], ":material/search_off: Nothing matches those filters. "
                                       "The library has {n} item in total.",
                           ":material/search_off: Nothing matches those filters. "
                           "The library has {n} items in total."))
        st.button(t(":material/filter_alt_off: Show all"), key="lib_ver_todo", on_click=_ver_todo)


def _etiqueta(it) -> str:
    _m = " · ".join(x for x in (str(it.get("Brand", "")).strip(),
                                str(it.get("Model", "")).strip()) if x)
    return _m or t("no brand")


def _galeria(fotos, pags, _PU):
    """Fotos en rejilla de miniaturas. ⚠️ PAGINADA a propósito (v147): cada miniatura es una
    descarga de Drive — reducida y guardada desde v604, pero la primera vez hay que bajarla."""
    with st.container(key="lib_gal"):
        _PU._bajar_a("lib_gal", "_bajar_lib_gal", bloque="start")
        # ⚠️ Sin `:material/…:`: `T.section` emite HTML y ahi el icono no se
        # interpreta — saldria el literal en pantalla (v443, y se vio en produccion).
        T.section(t("Photos"), _plural(len(fotos), "{n} photo", "{n} photos"))
        dr = _drive()
        if dr is None:
            st.caption(t("Drive is not connected: the photos are listed but cannot be shown."))
        _pag = int(st.session_state.get("_lib_pag", 0))
        _tot = max(1, (len(fotos) + _POR_PAGINA - 1) // _POR_PAGINA)
        _pag = max(0, min(_pag, _tot - 1))
        _vis = fotos[_pag * _POR_PAGINA:(_pag + 1) * _POR_PAGINA]
        _ids = [str(i.get("ID", "")) for i in fotos]
        _minis = {}
        if dr is not None:
            try:
                _minis = dr.miniaturas([str(i.get("DriveID", "")).strip() for i in _vis])
            except Exception:
                _minis = {}

        st.markdown(_CSS_GALERIA, unsafe_allow_html=True)
        for _f in range(0, len(_vis), 3):
            cols = st.columns(3)
            for _c, it in zip(cols, _vis[_f:_f + 3]):
                _lid = str(it.get("ID", ""))
                _mini = _minis.get(str(it.get("DriveID", "")).strip())
                with _c.container(key="libtile_%s" % _lid):
                    _pg = _pagina(it, pags)
                    if _pg:
                        # ⚠️ v605 · el número, una INSIGNIA sobre la foto: al final del título lo
                        # cortaba el límite de 2 líneas (en el móvil, 9 de 9 miniaturas)
                        st.markdown('<div class="lib-pag">%s</div>' % _pg, unsafe_allow_html=True)
                    if _mini:
                        st.image(_mini, width="stretch")
                    else:
                        st.markdown('<div class="lib-ph"></div>', unsafe_allow_html=True)
                    st.markdown('<div class="lib-tt">%s</div><div class="lib-ts">%s</div>' % (
                        _h.escape(str(it.get("Title", "")).strip()),
                        _h.escape("%s · %s" % (_etiqueta(it), t(str(it.get("Section", "")))))),
                        unsafe_allow_html=True)
                    # la pieza ENTERA se toca: el botón va encima, transparente (_CSS_GALERIA)
                    st.button(t("Open: {x}", x=_titulo(it, pags)), key="libfoto_%s" % _lid,
                              on_click=_abrir, args=(_lid, _ids, "fotos"))

        if _tot > 1:
            p1, p2, p3 = st.columns([1, 2, 1])
            p1.button(t(":material/chevron_left: Previous"), key="lib_prev",
                      disabled=_pag <= 0, width="stretch", on_click=_ir_pagina, args=(_pag - 1,))
            p2.caption(t("Page {a} of {b}", a=_pag + 1, b=_tot))
            p3.button(t(":material/chevron_right: Next"), key="lib_next",
                      disabled=_pag >= _tot - 1, width="stretch", on_click=_ir_pagina, args=(_pag + 1,))


def _tabla(items, pags, _PU):
    with st.container(key="lib_docs"):
        _PU._bajar_a("lib_docs", "_bajar_lib_docs", bloque="start")
        T.section(t("Documents"), _plural(len(items), "{n} item", "{n} items"))
        _con_modelo = any(str(it.get("Model", "")).strip() for it in items)
        _con_pagina = any(_pagina(it, pags) for it in items)
        df = pd.DataFrame([{
            # ⚠️ v605 · la página, su PROPIA columna y la primera: al final del título la cortaba
            # el ancho («… — installation ste…» sin su «(2/7)», medido en producción)
            **({"Page": _pagina(it, pags)} if _con_pagina else {}),
            "Title": str(it.get("Title", "")).strip(),
            "Brand": str(it.get("Brand", "")) or "—",
            **({"Model": str(it.get("Model", "")) or "—"} if _con_modelo else {}),
            "Section": t(str(it.get("Section", ""))),
            "Type": _mayus(_etq(str(it.get("Type", "")))),
            "Date": dmy(str(it.get("Date", ""))[:10]),
        } for it in items])
        # ⚠️ La clave lleva GENERACIÓN: soltar el estado del widget no llega al navegador
        # (trampa 31), y al volver la tabla reabriría la misma pieza.
        _gen = st.session_state.get("_lib_tbl_gen", 0)
        _ev = st.dataframe(df, width="stretch", hide_index=True,
                           # ⚠️ v598 · `single-cell`, como Files en v592: con `single-row` un toque
                           # en la celda solo la enmarcaba
                           on_select="rerun", selection_mode="single-cell", key="lib_tbl_%d" % _gen,
                           column_config=tabla.cfg(None, {
                               # v604 · más ancho: el título se cortaba donde se distingue
                               # (sin fijar: más ancho que el móvil, taparía las demás)
                               "Title": st.column_config.TextColumn(t("Title"), width=340),
                               "Page": st.column_config.TextColumn(t("Page"), width=56)}))
        _s = _ev.selection            # v598 · la fila de la CELDA tocada (o la de la casilla)
        _sr = [c[0] for c in (getattr(_s, "cells", None) or [])] or list(getattr(_s, "rows", None) or [])
        if _sr and _sr[0] < len(items):
            st.session_state["_lib_tbl_gen"] = _gen + 1
            _abrir(str(items[_sr[0]].get("ID", "")), [str(i.get("ID", "")) for i in items], "docs")
            st.rerun()


def _detalle(lid):
    st.button(t(":material/arrow_back: Back to the library"), key="lib_back", on_click=_volver)
    it = LIB.get_item(lid)
    if not it:
        st.error(t("That item is no longer in the library."))
        return
    pags = LIB.paginas()

    # v604 · «Previous / Next» por los resultados de donde se abrió («12 of 52»): para leer
    # un manual página a página había que volver a la lista cada vez.
    _nav = st.session_state.get("_lib_nav") or []
    if lid in _nav and len(_nav) > 1:
        _i = _nav.index(lid)
        a, b, c = st.columns([1, 2, 1])
        a.button(t(":material/chevron_left: Previous"), key="lib_it_prev", width="stretch",
                 disabled=_i <= 0, on_click=_abrir, args=(_nav[max(_i - 1, 0)], _nav))
        b.caption(t("{a} of {b}", a=_i + 1, b=len(_nav)))
        c.button(t(":material/chevron_right: Next"), key="lib_it_next", width="stretch",
                 disabled=_i >= len(_nav) - 1, on_click=_abrir,
                 args=(_nav[min(_i + 1, len(_nav) - 1)], _nav))

    st.markdown("### " + maps.literal_md(_titulo(it, pags)))
    st.markdown(" ".join([
        T.chip(_etiqueta(it)),
        T.chip(t(str(it.get("Section", ""))), T.VERDE),
        T.chip(_tipo(it.get("Type", ""))),
    ]), unsafe_allow_html=True)

    _did = str(it.get("DriveID", "")).strip()
    dr = _drive()
    _bytes = None
    if _did and dr is not None:
        try:
            _bytes = dr.download(_did)       # aquí SÍ: es UNA ficha, la que se eligió
        except Exception as e:
            st.error("%s: %s" % (t("Could not download the file"), e))
        if _bytes:
            # v604 · ARRIBA: una foto vertical (646 px) dejaba el botón bajo la pantalla
            st.download_button(t(":material/download: Download"), data=_bytes,
                               file_name=str(it.get("FileName", "")) or "file",
                               mime=str(it.get("MimeType", "")) or "application/octet-stream",
                               key="lib_dl")
    elif _did:
        st.caption(t("Drive is not connected: the file cannot be downloaded right now."))
    else:
        st.caption(t("This entry has no attached file — it is a note."))
    if _bytes and _es_imagen(it):
        st.image(_bytes, width="stretch")
    if str(it.get("Notes", "")).strip():
        # v604 · TAL CUAL (la nota la escribió una persona; el markdown la reinterpretaba)
        st.markdown(maps.literal_md(str(it.get("Notes", "")).strip()).replace("\n", "  \n"))
    st.caption(t("Filed by {who} on {when}",
                 who=str(it.get("UploadedBy", "")) or "—", when=_fecha(it.get("Date", ""))))

    if _puede_subir():
        with st.expander(t(":material/delete: Remove from the library"), key=f"exp_lib_del_{lid}"):
            _ok = st.checkbox(t("I confirm I want to remove it"), key="lib_del_ok")
            if st.button(t(":material/delete: Remove"), key="lib_del",
                         disabled=not _ok, type="primary"):
                # ⚠️ El archivo de Drive PRIMERO: al revés se pierde el DriveID con la
                # fila y el archivo queda huérfano, inalcanzable desde la app — que es
                # exactamente el error de orden de v456.
                # ⚠️ v604 · y si Drive NO lo borra, no se borra nada: `delete` se tragaba el
                # error y la app decía «Removed» con el archivo aún en Drive.
                if _did and dr is not None and not dr.delete(_did):
                    st.error(t("The file could not be deleted from Drive, so nothing was "
                               "removed. Try again in a moment."))
                    return
                ok, msg = LIB.delete_item(lid)
                if ok:
                    st.session_state.pop("_lib_open", None)
                    flash.exito(msg)
                    st.rerun()
                else:
                    st.error(msg)


# ── gestión (solo propietario) ───────────────────────────────────────────────
def _alta():
    # ⚠️ v604 · por GENERACIÓN y SIN enviar con Enter, como Inventory (v599) y Contacts (v602):
    # tras «File it» el formulario se quedaba lleno y un 2º clic creaba la ficha OTRA VEZ (y
    # volvía a subir el archivo a Drive); Enter en el título la mandaba a medias.
    _g = st.session_state.get("_lib_up_gen", 0)
    with st.expander(t(":material/add_circle: File new material"), key="exp_lib_alta"):
        _marcas = LIB.marcas()
        if not _marcas:
            st.info(t(":material/info: There are no brands yet. Add one in the "
                      "catalogue below before filing material."))
        # ⚠️ Marca y modelo van FUERA del `st.form`: dentro, los widgets no escriben
        # hasta el submit, así que el desplegable de modelos no podría reaccionar a la
        # marca elegida (misma razón que v127/v189/v306). Se QUEDAN tras guardar: lo
        # siguiente que se archiva suele ser de la misma marca.
        c1, c2 = st.columns(2)
        marca = c1.selectbox(t("Brand"), [""] + _marcas, key="lib_up_marca",
                             format_func=lambda x: t(LIB.SIN_MARCA) if not x else x)
        modelo = c2.selectbox(t("Model"), [""] + (LIB.modelos_de(marca) if marca else []),
                              key="lib_up_modelo", disabled=not marca,
                              format_func=lambda x: t(LIB.SIN_MODELO) if not x else x)

        with st.form(f"lib_up_{_g}", enter_to_submit=False):
            titulo = st.text_input(t("Title"), key=f"lib_up_tit_{_g}",
                                   placeholder=t("e.g. Controller board layout"))
            c3, c4 = st.columns(2)
            seccion = c3.selectbox(t("Section"), LIB.SECCIONES, key=f"lib_up_sec_{_g}",
                                   format_func=t)
            tipo = c4.selectbox(t("Type"), LIB.TIPOS, key=f"lib_up_tipo_{_g}", format_func=_tipo)
            notas = st.text_area(t("Notes (optional)"), height=80, key=f"lib_up_notas_{_g}",
                                 placeholder=t("what it shows, where it was taken, "
                                               "anything worth knowing later"))
            up = st.file_uploader(t("File (photo, PDF, datasheet…)"), key=f"lib_up_file_{_g}")
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
        st.session_state["_lib_up_gen"] = st.session_state.get("_lib_up_gen", 0) + 1
        flash.exito(t("Filed as {id}.", id=msg))
        _abrir(msg, [msg], "docs")             # v604 · y se ABRE lo archivado
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
    with st.expander(t(":material/sell: Brands and models"), key="exp_lib_cat"):
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

        # v604 · por GENERACIÓN y sin Enter: la marca añadida se quedaba escrita
        _g = st.session_state.get("_lib_cat_gen", 0)
        with st.form(f"lib_cat_new_{_g}", enter_to_submit=False):
            c1, c2 = st.columns(2)
            _mk = c1.text_input(t("Brand"), key=f"lib_cat_mk_{_g}", placeholder=t("e.g. Schindler"))
            # ⚠️ El modelo puede ir VACÍO a propósito: hay material de una marca sin
            # modelo concreto (un catálogo general), y exigirlo lo dejaría fuera.
            _md = c2.text_input(t("Model (optional)"), key=f"lib_cat_md_{_g}",
                                placeholder=t("e.g. 3300"))
            if st.form_submit_button(t(":material/add: Add to catalogue"),
                                     width="stretch"):
                ok, msg = LIB.add_modelo(_mk, _md)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.session_state["_lib_cat_gen"] = _g + 1
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
