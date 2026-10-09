# -*- coding: utf-8 -*-
"""Documenta v551 — el Panel de Planificación, probado acción por acción."""
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

SECCION = """## EL PANEL DE PLANIFICACIÓN, PROBADO ACCIÓN POR ACCIÓN (v551)

Recorrido «pantalla por pantalla» guiado por el usuario: Planning → Panel. Decisión del usuario:
«Dale 2-9 / 1 confirmacion».

- ⚠️ **«Copy previous week» pisaba semanas enteras sin preguntar.** `copiar_semana` reescribe la
  semana COMPLETA de cada persona que tenía algo la semana anterior. Ahora pide confirmación y
  dice a quién le reemplaza lo que ya tiene esta semana (también si solo tenía notas).
- **El selector segmentado (Week/Day/Free…) salía con bolitas y sin resaltado.** En 1.64 el
  radio es react-aria: cada opción va en su propio `div` y las reglas `> label` de v292 dejaron
  de casar. CSS reescrito sobre `data-testid="stRadioOption"` y `data-selected`, probado antes
  en producción con un estilo temporal.
- **Las 4 tarjetas KPI eran HTML pasivo** → botones (`cpxkpi_`): fichados → Compliance, libres
  → la vista «Free» en HOY, choques y certificados → el Radar.
- **Las líneas del Radar eran texto** → botones que abren la ficha rápida de esa persona
  (`_radar_scan` devuelve un 4º elemento: de quién es cada línea). Y « y » / «se solapan»,
  en inglés.
- «Free» y el día de «Assign» abrían en el lunes (un día pasado) → `_idx_hoy`, la misma regla
  que «Day».
- Compliance decía «not clocked in yet» de un día PASADO → «no time charged to it» (en un día
  pasado no se distingue «no fichó» de «fichó sin imputar»).
- El editor de la celda se quedaba ABIERTO tras «Save» y «View the day» → generación en la
  clave (`_ros_pop_gen`), en la del popover Y en la de su CSS de color, que tienen que casar.
- El editor ofrecía «Select all» (nuevo en 1.64): asignaba todas las obras y estados a la
  vez → `select_all=False`.
- **«←» desde Users no volvía al Panel**: el historial apilaba solo SECCIONES. Ahora
  (sección, sub-pestaña), normalizado como `_sub_header` (sin estado = la primera) y leyendo
  las entradas viejas de una sesión abierta antes del despliegue.
- Textos en español (Activar/Desactivar/inactivo, libre, Exige, Asignar, «Add suningo» en la
  ayuda del domingo) y el botón de asignar con el NOMBRE de la obra. «Free today» leía el
  nombre con `u.get(t("Name"))`, que en español habría buscado la clave «Nombre».

Guardianes reanclados con su razón: `verif_marcas` (el escaneo del radar se indexa: devuelve
4 elementos) y `verif_v487` (el patrón exento se mudó de `render_planificacion` a `_idx_hoy`).

__PROD__ · 64 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v551 | **El Panel de Planificación, probado acción por acción.** ⚠️ «Copy previous "
        "week» pisaba semanas enteras sin preguntar → confirmación con a quién reemplaza. El "
        "selector segmentado salía con bolitas (DOM del radio de 1.64) → CSS por `data-selected`. "
        "Tarjetas KPI y líneas del Radar ACTIVAS; «Free»/«Assign» abren en hoy; Compliance sin "
        "«yet» en días pasados; el editor de celda se cierra tras «Save»/«View the day» y sin "
        "«Select all»; «←» recuerda la sub-pestaña (Users → Panel); textos en inglés. "
        "__PROD__ · __BATERIA__ · __SUITE__ |" + chr(10))

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v550 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v550 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
N_VIEJA = "*Última puesta al día del estado de hecho: 09/10/2026 (v515-v550).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 09/10/2026 (v515-v551).*"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v551.py "<suite>" "<bateria>" "<produccion>"')
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
h = h.replace(A_HIST, "## Versiones desplegadas (v551 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v551 + fila + cabecera")

c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v551 = actual)")
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
print("CLAUDE.md: fila v551 · se cayo %s · %d bytes" % (vieja.strip(), len(c.encode("utf-8"))))

escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v551")
