"""v599 · INVENTORY, PROBADA EN PRODUCCIÓN (decisión del usuario: «Dale con todo»).

Visto en producción (25/10/2026, cliente1, activos de PRUEBA ACT-0001…0003):
  ⚠️ editar DESHACÍA el último mantenimiento (las fechas del formulario con clave fija);
  ⚠️ la baja PISABA la nota; ⚠️ Enter enviaba el alta a medias y dos envíos crearon dos activos
  iguales en 1 s; ⚠️ la edición dejaba poner «written off» (el activo seguía en la lista) y
  guardaba sin nombre; obras cerradas como destino y texto libre por obra/persona; «under
  repair» seguía «available»; «Leave the asset IN service» decía lo contrario; sin mensajes de
  alta/baja/reactivación ni confirmación de baja; la campana llevaba a la lista; sin forma de
  cambiar la foto; categorías (ofrecía las de fábrica, «tool» junto a «Tool», no se vaciaba);
  devolución pasada aceptada; cifras pasivas que se partían; tabla sin ID; informes cortados y
  sin traducir; fechas en ISO; valores y textos sin traducir; «Etiqueta_….pdf»; en el móvil las
  acciones bajo el QR; el responsable por usuario.
La hoja va SUSTITUIDA en memoria: nada toca la real.
"""
import ast
import datetime as dt
import io
import os
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
    """Las cadenas del CÓDIGO (trampa 2: un comentario mío no cuenta como código)."""
    _a = ast.parse(fuente(rel))
    out = [n.value for n in ast.walk(_a) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    out += ["".join(v.value for v in n.values if isinstance(v, ast.Constant) and isinstance(v.value, str))
            for n in ast.walk(_a) if isinstance(n, ast.JoinedStr)]
    return out


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
     "PurchaseDate": "2026-01-01", "NextService": "2026-10-01", "Condition": "good",
     "LocationType": "warehouse", "LocationRef": "Store", "AssignedTo": "", "ReturnDate": "",
     "Note": "nota original"},
    {"ID": "ACT-2", "Group": "G", "Name": "Andamio", "Category": "Equipment", "Serial": "SN-2",
     "Status": "in use", "Active": "SI", "PurchaseValue": "1200", "UsefulLifeYears": "0",
     "PurchaseDate": "", "NextService": "2030-01-01", "Condition": "fair",
     "LocationType": "project", "LocationRef": "PRJ-1", "AssignedTo": "helper1",
     "ReturnDate": "2030-01-10", "Note": ""}])
MOV = st.session_state.setdefault("_MOV", [])
UPD = st.session_state.setdefault("_UPD", [])
NUEVOS = st.session_state.setdefault("_NUEVOS", [])
INV.is_configured = lambda: True
INV.app_url = lambda: "https://app.example"
INV.list_activos = lambda grupo=None, incluir_baja=False: [a for a in A if incluir_baja or a.get("Active", "SI") != "NO"]
INV.get_activo = lambda aid: next((dict(a) for a in A if a["ID"] == aid), {})
_real_upd = INV.update_activo
def _upd(aid, fields):
    if "Name" in fields and not str(fields.get("Name") or "").strip():
        return False, "The asset name is required."
    for a in A:
        if a["ID"] == aid:
            a.update({k: str(v) for k, v in fields.items()})
    UPD.append((aid, dict(fields)))
    return True, "Asset updated."
INV.update_activo = _upd
def _log(grupo, aid, tipo, desde="", hacia="", usuario="", costo="", nota="", fecha="", creado_por=""):
    MOV.append({"AssetID": aid, "Type": tipo, "Date": HOY, "FromLocation": desde, "ToLocation": hacia,
                "User": usuario, "Cost": costo, "Note": nota, "Created": "%s %04d" % (HOY, len(MOV))})
    return True, "ok"
