# -*- coding: utf-8 -*-
"""Batería de roturas de v629. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v629"
TOPE_S = 240
L = "core/library.py"
U = "core/library_ui.py"
H = "core/home_ui.py"

ROTURAS = [
    # ── El buscador ──
    ("⚠️ el buscador vuelve a la frase exacta", L,
     [("        if all(w in heno for w in _ws):\n", "        if qn in heno:\n")]),
    ("⚠️ basta con ALGUNA palabra", L,
     [("        if all(w in heno for w in _ws):\n", "        if any(w in heno for w in _ws):\n")]),
    ("⚠️ el plural deja de encontrar el singular", L,
     [("""        elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"):\n            w = w[:-1]\n""", "")]),
    ("«glass» se convierte en «glas»", L,
     [("""        elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"):\n""", """        elif len(w) > 3 and w.endswith("s"):\n""")]),
    ("«boxes» se queda en «boxe»", L,
     [("""        if len(w) > 4 and w.endswith(("ches", "shes", "xes", "sses")):\n            w = w[:-2]\n        elif""", """        if""")]),
    ("una letra vuelve a filtrar", L,
     [("    if len(qn) < 2:                       # con una letra todo coincide y no informa\n        return base\n", "")]),
    # ── La pantalla ──
    ("⚠️ Model vuelve aunque no haya modelos", U,
     [("        cols = st.columns([3, 2, 2, 2] if _modelos else [3, 2, 2])\n", "        cols = st.columns([3, 2, 2, 2])\n"),
      ("        if _modelos:\n            modelo = cols[3].selectbox(", "        if True:\n            modelo = cols[3].selectbox(")]),
    ("⚠️ con modelos, Model no sale", U,
     [("""    _modelos = LIB.modelos_de(_ya) if _ya else []\n""", """    _modelos = []\n""")]),
    ("⚠️ el modelo se queda filtrando con otra marca", U,
     [("""        modelo = ""\n        if _modelos:\n""", """        modelo = st.session_state.get("lib_modelo") or ""\n        if _modelos:\n""")]),
    ("⚠️ desaparece el CSS de los filtros", U,
     [("    st.markdown(_CSS_FILTROS, unsafe_allow_html=True)\n", "")]),
    ("⚠️ los pies vuelven en estrecho", U,
     [("""    st.markdown(T.dos_por_fila("cpx_lib_kpis") + _CSS_CIFRAS, unsafe_allow_html=True)\n""", """    st.markdown(T.dos_por_fila("cpx_lib_kpis"), unsafe_allow_html=True)\n""")]),
    ("⚠️ «Previous/Next» se apilan otra vez", U,
     [("        st.markdown(_CSS_NAV, unsafe_allow_html=True)\n", "")]),
    ("⚠️ el zoom desaparece", U,
     [("    if _bytes and _es_imagen(it):\n        _foto(lid, _bytes)\n", """    if _bytes and _es_imagen(it):\n        st.image(_bytes, width="stretch")\n""")]),
    ("⚠️ 2× no amplía", U,
     [("""unsafe_allow_html=True)\n    with st.container(key="lib_foto"):\n""", """unsafe_allow_html=True) if False else None\n    with st.container(key="lib_foto"):\n""")]),
    ("⚠️ el zoom no llega al 300 %", U,
     [("""</style>" % (_f * 100),\n""", """</style>" % 200,\n""")]),
    ("⚠️ 1× también pinta el recuadro", U,
     [("    if _f > 1:\n        st.markdown(\n", "    if True:\n        st.markdown(\n")]),
    ("⚠️ el recuadro no se mueve con el dedo", U,
     [("overflow:auto!important;max-height:72vh;touch-action:pan-x pan-y;", "max-height:72vh;")]),
    ("⚠️ arranca en una esquina", U,
     [("""                "b.scrollLeft=(b.scrollWidth-b.clientWidth)/2;"\n""", "")]),
    ("⚠️ el script es el mismo en cada nivel: no se ejecutaría", U,
     [("""</script>" % (lid, _f))\n""", """</script>" % (lid, 2))\n""")]),
    ("⚠️ cada toque vuelve a bajar la foto", U,
     [("""    if _m and _m[0] == did:\n        return _m[1]\n""", "")]),
    ("⚠️ «Next» enseña la foto anterior", U,
     [("""    if _m and _m[0] == did:\n""", """    if _m:\n""")]),
    ("⚠️ al volver a la lista, la foto se queda en memoria", U,
     [("""    st.session_state.pop("_lib_foto_mem", None)\n""", "")]),
    ("⚠️ «Filed by» vuelve al campo", U,
     [("""    if _puede_subir():\n        # v629 · Solo a quien la gestiona""", """    if True:\n        # v629 · Solo a quien la gestiona""")]),
    # ── Atrás y el menú ──
    ("⚠️ atrás vuelve a salir de Library", H,
     [("""    if _foto_abierta():\n        from core import library_ui\n        library_ui._volver()\n        st.rerun()\n""", "")]),
    ("⚠️ sin historial, «←» sale apagado en la foto", H,
     [("""    return bool(st.session_state.get("_nav_hist")) or _foto_abierta()\n""", """    return bool(st.session_state.get("_nav_hist"))\n""")]),
    ("⚠️ fuera de Library, atrás gasta el toque", H,
     [("""    return bool(st.session_state.get("_lib_open")\n                and st.session_state.get("_admin_sec") == "biblioteca")\n""",
       """    return bool(st.session_state.get("_lib_open"))\n""")]),
    ("⚠️ el menú deja de cerrar la foto", H,
     [("""                if _k == "biblioteca" and st.session_state.get("_lib_open"):\n""", """                if False:\n""")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", L,
           [("# con una letra todo coincide y no informa", "# (control) con una letra todo coincide y no informa")])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        return None


def aplica(rel, cambios):
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    bak = io.open(p, encoding="utf-8", newline="").read()
    txt = bak.replace("\r\n", "\n")
    for a, b in cambios:
        if txt.count(a) != 1:
            return False, bak, p, "ancla x%d: %s" % (txt.count(a), a[:60])
        txt = txt.replace(a, b)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    if corre() is not True:
        print("⚠️ el guardian YA esta rojo: la tanda saldria «cazada» sin probar nada")
        sys.exit(1)
    cazadas, malas = 0, []
    for desc, rel, cambios in ROTURAS:
        ok, bak, p, msg = aplica(rel, cambios)
        if not ok:
            print("  ESCAPA %s (%s)" % (desc, msg))
            malas.append(desc)
            continue
        try:
            r = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)
        if r is False:
            cazadas += 1
            print("  ok    cazada: %s" % desc)
        else:
            print("  ESCAPA %s (%s)" % (desc, "COLGADA" if r is None else "verde"))
            malas.append(desc)
    desc, rel, cambios = CONTROL
    ok, bak, p, msg = aplica(rel, cambios)
    try:
        r = corre() if ok else None
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok   " if r is True else "ESCAPA", desc))
    if r is not True:
        malas.append(desc)
    if corre() is not True:
        print("⚠️ el guardian NO vuelve a verde tras restaurar")
        malas.append("restaurar")
    print("=== %d de %d roturas cazadas ===" % (cazadas, len(ROTURAS)))
    sys.exit(1 if malas else 0)
