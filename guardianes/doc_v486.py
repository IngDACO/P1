# -*- coding: utf-8 -*-
"""Documenta v486 en CLAUDE.md y CORRIGE lo que v467 y v485 dejaron escrito mal."""
import io

P = "C:/Users/diego/P1/CLAUDE.md"

SECCION = """## ⚠️ NaN TAMPOCO vacía la celda: v485 arregló un fallo con la cura equivocada (v486)

v485 cambió el `None` de la tabla del parte por `float("nan")`, lo desplegó, y **en
producción seguía pintando «None»**. Lo que corrige v486 no es un olvido: es una
afirmación que llevaba desde v467 escrita como **medida** y era falsa.

### ⚠️ Mi error de medición: leí el AGREGADO y lo atribuí a la columna que esperaba
La sonda local de v485 pintaba dos columnas a la vez —una de `None` y una de `NaN`— e
interceptaba `fillText`. Devolvió `«None»: 8` y **se lo asigné entero a la columna de
`None`**. Eran 2 columnas × 2 filas × 2 repintados: **la de NaN pintaba «None»
también**. Con las coordenadas se ve de un golpe — la cabecera `NANCOL` en x=172 y
`NONECOL` en x=351, y los «None» en **x=335 (borde derecho de NANCOL) y x=352** —, pero
yo solo miré el recuento.
→ **Un agregado no dice nada hasta saber QUÉ está contando.** Es la trampa nº12 en su
forma más barata de evitar: la misma sonda, mirando `x`.

### El cuadro, medido con una tabla por caso y control incluido
Una tabla por candidato con **una sola columna de datos**, para que ningún «None» pueda
atribuirse a otra cosa:

| valor de la celda | `column_config` de esa columna | se pinta |
|---|---|---|
| `nan` · `None` · `pd.NA` | ninguno · `{}` · `Column()` · `NumberColumn` · `+format` · `TextColumn` | **«None»** |
| `nan` + `Styler(na_rep="")` | — | **«None»** |
| **`""`** | **ninguno o `Column()`** | **vacío** |
| `""` | `NumberColumn` (con o sin formato) | **«None»** |

Ese «None» es el **placeholder de valor ausente** de Streamlit, y el control lo
confirma: con `column_config` **ninguno** también sale (`_F`), así que `tabla.cfg()`
queda exculpado. Y la última fila es la que decide el arreglo: **una columna TIPADA
convierte incluso la cadena vacía en nulo**, así que las dos piezas —cadena + columna
sin tipar— van juntas o ninguna sirve.

⚠️ `st.column_config.Column(label, alignment="right")` conserva los números a la
derecha, así que no se pierde la lectura de una columna de dinero. Pero `alignment` es
reciente y `requirements.txt` admite desde 1.39: `tabla.derecha()` **degrada** a la
columna genérica en vez de tumbar la tabla entera.

### No era una tabla: eran CUATRO
La frase «con `NaN` sale vacía — **medido**» está en CLAUDE.md desde v467 y se aplicó en
cuatro sitios, todos vivos:

| Dónde | Qué se veía |
|---|---|
| `contable_ui` · el parte de horas | «None» en cada día sin horas (v485) |
| `payroll_ui` · `Rate/h` | ⚠️ y el pie de esa misma tabla **PROMETE** *«an empty Rate/h means that person has no rate set»* |
| `inventory_ui` · `Costo` del historial | «None» en el movimiento sin costo |
| `catalogo_ui` · `Horas` | «None» en cada producto |

**Una afirmación equivocada documentada como medida no se queda quieta: se copia.**

### `tabla.celda` + `tabla.derecha`: una definición, no cuatro comentarios
El importe se formatea en Python y la columna se declara sin tipar. Verificado
**ejecutando** que el formato pinta IDÉNTICO al `NumberColumn` que sustituye —19 valores
× 2 formatos, 0 diferencias—, porque son columnas de dinero y un cambio de formato
habría movido cada cifra de esas pantallas en silencio. ⚠️ Y `%d` **trunca** mientras
`.0f` **redondea** (trampa nº20), así que se compara contra el camino viejo COMPLETO: el
`round()` que hacía el código + el printf de Streamlit.

⚠️ **No usa `theme.dinero`, a propósito**: ese escapa el `$` como `\\$` porque Streamlit
lee LaTeX en markdown (v309), y una celda de `st.dataframe` no es markdown — ahí el
escape se ve literal. Dos destinos, dos funciones.

### ⚠️ Y REINTRODUJE el fallo de v323 dentro del arreglo
`celda` hacía `float(valor)`. Con `"1,234.56"` —que es **como Sheets formatea el dinero
en AU/US**— eso revienta, así que devolvía **vacío**. Es exactamente el fallo que v323
documentó con cinco implementaciones divergentes de `_num`… y aquí era **peor**: allí
salía `$0` y aquí sale «no hay dato». Consideré importar `core/num.py`, comprobé que era
módulo hoja, y luego no lo usé.
→ Ahora usa `num(valor, None)` —`default=None` para poder distinguir un cero legítimo de
algo ilegible— y el guardián lo fija por AST, así que nadie puede volver a `float()`.
**Lo cazó comparar el formato contra el anterior**, no leer el código: 14 de 15 casos
idénticos y el que difería era ese.

### ⚠️ La red de v467 daba «0» con el fallo delante, otra vez
v485 la rehizo bien (le quitó tres cegueras) pero su **afirmación** seguía siendo falsa:
`ok("0 celdas con None (se usa NaN)")`. O sea que «arreglar» un None poniendo NaN
**pasaba el chequeo y seguía pintando «None»** — que es literalmente lo que hizo v485.
Ensanchada al NaN en sus tres escrituras (`float("nan")`, `np.nan`, `pd.NA`) y corregida
la nota, que decía lo contrario de lo medido.

⚠️ **Y una rotura SE ESCAPÓ: enumerar posiciones falló por tercera vez.** Cubría el valor
directo y la rama `else` de un ternario, y no vio `f["horas"].get(d, float("nan"))` — el
nulo metido en el **DEFECTO del `.get`**, que es EXACTAMENTE la forma que tenía v485 en
producción. Se cambió por recorrer el **subárbol** del valor: más ancho, y medido **0
falsos positivos** en el repo. Validada después en las dos direcciones: 5/5 roturas
cazadas (las tres escrituras × las tres posiciones) y el CONTROL verde.

⚠️ Y el mismo error en mi guardián nuevo: el chequeo de «`tabla.py` sigue siendo módulo
hoja» miraba el `module` de un `ImportFrom`, y **`from core import projects` tiene
`module == "core"`**, que no empieza por `"core."` — la rotura pasaba. Hay que mirar los
NOMBRES, no solo el módulo.

### Higiene: 3 `.pyc` estaban RASTREADOS en git
`survey_app/__pycache__/app.cpython-314.pyc` y dos de `extractors/`, pese al
`.gitignore` — que **no destrackea lo ya añadido**. Bytecode de Python 3.14 viajando al
Cloud, que corre 3.12 (v66). Destrackeados sin borrarlos del disco.

### Verificación
`verif_v486.py` (24 comprobaciones, todo EJECUTANDO donde decide: importar no ejecuta,
v378) probado contra **9 roturas + CONTROL**, con el **verde de base confirmado ANTES**
(sin ese paso una tanda entera sale «cazada» sin probar nada, v459/v461/v463). Las
cuatro tablas **vistas en pantalla** con el código real y datos inyectados por la
función de LECTURA de cada módulo, no replicando la expresión — que es justo el error
que me hizo dar v485 por bueno.
"""

