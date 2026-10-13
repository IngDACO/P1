# -*- coding: utf-8 -*-
"""v564 · LOCATIONS, PROBADA ACCIÓN POR ACCIÓN (decisión del usuario: «dale con todo»).

  1. ⚠️ Expenses de una localización enseñaba beneficio, beneficio fijo, «Invoice» y
     reclamaciones de obra (su propia pantalla dice «never invoiced») → fuera.
  2. ⚠️ Archivada ≠ cerrada: salía «closed» y seguía en la lista (la ayuda prometía que
     desaparecía) → fuera de la lista, «Show archived (n)» la trae, y se rotula «archived».
  3. Personas por su NOMBRE (selectores y «Permanently assigned»), no por login.
  4. Sin «Select all» en los selectores de personas (barrido de la app).
  5. Data: dirección y pin editables (antes solo al crear).
  6. Team: cabeceras «Hours»/«Cost» (salía la clave en español) y nombres en el aviso.
  7. Pre-Start: fechas DD/MM/YYYY, «attendee(s)», y «Do today's Pre-Start here» que lleva
     al Pre-Start con la localización YA elegida.
  8. Sin ninguna: ni 4 tarjetas a 0 ni el alta plegada.   9. KPI ACTIVOS (3) y recuento en
     la cabecera.  10. Una sola tarjeta a todo el ancho; horas con decimal.  11. «Person in
     charge».  12. `&l=` y el menú vuelve a la lista; la sección se recuerda.  13. El alta
     se VACÍA (generación de claves).  14. Textos con `t()` (también en Expenses).

AppTest y el motor con sus dependencias sustituidas: ninguna hoja se toca.
"""
import ast
import io
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


def _desplegables(at):
    """⚠️ AppTest clasifica un `st.expander` CON icono como `Status` (trampa 40)."""
    return list(at.expander) + list(at.status)


def _textos(at):
    """Todo el texto pintado (markdown, captions, avisos y botones)."""
    _t = []
    for coll in (at.markdown, at.caption, at.info, at.warning, at.success, at.error):
        _t += [str(x.value) for x in coll]
    _t += [str(b.label) for b in at.button]
    return " ¦ ".join(_t)


# ⚠️ En el proto, `select_all=False` es 0 (por defecto 1000 = umbral; True = -1): medido
# con un caso conocido de cada (la sonda `is False` daba rojo con el código bien).
def _html(at):
    try:
        return " ".join(str(getattr(e.proto, "body", "")) for e in at.get("html"))
    except Exception:
        return ""


from streamlit.testing.v1 import AppTest                                    # noqa: E402

CAB = r'''
import streamlit as st
from core import projects_ui as PU, projects as P, auth, alerts, location_ui
from core import expenses as E, prestart
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G",
                                     "nombre": "Jefa"})
_US = [{"User": "campo1", "Name": "Ana Campo", "Role": "field", "Group": "G"},
       {"User": "campo2", "Name": "Beto Campo", "Role": "field", "Group": "G"},
       {"User": "jefa", "Name": "Jefa Admin", "Role": "administrator", "Group": "G"}]
auth.list_users = lambda grupo=None, *a, **k: [dict(u) for u in _US]
_L = {"L1": {"ID": "L1", "Name": "Office A", "Type": "Office", "Status": "Open", "ManualStatus": "",
             "Group": "G", "FieldAssigned": "campo1;campo2", "HeadInstallers": "jefa",
             "Location": "1 George St", "Lat": "-33.8", "Lng": "151.2"},
      "L2": {"ID": "L2", "Name": "Store B", "Type": "Warehouse", "Status": "Closed",
             "ManualStatus": "Closed", "Group": "G", "FieldAssigned": "", "HeadInstallers": "",
             "Location": "", "Lat": "", "Lng": ""},
      "L3": {"ID": "L3", "Name": "Old shop", "Type": "Workshop", "Status": "Archived",
             "ManualStatus": "Archived", "Group": "G", "FieldAssigned": "", "HeadInstallers": "",
             "Location": "", "Lat": "", "Lng": ""}}
st.session_state.setdefault("_IDS", ["L1", "L2", "L3"])
PU._loc_datos = lambda g: ([dict(_L[i]) for i in st.session_state["_IDS"]],
                           {"L1": 0.4, "L2": 1.2}, {"L1": {"total": 100.0}}, {})
P.get_project = lambda pid: dict(_L[pid]) if pid in _L else None
st.session_state.setdefault("_LLAMADAS", [])
def _pick(key, lat=None, lng=None, direccion=""):
    st.session_state["_LLAMADAS"].append(("pick", key))
    return lat, lng
location_ui.location_picker = _pick
PU._avisar_asignados = lambda *a, **k: None
PU._notificar_asignados = lambda *a, **k: st.session_state["_LLAMADAS"].append(("notif", a[0]))
PU._alerts_section = lambda *a, **k: None
E.is_configured = lambda: False          # nada lee la hoja real (los casos que lo usan lo sustituyen)
'''

