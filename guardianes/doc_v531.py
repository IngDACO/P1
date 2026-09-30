# -*- coding: utf-8 -*-
"""Documenta v531 — Streamlit fijo a la versión del Cloud (1.64.0), y el local igualado."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"
SUITE = sys.argv[1] if len(sys.argv) > 1 else ""

SECCION = """## STREAMLIT FIJO A LA VERSIÓN DEL CLOUD, Y EL LOCAL IGUALADO (v531)

El usuario pasó los logs del Cloud (29/09 20:11 → 30/09 05:59, hora de Sydney: la v528 en
marcha y la subida de la v529). **Ni un error ni una traza** en casi 10 horas, y ni un
«missing ScriptRunContext»: el heartbeat en segundo plano de v528 no toca Streamlit, como se
diseñó. Lo que sí se repetía decenas de veces:

> `st.components.v1.html` will be removed after 2026-06-01.

La fecha ya pasó, y la app lo usa en **22 sitios de 10 ficheros** (los diagramas del survey,
el plomado, rieles, buffers, belting, el fichaje, la cookie de sesión, la portada y `app.py`).
Y los logs enseñan que **cada reinicio reinstala las dependencias**: con `streamlit>=1.39,<2`,
el día que salga una versión sin esa función, un reinicio cualquiera la instala y esas
pantallas se rompen sin haber cambiado nada nuestro.

### Lo hecho
- `requirements.txt`: **`streamlit==1.64.0`**, la versión que corre en el Cloud (se lee en
  los logs). Subirla pasa a ser una decisión: se prueba la suite con la nueva y se cambia ahí.
- ⚠️ **El local estaba en 1.57.0** (y Python 3.14; el Cloud, 3.12): la suite probaba contra
  una versión 7 menores más vieja que producción — la trampa nº11. Igualado a 1.64.0 (solo
  cambia Streamlit; el resto de dependencias ya cumplía). Repetidas en 1.64 las mediciones de
  v529/v530: el `pop` sigue sin mandar `set_value`, asignar sí, y el `selectbox` se sigue
  identificando solo por su clave.

### ✅ `NEGOCIO.md`, puesto al día por su guardián
La suite con Streamlit 1.64 salió 159 verde y **1 rojo: `check_negocio_al_dia`** — nada de la
versión: el brief declaraba v514 y la app iba por v530, una más que el tope de 15. Es la primera
vez que el guardián de v485 salta de verdad, y funcionó como se diseñó. Puesto al día contra
`HISTORIAL.md` (no de memoria): el parte diario y las propuestas (v516-v525), lo medido en
producción (v528-v530), el riesgo de `components.v1.html`, la decisión del usuario del 27/09
(«el parte diario, sin conexión no, de momento») en su fila de «lo que NO existe» y las cifras
(114 módulos, ~50.000 líneas, 32 hojas, 160 guardianes).

### Pendiente, en una versión aparte
Migrar los 22 usos a `st.iframe` probándolos uno a uno: varios inyectan JavaScript y pueden
comportarse distinto.

__SUITE__
"""

FILA = ("| v531 | **Streamlit fijo a la versión del Cloud (1.64.0), y el local igualado.** Los "
        "logs del Cloud (10 h con la v528): ni un error ni un «missing ScriptRunContext» del "
        "heartbeat en segundo plano. Pero Streamlit avisa que `st.components.v1.html` —22 usos: "
        "diagramas, plomado, rieles…— «will be removed after 2026-06-01», y cada reinicio "
        "reinstalaba la ÚLTIMA versión (`>=1.39,<2`): un reinicio cualquiera podía romper esas "
        "pantallas. ⚠️ El local estaba en 1.57 (trampa nº11): la suite probaba otra versión que "
        "producción. Migrar a `st.iframe`, aparte. __SUITE__ |\n")

LINEA_ENTORNO = ("- **Streamlit va FIJO (`==1.64.0`, v531)**, la versión del Cloud: con un rango, cada "
                 "reinicio reinstala la última y `st.components.v1.html` (22 usos) ya está "
                 "anunciado para quitarse. **El local tiene que estar en la misma** (en v531 estaba "
                 "en 1.57): la suite prueba lo que tenga instalado.\n")
A_ENTORNO = "- **`requirements.txt` va PINEADO** con topes de major"

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v530 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v530 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not SUITE:
    raise SystemExit('falta el resultado: doc_v531.py "<suite>"')
SECCION = SECCION.replace("__SUITE__", SUITE)
FILA = FILA.replace("__SUITE__", SUITE)

h = io.open(HIST, encoding="utf-8").read()
unica(h, A_HIST, "cabecera", "HISTORIAL.md")
unica(h, CAB, "tabla", "HISTORIAL.md")
unica(h, TRAS_CAB, "separador", "HISTORIAL.md")
h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v531 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v531 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
unica(c, A_ENTORNO, "entorno", "CLAUDE.md")
# La linea nueva va DETRAS del parrafo de requirements (que acaba en la linea siguiente).
_i = c.index(A_ENTORNO)
_fin = c.index("\n- ", _i + 1) + 1
c = c[:_fin] + LINEA_ENTORNO + c[_fin:]
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v531 = actual)")
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
print("CLAUDE.md: fila v531 + linea de entorno · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
