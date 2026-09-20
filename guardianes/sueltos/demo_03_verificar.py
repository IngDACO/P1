"""PASO 3 — ¿el libro de la demo es IDÉNTICO al maestro? Celda a celda.

Es la puerta que decide si se borra algo. Si esto no sale perfecto, no se toca el
maestro.

⚠️ Se lee POR LOTES (`values_batch_get`), no hoja por hoja. La primera versión
pedía `src.worksheet(t)` en cada vuelta —y eso refetchea los metadatos del libro
cada vez— así que gastaba ~88 llamadas y **reventó con un 429** a dos hojas del
final. Es exactamente el problema que v339 resolvió dentro de la app, cometido en
el script que venía a verificarla. Ahora son 2 llamadas.

⚠️ Se normaliza el relleno antes de comparar: al escribir hubo que hacer las filas
rectangulares, así que el destino puede tener «» de más al final de una fila donde
el maestro no los tenía. Eso NO es una diferencia de datos.
"""
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import gspread                                             # noqa: E402
import streamlit as st                                     # noqa: E402
from google.oauth2.service_account import Credentials      # noqa: E402

from core.timeclock import SHEETS_GLOBALES                 # noqa: E402

DESTINO_ID = "1WHGCrZndwdmqrR3RehLh7jocOIVkRvjAbigifvfSe1Y"
MAESTRO_ID = str(st.secrets["TIMECLOCK_SHEET_ID"])

RO = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
gc = gspread.authorize(Credentials.from_service_account_info(
    dict(st.secrets["gcp_service_account"]), scopes=RO))


def con_reintento(fn, intentos=4):
    """El 429 es de CUOTA POR MINUTO: esperar y reintentar es la respuesta correcta."""
    for i in range(intentos):
        try:
            return fn()
        except gspread.exceptions.APIError as e:
            if "429" not in str(e) or i == intentos - 1:
                raise
            espera = 25 * (i + 1)
            print(f"   … 429 (cuota por minuto): esperando {espera}s")
            time.sleep(espera)


src = con_reintento(lambda: gc.open_by_key(MAESTRO_ID))
dst = con_reintento(lambda: gc.open_by_key(DESTINO_ID))

hojas_src = [ws.title for ws in src.worksheets()]          # ya cacheado por gspread
hojas_dst = [ws.title for ws in dst.worksheets()]
inquilinas = [t for t in hojas_src if t.strip().lower() not in SHEETS_GLOBALES]

faltan = [t for t in inquilinas if t not in hojas_dst]
if faltan:
    print(f"‼️ faltan en el destino: {faltan}")
    sys.exit(1)

# ⚠️ UNA llamada por libro (v339). `values_batch_get` rechaza la petición ENTERA si
#    un rango no existe, por eso arriba se comprueba que estén todas.
rangos = [f"'{t}'" for t in inquilinas]
r_src = con_reintento(lambda: src.values_batch_get(rangos))
r_dst = con_reintento(lambda: dst.values_batch_get(rangos))


def a_dict(resp):
    out = {}
    for tramo in (resp.get("valueRanges") or []):
        titulo = str(tramo.get("range", "")).split("!")[0].strip("'")
        out[titulo] = tramo.get("values") or []
    return out


A, B = a_dict(r_src), a_dict(r_dst)


def normaliza(vals):
    out = []
    for r in vals:
        r = list(r)
        while r and str(r[-1]).strip() == "":
            r.pop()
        out.append(r)
    while out and not out[-1]:
        out.pop()
    return out


print(f"== comparando {len(inquilinas)} hojas (2 llamadas, no 88) ==")
ok = True
tot = 0
for t in inquilinas:
    a, b = normaliza(A.get(t, [])), normaliza(B.get(t, []))
    if a == b:
        cel = sum(len(r) for r in a)
        tot += cel
        print(f"   ✓ {t:<20} {max(0,len(a)-1):>4} filas · {cel:>5} celdas idénticas")
        continue
    ok = False
    print(f"   ‼️ {t}: DIFIEREN — {len(a)} filas en maestro vs {len(b)} en destino")
    for i in range(max(len(a), len(b))):
        fa, fb = (a[i] if i < len(a) else None), (b[i] if i < len(b) else None)
        if fa != fb:
            print(f"      fila {i+1}\n        maestro: {str(fa)[:110]}\n        destino: {str(fb)[:110]}")
            break

print(f"\n   {tot} celdas verificadas")

print("\n== las hojas GLOBALES no deben estar en la demo ==")
coladas = [t for t in hojas_dst if t.strip().lower() in SHEETS_GLOBALES]
ok &= not coladas
print(f"   {'✓ ninguna colada' if not coladas else '‼️ coladas: ' + str(coladas)}")
print("   (Login se queda solo en el maestro: ahí se valida ANTES de saber tu grupo)")

print("\n" + ("✅ el libro de la demo es idéntico. Se puede continuar al paso 4"
              if ok else "⛔ NO CONTINUAR — el maestro no se toca"))
sys.exit(0 if ok else 1)
