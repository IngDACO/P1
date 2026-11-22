# -*- coding: utf-8 -*-
"""v693 · Lo visto cerrando el ciclo 5 con la sesión de campo (22/11): «My equipment» pintaba su propio título, y como
la shell ya pinta «Self-service · My equipment», salía DOS veces. Las otras de Self-service no lo llevan (v478, v627).

AppTest con sustitutos; nada sale a la red.
"""
import os
import sys

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:900]))
    if not cond:
        FALLOS.append(nombre)


from streamlit.testing.v1 import AppTest                                   # noqa: E402

G = r'''
import streamlit as st
from core import inventory_ui as IU, inventory as INV
INV.is_configured = lambda: True
INV.list_activos = lambda g, incluir_baja=False: [{"ID": "ACT-6", "Group": "G", "Name": "Chain hoist", "Status": "in use",
                                                   "AssignedTo": "campo000", "LocationType": "user", "LocationRef": "campo000",
                                                   "ReturnDate": "2026-11-25"}]
IU._nombres = lambda g: {"campo000": "hjg,ujgjg (campo000)"}
st.session_state.setdefault("auth", {"usuario": "campo000", "rol": "field", "grupo": "G", "nombre": "hjg,ujgjg"})
IU.render_equipo_campo("campo000", "G")
'''
at = AppTest.from_string(G, default_timeout=60).run()
chk("«My equipment» se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_md = [str(x.value) for x in at.markdown]
chk("CONTROL: la sonda ve la pantalla (la lista con el polipasto)", any("Chain hoist" in str(b.label) for b in at.button),
    [b.label for b in at.button])
chk("…y SIN título propio (la shell ya pinta «Self-service · My equipment»)",
    not any("My equipment" in m for m in _md), _md)

print("\n" + ("TODO OK" if not FALLOS else f"{len(FALLOS)} FALLO(S): {FALLOS}"))
sys.exit(1 if FALLOS else 0)
