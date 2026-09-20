"""Las tarjetas del propietario muestran 0h. ¿De dónde salen esas horas?"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                     # noqa: E402
from core import projects as P, tenant                     # noqa: E402


def como(rol, g=""):
    st.session_state["auth"] = {"usuario": "u", "grupo": g, "rol": rol}
    st.session_state.pop("_tenant_grupo_activo", None)


print("== como ADMIN de cliente1 (su libro) ==")
como("administrador", "cliente1")
h = P.project_hours_bulk("cliente1")
print(f"   project_hours_bulk → {len(h)} proyectos con horas")
for pid, v in list(h.items())[:5]:
    print(f"      {pid}: {v:.1f} h")

print("\n== como PROPIETARIO (sesión sin grupo) ==")
como("propietario")
h2 = P.project_hours_bulk("cliente1")
print(f"   project_hours_bulk('cliente1') → {len(h2)} proyectos con horas")
for pid, v in list(h2.items())[:5]:
    print(f"      {pid}: {v:.1f} h")

print("\n== y el fichaje crudo que ve cada uno ==")
como("administrador", "cliente1")
print(f"   admin  → {len(P._fichaje_records())} fichajes")
como("propietario")
print(f"   dueño  → {len(P._fichaje_records())} fichajes")
with tenant.como_grupo("cliente1"):
    print(f"   dueño dentro de como_grupo('cliente1') → {len(P._fichaje_records())} fichajes")

print("\n== ¿y otras cifras de las tarjetas? ==")
from core import alerts, expenses                          # noqa: E402
como("propietario")
try:
    print(f"   alarmas abiertas (dueño): {len(alerts.open_counts_all('cliente1') or {})}")
except Exception as e:
    print(f"   alarmas: {type(e).__name__}: {e}")
try:
    ge = expenses.group_expenses("cliente1")
    print(f"   group_expenses (dueño): {len(ge.get('filas', ge) if isinstance(ge, dict) else ge)} entradas")
except Exception as e:
    print(f"   group_expenses: {type(e).__name__}: {e}")
