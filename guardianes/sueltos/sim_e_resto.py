"""SIMULACIÓN etapa E — cotizaciones, ganancia por rubro e inventario.

Cierra el escenario. Casos límite:
  ⚠️ Cotizaciones en los 4 estados (borrador · enviada · aceptada · rechazada), y
     una **VENCIDA** por fecha de validez (estado derivado, v353).
  ⚠️ **Aceptar una cotización** → crea el proyecto. Es la prueba de punta a punta
     del arreglo de v363: ese camino llamaba a `create_project`, que estaba MUERTO.
  ⚠️ Obras con ganancia por RUBRO (v360) mezcladas con obras al margen viejo, para
     que la pantalla de Rentabilidad tenga que distinguir los dos modelos.
  ⚠️ Una persona CON horas y SIN ganancia puesta → se factura a costo y la app
     tiene que nombrarla (`sin_ganancia`).
  ⚠️ Inventario: activos en bodega, en obra y uno EN MANTENIMIENTO, más uno dado
     de baja (para la casilla «ver también los de baja», v340).
"""
import sys
import time
from datetime import date, timedelta

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st
st.session_state["auth"] = {"usuario": "Bobo", "grupo": "cliente1", "rol": "administrador"}

from core import (projects as P, clientes as C, catalogo as CAT,     # noqa: E402
                  quotes as Q, inventory as INV)

G = "cliente1"
CLI = {str(c.get("Nombre", "")): str(c.get("ID", ""))
       for c in C.list_clientes(G, incluir_inactivos=True)}
ITEMS = {str(i.get("Nombre", "")): i for i in CAT.list_items(G)}
PRJ = {str(p.get("Nombre", "")): str(p.get("ID", ""))
       for p in P.list_projects(G, incluir_archivados=True)}


def pid(t):
    return next(i for n, i in PRJ.items() if t.lower() in n.lower())


def item(t):
    return next(v for n, v in ITEMS.items() if t.lower() in n.lower())


# ── E1. cotizaciones ────────────────────────────────────────────
print("== E1. cotizaciones ==")
COTS = [
    # (cliente, [(artículo, cantidad, ganancia $)], validez, estado final)
    ("Meriton Apartments",
     [("Instalación mecánica", 2, 2400), ("Riel guía T89", 24, 900),
      ("Operador de puerta VVVF", 2, 700)], date(2026, 9, 30), "enviada"),
    ("Stockland Retail",
     [("Desmontaje (ripout)", 1, 800), ("Survey y replanteo", 1, 200)],
     date(2026, 9, 15), "aceptada"),
    ("NSW Health Infrastructure",
     [("Puesta en marcha", 2, 900), ("Cuadro de maniobra", 1, 1100)],
     date(2026, 9, 20), "rechazada"),
    ("Bespoke Lifts Pty Ltd",
     [("Montaje de puertas", 3, 450)], date(2026, 10, 10), "borrador"),
    # ⚠️ VENCIDA: la validez ya pasó → el estado se DERIVA, no se guarda
    ("Meriton Apartments",
     [("Buffer hidráulico", 4, 300)], date(2026, 8, 1), "enviada"),
]
creadas = []
for cliente, lineas_def, validez, estado in COTS:
    lineas = []
    for art, cant, gan in lineas_def:
        try:
            lineas.append(Q.linea_de(item(art), cant, ganancia=gan))
        except StopIteration:
            print(f"      ⚠️ sin artículo «{art}», se salta")
    if not lineas:
        continue
    ok, res = Q.crear(G, CLI.get(cliente, ""), cliente, lineas, impuesto_pct=10.0,
                      validez=validez, creado_por="dmoreno")
    tot = Q.totales(lineas, 10.0)
    print(f"   {cliente[:24]:<25} {len(lineas)} líneas · total ${tot.get('total', 0):>10,.2f} "
          f"→ {'OK ' + str(res) if ok else '⚠️ ' + str(res)}")
    time.sleep(0.5)
    if ok:
        creadas.append((str(res), estado, cliente))

for cid, estado, cliente in creadas:
    if estado == "borrador":
        continue
    ok, msg = Q.set_estado(cid, "enviada")
    time.sleep(0.4)
    if estado in ("aceptada", "rechazada"):
        ok, msg = Q.set_estado(cid, estado)
        time.sleep(0.4)
    print(f"   {cid} → {estado}")

