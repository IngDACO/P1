# -*- coding: utf-8 -*-
"""Documenta v530 — elegir otra solución activa ya no deja el survey en un bucle."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"
SUITE = sys.argv[1] if len(sys.argv) > 1 else ""
BATERIA = sys.argv[2] if len(sys.argv) > 2 else ""

SECCION = """## ELEGIR OTRA SOLUCIÓN ACTIVA YA NO DEJA EL SURVEY EN UN BUCLE (v530)

Buscando el patrón de v529 (vaciar un widget con `pop`) en el resto de la app, apareció en
`survey_ui` algo más grave. Desde el 19/07 —la «solución activa elegible»—, **elegir en el
desplegable cualquier solución que no fuera la recomendada dejaba la página en un bucle de
pasadas sin fin**. La lista se ordenaba con la ACTIVA primero; al elegir otra se reordenaba,
y la POSICIÓN guardada en el desplegable pasaba a señalar OTRA solución, que el código
tomaba como una elección nueva, y vuelta a empezar. Medido con el survey REAL (AppTest, el
caso de `fixture_survey`, sin IA, sin correo y con las escrituras prohibidas): **más de 25
pasadas seguidas** eligiendo la 2.ª o la 3.ª, y la solución que usan diagramas, plomado e
informe cambiando en cada una. En la app, la página se queda en «Running» sin parar.

### El arreglo
- El ORDEN sale de la RECOMENDADA del cálculo (`optimizer_result.recomendada`, que no cambia),
  no de la activa; la activa se busca por IDENTIDAD. Elegir cuesta una pasada más y se queda.
- La estrella y el desplegado de «Solution N» siguen a la ACTIVA, como antes (antes la activa
  iba siempre primera; ahora puede estar en cualquier posición).
- Tras «Recalculate», la solución activa y los pisos ya no se borran con `pop` —el navegador
  seguía enseñando la selección vieja y la DEVOLVÍA en el siguiente clic—: cada cálculo lleva
  su número y esos widgets, **una clave nueva**, así que nacen como widgets nuevos.

### ⚠️ Por qué no bastaba el arreglo de v529
Asignar el valor antes de pintar (lo de la caja del parte) no alcanza aquí: «Recalculate»
corta la pasada con `st.rerun()` ANTES de pintar esos widgets, Streamlit tira el estado de lo
que no se pintó —el modo de pisos vuelve a «With issues»— y en la pasada siguiente el
selector de pisos ni siquiera está en pantalla. Lo destapó el guardián en su primera
versión. La clave por cálculo es la forma que tiene Streamlit de reiniciar un widget.

No se probó en producción: calcular manda el correo interno y llama a la IA. Aquí AppTest es
fiable, porque el bucle ocurre en el SERVIDOR. `verif_v530` ejecuta el survey real y simula al
navegador devolviendo el valor de la clave vieja tras recalcular.

29 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v530 | **Elegir otra solución activa ya no deja el survey en un bucle.** Desde el "
        "19/07, elegir cualquier solución que no fuera la recomendada dejaba la página en un "
        "bucle de pasadas SIN FIN (medido con el survey real: >25 pasadas), con diagramas, "
        "plomado e informe cambiando de solución en cada una: la lista se ordenaba con la "
        "ACTIVA primero y la POSICIÓN guardada pasaba a señalar otra. Ahora el orden sale de "
        "la RECOMENDADA y la activa se busca por identidad. ⚠️ Tras «Recalculate», la solución "
        "y los pisos llevan una clave POR CÁLCULO (con `pop` el navegador devolvía la vieja; "
        "asignar antes de pintar, como en v529, no alcanzaba porque el `st.rerun()` corta la "
        "pasada antes). 29 comprobaciones · __BATERIA__ · __SUITE__ |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v529 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v529 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA):
    raise SystemExit('faltan los resultados: doc_v530.py "<suite>" "<bateria>"')
for _k, _v in (("__BATERIA__", BATERIA), ("__SUITE__", SUITE)):
    SECCION = SECCION.replace(_k, _v)
    FILA = FILA.replace(_k, _v)

h = io.open(HIST, encoding="utf-8").read()
unica(h, A_HIST, "cabecera", "HISTORIAL.md")
unica(h, CAB, "tabla", "HISTORIAL.md")
unica(h, TRAS_CAB, "separador", "HISTORIAL.md")
h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v530 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v530 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v530 = actual)")
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
print("CLAUDE.md: fila v530 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
