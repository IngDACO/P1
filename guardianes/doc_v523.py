# -*- coding: utf-8 -*-
"""Documenta v523 — la pantalla donde se confirma lo que la app leyó en el parte."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"
SUITE = sys.argv[1] if len(sys.argv) > 1 else ""
BATERIA = sys.argv[2] if len(sys.argv) > 2 else ""
REAL = sys.argv[3] if len(sys.argv) > 3 else ""

SECCION = """## LA PANTALLA DONDE SE CONFIRMA LO QUE LA APP LEYÓ EN EL PARTE (v523)

La regla del usuario (28/09/2026) hecha interfaz: «**la app no asume nada sin consultar**;
más autonomía, cuando la IA interprete mejor». Debajo de cada parte PROPIO y sin revisar, el
de campo ve una tarjeta «What the app read in your log»:

- las **actividades** que nombra, cada una con la LÍNEA del parte que la respalda y sus
  avisos («dice que no está terminado», «dice que fue otro día», «informativa: no cuenta»);
- la **etapa como lista** cuando solo nombró la etapa («shaft wiring» → sus 8 actividades);
- las **preguntas** («lights» puede ser cinco cosas) con la regla del documento;
- lo **pendiente** y lo **retirado**, enseñado pero sin casilla.

⚠️ **Todo empieza DESMARCADO** y nada se acredita hasta «Confirm the N ticked», que llama a
`stage_progress.acreditar` con **origen `log` y el ID del parte en la nota** — la marca que
permitirá medir si la interpretación acierta, y con eso decidir cuánta autonomía darle.
«Nothing to credit» cierra la tarjeta sin tocar el avance. `DailyLogs` gana
`Reviewed`/`ReviewedBy` **al final** (v363); qué se acreditó NO se guarda ahí, vive en
StageProgress (una sola verdad). Solo el AUTOR revisa; el admin ve el estado, no confirma.
Si `acreditar` falla, el parte NO queda revisado y la tarjeta sigue.

### Varios ascensores (decisión 2 del usuario)
Un selector de obra por ascensor, con las obras SUYAS y **sin nada elegido**; lo que no
asigne no se propone en ningún sitio, y al confirmar se vuelve a comprobar que el destino es
suyo. `parte_propuestas.reparto` parte la nota y **repite la cabecera «Pending»** en cada
trozo: separar sin ella convertía lo pendiente en propuesta. «L2» se pregunta (ascensor o
piso) y ⚠️ **hasta que conteste, lo que va con él no va a ninguna obra**. Un solo ascensor
nombrado («lift 3 installed headers») NO parte la nota: la decisión del usuario fue separar
cuando hay VARIOS.

### La hoja real
`DailyLogs` pasó de 8 a 10 columnas y `Reviewed`/`ReviewedBy` quedaron en I y J — leído por
un SEGUNDO camino (gspread de solo lectura), que es donde `marcar_revisado` las calcula. Dos
obras de prueba, un parte de dos ascensores: cada crédito en SU obra, con origen `log` y el
ID del parte, `Activities.Progress` de la etapa 0 → 11; otro usuario no puede revisar; borrar
las obras no deja ni parte ni crédito huérfano, y la hoja queda idéntica. ⚠️ `DailyLogs` y
`StageProgress` estaban VACÍAS: nadie verá de golpe tarjetas de partes viejos.

### ⚠️ Lo que salió MIRANDO la pantalla a ancho de móvil, no de los tests
1. **«L2 call button» se proponía para la obra del parte** antes de contestar — o sea
   tratando «L2» como piso, que es justo lo que se estaba preguntando. Asumir por omisión.
2. **El parte se pintaba en UN párrafo** (Markdown se come el salto simple, desde v516), y la
   tarjeta cita LÍNEAS como prueba: no había dónde encontrarlas.
3. **«Confirm the 3 ticked» para 2 créditos**: la misma actividad sale en la lista de su
   etapa y en una pregunta; marcada en las dos, contaba doble.
4. La «×» de borrar salía sobre «— choose the job —» (era una opción `None`, no un
   placeholder); un único destino que NO era la obra del parte salía sin su nombre; y «tu
   parte habla de más de un ascensor» con un solo «L3».

### ⚠️ Y lo que salió RELEYENDO el diff antes de desplegar (trampa nº9)
- **«L2» de CABECERA.** Retener solo la línea que nombra «L2» no bastaba: con «L2» solo en
  su línea, lo de debajo depende de la respuesta igual, y se proponía en la obra del parte.
  `parte_propuestas.lineas_de` da lo que colgaría de él si fuera ascensor, y eso se retiene.