# ⚠️ aceptar = crear el proyecto. ESTE es el camino que v363 resucitó.
acept = [c for c in creadas if c[1] == "aceptada"]
if acept:
    cid = acept[0][0]
    ok, res = Q.aceptar_y_crear_proyecto(
        cid, nombre="Stockland Bankstown — Ripout", tipo="Ripout",
        fecha_inicio=date(2026, 9, 15), ubicacion="Bankstown NSW", creado_por="dmoreno")
    print(f"\n   ⚠️ aceptar {cid} → crear proyecto: {'OK ' + str(res) if ok else '⚠️ ' + str(res)}")
    time.sleep(0.6)

# ── E2. ganancia por rubro (v360) en algunas obras ──────────────
print("\n== E2. ganancia por hora (modelo por rubro) ==")
# ⚠️ A propósito NO se le pone a todo el mundo: en Torre A falta `apatel`, así que
#    su trabajo se factura A COSTO y la pantalla tiene que decirlo (`sin_ganancia`).
GANANCIAS = {
    "Torre A": {"jlopez": 18, "mchen": 15},                 # falta apatel → a costo
    "Torre B": {"jlopez": 18, "tobrien": 14},
    "RNSH Lift 4": {"campo1": 16, "apatel": 15, "mchen": 15},
}
for nom, mapa in GANANCIAS.items():
    p = pid(nom)
    ok, msg = P.set_ganancia_hora(p, mapa)
    print(f"   {nom:<16} {mapa} → {msg}")
    time.sleep(0.5)
P._invalidate()

# ── E3. inventario ──────────────────────────────────────────────
print("\n== E3. inventario ==")
ACTIVOS = [
    ("Taladro percutor Hilti TE 30", "Herramienta", "Hilti", "TE 30-AVR", "SN-8841",
     "2024-03-12", 1450.00, 5, "bodega", ""),
    ("Andamio modular 6 m", "Andamio", "Layher", "Allround", "SN-2210",
     "2023-08-01", 3800.00, 10, "proyecto", "Torre A"),
    ("Polipasto eléctrico 1 t", "Elevación", "Yale", "CPE 1000", "SN-5533",
     "2025-01-20", 2600.00, 8, "proyecto", "RNSH Lift 4"),
    ("Nivel láser Leica Lino", "Instrumento", "Leica", "L2P5G", "SN-7712",
     "2025-06-05", 890.00, 5, "bodega", ""),
    ("Generador 5 kVA", "Energía", "Honda", "EU50i", "SN-3390",
     "2022-11-11", 4200.00, 8, "mantenimiento", ""),
    ("Camioneta Hilux (vieja)", "Vehículo", "Toyota", "Hilux 2016", "SN-0001",
     "2016-05-01", 32000.00, 10, "bodega", ""),      # se dará de BAJA
]
ids = {}
for nom, cat, marca, mod, serie, compra, valor, vida, ubic, ref in ACTIVOS:
    ok, res = INV.create_activo(G, nom, categoria=cat, marca=marca, modelo=mod,
                                serie=serie, fecha_compra=compra, valor_compra=valor,
                                vida_util=vida, creado_por="dmoreno")
    print(f"   {nom[:30]:<31} ${valor:>9,.2f}  {'OK ' + str(res) if ok else '⚠️ ' + str(res)}")
    time.sleep(0.5)
    if ok:
        ids[nom] = (str(res), ubic, ref)

for nom, (aid, ubic, ref) in ids.items():
    if ubic == "proyecto" and ref:
        ok, msg = INV.salida(aid, G, hacia_tipo="proyecto", hacia_ref=pid(ref),
                             nota="Asignado a obra", creado_por="dmoreno")
        print(f"   → {nom[:26]:<27} a obra {ref}: {msg}")
        time.sleep(0.5)
    elif ubic == "mantenimiento":
        ok, msg = INV.mantenimiento(aid, G, costo=340, en_mant=True,
                                    nota="Cambio de aceite y filtros", creado_por="dmoreno")
        print(f"   → {nom[:26]:<27} a mantenimiento: {msg}")
        time.sleep(0.5)

if "Camioneta Hilux (vieja)" in ids:
    aid = ids["Camioneta Hilux (vieja)"][0]
    ok, msg = INV.dar_de_baja(aid, G, motivo="Vendida", creado_por="dmoreno")
    print(f"   → baja de la Hilux: {msg}")

print("\n== resumen ==")
print(f"   cotizaciones: {len(Q.list_cotizaciones(G))}")
print(f"   activos     : {len(INV.list_activos(G))} activos "
      f"+ {len(INV.list_activos(G, incluir_baja=True)) - len(INV.list_activos(G))} de baja")
print(f"   proyectos   : {len(P.list_projects(G, incluir_archivados=True))}")
