# -*- coding: utf-8 -*-
"""v562 · EL CLIC QUE SOBREVIVE A UNA PASADA CORTADA (decisión del usuario: «Dale»).

Un componente que se monta y envía su valor (mapa, firma del Pre-Start, gestor de cookies)
pide una pasada nueva; si llega mientras corre la de un clic, Streamlit 1.64 la CORTA y el
clic se pierde (mini-app: 8 de 8). `core/botones` anota el clic en un `on_click` (que corre
ANTES del cuerpo) y el botón devuelve True UNA vez en la pasada siguiente.

Aquí la pasada cortada se simula con un `st.rerun()` ANTES del botón: la pasada nueva llega
sin el disparador, igual que la del componente. ⚠️ El CONTROL va primero y sin instalar (la
instalación toca la clase para todo el proceso): si el control no pierde el clic, la sonda
no reproduce nada y el resto no valdría.
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


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("  ok   " + q)
    else:
        fallos.append(q)
        print("  FALLO " + q + (("  -> " + str(det)) if det != "" else ""))


from streamlit.testing.v1 import AppTest                                    # noqa: E402

GUION = r'''
import streamlit as st
from core import botones
if st.session_state.get("_instalar", True):
    botones.instalar()
for _k, _v in (("n_btn", 0), ("n_form", 0), ("n_cb", 0), ("n_dis", 0), ("chat_log", [])):
    st.session_state.setdefault(_k, _v)
if st.session_state.pop("_cortar", False):
    st.rerun()                 # la pasada del clic se corta ANTES de llegar al botón
if not st.session_state.get("_ocultar"):
    if st.button("Not now", key="nn"):
        st.session_state.n_btn += 1
def _cb():
    st.session_state.n_cb += 1
st.button("Con callback", key="cb", on_click=_cb)
if st.button("Deshabilitado", key="dis", disabled=st.session_state.get("_deshab", False)):
    st.session_state.n_dis += 1
with st.form("f"):
    st.text_input("Nombre", key="f_nombre")
    if st.form_submit_button("Guardar"):
        st.session_state.n_form += 1
        st.session_state.f_val = st.session_state.f_nombre
q = st.chat_input("Ask", key="chat")
if q:
    st.session_state.chat_log.append(q)
if st.session_state.get("_fin", True):
    botones.fin_de_pasada()
'''


def nuevo(**kw):
    at = AppTest.from_string(GUION, default_timeout=60)
    for k, v in kw.items():
        at.session_state[k] = v
    at.run()
    return at


def ss(at, k, d=None):
    return at.session_state[k] if k in at.session_state else d


# ══════════════════════════════════════════════════════════════════════════════
print("0. CONTROL sin la cura: la sonda REPRODUCE la pérdida")
at = nuevo(_instalar=False)
chk("el guion se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
at.button(key="nn").click()
at.session_state["_cortar"] = True
at.run()
chk("⚠️ sin la cura, el clic de una pasada cortada SE PIERDE (n_btn = 0)",
    ss(at, "n_btn") == 0, ss(at, "n_btn"))
chk("…y un clic normal sí cuenta (la sonda sabe ver un clic)",
    (at.button(key="nn").click().run() and ss(at, "n_btn") == 1), ss(at, "n_btn"))
at.text_input(key="f_nombre").set_value("Ana")
[b for b in at.button if b.label == "Guardar"][0].click()
at.session_state["_cortar"] = True
at.run()
chk("sin la cura, la ENTREGA de un formulario cortada también se pierde",
    ss(at, "n_form") == 0, ss(at, "n_form"))
at.chat_input(key="chat").set_value("hola")
at.session_state["_cortar"] = True
at.run()
chk("sin la cura, la pregunta del CHAT cortada también se pierde",
    ss(at, "chat_log") == [], ss(at, "chat_log"))

# ══════════════════════════════════════════════════════════════════════════════
print("\n1. Con la cura: el clic sobrevive, una sola vez")
at = nuevo()
chk("instalado, el guion se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
at.button(key="nn").click()
at.session_state["_cortar"] = True
at.run()
chk("⚠️ el clic de una pasada CORTADA se ejecuta en la siguiente (n_btn = 1)",
    ss(at, "n_btn") == 1, ss(at, "n_btn"))
at.run()
at.run()
chk("⚠️ …y UNA sola vez (dos pasadas más sin clic: sigue en 1)", ss(at, "n_btn") == 1, ss(at, "n_btn"))
at.button(key="nn").click().run()
chk("un clic normal: +1", ss(at, "n_btn") == 2, ss(at, "n_btn"))
at.run()
chk("…y nada en la pasada siguiente", ss(at, "n_btn") == 2, ss(at, "n_btn"))
chk("no quedan notas colgando", not ss(at, "_clic_pendiente", {}), ss(at, "_clic_pendiente"))
# ⚠️ Sin cierre de pasada (los caminos que acaban en `st.stop()`: el acceso, el bloqueo de
# contacto) lo único que impide repetir el clic es que la nota se GASTE al usarla. La 1ª
# versión de este guardián no lo miraba: la rotura «get en vez de pop» escapó (romper_v562).
at = nuevo(_fin=False)
at.button(key="nn").click()
at.session_state["_cortar"] = True
at.run()
at.run()
at.run()
chk("⚠️ sin cierre de pasada, el clic rescatado tampoco se repite (la nota se gasta)",
    ss(at, "n_btn") == 1, ss(at, "n_btn"))
at.button(key="nn").click().run()
at.run()
chk("…ni un clic normal", ss(at, "n_btn") == 2, ss(at, "n_btn"))

print("\n2. Entrega de formulario (sin clave) y chat")
at = nuevo()
at.text_input(key="f_nombre").set_value("Ana")
[b for b in at.button if b.label == "Guardar"][0].click()
at.session_state["_cortar"] = True
at.run()
chk("⚠️ la entrega de una pasada cortada se ejecuta, con lo escrito («Ana»)",
    ss(at, "n_form") == 1 and ss(at, "f_val") == "Ana", (ss(at, "n_form"), ss(at, "f_val")))
at.run()
chk("…una sola vez", ss(at, "n_form") == 1, ss(at, "n_form"))
at.chat_input(key="chat").set_value("hola")
at.session_state["_cortar"] = True
at.run()
chk("⚠️ la pregunta del chat de una pasada cortada llega («hola»)",
    ss(at, "chat_log") == ["hola"], ss(at, "chat_log"))
at.run()
chk("…una sola vez", ss(at, "chat_log") == ["hola"], ss(at, "chat_log"))

print("\n3. Una nota nunca dispara más tarde, en otra pantalla")
at = nuevo()
at.button(key="nn").click()
at.session_state["_ocultar"] = True       # la pasada del clic termina sin pintar el botón
at.run()
at.session_state["_ocultar"] = False
at.run()
chk("⚠️ una pasada COMPLETA que no pinta el botón tira su nota (no dispara después)",
    ss(at, "n_btn") == 0, ss(at, "n_btn"))
# sin el cierre de pasada (un `st.stop()` a mitad, p. ej.) manda la caducidad
at = nuevo(_fin=False)
at.button(key="nn").click()
at.session_state["_ocultar"] = True
at.run()
at.session_state["_ocultar"] = False
at.run()
chk("sin cierre de pasada y DENTRO de plazo, la nota sí dispara (la caducidad es lo que frena)",
    ss(at, "n_btn") == 1, ss(at, "n_btn"))
from core import botones as B                                               # noqa: E402
at = nuevo(_fin=False)
at.button(key="nn").click()
at.session_state["_ocultar"] = True
at.run()
_t0 = B.time.monotonic
B.time.monotonic = lambda: _t0() + B.VIGENCIA_S + 5
try:
    at.session_state["_ocultar"] = False
    at.run()
finally:
    B.time.monotonic = _t0
chk("⚠️ …y pasado el plazo (%d s) ya no dispara" % B.VIGENCIA_S, ss(at, "n_btn") == 0, ss(at, "n_btn"))

print("\n4. Lo que no se toca")
at = nuevo()
at.button(key="cb").click()
at.session_state["_cortar"] = True
at.run()
chk("un botón con `on_click` propio: su callback corre una vez (ya era seguro)",
    ss(at, "n_cb") == 1, ss(at, "n_cb"))
at = nuevo()
at.button(key="dis").click()
at.session_state["_cortar"] = True
at.session_state["_deshab"] = True
at.run()
chk("un botón que sale DESHABILITADO en la pasada de rescate no se dispara",
    ss(at, "n_dis") == 0, ss(at, "n_dis"))

# ══════════════════════════════════════════════════════════════════════════════
print("\n5. En la app")
APP = io.open(os.path.join(RAIZ, "app.py"), encoding="utf-8").read()
_t = ast.parse(APP)
_top = [ast.unparse(n.value.func) for n in _t.body
        if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)]
chk("⚠️ app.py cierra la pasada (`_botones.fin_de_pasada()`) y es lo ÚLTIMO que hace",
    _top and _top[-1] == "_botones.fin_de_pasada", _top[-3:])
chk("…después de pintar la sección", "_home.render_admin_content" in _top
    and _top.index("_home.render_admin_content") < _top.index("_botones.fin_de_pasada")
    if "_botones.fin_de_pasada" in _top else False)
_sin = []
for d, _, fs in os.walk(RAIZ):
    for f in fs:
        if f.endswith(".py"):
            for n in ast.walk(ast.parse(io.open(os.path.join(d, f), encoding="utf-8").read())):
                if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "button" \
                        and "key" not in {k.arg for k in n.keywords}:
                    _sin.append("%s:%d" % (f, n.lineno))
chk("⚠️ ningún `st.button` sin clave (sin clave la cura no lo reconoce)", not _sin, _sin)

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("TODO OK")
