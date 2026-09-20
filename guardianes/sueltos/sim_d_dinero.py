"""SIMULACIÓN etapa D — el dinero: compras, órdenes, facturas y nóminas.

Los indicadores del resumen financiero (v317) y el P&L (v309) son ocho cifras que
hoy salen todas en cero. Sin dinero real no se puede juzgar ninguna de esas
pantallas, ni la conciliación de v313.

CASOS LÍMITE metidos a propósito, cada uno reproduce un fallo ya documentado:
  ⚠️ factura VENCIDA con un ABONO PARCIAL → el fallo de v345: `estado_cobro` daba
     «parcial» y la sacaba de «vencida» para siempre, así que ese saldo no lo veía
     ni el indicador rojo ni el P&L. Aquí tiene que salir VENCIDA.
  ⚠️ orden de compra PENDIENTE que deja la obra sobre presupuesto **sin haber
     gastado** → el `over_comp` de v343, que es el aviso que llega a tiempo.
  ⚠️ orden ATRASADA (fecha esperada pasada) → obra parada esperando material.
  ⚠️ una obra con trabajo hecho y SIN facturar → indicador «Sin facturar» (v317).
  ⚠️ las nóminas se generan hasta el 16/08 y las horas llegan al 18 → quedan días
     trabajados sin nómina, que es el indicador «Horas sin nómina».
  ⚠️ `nsanchez` no tiene tarifa → v346: NO se le emite colilla de $0, se avisa.
"""
import sys
import time
from datetime import date, timedelta

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st
st.session_state["auth"] = {"usuario": "Bobo", "grupo": "cliente1", "rol": "administrador"}

from core import (projects as P, clientes as C, expenses as E,      # noqa: E402
                  orders as O, invoices as I, payroll as PR)

G = "cliente1"
CLI = {str(c.get("Nombre", "")): str(c.get("ID", ""))
       for c in C.list_clientes(G, incluir_inactivos=True)}
PRJ = {str(p.get("Nombre", "")): str(p.get("ID", ""))
       for p in P.list_projects(G, incluir_archivados=True)}


def pid(nombre_parcial):
    for n, i in PRJ.items():
        if nombre_parcial.lower() in n.lower():
            return i
    raise KeyError(nombre_parcial)


# ── D1. compras (recibos de material) ───────────────────────────
COMPRAS = [
    ("Torre A", 4820.00, "Materiales", "Schindler Parts AU", "Rieles y anclajes T89", "2026-08-04"),
    ("Torre A", 1240.00, "Materiales", "Liftco Supplies", "Puerta de rellano planta 3", "2026-08-11"),
    ("Torre B", 3600.00, "Materiales", "Schindler Parts AU", "Cuadro de maniobra", "2026-08-10"),
    ("Torre C", 980.00, "Materiales", "Liftco Supplies", "Kit de anclajes ×10", "2026-08-12"),
    ("Ripout", 450.00, "Herramientas", "Bunnings Trade", "Discos de corte y consumibles", "2026-07-28"),
    ("Ripout", 1850.00, "Transporte", "Metro Skips", "Retirada de chatarra", "2026-08-06"),
    ("RNSH Lift 4", 7400.00, "Materiales", "Schindler Parts AU", "Operadores VVVF ×4", "2026-06-15"),
    ("RNSH Lift 4", 2100.00, "Materiales", "Liftco Supplies", "Cable de tracción 140 m", "2026-07-09"),
    ("RNSH Lift 4", 620.00, "Otros", "Sydney Permits", "Permiso de trabajo hospital", "2026-05-12"),
    ("Delivery Chullora", 380.00, "Transporte", "Metro Freight", "Entrega a taller", "2026-07-29"),
    ("Rhodes", 0.0, None, None, None, None),          # marcador: sin compras
]

print("== D1. compras ==")
ya = {(str(g.get("ProyectoID")), str(g.get("Descripcion"))) for g in (E.list_expenses(G) or [])} \
    if hasattr(E, "list_expenses") else set()
for nom, valor, cat, prov, desc, fecha in COMPRAS:
    if not valor:
        continue
    p = pid(nom)
    if (p, desc) in ya:
        print(f"   {nom:<18} ya existe")
        continue
    ok, msg = E.add(p, G, valor, categoria=cat, proveedor=prov,
                    descripcion=desc, creado_por="dmoreno", fecha=fecha)
    print(f"   {nom:<18} ${valor:>9,.2f}  {cat:<12} {'OK' if ok else '⚠️ ' + str(msg)}")
    time.sleep(0.4)

