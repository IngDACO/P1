# -*- coding: utf-8 -*-
"""v625 · RECORRIDO DEL CAMPO: TOOLS (01/11/2026, «Dale con todo incluido lo recomendado»).

  (1) ⚠️ El fichaje iba por el NOMBRE: dos obras iguales, fichado en PRJ-2, la herramienta usaba PRJ-1
      → por ID (`plan_ui.obra_del_fichaje`), y el nombre solo si es de UNA obra;
  (2) calcular no llevaba al resultado → baja, solo si se calculó;
  (3) la portada le decía al campo dónde calculó otro → solo sus obras (y el Pre-Start de hoy);
  (4) «Clock in first» sin fichar → una obra se usa sola; varias, elige entre las suyas;
  (5) «It will be saved» bajo «Saved as CAL-…» → se quita;
  (6) «Clocked in at» sin traducir y nombres sin escapar;
  (7) «Client report» al campo, solo para decirle que no → fuera;
  (8) ⚠️ el campo no podía guardar su Survey → sí, en su obra, SIN PISAR uno guardado: se archiva
      como cálculo nuevo y la oficina decide (campana → Files → cargarlo o quedarse el suyo).
⚠️ Lo aprendido en v620: nada de estado preparado a mano. Se elige y se guarda con clics.
Sin red ni hoja real.
"""
import datetime
import inspect
import io
import json
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd                                               # noqa: E402
import streamlit as st                                            # noqa: E402
from streamlit.testing.v1 import AppTest                          # noqa: E402

st.session_state["auth"] = {"usuario": "installer", "nombre": "installer CI 1", "rol": "field",
                            "grupo": "cliente1"}
from core import plan_ui, projects as P, timeclock as T, toolruns as TR  # noqa: E402

# ⚠️ Los guiones de AppTest corren en ESTE proceso y sus sustituciones se quedan puestas: lo que se
# prueba de verdad más abajo se guarda aquí, antes de que ningún guion lo toque.
TR._REGISTRAR_REAL = TR.registrar
_SURVEY_LIBRE_REAL = P.survey_libre
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


def _src(rel):
    return io.open(os.path.join(RAIZ, "core", rel), encoding="utf-8").read()


sec("1. ⚠️ El fichaje, por ID")
A = {"ID": "PRJ-1", "Name": "Torre Norte — Lift 1", "Group": "cliente1"}
B = {"ID": "PRJ-2", "Name": "Torre Norte — Lift 1", "Group": "cliente1"}
C = {"ID": "PRJ-3", "Name": "Otra obra", "Group": "cliente1"}
chk("⚠️ dos obras con el mismo nombre: la del ID del fichaje, no la primera",
    plan_ui.obra_del_fichaje({"proyecto": A["Name"], "proyecto_id": "PRJ-2"}, [A, B])["ID"] == "PRJ-2")
chk("un ID que no está no cae al nombre",
    plan_ui.obra_del_fichaje({"proyecto": A["Name"], "proyecto_id": "PRJ-9"}, [A, B]) is None)
chk("un fichaje viejo sin ID va por el nombre si es de UNA obra (sin mayúsculas)",
    plan_ui.obra_del_fichaje({"proyecto": "otra OBRA", "proyecto_id": ""}, [A, B, C])["ID"] == "PRJ-3")
chk("⚠️ …y si el nombre es de DOS, ninguna: elegir la primera guardaría en la de otro",
    plan_ui.obra_del_fichaje({"proyecto": A["Name"], "proyecto_id": ""}, [A, B]) is None)
chk("sin fichaje, ninguna", plan_ui.obra_del_fichaje({}, [A, B]) is None)
_lp, _os = P.list_projects, T.open_sessions
P.list_projects = lambda **k: [A, B]
T.open_sessions = lambda *a, **k: {T.TIPO_GENERAL: None, T.TIPO_PROYECTO: {
    "clock_in": "2026-11-01 07:00:00", "proyecto": A["Name"], "proyecto_id": "PRJ-2"}}
chk("⚠️ `_proyecto_fichado` da la del fichaje (el fallo demostrado: daba PRJ-1)",
    plan_ui._proyecto_fichado(st.session_state["auth"])["ID"] == "PRJ-2")
T.open_sessions = lambda *a, **k: {T.TIPO_GENERAL: None, T.TIPO_PROYECTO: None}
chk("sin jornada abierta, ninguna", plan_ui._proyecto_fichado(st.session_state["auth"]) is None)
P.list_projects, T.open_sessions = _lp, _os
_ts = _src("tool_save_ui.py")
chk("el guardado usa la MISMA función (dos copias se desvían)",
    "plan_ui.obra_del_fichaje(" in _ts and "_fpn" not in _ts)

sec("2. El selector del campo (AppTest, clics reales)")
GS = r'''
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "installer", "nombre": "installer CI 1", "rol": "field", "grupo": "cliente1"})
from core import plan_ui, plan_data, projects as P, timeclock as T, estado_vivo
_O = st.session_state["_OBRAS"]
_F = st.session_state.get("_FICHADO")
P.is_configured = lambda: True
P.list_projects = lambda **k: list(_O)
P.list_projects_for_field = lambda u, grupo=None, incluir_internos=False: [p for p in _O if p.get("Mia")]
T.open_sessions = lambda *a, **k: {T.TIPO_GENERAL: None, T.TIPO_PROYECTO: _F}
plan_data.del_proyecto = lambda pid: {"PLANO": pid} if st.session_state.get("_CON_PLANO") else {}
plan_data.resumen = lambda d: "8 data"
prj, datos = plan_ui.selector_proyecto("bc")
st.session_state["_VIO"] = (prj or {}).get("ID")
'''
INST = {"Type": "Installation", "Status": "In progress", "Group": "cliente1", "Mia": True}
O1 = {**INST, "ID": "PRJ-1", "Name": "Obra *uno*"}
O2 = {**INST, "ID": "PRJ-2", "Name": "Obra dos"}
ENT = {**INST, "ID": "PRJ-3", "Name": "Entrega", "Type": "Delivery"}
CAN = {**INST, "ID": "PRJ-4", "Name": "Cancelada", "Status": "Cancelled"}
AJE = {**INST, "ID": "PRJ-5", "Name": "De otro", "Mia": False}


