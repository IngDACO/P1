"""v602 · CONTACTS → LA LISTA, PROBADA (decisión del usuario: «Dale con todo»).

Visto en producción (26/10/2026, cliente1, un cliente de PRUEBA «ZZ Prueba Contacts v602»):
  ⚠️ un cliente ARCHIVADO no se podía recuperar: su ficha decía «no record yet» (buscaba solo
     entre las activas, y por nombre), sin «Restore», y «Save record» respondía «already exists»;
  ⚠️ Enter enviaba «New client» a medias (creado solo con el nombre) y el formulario no se vaciaba;
  ⚠️ archivar volvía a la lista sin decir nada;
  el archivado no se distinguía en la tabla; la búsqueda y la casilla se perdían al volver de
  una ficha; «0290001003» no encontraba «02 9000 1003»; «nada coincide» sin salida; las cifras no
  bajaban a la tabla; las obras del cliente quedaban fuera de la vista (columnas); el avance medio
  contaba las canceladas; horas sin unidad, «Alarms», «yes», plurales «(s)»; teléfono y email
  mudos y sin validar.
La hoja va SUSTITUIDA en memoria: nada toca la real.
"""
import ast
import io
import json
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "jefa", "rol": "administrator", "grupo": "G"}
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


def fuente(rel):
    return io.open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8").read()


# ═══════════════════════════════════════════════════════════════════════════════════════════
print("1. El motor: el email con forma de email, el teléfono sin espacios, archivar/restaurar con su mensaje")
from core import clientes as C                                   # noqa: E402
chk("`email_valido`: vacío vale (es opcional), «a@b.co» vale; «abc», «a@b» y «a b@c.com» no",
    C.email_valido("") and C.email_valido("ops@ryderetail.example") and not C.email_valido("abc")
    and not C.email_valido("a@b") and not C.email_valido("a b@c.com"))
chk("`solo_digitos`: «02 9000 1003» → «0290001003»; «+61 (2) 9000» → «6129000»",
    C.solo_digitos("02 9000 1003") == "0290001003" and C.solo_digitos("+61 (2) 9000") == "6129000")
_esc = []


class _W:
    def append_row(self, row, **k):
        _esc.append(row)

    def get_all_records(self, **k):
        return [{"ID": "CLI-1", "Name": "Uno"}]

    def batch_update(self, b, **k):
        _esc.append(b)


C._ws = lambda: (_W(), None)
C._records = lambda: []
C._invalidate = lambda: None
C._next_id = lambda: "CLI-9"
_r = C.create_cliente("G", "Nuevo", email="abc")
chk("⚠️ el alta RECHAZA un email que no lo es (se guardaba «abc»)", _r[0] is False and not _esc, _r)
chk("…y con uno bueno, crea", C.create_cliente("G", "Nuevo", email="a@b.co") == (True, "CLI-9") and len(_esc) == 1)
_n = len(_esc)
_r = C.update_cliente("CLI-1", {"Email": "nada"})
chk("…la edición también (y sin tocar la hoja)", _r[0] is False and len(_esc) == _n, _r)
_upd = C.update_cliente
C.update_cliente = lambda cid, f: (True, "Client updated.")
chk("⚠️ archivar dice «Client archived.» (volvía a la lista sin decir nada); restaurar, «Client restored.»",
    C.set_activo("CLI-1", False) == (True, "Client archived.") and C.set_activo("CLI-1", True) == (True, "Client restored."))
C.update_cliente = _upd
_F = [{"ID": "CLI-1", "Name": "Meridian", "Group": "G", "Active": "SI"},
      {"ID": "CLI-3", "Name": "Archivado SA", "Group": "G", "Active": "NO"}]
C.list_clientes = lambda g=None, incluir_inactivos=False: [f for f in _F if incluir_inactivos or f["Active"] != "NO"]
chk("⚠️ `ficha_de` encuentra una ARCHIVADA por su ID (la ficha buscaba solo entre las activas)",
    C.ficha_de("G", "CLI-3").get("Name") == "Archivado SA")
chk("…y por su nombre normalizado (lo que llega de Invoices); lo que no existe, nada",
    C.ficha_de("G", "archivado  sa").get("ID") == "CLI-3" and C.ficha_de("G", "no existe") == {})

