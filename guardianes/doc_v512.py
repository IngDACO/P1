# -*- coding: utf-8 -*-
"""Documenta v512 — el catálogo de etapas sustituye al plan de 11 fases."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"

SECCION = """## EL CATÁLOGO DE ETAPAS (v512)

Primera mitad del trabajo que pidió el usuario: que el campo pueda escribir en texto
libre lo que hizo y que eso se cargue en el cronograma. Antes de nada de IA hace falta
**contra qué mapear**, y eso es este catálogo — sacado de los documentos de campo de
COPEX (`Lift_Install_Stage_Activity_Draft_v1.md` y los otros dos), no de suposiciones.

**18 etapas · 173 actividades · 11 condicionales.** 14 etapas de instalación que suman
100%, 4 de desmontaje que suman otro 100%, y cada actividad con su peso dentro de su
etapa. `core/stages.py` es **módulo HOJA**: no importa nada de `core`, así que se
ejercita entero sin Sheets ni Streamlit.

### Por qué sustituye a `PHASES` y no convive con él
El modelo anterior describía **una secuencia ideal de 11 fases**. Una obra real salta de
un lado a otro, así que medir contra una secuencia que nadie sigue obliga a estimar a
ojo «¿cuánto va de esta fase?». El catálogo es lo contrario: un menú fijo donde cada
cosa hecha **suma su peso**, en el orden que sea.

Convivir no era opción: serían **dos números de avance**, y uno de ellos se cobra
(v507/v510). Es la regla v361 en el sitio donde más caro sale.

⚠️ Las 14 etapas pasan a ser **las actividades del cronograma**, así que la ruta crítica
(v499), la fecha por cadena (v500) y la línea base (v501) siguen funcionando sin tocar
nada. `compute_avance` tampoco cambia: sigue siendo Σ(peso·avance)/Σpeso.

### ⚠️ Dos fallos de aritmética que traía el documento
La **Stage 2 sumaba 106%**, no 100 — «Fire services access & assist» se añadió en
sep-2026 con un 6% sin rebalancear el resto (sin esa fila, las otras trece suman 100
clavadas). Y su encabezado decía 4% mientras la tabla de pesos decía 3%: con 4% las
catorce etapas darían 101, así que el correcto es **3%**.

No era la primera vez: una nota del propio documento cuenta que los sub-grupos de la
Stage 14 sumaban 104 y hubo que corregirlos. Un 6% de más es avance inflado y el avance
se cobra, así que ahora hay un **validador con guardián**, no una revisión a ojo. Se
recalibró **proporcionalmente**, no a mano: repartir ese 6% con criterio es decisión de
oficio del usuario, no aritmética.

### ⚠️ Los condicionales no pueden entrar en el denominador
Tracción e hidráulico son **excluyentes** — una obra es de una clase o de la otra. Si la
que no aplica se quedara contando, **un desmontaje de tracción no pasaría del 85% de su
R3 jamás**. Igual con el espejo, el falso coche y el ascensor de obra.

Al dar de alta se crean solo las que aplican y el plan **se renormaliza a 100**. Sin
eso, una instalación sin extras sumaba 97,48% y un desmontaje 78,30%.

⚠️ Y se renormaliza **dentro de cada pista**. La primera versión lo hacía sobre el
total, y entonces un desmontaje sin parte hidráulica encogía solo: se declaraba un 30%
de rip-out y salía **28,08%**. El reparto entre pistas es un juicio declarado, no algo
que deba moverse porque una obra lleve menos condicionales.

### ⚠️ Lo que NO se adivina
Si el tipo lleva desmontaje, el alta pregunta **tracción o hidráulico**, sin
preselección (v139), y **no deja crear** hasta que se responde. Son el 25% y el 15% del
R3: elegir «tracción» por ser lo común escondería un dato que falta dentro de un número
que parece calculado — el «1 inventado» que prohibió v509.

### El plan se SELLA con la obra
Columna `StagePlanJSON` al final de Proyectos (v363): versión del juego de pesos,
condicionales y reparto. ⚠️ Los pesos son **provisionales** y van a recalibrarse;
si la obra los leyera del catálogo vivo, recalibrar movería el avance de obras ya en
curso, y el avance es lo que se reclama. Misma razón que la línea base (v501). Guarda la
**versión**, no los pesos: copiarlos serían 173 números por obra.

⚠️ Una obra anterior a v512 no tiene plan, y eso **no es un error**: `plan_etapas`
devuelve `{}` y toda la cartera existente sigue igual.

### ⚠️ «Ripout» a secas YA tiene cronograma — decisión cambiada
En v470 el usuario decidió que NO. El motivo era concreto: no existían actividades de
desmontaje, así que lo único que se le podía dar eran las 11 fases de INSTALACIÓN, y eso
habría ensuciado avance, SPI y el radar con trabajo que esa obra no hace. El 22/09/2026
decidió lo contrario y **el motivo de antes ya no aplica**: el catálogo le da sus 4
etapas propias. No es la misma pregunta contestada al revés; es otra pregunta. Queda
escrito con las dos fechas para que no se lea como un capricho.

