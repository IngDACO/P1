# -*- coding: utf-8 -*-
"""Documenta v469 en CLAUDE.md: seccion propia + fila de la tabla + cabecera."""
import io

P = r"C:\Users\diego\P1\CLAUDE.md"
s = io.open(P, encoding="utf-8").read()

SECCION = """## Los VALORES pasan a inglés (v469) — y los DOS fallos que escondía

Última capa de «todo en inglés» (v465 hojas · v467 carpetas de Drive · v468 columnas).
Aquí el fallo no es una pantalla en blanco ni una columna vacía: **una comparación que
deja de casar es una rama MUERTA, y no da ningún error**.

### El diseño, igual que en las columnas: canonizar al LEER
`core/valores.py` (módulo HOJA, **61 pares**) y `hojas.registros` traduce el valor viejo
al canónico, así que el código ve el nombre nuevo tenga el libro el viejo o el nuevo.
Eso es lo que permite desplegar ANTES de migrar la hoja.
⚠️ **Lista blanca por (HOJA, COLUMNA), nunca por nombre de columna suelto**: `proyecto`
es a la vez el tipo de FICHAJE (`Sheet1.Type`) y un valor de `UBIC_TIPOS`
(`Assets.LocationType`).

### ⚠️ FALLO 1: `Sheet1.Type` se quedó fuera de la lista blanca
`TIPO_PROYECTO` pasó a `"project"` y la pareja **no** se añadió, así que las ~500 filas
del histórico seguían diciendo `proyecto`, se leían sin canonizar y
`_tipo_of(r) == TIPO_PROYECTO` era **falso para todas**: ni una hora imputada a una obra
contaba como tal. Eso es la nómina, el costo de obra, la conciliación de v313 y el
reparto por proyecto, **todo a cero**, en lo que más se usa de la app. Sin un error.

⚠️ **Y el guardián de v469 estaba PROTEGIENDO el fallo.** Su bloque 2 exigía que
`Sheet1.Type` quedase FUERA — cierto cuando lo escribí, porque entonces la constante
todavía era `proyecto` y canonizar esa columna sí rompía el fichaje. Al migrar la
constante la conclusión se invirtió y el guardián no se enteró, así que **hacerle caso
al rojo sin mirar el código acusado habría reintroducido el fallo**. Es la regla v385
en su forma más incómoda: *el acusado tenía razón y el acusador no.*

Y los dos barridos que escribí para buscar justo esto **tampoco lo vieron**: el primero
comparaba por NOMBRE de columna —y `Type` ya estaba en la lista, para `Projects`—, así
que daba la pareja por cubierta; el segundo, ya por pareja, solo miraba constantes que
son LISTA, y `TIPO_GENERAL`/`TIPO_PROYECTO` son **sueltas**. **Un chequeo que mide por
el nombre cuando la unidad es la pareja aprueba justo el caso que busca.**

### ⚠️ FALLO 2: `estado_cobro` devolvía una MEZCLA
De sus cinco ramas, v469 migró **una**: devolvía `anulada`, `cobrada`, `vencida` y
`parcial` en español y `pending` en inglés. Como la clave de `invoices_ui._EST_FMT` es
justo lo que devuelve esa función, `pending` no se encontraba y **la factura salía sin
icono ni color, con el texto crudo**. Traducción a medias dentro de la misma función: el
peor caso (v443/v450).

Se **revierte** esa rama en vez de migrar las otras cuatro. Las facturas se quedan en
español de punta a punta —la columna `Invoices.Status`, las 5 comparaciones
`== "vencida"` y el mapa de chips—, `(Invoices, Status)` **no** está en la lista blanca,
y la pantalla ya lo traduce con `_est_fmt()` y `etiqueta()`. Migrar cuatro ramas más al
cierre de una versión que ya toca 32 ficheros es como se cuelan los fallos silenciosos.

### ⚠️ Y la red que buscaba mezclas era CIEGA a este caso exacto
La construí sobre `valores.LEGADO` (61 pares, lo que v469 migró) y dio **0 mezclas con
la mezcla delante**: los cuatro estados españoles de facturas **no están en el mapa de
migración**, así que el lado «sin migrar» salía vacío. Un valor migrado FUERA de ese
mapa es justo donde una traducción a medias duele, y una red hecha con el mapa de
migración no puede verlo. Rehecha sobre **`i18n.VALORES`** (el vocabulario completo, 81
pares) sí lo ve. **Solo lo destapó validar la sonda contra un caso conocido-bueno**
(trampa nº12); el guardián la valida él mismo antes de creerse su cero.

### `i18n.VALORES` no queda obsoleto: pasa a ser el LEGADO del display
Mapeaba español→inglés para MOSTRAR. Con el dato ya en inglés, `etiqueta()` devuelve el
canónico tal cual **y sigue traduciendo la fila sin migrar** — la misma compatibilidad,
del otro lado. Verificado que `valores.LEGADO` e `i18n.VALORES` coinciden en los **60
pares comunes, 0 discrepancias**: si difirieran, una fila migrada y una sin migrar
acabarían con dos ortografías del mismo estado.
De paso se añadió `otro → other`, que faltaba: se guarda en `Assets.LocationType`, así
que una fila anterior a la migración saldría cruda (el fallo de v462/v463 — un valor que
no está en el mapa se devuelve tal cual, sin error).

### Lo que NO se migra, con su razón
| | Por qué |
|---|---|
| **`payroll.TIPOS`** (`devengo`/`deduccion`/`aporte`) | no viven en una columna sino **dentro de `ConceptsJSON`**: migrarlos obliga a reescribir el JSON de cada nómina del histórico. Es migración de datos, no traducción — la clase de `schedule.PHASES` (v448/v453). ⚠️ Verificado que la constante, las escrituras y las comparaciones siguen **las tres** en español: media traducción aquí dejaría de restar las deducciones del neto, en silencio (v447) |
| **Facturas y nóminas** (`anulada`, `pagada`, `cobrada`…) | coherentes de punta a punta y fuera de la lista blanca |
| **`m` · `m²` · `kg`** | son símbolos, iguales en los dos idiomas; un mapa espejo es lo que v450 mandó borrar |
| **`OFF` · `LEAVE` · `FORMACION`** | claves reservadas del tablero, no texto |
| **`general`** | ya es palabra inglesa y la pantalla dice «workday» por `t()`; migrarla obligaría a reescribir el `Type` de las ~500 filas del fichaje a cambio de nada |

### Los 8 guardianes que afirmaban «el DATO sigue en español»
Caducados por un cambio deliberado, **invertidos con la razón escrita al lado**, nunca
relajados (regla v385). La afirmación cambia de objeto y no de principio: lo guardado y
lo mostrado no pueden divergir. Cada uno exige ahora tres cosas —el valor que se GUARDA
es el canónico, la fila SIN migrar sigue casando, y `etiqueta()` no muta un valor que ya
es canónico— y `verif_v445` lleva **el chequeo que habría cazado el fallo 1**,
ejercitando `_tipo_of` sobre una fila vieja y una nueva.

### Verificación
`verif_v463` gana la red de mezclas (que se auto-valida) y un chequeo de ramas muertas.
⚠️ Ese último dio un **FALLO inexistente** al primer intento: buscaba la comparación por
TEXTO y encontró **mi propio comentario** —el que explicaba por qué el valor no se
traducía—, trampa nº2 otra vez. Se quitan comentarios con `tokenize`; y el comentario,
que ya mentía sobre el código, se actualizó (es el caso del comentario de
`use_container_width` en v405). Lo mismo con el docstring de `inventory.alertas`.
⚠️ Un barrido de comentarios que nombran un valor migrado da **400 falsos positivos**
(claves internas y los propios mapas, que por definición nombran el viejo): se descarta
—un detector que grita sobre lo que está bien acaba ignorándose (v450)— porque el riesgo
real ya lo cubre el barrido de `ast.Compare`, que dio **2** y los dos son claves internas
de un resultado calculado (el buscador y la campana), no datos de hoja.
Nuevo `check_v469_smoke`: **ejecuta el viaje completo** de un valor (fila vieja →
canonizar → la comparación REAL del código → lo que se ve), 29 comprobaciones — porque
«compila e importa» no verifica nada de esto (v378/v439).
Batería: **9 roturas, 9 cazadas**, con **verde de base comprobado primero** (sin ese paso
una tanda entera sale «cazada» sin probar nada, v459) y un caso de **CONTROL**.
⚠️ Y la compatibilidad está demostrada **contra la hoja real**, no simulada:
`get_user('dacox').Role` llega como `owner` con la hoja diciendo `propietario`.

"""

