# -*- coding: utf-8 -*-
"""v687 · LO VISTO CON LA SESIÓN DE CAMPO DE CAMPO000 (17/11/2026), cerrando los ciclos 3 y 4.

  1. «My route» (My projects): el mapa se dibujaba con el desplegable CERRADO (0 px); `fit_bounds` encuadraba con 0 px
     y al abrirlo salía el mundo entero con las dos obras en un punto sobre Sídney. Al cambiar de día sí encuadraba (el
     mapa se volvía a dibujar ya visible). Ahora el desplegable lleva `on_change="rerun"` y la ruta se pinta solo con
     él abierto: el mapa nace con su tamaño, y cerrado ni se lee el tablero.

Sin red: proyectos, tablero, fichaje y la ruta, sustituidos y contados.
"""
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "campo000", "nombre": "X", "rol": "field", "grupo": "cliente1"}
from streamlit.testing.v1 import AppTest                          # noqa: E402

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


sec("1. «My route»: la ruta (y su mapa) solo con el desplegable ABIERTO")
_pu = leer("core/projects_ui.py")
_i = _pu.index('key="exp_mi_ruta"')
_bloque = _pu[_i - 200:_i + 500]
chk("⚠️ el desplegable sabe si está abierto: `on_change=\"rerun\"`", 'key="exp_mi_ruta",\n' in _bloque
    and 'on_change="rerun")' in _bloque, _bloque[150:330])
chk("⚠️ y la ruta se pinta bajo `if _exp_ruta.open:`",
    "if _exp_ruta.open:" in _bloque and _bloque.index("if _exp_ruta.open:") < _bloque.index("route_ui.render_mi_ruta(usuario, grupo)"))

APP = r'''
import streamlit as st
ss = st.session_state
ss.setdefault("auth", {"usuario": "campo000", "nombre": "X", "rol": "field", "grupo": "cliente1"})
from core import projects as P, projects_ui as PU, roster, route_ui, timeclock
ss.setdefault("_ruta", 0)
P.is_configured = lambda: True
P.list_projects_for_field = lambda u, grupo=None, incluir_internos=False: []
roster.is_configured = lambda: False
timeclock.open_sessions = lambda n, g, u: {}
def _ruta(u, g):
    ss["_ruta"] += 1
    st.caption("RUTA PINTADA %s %s" % (u, g))
route_ui.render_mi_ruta = _ruta
PU.render_field_projects("campo000", "cliente1")
'''


def textos(at):
    return [str(c.value) for c in at.caption] + [str(m.value) for m in at.markdown]


at = AppTest.from_string(APP, default_timeout=120).run()
chk("My projects sin obras: sin excepción", not at.exception, [e.value for e in at.exception][:1])
_ex = [x for x in list(at.expander) + list(at.status) if "My route" in str(getattr(x, "label", ""))]
chk("el desplegable «My route» está", len(_ex) == 1, [getattr(x, "label", "") for x in list(at.expander)])
chk("⚠️ cerrado: la ruta NO se pinta (ni se lee el tablero)", at.session_state["_ruta"] == 0
    and not any("RUTA PINTADA" in x for x in textos(at)), at.session_state["_ruta"])
at.session_state["exp_mi_ruta"] = True
at.run()
chk("⚠️ abierto: la ruta se pinta, una vez, para quien entró", at.session_state["_ruta"] == 1
    and any("RUTA PINTADA campo000 cliente1" in x for x in textos(at)), (at.session_state["_ruta"], textos(at)[-3:]))
at.session_state["exp_mi_ruta"] = False
at.run()
chk("al cerrarlo, deja de pintarse", at.session_state["_ruta"] == 1 and not any("RUTA PINTADA" in x for x in textos(at)),
    at.session_state["_ruta"])
chk("sin excepción en todo el recorrido", not at.exception, [e.value for e in at.exception][:1])

sec("2. El Field assistant responde solo a lo que se le pide (lo de v679/v680, que no llegó al campo)")
from core import chat_agent as CA                                # noqa: E402
_q = "What is planned for me on Monday 23/11, and am I working this Friday 20/11?"
_ca = CA._idioma_tras_datos(_q, "field")
_of = CA._idioma_tras_datos(_q, "administrator")
_sin = CA._idioma_tras_datos(_q)
chk("⚠️ el campo lee, justo antes de responder, «Answer only that question… Do not bring up earlier turns…»",
    "Answer only that question" in _ca and "Do not bring up earlier turns of this conversation" in _ca
    and "«What is planned for me on Monday 23/11" in _ca, _ca)
