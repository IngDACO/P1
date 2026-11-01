# -*- coding: utf-8 -*-
"""v619 · LAS EXPULSIONES DEL CAMPO (01/11/2026, «Dale con las 2»). Medido en producción: con 150 s
sin conexión —un móvil bloqueado— Streamlit borra la sesión y el primer toque sale en «Sign in»;
con 20 s, sobrevive. La cookie de «Keep me signed in» la restaura, pero la casilla venía desmarcada.
  (1) la sesión desconectada dura 30 min en el servidor (`server.disconnectedSessionTTL`);
  (2) la casilla viene MARCADA, y desmarcarla sigue valiendo.
Lo que esto NO prueba: que el Cloud aplique el valor. Eso solo se mide allí, cortando la conexión.
Sin red ni hoja real.
"""
import os
import sys
import tomllib

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

n_ok, fallos = 0, []


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("   ok   %s" % q)
    else:
        fallos.append(q)
        print("   FALLO %s%s" % (q, ("  -> " + str(det)) if det else ""))


print("1. La sesión desconectada")
from streamlit import config                                       # noqa: E402

with open(os.path.join(RAIZ, ".streamlit", "config.toml"), "rb") as fh:
    _cfg = tomllib.load(fh)
_op = "server.disconnectedSessionTTL"
chk("la opción EXISTE en el Streamlit fijado: un nombre mal escrito se ignoraría en silencio",
    _op in config.get_config_options(), _op)
_ttl = _cfg.get("server", {}).get("disconnectedSessionTTL")
chk("⚠️ `config.toml` le da 30 min (eran 120 s)", _ttl == 1800, _ttl)
chk("…y lo que se lee de verdad con ese fichero es ese valor", config.get_option(_op) == 1800,
    config.get_option(_op))

print("\n2. La casilla, con clics (AppTest)")
from streamlit.testing.v1 import AppTest                           # noqa: E402

APP = r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
from core import auth, auth_ui, session_cookie
auth.is_configured = lambda: True
auth.has_any_user = lambda: True
auth.verify_login = lambda u, p: {"ok": True, "usuario": "campo000", "rol": "field",
                                  "nombre": "Field", "grupo": "cliente1"}
auth.start_session = lambda u: (True, "TOK")
session_cookie.load = lambda: (None, None)
if auth_ui.render_login():
    st.write("DENTRO recordar=%s" % st.session_state.get("_remember_session"))
'''


def entrar(desmarcar=False):
    at = AppTest.from_string(APP, default_timeout=60).run()
    chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
    c = at.checkbox(key="login_remember")
    v0 = c.value
    if desmarcar:
        c.uncheck()
    at.text_input(key="login_u").set_value("campo000")
    at.text_input(key="login_p").set_value("x")
    at.button(key="login_entrar").click().run()
    return v0, " ".join(m.value for m in at.markdown)


_v, _t = entrar()
chk("⚠️ la casilla viene MARCADA", _v is True, _v)
chk("⚠️ …y entrar sin tocarla RECUERDA la sesión", "DENTRO recordar=True" in _t, _t[:120])
_v, _t = entrar(desmarcar=True)
chk("⚠️ desmarcarla sigue valiendo: en un equipo compartido no se recuerda",
    "DENTRO recordar=False" in _t, _t[:120])

print("\n3. Lo que se le dice al usuario")
_ui = open(os.path.join(RAIZ, "core", "auth_ui.py"), encoding="utf-8").read()
chk("la ayuda dice que hay que DESMARCARLA en un equipo compartido",
    "Untick it on a shared or public computer." in _ui)
chk("…y ya no dice lo contrario", "Leave it unticked" not in _ui)

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    sys.exit(1)
print("TODO OK")
