# -*- coding: utf-8 -*-
"""Documenta v478 en CLAUDE.md."""
import io

P = "C:\\Users\\diego\\P1\\CLAUDE.md"

SECCION = """## La AUTOGESTION del campo, y el movil (v478)

Peticion del usuario: *«vamos a juntar my credentials, my payslips y my absences bajo
un nivel de autogestion»*, con tres criterios suyos — **los avisos repetidos son
deliberados** («ayudan a que no se pasen por alto»), **haz los ajustes que requieras**,
y **la cuenta de campo se piensa para el MOVIL: facil, pero igual de completa**.

La nav del campo pasa de **8 a 6**: *Mis proyectos · Fichaje · Pre-Start · Herramientas
· **Self-service** · Library*. Dentro, las tres, con **ausencias PRIMERA**: es la unica
con una accion; las otras dos son consulta.

### ⚠️ Esto REVIERTE una decision de v154/v430, y a sabiendas
Aquellas dejaron esas pantallas sueltas a proposito: *«enterrarla un nivel le costaria
un toque cada mañana justo a quien lo usa en el movil»*. Medido en el codigo antes de
tocar, esa razon **no aplica igual a las tres**: en credenciales el campo **solo mira**
(`editable=False`, las carga el admin) y en colillas mira y descarga; la unica donde
ACTUA es ausencias — y ahi la accion urgente (avisar de una baja, que v430 registra al
instante justo por eso) **recupera su toque con un atajo desde Fichaje**, que es la
pantalla que esa persona abre esa misma mañana.
⚠️ El atajo solo sale **si NO ha fichado**: quien ya ficho no va a avisar de una baja, y
seria ruido en la pantalla mas usada. Y no es una duplicacion accidental: es el criterio
del usuario —los avisos en varios sitios— aplicado a su accion mas urgente.

### ⚠️ Y una CORRECCION mia, sobre una idea que propuse yo
Propuse arreglar un «callejon sin salida» en credenciales: el campo ve que le vence una
y no puede hacer nada. **La premisa era incompleta**: `credentials.notify_expiring` ya
avisa por email/Telegram **al admin Y al propio dueño**, en cada login de administrador
y sin repetir dentro de ~25 dias (v104/v187). El aviso sale solo.
Lo que faltaba era de INFORMACION, no de mecanismo —en su pantalla no habia ni una
palabra de eso— asi que es **una linea, y solo si tiene algo por vencer**. Construir un
canal nuevo sobre una premisa equivocada habria sido peor que no tocar nada.
⚠️ Tres cosas de ese parche estaban MAL y se cazaron mirando las firmas ANTES de
aplicarlo (regla v135): `list_for` toma UN argumento, la columna es `ExpiryDate`, y
**`auth_ui` no tiene `logger` de modulo** — habria sido el NameError latente de
v370/v423, en una pantalla del campo.

### El movil: lo que SI se pudo medir sin sesion
Barrido de las 7 pantallas del campo buscando la clase de fallo que ya mordio dos veces
aqui (el lienzo de firma de v393, el mapa de v307): **0 anchos fijos** que se salgan de
375 px. Pero aparecio otro, medible: **la tabla de credenciales tiene 6 columnas**, y a
375 px eso deja ~60 px por columna con glide **recortando SIN elipsis** (v408) — o sea
que el numero que hay que enseñar en obra se ve a medias y nadie avisa.
Cura, la de v408/v398: **priorizar, no encoger**. Orden *Tipo · Estado · Vence · Number
· Clase · Fecha de emision*, **sin ocultar ninguna**, y `Tipo` **anclada**: es la
identidad, y sin anclar se escapa por la izquierda justo cuando alguien se desplaza a
mirar la fecha.
⚠️ **Lo dinamico queda PENDIENTE y dicho**: medir el recorrido diario a 375 px exige
entrar como usuario de campo, y eso pide una contraseña. Lo estatico esta hecho; la
friccion real no se supone.

### ⚠️ CUATRO guardianes caducaron, y uno defendia la decision contraria
Todos actualizados con su razon escrita, **ninguno relajado**:
- **v297 · v298** exigian que credenciales y colillas fueran SECCIONES. Pasan a afirmar
  lo que de verdad protegian: que el campo **siga LLEGANDO** a todo, sea seccion o
  sub-seccion — y que lo que sigue siendo seccion **no se reordene**.
- **v303** validaba los destinos de `navegar()` contra la nav del **ADMIN**, y desde
  v297 los destinos dependen del ROL: el atajo nuevo apunta a una seccion del campo.
  Pasa a la union de los tres. ⚠️ Eso ENSANCHA el universo a proposito, y queda escrito:
  lo que ese chequeo caza es el destino que no existe para NADIE.
- **v430** es el interesante: **defendia la decision contraria a la que el usuario acaba
  de tomar** («ausencias va suelta»). No se relajo — se reescribio sobre lo que protegia
  (que el campo llegue a sus ausencias) **y se le añadio una comprobacion que antes no
  existia**: que el atajo desde Fichaje exista. Asi la razon original de v430 la protege
  el guardian, no mi palabra: si alguien quita ese atajo, salta.

### Verificacion
`verif_v478.py`, **20 comprobaciones**: la nav en 6 con nada perdido y ⚠️ **ninguna de
las tres suelta ademas** (estar en dos sitios es el patron de v140 que esto evita); el
despachador comparando el **ID exacto** y no el display (v303); el atajo apuntando a un
destino que EXISTE y colgando de «no fichado»; el aviso de credenciales **EJECUTADO** en
sus cuatro casos (importar no ejecuta, v378); la tabla priorizada y anclada; y 0 anchos
fijos, con la sonda **validada contra un `width=600`** antes de creerse su cero.
Suite entera: **117 verde · 0 rojo · 0 roto**, sin bloque SIN DATOS.
"""

FILA = ("| v478 | **La autogestión del campo** (petición del usuario): *My credentials · "
        "My payslips · My absences* pasan a sub-pestañas de **Self-service** y su nav baja "
        "de **8 a 6** — importa porque esa cuenta se usa en el MÓVIL. ⚠️ Revierte a "
        "sabiendas la decisión de v154/v430 (*«enterrarla un nivel cuesta un toque cada "
        "mañana»*): medido, eso solo aplica a **ausencias**, la única donde el campo ACTÚA, "
        "y su acción urgente —avisar de una baja— **recupera el toque con un atajo desde "
        "Fichaje**, visible solo si no ha fichado. ⚠️ **Corrección mía**: propuse arreglar "
        "un «callejón sin salida» en credenciales y la premisa era incompleta — "
        "`notify_expiring` ya avisa al admin Y al dueño (v104/v187), así que el arreglo es "
        "**una línea**, no un canal nuevo; y tres errores del parche se cazaron mirando las "
        "firmas antes de aplicarlo (v135), incluido un `logger` inexistente. + **móvil**: "
        "0 anchos fijos hostiles en las 7 pantallas, y la tabla de credenciales reordenada "
        "con el criterio de v408 (**priorizar, no encoger**) con `Tipo` anclada. ⚠️ Cuatro "
        "guardianes caducaron y **uno defendía la decisión contraria** (v430, «ausencias va "
        "suelta»): se reescribió sobre lo que protegía **y gana la comprobación de que el "
        "atajo exista**. 20 comprobaciones · suite **117 verde** |\n")

s = io.open(P, encoding="utf-8").read()
ANCLA = "## Versiones desplegadas (v477 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))
s = s.replace(ANCLA, SECCION + "\n## Versiones desplegadas (v478 = actual)")
s = s.replace(CAB, CAB + FILA)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: sección v478 + fila + cabecera")
