# -*- coding: utf-8 -*-
"""Inserta la sección y la fila de v450 en CLAUDE.md (por FICHERO, no por shell).

⚠️ El texto lleva backticks y `bash` los devora con sustitución de comandos: ya
reescribió dos filas de la tabla en versiones anteriores (trampa nº26).
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\diego\P1\CLAUDE.md"
D = (r"C:\Users\diego\AppData\Local\Temp\claude\C--Users-diego"
     r"\1734b676-4bc1-41b7-b6b7-689294f44640\scratchpad\doc_v450.md")

FILA = (
    "| v450 | **La SEXTA red: las CABECERAS DE TABLA seguían en español.** El usuario "
    "preguntó «¿ya quedó todo en inglés?» y la respuesta era **no**: `st.dataframe` "
    "pinta la CLAVE del dict, y las filas de esta app se construyen a mano, así que la "
    "cabecera es invisible para las cinco redes anteriores —que miran POSICIÓN o "
    "IDIOMA, nunca claves—. Medido: **46 cabeceras en 12 tablas**, y **mezcladas dentro "
    "de la misma tabla** (`Alerts` y `Status` en inglés al lado de `Elevador` y "
    "`Costo`), que se nota más que si estuviera todo en español. ⚠️ El arreglo es la "
    "ETIQUETA, nunca la clave: muchas se leen de vuelta (`r[\"Elevador\"]`, `r[\"Peso\"]`) "
    "y varias viajan a `DatosJSON`. Nuevo `core/tabla.py` aplicado a las **66 tablas**. "
    "⚠️ **Verificado en vivo interceptando `fillText`** (el DOM no sirve, v399): "
    "`Column(label)` cambia la cabecera, deja las celdas numéricas **idénticas**, el "
    "`data_editor` devuelve las claves ORIGINALES y tolera claves que la tabla no tiene "
    "—esto último es lo que hace el arreglo robusto, porque deja de depender de mi "
    "atribución estática, que falló DOS veces mientras medía—. ⚠️ Y el propio MEDIDOR "
    "se equivocó **cuatro** veces (ámbito de módulo en vez de función; el argumento de "
    "`.get()` contado como celda; dar por traducida una columna con `column_config` "
    "**sin etiqueta**; y no ver el dict INLINE, que es la mitad de las tablas): la "
    "cuenta pasó de «15» a **90**. + **SÉPTIMA red** por MORFOLOGÍA en vez de por "
    "léxico —ninguna veía «vencida», «devuelto» ni «mantenimiento», a la vista en la "
    "campana— con la que se tradujeron **~180** textos más: 60 mensajes de backend que "
    "v445-v447 se dejaron, los avisos, los estados de inventario, los chips de "
    "cotización, los días del tablero, el correo interno y **las 31 líneas del informe "
    "ADMIN que v448 dio por cerradas**. ⚠️ Tres mapas espejo el mismo día "
    "(`{\"vigente\": \"vigente\"}`) y el **`t()` congelado por SEXTA vez**. 7 roturas |\n"
)

doc = io.open(D, encoding="utf-8").read().rstrip()
s = io.open(P, encoding="utf-8").read()

ancla = "## i18n CERRADO del todo:"
assert ancla in s, "ancla de sección NO casa"
s = s.replace(ancla, doc + "\n\n" + ancla, 1)

old = "## Versiones desplegadas (v449 = actual)"
assert old in s, "ancla de tabla NO casa"
s = s.replace(old, "## Versiones desplegadas (v450 = actual)", 1)

f449 = "| v449 | **i18n CERRADO del todo:"
assert f449 in s, "ancla de fila v449 NO casa"
s = s.replace(f449, FILA + f449, 1)

io.open(P, "w", encoding="utf-8", newline="").write(s)

fila = [ln for ln in s.splitlines() if ln.startswith("| v450 |")]
assert len(fila) == 1, f"esperaba 1 fila v450, hay {len(fila)}"
for simbolo in ("core/tabla.py", "fillText", "column_config", "DatosJSON"):
    assert simbolo in fila[0], f"la fila perdió {simbolo!r}"
sec = re.search(r"## ⚠️ LA SEXTA RED:.*?(?=\n## )", s, re.S)
assert sec, "la sección de v450 no está"
for simbolo in ("verif_v450.py", "tabla.cfg", "status_label", "list(DICT)"):
    assert simbolo in sec.group(0), f"la sección perdió {simbolo!r}"
print(f"CLAUDE.md: fila ({len(fila[0])} chars) y sección "
      f"({len(sec.group(0).splitlines())} líneas) OK")
