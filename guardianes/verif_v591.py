"""v591 · Lo visto verificando v590 (decisión del usuario: «Ok dale terminalo»).

⚠️ «17 values taken from the project drawing. Check them and fill in the ones measured on site»
NO lo vio nadie: se pintaba solo en la pasada que RELLENABA los campos, y esa pasada cambia NS
de 2 a 8 (el del plano) y relanza para redimensionar la matriz. En producción no salió ni en
v589 ni en v590. → fijo mientras esté el plano de la obra (sin la cifra: ya la da la línea del
plano, «17/17 parameters»).

EJECUTANDO el camino real con AppTest: obra con plano de NS 8 sobre un Survey en NS 2.
"""
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Admin2", "rol": "administrator", "grupo": "cliente1"}
from streamlit.testing.v1 import AppTest                         # noqa: E402

fallos, n_ok = [], 0


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("   ok   " + q)
    else:
        fallos.append(q)
        print("   FALLO " + q + (("  -> " + str(det)) if det != "" else ""))


G = r'''
import streamlit as st
import importlib
st.session_state.setdefault("auth", {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"})
from core import survey_ui as SU, flash, plan_ui
plan_ui = importlib.reload(plan_ui)
SU.plan_ui = plan_ui
_RUNS = st.session_state.setdefault("_RUNS", [0])
_RUNS[0] += 1
_PRJ = {"ID": "PRJ-1", "Name": "Lift A", "Type": "Installation", "Status": "In progress", "Group": "cliente1"}
_PLANO = st.session_state.get("_PLANO", {})
SU.plan_ui.selector_proyecto = lambda key, ayuda="": (_PRJ, _PLANO)
SU.projects_data.head_installers_label = lambda *a, **k: "CI"
SU.projects_data.list_projects = lambda *a, **k: []
SU.init_state()
flash.mostrar()
SU.render_survey_tab("administrator", "cliente1")
'''
_PL = {"params": {"BS": 1998, "TS": 1750, "BK": 1100, "TK": 1400, "BKS": 1772, "BT": 900, "TKA": 100,
                  "TKS": 30, "TSW": 100, "TKSW": 965, "BKF1": 450, "BKF2": 450, "SF1": 51, "SF2": 51,
                  "BGS": 900, "SG": 300, "TG": 60},
       "ns": 8, "rail": "T75-3/B", "rail_altura": 62, "faltan": [], "n_params": 17, "n_total": 17}

print("1. ⚠️ Obra con plano (NS 8) sobre un Survey en NS 2: el aviso SIGUE en pantalla")
at = AppTest.from_string(G, default_timeout=300)
at.session_state["_PLANO"] = _PL
at.run()
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("CONTROL: el camino real pasó por el `st.rerun()` de la matriz (NS 2 → 8, más de una pasada)",
    at.session_state["ns"] == 8 and at.session_state["_RUNS"][0] >= 2
    and len(at.session_state["survey_df"]) == 8, (at.session_state["ns"], at.session_state["_RUNS"]))
_cap = " | ".join(str(c.value) for c in at.caption)
chk("⚠️ y el aviso «check them and fill in the ones measured on site» SE VE al final",
    "Check them and fill in the ones measured on site." in _cap, _cap[:400])
at.run()
_cap2 = " | ".join(str(c.value) for c in at.caption)
chk("…y sigue en la pasada siguiente (fijo, no de una pasada)",
    "Check them and fill in the ones measured on site." in _cap2)

print("\n2. Una obra SIN plano no lo dice")
at = AppTest.from_string(G, default_timeout=300)
at.session_state["_PLANO"] = {}
at.run()
chk("sin plano, sin el aviso", not at.exception and "fill in the ones measured on site" not in
    " | ".join(str(c.value) for c in at.caption))
# (la 1ª tanda de romper_v591 dejó escapar «sale también sin plano»: con `{}` ni se entra en el
# bloque. El caso que importa es un plano GUARDADO sin parámetros —la lectura del PDF falló—: ahí
# «los campos vienen del plano» sería falso.)
at = AppTest.from_string(G, default_timeout=300)
at.session_state["_PLANO"] = {"params": {}, "ns": 8, "faltan": list(_PL["params"]), "n_params": 0,
                              "n_total": 17}
at.run()
chk("⚠️ un plano guardado SIN parámetros (lectura fallida) tampoco lo dice",
    not at.exception and "fill in the ones measured on site" not in
    " | ".join(str(c.value) for c in at.caption))

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
sys.exit(1 if fallos else 0)
