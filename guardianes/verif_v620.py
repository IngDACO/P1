# -*- coding: utf-8 -*-
"""v620 · LO VISTO VERIFICANDO v619 (01/11/2026, «Dale»): al restaurar la sesión con la cookie, el
menú marcaba «Progress» con el contenido de la pestaña que se había tocado. El toque que destapa que
la sesión ya no existe llega con el valor de su control; el navegador quita ese selector mientras
se ve «Sign in», pero el servidor se queda con el valor.
Lo que AppTest NO ve (trampa 31): el navegador. Eso se mide en producción, con la sesión borrada.
Sin red ni hoja real.
"""
import os
import sys

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


from streamlit.testing.v1 import AppTest                           # noqa: E402

APP = r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
from core import auth, auth_ui, session_cookie
auth.is_configured = lambda: True
auth.has_any_user = lambda: True
auth.validate_session = lambda u, t: ({"usuario": "campo000", "rol": "field", "nombre": "Field",
                                       "grupo": "cliente1", "token": t} if t == "TOK" else {})
session_cookie.load = lambda: st.session_state.get("_prueba_cookie", (None, None))
if auth_ui.render_login():
    st.write("DENTRO sec=%s otra=%s mgr=%s usuario=%s" % (
        st.session_state.get("cpxseg_fld_sec", "NADA"), st.session_state.get("otra_clave", "NADA"),
        st.session_state.get("copex_prueba", "NADA"), st.session_state["auth"]["usuario"]))
    st.radio("Sec", ["A", "B"], key="cpxseg_fld_sec")
'''


def corre(cookie, previa=True):
    at = AppTest.from_string(APP, default_timeout=60)
    at.session_state["_prueba_cookie"] = cookie
    if previa:
        at.session_state["cpxseg_fld_sec"] = "B"
        at.session_state["otra_clave"] = "x"
        at.session_state["copex_prueba"] = "gestor"
    at.run()
    chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
    return at


print("1. La sesión restaurada no hereda la página anterior")
at = corre(("campo000", "TOK"))
_t = " ".join(m.value for m in at.markdown)
chk("⚠️ el valor del control tocado NO pasa a la sesión restaurada", "sec=NADA" in _t, _t[:120])
chk("…ni otra clave de la página anterior", "otra=NADA" in _t, _t[:120])
chk("el selector nace en su primera opción: menú y contenido dicen lo mismo",
    at.radio(key="cpxseg_fld_sec").value == "A", at.radio(key="cpxseg_fld_sec").value)
chk("⚠️ la sesión SÍ se restaura", "usuario=campo000" in _t, _t[:120])
chk("lo del gestor de cookies se conserva", "mgr=gestor" in _t, _t[:120])
chk("la marca de «recordar» sigue puesta", at.session_state["_remember_session"] is True)

print("\n2. Solo al restaurar")
at = corre(("campo000", "OTRO"))
chk("una cookie que no vale no entra", not any("DENTRO" in m.value for m in at.markdown))
chk("…y no borra nada: no ha restaurado", at.session_state["otra_clave"] == "x")
at = corre((None, None))
chk("sin cookie, tampoco", at.session_state["otra_clave"] == "x")

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    sys.exit(1)
print("TODO OK")