- **Preguntas que no cambian nada.** Se preguntaba por «L2 waiting on the scaffold» y se
  pedía obra para «lift 2 was in use by the builders». Ahora solo se pregunta si lo que
  cuelga de ahí PROPONE algo (`propone_algo`): una pregunta que no importa enseña a
  contestar sin leer.
- **Lo hecho en ESTA obra escondía el trabajo de otro ascensor.** La vista previa miraba lo
  acreditado aquí: «lift 3 installed sills» con los sills de lift 1 ya hechos → sin tarjeta,
  y el trabajo de lift 3 se perdía. Si la nota se reparte, lo hecho depende del DESTINO.

### ⚠️ Los guardianes, y dos pasos en vacío míos
`verif_v523` EJECUTA: la lógica contra el catálogo real, la escritura REAL de `acreditar`
con la hoja sustituida (no una copia de su validación) y la tarjeta con **`AppTest`** —
marcar, confirmar, fallar, vista admin—. ⚠️ Escribiendo el ejercicio real apareció que
«lo pendiente no pasa a propuesta» se probaba con «lift 3 sills», que **no casa con nada**:
pasaba sin probar nada (trampa nº1). Cambiada a «installed sills» y, de paso, cada «NO
aparece X» lleva ahora su control «X SÍ aparece cuando debe». Y un umbral que clavé a ojo
(«≥ 15 casillas») pasa a **derivarse** de `propuestas` (trampa nº16): la tarjeta ofrece
exactamente lo que la lógica saca. ⚠️ `check_anclas_roturas` cazó **3 anclas muertas en
`romper_v516`** por mis cambios (la fila lleva dos columnas más; el admin pasa `extra=`):
actualizadas con la razón escrita, deuda en 15 exactas.

### Lo que NO hace todavía
- El crédito lleva la fecha de CONFIRMAR, no la del parte (igual que marcar a mano). Un
  parte de ayer confirmado hoy cuenta hoy para la curva S.
- En una nota de varios ascensores, las líneas que no nombran ninguno van a la obra del
  parte (se ven bajo su nombre y pueden quedar sin marcar, pero no moverse a otra).
- No se guarda lo que se RECHAZÓ: se sabe qué se acreditó desde un parte, no qué se propuso
  y se dejó sin marcar. Para medir el acierto hará falta.

__VERIF__ · __BATERIA__ · __REAL__ · __SUITE__
"""

FILA = ("| v523 | **La pantalla donde se confirma lo que la app leyó en el parte.** La regla del "
        "usuario hecha interfaz: debajo de cada parte propio y sin revisar, actividades con la "
        "LÍNEA que las respalda, la etapa como lista, las preguntas y lo pendiente sin casilla. "
        "⚠️ **Todo desmarcado**; solo lo marcado se acredita, con origen `log` y el ID del parte "
        "(lo que permitirá medir el acierto). Varios ascensores: obra por ascensor, sin nada "
        "elegido; «L2» se pregunta y ⚠️ lo que va con él (también debajo, si es cabecera) no va "
        "a ninguna obra hasta contestar; y no se pregunta lo que no cambia nada. ⚠️ Mirar la "
        "pantalla a ancho de móvil destapó 4 fallos que los tests no veían (el «L2» asumido como "
        "piso, el parte en un párrafo, «3 marcadas» para 2 créditos, destinos sin nombre) y "
        "releer el diff, 3 más. `verif_v523` ejecuta la tarjeta con AppTest; ⚠️ dos pasos en "
        "vacío míos arreglados. __VERIF__ · __BATERIA__ · __REAL__ · __SUITE__ |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v522 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v522 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and REAL):
    raise SystemExit('faltan los resultados: doc_v523.py "<suite>" "<bateria>" "<hoja real>"')
for _k, _v in (("__VERIF__", "111 comprobaciones"), ("__BATERIA__", BATERIA),
               ("__REAL__", REAL), ("__SUITE__", SUITE)):
    SECCION = SECCION.replace(_k, _v)
    FILA = FILA.replace(_k, _v)

h = io.open(HIST, encoding="utf-8").read()
unica(h, A_HIST, "cabecera", "HISTORIAL.md")
unica(h, CAB, "tabla", "HISTORIAL.md")
unica(h, TRAS_CAB, "separador", "HISTORIAL.md")
h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v523 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v523 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v523 = actual)")
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
print("CLAUDE.md: fila v523 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
