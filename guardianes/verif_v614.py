# -*- coding: utf-8 -*-
"""v614 · UN EMAIL QUE NO ES UN EMAIL NO CUENTA COMO CONTACTO — decisión del usuario (28/10/2026,
«Ejecuta 2»), visto verificando v613: el de «driver 1» era literalmente «driver 1» y la ficha decía
a la vez «Contact OK» e «Invalid email». La regla solo miraba que no estuviera vacío, y con el
Telegram opcional (v613) el email es el ÚNICO canal de un usuario de campo.

Lo que protege, sin red y sin la hoja real:
  (a) `notify.email_campo_ok`: escrito Y que sea un correo (`auth.revisar_email`); una errata
      probable («hotmai.com») NO lo invalida — es un correo, y la ficha ya avisa aparte;
  (b) `contacto_campo_ok` (la regla de la puerta, el Home, el asistente y los paneles) la usa;
  (c) la puerta de `app.py` también (`_has_mail`), y a quien tiene algo escrito que no es un correo
      le dice ESO —y quién lo corrige—, no «te falta el email»;
  (d) el aviso al asignar dice «Without a valid email».
"""
import ast
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "admin1", "nombre": "Admin Test", "rol": "administrator",
                            "grupo": "cliente1"}

fallos, n_ok = [], 0


def ok(q, det=""):
    global n_ok
    n_ok += 1
    print("   ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("   FALLO %s%s" % (q, ("  -> " + str(det)) if det else ""))


def sec(x):
    print("\n" + x)
    print("-" * 70)


def chk(q, cond, det=""):
    (ok if cond else fallo)(q, det)


from streamlit.testing.v1 import AppTest                          # noqa: E402

from core import notify as N                                      # noqa: E402

# ═════════════════════════════════════════════════════════════════
sec("1. Qué email vale")
chk("⚠️ «driver 1» NO es un email (el caso real de producción)", N.email_campo_ok({"Email": "driver 1"}) is False)
chk("vacío, tampoco", N.email_campo_ok({"Email": "  "}) is False and N.email_campo_ok(None) is False)
chk("un correo, sí", N.email_campo_ok({"Email": "driver1@example.com"}) is True)
chk("⚠️ una errata probable («hotmai.com») NO lo invalida (es un correo; la ficha avisa aparte)",
    N.email_campo_ok({"Email": "helper1@hotmai.com"}) is True)
_o = (N.TELEGRAM_OBLIGATORIO_CAMPO, N.telegram_configured, N.bot_username)
try:
    for _pol in (False, True):
        N.TELEGRAM_OBLIGATORIO_CAMPO = _pol
        N.telegram_configured, N.bot_username = (lambda: True), (lambda: "bot")
        chk("⚠️ con un email que no es un correo, el contacto NO está completo (política=%s)" % _pol,
            N.contacto_campo_ok({"Email": "driver 1", "TelegramChatID": "123"}) is False)
finally:
    N.TELEGRAM_OBLIGATORIO_CAMPO, N.telegram_configured, N.bot_username = _o
chk("...y con uno bueno, sí (la política vigente: sin Telegram)",
    N.contacto_campo_ok({"Email": "driver1@example.com", "TelegramChatID": ""}) is True)

# ═════════════════════════════════════════════════════════════════
sec("2. La puerta de app.py")
_src = open(os.path.join(RAIZ, "app.py"), encoding="utf-8").read()
_arb = ast.parse(_src)
_hm = [ast.unparse(n.value) for n in ast.walk(_arb)
       if isinstance(n, ast.Assign) and len(n.targets) == 1 and getattr(n.targets[0], "id", "") == "_has_mail"]
chk("⚠️ `_has_mail` sale de la regla (`notify.email_campo_ok`), no de «no está vacío»",
    _hm == ["notify.email_campo_ok(_rec)"], _hm)
# la rama del email que no es un correo: ANTES de la de «te falta el email», y condicionada a que haya algo
_i_inv = _src.find("is not a valid address, and your administrator corrects it")
_i_fal = _src.find("Your account needs an **email**, and your administrator enters it")
chk("a quien tiene algo escrito que no es un correo se le dice ESO (y quién lo corrige)",
    0 < _i_inv < _i_fal, (_i_inv, _i_fal))
_ramas = [ast.unparse(n.test) for n in ast.walk(_arb) if isinstance(n, ast.If)
          and "_falta_mail" in ast.unparse(n.test) and "Email" in ast.unparse(n.test)]
chk("...en una rama que pide que HAYA algo escrito (si no, a todos les diría «no es válido»)",
    _ramas == ["_falta_mail and str(_rec.get('Email', '')).strip()"], _ramas)

# ═════════════════════════════════════════════════════════════════
sec("3. El aviso al asignar (AppTest)")
APP = r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
from core import auth, credentials, notify, projects_ui as PU
_U = {"drv": {"User": "drv", "Name": "Driver Uno", "Email": "driver 1", "TelegramChatID": ""},
      "bien": {"User": "bien", "Name": "Bien", "Email": "bien@example.com", "TelegramChatID": ""}}
auth.get_user = lambda u: _U.get(u, {})
credentials.list_for = lambda u: []
PU._etq_us = lambda us: {u: _U[u]["Name"] for u in us}
notify.telegram_configured = lambda: True
notify.bot_username = lambda: "copex_bot"
PU._avisar_asignados(["drv", "bien"])
'''
at = AppTest.from_string(APP, default_timeout=60).run()
_av = [str(w.value) for w in at.warning]
chk("asignar a quien tiene «driver 1» por email: «Without a valid email: Driver Uno» (y no al otro)",
    not at.exception and any("**Without a valid email:** Driver Uno." in x for x in _av)
    and not any("Bien" in x for x in _av), ([e.value for e in at.exception][:1], _av))

print("")
print("=" * 70)
if fallos:
    print("%d comprobaciones — %d FALLOS" % (n_ok + len(fallos), len(fallos)))
    for f in fallos:
        print("   · %s" % f)
    sys.exit(1)
print("%d comprobaciones — TODO OK" % n_ok)
