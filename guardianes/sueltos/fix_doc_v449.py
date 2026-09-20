# -*- coding: utf-8 -*-
"""Rehace el bloque del quinto `t()` congelado, que bash dejó sin los backticks.

⚠️ Tercera vez que pasa lo mismo: el texto con backticks va SIEMPRE por fichero,
nunca por `bash -c`, porque el shell hace sustitución de comandos con ellos.
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\diego\P1\CLAUDE.md"

BUENO = """### ⚠️ Y el `t()` congelado al importar mordió por QUINTA vez — en esta misma versión
Al traducir el chip de estado de factura metí `t("outstanding")` dentro de un dict de
MÓDULO. **Tres guardianes** (v445, v446, v447) lo cazaron a la vez, y los tres decían
lo mismo. Van cinco: `auth.SESION_OCUPADA`, `ausencias.TIPOS`, `plan_data.USA`,
`toolruns.HERRAMIENTAS` y ahora `invoices_ui._EST_FMT` — **las cinco cometidas
DESPUÉS de documentar la regla**. El arreglo es siempre el mismo: la constante guarda
el texto BASE (y aquí sus CLAVES son además el dato que devuelve `estado_cobro`) y la
traducción se mueve a una función que se llama al PINTAR (`_est_fmt()`). El chequeo se
añadió también al guardián de cierre, para que no dependa de correr otro.
"""

s = io.open(P, encoding="utf-8").read()
ini = s.index("### ⚠️ Y el  congelado al importar mordió por QUINTA vez")
fin = s.index("### Verificación", ini)
s = s[:ini] + BUENO + "\n" + s[fin:]
io.open(P, "w", encoding="utf-8", newline="").write(s)

# ⚠️ Comprobar que esta vez SÍ conservó los símbolos
bloque = s[s.index("### ⚠️ Y el `t()` congelado"):s.index("### Verificación",
                                                          s.index("### ⚠️ Y el `t()` congelado"))]
for simbolo in ("auth.SESION_OCUPADA", "ausencias.TIPOS", "plan_data.USA",
                "toolruns.HERRAMIENTAS", "invoices_ui._EST_FMT", "estado_cobro",
                "_est_fmt()"):
    assert simbolo in bloque, f"perdió {simbolo!r}"
print(f"bloque rehecho, {len(bloque.splitlines())} líneas, símbolos intactos")