FILA = ("| v486 | ⚠️ **NaN TAMPOCO vacía la celda: v485 arregló el fallo con la cura "
        "equivocada** y en producción seguía pintando «None». ⚠️ Mi error: la sonda "
        "devolvió `«None»: 8` y **se lo atribuí entero a la columna que esperaba** — "
        "eran 2 columnas × 2 filas × 2 repintados, o sea que **la de NaN pintaba «None» "
        "también**; con las coordenadas se veía de un golpe (x=335 es el borde derecho "
        "de la columna de NaN). *Un agregado no dice nada hasta saber QUÉ cuenta.* "
        "Medido con una tabla por caso y control: `nan`/`None`/`pd.NA` pintan «None» "
        "con cualquier config —y hasta con `Styler(na_rep=\"\")`—, y lo ÚNICO que vacía "
        "la celda es una **CADENA en una columna SIN tipar**, porque una columna tipada "
        "convierte incluso `\"\"` en nulo. **No era una tabla: eran CUATRO** (parte, "
        "`Rate/h` —cuyo pie PROMETE que vacío = sin tarifa—, Costo de inventario y "
        "Horas de catálogo), porque la frase «con NaN sale vacía, medido» está en "
        "CLAUDE.md desde v467: *una afirmación equivocada documentada como medida se "
        "copia*. Nuevas `tabla.celda`/`derecha` (una definición), con el formato "
        "verificado **idéntico** al `NumberColumn` que sustituye (19 valores × 2 "
        "formatos, 0 diferencias — son columnas de dinero, y `%d` trunca mientras "
        "`.0f` redondea). ⚠️ **Y reintroduje el fallo de v323 dentro del arreglo**: "
        "`float()` en vez de `num()` hacía que «1,234.56» —como Sheets formatea el "
        "dinero en AU— saliera **VACÍO**, o sea «no hay dato», peor que el `$0` de "
        "v323; lo cazó comparar el formato contra el anterior, no leer el código. "
        "⚠️ La red de v467 seguía afirmando «0 celdas con None (se usa NaN)», así que "
        "poner NaN **pasaba el chequeo**: ensanchada, y **una rotura se escapó** porque "
        "enumeraba posiciones y no vio el nulo en el **DEFECTO de un `.get()`** — la "
        "forma exacta de v485; ahora recorre el subárbol (0 falsos positivos). + **3 "
        "`.pyc` estaban RASTREADOS** en git pese al `.gitignore`, que no destrackea lo "
        "ya añadido | \n")

