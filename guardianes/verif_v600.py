"""v600 · LO VISTO VERIFICANDO v599 (decisión del usuario: «No dejes nada pendiente»).

Visto en producción (25/10/2026, cliente1, activos de PRUEBA):
  ⚠️ FANTASMAS que se VEN durante una pasada: la regla de v582 los oculta con la pasada parada,
     pero en cuanto arranca otra vuelven a verse atenuados (el «Record check-in» de una ficha
     salía en la LISTA de Inventory, ~2 s por pasada). Medido en una mini-app: CSS solo no lo
     distingue; un marcador que actúa al acabar cada pasada, sí (0 vistos, lo legítimo visible).
  ⚠️ un 2º toque REPITE el movimiento y su costo (los paneles se quedaban con lo tecleado);
  ⚠️ la devolución y la baja escribían «bodega»/«baja» en la hoja (el dato es inglés);
  ⚠️ en un activo de baja el formulario dejaba poner «available» (oculto pero disponible);
  la lista olvidaba sus filtros al abrir una ficha; «Service ov…» cortado; los nombres de
  categoría, las filas de los informes y «N written-off assets hidden» eran texto mudo.
La hoja va SUSTITUIDA en memoria: nada toca la real.
"""
import ast
import datetime as dt
import io
import os
import re
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Admin2", "rol": "administrator", "grupo": "G"}
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


