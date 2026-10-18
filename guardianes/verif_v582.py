"""v582 · FINANCE → CATALOGUE, PROBADA ACCIÓN POR ACCIÓN (decisión del usuario: «dale con todo»).

  1. ⚠️ FANTASMAS (trampa 37): crear el primer artículo dejó cuatro formularios de alta muertos
     donde iba la tabla → el tema oculta lo que sigue «stale» con la pasada terminada (toda la
     app: 57 desplegables con clave hacen un envío + `st.rerun()`).
  2. ⚠️ El formulario se quedaba lleno y un segundo toque creó otro idéntico → generación de
     formulario, y aviso (con casilla, como el alta de obras) si el nombre ya existe.
  3. ⚠️ La edición aceptaba costo $0 → UNA validación para el alta y la edición (motor).
  4. ⚠️ «Price it from the drawing» no podía proponer nada: la regla de cantidad no se podía
     poner en ninguna pantalla → «Quantity from the drawing» en el alta y en la edición, y la
     cotización avisa ANTES de leer el plano, con un botón al catálogo.
  5-9. La tabla: un toque abre, el costo delante, nombre fijado, «Active» solo con los
     desactivados; las cifras filtran (y el filtro se recuerda); «Nothing matches» con «Show
     all»; «1 item» / «3 items».
 10-18. El servicio sin unidad (salía «hora»), la categoría por defecto del tipo (era
     «Engineering»), «Product/Service», el aviso con el nombre, «deactivated/reactivated», el
     aviso falso del desactivado, el menú vuelve a la lista, dónde se usa (un toque abre la
     cotización) y el tipo se puede corregir.

AppTest y el motor con sus fuentes sustituidas: ninguna hoja se toca.
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


def _src(rel):
    return io.open(os.path.join(RAIZ, rel), encoding="utf-8").read()


def _func(rel, nombre):
    return next((n for n in ast.walk(ast.parse(_src(rel)))
                 if isinstance(n, ast.FunctionDef) and n.name == nombre), None)


import streamlit as st                                                      # noqa: E402
st.session_state["auth"] = {"usuario": "adm", "rol": "administrator", "grupo": "G"}
from core import catalogo as CAT, quotes as Q, auditoria, hojas            # noqa: E402
from core import theme as T, home_ui                                        # noqa: E402

# ═════════════════════════════════════════════════════════════════
print("1. ⚠️ Los fantasmas se ocultan (el tema, para toda la app)")
_css = T._CSS
chk("con la pasada TERMINADA, lo «stale» no se ve",
    '[data-testid="stApp"][data-test-script-state="notRunning"] [data-stale="true"]' in _css
    and "display: none !important" in _css)
chk("…y tampoco el bloque que SOLO tiene contenido viejo (la carcasa del desplegable)",
    ':has([data-stale="true"]):not(:has([data-stale="false"]))' in _css)
chk("…durante la pasada sí (se ve atenuado, como siempre): la regla exige «notRunning»",
    _css.count('data-test-script-state="notRunning"') == 2)

# ═════════════════════════════════════════════════════════════════
print("\n3. ⚠️ UNA validación para el alta y la edición (motor, EJECUTADO)")
chk("producto con costo 0 → no", "greater than 0" in CAT._valida("product", "R", 0, 0, 0))
chk("servicio sin tarifa → no", "hourly rate" in CAT._valida("service", "S", 0, 8, 0))
chk("sin nombre → no", "name" in CAT._valida("product", " ", 5, 0, 0).lower())
chk("tipo inválido → no", "Invalid type" in CAT._valida("xx", "R", 5, 0, 0))
chk("lo bueno pasa", CAT._valida("product", "R", 5, 0, 0) == "" and CAT._valida("service", "S", 0, 8, 60) == "")


class _WS:
    def __init__(self, recs):
        self.recs, self.lotes, self.filas = recs, [], []

    def get_all_records(self, **k):
        return [dict(r) for r in self.recs]

    def batch_update(self, lote, **k):
        self.lotes.append(lote)

    def append_row(self, fila, **k):
        self.filas.append(fila)


_REC = [{"ID": "CAT-00001", "Group": "G", "Type": "product", "Name": "Riel", "UnitCost": "120",
         "Unit": "unit", "EstHours": "", "HourlyRate": "", "Active": "SI"},
        {"ID": "CAT-00002", "Group": "G", "Type": "product", "Name": "Viejo a cero", "UnitCost": "0",
         "Unit": "unit", "EstHours": "", "HourlyRate": "", "Active": "NO"}]
_o = {n: getattr(CAT, n) for n in ("_ws", "_invalidate")}
_oa, _oir = auditoria.registrar, hojas.ids_referenciados
try:
    _w = _WS(_REC)
    CAT._ws = lambda: _w
    CAT._invalidate = lambda: None
    auditoria.registrar = lambda *a, **k: True
    hojas.ids_referenciados = lambda *a, **k: set()
    ok, msg = CAT.actualizar("CAT-00001", {"UnitCost": 0})
    chk("⚠️ editar el costo a 0 se RECHAZA (decía «Item updated.»)", not ok and "greater than 0" in msg
        and not _w.lotes, (ok, msg, _w.lotes))
    ok, msg = CAT.actualizar("CAT-00001", {"Name": "  "})
    chk("…y dejarlo sin nombre", not ok and not _w.lotes, (ok, msg))
    ok, msg = CAT.actualizar("CAT-00001", {"Type": "service"})
    chk("⚠️ pasarlo a SERVICIO sin horas ni tarifa, no", not ok and "hourly rate" in msg, (ok, msg))
    ok, msg = CAT.actualizar("CAT-00001", {"Type": "service", "EstHours": 8, "HourlyRate": 60, "Unit": ""})
    chk("…con ellas, sí (el tipo se puede corregir)", ok and _w.lotes, (ok, msg))
    _w.lotes.clear()
    ok, msg = CAT.set_activo("CAT-00002", True)
    chk("reactivar uno viejo a $0 no pasa por la validación (no toca el precio)", ok, (ok, msg))
    chk("⚠️ …y dice «Item reactivated.» (decía «Item updated.»)", msg == "Item reactivated.", msg)
    ok, msg = CAT.set_activo("CAT-00001", False)
    chk("«Item deactivated.»", ok and msg == "Item deactivated.", msg)
    ok, msg = CAT.crear("G", "Riel", tipo="product", costo_unit=0, creado_por="t")
    chk("el ALTA pasa por la misma validación (costo 0 → no)", not ok and "greater than 0" in msg
        and not _w.filas, (ok, msg))
    ok, cid = CAT.crear("G", "Montaje", tipo="service", horas_est=8, tarifa_hora=60,
                        unidad="hora", creado_por="t", qty_rule="per_stop")
    _f = _w.filas[-1] if _w.filas else []
    chk("⚠️ un servicio nace SIN unidad aunque le llegue «hora»", ok and _f[5] == "", _f[:6])
    chk("…y con su regla de cantidad (última columna)", _f[-1] == "per_stop", _f[-1:])
finally:
    for _n, _v in _o.items():
        setattr(CAT, _n, _v)
    auditoria.registrar, hojas.ids_referenciados = _oa, _oir

chk("categoría por defecto: Materials (producto) e Installation (servicio); era «Engineering»",
    CAT.categoria_defecto("product") == "Materials" and CAT.categoria_defecto("service") == "Installation")
chk("`regla_de`: sin regla, «manual»; una desconocida, también",
    CAT.regla_de({}) == "manual" and CAT.regla_de({"QtyRule": "zz"}) == "manual"
    and CAT.regla_de({"QtyRule": "per_stop"}) == "per_stop")
_or = CAT._records
try:
    CAT._records = lambda: [{"ID": "CAT-1", "Group": "G", "Name": "Riel  T75"},
                            {"ID": "CAT-2", "Group": "G", "Name": "riel t75", "Active": "NO"},
                            {"ID": "CAT-3", "Group": "OTRO", "Name": "Riel T75"}]
    chk("`homonimos`: sin mayúsculas ni espacios de más, también desactivados, solo su grupo",
        [i["ID"] for i in CAT.homonimos("G", " RIEL t75 ")] == ["CAT-1", "CAT-2"])
    chk("…y excluye el propio", [i["ID"] for i in CAT.homonimos("G", "riel t75", excluir="CAT-1")] == ["CAT-2"])
finally:
    CAT._records = _or

print("\n17. Dónde se usa: las cotizaciones con una línea de ESE artículo")
_oq = Q._records
try:
    Q._records = lambda: [
        {"ID": "COT-1", "Group": "G", "Date": "2026-10-01", "Number": "0001",
         "LinesJSON": json.dumps([{"catalogo_id": "CAT-1"}, {"catalogo_id": "CAT-9"}])},
        {"ID": "COT-2", "Group": "G", "Date": "2026-10-02", "Number": "0002",
         "LinesJSON": json.dumps([{"catalogo_id": "CAT-1"}])},
        {"ID": "COT-3", "Group": "G", "Date": "2026-10-03", "Number": "0003",
         "LinesJSON": json.dumps([{"catalogo_id": "CAT-11"}])},
        {"ID": "COT-4", "Group": "OTRO", "Date": "2026-10-04", "Number": "0004",
         "LinesJSON": json.dumps([{"catalogo_id": "CAT-1"}])}]
    chk("por ID exacto (CAT-11 no es CAT-1), de su grupo, la más nueva primero",
        [c["ID"] for c in Q.con_item("G", "CAT-1")] == ["COT-2", "COT-1"],
        [c["ID"] for c in Q.con_item("G", "CAT-1")])
finally:
    Q._records = _oq

print("\n10. El PDF: un servicio sin unidad (las líneas viejas traen «hora»)")
_pdf = _src("core/quote_pdf.py")
chk("las líneas de servicio no pintan unidad",
    'if str(l.get("tipo", "")) == "service":\n            uni = ""' in _pdf)

print("\n16. El menú vuelve a la lista")
chk("⚠️ «Catalogue» en el menú cierra el artículo abierto",
    home_ui._ABIERTO_EN_SUB.get(("finanzas", "📚 Catálogo")) == "_cat_open")

# ═════════════════════════════════════════════════════════════════
from streamlit.testing.v1 import AppTest                                    # noqa: E402

CAB = r'''
import sys, json
sys.path.insert(0, r"%s")
import streamlit as st
from core import catalogo_ui as CU, catalogo as CAT, quotes as Q
st.session_state["auth"] = {"rol": "administrator", "usuario": "adm", "nombre": "Adm", "grupo": "G"}
st.session_state.setdefault("_LL", [])
ROWS = st.session_state.setdefault("_ROWS", [
    {"ID": "CAT-1", "Group": "G", "Type": "product", "Name": "Item A", "Category": "Materials",
     "UnitCost": "120", "Unit": "unit", "Active": "SI"},
    {"ID": "CAT-2", "Group": "G", "Type": "service", "Name": "Montaje", "Category": "Installation",
     "EstHours": "8", "HourlyRate": "60", "Unit": "hora", "Active": "SI", "QtyRule": "per_stop"},
    {"ID": "CAT-3", "Group": "G", "Type": "product", "Name": "Botonera", "Category": "Materials",
     "UnitCost": "80", "Unit": "set", "Active": "SI"},
    {"ID": "CAT-4", "Group": "G", "Type": "product", "Name": "Viejo", "Category": "Other",
     "UnitCost": "5", "Unit": "unit", "Active": "NO"}] if not st.session_state.get("_VACIO") else [])
CAT._records = lambda: [dict(r) for r in ROWS]
CAT.is_configured = lambda: True
_LL = st.session_state["_LL"]
def _q(nombre, devuelve):
    def f(*a, **k):
        _LL.append((nombre, a, k))
        return devuelve
    return f
CAT.crear = _q("crear", (True, "CAT-9"))
CAT.actualizar = _q("actualizar", (True, "Item updated."))
CAT.set_activo = _q("set_activo", (True, "Item reactivated."))
Q._records = lambda: [
    {"ID": "COT-1", "Group": "G", "Date": "2026-10-01", "Number": "0001", "Version": "1",
     "ClientName": "Cli", "Status": "sent", "Total": "300", "ValidUntil": "2099-01-01",
     "LinesJSON": json.dumps([{"catalogo_id": "CAT-2"}])}]
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    for _k, _v in (st.session_state.get("_PRE") or {}).items():
        st.session_state[_k] = _v
from core import flash
flash.mostrar()
CU.render_catalogo("G")
''' % RAIZ


def _app(pre=None, vacio=False):
    a = AppTest.from_string(CAB, default_timeout=90)
    if pre:
        a.session_state["_PRE"] = pre
    if vacio:
        a.session_state["_VACIO"] = True
    a.run()
    return a


def _ss(a, k, d=None):
    try:
        return a.session_state[k]
    except KeyError:
        return d


def _kb(a):
    return {b.key: b.label for b in a.button}


def _textos(a):
    return " | ".join([str(x.value) for x in list(a.info) + list(a.error) + list(a.warning)
                       + list(a.success) + list(a.caption) + list(a.markdown)])


def _cols(df_el):
    try:
        return json.loads(df_el.proto.columns)
    except Exception:
        return {}


def _llamadas(a, nombre):
    return [x for x in (_ss(a, "_LL") or []) if x[0] == nombre]


def _boton(a, texto):
    return next((b for b in a.button if texto in str(b.label)), None)


print("\n7, 9. Las cifras, ACTIVAS")
at = _app()
chk("la lista se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_b = _kb(at)
chk("las 3 cifras son botones", [k for k in _b if str(k).startswith("cpxkpi_cat_")] ==
    ["cpxkpi_cat_n", "cpxkpi_cat_prod", "cpxkpi_cat_serv"], [k for k in _b if str(k).startswith("cpxkpi_cat_")])
chk("«Items 3 · Products 2 · Services 1» (el desactivado no cuenta)",
    (_b.get("cpxkpi_cat_n"), _b.get("cpxkpi_cat_prod"), _b.get("cpxkpi_cat_serv")) ==
    ("Items\n\n3\n\nactive in the catalogue", "Products\n\n2\n\ncharged by quantity",
     "Services\n\n1\n\ncharged by the hour"), (_b.get("cpxkpi_cat_n"), _b.get("cpxkpi_cat_serv")))
chk("«3 items» (decía «3 item(s)»)", "3 items" in _textos(at) and "item(s)" not in _textos(at), "")

print("\n5, 6, 12, 10. La tabla")
_df = at.dataframe[0] if at.dataframe else None
_v = _df.value if _df is not None else None
chk("⚠️ el COSTO delante (se quedaba fuera de la vista a 846 px y en el móvil)",
    _v is not None and list(_v.columns) == ["Item", "Costo", "Tipo", "Category", "Unidad", "Horas"],
    list(_v.columns) if _v is not None else None)
_c = _cols(_df)
chk("el nombre FIJADO", (_c.get("Item") or {}).get("pinned") is True)
chk("las cabeceras en inglés", {k: (_c.get(k) or {}).get("label") for k in ("Costo", "Tipo", "Unidad", "Horas")}
    == {"Costo": "Cost", "Tipo": "Type", "Unidad": "Unit", "Horas": "Hours"},
    {k: (_c.get(k) or {}).get("label") for k in ("Costo", "Tipo", "Unidad", "Horas")})
chk("«Product» / «Service» (salía en minúscula)", _v is not None and sorted(set(_v["Tipo"])) == ["Product", "Service"],
    sorted(set(_v["Tipo"])) if _v is not None else None)
_fila_s = list(_v["Item"]).index("Montaje") if _v is not None else -1
chk("⚠️ el servicio sin unidad: «—» (la hoja trae «hora»)", _v is not None and list(_v["Unidad"])[_fila_s] == "—",
    list(_v["Unidad"]) if _v is not None else None)
chk("sin la columna «Active» si no se ven los desactivados (era una columna de 🟢)",
    _v is not None and "Activo" not in _v.columns)
at.checkbox(key="cat_ver_inact").check()
at.run()
_v = at.dataframe[0].value if at.dataframe else None
chk("…con ellos, sí, y dice cuál", _v is not None and "🔴 deactivated" in list(_v.get("Activo", [])),
    list(_v.get("Activo", [])) if _v is not None else None)
_rc = _func("core/catalogo_ui.py", "render_catalogo")
chk("⚠️ un toque abre: `single-cell`",
    any(isinstance(n, ast.keyword) and n.arg == "selection_mode" and ast.unparse(n.value) == "'single-cell'"
        for n in ast.walk(_rc)))
at = _app(pre={"cat_tbl_0": {"selection": {"rows": [], "columns": [], "cells": [(1, "Category")]}}})
_orden = [r["ID"] for r in sorted([{"ID": "CAT-1", "c": "Materials", "n": "item a"},
                                    {"ID": "CAT-2", "c": "Installation", "n": "montaje"},
                                    {"ID": "CAT-3", "c": "Materials", "n": "botonera"}],
                                   key=lambda r: (r["c"], r["n"]))]
chk("⚠️ un toque en la CELDA de la 2ª fila abre ESE artículo (con otra generación de clave)",
    _ss(at, "_cat_open") == _orden[1] and _ss(at, "_cat_tbl_gen") == 1,
    (_ss(at, "_cat_open"), _ss(at, "_cat_tbl_gen"), _orden))

print("\n7. Las cifras filtran, y el filtro se recuerda")
at = _app()
at.button(key="cpxkpi_cat_serv").click()
at.run()
_v = at.dataframe[0].value if at.dataframe else None
chk("⚠️ «Services» deja solo los servicios", _ss(at, "cpxseg_cat_tipo") == "Servicios"
    and _v is not None and list(_v["Item"]) == ["Montaje"], list(_v["Item"]) if _v is not None else None)
chk("…«1 item» en singular", "1 item" in _textos(at) and "1 items" not in _textos(at), "")
chk("…y baja a la tabla", ".st-key-ir_cpx_cat_tabla" in _textos(at), "")
_rad = [n for n in ast.walk(_rc) if isinstance(n, ast.Call) and "radio" in ast.unparse(n.func)]
chk("el filtro se RECUERDA (`persist_state`)", _rad and any(k.arg == "persist_state" for k in _rad[0].keywords))

print("\n8. Una búsqueda sin resultados no dice «No items yet»")
at = _app()
at.text_input(key="cat_q").set_value("zzz-nada")
at.run()
chk("⚠️ «Nothing matches this search or filter.» (decía «No items yet» con tres artículos)",
    "Nothing matches this search or filter." in _textos(at) and "No items yet" not in _textos(at), "")
chk("…con «Show all»", "cat_ver_todo" in _kb(at))
at.button(key="cat_ver_todo").click()
at.run()
chk("…que borra la búsqueda y el filtro", _ss(at, "cat_q") == "" and _ss(at, "cpxseg_cat_tipo") == "Todos"
    and at.dataframe and len(at.dataframe[0].value) == 3, (_ss(at, "cat_q"), _ss(at, "cpxseg_cat_tipo")))
chk("la condición del alta abierta va en la CLAVE (verif_v547)",
    'key=f"exp_cat_new_{vacio}"' in _src("core/catalogo_ui.py"))
at = _app(vacio=True)
chk("con el catálogo VACÍO sí, «No items yet», y el alta abierta (la condición en la clave)",
    "No items yet" in _textos(at) and any(e.proto.expanded for e in at.expander
                                         if "New item" in str(e.label)), _textos(at)[:120])

print("\n2, 11, 4, 13. El alta")
at = _app()
chk("⚠️ la categoría por defecto de un producto es Materials (era «Engineering»)",
    at.selectbox(key="cat_new_cat_product_0").value == "Materials", at.selectbox(key="cat_new_cat_product_0").value)
chk("⚠️ hay «Quantity from the drawing» (sin ella «Price it from the drawing» no proponía nada)",
    at.selectbox(key="cat_new_regla_0").value == "manual")
at.text_input(key="cat_new_nom_0").set_value("Riel nuevo")
at.number_input(key="cat_new_c_0").set_value(15.0)
at.selectbox(key="cat_new_regla_0").set_value("per_stop")
_boton(at, "Save item").click()
at.run()
_cr = _llamadas(at, "crear")
chk("se crea con su categoría, su unidad y su regla", _cr and _cr[-1][2].get("categoria") == "Materials"
    and _cr[-1][2].get("unidad") == "unit" and _cr[-1][2].get("qty_rule") == "per_stop", _cr[-1] if _cr else None)
chk("⚠️ el aviso dice el NOMBRE (decía «Item CAT-00001 created.»)", "Item «Riel nuevo» created." in _textos(at), "")
chk("⚠️ y el formulario se VACÍA (otra generación): un segundo toque ya no crea otro igual",
    _ss(at, "_cat_new_gen") == 1 and at.text_input(key="cat_new_nom_1").value == "", _ss(at, "_cat_new_gen"))
at = _app()
at.text_input(key="cat_new_nom_0").set_value("  item A ")
at.number_input(key="cat_new_c_0").set_value(15.0)
_boton(at, "Save item").click()
at.run()
chk("⚠️ un nombre que YA existe (sin mayúsculas ni espacios) avisa y NO crea",
    not _llamadas(at, "crear") and "There is already an item called «item A»: CAT-1" in _textos(at), _textos(at)[:200])
_cb = [c for c in at.checkbox if "repeated" in str(c.label)]
chk("…con su casilla", len(_cb) == 1)
if _cb:
    _cb[0].check()
    _boton(at, "Save item").click()
    at.run()
chk("…y marcándola, se crea (el nombre PUEDE repetirse: la identidad es el ID)", len(_llamadas(at, "crear")) == 1,
    _llamadas(at, "crear"))
at = _app()
at.radio(key="cat_new_tipo").set_value("service")
at.run()
chk("un servicio: Installation por defecto", at.selectbox(key="cat_new_cat_service_0").value == "Installation")
at.text_input(key="cat_new_nom_0").set_value("Puesta en marcha")
at.number_input(key="cat_new_h_0").set_value(4.0)
at.number_input(key="cat_new_r_0").set_value(70.0)
_boton(at, "Save item").click()
at.run()
_cr = _llamadas(at, "crear")
chk("⚠️ …y nace SIN unidad (la pantalla le ponía «hora»)", _cr and _cr[-1][2].get("unidad") == ""
    and _cr[-1][2].get("tipo") == "service", _cr[-1] if _cr else None)
chk("«Product» / «Service» en el alta", [str(o) for o in at.radio(key="cat_new_tipo").options] ==
    [":material/inventory_2: Product", ":material/engineering: Service"], at.radio(key="cat_new_tipo").options)

print("\n17, 18, 4. El detalle")
at = _app(pre={"_cat_open": "CAT-2"})
chk("el detalle se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("el tipo, editable (`cat_ed_tipo_…`)", at.radio(key="cat_ed_tipo_CAT-2").value == "service")
_rg = [s for s in at.selectbox if s.label == "Quantity from the drawing"]
chk("su regla de cantidad, con la guardada", _rg and _rg[0].value == "per_stop", _rg[0].value if _rg else None)
chk("⚠️ dónde se usa: «Used in 1 quote»", "Used in 1 quote" in _textos(at), "")
_u = _kb(at).get("cat_uso_COT-1", "")
chk("…con un botón por cotización («No. 0001 · Cli · sent · $300»)",
    "No. 0001 · Cli · sent · \\$300" in _u or "No. 0001 · Cli · sent · $300" in _u, _u)
at.button(key="cat_uso_COT-1").click()
at.run()
chk("…que la ABRE en Quotes", _ss(at, "_cot_open") == "COT-1"
    and tuple(_ss(at, "_admin_nav_pending") or ()) == ("finanzas", "📄 Cotizaciones"),
    (_ss(at, "_cot_open"), _ss(at, "_admin_nav_pending")))
at = _app(pre={"_cat_open": "CAT-2"})
at.radio(key="cat_ed_tipo_CAT-2").set_value("product")
at.run()
_un = [s for s in at.selectbox if s.label == "Unit"]
chk("⚠️ de servicio a producto: la unidad empieza en «unit» (no la «hora» de antes)",
    _un and _un[0].value == "unit", _un[0].value if _un else None)
[n for n in at.number_input if n.label == "Unit cost"][0].set_value(30.0)
_boton(at, "Save changes").click()
at.run()
_ac = _llamadas(at, "actualizar")
chk("⚠️ …y guarda el TIPO nuevo con su costo y su unidad", _ac and _ac[-1][1][1].get("Type") == "product"
    and _ac[-1][1][1].get("Unit") == "unit" and _ac[-1][1][1].get("UnitCost") == 30.0, _ac[-1] if _ac else None)
at = _app(pre={"_cat_open": "CAT-4"})
chk("⚠️ el desactivado ya no promete salir al cotizar (esa casilla solo está en la lista)",
    "it is not offered when quoting. Reactivate it to quote it again." in _textos(at)
    and "unless you tick" not in _textos(at), "")
at.button(key="cat_on_CAT-4").click()
at.run()
chk("reactivar avisa con el mensaje del motor", "Item reactivated." in _textos(at), "")

print("\n4. La cotización avisa ANTES de leer el plano, con un botón")
CAB2 = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
from core import quotes_ui as QU, catalogo as CAT
st.session_state["auth"] = {"rol": "administrator", "usuario": "adm", "grupo": "G"}
CAT.list_items = lambda g, **k: [{"ID": "CAT-1", "Type": "product", "Name": "A", "QtyRule": ""}]
QU._desde_plano("G")
''' % RAIZ
at = AppTest.from_string(CAB2, default_timeout=60)
at.run()
chk("sin ningún artículo con regla, el aviso y «Set it in Catalogue» sin subir el plano",
    "cot_plano_cat" in _kb(at) and "Quantity from the drawing" in _textos(at), list(_kb(at)))
at.button(key="cot_plano_cat").click()
at.run()
chk("…que lleva al catálogo", tuple(_ss(at, "_admin_nav_pending") or ()) == ("finanzas", "📚 Catálogo"),
    _ss(at, "_admin_nav_pending"))

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
sys.exit(1 if fallos else 0)
