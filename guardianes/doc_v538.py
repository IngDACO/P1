# -*- coding: utf-8 -*-
"""Documenta v538 — ningún componente puede subir de versión solo."""
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

SECCION = """## NINGÚN COMPONENTE PUEDE SUBIR DE VERSIÓN SOLO (v538)

Auditando «¿ya está todo cerrado?» tras v537: lo que tumbó el Pre-Start —el Cloud reinstala
TODAS las dependencias cada vez que la app despierta, y un componente subió de versión dentro
de su rango— podía repetirse con los otros dos componentes de la app:
`extra-streamlit-components` (la cookie de «Keep me signed in») y `streamlit-folium` (los mapas
de la ubicación y de la ruta del día). Y `anthropic` (la IA) no tenía tope.

→ Los dos, fijos a lo que corre en el Cloud (0.1.81 y 0.27.4, de los logs del 06/10/2026), y
`anthropic<2`. El guardián detecta los componentes por lo que INSTALAN (un frontend con su
`index.html`), no por una lista escrita a mano, así que uno nuevo que se añada sin fijar sale
rojo; y exige tope en todo lo demás salvo `tzdata`.

__PROD__ · 7 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v538 | **Ningún componente puede subir de versión solo.** Lo que tumbó el Pre-Start "
        "(v537) podía repetirse con la cookie de «Keep me signed in» (`extra-streamlit-components`) "
        "y los mapas (`streamlit-folium`): fijos a lo que corre en el Cloud, y `anthropic<2`. El "
        "guardián detecta los componentes por lo que instalan, no por una lista. __PROD__ · "
        "__BATERIA__ · __SUITE__ |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v537 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v537 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
N_VIEJA = "*Última puesta al día del estado de hecho: 06/10/2026 (v515-v537).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 06/10/2026 (v515-v538).*"
P_VIEJA = ("  ⚠️ **Los componentes de terceros van FIJOS (==)**, no con tope de major: "
           "`streamlit-drawable-canvas`\n  pasó de 0.9 a 0.13 dentro de `<1` y dejó el Pre-Start "
           "caído (v537). El Cloud reinstala todo cada\n  vez que la app despierta.\n")
P_NUEVA = ("  ⚠️ **Los componentes de terceros van FIJOS (==)**, no con tope de major: "
           "`streamlit-drawable-canvas`\n  pasó de 0.9 a 0.13 dentro de `<1` y dejó el Pre-Start "
           "caído (v537). El Cloud reinstala todo cada\n  vez que la app despierta. Desde v538 lo "
           "vigila `verif_v538` (detecta los componentes por lo que\n  instalan) y exige tope en "
           "todo lo demás salvo `tzdata`.\n")


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v538.py "<suite>" "<bateria>" "<produccion>"')
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
unica(c, P_VIEJA, "componentes", "CLAUDE.md")
n = io.open(NEG, encoding="utf-8").read()
unica(n, N_VIEJA, "marcador", "NEGOCIO.md")

h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v538 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v538 + fila + cabecera")

c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v538 = actual)")
c = c.replace(CAB, CAB + FILA)
c = c.replace(P_VIEJA, P_NUEVA)
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
print("CLAUDE.md: fila v538 · se cayo %s · %d bytes" % (vieja.strip(), len(c.encode("utf-8"))))

escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v538")
