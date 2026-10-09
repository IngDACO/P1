# -*- coding: utf-8 -*-
"""Documenta v553 — la página va a la ficha recién abierta y el Radar se lee a la izquierda."""
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

SECCION = """## LA PÁGINA VA A LA FICHA RECIÉN ABIERTA; EL RADAR SE LEE A LA IZQUIERDA (v553)

Dos cosas vistas verificando v552 en producción (decisión del usuario: «arreglalos»):

- **La ficha recién abierta podía quedar fuera de la vista.** Con la línea del Radar al fondo
  de la página, salía bajo ella pero cortada (114 px); en una mini-app 1.64 con 10 personas,
  ENTERA por debajo (777-1000 con 768 de alto). Y con un NOMBRE del tablero, el mismo fallo
  hacia arriba: se pintaba en -472..-259, invisible. Ahora, al abrirla (Radar o tablero), se
  encola UNA vez (`_fp_ir`) un script que espera a que acabe la pasada y la trae con
  `scrollIntoView({block:'nearest'})`: lo justo, y nada si ya se ve. Medido: 381 → 603 desde
  el Radar y 667 → 195 desde el tablero, la ficha entera; en la pasada siguiente no se mueve.
  El recuadro del script va FUERA del flujo, él y su `stLayoutWrapper`: con solo el
  contenedor fuera, la ficha medía 223 px en vez de 213 (el envoltorio de 0 px seguía
  recibiendo el hueco de 9,6 px).
- **El texto de las líneas del Radar salía centrado**: en 1.64 lo centran el `div` y el
  `span` interiores del botón, no el botón. Con `flex-start` en los dos: a 13 px del borde
  (antes 84-99), las tarjetas KPI intactas.

Todo medido en una mini-app local con el Panel REAL (roster_ui) y datos inventados: el
panel del navegador había perdido la cookie y en producción no se puede entrar sin
contraseña. AppTest no ejecuta JavaScript: el guardián comprueba que el script ESTÁ cuando
debe (y solo entonces) y qué hace.

__PROD__ · 21 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v553 | **La página va a la ficha recién abierta; el Radar se lee a la izquierda.** "
        "Vistos verificando v552: la ficha abierta desde el fondo del Radar quedaba cortada (o "
        "entera por debajo) y desde un nombre del tablero, por ENCIMA de la pantalla (-472 px). "
        "Al abrirla, un script de una sola vez la trae con `block:'nearest'`; el recuadro y su "
        "envoltorio fuera del flujo. Texto del Radar a 13 px del borde (antes centrado). "
        "__PROD__ · __BATERIA__ · __SUITE__ |" + chr(10))

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v552 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v552 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
N_VIEJA = "*Última puesta al día del estado de hecho: 09/10/2026 (v515-v552).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 09/10/2026 (v515-v553).*"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v553.py "<suite>" "<bateria>" "<produccion>"')
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
n = io.open(NEG, encoding="utf-8").read()
unica(n, N_VIEJA, "marcador", "NEGOCIO.md")

h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v553 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v553 + fila + cabecera")

c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v553 = actual)")
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
print("CLAUDE.md: fila v553 · se cayo %s · %d bytes" % (vieja.strip(), len(c.encode("utf-8"))))

escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v553")
