"""Documenta v440 (F3) en CLAUDE.md: sección propia + fila en la tabla."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DOC = Path(r"C:\Users\diego\P1\CLAUDE.md")
s = DOC.read_text(encoding="utf-8")

SECCION = """## i18n F3: TODA la interfaz de gestión, en inglés (v440)

15 módulos, **~1.100 etiquetas**: `projects_ui` (479 únicas), `auth_ui`, `roster_ui`,
`inventory_ui`, `home_ui`, los cinco de finanzas/CRM (`clientes_ui`, `catalogo_ui`,
`invoices_ui`, `payroll_ui`, `quotes_ui`) y los pequeños (`location_ui`, `plan_ui`,
`tool_save_ui`, `ui_common`, `app.py`). **0 cadenas sueltas sin `t()`** en los 15.

### ⚠️ Antes de traducir nada hubo que arreglar TRES huecos del extractor
Los tres fallan en silencio, y el primero es el que arruinó F2:
| Hueco | Qué habría pasado |
|---|---|
| filtraba por **IDIOMA** | el agujero de v439: medido, era ciego a **13 de 15** («Fichar», «Firma», «Iniciales», «Pendientes», «Sitios»…). Ahora extrae por POSICIÓN y la decisión etiqueta-vs-dato se toma al escribir el diccionario, que es donde se puede mirar |
| se traía **CLAVES de widget** | `st.form("cli_nuevo")` recibe la key como primer posicional; envolverla en `t()` la haría depender del idioma y **el formulario perdería su estado al cambiarlo**. Igual `ui.confirmar_borrado(key, texto)` |
| no veía **cabeceras de tabla** ni **tarjetas KPI** | 71 `column_config` en el repo y las etiquetas dentro de `kpi_row([( … )])` —el número grande de cada pantalla— se quedaban en español |

Y al abrir el tercero apareció su reverso: al descender por las listas se colaban
**claves de dict** (`_tot["margen_pct"]`, `f["a_pagar"]`), que son el índice de un
`Subscript` en la misma tupla que la etiqueta. Se excluyen, junto con lo que ya está
dentro de un `t(...)`. ⚠️ Y en `column_config` se traduce la ETIQUETA pero **nunca la
CLAVE**: es el nombre de la columna que `st.data_editor` DEVUELVE, y el código la lee
por ese nombre — traducirla deja la lectura buscando una columna que no existe.

### ⚠️ VOLVÍ A ROMPER UN MÓDULO, por hacerlo en el orden equivocado
Al traducir `quotes_ui` metí llamadas `t(...)` en tres funciones donde **`t` ya era la
variable de totales**: «Nueva cotización» y el detalle no habrían abierto. Es el fallo de
v437 y v439 por **tercera vez**, y la causa no es el código: yo comprobaba el ámbito
DESPUÉS de traducir, cuando el daño ya está escrito en el fichero.
→ **`pre_i18n.py`**: pre-vuelo que lista, ANTES de tocar un módulo, qué funciones usan
`t`/`d` como variable. Pasado sobre lo que quedaba: **46 funciones** en 5 módulos. Ese
chequeo evitó repetir el fallo 46 veces.
⚠️ Y su primera versión daba **falsos positivos** por descender a ámbitos que son
propios: un `lambda t:` y un `[t for t, e in …]` **no ligan `t`** en la función que los
contiene (trampa nº3). Con eso corregido, los `t` reales a renombrar eran 7, no 46.

### ⚠️ Tres fallos de la herramienta que cazó su propio `ast.parse`
`aplicar.py` se niega a escribir un fichero que no compile, y esa guarda cobró:
1. Decidía «esto lleva comillas» mirando si el trozo EMPIEZA por comilla — y
   `'>Persona</div>` (de `f"<div style='{_CAB}'>Persona</div>"`) empieza por un apóstrofo
   que es **contenido**. Le añadía comillas y dejaba la f-string abierta.
2. Al arreglar eso rompí el caso MULTILÍNEA: la comilla de cierre está en la última línea
   y `crudo` es el resto de la PRIMERA, así que los cuatro literales largos se
   reescribían **sin comillas**.
3. La forma que funciona no es una heurística de caracteres sino **parsear el trozo**: si
   es una expresión de cadena válida, es un literal; si no, es texto de dentro de una
   f-string.
