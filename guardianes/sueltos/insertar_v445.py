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
"""Inserta la sección y la fila de v445 en CLAUDE.md (por fichero, no por shell)."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\diego\P1\CLAUDE.md"
D = (r"C:\Users\diego\AppData\Local\Temp\claude\C--Users-diego"
     r"\1734b676-4bc1-41b7-b6b7-689294f44640\scratchpad\doc_v445.md")

FILA = (
    "| v445 | **F5a: los mensajes de BACKEND que la interfaz pinta** — empieza la "
    "última fase. Aquí no vale la red de POSICIÓN (no hay llamadas a `st.*`): decide "
    "el **DESTINO** de la cadena — se traduce lo que la función **DEVUELVE** (la UI "
    "lo pinta con `flash`), y ⚠️ **NO** los mensajes de `logger` ni los **nombres de "
    "columna que viajan en el mismo `return`** (`\"Usuario\"`, `\"Nombre\"`), que son "
    "el DATO del libro. Se empieza por `auth.py` y `timeclock.py` (42 mensajes) "
    "porque son los que más se ven: cada login y cada jornada pasan por ahí. "
    "⚠️ **El orden**: la local `t` de `auth._session_active` se renombró ANTES de "
    "traducir (pre_i18n), y en `timeclock` solo entra `t` porque `d` ya es variable "
    "en tres funciones. ⚠️ **Correr el mismo parche dos veces duplicó un import** en "
    "`timeclock`, y en `auth` el ancla era ambigua, así que **el import no se aplicó "
    "mientras las llamadas `t()` sí** — un `NameError` esperando en cada login, "
    "cazado por el chequeo de importes de v443. ⚠️ Y **tres «fallos» del smoke eran "
    "del test**: `verify_login` devuelve un dict y no una tupla, `_segmentos_dia` "
    "recibe un datetime y no una cadena, y la validación de campos obligatorios vive "
    "en `auth_ui` — regla v135 tres veces en un script. 6 roturas probadas; una solo "
    "tras corregir el guardián, que miraba `'\"Usuario\"' in fuente` cuando esa "
    "cadena aparece en medio módulo |\n"
)

doc = io.open(D, encoding="utf-8").read().rstrip()
s = io.open(P, encoding="utf-8").read()

ancla = "## i18n: las CABECERAS DE TABLA"
assert ancla in s, "ancla de sección NO casa"
s = s.replace(ancla, doc + "\n\n" + ancla, 1)

old = "## Versiones desplegadas (v444 = actual)"
assert old in s, "ancla de tabla NO casa"
s = s.replace(old, "## Versiones desplegadas (v445 = actual)", 1)

f444 = "| v444 | **Las CABECERAS DE TABLA"
assert f444 in s, "ancla de fila v444 NO casa"
s = s.replace(f444, FILA + f444, 1)

io.open(P, "w", encoding="utf-8", newline="").write(s)

fila = [ln for ln in s.splitlines() if ln.startswith("| v445 |")]
assert len(fila) == 1, f"esperaba 1 fila v445, hay {len(fila)}"
for simbolo in ("auth._session_active", "timeclock", "verify_login", "pre_i18n"):
    assert simbolo in fila[0], f"la fila perdió {simbolo!r}"
sec = re.search(r"## i18n F5a:.*?(?=\n## )", s, re.S)
assert sec, "la sección de v445 no está"
for simbolo in ("verif_v445.py", "medir_f5.py", "LOGIN_HEADERS", "_segmentos_dia"):
    assert simbolo in sec.group(0), f"la sección perdió {simbolo!r}"
print(f"CLAUDE.md: fila ({len(fila[0])} chars) y sección "
      f"({len(sec.group(0).splitlines())} líneas) OK")
