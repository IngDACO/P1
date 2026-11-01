# -*- coding: utf-8 -*-
"""v626 · Lo que salió al verificar v625 en producción (01/11/2026).

  (1) ⚠️ Bajar a un bloque lo dejaba DEBAJO de la barra de Streamlit (60 px, encima de la página y
      transparente): medido a 375 px, las cifras de Belting a 0 px con «Fork» encima → margen arriba;
  (2) dos surveys por decidir en la misma obra: dos líneas idénticas en la campana → una, con el número;
  (3) la campana lleva a Files y Files no decía qué fila tocar → lo dice, con el nombre;
  (4) al campo le salía el texto de la oficina, que nombra el informe que no ve y, con un survey ya
      guardado, es falso → fuera.
⚠️ Lo aprendido en v620: nada de estado preparado a mano. Sin red ni hoja real.
"""
import io
import json
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
from streamlit.testing.v1 import AppTest                          # noqa: E402

st.session_state["auth"] = {"usuario": "installer", "nombre": "installer CI 1", "rol": "field",
                            "grupo": "cliente1"}
from core import toolruns as TR                                   # noqa: E402

TR._REGISTRAR_REAL = TR.registrar
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


def _btn(a, k):
    return next((b for b in a.button if b.key == k), None)


def _todo(a):
    return " | ".join(str(x.value) for k in ("markdown", "caption", "info", "warning", "error", "success",
                                              "header") for x in getattr(a, k, []))


sec("1. ⚠️ Bajar no deja lo buscado debajo de la barra")
GB = r'''
import streamlit as st
from core import projects_ui as PU, incrustar
_LL = st.session_state.setdefault("_LL", [])
incrustar.script = lambda html, *a, **k: _LL.append(html)
st.session_state["_MARCA"] = True
with st.container(key="cpx_prueba"):
    PU._bajar_a("cpx_prueba", "_MARCA", bloque=st.session_state.get("_BLOQUE", "start"))
    st.write("lo que se quiere ver")
'''
for _bl in ("start", "nearest"):
    a = AppTest.from_string(GB, default_timeout=60)
    a.session_state["_BLOQUE"] = _bl
    a.run()
    _s = " ".join(a.session_state["_LL"])
    chk("con `%s`, el margen de la barra ANTES de bajar" % _bl,
        "c.style.scrollMarginTop='68px';c.scrollIntoView(" in _s, _s[:300])
_px = int(_s.split("scrollMarginTop='")[1].split("px")[0])
chk("⚠️ el margen pasa los 60 px de `stHeader` (medido en producción) y deja aire", 60 < _px <= 80, _px)

sec("2. La campana: una línea por obra")
GC = r'''
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "x", "nombre": "x", "rol": "administrator", "grupo": "cliente1"})
from core import home_ui, toolruns as TR, projects as P, admin_digest, credentials as C, inventory as I
admin_digest.group_digest = lambda g: {}
C.is_configured = lambda: False
I.is_configured = lambda: False
TR.survey_por_decidir = lambda g: [{"ID": str(i), "ProjectID": p} for i, p in enumerate(st.session_state["_P"])]
P.get_project = lambda pid: {"Name": {"PRJ-1": "Obra uno", "PRJ-2": "Obra dos"}.get(pid)}
st.session_state["_AL"] = [a for a in home_ui._alertas_items("cliente1") if "from the field" in a["texto"]]
'''


def campana(p):
    a = AppTest.from_string(GC, default_timeout=60)
    a.session_state["_P"] = p
    a.run()
    chk("   (sin excepción)", not a.exception, [e.value for e in a.exception][:1])
    return a.session_state["_AL"]


_al = campana(["PRJ-1"])
chk("una: en singular, como en v625", len(_al) == 1 and "a survey from the field is waiting" in _al[0]["texto"], _al)
_al = campana(["PRJ-1", "PRJ-1"])
chk("⚠️ dos en la misma obra: UNA línea, con el número (eran dos idénticas)",
    len(_al) == 1 and "**Obra uno** — 2 surveys from the field are waiting" in _al[0]["texto"]
    and _al[0]["destino"] == ("archivos", "PRJ-1"), _al)
