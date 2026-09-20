# -*- coding: utf-8 -*-
"""EJECUTA las pantallas de v487 con Sheets sustituido y mira lo que se PINTA.

1. Inventario: las KPIs «Available»/«In use» marcaban 0 SIEMPRE desde v469 (buscaban
   "disponible"/"en_uso" y el estado llega canonizado a "available"/"in use").
2. Ficha del activo y del articulo: un valor guardado que no esta en la lista se
   CONSERVA (antes el desplegable mostraba la primera opcion y «Save» la escribia).

Importar NO ejecuta (v378): hay que llamar a la funcion. Firmas leidas del codigo (v135).
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

import streamlit as st                                            # noqa: E402
from streamlit.delta_generator import DeltaGenerator              # noqa: E402

st.session_state["auth"] = {"usuario": "smoke", "rol": "administrator",
                            "grupo": "cliente1", "nombre": "smoke"}

metricas, selects = {}, {}


def _nada(*a, **k):
    return None


def _metric(self_or_label, *a, **k):
    # llamado como st.metric(label, valor) o col.metric(label, valor)
    if isinstance(self_or_label, DeltaGenerator):
        label, valor = a[0], a[1]
    else:
        label, valor = self_or_label, a[0]
    metricas[str(label)] = valor


def _select(self_or_label, *a, **k):
    if isinstance(self_or_label, DeltaGenerator):
        label, opciones = a[0], (a[1] if len(a) > 1 else k.get("options"))
    else:
        label, opciones = self_or_label, (a[0] if a else k.get("options"))
    opciones = list(opciones)
    idx = k.get("index", 0)
    selects[str(label)] = (opciones, idx)
    return opciones[idx] if opciones else None


for _n in ("warning", "info", "success", "error", "markdown", "caption", "write",
           "subheader", "header", "title", "divider", "toast", "image", "code",
           "download_button", "dataframe", "plotly_chart"):
    setattr(st, _n, _nada)
    setattr(DeltaGenerator, _n, lambda self, *a, **k: None)
st.metric = lambda *a, **k: _metric(*a, **k)
DeltaGenerator.metric = _metric
st.selectbox = lambda *a, **k: _select(*a, **k)
DeltaGenerator.selectbox = _select

ok = True


def chk(txt, cond, det=""):
    global ok
    ok = ok and bool(cond)
    print("  %s %s%s" % ("OK  " if cond else "FALLO", txt, ("  -> %s" % det) if det and not cond else ""))


from core import inventory as INV, inventory_ui, catalogo as CAT, catalogo_ui  # noqa: E402

# ── 1 · KPIs del inventario ──────────────────────────────────────────────────
print("1. Las KPIs de inventario cuentan los estados CANONICOS")
ACTS = [{"ID": "A1", "Group": "cliente1", "Name": "x", "Status": INV.DISPONIBLE},
        {"ID": "A2", "Group": "cliente1", "Name": "y", "Status": INV.DISPONIBLE},
        {"ID": "A3", "Group": "cliente1", "Name": "z", "Status": INV.EN_USO}]
INV.list_activos = lambda grupo=None, incluir_baja=False: list(ACTS)
INV.alertas = lambda grupo: []
INV.categorias = lambda grupo: ["Consumable", "Equipment", "Other", "PPE", "Tool", "Vehicle"]
INV.is_configured = lambda: True
st.session_state.pop("_inv_open", None)
try:
    inventory_ui.render_inventario("cliente1")
except Exception as e:                  # lo que venga DESPUES de las KPIs no importa aqui
    print("     (render cortado tras las KPIs: %s)" % type(e).__name__)
_av = {k: v for k, v in metricas.items() if "vailable" in k}
_us = {k: v for k, v in metricas.items() if "n use" in k}
chk("se pintaron las dos tarjetas (si no, lo de abajo pasaria en vacio)",
    _av and _us, "metricas=%r" % metricas)
chk("Available = 2", list(_av.values()) == [2], _av)
chk("In use = 1", list(_us.values()) == [1], _us)

# ── 2 · la ficha del activo conserva lo guardado ─────────────────────────────
print("")
print("2. La ficha del activo CONSERVA valores que no estan en la lista")
ACT = {"ID": "A9", "Group": "cliente1", "Name": "Taladro", "Category": "Herramientas viejas",
       "Status": "prestado a otra obra", "Condition": "regular antiguo",
       "LocationType": "almacen 2", "LocationRef": "", "PurchaseValue": "900",
       "PurchaseDate": "", "UsefulLifeYears": "5", "NextService": "", "Note": ""}
INV.get_activo = lambda aid: dict(ACT)
INV.list_movimientos = lambda grupo=None, activo_id=None: []
INV.qr_png = lambda aid, scale=6: b""
INV.qr_data = lambda aid: ""
selects.clear()
try:
    inventory_ui._detalle("cliente1", "A9")
except Exception as e:
    print("     (render cortado: %s: %s)" % (type(e).__name__, e))
for etq, campo in (("Category", "Category"), ("Status", "Status"),
                   ("Condition", "Condition"), ("Location (type)", "LocationType")):
    ops, idx = next((v for k, v in selects.items() if k == etq), (None, None))
    chk("%s: el desplegable existe" % etq, ops is not None, sorted(selects))
    if ops is not None:
        chk("%s: preselecciona el valor GUARDADO (%r)" % (etq, ACT[campo]),
            ops[idx] == ACT[campo], "muestra %r" % ops[idx])

# control: un valor que SI esta en la lista sigue preseleccionado donde estaba
ACT2 = dict(ACT, Category="Tool", Status=INV.EN_USO, Condition="fair", LocationType="user")
INV.get_activo = lambda aid: dict(ACT2)
selects.clear()
try:
    inventory_ui._detalle("cliente1", "A9")
except Exception:
    pass
ops, idx = selects.get("Category", (None, None))
chk("CONTROL: un valor de la lista no se duplica y queda seleccionado",
    ops is not None and ops.count("Tool") == 1 and ops[idx] == "Tool", (ops, idx))

# ── 3 · la ficha del articulo del catalogo ───────────────────────────────────
print("")
print("3. La ficha del articulo CONSERVA categoria y unidad")
IT = {"ID": "CAT-1", "Group": "cliente1", "Type": CAT.PRODUCTO, "Name": "Guia",
      "Category": "Repuestos viejos", "Unit": "caja rara", "UnitCost": "10",
      "EstHours": "", "HourlyRate": "", "Active": "SI", "Description": ""}
CAT.get_item = lambda cid: dict(IT)
CAT.categorias = lambda grupo: ["Materials", "Labour", "Equipment"]
selects.clear()
try:
    catalogo_ui._detalle("cliente1", "CAT-1")
except Exception as e:
    print("     (render cortado: %s: %s)" % (type(e).__name__, e))
for etq, campo in (("Category", "Category"), ("Unit", "Unit")):
    ops, idx = selects.get(etq, (None, None))
    chk("%s: el desplegable existe" % etq, ops is not None, sorted(selects))
    if ops is not None:
        chk("%s: preselecciona el valor GUARDADO (%r)" % (etq, IT[campo]),
            ops[idx] == IT[campo], "muestra %r" % ops[idx])

print("")
if not ok:
    print("FALLO - v487 smoke")
    sys.exit(1)
print("TODO OK - v487 smoke")
