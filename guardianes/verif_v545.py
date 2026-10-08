# -*- coding: utf-8 -*-
"""v545 · LA CAMPANA SE CIERRA AL LLEVARTE A UNA ALERTA, Y SU NÚMERO SE LEE.

Visto en producción verificando v544 con el admin (08/10/2026):

1. Tocar una alerta llevaba a la obra… con el popover ABIERTO encima de la pantalla de
   destino: su estado abierto vive en el navegador. → La clave del popover lleva generación
   y la sube cada alerta tocada: el popover nuevo nace cerrado.
2. A 846 px la columna de la campana da 62 px y Streamlit 1.64 recorta la etiqueta en una
   línea (trampa 33): «🔔 4» pedía 27 px de los 23 que dejaban 12+12 de relleno → «🔔‥».
   → 6+6 de relleno en el botón de la campana (medido en producción: cabe).
"""
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
AQUI = os.path.dirname(os.path.abspath(__file__))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.path.insert(0, AQUI)
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


def sec(x):
    print("\n%s" % x)


def _fuente(f):
    return io.open(os.path.join(RAIZ, f), encoding="utf-8").read()


from streamlit.testing.v1 import AppTest                          # noqa: E402


def corre(at):
    at.run()
    if at.exception:
        raise SystemExit("EXCEPCION: %s" % [e.value for e in at.exception][:2])
    return at


def ss(at, k, defecto=None):
    try:
        return at.session_state[k]
    except KeyError:
        return defecto


GUION = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
from core import home_ui as H, admin_digest as AD, credentials as C, inventory as INV, auth
st.session_state["auth"] = {"rol": "administrator", "usuario": "adm", "nombre": "Adm",
                            "grupo": "g"}
AD.group_digest = lambda g: {
    "retrasos": [{"id": "PRJ-1", "nombre": "Uno", "dias": 31}],
    "vencidos": [{"id": "PRJ-1", "nombre": "Uno", "fin": "2026-10-02", "dias": -6}],
    "alarmas": []}
C.is_configured = lambda: False
INV.is_configured = lambda: False
auth.list_users = lambda *a, **k: []
H._campana("g")
''' % RAIZ

sec("1. Tocar una alerta cierra la campana (el popover nuevo nace cerrado)")
_s = _fuente("core/home_ui.py")
chk("el popover de la campana lleva clave CON generación",
    "st.popover(label, width=\"stretch\", key=f\"cpxbell_{st.session_state.get('_bell_gen', 0)}\")"
    in _s)
at = corre(AppTest.from_string(GUION, default_timeout=120))
_g0 = ss(at, "_bell_gen", 0)
_b = [b for b in at.button if str(b.key or "").startswith("bell_")]
chk("la campana pinta sus alertas (no es un paso en vacío)", len(_b) == 2, len(_b))
next(b for b in _b if "overdue since" in b.label).click()
corre(at)
chk("⚠️ tocar una alerta sube la generación del popover (antes se quedaba abierto encima)",
    ss(at, "_bell_gen", 0) == _g0 + 1, (_g0, ss(at, "_bell_gen")))
chk("...y sigue llevando a la obra", ss(at, "_admin_open_proj") == "PRJ-1"
    and ss(at, "_admin_nav_pending") == ("proyectos", "📊 Proyectos"))
corre(at)
chk("pintar la campana sin tocar nada NO la cierra (la generación no sube sola)",
    ss(at, "_bell_gen", 0) == _g0 + 1, ss(at, "_bell_gen"))

sec("2. El número de la campana cabe en su columna")
_i = _s.find("def render_topbar")
_top = _s[_i:_s.find("\ndef ", _i + 10)]
chk("la regla va en la barra superior y SOLO al botón de la campana",
    ".st-key-cpxtop [data-testid='stPopoverButton']{padding-left:6px !important;" in _top
    and "padding-right:6px !important;}" in _top, _top[:200])
GUION_TOP = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
from core import home_ui as H
st.session_state["auth"] = {"rol": "administrator", "usuario": "adm", "nombre": "Adm",
                            "grupo": "g"}
H._campana = lambda g: None
H._banda_prestart = lambda: None
H._mobile_back_trap = lambda: None
H.render_topbar("g")
''' % RAIZ
at = corre(AppTest.from_string(GUION_TOP, default_timeout=120))
chk("...y llega a la página al pintar la barra",
    any("[data-testid='stPopoverButton']{padding-left:6px" in m.value for m in at.markdown))

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
