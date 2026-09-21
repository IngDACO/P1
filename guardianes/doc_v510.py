# -*- coding: utf-8 -*-
"""Documenta v510 — el PDF de la reclamación y la liberación de la retención."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"

SECCION = """## EL PDF DE LA RECLAMACIÓN Y LA LIBERACIÓN DE LA RETENCIÓN (v510)

Cierra el flanco que quedó abierto en v507-v508. Aquello dejó los **números** —contrato,
variaciones, avance, bruto, retención, neto— pero no el **documento que se le manda al
cliente**, así que el contratista seguía armando su reclamación mensual en Excel. Es
exactamente el dolor que el estudio del 20/09/2026 identificó como el que aparece
*después* de que el cliente ya está dentro. Media función promete y no entrega.

### Qué hay
`core/claim_pdf.py` (nuevo): una página A4 con la identidad fiscal del emisor (v483),
el cliente, la obra, y el cálculo de arriba abajo hasta el **neto a pagar**. Dos
documentos con un solo generador: `PROGRESS CLAIM` y `RETENTION RELEASE`.

⚠️ **Las variaciones van DETALLADAS una a una**, y solo las aprobadas. Una reclamación
que dice «valor de contrato ajustado: 128.400» le pide al cliente que pague contra un
número que no puede comprobar; enumerarlas la hace discutible línea a línea. Y meter una
*propuesta* sería reclamar lo que nadie aceptó (regla v507).

⚠️ **El PDF no recalcula NADA**: todas las cifras salen de la fila congelada. Si
recalculara, cambiar el % de retención del grupo reescribiría documentos ya enviados.
Hay un chequeo por AST de que no llama ni a `calcular` ni a `retenido`.

⚠️ **No invoca ninguna ley, y es a propósito.** Una reclamación bajo *Security of
Payment* tiene que declararlo, pero el texto y sus efectos cambian por estado (NSW, VIC
y QLD no piden lo mismo) y declararlo mal tiene consecuencias legales. Lo pone quien
sepa, en la nota, que viaja íntegra. Es el criterio de v506 —la app no certifica
cumplimiento de nada— y hay un guardián que vigila que el módulo no se lo invente.

### La liberación de la retención
Columna **`Type`** al final de `Claims` (v363): vacío = reclamación de avance,
`retention_release` = liberación. Las dos viven en la MISMA hoja porque las dos piden
dinero: separarlas obligaría a dos series de numeración y el cliente recibiría dos «nº 3».

⚠️ **Una liberación no retiene nada** (`Retention` 0, el importe en `ThisClaim`), así que
`neto = ThisClaim − Retention` sigue valiendo para las dos sin un solo `if` en la
pantalla. Y ⚠️ **no mueve la base de trabajo ejecutado**: repite las cifras de la última
reclamación en vez de escribir un 0 que luego se leería como que la obra retrocedió.

⚠️ **Parcial a propósito**: en obra australiana la retención se devuelve en **dos
mitades** —una en *practical completion* y otra al acabar el periodo de defectos, meses
después—, así que un «todo o nada» no serviría para el caso normal.

⚠️ Tres cosas que NO se pueden hacer: liberar **más de lo retenido** (eso no es una
liberación, es una factura), liberar con la **obra a medias**, y liberar cuando el avance
**no se pudo leer** — ante la duda no se libera, porque tratar un fallo de lectura como
«está terminada» es lo que v492 prohibió. Cuando no se puede, el bloque sigue a la vista
**con el motivo**: esconderlo haría que una función que existe pareciera no existir (v505).

### ⚠️ La batería dejó escapar CINCO roturas, y eran las caras
Primera pasada: **7 de 12**. Lo que escapó —liberar de más, liberar con la obra a medias
por un fallo de lectura, que la liberación retuviera un 5%, que moviera la base de
trabajo— vivía todo en el camino de **escritura**, y el guardián solo ejercitaba la
aritmética de **lectura**: comprobaba mis propias filas de ejemplo, no lo que el código
escribe. La trampa nº1 dentro del propio guardián.

