"""¿Por qué el check dice que nadie está sin asignar?"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrador", "nombre": "dmoreno"}

from core import auth, clock, roster as R                         # noqa: E402

G = "cliente1"
LUNES = R.lunes_de(clock.today(G))
datos = R.get_semana(G, LUNES)

campo = [str(u.get("Usuario")) for u in auth.list_users()
         if str(u.get("Rol")) == "campo" and str(u.get("Grupo")) == G]
print(f"campo ({len(campo)}): {campo}")
print(f"filas en la semana: {sorted(datos)}\n")
for u in campo:
    n = sum(len(R.celda_items(datos, u, d)) for d in R.DIAS_TODOS)
    print(f"  {u:<12} {n} asignaciones{'   ← LIBRE' if n == 0 else ''}")
