# -*- coding: utf-8 -*-
"""Documenta v471 en CLAUDE.md."""
import io

P = r"C:\Users\diego\P1\CLAUDE.md"
s = io.open(P, encoding="utf-8").read()

SECCION = """## Auditar «¿qué falta?» destapó una pantalla que revienta (v471)

El usuario pidió no dejar nada pendiente. La lista se auditó **contra el código**, no
contra el documento — porque en v453 ya estuvo mal en las dos direcciones—, y de la
única deuda que v468 dejó anotada («las claves de display quedaron inconsistentes»)
salieron **cinco fallos reales**, uno de ellos un crash.

### ⚠️ EL GRAVE: `KeyError` en 💰 Costos
```python
_tot = sum(P._num(_ed.iloc[i]["Hours"]) * ...)   # la fila tiene "Horas"
```
El bloque «Cuánto ganas con cada persona» **revienta** en cuanto alguien tiene horas
fichadas en esa obra. Confirmado con `git log -S`: la clave de la fila es de **v360** y
esa lectura la introdujo **v468** — o sea que la migración de columnas renombró **la
lectura y no la clave**, y lleva dos versiones así. Invisible solo porque la demo se
vació en v456. Probado ejecutando: antes `KeyError`, ahora da 616,95.

### Y otros cuatro del mismo renombrado a medias
| Dónde | Qué pasaba |
|---|---|
| `projects_ui` · `disabled` | decía `"Hours"` con la columna en `"Horas"`, así que **las horas quedaban editables** — y vienen del fichaje |
| `quotes_ui` · `disabled` | decía `"Cost"` con la columna en `"Costo"`: **el costo de una cotización quedaba editable**, y está congelado a propósito desde v355/v356 porque el precio se calcula sobre él |
| `clientes_ui` · `column_config` | configuraba `"Progress"` y `"Cost"`, la fila tiene `"Avance"` y `"Costo"` → la barra de progreso no se aplicaba y **la columna de dinero perdió su `$%,d`**, o sea que v468 reintrodujo ahí el fallo de v399 |
| 8 cabeceras | se pintaban con su **clave cruda, en español**, dentro de tablas por lo demás inglesas (`Actividad`, `Inicio real`, `Fin real`, `Riel`, `Avance`, `Ganancia`) |

⚠️ Las claves NO se renombran: `Riel` y `Actividad` las **lee** el código de vuelta y
`Riel` además viaja a `DatosJSON` (v443), así que reabrir un cálculo dejaría de casar.
Lo que se cambia es la ETIQUETA, en `tabla.CABECERAS` — una definición para todas.

### ⚠️ `verif_v444` estaba VERDE con dos de esos huérfanos delante
Y por su propio fallo documentado, entrando por otra puerta. v444 ya excluye su
`column_config` de las «filas» porque si no **se aprobaba a sí mismo**… pero solo el
dict INLINE. Cuando llega por VARIABLE (`_colcfg = {...}` → `tabla.cfg(None, _colcfg)`)
ese dict sigue viviendo en la función, sus claves entraban en `filas` y el chequeo se
volvía a aprobar solo. Arreglado resolviendo la variable: pasa de mirar 24 tablas a 25,
y ahora sí caza el huérfano de `clientes_ui`.

### El guardián nuevo mira las DOS formas que v444 no ve
Una tabla editable tiene tres cosas que se desincronizan igual de calladas —el
`column_config` (v444), **la LECTURA del resultado** y **el `disabled`**— y v468 las
rompió en las tres. `verif_v471` cubre las dos que faltaban, más la cabecera cruda.
⚠️ Y las tres sondas **resuelven variables**: casi ninguna de estas tablas construye su
DataFrame inline, y mirando solo dentro de la llamada **4 de 5 salían como huérfanas
sin serlo** — habría «arreglado» código sano. Es el agujero del medidor de v450.
⚠️ Cada sonda **se valida a sí misma** contra un caso conocido-bueno antes de creerse su
cero: es literalmente lo que a v444 le faltaba (trampa nº12).
Batería: **5 roturas, 5 cazadas** + control verde, con verde de base primero.

### Lo demás de la auditoría, medido y CERRADO
| | |
|---|---|
| **Fallbacks de idioma** (`columnas.canon`, `valores.canon`) | **0 lecturas por clave vieja** en todo el repo: nadie depende de ellos en el CÓDIGO. Solo cubren DATOS viejos, y las hojas ya están migradas. Retirarlos es una DECISIÓN, no un pendiente — y se quedan mientras pueda entrar un cliente con histórico |
| **Red 14 de i18n** (concatenación) | 14 casos, **0 en español**: son fragmentos de markdown con variables. Cerrado |
| **Display sin `t()`** | 4, y las 4 son **solo iconos** (`:material/...:`): nada que traducir. ⚠️ El primer barrido dio 25 porque contaba `logger.warning` como texto de pantalla — el error de v439/v461, cometido otra vez; se filtra por RECEPTOR |
| **7 guardianes «SIN DATOS»** | de 108. **No es un fallo pero sí cobertura perdida**, y sigue abierto: mientras la demo esté vacía, esas 7 afirmaciones no se comprueban |

"""

ANCLA = "## Versiones desplegadas (v470 = actual)"
assert s.count(ANCLA) == 1, "ancla de la tabla ausente"
s = s.replace(ANCLA, SECCION + "## Versiones desplegadas (v471 = actual)")

FILA_ANCLA = "| v470 | **Tipo de proyecto «Ripout + Installation»**"
assert s.count(FILA_ANCLA) == 1, "fila v470 ausente"
FILA = (
    "| v471 | **Auditar «¿que falta?» destapo una pantalla que REVIENTA.** De la unica "
    "deuda que v468 dejo anotada salieron **cinco fallos reales**: ⚠️ el gordo, "
    "`_ed.iloc[i][\"Hours\"]` con la fila en `\"Horas\"` → **KeyError** en 💰 Costos en "
    "cuanto alguien tiene horas fichadas; `git log -S` confirma que v468 renombro **la "
    "lectura y no la clave**, y llevaba dos versiones asi, invisible solo porque la demo "
    "esta vacia. + dos `disabled` apuntando a columnas inexistentes (**las HORAS y el "
    "COSTO de una cotizacion quedaban EDITABLES**, y el costo esta congelado a proposito "
    "desde v355) + un `column_config` huerfano que le costo a una columna de dinero su "
    "`$%,d` (**v468 reintrodujo ahi el fallo de v399**) + 8 cabeceras pintandose con su "
    "clave CRUDA en español. ⚠️ Y **`verif_v444` estaba VERDE con dos de esos huerfanos "
    "delante**, por su propio fallo documentado entrando por otra puerta: excluye su "
    "`column_config` de las «filas» solo si es INLINE, y por variable volvia a aprobarse "
    "a si mismo. Arreglado (24→25 tablas miradas) + `verif_v471` con las dos formas que "
    "v444 no ve (la LECTURA del resultado y el `disabled`). ⚠️ Las sondas **resuelven "
    "variables** —sin eso 4 de 5 salian huerfanas sin serlo y habria «arreglado» codigo "
    "sano— y **se validan a si mismas** contra un caso conocido-bueno. 5/5 roturas |\n")
s = s.replace(FILA_ANCLA, FILA + FILA_ANCLA)

io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: seccion v471 + fila + cabecera")
