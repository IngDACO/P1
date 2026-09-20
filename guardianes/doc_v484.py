# -*- coding: utf-8 -*-
"""Documenta v484 en CLAUDE.md y pone NEGOCIO.md al día."""
import io

P = "C:\\Users\\diego\\P1\\CLAUDE.md"

SECCION = """## FASE 2.2-A: el parte de horas para la nómina (v484)

El usuario eligió «Xero Payroll» y **lo primero fue descubrir que ese destino no
existe**: Xero Payroll AU **no importa partes de horas por CSV**. Tres ángulos
independientes, el primero con la sonda validada contra un caso conocido-bueno:

| Evidencia | Qué dice |
|---|---|
| El artículo «Add or edit an employee's timesheet» de Xero Central | **0 menciones** de import/CSV/template. ⚠️ Y la sonda VALE: el de importar facturas, con el mismo cascarón de 1.635 caracteres, da `csv: 2 · template: 2`, porque los títulos de paso sí están en el cascarón |
| **Product Ideas de Xero** | petición **abierta y popular**: *«AU Payroll \\| Timesheets — Ability to Import Timesheet templates from excel»*. Si existiera, no se pediría |
| Sus foros | importar partes por CSV «no está en sus planes a corto plazo», y el camino sería **por API** — que es lo que hacen TimeDock y Upsheets |

Y su documentación lo confirma desde el otro lado: un parte se crea con
**`EmployeeID`, `EarningsRateID` y `TrackingItemID` — GUIDs** que solo se obtienen ya
conectado, y **`NumberOfUnits` es un array con una entrada por día del periodo**.

Así que se construyó **lo que sí sirve en cualquier rama** (decisión del usuario: «A y
luego B»): el parte propio, que un responsable de nómina teclea y que alimenta a
cualquier proveedor. ⚠️ Y de leer esa API salió el diseño: **el formato es ANCHO, una
columna por día y EN ORDEN**, porque así es el array — cuando exista OAuth, 2.3 es un
mapeo y no una reescritura.

### ⚠️ UNA definición de «qué día de ausencia se paga»
El parte necesita la ausencia día a día y `horas_pagadas_grupo` solo daba el agregado.
Reimplementar el criterio en el exportador habría creado **una segunda definición de lo
que se paga**, y eso no lo delata ninguna línea de la colilla: solo el total del día.
El criterio baja a **`ausencias.horas_pagadas_dia`** y el agregado **DELEGA**.
- ⚠️ **La semántica se preserva EXACTA**, incluido lo que parece raro: `por_tipo` y
  `dias` cuentan TODOS los días del rango, también los que pagan 0 porque la persona
  trabajó la jornada entera — son días CONCEDIDOS, que es lo que descuenta del saldo.
- ⚠️ Y **no se le puso tope por día** aunque dos ausencias sobre el mismo día pagarían
  dos veces: `solicitar` **ya impide** los solapes, así que sería arreglar un caso que
  la app no permite (lección v369) y cambiaría el agregado que la nómina ya usa.
- **Demostrado, no supuesto**: la demo tiene 0 ausencias, así que compararlo contra la
  hoja real habría sido el paso en vacío. Se sacó la implementación ANTERIOR del commit
  con `git show`, se ejecutó en el espacio de nombres del módulo y se comparó sobre las
  MISMAS filas: **13 casos idénticos**, incluida la rama del `except`.

### Lo que el parte exporta, y lo que NO
**Jornada fichada + ausencias pagadas**, que es lo que se PAGA — la misma base que
`payroll.generar`. ⚠️ Las horas de OBRA no entran: son lo que se le COBRA al cliente y
pueden ser más que la jornada (la app ya lo mide desde v320/v422), así que sumarlas
pagaría de más. El desvío **se avisa** en vez de sumarse.

Y el recorte de v432 viaja entero: en un día con ausencia **y** fichaje salen
`Ordinary Hours 4.68` + `Annual Leave 3.32` = **8.00**. Un día paga una jornada.
⚠️ Un día sin horas va **VACÍO, no en 0**: un 0 afirma «ese día trabajó cero».

### `PayrollID`, y el pendiente que casi dejo sin cerrar
Nuestra identidad es el login (v306/v413) y el proveedor no lo conoce: casa por nombre,
y el nombre **puede repetirse**. Columna nueva al final de `Login` (migra sola),
opcional, con respaldo al nombre — y el aviso salta **solo cuando el nombre se repite**,
porque un aviso que grita sobre lo que está bien acaba ignorándose entero (v450).
- ⚠️ `_COL` (v433) y la proyección de `list_users` (v434) **la recogieron solas**: las
  dos derivaciones que se hicieron a golpes pagando su precio.
- ⚠️ **Y se me quedaba sin editor.** La columna existía y no había dónde ponerla: el
  «pendiente que nadie puede cerrar» de v325/v340, con el parte avisando de un homónimo
  ambiguo sin ofrecer forma de resolverlo. Está en la ficha → 🔑 Acceso, y el guardián
  lo exige.
- Entra en `CAMPOS_CLAVE` **en el mismo lote**: no es un importe, pero equivocarlo paga
  a otra persona (la regla que v344, v352 y v373 aprendieron a golpes).

### ⚠️ Tres roturas se escaparon, y solo UNA era un fallo del guardián… de dos formas
| Escapó | Qué era |
|---|---|
| el aviso de homónimos salta con nombre ÚNICO | **hueco mío**: en mi fixture la persona de nombre único **no tenía horas**, así que sin horas no entra en el parte y ese caso no se ejercitaba NUNCA |
| `PayrollID` se mete en MEDIO de la cabecera | **hueco mío**: comprobaba solo el ÚLTIMO elemento, y la rotura insertaba otro nombre antes. Lo que protege la regla es que **nada se cuele delante de las históricas** (v363: las filas se escriben por POSICIÓN), así que ahora se fija el PREFIJO |
| los días se RECUENTAN en vez de venir del detalle | **NO es un fallo**: medido, **nadie lee `dias`** del agregado —`payroll.generar` usa `recortados`, `nombre`, `horas` y `por_tipo`— así que la rotura no corresponde a ningún defecto. Salió de la batería con la razón escrita, en vez de inventar un caso inalcanzable para justificarla |

### ⚠️ Y la batería dejó código ROTO en el árbol de trabajo
El `finally` que restaura reventó con **`OSError 22`** al reabrir el fichero, y la tanda
murió dejando `ausencias.py` **con el doble pago de v432 vivo**. Causa: el patrón
`io.open(...).write(...)` deja el descriptor a merced del recolector, y en Windows la
reapertura del mismo fichero en el bucle falla.
→ Ahora la batería (a) escribe con `with`, (b) hace **copia en disco ANTES** de tocar
nada, (c) **verifica** el restore leyendo el fichero y reintenta, y (d) **aborta la
tanda** si no puede, porque seguir con código roto en el árbol es peor que no haber
probado nada. **Un `finally` que puede fallar no es una garantía.**

### Y la trampa de v455, cometida
Toqué `auth_ui.py` **con la suite corriendo**, así que esa corrida quedó nula y hubo que
pararla y repetirla. La regla ya estaba escrita: *los scripts que modifican el árbol
nunca se solapan con nada que lea el código*.

### Verificación
`verif_v484.py`, **72 comprobaciones**, todo ejecutando donde importa: el oráculo del
agregado ⚠️ **escrito aquí y no sacado de `git show HEAD:`** (en cuanto se commitea,
HEAD tendría el código nuevo y el chequeo se quedaría vacío — un chequeo que caduca
solo), los conceptos derivados de `ausencias.TIPOS`, el criterio de v432 llegando al
CSV, el orden de las columnas, el día vacío, las dos guardas del setter genérico, el
editor del `PayrollID` y **la pantalla entera EJECUTADA**. Batería: **17 roturas, 17
cazadas + CONTROL verde**, con el verde de base comprobado antes.

### Lo que NO está hecho, dicho como límite
**B (la API) no está empezada.** Necesita una app en `developer.xero.com` y una
organización demo, que son del usuario. Lo que este parte deja resuelto es la forma: la
fila de aquí es la línea de allí y el orden de las columnas es el del array.
"""

