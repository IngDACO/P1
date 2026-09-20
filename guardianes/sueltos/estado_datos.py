"""¿Qué hay y qué falta en la demo para poder probar la app entera?

Simular a ciegas duplicaría lo que ya sembraron los `sim_*` de tandas anteriores. Esto
mide el estado ACTUAL por entidad, para llenar solo los huecos — y para saber qué
pantallas hoy no se pueden probar porque están vacías.

SOLO LECTURA.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrador", "nombre": "dmoreno"}
G = "cliente1"


def cuenta(nombre, fn):
    try:
        v = fn()
        n = len(v) if hasattr(v, "__len__") else v
        print(f"  {nombre:<26} {n}")
        return n
    except Exception as e:                                        # noqa: BLE001
        print(f"  {nombre:<26} ERROR: {str(e)[:70]}")
        return -1


from core import (alerts, auth, catalogo, clientes, credentials,   # noqa: E402
                  expenses, inventory, invoices, orders, payroll,
                  prestart, projects, quotes, roster, timeclock, toolruns)

print("== personas y accesos ==")
_u = auth.list_users()
cuenta("usuarios (todos)", lambda: _u)
print(f"  {'de campo':<26} {len([u for u in _u if str(u.get('Rol')) == 'campo'])}")
print(f"  {'con email':<26} {len([u for u in _u if str(u.get('Email', '')).strip()])}")
cuenta("credenciales del grupo", lambda: credentials.list_group(G))

print("\n== obra ==")
_p = projects.list_projects(G, incluir_archivados=True)
cuenta("proyectos (con archivados)", lambda: _p)
print(f"  {'activos':<26} "
      f"{len([x for x in _p if str(x.get('Estado')) not in ('Archivado', 'Cancelado')])}")
cuenta("agrupaciones", lambda: projects.list_groupings(G))
cuenta("trabajos del roster", lambda: roster.list_trabajos(G))
# ⚠️ `list_alerts(pid, estado)` y `list_prestarts(pid)` van POR PROYECTO, no por grupo:
# se suman sobre los proyectos (regla v135 — la firma, no el nombre que parece lógico).
cuenta("alarmas (todas las obras)",
       lambda: [a for x in _p for a in alerts.list_alerts(str(x.get("ID", "")))])
cuenta("pre-starts (todas las obras)",
       lambda: [a for x in _p for a in prestart.list_prestarts(str(x.get("ID", "")))])


print("\n== tiempo ==")
_f = timeclock._cached_records()
_g = [r for r in _f if str(r.get("Grupo", "")).strip().lower() == G]
print(f"  {'fichajes del grupo':<26} {len(_g)}")
print(f"  {'abiertos ahora':<26} "
      f"{len([r for r in _g if not str(r.get('Clock Out', '')).strip()])}")

print("\n== dinero ==")
cuenta("clientes", lambda: clientes.list_clientes(G))
cuenta("catálogo", lambda: catalogo.list_items(G))
cuenta("cotizaciones", lambda: quotes.list_cotizaciones(G))
cuenta("facturas", lambda: invoices.list_facturas(G))
cuenta("nóminas", lambda: payroll.list_nominas(G))
cuenta("órdenes de compra", lambda: orders.list_group(G))
cuenta("gastos (compras)",
       lambda: [g for x in _p for g in expenses.list_for(str(x.get("ID", "")))])

print("\n== inventario y herramientas ==")
cuenta("activos", lambda: inventory.list_activos(G, incluir_baja=True))
cuenta("categorías inventario", lambda: inventory.categorias(G))
cuenta("cálculos guardados",
       lambda: [t for x in _p for t in toolruns.list_for(str(x.get("ID", "")))])
cuenta("documentos",
       lambda: [d for x in _p for d in projects.list_documents(str(x.get("ID", "")))])