# ═══════════════════════════════════════════════════════════════════════════════════════════
G = r'''
import streamlit as st
from core import clientes as C, projects as P, alerts, expenses, invoices as I, incrustar, flash
from core import clientes_ui as CU
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G", "nombre": "Jefa"})
_LL = st.session_state.setdefault("_LL", [])
incrustar.script = lambda h, *a, **k: _LL.append(h)
F = st.session_state.setdefault("_F", [
    {"ID": "CLI-1", "Name": "Meridian", "Group": "G", "Active": "SI", "ContactName": "Sarah",
     "Phone": "02 9000 1001", "Email": "projects@meridian.example", "Address": "1 Martin Place"},
    {"ID": "CLI-2", "Name": "Ryde Retail", "Group": "G", "Active": "SI", "ContactName": "Priya",
     "Phone": "02 9000 1003", "Email": "ops@ryde.example", "Address": ""},
    {"ID": "CLI-3", "Name": "Archivado SA", "Group": "G", "Active": "NO", "ContactName": "",
     "Phone": "", "Email": "", "Address": ""}])
ACT = st.session_state.setdefault("_ACT", [])
_PR = [{"ID": "PRJ-A", "Name": "Alfa", "Status": "Completed", "Progress": "100", "ClientID": "CLI-1", "Client": "Meridian"},
       {"ID": "PRJ-B", "Name": "Beta", "Status": "Cancelled", "Progress": "0", "ClientID": "CLI-1", "Client": "Meridian"},
       {"ID": "PRJ-C", "Name": "Gamma", "Status": "In progress", "Progress": "40", "ClientID": "CLI-2", "Client": "Ryde Retail"},
       {"ID": "PRJ-D", "Name": "Delta", "Status": "Planned", "Progress": "0", "ClientID": "", "Client": "Solo Texto"}]
C.is_configured = lambda: True
C.list_clientes = lambda g=None, incluir_inactivos=False: [dict(f) for f in F if incluir_inactivos or f["Active"] != "NO"]
C.get_cliente = lambda cid: next((dict(f) for f in F if f["ID"] == cid), {})
def _activo(cid, a):
    ACT.append((cid, a))
    for f in F:
        if f["ID"] == cid:
            f["Active"] = "SI" if a else "NO"
    return True, ("Client restored." if a else "Client archived.")
C.set_activo = _activo
def _crear(grupo, nombre, *a, **k):
    if not str(nombre).strip():
        return False, "The client name is required."
    F.append({"ID": "CLI-%d" % (len(F) + 1), "Name": nombre, "Group": "G", "Active": "SI",
              "ContactName": "", "Phone": "", "Email": "", "Address": ""})
    return True, F[-1]["ID"]
C.create_cliente = _crear
P.list_projects = lambda *a, **k: [dict(x) for x in _PR]
P.project_hours_bulk = lambda g: {"PRJ-A": 3.0, "PRJ-C": 12.5}
alerts.is_configured = lambda: True
alerts.open_counts_all = lambda: {"PRJ-C": 2}
expenses.is_configured = lambda: True
expenses.group_expenses = lambda g: {"proyectos": [{"id": "PRJ-A", "total": 80.0}]}
I.is_configured = lambda: False
flash.mostrar()
CU.render_contactos("G")
'''


def _txt(a):
    return " | ".join(str(x.value) for k in ("markdown", "caption", "info", "warning", "error", "success")
                      for x in getattr(a, k, []))


def _ss(a, k, d=None):
    return a.session_state[k] if k in a.session_state else d


def _clic(a, key):
    next(b for b in a.button if b.key == key).click()
    a.run()


def _clientes(a):
    return list(a.dataframe[0].value["Cliente"]) if list(a.dataframe) else []


print("\n2. ⚠️ La ficha: una ARCHIVADA se abre y se RESTAURA; llamar y escribir con un toque")
at = AppTest.from_string(G, default_timeout=120)
at.session_state["_cli_open"] = "CLI-3"
at.run()
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
_t = _txt(at)
chk("⚠️ la ficha ARCHIVADA sale con su nombre y su aviso (salía «no record yet», en minúsculas)",
    "Archivado SA" in _t and "archived" in _t and "has no record yet" not in _t, _t[:300])
