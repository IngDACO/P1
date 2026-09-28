# -*- coding: utf-8 -*-
"""Documenta v522 — el vocabulario contra 1070 partes reales: proponer, no asumir."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"
SUITE = sys.argv[1] if len(sys.argv) > 1 else ""
BATERIA = sys.argv[2] if len(sys.argv) > 2 else ""

SECCION = """## EL VOCABULARIO CONTRA 1070 PARTES REALES: PROPONER, NO ASUMIR (v522)

El usuario compartió desde Drive los partes de **Simpro** de 11 obras (capturas del móvil,
«Work Completed Notes»). Descargados desde su Chrome, organizados en `D:\\CopeX\\Logs_simpro`
(una carpeta por obra, FUERA del repo: llevan nombres de trabajadores) y leídos con el OCR
que trae Windows. ⚠️ El conector de Drive no servía: solo da el texto que Drive ya indexó
(34 de 80 en una obra) y su listado se cortó en 55 de 80 sin avisar. La lectura se validó
contra ese texto: **0,997** de similitud, con un control cruzado de 0,138 (la medida
discrimina).

### Lo que dijeron los partes reales del vocabulario de v517-v519
27% de las líneas de trabajo con propuesta, y de 60 propuestas al azar solo 38 del todo
bien. Los errores tenían forma: quitar leído como montar («taking off the Tirak» →
*Mount tirak*), **toda cuerda como belting** (la raíz de «roping» era la de «rope»),
**toda luz como iluminación** (era la cortina de la puerta, o «make it light»), 25
propuestas salidas de «Issues/Pendings», y frases de etapa («shaft wiring», 33 veces) sin
nada que proponer.

### La regla del usuario, y sus dos decisiones
«**La app no asume nada sin consultar**: el avance tiene que darse de forma correcta; más
autonomía, cuando la IA interprete mejor». (1) Una frase de ETAPA propone la etapa entera y
el de campo marca lo que hizo. (2) Varios ascensores en una nota: se propone separarla.

### Lo que cambió en `core/vocabulario.py`
- **El contexto de la ORACIÓN manda.** `buscar` parte la nota en oraciones: lo que va bajo
  «Issues/Pendings» o dice «still needs / can't / missing / tomorrow» va a `pendientes`; lo
  que es llevar material («loaded… onto the hilux») a `no_avance` —salvo las actividades
  que SON entregas—; un verbo de QUITAR se convierte en su retirada (*Remove tirak gear*,
  *Pack up*), en el desmontaje (la pieza dice si es mecánico o eléctrico) o se pregunta en
  `retiradas`. ⚠️ Nunca acredita montar: **0 de 227 oraciones** de quitar del corpus.
- **`etapas`**: la frase de etapa propone la etapa con sus actividades del plan, en una
  pasada APARTE y solo sobre lo que ninguna actividad reclamó («Prep all landing doors»
  sigue siendo *Prep doors*).
- **`ascensores()`**: «lift 3 and lift 1» → proponer separar (23 notas del corpus);
  «L3», «M2», «SL3» pueden ser NIVEL → van a `dudosos`, se pregunta.
- **Preguntar donde se acertaba o fallaba en silencio**: «lights», «governor rope»,
  «install rings/rails», «bedplate», «handrail», «clean pit».
- «roping» y «reverses» dejan de recortarse; alias con evidencia (car = cabin, CWT = CW,
  «hung», «govenor»…), no un diccionario.

### ⚠️ Cómo se midió sin hacerse trampas
30 notas enteras **reservadas y etiquetadas ANTES** de tocar el código, y ningún término
añadido por aparecer en ellas («Light SW», «Stop pit» siguen sin reconocerse). Antes → ahora:
**8 → 22 de 40** líneas con propuesta correcta, **3 → 1** errores seguros. En el corpus
entero: cobertura **28,3% → 39,2%**, propuestas desde «Issues/Pendings» **25 → 0**.
⚠️ Dos métricas salieron PEOR en la primera medida y eran del MÉTODO: pasaba las notas
línea a línea (el módulo no veía la cabecera «Issues») y contaba como error convertir
«taking off the Tirak» en *Remove tirak gear*. Se midió de nuevo nota a nota.
⚠️ Y tres fallos nuevos que salieron mirando el detalle, no el número: «rip-out kit» leído
como verbo (lo cazó el corpus de v517), «so [name] could take off» leído como quitar, y
«reverse rotation» montando paredes.

