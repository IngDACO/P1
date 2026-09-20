"""Foto del estado ANTES de ejercitar v430.

⚠️ SOLO LECTURA con gspread crudo y scope `readonly`: los helpers de la app MIGRAN
la cabecera al acceder (regla v145), así que auditar con ellos escribe.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))
import os                                                       # noqa: E402
os.chdir(RAIZ)

import gspread, toml                                            # noqa: E402
from google.oauth2.service_account import Credentials           # noqa: E402

GRUPO = "cliente1"
sec = toml.load(".streamlit/secrets.toml")
gc = gspread.authorize(Credentials.from_service_account_info(
    sec["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]))

# el libro del grupo (v359): se resuelve por Grupos.SheetID del maestro
maestro = gc.open_by_key(sec["TIMECLOCK_SHEET_ID"])
grupos = maestro.worksheet("Grupos").get_all_records(numericise_ignore=["all"])
sid = next((str(g.get("SheetID", "")) for g in grupos
            if str(g.get("Grupo", "")) == GRUPO), "") or sec["TIMECLOCK_SHEET_ID"]
sh = gc.open_by_key(sid)
print(f"Libro de {GRUPO}: {sh.title}\n")

hojas = {w.title for w in sh.worksheets()}
rangos = [f"'{t}'!A1:AZ2000" for t in
          ("Ausencias", "Nominas", "Sheet1", "Roster") if t in hojas]
lote = sh.values_batch_get(rangos)["valueRanges"]


def filas(i):
    v = lote[i].get("values") or []
    if not v:
        return [], []
    return v[0], v[1:]


idx = {t: i for i, t in enumerate(
    [t for t in ("Ausencias", "Nominas", "Sheet1", "Roster") if t in hojas])}

for t in ("Ausencias", "Nominas", "Sheet1", "Roster"):
    if t not in idx:
        print(f"{t:12} — la hoja NO existe todavía")
        continue
    cab, fs = filas(idx[t])
    print(f"{t:12} {len(fs):>4} filas")

if "Nominas" in idx:
    cab, fs = filas(idx["Nominas"])
    c = {h: i for i, h in enumerate(cab)}
    print("\nNóminas existentes (periodo · usuario · estado):")
    for f in fs:
        def g(k):
            return f[c[k]] if k in c and c[k] < len(f) else ""
        print(f"  {g('ID'):10} {g('PeriodoDesde')} → {g('PeriodoHasta')}  "
              f"{g('Usuario'):12} {g('Estado'):10} base {g('Base'):>10}")

# ¿quién tiene horas HOY? (lo que `generar` recogería para un periodo de hoy)
from core import clock                                          # noqa: E402
import streamlit as st                                          # noqa: E402
st.session_state["auth"] = {"usuario": "verif", "rol": "administrador",
                            "grupo": GRUPO, "nombre": "verif"}
hoy = clock.today(GRUPO)
print(f"\nHoy: {hoy} ({['lun','mar','mié','jue','vie','sáb','dom'][hoy.weekday()]})")

if "Sheet1" in idx:
    cab, fs = filas(idx["Sheet1"])
    c = {h: i for i, h in enumerate(cab)}
    hoy_s = str(hoy)
    n = 0
    for f in fs:
        ci = f[c["Clock In"]] if "Clock In" in c and c["Clock In"] < len(f) else ""
        if ci.startswith(hoy_s):
            n += 1
    print(f"Fichajes con Clock In de HOY: {n}")

from core import auth                                           # noqa: E402
print("\nTarifas del grupo:", auth.rate_map(GRUPO))