chk("…y con «Restore this record» (no había forma de recuperarla)", any(b.key == "cli_rest_CLI-3" for b in at.button))
_clic(at, "cli_rest_CLI-3")
chk("…que la RESTAURA, con su mensaje", ("CLI-3", True) in _ss(at, "_ACT", []) and "Client restored." in _txt(at),
    (_ss(at, "_ACT"), _txt(at)[:200]))
at = AppTest.from_string(G, default_timeout=120)
at.session_state["_cli_open"] = "archivado sa"         # como lo abre Invoices: por el nombre
at.run()
chk("…también si llega por el NOMBRE (Invoices)", any(b.key == "cli_rest_CLI-3" for b in at.button))
at = AppTest.from_string(G, default_timeout=120)
at.session_state["_cli_open"] = "CLI-1"
at.run()
_md = " ".join(str(m.value) for m in at.markdown)
chk("⚠️ el teléfono LLAMA y el email ESCRIBE (eran texto): `tel:0290001001` y `mailto:`",
    'href="tel:0290001001"' in _md and 'href="mailto:projects@meridian.example"' in _md, _md[-300:])
_exp = next((e for e in list(at.expander) + list(getattr(at, "status", [])) if "Archive client" in str(e.label)), None)
_clic(at, "cli_arch_CLI-1")
chk("⚠️ archivar AVISA («Client archived.») y vuelve a la lista",
    ("CLI-1", False) in _ss(at, "_ACT", []) and "Client archived." in _txt(at) and "_cli_open" not in at.session_state,
    (_ss(at, "_ACT"), _txt(at)[:200]))
_ui = ast.parse(fuente("core/clientes_ui.py"))
_forms = [n for n in ast.walk(_ui) if isinstance(n, ast.Call) and ast.unparse(n.func) == "st.form"]
chk("⚠️ los DOS formularios (la ficha y el alta) no se envían con Enter",
    len(_forms) == 2 and all(any(k.arg == "enter_to_submit" and ast.unparse(k.value) == "False" for k in f.keywords)
                             for f in _forms), [ast.unparse(f)[:60] for f in _forms])

print("\n3. La lista: filtros recordados, el archivado se ve, el teléfono sin espacios, todo activo")
_pers = {ast.unparse(k.value) for n in ast.walk(_ui) if isinstance(n, ast.Call) for k in n.keywords
         if k.arg == "key" and any(kk.arg == "persist_state" for kk in n.keywords)}
chk("⚠️ la búsqueda y la casilla de archivados se RECUERDAN (y el filtro, de v575)",
    {"'cli_q'", "'cli_ver_arch'", "'cpxseg_clis_filt'"} <= _pers, sorted(_pers))
at = AppTest.from_string(G, default_timeout=120)
at.run()
chk("sin excepción (lista)", not at.exception, [e.value for e in at.exception][:1])
_df = at.dataframe[0].value
chk("⚠️ las columnas: lo que importa PRIMERO (Client · Active · Projects · Progress) y «Record» al final",
    list(_df.columns)[:4] == ["Cliente", "Active", "Projects", "Avance"] and list(_df.columns)[-1] == "Ficha",
    list(_df.columns))
_cfg = json.loads(at.dataframe[0].proto.columns)
chk("…las horas con su unidad («%.1f h») y «Open alerts» (decía «Alarms»)",
    (_cfg.get("Horas") or {}).get("type_config", {}).get("format") == "%.1f h"
    and (_cfg.get("Alarms") or {}).get("label") == "Open alerts", (_cfg.get("Horas"), _cfg.get("Alarms")))
_av = dict(zip(_df["Cliente"], _df["Avance"]))
chk("⚠️ el avance medio SIN la cancelada (Meridian: 100 % y una cancelada a 0 → 100, no 50)",
    _av.get("Meridian") == 100, _av)
chk("«Yes» en Record (era «yes») y los plurales de verdad («(3 clients)»)",
    "Yes" in list(_df["Ficha"]) and "Tap a client to see its record, summary and projects. (3 clients)" in _txt(at),
    (list(_df["Ficha"]), _txt(at)[:300]))
_vb = next((b for b in at.button if b.key == "cli_ver_arch_btn"), None)
chk("⚠️ «1 archived client hidden — show it» es un BOTÓN (era un texto mudo, con «(s)»)",
    _vb is not None and "1 archived client hidden — show it" in str(_vb.label), getattr(_vb, "label", None))
