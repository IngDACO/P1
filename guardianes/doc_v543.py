# -*- coding: utf-8 -*-
"""Documenta v543 — el aviso «el survey empezó de cero» sale en el momento."""
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

SECCION = """## EL AVISO «EL SURVEY EMPEZÓ DE CERO» SALE EN EL MOMENTO (v543)

Visto en producción probando v542 con la cuenta de campo: al fichar en otra obra el Survey
empezaba de cero en el acto, pero el aviso salía UNA PASADA TARDE, en el clic siguiente. Iba
por `flash`, y la shell pinta la cola de `flash` ANTES de que el Survey encole en esa misma
pasada. (Se había ido a `flash` porque, con otro nº de paradas, la matriz se redimensiona con
`st.rerun()` y se lleva un `st.info` pintado antes.)

→ Una marca en la sesión (`_AVISO_CERO`): el aviso se pinta junto al selector mientras dure,
y la marca se quita solo DESPUÉS del punto en que la matriz puede cortar la pasada. Cortada o
no, el aviso está en la pasada que se ve, y no se queda colgado para la siguiente.

⚠️ Lección: `flash` sirve para lo que se encola ANTES de un `st.rerun()` y se pinta en la
pasada siguiente; para un aviso que nace a mitad de una pantalla, después de que la shell ya
pintó la cola, llega tarde.

__PROD__ · 9 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v543 | **El aviso «el survey empezó de cero» sale en el momento.** Visto en producción "
        "con v542: al fichar en otra obra el aviso salía una pasada tarde — iba por `flash`, que "
        "la shell pinta ANTES de que el Survey encole. Ahora una marca que dura hasta pasar el "
        "corte de la matriz (`st.rerun()` al cambiar de tamaño): el aviso está en la pasada que "
        "se ve y no se queda colgado. __PROD__ · __BATERIA__ · __SUITE__ |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v542 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v542 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
N_VIEJA = "*Última puesta al día del estado de hecho: 07/10/2026 (v515-v542).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 07/10/2026 (v515-v543).*"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v543.py "<suite>" "<bateria>" "<produccion>"')
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
h = h.replace(A_HIST, "## Versiones desplegadas (v543 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v543 + fila + cabecera")

c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v543 = actual)")
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
print("CLAUDE.md: fila v543 · se cayo %s · %d bytes" % (vieja.strip(), len(c.encode("utf-8"))))

escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v543")
