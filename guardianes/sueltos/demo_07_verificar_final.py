"""PASO 7 — la prueba decisiva.

Con el maestro VACÍO, que la app siga dando las mismas cifras solo puede
significar una cosa: las está leyendo del libro de la demo. Hasta ahora los dos
libros tenían lo mismo y ninguna cifra probaba nada.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import gspread                                             # noqa: E402
import streamlit as st                                     # noqa: E402
from google.oauth2.service_account import Credentials      # noqa: E402

st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1", "rol": "administrador"}

from core.timeclock import SHEETS_GLOBALES                 # noqa: E402
from core import projects as P, finance as F, auth, timeclock   # noqa: E402

MAESTRO_ID = str(st.secrets["TIMECLOCK_SHEET_ID"])
DEMO_ID = "1WHGCrZndwdmqrR3RehLh7jocOIVkRvjAbigifvfSe1Y"
ok = True

RO = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
gc = gspread.authorize(Credentials.from_service_account_info(
    dict(st.secrets["gcp_service_account"]), scopes=RO))
m = gc.open_by_key(MAESTRO_ID)

print("== 1. el maestro: vacío de datos de inquilino, globales intactas ==")
titulos = [w.title for w in m.worksheets()]
r = m.values_batch_get([f"'{t}'" for t in titulos])
filas = {}
for tramo in (r.get("valueRanges") or []):
    t = str(tramo.get("range", "")).split("!")[0].strip("'")
    filas[t] = max(0, len(tramo.get("values") or []) - 1)
    cab = (tramo.get("values") or [[]])[0]
    filas[t + "__cab"] = len(cab)

for t in titulos:
    es_global = t.strip().lower() in SHEETS_GLOBALES
    n, ncab = filas.get(t, 0), filas.get(t + "__cab", 0)
    if es_global:
        bien = True
        print(f"   GLOBAL   {t:<18} {n:>3} filas  (intacta)")
    else:
        bien = n == 0 and ncab > 0        # sin datos PERO con cabecera
        ok &= bien
        print(f"   {'✓' if bien else '‼️'} inquilino {t:<15} {n:>3} filas · "
              f"cabecera de {ncab} columnas")

print("\n== 2. ⚠️ LA PRUEBA: la app sigue viendo los datos (del libro de la demo) ==")
ESPERADO = {"obras": 16, "facturado": 101157.21, "costo_total": 92630.61,
            "ganancia": 8526.60, "por_cobrar": 69742.01}
try:
    proys = P.list_projects(grupo="cliente1", incluir_archivados=True)
    pnl = F.pnl("cliente1")
    got = {"obras": len(proys), "facturado": pnl["facturado"],
           "costo_total": pnl["costo_total"], "ganancia": pnl["ganancia"],
           "por_cobrar": pnl["por_cobrar"]}
    for k, esp in ESPERADO.items():
        v = got[k]
        bien = (v == esp) if k == "obras" else abs(v - esp) < 0.01
        ok &= bien
        fmt = (lambda x: f"{x}") if k == "obras" else (lambda x: f"${x:,.2f}")
        print(f"   {'✓' if bien else '‼️'} {k:<12} {fmt(v):>14}  (esperado {fmt(esp)})")
except Exception as e:
    ok = False
    print(f"   ‼️ {type(e).__name__}: {e}")

print("\n== 3. el enrutado sigue en su sitio ==")
for hoja, esperado, etq in [("Proyectos", DEMO_ID, "DEMO"), ("Login", MAESTRO_ID, "MAESTRO")]:
    got = timeclock.sheet_id_para(hoja, "cliente1")
    bien = got == esperado
    ok &= bien
    print(f"   {'✓' if bien else '‼️'} {hoja:<10} → {etq}")

print("\n== 4. el login sigue funcionando (Login es global) ==")
us = auth.list_users()
ok &= len(us) == 13
print(f"   {'✓' if len(us) == 13 else '‼️'} {len(us)} cuentas en el maestro")

print("\n" + ("✅ MIGRACIÓN COMPLETA: la demo vive en su libro, el maestro queda limpio "
              "para el primer cliente real" if ok else "⛔ REVISAR — hay respaldo en disco"))
sys.exit(0 if ok else 1)
