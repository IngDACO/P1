# -*- coding: utf-8 -*-
"""Añade a la seccion de v469 lo que paso al desplegar y migrar."""
import io

P = r"C:\Users\diego\P1\CLAUDE.md"
s = io.open(P, encoding="utf-8").read()

BLOQUE = """
### El despliegue: «desplegado ≠ corriendo», medido con el CAMBIO
Tras subir v469 el sidebar anunciaba **v469** y la app ejecutaba **v468**. No se
diagnosticó por la versión —que no prueba nada en ninguna dirección (v334 corregido por
v408/v452)— sino por el cambio: el formulario del catálogo seguía ofreciendo `Equipos` y
`unidad`, que son los `CAT_DEFAULT`/`UNIDADES` de v468; los de v469 son `Equipment` y
`unit`. Y el catálogo estaba vacío, así que no podían venir de la hoja. Tras el reinicio,
los mismos dos campos dicen **`Engineering` y `unit`**.
⚠️ **Y por poco lo leo mal**: mi primera sonda devolvió **una sola** opción («Equipos»)
cuando `CAT_DEFAULT` tiene siete — imposible en las dos versiones. Estaba leyendo el
valor SELECCIONADO con el desplegable ya cerrado, no las opciones. **Un dato imposible en
los dos escenarios no concluye nada**: hay que ir a mirar antes de afirmar (trampa nº12).

### Y el orden importaba: la hoja NO se podía migrar antes
`Login.Role` decide el rol de cada persona, y con el Cloud aún en v468 —que compara
`== "administrador"`— migrarla habría dejado a las 5 cuentas sin rol reconocido, cayendo
al default del CAMPO (v297, menor privilegio) sin dar ningún error. Por eso la secuencia
es desplegar → **ver el cambio** → migrar, y no al revés.
Migradas después las **5 celdas** (`propietario→owner`, `administrador→administrator`),
con foto previa **fuera del repo**, verificado leyendo (0 pendientes) y —lo que de verdad
importa— comprobando que **los 5 roles se reconocen y cada uno conserva su navegación**:
los dos `owner` con Administración/Pre-Start/Herramientas y los tres `administrator` con
Home/Fichaje/Planificación/Proyectos/Finanzas. Ninguno cae a la del campo.
⚠️ Son solo 5 celdas porque la demo se vació en v456; el resto de columnas de la lista
blanca no tienen datos, así que **esa parte de la migración no está ejercitada con
volumen** — se dice, en vez de dar por probado lo que no se probó.

### ⚠️ Y migrar la hoja dejó un chequeo midiendo OTRA COSA
El bloque 7 de `verif_v469` decía «contra la hoja REAL: el rol llega en inglés **con la
hoja en español**» y medía exactamente eso. Al migrar las 5 celdas, esa afirmación se
convirtió en la **identidad** —la hoja ya dice `owner`— así que su verde dejó de probar
la canonización, y nada lo anunció. Es la trampa nº1 en una forma nueva: **un cambio en
los DATOS puede vaciar un chequeo sin tocar una línea de código.** Partido en las dos
direcciones: la fila migrada (identidad) y una fila sin migrar (canonización), esta con
un caso CONSTRUIDO, porque en la hoja ya no queda ninguna.
"""

ANCLA = "### Los 8 guardianes que afirmaban «el DATO sigue en español»"
assert s.count(ANCLA) == 1, "ancla ausente"
io.open(P, "w", encoding="utf-8", newline="").write(s.replace(ANCLA, BLOQUE + "\n" + ANCLA))
print("CLAUDE.md: despliegue y migracion documentados")