def corre(obras, fichado=None, plano=True):
    a = AppTest.from_string(GS, default_timeout=60)
    a.session_state["_OBRAS"] = obras
    a.session_state["_FICHADO"] = fichado
    a.session_state["_CON_PLANO"] = plano
    a.run()
    chk("   (sin excepción)", not a.exception, [e.value for e in a.exception][:1])
    return a


a = corre([O1, O2, AJE], {"proyecto": "Obra dos", "proyecto_id": "PRJ-2"})
chk("fichado: manda el fichaje, sin lista", a.session_state["_VIO"] == "PRJ-2" and not list(a.selectbox))
chk("…y lo dice", "Clocked in at **Obra dos**" in _todo(a), _todo(a))
a = corre([O1, ENT, CAN, AJE])
chk("⚠️ sin fichar, UNA obra suya abierta: se usa sola (decía «Clock in first»)",
    a.session_state["_VIO"] == "PRJ-1" and not list(a.selectbox) and "Clock in first" not in _todo(a), _todo(a))
chk("…y no dice que fichó", "Clocked in" not in _todo(a), _todo(a))
chk("⚠️ el nombre tal cual: los * no se vuelven cursiva", "Obra \\*uno\\*" in _todo(a), _todo(a))
a = corre([O1, O2, ENT, AJE])
_sel = list(a.selectbox)
chk("⚠️ con varias, elige entre las SUYAS (ni la entrega ni la de otro)",
    len(_sel) == 1 and list(_sel[0].options) == [plan_ui.SIN_PROYECTO, "Obra *uno* (PRJ-1)", "Obra dos (PRJ-2)"],
    [list(x.options) for x in _sel])
chk("…y hasta elegir no usa ninguna", a.session_state["_VIO"] is None)
_sel[0].select("Obra dos (PRJ-2)")
a.run()
chk("⚠️ al elegir (clic), esa", a.session_state["_VIO"] == "PRJ-2")
a2 = AppTest.from_string(GS.replace('prj, datos = plan_ui',
                                    'st.session_state["pl_prj_bc"] = "Ya no está (PRJ-9)"; prj, datos = plan_ui'),
                         default_timeout=60)
a2.session_state["_OBRAS"], a2.session_state["_FICHADO"], a2.session_state["_CON_PLANO"] = [O1, O2], None, True
a2.run()
chk("una elección que ya no está no tumba la pantalla",
    not a2.exception and a2.session_state["_VIO"] is None, [e.value for e in a2.exception][:1])
a = corre([ENT, CAN, AJE])
chk("sin ninguna: lo dice, y no manda a fichar como única salida",
    a.session_state["_VIO"] is None and "no open installation assigned" in _todo(a), _todo(a))
a = corre([O1], plano=False)
chk("sin plano, el aviso con el nombre escapado", "Obra \\*uno\\*" in _todo(a) and "no drawing data" in _todo(a))
_c = inspect.getsource(plan_ui._cabecera)
chk("⚠️ «Clocked in at» por `t()`, con la frase entera (el literal concatenado no se traducía)",
    't(":material/schedule: Clocked in at **{x}** · {y}"' in _c and '":material/schedule: Clocked in at " if' not in _c)

sec("3. Guardar un cálculo (tool_save_ui)")
GG = r'''
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "installer", "nombre": "installer CI 1", "rol": "field", "grupo": "cliente1"})
from core import tool_save_ui as TS, toolruns as TR, projects as P, timeclock as T
_O = {"ID": "PRJ-1", "Name": "Obra *uno*", "Type": "Installation", "Status": "In progress", "Group": "cliente1"}
TR.is_configured = lambda: True
P.list_projects_for_field = lambda *a, **k: [_O]
T.open_sessions = lambda *a, **k: {T.TIPO_GENERAL: None, T.TIPO_PROYECTO: st.session_state.get("_FICHADO")}
def _reg(**k):
    st.session_state.setdefault("_REG", []).append(k)
    return {"ok": True, "id": "CAL-9", "drive_id": "x"}
TR.registrar = _reg
TS.render_guardar("buffers", "cuts", b"%PDF", "resumen", {"a": 1}, "x.pdf", key="bc", obra_id=st.session_state.get("_OBRA", ""))
'''
a = AppTest.from_string(GG, default_timeout=60)
a.session_state["_FICHADO"] = {"proyecto": "Obra *uno*", "proyecto_id": "PRJ-1"}
a.session_state["_OBRA"] = "PRJ-1"
a.run()
chk("antes de guardar dice a dónde va, con el nombre escapado",
    "It will be saved to **Obra \\*uno\\***" in _todo(a), _todo(a))
_btn(a, "save_bc").click()
a.run()
chk("⚠️ guardado: «Saved as…», y ya sin «It will be saved»",
    "Saved as **CAL-9**" in _todo(a) and "It will be saved" not in _todo(a), _todo(a))
chk("…con el nombre escapado", "in Obra \\*uno\\*." in _todo(a), _todo(a))
a = AppTest.from_string(GG, default_timeout=60)
a.session_state["_OBRA"] = "PRJ-1"
a.run()
chk("⚠️ sin fichar, con la obra elegida arriba: sin «You have not clocked in», y ya elegida",
    "You have not clocked in" not in _todo(a)
    and any(s.key == "prj_bc" and "PRJ-1" in str(s.value) for s in a.selectbox), _todo(a))
a = AppTest.from_string(GG, default_timeout=60)
a.run()
chk("sin fichar y sin obra, sí se lo dice", "You have not clocked in" in _todo(a))

sec("4. La portada de Tools")
TR._records = lambda: [
    {"ID": "CAL-1", "ProjectID": "PRJ-1", "Group": "cliente1", "Tool": "buffers", "Date": "2026-10-01 08:00"},
    {"ID": "CAL-2", "ProjectID": "PRJ-9", "Group": "cliente1", "Tool": "buffers", "Date": "2026-10-20 08:00"},
    {"ID": "CAL-3", "ProjectID": "PRJ-9", "Group": "cliente1", "Tool": "belting", "Date": "2026-10-20 08:00"},
    {"ID": "CAL-4", "ProjectID": "PRJ-1", "Group": "otro", "Tool": "belting", "Date": "2026-10-20 08:00"}]
