# -*- coding: utf-8 -*-
"""v688 · LO VISTO CERRANDO EL CICLO 4 DESDE LA OFICINA (17/11/2026): la decisión sobre el Survey de campo (CAL-0027).

  1. El Survey que guarda el campo en una obra que ya tiene uno se archivaba como «Survey_2026-11-17_0601_campo000.json»:
     con la cuenta y sin la obra, cuando lo demás de Files lleva la obra y la fecha (v682). Ahora
     «Field_survey_<obra>_<fecha>.json»; quién lo guardó sigue en la fila (User) y en «Uploaded by».
  2. Al cargarlo desde Files («Load it into the Survey») el Survey decía «You loaded project C4 — …», igual que al
     cargar el de la obra, con los dos en juego. Ahora dice que es el del campo, de quién (su nombre, no la cuenta) y
     de cuándo, y que el de la obra solo cambia si se guarda este.

Sin red: Drive, la hoja y los usuarios, sustituidos.
"""
import json
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"}
from streamlit.testing.v1 import AppTest                          # noqa: E402

n_ok, fallos = 0, []


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("   ok   %s" % q)
    else:
        fallos.append(q)
        print("   FALLO %s%s" % (q, ("  -> " + str(det)) if det != "" else ""))


def sec(x):
    print("\n" + x)
    print("-" * 70)


def leer(rel):
    with open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


sec("1. El Survey del campo se archiva con la obra")
from core.num import nombre_archivo                               # noqa: E402
_su = leer("core/survey_ui.py")
chk("⚠️ «Field_survey_<obra>_<fecha>.json» (era «Survey_<fecha>_<cuenta>.json»)",
    "filename=f\"Field_survey_{nombre_archivo(prj.get('Name'), 'project')}_{_cuando}.json\"" in _su
    and "filename=f\"Survey_{_cuando}_{usuario}.json\"" not in _su)
chk("...que con la obra del ciclo 4 da «Field_survey_C4_Harbour_Lifts_Lift_4_tools_…»",
    nombre_archivo("C4 — Harbour Lifts — Lift 4 (tools)", "project") == "C4_Harbour_Lifts_Lift_4_tools",
    nombre_archivo("C4 — Harbour Lifts — Lift 4 (tools)", "project"))

sec("2. «Load it into the Survey»: de quién y de cuándo (AppTest de `_decidir_survey`)")
GD = r'''
import json
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"})
from core import projects_ui as PU, projects as P, drive_store, toolruns, auth
P.get_project = lambda pid: {"ID": "PRJ-1", "Name": "Obra uno", "Group": "cliente1"}
P.head_installers_label = lambda *a, **k: "Head"
drive_store.download = lambda did: json.dumps({"params": {"BKS": 1600, "NS": 2, "WALL_LIMITING": True, "WALL_STOP": 2},
    "matriz": [{"WR": 95.0, "FR": 830.0, "OR": 280.0, "WL": 90.0, "FL": 828.0, "OL": 285.0}] * 2}).encode()
toolruns.decidir_survey = lambda run, como, u="": st.session_state.setdefault("_DEC", []).append(como) or True
auth.list_users = lambda *a, **k: [{"User": "campo000", "Name": "hjg,ujgjg"}, {"User": "Admin2", "Name": "Bobo"}]
RUN = {"ID": "CAL-7", "User": "campo000", "Date": "2026-11-17 06:01", "DataJSON": json.dumps({"por_decidir": True})}
if st.session_state.get("_VIA") == "obra":
    PU._cargar_en_survey("PRJ-1", P.get_project("PRJ-1"), "cliente1", {"BKS": 1600, "NS": 2}, [])
else:
    PU._decidir_survey("PRJ-1", "D1", RUN)
'''
a = AppTest.from_string(GD, default_timeout=60)
a.run()
chk("sin excepción", not a.exception, [e.value for e in a.exception][:1])
next(b for b in a.button if b.key == "arch_svcarga_PRJ-1").click()
a.run()
_c = a.session_state["_rebuilt_campo"] if "_rebuilt_campo" in a.session_state else None
chk("⚠️ cargarlo apunta que es del CAMPO, con el NOMBRE (no la cuenta) y la fecha en DD/MM/YYYY HH:MM",
    _c == {"quien": "hjg,ujgjg", "cuando": "17/11/2026 06:01"}, _c)
chk("...junto a la obra (lo de siempre) y la decisión «loaded»", a.session_state["_rebuilt_from"] == "Obra uno"
    and a.session_state["_DEC"] == ["loaded"], (a.session_state["_rebuilt_from"], a.session_state["_DEC"]))
a2 = AppTest.from_string(GD, default_timeout=60)
a2.session_state["_VIA"] = "obra"
a2.session_state["_rebuilt_campo"] = {"quien": "viejo", "cuando": "x"}
a2.run()
chk("⚠️ «Load this project into the Survey» (el de la obra) lo QUITA: no se arrastra de una carga anterior",
    "_rebuilt_campo" not in a2.session_state and a2.session_state["_rebuilt_from"] == "Obra uno")

sec("3. El aviso del Survey (AppTest)")
GS = r'''
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"})
from core import survey_ui as SU, projects as P
SU.plan_ui.selector_proyecto = lambda key, ayuda="": (None, {})
P.list_projects = lambda *a, **k: []
SU.init_state()
SU.render_survey_tab("administrator", "cliente1")
'''


def todo(x):
    return " | ".join(str(i.value) for i in list(x.info) + list(x.markdown))


s = AppTest.from_string(GS, default_timeout=60)
s.session_state["_rebuilt_from"] = "C4 — X"
s.session_state["_rebuilt_campo"] = {"quien": "hjg,ujgjg", "cuando": "17/11/2026 06:01"}
s.run()
chk("sin excepción", not s.exception, [e.value for e in s.exception][:1])
chk("⚠️ el del campo: «You loaded the survey that **hjg,ujgjg** saved from the field on **17/11/2026 06:01** for **C4 — X**…»",
    "You loaded the survey that **hjg,ujgjg** saved from the field on **17/11/2026 06:01** for **C4 — X**" in todo(s)
    and "the project's survey only changes if you then save this one" in todo(s) and "You loaded project" not in todo(s),
    todo(s)[:400])
s2 = AppTest.from_string(GS, default_timeout=60)
s2.session_state["_rebuilt_from"] = "C4 — X"
s2.run()
chk("el de la obra, como siempre: «You loaded project **C4 — X**»", "You loaded project **C4 — X**" in todo(s2)
    and "saved from the field" not in todo(s2), todo(s2)[:300])
chk("y se olvida con lo demás (empezar de cero, duplicar, calcular)", _su.count('"_rebuilt_campo"') >= 4, _su.count('"_rebuilt_campo"'))

print("\n%s: %d ok, %d FALLO" % ("verif_v688", n_ok, len(fallos)))
if fallos:
    print("FALLOS:")
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("TODO OK")
