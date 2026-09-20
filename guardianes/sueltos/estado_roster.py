"""¿Tiene la planificación algo que enseñar esta semana? (solo lectura)

De esto dependen: Panel, vista Día, Libres, Cumplimiento, Ruta del día y la agenda de
HOME. Si la semana está vacía, esas seis pantallas no se pueden probar.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrador", "nombre": "dmoreno"}

from core import auth, clock, roster as R                         # noqa: E402

G = "cliente1"
hoy = clock.today(G)
lunes = R.lunes_de(hoy)
print(f"hoy {hoy} · lunes de esta semana {lunes}\n")

campo = [u for u in auth.list_users() if str(u.get("Rol")) == "campo"
         and str(u.get("Grupo")) == G]
print(f"{len(campo)} personas de campo: {[str(u.get('Usuario')) for u in campo]}\n")

for k in (0, 1):
    import datetime as dt
    lu = lunes + dt.timedelta(days=7 * k)
    datos = R.get_semana(G, lu)
    con = 0
    conhora = 0
    for _u, d in (datos or {}).items():
        for dia in R.DIAS_TODOS:
            c = (d or {}).get(dia)
            if not c:
                continue
            items = c if isinstance(c, list) else [c]
            for it in items:
                if isinstance(it, dict) and it.get("asig"):
                    con += 1
                    if it.get("ini") or it.get("fin"):
                        conhora += 1
                elif isinstance(it, str) and it:
                    con += 1
    print(f"semana del {lu}: {len(datos or {})} personas con fila · "
          f"{con} asignaciones · {conhora} con franja horaria")

print(f"\ntrabajos del catálogo: {len(R.list_trabajos(G))}")