_u = TR.ultimos_por_herramienta("cliente1")
chk("sin `pids`, todo el grupo, como antes", _u["buffers"]["ID"] == "CAL-2" and _u["belting"]["ID"] == "CAL-3")
_u = TR.ultimos_por_herramienta("cliente1", pids={"PRJ-1"})
chk("⚠️ con `pids`, solo esas obras", _u.get("buffers", {}).get("ID") == "CAL-1" and "belting" not in _u, _u)
chk("`pids` vacío: ninguna (no «todas»)", TR.ultimos_por_herramienta("cliente1", pids=set()) == {})
GH = r'''
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "installer", "nombre": "installer CI 1", "rol": st.session_state.get("_ROL", "field"), "grupo": "cliente1"})
from core import home_ui, toolruns as TR, projects as P, prestart as PS
TR._records = lambda: [
    {"ID": "CAL-1", "ProjectID": "PRJ-1", "Group": "cliente1", "Tool": "buffers", "Date": "2026-10-01 08:00"},
    {"ID": "CAL-2", "ProjectID": "PRJ-9", "Group": "cliente1", "Tool": "buffers", "Date": "2026-10-20 08:00"},
    {"ID": "CAL-3", "ProjectID": "PRJ-9", "Group": "cliente1", "Tool": "belting", "Date": "2026-10-21 08:00"}]
P.get_project = lambda pid: {"Name": {"PRJ-1": "Mi obra", "PRJ-9": "Obra ajena"}.get(pid)}
P.list_projects_for_field = lambda u, grupo=None, incluir_internos=False: [{"ID": "PRJ-1"}]
PS.de_hoy = lambda g: [{"ProjectID": "PRJ-9"}, {"ProjectID": "PRJ-9"}]
st.session_state["_USO"] = home_ui._ultimos_usos("cliente1", ["🛡 Buffers", "🎗 Belting", "🦺 Pre-Start"])
'''
a = AppTest.from_string(GH, default_timeout=60).run()
_u = a.session_state["_USO"]
chk("⚠️ al campo: su obra, nunca la ajena", "Mi obra" in _u.get("🛡 Buffers", "") and "ajena" not in str(_u), _u)
chk("…lo que no ha usado no sale (la tarjeta dirá «Not used yet»)", "🎗 Belting" not in _u, _u)
chk("⚠️ …y el Pre-Start de hoy, solo de sus obras (contaba los del grupo)",
    _u.get("🦺 Pre-Start") == "None done today", _u)
a = AppTest.from_string(GH, default_timeout=60)
a.session_state["_ROL"] = "administrator"
a.run()
_u = a.session_state["_USO"]
chk("a la oficina, todo el grupo, como antes",
    "ajena" in _u.get("🛡 Buffers", "") and _u.get("🦺 Pre-Start") == "2 done today", _u)

sec("5. ⚠️ Calcular lleva al resultado, solo si se calculó")
CAB = r'''
import streamlit as st
import importlib
import pandas as pd
st.session_state.setdefault("auth", {"usuario": "installer", "nombre": "installer CI 1", "rol": "field", "grupo": "cliente1"})
from core import plan_ui, incrustar, toolruns, projects as P
plan_ui = importlib.reload(plan_ui)
from core import %s
_LL = st.session_state.setdefault("_LL", [])
incrustar.dibujo = lambda html, *a, **k: None
incrustar.script = lambda html, *a, **k: _LL.append(html)
plan_ui.selector_proyecto = lambda key, ayuda="": (None, st.session_state.get("_PLANO", {}))
P.list_projects_for_field = lambda *a, **k: []
toolruns.is_configured = lambda: False
%s
%s
'''


def baja(a, clave, n0=0):
    return any((".st-key-" + clave) in s and "block:'start'" in s for s in a.session_state["_LL"][n0:])


# Buffers
GB = CAB % ("buffer_cut_ui", "", "buffer_cut_ui.render_buffer_cut_tab()")
a = AppTest.from_string(GB, default_timeout=120)
a.session_state["_PLANO"] = {}
a.run()
_btn(a, "bc_calc").click()
a.run()
chk("Buffers sin medir: NO baja (no hay nada a donde ir)",
    not baja(a, "cpx_bc_kpis") and "_bajar_cpx_bc_kpis" not in a.session_state, a.session_state["_LL"][-1:])
a = AppTest.from_string(GB, default_timeout=120)
a.session_state["_PLANO"] = {"hkp": 520}
a.session_state["bc_df"] = pd.DataFrame({"Buffer": ["Buffer 1"], "HKPR (mm)": [500.0]})
a.run()
_n0 = len(a.session_state["_LL"])
_btn(a, "bc_calc").click()
a.run()
chk("sin excepción", not a.exception, [e.value for e in a.exception][:1])
chk("⚠️ Buffers: calculado, baja a las cifras", "bc_res" in a.session_state and baja(a, "cpx_bc_kpis", _n0),
    a.session_state["_LL"][_n0:])
_n0 = len(a.session_state["_LL"])
a.run()
chk("…una sola vez (no devuelve la vista en cada toque)", not baja(a, "cpx_bc_kpis", _n0))
# Belting
GE = CAB % ("belting_ui", "", "belting_ui.render_belting_tab()")
a = AppTest.from_string(GE, default_timeout=120)
a.session_state["_PLANO"] = {}
a.run()
_btn(a, "belt_calc").click()
a.run()
chk("Belting sin medir: NO baja", not baja(a, "cpx_belt_kpis"))
a = AppTest.from_string(GE, default_timeout=120)
a.session_state["_PLANO"] = {"hq": 30000, "hgp": 1500}
a.run()
a.number_input(key="belt_hgpr_0").set_value(1547.0).run()
_n0 = len(a.session_state["_LL"])
_btn(a, "belt_calc").click()
a.run()
chk("⚠️ Belting: calculado, baja a las cifras",
    "belt_res" in a.session_state and baja(a, "cpx_belt_kpis", _n0), [e.value for e in a.exception][:1])
