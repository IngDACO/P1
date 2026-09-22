# -*- coding: utf-8 -*-
"""Documenta v513 — los pesos guardados vuelven a sumar 100."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"

SECCION = """## LOS PESOS QUE SE GUARDAN (v513)

Arreglo de v512, encontrado **ejercitando contra la hoja real** inmediatamente después
de desplegarla — no por el guardián.

Al crear una obra, los pesos que quedaban escritos en `Activities` sumaban **99,8**
(instalación, 14 filas) o **99,9** (combinada, 18 filas), no 100. `build_schedule`
normalizaba y redondeaba **cada peso a un decimal por su cuenta**, y con catorce o
dieciocho actividades los redondeos no se compensan.

### Por qué importaba aunque el avance estuviera bien
`compute_avance` es Σ(peso·avance)/Σpeso, o sea **escala-invariante**: con pesos que
suman 99,8 el porcentaje sale exactamente igual. El avance nunca estuvo mal.

Lo que estaba mal es **la columna que mira el usuario**. Un plan cuyos pesos no suman
100 invita a buscar un error que no existe, y en la pantalla donde se reparte el
esfuerzo de una obra eso no es un detalle cosmético: es minar la confianza en el número
que luego se reclama.

### ⚠️ Dónde vivía: en la frontera entre dos capas
`verif_v512` comprobaba que los pesos sumaran 100 — pero los de **`filas_de_etapas`**,
que son exactos. El desvío aparecía en lo que **`build_schedule` escribe**, una capa más
abajo. Comprobar una capa y dar por buena la siguiente es la misma familia que el paso
en vacío: cada una estaba bien por separado y el resultado no.

Por eso lo encontró el ejercicio contra la hoja real y no la suite. Es, otra vez, la
lección de v511: **hay fallos que solo aparecen tocando lo real**.

Arreglado repartiendo el resto (misma técnica que las duraciones de v512), verificado en
los tres tipos × seis números de paradas, y con rotura propia en la batería: **22/22**.
⚠️ De paso cuadra también el camino viejo de `PHASES`, que arrastraba el mismo desvío y
alimenta el informe del survey.

### ⚠️ Y un guardián viejo cazó otro fallo mío
`verif_v438` denunció que la comprensión nueva usaba `_d` como variable descartable, y
`_d` es la función de display de i18n a nivel de módulo. En una comprensión **no se
filtra** (tiene ámbito propio), así que no era un fallo real — pero es exactamente el
patrón que tumbó v439 y v503 donde sí se filtra. Renombrado, con la razón escrita.

Van **tres fallos propios cazados por guardianes viejos** en esta tanda:
`check_nombres_libres` con un `_num` que no existía en `projects_ui`, `verif_v448/v449`
con dos mensajes en español, y este. Ninguno se habría visto leyendo el código.

### Verificación
`verif_v512.py` pasa de 86 a **88 comprobaciones** (las dos nuevas miran los pesos
GUARDADOS, en la capa donde estaba el fallo). Batería: **22 roturas, 22 cazadas +
CONTROL**. Suite: **145 verde · 0 rojo · 0 roto**.

**Ejercitado contra la HOJA REAL** (método v344, `ejercitar_v512_real.py`): se crea una
obra de cada tipo y se lee de vuelta. Instalación **14 etapas** (fin 03/11, la misma
fecha que daba el modelo viejo), combinada **18** con el desmontaje delante, rip-out
solo **4**, y ⚠️ un *Delivery* sigue naciendo con **UNA** actividad y sin plan — el
cambio no se derramó a donde no debía. Las cuatro obras borradas y la hoja devuelta a
sus 2 obras y 17 actividades.
"""

FILA = ("| v513 | **Los pesos que se guardan vuelven a sumar 100.** Arreglo de v512 encontrado "
        "ejercitando contra la hoja REAL justo después de desplegarla: los pesos escritos en "
        "`Activities` sumaban **99,8** con 14 actividades. El avance nunca estuvo mal —"
        "`compute_avance` divide por Σpeso y es escala-invariante— pero **la columna que mira el "
        "usuario mentía**, y un plan que no suma 100 invita a buscar un error que no existe. ⚠️ El "
        "fallo vivía **en la frontera entre dos capas**: el guardián comprobaba los pesos de "
        "`filas_de_etapas` (exactos) y el desvío nacía en lo que `build_schedule` escribe. Cada capa "
        "bien por separado y el resultado mal — por eso lo encontró la hoja real y no la suite. ⚠️ Y "
        "`verif_v438` cazó otro fallo mío de paso: una comprensión usaba `_d`, que es la función de "
        "display de i18n (no se filtra en una comprensión, pero es el patrón de v439/v503). Tres "
        "fallos propios cazados por guardianes viejos en esta tanda. 88 comprobaciones · **22/22 + "
        "control** · suite 145 verde |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v512 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v512 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


h = io.open(HIST, encoding="utf-8").read()
unica(h, A_HIST, "cabecera", "HISTORIAL.md")
unica(h, CAB, "tabla", "HISTORIAL.md")
unica(h, TRAS_CAB, "separador", "HISTORIAL.md")
h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v513 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v513 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v513 = actual)")
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
print("CLAUDE.md: fila v513 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
