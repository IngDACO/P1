"""v667 · Ciclo 1 → mejoras 5/5: MÓVIL Y PANTALLAS (y H44, visto verificando v664).

  H28 una sola definición de obra activa (la tarjeta y la lista de Home decían 11 y 10);
  H1  la ficha de una persona dice su usuario; H22 la línea base en DD/MM/YYYY y por nombre;
  H11 «Save changes» dice que guardó y a quién avisó (se perdía con el rerun);
  H41 el buscador encuentra activos, facturas y cotizaciones;
  H13/H18 fichar y mandar un activo: sin obras cerradas, con el ID y «location» a la vista;
  H10 la dirección que se ESCRIBIÓ se guarda (Google pone el punto); H44 la obra desde una cotización
      sale en el mapa; H17/H42 Inventario con códigos en mayúscula, años sin decimales y la balda al devolver;
  H3  una fecha sin icono en la etiqueta; H19 «Restoring your session…» en vez del formulario;
  H36 en el móvil se pliega el menú al cambiar de sección.
Todo con las hojas SUSTITUIDAS en memoria: nada sale ni se escribe.
"""
import ast
import io
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


def funcion(rel, nombre):
    s = fuente(rel)
    for n in ast.walk(ast.parse(s)):
        if isinstance(n, ast.FunctionDef) and n.name == nombre:
            return ast.get_source_segment(s, n) or ""
    return ""


ADMIN = '{"usuario": "jefa", "rol": "administrator", "grupo": "G", "nombre": "Jefa"}'

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("1. H28 · Una sola definición de obra activa")
from core import projects as P, projects_ui as PU, roster as R, alerts  # noqa: E402
_PRJS = [{"ID": f"PRJ-{i}", "Status": s, "Progress": "0"} for i, s in
         enumerate(["Planned", "In progress", "On hold", "Completed", "Cancelled"], start=1)]
chk("activa = «Planned» o «In progress» (una en pausa no)",
    [P.es_activa(p) for p in _PRJS] == [True, True, False, False, False]
    and tuple(P.ESTADOS_ACTIVOS) == ("Planned", "In progress"))
_o = (P.list_projects, P.project_hours_bulk, alerts.is_configured, P.delays_of_group)
try:
    P.list_projects = lambda *a, **k: [dict(p) for p in _PRJS]
    P.project_hours_bulk = lambda g: {}
    alerts.is_configured = lambda: False
    P.delays_of_group = lambda g: {}
    _k = PU._kpis("G")
finally:
    P.list_projects, P.project_hours_bulk, alerts.is_configured, P.delays_of_group = _o
chk("⚠️ la tarjeta «Active» cuenta lo mismo que la lista (2, no 3 con la de en pausa)", _k["activos"] == 2, _k)
_ph = funcion("core/home_ui.py", "_proyectos_home")
chk("…la lista de Home usa la misma definición y su pie va por t()",
    "if P.es_activa(p)]" in _ph and 't("{n} active · sorted by urgency", n=len(proys))' in _ph)
chk("…y el tablero cuenta como en marcha lo mismo", set(R.ACTIVAS_PLAN) == set(P.ESTADOS_ACTIVOS))

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("2. H1 · H22 · H11 · la ficha de una persona, la línea base y «Save changes»")
_fu = funcion("core/auth_ui.py", "_ficha_usuario")
chk("H1 · la cabecera lleva el USUARIO (como código) cuando no es el nombre",
    '_login = f"  `{sel}`" if _nom_f.strip() != str(sel).strip()' in _fu and 'st.markdown(f"**{_nom_f}**{_login}' in _fu)
_dp = funcion("core/projects_ui.py", "_detalle_proyecto")
_es = funcion("core/projects_ui.py", "_estado_section")
chk("H22 · «Baseline: … set on DD/MM/YYYY by <nombre>»",
    'c=_fmt_fecha(str(_o.get("fijada", ""))[:10]),' in _dp and 'q=_nombres_de([_o.get("por", "?")], grupo)[0]))' in _dp)
