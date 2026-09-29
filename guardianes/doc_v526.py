# -*- coding: utf-8 -*-
"""Documenta v526 — el selector de obra del campo guarda el ID (y dos detalles)."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"
SUITE = sys.argv[1] if len(sys.argv) > 1 else ""
BATERIA = sys.argv[2] if len(sys.argv) > 2 else ""

SECCION = """## EL SELECTOR DE OBRA DEL CAMPO GUARDA EL ID (v526)

El usuario pidió probar v523-v525 y **la prueba se hizo EN PRODUCCIÓN**, con la sesión de
campo que dejó abierta (`campo000`, PRJ-0015): un parte con fecha del 26 escrito el 29, la
tarjeta, tres marcas de dos actividades («Confirm the 2 ticked») y confirmar. En la hoja
real, leído por el camino de solo lectura: créditos con origen `log`, `WorkDate` del 26,
etapas 7 y 11 con inicio el **26/09** (no el 29), registro de lo ofrecido (14) y lo
marcado (2), obra de 0% a 2,1%. Todo lo de v523-v525 funcionó.

### ⚠️ El fallo que salió: al confirmar, el trabajador perdía la obra
El desplegable «Assigned project» guardaba la ETIQUETA —`«Nombre (PRJ-0015) — Planned»`—, y
la etiqueta lleva el ESTADO. Al acreditar lo primero la obra pasa a «In progress», la
etiqueta guardada deja de existir y Streamlit tira la selección: se volvía a «— choose a
project —». Pasaba igual al marcar a mano en «Progress» y al completar una obra; no era de
v523-v525, pero confirmar un parte lo hacía pasar en CADA primera confirmación. Ahora el
desplegable guarda el **ID** (que no cambia nunca, regla «el ID es la identidad») y enseña la
etiqueta con `format_func`. Un valor viejo (la etiqueta) se rescata por su ID; una obra que
ya no es suya vuelve a «elegir» en vez de quedar fantasma. Solo un sitio escribía esa clave.

### Y dos detalles vistos en la misma prueba
- Un parte de OTRO día enseñaba cuándo se escribió con segundos («2026-09-29 16:35:28").
- La caja del asistente del campo decía **«Escribe tu pregunta…»**: en español y sin `t()`.
  Ningún barrido de i18n miraba `st.chat_input` — la trampa nº30 otra vez. Buscados sus
  gemelos (`chat_input`/`placeholder=` con literal): solo quedan dos URLs de ejemplo.

### Los guardianes
`verif_v526` EJECUTA la pantalla del campo con AppTest y reproduce el fallo: elige una obra,
le cambia el estado a «In progress» y luego a «Completed», y la obra tiene que seguir
elegida. ⚠️ `romper_v526` devuelve el selector al código **EXACTO** de v525 (cuatro trozos a
la vez) y el guardián lo caza: prueba de que ve el fallo real, no una variante.
⚠️ Y el trinquete de v524 hizo su trabajo: la batería nueva nació con cada rotura como LISTA
de cambios, `check_anclas_roturas` no sabía leerla y **se puso en rojo** en vez de callarse.
Ahora lee listas: **621** anclas revisadas (579 antes), y las 33 de `romper_v488/v490`
pasan a vigilarse (ilegibles 86 → 53, ninguna muerta escondida esta vez).

15 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v526 | **El selector de obra del campo guarda el ID.** Probado v523-v525 EN PRODUCCIÓN "
        "(sesión de campo, PRJ-0015): parte del 26 escrito el 29 → créditos con `WorkDate` 26 y "
        "etapas con inicio el 26/09; todo funcionó. ⚠️ Salió un fallo: al confirmar, el "
        "desplegable volvía a «choose a project» porque guardaba la ETIQUETA, que lleva el "
        "estado, y la obra pasaba a «In progress». Ahora guarda el ID y enseña la etiqueta. Y "
        "dos detalles: segundos en la hora de un parte de otro día, y «Escribe tu pregunta…» en "
        "español sin `t()`. `romper_v526` devuelve el código EXACTO de v525 y se caza; el "
        "trinquete de v524 paró la batería nueva por ilegible → el chequeo lee listas (621 "
        "anclas). 15 comprobaciones · __BATERIA__ · __SUITE__ |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v525 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v525 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA):
    raise SystemExit('faltan los resultados: doc_v526.py "<suite>" "<bateria>"')
for _k, _v in (("__BATERIA__", BATERIA), ("__SUITE__", SUITE)):
    SECCION = SECCION.replace(_k, _v)
    FILA = FILA.replace(_k, _v)

h = io.open(HIST, encoding="utf-8").read()
unica(h, A_HIST, "cabecera", "HISTORIAL.md")
unica(h, CAB, "tabla", "HISTORIAL.md")
unica(h, TRAS_CAB, "separador", "HISTORIAL.md")
h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v526 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v526 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v526 = actual)")
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
print("CLAUDE.md: fila v526 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
