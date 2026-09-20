"""SIMULACIÓN etapa A — el equipo, los clientes y el catálogo.

El usuario autorizó simular datos: todo lo del grupo `cliente1` es de prueba.
Objetivo: que las pantallas tengan VOLUMEN y VARIEDAD suficientes para juzgarlas
y para que salgan los fallos que solo aparecen con datos reales.

Casos límite metidos a propósito (no son adorno, son la prueba):
  · **Homónimos**: dos personas distintas con el mismo Nombre → ejercita
    `auth.etiqueta_usuarios` (el fallo de v151/v319/v348).
  · **Apóstrofo y acentos** en los nombres → escapes de HTML/markdown.
  · **Alguien SIN tarifa** → el aviso de v325 («falta tarifa» vs «de baja»).
  · **Un servicio y un producto con el mismo nombre** en el catálogo.
"""
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st
st.session_state["auth"] = {"usuario": "Bobo", "grupo": "cliente1", "rol": "administrador"}

from core import auth, clientes as C, catalogo as CAT      # noqa: E402

G = "cliente1"
PW = "prueba2026"          # ⚠️ contraseña de PRUEBA, la misma para todas las cuentas simuladas

# ── 1) El equipo ────────────────────────────────────────────────
# (usuario, nombre, rol, tarifa, email)   tarifa None = a propósito sin tarifa
EQUIPO = [
    ("jlopez",  "Javier López",   "campo",         42.0, "jlopez@copextest.local"),
    ("mchen",   "Mei Chen",       "campo",         38.0, "mchen@copextest.local"),
    ("mchen2",  "Mei Chen",       "campo",         45.0, "mchen2@copextest.local"),  # homónimo
    ("tobrien", "Tom O'Brien",    "campo",         36.0, "tobrien@copextest.local"),  # apóstrofo
    ("apatel",  "Anjali Patel",   "campo",         40.0, "apatel@copextest.local"),
    ("nsanchez", "Nuria Sánchez", "campo",         None, "nsanchez@copextest.local"),  # sin tarifa
    ("dmoreno", "Diego Moreno",   "administrador", 55.0, "dmoreno@copextest.local"),
]

print("== A1. equipo ==")
existentes = {u.get("Usuario") for u in auth.list_users(G)}
for usr, nom, rol, tar, mail in EQUIPO:
    if usr in existentes:
        print(f"   {usr:<9} ya existe, se salta")
        continue
    ok, msg = auth.add_user(usr, PW, rol, nom, G, True)
    print(f"   {usr:<9} {nom:<15} {rol:<14} {'OK' if ok else '⚠️ ' + msg}")
    if not ok:
        continue
    if tar is not None:
        auth.set_rate(usr, tar)
    auth.set_contact(usr, email=mail, telegram="")
    time.sleep(0.4)                     # el techo es 60 escrituras/min

# ── 2) Los clientes ─────────────────────────────────────────────
CLIENTES = [
    ("Meriton Apartments",       "Sarah Whitfield", "+61 2 9000 1122", "projects@meriton.test",
     "528 Kent St, Sydney NSW 2000", "Torres residenciales. Paga a 30 días."),
    ("Stockland Retail",         "Peter Nguyen",    "+61 2 9000 3344", "facilities@stockland.test",
     "133 Castlereagh St, Sydney NSW 2000", "Centros comerciales. Trabajo nocturno."),
    ("NSW Health Infrastructure", "Dr. Alan Reid",  "+61 2 9000 5566", "lifts@health.test",
     "1 Reserve Rd, St Leonards NSW 2065", "Hospitales. Exige White Card y police check."),
    ("Bespoke Lifts Pty Ltd",    "Marco Ferretti",  "+61 2 9000 7788", "marco@bespokelifts.test",
     "12 Hume Hwy, Chullora NSW 2190", "Subcontratista. Facturamos por horas."),
]

