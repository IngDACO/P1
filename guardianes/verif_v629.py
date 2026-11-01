# -*- coding: utf-8 -*-
"""v629 · RECORRIDO DEL CAMPO: LIBRARY (02/11/2026, «Dale con todo»).

  (1) ⚠️ el buscador exigía la frase EXACTA: «buffer pit» 0 de 24, «rail bracket» 1 de 8, «sills» 0 de 17
      (medido con las 750 piezas reales) → todas las palabras, en cualquier orden y con singular o plural;
  (2) ⚠️ una foto no se podía ampliar: la pantalla completa la deja a 351 px de 1200 y la página del Cloud
      lleva `user-scalable=no` → 1× · 2× · 3× dentro de un recuadro, sin volver a bajarla;
  (3) ⚠️ atrás sacaba de Library (también el gesto del móvil, que usa ese botón) y el menú no hacía nada
      → con una foto abierta, atrás y el menú llevan a la lista;
  (4) ⚠️ al entrar no se veía ninguna foto (812 px en una pantalla de 812) → filtros más compactos y sin Model
      si no hay modelos; (5) «Previous/Next» en una fila; (6) «Filed by», solo a quien gestiona.
⚠️ Lo aprendido en v620: nada de estado preparado a mano. Sin red ni hoja real; Library no se escribe.
"""
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
from streamlit.testing.v1 import AppTest                          # noqa: E402

st.session_state["auth"] = {"usuario": "installer", "nombre": "i", "rol": "field", "grupo": "cliente1"}
from core import library as LIB                                   # noqa: E402

n_ok, fallos = 0, []


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("   ok   %s" % q)
    else:
        fallos.append(q)
        print("   FALLO %s%s" % (q, ("  -> " + str(det)) if det != "" else ""))


def sec(x):
    print("\n" + x)
    print("-" * 70)


def _btn(a, k):
    return next((b for b in a.button if b.key == k), None)


def _todo(a):
    return " | ".join(str(x.value) for k in ("markdown", "caption", "info", "warning", "error", "success")
                      for x in getattr(a, k, []))


def _src(rel):
    return io.open(os.path.join(RAIZ, "core", rel), encoding="utf-8").read()


sec("1. ⚠️ El buscador")
P = LIB._palabras
chk("singular: sills · brakes · buffers", P("sills brakes buffers") == ["sill", "brake", "buffer"], P("sills brakes buffers"))
chk("…boxes, brushes", P("boxes brushes") == ["box", "brush"], P("boxes brushes"))
chk("…lo que acaba en doble s o es corto no se toca", P("glass bus") == ["glass", "bus"], P("glass bus"))
PZ = [{"ID": "1", "Title": "Pit buffer and striker plate", "Notes": "", "Brand": "Schindler", "Model": "", "Section": "Pit", "FileName": "a.jpg"},
      {"ID": "2", "Title": "Counterweight guide shoe on the frame", "Notes": "", "Brand": "Schindler", "Model": "", "Section": "Counterweight", "FileName": "b.jpg"},
      {"ID": "3", "Title": "Rail fixing", "Notes": "Check the bracket torque", "Brand": "", "Model": "", "Section": "Guide rails & brackets", "FileName": "c.jpg"},
      {"ID": "4", "Title": "Door sill and lock", "Notes": "", "Brand": "Sematic", "Model": "", "Section": "Landing doors", "FileName": "IMG_0231.jpg"},
      {"ID": "5", "Title": "Buffers cut to length", "Notes": "", "Brand": "", "Model": "", "Section": "Pit", "FileName": "d.jpg"}]
LIB.list_items = lambda *a, **k: list(PZ)


def b(q):
    return [r["ID"] for r in LIB.buscar(q)]


