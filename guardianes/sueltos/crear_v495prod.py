# -*- coding: utf-8 -*-
"""Datos de prueba para v495: un cliente y una factura marcados «ZZ PRUEBA v495»."""
import datetime as dt
import io
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(sys.argv[0]))
os.chdir("C:/Users/diego/P1/survey_app")
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import streamlit as st  # noqa: E402

G = "cliente1"
st.session_state["auth"] = {"usuario": "Admin2", "rol": "administrator", "nombre": "Bobo", "grupo": G}
from core import clientes, clock, invoices  # noqa: E402

print("antes:", len(clientes.list_clientes(G)), "clientes ·", len(invoices.list_facturas(G)), "facturas")
ok, cid = clientes.create_cliente(G, "ZZ PRUEBA v495 Cliente", email="zzprueba-v495@example.com")
print("cliente:", ok, cid)
hoy = clock.today(G)
ok, fid = invoices.create_factura(
    G, cid, "ZZ PRUEBA v495 Cliente",
    [{"concepto": "ZZ PRUEBA v495 · Servicio de prueba", "importe": 100.00, "proyecto_id": ""}],
    impuesto_pct=10, fecha=hoy.isoformat(), vencimiento=(hoy + dt.timedelta(days=14)).isoformat(),
    nota="ZZ PRUEBA v495 - borrar", creado_por="Admin2")
print("factura:", ok, fid)
invoices._invalidate()
f = invoices.get_factura(fid)
print({k: f.get(k) for k in ("ID", "Number", "Date", "Subtotal", "Tax", "Total", "Collected", "Status")})
io.open(os.path.join(AQUI, "creado_v495prod.json"), "w", encoding="utf-8").write(
    json.dumps({"cliente": cid, "factura": fid, "numero": f.get("Number")}))
