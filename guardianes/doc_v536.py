# -*- coding: utf-8 -*-
"""Documenta v536 — un despliegue ya no puede correr con los módulos viejos en memoria."""
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

SECCION = """## UN DESPLIEGUE YA NO PUEDE CORRER CON LOS MÓDULOS VIEJOS (v536)

### ⚠️ Lo que pasó al desplegar v535 (06/10/2026)
La app entera cayó en producción: `AttributeError` en `app.py` línea 133, para cualquiera con
sesión. El Cloud vuelve a ejecutar `app.py` en cada pasada, pero los `core.*` ya importados
se quedan en memoria: el `app.py` de v535 llamó a `estado_vivo.de_la_cuenta` —nueva— sobre el
`estado_vivo` de v534. CLAUDE.md lo tenía anotado desde hace tiempo como «si el chip sigue
diciendo la versión vieja: Settings → Reboot app»; mientras los cambios cabían en módulos
viejos, solo se veía un chip desfasado. Esta vez `app.py` dependía de una función nueva y
la app no arrancaba.

### La cura
`app.py`, antes de importar nada de la app: si la versión del DISCO (`VERSION`) no es
aquella con la que se importaron los módulos (`core._VERSION_CARGADA`), descarta TODOS los
`core.*` y `extractors.*` de `sys.modules` y los vuelve a importar en esa misma pasada.
Misma versión → no se toca nada. Un proceso sin marca (el de v535, el que estaba caído)
cuenta como «distinta», así que el propio despliegue de v536 lo levantó sin reiniciar.

⚠️ Lo que NO arregla: las sesiones que estén A MITAD de una pasada siguen con los módulos que
tenían hasta su pasada siguiente (no hay forma limpia de cambiarles el código en vuelo).

__PROD__ · 7 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v536 | **Un despliegue ya no puede correr con los módulos viejos en memoria.** ⚠️ Al "
        "desplegar v535 la app entera CAYÓ (`AttributeError` en `app.py`): el `app.py` nuevo "
        "llamó a una función nueva de `estado_vivo` con el módulo de v534 aún cargado — lo que "
        "CLAUDE.md anotaba como «Reboot app si el chip sigue viejo», esta vez con la app caída. "
        "Ahora `app.py`, antes de importar nada, compara la versión del disco con la de los "
        "módulos cargados y, si no coinciden, los descarta y reimporta. __PROD__ · "
        "__BATERIA__ · __SUITE__ |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v535 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v535 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
N_VIEJA = "*Última puesta al día del estado de hecho: 06/10/2026 (v515-v535).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 06/10/2026 (v515-v536).*"
R_VIEJA = ("⚠️ **Streamlit no siempre recarga los módulos al desplegar.** Si el chip del topbar sigue\n"
           "diciendo la versión vieja mientras la cabecera dice la nueva, el proceso está sirviendo\n"
           "los `core.*` de antes: **Settings → Reboot app**. El chip lee la versión AL IMPORTAR\n"
           "justo para delatar esto (ver la nota en `home_ui._VERSION`).\n")
R_NUEVA = ("⚠️ **Streamlit NO recarga los `core.*` al desplegar**: el `app.py` nuevo corría con los\n"
           "módulos viejos en memoria, y en v535 eso TUMBÓ la app (`AttributeError`). Desde v536\n"
           "`app.py`, antes de importar nada de la app, compara `VERSION` con `core._VERSION_CARGADA`\n"
           "y, si no coinciden, descarta todos los `core.*`/`extractors.*` y los reimporta en esa\n"
           "pasada. Si aun así el chip del topbar dijera la versión vieja: **Settings → Reboot app**\n"
           "(el chip lee la versión AL IMPORTAR justo para delatarlo, `home_ui._VERSION`).\n")


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v536.py "<suite>" "<bateria>" "<produccion>"')
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
unica(c, R_VIEJA, "recarga", "CLAUDE.md")
n = io.open(NEG, encoding="utf-8").read()
unica(n, N_VIEJA, "marcador", "NEGOCIO.md")

h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v536 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v536 + fila + cabecera")

c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v536 = actual)")
c = c.replace(CAB, CAB + FILA)
c = c.replace(R_VIEJA, R_NUEVA)
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
print("CLAUDE.md: fila v536 + recarga al desplegar · se cayo %s · %d bytes"
      % (vieja.strip(), len(c.encode("utf-8"))))

escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v536")
