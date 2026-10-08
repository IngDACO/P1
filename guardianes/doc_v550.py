# -*- coding: utf-8 -*-
"""Documenta v550 — la cifra de una tarjeta KPI no se parte nunca."""
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

SECCION = """## LA CIFRA DE UNA TARJETA KPI NO SE PARTE NUNCA (v550)

Verificando v549 en producción (1024 px con el menú abierto): desde que los botones parten su
texto (`wrap=True`, con `overflow-wrap: break-word`), en una tarjeta KPI de 62 px (31 útiles)
«0%» salía «0» / «%» y «4 h», «4» / «h». La etiqueta y el pie ya se recortan con «…» a
propósito (v303); la cifra tiene que leerse entera. → `nowrap` + `keep-all` en la línea de la
cifra (`theme.py`). Probado ANTES en producción con un estilo temporal: las tres cifras en una
línea y la tarjeta de vuelta a 96 px.

Trampa nº33 puesta al día: la app parte el texto de los botones por defecto desde v549; una
cifra dentro de un botón que parte líneas necesita `nowrap`.

__PROD__ · 5 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v550 | **La cifra de una tarjeta KPI no se parte nunca.** Verificando v549 a 1024 px "
        "con el menú abierto: en la tarjeta de 62 px, «0%» salía «0» / «%» (el modo wrap parte "
        "con `break-word`). `nowrap` en la línea de la cifra, probado antes con un estilo "
        "temporal en producción. Trampa 33 al día. __PROD__ · __BATERIA__ · __SUITE__ |" + chr(10))

T33_VIEJA = ("columna, recortar. → Un botón de varias líneas en columnas necesita `wrap=True` o su CSS" + chr(10)
             + "    (las tarjetas `cpxkpi_` lo llevan en `theme.py`, medido en producción).")
T33_NUEVA = ("columna, recortar. → Desde v549 la app pone `wrap=True` POR DEFECTO (`core/botones`," + chr(10)
             + "    instalado en app.py); `wrap=False` explícito para una línea a propósito. Y una CIFRA" + chr(10)
             + "    dentro de un botón que parte líneas necesita `nowrap` (v550: «0» / «%» en 62 px).")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v549 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v549 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
N_VIEJA = "*Última puesta al día del estado de hecho: 09/10/2026 (v515-v549).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 09/10/2026 (v515-v550).*"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v550.py "<suite>" "<bateria>" "<produccion>"')
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
unica(c, T33_VIEJA, "trampa 33", "CLAUDE.md")
n = io.open(NEG, encoding="utf-8").read()
unica(n, N_VIEJA, "marcador", "NEGOCIO.md")

h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v550 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v550 + fila + cabecera")

c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v550 = actual)")
c = c.replace(CAB, CAB + FILA)
c = c.replace(T33_VIEJA, T33_NUEVA)
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
print("CLAUDE.md: fila v550 · se cayo %s · %d bytes" % (vieja.strip(), len(c.encode("utf-8"))))

escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v550")
