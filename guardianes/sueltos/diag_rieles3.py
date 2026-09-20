"""¿Escribe `rails` en un libro y lee de otro?

`rails._ws()` abre la hoja con `timeclock._get_worksheet()` (el lector antiguo) y luego
`ss.worksheet("Rieles")`. La LECTURA, en cambio, va por `hojas.registros`, que resuelve
el libro con `timeclock.sheet_id_para("Rieles")` — y `Rieles` es una hoja GLOBAL, o sea
el maestro. Si los dos libros no son el mismo, escribir y leer van a sitios distintos.

SOLO LECTURA de metadatos: no escribe nada.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrador"}

from core import rails, timeclock                                 # noqa: E402

w, err = rails._ws()
libro_escritura = w.spreadsheet.id if w is not None else f"(error: {err})"
libro_lectura = timeclock.sheet_id_para(rails.RIELES_SHEET)
maestro = timeclock._sheet_maestro()
del_grupo = timeclock.sheet_id_para("Proyectos", "cliente1")

print(f"libro donde ESCRIBE rails._ws()      : {libro_escritura}")
print(f"libro de donde LEE  hojas.registros  : {libro_lectura}")
print(f"maestro                              : {maestro}")
print(f"libro del grupo cliente1 (Proyectos) : {del_grupo}")
print()
if libro_escritura == libro_lectura:
    print("COINCIDEN → el fallo del riel es otra cosa")
else:
    print("⚠️ NO COINCIDEN: `rails` escribe en un libro y lee de otro.")
    print("   Efecto: un riel añadido no se encuentra nunca al cargar un plano,")
    print("   así que RAIL se queda en 0 — el síntoma que v157 dio por resuelto.")

# ¿cuántos rieles ve cada camino?
try:
    print(f"\nrieles leyendo por hojas.registros : {len(rails.list_rieles())}")
    print(f"rieles leyendo la hoja escrita     : "
          f"{len(w.get_all_records(numericise_ignore=['all'])) if w else 'n/d'}")
except Exception as e:                                            # noqa: BLE001
    print("no se pudo contar:", e)
