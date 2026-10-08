# -*- coding: utf-8 -*-
"""Documenta v545 — la campana se cierra al llevarte a una alerta, y su número se lee."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"
NEG = "C:/Users/diego/P1/NEGOCIO.md"
SUITE = sys.argv[1] if len(sys.argv) > 1 else ""
BATERIA = sys.argv[2] if len(sys.argv) > 2 else ""
PROD = sys.argv[3] if len(sys.argv) > 3 else ""

SECCION = """## LA CAMPANA SE CIERRA AL LLEVARTE A UNA ALERTA, Y SU NÚMERO SE LEE (v545)

Visto en producción verificando v544 con el admin:

1. Tocar una alerta de la campana llevaba a la obra con el popover **abierto encima** de la
   pantalla de destino (su estado abierto vive en el navegador). → La clave del popover lleva
   generación y la sube cada alerta tocada: el popover nuevo nace cerrado (lo mismo que el mapa
   en v544, trampa 34).
2. A 846 px la columna de la campana da 62 px y Streamlit 1.64 recorta su etiqueta en una línea
   (trampa 33): «🔔 4» pedía 27 px de los 23 que dejaban 12+12 de relleno → se leía «🔔‥». → 6+6
   de relleno solo en ese botón (`.st-key-cpxtop [data-testid='stPopoverButton']`), medido en
   producción con un estilo temporal antes de escribirlo.

__PROD__ · 7 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v545 | **La campana se cierra al llevarte a una alerta, y su número se lee.** Vistos "
        "verificando v544: tocar una alerta llevaba a la obra con el popover ABIERTO encima (su "
        "estado vive en el navegador → clave con generación, como el mapa) y a 846 px se leía "
        "«🔔‥» (la columna recorta la etiqueta → 6+6 px de relleno, medido). __PROD__ · "
        "__BATERIA__ · __SUITE__ |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v544 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v544 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
N_VIEJA = "*Última puesta al día del estado de hecho: 08/10/2026 (v515-v544).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 08/10/2026 (v515-v545).*"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v545.py "<suite>" "<bateria>" "<produccion>"')
for _k, _v in (("__BATERIA__", BATERIA), ("__SUITE__", SUITE), ("__PROD__", PROD)):
    SECCION = SECCION.replace(_k, _v)
    FILA = FILA.replace(_k, _v)

h = io.open(HIST, encoding="utf-8").read()
unica(h, A_HIST, "cabecera", "HISTORIAL.md")
unica(h, CAB, "tabla", "HISTORIAL.md")
unica(h, TRAS_CAB, "separador", "HISTORIAL.md")
c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
n = io.open(NEG, encoding="utf-8").read()
unica(n, N_VIEJA, "marcador", "NEGOCIO.md")

h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v545 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v545 + fila + cabecera")

c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v545 = actual)")
c = c.replace(CAB, CAB + FILA)
lineas = c.splitlines(True)
idx = [i for i, l in enumerate(lineas) if l.startswith("| v")]
if len(idx) != 16:
    raise SystemExit("esperaba 16 filas tras insertar: %d" % len(idx))
vieja = lineas[idx[-1]][:10]
del lineas[idx[-1]]
c = "".join(lineas)
m = re.search(r"_\(y (\d+) versiones anteriores", c)
if not m:
    raise SystemExit("no encuentro la nota de cierre")
c = c.replace(m.group(0), "_(y %d versiones anteriores" % (int(m.group(1)) + 1))
escribir(CLAUDE, c)
print("CLAUDE.md: fila v545 · se cayo %s · %d bytes" % (vieja.strip(), len(c.encode("utf-8"))))

escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v545")
