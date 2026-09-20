# -*- coding: utf-8 -*-
"""Documenta v503 — el UnboundLocalError que v502 se llevó a producción.

Misma mecánica que `doc_v502.py`: sección larga a HISTORIAL.md, solo la fila a CLAUDE.md,
y se cae la más vieja para que la lista no crezca.
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"

SECCION = """## ⚠️ LIGAR UN NOMBRE QUE YA ERA UNA FUNCIÓN: la pantalla caída de v502 (v503)

v502 se desplegó y **tumbó la pantalla de detalle de proyecto entera**. Se vio al ir a
verificar el cambio en producción: donde tenía que estar la tabla había un traceback.

```
projects_ui.py:2425 in _detalle_proyecto
    ing = e1.multiselect(
projects_ui.py:2428 in <lambda>
    format_func=lambda u: _etq_us(_cmp_ed).get(u, u),
```

`_etq_us` es la **función de módulo** de `projects_ui` (L54), y `_detalle_proyecto` la
llama en la L2428. v502 escribió `_etq_us = auth.etiqueta_usuarios(...)` en la L2566 de
esa misma función. Python marca el nombre **local en el ámbito ENTERO**, así que la
llamada de la L2428 —que se ejecuta *antes*— revienta con `UnboundLocalError`.

Es la **trampa nº29** palabra por palabra: «si al traducir aparece una llamada `t(...)`
en una función donde `t` ya era una variable, Python la marca local en el ámbito ENTERO y
revienta — y nada de lo anterior lo ve». Los dos fallos de v439, otra vez.

### ⚠️ Lo que no lo vio, y por qué
`compileall` en verde · los 98 módulos importando sin queja · las 25 comprobaciones de
`verif_v502` · la batería **13/13** · los **135 guardianes** de la suite · y el ejercicio
contra la **hoja real**. Ninguna de esas redes ejecuta `_detalle_proyecto`, y
**importar no ejecuta** (v378). Lo vio la PANTALLA.

Es el argumento de v459 llevado hasta el final: el verde de seis redes distintas no dice
nada de una función que ninguna de las seis llama. Y es la razón de la regla de mirar
**el cambio** en producción y no el banner de versión — aquí el banner decía v502 y era
verdad; lo que no funcionaba era la pantalla.

### El arreglo: la función ya existía
`_etq_us(logins)` hacía exactamente lo que v502 reimplementó, y mejor: desempata
homónimos sobre **TODO el grupo**, no sobre la lista visible, «porque una identidad que
cambia de nombre según la pantalla no es una identidad» (v413). v502 había duplicado
lógica que ya estaba (es el concepto de v323: una sola definición). Ahora son dos líneas
menos, en el detalle y en `_estado_section`.

### La red nueva
Barrido estático sobre **todo `core/`** (en `verif_v502.py`, que es lo que protege):
ninguna función puede ligar un nombre que ya es función de módulo **y que ella misma
llama ANTES** de ligarlo.

⚠️ Mira el **ORDEN**, y eso importa: un `def` anidado antes de su única llamada es
legítimo. El primer barrido, sin orden, denunciaba `roster_ui._cumplimiento` (define
`_hm` en la L954 y lo llama en la L964) donde no hay ningún fallo. Con el orden dentro:
**0 casos** en todo `core/`.

Y la red **se autovalida contra un caso conocido-malo** antes de afirmar su cero, que es
la nº12: una sonda que «no ve nada» no prueba nada hasta demostrar que sabe ver.

### Verificación
`verif_v502.py`, **27 comprobaciones**. Batería: **14 roturas, 14 cazadas + CONTROL**,
con una rotura nueva que **recrea este fallo exacto**. Suite completa: **135 verde ·
0 rojo · 0 roto**. Verificado en producción abriendo la pantalla que estaba caída.
"""

FILA = ("| v503 | ⚠️ **v502 tumbó la pantalla de detalle de proyecto, y se vio al verificar en "
        "producción.** `_etq_us` ya era la función de módulo y `_detalle_proyecto` la llama en la "
        "L2428; v502 le puso ese nombre a una variable en la L2566 y Python la marca local en el "
        "ámbito ENTERO → `UnboundLocalError` en la llamada anterior. Es la trampa nº29 literal (los "
        "dos fallos de v439). ⚠️ **No lo vio nadie**: `compileall`, los 98 imports, 25 "
        "comprobaciones, la batería 13/13, los 135 guardianes y el ejercicio contra la hoja real — "
        "ninguna de esas redes EJECUTA esa función, y **importar no ejecuta** (v378). Lo vio la "
        "pantalla. Arreglado usando `_etq_us`, que ya hacía eso y desempata homónimos sobre TODO el "
        "grupo (v413), o sea que v502 había duplicado lógica existente. Red nueva sobre todo "
        "`core/`: nadie liga un nombre que ya es función de módulo y que llama ANTES — mira el "
        "ORDEN (un `def` anidado antes de su llamada es legítimo, como `roster_ui._hm`) y se "
        "autovalida contra un caso conocido-malo. 27 comprobaciones · **14/14 roturas + control** |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v502 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v502 = actual)"
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
h = h.replace(A_HIST, "## Versiones desplegadas (v503 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v503 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v503 = actual)")
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
print("CLAUDE.md: fila v503 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
