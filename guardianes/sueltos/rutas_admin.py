"""Las URLs de TODAS las pantallas del admin, sacadas del propio código (no a mano).

Escribirlas a mano garantizaría olvidarse de alguna — y el barrido serviría de poco si
la pantalla que falla es justo la que no está en mi lista.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrador", "nombre": "dmoreno"}

from core import home_ui as H                                     # noqa: E402

secs = H._secciones()
subs = H._subsecciones()
print(f"{len(secs)} secciones del rol administrador\n")
n = 0
for clave, _label in secs:
    lista = subs.get(clave)
    if not lista:
        print(f"?s={clave}")
        n += 1
        continue
    _k, opciones = lista
    for op in opciones:
        sid = op[0] if isinstance(op, (tuple, list)) else op
        print(f"?s={clave}&t={H._slug(sid)}    # {sid}")
        n += 1
print(f"\nTOTAL {n} pantallas")
