# -*- coding: utf-8 -*-
"""v542: «guardar el survey en su proyecto lo limpia», comprobado en producción con el admin
(08/10/2026). Y la columna del proyecto se llama MatrixJSON, no MatrizJSON. Un solo uso."""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CAMBIOS = [
    ("Guardar el survey en un proyecto, sin comprobar en producción (pide cuenta admin y un "
     "cálculo, que manda correo): lo cubre el guardián",
     "Después, con el admin (08/10/2026): el survey guardado de 88 walker cargado con «Rebuild», "
     "calculado y guardado en PRJ-0015 → el Survey vuelve a los datos VACÍO (BS/BSR/FS 0, NS 2, "
     "matriz a ceros, selector en «sin proyecto») con «Survey saved…», «Documents filed in "
     "Drive» y «Project PRJ-0015 … updated» con «Open project ➜»; en la hoja (solo lectura), "
     "PRJ-0015 con sus 92 parámetros, la matriz de 6 filas, CAL-0007 y los 2 documentos"),
]
SOLO_CLAUDE = [("**ParamsJSON·MatrizJSON·InterpJSON**", "**ParamsJSON·MatrixJSON·InterpJSON**")]
for p, cambios in (("C:/Users/diego/P1/CLAUDE.md", CAMBIOS + SOLO_CLAUDE),
                   ("C:/Users/diego/P1/HISTORIAL.md", CAMBIOS)):
    s = io.open(p, encoding="utf-8").read()
    for viejo, nuevo in cambios:
        n = s.count(viejo)
        if n < 1:
            raise SystemExit("ancla no encontrada en %s: %s" % (p, viejo[:60]))
        s = s.replace(viejo, nuevo)
        print(p, "reemplazos:", n, "·", viejo[:40])
    io.open(p, "w", encoding="utf-8", newline="").write(s)
