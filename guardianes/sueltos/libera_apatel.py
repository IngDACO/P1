"""Deja a `apatel` sin asignar esta semana, para tener el caso «sin plan».

Lo necesitan: la línea de cobertura del Panel, la vista Libres y el «N sin plan» de la
Ruta del día. Tenía 1 asignación suelta de antes.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrador", "nombre": "dmoreno"}

from core import clock, roster as R                               # noqa: E402

G, USR = "cliente1", "apatel"
LUNES = R.lunes_de(clock.today(G))
antes = R.get_semana(G, LUNES)
print(f"antes: {sum(len(R.celda_items(antes, USR, d)) for d in R.DIAS_TODOS)} asignaciones")

ok, msg = R.guardar_persona(G, LUNES, USR, {})      # `_compact` omite lo vacío
print(f"guardar_persona(vacío) -> {ok} · {msg}")

R._invalidate()
desp = R.get_semana(G, LUNES)
print(f"después: {sum(len(R.celda_items(desp, USR, d)) for d in R.DIAS_TODOS)} asignaciones")
print(f"el resto sigue: {sum(len(R.celda_items(desp, u, d)) for u in desp for d in R.DIAS_TODOS)} en total")
