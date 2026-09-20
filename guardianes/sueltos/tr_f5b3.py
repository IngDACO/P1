# -*- coding: utf-8 -*-
"""F5b, tanda 3: `quotes.py`, `projects.py`, `ausencias.py`.

⚠️ Lo que NO se toca, comprobado uno a uno antes de escribir:
  · `projects.derive_estado` devuelve `"En progreso"`/`"Planificado"`/`"Completado"`:
    son el DATO que se ESCRIBE en la hoja, y traducirlos deja de encontrar proyectos
    sin dar ningún error. El filtro de «mensaje» (3+ palabras o puntuación) ya los
    excluye, pero se dice aquí porque es el fallo que más caro sale.
  · las CLAVES de `ausencias.TIPOS` (`"vacaciones"`, `"enfermedad"`, `"libre"`) y sus
    `estado_roster` (`"LEAVE"`, `"OFF"`): se guardan y se comparan. Solo se traduce
    el `nombre`, que únicamente se pinta.
  · `quotes` `"motivo"`: verificado que solo se muestra (`quotes_ui:303`), nunca se
    compara.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

GS = '"Google Sheets no está configurado."'
GS_EN = 't("Google Sheets is not configured.")'

CAMBIOS = [
    # ── quotes.py ──
    ("core/quotes.py", GS, GS_EN, 3),
    ("core/quotes.py", '"motivo": "ya no está en el catálogo"',
     '"motivo": t("no longer in the catalogue")', 1),
    ("core/quotes.py", '"motivo": "cambió en el catálogo"',
     '"motivo": t("changed in the catalogue")', 1),
    ("core/quotes.py", '"Cotización no encontrada."', 't("Quote not found.")', 5),
    ("core/quotes.py",
     '"Solo se pueden actualizar precios en un borrador. '
     'Esta ya se envió: saca una versión nueva."',
     't("Prices can only be updated on a draft. This one was already sent: '
     'create a new version.")', 1),
    ("core/quotes.py", '"Los precios ya están al día."',
     't("Prices are already up to date.")', 1),
    ("core/quotes.py", '"Añade al menos una línea a la cotización."',
     't("Add at least one line to the quote.")', 1),
    ("core/quotes.py", '"Elige a quién va la cotización."',
     't("Choose who the quote is for.")', 1),
    ("core/quotes.py", 'f"Error guardando la cotización: {e}"',
     'f"{t(\'Error saving the quote\')}: {e}"', 1),
    ("core/quotes.py",
     '"Esta cotización ya no es un borrador. Crea una versión nueva para cambiarla."',
     't("This quote is no longer a draft. Create a new version to change it.")', 1),
    ("core/quotes.py", '"Cotización actualizada."', 't("Quote updated.")', 1),
    ("core/quotes.py", '"La cotización no tiene líneas."',
     't("The quote has no lines.")', 1),
    ("core/quotes.py", 'f"No se pudo crear el proyecto: {msg}"',
     'f"{t(\'Could not create the project\')}: {msg}"', 1),

    # ── projects.py ──
    ("core/projects.py", GS, GS_EN, 1),
    ("core/projects.py", '"Ya existe una agrupación con ese nombre en el grupo."',
     't("A grouping with that name already exists in this group.")', 1),
    ("core/projects.py", '"Agrupación no encontrada."', 't("Grouping not found.")', 1),
    ("core/projects.py", '"Agrupación eliminada."', 't("Grouping deleted.")', 1),
    ("core/projects.py", '"Nada que adjuntar."', 't("Nothing to attach.")', 1),
    ("core/projects.py", '"Proyecto no encontrado."', 't("Project not found.")', 3),
    ("core/projects.py", '"Proyecto actualizado."', 't("Project updated.")', 1),
    ("core/projects.py", '"Proyecto eliminado."', 't("Project deleted.")', 1),
    ("core/projects.py", '"Sin cambios que guardar."',
     't("No changes to save.")', 2),
    ("core/projects.py", 'f"Error guardando actividades: {e}"',
     'f"{t(\'Error saving activities\')}: {e}"', 1),
    ("core/projects.py", '"Actividades actualizadas."',
     't("Activities updated.")', 1),
    ("core/projects.py", '"Documento eliminado."', 't("Document deleted.")', 1),

    # ── ausencias.py ──
    ("core/ausencias.py", GS, GS_EN, 3),
    ("core/ausencias.py", '"nombre": "Vacaciones"', '"nombre": t("Annual leave")', 1),
    ("core/ausencias.py", '"nombre": "Baja por enfermedad"',
     '"nombre": t("Sick leave")', 1),
    ("core/ausencias.py", '"nombre": "Día libre"', '"nombre": t("Day off")', 1),
    ("core/ausencias.py", '"El rango no tiene días."',
     't("The range has no days.")', 1),
    ("core/ausencias.py", '"No se entienden las fechas."',
     't("The dates could not be read.")', 1),
    ("core/ausencias.py",
     '"La fecha de fin no puede ser anterior a la de inicio."',
     't("The end date cannot be earlier than the start date.")', 1),
    ("core/ausencias.py", '"Esa solicitud ya no está vigente."',
     't("That request is no longer active.")', 1),
    ("core/ausencias.py", '"Ausencia aprobada."', 't("Absence approved.")', 1),
    ("core/ausencias.py", '"Ausencia cancelada."', 't("Absence cancelled.")', 1),
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


for rel in ("core/quotes.py", "core/projects.py", "core/ausencias.py"):
    _import(rel, "logger = logging.getLogger(__name__)")

for rel, viejo, nuevo, n_esp in CAMBIOS:
    f = R / rel
    src = f.read_text(encoding="utf-8")
    n = src.count(viejo)
    if n != n_esp:
        print(f"  ⚠️ {rel}: esperaba {n_esp} y hay {n} de {viejo[:46]!r} — NO se toca")
        continue
    f.write_text(src.replace(viejo, nuevo), encoding="utf-8")
    print(f"  OK  {rel}: {n}x {viejo[:50]}")