# Plomada
GP = CAB % ("plumb_ui", '''
if "_INI" not in st.session_state and st.session_state.get("_LLENO"):
    st.session_state["_INI"] = 1
    for k, v in {"plb_bks": 1772, "plb_rail": 62, "plb_tksw": 965, "plb_lt": 300, "plb_sf1": 51,
                 "plb_sf2": 51, "plb_bs": 1998, "plb_sg": 300, "plb_tg": 60}.items():
        st.session_state[k] = float(v)
    st.session_state["plb_n"] = 1
    st.session_state["plb_bsr_df"] = pd.DataFrame({"Elevador": ["Lift 1"], "BSR (mm)": [1985.0]})
''', "plumb_ui.render_plumb_tab()")
a = AppTest.from_string(GP, default_timeout=120).run()
_btn(a, "plb_calc").click()
a.run()
chk("Plomada sin datos: NO baja", not baja(a, "cpx_plb_res") and "_bajar_cpx_plb_res" not in a.session_state)
a = AppTest.from_string(GP, default_timeout=120)
a.session_state["_LLENO"] = True
a.run()
_n0 = len(a.session_state["_LL"])
_btn(a, "plb_calc").click()
a.run()
chk("⚠️ Plomada: calculada, baja al título del resultado",
    "plb_res_multi" in a.session_state and baja(a, "cpx_plb_res", _n0), [e.value for e in a.exception][:1])
# Rieles
GR = CAB % ("rail_cut_ui", "", "rail_cut_ui.render_rail_cut_tab()")
a = AppTest.from_string(GR, default_timeout=120)
a.session_state["_PLANO"] = {"lfkk": 1150, "lfgk": 980}
a.run()
_btn(a, "rc_calc1").click()
a.run()
chk("Rieles sin datos: NO baja", not baja(a, "cpx_rc_res"))
a.number_input(key="rc_n2500").set_value(2).run()
a.number_input(key="rc_n5000").set_value(3).run()
a.session_state["rc_L_df"] = pd.DataFrame({"Elevador": ["Lift 1"], "L (mm)": [19500.0]})
a.run()
_n0 = len(a.session_state["_LL"])
_btn(a, "rc_calc1").click()
a.run()
chk("⚠️ Rieles caso 1: calculado, baja a las cifras",
    bool((a.session_state["rc_res"] if "rc_res" in a.session_state else None)) and baja(a, "cpx_rc_res", _n0),
    [e.value for e in a.exception][:1])
a = AppTest.from_string(GR, default_timeout=120)
a.session_state["_PLANO"] = {"lfkk": 1150, "lfgk": 980}
a.run()
a.radio(key="rc_caso").set_value(a.radio(key="rc_caso").options[1]).run()
a.session_state["rc_in_df"] = pd.DataFrame({"Riel": ["RZ", "RO", "RF", "RB"], "Elevador 1": [300.0, 310.0, 280.0, 290.0]})
a.run()
_n0 = len(a.session_state["_LL"])
_btn(a, "rc_calc2").click()
a.run()
chk("⚠️ Rieles caso 2: calculado, baja a las cifras",
    bool((a.session_state["rc_res"] if "rc_res" in a.session_state else None)) and baja(a, "cpx_rc_res", _n0),
    [e.value for e in a.exception][:1])
_k = sorted(b.key for b in a.button if str(b.key or "").startswith("cpxkpi_rc2_"))
chk("…y las cifras siguen siendo botones", len(_k) == 4, _k)

sec("6. ⚠️ El Survey del campo (IA y correo sustituidos, clics reales)")
GV = r'''
import streamlit as st
import pandas as pd
st.session_state.setdefault("auth", {"usuario": "installer", "nombre": "installer CI 1", "rol": st.session_state.get("_ROL", "field"), "grupo": "cliente1"})
from core import survey_ui as SU, flash
_INT = {k: "x" for k in ("parametros", "estado_inicial", "desplazamientos", "solucion_optima",
                         "evasion_pared", "bsr_vs_bs", "consideraciones")}
_INT["_ok"] = True
_INTU = {k: "x" for k in ("resumen", "desplazamientos", "cortes", "implementacion", "verificacion")}
_INTU["_ok"] = True
SU.generate_interpretation = lambda *a, **k: dict(_INT)
SU.generate_user_interpretation = lambda *a, **k: dict(_INTU)
SU.send_usage_notification = lambda *a, **k: None
SU.toolruns.registrar = SU.toolruns._REGISTRAR_REAL
_O = st.session_state["_OBRA"]
SU.plan_ui.selector_proyecto = lambda key, ayuda="": (st.session_state.get("_ARRIBA"), {})
_P = SU.projects_data
_P.is_configured = lambda: True
_P.list_projects_for_field = lambda u, grupo=None, incluir_internos=False: [dict(_O)] if st.session_state.get("_ASIGNADA", True) else []
_P.list_projects = lambda *a, **k: [dict(_O)]
_P.get_project = lambda pid: dict(_O)
_P.survey_libre = lambda pid: st.session_state["_LIBRE"]
_L = st.session_state.setdefault("_LOG", [])
_P.attach_survey = lambda pid, **k: (_L.append(("attach", pid, k)) or (True, "ok"))
_P.add_document = lambda *a, **k: _L.append(("doc", a))
_P.head_installers_label = lambda *a, **k: "Head"
SU.drive_store.is_configured = lambda: True
SU.drive_store.is_available = lambda: st.session_state.get("_DRIVE", True)
SU.drive_store.upload = lambda pid, nombre, datos, mime="": (_L.append(("drive", nombre, datos, mime)) or "DRV-1")
SU.generate_user_report = lambda **k: b"%PDF"
SU.toolruns.registrar.__globals__["_next_id"] = lambda: "CAL-0077"
class _H:
    def append_row(self, fila, **k): _L.append(("fila", fila))
SU.toolruns.registrar.__globals__["_ws"] = lambda: _H()
SU.toolruns.registrar.__globals__["_invalidate"] = lambda: None
from core import projects as _PR
_PR.add_document = _P.add_document
import core.drive_store as _DS
_DS.upload = SU.drive_store.upload
SU.init_state()
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    P = {"BKS": 1600, "RAIL": 62, "TKSW": 965, "SF1": 51, "SF2": 51, "BS": 1998, "BSR": 1985,
         "BT": 900, "FRAME": 30, "TS": 1750, "TK": 1400, "TKA": 100, "TKS": 30, "TSW": 100,
         "FS": 120, "OFFSET_CABIN": 0, "SG": 300, "TG": 60, "LengthTemplate": 300,
         "BGS": 900, "BK": 1100, "BKF1": 450, "BKF2": 450}
    for k, v in P.items():
        st.session_state["inp_" + k] = float(v)
    st.session_state["ns"] = 6
    st.session_state["survey_df"] = pd.DataFrame({
        "WR": [95, 88, 76, 92, 85, 80], "FR": [830, 822, 810, 818, 826, 815],
        "OR": [280, 296, 310, 288, 302, 295], "WL": [90, 84, 98, 79, 88, 86],
        "FL": [828, 820, 812, 824, 819, 816], "OL": [285, 292, 300, 305, 290, 298]}).astype(float)
flash.mostrar()
SU.render_survey_tab(st.session_state.get("_ROL", "field"), "cliente1")
'''
OB = {"ID": "PRJ-1", "Name": "Obra *uno*", "Type": "Installation", "Status": "In progress", "Group": "cliente1",
      "NS": 6, "ParamsJSON": "{}", "MatrixJSON": "[]"}
