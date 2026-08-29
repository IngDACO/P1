"""Diccionario ESPAÑOL — inglés → español (v435).

⚠️ **Empieza vacío a propósito** (decisión del usuario): el idioma base es el inglés y
el español es una opción para traducir *solo lo que salga barato*. Con el fallback de
`i18n.t()`, lo que no esté aquí sale en inglés, que es correcto — así que este fichero
se puede llenar por partes, cuando estorbe leer algo, sin bloquear nada ni romper nada.

Cómo se añade una entrada: la clave es **el texto en inglés tal cual está en el
código**, incluidos los placeholders.

    TEXTOS = {
        "Save project":        "Guardar proyecto",
        "Saved {n} rows":      "Se guardaron {n} filas",   # ⚠️ el mismo placeholder
    }

⚠️ Los **valores de negocio** (`"En progreso"`, `"aprobada"`, `"campo"`…) NO van aquí:
viven en Google Sheets en español y se muestran con `i18n.etiqueta()`. Meterlos en
este diccionario no haría nada, porque `t()` ni los mira.
"""

TEXTOS = {}
