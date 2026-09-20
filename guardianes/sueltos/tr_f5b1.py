# -*- coding: utf-8 -*-
"""F5b, tanda 1: `orders.py`, `catalogo.py`, `clientes.py`.

Los tres estaban limpios de colisiones (pre_i18n), así que entra `t` directo.
⚠️ El import se inserta con un ancla ÚNICA y comprobando que no esté ya: correr el
mismo parche dos veces duplicó un import en v445.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

MSG = "Google Sheets no está configurado."
MSG_EN = 't("Google Sheets is not configured.")'

CAMBIOS = [
    # ── orders.py ──
    ("core/orders.py", f'"{MSG}"', MSG_EN, 4),
    ("core/orders.py", '"El valor de la orden debe ser mayor que 0."',
     't("The order value must be greater than 0.")', 1),
    ("core/orders.py", '"Indica el proveedor."', 't("Enter the supplier.")', 1),
    ("core/orders.py", 'f"Error guardando la orden: {e}"',
     'f"{t(\'Error saving the order\')}: {e}"', 1),
    ("core/orders.py", '"El valor recibido debe ser mayor que 0."',
     't("The received value must be greater than 0.")', 1),
    ("core/orders.py",
     '"Ya se recibió: no se puede cancelar (elimina su recibo si fue un error)."',
     't("Already received: it cannot be cancelled '
     '(delete its receipt if it was a mistake).")', 1),

    # ── catalogo.py ──
    ("core/catalogo.py", f'"{MSG}"', MSG_EN, 2),
    ("core/catalogo.py", '"Ponle un nombre al artículo."',
     't("Give the item a name.")', 1),
    ("core/catalogo.py",
     '"Un servicio necesita horas estimadas y tarifa/hora mayores que 0."',
     't("A service needs estimated hours and an hourly rate greater than 0.")', 1),
    ("core/catalogo.py", '"El costo unitario debe ser mayor que 0."',
     't("The unit cost must be greater than 0.")', 1),
    ("core/catalogo.py", '"Artículo no encontrado."', 't("Item not found.")', 1),
    ("core/catalogo.py", '"Artículo actualizado."', 't("Item updated.")', 1),

    # ── clientes.py ──
    ("core/clientes.py", f'"{MSG}"', MSG_EN, 1),
    ("core/clientes.py", '"El nombre del cliente es obligatorio."',
     't("The client name is required.")', 1),
    ("core/clientes.py",
     '"Ya existe una ficha de cliente con ese nombre en el grupo."',
     't("A client with that name already exists in this group.")', 1),
    ("core/clientes.py", '"Cliente no encontrado."', 't("Client not found.")', 1),
    ("core/clientes.py", '"Cliente actualizado."', 't("Client updated.")', 1),
]


def _import(rel, ancla):
    f = R / rel
    src = f.read_text(encoding="utf-8")
    if "from core.i18n import t" in src:
        print(f"  ·   {rel}: ya importa `t`")
        return
    if src.count(ancla) != 1:
        print(f"  ⚠️ {rel}: ancla del import ambigua ({src.count(ancla)})")
        return
    f.write_text(src.replace(ancla, f"from core.i18n import t\n{ancla}", 1),
                 encoding="utf-8")
    print(f"  OK  {rel}: import añadido")


for rel, ancla in (("core/orders.py", "logger = logging.getLogger(__name__)"),
                   ("core/catalogo.py", "logger = logging.getLogger(__name__)"),
                   ("core/clientes.py", "logger = logging.getLogger(__name__)")):
    _import(rel, ancla)

for rel, viejo, nuevo, n_esp in CAMBIOS:
    f = R / rel
    src = f.read_text(encoding="utf-8")
    n = src.count(viejo)
    if n != n_esp:
        print(f"  ⚠️ {rel}: esperaba {n_esp} y hay {n} de {viejo[:44]!r} — NO se toca")
        continue
    f.write_text(src.replace(viejo, nuevo), encoding="utf-8")
    print(f"  OK  {rel}: {n}x {viejo[:52]}")
