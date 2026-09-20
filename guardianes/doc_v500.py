# -*- coding: utf-8 -*-
"""Documenta v500 en CLAUDE.md: el fin previsto sale de la cadena, no del ritmo."""
import io

P = "C:/Users/diego/P1/CLAUDE.md"

SECCION = """## EL FIN PREVISTO SALE DE LA CADENA, NO DEL RITMO (v500)

Segunda mitad de lo que el usuario pidió en v499 («recalcular el fin previsto desde la
cadena»), elegida por él tras una auditoría de los cuatro huecos que quedaban en gestión
de instalación. v499 puso el encadenado; aquí es donde sirve para algo.

Hasta ahora el fin previsto era **una regla de tres sobre el % de avance**
(`fecha = inicio + total/SPI`), así que repartía el retraso entre todas las actividades
por igual. Medido antes de tocar nada (v360), con casos construidos porque la demo tiene
UNA obra y medir solo esa habría sido un paso en vacío:

| Situación | El SPI decía | La CADENA dice |
|---|---|---|
| **50% de avance, pero la actividad que bloquea a las demás sin empezar** | **+0 d, «en plazo»** | **+10 d** |
| todo al 25%, nada terminado | +20 d | +5 d |
| día 15 de 20, solo la primera terminada | +40 d | +10 d |
| **la obra REAL (`PRJ-0001`)** | **«—»: no podía calcularlo** | **04/10, +9 d, y qué actividades mandan** |

O sea que el SPI o **no decía nada** (con avance 0 es una división por cero, justo cuando
más importa saber que la obra no arranca), o **exageraba**, o —lo peor— **tranquilizaba
cuando no debía**.

### `plan.pronostico(acts, hoy)`: las tres reglas, que es donde está el dominio
`calcular` responde «cuándo debería»; `pronostico` responde «cuándo va a ser».
- **terminada** → su fecha es la REAL: ya no se mueve ni la mueve nadie;
- **en curso** → le queda `duración × (1 − avance)`, y eso corre **desde HOY**;
- **sin empezar** → arranca cuando sus predecesoras la dejen, ⚠️ **nunca antes de HOY**:
  lo que tocaba el martes y no se hizo no se puede hacer el martes.

Por eso el retraso **se propaga por la cadena** en vez de diluirse en un promedio — y por
eso la obra también puede **adelantarse** si una actividad termina antes (probado: la
cadena entera se recoge). Además dice **qué actividades mandan** en esa fecha, que es lo
accionable: son las que hay que empujar para recuperar.

### ⚠️ UNA sola respuesta a «cuándo termina»
`fecha_proj`/`proj_dias` (las del SPI) **se eliminan**, no se dejan al lado: dos
definiciones del mismo número es exactamente lo que hizo que Rentabilidad y el detalle
dieran dos ingresos distintos para la misma obra (v361) — mientras coinciden nadie lo
nota, y el día que discrepan ya está en pantalla. El **SPI se conserva** porque responde
otra pregunta (a qué ritmo se avanza), pero ya no produce una fecha.
Y `_preparar` se extrae para que el plan y el pronóstico resuelvan las dependencias
**igual**: si cada uno lo hiciera por su cuenta podrían discrepar sobre quién va detrás de
quién, y eso no da ningún error — solo dos fechas que no cuadran (v323).

### ⚠️ El consumidor que se me escapó, y que el guardián cazó
Barrí los consumidores de `fecha_proj` **excluyendo `core/schedule.py`**, dando por hecho
que ahí solo estaba la definición. No: **`schedule_svg` dibuja con ella la proyección del
Gantt**, así que al retirar la clave la línea de proyección habría **desaparecido del
gráfico sin dar ningún error**. Lo destapó el barrido del guardián —que sí mira el módulo
entero—, no leer el código. El chequeo quedó: la proyección se dibuja, y con la fecha de
la cadena.

### ⚠️ Y TRES roturas se escaparon la primera vez: por culpa del GUARDIÁN
- **Dos ESCAPARON** porque comprobaba *presencia* de `dias_cadena` en la función… y la
  encontraba **en el docstring que yo mismo había escrito ahí**, con el código leyendo ya
  la clave vieja. Es la trampa nº2 (*grep ≠ uso*) dentro del guardián, la misma de v461 y
  v472. Ahora mira el **cuerpo SIN docstring** y afirma en las **dos direcciones**: que
  lea la clave nueva **y** que no quede leyendo la del ritmo.
- **Una REVENTABA**, y un guardián roto «caza» todo sin probar nada (v463); con el chequeo
  estructural falla limpio.
Con eso: **10 de 10 roturas cazadas + CONTROL verde**, y el verde de base confirmado
ANTES (v459).

### ⚠️ Un chequeo mío que acusó a un código sano
El de «el Gantt sigue dibujando la proyección» daba FALLO con el código correcto: la
proyección solo se dibuja **si hay curva real**, y yo no se la pasaba — el test fallando
por su propia construcción (v363/v372). Se construye con `real_scurve`, la función de
verdad, en vez de inventarse la forma del dato (v135).

### Verificación
`verif_v500.py`, **30 comprobaciones**, todo EJECUTANDO: las tres reglas y sus casos
límite (adelanto, obra terminada que no se mueve aunque hoy sea muy posterior, actividad
en paralelo que manda, desfase, obra sin actividades), que no queda ninguna lectura de la
fecha del SPI en TODO el repo, que los **cuatro** consumidores —cartera, agrupaciones,
radar y detalle— leen la misma, que el Gantt la dibuja, que el **plan de v499 no se movió**
con el refactor, y la mejora medida sobre la obra REAL.
"""

FILA = ("| v500 | **El fin previsto sale de la CADENA, no del ritmo** (2.ª mitad de lo que el usuario "
        "pidió en v499). El SPI era una regla de tres sobre el % de avance: medido, una obra con el "
        "**50% hecho y la actividad que bloquea a las demás sin empezar** salía **«+0 d, en plazo»** "
        "y la cadena dice **+10 d**; y con avance 0 el SPI **no daba NINGUNA fecha** (división por "
        "cero) mientras la cadena da una y dice **qué actividades mandan**. La obra real pasó de «—» "
        "a **04/10 (+9 d)**. Tres reglas: lo terminado no se mueve · lo en curso cuenta su resto "
        "**desde hoy** · lo que no empezó **no puede arrancar en el pasado** — así el retraso se "
        "PROPAGA (y la obra también puede adelantarse). ⚠️ `fecha_proj`/`proj_dias` **se eliminan**: "
        "dos respuestas a «cuándo termina» es el fallo de v361; el SPI se conserva como ritmo. ⚠️ El "
        "guardián cazó un consumidor que se me escapó (**el Gantt**, que habría dejado de dibujar la "
        "proyección en silencio) y ⚠️ **3 roturas escaparon por culpa del guardián**: comprobaba "
        "presencia de la clave y la encontraba **en su propio docstring**. 30 comprobaciones · "
        "**10/10 roturas + control** |\n")

s = io.open(P, encoding="utf-8").read()
ANCLA = "## Versiones desplegadas (v499 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))
s = s.replace(ANCLA, SECCION + "\n## Versiones desplegadas (v500 = actual)")
s = s.replace(CAB, CAB + FILA)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: seccion v500 + fila + cabecera")
