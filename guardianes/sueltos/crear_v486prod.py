# -*- coding: utf-8 -*-
# =====================================================================
# HISTORICO - NO SE PUEDE EJECUTAR (marcado el 20/09/2026)
#
# Apunta al scratchpad temporal de la sesion 1734b676..., que ya no existe,
# y ademas opera sobre ficheros intermedios de aquella tanda que tampoco
# existen: era una transformacion de un solo uso, ya aplicada.
#
# Se conserva como RASTRO de como se hizo aquel cambio, no como herramienta.
# Arreglarle la ruta no lo haria funcionar: lo que leia ya no esta.
# =====================================================================
"""Siembra en cliente1 las filas que ejercitan las 3 tablas de v486 en PRODUCCION.

Cada tabla lleva una fila CON valor y otra SIN el: la vacia es la prueba, la llena es el
CONTROL de que la tabla pinta (un vacio solo vale si al lado se ve una cifra, trampa n12).
Todo lleva «ZZ PRUEBA v486» y los IDs creados se guardan para borrarlos despues.
"""
import io
import json
import os
import sys

os.chdir("C:/Users/diego/P1/survey_app")
sys.path.insert(0, ".")

import streamlit as st  # noqa: E402

GRUPO = "cliente1"
# ⚠️ sesion simulada: sin grupo, `sheet_id_para` resuelve al MAESTRO y no al libro de
# cliente1 (v359), y el rol va en INGLES (v469).
st.session_state["auth"] = {"usuario": "zzprueba", "rol": "administrator",
                            "nombre": "ZZ Prueba", "grupo": GRUPO}

from core import catalogo, inventory as INV, payroll, timeclock  # noqa: E402

AQUI = r"C:\Users\diego\AppData\Local\Temp\claude\C--Users-diego\1734b676-4bc1-41b7-b6b7-689294f44640\scratchpad"
creado = {"Catalogue": [], "Payroll": [], "Assets": [], "AssetMovements": []}

# ── 1 · catalogo: servicio (con horas) + producto (sin horas) ─────────────────
ok, cid = catalogo.crear(GRUPO, "ZZ PRUEBA v486 servicio", tipo=catalogo.SERVICIO,
                         horas_est=6.5, tarifa_hora=95, unidad="hour",
                         categoria="Labour", creado_por="zzprueba")
print("catalogo servicio:", ok, cid)
if ok:
    creado["Catalogue"].append(cid)
ok, cid = catalogo.crear(GRUPO, "ZZ PRUEBA v486 producto", tipo=catalogo.PRODUCTO,
                         costo_unit=310, unidad="unit", categoria="Materials",
                         creado_por="zzprueba")
print("catalogo producto:", ok, cid)
if ok:
    creado["Catalogue"].append(cid)

# ── 2 · nominas: una CON tarifa y otra SIN ella ───────────────────────────────
# ⚠️ `generar` no puede crear la de sin tarifa: v346 la salta a proposito. Asi que se
# anaden las dos filas alineadas por NOMBRE a la cabecera real de la hoja, leida fresca
# (las filas se escriben por POSICION, v363).
w, err = payroll._ws()
if err:
    raise SystemExit("payroll: %s" % err)
cab = w.row_values(1)
ahora = timeclock.clock.now(GRUPO).strftime("%Y-%m-%d %H:%M") if hasattr(timeclock, "clock") else ""
for nid, usr, nom, horas, rate, base, net, estado in (
        ("NOM-9901", "zzprueba_a", "ZZ Prueba A", 76, 42.5, 3230, 2800, "issued"),
        ("NOM-9902", "zzprueba_b", "ZZ Prueba B", 40, "", 1200, 1050, "paid")):
    d = {"ID": nid, "Group": GRUPO, "User": usr, "Name": nom,
         "PeriodFrom": "2026-08-01", "PeriodTo": "2026-08-14", "Hours": str(horas),
         "HourlyRate": str(rate), "Base": str(base), "ConceptsJSON": "[]", "Net": str(net),
         "PaymentDate": "", "Status": estado, "Note": "ZZ PRUEBA v486",
         "CreatedBy": "zzprueba", "Created": ahora}
    faltan = [k for k in d if k not in cab]
    if faltan:
        raise SystemExit("columnas que la hoja no tiene: %s" % faltan)
    w.append_row([d.get(h, "") for h in cab], value_input_option="RAW")
    creado["Payroll"].append(nid)
    print("nomina:", nid, "rate=%r" % rate)
payroll._invalidate()

# ── 3 · inventario: un activo + dos mantenimientos (con y sin costo) ──────────
ok, aid = INV.create_activo(GRUPO, "ZZ PRUEBA v486 taladro", categoria="Tools",
                           marca="Hilti", modelo="TE-2", fecha_compra="2025-03-01",
                           valor_compra=900, vida_util=5, creado_por="zzprueba")
print("activo:", ok, aid)
if not ok:
    raise SystemExit("no se creo el activo")
creado["Assets"].append(aid)
print("mant con costo:", INV.mantenimiento(aid, GRUPO, costo=128.5,
                                           nota="ZZ PRUEBA v486 con costo",
                                           creado_por="zzprueba"))
print("mant sin costo:", INV.mantenimiento(aid, GRUPO, costo="",
                                           nota="ZZ PRUEBA v486 sin costo",
                                           creado_por="zzprueba"))
INV._invalidate()
for m in INV.list_movimientos(GRUPO, aid):
    creado["AssetMovements"].append(str(m.get("ID", "")))

with io.open(os.path.join(AQUI, "creado_v486prod.json"), "w", encoding="utf-8") as f:
    json.dump(creado, f, indent=1)
print("")
print("CREADO:", json.dumps(creado))
