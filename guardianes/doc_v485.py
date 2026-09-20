# -*- coding: utf-8 -*-
"""Documenta v485 en CLAUDE.md."""
import io

P = "C:\\Users\\diego\\P1\\CLAUDE.md"

SECCION = """## ⚠️ La tabla del parte pintaba «None», y la red que lo vigila estaba CIEGA (v485)

Encontrado **mirando la pantalla** de v484 en producción, no leyendo código: las celdas
de los días de la tabla del parte salían con el literal **`None`**. El CSV estaba bien
—ahí emito `""` explícitamente— pero la tabla que lee el responsable de nómina decía
`None` en cada día sin horas.

Causa: `f["horas"].get(d)` devuelve `None` para los días que faltan y, **con la columna
entera vacía, pandas la deja en `object` y Streamlit imprime el texto**. Es literalmente
el fallo que documentó v467, repetido. Arreglo: `float("nan")`, que deja la columna en
float y la celda vacía.

### ⚠️ Lo grave no era el `None`: era que su red diera «0»
`verif_v467` tiene una red para exactamente esto, y decía **0 celdas con None** con el
fallo delante. Tenía **tres** cegueras, y se descubrieron una a una **probándola contra
el fallo reintroducido**, no leyéndola:

| Ceguera | Por qué se escapaba |
|---|---|
| solo veía el ternario `A if c else None` y el `None` literal | lo mío es un **`.get(k)` sin defecto**, que devuelve None *implícitamente* |
| solo miraba DENTRO de la llamada a `pd.DataFrame(...)` | mi dict se construye fuera y a `DataFrame` le llega una **variable** — el mismo agujero que v471 tuvo que cerrar |
| solo miraba `ast.Dict` | el mío es un **`ast.DictComp`**, que tiene `.key`/`.value` y no `.keys`/`.values` |

Con las tres, su «0» no significaba nada para esa tabla. **Un «0» vale solo para la
forma que la red sabe ver** (v450), y esta red llevaba desde v467 sin saber ver ninguna
de las tres.

### ⚠️ Y ensancharla de golpe la volvió inservible: dos pasadas de falsos positivos
1. Marcando **todo** `.get()` de un argumento salieron **12 sitios sanos**: una fila de
   hoja se lee con el nombre LITERAL de su cabecera y `hojas.registros` **siempre las
   trae todas**, así que `r.get("Type")` nunca da None — da `""`, que sí sale vacío. El
   discriminador de verdad es la **clave VARIABLE**: lo que puede faltar es la clave
   calculada.
2. Recorriendo la **función entera** salieron **5 dicts sanos** que no alimentan ninguna
   tabla. Se arregló resolviendo la variable que recibe `pd.DataFrame`, que es la sonda
   de v471.

Las dos veces la tentación era relajar el chequeo o «arreglar» código sano. ⚠️ **Un
detector que grita sobre lo que está bien acaba ignorándose entero**, así que el criterio
es: precisión primero, y validar en LAS DOS direcciones — 0 con el código bueno, y caza
exactamente un sitio con el fallo dentro. Es lo que se hizo.

### Verificación
La red, validada en las dos direcciones tras cada iteración (tres, hasta que dejó de
tener falsos positivos y empezó a cazar el caso real), y suite entera.
"""

FILA = ("| v485 | ⚠️ **La tabla del parte pintaba «None»** en cada día sin horas — visto "
        "MIRANDO la pantalla de v484 en producción, no leyendo. Con la columna entera "
        "vacía pandas la deja en `object` y Streamlit imprime el texto: es el fallo de "
        "v467 repetido (el CSV sí estaba bien). Arreglado con `NaN`. ⚠️ **Y lo grave era "
        "que su red diera «0» con el fallo delante**: tenía TRES cegueras —solo veía el "
        "ternario y el `None` literal (lo mío es un `.get()` **sin defecto**), solo miraba "
        "DENTRO de `pd.DataFrame(...)` (mi dict llega por **variable**, el agujero de "
        "v471) y solo `ast.Dict` (el mío es un **DictComp**)—, así que su cero no "
        "significaba nada para esa tabla. ⚠️ Ensancharla de golpe dio **12 falsos "
        "positivos** (una fila de hoja se lee por nombre LITERAL y `registros` siempre "
        "trae todas las cabeceras → nunca da None) y luego **5 más** al recorrer la "
        "función entera. El discriminador real es la **clave VARIABLE**, y la sonda "
        "resuelve la variable. Validada en las DOS direcciones tras cada iteración |\n")

s = io.open(P, encoding="utf-8").read()
ANCLA = "## Versiones desplegadas (v484 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))
s = s.replace(ANCLA, SECCION + "\n## Versiones desplegadas (v485 = actual)")
s = s.replace(CAB, CAB + FILA)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: seccion v485 + fila + cabecera")
