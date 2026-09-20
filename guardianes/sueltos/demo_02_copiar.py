"""PASO 2b — copiar las hojas de INQUILINO del maestro al libro de la demo.

NO borra nada del maestro: eso es el paso 6, y solo después de verificar.

⚠️ Se escribe con `value_input_option="RAW"`, como escribe la app entera. Con
USER_ENTERED, Google reinterpretaría «2026-08-01» como fecha serial y «0.19» según
la configuración regional — y los datos dejarían de leerse igual.
⚠️ Las hojas GLOBALES (Login, Grupos, Rieles, Manuales) se quedan en el maestro:
son el registro de la app, y `Login` además se lee ANTES de saber de qué grupo eres.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import gspread                                             # noqa: E402
import streamlit as st                                     # noqa: E402
from google.oauth2.service_account import Credentials      # noqa: E402
from gspread.utils import rowcol_to_a1                     # noqa: E402

from core.timeclock import SHEETS_GLOBALES                 # noqa: E402

DESTINO_ID = "1WHGCrZndwdmqrR3RehLh7jocOIVkRvjAbigifvfSe1Y"
MAESTRO_ID = str(st.secrets["TIMECLOCK_SHEET_ID"])
NOMBRE_NUEVO = "COPEX — DEMO (cliente1)"

assert DESTINO_ID != MAESTRO_ID, "‼️ destino y maestro son el mismo libro"

RW = ["https://www.googleapis.com/auth/spreadsheets"]
gc = gspread.authorize(Credentials.from_service_account_info(
    dict(st.secrets["gcp_service_account"]), scopes=RW))
src = gc.open_by_key(MAESTRO_ID)
dst = gc.open_by_key(DESTINO_ID)

# ── el nombre ───────────────────────────────────────────────────────
print("== nombre del libro ==")
print(f"   antes: «{dst.title}»")
try:
    if dst.title != NOMBRE_NUEVO:
        dst.update_title(NOMBRE_NUEVO)
        print(f"   ✓ ahora: «{NOMBRE_NUEVO}»")
except Exception as e:
    print(f"   ⚠️ no se pudo renombrar ({type(e).__name__}); renómbralo tú en Drive")

# ── qué se copia ────────────────────────────────────────────────────
inquilinas = [ws for ws in src.worksheets()
              if ws.title.strip().lower() not in SHEETS_GLOBALES]
globales = [ws.title for ws in src.worksheets()
            if ws.title.strip().lower() in SHEETS_GLOBALES]
print(f"\n== plan ==")
print(f"   se copian {len(inquilinas)} hojas de inquilino")
print(f"   se QUEDAN en el maestro (globales): {', '.join(globales)}")

destino_por_titulo = {ws.title: ws for ws in dst.worksheets()}
print("\n== copiando ==")
copiadas = {}
for ws in inquilinas:
    vals = ws.get_all_values()
    nfil = len(vals)
    ncol = max((len(r) for r in vals), default=1) or 1
    # rellenar filas cortas: `update` exige rectangular
    vals = [r + [""] * (ncol - len(r)) for r in vals]

    d = destino_por_titulo.get(ws.title)
    if d is None:
        d = dst.add_worksheet(title=ws.title, rows=max(nfil + 50, 100), cols=max(ncol, 8))
        destino_por_titulo[ws.title] = d
    d.clear()
    if d.row_count < nfil or d.col_count < ncol:
        d.resize(rows=max(nfil + 50, 100), cols=max(ncol, d.col_count))
    if nfil:
        rango = f"A1:{rowcol_to_a1(nfil, ncol)}"
        d.update(values=vals, range_name=rango, value_input_option="RAW")
    copiadas[ws.title] = max(0, nfil - 1)
    print(f"   {ws.title:<20} {max(0, nfil-1):>4} filas → copiadas")

# ── restos del ensayo de v359 que ya no pintan nada ─────────────────
sobrantes = [t for t in destino_por_titulo
             if t not in copiadas and t.strip().lower() not in SHEETS_GLOBALES]
if sobrantes:
    print(f"\n== restos del ensayo de v359 ==")
    for t in sobrantes:
        # No se borran hojas a lo loco: solo se vacían las que el ensayo creó y
        # que ninguna hoja del maestro reemplazó.
        destino_por_titulo[t].clear()
        print(f"   {t:<20} vaciada")

print(f"\n   ✓ {len(copiadas)} hojas copiadas · {sum(copiadas.values())} filas")
print("   (el maestro NO se ha tocado — eso es el paso 6, tras verificar)")
