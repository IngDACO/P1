# -*- coding: utf-8 -*-
"""Documenta v499 en CLAUDE.md: el plan con dependencias."""
import io

P = "C:/Users/diego/P1/CLAUDE.md"

SECCION = """## PLAN CON DEPENDENCIAS: las actividades se encadenan (v499)

Petición del usuario: *«vamos a trabajar en la Gestión de instalación, que me dices que
estamos atrás en profundidad y en integraciones»*. Decisiones suyas: **plan con
dependencias**, **con desfase en días** y **el fin previsto se recalcula de la cadena**.

Hasta v498 el cronograma era una **CADENA RÍGIDA**: `build_schedule` acumulaba `cur += dur`,
así que cada actividad empezaba justo cuando terminaba la anterior. Eso no es un plan de
obra — las puertas de rellano y el cableado se solapan, y el atraso de los rieles no
arrastraba nada porque no había nada que arrastrar.

### `core/plan.py`: el cálculo, y SOLO el cálculo
Funciones puras, sin Streamlit ni Sheets, para poder ejercitarlo entero (v378: importar no
ejecuta). Columna `Predecessors` de cada actividad:

| | |
|---|---|
| **vacío** | detrás de la ANTERIOR — ⚠️ es lo que hacía la app hasta v498, así que **una obra que ya existe se comporta EXACTAMENTE igual** hasta que alguien la edite |
| **`-`** | sin predecesora: empieza el día 0, en paralelo |
| **`3` · `3+2` · `3-1`** | detrás de la nº 3; `+2` espera dos días, `-1` la solapa uno |
| **`3;5-2`** | detrás de varias: manda la que la deje empezar MÁS TARDE |

Y la **ruta crítica** sale sola (las que no tienen holgura): el Gantt les pinta el borde
rojo, que es la información que el cronograma nunca daba — atrasar ESAS atrasa la entrega.

⚠️ **Un plan mal encadenado tiene que seguir dibujándose**, que es lo que permite verlo para
arreglarlo: un **ciclo** (A detrás de B y B detrás de A) colgaría el cálculo, así que se
detecta, esa actividad pasa a ir detrás de la anterior y se avisa; una **predecesora que no
existe** (se borró) se ignora con aviso, en vez de dar por bueno un plan que empieza el día 0.

### ⚠️ Lo que rompe en silencio: reordenar
Las predecesoras se refieren al **número de orden**, que es como la hoja identifica cada fila
(ProjectID + Order). Así que reordenar el cronograma haría que «detrás de la 3» pasara a
apuntar a **otra actividad sin que nada avise** — la peor forma de equivocar un plan.
`plan.remapear` reescribe las referencias con el mapa viejo→nuevo, y `limpiar_predecesoras`
las suelta al borrar una actividad.

### ⚠️ EL FALLO QUE CAZÓ EL GUARDIÁN: el mapa salía de los `edits`
```python
mapa = {int(e["orden0"]): int(e["Order"]) for e in edits}   # ← solo lo que el llamador manda
```
Hoy el único llamador manda **la tabla completa**, así que el mapa está completo y el fallo
es LATENTE. Pero un guardado **parcial** —que es el patrón de `save_field_progress` (v162) y
lo natural para ahorrar cuota— dejaría fuera del mapa a las filas no tocadas y `remapear` las
**tiraría de la lista**: el plan entero reescrito, sin ningún error. Ahora el mapa se
construye con **TODAS las actividades de la obra** y los `edits` solo SOBRESCRIBEN, así que
una lista parcial ya no puede borrar nada. Es el criterio de v487 (`opciones_con_actual`) y
v492 (`guardar_claves`): **lo que no se toca, se conserva** — la función no puede depender de
que el llamador se acuerde.

### ⚠️ Y DOS KeyError VIVOS desde v468, encontrados al extender la sonda de v471
`verif_v471` comprueba que una tabla editable se lea por la CLAVE del cuadro y no por la
etiqueta. Extendida para seguir **un nivel de alias** (`r = _ed.iloc[i]`) aparecieron dos que
no veía:

| Dónde | Qué pasaba |
|---|---|
| **«Save activity table»** (admin) | `r["Weight"]` y `r["Order"]` con la fila en `"Peso"`/`"Orden"` |
| **«Save progress»** (campo) | `r["Note"]` con la fila en `"Nota"` |

Los dos **revientan el guardado entero**, y el segundo es la escritura más usada de la app.
`git log -S` los data en **v468**: la migración de columnas a inglés renombró **la LECTURA y
no la clave del cuadro** — exactamente la familia que v471 documentó y arregló en 5 sitios,
con estos dos escapándosele por el hueco del alias.

### ⚠️ Mi oráculo escrito DE MEMORIA dio dos rojos que no existían
El guardián comprueba que un cronograma **sin dependencias** salga como hasta v498 (si se
moviera, cambiarían las fechas de todas las obras existentes sin que nadie lo pidiera). Escribí
los números de memoria y dos estaban mal (NS=1 son **19** días, no 20; NS=12 con ripout son
**50**, no 48), así que el guardián acusaba a un código correcto — y con un rojo de base, la
tanda de roturas no habría probado nada (v459). El oráculo se sacó del **módulo de v498**
(`git show HEAD:…/schedule.py`, ejecutado aparte) y se escribió LITERAL en el guardián:
comparar la salida del código nuevo consigo misma no probaría nada (trampa nº1) y sacarlo de
git DENTRO del guardián lo dejaría vacío en cuanto se hiciera el commit (v484).
Resultado: **14 cronogramas (7 NS × ripout) idénticos**, y no solo en el total —dos
cronogramas distintos pueden durar lo mismo— sino **actividad por actividad**: mismo nombre,
mismo inicio, misma duración y mismo peso, **0 diferencias**.

### ⚠️ El aviso que podría no salir NUNCA
La pantalla saca los avisos con `project_schedule(pid)["sched"]["avisos_plan"]`. Si la FORMA
del dato fuera otra, **no saldrían nunca y nada lo diría** — no hay error que atrapar, solo
silencio (regla v135). El guardián compara la cadena de claves que usa la pantalla contra lo
que la función DEVUELVE de verdad, por AST y **sin leer la hoja** (el techo son 60
lecturas/min, v339), incluida la guarda del `None` de una obra recién creada.

### Verificación
`verif_v499.py`, **39 comprobaciones**, todo EJECUTANDO: el encadenado (desfase, solape,
paralelo, ciclo, referencia rota, remapeo), el oráculo de los 14 cronogramas, la fila
posicional contra su cabecera (v363), `save_activities` y `limpiar_predecesoras` con una hoja
simulada —incluido el **guardado parcial**— y las dos tablas editables leídas por su clave.
Batería: **13 roturas, 13 cazadas + CONTROL verde**, con el **verde de base confirmado antes**
(v459) y **el motivo de cada rotura a la vista** (v492: un guardián que revienta también
«caza» todo). ⚠️ En la primera pasada **2 de las 13 no probaron nada**: escribí anclas que no
existían en `schedule.py`, y el propio informe lo dijo («ANCLA no única (0)») en vez de
contarlas como cazadas.

### ⚠️ Y la SUITE dio 2 rojos: uno mío y REAL, otro del guardián
Correrla entera (v385) es lo que los destapó, y **ninguno era caducado**:
- **`verif_v323` tenía razón**: `plan.py` definía un **`_num` LOCAL**. Hoy delegaba en
  `core.num`, pero es la sexta copia local del concepto que v323 eliminó — y aquella tanda
  encontró que **dos de las cinco divergencias eran fallos de dinero** (un importe con
  separador de miles leído como $0). Se quita: `core.num` es módulo HOJA, así que importarlo
  arriba no crea ningún ciclo con `schedule`. La regla no es «hoy da lo mismo», es que mañana
  alguien le añade un default y vuelve la divergencia.
- **`verif_v469` era un FALSO POSITIVO**, y del tipo que empuja a romper código sano: su sonda
  comparaba **TEXTO por línea** (`"valores.canonizar" not in linea`), así que una llamada
  **partida en dos líneas** —la de `limpiar_predecesoras`, que canoniza perfectamente— salía
  denunciada. Es exactamente el fallo que **v472 ya corrigió en `verif_v468`**, en otro
  guardián. Reescrita por AST sobre la SENTENCIA (`ast.unparse` normaliza la línea lógica
  entera) y ⚠️ **auto-validada en las dos direcciones** antes de creerse su cero: tiene que
  cazar la lectura cruda **y** no marcar la partida en dos líneas (trampa nº12).

### Lo que NO entra, y por qué
El **fin previsto y el retraso de toda la app** (cartera, KPIs, radar, curva S) siguen
saliendo del ritmo/SPI, no de la cadena. Es lo que el usuario pidió («recalcular la cadena»)
y toca cartera, agrupaciones y el radar del admin: va en su propia versión, con su guardián y
su despliegue, en vez de colarlo al cierre de una que ya toca cuatro módulos.
"""

