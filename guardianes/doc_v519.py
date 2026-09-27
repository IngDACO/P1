# -*- coding: utf-8 -*-
"""Documenta v519 — las cuatro decisiones del usuario del 27/09/2026."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"

SECCION = """## LAS DECISIONES DEL USUARIO DEL 27/09/2026 (v519)

Cuatro preguntas que v518 dejó abiertas, contestadas por el usuario en una línea cada una:

| | Pregunta | Decisión |
|---|---|---|
| 1 | «Roping»: su documento lo resolvía de dos maneras | **A** — es *belting* ese día |
| 2 | Cuatro actividades del desglose de tareas que no estaban en el catálogo | **Entran, a modo informativo** |
| 3 | Cuánto pesa el desmontaje en una obra combinada (heredado: 14%) | **50/50, de momento** |
| 4 | ¿El parte diario trabaja sin conexión? | **No, de momento** — no hay código |

### 1 · Roping
Vuelve a ser sinónimo de *Install belts*. En v518 estaba MARCADO y sin acreditar nada
porque el documento se contradecía; con la decisión, la contradicción ya no existe y los
guardianes que vigilaban «no acreditar» se INVIERTEN — caducados por decisión, no relajados.

### 2 · Las informativas: se marcan, NO cuentan
*Lighten cabin* (R2), *Bridge landing door circuit* y *Cut/expand concrete door openings /
chaser job* (etapa 7), *Program controller parameters* (etapa 14) — cada una en la etapa
donde la pone el propio desglose de tareas.

⚠️ **Van en una tabla APARTE (`stages.INFORMATIVAS`), no en la de pesos con peso cero.**
Dos razones: `validar()` rechaza a propósito todo peso ≤ 0 —la regla caza un cero que
debería ser un número—, y así es **imposible** que muevan el avance: `plan_de`, la
renormalización y `avance_de` no las reciben NUNCA. No es que valgan cero; es que las
cuentas no las ven. Eso es más fuerte que un cero, que alguien puede cambiar.

⚠️ `_sobre` las pone en su PROPIA clave de cada etapa, y `acreditar` las acepta pero
**solo una actividad con peso toca su etapa**: marcar una informativa guardaba antes el
hecho y reescribía `Activities.Progress` con el MISMO número — una escritura inútil contra
la cuota y una que haría creer que movió algo. En el móvil salen debajo, **sin porcentaje**
y con el aviso *«For the record only — ticking these does not change the progress»*.

⚠️ **Por eso NO sube `VERSION`.** La versión identifica el JUEGO DE PESOS, y esto no añade
ninguno. Subirla habría bloqueado en solo lectura obras cuyo avance no cambió.

### 3 · El 50/50 solo afecta a obras NUEVAS
Comprobado ANTES de tocarlo, porque el reparto mueve el avance y el avance se reclama:
`projects.plan_nuevo` **sella** el porcentaje en el `StagePlanJSON` de cada obra, y
`plan_de_obra` lee el sellado. Una obra combinada creada con 14 se sigue midiendo con 14.
⚠️ Es PESO, no tiempo: los días siguen saliendo de `schedule.DIAS_POR_PISTA`.

### ⚠️ La huella de los pesos: el contrato de v514 deja de ser disciplina
La obra sella la versión del juego de pesos y `version_desfasada` la deja en solo lectura si
el catálogo cambió — pero eso solo funciona si quien cambia un peso SUBE la versión, y hasta
hoy lo sostenía la disciplina. `verif_v519` guarda una **huella (sha256) de los pesos por
versión**: cambiar UNA décima sin subir `VERSION` es un rojo. Las informativas no entran en
la huella. Comprobado contra el HEAD anterior: huella idéntica (`7240bebb83ccab8f`).

### ⚠️ Las baterías dejan de saltarse roturas en silencio
En v516 escribí «una batería no avisa de sus anclas muertas, solo las salta» y lo dejé así.
En esta tanda volvió a pasar: un ancla aparecía **dos veces**, la batería la saltó con «??»
y anunció «27 de 27» contando solo lo aplicado — y `check_anclas_roturas` no lo vio, porque
su regla es «aparece al menos una vez». Endurecer esa regla marcaría como muertas **diez
tuplas sanas** de baterías viejas que sustituyen la primera aparición a propósito (medido).
El arreglo va en las baterías: en v516, v517 y v519 una rotura no aplicable pone la batería
en **ROJO**. Validado con una sonda: una batería con un ancla muerta decía «0 de 0 roturas
cazadas» y salía **en verde**; ahora sale en rojo. Y la de v516 destapó que anunciaba 19 de
19 teniendo 20.

### Verificación
`verif_v519`, **28 comprobaciones** — con la etapa **a medias** (31%): la primera prueba que
hice fue con la etapa vacía y dio «0,0% → 0,0%», que no demuestra nada. Batería **13/13 +
control**. `verif_v517` 62 · corpus **49/49**, 0 errores (roping y tres informativas como
casos nuevos, suelo del trinquete 45 → 49 con la razón). **Hoja real 22/22**: etapa 7 a
**31,0% → 31,0%** y obra **3,50% → 3,50%** tras marcar las informativas, leído de la hoja;
combinada nueva sella 50, la que selló 14 sigue en 14. Limpia por dos caminos.
"""

FILA = ("| v519 | **Las decisiones del usuario del 27/09.** (1) «Roping» = belting: la contradicción de "
        "su documento, resuelta. (2) Cuatro actividades **entran a modo informativo**: se marcan y NO "
        "cuentan — ⚠️ en una tabla APARTE, no con peso cero (`validar` lo rechaza a propósito), así que "
        "`avance_de` no las recibe nunca; ⚠️ marcarlas no toca `Activities.Progress`. (3) **50/50** en "
        "obras combinadas — ⚠️ solo NUEVAS: el reparto va sellado en cada obra, comprobado antes de "
        "tocarlo. (4) Sin offline, de momento. ⚠️ **La huella de los pesos**: cambiar una décima sin "
        "subir `VERSION` ya es rojo — el contrato de v514 deja de depender de la disciplina. ⚠️ Las "
        "baterías **dejan de saltarse roturas en silencio**: una que anunciaba «0 de 0» salía en "
        "verde, y la de v516 decía 19 de 19 teniendo 20. Hoja real: etapa **31,0 → 31,0%** y obra "
        "**3,50 → 3,50%** tras marcar las informativas. 28 comprobaciones · **13/13 + control** · "
        "corpus 49/49 · hoja real 22/22 · suite 150 verde |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v518 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v518 = actual)"
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
h = h.replace(A_HIST, "## Versiones desplegadas (v519 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v519 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v519 = actual)")
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
print("CLAUDE.md: fila v519 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
