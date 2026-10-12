# -*- coding: utf-8 -*-
"""v565 · LO VISTO VERIFICANDO v564 EN PRODUCCIÓN (decisión del usuario: «Dale»).

  1. ⚠️ Una localización ARCHIVADA: «Do today's Pre-Start here» llevaba al Pre-Start SIN ella
     (el Pre-Start no lista archivadas) → en una archivada se dice por qué y dónde se reabre;
     y el Pre-Start avisa si la pedida no está (con el nombre solo si es de esta empresa).
  2. Pies de las tarjetas KPI que CABEN («assigned here», «not charged to jobs»; medidos).
  3. Con «Show archived», la cabecera las cuenta («· 1 archived»).
  4. Cero horas es «0 h» (no «0.0 h»).
  5. Una recién creada se abre en Team (no en la sección recordada de la anterior).

AppTest con sus dependencias sustituidas: ninguna hoja se toca.
"""
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


def _textos(at):
    _t = []
    for coll in (at.markdown, at.caption, at.info, at.warning, at.success, at.error):
        _t += [str(x.value) for x in coll]
    _t += [str(b.label) for b in at.button]
    return " ¦ ".join(_t)


from streamlit.testing.v1 import AppTest                                    # noqa: E402

CAB = r'''
import streamlit as st
from core import projects_ui as PU, projects as P, auth, location_ui, prestart
from core import expenses as E
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G",
                                     "nombre": "Jefa"})
_US = [{"User": "campo1", "Name": "Ana Campo", "Role": "field", "Group": "G"},
       {"User": "jefa", "Name": "Jefa Admin", "Role": "administrator", "Group": "G"}]
auth.list_users = lambda grupo=None, *a, **k: [dict(u) for u in _US]
_L = {"L1": {"ID": "L1", "Name": "Office A", "Type": "Office", "Status": "Open", "ManualStatus": "",
             "Group": "G", "FieldAssigned": "campo1", "HeadInstallers": "", "Location": "", "Lat": "", "Lng": ""},
      "L3": {"ID": "L3", "Name": "Old shop", "Type": "Workshop", "Status": "Archived",
             "ManualStatus": "Archived", "Group": "G", "FieldAssigned": "", "HeadInstallers": "",
             "Location": "", "Lat": "", "Lng": ""}}
st.session_state.setdefault("_IDS", ["L1", "L3"])
st.session_state.setdefault("_H", {"L1": 0.0})
PU._loc_datos = lambda g: ([dict(_L[i]) for i in st.session_state["_IDS"]],
                           st.session_state["_H"], {}, {})
P.get_project = lambda pid: dict(_L[pid]) if pid in _L else None
st.session_state.setdefault("_LLAMADAS", [])
location_ui.location_picker = lambda key, lat=None, lng=None, direccion="": (lat, lng)
PU._avisar_asignados = lambda *a, **k: None
PU._notificar_asignados = lambda *a, **k: None
PU._alerts_section = lambda *a, **k: None
E.is_configured = lambda: False
prestart.is_configured = lambda: True
prestart.list_prestarts = lambda pid: []
'''

# ══════════════════════════════════════════════════════════════════════════════
print("1. ⚠️ Archivada: sin botón que no cumple, y el Pre-Start avisa")
G_PS = CAB + r'''
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    st.session_state["_loc_open"] = st.session_state.get("_ABRE", "L3")
st.session_state.setdefault("cpxseg_loc_sec", "🦺 Pre-Start")
PU.render_localizaciones("G")
'''
at = AppTest.from_string(G_PS, default_timeout=90)
at.run()
chk("la ficha archivada se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("⚠️ archivada: NO ofrece «Do today's Pre-Start here» (llevaba a una página sin ella)",
    not [b for b in at.button if b.key == "loc_ir_ps_L3"], [b.key for b in at.button])
chk("…y dice por qué y dónde se arregla («Reopen it in Data»)",
    any("Archived: it does not appear in the Pre-Start" in c.value and "Reopen it in Data" in c.value
        for c in at.caption), [c.value for c in at.caption])
at = AppTest.from_string(G_PS, default_timeout=90)
at.session_state["_ABRE"] = "L1"
at.run()
chk("(control) abierta: el botón sigue", [b.key for b in at.button if b.key == "loc_ir_ps_L1"] == ["loc_ir_ps_L1"])
chk("…y sin el aviso de archivada", not any("Archived:" in c.value for c in at.caption))