chk("…y el pie «baseline set on» y el historial de replanificaciones, igual",
    'pie=t("baseline set on {f}", f=_fmt_fecha(_cmp["fijada"][:10])))' in _es
    and 'f=_fecha_hora(_h.get("fijada", "")), q=_nombres_de([_h.get("por", "?")], grupo)[0],' in _es)
chk("H11 · «Save changes» lo dice por flash (con a quién avisó) y el tablero también; sin el toast que se perdía",
    'flash.exito(t("Changes saved.") + (" " + t(":material/send: {n} field user(s) notified: {l}.",' in _dp
    and "_autoagenda(grupo, pid, nuevos, _quitados, f_ini, f_fin, al_flash=True)" in _dp
    and 'st.toast(t("Changes saved.")' not in _dp and "_avisados.append(un)" in _dp)

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("3. H41 · El buscador")
from core import home_ui as H, auth as AUTH, inventory as INV, invoices as IV, quotes as QT, library as LIB  # noqa: E402
_o = (P.list_projects, AUTH.list_users, R.list_trabajos, LIB.list_items, INV.list_activos, IV.list_facturas, QT.list_cotizaciones)
try:
    P.list_projects = lambda *a, **k: []
    AUTH.list_users = lambda *a, **k: []
    R.list_trabajos = lambda *a, **k: []
    LIB.list_items = lambda *a, **k: []
    INV.list_activos = lambda g=None, incluir_baja=False: [{"ID": "ACT-0005", "Name": "Hoist 500kg", "Serial": "SN-77",
                                                           "Category": "Equipment", "Status": "available"}]
    IV.list_facturas = lambda g=None, **k: [{"ID": "FAC-1", "Number": "0001", "ClientName": "C1 — Harbour", "Date": "2026-11-09"}]
    QT.list_cotizaciones = lambda g=None, **k: [{"ID": "COT-6", "Number": "0006", "ClientName": "C1 — Harbour",
                                                 "Status": "accepted", "Version": "2"}]
    st.session_state["auth"] = {"usuario": "jefa", "rol": "administrator", "grupo": "G"}
    _r1 = H.buscar("ACT-0005", "G")
    _r2 = H.buscar("sn-77", "G")
    _r3 = H.buscar("0001", "G")
    _r4 = H.buscar("0006", "G")
    st.session_state["auth"] = {"usuario": "f1", "rol": "field", "grupo": "G"}
    _r5 = H.buscar("ACT-0005", "G")
finally:
    (P.list_projects, AUTH.list_users, R.list_trabajos, LIB.list_items, INV.list_activos, IV.list_facturas,
     QT.list_cotizaciones) = _o
    st.session_state["auth"] = {"usuario": "jefa", "rol": "administrator", "grupo": "G"}
chk("⚠️ «ACT-0005» encuentra el activo (y por su nº de serie)",
    [(r["tipo"], r["id"], r["orden"]) for r in _r1] == [("activo", "ACT-0005", 0)] and _r2 and _r2[0]["id"] == "ACT-0005", (_r1, _r2))
chk("…«0001» la factura (con su fecha DD/MM/YYYY) y «0006» la cotización, con su número y versión",
    [r["tipo"] for r in _r3] == ["factura"] and _r3[0]["titulo"] == "Invoice No. 0001" and "09/11/2026" in _r3[0]["pie"]
    and [r["tipo"] for r in _r4] == ["cotizacion"] and _r4[0]["titulo"] == "Quote No. 0006 v2", (_r3, _r4))
chk("…y nada de eso para el campo (no tiene Inventory ni Finance)", _r5 == [], _r5)
G3 = r'''
import streamlit as st
from core import home_ui as H
st.session_state.setdefault("auth", ''' + ADMIN + r''')
if st.session_state.pop("_GO", None):
    H._abrir_resultado(st.session_state["_RES"])
'''
_abre = {}
for _res, _k, _nav in (({"tipo": "activo", "id": "ACT-0005"}, "_inv_open", ("inventario", None)),
                       ({"tipo": "factura", "id": "FAC-1"}, "_fac_open", ("finanzas", "🧾 Facturas")),
                       ({"tipo": "cotizacion", "id": "COT-6"}, "_cot_open", ("finanzas", "📄 Cotizaciones"))):
    at = AppTest.from_string(G3, default_timeout=60)
    at.session_state["_GO"], at.session_state["_RES"] = True, _res
    at.run()
    _abre[_res["tipo"]] = (not at.exception, at.session_state[_k] if _k in at.session_state else None,
                           tuple(at.session_state["_admin_nav_pending"]) if "_admin_nav_pending" in at.session_state else None)
