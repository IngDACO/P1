# -*- coding: utf-8 -*-
"""v532 · LOS 22 USOS DE `st.components.v1.html` PASAN A `st.iframe` (vía `core/incrustar`).

Streamlit anuncia que quitará `st.components.v1.html` («will be removed after 2026-06-01»,
en los logs del Cloud). La app lo usaba en 22 sitios: 17 dibujos, 2 cronómetros del fichaje
y 3 scripts invisibles que actúan sobre la página (la cabecera de la PWA, el botón «atrás»
del móvil y la cookie del login persistente). En Streamlit 1.64 `st.iframe` genera el MISMO
elemento, con dos diferencias que `core/incrustar.py` neutraliza en un solo sitio: siempre
permite scroll (antes los dibujos se recortaban sin barra) y no admite altura 0.

Lo que protege:
  (a) ⚠️ ya no queda ni una llamada ni un import de `st.components.v1` en la app, y la sonda
      que lo busca SÍ encuentra uno cuando lo hay (trampa nº12);
  (b) los 3 scripts van por `incrustar.script` y siguen actuando sobre `window.parent`;
  (c) ⚠️ `dibujo` recorta sin barra como antes (inyecta `overflow:hidden` DENTRO del
      <body>, sin romper el `<!DOCTYPE>`), con la MISMA altura; `scroll=True` no toca nada;
  (d) `script` va a 1 px (no 0, que `st.iframe` rechaza), sin márgenes, con el JS intacto;
  (e) ⚠️ EJECUTANDO: los cronómetros, la trampa del «atrás» y la cookie pintan su recuadro
      con la altura de siempre; y el survey real pinta sus diagramas por `incrustar`.
"""
import ast
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
AQUI = os.path.dirname(os.path.abspath(__file__))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.path.insert(0, AQUI)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

fallos, n_ok = [], 0


def ok(q):
    global n_ok
    n_ok += 1
    print("  ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("  FALLO %s%s" % (q, ("  -> " + str(det)) if det != "" else ""))


def chk(q, cond, det=""):
    (ok(q) if cond else fallo(q, det))


def sec(x):
    print("\n%s" % x)


from streamlit.testing.v1 import AppTest                          # noqa: E402

FICHEROS = ["app.py"] + ["core/" + f for f in sorted(os.listdir(os.path.join(RAIZ, "core")))
                         if f.endswith(".py")]


def _viejos(src):
    """Llamadas a `components.html` / `st.components.v1.html` e imports de ese módulo."""
    out = []
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "html" \
                and "components" in ast.unparse(n.func.value):
            out.append(("llamada", n.lineno))
        if isinstance(n, ast.Import) and any(a.name.startswith("streamlit.components")
                                              for a in n.names):
            out.append(("import", n.lineno))
        if isinstance(n, ast.ImportFrom) and (n.module or "").startswith("streamlit.components"):
            out.append(("import", n.lineno))
    return out


def _nuevos(src, fn):
    return [n.lineno for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Call)
            and ast.unparse(n.func) == "incrustar." + fn]


# ═════════════════════════════════════════════════════════════════
sec("1. ⚠️ Ya no queda `st.components.v1` en la app")
_restos, _dib, _scr = {}, {}, {}
for f in FICHEROS:
    s = io.open(os.path.join(RAIZ, f), encoding="utf-8").read()
    if _viejos(s):
        _restos[f] = _viejos(s)
    if _nuevos(s, "dibujo"):
        _dib[f] = len(_nuevos(s, "dibujo"))
    if _nuevos(s, "script"):
        _scr[f] = len(_nuevos(s, "script"))
chk("ni una llamada ni un import de `st.components.v1` en %d ficheros" % len(FICHEROS),
    not _restos, _restos)
chk("la sonda SÍ encuentra una llamada y un import cuando los hay (trampa nº12)",
    len(_viejos("import streamlit.components.v1 as components\n"
                "components.html('<p>x</p>', height=10)\n")) == 2)
chk("los 19 dibujos y cronómetros van por `incrustar.dibujo`",
    sum(_dib.values()) == 19, _dib)
# v553 · un 4º, a propósito: llevar la vista a la ficha rápida recién abierta en el Panel
# (`roster_ui._ficha_rapida`, una vez por apertura). El inventario sigue siendo EXACTO: un
# script nuevo tiene que entrar aquí con su razón, no colarse.
chk("⚠️ los 4 scripts de página van por `incrustar.script` (cabecera PWA, «atrás», cookie, "
    "ir a la ficha del Panel)",
    _scr == {"app.py": 1, "core/home_ui.py": 1, "core/session_cookie.py": 1,
             "core/roster_ui.py": 1}, _scr)
