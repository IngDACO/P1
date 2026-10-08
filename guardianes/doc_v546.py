# -*- coding: utf-8 -*-
"""Documenta v546 — la pantalla de Fichaje, probada acción por acción en producción."""
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

SECCION = """## LA PANTALLA DE FICHAJE, PROBADA ACCIÓN POR ACCIÓN EN PRODUCCIÓN (v546)

Segunda pantalla del recorrido guiado por el usuario, con la cuenta admin. Funcionaban:
tarjetas y «Charged today» (cuadran con la hoja), abrir/cerrar la jornada, fichar en una obra,
«Switch project» (cierra una y abre otra en el mismo segundo), «Leave the project» (la jornada
sigue), y «Did you forget…» (abrir a una hora pasada y corregir una hora quedan como
correcciones pendientes, COR-0001 y COR-0002). Lo que no:

1. **⚠️ Jornadas solapadas: tiempo pagado contado dos veces.** «Abrir la jornada a las 18:00»
   con una ya cerrada de 18:24 a 18:26 se aceptaba (la tarjeta subió a 0,51 h), y «Fix the
   time» solo comparaba la entrada con su propia salida. → `timeclock._choca`: una hora pasada
   que pisa otra entrada del MISMO tipo de esa persona se rechaza en `clock_in` y en
   `corregir_fichaje`, diciendo con cuál choca. Un tramo de obra dentro de la jornada no es
   choque (otro tipo); fichar «ahora» no se comprueba (va siempre después).
2. **El panel «Did you forget…» se cerraba solo** tras cada paso (3 veces): sin clave, Streamlit
   lo crea de nuevo cuando el aviso verde de arriba aparece o se va, y nace cerrado. Comprobado
   ANTES en una mini-app 1.64: con clave sigue abierto. → clave; y la lectura de la IA del Home
   (visto en v544), igual.
3. **Fichar desde la pantalla no sacaba el modal del Pre-Start** (el lateral sí, v374). Decisión
   del usuario: «deben comportarse igual». → la pantalla ficha por `_fichar` (selector, obra
   única y atajo del roster), y «Switch» también avisa de la obra nueva
   (`_armar_aviso_prestart`).
4. El historial ponía la fecha como mes/día («10/08» por el 8 de octubre) → día/mes.
5. «— cambiar a… —» en español en «Switch project» → «— switch to… —».

Reanclados con su motivo: `verif_v308` (la pantalla ficha por `_fichar`; el nombre sigue
saliendo de `_nom_de`) y `verif_v374` (la bandera vive en `_armar_aviso_prestart`). Los dos se
comprobaron rompiendo su regla a mano: los dos se ponen rojos.

Sin probar (no se puede con esta cuenta): el aviso de sesión olvidada de otro día y los botones
del campo (baja, atajo del roster, obra única).

__PROD__ · 21 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v546 | **La pantalla de Fichaje, probada acción por acción en producción.** ⚠️ Abrir la "
        "jornada «a las 18:00» con otra ya cerrada de 18:24 a 18:26 se aceptaba y esos minutos se "
        "pagaban dos veces → `timeclock` rechaza una hora que pise otra entrada del mismo tipo "
        "(abrir y corregir). El panel «Did you forget…» se cerraba solo tras cada paso → clave "
        "(y la IA del Home). Fichar desde la pantalla no sacaba el modal del Pre-Start → igual "
        "que el lateral, también «Switch». Historial en día/mes y «— switch to… —». __PROD__ · "
        "__BATERIA__ · __SUITE__ |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v545 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v545 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
N_VIEJA = "*Última puesta al día del estado de hecho: 08/10/2026 (v515-v545).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 08/10/2026 (v515-v546).*"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v546.py "<suite>" "<bateria>" "<produccion>"')
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
h = h.replace(A_HIST, "## Versiones desplegadas (v546 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v546 + fila + cabecera")

c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v546 = actual)")
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
print("CLAUDE.md: fila v546 · se cayo %s · %d bytes" % (vieja.strip(), len(c.encode("utf-8"))))

escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v546")
