# -*- coding: utf-8 -*-
"""Documenta v518 — el vocabulario, puesto a prueba contra frases reales."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"

SECCION = """## EL VOCABULARIO, PUESTO A PRUEBA CONTRA FRASES REALES (v518)

El usuario pidió «testea si funciona, ponlo a prueba». El problema de base: no hay partes
reales, y una frase que invento yo **acierta siempre** — la escribo sabiendo cómo la va a
leer. Eso es un espejo, no una medida (trampa nº1 en su forma más cara).

### ⚠️ El corpus: frases que el USUARIO cita, con la respuesta que da SU documento
`docs/` cita literalmente trozos de partes de instaladores para explicar cada corrección
—«Cleaned 4 car rails», «Installed 2 door blades — Lift 3», «yemny wheel»…— y en la misma
línea dice qué significan. Ese es el corpus (`ejercitar_v517_corpus.py`): **45 frases**, la
respuesta correcta tomada del documento con su cita al lado, y **5 negativas** sacadas de
su sección de BLOQUEOS reales (Kemset, tornillería, una sierra encerrada) — líneas que un
parte trae y que NO son avance.

⚠️ **Cómo leer el número, dicho antes de darlo:** el vocabulario salió de los MISMOS
documentos, así que un acierto dice «transcribí bien el conocimiento y el buscador lo
encuentra en prosa», **no** «generaliza a partes que nunca vio». Es un TECHO, no una
estimación. Para lo segundo hacen falta los partes en bruto.

### Primera pasada: 55% — y ningún test lo había visto
| Fallo | Frase real |
|---|---|
| ⚠️ **El verbo más frecuente no casaba consigo mismo** | «install» ≠ «installed» |
| Cantidad y sitio EN MEDIO de la frase del catálogo | «Cleaned **4 car** rails» |
| El paréntesis del nombre, que nadie escribe | «installed belts» ≠ «Install belts (motor, CW, cabin)» |
| Vocabulario que el documento DA y no transcribí | yemny wheel · plumb lasers · combo bracket |
| Lo que va «por defecto» quedaba sin puntuar | «Pit doors» |

⚠️ **El primero es el que más duele.** `install` → `install` pero `installed` e
`installing` → `instal`: la consonante doblada solo se recortaba si se había cortado una
terminación, condición que puse YO para que «install» no saliera «instal». Y el guardián
de v517 lo tenía **blindado**: afirmaba la FORMA de la raíz («install → install») en vez
del principio (las formas de un verbo coinciden). La trampa nº16 en un guardián escrito ese
mismo día. Ahora afirma el principio sobre seis verbos.

### El arreglo que abrió un riesgo, y cómo se midió
Tolerar palabras metidas en medio (`HUECO = 2`) arregla «Cleaned 4 car rails»… y el
negativo lo cazó enseguida: **«cleaned the pit, rails arriving tomorrow» acreditaba Clean
rails** — y los rieles ni siquiera habían llegado. Arreglo: el hueco **no cruza una
frontera de oración** (coma, punto, raya entre espacios). ⚠️ La raya DENTRO de una palabra
no corta: «3-phase» y «rip-out» son una palabra.

### ⚠️ Una sola pasada para los cuatro tipos
Antes los candidatos iban primero y lo ambiguo después, y eso daba dos respuestas que el
documento contradice: «fixed LADDER CONTACT» salía como Ladder contact **y además** como
«contacts» ambiguo (el documento: con el sitio nombrado, va al sitio), y «joined FLEX
cable» sin zona salía como «Flex cables (top of cabin)» (el documento: sin zona, LAS DOS).
Compitiendo juntos por longitud se resuelven solas. En empate gana lo marcado.

### ⚠️ El documento del usuario se contradice
«Roping»: el glosario dice que es belting ese día; la sección de ambiguos, con
confirmación, dice que es genérico y «don't default it to one fixed stage». Estaba como
sinónimo de Install belts —la primera lectura—. Ahora queda **MARCADO y sin acreditar
nada** hasta que el usuario decida, y hay un guardián que lo vigila.