chk("...detrás de lo del idioma, como la oficina", _ca.index("Do not comment on the language.") < _ca.index("Answer only"))
chk("la oficina, igual que antes; sin rol, sin él", "Answer only that question" in _of and "Answer only" not in _sin)
_g = CA._PERSONA["field_tools"]
chk("⚠️ y su guía lo dice: «Responde SOLO a lo que te pide ahora… ni corrijas por tu cuenta…»",
    "Responde SOLO a lo que te pide ahora. No comentes, repitas ni corrijas por tu cuenta" in _g
    and "era cierto con los datos de entonces" in _g, _g[-700:])
chk("la de la oficina sigue igual", "Responde SOLO a lo que te pide ahora." in CA._PERSONA["office_tools"])

sec("3. Ausencias: llevar «From» más allá de «To» arrastra «To» (My absences y el formulario de la oficina)")
import datetime                                                  # noqa: E402
from core import clock as _CK, ausencias as AU                    # noqa: E402
_CK.today = lambda *a, **k: datetime.date(2026, 11, 17)
_CK.now = lambda *a, **k: datetime.datetime(2026, 11, 17, 7, 0)
AU.periodo_saldo = lambda g, u, ref=None: {"desde": datetime.date(2026, 1, 1), "hasta": datetime.date(2026, 12, 31),
                                           "origen": "natural", "ingreso": None}
G3 = r'''
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "installer", "nombre": "installer CI 1", "rol": "field", "grupo": "cliente1"})
from core import ausencias as AU, ausencias_ui as AUI, flash, notify, alerts, auth
_F = st.session_state["_F"]
AU._records = lambda: _F
AU._invalidate = lambda: None
notify.notify_user = lambda *a, **k: {}
alerts._admins_and_owners = lambda g: ["Admin2"]
auth.list_users = lambda *a: [{"User": "installer", "Name": "installer CI 1", "Group": "cliente1"}]
flash.mostrar()
AUI.render_mis_ausencias()
'''


def _todo3(a):
    return " | ".join(str(x.value) for k in ("markdown", "caption", "info", "warning", "error", "success")
                      for x in getattr(a, k, []))


a = AppTest.from_string(G3, default_timeout=60)
a.session_state["_F"] = []
a.run()
chk("My absences: sin excepción", not a.exception, [e.value for e in a.exception][:1])
chk("nace con «From» y «To» en hoy (17/11)", a.date_input(key="aus_desde_0").value == datetime.date(2026, 11, 17)
    and a.date_input(key="aus_hasta_0").value == datetime.date(2026, 11, 17))
a.date_input(key="aus_desde_0").set_value(datetime.date(2026, 11, 20)).run()
chk("⚠️ «From» al viernes 20/11: «To» va con él (era «The end date cannot be earlier…» con el botón parado)",
    a.date_input(key="aus_hasta_0").value == datetime.date(2026, 11, 20) and "cannot be earlier" not in _todo3(a)
    and "This takes **1 day**" in _todo3(a), (a.date_input(key="aus_hasta_0").value, _todo3(a)[:300]))
chk("...y se puede enviar", not next(b for b in a.button if b.key == "aus_enviar").disabled)
a.date_input(key="aus_hasta_0").set_value(datetime.date(2026, 11, 18)).run()
chk("llevar «To» hacia atrás sigue avisando y no deja enviar", "The end date cannot be earlier" in _todo3(a)
    and next(b for b in a.button if b.key == "aus_enviar").disabled, _todo3(a)[:300])
a.date_input(key="aus_hasta_0").set_value(datetime.date(2026, 11, 25)).run()
a.date_input(key="aus_desde_0").set_value(datetime.date(2026, 11, 23)).run()
chk("«From» antes de «To»: «To» no se toca (sigue en el 25)", a.date_input(key="aus_hasta_0").value == datetime.date(2026, 11, 25),
    a.date_input(key="aus_hasta_0").value)
_au = leer("core/ausencias_ui.py")
chk("⚠️ el formulario de la OFICINA lleva lo mismo (sus claves)",
    'on_change=_hasta_no_antes, args=(f"aus_of_d_{_g}", f"aus_of_h_{_g}"))' in _au
    and 'on_change=_hasta_no_antes, args=(f"aus_desde_{_g}", f"aus_hasta_{_g}"))' in _au)

print("\n%s: %d ok, %d FALLO" % ("verif_v687", n_ok, len(fallos)))
if fallos:
    print("FALLOS:")
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("TODO OK")