# ══════════════════════════════════════════════════════════════════════════════
print("1. La lista")
G_LISTA = CAB + r'''
PU.render_localizaciones("G")
'''
at = AppTest.from_string(G_LISTA, default_timeout=90)
at.run()
chk("la lista se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_keys = {b.key for b in at.button}
chk("⚠️ la ARCHIVADA no sale en la lista (la abierta y la cerrada sí)",
    "locopen_L1" in _keys and "locopen_L2" in _keys and "locopen_L3" not in _keys, sorted(_keys))
_tg = [x for x in at.toggle if x.key == "loc_ver_arch"]
chk("⚠️ «Show archived (1)» para traerla", len(_tg) == 1 and "Show archived (1)" in _tg[0].label,
    [x.label for x in at.toggle])
_tx = _textos(at)
chk("⚠️ el recuento va en la cabecera («Locations — 2 · 1 open · 1 closed»)",
    "**Locations — 2** · 1 open · 1 closed" in _tx, re.findall(r"Locations[^¦]{0,60}", _tx))
_kb = {b.key: b.label for b in at.button if str(b.key).startswith("cpxkpi_loc_")}
chk("⚠️ 3 tarjetas KPI ACTIVAS (botones con clave)",
    sorted(_kb) == ["cpxkpi_loc_gasto", "cpxkpi_loc_gente", "cpxkpi_loc_horas"], sorted(_kb))
chk("…sin la de «Locations 0 · of 1»", "Locations\n" not in " ".join(_kb.values()))
chk("⚠️ horas con un decimal bajo 10 h («1.6 h», no «2»)", "1.6 h" in _kb.get("cpxkpi_loc_horas", ""),
    _kb.get("cpxkpi_loc_horas"))
chk("«People 2» (las asignadas de forma permanente)", "\n\n2\n\n" in _kb.get("cpxkpi_loc_gente", ""),
    _kb.get("cpxkpi_loc_gente"))
chk("la tarjeta: «0.4 h» trabajadas (antes «0 h»)", "**0.4 h**" in _tx)
chk("la cerrada se rotula «closed»", "closed" in _tx)
chk("la regla de una por fila si no caben dos (`@container`)",
    "@container (max-width:620px){.st-key-cpx_loc_cartas" in _html(at), _html(at)[:200])

[b for b in at.button if b.key == "cpxkpi_loc_gente"][0].click()
at.run()
_tx = _textos(at)
chk("⚠️ tocar «People» enseña QUIÉN, por su nombre («Ana Campo, Beto Campo»)",
    "Office A: Ana Campo, Beto Campo" in _tx and "campo1" not in _tx, re.findall(r"Office A:[^¦]*", _tx))
[b for b in at.button if b.key == "cpxkpi_loc_gente"][0].click()
at.run()
chk("…y otra vez lo cierra", "Office A: Ana Campo" not in _textos(at))

at.toggle(key="loc_ver_arch").set_value(True)
at.run()
_keys = {b.key for b in at.button}
chk("⚠️ con «Show archived», vuelve la archivada", "locopen_L3" in _keys, sorted(_keys))
chk("…rotulada «archived» (no «closed»)", "archived" in _textos(at))

print("\n2. Una sola, y ninguna")
at = AppTest.from_string(G_LISTA, default_timeout=90)
at.session_state["_IDS"] = ["L1"]
at.run()
chk("con UNA, una tarjeta por fila: `st.columns(1)` (antes ocupaba media)",
    "_por_fila = 1 if len(_ord) == 1 else 2" in io.open(os.path.join(RAIZ, "core", "projects_ui.py"),
                                                          encoding="utf-8").read())
chk("…y se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])

at = AppTest.from_string(G_LISTA, default_timeout=90)
at.session_state["_IDS"] = []
at.run()
chk("sin ninguna se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("⚠️ sin ninguna, NI una tarjeta KPI a 0", not [b for b in at.button if str(b.key).startswith("cpxkpi_loc")])
chk("…un aviso que dice qué hacer", "No locations yet" in _textos(at))
chk("⚠️ …y «New location» ABIERTO",
    [e.proto.expanded for e in _desplegables(at) if "New location" in e.proto.label] == [True],
    [(e.proto.label, e.proto.expanded) for e in _desplegables(at)])
at = AppTest.from_string(G_LISTA, default_timeout=90)
at.session_state["_IDS"] = ["L3"]
at.run()
chk("con solo una ARCHIVADA, lo mismo (y el toggle para verla)",
    [e.proto.expanded for e in _desplegables(at) if "New location" in e.proto.label] == [True]
    and [x.key for x in at.toggle] == ["loc_ver_arch"])
at = AppTest.from_string(G_LISTA, default_timeout=90)
at.run()
chk("con localizaciones, «New location» empieza PLEGADO",
    [e.proto.expanded for e in _desplegables(at) if "New location" in e.proto.label] == [False])

print("\n3. El alta")
G_ALTA = CAB + r'''
def _crea(g, nom, **k):
    st.session_state["_LLAMADAS"].append(("crea", nom, k.get("campo_asignados"), k.get("ingeniero")))
    return True, "L9"
P.create_project = _crea
_L["L9"] = dict(_L["L1"], ID="L9", Name="Nueva oficina")
st.session_state["_IDS"] = []
# v570 · los avisos ANTES de la sección, como la shell (ver verif_v569/v570)
from core import flash
flash.mostrar()
PU.render_localizaciones("G")
'''
at = AppTest.from_string(G_ALTA, default_timeout=90)
at.run()
chk("el alta se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_ms = {m.key: m for m in at.multiselect}
_asg, _rsp = _ms.get("nloc_asg"), _ms.get("nloc_resp")
chk("⚠️ «Who normally works here» por NOMBRE", _asg is not None and list(_asg.options) == ["Ana Campo", "Beto Campo"],
    list(_asg.options) if _asg else None)
chk("⚠️ …y sin «Select all»", _asg is not None and _asg.proto.select_all == 0)
chk("«Person in charge» por nombre y sin «Select all»",
    _rsp is not None and "Jefa Admin" in list(_rsp.options) and _rsp.proto.select_all == 0)
_asg.set_value(["campo1"])
at.run()
at.text_input(key="nloc_nom").set_value("Nueva oficina")
[b for b in at.button if "Create location" in str(b.label)][0].click()
at.run()
_cr = [x for x in at.session_state["_LLAMADAS"] if x[0] == "crea"]
chk("se crea con el asignado por LOGIN (el nombre es solo lo que se ve)",
    _cr == [("crea", "Nueva oficina", ["campo1"], "")], _cr)
chk("⚠️ tras crear, otra generación de claves (el alta nace VACÍA)",
    at.session_state["_loc_new_gen"] == 1 and at.session_state["_loc_open"] == "L9")
chk("el aviso lo dice («Location created: L9 · Nueva oficina»)",
    any("Location created: L9 · Nueva oficina" in s.value for s in at.success), [s.value for s in at.success])
del at.session_state["_loc_open"]
at.run()
chk("⚠️ el alta vuelve VACÍA (nombre y asignados)",
    at.text_input(key="nloc_nom_1").value == "" and list(at.multiselect(key="nloc_asg_1").value) == [])
chk("…y el buscador de dirección con su clave nueva (`nlocloc_1`)",
    ("pick", "nlocloc_1") in at.session_state["_LLAMADAS"])

# ══════════════════════════════════════════════════════════════════════════════
print("\n4. El detalle: cabecera, Team y la sección recordada")
G_DET = CAB + r'''
E.is_configured = lambda: True
E.labor_breakdown = lambda pid, g: {"items": [{"usuario": "campo1", "horas": 0.45, "tarifa": 40.0,
                                               "costo": 18.0}], "horas": 0.45, "total": 18.0,
                                    "sin_tarifa": ["campo2"]}
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    st.session_state["_loc_open"] = st.session_state.get("_ABRE", "L1")
PU.render_localizaciones("G")
'''
at = AppTest.from_string(G_DET, default_timeout=90)
at.run()
chk("el detalle se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_tx = _textos(at)
chk("⚠️ «Person in charge: Jefa Admin» (antes «resp. …»)", "Person in charge: Jefa Admin" in _tx
    and "resp." not in _tx, re.findall(r"`L1`[^¦]*", _tx))
chk("⚠️ «Permanently assigned» por nombre", "· Ana Campo" in _tx and "· Beto Campo" in _tx
    and "· campo1" not in _tx)
_df = at.dataframe[0] if at.dataframe else None
_cfg = _df.proto.columns.replace(" ", "") if _df is not None else ""
chk("⚠️ Team: cabeceras «Hours» y «Cost» (salía «Horas»/«Costo»)",
    '"Horas":{"label":"Hours"' in _cfg and '"Costo":{"label":"Cost"' in _cfg, _cfg[:300])
chk("…y la tarifa y el coste con $", _cfg.count("$%,.2f") == 2, _cfg[:300])
chk("⚠️ el aviso «sin tarifa» por NOMBRE (no el login)",
    any("Beto Campo" in w.value and "campo2" not in w.value for w in at.warning), [w.value for w in at.warning])
chk("el total con decimal («0.5 h»)", "**0.5 h**" in _tx, re.findall(r"\*\*[0-9.]+ h\*\*", _tx))
PUS = io.open(os.path.join(RAIZ, "core", "projects_ui.py"), encoding="utf-8").read()
_t = ast.parse(PUS)
_det = next(n for n in ast.walk(_t) if isinstance(n, ast.FunctionDef) and n.name == "_detalle_localizacion")
_sc = [n for n in ast.walk(_det) if isinstance(n, ast.Call) and ast.unparse(n.func).endswith("segmented_control")]
chk("⚠️ la sección se RECUERDA (`persist_state='session'`)",
    len(_sc) == 1 and any(k.arg == "persist_state" and ast.unparse(k.value) == "'session'"
                          for k in _sc[0].keywords))

at = AppTest.from_string(G_DET, default_timeout=90)
at.session_state["_ABRE"] = "L3"
at.run()
chk("una archivada se rotula «archived» en su cabecera", "archived" in _textos(at)
    and ":material/lock: closed" not in _textos(at))

print("\n5. Pre-Start: activo y con la localización ya elegida")
G_PS = G_DET.replace('PU.render_localizaciones("G")', r'''
st.session_state.setdefault("cpxseg_loc_sec", "🦺 Pre-Start")
prestart.is_configured = lambda: True
prestart.leer = lambda r: r
prestart.list_prestarts = lambda pid: [{"fecha": "2026-10-12", "hora": "07:05", "facilitador": "Jefa",
                                        "asistentes": ["a", "b"], "n_no": 0, "near_miss": False}]
PU.render_localizaciones("G")
''')
at = AppTest.from_string(G_PS, default_timeout=90)
at.run()
chk("Pre-Start se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_tx = _textos(at)
chk("⚠️ fecha DD/MM/YYYY y «2 attendee(s)»", "**12/10/2026**" in _tx and "2 attendee(s)" in _tx,
    re.findall(r"🟢[^¦]*", _tx))
_bps = [b for b in at.button if b.key == "loc_ir_ps_L1"]
chk("⚠️ «Do today's Pre-Start here» es un botón", len(_bps) == 1)
if _bps:
    _bps[0].click()
    at.run()
    chk("⚠️ …que lleva al Pre-Start con ESTA localización pedida",
        at.session_state["_admin_nav_pending"] == ("herramientas", "🦺 Pre-Start")
        and at.session_state["_ps_proy_pending"] == "L1")

G_PSTAB = r'''
import streamlit as st
from core import prestart_ui as PSU, projects as P, timeclock
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G",
                                     "nombre": "Jefa"})
PSU.PS.is_configured = lambda: True
P.list_projects = lambda *a, **k: [{"ID": "PRJ-1", "Name": "Lift A", "Group": "G"},
                                   {"ID": "L1", "Name": "Office A", "Group": "G"}]
timeclock.open_sessions = lambda *a, **k: {timeclock.TIPO_PROYECTO: {"proyecto_id": "PRJ-1"}}
PSU.PS.pendiente_de_firma = lambda *a, **k: {"id": "x"}
PSU._bloque_firmar = lambda *a, **k: st.stop()
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    if st.session_state.get("_PEND"):
        st.session_state["_ps_proy_pending"] = st.session_state["_PEND"]
PSU.render_prestart_tab()
'''
at = AppTest.from_string(G_PSTAB, default_timeout=90)
at.session_state["_PEND"] = "L1"
at.run()
chk("el Pre-Start se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("⚠️ llega con «Office A (L1)» elegida (gana al fichaje abierto en PRJ-1)",
    at.selectbox(key="ps_proy").value == "Office A (L1)", at.selectbox(key="ps_proy").value)
chk("…y el pedido se consume (no vuelve a pisar la elección)", "_ps_proy_pending" not in at.session_state)
at = AppTest.from_string(G_PSTAB, default_timeout=90)
at.run()
chk("sin pedido, sigue mandando el fichaje («Lift A (PRJ-1)»)",
    at.selectbox(key="ps_proy").value == "Lift A (PRJ-1)", at.selectbox(key="ps_proy").value)

print("\n6. Data: nombres, sin «Select all», y la dirección y el pin editables")
G_DATA = G_DET.replace('PU.render_localizaciones("G")', r'''
st.session_state.setdefault("cpxseg_loc_sec", "✏️ Datos")
def _upd(pid, campos):
    st.session_state["_LLAMADAS"].append(("upd", pid, dict(campos)))
    return True, ""
P.update_project = _upd
if st.session_state.get("_ADDR") and "_INI2" not in st.session_state:
    st.session_state["_INI2"] = 1
    st.session_state["elocloc_L1_addr"] = st.session_state["_ADDR"]
PU.render_localizaciones("G")
''')
at = AppTest.from_string(G_DATA, default_timeout=90)
at.session_state["_ADDR"] = "2 New St, Sydney"
at.run()
chk("Data se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_ms = {m.key: m for m in at.multiselect}
_ea, _er = _ms.get("eloc_asg_L1"), _ms.get("eloc_resp_L1")
chk("⚠️ «Who normally works here» por NOMBRE y sin «Select all»",
    _ea is not None and list(_ea.options) == ["Ana Campo", "Beto Campo"] and _ea.proto.select_all == 0,
    list(_ea.options) if _ea else None)
chk("«Person in charge» por nombre y sin «Select all»",
    _er is not None and "Jefa Admin" in list(_er.options) and _er.proto.select_all == 0)
chk("⚠️ el buscador de dirección está en Data (clave `elocloc_L1`)", ("pick", "elocloc_L1") in at.session_state["_LLAMADAS"])
chk("con pin puesto, su desplegable empieza PLEGADO",
    [e.proto.expanded for e in _desplegables(at) if "Where it is" in e.proto.label] == [False],
    [(e.proto.label, e.proto.expanded) for e in _desplegables(at)])
_est = at.selectbox(key="eloc_est_L1")
chk("la ayuda del estado dice lo que pasa («Show archived» la trae)", "Show archived" in (_est.help or ""), _est.help)
[b for b in at.button if str(b.label).endswith("Save")][0].click()
at.run()
_up = [x for x in at.session_state["_LLAMADAS"] if x[0] == "upd"]
chk("se guarda", len(_up) == 1, _up)
if _up:
    _c = _up[0][2]
    chk("⚠️ con la dirección CONFIRMADA y el pin («2 New St, Sydney», -33.8, 151.2)",
        _c.get("Location") == "2 New St, Sydney" and _c.get("Lat") == -33.8 and _c.get("Lng") == 151.2, _c)
    chk("los asignados siguen por LOGIN", _c.get("FieldAssigned") == "campo1;campo2", _c.get("FieldAssigned"))
at = AppTest.from_string(G_DATA, default_timeout=90)
at.session_state["_ABRE"] = "L2"
at.run()
chk("sin pin, el desplegable de la dirección empieza ABIERTO",
    [e.proto.expanded for e in _desplegables(at) if "Where it is" in e.proto.label] == [True])
[b for b in at.button if str(b.label).endswith("Save")][0].click()
at.run()
_up = [x for x in at.session_state["_LLAMADAS"] if x[0] == "upd"]
chk("sin tocar la dirección, guardar NO la inventa (vacía sigue vacía)",
    _up and _up[0][2].get("Location") == "" and _up[0][2].get("Lat") == "", _up)

print("\n7. Expenses de una localización: sin beneficio, sin facturar, sin reclamaciones")
G_CST = r'''
import streamlit as st
from core import projects_ui as PU, projects as P, expenses as E
import core.claims_ui as CLU
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G"})
_PR = {"L1": {"ID": "L1", "Name": "Office A", "Type": "Office", "Group": "G"},
       "PRJ-1": {"ID": "PRJ-1", "Name": "Lift A", "Type": "Installation", "Group": "G"}}
P.get_project = lambda pid: dict(_PR[pid])
E.cost_projection = lambda pid, g: {"presupuesto": 0, "proyectado": 0, "total": 50.0, "compras": 50.0,
                                    "mano_obra": 0.0, "comprometido": 0, "pct": 0, "avance": 0,
                                    "por_punto": 0, "over": False, "over_comp": False, "total_comp": 0}
E.labor_breakdown = lambda pid, g: {"items": [], "sin_tarifa": [], "horas": 0, "total": 0}
E.spend_curve = lambda pid, g: []
st.session_state.setdefault("_LL", [])
PU._ganancia_section = lambda *a, **k: st.session_state["_LL"].append("ganancia")
PU._facturar_atajo = lambda *a, **k: st.session_state["_LL"].append("facturar")
PU._ordenes_section = lambda *a, **k: st.session_state["_LL"].append("ordenes")
CLU.render = lambda *a, **k: st.session_state["_LL"].append("claims")
PU._costos_section(st.session_state.get("_PID", "L1"), "G",
                   {"items": [], "por_categoria": {}, "total": 50.0}, True, "loc")
'''
at = AppTest.from_string(G_CST, default_timeout=90)
at.run()
chk("Expenses de una localización sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("⚠️ ni beneficio, ni «Invoice», ni reclamaciones; las órdenes SÍ",
    at.session_state["_LL"] == ["ordenes"], at.session_state["_LL"])
at = AppTest.from_string(G_CST, default_timeout=90)
at.session_state["_PID"] = "PRJ-1"
at.run()
chk("(control) en una OBRA siguen las cuatro", at.session_state["_LL"] == ["ganancia", "facturar", "ordenes", "claims"],
    at.session_state["_LL"])
chk("el titular de una obra sin presupuesto sale (por `t()`)", any("has no budget set" in i.value for i in at.info))

print("\n8. La URL y el menú")
G_URL = r'''
import streamlit as st
from core import home_ui
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G"})
st.session_state["adm_proy_sub"] = st.session_state.get("_SUB", "🏢 Localizaciones")
st.session_state["_loc_open"] = "L1"
st.session_state["_admin_open_agr"] = "AGR-9"
home_ui._estado_a_url("proyectos")
'''
at = AppTest.from_string(G_URL, default_timeout=60)
at.run()
_q = {k: (v[0] if isinstance(v, list) else v) for k, v in dict(at.query_params).items()}
chk("⚠️ con una localización abierta, la URL lleva l=L1", _q.get("l") == "L1", _q)
chk("…y no el `&g=` de otra sub-pestaña", "g" not in _q, _q)
at = AppTest.from_string(G_URL, default_timeout=60)
at.session_state["_SUB"] = "🗂 Agrupaciones"
at.run()
_q = {k: (v[0] if isinstance(v, list) else v) for k, v in dict(at.query_params).items()}
chk("en Groupings, `&g=` y sin `&l=`", _q.get("g") == "AGR-9" and "l" not in _q, _q)
G_URL2 = r'''
import streamlit as st
from core import home_ui
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G"})
home_ui._url_a_estado()
'''
at = AppTest.from_string(G_URL2, default_timeout=60)
at.query_params["s"] = "proyectos"
at.query_params["t"] = "localizaciones"
at.query_params["l"] = "L1"
at.run()
chk("⚠️ un enlace con `&l=` abre esa localización",
    at.session_state["_loc_open"] == "L1" if "_loc_open" in at.session_state else False)
G_MENU = r'''
import streamlit as st
from core import home_ui
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G"})
_lbl = dict(home_ui._secciones())["proyectos"]
st.session_state.setdefault("admin_nav", _lbl)
st.session_state.setdefault("_admin_expanded", "proyectos")
st.session_state.setdefault("adm_proy_sub", "🏢 Localizaciones")
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    st.session_state["_loc_open"] = "L1"
    st.session_state["_admin_open_agr"] = "AGR-9"
st.session_state.setdefault("_url_leida", True)
with st.sidebar:
    home_ui.sidebar_menu()
'''
at = AppTest.from_string(G_MENU, default_timeout=60)
at.run()
_sub = [b for b in at.button if b.key == "navsub_proyectos_2"]
chk("se localiza «Locations» en el menú", len(_sub) == 1 and "Locations" in _sub[0].label if _sub else False)
if _sub:
    _sub[0].click()
    at.run()
    chk("⚠️ tocar «Locations» estando en Locations vuelve a la LISTA", "_loc_open" not in at.session_state)
    chk("…y no toca la agrupación abierta en Groupings", "_admin_open_agr" in at.session_state)

print("\n9. «Select all» en los selectores de PERSONAS (barrido de la app)")
import glob                                                                 # noqa: E402
_PERSONAS = ("np_asg_", "np_ing_", "asig_", "nloc_asg", "nloc_resp", "eloc_asg_", "eloc_resp_",
             "ai_pick", "pva_")
_vistos, _malos = set(), []
for f in sorted(glob.glob(os.path.join(RAIZ, "core", "*.py"))):
    for n in ast.walk(ast.parse(io.open(f, encoding="utf-8").read())):
        if isinstance(n, ast.Call) and ast.unparse(n.func).endswith("multiselect"):
            kw = {k.arg: ast.unparse(k.value) for k in n.keywords}
            _k = kw.get("key", "").strip("f'\"")
            _p = next((p for p in _PERSONAS if _k.startswith(p)), None)
            if _p:
                _vistos.add(_p)
                if kw.get("select_all") != "False":
                    _malos.append("%s:%d %s" % (os.path.basename(f), n.lineno, _k))
            # la cabecera del data head installers no lleva key: se reconoce por su línea
            if not _k and "_cmp_ed" in ast.unparse(n) and kw.get("select_all") != "False":
                _malos.append("%s:%d (head installers)" % (os.path.basename(f), n.lineno))
chk("se encuentran TODOS los selectores de personas (la sonda ve lo que busca)",
    _vistos == set(_PERSONAS), sorted(set(_PERSONAS) - _vistos))
chk("⚠️ ninguno ofrece «Select all» (asignaría y avisaría a todo el campo)", not _malos, _malos)

print("\n10. Textos con `t()`")
_lit = []
for fn in ("_cartera_localizaciones", "_nueva_localizacion_form", "_loc_equipo", "_loc_prestarts",
           "_detalle_localizacion", "_editar_localizacion", "_loc_kpis", "render_localizaciones",
           "_loc_estado_lbl", "render_expenses", "_costos_section"):
    _f = next(n for n in ast.walk(_t) if isinstance(n, ast.FunctionDef) and n.name == fn)
    for n in ast.walk(_f):
        if (isinstance(n, ast.Call) and not ast.unparse(n.func).startswith("logger")
                and ast.unparse(n.func).split(".")[-1] in (
                "caption", "warning", "info", "error", "success", "markdown", "expander", "button",
                "exito", "aviso", "toggle", "selectbox", "multiselect")):
            for a in n.args[:1]:
                _s = ast.unparse(a)
                if (isinstance(a, ast.Constant) and isinstance(a.value, str)
                        and re.search(r"[A-Za-z]{4}", re.sub(r":material/\w+:", "", a.value))
                        and not a.value.lstrip().startswith("<")):
                    _lit.append("%s:%d %s" % (fn, n.lineno, _s[:60]))
                elif isinstance(a, ast.JoinedStr):
                    # una f-string vale solo si sus trozos de TEXTO no son frases (datos + t())
                    _txt = "".join(v.value for v in a.values if isinstance(v, ast.Constant))
                    if re.search(r"[A-Za-z]{4,}\s+[A-Za-z]{2,}", _txt):
                        _lit.append("%s:%d %s" % (fn, n.lineno, _s[:60]))
        # los titulares que van por una VARIABLE (trampa 30)
        if isinstance(n, ast.Assign) and isinstance(n.value, (ast.JoinedStr, ast.Constant)):
            _v = n.value
            _txt = (_v.value if isinstance(_v, ast.Constant) and isinstance(_v.value, str) else
                    "".join(x.value for x in getattr(_v, "values", []) if isinstance(x, ast.Constant)))
            if re.search(r"[A-Za-z]{4,} [a-z]{2,} [a-z]{2,}", str(_txt)) and not str(_txt).lstrip().startswith("<"):
                _lit.append("%s:%d = %s" % (fn, n.lineno, str(_txt)[:60]))
chk("⚠️ Locations y Expenses sin frases sueltas (ni por variable)", not _lit, _lit)
# ⚠️ Por las CONSTANTES del AST: `ast.unparse` escribe las cadenas con comillas SIMPLES y
# buscar '"Interno"' en su salida no veía nada (escapó en la 1ª vuelta de romper_v564).
_cte = {n.value for fn in ("_cartera_localizaciones", "_detalle_localizacion")
        for n in ast.walk(next(f for f in ast.walk(_t) if isinstance(f, ast.FunctionDef) and f.name == fn))
        if isinstance(n, ast.Constant) and isinstance(n.value, str)}
chk("(la sonda ve las constantes: «Internal» está)", "Internal" in _cte)
chk("«Internal» (no «Interno») como tipo por defecto", "Interno" not in _cte)

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("TODO OK")
