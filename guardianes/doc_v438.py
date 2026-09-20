"""Añade la sección de v438 a CLAUDE.md + la trampa nº26 (el `\\b` del heredoc)."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = Path(r"C:\Users\diego\P1\CLAUDE.md")
s = p.read_text(encoding="utf-8")

SEC = """## i18n F1c: los DIAGRAMAS y las PLOMADAS. **F1 CERRADO** (v438)

Petición del usuario tras v437: *«adelanta los diagramas y las plomadas, cierra F1»* —
o sea, sacar de F4/F5 lo único que impedía que un documento saliera entero en inglés.
**80 etiquetas** en seis módulos (`plumb`, `diagrams`, `schedule`, `rail_cut`,
`buffer_cut`, `belting`), que son las que se pintan dentro del informe del cliente y de
los cuatro PDF de las herramientas de cálculo.

**Resultado medido en el PDF del cliente: de 37 líneas en español a 0**, salvo los 11
nombres de actividad, que son DATO.

### ⚠️ El motor se importa con ALIAS `_d`, no como `d`
En estos seis módulos `d` ya es una variable corriente —días, dicts, deltas— en **14
sitios**, y Python marca el nombre local en el **ámbito ENTERO** de la función: un
`d = 0` al final del cuerpo revienta las etiquetas de arriba con `UnboundLocalError`.
Es exactamente el fallo del glosario de v437, y renombrar 14 variables es más riesgo
que aliasear el import. El guardián prohíbe importarlo como `d` pelado.

### Lo que NO se traduce, y por qué
| | |
|---|---|
| **Claves** de `schedule_table` / `plumb_table` / `plumb_checks` (11) | las indexan `report.py` y `user_report.py` (`r["Actividad"]`, `r["Línea"]`, `r["Medida"]`) → KeyError o columna vacía |
| **Nombres de las actividades** (`schedule.PHASES`) | son DATO: se guardan en la hoja `Actividades`. Traducirlos dejaría los proyectos viejos en español y los nuevos en inglés, sin forma de casarlos → van con la migración del histórico |
| Claves internas (`origen`, `peso`, `izq`, `der`, `cabina`, `contra`) | banderas, no texto |
⚠️ **Los VALORES sí**: `LINE_NAMES` viaja como valor de la clave `"Línea"`, y ahí sí se
traduce. Verificado antes de tocarlo que **nadie compara** contra esos nombres.

### ⚠️ El barrido ESTÁTICO se dejó cinco restos; los cazó RENDERIZAR
El volcado de literales por AST filtraba cadenas de más de 95 caracteres y su regex
exigía `>texto</text>` **en una sola línea**. Con eso se escaparon cinco etiquetas que
solo aparecieron al generar los SVG y leer su texto:
`FICHA DE REPLANTEO` · el título y el subtítulo de **belting** · el subtítulo y la
leyenda del **Caso 2** de rieles (llevan entidades HTML, `&#183;`). → Un barrido del
FUENTE mide lo que está escrito; solo el barrido de lo RENDERIZADO mide lo que se ve.

### Verificación
`verif_v438.py`, **59 comprobaciones**: claves intactas, actividades en español, alias
`_d` sin tapar, 0 etiquetas en el fuente, y los **11 SVG generados** (planta,
isométrica, 4 de plomada, cronograma, rieles caso 1 y 2, buffers, belting) sin español,
con su texto inglés ESPERADO presente y ⚠️ **sin `<defs>`/`<marker>`**, que svglib no
convierte y haría desaparecer el diagrama del PDF sin ningún error (regla v39).
Probado contra **12 roturas**: las caza las 12 — pero **cuatro solo tras corregirlo**:
- «traducir UN nombre de actividad» pasaba: mi chequeo era un `or` sobre varios, así que
  otro casaba. Y sustituirlo por «cuántos parecen españoles» dio **FALLO con el código
  correcto** (5 de los 11 no llevan ni acento ni palabra funcional: «Brackets /
  soportes»). Se exigen **tres nombres concretos, verbatim**.
- «una etiqueta de plomada vuelve al español» no la veía **nadie**: `LINE_NAMES` no vive
  dentro de un `<text>` y `plumb_svg` usa `LINE_SHORT`. Se comprueban los VALORES que
  las tablas entregan.
- «la leyenda del cronograma vuelve al español» se escapaba porque *Planificado* no
  lleva acento ni palabra funcional → se añadieron chequeos **POSITIVOS** (el inglés
  esperado tiene que estar), y fue justo eso lo que destapó el `FICHA DE REPLANTEO`.
