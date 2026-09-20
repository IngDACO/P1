# -*- coding: utf-8 -*-
"""Documenta v470 en CLAUDE.md: seccion propia + fila de la tabla + cabecera."""
import io

P = r"C:\Users\diego\P1\CLAUDE.md"
s = io.open(P, encoding="utf-8").read()

SECCION = """## Tipo de proyecto «Ripout + Installation» (v470)

Petición del usuario: *«un nuevo tipo de trabajo que va a ser rip out + instalación»* —
sustituir un ascensor, o sea desmontar el viejo y montar el nuevo.

### El desmontaje es UNA actividad, no una tabla de fases
Se propusieron ocho fases de strip-out y el usuario lo corrigió: **«en el combinado el
rip out entra como la primera actividad»**. Eso quita una tabla entera que mantener y
deja el cronograma en `FASE_RIPOUT + PHASES`. Su duración **escala con las paradas**
(decisión suya): más plantas son más puertas de rellano que quitar y más riel que
desmontar — 3 paradas dan 4 días, 12 dan 9, y el proyecto de 6 paradas pasa de 29 a 35.
⚠️ Duración y peso son solo el punto de partida: la tabla de actividades es **editable
por proyecto** desde v83. Y el nombre nace en INGLÉS porque se GUARDA en la hoja
`Activities`: traducirlo después obliga a migrar el histórico (lo que costó v453).

### ⚠️ El cambio de fondo NO es la fase: es que había TRES sitios decidiendo
«¿este tipo genera cronograma?» se preguntaba en el alta a mano, en la edición y en
`quotes.aceptar_y_crear_proyecto` — y **este último comparaba contra el LITERAL**
`"Installation"` en vez de la constante. Añadir un tipo a dos de los tres lo deja
comportándose como «Other» **sin dar ningún error**: es exactamente el fallo de v454,
donde una obra creada desde cotización nació con CERO actividades y se quedó clavada en
0% para siempre, porque el avance es Σ(peso·avance)/Σpeso sobre las actividades.
→ **`projects.genera_cronograma(tipo)` es ahora la única definición** y los tres
delegan, más `con_ripout(tipo)` para la fase. El guardián prohíbe volver a comparar el
literal, así que el tipo SIGUIENTE que se añada tampoco podrá divergir.

### ⚠️ Y `custom_rows` no puede volver a insertarla
`build_schedule(..., custom_rows=…)` es el camino que se usa al GUARDAR el cronograma
editado. Si el `ripout=True` antepusiera la fase también ahí, se duplicaría en **cada
guardado**. Va solo en la rama automática, y el guardián lo comprueba ejecutando un
ciclo generar → editar → guardar.

### Cambiar el tipo NO regenera el cronograma, y ahora se dice
Regenerarlo borraría el avance que el campo ya haya reportado — la misma razón por la
que `attach_survey` no toca las actividades desde v135. Correcto, pero hasta aquí
pasaba **en silencio**: se marcaba la obra como «Ripout + Installation» y su plan seguía
sin el desmontaje. Se avisa por **CONDICIÓN, no por evento** (uno que solo saliera al
cambiar el tipo se perdería en el primer rerun, v375/v383) y **donde se arregla** —junto
a la tabla de actividades, con el «Add activity» debajo—, no junto al selector (v395).
⚠️ De paso, los dos `help` decían «Only «Installation»…» y al añadir el tipo pasaron a
ser **falsos**: es la familia del comentario de `use_container_width` (v405) y del de
`inventory_ui` (v469) — un texto que miente sobre el código.

### ⚠️ El default que se queda como literal, a propósito
`quotes.aceptar_y_crear_proyecto(tipo="Installation")` sigue siendo un literal porque
`projects` se importa DENTRO de esa función, y reestructurar el grafo de imports de un
módulo de 600 líneas por un valor por defecto es más riesgo que valor (comprobado que no
hay ciclo, pero no es razón para tocarlo). En su lugar **se afirma la invariante**: si
alguien renombra la constante, ese default apuntaría a un tipo que ya no existe y el
proyecto nacería con un tipo desconocido, en silencio. El guardián lo compara por AST.

### Verificación
`verif_v470`, **23 comprobaciones**, todo EJECUTANDO (importar no ejecuta, v378, y este
fallo vive dentro de la función). Incluye que **una instalación normal salga exactamente
igual que antes** —mismas fases y misma duración—, porque si se moviera, v470 habría
cambiado el plan de todas las obras nuevas sin que nadie lo pidiera.
Batería: **13 roturas, 13 cazadas** + control verde, con verde de base primero (v459).
⚠️ Una **SE ESCAPÓ** al primer intento: el chequeo del marcador `{act}` **reproducía la
cadena en el propio guardián** en vez de leerla del código, así que romper el código no
cambiaba nada — el fallo de v412. Rehecho leyendo la llamada por AST, y de paso
generalizado: **ninguna llamada a `t()`/`d()` del repo puede tener un marcador sin su
kwarg**, que si no se pinta `{x}` literal y nada salta (v453).

"""

ANCLA = "## Versiones desplegadas (v469 = actual)"
assert s.count(ANCLA) == 1, "ancla de la tabla ausente"
s = s.replace(ANCLA, SECCION + "## Versiones desplegadas (v470 = actual)")

FILA_ANCLA = "| v469 | **Los VALORES pasan a INGLES**"
assert s.count(FILA_ANCLA) == 1, "fila v469 ausente"
FILA = (
    "| v470 | **Tipo de proyecto «Ripout + Installation»** (peticion del usuario): "
    "sustituir un ascensor. El desmontaje entra como **UNA actividad, la primera** "
    "—no una tabla de fases, lo corrigio el usuario— y su duracion **escala con las "
    "paradas** (3 paradas: 4 d · 12: 9 d; el proyecto de 6 pasa de 29 a 35 d). "
    "⚠️ El cambio de fondo NO es la fase: habia **TRES** sitios preguntando «¿este tipo "
    "genera cronograma?» (alta, edicion y aceptar cotizacion) y uno comparaba el "
    "**LITERAL** en vez de la constante — anadir un tipo a dos de los tres lo deja "
    "comportandose como «Other» sin dar ningun error, que es el fallo de v454 (una obra "
    "nacida con CERO actividades, clavada en 0% para siempre). Ahora "
    "`projects.genera_cronograma()` es la unica definicion y los tres delegan. "
    "⚠️ `custom_rows` NO reinserta la fase, o se duplicaria en cada guardado del "
    "cronograma. Cambiar el tipo sigue sin regenerar el plan (regenerarlo borraria el "
    "avance ya reportado, v135) pero **ya se avisa**, por CONDICION y donde se arregla; "
    "y los dos `help` que decian «Only Installation» pasaron a mentir y se corrigieron. "
    "23 comprobaciones ejecutando + **13/13 roturas cazadas** — ⚠️ una **SE ESCAPO** "
    "porque el chequeo del marcador reproducia la cadena en el guardian en vez de leerla "
    "del codigo (el fallo de v412); rehecho por AST y generalizado a todo `t()`/`d()` del "
    "repo |\n")
s = s.replace(FILA_ANCLA, FILA + FILA_ANCLA)

io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: seccion v470 + fila + cabecera")
