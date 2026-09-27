# Documentos de origen del catálogo de obra

Estos tres documentos son la **fuente** del modelo de obra de la app. No son notas: hay
código que depende de ellos y trabajo humano de semanas dentro.

| Documento | Qué es | Qué depende de él |
|---|---|---|
| `Lift_Install_Stage_Activity_Draft_v1.md` | Etapa → Actividad, con pesos | **`survey_app/core/stages.py`** (v512): 18 etapas, 173 actividades, 11 condicionales |
| `Lift_Install_Task_Breakdown.md` | El **tercer** nivel: Tarea bajo Actividad (83 tareas) | Todavía nada — el catálogo en código llega solo a Actividad |
| `Process_Knowledge_Reference.md` | Glosario, jerga, reglas de desambiguación y de puntuación de partes | Todavía nada — es la base de F2 |

## ⚠️ Por qué están aquí (27/09/2026)

Llegaron como **adjuntos de una conversación** el 22/09/2026 y, tras dos compactaciones,
dejaron de estar en ningún sitio salvo dentro de un fichero de transcript de 19 MB
(`.claude/projects/.../f730f8c8-….jsonl`, líneas 5320-5322). Se recuperaron de ahí.

Un borrado de ese fichero —o una limpieza de sesiones viejas— se los habría llevado. Aquí
viven en el repo, van al ZIP y al Drive con cada despliegue, y quedan versionados.

## ⚠️ Lo que los hace insustituibles

`Process_Knowledge_Reference.md` **no es documentación escrita de una vez**: es el
resultado corregido de pasar un intérprete sobre partes REALES de instaladores. Se nota en
las **58 anotaciones «(Danilo, Sep 2026)»** repartidas por los tres, que no explican
diseño sino que **corrigen respuestas concretas** — «earlier draft had this as permanent»,
o que los interruptores de *park/limit* son de un TKE de otra cuadrilla y hay que
ignorarlos en una obra Schindler.

Eso no se puede reconstruir leyendo el catálogo. Solo se obtiene equivocándose contra
partes de verdad y que alguien que estuvo en obra diga en qué.

## Lo que contiene el de conocimiento, en corto

- **Glosario con los sinónimos reales**: OKR = «revision box» = «inspection box»;
  groutguarding = «fire brackets» = «fire trims» = «fire rating» = «fire seal».
- **Desambiguación por CRONOLOGÍA, no por vocabulario**: «under the cabin work» es
  mecánico si los rieles no han subido y eléctrico si ya subieron. Necesita saber por
  dónde va la obra — justo el dato que `stage_progress` guarda desde v514.
- **Reglas de puntuación**: qué no cuenta como avance (inducción, pre-start), qué se queda
  sin puntuar, cuándo acreditar con confianza baja en vez de descartar, y que el parte de
  un ayudante no lleva peso propio.
- **Patrones de obra** que explican retrasos: curado del Kemset, ladrillo hueco, faltas de
  tornillería, una sierra encerrada en la caja de otro.

## Si se editan

El catálogo en código **no se regenera solo** desde estos ficheros: `stages.py` se escribió
a mano a partir del primero, con dos correcciones de aritmética que el original traía (la
Stage 2 sumaba 106%). Cambiar un peso aquí no cambia nada allí — y al revés, `stages.py`
sella su versión en cada obra (`StagePlanJSON`) justo para que recalibrar no mueva el
avance de obras que ya reclaman dinero. Ver la cabecera de `core/stages.py`.
