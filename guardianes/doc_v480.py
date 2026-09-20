# -*- coding: utf-8 -*-
"""Documenta v480 en CLAUDE.md."""
import io

P = "C:\\Users\\diego\\P1\\CLAUDE.md"

SECCION = """## El recorrido diario del campo, medido en un móvil (v480)

Cuatro ajustes, y **ninguno salió de leer el código**: salieron de recorrer la app con
sesión de campo a 375×812. Para poder medir hubo que crear una obra de prueba y
asignársela a `campo000` — sin datos, la pantalla del campo era un cartel de vacío y
**la densidad real no se podía juzgar**, que es justo lo que v478 dejó como pendiente.

### 1 · Fichaje: la acción antes del resumen
Las cuatro tarjetas ocupaban **230 px —el 28% del teléfono— enseñando «0.00 h»** de un
día que no ha empezado, y empujaban «Workday» a **y=618** y «Project» a **y=759** con la
pantalla en 812: la acción de **cada mañana**, bajo el pliegue.
⚠️ Esto **matiza con medida lo que dejó escrito v308 en ese mismo sitio** —*«en móvil
Streamlit apila las columnas solo, así que no se pierde nada»*—: horizontalmente no se
pierde nada; **verticalmente se pierde la pantalla entera**.
No se quita ni una cifra (v408: priorizar, no encoger): el resumen baja a donde están
las otras cifras del día —barras por proyecto e historial—, y de paso quedan juntas.

### 2 · Una sola obra: se abre sola al consultar, botón explícito al actuar
Con **una** obra asignada, elegir en un desplegable es un toque para una lista de uno, y
hasta elegir no se ve nada. Pero **no es el mismo caso en las tres pantallas**, y esa
distinción ya estaba escrita en el repo:
- **Mis proyectos** y **Pre-Start** (se CONSULTA): se abre sola. ⚠️ No es «el primero de
  la lista» que evitó v139: `list_projects_for_field` devuelve **solo las suyas**, así
  que una significa que no hay nada que elegir — la señal fuerte, mostrada y cambiable,
  de v138. En Pre-Start se limita **al campo**: a admin y propietario esa lista les da
  las del GRUPO, donde «una» significaría otra cosa.
- **Fichar** (se ACTÚA): **no se preselecciona**. v138 pide aquí una acción que diga a
  qué obra se fichará, así que se usa el mismo patrón del atajo del roster — un botón
  con el nombre de la obra. Solo si es **suya** (`propios`) y si el roster no puso ya
  ese botón.
⚠️ Y una trampa que casi me como: `_hechos` se creaba **dentro** del `try` del roster.
Con el roster sin configurar no existiría y el bloque nuevo daría `NameError` — el fallo
latente de v370/v423. Ahora se crea fuera.

### 3 · El contexto, después de la tarea
El plan de la semana y la ruta, **plegados**, ocupaban ~95 px arriba y empujaban la tabla
de «update your progress» a **y=676 de 812**: la única tarea de esa pantalla, bajo el
pliegue. Se bajan detrás del trabajo —la ruta se mira al salir, no mientras se reporta
avance— y la línea «Hoy:» se queda arriba, que eso sí es lo primero de la mañana.
⚠️ La función tiene **dos salidas tempranas** (sin obras asignadas, sin obra elegida).
Moverlos al final sin más los habría hecho **desaparecer justo para quien todavía no
tiene obra** — el único caso en que el plan y la ruta son lo único que esa pantalla puede
ofrecer. Van recogidos en `_contexto()` y se llama en las tres salidas.

### 4 · La barra deja de tener 197 px vacíos
El buscador es solo del admin (v330), así que para el campo la columna del medio no decía
**nada**: 197 de los 375 px de la fila. Encogerla solo la habría hecho más pequeña; se
**llena** con su estado de fichaje, y **activo**: un toque lleva a Fichaje desde cualquier
pantalla.
⚠️ **Cero lecturas nuevas**: `open_sessions` sale de `_cached_records` (caché de 120 s),
el mismo dato que ya pinta Fichaje — y la barra se dibuja en TODAS las pantallas, con el
techo de 60 lecturas/min de una sola cuenta de servicio.
⚠️ Los tres textos son los **mismos** de la banda de estado (v323: una sola forma de decir
cada cosa) y **caben medidos**: 71, 150 y 83 px con la fuente real de la app contra 173
disponibles. Un botón que no cupiera partiría la fila en dos y desharía v479.

### Lo que se descartó mirando el código, no suponiendo
Un recorrido sintáctico decía que el campo llegaba a `_editor_ganancia_hora`
(**Costo/h · Ganancia/h · Precio/h**). **Es falso**: cuelga de `_ganancia_section`, y el
campo entra en `render_expenses` con `can_delete=False`. Mirar el código deshizo la
alarma (trampa nº2: grep ≠ uso).
⚠️ Lo que sí es cierto y **queda como pregunta abierta al usuario, sin tocar**: las
tarjetas de **Costo total · Compras · Mano de obra · Presupuesto · Costo al terminar** y
el «llevas gastado X de Y» **no tienen guarda de rol**, así que el campo las ve en
Recibos. El margen sí está protegido; el costo no. Es una decisión de negocio.

### Verificación
`verif_v480.py`, **25 comprobaciones**. Las que valen: el chip **EJECUTADO** en sus tres
estados con `st.button` interceptado (importar no ejecuta, v378); **cada salida temprana
comprobada una por una** con la sonda validada contra un caso construido (trampa nº12);
que no se perdió ninguna tarjeta; que **no hay preselección silenciosa** al fichar; y que
los textos del chip son los mismos de la banda, atados a ella y no a una lista escrita a
mano que se quedaría vieja (v433/v434).
⚠️ Y un fallo **de la sonda, no del código**: `ast.walk` devolvía el `if prj:` de fuera
porque el texto del hijo está dentro del padre, y el guardián acusaba a un código
correcto. Se ató al `test`.
"""

FILA = ("| v480 | **El recorrido diario del campo, medido en un móvil** (375×812, con una "
        "obra de prueba asignada — sin datos no se podía juzgar la densidad, el pendiente "
        "que dejó v478). **(1) Fichaje**: las 4 tarjetas gastaban **230 px enseñando 0.00 h** "
        "y empujaban la acción de cada mañana a **y=618/759 de 812** — ahora las acciones van "
        "antes y no se pierde ni una cifra (v408). ⚠️ Matiza con medida lo que decía v308 ahí "
        "mismo. **(2) Una sola obra**: se abre sola donde se CONSULTA, y donde se ACTÚA es un "
        "**botón explícito** — v138 prohíbe preseleccionar al fichar. **(3)** El plan y la ruta "
        "bajan detrás de la tarea (la tabla de avance estaba en y=676), ⚠️ con `_contexto()` en "
        "**las dos salidas tempranas**, que si no desaparecía para quien aún no tiene obra. "
        "**(4)** La barra tenía **197 px vacíos** para el campo: ahora lleva su estado de "
        "fichaje, activo, con **0 lecturas nuevas** y textos que **caben medidos**. + se "
        "descartó una alarma propia (el campo **no** ve el margen) y queda **una pregunta "
        "abierta**: sí ve las tarjetas de costo y presupuesto. 25 comprobaciones |\n")

s = io.open(P, encoding="utf-8").read()
ANCLA = "## Versiones desplegadas (v479 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))
s = s.replace(ANCLA, SECCION + "\n## Versiones desplegadas (v480 = actual)")
s = s.replace(CAB, CAB + FILA)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: seccion v480 + fila + cabecera")
