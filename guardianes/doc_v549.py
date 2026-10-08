# -*- coding: utf-8 -*-
"""Documenta v549 — los botones parten su texto en vez de recortarlo."""
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

SECCION = """## LOS BOTONES PARTEN SU TEXTO EN VEZ DE RECORTARLO CON «…» (v549)

Streamlit 1.64 añadió `wrap` a los botones, y su defecto (`None`, «decide Streamlit») recorta
en UNA línea la etiqueta de un botón colocado en una columna (trampa nº33): «AC…» por «Active 3»,
«No contact det…», «installer leader CI · 88 wa…» en el Home; «Open workda…» y «Leave …» en
Fichaje. Había ~123 botones en columnas. Decisión del usuario: barrido de una vez.

→ `core/botones.instalar()` (lista `METODOS`; se llamaba `TIPOS` y `verif_v463` la tomó por un valor de negocio) pone `wrap=True` por DEFECTO en toda la app (botón, descarga, envío
de formulario y enlace), y app.py lo llama antes de cualquier botón (el login incluido). Lo
explícito manda: `wrap=False` en la llamada se respeta para una línea a propósito. En vez de
tocar ~123 sitios —y que se escaparan los que nacen en bucles y los futuros—, una sola regla.

- ⚠️ `st.button` es un método LIGADO al DeltaGenerator principal al importar streamlit
  (`button = _main.button`): cambiar la clase no lo alcanza y hay que volver a ligarlo. Las
  columnas, el lateral y los formularios buscan el método en la clase y sí lo ven.
- Idempotente (una marca evita envolver dos veces) y no toca nada si una versión futura de
  Streamlit quita `wrap` (se mira la firma).
- Las celdas del tablero semanal son *popovers*, no botones: no entran (ya llevan su CSS de
  2 líneas, v412); se revisarán al recorrer esa pantalla.

Guardián `verif_v549`, EJECUTANDO botones con AppTest y leyendo lo que recibe el navegador
(`proto.wrap`): la sonda ve el recorte antes de instalar; instalado, los 4 tipos llevan wrap en
columnas y fuera; `wrap=False` se respeta; una sola capa; app.py lo instala antes del primer
botón.

__PROD__ · 12 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v549 | **Los botones parten su texto en vez de recortarlo con «…».** Streamlit 1.64 "
        "recorta en una línea los botones en columnas (`wrap=None`): «AC…», «No contact det…», "
        "«Open workda…». ~123 en la app → `wrap=True` por DEFECTO (`core/botones`, instalado "
        "en app.py; re-liga `st.button`), con `wrap=False` explícito si se quiere una línea. "
        "__PROD__ · __BATERIA__ · __SUITE__ |" + chr(10))

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v548 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v548 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
N_VIEJA = "*Última puesta al día del estado de hecho: 09/10/2026 (v515-v548).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 09/10/2026 (v515-v549).*"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v549.py "<suite>" "<bateria>" "<produccion>"')
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
h = h.replace(A_HIST, "## Versiones desplegadas (v549 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v549 + fila + cabecera")

c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v549 = actual)")
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
print("CLAUDE.md: fila v549 · se cayo %s · %d bytes" % (vieja.strip(), len(c.encode("utf-8"))))

escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v549")
