# -*- coding: utf-8 -*-
"""Documenta v483 en CLAUDE.md."""
import io

P = "C:\\Users\\diego\\P1\\CLAUDE.md"

SECCION = """## FASE 2 de la ruta: identidad fiscal y exportación contable (v483)

Fases **2.0** y **2.1**: que el contable deje de frenar la venta. No integra con nadie
todavía —eso es 2.3, OAuth y tokens—: produce el fichero.

### ⚠️ EL HALLAZGO: se emitían documentos fiscales INCOMPLETOS
`invoice_pdf` imprime **«TAX INVOICE»** en cada factura que sale al cliente. En Australia
un documento con ese título por **82,50 $ o más** tiene que llevar el **ABN** y el nombre
legal del emisor, y `grep -ri "abn"` daba **cero** en todo el repositorio: la marca era el
nombre INTERNO del grupo (`cliente1`). O sea que las facturas ya emitidas iban
incompletas, y nada lo señalaba.

Salió de auditar el código de dinero antes de proponer la fase, no de una revisión de
pantallas. Cuatro columnas nuevas en `Groups` —`ABN`, `LegalName`, `PaymentTermsDays`,
`AccountingJSON`— ⚠️ **al final, que es lo que las hace migrar solas**: una columna en
medio desplaza a todas las siguientes y las filas se escriben por POSICIÓN (el fallo que
mató `create_project` durante tres versiones, v363).

⚠️ Y el PDF **degrada en las tres direcciones**: sin ABN se emite igual (sin esa línea),
sin razón social cae a la marca del grupo, y si la lectura de la identidad **falla** se
emite lo mismo. Un problema de red no puede impedir facturar. Las tres se ejercitan.

### El vencimiento nacía HOY
`date_input(value=clock.today())`, así que **toda factura entraba vencida el mismo día**:
el indicador «vencido» del resumen financiero y el estado de la lista saltaban al
instante, y exportada llegaba en mora sin haberse enviado. Ahora sale del **plazo de pago
del grupo** (14 días por defecto).

### 2.1 · El CSV, con tres reglas que no son negociables
1. ⚠️ **Los importes salen SIEMPRE sin impuesto**, con el impuesto en su columna. Xero
   pregunta al importar si el fichero viene «tax inclusive» o «exclusive»: si el criterio
   cambiara según el caso, esa pregunta se contestaría mal tarde o temprano y el GST del
   cliente saldría torcido. Un solo criterio, y dicho en pantalla.
2. ⚠️ **El impuesto se REPARTE de forma que sume exactamente el de la factura.**
   Redondear línea a línea da diferencias de centavos contra un documento ya emitido y
   cobrado, y una factura que no cuadra al centavo la rebota el contable. Ejercitado
   contra la hoja real con el caso que lo motiva: tres líneas de `33,33 · 33,33 · 33,34`
   al 10 % → línea a línea da **9,99** y el reparto da **3,33 · 3,33 · 3,34 = 10,00**.
3. ⚠️ **El mapa de cuentas es POR PERFIL, no compartido**: en Xero las ventas son `200` y
   en MYOB `4-1000`. Un solo mapa habría exportado a MYOB códigos que no existen en su
   archivo — y MYOB **rechaza la fila entera**, no la avisa.

Lo que se enseña ANTES de descargar es lo que va a fallar al importar: cuentas sin poner,
**un proveedor escrito de dos formas** (los dos casan por nombre exacto, así que el gasto
del año se parte en dos fichas sin que nada avise) y la lista de trabajos que hay que
crear primero. Un importador rechaza la fila y no siempre dice por qué.

### Lo que se verificó EN LA FUENTE, no de memoria
- **Nombres de impuesto de Xero** (tabla de Australia de su documentación de la API):
  `OUTPUT` = *GST on Income*, `INPUT` = *GST on Expenses*, `EXEMPTOUTPUT` = *GST Free
  Income*, `EXEMPTEXPENSES` = *GST Free Expenses*. ⚠️ La **API usa el código** y el **CSV
  el nombre**: se guardan los dos, porque 2.3 necesitará el código.
- **Campos de importación de MYOB**: `Co./Last Name` (tiene que casar con una ficha
  EXISTENTE), `Invoice #`, `Date` en DD/MM/YYYY, `Description` ≤255, `Account #`
  (obligatorio y válido), `Amount`, `Inc-Tax Amount`, `Job`, `Tax Code` (`GST`/`FRE`/`N-T`).
- **La opción de seguimiento de Xero se corta en 50 caracteres**, así que una etiqueta
  larga **cae al ID**: recortarla podría dar la MISMA opción a dos obras distintas y el
  costo de una se cargaría a la otra.

### ⚠️ Un error de semántica MÍO, cazado volcando el CSV
La 4ª columna de MYOB es **«Customer PO» / «Supplier Invoice #»**: el número de pedido
DEL CLIENTE o la factura DEL PROVEEDOR. Yo le estaba metiendo el nombre del proyecto, que
sí es legítimo en el `Reference` de Xero (texto libre) pero ahí no: el contable lo leería
como el número del proveedor. Va vacía; el proyecto viaja en `Job`, que es su sitio.
**No se vio leyendo el código: se vio imprimiendo la fila generada.**

### ⚠️ Y una ROTURA SE ESCAPÓ: el guardián afirmaba la CONSTANTE, no lo que sale
La rotura intercambiaba el desempaquetado (`nombre, cod = …`), lo que escribe **`OUTPUT`**
en el fichero en vez de `GST on Income` — y Xero rechaza fila a fila. El guardián pasaba
en verde porque comprobaba `IMPUESTOS_XERO["venta_con"][1] == "GST on Income"`, o sea la
constante, que seguía perfecta.
→ Ahora se afirma **lo que el CSV PRODUCE**, en las dos ramas (con GST y sin GST), con la
sonda validada contra su contrario: si no supiera distinguirlas, los dos casos darían lo
mismo y el verde no significaría nada (trampa nº12). Es la familia de v309/v349/v441 —
*un guardián acota el fallo a la forma en que lo viste*— y solo lo destapó la batería.

### ⚠️ Un `NameError` que habría reventado la pantalla, cazado por el chequeo de ámbito
Escribí `_num(...)` en el editor de identidad de `auth_ui`, y **ese módulo no tiene `_num`
a nivel de módulo**: `compileall` y los imports lo dan por bueno, y habría fallado la
primera vez que alguien abriera el desplegable. Es el fallo de v423/v425/v443, cazado por
el barrido de ámbito ANTES de desplegar. ⚠️ Y al añadir el import se comprobó primero que
nadie use `_num` como VARIABLE en ese módulo: tapar un nombre lo marca local en el ámbito
ENTERO de la función (v445/v447).

### Ejercitado contra la hoja REAL (método v344), sin dejar rastro
foto → escribir las 4 columnas nuevas → factura con el redondeo que no cuadra → exportar y
leer el CSV → generar el PDF y **extraer su texto** → borrar la fila → restaurar la
identidad → segunda foto. **21 comprobaciones, 0 fallos**, y `cliente1` vuelve a 0 facturas
con el ABN vacío. El PDF llevaba `12 345 678 901` y `ZZZ Prueba v483 Pty Ltd`, y **ya no el
nombre interno del grupo**.

### Verificación
`verif_v483.py`, **80 comprobaciones**, todo EJECUTANDO donde importa (importar no ejecuta,
v378): el reparto en 7 casos —incluido uno que el redondeo ingenuo NO resuelve, o no
probaría nada—, el mapa fusionando sin borrar el otro perfil, un `AccountingJSON` ilegible
degradando a los de fábrica, el criterio único de impuesto comprobado sobre el gasto REAL,
el PDF en sus tres estados, y que el despacho deje **exactamente una** sub-sección al
`else` (la lección de v449). Batería: **15 roturas, 15 cazadas + CONTROL verde**, con el
verde de base confirmado ANTES (sin ese paso una tanda entera sale «cazada» sin probar
nada, v459/v461/v463).

### Lo que NO está probado, dicho como límite
**Que Xero y MYOB acepten el fichero no está demostrado**: hace falta importarlo en una
cuenta demo, y crear una cuenta no es algo que yo haga. Lo que sí está comprobado es que
las columnas obligatorias van completas, que la aritmética cuadra al centavo y que los
nombres de impuesto son los de su documentación. Los perfiles son **datos, no código**
(una lista de columnas y un constructor de fila), así que si el importador pide un ajuste
es una línea, no una reescritura.
"""