G_PSTAB = r'''
import streamlit as st
from core import prestart_ui as PSU, projects as P, timeclock
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G",
                                     "nombre": "Jefa"})
PSU.PS.is_configured = lambda: True
P.list_projects = lambda *a, **k: [{"ID": "PRJ-1", "Name": "Lift A", "Group": "G"}]
_OTROS = {"L3": {"ID": "L3", "Name": "Old shop", "Group": "G"},
          "X9": {"ID": "X9", "Name": "Oficina de OTRA empresa", "Group": "OTRA"}}
P.get_project = lambda pid: dict(_OTROS[pid]) if pid in _OTROS else None
timeclock.open_sessions = lambda *a, **k: {}
PSU.PS.pendiente_de_firma = lambda *a, **k: {"id": "x"}
PSU._bloque_firmar = lambda *a, **k: st.stop()
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    st.session_state["_ps_proy_pending"] = st.session_state.get("_PEND", "L3")
PSU.render_prestart_tab()
'''
at = AppTest.from_string(G_PSTAB, default_timeout=90)
at.run()
chk("el Pre-Start se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_inf = [i.value for i in at.info]
chk("⚠️ si la pedida no está en la lista, LO DICE («Old shop» is not available…)",
    any("«Old shop» is not available for a pre-start" in v for v in _inf), _inf)
chk("…y el pedido se consume", "_ps_proy_pending" not in at.session_state)
at = AppTest.from_string(G_PSTAB, default_timeout=90)
at.session_state["_PEND"] = "X9"
at.run()
_inf = [i.value for i in at.info]
chk("⚠️ de OTRA empresa: el aviso NO enseña su nombre (cerrojo v351), solo el ID",
    any("«X9» is not available" in v for v in _inf) and not any("OTRA" in v for v in _inf), _inf)

# ══════════════════════════════════════════════════════════════════════════════
print("\n2-4. La lista: pies que caben, archivadas contadas, «0 h»")
G_LISTA = CAB + r'''
PU.render_localizaciones("G")
'''
at = AppTest.from_string(G_LISTA, default_timeout=90)
at.run()
chk("la lista se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_kb = {b.key: b.label for b in at.button if str(b.key).startswith("cpxkpi_loc_")}
chk("⚠️ «assigned here» (el largo se recortaba: 136 px en 115)",
    _kb.get("cpxkpi_loc_gente", "").endswith("assigned here"), _kb.get("cpxkpi_loc_gente"))
chk("«not charged to jobs» (113 px en 113: al borde)",
    _kb.get("cpxkpi_loc_horas", "").endswith("not charged to jobs"), _kb.get("cpxkpi_loc_horas"))
chk("⚠️ cero horas es «0 h» (no «0.0 h»)", "\n\n0 h\n\n" in _kb.get("cpxkpi_loc_horas", "")
    and "0.0 h" not in _textos(at), _kb.get("cpxkpi_loc_horas"))
chk("sin «Show archived», la cabecera no las nombra", "archived" not in
    " ".join(m.value for m in at.markdown if "Locations —" in m.value))
at.toggle(key="loc_ver_arch").set_value(True)
at.run()
_cab = [m.value for m in at.markdown if "Locations —" in m.value]
chk("⚠️ con «Show archived», la cabecera las cuenta («· 1 archived»)",
    _cab == ["**Locations — 1** · 1 open · 1 archived"], _cab)
at = AppTest.from_string(G_LISTA, default_timeout=90)
at.session_state["_IDS"] = ["L3"]
at.run()
at.toggle(key="loc_ver_arch").set_value(True)
at.run()
_cab = [m.value for m in at.markdown if "Locations —" in m.value]
chk("⚠️ solo archivadas a la vista: «0 · 0 open · 1 archived» (antes «0 · 0 open» enseñando una)",
    _cab == ["**Locations — 0** · 0 open · 1 archived"], _cab)
at = AppTest.from_string(G_LISTA, default_timeout=90)
at.session_state["_H"] = {"L1": 0.45}
at.run()
chk("(control) 0,45 h sigue con su decimal", "\n\n0.5 h\n\n" in
    {b.key: b.label for b in at.button}.get("cpxkpi_loc_horas", ""))

# ══════════════════════════════════════════════════════════════════════════════
print("\n5. ⚠️ Una recién creada se abre en Team")
G_ALTA = CAB + r'''
def _crea(g, nom, **k):
    return True, "L9"
P.create_project = _crea
_L["L9"] = dict(_L["L1"], ID="L9", Name="Nueva")
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    st.session_state["cpxseg_loc_sec"] = "🦺 Pre-Start"       # lo recordado de la anterior
PU.render_localizaciones("G")
'''
at = AppTest.from_string(G_ALTA, default_timeout=90)
at.run()
at.text_input(key="nloc_nom").set_value("Nueva")
[b for b in at.button if "Create location" in str(b.label)][0].click()
at.run()
chk("se crea y se abre", not at.exception and at.session_state["_loc_open"] == "L9",
    [e.value for e in at.exception][:1])
chk("⚠️ …en Team (no en el Pre-Start que se recordaba)",
    at.session_state["cpxseg_loc_sec"] == "👥 Equipo", at.session_state["cpxseg_loc_sec"])
chk("…y lo PINTA en Team («Who has worked here»)", "Who has worked here" in _textos(at))

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("TODO OK")