_vb.click().run()
_df = at.dataframe[0].value
chk("…que los enseña, y el archivado se DISTINGUE («Archived» en Record)",
    at.checkbox(key="cli_ver_arch").value is True
    and dict(zip(_df["Cliente"], _df["Ficha"])).get("Archivado SA") == "Archived", list(_df["Ficha"]))
at.checkbox(key="cli_ver_arch").uncheck().run()
at.text_input(key="cli_q").set_value("0290001003").run()
chk("⚠️ el teléfono SIN espacios encuentra «02 9000 1003» (daba 0)", _clientes(at) == ["Ryde Retail"], _clientes(at))
at.text_input(key="cli_q").set_value("1003").run()
chk("…y con un trozo, como antes", _clientes(at) == ["Ryde Retail"], _clientes(at))
at.text_input(key="cli_q").set_value("nadie se llama así").run()
chk("⚠️ si nada coincide, lo dice y ofrece «Show all»",
    "No client matches the search or the filter." in _txt(at) and any(b.key == "cli_ver_todos" for b in at.button))
_clic(at, "cli_ver_todos")
chk("…que lo devuelve todo (sin búsqueda ni filtro)",
    sorted(_clientes(at)) == ["Meridian", "Ryde Retail", "Solo Texto"] and at.text_input(key="cli_q").value == "",
    _clientes(at))
at.text_input(key="cli_q").set_value("ryde").run()
_n0 = len(_ss(at, "_LL", []))
_clic(at, "cpxkpi_clis_sin")
chk("⚠️ una cifra filtra Y baja a la tabla (la tabla quedaba en el borde, en el móvil fuera)",
    _clientes(at) == ["Solo Texto"] and any(".st-key-cpx_clis_tabla" in s for s in _ss(at, "_LL", [])[_n0:]),
    _clientes(at))
chk("…contando la lista ENTERA: suelta la búsqueda que hubiera («ryde» dejaba la cifra en nada)",
    at.text_input(key="cli_q").value == "", at.text_input(key="cli_q").value)
_con = [n for n in ast.walk(_ui) if isinstance(n, ast.With)
        and any("cpx_clis_tabla" in ast.unparse(i.context_expr) for i in n.items)]
_dentro = " ".join(ast.unparse(n) for n in _con)
chk("…y la tabla está DENTRO del bloque al que se baja (sin él, el script no encuentra destino)",
    len(_con) == 1 and "_tabla_clientes(rows)" in _dentro and "_bajar_a('cpx_clis_tabla'" in _dentro,
    len(_con))
_clic(at, "cpxkpi_clis_tot")
at.session_state["cli_tbl_" + str(_ss(at, "_cli_tbl_gen", 0))] = {
    "selection": {"rows": [], "columns": [], "cells": [(list(at.dataframe[0].value["Cliente"]).index("Ryde Retail"), "Cliente")]}}
at.run()
chk("⚠️ un toque abre la ficha por su ID («CLI-2»; un cliente solo-texto, por su nombre)",
    _ss(at, "_cli_open") == "CLI-2", _ss(at, "_cli_open"))

print("\n4. ⚠️ El alta: sin Enter, por generación (nace vacía), abre la ficha nueva por su ID")
at = AppTest.from_string(G, default_timeout=120)
at.run()
_nom = next(t_ for t_ in at.text_input if str(t_.key).startswith("cli_new_nom_"))
chk("los campos del alta llevan la generación (`cli_new_nom_0`)", _nom.key == "cli_new_nom_0", _nom.key)
_nom.set_value("Nuevo Cliente")
next(b for b in at.button if "Create client" in str(b.label)).click()
at.run()
chk("crea, abre la ficha nueva por su ID y avisa",
    _ss(at, "_cli_open") == "CLI-4" and "Client created." in _txt(at), (_ss(at, "_cli_open"), _txt(at)[:200]))
del at.session_state["_cli_open"]
at.run()
_nom = next(t_ for t_ in at.text_input if str(t_.key).startswith("cli_new_nom_"))
chk("⚠️ y al volver, el alta nace VACÍA (otra generación; se quedaba con lo tecleado)",
    _nom.key == "cli_new_nom_1" and _nom.value == "", (_nom.key, _nom.value))

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
for f in fallos:
    print("  - " + f)
sys.exit(1 if fallos else 0)