ANCLA = "## Versiones desplegadas (v468 = actual)"
assert s.count(ANCLA) == 1, "ancla de la tabla ausente"
s = s.replace(ANCLA, SECCION + "## Versiones desplegadas (v469 = actual)")

FILA_ANCLA = "| v468 | **Las 160 COLUMNAS pasan a nombre INGLES**"
assert s.count(FILA_ANCLA) == 1, "fila v468 ausente"
FILA = (
    "| v469 | **Los VALORES pasan a INGLES** (61 pares), ultima capa de «todo en ingles». "
    "Mismo diseno que las columnas: `core/valores.py` canoniza al LEER, asi que el codigo "
    "aguanta las dos formas y se puede desplegar ANTES de migrar la hoja. ⚠️ **Lista blanca "
    "por (HOJA, COLUMNA)**, nunca por nombre suelto. **Dos fallos silenciosos**: "
    "**(1)** `Sheet1.Type` se quedo FUERA de esa lista mientras `TIPO_PROYECTO` pasaba a "
    "`\"project\"`, asi que las ~500 filas del historico se leian crudas y **ni una hora "
    "imputada a una obra contaba como tal** — nomina, costo de obra, conciliacion y reparto "
    "por proyecto, todo a cero. ⚠️ Y **el guardian de v469 estaba PROTEGIENDO el fallo** "
    "(exigia que quedase fuera, cierto cuando la constante aun era `proyecto`): hacerle caso "
    "al rojo sin mirar el codigo acusado lo habria reintroducido — regla v385 con el acusado "
    "teniendo razon y el acusador no. Los dos barridos que lo buscaban tampoco lo vieron: uno "
    "comparaba por NOMBRE de columna (y `Type` ya estaba, para otra hoja) y el otro solo "
    "miraba constantes que son LISTA, y estas son sueltas. "
    "**(2)** `estado_cobro` devolvia una MEZCLA (cuatro ramas en espanol y una migrada), asi "
    "que el chip de la factura perdia icono y color y salia el texto crudo; se revierte esa "
    "rama y las facturas se quedan en espanol de punta a punta. ⚠️ **Y la red que buscaba "
    "mezclas era CIEGA a ese caso**: hecha sobre el mapa de MIGRACION, daba 0 con la mezcla "
    "delante — un valor migrado fuera de ese mapa es justo donde duele; rehecha sobre el "
    "vocabulario completo si lo ve, y solo lo destapo validarla contra un caso conocido-bueno. "
    "Los 8 guardianes de «el DATO sigue en espanol» **invertidos con su razon**, no relajados. "
    "9/9 roturas cazadas + control; smoke que ejecuta el viaje completo de un valor (29); y la "
    "compatibilidad demostrada **contra la hoja real** (`Role` llega `owner` con la hoja "
    "diciendo `propietario`) |\n")
s = s.replace(FILA_ANCLA, FILA + FILA_ANCLA)

io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: seccion v469 + fila + cabecera")
