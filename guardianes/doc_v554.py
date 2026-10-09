# -*- coding: utf-8 -*-
"""Documenta v554 — Day route, probada acción por acción."""
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

SECCION = """## DAY ROUTE, PROBADA ACCIÓN POR ACCIÓN (v554)

Recorrido en producción (Planning → Day route, decisión del usuario: «Dale»). Funcionaban
la carga (1,7 s; el mapa 1,3 s después), los saltos de día (~1,5 s), el fin de semana, el
mapa, «Directions» y la tabla. Arreglado:

- ⚠️ **Un día FUTURO salía «⚠️ not clocked in» para todos** (el martes 13): ahora
  «🗓️ planned»; hoy, «not clocked in yet» (como Compliance, v551); pasado, «not clocked in».
- «Today's sites» / «with people today» en cualquier día → el día que se mira.
- **«On site» contaba ASIGNACIONES**: una persona en dos obras contaba dos («2 of 2 people»
  con otra sin plan, sumando 3 de 2). Ahora «Planned» (un día futuro nadie está en obra) y
  cuenta personas; «No location» cuenta obras sin pin, no filas persona→obra.
- «Planned» y «No plan» llevaban al Panel en OTRA semana (desde el 13/10, la del 05/10) →
  la semana del día que se mira (`ros_lunes`).
- «←» devolvía la pantalla a HOY: Streamlit purga el widget no pintado → el día se recuerda
  en `_rd_dia`, y el `date_input` va sin `value` (con `value` y el estado a la vez,
  Streamlit lo apunta en el log, v537).
- Las obras no se podían tocar → el nombre en su tarjeta abre la obra; «Sites» y
  «No location» con UNA obra la abren (`_abrir_obra`, la vía `_prjsel_pending`).
- «Friday 9 of October» (calco del español) → «Friday 9 October» por plantilla; el aviso de
  fin de semana por `t()` y sin minúscula; las etiquetas de las tarjetas por `t()`.

Descartado al verificar: las cabeceras de «Who goes where» SÍ salen en inglés
(`tabla.cfg()` traduce «Persona»/«Horario»); y la lentitud de los saltos de día era de la
sonda (clics encolados por una llamada cortada), no de la app.

__PROD__ · 29 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v554 | **Day route, probada acción por acción.** ⚠️ Un día FUTURO salía «not clocked "
        "in» para todos → «planned» (hoy «yet», pasado sin él); «Today's» solo hoy; «On site» "
        "contaba asignaciones → «Planned» cuenta personas; los KPI al Panel en la semana del "
        "día; «←» recuerda el día; el nombre de cada obra la abre; «9 October» sin «of». "
        "__PROD__ · __BATERIA__ · __SUITE__ |" + chr(10))

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v553 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v553 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
N_VIEJA = "*Última puesta al día del estado de hecho: 09/10/2026 (v515-v553).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 09/10/2026 (v515-v554).*"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v554.py "<suite>" "<bateria>" "<produccion>"')
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
h = h.replace(A_HIST, "## Versiones desplegadas (v554 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v554 + fila + cabecera")

c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v554 = actual)")
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
print("CLAUDE.md: fila v554 · se cayo %s · %d bytes" % (vieja.strip(), len(c.encode("utf-8"))))

escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v554")