chk("⚠️ en cualquier orden (daba 0)", b("buffer pit") == ["1", "5"] and b("shoe guide") == ["2"] and b("lock door") == ["4"], b("buffer pit"))
chk("⚠️ el plural encuentra el singular (daba 0)", b("sills") == ["4"], b("sills"))
chk("⚠️ …y el singular, el plural, como antes", b("buffer") == ["1", "5"], b("buffer"))
chk("⚠️ una palabra en el título y otra en las notas o la sección", b("rail bracket") == ["3"] and b("counterweight shoe") == ["2"], b("rail bracket"))
chk("⚠️ TODAS las palabras: no «alguna»", b("pit lock") == [], b("pit lock"))
chk("sin mayúsculas", b("BUFFER PIT") == ["1", "5"], b("BUFFER PIT"))
chk("el nombre de archivo sigue encontrándose", b("img_0231") == ["4"], b("img_0231"))
chk("una letra no filtra (como antes)", len(b("a")) == 5, b("a"))
chk("nada que casar: nada", b("zzz") == [], b("zzz"))

sec("2. La pantalla (AppTest, clics reales)")
G = r'''
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "x", "nombre": "x", "rol": st.session_state.get("_ROL", "field"), "grupo": "cliente1"})
from core import library as LIB, library_ui as UI, incrustar
_LL = st.session_state.setdefault("_LL", [])
incrustar.script = lambda html, *a, **k: _LL.append(html)
_I = [{"ID": "LIB-%03d" % i, "Title": "Pieza %d" % i, "Brand": "Schindler", "Model": "", "Type": "photo", "Section": "Pit", "Notes": "",
       "DriveID": "D%d" % i, "FileName": "f%d.jpg" % i, "MimeType": "image/jpeg", "UploadedBy": "COPEX library import",
       "Date": "2026-09-28 17:56"} for i in range(4)]
_I.append({**_I[0], "ID": "LIB-009", "Title": "Manual", "Type": "manual", "FileName": "m.pdf", "MimeType": "application/pdf", "DriveID": "D9"})
_D = st.session_state.setdefault("_DESC", [])
_PNG = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000" "1f15c4890000000d49444154789c6360000002000001"
                     "e221bc330000000049454e44ae426082")
class Dr:
    def miniaturas(self, ids): return {}
    def download(self, did):
        _D.append(did)
        return _PNG
LIB.is_configured = lambda: True
LIB.resumen = lambda: {"total": 5, "por_tipo": {"photo": 4, "manual": 1}, "por_seccion": {"Pit": 5}, "marcas": 2, "modelos": 0}
LIB.marcas = lambda *a: ["Schindler", "Sematic"]
LIB.modelos_de = lambda m, *a: (["3300"] if m == "Sematic" else [])
LIB.buscar = lambda q, marca="", modelo="", seccion="", tipo="": (st.session_state.__setitem__("_PIDE", (marca, modelo)) or list(_I))
LIB.paginas = lambda: {}
LIB.get_item = lambda lid: next((x for x in _I if x["ID"] == lid), {})
UI._drive = lambda: Dr()
UI.render_biblioteca()
'''


def ap(rol="field"):
    a = AppTest.from_string(G, default_timeout=60)
    a.session_state["_ROL"] = rol
    a.run()
    chk("   (sin excepción)", not a.exception, [e.value for e in a.exception][:1])
    return a


a = ap()
_k = [s.key for s in a.selectbox]
chk("⚠️ sin marca, sin Model: no se pinta un desplegable apagado", "lib_marca" in _k and "lib_modelo" not in _k, _k)
a.selectbox(key="lib_marca").select("Schindler").run()
chk("⚠️ una marca sin modelos, tampoco (las 750 reales)", "lib_modelo" not in [s.key for s in a.selectbox])
a.selectbox(key="lib_marca").select("Sematic").run()
chk("⚠️ con modelos, sale", not a.exception and "lib_modelo" in [s.key for s in a.selectbox], [s.key for s in a.selectbox])
a.selectbox(key="lib_modelo").select("3300").run()
chk("…y filtra", a.session_state["_PIDE"] == ("Sematic", "3300"), a.session_state["_PIDE"])
a.selectbox(key="lib_marca").select("Schindler").run()
chk("⚠️ un modelo de OTRA marca no se queda filtrando", not a.exception and a.session_state["_PIDE"] == ("Schindler", ""), a.session_state["_PIDE"])
_u = _src("library_ui.py")
chk("el CSS de los filtros y de las cifras, en estrecho", "_CSS_FILTROS, unsafe_allow_html" in _u and "+ _CSS_CIFRAS" in _u
    and "@container (max-width:700px){.st-key-cpx_lib_kpis button" in _u)

