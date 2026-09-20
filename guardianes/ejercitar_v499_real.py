# -*- coding: utf-8 -*-
"""v499 contra la HOJA REAL (método v344): foto → ejercitar → verificar leyendo → restaurar.

Prueba lo único que no puede probar una hoja simulada: que la columna `Predecessors` se
CREE sola en la hoja (migración de cabecera) y que el valor llegue a su sitio.
Obra de prueba (`PRUEBA MOVIL`, la creé yo en v480); todo se devuelve a su estado.
"""
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Bobo", "nombre": "Bobo",
                            "rol": "administrator", "grupo": "cliente1"}

import gspread                                                    # noqa: E402
from google.oauth2.service_account import Credentials             # noqa: E402
from core import projects as P                                    # noqa: E402
from core.schedule import build_schedule                          # noqa: E402


def foto():
    """⚠️ SOLO LECTURA con gspread crudo: los helpers migran cabeceras (v145)."""
    c = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    gc = gspread.authorize(c)
    lib = gc.open_by_key(st.secrets["TIMECLOCK_SHEET_ID"])
    grp = lib.worksheet("Groups").get_all_values()
    sid = [f[grp[0].index("SheetID")] for f in grp[1:] if f and f[0] == "cliente1"][0]
    return gc.open_by_key(sid).worksheet("Activities").get_all_values()


PID = "PRJ-0001"
antes = foto()
print("ANTES · cabecera (%d col): %s" % (len(antes[0]), antes[0][-3:]))
print("        «Predecessors» en la hoja: %s" % ("Predecessors" in antes[0]))
print("        filas: %d" % (len(antes) - 1))

acts = P.list_activities(PID)
print("\nactividades: %s" % [(a.get("Order"), a.get("Name")[:22]) for a in acts])

# ── el plan ANTES (cadena rígida: cada una detrás de la anterior) ──
s0 = P.project_schedule(PID)["sched"]
print("\nplan ANTES : %s · total %s d" % (
    [(a["orden"], a["fecha_inicio"].isoformat()) for a in s0["activities"]], s0["total_dias"]))

# ── se declara que la 3 va detrás de la 1 con 2 días de espera ──
edits = [{"orden0": a.get("Order"), "Order": int(a.get("Order")),
          "Predecessors": ("1+2" if str(a.get("Order")) == "3" else "")} for a in acts]
ok, msg = P.save_activities(PID, edits)
print("\nguardar: %s · %s" % (ok, msg))

despues = foto()
print("\nDESPUÉS· cabecera (%d col): %s" % (len(despues[0]), despues[0][-3:]))
print("        «Predecessors» en la hoja: %s  ← la migró la ESCRITURA" % ("Predecessors" in despues[0]))
if "Predecessors" in despues[0]:
    i = despues[0].index("Predecessors")
    print("        valores: %s" % [f[i] if len(f) > i else "" for f in despues[1:]])

P._invalidate()
s1 = P.project_schedule(PID)["sched"]
print("\nplan AHORA : %s · total %s d" % (
    [(a["orden"], a["fecha_inicio"].isoformat()) for a in s1["activities"]], s1["total_dias"]))
print("criticas   : %s" % [a["orden"] for a in s1["activities"] if a.get("critica")])

# ── restaurar: se quita la dependencia ──
P.save_activities(PID, [{"orden0": a.get("Order"), "Order": int(a.get("Order")),
                         "Predecessors": ""} for a in acts])
P._invalidate()
fin = foto()
i = fin[0].index("Predecessors") if "Predecessors" in fin[0] else -1
vals = [f[i] if len(f) > i else "" for f in fin[1:]] if i >= 0 else []
s2 = P.project_schedule(PID)["sched"]
print("\nRESTAURADO · predecesoras: %s · plan igual que al principio: %s" % (
    vals,
    [(a["orden"], a["fecha_inicio"].isoformat()) for a in s2["activities"]] ==
    [(a["orden"], a["fecha_inicio"].isoformat()) for a in s0["activities"]]))
print("            filas: %d (antes %d)" % (len(fin) - 1, len(antes) - 1))
