# -*- coding: utf-8 -*-
"""Documenta v548 — segunda tanda del barrido (controles dentro de funciones auxiliares)."""
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

SECCION = """## SEGUNDA TANDA DEL BARRIDO: CONTROLES DENTRO DE FUNCIONES AUXILIARES (v548)

Recorriendo la app en producción tras v547, «Create field user» (Planning · Users) seguía sin
clave: sus controles están en `_crear_usuario_form`, y el barrido —y su guardián— solo miraban
las llamadas DIRECTAS del cuerpo del desplegable. Siguiendo las funciones a las que llama
(también las de otros módulos, por nombre) salieron **11**: los dos «Create field user» (ramas
excluyentes, claves distintas), el «Upload drawing» de las 4 herramientas (`selector`), dos de
Contabilidad, la ubicación de la obra y su ganancia (se abren solas según los datos: la
condición va en la clave) y el plan semanal del campo.

- `verif_v547` ampliado: sigue las funciones auxiliares hasta un punto fijo, con un caso
  construido (local y de otro módulo) que la versión anterior no veía. Ahora cuenta 79
  desplegables con controles (68 directos + 11).
- «Progress claims» y la entrega compartían el esquema `{key_prefix}_exp_{pid}`; hoy no
  chocaban (prefijos y pestañas distintos), pero se hacen distintos por construcción
  (`_exp_claims_` / `_exp_ho_`).

⚠️ Lección (otra vez la nº30): un «0» de un barrido solo vale para la FORMA que su sonda mira.
Aquí la sonda miraba llamadas directas; los controles detrás de una función no existían para ella.

__PROD__ · 15 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v548 | **Segunda tanda del barrido: controles dentro de funciones auxiliares.** Tras "
        "v547, «Create field user» seguía sin clave (controles en `_crear_usuario_form`): el "
        "barrido y su guardián solo miraban llamadas directas. Siguiendo las funciones, 11 más "
        "(las 4 herramientas, Contabilidad, ubicación y ganancia de la obra…), y `verif_v547` "
        "ampliado para seguirlas. __PROD__ · __BATERIA__ · __SUITE__ |" + chr(10))

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v547 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v547 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
N_VIEJA = "*Última puesta al día del estado de hecho: 09/10/2026 (v515-v547).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 09/10/2026 (v515-v548).*"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v548.py "<suite>" "<bateria>" "<produccion>"')
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
h = h.replace(A_HIST, "## Versiones desplegadas (v548 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v548 + fila + cabecera")

c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v548 = actual)")
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
print("CLAUDE.md: fila v548 · se cayo %s · %d bytes" % (vieja.strip(), len(c.encode("utf-8"))))

escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v548")
