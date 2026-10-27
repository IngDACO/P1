# -*- coding: utf-8 -*-
"""v613 · EL TELEGRAM YA NO ES OBLIGATORIO PARA ENTRAR (por ahora) — decisión del usuario
(27/10/2026): «vamos a desactivar por ahora que se tenga que ligar a un telegram para poder
loguear, para poder hacer pruebas con más usuarios de campo ficticios».

Por qué: con el bot configurado en el Cloud, la puerta de `app.py` exigía Telegram a todo usuario
de campo, y solo campo000 lo tenía (un chat_id es una conversación REAL: no se inventa).

Lo que protege, sin red y sin la hoja real:
  (a) la decisión vigente: `notify.TELEGRAM_OBLIGATORIO_CAMPO` en False — el email SIGUE siendo
      obligatorio;
  (b) UNA sola regla (`notify.contacto_campo_ok`): ningún otro sitio de la app decide por su cuenta
      que el contacto de campo es «email Y Telegram» (si no, el Home, el resumen del admin y los
      paneles dirían «no puede usar la app» de quien sí puede);
  (c) con la política de vuelta (True), el Telegram se exige — pero solo si el bot existe (v368);
  (d) la ficha de contacto dice que por ahora es opcional, y solo cuando lo es.
(La puerta de `app.py`, evaluada por AST en los 16 escenarios, la vigila verif_v368.)
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
sec("1. La decisión vigente y la regla")
chk("⚠️ POR AHORA el Telegram no se exige al campo (decisión del usuario, 27/10/2026)",
    N.TELEGRAM_OBLIGATORIO_CAMPO is False, N.TELEGRAM_OBLIGATORIO_CAMPO)
_o = (N.TELEGRAM_OBLIGATORIO_CAMPO, N.telegram_configured, N.bot_username)
_MAIL = {"Email": "a@b.co", "TelegramChatID": ""}
_TODO = {"Email": "a@b.co", "TelegramChatID": "123"}
_SIN = {"Email": "", "TelegramChatID": "123"}
try:
    N.telegram_configured, N.bot_username = (lambda: True), (lambda: "bot")
    N.TELEGRAM_OBLIGATORIO_CAMPO = False
    chk("sin exigirlo y CON bot: con email basta", N.contacto_campo_ok(_MAIL) and not N.exige_telegram_campo())
    chk("...pero el email SIGUE siendo obligatorio", not N.contacto_campo_ok(_SIN))
    chk("...y un usuario vacío no revienta", N.contacto_campo_ok(None) is False)
    N.TELEGRAM_OBLIGATORIO_CAMPO = True
    chk("con la política de vuelta: el Telegram se exige", N.exige_telegram_campo()
        and not N.contacto_campo_ok(_MAIL) and N.contacto_campo_ok(_TODO))
    N.telegram_configured, N.bot_username = (lambda: False), (lambda: "")
    chk("...pero SIN bot no se exige (v368: no hay callejón sin salida)",
        not N.exige_telegram_campo() and N.contacto_campo_ok(_MAIL))
finally:
    N.TELEGRAM_OBLIGATORIO_CAMPO, N.telegram_configured, N.bot_username = _o

# ═════════════════════════════════════════════════════════════════
sec("2. ⚠️ UNA sola regla: nadie más decide «email Y Telegram» por su cuenta")


def _dobles(fuente):
    """`and` que mira a la vez el email y el TelegramChatID (la regla vieja, copiada a mano)."""
    out = []
    for n in ast.walk(ast.parse(fuente)):
        if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.And):
            s = ast.unparse(n)
            if "'Email'" in s and "'TelegramChatID'" in s:
                out.append(s[:80])
    return out


# la sonda, validada con un caso conocido-malo y uno bueno (trampa 12)
chk("la sonda VE la regla vieja copiada a mano",
    len(_dobles("ok = str(u.get('Email', '')).strip() and str(u.get('TelegramChatID', '')).strip()")) == 1)
chk("...y no confunde el «o» de los avisos del admin (uno de los dos basta)",
    _dobles("x = not (str(u.get('Email', '')).strip() or str(u.get('TelegramChatID', '')).strip())") == [])
_hallados = {}
for rel in ["app.py"] + ["core/" + f for f in sorted(os.listdir(os.path.join(RAIZ, "core"))) if f.endswith(".py")]:
    if rel == "core/notify.py":
        continue
    _d = _dobles(open(os.path.join(RAIZ, rel), encoding="utf-8").read())
    if _d:
        _hallados[rel] = _d
chk("en toda la app, nadie más exige «email Y Telegram» (todo pasa por `contacto_campo_ok`)",
    not _hallados, _hallados)
# la puerta de `app.py`: `_exige_tg` sale de la regla de notify (verif_v368 evalúa `_falta_tg` con la
# regla REAL, pero no mira de dónde saca `app.py` su `_exige_tg`: si la calculara por su cuenta —solo
# el bot—, la puerta volvería a exigir el Telegram con la política apagada)
_ex = [ast.unparse(n.value) for n in ast.walk(ast.parse(open(os.path.join(RAIZ, "app.py"), encoding="utf-8").read()))
       if isinstance(n, ast.Assign) and len(n.targets) == 1 and getattr(n.targets[0], "id", "") == "_exige_tg"]
chk("⚠️ la puerta de `app.py` pregunta a la regla (`notify.exige_telegram_campo()`), no por su cuenta",
    "notify.exige_telegram_campo()" in _ex and all(x in ("notify.exige_telegram_campo()", "False") for x in _ex), _ex)
_usos = {}
for rel in ("core/admin_digest.py", "core/auth_ui.py", "core/projects_ui.py"):
    _usos[rel] = open(os.path.join(RAIZ, rel), encoding="utf-8").read().count("contacto_campo_ok(")
# el resumen (cifra del Home + texto del asistente), los paneles de usuarios (tabla, aviso, ficha y
# fila de salud) y el aviso al ASIGNAR gente a una obra — este último lo destapó el barrido de arriba
chk("el resumen del admin (2), los paneles de usuarios (4) y el aviso al asignar (1) usan la regla",
    _usos == {"core/admin_digest.py": 2, "core/auth_ui.py": 4, "core/projects_ui.py": 1}, _usos)

# ═════════════════════════════════════════════════════════════════
sec("3. La ficha de contacto lo dice (AppTest)")
APP = r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
ss = st.session_state
from core import auth, auth_ui, notify
auth.get_user = lambda u: {"User": u, "Email": "a@b.co", "TelegramChatID": ""}
notify.telegram_configured = lambda: True
notify.bot_username = lambda: "copex_bot"
notify.TELEGRAM_OBLIGATORIO_CAMPO = bool(ss.get("_pol", False))
auth_ui._contacto_uno("helper 1", key_prefix="cc")
'''


def _txt(at):
    return [c.value for c in at.caption] + [m.value for m in at.markdown]


at = AppTest.from_string(APP, default_timeout=60).run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("sin exigirlo: dice que por ahora es OPCIONAL (y que vincularlo sirve para los avisos)",
    any("For now Telegram is **optional**" in x for x in _txt(at)), _txt(at)[:6])
chk("...y el enlace del bot sigue ahí para vincularlo",
    any("t.me/copex_bot?start=helper1" in str(c.value) for c in at.code), [str(c.value) for c in at.code])
at2 = AppTest.from_string(APP, default_timeout=60)
at2.session_state["_pol"] = True
at2.run()
chk("con la política de vuelta, no dice que sea opcional",
    not any("optional" in x for x in _txt(at2)), _txt(at2)[:6])

# ═════════════════════════════════════════════════════════════════
sec("4. El aviso al ASIGNAR gente a una obra (AppTest) — el sitio que destapó el barrido")
APP2 = r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
ss = st.session_state
from core import auth, credentials, notify, projects_ui as PU
_U = {"conmail": {"User": "conmail", "Name": "Con Mail", "Email": "a@b.co", "TelegramChatID": ""},
      "sinmail": {"User": "sinmail", "Name": "Sin Mail", "Email": "", "TelegramChatID": "9"}}
auth.get_user = lambda u: _U.get(u, {})
credentials.list_for = lambda u: []
PU._etq_us = lambda us: {u: _U[u]["Name"] for u in us}
notify.telegram_configured = lambda: True
notify.bot_username = lambda: "copex_bot"
notify.TELEGRAM_OBLIGATORIO_CAMPO = bool(ss.get("_pol", False))
PU._avisar_asignados(ss.get("_us", ["conmail"]))
'''


def _avisos(at):
    return [str(w.value) for w in at.warning]


at3 = AppTest.from_string(APP2, default_timeout=60).run()
chk("asignar a quien tiene email y NO Telegram: sin aviso de contacto (le llega por correo)",
    not at3.exception and not any("contact" in x.lower() or "email" in x.lower() for x in _avisos(at3)),
    ([e.value for e in at3.exception][:1], _avisos(at3)))
at4 = AppTest.from_string(APP2, default_timeout=60)
at4.session_state["_us"] = ["conmail", "sinmail"]
at4.run()
chk("...a quien NO tiene email: «Without an email: Sin Mail» (solo él, y lo que de verdad le falta)",
    any("**Without an email:** Sin Mail." in x for x in _avisos(at4))
    and not any("Con Mail" in x for x in _avisos(at4)), _avisos(at4))
at5 = AppTest.from_string(APP2, default_timeout=60)
at5.session_state["_pol"] = True
at5.run()
chk("con la política de vuelta: avisa de quien no tiene Telegram, con el texto de los dos canales",
    any("(email + Telegram)" in x and "Con Mail" in x for x in _avisos(at5)), _avisos(at5))

print("")
print("=" * 70)
if fallos:
    print("%d comprobaciones — %d FALLOS" % (n_ok + len(fallos), len(fallos)))
    for f in fallos:
        print("   · %s" % f)
    sys.exit(1)
print("%d comprobaciones — TODO OK" % n_ok)
