# -*- coding: utf-8 -*-
# =====================================================================
# HISTORICO - NO SE PUEDE EJECUTAR (marcado el 20/09/2026)
#
# Apunta al scratchpad temporal de la sesion 1734b676..., que ya no existe,
# y ademas opera sobre ficheros intermedios de aquella tanda que tampoco
# existen: era una transformacion de un solo uso, ya aplicada.
#
# Se conserva como RASTRO de como se hizo aquel cambio, no como herramienta.
# Arreglarle la ruta no lo haria funcionar: lo que leia ya no esta.
# =====================================================================
"""Inserta la sección y la fila de v449 en CLAUDE.md (por fichero, no por shell)."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\diego\P1\CLAUDE.md"
D = (r"C:\Users\diego\AppData\Local\Temp\claude\C--Users-diego"
     r"\1734b676-4bc1-41b7-b6b7-689294f44640\scratchpad\doc_v449.md")

FILA = (
    "| v449 | **i18n CERRADO del todo: la navegación y las últimas etiquetas.** Al "
    "medir con las tres redes tras v448 aparecieron **32** que seguían en español, "
    "casi todas en lo más visible: los displays de `_SECCIONES`/`_SUBSECCIONES`, a "
    "medias («Projects» al lado de «Finanzas»). ⚠️ Cada entrada es **(ID, display)** y "
    "solo se toca el segundo: el ID lleva emoji porque **ES el identificador** que "
    "compara `sub ==` y usan los deep-links. ⚠️ Y faltaba el chequeo de **RAMA "
    "MUERTA para las sub-pestañas** (el de v442 solo mira opciones de widget); hubo "
    "que escribirlo **dos veces**: la primera comprobaba «el ID sigue en el fichero» "
    "y **pasaba con la rama muerta delante** (aparece dos veces: definición y "
    "comparación), y la segunda daba **dos ramas muertas inexistentes** por asumir "
    "que el del `else` es «el último de la lista» — en finanzas es el 5.º de 8 y en "
    "proyectos el PRIMERO. El invariante correcto es por SECCIÓN: un `if/elif/else` "
    "deja **exactamente uno** sin comparar. **Recuento final: 0 en interfaz y 0 en "
    "backend**; lo que queda en español es solo lo que no se puede traducir (datos, "
    "IDs, nombres de actividad, la carpeta de Drive `COPEX Activos` y la base de "
    "conocimiento del asistente), cada uno afirmado por el guardián. 6 roturas |\n"
)

doc = io.open(D, encoding="utf-8").read().rstrip()
s = io.open(P, encoding="utf-8").read()

ancla = "## i18n F5 CERRADO:"
assert ancla in s, "ancla de sección NO casa"
s = s.replace(ancla, doc + "\n\n" + ancla, 1)

old = "## Versiones desplegadas (v448 = actual)"
assert old in s, "ancla de tabla NO casa"
s = s.replace(old, "## Versiones desplegadas (v449 = actual)", 1)

f448 = "| v448 | **F5 CERRADO:"
assert f448 in s, "ancla de fila v448 NO casa"
s = s.replace(f448, FILA + f448, 1)

io.open(P, "w", encoding="utf-8", newline="").write(s)

fila = [ln for ln in s.splitlines() if ln.startswith("| v449 |")]
assert len(fila) == 1, f"esperaba 1 fila v449, hay {len(fila)}"
for simbolo in ("_SUBSECCIONES", "COPEX Activos", "if/elif/else"):
    assert simbolo in fila[0], f"la fila perdió {simbolo!r}"
sec = re.search(r"## i18n CERRADO del todo:.*?(?=\n## )", s, re.S)
assert sec, "la sección de v449 no está"
for simbolo in ("verif_v449.py", "schedule.PHASES", "chat_agent", "owner_sec"):
    assert simbolo in sec.group(0), f"la sección perdió {simbolo!r}"
print(f"CLAUDE.md: fila ({len(fila[0])} chars) y sección "
      f"({len(sec.group(0).splitlines())} líneas) OK")
