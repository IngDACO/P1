# -*- coding: utf-8 -*-
"""Documenta v534 — lo que destapó terminar de cerrar en producción (Survey real)."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"
NEG = "C:/Users/diego/P1/NEGOCIO.md"
SUITE = sys.argv[1] if len(sys.argv) > 1 else ""
BATERIA = sys.argv[2] if len(sys.argv) > 2 else ""
PROD = sys.argv[3] if len(sys.argv) > 3 else ""

SECCION = """## LO TECLEADO YA NO SE PIERDE AL SALIR DE UNA HERRAMIENTA (v534)

Quedaba por probar EN PRODUCCIÓN el Survey de punta a punta (v530 y los dibujos de v532). Se
hizo con la sesión de campo y el caso del fixture, tecleado a mano: 23 parámetros y una
matriz de 3 pisos. v530 y v532 salieron bien (ver la fila de v533). Pero recorrer la pantalla
de verdad enseñó seis cosas que ningún test miraba.

### ⚠️ 1. Lo tecleado se perdía al salir de la herramienta
Con el survey calculado, un clic en «Rails» y otro de vuelta en «Survey»: **los 23 parámetros
a 0,00, las paradas a 2 y la matriz cortada a 2 filas**. Los resultados seguían en pantalla
con el aviso «You changed data since the last calculation», y «Recalculate» habría calculado
con ceros. Un técnico que teclea 12 pisos en obra y pulsa «Timeclock» para fichar lo perdía
todo.

Streamlit borra el valor de un widget en cuanto una pasada no lo pinta. `survey_ui` lo sabía
y reasignaba sus claves… DENTRO de su pantalla, que en las pasadas de otra sección no corre.
Las otras cuatro herramientas no lo hacían en ningún sitio.

→ `core/estado_vivo.pasada()`, llamado desde `app.py` en CADA pasada, después del login:
reasigna las entradas de las cinco herramientas. ⚠️ Con **lista cerrada**: a un botón, una
tabla editable o una subida no se les puede asignar la clave (Streamlit lanza una excepción),
así que no se va por prefijos amplios. El guardián exige las dos cosas leyendo el código:
que toda entrada de las herramientas esté en la lista y que ningún botón lo esté.

#### ⚠️ Lo que ese borrado protegía sin querer (visto releyendo el arreglo, antes de desplegar)
La suite estaba en verde (163) y el arreglo listo. Releyendo el diff: `plan_ui.aplicar` solo
rellena un campo **si está vacío**. El técnico que calcula Rieles en la obra A, ficha en la B
y vuelve, encontraba los campos vacíos —Streamlit los había borrado— y se rellenaban con el
plano de B. Conservándolos sin más se habría quedado **el LFKK de A bajo el nombre de B**, en
un corte que no se deshace. El borrado era un fallo y, a la vez, la única protección.

→ Lo conservado es **de una obra**. `plan_ui.selector_proyecto` —las cinco herramientas lo
llaman lo primero— avisa de con qué obra se pinta cada una; si la herramienta VUELVE (no se
pintó en la pasada anterior) y la obra es otra, sus entradas se olvidan y manda el plano
nuevo: exactamente lo que pasaba antes. Misma obra, o ninguna las dos veces → se conservan.
Cambiar de obra sin salir de la herramienta no borraba antes y no borra ahora («Duplicate
for the next lift» cuenta con ello). Lo que otra pantalla carga a propósito —reabrir un
cálculo, reconstruir un survey— se respeta. La obra elegida por el admin en cada herramienta
también se conserva (si no, al volver siempre sería «otra»); la fase del Survey no: al volver
se abre en «Survey data», que es donde se mira la obra.

