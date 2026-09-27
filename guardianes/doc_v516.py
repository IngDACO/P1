# -*- coding: utf-8 -*-
"""Documenta v516 — el parte diario en texto libre."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"

SECCION = """## EL PARTE DIARIO EN TEXTO LIBRE (v516)

F1 de lo que pidió el usuario: que el campo escriba lo que hizo y un agente lo cargue en
el cronograma. Esto es **la primera mitad y solo la primera**: texto con obra, fecha y
autor. No interpreta, no mueve el avance, no toca ninguna actividad.

### ⚠️ Por qué el texto va ANTES que la IA
Empezar por la interpretación obliga a probarla con frases que me invente yo, y una frase
inventada por quien escribe el intérprete **acierta siempre**. Es la trampa nº1 en su
forma más cara: un corpus de mentira da una precisión de mentira. Con esto desplegado, el
corpus crece cada día **con el vocabulario real de los instaladores** — las abreviaturas,
el orden en que cuentan las cosas, qué dan por supuesto.

⚠️ Y vale por sí solo aunque la IA no llegara nunca: hoy ese parte se da por WhatsApp o no
se da, y no queda en la obra.

### Tres decisiones
**El borrador no se pierde si falla el guardado.** La caja **solo** se vacía cuando la
hoja confirma. Alguien que escribe doscientas palabras en un sótano y las ve desaparecer
no las reescribe: deja de usar la pantalla. Y el error dice la verdad
(`timeclock.motivo_sin_hoja`, v511), no «no está configurado» cuando es la cuota.

**Se AÑADE, no se edita.** Cada guardado es una entrada nueva; se puede borrar **la
propia y del día**, no la de la semana pasada. Lo único que hace valioso a esto es que
sea *lo que alguien dijo que hizo ese día*.

**El parte va FUERA de Avance.** En Avance se marca lo hecho contra el catálogo; aquí se
cuenta el día, incluido lo que el catálogo **no tiene casilla para recoger**: una espera,
un acceso cerrado, material que no llegó. Dentro, el texto habría parecido opcional al
lado de las casillas.

### ⚠️ El fallo que solo salió contra la hoja REAL
Los dos partes de prueba se escribieron **en el mismo minuto**. `Created` guardaba
`hh:mm`, así que empataban; `sorted` es estable y el empate dejaba **el más viejo
arriba**. El guardián no lo vio porque **yo le di horas distintas a mano** — el test con
datos que me invento, otra vez.

⚠️ Y había una segunda capa: mi reloj de mentira devolvía una cadena fija en vez de
formatear, así que el código podía pedir segundos y el guardián nunca se enteraba. **Un
stub que miente sobre su contrato hace que el guardián mida al stub.** Arreglado en las
dos mitades (segundos en `Created` **y** el ID de desempate), con una rotura para cada
una: arreglar solo una dejaba el fallo vivo la mitad de las veces.

### Cuatro rojos en la suite, y ninguno era lo mismo
**Dos eran fallos míos, cazados por guardianes viejos antes de desplegar.** `verif_v472`:
`theme.section` **escapa** su texto, así que mis cabeceras habrían pintado
`:material/edit_note: Daily log` **literal** en pantalla — no es una etiqueta de widget,
es HTML. `verif_v468`: tres lecturas crudas sin canonizar, que es la regla que hace que un
libro con cabeceras viejas siga casando.

**Uno era el guardián acusando a código sano.** `verif_v311` da por libre todo nombre que
no sea un `ast.Name`, y `except Exception as e` liga `e` como **atributo del handler**.
Los otros once `except ... as e` del módulo estaban fuera de esa función, así que nunca
había mordido. Es la misma familia que la nota de v502 escrita tres líneas más arriba **en
el mismo guardián**, y la trampa nº3.

**Y uno fue `check_anclas_roturas` cazándome a mí**, el mismo día en que nació: un ancla
muerta en **mi propia batería de v516**, porque el arreglo del empate cambió el formato y
el ancla seguía diciendo `%H:%M`. La batería la contaba como «??» mientras anunciaba **19
de 19** — una batería no avisa de sus anclas muertas, solo las salta.

### Verificación
`verif_v516`, **58 comprobaciones**, con la hoja sustituida por una que se queda con lo
escrito. Batería: **19 roturas, 19 cazadas + CONTROL** — dos escaparon primero, una porque
no ejercitaba la rama de «no hay hoja» y otra porque medía el literal en el FICHERO y el
mismo texto sobrevive en el `format_func` de al lado (trampa nº2 y nº30 a la vez).

**Ejercitado contra la HOJA REAL** (método v344): la hoja se creó sola, el parte se leyó
de vuelta **por el lote** (que es como lee la app, no como escribe el guion), dos partes
del mismo día quedaron como dos entradas y **un día** de corpus, borrar el propio del día
funcionó y el de otro no, y `delete_project` se llevó los partes sin dejar huérfanos.
Cartera devuelta a sus 2 obras. Suite: **148 verde**.
"""

FILA = ("| v516 | **El parte diario en texto libre: el campo cuenta el día en sus palabras.** F1 de lo "
        "que pidió el usuario, y **solo la primera mitad**: texto con obra, fecha y autor, sin IA. "
        "⚠️ El texto va ANTES que el intérprete porque probarlo con frases que yo me invente **acierta "
        "siempre** (trampa nº1): desplegado esto, el corpus crece con el vocabulario REAL de los "
        "instaladores. ⚠️ La caja **solo se vacía si la hoja confirmó** — quien escribe 200 palabras en "
        "un sótano y las ve desaparecer no vuelve. ⚠️ Se **añade, no se edita**: borrar solo lo propio y "
        "del día, porque el valor es que sea *lo que alguien dijo que hizo ese día*. ⚠️ Va FUERA de "
        "Avance: ahí se marcan casillas del catálogo, aquí cabe lo que el catálogo no recoge (esperas, "
        "accesos, material). ⚠️ **El fallo lo encontró la hoja REAL**: dos partes del mismo MINUTO "
        "empataban en `Created` y salían al revés — y mi reloj de mentira devolvía una cadena fija, así "
        "que **el guardián medía al stub**. ⚠️ Cuatro rojos en la suite: dos fallos míos cazados por "
        "guardianes viejos (un icono que se habría pintado literal, tres lecturas sin canonizar), uno "
        "del guardián acusando código sano (`except ... as e` no es un `ast.Name`) y uno de "
        "`check_anclas_roturas` **cazando un ancla muerta en mi propia batería el día que nació**. "
        "58 comprobaciones · **19/19 + control** · 17/17 hoja real · suite 148 verde |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v515 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v515 = actual)"
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
h = h.replace(A_HIST, "## Versiones desplegadas (v516 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v516 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v516 = actual)")
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
print("CLAUDE.md: fila v516 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