chk("…y cada resultado ABRE su ficha (activo, factura, cotización)",
    _abre == {"activo": (True, "ACT-0005", ("inventario", None)), "factura": (True, "FAC-1", ("finanzas", "🧾 Facturas")),
              "cotizacion": (True, "COT-6", ("finanzas", "📄 Cotizaciones"))}, _abre)

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("4. H13/H18 · Dónde se ficha y a dónde va un activo")
_PS2 = [{"ID": "PRJ-1", "Name": "Bondi", "Status": "In progress", "Type": "Installation"},
        {"ID": "PRJ-2", "Name": "Done", "Status": "Completed", "Type": "Installation"},
        {"ID": "PRJ-3", "Name": "Gone", "Status": "Cancelled", "Type": "Installation"},
        {"ID": "PRJ-4", "Name": "Alexandria Warehouse", "Status": "Open", "Type": list(P.TIPOS_INTERNOS)[0]},
        {"ID": "PRJ-5", "Name": "Old store", "Status": "Closed", "Type": list(P.TIPOS_INTERNOS)[0]},
        {"ID": "PRJ-6", "Name": "Paused", "Status": "On hold", "Type": "Installation"}]
_et = P.etiqueta_con_id(_PS2[:1] + _PS2[3:4])
chk("etiqueta_con_id: el ID siempre, y «location» si es una localización",
    _et == {"PRJ-1": "Bondi (PRJ-1)", "PRJ-4": "Alexandria Warehouse (PRJ-4 · location)"}, _et)
from core import timeclock_ui as TU                               # noqa: E402
_o = (TU.projects_data.list_projects, TU._asignadas_hoy)
try:
    TU.projects_data.list_projects = lambda *a, **k: [dict(p) for p in _PS2]
    TU._asignadas_hoy = lambda u, g: []
    _pp, _ = TU._proyectos_para("administrator", "jefa", "G")
finally:
    TU.projects_data.list_projects, TU._asignadas_hoy = _o
chk("⚠️ al fichar: ni completadas, ni canceladas, ni localizaciones cerradas (sí la abierta y la de en pausa)",
    [p["ID"] for p in _pp] == ["PRJ-1", "PRJ-4", "PRJ-6"], [p["ID"] for p in _pp])
_tu = fuente("core/timeclock_ui.py")
chk("…la barra lateral y la pantalla de Fichaje lo enseñan con etiqueta_con_id",
    _tu.count("idmap = {_lbl: _pid for _pid, _lbl in _P.etiqueta_con_id(proys).items()}") == 2
    and "etiqueta_proyectos(proys)" not in _tu)
from core import inventory_ui as IUI                               # noqa: E402
_o = P.list_projects
try:
    P.list_projects = lambda *a, **k: [dict(p) for p in _PS2]
    _ids, _lb = IUI._proyectos("G")
finally:
    P.list_projects = _o
