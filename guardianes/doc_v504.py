# -*- coding: utf-8 -*-
"""Documenta v504 — el «None» que pintaba cada celda sin responsable."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"

SECCION = """## LA PALABRA «None» EN CADA CELDA VACÍA (v504)

La columna Responsable de v502 funcionaba, pero **toda actividad sin dueño mostraba
literalmente la palabra `None`**. Un `st.column_config.SelectboxColumn` cuya opción de
«vacío» es la cadena vacía pinta `None` en la celda; «After», que también es opcional,
queda en blanco porque es `TextColumn`.

### ⚠️ Cómo se vio, y por qué no se podía ver de otra forma
No aparece compilando, ni en los 135 guardianes, ni en el DOM: `st.data_editor` pinta en
un **canvas** (v398/nº18). Se vio **interceptando `CanvasRenderingContext2D.fillText`** en
producción y mirando las posiciones:

```
Order@32 · Activity@147 · Owner@355 · Days@475 · After@585 · Weight@694 · Progress %@792
«None» × 20  en  x≈332-360   → la columna Owner
```

⚠️ Y hubo que forzar un repintado **REAL** (`resize_window`): un `new Event('resize')`
sintético no dispara nada, glide observa su contenedor. La sonda se validó antes contra
un caso conocido-bueno —pintar uno mismo y comprobar que el hook lo registra— porque un
«0 pintado» no significa nada hasta demostrar que la sonda sabe ver (nº12).

### El arreglo
La opción de «sin responsable» pasa a llevar TEXTO (`— nobody —`). La vuelta a login
sigue dando `""` sola, porque el mapa inverso se construye de `_lbl_de` y esa clave no
está ahí — no hay caso especial que mantener.

### Verificación
`verif_v502.py`, **29 comprobaciones** (red nueva: la opción vacía lleva texto y la fila
sin dueño la usa). Batería: **15 roturas, 15 cazadas + CONTROL**. Suite: **135 verde ·
0 rojo · 0 roto**. Verificado en producción leyendo otra vez el canvas.

_Nota de método: v502, v503 y v504 son la misma lección tres veces. Las redes locales
—compilar, importar, 135 guardianes, batería, hoja real— no ven lo que solo existe
cuando la pantalla se EJECUTA. Las tres las cazó abrir la pantalla en producción._
"""

FILA = ("| v504 | **La palabra «None» en cada celda sin responsable.** Un `SelectboxColumn` cuya "
        "opción de vacío es la cadena vacía la pinta literal; «After», opcional también, queda en "
        "blanco por ser `TextColumn`. ⚠️ **No se ve compilando ni en el DOM**: `st.data_editor` "
        "pinta en canvas, así que se cazó interceptando `fillText` en producción y midiendo las "
        "posiciones (**«None» × 20 en x≈332-360**, justo la columna Owner@355) — y forzando un "
        "repintado REAL, porque un `resize` sintético no dispara nada. La sonda se validó antes "
        "contra un caso conocido-bueno (nº12). Arreglado con una opción con TEXTO; la vuelta a "
        "login sigue dando «» sola. 29 comprobaciones · **15/15 roturas + control** · suite 135 "
        "verde. ⚠️ v502-v503-v504 son la misma lección tres veces: lo que solo existe al EJECUTAR "
        "la pantalla no lo ve ninguna red local |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v503 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v503 = actual)"
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
h = h.replace(A_HIST, "## Versiones desplegadas (v504 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v504 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v504 = actual)")
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
print("CLAUDE.md: fila v504 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