#### ⚠️ Y de paso: «reabrir un cálculo» tumbaba la pantalla
Al leer cómo se restauran las entradas: la foto que se guarda con cada cálculo cogía todo lo
que empezara por el prefijo de la herramienta, **incluido el botón de calcular**
(`rc_calc1: false`). Al reabrirlo se le asignaba ese valor y Streamlit lanza «Values for the
widget with key 'rc_calc1' cannot be set using st.session_state». Ejecutado con la pantalla
real de Rieles: excepción. Ahora solo se guardan y se restauran entradas y tablas — el filtro
va también al restaurar, porque los cálculos ya guardados traen el botón dentro (leído en
la hoja real: los 4 cálculos guardados de `cliente1` lo traen).

#### ⚠️ La batería cazó un paso en vacío del propio guardián
Dos roturas escaparon: quitar el «respeto» a lo reabierto no ponía nada rojo. Los guiones de
AppTest corren en el MISMO proceso y comparten los módulos: el guion que anulaba `al_pintar`
para enseñar el peligro lo dejaba anulado para el siguiente, así que «lo reabierto se
respeta» pasaba porque ya no se olvidaba NADA. Ahora cada guion repone lo que sustituye, y
el test lleva su control: en la misma situación, sin reabrir, sí se olvida.

### 2. Dibujos con el texto cortado por el borde
- **Belting** con 1 o 2 ascensores: el dibujo medía 198/348 de ancho y su título pide ~350.
  Ahora mide 470 como mínimo, con las columnas centradas, y el nombre de la obra va en su
  propia línea (a la derecha del título se pisaba con él hasta con 3).
- **Rieles, Caso 1** con 1 ascensor: la leyenda perdía el «)» final. Va en dos líneas.
⚠️ El detector de v533 estimaba el ancho (0,52 × tamaño por carácter) y daba por cortado lo
que cabía. Ahora mide con la fuente REAL (Arial, con PIL) y da exactamente lo que se vio en
producción: la leyenda se salía 3 px. 91 dibujos medidos, con y sin nombre de obra.

### 3. El cronómetro del fichaje, cortado en una columna estrecha
En una columna de 204 px (tableta, o PC con el menú abierto) rótulo y reloj pedían 225 y el
reloj salía sin los segundos. Ahora, si no caben, el reloj baja a su línea — y sin los
márgenes del documento las dos líneas caben en los mismos 52 px. Medido en el navegador de
producción con el HTML viejo y el nuevo: 225 → 171 de 204; con sitio, se ve igual que antes.

### 4. El VALOR de las métricas se cortaba con «…»
«+0.0…» por «+0.0 mm» en el resumen del Survey, «30/09/2…» en el cronograma: cinco en una
pantalla. La etiqueta ya se había arreglado en v335; el valor es peor, porque un número
cortado en obra alguien lo completa de memoria. El recorte lo pone el contenedor de markdown
de DENTRO del valor (medido en producción antes de escribir el CSS): ahora parte en dos
líneas.

### 5. Restos en español en una pantalla en inglés
«1 fuera» (desplegable de soluciones), «Matriz: 3 niveles», «Piso 1», y «Elevador 1» en las
tablas de Rieles y Plomada. Tres eran trozos de f-string, invisibles para las redes de i18n.
⚠️ En la tabla del Caso 2 de Rieles «Elevador N» es la CLAVE de la columna: se le cambia la
etiqueta, no el nombre (v450) — y la batería incluye el arreglo tentador de renombrarla.

### 6. La matriz del Survey, con seis decimales
Un Styler sin `format` manda cada número como «76.000000»: la matriz ajustada no cabía y
había que desplazarla de lado para leer un milímetro. Las tres tablas coloreadas fijan un
decimal.

### Anotado, sin tocar (decisiones del usuario)
- **Pasar de «sin obra» a una obra cuenta como cambio**: quien teclea un survey sin fichar,
  ficha y vuelve, lo pierde — igual que antes de esta versión. Conservarlo ahí es cómodo,
  pero deja datos de un cálculo suelto bajo el nombre de una obra.
