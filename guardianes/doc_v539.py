# -*- coding: utf-8 -*-
"""Documenta v539 — lo reabierto es de la obra del cálculo."""
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

SECCION = """## LO REABIERTO ES DE LA OBRA DEL CÁLCULO (v539)

⚠️ Fallo introducido en v535, encontrado sin la cuenta del admin: con los datos REALES de
cliente1 leídos en solo lectura (el plano de 88 walker y sus 6 cálculos guardados), se
ensayaron en local las pantallas del admin con su selector de obra — la app sin tocar la
hoja. 28 de 33 bien; los 5 fallos, el mismo caso: el admin usaba una herramienta con la
obra A, iba a 88 walker → Files → «Reopen in the tool» (todo se cargaba bien y el selector
quedaba en «no project») y elegía 88 walker en el selector, lo natural para volver a
guardarlo. La regla de v535 («de X a Y sin salir, se olvida») tomaba la última obra de la
herramienta (A) y **borraba lo medido sin aviso**: HGPR 1547 y 1785 → 0 (Belting), 2
buffers → 1, plantilla de plomada 770 → 0. Con la herramienta sin usar antes no se perdía
nada — por eso los guardianes de v535 no lo vieron. «Rebuild the project in the Survey»
tenía el mismo hueco (el plano pisaba lo reconstruido).

→ Quien carga valores dice de qué obra son: `estado_vivo.respetar(h, obra)`. El cálculo
reabierto lleva su `ProjectID`; el survey reconstruido, su proyecto. Elegir después ESA obra
ya no es un cambio; elegir otra sí (la regla de v535 sigue). Un reabrir pedido con el código
anterior (sin obra) no se olvida al elegir ninguna. El campo no cambia: su obra sale del
fichaje.

Ensayo con los datos reales tras el arreglo: 33 de 33 (selector del admin en las cuatro
herramientas con el plano de 88 walker, los 5 cálculos reabiertos y el NS = 6 del plano).

⚠️ La batería destapó un hueco del propio guardián: solo elegía «otra obra» DESPUÉS de
elegir la del cálculo, así que `respetar` sin guardar la obra pasaba (5 de 6). Ahora se
elige otra obra justo después de reabrir y de reconstruir.

__PROD__ · 16 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v539 | **Lo reabierto es de la obra del cálculo.** ⚠️ Fallo de v535, encontrado "
        "ensayando en local las pantallas del admin con los datos REALES de 88 walker (leídos "
        "en solo lectura): con la herramienta usada antes en otra obra, reabrir un cálculo y "
        "elegir su obra en el selector borraba lo medido sin aviso (HGPR 1547 → 0, 2 buffers "
        "→ 1, plantilla 770 → 0); «Rebuild the project in the Survey», igual. `respetar(h, "
        "obra)`: elegir esa obra ya no es un cambio, otra sí. Ensayo real 33/33 (antes 28/33). "
        "__PROD__ · __BATERIA__ · __SUITE__ |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v538 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v538 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
N_VIEJA = "*Última puesta al día del estado de hecho: 06/10/2026 (v515-v538).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 07/10/2026 (v515-v539).*"
E_VIEJA = ("mientras sea la MISMA obra (v534-v535); de_la_cuenta(): los datos de trabajo son "
           "de UNA cuenta (v535). Lista CERRADA")
E_NUEVA = ("mientras sea la MISMA obra (v534-v535); respetar(h, obra): lo cargado a propósito "
           "es de SU obra (v539); de_la_cuenta(): los datos de trabajo son de UNA cuenta (v535). "
           "Lista CERRADA")


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v539.py "<suite>" "<bateria>" "<produccion>"')
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
unica(c, E_VIEJA, "estado_vivo", "CLAUDE.md")
n = io.open(NEG, encoding="utf-8").read()
unica(n, N_VIEJA, "marcador", "NEGOCIO.md")

h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v539 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v539 + fila + cabecera")

c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v539 = actual)")
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
print("CLAUDE.md: fila v539 · se cayo %s · %d bytes" % (vieja.strip(), len(c.encode("utf-8"))))

escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v539")