for f in _scr:
    _s = io.open(os.path.join(RAIZ, f), encoding="utf-8").read()
    _args = [ast.unparse(n.args[0]) for n in ast.walk(ast.parse(_s)) if isinstance(n, ast.Call)
             and ast.unparse(n.func) == "incrustar.script"]
    chk("...%s sigue actuando sobre `window.parent` (la página de la app)" % f,
        all("window.parent" in a for a in _args), _args[:1])

# ═════════════════════════════════════════════════════════════════
sec("2. ⚠️ `incrustar`: mismo recuadro, misma altura, recortado como antes")
from core import incrustar                                         # noqa: E402

_LLAM = []
GUION_H = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
from core import incrustar
DOC = '<!DOCTYPE html><html><body style="margin:0;background:transparent"><svg></svg></body></html>'
incrustar.dibujo(DOC, 330)
incrustar.dibujo('<svg viewBox="0 0 10 10"></svg>', 500)
incrustar.dibujo(DOC, 800, scroll=True)
incrustar.dibujo(DOC, 0, ajustar=False)
incrustar.script("<script>window.parent.x=1;</script>")
''' % RAIZ
import streamlit as st                                             # noqa: E402
_orig_iframe = st.iframe


def _anota(src, **k):
    _LLAM.append((str(src), k.get("height")))
    return _orig_iframe(src, **k)


st.iframe = _anota
try:
    at = AppTest.from_string(GUION_H, default_timeout=60)
    at.run()
finally:
    st.iframe = _orig_iframe
chk("sin errores", not at.exception, [e.value for e in at.exception][:1])
_ifr = at.get("iframe")
chk("cinco recuadros pintados", len(_ifr) == 5 and len(_LLAM) == 5, (len(_ifr), len(_LLAM)))
if len(_LLAM) == 5 and len(_ifr) == 5:
    (d1, h1), (d2, h2), (d3, h3), (d4, h4), (d5, h5) = _LLAM
    chk("⚠️ documento con DOCTYPE: el estilo va DENTRO del <body>, el DOCTYPE sigue primero",
        d1.startswith("<!DOCTYPE html>") and
        '<body style="margin:0;background:transparent"><style>html,body{overflow:hidden}</style>'
        in d1, d1[:140])
    # ⚠️ v535 · Actualizada con su razón (v385): exigía la altura FIJA de siempre. Desde
    # v535 un dibujo mide lo que mide su contenido (`height="content"`): con alto fijo, en
    # pantalla estrecha quedaba un hueco en blanco debajo (medido en producción). El
    # principio que se afirma ahora: el dibujo NO lleva una altura inventada.
    chk("...y el recuadro mide lo que mide el dibujo (v535: `content`, no una altura fija)",
        h1 == "content", h1)
    chk("fragmento sin <body>: el estilo va delante (ya se pintaba sin doctype)",
        d2.startswith("<style>html,body{overflow:hidden}</style><svg"), d2[:80])
    chk("`scroll=True` deja el HTML intacto (la planta por pisos ya tenía scroll)",
        "overflow:hidden" not in d3 and h3 == 800, (d3[:60], h3))
    chk("una altura 0 (con alto fijo) no revienta: sale a 1 (st.iframe no admite 0)", h4 == 1, h4)
    chk("⚠️ el script: 1 px, sin márgenes y con el JS intacto",
        h5 == 1 and d5 == '<html><body style="margin:0"><script>window.parent.x=1;</script>'
                          '</body></html>', (h5, d5))
    chk("lo que llega al navegador es ese mismo HTML (`srcdoc` del proto)",
        [e.proto.srcdoc for e in _ifr] == [d for d, _h in _LLAM])

# ═════════════════════════════════════════════════════════════════
sec("3. ⚠️ EJECUTANDO: cronómetros, «atrás» y cookie")
_LLAM.clear()
GUION_R = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
from core import timeclock, timeclock_ui as TU, home_ui as HU, session_cookie as SC
timeclock.elapsed_seconds = lambda s: 3723
TU._chronometer("2026-09-30 08:00:00", key="c_grande")
TU._chrono_mini("2026-09-30 08:00:00", "On site", "#1e8449", key="c_mini")
HU._mobile_back_trap()
SC.save("campo000", "TOKEN-DE-PRUEBA")
''' % RAIZ
st.iframe = _anota
try:
    at = AppTest.from_string(GUION_R, default_timeout=60)
    at.run()
finally:
    st.iframe = _orig_iframe
