# -*- coding: utf-8 -*-
"""Inserta la sección y la fila de v444 en CLAUDE.md.

⚠️ Va por FICHERO, no por `bash -c`: el shell hace sustitución de comandos con los
backticks y deja la fila con los nombres de símbolo vacíos (pasó con v443).
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\diego\P1\CLAUDE.md"
D = (r"C:\Users\diego\AppData\Local\Temp\claude\C--Users-diego"
     r"\1734b676-4bc1-41b7-b6b7-689294f44640\scratchpad\doc_v444.md")

FILA = (
    "| v444 | **Las CABECERAS DE TABLA que son clave de dict, y la QUINTA red.** "
    "⚠️ Aquí no se decide por idioma: una clave de dict y una etiqueta **se ven "
    "igual en el AST**, así que `riesgo_claves.py` clasifica las 70 candidatas por "
    "lo que HACEN — 15 son IDENTIFICADOR (opción de widget o comparada con `==`: "
    "traducirla deja la rama MUERTA), 10 son COLUMNA DE EDITOR (el `_snapshot` de "
    "v148 las guarda en `DatosJSON`), 17 SE LEEN desde otro módulo y 4 son VALOR de "
    "`i18n`. Las **31 traducibles** se aplicaron **por AST y por posición**, nunca "
    "por texto: `\"Credenciales\"` es también el nombre de una hoja y `\"Horas\"`/"
    "`\"Estado\"` son columnas reales del libro. ⚠️ **El clasificador dio por SEGURA "
    "una que no lo era**: `'Riel'` es columna del editor persistido y no la vio "
    "porque `[\"Riel\"]` dentro de una lista no es un `Subscript` — un falso «se "
    "puede» invita a romper justo lo que hay que proteger. + **QUINTA red**: "
    "etiquetas de UNA palabra dentro de TUPLAS (`(\"cred\", …, \"Credenciales\", …)`, "
    "`f\"→ Ir a {secn}\"`), invisibles para las cuatro redes anteriores y que van a "
    "mano porque la misma cadena es dato en otro sitio; ⚠️ mi propia exclusión de "
    "nombres de hoja **tapaba dos etiquetas reales**. ⚠️ Y el chequeo de "
    "`column_config` **se aprobaba a sí mismo** (contaba sus propias claves como si "
    "fueran de la fila) y decía «0 huérfanas» con media traducción rota delante. "
    "7 roturas probadas — dos solo tras corregir el guardián, las dos por comprobar "
    "PRESENCIA en vez del literal exacto |\n"
)

doc = io.open(D, encoding="utf-8").read().rstrip()
s = io.open(P, encoding="utf-8").read()

ancla = "## i18n: la CUARTA red"
assert ancla in s, "ancla de sección NO casa"
s = s.replace(ancla, doc + "\n\n" + ancla, 1)

old = "## Versiones desplegadas (v443 = actual)"
assert old in s, "ancla de tabla NO casa"
s = s.replace(old, "## Versiones desplegadas (v444 = actual)", 1)

f443 = "| v443 | **La CUARTA red del i18n"
assert f443 in s, "ancla de fila v443 NO casa"
s = s.replace(f443, FILA + f443, 1)

io.open(P, "w", encoding="utf-8", newline="").write(s)

# ⚠️ Comprobar que ni la fila ni la sección perdieron sus backticks
fila = [ln for ln in s.splitlines() if ln.startswith("| v444 |")]
assert len(fila) == 1, f"esperaba 1 fila v444, hay {len(fila)}"
for simbolo in ("riesgo_claves.py", "DatosJSON", "column_config", "Subscript"):
    assert simbolo in fila[0], f"la fila perdió {simbolo!r}"
sec = re.search(r"## i18n: las CABECERAS DE TABLA.*?(?=\n## )", s, re.S)
assert sec, "la sección de v444 no está"
for simbolo in ("verif_v444.py", "cols_expected", "riesgo_claves.py", "Duración (d)"):
    assert simbolo in sec.group(0), f"la sección perdió {simbolo!r}"
print(f"CLAUDE.md: fila ({len(fila[0])} chars) y sección "
      f"({len(sec.group(0).splitlines())} líneas) OK")
