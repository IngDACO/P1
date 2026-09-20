# -*- coding: utf-8 -*-
"""Los mensajes de backend que v445-v447 se dejaron (v450).

Todos son `return ok, "..."` que la interfaz pinta con `flash`/`st.error`, así que van
con `t()`. ⚠️ NO entra aquí nada que sea DATO (columna de hoja, estado guardado,
nombre de actividad): esos se quedan en español a propósito.

⚠️ Cada entrada lleva su CONTEO esperado. Sin él, un reemplazo global aplica de más
(y traduce un dato) o de menos (y deja media traducción, que es peor que ninguna
porque nadie la ve venir).
"""
import ast
import io
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CORE = Path(r"C:\Users\diego\P1\survey_app\core")

# fichero -> [(viejo, nuevo, veces)]
CAMBIOS = {
    "ausencias.py": [
        ('f"Error guardando: {e}"', 'f"{t(\'Error saving\')}: {e}"', 3),
        ('"Solicitud no encontrada."', 't("Request not found.")', 2),
        ('"Solicitud rechazada."', 't("Request rejected.")', 1),
        ('"(automático)"', 't("(automatic)")', 1),
    ],
    "auth.py": [
        ('"Zona horaria actualizada."', 't("Time zone updated.")', 1),
        ('"Grupo no encontrado."', 't("Company not found.")', 6),
        ('f"Error guardando contacto: {e}"', 'f"{t(\'Error saving contact\')}: {e}"', 1),
        ('"Contacto actualizado."', 't("Contact updated.")', 1),
        ('f"Error guardando: {e}"', 'f"{t(\'Error saving\')}: {e}"', 1),
        ('"Libro enlazado."', 't("Workbook linked.")', 1),
    ],
    "catalogo.py": [
        ('f"Error guardando: {e}"', 'f"{t(\'Error saving\')}: {e}"', 1),
        ('f"Error actualizando: {e}"', 'f"{t(\'Error updating\')}: {e}"', 1),
    ],
    "credentials.py": [
        ('f"Error actualizando: {e}"', 'f"{t(\'Error updating\')}: {e}"', 1),
    ],
    "expenses.py": [
        ('f"Error guardando: {e}"', 'f"{t(\'Error saving\')}: {e}"', 1),
        ('"Recibo no encontrado."', 't("Receipt not found.")', 1),
    ],
    "inventory.py": [
        ('"Salida registrada."', 't("Check-out recorded.")', 1),
        ('"Traslado registrado."', 't("Transfer recorded.")', 1),
        ('"Mantenimiento registrado."', 't("Maintenance recorded.")', 1),
    ],
    "invoices.py": [
        ('"Factura no encontrada."', 't("Invoice not found.")', 3),
        ('"Cobro registrado."', 't("Payment recorded.")', 1),
        ('"Factura anulada."', 't("Invoice voided.")', 1),
    ],
    "orders.py": [
        ('f"Error actualizando: {e}"', 'f"{t(\'Error updating\')}: {e}"', 1),
        ('"Orden no encontrada."', 't("Order not found.")', 3),
        ('"Esa orden ya estaba recibida."', 't("That order was already received.")', 1),
        ('"Esa orden ya tiene su gasto registrado."',
         't("That order already has its expense recorded.")', 1),
        ('"Gasto registrado."', 't("Expense recorded.")', 1),
        ('"Orden cancelada."', 't("Order cancelled.")', 1),
    ],
    "projects.py": [
        ('f"Error actualizando: {e}"', 'f"{t(\'Error updating\')}: {e}"', 1),
        ('"Actividad no encontrada."', 't("Activity not found.")', 2),
        ('"Actividad agregada."', 't("Activity added.")', 1),
        ('"Actividad eliminada."', 't("Activity deleted.")', 1),
        ('f"Error guardando: {ex}"', 'f"{t(\'Error saving\')}: {ex}"', 1),
        ('"Avances guardados."', 't("Progress saved.")', 1),
        ('"Documento registrado."', 't("Document recorded.")', 1),
        ('"Registro no encontrado."', 't("Record not found.")', 1),
        ('"(sin nombre)"', 't("(no name)")', 1),
    ],
    "quotes.py": [
        ('f"Error actualizando: {e}"', 'f"{t(\'Error updating\')}: {e}"', 1),
    ],
    "rails.py": [
        ('"Referencia no encontrada."', 't("Reference not found.")', 2),
    ],
    "roster.py": [
        ('f"Error guardando: {e}"', 'f"{t(\'Error saving\')}: {e}"', 2),
        ('f"Error actualizando: {e}"', 'f"{t(\'Error updating\')}: {e}"', 1),
        ('f"Error borrando: {e}"', 'f"{t(\'Error deleting\')}: {e}"', 1),
    ],
    "timeclock.py": [
        ('"(sin proyecto)"', 't("(no project)")', 2),
    ],
    "finance.py": [
        ('"(sin cliente)"', 't("(no client)")', 1),
    ],
    "interpretation.py": [
        ('"API key no configurada."', 'd("API key not configured.")', 1),
    ],
}


def main():
    tot = 0
    for nombre, cambios in CAMBIOS.items():
        ruta = CORE / nombre
        src = ruta.read_text(encoding="utf-8")
        for viejo, nuevo, veces in cambios:
            n = src.count(viejo)
            if n != veces:
                raise SystemExit(f"{nombre}: {viejo!r} aparece {n} veces, esperaba {veces}")
            src = src.replace(viejo, nuevo)
            tot += veces
        ast.parse(src)                     # ⚠️ no se escribe nada que no compile
        io.open(ruta, "w", encoding="utf-8", newline="").write(src)
        print(f"  {nombre:20} {sum(c[2] for c in cambios)} mensajes")
    print(f"\n{tot} mensajes traducidos")


if __name__ == "__main__":
    main()
