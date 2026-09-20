"""Corrige las 86,83 h fantasma de `campo1` del 21/08.

La sesión olvidada se cerró con «ahora» (24/08 21:34), así que quedaron **86,83 horas
por sesión** de un turno que empezó el 21 a las 06:44 — 3 días y medio que nadie
trabajó. Es justo el registro que v164 evita cerrando a la hora que dice la persona.

El usuario: «ponle cualquier hora, ahora no es importante». Se pone **15:30 del 21/08**
(8,75 h de jornada, plausible) y se DICE cuál. Empresa simulada; en producción esa hora
la pone quien trabajó, no yo.

En seco por defecto; `--apply` escribe.
"""
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

SALIDA = "2026-08-21 15:30:00"
HORAS = "8.75"                                   # 06:44:44 → 15:30:00
APLICAR = "--apply" in sys.argv

ws, err = T._get_worksheet()
if err:
    print("no se pudo abrir la hoja:", err)
    sys.exit(2)
filas = ws.get_all_records(numericise_ignore=["all"])
cab = ws.row_values(1)
col_out = cab.index("Clock Out") + 1
col_h = cab.index("Horas") + 1

objetivo = [(i, r) for i, r in enumerate(filas)
            if str(r.get("Usuario", "")) == "campo1"
            and str(r.get("Clock In", "")).startswith("2026-08-21")
            and str(r.get("Clock Out", "")).startswith("2026-08-24")]
print(f"{len(objetivo)} filas a corregir:")
for i, r in objetivo:
    print(f"   fila {i + 2}: {r.get('Tipo')} · in={r.get('Clock In')} "
          f"· out={r.get('Clock Out')} · horas={r.get('Horas')}  →  {SALIDA} · {HORAS} h")

prj = P.get_project("PRJ-0005")
print(f"\nANTES · PRJ-0005 costo {F.project_revenue('PRJ-0005', 'cliente1', prj)['costo']}"
      f" · pendiente {I.pendiente_de_facturar('PRJ-0005', 'cliente1', prj):,.2f}")

if not APLICAR:
    print("\n(en seco — repetir con --apply)")
    sys.exit(0)

for i, _r in objetivo:
    ws.update_cell(i + 2, col_out, SALIDA)
    ws.update_cell(i + 2, col_h, HORAS)
T._invalidate_records()
try:
    from core import hojas
    hojas.invalidar()
except Exception:
    pass

st.cache_data.clear()
prj = P.get_project("PRJ-0005")
print(f"DESPUÉS · PRJ-0005 costo {F.project_revenue('PRJ-0005', 'cliente1', prj)['costo']}"
      f" · pendiente {I.pendiente_de_facturar('PRJ-0005', 'cliente1', prj):,.2f}")
print("\nsesiones abiertas:",
      len([r for r in T._cached_records()
           if str(r.get("Grupo", "")).strip().lower() == "cliente1"
           and not str(r.get("Clock Out", "")).strip()]))
