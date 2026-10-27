# -*- coding: utf-8 -*-
"""Migración de v609: pasa las obras del juego de pesos «2026-09-22» al de hoy, A PROPÓSITO,
con `stage_progress.migrar_catalogo` (decisión del usuario, 27/10/2026: «Install motor (machine)»
5 % sacado de «Install motor bedplate» y la etapa renombrada «Shaft Climb, Bedplate & Motor»).

    py -3.12 sueltos/migrar_v609_catalogo.py            → EN SECO: qué haría y cuánto se mueve
    py -3.12 sueltos/migrar_v609_catalogo.py --aplicar  → copia en D: y migra

⚠️ Con `--aplicar` ESCRIBE en la hoja real (Projects, Activities, AuditTrail). Antes guarda una
copia de Projects, Activities y StageProgress de cada libro en D:\\CopeX\\respaldos (fuera del
repo). Lo leído para el ensayo, en SOLO LECTURA.
"""
import io
import json
import os
import sys
import time

RAIZ = r"C:\Users\diego\P1\survey_app"
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "migracion-v609", "nombre": "Catalogue migration v609",
                            "rol": "owner", "grupo": ""}
import gspread                                                    # noqa: E402
import tomllib                                                    # noqa: E402
from google.oauth2.service_account import Credentials            # noqa: E402

from core import projects as P                                    # noqa: E402
from core import stage_progress as SP                             # noqa: E402
from core import stages as S                                      # noqa: E402
from core import tenant                                           # noqa: E402

APLICAR = "--aplicar" in sys.argv
SEC = tomllib.load(open(os.path.join(RAIZ, ".streamlit", "secrets.toml"), "rb"))
gc = gspread.authorize(Credentials.from_service_account_info(
    dict(SEC["gcp_service_account"]), scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]))
m = gc.open_by_key(SEC["TIMECLOCK_SHEET_ID"])
grupos = [(str(g.get("Group", "")).strip(), str(g.get("SheetID", "")).strip() or SEC["TIMECLOCK_SHEET_ID"])
          for g in m.worksheet("Groups").get_all_records() if str(g.get("Group", "")).strip()]

copia, plan_trabajo = {}, []
for g, sid in grupos:
    L = gc.open_by_key(sid)
    hojas = {h: L.worksheet(h).get_all_records(numericise_ignore=["all"])
             for h in ("Projects", "Activities", "StageProgress")}
    copia[g] = hojas
    for prj in hojas["Projects"]:
        pl = P.plan_etapas(prj)
        if not pl or str(pl.get("version", "")) == S.VERSION:
            continue
        pid = str(prj.get("ID", ""))
        _v = str(pl.get("version", ""))
        _mig = S.MIGRABLES.get(_v)
        nuevo = dict(prj, StagePlanJSON=json.dumps(dict(pl, version=S.VERSION)))
        plan = SP.plan_de_obra(nuevo)
        mapa = {(int(float(r["StageOrder"])), str(r["Activity"])): float(r.get("Pct") or 0)
                for r in hojas["StageProgress"] if str(r.get("ProjectID")) == pid}
        det = {e["orden"]: e for e in SP._sobre(plan, mapa)}
        acts = [dict(a) for a in hojas["Activities"] if str(a.get("ProjectID")) == pid]
        cambios = []
        for k in (_mig or {}).get("etapas") or ():
            o = next((i for i, e in enumerate(plan, start=1) if (e["pista"], e["numero"]) == k), None)
            if o is None:
                continue
            fila = next((a for a in acts if str(a.get("Order")) == str(o)), {})
            cambios.append((o, fila.get("Name"), fila.get("Progress"), det[o]["pct"]))
            fila["Progress"] = det[o]["pct"]
        plan_trabajo.append({"grupo": g, "pid": pid, "nombre": prj.get("Name"), "version": _v,
                             "migrable": bool(_mig), "cambios": cambios,
                             "avance_antes": prj.get("Progress"), "avance_despues": P.compute_avance(acts),
                             "prj": prj})

print("Juego de hoy: %s · obras por migrar: %d" % (S.VERSION, len(plan_trabajo)))
for x in plan_trabajo:
    print("  %s %-34s %s → %s · avance %s%% → %.1f%%%s" % (
        x["pid"], str(x["nombre"])[:34], x["version"], S.VERSION, x["avance_antes"], x["avance_despues"],
        "" if x["migrable"] else "  ⚠️ NO MIGRABLE"))
    for o, n, a, b in x["cambios"]:
        print("       etapa #%d «%s»: %s%% → %.1f%%" % (o, n, a, b))

if not APLICAR:
    print("\n(en seco: nada escrito. Con --aplicar, copia en D: y migra)")
    sys.exit(0)

_dir = r"D:\CopeX\respaldos"
os.makedirs(_dir, exist_ok=True)
_f = os.path.join(_dir, "v609_antes_de_migrar_%s.json" % time.strftime("%Y%m%d_%H%M%S"))
json.dump(copia, io.open(_f, "w", encoding="utf-8"), ensure_ascii=False)
print("\nCopia: %s" % _f)
for x in plan_trabajo:
    if not x["migrable"]:
        print("  %s: no migrable, no se toca" % x["pid"])
        continue
    with tenant.como_grupo(x["grupo"]):
        ok, msg = SP.migrar_catalogo(x["pid"], x["grupo"], x["prj"], quien="migracion-v609")
    print("  %s %s: %s" % (x["pid"], "OK" if ok else "FALLO", msg))
    time.sleep(2)                    # espaciado: el techo de 60 lecturas/min
