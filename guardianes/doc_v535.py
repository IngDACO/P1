# -*- coding: utf-8 -*-
"""Documenta v535 — lo que quedaba pendiente de v534 («no dejes nada pendiente»)."""
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

SECCION = """## LO QUE QUEDABA PENDIENTE DE v534 (v535)

Al cerrar v534 quedaron cuatro cosas anotadas «para el usuario». Su respuesta fue «no dejes
nada pendiente».

### ⚠️ 1. Cambiar de obra SIN salir de la herramienta
v534 hizo que lo conservado fuera de UNA obra, pero solo al VOLVER a la herramienta. Sin
salir de ella también se cambia de obra: el campo ficha en otra desde el menú lateral sin
dejar Rieles, y el admin cambia el selector de obra. Ahí no se olvidaba nada y
`plan_ui.aplicar` solo rellena lo vacío: **el LFKK de la obra X seguía bajo el nombre de la
Y**. Venía de v137; v534 no lo empeoró, pero era el mismo peligro por otra puerta.
→ `estado_vivo.al_pintar` recuerda la última obra REAL de cada herramienta (también si en
medio hubo «ninguna»): de X a Y, lo tecleado para X se olvida y `aplicar` deja que el plano
de Y PISE lo que haya (aviso `_pl_forzar`, que `selector_proyecto` escribe siempre y
`aplicar` consume). ⚠️ Salvo el Survey: «Duplicate for the next lift» conserva a propósito
lo medido para el siguiente ascensor, así que ahí solo manda el plano en lo que el plano
trae (BS, NS…) y lo medido a mano (BSR…) se queda.

### ⚠️ 2. Los datos de trabajo son de UNA cuenta
Cerrar sesión solo quitaba `auth`: resultados, lo tecleado y el historial del asistente se
quedaban en la pestaña, y otra cuenta que entrara en ella sin recargar —otra empresa
cliente— los veía. → `estado_vivo.de_la_cuenta`, en `app.py` tras el login: si entra OTRA
cuenta, se borra todo menos la infraestructura (identidad, idioma, gestor de la cookie y sus
componentes, mensajes pendientes) y se vuelve a poner el estado base. La MISMA cuenta que
vuelve —tras salir o tras una expulsión de la sesión única— encuentra lo suyo. Se eligió
esto y no «borrar al salir» porque cubre también la expulsión, y no hace perder lo tecleado
a quien solo volvía a entrar.

### 3. Los dibujos miden lo que mide su contenido
Con alto fijo, en pantalla estrecha el SVG encogía y debajo quedaba un hueco en blanco
(medido en producción: 379 px de cronograma en un recuadro de 648; 256 de isométrica en
650). `incrustar.dibujo` usa ahora `st.iframe(height="content")`: Streamlit añade al
documento un script que mide el cuerpo y avisa a la página al cargar, al cambiar el DOM y
al cambiar de ancho. Siguen fijos los dos cronómetros (alto exacto, v534) y la planta por
pisos con scroll. ⚠️ Lo que NO hace: si la ventana se ESTRECHA después de pintar, el
recuadro no encoge (la medida usa también el alto de la ventana del recuadro) — igual que
antes, sin empeorar.

### ⚠️ 4. Lo que destapó el guardián: el nº de paradas del plano no se aplicaba
El Survey nace con NS = 2 («mínimo neutro; el NS real sale del plano»), y `aplicar` solo
rellena lo vacío: el 2 no es vacío, así que el NS del plano **no se aplicaba nunca** al
elegir obra. Funcionaba por ACCIDENTE: Streamlit borraba el campo al salir de la
herramienta y al volver estaba vacío — justo lo que v534 dejó de hacer. → `aplicar(...,
neutros={"ns": 2})`, UNA vez por obra (si el 2 contara siempre como vacío, quien pusiera 2 a
mano lo vería volver al del plano en cada pasada); «Start a new survey» lo rearma.

### 5. La suite corre con el Python del Cloud (3.12)
Con permiso del usuario (06/10/2026) se instaló Python 3.12.10 (`winget`, instalador de
python.org, por usuario) con las librerías de `requirements.txt`: Streamlit 1.64.0, pandas
2.2.3, numpy 1.26.4, pyarrow 17, Pillow 11.3 — lo que resuelve el Cloud con esos topes.
`run_suite.py` lanza ahora cada guardián con `py -3.12` aunque se arranque con el 3.14, y lo
dice en la primera y en la última línea; si el 3.12 faltara, lo avisa en vez de callarlo.
Era la trampa nº11 (lo local no es lo que corre) aplicada al intérprete.

### Decidido (era una pregunta abierta)
**Pasar de «sin obra» a una obra AL VOLVER cuenta como cambio**, como siempre: guardar un
cálculo de una herramienta no exige fichar (el campo elige la obra al guardar), así que no
se pierde nada por fichar; y conservarlo dejaría datos de un cálculo suelto bajo el nombre
de una obra.

__PROD__ · 26 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v535 | **Lo que quedaba pendiente de v534** («no dejes nada pendiente»). ⚠️ Cambiar "
        "de obra SIN salir de la herramienta (el campo ficha en otra desde el menú lateral; el "
        "admin cambia el selector) dejaba el LFKK de la obra anterior bajo el nombre de la "
        "nueva: ahora manda el plano de la nueva y lo tecleado se olvida (en el Survey solo "
        "manda el plano; lo medido se queda, por «Duplicate»). ⚠️ Los datos de trabajo son de "
        "UNA cuenta: otra cuenta en la misma pestaña ya no ve los resultados ni el chat de la "
        "anterior. Los dibujos miden su contenido (sin hueco en blanco en pantalla estrecha). "
        "⚠️ El guardián destapó que el NS del plano no se aplicaba nunca (el 2 neutro no es "
        "«vacío»; funcionaba por accidente con el borrado que v534 quitó). Y la suite corre "
        "ya con el Python del Cloud (3.12, instalado con permiso del usuario). __PROD__ · "
        "__BATERIA__ · __SUITE__ |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v534 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v534 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
N_VIEJA = "*Última puesta al día del estado de hecho: 30/09/2026 (v515-v534).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 06/10/2026 (v515-v535).*"
E_VIEJA = ("│   ├── estado_vivo.py      # pasada(): las entradas de las 5 herramientas sobreviven a "
           "cambiar de sección, mientras sea la MISMA obra (v534). Lista CERRADA\n")
E_NUEVA = ("│   ├── estado_vivo.py      # pasada(): las entradas de las 5 herramientas sobreviven a "
           "cambiar de sección, mientras sea la MISMA obra (v534-v535); de_la_cuenta(): los datos "
           "de trabajo son de UNA cuenta (v535). Lista CERRADA\n")


P_VIEJA = "- Un segfault en los logs = problema de dependencias/entorno, **nunca** del código Python.\n"
P_NUEVA = ("- **El local tiene el Python del Cloud (3.12.10, v535)** con las librerías de "
           "`requirements.txt` (`py -3.12`): `run_suite.py` lanza los guardianes con él aunque se "
           "arranque con el 3.14, y lo dice en la primera y la última línea. Las baterías usan el "
           "Python con que se lanzan: `py -3.12 romper_vNNN.py`.\n")


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v535.py "<suite>" "<bateria>" "<produccion>"')
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
unica(c, P_VIEJA, "entorno", "CLAUDE.md")
n = io.open(NEG, encoding="utf-8").read()
unica(n, N_VIEJA, "marcador", "NEGOCIO.md")

h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v535 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v535 + fila + cabecera")

c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v535 = actual)")
c = c.replace(CAB, CAB + FILA)
c = c.replace(E_VIEJA, E_NUEVA)
c = c.replace(P_VIEJA, P_NUEVA + P_VIEJA)
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
print("CLAUDE.md: fila v535 · se cayo %s · %d bytes" % (vieja.strip(), len(c.encode("utf-8"))))

escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v535")