INV._log_mov = _log
INV.list_movimientos = lambda grupo=None, activo_id=None: [m for m in MOV if activo_id is None or m["AssetID"] == activo_id]
INV.categorias = lambda grupo: sorted(set(INV.CAT_DEFAULT) | set(st.session_state.get("_CATS", [])), key=str.lower)
def _crear(**k):
    aid = "ACT-%d" % (len(A) + 1)
    A.append({"ID": aid, "Group": "G", "Name": k["nombre"], "Serial": k.get("serie", ""), "Status": "available",
              "Active": "SI", "Category": k.get("categoria", ""), "LocationType": k.get("ubicacion_tipo", ""),
              "LocationRef": k.get("ubicacion_ref", ""), "PurchaseValue": "0", "UsefulLifeYears": "0",
              "NextService": k.get("proximo_mant", ""), "Note": k.get("nota", "")})
    NUEVOS.append(k)
    return True, aid
INV.create_activo = _crear
auth.list_users = lambda *a, **k: [{"User": "helper1", "Name": "Helper One"}, {"User": "dmoreno", "Name": "Diego M"}]
P.list_projects = lambda *a, **k: [{"ID": "PRJ-1", "Name": "Open job", "Status": "In progress"},
                                   {"ID": "PRJ-2", "Name": "Cancelled job", "Status": "Cancelled"},
                                   {"ID": "PRJ-3", "Name": "Done job", "Status": "Completed"},
                                   {"ID": "LOC-1", "Name": "Store A", "Status": "Open"},
                                   {"ID": "LOC-2", "Name": "Old store", "Status": "Closed"}]
