# -*- coding: utf-8 -*-
import io, json, os, sys, datetime as dt
os.chdir("C:/Users/diego/P1/survey_app"); sys.path.insert(0, ".")
import streamlit as st
G = "cliente1"
st.session_state["auth"] = {"usuario": "Admin2", "rol": "administrator", "nombre": "ZZ Prueba", "grupo": G}
from core import clientes, invoices, clock
AQUI = os.path.dirname(os.path.abspath(sys.argv[0]))
antes = len(invoices.list_facturas(G))
print("facturas antes:", antes)
ok, cid = clientes.create_cliente(G, "ZZ PRUEBA v488 Cliente", email="zzprueba@example.com")
print("cliente:", ok, cid)
hoy = clock.today(G)
ok, fid = invoices.create_factura(G, cid, "ZZ PRUEBA v488 Cliente",
    [{"concepto": "ZZ PRUEBA v488 · Instalación", "importe": 33.33, "proyecto_id": ""},
     {"concepto": "ZZ PRUEBA v488 · Material", "importe": 33.33, "proyecto_id": ""},
     {"concepto": "ZZ PRUEBA v488 · Extra", "importe": 33.34, "proyecto_id": ""}],
    impuesto_pct=10, fecha=hoy.isoformat(), vencimiento=(hoy + dt.timedelta(days=14)).isoformat(),
    nota="ZZ PRUEBA v488 - borrar", creado_por="Admin2")
print("factura:", ok, fid)
invoices._invalidate()
f = invoices.get_factura(fid)
print({k: f.get(k) for k in ("ID", "Number", "Date", "ExpiryDate", "Subtotal", "Tax", "Total", "Status")})
io.open(os.path.join(AQUI, "creado_v488prod.json"), "w", encoding="utf-8").write(json.dumps({"cliente": cid, "factura": fid}))
