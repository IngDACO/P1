# -*- coding: utf-8 -*-
"""Documenta v472 en CLAUDE.md: seccion nueva + fila en la tabla + cabecera."""
import io

P = "C:\\Users\\diego\\P1\\CLAUDE.md"

SECCION = """## BIBLIOTECA TECNICA: fotos, manuales y fichas con buscador (v472)

Peticion del usuario: *«vamos a crear una base de datos de fotos y manuales e
informacion con barra de busqueda; vamos a establecer una taxonomia por marca,
modelo y seccion del elevador»*. Cinco decisiones suyas, tomadas antes de escribir
nada — y **tres fueron contra mi recomendacion**, que es como debe ser:

| | |
|---|---|
| **Biblioteca aparte**, con su propia subida | no se alimenta etiquetando lo de las obras: es material de REFERENCIA, curado |
| **Vocabulario propio** de secciones | pensado para BUSCAR documentacion, no para planificar obra — no reusa `schedule.PHASES` |
| **Catalogo mantenido** por el propietario | como `Rieles`: se elige de una lista, no se teclea |
| **GLOBAL**, como los manuales | una sola biblioteca en el libro maestro |
| **Solo el propietario sube** | control de calidad; todos consultan |

`core/library.py` (hojas `Library` + `LibraryModels`, carpeta de Drive
`COPEX Library`) + `core/library_ui.py`, seccion propia para los tres roles.

### Lo que no se invento: las reglas que ya existian
Casi nada aqui es nuevo — es aplicar lo que el repo ya aprendio a golpes:
- **GLOBAL de verdad** (v359): las dos hojas en `SHEETS_GLOBALES`, ⚠️ **en
  minusculas**, porque la comprobacion es `.lower()`. Sin eso, cada cliente acabaria
  con su propia biblioteca **VACIA** en su libro — lo contrario de «global», y sin
  dar ningun error.
- **En el LOTE** (`hojas.HOJAS_LECTURA`): ⚠️ un modulo que lee con
  `hojas.registros(SHEET, HEADERS)` y no esta en el lote **lee vacio PARA SIEMPRE**
  si ademas lee sin cabeceras (v353). Y aqui cuesta **0 llamadas extra**: la
  biblioteca es global, asi que vive en el maestro, cuyo lote ya viene caliente del
  `Login` de cada sesion — solo añade dos rangos a un `batchGet` que ya se hacia.
- **`get_sheet`, nunca `_get_worksheet`** (v404): el segundo resuelve el libro del
  grupo de la SESION mientras el lector resuelve con `sheet_id_para` → se escribe en
  un libro y se lee de otro, en silencio. Es el fallo que dejo el catalogo de rieles
  roto durante nueve versiones.
- **Descarga perezosa + galeria PAGINADA** (v147): `st.download_button(data=…)`
  evalua `data` al RENDERIZAR, asi que un boton por fila se baja **todo Drive** en
  cada pasada. Cada miniatura ES una descarga, de ahi el tope de 6.
- **Orden de escrituras con Drive** (v343/v456): al filar, el archivo ANTES que la
  fila; al borrar, el archivo ANTES que la fila. Al reves se pierde el DriveID con la
  fila y el archivo queda huerfano y sin manija.
- **IDs que no reciclan ni se cuentan** (v427/v428), **fila posicional** que casa con
  la cabecera (v363, el fallo que dejo `create_project` muerto 3 versiones), **titulo
  propio** porque la seccion no tiene sub-pestañas (v320), **mensajes por `flash`**
  (v365) y las lecturas frescas por `columnas.canonizar` (v468).
- ⚠️ **La seccion va al FINAL de la nav de cada rol**, no en medio: una seccion nueva
  no le reordena el menu a quien ya lo usaba (`verif_v297`, y es como entro
  «ausencias» en v430). La primera version la metia delante de «Mis credenciales».

### ⚠️ EL BUSCADOR DE LA BARRA SUPERIOR NO DEVOLVIA UN TRABAJO NUNCA
Encontrado de paso, y llevaba **32 versiones** vivo:
```python
_num = str(t.get("Number", "")).strip()      # ← `t` es la FUNCION de traduccion
```
`t` es la funcion de i18n del modulo y la fila del bucle es `_trb`, asi que eso lanza
`AttributeError`… **que el `except Exception` del propio bloque se tragaba**. Efecto:
`buscar()` devolvia proyectos y personas pero **jamas un trabajo**. Datado con
`git log -S`: lo introdujo **v440** (el renombrado de la variable `t` → `_trb` de la
migracion i18n) y v468 volvio a tocar la linea sin verlo.
⚠️ Probado en las DOS direcciones, no leido: arreglado devuelve
`('trabajo', 'Grua Talavera', 'TRB-0007 · nº 89')`; reinyectando el fallo devuelve
`[]` mas la linea de log que nadie miraba. Es el shadowing de v437/v439/v440/v442 y
el `except` que esconde lo que acabas de escribir de v323/v338/v344.

### ⚠️ Y `correcciones` llamaba a `siguiente_id_libre` con los argumentos CAMBIADOS
```python
hojas.siguiente_id_libre(SHEET, "COR", n + 1)   # la firma es (prefijo, maximo, propia=…)
```
Lanza `ValueError: invalid literal for int() with base 10: 'COR'` — **verificado
ejecutandolo, no leyendolo** — y el `except` de al lado se lo traga, asi que caia
siempre al `max+1`: **el salto de IDs de v427 no se aplicaba ahi desde v461**, que es
justo lo que aquella version vino a arreglar. Tercera vez en la tanda que un `except`
amplio esconde el fallo recien introducido.

### ⚠️ LO QUE DEFINE ESTA VERSION: comprobaciones que NO PODIAN FALLAR
El guardian salio verde y la bateria de roturas dijo **13 de 15**. Las dos escapadas
tenian la misma forma — **el chequeo aprobaba por un motivo que no era el suyo**:

| Escapo | Por que |
|---|---|
| «la galeria deja de paginar» | miraba `"_POR_PAGINA" in ast.dump(_galeria)`, y esa constante aparece **CUATRO veces** ahi (el total de paginas y los dos extremos del corte): borrar el corte deja tres y el `in` sigue cierto. La **trampa nº2** (*grep != uso*) dentro del guardian |
| «un tipo vuelve al español» | miraba `etiqueta(x) == x and canon(x) == x`, y eso es cierto para **cualquier cadena que el vocabulario no conozca** — `foto` incluida. Era una afirmacion que **no podia fallar nunca** |

La segunda es la leccion de v462 mordiendo del otro lado: **`etiqueta()` devuelve TAL
CUAL lo que no conoce**, asi que esa igualdad no distingue un canonico de un español
que nadie mapeo. Los arreglos son estructurales: lo que la galeria pinta tiene que
venir de un **CORTE** (`ast.Subscript` con `Slice`, no la mencion de un nombre), y un
valor de negocio tiene que ser un **canonico CONOCIDO**.

### ⚠️ Y la misma ceguera estaba en `verif_v463`, que es la regla GENERAL del repo
O sea que **cualquier lista de negocio podia volver al español sin que saltara nada**,
mientras la palabra no fuera clave del mapa. Medido antes de proponer (v453: estimar
es peor que no dar numero): de **78 valores de negocio, solo 11 fuera del vocabulario
canonico**, y **6 ya exentos con razon** (los simbolos `m`/`m²`/`kg` y los 3 de
`payroll`, que siguen en español a proposito). O sea que cerrar el hueco costaba
**3 entradas y 2 exenciones**, no una migracion:
- `foto → photo` y `diagrama → diagram` (v472);
- **`Ripout + Instalación → Ripout + Installation`**, que **lo dejo v470**: añadio un
  tipo de proyecto y no lo mapeo. El hueco de v462 —*un valor nuevo no entra solo en
  el mapa, y no da ningun error*— repetido dos versiones despues;
- exentos UNO A UNO y con razon: `manual` se escribe IGUAL en los dos idiomas
  (mapearlo seria un «mapa espejo», que v450 mando borrar) y a `datasheet` habria que
  inventarle una clave española que nadie escribe.

**Y con la invariante fuerte, el guardian general cazo mi propio codigo a la primera**:
la tabla de la biblioteca pintaba `Type` con `t()`. `t()` traduce literales de
INTERFAZ contra el catalogo; un valor que viene de la HOJA va por `etiqueta()`
(v442/v463) — con `t()`, una fila heredada que diga `foto` se pintaria `foto` bajo una
cabecera ya inglesa: traduccion a medias dentro de la misma tabla (v450). Es la mitad
1 del fallo de v462, en una pantalla recien escrita.
⚠️ **Y entonces el guardian dio un FALSO POSITIVO sobre el arreglo correcto**: su
sonda solo reconocia `i18n.etiqueta(...)` y el alias `_etq(...)`, no el nombre pelado
— la sonda midiendo por la forma en que se escribio la primera vez (v450/v459). Se
arreglaron las dos cosas: el codigo se alinea con la convencion del repo (`_etq`, como
los otros cuatro modulos, criterio de v461) **y** la sonda reconoce las tres formas,
porque un falso positivo no es inofensivo — es lo que hace que un guardian acabe
ignorandose (v450) y lo que empuja a «arreglar» codigo sano (v385).

### ⚠️ LA SUITE: 8 rojos, y CUATRO eran guardianes anclados a la FORMA
Correr la suite ENTERA (regla v385) dio **8 rojos**. Clasificados uno a uno mirando el
codigo acusado ANTES de tocar nada, el reparto es la leccion de la tanda:

| | Guardian | Que pasaba |
|---|---|---|
| **REAL** | v322 | un `import parse_date` MUERTO en `library.py`, con un comentario que decia «lo usan los consumidores»: **nadie lo reexporta**. El comentario mentia sobre el codigo (v405/v469) |
| **REAL** | v297 | su afirmacion «las que se añadan van DESPUES» era CORRECTA y yo meti la seccion en medio de la nav del campo y del admin → se arreglo el CODIGO, no el guardian |
| forma | **v378** | `GLOBALES_OK` era una lista de funciones **a mano** en paralelo a `SHEETS_GLOBALES` → denunciaba un modulo GLOBAL como fuga entre inquilinos. Ahora se DERIVA |
| forma | **v469** | la exencion iba por **NUMERO DE LINEA** (661, 761): mis añadidos a `home_ui` los corrieron a 696/801 y los falsos positivos «volvieron». Reanclada a (fichero, funcion, valor) |
| forma | **v468** | exigia la palabra `canonizar` **en la misma linea** que `get_all_records`: una llamada partida en dos salia denunciada estando bien. Pasado a estructural |
| forma | **v449** | su heuristica «3+ palabras = mensaje» marco `'Ripout + Instalación'`, que es una **CLAVE del vocabulario heredado** (dato); el `+` cuenta como palabra |
| caducado | v298 · v465 | igualdad exacta de secciones por rol, y «toda hoja necesita entrada en `LEGADO`» — pero estas dos **nacieron en ingles** y no tienen nombre viejo con el que ser compatible |

⚠️ Un ancla por numero de linea es fragil en las DOS direcciones: cualquier edicion mas
arriba reabre el falso positivo **y** una comparacion REAL que caiga algun dia en ese
numero quedaria eximida en silencio. Los cuatro se arreglaron igual: **derivando el
dato de su fuente** (`SHEETS_GLOBALES`, el propio mapa `VALORES`) o midiendo
ESTRUCTURA en vez de texto, y **cada sonda quedo validada contra un caso
conocido-malo** antes de creerse su cero (trampa nº12). La de v378 se probo en las dos
direcciones: exime la hoja global, **no** exime a `catalogo`/`quotes`, y si la
biblioteca dejara de ser global volveria a estar denunciada.

⚠️ Y dos veces me tape a mi mismo arreglandolos: un `.replace()` que alcanzo tambien
la **DEFINICION** del helper (renombrar en un paso lo que son DOS — leccion v446/v447)
y dejo el guardian **REVENTANDO**, que es el modo de fallo mas engañoso porque
devuelve codigo != 0 siempre y parece un rojo del codigo auditado (v459/v463); y otro
`\\n` mangullado por heredoc (**trampa nº26, sexta vez**), que solo se vio MIDIENDO —
las dos variantes contenian un salto REAL — en vez de teorizando.

### Verificacion
`verif_v472.py`, **28 comprobaciones** (hojas globales afirmadas **por ejecucion**:
`sheet_id_para('Library') == sheet_id_para('Login')`; 0 `download_button` en bucle con
la sonda validada contra un caso construido; los dos ordenes de escritura de Drive;
`_next_id` sin `len()` y con la firma comprobada por `inspect.signature`; fila
posicional 12 == 12 cabeceras; **ningun modulo usa `t` como variable**, con la sonda
validada contra el codigo REAL de v440; la seccion en los tres roles con despacho por
ID exacto; y el buscador EJECUTADO devolviendo la biblioteca y el trabajo).
Bateria: **15 de 15 roturas cazadas + CONTROL verde**, con el **verde de base
comprobado ANTES** (sin ese paso una tanda entera sale «cazada» sin probar nada,
v459/v461/v463). Suite entera: **109 verde · 0 rojo · 0 roto** (776 s), mas los 7
«SIN DATOS» conocidos de v471 — la demo vacia, que no es un fallo pero tampoco una
garantia.
"""

