# -*- coding: utf-8 -*-
"""Documenta v515 — el survey deja de prometer un cronograma que ya no existe."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"

SECCION = """## EL SURVEY PASA AL CATÁLOGO, Y `PHASES` SE BORRA (v515)

v512 cambió los dos caminos que crean obras —cotización aceptada y alta manual— y el
survey se quedó atrás. Era el **último** sitio que llamaba a `build_schedule` sin filas
propias, así que seguía recibiendo las 11 fases ideales del modelo viejo.

### ⚠️ El problema era un DOCUMENTO, no un número
El informe del cliente imprime esas actividades en su sección 6 («Project schedule and
S-curve») y ese PDF **se sube a Drive y se registra en los documentos de la obra**. O sea
que la carpeta del proyecto contenía un calendario que no era el del proyecto:

| | Informe del survey | Obra real |
|---|---|---|
| actividades | 11 | 14 |
| nombres en común | **0 de 11** | |
| días / entrega | 33 d · 03/11 | 33 d · 03/11 |

El cliente veía *«Guide rail installation»* y preguntaba cómo iba; esa actividad **no
existe en el sistema**, que tiene *«Shaft Climb & Bedplates»* y *«Car Assembly»*. Ningún
cálculo estaba mal —avance, curva S, SPI y reclamaciones salen del catálogo desde v512—,
pero el papel que se entrega decía otra cosa.

### La decisión: sustituir, no mapear
El usuario lo zanjó: **las actividades son las del catálogo y las anteriores ya no van**.
Así que `PHASES`, `FASE_RIPOUT` y `detect_flags` se **borran**, y el camino por defecto de
`build_schedule` pasa a salir del catálogo. Quien no traiga filas propias recibe las
MISMAS etapas que la obra real, no una lista paralela que se queda vieja sola.

⚠️ **Reventar habría sido peor.** La primera idea fue que `build_schedule` sin
`custom_rows` lanzara error. Mirando quién llama: **39 sitios en los guardianes**, y buena
parte usan esa forma como *fixture*. Habrían caído todos a la vez por un cambio que no
iba con ellos. El tercer parámetro, además, recupera sentido: era un dict de banderas del
survey (`cortes`, `shaft`) y ahora son los **nombres de condicionales del catálogo**.

### ⚠️ Lo que se pierde de las banderas no es información
`cortes` (OR/OL fuera de límite) y `shaft` (BSR<BS) eran lo único que el survey de verdad
calculaba, y no tienen equivalente en el catálogo: sus 11 condicionales son cosas físicas
de obra (plataformas, sky climber, espejo, banderas de imán). Desaparecen del calendario
**pero no del informe**: los cortes siguen en el veredicto de portada y en la sección 3
**piso por piso**, y el BS/BSR en la suya. Se quita una duplicación peor, no un dato.

### ⚠️ El desmontaje deja de ser UNA actividad
`projects_ui` avisaba «este trabajo es ripout+instalación y su plan no tiene la actividad
de desmontaje» comparando contra el nombre fijo de `FASE_RIPOUT`. El **principio** sigue
vivo, así que el aviso se conserva con los nombres DERIVADOS del catálogo (trampa nº16).
⚠️ Y el nombre viejo se sigue aceptando: está **guardado en la hoja** de las obras
anteriores a v512, y rechazarlo les sacaría un aviso falso.

### ⚠️ Dos guardianes que habrían pasado a verde vigilando una lista VACÍA
`verif_v448` y `verif_v449` son los que impiden que los nombres de actividad se traduzcan
(son DATO: se guardan en la hoja). Estaban escritos como
`getattr(SCH, "PHASES", None) or getattr(SCH, "ACTIVIDADES", [])`, así que borrar `PHASES`
los habría dejado **en verde revisando cero nombres** — la trampa nº30 en su forma más
cara, porque la regla parece seguir viva. Re-apuntados al catálogo, vigilan los **191**
nombres reales.

