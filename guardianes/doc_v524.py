# -*- coding: utf-8 -*-
"""Documenta v524 — guardar lo que se propuso y se dejó sin marcar."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"
SUITE = sys.argv[1] if len(sys.argv) > 1 else ""
BATERIA = sys.argv[2] if len(sys.argv) > 2 else ""
REAL = sys.argv[3] if len(sys.argv) > 3 else ""

SECCION = """## GUARDAR LO QUE SE PROPUSO Y SE DEJÓ SIN MARCAR (v524)

Decisión del usuario (29/09/2026), de las tres cosas que v523 dejó sin hacer: **primero
esta** («Dale con 3 y luego 1A, 2B»). Hasta v523 solo quedaba lo ACEPTADO (StageProgress
con origen `log`); lo que la app ofreció y el trabajador dejó sin marcar no estaba en ningún
sitio. Sin eso, «de cada 10 cosas que propone, confirman X» —el número con el que el usuario
decidirá cuándo darle más autonomía— no se puede calcular. ⚠️ Y **no se puede reconstruir
después**: el vocabulario cambia y lo ya acreditado también. `DailyLogs` estaba vacía, así
que se captura desde el primer parte real.

### Qué se guarda
`DailyLogs` gana `Proposals` **al final** (v363). Al revisar —«Confirm» o «Nothing to
credit»— y **en la MISMA escritura** que la revisión (ni una llamada más contra la cuota, y
ningún parte revisado sin registro), `parte_propuestas.registro` guarda en JSON: cada
casilla OFRECIDA con su tipo (`a` propuesta suelta, `e` opción de la lista de una etapa, `q`
opción de una pregunta), su etapa, la actividad y **el término del vocabulario que la
trajo**; lo MARCADO; lo que ya estaba hecho; lo que contestó de «L2»; la obra elegida para
cada ascensor; y la **versión del código** que propuso. ⚠️ «Nothing to credit» se guarda
como NADA aceptado aunque hubiera casillas marcadas: no se acreditaron.

⚠️ `_pintar` anota cada casilla **AL PINTARLA**, no se deduce después: lo guardado tiene
que ser exactamente lo que vio quien confirmó (regla v361). `verif_v524` lo comprueba
ejecutando la tarjeta con AppTest y comparando el registro con las casillas pintadas.

### `acierto`, por TIPO
Una propuesta suelta rechazada es un error de la app; una opción de la lista de una etapa o
de una pregunta queda sin marcar POR DISEÑO. Juntarlas hundiría la cifra sin que la app
hubiera fallado, así que se cuentan aparte. Tope de la celda (50.000 caracteres): primero
se quitan los términos, después solo cuentas, y el recorte queda dicho en el registro.

### ⚠️ El hueco que destapó: `check_anclas_roturas` no leía las constantes
Al cambiar `_pintar` murieron 4 anclas de `romper_v523` — y **nadie avisó**. El chequeo
leía solo LITERALES: una tupla con el fichero en una constante (`UI = "core/…"`, como
escriben `romper_v522` y `romper_v523`) salía con `None` y se saltaba como «rotura
desactivada a propósito», **en silencio**. Trampa nº30: su «0 muertas» valía solo para la
forma que sabía leer. Ahora resuelve las constantes del módulo y las sumas de textos (**442
→ 500** anclas leídas), y lo que sigue sin poder leerse —128 tuplas de 21 baterías viejas
que arman el ancla con `%`, `.join()` o listas— se **declara** con el mismo trinquete que las
muertas: se ve en cada pasada, y una batería NUEVA escrita así pone el chequeo en rojo.
Las anclas de `romper_v516` pasan a una forma que no muere con cada columna nueva (tercera
vez que morían por lo mismo).

### ⚠️ Y un paso en vacío mío
El «registro enorme» de la prueba era tan grande que saltaba directo a «solo cuentas»: el
primer recorte (quitar términos) no se ejercitaba nunca. Redimensionado, con un control de
que sin recortar no cabría.

### Lo que NO hace todavía
No hay pantalla que enseñe el acierto: los datos empiezan a acumularse ahora, y con pocos
partes la cifra no diría nada.

41 comprobaciones · __BATERIA__ · __REAL__ · __SUITE__
"""

FILA = ("| v524 | **Guardar lo que se propuso y se dejó sin marcar.** Decisión del usuario: "
        "primero esto, porque cada parte revisado sin registro es un dato perdido para siempre "
        "(no se puede reconstruir). `DailyLogs.Proposals` al final: lo OFRECIDO (tipo, etapa, "
        "actividad y el término que lo trajo), lo MARCADO, lo hecho, las respuestas de «L2», "
        "las obras elegidas y la versión — en la MISMA escritura que la revisión. «Nothing to "
        "credit» = nada aceptado. `acierto` cuenta por TIPO (una opción de lista sin marcar no "
        "es un error). ⚠️ Destapó que `check_anclas_roturas` saltaba EN SILENCIO las roturas "
        "con el fichero en una constante: 4 anclas muertas de romper_v523 sin aviso; ahora lee "
        "500 (antes 442) y declara las 128 ilegibles. 41 comprobaciones · __BATERIA__ · "
        "__REAL__ · __SUITE__ |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v523 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v523 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and REAL):
    raise SystemExit('faltan los resultados: doc_v524.py "<suite>" "<bateria>" "<hoja real>"')
for _k, _v in (("__BATERIA__", BATERIA), ("__REAL__", REAL), ("__SUITE__", SUITE)):
    SECCION = SECCION.replace(_k, _v)
    FILA = FILA.replace(_k, _v)

h = io.open(HIST, encoding="utf-8").read()
unica(h, A_HIST, "cabecera", "HISTORIAL.md")
unica(h, CAB, "tabla", "HISTORIAL.md")
unica(h, TRAS_CAB, "separador", "HISTORIAL.md")
h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v524 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v524 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v524 = actual)")
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
print("CLAUDE.md: fila v524 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