a = ap()
next(b_ for b_ in a.button if b_.key == "libfoto_LIB-001").click()
a.run()
chk("sin excepción al abrir", not a.exception, [e.value for e in a.exception][:1])
_v = _todo(a)
chk("⚠️ «Previous/Next» en su bloque de una fila", "_CSS_NAV, unsafe_allow_html" in _u and 'key="lib_nav"' in _u
    and _btn(a, "lib_it_prev") is not None and _btn(a, "lib_it_next") is not None)
chk("⚠️ «Filed by» no sale al campo", "Filed by" not in _v, _v)
_zc = a.button_group(key="lib_zoom") if hasattr(a, "button_group") else None
chk("⚠️ el zoom está, en 1×", _zc is not None and _zc.value in ("1×", ["1×"]), _zc)
chk("⚠️ la foto se baja UNA vez", a.session_state["_DESC"] == ["D1"], a.session_state["_DESC"])
a.run()
chk("⚠️ …y en cada toque no se vuelve a bajar", a.session_state["_DESC"] == ["D1"], a.session_state["_DESC"])
_btn(a, "lib_it_next").click()
a.run()
chk("«Next» baja la siguiente", a.session_state["_DESC"] == ["D1", "D2"], a.session_state["_DESC"])
chk("⚠️ …y solo guarda UNA, la de ahora", a.session_state["_lib_foto_mem"][0] == "D2", a.session_state["_lib_foto_mem"][0])
_btn(a, "lib_back").click()
a.run()
chk("⚠️ al volver a la lista, la foto se suelta", "_lib_foto_mem" not in a.session_state)

# El zoom, ejecutando `_foto` con cada nivel
GZ = r'''
import streamlit as st
from core import library_ui as UI, incrustar
_LL = st.session_state.setdefault("_LL", [])
incrustar.script = lambda html, *a, **k: _LL.append(html)
_PNG = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000" "1f15c4890000000d49444154789c6360000002000001"
                     "e221bc330000000049454e44ae426082")
st.session_state["lib_zoom"] = st.session_state.get("_Z", "1×")
UI._foto("LIB-001", _PNG)
'''


def zoom(z):
    a = AppTest.from_string(GZ, default_timeout=60)
    a.session_state["_Z"] = z
    a.run()
    chk("   (sin excepción)", not a.exception, [e.value for e in a.exception][:1])
    return " ".join(str(x.value) for x in a.markdown), a.session_state["_LL"]


_m, _l = zoom("1×")
chk("1×: tal cual, sin recuadro ni script", "st-key-lib_foto{" not in _m and _l == [], _m[:200])
_m, _l = zoom("2×")
chk("⚠️ 2×: la foto al 200 % dentro de un recuadro que se mueve con el dedo",
    "width:200%!important" in _m and "overflow:auto!important" in _m and "touch-action:pan-x pan-y" in _m, _m[:300])
chk("⚠️ …y arranca centrada", _l and "b.scrollLeft=(b.scrollWidth-b.clientWidth)/2" in _l[0] and "b.scrollTop=" in _l[0], _l[:1])
_m3, _l3 = zoom("3×")
chk("⚠️ 3×: al 300 %", "width:300%!important" in _m3, _m3[:200])
chk("⚠️ …y cada nivel lleva su script (el mismo texto no se volvería a ejecutar, v600)", _l and _l3 and _l[0] != _l3[0])