Y una escapó por un motivo más fino: el objeto que simulaba «no se puede leer el avance»
era un `dict` **vacío**, o sea *falsy*, así que `prj or get_project(pid)` lo descartaba y
el `except` no se ejecutaba nunca. El chequeo pasaba en verde sin tocar ni una línea de
lo que decía proteger.

La quinta: el filtro que ignora la retención de una liberación **no se podía distinguir**
con filas limpias, porque el código escribe `Retention` 0 y quitar el filtro no cambia
nada. Hizo falta una fila **sucia** —una liberación con retención— que es justo de lo que
el filtro protege.

Con la hoja sustituida por una de mentira que se queda con la fila escrita, el guardián
pasó de **38 a 56 comprobaciones** y la batería a **12/12 + CONTROL**.

### ⚠️ Y el extractor del PDF también pasó en vacío
La primera sonda descomprimía los flujos del PDF a mano con zlib y devolvía **cero** con
el texto perfectamente puesto: el regex de `stream…endstream` no casaba. Todas las
afirmaciones de contenido pasaban en vacío y las **negativas** («no mete la propuesta»)
pasaban por partida doble. Lo delató el único chequeo que importaba —*que la sonda sepa
leer el caso conocido-bueno*—, que es la trampa nº12. Se cambió a **pypdf**, que ya es
dependencia y es lo que la app usa para leer planos.

### Verificación
`verif_v510.py`, **56 comprobaciones**. Batería: **12 roturas, 12 cazadas + CONTROL**.
Suite completa: **144 verde · 0 rojo · 0 roto**.

**Ejercitado contra la HOJA REAL** (método v344): la columna se creó sola (**18 → 19**,
al final), una reclamación sembrada se leyó de vuelta con `Type` vacío y **no** como
liberación, `crear_liberacion` escribió de verdad («*Retention release 2: net payable
1200.00*»), se leyó de vuelta **como liberación**, y la aritmética sobre datos reales dio
**retenido 3.000 · liberado 1.200 · pendiente 1.800**. Los dos PDF se generaron desde
filas de Sheets —todo en texto— y las dos filas se borraron: la hoja quedó en 0.

⚠️ **La primera versión del ejercicio terminó en «TODO OK» sin probar nada**: la hoja real
tiene cero reclamaciones, así que los dos apartados que importaban se saltaban enteros.
Un verde que solo significa «no había datos» es el paso en vacío otra vez.
"""

FILA = ("| v510 | **El PDF de la reclamación y la liberación de la retención.** v507-v508 dejó los "
        "números pero no el papel que se le manda al cliente, así que la reclamación mensual se "
        "seguía armando en Excel — el dolor que el estudio identificó como el que aparece cuando el "
        "cliente ya está dentro. Un generador para dos documentos, con las **variaciones aprobadas "
        "detalladas una a una** (un total que el cliente no puede comprobar no es discutible) y ⚠️ "
        "**sin recalcular nada**: las cifras salen de la fila congelada. ⚠️ **No invoca ninguna ley** "
        "—el texto de *Security of Payment* cambia por estado y declararlo mal tiene efectos "
        "legales—: lo pone quien sepa, en la nota (criterio v506). Retención: columna `Type` al final "
        "(v363), liberación **parcial** porque en AU va en dos mitades, ⚠️ nunca más de lo retenido, "
        "ni con la obra a medias, ni con el avance ilegible. ⚠️ **La batería dejó escapar 5 de 12 a la "
        "primera**, todas en el camino de ESCRITURA que el guardián no ejercitaba —y una porque mi "
        "objeto de prueba era un dict vacío, *falsy*, que el código descartaba antes de llegar al "
        "`except`—; y el extractor del PDF devolvía cero con el texto puesto, así que las "
        "afirmaciones negativas pasaban por partida doble. 38 → **56 comprobaciones** · **12/12 + "
        "control** · suite 144 verde |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v509 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v509 = actual)"
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
h = h.replace(A_HIST, "## Versiones desplegadas (v510 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v510 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v510 = actual)")
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
print("CLAUDE.md: fila v510 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
