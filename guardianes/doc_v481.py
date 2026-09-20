# -*- coding: utf-8 -*-
"""Documenta v481 en CLAUDE.md."""
import io

P = "C:\\Users\\diego\\P1\\CLAUDE.md"

SECCION = """## El campo deja de ver el dinero de la obra (v481)

Decisión del usuario, tomada sobre la pregunta que dejó abierta v480. Y con un dato que
apareció **al ir a implementarla**: yo había reportado que el campo veía «las tarjetas de
costo y el presupuesto», y era **incompleto**. Veía también **la mano de obra PERSONA POR
PERSONA** (`Labour by person`), que es el dato del que se deduce lo que cobra cada
compañero, además de las órdenes de compra y la curva de gasto acumulado.
⚠️ Ese error mío venía de una sonda que probaba la línea del **comentario** de cada
bloque, que va justo ANTES del `if` que lo protege — así que daba «sin guarda» para
bloques que sí la tenían y viceversa. Se vio porque **se contradecía con lo que ya había
leído en el código**, no porque la sonda avisara.

### Qué sale y qué se queda
Sale de 💰 Recibos para el campo: el titular «a este ritmo costará X, Y por encima», las
tarjetas **Costo total · Compras · Mano de obra · Presupuesto · Costo al terminar ·
Comprometido**, la barra «llevas gastado X de Y» con su aviso OVER BUDGET, las órdenes
de compra, el reparto del costo por categoría, **la mano de obra por persona** y la curva
de gasto.
Se queda lo suyo: **cargar recibos y ver los recibos de la obra, con su importe** — sin
eso la pestaña no sirve para nada. Medido después del cambio: en lo que el campo ve queda
**1** sola cifra de dinero (el importe del recibo); las otras **17** viven ya en la
función de gestión.
El admin y el propietario no cambian en nada.

### ⚠️ Cómo se hizo, que importa tanto como el qué
- **Extraído, no envuelto.** El bloque son ~140 líneas ya a profundidad de cuerpo de
  función, así que sacarlo a `_costos_section` **no reindenta ni una línea**. Envolverlo
  en un `if` habría movido las 140 — la clase de cambio que rompió v120 y v148.
- **El interruptor es `ver_costos`, no `can_delete`.** Reutilizar `can_delete` habría
  sido gratis y es una trampa: ese permiso dice «puede borrar recibos», y quien mañana
  quiera dejar al campo borrar los suyos le abriría las finanzas de la obra **sin
  enterarse**. Un permiso que decide dos cosas distintas acaba decidiendo la que no era.
- **Por defecto `False`**: un sitio de llamada nuevo que se olvide **no enseña dinero**.
  Falla cerrado.
- **Verificado antes de escribir**: el parche comprueba que la función extraída no quede
  con ningún nombre huérfano — eso no falla al importar, solo cuando alguien ABRE la
  pantalla (el NameError latente de v370/v423). ⚠️ Y el verificador acusó primero a
  `_blq_reparto` y `_blq_categorias`, que son **funciones anidadas dentro de la propia
  región**: era un fallo del verificador, no del código. Se corrigió y se le puso un
  **control** que le da un huérfano construido para comprobar que sabe verlo.

### Verificación
`verif_v481.py`, **17 comprobaciones**. La que vale es la última: **EJECUTA**
`render_expenses` con `_costos_section` interceptada y comprueba que con el campo **no se
llama** y con gestión **sí** — ⚠️ el caso positivo al lado del negativo a propósito, porque
si la función reventara antes de llegar también saldría «no se llamó» y parecería que
protege (trampa nº12). Lo demás: que el interruptor no sea `can_delete`, que el defecto
sea `False`, que las cinco piezas de dinero estén fuera y las dos de recibos dentro.
"""

FILA = ("| v481 | **El campo deja de ver el dinero de la obra** (decisión del usuario sobre "
        "la pregunta abierta en v480). ⚠️ Al implementarla apareció que mi reporte era "
        "**incompleto**: veía también **la mano de obra PERSONA POR PERSONA**, las órdenes de "
        "compra y la curva de gasto — el error venía de una sonda que probaba la línea del "
        "**comentario**, no la del `if`. Se queda con lo suyo: cargar y ver recibos con su "
        "importe (**1** cifra de dinero frente a **17** que pasan a gestión). ⚠️ **Extraído a "
        "`_costos_section`, no envuelto en un `if`**: 140 líneas ya a profundidad de función, "
        "así que no se reindenta ni una (v120/v148). ⚠️ Interruptor **`ver_costos`, NO "
        "`can_delete`** —ese dice «puede borrar recibos», y reutilizarlo abriría las finanzas "
        "a quien mañana pueda borrar las suyas— y **por defecto False**: falla cerrado. "
        "17 comprobaciones, la última **ejecutando** ambos casos |\n")

s = io.open(P, encoding="utf-8").read()
ANCLA = "## Versiones desplegadas (v480 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))
s = s.replace(ANCLA, SECCION + "\n## Versiones desplegadas (v481 = actual)")
s = s.replace(CAB, CAB + FILA)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: seccion v481 + fila + cabecera")