⚠️ Y la sonda nueva tenía un fallo mío: comparaba `_sin(n) != n` cuando `_sin` baja a
minúsculas de paso, así que habría denunciado «Set Up» como acentuado. Se compara contra
`n.lower()` y **se valida con un caso conocido-malo** (nº12).

### ⚠️ El hallazgo grande: las baterías se pudren en silencio
`romper_v470` anunciaba **«5 de 13 roturas cazadas»** y ocho decían «ancla ausente».
Comprobado contra el HEAD anterior: **cinco llevaban muertas desde v512**, cuando el
modelo cambió a propósito y nadie volvió a la batería. Una batería con anclas muertas es
peor que no tenerla: imprime un recuento que parece cobertura.

El motivo de que se pudra sin que nadie lo vea es **estructural**: las `romper_*` NO están
en `run_suite.py` porque modifican el árbol (v455). De ahí sale `check_anclas_roturas.py`,
que es **estático** —no escribe un byte— y por eso sí entra en la suite: revisa las **52
baterías y sus 367 anclas** de una pasada.

⚠️ **Su primera versión acusó a 60 anclas y la mayoría estaban sanas.** Adivinaba cuál era
el ancla por su POSICIÓN («la cadena detrás del `.py`») y las baterías usan **cuatro
formas distintas** de tupla, así que leía DESCRIPCIONES. Habría llevado a «arreglar»
cincuenta baterías que funcionan — el fallo de v385. La afirmación se debilitó hasta la
que no tiene falsos positivos: *si NINGUNA de las cadenas de la tupla está en el fichero
que ella misma nombra, esa rotura no puede parchear nada.* De 60 a **17 reales**.

⚠️ Las 15 que no son de esta versión quedan como **DEUDA DECLARADA, no exceptuada**: es un
**trinquete** que falla si una batería tiene más muertas de las declaradas *y también si
tiene menos*. Lo segundo es lo que impide que la lista se convierta en el problema que
viene a denunciar. Se cazó a sí mismo en su primera pasada: había declarado una que yo ya
había reparado.

### Verificación
`romper_v470`: **13/13 + control** (era 5/13). `romper_v453`: **5/5** (era 3/5) — y una de
sus escapadas fue la trampa nº28 dentro del guardián del idioma: «Puertas de rellano» no
lleva acento, así que traducir una etapa se escapaba del detector. Suite: **147 verde**.
"""

FILA = ("| v515 | **El survey pasa al catálogo y `PHASES` se borra.** Era el ÚLTIMO sitio que pedía "
        "las 11 fases viejas, y de ahí salía la sección 6 del **informe del cliente** — un PDF que "
        "se sube a Drive y se archiva en la carpeta de la obra. O sea que el proyecto guardaba un "
        "calendario **con 0 de 11 nombres en común** con el suyo. ⚠️ Ningún número estaba mal "
        "(avance, curva S, SPI y reclamaciones salen del catálogo desde v512): era el **papel que "
        "se entrega**. Decisión del usuario: las actividades son las del catálogo y las anteriores "
        "ya no van. ⚠️ Reventar sin `custom_rows` habría tumbado **39 llamadas** de los guardianes "
        "que la usan de fixture, así que el camino por defecto sale del catálogo y el 3.er "
        "parámetro recupera sentido (banderas → condicionales). ⚠️ `verif_v448/v449` habrían pasado "
        "a **verde vigilando una lista VACÍA** (`getattr(..., [])`) — trampa nº30; re-apuntados, "
        "vigilan 191 nombres. ⚠️ **Hallazgo de fondo**: `romper_v470` llevaba desde v512 en «5 de "
        "13», porque las baterías **no están en la suite** (modifican el árbol). Nace "
        "`check_anclas_roturas`, estático, sobre las **52 baterías y sus 367 anclas** — y su primera "
        "versión acusó a 60 sanas por adivinar el ancla por su posición. 13/13 y 5/5 · suite 147 verde |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v514 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v514 = actual)"
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
h = h.replace(A_HIST, "## Versiones desplegadas (v515 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v515 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v515 = actual)")
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
print("CLAUDE.md: fila v515 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
