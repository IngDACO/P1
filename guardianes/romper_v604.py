# -*- coding: utf-8 -*-
"""Bateria de roturas de v604 (Library, probada). ⚠️ Verde de BASE primero (v459) y NO en
paralelo con la suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ Las marcadas devuelven lo medido en producción con las 750 piezas reales del usuario.
⚠️ Anclas en LÍNEA y literales: check_anclas_roturas no lee variables (v570).
`--anclas` solo comprueba que cada ancla casa UNA vez; un argumento suelto filtra roturas.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v604"
LB = "core/library.py"
LU = "core/library_ui.py"
DS = "core/drive_store.py"
TOPE_S = 480


def corre(g=G):
    """True = verde, False = rojo, None = COLGADO (supero el tope)."""
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                           cwd=RAIZ, capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


ROTURAS = [
    # ── el motor ──
    ("«todos los documentos» vuelve a incluir las fotos", LB,
     [('            if str(r.get("Type", "")).strip() == "photo":\n                continue\n',
       '            pass\n')]),
    ("⚠️ las páginas se numeran al revés (30/30 la primera)", LB,
     [('            for n, lid in enumerate(sorted(ids, key=_orden_id), start=1):\n',
       '            for n, lid in enumerate(sorted(ids, key=_orden_id, reverse=True), start=1):\n')]),
    ("una pieza de título único también lleva número", LB,
     [('        if len(ids) > 1:\n', '        if len(ids) > 0:\n')]),
    # ── Drive ──
    ("⚠️ la descarga vuelve sin tiempo máximo (colgaba la página)", DS,
     [('    r = requests.get(f"{_API}/{file_id}", headers=_headers(), params={"alt": "media"}, timeout=_T)\n',
       '    r = requests.get(f"{_API}/{file_id}", headers=_headers(), params={"alt": "media"})\n')]),
    ("⚠️ el borrado vuelve a decir que sí aunque falle (403)", DS,
     [('        if r.status_code in (200, 204, 404):\n            return True\n', '        return True\n')]),
    ("⚠️ las miniaturas vuelven a bajarse una detrás de otra", DS,
     [('        with ThreadPoolExecutor(max_workers=min(8, len(faltan))) as ex:\n',
       '        with ThreadPoolExecutor(max_workers=1) as ex:\n')]),
    ("⚠️ la miniatura sale tumbada (sin aplicar el EXIF)", DS,
     [('        im = ImageOps.exif_transpose(im).convert("RGB")\n', '        im = im.convert("RGB")\n')]),
    ("la miniatura deja de ser cuadrada", DS,
     [('        im = ImageOps.fit(im, (lado, lado), Image.LANCZOS)\n',
       '        im = im.resize((lado, max(1, int(lado * im.height / im.width))))\n')]),
    ("las ya hechas se vuelven a bajar (sin caché)", DS,
     [('        out = {i: alm["datos"][i] for i in ids if i in alm["datos"]}\n', '        out = {}\n')]),
    ("una miniatura que falla tumba todas", DS,
     [('                    logger.warning("drive_store: miniatura no disponible: %s", e)\n                    continue\n',
       '                    raise\n')]),
    # ── las cifras y los filtros ──
    ("⚠️ las cifras vuelven a ser mudas", LU,
     [('                        on_click=_cifra, args=(_s,))\n', '                        )\n')]),
    ("«Documents» deja de bajar a su tabla", LU,
     [('        st.session_state["lib_tipo"] = LIB.DOCUMENTOS\n        st.session_state["_bajar_lib_docs"] = True\n',
       '        st.session_state["lib_tipo"] = LIB.DOCUMENTOS\n')]),
    ("«Items» deja de devolverlo todo", LU,
     [('    if s == "tot":\n        _ver_todo()\n', '    if s == "tot":\n        pass\n')]),
    ("⚠️ las secciones pierden su número", LU,
     [('                        format_func=lambda s: "%s · %d" % (t(s), _n.get(s, 0))) or ""\n',
       '                        format_func=lambda s: t(s)) or ""\n')]),
    ("⚠️ la búsqueda vuelve a perderse al abrir una pieza", LU,
     [('    q = c1.text_input(t("Search"), key="lib_q", label_visibility="collapsed",\n'
       '                      persist_state="session",\n',
       '    q = c1.text_input(t("Search"), key="lib_q", label_visibility="collapsed",\n')]),
    # (sin roturas para «un valor recordado que ya no vale»: lo suelta Streamlit solo — la 1ª
    # tanda las vio ESCAPAR y las guardas propias, de más, se quitaron)
    ("⚠️ otra búsqueda deja la galería en la página de antes", LU,
     [('        st.session_state["_lib_pag"] = 0\n', '        pass\n')]),
    # ── la galería ──
    ("«Next» vuelve a dejar la vista en los botones", LU,
     [('    st.session_state["_bajar_lib_gal"] = True     # v604 · al PRINCIPIO de la página nueva\n', '')]),
    ("⚠️ en el móvil la galería vuelve a apilarse (una por fila)", LU,
     [(""".st-key-lib_gal [data-testid='stHorizontalBlock']{flex-wrap:nowrap!important;gap:0.5rem!important}""",
       """.st-key-lib_gal [data-testid='stHorizontalBlock']{gap:0.5rem!important}""")]),
    ("⚠️ la foto deja de tocarse (el botón ya no va encima)", LU,
     [(""".st-key-lib_gal [class*='st-key-libfoto_']{position:absolute!important;inset:0;z-index:2;""",
       """.st-key-lib_gal [class*='st-key-libfoto_']{z-index:2;""")]),
    ("⚠️ la galería vuelve a bajar la foto ENTERA, una a una", LU,
     [('                _minis = dr.miniaturas([str(i.get("DriveID", "")).strip() for i in _vis])\n',
       '                _minis = {str(i.get("DriveID", "")).strip(): dr.download(str(i.get("DriveID", "")).strip())\n'
       '                          for i in _vis}\n')]),
    # ── la ficha ──
    ("⚠️ la ficha pierde «Previous / Next»", LU,
     [('    if lid in _nav and len(_nav) > 1:\n', '    if False:\n')]),
    ("volver deja la galería en otra página", LU,
     [('        st.session_state["_lib_pag"] = nav.index(lid) // _POR_PAGINA\n', '')]),
    ("⚠️ los documentos vuelven a abrirse SIN imagen", LU,
     [('    if _bytes and _es_imagen(it):\n', '    if _bytes and str(it.get("Type", "")) == "photo":\n')]),
    ("«Download» vuelve debajo de la imagen", LU,
     [('            # v604 · ARRIBA: una foto vertical (646 px) dejaba el botón bajo la pantalla\n',
       '            st.image(_bytes, width="stretch")\n')]),
    ("la nota vuelve a reinterpretarse como markdown", LU,
     [('        st.markdown(maps.literal_md(str(it.get("Notes", "")).strip()).replace("\\n", "  \\n"))\n',
       '        st.markdown(str(it.get("Notes", "")).strip())\n')]),
    ("⚠️ la fecha de la tabla vuelve al ISO", LU,
     [('            "Date": dmy(str(it.get("Date", ""))[:10]),\n',
       '            "Date": str(it.get("Date", ""))[:10],\n')]),
    ("el tipo vuelve en minúsculas («manual»)", LU,
     [('    return s[:1].upper() + s[1:]\n', '    return s\n')]),
    ("⚠️ los títulos repetidos vuelven sin su página", LU,
     [('    return "%s (%d/%d)" % (base, nm[0], nm[1]) if nm else base\n', '    return base\n')]),
    ("la columna Model vuelve aunque no haya ninguno", LU,
     [('            **({"Model": str(it.get("Model", "")) or "—"} if _con_modelo else {}),\n',
       '            "Model": str(it.get("Model", "")) or "—",\n')]),
    ("los plurales vuelven a «(s)» (siempre la forma de varios)", LU,
     [('    return t(uno, n=n) if n == 1 else t(varios, n=n)\n', '    return t(varios, n=n)\n')]),
    # ── el propietario ──
    ("⚠️ el alta vuelve a enviarse con Enter", LU,
     [('        with st.form(f"lib_up_{_g}", enter_to_submit=False):\n',
       '        with st.form(f"lib_up_{_g}"):\n')]),
    ("⚠️ el alta vuelve a quedarse llena (un 2º clic la repite)", LU,
     [('        st.session_state["_lib_up_gen"] = st.session_state.get("_lib_up_gen", 0) + 1\n', '')]),
    ("lo archivado deja de abrirse", LU,
     [('        _abrir(msg, [msg], "docs")             # v604 · y se ABRE lo archivado\n', '')]),
    ("⚠️ se borra la ficha aunque Drive no borre el archivo", LU,
     [('                if _did and dr is not None and not dr.delete(_did):\n',
       '                if _did and dr is not None and not (dr.delete(_did) or True):\n')]),
    ("el catálogo vuelve a quedarse con lo tecleado", LU,
     [('                    st.session_state["_lib_cat_gen"] = _g + 1\n', '')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           LU, [('_POR_PAGINA = 12         # ⚠️ cada miniatura es una descarga de Drive (v147) — reducida desde v604\n',
                 '_POR_PAGINA = 12         # ⚠️ cada miniatura es una descarga de Drive (v147) — reducida desde v604 (control)\n')])


def aplica(rel, cambios):
    """Aplica TODOS los cambios o ninguno. Devuelve (ok, bak, p, detalle)."""
    p = os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep)))
    bak = io.open(p, encoding="utf-8", newline="").read()
    txt = bak
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    _filtro = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--anclas" in sys.argv:
        _m = 0
        for r in ROTURAS + [CONTROL]:
            desc, rel, cambios = r[:3]
            txt = io.open(os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep))),
                          encoding="utf-8", newline="").read()
            for viejo, _ in cambios:
                if txt.count(viejo) != 1:
                    _m += 1
                    print("  x%d  %s  <- %s" % (txt.count(viejo), desc, viejo[:60]))
        print("anclas: %d mal de %d roturas" % (_m, len(ROTURAS) + 1))
        sys.exit(1 if _m else 0)

    _rot = [r for r in ROTURAS if not _filtro or any(f in r[0] for f in _filtro)]
    print("0. Verde de base")
    for _g in sorted({r[3] if len(r) > 3 else G for r in _rot} | {G}):
        _base = corre(_g)
        if not _base:
            print("   ⚠️ %s YA esta %s: la tanda saldria «cazada» sin probar nada"
                  % (_g, "COLGADO" if _base is None else "rojo"))
            sys.exit(1)
        print("   %s verde" % _g)

    print("")
    print("1. Roturas (cada una debe ponerse ROJA)")
    cazadas = total = 0
    saltadas, colgadas = [], []
    for r in _rot:
        desc, rel, cambios = r[:3]
        _g = r[3] if len(r) > 3 else G
        _ok, bak, p, det = aplica(rel, cambios)
        if _ok is None:
            print("  ??      ancla %s en %s -> %s" % (det, rel, desc))
            saltadas.append(desc)
            continue
        total += 1
        try:
            verde = corre(_g)
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE
        if verde is None:
            colgadas.append(desc)
            print("  COLGADA  %s" % desc)
            continue
        cazadas += (not verde)
        print("  %s %s%s" % ("CAZADA  " if not verde else "ESCAPADA", desc,
                             "" if _g == G else "  [%s]" % _g))

    print("")
    print("2. Control (debe seguir VERDE)")
    _d, _r, _c = CONTROL
    _ok, bak, p, det = aplica(_r, _c)
    control_ok = False
    if _ok is None:
        print("  ??      ancla del control %s" % det)
    else:
        try:
            control_ok = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)
        print("  %s %s" % ("ok     " if control_ok else "MAL    ", _d))

    print("")
    print("=== %d de %d roturas cazadas ===" % (cazadas, total))
    if saltadas:
        print("⚠️ %d rotura(s) NO se pudieron aplicar: la bateria no las ha probado"
              % len(saltadas))
    if colgadas:
        print("⚠️ %d rotura(s) COLGARON el guardian (tope %d s): no son detecciones"
              % (len(colgadas), TOPE_S))
    sys.exit(0 if cazadas == total and not saltadas and not colgadas and control_ok else 1)
