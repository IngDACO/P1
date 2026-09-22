# -*- coding: utf-8 -*-
"""Documenta v514 — el campo marca QUÉ hizo, no cuánto cree que va."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"

SECCION = """## EL AVANCE POR ACTIVIDAD (v514)

Segunda mitad de F0, y la que hace que el catálogo de v512 deje de ser una estructura y
empiece a medir. Hasta aquí las obras nacían con sus 14-18 etapas pero el avance se
seguía **tecleando**: el campo movía un porcentaje a ojo. Ahora marca **qué hizo** y el
número sale ponderado por lo que pesa cada cosa.

    avance de la etapa = Σ(peso de la actividad × su %) / Σ(peso de sus actividades)

### ⚠️ La hoja es DISPERSA, y es lo que lo hace viable
`StageProgress` solo tiene fila para lo que se ha acreditado. Una instalación tiene
**143 actividades**: crearlas todas al dar de alta serían 143 escrituras por obra y
miles de filas vacías. La lista completa ya vive en el catálogo, que no cuesta nada; la
hoja lleva solo lo que pasó.

### ⚠️ El número sigue viviendo en `Activities.Progress`
Lo tentador era calcular el % de la etapa al vuelo y no guardarlo. Sería un segundo
número diciendo lo mismo que la rejilla (regla v361) y, peor, **todo lo de abajo lee esa
columna**: `compute_avance`, la curva S real, el SPI, la cadena de v500, la línea base de
v501 y al final la reclamación que se cobra (v507/v510).

Lo que cambia no es dónde está el dato: es **quién lo escribe**. Y la escritura se delega
en `projects.save_field_progress`, que ya hace el lote en una llamada y pone solas las
fechas reales (v162) — reusarla es también no duplicar esa lógica.

### ⚠️ Casillas, no porcentajes
Casi todas las actividades son binarias: el bedplate está instalado o no. Pedir un % de
cada una en un móvil con 143 sería peor que la rejilla que se viene a quitar. Lo parcial
—«8 puertas de 10»— llega con el parte diario, donde el número está en la frase.

Regla escrita mientras tanto: **media actividad cuenta como no hecha**. Quedarse corto
solo retrasa una reclamación; inflar el avance la mueve.

### ⚠️ Un hueco que v512 dejó abierto y aquí se cierra
El plan sella la **versión** del catálogo, pero el catálogo vive en el código y solo hay
una versión: nada impedía añadir una etapa mañana y que una obra creada ayer se midiera
contra un menú distinto. Los órdenes se desplazan, el crédito se cuelga de **otra
etapa** y el avance sale mal **sin un solo error**. Ahora se detecta y **se niega a
escribir**, dejando la obra en solo lectura con el aviso. Leer sí: esconderla sería peor.

### ⚠️ Toda obra anterior a v512 sigue igual
Sin `StagePlanJSON` no hay contra qué acreditar, así que la pantalla del campo **cae a
la rejilla de siempre**. El día del despliegue la cartera existente no se entera de nada.

### Dos fallos que encontró el método, no la lectura del código
**1. Recalcular releyendo la hoja.** El guardián dio un rojo que en producción habría
funcionado —`acreditar` escribe, invalida y relee—, así que era tentador descartarlo
como artefacto del test. Mirándolo, el diseño era peor: una lectura extra por cada
acreditación (con el techo de 60/min que ya mordió en v511) y la corrección atada a que
la invalidación hubiera funcionado. Lo que se acaba de escribir ya se sabe: ahora se
calcula en memoria y no se le pregunta a Google.

**2. `delete_project` dejaba créditos huérfanos.** Viven en otra hoja, así que borrar una
obra los dejaba apuntando a algo inexistente: no da error, ensucia el libro para siempre.
⚠️ Y lo peor es que **el propio ejercicio lo estaba tapando** — los limpiaba a mano para
que la foto final cuadrara. Se quitó ese apaño: ahora el ejercicio **comprueba** que el
código los borra. Un test que arregla lo que debería verificar no verifica nada.

### ⚠️ Dos agujeros en el guardián, cazados por la batería
Uno **reventaba** al guardián con `ZeroDivisionError` en vez de ser denunciado —sexta vez
con ese patrón en este proyecto— y la primera corrección envolvió solo UNA de las dos
llamadas que dividían, así que el reventón seguía saliendo de la de al lado. El otro
**pasaba por el motivo equivocado**: sin plan, la lista de actividades válidas queda
vacía, así que el rechazo llegaba igual pero por «no está en el plan»; comprobar solo
`False` no protegía lo que decía proteger.

⚠️ Y el CONTROL de la batería nació **vacío**: ponía el mismo texto a los dos lados, o
sea que no cambiaba nada y pasaba sin probar nada. Un control vacío es peor que no
tenerlo, porque parece cobertura.

### Verificación
`verif_v514.py`, **52 comprobaciones**, con la hoja sustituida por una de mentira que se
queda con lo escrito (sin ejercitar la ESCRITURA, las roturas que importan se escapan —
la lección de v510). Batería: **15 roturas, 15 cazadas + CONTROL**. Suite: **146 verde**.

⚠️ `verif_v465` se puso rojo y tenía razón: toda hoja necesita respaldo de nombre, o un
libro con el nombre viejo haría que la app se fabricara una pestaña VACÍA. `StageProgress`
nació en inglés y nunca tuvo nombre español, así que va a la lista de excepciones
**declaradas** junto a `Library` (v472) y `XeroConnections` (v488), con su razón escrita.

**Ejercitado contra la HOJA REAL** (método v344): la hoja se creó sola, tres actividades
acreditadas dieron **42%** en la etapa 6 (17+13+12, los pesos exactos), el número llegó a
`Activities.Progress` **con la fecha real puesta sola**, el avance de la obra subió al
**5,5%** (la etapa 6 pesa 13 de 100), desmarcar una lo bajó a **29%** dejando el rastro a
0, y `delete_project` se llevó los créditos. Cartera devuelta a sus 2 obras.
"""

FILA = ("| v514 | **El avance por actividad: el campo marca QUÉ hizo.** Segunda mitad de F0 — el "
        "catálogo de v512 deja de ser una estructura y empieza a medir. Hasta aquí el avance se "
        "TECLEABA a ojo; ahora se marcan actividades reales y el % sale ponderado por lo que pesa "
        "cada una. ⚠️ La hoja es **dispersa** (solo lo acreditado): con 143 actividades por obra, "
        "crearlas todas serían miles de filas vacías. ⚠️ El número **sigue viviendo en "
        "`Activities.Progress`**, que es lo que leen la curva S, el SPI, la cadena de v500 y la "
        "reclamación que se cobra — lo que cambia es **quién lo escribe**. ⚠️ Cierra un hueco de "
        "v512: si el catálogo cambia, el crédito se colgaría de otra etapa, así que se detecta y se "
        "niega a escribir. ⚠️ Dos fallos que encontró el método: recalcular releyendo la hoja (peor "
        "diseño, no bug) y `delete_project` dejando créditos huérfanos — **que mi propio ejercicio "
        "estaba tapando** limpiándolos a mano. ⚠️ Y dos agujeros del guardián: uno lo REVENTABA en "
        "vez de denunciar y otro acertaba por el motivo equivocado. 52 comprobaciones · **15/15 + "
        "control** · suite 146 verde |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v513 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v513 = actual)"
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
h = h.replace(A_HIST, "## Versiones desplegadas (v514 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v514 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v514 = actual)")
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
print("CLAUDE.md: fila v514 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
