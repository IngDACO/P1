# -*- coding: utf-8 -*-
"""Documenta v491 en CLAUDE.md: la prueba de 2.3-B en producción contra la Demo Company."""
import io

P = "C:/Users/diego/P1/CLAUDE.md"

SECCION = """## El parte de horas a Xero Payroll, probado EN PRODUCCIÓN contra la Demo Company (v491)

Solo documentación: v490 verificada de punta a punta el 16/09/2026, con el usuario
confirmando antes de mandar nada y verificando él mismo el lado de Xero.

### Lo que se vio en producción
- El bloque «Send to Xero Payroll» **lee en vivo** la Demo Company: 6 empleados (con su
  email) y los calendarios de nómina, con el periodo quincenal **15–28 sep 2026** propuesto.
- Datos de prueba en `cliente1`: una jornada de 8 h de «helper 2» el martes 15/09 y unas
  vacaciones aprobadas el jueves 17/09 (`AUS-0001`). Emparejado a mano con **Oliver Gray**.
- La vista previa dijo `8.00 h · Annual Leave 8 h · will be sent` — ⚠️ y ese «will be sent»
  **comprueba el calendario del empleado** (`PayrollCalendarID`), así que ya decía que
  Oliver Gray está en el quincenal antes de enviar.
- **1.er envío**: «1 timesheet(s) created, 0 updated, 1 leave application(s) created».
- ⚠️ **2.º envío, lo mismo otra vez**: «0 created, **1 updated**, 0 leave» + «Annual Leave
  17/09–17/09 was already in Xero». Las dos protecciones contra duplicados —actualizar el
  borrador y no repetir el permiso— solo podían probarse contra un Xero real.
- **El usuario lo verificó en Xero**: un solo parte en borrador, las 8 h en el día correcto
  y el permiso de 8 h.

### ⚠️ La guarda de la limpieza saltó, y con razón
`Groups.AccountingJSON` de `cliente1` estaba **vacío** antes de la prueba y después traía
la configuración contable ENTERA: `guardar_emparejado` escribe `contable.mapa()` —los valores
de fábrica fusionados— más el emparejado. Antes de devolverlo a vacío se comprobó que todo lo
demás era **exactamente** lo de fábrica (si hubiera algo configurado por alguien, borrarlo lo
perdería). ⚠️ Consecuencia anotada, no corregida: guardar el emparejado **congela** los valores
de fábrica en ese grupo, así que un cambio futuro de un valor por defecto en el código no le
llegaría. Es el mismo comportamiento que ya tenía el editor del plan de cuentas (v483).

### Limpieza
Con doble guarda (usuario + horas exactas; ID + marca «ZZ PRUEBA») y foto antes/después en
SOLO LECTURA: la jornada, `AUS-0001` y el emparejado fuera — **las 9 comprobaciones idénticas**.
`Auditoria` no se toca. El parte y el permiso de Xero los borra el usuario (la Demo se reinicia).

### ⚠️ Una trampa de método, otra vez
Un clic sobre un `ref` viejo (`ref_292`) cayó en otro sitio tras un rerun. No cambió nada —se
comprobó leyendo el valor de TODOS los desplegables antes de seguir—, pero es la regla de
v431: tras un rerun los `ref` y las coordenadas caducan; se vuelven a buscar.
"""

FILA = ("| v491 | Documentación: **el parte de horas a Xero Payroll probado EN PRODUCCIÓN** contra la "
        "Demo Company. Lectura en vivo de empleados y calendarios; 1.er envío crea parte en borrador "
        "+ permiso; ⚠️ **reenviar lo mismo ACTUALIZA el borrador y no repite el permiso** (solo "
        "probable contra un Xero real). El usuario lo verificó en Xero. ⚠️ La guarda de la limpieza "
        "destapó que guardar el emparejado **congela los valores de fábrica** en `AccountingJSON` "
        "(comprobado idéntico a fábrica antes de vaciarlo; anotado). Foto antes/después idéntica |\n")

s = io.open(P, encoding="utf-8").read()
ANCLA = "## Versiones desplegadas (v490 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))
s = s.replace(ANCLA, SECCION + "\n## Versiones desplegadas (v491 = actual)")
s = s.replace(CAB, CAB + FILA)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: seccion v491 + fila + cabecera")