OC = {**OB, "ParamsJSON": '{"NS": 6}', "MatrixJSON": '[{"WR": 90}]'}


def survey(obra, libre, rol="field", arriba=True, **ss):
    a = AppTest.from_string(GV, default_timeout=600)
    a.session_state["_ROL"] = rol
    a.session_state["_OBRA"] = obra
    a.session_state["_LIBRE"] = libre
    a.session_state["_ARRIBA"] = obra if arriba else None
    for k, v in ss.items():
        a.session_state[k] = v
    a.run()
    _btn(a, "btn_calc_datos").click()
    a.run()
    chk("   (calcula sin excepción)", not a.exception, [e.value for e in a.exception][:1])
    return a


a = survey(OB, True)
_h = [str(x.value) for x in a.header]
chk("⚠️ al campo no se le nombra «Client report» (una cabecera para decirle que no)",
    not [x for x in _h if "Client report" in x] and "Report downloads are available" not in _todo(a)
    and _btn(a, "sv_gen_informe_cliente") is None, [x for x in _todo(a).split(" | ") if "management" in x])
chk("…y SÍ tiene «Save to the project»", any("Save to the project" in x for x in _h), _h)
chk("⚠️ la obra de este cálculo, sin lista que elegir",
    "It will be saved to **Obra \\*uno\\***" in _todo(a) and not [s for s in a.selectbox if s.key == "sv_prj_sel"])
chk("…y sin aviso de que ya hay uno", "already has a saved survey" not in _todo(a))
chk("el botón dice lo de siempre", "Save the survey to this project" in str(_btn(a, "sv_save_prj").label))
_btn(a, "sv_save_prj").click()
a.run()
_L = a.session_state["_LOG"]
chk("sin excepción al guardar", not a.exception, [e.value for e in a.exception][:1])
_at = [x for x in _L if x[0] == "attach"]
chk("⚠️ obra sin survey: se ADJUNTA (es el survey de la obra)", len(_at) == 1 and _at[0][1] == "PRJ-1"
    and _at[0][2]["params"].get("NS") and len(_at[0][2]["matriz"]) == 6, _at[:1])
_fi = [x[1] for x in _L if x[0] == "fila"]
chk("…entra al historial de cálculos, sin marca de decisión",
    len(_fi) == 1 and "por_decidir" not in _fi[0][7], _fi)
chk("…con los documentos de siempre", {x[1] for x in _L if x[0] == "drive"} >= {"survey_matrix.csv", "client_report.pdf"},
    [x[1] for x in _L if x[0] == "drive"])
chk("⚠️ …sin el botón «Open project ➜» (lleva a la ficha de la oficina)", _btn(a, "ir_al_proyecto") is None
    and "_prj_creado" not in a.session_state)
chk("…y el survey empieza de cero", a.session_state["survey_fase"] == "📝 Survey data"
    and not a.session_state["calc_results"], a.session_state["survey_fase"])
chk("…y lo dice", "Survey saved to **PRJ-1 · Obra \\*uno\\***" in _todo(a), _todo(a)[:300])

a = survey(OC, False)
chk("⚠️ obra CON survey: lo dice ANTES de guardar",
    "already has a saved survey" in _todo(a) and "the office decides" in _todo(a), _todo(a)[-400:])
chk("…y el botón dice lo que va a hacer", "Save as a new calculation" in str(_btn(a, "sv_save_prj").label))
_btn(a, "sv_save_prj").click()
a.run()
_L = a.session_state["_LOG"]
chk("sin excepción", not a.exception, [e.value for e in a.exception][:1])
chk("⚠️⚠️ NO pisa: `attach_survey` no se llama", not [x for x in _L if x[0] == "attach"], [x[0] for x in _L])
_dr = [x for x in _L if x[0] == "drive"]
chk("⚠️ un solo archivo, en JSON (no el plano ni el informe)", len(_dr) == 1 and _dr[0][3] == "application/json"
    and _dr[0][1].endswith("_installer.json"), [(x[1], x[3]) for x in _dr])
_j = json.loads(_dr[0][2].decode("utf-8")) if _dr else {}
chk("⚠️ con TODO para cargarlo: parámetros y las 6 filas de la matriz",
    _j.get("params", {}).get("NS") == 6 and len(_j.get("matriz", [])) == 6 and _j["matriz"][0]["WR"] == 95.0,
    str(_j)[:200])
