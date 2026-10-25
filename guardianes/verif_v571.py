# -*- coding: utf-8 -*-
"""v571 · LO VISTO EN LA FICHA DEL CLIENTE VERIFICANDO v570 (decisión del usuario: «De una»).

  1. El resumen del cliente eran `st.metric` que no se podían tocar (y las alertas, una
     línea suelta) → tarjetas-BOTÓN; cada una abre debajo, a todo el ancho, el desglose
     por obra con su filtro u orden (activas, menos avanzadas primero, más horas, más
     coste, con alertas), la vista baja a él una vez y un toque abre la obra (en Costs si
     se vino por el coste). Lo abierto es de ESA ficha.
  2. Textos sin `t()`: «{n} project(s) linked.», «open alert(s)», «… archived client(s)
     hidden.», «Tap a client… ({n} client(s))», «See the address on the map»; y el estado
     de cada obra salía crudo (es un DATO de la hoja) → `etiqueta`.
  3. La columna «Cost» de la lista de clientes salía en dólares enteros (`round(…, 0)` +
     `$%,d`) → con céntimos, como el resto de tablas de dinero.

AppTest con las fuentes sustituidas: ninguna hoja se toca.
"""
import ast
import io
import json
import os
import re
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
import streamlit as st
from core import clientes as C, projects as P, alerts, expenses, invoices as I, incrustar, flash
from core import clientes_ui as CU
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G",
                                     "nombre": "Jefa"})
st.session_state.setdefault("_LL", [])
incrustar.script = lambda h, *a, **k: st.session_state["_LL"].append("script")
_PR = [{"ID": "PRJ-A", "Name": "Alfa", "Group": "G", "Status": "Completed", "Progress": "100", "ClientID": "CLI-1"},
       {"ID": "PRJ-B", "Name": "Beta", "Group": "G", "Status": "In progress", "Progress": "40", "ClientID": "CLI-1"},
       {"ID": "PRJ-C", "Name": "Gamma", "Group": "G", "Status": "Planned", "Progress": "0", "ClientID": "CLI-1"}]
C.is_configured = lambda: True
C.list_clientes = lambda g=None, **k: [{"ID": "CLI-1", "Name": "Cliente Uno", "Group": "G", "Active": "SI"},
                                       {"ID": "CLI-2", "Name": "Otro", "Group": "G", "Active": "SI"}]
C.get_cliente = lambda cid: {"ID": cid, "Name": "Cliente Uno", "Active": "SI"}
C.es_del_cliente = lambda p, cid, cn: cid == "CLI-1"
C.client_key = lambda p, by_id: ("cliente uno", "Cliente Uno")
P.list_projects = lambda *a, **k: [dict(x) for x in _PR]
P.project_hours_bulk = lambda g: {"PRJ-A": 3.0, "PRJ-B": 12.5}
alerts.is_configured = lambda: True
alerts.open_counts_all = lambda: {"PRJ-B": 2}
expenses.is_configured = lambda: True
expenses.group_expenses = lambda g: {"proyectos": [{"id": "PRJ-A", "total": 80.0},
                                                   {"id": "PRJ-B", "total": 270.6},
                                                   {"id": "PRJ-C", "total": 0.0}]}
I.is_configured = lambda: False
flash.mostrar()
if st.session_state.get("_LISTA"):
    CU.render_contactos("G")
else:
    CU._detalle_cliente("G", st.session_state.get("_KEY", "cliente uno"))
