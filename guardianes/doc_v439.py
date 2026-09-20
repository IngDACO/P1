"""Documenta v439 en CLAUDE.md: sección propia + fila en la tabla de versiones."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DOC = Path(r"C:\Users\diego\P1\CLAUDE.md")
s = DOC.read_text(encoding="utf-8")

SECCION = """## i18n F1d + F2: los correos y LA APP DE CAMPO, en inglés (v439)

Cierra F1 (todo lo que SALE de la empresa) y hace F2 entera. **235 reemplazos**: 13 en
`notify.py` / `alerts.py` (correos de asignación e inducción, alarmas de problema y de
cambio) y 222 en los cuatro módulos que usa el técnico en obra — `timeclock_ui`,
`prestart_ui`, `ausencias_ui`, `route_ui`. Los correos van con **`d` (idioma BASE)** y la
pantalla con `t`: un correo SALE de la app, así que su idioma no puede depender de cómo
tenga la pantalla quien lo dispara (regla de v436).

### ⚠️ DOS `UnboundLocalError` que introduje yo, y que «compila e importa» NO ve
Al traducir aparecieron llamadas a `t()` en funciones donde `t` **ya era una variable**:
```python
# timeclock_ui._aviso_olvido
lineas.append(f"- **{etq}** {t('open since')} ...")   # ← línea 402
t = _dt.strptime(s["clock_in"], timeclock.FMT)        # ← línea 404: la marca LOCAL
```
Python marca el nombre local en el **ámbito ENTERO de la función**, así que las llamadas
de ARRIBA revientan. Es el fallo del glosario de v437, cometido otra vez el mismo día —
y el segundo es peor: en `render_mis_ausencias` el `for t, cfg in AU.TIPOS.items()` deja
`t` como una CADENA, así que `t("What do you need?")` daba **`TypeError: 'str' object is
not callable`** y la pantalla «Mis ausencias» **no abría en absoluto**.
Mi verificación de F2 fue *«los cuatro compilan e importan»* y eso **no ejercita nada**:
importar no ejecuta (la lección de v378). Lo cazó el guardián, mirando el ÁMBITO.
→ En estos módulos `t` se queda como nombre del motor y las variables se renombran
(`_ci`, `_tp`, `_k`); en los seis de v438, donde `d` era variable en 14 sitios, se hizo
al revés (alias `_d`). El criterio es cuál de los dos hay menos veces.

### ⚠️ Los cambios de `notify.py` y `alerts.py` NO estaban en el disco
El guardián los dio por no aplicados y era cierto: el fichero seguía en español pese a
que el registro de trabajo decía que se habían aplicado. Se reaplicaron y se verificaron
**generando los mensajes**, no leyendo el código. Sirve de recordatorio de que un paso
«hecho» sin evidencia comprobable no está hecho.

### Lo que NO se traduce
Las **claves de dato** — `usuario`, `proyecto`, `fecha`, `clock_in`, `tipo`, `Desde`,
`Hasta`, `Tipo`, `Estado`, `Usuario`, `Ubicacion`, `ProyectoID` — son claves de dict y
nombres de columna: traducirlas rompe la lectura **sin dar ningún error**. Tampoco los
mensajes de **log** (⚠️ `logger.warning` comparte NOMBRE con `st.warning`, y el extractor
los coló 92 veces en la primera pasada: hay que filtrar por RECEPTOR, no por atributo).

### Verificación
`verif_v439.py`, 24 comprobaciones, con los correos **generados de verdad** y los
remitentes interceptados (`notify_user` / `_notify` sustituidos: no sale ni un correo ni
un Telegram). Probado contra **8 roturas** — y **tres solo se cazaron tras corregir el
guardián**, las tres por chequeos que aprobaban por el motivo equivocado:
- **Traducir UNA de las seis apariciones de `"clock_in"`** pasaba: yo comprobaba
  PRESENCIA, y quedaban cinco. Y una traducción PARCIAL es la peor variante (unos sitios
  leen la clave vieja y otros la nueva). Ahora se pinta el número **MÍNIMO** de
  apariciones — mínimo y no igualdad, para que añadir usos legítimos no lo ponga rojo.
- **«Recorded» → «Registrados»** era invisible: el detector de español busca acentos y
  palabras funcionales, y «Registrados» no tiene ninguna de las dos. Es exactamente el
  «Planificado» de v438 → chequeos **POSITIVOS**, el inglés esperado tiene que ESTAR.
- La rotura del logger apuntaba a `route_ui`, que **no tiene ni una llamada a logger**:
  una rotura sobre código que no existe no prueba nada (el `<marker>` de v438).

### ⚠️ Y la corrección de escala que hay que decir en voz alta
Lo pendiente NO son los ~1.153 literales que cité al planificar: un barrido completo da
**3.122**. Mi primera cuenta salía de una lista blanca de funciones de Streamlit y veía
solo una parte. Ese número incluye además DATOS (columnas, formatos, claves), así que
cada uno necesita el juicio etiqueta-vs-dato — no es un reemplazo mecánico. F3, F4 y F5
van fase a fase, con guardián y deploy propios.

"""

ANCLA = "## i18n F1c: los DIAGRAMAS y las PLOMADAS. **F1 CERRADO** (v438)"
assert s.count(ANCLA) == 1, f"ancla de sección: {s.count(ANCLA)}"
s = s.replace(ANCLA, SECCION + ANCLA, 1)

FILA = ("| v439 | **i18n F1d + F2: los correos y LA APP DE CAMPO, en inglés** — cierra F1 "
        "y hace F2 entera (235 reemplazos: 13 en `notify`/`alerts`, 222 en los 4 módulos "
        "de obra). Los correos van con **`d` (idioma BASE)** y la pantalla con `t`. "
        "⚠️ **Dos `UnboundLocalError` que introduje yo**: al traducir aparecieron llamadas "
        "a `t()` en funciones donde `t` YA era variable, y Python la marca local en el "
        "ámbito ENTERO — el peor dejaba **«Mis ausencias» sin abrir** (`'str' object is not "
        "callable`). Mi verificación fue «compilan e importan», que **no ejercita nada**. "
        "⚠️ Y los cambios de `notify`/`alerts` **no estaban en el disco** pese a figurar como "
        "hechos: se reaplicaron y se verificaron GENERANDO los mensajes. Guardián probado "
        "contra 8 roturas — **tres solo se cazaron tras corregirlo**: comprobar PRESENCIA "
        "dejaba pasar traducir 1 de 6 apariciones de una clave, «Registrados» es invisible "
        "para el detector de español (→ chequeos POSITIVOS, el «Planificado» de v438) y una "
        "rotura apuntaba a un módulo **sin ningún logger**. ⚠️ Corrección de escala: lo "
        "pendiente son **3.122 literales**, no los 1.153 que cité — mi lista blanca veía "
        "solo una parte, y el número incluye datos |\n")

ANCLA_T = "| v438 | **i18n F1c: los DIAGRAMAS y las PLOMADAS — F1 CERRADO**"
assert s.count(ANCLA_T) == 1, f"ancla de tabla: {s.count(ANCLA_T)}"
s = s.replace(ANCLA_T, FILA + ANCLA_T, 1)

s = s.replace("## Versiones desplegadas (v438 = actual)",
              "## Versiones desplegadas (v439 = actual)", 1)

DOC.write_text(s, encoding="utf-8")
print(f"OK — CLAUDE.md {len(s.splitlines())} líneas")
