# -*- coding: utf-8 -*-
"""v501 contra la HOJA REAL (método v344): foto → fijar → cambiar el plan → re-fijar →
verificar leyendo → restaurar → foto. Obra de prueba (`PRUEBA MOVIL`, creada por mí)."""
import json
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
from core import baseline as BL, projects as P                    # noqa: E402

PID = "PRJ-0001"


def foto():
    """⚠️ SOLO LECTURA (los helpers migran cabeceras al acceder, v145)."""
    c = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    gc = gspread.authorize(c)
    lib = gc.open_by_key(st.secrets["TIMECLOCK_SHEET_ID"])
    grp = lib.worksheet("Groups").get_all_values()
    sid = [f[grp[0].index("SheetID")] for f in grp[1:] if f and f[0] == "cliente1"][0]
    v = gc.open_by_key(sid).worksheet("Projects").get_all_values()
    col = v[0].index("BaselineJSON") if "BaselineJSON" in v[0] else -1
    fila = next((f for f in v[1:] if f and f[0] == PID), [])
    return (len(v[0]), col, (fila[col] if col >= 0 and len(fila) > col else ""))


ncol, col, crudo = foto()
print("ANTES · %d columnas · «BaselineJSON» en la hoja: %s · valor: %r"
      % (ncol, col >= 0, crudo[:40]))

acts = P.list_activities(PID)
dur0 = {a.get("Order"): a.get("DurationDays") for a in acts}
print("        duraciones: %s" % dur0)

# 1) fijar
ok, msg = P.fijar_baseline(PID, "Bobo")
print("\n1) fijar  -> %s · %s" % (ok, msg))
ncol, col, crudo = foto()
bl = json.loads(crudo or "{}")
print("   hoja: %d columnas · original entrega %s (total %s) · historial %d"
      % (ncol, bl.get("original", {}).get("entrega"), bl.get("original", {}).get("total"),
         len(bl.get("historial", []))))

# 2) alargar una actividad: lo que ANTES no dejaba rastro
_a2 = [a for a in acts if str(a.get("Order")) == "2"][0]
P.save_activities(PID, [{"orden0": a.get("Order"), "Order": int(a.get("Order")),
                         "DurationDays": (int(P._num(a.get("DurationDays"))) + 4
                                          if str(a.get("Order")) == "2"
                                          else int(P._num(a.get("DurationDays"))))}
                        for a in acts])
P._invalidate()
ps = P.project_schedule(PID)
cmp_ = BL.comparar(ps["sched"], P.get_baseline(PID))
print("\n2) se alarga la actividad 2 en 4 días (antes: sin rastro)")
print("   entrega acordada %s → hoy %s  (%+.1f d) · replanificaciones: %d"
      % (cmp_["entrega_base"], cmp_["entrega_hoy"], cmp_["movio"], cmp_["replanificaciones"]))
for f in cmp_["actividades"]:
    print("   · %s (orden %d): %s  %s → %s d · se movió %s"
          % (f["nombre"][:26], f["orden"], f["estado"], f["dur_base"], f["dur_hoy"], f["movio"]))

# 3) re-fijar: la original NO se pierde
ok, msg = P.fijar_baseline(PID, "Bobo")
print("\n3) re-fijar -> %s · %s" % (ok, msg))
bl2 = P.get_baseline(PID)
print("   original INTACTA: %s · vigente: %s · historial: %d (movió %+.1f d)"
      % (bl2["original"]["entrega"], bl2["vigente"]["entrega"], len(bl2["historial"]),
         bl2["historial"][-1]["movio"]))
cmp2 = BL.comparar(P.project_schedule(PID)["sched"], bl2)
print("   y se sigue comparando contra la ORIGINAL: %+.1f d" % cmp2["movio"])

# ── restaurar: duraciones y línea base fuera ──
P.save_activities(PID, [{"orden0": a.get("Order"), "Order": int(a.get("Order")),
                         "DurationDays": int(P._num(dur0.get(a.get("Order"))))} for a in acts])
P.update_project(PID, {"BaselineJSON": ""})
P._invalidate()
ncol, col, crudo = foto()
acts2 = P.list_activities(PID)
print("\nRESTAURADO · BaselineJSON: %r · duraciones: %s · iguales que al principio: %s"
      % (crudo, {a.get("Order"): a.get("DurationDays") for a in acts2},
         {a.get("Order"): a.get("DurationDays") for a in acts2} == dur0))
