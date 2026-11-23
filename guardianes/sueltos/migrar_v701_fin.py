# -*- coding: utf-8 -*-
"""Migración de v701 · D1 del ciclo 7 («Arreglalas»): la fecha de fin GUARDADA (`EndDateEst`) de las obras creadas
antes de v698 sigue en días NATURALES (inicio + días del plan): C6 25/12/2026 con su plan hasta el 06/01/2027. Se
recalcula con el plan de lunes a viernes (y sus pausas), SOLO si la puso la app: la fecha guardada es exactamente la
vieja automática y el rastro de cambios no tiene ningún cambio de `EndDateEst` hecho por una persona.

    py -3.12 sueltos/migrar_v701_fin.py            → EN SECO: obra por obra, qué cambiaría y por qué no
    py -3.12 sueltos/migrar_v701_fin.py --aplicar  → copia de Projects en D: y escribe (con su rastro)

⚠️ Con `--aplicar` ESCRIBE en la hoja real (Projects y AuditTrail, autor «migracion-v701»). Lo leído, en SOLO LECTURA.
"""
import io
import json
import os
import sys
import time
from datetime import date, timedelta

RAIZ = r"C:\Users\diego\P1\survey_app"
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "migracion-v701", "nombre": "End date migration v701",
                            "rol": "owner", "grupo": ""}
import gspread                                                    # noqa: E402
import tomllib                                                    # noqa: E402
from google.oauth2.service_account import Credentials            # noqa: E402

from core import clock                                            # noqa: E402
from core import projects as P                                    # noqa: E402
from core import tenant                                           # noqa: E402
from core.calendario import Calendario, pausas_de                 # noqa: E402
from core.num import num as _num                                  # noqa: E402
from core.schedule import build_schedule                          # noqa: E402

APLICAR = "--aplicar" in sys.argv
VIVAS = ("Planned", "In progress", "On hold")
SEC = tomllib.load(open(os.path.join(RAIZ, ".streamlit", "secrets.toml"), "rb"))
gc = gspread.authorize(Credentials.from_service_account_info(
    dict(SEC["gcp_service_account"]), scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]))
m = gc.open_by_key(SEC["TIMECLOCK_SHEET_ID"])
grupos = [(str(g.get("Group", "")).strip(), str(g.get("SheetID", "")).strip() or SEC["TIMECLOCK_SHEET_ID"])
          for g in m.worksheet("Groups").get_all_records() if str(g.get("Group", "")).strip()]


def _fecha(s):
    try:
        y, mm, d = str(s or "").strip()[:10].split("-")
        return date(int(y), int(mm), int(d))
    except Exception:
        return None


copia, cambiar, quedan = {}, [], []
for g, sid in grupos:
    L = gc.open_by_key(sid)
    hojas = {h: L.worksheet(h).get_all_records(numericise_ignore=["all"])
             for h in ("Projects", "Activities", "AuditTrail")}
    copia[g] = {"Projects": hojas["Projects"]}
    hoy = clock.today(g)
    for prj in hojas["Projects"]:
        pid, st_ = str(prj.get("ID", "")), str(prj.get("Status", ""))
        if st_ not in VIVAS or _num(prj.get("Progress")) >= 100:
            continue
        ini, guardada = _fecha(prj.get("StartDate")), str(prj.get("EndDateEst", "")).strip()[:10]
        acts = sorted([a for a in hojas["Activities"] if str(a.get("ProjectID")) == pid],
                      key=lambda a: _num(a.get("Order")))
        if not ini or not acts:
            quedan.append((g, pid, prj.get("Name"), guardada, "", "sin inicio o sin actividades"))
            continue
        custom = [{"nombre": a.get("Name", ""), "duracion": _num(a.get("DurationDays")) or 1.0,
                   "peso": _num(a.get("Weight")), "orden": _num(a.get("Order")) or (i + 1),
                   "pred": str(a.get("Predecessors", "") or "")} for i, a in enumerate(acts)]
        hist = []
        for r in hojas["AuditTrail"]:
            if r.get("Entity") == "proyecto" and str(r.get("EntityID", "")) == pid:
                try:
                    cam = json.loads(r.get("ChangesJSON", "") or "{}")
                except Exception:
                    cam = {}
                hist.append({**r, "cambios": cam})
        hist.sort(key=lambda x: str(x.get("Date", "")), reverse=True)
        cal = Calendario(ini, pausas_de(hist, st_, hoy), hoy)
        sched = build_schedule(1, ini, {}, custom_rows=custom, cal=cal)
        nueva = sched["fecha_fin"].isoformat()
        vieja_auto = (ini + timedelta(days=int(sched["total_dias"]))).isoformat()
        a_mano = [h for h in hist if "EndDateEst" in (h.get("cambios") or {})]
        if guardada == nueva:
            quedan.append((g, pid, prj.get("Name"), guardada, nueva, "ya al día"))
        elif a_mano:
            quedan.append((g, pid, prj.get("Name"), guardada, nueva,
                           "cambiada a mano (%s, %s)" % (a_mano[0].get("User", "?"), str(a_mano[0].get("Date", ""))[:10])))
        elif guardada != vieja_auto:
            quedan.append((g, pid, prj.get("Name"), guardada, nueva,
                           "no es la automática vieja (%s): el plan cambió después" % vieja_auto))
        else:
            cambiar.append((g, pid, prj.get("Name"), guardada, nueva))


def _dmy(s):
    d = _fecha(s)
    return d.strftime("%d/%m/%Y") if d else (s or "—")


print("Se recalculan (%d):" % len(cambiar))
for g, pid, nom, a, b in cambiar:
    print("  %s %-42s %s → %s" % (pid, str(nom)[:42], _dmy(a), _dmy(b)))
print("Se quedan como están (%d):" % len(quedan))
for g, pid, nom, a, b, por in quedan:
    print("  %s %-42s %s (plan %s) · %s" % (pid, str(nom)[:42], _dmy(a), _dmy(b), por))

if not APLICAR:
    print("\n(en seco: nada escrito. Con --aplicar, copia en D: y escribe)")
    sys.exit(0)

_dir = r"D:\CopeX\respaldos"
os.makedirs(_dir, exist_ok=True)
_f = os.path.join(_dir, "v701_antes_de_migrar_fin_%s.json" % time.strftime("%Y%m%d_%H%M%S"))
json.dump(copia, io.open(_f, "w", encoding="utf-8"), ensure_ascii=False)
print("\nCopia: %s" % _f)
for g, pid, nom, a, b in cambiar:
    with tenant.como_grupo(g):
        ok, msg = P.update_project(pid, {"EndDateEst": b})
    print("  %s %s: %s" % (pid, "OK" if ok else "FALLO", msg))
    time.sleep(2)                    # espaciado: el techo de 60 lecturas/min
