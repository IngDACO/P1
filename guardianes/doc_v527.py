# -*- coding: utf-8 -*-
"""Documenta v527 — el selector de obra sin el estado en el texto."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"
SUITE = sys.argv[1] if len(sys.argv) > 1 else ""
BATERIA = sys.argv[2] if len(sys.argv) > 2 else ""

SECCION = """## EL SELECTOR DE OBRA, SIN EL ESTADO EN EL TEXTO (v527)

La v526 se probó EN PRODUCCIÓN con la sesión de campo (`campo000`, PRJ-0015), tras el
Reboot que pedía el chip (`v525` con la cabecera en `v526`): se desmarcaron en «Progress»
las dos actividades acreditadas desde el parte, la obra volvió de «In progress» a
«Planned» y **siguió elegida** — el caso exacto que antes la perdía. La hoja real quedó con
la obra a 0% (créditos a 0, el parte revisado con su registro).

### ⚠️ Lo que quedaba, y que ningún test podía ver
Con el ID guardado la selección se conservaba, pero el desplegable CERRADO no repinta su
texto mientras no cambie la obra elegida: decía «PRJ-0015 — In progress» con la tarjeta
de debajo en «Planned». Abierto, la lista sí decía «— Planned». Es del componente del
navegador (el `react-aria` de Streamlit), así que AppTest —que no pinta nada— no lo ve.
Decisión del usuario: **quitar el estado de la etiqueta** («Nombre (PRJ-0015)»); el estado
ya está en la tarjeta de justo debajo. Un valor guardado con la etiqueta vieja se sigue
rescatando por su ID.

`verif_v526` actualizado con la razón escrita: afirma el principio —el texto del
desplegable no depende del estado, y es el MISMO antes y después de cambiarlo—, no la
forma. `romper_v526` gana la rotura «el estado vuelve a la etiqueta», y la que devuelve el
código exacto de v525 se re-ancló en la línea nueva.

### Anotado, sin tocar
Al desmarcar todo, las etapas 7 y 11 conservan su «inicio real 26/09» con 0%: la app nunca
ha borrado la fecha de inicio al volver a 0 (tampoco antes de v525), y no mueve la curva.

15 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v527 | **El selector de obra, sin el estado en el texto.** La v526 probada EN "
        "PRODUCCIÓN: desmarcar lo acreditado devolvió la obra a «Planned» y **siguió elegida**. "
        "⚠️ Quedaba que el desplegable CERRADO no repinta su texto mientras no cambie la obra: "
        "decía «— In progress» con la tarjeta en «Planned» — del navegador, invisible para "
        "AppTest. Decisión del usuario: la etiqueta pasa a «Nombre (PRJ-…)»; el estado ya está "
        "en la tarjeta. `verif_v526` afirma el principio (el texto no depende del estado). "
        "15 comprobaciones · __BATERIA__ · __SUITE__ |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v526 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v526 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA):
    raise SystemExit('faltan los resultados: doc_v527.py "<suite>" "<bateria>"')
for _k, _v in (("__BATERIA__", BATERIA), ("__SUITE__", SUITE)):
    SECCION = SECCION.replace(_k, _v)
    FILA = FILA.replace(_k, _v)

h = io.open(HIST, encoding="utf-8").read()
unica(h, A_HIST, "cabecera", "HISTORIAL.md")
unica(h, CAB, "tabla", "HISTORIAL.md")
unica(h, TRAS_CAB, "separador", "HISTORIAL.md")
h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v527 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v527 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v527 = actual)")
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
print("CLAUDE.md: fila v527 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
