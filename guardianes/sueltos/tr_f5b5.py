# -*- coding: utf-8 -*-
"""F5b, tanda 5: los f-strings de varias líneas que quedaban.

⚠️ Anclajes con la indentación de la continuación copiada AL CARÁCTER: es lo que en
v440 hizo que 20 de 27 no casaran. Cada uno se comprueba antes de escribir.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

C = [
    # ── quotes.py ──
    ("core/quotes.py",
     'txt = f"{n} línea(s) actualizada(s) con los precios de hoy."',
     'txt = f"{n} " + t("line(s) updated with today\'s prices.")'),
    ("core/quotes.py",
     'txt += (" Sin tocar (ya no están en el catálogo): " + ", ".join(huerf) + ".")',
     'txt += (" " + t("Untouched (no longer in the catalogue)") + ": "\n'
     '                + ", ".join(huerf) + ".")'),
    ("core/quotes.py", 'f"Estado no válido: {estado}."',
     'f"{t(\'Invalid status\')}: {estado}."'),
    ("core/quotes.py",
     'return False, ("Esta cotización ya generó el proyecto "\n'
     '                       f"{c.get(\'ProyectoID\')}: no se puede cambiar su estado.")',
     'return False, (t("This quote already created project") + " "\n'
     '                       + f"{c.get(\'ProyectoID\')}: "\n'
     '                       + t("its status cannot be changed."))'),
    ("core/quotes.py", 'f"Cotización marcada como {estado}."',
     'f"{t(\'Quote marked as\')} {estado}."'),
    ("core/quotes.py",
     'return False, (f"Esta cotización ya generó el proyecto {c.get(\'ProyectoID\')}.")',
     'return False, (t("This quote already created project")\n'
     '                       + f" {c.get(\'ProyectoID\')}.")'),
    ("core/quotes.py",
     'return False, (f"Se creó el proyecto {res}, pero no se pudo enlazar con la "\n'
     '                       "cotización. Enlázalo a mano.")',
     'return False, (f"{t(\'Project\')} {res} "\n'
     '                       + t("was created, but it could not be linked to the "\n'
     '                           "quote. Link it by hand."))'),

    # ── projects.py ──
    ("core/projects.py", 'f"No se pudo abrir la hoja {title}: {e}"',
     'f"{t(\'Could not open sheet\')} {title}: {e}"'),
    ("core/projects.py",
     'return False, (f"Error interno: la fila tiene {len(row)} valores y la cabecera "\n'
     '                       f"{len(PROJECTS_HEADERS)} columnas.")',
     'return False, (f"{t(\'Internal error: the row has\')} {len(row)} "\n'
     '                       f"{t(\'values and the header has\')} "\n'
     '                       f"{len(PROJECTS_HEADERS)} {t(\'columns.\')}")'),
    ("core/projects.py",
     'return False, ("Ningún campo reconocido: " + ", ".join(_ignorados)\n'
     '                       + ". No se guardó nada.")',
     'return False, (t("No recognised field") + ": " + ", ".join(_ignorados)\n'
     '                       + ". " + t("Nothing was saved."))'),
    ("core/projects.py", 'f"Avance actualizado. Proyecto: {nuevo}%"',
     'f"{t(\'Progress updated. Project\')}: {nuevo}%"'),
    ("core/projects.py", 'f"{cambios} proyecto(s) actualizados."',
     'f"{cambios} " + t("project(s) updated.")'),

    # ── ausencias.py ──
    ("core/ausencias.py", 'f"Tipo de ausencia desconocido: {tipo}"',
     'f"{t(\'Unknown absence type\')}: {tipo}"'),
    ("core/ausencias.py",
     'return False, ("Ese rango solo tiene fin de semana. Si en esos días se "\n'
     '                       "trabaja, marca «incluir fines de semana».")',
     'return False, t("That range only covers the weekend. If those days are "\n'
     '                        "worked, tick «include weekends».")'),
    ("core/ausencias.py",
     'return False, (f"Ya hay una ausencia que pisa esas fechas: "',
     'return False, (f"{t(\'There is already an absence overlapping those dates\')}: "'),
    ("core/ausencias.py",
     'return False, (f"Error interno: la fila tiene {len(fila)} valores y la "\n'
     '                       f"cabecera {len(HEADERS)} columnas.")',
     'return False, (f"{t(\'Internal error: the row has\')} {len(fila)} "\n'
     '                       f"{t(\'values and the header has\')} "\n'
     '                       f"{len(HEADERS)} {t(\'columns.\')}")'),
    ("core/ausencias.py",
     'return False, (f"Esa solicitud ya está **{actual}**; no se puede volver a "\n'
     '                       "resolver. Para deshacer una ausencia aprobada, cancélala.")',
     'return False, (f"{t(\'That request is already\')} **{actual}**; "\n'
     '                       + t("it cannot be resolved again. To undo an approved "\n'
     '                           "absence, cancel it."))'),

    # ── orders.py ──
    ("core/orders.py", '"Complétalo desde la lista de órdenes.")',
     '+ t("Complete it from the orders list."))'),
]

for rel, viejo, nuevo in C:
    f = R / rel
    src = f.read_text(encoding="utf-8")
    n = src.count(viejo)
    if n != 1:
        print(f"  ⚠️ {rel}: {n} de {viejo.splitlines()[0][:56]!r}")
        continue
    f.write_text(src.replace(viejo, nuevo, 1), encoding="utf-8")
    print(f"  OK  {rel}: {viejo.splitlines()[0][:56]}")