### ⚠️ Lo que cazaron las baterías (y lo que se aprendió de ellas)
- **Una rotura que COLGABA el guardián.** La primera versión de «la etapa compite con las
  actividades» le daba al bucle una máscara vacía en cada vuelta: buscaba la misma frase
  para siempre. 18 minutos de CPU al 100% y la batería detrás, sin tope. Una rotura tiene
  que imitar un fallo, no colgar la prueba: rehecha con su propia máscara, y `corre()` con
  **tope de 420 s** — un cuelgue se cuenta aparte y pone la batería en rojo.
- **Una batería que MURIÓ a medias dejó un parche puesto** (`elif False:` en el
  vocabulario): la herramienta mueve a segundo plano lo que pasa de 600 s y le cortó la
  tubería. El paso 0 («verde de base») lo detectó: la segunda corrida se negó a empezar. Se
  restauró comprobando las 17 anclas contra la lista de la propia batería. ⚠️ Las baterías
  largas, en segundo plano DESDE EL PRINCIPIO y con log.
- **Tres escapes, 14 de 17 a la primera:** «rip-out» como verbo pasaba porque otra red (las
  entregas no se convierten) tapaba la prueba; «L3» como ascensor seguro pasaba porque el
  ejemplo solo tenía una «L»; y una rotura no imitaba nada visible. Tres comprobaciones
  nuevas y una rotura rehecha → **17 de 17**.
- **5 anclas muertas en `romper_v517`**: la reescritura de `buscar` movió las líneas que esa
  batería rompe. Actualizadas con la razón escrita (caducadas, no relajadas): **28 de 28**
  sobre el código nuevo, y la deuda de `check_anclas_roturas` sigue en 15 exactas.

### Lo que NO hace todavía
Nada de esto se ve en la app: `buscar` no lo llama ninguna pantalla. El siguiente paso es la
pantalla donde el de campo ve las propuestas bajo su parte y **confirma** — la regla del
usuario hecha interfaz.

__VERIF__ · __BATERIA__ · __SUITE__
"""

FILA = ("| v522 | **El vocabulario contra 1070 partes REALES de Simpro: proponer, no asumir.** Regla "
        "del usuario: la app no asume — propone y él confirma. La oración manda: lo de «Issues/"
        "Pendings» se aparta (**25 → 0** propuestas), lo que se lleva no se monta, y un verbo de "
        "QUITAR nunca acredita montar (**0 de 227** oraciones). Frase de etapa → la etapa entera "
        "(decisión 1); varios ascensores → proponer separar, «L3» se pregunta (decisión 2). "
        "⚠️ Medido con 30 notas **reservadas y etiquetadas antes** de tocar nada: **8 → 22 de 40**, "
        "errores seguros **3 → 1**; corpus entero 28,3% → 39,2%. ⚠️ Dos métricas salieron peor y "
        "eran del MÉTODO (línea a línea). OCR de Windows validado 0,997; los partes, fuera del repo. "
        "__VERIF__ · __BATERIA__ · __SUITE__ |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v521 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v521 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA):
    raise SystemExit("faltan los resultados: doc_v522.py \"<suite>\" \"<bateria>\"")
for _k, _v in (("__VERIF__", "62 comprobaciones"), ("__BATERIA__", BATERIA), ("__SUITE__", SUITE)):
    SECCION = SECCION.replace(_k, _v)
    FILA = FILA.replace(_k, _v)

h = io.open(HIST, encoding="utf-8").read()
unica(h, A_HIST, "cabecera", "HISTORIAL.md")
unica(h, CAB, "tabla", "HISTORIAL.md")
unica(h, TRAS_CAB, "separador", "HISTORIAL.md")
h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v522 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v522 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v522 = actual)")
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
print("CLAUDE.md: fila v522 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
