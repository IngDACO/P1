# -*- coding: utf-8 -*-
"""Documenta v492 en CLAUDE.md: los ajustes contables se guardan por claves."""
import io

P = "C:/Users/diego/P1/CLAUDE.md"

SECCION = """## Los ajustes contables se guardan por CLAVES, no volcando `mapa()` entero (v492)

Pedido por el usuario tras verlo en la limpieza de v491: «que guarde solo el emparejado».

### El fallo
`contable.mapa(grupo)` devuelve lo guardado **ya FUSIONADO con los valores de fábrica**, y
los cuatro escritores del ajuste (`xero_nomina.guardar_emparejado`, el radio de estado de
envío de `xero_ui`, y los editores de cuentas y de nombres de nómina de `contable_ui`) lo
modificaban y lo escribían ENTERO con `guardar_mapa`. Así, guardar un emparejado con Xero
**congelaba en el grupo todos los valores por defecto** —cuentas, nombres de nómina, moneda,
categoría de seguimiento—, y un cambio futuro de un valor de fábrica en el código ya no le
llegaba, sin avisar. En producción: `AccountingJSON` de `cliente1` estaba vacío y salió lleno.

### El arreglo: `contable.guardar_claves(grupo, cambios)`
- Escribe **solo las claves que se tocan** y conserva todo lo demás guardado.
- Una clave cuyo valor es un dict se **fusiona UN nivel**: guardar las cuentas de Xero no
  borra las de MYOB. Un nivel y no más, a propósito: el `map` del emparejado se SUSTITUYE,
  así que quitar a una persona la quita de verdad en vez de acumularse.
- ⚠️ Lee lo guardado **FRESCO** (`auth.group_text_setting_fresco`), no de la caché: decide
  qué se escribe, y fusionar sobre algo de hace 120 s perdería lo que otra sesión acaba de
  guardar (v323).
- ⚠️ Si **no puede leer**, NO escribe y lo dice. Tratar un fallo de lectura como «vacío» y
  escribir solo lo nuevo borraría todo lo que había — es el caso que la lectura fresca
  **lanza** en vez de devolver el valor por defecto.
- Un JSON ilegible (que ya nadie podía leer) se reemplaza, dejando rastro en el log.
- `guardar_mapa` **se elimina**: con cuatro escritores volcando el mismo diccionario, el
  quinto habría vuelto a hacerlo.
- `auth._grupo_fresco` es la **única** búsqueda de la fila del grupo, compartida por quien lee
  para escribir y por `set_group_setting`: si divergieran, se leería una fila y se escribiría
  en otra.

### Verificación
`verif_v492.py`, **28 comprobaciones**, ejecutando `guardar_claves` contra una hoja falsa
(desde vacío, conservar MYOB, quitar un emparejado, no leer de la caché, no escribir si falla
la lectura, JSON ilegible) + estático (nadie vuelca `mapa()`, solo `contable.py` escribe
`AccountingJSON`, con la sonda validada contra un volcado construido). Batería: **8/8 roturas
+ CONTROL**, ⚠️ y esta vez **leyendo qué comprobación falla en cada una**: un guardián que
revienta también «caza» todas las roturas (v459/v463), así que el 8/8 solo vale con el
motivo a la vista. **Contra la hoja real**: guardar el emparejado dejó en `AccountingJSON`
solo `xero_empleados`, otra clave lo conservó, y se devolvió exactamente a vacío.
"""

FILA = ("| v492 | **Los ajustes contables se guardan por CLAVES** (pedido por el usuario). Los cuatro "
        "escritores volcaban `mapa()` —lo guardado YA fusionado con los valores de fábrica—, así "
        "que guardar un emparejado con Xero **congelaba todos los valores por defecto** en el "
        "grupo y un cambio futuro en el código dejaba de llegarle. Nueva `contable.guardar_claves`: "
        "solo lo tocado, fusión de un nivel (MYOB sobrevive a guardar Xero), ⚠️ lectura FRESCA y "
        "**si no puede leer, no escribe** (escribir solo lo nuevo borraría lo guardado). "
        "`guardar_mapa` eliminada; una sola búsqueda de la fila del grupo. 28 comprobaciones · "
        "**8/8 roturas + control** con el motivo de cada una a la vista · ejercitado contra la "
        "hoja real y devuelto a vacío |\n")

s = io.open(P, encoding="utf-8").read()
ANCLA = "## Versiones desplegadas (v491 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))
s = s.replace(ANCLA, SECCION + "\n## Versiones desplegadas (v492 = actual)")
s = s.replace(CAB, CAB + FILA)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: seccion v492 + fila + cabecera")
