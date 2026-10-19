"""v583 · Lo visto verificando v582 (decisión del usuario: «ok dale»).

  1. ⚠️ «Used in N quotes» abría Quotes pero, si el ALTA de cotización seguía abierta (tras
     «Set it in Catalogue»), salía el alta delante de la cotización pedida (visto en
     producción) → el botón cierra el alta.
  2. ⚠️ Y el borrador de ese alta perdía el cliente y la nota al salir de Quotes: Streamlit
     borra un widget en cuanto una pasada no lo pinta (las líneas sí vivían, en `new_lineas`)
     → `_cot_borrador`, una clave que no es de widget, y se devuelven al volver.

AppTest con sus fuentes sustituidas: ninguna hoja se toca.
"""
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
fallos, n_ok = [], 0


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("  ok   " + q)
    else:
        fallos.append(q)
        print("  FALLO " + q + (("  -> " + str(det)) if det != "" else ""))


from streamlit.testing.v1 import AppTest                                    # noqa: E402

CAB = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
from core import quotes_ui as QU, clientes as C, catalogo as CAT, auth
st.session_state["auth"] = {"rol": "administrator", "usuario": "adm", "grupo": "G"}
C.list_clientes = lambda g, **k: [{"ID": "CLI-1", "Name": "Cli"}]
CAT.list_items = lambda g, **k: [{"ID": "CAT-1", "Type": "product", "Name": "A", "UnitCost": "10",
                                  "Unit": "unit", "QtyRule": "fixed"}]
auth.group_tax_default = lambda g: 10.0
auth.group_margin_default = lambda g: 20.0
if "_INI" not in st.session_state:                  # el alta, abierta (como la abre «New quote»)
    st.session_state["_INI"] = 1
    st.session_state["_cot_nueva"] = True
# como la shell: el alta solo se pinta mientras esté ABIERTA y se esté en Quotes
if st.session_state.get("_VER", "cot") == "cot" and st.session_state.get("_cot_nueva"):
    QU._nueva("G")
else:
    st.write("otra sección")
''' % RAIZ


def _ss(a, k, d=None):
    try:
        return a.session_state[k]
    except KeyError:
        return d


print("2. El borrador del alta sobrevive a salir de Quotes")
at = AppTest.from_string(CAB, default_timeout=90)
at.run()
chk("el alta se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_nuevo = [o for o in at.selectbox(key="cot_new_cli").options if "New client" in str(o)]
at.selectbox(key="cot_new_cli").set_value(_nuevo[0] if _nuevo else None)
at.run()
at.text_input(key="cot_new_cli_nom").set_value("Cliente nuevo")
at.text_input(key="cot_new_cli_tel").set_value("0400 000 000")
at.text_area(key="cot_new_nota").set_value("Nota del borrador")
at.run()
at.session_state["_VER"] = "otro"
at.run()
# ⚠️ La sonda primero: si Streamlit NO borrara al salir, la prueba no probaría nada
chk("(sonda) salir de Quotes BORRA los widgets del alta, como en producción",
    _ss(at, "cot_new_cli_nom") is None and _ss(at, "cot_new_nota") is None,
    (_ss(at, "cot_new_cli_nom"), _ss(at, "cot_new_nota")))
at.session_state["_VER"] = "cot"
at.run()
chk("al volver, sin excepción ni aviso de Streamlit", not at.exception and not
    [w for w in at.warning if "Session State" in str(w.value)], [e.value for e in at.exception][:1])
chk("⚠️ el cliente NUEVO elegido vuelve", "New client" in str(at.selectbox(key="cot_new_cli").value),
    at.selectbox(key="cot_new_cli").value)
chk("⚠️ …con su nombre y su teléfono", at.text_input(key="cot_new_cli_nom").value == "Cliente nuevo"
    and at.text_input(key="cot_new_cli_tel").value == "0400 000 000",
    (at.text_input(key="cot_new_cli_nom").value, at.text_input(key="cot_new_cli_tel").value))
chk("⚠️ …y la nota", at.text_area(key="cot_new_nota").value == "Nota del borrador",
    at.text_area(key="cot_new_nota").value)
at.button(key="cot_new_back").click()
at.run()
chk("«Cancel» tira el borrador y la nota (la próxima empieza vacía)", _ss(at, "_cot_borrador") is None
    and _ss(at, "_cot_nueva") is None and _ss(at, "cot_new_nota") is None,
    (_ss(at, "_cot_borrador"), _ss(at, "cot_new_nota")))

at = AppTest.from_string(CAB, default_timeout=90)
at.run()
at.selectbox(key="cot_new_cli").set_value("Cli")
at.run()
at.session_state["_VER"] = "otro"
at.run()
at.session_state["_VER"] = "cot"
at.run()
chk("una ficha EXISTENTE elegida también vuelve", at.selectbox(key="cot_new_cli").value == "Cli",
    at.selectbox(key="cot_new_cli").value)

print("\n1. «Used in N quotes» abre la cotización aunque el alta siguiera abierta")
CAB2 = r'''
import sys, json
sys.path.insert(0, r"%s")
import streamlit as st
from core import catalogo_ui as CU, catalogo as CAT, quotes as Q
st.session_state["auth"] = {"rol": "administrator", "usuario": "adm", "grupo": "G"}
CAT._records = lambda: [{"ID": "CAT-2", "Group": "G", "Type": "service", "Name": "Montaje",
                         "EstHours": "8", "HourlyRate": "60", "Active": "SI"}]
CAT.is_configured = lambda: True
Q._records = lambda: [{"ID": "COT-1", "Group": "G", "Date": "2026-10-01", "Number": "0001",
                       "Version": "1", "ClientName": "Cli", "Status": "sent", "Total": "300",
                       "ValidUntil": "2099-01-01", "LinesJSON": json.dumps([{"catalogo_id": "CAT-2"}])}]
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    st.session_state["_cat_open"] = "CAT-2"
    st.session_state["_cot_nueva"] = True          # el alta, abierta desde antes
CU.render_catalogo("G")
''' % RAIZ
at = AppTest.from_string(CAB2, default_timeout=90)
at.run()
at.button(key="cat_uso_COT-1").click()
at.run()
chk("⚠️ el botón CIERRA el alta (si no, Quotes la pinta delante de la cotización)",
    _ss(at, "_cot_nueva") is None, _ss(at, "_cot_nueva"))
chk("…y pide ESA cotización en Quotes", _ss(at, "_cot_open") == "COT-1"
    and tuple(_ss(at, "_admin_nav_pending") or ()) == ("finanzas", "📄 Cotizaciones"),
    (_ss(at, "_cot_open"), _ss(at, "_admin_nav_pending")))
_qs = io.open(os.path.join(RAIZ, "core", "quotes_ui.py"), encoding="utf-8").read()
chk("el impuesto NO entra en el borrador (lleva `value=`: reasignarlo saca el aviso de Streamlit)",
    '"cot_new_imp"' not in _qs.split("_BORRADOR = (")[1].split(")")[0])

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
sys.exit(1 if fallos else 0)