FILA = ("| v484 | **FASE 2.2-A: el parte de horas.** ⚠️ El usuario eligió Xero Payroll y "
        "lo primero fue descubrir que **ese destino no existe**: Xero Payroll AU no "
        "importa partes por CSV — su artículo no tiene paso de import (⚠️ con la sonda "
        "validada: el de facturas, con el mismo cascarón, sí lo tiene), su Product Ideas "
        "lo pide y sus foros dicen que iría por API. Así que se construyó lo que sirve en "
        "cualquier rama, y ⚠️ **de leer su API salió el diseño**: formato **ANCHO, una "
        "columna por día y en ORDEN**, porque `NumberOfUnits` es un array por día → 2.3 "
        "será un mapeo. + ⚠️ **una sola definición de «qué día de ausencia se paga»**: el "
        "criterio de v432 baja a `horas_pagadas_dia` y el agregado DELEGA —dos "
        "implementaciones pagarían días distintos y solo lo delata el total—, "
        "**demostrado idéntico en 13 casos** contra la implementación anterior sacada del "
        "commit (la demo tiene 0 ausencias, así que la hoja real no probaba nada). + "
        "`PayrollID` (el login no lo conoce el proveedor, y el nombre se repite), que "
        "⚠️ **casi dejo sin editor** — el «pendiente que nadie puede cerrar» de v325/v340. "
        "⚠️ **Tres roturas escaparon y solo dos eran huecos míos**: la tercera cambiaba un "
        "campo que **nadie lee**, así que salió de la batería en vez de inventar un caso "
        "inalcanzable. ⚠️ Y la batería **dejó el doble pago de v432 VIVO en el árbol** al "
        "fallar su `finally` con OSError: ahora copia en disco, verifica el restore y "
        "**aborta** si no puede. 72 comprobaciones · **17/17 roturas + control** |\n")

