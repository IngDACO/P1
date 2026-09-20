"""PASO 2a — mirar el libro destino ANTES de escribir en él.

No toca nada: solo dice qué hay dentro (los restos del ensayo de v359) y confirma
que la cuenta de servicio llega. Lo que se decida borrar se hace en otro script,
para que este no pueda estropear nada.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import gspread                                             # noqa: E402
import streamlit as st                                     # noqa: E402
from google.oauth2.service_account import Credentials      # noqa: E402

DESTINO_ID = "1WHGCrZndwdmqrR3RehLh7jocOIVkRvjAbigifvfSe1Y"
MAESTRO_ID = str(st.secrets["TIMECLOCK_SHEET_ID"])

RO = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
gc = gspread.authorize(Credentials.from_service_account_info(
    dict(st.secrets["gcp_service_account"]), scopes=RO))

print("== ¿son libros distintos? ==")
print(f"   maestro : {MAESTRO_ID}")
print(f"   destino : {DESTINO_ID}")
if DESTINO_ID == MAESTRO_ID:
    print("   ‼️ ES EL MISMO LIBRO — abortar")
    sys.exit(1)
print("   ✓ distintos")

try:
    dst = gc.open_by_key(DESTINO_ID)
except Exception as e:
    print(f"\n   ‼️ no se puede abrir: {type(e).__name__}: {e}")
    print("      ¿está compartido con fichaje-bot@gen-lang-client-0922870449.iam.gserviceaccount.com?")
    sys.exit(1)

print(f"\n== contenido actual de «{dst.title}» ==")
total = 0
for ws in dst.worksheets():
    vals = ws.get_all_values()
    filas = max(0, len(vals) - 1)
    total += filas
    cab = ", ".join(vals[0][:6]) if vals else "(vacía)"
    print(f"   {ws.title:<20} {filas:>4} filas   cabecera: {cab[:64]}")
print(f"\n   {len(dst.worksheets())} hojas · {total} filas (restos del ensayo de v359)")

print("\n== el nombre ==")
print(f"   actual: «{dst.title}»")
if "borrar" in dst.title.lower():
    print("   ⚠️ dice «borrar»: hay que renombrarlo antes de que albergue la demo")
