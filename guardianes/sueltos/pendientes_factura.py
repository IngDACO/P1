"""¿Cuánto dinero hay sin facturar, y en cuántas obras? — dato antes de proponer."""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrador"}

from core import projects as P                                   # noqa: E402
from core import invoices as I                                   # noqa: E402

G = "cliente1"
fact = I.facturado_por_proyecto(G)
filas = []
for p in P.list_projects(G, incluir_archivados=True):
    pid = str(p.get("ID", ""))
    try:
        pend = I.pendiente_de_facturar(pid, G, p)
    except Exception as e:
        pend = 0.0
        print("  (error en", pid, e, ")")
    ya = fact.get(pid, 0.0)
    filas.append((pid, str(p.get("Nombre", ""))[:26], str(p.get("Estado", "")),
                  round(pend, 2), round(ya, 2)))

filas.sort(key=lambda r: -r[3])
print(f"{'ID':<10}{'obra':<28}{'estado':<13}{'pendiente':>12}{'facturado':>12}")
for f in filas:
    print(f"{f[0]:<10}{f[1]:<28}{f[2]:<13}{f[3]:>12,.2f}{f[4]:>12,.2f}")

_con = [f for f in filas if f[3] > 0]
print(f"\n   obras totales:            {len(filas)}")
print(f"   con algo PENDIENTE:       {len(_con)}")
print(f"   dinero sin facturar:      {sum(f[3] for f in _con):,.2f}")
print(f"   ya facturado:             {sum(f[4] for f in filas):,.2f}")
_arch = [f for f in _con if f[2] == "Archivado"]
print(f"   …de ellas ARCHIVADAS:     {len(_arch)}  ({sum(f[3] for f in _arch):,.2f})")

# ¿cuántos clics cuesta hoy facturar una obra desde la cartera?
print("\n== Camino actual (medido en el código) ==")
print("   cartera → abrir la obra → sub-pestaña 💰 Costos → «Facturar esta obra»")
print("   = 3 clics antes de llegar al botón, y el atajo está al FINAL de Costos,")
print("     debajo de la tabla de mano de obra y de la ganancia por persona.")