s = io.open(P, encoding="utf-8").read()
ANCLA = "## Versiones desplegadas (v485 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))

# ⚠️ Corregir la AFIRMACION FALSA donde se escribio, no solo anadir la nueva seccion:
# si se deja, el siguiente que la lea vuelve a "arreglar" un None con NaN.
CORRECCIONES = [
    # v485
    ("el fallo que documentó v467, repetido. Arreglo: `float(\"nan\")`, que deja la columna en\nfloat y la celda vacía.",
     "el fallo que documentó v467, repetido. ⚠️ **El arreglo de esta versión —`float(\"nan\")`—\nera FALSO y se corrigió en v486: el NaN se pinta «None» igual. Lo único que vacía la\ncelda es una CADENA en una columna sin tipar (`tabla.celda`).**"),
    # v467, en la tabla de versiones
    ("con TODA la columna vacia pandas la deja en `object` y Streamlit imprime el texto; con `NaN` sale vacia — medido)",
     "con TODA la columna vacia pandas la deja en `object` y Streamlit imprime el texto; ⚠️ **el «con `NaN` sale vacia — medido» que decia aqui era FALSO, corregido en v486**)"),
]
for viejo, nuevo in CORRECCIONES:
    if s.count(viejo) != 1:
        raise SystemExit("correccion no unica (%d): %.60s" % (s.count(viejo), viejo))
    s = s.replace(viejo, nuevo, 1)

s = s.replace(ANCLA, SECCION + "\n## Versiones desplegadas (v486 = actual)")
s = s.replace(CAB, CAB + FILA)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: seccion v486 + fila + cabecera + 2 correcciones de lo escrito mal")