- **Cambiar de obra DENTRO de una herramienta no recarga el plano** (viene de v137): los
  campos ya rellenos se quedan con los de la obra anterior. Arreglarlo choca con «Duplicate
  for the next lift», que cuenta con que se queden.
- **Al cerrar sesión solo se borra la identidad**: los resultados de las herramientas se
  quedan en la pestaña, y otra cuenta que entre en esa misma pestaña sin recargar los ve.
- **Los dibujos tienen alto fijo**: en una pantalla estrecha el dibujo encoge y debajo queda
  un hueco en blanco (hasta ~390 px en el cronograma). `st.iframe` sabe medir el contenido,
  pero cambia los 19 dibujos y no se puede probar en la app de Android desde aquí.

__PROD__ · 61 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v534 | **Lo tecleado ya no se pierde al salir de una herramienta.** Survey real EN "
        "PRODUCCIÓN (23 parámetros y 3 pisos a mano): un clic en «Rails» y otro de vuelta, y "
        "los parámetros estaban a cero y la matriz cortada a 2 filas. Streamlit borra el valor "
        "de un widget que una pasada no pinta, y `survey_ui` los reasignaba DENTRO de su "
        "pantalla. Ahora `core/estado_vivo` lo hace desde `app.py` en cada pasada, para las 5 "
        "herramientas y con lista cerrada (a un botón no se le puede asignar la clave). ⚠️ "
        "Releyendo el arreglo con la suite ya en verde: ese borrado era también lo único que "
        "impedía que el plano de la obra A se quedara bajo el nombre de la B (`aplicar` solo "
        "rellena lo vacío) — lo conservado es de UNA obra, y al volver con otra se olvida. ⚠️ "
        "Y «reabrir un cálculo» tumbaba la pantalla: la foto de las entradas guardaba el "
        "BOTÓN. Además: el título de Belting y la leyenda de Rieles ya no se cortan (⚠️ el detector "
        "mide ahora con la fuente REAL y da el mismo corte que producción); el cronómetro no "
        "se corta en columna estrecha; el valor de las métricas parte en dos líneas en vez de "
        "«+0.0…»; cuatro restos en español; y la matriz del Survey con un decimal, no seis. "
        "__PROD__ · __BATERIA__ · __SUITE__ |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v533 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v533 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
N_VIEJA = "*Última puesta al día del estado de hecho: 30/09/2026 (v515-v533).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 30/09/2026 (v515-v534).*"
E_VIEJA = "├── core/\n"
E_NUEVA = ("├── core/\n"
           "│   ├── estado_vivo.py      # pasada(): las entradas de las 5 herramientas sobreviven a "
           "cambiar de sección, mientras sea la MISMA obra (v534). Lista CERRADA\n")


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v534.py "<suite>" "<bateria>" "<produccion>"')
for _k, _v in (("__BATERIA__", BATERIA), ("__SUITE__", SUITE), ("__PROD__", PROD)):
    SECCION = SECCION.replace(_k, _v)
    FILA = FILA.replace(_k, _v)

h = io.open(HIST, encoding="utf-8").read()
unica(h, A_HIST, "cabecera", "HISTORIAL.md")
unica(h, CAB, "tabla", "HISTORIAL.md")
unica(h, TRAS_CAB, "separador", "HISTORIAL.md")
c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
unica(c, E_VIEJA, "estructura", "CLAUDE.md")
n = io.open(NEG, encoding="utf-8").read()
unica(n, N_VIEJA, "marcador", "NEGOCIO.md")

h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v534 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v534 + fila + cabecera")

c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v534 = actual)")
c = c.replace(CAB, CAB + FILA)
c = c.replace(E_VIEJA, E_NUEVA)
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
print("CLAUDE.md: fila v534 + estado_vivo en la estructura · se cayo %s · %d bytes"
      % (vieja.strip(), len(c.encode("utf-8"))))

escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v534")