### Las duraciones son un arranque, no un dato
El catálogo pondera **esfuerzo**, no tiempo: no dice cuánto dura nada. Los días salen de
lo que la app ya suponía —`PHASES` sumaba 17 de base + 2,0 por parada, `FASE_RIPOUT` 3 y
0,5—, repartidos por peso. Una obra de 8 paradas da los 33 días de siempre.

⚠️ Se reparten por **resto mayor**. Redondeando cada etapa por su cuenta, catorce no
suman lo mismo que once y la entrega se movía **hasta 3 días**: de 30 números de
paradas, solo 7 daban la misma fecha. Y al medirlo apareció que **el que redondeaba mal
era el modelo viejo** — `PHASES` redondea fase a fase y su total se desvía de su propia
fórmula en los NS impares. Donde las dos fechas difieren, la que estaba mal era la vieja.

### La suite: 5 rojos, ninguno una regresión
`verif_v448`/`v449` cazaron dos mensajes en español míos (traducidos). `v306`, `v501` y
`v470` estaban atados a una **forma** que cambió a propósito (trampa nº16) y se
reescribieron sobre el principio, con la razón al lado (v385):
- v306: un tipo genera cronograma **si y solo si el catálogo le da etapas** — el valor
  se deriva del código en vez de ser una lista fija.
- v501: «BaselineJSON va AL FINAL» dejó de ser cierto al añadir la columna detrás. Lo
  que v363 protege es que **una columna existente no se mueva**, y eso es lo que afirma.
- v470: la palabra `ripout=` era del modelo viejo; el principio —que los dos caminos de
  alta armen el plan igual, y que la vista previa arme lo MISMO que la creación— sigue
  afirmado con el mecanismo de hoy.

### ⚠️ `check_nombres_libres` cazó un fallo antes de desplegar
Usé `_num` en `projects_ui` y ese módulo no lo tiene a nivel de fichero: un `NameError`
que solo habría saltado **al abrir el alta de una obra**. Es la familia exacta de v502,
que sí llegó a producción. La red de v509 se ganó el sueldo.

### Verificación
`verif_v512.py`, **86 comprobaciones**, con el validador **autovalidado** contra cinco
catálogos malos conocidos (sin eso, un validador roto devuelve lista vacía, que es
indistinguible de «todo cuadra»). Batería: **21 roturas, 21 cazadas + CONTROL**. Suite
completa: **145 verde · 0 rojo · 0 roto**.

⚠️ Dos roturas se escaparon a la primera, las dos por probar con **una sola muestra**:
el suelo de un día se miraba solo con NS=8 —donde el reparto del resto devuelve el día
que el truncado quitó— y las duraciones solo en obras de una pista, donde el divisor es
100 igualmente. Y una tercera escapó porque el chequeo buscaba `"_pregunta_etapas("` como
TEXTO, cadena que aparece en la propia **definición** de la función: la trampa nº2 en su
forma más tonta, buscando lo que yo mismo había escrito.

### Lo que queda para la siguiente
El nivel de abajo: las obras nacen con sus 14-18 etapas pero el avance se sigue
tecleando; las 173 actividades están en el catálogo y **nadie las usa aún**. Y
⚠️ `PHASES` sigue vivo en el survey, así que su informe enseña 11 fases mientras la obra
tiene 14 etapas — incoherente de cara al cliente, anotado y sin tocar para no ampliar el
alcance sin avisar.
"""

FILA = ("| v512 | **El catálogo de etapas sustituye al plan de 11 fases.** Primera mitad de lo que "
        "pidió el usuario —que el campo escriba en texto y eso cargue el cronograma—: antes de la IA "
        "hace falta contra qué mapear. **18 etapas · 173 actividades · 11 condicionales**, de los "
        "documentos de campo de COPEX. El modelo viejo describía una secuencia IDEAL y una obra real "
        "salta; este es un menú donde cada cosa hecha suma su peso en el orden que sea. ⚠️ El "
        "documento traía **dos fallos de aritmética** (la Stage 2 sumaba 106% y su encabezado "
        "contradecía la tabla) — recalibrada proporcionalmente y con validador. ⚠️ Los condicionales "
        "**no entran en el denominador**: tracción e hidráulico son excluyentes y contar la que no "
        "aplica dejaría un desmontaje clavado en el 85% para siempre. ⚠️ El plan se **sella** con la "
        "obra (`StagePlanJSON`) porque recalibrar pesos movería el avance de obras que ya reclaman. "
        "⚠️ **«Ripout» a secas pasa a tener cronograma** — decisión cambiada respecto de v470, y el "
        "motivo de entonces ya no aplica. ⚠️ Medir la entrega destapó que **el que redondeaba mal era "
        "el modelo VIEJO**. 5 rojos en la suite, ninguno una regresión: dos fallos míos de idioma y "
        "tres guardianes atados a una forma que cambió a propósito. 86 comprobaciones · **21/21 + "
        "control** · suite 145 verde |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v511 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v511 = actual)"
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
h = h.replace(A_HIST, "## Versiones desplegadas (v512 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v512 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v512 = actual)")
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
print("CLAUDE.md: fila v512 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