_fi = [x[1] for x in _L if x[0] == "fila"]
_d = json.loads(_fi[0][7]) if _fi else {}
chk("⚠️ la fila: survey, de installer, por decidir, enlazada al archivo",
    _fi and _fi[0][3] == "survey" and _fi[0][5] == "installer" and _d.get("por_decidir") is True
    and _fi[0][9] == "DRV-1", _fi[:1])
chk("…con su resumen («RL … · FB … · … out of limit»)", _fi and _fi[0][6].startswith("RL ") and "out of limit" in _fi[0][6])
chk("…y cabe: la fila no lleva la matriz (`DataJSON` se corta a 4800)", _fi and len(_fi[0][7]) < 200, len(_fi[0][7]) if _fi else 0)
chk("⚠️ se le dice qué pasó", "as a new calculation (CAL-0077)" in _todo(a) and "office" in _todo(a), _todo(a)[:300])
chk("…y empieza de cero", not a.session_state["calc_results"])

a = survey(OB, False)
_btn(a, "sv_save_prj").click()
a.run()
chk("⚠️⚠️ la caché decía «libre» y otro acaba de guardar el suyo: manda la lectura FRESCA, no pisa",
    not [x for x in a.session_state["_LOG"] if x[0] == "attach"]
    and [x for x in a.session_state["_LOG"] if x[0] == "fila"])

a = survey(OC, False, _DRIVE=False)
_btn(a, "sv_save_prj").click()
a.run()
_L = a.session_state["_LOG"]
chk("⚠️ sin Drive no se guarda nada: una fila sin archivo pediría decidir sobre la nada",
    not [x for x in _L if x[0] in ("attach", "fila", "drive")], [x[0] for x in _L])
chk("…lo dice", "Drive is not connected" in _todo(a), _todo(a)[-300:])
chk("⚠️ …y no pierde lo calculado (el resultado sigue, se puede reintentar)",
    bool(a.session_state["calc_results"]) and _btn(a, "sv_save_prj") is not None)

a = survey(OB, True, arriba=False)
chk("sin obra arriba: elige entre las suyas", [s for s in a.selectbox if s.key == "sv_prj_sel"]
    and "It will be saved" not in _todo(a))
a = survey(OB, True, arriba=False, _ASIGNADA=False)
chk("sin ninguna: lo dice, sin el botón de la oficina",
    "assign you to the project" in _todo(a) and _btn(a, "sv_ir_proyectos") is None
    and _btn(a, "sv_save_prj") is None, _todo(a)[-300:])

a = survey(OC, False, rol="administrator")
chk("⚠️ la oficina, igual que siempre: elige en la lista y sin aviso",
    [s for s in a.selectbox if s.key == "sv_prj_sel"] and "already has a saved survey" not in _todo(a)
    and "Save the survey to this project" in str(_btn(a, "sv_save_prj").label))
chk("…y con su informe del cliente", any("Client report" in str(x.value) for x in a.header)
    and _btn(a, "sv_gen_informe_cliente") is not None)
_btn(a, "sv_save_prj").click()
a.run()
chk("⚠️ …guardar SÍ sustituye: es su decisión", [x for x in a.session_state["_LOG"] if x[0] == "attach"]
    and "_prj_creado" in a.session_state)
GN = GV.replace('SU.render_survey_tab(st.session_state.get("_ROL", "field"), "cliente1")',
                'st.session_state["survey_fase"] = "📊 Resultados e informes"\n'
                'SU.render_survey_tab(st.session_state.get("_ROL", "field"), "cliente1")')
a = AppTest.from_string(GN, default_timeout=120)
a.session_state["_ROL"], a.session_state["_OBRA"], a.session_state["_LIBRE"] = "field", OB, True
a.run()
chk("sin cálculo, el aviso del campo no promete el informe del cliente",
    "No calculation yet" in _todo(a) and "client" not in _todo(a).lower().split("no calculation yet")[1][:220], _todo(a)[:300])

sec("7. El motor de la decisión")
chk("una obra nueva trae «{}» y «[]»: no tiene survey",
    not P.tiene_survey({"ParamsJSON": "{}", "MatrixJSON": "[]"}) and not P.tiene_survey({}))
chk("con parámetros o con matriz, sí", P.tiene_survey({"ParamsJSON": '{"NS": 6}', "MatrixJSON": "[]"})
    and P.tiene_survey({"ParamsJSON": "{}", "MatrixJSON": '[{"a": 1}]'}))


class HojaP:
    def __init__(self, filas=None, falla=False):
        self.filas, self.falla = filas or [], falla

    def get_all_records(self, **k):
        if self.falla:
            raise RuntimeError("cuota")
        return self.filas


_pw = P._projects_ws
P.survey_libre = _SURVEY_LIBRE_REAL
P._projects_ws = lambda: (HojaP([{"ID": "PRJ-1", "ParamsJSON": "{}", "MatrixJSON": "[]"}]), None)
chk("`survey_libre`: libre", P.survey_libre("PRJ-1") is True)
P._projects_ws = lambda: (HojaP([{"ID": "PRJ-1", "ParamsJSON": '{"NS":6}', "MatrixJSON": "[]"}]), None)
chk("…ocupada", P.survey_libre("PRJ-1") is False)
P._projects_ws = lambda: (HojaP([{"ID": "PRJ-2", "ParamsJSON": "{}"}]), None)
chk("⚠️ …una obra que no aparece no es «libre»", P.survey_libre("PRJ-1") is False)
P._projects_ws = lambda: (HojaP(falla=True), None)
chk("⚠️ …si no se puede leer, tampoco: no pisar es lo seguro", P.survey_libre("PRJ-1") is False)
P._projects_ws = lambda: (None, "sin hoja")
chk("…ni sin hoja", P.survey_libre("PRJ-1") is False)
P._projects_ws = _pw

R1 = {"ID": "CAL-7", "ProjectID": "PRJ-1", "Group": "cliente1", "Tool": "survey", "DriveID": "D1",
      "DataJSON": json.dumps({"por_decidir": True, "ns": 6})}