a = ap(rol="owner")
next(b_ for b_ in a.button if b_.key == "libfoto_LIB-001").click()
a.run()
chk("⚠️ al propietario sí: «Filed by»", "Filed by" in _todo(a), _todo(a)[:200])
a = ap()
_mp = [x for x in a.selectbox]
_btn2 = _btn(a, "cpxkpi_lib_doc")
_btn2.click()
a.run()
next((x for x in a.button if x.key == "libfoto_LIB-001"), None)
chk("un documento sin imagen no lleva zoom", "lib_zoom" not in str([getattr(x, "key", "") for x in a.get("button_group")]))

sec("3. ⚠️ Atrás y el menú")
GA = r'''
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "x", "nombre": "x", "rol": "field", "grupo": "cliente1"})
from core import home_ui as H
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    st.session_state["_admin_sec"] = st.session_state["_SEC"]
    st.session_state["_lib_open"] = "LIB-002"
    st.session_state["_lib_nav"] = ["LIB-%03d" % i for i in range(30)]
    st.session_state["_lib_nav_de"] = "fotos"
    st.session_state["_nav_hist"] = st.session_state["_HIST"]
st.session_state["_PUEDE"] = H.puede_atras()
H.navegar = lambda *a, **k: st.session_state.__setitem__("_NAV", a)
if st.session_state.pop("_TOCA", False):
    H.ir_atras()
st.session_state["_PUEDE2"] = H.puede_atras()
'''


def atras(sec_, hist):
    a = AppTest.from_string(GA, default_timeout=60)
    a.session_state["_SEC"], a.session_state["_HIST"], a.session_state["_TOCA"] = sec_, hist, False
    a.run()
    chk("   (sin excepción)", not a.exception, [e.value for e in a.exception][:1])
    return a


a = atras("biblioteca", [("autogestion", "🎫 Credenciales")])
_ss = a.session_state
a.session_state["_TOCA"] = True
a.run()
chk("⚠️ con una foto abierta, atrás cierra la foto", "_lib_open" not in a.session_state, a.session_state["_lib_open"] if "_lib_open" in a.session_state else None)
chk("⚠️ …no navega a la pantalla anterior", "_NAV" not in a.session_state)
chk("⚠️ …y gasta nada del historial", a.session_state["_nav_hist"] == [("autogestion", "🎫 Credenciales")], a.session_state["_nav_hist"])
chk("⚠️ …vuelve a la página de la lista donde estaba la foto", a.session_state["_lib_pag"] == 0 and a.session_state["_bajar_lib_gal"] is True)
a = atras("biblioteca", [])
chk("⚠️ sin historial (entrando directo a Library), «←» no sale apagado", a.session_state["_PUEDE"] is True)
a = atras("autogestion", [("biblioteca", None)])
a.session_state["_TOCA"] = True
a.run()
chk("⚠️ fuera de Library, atrás hace lo de siempre (no gasta el toque en algo invisible)",
    "_NAV" in a.session_state and "_lib_open" in a.session_state, a.session_state["_NAV"] if "_NAV" in a.session_state else None)
a = atras("autogestion", [])
chk("…y sin historial, apagado, como siempre", a.session_state["_PUEDE"] is False)
_h = _src("home_ui.py")
chk("⚠️ tocar Library en el menú cierra la foto", 'if _k == "biblioteca" and st.session_state.get("_lib_open"):' in _h
    and _h.index('if _k == "biblioteca" and st.session_state.get("_lib_open"):') < _h.index('navegar(_k)\n        if _open:'))
chk("el botón «←» del móvil depende de `puede_atras`", 'disabled=not puede_atras()' in _h
    and ".st-key-nav_back_btn button" in _h)

print("\n%d ok, %d fallos" % (n_ok, len(fallos)))
for x in fallos:
    print("  FALLO:", x)
sys.exit(1 if fallos else 0)
