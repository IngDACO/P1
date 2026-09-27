# -*- coding: utf-8 -*-
"""Documenta v517 — el vocabulario de obra."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"

SECCION = """## EL VOCABULARIO DE OBRA (v517)

F2a: la mitad **determinista** de interpretar el parte diario. Sin modelo y sin API — una
tabla de **339 términos** y una función que busca.

### ⚠️ De dónde sale, y por qué eso importa
De `docs/Process_Knowledge_Reference.md`, que **no es documentación escrita de una vez**:
es el resultado corregido de pasar un intérprete sobre partes REALES de instaladores. Las
**58 anotaciones «(Danilo, Sep 2026)»** de los tres documentos no explican diseño,
corrigen respuestas concretas. Eso no se reconstruye leyendo el catálogo.

⚠️ Y esos documentos **estuvieron a punto de perderse**: llegaron como adjuntos el
22/09/2026 y, tras dos compactaciones, solo existían dentro de un transcript de 19 MB. Se
rescataron de ahí y viven ahora en `docs/`, versionados y en el ZIP de cada despliegue.

### Para qué sirve si de todos modos va a haber un modelo detrás
1. **Barandilla.** Un modelo puede devolver «Landing Door Install», que suena bien y no
   existe. Aquí solo se propone una actividad del plan SELLADO de esa obra (regla v509).
2. **Suelo medible**, sin coste ni API, contra el que leer lo que aporta el modelo.
3. **Es lo único verificable hoy.** Una tabla se prueba; una interpretación solo se puede
   juzgar contra partes reales, y de esos todavía no hay.

### Las cuatro cosas que el documento pedía
| Parte | Qué sale |
|---|---|
| «Fitted the motor bedplate and the single bedplate» | las dos actividades, cada una con el término que la disparó |
| «Mounted the tirak» **en una instalación** | **0 candidatos** — 3 apartados por no estar en el plan |
| «Induction, then pre-start» | reconocido y marcado **no es avance** |
| «Under the cabin work» | **ambiguo**, con su regla: mecánico si los rieles no han subido, eléctrico si ya subieron |

⚠️ La última es la que más importa: el documento es explícito en que esas frases **no se
resuelven con vocabulario** sino con la cronología de la obra — justo el dato que
`stage_progress` guarda desde v514. Elegir una aquí sería inventar.

### ⚠️ Tres actividades existen en UN documento y no en el otro
`Lighten cabin`, `Bridging` y el `chaser job` están en el desglose de tareas y no en el de
etapas, que es de donde salió el catálogo **con sus pesos**. Los dos documentos han
derivado. No se cuelgan de la actividad más parecida —sería inventar trabajo con peso
ajeno—: se reconocen y se **declaran**, para que el usuario decida si entran y con cuánto.

### ⚠️ Mi comentario decía algo que el código NO hacía
Escribí que el término largo gana al corto, ordené por longitud… y nunca usé el orden:
recorrer todos los términos encuentra los mismos con cualquier orden. El `sorted` era
**decorativo** y el comentario mentía. Lo destapó la batería, con la rotura que invertía
el orden y no ponía nada rojo. Ahora se tapa el tramo ya explicado — ⚠️ y tapando **solo
el término, no sus espacios**: el espacio que cierra uno abre el siguiente, y con los
bordes incluidos «motor bedplate y single bedplate» solo reconocía el primero.

### Lo que NO alcanza, escrito en el módulo
**Verbos irregulares**: la raíz lleva «hanging» a «hang» pero no «hung» — una frase de
prueba con el irregular puso el guardián rojo acusando a código sano. **Y el sentido**:
«no pude hacer las puertas porque no llegaron los marcos» menciona las puertas y sale como
candidato. Una tabla no distingue lo hecho de lo impedido. Las dos son la razón de que
esto sea la MITAD y no la solución.

### Verificación
`verif_v517`, **41 comprobaciones**. Batería: **18 roturas, 18 cazadas + CONTROL** — tres
escaparon primero, y las tres eran huecos reales: una pasaba por el motivo equivocado
(comprobaba que ALGUNA ambigua tuviera dos alternativas, no la que rompí), otra cambiaba
una de dos claves sinónimas y no rompía nada, y la tercera destapó el `sorted` decorativo.
⚠️ Y `check_anclas_roturas` volvió a cazar un ancla muerta en **mi propia batería**, por
segunda versión seguida: traduje un texto al inglés (lo exigió `verif_v448`) y el ancla se
quedó apuntando al español. Suite: **149 verde**.
"""

FILA = ("| v517 | **El vocabulario de obra: 339 términos que apuntan a actividades reales.** F2a — la "
        "mitad DETERMINISTA de interpretar el parte, sin modelo ni API. Sale del documento de "
        "conocimiento del usuario, que no es documentación sino el poso CORREGIDO de pasar un "
        "intérprete sobre partes reales (**58 anotaciones «(Danilo, Sep 2026)»**). ⚠️ Esos documentos "
        "solo existían dentro de un transcript de 19 MB tras dos compactaciones: rescatados a "
        "`docs/`. ⚠️ Sirve de **barandilla**: solo se puede proponer una actividad del plan SELLADO "
        "de esa obra, así que el modelo no podrá inventarse un nombre (regla v509). Un parte de "
        "instalación que diga «tirak» recibe **0 candidatos**. ⚠️ Lo ambiguo sale MARCADO con su "
        "regla, nunca resuelto: el documento dice que «under the cabin work» depende de la "
        "CRONOLOGÍA, que es el dato que `stage_progress` guarda desde v514. ⚠️ Tres actividades "
        "existen en un documento y no en el otro — declaradas, no colgadas de la más parecida. "
        "⚠️ **Mi comentario decía algo que el código no hacía**: ordenaba por longitud y nunca usaba "
        "el orden; el `sorted` era decorativo y lo destapó la batería. 41 comprobaciones · **18/18 + "
        "control** · suite 149 verde |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v516 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v516 = actual)"
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
h = h.replace(A_HIST, "## Versiones desplegadas (v517 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v517 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v517 = actual)")
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
print("CLAUDE.md: fila v517 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