def cadenas(rel):
    """Las cadenas del CÓDIGO (trampa 2: un comentario no cuenta como código)."""
    _a = ast.parse(fuente(rel))
    out = [n.value for n in ast.walk(_a) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    out += ["".join(v.value for v in n.values if isinstance(v, ast.Constant) and isinstance(v.value, str))
            for n in ast.walk(_a) if isinstance(n, ast.JoinedStr)]
    return out


def funcion(rel, nombre):
    return next(n for n in ast.walk(ast.parse(fuente(rel)))
                if isinstance(n, ast.FunctionDef) and n.name == nombre)


# ═══════════════════════════════════════════════════════════════════════════════════════════
print("1. ⚠️ FANTASMAS: ocultos también DURANTE las pasadas (el marcador + su CSS)")
from core import theme as T                                      # noqa: E402
_css = T._CSS
chk("la regla de v582 sigue (pasada parada)",
    '[data-testid="stApp"][data-test-script-state="notRunning"] [data-stale="true"]' in _css)
_r1 = re.search(r'\[data-copex-fantasma\]\[data-stale="true"\]\s*\{\{?\s*display:\s*none\s*!important', _css)
chk("⚠️ lo MARCADO y aún «stale» se oculta SIEMPRE (también con la pasada en marcha)", bool(_r1))
chk("…y un nodo marcado que vuelve a la vida (stale=false) NO se oculta (la regla exige stale=true)",
    not re.search(r'\[data-copex-fantasma\]\s*\{', _css))
chk("…y el bloque marcado se oculta solo si no tiene nada VIVO dentro",
    '[data-testid="stLayoutWrapper"][data-copex-fantasma]:not(:has([data-stale="false"]))' in _css)
_m = T._MARCADOR
_i_cond = _m.find("!=='notRunning')return")
_i_marca = _m.find("setAttribute('data-copex-fantasma'")
chk("⚠️ el marcador SOLO marca con la pasada PARADA (durante una pasada lo viejo es legítimo)",
    0 <= _i_cond < _i_marca, (_i_cond, _i_marca))
chk("…marca solo lo que sigue en «stale» (`[data-stale=\"true\"]`)",
    "querySelectorAll('[data-stale=\"true\"]')" in _m)
chk("…y sube a los bloques MIENTRAS no tengan nada vivo (si no, ocultaría contenido legítimo)",
    "while(w&&!w.querySelector('[data-stale=\"false\"]'))" in _m)
chk("…escucha el estado de la pasada (`data-test-script-state`) y se instala UNA vez",
    "attributeFilter:['data-test-script-state']" in _m and "if(window.__copexFantasmas)return" in _m)
_s = T.script_fantasmas()
chk("se instala en el contexto de la PÁGINA (un <script> en su <head>), con respaldo",
    "D.createElement('script')" in _s and "D.head.appendChild(s)" in _s and "new Function" in _s)
_ap = ast.parse(fuente("app.py"))
_inc = [n for n in _ap.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
        and ast.unparse(n.value.func) == "incrustar.script"]
chk("⚠️ app.py lo trae en el recuadro de la PWA, SIN un recuadro nuevo (cambiaría las posiciones)",
    len(_inc) == 1 and "_cpx_theme.script_fantasmas()" in ast.unparse(_inc[0]), [ast.unparse(n)[:60] for n in _inc])

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("\n2. ⚠️ El motor: nada se repite, el estado de baja solo cambia con baja/reactivación, datos en inglés")
from core import inventory as INV                                # noqa: E402
from core.num import col_letter                                  # noqa: E402
_LET = {col_letter(i): h for h, i in INV._ACOL.items()}
FILAS = []


def _fila(**k):
    r = {h: "" for h in INV.ACTIVOS_HEADERS}
    r.update({"Group": "G", "Active": "SI", "Condition": "good"})
    r.update(k)
    return r


class _WS:
    def get_all_records(self, **k):
        return [dict(r) for r in FILAS]

    def batch_update(self, batch, **k):
        for b in batch:
            _l, _n = re.match(r"([A-Z]+)(\d+)$", b["range"]).groups()
            FILAS[int(_n) - 2][_LET[_l]] = b["values"][0][0]


MOVS = []
INV._ws = lambda title: (_WS(), None)
INV._invalidate = lambda: None
INV.get_activo = lambda aid: next((dict(r) for r in FILAS if r["ID"] == aid), {})
INV.ubic_ref_label = lambda r: str(r)


def _log(grupo, aid, tipo, desde="", hacia="", usuario="", costo="", nota="", fecha="", creado_por=""):
    MOVS.append({"AssetID": aid, "Type": tipo, "From": desde, "To": hacia, "Cost": costo})
    return True, "ok"


INV._log_mov = _log
FILAS[:] = [_fila(ID="A1", Name="Taladro", Status="available", LocationType="warehouse", LocationRef="Store",
                  NextService="2027-01-01"),
            _fila(ID="A2", Name="Viejo", Status="written off", Active="NO", LocationType="warehouse")]
_r = INV.update_activo("A2", {"Status": "available"})
chk("⚠️ un activo de BAJA no pasa a «available» editándolo (quedaba oculto pero disponible)",
    _r[0] is False and FILAS[1]["Status"] == "written off", _r)
_r = INV.update_activo("A1", {"Status": "written off"})
chk("…ni uno activo pasa a «written off» sin la baja (seguía en la lista)", _r[0] is False and FILAS[0]["Status"] == "available", _r)
chk("…y lo demás se sigue editando (la nota de uno de baja)", INV.update_activo("A2", {"Note": "x"})[0] is True)
_n = len(MOVS)
chk("la salida de un disponible, bien", INV.salida("A1", "G", usuario="u1", hacia_tipo="user", hacia_ref="u1")[0] is True)
_r = INV.salida("A1", "G", usuario="u1", hacia_tipo="user", hacia_ref="u1")
chk("⚠️ un 2º toque de salida se RECHAZA (ya está «in use») y no deja otro movimiento",
    _r[0] is False and len(MOVS) == _n + 1, (_r, len(MOVS) - _n))
chk("la devolución, bien", INV.entrada("A1", "G", bodega="Store")[0] is True)
chk("⚠️ y escribe «warehouse: Store» (escribía «bodega: Store»)", MOVS[-1]["To"] == "warehouse: Store", MOVS[-1]["To"])
_n = len(MOVS)
_r = INV.entrada("A1", "G", bodega="Store")
chk("⚠️ un 2º toque de devolución se RECHAZA (ya está disponible)", _r[0] is False and len(MOVS) == _n, _r)
_r = INV.traslado("A1", "G", "warehouse", "Store")
chk("⚠️ trasladar a DONDE YA ESTÁ se rechaza (un 2º toque lo repetía)", _r[0] is False and len(MOVS) == _n, _r)
chk("…a otro sitio, bien", INV.traslado("A1", "G", "warehouse", "Store B")[0] is True)
_n = len(MOVS)
_r = INV.mantenimiento("A1", "G", costo=0, proximo="2027-01-01", nota="")
chk("⚠️ un servicio SIN NADA que anotar (costo 0, la misma fecha, sin nota) se rechaza",
    _r[0] is False and len(MOVS) == _n, _r)
chk("…con costo, bien", INV.mantenimiento("A1", "G", costo=85.5)[0] is True)
_a = {"NextService": "2027-01-01", "Status": "available"}
chk("`servicio_con_datos`: la MISMA fecha no cuenta, una nueva sí; la nota y el costo sí",
    not INV.servicio_con_datos(_a, 0, "2027-01-01", "", False) and INV.servicio_con_datos(_a, 0, "2027-05-01", "", False)
    and INV.servicio_con_datos(_a, 0, "", "cambio de aceite", False) and INV.servicio_con_datos(_a, 10, "", "", False))
chk("…y «a mantenimiento» solo cuenta si no lo está ya",
    INV.servicio_con_datos(_a, 0, "", "", True) and not INV.servicio_con_datos({"Status": "maintenance"}, 0, "", "", True))
chk("la baja, bien", INV.dar_de_baja("A1", "G", "roto")[0] is True)
chk("⚠️ y escribe «written off» como destino (escribía «baja»)", MOVS[-1]["To"] == "written off", MOVS[-1]["To"])
chk("…con Active=NO y el estado de baja, juntos", FILAS[0]["Active"] == "NO" and FILAS[0]["Status"] == "written off")
_n = len(MOVS)
chk("⚠️ un 2º toque de baja se rechaza", INV.dar_de_baja("A1", "G", "roto")[0] is False and len(MOVS) == _n)
chk("reactivar, bien, y su origen «written off» (era «baja»)",
    INV.reactivar("A1", "G")[0] is True and MOVS[-1]["From"] == "written off", MOVS[-1])
chk("⚠️ un 2º toque de reactivar se rechaza", INV.reactivar("A1", "G")[0] is False)
_cs = cadenas("core/inventory.py")
chk("⚠️ el motor ya no ESCRIBE «baja» ni «bodega…» (ninguna cadena del código)",
    "baja" not in _cs and not any(str(c).startswith("bodega") for c in _cs),
    [c for c in _cs if c == "baja" or str(c).startswith("bodega")])

# ═══════════════════════════════════════════════════════════════════════════════════════════
HOY = dt.date.today()
G = r'''
import streamlit as st
import datetime as dt
st.session_state.setdefault("auth", {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "G"})
from core import inventory as INV, inventory_ui as IU, incrustar, flash, auth, clock
from core import projects as P
HOY = clock.today().isoformat()
A = st.session_state.setdefault("_A", [
    {"ID": "ACT-1", "Group": "G", "Name": "Taladro", "Category": "Tool", "Serial": "SN-1",
     "Status": "available", "Active": "SI", "PurchaseValue": "500", "UsefulLifeYears": "5",
     "PurchaseDate": "2026-01-01", "NextService": "2027-01-01", "Condition": "good",
     "LocationType": "warehouse", "LocationRef": "Store", "AssignedTo": "", "ReturnDate": "", "Note": ""},
    {"ID": "ACT-2", "Group": "G", "Name": "Andamio", "Category": "Equipment", "Serial": "SN-2",
     "Status": "in use", "Active": "SI", "PurchaseValue": "1200", "UsefulLifeYears": "0",
     "PurchaseDate": "", "NextService": "2030-01-01", "Condition": "fair",
     "LocationType": "project", "LocationRef": "PRJ-1", "AssignedTo": "helper1", "ReturnDate": "2030-01-10", "Note": ""},
    {"ID": "ACT-3", "Group": "G", "Name": "Escalera rota", "Category": "Tool", "Serial": "SN-3",
     "Status": "written off", "Active": "NO", "PurchaseValue": "100", "UsefulLifeYears": "0",
     "PurchaseDate": "", "NextService": "", "Condition": "poor",
     "LocationType": "warehouse", "LocationRef": "Store", "AssignedTo": "", "ReturnDate": "", "Note": ""}])
MOV = st.session_state.setdefault("_MOV", [])
INV.is_configured = lambda: True
INV.app_url = lambda: "https://app.example"
INV.list_activos = lambda grupo=None, incluir_baja=False: [a for a in A if incluir_baja or a.get("Active", "SI") != "NO"]
INV.get_activo = lambda aid: next((dict(a) for a in A if a["ID"] == aid), {})
def _upd(aid, fields):
    for a in A:
        if a["ID"] == aid:
            a.update({k: str(v) for k, v in fields.items()})
    return True, "Asset updated."
INV.update_activo = _upd
def _log(grupo, aid, tipo, desde="", hacia="", usuario="", costo="", nota="", fecha="", creado_por=""):
    MOV.append({"AssetID": aid, "Type": tipo, "Date": HOY, "FromLocation": desde, "ToLocation": hacia,
                "User": usuario, "Cost": costo, "Note": nota, "Created": "%s %04d" % (HOY, len(MOV))})
    return True, "ok"
INV._log_mov = _log
INV.list_movimientos = lambda grupo=None, activo_id=None: [m for m in MOV if activo_id is None or m["AssetID"] == activo_id]
INV.categorias = lambda grupo: sorted(INV.CAT_DEFAULT, key=str.lower)
INV.categorias_propias = lambda grupo: []
auth.list_users = lambda *a, **k: [{"User": "helper1", "Name": "Helper One"}]
P.list_projects = lambda *a, **k: [{"ID": "PRJ-1", "Name": "Open job", "Status": "In progress"}]
P.etiqueta_proyectos = lambda ps: {p["ID"]: p["Name"] for p in ps}
P.get_project = lambda pid: next((p for p in P.list_projects() if p["ID"] == pid), {})
_LL = st.session_state.setdefault("_LL", [])
incrustar.script = lambda html, *a, **k: _LL.append(html)
_pr = st.session_state.pop("_probar", None)
if _pr == "informe_cat":
    st.session_state["inv_rep_cat_0"] = {"selection": {"rows": [], "columns": [], "cells": [(1, 0)]}}
    IU._tocar_informe("inv_rep_cat_0", ["Equipment", "Tool"], "categoria")
elif _pr == "informe_ubi":
    st.session_state["inv_rep_ubi_0"] = {"selection": {"rows": [], "columns": [], "cells": [(0, 0)]}}
    IU._tocar_informe("inv_rep_ubi_0", ["project", "warehouse"], "ubicacion")
elif _pr == "pill":
    st.session_state["inv_cat_pills_0"] = "Equipment"
    IU._tocar_categoria("inv_cat_pills_0")
flash.mostrar()
IU.render_inventario("G")
'''


def _txt(a):
    return " | ".join(str(x.value) for k in ("markdown", "caption", "info", "warning", "error", "success")
                      for x in getattr(a, k, []))


def _ss(a, k, d=None):
    return a.session_state[k] if k in a.session_state else d


def _de(lista, pref):
    """El widget cuya clave es `pref` + algo (la generación o el tipo que v600 añade)."""
    return next((w for w in lista if str(w.key).startswith(pref)), None)


def _ids(a):
    return sorted(a.dataframe[0].value["ID"]) if list(a.dataframe) else []


print("\n3. ⚠️ La ficha: los paneles nacen con lo de ahora y se VACÍAN tras registrar; el estado fijo")
at = AppTest.from_string(G, default_timeout=300)
at.session_state["_inv_open"] = "ACT-1"
at.run()
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
_tt = _de(at.selectbox, "inv_ttt_ACT-1_0")
_tr = _de(at.text_input, "inv_ttr_ACT-1_warehouse_0")
_tb = _de(at.button, "inv_tbtn_ACT-1_0")
chk("⚠️ el traslado NACE con donde está («warehouse» · «Store») y el botón DESACTIVADO",
    _tt is not None and _tt.value == "warehouse" and _tr is not None and _tr.value == "Store"
    and _tb is not None and _tb.disabled is True,
    (getattr(_tt, "value", None), getattr(_tr, "value", None), getattr(_tb, "disabled", None)))
chk("…y lo dice («The asset is already there.»)", "The asset is already there." in _txt(at))
_mb = _de(at.button, "inv_mbtn_ACT-1_0")
chk("⚠️ «Record service» DESACTIVADO sin nada que anotar", _mb is not None and _mb.disabled is True)
_de(at.number_input, "inv_mcosto_ACT-1_0").set_value(85.5).run()
chk("…con un costo, se activa", _de(at.button, "inv_mbtn_ACT-1_0").disabled is False)
_de(at.button, "inv_mbtn_ACT-1_0").click().run()
_m = [m for m in _ss(at, "_MOV", []) if m["Type"] == "maintenance"]
chk("…registra el servicio", len(_m) == 1 and str(_m[0]["Cost"]) in ("85.5", "85.50"), _m)
_c1 = _de(at.number_input, "inv_mcosto_ACT-1_")
chk("⚠️ y el panel RENACE vacío (otra generación): costo 0 y el botón desactivado otra vez",
    _c1 is not None and str(_c1.key).endswith("_1") and float(_c1.value or 0) == 0
    and _de(at.button, "inv_mbtn_ACT-1_1").disabled is True, (getattr(_c1, "key", None), getattr(_c1, "value", None)))
_de(at.selectbox, "inv_ttt_ACT-1_1").set_value("under repair").run()
_de(at.text_input, "inv_ttr_ACT-1_under repair_1").set_value("Taller").run()
_de(at.button, "inv_tbtn_ACT-1_1").click().run()
_a1 = next(a for a in _ss(at, "_A") if a["ID"] == "ACT-1")
chk("el traslado al taller, registrado", _a1["LocationType"] == "under repair" and _a1["LocationRef"] == "Taller")
_tt2, _tb2 = _de(at.selectbox, "inv_ttt_ACT-1_2"), _de(at.button, "inv_tbtn_ACT-1_2")
chk("⚠️ …y el panel renace con el sitio NUEVO y desactivado (un 2º toque no repite)",
    _tt2 is not None and _tt2.value == "under repair" and _tb2 is not None and _tb2.disabled is True,
    (getattr(_tt2, "value", None), getattr(_tb2, "disabled", None)))
_st = next((s for s in at.selectbox if s.label == "Status"), None)
chk("en un activo disponible, el estado se edita (available · maintenance · damaged)",
    _st is not None and _st.disabled is False)
at.session_state["_inv_open"] = "ACT-2"
at.run()
_st = next((s for s in at.selectbox if s.label == "Status"), None)
chk("⚠️ en uno PRESTADO el estado está FIJO («in use»: sale con la devolución)",
    _st is not None and _st.disabled is True and list(_st.options) == ["in use"], getattr(_st, "options", None))
at.session_state["_inv_open"] = "ACT-3"
at.run()
_st = next((s for s in at.selectbox if s.label == "Status"), None)
chk("⚠️ en uno de BAJA el estado está FIJO («written off»: sale con «Reactivate»)",
    _st is not None and _st.disabled is True and list(_st.options) == ["written off"], getattr(_st, "options", None))

print("\n4. La lista: filtros RECORDADOS, por ubicación, «nada coincide» con salida, todo activo")
_ui = ast.parse(fuente("core/inventory_ui.py"))
_pers = {ast.unparse(k.value) for n in ast.walk(_ui) if isinstance(n, ast.Call)
         for k in n.keywords if k.arg == "key"
         if any(kk.arg == "persist_state" and ast.unparse(kk.value) == "'session'" for kk in n.keywords)}
chk("⚠️ los cinco filtros llevan `persist_state` (al volver de una ficha se perdían)",
    {"'inv_ver_baja'", "'inv_q'", "'inv_catf'", "'inv_estf'", "'inv_ubicf'"} <= _pers, sorted(_pers))
_fr = funcion("core/inventory_ui.py", "render_inventario")
_cols = [ast.unparse(n) for n in ast.walk(_fr) if isinstance(n, ast.Call) and ast.unparse(n.func) == "st.columns"]
chk("los filtros en TRES columnas bajo la búsqueda (en [2, 1, 1] «Service ov…» salía cortado)",
    "st.columns(3)" in _cols and "st.columns([2, 1, 1])" not in _cols, _cols)
at = AppTest.from_string(G, default_timeout=300)
at.run()
chk("sin excepción (lista)", not at.exception, [e.value for e in at.exception][:1])
at.text_input(key="inv_q").set_value("Andamio").run()
chk("la búsqueda filtra («Andamio» → ACT-2)", _ids(at) == ["ACT-2"], _ids(at))
at.session_state["_inv_open"] = "ACT-2"
at.run()
del at.session_state["_inv_open"]
at.run()
chk("⚠️ al VOLVER de la ficha, la búsqueda sigue («Andamio», ACT-2)",
    at.text_input(key="inv_q").value == "Andamio" and _ids(at) == ["ACT-2"], (at.text_input(key="inv_q").value, _ids(at)))
at.text_input(key="inv_q").set_value("almacén que no existe").run()
chk("⚠️ si nada coincide, lo dice y ofrece salida", "Nothing matches these filters." in _txt(at)
    and any("Show all" in str(b.label) for b in at.button))
next(b for b in at.button if "Show all" in str(b.label)).click().run()
chk("…«Show all» lo devuelve todo (sin búsqueda)", _ids(at) == ["ACT-1", "ACT-2"] and at.text_input(key="inv_q").value == "",
    _ids(at))
at.selectbox(key="inv_ubicf").set_value("project").run()
chk("por UBICACIÓN: «project» → solo el que está en la obra (ACT-2)", _ids(at) == ["ACT-2"], _ids(at))
at.selectbox(key="inv_ubicf").set_value("Todas").run()
at.text_input(key="inv_q").set_value("Store").run()
chk("la búsqueda también mira la UBICACIÓN («Store» → ACT-1)", _ids(at) == ["ACT-1"], _ids(at))
at.text_input(key="inv_q").set_value("").run()
_vb = next((b for b in at.button if str(b.key) == "inv_ver_bajas_btn"), None)
chk("⚠️ «1 written-off asset hidden — show it» es un BOTÓN (era un texto mudo)",
    _vb is not None and "1 written-off asset hidden" in str(_vb.label), getattr(_vb, "label", None))
_vb.click().run()
chk("…y las enseña (ACT-3 en la tabla, la casilla marcada)",
    "ACT-3" in _ids(at) and at.checkbox(key="inv_ver_baja").value is True, _ids(at))
at.checkbox(key="inv_ver_baja").uncheck().run()
at.session_state["_probar"] = "informe_cat"
at.run()
chk("⚠️ una fila de «By category» lleva a la lista con ESA categoría (Tool → ACT-1)",
    _ss(at, "inv_catf") == "Tool" and _ids(at) == ["ACT-1"], (_ss(at, "inv_catf"), _ids(at)))
chk("…baja a la tabla, y la tabla del informe nace sin selección (otra generación)",
    any(".st-key-cpx_inv_tabla" in s for s in _ss(at, "_LL", [])) and _ss(at, "_inv_rep_sel_gen") == 1)
at.session_state["_probar"] = "informe_ubi"
at.run()
chk("…una de «By location», con ESA ubicación (project → ACT-2) y sin la categoría de antes",
    _ss(at, "inv_ubicf") == "project" and _ss(at, "inv_catf") == "Todas" and _ids(at) == ["ACT-2"],
    (_ss(at, "inv_ubicf"), _ss(at, "inv_catf"), _ids(at)))
at.session_state["_probar"] = "pill"
at.run()
chk("⚠️ un NOMBRE de categoría lleva a la lista filtrada (Equipment → ACT-2)",
    _ss(at, "inv_catf") == "Equipment" and _ids(at) == ["ACT-2"], (_ss(at, "inv_catf"), _ids(at)))
_rep = funcion("core/inventory_ui.py", "_reportes")
_dfs = [n for n in ast.walk(_rep) if isinstance(n, ast.Call) and ast.unparse(n.func) == "st.dataframe"]
chk("las DOS tablas de los informes responden al toque (`on_select` → `_tocar_informe`)",
    len(_dfs) == 2 and all(any(k.arg == "on_select" and "_tocar_informe" in ast.unparse(k.value) for k in d.keywords)
                           for d in _dfs))
_cx = funcion("core/inventory_ui.py", "_categorias_expander")
chk("…y los nombres de categoría (`st.pills` → `_tocar_categoria`)",
    any(isinstance(n, ast.Call) and ast.unparse(n.func) == "st.pills"
        and any(k.arg == "on_change" and ast.unparse(k.value) == "_tocar_categoria" for k in n.keywords)
        for n in ast.walk(_cx)))

print("\n5. ⚠️ La migración de «bodega»/«baja» (guardianes/sueltos)")
_mig = io.open(os.path.join(RAIZ, "..", "guardianes", "sueltos", "migrar_v600_movimientos.py"),
               encoding="utf-8").read()
_fn = next(n for n in ast.parse(_mig).body if isinstance(n, ast.FunctionDef) and n.name == "nuevo")
_ns = {}
exec(compile(ast.Module(body=[_fn], type_ignores=[]), "mig", "exec"), _ns)
_nuevo = _ns["nuevo"]
chk("«bodega: Store» → «warehouse: Store»; «bodega» → «warehouse»; «baja» → «written off»",
    _nuevo("bodega: Store") == "warehouse: Store" and _nuevo("bodega") == "warehouse"
    and _nuevo("baja") == "written off" and _nuevo("Bodega: X") == "warehouse: X")
chk("…y NO toca lo que no es eso (el canónico, ni una obra que se llame «Baja Tower»)",
    _nuevo("warehouse: Store") is None and _nuevo("project: Baja Tower") is None and _nuevo("") is None)
chk("…por defecto solo ENSEÑA (escribe con `--aplicar`) y guarda copia FUERA del repo",
    'APLICAR = "--aplicar" in sys.argv' in _mig and "if APLICAR and cambios:" in _mig and r'D:\CopeX\respaldos' in _mig)

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
for f in fallos:
    print("  - " + f)
sys.exit(1 if fallos else 0)
