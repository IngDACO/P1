"""¿Qué pasó con las sesiones de campo1 del 21/08? (solo lectura)"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrador"}

from core import finance as F                                     # noqa: E402
from core import invoices as I                                    # noqa: E402
from core import projects as P                                    # noqa: E402
from core import timeclock as T                                   # noqa: E402

filas = [r for r in T._cached_records()
         if str(r.get("Clock In", "")).startswith("2026-08-21")]
print(f"{len(filas)} fichajes del 21/08:")
for r in filas:
    print(f"   {str(r.get('Usuario')):<10} {str(r.get('Tipo')):<9} "
          f"in={r.get('Clock In')}  out={r.get('Clock Out')!r}  horas={r.get('Horas')!r}")

prj = P.get_project("PRJ-0005")
rev = F.project_revenue("PRJ-0005", "cliente1", prj)
print(f"\nPRJ-0005 · costo {rev.get('costo')} · ingreso {rev.get('ingreso')} "
      f"· pendiente {I.pendiente_de_facturar('PRJ-0005', 'cliente1', prj):,.2f}")