⚠️ Y hay un TERCER caso que se deja A MANO a propósito: una cadena normal concatenada
con una f-string (`st.caption("texto " f"**{x}**…")`), donde el span EMPIEZA en la comilla
de apertura y TERMINA dentro de la f-string. Automatizarlo en un módulo de 5.000 líneas
es más riesgo que valor: los 35 de `projects_ui` van con ancla, verificables de un vistazo.
⚠️ Y las anclas son de **UNA LÍNEA**: las multilínea obligan a copiar la indentación de la
continuación al carácter, y 20 de 27 no casaron al primer intento.

### El guardián
`verif_v440.py`, 25 comprobaciones, probado contra **6 roturas**: las caza las 6 — pero
**dos solo tras corregirlo**, y las dos por lo mismo, medir por IDIOMA:
- afirmaba que `clientes_ui` tenía la clave `"Pendiente"` y **no existe** (ahí es una
  etiqueta de `st.metric`), así que daba **FALLO con el código correcto**. Se reescribió
  sobre la REGLA —ninguna clave de `column_config` puede ser un `t(...)`— en vez de sobre
  una lista adivinada.
- devolver `t("Net pay")` a `"Neto a pagar"` **no lo veía**: sin acentos ni palabras
  funcionales. El invariante que sí mide no habla de idioma: **toda cadena SUELTA que
  llegue a una función de display tiene que estar envuelta en `t()`** (los trozos de
  f-string no se pueden envolver y se marcan aparte). Hoy son **0**.
⚠️ Para que ese cero significara algo hubo que arreglar el extractor dos veces más:
contaba como «sin envolver» lo que ya estaba dentro de `t(...)`, y al aplanar las listas
perdía la marca de f-string, así que 7 trozos salían como cadenas sueltas.

"""

ANCLA = "## i18n F1d + F2: los correos y LA APP DE CAMPO, en inglés (v439)"
assert s.count(ANCLA) == 1, f"ancla de sección: {s.count(ANCLA)}"
s = s.replace(ANCLA, SECCION + ANCLA, 1)

FILA = ("| v440 | **i18n F3: TODA la interfaz de gestión en inglés** — 15 módulos, "
        "~1.100 etiquetas, **0 cadenas sueltas sin `t()`**. ⚠️ Antes hubo que tapar tres "
        "huecos del extractor, los tres silenciosos: filtraba por **idioma** (ciego a 13 "
        "de 15 palabras probadas), se traía **claves de widget** (`st.form(key)` → la "
        "clave dependería del idioma y el formulario perdería su estado) y no veía "
        "**cabeceras de tabla ni tarjetas KPI** (71 `column_config` + las etiquetas "
        "dentro de `kpi_row`). En `column_config` se traduce la etiqueta y **nunca la "
        "clave**, que es la columna que `st.data_editor` devuelve. ⚠️ **Volví a romper "
        "`quotes_ui`** metiendo `t(...)` donde `t` ya era variable — tercera vez (v437, "
        "v439): la causa era comprobar el ámbito DESPUÉS de traducir, así que ahora hay "
        "**pre-vuelo** (`pre_i18n.py`), que señaló 46 funciones. ⚠️ Su primera versión "
        "daba falsos positivos: un `lambda t:` y un `[t for t, e in …]` **no ligan `t`** "
        "(trampa nº3) — los reales eran 7. Guardián probado contra 6 roturas; **dos solo "
        "se cazaron tras corregirlo**, las dos por medir por idioma: una afirmaba una "
        "clave que no existe (**FALLO con el código correcto**) y la otra no veía «Neto a "
        "pagar». El invariante que sí mide: **toda cadena suelta de display envuelta en "
        "`t()`** |\n")

ANCLA_T = "| v439 | **i18n F1d + F2: los correos y LA APP DE CAMPO, en inglés**"
assert s.count(ANCLA_T) == 1, f"ancla de tabla: {s.count(ANCLA_T)}"
s = s.replace(ANCLA_T, FILA + ANCLA_T, 1)

s = s.replace("## Versiones desplegadas (v439 = actual)",
              "## Versiones desplegadas (v440 = actual)", 1)

DOC.write_text(s, encoding="utf-8")
print(f"OK — CLAUDE.md {len(s.splitlines())} líneas")
