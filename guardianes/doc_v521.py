# -*- coding: utf-8 -*-
"""Documenta v521 — la tarjeta «Models» de la biblioteca cuenta modelos, no filas."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"
SUITE = sys.argv[1] if len(sys.argv) > 1 else ""

SECCION = """## LA TARJETA «MODELS» CUENTA MODELOS, NO FILAS DEL CATÁLOGO (v521)

Encontrado al mirar la biblioteca en producción después de cargarla (v520): la cabecera
decía **«Models 2»** y no hay ningún modelo. El catálogo tenía dos filas —«Schindler» y
«Sematic», las dos SIN modelo— y `resumen()` contaba `len(list_modelos())`, o sea FILAS.

Una marca sin modelo es un estado **legítimo** (`SIN_MODELO`: hay material de una marca
sin modelo concreto), así que el fallo no era del dato sino de la cuenta. Y se
contradecía con la propia pantalla: el desplegable de modelos usa `modelos_de`, que
descarta el vacío, y no ofrecía ninguno. Ahora `_num_modelos()` cuenta con el MISMO
criterio que el desplegable —pares marca·modelo con modelo escrito, sin repetidos y sin
desactivados—, así que la tarjeta y el desplegable ya no pueden decir cosas distintas.
Decisión del usuario: «dale, arregla el contador».

Hoja real: **modelos 2 → 0**, marcas 2, 750 piezas. 11 comprobaciones · **4/4 roturas +
control** · %s
""" % SUITE

FILA = ("| v521 | **La tarjeta «Models» cuenta modelos, no filas del catálogo.** Tras cargar la "
        "biblioteca decía «Models 2» con CERO modelos: el catálogo tenía «Schindler» y «Sematic» sin "
        "modelo —un estado legítimo— y `resumen()` contaba filas. ⚠️ Se contradecía con el desplegable, "
        "que ya descartaba el vacío; ahora cuentan con el MISMO criterio (sin repetidos ni "
        "desactivados) y no pueden volver a discrepar. Hoja real: **2 → 0**. 11 comprobaciones · "
        "**4/4 + control** · %s |\n" % SUITE)

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v520 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v520 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not SUITE:
    raise SystemExit("falta el resultado de la suite (primer argumento)")

h = io.open(HIST, encoding="utf-8").read()
unica(h, A_HIST, "cabecera", "HISTORIAL.md")
unica(h, CAB, "tabla", "HISTORIAL.md")
unica(h, TRAS_CAB, "separador", "HISTORIAL.md")
h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v521 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v521 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v521 = actual)")
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
print("CLAUDE.md: fila v521 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