_al = campana(["PRJ-1", "PRJ-2", "PRJ-1"])
chk("en dos obras: una línea cada una, cada una a la suya",
    [(x["destino"][1], "2 surveys" in x["texto"]) for x in _al] == [("PRJ-1", True), ("PRJ-2", False)], _al)
chk("ninguna: nada", campana([]) == [])

sec("3. Files dice qué fila tocar")
GF = r'''
import streamlit as st
st.session_state.setdefault("auth", st.session_state["_AUTH"])
from core import projects_ui as PU, toolruns as TR, projects as P, drive_store as DS
DS.is_configured = lambda: True
TR.is_configured = lambda: True
TR.list_for = lambda pid: st.session_state["_RUNS"]
P.list_documents = lambda pid: [{"Type": "calculo", "DriveID": "D1", "Name": "Survey_*1*.json", "Date": "2026-11-01"}]
PU._archivos_section("PRJ-1")
'''
PEND = {"ID": "CAL-7", "Tool": "survey", "File": "Survey_*1*.json", "DriveID": "D1",
        "DataJSON": json.dumps({"por_decidir": True})}
HECHA = {**PEND, "DataJSON": json.dumps({"por_decidir": False})}
SINF = {**PEND, "DriveID": ""}
OF = {"usuario": "Admin2", "nombre": "B", "rol": "administrator", "grupo": "cliente1"}
CA = {"usuario": "installer", "nombre": "i", "rol": "field", "grupo": "cliente1"}


def files(auth, runs):
    a = AppTest.from_string(GF, default_timeout=60)
    a.session_state["_AUTH"], a.session_state["_RUNS"] = auth, runs
    a.run()
    chk("   (sin excepción)", not a.exception, [e.value for e in a.exception][:1])
    return " | ".join(str(x.value) for x in a.info)


_i = files(OF, [PEND])
chk("⚠️ a la oficina, cuál es y qué hacer", "Waiting for your decision: **Survey\\_\\*1\\*.json**" in _i
    or "Waiting for your decision: **Survey_\\*1\\*.json**" in _i, _i)
chk("…con «Tap its row below»", "Tap its row below" in _i, _i)
chk("ya decidida, no", "Waiting for your decision" not in files(OF, [HECHA]))
chk("sin archivo, no (no hay fila que tocar)", "Waiting for your decision" not in files(OF, [SINF]))
chk("⚠️ al campo, no: no es suya la decisión", "Waiting for your decision" not in files(CA, [PEND]))

sec("4. El texto de la oficina no es para el campo")
_v625 = io.open(os.path.join(RAIZ, "..", "guardianes", "verif_v625.py"), encoding="utf-8").read()
GV = _v625.split("GV = r'''")[1].split("'''")[0]
OB = {"ID": "PRJ-1", "Name": "Obra uno", "Type": "Installation", "Status": "In progress", "Group": "cliente1",
      "NS": 6, "ParamsJSON": "{}", "MatrixJSON": "[]"}
OC = {**OB, "ParamsJSON": '{"NS": 6}', "MatrixJSON": '[{"WR": 90}]'}


def survey(obra, libre, rol="field"):
    a = AppTest.from_string(GV, default_timeout=600)
    a.session_state["_ROL"], a.session_state["_OBRA"] = rol, obra
    a.session_state["_LIBRE"], a.session_state["_ARRIBA"] = libre, obra
    a.run()
    _btn(a, "btn_calc_datos").click()
    a.run()
    chk("   (calcula sin excepción)", not a.exception, [e.value for e in a.exception][:1])
    return a


_L = "are attached to the project"
a = survey(OC, False)
chk("⚠️ campo, obra con survey: sin «are attached» (es falso: no se adjunta)", _L not in _todo(a), _todo(a)[-300:])
chk("…y sí lo que va a pasar", "already has a saved survey" in _todo(a))
a = survey(OB, True)
chk("⚠️ campo, obra sin survey: tampoco (nombra el informe del cliente, que no ve)",
    _L not in _todo(a) and "client report" not in _todo(a).lower(), _todo(a)[-300:])
chk("…y sí a dónde va", "It will be saved to **Obra uno**" in _todo(a))
a = survey(OC, False, rol="administrator")
chk("a la oficina, sí, como siempre", _L in _todo(a))

print("\n%d ok, %d fallos" % (n_ok, len(fallos)))
for x in fallos:
    print("  FALLO:", x)
sys.exit(1 if fallos else 0)
