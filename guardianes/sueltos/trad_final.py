# -*- coding: utf-8 -*-
"""Último resto de v450: el correo interno, el radar, el log del Survey y plan_data.

⚠️ `email_notify` va en texto BASE **literal**, sin `d()`: son trozos de una plantilla
HTML gigante en f-strings, y ahí no cabe una llamada sin reescribirla entera. El
idioma base es el inglés, así que el literal ES el texto correcto (regla v436: un
correo sale de la empresa y no sigue la pantalla de quien lo dispara).
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

CAMBIOS = {
    "core/email_notify.py": [
        ('"RL (desplazamiento lateral)"', '"RL (lateral shift)"', 1),
        ('"FB (desplazamiento frontal)"', '"FB (front shift)"', 1),
        ("No se encontró solución válida.", "No valid solution was found.", 1),
        ("'(no especificado)'", "'(not specified)'", 2),
        (">Parámetros principales<", ">Main parameters<", 1),
        ('"BSR (obra)"', '"BSR (on site)"', 1),
        ('"Paradas (NS)"', '"Stops (NS)"', 1),
        ('"Pared limitante"', '"Limiting wall"', 1),
        ('"BS (plano)"', '"BS (drawing)"', 1),
        (">Estado inicial del survey<", ">Initial survey state<", 1),
        (">Análisis BSR vs BS<", ">BSR vs BS analysis<", 1),
        ("'Sin proyecto'", "'No project'", 1),
        ("<strong>Fecha:</strong>", "<strong>Date:</strong>", 1),
        ("<strong>Proyecto:</strong>", "<strong>Project:</strong>", 1),
        ("<strong>Ingeniero:</strong>", "<strong>Engineer:</strong>", 1),
    ],
    "core/admin_digest.py": [
        ('f"## ESTADO EN VIVO DEL GRUPO {grupo} ({len(proys)} proyectos)"',
         'f"## LIVE STATUS OF {grupo} ({len(proys)} projects)"', 1),
        ('or "sin asignar"', 'or t("unassigned")', 1),
    ],
    "core/plan_data.py": [
        ('"params":  "Survey · Plomadas"', '"params":  "Survey · Plumb lines"', 1),
    ],
    "core/survey_ui.py": [
        # ⚠️ Valor que se PINTA en la tabla del log Y se compara tres veces en la
        # misma función (incluido el resaltado). Se renombran TODOS los lados a la
        # vez: traducir uno solo deja la fila sin color y sin orden, en silencio.
        ('"SELECCIONADA"', '"SELECTED"', 3),
        ('"ÓPTIMA"', '"OPTIMAL"', 3),
    ],
}


def main():
    tot = 0
    for rel, cambios in CAMBIOS.items():
        ruta = RAIZ / rel
        src = ruta.read_text(encoding="utf-8")
        for viejo, nuevo, veces in cambios:
            n = src.count(viejo)
            if n != veces:
                raise SystemExit(f"{rel}: {viejo[:60]!r} aparece {n}, esperaba {veces}")
            src = src.replace(viejo, nuevo)
            tot += veces
        ast.parse(src)
        ruta.write_text(src, encoding="utf-8", newline="")
        print(f"  {rel:26} {sum(c[2] for c in cambios)}")
    print(f"\n{tot} textos traducidos")


if __name__ == "__main__":
    main()