FILA = ("| v472 | **Biblioteca tecnica** (peticion del usuario): fotos, manuales y "
        "fichas con buscador y taxonomia marca/modelo/seccion, GLOBAL y curada por el "
        "propietario — cinco decisiones suyas, tres contra mi recomendacion. Aplica lo "
        "ya aprendido: hojas globales en minusculas (v359), en el LOTE con **0 llamadas "
        "extra** (v339/v353), `get_sheet` y no `_get_worksheet` (v404), galeria paginada "
        "porque cada miniatura ES una descarga (v147) y el archivo ANTES que la fila en "
        "las dos direcciones (v343/v456). ⚠️ **De paso, dos fallos reales**: el buscador "
        "de la barra superior **no devolvia un trabajo NUNCA** desde **v440** —`t.get(...)` "
        "con `t` siendo la funcion de i18n, `AttributeError` que el `except` se tragaba, "
        "32 versiones— y `correcciones` llamaba a `siguiente_id_libre` con los argumentos "
        "CAMBIADOS desde v461, asi que **el salto de IDs de v427 no se aplicaba ahi**. "
        "⚠️ Pero lo que define la version son **comprobaciones que NO PODIAN FALLAR**: dos "
        "roturas se escaparon por `\"_POR_PAGINA\" in dump` (la constante aparece 4 veces, "
        "borrar el corte deja 3) y por `etiqueta(x) == x` (cierto para CUALQUIER cadena que "
        "el vocabulario no conozca — v462 del otro lado). **La misma ceguera estaba en "
        "`verif_v463`, la regla GENERAL**: medido, cerrarla costaba **3 entradas y 2 "
        "exenciones** —una **de v470**, que añadio un tipo y no lo mapeo—, no una migracion. "
        "Con la invariante fuerte el guardian **cazo mi propio codigo** (`Type` con `t()` en "
        "vez de `etiqueta()`) y luego dio un **falso positivo sobre el arreglo correcto**. "
        "⚠️ Y la suite dio **8 rojos de los que CUATRO eran guardianes anclados a la FORMA** "
        "(una lista a mano, **numeros de linea**, texto en la misma linea, «3+ palabras = "
        "mensaje»), no fallos del codigo: se arreglaron derivando el dato de su fuente o "
        "midiendo estructura. 28 comprobaciones · **15/15 roturas** + control · suite "
        "**109 verde** |\n")

s = io.open(P, encoding="utf-8").read()

ANCLA = "## Versiones desplegadas (v471 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))

NUEVA_CAB = "## Versiones desplegadas (v472 = actual)"
s = s.replace(ANCLA, SECCION + "\n" + NUEVA_CAB)
s = s.replace(CAB, CAB + FILA)

io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: seccion v472 + fila + cabecera (v472 = actual)")