print("\n== A2. clientes ==")
ya = {str(c.get("Nombre", "")).casefold() for c in C.list_clientes(G, incluir_inactivos=True)}
cli_ids = {}
for nom, cont, tel, mail, dirn, notas in CLIENTES:
    if nom.casefold() in ya:
        print(f"   {nom:<26} ya existe")
        continue
    ok, msg = C.create_cliente(G, nom, cont, tel, mail, dirn, notas, "dmoreno")
    print(f"   {nom:<26} {'OK ' + str(msg) if ok else '⚠️ ' + str(msg)}")
    time.sleep(0.4)
for c in C.list_clientes(G, incluir_inactivos=True):
    cli_ids[str(c.get("Nombre", ""))] = str(c.get("ClienteID", ""))
print("   IDs:", cli_ids)

# ── 3) El catálogo ──────────────────────────────────────────────
# producto  → costo_unit
# servicio  → horas_est × tarifa_hora
ITEMS = [
    ("producto", "Riel guía T89/B (5 m)",        "riel",     185.50, None, None, "unidad", "Rieles"),
    ("producto", "Riel guía T127-2/B (5 m)",     "riel",     264.00, None, None, "unidad", "Rieles"),
    ("producto", "Buffer hidráulico 1.0 m/s",    "buffer",   420.00, None, None, "unidad", "Amortiguación"),
    ("producto", "Operador de puerta VVVF",      "operador", 1850.00, None, None, "unidad", "Puertas"),
    ("producto", "Puerta de rellano 900×2100",   "puerta",   1240.00, None, None, "unidad", "Puertas"),
    ("producto", "Cuadro de maniobra 8 paradas", "cuadro",   3600.00, None, None, "unidad", "Control"),
    ("producto", "Cable de tracción 8 mm (m)",   "cable",     14.80, None, None, "metro",  "Tracción"),
    ("producto", "Kit de anclajes por parada",   "anclaje",   96.00, None, None, "kit",    "Fijaciones"),
    # servicios: horas estimadas × tarifa
    ("servicio", "Instalación mecánica",         "inst",     None, 120.0, 42.0, "servicio", "Mano de obra"),
    ("servicio", "Montaje de puertas",           "puertas",  None,  36.0, 40.0, "servicio", "Mano de obra"),
    ("servicio", "Puesta en marcha y ajuste",    "commis",   None,  24.0, 55.0, "servicio", "Mano de obra"),
    ("servicio", "Survey y replanteo",           "survey",   None,   8.0, 55.0, "servicio", "Ingeniería"),
    ("servicio", "Desmontaje (ripout)",          "ripout",   None,  40.0, 38.0, "servicio", "Mano de obra"),
]

print("\n== A3. catálogo ==")
yai = {str(i.get("Nombre", "")).casefold() for i in CAT.list_items(G, incluir_inactivos=True)}
for tipo, nombre, _k, costo, horas, tarifa, unidad, categoria in ITEMS:
    if nombre.casefold() in yai:
        print(f"   {nombre:<30} ya existe")
        continue
    ok, msg = CAT.crear(G, nombre, tipo,
                        costo_unit=costo if costo is not None else "",
                        horas_est=horas if horas is not None else "",
                        tarifa_hora=tarifa if tarifa is not None else "",
                        unidad=unidad, categoria=categoria, creado_por="dmoreno")
    base = CAT.costo_de({"Tipo": tipo, "CostoUnit": costo or "",
                         "HorasEst": horas or "", "TarifaHora": tarifa or ""}, 1)
    print(f"   {tipo:<9} {nombre:<30} costo/u ${base:>9,.2f}  {'OK' if ok else '⚠️ ' + str(msg)}")
    time.sleep(0.4)

print("\n== resumen ==")
print(f"   usuarios : {len(auth.list_users(G))}")
print(f"   clientes : {len(C.list_clientes(G, incluir_inactivos=True))}")
print(f"   catálogo : {len(CAT.list_items(G, incluir_inactivos=True))}")