chk("…y el destino de un activo, igual (con su almacén marcado «location»)",
    _ids == ["PRJ-1", "PRJ-4", "PRJ-6"] and _lb.get("PRJ-4") == "Alexandria Warehouse (PRJ-4 · location)", (_ids, _lb))

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("5. H10 · La dirección que se escribió · H44 · la obra desde una cotización, en el mapa")
G5 = r'''
import streamlit as st
from core import location_ui as LU
LU.geocode_candidates = lambda q, limit=6: [{"lat": -33.8607, "lon": 151.2148, "exacto": True,
    "label": "Bennelong Apartments, 1, Macquarie Street, Quay Quarter, Sydney, New South Wales, 2000, Australia"}]
LU.geocoder_activo = lambda: "google"
LU.location_picker("loc", None, None, "")
st.session_state["_ADDR"] = st.session_state.get("loc_addr")
'''
at = AppTest.from_string(G5, default_timeout=60).run()
at.text_input(key="loc_q").set_value("1 Macquarie St, Sydney NSW 2000")
at.button(key="loc_btn").click().run()
at.run()
_a1 = at.session_state["_ADDR"] if "_ADDR" in at.session_state else None
chk("⚠️ tras «Search» se guarda lo ESCRITO, no la versión de Google", not at.exception and _a1 == "1 Macquarie St, Sydney NSW 2000",
    (_a1, [e.value for e in at.exception][:1]))
chk("…y el punto sí es el de Google", at.session_state["loc_lat"] == -33.8607 and at.session_state["loc_lng"] == 151.2148)
_cb = [c for c in at.checkbox if c.key == "loc_usar_g"]
chk("…con una casilla para guardar la de Google si se quiere", bool(_cb) and "Bennelong Apartments" in str(_cb[0].label))
if _cb:
    _cb[0].check().run()
    at.run()
chk("…y marcada, se guarda la de Google", (at.session_state["_ADDR"] if "_ADDR" in at.session_state else "").startswith("Bennelong"))

from core import quotes_ui as QU, location_ui as LU, flash        # noqa: E402
_cap = []
_o = (LU.geocode, P.update_project, flash.aviso)
try:
    LU.geocode = lambda d: (-33.86, 151.21) if d else None
    P.update_project = lambda pid, f: (_cap.append((pid, f)), (True, ""))[1]
    _av = []
    flash.aviso = lambda m: _av.append(m)
    QU._ubicar_obra("PRJ-0042", "1 Macquarie St, Sydney NSW 2000")
    QU._ubicar_obra("PRJ-0043", "")
    LU.geocode = lambda d: None
    QU._ubicar_obra("PRJ-0044", "nowhere at all")
finally:
    LU.geocode, P.update_project, flash.aviso = _o
chk("⚠️ H44 · la obra nueva recibe su punto (Lat/Lng), sin tocar el texto",
    _cap == [("PRJ-0042", {"Lat": -33.86, "Lng": 151.21})], _cap)
chk("…sin dirección no hace nada; si no la encuentra, lo dice", len(_av) == 1 and "could not be placed" in _av[0], _av)
chk("…y se llama al crear la obra desde la cotización",
    "_ubicar_obra(str(msg), ubic)" in funcion("core/quotes_ui.py", "_crear_proyecto"))

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("6. H17/H42 · Inventario")
chk("⚠️ los códigos con mayúscula; lo que escribió una persona, tal cual",
    [IUI._etq(x) for x in ("good", "available", "in use", "warehouse", "check-out", "zz my category", "Equipment")]
    == ["Good", "Available", "In use", "Warehouse", "Check-out", "zz my category", "Equipment"],
    [IUI._etq(x) for x in ("good", "available", "in use", "warehouse", "check-out", "zz my category", "Equipment")])
chk("…también en la ubicación («Warehouse: Main store»)",
    INV.ubic_str({"LocationType": "warehouse", "LocationRef": "Main store"}, IUI._etq) == "Warehouse: Main store")
_iu = fuente("core/inventory_ui.py")
chk("…y la vida útil sin decimales («%g»), en el alta y en la edición",
    _iu.count('t("Useful life (years)"), min_value=0.0, step=1.0, format="%g"') == 2)
_o = INV.list_movimientos
try:
    INV.list_movimientos = lambda g=None, activo_id=None: [
        {"ID": "MOV-1", "Date": "2026-10-01", "FromLocation": "warehouse: Main store · Shelf B2", "ToLocation": "project: PRJ-1"},
        {"ID": "MOV-2", "Date": "2026-10-20", "FromLocation": "project: PRJ-1", "ToLocation": "warehouse: Store"},
        {"ID": "MOV-3", "Date": "2026-11-02", "FromLocation": "warehouse: Store · Shelf C1", "ToLocation": "project: PRJ-2"},
        {"ID": "MOV-4", "Date": "2026-11-05", "FromLocation": "project: PRJ-2", "ToLocation": "project: PRJ-3"}]
    _b1 = INV.ultima_bodega("G", "ACT-5")
    INV.list_movimientos = lambda g=None, activo_id=None: []
    _b3 = INV.ultima_bodega("G", "ACT-5")
