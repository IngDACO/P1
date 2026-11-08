# -*- coding: utf-8 -*-
"""v645 · LO QUE ESCRIBE LA APP AL TOCAR UNA TARJETA YA NO LO LEE EL MODELO COMO SUYO (03/11/2026).

Visto en producción con v644, 2 de 2: tras pulsar Confirm, la app escribe «✅ …» en el chat como turno del asistente,
y en la pregunta siguiente el modelo lo negó («I hadn't confirmed that»): dijo que campo000 no estaba en PRJ-0030 con
la asignación ya hecha. Ahora `chat_ui.atender` lo marca (`app`, `card`), `chat_memoria` conserva la marca y
`chat_agent._para_el_modelo` se lo pasa como nota de la PERSONA. En pantalla sale igual.

Sin la API ni la hoja: confirmar, la memoria y el modelo, sustituidos.
"""
import datetime as dt
import json
import os
import sys
import types

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"}

from streamlit.testing.v1 import AppTest                          # noqa: E402

import core                                                        # noqa: E402
from core import chat_agent as CA, chat_memoria as CM, chat_tools as CT, chat_ui as CU   # noqa: E402

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


def leer(rel):
    with open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


HOY = dt.date(2026, 11, 3)
CM.guardar = lambda *a, **k: True                 # ⚠️ ni una escritura real (v643)
CM.borrar = lambda *a, **k: True

