# -*- coding: utf-8 -*-
"""Documenta v501 en CLAUDE.md: la línea base del cronograma."""
import io

P = "C:/Users/diego/P1/CLAUDE.md"

SECCION = """## LA LÍNEA BASE: el plan que se ACORDÓ, congelado (v501)

Tercero de los cuatro huecos que la auditoría de gestión de instalación dejó medidos, y
el que el usuario eligió seguir («la idea es cerrar esta brecha competitiva»).

Hasta aquí el cronograma se **recalculaba siempre** desde las duraciones vigentes, así que
alargar una actividad de 4 a 8 días **no dejaba rastro**: el plan nuevo pasaba a ser «el
plan», la curva S comparaba contra un blanco móvil y la obra seguía pareciendo que iba
bien. Eso es justo lo que hace falta para defender por qué se retrasó una entrega.

Ahora la app distingue **tres fechas** que antes eran una sola:
| | |
|---|---|
| **línea base** | lo que se ACORDÓ (v501) |
| **plan vigente** | lo que dicen hoy las duraciones y dependencias (v499) |
| **pronóstico** | cuándo va a terminar de verdad (v500) |

### Decisiones del usuario
- **Se fija con un BOTÓN**, cuando el plan está pactado — no al crear la obra, que nace de
  una plantilla y casi siempre se ajusta después: congelar eso sería congelar un plan que
  nadie llegó a acordar.
- **La ORIGINAL nunca se pierde**: se puede re-fijar cuando el cliente aprueba un plan
  nuevo, y la app conserva la original, cuenta **cuántas veces se replanificó** y guarda
  cuánto movió la entrega cada vez.

### Dónde vive, y por qué así
Columna `BaselineJSON` en `Proyectos` (⚠️ **al final**, v363, y opcional: una obra sin
línea base se comporta exactamente como hasta v500). Es un **snapshot**, no columnas por
actividad: si alguien reordena o borra una actividad, la foto conserva lo que se acordó
—que es el punto— en vez de desincronizarse fila a fila. El historial guarda solo el
resumen de cada replanificación (fecha, quién, cuánto movió), no el plan entero: así no
crece sin control dentro de una celda.

### ⚠️ Las tres cosas que fallarían en silencio
1. **Re-fijar no puede reescribir el pasado.** La ORIGINAL solo se escribe la primera vez;
   lo que cambia es la vigente. Sin eso, la línea base no sirve para discutir nada.
2. **Un fallo de LECTURA no puede borrarla.** `fijar_baseline` lee el JSON actual
   **FRESCO** (aquí se decide qué se escribe, y fusionar sobre algo de hace 120 s perdería
   la replanificación que otra sesión acaba de registrar) y ⚠️ **si no puede leer, NO
   escribe**: tratar el fallo como «no había línea base» borraría la original, que es
   exactamente lo que esta versión existe para proteger (el criterio de v492).
3. **La comparación casa por ORDEN, no por posición.** Dos listas comparadas por posición
   dan basura en cuanto alguien reordena o borra una actividad; las que no estaban se
   marcan «nueva» y las que ya no están, «eliminada».

### Qué se ve
En 📊 Estado, junto a los KPIs: **entrega acordada**, **cuánto se ha movido respecto a
ella** y **cuántas veces se replanificó**, más dos desplegables — qué actividades
cambiaron (con sus días antes/ahora y cuánto se desplazó cada una) y el historial de
replanificaciones. El botón vive en ✏️ Datos, junto a la tabla de actividades, que es
donde se acuerda el plan. ⚠️ **El campo no fija líneas base** ni ve esa pantalla.

### Ejercitado contra la HOJA REAL (método v344)
La columna se creó sola (33 → 34). Fijada la línea base con entrega **25/09**, se alargó
la actividad 2 de 5 a 9 días: la app pasó a decir **25/09 → 29/09 (+4 d)** e identificó
que la 2 cambió de duración y que **la 3, la 4 y la 5 se movieron +4 d sin cambiar ellas**
— el rastro que antes no existía. Al re-fijar, la original siguió intacta, el historial
registró «+4 d» y la comparación siguió midiendo contra lo acordado. Producción devuelta a
su estado (`BaselineJSON` vacío y las duraciones originales).

### Verificación
`verif_v501.py`, **24 comprobaciones**, todo EJECUTANDO. Batería: **11 roturas, 11 cazadas
+ CONTROL verde**, con el verde de base confirmado antes (v459).
⚠️ **Dos escaparon en la primera pasada, y las dos por culpa del guardián** —casos que no
podían distinguir la rotura—:
- el de «casa por posición» usaba órdenes **1, 2, 3**, donde posición y orden coinciden:
  las dos formas dan lo mismo y el chequeo aprobaba con el fallo dentro. Ahora usa una obra
  con órdenes **1, 5 y 9**;
- el de «obra sin cronograma» comprobaba solo que devolviera `False`… y con la guarda rota
  **también** devuelve `False`, pero por otro motivo (ese pid no existe en la hoja). Ahora
  se comprueba el MOTIVO, no el booleano.
Es la lección de v472 otra vez: **una comprobación que puede pasar por otro camino no
comprueba lo que dice**.
"""

FILA = ("| v501 | **Línea base: el plan que se ACORDÓ, congelado.** Hasta aquí el cronograma se "
        "recalculaba siempre, así que alargar una actividad de 4 a 8 días **no dejaba rastro** —el "
        "plan nuevo pasaba a ser «el plan» y la curva S comparaba contra un blanco móvil—, que es "
        "justo lo que hace falta para defender por qué se retrasó una entrega. Se fija **con un "
        "botón** cuando el plan está pactado (decisión del usuario) y ⚠️ **la ORIGINAL nunca se "
        "pierde**: re-fijar conserva la acordada, cuenta las replanificaciones y guarda cuánto movió "
        "la entrega cada vez. ⚠️ Si no se puede LEER, **no se escribe** (tratar el fallo como «no "
        "había» borraría la original, criterio v492), y la comparación casa por **ORDEN**, no por "
        "posición. Ejercitado contra la hoja real: alargar una actividad pasó a decir **25/09 → 29/09 "
        "(+4 d)** identificando que la 2 cambió y que **la 3, 4 y 5 se movieron sin cambiar ellas**. "
        "24 comprobaciones · **11/11 roturas + control** ⚠️ (2 escaparon primero por casos míos que "
        "no podían distinguir la rotura: órdenes 1-2-3 donde posición y orden coinciden, y un `False` "
        "que llegaba por otro motivo) |\n")

s = io.open(P, encoding="utf-8").read()
ANCLA = "## Versiones desplegadas (v500 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))
s = s.replace(ANCLA, SECCION + "\n## Versiones desplegadas (v501 = actual)")
s = s.replace(CAB, CAB + FILA)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: seccion v501 + fila + cabecera")