finally:
    INV.list_movimientos = _o
chk("⚠️ H42 · al devolver, el sitio de donde SALIÓ la última vez (su balda)", _b1 == "Store · Shelf C1", _b1)
chk("…y sin historial, nada (la caja propone «Store»)", _b3 == "", _b3)
chk("…y la caja de la devolución nace con él", 'value=INV.ultima_bodega(grupo, aid) or t("Store"),' in _iu)

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("7. H3 · Una fecha sin icono en la etiqueta")
G7 = r'''
import streamlit as st
from core import ui_common as ui
ui.fecha_opcional(":material/event_available: Start date at the company", None, "f1")
'''
at = AppTest.from_string(G7, default_timeout=60).run()
chk("⚠️ fecha_opcional quita el icono de la etiqueta", not at.exception and at.date_input(key="f1").label == "Start date at the company",
    at.date_input(key="f1").label if not at.exception else at.exception)
chk("…y la ficha ya no se lo pasa", 'ui.fecha_opcional(t("Start date at the company"),' in fuente("core/auth_ui.py"))

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("8. H19 · «Restoring your session…»")
G8 = r'''
import streamlit as st
from core import auth_ui as AU, auth, session_cookie
session_cookie.load = lambda: (None, None)
auth.is_configured = lambda: True
auth.has_any_user = lambda: True
st.session_state["_R"] = AU.render_login()
'''


def _g8(**estado):
    a = AppTest.from_string(G8, default_timeout=60)
    for k, v in estado.items():
        a.session_state[k] = v
    return a.run()


at = _g8()
_inf = [str(i.value) for i in at.info]
chk("⚠️ sin respuesta aún del componente de cookies: «Restoring your session…» y NO el formulario",
    not at.exception and any("Restoring your session" in x for x in _inf) and not [x for x in at.text_input if x.key == "login_u"]
    and not [x for x in at.text_input if "Username" in str(x.label)], (_inf, [x.label for x in at.text_input]))
at.button(key="ck_ver_login").click().run()
chk("…el botón «Sign in with your password instead» enseña el formulario",
    any("Username" in str(x.label) or "User" in str(x.label) for x in at.text_input), [x.label for x in at.text_input])
at = _g8(copex_cookie_get={})
chk("…cuando el componente ya contestó (sin cookie), el formulario directo",
    not any("Restoring your session" in str(i.value) for i in at.info) and len(at.text_input) >= 1)
at = _g8(_no_cookie_restore=True)
chk("…y tras cerrar sesión a propósito, también directo",
    not any("Restoring your session" in str(i.value) for i in at.info) and len(at.text_input) >= 1)
at = AppTest.from_string(G8, default_timeout=60).run()
at.run()
at.run()
chk("…y si el componente no contesta, a la 3ª pasada sale el formulario igual",
    not any("Restoring your session" in str(i.value) for i in at.info) and len(at.text_input) >= 1)

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("9. H36 · El menú en el móvil")
_sv = funcion("core/home_ui.py", "subir_si_cambia_la_vista")
_pm = funcion("core/home_ui.py", "_plegar_menu_movil")
chk("al cambiar de SECCIÓN (no al abrir una ficha) se pliega el menú",
    "if ant[0] != v[0]:\n            _plegar_menu_movil()" in _sv)
chk("…solo con pantalla estrecha, si está abierto, y con SU botón",
    "if(W.innerWidth>=768)return;" in _pm and "if(r.width<=50||r.right<=1)return;" in _pm
    and "[data-testid=\\\"stSidebarCollapseButton\\\"] button" in _pm and "b.click()" in _pm)

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
for f in fallos:
    print("  - " + f)
sys.exit(1 if fallos else 0)
