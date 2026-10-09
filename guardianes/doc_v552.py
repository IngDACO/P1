# -*- coding: utf-8 -*-
"""Documenta v552 — la ficha abierta desde el Radar se ve donde se tocó."""
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

SECCION = """## LA FICHA ABIERTA DESDE EL RADAR SE VE DONDE SE TOCÓ (v552)

Verificando v551 en producción: tocar una línea del Radar abría la ficha rápida ARRIBA del
Panel. El Radar está debajo del tablero, así que con la vista donde se toca la ficha quedaba
373 px por encima de la pantalla y el clic parecía no hacer nada (decisión del usuario: «Dale»).

Ahora la ficha abierta desde una línea se pinta DEBAJO de esa línea (`_panel_ficha_en` guarda
su key); la misma línea otra vez la cierra. Si la lista cambió entre pasadas y esa key ya es
de otra persona, o ya no existe, o el Radar se quedó vacío, la ficha va al final del Radar —
nunca a ninguna parte. Con el Radar cerrado, o tocando un nombre del tablero, sale arriba
como siempre. La posición se comprueba recorriendo el árbol de AppTest en orden, con la ficha
REAL (su ✕ también olvida de dónde venía).

__PROD__ · 21 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v552 | **La ficha abierta desde el Radar se ve donde se tocó.** Visto verificando v551: "
        "tocar una línea del Radar abría la ficha arriba del Panel, 373 px por encima de la vista "
        "(el clic parecía no hacer nada). Ahora se pinta bajo esa línea, la misma línea la cierra, "
        "y si la línea cambió o desapareció va al final del Radar. __PROD__ · __BATERIA__ · "
        "__SUITE__ |" + chr(10))

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v551 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v551 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
N_VIEJA = "*Última puesta al día del estado de hecho: 09/10/2026 (v515-v551).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 09/10/2026 (v515-v552).*"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v552.py "<suite>" "<bateria>" "<produccion>"')
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
h = h.replace(A_HIST, "## Versiones desplegadas (v552 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v552 + fila + cabecera")

c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v552 = actual)")
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
print("CLAUDE.md: fila v552 · se cayo %s · %d bytes" % (vieja.strip(), len(c.encode("utf-8"))))

escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v552")
