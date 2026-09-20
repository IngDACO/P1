# -*- coding: utf-8 -*-
"""Documenta v490 en CLAUDE.md: parte de horas y ausencias a Xero Payroll AU (fase 2.3-B)."""
import io

P = "C:/Users/diego/P1/CLAUDE.md"

SECCION = """## FASE 2.3-B: el parte de horas y las ausencias pagadas, a Xero Payroll AU (v490)

Decisiones del usuario: **horas Y permisos** (las ausencias pagadas que COPEX ya aprueba
van también), el parte llega en **borrador**, cada usuario se **empareja solo y se confirma**
una vez, y un parte que ya existe se **actualiza solo si sigue en borrador**.
`core/xero_nomina.py` + `xero_ui.render_partes_xero`, dentro de «Timesheet for payroll».

### ⚠️ Lo que la especificación de Xero obligó a cambiar respecto al parte de v484
Leída la especificación OpenAPI oficial de Payroll AU antes de escribir nada:
1. **Las ausencias NO van en el parte.** Una línea de parte solo admite un *EarningsRate*;
   vacaciones y bajas son *LeaveTypes* y se registran como *LeaveApplications*, que creadas
   por la API quedan **programadas** (aprobadas para pagarse). El CSV de v484 las ponía como
   líneas — el diseño «cada fila es una línea de allí» era verdad solo para las horas.
2. **El periodo no es libre**: las fechas del parte tienen que ser EXACTAMENTE un periodo del
   calendario de nómina del empleado, o Xero lo rechaza. El periodo sale de `PayrollCalendars`
   (su `StartDate` es el inicio del PRÓXIMO periodo; los anteriores se cuentan hacia atrás) y
   se valida antes de llamar a nada. Un tipo que no se sabe calcular devuelve [] en vez de
   inventar fechas.
3. **Un empleado de Xero AU no tiene número**, solo nombre y email. El emparejado se guarda en
   `AccountingJSON.xero_empleados` **atado a la ORGANIZACIÓN** (`tenant`): si se reconecta a
   otra, deja de valer solo en vez de pagar a quien no es.

### Las reglas que fallarían en silencio
- **Una definición de «qué se paga»**: las horas salen de `contable.partes`, la misma función
  del CSV (jornada fichada + `ausencias.horas_pagadas_dia`, el criterio de v432).
- La hora ordinaria usa el **`OrdinaryEarningsRateID` de cada empleado**, no un nombre.
- `NumberOfUnits` = **una entrada por día del periodo y en orden**, con 0 donde no hay horas.
- Fechas en `/Date(ms+0000)/` a **medianoche UTC**: con la hora local el día se correría.
- Los permisos llevan las **horas explícitas** (`LeavePeriods`): sin ellas Xero usa la jornada
  tipo del empleado, y COPEX ya recortó lo que se paga en un día con fichaje (v432). Van en
  **tramos de días seguidos**: un permiso de viernes a lunes contaría el fin de semana.
- **Emparejado**: primero por email, luego por nombre, y **solo parejas únicas** (homónimos o
  email repetido: no se propone nada — adivinar paga las horas de otro). Guardar se bloquea si
  dos personas apuntan al mismo empleado. El valor guardado se **antepone** si el empleado ya
  no está activo (`ui.opciones_con_actual`, v487), en vez de pisarlo en silencio.
- **No duplicar**: se buscan los partes del empleado **recorriendo TODAS las páginas** (con
  más de 100 partes, el del periodo puede estar en la segunda); borrador → se actualiza con su
  `TimesheetID`; aprobado o procesado → no se toca y se dice; y **si no se puede comprobar, no
  se crea**. Un permiso que se solapa con uno igual ya en Xero no se reenvía.
- Se manda solo a quien está emparejado, activo y **en ese calendario**; los demás se nombran.

### Tres cosas en `xero.py` que también sirven a las facturas
- **Ritmo**: `_espera_cupo` no deja pasar de 55 llamadas/min por organización. El parte de un
  equipo son ~4 llamadas por persona: con 15 personas Xero respondía 429 a mitad del envío,
  dejando a unos con parte y a otros sin él.
- Un **429 con espera corta** (≤ 20 s) se reintenta una vez; uno largo se devuelve.
- `mensajes_error` lee los errores **dentro de cada objeto** (`Timesheets[i].ValidationErrors`),
  que es donde los pone Payroll AU; sin eso el aviso decía solo «A validation exception occurred».

### Verificación
`verif_v490.py`, **56 comprobaciones**, todo ejecutando con Xero sustituido: fechas (incluido
el ejemplo oficial de la especificación), los seis tipos de calendario, el emparejado, el
parte y los permisos, **el envío en todas sus ramas** (crear, actualizar borrador, no tocar
aprobado, no crear sin comprobar, página 2, otro calendario, sin emparejar, empleado de baja,
permiso ya existente, error de validación, tipo de permiso inexistente), ritmo, 429 y la
pantalla. ⚠️ Una sonda dio un **rojo que no existía**: buscaba «Earnings rate names» como
texto y lo encontraba en el comentario que explica el cambio — pasada a AST. Batería:
**15/15 roturas + CONTROL**, con el verde de base primero.

### ⚠️ El único rojo de la suite era un FALSO POSITIVO del guardián de v433
`verif_v430` (bloque 14) marcaba `xero_nomina._DIAS_TIPO = {"WEEKLY": 7, ...}` como un mapa
de columnas escrito a mano: su criterio era «dict de 3+ textos → enteros», y los días de un
periodo de nómina tienen esa forma sin ser columnas. Se miró el código acusado antes de tocar
nada (regla v385) y el guardián se afinó, no se relajó: un mapa de columnas es uno cuyas
CLAVES son CABECERAS, y el conjunto se **deriva** de todos los `*_HEADERS` del repo más los
nombres viejos y nuevos de `columnas.LEGADO`. Validado en las dos direcciones: caza el `_COL`
de v433 construido **y** una rotura real metida en el árbol, y no marca los días de nómina.
Suite: **126 verde** + ese rojo corregido y re-verificado.
"""

FILA = ("| v490 | **FASE 2.3-B: parte de horas y ausencias pagadas a Xero Payroll AU** (decisiones del "
        "usuario: horas y permisos, borrador, emparejado automático + confirmar, actualizar solo "
        "borradores). ⚠️ Leer la especificación cambió el diseño de v484 en tres puntos: las "
        "ausencias **no van en el parte** (son LeaveApplications), el periodo **tiene que ser uno "
        "del calendario** de Xero o lo rechaza, y el empleado no tiene número (emparejado atado a "
        "la organización). Una definición de lo que se paga (`contable.partes`), tipo ordinario de "
        "CADA empleado, una entrada por día en orden, permisos con las horas explícitas y en tramos "
        "seguidos, y sin duplicar (todas las páginas; si no se puede comprobar, no se crea). + ritmo "
        "de 55 llamadas/min y reintento corto ante 429, que también sirven a las facturas. 56 "
        "comprobaciones · **15/15 roturas + control** |\n")

s = io.open(P, encoding="utf-8").read()
ANCLA = "## Versiones desplegadas (v489 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))
s = s.replace(ANCLA, SECCION + "\n## Versiones desplegadas (v490 = actual)")
s = s.replace(CAB, CAB + FILA)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: seccion v490 + fila + cabecera")
