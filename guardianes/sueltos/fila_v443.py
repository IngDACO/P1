# -*- coding: utf-8 -*-
"""Reescribe la fila de v443 de la tabla de versiones.

⚠️ El primer intento fue por `bash -c "python -c '...'"` y **bash se comió los
backticks** haciendo sustitución de comandos: la fila quedó con los nombres de
símbolo vacíos. Es la familia de la trampa nº26 (escapes que se rompen al pasar por
el shell): el texto con backticks va SIEMPRE por fichero.
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\diego\P1\CLAUDE.md"

FILA = (
    "| v443 | **La CUARTA red del i18n: la f-string ENTERA, no sus trozos.** Salió "
    "clasificando los 6 rojos de la suite: el desglose de alertas del propietario "
    "estaba **a medias** (`f\"{n} behind schedule\"` traducido y `f\"{n} alarmas\"` "
    "no). ⚠️ Una f-string **no es una cadena, es una lista de trozos**, así que las "
    "tres redes anteriores —que miran cadenas COMPLETAS— no ven ni un **fragmento de "
    "UNA palabra** (`f\"{n} alarmas\"`, que además NO se puede envolver en `t()`) ni "
    "una **f-string a medio traducir** (`f\"Collected {x} de {y}\"`, cuyo español solo "
    "aparece al CONCATENAR los trozos). Barrido: **141 en `core/`, 48 en interfaz** — "
    "fases que yo había declarado cerradas. ⚠️ **Y la red se validó contra un caso "
    "construido y FALLÓ**: veía «de» pero **no «alarmas»** —su léxico eran palabras "
    "funcionales y ésa es un sustantivo sin acento—, o sea que el caso que originó la "
    "versión se le escapaba (trampa nº28, cuarta vez); con el léxico del dominio "
    "aparecieron **9 más**. ⚠️ **`Elevador` NO se traduce**: es la columna del editor "
    "de entrada que el `_snapshot` de v148 guarda en `DatosJSON` —`CAL-0002` ya tiene "
    "una— y renombrarla rompería «reabrir el cálculo»; sí las tablas de RESULTADO, que "
    "viajan al PDF de obra. ⚠️ Y un **NameError camino de producción**: `d('Works')` en "
    "un módulo que solo importa `t` (el fallo de v423), invisible para `compileall` y "
    "para el import. 7 roturas probadas — una solo tras corregir el guardián, que "
    "comprobaba PRESENCIA y con DOS tablas dejaba pasar romper una. Los 6 rojos eran "
    "CADUCADOS, ⚠️ uno **por el CALENDARIO** (miraba la semana actual, así que se ponía "
    "rojo todos los lunes) |\n"
)

s = io.open(P, encoding="utf-8").read()
viejas = [l for l in s.splitlines(keepends=True) if l.startswith("| v443 |")]
assert len(viejas) == 1, f"esperaba 1 fila v443, hay {len(viejas)}"
s = s.replace(viejas[0], FILA, 1)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("fila v443 reescrita, longitud", len(FILA))

# ⚠️ Comprobar que la sección larga NO sufrió lo mismo (fue por fichero, pero se mira)
sec = re.search(r"## i18n: la CUARTA red.*?(?=\n## )", s, re.S)
assert sec, "la sección de v443 no está"
txt = sec.group(0)
for simbolo in ("DatosJSON", "in_edit[f\"Elevador {i+1}\"]", "verif_v443.py",
                "roster_ui", "invoices_ui", "_result_matrix"):
    assert simbolo in txt, f"la sección perdió {simbolo!r} (¿se comió los backticks?)"
print(f"sección OK: {len(txt.splitlines())} líneas, símbolos intactos")
