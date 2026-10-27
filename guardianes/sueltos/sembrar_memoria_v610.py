# -*- coding: utf-8 -*-
"""Siembra de la memoria del agente (v610): lo que ya se REVISÓ de partes que leyó el agente
(registro `Proposals` con `lector` del modelo) y la regla del motor que decidió el usuario.

    py -3.12 sueltos/sembrar_memoria_v610.py            → EN SECO: qué aprendería
    py -3.12 sueltos/sembrar_memoria_v610.py --aplicar  → lo escribe en AgentMemory (maestro)

⚠️ Con `--aplicar` ESCRIBE en la hoja global `AgentMemory` (la crea si falta). Lo demás, en solo
lectura. Se puede correr una vez: lo ya aprendido de un parte no se vuelve a sumar (mira `LogID`).
"""
import json
import os
import sys

RAIZ = r"C:\Users\diego\P1\survey_app"
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "siembra-v610", "nombre": "Memory seed v610",
                            "rol": "owner", "grupo": ""}
import gspread                                                    # noqa: E402
import tomllib                                                    # noqa: E402
from google.oauth2.service_account import Credentials            # noqa: E402

from core import agente_memoria as MEM                            # noqa: E402

APLICAR = "--aplicar" in sys.argv
REGLA = ("installed motor", "Install motor (machine)")
SEC = tomllib.load(open(os.path.join(RAIZ, ".streamlit", "secrets.toml"), "rb"))
gc = gspread.authorize(Credentials.from_service_account_info(
    dict(SEC["gcp_service_account"]), scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]))
m = gc.open_by_key(SEC["TIMECLOCK_SHEET_ID"])
grupos = [(str(g.get("Group", "")).strip(), str(g.get("SheetID", "")).strip() or SEC["TIMECLOCK_SHEET_ID"])
          for g in m.worksheet("Groups").get_all_records() if str(g.get("Group", "")).strip()]
try:
    ya = {str(r.get("LogID", "")) for r in m.worksheet(MEM.SHEET).get_all_records()}
except Exception:
    ya = set()

lotes = []
for g, sid in grupos:
    for r in gc.open_by_key(sid).worksheet("DailyLogs").get_all_records(numericise_ignore=["all"]):
        try:
            d = json.loads(str(r.get("Proposals", "") or "{}"))
        except ValueError:
            continue
        if not str(d.get("lector", "")).startswith("claude-") or d.get("nada"):
            continue
        if str(r.get("ID")) in ya:
            print("  %s: ya aprendido, se salta" % r.get("ID"))
            continue
        obs = MEM.observaciones(d.get("destinos"))
        lotes.append((g, str(r.get("ReviewedBy", "")), str(r.get("ID")), obs))
        print("  %s (%s): %s" % (r.get("ID"), g, obs))
print("Regla: «%s» → %s" % REGLA)
if not APLICAR:
    print("\n(en seco: nada escrito)")
    sys.exit(0)
for g, autor, lid, obs in lotes:
    print("  %s:" % lid, MEM.aprender(obs, g, autor, lid))
print("  regla:", MEM.poner_regla(REGLA[0], REGLA[1], "", "owner (user's decision, 27/10/2026)"))
