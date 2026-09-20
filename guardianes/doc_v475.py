# -*- coding: utf-8 -*-
"""Documenta v475 en CLAUDE.md (seccion + fila + cabecera, en el MISMO commit)."""
import io

P = "C:\\Users\\diego\\P1\\CLAUDE.md"

SECCION = """## Los 7 guardianes que no comprobaban nada, y lo que tapaban (v475)

Peticion del usuario: **«no dejes nada pendiente»**. El unico pendiente real eran los
**7 guardianes SIN DATOS** desde que v456 vacio la demo — no eran fallos, pero tampoco
garantia, y llevaban asi desde v471. Decision suya entre tres opciones: **que se apañen
solos** (construir su caso) en vez de volver a sembrar la demo de ruido.

Suite: **109 verde + 7 sin datos → 116 verde · 0 rojo · 0 roto, y ningun bloque
«SIN DATOS»**.

### ⚠️ TRES CADUCIDADES REALES que el «SIN DATOS» estaba tapando
Un guardian que no corre **no envejece a la vista: envejece a oscuras**. Al
descongelarlos salieron tres cambios deliberados que nadie les habia llevado:

| Qué | Desde |
|---|---|
| **43 guardianes simulaban una sesion con un ROL que ya no existe** (`administrador`, `propietario`, `campo`). Medido, no supuesto: `tenant.es_propietario()` devuelve **False** con el rol en español, asi que los caminos de propietario **no se estaban ejercitando** — parte de la suite salia verde bajo una sesion IMPOSIBLE | **v469** |
| `verif_v374_positivo` listaba los pre-starts por `ProyectoID`/`Fecha` y `hecho_hoy` lee `ProjectID`/`Date`: habria dicho «no hay pre-starts» **aunque los hubiera** | **v468** |
| `verif_v437` exigia «Engineer in charge» en la firma del informe al CLIENTE, y v459 lo renombro a «Head installer/s» | **v459** |

Las tres son la misma familia que `auth._COL` (v433) y la proyeccion de `list_users`
(v434): **algo migrado en el codigo y olvidado en lo que lo comprueba**.

### El metodo: caso construido, y cada sonda validada contra su contrario
Un caso construido sin validar es exactamente el «OK en vacio» que el mecanismo de
SIN DATOS existia para no fingir (trampa nº1). Asi que cada uno demuestra ademas que
CAZA lo que dice cazar:
- `hecho_hoy` con un `return False` fijo **y** con un `return True` fijo — los dos cazados;
- la agregacion de `pendiente_por_proyecto` indexada por NOMBRE, colando las que no
  deben nada, o dejandose fuera las archivadas — las tres cazadas;
- leer una vez por GRUPO en vez de por LIBRO (el fallo REAL de v377), que duplicaria filas;
- y los detectores del roster, que sobre una semana LIMPIA no pueden inventar ni un caso.

⚠️ Y `fixture_survey` **se auto-comprueba**: si `recalcular` no lo digiere, el guardian
sale ROJO en vez de dar por generado un informe que nunca se genero. Costo tres intentos
acertar la geometria, y cada fallo enseño una regla del dominio que no estaba escrita:
`BS` tiene que cuadrar con `SF1+BKS+2·RAIL+SF2`, `FS − TSW` tiene que caber en
`BC_CALC`, y ⚠️ **los pisos tienen que DIFERIR entre si** — `apply_offsets` normaliza
contra la ULTIMA fila, asi que con todos iguales `MAX_OFF_RL` sale ≤ 0, el barrido del
optimizador queda VACIO y no hay solucion que informar. **Un survey con todos los pisos
identicos no ejercita nada.**

### ⚠️ TRES SONDAS MIAS que fallaron por su propia FORMA
Las tres se cazaron midiendo, y las tres habrian dejado el trabajo a medias:
1. el barrido de roles miraba solo **diccionarios literales**, asi que se dejo los 12
   que entran por un helper (`como("propietario")`);
2. el detector de esos helpers dio **0** porque filtraba con `'"auth"'` — comillas
   DOBLES— sobre `ast.unparse`, que las escribe **simples**. Es el error de v459 con
   `ast.dump`, cometido otra vez;
3. la semana construida del roster usaba las claves de SALIDA (`asig`/`ini`/`fin`)
   cuando lo guardado son las CORTAS (`a`/`i`/`f`): los detectores veian **cero casos**
   — y lo dijeron, porque la validacion contra el contrario estaba puesta.

⚠️ Y un detalle que se repite: `col_offset` del AST va en **BYTES**, no en caracteres
(v468), asi que los dos parches de roles cortan sobre los bytes de la linea.

### Y una decision cerrada
Las **14 secciones** del elevador de la biblioteca se quedan como estan (decision del
usuario). Renombrarlas era gratis con la biblioteca vacia; a partir de que haya
material archivado arrastra migracion de la columna `Section`.
"""

FILA = ("| v475 | **«No dejes nada pendiente»**: los **7 guardianes SIN DATOS** desde "
        "que v456 vació la demo pasan a construir su propio caso (decisión del usuario, "
        "en vez de volver a sembrar ruido) → suite **116 verde · 0 rojo · 0 roto y sin "
        "bloque SIN DATOS**. ⚠️ Descongelarlos destapó **tres caducidades reales** que "
        "tapaban: **43 guardianes simulaban una sesión con un ROL que ya no existe** "
        "desde v469 —medido: `es_propietario()` es **False** con el rol en español, así "
        "que los caminos de propietario no se ejercitaban—, uno listaba pre-starts por "
        "columnas que **v468 renombró**, y otro exigía «Engineer in charge» cuando **v459** "
        "lo pasó a «Head installer/s». *Un guardián que no corre no envejece a la vista: "
        "envejece a oscuras.* Cada caso construido se valida contra su contrario (un "
        "`return False` fijo, una agregación por NOMBRE, leer por GRUPO en vez de por "
        "LIBRO…) y el fixture del survey **se auto-comprueba**. ⚠️ Y tres sondas MÍAS "
        "fallaron por su forma: mirar solo dicts literales, filtrar `ast.unparse` con "
        "comillas dobles (las escribe simples) y usar las claves de SALIDA del roster en "
        "vez de las cortas |\n")

s = io.open(P, encoding="utf-8").read()
ANCLA = "## Versiones desplegadas (v474 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))

s = s.replace(ANCLA, SECCION + "\n## Versiones desplegadas (v475 = actual)")
s = s.replace(CAB, CAB + FILA)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: sección v475 + fila + cabecera, todo en el mismo cambio")