FILA = ("| v499 | **Plan con dependencias**: las actividades se encadenan («detrás de la 3», con "
        "**desfase** `3+2` y **solape** `3-1`, y varias con `3;5-2`), sale la **ruta crítica** "
        "(borde rojo en el Gantt) y un plan mal encadenado —ciclo o predecesora borrada— se avisa y "
        "**se sigue dibujando**. ⚠️ Vacío = «detrás de la anterior», así que **una obra que ya existe "
        "no se mueve**: verificado contra el módulo de v498, **14 cronogramas idénticos actividad por "
        "actividad** (0 diferencias en fechas, duraciones y pesos). ⚠️ **El guardián cazó un fallo "
        "real**: el mapa de remapeo salía de los `edits`, así que un guardado PARCIAL habría tirado "
        "las predecesoras de las filas no tocadas —el plan entero reescrito sin ningún error—; ahora "
        "sale de TODAS las actividades y los edits solo sobrescriben. ⚠️ Y al extender la sonda de "
        "v471 a los ALIAS aparecieron **dos KeyError vivos desde v468** que reventaban el guardado de "
        "la tabla de actividades y **el del avance del campo** (la escritura más usada): la migración "
        "de columnas renombró la LECTURA y no la clave del cuadro. ⚠️ Mi oráculo escrito **de memoria** "
        "dio 2 rojos inexistentes → se sacó del módulo de v498. ⚠️ Y la SUITE dio 2 rojos, ninguno "
        "caducado: `verif_v323` **tenía razón** (`plan.py` definía un `_num` LOCAL, la sexta copia del "
        "concepto que v323 eliminó, donde 2 de 5 divergencias eran fallos de dinero) y `verif_v469` era "
        "un **falso positivo** que denunciaba código correcto — comparaba TEXTO por línea, así que una "
        "llamada partida en dos la marcaba; reescrita por AST y **auto-validada en las dos direcciones** "
        "(es el fallo que v472 ya corrigió en otro guardián). 39 comprobaciones · **13/13 roturas + "
        "control** (⚠️ 2 anclas no existían y no probaron nada en la 1ª pasada) |\n")

s = io.open(P, encoding="utf-8").read()
ANCLA = "## Versiones desplegadas (v498 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))
s = s.replace(ANCLA, SECCION + "\n## Versiones desplegadas (v499 = actual)")
s = s.replace(CAB, CAB + FILA)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: seccion v499 + fila + cabecera")
