# -*- coding: utf-8 -*-
"""Documenta v537 — lo que enseñaron los logs del Cloud del 06/10/2026."""
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

SECCION = """## LO QUE ENSEÑARON LOS LOGS DEL CLOUD (v537)

El usuario bajó los logs del Cloud del 06/10/2026 (04:53-06:49 UTC). ⚠️ Solo traen el
proceso ACTUAL: el de antes de que la app se durmiera se perdió, así que los días v529-v533
ya no se pueden revisar ahí — lo verificado entonces fue en la propia app.

### ⚠️ 1. El Pre-Start entero caído (dependencia que subió sola)
Al despertar la app, el Cloud reinstaló todo y `streamlit-drawable-canvas` subió a 0.13.0:
el requirements decía `>=0.9.3,<1`. La 0.13 quita `display_toolbar` y ya no devuelve la
imagen salvo que se le pida, así que `st_canvas(...)` reventaba con `TypeError` y **el
Pre-Start —la charla de seguridad diaria del campo— no abría**.
⚠️ La suite no lo vio aunque ya corría con el Python del Cloud: en local, sin servidor, la
0.13 ni siquiera importaba y el Pre-Start caía a su plan B (iniciales) sin dar error — un
verde que no había tocado el lienzo (trampa nº1). Y el resto de paquetes del 3.12 local
coincidía con el Cloud: la única deriva era esta.
→ versión FIJA (`==0.9.3`, la probada en v383; subirla es una decisión, como Streamlit), y
`_canvas_disponible` comprueba que la función ACEPTA `_LIENZO` antes de usarla: si no,
iniciales. Las dos firmas usan los mismos parámetros. El guardián exige además que en el
Python de la suite el lienzo CARGUE (no el plan B).

### 2. Una traza de error en cada cálculo del Survey
La tabla de parámetros calculados mezclaba números y letras («L», el lado Z) y no pasaba a
Arrow; Streamlit la arreglaba solo y dejaba la traza. Ahora es texto (y las columnas CUT
OR/OL, que mezclaban «» y números).

### 3. Una traza de 30 líneas por «valor por defecto + Session State»
Las herramientas fijan sus entradas por `st.session_state` (plano, reabrir, `estado_vivo`) y
algunas además pasan `value=`: es a propósito. `global.disableWidgetStateDuplicationWarning`
en `config.toml` apaga solo ese aviso.

### Lo que confirmaron los logs
- **La caída de v535**: `AttributeError ... de_la_cuenta` tres veces, entre el despliegue de
  v535 y el de v536.
- **v536 la levantó SIN reiniciar**: después de su despliegue ya no hay `AttributeError`, y no
  hay ningún «Starting up» entre medias (un reinicio manual lo habría dejado).

__PROD__ · 13 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v537 | **Lo que enseñaron los logs del Cloud.** ⚠️ El Pre-Start entero estaba CAÍDO: al "
        "despertar la app, el Cloud reinstaló y `streamlit-drawable-canvas` subió a 0.13 (el "
        "requirements decía `<1`), que quita `display_toolbar` — `TypeError` al abrirlo. La suite "
        "no lo vio: en local la 0.13 ni importaba y el Pre-Start caía a su plan B sin error. "
        "Versión fija, y si el lienzo no acepta los parámetros, iniciales en vez de caerse. "
        "Además: dos trazas de los logs fuera (la tabla de parámetros a Arrow; el aviso de "
        "Session State). Los logs confirman que v536 levantó la caída de v535 sin reiniciar. "
        "__PROD__ · __BATERIA__ · __SUITE__ |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v536 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v536 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
N_VIEJA = "*Última puesta al día del estado de hecho: 06/10/2026 (v515-v536).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 06/10/2026 (v515-v537).*"
P_VIEJA = ("- **`requirements.txt` va PINEADO** con topes de major (pandas<2.3, numpy<2, "
           "reportlab<5, svglib<2,\n  lxml<6, pillow<12, pyarrow<18). NO volver a dejar todo `>=` "
           "sin tope.\n")
P_NUEVA = ("- **`requirements.txt` va PINEADO** con topes de major (pandas<2.3, numpy<2, "
           "reportlab<5, svglib<2,\n  lxml<6, pillow<12, pyarrow<18). NO volver a dejar todo `>=` "
           "sin tope.\n  ⚠️ **Los componentes de terceros van FIJOS (==)**, no con tope de major: "
           "`streamlit-drawable-canvas`\n  pasó de 0.9 a 0.13 dentro de `<1` y dejó el Pre-Start "
           "caído (v537). El Cloud reinstala todo cada\n  vez que la app despierta.\n")


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v537.py "<suite>" "<bateria>" "<produccion>"')
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
unica(c, P_VIEJA, "pineado", "CLAUDE.md")
n = io.open(NEG, encoding="utf-8").read()
unica(n, N_VIEJA, "marcador", "NEGOCIO.md")

h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v537 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v537 + fila + cabecera")

c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v537 = actual)")
c = c.replace(CAB, CAB + FILA)
c = c.replace(P_VIEJA, P_NUEVA)
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
print("CLAUDE.md: fila v537 + componentes fijos · se cayo %s · %d bytes"
      % (vieja.strip(), len(c.encode("utf-8"))))

escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v537")