'''


def _app(**ss):
    a = AppTest.from_string(CAB, default_timeout=90)
    for k, v in ss.items():
        a.session_state[k] = v
    a.run()
    return a


def _clic(at, key):
    [b for b in at.button if b.key == key][0].click()
    at.run()


# ══════════════════════════════════════════════════════════════════════════════
print("1. El resumen del cliente, ACTIVO")
at = _app()
chk("la ficha se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_kb = {b.key: b.label for b in at.button if str(b.key).startswith("cpxkpi_cls_")}
chk("⚠️ seis cifras-BOTÓN (eran `st.metric`; las alertas, una línea suelta)",
    list(_kb) == ["cpxkpi_cls_prj", "cpxkpi_cls_act", "cpxkpi_cls_av", "cpxkpi_cls_hrs",
                  "cpxkpi_cls_cost", "cpxkpi_cls_al"], list(_kb))
chk("…con sus valores: 3 obras, 2 activas, 47 % de media, 15.5 h, $351, 2 alertas",
    [v.split("\n\n")[1] for v in _kb.values()] == ["3", "2", "47%", "15.5 h", "\\$351", "2"],
    [v.split("\n\n")[1] for v in _kb.values()])
chk("ningún `st.metric` queda en la ficha", not at.metric, [m.label for m in at.metric])
chk("con alertas, su tarjeta en rojo", any(".st-key-cpxkpi_cls_al button{border-left-color:#c0392b"
                                           in m.value for m in at.markdown))
chk("cerrado de entrada: ni desglose ni script", not at.dataframe and "script" not in at.session_state["_LL"])


def _tabla(at):
    return at.dataframe[0].value if at.dataframe else None


_clic(at, "cpxkpi_cls_act")
_v = _tabla(at)
chk("⚠️ «Active» abre el desglose: solo las NO completadas (Beta, Gamma)",
    _v is not None and list(_v["Proyecto"]) == ["Beta", "Gamma"], None if _v is None else list(_v["Proyecto"]))
chk("…con su título", any("Its active projects (not completed)" in m.value for m in at.markdown))
chk("⚠️ …y la vista BAJA a él una vez (`_bajar_a`)", at.session_state["_LL"].count("script") == 1,
    at.session_state["_LL"])
_cj = json.loads(at.dataframe[0].proto.columns)
_enum = at.dataframe[0].proto.DESCRIPTOR.fields_by_name["selection_mode"].enum_type
chk("columnas: obra FIJADA, estado, avance en barra, horas, coste con céntimos, alertas; un toque",
    list(_v.columns) == ["Proyecto", "Estado", "Avance", "Horas", "Costo", "Alarms"]
    and _cj.get("Proyecto", {}).get("pinned") is True
    and _cj.get("Costo", {}).get("type_config", {}).get("format") == "$%,.2f"
    and [_enum.values_by_number[x].name for x in at.dataframe[0].proto.selection_mode] == ["SINGLE_CELL"],
    (list(_v.columns), _cj.get("Costo")))
_clic(at, "cpxkpi_cls_av")
chk("«Avg. progress»: todas, la menos avanzada primero",
    list(_tabla(at)["Proyecto"]) == ["Gamma", "Beta", "Alfa"], list(_tabla(at)["Proyecto"]))
chk("…y la vista vuelve a bajar (otra petición)", at.session_state["_LL"].count("script") == 2,
    at.session_state["_LL"])
_clic(at, "cpxkpi_cls_hrs")
chk("«Hours»: la de más horas primero", list(_tabla(at)["Proyecto"]) == ["Beta", "Alfa", "Gamma"]
    and list(_tabla(at)["Horas"]) == [12.5, 3.0, 0.0], list(_tabla(at)["Horas"]))
_clic(at, "cpxkpi_cls_al")
chk("«Open alerts»: solo las que tienen", list(_tabla(at)["Proyecto"]) == ["Beta"], list(_tabla(at)["Proyecto"]))
_clic(at, "cpxkpi_cls_cost")
chk("«Total cost»: la más cara primero, con céntimos",
    list(_tabla(at)["Proyecto"]) == ["Beta", "Alfa", "Gamma"] and list(_tabla(at)["Costo"])[0] == 270.6,
    list(_tabla(at)["Costo"]))
_clic(at, "cpxkpi_cls_cost")
chk("la misma cifra otra vez lo CIERRA", not at.dataframe)

print("\n   …lo abierto es de ESA ficha, y un toque abre la obra")
_clic(at, "cpxkpi_cls_prj")
at.session_state["_KEY"] = "otro"
at.run()
chk("⚠️ otra ficha nace cerrada (no hereda el desglose)", not at.dataframe and not at.exception,
    [e.value for e in at.exception][:1])
at = _app(**{"_cls_vista::cliente uno": "cost",
             "_INI_SEL": 1})
at.session_state["cls_tbl_0"] = {"selection": {"rows": [], "columns": [], "cells": [(0, "Horas")]}}
at.run()
chk("⚠️ tocar una celda del desglose del COSTE abre esa obra en Costs",
    at.session_state["_prjsel_pending"] == "PRJ-B" and at.session_state["_prj_sec_pending"] == "💰 Costos"
    and at.session_state["_admin_nav_pending"] == ("proyectos", "📊 Proyectos")
    and at.session_state["_cls_tbl_gen"] == 1 if "_prjsel_pending" in at.session_state else False)
at = _app(**{"_cls_vista::cliente uno": "act"})
at.session_state["cls_tbl_0"] = {"selection": {"rows": [], "columns": [], "cells": [(1, "Proyecto")]}}
at.run()
chk("…y desde las demás, en Status (Gamma, 2ª de las activas)",
    at.session_state["_prjsel_pending"] == "PRJ-C" and at.session_state["_prj_sec_pending"] == "📊 Estado"
    if "_prjsel_pending" in at.session_state else False)

# ══════════════════════════════════════════════════════════════════════════════
print("\n2. Los textos")
_src = io.open(os.path.join(RAIZ, "core", "clientes_ui.py"), encoding="utf-8").read()
_arb = ast.parse(_src)
_DISP = {"caption", "markdown", "info", "warning", "success", "error", "button", "exito", "aviso",
         "maps_link_md", "metric", "checkbox", "text_input", "expander"}
_lit = []


def _frase(tx):
    """¿Hay FRASE? Dos palabras o más, sin mirar qué las separa. ⚠️ La 1ª sonda pedía
    «palabra ESPACIO palabra» y «{n} project(s) linked.» se le escapaba: entre «project» y
    «linked» hay un «(s)» (romper_v571 lo pilló)."""
    tx = re.sub(r":material/\w+:", "", tx)
    return not tx.lstrip().startswith("<") and len(re.findall(r"[A-Za-z]{2,}", tx)) >= 2


for n in ast.walk(_arb):
    if not (isinstance(n, ast.Call) and isinstance(n.func, (ast.Attribute, ast.Name))):
        continue
    _fn = n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id
    if _fn not in _DISP:
        continue
    for a in n.args:
        if isinstance(a, ast.Constant) and isinstance(a.value, str) and _frase(a.value):
            _lit.append("%d %s" % (n.lineno, a.value[:50]))
        elif isinstance(a, ast.JoinedStr) and _frase(
                "".join(v.value for v in a.values if isinstance(v, ast.Constant))):
            _lit.append("%d %s" % (n.lineno, ast.unparse(a)[:50]))
# ⚠️ Trampa 12: la sonda tiene que VER el caso que se le escapó
chk("la sonda ve «{n} project(s) linked.» en un f-string", _frase(" project(s) linked.")
    and not _frase("**") and not _frase(" · ") and not _frase("## :material/apartment: "))
chk("⚠️ ningún texto de pantalla sin `t()` en Contacts (los f-string de avisos y pies, el mapa)",
    not _lit, _lit)
_lbl = [n for n in ast.walk(_arb) if isinstance(n, ast.Assign) and any(
    getattr(tg, "id", "") == "_lbl" for tg in n.targets) and isinstance(n.value, ast.JoinedStr)]
chk("el estado de cada obra, con `etiqueta` (es un DATO de la hoja)",
    _lbl and any(isinstance(x, ast.Call) and getattr(x.func, "id", "") == "_etq"
                 for x in ast.walk(_lbl[0].value)), [ast.unparse(x)[:70] for x in _lbl])

# ══════════════════════════════════════════════════════════════════════════════
print("\n3. La lista de clientes: el coste con céntimos")
at = _app(_LISTA=True)
chk("la lista se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_d = at.dataframe[0]
_cj = json.loads(_d.proto.columns)
chk("⚠️ «Cost» con céntimos: $350.60 y formato `$%,.2f` (era `round(…, 0)` + `$%,d`)",
    list(_d.value["Costo"]) == [350.6, 0.0] and _cj.get("Costo", {}).get("type_config", {}).get("format") == "$%,.2f",
    (list(_d.value["Costo"]), _cj.get("Costo")))
# (dos fichas en el guion: «Otro» no tiene obras — la 1ª sonda esperaba una fila)
# (v602 · con su plural de verdad: «(2 clients)», no «(2 client(s))»)
chk("los pies, traducibles: «… (2 clients)»",
    any("Tap a client to see its record, summary and projects. (2 clients)" in c.value for c in at.caption),
    [c.value for c in at.caption])

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("TODO OK")
