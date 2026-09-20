"""PASO 6 — vaciar las hojas de INQUILINO del maestro. El paso irreversible.

Antes de borrar nada comprueba, en el momento, que la demo TIENE los datos. Si esa
comprobación no sale, no se toca una celda.

⚠️ Se conservan las CABECERAS (se limpia desde A2): así el libro maestro queda
listo para el primer cliente real sin que `get_sheet` tenga que recrear nada.
⚠️ Las globales (Login, Grupos, Rieles, Manuales) NI SE MENCIONAN en el rango.
⚠️ Un solo `values_batch_clear` para las 22 hojas: hacerlo hoja por hoja serían 44
llamadas contra un techo de 60/min — el 429 que ya reventó el verificador.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import gspread                                             # noqa: E402
import streamlit as st                                     # noqa: E402
from google.oauth2.service_account import Credentials      # noqa: E402

from core.timeclock import SHEETS_GLOBALES                 # noqa: E402

DEMO_ID = "1WHGCrZndwdmqrR3RehLh7jocOIVkRvjAbigifvfSe1Y"
MAESTRO_ID = str(st.secrets["TIMECLOCK_SHEET_ID"])
assert DEMO_ID != MAESTRO_ID

RW = ["https://www.googleapis.com/auth/spreadsheets"]
gc = gspread.authorize(Credentials.from_service_account_info(
    dict(st.secrets["gcp_service_account"]), scopes=RW))
src = gc.open_by_key(MAESTRO_ID)
dst = gc.open_by_key(DEMO_ID)

inquilinas = [ws.title for ws in src.worksheets()
              if ws.title.strip().lower() not in SHEETS_GLOBALES]

# ── PUERTA: la demo tiene que tener los datos AHORA MISMO ───────────
print("== puerta: ¿la demo tiene los datos? ==")
CLAVE = {"Sheet1": 484, "Proyectos": 16, "Nominas": 38, "Facturas": 9,
         "Actividades": 121, "Auditoria": 44}
r = dst.values_batch_get([f"'{t}'" for t in CLAVE])
hay = {}
for tramo in (r.get("valueRanges") or []):
    t = str(tramo.get("range", "")).split("!")[0].strip("'")
    hay[t] = max(0, len(tramo.get("values") or []) - 1)
puerta = True
for t, esperado in CLAVE.items():
    n = hay.get(t, 0)
    b = n >= esperado
    puerta &= b
    print(f"   {'✓' if b else '‼️'} {t:<14} {n:>4} filas (esperaba ≥{esperado})")
if not puerta:
    print("\n⛔ La demo NO tiene los datos. NO se toca el maestro.")
    sys.exit(1)
print("   ✓ puerta superada")

# ── el borrado ──────────────────────────────────────────────────────
print(f"\n== vaciando {len(inquilinas)} hojas del maestro (desde A2) ==")
# ⚠️ La firma es `values_batch_clear(params, body)`: pasarle la lista suelta la mete
#    como PARAMS y revienta dentro de `requests` con un «too many values to unpack»
#    que no dice nada. La lista va en el BODY. (Falló así una vez; el maestro quedó
#    intacto porque el error ocurre antes de enviar nada.)
rangos = [f"'{t}'!A2:ZZ" for t in inquilinas]
src.values_batch_clear(body={"ranges": rangos})
print("   ✓ hecho en 1 llamada")
for t in inquilinas:
    print(f"      {t}")

globales = [ws.title for ws in src.worksheets()
            if ws.title.strip().lower() in SHEETS_GLOBALES]
print(f"\n   INTACTAS (globales): {', '.join(globales)}")
print("   respaldo en disco: C:\\Users\\diego\\respaldo_sheets\\")
