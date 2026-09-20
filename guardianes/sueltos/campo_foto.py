"""FOTO del ANTES en SOLO LECTURA (gspread crudo, scope readonly).

⚠️ Regla v145: `projects._get_ws` MIGRA la cabecera al acceder — un "lector" que
escribe. Para auditar de verdad hay que ir por gspread crudo.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import gspread                                             # noqa: E402
import streamlit as st                                     # noqa: E402
from google.oauth2.service_account import Credentials      # noqa: E402

RO = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
cred = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=RO)
gc = gspread.authorize(cred)
libro = gc.open_by_key(st.secrets["TIMECLOCK_SHEET_ID"])

prj = libro.worksheet("Proyectos").get_all_records(numericise_ignore=["all"])
act = libro.worksheet("Actividades").get_all_records(numericise_ignore=["all"])

print("== proyectos de jlopez (campo) ==")
mios = [p for p in prj
        if "jlopez" in str(p.get("CampoAsignados", "")).lower()
        and str(p.get("Grupo", "")) == "cliente1"]
for p in mios:
    n = len([a for a in act if str(a.get("ProyectoID")) == str(p.get("ID"))])
    print(f"   {p.get('ID')}  {str(p.get('Nombre'))[:28]:<29} avance={str(p.get('Avance')):>6} "
          f"estado={str(p.get('Estado'))[:12]:<13} actividades={n:>2}  arch={p.get('EstadoManual')}")

print("\n== actividades, por proyecto (el candidato con más ramas por ejercitar) ==")
for p in mios:
    pid = str(p.get("ID"))
    filas = [a for a in act if str(a.get("ProyectoID")) == pid]
    if not filas:
        continue
    print(f"\n   {pid} · {p.get('Nombre')}")
    for a in filas:
        print(f"      orden={str(a.get('Orden')):>3}  {str(a.get('Nombre'))[:26]:<27} "
              f"av={str(a.get('Avance')):>6}  peso={str(a.get('Peso')):>5}  "
              f"ini={str(a.get('FechaInicioReal')) or '—':<11} fin={str(a.get('FechaFinReal')) or '—':<11} "
              f"nota={str(a.get('Nota'))[:18]!r}")
