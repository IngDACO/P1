# -*- coding: utf-8 -*-
"""Documenta v495 en CLAUDE.md: los cobros vienen de Xero (fase 2.3-C)."""
import io

P = "C:/Users/diego/P1/CLAUDE.md"

SECCION = """## FASE 2.3-C: lo cobrado en Xero entra en COPEX (v495)

Decisiones del usuario: **el cobro lo registra el contable EN XERO**, se trae con un
**botón**, las facturas **siguen saliendo en borrador** (y se avisa de las que por eso no
pueden recibir un pago), y si el importe no cuadra **manda Xero** y se avisa.
`xero.traer_cobros` + `invoices.sincronizar_cobros` + el botón en Finanzas → Accounting.

### El problema que cierra
Las facturas salían a Xero desde v488, pero el **cobro** no viajaba: si el contable
conciliaba el banco en Xero, COPEX seguía diciendo que la factura estaba por cobrar. Dos
pantallas del mismo dinero diciendo cosas distintas, y la que se usa para perseguir a un
cliente es la de COPEX.

### ⚠️ Lo que la especificación decidió del diseño
Leída antes de escribir nada (`Invoice` de la Accounting API):
1. **`AmountPaid` es la cifra**, no `GET /Payments`: el resumen de la lista de facturas ya
   la trae, así que un lote de 40 IDs cuesta UNA llamada, y es lo que Xero mantiene al
   conciliar. (`Payments` solo viene al pedir una factura suelta.)
2. **`AmountCredited` NO se suma.** Son notas de crédito, anticipos y sobrepagos: reducen
   lo que se debe, pero **no son dinero recibido**. Sumarlo diría «cobrado» de algo que
   nadie pagó, así que se AVISA aparte.
3. **Los estados son seis** (`DRAFT · SUBMITTED · DELETED · AUTHORISED · PAID · VOIDED`),
   y ahí está el fallo que habría sido silencioso: **una factura en borrador tiene
   `AmountPaid = 0`**, así que sincronizar desde ella **pondría a cero un cobro real
   apuntado en COPEX**. Solo se lee de `AUTHORISED` y `PAID`; del borrador se avisa
   («así no va a llegar ningún cobro: tu contable las aprueba en Xero») y de una
   `VOIDED`/`DELETED` no se toca nada aquí.

### Las otras reglas que fallarían en silencio
- **Idempotente**: se FIJA el valor, no se suma, así que pulsar el botón dos veces no
  cobra dos veces; y si no cambia nada, no se apunta línea en el historial ni se escribe.
- El historial guarda el **movimiento** con su **origen** (`xero`), y puede ser
  **negativo** si en Xero se deshizo un pago: así se distingue de lo apuntado a mano.
- ⚠️ **Un fallo de red no acusa a nadie**: si la llamada falla, las facturas NO se marcan
  como «no encontradas en Xero» (que se lee como «las borraron allí») y no se escribe nada.
- **Una lectura fresca y UNA escritura** para todo el lote (`_find_row` por factura serían
  N lecturas contra el techo de 60/min, v339), y la columna se busca por su NOMBRE.
- **Una sola definición del parser de fechas de Xero**: `de_ms` vivía en `xero_nomina`
  (v490) y ahora la necesita también el cobrado, así que sube a `xero.de_fecha` y la de
  nómina DELEGA. Dos parsers de la misma fecha es como empiezan las divergencias de v323.

### Verificación
`verif_v495.py`, **33 comprobaciones**, todo ejecutando con Xero y la hoja sustituidos:
el caso normal, la segunda pasada, borrador y enviada-para-aprobar, anulada en Xero, nota
de crédito, el descuadre en contra (Xero manda y el historial guarda el negativo), lo que
NO se consulta, el fallo de red, el troceado en 2 llamadas para 45 facturas, las guardas de
`sincronizar_cobros` y la pantalla EJECUTADA con sus siete casos. Batería: **11/11 roturas
+ CONTROL**, con el motivo de cada una a la vista.
⚠️ **Tres roturas se escaparon en la primera tanda**, y solo una era un agujero del código:
(1) quitar el `continue` del borrador lo frenaba la guarda siguiente —el código tiene doble
defensa, así que **la rotura no era un fallo** y se reescribió al fallo REAL (que el
borrador cuente como cobrable); (2) mi hoja falsa **excluía las anuladas**, o sea que hacía
el trabajo que el código debe hacer y su guarda quedaba sin probar (v309/v310: un mock que
hace lo que auditas garantiza un OK falso); y (3) la delegación del parser se comprobaba
buscando «de_fecha» **como texto**, y eso aparece en el comentario de la función — pasada a
la LLAMADA por AST (trampa nº2, otra vez dentro de un guardián).
"""

FILA = ("| v495 | **FASE 2.3-C: lo cobrado en Xero entra en COPEX** (decisiones del usuario: lo "
        "registra el contable en Xero, con botón, facturas en borrador avisando, y si no cuadra "
        "manda Xero). ⚠️ La especificación decidió tres cosas: el cobrado es `AmountPaid` (una "
        "llamada por lote de 40), **`AmountCredited` NO se suma** (nota de crédito no es dinero "
        "recibido) y **una factura en borrador tiene AmountPaid 0**, así que sincronizar desde ella "
        "pondría a CERO un cobro real — solo se lee de aprobada/pagada. Idempotente (fija, no suma), "
        "historial con origen y movimiento negativo, un fallo de red no acusa de borradas, 1 lectura "
        "+ 1 escritura por lote, y el parser de fechas de Xero pasa a tener UNA definición. 33 "
        "comprobaciones · **11/11 roturas + control** ⚠️ tres se escaparon primero: una rotura que "
        "no era fallo, un mock que hacía el trabajo del código, y un chequeo que casaba con un "
        "comentario |\n")

s = io.open(P, encoding="utf-8").read()
ANCLA = "## Versiones desplegadas (v494 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))
s = s.replace(ANCLA, SECCION + "\n## Versiones desplegadas (v495 = actual)")
s = s.replace(CAB, CAB + FILA)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: seccion v495 + fila + cabecera")