FILA = ("| v483 | **FASE 2 de la ruta: identidad fiscal + exportación contable.** ⚠️ El "
        "hallazgo: `invoice_pdf` imprime «TAX INVOICE» en cada factura y **no había ABN en "
        "todo el repositorio** —la marca era el nombre INTERNO del grupo—, así que las ya "
        "emitidas iban incompletas ante la ATO sin que nada lo dijera. + el vencimiento "
        "nacía **HOY**, o sea que toda factura entraba vencida el mismo día. Cuatro columnas "
        "nuevas en `Groups` ⚠️ **al final, que es lo que las hace migrar solas** (v363), y el "
        "PDF **degrada en tres direcciones**: sin ABN, sin razón social y con la lectura "
        "fallando se emite igual. + **CSV para Xero y MYOB** con tres reglas: importes "
        "**siempre sin impuesto** (o la casilla «inclusive/exclusive» se contesta mal y el "
        "GST sale torcido), el impuesto **REPARTIDO** para que sume exacto —ejercitado contra "
        "la hoja real: línea a línea da **9,99** y el reparto **10,00**— y el mapa de cuentas "
        "**por PERFIL** (200 de Xero no existe en MYOB, que rechaza la fila entera). Nombres "
        "de impuesto y campos de MYOB **verificados en su documentación**. ⚠️ Un error mío de "
        "semántica cazado **volcando el CSV**, no leyendo: la 4ª de MYOB es el PO del CLIENTE, "
        "no el proyecto. ⚠️ Y una **rotura SE ESCAPÓ** porque el guardián afirmaba la "
        "CONSTANTE y no lo que el CSV produce: intercambiar el desempaquetado escribe "
        "`OUTPUT` en el fichero con la constante perfecta. ⚠️ + un `NameError` (`_num` sin "
        "importar en `auth_ui`) cazado por el chequeo de ámbito antes de desplegar. 80 "
        "comprobaciones · **15/15 roturas + control** · 21 contra la hoja real sin rastro |\n")

s = io.open(P, encoding="utf-8").read()
ANCLA = "## Versiones desplegadas (v482 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))
s = s.replace(ANCLA, SECCION + "\n## Versiones desplegadas (v483 = actual)")
s = s.replace(CAB, CAB + FILA)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: seccion v483 + fila + cabecera")