R2 = {"ID": "CAL-8", "ProjectID": "PRJ-1", "Group": "cliente1", "Tool": "survey", "DriveID": "D2",
      "DataJSON": json.dumps({"por_decidir": False, "decidido": {"como": "kept"}})}
R3 = {"ID": "CAL-9", "ProjectID": "PRJ-1", "Group": "cliente1", "Tool": "survey", "DriveID": "",
      "DataJSON": json.dumps({"por_decidir": True})}
R4 = {"ID": "CAL-1", "ProjectID": "PRJ-1", "Group": "cliente1", "Tool": "survey", "DriveID": "",
      "DataJSON": json.dumps({"rl": 1.0, "ns": 6})}
R5 = {"ID": "CAL-2", "ProjectID": "PRJ-1", "Group": "otro", "Tool": "survey", "DriveID": "D3",
      "DataJSON": json.dumps({"por_decidir": True})}
R6 = {"ID": "CAL-3", "ProjectID": "PRJ-1", "Group": "cliente1", "Tool": "plomada", "DriveID": "D4",
      "DataJSON": "{no es json"}
TR._records = lambda: [R1, R2, R3, R4, R5, R6]
chk("⚠️ por decidir: solo CAL-7 (no las decididas, ni sin archivo, ni de otro grupo, ni con JSON roto)",
    [r["ID"] for r in TR.survey_por_decidir("cliente1")] == ["CAL-7"], TR.survey_por_decidir("cliente1"))
chk("una decidida sigue siendo de esta clase (el archivo se puede cargar)", TR.es_survey_a_decidir(R2))
chk("…un survey normal, no", not TR.es_survey_a_decidir(R4) and not TR.es_survey_a_decidir(R6))


class Cel:
    row = 5


class HojaT:
    def __init__(self, hay=True, falla=False):
        self.hay, self.falla, self.esc = hay, falla, []

    def find(self, q, in_column=None):
        self.q = (q, in_column)
        return Cel() if self.hay else None

    def update_cell(self, r, c, v):
        if self.falla:
            raise RuntimeError("cuota")
        self.esc.append((r, c, v))


_inv = TR._invalidate
_invalidado = []
TR._invalidate = lambda: _invalidado.append(1)
h = HojaT()
TR._ws = lambda: h
_ok = TR.decidir_survey(R1, "kept", "Admin2")
_d = json.loads(h.esc[0][2]) if h.esc else {}
chk("⚠️ decidir escribe en SU fila y en DataJSON", _ok and h.q == ("CAL-7", 1)
    and h.esc and h.esc[0][:2] == (5, TR.HEADERS.index("DataJSON") + 1), h.esc[:1])
chk("…queda decidido, con quién y cómo", _d.get("por_decidir") is False
    and _d["decidido"]["como"] == "kept" and _d["decidido"]["por"] == "Admin2", _d)
chk("…conserva lo que había", _d.get("ns") == 6)
chk("…y tira la caché: la campana se apaga", bool(_invalidado))
h = HojaT(hay=False)
chk("una fila que ya no está: False", TR.decidir_survey(R1, "kept") is False)
h = HojaT(falla=True)
chk("⚠️ si la hoja falla: False, sin reventar", TR.decidir_survey(R1, "kept") is False)
TR._ws = lambda: None
chk("sin hoja: False", TR.decidir_survey(R1, "kept") is False)
_llam = []
_ds, TR.decidir_survey = TR.decidir_survey, lambda f, c, u="": _llam.append((f["ID"], c, u))
TR.decidir_por_drive("D1", "Admin2")
chk("⚠️ borrar el archivo cierra la decisión", _llam == [("CAL-7", "deleted", "Admin2")], _llam)
_llam.clear()
TR.decidir_por_drive("D2")
TR.decidir_por_drive("D4")
chk("…solo si estaba por decidir", _llam == [], _llam)
TR.decidir_survey = _ds
TR._invalidate = _inv

sec("8. ⚠️ La oficina decide (Files, clics reales)")
GD = r'''
import json
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"})
from core import projects_ui as PU, toolruns as TR, drive_store as DS, projects as P, flash
_L = st.session_state.setdefault("_LOG", [])
_pl = {"params": {"BKS": 1600, "NS": 6}, "matriz": [{"WR": 95.0}, {"WR": 88.0}]}
DS.download = lambda did: json.dumps(_pl).encode() if not st.session_state.get("_ROTO") else b"no json"
P.get_project = lambda pid: {"ID": pid, "Name": "Obra uno", "Group": "cliente1"}
P.head_installers_label = lambda *a, **k: "Head"
TR.decidir_survey = lambda f, c, u="": (_L.append((f["ID"], c, u)) or True)
flash.mostrar()
PU._decidir_survey("PRJ-1", "DRV-1", st.session_state["_RUN"])
'''
a = AppTest.from_string(GD, default_timeout=60)
a.session_state["_RUN"] = R1
a.run()
chk("sin excepción", not a.exception, [e.value for e in a.exception][:1])
chk("explica qué pasa y que cargarlo no sustituye nada", "did not replace it" in _todo(a)
    and "only changes if you then save" in _todo(a), _todo(a))
chk("los dos caminos", _btn(a, "arch_svcarga_PRJ-1") is not None and _btn(a, "arch_svquedar_PRJ-1") is not None)
_btn(a, "arch_svquedar_PRJ-1").click()
a.run()
chk("⚠️ «Keep»: decidido, y sin tocar el Survey",
    a.session_state["_LOG"] == [("CAL-7", "kept", "Admin2")] and "_rebuilt_from" not in a.session_state,
    a.session_state["_LOG"])
chk("…lo dice", "keeps its survey" in _todo(a), _todo(a))
a = AppTest.from_string(GD, default_timeout=60)
a.session_state["_RUN"] = R1
a.run()
_btn(a, "arch_svcarga_PRJ-1").click()
a.run()
chk("sin excepción al cargar", not a.exception, [e.value for e in a.exception][:1])
_df = a.session_state["survey_df"]
chk("⚠️ «Load»: la matriz del archivo en el Survey", list(_df["WR"]) == [95.0, 88.0], _df)
chk("…los parámetros y las paradas", a.session_state["inp_BKS"] == 1600.0 and a.session_state["ns"] == 6)
chk("…la obra ya elegida para guardarla ahí", a.session_state["pl_prj_sv"] == "Obra uno (PRJ-1)")
chk("…y lleva al Survey", a.session_state["_admin_nav_pending"] == ("herramientas", "📐 Survey"),
    a.session_state["_admin_nav_pending"] if "_admin_nav_pending" in a.session_state else None)
