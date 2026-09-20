"""¿Cuánto cuesta poner «pendiente de facturar» en CADA FILA de la cartera?

Regla de v142: antes de meter un dato derivado en una LISTA, medir cuánto cuesta
calcularlo por fila. `pendiente_de_facturar` llama a `project_revenue`, que consulta
cotizaciones, ganancias por hora, mano de obra y compras. Con 16 obras eso puede ser
16 cadenas de cálculo en CADA rerun de la cartera.
"""
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrador"}

from core import projects as P                                   # noqa: E402
from core import invoices as I                                   # noqa: E402
from core import hojas                                           # noqa: E402

G = "cliente1"

# ── contar las llamadas REALES a la API, no suponer ──
import gspread                                                   # noqa: E402
_orig = gspread.http_client.HTTPClient.request
_n = {"api": 0}


def _cuenta(self, *a, **k):
    _n["api"] += 1
    return _orig(self, *a, **k)


gspread.http_client.HTTPClient.request = _cuenta

proys = P.list_projects(G, incluir_archivados=True)
print(f"obras: {len(proys)}")

# 1) en FRÍO (cachés vacías), como al entrar por primera vez
st.cache_data.clear()
_n["api"] = 0
t0 = time.perf_counter()
fact = I.facturado_por_proyecto(G)
for p in proys:
    I.pendiente_de_facturar(str(p.get("ID", "")), G, p)
t_frio = time.perf_counter() - t0
api_frio = _n["api"]

# 2) en CALIENTE (lo normal: un rerun cualquiera con las cachés vivas)
_n["api"] = 0
t0 = time.perf_counter()
fact = I.facturado_por_proyecto(G)
for p in proys:
    I.pendiente_de_facturar(str(p.get("ID", "")), G, p)
t_cal = time.perf_counter() - t0
api_cal = _n["api"]

gspread.http_client.HTTPClient.request = _orig

print(f"\n   FRÍO     : {t_frio * 1000:8.0f} ms · {api_frio} llamadas a Sheets")
print(f"   CALIENTE : {t_cal * 1000:8.0f} ms · {api_cal} llamadas a Sheets")
print(f"   por obra (caliente): {t_cal / max(1, len(proys)) * 1000:.1f} ms")

print("\n== Veredicto ==")
if api_cal == 0 and t_cal < 0.35:
    print("   ✓ Se puede poner en la tabla: 0 llamadas nuevas y coste despreciable")
    print("     en el rerun normal (todo sale de cachés ya vivas).")
elif api_cal == 0:
    print(f"   ⚠️ 0 llamadas, pero {t_cal * 1000:.0f} ms de CPU por render:")
    print("      conviene cachearlo como mapa (patrón `project_hours_bulk`).")
else:
    print(f"   ⚠️ {api_cal} llamadas a Sheets POR RENDER: NO va en la tabla sin")
    print("      un mapa cacheado (el problema que resolvió `gaps_by_group` en v107).")
