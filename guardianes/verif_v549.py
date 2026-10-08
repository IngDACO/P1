# -*- coding: utf-8 -*-
"""v549 · LOS BOTONES PARTEN SU TEXTO EN VEZ DE RECORTARLO CON «…» (trampa nº33).

Streamlit 1.64 recorta en UNA línea la etiqueta de un botón colocado en una columna
(`wrap=None`): «AC…», «No contact det…», «Open workda…», «Leave …». ~123 botones en columnas;
decisión del usuario: barrido de una vez. → `core/botones.instalar()` pone `wrap=True` por
defecto en toda la app (app.py lo llama antes de cualquier botón); `wrap=False` explícito
sigue mandando donde se quiera una línea a propósito.

Lo que se protege, EJECUTANDO botones reales con AppTest y mirando el mensaje que recibe el
navegador (`proto.wrap`), no la forma del código:
1. Antes de instalar, un botón en columna sale SIN wrap (la sonda ve el problema).
2. Instalado: botón, descarga, envío de formulario y enlace, en columnas y fuera, con wrap.
3. `wrap=False` explícito se respeta.
4. Instalar dos veces no envuelve dos veces; y app.py lo instala antes de cualquier botón.
"""
import ast
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
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


from streamlit.testing.v1 import AppTest                          # noqa: E402

GUION = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
from core import botones
if st.session_state.get("_instalar"):
    botones.instalar()
    if st.session_state.get("_dos_veces"):
        botones.instalar()
c1, c2 = st.columns(2)
c1.button("Open workday at that time", key="b_col")
with c2:
    st.button("Leave the project", key="b_with")
st.button("Fuera de columnas", key="b_fuera")
c1.button("Una sola línea a propósito", key="b_false", wrap=False)
c2.download_button("Download the report", data=b"x", file_name="x.txt", key="d_col")
with st.form("f"):
    st.columns(2)[0].form_submit_button("Save the corrected time")
c1.link_button("Open in Google Maps", "https://example.com", key="l_col")
st.session_state["_marcas"] = [getattr(getattr(type(c1), n), "_copex_wrap_por_defecto", False)
                               for n in botones.METODOS]
''' % RAIZ


def corre(**kw):
    at = AppTest.from_string(GUION, default_timeout=120)
    for k, v in kw.items():
        at.session_state[k] = v
    at.run()
    if at.exception:
        raise SystemExit("EXCEPCION: %s" % [e.value for e in at.exception][:2])
    return at


def wraps(at):
    """{clave o etiqueta: wrap} de TODOS los botones que recibe el navegador."""
    out = {}
    for el in at.main:
        pass
    for b in at.button:
        out[b.key or b.label] = bool(b.proto.wrap)
    for b in at.get("download_button"):
        out[b.proto.id.split("-")[-1] if not b.key else b.key] = bool(b.proto.wrap)
    for b in at.get("link_button"):
        out["l_col"] = bool(b.proto.wrap)
    return out


print("1. La sonda VE el problema: sin instalar, el botón en columna va sin wrap")
_w = wraps(corre())
chk("antes de instalar, «Open workday at that time» (en columna) sale SIN wrap",
    _w.get("b_col") is False, _w)

print("\n2. Instalado: todo botón lleva wrap (el texto nunca se recorta)")
at = corre(_instalar=True)
_w = wraps(at)
for k, q in (("b_col", "botón en columna (col.button)"),
             ("b_with", "botón dentro de `with col:`"),
             ("b_fuera", "botón fuera de columnas"),
             ("d_col", "botón de DESCARGA en columna"),
             ("l_col", "botón de ENLACE en columna")):
    chk("⚠️ %s → wrap" % q, _w.get(k) is True, _w)
_fs = [b for b in at.button if "corrected" in (b.label or "")]
chk("botón de ENVÍO de formulario en columna → wrap", _fs and bool(_fs[0].proto.wrap), _fs)

print("\n3. Lo explícito manda")
chk("`wrap=False` en la llamada se respeta (una línea a propósito)", _w.get("b_false") is False, _w)

print("\n4. Idempotente y en su sitio")
at2 = corre(_instalar=True, _dos_veces=True)
chk("instalar dos veces no rompe nada y sigue con wrap", wraps(at2).get("b_col") is True)
from core import botones                                          # noqa: E402
import streamlit as st                                            # noqa: E402
from streamlit.delta_generator import DeltaGenerator              # noqa: E402
botones.instalar()
botones.instalar()
_f = DeltaGenerator.button
_capas = 0
while getattr(_f, "__wrapped__", None) is not None and getattr(_f, "_copex_wrap_por_defecto", False):
    _capas += 1
    _f = _f.__wrapped__
chk("...una sola capa de envoltorio en la clase", _capas == 1, _capas)
chk("`st.button` (alias del módulo) también queda cubierto",
    getattr(getattr(st.button, "__func__", None), "_copex_wrap_por_defecto", False))
_src = io.open(os.path.join(RAIZ, "app.py"), encoding="utf-8").read()
_arbol = ast.parse(_src)
_ins = next((n.lineno for n in ast.walk(_arbol) if isinstance(n, ast.Call)
             and ast.unparse(n.func) == "_botones.instalar"), None)
_primer_btn = min((n.lineno for n in ast.walk(_arbol) if isinstance(n, ast.Call)
                   and getattr(n.func, "attr", None) in botones.METODOS), default=10 ** 9)
_login = next((n.lineno for n in ast.walk(_arbol) if isinstance(n, ast.Call)
               and ast.unparse(n.func) == "render_login"), 10 ** 9)
chk("app.py instala el defecto ANTES de cualquier botón (el login incluido)",
    _ins is not None and _ins < min(_primer_btn, _login), (_ins, _primer_btn, _login))

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
