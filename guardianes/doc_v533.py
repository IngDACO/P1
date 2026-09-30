# -*- coding: utf-8 -*-
"""Documenta v533 — lo que destapó cerrar los pendientes en producción."""
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

SECCION = """## LO QUE DESTAPÓ CERRAR LOS PENDIENTES EN PRODUCCIÓN (v533)

El usuario pidió no dejar nada pendiente. Lo que quedaba por ver EN PRODUCCIÓN se probó, y
probarlo encontró un fallo que la hoja de mentira no podía enseñar.

### ✅ La expulsión de la sesión única, probada en producción (pendiente desde v528)
Sin contraseñas: se cambió el `SessionToken` de la cuenta de prueba en `Login` —lo que deja
en la hoja otro dispositivo al tomar la cuenta—, con el token original guardado aparte y sin
imprimirlo. Control primero: con el token bueno, dos pasadas y sigue dentro (y en la hoja, el
heartbeat en segundo plano marcó vida 13 s antes). Con el token desplazado: primer clic, sigue
dentro (el heartbeat corre en su hilo); segundo clic, «Your session was closed…» y la app se
corta. Exactamente el diseño de v528.

### ⚠️ El fallo: el veredicto se quedaba guardado
Al reponer el token y recargar, la cookie restauró la sesión… y la app la expulsó otra vez AL
INSTANTE. El veredicto vive en el proceso con la clave (usuario, token), y el `False` seguía
ahí: la expulsión corta la pasada antes de lanzar otro heartbeat, así que nunca se volvía a
preguntar a la hoja. En la vida real un token desplazado no vuelve a valer — pero una lectura
de `Login` que una vez no trajera la fila dejaría a alguien fuera con su cookie buena hasta
teclear la contraseña, y antes de v528 una recarga lo arreglaba sola.
→ `auth.heartbeat_olvidar`: se olvida al EXPULSAR y al RESTAURAR desde la cookie (se acaba de
validar contra la hoja: lo guardado es más viejo). Y un hilo que termina después de olvidar
no vuelve a meter su veredicto.

### Los dos «anotados, sin tocar»
- **La leyenda del dibujo de Buffers** se pisaba con 1-3 buffers (la nota de escala, anclada
  a la derecha en un dibujo de 460 de ancho): va en su propia línea. Medido con un detector
  de textos pisados —validado contra el código viejo: 143 y 49 px de solape, 0 con 5— que de
  paso dejó limpios Belting y Rieles.
- **Una etapa que vuelve a 0% ya no conserva su «inicio real»** (anotado en v527): es la
  gemela de «reabierta → borrar fin real». No mueve la curva S —al 0% no hay avance que
  repartir— y al volver a marcar el inicio sale otra vez del primer día de trabajo.

### Lo que NO se pudo cerrar, y por qué
- **Python 3.12 en local** (el Cloud usa 3.12; aquí solo hay 3.14): exige instalar software en
  la máquina del usuario. Queda a su decisión.
- **Los logs del Cloud de v529 en adelante**: solo los puede descargar el usuario.

__PROD__ · 21 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v533 | **Lo que destapó cerrar los pendientes en producción.** La expulsión de la "
        "sesión única, probada EN PRODUCCIÓN sin contraseñas (token de la cuenta de prueba "
        "cambiado en `Login`): expulsa al segundo clic, como se diseñó. ⚠️ Pero al reponer el "
        "token, la cookie restauraba la sesión y la app la expulsaba AL INSTANTE: el veredicto "
        "del heartbeat se quedaba guardado en el proceso. Ahora se olvida al expulsar y al "
        "restaurar. Además: la leyenda de Buffers ya no se pisa y una etapa que vuelve a 0% "
        "pierde su «inicio real». __PROD__ · __BATERIA__ · __SUITE__ |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v532 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v532 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
N_VIEJA = "*Última puesta al día del estado de hecho: 30/09/2026 (v515-v532).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 30/09/2026 (v515-v533).*"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v533.py "<suite>" "<bateria>" "<produccion>"')
for _k, _v in (("__BATERIA__", BATERIA), ("__SUITE__", SUITE), ("__PROD__", PROD)):
    SECCION = SECCION.replace(_k, _v)
    FILA = FILA.replace(_k, _v)

h = io.open(HIST, encoding="utf-8").read()
unica(h, A_HIST, "cabecera", "HISTORIAL.md")
unica(h, CAB, "tabla", "HISTORIAL.md")
unica(h, TRAS_CAB, "separador", "HISTORIAL.md")
h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v533 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v533 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v533 = actual)")
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
print("CLAUDE.md: fila v533 · se cayo %s · %d bytes" % (vieja.strip(), len(c.encode("utf-8"))))

n = io.open(NEG, encoding="utf-8").read()
unica(n, N_VIEJA, "marcador", "NEGOCIO.md")
escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v533")
