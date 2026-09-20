# -*- coding: utf-8 -*-
"""Documenta v505 — el material que bloquea una actividad. Cierra la auditoría."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"

SECCION = """## EL MATERIAL QUE BLOQUEA UNA ACTIVIDAD: el retraso con causa (v505)

Quinto y **último** hueco de los que dejó medidos la auditoría de gestión de instalación.
Con lo anterior la app ya sabía **qué** va tarde (v499, dependencias y ruta crítica),
**cuánto** (v500, pronóstico desde la cadena), contra **qué** se mide (v501, línea base)
y **de quién es** (v502, responsable). Faltaba **por qué**.

Ahora una orden de compra puede decir a qué actividad está esperando, y esa actividad
lo cuenta donde se mira el retraso: *«no arrancó · esperando Riel T75 (late since 18/09)»*.

### Decisiones del usuario
- **Una actividad por orden**: columna al final de `PurchaseOrders` con el **nº de Orden**
  de la actividad. Mismo criterio que las predecesoras de v499, y `save_activities` ya
  remapea los órdenes al reordenar. Se guarda el ORDEN y no el nombre: el nombre se edita.
- **Se ve en el diagnóstico de retraso**, junto a la parada y la arrastrada — la causa al
  lado del síntoma, no en una pantalla aparte.
- **El campo lo VE, en solo lectura.** Saber que el material no ha llegado es justo lo que
  evita el viaje en balde. Va como aviso ANTES de la tabla y no como columna: ya son seis
  y el campo entra por el móvil, donde una séptima corta los nombres (medido en v408).

### ⚠️ Las tres cosas que fallarían en silencio
1. **Solo bloquea lo PENDIENTE.** Una orden recibida ya no bloquea nada y una cancelada
   tampoco; si no, la obra se quedaría «esperando» material que ya está en el sitio.
2. **Sin fecha esperada, bloquea pero NO se dice atrasada.** Es el mismo criterio de
   `atrasadas` (v343): no se puede afirmar que algo llega tarde si nadie dijo cuándo
   llegaba.
3. **Una orden sin actividad no bloquea a nadie.** Se pidió material para la obra, no
   para un paso concreto; decir que bloquea «la 3» sería inventárselo.

Y las órdenes siguen siendo **opcionales**: sin la hoja, o con la hoja caída, la pantalla
de estado —la que se mira justo cuando algo va mal— sigue en pie.

### ⚠️ El guardián cazó un fallo REAL antes de desplegar
Con una celda de basura (`"tres"` en vez de un número) la orden quedaba colgada de una
actividad **fantasma nº 0**: `_num()` degrada a `0.0` **sin lanzar**, así que el
`try/except` no se disparaba nunca. Y si una obra llegara a tener un Orden 0, la
bloquearía sin motivo. `_num` es la herramienta equivocada aquí: hace falta saber si el
texto **es** un número, no obtener un número a toda costa.

### ⚠️ Y dos lecciones de método, las dos mías
- **Una rotura que no rompe nada no prueba nada.** Quitar la guarda de «orden sin
  actividad» no cambiaba el comportamiento, porque el parseo estricto también tira la
  cadena vacía — dos redes sobre lo mismo. La rotura de verdad es la que **inventa** a
  quién bloquea: una orden sin actividad colgándose de la 1.
- **Mi ejercicio contra la hoja real pasó EN VACÍO la primera vez.** La foto leía una
  hoja llamada `Orders` —se llama `PurchaseOrders`— y un `except` se tragaba el fallo, así
  que devolvía vacío: el chequeo de «la columna va al final» comparaba `-1` con
  `len([])-1 = -1` y **aprobaba sin mirar nada**. Es la trampa nº1 dentro de la propia
  verificación. Ahora el nombre sale del módulo y una foto que no se puede tomar **aborta**
  en vez de devolver una foto falsa.

### Verificación
`verif_v505.py`, **26 comprobaciones**, ejecutando `bloqueos` de verdad. Batería:
**12 roturas, 12 cazadas + CONTROL** ⚠️ (dos escaparon en la primera pasada: una rotura
que no rompía nada, y otra que hacía **reventar** al guardián en vez de ser denunciada —
tercera vez en el día con ese patrón, ya corregido en los tres). Suite completa:
**136 verde · 0 rojo · 0 roto**.

**Ejercitado contra la HOJA REAL** (método v344): la columna se creó sola (**15 → 16**,
`ActivityOrder` en el índice 15). Una orden ligada a la actividad 2 bloqueó **la 2 y no la
1**, con su descripción y sin declararse atrasada (fecha futura); al dejar de estar
pendiente, dejó de bloquear. Las órdenes de prueba se borraron de la hoja y la cabecera
quedó intacta. ⚠️ La rama RECIBIDA se prueba en el guardián y no contra la hoja: recibir
**crea una fila en `Gastos`** que la app no sabe borrar, y no se ensucia la contabilidad
de la obra para probar un invariante que ya está cubierto.

---

Con esto **se cierra la auditoría de gestión de instalación**: v499 · v500 · v501 · v502 ·
v505. La app pasó de decir «vas al 40%» a decir «la 3 lleva 4 días parada, es de Ana, y
espera un riel que llegaba el 18».
"""

FILA = ("| v505 | **El material que bloquea una actividad: el retraso con causa.** Cierra el "
        "ÚLTIMO hueco de gestión de instalación (v499 qué · v500 cuánto · v501 contra qué · v502 de "
        "quién · v505 **por qué**). Una orden de compra dice a qué actividad espera y la actividad "
        "lo cuenta donde se mira el retraso; el campo lo ve en solo lectura, como aviso y no como "
        "columna (en móvil una séptima corta nombres, v408). ⚠️ Solo bloquea lo **pendiente**, "
        "⚠️ sin fecha esperada bloquea pero **no se dice atrasada** (criterio de v343) y ⚠️ una "
        "orden sin actividad **no bloquea a nadie**. Las órdenes siguen siendo opcionales: sin hoja "
        "o con la hoja caída, la pantalla de estado sigue en pie. ⚠️ **El guardián cazó un fallo "
        "real antes de desplegar**: `_num('tres')` degrada a 0.0 sin lanzar, así que la basura se "
        "colgaba de una actividad FANTASMA nº 0. ⚠️ Y mi ejercicio contra la hoja **pasó en vacío** "
        "la primera vez (leía `Orders`, se llama `PurchaseOrders`, y un except se lo tragaba: "
        "comparaba -1 con -1). 26 comprobaciones · **12/12 roturas + control** · suite 136 verde |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v504 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v504 = actual)"
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
h = h.replace(A_HIST, "## Versiones desplegadas (v505 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v505 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v505 = actual)")
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
print("CLAUDE.md: fila v505 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