# ── D2. órdenes de compra (dinero COMPROMETIDO) ─────────────────
print("\n== D2. órdenes de compra ==")
ORDENES = [
    # (obra, proveedor, valor, descripción, fecha esperada, ¿recibir?)
    ("Torre B", "Schindler Parts AU", 12400.00, "Puertas de rellano ×8", "2026-09-05", False),
    ("Torre C", "Schindler Parts AU", 9800.00, "Operadores VVVF ×8", "2026-09-20", False),
    # ⚠️ ATRASADA: la fecha esperada ya pasó y sigue pendiente
    ("Ripout", "Metro Skips", 900.00, "Segundo contenedor", "2026-08-10", False),
    # recibida → crea su gasto sola
    ("Torre A", "Liftco Supplies", 2650.00, "Cable de tracción 180 m", "2026-08-08", True),
]
for nom, prov, valor, desc, esperada, recibir in ORDENES:
    ok, res = O.crear(pid(nom), G, prov, valor, descripcion=desc,
                      fecha_esperada=esperada, creado_por="dmoreno")
    print(f"   {nom:<18} ${valor:>9,.2f}  {desc[:28]:<29} {'OK ' + str(res) if ok else '⚠️ ' + str(res)}")
    time.sleep(0.4)
    if ok and recibir:
        ok2, msg2 = O.marcar_recibida(str(res), creado_por="dmoreno")
        print(f"      recibida → {msg2}")
        time.sleep(0.4)

# ── D3. facturas ────────────────────────────────────────────────
print("\n== D3. facturas ==")
HOY = date(2026, 8, 18)
FACTURAS = [
    # (cliente, obra, concepto, importe, fecha, vencimiento, cobrado)
    ("Meriton Apartments", "Torre A", "Avance de obra 60% — Torre A", 18500.00,
     "2026-08-01", "2026-08-31", 18500.00),                      # pagada
    ("Meriton Apartments", "Torre B", "Avance de obra 40% — Torre B", 12000.00,
     "2026-08-12", "2026-09-11", 0.0),                            # emitida, al día
    # ⚠️ VENCIDA CON ABONO PARCIAL — el fallo de v345
    ("Stockland Retail", "Ripout", "Desmontaje Wetherill Park", 9800.00,
     "2026-07-05", "2026-08-04", 1500.00),
    # ⚠️ VENCIDA sin ningún abono
    ("NSW Health Infrastructure", "RNSH Lift 4", "Modernización Lift 4 — hito 1", 22000.00,
     "2026-06-20", "2026-07-20", 0.0),
    ("Bespoke Lifts Pty Ltd", "Delivery Chullora", "Entrega y montaje Chullora", 5200.00,
     "2026-07-31", "2026-08-30", 5200.00),                        # pagada
    ("Meriton Apartments", "Rhodes", "Survey y replanteo Rhodes", 1450.00,
     "2026-08-12", "2026-09-11", 700.00),                         # parcial, al día
]
for cliente, obra, concepto, importe, fecha, venc, cobrado in FACTURAS:
    p = pid(obra)
    ok, res = I.create_factura(G, CLI.get(cliente, ""), cliente,
                               [{"concepto": concepto, "importe": importe, "proyecto_id": p}],
                               impuesto_pct=10.0, fecha=fecha, vencimiento=venc,
                               creado_por="dmoreno")
    print(f"   {cliente[:22]:<23} ${importe:>9,.2f}  venc {venc}  "
          f"{'OK ' + str(res) if ok else '⚠️ ' + str(res)}")
    time.sleep(0.4)
    if ok and cobrado > 0:
        ok2, msg2 = I.registrar_cobro(str(res), cobrado, fecha=fecha)
        est = I.estado_cobro(I.get_factura(str(res)))
        print(f"      cobrado ${cobrado:,.2f} → estado «{est}»")
        time.sleep(0.4)

# ── D4. nóminas quincenales ─────────────────────────────────────
print("\n== D4. nóminas (quincenales, AU) ==")
# ⚠️ Se paga hasta el 16/08 y las horas llegan al 18 → quedan días trabajados sin
#    nómina a propósito: es el indicador «Horas sin nómina» del resumen financiero.
QUINCENAS = [("2026-06-22", "2026-07-05"), ("2026-07-06", "2026-07-19"),
             ("2026-07-20", "2026-08-02"), ("2026-08-03", "2026-08-16")]
for desde, hasta in QUINCENAS:
    r = PR.generar(G, desde, hasta, super_pct=11.5, ret_pct=20.0, creado_por="dmoreno")
    print(f"   {desde} → {hasta}: creadas {r.get('creadas')} · omitidas {r.get('omitidas')} "
          f"· sin tarifa {r.get('sin_tarifa')}")
    time.sleep(0.8)

# las dos primeras quincenas se marcan PAGADAS; las dos últimas quedan por pagar
noms = [n for n in PR.list_nominas(G) if str(n.get("PeriodoHasta", "")) <= "2026-07-19"]
print(f"\n   marcando pagadas las 2 primeras quincenas ({len(noms)} colillas)…")
for n in noms:
    PR.marcar_pagada(str(n.get("ID")), fecha=str(n.get("PeriodoHasta")))
    time.sleep(0.35)
print("   hecho")