s = io.open(P, encoding="utf-8").read()
ANCLA = "## Versiones desplegadas (v483 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))
s = s.replace(ANCLA, SECCION + "\n## Versiones desplegadas (v484 = actual)")
s = s.replace(CAB, CAB + FILA)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: seccion v484 + fila + cabecera")

# ── NEGOCIO.md ──────────────────────────────────────────────────────────────
P2 = "C:\\Users\\diego\\P1\\NEGOCIO.md"
s2 = io.open(P2, encoding="utf-8").read()

V = ("| **Nómina** | Retención y *superannuation* son porcentajes editables: **no hay STP "
     "ni interpretación de awards**. Como costeo de mano de obra es sólido; como nómina "
     "certificada, no se puede vender |")
N = ("| **Nómina** | ⚠️ Sigue sin **STP ni interpretación de awards**, así que como nómina "
     "certificada no se puede vender. Lo que v484 añade es el puente: **parte de horas "
     "exportable** (jornada + ausencias pagadas, persona × día) para que lo procese un "
     "proveedor certificado. ⚠️ Y ese trabajo **no se tira decida lo que se decida** — "
     "conectar con un proveedor y renombrar el módulo a «costeo de mano de obra» "
     "necesitan los dos lo mismo primero |")
if s2.count(V) != 1:
    raise SystemExit("ancla nomina no unica: %d" % s2.count(V))
s2 = s2.replace(V, N)

V2 = "   > ⚠️ Y la pregunta abierta que no decide el código: **nómina, ¿conectar o renombrar?**"
N2 = ("   > 🟡 **2.2-A hecha (v484)**: hay parte de horas exportable. ⚠️ Y se descubrió algo "
      "que cambia el plan: **Xero Payroll AU no importa partes por CSV** —su propia "
      "petición de esa función sigue abierta—, así que conectar las horas con Xero exige "
      "la **API**, el mismo OAuth que las facturas. Se hacen de una.\n"
      "   > ⚠️ Y la pregunta abierta que no decide el código: **nómina, ¿conectar o renombrar?**")
if s2.count(V2) != 1:
    raise SystemExit("ancla pregunta no unica: %d" % s2.count(V2))
s2 = s2.replace(V2, N2)

s2 = s2.replace("*Última puesta al día del estado de hecho: 08/09/2026 (v481-v483).*",
                "*Última puesta al día del estado de hecho: 14/09/2026 (v481-v484).*")
io.open(P2, "w", encoding="utf-8", newline="").write(s2)
print("NEGOCIO.md al dia con v484")
