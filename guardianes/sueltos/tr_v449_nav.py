# -*- coding: utf-8 -*-
"""v449: los DISPLAYS de la navegación, que estaban a medio traducir.

⚠️ Cada entrada es **(ID, display)** (v232). Se traduce SOLO el segundo: el ID lleva
emoji porque ES el identificador — lo comparan los `_seccion_*` con `sub ==` y lo
usan los deep-links (`_ir_a`, `_admin_nav_pending`, `owner_sec`). Tocarlo dejaría la
rama muerta y la navegación rota **sin dar ningún error** (el fallo de v441 en corte
de rieles, y el de v303 con los «→ Ir a»).

Las claves de sección de nivel 1 (`"planificacion"`, `"finanzas"`…) tampoco: son la
clave de estado que enruta `render_admin_content`.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
F = Path(r"C:\Users\diego\P1\survey_app\core\home_ui.py")

# (viejo, nuevo) — solo el DISPLAY, nunca el ID
C = [
    # nivel 1 · admin
    ('":material/schedule: Fichaje"', '":material/schedule: Timeclock"'),
    ('":material/calendar_month: Planificación"',
     '":material/calendar_month: Planning"'),
    ('":material/payments: Finanzas"', '":material/payments: Finance"'),
    ('":material/inventory_2: Inventario"', '":material/inventory_2: Inventory"'),
    ('":material/build: Herramientas"', '":material/build: Tools"'),
    ('":material/contacts: Contactos"', '":material/contacts: Contacts"'),
    # nivel 1 · campo
    ('":material/payments: Mis colillas"', '":material/payments: My payslips"'),
    # nivel 1 · propietario
    ('":material/shield_person: Administración"',
     '":material/shield_person: Administration"'),
    # nivel 2 · proyectos
    ('":material/account_tree: Agrupaciones"', '":material/account_tree: Groupings"'),
    ('":material/business: Localizaciones"', '":material/business: Locations"'),
    # nivel 2 · finanzas
    ('":material/insights: Resumen"', '":material/insights: Summary"'),
    ('":material/receipt_long: Gastos"', '":material/receipt_long: Expenses"'),
    ('":material/receipt: Facturas"', '":material/receipt: Invoices"'),
    ('":material/trending_up: Rentabilidad"',
     '":material/trending_up: Profitability"'),
    ('":material/request_quote: Cotizaciones"', '":material/request_quote: Quotes"'),
    ('":material/sell: Catálogo"', '":material/sell: Catalogue"'),
    # nivel 2 · herramientas
    ('":material/apps: Inicio"', '":material/apps: Home"'),
    ('":material/straighten: Plomada"', '":material/straighten: Plumb line"'),
    # nivel 2 · propietario
    ('":material/dashboard: Resumen"', '":material/dashboard: Summary"'),
    ('":material/business: Grupos"', '":material/business: Groups"'),
    ('":material/menu_book: Manuales"', '":material/menu_book: Manuals"'),
]

src = F.read_text(encoding="utf-8")
for viejo, nuevo in C:
    n = src.count(viejo)
    if n < 1:
        print(f"  ⚠️ 0 de {viejo[:56]!r}")
        continue
    src = src.replace(viejo, nuevo)
    print(f"  OK  {n}x {viejo[:56]}")
F.write_text(src, encoding="utf-8")
