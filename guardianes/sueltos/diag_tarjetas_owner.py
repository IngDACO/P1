"""¿Qué MÁS de las tarjetas del propietario sale del libro equivocado?

Se compara, dato a dato, lo que ve el admin de cliente1 con lo que ve el
propietario. Cualquier diferencia es un hueco de fase 2 que queda por cubrir.
"""
import inspect
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                     # noqa: E402
from core import projects as P, alerts, expenses           # noqa: E402


def como(rol, g=""):
    st.session_state["auth"] = {"usuario": "u", "grupo": g, "rol": rol}
    st.session_state.pop("_tenant_grupo_activo", None)


def medir(etq):
    out = {}
    out["horas"] = len(P.project_hours_bulk("cliente1"))
    try:
        a = alerts.open_counts_all()
        out["alarmas"] = sum(a.values()) if isinstance(a, dict) else len(a or [])
    except Exception as e:
        out["alarmas"] = f"{type(e).__name__}"
    try:
        ge = expenses.group_expenses("cliente1")
        filas = ge.get("filas") if isinstance(ge, dict) else ge
        out["gastos_filas"] = len(filas or [])
        out["gastos_total"] = round(float(ge.get("compras_grupo", 0) or 0), 2) if isinstance(ge, dict) else "?"
    except Exception as e:
        out["gastos_filas"] = f"{type(e).__name__}: {e}"
    try:
        out["retrasos"] = len(P.gaps_by_group("cliente1") or {})
    except Exception as e:
        out["retrasos"] = f"{type(e).__name__}"
    print(f"   {etq:<12} " + "  ".join(f"{k}={v}" for k, v in out.items()))
    return out


print("== firma de open_counts_all ==")
print(f"   {inspect.signature(alerts.open_counts_all)}")

print("\n== comparación ==")
como("administrador", "cliente1")
a = medir("admin")
como("propietario")
b = medir("propietario")

print("\n== diferencias ==")
dif = [k for k in a if a[k] != b[k]]
if not dif:
    print("   ✓ el propietario ve lo mismo que el admin en todos los datos medidos")
else:
    for k in dif:
        print(f"   ‼️ {k}: admin={a[k]}  ·  propietario={b[k]}")

# ⚠️ Este chequeo encontró DOS huecos que la fase 2 se había dejado —las horas y las
# alarmas salían a 0 en la cartera del propietario— y ninguno aparecía en los tests
# de `list_projects`. La cartera se compone de varias fuentes: hay que compararlas
# TODAS contra lo que ve el admin del mismo grupo, no solo los proyectos.
print("\n" + ("✅ la cartera del propietario cuadra con la del admin"
              if not dif else "⚠️ quedan huecos de fase 2"))
sys.exit(0 if not dif else 1)
