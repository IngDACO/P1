# -*- coding: utf-8 -*-
"""Documenta v525 — la fecha del parte (1A) y las líneas sin ascensor (2B)."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"
SUITE = sys.argv[1] if len(sys.argv) > 1 else ""
BATERIA = sys.argv[2] if len(sys.argv) > 2 else ""
REAL = sys.argv[3] if len(sys.argv) > 3 else ""

SECCION = """## LA FECHA DEL PARTE Y LAS LÍNEAS SIN ASCENSOR (v525)

Las otras dos decisiones del usuario (29/09/2026) sobre lo que v523 dejó sin hacer: **1A**
(fechar con el día del parte) y **2B** (selector propio para las líneas sin ascensor).

### 1A · El día del TRABAJO, no el de confirmar
Hasta aquí lo confirmado desde un parte se fechaba al confirmar: un parte del lunes
confirmado el jueves decía que la etapa empezó el jueves. `StageProgress` gana `WorkDate`
**al final** (v363) y `acreditar(…, fecha=)` recibe el día del parte (a mano: hoy; ilegible
o del FUTURO: hoy — una fecha real posterior a hoy dibujaría avance que no ha pasado).
⚠️ Las fechas reales de la etapa salen de **TODOS** sus créditos con peso, no del de ahora:
el inicio es el primer día de trabajo y el fin el último — el parte que CIERRA una etapa no
la fecha si otra de sus actividades se hizo después. `save_field_progress` acepta esas
fechas: adelanta un inicio posterior, nunca atrasa uno anterior, y sin ellas se comporta
como siempre (la rejilla a mano no cambia). Los créditos de antes de v525 cuentan con su día
de registro. ⚠️ **Qué cambia y qué no:** el historial (la curva S real, las fechas de inicio
y fin); NO el %, ni el SPI, ni el importe de una reclamación (cobra el acumulado al emitirla).

### 2B · Las líneas que no nombran ascensor
En una nota de varios ascensores, lo que no nombra ninguno («cleaned the pit») iba a la obra
del parte: decidir por él. Ahora, si esas líneas PROPONEN algo —miradas juntas y en orden,
para que una cabecera «Pendings» siga mandando—, llevan **su propio selector, sin nada
elegido**, con las líneas a la vista; sin elegir, no se proponen en ninguna obra. El
registro de v524 guarda la elección bajo la clave `""`. Y un trozo sin nada que enseñar ya
no deja un «→ obra» vacío.

### ⚠️ Lo que salió por el camino
- **`romper_v514` tenía un ancla MUERTA desde v516**: «la hoja se cae del lote» se anclaba en
  `"StageProgress",` + el `)` de cierre, y v516 añadió `"DailyLogs"` detrás. Nadie volvió a
  correr esa batería, y `check_anclas_roturas` no la veía: la tupla usa `+ N +` con
  `N = chr(10)`, una LLAMADA, y quedaba entre las 128 «ilegibles» declaradas en v524.
  Enseñarle `chr()` hizo legibles **42 tuplas de 10 baterías** (128 → 86) y la destapó.
- **Y mi cambio mató otra de `romper_v514`** («se recalculan TODAS las etapas»): la lista de
  `_cambios` pasó a ser un bucle. ⚠️ **La leí mal a la primera**: filtraba la salida de las
  baterías por el formato `=== N de N ===`, y `romper_v514` imprime `13/15` — dos escapes que
  no vi hasta que el chequeo estático los señaló. Re-anclada: **15/15**. Lección: el resumen
  de CADA batería se lee entero; no todas lo escriben igual.
- **Esta vez el chequeo avisó en el acto**: el ancla «como si fuera MANUAL» de `romper_v523`
  murió al añadir `fecha=` a la llamada, y `check_anclas_roturas` —arreglado en v524 para
  leer constantes— lo dijo en la misma pasada.
- `_fecha_trabajo` toma «hoy» del MISMO `clock.now(grupo).strftime` que el sello `Updated`:
  la primera versión usaba `clock.today` y rompía los relojes falsos de `verif_v514/v519`,
  que solo ofrecen `strftime`. En vez de tocarlos, un solo reloj para las dos cosas.
- Guardianes viejos actualizados con su razón escrita: `verif_v514` (el número de columnas
  → el principio), `verif_v519` (compara orden y avance, no el diccionario entero),
  `verif_v523/v524` (sus stubs aceptan `fecha`).

26 comprobaciones · __BATERIA__ · __REAL__ · __SUITE__
"""

FILA = ("| v525 | **La fecha del parte (1A) y las líneas sin ascensor (2B)**, decisiones del "
        "usuario. Cada crédito guarda el día del TRABAJO (`StageProgress.WorkDate`, al final) y "
        "las fechas reales de la etapa salen de TODOS sus créditos: inicio el primero, fin el "
        "último — un parte del lunes confirmado el jueves fecha el lunes; ⚠️ cambia el historial "
        "(curva S real), no el %, ni el SPI, ni lo que se cobra. En notas de varios ascensores, "
        "las líneas sin ascensor que proponen algo llevan su propio selector, sin nada elegido. "
        "⚠️ Destapó un ancla de `romper_v514` MUERTA desde v516, escondida entre las ilegibles "
        "(`N = chr(10)`): el chequeo lee ahora `chr()` → 42 tuplas más vigiladas (128 → 86 "
        "ilegibles). 26 comprobaciones · __BATERIA__ · __REAL__ · __SUITE__ |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v524 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v524 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and REAL):
    raise SystemExit('faltan los resultados: doc_v525.py "<suite>" "<bateria>" "<hoja real>"')
for _k, _v in (("__BATERIA__", BATERIA), ("__REAL__", REAL), ("__SUITE__", SUITE)):
    SECCION = SECCION.replace(_k, _v)
    FILA = FILA.replace(_k, _v)

h = io.open(HIST, encoding="utf-8").read()
unica(h, A_HIST, "cabecera", "HISTORIAL.md")
unica(h, CAB, "tabla", "HISTORIAL.md")
unica(h, TRAS_CAB, "separador", "HISTORIAL.md")
h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v525 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v525 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v525 = actual)")
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
print("CLAUDE.md: fila v525 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