# ═════════════════════════════════════════════════════════════════
sec("1. Lo que escribe la app al tocar una tarjeta, marcado como suyo (con clics)")
GUION = r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
from core import chat_tools as CT, chat_ui as U
E = st.session_state["_esc"]
st.session_state["auth"] = {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"}
CT.confirmar = lambda a, ctx: E.get("res", (True, "Alert resolved."))
if not st.session_state.get("_ya"):
    st.session_state["_ya"] = True
    st.session_state["_chat_acciones"] = list(E["cartas"])
U.atender()
U.tarjetas()
'''
_cf = CT.confirmar


def app(**esc):
    at = AppTest.from_string(GUION, default_timeout=60)
    at.session_state["_esc"] = {"cartas": [{"id": "a1", "tipo": "aviso_cerrar", "titulo": "Close alert · Bondi", "detalle": "x", "datos": {}}], **esc}
    at.run()
    chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
    return at


def btn(at, k):
    return next((b for b in at.button if b.key == k), None)


at = app()
btn(at, "chat_ok_a1").click().run()
_u = at.session_state["chat_history"][-1]
chk("⚠️ Confirm: la línea de la app, marcada, con su tarjeta", _u.get("app") == "confirm" and _u.get("card") == "Close alert · Bondi"
    and _u["content"] == "✅ Alert resolved." and _u["role"] == "assistant", _u)
at = app()
btn(at, "chat_no_a1").click().run()
_u = at.session_state["chat_history"][-1]
chk("⚠️ Cancel, también", _u.get("app") == "cancel" and _u.get("card") == "Close alert · Bondi" and "Nothing was sent" in _u["content"], _u)
at = app(res=(False, "The sheet is busy."))
btn(at, "chat_ok_a1").click().run()
_u = at.session_state["chat_history"][-1]
chk("⚠️ y si falla: marcada, y la tarjeta sigue", _u.get("app") == "confirm" and _u["content"] == "⚠️ The sheet is busy." and btn(at, "chat_ok_a1") is not None, _u)
CT.confirmar = _cf

sec("2. La memoria conserva la marca")
_h = [{"role": "user", "content": "close it", "at": "2026-11-03"},
      {"role": "assistant", "content": "Card ready.", "at": "2026-11-03"},
      {"role": "assistant", "content": "✅ Alert resolved.", "at": "2026-11-03", "app": "confirm", "card": "Close alert · Bondi"}]
_r = json.loads(json.dumps(CM.recortar(_h, HOY), ensure_ascii=False))
chk("⚠️ mañana sigue siendo de la app", _r[2].get("app") == "confirm" and _r[2].get("card") == "Close alert · Bondi", _r)
chk("lo demás, sin claves de más", set(_r[0]) == {"role", "content", "at"} and set(_r[1]) == {"role", "content", "at"}, _r[:2])

sec("3. Lo que le llega al modelo")
_m = CA._para_el_modelo(_h[2])
chk("⚠️ Confirm, como nota de la PERSONA, que dice que lo hizo la app", _m["role"] == "user" and _m["content"].startswith("[I pressed Confirm on the card «Close alert · Bondi».")
    and "The app, not you, handled it" in _m["content"] and "✅ Alert resolved." in _m["content"], _m)
_m = CA._para_el_modelo({"role": "assistant", "content": "Cancelled: x. Nothing was sent.", "app": "cancel", "card": "Notice · Bondi"})
chk("Cancel: que no se hizo nada", _m == {"role": "user", "content": "[I pressed Cancel on the card «Notice · Bondi». Nothing was done.]"}, _m)
chk("⚠️ lo que dijo el asistente, tal cual", CA._para_el_modelo(_h[1]) == {"role": "assistant", "content": "Card ready."})
chk("y la persona, tal cual", CA._para_el_modelo(_h[0]) == {"role": "user", "content": "close it"})
chk("⚠️ una conversación guardada antes de v645 (sin marca) sigue pasando", CA._para_el_modelo({"role": "assistant", "content": "✅ x"}) == {"role": "assistant", "content": "✅ x"})


def bloque(tipo, **k):
    return types.SimpleNamespace(type=tipo, **k)


_vistos = []


class _Msgs:
    def create(self, **kw):
        _vistos.append({**kw, "messages": list(kw["messages"])})
        return types.SimpleNamespace(content=[bloque("text", text="ok")], stop_reason="end_turn")


_man = types.SimpleNamespace(is_available=lambda: False)
# ⚠️ v655 · `**_kw`: el cliente de verdad lleva ahora timeout y max_retries (antes, solo la clave)
CA.anthropic = types.SimpleNamespace(Anthropic=lambda api_key=None, **_kw: types.SimpleNamespace(beta=types.SimpleNamespace(messages=_Msgs())),
                                     AuthenticationError=type("A", (Exception,), {}), RateLimitError=type("R", (Exception,), {}))
CA.st = types.SimpleNamespace(secrets={"ANTHROPIC_API_KEY": "x"})
sys.modules["core.manuals"] = _man
core.manuals = _man
for _rol, _us in (("administrator", "Admin2"), ("field", "campo000")):
    _vistos.clear()
    CA.get_chat_response("and now?", list(_h), None, None, rol=_rol, grupo="cliente1", usuario=_us, nombre="x", acciones=[])
    _ms = _vistos[0]["messages"]
    chk("⚠️ %s: la línea de la app llega como nota de la persona, y la pregunta detrás" % _rol,
        [m["role"] for m in _ms] == ["user", "assistant", "user", "user"] and _ms[2]["content"].startswith("[I pressed Confirm")
        and _ms[3]["content"] == "and now?", [(m["role"], str(m["content"])[:40]) for m in _ms])
    chk("⚠️ %s: a la API no le llegan claves de la app" % _rol, all(set(m) == {"role", "content"} for m in _ms), _ms)
_vistos.clear()
CA.get_chat_response("hi", [{"role": "assistant", "content": "✅ x", "app": "confirm", "card": "c"}], None, None, rol="administrator",
                     grupo="cliente1", usuario="Admin2", nombre="x", acciones=[])
chk("una conversación que empieza por la app empieza por la persona", _vistos[0]["messages"][0]["role"] == "user", _vistos[0]["messages"])

sec("4. Lo que se le dice")
_l = "Las notas entre corchetes que empiezan por «[I pressed Confirm» o «[I pressed Cancel» las escribe la APP"
for _k in ("field_tools", "office_tools"):
    _p = CA._PERSONA[_k].replace('"\n        "', "")
    chk("⚠️ %s: esas notas son de la app y pasaron de verdad; no negarlas ni reintentar" % _k,
        _l in _p and "lo que dicen pasó de verdad" in _p and "No las niegues" in _p and "no lo reintentes por tu cuenta" in _p)
chk("en pantalla, igual que antes: el historial se pinta con su rol", 'with st.chat_message(msg["role"]' in leer("app.py"))

print("\n=== verif_v645: %d OK, %d FALLOS ===" % (n_ok, len(fallos)))
for f in fallos:
    print("   -", f)
sys.exit(1 if fallos else 0)
