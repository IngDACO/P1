# -*- coding: utf-8 -*-
"""Inserta la sección y la fila de v446 en CLAUDE.md (por fichero, no por shell)."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\diego\P1\CLAUDE.md"
D = (r"C:\Users\diego\AppData\Local\Temp\claude\C--Users-diego"
     r"\1734b676-4bc1-41b7-b6b7-689294f44640\scratchpad\doc_v446.md")

FILA = (
    "| v446 | **F5b: seis módulos de backend más** (`quotes`, `projects`, "
    "`ausencias`, `orders`, `catalogo`, `clientes`; 88 mensajes). ⚠️ Aquí el riesgo "
    "de traducir un DATO es máximo y se midió antes: `projects.derive_estado` "
    "**devuelve** `\"En progreso\"`/`\"Planificado\"`, que se escriben en la hoja y se "
    "comparan en 387 sitios. ⚠️ **Renombrar es dos pasos**: al pasar los `t = "
    "totales(...)` de `quotes` a `_tot` quedaron **16 usos de `t[\"subtotal\"]` "
    "colgando** —`NameError` en cuanto alguien creara una cotización—, encontrados "
    "preguntando al AST por todos los `Name` llamados `t` (16 antes, 0 después). "
    "⚠️ Y **cometí el fallo de v445 veinte minutos después de documentarlo**: metí "
    "`t()` dentro de `ausencias.TIPOS`, que se construye a nivel de módulo, así que "
    "las etiquetas quedaban congeladas al importar — lo cazó el guardián recién "
    "escrito; la constante guarda el texto BASE y `nombre_tipo()` traduce al pintar "
    "(en los correos se queda en base, regla v436). ⚠️ Al mover esas lecturas escribí "
    "`nombre_tipo(k)` cuando **la variable del bucle es `_tp`**: otro `NameError` que "
    "habría reventado «Mis ausencias» y que ni `compileall` ni el import ven. "
    "⚠️ Y **cuatro «fallos» del smoke eran del test** (firmas de `solicitar`, `crear` "
    "×2 y `create_cliente`) — regla v135, novena vez. 7 roturas probadas |\n"
)

doc = io.open(D, encoding="utf-8").read().rstrip()
s = io.open(P, encoding="utf-8").read()

ancla = "## i18n F5a:"
assert ancla in s, "ancla de sección NO casa"
s = s.replace(ancla, doc + "\n\n" + ancla, 1)

old = "## Versiones desplegadas (v445 = actual)"
assert old in s, "ancla de tabla NO casa"
s = s.replace(old, "## Versiones desplegadas (v446 = actual)", 1)

f445 = "| v445 | **F5a: los mensajes de BACKEND"
assert f445 in s, "ancla de fila v445 NO casa"
s = s.replace(f445, FILA + f445, 1)

io.open(P, "w", encoding="utf-8", newline="").write(s)

fila = [ln for ln in s.splitlines() if ln.startswith("| v446 |")]
assert len(fila) == 1, f"esperaba 1 fila v446, hay {len(fila)}"
for simbolo in ("derive_estado", "ausencias.TIPOS", "nombre_tipo", "create_cliente"):
    assert simbolo in fila[0], f"la fila perdió {simbolo!r}"
sec = re.search(r"## i18n F5b:.*?(?=\n## )", s, re.S)
assert sec, "la sección de v446 no está"
for simbolo in ("verif_v446.py", "pre_i18n", "estado_roster", "SESION_OCUPADA"):
    assert simbolo in sec.group(0), f"la sección perdió {simbolo!r}"
print(f"CLAUDE.md: fila ({len(fila[0])} chars) y sección "
      f"({len(sec.group(0).splitlines())} líneas) OK")