P.etiqueta_proyectos = lambda ps: {p["ID"]: p["Name"] for p in ps}
P.get_project = lambda pid: next((p for p in P.list_projects() if p["ID"] == pid), {})
_LL = st.session_state.setdefault("_LL", [])
incrustar.script = lambda html, *a, **k: _LL.append(html)
flash.mostrar()
IU.render_inventario("G")
'''


def _btn(a, k):
    # ⚠️ v600 · los campos y botones de las ACCIONES llevan una generación al final de la clave
    # (`inv_tbtn_ACT-1_0`): tras registrar nacen vacíos, para que un 2º toque no repita el
    # movimiento. Se busca por la clave exacta o por la de esta generación.
    return next((b for b in a.button if b.key == k), None) or         next((b for b in a.button if _es_de(b.key, k)), None)


def _es_de(clave, k):
    """¿`clave` es el campo `k` (con o sin la generación/tipo que v600 le añade detrás)?"""
    return str(clave) == k or str(clave).startswith(k + "_")


def _ss(a, k, d=None):
    return a.session_state[k] if k in a.session_state else d


def _txt(a):
    return " | ".join(str(x.value) for k in ("markdown", "caption", "info", "warning", "error", "success")
                      for x in getattr(a, k, []))


def _exp(a):
    return list(a.expander) + list(getattr(a, "status", []))


print("1. Las cifras ACTIVAS filtran la lista y bajan a ella; el valor abre los informes")
at = AppTest.from_string(G, default_timeout=300)
at.run()
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
_k = sorted(b.key for b in at.button if str(b.key or "").startswith("cpxkpi_inv_"))
chk("las cinco cifras son BOTONES (eran `st.metric`)",
    _k == ["cpxkpi_inv_disp", "cpxkpi_inv_mant", "cpxkpi_inv_n", "cpxkpi_inv_uso", "cpxkpi_inv_valor"], _k)
chk("…«Available 1 · In use 1 · Service overdue 1»",
    "1" in _btn(at, "cpxkpi_inv_disp").label and "1" in _btn(at, "cpxkpi_inv_uso").label
    and "1" in _btn(at, "cpxkpi_inv_mant").label, [b.label for b in at.button if "cpxkpi_inv" in str(b.key)])
_btn(at, "cpxkpi_inv_mant").click()
at.run()
_ids = list(at.dataframe[0].value["ID"]) if list(at.dataframe) else []
chk("«Service overdue» filtra la lista: solo el del mantenimiento vencido (ACT-1)", _ids == ["ACT-1"], _ids)
chk("…y baja a la tabla", any(".st-key-cpx_inv_tabla" in s for s in _ss(at, "_LL", [])))
_btn(at, "cpxkpi_inv_uso").click()
at.run()
chk("«In use» filtra: ACT-2", list(at.dataframe[0].value["ID"]) == ["ACT-2"], list(at.dataframe[0].value["ID"]))
_btn(at, "cpxkpi_inv_n").click()
at.run()
chk("«Assets» quita los filtros (las dos)", sorted(at.dataframe[0].value["ID"]) == ["ACT-1", "ACT-2"])
_n0 = len(_ss(at, "_LL", []))
_btn(at, "cpxkpi_inv_valor").click()
at.run()
_rep = [e for e in _exp(at) if "Value reports" in str(getattr(e, "label", ""))]
chk("«Current value» ABRE los informes y baja a ellos",
    bool(_rep) and any(".st-key-cpx_inv_rep" in s for s in _ss(at, "_LL", [])[_n0:]), [getattr(e, "label", "") for e in _exp(at)])
import json  # noqa: E402
_cfg = json.loads(at.dataframe[0].proto.columns)
chk("⚠️ la tabla con el ID delante, FIJADO (dos activos con el mismo nombre no se distinguían)",
    list(at.dataframe[0].value.columns)[0] == "ID" and (_cfg.get("ID") or {}).get("pinned") is True, _cfg.get("ID"))
chk("…y el responsable por su NOMBRE («Helper One (helper1)», no «helper1» a secas)",
    "Helper One (helper1)" in list(at.dataframe[0].value["Assigned to"]), list(at.dataframe[0].value["Assigned to"]))
_ru = ast.parse(fuente("core/inventory_ui.py"))
_fr = next(n for n in ast.walk(_ru) if isinstance(n, ast.FunctionDef) and n.name == "_reportes")
chk("los informes a ANCHO COMPLETO (en dos columnas cortaban «$4» por $419)",
    not any(isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "columns" for n in ast.walk(_fr)))

print("\n2. La ficha: acciones arriba, fechas DD/MM/YYYY, el QR plegado")
at.session_state["_inv_open"] = "ACT-1"
at.run()
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
_t = _txt(at)
chk("⚠️ «Maintenance OVERDUE: 01/10/2026» (salía «2026-10-01»)", "Maintenance OVERDUE: 01/10/2026" in _t, _t[:300])
_labs = [str(getattr(e, "label", "")) for e in _exp(at)]
_i_sal = next((i for i, l in enumerate(_labs) if "Check out" in l), None)
_i_qr = next((i for i, l in enumerate(_labs) if "QR code and label" in l), None)
chk("las ACCIONES antes que el QR (en el móvil quedaban debajo), y el QR en su desplegable",
    _i_sal is not None and _i_qr is not None and _i_sal < _i_qr, _labs)
chk("«Mark it as under maintenance (out of use)» (decía «Leave the asset IN service»)",
    any(c.label == "Mark it as under maintenance (out of use)" for c in at.checkbox))
_dl = [d for d in at.get("download_button")]
chk("la etiqueta «Asset_label_ACT-1.pdf» (era «Etiqueta_ACT-1.pdf»)",
    "Asset_label_ACT-1.pdf" in fuente("core/inventory_ui.py").replace('{aid}', 'ACT-1'))

print("\n3. ⚠️ La salida: solo obras ABIERTAS, el responsable por nombre, nada de devoluciones pasadas")
_sb = next(s for s in at.selectbox if _es_de(s.key, "inv_sdt_ACT-1"))
_sb.set_value("project").run()
_pr = next(s for s in at.selectbox if _es_de(s.key, "inv_srp_ACT-1"))
chk("⚠️ ni la cancelada ni la entregada ni el almacén cerrado (salían Penrith y Mascot)",
    list(_pr.options) == ["Open job", "Store A"], list(_pr.options))
_dev = next(d for d in at.date_input if _es_de(d.key, "inv_sdev_ACT-1"))
chk("…la devolución prevista no deja elegir un día pasado (`min_value` = hoy)",
    str(_dev.proto.min) == HOY.isoformat(), _dev.proto.min)
_rs = next(s for s in at.selectbox if _es_de(s.key, "inv_srsp_ACT-1"))
chk("…el responsable por su nombre («Helper One (helper1)»)", "Helper One (helper1)" in list(_rs.options), list(_rs.options))
from core import inventory as INV                                  # noqa: E402
_pasada = (HOY - dt.timedelta(days=3)).isoformat()
INV.get_activo = lambda aid: {"ID": aid, "Status": "available"}
chk("⚠️ el motor tampoco acepta una devolución pasada (nacía «no devuelto»)",
    INV.salida("ACT-1", "G", fecha_devolucion=_pasada)[0] is False)

print("\n4. ⚠️ El traslado: obra/persona ELEGIDAS; «under repair» pone en mantenimiento")
_tt = next(s for s in at.selectbox if _es_de(s.key, "inv_ttt_ACT-1"))
_tt.set_value("under repair").run()
next(t_ for t_ in at.text_input if _es_de(t_.key, "inv_ttr_ACT-1")).set_value("Taller").run()
_btn(at, "inv_tbtn_ACT-1").click()
at.run()
_A = _ss(at, "_A")
_a1 = next(a for a in _A if a["ID"] == "ACT-1")
chk("⚠️ a reparar → «maintenance» (seguía «available» en el taller)",
    _a1["Status"] == "maintenance" and _a1["LocationType"] == "under repair", (_a1["Status"], _a1["LocationType"]))
next(s for s in at.selectbox if _es_de(s.key, "inv_ttt_ACT-1")).set_value("project").run()
chk("…a una obra: se ELIGE la obra (era texto libre)",
    any(_es_de(s.key, "inv_ttp_ACT-1") for s in at.selectbox) and not any(_es_de(t_.key, "inv_ttr_ACT-1") for t_ in at.text_input))
# (se vuelve a buscar en el árbol NUEVO: el elemento de la pasada anterior ya no existe)
next(s for s in at.selectbox if _es_de(s.key, "inv_ttt_ACT-1")).set_value("warehouse").run()
next(t_ for t_ in at.text_input if _es_de(t_.key, "inv_ttr_ACT-1")).set_value("Store").run()
_btn(at, "inv_tbtn_ACT-1").click()
at.run()
_a1 = next(a for a in _ss(at, "_A") if a["ID"] == "ACT-1")
chk("…y de vuelta del taller, disponible", _a1["Status"] == "available", _a1["Status"])

print("\n5. ⚠️ La edición: muestra LO GUARDADO (no deshace el mantenimiento), sin nombre no guarda")
_fs = [f for f in ast.walk(_ru) if isinstance(f, ast.Call) and ast.unparse(f.func) == "st.form"]
chk("los formularios NO se envían con Enter (enviaban el alta a medias)",
    len(_fs) == 2 and all(any(k.arg == "enter_to_submit" and ast.unparse(k.value) == "False" for k in f.keywords)
                          for f in _fs), [ast.unparse(f) for f in _fs])
_d0 = next(d for d in at.date_input if str(d.key).startswith("inv_pm_ACT-1"))
chk("(la próxima revisión del formulario, hoy 01/10/2026)", str(_d0.value) == "2026-10-01", _d0.value)
for a in _ss(at, "_A"):
    if a["ID"] == "ACT-1":
        a["NextService"] = "2027-04-01"            # lo que deja un mantenimiento
at.run()
_d1 = next(d for d in at.date_input if str(d.key).startswith("inv_pm_ACT-1"))
chk("⚠️ tras un mantenimiento, el formulario trae la NUEVA (con clave fija traía la vieja y la escribía)",
    str(_d1.value) == "2027-04-01", (_d1.key, _d1.value))
_st = next(s for s in at.selectbox if s.label == "Status")
chk("⚠️ el estado editable: available · maintenance · damaged (sin «in use» ni «written off»)",
    list(_st.options) == ["available", "maintenance", "damaged"], list(_st.options))
next(t_ for t_ in at.text_input if t_.label == "Name").set_value("")
next(b for b in at.button if "Save changes" in str(b.label)).click()
at.run()
chk("⚠️ sin nombre NO se guarda («The asset name is required.»)",
    "The asset name is required." in _txt(at) and next(a for a in _ss(at, "_A") if a["ID"] == "ACT-1")["Name"] == "Taladro",
    _txt(at)[:300])
chk("…y el motor de verdad, igual",
    __import__("importlib").reload(INV).update_activo("ACT-1", {"Name": "  "}) ==
    (False, "The asset name is required."))

print("\n6. ⚠️ La baja: con confirmación, con aviso, SIN pisar la nota; la vuelta con su movimiento")
at = AppTest.from_string(G, default_timeout=300)
at.session_state["_inv_open"] = "ACT-1"
at.run()
next(t_ for t_ in at.text_input if t_.key == "inv_baja_mot_ACT-1").set_value("roto").run()
chk("sin la casilla, el botón está DESACTIVADO", _btn(at, "inv_baja_ACT-1").disabled is True)
next(c for c in at.checkbox if c.key == "inv_baja_conf_ACT-1").check().run()
_btn(at, "inv_baja_ACT-1").click()
at.run()
_a1 = next(a for a in _ss(at, "_A") if a["ID"] == "ACT-1")
_m = [m for m in _ss(at, "_MOV") if m["Type"] == "written off"]
chk("⚠️ la NOTA se conserva («nota original»; el motivo la pisaba) y el motivo va al historial",
    _a1["Note"] == "nota original" and _m and _m[-1]["Note"] == "roto", (_a1["Note"], _m))
chk("…y «Asset written off.» A LA VISTA (no decía nada)",
    "Asset written off." in " ".join(str(x.value) for x in at.success), [x.value for x in at.success])
at.session_state["_inv_open"] = "ACT-1"
at.run()
chk("la ficha de baja dice su MOTIVO («Reason: roto»)", "Reason: roto" in _txt(at), _txt(at)[:300])
_btn(at, "inv_react_ACT-1").click()
at.run()
_a1 = next(a for a in _ss(at, "_A") if a["ID"] == "ACT-1")
chk("reactivar: «Asset reactivated.» y su movimiento en el historial",
    _a1["Status"] == "available" and _a1["Active"] == "SI"
    and any(m["Type"] == "reactivated" for m in _ss(at, "_MOV"))
    and "Asset reactivated." in " ".join(str(x.value) for x in at.success), [x.value for x in at.success])

print("\n7. ⚠️ El alta: sin Enter, avisa de nombre o serie REPETIDOS, con mensaje")
at = AppTest.from_string(G, default_timeout=300)
at.session_state["_inv_nuevo"] = True
at.run()
_ut = next(s for s in at.selectbox if s.label == "Location (type)")
chk("nace en el almacén o en reparación (a una obra, con la salida)",
    list(_ut.options) == ["warehouse", "under repair"], list(_ut.options))
next(t_ for t_ in at.text_input if t_.label == "Asset name *").set_value("taladro ")
next(b for b in at.button if "Register" in str(b.label)).click()
at.run()
chk("⚠️ «taladro» como «Taladro»: AVISA y no crea (dos envíos creaban dos iguales)",
    "There is already an asset with that name or serial: ACT-1" in _txt(at) and not _ss(at, "_NUEVOS"), _txt(at)[:300])
next(c for c in at.checkbox if "Register it even though" in str(c.label)).check()
next(b for b in at.button if "Register" in str(b.label)).click()
at.run()
chk("…con la casilla, crea y lo DICE («Asset ACT-3 «taladro» registered.»)",
    len(_ss(at, "_NUEVOS", [])) == 1 and "Asset ACT-3 «taladro» registered." in " ".join(str(x.value) for x in at.success),
    [x.value for x in at.success])
_rs = INV.homonimos.__code__.co_varnames
INV.list_activos = lambda grupo=None, incluir_baja=False: [{"ID": "ACT-9", "Name": "X", "Serial": "SN-77"}]
chk("…y la SERIE repetida también avisa (ACT-0001 y 0002 compartían «ZZ-SN-001»)",
    [a["ID"] for a in INV.homonimos("G", "Otro", "sn-77")] == ["ACT-9"])

print("\n8. Categorías: solo las propias se quitan, sin repetir por mayúsculas, el campo se vacía")
INV.categorias = lambda grupo: ["Consumable", "Equipment", "Other", "PPE", "Tool", "Vehicle", "Grúas"]
chk("`categorias_propias` deja fuera las de fábrica", INV.categorias_propias("G") == ["Grúas"], INV.categorias_propias("G"))
chk("⚠️ «tool» junto a «Tool» NO entra", INV.add_categoria("G", "tool") == (False, "That category already exists."))
at = AppTest.from_string(G, default_timeout=300)
at.run()
chk("sin categorías propias, no ofrece quitar ninguna", not any(s.key == "inv_cat_del" for s in at.selectbox)
    and "You have not added any category of your own yet." in _txt(at))
# el campo se VACÍA al añadir (`add_categoria` sustituido: la prueba no escribe en la hoja)
at = AppTest.from_string(G.replace("flash.mostrar()",
                                   "INV.add_categoria = lambda g, n: (True, 'Category added.')\nflash.mostrar()"),
                         default_timeout=300)
at.run()
next(t_ for t_ in at.text_input if t_.key == "inv_cat_new").set_value("Grúas").run()
_btn(at, "inv_cat_add").click()
at.run()
_cn = next(t_ for t_ in at.text_input if t_.key == "inv_cat_new")
chk("al añadir, el campo se VACÍA (se quedaba con lo escrito) — y en el navegador: lo ASIGNA (trampa 31)",
    _cn.value == "" and bool(_cn.proto.set_value)
    and "Category added." in " ".join(str(x.value) for x in at.success),
    (_cn.value, _cn.proto.set_value, [x.value for x in at.success]))

print("\n9. La campana abre el ACTIVO (llevaba a la lista)")
_hu = fuente("core/home_ui.py")
chk("la alerta del inventario lleva al activo", '"destino": ("activo", e.get("id", ""))' in _hu)
from core import home_ui as HU                                     # noqa: E402
_nav = []
HU.navegar = lambda s, sub=None: _nav.append((s, sub))
st.session_state.pop("_inv_open", None)
HU._ir_alerta(("activo", "ACT-7"), "G")
chk("…`_ir_alerta` abre su ficha en Inventory", st.session_state.get("_inv_open") == "ACT-7"
    and _nav == [("inventario", None)], (st.session_state.get("_inv_open"), _nav))

print("\n10. Textos y valores traducibles (las formas viejas ya no están en el código)")
_c = cadenas("core/inventory_ui.py")
_viejas = ["Tap an asset to see its record, its QR code and manage it. (",
           "written-off asset(s) hidden.", "Leave the asset IN service", "Etiqueta_",
           "**Location:** ", "Next service: "]
_quedan = [v for v in _viejas if any(v in c and "{" not in c for c in _c)]
chk("ninguna de las formas viejas sin `t()`", not _quedan, _quedan)
# ⚠️ Por la ETIQUETA del desplegable, no por la lista que recibe: la edición pasa la lista en una
# variable (`_conds`, de `opciones_con_actual`) y la 1ª tanda de romper_v599 dejó escapar «la
# condición vuelve sin su etiqueta» con razón — la sonda solo veía el alta (trampa 30).
_ETQS = {"Condition", "Location (type)", "New location (type)", "Status", "Category"}


def _etq_de(n):
    _a = n.args[0] if n.args else None
    return (_a.args[0].value if isinstance(_a, ast.Call) and _a.args and isinstance(_a.args[0], ast.Constant)
            else "")


_sb = [n for n in ast.walk(_ru) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "selectbox"
       and _etq_de(n) in _ETQS]
_fmt = [_etq_de(n) for n in _sb if not any(k.arg == "format_func" for k in n.keywords)]
chk("condición, ubicación, estado y categoría con su etiqueta, en TODOS sus desplegables (%d)" % len(_sb),
    len(_sb) >= 9 and not _fmt, (len(_sb), _fmt))

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
sys.exit(1 if fallos else 0)
