# -*- coding: utf-8 -*-
"""Documenta v507 — cobro de obra: variaciones y reclamaciones de avance."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"

SECCION = """## COBRO DE OBRA: variaciones y reclamaciones de avance (v507)

Cierra la **brecha 2** del estudio de mercado del 20/09/2026. Hasta aquí se podía
facturar, pero no **reclamar**: sin variaciones, sin *progress claims* y sin retenciones,
la reclamación mensual se seguía armando en Excel — que es justo donde el contratista
pelea su dinero, y donde FIELDBOSS ya estaba con *change orders*, *retainage* y AIA
billing.

### La aritmética, que es la de siempre en obra
```
valor          = contrato + variaciones APROBADAS
trabajo_hecho  = valor × avance%                     (acumulado, desde el principio)
bruto          = trabajo_hecho − lo reclamado antes   (lo nuevo de este periodo)
retención      = bruto × retención%                   (5% por defecto, editable)
neto           = bruto − retención
```

### Decisión del usuario: el contrato sale de la cotización ACEPTADA
Ya está enlazada a la obra (`aceptar_y_crear_proyecto`) y es el precio que el cliente
firmó: una sola fuente de verdad, sin un dato nuevo que pueda contradecirla. Una obra sin
cotización aceptada no puede emitir reclamaciones, **y se dice en pantalla antes de
enseñar ninguna cifra**.

⚠️ Se usa el **Subtotal**, no el Total: es la misma base que `finance.project_revenue` e
`invoices.facturado_por_proyecto`, que suman importes de línea. Mezclar bases con y sin
impuesto haría que los totales comparasen peras con manzanas (la nota de v370).

### ⚠️ Las cuatro cosas que fallarían en silencio
1. **Una reclamación CONGELA sus números.** Contrato, variaciones, avance y retención se
   guardan al emitir. Si mañana se aprueba otra variación, la reclamación que ya mandaste
   sigue diciendo lo mismo. Mismo principio que las líneas de cotización (v353), la
   nómina y la línea base (v501).
2. **Si el avance BAJA, el bruto es cero, no una devolución.** Devolver dinero ya cobrado
   es una nota de crédito: otro documento, otras consecuencias. No se hace en silencio.
3. **Lo acumulado se lleva en `WorkDone`, no sumando netos.** La retención se descuenta
   del PAGO, no del trabajo hecho; sumando netos la obra no llegaría nunca al 100%.
4. **Una variación PROPUESTA no es dinero.** Solo la aprobada mueve el contrato — y una
   reducción de alcance (importe negativo) lo resta, porque en obra existe.

Además: una variación ya decidida no se re-decide (movería el valor por debajo de
reclamaciones ya emitidas con él), y solo se puede anular la **última** reclamación (las
siguientes se emitieron restando el acumulado de ésta).

### ⚠️ El fallo de fondo: dos hojas fuera del lote de lectura
`hojas.registros(SHEET)` **sin cabeceras devuelve `None`** cuando esa hoja no está en
`HOJAS_LECTURA`. `Variations` y `Claims` no estaban: las filas se escribían en el libro y
la app **leía VACÍO PARA SIEMPRE, sin un solo error**.

⚠️ Y el código ya lo advertía. La nota de v461 sobre `TimeCorrections` dice exactamente
esto, palabra por palabra. Se leyó **después** de que mordiera.

**Un comentario no es una red.** Nueva: `check_hojas_en_lote.py` — ninguna hoja leída por
lote puede estar fuera del lote. Validada en tres direcciones: caso malo, caso bueno, y la
lectura CON cabeceras, que cae a `get_sheet` y es otro camino que no debe denunciarse.

⚠️ La suite no podía ver esto: solo aparece leyendo el libro de verdad. Lo cazó el
ejercicio contra la hoja real.

### ⚠️ Y dos chequeos míos que no comprobaban lo que decían
- **La batería** destapó uno que buscaba la palabra `_ultima` **en el fuente** para
  comprobar que solo se anula la última. La rotura quitó el `if` y dejó la asignación:
  pasó tan campante (grep ≠ uso, trampa nº2). Ahora se EJECUTA `anular` y se exige que
  rechace, y que acepte el caso bueno.
- **En el ejercicio**, «una variación propuesta no mueve el contrato» pasaba igual cuando
  la variación **no se había leído** — que es justo lo que ocultaba el bug de arriba. Un
  chequeo que aprueba por ausencia de datos no comprueba nada (trampa nº1). Ahora se
  comprueba primero que se lea de vuelta.

### Verificación
`verif_v507.py`, **25 comprobaciones**, ejecutando la aritmética de verdad. Batería:
**12 roturas, 12 cazadas + CONTROL**. Suite completa: **140 verde · 0 rojo · 0 roto**.

**Ejercitado contra la HOJA REAL** (método v344), el ciclo entero: se le creó a la obra
una cotización de prueba para darle contrato (se borra al final) → variación propuesta,
leída de vuelta, que **no** mueve el contrato → aprobada, que **sí** lo mueve → claim al
30% (**neto 29.925** sobre 105.000 con 5% de retención) → claim al 50% que reclama **solo
la diferencia** → anular la primera se rechaza, la última no → anulada, deja de contar.
Las dos hojas se crean solas; la obra queda sin variaciones ni reclamaciones y el contrato
vuelve a su estado de partida.
"""

FILA = ("| v507 | **Cobro de obra: variaciones y reclamaciones de avance.** Cierra la brecha 2 del "
        "estudio: hasta aquí se podía facturar pero no **reclamar**. `valor = contrato + variaciones "
        "aprobadas`, `bruto = valor × avance − lo ya reclamado`, `neto = bruto − retención`. El "
        "contrato sale del **Subtotal** de la cotización aceptada (decisión del usuario; misma base "
        "que `finance` e `invoices`). ⚠️ Una reclamación **congela** sus números; ⚠️ si el avance "
        "BAJA el bruto es **cero**, no una devolución; ⚠️ lo acumulado va en `WorkDone`, no sumando "
        "netos; ⚠️ una variación **propuesta no es dinero**. ⚠️ **El fallo de fondo**: `Variations` y "
        "`Claims` estaban fuera de `HOJAS_LECTURA`, así que `registros()` devolvía None y la app "
        "leía **VACÍO PARA SIEMPRE sin un solo error** — el código ya lo advertía en la nota de "
        "v461 y se leyó después de que mordiera. Red nueva `check_hojas_en_lote`. Lo cazó el "
        "ejercicio contra la hoja, no la suite. 25 comprobaciones · **12/12 roturas + control** · "
        "suite 140 verde |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v506 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v506 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


h = io.open(HIST, encoding="utf-8").read()
unica(h, A_HIST, "cabecera", "HISTORIAL.md")
unica(h, CAB, "tabla", "HISTORIAL.md")
unica(h, TRAS_CAB, "separador", "HISTORIAL.md")
h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v507 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v507 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v507 = actual)")
c = c.replace(CAB, CAB + FILA)

lineas = c.splitlines(True)
idx = [i for i, l in enumerate(lineas) if l.startswith("| v")]
if len(idx) != 16:
    raise SystemExit("esperaba 16 filas tras insertar: %d" % len(idx))
vieja = lineas[idx[-1]][:10]
del lineas[idx[-1]]
c = "".join(lineas)

m = re.search(r"_\(y (\d+) versiones anteriores", c)
if not m:
    raise SystemExit("no encuentro la nota de cierre")
c = c.replace(m.group(0), "_(y %d versiones anteriores" % (int(m.group(1)) + 1))
escribir(CLAUDE, c)
print("CLAUDE.md: fila v507 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
