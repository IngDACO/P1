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
"""Inserta la sección y la fila de v447 en CLAUDE.md (por fichero, no por shell)."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\diego\P1\CLAUDE.md"
D = (r"C:\Users\diego\AppData\Local\Temp\claude\C--Users-diego"
     r"\1734b676-4bc1-41b7-b6b7-689294f44640\scratchpad\doc_v447.md")

FILA = (
    "| v447 | **F5c: los 14 módulos de backend que quedaban** — con esto el backend "
    "no tiene un solo mensaje en español. ⚠️ Aquí lo peligroso no fue traducir sino "
    "**RENOMBRAR**: `pre_i18n` marcó 25 funciones con `t`/`d` como variable, y "
    "renombrar es DOS pasos. El que se me escapó, en `payroll.neto`, era "
    "`elif t == \"deduccion\"` — con `t` ya importado como la función de idioma **no "
    "da error**: la comparación sale siempre False y **las deducciones dejan de "
    "restarse del neto a pagar**. Un fallo de dinero, silencioso, con `compileall` e "
    "imports en verde; lo encontró preguntarle al AST por todos los `Name` llamados "
    "`t` tras cada renombrado. ⚠️ Y me tapé a mí mismo dos veces más: en `manuals` "
    "renombré la variable del bucle a `_tok`, **que ya era el TOKENIZADOR del "
    "módulo** (shadowing dentro del arreglo del shadowing), y el **`t()` congelado al "
    "importar** salió otras dos veces (`plan_data.USA`, `toolruns.HERRAMIENTAS`) — "
    "cuatro en tres versiones, las cuatro cazadas por el guardián de v445. ⚠️ Y la "
    "foto de 261 líneas que prueba que **ningún número se movió** dio primero "
    "«IDÉNTICAS» comparando **dos ficheros vacíos** (el script fallaba con el stderr "
    "silenciado): el paso en vacío dentro de la propia comprobación. 7 roturas "
    "probadas — una solo tras integrar el chequeo de importes, que vivía aparte: "
    "*un chequeo que no está en la suite no protege nada* |\n"
)

doc = io.open(D, encoding="utf-8").read().rstrip()
s = io.open(P, encoding="utf-8").read()

ancla = "## i18n F5b:"
assert ancla in s, "ancla de sección NO casa"
s = s.replace(ancla, doc + "\n\n" + ancla, 1)

old = "## Versiones desplegadas (v446 = actual)"
assert old in s, "ancla de tabla NO casa"
s = s.replace(old, "## Versiones desplegadas (v447 = actual)", 1)

f446 = "| v446 | **F5b: seis módulos de backend"
assert f446 in s, "ancla de fila v446 NO casa"
s = s.replace(f446, FILA + f446, 1)

io.open(P, "w", encoding="utf-8", newline="").write(s)

fila = [ln for ln in s.splitlines() if ln.startswith("| v447 |")]
assert len(fila) == 1, f"esperaba 1 fila v447, hay {len(fila)}"
for simbolo in ("payroll.neto", "_tok", "plan_data.USA", "compileall"):
    assert simbolo in fila[0], f"la fila perdió {simbolo!r}"
sec = re.search(r"## i18n F5c:.*?(?=\n## )", s, re.S)
assert sec, "la sección de v447 no está"
for simbolo in ("verif_v447.py", "git stash", "HERRAMIENTAS", "report.py"):
    assert simbolo in sec.group(0), f"la sección perdió {simbolo!r}"
print(f"CLAUDE.md: fila ({len(fila[0])} chars) y sección "
      f"({len(sec.group(0).splitlines())} líneas) OK")
