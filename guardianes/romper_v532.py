# -*- coding: utf-8 -*-
"""Bateria de roturas de v532. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ La primera rotura NO es una variante: devuelve un dibujo al codigo EXACTO de v531
(`components.html` con su import).
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v532"
INC = "core/incrustar.py"
BEL = "core/belting_ui.py"
COO = "core/session_cookie.py"
TOPE_S = 420

_BEL_NUEVO = ("    incrustar.dibujo('<!DOCTYPE html><html><body style=\"margin:0;background:transparent\">'\n"
              "        + svg + '</body></html>', 330)\n")
_BEL_VIEJO = ("    components.html(\n"
              "        '<!DOCTYPE html><html><body style=\"margin:0;background:transparent\">'\n"
              "        + svg + '</body></html>', height=330, scrolling=False)\n")


def corre(g=G):
    """True = verde, False = rojo, None = COLGADO (supero el tope)."""
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                           cwd=RAIZ, capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


ROTURAS = [
    ("⚠️ un dibujo vuelve al codigo EXACTO de v531 (`components.html`)",
     BEL, [(_BEL_NUEVO, _BEL_VIEJO),
           ("import streamlit as st\n\nfrom core.belting import",
            "import streamlit as st\nimport streamlit.components.v1 as components\n\n"
            "from core.belting import")]),

    ("⚠️ los dibujos dejan de recortar (saldrian barras de scroll)",
     INC, [("    if not scroll:\n", "    if False:\n")]),

    ("el estilo va DELANTE del DOCTYPE (el documento pasa a modo quirks)",
     INC, [('        _i = h.lower().find("<body")', "        _i = -1")]),

    # v535 · re-anclada: desde v535 los dibujos SÍ miden su contenido a propósito; lo que
    # vigila ahora es que un alto FIJO (cronómetros, plantas con scroll) se siga respetando.
    ("un alto fijo deja de respetarse (los cronometros y las plantas medirian su contenido)",
     INC, [('    return st.iframe(h, height="content" if ajustar else max(1, int(alto)))',
            '    return st.iframe(h, height="content")')]),

    ("`scroll=True` tambien recorta (la planta por pisos perderia su scroll)",
     INC, [("    if not scroll:\n", "    if True:\n")]),

    ("⚠️ el script a altura 0 (`st.iframe` lo rechaza: se caen cookie, «atras» y PWA)",
     INC, [("                     height=1)", "                     height=0)")]),

    ("⚠️ la cookie deja de ir por el recuadro (`window.parent` seria otro documento)",
     COO, [('        incrustar.script("<script>try{window.parent.document.cookie="',
            '        st.html("<script>try{window.parent.document.cookie="')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           INC, [('_SIN_SCROLL = "<style>html,body{overflow:hidden}</style>"',
                  '# comentario inocuo del control\n'
                  '_SIN_SCROLL = "<style>html,body{overflow:hidden}</style>"')])


def aplica(rel, cambios):
    """Aplica TODOS los cambios o ninguno. Devuelve (ok, bak, p, detalle)."""
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    bak = io.open(p, encoding="utf-8").read()
    txt = bak
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


print("0. Verde de base")
_base = corre()
if not _base:
    print("   ⚠️ el guardian YA esta %s: la tanda saldria «cazada» sin probar nada"
          % ("COLGADO" if _base is None else "rojo"))
    sys.exit(1)
print("   verde")

print("")
print("1. Roturas (cada una debe ponerse ROJA)")
cazadas = total = 0
saltadas, colgadas = [], []
for desc, rel, cambios in ROTURAS:
    _ok, bak, p, det = aplica(rel, cambios)
    if _ok is None:
        print("  ??      ancla %s en %s -> %s" % (det, rel, desc))
        saltadas.append(desc)
        continue
    total += 1
    try:
        verde = corre()
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE
    if verde is None:
        colgadas.append(desc)
        print("  COLGADA  %s" % desc)
        continue
    cazadas += (not verde)
    print("  %s %s" % ("CAZADA  " if not verde else "ESCAPADA", desc))

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