chk("⚠️ …la decisión queda cerrada (se apaga la campana)", a.session_state["_LOG"] == [("CAL-7", "loaded", "Admin2")])
a = AppTest.from_string(GD, default_timeout=60)
a.session_state["_RUN"] = R2
a.run()
chk("ya decidida: se puede volver a cargar, sin «Keep» ni aviso",
    _btn(a, "arch_svcarga_PRJ-1") is not None and _btn(a, "arch_svquedar_PRJ-1") is None
    and "did not replace it" not in _todo(a))
a = AppTest.from_string(GD, default_timeout=60)
a.session_state["_RUN"] = R1
a.session_state["_ROTO"] = True
a.run()
_btn(a, "arch_svcarga_PRJ-1").click()
a.run()
chk("⚠️ un archivo ilegible: lo dice y NO cierra la decisión",
    not a.exception and "could not be read" in _todo(a) and a.session_state["_LOG"] == [], _todo(a))
_ac = inspect.getsource(__import__("core.projects_ui", fromlist=["x"])._acciones_archivo)
chk("⚠️ solo la oficina decide (`puede_borrar`), y solo con archivo",
    "if puede_borrar and did and bool(run) and toolruns.es_survey_a_decidir(run):" in _ac)
_as = _src("projects_ui.py")
chk("borrar el archivo cierra la decisión (en el borrado confirmado)",
    "toolruns.decidir_por_drive(_pend[\"did\"]" in _as)
chk("«Rebuild» y la decisión cargan con la MISMA función",
    _as.count("_cargar_en_survey(") == 3 and "_ev.respetar(\"sv\", pid)" in inspect.getsource(
        __import__("core.projects_ui", fromlist=["x"])._cargar_en_survey))

print("\n   Lo cargado llega al Survey de verdad (selector real, obra elegida, plano que no lo pisa)")
GL = r'''
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"})
from core import survey_ui as SU, plan_data, projects as P, projects_ui as PU
_O = {"ID": "PRJ-1", "Name": "Obra uno", "Type": "Installation", "Status": "In progress", "Group": "cliente1", "Client": "c", "Location": "l"}
P.is_configured = lambda: True
P.list_projects = lambda *a, **k: [_O]
P.get_project = lambda pid: dict(_O)
P.head_installers_label = lambda *a, **k: "Head"
plan_data.del_proyecto = lambda pid: {"lfkk": 1, "params": {"BKS": 9999}}
plan_data.resumen = lambda d: "plano"
SU.init_state()
if "_CARGADO" not in st.session_state:
    st.session_state["_CARGADO"] = 1
    PU._cargar_en_survey("PRJ-1", _O, "cliente1", {"BKS": 1600, "NS": 6}, [{"WR": 95.0, "FR": 830.0, "OR": 280.0, "WL": 90.0, "FL": 828.0, "OL": 285.0}] * 6)
    st.session_state["pl_prj_sv"] = "Obra uno (PRJ-1)"
SU.render_survey_tab("administrator", "cliente1")
'''
a = AppTest.from_string(GL, default_timeout=120).run()
chk("sin excepción", not a.exception, [e.value for e in a.exception][:1])
chk("⚠️ la obra sale elegida en el Survey", a.session_state["pl_prj_sv"] == "Obra uno (PRJ-1)")
chk("⚠️ …y el plano de la obra NO pisa lo cargado (BKS 1600, no 9999)", a.session_state["inp_BKS"] == 1600.0,
    a.session_state["inp_BKS"])
chk("…y avisa de lo cargado", "You loaded project **Obra uno**" in _todo(a), _todo(a)[:300])

sec("9. ⚠️ La campana")
GC = r'''
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "x", "nombre": "x", "rol": st.session_state.get("_ROL", "administrator"), "grupo": "cliente1"})
from core import home_ui, toolruns as TR, projects as P, admin_digest, credentials as C, inventory as I
admin_digest.group_digest = lambda g: {}
C.is_configured = lambda: False
I.is_configured = lambda: False
TR.survey_por_decidir = lambda g: [{"ID": "CAL-7", "ProjectID": "PRJ-1"}]
P.get_project = lambda pid: {"Name": "Obra uno"}
home_ui.navegar = lambda *a: st.session_state.__setitem__("_NAV", a)
st.session_state["_AL"] = home_ui._alertas_items("cliente1")
if st.session_state.get("_IR"):
    home_ui._ir_alerta(st.session_state["_AL"][-1]["destino"], "cliente1")
'''
a = AppTest.from_string(GC, default_timeout=60).run()
_al = [x for x in a.session_state["_AL"] if "survey from the field" in x["texto"]]
chk("⚠️ a la oficina le sale, con la obra", len(_al) == 1 and "**Obra uno**" in _al[0]["texto"], a.session_state["_AL"])
chk("…y lleva a los archivos de ESA obra", _al and _al[0]["destino"] == ("archivos", "PRJ-1"))
a = AppTest.from_string(GC, default_timeout=60)
a.session_state["_IR"] = True
a.run()
chk("⚠️ tocarla abre la obra en Files", a.session_state["_prjsel_pending"] == "PRJ-1"
    and a.session_state["_prj_sec_pending"] == "📎 Archivos" and a.session_state["_NAV"] == ("proyectos", "📊 Proyectos"))
a = AppTest.from_string(GC, default_timeout=60)
a.session_state["_ROL"] = "field"
a.run()
chk("al campo no le sale", not [x for x in a.session_state["_AL"] if "survey from the field" in x["texto"]])

print("\n%d ok, %d fallos" % (n_ok, len(fallos)))
for x in fallos:
    print("  FALLO:", x)
sys.exit(1 if fallos else 0)