- la rotura del `<marker>` estaba **mal apuntada**: caía en el stub 10×10 px del retorno
  temprano, un camino que el test no dibuja. Una rotura en código que nadie ejercita no
  prueba nada.

### ⚠️ La trampa del `\\b` en el heredoc, POR SEGUNDA VEZ en la misma tanda
El chequeo de los valores de plomada se insertó desde un heredoc de bash, y `\\b` se
convirtió en el **carácter 0x08** (backspace). El regex quedó pidiendo un backspace
literal, así que **no casaba nunca** — y dejó pasar «Plomo riel izquierdo» dando OK.
Es el mismo fallo de v436, cometido otra vez ese mismo día. Se vio con `cat -A`, no
leyendo. → **Cualquier `\\b`, `\\n` o `\\w` va por fichero escrito, nunca por heredoc.**

"""

anc = "## Versiones desplegadas (v437 = actual)"
assert s.count(anc) == 1, f"ancla {s.count(anc)}x"
s = s.replace(anc, SEC + "## Versiones desplegadas (v438 = actual)", 1)

TRAMPA = """26. ⚠️ **Un `\\b` escrito dentro de un heredoc de bash se convierte en el
    carácter 0x08.** El regex queda pidiendo un backspace literal y **no casa
    nunca**, sin dar ningún error: en v436 dejó pasar un texto del Pre-Start en
    español y en v438 una etiqueta de plomada, las dos con un OK en verde. Se ve
    con `cat -A` (`^H`), no leyendo el fichero. → **Todo `\\b`, `\\n` o `\\w` se
    escribe a un fichero con la herramienta de escritura, nunca por heredoc.** Es
    la familia de v429 (los `\\n` escapados que rompieron un guardián dos veces).
27. ⚠️ **Un barrido del FUENTE no mide lo que se ve.** El volcado de literales por
    AST de v438 se dejó **cinco** etiquetas en español: filtraba cadenas de más de
    95 caracteres y exigía `>texto</text>` en una sola línea, así que no vio los
    títulos largos ni los que llevan entidades HTML (`&#183;`). Aparecieron al
    **generar el SVG y leer su texto**. → Para afirmar «no queda nada en X»,
    medirlo sobre la SALIDA, no sobre el código que la produce.

"""
anc2 = "**Y la regla de siempre, que volvió a aplicar:**"
assert s.count(anc2) == 1
s = s.replace(anc2, TRAMPA + anc2, 1)

FILA = """| v438 | **i18n F1c: los DIAGRAMAS y las PLOMADAS — F1 CERRADO** (pedido por el usuario: «adelanta los diagramas y las plomadas»). 80 etiquetas en 6 módulos; el informe del cliente pasa de **37 líneas en español a 0**, salvo los 11 nombres de actividad, que son DATO de la hoja `Actividades`. ⚠️ El motor se importa con **alias `_d`**: en estos módulos `d` ya es variable en 14 sitios y taparía la función en el ámbito entero (el fallo de v437). ⚠️ NO se tocan las 11 CLAVES de `schedule_table`/`plumb_table`/`plumb_checks` (las indexan los informes) — pero sus VALORES sí, tras comprobar que nadie compara contra ellos. ⚠️ **El barrido estático se dejó CINCO restos** (filtraba cadenas largas y exigía el `<text>` en una línea): los cazó **renderizar los SVG y leer su texto**. Guardián de 59 comprobaciones sobre los **11 SVG generados** (incluido que sigan sin `<defs>`/`<marker>`, o svglib los tira del PDF), probado contra **12 roturas** — cuatro solo se cazaron tras corregirlo: un `or` que dejaba traducir un nombre, un umbral que daba **FALLO con el código correcto**, «Planificado» invisible para el detector de español (→ chequeos POSITIVOS, que de paso destaparon un `FICHA DE REPLANTEO`), y una rotura apuntada a un stub que nadie dibuja. ⚠️ Y **la trampa del `\\b` del heredoc por SEGUNDA vez** (v436): 0x08 en el regex → no casa nunca y aprueba en verde |
"""
anc3 = "| v437 | **i18n F1b"
i = s.find(anc3)
assert i > 0
s = s[:i] + FILA + s[i:]

p.write_text(s, encoding="utf-8")
print("CLAUDE.md actualizado con v438 + trampas 26 y 27")