chk("sin errores", not at.exception, [e.value for e in at.exception][:1])
chk("cuatro recuadros", len(_LLAM) == 4, [h for _d, h in _LLAM])
if len(_LLAM) == 4:
    (c1, a1), (c2, a2), (b, ab), (k, ak) = _LLAM
    chk("cronómetro grande: su altura de siempre (52) y recortado sin barra",
        a1 == 52 and "overflow:hidden" in c1 and "var e=3723" in c1, (a1, c1[:60]))
    chk("⚠️ cronómetro del sidebar: 44 y recortado — el más justo de todos: sin el estilo, "
        "`st.iframe` le pondría barra en cuanto el contenido pase de 44",
        a2 == 44 and "overflow:hidden" in c2, (a2, c2[:60]))
    chk("trampa del «atrás»: 1 px y el mismo JS sobre `window.parent`",
        ab == 1 and "P.__copexBack" in b and "window.parent" in b, (ab, b[:80]))
    chk("⚠️ cookie del login: 1 px y la MISMA escritura en `window.parent.document.cookie`",
        ak == 1 and "window.parent.document.cookie" in k and "campo000|TOKEN-DE-PRUEBA" in k
        and "max-age=" in k, (ak, k[:120]))

# ═════════════════════════════════════════════════════════════════
sec("4. ⚠️ EJECUTANDO: el survey real pinta sus diagramas por `incrustar`")
_LLAM.clear()
GUION_S = r'''
import sys
sys.path.insert(0, r"%s")
sys.path.insert(0, r"%s")
import pandas as pd
import streamlit as st
import fixture_survey as FX
from core import survey_ui as SU


def _prohibido(*a, **k):
    raise RuntimeError("ESCRITURA PROHIBIDA en esta prueba")


if not getattr(SU, "_prueba_v532", False):
    SU._prueba_v532 = True
    SU.generate_interpretation = lambda *a, **k: {"_ok": False}
    SU.generate_user_interpretation = lambda *a, **k: {"_ok": False}
    SU.send_usage_notification = lambda *a, **k: None
    SU.generate_report = lambda *a, **k: None
    SU.plan_ui.selector_proyecto = lambda *a, **k: (None, {})
    SU.toolruns.registrar = _prohibido
    SU.drive_store.upload = _prohibido
st.session_state.setdefault("auth", {"usuario": "dacox", "rol": "administrator",
                                     "grupo": "cliente1"})
SU.init_state()
if not st.session_state.get("_fx"):
    st.session_state["_fx"] = True
    for k, v in FX.PARAMS.items():
        if k in SU.PDF_PARAMS or k in SU.USER_ONLY:
            st.session_state["inp_%%s" %% k] = float(v)
    st.session_state["cfg_omega_side"] = FX.PARAMS["OMEGA_SIDE"]
    st.session_state["cfg_offset_side"] = FX.PARAMS["OFFSET_SIDE"]
    st.session_state["cfg_wall_yn"] = "N"
    st.session_state["ns"] = FX.PARAMS["NS"]
    st.session_state["survey_df"] = pd.DataFrame(
        [{c: r[c] for c in SU.SURVEY_COLS} for r in FX.MATRIZ])
SU.render_survey_tab("administrator", "cliente1")
''' % (RAIZ, AQUI)
st.iframe = _anota
try:
    at = AppTest.from_string(GUION_S, default_timeout=180)
    at.run()
    _b = next((x for x in at.button if "Calculate and see the results" in str(x.proto.label)),
              None)
    if _b is not None:
        _LLAM.clear()
        _b.click().run()
finally:
    st.iframe = _orig_iframe
chk("el survey calcula y pinta sin errores", _b is not None and not at.exception,
    [e.value for e in at.exception][:1])
_svg = [(d, h) for d, h in _LLAM if "<svg" in d]
chk("⚠️ los diagramas del survey salen por `incrustar` (%d con SVG)" % len(_svg),
    len(_svg) >= 3, [h for _d, h in _LLAM])
chk("...todos recortados sin barra, salvo la planta por pisos (que ya tenía scroll)",
    all("overflow:hidden" in d for d, h in _svg if "Piso" not in d and "floor" not in d.lower())
    and len([1 for d, h in _svg if "overflow:hidden" in d]) >= 2,
    [("overflow:hidden" in d, h) for d, h in _svg])
# ⚠️ v535 · Actualizada con su razón: era «con su altura de siempre (730)»; ahora todos los
# dibujos sin `scroll` miden su contenido, y la planta por pisos (con `scroll`) sigue fija.
chk("los dibujos del survey miden su contenido; solo la planta por pisos (con scroll) va fija",
    any(h == "content" for _d, h in _svg)
    and all(h == "content" for d, h in _svg if "overflow:hidden" in d),
    [h for _d, h in _svg])

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
