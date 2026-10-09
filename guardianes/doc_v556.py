# -*- coding: utf-8 -*-
"""Documenta v556 — Time fixes (bandeja del admin), probada acción por acción."""
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

SECCION = """## TIME FIXES (BANDEJA DEL ADMIN), PROBADA ACCIÓN POR ACCIÓN (v556)

Recorrido en producción (Planning → Time fixes, decisión del usuario: «Dale») sobre las
tres correcciones de prueba del propio admin (COR-0001..0003, de v546). Aprobar
funcionaba, y revertir respetaba la regla anti-solapes de v546. Arreglado:

- ⚠️ **Dos correcciones sobre el MISMO fichaje.** COR-0001 pasó una entrada de 18:27 a
  18:00 y COR-0002 la devolvió a 18:27: «Revert» en COR-0001 daba «That time entry no
  longer exists», y «Approve» habría confirmado un «now 18:00» falso. Ahora
  `correcciones.sustituida_por` la detecta (misma persona, tipo y campo, y la posterior
  parte de la hora que dejó esta) y la tarjeta solo ofrece «Close as superseded»
  (estado nuevo `superseded`, `cerrar_sustituida`, sin tocar el fichaje).
- ⚠️ **Sin salida cuando revertir choca.** Revertir COR-0002 lo rechazaba la regla de
  v546 («overlaps your workday entry… Pick a time outside it») y no había dónde elegir
  otra hora: «Set the right time» solo existía en los cierres olvidados. Ahora en TODAS,
  y el aviso de solape, neutro («the workday entry»): lo lee también el admin.
- ⚠️ **La persona no se enteraba** de que su hora cambiaba (y con ella lo que cobra) →
  aviso al revertir o fijar la hora, en inglés; aprobar no avisa (no cambia nada).
- El DÍA del fichaje en la tarjeta y en el historial (columna «Día» → «Day» en
  `tabla`); «Asked on» y la fecha de revisión en dd/mm/aaaa; el tipo legible («workday»
  / «project»); el revisor por su NOMBRE; lo más antiguo primero; tarjetas activas.
- Acción DIFERIDA (trampa 37) y aislamiento por grupo (`_de_grupo`).

Guardianes reanclados con su razón: `verif_v461` (las tarjetas se movieron a `_kpis`).
`superseded` entra en `i18n.VALORES` («sustituida»), lo exigió `verif_v463`.

__PROD__ · 36 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v556 | **Time fixes, probada acción por acción.** ⚠️ Dos correcciones sobre el "
        "mismo fichaje dejaban la vieja sin salida («no longer exists») → «superseded». "
        "⚠️ Revertir que choca no tenía salida → «Set the right time» en todas y aviso de "
        "solape neutro. ⚠️ La persona no se enteraba → aviso al revertir o fijar. Día del "
        "fichaje, dd/mm, antiguo primero, tarjetas activas, acción diferida. "
        "__PROD__ · __BATERIA__ · __SUITE__ |" + chr(10))

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v555 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v555 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
N_VIEJA = "*Última puesta al día del estado de hecho: 09/10/2026 (v515-v555).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 09/10/2026 (v515-v556).*"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v556.py "<suite>" "<bateria>" "<produccion>"')
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
h = h.replace(A_HIST, "## Versiones desplegadas (v556 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v556 + fila + cabecera")

c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v556 = actual)")
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
print("CLAUDE.md: fila v556 · se cayo %s · %d bytes" % (vieja.strip(), len(c.encode("utf-8"))))

escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v556")
