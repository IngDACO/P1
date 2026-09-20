"""Añade la sección de v437 a CLAUDE.md, antes de la tabla de versiones."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = Path(r"C:\Users\diego\P1\CLAUDE.md")
s = p.read_text(encoding="utf-8")

SEC = """## i18n F1b: el informe del CLIENTE, en inglés (v437)

Sigue a v436 (los cinco PDF comerciales). Este es el documento más visible que sale de
la empresa, y traducir solo sus encabezados lo habría dejado peor que antes: **cinco de
sus doce secciones las escribe la IA**, así que el prompt del informe del cliente entra
en el mismo lote. El prompt del informe ADMIN **no** se toca: es interno, y va en F5.

### ⚠️ EL FALLO QUE HABÍA DETRÁS: el veredicto se deducía del TEXTO de la IA
```python
_cortes = "requiere cortes" in str(ia.get("cortes", "")).lower() or "cortar" in ...
```
De ahí salía si el veredicto verde dice «con los cortes indicados en la sección 3» o
«sin valores fuera de límite». Era frágil **ya en español** —basta con que el modelo
redacte distinto— y con la IA escribiendo en inglés esa frase no casaría **nunca**: el
informe diría «sin valores fuera de límite» en un hueco que sí hay que cortar.
→ Nueva **`interpretation.cortes_por_piso(lim, best)`**, la ÚNICA definición de «hay
cortes» (OR/OL por encima de su límite, por piso). La usan el veredicto **y** el payload
de la IA, así que no pueden hablar de cortes distintos. Un dato se saca de los datos.

### Lo que NO se traduce, y por qué
| | |
|---|---|
| **Claves de `USER_SCHEMA`** (`resumen`, `cortes`…) | se guardan en `Proyectos.InterpJSON` y las lee `ia.get("resumen")` → traducirlas dejaría las 5 secciones **en blanco** en todos los informes, sin ningún error |
| **Claves de `schedule_table` / `plumb_table` / `plumb_checks`** | las produce otro módulo; el informe traduce el ENCABEZADO y sigue indexando por la clave |
| **`INF-AAAAMMDD-HHMM`** | es el número de informe, un identificador opaco; cambiar el prefijo cambiaría la numeración de aquí en adelante |

### ⚠️ Dos fallos MÍOS que solo se vieron GENERANDO el PDF
1. **`for i, (t, d) in enumerate(_terms)`** en el glosario: la variable del bucle **tapa
   la función `d()`** del motor de idiomas en TODA la función (Python la marca local en
   el ámbito entero), así que las 40 etiquetas de arriba reventaban con
   `UnboundLocalError`. Compilar ✓, importar ✓ — solo lo caza generar el documento.
   El guardián comprueba ahora que ninguna variable del módulo se llame `d`.
2. **`cortes_por_piso(limits or {}, …)`** cuando el parámetro se llama `calculated`:
   NameError **que mi propio `except` se tragaba**, dejando `_cortes = False` para
   siempre. Es la lección de v323/v338/v344 —un `except` alrededor de código recién
   escrito esconde justo el fallo que acabas de introducir— y solo se vio **leyendo el
   log** del módulo mientras se generaba el PDF. El guardián captura ese logger y falla
   si aparece un solo aviso.

### Verificación
`verif_v437.py`, **34 comprobaciones**, probado contra **10 roturas**: las caza las 10 —
pero dos solo tras corregirlo, las dos por chequeos que aprobaban por el motivo
equivocado:
- «un título de sección vuelve al español» pasaba porque yo miraba el **ÍNDICE**, no la
  cabecera. Ahora se comprueba por AST que ningún `_section`/`_callout` reciba un
  literal, y además los 12 títulos en el PDF.
- ⚠️ Y ese chequeo nuevo daba **FALLO con el código correcto**: `_section` **parte** el
  título («05» a un lado, el texto al otro), así que buscar «5. Shaft diagrams» entero
  no casa nunca — y los otros diez pasaban… **porque el índice contiene esas mismas
  cadenas**. Se compara el título SIN el número, que es lo que se pinta.
- Las etiquetas KPI se comparan en mayúsculas: **el estilo las sube**, y compararlas tal
  cual daba FALLO con el informe perfecto (el test fallando por su propio formato, v372).

### ⚠️ Lo que SIGUE en español dentro de ese PDF (medido, no supuesto)
**37 líneas**, y ninguna es de F1b: las etiquetas de los diagramas (`diagrams.py`,
`plumb.py` → **F5**), los nombres de las líneas de plomada (`plumb.LINE_NAMES` → **F4**)
y los **nombres de las actividades** del cronograma (`schedule.ACTIVIDADES`, que además
se GUARDAN en la hoja `Actividades` → migración del histórico). El informe del cliente
no está entero en inglés hasta que caigan esas tres, y conviene saberlo antes de
enseñárselo a un cliente.

"""

anc = "## Versiones desplegadas (v434 = actual)"
assert s.count(anc) == 1, f"ancla {s.count(anc)}×"
s = s.replace(anc, SEC + "## Versiones desplegadas (v437 = actual)", 1)

FILA = """| v437 | **i18n F1b: el informe del CLIENTE en inglés**, con el prompt de la IA incluido — traducir solo los encabezados habría dejado **5 de las 12 secciones en español**, porque las escribe el modelo. ⚠️ **Y detrás había un fallo**: el veredicto se deducía del TEXTO de la IA (`"requiere cortes" in ia["cortes"]`), frágil ya en español e **imposible en inglés** — habría dicho «sin valores fuera de límite» en un hueco que sí hay que cortar. Nueva `interpretation.cortes_por_piso`, única definición, compartida con el payload de la IA. ⚠️ **NO se traducen las claves** de `USER_SCHEMA` (se guardan en `InterpJSON`: traducirlas dejaría las 5 secciones EN BLANCO) ni las de las tablas de cronograma y plomado. ⚠️ **Dos fallos míos que solo se vieron GENERANDO el PDF**: la variable del bucle del glosario se llamaba `d` y **tapaba la función del motor** en toda la función (UnboundLocalError; compilar e importar no lo ven), y `cortes_por_piso(limits…)` con el parámetro llamado `calculated` → NameError **que mi propio `except` se tragaba** dejando `_cortes=False` (v323/v338/v344 otra vez), visto solo al leer el log. Guardián probado contra **10 roturas**; dos solo se cazaron tras corregirlo — uno miraba el ÍNDICE en vez de la cabecera, y su sustituto daba **FALLO con el código correcto** porque `_section` PARTE el título |
"""
anc2 = "| v434 | ⚠️ **`list_users` se COMÍA"
i = s.find(anc2)
assert i > 0
s = s[:i] + FILA + s[i:]

p.write_text(s, encoding="utf-8")
print("CLAUDE.md actualizado con v437")
