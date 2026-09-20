"""PASO 1 — copia de seguridad del libro maestro a disco, ANTES de tocar nada.

⚠️ Los ZIP del despliegue guardan el CÓDIGO, no los datos. Antes de mover 838
filas y vaciar el maestro quiero una red en disco que no dependa de Google.

Solo lectura (scope `readonly`, regla v145): se guarda TODO tal cual —valores
crudos, sin interpretar— para poder reconstruir cualquier hoja si algo sale mal.
"""
import csv
import json
import pathlib
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import gspread                                             # noqa: E402
import streamlit as st                                     # noqa: E402
from google.oauth2.service_account import Credentials      # noqa: E402

DESTINO = pathlib.Path(r"C:\Users\diego\P1\respaldo_sheets") / datetime.now().strftime("%Y%m%d_%H%M")
DESTINO.mkdir(parents=True, exist_ok=True)

RO = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
gc = gspread.authorize(Credentials.from_service_account_info(
    dict(st.secrets["gcp_service_account"]), scopes=RO))
libro = gc.open_by_key(st.secrets["TIMECLOCK_SHEET_ID"])

print(f"libro : {libro.title}")
print(f"destino: {DESTINO}\n")

resumen = {}
for ws in libro.worksheets():
    # `get_all_values` = las celdas TAL CUAL, sin cabeceras ni conversiones: es lo
    # que hace falta para poder restaurar, no para analizar.
    vals = ws.get_all_values()
    f = DESTINO / f"{ws.title}.csv"
    with open(f, "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(vals)
    filas = max(0, len(vals) - 1)              # sin la cabecera
    resumen[ws.title] = {"filas": filas, "columnas": len(vals[0]) if vals else 0}
    print(f"   {ws.title:<20} {filas:>4} filas × {resumen[ws.title]['columnas']:>2} col")

(DESTINO / "_resumen.json").write_text(
    json.dumps({"libro": libro.title, "id": libro.id, "hojas": resumen,
                "fecha": datetime.now().isoformat(timespec="seconds")},
               ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n   {len(resumen)} hojas · {sum(v['filas'] for v in resumen.values())} filas guardadas")
print(f"   ✓ respaldo en {DESTINO}")
