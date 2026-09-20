# -*- coding: utf-8 -*-
"""F5c: los mensajes de backend de los 12 módulos que quedaban.

⚠️ Lo que NO se toca, mirado uno a uno:
  · las CLAVES de `toolruns.HERRAMIENTAS` (`"plomada"`, `"rieles"`, `"buffers"`,
    `"belting"`, `"survey"`): se guardan en la hoja `Calculos` y las compara el
    reabrir-cálculo (v441). Solo se traduce el VALOR, que es lo que se pinta.
  · `credentials.CATALOGO` y los tipos: se guardan en la hoja.
  · `inventory` `"Dado de baja"` es un ESTADO que se escribe; el `"Mano de obra"` de
    `expenses` es una etiqueta de reparto que se pinta.
  · los textos de correo/Telegram de `credentials.notify_expiring` van en idioma
    BASE, sin `t()`: salen de la empresa (regla v436).
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

GS = '"Google Sheets no está configurado."'
GS_EN = 't("Google Sheets is not configured.")'

IMPORTS = ["core/expenses.py", "core/roster.py", "core/inventory.py",
           "core/credentials.py", "core/payroll.py", "core/prestart.py",
           "core/rails.py", "core/plan_data.py", "core/invoices.py",
           "core/manuals.py", "core/toolruns.py"]

CAMBIOS = [
    # ── expenses ──
    ("core/expenses.py", GS, GS_EN, 1),
    ("core/expenses.py", '"El valor del recibo debe ser mayor que 0."',
     't("The receipt value must be greater than 0.")', 1),
    ("core/expenses.py", '"Recibo eliminado."', 't("Receipt deleted.")', 1),

    # ── roster ──
    ("core/roster.py", GS, GS_EN, 1),
    ("core/roster.py", '"El nombre del trabajo es obligatorio."',
     't("The job name is required.")', 1),
    ("core/roster.py", '"Guardado."', 't("Saved.")', 1),
    ("core/roster.py", '"La semana de origen está vacía."',
     't("The source week is empty.")', 1),
    ("core/roster.py", '"Trabajo actualizado."', 't("Job updated.")', 1),
    ("core/roster.py", '"Trabajo eliminado."', 't("Job deleted.")', 1),
    ("core/roster.py", '"Trabajo no encontrado."', 't("Job not found.")', 1),

    # ── inventory ──
    ("core/inventory.py", GS, GS_EN, 1),
    ("core/inventory.py", '"Activo actualizado."', 't("Asset updated.")', 1),
    ("core/inventory.py", '"Activo no encontrado."', 't("Asset not found.")', 1),
    ("core/inventory.py", '"Categoría añadida."', 't("Category added.")', 1),
    ("core/inventory.py", '"Categoría eliminada."', 't("Category deleted.")', 1),
    ("core/inventory.py", '"El nombre del activo es obligatorio."',
     't("The asset name is required.")', 1),
    ("core/inventory.py", '"Entrada (devolución) registrada."',
     't("Return recorded.")', 1),
    ("core/inventory.py", '"Esa categoría ya existe."',
     't("That category already exists.")', 1),
    ("core/inventory.py", '"No se encontró (¿es una por defecto? esas no se quitan)."',
     't("Not found (is it a default one? those cannot be removed).")', 1),
    ("core/inventory.py", '"Nombre vacío."', 't("Empty name.")', 1),

    # ── credentials ──
    ("core/credentials.py", GS, GS_EN, 1),
    ("core/credentials.py", '"Credencial actualizada."', 't("Credential updated.")', 1),
    ("core/credentials.py", '"Credencial eliminada."', 't("Credential deleted.")', 1),
    ("core/credentials.py", '"Credencial no encontrada."',
     't("Credential not found.")', 1),
    ("core/credentials.py", '"El tipo de credencial es obligatorio."',
     't("The credential type is required.")', 1),

    # ── payroll ──
    ("core/payroll.py", GS, GS_EN, 1),
    ("core/payroll.py", '"Nómina actualizada."', 't("Payslip updated.")', 1),
    ("core/payroll.py", '"Nómina anulada."', 't("Payslip voided.")', 1),
    ("core/payroll.py", '"Nómina marcada como pagada."',
     't("Payslip marked as paid.")', 1),
    ("core/payroll.py", '"Nómina no encontrada."', 't("Payslip not found.")', 1),

    # ── prestart ──
    ("core/prestart.py", '"Falta el Pre-Start o el nombre de quien firma."',
     't("The Pre-Start or the signer name is missing.")', 1),
    ("core/prestart.py", '"No se pudo abrir la hoja de pre-starts."',
     't("Could not open the pre-starts sheet.")', 1),

    # ── rails ──
    ("core/rails.py", '"La referencia es obligatoria."',
     't("The reference is required.")', 1),
    ("core/rails.py", '"Riel actualizado."', 't("Rail updated.")', 1),
    ("core/rails.py", '"Riel eliminado."', 't("Rail deleted.")', 1),

    # ── plan_data: los NOMBRES de herramienta que se pintan ──
    ("core/plan_data.py", '"Survey de elevador"', 't("Lift survey")', 1),
    ("core/plan_data.py", '"Líneas de plomada"', 't("Plumb lines")', 1),
    ("core/plan_data.py", '"Corte de rieles"', 't("Rail cutting")', 1),
    ("core/plan_data.py", '"Corte de buffers"', 't("Buffer cutting")', 1),
    ("core/plan_data.py", '"Sin datos del plano."', 't("No drawing data.")', 1),
    ("core/plan_data.py", '"Parámetros del hueco"', 't("Shaft parameters")', 1),
    ("core/plan_data.py", '"Número de paradas"', 't("Number of stops")', 1),
    ("core/plan_data.py", '"N.º de paradas (NS)"', 't("No. of stops (NS)")', 1),
    ("core/plan_data.py", '"Código de riel"', 't("Rail code")', 1),
    ("core/plan_data.py", '"Modelo (línea de producto)"',
     't("Model (product line)")', 1),
    ("core/plan_data.py", '"Datos de belting"', 't("Belting data")', 1),
    ("core/plan_data.py", '"LFKK / LFGK (rieles)"', 't("LFKK / LFGK (rails)")', 1),
    ("core/plan_data.py", '"Survey (RAIL del catálogo)"',
     't("Survey (RAIL from the catalogue)")', 1),

    # ── invoices ──
    ("core/invoices.py", GS, GS_EN, 1),
    ("core/invoices.py", '"La factura no tiene líneas."',
     't("The invoice has no lines.")', 1),

    # ── manuals ──
    ("core/manuals.py", '"El almacenamiento (Drive + hoja) no está configurado."',
     't("Storage (Drive + sheet) is not configured.")', 1),
    ("core/manuals.py",
     '"No se extrajo texto (¿PDF escaneado/imagen?). Súbelo con OCR aplicado."',
     't("No text was extracted (scanned/image PDF?). Upload it with OCR applied.")', 1),
    ("core/manuals.py", '"No se pudo abrir la hoja de manuales."',
     't("Could not open the manuals sheet.")', 1),

    # ── toolruns: los VALORES de HERRAMIENTAS (las claves NO se tocan) ──
    ("core/toolruns.py", '"Falta el proyecto."', 't("The project is missing.")', 1),
    ("core/toolruns.py", '"No se pudo abrir la hoja de cálculos."',
     't("Could not open the calculations sheet.")', 1),
]


def _import(rel):
    f = R / rel
    src = f.read_text(encoding="utf-8")
    if "from core.i18n import t" in src:
        return
    ancla = "logger = logging.getLogger(__name__)"
    if src.count(ancla) != 1:
        print(f"  ⚠️ {rel}: ancla del import ambigua ({src.count(ancla)})")
        return
    f.write_text(src.replace(ancla, f"from core.i18n import t\n{ancla}", 1),
                 encoding="utf-8")
    print(f"  OK  {rel}: import añadido")


for rel in IMPORTS:
    _import(rel)

hechos = fallos = 0
for rel, viejo, nuevo, n_esp in CAMBIOS:
    f = R / rel
    src = f.read_text(encoding="utf-8")
    n = src.count(viejo)
    if n != n_esp:
        print(f"  ⚠️ {rel}: esperaba {n_esp} y hay {n} de {viejo[:46]!r}")
        fallos += 1
        continue
    f.write_text(src.replace(viejo, nuevo), encoding="utf-8")
    hechos += 1
print(f"\n{hechos} cambios aplicados · {fallos} sin casar")