### Contra la HOJA REAL (método v344)
`ejercitar_v517_real.py`, **29 comprobaciones**: dos obras con plan SELLADO (una
instalación y una combinada), partes escritos en la hoja, **releídos por el lote** como
los lee la app, e interpretados contra el plan **releído de la obra**. La raya «—»
sobrevive al viaje por Sheets byte a byte (la frontera de oración depende de ella). El
mismo parte de «orange box» **no propone nada en la instalación y sí en la combinada**, y
ninguna propuesta de ningún parte se sale del plan de su obra. `delete_project` se llevó
los partes sin limpiarlos a mano.

⚠️ **Y mi ejercicio tenía un hueco**: su foto contaba Projects y DailyLogs pero no las **32
filas de actividades** que crear dos obras escribe por debajo. Si `delete_project` dejara
de borrarlas, el ejercicio habría dado verde. Lo vio la verificación por un **segundo
camino** (10 hojas, 0 restos), no el ejercicio; ahora la foto las cuenta.

### Cinco fallos MÍOS en el propio proceso de probar
- **Dos roturas que no rompían nada**: renombraba «yemny wheel» a «yemny_wheel», y la
  normalización convierte el guion bajo en espacio — el término seguía siendo el mismo. Como
  el CONTROL que nació vacío en v514.
- **Un punto ciego de `check_anclas_roturas`** (v515): no distingue un ancla viva de una
  rotura cuyo texto de REEMPLAZO se convirtió en el código bueno. Lo cazó correr la batería.
- **Un `raise ImportError`** para cortar un script al importarlo, que habría hecho FALLAR
  la importación.
- **Un comentario falso** escrito mientras arreglaba otra cosa (que una variable la usaba
  la regla de la «e» muda; no la usaba, y quedaba muerta).
- **La trampa nº26 cuatro veces**: heredocs que rompieron `\\n`, rutas de Windows y «».

### Verificación
`verif_v517`: 41 → **61 comprobaciones**, con el corpus DENTRO como trinquete (0 errores
siempre; los aciertos no bajan del suelo de 45) — lo que se corre a mano se pudre, como las
baterías de v515. Batería: **27/27 + control**. Corpus: **45/45, 0 errores**. Hoja real:
**29/29**. Suite: **149 verde**.
"""

FILA = ("| v518 | **El vocabulario, puesto a prueba contra frases REALES.** Sin partes en bruto, una "
        "frase que invento yo acierta siempre; así que el corpus son **45 frases que el usuario "
        "CITA** de partes de verdad, con la respuesta que da su documento al lado, y 5 negativas de "
        "su sección de bloqueos. ⚠️ **Primera pasada: 55%.** El peor fallo: `install` no casaba con "
        "`installed` — el verbo más frecuente de los partes — y **el guardián lo tenía blindado** "
        "afirmando la forma en vez del principio (nº16). Además: cantidades en medio («Cleaned 4 car "
        "rails»), el paréntesis del nombre, vocabulario sin transcribir y lo «por defecto» sin "
        "puntuar. ⚠️ Tolerar palabras en medio abrió un riesgo que el negativo **midió**: «cleaned "
        "the pit, rails arriving» acreditaba Clean rails — ahora el hueco no cruza una coma. ⚠️ **El "
        "documento se contradice** con «roping»: marcado y sin acreditar hasta que el usuario "
        "decida. ⚠️ El 100% es un **techo**, no una estimación: mide la transcripción, no la "
        "generalización. Hoja real 29/29, limpia por dos caminos. **45/45 · 0 errores · 27/27 + "
        "control** · suite 149 verde |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v517 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v517 = actual)"
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
h = h.replace(A_HIST, "## Versiones desplegadas (v518 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v518 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v518 = actual)")
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
print("CLAUDE.md: fila v518 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
