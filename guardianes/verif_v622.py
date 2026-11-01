# -*- coding: utf-8 -*-
"""v622 · LO QUE v620 NO ARREGLÓ (01/11/2026). Tras perder la sesión, restaurar con la cookie dejaba el
menú en «Progress» con el contenido de la pestaña tocada. v620 borraba ese valor en el servidor; con
31 min sin conexión en producción siguió igual (su guardián dio verde con un caso preparado a mano:
trampa 31). Ahora la página vieja se recarga UNA vez; una recién abierta, no.
⚠️ Lo que esto NO prueba: el navegador. Eso solo se mide en producción, con la sesión borrada.
Sin red ni hoja real.
"""
import os
import re
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
from core import auth, auth_ui, incrustar, session_cookie
auth.is_configured = lambda: True
auth.has_any_user = lambda: True
auth.validate_session = lambda u, t: ({"usuario": "campo000", "rol": "field", "nombre": "Field",
                                       "grupo": "cliente1", "token": t} if t == "TOK" else {})
session_cookie.load = lambda: st.session_state.get("_prueba_cookie", (None, None))
session_cookie.save = lambda *a: None
incrustar.script = lambda js: st.session_state.setdefault("_scripts", []).append(js)
if auth_ui.render_login():
    auth_ui.render_user_bar()
    st.write("DENTRO")
'''


def corre(cookie):
    at = AppTest.from_string(APP, default_timeout=60)
    at.session_state["_prueba_cookie"] = cookie
    at.run()
    chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
    return at


def scripts(at):
    return [s for s in (at.session_state["_scripts"] if "_scripts" in at.session_state else [])
            if "location.reload" in s]


print("1. Restaurar deja el script, una vez")
at = corre(("campo000", "TOK"))
chk("la sesión se restaura", any("DENTRO" in m.value for m in at.markdown))
chk("⚠️ se inyecta el script que recarga una página vieja", len(scripts(at)) == 1, scripts(at))
chk("la marca se consume", "_restaurada" not in at.session_state)
at.run()
chk("⚠️ en la pasada siguiente NO se repite", len(scripts(at)) == 1, scripts(at))
at = corre(("campo000", "OTRO"))
chk("una cookie que no vale no inyecta nada", not scripts(at))
at = corre((None, None))
chk("sin cookie, tampoco", not scripts(at))

print("\n2. El script: el navegador decide, y sin bucles")
from core import auth_ui                                           # noqa: E402
_js = auth_ui._RECARGAR_SI_VIEJA
chk("recarga la página de la app (`window.parent`), no su recuadro", "w=window.parent" in _js and "w.location.reload()" in _js)
_m = re.search(r"if\((.*?)\)\{", _js)
_c = _m.group(1) if _m else ""
chk("⚠️ solo si la página no es recién abierta: abrir la app con la cookie no se ralentiza",
    "n-w.performance.timeOrigin>20000" in _c, _c)
chk("⚠️ el seguro contra bucles va en la MISMA condición", "n-a>120000" in _c and "&&" in _c, _c)
chk("…y apunta la recarga ANTES de hacerla", _js.index("setItem(k") < _js.index("location.reload"))
chk("un fallo del script no rompe nada", "try{" in _js and "catch(e){}" in _js)


def decide(ahora, origen, ultima):
    """La misma condición, en Python: que los números digan lo que el texto promete."""
    return ahora - origen > 20000 and ahora - ultima > 120000


chk("página vieja, sin recarga reciente: recarga", decide(2_000_000, 0, 0))
chk("⚠️ página recién abierta: NO", not decide(2_000_000, 1_995_000, 0))
chk("⚠️ página vieja pero recargada hace poco: NO (el seguro)", not decide(2_000_000, 0, 1_950_000))

print("\n3. Lo que v620 dejó no vuelve")
_src = open(os.path.join(RAIZ, "core", "auth_ui.py"), encoding="utf-8").read()
chk("el borrado en el servidor, que no servía, ya no está", "del st.session_state[k]" not in _src.split("def render_login")[0]
    and "_olvidar_pagina_anterior(" not in _src)
_tc = open(os.path.join(RAIZ, "core", "timeclock_ui.py"), encoding="utf-8").read()
chk("el pie de «Unassigned» cabe en la tarjeta", 't("travel or waiting")' in _tc and "a project not clocked in" not in _tc)

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    sys.exit(1)
print("TODO OK")
